"""reconstruct elapsed exposure without replacing reported event membership."""

from collections import Counter, defaultdict
import math
import re
from typing import Literal, TypedDict

from .interpret import GameDocument, Issue, clock_seconds


class Period(TypedDict):
    period_number: int
    end_seconds: int | None
    end_event_source_index: int | None
    status: Literal["supported", "unavailable"]
    issue_indices: list[int]


class Membership(TypedDict):
    away_skaters: list[int] | None
    home_skaters: list[int] | None
    away_goalies: list[int] | None
    home_goalies: list[int] | None


class Interval(Membership):
    period_number: int
    start_seconds: int
    end_seconds: int
    shift_source_indices: list[int]
    classification: Literal["five_on_five", "other", "unresolved"]
    issue_indices: list[int]


class ShotTypeEvidence(TypedDict):
    api_value: str | None
    report_value: str | None
    value: str | None
    status: Literal["agreement", "api_only", "report_only", "missing", "conflict", "unsupported", "unmatched"]


class GoalModifierEvidence(TypedDict):
    source_path: str | None
    reported_value: str | None
    status: Literal["reported", "missing", "unavailable", "unmatched", "conflict", "unsupported"]


class ReconstructedEvent(Membership):
    shot_type_evidence: ShotTypeEvidence | None
    goal_modifier_evidence: GoalModifierEvidence | None
    source_index: int
    report_source_index: int | None
    match_status: Literal["matched", "unmatched", "ambiguous", "unavailable", "untimed"]
    classification: Literal["five_on_five", "other", "unresolved", "untimed"]
    shift_relation: Literal["before", "after", "both", "neither", "unavailable"]
    interval_indices: list[int]
    attacking_x: int | float | None
    attacking_y: int | float | None
    coordinate_status: Literal["normalized", "missing_coordinates", "unresolved_frame", "not_applicable"]
    issue_indices: list[int]


class PlayerExposure(TypedDict):
    player_id: int
    team_id: int
    supported_5v5_seconds: int | None
    complete: bool
    issue_indices: list[int]


class TimeCoverage(TypedDict):
    expected_periods: list[int] | None
    supported_periods: list[int]
    known_seconds: int | None
    five_on_five_seconds: int | None
    other_seconds: int | None
    unresolved_seconds: int | None


class AttemptCoverage(TypedDict):
    known_timed_attempts: int | None
    five_on_five: int | None
    other: int | None
    unresolved: int | None
    linked_five_on_five: int | None
    unclassified_events: int | None


class LocationCoverage(TypedDict):
    known_timed_attempts: int | None
    normalized: int | None
    missing_coordinates: int | None
    unresolved_frame: int | None


class Coverage(TypedDict):
    time: TimeCoverage
    attempts: AttemptCoverage
    locations: LocationCoverage


class Reconstruction(TypedDict):
    periods: list[Period] | None
    intervals: list[Interval] | None
    events: list[ReconstructedEvent] | None
    player_exposure: list[PlayerExposure] | None
    coverage: Coverage
    issues: list[Issue]


REPORT_CODES = {
    "period-start": "PSTR", "faceoff": "FAC", "hit": "HIT", "giveaway": "GIVE",
    "goal": "GOAL", "shot-on-goal": "SHOT", "missed-shot": "MISS", "blocked-shot": "BLOCK",
    "penalty": "PENL", "stoppage": "STOP", "period-end": "PEND", "game-end": "GEND",
    "takeaway": "TAKE", "delayed-penalty": "DELPEN", "shootout-complete": "SOC",
}
_ATTEMPTS = {"goal", "shot-on-goal", "missed-shot", "blocked-shot"}
_SKATERS = {"C", "L", "R", "D", "F"}
_EMPTY: Membership = {"away_skaters": None, "home_skaters": None,
                      "away_goalies": None, "home_goalies": None}


def _issue(issues: list[Issue], code: str, source: str, path: str, message: str) -> int:
    issues.append({"code": code, "source": source, "path": path, "message": message})
    return len(issues) - 1


def _category(position: str | None) -> str | None:
    return "goalie" if position == "G" else "skater" if position in _SKATERS else None


def _lineup_classification(members: Membership) -> Literal["five_on_five", "other", "unresolved"]:
    if any(value is None for value in members.values()):
        return "unresolved"
    away_skaters, home_skaters = members["away_skaters"], members["home_skaters"]
    away_goalies, home_goalies = members["away_goalies"], members["home_goalies"]
    assert away_skaters is not None and home_skaters is not None
    assert away_goalies is not None and home_goalies is not None
    away, home = away_skaters + away_goalies, home_skaters + home_goalies
    if (not 3 <= len(away_skaters) <= 6 or not 3 <= len(home_skaters) <= 6
            or len(away_goalies) > 1 or len(home_goalies) > 1 or len(away) > 6 or len(home) > 6
            or len(set(away)) != len(away) or len(set(home)) != len(home) or set(away) & set(home)):
        return "unresolved"
    return "five_on_five" if len(away_skaters) == len(home_skaters) == 5 and len(away_goalies) == len(home_goalies) == 1 else "other"


# these spellings are source observations; no case folding or inferred aliases.
_SHOT_TYPES = {
    "wrist": "wrist", "Wrist": "wrist", "snap": "snap", "Snap": "snap",
    "slap": "slap", "Slap": "slap", "backhand": "backhand", "Backhand": "backhand",
    "tip-in": "tip-in", "Tip-In": "tip-in", "deflected": "deflected", "Deflected": "deflected",
    "wrap-around": "wrap-around", "Wrap-around": "wrap-around",
    "poke": "poke", "Poke": "poke", "bat": "bat", "Bat": "bat",
}


def canonical_shot_type(value: str | None) -> str | None:
    return _SHOT_TYPES.get(value)


def reconcile_shot_type(api_value: str | None, report_value: str | None, matched: bool) -> ShotTypeEvidence:
    a, b = canonical_shot_type(api_value), canonical_shot_type(report_value)
    value = None
    if not matched:
        status = "unmatched"
    elif (api_value is not None and a is None) or (report_value is not None and b is None):
        status = "unsupported"
    elif a is not None and b is not None:
        status = "agreement" if a == b else "conflict"
        value = a if a == b else None
    elif a is not None:
        status, value = "api_only", a
    elif b is not None:
        status, value = "report_only", b
    else:
        status = "missing"
    return {"api_value": api_value, "report_value": report_value, "value": value, "status": status}


def _attempt_group(api, reports, event_ids, sort_orders, report_ids, report_numbers, identities):
    if any(not row["kind_valid"] or row["event_id"] is None or event_ids[row["event_id"]] != 1
           or row["sort_order"] is None or sort_orders[row["sort_order"]] != 1 for row in api) or any(
           row["row_id"] is None or report_ids[row["row_id"]] != 1
           or row["event_number"] is None or report_numbers[row["event_number"]] != 1 for row in reports):
        return "unavailable", {}, "attempt group contains invalid kind or missing/repeated source identities"
    if len(api) != len(reports) or not reports:
        return "ambiguous", {}, "attempt group has unequal api/report sizes"
    edges = {}
    for row in api:
        shooter = row["roles"].get("scorer" if row["type_key"] == "goal" else "shooter")
        choices = []
        for report in reports:
            identity = identities.get(report["shooter_id"])
            report_shooter = report["shooter_id"] if identity is not None and (
                report["shooter_sweater_number"] is None or identity["sweater_number"] == report["shooter_sweater_number"]
            ) and identity["team_id"] == report["shooting_team_id"] else None
            facts = ((row["shooting_team_id"], report["shooting_team_id"]), (shooter, report_shooter),
                     (canonical_shot_type(row["shot_type"]), canonical_shot_type(report["shot_type"])))
            if not any(a is not None and b is not None and a != b for a, b in facts):
                choices.append(report)
        edges[row["source_index"]] = choices
    solutions = []
    ordered = sorted(api, key=lambda row: len(edges[row["source_index"]]))
    def search(offset, chosen, used):
        if len(solutions) == 2:
            return
        if offset == len(ordered):
            solutions.append(dict(chosen))
            return
        index = ordered[offset]["source_index"]
        for report in edges[index]:
            number = report["source_index"]
            if number not in used:
                chosen[index] = report
                search(offset + 1, chosen, used | {number})
                del chosen[index]
    search(0, {}, set())
    if not solutions:
        return "unmatched", {}, "attempt group has no complete assignment compatible with supported team/shooter/type"
    if len(solutions) > 1:
        return "ambiguous", {}, "attempt group has multiple complete assignments"
    return "matched", solutions[0], "unique complete assignment from supported team/shooter/type"


def _goal_modifier(row, document, event_ids, landing_ids) -> GoalModifierEvidence:
    evidence: GoalModifierEvidence = {"source_path": None, "reported_value": None, "status": "unavailable"}
    goals = document["landing_goals"]
    if goals is None:
        return evidence
    matches = [goal for goal in goals if row["event_id"] is not None and goal["event_id"] == row["event_id"]]
    if len(matches) == 1:
        goal = matches[0]
        evidence.update(source_path=goal["source_path"], reported_value=goal["goal_modifier"])
    if row["event_id"] is None or event_ids[row["event_id"]] != 1:
        return evidence
    api_path = f"/plays/{row['source_index']}"
    corroboration_fields = (api_path + "/periodDescriptor", api_path + "/timeInPeriod",
                            api_path + "/timeRemaining", api_path + "/details/eventOwnerTeamId")
    if (not row["kind_valid"] or row["timed_period"] is None
            or any(value is None for value in (row["period_number"], row["period_type"], row["time_in_period"], row["shooting_team_id"], row["roles"].get("scorer")))
            or row["timed_period"] is True and row["elapsed_seconds"] is None
            or any(issue["source"] == "play-by-play" and issue["code"] in (
                "invalid_integer", "invalid_string", "invalid_object", "invalid_clock", "inconsistent_event_clock", "unsupported_period", "unresolved_team")
                and (issue["path"] == api_path or any(issue["path"] == field or issue["path"].startswith(field + "/") for field in corroboration_fields))
                for issue in document["issues"])):
        return evidence
    if not matches:
        evidence["status"] = "unmatched"
        return evidence
    if len(matches) != 1 or landing_ids[row["event_id"]] != 1:
        return evidence
    goal = matches[0]
    path = goal["source_path"]
    period_path = path.rsplit("/goals/", 1)[0] + "/periodDescriptor"
    located = [issue for issue in document["issues"] if issue["source"] == "landing" and (
        issue["path"] == path or issue["path"].startswith(path + "/")
        or issue["path"] == period_path or issue["path"].startswith(period_path + "/"))]
    invalid_codes = {"invalid_integer", "invalid_string", "invalid_object", "invalid_clock",
                     "inconsistent_event_clock", "unsupported_period", "invalid_goal_team",
                     "invalid_goal_team_abbreviation", "unavailable_goal_team_abbreviation"}
    if any(issue["code"] in invalid_codes for issue in located):
        return evidence
    facts = ((row["period_number"], goal["period_number"]), (row["period_type"], goal["period_type"]),
             (clock_seconds(row["time_in_period"], "play-by-play", api_path + "/timeInPeriod", []),
              clock_seconds(goal["time_in_period"], "landing", path + "/timeInPeriod", [])), (row["shooting_team_id"], goal["team_id"]),
             (row["roles"].get("scorer"), goal["credited_scorer_id"]))
    if any(a is None or b is None for a, b in facts):
        return evidence
    if row["timed_period"] is True and goal["elapsed_seconds"] is None:
        return evidence
    if (any(a != b for a, b in facts)
            or row["owner_team_id"] is not None and row["owner_team_id"] != goal["team_id"]
            or any(issue["code"] == "goal_team_disagreement" for issue in located)):
        evidence["status"] = "conflict"
    elif goal["goal_modifier"] is None:
        evidence["status"] = "missing"
    elif goal["goal_modifier"] in ("none", "own-goal", "awarded", "penalty-shot"):
        evidence["status"] = "reported"
    else:
        evidence["status"] = "unsupported"
    return evidence


def reconstruct_game(document: GameDocument) -> Reconstruction:
    """calculate from admitted facts and shared clock conversion; do not read files."""
    issues: list[Issue] = []
    game = document["game"]
    api = document["events"]
    reports = document["report_rows"]
    roster = document["roster_records"]
    shifts = document["shift_records"]

    # only a single roster record establishes a player's team and position.
    roster_by_id = defaultdict(list)
    for row in roster or []:
        if row["player_id"] is not None:
            roster_by_id[row["player_id"]].append(row)
    identities = {player: rows[0] for player, rows in roster_by_id.items()
                  if len(rows) == 1 and rows[0]["team_id"] is not None}

    event_ids = Counter(row["event_id"] for row in api or [] if row["event_id"] is not None)
    sort_orders = Counter(row["sort_order"] for row in api or [] if row["sort_order"] is not None)
    report_ids = Counter(row["row_id"] for row in reports or [] if row["row_id"] is not None)
    landing_ids = Counter(row["event_id"] for row in document["landing_goals"] or [] if row["event_id"] is not None)
    report_numbers = Counter(row["event_number"] for row in reports or [] if row["event_number"] is not None)

    periods: list[Period] | None = None
    intervals: list[Interval] | None = None
    interval_possible_players: list[set[int] | None] = []
    expected: list[int] | None = None
    if game is not None:
        outcomes = {row["last_period_type"] for row in document["reported_results"] if row["last_period_type"] is not None}
        shootout = outcomes == {"SO"} or any(row["period_number"] == 5 and row["timed_period"] is False for row in api or []) or any(
            row["period_number"] == 5 and row["event_code"] in ("GOAL", "SHOT", "MISS", "BLOCK", "SOC") for row in reports or [])
        overtime = bool(outcomes & {"OT", "SO"}) or any(
            (row["period_number"] == 4 and row["timed_period"] is True)
            or (row["period_number"] == 5 and row["timed_period"] is False) for row in api or []) or any(
            row["period_number"] in (4, 5) for row in reports or [])
        expected = [1, 2, 3] + ([4] if overtime else [])
        periods = [{"period_number": number, "end_seconds": 1200 if number <= 3 else None,
                    "end_event_source_index": None, "status": "supported" if number <= 3 else "unavailable",
                    "issue_indices": []} for number in expected]
        by_period = {row["period_number"]: row for row in periods}
        if overtime:
            period = by_period[4]
            if len(outcomes) > 1 or (outcomes and not outcomes <= {"OT", "SO"}):
                for result in document["reported_results"]:
                    if result["last_period_type"] is not None:
                        period["issue_indices"].append(_issue(issues, "conflicting_overtime_outcome", result["source"],
                            "/gameOutcome/lastPeriodType", "reported final period types disagree with overtime evidence; overtime horizon unavailable"))
            elif outcomes == {"SO"}:
                period["end_seconds"], period["status"] = 300, "supported"
            else:
                endings = [row for row in api or [] if row["period_number"] == 4 and row["type_key"] == "period-end"]
                if (len(endings) == 1 and endings[0]["kind_valid"] and endings[0]["timed_period"] is True
                        and endings[0]["elapsed_seconds"] is not None
                        and endings[0]["event_id"] is not None and event_ids[endings[0]["event_id"]] == 1
                        and endings[0]["sort_order"] is not None and sort_orders[endings[0]["sort_order"]] == 1):
                    period["end_seconds"] = endings[0]["elapsed_seconds"]
                    period["end_event_source_index"] = endings[0]["source_index"]
                    period["status"] = "supported"
                else:
                    period["issue_indices"].append(_issue(issues, "unavailable_overtime_end", "play-by-play",
                        "/plays", "overtime requires one valid uniquely identified period-end record; overtime horizon unavailable"))

        # a missing report terminal is not disagreement. supplied claims must fit
        # their declared period; final game-end claims must also name the same period.
        terminals = []
        for row in api or []:
            if row["type_key"] in ("period-end", "game-end"):
                terminals.append(("play-by-play", f"/plays/{row['source_index']}",
                                  row["period_number"], REPORT_CODES[row["type_key"]],
                                  row["elapsed_seconds"], row["kind_valid"], row["timed_period"]))
        for row in reports or []:
            if row["event_code"] in ("PEND", "GEND"):
                number = row["period_number"]
                terminals.append(("play-report", f"/rows/{row['source_index']}[{row['row_id']}]",
                                  number, row["event_code"], row["elapsed_seconds"], True,
                                  False if number == 5 else True if number in (1, 2, 3, 4) else None))
        final_claims = {source: {number for terminal_source, _, number, kind, _, _, _ in terminals
                                 if terminal_source == source and kind == "GEND"}
                        for source in ("play-by-play", "play-report")}
        final_conflict = bool(final_claims["play-by-play"] and final_claims["play-report"]
                              and final_claims["play-by-play"] != final_claims["play-report"])
        terminal_keys = {source: Counter((number, kind) for terminal_source, _, number, kind, _, _, _ in terminals
                                       if terminal_source == source)
                         for source in ("play-by-play", "play-report")}
        # repeated terminal claims can displace a period or kind. an absent
        # claim alone does not contradict an independently established horizon.
        if all(terminal_keys.values()) and any(count > 1 for counts in terminal_keys.values() for count in counts.values()):
            disputed = {key for key in terminal_keys["play-by-play"].keys() | terminal_keys["play-report"].keys()
                        if terminal_keys["play-by-play"][key] != terminal_keys["play-report"][key]}
            for source, path, number, kind, _, _, _ in terminals:
                if terminal_keys[source][number, kind] > 1:
                    for affected in sorted({n if n in by_period else expected[-1] for n, _ in disputed}):
                        by_period[affected]["issue_indices"].append(_issue(issues, "conflicting_terminal_identity", source, path,
                            f"repeated terminal period/kind claims disagree with the other source; period {affected} horizon unavailable"))
        for source, path, number, kind, elapsed, valid, timed in terminals:
            affected = number if number in by_period else expected[-1]
            period = by_period[affected]
            reason = None
            if not valid:
                reason = "terminal event kind/code is inconsistent"
            elif kind == "GEND" and (final_conflict or number != (5 if shootout else expected[-1])):
                reason = "final game-end names a conflicting final period"
            elif number not in by_period and not (number == 5 and shootout):
                reason = "terminal record names an unsupported timed period"
            elif number in by_period and period["end_seconds"] is not None:
                if timed is not True or elapsed is None:
                    reason = "supplied timed terminal has unavailable timing"
                elif elapsed != period["end_seconds"]:
                    reason = "terminal clock disagrees with this period's established endpoint"
            if reason is not None:
                period["issue_indices"].append(_issue(issues, "conflicting_terminal", source, path,
                    reason + "; affected period horizon unavailable"))
        for row in api or []:
            period = by_period.get(row["period_number"])
            if (period is not None and period["end_seconds"] is not None and row["timed_period"] is True
                    and row["elapsed_seconds"] is not None and row["elapsed_seconds"] > period["end_seconds"]):
                period["issue_indices"].append(_issue(issues, "event_after_period_end", "play-by-play",
                    f"/plays/{row['source_index']}", "timed event follows the established endpoint; period horizon unavailable"))
        for row in reports or []:
            period = by_period.get(row["period_number"])
            if period is not None and period["end_seconds"] is not None and row["elapsed_seconds"] is not None and row["elapsed_seconds"] > period["end_seconds"]:
                period["issue_indices"].append(_issue(issues, "event_after_period_end", "play-report",
                    f"/rows/{row['source_index']}[{row['row_id']}]", "reported event follows the established endpoint; period horizon unavailable"))
        for period in periods:
            if period["issue_indices"]:
                period["status"], period["end_seconds"], period["end_event_source_index"] = "unavailable", None, None

        intervals = []
        complete_shifts = shifts is not None and any(check["name"] == "shift_collection" and check["status"] == "match"
                                                   for check in document["checks"])
        global_shift_issues: list[int] = []
        period_shift_issues = defaultdict(list)
        period_uncertain_players: dict[int, set[int] | None] = {number: set() for number in expected}
        row_shift_issues = defaultdict(list)
        overlap_issue_indices: dict[int, int] = {}
        bounded_rows = defaultdict(list)
        record_ids = Counter(row["record_id"] for row in shifts or [] if row["record_id"] is not None)
        shift_identities = Counter((row["player_id"], row["period_number"], row["shift_number"])
                                   for row in shifts or [] if row["type_code"] == 517
                                   and None not in (row["player_id"], row["period_number"], row["shift_number"]))
        if not complete_shifts:
            global_shift_issues.append(_issue(issues, "unavailable_shift_collection", "shifts", "/data",
                "shift collection is missing or incomplete; elapsed membership unavailable throughout supported horizons"))
        for row in shifts or []:
            if row["interval_status"] == "not_shift":
                continue
            number, start, end = row["period_number"], row["start_seconds"], row["end_seconds"]
            index = row["source_index"]
            path = f"/data/{index}"
            row_issues = row_shift_issues[index]
            if row["type_code"] != 517:
                row_issues.append(_issue(issues, "unknown_shift_kind", "shifts", path + "/typeCode",
                    "record may contain a shift; elapsed membership unavailable where this row can apply"))
            elif row["interval_status"] != "coherent":
                row_issues.append(_issue(issues, "defective_shift_interval", "shifts", path,
                    "reported interval is not coherent; elapsed membership unavailable where its bounds can apply"))
            if row["record_id"] is None or record_ids[row["record_id"]] != 1:
                row_issues.append(_issue(issues, "unresolved_shift_identity", "shifts", path + "/id",
                    "shift record identity is missing or repeated; affected elapsed membership unavailable"))
            identity = identities.get(row["player_id"])
            if identity is None or identity["team_id"] != row["team_id"] or _category(identity["reported_position"]) is None:
                row_issues.append(_issue(issues, "unresolved_shift_player", "shifts", path,
                    "shift player has no unique compatible roster team/position; affected elapsed membership unavailable"))
            key = (row["player_id"], number, row["shift_number"])
            if None not in key and shift_identities[key] > 1:
                row_issues.append(_issue(issues, "repeated_shift_identity", "shifts", path,
                    "player/period/shift number is repeated; affected elapsed membership unavailable"))
            if number not in by_period:
                global_shift_issues.extend(row_issues or [_issue(issues, "unlocatable_shift", "shifts", path,
                    "potential shift cannot be located in an expected period; elapsed membership unavailable throughout the game")])
            elif start is None or end is None:
                period_shift_issues[number].extend(row_issues or [_issue(issues, "unavailable_shift_bounds", "shifts", path,
                    "potential shift has unavailable bounds; this period's elapsed membership unavailable")])
                if row["player_id"] is None:
                    period_uncertain_players[number] = None
                elif period_uncertain_players[number] is not None:
                    period_uncertain_players[number].add(row["player_id"])
            else:
                bounded_rows[number].append(row)
                horizon = by_period[number]["end_seconds"]
                if horizon is not None and end > horizon:
                    period_shift_issues[number].append(_issue(issues, "shift_after_period_end", "shifts", path,
                        "shift extends beyond the actual horizon; this period's elapsed membership unavailable without clipping"))
                    if row["player_id"] is None:
                        period_uncertain_players[number] = None
                    elif period_uncertain_players[number] is not None:
                        period_uncertain_players[number].add(row["player_id"])
        for period in periods:
            horizon, number = period["end_seconds"], period["period_number"]
            if period["status"] != "supported" or horizon is None:
                continue
            points = {0, horizon}
            for row in bounded_rows[number]:
                points.update(value for value in (row["start_seconds"], row["end_seconds"]) if 0 <= value <= horizon)
            ordered = sorted(points)
            for start, end in zip(ordered, ordered[1:]):
                covering = [row for row in bounded_rows[number] if row["start_seconds"] < end and row["end_seconds"] > start]
                local_issues = list(global_shift_issues) + period_shift_issues[number]
                for row in covering:
                    local_issues.extend(row_shift_issues[row["source_index"]])
                members: Membership = {"away_skaters": [], "home_skaters": [], "away_goalies": [], "home_goalies": []}
                unknown_membership = False
                if not local_issues:
                    active = Counter(row["player_id"] for row in covering)
                    overlaps = {player for player, count in active.items() if count > 1}
                    for row in covering:
                        if row["player_id"] in overlaps:
                            source_index = row["source_index"]
                            if source_index not in overlap_issue_indices:
                                overlap_issue_indices[source_index] = _issue(issues, "overlapping_player_shifts", "shifts", f"/data/{source_index}",
                                    "player has overlapping shift rows; overlapping elapsed membership unavailable")
                            local_issues.append(overlap_issue_indices[source_index])
                        identity = identities[row["player_id"]]
                        side = "away" if identity["team_id"] == game["away_team_id"] else "home"
                        key = side + ("_goalies" if _category(identity["reported_position"]) == "goalie" else "_skaters")
                        members[key].append(row["player_id"])
                    for value in members.values():
                        value.sort()
                    classification = _lineup_classification(members)
                    if classification == "unresolved" and not local_issues:
                        unknown_membership = True
                        local_issues.append(_issue(issues, "implausible_elapsed_lineup", "shifts", "/data",
                            f"period {number} [{start},{end}) has unsupported player counts or identities; elapsed membership unavailable"))
                if local_issues:
                    members = dict(_EMPTY)
                    classification = "unresolved"
                intervals.append({"period_number": number, "start_seconds": start, "end_seconds": end,
                                  **members, "shift_source_indices": sorted(row["source_index"] for row in covering),
                                  "classification": classification, "issue_indices": sorted(set(local_issues))})
                uncertain = period_uncertain_players[number]
                if global_shift_issues or unknown_membership or uncertain is None or any(row["player_id"] is None for row in covering):
                    interval_possible_players.append(None)
                else:
                    interval_possible_players.append({row["player_id"] for row in covering} | uncertain)

    api_keys = defaultdict(list)
    report_keys = defaultdict(list)
    for row in api or []:
        kind = REPORT_CODES.get(row["type_key"])
        if (row["kind_valid"] or row["type_key"] in _ATTEMPTS) and row["timed_period"] is True and row["elapsed_seconds"] is not None and kind is not None:
            api_keys[(row["period_number"], row["elapsed_seconds"], kind)].append(row)
    for row in reports or []:
        if row["period_number"] in (1, 2, 3, 4) and row["elapsed_seconds"] is not None and row["event_code"] in REPORT_CODES.values():
            report_keys[(row["period_number"], row["elapsed_seconds"], row["event_code"])].append(row)
    attempt_groups = {}
    for key in api_keys:
        if key[2] in ("GOAL", "SHOT", "MISS", "BLOCK") and (len(api_keys[key]) > 1 or len(report_keys[key]) > 1):
            attempt_groups[key] = _attempt_group(api_keys[key], report_keys[key], event_ids, sort_orders,
                                                  report_ids, report_numbers, identities)
    period_sides = defaultdict(set)
    for row in api or []:
        if row["timed_period"] is True and row["home_team_defending_side"] in ("left", "right"):
            period_sides[row["period_number"]].add(row["home_team_defending_side"])

    reconstructed_events: list[ReconstructedEvent] | None = None
    if api is not None:
        reconstructed_events = []
        for row in api:
            index, path = row["source_index"], f"/plays/{row['source_index']}"
            event: ReconstructedEvent = {"source_index": index, "report_source_index": None, "match_status": "unavailable",
                "shot_type_evidence": None, "goal_modifier_evidence": None,
                **_EMPTY, "classification": "unresolved", "shift_relation": "unavailable", "interval_indices": [],
                "attacking_x": None, "attacking_y": None, "coordinate_status": "not_applicable", "issue_indices": []}
            event_issues = event["issue_indices"]
            if row["type_key"] == "goal":
                event["goal_modifier_evidence"] = _goal_modifier(row, document, event_ids, landing_ids)
                modifier = event["goal_modifier_evidence"]
                if modifier["status"] in ("unavailable", "unmatched", "conflict", "unsupported"):
                    event_issues.append(_issue(issues, "goal_modifier_" + modifier["status"], "landing",
                        modifier["source_path"] or "/summary/scoring", "goal modifier evidence is " + modifier["status"]))
            kind = REPORT_CODES.get(row["type_key"])
            situation = row["situation_code"]
            valid_situation = situation is not None and re.fullmatch(r"[01][0-6][0-6][01]", situation) is not None
            if row["timed_period"] is True and not valid_situation:
                event_issues.append(_issue(issues, "unavailable_situation_check", "play-by-play", path + "/situationCode",
                    "timed situation code is missing/invalid; report-count corroboration unavailable"))
            report = None
            if row["timed_period"] is False:
                event["match_status"], event["classification"] = "untimed", "untimed"
            elif (row["timed_period"] is not True or not row["kind_valid"] or row["elapsed_seconds"] is None
                    or kind is None or row["event_id"] is None or event_ids[row["event_id"]] != 1
                    or row["sort_order"] is None or sort_orders[row["sort_order"]] != 1):
                event_issues.append(_issue(issues, "unavailable_event_identity", "play-by-play", path,
                    "event kind, timing or unique api identities unavailable; reported event membership unavailable"))
            elif reports is None or game is None:
                event_issues.append(_issue(issues, "unavailable_event_report", "play-report", "/rows",
                    "admitted event report or game identity unavailable; event membership unavailable"))
            else:
                key = (row["period_number"], row["elapsed_seconds"], kind)
                candidates = report_keys[key]
                if key in attempt_groups:
                    status, assignment, reason = attempt_groups[key]
                    event["match_status"] = status
                    if status == "matched":
                        report = assignment[index]
                        event["report_source_index"] = report["source_index"]
                    else:
                        event_issues.append(_issue(issues, "attempt_group_" + status, "play-by-play", path,
                            reason + "; whole group event membership unavailable"))
                elif len(api_keys[key]) > 1 or len(candidates) > 1:
                    event["match_status"] = "ambiguous"
                    event_issues.append(_issue(issues, "ambiguous_event_match", "play-by-play", path,
                        "period/clock/kind has multiple api or report candidates; event membership unavailable"))
                elif not candidates:
                    event["match_status"] = "unmatched"
                    event_issues.append(_issue(issues, "unmatched_event", "play-by-play", path,
                        "no report row shares this period/clock/kind; event membership unavailable"))
                else:
                    candidate = candidates[0]
                    report_path = f"/rows/{candidate['source_index']}[{candidate['row_id']}]"
                    if (candidate["row_id"] is None or report_ids[candidate["row_id"]] != 1
                            or candidate["event_number"] is None or report_numbers[candidate["event_number"]] != 1):
                        event_issues.append(_issue(issues, "unavailable_report_identity", "play-report", report_path,
                            "report row identity is missing or repeated; event membership unavailable"))
                    else:
                        report = candidate
                        event["report_source_index"], event["match_status"] = report["source_index"], "matched"
            if row["type_key"] in _ATTEMPTS:
                event["shot_type_evidence"] = reconcile_shot_type(row["shot_type"], report["shot_type"] if report is not None else None, report is not None)
                if event["shot_type_evidence"]["status"] in ("conflict", "unsupported"):
                    event_issues.append(_issue(issues, "shot_type_" + event["shot_type_evidence"]["status"],
                        "play-by-play", path + "/details/shotType", "api/report shot type evidence is " + event["shot_type_evidence"]["status"]))
            membership_issues: list[int] = []
            if report is not None:
                report_path = f"/rows/{report['source_index']}[{report['row_id']}]"
                for side in ("away", "home"):
                    reported_members = report[side + "_members"]
                    if reported_members is None:
                        membership_issues.append(_issue(issues, "unavailable_report_members", "play-report", report_path + "/" + side + "_members",
                            "reported member list unavailable; event strength unresolved"))
                        continue
                    skaters, goalies = [], []
                    for slot, member in enumerate(reported_members):
                        player = member["player_id"]
                        category = _category(member["reported_position"])
                        identity = identities.get(player)
                        if player is not None and category is not None:
                            (goalies if category == "goalie" else skaters).append(player)
                        team = game[side + "_team_id"]
                        if (player is None or identity is None or identity["team_id"] != team or category is None
                                or category != _category(identity["reported_position"])):
                            membership_issues.append(_issue(issues, "unresolved_report_member", "play-report",
                                report_path + f"/{side}_members/{slot}",
                                "member has missing/ambiguous identity or incompatible roster team/position; event strength unresolved"))
                    event[side + "_skaters"], event[side + "_goalies"] = sorted(skaters), sorted(goalies)
                membership: Membership = {key: event[key] for key in _EMPTY}
                classification = _lineup_classification(membership)
                if row["type_key"] in _ATTEMPTS and report["penalty_shot"] is None:
                    membership_issues.append(_issue(issues, "unavailable_penalty_shot_status", "play-report", report_path + "/description",
                        "attempt description cannot establish ordinary versus penalty-shot play; event population unresolved"))
                modifier = event["goal_modifier_evidence"]
                penalty_shot = row["type_key"] in _ATTEMPTS and (report["penalty_shot"] is True or
                    modifier is not None and modifier["status"] == "reported" and modifier["reported_value"] == "penalty-shot")
                if penalty_shot and all(value is not None for value in membership.values()):
                    away_ids = event["away_skaters"] + event["away_goalies"]
                    home_ids = event["home_skaters"] + event["home_goalies"]
                    if (len(away_ids) == len(set(away_ids)) and len(home_ids) == len(set(home_ids))
                            and len(away_ids) <= 6 and len(home_ids) <= 6
                            and len(event["away_goalies"]) <= 1 and len(event["home_goalies"]) <= 1
                            and not set(away_ids) & set(home_ids)):
                        classification = "other"
                if classification == "unresolved":
                    membership_issues.append(_issue(issues, "implausible_event_lineup", "play-report", report_path,
                        "reported lineup has unavailable or unsupported player counts/identities; event strength unresolved"))
                away = set((event["away_skaters"] or []) + (event["away_goalies"] or []))
                home = set((event["home_skaters"] or []) + (event["home_goalies"] or []))
                roles = row["roles"]
                if row["type_key"] in _ATTEMPTS:
                    shooter_role = "scorer" if row["type_key"] == "goal" else "shooter"
                    shooting_team = row["shooting_team_id"]
                    for issue in document["issues"]:
                        if issue["source"] == "play-report" and issue["code"] in ("unresolved_report_shooting_team", "unresolved_report_shooter") and (
                                issue["path"] == report_path or issue["path"].startswith(report_path + "/")):
                            membership_issues.append(_issue(issues, issue["code"], issue["source"], issue["path"], issue["message"]))
                    report_shooter = report["shooter_id"]
                    shooter_identity = identities.get(report_shooter)
                    if (report["shooting_team_id"] is not None and report["shooting_team_id"] != shooting_team
                            or report_shooter is not None and (report_shooter != roles.get(shooter_role)
                            or shooter_identity is None or shooter_identity["team_id"] != report["shooting_team_id"]
                            or report["shooter_sweater_number"] is not None and shooter_identity["sweater_number"] != report["shooter_sweater_number"])):
                        membership_issues.append(_issue(issues, "report_attempt_participant_disagreement", "play-report", report_path,
                            "parsed report shooting team/shooter conflicts with api or unique roster identity; event strength unresolved"))
                    shooters = away if shooting_team == game["away_team_id"] else home if shooting_team == game["home_team_id"] else set()
                    opponents = event["home_goalies"] if shooting_team == game["away_team_id"] else event["away_goalies"] if shooting_team == game["home_team_id"] else None
                    if roles.get(shooter_role) not in shooters:
                        shooter_field = "scoringPlayerId" if shooter_role == "scorer" else "shootingPlayerId"
                        membership_issues.append(_issue(issues, "incompatible_attempt_participant", "play-by-play", path + "/details/" + shooter_field,
                            "scorer/shooter has no compatible reported membership and shooting team; event strength unresolved"))
                    if "blocker" in roles and (roles["blocker"] is None or roles["blocker"] not in away | home):
                        membership_issues.append(_issue(issues, "incompatible_attempt_participant", "play-by-play", path + "/details/blockingPlayerId",
                            "supplied blocker is absent from the reported lineup; event strength unresolved"))
                    if "goalie" in roles and (roles["goalie"] is None or opponents is None or roles["goalie"] not in opponents):
                        membership_issues.append(_issue(issues, "incompatible_attempt_participant", "play-by-play", path + "/details/goalieInNetId",
                            "supplied opposing goalie is absent from the reported goalie list; event strength unresolved"))
                elif row["type_key"] == "faceoff":
                    winner, loser = roles.get("faceoff_winner"), roles.get("faceoff_loser")
                    if not ((winner in away and loser in home) or (winner in home and loser in away)):
                        membership_issues.append(_issue(issues, "incompatible_faceoff_participants", "play-by-play", path + "/details",
                            "faceoff participants do not identify opposite reported teams; event strength unresolved"))
                description = report["description"] or ""
                leading = re.match(r"^([A-Z]{2,3})\b", description)
                if leading is not None and row["type_key"] not in _ATTEMPTS:
                    expected_team = row["owner_team_id"]
                    named_team = {game["away_team_abbrev"]: game["away_team_id"], game["home_team_abbrev"]: game["home_team_id"]}.get(leading[1])
                    names_team = named_team is not None or re.match(r"^[A-Z]{2,3}\s+(?:#|won\b)", description) is not None
                    if names_team and (named_team is None or expected_team is None or named_team != expected_team):
                        membership_issues.append(_issue(issues, "report_event_team_disagreement", "play-report", report_path + "/description",
                            "leading event team does not agree with the api event/shooting team; event strength unresolved"))
                if valid_situation:
                    if all(value is not None for value in membership.values()):
                        counts = (len(event["away_goalies"]), len(event["away_skaters"]), len(event["home_skaters"]), len(event["home_goalies"]))
                        if counts != tuple(int(value) for value in situation):
                            membership_issues.append(_issue(issues, "situation_report_disagreement", "play-by-play", path + "/situationCode",
                                "situation counts disagree with the reported lineup; event strength unresolved"))
                event_issues.extend(membership_issues)
                if not membership_issues:
                    event["classification"] = classification

            if event["classification"] in ("five_on_five", "other") and intervals is not None:
                time, number = row["elapsed_seconds"], row["period_number"]
                before = [(i, interval) for i, interval in enumerate(intervals)
                          if interval["period_number"] == number and interval["start_seconds"] < time <= interval["end_seconds"]]
                after = [(i, interval) for i, interval in enumerate(intervals)
                         if interval["period_number"] == number and interval["start_seconds"] <= time < interval["end_seconds"]]
                horizon = next((period["end_seconds"] for period in periods if period["period_number"] == number and period["status"] == "supported"), None)
                necessary = before + after
                if (horizon is not None and 0 <= time <= horizon and necessary
                        and (time == 0 or before) and (time == horizon or after)
                        and all(interval["classification"] != "unresolved" for _, interval in necessary)):
                    matches_before = [i for i, interval in before if all(event[key] == interval[key] for key in _EMPTY)]
                    matches_after = [i for i, interval in after if all(event[key] == interval[key] for key in _EMPTY)]
                    event["interval_indices"] = sorted(set(matches_before + matches_after))
                    event["shift_relation"] = "both" if matches_before and matches_after else "before" if matches_before else "after" if matches_after else "neither"
                    if event["shift_relation"] == "neither":
                        event_issues.append(_issue(issues, "event_exposure_disagreement", "play-by-play", path,
                            "reported lineup matches neither adjacent supported interval; exposure link unavailable"))
                else:
                    event_issues.append(_issue(issues, "unavailable_event_exposure_link", "play-by-play", path,
                        "necessary adjacent elapsed membership or horizon unavailable; exposure link unavailable"))

            if row["kind_valid"] and row["type_key"] in _ATTEMPTS and row["timed_period"] is True:
                x, y = row["reported_x"], row["reported_y"]
                missing = [field for field, value in (("xCoord", x), ("yCoord", y))
                           if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value))]
                if missing:
                    event["coordinate_status"] = "missing_coordinates"
                    for field in missing:
                        event_issues.append(_issue(issues, "missing_attempt_coordinates", "play-by-play", path + "/details/" + field,
                            "finite recorded coordinate unavailable; normalized recorded location unavailable"))
                elif game is None or row["shooting_team_id"] not in (game["away_team_id"], game["home_team_id"]):
                    event["coordinate_status"] = "unresolved_frame"
                    field = "scoringPlayerId" if row["type_key"] == "goal" else "shootingPlayerId"
                    event_issues.append(_issue(issues, "unresolved_attempt_frame", "play-by-play", path + "/details/" + field,
                        "participant has no resolved shooting team; normalized recorded location unavailable"))
                elif row["home_team_defending_side"] not in ("left", "right") or len(period_sides[row["period_number"]]) > 1:
                    event["coordinate_status"] = "unresolved_frame"
                    reason = "event has no explicit defending side" if row["home_team_defending_side"] not in ("left", "right") else "period reports conflicting defending sides"
                    event_issues.append(_issue(issues, "unresolved_attempt_frame", "play-by-play", path + "/homeTeamDefendingSide",
                        reason + "; normalized recorded location unavailable"))
                else:
                    positive = (row["shooting_team_id"] == game["home_team_id"]) == (row["home_team_defending_side"] == "left")
                    event["attacking_x"], event["attacking_y"] = (x, y) if positive else (-x, -y)
                    event["coordinate_status"] = "normalized"
            reconstructed_events.append(event)

    supported = [period["period_number"] for period in periods or [] if period["status"] == "supported"]
    durations = Counter()
    for interval in intervals or []:
        durations[interval["classification"]] += interval["end_seconds"] - interval["start_seconds"]
    time_coverage: TimeCoverage = {"expected_periods": expected, "supported_periods": supported,
        "known_seconds": sum(period["end_seconds"] for period in periods or [] if period["status"] == "supported") if supported else None,
        "five_on_five_seconds": durations["five_on_five"] if supported else None,
        "other_seconds": durations["other"] if supported else None,
        "unresolved_seconds": durations["unresolved"] if supported else None}

    exposures: list[PlayerExposure] | None = None
    if roster is not None:
        exposures = []
        elapsed_available = any(interval["classification"] != "unresolved" for interval in intervals or [])
        incomplete_horizon = periods is None or any(period["status"] != "supported" for period in periods)
        for player, identity in sorted(identities.items()):
            if _category(identity["reported_position"]) != "skater":
                continue
            side = "away" if game is not None and identity["team_id"] == game["away_team_id"] else "home"
            unresolved_intervals = [interval for interval, possible in zip(intervals or [], interval_possible_players)
                                    if interval["classification"] == "unresolved" and (possible is None or player in possible)]
            player_issues = sorted({i for period in periods or [] if period["status"] != "supported" for i in period["issue_indices"]}
                                   | {i for interval in unresolved_intervals for i in interval["issue_indices"]})
            conflicting_toi = [check for check in document["checks"] if check["name"] == "player_toi" and check.get("player_id") == player and check["status"] == "mismatch"]
            if conflicting_toi:
                boxscore = next((row for row in document["boxscore_players"] or [] if row["player_id"] == player), None)
                player_issues.append(_issue(issues, "conflicting_player_toi", "boxscore", boxscore["source_path"] + "/toi" if boxscore else "/playerByGameStats",
                    "shift-based toi disagrees with reported player toi; full-game 5v5 exposure completeness unresolved"))
            exposures.append({"player_id": player, "team_id": identity["team_id"],
                "supported_5v5_seconds": sum(interval["end_seconds"] - interval["start_seconds"] for interval in intervals or []
                    if interval["classification"] == "five_on_five" and player in interval[side + "_skaters"]) if elapsed_available else None,
                "complete": not incomplete_horizon and not unresolved_intervals and not conflicting_toi,
                "issue_indices": player_issues})

    attempt_coverage: AttemptCoverage = {"known_timed_attempts": None, "five_on_five": None, "other": None,
        "unresolved": None, "linked_five_on_five": None, "unclassified_events": None}
    location_coverage: LocationCoverage = {"known_timed_attempts": None, "normalized": None,
        "missing_coordinates": None, "unresolved_frame": None}
    if api is not None:
        counts, locations, linked, unclassified = Counter(), Counter(), 0, 0
        for row, event in zip(api, reconstructed_events):
            if not row["kind_valid"] or row["timed_period"] is None:
                unclassified += 1
            if row["kind_valid"] and row["type_key"] in _ATTEMPTS and row["timed_period"] is True:
                counts[event["classification"]] += 1
                locations[event["coordinate_status"]] += 1
                if event["classification"] == "five_on_five" and event["interval_indices"]:
                    linked += 1
        total = sum(counts.values())
        attempt_coverage = {"known_timed_attempts": total, "five_on_five": counts["five_on_five"], "other": counts["other"],
                            "unresolved": counts["unresolved"], "linked_five_on_five": linked, "unclassified_events": unclassified}
        location_coverage = {"known_timed_attempts": total, "normalized": locations["normalized"],
                             "missing_coordinates": locations["missing_coordinates"], "unresolved_frame": locations["unresolved_frame"]}
    return {"periods": periods, "intervals": intervals, "events": reconstructed_events, "player_exposure": exposures,
            "coverage": {"time": time_coverage, "attempts": attempt_coverage, "locations": location_coverage}, "issues": issues}
