"""interpret season inventory and located player bio observations offline."""

from datetime import date
from pathlib import Path
import re
from typing import Any, TypedDict

from .captures import InputContractError, REFERENCE_SOURCES, read_reference_capture, strict_json
from .interpret import Check, Input, Issue


class Season(TypedDict):
    season: str
    reported_regular_games: int
    reported_start: str | None
    reported_regular_end: str | None


class InventoryGame(TypedDict):
    source_index: int
    game_id: str
    season: str
    game_type: int
    game_date: str
    away_team_id: int
    home_team_id: int
    reported_game_state: int | None
    reported_schedule_state: int | None


class BioCollection(TypedDict):
    source: str
    received_rows: int | None
    reported_total: int | None
    complete: bool


class BioObservation(TypedDict):
    source: str
    source_index: int
    player_id: int | None
    birth_date: str | None
    shoots_catches: str | None
    issue_indices: list[int]


class ReferenceDocument(TypedDict):
    schema_version: int
    requested_season: str
    inputs: list[Input]
    season: Season | None
    inventory: list[InventoryGame] | None
    bio_collections: list[BioCollection]
    bio_observations: list[BioObservation]
    checks: list[Check]
    issues: list[Issue]


def _issue(issues: list[Issue], source: str, path: str, code: str, message: str) -> None:
    issues.append({"code": code, "source": source, "path": path, "message": message})


def _integer(row: dict[str, Any], field: str, source: str, path: str,
             issues: list[Issue], minimum: int | None = 0) -> int | None:
    value = row.get(field)
    if type(value) is int and (minimum is None or value >= minimum):
        return value
    _issue(issues, source, path + "/" + field, "invalid_integer",
           ("expected integer" if minimum is None else f"expected integer >= {minimum}") + "; selected value unavailable")
    return None


def _date(value: Any) -> bool:
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def interpret_references(directory: Path) -> ReferenceDocument:
    captures = [read_reference_capture(directory, source) for source in REFERENCE_SOURCES]
    requested_ids = {capture.requested_season for capture in captures if capture.requested_season is not None}
    if len(requested_ids) != 1:
        raise InputContractError(
            f"{directory}: capture records must establish one coherent requested season; repair metadata or recapture"
        )
    requested = requested_ids.pop()
    inputs: list[Input] = []
    issues: list[Issue] = []
    rows: dict[str, list[Any] | None] = {}
    totals: dict[str, int | None] = {}
    for capture in captures:
        source = capture.source
        entry: Input = {"source": source, "capture_path": str(capture.capture_path),
                        "requested_at": capture.requested_at, "http_status": capture.http_status,
                        "body_sha256": capture.body_sha256, "status": "unavailable", "reason": capture.reason}
        inputs.append(entry)
        rows[source] = None
        totals[source] = None
        if capture.body is not None:
            try:
                body = strict_json(capture.body)
            except (ValueError, UnicodeDecodeError) as error:
                entry["reason"] = f"invalid source json: {error}; source unavailable"
            else:
                if not isinstance(body, dict):
                    entry["reason"] = "source json must be an object; source unavailable"
                else:
                    entry["status"] = "parsed"
                    entry["reason"] = None
                    totals[source] = _integer(body, "total", source, "", issues)
                    data = body.get("data")
                    if isinstance(data, list):
                        rows[source] = data
                    else:
                        _issue(issues, source, "/data", "unavailable_collection",
                               "expected array; collection unavailable")
        if entry["reason"] is not None:
            _issue(issues, source, "/", "unavailable_source", entry["reason"])

    checks: list[Check] = []

    def check(name: str, source: str, observed: int | None, expected: int | None) -> bool:
        status = "unavailable" if observed is None or expected is None else "match" if observed == expected else "mismatch"
        reason = None if status == "match" else "received or expected count unavailable" if status == "unavailable" else "received count disagrees with expected count"
        checks.append({"name": name, "source": source, "status": status,
                       "observed": observed, "expected": expected, "reason": reason})
        if status != "match":
            _issue(issues, source, "/data" if name.endswith("rows") or name in ("season_regular_games", "inventory_unique_ids") else "/total",
                   name, reason)
        return status == "match"

    source = "season-summary"
    summary_rows = rows[source]
    summary_count = None if summary_rows is None else len(summary_rows)
    summary_rows_match = check("season_summary_rows", source, summary_count, 1)
    summary_total_match = check("season_summary_total", source, totals[source], 1)
    season: Season | None = None
    if summary_rows_match:
        row = summary_rows[0]
        if not isinstance(row, dict):
            _issue(issues, source, "/data/0", "invalid_object", "expected season object; season unavailable")
        else:
            row_id = _integer(row, "id", source, "/data/0", issues, 1)
            count = _integer(row, "totalRegularSeasonGames", source, "/data/0", issues, 1)
            identity_matches = row_id is not None and str(row_id) == requested
            if not identity_matches:
                _issue(issues, source, "/data/0/id", "season_identity_mismatch",
                       "summary id must identify requested season; season unavailable")
            boundaries: dict[str, str | None] = {}
            for field in ("startDate", "regularSeasonEndDate"):
                value = row.get(field)
                if not isinstance(value, str):
                    _issue(issues, source, "/data/0/" + field, "unavailable_boundary",
                           "reported season boundary text missing or malformed; boundary unavailable")
                    value = None
                boundaries[field] = value
            if summary_total_match and identity_matches and count is not None:
                season = {"season": requested, "reported_regular_games": count,
                          "reported_start": boundaries["startDate"],
                          "reported_regular_end": boundaries["regularSeasonEndDate"]}

    source = "season-games"
    inventory_rows = rows[source]
    inventory_count = None if inventory_rows is None else len(inventory_rows)
    rows_match = check("inventory_rows", source, inventory_count, totals[source])
    candidate: list[InventoryGame] = []
    valid_ids: set[int] = set()
    identities_valid = inventory_rows is not None
    for index, row in enumerate(inventory_rows or []):
        path = f"/data/{index}"
        if not isinstance(row, dict):
            identities_valid = False
            _issue(issues, source, path, "invalid_object", "expected game object; inventory unavailable")
            continue
        game_id = _integer(row, "id", source, path, issues, 1)
        row_season = _integer(row, "season", source, path, issues, 1)
        game_type = _integer(row, "gameType", source, path, issues, 1)
        away = _integer(row, "visitingTeamId", source, path, issues, 1)
        home = _integer(row, "homeTeamId", source, path, issues, 1)
        game_date = row.get("gameDate")
        id_valid = game_id is not None and re.fullmatch(r"[0-9]{10}", str(game_id)) is not None
        if id_valid:
            if game_id in valid_ids:
                _issue(issues, source, path + "/id", "duplicate_identity", "repeated game id; inventory unavailable")
                identities_valid = False
            valid_ids.add(game_id)
        else:
            _issue(issues, source, path + "/id", "invalid_game_id", "expected ten-digit integer game id; inventory unavailable")
        identity_matches = (id_valid and str(game_id)[:4] == requested[:4]
                            and str(game_id)[4:6] == "02" and row_season == int(requested)
                            and game_type == 2)
        if not identity_matches:
            identities_valid = False
            _issue(issues, source, path, "game_identity_mismatch",
                   "game id year/type and reported season/type must identify requested regular season; inventory unavailable")
        date_valid = _date(game_date)
        if not date_valid:
            identities_valid = False
            _issue(issues, source, path + "/gameDate", "invalid_date", "expected actual YYYY-MM-DD date; inventory unavailable")
        teams_valid = away is not None and home is not None and away != home
        if not teams_valid:
            identities_valid = False
            _issue(issues, source, path, "invalid_game_teams", "expected distinct positive team ids; inventory unavailable")
        game_state = _integer(row, "gameStateId", source, path, issues, None)
        schedule_state = _integer(row, "gameScheduleStateId", source, path, issues, None)
        if identity_matches and date_valid and teams_valid:
            candidate.append({"source_index": index, "game_id": str(game_id), "season": requested,
                              "game_type": 2, "game_date": game_date, "away_team_id": away,
                              "home_team_id": home, "reported_game_state": game_state,
                              "reported_schedule_state": schedule_state})
    unique_match = check("inventory_unique_ids", source, None if inventory_rows is None else len(valid_ids), inventory_count)
    season_match = check("season_regular_games", source, inventory_count,
                         None if season is None else season["reported_regular_games"])
    inventory = sorted(candidate, key=lambda row: row["game_id"]) if identities_valid and rows_match and unique_match and season_match else None

    collections: list[BioCollection] = []
    observations: list[BioObservation] = []
    for source in ("skater-bios", "goalie-bios"):
        data = rows[source]
        received = None if data is None else len(data)
        total = totals[source]
        complete = received is not None and total is not None and received == total
        collections.append({"source": source, "received_rows": received,
                            "reported_total": total, "complete": complete})
        if received is not None and total is not None and not complete:
            _issue(issues, source, "/total", "incomplete_collection",
                   "received bio row count disagrees with advertised total; absent players cannot be established")
        seen: set[int] = set()
        for index, row in enumerate(data or []):
            start = len(issues)
            path = f"/data/{index}"
            player_id = None
            values: dict[str, str | None] = {"birthDate": None, "shootsCatches": None}
            if not isinstance(row, dict):
                _issue(issues, source, path, "invalid_object", "expected bio object; fields unavailable")
            else:
                player_id = _integer(row, "playerId", source, path, issues, 1)
                if player_id is not None:
                    if player_id in seen:
                        _issue(issues, source, path + "/playerId", "duplicate_identity", "repeated player id in report; observations retained separately")
                    seen.add(player_id)
                for field in values:
                    value = row.get(field)
                    if field not in row:
                        code, message = "missing_field", "field absent; selected value unavailable"
                    elif value is None:
                        code, message = "null_field", "field explicitly null; selected value unavailable"
                    elif (_date(value) if field == "birthDate" else isinstance(value, str) and value in ("L", "R")):
                        values[field] = value
                        continue
                    else:
                        code, message = "invalid_field", "expected actual YYYY-MM-DD date" if field == "birthDate" else "expected L or R"
                    _issue(issues, source, path + "/" + field, code, message)
            observations.append({"source": source, "source_index": index, "player_id": player_id,
                                 "birth_date": values["birthDate"], "shoots_catches": values["shootsCatches"],
                                 "issue_indices": list(range(start, len(issues)))})

    return {"schema_version": 1, "requested_season": requested, "inputs": inputs,
            "season": season, "inventory": inventory, "bio_collections": collections,
            "bio_observations": observations, "checks": checks, "issues": issues}
