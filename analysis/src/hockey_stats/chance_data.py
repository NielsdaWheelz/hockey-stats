"""prepare selected 02c evidence; no acquisition, reconstruction or fitting.

public contract: prepare(selection_path) returns a finite-json-compatible dict:
  attempts: every recognized attempt, including exclusions, in source order;
  coverage: games_by_status, games/attempts counts and per_game evidence ledger;
  inputs: {kind, path, sha256} for the actual bytes read;
  selection: schema 2 target/history selection with absolute corpus paths;
  purpose: fixture_exercise or research; game_dates: selected id -> inventory date;
  games: selected inventory/status ledger; input_roots: absolute parents;
  preparation_identity: exact fact contract; feature_games and
  feature_player_games: shared keyed facts; feature_facts: local attempt facts.

prepare_core(selection_path) returns the same source projection and identity,
without retained feature/history facts. history_corpora must be empty; both
per-game feature joins remain complete dictionaries with empty inactive values.

prepare_game_attempts(envelope, envelope_path, inventory_entry) returns core
attempts, unclassified_events, evidence and chronology without retained features.

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
import hashlib
import json
import re
from pathlib import Path

from .captures import InputContractError
from .corpus import STATUSES
from .corpus_inputs import (
    IDENTITY_FIELDS, array, load_corpus, object_fields, read_document, require, schema, text,
    validate_envelope,
)
from .game_chronology import period_length, score_chronology
from .feature_data import ACTION_KINDS, ATTEMPT_KINDS, RESETS
from .shot_origins import in_rink
from .reconstruct import (
    attacking_coordinates, defending_sides,
)

_ATTEMPTS = ATTEMPT_KINDS
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
_RESETS = RESETS
_RECENT = set(ACTION_KINDS)


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
    length, seconds = period_length(event), event["elapsed_seconds"]
    if predecessor is not None:
        result.update(
            source_index=predecessor["source_index"],
            event_id=predecessor["event_id"],
            kind=predecessor["type_key"],
        )
        prior_length, prior_seconds = (
            period_length(predecessor),
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


def prepare_game_attempts(envelope, envelope_path, inventory_entry):
    """validate and prepare one game's core attempts, evidence and chronology."""
    interpreted, reconstructed, events, recon, reports = validate_envelope(
        envelope, envelope_path, inventory_entry
    )
    game = interpreted["game"]
    scores, score_failures, ordered, order_supported = score_chronology(
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
        length, seconds = period_length(event), event["elapsed_seconds"]
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
                "file": str(envelope_path),
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
                    {"file": str(envelope_path), "layer": "interpreted", "index": i, **issue}
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
    return {
        "attempts": attempts,
        "unclassified_events": sum(not event["kind_valid"] for event in events.values()),
        "evidence": {
            "source_inputs": interpreted["inputs"],
            "interpreted_issues": interpreted["issues"],
            "reconstruction_issues": reconstructed["issues"],
            "source_coverage": reconstructed["coverage"],
            "score_support": "unavailable" if score_failures else "supported",
            "score_issues": score_failures,
            "event_collection_available": interpreted["events"] is not None,
        },
        "chronology": {"ordered": ordered, "order_supported": order_supported, "scores": scores},
    }


def prepare(selection_path):
    """assemble target facts once; history adds strictly earlier evidence only."""
    return _prepare(selection_path, include_features=True)


def prepare_core(selection_path):
    """prepare source evidence with explicitly inactive feature/history joins."""
    return _prepare(selection_path, include_features=False)


def _prepare(selection_path, *, include_features):
    from .chance_features import PREPARATIONIDENTITY_FIELDS
    if include_features:
        from .feature_data import prepare_game, prepare_missing_game
        from .feature_history import prepare_history

    path = Path(selection_path).resolve()
    inputs = []
    selection = read_document(path, "selection", inputs)
    schema(selection, str(path), 2, ("purpose", "corpora", "history_corpora"))
    require(set(selection) == {"schema_version", "purpose", "corpora", "history_corpora"},
             path, "unexpected selection fields")
    require(selection["purpose"] in ("fixture_exercise", "research"), path,
             "unsupported purpose")
    corpora = array(selection["corpora"], f"{path}/corpora")
    require(bool(corpora), path, "nonempty explicit corpus selection required")
    selected_ids, resolved, target_paths = set(), [], {}
    for i, selected in enumerate(corpora):
        loc = f"{path}/corpora/{i}"
        object_fields(selected, loc, ("path", "game_ids"))
        require(set(selected) == {"path", "game_ids"}, loc,
                 "unexpected corpus selection fields")
        text(selected["path"], loc + "/path")
        require(bool(selected["path"]), loc, "empty corpus path")
        corpus_path = str((path.parent / selected["path"]).resolve())
        ids = array(selected["game_ids"], loc + "/game_ids")
        require(bool(ids), loc, "nonempty explicit game_ids required")
        for gid in ids:
            require(type(gid) is str and re.fullmatch(r"[0-9]{10}", gid), loc,
                     "expected ten-digit string game id")
            require(gid not in selected_ids, loc, "duplicate selected game id " + gid)
            selected_ids.add(gid)
            target_paths[gid] = corpus_path
        resolved.append({"path": corpus_path, "game_ids": list(ids)})
    history_paths = []
    for i, value in enumerate(array(selection["history_corpora"], f"{path}/history_corpora")):
        loc = f"{path}/history_corpora/{i}"
        text(value, loc)
        require(bool(value), loc, "empty history corpus path")
        corpus_path = str((path.parent / value).resolve())
        require(corpus_path not in history_paths, loc, "duplicate history corpus path")
        history_paths.append(corpus_path)
    require(include_features or not history_paths, f"{path}/history_corpora",
             "core preparation requires history_corpora=[]")
    input_roots = {str(path.parent)}
    bio_observations, reference_signatures, candidates = {}, {}, defaultdict(list)
    target_inventories, history_ids = set(), set()
    identities = {}
    for value in dict.fromkeys([row["path"] for row in resolved] + history_paths):
        corpus_path = Path(value)
        input_roots.add(str(corpus_path.parent))
        document, inventory, ledger = load_corpus(corpus_path, inputs)
        reference_signatures[value] = hashlib.sha256(json.dumps(document["reference"], sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        require(all(gid in inventory for gid, target in target_paths.items() if target == value),
                 corpus_path, "target game absent from its explicitly selected inventory")
        if include_features:
            bio_observations[value] = [{**observation, "input_ref": value}
                for observation in document["reference"]["bio_observations"]]
        admitted = value in history_paths
        if value in target_paths.values():
            target_inventories.update(inventory)
        if admitted:
            history_ids.update(inventory)
        for gid, entry in inventory.items():
            if gid in identities:
                require(all(identities[gid][field] == entry[field] for field in IDENTITY_FIELDS),
                         corpus_path, "conflicting inventory identity for " + gid)
            else:
                identities[gid] = {**entry, "input_ref": value, "selection_input_ref": str(path), "history_admitted": False}
            identities[gid]["history_admitted"] |= admitted
            if admitted or target_paths.get(gid) == value:
                candidates[gid].append((value, entry, ledger[gid]))
    require(selected_ids <= target_inventories, path,
             "unknown selected game ids: " + ", ".join(sorted(selected_ids - target_inventories)))
    require(not history_paths or selected_ids <= history_ids, path,
             "nonempty history inventories must contain every target")
    target_order = [gid for row in resolved for gid in row["game_ids"]]
    target_attempts, target_counts, target_games, summaries = {}, {}, {}, {}
    feature_games = {gid: {} for gid in target_order}
    feature_player_games = {gid: {} for gid in target_order}
    requested = selected_ids | history_ids
    for gid in sorted(requested, key=lambda key: (identities[key]["game_date"], key)):
        chosen, chosen_path, chosen_signature, chosen_corpus, chosen_entry, chosen_row = None, None, None, None, None, None
        chosen_reference_signature = None
        seen_paths = set()
        for corpus_value, entry, row in candidates[gid]:
            corpus_path = Path(corpus_value)
            status = row["status"]
            if status in ("input_error", "identity_mismatch"):
                raise InputContractError(f"{corpus_path}/games/{gid}: {status}: {row['reason']}")
            reference_signature = reference_signatures[corpus_value]
            require(chosen_reference_signature is None or reference_signature == chosen_reference_signature,
                     corpus_path, "different reference bio snapshots for historical game " + gid)
            chosen_reference_signature = reference_signature
            envelope, envelope_path, signature = None, None, (status,)
            if status == "reconstructed":
                envelope_path = (corpus_path.parent / row["output_path"]).resolve()
                input_roots.add(str(envelope_path.parent))
                if envelope_path in seen_paths:
                    continue
                seen_paths.add(envelope_path)
                envelope = read_document(envelope_path, "game", inputs)
                signature = (status, inputs[-1]["sha256"])
            require(chosen_signature is None or signature == chosen_signature, corpus_path,
                     "different snapshots of historical game " + gid)
            if chosen_signature is None:
                chosen, chosen_path, chosen_signature = envelope, envelope_path, signature
                chosen_corpus, chosen_entry, chosen_row = corpus_value, entry, row
        status = chosen_row["status"]
        if chosen is not None:
            core = prepare_game_attempts(chosen, chosen_path, chosen_entry)
            attempts, unclassified, evidence = (
                core["attempts"], core["unclassified_events"], core["evidence"])
            if include_features:
                features = prepare_game(chosen, attempts, input_ref=str(chosen_path),
                    bio_rows=bio_observations[chosen_corpus], chronology=core["chronology"])
                summaries[gid] = features["history_summary"]
        else:
            attempts, unclassified, evidence = [], 0, {"event_collection_available": False}
            if include_features:
                features = prepare_missing_game(chosen_entry, input_ref=chosen_corpus)
                summaries[gid] = None
        if gid not in selected_ids:
            continue
        selected_corpus = target_paths[gid]
        selected_entry = identities[gid]
        target_games[gid] = {**{field: selected_entry[field] for field in chosen_entry},
            "corpus_path": selected_corpus, "status": status, "reason": chosen_row["reason"],
            "output_path": chosen_row["output_path"]}
        target_attempts[gid] = attempts
        if include_features:
            feature_games[gid] = features["game_facts"]
            feature_player_games[gid] = features["player_game_facts"]
        available = evidence["event_collection_available"]
        target_counts[gid] = {
            "game_id": gid, "game_date": chosen_entry["game_date"], "corpus_status": status,
            "reason": chosen_row["reason"], "known_attempts": len(attempts) if available else None,
            "recognized_attempts": len(attempts) if available else None,
            "genuine_five_on_five_attempts": sum(a["classification"] == "five_on_five"
                and a["source_event"]["timed_period"] is True for a in attempts) if available else None,
            "chance_2_eligible_attempts": sum(a["status"] == "eligible" for a in attempts) if available else None,
            "goals_by_status": {s: sum(a["goal"] and a["status"] == s for a in attempts)
                for s in ("eligible", "out_of_scope", "unavailable")} if available else None,
            "excluded_goals_by_reason": {r: sum(a["goal"] and a["status"] != "eligible"
                and r in a["reasons"] for a in attempts) for r in _REASONS} if available else None,
            "unclassifiable_source_rows": unclassified if available else None,
            "attempts_by_status": {s: sum(a["status"] == s for a in attempts)
                for s in ("eligible", "out_of_scope", "unavailable")} if available else None,
            "attempts_by_reason": {r: sum(r in a["reasons"] for a in attempts)
                for r in _REASONS} if available else None, **evidence}
    if include_features:
        history = prepare_history(list(identities.values()), summaries, target_order)
        for gid in target_order:
            for team_id, groups in history["games"][gid]["teams"].items():
                require(team_id in feature_games[gid]["teams"], gid,
                         "history join lacks target team " + team_id)
                feature_games[gid]["teams"][team_id].update(groups)
            for player_id, groups in history["players"][gid].items():
                require(player_id in feature_player_games[gid], gid,
                         "history join lacks uniquely identified target player " + player_id)
                feature_player_games[gid][player_id].update(groups)
    attempts = [attempt for gid in target_order for attempt in target_attempts[gid]]
    games = [target_games[gid] for gid in target_order]
    per_game = [target_counts[gid] for gid in target_order]
    game_dates = {gid: identities[gid]["game_date"] for gid in target_order}
    by_status = Counter(a["status"] for a in attempts)
    corpus_statuses = Counter(g["status"] for g in games)
    contributing = [g for g in per_game if g["known_attempts"] is not None]
    coverage = {
        "games": {
            "selected": len(games),
            "unselected": len(target_inventories - selected_ids),
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
            "schema_version": 2,
            "purpose": selection["purpose"],
            "corpora": resolved,
            "history_corpora": history_paths,
        },
        "purpose": selection["purpose"],
        "game_dates": game_dates,
        "games": games,
        "input_roots": sorted(input_roots),
        "preparation_identity": dict(PREPARATIONIDENTITY_FIELDS),
        "feature_games": feature_games,
        "feature_player_games": feature_player_games,
    }
