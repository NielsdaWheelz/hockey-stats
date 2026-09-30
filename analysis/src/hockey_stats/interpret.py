"""interpret selected captured hockey records without reconstructing exposure."""

from datetime import date
from pathlib import Path
import re
from typing import Any, Literal, NotRequired, TypedDict

from .captures import InputContractError, SOURCES, read_capture, strict_json


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


class Game(TypedDict):
    game_id: str
    season: str
    game_type: int
    game_date: str
    away_team_id: int
    home_team_id: int


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


class Event(TypedDict):
    source_index: int
    event_id: int | None
    sort_order: int | None
    type_code: int | None
    type_key: str | None
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
    penalty_type: str | None
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
    checks: list[Check]
    issues: list[Issue]
    uncomputed: list[str]


# these selected source kinds distinguish counted records from non-attempts.
_EVENT_CODES = {
    "faceoff": 502, "hit": 503, "giveaway": 504, "goal": 505,
    "shot-on-goal": 506, "missed-shot": 507, "blocked-shot": 508,
    "penalty": 509, "stoppage": 516, "period-start": 520,
    "period-end": 521, "shootout-complete": 523, "game-end": 524,
    "takeaway": 525, "delayed-penalty": 535,
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


def _issue(issues: list[Issue], source: str, path: str, code: str, message: str) -> None:
    issues.append({"code": code, "source": source, "path": path, "message": message})


def _integer(value: Any, source: str, path: str, issues: list[Issue], minimum: int = 0, *, required: bool = False) -> int | None:
    if value is None and not required:
        return None
    if type(value) is int and value >= minimum:
        return value
    _issue(issues, source, path, "invalid_integer", f"expected integer >= {minimum}; selected value unavailable")
    return None


def _text(value: Any, source: str, path: str, issues: list[Issue]) -> str | None:
    if value is None or isinstance(value, str):
        return value
    _issue(issues, source, path, "invalid_string", "expected string; selected value unavailable")
    return None


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


def _clock(value: str | None, source: str, path: str, issues: list[Issue]) -> int | None:
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
            _issue(issues, source, locator, "duplicate_identity", f"repeated {field} {value}; records retained separately")
        seen.add(value)
    return duplicates


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
            "game_date": game_date, "away_team_id": away_id, "home_team_id": home_id}, None


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
        if capture.source == "game-summary":
            entry["status"] = "reference_only"
            entry["reason"] = "integrity-checked html; hockey content requires manual inspection"
            continue
        try:
            parsed = strict_json(capture.body)
        except (ValueError, UnicodeDecodeError) as error:
            entry["reason"] = f"invalid source json: {error}; source unavailable"
            continue
        if not isinstance(parsed, dict):
            entry["reason"] = "source json must be an object; source unavailable"
            continue
        if capture.source in ("play-by-play", "boxscore"):
            identity, reason = _identity(parsed, requested)
            if identity is None:
                entry["reason"] = reason
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
                    "reported_position": _text(row.get("positionCode"), source, path + "/positionCode", issues)}
                roster.append(record)
                if record["player_id"] is not None:
                    if record["team_id"] is None:
                        unresolved_memberships.add(record["player_id"])
                    else:
                        memberships.setdefault(record["player_id"], set()).add(record["team_id"])
            _duplicate_ids(roster, "player_id", source, "/rosterSpots", issues)

    players: list[BoxscorePlayer] | None = None
    admitted_boxscore_arrays = False
    source = "boxscore"
    if source in bodies:
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
                        toi = _text(row.get("toi"), source, path + "/toi", issues)
                        assert game is not None
                        players.append({"source_path": path, "player_id": _integer(row.get("playerId"), source, path + "/playerId", issues, 1, required=True),
                            "team_id": game[team_key], "name": _text(name.get("default") if name else None, source, path + "/name/default", issues),
                            "reported_position": _text(row.get("position"), source, path + "/position", issues),
                            "toi": toi, "toi_seconds": _clock(toi, source, path + "/toi", issues),
                            "shift_count": _integer(row.get("shifts"), source, path + "/shifts", issues),
                            "goals": _integer(row.get("goals"), source, path + "/goals", issues),
                            "assists": _integer(row.get("assists"), source, path + "/assists", issues),
                            "sog": _integer(row.get("sog"), source, path + "/sog", issues),
                            "blocked_shots": _integer(row.get("blockedShots"), source, path + "/blockedShots", issues)})
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
                elapsed = _clock(time, source, path + "/timeInPeriod", issues)
                remaining_seconds = _clock(remaining, source, path + "/timeRemaining", issues)
                if timed is not True:
                    elapsed = None
                elif elapsed is None or elapsed > length or (row.get("timeRemaining") is not None and (remaining_seconds is None or remaining_seconds + elapsed != length)):
                    _issue(issues, source, path, "inconsistent_event_clock", "elapsed and remaining clocks must fit and sum to the period length; elapsed seconds unavailable")
                    elapsed = None
                roles = {role: _integer(details[field], source, path + "/details/" + field, issues, 1)
                         for role, field in _ROLES.items() if field in details}
                type_key = _text(row.get("typeDescKey"), source, path + "/typeDescKey", issues)
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
                    "type_code": type_code, "type_key": type_key, "period_number": number, "period_type": period_type,
                    "time_in_period": time, "time_remaining": remaining, "elapsed_seconds": elapsed, "timed_period": timed,
                    "situation_code": _text(row.get("situationCode"), source, path + "/situationCode", issues),
                    "home_team_defending_side": _text(row.get("homeTeamDefendingSide"), source, path + "/homeTeamDefendingSide", issues),
                    "zone_code": _text(details.get("zoneCode"), source, path + "/details/zoneCode", issues),
                    "owner_team_id": owner, "reported_x": coordinates[0], "reported_y": coordinates[1], "roles": roles,
                    "shooting_team_id": shooting_team,
                    "shot_type": _text(details.get("shotType"), source, path + "/details/shotType", issues),
                    "reason": _text(details.get("reason"), source, path + "/details/reason", issues),
                    "penalty_type": _text(details.get("typeCode"), source, path + "/details/typeCode", issues) if type_key == "penalty" else None,
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
                if type_code == 517:
                    start_seconds = _clock(start, source, path + "/startTime", issues)
                    end_seconds = _clock(end, source, path + "/endTime", issues)
                    duration_seconds = _clock(duration, source, path + "/duration", issues)
                    length = 1200 if period in (1, 2, 3) else 300 if period == 4 else None
                    if (length is None or start_seconds is None or end_seconds is None or duration_seconds is None
                            or not 0 <= start_seconds <= end_seconds <= length or duration_seconds != end_seconds - start_seconds):
                        _issue(issues, source, path, "invalid_shift_interval", "shift clocks must fit a supported timed period and duration equal end minus start; normalized interval unavailable")
                        start_seconds = end_seconds = duration_seconds = None
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
                elif type_code is None:
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
                    "start_seconds": start_seconds, "end_seconds": end_seconds, "duration_seconds": duration_seconds})
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
            duration_valid = all(row["duration_seconds"] is not None for row in player_shifts)
            observed_toi = sum(row["duration_seconds"] for row in player_shifts) if unavailable is None and duration_valid else None
            observed_count = len(player_shifts) if unavailable is None else None
            for name, observed_value, expected_value in (("player_toi", observed_toi, player["toi_seconds"]), ("player_shift_count", observed_count, player["shift_count"])):
                reason = unavailable
                if reason is None and observed_value is None:
                    reason = "player has an invalid shift duration; duration sum unavailable"
                if reason is None and expected_value is None:
                    reason = "reported boxscore value unavailable"
                status = "unavailable" if observed_value is None or expected_value is None else "match" if observed_value == expected_value else "mismatch"
                if status == "mismatch":
                    reason = "shift records disagree with reported boxscore value"
                checks.append({"name": name, "source": "boxscore", "team_id": player["team_id"], "player_id": player_id,
                    "status": status, "observed": observed_value, "expected": expected_value, "reason": reason})

    return {"schema_version": 1, "requested_game_id": requested, "inputs": inputs, "game": game,
            "reported_results": results, "roster_records": roster, "boxscore_players": players,
            "events": events, "shift_records": shifts, "checks": checks, "issues": issues,
            "uncomputed": ["on_ice_membership", "genuine_5v5_exposure", "attacking_coordinates", "shooting_origins"]}
