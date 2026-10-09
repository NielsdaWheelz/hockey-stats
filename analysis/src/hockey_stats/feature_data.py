"""derive located local facts from one interpreted/reconstructed game."""

from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict, deque
from datetime import date
import math

from .reconstruct import attacking_coordinates, defending_sides
from .shot_origins import in_rink

ATTEMPT_KINDS = {"blocked-shot", "missed-shot", "shot-on-goal", "goal"}
RESETS = {
    "goal", "stoppage", "penalty", "period-start", "period-end", "game-end",
    "shootout-complete",
}
ACTION_KINDS = (
    "faceoff", "hit", "giveaway", "takeaway", "shot-on-goal", "missed-shot",
    "blocked-shot",
)
_ATTEMPTS = ATTEMPT_KINDS
_RESETS = RESETS
COUNTERS = (
    "ice_appearances", "starts", "relief_appearances", "toi_all_seconds",
    "toi_5v5_seconds", "shifts", "attempts", "goals", "sog", "saves",
    "shots_against", "goals_against",
)


def fact(values, evidence=(), *, reason="supporting evidence unavailable"):
    """one envelope contract for local, player, unit and window facts."""
    refs = list(range(len(evidence)))
    return {
        "values": values,
        "problems": {
            field: {"status": "unavailable", "reason": reason,
                    "evidence_refs": refs}
            for field, value in values.items() if value is None
        },
        "evidence": list(evidence),
    }


def _problem(record, fields, reason, status="unavailable"):
    refs = list(range(len(record["evidence"])))
    for field in fields:
        record["values"][field] = None
        record["problems"][field] = {
            "status": status, "reason": reason,
            "evidence_refs": refs,
        }


def _links(input_ref):
    """one locator per cited source record, shared by this game's facts."""
    locators = {}

    def link(source, path):
        key = source, path
        if key not in locators:
            locators[key] = {"input_ref": input_ref, "source": source, "path": path}
        return locators[key]

    return link


def _clock(event):
    if (event["timed_period"] is True
            and event["period_number"] in (1, 2, 3, 4)
            and event["elapsed_seconds"] is not None):
        return (event["period_number"] - 1) * 1200 + event["elapsed_seconds"]
    return None


def _zone(x):
    return "defensive" if x < -25 else "offensive" if x > 25 else "neutral"


def candidate_geometry(origin_xy, previous_event, hand):
    """the focal shooting-team frame; block contacts are never origins."""
    x, y = origin_xy
    supported = all(type(v) in (int, float) and math.isfinite(v) for v in (x, y))
    if not supported:
        return fact(dict.fromkeys((
            "x", "y", "distance_ft", "signed_angle_rad", "absolute_angle_rad",
            "region", "side", "off_wing", "dx_ft", "dy_ft", "displacement_ft",
            "crossed_centerline",
        )), reason="finite candidate origin unavailable")
    distance = math.hypot(89 - x, y)
    angle = math.atan2(y, 89 - x) if distance else None
    px, py = previous_event.get("current_attack_x"), previous_event.get("current_attack_y")
    prior = all(type(v) in (int, float) and math.isfinite(v) for v in (px, py))
    dx, dy = (x - px, y - py) if prior else (None, None)
    result = fact({
        "x": x, "y": y, "distance_ft": distance, "signed_angle_rad": angle,
        "absolute_angle_rad": abs(angle) if angle is not None else None,
        "region": "outside_zone" if x <= 25 else "beyond_goal" if x > 89 else "attacking_zone",
        "side": "positive_y" if y > 0 else "negative_y" if y < 0 else "centerline",
        "off_wing": (hand == "R" and y > 0 or hand == "L" and y < 0)
        if hand in ("R", "L") else None,
        "dx_ft": dx, "dy_ft": dy,
        "displacement_ft": math.hypot(dx, dy) if prior else None,
        "crossed_centerline": (py * y < 0) if prior else None,
    })
    if not distance:
        _problem(result, ("signed_angle_rad", "absolute_angle_rad"),
                 "angle is undefined at the goal", "not_applicable")
    return result


def _normal_attempt(event, reconstructed, report):
    if (not event["kind_valid"] or event["type_key"] not in _ATTEMPTS
            or event["timed_period"] is not True or _clock(event) is None
            or report is not None and report["penalty_shot"] is True):
        return False
    if event["type_key"] == "goal":
        modifier = reconstructed["goal_modifier_evidence"]
        return (modifier is not None and modifier["status"] == "reported"
                and modifier["reported_value"] == "none")
    return True


def _people(document, bio_rows, input_ref, link):
    rosters, boxes = defaultdict(list), defaultdict(list)
    for row in document["roster_records"] or []:
        rosters[row["player_id"]].append(row)
    for row in document["boxscore_players"] or []:
        boxes[row["player_id"]].append(row)
    bios = defaultdict(list)
    for row in bio_rows:
        bios[row["player_id"]].append(row)
    game = document["game"]
    players, identities = {}, {}
    for player_id in sorted((rosters.keys() | boxes.keys()) - {None}):
        roster, box = rosters[player_id], boxes[player_id]
        rows = roster + box
        teams = {row["team_id"] for row in rows if row["team_id"] is not None}
        team = None
        if len(teams) == 1 and teams <= {game["away_team_id"], game["home_team_id"]}:
            team = next(iter(teams))
        r = roster[0] if len(roster) == 1 else {}
        unique_box = box[0] if len(box) == 1 else {}
        b = unique_box if team is not None else {}
        evidence = [link("play-by-play", f"/rosterSpots/{row['source_index']}") for row in roster]
        evidence.extend(link("boxscore", row["source_path"]) for row in box)
        source_evidence = list(evidence)
        box_problem = None
        if len(box) > 1 or box and team is None:
            box_problem = {
                "status": "conflict" if len(box) > 1 or len(teams) > 1 else "unavailable",
                "reason": "boxscore observations lack a unique compatible game-team join",
            }
        counter_evidence = [link("boxscore", b["source_path"])] if b else [link("play-by-play", "/rosterSpots")]
        if box_problem:
            counter_evidence.extend(source_evidence)
        event_team, event_team_source = None, None
        if r and r["team_id"] in (game["away_team_id"], game["home_team_id"]):
            event_team, event_team_source = r["team_id"], "play-by-play"
        elif b:
            event_team, event_team_source = b["team_id"], "boxscore"
        observations = bios[player_id]
        for observation in observations:
            evidence.append({
                "input_ref": observation.get("input_ref", input_ref),
                "source": observation["source"],
                "path": f"/data/{observation['source_index']}",
                "requested_at": observation.get("requested_at"),
                "requested_season": observation.get("requested_season"),
            })
        positions = {row["reported_position"] for row in rows if row["reported_position"] is not None}
        values = {
            "player_id": player_id, "team_id": team,
            "reported_position": next(iter(positions)) if len(positions) == 1 else None,
            "first_name": None, "last_name": None,
            "name": None, "birth_date": None, "shoots_catches": None,
            "age_days": None, "bio_observations": observations,
            "reported_totals": unique_box.get("source_fields"),
        }
        result = fact(values, evidence)
        if team is None:
            _problem(result, ("team_id",), "reported game-team observations are conflicting or unavailable", "conflict" if len(teams) > 1 else "unavailable")
        if len(box) > 1:
            _problem(result, ("reported_totals",), "multiple boxscore observations", "conflict")
        if len(roster) > 1 or box_problem or team is None:
            values["identity_observations"] = {"roster": roster, "boxscore": box}
        if len(positions) > 1:
            _problem(result, ("reported_position",), "conflicting reported roster/boxscore positions", "conflict")
        values["position_observations"] = [
            {"reported_position": row["reported_position"],
             "source": "play-by-play" if "source_index" in row else "boxscore",
             "path": f"/rosterSpots/{row['source_index']}" if "source_index" in row else row["source_path"]}
            for row in rows
        ]
        for field, field_rows in (("first_name", roster), ("last_name", roster), ("name", box),
                                  ("birth_date", observations), ("shoots_catches", observations)):
            known = {row[field] for row in field_rows if row[field] is not None}
            if len(known) == 1:
                values[field] = known.pop()
                result["problems"].pop(field, None)
            elif len(known) > 1:
                reason = "conflicting attributed bio observations" if field in ("birth_date", "shoots_catches") else f"conflicting attributed {field} observations"
                _problem(result, (field,), reason, "conflict")
        if values["birth_date"] is not None:
            age = (date.fromisoformat(game["game_date"]) - date.fromisoformat(values["birth_date"])).days
            if age >= 0:
                values["age_days"] = age
                result["problems"].pop("age_days", None)
            else:
                _problem(result, ("age_days",), "birth date follows game date")
        players[str(player_id)] = {"people": result}
        identities[player_id] = {"team_id": team, "position": values["reported_position"],
                                 "box": b, "roster": r, "box_problem": box_problem,
                                 "counter_evidence": counter_evidence,
                                 "event_team_id": event_team, "event_team_source": event_team_source}
    return players, identities


def _state(attempt, event, row, game, scores, link):
    length = 1200 if event["period_number"] in (1, 2, 3) else 300 if event["period_number"] == 4 else None
    if event["timed_period"] is not True:
        length = None
    seconds = event["elapsed_seconds"] if length is not None else None
    before = scores.get(event["source_index"])
    team = event["shooting_team_id"]
    side = "away" if team == game["away_team_id"] else "home" if team == game["home_team_id"] else None
    opponent = game["home_team_id"] if side == "away" else game["away_team_id"] if side == "home" else None
    margin = (before[side] - before["home" if side == "away" else "away"]
              if before is not None and side is not None else None)
    values = {
        "away_score": before["away"] if before is not None else None,
        "home_score": before["home"] if before is not None else None,
        "score_margin": margin, "period_number": event["period_number"],
        "period_type": event["period_type"], "elapsed_seconds": seconds,
        "remaining_seconds": length - seconds if seconds is not None else None,
        "nominal_length_seconds": length, "game_seconds": _clock(event),
        "even_period_proxy": event["period_number"] == 2 if length is not None else None,
        "first_minute": seconds < 60 if seconds is not None else None,
        "last_minute": seconds >= length - 60 if seconds is not None else None,
        "home_away": side, "shooting_team_id": team, "opponent_team_id": opponent,
        "situation_code": event["situation_code"],
    }
    for field in ("away_skaters", "home_skaters", "away_goalies", "home_goalies"):
        values[field] = row[field]
        singular = field[:-1] + "_count"
        values[singular] = len(row[field]) if row[field] is not None else None
    return fact(values, [link("play-by-play", f"/plays/{event['source_index']}"),
                         link("reconstruction", f"/events/{event['source_index']}")])


def _preceding(attempt, predecessor, previous_recon, normal, game, period_sides,
               order_supported, link):
    previous = attempt["previous_event"]
    values = dict(previous)
    values.update({
        "roles": predecessor["roles"] if predecessor is not None else None,
        "reason": predecessor["reason"] if predecessor is not None else None,
        "context_reason": previous["reason"],
        "secondary_reason": predecessor.get("secondary_reason") if predecessor is not None else None,
        "penalty_description": predecessor.get("penalty_description") if predecessor is not None else None,
        "recent_same_team_attempt": None, "recent_saved_shot": None,
        "inside_zone": None, "outside_zone": None,
        "owner_team_id": predecessor["owner_team_id"] if predecessor else None,
        "shooting_team_id": predecessor["shooting_team_id"] if predecessor else None,
    })
    evidence = [link("play-by-play", f"/plays/{attempt['source_index']}")]
    if predecessor is not None:
        evidence.append(link("play-by-play", f"/plays/{predecessor['source_index']}"))
    result = fact(values, evidence)
    immediate = dict.fromkeys(("reported_x", "reported_y", "current_attack_x", "current_attack_y", "location_basis"))
    if predecessor is not None and order_supported:
        immediate["reported_x"], immediate["reported_y"] = predecessor["reported_x"], predecessor["reported_y"]
        x, y, frame_problem = attacking_coordinates(predecessor, game, attempt["shooting_team_id"], period_sides)
        if frame_problem is None and in_rink(x, y):
            immediate.update(current_attack_x=x, current_attack_y=y,
                             location_basis="block_evidence" if predecessor["type_key"] == "blocked-shot"
                             else "recorded_proxy" if predecessor["type_key"] in _ATTEMPTS else "recorded_event")
    values["immediate_geometry"] = fact(immediate, evidence,
                                        reason="immediate source location, order or focal-team frame unavailable")
    if previous["status"] == "none":
        for field in ("recent_same_team_attempt", "recent_saved_shot", "inside_zone", "outside_zone"):
            values[field] = False
            result["problems"].pop(field, None)
    elif previous["status"] == "recent":
        same = previous["owner_team_relation"] == "same"
        is_attempt = normal and same
        values["recent_same_team_attempt"] = is_attempt
        if predecessor["type_key"] == "shot-on-goal" and is_attempt:
            side = "home" if attempt["home_away"] == "away" else "away"
            goalies = previous_recon[side + "_goalies"]
            values["recent_saved_shot"] = len(goalies) == 1 if goalies is not None and len(goalies) <= 1 else None
        else:
            values["recent_saved_shot"] = False
        values["inside_zone"] = is_attempt and previous["current_attack_x"] > 25
        values["outside_zone"] = is_attempt and previous["current_attack_x"] <= 25
        for field in ("recent_same_team_attempt", "recent_saved_shot", "inside_zone", "outside_zone"):
            if values[field] is not None:
                result["problems"].pop(field, None)
    if predecessor is None:
        _problem(result, ("roles", "reason", "secondary_reason", "penalty_description"),
                 "no immediate preceding record", "not_applicable")
    if not order_supported:
        _problem(result, (field for field in values if field not in ("status", "context_reason", "immediate_geometry")),
                 "validated immediate predecessor order unavailable")
    return result


def _action_windows(ordered, game, order_supported, link):
    """fixed rolling windows; source order resolves tied clocks."""
    result = {}
    windows = {width: deque() for width in (5, 15, 30)}
    counts = {width: Counter() for width in windows}
    uncertain = {width: Counter() for width in windows}
    previous_period = None
    teams = (game["away_team_id"], game["home_team_id"])
    timing_bounds, following_clock, following_period = {}, None, None
    for event in reversed(ordered):
        if event["period_number"] != following_period:
            following_clock = None
        following_period = event["period_number"]
        if _clock(event) is not None:
            following_clock = event["elapsed_seconds"]
        timing_bounds[event["source_index"]] = following_clock
    for event in ordered:
        seconds, period = event["elapsed_seconds"], event["period_number"]
        if period != previous_period:
            for width in windows:
                windows[width].clear()
                counts[width].clear()
                uncertain[width].clear()
        previous_period = period
        snapshots = {}
        for width in windows:
            if seconds is not None:
                while windows[width] and windows[width][0][0] is not None and seconds - windows[width][0][0] > width:
                    _, keys, unknown, _ = windows[width].popleft()
                    counts[width].subtract(keys)
                    uncertain[width].subtract(unknown)
            relations = {}
            team = event["shooting_team_id"]
            for relation in ("same", "opponent"):
                owner = team if relation == "same" else next((t for t in teams if t != team), None)
                values = {kind: counts[width][owner, kind] for kind in (*ACTION_KINDS, "attempts")}
                evidence = [link("play-by-play", f"/plays/{event['source_index']}")]
                evidence.extend(link("play-by-play", f"/plays/{index}") for _, _, _, index in windows[width])
                record = fact(values, evidence)
                for kind in tuple(values):
                    if (not order_supported or seconds is None or _clock(event) is None or team not in teams
                            or uncertain[width][kind] > 0):
                        _problem(record, (kind,), "window order, clock, action kind or ownership unavailable")
                    record["values"]["known_" + kind] = counts[width][owner, kind] if order_supported else 0
                relations[relation] = record
            snapshots[str(width)] = fact(relations)
        result[event["source_index"]] = snapshots
        if event["kind_valid"] and event["type_key"] in _RESETS:
            for width in windows:
                windows[width].clear()
                counts[width].clear()
                uncertain[width].clear()
            continue
        kind, owner = event["type_key"], event["owner_team_id"]
        keys, unknown = Counter(), Counter()
        if not event["kind_valid"]:
            unknown.update((*ACTION_KINDS, "attempts"))
        elif kind in ACTION_KINDS:
            kinds = (kind, "attempts") if kind in _ATTEMPTS else (kind,)
            if owner in teams and seconds is not None and _clock(event) is not None:
                keys.update((owner, k) for k in kinds)
            else:
                unknown.update(kinds)
        for width in windows:
            windows[width].append((timing_bounds[event["source_index"]], keys, unknown, event["source_index"]))
            counts[width].update(keys)
            uncertain[width].update(unknown)
    return result


def _zone_runs(ordered, game, period_sides, order_supported, link):
    runs = {team: {"count": 0, "start": None, "unknown": False, "indices": []}
            for team in (game["away_team_id"], game["home_team_id"])}
    result, previous_period = {}, None
    for event in ordered:
        if event["period_number"] != previous_period:
            for run in runs.values():
                run.update(count=0, start=None, unknown=False, indices=[])
        previous_period = event["period_number"]
        team = event["shooting_team_id"]
        run = runs.get(team)
        values = {
            "prior_zone_run_count": run["count"] if run is not None else None,
            "prior_zone_run_start_seconds": run["start"] if run is not None else None,
            "prior_zone_run_age_seconds": event["elapsed_seconds"] - run["start"]
            if run is not None and run["start"] is not None and event["elapsed_seconds"] is not None else None,
        }
        evidence = [link("play-by-play", f"/plays/{event['source_index']}")]
        if run:
            evidence.extend(link("play-by-play", f"/plays/{i}") for i in run["indices"])
        record = fact(values, evidence)
        if (not order_supported or _clock(event) is None or run is None or run["unknown"]):
            _problem(record, values.keys(), "preceding zone run cannot be established")
        elif not run["count"]:
            _problem(record, ("prior_zone_run_start_seconds", "prior_zone_run_age_seconds"),
                     "known empty prior recorded-action run", "not_applicable")
        result[event["source_index"]] = record
        for team, run in runs.items():
            if event["kind_valid"] and event["type_key"] in _RESETS:
                run.update(count=0, start=None, unknown=False, indices=[])
                continue
            x, y, problem = attacking_coordinates(event, game, team, period_sides)
            if not event["kind_valid"] or _clock(event) is None or problem is not None or not in_rink(x, y):
                run["unknown"] = True
            elif x <= 25:
                run.update(count=0, start=None, unknown=False, indices=[])
            else:
                if not run["count"]:
                    run["start"] = event["elapsed_seconds"]
                run["count"] += 1
                run["indices"].append(event["source_index"])
    return result


def _compatible_intervals(event, row, intervals):
    relation, seconds = row["shift_relation"], event["elapsed_seconds"]
    if relation not in ("before", "after", "both") or seconds is None:
        return []
    result = []
    for index in row["interval_indices"]:
        interval = intervals[index]
        before = interval["start_seconds"] < seconds <= interval["end_seconds"]
        after = interval["start_seconds"] <= seconds < interval["end_seconds"]
        if (relation == "before" and before or relation == "after" and after
                or relation == "both" and (before or after)):
            result.append((index, interval))
    return result


def _row_members(interval, side, shifts):
    if interval["classification"] == "unresolved" or interval[side + "_skaters"] is None:
        return None
    members = {}
    for index in interval["shift_source_indices"]:
        shift = shifts[index]
        if shift["player_id"] not in interval[side + "_skaters"]:
            continue
        if (shift["interval_status"] != "coherent" or shift["type_code"] != 517
                or shift["end_seconds"] <= shift["start_seconds"]
                or shift["player_id"] in members):
            return None
        members[shift["player_id"]] = index
    return set(members.values()) if len(members) == len(interval[side + "_skaters"]) else None


def _defender_sequences(ordered, reconstruction, game, shifts, reports, order_supported, link):
    """initial coherent rows can disappear once; a returning id is a new row."""
    recon = {row["source_index"]: row for row in reconstruction["events"] or []}
    intervals = reconstruction["intervals"] or []
    by_period = defaultdict(list)
    for index, interval in enumerate(intervals):
        by_period[interval["period_number"]].append((index, interval))
    states = {team: {"survivors": None, "index": 0, "start": None,
                     "unknown": False, "period": None, "cursor": 0,
                     "evidence": []}
              for team in (game["away_team_id"], game["home_team_id"])}
    result = {}
    for event in ordered:
        if event["shooting_team_id"] not in states:
            continue
        team, row = event["shooting_team_id"], recon[event["source_index"]]
        side = "home" if team == game["away_team_id"] else "away"
        state = states[team]
        if state["period"] != event["period_number"]:
            state.update(survivors=None, index=0, start=None, unknown=False,
                         period=event["period_number"], cursor=0, evidence=[])
        if not _normal_attempt(event, row, reports.get(row["report_source_index"])):
            continue
        compatible = _compatible_intervals(event, row, intervals)
        current_rows = [_row_members(interval, side, shifts) for _, interval in compatible]
        current = current_rows[0] if current_rows and None not in current_rows and all(x == current_rows[0] for x in current_rows) else None
        # traverse every intervening span, not merely attempt endpoint rosters.
        period_intervals = by_period[event["period_number"]]
        if state["survivors"] is not None:
            boundary = max((i for i, _ in compatible), default=None)
            while state["cursor"] < len(period_intervals):
                index, interval = period_intervals[state["cursor"]]
                if interval["start_seconds"] > event["elapsed_seconds"] or boundary is not None and index > boundary:
                    break
                if interval["end_seconds"] <= state["start"]:
                    state["cursor"] += 1
                    continue
                members = _row_members(interval, side, shifts)
                state["evidence"].append(link("reconstruction", f"/intervals/{index}"))
                if members is None:
                    state["unknown"] = True
                else:
                    state["survivors"].intersection_update(members)
                state["cursor"] += 1
        if current is None or not order_supported:
            state["unknown"] = True
            possible = [members for members in current_rows if members is not None]
            if state["survivors"] is None and possible:
                state.update(survivors=set.union(*possible), start=event["elapsed_seconds"])
        elif state["survivors"] is None:
            # a supported endpoint after an unknown initial attempt cannot by
            # itself prove turnover. follow this row set until it is exhausted.
            state.update(survivors=set(current), index=0, start=event["elapsed_seconds"],
                         evidence=[link("reconstruction", f"/intervals/{i}") for i, _ in compatible])
        elif not state["survivors"]:
            state.update(survivors=set(current), index=0, start=event["elapsed_seconds"], unknown=False,
                         evidence=[link("reconstruction", f"/intervals/{i}") for i, _ in compatible])
        elif current is not None:
            state["survivors"].intersection_update(current)
            if not state["survivors"]:
                state.update(survivors=set(current), index=0, start=event["elapsed_seconds"], unknown=False)
        state["index"] += 1
        values = {
            "defender_sequence_index": state["index"] if not state["unknown"] else None,
            "defender_sequence_age_seconds": event["elapsed_seconds"] - state["start"]
            if not state["unknown"] and state["start"] is not None else None,
        }
        evidence = list(state["evidence"])
        evidence.append(link("play-by-play", f"/plays/{event['source_index']}"))
        evidence.append(link("reconstruction", f"/events/{event['source_index']}"))
        result[event["source_index"]] = fact(values, evidence,
                                             reason="defender shift-row continuity unavailable")
    return result


def _prefix_workload(ordered, reconstruction, identities, shifts, normal_attempts, order_supported, link):
    """one elapsed sweep and indexed shift/event prefixes, before each record."""
    intervals = reconstruction["intervals"] or []
    recon = {row["source_index"]: row for row in reconstruction["events"] or []}
    spans = [((row["period_number"] - 1) * 1200 + row["start_seconds"],
              (row["period_number"] - 1) * 1200 + row["end_seconds"], row)
             for row in intervals]
    bad_horizons = [(p["period_number"] - 1) * 1200 for p in reconstruction["periods"] or []
                    if p["status"] != "supported"]
    supported_shifts = {i for row in intervals if row["classification"] != "unresolved"
                        for i in row["shift_source_indices"]}
    indexed_shifts = defaultdict(lambda: {"starts": [], "ends": [], "bad_from": None})
    for shift in shifts.values():
        if shift["type_code"] != 517:
            continue
        entry = indexed_shifts[shift["player_id"]]
        period = shift["period_number"]
        if (shift["source_index"] in supported_shifts
                and shift["interval_status"] == "coherent"
                and shift["start_seconds"] < shift["end_seconds"]):
            base = (period - 1) * 1200
            entry["starts"].append((base + shift["start_seconds"], shift["source_index"]))
            entry["ends"].append((base + shift["end_seconds"], shift["source_index"]))
        else:
            earliest = (period - 1) * 1200 + (shift["start_seconds"] or 0) if period in (1, 2, 3, 4) else 0
            entry["bad_from"] = min(entry["bad_from"], earliest) if entry["bad_from"] is not None else earliest
    for entry in indexed_shifts.values():
        entry["starts"].sort()
        entry["ends"].sort()
        entry["start_clocks"] = [r[0] for r in entry["starts"]]
        entry["end_clocks"] = [r[0] for r in entry["ends"]]
    prefix = {player: Counter() for player in identities}
    incomplete_all, incomplete_5v5, unknown_attempt_teams = set(), set(), set()
    result, cursor, integrated = {}, 0, 0
    for event in ordered:
        clock = _clock(event)
        row = recon[event["source_index"]]
        if clock is not None:
            if any(start < clock for start in bad_horizons):
                incomplete_all.update(identities)
                incomplete_5v5.update(identities)
            while cursor < len(spans):
                start, end, interval = spans[cursor]
                stop = min(clock, end)
                begin = max(integrated, start)
                if stop <= begin:
                    break
                duration = stop - begin
                if interval["classification"] == "unresolved":
                    incomplete_all.update(identities)
                    incomplete_5v5.update(identities)
                else:
                    for side in ("away", "home"):
                        for player in interval[side + "_skaters"] + interval[side + "_goalies"]:
                            if player in prefix:
                                prefix[player]["toi_all_seconds"] += duration
                                if interval["classification"] == "five_on_five":
                                    prefix[player]["toi_5v5_seconds"] += duration
                integrated = stop
                if stop < end:
                    break
                cursor += 1
        if event["type_key"] in _ATTEMPTS:
            reported = set(sum((row[field] or [] for field in ("away_skaters", "home_skaters", "away_goalies", "home_goalies")), []))
            shooter = event["roles"].get("scorer" if event["type_key"] == "goal" else "shooter")
            if shooter in identities:
                reported.add(shooter)
            compatible = _compatible_intervals(event, row, intervals)
            active_rows = [set(interval["shift_source_indices"]) for _, interval in compatible]
            players = {}
            for player in reported & identities.keys():
                shift_index = indexed_shifts[player]
                values = {field: prefix[player][field] for field in ("toi_all_seconds", "toi_5v5_seconds", "attempts", "goals")}
                ambiguous = False
                for field, rows_key, clocks_key in (("shifts_begun", "starts", "start_clocks"), ("shifts_completed", "ends", "end_clocks")):
                    clocks = shift_index.get(clocks_key, [])
                    lo, hi = (bisect_left(clocks, clock), bisect_right(clocks, clock)) if clock is not None else (0, 0)
                    count = lo
                    if clock is not None:
                        for _, shift_index_id in shift_index[rows_key][lo:hi]:
                            memberships = [shift_index_id in active for active in active_rows]
                            if not memberships or any(v != memberships[0] for v in memberships):
                                ambiguous = True
                            elif field == "shifts_begun" and memberships[0] or field == "shifts_completed" and not memberships[0]:
                                count += 1
                    values[field] = count
                record = fact(values, [link("reconstruction", "/intervals"),
                                       link("shifts", "/data"),
                                       link("play-by-play", "/plays")])
                for field in tuple(values):
                    values["known_" + field] = values[field]
                if clock is None or not order_supported:
                    _problem(record, tuple(field for field in values if not field.startswith("known_")), "focal timed order/clock unavailable")
                else:
                    if player in incomplete_all:
                        _problem(record, ("toi_all_seconds",), "unknown elapsed membership in prefix")
                    if player in incomplete_5v5:
                        _problem(record, ("toi_5v5_seconds",), "unknown 5v5 membership in prefix")
                    if (ambiguous or player in incomplete_all
                            or shift_index["bad_from"] is not None and shift_index["bad_from"] <= clock
                            or indexed_shifts[None]["bad_from"] is not None and indexed_shifts[None]["bad_from"] <= clock):
                        _problem(record, ("shifts_begun", "shifts_completed"), "positive shift-prefix coverage or tied-clock frame unavailable")
                    if identities[player]["event_team_id"] is None or identities[player]["event_team_id"] in unknown_attempt_teams:
                        _problem(record, ("attempts", "goals"), "attributed earlier event count unavailable")
                players[str(player)] = record
            result[event["source_index"]] = players
        if event["source_index"] in normal_attempts:
            shooter = event["roles"].get("scorer" if event["type_key"] == "goal" else "shooter")
            if shooter in prefix and identities[shooter]["event_team_id"] == event["shooting_team_id"]:
                prefix[shooter]["attempts"] += 1
                prefix[shooter]["goals"] += event["type_key"] == "goal"
            else:
                unknown_attempt_teams.add(event["shooting_team_id"])
        elif (not event["kind_valid"] or event["timed_period"] is None
              or event["type_key"] == "goal" and event["timed_period"] is True):
            unknown_attempt_teams.update(identity["event_team_id"] for identity in identities.values())
    return result


def _outcomes(ordered, reconstruction, reports, attempts_by_index, order_supported, link):
    result = {}
    recon = {r["source_index"]: r for r in reconstruction["events"] or []}
    next_stop, intervening, terminal_seen, span_unknown = None, [], False, False
    for position in range(len(ordered) - 1, -1, -1):
        event = ordered[position]
        following = ordered[position + 1] if position + 1 < len(ordered) else None
        period = event["period_number"]
        same_period = following is not None and following["period_number"] == period
        if not same_period or event["type_key"] in ("period-end", "game-end"):
            next_stop, intervening, terminal_seen, span_unknown = None, [], False, False
        if event["kind_valid"] and event["type_key"] in ("period-end", "game-end") and _clock(event) is not None:
            terminal_seen = True
        row = recon[event["source_index"]]
        if event["source_index"] in attempts_by_index:
            next_clock = _clock(following) if following is not None else None
            delay = next_clock - _clock(event) if next_clock is not None and _clock(event) is not None else None
            stop_delay = next_stop["elapsed_seconds"] - event["elapsed_seconds"] if next_stop is not None and next_stop["elapsed_seconds"] is not None and event["elapsed_seconds"] is not None else None
            next_attempt = attempts_by_index.get(following["source_index"]) if same_period else None
            following_previous = next_attempt["previous_event"] if next_attempt is not None else None
            same_attempt = False
            if next_attempt is not None and _normal_attempt(following, recon[following["source_index"]], reports.get(recon[following["source_index"]]["report_source_index"])):
                if following_previous["status"] == "unavailable":
                    same_attempt = None
                else:
                    same_attempt = (following_previous["status"] == "recent"
                                    and following_previous["owner_team_relation"] == "same"
                                    and event["shooting_team_id"] == following["shooting_team_id"]
                                    and _normal_attempt(event, row, reports.get(row["report_source_index"])))
            modifier = row["goal_modifier_evidence"]
            focal_attempt = attempts_by_index[event["source_index"]]
            goalie_presence = row["home_goalies"] if focal_attempt["home_away"] == "away" else row["away_goalies"] if focal_attempt["home_away"] == "home" else None
            values = {
                "recorded_outcome": event["type_key"],
                "outcome": {"blocked-shot": "block", "missed-shot": "miss", "shot-on-goal": "save", "goal": "goal"}[event["type_key"]]
                if event["type_key"] != "shot-on-goal" or goalie_presence is not None and len(goalie_presence) == 1 else None,
                "on_net": event["type_key"] in ("shot-on-goal", "goal") if event["type_key"] != "blocked-shot" else None,
                "modifier": modifier["reported_value"] if modifier is not None else None,
                "blocker_id": event["roles"].get("blocker"),
                "miss_reason": event["reason"] if event["type_key"] == "missed-shot" else None,
                "penalty_reason": event.get("penalty_description"), "stoppage_reason": event["reason"],
                "next_event_source_index": following["source_index"] if following else None,
                "next_event_id": following["event_id"] if following else None,
                "next_event_kind": following["type_key"] if following else None,
                "next_event_delay_seconds": delay,
                "next_event_roles": following["roles"] if following else None,
                "next_event_reason": following["reason"] if following else None,
                "next_event_secondary_reason": following.get("secondary_reason") if following else None,
                "next_stoppage_source_index": next_stop["source_index"] if next_stop else None,
                "next_stoppage_event_id": next_stop["event_id"] if next_stop else None,
                "next_stoppage_delay_seconds": stop_delay,
                "next_stoppage_reason": next_stop["reason"] if next_stop else None,
                "next_stoppage_secondary_reason": next_stop.get("secondary_reason") if next_stop else None,
                "intervening_source_indices": [e["source_index"] for e in intervening],
                "intervening_kinds": [e["type_key"] for e in intervening],
                "next_same_team_attempt_within_5s": same_attempt,
                "next_same_team_attempt_source_index": following["source_index"] if same_attempt else None,
                "goalie_stopped_after_sog": None,
                "goalie_stoppage_delay_seconds": None,
            }
            goalie_stop = (event["type_key"] == "shot-on-goal" and next_stop is not None
                           and next_stop["reason"] == "goalie-stopped-after-sog"
                           and not any(e["type_key"] in _ATTEMPTS for e in intervening))
            pair_known = order_supported and _clock(event) is not None and not span_unknown and (next_stop is not None or terminal_seen)
            if event["type_key"] == "shot-on-goal" and pair_known:
                values["goalie_stopped_after_sog"] = bool(goalie_stop)
                values["goalie_stoppage_delay_seconds"] = stop_delay if goalie_stop else None
            evidence = [link("play-by-play", f"/plays/{event['source_index']}")]
            if following is not None:
                evidence.append(link("play-by-play", f"/plays/{following['source_index']}"))
            if next_stop is not None:
                evidence.append(link("play-by-play", f"/plays/{next_stop['source_index']}"))
            evidence.extend(link("play-by-play", f"/plays/{e['source_index']}") for e in intervening)
            record = fact(values, evidence)
            if not order_supported or _clock(event) is None:
                _problem(record, (field for field in values if field.startswith("next_") or field.startswith("goalie_stop") or field.startswith("intervening_")),
                         "validated focal order/timing unavailable")
            else:
                if following is None:
                    _problem(record, (field for field in values if field.startswith("next_event_")),
                             "known terminal has no following record" if terminal_seen else "no validated terminal proves the remaining record stream",
                             "not_applicable" if terminal_seen else "unavailable")
                elif not following["kind_valid"]:
                    _problem(record, (field for field in values if field.startswith("next_event_")),
                             "following record kind unavailable")
                elif following["timed_period"] is False:
                    _problem(record, ("next_event_delay_seconds",), "following record is untimed", "not_applicable")
                if span_unknown:
                    _problem(record, (field for field in values if field.startswith("next_stoppage_") or field.startswith("goalie_stop") or field.startswith("intervening_")),
                             "intervening chronological timing or kind unavailable")
                elif next_stop is None:
                    _problem(record, (field for field in values if field.startswith("next_stoppage_")),
                             "timed period ended without a subsequent stoppage" if terminal_seen else "no validated terminal proves the remaining period",
                             "not_applicable" if terminal_seen else "unavailable")
                if same_attempt is False:
                    _problem(record, ("next_same_team_attempt_source_index",), "no immediate same-team normal attempt within five seconds", "not_applicable")
                if same_attempt is None or delay is None and same_period or same_period and not following["kind_valid"]:
                    _problem(record, ("next_same_team_attempt_within_5s",), "following record clock unavailable")
                    _problem(record, ("next_same_team_attempt_source_index",), "immediate-predecessor rule unavailable for the next attempt")
                elif following is None and not terminal_seen and event["type_key"] not in _RESETS:
                    _problem(record, ("next_same_team_attempt_within_5s", "next_same_team_attempt_source_index"),
                             "unvalidated remaining period cannot exclude a subsequent immediate attempt")
                if event["type_key"] == "shot-on-goal" and not pair_known:
                    _problem(record, ("goalie_stopped_after_sog", "goalie_stoppage_delay_seconds"),
                             "complete validated subsequent span is unavailable")
            for field in ("on_net", "modifier", "blocker_id", "miss_reason", "penalty_reason", "stoppage_reason", "goalie_stopped_after_sog", "goalie_stoppage_delay_seconds"):
                if values[field] is None and field not in ("modifier", "blocker_id", "miss_reason"):
                    if field.startswith("goalie_stop") and event["type_key"] == "shot-on-goal" and not pair_known:
                        continue
                    _problem(record, (field,), "label does not apply to this recorded outcome", "not_applicable")
            result[event["source_index"]] = record
        if event["kind_valid"] and event["type_key"] == "stoppage":
            next_stop, intervening = event, []
            span_unknown = _clock(event) is None
        elif next_stop is not None:
            intervening.insert(0, event)
            span_unknown |= _clock(event) is None or not event["kind_valid"]
        elif _clock(event) is None or not event["kind_valid"]:
            span_unknown = True
    return result


def _deployment(attempt, event, row, intervals, shifts, shift_lists, faceoffs, last_faceoff,
                last_penalty, faceoff_uncertainty, penalty_uncertainty, transition,
                order_supported, game, period_sides, link):
    compatible = _compatible_intervals(event, row, intervals)
    evidence = [link("play-by-play", f"/plays/{event['source_index']}"),
                link("reconstruction", f"/events/{event['source_index']}")]
    evidence.extend(link("reconstruction", f"/intervals/{i}") for i, _ in compatible)
    players = {}
    membership = sum((row[field] or [] for field in ("away_skaters", "home_skaters", "away_goalies", "home_goalies")), [])
    for player in membership:
        candidates = []
        player_evidence = list(evidence)
        for _, interval in compatible:
            rows = [shifts[i] for i in interval["shift_source_indices"] if shifts[i]["player_id"] == player]
            candidates.extend(rows)
        unique = {r["source_index"] for r in candidates}
        shift = candidates[0] if (compatible and len(candidates) == len(compatible) and len(unique) == 1
                                  and all(r["interval_status"] == "coherent" and r["type_code"] == 517
                                          and r["start_seconds"] < r["end_seconds"] for r in candidates)) else None
        values = dict.fromkeys(("shift_source_index", "start_seconds", "end_seconds", "age_seconds", "previous_shift_gap_seconds", "start_type", "start_zone"))
        record = fact(values, player_evidence, reason="coherent report-compatible shift row unavailable")
        if shift is not None:
            player_evidence.append(link("shifts", f"/data/{shift['source_index']}"))
            record["evidence"] = player_evidence
            values.update(shift_source_index=shift["source_index"], start_seconds=shift["start_seconds"],
                          end_seconds=shift["end_seconds"], age_seconds=event["elapsed_seconds"] - shift["start_seconds"])
            for field in ("shift_source_index", "start_seconds", "end_seconds", "age_seconds"):
                record["problems"].pop(field, None)
            prior = [r for r in shift_lists[player, event["period_number"]] if r["source_index"] != shift["source_index"] and r["end_seconds"] is not None and r["end_seconds"] <= shift["start_seconds"]]
            if prior:
                latest = max(r["end_seconds"] for r in prior)
                latest_rows = [r for r in prior if r["end_seconds"] == latest]
                if len(latest_rows) == 1 and latest_rows[0]["interval_status"] == "coherent" and latest_rows[0]["start_seconds"] < latest:
                    values["previous_shift_gap_seconds"] = shift["start_seconds"] - latest
                    record["problems"].pop("previous_shift_gap_seconds", None)
                    record["evidence"].append(link("shifts", f"/data/{latest_rows[0]['source_index']}"))
            else:
                _problem(record, ("previous_shift_gap_seconds",), "no preceding positive shift in this period", "not_applicable")
            starts = faceoffs.get((event["period_number"], shift["start_seconds"]), [])
            unknown_starts = faceoffs.get((event["period_number"], None), []) + faceoffs.get((None, None), [])
            admitted = [f for f in starts if f[0]["kind_valid"] and f[0]["type_key"] == "faceoff"
                        and player in sum((f[1][field] or [] for field in ("away_skaters", "home_skaters", "away_goalies", "home_goalies")), [])]
            unresolved_starts = [f for f in starts if not f[0]["kind_valid"] or f[1]["classification"] == "unresolved"]
            for source_event, _ in unknown_starts + unresolved_starts:
                record["evidence"].append(link("play-by-play", f"/plays/{source_event['source_index']}"))
            if len(admitted) == 1 and not unknown_starts and not unresolved_starts and order_supported:
                faceoff = admitted[0][0]
                x, y, problem = attacking_coordinates(faceoff, game, event["shooting_team_id"], period_sides)
                values["start_type"] = "faceoff"
                record["problems"].pop("start_type", None)
                if problem is None and in_rink(x, y):
                    values["start_zone"] = _zone(x)
                    record["problems"].pop("start_zone", None)
                record["evidence"].append(link("play-by-play", f"/plays/{faceoff['source_index']}"))
            elif not starts and not unknown_starts and order_supported:
                values["start_type"] = "no_same_clock_faceoff"
                record["problems"].pop("start_type", None)
                _problem(record, ("start_zone",), "no same-clock faceoff at shift start", "not_applicable")
        players[str(player)] = record
    values = {"players": players}
    side = "away" if attempt["home_away"] == "away" else "home" if attempt["home_away"] == "home" else None
    for unit, member_side in (("attacking_five", side), ("opposing_five", "home" if side == "away" else "away" if side == "home" else None)):
        ids = row[member_side + "_skaters"] if member_side else None
        ages = [players[str(p)]["values"]["age_seconds"] for p in ids] if ids is not None else []
        complete = ids is not None and len(ids) == 5 and None not in ages
        values[unit] = fact({"age_min_seconds": min(ages) if complete else None,
                             "age_mean_seconds": sum(ages) / 5 if complete else None,
                             "age_max_seconds": max(ages) if complete else None}, evidence,
                            reason="every reported unit member needs a compatible shift age")
    faceoff_exists = (True if last_faceoff is not None else None if faceoff_uncertainty else False) if order_supported else None
    faceoff_zone, faceoff_age = None, None
    if last_faceoff is not None and order_supported and faceoff_uncertainty is None:
        x, y, problem = attacking_coordinates(last_faceoff, game, event["shooting_team_id"], period_sides)
        if problem is None and in_rink(x, y):
            faceoff_zone = _zone(x)
        if last_faceoff["elapsed_seconds"] is not None and event["elapsed_seconds"] is not None:
            faceoff_age = event["elapsed_seconds"] - last_faceoff["elapsed_seconds"]
        evidence.append(link("play-by-play", f"/plays/{last_faceoff['source_index']}"))
    for uncertain_event in (faceoff_uncertainty, penalty_uncertainty):
        if uncertain_event is not None:
            evidence.append(link("play-by-play", f"/plays/{uncertain_event['source_index']}"))
    values.update({
        "last_faceoff_exists": faceoff_exists,
        "last_faceoff_source_index": last_faceoff["source_index"] if last_faceoff and faceoff_uncertainty is None else None,
        "last_faceoff_zone": faceoff_zone, "last_faceoff_age_seconds": faceoff_age,
        "strength_transition_exists": transition["exists"],
        "previous_strength_side": transition["side"],
        "strength_transition_age_seconds": transition["age"],
        "penalty_source_index": last_penalty["source_index"] if last_penalty else None,
        "penalty_team_id": last_penalty["owner_team_id"] if last_penalty else None,
        "penalty_roles": last_penalty["roles"] if last_penalty else None,
        "penalty_type": last_penalty["penalty_type"] if last_penalty else None,
        "penalty_description": last_penalty.get("penalty_description") if last_penalty else None,
        "penalty_duration_minutes": last_penalty["penalty_duration_minutes"] if last_penalty else None,
        "penalty_age_seconds": event["elapsed_seconds"] - last_penalty["elapsed_seconds"]
        if last_penalty and event["elapsed_seconds"] is not None and last_penalty["elapsed_seconds"] is not None else None,
        "interval_substitution_count": None, "endpoint_change_count": None,
    })
    if compatible:
        endpoint = min(i for i, _ in compatible)
        current = intervals[endpoint]
        previous = intervals[endpoint - 1] if endpoint and intervals[endpoint - 1]["period_number"] == event["period_number"] else None
        if previous is not None and previous["classification"] != "unresolved" and current["classification"] != "unresolved":
            values["interval_substitution_count"] = len(set(previous["shift_source_indices"]) - set(current["shift_source_indices"]))
            values["endpoint_change_count"] = sum(len(set(previous[field]) - set(current[field])) for field in ("away_skaters", "home_skaters", "away_goalies", "home_goalies"))
        elif previous is None and current["start_seconds"] == 0:
            values["interval_substitution_count"] = 0
            values["endpoint_change_count"] = 0
    result = fact(values, evidence)
    if faceoff_exists is False:
        _problem(result, ("last_faceoff_source_index", "last_faceoff_zone", "last_faceoff_age_seconds"),
                 "no preceding faceoff in this timed period", "not_applicable")
    if transition["exists"] is False:
        _problem(result, ("previous_strength_side", "strength_transition_age_seconds"),
                 "no supported unequal-strength return before reset", "not_applicable")
    if penalty_uncertainty is not None or not order_supported:
        _problem(result, (field for field in values if field.startswith("penalty_")),
                 "latest preceding penalty identity cannot be established")
    elif last_penalty is None:
        _problem(result, (field for field in values if field.startswith("penalty_")),
                 "no preceding penalty award in this period", "not_applicable")
    return result


def _strength_transitions(ordered, reconstruction, game, order_supported):
    intervals = reconstruction["intervals"] or []
    recon = {row["source_index"]: row for row in reconstruction["events"] or []}
    by_period = defaultdict(list)
    for interval in intervals:
        by_period[interval["period_number"]].append(interval)
    starts = {period: [row["start_seconds"] for row in rows] for period, rows in by_period.items()}
    result = {}
    period, cursor, reset_time = None, 0, 0
    prior, returned, unknown = None, None, False
    for event in ordered:
        if event["period_number"] != period:
            period, cursor, reset_time = event["period_number"], 0, 0
            prior, returned, unknown = None, None, False
        if _clock(event) is not None:
            rows = by_period[period]
            before_only = recon[event["source_index"]]["shift_relation"] == "before"
            while (cursor < len(rows) and (rows[cursor]["start_seconds"] < event["elapsed_seconds"]
                   or not before_only and rows[cursor]["start_seconds"] == event["elapsed_seconds"])):
                interval = rows[cursor]
                if interval["start_seconds"] >= reset_time:
                    if interval["classification"] == "unresolved":
                        unknown = True
                    else:
                        away, home = len(interval["away_skaters"]), len(interval["home_skaters"])
                        if away != home:
                            prior, returned = "away" if away < home else "home", None
                        elif interval["classification"] == "five_on_five" and prior is not None and returned is None:
                            returned = interval["start_seconds"]
                cursor += 1
        focal_side = "away" if event["shooting_team_id"] == game["away_team_id"] else "home"
        exists = returned is not None
        result[event["source_index"]] = {
            "exists": None if unknown or not order_supported or _clock(event) is None else exists,
            "side": "same" if prior == focal_side else "opponent" if prior is not None else None,
            "age": event["elapsed_seconds"] - returned if returned is not None and event["elapsed_seconds"] is not None else None,
        }
        if event["kind_valid"] and event["type_key"] in _RESETS:
            prior, returned, unknown = None, None, False
            reset_time = event["elapsed_seconds"] if event["elapsed_seconds"] is not None else 0
            # the ongoing interval also supplies membership after a reset.
            # an unequal-strength span need not begin at the reset clock.
            position = bisect_right(starts.get(period, []), reset_time) - 1
            if position >= 0:
                active = by_period[period][position]
                if reset_time < active["end_seconds"]:
                    if active["classification"] == "unresolved":
                        unknown = True
                    else:
                        away, home = len(active["away_skaters"]), len(active["home_skaters"])
                        if away != home:
                            prior = "away" if away < home else "home"
    return result


def _history_summary(document, reconstruction, identities, attempts, normal_attempts, input_ref, link):
    game = document["game"]
    exposures = {row["player_id"]: row for row in reconstruction["player_exposure"] or []}
    attributed_attempts = Counter()
    uncertain_teams = set()
    credited_goals, credited_sog = Counter(), Counter()
    uncertain_goals, uncertain_sog = set(), set()
    recon = {row["source_index"]: row for row in reconstruction["events"] or []}
    teams = (game["away_team_id"], game["home_team_id"])
    for event in document["events"] or []:
        if not event["kind_valid"] or event["timed_period"] is None:
            uncertain_goals.update(teams)
            uncertain_sog.update(teams)
            continue
        if event["timed_period"] is not True or event["type_key"] not in ("shot-on-goal", "goal"):
            continue
        player = event["roles"].get("scorer" if event["type_key"] == "goal" else "shooter")
        team = event["shooting_team_id"]
        attributed = player in identities and identities[player]["event_team_id"] == team
        relevant = (team,) if team in teams else teams
        if event["type_key"] == "goal":
            if attributed:
                credited_goals[player] += 1
            else:
                uncertain_goals.update(relevant)
            modifier = recon[event["source_index"]]["goal_modifier_evidence"]
            if modifier is None or modifier["status"] != "reported" or modifier["reported_value"] not in ("none", "penalty-shot"):
                uncertain_sog.update(relevant)
                continue
        if attributed:
            credited_sog[player] += 1
        else:
            uncertain_sog.update(relevant)
    for attempt in attempts:
        event = attempt["source_event"]
        if event["timed_period"] is not True or event["type_key"] not in _ATTEMPTS:
            continue
        modifier = attempt["goal_modifier_evidence"]
        if modifier is not None and modifier["status"] == "reported" and modifier["reported_value"] == "penalty-shot":
            continue
        if event["source_index"] not in normal_attempts:
            if "physical_attempt_unresolved" in attempt["reasons"]:
                uncertain_teams.update((game["away_team_id"], game["home_team_id"]) if attempt["shooting_team_id"] is None else (attempt["shooting_team_id"],))
            continue
        shooter = event["roles"].get("scorer" if event["type_key"] == "goal" else "shooter")
        if shooter in identities and identities[shooter]["event_team_id"] == event["shooting_team_id"]:
            attributed_attempts[shooter] += 1
        else:
            uncertain_teams.update((game["away_team_id"], game["home_team_id"]) if attempt["shooting_team_id"] is None else (attempt["shooting_team_id"],))
    if any(not row["kind_valid"] or row["timed_period"] is None for row in document["events"] or []):
        uncertain_teams.update((game["away_team_id"], game["home_team_id"]))
    complete_roster = (document["roster_records"] is not None and document["boxscore_players"] is not None
                       and len(identities) == len(document["roster_records"])
                       and all(row["player_id"] in identities for row in document["roster_records"])
                       and all(row["player_id"] in identities for row in document["boxscore_players"]))
    intervals = reconstruction["intervals"] or []
    supported_all = Counter()
    for interval in intervals:
        if interval["classification"] == "unresolved":
            continue
        duration = interval["end_seconds"] - interval["start_seconds"]
        for side in ("away", "home"):
            for player in interval[side + "_skaters"] + interval[side + "_goalies"]:
                supported_all[player] += duration
    full_elapsed = bool(intervals) and bool(reconstruction["periods"]) and all(p["status"] == "supported" for p in reconstruction["periods"]) and all(i["classification"] != "unresolved" for i in intervals)
    supported_rows = {i for interval in intervals if interval["classification"] != "unresolved"
                      for i in interval["shift_source_indices"]}
    shift_counts = Counter(row["player_id"] for row in document["shift_records"] or []
                           if row["source_index"] in supported_rows and row["type_code"] == 517
                           and row["interval_status"] == "coherent" and row["start_seconds"] < row["end_seconds"])
    goals_complete, sog_complete = True, {team: True for team in teams}
    for source in ("play-by-play", "boxscore"):
        goal_checks = [c for c in document["checks"] if c["name"] == "timed_goals" and c.get("source") == source]
        goals_complete &= len(goal_checks) == 1 and goal_checks[0]["status"] == "match"
        for team in teams:
            shot_checks = [c for c in document["checks"] if c["name"] == "timed_shots" and c.get("source") == source and c.get("team_id") == team]
            sog_complete[team] &= len(shot_checks) == 1 and shot_checks[0]["status"] == "match"
    players = {}
    for player, identity in identities.items():
        box = identity["box"]
        fields = box.get("source_fields", {"values": {}})["values"]
        toi = box.get("toi_seconds")
        appearance = toi > 0 if toi is not None else None
        goalie = identity["position"] == "G" if identity["position"] is not None else None
        starter = fields.get("starter") if goalie else None
        exposure = exposures.get(player)
        event_team = identity["event_team_id"]
        known_5v5 = (exposure["supported_5v5_seconds"] if exposure else sum(
            i["end_seconds"] - i["start_seconds"] for i in intervals
            if i["classification"] == "five_on_five" and player in i["away_goalies"] + i["home_goalies"]))
        complete_5v5 = exposure["complete"] if exposure else goalie and full_elapsed
        zero_toi_conflict = appearance is False and supported_all[player] > 0
        if appearance is False:
            if zero_toi_conflict:
                appearance = None
            else:
                complete_5v5, known_5v5 = True, 0
        shift_count = box.get("shift_count")
        reconstructed_shifts = shift_count is None and full_elapsed
        if reconstructed_shifts:
            shift_count = shift_counts[player]
        if goalie:
            goals = None
            if event_team in teams and goals_complete and event_team not in uncertain_goals:
                goals = credited_goals[player]
            sog = None
            if event_team in teams and sog_complete[event_team] and event_team not in uncertain_sog:
                sog = credited_sog[player]
            counter_basis = {
                "goals": "timed_recorded_scorer_credits",
                "sog": "timed_recorded_shooter_credits_and_supported_physical_goals",
            }
        else:
            goals, sog = box.get("goals"), box.get("sog")
            counter_basis = {"goals": "reported_boxscore_goals", "sog": "reported_boxscore_sog"}
        values = {
            "ice_appearances": int(appearance) if appearance is not None else None,
            "starts": int(starter) if starter is not None else None,
            "relief_appearances": int(not starter and appearance) if starter is not None and appearance is not None else None,
            "toi_all_seconds": toi,
            "toi_5v5_seconds": known_5v5 if complete_5v5 else None,
            "shifts": shift_count,
            "attempts": attributed_attempts[player] if event_team in teams and event_team not in uncertain_teams and document["events"] is not None else None,
            "goals": goals,
            "sog": sog,
            "saves": fields.get("saves") if goalie else None,
            "shots_against": fields.get("shotsAgainst") if goalie else None,
            "goals_against": fields.get("goalsAgainst") if goalie else None,
        }
        known_values = dict(values)
        known_values["toi_5v5_seconds"] = known_5v5
        known_values["attempts"] = attributed_attempts[player]
        if goalie:
            known_values["goals"] = credited_goals[player]
            known_values["sog"] = credited_sog[player]
        if zero_toi_conflict:
            known_values["toi_all_seconds"] = supported_all[player]
        evidence = identity["counter_evidence"] + [link("play-by-play", "/plays"), link("reconstruction", "/player_exposure")]
        if zero_toi_conflict or reconstructed_shifts:
            evidence.append(link("reconstruction", "/intervals"))
        if reconstructed_shifts:
            evidence.append(link("shifts", "/data"))
        record = fact(values, evidence)
        record["counter_basis"] = counter_basis
        if zero_toi_conflict:
            fields = ["ice_appearances", "toi_all_seconds"]
            if known_5v5 is not None and known_5v5 > 0:
                fields.append("toi_5v5_seconds")
            _problem(record, fields, "zero reported toi conflicts with positive supported exposure", "conflict")
            record["counter_basis"]["known_toi_all_seconds"] = "supported_all_strength_interval_membership_lower_bound"
        if identity["team_id"] is None and event_team is not None:
            record["counter_basis"]["event_team"] = {"source": identity["event_team_source"], "reported_team_id": event_team}
        if identity["box_problem"]:
            box_fields = ["ice_appearances", "starts", "relief_appearances", "toi_all_seconds", "shifts"]
            if goalie is not True:
                box_fields.extend(("goals", "sog"))
            if goalie is not False:
                box_fields.extend(("saves", "shots_against", "goals_against"))
            _problem(record, tuple(field for field in box_fields if values[field] is None),
                     identity["box_problem"]["reason"], identity["box_problem"]["status"])
        if goalie is False:
            _problem(record, ("starts", "relief_appearances", "saves", "shots_against", "goals_against"),
                     "goaltending counter for a reported skater", "not_applicable")
        for field, value in known_values.items():
            known_field = "known_" + field
            record["values"][known_field] = value
            if value is None:
                record["problems"][known_field] = dict(record["problems"][field])
        players[str(player)] = {"team_id": identity["team_id"], "role": identity["position"],
                                "participation": appearance, "counters": record}
    return {**game, "input_ref": input_ref, "players": players,
            "complete_roster": complete_roster}


def prepare_missing_game(entry, *, input_ref):
    """an inventory game is retained even when no analytical source joins."""
    link = _links(input_ref)
    evidence = [link("season-games", f"/data/{entry.get('source_index', entry.get('inventory_source_index', 0))}")]
    game_facts = {
        "game": fact({field: entry[field] for field in ("game_id", "season", "game_date", "away_team_id", "home_team_id")}, evidence),
        "recording": fact({"observations": None}, evidence, reason="game capture or identity unavailable"),
        "component": fact({"events": None, "reported_totals": None}, evidence, reason="game evidence unavailable"),
        "coach_team": fact({"observations": None}, evidence, reason="game evidence unavailable"),
        "people": fact({"player_ids": None}, evidence, reason="attributed roster/boxscore unavailable"),
        "teams": {str(entry[side + "_team_id"]): {} for side in ("away", "home")},
    }
    return {"game_facts": game_facts, "player_game_facts": {}, "history_summary": None}


def prepare_game(envelope, attempts, *, input_ref, bio_rows, chronology):
    """prepare shared rows and local attempt facts without changing eligibility."""
    document, reconstruction = envelope["interpreted"], envelope["reconstruction"]
    game = document["game"]
    link = _links(input_ref)
    players, identities = _people(document, bio_rows, input_ref, link)
    events = {row["source_index"]: row for row in document["events"] or []}
    recon = {row["source_index"]: row for row in reconstruction["events"] or []}
    reports = {row["source_index"]: row for row in document["report_rows"] or []}
    shifts = {row["source_index"]: row for row in document["shift_records"] or []}
    ordered = chronology["ordered"] or list(events.values())
    order_supported = chronology["order_supported"] and chronology["ordered"] is not None
    interval_rows = reconstruction["intervals"] or []
    period_sides = defending_sides(ordered)
    normal = {event["source_index"] for event in ordered if _normal_attempt(event, recon[event["source_index"]], reports.get(recon[event["source_index"]]["report_source_index"]))}
    action_windows = _action_windows(ordered, game, order_supported, link)
    zone_runs = _zone_runs(ordered, game, period_sides, order_supported, link)
    sequences = _defender_sequences(ordered, reconstruction, game, shifts, reports, order_supported, link)
    prefixes = _prefix_workload(ordered, reconstruction, identities, shifts, normal, order_supported, link)
    attempts_by_index = {a["source_index"]: a for a in attempts}
    outcomes = _outcomes(ordered, reconstruction, reports, attempts_by_index, order_supported, link)
    transitions = _strength_transitions(ordered, reconstruction, game, order_supported)
    faceoffs, shift_lists = defaultdict(list), defaultdict(list)
    for event in ordered:
        if event["type_key"] == "faceoff" or not event["kind_valid"]:
            number = event["period_number"]
            seconds = event["elapsed_seconds"] if event["timed_period"] is True else None
            faceoffs[number, seconds].append((event, recon[event["source_index"]]))
    for shift in shifts.values():
        if shift["type_code"] == 517:
            shift_lists[shift["player_id"], shift["period_number"]].append(shift)
    previous, last_faceoff, last_penalty, period = None, None, None, None
    faceoff_uncertainty, penalty_uncertainty = None, None
    for event in ordered:
        if event["period_number"] != period:
            last_faceoff, last_penalty, period = None, None, event["period_number"]
            faceoff_uncertainty, penalty_uncertainty = None, None
        index = event["source_index"]
        attempt = attempts_by_index.get(index)
        if attempt is not None:
            row = recon[index]
            shooter_people = players.get(str(attempt["shooter_id"]), {}).get("people")
            hand = shooter_people["values"]["shoots_catches"] if shooter_people else None
            geometry = candidate_geometry((attempt["attacking_x"], attempt["attacking_y"]), attempt["previous_event"], hand)
            recorded_evidence = [link("play-by-play", f"/plays/{index}"),
                                 link("reconstruction", f"/events/{index}")]
            report = reports.get(row["report_source_index"])
            if report is not None:
                recorded_evidence.append(link("play-report", f"/rows/{report['source_index']}[{report['row_id']}]"))
            geometry["evidence"] = list(recorded_evidence)
            previous_index = attempt["previous_event"].get("source_index")
            geometry["evidence"].append(link("play-by-play", f"/plays/{previous_index}" if previous_index is not None else "/plays"))
            geometry["evidence"].extend(shooter_people["evidence"] if shooter_people else [
                link("play-by-play", "/rosterSpots"), link("boxscore", "/playerByGameStats")])
            refs = list(range(len(geometry["evidence"])))
            for problem in geometry["problems"].values():
                problem["evidence_refs"] = refs
            if attempt["blocked"]:
                _problem(geometry, tuple(geometry["values"]), "block contact does not establish shooting origin")
            geometry["values"]["recorded"] = fact({
                "recorded_shot_type": event["shot_type"],
                "reconciled_shot_type": attempt["shot_type"],
                "model_shot_type": attempt["model_shot_type"],
                "reported_x": attempt["reported_x"], "reported_y": attempt["reported_y"],
                "location_kind": attempt["location_kind"],
                "coordinate_status": row["coordinate_status"],
            }, recorded_evidence)
            sequence = sequences.get(index, fact({"defender_sequence_index": None, "defender_sequence_age_seconds": None},
                                                 [link("play-by-play", f"/plays/{index}")],
                                                 reason="record is not a supported normal timed attempt"))
            zone = zone_runs[index]
            offset = len(sequence["evidence"])
            sequence["evidence"].extend(zone["evidence"])
            sequence["values"].update(zone["values"])
            sequence["problems"].update({field: {**problem, "evidence_refs": [i + offset for i in problem["evidence_refs"]]}
                                         for field, problem in zone["problems"].items()})
            sequence["values"]["action_counts"] = action_windows[index]
            local_prefixes = prefixes.get(index, {})
            opposing_side = "home" if attempt["home_away"] == "away" else "away"
            opposing_ids = row[opposing_side + "_skaters"]
            tois = [local_prefixes.get(str(p), {"values": {}})["values"].get("toi_all_seconds") for p in opposing_ids] if opposing_ids else []
            complete = opposing_ids is not None and len(opposing_ids) == 5 and None not in tois
            workload = fact({
                "players": local_prefixes,
                "opposing_five": fact({"toi_all_mean_seconds": sum(tois) / 5 if complete else None,
                                        "toi_all_max_seconds": max(tois) if complete else None},
                                       [link("reconstruction", "/intervals")]),
            })
            attempt["feature_facts"] = {
                "geometry": geometry,
                "state": _state(attempt, event, row, game, chronology["scores"], link),
                "preceding": _preceding(attempt, previous, recon[previous["source_index"]] if previous else None,
                                         previous is not None and previous["source_index"] in normal,
                                         game, period_sides, order_supported, link),
                "sequence": sequence,
                "deployment": _deployment(attempt, event, row, interval_rows, shifts, shift_lists, faceoffs,
                                           last_faceoff, last_penalty, faceoff_uncertainty, penalty_uncertainty,
                                           transitions[index], order_supported,
                                           game, period_sides, link),
                "current_workload": workload,
                "outcome": outcomes[index],
            }
        if event["kind_valid"] and event["type_key"] == "faceoff":
            last_faceoff = event
            faceoff_uncertainty = None
        if event["kind_valid"] and event["type_key"] == "penalty":
            last_penalty = event
            penalty_uncertainty = None
        if not event["kind_valid"]:
            faceoff_uncertainty, penalty_uncertainty = event, event
        previous = event
    game_evidence = [link("interpreted", "/game")]
    game_facts = {
        "game": fact(dict(game), game_evidence),
        "recording": fact({"observations": document.get("recording_observations")}, game_evidence),
        "component": fact({"events": [
            fact({"source_index": event["source_index"], "event_id": event["event_id"],
             "kind": event["type_key"], "roles": event["roles"],
             "owner_team_id": event["owner_team_id"],
             "reason": event["reason"], "secondary_reason": event.get("secondary_reason"),
             "penalty_type": event["penalty_type"],
             "penalty_description": event.get("penalty_description"),
             "penalty_duration_minutes": event["penalty_duration_minutes"],
             "source_locator": link("play-by-play", f"/plays/{event['source_index']}")},
                 [link("play-by-play", f"/plays/{event['source_index']}")])
            for event in ordered
        ], "reported_totals": document["boxscore_players"]}, game_evidence),
        "coach_team": fact({"observations": document.get("coach_scratch_observations")}, game_evidence),
        "people": fact({"player_ids": [int(p) for p in players]}, game_evidence),
        "teams": {str(game[side + "_team_id"]): {} for side in ("away", "home")},
    }
    return {"game_facts": game_facts, "player_game_facts": players,
            "history_summary": _history_summary(document, reconstruction, identities, attempts, normal, input_ref, link)}
