"""prepare selected 02c evidence; no acquisition, reconstruction or fitting.

public contract: prepare(selection_path) returns a finite-json-compatible dict:
  attempts: every recognized attempt, including exclusions, in source order;
  coverage: games_by_status, games/attempts counts and per_game evidence ledger;
  inputs: {kind, path, sha256} for the actual bytes read;
  selection: schema 1 selection with absolute corpus paths;
  purpose: fixture_exercise or research; game_dates: selected id -> inventory date;
  games: selected inventory/status ledger; input_roots: absolute parents.

attempt fields: game_id, source_index, event_id, report_row_id,
report_source_index, interval_indices, shooting_team_id, shooter_id, goalie_id,
role (F/D/unknown), score (trailing/tied/leading/null), pre_event_score
({away,home}/null), blocked, goal, reported_x/y, attacking_x/y,
location_kind (block_evidence/recorded_proxy),
status (eligible/out_of_scope/unavailable), reasons, reason_details, source_issues,
season, home_away, shot_type, classification, source_event, diagnostics.

numerical consumers use status == 'eligible'. all applicable exclusions remain;
source_event is interpreted evidence, never a raw observation. source_issues
include file, layer and original located issue. interval links are diagnostic,
not eligibility requirements. score accounting is all-or-unavailable per game.
local file/schema/reference/identity failures raise InputContractError.
"""

from collections import Counter, defaultdict
from datetime import date
import hashlib
import re
from pathlib import Path

from .captures import InputContractError, REFERENCE_SOURCES, SOURCES, strict_json
from .corpus import STATUSES
from .interpret import Check, Event
from .shot_origins import in_rink

_ATTEMPTS = {"blocked-shot", "missed-shot", "shot-on-goal", "goal"}
_IDENTITY = ("game_id", "season", "game_type", "game_date", "away_team_id", "home_team_id")
_REASONS = (
    "outside_5v5",
    "membership_unresolved",
    "actor_unavailable",
    "location_unavailable",
    "score_unavailable",
)


def _require(condition, location, message):
    if not condition:
        raise InputContractError(f"{location}: {message}")


def _object(value, location, fields):
    _require(type(value) is dict, location, "expected object")
    _require(
        set(fields).issubset(value),
        location,
        "missing fields: " + ", ".join(sorted(set(fields) - value.keys())),
    )
    return value


def _array(value, location, *, nullable=False):
    _require(
        type(value) is list or nullable and value is None,
        location,
        "expected array" + (" or null" if nullable else ""),
    )
    return value or []


def _integer(value, location, *, nullable=False, minimum=0):
    _require(
        type(value) is int and value >= minimum or nullable and value is None,
        location,
        "expected integer" + (" or null" if nullable else ""),
    )


def _text(value, location, *, nullable=False):
    _require(
        type(value) is str or nullable and value is None,
        location,
        "expected string" + (" or null" if nullable else ""),
    )


def _number(value, location):
    # strict_json already rejects non-finite numbers.
    _require(
        type(value) in (int, float) or value is None, location, "expected finite number or null"
    )


def _read(path, kind, inputs):
    try:
        data = path.read_bytes()
        value = strict_json(data)
    except (OSError, ValueError) as error:
        raise InputContractError(f"{path}: {error}") from error
    inputs.append({"kind": kind, "path": str(path), "sha256": hashlib.sha256(data).hexdigest()})
    return value


def _schema(value, location, version, fields):
    _object(value, location, ("schema_version", *fields))
    _require(
        type(value["schema_version"]) is int and value["schema_version"] == version,
        location,
        f"expected schema {version}",
    )


def _game_identity(game, location):
    _object(game, location, _IDENTITY)
    _require(
        type(game["game_id"]) is str and re.fullmatch(r"[0-9]{10}", game["game_id"]),
        location,
        "expected ten-digit game id",
    )
    _require(
        type(game["season"]) is str and re.fullmatch(r"[0-9]{8}", game["season"]),
        location,
        "expected season id",
    )
    _require(
        game["season"] == game["game_id"][:4] + str(int(game["game_id"][:4]) + 1),
        location,
        "season/game id disagreement",
    )
    _require(
        type(game["game_type"]) is int and game["game_type"] == 2 and game["game_id"][4:6] == "02",
        location,
        "expected regular-season identity",
    )
    try:
        valid_date = (
            type(game["game_date"]) is str
            and date.fromisoformat(game["game_date"]).isoformat() == game["game_date"]
        )
    except ValueError:
        valid_date = False
    _require(valid_date, location, "expected calendar date")
    for field in ("away_team_id", "home_team_id"):
        _integer(game[field], f"{location}/{field}", minimum=1)
    _require(game["away_team_id"] != game["home_team_id"], location, "teams must differ")


def _indexed(rows, location):
    result = {}
    for i, row in enumerate(rows):
        loc = f"{location}/{i}"
        _object(row, loc, ("source_index",))
        index = row["source_index"]
        _integer(index, loc + "/source_index")
        _require(index not in result, loc, "duplicate source_index")
        result[index] = row
    return result


def _issues(rows, location):
    rows = _array(rows, location)
    for i, issue in enumerate(rows):
        _object(issue, f"{location}/{i}", ("code", "source", "path", "message"))
        for field in ("code", "source", "path", "message"):
            _text(issue[field], f"{location}/{i}/{field}")
    return rows


def _provenance(rows, location, sources):
    seen = set()
    for i, receipt in enumerate(_array(rows, location)):
        loc = f"{location}/{i}"
        _object(
            receipt,
            loc,
            (
                "source",
                "capture_path",
                "requested_at",
                "http_status",
                "body_sha256",
                "status",
                "reason",
            ),
        )
        _text(receipt["source"], loc + "/source")
        _require(
            receipt["source"] in sources and receipt["source"] not in seen,
            loc,
            "unknown or duplicate source",
        )
        seen.add(receipt["source"])
        _text(receipt["capture_path"], loc + "/capture_path")
        _require(bool(receipt["capture_path"]), loc, "empty provenance path")
        _text(receipt["requested_at"], loc + "/requested_at", nullable=True)
        _integer(receipt["http_status"], loc + "/http_status", nullable=True, minimum=100)
        _require(
            receipt["http_status"] is None or receipt["http_status"] <= 599,
            loc,
            "invalid http status",
        )
        _text(receipt["body_sha256"], loc + "/body_sha256", nullable=True)
        _require(
            receipt["body_sha256"] is None or re.fullmatch(r"[0-9a-f]{64}", receipt["body_sha256"]),
            loc,
            "invalid body digest",
        )
        _require(
            receipt["status"] in ("parsed", "unavailable", "reference_only"),
            loc,
            "invalid source status",
        )
        _require(
            receipt["status"] == "unavailable" or receipt["body_sha256"] is not None,
            loc,
            "consumed source lacks body digest",
        )
        _text(receipt["reason"], loc + "/reason", nullable=True)
    _require(seen == set(sources), location, "source provenance does not cover declared source set")


def _envelope(value, path, entry):
    """validate consumed contracts before distinguishing missing evidence."""
    _schema(value, str(path), 1, ("interpreted", "reconstruction"))
    interpreted, reconstructed = value["interpreted"], value["reconstruction"]
    _schema(
        interpreted,
        f"{path}/interpreted",
        2,
        (
            "requested_game_id",
            "game",
            "inputs",
            "events",
            "roster_records",
            "report_rows",
            "checks",
            "issues",
        ),
    )
    _require(
        interpreted["requested_game_id"] == entry["game_id"],
        path,
        "requested game/inventory disagreement",
    )
    _game_identity(interpreted["game"], f"{path}/interpreted/game")
    conflicts = [field for field in _IDENTITY if interpreted["game"][field] != entry[field]]
    _require(not conflicts, path, "inventory/game disagreement: " + ", ".join(conflicts))
    _provenance(interpreted["inputs"], f"{path}/interpreted/inputs", SOURCES)
    _issues(interpreted["issues"], f"{path}/interpreted/issues")
    _object(
        reconstructed,
        f"{path}/reconstruction",
        ("events", "intervals", "periods", "issues", "coverage"),
    )
    _issues(reconstructed["issues"], f"{path}/reconstruction/issues")
    events = _indexed(
        _array(interpreted["events"], f"{path}/interpreted/events", nullable=True),
        f"{path}/interpreted/events",
    )
    recon = _indexed(
        _array(reconstructed["events"], f"{path}/reconstruction/events", nullable=True),
        f"{path}/reconstruction/events",
    )
    _require(
        events.keys() == recon.keys(),
        path,
        "interpreted/reconstruction event source indices differ",
    )
    roster = _array(
        interpreted["roster_records"], f"{path}/interpreted/roster_records", nullable=True
    )
    for i, player in enumerate(roster):
        loc = f"{path}/interpreted/roster_records/{i}"
        _object(player, loc, ("player_id", "team_id", "reported_position"))
        _integer(player["player_id"], loc + "/player_id", nullable=True, minimum=1)
        _integer(player["team_id"], loc + "/team_id", nullable=True, minimum=1)
        _text(player["reported_position"], loc + "/reported_position", nullable=True)
    reports = _indexed(
        _array(interpreted["report_rows"], f"{path}/interpreted/report_rows", nullable=True),
        f"{path}/interpreted/report_rows",
    )
    intervals = _array(
        reconstructed["intervals"], f"{path}/reconstruction/intervals", nullable=True
    )
    periods = _array(reconstructed["periods"], f"{path}/reconstruction/periods", nullable=True)
    for i, period in enumerate(periods):
        loc = f"{path}/reconstruction/periods/{i}"
        _object(period, loc, ("period_number", "end_seconds", "status"))
        _integer(period["period_number"], loc + "/period_number", minimum=1)
        _integer(period["end_seconds"], loc + "/end_seconds", nullable=True)
        _require(period["status"] in ("supported", "unavailable"), loc, "invalid period status")
    for i, check in enumerate(_array(interpreted["checks"], f"{path}/interpreted/checks")):
        loc = f"{path}/interpreted/checks/{i}"
        _object(check, loc, Check.__required_keys__)
        _text(check["name"], loc + "/name")
        _text(check["reason"], loc + "/reason", nullable=True)
        if "source" in check:
            _text(check["source"], loc + "/source")
        _require(
            check["status"] in ("match", "mismatch", "unavailable"),
            loc,
            "invalid accounting status",
        )
        for field in ("observed", "expected"):
            count = check[field]
            if type(count) is dict:
                _require(
                    set(count) == {"away", "home"}, loc + "/" + field, "expected away/home counts"
                )
                for number in count.values():
                    _integer(number, loc + "/" + field, nullable=True)
            else:
                _integer(count, loc + "/" + field, nullable=True)
    for index, event in events.items():
        loc = f"{path}/interpreted/events/{index}"
        _object(event, loc, Event.__required_keys__)
        for field in (
            "event_id",
            "sort_order",
            "type_code",
            "period_number",
            "elapsed_seconds",
            "shooting_team_id",
            "owner_team_id",
            "penalty_duration_minutes",
            "away_score",
            "home_score",
        ):
            _integer(event[field], loc + "/" + field, nullable=True)
        for field in (
            "type_key",
            "period_type",
            "shot_type",
            "time_in_period",
            "time_remaining",
            "situation_code",
            "home_team_defending_side",
            "zone_code",
            "reason",
            "penalty_type",
        ):
            _text(event[field], loc + "/" + field, nullable=True)
        _require(type(event["kind_valid"]) is bool, loc, "kind_valid must be boolean")
        _require(
            event["timed_period"] is None or type(event["timed_period"]) is bool,
            loc,
            "timed_period must be boolean or null",
        )
        _object(event["roles"], loc + "/roles", ())
        for role, actor in event["roles"].items():
            _integer(actor, loc + "/roles/" + role, nullable=True, minimum=1)
        for field in ("reported_x", "reported_y"):
            _number(event[field], loc + "/" + field)
        row = recon[index]
        loc = f"{path}/reconstruction/events/{index}"
        _object(
            row,
            loc,
            (
                "report_source_index",
                "classification",
                "interval_indices",
                "issue_indices",
                "coordinate_status",
                "attacking_x",
                "attacking_y",
                "away_goalies",
                "home_goalies",
            ),
        )
        _require(
            row["classification"] in ("five_on_five", "other", "unresolved", "untimed"),
            loc,
            "invalid event classification",
        )
        _require(
            row["coordinate_status"]
            in ("normalized", "missing_coordinates", "unresolved_frame", "not_applicable"),
            loc,
            "invalid coordinate status",
        )
        for field in ("attacking_x", "attacking_y"):
            _number(row[field], loc + "/" + field)
        _integer(row["report_source_index"], loc + "/report_source_index", nullable=True)
        if row["report_source_index"] is not None:
            _require(row["report_source_index"] in reports, loc, "broken report row reference")
            report = reports[row["report_source_index"]]
            _object(report, loc + "/report", ("row_id", "penalty_shot"))
            _text(report["row_id"], loc + "/report/row_id")
            _require(
                report["penalty_shot"] is None or type(report["penalty_shot"]) is bool,
                loc,
                "invalid penalty_shot status",
            )
        for field, length in (
            ("interval_indices", len(intervals)),
            ("issue_indices", len(reconstructed["issues"])),
        ):
            indices = _array(row[field], loc + "/" + field)
            for item in indices:
                _integer(item, loc + "/" + field)
                _require(item < length, loc, "broken " + field + " reference")
            _require(len(indices) == len(set(indices)), loc, "duplicate " + field + " reference")
        for field in ("away_goalies", "home_goalies"):
            for actor in _array(row[field], loc + "/" + field, nullable=True):
                _integer(actor, loc + "/" + field, minimum=1)
    return interpreted, reconstructed, events, recon, reports


def _scores(interpreted, events, game):
    """count all strengths before each event; never read post-event scores."""
    failures = []
    for source in ("play-by-play", "boxscore"):
        checks = [
            c
            for c in interpreted["checks"]
            if c["name"] == "timed_goals" and c.get("source") == source
        ]
        if len(checks) != 1 or checks[0]["status"] != "match":
            failures.append(
                {
                    "source": source,
                    "path": "/checks",
                    "message": "unique matching timed_goals check required",
                    "checks": checks,
                }
            )
    if interpreted["events"] is None:
        failures.append(
            {"source": "play-by-play", "path": "/events", "message": "event collection unavailable"}
        )
    orders = [event["sort_order"] for event in events.values()]
    if None in orders or len(orders) != len(set(orders)):
        failures.append(
            {
                "source": "play-by-play",
                "path": "/events",
                "message": "unique sort_order required for every source event",
            }
        )
    previous = None
    previous_period = 0
    shootout_started = False
    ordered = sorted(
        events.values(), key=lambda e: e["sort_order"] if e["sort_order"] is not None else -1
    )
    teams = (game["away_team_id"], game["home_team_id"])
    for event in ordered:
        problem = None
        period = event["period_number"]
        if period is None or period < previous_period:
            problem = "event periods must be known and nondecreasing in sort_order"
        elif period is not None:
            previous_period = period
        if (
            event["timed_period"] is None
            or event["timed_period"] is True
            and not event["kind_valid"]
        ):
            problem = "event kind or period cannot exclude an unaccounted timed goal"
        elif event["timed_period"] is True:
            period, seconds = event["period_number"], event["elapsed_seconds"]
            if shootout_started:
                problem = "timed play follows shootout evidence"
            elif (
                period is None
                or seconds is None
                or event["period_type"] not in ("REG", "OT")
                or not (
                    1 <= period <= 3
                    and event["period_type"] == "REG"
                    and seconds <= 1200
                    or period == 4
                    and event["period_type"] == "OT"
                    and seconds <= 300
                )
            ):
                problem = "supported timed period/clock required"
            elif previous is not None and (period, seconds) < previous:
                problem = "sort_order contradicts period/elapsed chronology"
            else:
                previous = (period, seconds)
            if event["type_key"] == "goal" and (
                event["shooting_team_id"] not in teams
                or event["owner_team_id"] != event["shooting_team_id"]
            ):
                problem = "timed goal ownership missing or conflicting"
        else:
            shootout_started = True
            if event["period_type"] != "SO" or period != 5:
                problem = "untimed event must identify regular-season shootout period 5"
        if problem:
            failures.append(
                {
                    "source": "play-by-play",
                    "path": f"/events/{event['source_index']}",
                    "message": problem,
                }
            )
    if failures:
        return {}, failures
    score = {"away": 0, "home": 0}
    result = {}
    for event in ordered:
        result[event["source_index"]] = dict(score)
        if event["type_key"] == "goal" and event["timed_period"] is True:
            score["away" if event["shooting_team_id"] == game["away_team_id"] else "home"] += 1
    # corroborate the embedded observed totals, not just a stale status label.
    for check in interpreted["checks"]:
        if (
            check["name"] == "timed_goals"
            and check.get("source") in ("play-by-play", "boxscore")
            and check.get("observed") != score
        ):
            failures.append(
                {
                    "source": check["source"],
                    "path": "/checks",
                    "message": "counted timed goals disagree with embedded observed accounting",
                    "check": check,
                }
            )
    return ({}, failures) if failures else (result, [])


def _prepare_game(value, path, entry):
    interpreted, reconstructed, events, recon, reports = _envelope(value, path, entry)
    game = interpreted["game"]
    scores, score_failures = _scores(interpreted, events, game)
    players = defaultdict(list)
    for player in interpreted["roster_records"] or []:
        if player["player_id"] is not None:
            players[player["player_id"]].append(player)
    attempts = []
    for index, event in events.items():
        if not event["kind_valid"] or event["type_key"] not in _ATTEMPTS:
            continue
        row = recon[index]
        report = reports.get(row["report_source_index"])
        details = {}
        classification = row["classification"]
        outside = (
            event["timed_period"] is False
            or classification in ("other", "untimed")
            or report is not None
            and report["penalty_shot"] is True
        )
        if outside:
            details["outside_5v5"] = [
                {
                    "message": "known situation is outside supported timed 5v5",
                    "classification": classification,
                    "period_type": event["period_type"],
                }
            ]
        elif event["timed_period"] is not True or classification != "five_on_five":
            details["membership_unresolved"] = [
                {
                    "message": "supported timed five_on_five event membership unavailable",
                    "classification": classification,
                }
            ]
        team = event["shooting_team_id"]
        side = (
            "away"
            if team == game["away_team_id"]
            else "home" if team == game["home_team_id"] else None
        )
        opposing = "home" if side == "away" else "away" if side == "home" else None
        shooter = event["roles"].get("scorer" if event["type_key"] == "goal" else "shooter")
        identities = players.get(shooter, [])
        actor_problems = []
        if event["owner_team_id"] is not None and event["owner_team_id"] != team:
            actor_problems.append(
                {
                    "message": "reported owner contradicts established shooting team",
                    "owner_team_id": event["owner_team_id"],
                    "shooting_team_id": team,
                }
            )
        if side is None or len(identities) != 1 or identities[0]["team_id"] != team:
            actor_problems.append(
                {
                    "message": "shooting team and unique compatible game-roster shooter required",
                    "shooting_team_id": team,
                    "reported_shooter_id": shooter,
                }
            )
            shooter = None
        goalies = row[opposing + "_goalies"] if opposing is not None else None
        goalie = goalies[0] if goalies is not None and len(goalies) == 1 else None
        goalie_roster = players.get(goalie, [])
        if (
            goalie is None
            or len(goalie_roster) != 1
            or goalie_roster[0]["team_id"] != game[opposing + "_team_id"]
            or goalie_roster[0]["reported_position"] != "G"
            or "goalie" in event["roles"]
            and event["roles"]["goalie"] != goalie
        ):
            actor_problems.append(
                {
                    "message": "unique roster-resolved opposing reported goalie required; supplied goalie must agree",
                    "reported_goalie_ids": goalies,
                    "api_goalie_id": event["roles"].get("goalie"),
                }
            )
            goalie = None
        # both reported goalies define the population, independently of actor resolution.
        if (
            not outside
            and classification == "five_on_five"
            and any(
                row[s + "_goalies"] is None or len(row[s + "_goalies"]) != 1
                for s in ("away", "home")
            )
        ):
            details["membership_unresolved"] = [{"message": "both reported goalies required"}]
        if actor_problems:
            details["actor_unavailable"] = actor_problems
        position = identities[0]["reported_position"] if shooter is not None else None
        role = "F" if position in ("C", "L", "R", "F") else "D" if position == "D" else "unknown"
        x, y = row["attacking_x"], row["attacking_y"]
        location_ok = (
            row["coordinate_status"] == "normalized"
            and x is not None
            and y is not None
            and in_rink(x, y)
        )
        if not location_ok:
            details["location_unavailable"] = [
                {
                    "message": "finite normalized in-rink recorded location required; no clipping",
                    "coordinate_status": row["coordinate_status"],
                    "attacking_x": x,
                    "attacking_y": y,
                }
            ]
        before = scores.get(index)
        category = None
        if before is None or side is None:
            details["score_unavailable"] = score_failures or [
                {"message": "shooting team unavailable for score perspective"}
            ]
        else:
            difference = before[side] - before[opposing]
            category = "trailing" if difference < 0 else "leading" if difference > 0 else "tied"
        source_issues = [
            {"file": str(path), "layer": "reconstruction", "index": i, **reconstructed["issues"][i]}
            for i in row["issue_indices"]
        ]
        for i, issue in enumerate(interpreted["issues"]):
            # preserve exact event issue paths; avoid /plays/1 matching /plays/10.
            prefix = f"/plays/{index}"
            if issue["source"] == "play-by-play" and (
                issue["path"] == prefix or issue["path"].startswith(prefix + "/")
            ):
                source_issues.append(
                    {"file": str(path), "layer": "interpreted", "index": i, **issue}
                )
        for reason in details:
            details[reason] = [
                {**detail, "source_issue_links": source_issues} for detail in details[reason]
            ]
        reasons = [reason for reason in _REASONS if reason in details]
        attempts.append(
            {
                "game_id": game["game_id"],
                "source_index": index,
                "event_id": event["event_id"],
                "report_source_index": row["report_source_index"],
                "report_row_id": report["row_id"] if report else None,
                "interval_indices": row["interval_indices"],
                "shooting_team_id": team,
                "shooter_id": shooter,
                "goalie_id": goalie,
                "role": role,
                "score": category,
                "pre_event_score": before,
                "blocked": event["type_key"] == "blocked-shot",
                "goal": event["type_key"] == "goal",
                "reported_x": event["reported_x"],
                "reported_y": event["reported_y"],
                "attacking_x": x,
                "attacking_y": y,
                "location_kind": (
                    "block_evidence" if event["type_key"] == "blocked-shot" else "recorded_proxy"
                ),
                "status": "out_of_scope" if outside else "unavailable" if reasons else "eligible",
                "reasons": reasons,
                "reason_details": details,
                "source_issues": source_issues,
                "season": game["season"],
                "home_away": side,
                "shot_type": event["shot_type"],
                "classification": classification,
                "source_event": event,
                "diagnostics": (
                    ["tip_deflection_recorded_proxy"]
                    if event["shot_type"] in ("tip-in", "deflected", "deflection")
                    else []
                ),
            }
        )
    return (
        attempts,
        sum(not event["kind_valid"] for event in events.values()),
        {
            "source_inputs": interpreted["inputs"],
            "interpreted_issues": interpreted["issues"],
            "reconstruction_issues": reconstructed["issues"],
            "source_coverage": reconstructed["coverage"],
            "score_support": "unavailable" if score_failures else "supported",
            "score_issues": score_failures,
            "event_collection_available": interpreted["events"] is not None,
        },
    )


def prepare(selection_path):
    """read explicit selected evidence, preserving every exclusion and game gap."""
    path = Path(selection_path).resolve()
    inputs = []
    selection = _read(path, "selection", inputs)
    _schema(selection, str(path), 1, ("purpose", "corpora"))
    _require(
        set(selection) == {"schema_version", "purpose", "corpora"},
        path,
        "unexpected selection fields",
    )
    _require(selection["purpose"] in ("fixture_exercise", "research"), path, "unsupported purpose")
    corpora = _array(selection["corpora"], f"{path}/corpora")
    _require(bool(corpora), path, "nonempty explicit corpus selection required")
    selected_ids = set()
    resolved = []
    for i, corpus in enumerate(corpora):
        loc = f"{path}/corpora/{i}"
        _object(corpus, loc, ("path", "game_ids"))
        _require(set(corpus) == {"path", "game_ids"}, loc, "unexpected corpus selection fields")
        _text(corpus["path"], loc + "/path")
        _require(bool(corpus["path"]), loc, "empty corpus path")
        ids = _array(corpus["game_ids"], loc + "/game_ids")
        _require(bool(ids), loc, "nonempty explicit game_ids required")
        for gid in ids:
            _require(
                type(gid) is str and re.fullmatch(r"[0-9]{10}", gid),
                loc,
                "expected ten-digit string game id",
            )
            _require(gid not in selected_ids, loc, "duplicate selected game id " + gid)
            selected_ids.add(gid)
        resolved.append(
            {"path": str((path.parent / corpus["path"]).resolve()), "game_ids": list(ids)}
        )
    attempts, games, per_game = [], [], []
    game_dates = {}
    inventories = set()
    input_roots = {str(path.parent)}
    for selected in resolved:
        corpus_path = Path(selected["path"])
        input_roots.add(str(corpus_path.parent))
        document = _read(corpus_path, "corpus", inputs)
        _schema(document, str(corpus_path), 1, ("reference", "games"))
        reference = document["reference"]
        _schema(reference, f"{corpus_path}/reference", 1, ("inventory", "inputs"))
        _provenance(reference["inputs"], f"{corpus_path}/reference/inputs", REFERENCE_SOURCES)
        _require(
            reference["inventory"] is not None and document["games"] is not None,
            corpus_path,
            "admitted inventory and corpus game ledger required",
        )
        inventory = {}
        for i, entry in enumerate(
            _array(reference["inventory"], f"{corpus_path}/reference/inventory")
        ):
            loc = f"{corpus_path}/reference/inventory/{i}"
            _game_identity(entry, loc)
            _integer(entry.get("source_index"), loc + "/source_index")
            gid = entry["game_id"]
            _require(gid not in inventory, loc, "duplicate inventory game id")
            inventory[gid] = entry
        ledger = {}
        for i, row in enumerate(_array(document["games"], f"{corpus_path}/games")):
            loc = f"{corpus_path}/games/{i}"
            _object(
                row, loc, ("game_id", "inventory_source_index", "status", "reason", "output_path")
            )
            gid = row["game_id"]
            _require(
                type(gid) is str and gid in inventory and gid not in ledger,
                loc,
                "unknown or duplicate corpus game id",
            )
            _require(
                type(row["inventory_source_index"]) is int
                and row["inventory_source_index"] == inventory[gid]["source_index"],
                loc,
                "inventory source index disagreement",
            )
            _require(row["status"] in STATUSES, loc, "unsupported corpus game status")
            _text(row["reason"], loc + "/reason", nullable=True)
            _text(row["output_path"], loc + "/output_path", nullable=True)
            ledger[gid] = row
        _require(
            ledger.keys() == inventory.keys(),
            corpus_path,
            "corpus ledger does not cover admitted inventory",
        )
        inventories.update(inventory)
        for gid in selected["game_ids"]:
            _require(gid in inventory, corpus_path, "unknown selected game id " + gid)
            entry, row = inventory[gid], ledger[gid]
            status = row["status"]
            game_dates[gid] = entry["game_date"]
            games.append(
                {
                    **entry,
                    "corpus_path": str(corpus_path),
                    "status": status,
                    "reason": row["reason"],
                    "output_path": row["output_path"],
                }
            )
            if status in ("input_error", "identity_mismatch"):
                raise InputContractError(f"{corpus_path}/games/{gid}: {status}: {row['reason']}")
            counts = {
                "game_id": gid,
                "game_date": entry["game_date"],
                "corpus_status": status,
                "reason": row["reason"],
                "known_attempts": None,
                "unclassifiable_source_rows": None,
                "attempts_by_status": None,
                "attempts_by_reason": None,
            }
            per_game.append(counts)
            if status != "reconstructed":
                continue
            _require(
                bool(row["output_path"]),
                corpus_path,
                "reconstructed game lacks envelope reference: " + gid,
            )
            envelope_path = (corpus_path.parent / row["output_path"]).resolve()
            input_roots.add(str(envelope_path.parent))
            envelope = _read(envelope_path, "game", inputs)
            prepared, unclassified, evidence = _prepare_game(envelope, envelope_path, entry)
            attempts.extend(prepared)
            available = evidence["event_collection_available"]
            counts.update(
                {
                    "known_attempts": len(prepared) if available else None,
                    "unclassifiable_source_rows": unclassified if available else None,
                    "attempts_by_status": (
                        {
                            s: sum(a["status"] == s for a in prepared)
                            for s in ("eligible", "out_of_scope", "unavailable")
                        }
                        if available
                        else None
                    ),
                    "attempts_by_reason": (
                        {r: sum(r in a["reasons"] for a in prepared) for r in _REASONS}
                        if available
                        else None
                    ),
                    **evidence,
                }
            )
    by_status = Counter(a["status"] for a in attempts)
    corpus_statuses = Counter(g["status"] for g in games)
    contributing = [g for g in per_game if g["known_attempts"] is not None]
    coverage = {
        "games": {
            "selected": len(games),
            "unselected": len(inventories - selected_ids),
            "missing_capture": corpus_statuses["missing_capture"],
            "identity_unavailable": corpus_statuses["identity_unavailable"],
            "missing": sum(g["known_attempts"] is None for g in per_game),
            "usable": sum(
                bool(g["attempts_by_status"] and g["attempts_by_status"]["eligible"])
                for g in per_game
            ),
            "excluded": sum(
                g["known_attempts"] is not None and not g["attempts_by_status"]["eligible"]
                for g in per_game
            ),
        },
        "games_by_status": {s: corpus_statuses[s] for s in STATUSES},
        "attempts": {
            "known": len(attempts) if contributing else None,
            "usable": by_status["eligible"] if contributing else None,
            "excluded": (
                by_status["out_of_scope"] + by_status["unavailable"] if contributing else None
            ),
            "missing_games": len(games) - len(contributing),
            "unselected": None,
            "unselected_count_reason": "unselected envelopes not consumed; attempt count unavailable",
            "unclassifiable_source_rows": (
                sum(g["unclassifiable_source_rows"] for g in contributing) if contributing else None
            ),
        },
        "attempts_by_status": {
            s: by_status[s] if contributing else None
            for s in ("eligible", "out_of_scope", "unavailable")
        },
        "attempts_by_reason": {
            r: sum(r in a["reasons"] for a in attempts) if contributing else None for r in _REASONS
        },
        "per_game": per_game,
    }
    return {
        "attempts": attempts,
        "coverage": coverage,
        "inputs": inputs,
        "selection": {"schema_version": 1, "purpose": selection["purpose"], "corpora": resolved},
        "purpose": selection["purpose"],
        "game_dates": game_dates,
        "games": games,
        "input_roots": sorted(input_roots),
    }
