"""matched recorded-count populations, exposure ledgers and annual sufficient statistics.

``prepare_game`` preserves native memberships and chronology; each positive
segment has two directions or neither. ``prepare_attribution`` streams the
segments and sparse count rows and returns the completed manifest reference.
Neither operation fits a model or applies chance-model eligibility.
"""

from collections import Counter, defaultdict
from contextlib import ExitStack
import hashlib
import json
import math
from pathlib import Path
import time
from typing import TypedDict

import numpy as np

from .artifacts import clean_implementation, implementation, linked_path, require, resources, rows, write_json
from .captures import InputContractError
from .chance_cli import identity, output_path, read_json
from .corpus_inputs import load_corpus, read_document, validate_envelope
from .game_chronology import score_chronology
from .reconstruct import Interval
from .shot_origins import cell_id, grid, in_rink

POPULATIONS = ("all_attempts", "unblocked_spatial")
ATTEMPTS = frozenset(("goal", "shot-on-goal", "missed-shot", "blocked-shot"))
MEMBERSHIP_FIELDS = ("away_skaters", "home_skaters", "away_goalies", "home_goalies")
RESEARCH_CORPORA = {
    "20212022": "30eb12b290ccd9af9eae7ade8c7dcd5f285129b52b646eec3fced3e2628badc8",
    "20222023": "735c741115725e7c4fe8a28782f352c787895db5eea2123b2b7ec27b4db1e02a",
    "20232024": "92392c80b145d72c3be759a94b8113db04a7e8d26a4404e1e15a40119db6a414",
    "20242025": "46208ef0830949de4faf1e6695f052c9fdbc23bca5b86fa045c3552d3d467639",
    "20252026": "8229fc6686fa03c4f6cc00d68d68aac1d1d2b83d6950d56eeebb7c9fc923fd43",
}
DESIGN = {
    "grid": "native_656_five_foot",
    "player_columns": "all_seen_offense_then_defense",
    "context": ["attacking_home_away", "period_1_2_3_overtime", "attacking_pre_score_clipped_minus3_plus3"],
    "zero_event_segments": True,
    "paired_team_direction_masks": True,
    "matched_spatial_exclusion": True,
    "pair_selection": ["greatest_shared_scalar_exposure", "greatest_combined_scalar_exposure_with_zero_shared"],
    "pair_ties": "sorted_player_ids",
}


class ArtifactReference(TypedDict):
    path: str
    sha256: str


def _membership(row: dict, roster: dict[int, list[dict]], game: dict) -> bool:
    """check native five-on-five admission against stable roster identities."""
    members = []
    for side in ("away", "home"):
        for role, number in (("skaters", 5), ("goalies", 1)):
            values = row.get(side + "_" + role)
            if type(values) is not list or len(values) != number:
                return False
            for player in values:
                candidates = roster.get(player, [])
                if len(candidates) != 1 or candidates[0]["team_id"] != game[side + "_team_id"]:
                    return False
                position = candidates[0]["reported_position"]
                if position not in (("G",) if role == "goalies" else ("C", "L", "R", "D", "F")):
                    return False
            members.extend(values)
    return len(members) == len(set(members))


def prepare_game(envelope: dict, envelope_path: Path, inventory_entry: dict) -> dict:
    """return inspectable positive segments, event dispositions and game coverage."""
    interpreted, reconstructed, events, native_events, reports = validate_envelope(
        envelope, envelope_path, inventory_entry)
    game = interpreted["game"]
    scores, score_failures, ordered, _ = score_chronology(interpreted, events, game)
    roster = defaultdict(list)
    for player in interpreted["roster_records"] or []:
        if player["player_id"] is not None:
            roster[player["player_id"]].append(player)
    goals = [event for event in ordered or [] if event["type_key"] == "goal"
             and event["timed_period"] is True] if not score_failures else []
    changes = []
    for event in goals:
        pre = scores[event["source_index"]]
        post = dict(pre)
        post["away" if event["shooting_team_id"] == game["away_team_id"] else "home"] += 1
        changes.append(dict(source_index=event["source_index"], period=event["period_number"],
                            elapsed_seconds=event["elapsed_seconds"], pre_score=pre, post_score=post))
    segments = []
    last_end = {}
    for native_index, interval in enumerate(reconstructed["intervals"] or []):
        require(Interval.__required_keys__ <= interval.keys(), "incomplete native elapsed interval")
        period, start, end = interval["period_number"], interval["start_seconds"], interval["end_seconds"]
        require(type(period) is int and period in (1, 2, 3, 4)
                and type(start) is int and type(end) is int and 0 <= start < end,
                "native intervals require supported periods and positive elapsed time")
        require(period not in last_end or start == last_end[period],
                "native elapsed intervals must partition each supported period")
        last_end[period] = end
        classification = interval["classification"]
        require(classification in ("five_on_five", "other", "unresolved"),
                "unsupported native interval classification")
        if classification == "five_on_five":
            require(_membership(interval, roster, game), "native 5v5 interval lacks stable roster membership")
        boundaries = sorted({start, end} | {goal["elapsed_seconds"] for goal in goals
                            if goal["period_number"] == period and start < goal["elapsed_seconds"] < end})
        for left, right in zip(boundaries[:-1], boundaries[1:], strict=True):
            earlier = [change for change in changes if change["period"] < period
                       or change["period"] == period and change["elapsed_seconds"] <= left]
            score = earlier[-1]["post_score"] if earlier else {"away": 0, "home": 0}
            difference = max(-3, min(3, score["home"] - score["away"])) if not score_failures else None
            reasons = []
            if classification == "unresolved":
                reasons.append(dict(reason="membership_unresolved", event_source_index=None))
            if score_failures:
                reasons.append(dict(reason="score_unavailable", event_source_index=None))
            segment = dict(game_id=game["game_id"], season=game["season"], period=period,
                           start=left, end=right, interval_indices=[native_index],
                           **{field: interval[field] for field in MEMBERSHIP_FIELDS},
                           classification=classification, score=dict(score) if not score_failures else None,
                           score_difference=difference, score_changes=[],
                           masks={population: list(reasons) for population in POPULATIONS},
                           counts={side: {"all_attempts": 0, "unblocked_spatial": []}
                                   for side in ("away", "home")})
            previous = segments[-1] if segments else None
            if (previous is not None and previous["period"] == period and previous["end"] == left
                    and previous["classification"] == classification
                    and previous["score_difference"] == difference
                    and all(previous[field] == segment[field] for field in MEMBERSHIP_FIELDS)):
                previous["end"] = right
                if native_index not in previous["interval_indices"]:
                    previous["interval_indices"].append(native_index)
            else:
                segments.append(segment)
    for segment in segments:
        segment["score_changes"] = [change for change in changes if change["period"] == segment["period"]
                                    and segment["start"] <= change["elapsed_seconds"] <= segment["end"]]
    centers, _ = grid()
    dispositions = []
    cell_counts = [{side: Counter() for side in ("away", "home")} for _ in segments]
    for index, event in events.items():
        if not event["kind_valid"] or event["type_key"] not in ATTEMPTS:
            continue
        native = native_events[index]
        report = reports.get(native["report_source_index"])
        modifier = native["goal_modifier_evidence"]
        outside = (event["timed_period"] is False or native["classification"] in ("other", "untimed")
                   or report is not None and report["penalty_shot"] is True
                   or modifier is not None and modifier["status"] == "reported"
                   and modifier["reported_value"] == "penalty-shot")
        period, clock = event["period_number"], event["elapsed_seconds"]
        side = ("away" if event["shooting_team_id"] == game["away_team_id"] else
                "home" if event["shooting_team_id"] == game["home_team_id"] else None)
        plausible = [i for i, segment in enumerate(segments)
                     if period is None or segment["period"] == period
                     and (clock is None or segment["start"] <= clock <= segment["end"])]
        reasons = []
        compatible = []
        pre = scores.get(index)
        if not outside:
            if score_failures:
                reasons.append("score_unavailable")
            if side is None:
                reasons.append("ownership_unresolved")
            if event["timed_period"] is not True or native["classification"] != "five_on_five":
                reasons.append("membership_unresolved")
            elif not _membership(native, roster, game):
                raise InputContractError("native 5v5 event lacks stable roster membership")
            if not reasons and clock is not None and period is not None:
                difference = max(-3, min(3, pre["home"] - pre["away"]))
                require(native.get("shift_relation") in ("before", "after", "both", "neither", "unavailable"),
                        "unsupported native event shift relation")
                for i in plausible:
                    segment = segments[i]
                    if (segment["classification"] == "five_on_five"
                            and segment["score_difference"] == difference
                            and set(segment["interval_indices"]) & set(native["interval_indices"])
                            and all(segment[field] == native[field] for field in MEMBERSHIP_FIELDS)):
                        compatible.append(i)
            if len(compatible) != 1:
                reasons.append("segment_assignment_unresolved")
        assigned = compatible[0] if len(compatible) == 1 and not outside else None
        target_segments = [assigned] if assigned is not None else plausible
        if not outside and reasons:
            for i in plausible:
                for population in POPULATIONS:
                    segments[i]["masks"][population].extend(
                        dict(reason=reason, event_source_index=index) for reason in reasons)
        spatial_cell = None
        location_reason = None
        if event["type_key"] != "blocked-shot" and not outside:
            point = (native["attacking_x"], native["attacking_y"])
            if (native["coordinate_status"] != "normalized"
                    or any(type(value) not in (int, float) or not math.isfinite(value) for value in point)):
                location_reason = "location_unavailable"
            elif not in_rink(*point):
                location_reason = "location_outside_rink"
            else:
                spatial_cell = cell_id(point, centers)
            if location_reason:
                for i in target_segments:
                    segments[i]["masks"]["unblocked_spatial"].append(
                        dict(reason=location_reason, event_source_index=index))
        if assigned is not None and not reasons:
            segments[assigned]["counts"][side]["all_attempts"] += 1
            if spatial_cell is not None:
                cell_counts[assigned][side][spatial_cell] += 1
        dispositions.append(dict(game_id=game["game_id"], season=game["season"], source_index=index,
                                 event_id=event["event_id"], type=event["type_key"], period=period, clock=clock,
                                 shooting_team_id=event["shooting_team_id"], side=side,
                                 membership={field: native[field] for field in MEMBERSHIP_FIELDS},
                                 classification=native["classification"], interval_indices=native["interval_indices"],
                                 shift_relation=native["shift_relation"], pre_score=pre,
                                 report_source_index=native["report_source_index"],
                                 reconstruction_issue_indices=native["issue_indices"],
                                 assigned_segment=assigned, plausible_segments=plausible,
                                 cell_id=spatial_cell, reasons=reasons, location_reason=location_reason,
                                 all_attempts="out_of_scope" if outside else "pending",
                                 unblocked_spatial="out_of_scope" if outside else
                                 "not_applicable" if event["type_key"] == "blocked-shot" else "pending"))
    for i, segment in enumerate(segments):
        for side in ("away", "home"):
            segment["counts"][side]["unblocked_spatial"] = sorted(cell_counts[i][side].items())
        for population in POPULATIONS:
            segment["masks"][population] = [dict(reason=reason, event_source_index=index)
                for reason, index in dict.fromkeys((item["reason"], item["event_source_index"])
                                                   for item in segment["masks"][population])]
    for event in dispositions:
        for population in POPULATIONS:
            if event[population] != "pending":
                continue
            assigned = event["assigned_segment"]
            event[population] = ("retained" if assigned is not None
                                 and not segments[assigned]["masks"][population] else "excluded")
            event[population + "_collateral"] = (event[population] == "excluded" and assigned is not None
                and not event["reasons"] and (population == "all_attempts" or event["location_reason"] is None))
    coverage = dict(game_id=game["game_id"], season=game["season"],
                    source=str(envelope_path), native_coverage=reconstructed["coverage"],
                    periods=reconstructed["periods"], score_failures=score_failures,
                    unresolved_membership_seconds=sum(segment["end"] - segment["start"] for segment in segments
                        if segment["classification"] == "unresolved"),
                    unknown_horizon_periods=[period["period_number"] for period in reconstructed["periods"] or []
                                             if period["status"] != "supported"],
                    populations={}, teams=[], players=[])
    native_exposure = {row["player_id"]: row for row in reconstructed["player_exposure"] or []}
    common = [segment for segment in segments if segment["classification"] == "five_on_five"
              and not segment["masks"]["unblocked_spatial"]]
    common_counts = dict(
        common_population_seconds=sum(segment["end"] - segment["start"] for segment in common),
        common_population_all_attempts=sum(segment["counts"][side]["all_attempts"]
            for segment in common for side in ("away", "home")),
        common_population_unblocked_attempts=sum(count for segment in common for side in ("away", "home")
            for _, count in segment["counts"][side]["unblocked_spatial"]))
    for population in POPULATIONS:
        supported = [segment for segment in segments if segment["classification"] == "five_on_five"]
        retained = [segment for segment in supported if not segment["masks"][population]]
        relevant = [event for event in dispositions if event[population] not in ("out_of_scope", "not_applicable")]
        coverage["populations"][population] = dict(
            supported_seconds=sum(segment["end"] - segment["start"] for segment in supported),
            retained_seconds=sum(segment["end"] - segment["start"] for segment in retained),
            excluded_seconds=sum(segment["end"] - segment["start"] for segment in supported
                                 if segment["masks"][population]),
            recognized_attempts=len(relevant),
            retained_attempts=sum(event[population] == "retained" for event in relevant),
            excluded_attempts=sum(event[population] == "excluded" for event in relevant),
            collateral_attempts=sum(event.get(population + "_collateral", False) for event in relevant),
            unassigned_attempts=sum(event["assigned_segment"] is None for event in relevant),
            unallocated_ownership_attempts=sum(event["side"] is None for event in relevant),
            **common_counts,
            unresolved_membership_seconds=coverage["unresolved_membership_seconds"],
            unknown_horizon_periods=coverage["unknown_horizon_periods"])
        for side in ("away", "home"):
            team = game[side + "_team_id"]
            team_events = [event for event in relevant if event["side"] == side]
            coverage["teams"].append(dict(population=population, team_id=team,
                retained_seconds=coverage["populations"][population]["retained_seconds"],
                excluded_seconds=coverage["populations"][population]["excluded_seconds"],
                unresolved_membership_seconds=coverage["unresolved_membership_seconds"],
                unknown_horizon_periods=coverage["unknown_horizon_periods"],
                retained_attempts=sum(event[population] == "retained" for event in team_events),
                excluded_attempts=sum(event[population] == "excluded" for event in team_events)))
            players = sorted(player for player, candidates in roster.items() if len(candidates) == 1
                             and candidates[0]["team_id"] == team
                             and candidates[0]["reported_position"] in ("C", "L", "R", "D", "F"))
            unknown_membership_seconds = sum(segment["end"] - segment["start"] for segment in segments
                if segment["classification"] == "unresolved" and segment[side + "_skaters"] is None)
            for player in players:
                admitted = [segment for segment in retained if player in segment[side + "_skaters"]]
                excluded = [segment for segment in supported if player in segment[side + "_skaters"]
                            and segment["masks"][population]]
                on_ice = [event for event in relevant if player in (event["membership"][side + "_skaters"] or [])]
                coverage["players"].append(dict(population=population, team_id=team, player_id=player,
                    retained_seconds=sum(segment["end"] - segment["start"] for segment in admitted),
                    excluded_seconds=sum(segment["end"] - segment["start"] for segment in excluded),
                    native_exposure=native_exposure.get(player),
                    unresolved_membership_seconds=None if unknown_membership_seconds else sum(
                        segment["end"] - segment["start"] for segment in segments
                        if segment["classification"] == "unresolved" and player in (segment[side + "_skaters"] or [])),
                    unresolved_membership_known_seconds=sum(segment["end"] - segment["start"] for segment in segments
                        if segment["classification"] == "unresolved" and player in (segment[side + "_skaters"] or [])),
                    unknown_membership_seconds=unknown_membership_seconds,
                    unknown_event_membership_attempts=sum(event["membership"][side + "_skaters"] is None
                                                          for event in relevant),
                    for_retained=sum(event[population] == "retained" and event["side"] == side for event in on_ice),
                    against_retained=sum(event[population] == "retained" and event["side"] not in (side, None) for event in on_ice),
                    for_excluded=sum(event[population] == "excluded" and event["side"] == side for event in on_ice),
                    against_excluded=sum(event[population] == "excluded" and event["side"] not in (side, None) for event in on_ice)))
    return dict(segments=segments, events=dispositions, coverage=coverage, score_failures=score_failures)


def _line(destination, value: dict) -> None:
    destination.write(json.dumps(value, allow_nan=False, separators=(",", ":")) + "\n")


def prepare_attribution(selection: Path | str, protocol: Path | str, out: Path | str) -> ArtifactReference:
    """prepare native populations and residualized statistics without fitting."""
    started = time.monotonic()
    selection_path, protocol_path = Path(selection).resolve(strict=True), Path(protocol).resolve(strict=True)
    inputs = []
    selected = read_document(selection_path, "selection", inputs)
    frozen = read_json(protocol_path)
    require(type(selected) is dict and set(selected) == {
        "schema_version", "kind", "purpose", "corpora", "target_season"}
        and type(selected["schema_version"]) is int and selected["schema_version"] == 1
        and selected["kind"] == "attribution_selection"
        and selected["purpose"] in ("research", "fixture_exercise"), "invalid attribution selection")
    required_protocol = {"schema_version", "kind", "purpose", "implementation", "selection", "spec_snapshot",
                         "source_binding", "seasons", "target_season", "populations", "design", "scale",
                         "generator", "scenarios", "components", "units", "output_root"}
    require(type(frozen) is dict and set(frozen) == required_protocol
            and type(frozen["schema_version"]) is int and frozen["schema_version"] == 1
            and frozen["kind"] == "attribution_protocol", "invalid attribution protocol")
    require(linked_path(frozen["selection"]) == selection_path and frozen["purpose"] == selected["purpose"],
            "protocol selection/purpose mismatch")
    linked_path(frozen["spec_snapshot"])
    require(frozen["populations"] == list(POPULATIONS), "protocol population mismatch")
    require(type(frozen["design"]) is dict and all(frozen["design"].get(key) == value for key, value in DESIGN.items()),
            "protocol/native population design mismatch")
    current_implementation = implementation()
    if selected["purpose"] == "research":
        clean_implementation(current_implementation)
        require(frozen["implementation"] == current_implementation, "research implementation differs from frozen protocol")
    corpora = selected["corpora"]
    require(type(corpora) is list and bool(corpora), "attribution requires ordered corpus seasons")
    require(all(type(row) is dict and set(row) == {"season", "corpus_path"}
                and type(row["season"]) is str and len(row["season"]) == 8 for row in corpora),
            "invalid attribution corpus selection")
    seasons = [row["season"] for row in corpora]
    require(seasons == sorted(set(seasons)) and selected["target_season"] == seasons[-1]
            and frozen["seasons"] == seasons and frozen["target_season"] == seasons[-1],
            "attribution years/target must match ordered protocol years")
    paths = [(selection_path.parent / row["corpus_path"]).resolve(strict=True) for row in corpora]
    require(len(paths) == len(set(paths)), "duplicate attribution corpus path")
    if selected["purpose"] == "research":
        require(seasons == list(RESEARCH_CORPORA), "research requires the five fixed 03m seasons")
        require(all(identity(path)["sha256"] == RESEARCH_CORPORA[season]
                    for season, path in zip(seasons, paths, strict=True)), "research corpus digest mismatch")
    binding = frozen["source_binding"]
    require(type(binding) is dict and set(binding) == {"selection", "audit", "corpora"},
            "invalid frozen source binding")
    for key in ("selection", "audit"):
        if binding[key] is not None:
            linked_path(binding[key])
        else:
            require(selected["purpose"] == "fixture_exercise", "research source binding is missing")
    require(binding["corpora"] == [dict(season=season, **identity(path))
        for season, path in zip(seasons, paths, strict=True)], "protocol corpus binding mismatch")
    output = output_path(str(out), [str(path.parent) for path in paths] +
                         [str(selection_path.parent), str(protocol_path.parent)])
    require(output.is_relative_to(Path(frozen["output_root"]).resolve()), "output differs from frozen root")
    if selected["purpose"] == "research":
        require(output.is_relative_to(Path("/Volumes/Expansion/hockey-stats"))
                and all(path.is_relative_to(Path("/Volumes/Expansion/hockey-stats")) for path in paths),
                "research inputs and outputs must remain external")
    output.mkdir()
    (output / "rows").mkdir()
    annual = {(population, season): dict(players=set(), strata=set(), seconds=0, count=0, row_count=0)
              for population in POPULATIONS for season in seasons}
    exposure = Counter()
    shared = Counter()
    game_totals = Counter()
    segments_path, events_path, coverage_path = [output / name for name in
        ("segments.jsonl", "events.jsonl", "coverage.jsonl")]
    row_paths = {(population, season): output / "rows" / f"{population}-{season}.jsonl"
                 for population in POPULATIONS for season in seasons}
    season_coverage = {(population, season): Counter() for population in POPULATIONS for season in seasons}
    with ExitStack() as files:
        segment_file = files.enter_context(segments_path.open("x"))
        event_file = files.enter_context(events_path.open("x"))
        coverage_file = files.enter_context(coverage_path.open("x"))
        row_files = {key: files.enter_context(path.open("x")) for key, path in row_paths.items()}
        for season, corpus_path in zip(seasons, paths, strict=True):
            document, inventory, ledger = load_corpus(corpus_path, inputs)
            require(document["reference"]["requested_season"] == season, "selected/reference season mismatch")
            if selected["purpose"] == "research":
                require(len(inventory) == 1312, "research inventory requires 1312 games per season")
            for game_id in sorted(inventory, key=lambda gid: (inventory[gid]["game_date"], gid)):
                entry, source = inventory[game_id], ledger[game_id]
                game_totals[season] += 1
                if source["status"] in ("input_error", "identity_mismatch"):
                    raise InputContractError(f"{corpus_path}/games/{game_id}: {source['status']}: {source['reason']}")
                if source["status"] != "reconstructed":
                    for population in POPULATIONS:
                        season_coverage[(population, season)]["missing_games"] += 1
                    _line(coverage_file, dict(game_id=game_id, season=season, source=str(corpus_path),
                        source_status=source["status"], reason=source["reason"], populations=None))
                    continue
                envelope_path = (corpus_path.parent / source["output_path"]).resolve(strict=True)
                envelope = read_document(envelope_path, "game", inputs)
                prepared = prepare_game(envelope, envelope_path, entry)
                _line(coverage_file, prepared["coverage"])
                for population in POPULATIONS:
                    season_coverage[(population, season)].update(
                        measured_games=1, score_unavailable_games=int(bool(prepared["score_failures"])),
                        unknown_horizon_games=int(bool(prepared["coverage"]["unknown_horizon_periods"])),
                        unresolved_membership_games=int(bool(prepared["coverage"]["unresolved_membership_seconds"])))
                    season_coverage[(population, season)].update({key: value
                        for key, value in prepared["coverage"]["populations"][population].items()
                        if type(value) is int})
                for event in prepared["events"]:
                    _line(event_file, event)
                for segment_index, segment in enumerate(prepared["segments"]):
                    _line(segment_file, dict(segment_index=segment_index, **segment))
                    seconds = segment["end"] - segment["start"]
                    if (season == seasons[-1] and segment["classification"] == "five_on_five"
                            and not segment["masks"]["all_attempts"]):
                        players = sorted(segment["away_skaters"] + segment["home_skaters"])
                        exposure.update({player: seconds for player in players})
                        for i, first in enumerate(players):
                            for second in players[i + 1:]:
                                shared[(first, second)] += seconds
                    for population in POPULATIONS:
                        if segment["classification"] != "five_on_five" or segment["masks"][population]:
                            continue
                        summary = annual[(population, season)]
                        summary["players"].update(segment["away_skaters"] + segment["home_skaters"])
                        for side in ("away", "home"):
                            opponent = "home" if side == "away" else "away"
                            stratum = (side, str(segment["period"]) if segment["period"] <= 3 else "overtime",
                                       segment["score_difference"] * (1 if side == "home" else -1))
                            counts = ([(0, segment["counts"][side][population])]
                                      if population == "all_attempts" else segment["counts"][side][population])
                            counts = [(cell, count) for cell, count in counts if count]
                            summary["strata"].add(stratum)
                            summary["seconds"] += seconds
                            summary["count"] += sum(count for _, count in counts)
                            summary["row_count"] += 1
                            _line(row_files[(population, season)], dict(population=population, season=season, game_id=game_id,
                                period=segment["period"], start=segment["start"], end=segment["end"],
                                attacking_team=entry[side + "_team_id"], segment_index=segment_index,
                                offense=segment[side + "_skaters"], defense=segment[opponent + "_skaters"],
                                stratum=stratum, seconds=seconds, counts=counts))
    players = sorted(exposure)
    greatest_shared = min(shared, key=lambda pair: (-shared[pair], pair)) if shared else None
    independent = [(first, second) for i, first in enumerate(players) for second in players[i + 1:]
                   if shared[(first, second)] == 0]
    greatest_disjoint = min(independent, key=lambda pair: (-exposure[pair[0]] - exposure[pair[1]], pair)) if independent else None
    annual_documents = []
    for population in POPULATIONS:
        for season in seasons:
            summary = annual[(population, season)]
            current_players, strata = sorted(summary["players"]), sorted(summary["strata"])
            n, k, h = len(current_players), 1 if population == "all_attempts" else 656, len(strata)
            row_path = row_paths[(population, season)]
            if summary["seconds"] == 0 or summary["count"] == 0:
                annual_documents.append(dict(population=population, season=season, players=current_players,
                    strata=strata, status="unavailable", reason="no_positive_exposure_or_count", r=None,
                    arrays=None, rows=identity(row_path), coverage=dict(season_coverage[(population, season)]), row_count=summary["row_count"], team_seconds=summary["seconds"],
                    total_count=summary["count"]))
                continue
            player_index = {player: index for index, player in enumerate(current_players)}
            stratum_index = {stratum: index for index, stratum in enumerate(strata)}
            H = np.zeros((2 * n, 2 * n))
            T = np.zeros((2 * n, k))
            stratum_e = np.zeros(h)
            stratum_x = np.zeros((h, 2 * n))
            stratum_n = np.zeros((h, k))
            player_exposure = np.zeros(n)
            response_counts = np.zeros(k)
            yy = 0.0
            for row in rows(row_path):
                e = row["seconds"] / 3600
                indices = np.array([player_index[player] for player in row["offense"]] +
                                   [n + player_index[player] for player in row["defense"]])
                s = stratum_index[tuple(row["stratum"])]
                H[np.ix_(indices, indices)] += e
                stratum_e[s] += e
                stratum_x[s, indices] += e
                player_exposure[indices[:5]] += row["seconds"]
                total = sum(count for _, count in row["counts"])
                yy += total * total / e
                for cell, count in row["counts"]:
                    T[indices, cell] += count
                    stratum_n[s, cell] += count
                    response_counts[cell] += count
            rate = summary["count"] / (summary["seconds"] / 3600)
            xbar = stratum_x / stratum_e[:, None]
            ybar = stratum_n / (rate * stratum_e[:, None])
            H = rate * (H - stratum_x.T @ xbar)
            T -= stratum_x.T @ (stratum_n / stratum_e[:, None])
            yy = (yy - np.sum(np.square(stratum_n.sum(axis=1)) / stratum_e)) / rate
            arrays = dict(H=H, T=T, yy=np.asarray(yy), xbar=xbar, ybar=ybar,
                          stratum_weight=rate * stratum_e, player_exposure=player_exposure,
                          response_counts=response_counts)
            require(all(np.isfinite(value).all() for value in arrays.values()), "nonfinite attribution statistics")
            require(int(player_exposure.sum()) == 5 * summary["seconds"], "player/directional exposure identity failed")
            require(int(response_counts.sum()) == summary["count"], "response count identity failed")
            require(summary["row_count"] % 2 == 0, "directional rows do not pair")
            array_path = output / f"{population}-{season}.npz"
            with array_path.open("xb") as destination:
                np.savez(destination, **arrays)
            annual_documents.append(dict(population=population, season=season, players=current_players,
                strata=strata, status="prepared", reason=None, r=rate, arrays=identity(array_path),
                rows=identity(row_path), coverage=dict(season_coverage[(population, season)]),
                shapes={name: list(value.shape) for name, value in arrays.items()},
                row_count=summary["row_count"], team_seconds=summary["seconds"], total_count=summary["count"]))
    centers, edges = grid()
    grid_identity = hashlib.sha256(centers.tobytes() + edges.tobytes()).hexdigest()
    source_design_sha256 = hashlib.sha256(json.dumps(dict(inputs=inputs, grid_sha256=grid_identity, design=DESIGN),
                                                        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    protocol_reference = identity(protocol_path)
    manifest = dict(schema_version=1, kind="attribution_prepared", purpose=selected["purpose"],
        implementation=current_implementation, protocol=protocol_reference, selection=identity(selection_path),
        population_ids={population: hashlib.sha256((protocol_reference["sha256"] + ":" + source_design_sha256 + ":" + population).encode()).hexdigest()
                        for population in POPULATIONS},
        inputs=inputs, seasons=seasons, target_season=seasons[-1], populations=list(POPULATIONS),
        grid=dict(sha256=grid_identity, cells=len(centers), width_feet=5, coordinate_frame="native attacking"),
        design=DESIGN, design_sha256=hashlib.sha256(json.dumps(DESIGN, sort_keys=True).encode()).hexdigest(),
        units=dict(time="seconds", rates="attempts per 60 team minutes", counts="recorded attempts",
                   segment_clock="elapsed seconds within period", coordinates="feet in native attacking frame",
                   score="goals before the event; segment context is clipped home-minus-away goals",
                   arrays=dict(H="expected attempts", T="recorded attempts", yy="expected-attempt-weighted squared relative rate",
                               xbar="player indicators", ybar="relative rate", stratum_weight="expected attempts",
                               player_exposure="seconds", response_counts="recorded attempts")),
        annual=annual_documents, games_by_season=dict(game_totals),
        pairs=dict(greatest_shared=list(greatest_shared) if greatest_shared else None,
                   greatest_disjoint=list(greatest_disjoint) if greatest_disjoint else None,
                   shared_seconds=shared[greatest_shared] if greatest_shared else None,
                   disjoint_combined_seconds=sum(exposure[player] for player in greatest_disjoint) if greatest_disjoint else None),
        ledgers={**{name: identity(path) for name, path in (("segments", segments_path), ("events", events_path),
                                                        ("coverage", coverage_path))},
                 "rows": [dict(population=population, season=season, reference=identity(path))
                          for (population, season), path in row_paths.items()]},
        row_contracts=dict(segments="one positive native/coalesced physical segment, source interval links, masks and sparse pre-mask counts",
                          events="one recognized recorded attempt keyed by game_id/source_index; assignment and population dispositions",
                          coverage="one inventory game with native horizons and population/team/player count and time losses",
                          rows="one admitted attacking direction keyed by game_id/period/start/end/attacking_team per population"),
        array_contract="H=Xr'WXr; T=Xr'WY; yy=matched scalar yr'Wyr; xbar/ybar=context means; stratum_weight=e*r",
        resources=resources(started))
    write_json(output / "prepared.json", manifest)
    return identity(output / "prepared.json")
