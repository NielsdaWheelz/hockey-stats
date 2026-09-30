"""account for an admitted season population without inventing missing evidence."""

from collections import Counter, defaultdict
from pathlib import Path
import stat
from typing import Literal, TypedDict

from .artifacts import write_json
from .captures import InputContractError
from .interpret import Interpretation, Issue, interpret_game
from .reconstruct import Coverage, reconstruct_game
from .references import ReferenceDocument


GameStatus = Literal["missing_capture", "input_error", "identity_unavailable",
                     "identity_mismatch", "reconstructed"]
STATUSES: tuple[GameStatus, ...] = ("missing_capture", "input_error", "identity_unavailable",
                                   "identity_mismatch", "reconstructed")


class CorpusGame(TypedDict):
    game_id: str
    inventory_source_index: int
    capture_path: str
    status: GameStatus
    reason: str | None
    output_path: str | None
    coverage: Coverage | None


class CorpusPlayer(TypedDict):
    player_id: int
    game_ids: list[str]
    birth_date: str | None
    shoots_catches: str | None
    observation_indices: list[int]
    issues: list[Issue]


class CoverageTotal(TypedDict):
    value: int | None
    contributing_games: int
    unavailable_games: int


class CorpusSummary(TypedDict):
    expected_games: int
    games_by_status: dict[GameStatus, int]
    games_with_unavailable_rosters: int
    players_seen: int
    players_with_birth_date: int
    players_with_shoots_catches: int
    games_with_unavailable_horizons: int
    coverage_totals: dict[str, dict[str, CoverageTotal]]


class CorpusDocument(TypedDict):
    schema_version: Literal[1]
    implementation: Interpretation
    reference: ReferenceDocument
    games_root: str
    games: list[CorpusGame] | None
    players: list[CorpusPlayer] | None
    summary: CorpusSummary | None
    missing_game_ids: list[str] | None
    issues: list[Issue]


def audit_corpus(reference: ReferenceDocument, games_root: Path, output: Path,
                 implementation: Interpretation) -> CorpusDocument:
    """write per-game diagnostics into a new prepared output directory.

    local capture contract errors belong to game rows and do not stop later
    games. filesystem and programming errors propagate; the caller writes
    the final report only after this function returns.
    """
    result: CorpusDocument = {
        "schema_version": 1, "implementation": implementation, "reference": reference,
        "games_root": str(games_root), "games": None, "players": None,
        "summary": None, "missing_game_ids": None, "issues": [],
    }
    inventory = reference["inventory"]
    if inventory is None:
        result["issues"].append({"code": "inventory_unavailable", "source": "season-games",
                                 "path": "/inventory", "message": "inventory not admitted; season population unavailable; inspect reference issues"})
        return result
    (output / "games").mkdir()
    games: list[CorpusGame] = []
    roster_games: dict[int, set[str]] = defaultdict(set)
    available_rosters = 0
    available_horizons = 0
    for entry in sorted(inventory, key=lambda row: row["game_id"]):
        game_id = entry["game_id"]
        directory = games_root / game_id
        row: CorpusGame = {
            "game_id": game_id, "inventory_source_index": entry["source_index"],
            "capture_path": str(directory.resolve()), "status": "missing_capture",
            "reason": None, "output_path": None, "coverage": None,
        }
        games.append(row)
        try:
            mode = directory.lstat().st_mode
        except FileNotFoundError:
            row["reason"] = "capture directory absent; game evidence unavailable"
            continue
        try:
            if stat.S_ISLNK(mode):
                mode = directory.stat().st_mode
            if not stat.S_ISDIR(mode):
                raise InputContractError(f"{directory}: capture path is not a directory")
            interpreted = interpret_game(directory)
            if interpreted["requested_game_id"] != game_id:
                raise InputContractError(f"{directory}: requested game {interpreted['requested_game_id']} conflicts with inventory lookup {game_id}")
        except InputContractError as error:
            row["status"] = "input_error"
            row["reason"] = str(error)
            result["issues"].append({"code": "game_input_error", "source": "corpus",
                                     "path": f"/games/{len(games) - 1}", "message": str(error)})
            continue
        reconstruction = reconstruct_game(interpreted)
        relative = f"games/{game_id}.json"
        write_json(output / relative, {"schema_version": 1, "implementation": implementation,
                                       "interpreted": interpreted, "reconstruction": reconstruction})
        row["output_path"] = relative
        game = interpreted["game"]
        if game is None:
            row["status"] = "identity_unavailable"
            row["reason"] = "completed regular-season identity unavailable; inspect game diagnostic"
        else:
            conflicts = [field for field in ("game_id", "season", "game_type", "game_date",
                                             "away_team_id", "home_team_id") if game[field] != entry[field]]
            if conflicts:
                row["status"] = "identity_mismatch"
                row["reason"] = "inventory/game disagreement: " + ", ".join(conflicts)
            else:
                row["status"] = "reconstructed"
                row["coverage"] = reconstruction["coverage"]
                roster = interpreted["roster_records"]
                if roster is not None:
                    available_rosters += 1
                    for player in roster:
                        if player["player_id"] is not None:
                            roster_games[player["player_id"]].add(game_id)
                time = reconstruction["coverage"]["time"]
                expected = time["expected_periods"]
                if expected is not None and set(expected).issubset(time["supported_periods"]):
                    available_horizons += 1
        if row["reason"] is not None:
            result["issues"].append({"code": row["status"], "source": "corpus",
                                     "path": f"/games/{len(games) - 1}", "message": row["reason"]})

    observations_by_id = defaultdict(list)
    unavailable_bio_identities = any(observation["player_id"] is None
                                   for observation in reference["bio_observations"])
    for index, observation in enumerate(reference["bio_observations"]):
        if observation["player_id"] is not None:
            observations_by_id[observation["player_id"]].append(index)
    players: list[CorpusPlayer] = []
    for player_id, game_ids in sorted(roster_games.items()):
        indices = observations_by_id[player_id]
        player: CorpusPlayer = {"player_id": player_id, "game_ids": sorted(game_ids),
                                "birth_date": None, "shoots_catches": None,
                                "observation_indices": indices, "issues": []}
        players.append(player)
        issue_indices = sorted({issue for index in indices
                                for issue in reference["bio_observations"][index]["issue_indices"]})
        player["issues"].extend(reference["issues"][index] for index in issue_indices)
        if not indices:
            incomplete = any(not collection["complete"] for collection in reference["bio_collections"])
            if incomplete:
                reason = "reference collections incomplete or unavailable"
            elif unavailable_bio_identities:
                reason = "row identities unavailable; collection counts cannot establish player absence"
            else:
                reason = "both complete reference collections lack this roster id"
            player["issues"].append({"code": "bio_unavailable", "source": "references",
                                      "path": f"/players/{len(players) - 1}",
                                      "message": "no matching identifiable bio row; " + reason})
        for field in ("birth_date", "shoots_catches"):
            values = {reference["bio_observations"][index][field] for index in indices
                      if reference["bio_observations"][index][field] is not None}
            if len(values) == 1:
                player[field] = values.pop()
            elif len(values) > 1:
                player["issues"].append({"code": "bio_field_conflict", "source": "references",
                                          "path": f"/players/{len(players) - 1}/{field}",
                                          "message": f"conflicting known {field} observations; joined field unavailable"})

    count = len(inventory)
    coverage_totals: dict[str, dict[str, CoverageTotal]] = {}
    # scalar fields follow the existing coverage contracts; period arrays are
    # counted through horizon availability rather than nonsensically summed.
    for group, fields in (
        ("time", ("known_seconds", "five_on_five_seconds", "other_seconds", "unresolved_seconds")),
        ("attempts", ("known_timed_attempts", "five_on_five", "other", "unresolved", "linked_five_on_five", "unclassified_events")),
        ("locations", ("known_timed_attempts", "normalized", "missing_coordinates", "unresolved_frame")),
    ):
        coverage_totals[group] = {}
        for field in fields:
            values = [row["coverage"][group][field] for row in games
                      if row["coverage"] is not None and row["coverage"][group][field] is not None]
            coverage_totals[group][field] = {"value": sum(values) if values else None,
                                             "contributing_games": len(values),
                                             "unavailable_games": count - len(values)}
    statuses = Counter(row["status"] for row in games)
    result.update({"games": games, "players": players,
                   "missing_game_ids": [row["game_id"] for row in games if row["status"] == "missing_capture"],
                   "summary": {
                       "expected_games": count, "games_by_status": {status: statuses[status] for status in STATUSES},
                       "games_with_unavailable_rosters": count - available_rosters,
                       "players_seen": len(players),
                       "players_with_birth_date": sum(player["birth_date"] is not None for player in players),
                       "players_with_shoots_catches": sum(player["shoots_catches"] is not None for player in players),
                       "games_with_unavailable_horizons": count - available_horizons,
                       "coverage_totals": coverage_totals,
                   }})
    return result


def report_corpus(document: CorpusDocument, output: Path) -> None:
    season = document["reference"]["requested_season"]
    print(f"corpus audit written: {season[:4]}–{season[6:]} regular season")
    summary = document["summary"]
    if summary is None:
        print("inventory unavailable; no season denominator; inspect reference issues")
    else:
        statuses = summary["games_by_status"]
        print(f"inventory: {summary['expected_games']} games; source counts agree")
        print(f"captures: {summary['expected_games'] - statuses['missing_capture']} present; {statuses['missing_capture']} missing")
        print(f"game identity: {statuses['reconstructed']} admitted; {statuses['identity_unavailable']} unavailable; {statuses['identity_mismatch']} conflicting; {statuses['input_error']} input errors")
        total = summary["coverage_totals"]["time"]["five_on_five_seconds"]
        value = total["value"] if total["value"] is not None else "unavailable"
        print(f"supported 5v5 seconds: {value} from {total['contributing_games']} games; unavailable for {total['unavailable_games']}")
        for group, field in (("time", "unresolved_seconds"), ("attempts", "unresolved"), ("attempts", "unclassified_events")):
            quantity = summary["coverage_totals"][group][field]
            if quantity["value"]:
                print(f"{group} {field}: {quantity['value']} from {quantity['contributing_games']} games; unavailable for {quantity['unavailable_games']}")
        print(f"period horizons unavailable or incomplete: {summary['games_with_unavailable_horizons']} games")
        print(f"rosters unavailable: {summary['games_with_unavailable_rosters']} games")
        print(f"player references: {summary['players_seen']} roster ids seen; {summary['players_with_birth_date']} birth dates; {summary['players_with_shoots_catches']} shoots/catches")
        gaps = sum(player["birth_date"] is None or player["shoots_catches"] is None for player in document["players"])
        if gaps:
            print(f"player reference gaps: {gaps} roster ids; inspect player issues and observations")
    for collection in document["reference"]["bio_collections"]:
        if not collection["complete"]:
            print(f"{collection['source']} incomplete or unavailable: {collection['received_rows']} received; {collection['reported_total']} advertised; inspect reference issues")
    print("model eligibility: not assessed")
    print(f"output: {output / 'corpus.json'}")
