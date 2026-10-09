"""interpret selected captured hockey records without reconstructing exposure."""

from datetime import date, datetime, timezone
import math
from pathlib import Path
import re
from typing import Any, Literal, NotRequired, TypedDict

from .captures import InputContractError, SOURCES, read_capture, strict_json
from .play_report import extract_report, extract_summary, report_identity


class Issue(TypedDict):
    code: str
    source: str
    path: str
    message: str


class Input(TypedDict):
    source: str
    capture_path: str
    requested_at: str | None
    http_status: int | None
    body_sha256: str | None
    status: Literal["parsed", "unavailable", "reference_only"]
    reason: str | None


class SourceEvidence(TypedDict):
    source: str
    path: str
    input_index: int


class FieldProblem(TypedDict):
    status: Literal["unavailable", "conflict", "not_applicable"]
    reason: str
    evidence_refs: list[int]


class SourceFields(TypedDict):
    values: dict[str, Any]
    problems: dict[str, FieldProblem]
    evidence: list[SourceEvidence]


class SourceObservation(TypedDict):
    source: str
    source_fields: SourceFields


class Game(TypedDict):
    game_id: str
    season: str
    game_type: int
    game_date: str
    away_team_id: int
    home_team_id: int
    away_team_abbrev: str | None
    home_team_abbrev: str | None


class Result(TypedDict):
    source: str
    away_score: int | None
    home_score: int | None
    away_sog: int | None
    home_sog: int | None
    last_period_type: str | None


class RosterRecord(TypedDict):
    source_index: int
    player_id: int | None
    team_id: int | None
    first_name: str | None
    last_name: str | None
    reported_position: str | None
    sweater_number: int | None


class BoxscorePlayer(TypedDict):
    source_path: str
    player_id: int | None
    team_id: int
    name: str | None
    reported_position: str | None
    toi: str | None
    toi_seconds: int | None
    shift_count: int | None
    goals: int | None
    assists: int | None
    sog: int | None
    blocked_shots: int | None
    source_fields: SourceFields
    derived_fields: SourceFields


class Event(TypedDict):
    source_index: int
    event_id: int | None
    sort_order: int | None
    type_code: int | None
    type_key: str | None
    kind_valid: bool
    period_number: int | None
    period_type: str | None
    time_in_period: str | None
    time_remaining: str | None
    elapsed_seconds: int | None
    timed_period: bool | None
    situation_code: str | None
    home_team_defending_side: str | None
    zone_code: str | None
    owner_team_id: int | None
    reported_x: int | float | None
    reported_y: int | float | None
    roles: dict[str, int | None]
    shooting_team_id: int | None
    shot_type: str | None
    reason: str | None
    secondary_reason: str | None
    penalty_type: str | None
    penalty_description: str | None
    penalty_duration_minutes: int | None
    away_score: int | None
    home_score: int | None


class Shift(TypedDict):
    source_index: int
    record_id: int | None
    type_code: int | None
    kind: Literal["shift", "other"]
    player_id: int | None
    team_id: int | None
    period_number: int | None
    shift_number: int | None
    start_time: str | None
    end_time: str | None
    duration: str | None
    event_number: int | None
    event_description: str | None
    start_seconds: int | None
    end_seconds: int | None
    duration_seconds: int | None
    interval_status: Literal["coherent", "inconsistent", "unavailable", "not_shift"]


class ReportMember(TypedDict):
    sweater_number: int | None
    reported_position: str | None
    player_id: int | None


class ReportRow(TypedDict):
    source_index: int
    row_id: str
    event_number: int | None
    period_number: int | None
    time_in_period: str | None
    time_remaining: str | None
    elapsed_seconds: int | None
    event_code: str | None
    reported_strength: str | None
    description: str | None
    away_members: list[ReportMember] | None
    home_members: list[ReportMember] | None
    penalty_shot: bool | None
    shooting_team_id: int | None
    shooter_sweater_number: int | None
    shooter_id: int | None
    shot_type: str | None


class LandingGoal(TypedDict):
    source_path: str
    event_id: int | None
    period_number: int | None
    period_type: str | None
    time_in_period: str | None
    elapsed_seconds: int | None
    team_id: int | None
    credited_scorer_id: int | None
    goal_modifier: str | None


class ScoreCounts(TypedDict):
    away: int | None
    home: int | None


class Check(TypedDict):
    name: str
    source: NotRequired[str]
    team_id: NotRequired[int]
    player_id: NotRequired[int | None]
    status: Literal["match", "mismatch", "unavailable"]
    observed: int | ScoreCounts | None
    expected: int | ScoreCounts | None
    reason: str | None


class Interpretation(TypedDict):
    git_commit: str | None
    git_dirty: bool | None
    python_version: str


class GameDocument(TypedDict):
    schema_version: int
    interpretation: NotRequired[Interpretation]
    requested_game_id: str
    inputs: list[Input]
    game: Game | None
    reported_results: list[Result]
    roster_records: list[RosterRecord] | None
    boxscore_players: list[BoxscorePlayer] | None
    events: list[Event] | None
    shift_records: list[Shift] | None
    report_rows: list[ReportRow] | None
    landing_goals: list[LandingGoal] | None
    recording_observations: list[SourceObservation]
    coach_scratch_observations: list[SourceObservation]
    checks: list[Check]
    issues: list[Issue]
    uncomputed: list[str]


# these selected source kinds distinguish counted records from non-attempts.
_EVENT_CODES = {
    "faceoff": 502, "hit": 503, "giveaway": 504, "goal": 505,
    "shot-on-goal": 506, "missed-shot": 507, "blocked-shot": 508,
    "penalty": 509, "stoppage": 516, "period-start": 520,
    "period-end": 521, "shootout-complete": 523, "game-end": 524,
    "takeaway": 525, "delayed-penalty": 535, "failed-shot-attempt": 537,
}
_ROLES = {
    "shooter": "shootingPlayerId", "scorer": "scoringPlayerId",
    "blocker": "blockingPlayerId", "goalie": "goalieInNetId",
    "assist1": "assist1PlayerId", "assist2": "assist2PlayerId",
    "faceoff_winner": "winningPlayerId", "faceoff_loser": "losingPlayerId",
    "hitter": "hittingPlayerId", "hit_player": "hitteePlayerId",
    "penalty_committed_by": "committedByPlayerId",
    "penalty_drawn_by": "drawnByPlayerId", "penalty_served_by": "servedByPlayerId",
}
SKATER_SOURCE_FIELDS = ("toi", "shifts", "goals", "assists", "sog", "blockedShots", "points", "plusMinus", "pim", "hits",
    "powerPlayGoals", "giveaways", "takeaways", "faceoffWinningPctg")
GOALIE_SOURCE_FIELDS = ("toi", "starter", "decision", "saves", "shotsAgainst", "goalsAgainst", "savePctg", "saveShotsAgainst",
    "evenStrengthShotsAgainst", "powerPlayShotsAgainst", "shorthandedShotsAgainst", "evenStrengthGoalsAgainst",
    "powerPlayGoalsAgainst", "shorthandedGoalsAgainst", "pim")
RECORDING_FIELDS = ("venue", "venueLocation", "startTimeUTC", "easternUTCOffset", "venueUTCOffset", "venueTimezone")
SUMMARY_RECORDING_FIELDS = ("reported_date", "reported_start", "reported_end", "attendance", "venue", "officials")


def _issue(issues: list[Issue], source: str, path: str, code: str, message: str) -> None:
    issues.append({"code": code, "source": source, "path": path, "message": message})


def _integer(value: Any, source: str, path: str, issues: list[Issue], minimum: int | None = 0, *, required: bool = False) -> int | None:
    if value is None and not required:
        return None
    if type(value) is int and (minimum is None or value >= minimum):
        return value
    requirement = "integer" if minimum is None else f"integer >= {minimum}"
    _issue(issues, source, path, "invalid_integer", f"expected {requirement}; selected value unavailable")
    return None


def _text(value: Any, source: str, path: str, issues: list[Issue]) -> str | None:
    if value is None or isinstance(value, str):
        return value
    _issue(issues, source, path, "invalid_string", "expected string; selected value unavailable")
    return None


def _fraction(value: Any, source: str, path: str, issues: list[Issue]) -> int | float | None:
    if value is None:
        return None
    if type(value) in (int, float) and 0 <= value <= 1 and math.isfinite(value):
        return value
    _issue(issues, source, path, "invalid_fraction", "expected finite fraction in [0,1]; selected value unavailable")
    return None


def _boolean(value: Any, source: str, path: str, issues: list[Issue]) -> bool | None:
    if value is None or type(value) is bool:
        return value
    _issue(issues, source, path, "invalid_boolean", "expected boolean; selected value unavailable")
    return None


def source_fields(values: dict[str, Any], source: str, input_index: int,
                  paths: dict[str, str], issues: list[Issue]) -> SourceFields:
    """locate selected source values and retain a problem for every null."""
    evidence = [{"source": source, "path": paths[field], "input_index": input_index} for field in values]
    messages = {issue["path"]: issue["message"] for issue in issues if issue["source"] == source}
    problems = {field: {"status": "unavailable", "reason": messages.get(paths[field], "source field missing or null"),
                        "evidence_refs": [index]}
                for index, (field, value) in enumerate(values.items()) if value is None}
    return {"values": values, "problems": problems, "evidence": evidence}


def _boxscore_features(row: dict[str, Any], goalie: bool, source: str, path: str,
                       input_index: int, issues: list[Issue]) -> tuple[SourceFields, SourceFields]:
    """retain reported totals and derive only arithmetically supported saves."""
    issue_start = len(issues)
    values: dict[str, Any] = {}
    selected_fields = GOALIE_SOURCE_FIELDS if goalie else SKATER_SOURCE_FIELDS
    for field in selected_fields:
        field_path = path + "/" + field
        if field == "starter":
            values[field] = _boolean(row.get(field), source, field_path, issues)
        elif field in ("savePctg", "faceoffWinningPctg"):
            values[field] = _fraction(row.get(field), source, field_path, issues)
        elif field in ("toi", "decision") or field.endswith("ShotsAgainst"):
            values[field] = _text(row.get(field), source, field_path, issues)
        else:
            values[field] = _integer(row.get(field), source, field_path, issues, None if field == "plusMinus" else 0)
    facts = source_fields(values, source, input_index, {field: path + "/" + field for field in values}, issues[issue_start:])
    derived: SourceFields = {"values": {}, "problems": {}, "evidence": []}
    if goalie:
        pairs: dict[str, tuple[int, int] | None] = {}
        for field in ("saveShotsAgainst", "evenStrengthShotsAgainst", "powerPlayShotsAgainst", "shorthandedShotsAgainst"):
            raw = values[field]
            match = re.fullmatch(r"([0-9]+)/([0-9]+)", raw) if raw is not None else None
            pair = (int(match[1]), int(match[2])) if match is not None else None
            if pair is not None and pair[0] > pair[1]:
                pair = None
            pairs[field] = pair
            if raw is not None and pair is None:
                _issue(issues, source, path + "/" + field, "invalid_goalie_ratio",
                       "expected saves/shots with numerator no greater than denominator; reported string retained")
            goals_field = "goalsAgainst" if field == "saveShotsAgainst" else field.replace("Shots", "Goals")
            goals = values[goals_field]
            if pair is not None and goals is not None and pair[1] - pair[0] != goals:
                _issue(issues, source, path + "/" + field, "goalie_ratio_conflict",
                       "shots minus saves disagrees with reported goals against; source observations retained")
        overall = pairs["saveShotsAgainst"]
        if overall is not None:
            if ((values["saves"] is not None and overall[0] != values["saves"])
                    or (values["shotsAgainst"] is not None and overall[1] != values["shotsAgainst"])):
                _issue(issues, source, path + "/saveShotsAgainst", "goalie_total_conflict",
                       "formatted saves/shots disagrees with reported scalar totals; source observations retained")
            percentage = values["savePctg"]
            if percentage is not None and (overall[1] == 0 or abs(percentage - overall[0] / overall[1]) > 0.000001):
                _issue(issues, source, path + "/savePctg", "goalie_percentage_conflict",
                       "reported save fraction disagrees with formatted saves/shots; source observations retained")
        for field, derived_name in (("evenStrengthShotsAgainst", "even_strength_saves"), ("powerPlayShotsAgainst", "power_play_saves"), ("shorthandedShotsAgainst", "shorthanded_saves")):
            goals_field = field.replace("Shots", "Goals")
            pair, goals = pairs[field], values[goals_field]
            conflict = pair is not None and goals is not None and pair[1] - pair[0] != goals
            derived["values"][derived_name] = pair[0] if pair is not None and goals is not None and not conflict else None
            evidence_start = len(derived["evidence"])
            derived["evidence"].extend({"source": source, "path": path + "/" + selected, "input_index": input_index}
                                       for selected in (field, goals_field))
            if derived["values"][derived_name] is None:
                derived["problems"][derived_name] = {"status": "conflict" if conflict else "unavailable",
                    "reason": "reported strength saves/shots and goals disagree" if conflict else "supported strength saves/shots and goals required",
                    "evidence_refs": [evidence_start, evidence_start + 1]}
    return facts, derived


def _object(value: Any, source: str, path: str, issues: list[Issue]) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    _issue(issues, source, path, "invalid_object", "expected object; selected fields unavailable")
    return None


def _array(value: Any, source: str, path: str, issues: list[Issue]) -> list[Any] | None:
    if isinstance(value, list):
        return value
    _issue(issues, source, path, "unavailable_collection", "expected array; collection unavailable")
    return None


def _team(value: Any, game: Game | None, source: str, path: str, issues: list[Issue], *, required: bool = False) -> int | None:
    team = _integer(value, source, path, issues, 1, required=required)
    if team is not None and (game is None or team not in (game["away_team_id"], game["home_team_id"])):
        _issue(issues, source, path, "unresolved_team", "team is not an admitted game team; assignment unavailable")
        return None
    return team


def clock_seconds(value: str | None, source: str, path: str, issues: list[Issue]) -> int | None:
    if value is None:
        return None
    if re.fullmatch(r"[0-9]+:[0-5][0-9]", value):
        minutes, seconds = value.split(":")
        try:
            return int(minutes) * 60 + int(seconds)
        except ValueError:
            pass
    _issue(issues, source, path, "invalid_clock", "expected minutes:seconds with seconds 00–59; normalized clock unavailable")
    return None


def _elapsed(time: str | None, remaining: str | None, length: int | None,
             source: str, path: str, issues: list[Issue], *, remaining_supplied: bool = False) -> int | None:
    elapsed = clock_seconds(time, source, path + "/timeInPeriod", issues)
    remaining_seconds = clock_seconds(remaining, source, path + "/timeRemaining", issues)
    if length is None:
        return None
    if elapsed is None or elapsed > length or ((remaining_supplied or remaining is not None) and
            (remaining_seconds is None or remaining_seconds + elapsed != length)):
        _issue(issues, source, path, "inconsistent_event_clock", "elapsed and remaining clocks must fit and sum to the period length; elapsed seconds unavailable")
        return None
    return elapsed


def _duplicate_ids(rows: list[Any], field: str, source: str, prefix: str, issues: list[Issue]) -> set[int]:
    seen: set[int] = set()
    duplicates: set[int] = set()
    for row in rows:
        value = row[field]
        if value is None:
            continue
        if value in seen:
            duplicates.add(value)
            locator = row.get("source_path", f"{prefix}/{row.get('source_index')}")
            if "row_id" in row:
                locator += f"[{row['row_id']}]"
            _issue(issues, source, locator, "duplicate_identity", f"repeated {field} {value}; records retained separately")
        seen.add(value)
    return duplicates


def _report_player(sweaters: dict[tuple[int, int], list[RosterRecord]], unresolved: set[int],
                   team: int | None, sweater: int | None) -> int | None:
    if team is None or sweater is None or not 1 <= sweater <= 99:
        return None
    candidates = sweaters.get((team, sweater), [])
    player = candidates[0]["player_id"] if len(candidates) == 1 else None
    return player if player not in unresolved else None


def _identity(body: dict[str, Any], requested: str) -> tuple[Game | None, str | None]:
    if type(body.get("id")) is not int or str(body["id"]) != requested:
        return None, "/id does not identify the requested game; source unavailable"
    if type(body.get("gameType")) is not int or body["gameType"] != 2 or body.get("gameState") != "OFF":
        return None, "/gameType and /gameState must identify a completed regular-season game; source unavailable"
    season = body.get("season")
    if type(season) is not int or not re.fullmatch(r"[0-9]{8}", str(season)):
        return None, "/season must be an eight-digit source integer; source unavailable"
    game_date = body.get("gameDate")
    if not isinstance(game_date, str):
        return None, "/gameDate must be an iso date; source unavailable"
    try:
        if date.fromisoformat(game_date).isoformat() != game_date:
            raise ValueError
    except ValueError:
        return None, "/gameDate must be an iso date; source unavailable"
    away, home = body.get("awayTeam"), body.get("homeTeam")
    if not isinstance(away, dict) or not isinstance(home, dict):
        return None, "/awayTeam and /homeTeam must identify both teams; source unavailable"
    away_id, home_id = away.get("id"), home.get("id")
    if type(away_id) is not int or away_id <= 0 or type(home_id) is not int or home_id <= 0 or away_id == home_id:
        return None, "/awayTeam/id and /homeTeam/id must be distinct positive integers; source unavailable"
    return {"game_id": requested, "season": str(season), "game_type": 2,
            "game_date": game_date, "away_team_id": away_id, "home_team_id": home_id,
            "away_team_abbrev": None, "home_team_abbrev": None}, None


def interpret_game(directory: Path) -> GameDocument:
    captures = [read_capture(directory, source) for source in SOURCES]
    requested_ids = {capture.requested_game_id for capture in captures if capture.requested_game_id is not None}
    if len(requested_ids) != 1:
        raise InputContractError(f"{directory}: capture records must establish one coherent requested game id; repair capture metadata or recapture")
    requested = requested_ids.pop()
    inputs: list[Input] = []
    bodies: dict[str, dict[str, Any]] = {}
    issues: list[Issue] = []
    game: Game | None = None
    for capture in captures:
        entry: Input = {"source": capture.source, "capture_path": str(capture.capture_path),
                        "requested_at": capture.requested_at, "http_status": capture.http_status,
                        "body_sha256": capture.body_sha256, "status": "unavailable", "reason": capture.reason}
        inputs.append(entry)
        if capture.body is None:
            continue
        if capture.source in ("play-report", "game-summary"):
            continue  # report identity depends on the admitted game and roster below.
        try:
            parsed = strict_json(capture.body)
        except (ValueError, UnicodeDecodeError) as error:
            entry["reason"] = f"invalid source json: {error}; source unavailable"
            continue
        if not isinstance(parsed, dict):
            entry["reason"] = "source json must be an object; source unavailable"
            continue
        if capture.source in ("play-by-play", "boxscore", "landing"):
            identity, reason = _identity(parsed, requested)
            if identity is None:
                entry["reason"] = reason
                continue
            if capture.source == "landing":
                if game is None or identity != game:
                    entry["reason"] = "landing identity does not agree with the admitted core game; source unavailable"
                    continue
                bodies[capture.source] = parsed
                entry["status"] = "parsed"
                entry["reason"] = None
                continue
            if game is not None and game != identity:
                raise InputContractError(f"{capture.capture_path}: play-by-play and boxscore disagree on game identity; recapture or repair the conflicting source")
            game = identity
        else:
            rows = parsed.get("data")
            if isinstance(rows, list):
                bad = next((index for index, row in enumerate(rows)
                            if not isinstance(row, dict) or type(row.get("gameId")) is not int
                            or str(row["gameId"]) != requested), None)
                if bad is not None:
                    entry["reason"] = f"/data/{bad}/gameId does not identify the requested game; source unavailable"
                    continue
        bodies[capture.source] = parsed
        entry["status"] = "parsed"
        entry["reason"] = None

    if game is not None:
        for side in ("away", "home"):
            supplied = []
            for source in ("play-by-play", "boxscore"):
                if source in bodies:
                    abbreviation = _text(bodies[source][side + "Team"].get("abbrev"), source,
                                         "/" + side + "Team/abbrev", issues)
                    if abbreviation is not None:
                        supplied.append(abbreviation)
            if len(set(supplied)) <= 1:
                game[side + "_team_abbrev"] = supplied[0] if supplied else None
            else:
                _issue(issues, "game", "/" + side + "_team_abbrev", "conflicting_team_abbreviation",
                       "admitted sources disagree on team abbreviation; numeric identity retained and report admission unavailable")

    results: list[Result] = []
    for source in ("play-by-play", "boxscore"):
        if source not in bodies:
            continue
        body = bodies[source]
        outcome = _object(body["gameOutcome"], source, "/gameOutcome", issues) if body.get("gameOutcome") is not None else None
        results.append({"source": source,
                        "away_score": _integer(body["awayTeam"].get("score"), source, "/awayTeam/score", issues),
                        "home_score": _integer(body["homeTeam"].get("score"), source, "/homeTeam/score", issues),
                        "away_sog": _integer(body["awayTeam"].get("sog"), source, "/awayTeam/sog", issues),
                        "home_sog": _integer(body["homeTeam"].get("sog"), source, "/homeTeam/sog", issues),
                        "last_period_type": _text(outcome.get("lastPeriodType") if outcome is not None else None, source, "/gameOutcome/lastPeriodType", issues)})

    roster: list[RosterRecord] | None = None
    memberships: dict[int, set[int]] = {}
    unresolved_memberships: set[int] = set()
    source = "play-by-play"
    if source in bodies:
        rows = _array(bodies[source].get("rosterSpots"), source, "/rosterSpots", issues)
        if rows is not None:
            roster = []
            for index, value in enumerate(rows):
                path = f"/rosterSpots/{index}"
                row = _object(value, source, path, issues)
                row = row if row is not None else {}
                first = _object(row["firstName"], source, path + "/firstName", issues) if row.get("firstName") is not None else None
                last = _object(row["lastName"], source, path + "/lastName", issues) if row.get("lastName") is not None else None
                record: RosterRecord = {"source_index": index,
                    "player_id": _integer(row.get("playerId"), source, path + "/playerId", issues, 1, required=True),
                    "team_id": _team(row.get("teamId"), game, source, path + "/teamId", issues, required=True),
                    "first_name": _text(first.get("default") if first else None, source, path + "/firstName/default", issues),
                    "last_name": _text(last.get("default") if last else None, source, path + "/lastName/default", issues),
                    "reported_position": _text(row.get("positionCode"), source, path + "/positionCode", issues),
                    "sweater_number": _integer(row.get("sweaterNumber"), source, path + "/sweaterNumber", issues, 1)}
                roster.append(record)
                if record["player_id"] is not None:
                    if record["team_id"] is None:
                        unresolved_memberships.add(record["player_id"])
                    else:
                        memberships.setdefault(record["player_id"], set()).add(record["team_id"])
            unresolved_memberships.update(_duplicate_ids(roster, "player_id", source, "/rosterSpots", issues))

    players: list[BoxscorePlayer] | None = None
    admitted_boxscore_arrays = False
    source = "boxscore"
    if source in bodies:
        source_input_index = next(i for i, entry in enumerate(inputs) if entry["source"] == source)
        stats = _object(bodies[source].get("playerByGameStats"), source, "/playerByGameStats", issues)
        if stats is not None:
            players = []
            for side, team_key in (("awayTeam", "away_team_id"), ("homeTeam", "home_team_id")):
                side_path = "/playerByGameStats/" + side
                groups = _object(stats.get(side), source, side_path, issues)
                if groups is None:
                    continue
                for group in ("forwards", "defense", "goalies"):
                    group_path = side_path + "/" + group
                    rows = _array(groups.get(group), source, group_path, issues)
                    if rows is None:
                        continue
                    admitted_boxscore_arrays = True
                    for index, value in enumerate(rows):
                        path = f"{group_path}/{index}"
                        row = _object(value, source, path, issues)
                        row = row if row is not None else {}
                        name = _object(row["name"], source, path + "/name", issues) if row.get("name") is not None else None
                        assert game is not None
                        facts, derived = _boxscore_features(row, group == "goalies", source, path,
                                                              source_input_index, issues)
                        toi = facts["values"]["toi"]
                        players.append({"source_path": path, "player_id": _integer(row.get("playerId"), source, path + "/playerId", issues, 1, required=True),
                            "team_id": game[team_key], "name": _text(name.get("default") if name else None, source, path + "/name/default", issues),
                            "reported_position": _text(row.get("position"), source, path + "/position", issues),
                            "toi": toi, "toi_seconds": clock_seconds(toi, source, path + "/toi", issues),
                            "shift_count": facts["values"].get("shifts"),
                            "goals": facts["values"].get("goals"),
                            "assists": facts["values"].get("assists"),
                            "sog": facts["values"].get("sog"),
                            "blocked_shots": facts["values"].get("blockedShots"),
                            "source_fields": facts, "derived_fields": derived})
            _duplicate_ids(players, "player_id", source, "/playerByGameStats", issues)
            if not admitted_boxscore_arrays:
                players = None

    events: list[Event] | None = None
    goal_counts_available = True
    shot_counts_available = True
    counts = {"away": 0, "home": 0}
    shots = {"away": 0, "home": 0}
    source = "play-by-play"
    if source in bodies:
        rows = _array(bodies[source].get("plays"), source, "/plays", issues)
        if rows is not None:
            events = []
            for index, value in enumerate(rows):
                path = f"/plays/{index}"
                row = _object(value, source, path, issues)
                row = row if row is not None else {}
                descriptor = _object(row.get("periodDescriptor"), source, path + "/periodDescriptor", issues)
                descriptor = descriptor if descriptor is not None else {}
                details = _object(row["details"], source, path + "/details", issues) if "details" in row else None
                details = details if details is not None else {}
                number = _integer(descriptor.get("number"), source, path + "/periodDescriptor/number", issues, 1, required=True)
                period_type = _text(descriptor.get("periodType"), source, path + "/periodDescriptor/periodType", issues)
                timed = None
                length = None
                if period_type == "REG" and number in (1, 2, 3):
                    timed, length = True, 1200
                elif period_type == "OT" and number == 4:
                    timed, length = True, 300
                elif period_type == "SO" and number == 5:
                    timed = False
                else:
                    _issue(issues, source, path + "/periodDescriptor", "unsupported_period", "unsupported period number/type; timing and complete event counts unavailable")
                time = _text(row.get("timeInPeriod"), source, path + "/timeInPeriod", issues)
                remaining = _text(row.get("timeRemaining"), source, path + "/timeRemaining", issues)
                elapsed = _elapsed(time, remaining, length, source, path, issues,
                                   remaining_supplied=row.get("timeRemaining") is not None)
                roles = {role: _integer(details[field], source, path + "/details/" + field, issues, 1)
                         for role, field in _ROLES.items() if field in details}
                type_key = _text(row.get("typeDescKey"), source, path + "/typeDescKey", issues)
                if type_key in ("giveaway", "takeaway") and "playerId" in details:
                    roles["turnover_player"] = _integer(details["playerId"], source, path + "/details/playerId", issues, 1)
                type_code = _integer(row.get("typeCode"), source, path + "/typeCode", issues, 1, required=True)
                classifiable = type_key in _EVENT_CODES and type_code == _EVENT_CODES[type_key]
                if not classifiable:
                    _issue(issues, source, path, "unclassifiable_event", "event kind/code cannot be classified; timed goal and shot counts unavailable if this is a timed period")
                owner = _team(details.get("eventOwnerTeamId"), game, source, path + "/details/eventOwnerTeamId", issues)
                shooting_team = None
                if type_key in ("goal", "shot-on-goal", "missed-shot", "blocked-shot"):
                    role = "scorer" if type_key == "goal" else "shooter"
                    participant = roles.get(role)
                    teams = memberships.get(participant, set())
                    if len(teams) == 1 and participant not in unresolved_memberships:
                        shooting_team = next(iter(teams))
                    else:
                        _issue(issues, source, path + "/details/" + _ROLES[role], "unresolved_shooting_team", "participant has no unique roster team; shooting team unavailable")
                    if shooting_team is not None and owner is not None and shooting_team != owner:
                        _issue(issues, source, path + "/details/eventOwnerTeamId", "shooting_owner_disagreement", "owner disagrees with participant roster team; both observations retained")
                coordinates = []
                for field in ("xCoord", "yCoord"):
                    coordinate = details.get(field)
                    if coordinate is not None and type(coordinate) not in (int, float):
                        _issue(issues, source, path + "/details/" + field, "invalid_coordinate", "expected finite number; coordinate unavailable")
                        coordinate = None
                    coordinates.append(coordinate)
                event: Event = {"source_index": index,
                    "event_id": _integer(row.get("eventId"), source, path + "/eventId", issues, 1, required=True),
                    "sort_order": _integer(row.get("sortOrder"), source, path + "/sortOrder", issues, required=True),
                    "type_code": type_code, "type_key": type_key, "kind_valid": classifiable,
                    "period_number": number, "period_type": period_type,
                    "time_in_period": time, "time_remaining": remaining, "elapsed_seconds": elapsed, "timed_period": timed,
                    "situation_code": _text(row.get("situationCode"), source, path + "/situationCode", issues),
                    "home_team_defending_side": _text(row.get("homeTeamDefendingSide"), source, path + "/homeTeamDefendingSide", issues),
                    "zone_code": _text(details.get("zoneCode"), source, path + "/details/zoneCode", issues),
                    "owner_team_id": owner, "reported_x": coordinates[0], "reported_y": coordinates[1], "roles": roles,
                    "shooting_team_id": shooting_team,
                    "shot_type": _text(details.get("shotType"), source, path + "/details/shotType", issues),
                    "reason": _text(details.get("reason"), source, path + "/details/reason", issues),
                    "secondary_reason": _text(details.get("secondaryReason"), source, path + "/details/secondaryReason", issues),
                    "penalty_type": _text(details.get("typeCode"), source, path + "/details/typeCode", issues) if type_key == "penalty" else None,
                    "penalty_description": _text(details.get("descKey"), source, path + "/details/descKey", issues) if type_key == "penalty" else None,
                    "penalty_duration_minutes": _integer(details.get("duration"), source, path + "/details/duration", issues) if type_key == "penalty" else None,
                    "away_score": _integer(details.get("awayScore"), source, path + "/details/awayScore", issues),
                    "home_score": _integer(details.get("homeScore"), source, path + "/details/homeScore", issues)}
                events.append(event)
                if timed is None or (timed and not classifiable):
                    goal_counts_available = False
                    shot_counts_available = False
                if timed and type_key in ("goal", "shot-on-goal"):
                    if owner is None:
                        shot_counts_available = False
                        if type_key == "goal":
                            goal_counts_available = False
                        _issue(issues, source, path + "/details/eventOwnerTeamId", "missing_count_owner", "timed counting record has no admitted owner; its goal/shot total unavailable")
                    else:
                        assert game is not None
                        side = "away" if owner == game["away_team_id"] else "home"
                        shots[side] += 1
                        if type_key == "goal":
                            counts[side] += 1
            _duplicate_ids(events, "event_id", source, "/plays", issues)
            _duplicate_ids(events, "sort_order", source, "/plays", issues)

    shifts: list[Shift] | None = None
    checks: list[Check] = []
    complete_shifts = False
    affected_players: set[int] = set()
    unknown_shift_identity = False
    source = "shifts"
    if source in bodies:
        rows = _array(bodies[source].get("data"), source, "/data", issues)
        total = _integer(bodies[source].get("total"), source, "/total", issues)
        received = len(rows) if rows is not None else None
        complete_shifts = received is not None and total is not None and received == total
        checks.append({"name": "shift_collection", "source": source, "status": "unavailable" if received is None or total is None else "match" if complete_shifts else "mismatch",
                       "observed": received, "expected": total, "reason": None if complete_shifts else "shift data or advertised total unavailable" if received is None or total is None else "received records differ from advertised total; per-player reconciliation unavailable"})
        if rows is not None:
            shifts = []
            tuples: set[tuple[int, int, int]] = set()
            for index, value in enumerate(rows):
                path = f"/data/{index}"
                row = _object(value, source, path, issues)
                assert row is not None  # shift identity admission already checked every row.
                type_code = _integer(row.get("typeCode"), source, path + "/typeCode", issues, 1, required=True)
                period = _integer(row.get("period"), source, path + "/period", issues, 1)
                player_id = _integer(row.get("playerId"), source, path + "/playerId", issues, 1, required=type_code == 517)
                team_id = _team(row.get("teamId"), game, source, path + "/teamId", issues, required=type_code == 517)
                record_id = _integer(row.get("id"), source, path + "/id", issues, 1, required=True)
                shift_number = _integer(row.get("shiftNumber"), source, path + "/shiftNumber", issues)
                start = _text(row.get("startTime"), source, path + "/startTime", issues)
                end = _text(row.get("endTime"), source, path + "/endTime", issues)
                duration = _text(row.get("duration"), source, path + "/duration", issues)
                start_seconds = end_seconds = duration_seconds = None
                interval_status: Literal["coherent", "inconsistent", "unavailable", "not_shift"] = "unavailable"
                if type_code == 517:
                    start_seconds = clock_seconds(start, source, path + "/startTime", issues)
                    end_seconds = clock_seconds(end, source, path + "/endTime", issues)
                    duration_seconds = clock_seconds(duration, source, path + "/duration", issues)
                    length = 1200 if period in (1, 2, 3) else 300 if period == 4 else None
                    if (length is None or start_seconds is None or end_seconds is None
                            or not 0 <= start_seconds <= end_seconds <= length):
                        _issue(issues, source, path, "invalid_shift_interval", "shift bounds must be ordered within a supported timed period; normalized bounds unavailable")
                        start_seconds = end_seconds = None
                    elif duration_seconds is None:
                        _issue(issues, source, path + "/duration", "unavailable_shift_duration", "reported duration unavailable; usable bounds retained and coherent shift membership unavailable")
                    elif duration_seconds != end_seconds - start_seconds:
                        interval_status = "inconsistent"
                        _issue(issues, source, path, "inconsistent_shift_duration", "reported duration disagrees with end minus start; bounds retained and coherent shift membership unavailable")
                    else:
                        interval_status = "coherent"
                    if player_id is None:
                        unknown_shift_identity = True
                    elif record_id is None or team_id is None:
                        affected_players.add(player_id)
                    elif period is not None and shift_number is not None:
                        identity = (player_id, period, shift_number)
                        if identity in tuples:
                            affected_players.add(player_id)
                            _issue(issues, source, path, "duplicate_shift_identity", "repeated player/period/shift number; affected player reconciliations unavailable")
                        tuples.add(identity)
                elif type_code == 505:
                    interval_status = "not_shift"
                else:
                    if player_id is None:
                        unknown_shift_identity = True
                    else:
                        affected_players.add(player_id)
                    _issue(issues, source, path + "/typeCode", "unknown_shift_kind", "record may be a shift; affected player reconciliations unavailable")
                shifts.append({"source_index": index, "record_id": record_id, "type_code": type_code,
                    "kind": "shift" if type_code == 517 else "other", "player_id": player_id, "team_id": team_id,
                    "period_number": period, "shift_number": shift_number, "start_time": start, "end_time": end,
                    "duration": duration, "event_number": _integer(row.get("eventNumber"), source, path + "/eventNumber", issues),
                    "event_description": _text(row.get("eventDescription"), source, path + "/eventDescription", issues),
                    "start_seconds": start_seconds, "end_seconds": end_seconds, "duration_seconds": duration_seconds,
                    "interval_status": interval_status})
            duplicate_ids = _duplicate_ids(shifts, "record_id", source, "/data", issues)
            for shift in shifts:
                if shift["record_id"] in duplicate_ids:
                    if shift["player_id"] is None:
                        unknown_shift_identity = True
                    else:
                        affected_players.add(shift["player_id"])
    else:
        checks.append({"name": "shift_collection", "source": source, "status": "unavailable", "observed": None, "expected": None, "reason": "shift source unavailable"})

    for result in results:
        expected = {"away": result["away_score"], "home": result["home_score"]}
        usable = events is not None and goal_counts_available
        observed = dict(counts) if usable else None
        reason = None
        status: Literal["match", "mismatch", "unavailable"] = "unavailable"
        if not usable:
            reason = "complete classifiable play-by-play goals unavailable"
        elif None in expected.values() or result["last_period_type"] not in ("REG", "OT", "SO"):
            reason = "reported final score or supported last period type unavailable"
        else:
            if result["last_period_type"] == "SO":
                match = counts["away"] == counts["home"] and (
                    (expected["away"] == counts["away"] + 1 and expected["home"] == counts["home"])
                    or (expected["home"] == counts["home"] + 1 and expected["away"] == counts["away"]))
            else:
                match = counts == expected
            status = "match" if match else "mismatch"
            if not match:
                reason = "timed goals disagree with this source's reported final accounting"
        checks.append({"name": "timed_goals", "source": result["source"], "status": status, "observed": observed, "expected": expected, "reason": reason})
        for side in ("away", "home"):
            assert game is not None
            expected_shots = result[side + "_sog"]
            observed_shots = shots[side] if events is not None and shot_counts_available else None
            checks.append({"name": "timed_shots", "source": result["source"], "team_id": game[side + "_team_id"],
                "status": "unavailable" if observed_shots is None or expected_shots is None else "match" if observed_shots == expected_shots else "mismatch",
                "observed": observed_shots, "expected": expected_shots,
                "reason": "complete classifiable play-by-play shots or reported shots unavailable" if observed_shots is None or expected_shots is None else None if observed_shots == expected_shots else "timed shots disagree with this source's reported team shots"})

    if players is not None:
        for player in players:
            player_id = player["player_id"]
            player_shifts = [row for row in shifts or [] if row["kind"] == "shift" and row["player_id"] == player_id]
            unavailable = None
            if not complete_shifts:
                unavailable = "complete shift collection unavailable"
            elif unknown_shift_identity:
                unavailable = "shift identity cannot be assigned; player reconciliation unavailable"
            elif player_id is None or player_id in affected_players:
                unavailable = "player or shift identities missing/ambiguous; player reconciliation unavailable"
            elif any(row["team_id"] != player["team_id"] for row in player_shifts):
                unavailable = "shift team disagrees with boxscore team; player reconciliation unavailable"
                for row in player_shifts:
                    if row["team_id"] != player["team_id"]:
                        _issue(issues, "shifts", f"/data/{row['source_index']}/teamId", "player_team_disagreement", unavailable)
            duration_valid = all(row["interval_status"] == "coherent" for row in player_shifts)
            observed_toi = sum(row["duration_seconds"] for row in player_shifts) if unavailable is None and duration_valid else None
            observed_count = len(player_shifts) if unavailable is None else None
            for name, observed_value, expected_value in (("player_toi", observed_toi, player["toi_seconds"]), ("player_shift_count", observed_count, player["shift_count"])):
                reason = unavailable
                if reason is None and observed_value is None:
                    reason = "player has a noncoherent shift interval; duration sum unavailable"
                if reason is None and expected_value is None:
                    reason = "reported boxscore value unavailable"
                status = "unavailable" if observed_value is None or expected_value is None else "match" if observed_value == expected_value else "mismatch"
                if status == "mismatch":
                    reason = "shift records disagree with reported boxscore value"
                checks.append({"name": name, "source": "boxscore", "team_id": player["team_id"], "player_id": player_id,
                    "status": status, "observed": observed_value, "expected": expected_value, "reason": reason})

    report_rows: list[ReportRow] | None = None
    source = "play-report"
    capture = next(record for record in captures if record.source == source)
    entry = next(record for record in inputs if record["source"] == source)
    if capture.body is not None:
        report = extract_report(capture.body)
        for issue in report["issues"]:
            _issue(issues, source, issue["path"], issue["code"], issue["message"])
        admitted = game is not None and bool(report["game_info"]) and bool(report["team_headers"])
        admitted = admitted and not any(issue["code"] == "unsupported_report_structure" for issue in report["issues"])
        for index, cells in enumerate(report["game_info"]):
            if game is None or not report_identity(cells, game["game_date"], requested[-4:]):
                admitted = False
                _issue(issues, source, f"/GameInfo/{index}", "report_identity_disagreement",
                       "report requires matching game date/number and final status; event report unavailable")
        for index, headers in enumerate(report["team_headers"]):
            if (game is None or game["away_team_abbrev"] is None or game["home_team_abbrev"] is None
                    or headers != [game["away_team_abbrev"] + " On Ice", game["home_team_abbrev"] + " On Ice"]):
                admitted = False
                _issue(issues, source, f"/headers/{index}", "report_team_disagreement",
                       "away/home on-ice columns must agree with admitted team abbreviations; event report unavailable")
        if not admitted:
            entry["reason"] = "missing, unsupported or conflicting report identity; event report unavailable"
            if not report["game_info"] or not report["team_headers"]:
                _issue(issues, source, "/", "unavailable_report_identity", entry["reason"])
        else:
            assert game is not None
            entry["status"] = "parsed"
            entry["reason"] = None
            sweaters: dict[tuple[int, int], list[RosterRecord]] = {}
            for record in roster or []:
                if record["team_id"] is not None and record["sweater_number"] is not None:
                    sweaters.setdefault((record["team_id"], record["sweater_number"]), []).append(record)
            report_rows = []
            seen_ids: set[str] = set()
            for row in report["rows"]:
                path = f"/rows/{row['source_index']}[{row['row_id']}]"
                if row["row_id"] in seen_ids:
                    _issue(issues, source, path, "duplicate_report_identity", "repeated html row id; records retained separately")
                seen_ids.add(row["row_id"])
                integers: dict[str, int | None] = {}
                for field in ("event_number", "period_number"):
                    text = row[field]
                    value = int(text) if text is not None and re.fullmatch(r"[0-9]{1,9}", text) else None
                    integers[field] = _integer(value, source, path + "/" + field, issues, 1, required=True)
                period = integers["period_number"]
                length = 1200 if period in (1, 2, 3) else 300 if period == 4 else None
                if period not in (1, 2, 3, 4, 5):
                    _issue(issues, source, path + "/period_number", "unsupported_period", "unsupported report period; elapsed timing unavailable")
                elapsed = _elapsed(row["time_in_period"], row["time_remaining"], length, source, path, issues)
                member_lists: dict[str, list[ReportMember] | None] = {}
                for side in ("away", "home"):
                    extracted = row[side + "_members"]
                    members = None if extracted is None else []
                    for index, member in enumerate(extracted or []):
                        member_path = f"{path}/{side}_members/{index}"
                        text = member["sweater_number"]
                        sweater = int(text) if text is not None and re.fullmatch(r"[0-9]{1,2}", text) else None
                        sweater = _integer(sweater, source, member_path + "/sweater_number", issues, 1, required=True)
                        position = member["reported_position"]
                        if position not in ("C", "L", "R", "D", "F", "G"):
                            _issue(issues, source, member_path + "/reported_position", "unresolved_member_position",
                                   "reported member position is missing or unsupported; category unavailable")
                        player_id = _report_player(sweaters, unresolved_memberships, game[side + "_team_id"], sweater)
                        if player_id is None:
                            _issue(issues, source, member_path + "/player_id", "unresolved_report_sweater",
                                   "jersey has no unique game/team roster identity; reported slot retained without player id")
                        assert members is not None
                        members.append({"sweater_number": sweater, "reported_position": position, "player_id": player_id})
                    member_lists[side] = members
                code = row["event_code"]
                description = row["description"]
                shooting_team = sweater = shooter = shot_type = penalty_shot = None
                if code in ("GOAL", "SHOT", "MISS", "BLOCK") and description is not None:
                    if "Penalty Shot" in description:
                        penalty_shot = True
                    # only the leading identity and explicit comma-delimited type slot are attributed.
                    prefix = r"(\S+) ONGOAL - #([^\s,]+)(?=\s|,)" if code == "SHOT" else r"(\S+) #([^\s,]+)(?=\s|,)"
                    match = re.match(prefix, description)
                    fragments = description.split(",")
                    if match is None:
                        _issue(issues, source, path + "/description", "unsupported_attempt_description",
                               "attempt description has no supported leading team/shooter form; attributed fields unavailable")
                    else:
                        teams = [game[side + "_team_id"] for side in ("away", "home")
                                 if game[side + "_team_abbrev"] == match[1]]
                        shooting_team = teams[0] if len(teams) == 1 else None
                        if shooting_team is None:
                            _issue(issues, source, path + "/shooting_team_id", "unresolved_report_shooting_team",
                                   "supplied shooting abbreviation does not identify one admitted team; identity unavailable")
                        supplied_sweater = int(match[2]) if re.fullmatch(r"[0-9]{1,9}", match[2]) else None
                        sweater = _integer(supplied_sweater, source, path + "/shooter_sweater_number", issues, 1, required=True)
                        shooter = _report_player(sweaters, unresolved_memberships, shooting_team, sweater)
                        if shooter is None:
                            _issue(issues, source, path + "/shooter_id", "unresolved_report_shooter",
                                   "supplied shooter jersey has no unique game/team roster identity; shooter unavailable")
                        penalty_shot = "Penalty Shot" in description
                        type_index = 2 if len(fragments) > 1 and fragments[1].strip() == "Penalty Shot" else 1
                        if len(fragments) > type_index:
                            token = fragments[type_index].strip()
                            # a deficient row can place context where the type should be.
                            context = ("Off. Zone", "Def. Zone", "Neu. Zone", "Wide Left", "Wide Right", "Short",
                                       "Above Crossbar", "Hit Crossbar", "Hit Left Post", "Hit Right Post",
                                       "High and Wide Left", "High and Wide Right", "Failed Bank Attempt", "Failed Attempt",
                                       "Failed Attempt Flub", "Defensive Deflection", "Flub")
                            if (token and token not in context
                                    and not token.startswith(("Assist:", "Assists:", "OPPONENT-BLOCKED BY ", "BLOCKED BY "))
                                    and re.fullmatch(r"[0-9]+(?:\.[0-9]+)? ft\.", token) is None):
                                shot_type = token
                report_rows.append({"source_index": row["source_index"], "row_id": row["row_id"],
                    "event_number": integers["event_number"], "period_number": period,
                    "time_in_period": row["time_in_period"], "time_remaining": row["time_remaining"],
                    "elapsed_seconds": elapsed, "event_code": code, "reported_strength": row["reported_strength"],
                    "description": description, "away_members": member_lists["away"], "home_members": member_lists["home"],
                    "penalty_shot": penalty_shot, "shooting_team_id": shooting_team,
                    "shooter_sweater_number": sweater, "shooter_id": shooter, "shot_type": shot_type})
            _duplicate_ids(report_rows, "event_number", source, "/rows", issues)

    landing_goals: list[LandingGoal] | None = None
    source = "landing"
    if source in bodies:
        entry = next(record for record in inputs if record["source"] == source)
        summary = _object(bodies[source].get("summary"), source, "/summary", issues)
        scoring = _array(summary.get("scoring") if summary is not None else None, source, "/summary/scoring", issues)
        periods = []
        for index, value in enumerate(scoring or []):
            path = f"/summary/scoring/{index}"
            period = _object(value, source, path, issues)
            goals = _array(period.get("goals") if period is not None else None, source, path + "/goals", issues)
            periods.append((path, period, goals))
        if scoring is None or any(goals is None for _, _, goals in periods):
            entry["status"] = "unavailable"
            entry["reason"] = "missing or malformed scoring collection; landing goals unavailable"
        else:
            assert game is not None
            landing_goals = []
            for period_path, period, goals in periods:
                descriptor_path = period_path + "/periodDescriptor"
                descriptor = _object(period.get("periodDescriptor"), source, descriptor_path, issues)
                descriptor = descriptor if descriptor is not None else {}
                number = _integer(descriptor.get("number"), source, descriptor_path + "/number", issues, 1, required=True)
                period_type = _text(descriptor.get("periodType"), source, descriptor_path + "/periodType", issues)
                length = 1200 if period_type == "REG" and number in (1, 2, 3) else 300 if period_type == "OT" and number == 4 else None
                if length is None and not (period_type == "SO" and number == 5):
                    _issue(issues, source, descriptor_path, "unsupported_period",
                           "unsupported period number/type; elapsed exposure unavailable")
                for index, value in enumerate(goals):
                    path = f"{period_path}/goals/{index}"
                    row = _object(value, source, path, issues)
                    row = row if row is not None else {}
                    time = _text(row.get("timeInPeriod"), source, path + "/timeInPeriod", issues)
                    elapsed = _elapsed(time, None, length, source, path, issues)
                    home = row.get("isHome")
                    team = game["home_team_id"] if home is True else game["away_team_id"] if home is False else None
                    if type(home) is not bool:
                        _issue(issues, source, path + "/isHome", "invalid_goal_team",
                               "goal ownership requires a supplied boolean isHome; team unavailable")
                    if "teamAbbrev" in row:
                        abbreviation = _object(row["teamAbbrev"], source, path + "/teamAbbrev", issues)
                        reported = _text(abbreviation.get("default") if abbreviation is not None else None,
                                         source, path + "/teamAbbrev/default", issues)
                        expected = game["home_team_abbrev"] if home is True else game["away_team_abbrev"] if home is False else None
                        if abbreviation is not None and not isinstance(abbreviation.get("default"), str):
                            _issue(issues, source, path + "/teamAbbrev/default", "invalid_goal_team_abbreviation",
                                   "supplied team abbreviation requires a string default; context unavailable")
                        elif reported is not None and expected is not None and reported != expected:
                            _issue(issues, source, path + "/teamAbbrev/default", "goal_team_disagreement",
                                   "supplied abbreviation contradicts admitted goal team; context conflicting")
                        elif reported is not None and expected is None:
                            _issue(issues, source, path + "/teamAbbrev/default", "unavailable_goal_team_abbreviation",
                                   "supplied abbreviation has no admitted comparison; context unavailable")
                    landing_goals.append({"source_path": path,
                        "event_id": _integer(row.get("eventId"), source, path + "/eventId", issues, 1, required=True),
                        "period_number": number, "period_type": period_type, "time_in_period": time,
                        "elapsed_seconds": elapsed, "team_id": team,
                        "credited_scorer_id": _integer(row.get("playerId"), source, path + "/playerId", issues, 1, required=True),
                        "goal_modifier": _text(row.get("goalModifier"), source, path + "/goalModifier", issues)})
            _duplicate_ids(landing_goals, "event_id", source, "/summary/scoring", issues)

    recording_observations: list[SourceObservation] = []
    for source in ("play-by-play", "boxscore", "landing"):
        input_index = next(i for i, entry in enumerate(inputs) if entry["source"] == source)
        body = bodies.get(source)
        values = {}
        paths = {}
        recording_issue_start = len(issues)
        for field in RECORDING_FIELDS:
            path = "/" + field
            supplied = body.get(field) if body is not None else None
            if field in ("venue", "venueLocation"):
                localized = _object(supplied, source, path, issues) if supplied is not None else None
                supplied = localized.get("default") if localized is not None else None
                path += "/default"
            value = _text(supplied, source, path, issues)
            if value is not None and field == "startTimeUTC":
                try:
                    parsed_time = datetime.fromisoformat(value)
                    valid_time = parsed_time.utcoffset() == timezone.utc.utcoffset(parsed_time)
                except ValueError:
                    valid_time = False
                if not valid_time:
                    _issue(issues, source, path, "invalid_scheduled_time", "expected explicitly UTC iso datetime; scheduled time unavailable")
                    value = None
            if value is not None and field in ("easternUTCOffset", "venueUTCOffset") and re.fullmatch(r"[+-](?:[01][0-9]|2[0-3]):[0-5][0-9]", value) is None:
                _issue(issues, source, path, "invalid_utc_offset", "expected signed hours:minutes offset; supplied offset unavailable")
                value = None
            values[field], paths[field] = value, path
        facts = source_fields(values, source, input_index, paths, issues[recording_issue_start:])
        if body is None:
            for problem in facts["problems"].values():
                problem["reason"] = inputs[input_index]["reason"] or "source unavailable"
        recording_observations.append({"source": source, "source_fields": facts})

    source = "game-summary"
    input_index = next(i for i, entry in enumerate(inputs) if entry["source"] == source)
    capture = captures[input_index]
    entry = inputs[input_index]
    values = dict.fromkeys(SUMMARY_RECORDING_FIELDS)
    paths = {field: "/GameInfo" if field != "officials" else "/OFFICIALS" for field in values}
    summary_issue_start = len(issues)
    if capture.body is not None:
        summary = extract_summary(capture.body)
        for issue in summary["issues"]:
            _issue(issues, source, issue["path"], issue["code"], issue["message"])
        admitted = (game is not None and len(summary["game_info"]) == 1
                    and report_identity(summary["game_info"][0], game["game_date"], requested[-4:]))
        if admitted:
            entry["status"], entry["reason"] = "parsed", None
            values, paths = summary["values"], summary["paths"]
        else:
            entry["reason"] = "missing, unsupported or conflicting summary identity; recording fields unavailable"
            _issue(issues, source, "/GameInfo", "report_identity_disagreement", entry["reason"])
    facts = source_fields(values, source, input_index, paths, issues[summary_issue_start:])
    if entry["status"] != "parsed":
        for problem in facts["problems"].values():
            problem["reason"] = entry["reason"] or "summary source unavailable"
    recording_observations.append({"source": source, "source_fields": facts})
    for field in RECORDING_FIELDS:
        supplied = {row["source_fields"]["values"][field] for row in recording_observations
                    if field in row["source_fields"]["values"] and row["source_fields"]["values"][field] is not None}
        if len(supplied) > 1:
            _issue(issues, "game", "/recording/" + field, "recording_field_conflict",
                   "supplied recording sources disagree; source observations retained separately")
    coach_scratch_observations: list[SourceObservation] = []
    for source in ("boxscore", "landing", "game-summary"):
        input_index = next(i for i, entry in enumerate(inputs) if entry["source"] == source)
        facts = source_fields({"coaches": None, "scratches": None}, source, input_index,
                              {"coaches": "/", "scratches": "/"}, [])
        for problem in facts["problems"].values():
            problem["reason"] = ("captured source has no admitted coach/scratch collection" if inputs[input_index]["status"] == "parsed"
                                 else inputs[input_index]["reason"] or "source unavailable")
        coach_scratch_observations.append({"source": source, "source_fields": facts})

    return {"schema_version": 4, "requested_game_id": requested, "inputs": inputs, "game": game,
            "reported_results": results, "roster_records": roster, "boxscore_players": players,
            "events": events, "shift_records": shifts, "report_rows": report_rows, "landing_goals": landing_goals,
            "recording_observations": recording_observations, "coach_scratch_observations": coach_scratch_observations,
            "checks": checks, "issues": issues,
            "uncomputed": ["supported_event_membership", "elapsed_on_ice_membership", "genuine_5v5_exposure",
                           "attacking_coordinates", "shooting_origins"]}
