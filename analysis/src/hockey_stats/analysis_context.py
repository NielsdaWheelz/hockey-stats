"""product facts composed from the native chronology, feature and source owners."""

from collections import defaultdict
from copy import deepcopy
from pathlib import Path

from . import feature_data as features
from .analysis_support import assign_support_chunks, prepare_support
from .chance_data import prepare_game_attempts
from .corpus_inputs import require
from .feature_history import prepare_history
from .game_chronology import elapsed_scores
from .reconstruct import MEMBERSHIP_FIELDS as MEMBERS
from .reconstruct import (
    attacking_coordinates,
    defending_sides,
    lineup_classification,
    report_membership,
    roster_identities,
)
from .scoring_credits import scoring_credits
from .shot_origins import in_rink

AGE_CUTS = (0, 10, 20, 40, 60, 90)


def unit_workload(ids, prefixes, evidence):
    """complete actual-unit aggregates exclude individual partial lower bounds."""
    values = [
        prefixes.get(str(p), {}).get("values", {}).get("toi_all_seconds")
        for p in ids or []
    ]
    known = [v for v in values if v is not None]
    complete = ids is not None and len(known) == len(ids) and bool(ids)
    return features.fact(
        {
            "member_count": len(ids) if ids is not None else None,
            "known_count": len(known) if ids is not None else None,
            "known_toi_all_sum_seconds": sum(known) if ids is not None else None,
            "toi_all_mean_seconds": sum(known) / len(ids) if complete else None,
            "toi_all_max_seconds": max(known) if complete else None,
        },
        evidence,
        reason="all actual unit members need complete elapsed workload",
    )


def _unit_ages(ids, players, evidence):
    ages = [
        players.get(str(p), {}).get("values", {}).get("age_seconds") for p in ids or []
    ]
    known = [v for v in ages if v is not None]
    complete = ids is not None and bool(ids) and len(known) == len(ids)
    return features.fact(
        {
            "member_count": len(ids) if ids is not None else None,
            "known_count": len(known) if ids is not None else None,
            "known_age_sum_seconds": sum(known) if ids is not None else None,
            "age_min_seconds": min(known) if complete else None,
            "age_mean_seconds": sum(known) / len(ids) if complete else None,
            "age_max_seconds": max(known) if complete else None,
        },
        evidence,
        reason="all actual unit members need complete coalesced shift age",
    )


def immediate_outcomes(ordered, details, order_supported, link, *, terminals=()):
    """the immediately following recorded row alone supplies future labels."""
    result = {}
    for position, event in enumerate(ordered):
        index = event["source_index"]
        if index not in details:
            continue
        focal = details[index]["values"]
        following = ordered[position + 1] if position + 1 < len(ordered) else None
        evidence = [link("play-by-play", f"/plays/{index}")]
        if following:
            evidence.append(link("play-by-play", f"/plays/{following['source_index']}"))
        values = dict.fromkeys(
            (
                "recorded_goalie_stop",
                "reattempt_within_5s",
                "reattempt_source_index",
                "next_event_source_index",
                "next_event_delay_seconds",
            )
        )
        record = features.fact(
            values,
            evidence,
            reason="immediate successor order, timing or physical action unavailable",
        )
        result[index] = record
        if focal["physical_status"] == "unresolved" and event["type_key"] in (
            "shot-on-goal",
            "goal",
        ):
            continue
        if focal["outcome"] == "goal" and focal["physical_status"] == "ordinary":
            values["recorded_goalie_stop"] = False
            record["problems"].pop("recorded_goalie_stop", None)
        if (
            focal["physical_status"] == "outside_population"
            or focal["outcome"] != "save"
        ):
            fields = [
                field
                for field in values
                if field != "recorded_goalie_stop" or values[field] is None
            ]
            features._problem(
                record,
                fields,
                "immediate save outcomes apply to saved shots",
                "not_applicable",
            )
            continue
        if not order_supported or features._clock(event) is None:
            continue
        terminal = next(
            (
                t
                for t in terminals
                if t["period_number"] == event["period_number"]
                and event["elapsed_seconds"] <= t["end_seconds"]
            ),
            None,
        )
        if following is None or following["period_number"] != event["period_number"]:
            if following is not None:
                values["next_event_source_index"] = following["source_index"]
                record["problems"].pop("next_event_source_index", None)
            if terminal is not None:
                record["evidence"].extend(terminal["evidence"])
                values["recorded_goalie_stop"] = False
                values["reattempt_within_5s"] = False
                record["problems"].pop("recorded_goalie_stop", None)
                record["problems"].pop("reattempt_within_5s", None)
                absent = ["reattempt_source_index", "next_event_delay_seconds"]
                if following is None:
                    absent.append("next_event_source_index")
                features._problem(
                    record,
                    absent,
                    "validated terminal has no subsequent same-period record",
                    "not_applicable",
                )
            continue
        valid = following["kind_valid"] and features._clock(following) is not None
        same_period = following["period_number"] == event["period_number"]
        terminal = valid and following["type_key"] in ("period-end", "game-end")
        delay = (
            following["elapsed_seconds"] - event["elapsed_seconds"]
            if same_period and valid
            else None
        )
        if not valid or delay is not None and delay < 0:
            continue
        # crossing a period without a recorded terminal does not prove the chain.
        if not same_period and not terminal:
            continue
        values["next_event_source_index"] = following["source_index"]
        values["next_event_delay_seconds"] = delay
        for field in ("next_event_source_index", "next_event_delay_seconds"):
            if values[field] is not None:
                record["problems"].pop(field, None)
        stop_reason = following.get("reason")
        if following["type_key"] != "stoppage" or delay is not None and delay > 2:
            values["recorded_goalie_stop"] = False
        elif stop_reason is not None and delay is not None:
            values["recorded_goalie_stop"] = (
                stop_reason == "goalie-stopped-after-sog" and 0 <= delay <= 2
            )
        next_details = details.get(following["source_index"])
        if (
            following["type_key"] not in features.ATTEMPT_KINDS
            or terminal
            or delay is not None
            and delay > 5
        ):
            values["reattempt_within_5s"] = False
        elif next_details is not None:
            next_values = next_details["values"]
            if (
                next_values["shooting_team_id"] is not None
                and focal["shooting_team_id"] is not None
                and next_values["shooting_team_id"] != focal["shooting_team_id"]
            ) or next_values["physical_status"] == "outside_population":
                values["reattempt_within_5s"] = False
            elif (
                next_values["physical_status"] == "ordinary"
                and next_values["shooting_team_id"] is not None
                and focal["shooting_team_id"] is not None
                and delay is not None
            ):
                values["reattempt_within_5s"] = (
                    next_values["shooting_team_id"] == focal["shooting_team_id"]
                    and 0 <= delay <= 5
                )
        if values["reattempt_within_5s"]:
            values["reattempt_source_index"] = following["source_index"]
        elif values["reattempt_within_5s"] is False:
            features._problem(
                record,
                ("reattempt_source_index",),
                "no qualifying immediate reattempt",
                "not_applicable",
            )
        for field, value in values.items():
            if value is not None:
                record["problems"].pop(field, None)
    return result


def _checked_faceoffs(document, recon, reports):
    identities = roster_identities(document["roster_records"])
    result = set()
    for event in document["events"] or []:
        row = recon[event["source_index"]]
        report = reports.get(row["report_source_index"])
        if (
            event["kind_valid"]
            and event["type_key"] == "faceoff"
            and row["match_status"] == "matched"
            and report is not None
        ):
            membership, invalid = report_membership(
                report, document["game"], identities, []
            )
            away = set(
                (membership["away_skaters"] or []) + (membership["away_goalies"] or [])
            )
            home = set(
                (membership["home_skaters"] or []) + (membership["home_goalies"] or [])
            )
            winner = event["roles"].get("faceoff_winner")
            loser = event["roles"].get("faceoff_loser")
            opposed = (
                winner in away and loser in home or winner in home and loser in away
            )
            if (
                not invalid
                and lineup_classification(membership) != "unresolved"
                and opposed
            ):
                result.add(event["source_index"])
    return result


def _episodes(ordered, recon, reports, faceoffs, order_supported):
    episodes, event_episode, pre_event_episode, reset_links = [], {}, {}, {}
    active, previous, last_reset = None, None, None
    for event in ordered:
        index, clock = event["source_index"], features._clock(event)
        valid = order_supported and event["kind_valid"] and clock is not None
        pre_event_episode[index] = (
            active["episode_index"]
            if active is not None
            and valid
            and event["period_number"] == active["period_number"]
            else None
        )
        terminal = event["type_key"] in ("period-end", "game-end")
        row = recon.get(index)
        faceoff = valid and index in faceoffs
        live = valid and event["type_key"] in set(features.ACTION_KINDS) - {"faceoff"}
        if live and event["type_key"] in features.ATTEMPT_KINDS:
            live = row is not None and features._normal_attempt(
                event, row, reports.get(row["report_source_index"])
            )
        closing_episode = (
            active["episode_index"]
            if active is not None
            and valid
            and event["period_number"] == active["period_number"]
            and event["type_key"] in features.RESETS
            else None
        )
        if active is not None and (
            not valid
            or faceoff
            or event["type_key"] in features.RESETS
            or event["period_number"] != active["period_number"]
        ):
            active["end_seconds"] = (
                event["elapsed_seconds"]
                if valid and event["period_number"] == active["period_number"]
                else previous["elapsed_seconds"]
                if previous
                else None
            )
            active["end_source_index"] = (
                index
                if valid and event["period_number"] == active["period_number"]
                else previous["source_index"]
                if previous
                else None
            )
            active["end_reason"] = (
                "faceoff"
                if faceoff
                else "terminal"
                if valid and terminal
                else "reset"
                if valid and event["type_key"] in features.RESETS
                else "unknown"
            )
            active = None
        if active is None and (faceoff or live):
            active = {
                "episode_index": len(episodes),
                "period_number": event["period_number"],
                "start_seconds": event["elapsed_seconds"],
                "end_seconds": None,
                "start_source_index": index,
                "end_source_index": None,
                "start_kind": "faceoff" if faceoff else "first_live_action",
                "left_censored": not faceoff,
                "end_reason": "unknown",
                "issue_indices": [],
            }
            episodes.append(active)
        event_episode[index] = (
            closing_episode
            if closing_episode is not None
            else active["episode_index"]
            if active
            else None
        )
        reset_links[index] = last_reset
        if valid and event["type_key"] in features.RESETS:
            last_reset = index
        elif (
            not valid
            or previous
            and previous["period_number"] != event["period_number"]
        ):
            last_reset = None
        previous = event
    return episodes, event_episode, pre_event_episode, reset_links


def _player_shifts(
    document,
    reconstruction,
    ordered,
    recon,
    episodes,
    faceoffs,
    order_supported,
    link,
    issues,
):
    """individual continuity survives teammate changes and recorded stoppages."""
    game = document["game"]
    native = {s["source_index"]: s for s in document["shift_records"] or []}
    coverage = features.participation_coverage(document)
    supported_rows, overlap_conflicts = features.individual_participation(
        document["shift_records"]
    )
    for rows in overlap_conflicts:
        issues.append(
            {
                "code": "overlapping_individual_participation",
                "source": "prepared-analysis",
                "path": "/player_shifts",
                "message": f"distinct strictly overlapping shift bounds for player {rows[0]['player_id']} in period {rows[0]['period_number']}; component omitted from known participation",
                "evidence": [
                    link("shifts", f"/data/{row['source_index']}") for row in rows
                ],
            }
        )
    # individual native shifts remain evidence when an unrelated lineup member
    # makes full membership unresolved. union participation, not row counters.
    by_person = defaultdict(list)
    for shift in supported_rows:
        if shift["team_id"] in (game["away_team_id"], game["home_team_id"]):
            by_person[
                shift["player_id"], shift["team_id"], shift["period_number"]
            ].append(shift)
    runs = defaultdict(list)
    for key, source_rows in by_person.items():
        for shift in sorted(
            source_rows,
            key=lambda s: (s["start_seconds"], s["end_seconds"], s["source_index"]),
        ):
            intervals = [
                i
                for i, interval in enumerate(reconstruction["intervals"] or [])
                if shift["source_index"] in interval["shift_source_indices"]
            ]
            rows = runs[key]
            if rows and shift["start_seconds"] <= rows[-1]["end_seconds"]:
                current = rows[-1]
                current["end_seconds"] = max(
                    current["end_seconds"], shift["end_seconds"]
                )
                current["native_shift_indices"].append(shift["source_index"])
                current["native_interval_indices"] = sorted(
                    set(current["native_interval_indices"] + intervals)
                )
            else:
                rows.append(
                    {
                        "player_id": key[0],
                        "team_id": key[1],
                        "period_number": key[2],
                        "start_seconds": shift["start_seconds"],
                        "end_seconds": shift["end_seconds"],
                        "native_shift_indices": [shift["source_index"]],
                        "native_interval_indices": intervals,
                    }
                )
    result = []
    sides = defending_sides(ordered)
    for key, rows in sorted(runs.items()):
        previous = None
        for row in rows:
            evidence = [
                link("reconstruction", f"/intervals/{i}")
                for i in row["native_interval_indices"]
            ]
            evidence.extend(
                link("shifts", f"/data/{i}") for i in row["native_shift_indices"]
            )
            uncertain = [
                s
                for s in native.values()
                if (
                    s["type_code"] == 517
                    and s["interval_status"] != "coherent"
                    or s["type_code"] not in (517, 505)
                )
                and s["player_id"] in (row["player_id"], None)
                and s["period_number"] in (row["period_number"], None)
            ]
            left_censored = (
                not coverage.get(row["player_id"], False)
                or row["start_seconds"] > 0
                and any(
                    (s["start_seconds"] or 0) <= row["start_seconds"]
                    and (
                        s["end_seconds"] is None
                        or row["start_seconds"] <= s["end_seconds"]
                    )
                    for s in uncertain
                )
            )
            uncertain_rest = not coverage.get(row["player_id"], False) or any(
                (s["start_seconds"] or 0) <= row["start_seconds"]
                and (
                    previous is None
                    or s["end_seconds"] is None
                    or previous["end_seconds"] <= s["end_seconds"]
                )
                for s in uncertain
            )
            evidence.extend(
                link("shifts", f"/data/{s['source_index']}") for s in uncertain
            )
            start = {
                "kind": "unknown",
                "zone": None,
                "event_source_index": None,
                "episode_index": None,
                "rest_seconds": row["start_seconds"] - previous["end_seconds"]
                if previous
                else None,
            }
            matching = [
                e
                for e in ordered
                if e["source_index"] in faceoffs
                and e["period_number"] == row["period_number"]
                and e["elapsed_seconds"] == row["start_seconds"]
                and row["player_id"]
                in [p for k in MEMBERS for p in recon[e["source_index"]][k] or []]
            ]
            tied_unknown = any(
                e["period_number"] == row["period_number"]
                and e["elapsed_seconds"] == row["start_seconds"]
                and (
                    not e["kind_valid"]
                    or e["type_key"] == "faceoff"
                    and e["source_index"] not in faceoffs
                )
                for e in ordered
            )
            if (
                len(matching) == 1
                and order_supported
                and not tied_unknown
                and not left_censored
            ):
                event = matching[0]
                start.update(kind="faceoff", event_source_index=event["source_index"])
                x, y, reason = attacking_coordinates(event, game, row["team_id"], sides)
                if reason is None and in_rink(x, y):
                    start["zone"] = features._zone(x)
                start["episode_index"] = next(
                    (
                        e["episode_index"]
                        for e in episodes
                        if e["start_source_index"] == event["source_index"]
                    ),
                    None,
                )
                evidence.append(link("play-by-play", f"/plays/{event['source_index']}"))
            elif order_supported and not tied_unknown and not left_censored:
                live = [
                    e
                    for e in episodes
                    if e["period_number"] == row["period_number"]
                    and e["end_seconds"] is not None
                    and e["start_seconds"] < row["start_seconds"] < e["end_seconds"]
                ]
                if len(live) == 1:
                    start.update(
                        kind="on_the_fly", episode_index=live[0]["episode_index"]
                    )
            fact = features.fact(
                start,
                evidence,
                reason="coalesced start lacks supported live or faceoff evidence",
            )
            if start["kind"] == "on_the_fly":
                features._problem(
                    fact,
                    ("zone", "event_source_index"),
                    "on-the-fly start has no faceoff anchor",
                    "not_applicable",
                )
            if uncertain_rest:
                features._problem(
                    fact,
                    ("rest_seconds",),
                    "unknown individual participation prevents exact prior rest",
                )
            elif previous is None:
                features._problem(
                    fact,
                    ("rest_seconds",),
                    "no earlier supported participation span this period",
                    "not_applicable",
                )
            issue_indices = []
            if left_censored:
                issue_indices.append(len(issues))
                issues.append(
                    {
                        "code": "participation_start_left_censored",
                        "source": "prepared-analysis",
                        "path": f"/player_shifts/{len(result)}",
                        "message": "unknown individual shift evidence may precede this supported participation span",
                        "evidence": evidence,
                    }
                )
            result.append(
                {
                    "player_shift_index": len(result),
                    **row,
                    "start": fact,
                    "issue_indices": issue_indices,
                }
            )
            previous = row
    return result


def _transition_records(ordered, reconstruction, game, supported, link):
    raw = features._strength_transitions(
        ordered, reconstruction, game, supported, product=True
    )
    result = {}
    for event in ordered:
        row = raw[event["source_index"]]
        focal = "away" if event["shooting_team_id"] == game["away_team_id"] else "home"
        side = (
            focal
            if row["side"] == "same"
            else ("home" if focal == "away" else "away")
            if row["side"] == "opponent"
            else None
        )
        returned = (
            event["elapsed_seconds"] - row["age"] if row["age"] is not None else None
        )
        if row["exists"] is None:
            side, returned = None, None
            row = {**row, "age": None}
        fact = features.fact(
            {
                "exists": row["exists"],
                "prior_shorthanded_side": side,
                "return_seconds": returned,
                "age_seconds": row["age"],
            },
            [link("reconstruction", "/intervals"), link("play-by-play", "/plays")],
        )
        if row["exists"] is False:
            features._problem(
                fact,
                ("prior_shorthanded_side", "return_seconds", "age_seconds"),
                "no supported unequal-strength return before reset",
                "not_applicable",
            )
        result[event["source_index"]] = fact
    return result


def _age_supported(shift, issues):
    return shift is not None and not any(
        issues[i]["code"] == "participation_start_left_censored"
        for i in shift["issue_indices"]
    )


def _attempt_details(attempt, event, row, reports, link):
    report = reports.get(row["report_source_index"])
    modifier = row["goal_modifier_evidence"]
    penalty = (
        report is not None
        and report["penalty_shot"] is True
        or modifier is not None
        and modifier["status"] == "reported"
        and modifier["reported_value"] == "penalty-shot"
    )
    physical = (
        event["kind_valid"]
        and features._clock(event) is not None
        and (
            event["type_key"] != "goal"
            or modifier is not None
            and modifier["status"] == "reported"
            and modifier["reported_value"] in ("none", "penalty-shot")
        )
    )
    nonphysical = event["type_key"] == "goal" and (
        modifier is not None
        and modifier["status"] == "reported"
        and modifier["reported_value"] in ("own-goal", "awarded")
    )
    status = (
        "outside_population"
        if event["timed_period"] is False or penalty or nonphysical
        else "ordinary"
        if physical
        else "unresolved"
    )
    location = "unavailable"
    if attempt["reported_x"] is not None and attempt["reported_y"] is not None:
        location = (
            "block_contact"
            if event["type_key"] == "blocked-shot"
            else "reported_attempt"
        )
    return features.fact(
        {
            "outcome": {
                "goal": "goal",
                "shot-on-goal": "save",
                "missed-shot": "miss",
                "blocked-shot": "block",
            }[event["type_key"]]
            if physical
            else None,
            "physical_status": status,
            "credited_shooter_id": attempt["credited_scorer_id"]
            if event["type_key"] == "goal"
            else event["roles"].get("shooter"),
            "physical_shooter_id": attempt["shooter_id"],
            "shooting_team_id": event["shooting_team_id"],
            "opposing_goalie_id": attempt["goalie_id"],
            "location_kind": location,
        },
        [
            link("play-by-play", f"/plays/{event['source_index']}"),
            link("reconstruction", f"/events/{event['source_index']}"),
        ],
    )


def _base(envelope, inventory_entry, references, input_ref):
    core = prepare_game_attempts(envelope, Path(input_ref["path"]), inventory_entry)
    local = features.prepare_game(
        envelope,
        core["attempts"],
        input_ref=input_ref,
        bio_rows=_bio_rows(references),
        chronology=core["chronology"],
    )
    return core, local


def _bio_rows(references):
    """direct game calls bind bios to their source body when no corpus ref exists."""
    inputs = {row["source"]: row for row in references.get("inputs", [])}
    result = []
    for observation in references.get("bio_observations", []):
        if "input_ref" in observation:
            result.append(observation)
            continue
        source = inputs.get(observation["source"])
        require(
            source is not None and source["body_sha256"] is not None,
            "references/bio_observations",
            "bio observation has no immutable source identity",
        )
        result.append(
            {
                **observation,
                "input_ref": {
                    "path": str(Path(source["capture_path"]).parent / "body.bin"),
                    "sha256": source["body_sha256"],
                },
            }
        )
    return result


def game_summary(envelope, inventory_entry, references, input_ref):
    core = prepare_game_attempts(envelope, Path(input_ref["path"]), inventory_entry)
    document, reconstruction = envelope["interpreted"], envelope["reconstruction"]
    link = features._links(input_ref)
    _, identities = features._people(document, _bio_rows(references), input_ref, link)
    recon = {r["source_index"]: r for r in reconstruction["events"] or []}
    reports = {r["source_index"]: r for r in document["report_rows"] or []}
    normal = {
        event["source_index"]
        for event in document["events"] or []
        if features._normal_attempt(
            event,
            recon[event["source_index"]],
            reports.get(recon[event["source_index"]]["report_source_index"]),
        )
    }
    return features._history_summary(
        document,
        reconstruction,
        identities,
        core["attempts"],
        normal,
        input_ref,
        link,
    )


def prepare_game(envelope, inventory_entry, references, input_ref):
    document, reconstruction = envelope["interpreted"], envelope["reconstruction"]
    core, local = _base(envelope, inventory_entry, references, input_ref)
    game = document["game"]
    link = features._links(input_ref)
    chronology = core["chronology"]
    ordered = chronology["ordered"] or list(document["events"] or [])
    supported = (
        chronology["order_supported"]
        and chronology["ordered"] is not None
        and document["events"] is not None
    )
    recon = {r["source_index"]: r for r in reconstruction["events"] or []}
    reports = {r["source_index"]: r for r in document["report_rows"] or []}
    shifts = {r["source_index"]: r for r in document["shift_records"] or []}
    _, identities = features._people(document, _bio_rows(references), input_ref, link)
    support = prepare_support(document, reconstruction, input_ref)
    faceoffs = _checked_faceoffs(document, recon, reports)
    episodes, event_episode, pre_event_episode, reset_links = _episodes(
        ordered, recon, reports, faceoffs, supported
    )
    player_shifts = _player_shifts(
        document,
        reconstruction,
        ordered,
        recon,
        episodes,
        faceoffs,
        supported,
        link,
        support["issues"],
    )
    participation_complete = features.participation_coverage(document)
    normal = {
        e["source_index"]
        for e in ordered
        if features._normal_attempt(
            e,
            recon[e["source_index"]],
            reports.get(recon[e["source_index"]]["report_source_index"]),
        )
    }
    prefixes = features._prefix_workload(
        ordered,
        reconstruction,
        identities,
        shifts,
        normal,
        supported,
        link,
        product=True,
        game=game,
        participation=player_shifts,
        participation_complete=participation_complete,
    )
    transitions = _transition_records(ordered, reconstruction, game, supported, link)
    details = {
        a["source_index"]: _attempt_details(
            a, a["source_event"], recon[a["source_index"]], reports, link
        )
        for a in core["attempts"]
    }
    terminals = []
    for period in reconstruction["periods"] or []:
        if period["status"] != "supported":
            continue
        for report in reports.values():
            if (
                report["event_code"] in ("PEND", "GEND")
                and report["period_number"] == period["period_number"]
                and report["elapsed_seconds"] == period["end_seconds"]
            ):
                terminals.append(
                    {
                        "period_number": period["period_number"],
                        "end_seconds": period["end_seconds"],
                        "evidence": [
                            link("play-report", f"/rows/{report['source_index']}"),
                            link("reconstruction", "/periods"),
                        ],
                    }
                )
    outcomes = immediate_outcomes(
        ordered, details, supported, link, terminals=terminals
    )
    sides = defending_sides(ordered)
    event_records = []
    for position, event in enumerate(ordered):
        index = event["source_index"]
        x, y, reason = attacking_coordinates(event, game, game["home_team_id"], sides)
        located = reason is None and in_rink(x, y)
        geometry = features.fact(
            {
                "x_ft": x if located else None,
                "y_ft": y if located else None,
                "frame": "home_attack" if located else None,
                "location_kind": "block_contact"
                if located and event["type_key"] == "blocked-shot"
                else "reported_event"
                if located
                else "unavailable",
            },
            [link("play-by-play", f"/plays/{index}")],
            reason=reason or "recorded coordinates outside rink",
        )
        score = chronology["scores"].get(index, {"away": None, "home": None})
        event_records.append(
            {
                "source": event,
                "pre_score": features.fact(
                    score,
                    [link("interpreted", "/checks")],
                    reason="whole-game score corroboration unavailable",
                ),
                "geometry": geometry,
                "chronology": features.fact(
                    {
                        "order_index": position if supported else None,
                        "predecessor_source_index": ordered[position - 1][
                            "source_index"
                        ]
                        if supported and position
                        else None,
                        "successor_source_index": ordered[position + 1]["source_index"]
                        if supported and position + 1 < len(ordered)
                        else None,
                        "episode_index": event_episode[index],
                        "reset_source_index": reset_links[index],
                    },
                    [link("play-by-play", f"/plays/{index}")],
                ),
                "context": {
                    "prefix_by_player": prefixes.get(index, {}),
                    "live_episode_index": pre_event_episode[index],
                    "strength_transition": transitions[index],
                },
            }
        )
    chunks = []
    for segment in support["segments"] or []:
        period, start, end = (
            segment["period_number"],
            segment["start_seconds"],
            segment["end_seconds"],
        )
        members = [p for k in MEMBERS for p in segment["membership"][k]]
        cuts = {start, end}
        if period <= 3 and start < 600 < end:
            cuts.add(600)
        cuts.update(
            e["elapsed_seconds"]
            for e in ordered
            if e["period_number"] == period
            and e["kind_valid"]
            and e["elapsed_seconds"] is not None
            and start < e["elapsed_seconds"] < end
            and e["type_key"] in features.RESETS
        )
        for shift in player_shifts:
            if (
                shift["player_id"] in members
                and shift["period_number"] == period
                and shift["start_seconds"] <= start < shift["end_seconds"]
                and _age_supported(shift, support["issues"])
            ):
                cuts.update(
                    shift["start_seconds"] + age
                    for age in AGE_CUTS
                    if start < shift["start_seconds"] + age < end
                )
        for left, right in zip(sorted(cuts), sorted(cuts)[1:]):
            chunks.append(
                {
                    "chunk_index": len(chunks),
                    "segment_index": segment["segment_index"],
                    "start_seconds": left,
                    "end_seconds": right,
                    "score": None,
                    "strength_transition": None,
                    "member_contexts": [],
                    "away_unit": None,
                    "home_unit": None,
                    "issue_indices": [],
                }
            )
    # marker prefixes precede every same-clock record; transition markers follow resets.
    markers, marker_recon = [], []
    next_index = max(recon, default=-1) + 1
    template = ordered[0] if ordered else {}
    for chunk in chunks:
        segment = support["segments"][chunk["segment_index"]]
        marker = {
            **template,
            "source_index": next_index + chunk["chunk_index"],
            "type_key": "context-boundary",
            "kind_valid": True,
            "period_number": segment["period_number"],
            "period_type": "REG" if segment["period_number"] <= 3 else "OT",
            "timed_period": True,
            "elapsed_seconds": chunk["start_seconds"],
            "shooting_team_id": None,
            "roles": {},
        }
        markers.append(marker)
        marker_recon.append(
            {
                "source_index": marker["source_index"],
                "shift_relation": "after",
                "interval_indices": [
                    i
                    for i in segment["native_interval_indices"]
                    if reconstruction["intervals"][i]["start_seconds"]
                    <= chunk["start_seconds"]
                    < reconstruction["intervals"][i]["end_seconds"]
                ],
                "goal_modifier_evidence": None,
                **segment["membership"],
            }
        )
    augmented = {
        **reconstruction,
        "events": [*(reconstruction["events"] or []), *marker_recon],
    }
    # an unclocked source row stays after its verified predecessor and taints
    # later prefixes; moving it to the end would silently restore completeness.
    sort_clocks = {}
    prior_clock = 0
    for event in ordered:
        clock = features._clock(event)
        if clock is not None:
            prior_clock = clock
        elif event["timed_period"] is False:
            prior_clock = float("inf")
        sort_clocks[event["source_index"]] = prior_clock
    for marker in markers:
        sort_clocks[marker["source_index"]] = features._clock(marker)
    sequence = sorted(
        [*ordered, *markers],
        key=lambda e: (
            sort_clocks[e["source_index"]],
            0 if e["type_key"] == "context-boundary" else 1,
            e.get("sort_order") or 0,
        ),
    )
    elapsed_prefixes = features._prefix_workload(
        sequence,
        augmented,
        identities,
        shifts,
        normal,
        supported,
        link,
        product=True,
        game=game,
        participation=player_shifts,
        participation_complete=participation_complete,
    )
    transition_sequence = sorted(
        [*ordered, *markers],
        key=lambda e: (
            sort_clocks[e["source_index"]],
            1 if e["type_key"] == "context-boundary" else 0,
            e.get("sort_order") or 0,
        ),
    )
    elapsed_transitions = _transition_records(
        transition_sequence, augmented, game, supported, link
    )

    scores = elapsed_scores(ordered, chronology["scores"], game)
    for chunk, marker in zip(chunks, markers):
        segment = support["segments"][chunk["segment_index"]]
        period, left = segment["period_number"], chunk["start_seconds"]
        evidence = [link("reconstruction", "/intervals")]
        before = [
            s
            for s in scores
            if (s["period_number"], s["elapsed_seconds"]) <= (period, left)
        ]
        score = (
            before[-1]["score"]
            if before
            else {"away": 0, "home": 0}
            if core["evidence"]["score_support"] == "supported"
            else {"away": None, "home": None}
        )
        chunk["score"] = features.fact(
            score, evidence, reason="whole-game score corroboration unavailable"
        )
        chunk["strength_transition"] = elapsed_transitions[marker["source_index"]]
        prefix = elapsed_prefixes[marker["source_index"]]
        for player in [p for k in MEMBERS for p in segment["membership"][k]]:
            active = [
                s
                for s in player_shifts
                if s["player_id"] == player
                and s["period_number"] == period
                and s["start_seconds"] <= left < s["end_seconds"]
            ]
            shift = active[0] if len(active) == 1 else None
            chunk["member_contexts"].append(
                {
                    "player_id": player,
                    "player_shift_index": shift["player_shift_index"]
                    if shift
                    else None,
                    "shift_age_seconds": features.fact(
                        {
                            "value": left - shift["start_seconds"]
                            if _age_supported(shift, support["issues"])
                            else None
                        },
                        evidence,
                    ),
                    "elapsed_prefix": prefix[str(player)]
                    if str(player) in prefix
                    else (
                        features.fact(
                            dict.fromkeys(
                                (
                                    "toi_all_seconds",
                                    "toi_5v5_seconds",
                                    "attempts",
                                    "goals",
                                    "shifts_begun",
                                    "shifts_completed",
                                    "known_toi_all_seconds",
                                    "known_toi_5v5_seconds",
                                    "known_attempts",
                                    "known_goals",
                                    "known_shifts_begun",
                                    "known_shifts_completed",
                                    "on_net_faced",
                                    "known_on_net_faced",
                                )
                            ),
                            [
                                link("interpreted", "/roster_records"),
                                link("interpreted", "/boxscore_players"),
                            ],
                            reason="segment member has no attributed dated game identity",
                        )
                    ),
                }
            )
        for side in ("away", "home"):
            chunk[side + "_unit"] = unit_workload(
                segment["membership"][side + "_skaters"], prefix, evidence
            )
    assign_support_chunks(support, chunks, document["events"] or [])
    attempts = []
    for attempt in core["attempts"]:
        index = attempt["source_index"]
        row = recon[index]
        facts = deepcopy(attempt["feature_facts"])
        side = (
            attempt["home_away"] if attempt["home_away"] in ("away", "home") else None
        )
        opposing = "home" if side == "away" else "away" if side == "home" else None
        facts["current_workload"] = features.fact(
            {
                "players": prefixes[index],
                "opposing_unit": unit_workload(
                    row[opposing + "_skaters"] if opposing else None,
                    prefixes[index],
                    [link("reconstruction", "/intervals")],
                ),
            }
        )
        deployment = facts["deployment"]
        deployment["values"].pop("attacking_five", None)
        deployment["values"].pop("opposing_five", None)
        player_facts = deployment["values"]["players"]
        event = attempt["source_event"]
        for player, fact in player_facts.items():
            active = (
                [
                    s
                    for s in player_shifts
                    if s["player_id"] == int(player)
                    and s["period_number"] == event["period_number"]
                    and s["start_seconds"]
                    <= event["elapsed_seconds"]
                    <= s["end_seconds"]
                    and set(s["native_interval_indices"]) & set(row["interval_indices"])
                ]
                if event["elapsed_seconds"] is not None
                else []
            )
            if len(active) == 1:
                s = active[0]
                fact["values"].update(
                    start_seconds=s["start_seconds"],
                    end_seconds=s["end_seconds"],
                    age_seconds=event["elapsed_seconds"] - s["start_seconds"],
                    start_type=s["start"]["values"]["kind"],
                    start_zone=s["start"]["values"]["zone"],
                    previous_shift_gap_seconds=s["start"]["values"]["rest_seconds"],
                )
                for field, value in fact["values"].items():
                    if value is not None:
                        fact["problems"].pop(field, None)
                if not _age_supported(s, support["issues"]):
                    features._problem(
                        fact,
                        ("age_seconds",),
                        "individual participation start is left-censored",
                    )
                offset = len(fact["evidence"])
                fact["evidence"].extend(s["start"]["evidence"])
                for original, target in (
                    ("kind", "start_type"),
                    ("zone", "start_zone"),
                    ("rest_seconds", "previous_shift_gap_seconds"),
                ):
                    problem = s["start"]["problems"].get(original)
                    if problem:
                        fact["problems"][target] = {
                            **problem,
                            "evidence_refs": [
                                offset + i for i in problem["evidence_refs"]
                            ],
                        }
                if len(s["native_shift_indices"]) != 1:
                    features._problem(
                        fact,
                        ("shift_source_index",),
                        "coalesced participation has no unique native shift row",
                    )
        deployment["values"]["attacking_unit"] = _unit_ages(
            row[side + "_skaters"] if side else None,
            player_facts,
            deployment["evidence"],
        )
        deployment["values"]["opposing_unit"] = _unit_ages(
            row[opposing + "_skaters"] if opposing else None,
            player_facts,
            deployment["evidence"],
        )
        attempts.append(
            {
                "source_index": index,
                "details": details[index],
                "feature_facts": facts,
                "immediate_outcomes": outcomes[index],
            }
        )
    people = local["player_game_facts"]
    # the one-game API has no admitted history inventory. retain the named
    # left-censored contracts until the preparation owner joins its selection.
    history = prepare_history(
        [
            {
                **inventory_entry,
                "input_ref": input_ref,
                "selection_input_ref": input_ref,
                "history_admitted": False,
            }
        ],
        {game["game_id"]: local["history_summary"]},
        [game["game_id"]],
        missing_source_path="/game",
        missing_source="interpreted",
    )
    for player, person in people.items():
        person.update(history["players"][game["game_id"]].get(player, {}))
        person["roster"] = [
            r for r in document["roster_records"] or [] if r["player_id"] == int(player)
        ]
        person["boxscore"] = [
            r
            for r in document["boxscore_players"] or []
            if r["player_id"] == int(player)
        ]
        person["sweaters"] = [
            {
                "team_id": r["team_id"],
                "game_id": game["game_id"],
                "number": r["sweater_number"],
            }
            for r in person["roster"]
            if r["sweater_number"] is not None
        ]
    for shift in player_shifts:
        if shift["start"]["values"]["kind"] == "unknown":
            shift["issue_indices"].append(len(support["issues"]))
            support["issues"].append(
                {
                    "code": "shift_start_unavailable",
                    "source": "prepared-analysis",
                    "path": f"/player_shifts/{shift['player_shift_index']}/start",
                    "message": "coalesced participation start lacks a supported live or faceoff anchor",
                    "evidence": shift["start"]["evidence"],
                }
            )
    for episode in episodes:
        if episode["end_reason"] == "unknown":
            episode["issue_indices"].append(len(support["issues"]))
            support["issues"].append(
                {
                    "code": "episode_end_unavailable",
                    "source": "prepared-analysis",
                    "path": f"/episodes/{episode['episode_index']}",
                    "message": "recorded live continuity has no supported closing reset or terminal",
                    "evidence": [
                        link("play-by-play", f"/plays/{episode['start_source_index']}")
                    ],
                }
            )
    if document["roster_records"] is None and document["boxscore_players"] is None:
        people = None
        support["issues"].append(
            {
                "code": "identity_unavailable",
                "source": "prepared-analysis",
                "path": "/people",
                "message": "both dated roster and boxscore identity collections are unavailable",
                "evidence": [
                    link("interpreted", "/roster_records"),
                    link("interpreted", "/boxscore_players"),
                ],
            }
        )
    selected = [
        e
        for e in ordered
        if e["kind_valid"] and e["type_key"] in ("goal", "shot-on-goal")
    ]
    credits = (
        scoring_credits(document, selected, identities, [], factual=True)
        if document["events"] is not None
        else None
    )
    return {
        "schema_version": 1,
        "season": game["season"],
        "game_id": game["game_id"],
        "game": {
            "inventory": inventory_entry,
            "ledger": {"status": "reconstructed", "reason": None},
            "identity": game,
            "inputs": document["inputs"],
            "reported_results": document["reported_results"],
            "checks": document["checks"],
            "periods": reconstruction["periods"],
            "native_intervals": reconstruction["intervals"],
            "report_rows": document["report_rows"],
            "recording_observations": document.get("recording_observations", []),
            "source_issues": document["issues"],
            "native_issues": reconstruction["issues"],
        },
        "events": event_records if document["events"] is not None else None,
        "associations": support["associations"],
        "segments": support["segments"],
        "chunks": chunks if reconstruction["intervals"] is not None else None,
        "player_shifts": player_shifts
        if document["shift_records"] is not None
        else None,
        "episodes": episodes if document["events"] is not None else None,
        "people": people,
        "attempts": attempts if document["events"] is not None else None,
        "credits": credits,
        "ordinary_attempt_support": support["ordinary_attempt_support"],
        "issues": support["issues"],
    }
