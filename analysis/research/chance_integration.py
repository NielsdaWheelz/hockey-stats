"""one saved conversion substitution; diagnostic completion never admits a model."""

import argparse
from collections import Counter
from itertools import zip_longest
import json
import math
from pathlib import Path
import sys
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from hockey_stats.artifacts import write_json
from hockey_stats.captures import InputContractError
from hockey_stats.chance import (
    benchmark_actor_evidence, predict_attempt, predict_cells, prediction_context,
    score_attempt, validate_component, validate_model,
)
from hockey_stats.chance_cli import identity, output_path, read_json
from hockey_stats.chance_data import prepare
from hockey_stats.chance_evaluation import (
    PROBABILITY_SUMS, REGION_NAMES, add_binary, binary_metrics, compound_region_records,
    compound_regions, diagnostic_groups, finish_binary, summarize_component,
)
from hockey_stats.cli import Once
from chance_development import (
    QUANTITIES, implementation, prediction_check, prediction_row, resources, rows,
    source_identities,
)
from chance_review import (
    absolute_path, agrees, calendar_blocks, caption_layout, clean_implementation,
    linked_path, ratio_interval, require, scored_distribution,
)


FROZEN_DIGESTS = {
    "source_evidence": "cdaa37d12e8cbfa1d48d86871eb3ab77a49b9d0d8997ef99794151f40261f0e9",
    "component_screen": "59f6dd8011d496a9ed3ba9783059c8b333a3eadbbc354721a492a64dad4a462c",
    "anchor_model": "fff2c86b743fcbcae3a44848e9ae084341bcec00ecbd77797b0060c276a1549e",
    "conversion_component": "590e411694e52dacb42d9f57cd8935e3988a049fa5436da8314e31f28d5faf98",
}
PREDICTORS = {
    "unblocked_conversion": ("baseline", "revision", "historical_stronger"),
    "all_attempt_recorded_context": (
        "baseline", "revision", "historical_stronger", "improved_direct",
    ),
    "marginal_unblocked": ("baseline", "revision"),
}
NATIVE_FIELDS = {
    "unblocked_conversion": "candidate_r",
    "all_attempt_recorded_context": "candidate_all",
    "marginal_unblocked": "candidate_unblocked",
}
CONTEXTS = ("all", "none", "recent")


def load_evidence(path):
    """resolve only indexed current artifacts; source preparation happens once later."""
    path = Path(path).resolve(strict=True)
    evidence = read_json(path)
    require(
        set(evidence) == {"schema_version", "artifact_kind", "purpose", "protocol",
                          "source_evidence", "component_screen"}
        and type(evidence["schema_version"]) is int and evidence["schema_version"] == 1
        and evidence["artifact_kind"] == "chance_conversion_integration"
        and evidence["purpose"] in ("research", "fixture_exercise"),
        "schema-1 conversion integration evidence required",
    )
    purpose = evidence["purpose"]
    protocol_path = linked_path(evidence["protocol"])
    source_path = linked_path(evidence["source_evidence"])
    screen_path = linked_path(evidence["component_screen"])
    source = read_json(source_path)
    screen = read_json(screen_path)
    require(source["schema_version"] == 2 and source["purpose"] == purpose
            and source["benchmarks"] == dict.fromkeys(QUANTITIES, "stronger")
            and source["reference_score"] == "anchor"
            and source["resampling"] == dict(draws=2000, seed=3032026),
            "original development evidence or benchmark choices changed")
    original_protocol = identity(absolute_path(source["protocol"]))
    require(type(screen["schema_version"]) is int and screen["schema_version"] == 1
            and screen["artifact_kind"] == "chance_component_screen"
            and screen["purpose"] == purpose, "component screen identity mismatch")
    linked_path(screen["protocol"])
    study = read_json(linked_path(screen["study_inputs"]))
    require(type(study["schema_version"]) is int and study["schema_version"] == 1 and study["purpose"] == purpose
            and study["source_evidence"] == evidence["source_evidence"]
            and study["resampling"] == dict(draws=2000, seed=3032026, generator="PCG64",
                                             percentile_method="linear", calendar_days=[7, 14]),
            "screen study must bind the same original evidence and fixed resampling")
    if "specification" in study:
        linked_path(study["specification"])
    config = read_json(linked_path(study["config"]))
    selected = study["selections"]["development"]
    training_path = linked_path(selected["training"])
    assessment_path = linked_path(selected["assessment"])
    assessments = {entry["label"]: entry for entry in source["assessments"]}
    scores = {entry["label"]: entry for entry in source["scores"]}
    require(len(assessments) == len(source["assessments"])
            and len(scores) == len(source["scores"])
            and {"anchor", "stronger"} <= assessments.keys() and "anchor" in scores,
            "original index needs unique anchor/stronger assessments and anchor score")
    parents = {entry["label"]: entry for entry in study["models"]}
    require(len(parents) == len(study["models"]) and {"anchor", "stronger"} <= parents.keys(),
            "screen study needs unique original anchor/stronger parents")
    originals, models, resolved = {}, {}, {}
    for label in ("anchor", "stronger"):
        document_path = absolute_path(assessments[label]["path"])
        document = read_json(document_path)
        require(identity(document_path) == parents[label]["assessment"],
                "screen/original assessment identities differ")
        require(document["schema_version"] == 3 and document["purpose"] == purpose
                and document["scientific_assessment"] == "not_performed",
                "original native assessment schema/purpose mismatch")
        require(document["model"] == parents[label]["model"],
                "screen/original model identities differ")
        model = validate_model(read_json(linked_path(document["model"])))
        require(model["purpose"] == purpose, "native model purpose cannot be relabeled")
        if purpose == "research":
            clean_implementation(model["implementation"])
            clean_implementation(document["implementation"])
        require(document["geometry"] == model["grid"]
                and document["reference"] == model["reference"]
                and document["reference_season"] == model["reference_season"],
                "native assessment/model grid or reference mismatch")
        training = model["training_game_dates"]
        require(not set(training) & set(document["game_dates"])
                and document["game_dates"]
                and min(document["game_dates"].values()) > max(training.values()),
                "assessment must be disjoint and strictly later than all training")
        training_ref = next(v for v in model["inputs"] if v["kind"] == "selection")
        require(training_ref["sha256"] == selected["training"]["sha256"],
                "screen training does not bind the original parent")
        if label == "anchor":
            require(model["config_identity"]["sha256"] == study["config"]["sha256"]
                    and model["config"] == config, "screen config does not bind the original anchor")
        if purpose == "research":
            require(training_ref["path"] == str(training_path), "research training identity changed")
            if label == "anchor":
                require(model["config_identity"] == study["config"], "research anchor config identity changed")
        if originals:
            for field in ("selection", "inputs", "game_dates", "coverage", "prediction_definitions"):
                require(document[field] == originals["anchor"][field],
                        f"original assessments disagree on {field}")
            for field in ("inputs", "selection", "training_game_dates"):
                require(model[field] == models["anchor"][field],
                        f"original model training {field} changed")
        originals[label] = document
        models[label] = model
        resolved[f"{label}_assessment"] = identity(document_path)
        resolved[f"{label}_model"] = document["model"]
    anchor = models["anchor"]
    original = originals["anchor"]
    require(next(v["sha256"] for v in original["inputs"] if v["kind"] == "selection")
            == selected["assessment"]["sha256"], "original assessment selection changed")
    score_path = absolute_path(scores["anchor"]["path"])
    score = read_json(score_path)
    require(score["schema_version"] == 2 and score["purpose"] == purpose
            and score["scientific_assessment"] == "not_performed"
            and score["quantity"] == "reference_opportunity_value"
            and score["units"] == "expected_goals" and score["model"] == original["model"],
            "original anchor score binding mismatch")
    for field in ("inputs", "selection", "game_dates", "coverage", "geometry", "reference", "reference_season"):
        require(score[field] == original[field], f"anchor score/assessment {field} mismatch")
    if purpose == "research":
        clean_implementation(score["implementation"])
    score_stream = linked_path(score["attempts"])
    resolved.update(anchor_score=identity(score_path), anchor_score_stream=score["attempts"])
    components, evaluations, streams = {}, {}, {}
    for quantity in QUANTITIES:
        cells = [cell for cell in screen["cells"]
                 if (cell["window"], cell["recipe"], cell["quantity"])
                 == ("development", "context_interactions", quantity)]
        require(len(cells) == 1, "screen must select exactly one declared interaction cell")
        cell = cells[0]
        require(cell["status"] == "fitted" and cell["training_selection"] == selected["training"]
                and cell["assessment_selection"] == selected["assessment"],
                "selected screen cell must retain original training/assessment")
        component = validate_component(read_json(linked_path(cell["component"])))
        require(component["purpose"] == purpose and component["quantity"] == quantity
                and component["feature_set"] == "recent_interactions"
                and component["protocol_identity"] == screen["protocol"]
                and component["config_identity"]["sha256"] == study["config"]["sha256"],
                "selected component kind/features/protocol/config mismatch")
        for field in ("inputs", "selection", "training_game_dates", "training_eligible_attempts"):
            expected = (anchor["coverage"]["attempts_by_status"]["eligible"]
                        if field == "training_eligible_attempts" else anchor[field])
            require(component[field] == expected, f"component/anchor training {field} mismatch")
        evaluation = read_json(linked_path(cell["evaluation"]))
        require(type(evaluation["schema_version"]) is int and evaluation["schema_version"] == 1
                and evaluation["artifact_kind"] == "chance_component_evaluation"
                and evaluation["purpose"] == purpose and evaluation["quantity"] == quantity
                and evaluation["scientific_assessment"] == "not_performed"
                and evaluation["component"] == cell["component"]
                and evaluation["protocol"] == screen["protocol"]
                and evaluation["selection_identity"] == selected["assessment"],
                "selected component evaluation binding mismatch")
        for field in ("selection", "inputs", "game_dates", "coverage"):
            require(evaluation[field] == original[field], f"component evaluation {field} changed")
        diagnostics = read_json(linked_path(cell["diagnostics"]))
        require(type(diagnostics["schema_version"]) is int and diagnostics["schema_version"] == 1
                and diagnostics["artifact_kind"] == "chance_component_fit"
                and diagnostics["status"] == "fitted" and diagnostics["purpose"] == purpose
                and diagnostics["quantity"] == quantity
                and diagnostics["feature_set"] == "recent_interactions"
                and diagnostics["diagnostics"] == component["diagnostics"],
                "selected component fit diagnostics mismatch")
        for field in ("implementation", "inputs", "selection", "config_identity", "protocol_identity",
                      "training_game_dates", "training_game_ids", "training_dates"):
            require(diagnostics[field] == component[field], f"selected fit/component {field} mismatch")
        if purpose == "research":
            clean_implementation(component["implementation"])
            clean_implementation(evaluation["implementation"])
            clean_implementation(diagnostics["implementation"])
        components[quantity] = component
        evaluations[quantity] = evaluation
        streams[quantity] = linked_path(evaluation["attempts"])
        name = "conversion" if quantity == "unblocked_conversion" else "improved_direct"
        resolved.update({f"{name}_component": cell["component"],
                         f"{name}_evaluation": cell["evaluation"],
                         f"{name}_stream": evaluation["attempts"],
                         f"{name}_fit": cell["diagnostics"]})
    if purpose == "research":
        for field, digest in FROZEN_DIGESTS.items():
            reference = evidence[field] if field in evidence else resolved[field]
            require(reference["sha256"] == digest, f"frozen research {field} digest changed")
        require(len(anchor["training_game_dates"]) == 1912
                and max(anchor["training_game_dates"].values()) == "2024-12-31"
                and anchor["coverage"]["attempts_by_status"]["eligible"] == 181147
                and sum(v["total"] for v in components["unblocked_conversion"]["layout"]["shooter_counts"].values()) == 128679
                and len(original["game_dates"]) == 712
                and original["reference_season"] == "20242025",
                "frozen research population/cutoff/reference changed")
    # this validates the complete replacement against the anchor without fitting.
    baseline_context = prediction_context(anchor)
    revision_context = prediction_context(anchor, conversion=components["unblocked_conversion"])
    resolved.update(evidence=identity(path), protocol=evidence["protocol"],
                    source_evidence=evidence["source_evidence"], original_protocol=original_protocol,
                    component_screen=evidence["component_screen"], screen_protocol=screen["protocol"],
                    study_inputs=screen["study_inputs"], training_selection=selected["training"],
                    assessment_selection=selected["assessment"], config=study["config"])
    return dict(evidence=evidence, resolved=resolved, models=models, originals=originals,
                score=score, score_stream=score_stream, components=components,
                evaluations=evaluations, streams=streams, assessment_path=assessment_path,
                baseline_context=baseline_context, revision_context=revision_context)


def factual_rows(path, quantity, predictor, *, paired=False, cohort=False):
    """quantity rows preserve source dispositions; anchor owns paired support groups."""
    field = NATIVE_FIELDS[quantity]
    if predictor == "historical_stronger":
        field = "benchmark_r" if quantity == "unblocked_conversion" else "benchmark_all"
    elif predictor == "improved_direct":
        field = "benchmark_all"
    for row in rows(path):
        if cohort and not row["anchor_cohort"]:
            continue
        value = row["predictions"][predictor][field]
        applicable = quantity != "unblocked_conversion" or not row["blocked"]
        groups = row["predictor_groups"]["baseline" if paired else predictor][quantity]
        yield dict(row, diagnostic_groups=groups, applicable=applicable,
                   status="predicted" if value is not None else
                   "not_applicable" if row["status"] == "eligible" else row["status"],
                   observed=int(not row["blocked"] if quantity == "marginal_unblocked" else row["goal"])
                   if value is not None else None,
                   log_p=value["log_p"] if value else None,
                   log_not_p=value["log_not_p"] if value else None)


def paired_deltas(before, after, game_dates, samples):
    """pooled paired deltas reuse whole-game and calendar-block ratio arithmetic."""
    games = list(game_dates)
    require([row["game_id"] for row in before["per_game"]] == games
            == [row["game_id"] for row in after["per_game"]], "paired metric game order changed")
    denominators = [row["metrics"]["count"] for row in before["per_game"]]
    require(denominators == [row["metrics"]["count"] for row in after["per_game"]],
            "paired metric denominators changed")
    units = dict(games=None, calendar_7_day=calendar_blocks(list(game_dates.values()), 7),
                 calendar_14_day=calendar_blocks(list(game_dates.values()), 14))
    return {
        metric: {name: ratio_interval(
            [scale * (right["metrics"][field] - left["metrics"][field])
             for left, right in zip(before["per_game"], after["per_game"], strict=True)],
            denominators, 3032026, blocks=blocks, samples=samples[name])
                 for name, blocks in units.items()}
        for metric, field, scale in (("log_loss", "log_loss_sum", 1),
                                     ("brier_score", "brier_score_sum", 1),
                                     ("predicted_minus_observed_pp", "predicted_probability_sum", 100))
    }


def pair_component(saved, row, quantity, reference):
    """current formats pair by semantic disposition, never literal status spelling."""
    prediction_check(saved)
    for field in ("game_id", "source_index", "event_id", "game_date", "season",
                  "source_identity", "reasons", "blocked", "goal"):
        require(saved[field] == row[field], f"saved component {field} disagrees with prepared evidence")
    applicable = quantity != "unblocked_conversion" or not row["blocked"]
    status = ("predicted" if applicable else "not_applicable") if row["status"] == "eligible" else row["status"]
    require(saved["status"] == status and saved["applicable"] == applicable
            and saved["quantity"] == quantity and saved["component"] == reference,
            "saved component semantic disposition or identity mismatch")
    groups = {key: value for key, value in saved["diagnostic_groups"].items()
              if not key.startswith("actor_support:")}
    require(groups == row["diagnostic_groups"], "saved component source-context descriptors changed")


def run(evidence_path, output_value):
    started = time.monotonic()
    loaded = load_evidence(evidence_path)
    evidence, resolved = loaded["evidence"], loaded["resolved"]
    purpose = evidence["purpose"]
    anchor, stronger = loaded["models"]["anchor"], loaded["models"]["stronger"]
    original = loaded["originals"]["anchor"]
    prepared = prepare(loaded["assessment_path"])
    require(prepared["purpose"] == purpose, "assessment selection purpose changed")
    for field in ("selection", "inputs", "game_dates", "coverage"):
        require(prepared[field] == original[field], f"prepared original assessment {field} changed")
    if purpose == "research":
        counts = Counter(attempt["status"] for attempt in prepared["attempts"])
        require(len(prepared["attempts"]) == 85317
                and counts == Counter(eligible=68775, out_of_scope=16270, unavailable=272)
                and sum(not a["blocked"] for a in prepared["attempts"] if a["status"] == "eligible") == 49014
                and sum(a["goal"] for a in prepared["attempts"] if a["status"] == "eligible") == 2804,
                "frozen research assessment counts changed")
    roots = prepared["input_roots"] + [str(Path(ref["path"]).parent) for ref in resolved.values()]
    roots.extend(str(Path(ref["path"]).parent) for ref in anchor["inputs"])
    if purpose == "research":
        roots.extend(str(Path(evidence[field]["path"]).parent.parent)
                     for field in ("source_evidence", "component_screen"))
    output = output_path(output_value, roots)
    output.mkdir()
    execution = implementation()
    if purpose == "research":
        clean_implementation(execution)
    composition = dict(
        schema_version=1, artifact_kind="chance_conversion_composition", purpose=purpose,
        implementation=execution, identities=resolved,
        parent_implementations=dict(
            anchor_model=anchor["implementation"],
            anchor_assessment=original["implementation"], anchor_score=loaded["score"]["implementation"],
            conversion=loaded["components"]["unblocked_conversion"]["implementation"],
            conversion_evaluation=loaded["evaluations"]["unblocked_conversion"]["implementation"],
            historical_stronger=stronger["implementation"],
            improved_direct=loaded["components"]["all_attempt_recorded_context"]["implementation"],
        ),
        compatibility=dict(
            retained=["origin", "avoidance", "forward_kernel", "joint_reference"],
            replaced="complete conversion layout and coefficients",
            feature_set="recent_interactions", training_game_dates=anchor["training_game_dates"],
            training_eligible_attempts=anchor["coverage"]["attempts_by_status"]["eligible"],
            conversion_training_attempts=sum(v["total"] for v in anchor["stages"]["r"]["shooter_counts"].values()),
            config=anchor["config_identity"], reference_season=anchor["reference_season"],
            checked=["training identities/selection/dates/counts", "config", "seasons/grid",
                     "category orders", "actor identities/support"],
        ), scientific_assessment="not_performed",
    )
    write_json(output / "composition.json", composition)
    contexts = dict(baseline=loaded["baseline_context"], revision=loaded["revision_context"])
    stronger_context = prediction_context(stronger)
    centers = np.asarray(anchor["grid"]["centers"])
    cell_regions = compound_regions(centers)
    game_dates = prepared["game_dates"]
    sources = source_identities(prepared)
    region_games = {
        predictor: {quantity: {context: {
            gid: [binary_metrics(calibration=False, outcome=quantity) for _ in REGION_NAMES]
            for gid in game_dates} for context in CONTEXTS}
                    for quantity in ("unblocked", "goal")}
        for predictor in ("baseline", "revision")
    }
    opportunity = {
        label: dict(count=0, baseline_total=0.0, revision_total=0.0,
                    absolute_change_sum=0.0, max_absolute_event_value_change=0.0,
                    baseline_cell_mass=np.zeros(len(centers)), revision_cell_mass=np.zeros(len(centers)))
        for label in ("blocked", "unblocked")
    }
    maxima = {}

    def check(name, before, after):
        difference = float(np.max(np.abs(np.asarray(before) - np.asarray(after))))
        require(math.isfinite(difference) and difference <= 1e-12, f"{name} invariant failed: {difference}")
        maxima[name] = max(maxima.get(name, 0.0), difference)

    score_counts, score_reasons, score_origins = Counter(), Counter(), Counter()
    score_games = {gid: Counter() for gid in game_dates}
    seen = set()
    stream = output / "attempts.jsonl"
    pass_started = time.monotonic()
    paired_inputs = zip_longest(
        prepared["attempts"], rows(loaded["score_stream"]),
        rows(loaded["streams"]["unblocked_conversion"]),
        rows(loaded["streams"]["all_attempt_recorded_context"]),
    )
    with stream.open("x", encoding="utf-8") as destination:
        for attempt, score, conversion, direct in paired_inputs:
            require(all(value is not None for value in (attempt, score, conversion, direct)),
                    "complete recognized stream lengths disagree")
            key = attempt["game_id"], attempt["source_index"]
            require(key not in seen, "duplicate recognized attempt key")
            seen.add(key)
            expected_status = "valued" if attempt["status"] == "eligible" else attempt["status"]
            require(score["schema_version"] == 2 and score["status"] == expected_status,
                    "native score semantic disposition disagrees")
            for field, value in attempt.items():
                if field not in ("status", "source_event"):
                    require(score[field] == value, f"native score prepared {field} changed")
            score_counts[expected_status] += 1
            score_reasons.update(score["reasons"])
            score_games[attempt["game_id"]][expected_status] += 1
            row = prediction_row(attempt, prepared, sources)
            row.update(
                diagnostic_groups=diagnostic_groups(attempt, row["game_date"], {}),
                context=attempt["context"], previous_event=attempt["previous_event"],
                shot_type=attempt["shot_type"], model_shot_type=attempt["model_shot_type"],
                classification=attempt["classification"],
                predictions={name: dict.fromkeys(
                    ("candidate_r", "candidate_all", "candidate_unblocked")
                    if name in contexts else ("benchmark_r", "benchmark_all")
                    if name == "historical_stronger" else ("benchmark_all",))
                             for name in ("baseline", "revision", "historical_stronger", "improved_direct")},
                predictor_groups={}, stage_evidence=dict.fromkeys(contexts),
                region_probabilities=dict.fromkeys(contexts), proxy_cell_id=None,
                opportunity=dict.fromkeys(contexts), anchor_cohort=False, improved_direct_evidence=None,
            )
            for name in row["predictions"]:
                row["predictor_groups"][name] = {}
                for quantity in (PREDICTORS if name in contexts else QUANTITIES):
                    empty = ({"u": {"shooter": dict(basis=None)},
                              "r": {"shooter": dict(basis=None), "goalie": dict(basis=None)}}
                             if quantity == "all_attempt_recorded_context" and name in contexts else
                             {"shooter": dict(basis=None)} if quantity == "marginal_unblocked" else
                             {"shooter": dict(basis=None), "goalie": dict(basis=None)})
                    row["predictor_groups"][name][quantity] = diagnostic_groups(attempt, row["game_date"], empty)
            for quantity, saved in (("unblocked_conversion", conversion),
                                    ("all_attempt_recorded_context", direct)):
                reference = resolved["conversion_component" if quantity == "unblocked_conversion"
                                     else "improved_direct_component"]
                pair_component(saved, row, quantity, reference)
            if attempt["status"] == "eligible":
                recent = attempt["previous_event"]["status"]
                require(recent in ("none", "recent"), "eligible preceding-action context must be supported")
                cells = {name: predict_cells(anchor, attempt, context) for name, context in contexts.items()}
                predictions = {name: predict_attempt(anchor, attempt, context, cells=cells[name])
                               for name, context in contexts.items()}
                for field in ("log_pi", "log_u", "log_not_u"):
                    check(f"unchanged_{field}", cells["baseline"][field], cells["revision"][field])
                check("unchanged_origin_posterior", predictions["baseline"]["origin_weights"],
                      predictions["revision"]["origin_weights"])
                for field in ("log_p", "log_not_p"):
                    check(f"unchanged_marginal_unblocked_{field}",
                          predictions["baseline"]["candidate_unblocked"][field],
                          predictions["revision"]["candidate_unblocked"][field])
                check("origin_normalization", predictions["baseline"]["origin_weights"].sum(), 1)
                row["proxy_cell_id"] = None if attempt["blocked"] else cells["baseline"]["cell_id"]
                records = {name: compound_region_records(attempt, cell_regions, terms)
                           for name, terms in cells.items()}
                check("unchanged_regional_unblocked", [r["predicted_probability_sum"] for r in records["baseline"]["unblocked"]],
                      [r["predicted_probability_sum"] for r in records["revision"]["unblocked"]])
                for name in contexts:
                    row["predictions"][name] = {field: predictions[name][field] for field in NATIVE_FIELDS.values()}
                    row["stage_evidence"][name] = {field: cells[name][field] for field in (
                        "stage_actor_evidence", "stage_season_basis", "stage_state_season")}
                    row["region_probabilities"][name] = {}
                    for quantity in ("unblocked", "goal"):
                        row["region_probabilities"][name][quantity] = [r["predicted_probability_sum"]
                                                                      for r in records[name][quantity]]
                        native = "candidate_unblocked" if quantity == "unblocked" else "candidate_all"
                        check(f"{name}_{quantity}_region_partition",
                              sum(row["region_probabilities"][name][quantity]),
                              math.exp(predictions[name][native]["log_p"]))
                        require(sum(r["observed_positive_count"] for r in records[name][quantity])
                                == int(not attempt["blocked"] if quantity == "unblocked" else attempt["goal"]),
                                "compound regional outcome labels do not partition")
                        for context in ("all", recent):
                            for target, record in zip(region_games[name][quantity][context][row["game_id"]],
                                                      records[name][quantity], strict=True):
                                add_binary(target, record)
                    for quantity in PREDICTORS:
                        actors = predictions[name]["actor_evidence"]
                        selected_actors = (actors["r"] if quantity == "unblocked_conversion" else
                                           actors["u"] if quantity == "marginal_unblocked" else actors)
                        if quantity != "unblocked_conversion" or not attempt["blocked"]:
                            row["predictor_groups"][name][quantity] = diagnostic_groups(
                                attempt, row["game_date"], selected_actors)
                historical = predict_attempt(stronger, attempt, stronger_context)
                historical_actors = benchmark_actor_evidence(stronger, attempt, historical["state_season"])
                for quantity in QUANTITIES:
                    if quantity == "unblocked_conversion" and attempt["blocked"]:
                        continue
                    field = "benchmark_r" if quantity == "unblocked_conversion" else "benchmark_all"
                    row["predictions"]["historical_stronger"][field] = historical[field]
                    row["predictor_groups"]["historical_stronger"][quantity] = diagnostic_groups(
                        attempt, row["game_date"], historical_actors[field])
                row["predictions"]["improved_direct"]["benchmark_all"] = {
                    field: direct[field] for field in ("log_p", "log_not_p")}
                row["predictor_groups"]["improved_direct"]["all_attempt_recorded_context"] = direct["diagnostic_groups"]
                row["improved_direct_evidence"] = {field: direct[field] for field in (
                    "season_basis", "state_season", "actor_evidence")}
                if not attempt["blocked"]:
                    for field in ("log_p", "log_not_p"):
                        check(f"saved_revised_conversion_{field}", conversion[field],
                              predictions["revision"]["candidate_r"][field])
                    require(conversion["actor_evidence"] == cells["revision"]["stage_actor_evidence"]["r"]
                            and conversion["season_basis"] == cells["revision"]["stage_season_basis"]["r"]
                            and conversion["state_season"] == cells["revision"]["stage_state_season"]["r"],
                            "saved conversion selected actor/season semantics changed")
                row["anchor_cohort"] = .10 <= math.exp(predictions["baseline"]["candidate_all"]["log_p"]) < .15
                weights = predictions["baseline"]["origin_weights"]
                masses = {}
                for name, context in contexts.items():
                    value = score_attempt(anchor, attempt, context, prediction=predictions[name])
                    _, masses[name], row["opportunity"][name] = scored_distribution(
                        dict(attempt, **value), len(centers))
                    check(f"{name}_opportunity_conservation", masses[name].sum(), row["opportunity"][name])
                saved_weights, saved_mass, saved_value = scored_distribution(score, len(centers))
                check("saved_anchor_posterior", weights, saved_weights)
                check("saved_anchor_cell_opportunity", masses["baseline"], saved_mass)
                check("saved_anchor_value", row["opportunity"]["baseline"], saved_value)
                require(score["actor_evidence"] == predictions["baseline"]["actor_evidence"]
                        and score["season_basis"] == predictions["baseline"]["season_basis"]
                        and score["state_season"] == predictions["baseline"]["state_season"],
                        "native score actor/season semantics changed")
                score_origins[score["origin_basis"]] += 1
                values = opportunity["blocked" if attempt["blocked"] else "unblocked"]
                change = row["opportunity"]["revision"] - row["opportunity"]["baseline"]
                values["count"] += 1
                values["baseline_total"] += row["opportunity"]["baseline"]
                values["revision_total"] += row["opportunity"]["revision"]
                values["absolute_change_sum"] += abs(change)
                values["max_absolute_event_value_change"] = max(values["max_absolute_event_value_change"], abs(change))
                for name in contexts:
                    values[f"{name}_cell_mass"] += masses[name]
            else:
                require(all(score[field] is None for field in (
                    "reference_opportunity_value", "origin_distribution", "origin_basis",
                    "actor_evidence", "season_basis", "state_season")),
                    "inapplicable native score predictions must be null")
            destination.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")
    numerical_seconds = time.monotonic() - pass_started
    original_score = loaded["score"]
    require(dict(score_reasons) == original_score["counts_by_reason"]
            and dict(score_origins) == original_score["counts_by_origin_basis"]
            and {s: score_counts[s] for s in ("valued", "out_of_scope", "unavailable")}
            == original_score["counts_by_status"]
            and {gid: {s: counts[s] for s in ("valued", "out_of_scope", "unavailable")}
                 for gid, counts in score_games.items()} == original_score["per_game"],
            "complete native score counts/reasons/origins/per-game accounting changed")
    samples = {}
    for name, blocks in dict(games=None, calendar_7_day=calendar_blocks(list(game_dates.values()), 7),
                             calendar_14_day=calendar_blocks(list(game_dates.values()), 14)).items():
        n = len(game_dates) if blocks is None else int(max(blocks)) + 1
        samples[name] = np.random.Generator(np.random.PCG64(3032026)).integers(0, n, size=(2000, n))
    probabilities, cohort = {}, {}
    for quantity, predictors in PREDICTORS.items():
        outcome = "unblocked" if quantity == "marginal_unblocked" else "goal"
        own = {name: summarize_component(factual_rows(stream, quantity, name), game_dates, outcome=outcome)
               for name in predictors}
        expected = original["metrics"][quantity][NATIVE_FIELDS[quantity]]
        require(all(agrees(own["baseline"]["metrics"][field], expected[field]) for field in PROBABILITY_SUMS),
                "baseline native factual aggregate does not reconcile")
        for actual, saved in zip(own["baseline"]["per_game"], original["per_game"], strict=True):
            require(actual["game_id"] == saved["game_id"] and all(
                agrees(actual["metrics"][field], saved["metrics"][quantity][NATIVE_FIELDS[quantity]][field])
                for field in PROBABILITY_SUMS), "baseline native factual game sums do not reconcile")
        if quantity in QUANTITIES:
            field = "benchmark_r" if quantity == "unblocked_conversion" else "benchmark_all"
            expected = loaded["originals"]["stronger"]["metrics"][quantity][field]
            require(all(agrees(own["historical_stronger"]["metrics"][key], expected[key]) for key in PROBABILITY_SUMS),
                    "historical stronger scalar benchmark does not reconcile")
            selected_predictor = "revision" if quantity == "unblocked_conversion" else "improved_direct"
            saved = loaded["evaluations"][quantity]
            actual = own[selected_predictor]
            require(all(agrees(actual["metrics"][field], saved["metrics"][field]) for field in PROBABILITY_SUMS)
                    and actual["counts_by_status"] == saved["counts_by_status"]
                    and actual["counts_by_reason"] == saved["counts_by_reason"],
                    "saved component factual/accounting summary does not reconcile")
            for before, after in zip(actual["per_game"], saved["per_game"], strict=True):
                require(before["game_id"] == after["game_id"] and all(
                    agrees(before["metrics"][field], after["metrics"][field]) for field in PROBABILITY_SUMS),
                    "saved component per-game factual sums do not reconcile")
        paired = {name: summarize_component(factual_rows(stream, quantity, name, paired=True),
                                           game_dates, outcome=outcome)
                  for name in predictors if name != "baseline"}
        for after in paired.values():
            require(all(after["metrics"][field] == own["baseline"]["metrics"][field]
                        for field in ("count", "observed_positive_count")), "paired factual populations changed")
        probabilities[quantity] = dict(
            own=own, paired_groups={name: summary["groups"] for name, summary in paired.items()},
            paired_delta={name: paired_deltas(own["baseline"], summary, game_dates, samples)
                          for name, summary in paired.items()},
            paired_group_definition="anchor defines actor-support memberships; revised support retained in own groups and stage evidence; each predictor owns its bins",
        )
        cohort[quantity] = {
            name: summarize_component(factual_rows(stream, quantity, name, paired=True, cohort=True),
                                      game_dates, outcome=outcome) for name in predictors}
        # per-game bootstrap units need additive sums, not duplicated own-bin arrays.
        for summary in list(own.values()) + list(cohort[quantity].values()):
            for game in summary["per_game"]:
                game["metrics"].pop("calibration")
    regional = {name: {quantity: {} for quantity in ("unblocked", "goal")} for name in contexts}
    for name in contexts:
        for quantity in ("unblocked", "goal"):
            for context in CONTEXTS:
                records = []
                games = region_games[name][quantity][context]
                for region, label in enumerate(REGION_NAMES):
                    record = binary_metrics(calibration=False, outcome=quantity)
                    per_game = []
                    for gid in game_dates:
                        metric = games[gid][region]
                        add_binary(record, metric)
                        per_game.append(dict(game_id=gid, **metric))
                    finish_binary(record)
                    record.update(quantity=quantity, region=label, context=context, per_game=per_game)
                    record["residual_interval"] = ratio_interval(
                        [100 * (r["predicted_probability_sum"] - r["observed_positive_count"]) for r in per_game],
                        [r["count"] for r in per_game], 3032026,
                        observed=[r["observed_positive_count"] for r in per_game], samples=samples["games"])
                    records.append(record)
                regional[name][quantity][context] = records
            for index in range(len(REGION_NAMES)):
                total = regional[name][quantity]["all"][index]
                parts = [regional[name][quantity][context][index] for context in ("none", "recent")]
                require(all(agrees(sum(p[field] for p in parts), total[field]) for field in PROBABILITY_SUMS),
                        "none/recent regional sums do not reconcile to all")
    for label, values in opportunity.items():
        values["signed_total_change"] = values["revision_total"] - values["baseline_total"]
        absolute_change = values.pop("absolute_change_sum")
        values["mean_absolute_event_value_change"] = absolute_change / values["count"] if values["count"] else None
        if not values["count"]:
            values["max_absolute_event_value_change"] = None
        for name in contexts:
            require(agrees(float(values[f"{name}_cell_mass"].sum()), values[f"{name}_total"]),
                    "opportunity aggregate cell masses do not conserve totals")
        change = values["revision_cell_mass"] - values["baseline_cell_mass"]
        values["cell_mass_difference"] = change.tolist()
        values["region_mass_difference"] = [float(change[cell_regions == i].sum()) for i in range(len(REGION_NAMES))]
        require(agrees(sum(values["region_mass_difference"]), values["signed_total_change"]),
                "opportunity regional changes do not conserve total change")
        for name in contexts:
            values[f"{name}_cell_mass"] = values[f"{name}_cell_mass"].tolist()
    first, last = min(game_dates.values()), max(game_dates.values())
    population = (f"{purpose.replace('_', ' ')}: {len(game_dates)} assessment games, {first}–{last}; "
                  f"training through {max(anchor['training_game_dates'].values())}; "
                  f"{score_counts['valued']:,} eligible attempts; native 5-foot rink grid.")
    comparison = dict(
        schema_version=1, artifact_kind="chance_conversion_diagnosis", purpose=purpose,
        implementation=execution, composition=identity(output / "composition.json"),
        attempts=identity(stream), coverage=prepared["coverage"], game_dates=game_dates,
        population_description=population, geometry=anchor["grid"],
        benchmarks=dict(historical_stronger_model=resolved["stronger_model"],
                        historical_stronger_assessment=resolved["stronger_assessment"],
                        improved_direct_component=resolved["improved_direct_component"],
                        improved_direct_evaluation=resolved["improved_direct_evaluation"]),
        probabilities=probabilities,
        anchor_cohort=dict(definition="baseline candidate_all probability in [0.10, 0.15); identical rows for all predictors, separate from own bins", summaries=cohort),
        regions=dict(names=list(REGION_NAMES), contexts=list(CONTEXTS), cell_regions=cell_regions.tolist(),
                     definitions=["behind_goal: x > 89", "outside_attacking_zone: x <= 25",
                                  "remaining cells: distance to (89,0) in [0,10), [10,20), [20,40), [40,infinity) feet"],
                     summaries=regional, denominator="all eligible attempts in context",
                     measurement="quantized recorded proxies; regional residuals do not identify a unique component or establish blocked-origin accuracy"),
        opportunity=dict(units="expected_goals", reference_season=anchor["reference_season"],
                         definition="anchor joint shooter-goalie frequencies; exact pairwise probability products; anchor conditional origin law", **opportunity),
        invariant_maxima=maxima, reconciled=dict(native_assessment=True, native_score=True,
                                                saved_conversion=True, saved_improved_direct=True,
                                                historical_stronger=True, complete_recognized_streams=True),
        resampling=dict(draws=2000, seed=3032026, generator="PCG64", percentile_method="linear",
                        calendar_days=[7, 14], undefined="null interval without redraw",
                        interpretation="paired pooled additive sums; original empty units/final partial blocks retained; pointwise intervals condition on fitted models and omit fitting, selection and origin-law uncertainty"),
        scientific_assessment="not_performed", resources=resources(started),
    )
    figures = save_figures(comparison, output)
    comparison["resources"] = dict(resources(started), numerical_pass_seconds=numerical_seconds,
                                   attempts_bytes=stream.stat().st_size,
                                   figures_bytes=sum(Path(ref["path"]).stat().st_size for ref in figures))
    write_json(output / "comparison.json", comparison)
    completion = dict(
        schema_version=1, artifact_kind="chance_conversion_diagnosis_completion", purpose=purpose,
        composition=identity(output / "composition.json"), attempts=identity(stream),
        comparison=identity(output / "comparison.json"), figures=figures,
        resources=dict(resources(started), output_bytes_before_completion=sum(p.stat().st_size for p in output.iterdir())),
        scientific_assessment="not_performed",
    )
    write_json(output / "completion.json", completion)
    return comparison


def save_figures(comparison, output):
    """three fixed static views; every map retains one signed native-unit scale."""
    probabilities = comparison["probabilities"]
    population = comparison["population_description"]
    colors = dict(baseline="#666666", revision="#176B87", historical_stronger="#A75D33",
                  improved_direct="#76518D")
    caption, height = caption_layout([
        population,
        "observed-cell conversion conditions on unblocked and the quantized recorded-origin proxy; all-attempt probabilities integrate the saved origin prior. these are retrospective recorded-context probabilities, not demonstrated pre-release forecasts.",
        "residual = 100 × (predicted − observed)/bin count; positive means overprediction. each predictor has its own 20 fixed bins: memberships differ. count panels retain all bins; grid centers and distances are in feet.",
        "no confidence shading. dotted ±1 percentage-point historical margins are reference lines only. paired pooled game/calendar intervals in comparison.json condition on fitted models and omit fitting, selection and origin-law uncertainty.",
    ], 12)
    fig, axes = plt.subplots(2, 2, figsize=(12, 6.4 + height), sharex=True, sharey="row")
    for column, quantity in enumerate(QUANTITIES):
        for predictor in PREDICTORS[quantity]:
            bins = probabilities[quantity]["own"][predictor]["metrics"]["calibration"]
            xs = [(bucket["lower"] + bucket["upper"]) / 2 for bucket in bins]
            residuals = [100 * (bucket["predicted_rate"] - bucket["observed_rate"])
                         if bucket["count"] else np.nan for bucket in bins]
            axes[0, column].plot(xs, residuals, "o", ms=3, color=colors[predictor], label=predictor)
            axes[1, column].plot(xs, [bucket["count"] for bucket in bins], "o", ms=3,
                                 color=colors[predictor])
        axes[0, column].axhline(0, color="#222222", lw=.7)
        axes[0, column].axhline(1, color="#BBBBBB", lw=.6, ls=":")
        axes[0, column].axhline(-1, color="#BBBBBB", lw=.6, ls=":")
        axes[0, column].set_title(quantity.replace("_", " "))
        axes[0, column].legend(fontsize=8)
        axes[1, column].set_yscale("symlog", linthresh=1)
        axes[1, column].set_xlabel("own fixed probability bin")
    axes[0, 0].set_ylabel("predicted − observed, percentage points")
    axes[1, 0].set_ylabel("absolute bin count")
    fig.tight_layout(rect=(0, height / fig.get_figheight(), 1, 1))
    fig.text(.04, .025, caption, fontsize=8, va="bottom")
    fig.savefig(output / "probabilities.png", dpi=180)
    plt.close(fig)

    caption, height = caption_layout([
        population,
        "fixed regions partition native 5-foot cell centers with behind-goal/outside-zone precedence; proxy labels use native cell_id, not raw coordinate cuts. unblocked = unblocked and proxy in region; goal = goal and proxy in region. blocked labels are zero and do not assign origins.",
        "all/none/recent denominators are all eligible attempts in that preceding-action context. residual = 100 × (predicted − observed)/count; positive means excess probability per 100 eligible attempts. unchanged unblocked mass is shown once; each quantity row has its own range.",
        "bars show pointwise 95% whole-game linear-percentile intervals conditional on fitted models; undefined draws have no interval. hollow points mark constant-label regions, which cannot establish calibration support. fitting, selection and origin-law uncertainty are excluded; no unique faulty component or physical-origin accuracy follows.",
    ], 14)
    fig, axes = plt.subplots(2, 3, figsize=(14, 7.5 + height), sharey="row")
    region_labels = [name.replace("_", " ") for name in REGION_NAMES]
    xs = np.arange(len(REGION_NAMES))
    for ri, quantity in enumerate(("unblocked", "goal")):
        for ci, context in enumerate(CONTEXTS):
            ax = axes[ri, ci]
            for predictor in (("baseline",) if quantity == "unblocked" else ("baseline", "revision")):
                records = comparison["regions"]["summaries"][predictor][quantity][context]
                offset = 0 if quantity == "unblocked" else -.10 if predictor == "baseline" else .10
                for i, record in enumerate(records):
                    interval = record["residual_interval"]
                    y = interval["estimate"]
                    if y is None:
                        continue
                    ax.plot(xs[i] + offset, y, "o", color=colors[predictor], ms=4,
                            markerfacecolor="none" if interval["all_one_label"] else colors[predictor],
                            label=predictor if i == 0 else None)
                    if interval["interval"] is not None:
                        low, high = interval["interval"]
                        ax.vlines(xs[i] + offset, low, high, color=colors[predictor], lw=1)
            ax.axhline(0, color="#222222", lw=.7)
            baseline_records = comparison["regions"]["summaries"]["baseline"][quantity][context]
            labels = [f"{label}\nobserved={record['observed_positive_count']}"
                      for label, record in zip(region_labels, baseline_records, strict=True)]
            ax.set_xticks(xs, labels, rotation=45, ha="right", fontsize=8)
            ax.set_title(f"{quantity}; {context}; n={baseline_records[0]['count']}; "
                         f"games={baseline_records[0]['residual_interval']['contributing_games']}")
    axes[0, 0].set_ylabel("predicted − observed\nper 100 eligible attempts")
    axes[1, 0].set_ylabel("predicted − observed\nper 100 eligible attempts")
    fig.legend(handles=[plt.Line2D([], [], marker="o", color=colors[name], linestyle="none", label=name)
                        for name in ("baseline", "revision")],
               loc="upper center", ncols=2, fontsize=9)
    fig.tight_layout(rect=(0, height / fig.get_figheight(), 1, .97))
    fig.text(.035, .025, caption, fontsize=8, va="bottom")
    fig.savefig(output / "regions.png", dpi=180)
    plt.close(fig)

    caption, height = caption_layout([
        population,
        "signed revision − baseline summed opportunity mass per native 5-foot cell; expected-goal units, one symmetric color scale for blocked/unblocked totals, no independent map normalization. x points toward attacking goal (89, 0); y retains native orientation; coordinates are feet.",
        "anchor target-season joint shooter–goalie weights average pairwise u × revised r products. unblocked origins are recorded-proxy point masses; blocked origins retain saved anchor conditional inference. opportunity has no observed calibration target or error bars and is not a player effect.",
        "point estimates omit fitting, selection and origin-law uncertainty; physical blocked-origin accuracy is unestablished.",
    ], 12)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.7 + height), sharex=True, sharey=True)
    centers = np.asarray(comparison["geometry"]["centers"])
    xs, ys = np.unique(centers[:, 0]), np.unique(centers[:, 1])
    limit = max(abs(value) for label in ("blocked", "unblocked")
                for value in comparison["opportunity"][label]["cell_mass_difference"])
    limit = limit or 1e-12
    for ax, label in zip(axes, ("blocked", "unblocked"), strict=True):
        values = comparison["opportunity"][label]
        cells = np.full((len(ys), len(xs)), np.nan)
        cells[np.searchsorted(ys, centers[:, 1]), np.searchsorted(xs, centers[:, 0])] = values["cell_mass_difference"]
        artist = ax.pcolormesh(xs, ys, cells, shading="nearest", cmap="RdBu_r", vmin=-limit, vmax=limit)
        ax.plot(89, 0, "+", color="#222222", ms=7)
        ax.set_aspect("equal")
        ax.set_title(f"{label}; n={values['count']}; total Δ={values['signed_total_change']:.3f} xg")
        ax.set_xlabel("attacking x, feet")
    axes[0].set_ylabel("attacking y, feet")
    fig.subplots_adjust(left=.06, right=.86, top=.91, bottom=height / fig.get_figheight() + .09,
                        wspace=.12)
    bar = fig.add_axes((.89, height / fig.get_figheight() + .14, .018,
                        .70 - height / fig.get_figheight()))
    fig.colorbar(artist, cax=bar, label="revision − baseline expected goals per cell")
    fig.text(.035, .025, caption, fontsize=8, va="bottom")
    fig.savefig(output / "opportunity.png", dpi=180)
    plt.close(fig)
    return [identity(output / name) for name in ("probabilities.png", "regions.png", "opportunity.png")]


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--evidence", required=True, action=Once)
    parser.add_argument("--out", required=True, action=Once)
    args = parser.parse_args()
    try:
        run(Path(args.evidence), args.out)
    except (InputContractError, OSError, KeyError, TypeError, ValueError, OverflowError) as error:
        print(f"conversion diagnosis failed: {error}", file=sys.stderr)
        return 1
    print(f"conversion diagnosis complete: {args.out}; scientific assessment not performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
