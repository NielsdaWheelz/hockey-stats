"""native corpus/envelope contracts and consumed source identities."""

from datetime import date
import hashlib
import re
from pathlib import Path

from .captures import InputContractError, REFERENCE_SOURCES, SOURCES, strict_json
from .corpus import STATUSES
from .interpret import (
    BoxscorePlayer, Check, Event, GOALIE_SOURCE_FIELDS, LandingGoal,
    RECORDING_FIELDS, Result, SKATER_SOURCE_FIELDS, SUMMARY_RECORDING_FIELDS, Shift, SourceEvidence,
)
from .references import BIO_GOALIE_SOURCE_FIELDS, BIO_INTEGER_SOURCE_FIELDS, BIO_SKATER_SOURCE_FIELDS
from .feature_data import ATTEMPT_KINDS
from .reconstruct import AttemptCoverage, Coverage, LocationCoverage, TimeCoverage, reconcile_shot_type

_ATTEMPTS = ATTEMPT_KINDS
IDENTITY_FIELDS = ("game_id", "season", "game_type", "game_date", "away_team_id", "home_team_id")


def require(condition, location, message):
    if not condition:
        raise InputContractError(f"{location}: {message}")


def object_fields(value, location, fields):
    require(type(value) is dict, location, "expected object")
    require(
        set(fields).issubset(value),
        location,
        "missing fields: " + ", ".join(sorted(set(fields) - value.keys())),
    )
    return value


def array(value, location, *, nullable=False):
    require(
        type(value) is list or nullable and value is None,
        location,
        "expected array" + (" or null" if nullable else ""),
    )
    return value or []


def integer(value, location, *, nullable=False, minimum=0):
    require(
        type(value) is int and value >= minimum or nullable and value is None,
        location,
        "expected integer" + (" or null" if nullable else ""),
    )


def text(value, location, *, nullable=False):
    require(
        type(value) is str or nullable and value is None,
        location,
        "expected string" + (" or null" if nullable else ""),
    )


def _number(value, location):
    # strict_json already rejects non-finite numbers.
    require(
        type(value) in (int, float) or value is None,
        location,
        "expected finite number or null",
    )


def read_document(path, kind, inputs):
    try:
        data = path.read_bytes()
        value = strict_json(data)
    except (OSError, ValueError) as error:
        raise InputContractError(f"{path}: {error}") from error
    inputs.append(
        {"kind": kind, "path": str(path), "sha256": hashlib.sha256(data).hexdigest()}
    )
    return value


def schema(value, location, version, fields):
    object_fields(value, location, ("schema_version",))
    require(
        type(value["schema_version"]) is int and value["schema_version"] == version,
        location,
        f"expected schema {version}",
    )
    object_fields(value, location, fields)


def _game_identity(game, location):
    object_fields(game, location, IDENTITY_FIELDS)
    require(
        type(game["game_id"]) is str and re.fullmatch(r"[0-9]{10}", game["game_id"]),
        location,
        "expected ten-digit game id",
    )
    require(
        type(game["season"]) is str and re.fullmatch(r"[0-9]{8}", game["season"]),
        location,
        "expected season id",
    )
    require(
        game["season"] == game["game_id"][:4] + str(int(game["game_id"][:4]) + 1),
        location,
        "season/game id disagreement",
    )
    require(
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
    require(valid_date, location, "expected calendar date")
    for field in ("away_team_id", "home_team_id"):
        integer(game[field], f"{location}/{field}", minimum=1)
    require(
        game["away_team_id"] != game["home_team_id"], location, "teams must differ"
    )


def _indexed(rows, location):
    result = {}
    for i, row in enumerate(rows):
        loc = f"{location}/{i}"
        object_fields(row, loc, ("source_index",))
        index = row["source_index"]
        integer(index, loc + "/source_index")
        require(index not in result, loc, "duplicate source_index")
        result[index] = row
    return result


def _issues(rows, location):
    rows = array(rows, location)
    for i, issue in enumerate(rows):
        object_fields(issue, f"{location}/{i}", ("code", "source", "path", "message"))
        for field in ("code", "source", "path", "message"):
            text(issue[field], f"{location}/{i}/{field}")
    return rows


def _provenance(rows, location, sources):
    seen = set()
    for i, receipt in enumerate(array(rows, location)):
        loc = f"{location}/{i}"
        object_fields(
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
        text(receipt["source"], loc + "/source")
        require(
            receipt["source"] in sources and receipt["source"] not in seen,
            loc,
            "unknown or duplicate source",
        )
        seen.add(receipt["source"])
        text(receipt["capture_path"], loc + "/capture_path")
        require(bool(receipt["capture_path"]), loc, "empty provenance path")
        text(receipt["requested_at"], loc + "/requested_at", nullable=True)
        integer(
            receipt["http_status"], loc + "/http_status", nullable=True, minimum=100
        )
        require(
            receipt["http_status"] is None or receipt["http_status"] <= 599,
            loc,
            "invalid http status",
        )
        text(receipt["body_sha256"], loc + "/body_sha256", nullable=True)
        require(
            receipt["body_sha256"] is None
            or re.fullmatch(r"[0-9a-f]{64}", receipt["body_sha256"]),
            loc,
            "invalid body digest",
        )
        require(
            receipt["status"] in ("parsed", "unavailable", "reference_only"),
            loc,
            "invalid source status",
        )
        require(
            receipt["status"] == "unavailable" or receipt["body_sha256"] is not None,
            loc,
            "consumed source lacks body digest",
        )
        text(receipt["reason"], loc + "/reason", nullable=True)
    require(
        seen == set(sources),
        location,
        "source provenance does not cover declared source set",
    )


def _source_facts(record, location, inputs, fields, *, links_per_field=1):
    """validate a located source-fact envelope, keeping missing evidence legal."""
    object_fields(record, location, ("values", "problems", "evidence"))
    require(set(record) == {"values", "problems", "evidence"}, location,
             "unexpected source-fact fields")
    values = object_fields(record["values"], location + "/values", ())
    require(set(values) == set(fields), location,
             "source value fields disagree with the declared contract")
    integer_fields = set(BIO_INTEGER_SOURCE_FIELDS) | {
        "playerId", "points", "plusMinus", "pim", "hits", "powerPlayGoals", "giveaways",
        "takeaways", "saves", "shotsAgainst", "goalsAgainst", "evenStrengthGoalsAgainst",
        "powerPlayGoalsAgainst", "shorthandedGoalsAgainst", "shifts", "goals", "assists",
        "sog", "blockedShots", "attendance", "even_strength_saves", "power_play_saves",
        "shorthanded_saves",
    }
    for field, value in values.items():
        if value is None:
            continue
        loc = location + "/values/" + field
        if field == "plusMinus":
            require(type(value) is int, loc, "expected signed integer")
        elif field in integer_fields:
            integer(value, loc, minimum=1 if field == "playerId" else 0)
        elif field == "starter":
            require(type(value) is bool, loc, "expected boolean")
        elif field in ("savePctg", "faceoffWinningPctg"):
            require(type(value) in (int, float) and 0 <= value <= 1, loc,
                     "expected finite source fraction in [0,1]")
        elif field == "officials":
            object_fields(value, loc, ())
            for role, names in value.items():
                text(role, loc)
                for name in array(names, loc + "/" + role):
                    text(name, loc + "/" + role)
        elif field in ("coaches", "scratches"):
            array(value, loc)
        else:
            text(value, loc)
    problems = object_fields(record["problems"], location + "/problems", ())
    evidence = array(record["evidence"], location + "/evidence")
    require(set(problems) == {key for key, value in values.items() if value is None},
             location, "every null requires exactly one located problem")
    field_refs = {field: [] for field in fields}
    for i, item in enumerate(evidence):
        loc = f"{location}/evidence/{i}"
        object_fields(item, loc, SourceEvidence.__required_keys__)
        require(set(item) == SourceEvidence.__required_keys__, loc,
                 "source locator fields disagree with the declared contract")
        text(item["field"], loc + "/field")
        require(item["field"] in field_refs, loc, "locator names an unknown source field")
        field_refs[item["field"]].append(i)
        text(item["source"], loc + "/source")
        text(item["path"], loc + "/path")
        integer(item["input_index"], loc + "/input_index")
        require(item["input_index"] < len(inputs), loc, "broken input reference")
        require(item["source"] == inputs[item["input_index"]]["source"], loc,
                 "source and input reference disagree")
    require(all(len(refs) == links_per_field for refs in field_refs.values()), location,
             "source field locator counts disagree with the declared contract")
    for field, problem in problems.items():
        loc = f"{location}/problems/{field}"
        object_fields(problem, loc, ("status", "reason", "evidence_refs"))
        require(set(problem) == {"status", "reason", "evidence_refs"}, loc,
                 "unexpected problem fields")
        require(problem["status"] in ("unavailable", "conflict", "not_applicable"),
                 loc, "unsupported field problem status")
        text(problem["reason"], loc + "/reason")
        require(bool(problem["reason"]), loc, "empty field problem reason")
        refs = array(problem["evidence_refs"], loc + "/evidence_refs")
        require(bool(refs), loc, "located field problem requires evidence")
        for ref in refs:
            integer(ref, loc + "/evidence_refs")
            require(ref < len(evidence), loc, "broken evidence reference")
        require(len(refs) == links_per_field and set(refs) == set(field_refs[field]), loc,
                 "null problem must name exactly its source field locators")


def validate_envelope(value, path, entry):
    """validate consumed contracts before distinguishing missing evidence."""
    schema(value, str(path), 4, ("interpreted", "reconstruction"))
    interpreted, reconstructed = value["interpreted"], value["reconstruction"]
    schema(
        interpreted,
        f"{path}/interpreted",
        4,
        (
            "requested_game_id",
            "game",
            "inputs",
            "reported_results",
            "events",
            "roster_records",
            "report_rows",
            "landing_goals",
            "boxscore_players",
            "shift_records",
            "recording_observations",
            "coach_scratch_observations",
            "checks",
            "issues",
        ),
    )
    require(
        interpreted["requested_game_id"] == entry["game_id"],
        path,
        "requested game/inventory disagreement",
    )
    _game_identity(interpreted["game"], f"{path}/interpreted/game")
    conflicts = [
        field for field in IDENTITY_FIELDS if interpreted["game"][field] != entry[field]
    ]
    require(
        not conflicts, path, "inventory/game disagreement: " + ", ".join(conflicts)
    )
    _provenance(interpreted["inputs"], f"{path}/interpreted/inputs", SOURCES)
    _issues(interpreted["issues"], f"{path}/interpreted/issues")
    result_sources = set()
    for i, result in enumerate(array(interpreted["reported_results"],
                                      f"{path}/interpreted/reported_results")):
        loc = f"{path}/interpreted/reported_results/{i}"
        object_fields(result, loc, Result.__required_keys__)
        source = result["source"]
        require(source in ("play-by-play", "boxscore") and source not in result_sources,
                 loc + "/source", "unknown or duplicate reported result source")
        result_sources.add(source)
        for field in ("away_score", "home_score", "away_sog", "home_sog"):
            integer(result[field], loc + "/" + field, nullable=True)
        text(result["last_period_type"], loc + "/last_period_type", nullable=True)
    for i, player in enumerate(array(interpreted["boxscore_players"],
                                     f"{path}/interpreted/boxscore_players", nullable=True)):
        loc = f"{path}/interpreted/boxscore_players/{i}"
        object_fields(player, loc, BoxscorePlayer.__required_keys__)
        text(player["source_path"], loc + "/source_path")
        goalie = "/goalies/" in player["source_path"]
        for field in ("player_id", "team_id"):
            integer(player[field], loc + "/" + field, nullable=True, minimum=1)
        for field in ("toi_seconds", "shift_count", "goals", "assists", "sog", "blocked_shots"):
            integer(player[field], loc + "/" + field, nullable=True)
        _source_facts(player["source_fields"], loc + "/source_fields", interpreted["inputs"],
                      GOALIE_SOURCE_FIELDS if goalie else SKATER_SOURCE_FIELDS)
        _source_facts(player["derived_fields"], loc + "/derived_fields", interpreted["inputs"],
                      ("even_strength_saves", "power_play_saves", "shorthanded_saves") if goalie else (),
                      links_per_field=2)
    for i, shift in enumerate(array(interpreted["shift_records"],
                                    f"{path}/interpreted/shift_records", nullable=True)):
        loc = f"{path}/interpreted/shift_records/{i}"
        object_fields(shift, loc, Shift.__required_keys__)
        for field in ("source_index", "start_seconds", "end_seconds", "duration_seconds"):
            integer(shift[field], loc + "/" + field, nullable=field != "source_index")
        require(shift["interval_status"] in ("coherent", "inconsistent", "unavailable", "not_shift"),
                 loc, "unsupported shift interval status")
    recording_sources = set()
    declared_recording_sources = {"play-by-play", "boxscore", "landing", "game-summary"}
    for collection in ("recording_observations", "coach_scratch_observations"):
        for i, row in enumerate(array(interpreted[collection], f"{path}/interpreted/{collection}")):
            loc = f"{path}/interpreted/{collection}/{i}"
            object_fields(row, loc, ("source", "source_fields"))
            require(row["source"] in SOURCES, loc, "unknown source observation")
            if collection == "recording_observations":
                require(row["source"] in declared_recording_sources
                         and row["source"] not in recording_sources, loc,
                         "unknown or duplicate recording source")
                recording_sources.add(row["source"])
            fields = ("coaches", "scratches") if collection == "coach_scratch_observations" else (
                SUMMARY_RECORDING_FIELDS if row["source"] == "game-summary" else RECORDING_FIELDS)
            _source_facts(row["source_fields"], loc + "/source_fields", interpreted["inputs"], fields)
            require(all(item["source"] == row["source"] for item in row["source_fields"]["evidence"]),
                     loc + "/source_fields/evidence", "observation source and field evidence disagree")
    require(recording_sources == declared_recording_sources,
             f"{path}/interpreted/recording_observations",
             "recording observations must cover the native source set")
    object_fields(
        reconstructed,
        f"{path}/reconstruction",
        ("events", "intervals", "periods", "issues", "coverage"),
    )
    coverage_loc = f"{path}/reconstruction/coverage"
    coverage = object_fields(reconstructed["coverage"], coverage_loc, Coverage.__required_keys__)
    require(set(coverage) == Coverage.__required_keys__, coverage_loc, "unexpected coverage groups")
    for group, contract, total, parts in (
        ("time", TimeCoverage, "known_seconds", ("five_on_five_seconds", "other_seconds", "unresolved_seconds")),
        ("attempts", AttemptCoverage, "known_timed_attempts", ("five_on_five", "other", "unresolved")),
        ("locations", LocationCoverage, "known_timed_attempts", ("normalized", "missing_coordinates", "unresolved_frame")),
    ):
        loc = coverage_loc + "/" + group
        row = object_fields(coverage[group], loc, contract.__required_keys__)
        require(set(row) == contract.__required_keys__, loc, "unexpected coverage fields")
        for field in sorted(contract.__required_keys__ - {"expected_periods", "supported_periods"}):
            integer(row[field], loc + "/" + field, nullable=True)
            require((row[field] is None) == (row[total] is None), loc + "/" + field,
                     "coverage count availability differs from total")
        if row[total] is not None:
            require(row[total] == sum(row[field] for field in parts), loc,
                     "coverage partition does not sum to total")
    time = coverage["time"]
    for field in ("expected_periods", "supported_periods"):
        loc = coverage_loc + "/time/" + field
        numbers = array(time[field], loc, nullable=field == "expected_periods")
        for number in numbers:
            integer(number, loc, minimum=1)
        require(len(numbers) == len(set(numbers)), loc, "duplicate coverage period")
    require(set(time["supported_periods"]) <= set(time["expected_periods"] or []),
             coverage_loc + "/time", "supported periods absent from expected periods")
    require((time["known_seconds"] is not None) == bool(time["supported_periods"]),
             coverage_loc + "/time", "elapsed coverage availability differs from supported periods")
    attempts = coverage["attempts"]
    require(attempts["known_timed_attempts"] == coverage["locations"]["known_timed_attempts"],
             coverage_loc, "attempt and location totals disagree")
    if attempts["linked_five_on_five"] is not None:
        require(attempts["linked_five_on_five"] <= attempts["five_on_five"],
                 coverage_loc + "/attempts", "linked 5v5 attempts exceed 5v5 attempts")
    _issues(reconstructed["issues"], f"{path}/reconstruction/issues")
    events = _indexed(
        array(interpreted["events"], f"{path}/interpreted/events", nullable=True),
        f"{path}/interpreted/events",
    )
    recon = _indexed(
        array(reconstructed["events"], f"{path}/reconstruction/events", nullable=True),
        f"{path}/reconstruction/events",
    )
    require(
        events.keys() == recon.keys(),
        path,
        "interpreted/reconstruction event source indices differ",
    )
    roster = array(
        interpreted["roster_records"],
        f"{path}/interpreted/roster_records",
        nullable=True,
    )
    for i, player in enumerate(roster):
        loc = f"{path}/interpreted/roster_records/{i}"
        object_fields(player, loc, ("player_id", "team_id", "reported_position"))
        integer(player["player_id"], loc + "/player_id", nullable=True, minimum=1)
        integer(player["team_id"], loc + "/team_id", nullable=True, minimum=1)
        text(player["reported_position"], loc + "/reported_position", nullable=True)
    reports = _indexed(
        array(
            interpreted["report_rows"], f"{path}/interpreted/report_rows", nullable=True
        ),
        f"{path}/interpreted/report_rows",
    )
    for index, report in reports.items():
        loc = f"{path}/interpreted/report_rows/{index}"
        object_fields(
            report,
            loc,
            ("shot_type", "shooting_team_id", "shooter_sweater_number", "shooter_id"),
        )
        text(report["shot_type"], loc + "/shot_type", nullable=True)
        for field in ("shooting_team_id", "shooter_sweater_number", "shooter_id"):
            integer(report[field], loc + "/" + field, nullable=True, minimum=1)
    landing = {}
    for i, goal in enumerate(
        array(
            interpreted["landing_goals"],
            f"{path}/interpreted/landing_goals",
            nullable=True,
        )
    ):
        loc = f"{path}/interpreted/landing_goals/{i}"
        object_fields(goal, loc, LandingGoal.__required_keys__)
        text(goal["source_path"], loc + "/source_path")
        require(
            re.fullmatch(r"/summary/scoring/[0-9]+/goals/[0-9]+", goal["source_path"]),
            loc,
            "invalid landing source path",
        )
        require(
            goal["source_path"] not in landing, loc, "duplicate landing source path"
        )
        landing[goal["source_path"]] = goal
        for field in ("event_id", "period_number", "team_id", "credited_scorer_id"):
            integer(goal[field], loc + "/" + field, nullable=True, minimum=1)
        integer(goal["elapsed_seconds"], loc + "/elapsed_seconds", nullable=True)
        for field in ("period_type", "time_in_period", "goal_modifier"):
            text(goal[field], loc + "/" + field, nullable=True)
    intervals = array(
        reconstructed["intervals"], f"{path}/reconstruction/intervals", nullable=True
    )
    periods = array(
        reconstructed["periods"], f"{path}/reconstruction/periods", nullable=True
    )
    for i, period in enumerate(periods):
        loc = f"{path}/reconstruction/periods/{i}"
        object_fields(period, loc, ("period_number", "end_seconds", "status"))
        integer(period["period_number"], loc + "/period_number", minimum=1)
        integer(period["end_seconds"], loc + "/end_seconds", nullable=True)
        require(
            period["status"] in ("supported", "unavailable"),
            loc,
            "invalid period status",
        )
    for i, check in enumerate(
        array(interpreted["checks"], f"{path}/interpreted/checks")
    ):
        loc = f"{path}/interpreted/checks/{i}"
        object_fields(check, loc, Check.__required_keys__)
        text(check["name"], loc + "/name")
        text(check["reason"], loc + "/reason", nullable=True)
        if "source" in check:
            text(check["source"], loc + "/source")
        require(
            check["status"] in ("match", "mismatch", "unavailable"),
            loc,
            "invalid accounting status",
        )
        for field in ("observed", "expected"):
            count = check[field]
            if type(count) is dict:
                require(
                    set(count) == {"away", "home"},
                    loc + "/" + field,
                    "expected away/home counts",
                )
                for number in count.values():
                    integer(number, loc + "/" + field, nullable=True)
            else:
                integer(count, loc + "/" + field, nullable=True)
    for index, event in events.items():
        loc = f"{path}/interpreted/events/{index}"
        object_fields(event, loc, Event.__required_keys__)
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
            integer(event[field], loc + "/" + field, nullable=True)
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
            "secondary_reason",
            "penalty_description",
        ):
            text(event[field], loc + "/" + field, nullable=True)
        require(type(event["kind_valid"]) is bool, loc, "kind_valid must be boolean")
        require(
            event["timed_period"] is None or type(event["timed_period"]) is bool,
            loc,
            "timed_period must be boolean or null",
        )
        object_fields(event["roles"], loc + "/roles", ())
        for role, actor in event["roles"].items():
            integer(actor, loc + "/roles/" + role, nullable=True, minimum=1)
        for field in ("reported_x", "reported_y"):
            _number(event[field], loc + "/" + field)
        row = recon[index]
        loc = f"{path}/reconstruction/events/{index}"
        object_fields(
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
        integer(
            row["report_source_index"], loc + "/report_source_index", nullable=True
        )
        type_evidence = row["shot_type_evidence"]
        if event["type_key"] in _ATTEMPTS:
            evidence_loc = loc + "/shot_type_evidence"
            object_fields(
                type_evidence,
                evidence_loc,
                ("api_value", "report_value", "value", "status"),
            )
            for field in ("api_value", "report_value", "value"):
                text(type_evidence[field], evidence_loc + "/" + field, nullable=True)
            require(
                type_evidence["api_value"] == event["shot_type"],
                evidence_loc,
                "api type observation differs",
            )
            require(
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
            require(
                type_evidence["report_value"]
                == (report["shot_type"] if report else None),
                evidence_loc,
                "report type observation differs",
            )
            require(
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
            require(
                type_evidence is None, loc, "non-attempt must not carry type evidence"
            )
        modifier = row["goal_modifier_evidence"]
        if event["type_key"] == "goal":
            evidence_loc = loc + "/goal_modifier_evidence"
            object_fields(modifier, evidence_loc, ("source_path", "reported_value", "status"))
            text(modifier["source_path"], evidence_loc + "/source_path", nullable=True)
            text(
                modifier["reported_value"],
                evidence_loc + "/reported_value",
                nullable=True,
            )
            require(
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
            require(
                modifier["source_path"] is None
                or re.fullmatch(
                    r"/summary/scoring/[0-9]+/goals/[0-9]+", modifier["source_path"]
                ),
                evidence_loc,
                "invalid landing source path",
            )
            if modifier["source_path"] is not None:
                require(
                    modifier["source_path"] in landing,
                    evidence_loc,
                    "broken landing source reference",
                )
                counterpart = landing[modifier["source_path"]]
                require(
                    modifier["reported_value"] == counterpart["goal_modifier"],
                    evidence_loc,
                    "modifier source observation differs",
                )
                require(
                    counterpart["event_id"] == event["event_id"],
                    evidence_loc,
                    "modifier source event identity differs",
                )
            else:
                require(
                    modifier["reported_value"] is None,
                    evidence_loc,
                    "unlocated modifier observation",
                )
            if modifier["status"] == "reported":
                require(
                    modifier["source_path"] is not None
                    and modifier["reported_value"]
                    in ("none", "own-goal", "awarded", "penalty-shot"),
                    evidence_loc,
                    "incoherent reported modifier",
                )
            elif modifier["status"] == "missing":
                require(
                    modifier["source_path"] is not None
                    and modifier["reported_value"] is None,
                    evidence_loc,
                    "incoherent missing modifier",
                )
            elif modifier["status"] == "unsupported":
                require(
                    modifier["source_path"] is not None
                    and modifier["reported_value"] is not None
                    and modifier["reported_value"]
                    not in ("none", "own-goal", "awarded", "penalty-shot"),
                    evidence_loc,
                    "incoherent unsupported modifier",
                )
            elif modifier["status"] == "unmatched":
                require(
                    modifier["source_path"] is None
                    and modifier["reported_value"] is None,
                    evidence_loc,
                    "unmatched modifier cannot name a counterpart",
                )
        else:
            require(modifier is None, loc, "non-goal must not carry modifier evidence")
        require(
            row["classification"] in ("five_on_five", "other", "unresolved", "untimed"),
            loc,
            "invalid event classification",
        )
        require(
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
            require(
                row["report_source_index"] in reports,
                loc,
                "broken report row reference",
            )
            report = reports[row["report_source_index"]]
            object_fields(report, loc + "/report", ("row_id", "penalty_shot"))
            text(report["row_id"], loc + "/report/row_id")
            require(
                report["penalty_shot"] is None or type(report["penalty_shot"]) is bool,
                loc,
                "invalid penalty_shot status",
            )
        for field, length in (
            ("interval_indices", len(intervals)),
            ("issue_indices", len(reconstructed["issues"])),
        ):
            indices = array(row[field], loc + "/" + field)
            for item in indices:
                integer(item, loc + "/" + field)
                require(item < length, loc, "broken " + field + " reference")
            require(
                len(indices) == len(set(indices)),
                loc,
                "duplicate " + field + " reference",
            )
        for field in ("away_goalies", "home_goalies"):
            for actor in array(row[field], loc + "/" + field, nullable=True):
                integer(actor, loc + "/" + field, minimum=1)
    return interpreted, reconstructed, events, recon, reports


def load_corpus(path, inputs):
    """admit one complete inventory and its attributed derived-game ledger."""
    document = read_document(path, "corpus", inputs)
    schema(document, str(path), 2, ("reference", "games"))
    reference = document["reference"]
    schema(reference, f"{path}/reference", 2,
            ("requested_season", "inventory", "inputs", "bio_observations", "bio_collections"))
    _provenance(reference["inputs"], f"{path}/reference/inputs", REFERENCE_SOURCES)
    require(reference["inventory"] is not None and document["games"] is not None,
             path, "admitted inventory and corpus game ledger required")
    for i, observation in enumerate(array(reference["bio_observations"],
                                           f"{path}/reference/bio_observations")):
        loc = f"{path}/reference/bio_observations/{i}"
        object_fields(observation, loc, ("source", "source_index", "player_id", "birth_date",
                                  "shoots_catches", "source_fields", "requested_season",
                                  "requested_at", "effective_at"))
        require(observation["source"] in ("skater-bios", "goalie-bios"), loc,
                 "unknown bio observation source")
        integer(observation["source_index"], loc + "/source_index")
        integer(observation["player_id"], loc + "/player_id", nullable=True, minimum=1)
        text(observation["birth_date"], loc + "/birth_date", nullable=True)
        try:
            valid_birth_date = (observation["birth_date"] is None
                or date.fromisoformat(observation["birth_date"]).isoformat() == observation["birth_date"])
        except ValueError:
            valid_birth_date = False
        require(valid_birth_date, loc + "/birth_date", "expected canonical calendar date")
        require(observation["shoots_catches"] in (None, "L", "R"), loc,
                 "unsupported reported hand")
        require(observation["requested_season"] == reference["requested_season"], loc,
                 "bio report season disagreement")
        text(observation["requested_at"], loc + "/requested_at", nullable=True)
        source_input = next(row for row in reference["inputs"] if row["source"] == observation["source"])
        require(observation["requested_at"] == source_input["requested_at"], loc,
                 "bio retrieval date differs from its receipt")
        require(observation["effective_at"] is None, loc,
                 "bio contract does not establish historical effective time")
        _source_facts(observation["source_fields"], loc + "/source_fields", reference["inputs"],
                      BIO_SKATER_SOURCE_FIELDS if observation["source"] == "skater-bios" else BIO_GOALIE_SOURCE_FIELDS)
        require(all(observation["source_fields"]["values"][source] == observation[field]
                     for source, field in (("playerId", "player_id"), ("birthDate", "birth_date"),
                                           ("shootsCatches", "shoots_catches"))), loc,
                 "bio source values and resolved aliases disagree")
    inventory = {}
    for i, entry in enumerate(array(reference["inventory"], f"{path}/reference/inventory")):
        loc = f"{path}/reference/inventory/{i}"
        _game_identity(entry, loc)
        require(entry["season"] == reference["requested_season"], loc,
                 "inventory and requested reference season disagree")
        integer(entry.get("source_index"), loc + "/source_index")
        gid = entry["game_id"]
        require(gid not in inventory, loc, "duplicate inventory game id")
        inventory[gid] = entry
    ledger = {}
    for i, row in enumerate(array(document["games"], f"{path}/games")):
        loc = f"{path}/games/{i}"
        object_fields(row, loc, ("game_id", "inventory_source_index", "status", "reason", "output_path"))
        gid = row["game_id"]
        require(type(gid) is str and gid in inventory and gid not in ledger, loc,
                 "unknown or duplicate corpus game id")
        require(type(row["inventory_source_index"]) is int
                 and row["inventory_source_index"] == inventory[gid]["source_index"], loc,
                 "inventory source index disagreement")
        require(row["status"] in STATUSES, loc, "unsupported corpus game status")
        text(row["reason"], loc + "/reason", nullable=True)
        text(row["output_path"], loc + "/output_path", nullable=True)
        require((row["status"] == "reconstructed") == bool(row["output_path"])
                 or row["status"] in ("identity_unavailable", "identity_mismatch"), loc,
                 "game status and envelope reference disagree")
        ledger[gid] = row
    require(ledger.keys() == inventory.keys(), path,
             "corpus ledger does not cover admitted inventory")
    return document, inventory, ledger


