"""matched recorded attempts and elapsed time from an explicit native corpus."""

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Literal

from .corpus_inputs import (
    array, integer, load_corpus, object_fields, read_document, require,
    schema, text, validate_envelope, validate_provenance,
)
from .captures import SOURCES
from .feature_data import ATTEMPT_KINDS
from .reconstruct import REPORT_CODES, lineup_classification
from .interpret import clock_seconds

Purpose = Literal["real", "fixture"]
Status = Literal["complete", "partial", "unavailable"]
_ATTEMPTS = ATTEMPT_KINDS
_SKATERS = frozenset(("C", "L", "R", "D", "F"))
_MEMBERS = ("away_skaters", "home_skaters", "away_goalies", "home_goalies")
_REAL_CORPUS = Path("/Users/nnandal/Documents/code/hockey-stats-local/03m-20261010/corpora/20252026/corpus.json")
_REAL_DIGEST = "1e4273d00107f8b7c04a49c70e4ac8a53153d46c493f2bf2bb2c4fd0e30ce034"
_MAX_INTEGER = 2**53 - 1
REASON_CODES = frozenset((
    "required_source_unavailable", "count_accounting_conflict",
    "event_evidence_unresolved", "unpaired_report_attempt",
    "elapsed_membership_unresolved", "period_horizon_unavailable",
    "player_toi_conflict", "roster_identity_unresolved",
    "unassigned_player_games", "no_5v5_exposure",
))


@dataclass(frozen=True)
class Player:
    player_id: str
    display_name: str | None
    reported_position: str
    name_source: dict | None
    position_source: dict


@dataclass(frozen=True)
class Game:
    game_id: str
    game_date: str
    away_team_id: str
    home_team_id: str
    away_abbreviation: str | None
    home_abbreviation: str | None
    included_seconds: int
    known_excluded_seconds: int
    known_unresolved_seconds: int
    horizon_unavailable: bool
    away_attempts: int | None
    home_attempts: int | None
    coverage_status: Status
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class Metrics:
    included_seconds: int
    known_excluded_seconds: int
    attempts_for: int | None
    attempts_against: int | None
    for_per60: float | None
    against_per60: float | None
    coverage_status: Status
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class PlayerGame(Metrics):
    player_id: str
    game_id: str
    team_id: str


@dataclass(frozen=True)
class PlayerSeason(Metrics):
    player_id: str
    teams: tuple[dict, ...]
    listed_games: int
    games_with_included_time: int
    partial_games: int
    unavailable_games: int


@dataclass(frozen=True)
class ObservedResult:
    season: str
    corpus_sha256: str
    players: tuple[Player, ...]
    games: tuple[Game, ...]
    player_games: tuple[PlayerGame, ...]
    player_seasons: tuple[PlayerSeason, ...]
    coverage: dict
    source_requested_min: str | None
    source_requested_max: str | None
    undated_sources: int
    source_implementations: tuple[dict, ...]
    receipt: dict


def _metrics(seconds, excluded, attempts_for, attempts_against, reasons):
    reasons = set(reasons) - {"no_5v5_exposure"}
    require(all(code in REASON_CODES for code in reasons), "observed", "unknown coverage reason")
    require(all(type(value) is int and 0 <= value <= _MAX_INTEGER
                for value in (seconds, excluded, attempts_for, attempts_against)),
            "observed", "metric exceeds safe nonnegative integer range")
    if seconds:
        return Metrics(seconds, excluded, attempts_for, attempts_against,
                       3600 * attempts_for / seconds, 3600 * attempts_against / seconds,
                       "partial" if reasons else "complete", tuple(sorted(reasons)))
    if reasons:
        return Metrics(seconds, excluded, None, None, None, None, "unavailable", tuple(sorted(reasons)))
    require(attempts_for == attempts_against == 0, "observed", "attempt without exposure")
    return Metrics(0, excluded, 0, 0, None, None, "complete", ("no_5v5_exposure",))


def _metric_fields(metrics):
    return {field: getattr(metrics, field) for field in Metrics.__dataclass_fields__}


def _members(row, loc):
    result = []
    for field in _MEMBERS:
        values = array(row[field], loc + "/" + field, nullable=True)
        for value in values:
            integer(value, loc + "/" + field, minimum=1)
        result.append(None if row[field] is None else tuple(values))
    return tuple(result)


def _roster_matches(members, identities, game):
    for field, players in zip(_MEMBERS, members):
        if players is None:
            return False
        team = game["away_team_id" if field.startswith("away") else "home_team_id"]
        for player in players:
            row = identities.get(player)
            if row is None or row["team_id"] != team:
                return False
            correct_role = (row["reported_position"] == "G" if field.endswith("goalies")
                            else row["reported_position"] in _SKATERS)
            if not correct_role:
                return False
    return True


def _issue_indices(value, size, loc):
    indices = array(value, loc)
    for index in indices:
        integer(index, loc)
        require(index < size, loc, "broken issue reference")
    require(len(indices) == len(set(indices)), loc, "duplicate issue reference")


def _validate_native(interpreted, native, events, recon, reports, loc):
    """check newly consumed bodies, partitions and native cross-references."""
    game = interpreted["game"]
    roster = array(interpreted["roster_records"], loc + "/roster", nullable=True)
    seen = set()
    by_player = defaultdict(list)
    for row in roster:
        object_fields(row, loc + "/roster", ("source_index", "first_name", "last_name"))
        index = row["source_index"]
        integer(index, loc + "/roster/source_index")
        require(index not in seen, loc, "duplicate roster source_index")
        seen.add(index)
        for field in ("first_name", "last_name"):
            text(row[field], loc + "/roster/" + field, nullable=True)
        if row["player_id"] is not None:
            by_player[row["player_id"]].append(row)
    identities = {pid: rows[0] for pid, rows in by_player.items() if len(rows) == 1
                  and rows[0]["team_id"] in (game["away_team_id"], game["home_team_id"])
                  and rows[0]["reported_position"] in _SKATERS | {"G"}}
    unassigned = not roster or any(
        row["reported_position"] != "G" and (
            row["player_id"] not in identities or row["reported_position"] not in _SKATERS
        ) for row in roster
    )
    for side in ("away", "home"):
        text(game.get(side + "_team_abbrev"), loc + "/game/" + side + "_team_abbrev", nullable=True)
    periods = array(native["periods"], loc + "/periods", nullable=True)
    by_period = {}
    for row in periods:
        number = row["period_number"]
        require(number not in by_period, loc, "duplicate period")
        require((row["status"] == "supported") == (row["end_seconds"] is not None), loc, "period availability disagrees")
        object_fields(row, loc + "/periods", ("issue_indices",))
        _issue_indices(row["issue_indices"], len(native["issues"]), loc + "/periods/issue_indices")
        by_period[number] = row
    time = native["coverage"]["time"]
    require(set(by_period) == set(time["expected_periods"] or []), loc, "period coverage differs")
    require({n for n, row in by_period.items() if row["status"] == "supported"}
            == set(time["supported_periods"]), loc, "supported period coverage differs")
    intervals = array(native["intervals"], loc + "/intervals", nullable=True)
    interval_members = []
    partition = defaultdict(list)
    duration = Counter()
    for index, row in enumerate(intervals):
        here = loc + f"/intervals/{index}"
        object_fields(row, here, ("period_number", "start_seconds", "end_seconds", "classification", "issue_indices", *_MEMBERS))
        for field in ("period_number", "start_seconds", "end_seconds"):
            integer(row[field], here + "/" + field, minimum=1 if field == "period_number" else 0)
        require(row["end_seconds"] > row["start_seconds"], here, "interval must be positive")
        period = by_period.get(row["period_number"])
        require(period is not None and period["status"] == "supported"
                and row["end_seconds"] <= period["end_seconds"], here, "interval outside supported horizon")
        require(row["classification"] in ("five_on_five", "other", "unresolved"), here, "invalid interval classification")
        members = _members(row, here)
        require(row["classification"] == "unresolved" or row["classification"] == lineup_classification(dict(zip(_MEMBERS, members))),
                here, "native interval classification differs from full membership")
        interval_members.append(members)
        _issue_indices(row["issue_indices"], len(native["issues"]), here + "/issue_indices")
        partition[row["period_number"]].append((row["start_seconds"], row["end_seconds"]))
        duration[row["classification"]] += row["end_seconds"] - row["start_seconds"]
    for number, period in by_period.items():
        if period["status"] == "supported":
            cursor = 0
            for start, end in sorted(partition[number]):
                require(start == cursor, loc, "elapsed intervals have gap or overlap")
                cursor = end
            require(cursor == period["end_seconds"], loc, "elapsed partition does not reach horizon")
    for name, classification in (("five_on_five_seconds", "five_on_five"), ("other_seconds", "other"), ("unresolved_seconds", "unresolved")):
        require(time[name] == (duration[classification] if time["supported_periods"] else None), loc, "elapsed coverage differs from intervals")
    require(time["known_seconds"] == (sum(row["end_seconds"] for row in periods if row["status"] == "supported")
            if time["supported_periods"] else None), loc, "elapsed horizon total differs")
    for index, report in reports.items():
        here = loc + f"/report_rows/{index}"
        object_fields(report, here, ("row_id", "period_number", "elapsed_seconds", "event_code", "penalty_shot", "time_in_period", "away_members", "home_members"))
        integer(report["period_number"], here + "/period_number", nullable=True, minimum=1)
        integer(report["elapsed_seconds"], here + "/elapsed_seconds", nullable=True)
        for field in ("row_id", "event_code", "time_in_period"):
            text(report[field], here + "/" + field, nullable=True)
        require(report["penalty_shot"] is None or type(report["penalty_shot"]) is bool, here, "invalid penalty-shot status")
        if report["elapsed_seconds"] is not None:
            require(report["period_number"] in (1, 2, 3, 4)
                    and clock_seconds(report["time_in_period"], "play-report", here, []) == report["elapsed_seconds"], here, "incoherent report clock")
        for side in ("away", "home"):
            for member in array(report[side + "_members"], here + "/" + side + "_members", nullable=True):
                object_fields(member, here, ("player_id", "reported_position"))
                integer(member["player_id"], here + "/member/player_id", nullable=True, minimum=1)
                text(member["reported_position"], here + "/member/reported_position", nullable=True)
    for index, event in events.items():
        row = recon[index]
        here = loc + f"/events/{index}"
        object_fields(row, here, ("match_status", "shift_relation", *_MEMBERS))
        require(row["match_status"] in ("matched", "unmatched", "ambiguous", "unavailable", "untimed"), here, "invalid native match status")
        require(row["shift_relation"] in ("before", "after", "both", "neither", "unavailable"), here, "invalid native shift relation")
        members = _members(row, here)
        require(row["classification"] != "five_on_five" or lineup_classification(dict(zip(_MEMBERS, members))) == "five_on_five",
                here, "native event classification differs from full membership")
        report = reports.get(row["report_source_index"])
        require((row["match_status"] == "matched") == (report is not None), here, "native match status and report link differ")
        if report is not None:
            require(report["period_number"] == event["period_number"]
                    and report["elapsed_seconds"] == event["elapsed_seconds"]
                    and REPORT_CODES.get(event["type_key"]) == report["event_code"], here, "native report link differs in period/clock/kind")
            for side in ("away", "home"):
                source = report[side + "_members"]
                for role, positions in (("skaters", _SKATERS), ("goalies", {"G"})):
                    expected = None if source is None else tuple(sorted(m["player_id"] for m in source
                        if m["player_id"] is not None and m["reported_position"] in positions))
                    require(members[_MEMBERS.index(side + "_" + role)] == expected, here, "native event membership differs from report")
        number, elapsed = event["period_number"], event["elapsed_seconds"]
        before = [i for i, interval in enumerate(intervals) if interval["period_number"] == number
                  and elapsed is not None and interval["start_seconds"] < elapsed <= interval["end_seconds"]]
        after = [i for i, interval in enumerate(intervals) if interval["period_number"] == number
                 and elapsed is not None and interval["start_seconds"] <= elapsed < interval["end_seconds"]]
        period = by_period.get(number)
        horizon = period["end_seconds"] if period is not None else None
        expected_indices, relation = [], "unavailable"
        if (row["classification"] in ("five_on_five", "other") and horizon is not None and elapsed is not None
                and 0 <= elapsed <= horizon and before + after
                and (elapsed == 0 or before) and (elapsed == horizon or after)
                and all(intervals[i]["classification"] != "unresolved" for i in before + after)):
            mb = [i for i in before if interval_members[i] == members]
            ma = [i for i in after if interval_members[i] == members]
            expected_indices = sorted(set(mb + ma))
            relation = "both" if mb and ma else "before" if mb else "after" if ma else "neither"
        require(row["interval_indices"] == expected_indices and row["shift_relation"] == relation,
                here, "native exposure link differs in period/clock/full membership")
    object_fields(native, loc, ("player_exposure",))
    require((native["player_exposure"] is None) == (interpreted["roster_records"] is None),
            loc, "native exposure collection availability differs from roster")
    exposures = {}
    elapsed_available = any(row["classification"] != "unresolved" for row in intervals)
    for row in array(native["player_exposure"], loc + "/player_exposure", nullable=True):
        object_fields(row, loc + "/player_exposure", ("player_id", "team_id", "supported_5v5_seconds", "complete", "issue_indices"))
        integer(row["player_id"], loc + "/player_exposure/player_id", minimum=1)
        integer(row["team_id"], loc + "/player_exposure/team_id", minimum=1)
        integer(row["supported_5v5_seconds"], loc + "/player_exposure/supported_5v5_seconds", nullable=True)
        require(type(row["complete"]) is bool, loc, "native exposure completeness must be boolean")
        require(row["player_id"] not in exposures, loc, "duplicate native player exposure")
        require(row["team_id"] in (game["away_team_id"], game["home_team_id"]), loc, "native exposure team outside game")
        _issue_indices(row["issue_indices"], len(native["issues"]), loc + "/player_exposure/issue_indices")
        side = "away_skaters" if row["team_id"] == game["away_team_id"] else "home_skaters"
        expected = sum(i["end_seconds"] - i["start_seconds"] for i in intervals
                       if i["classification"] == "five_on_five" and row["player_id"] in i[side]) if elapsed_available else None
        require(row["supported_5v5_seconds"] == expected, loc, "native player exposure differs from intervals")
        require(not row["complete"] or (not row["issue_indices"] and all(p["status"] == "supported" for p in periods)
                and not any(c["name"] == "player_toi" and c.get("player_id") == row["player_id"] and c["status"] == "mismatch"
                            for c in interpreted["checks"])), loc, "native complete exposure contradicts retained evidence")
        exposures[row["player_id"]] = row
    require(exposures.keys() == {pid for pid, row in identities.items() if row["reported_position"] in _SKATERS},
            loc, "native exposure population differs from supported roster")
    return identities, unassigned, intervals, interval_members, periods, exposures


def _game(entry, value, path):
    interpreted, native, events, recon, reports = validate_envelope(value, path, entry)
    identities, unassigned, intervals, members, periods, exposures = _validate_native(
        interpreted, native, events, recon, reports, str(path))
    game = interpreted["game"]
    reasons = set()
    if any(row["classification"] == "unresolved" for row in intervals):
        reasons.add("elapsed_membership_unresolved")
        if any(native["issues"][i]["code"] == "unresolved_shift_player" for row in intervals
               if row["classification"] == "unresolved" for i in row["issue_indices"]):
            reasons.add("roster_identity_unresolved")
    horizon_unavailable = not periods or any(row["status"] == "unavailable" for row in periods)
    if horizon_unavailable:
        reasons.add("period_horizon_unavailable")
    segments = []
    native_to_segment = {}
    mask = defaultdict(set)
    for index, row in enumerate(intervals):
        if row["classification"] != "five_on_five":
            continue
        if segments and segments[-1]["period"] == row["period_number"] and segments[-1]["end"] == row["start_seconds"] and segments[-1]["members"] == members[index]:
            segment = segments[-1]
            segment["end"] = row["end_seconds"]
            segment["indices"].append(index)
        else:
            segment = dict(period=row["period_number"], start=row["start_seconds"], end=row["end_seconds"], members=members[index], indices=[index])
            segments.append(segment)
        native_to_segment[index] = len(segments) - 1
        if not _roster_matches(members[index], identities, game):
            mask[len(segments) - 1].add("roster_identity_unresolved")
            reasons.add("roster_identity_unresolved")
    masks = []
    def remove(code, source, source_index, period=None, clock=None, whole=False):
        affected = [i for i, row in enumerate(segments) if whole or (
            (period is None or row["period"] == period) and
            (clock is None or row["start"] <= clock <= row["end"]))]
        for index in affected:
            mask[index].add(code)
        reasons.add(code)
        masks.append(dict(code=code, source=source, source_index=source_index,
                          period_number=period, elapsed_seconds=clock, segment_indices=affected))
    if interpreted["events"] is None or interpreted["report_rows"] is None:
        remove("required_source_unavailable", "interpreted", None, whole=True)
    for i, check in enumerate(interpreted["checks"]):
        if check["name"] in ("timed_goals", "timed_shots") and check["status"] == "mismatch":
            remove("count_accounting_conflict", "checks", i, whole=True)
    linked_reports = {row["report_source_index"] for row in recon.values() if row["report_source_index"] is not None}
    candidates = []
    dispositions = []
    for index, event in events.items():
        row = recon[index]
        report = reports.get(row["report_source_index"])
        modifier = row["goal_modifier_evidence"]
        known_penalty_shot = (report is not None and report["penalty_shot"] is True or
            modifier is not None and modifier["status"] == "reported" and modifier["reported_value"] == "penalty-shot")
        disposition = dict(source_index=index, report_source_index=row["report_source_index"],
                           shift_relation=row["shift_relation"], status="outside_population")
        dispositions.append(disposition)
        if event["timed_period"] is False or known_penalty_shot:
            continue
        if event["kind_valid"] and event["type_key"] not in _ATTEMPTS:
            continue
        if event["kind_valid"] and row["classification"] == "other":
            continue
        targets = {native_to_segment[i] for i in row["interval_indices"] if i in native_to_segment}
        valid = (event["kind_valid"] and event["timed_period"] is True
                 and event["type_key"] in _ATTEMPTS and row["classification"] == "five_on_five"
                 and row["match_status"] == "matched" and report is not None and report["penalty_shot"] is False
                 and event["shooting_team_id"] in (game["away_team_id"], game["home_team_id"])
                 and _roster_matches(_members(row, str(path)), identities, game)
                 and len(targets) == 1)
        if valid:
            target = next(iter(targets))
            candidates.append((target, event["shooting_team_id"], disposition))
            disposition.update(status="candidate", segment_index=target)
        else:
            disposition["status"] = "unresolved"
            roster_problem = (row["classification"] == "five_on_five"
                              and not _roster_matches(_members(row, str(path)), identities, game)) or any(
                native["issues"][i]["code"] == "unresolved_report_member" for i in row["issue_indices"])
            remove("roster_identity_unresolved" if roster_problem else "event_evidence_unresolved", "play-by-play", index,
                   event["period_number"] if event["timed_period"] is True else None,
                   event["elapsed_seconds"] if event["timed_period"] is True else None)
    report_dispositions = []
    for index, row in reports.items():
        if row["event_code"] not in ("GOAL", "SHOT", "MISS", "BLOCK") or index in linked_reports:
            continue
        disposition = dict(source_index=index, row_id=row["row_id"], status="outside_population")
        report_dispositions.append(disposition)
        if row["period_number"] == 5 or row["penalty_shot"] is True:
            continue
        disposition["status"] = "unresolved"
        number = row["period_number"] if row["period_number"] in (1, 2, 3, 4) else None
        remove("unpaired_report_attempt", "play-report", index, number, row["elapsed_seconds"] if number is not None else None)
    attempts = Counter()
    per_segment = Counter()
    for target, team, disposition in candidates:
        if target in mask:
            disposition["status"] = "masked"
        else:
            attempts[team] += 1
            per_segment[target, team] += 1
            disposition["status"] = "included"
    included = sum(row["end"] - row["start"] for i, row in enumerate(segments) if i not in mask)
    excluded = sum(row["end"] - row["start"] for i, row in enumerate(segments) if i in mask)
    unresolved = sum(row["end_seconds"] - row["start_seconds"] for row in intervals if row["classification"] == "unresolved")
    player_rows = []
    seconds_by_player, excluded_by_player, for_by_player, against_by_player = Counter(), Counter(), Counter(), Counter()
    for i, segment in enumerate(segments):
        seconds = segment["end"] - segment["start"]
        for side, team in ((0, game["away_team_id"]), (1, game["home_team_id"])):
            opponent = game["home_team_id"] if side == 0 else game["away_team_id"]
            for pid in segment["members"][side]:
                if i in mask:
                    excluded_by_player[pid] += seconds
                else:
                    seconds_by_player[pid] += seconds
                    for_by_player[pid] += per_segment[i, team]
                    against_by_player[pid] += per_segment[i, opponent]
    listed = {pid: row for pid, row in identities.items() if row["reported_position"] in _SKATERS}
    for pid, identity in sorted(listed.items()):
        player_reasons = set(reasons)
        exposure = exposures.get(pid)
        if exposure is None or exposure["complete"] is False:
            codes = {native["issues"][i]["code"] for i in exposure["issue_indices"]} if exposure else set()
            if "conflicting_player_toi" in codes or any(check["name"] == "player_toi" and check.get("player_id") == pid and check["status"] == "mismatch" for check in interpreted["checks"]):
                player_reasons.add("player_toi_conflict")
            elif not player_reasons & {"elapsed_membership_unresolved", "period_horizon_unavailable"}:
                player_reasons.add("elapsed_membership_unresolved")
        metric = _metrics(seconds_by_player[pid], excluded_by_player[pid], for_by_player[pid], against_by_player[pid], player_reasons)
        player_rows.append(PlayerGame(**_metric_fields(metric), player_id=str(pid), game_id=game["game_id"], team_id=str(identity["team_id"])))
    require(sum(row.included_seconds for row in player_rows) == 10 * included, path, "player exposure conservation failed")
    require(sum(row.attempts_for or 0 for row in player_rows) == sum(row.attempts_against or 0 for row in player_rows) == 5 * sum(attempts.values()), path, "player attempt conservation failed")
    game_metric = _metrics(included, excluded, attempts[game["away_team_id"]], attempts[game["home_team_id"]], reasons)
    output = Game(game["game_id"], game["game_date"], str(game["away_team_id"]), str(game["home_team_id"]),
                  game.get("away_team_abbrev"), game.get("home_team_abbrev"), included, excluded, unresolved,
                  horizon_unavailable, game_metric.attempts_for, game_metric.attempts_against,
                  game_metric.coverage_status, game_metric.reason_codes)
    receipt = dict(game_id=game["game_id"], status="reconstructed", source_inputs=interpreted["inputs"],
        unassigned_player_associations=unassigned, masks=masks,
        segments=[dict(period_number=s["period"], start_seconds=s["start"], end_seconds=s["end"],
                       interval_indices=s["indices"], excluded_reasons=sorted(mask.get(i, ()))) for i, s in enumerate(segments)],
        event_dispositions=dispositions, report_dispositions=report_dispositions,
        native_checks=interpreted["checks"], native_issues=interpreted["issues"] + native["issues"],
        identities=dict(physical_included_seconds=included, player_included_seconds=sum(r.included_seconds for r in player_rows),
                        included_attempts=sum(attempts.values()), player_attempts_for=sum(r.attempts_for or 0 for r in player_rows),
                        player_attempts_against=sum(r.attempts_against or 0 for r in player_rows)))
    return output, player_rows, listed, unassigned, receipt


def aggregate(corpus_path: Path | str, purpose: Purpose) -> ObservedResult:
    """admit explicit native evidence and return finalized, deterministic quantities."""
    require(purpose in ("real", "fixture"), "observed", "purpose must be real or fixture")
    path = Path(corpus_path).resolve(strict=True)
    inputs = []
    corpus, inventory, ledger = load_corpus(path, inputs)
    season = corpus["reference"]["requested_season"]
    require(type(season) is str and re.fullmatch(r"[0-9]{8}", season), path, "invalid season")
    if purpose == "fixture":
        require(corpus.get("purpose") == "fixture", path, "fixture corpus must explicitly declare purpose:fixture")
    if purpose == "real":
        require(path == _REAL_CORPUS and inputs[0]["sha256"] == _REAL_DIGEST
                and season == "20252026" and len(inventory) == 1312, path, "real publication requires the specified 2025–26 corpus")
    games, player_games, receipts, unassigned_games = [], [], [], []
    players = {}
    observations = []
    implementations = []
    def producer(value, loc):
        object_fields(value, loc, ("git_commit", "git_dirty", "python_version"))
        require(value["git_commit"] is None or type(value["git_commit"]) is str and re.fullmatch(r"[0-9a-f]{40}", value["git_commit"]), loc, "invalid producer git commit")
        require(value["git_dirty"] is None or type(value["git_dirty"]) is bool, loc, "invalid producer dirty state")
        text(value["python_version"], loc + "/python_version")
        identity = {key: value[key] for key in ("git_commit", "git_dirty", "python_version")}
        if identity not in implementations:
            implementations.append(identity)
    def sources(rows):
        for row in rows:
            requested = row["requested_at"]
            if requested is None:
                observations.append(None)
                continue
            try:
                parsed = datetime.fromisoformat(requested.replace("Z", "+00:00"))
                require(parsed.tzinfo is not None, path, "source retrieval timestamp lacks timezone")
            except ValueError as error:
                require(False, path, f"invalid source retrieval timestamp: {error}")
            observations.append(parsed.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"))
    object_fields(corpus, str(path), ("implementation",))
    producer(corpus["implementation"], str(path) + "/implementation")
    sources(corpus["reference"]["inputs"])
    for gid, entry in sorted(inventory.items(), key=lambda pair: (pair[1]["game_date"], pair[0])):
        row = ledger[gid]
        value = None
        if row["output_path"] is not None:
            envelope_path = path.parent / row["output_path"]
            value = read_document(envelope_path, "reconstruction", inputs)
            schema(value, str(envelope_path), 4, ("implementation", "interpreted", "reconstruction"))
            producer(value["implementation"], str(envelope_path) + "/implementation")
            schema(value["interpreted"], str(envelope_path) + "/interpreted", 4, ("inputs",))
            validate_provenance(value["interpreted"]["inputs"], str(envelope_path) + "/interpreted/inputs", SOURCES)
            if "interpretation" in value["interpreted"]:
                producer(value["interpreted"]["interpretation"], str(envelope_path) + "/interpreted/interpretation")
            sources(value["interpreted"]["inputs"])
        if row["status"] != "reconstructed":
            reasons = ("required_source_unavailable",)
            game = Game(gid, entry["game_date"], str(entry["away_team_id"]), str(entry["home_team_id"]), None, None,
                        0, 0, 0, True, None, None, "unavailable", reasons)
            games.append(game)
            receipts.append(dict(game_id=gid, status=row["status"], reason=row["reason"],
                                 source_inputs=value["interpreted"]["inputs"] if value is not None else [],
                                 event_dispositions=[], unassigned_player_associations=True))
            unassigned_games.append(dict(game_id=gid, date=entry["game_date"], away_team_id=game.away_team_id,
                                         home_team_id=game.home_team_id, reason_codes=list(reasons)))
            continue
        game, rows, listed, unassigned, receipt = _game(entry, value, envelope_path)
        games.append(game)
        player_games.extend(rows)
        receipts.append(receipt)
        receipt["source_implementation"] = value["implementation"]
        receipt["interpretation_implementation"] = value["interpreted"].get("interpretation")
        if unassigned:
            unassigned_games.append(dict(game_id=gid, date=game.game_date, away_team_id=game.away_team_id,
                                         home_team_id=game.home_team_id,
                                         reason_codes=sorted(set(game.reason_codes) | {"roster_identity_unresolved"})))
        for pid, observation in listed.items():
            locator = dict(game_id=gid, source_index=observation["source_index"])
            previous = players.get(pid)
            name = (observation["first_name"] + " " + observation["last_name"]
                    if observation["first_name"] and observation["last_name"] else None)
            players[pid] = Player(str(pid), name if name is not None else previous.display_name if previous else None,
                                  observation["reported_position"], locator if name is not None else previous.name_source if previous else None,
                                  locator)
    by_player = defaultdict(list)
    game_index = {row.game_id: row for row in games}
    for row in player_games:
        by_player[row.player_id].append(row)
    seasons = []
    player_reductions = []
    for pid, rows in sorted(by_player.items(), key=lambda item: int(item[0])):
        reasons = {reason for row in rows for reason in row.reason_codes if reason != "no_5v5_exposure"}
        if unassigned_games:
            reasons.add("unassigned_player_games")
        seconds = sum(row.included_seconds for row in rows)
        excluded = sum(row.known_excluded_seconds for row in rows)
        for_count = sum(row.attempts_for or 0 for row in rows)
        against_count = sum(row.attempts_against or 0 for row in rows)
        metric = _metrics(seconds, excluded, for_count, against_count, reasons)
        teams = {}
        for row in rows:
            game = game_index[row.game_id]
            teams[row.team_id] = dict(id=row.team_id, abbreviation=game.away_abbreviation if row.team_id == game.away_team_id else game.home_abbreviation)
        seasons.append(PlayerSeason(**_metric_fields(metric), player_id=pid,
            teams=tuple(teams[key] for key in sorted(teams, key=int)), listed_games=len(rows),
            games_with_included_time=sum(row.included_seconds > 0 for row in rows),
            partial_games=sum(row.coverage_status == "partial" for row in rows),
            unavailable_games=sum(row.coverage_status == "unavailable" for row in rows)))
        player_reductions.append(dict(player_id=pid, listed_games=len(rows), included_seconds=seconds,
            known_excluded_seconds=excluded, available_attempts_for=for_count, available_attempts_against=against_count,
            projected_attempts_for=metric.attempts_for, projected_attempts_against=metric.attempts_against))
        require(sum(row.included_seconds for row in rows) == metric.included_seconds
                and (metric.attempts_for is None or metric.attempts_for == for_count)
                and (metric.attempts_against is None or metric.attempts_against == against_count), path, "season reduction failed")
    require(sum(row.included_seconds for row in player_games) == 10 * sum(row.included_seconds for row in games), path, "corpus exposure conservation failed")
    require(sum(row.attempts_for or 0 for row in player_games) == sum(row.attempts_against or 0 for row in player_games)
            == 5 * sum((row.away_attempts or 0) + (row.home_attempts or 0) for row in games), path, "corpus attempt conservation failed")
    require(purpose != "real" or any(row.included_seconds > 0 for row in games), path, "real candidate has no supported positive exposure")
    reason_counts = Counter(code for row in games for code in row.reason_codes)
    coverage = dict(inventory_games=len(games), games_with_included_time=sum(row.included_seconds > 0 for row in games),
        partial_games=sum(row.coverage_status == "partial" for row in games), unavailable_games=sum(row.coverage_status == "unavailable" for row in games),
        games_with_unassigned_player_associations=len(unassigned_games),
        reason_game_counts=[dict(code=code, games=count) for code, count in sorted(reason_counts.items())], unassigned_games=unassigned_games)
    dated = [value for value in observations if value is not None]
    receipt = dict(consumed=inputs, games=receipts, player_reductions=player_reductions, aggregate_identities=dict(
        physical_included_seconds=sum(row.included_seconds for row in games),
        player_included_seconds=sum(row.included_seconds for row in player_games),
        known_excluded_seconds=sum(row.known_excluded_seconds for row in games),
        known_unresolved_seconds=sum(row.known_unresolved_seconds for row in games),
        included_attempts=sum((row.away_attempts or 0) + (row.home_attempts or 0) for row in games),
        player_attempts_for=sum(row.attempts_for or 0 for row in player_games),
        player_attempts_against=sum(row.attempts_against or 0 for row in player_games)))
    return ObservedResult(season, inputs[0]["sha256"], tuple(players[pid] for pid in sorted(players)), tuple(games),
        tuple(sorted(player_games, key=lambda row: (int(row.player_id), game_index[row.game_id].game_date, row.game_id))),
        tuple(seasons), coverage, min(dated) if dated else None, max(dated) if dated else None,
        sum(value is None for value in observations), tuple(implementations), receipt)
