"""one saved-stream necessary calibration screen; neither disposition admits a model."""

import argparse
from collections import Counter
from datetime import date
import hashlib
import math
from pathlib import Path
import platform
import sys
import time

import numpy as np

from hockey_stats.artifacts import write_json
from hockey_stats.captures import InputContractError, strict_json
from hockey_stats.chance import CONTEXT_CATEGORIES, TYPES
from hockey_stats.chance_cli import identity, output_path, read_json
from hockey_stats.chance_data import MODEL_SHOT_TYPES
from hockey_stats.chance_features import PREPARATION_IDENTITY, stage_design
from hockey_stats.chance_evaluation import (
    PROBABILITY_SUMS, add_binary, binary_metrics, binary_record, finish_binary,
)
from hockey_stats.cli import Once
from chance_development import implementation, resources
from chance_review import (
    absolute_path, agrees, calendar_blocks, clean_implementation, digest,
    integer, linked_path, ratio_interval, require, validate_probability,
)


QUANTITIES = {
    "unblocked_conversion": ("candidate_r", "goal"),
    "all_attempt_recorded_context": ("candidate_all", "goal"),
    "marginal_unblocked": ("candidate_unblocked", "unblocked"),
}
STATUSES = ("eligible", "out_of_scope", "unavailable")
BIN_SUMS = ("count", "observed_positive_count", "predicted_probability_sum")
FROZEN_DIGESTS = {
    "completion": "8f4e098acb1b9b8ece3a989beb5e6a6d631d8ac32e3f7402923b59425d78080b",
    "comparison": "e2d825297f5dd5a02871595a101d4a458a1c0546742f1acb9c8068a9f51e5e3c",
    "composition": "d9c5f3773dfcb803cc7bcd3d41fd0c90025282247bfd3ffcc698eed13040a6d9",
    "attempts": "2830f700f4304c24da332cc34467670b9970f66f7d18de6791d8ca74754daca9",
}
RESAMPLING = dict(draws=2000, seed=3032026, generator="PCG64",
                  percentile_method="linear", calendar_days=[7, 14])
REMAINING_OBLIGATIONS = (
    "inherited_named_subgroups_and_tip_evidence", "comparator_inferiority",
    "spatial_adequacy", "origin_execution_sensitivity", "later_season_support",
)


def measured_resources(started):
    value = resources(started)
    if sys.platform != "darwin":
        value["peak_memory_bytes"] *= 1024
    return value


def calibration_fact(saved, margin):
    """retain the inherited order: decisive failure precedes support exclusions."""
    interval = saved["interval"]
    if interval is None:
        classification, reason = "insufficient", saved["missing_reason"]
    else:
        lower, upper = interval
        require(math.isfinite(lower) and math.isfinite(upper) and lower <= upper,
                "invalid calibration interval")
        if lower > margin or upper < -margin:
            classification, reason = "failure", "whole interval beyond margin"
        elif lower < -margin or upper > margin:
            classification, reason = "insufficient", "interval overlaps margin"
        elif saved["all_one_label"]:
            classification, reason = "insufficient", "all-one-label population"
        elif saved["contributing_games"] < 100:
            classification, reason = "insufficient", "fewer than 100 contributing games"
        else:
            classification, reason = "support", None
    return {
        key: saved[key]
        for key in (
            "estimate", "count", "contributing_games", "observed_positive_count",
            "interval", "undefined_draws", "all_one_label", "missing_reason",
        )
    } | {
        "margin": margin, "classification": classification, "criterion_reason": reason,
        "contributing_blocks": saved.get("contributing_blocks"),
        "selected_blocks": saved.get("selected_blocks"),
    }


def load_evidence(completion_path):
    """check completed diagnosis links; never reopen parents or the raw corpus."""
    completion_path = Path(completion_path).resolve(strict=True)
    completion = read_json(completion_path)
    purpose = completion["purpose"]
    require(purpose in ("research", "fixture_exercise"), "invalid diagnosis purpose")
    comparison_path = linked_path(completion["comparison"])
    composition_path = linked_path(completion["composition"])
    comparison, composition = read_json(comparison_path), read_json(composition_path)
    for document, kind, version in (
        (completion, "chance_conversion_diagnosis_completion", 1),
        (comparison, "chance_conversion_diagnosis", 1),
        (composition, "chance_conversion_composition", 2),
    ):
        require(type(document["schema_version"]) is int and document["schema_version"] == version
                and document["artifact_kind"] == kind and document["purpose"] == purpose
                and document["scientific_assessment"] == "not_performed",
                "current completed diagnosis kinds/schemas/purposes required")
    require(composition["preparation_identity"] == PREPARATION_IDENTITY,
            "composition preparation identity disagrees")
    design = composition["compatibility"]["stage_design"]
    require(design["stage"] == "r" and design == stage_design(
                "r", design["families"], core_layout=design["core_layout"],
                trait_assumptions=design["trait_assumptions"]),
            "composition conversion design disagrees")
    require(comparison["composition"] == completion["composition"]
            and comparison["attempts"] == completion["attempts"]
            and comparison["implementation"] == composition["implementation"],
            "diagnosis cross-links or execution identities disagree")
    require(all(comparison["resampling"][key] == value for key, value in RESAMPLING.items()),
            "saved diagnosis resampling changed")
    stream = absolute_path(completion["attempts"]["path"])
    digest(completion["attempts"]["sha256"])
    dates = comparison["game_dates"]
    training = composition["compatibility"]["training_game_dates"]
    for name, selected in (("assessment", dates), ("training", training)):
        require(isinstance(selected, dict) and bool(selected), f"missing {name} games")
        require(all(isinstance(gid, str) and len(gid) == 10 and gid.isdigit()
                    and isinstance(day, str) and date.fromisoformat(day).isoformat() == day
                    for gid, day in selected.items()), f"invalid {name} game identities/dates")
    require(list(dates) == sorted(dates, key=lambda gid: (dates[gid], gid)),
            "saved assessment game order is not chronological")
    require(not set(training) & set(dates)
            and min(dates.values()) > max(training.values()),
            "assessment must be disjoint and strictly later than training")
    require(set(comparison["probabilities"]) == set(QUANTITIES),
            "saved diagnosis probability quantities disagree")
    identities = dict(completion=identity(completion_path), comparison=completion["comparison"],
                      composition=completion["composition"], attempts=completion["attempts"])
    if purpose == "research":
        require(all(identities[name]["sha256"] == value for name, value in FROZEN_DIGESTS.items()),
                "frozen research diagnosis identity changed")
        clean_implementation(composition["implementation"])
        for value in composition["parent_implementations"].values():
            clean_implementation(value)
    return dict(
        completion=completion, comparison=comparison, composition=composition, stream=stream,
        identities=identities,
    )


def reconcile_metric(actual, saved, *, calibration=False):
    validate_probability(saved if calibration else
                         {field: saved[field] for field in ("outcome", *PROBABILITY_SUMS)},
                         actual["outcome"], compact=not calibration)
    for field in (*PROBABILITY_SUMS, "log_loss", "brier_score", "predicted_minus_observed_pp"):
        left, right = actual[field], saved[field]
        require(left is None and right is None or
                type(right) in (int, float) and left is not None and agrees(left, right),
                f"saved binary {field} disagrees")
    if calibration:
        for left, right in zip(actual["calibration"], saved["calibration"], strict=True):
            for field in (*BIN_SUMS, "predicted_rate", "observed_rate"):
                a, b = left[field], right[field]
                require(a is None and b is None or
                        type(b) in (int, float) and a is not None and agrees(a, b),
                        f"saved own-bin {field} disagrees")


def reconcile_counts(actual, saved, description):
    require(isinstance(saved, dict) and all(type(v) is int and v >= 0 for v in saved.values())
            and Counter(actual) == Counter(saved), f"{description} disagree")


def saved_descriptors(row):
    """check shared saved descriptors; return original/model type, month and recentness."""
    previous, groups, context = row["previous_event"], row["diagnostic_groups"], row["context"]
    require(isinstance(previous, dict) and isinstance(groups, dict) and isinstance(context, dict),
            "saved descriptors must be objects")
    recent = previous["status"]
    require(recent in ("none", "recent", "unavailable"), "invalid saved preceding-action status")
    original, model_type, month = row["shot_type"], row["model_shot_type"], row["game_date"][:7]
    require((original is None or isinstance(original, str))
            and model_type == MODEL_SHOT_TYPES.get(original),
            "saved original/model shot-type mapping disagrees")
    descriptors = dict(
        original_type=original, model_type=model_type, calendar_month=month,
        recent_context=recent, recent_kind=previous["kind"] if recent != "none" else None,
        recent_team=previous["owner_team_relation"] if recent != "none" else None,
        recent_delay=previous["time_gap_seconds"] if recent != "none" else None,
    )
    require(all(groups[field] == value for field, value in descriptors.items()),
            "saved diagnostic date/type/recent descriptors disagree")
    for field, previous_field in (
        ("recent_kind", "kind"), ("recent_team", "owner_team_relation"),
        ("recent_delay", "time_gap_seconds"),
    ):
        require(context[field] == (previous[previous_field] if recent == "recent" else None),
                "saved model context and preceding descriptor disagree")
    if recent == "recent":
        require(type(previous["time_gap_seconds"]) is int
                and previous["time_gap_seconds"] in CONTEXT_CATEGORIES["recent_delay"]
                and previous["owner_team_relation"] in CONTEXT_CATEGORIES["recent_team"]
                and all(type(previous[field]) in (int, float) and math.isfinite(previous[field])
                        for field in ("current_attack_x", "current_attack_y"))
                and (previous["same_shooter"] is None or type(previous["same_shooter"]) is bool),
                "saved recent descriptors are unsupported")
        recent_zone = "attacking" if previous["current_attack_x"] > 25 else "other"
        recent_shooter = None if previous["same_shooter"] is None else (
            "same" if previous["same_shooter"] else "different")
    else:
        recent_zone, recent_shooter = None, None
    require(context["recent_zone"] == recent_zone and context["recent_shooter"] == recent_shooter
            and groups["home_away"] == context["home_away"],
            "saved model context location/shooter/side descriptors disagree")
    predictor_groups = row["predictor_groups"]
    require(isinstance(predictor_groups, dict) and set(predictor_groups) == {
                "baseline", "revision", "historical_stronger", "improved_direct"}
            and all(set(predictor_groups[name]) == set(QUANTITIES)
                    for name in ("baseline", "revision"))
            and all(set(predictor_groups[name]) == {
                        "unblocked_conversion", "all_attempt_recorded_context"}
                    for name in ("historical_stronger", "improved_direct"))
            and all(all(part[field] == value for field, value in descriptors.items())
                    and part["home_away"] == groups["home_away"] and part["role"] == groups["role"]
                    for quantities in predictor_groups.values() for part in quantities.values()),
            "saved predictor descriptors disagree")
    if row["status"] == "eligible":
        require(recent in ("none", "recent") and model_type in TYPES
                and (recent != "recent" or previous["kind"] in CONTEXT_CATEGORIES["recent_kind"]),
                "eligible saved type/recent context must be supported")
    return original, model_type, month, recent


def reconstruct(loaded, *, diagnostic=None):
    """hash one pass; diagnostic sums are provisional until reconciliation returns."""
    comparison, stream = loaded["comparison"], loaded["stream"]
    dates = comparison["game_dates"]
    metrics = {q: binary_metrics(outcome=outcome) for q, (_, outcome) in QUANTITIES.items()}
    games = {
        gid: dict(game_id=gid, game_date=day, recognized_count=0, source_identity=None,
                  counts_by_status=Counter(), counts_by_reason=Counter(), goals_by_status=Counter(),
                  excluded_goals_by_reason=Counter(),
                  quantities={q: dict(metrics=binary_metrics(outcome=outcome), counts_by_status=Counter())
                              for q, (_, outcome) in QUANTITIES.items()})
        for gid, day in dates.items()
    }
    counts, reasons, goals, excluded_goals = Counter(), Counter(), Counter(), Counter()
    quantity_counts = {q: Counter() for q in QUANTITIES}
    order = {gid: i for i, gid in enumerate(dates)}
    previous_key = (-1, -1)
    hasher, byte_count = hashlib.sha256(), 0
    with stream.open("rb") as source:
        for line_number, body in enumerate(source, 1):
            hasher.update(body)
            byte_count += len(body)
            try:
                row = strict_json(body)
            except ValueError as error:
                raise InputContractError(f"{stream}:{line_number}: invalid prediction json") from error
            require(isinstance(row, dict) and type(row["schema_version"]) is int
                    and row["schema_version"] == 3, "schema-3 saved prediction row required")
            gid, index = row["game_id"], row["source_index"]
            require(gid in games and type(index) is int and index >= 0, "invalid recognized key")
            key = (order[gid], index)
            require(key > previous_key, "duplicate or unordered recognized key")
            previous_key = key
            require(row["game_date"] == dates[gid]
                    and row["season"] == gid[:4] + str(int(gid[:4]) + 1)
                    and (row["event_id"] is None or type(row["event_id"]) is int
                         and row["event_id"] >= 0), "saved date/season/event identity disagrees")
            reference = row["source_identity"]
            require(isinstance(reference, dict) and reference["kind"] == "game"
                    and isinstance(reference["path"], str) and Path(reference["path"]).is_absolute()
                    and Path(reference["path"]).name == gid + ".json", "invalid saved source identity")
            digest(reference["sha256"])
            game = games[gid]
            require(game["source_identity"] is None or game["source_identity"] == reference,
                    "source identity changed within a saved game")
            game["source_identity"] = reference
            status, excluded = row["status"], row["reasons"]
            require(row["source_status"] == status and row["source_reasons"] == excluded and
                    row["study_inclusion"] == ("included" if status == "eligible" else "source_excluded") and
                    not row["study_reasons"], "saved full-model source/study disposition changed")
            require(status in STATUSES and isinstance(excluded, list)
                    and row["classification"] in ("five_on_five", "other", "unresolved", "untimed")
                    and all(isinstance(reason, str) and reason for reason in excluded)
                    and len(set(excluded)) == len(excluded), "invalid saved disposition/reasons")
            require((status == "eligible" and not excluded and row["classification"] == "five_on_five")
                    or (status == "out_of_scope" and "outside_5v5" in excluded)
                    or (status == "unavailable" and bool(excluded) and "outside_5v5" not in excluded),
                    "saved disposition/classification/reasons disagree")
            require(type(row["blocked"]) is bool and type(row["goal"]) is bool
                    and not (row["blocked"] and row["goal"]), "invalid saved block/goal labels")
            counts[status] += 1
            reasons.update(excluded)
            goals[status] += row["goal"]
            game["recognized_count"] += 1
            game["counts_by_status"][status] += 1
            game["counts_by_reason"].update(excluded)
            game["goals_by_status"][status] += row["goal"]
            if row["goal"] and status != "eligible":
                excluded_goals.update(excluded)
                game["excluded_goals_by_reason"].update(excluded)
            predictions = row["predictions"]["revision"]
            require(set(predictions) == {field for field, _ in QUANTITIES.values()},
                    "revised prediction quantities disagree")
            records = {}
            for quantity, (field, outcome) in QUANTITIES.items():
                applicable = status == "eligible" and (quantity != "unblocked_conversion" or not row["blocked"])
                prediction_status = "predicted" if applicable else "not_applicable" if status == "eligible" else status
                quantity_counts[quantity][prediction_status] += 1
                part = game["quantities"][quantity]
                part["counts_by_status"][prediction_status] += 1
                value = predictions[field]
                if not applicable:
                    require(value is None, "inapplicable saved prediction must be null")
                    continue
                require(isinstance(value, dict) and set(value) == {"log_p", "log_not_p"},
                        "applicable saved complementary log probabilities required")
                positive = not row["blocked"] if outcome == "unblocked" else row["goal"]
                record = binary_record(positive, value["log_p"], value["log_not_p"])
                records[quantity] = record
                add_binary(metrics[quantity], record)
                add_binary(part["metrics"], record)
            if diagnostic is not None:
                diagnostic.consume(row, records)
    require(hasher.hexdigest() == loaded["identities"]["attempts"]["sha256"],
            "saved attempt stream digest mismatch")
    coverage = comparison["coverage"]
    attempts = coverage["attempts"]
    require(integer(coverage["games"]["selected"]) == len(dates)
            and integer(attempts["recognized_attempts"]) == sum(counts.values())
            and integer(attempts["known"]) == sum(counts.values())
            and integer(attempts["chance_2_eligible_attempts"]) == counts["eligible"]
            and integer(attempts["usable"]) == counts["eligible"]
            and integer(attempts["excluded"]) == counts["out_of_scope"] + counts["unavailable"],
            "recognized population/selected game coverage disagrees")
    reconcile_counts(counts, coverage["attempts_by_status"], "coverage dispositions")
    reconcile_counts(reasons, coverage["attempts_by_reason"], "coverage exclusions")
    reconcile_counts(goals, coverage["attempts"]["goals_by_status"], "coverage goal labels")
    reconcile_counts(excluded_goals, attempts["excluded_goals_by_reason"], "coverage excluded goals")
    require([row["game_id"] for row in coverage["per_game"]] == list(dates),
            "per-game coverage order disagrees")
    for game, saved in zip(games.values(), coverage["per_game"], strict=True):
        require(game["game_date"] == saved["game_date"]
                and game["recognized_count"] == integer(saved["recognized_attempts"])
                and game["recognized_count"] == integer(saved["known_attempts"])
                and game["counts_by_status"]["eligible"] == integer(saved["chance_2_eligible_attempts"]),
                "per-game recognized coverage disagrees")
        reconcile_counts(game["counts_by_status"], saved["attempts_by_status"], "per-game dispositions")
        reconcile_counts(game["counts_by_reason"], saved["attempts_by_reason"], "per-game exclusions")
        reconcile_counts(game["goals_by_status"], saved["goals_by_status"], "per-game goals")
        reconcile_counts(game["excluded_goals_by_reason"], saved["excluded_goals_by_reason"], "per-game excluded goals")
        for field in ("counts_by_status", "goals_by_status"):
            game[field] = {status: game[field][status] for status in STATUSES}
        game["counts_by_reason"] = dict(game["counts_by_reason"])
        game["excluded_goals_by_reason"] = dict(game["excluded_goals_by_reason"])
    for quantity, metric in metrics.items():
        saved = comparison["probabilities"][quantity]["own"]["revision"]
        finish_binary(metric)
        reconcile_metric(metric, saved["metrics"], calibration=True)
        reconcile_counts(quantity_counts[quantity], saved["counts_by_status"], "quantity dispositions")
        reconcile_counts(reasons, saved["counts_by_reason"], "quantity exclusions")
        require([row["game_id"] for row in saved["per_game"]] == list(dates),
                "saved quantity game order disagrees")
        for game, original in zip(games.values(), saved["per_game"], strict=True):
            part = game["quantities"][quantity]
            finish_binary(part["metrics"])
            reconcile_metric(part["metrics"], original["metrics"])
            reconcile_counts(part["counts_by_status"], original["counts_by_status"], "quantity game dispositions")
            part["counts_by_status"] = dict(part["counts_by_status"])
        for field in PROBABILITY_SUMS:
            require(agrees(math.fsum(g["quantities"][quantity]["metrics"][field] for g in games.values()),
                           metric[field]), "binary game sums disagree")
        for i, bucket in enumerate(metric["calibration"]):
            for field in BIN_SUMS:
                require(agrees(math.fsum(g["quantities"][quantity]["metrics"]["calibration"][i][field]
                                       for g in games.values()), bucket[field]), "own-bin game sums disagree")
        for field in BIN_SUMS:
            require(agrees(math.fsum(b[field] for b in metric["calibration"]), metric[field]),
                    "own-bin population sums disagree")
    for game in games.values():
        for part in game["quantities"].values():
            part["metrics"]["calibration"] = [
                {field: bucket[field] for field in BIN_SUMS}
                for bucket in part["metrics"]["calibration"]
            ]
    return dict(metrics=metrics, per_game=list(games.values()), attempts_bytes=byte_count,
                coverage=coverage)


def assess_quantities(metrics, per_game, game_dates):
    """assess all own bins; only required failures determine withholding."""
    require([row["game_id"] for row in per_game] == list(game_dates), "assessment game order disagrees")
    dates = list(game_dates.values())
    units = dict(games=None, calendar_7_day=calendar_blocks(dates, 7),
                 calendar_14_day=calendar_blocks(dates, 14))
    samples = {}
    for name, blocks in units.items():
        n = len(dates) if blocks is None else int(max(blocks)) + 1
        samples[name] = np.random.Generator(np.random.PCG64(RESAMPLING["seed"])).integers(
            0, n, size=(RESAMPLING["draws"], n))
    quantities, blocking = {}, []
    for quantity, total in metrics.items():
        overall_margin, bin_margin = (0.01, 0.03) if quantity == "marginal_unblocked" else (0.0025, 0.01)
        game_metrics = [row["quantities"][quantity]["metrics"] for row in per_game]
        criteria = []
        for index in (None, *range(20)):
            aggregate = total if index is None else total["calibration"][index]
            parts = game_metrics if index is None else [metric["calibration"][index] for metric in game_metrics]
            count, predicted = aggregate["count"], aggregate["predicted_probability_sum"]
            fraction = count / total["count"] if total["count"] else None
            mass = predicted / total["predicted_probability_sum"] if total["predicted_probability_sum"] else None
            trigger = index is not None and bool(count) and (
                fraction is not None and fraction >= 0.05 or mass is not None and mass >= 0.05)
            margin = overall_margin if index is None else bin_margin
            methods = {
                name: calibration_fact(ratio_interval(
                    [part["predicted_probability_sum"] - part["observed_positive_count"] for part in parts],
                    [part["count"] for part in parts], RESAMPLING["seed"],
                    observed=[part["observed_positive_count"] for part in parts],
                    blocks=blocks, samples=samples[name]), margin)
                for name, blocks in units.items()
            }
            criterion = dict(
                id=f"{quantity}/overall" if index is None else f"{quantity}/bin/{index}",
                quantity=quantity, kind="overall" if index is None else "bin", index=index,
                count=count, observed_positive_count=aggregate["observed_positive_count"],
                predicted_probability_sum=predicted, predicted_rate=predicted / count if count else None,
                observed_rate=aggregate["observed_positive_count"] / count if count else None,
                attempt_fraction=fraction, predicted_positive_mass_fraction=mass,
                consequential_now=trigger, represented=bool(count), required=index is None or trigger,
                required_reason="overall population" if index is None else
                "attempt share or predicted-positive-mass share at least 0.05" if trigger else
                "empty bin" if not count else "below both 0.05 share thresholds",
                margin=margin, methods=methods,
            )
            if index is not None:
                criterion.update(lower=aggregate["lower"], upper=aggregate["upper"],
                                 upper_inclusive=aggregate["upper_inclusive"])
            criteria.append(criterion)
            failed = [name for name, fact in methods.items() if fact["classification"] == "failure"]
            if criterion["required"] and failed:
                blocking.append(dict(id=criterion["id"], count=count, margin=margin,
                                     failed_methods=failed, methods=methods))
        quantities[quantity] = dict(metrics=total, overall=criteria[0], bins=criteria[1:])
    return quantities, blocking


def run(completion_path, protocol_path, output_value):
    started = time.monotonic()
    loaded = load_evidence(completion_path)
    protocol = Path(protocol_path).resolve(strict=True)
    loaded["identities"]["protocol"] = identity(protocol)
    output = output_path(output_value, [str(Path(ref["path"]).parent) for ref in loaded["identities"].values()])
    execution = implementation()
    execution.update(platform=platform.platform(), python_executable=sys.executable)
    purpose = loaded["completion"]["purpose"]
    if purpose == "research":
        clean_implementation(execution)
    pass_started = time.monotonic()
    reconstructed = reconstruct(loaded)
    pass_seconds = time.monotonic() - pass_started
    quantities, blocking = assess_quantities(reconstructed["metrics"], reconstructed["per_game"],
                                             loaded["comparison"]["game_dates"])
    input_bytes = reconstructed["attempts_bytes"] + sum(
        Path(ref["path"]).stat().st_size for name, ref in loaded["identities"].items() if name != "attempts")
    measured = dict(measured_resources(started), stream_passes=1, stream_pass_seconds=pass_seconds,
                    attempts_bytes_read=reconstructed["attempts_bytes"], input_bytes=input_bytes)
    composition = loaded["composition"]
    assessment = dict(
        schema_version=1, artifact_kind="chance_necessary_calibration_assessment", purpose=purpose,
        identities=loaded["identities"], implementation=execution,
        original_execution=dict(implementation=composition["implementation"],
                                parent_implementations=composition["parent_implementations"],
                                identities=composition["identities"]),
        population=dict(description=loaded["comparison"]["population_description"],
                        training_game_dates=composition["compatibility"]["training_game_dates"],
                        selected_games=len(loaded["comparison"]["game_dates"]),
                        recognized_rows=sum(reconstructed["coverage"]["attempts_by_status"].values())),
        game_dates=loaded["comparison"]["game_dates"], coverage=reconstructed["coverage"],
        per_game=reconstructed["per_game"], quantities=quantities,
        resampling=dict(RESAMPLING, interval_units="proportion", confidence=0.95,
                        undefined="null interval without redraw",
                        interpretation="pointwise pooled additive residuals; all selected games, empty calendar blocks and final partial blocks retained; intervals omit fitting, selection and origin-law uncertainty"),
        scope="retrospective necessary-condition screen; linked proper-loss and observable-spatial diagnosis evidence remains relevant; factual probability failure does not establish opportunity bias or physical-origin error",
        decision="withheld" if blocking else "further_assessment_required",
        blocking_criteria=blocking,
        remaining_obligations=[dict(id=name, status="not_assessed_by_this_slice")
                               for name in REMAINING_OBLIGATIONS], resources=measured,
    )
    output.mkdir()
    write_json(output / "assessment.json", assessment)
    assessment_identity = identity(output / "assessment.json")
    completion_resources = dict(measured, **measured_resources(started),
                                output_bytes_before_completion=(output / "assessment.json").stat().st_size)
    write_json(output / "completion.json", dict(
        schema_version=1, artifact_kind="chance_necessary_calibration_assessment_completion", purpose=purpose,
        identities=loaded["identities"], implementation=execution,
        assessment=assessment_identity, resources=completion_resources,
    ))
    return assessment


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for name in ("completion", "protocol", "out"):
        parser.add_argument(f"--{name}", required=True, action=Once)
    args = parser.parse_args()
    try:
        result = run(Path(args.completion), Path(args.protocol), args.out)
    except (InputContractError, OSError, KeyError, TypeError, ValueError, OverflowError) as error:
        print(f"saved calibration assessment failed: {error}", file=sys.stderr)
        return 1
    print(f"saved calibration assessment complete: {result['decision']}; {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
