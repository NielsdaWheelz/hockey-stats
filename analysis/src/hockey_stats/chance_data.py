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
role (F/D/unknown), context (ordered fixed scalar evidence), pre_event_score
({away,home}/null), blocked, goal, reported_x/y, attacking_x/y,
location_kind (block_evidence/recorded_proxy),
status (eligible/out_of_scope/unavailable), reasons, reason_details, source_issues,
season, home_away, shot_type, model_shot_type, credited_scorer_id,
previous_event, shot_type_evidence, goal_modifier_evidence,
classification, source_event, diagnostics.

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
from .interpret import Check, Event, LandingGoal
from .shot_origins import in_rink
from .reconstruct import attacking_coordinates, defending_sides, reconcile_shot_type

_ATTEMPTS = {"blocked-shot", "missed-shot", "shot-on-goal", "goal"}
_IDENTITY = (
    "game_id",
    "season",
    "game_type",
    "game_date",
    "away_team_id",
    "home_team_id",
)
_REASONS = (
    "outside_5v5",
    "membership_unresolved",
    "actor_unavailable",
    "location_unavailable",
    "score_unavailable",
    "type_unavailable",
    "physical_attempt_unresolved",
    "context_unavailable",
)
MODEL_SHOT_TYPES = {
    "wrist": "wrist",
    "snap": "snap",
    "slap": "slap",
    "backhand": "backhand",
    "tip-in": "tip",
    "deflected": "tip",
    "wrap-around": "other",
    "poke": "other",
    "bat": "other",
    "between-legs": "other",
    "cradle": "other",
}
_RESETS = {
    "goal",
    "stoppage",
    "penalty",
    "period-start",
    "period-end",
    "game-end",
    "shootout-complete",
}
_RECENT = {
    "faceoff",
    "hit",
    "giveaway",
    "takeaway",
    "shot-on-goal",
    "missed-shot",
    "blocked-shot",
}


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
        type(value) in (int, float) or value is None,
        location,
        "expected finite number or null",
    )


def _read(path, kind, inputs):
    try:
        data = path.read_bytes()
        value = strict_json(data)
    except (OSError, ValueError) as error:
        raise InputContractError(f"{path}: {error}") from error
    inputs.append(
        {"kind": kind, "path": str(path), "sha256": hashlib.sha256(data).hexdigest()}
    )
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
        type(game["game_type"]) is int
        and game["game_type"] == 2
        and game["game_id"][4:6] == "02",
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
    _require(
        game["away_team_id"] != game["home_team_id"], location, "teams must differ"
    )


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
        _integer(
            receipt["http_status"], loc + "/http_status", nullable=True, minimum=100
        )
        _require(
            receipt["http_status"] is None or receipt["http_status"] <= 599,
            loc,
            "invalid http status",
        )
        _text(receipt["body_sha256"], loc + "/body_sha256", nullable=True)
        _require(
            receipt["body_sha256"] is None
            or re.fullmatch(r"[0-9a-f]{64}", receipt["body_sha256"]),
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
    _require(
        seen == set(sources),
        location,
        "source provenance does not cover declared source set",
    )


def _envelope(value, path, entry):
    """validate consumed contracts before distinguishing missing evidence."""
    _schema(value, str(path), 3, ("interpreted", "reconstruction"))
    interpreted, reconstructed = value["interpreted"], value["reconstruction"]
    _schema(
        interpreted,
        f"{path}/interpreted",
        3,
        (
            "requested_game_id",
            "game",
            "inputs",
            "events",
            "roster_records",
            "report_rows",
            "landing_goals",
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
    conflicts = [
        field for field in _IDENTITY if interpreted["game"][field] != entry[field]
    ]
    _require(
        not conflicts, path, "inventory/game disagreement: " + ", ".join(conflicts)
    )
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
        interpreted["roster_records"],
        f"{path}/interpreted/roster_records",
        nullable=True,
    )
    for i, player in enumerate(roster):
        loc = f"{path}/interpreted/roster_records/{i}"
        _object(player, loc, ("player_id", "team_id", "reported_position"))
        _integer(player["player_id"], loc + "/player_id", nullable=True, minimum=1)
        _integer(player["team_id"], loc + "/team_id", nullable=True, minimum=1)
        _text(player["reported_position"], loc + "/reported_position", nullable=True)
    reports = _indexed(
        _array(
            interpreted["report_rows"], f"{path}/interpreted/report_rows", nullable=True
        ),
        f"{path}/interpreted/report_rows",
    )
    for index, report in reports.items():
        loc = f"{path}/interpreted/report_rows/{index}"
        _object(
            report,
            loc,
            ("shot_type", "shooting_team_id", "shooter_sweater_number", "shooter_id"),
        )
        _text(report["shot_type"], loc + "/shot_type", nullable=True)
        for field in ("shooting_team_id", "shooter_sweater_number", "shooter_id"):
            _integer(report[field], loc + "/" + field, nullable=True, minimum=1)
    landing = {}
    for i, goal in enumerate(
        _array(
            interpreted["landing_goals"],
            f"{path}/interpreted/landing_goals",
            nullable=True,
        )
    ):
        loc = f"{path}/interpreted/landing_goals/{i}"
        _object(goal, loc, LandingGoal.__required_keys__)
        _text(goal["source_path"], loc + "/source_path")
        _require(
            re.fullmatch(r"/summary/scoring/[0-9]+/goals/[0-9]+", goal["source_path"]),
            loc,
            "invalid landing source path",
        )
        _require(
            goal["source_path"] not in landing, loc, "duplicate landing source path"
        )
        landing[goal["source_path"]] = goal
        for field in ("event_id", "period_number", "team_id", "credited_scorer_id"):
            _integer(goal[field], loc + "/" + field, nullable=True, minimum=1)
        _integer(goal["elapsed_seconds"], loc + "/elapsed_seconds", nullable=True)
        for field in ("period_type", "time_in_period", "goal_modifier"):
            _text(goal[field], loc + "/" + field, nullable=True)
    intervals = _array(
        reconstructed["intervals"], f"{path}/reconstruction/intervals", nullable=True
    )
    periods = _array(
        reconstructed["periods"], f"{path}/reconstruction/periods", nullable=True
    )
    for i, period in enumerate(periods):
        loc = f"{path}/reconstruction/periods/{i}"
        _object(period, loc, ("period_number", "end_seconds", "status"))
        _integer(period["period_number"], loc + "/period_number", minimum=1)
        _integer(period["end_seconds"], loc + "/end_seconds", nullable=True)
        _require(
            period["status"] in ("supported", "unavailable"),
            loc,
            "invalid period status",
        )
    for i, check in enumerate(
        _array(interpreted["checks"], f"{path}/interpreted/checks")
    ):
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
                    set(count) == {"away", "home"},
                    loc + "/" + field,
                    "expected away/home counts",
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
                "shot_type_evidence",
                "goal_modifier_evidence",
            ),
        )
        _integer(
            row["report_source_index"], loc + "/report_source_index", nullable=True
        )
        type_evidence = row["shot_type_evidence"]
        if event["type_key"] in _ATTEMPTS:
            evidence_loc = loc + "/shot_type_evidence"
            _object(
                type_evidence,
                evidence_loc,
                ("api_value", "report_value", "value", "status"),
            )
            for field in ("api_value", "report_value", "value"):
                _text(type_evidence[field], evidence_loc + "/" + field, nullable=True)
            _require(
                type_evidence["api_value"] == event["shot_type"],
                evidence_loc,
                "api type observation differs",
            )
            _require(
                type_evidence["status"]
                in (
                    "agreement",
                    "api_only",
                    "report_only",
                    "missing",
                    "conflict",
                    "unsupported",
                    "unmatched",
                ),
                evidence_loc,
                "invalid type evidence status",
            )
            report = reports.get(row["report_source_index"])
            _require(
                type_evidence["report_value"]
                == (report["shot_type"] if report else None),
                evidence_loc,
                "report type observation differs",
            )
            _require(
                type_evidence
                == reconcile_shot_type(
                    event["shot_type"],
                    report["shot_type"] if report else None,
                    report is not None,
                ),
                evidence_loc,
                "incoherent type evidence",
            )
        else:
            _require(
                type_evidence is None, loc, "non-attempt must not carry type evidence"
            )
        modifier = row["goal_modifier_evidence"]
        if event["type_key"] == "goal":
            evidence_loc = loc + "/goal_modifier_evidence"
            _object(modifier, evidence_loc, ("source_path", "reported_value", "status"))
            _text(modifier["source_path"], evidence_loc + "/source_path", nullable=True)
            _text(
                modifier["reported_value"],
                evidence_loc + "/reported_value",
                nullable=True,
            )
            _require(
                modifier["status"]
                in (
                    "reported",
                    "missing",
                    "unavailable",
                    "unmatched",
                    "conflict",
                    "unsupported",
                ),
                evidence_loc,
                "invalid modifier evidence status",
            )
            _require(
                modifier["source_path"] is None
                or re.fullmatch(
                    r"/summary/scoring/[0-9]+/goals/[0-9]+", modifier["source_path"]
                ),
                evidence_loc,
                "invalid landing source path",
            )
            if modifier["source_path"] is not None:
                _require(
                    modifier["source_path"] in landing,
                    evidence_loc,
                    "broken landing source reference",
                )
                counterpart = landing[modifier["source_path"]]
                _require(
                    modifier["reported_value"] == counterpart["goal_modifier"],
                    evidence_loc,
                    "modifier source observation differs",
                )
                _require(
                    counterpart["event_id"] == event["event_id"],
                    evidence_loc,
                    "modifier source event identity differs",
                )
            else:
                _require(
                    modifier["reported_value"] is None,
                    evidence_loc,
                    "unlocated modifier observation",
                )
            if modifier["status"] == "reported":
                _require(
                    modifier["source_path"] is not None
                    and modifier["reported_value"]
                    in ("none", "own-goal", "awarded", "penalty-shot"),
                    evidence_loc,
                    "incoherent reported modifier",
                )
            elif modifier["status"] == "missing":
                _require(
                    modifier["source_path"] is not None
                    and modifier["reported_value"] is None,
                    evidence_loc,
                    "incoherent missing modifier",
                )
            elif modifier["status"] == "unsupported":
                _require(
                    modifier["source_path"] is not None
                    and modifier["reported_value"] is not None
                    and modifier["reported_value"]
                    not in ("none", "own-goal", "awarded", "penalty-shot"),
                    evidence_loc,
                    "incoherent unsupported modifier",
                )
            elif modifier["status"] == "unmatched":
                _require(
                    modifier["source_path"] is None
                    and modifier["reported_value"] is None,
                    evidence_loc,
                    "unmatched modifier cannot name a counterpart",
                )
        else:
            _require(modifier is None, loc, "non-goal must not carry modifier evidence")
        _require(
            row["classification"] in ("five_on_five", "other", "unresolved", "untimed"),
            loc,
            "invalid event classification",
        )
        _require(
            row["coordinate_status"]
            in (
                "normalized",
                "missing_coordinates",
                "unresolved_frame",
                "not_applicable",
            ),
            loc,
            "invalid coordinate status",
        )
        for field in ("attacking_x", "attacking_y"):
            _number(row[field], loc + "/" + field)
        if row["report_source_index"] is not None:
            _require(
                row["report_source_index"] in reports,
                loc,
                "broken report row reference",
            )
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
            _require(
                len(indices) == len(set(indices)),
                loc,
                "duplicate " + field + " reference",
            )
        for field in ("away_goalies", "home_goalies"):
            for actor in _array(row[field], loc + "/" + field, nullable=True):
                _integer(actor, loc + "/" + field, minimum=1)
    return interpreted, reconstructed, events, recon, reports


def _period_length(event):
    if event["timed_period"] is True:
        if event["period_number"] in (1, 2, 3) and event["period_type"] == "REG":
            return 1200
        if event["period_number"] == 4 and event["period_type"] == "OT":
            return 300
    return None


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
            {
                "source": "play-by-play",
                "path": "/events",
                "message": "event collection unavailable",
            }
        )
    orders = [event["sort_order"] for event in events.values()]
    unique_order = None not in orders and len(orders) == len(set(orders))
    order_supported = unique_order
    if not order_supported:
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
        events.values(),
        key=lambda e: e["sort_order"] if e["sort_order"] is not None else -1,
    )
    teams = (game["away_team_id"], game["home_team_id"])
    for event in ordered:
        problem = None
        period = event["period_number"]
        if period is None or period < previous_period:
            problem = "event periods must be known and nondecreasing in sort_order"
            order_supported = False
        elif period is not None:
            previous_period = period
        if event["timed_period"] is True and not event["kind_valid"]:
            failures.append(
                {
                    "source": "play-by-play",
                    "path": f"/events/{event['source_index']}",
                    "message": "event kind cannot exclude an unaccounted timed goal",
                }
            )
        if event["timed_period"] is None:
            problem = "event kind or period cannot exclude an unaccounted timed goal"
        elif event["timed_period"] is True:
            period, seconds = event["period_number"], event["elapsed_seconds"]
            length = _period_length(event)
            if shootout_started:
                problem = "timed play follows shootout evidence"
            elif (
                period is None
                or length is None
                or seconds is not None
                and not (0 <= seconds <= length)
            ):
                problem = "supported timed period/clock required"
            elif (
                seconds is not None
                and previous is not None
                and (period, seconds) < previous
            ):
                problem = "sort_order contradicts period/elapsed chronology"
            elif seconds is not None:
                previous = (period, seconds)
            if event["type_key"] == "goal" and seconds is None:
                failures.append(
                    {
                        "source": "play-by-play",
                        "path": f"/events/{event['source_index']}",
                        "message": "known timed goal clock required for score accounting",
                    }
                )
            if event["type_key"] == "goal" and (
                event["shooting_team_id"] not in teams
                or event["owner_team_id"] != event["shooting_team_id"]
            ):
                failures.append(
                    {
                        "source": "play-by-play",
                        "path": f"/events/{event['source_index']}",
                        "message": "timed goal ownership missing or conflicting",
                    }
                )
        else:
            shootout_started = True
            if event["period_type"] != "SO" or period != 5:
                problem = "untimed event must identify regular-season shootout period 5"
        if problem:
            order_supported = False
            failures.append(
                {
                    "source": "play-by-play",
                    "path": f"/events/{event['source_index']}",
                    "message": problem,
                }
            )
    if failures:
        return {}, failures, ordered if unique_order else None, order_supported
    score = {"away": 0, "home": 0}
    result = {}
    for event in ordered:
        result[event["source_index"]] = dict(score)
        if event["type_key"] == "goal" and event["timed_period"] is True:
            score[
                "away" if event["shooting_team_id"] == game["away_team_id"] else "home"
            ] += 1
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
    return (
        ({}, failures, ordered, order_supported)
        if failures
        else (result, [], ordered, order_supported)
    )


def _previous_event(
    event, predecessor, order_supported, game, players, shooter, period_sides
):
    """the immediate record owns context, including exclusions and reset barriers."""
    result = {
        "status": "unavailable",
        "source_index": None,
        "event_id": None,
        "kind": None,
        "time_gap_seconds": None,
        "owner_team_relation": None,
        "current_attack_x": None,
        "current_attack_y": None,
        "location_basis": None,
        "same_shooter": None,
        "reason": None,
    }
    length, seconds = _period_length(event), event["elapsed_seconds"]
    if predecessor is not None:
        result.update(
            source_index=predecessor["source_index"],
            event_id=predecessor["event_id"],
            kind=predecessor["type_key"],
        )
        prior_length, prior_seconds = (
            _period_length(predecessor),
            predecessor["elapsed_seconds"],
        )
        if (
            prior_length is not None
            and predecessor["period_number"] == event["period_number"]
            and prior_seconds is not None
            and length is not None
            and seconds is not None
            and 0 <= prior_seconds <= prior_length
            and prior_seconds <= seconds <= length
        ):
            result["time_gap_seconds"] = seconds - prior_seconds
    if length is None or seconds is None or not 0 <= seconds <= length:
        result["reason"] = "focal_period_or_clock_unavailable"
        return result
    if not order_supported:
        result["reason"] = "source_order_unavailable"
        return result
    if predecessor is None:
        result.update(status="none", reason="no_predecessor")
        return result
    if (
        prior_length is not None
        and predecessor["period_number"] < event["period_number"]
    ):
        result.update(status="none", reason="period_transition")
        return result
    if predecessor["kind_valid"] and predecessor["type_key"] in _RESETS:
        result.update(status="none", reason="reset_boundary")
        return result
    if (
        prior_length is None
        or predecessor["period_number"] != event["period_number"]
        or prior_seconds is None
        or not 0 <= prior_seconds <= prior_length
        or prior_seconds > seconds
    ):
        result["reason"] = "predecessor_period_or_clock_unavailable"
        return result
    gap = seconds - prior_seconds
    result["time_gap_seconds"] = gap
    if gap > 5:
        result.update(status="none", reason="older_than_five_seconds")
        return result
    problems = []
    kind = predecessor["type_key"]
    if not predecessor["kind_valid"] or kind not in _RECENT:
        problems.append("unsupported_recent_action")
    team = event["shooting_team_id"]
    owner = predecessor["owner_team_id"]
    if owner not in (game["away_team_id"], game["home_team_id"]) or team not in (
        game["away_team_id"],
        game["home_team_id"],
    ):
        problems.append("recent_owner_unavailable")
    else:
        result["owner_team_relation"] = "same" if owner == team else "opponent"
    x, y, frame_reason = attacking_coordinates(predecessor, game, team, period_sides)
    result.update(current_attack_x=x, current_attack_y=y)
    if x is not None and y is not None:
        result["location_basis"] = (
            "block_evidence"
            if kind == "blocked-shot"
            else "recorded_proxy"
            if kind in _ATTEMPTS
            else "recorded_event"
        )
    if frame_reason is not None or x is None or y is None or not in_rink(x, y):
        problems.append("recent_location_or_frame_unavailable")
    if predecessor["kind_valid"] and kind in _ATTEMPTS - {"goal"}:
        prior_shooter = predecessor["roles"].get("shooter")
        identities = players.get(prior_shooter, [])
        if (
            len(identities) != 1
            or identities[0]["team_id"] != predecessor["shooting_team_id"]
            or predecessor["shooting_team_id"]
            not in (game["away_team_id"], game["home_team_id"])
            or owner != predecessor["shooting_team_id"]
        ):
            problems.append("recent_shooter_unavailable")
        elif shooter is None:
            problems.append("focal_shooter_unavailable")
        else:
            result["same_shooter"] = prior_shooter == shooter
    if problems:
        result["reason"] = ",".join(problems)
    else:
        result.update(status="recent")
    return result


def _prepare_game(value, path, entry):
    interpreted, reconstructed, events, recon, reports = _envelope(value, path, entry)
    game = interpreted["game"]
    scores, score_failures, ordered, order_supported = _scores(
        interpreted, events, game
    )
    predecessors = {
        event["source_index"]: ordered[i - 1] if i else None
        for i, event in enumerate(ordered or [])
    }
    period_sides = defending_sides(events.values())
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
        modifier = row["goal_modifier_evidence"]
        landing_penalty = (
            modifier is not None
            and modifier["status"] == "reported"
            and modifier["reported_value"] == "penalty-shot"
        )
        outside = (
            event["timed_period"] is False
            or classification in ("other", "untimed")
            or landing_penalty
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
            else "home"
            if team == game["home_team_id"]
            else None
        )
        opposing = "home" if side == "away" else "away" if side == "home" else None
        credited_scorer = (
            event["roles"].get("scorer") if event["type_key"] == "goal" else None
        )
        physical_resolved = event["type_key"] != "goal" or (
            modifier["status"] == "reported"
            and modifier["reported_value"] in ("none", "penalty-shot")
        )
        if not physical_resolved:
            details["physical_attempt_unresolved"] = [
                {
                    "message": "goal physical action unresolved; credited scorer is retained separately",
                    "goal_modifier_evidence": modifier,
                    "credited_scorer_id": credited_scorer,
                }
            ]
        shooter = (
            credited_scorer
            if event["type_key"] == "goal"
            else event["roles"].get("shooter")
        )
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
        if not physical_resolved:
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
            details["membership_unresolved"] = [
                {"message": "both reported goalies required"}
            ]
        if actor_problems:
            details["actor_unavailable"] = actor_problems
        position = identities[0]["reported_position"] if shooter is not None else None
        role = (
            "F"
            if position in ("C", "L", "R", "F")
            else "D"
            if position == "D"
            else "unknown"
        )
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
        bucket = None
        if before is None or side is None:
            details["score_unavailable"] = score_failures or [
                {"message": "shooting team unavailable for score perspective"}
            ]
        else:
            difference = before[side] - before[opposing]
            bucket = (
                "trailing_2_plus"
                if difference <= -2
                else "trailing_1"
                if difference == -1
                else "leading_2_plus"
                if difference >= 2
                else "leading_1"
                if difference == 1
                else "tied"
            )
        shot_type = row["shot_type_evidence"]["value"]
        model_type = MODEL_SHOT_TYPES.get(shot_type)
        if model_type is None:
            details["type_unavailable"] = [
                {
                    "message": "supported reconciled shot type required; no default or missingness predictor",
                    "shot_type_evidence": row["shot_type_evidence"],
                }
            ]
        previous = _previous_event(
            event,
            predecessors.get(index),
            order_supported,
            game,
            players,
            shooter,
            period_sides,
        )
        length, seconds = _period_length(event), event["elapsed_seconds"]
        minute_band = None
        if length is not None and seconds is not None and 0 <= seconds <= length:
            minute_band = (
                "first"
                if seconds < 60
                else "last"
                if seconds >= length - 60
                else "middle"
            )
        context = {
            "score_bucket": bucket,
            "period": str(event["period_number"])
            if length == 1200
            else "OT"
            if length == 300
            else None,
            "home_away": side,
            "minute_band": minute_band,
            "recent_kind": previous["kind"] if previous["status"] == "recent" else None,
            "recent_team": previous["owner_team_relation"]
            if previous["status"] == "recent"
            else None,
            "recent_delay": previous["time_gap_seconds"]
            if previous["status"] == "recent"
            else None,
            "recent_zone": (
                "attacking" if previous["current_attack_x"] > 25 else "other"
            )
            if previous["status"] == "recent"
            else None,
            "recent_shooter": ("same" if previous["same_shooter"] else "different")
            if previous["status"] == "recent" and previous["same_shooter"] is not None
            else None,
        }
        if previous["status"] == "unavailable":
            details["context_unavailable"] = [
                {
                    "message": "supported recorded preceding-play context required",
                    "previous_event": previous,
                }
            ]
        source_issues = [
            {
                "file": str(path),
                "layer": "reconstruction",
                "index": i,
                **reconstructed["issues"][i],
            }
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
                {**detail, "source_issue_links": source_issues}
                for detail in details[reason]
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
                "credited_scorer_id": credited_scorer,
                "goalie_id": goalie,
                "role": role,
                "context": context,
                "previous_event": previous,
                "pre_event_score": before,
                "blocked": event["type_key"] == "blocked-shot",
                "goal": event["type_key"] == "goal",
                "reported_x": event["reported_x"],
                "reported_y": event["reported_y"],
                "attacking_x": x,
                "attacking_y": y,
                "location_kind": (
                    "block_evidence"
                    if event["type_key"] == "blocked-shot"
                    else "recorded_proxy"
                ),
                "status": "out_of_scope"
                if outside
                else "unavailable"
                if reasons
                else "eligible",
                "reasons": reasons,
                "reason_details": details,
                "source_issues": source_issues,
                "season": game["season"],
                "home_away": side,
                "shot_type": shot_type,
                "model_shot_type": model_type,
                "shot_type_evidence": row["shot_type_evidence"],
                "goal_modifier_evidence": modifier,
                "classification": classification,
                "source_event": event,
                "diagnostics": (
                    ["tip_deflection_recorded_proxy"]
                    if row["shot_type_evidence"]["value"] in ("tip-in", "deflected")
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
    _require(
        selection["purpose"] in ("fixture_exercise", "research"),
        path,
        "unsupported purpose",
    )
    corpora = _array(selection["corpora"], f"{path}/corpora")
    _require(bool(corpora), path, "nonempty explicit corpus selection required")
    selected_ids = set()
    resolved = []
    for i, corpus in enumerate(corpora):
        loc = f"{path}/corpora/{i}"
        _object(corpus, loc, ("path", "game_ids"))
        _require(
            set(corpus) == {"path", "game_ids"},
            loc,
            "unexpected corpus selection fields",
        )
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
            {
                "path": str((path.parent / corpus["path"]).resolve()),
                "game_ids": list(ids),
            }
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
        _provenance(
            reference["inputs"], f"{corpus_path}/reference/inputs", REFERENCE_SOURCES
        )
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
                row,
                loc,
                (
                    "game_id",
                    "inventory_source_index",
                    "status",
                    "reason",
                    "output_path",
                ),
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
                raise InputContractError(
                    f"{corpus_path}/games/{gid}: {status}: {row['reason']}"
                )
            counts = {
                "game_id": gid,
                "game_date": entry["game_date"],
                "corpus_status": status,
                "reason": row["reason"],
                "known_attempts": None,
                "recognized_attempts": None,
                "genuine_five_on_five_attempts": None,
                "chance_2_eligible_attempts": None,
                "goals_by_status": None,
                "excluded_goals_by_reason": None,
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
            prepared, unclassified, evidence = _prepare_game(
                envelope, envelope_path, entry
            )
            attempts.extend(prepared)
            available = evidence["event_collection_available"]
            counts.update(
                {
                    "known_attempts": len(prepared) if available else None,
                    "recognized_attempts": len(prepared) if available else None,
                    "genuine_five_on_five_attempts": sum(
                        a["classification"] == "five_on_five"
                        and a["source_event"]["timed_period"] is True
                        for a in prepared
                    )
                    if available
                    else None,
                    "chance_2_eligible_attempts": sum(
                        a["status"] == "eligible" for a in prepared
                    )
                    if available
                    else None,
                    "goals_by_status": {
                        s: sum(a["goal"] and a["status"] == s for a in prepared)
                        for s in ("eligible", "out_of_scope", "unavailable")
                    }
                    if available
                    else None,
                    "excluded_goals_by_reason": {
                        r: sum(
                            a["goal"]
                            and a["status"] != "eligible"
                            and r in a["reasons"]
                            for a in prepared
                        )
                        for r in _REASONS
                    }
                    if available
                    else None,
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
                g["known_attempts"] is not None
                and not g["attempts_by_status"]["eligible"]
                for g in per_game
            ),
        },
        "games_by_status": {s: corpus_statuses[s] for s in STATUSES},
        "attempts": {
            "known": len(attempts) if contributing else None,
            "recognized_attempts": len(attempts) if contributing else None,
            "genuine_five_on_five_attempts": sum(
                g["genuine_five_on_five_attempts"] for g in contributing
            )
            if contributing
            else None,
            "chance_2_eligible_attempts": by_status["eligible"]
            if contributing
            else None,
            "excluded_goals_by_reason": {
                r: sum(
                    a["goal"] and a["status"] != "eligible" and r in a["reasons"]
                    for a in attempts
                )
                if contributing
                else None
                for r in _REASONS
            },
            "goals_by_status": {
                s: sum(a["goal"] and a["status"] == s for a in attempts)
                if contributing
                else None
                for s in ("eligible", "out_of_scope", "unavailable")
            },
            "usable": by_status["eligible"] if contributing else None,
            "excluded": (
                by_status["out_of_scope"] + by_status["unavailable"]
                if contributing
                else None
            ),
            "missing_games": len(games) - len(contributing),
            "unselected": None,
            "unselected_count_reason": "unselected envelopes not consumed; attempt count unavailable",
            "unclassifiable_source_rows": (
                sum(g["unclassifiable_source_rows"] for g in contributing)
                if contributing
                else None
            ),
        },
        "attempts_by_status": {
            s: by_status[s] if contributing else None
            for s in ("eligible", "out_of_scope", "unavailable")
        },
        "attempts_by_reason": {
            r: sum(r in a["reasons"] for a in attempts) if contributing else None
            for r in _REASONS
        },
        "per_game": per_game,
    }
    return {
        "attempts": attempts,
        "coverage": coverage,
        "inputs": inputs,
        "selection": {
            "schema_version": 1,
            "purpose": selection["purpose"],
            "corpora": resolved,
        },
        "purpose": selection["purpose"],
        "game_dates": game_dates,
        "games": games,
        "input_roots": sorted(input_roots),
    }
