"""bounded, manual component research; completion never means scientific approval."""

import argparse
from collections import Counter
import json
import hashlib
import math
from pathlib import Path
import resource
import sys
import time
from itertools import zip_longest

import numpy as np
import scipy
from hockey_stats.artifacts import implementation_identity, write_json
from hockey_stats.captures import InputContractError, strict_json
from hockey_stats.chance_cli import identity, output_path, read_json
from hockey_stats.chance_data import prepare
from hockey_stats.chance_cohort import SOURCE_STATUSES, STUDY_INCLUSIONS
from hockey_stats.chance_features import PREPARATION_IDENTITY
from hockey_stats.chance_evaluation import (
    PROBABILITY_POPULATIONS, PROBABILITY_SUMS, add_binary, binary_metrics, binary_record,
    calibration_bin, diagnostic_groups, finish_binary, summarize_component,
)
from hockey_stats.cli import Once
from chance_review import agrees, calendar_blocks, linked_path, ratio_interval, require

QUANTITIES = ("unblocked_conversion", "all_attempt_recorded_context")
WINDOWS = ("development", "season_transfer")
RECIPES = ("baseline", "context_interactions", "recent_history")
PAIR_FIELDS = (
    "game_id", "source_index", "event_id", "game_date", "season", "source_identity",
    "source_status", "source_reasons", "study_inclusion", "study_reasons",
    "quantity", "applicable", "blocked", "goal",
)


def implementation():
    value = implementation_identity()
    value.update(
        numpy_version=np.__version__, scipy_version=scipy.__version__,
        lockfile_sha256=identity(Path(__file__).resolve().parents[1] / "uv.lock")["sha256"],
    )
    return value


def resources(started):
    return dict(wall_seconds=time.monotonic() - started,
                peak_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def rows(path):
    with path.open(encoding="utf-8") as source:
        for index, line in enumerate(source):
            try:
                value = strict_json(line.encode())
            except ValueError as error:
                raise InputContractError(f"{path}:{index + 1}: invalid prediction json") from error
            require(isinstance(value, dict), "prediction row must be an object")
            yield value


def common(prepared):
    return dict(schema_version=3, purpose=prepared["purpose"], implementation=implementation(),
                inputs=prepared["inputs"], selection=prepared["selection"],
                game_dates=prepared["game_dates"], coverage=prepared["coverage"],
                preparation_identity=prepared["preparation_identity"],
                scientific_assessment="not_performed")


def prediction_row(attempt, prepared, sources, cohort_row):
    gid = attempt["game_id"]
    return dict(
        schema_version=3, game_id=gid, source_index=attempt["source_index"],
        event_id=attempt["event_id"], game_date=prepared["game_dates"][gid],
        season=attempt["season"], source_identity=sources[gid],
        status=attempt["status"], reasons=attempt["reasons"],
        **{field: cohort_row[field] for field in
           ("source_status", "source_reasons", "study_inclusion", "study_reasons")},
        blocked=attempt["blocked"], goal=attempt["goal"],
    )


def source_identities(prepared):
    sources = {}
    for value in prepared["inputs"]:
        if value["kind"] == "game":
            gid = Path(value["path"]).stem
            require(gid not in sources and gid in prepared["game_dates"],
                    "duplicate or unselected game source identity")
            sources[gid] = value
    return sources


def prediction_check(row):
    require(isinstance(row, dict) and all(field in row for field in (
        "schema_version", *PAIR_FIELDS, "status", "reasons", "observed", "log_p",
        "log_not_p", "probability", "diagnostic_groups", "component")),
        "incomplete component prediction row")
    require(type(row["schema_version"]) is int and row["schema_version"] == 3,
            "schema-3 component prediction row required")
    require(type(row["source_index"]) is int and row["source_index"] >= 0,
            "invalid attempt source index")
    require(row["quantity"] in QUANTITIES, "invalid component quantity")
    require(row["status"] in ("predicted", "study_excluded", "not_applicable", "out_of_scope", "unavailable"),
            "invalid component prediction status")
    require(row["source_status"] in SOURCE_STATUSES and row["study_inclusion"] in STUDY_INCLUSIONS,
            "invalid source or study disposition")
    require(all(isinstance(row[field], list) and all(isinstance(v, str) for v in row[field])
                for field in ("reasons", "source_reasons", "study_reasons")),
            "component prediction reasons must be string arrays")
    require(isinstance(row["diagnostic_groups"], dict), "invalid prediction diagnostic groups")
    require(type(row["applicable"]) is bool, "invalid component applicability")
    require(type(row["blocked"]) is bool and type(row["goal"]) is bool and
            not (row["blocked"] and row["goal"]), "invalid recorded block/goal labels")
    require(row["applicable"] == (row["quantity"] != "unblocked_conversion" or not row["blocked"]),
            "source quantity applicability changed")
    source, study, status = row["source_status"], row["study_inclusion"], row["status"]
    require(source != "eligible" or not row["source_reasons"],
            "eligible source row has exclusion reasons")
    if source != "eligible":
        require(study == "source_excluded" and status == source and
                row["reasons"] == row["source_reasons"] and not row["study_reasons"],
                "source exclusion disposition changed")
    elif not row["applicable"]:
        require(study == "not_applicable" and status == "not_applicable" and
                row["reasons"] == row["source_reasons"] and not row["study_reasons"],
                "blocked conversion must be non-applicable")
    elif study == "included":
        require(status == "predicted" and not row["study_reasons"] and not row["reasons"],
                "included rows must be predicted without exclusion reasons")
    else:
        require(study == "feature_unavailable" and bool(row["study_reasons"]) and
                status in ("predicted", "study_excluded") and
                row["reasons"] == ([] if status == "predicted" else row["study_reasons"]),
                "invalid omitted-row prediction disposition")
    if row["status"] == "predicted":
        require(row["applicable"] and type(row["observed"]) is int and
                row["observed"] == int(row["goal"]), "invalid predicted label")
        record = binary_record(row["observed"], row["log_p"], row["log_not_p"])
        require(type(row["probability"]) in (int, float) and math.isfinite(row["probability"]) and
                0 <= row["probability"] <= 1, "invalid component prediction probability")
        require(agrees(row["probability"], record["predicted_probability_sum"]),
                "prediction probability/log probability disagree")
    else:
        require(all(row[field] is None for field in ("observed", "log_p", "log_not_p", "probability")),
                "excluded or non-applicable prediction must be null")


def paired_rows(left, right):
    seen = set()
    for before, after in zip_longest(rows(left), rows(right)):
        require(before is not None and after is not None, "prediction stream length mismatch")
        prediction_check(before)
        prediction_check(after)
        require(all(before[field] == after[field] for field in PAIR_FIELDS),
                "prediction keys, labels, source identities or cohorts mismatch")
        omitted_pair = before["study_inclusion"] == "feature_unavailable"
        if omitted_pair:
            require(before["status"] == "predicted" and after["status"] == "study_excluded",
                    "omitted pairs require baseline predictions and null candidate predictions")
        else:
            require(all(before[field] == after[field] for field in ("status", "reasons", "observed")),
                    "paired prediction disposition or observed labels changed")
        require(
            {k: v for k, v in before["diagnostic_groups"].items() if not k.startswith("actor_support:")} ==
            {k: v for k, v in after["diagnostic_groups"].items() if not k.startswith("actor_support:")},
            "paired source-context diagnostic descriptors changed",
        )
        key = before["game_id"], before["source_index"]
        require(key not in seen, "duplicate prediction key")
        seen.add(key)
        yield before, after


def fit(args):
    from hockey_stats.chance import fit_component, compile_designs, COMPONENT_QUANTITIES
    from hockey_stats.chance_cohort import outcome_audit, validate_cohort

    started = time.monotonic()
    selection = Path(args.selection).resolve(strict=True)
    cohort_path = Path(args.cohort).resolve(strict=True)
    config_path = Path(args.config).resolve(strict=True)
    protocol = Path(args.protocol).resolve(strict=True)
    prepared = prepare(selection)
    cohort = validate_cohort(read_json(cohort_path), prepared)
    require(cohort["quantity"] == args.quantity, "training cohort quantity mismatch")
    output = output_path(args.out, prepared["input_roots"] +
                         [str(p.parent) for p in (selection, cohort_path, config_path, protocol)])
    metadata = dict(common(prepared), config_identity=identity(config_path),
                    protocol_identity=identity(protocol), training_cohort_identity=identity(cohort_path),
                    training_game_dates=prepared["game_dates"],
                    training_game_ids=list(prepared["game_dates"]),
                    training_dates=sorted(set(prepared["game_dates"].values())))
    config = read_json(config_path)
    included = [attempt for attempt, membership in zip(prepared["attempts"], cohort["rows"], strict=True)
                if membership["study_inclusion"] == "included"]
    design = compile_designs(included, config,
                             seasons=[game["season"] for game in prepared["games"]])[
                                 COMPONENT_QUANTITIES[args.quantity]]["design"]
    output.mkdir()
    component, diagnostics = fit_component(
        [r for r in prepared["attempts"] if r["status"] == "eligible"],
        config, metadata, quantity=args.quantity, design=design, training_cohort=cohort,
        feature_games=prepared["feature_games"], feature_player_games=prepared["feature_player_games"],
    )
    document = dict(metadata, artifact_kind="chance_component_fit", quantity=args.quantity,
                    stage_design=design, training_cohort_audit=outcome_audit(prepared, cohort),
                    diagnostics=diagnostics, status="fitted" if component is not None else "failed",
                    resources=resources(started))
    write_json(output / "fit.json", document)
    if component is None:
        print(f"component fit failed; diagnostics saved to {output}", file=sys.stderr)
        return 1
    write_json(output / "component.json", component)
    write_json(output / "completion.json", dict(
        artifact_kind="chance_component_fit_completion", schema_version=3, purpose=prepared["purpose"],
        protocol=identity(protocol), config=identity(config_path), selection=identity(selection),
        preparation_identity=prepared["preparation_identity"], training_cohort=identity(cohort_path),
        fit=identity(output / "fit.json"), component=identity(output / "component.json"),
        scientific_assessment="not_performed"))
    print(f"component fit complete: {output}; scientific assessment not performed")
    return 0


def predict_component_rows(component, prepared, assessment_cohort, *, component_identity, arm):
    """one native pass over validated source facts and their explicit cohort ledger."""
    from hockey_stats.chance import component_prediction_context, predict_component

    require(arm in ("baseline", "sequence"), "component evaluation arm must be baseline or sequence")
    context = component_prediction_context(component, feature_games=prepared["feature_games"],
                                           feature_player_games=prepared["feature_player_games"])
    sources = source_identities(prepared)
    for attempt, membership in zip(prepared["attempts"], assessment_cohort["rows"], strict=True):
        row = prediction_row(attempt, prepared, sources, membership)
        applicable = component["quantity"] != "unblocked_conversion" or not attempt["blocked"]
        row.update(quantity=component["quantity"], component=component_identity,
                   applicable=applicable, observed=None, log_p=None, log_not_p=None,
                   probability=None, season_basis=None, state_season=None, actor_evidence=None)
        if attempt["status"] == "eligible":
            if not applicable:
                row["status"] = "not_applicable"
            elif membership["study_inclusion"] == "feature_unavailable" and arm == "sequence":
                row.update(status="study_excluded", reasons=membership["study_reasons"])
            else:
                row["status"] = "predicted"
                prediction = predict_component(component, attempt, context)
                row.update(prediction, observed=int(attempt["goal"]),
                           probability=math.exp(prediction["log_p"]))
        row["diagnostic_groups"] = diagnostic_groups(
            attempt, row["game_date"], row["actor_evidence"] or
            {actor: dict(basis=None) for actor in ("shooter", "goalie")})
        prediction_check(row)
        yield row


def evaluate(args):
    from hockey_stats.chance import validate_component
    from hockey_stats.chance_cohort import outcome_audit, validate_cohort

    started = time.monotonic()
    selection = Path(args.selection).resolve(strict=True)
    cohort_path = Path(args.cohort).resolve(strict=True)
    protocol = Path(args.protocol).resolve(strict=True)
    component_path = Path(args.component).resolve(strict=True)
    component = validate_component(read_json(component_path))
    prepared = prepare(selection)
    cohort = validate_cohort(read_json(cohort_path), prepared)
    require(component["purpose"] == prepared["purpose"], "component and selection purposes disagree")
    require(cohort["quantity"] == component["quantity"] and
            cohort["definition"] == component["training_cohort"]["definition"],
            "training and assessment cohort definitions disagree")
    require(identity(protocol) == component["protocol_identity"], "component evaluation protocol changed")
    training = component["training_game_dates"]
    require(not set(training) & set(prepared["game_dates"]), "assessment game ids overlap training")
    require(min(prepared["game_dates"].values()) > max(training.values()),
            "assessment dates must follow all training dates")
    output = output_path(args.out, prepared["input_roots"] +
                         [str(p.parent) for p in (selection, cohort_path, component_path, protocol)])
    output.mkdir()
    component_identity = identity(component_path)
    with (output / "attempts.jsonl").open("x", encoding="utf-8") as destination:
        for row in predict_component_rows(component, prepared, cohort,
                                          component_identity=component_identity, arm=args.arm):
            destination.write(json.dumps(row, allow_nan=False) + "\n")
    document = dict(common(prepared), artifact_kind="chance_component_evaluation",
                    quantity=component["quantity"], component=component_identity,
                    stage_design=component["layout"]["design"], arm=args.arm,
                    protocol=identity(protocol), selection_identity=identity(selection),
                    cohort=identity(cohort_path), training_cohort=component["training_cohort"]["membership_identity"],
                    assessment_cohort_audit=outcome_audit(prepared, cohort),
                    attempts=identity(output / "attempts.jsonl"),
                    **summarize_component(rows(output / "attempts.jsonl"), prepared["game_dates"]),
                    resources=resources(started))
    write_json(output / "evaluation.json", document)
    write_json(output / "completion.json", dict(
        schema_version=3, artifact_kind="chance_component_evaluation_completion", purpose=prepared["purpose"],
        protocol=identity(protocol), selection=identity(selection), preparation_identity=prepared["preparation_identity"],
        training_cohort=component["training_cohort"]["membership_identity"], assessment_cohort=identity(cohort_path),
        component=component_identity, arm=args.arm, attempts=identity(output / "attempts.jsonl"),
        evaluation=identity(output / "evaluation.json"), scientific_assessment="not_performed"))
    print(f"component evaluation complete: {output}; scientific assessment not performed")
    return 0


def factual_component_rows(path, quantity, predictor, cohort=None):
    for row in rows(path):
        if cohort is not None and (row["game_id"], row["source_index"]) not in cohort:
            continue
        value = row["predictions"].get(predictor)
        applicable = quantity != "unblocked_conversion" or not row["blocked"]
        inclusion = ("included" if applicable else "not_applicable") if row["source_status"] == "eligible" else "source_excluded"
        yield dict(row, quantity=quantity, applicable=applicable, study_inclusion=inclusion, study_reasons=[],
                   diagnostic_groups=row["predictor_groups"][predictor],
                   status="predicted" if value is not None else
                   "not_applicable" if row["status"] == "eligible" else row["status"],
                   observed=int(not row["blocked"] if quantity == "marginal_unblocked" else row["goal"])
                   if value is not None else None,
                   log_p=value["log_p"] if value else None,
                   log_not_p=value["log_not_p"] if value else None,
                   probability=math.exp(value["log_p"]) if value else None)


def diagnose(args):
    from hockey_stats.chance import (
        validate_model, prediction_context, predict_attempt, extract_component, benchmark_actor_evidence,
        component_prediction_context, predict_component,
    )
    from hockey_stats.chance_cohort import component_cohort

    started = time.monotonic()
    evidence_path = Path(args.evidence).resolve(strict=True)
    evidence = read_json(evidence_path)
    protocol = Path(args.protocol).resolve(strict=True)
    require(evidence["schema_version"] == 2 and evidence["purpose"] == "research",
            "diagnosis requires schema-2 research evidence")
    require([v["label"] for v in evidence["assessments"]] == ["anchor", "weaker", "stronger"],
            "diagnosis requires three saved 03e development models in native order")
    require(evidence["benchmarks"] == dict.fromkeys(QUANTITIES, "stronger"),
            "historical stronger direct benchmark identities must be retained")
    output = output_path(args.out, [str(evidence_path.parent), str(protocol.parent)])
    output.mkdir()
    prepared_cache = {}
    records = []
    absent_actor_support = {
        "candidate_r": dict(shooter=dict(basis=None), goalie=dict(basis=None)),
        "benchmark_r": dict(shooter=dict(basis=None), goalie=dict(basis=None)),
        "benchmark_all": dict(shooter=dict(basis=None), goalie=dict(basis=None)),
        "candidate_unblocked": dict(shooter=dict(basis=None)),
        "candidate_all": dict(u=dict(shooter=dict(basis=None)),
                              r=dict(shooter=dict(basis=None), goalie=dict(basis=None))),
    }
    for entry in evidence["assessments"]:
        assessment_path = Path(entry["path"]).resolve(strict=True)
        assessment = read_json(assessment_path)
        require(assessment["schema_version"] == 4, "current assessment schema 4 required; historical studies use their git revision")
        model_path = linked_path(assessment["model"])
        model = validate_model(read_json(model_path))
        model_identity = identity(model_path)
        components, component_contexts = {}, {}
        for quantity in QUANTITIES:
            component = extract_component(model, quantity=quantity)
            component["protocol_identity"] = identity(protocol)
            components[quantity] = component
        require(model["purpose"] == "research", "fixture candidate cannot supply scientific diagnosis")
        for population, origin in (("training", model), ("assessment", assessment)):
            selection_ref = next(v for v in origin["inputs"] if v["kind"] == "selection")
            selection_path = linked_path(selection_ref)
            if str(selection_path) not in prepared_cache:
                prepared_cache[str(selection_path)] = prepare(selection_path)
            prepared = prepared_cache[str(selection_path)]
            context = prediction_context(model, feature_games=prepared["feature_games"], feature_player_games=prepared["feature_player_games"])
            component_contexts = {quantity: component_prediction_context(component, feature_games=prepared["feature_games"], feature_player_games=prepared["feature_player_games"]) for quantity, component in components.items()}
            require(not any(output.is_relative_to(Path(root)) for root in prepared["input_roots"]),
                    "diagnosis output must be outside source input directories")
            require(all(prepared[field] == origin[field] for field in ("selection", "inputs", "game_dates", "coverage")),
                    "saved original population identity changed")
            stream = output / f"{population}-{entry['label']}.jsonl"
            sources = source_identities(prepared)
            source_cohort = component_cohort(prepared, quantity="all_attempt_recorded_context", required_families=[])
            extraction_errors = {q: dict(max_abs_log_probability_difference=0.0,
                                         max_abs_probability_difference=0.0) for q in QUANTITIES}
            with stream.open("x", encoding="utf-8") as destination:
                for attempt, membership in zip(prepared["attempts"], source_cohort["rows"], strict=True):
                    row = prediction_row(attempt, prepared, sources, membership)
                    predictions, actors, predictor_groups = {}, {}, {}
                    for quantity, (_, predictors) in PROBABILITY_POPULATIONS.items():
                        for predictor in predictors:
                            predictor_groups[predictor] = diagnostic_groups(
                                attempt, row["game_date"], absent_actor_support[predictor])
                    if attempt["status"] == "eligible":
                        result = predict_attempt(model, attempt, context)
                        for quantity, native in (("unblocked_conversion", "candidate_r"),
                                                  ("all_attempt_recorded_context", "benchmark_all")):
                            if quantity == "unblocked_conversion" and attempt["blocked"]:
                                continue
                            extracted = predict_component(components[quantity], attempt, component_contexts[quantity])
                            for field in ("log_p", "log_not_p"):
                                error = abs(extracted[field] - result[native][field])
                                extraction_errors[quantity]["max_abs_log_probability_difference"] = max(
                                    extraction_errors[quantity]["max_abs_log_probability_difference"], error)
                                require(error <= 1e-12, "extracted component log predictions differ from native stage")
                            error = abs(math.exp(extracted["log_p"]) - math.exp(result[native]["log_p"]))
                            extraction_errors[quantity]["max_abs_probability_difference"] = max(
                                extraction_errors[quantity]["max_abs_probability_difference"], error)
                            require(error <= 1e-12, "extracted component probabilities differ from native stage")
                        actors = result["actor_evidence"]
                        benchmarks = benchmark_actor_evidence(model, attempt, result["state_season"])
                        for quantity, (_, predictors) in PROBABILITY_POPULATIONS.items():
                            if quantity == "unblocked_conversion" and attempt["blocked"]:
                                continue
                            for predictor in predictors:
                                predictions[predictor] = result[predictor]
                                support = benchmarks[predictor] if predictor in benchmarks else (
                                    actors["r"] if predictor == "candidate_r" else
                                    actors["u"] if predictor == "candidate_unblocked" else actors)
                                predictor_groups[predictor] = diagnostic_groups(attempt, row["game_date"], support)
                    row.update(model=model_identity, predictions=predictions, actor_evidence=actors,
                               predictor_groups=predictor_groups,
                               diagnostic_groups=diagnostic_groups(attempt, row["game_date"], actors))
                    destination.write(json.dumps(row, allow_nan=False) + "\n")
            summaries = {}
            for quantity, (_, predictors) in PROBABILITY_POPULATIONS.items():
                summaries[quantity] = {}
                for predictor in predictors:
                    summary = summarize_component(factual_component_rows(stream, quantity, predictor), prepared["game_dates"],
                                                  outcome="unblocked" if quantity == "marginal_unblocked" else "goal")
                    summaries[quantity][predictor] = summary
                    if population == "assessment":
                        expected = assessment["metrics"][quantity][predictor]
                        require(all(agrees(summary["metrics"][key], expected[key]) for key in PROBABILITY_SUMS),
                                "factual assessment counts/probability/loss sums do not reconcile")
                        for actual, saved in zip(summary["per_game"], assessment["per_game"], strict=True):
                            require(actual["game_id"] == saved["game_id"] and
                                    all(agrees(actual["metrics"][key], saved["metrics"][quantity][predictor][key])
                                        for key in PROBABILITY_SUMS), "factual per-game sums do not reconcile")
            records.append(dict(label=entry["label"], population=population,
                                in_sample=population == "training", model=identity(model_path),
                                original_assessment=identity(assessment_path), selection=selection_ref,
                                game_dates=prepared["game_dates"], coverage=prepared["coverage"],
                                attempts=identity(stream), summaries=summaries,
                                extraction_verification=extraction_errors,
                                reconciled_to_saved_evaluation=population == "assessment"))
        if entry["label"] == "anchor":
            for quantity in QUANTITIES:
                write_json(output / f"baseline-{quantity}.json", components[quantity])
    cohorts = {}
    for population in ("training", "assessment"):
        anchor = next(r for r in records if r["label"] == "anchor" and r["population"] == population)
        cohort = {(r["game_id"], r["source_index"]) for r in rows(linked_path(anchor["attempts"]))
                  if "candidate_all" in r["predictions"] and
                  .10 <= math.exp(r["predictions"]["candidate_all"]["log_p"]) < .15}
        cohorts[population] = dict(definition="anchor candidate_all probability in [0.10, 0.15); descriptive paired cohort",
                                  count=len(cohort), models={})
        for record in records:
            if record["population"] != population:
                continue
            cohorts[population]["models"][record["label"]] = {
                quantity: {predictor: summarize_component(
                    factual_component_rows(linked_path(record["attempts"]), quantity, predictor, cohort),
                    record["game_dates"], outcome="unblocked" if quantity == "marginal_unblocked" else "goal")
                    for predictor in predictors}
                for quantity, (_, predictors) in PROBABILITY_POPULATIONS.items()
            }
    document = dict(schema_version=1, artifact_kind="chance_saved_diagnosis", purpose="research",
                    implementation=implementation(), protocol=identity(protocol), evidence=identity(evidence_path),
                    historical_benchmarks=evidence["benchmarks"], records=records, anchor_cohorts=cohorts,
                    interpretation="training is in-sample; subgroup associations do not identify a unique cause",
                    scientific_assessment="not_performed", resources=resources(started))
    write_json(output / "diagnosis.json", document)
    write_json(output / "completion.json", dict(schema_version=1, diagnosis=identity(output / "diagnosis.json"),
                                               scientific_assessment="not_performed"))
    print(f"saved diagnosis complete: {output}; scientific assessment not performed")
    return 0


def compare_pair(baseline, changed):
    """strict entire-stream pairing; baseline owns paired subgroup membership."""
    require(baseline["game_dates"] == changed["game_dates"], "paired selected game ledgers changed")
    left = linked_path(baseline["attempts"])
    right = linked_path(changed["attempts"])
    bins = [dict(lower=b["lower"], upper=b["upper"], upper_inclusive=b["upper_inclusive"],
                 baseline=binary_metrics(calibration=False), changed=binary_metrics(calibration=False))
            for b in binary_metrics()["calibration"]]

    def paired_predictions():
        for before, after in paired_rows(left, right):
            if before["study_inclusion"] == "included":
                bucket = bins[calibration_bin(before["probability"])]
                for name, row in (("baseline", before), ("changed", after)):
                    add_binary(bucket[name], binary_record(row["observed"], row["log_p"], row["log_not_p"]))
            yield dict(after, diagnostic_groups=before["diagnostic_groups"])

    paired_summary = summarize_component(
        paired_predictions(), baseline["game_dates"])
    for field in ("count", "observed_positive_count"):
        require(paired_summary["metrics"][field] == baseline["metrics"][field],
                "paired quantity population mismatch")
    for key in PROBABILITY_SUMS:
        require(agrees(paired_summary["metrics"][key], changed["metrics"][key]),
                "stream and saved changed metrics disagree")
    dates = list(baseline["game_dates"].values())
    units = dict(games=None, calendar_7_day=calendar_blocks(dates, 7),
                 calendar_14_day=calendar_blocks(dates, 14))
    samples = {
        name: np.random.Generator(np.random.PCG64(3032026)).integers(
            0, len(dates) if blocks is None else int(max(blocks)) + 1,
            size=(2000, len(dates) if blocks is None else int(max(blocks)) + 1))
        for name, blocks in units.items()
    }
    before_games = baseline["per_game"]
    after_games = paired_summary["per_game"]
    require([v["game_id"] for v in before_games] == [v["game_id"] for v in after_games],
            "paired game order mismatch")
    denominators = [v["metrics"]["count"] for v in before_games]
    require(denominators == [v["metrics"]["count"] for v in after_games],
            "paired per-game cohort denominators changed")
    results = {}
    for name, field, scale in (("log_loss", "log_loss_sum", 1),
                               ("brier_score", "brier_score_sum", 1),
                               ("predicted_minus_observed_pp", "predicted_probability_sum", 100)):
        numerators = [scale * (a["metrics"][field] - b["metrics"][field])
                      for b, a in zip(before_games, after_games, strict=True)]
        results[name] = {
            unit: ratio_interval(numerators, denominators, 3032026,
                                 blocks=blocks, samples=samples[unit])
            for unit, blocks in units.items()
        }
    groups = {}
    for category, before_groups in baseline["groups"].items():
        after_groups = {g["value"]: g for g in paired_summary["groups"][category]}
        groups[category] = []
        for before in before_groups:
            after = after_groups[before["value"]]
            groups[category].append(dict(
                value=before["value"], baseline=before["metrics"], changed=after["metrics"],
                delta_log_loss=(after["metrics"]["log_loss"] - before["metrics"]["log_loss"])
                if before["metrics"]["count"] else None,
                delta_brier=(after["metrics"]["brier_score"] - before["metrics"]["brier_score"])
                if before["metrics"]["count"] else None,
                delta_predicted_minus_observed_pp=(after["metrics"]["predicted_minus_observed_pp"] -
                                                   before["metrics"]["predicted_minus_observed_pp"])
                if before["metrics"]["count"] else None,
            ))
    for bucket in bins:
        before, after = bucket["baseline"], bucket["changed"]
        finish_binary(before)
        finish_binary(after)
        bucket.update(
            delta_log_loss=after["log_loss"] - before["log_loss"] if before["count"] else None,
            delta_brier=after["brier_score"] - before["brier_score"] if before["count"] else None,
            delta_predicted_minus_observed_pp=(after["predicted_minus_observed_pp"] -
                                               before["predicted_minus_observed_pp"])
            if before["count"] else None,
        )
    for name, expected in (("baseline", baseline["metrics"]), ("changed", changed["metrics"])):
        require(all(agrees(sum(bucket[name][field] for bucket in bins), expected[field])
                    for field in PROBABILITY_SUMS), "paired calibration sums do not reconcile")
    return dict(delta=results, baseline_metrics=baseline["metrics"], changed_metrics=changed["metrics"],
                paired_groups=groups, paired_calibration=bins,
                group_definition="baseline component defines actor-support memberships for both predictors; own calibration bins remain separate",
                changed_own_groups=changed["groups"], counts_by_status=changed["counts_by_status"])


def validate_evaluation(reference, component_reference, selection_reference, protocol, quantity, purpose,
                        *, component, cohort_reference, arm):
    """bind the whole recognized stream to one saved cohort, source ledger and summary."""
    from hockey_stats.chance_cohort import validate_cohort_document, validate_outcome_audit

    document = read_json(linked_path(reference))
    cohort = validate_cohort_document(read_json(linked_path(cohort_reference)))
    require(type(document["schema_version"]) is int and document["schema_version"] == 3 and
            document["artifact_kind"] == "chance_component_evaluation" and
            document["purpose"] == purpose and document["quantity"] == quantity and
            document["scientific_assessment"] == "not_performed" and
            document["component"] == component_reference and document["protocol"] == protocol and
            document["selection_identity"] == selection_reference and
            document["cohort"] == cohort_reference and document["arm"] == arm and
            document["training_cohort"] == component["training_cohort"]["membership_identity"] and
            document["preparation_identity"] == component["preparation_identity"] and
            document["stage_design"] == component["layout"]["design"],
            "component evaluation binding mismatch")
    require(arm in ("baseline", "sequence") and cohort["quantity"] == quantity and
            cohort["definition"] == component["training_cohort"]["definition"] and
            all(cohort[field] == document[field] for field in
                ("purpose", "selection", "inputs", "game_dates", "preparation_identity")),
            "component evaluation cohort identities or definition changed")
    selection_path = linked_path(selection_reference)
    selection = read_json(selection_path)
    for corpus in selection["corpora"]:
        corpus["path"] = str((selection_path.parent / corpus["path"]).resolve(strict=True))
    selection["history_corpora"] = [
        str((selection_path.parent / path).resolve(strict=True))
        for path in selection["history_corpora"]
    ]
    require(document["selection"] == selection, "evaluation selection content mismatch")
    require([v["game_id"] for v in document["per_game"]] == list(document["game_dates"]),
            "evaluation selected/per-game identities mismatch")
    coverage = document["coverage"]
    source_available = coverage["attempts"]["recognized_attempts"] is not None
    if source_available:
        require(coverage["attempts_by_status"] == cohort["counts"]["source_statuses"] and
                coverage["attempts"]["recognized_attempts"] == len(cohort["rows"]),
                "evaluation original source coverage differs from cohort")
    else:
        require(not cohort["rows"] and all(value is None for value in coverage["attempts_by_status"].values()),
                "unavailable source coverage must have no recognized cohort rows")
    corpus_references = {item["path"]: item for item in document["inputs"] if item["kind"] == "corpus"}
    games = {}
    for selected in selection["corpora"]:
        corpus = read_json(linked_path(corpus_references[selected["path"]]))
        inventory = {game["game_id"]: game for game in corpus["reference"]["inventory"]}
        for gid in selected["game_ids"]:
            game = inventory[gid]
            require(gid not in games and game["game_date"] == document["game_dates"][gid],
                    "evaluation source inventory game/date mismatch")
            games[gid] = game
    stream = linked_path(document["attempts"])
    sources = source_identities(document)
    goals = {gid: Counter() for gid in document["game_dates"]}
    reasons = Counter()
    for row, membership in zip_longest(rows(stream), cohort["rows"]):
        require(row is not None and membership is not None, "prediction stream and cohort length mismatch")
        prediction_check(row)
        require(all(row[field] == membership[field] for field in membership),
                "prediction stream and cohort keys, order or dispositions mismatch")
        gid = row["game_id"]
        require(row["component"] == component_reference and row["quantity"] == quantity and
                row["source_identity"] == sources[gid] and row["season"] == games[gid]["season"] and
                row["game_date"] == document["game_dates"][gid],
                "component prediction source/model identity mismatch")
        if row["study_inclusion"] == "feature_unavailable":
            require(row["status"] == ("predicted" if arm == "baseline" else "study_excluded"),
                    "omitted prediction does not follow declared arm")
        goals[gid][row["source_status"]] += int(row["goal"])
        reasons.update(row["source_reasons"])
    for status in ("eligible", "out_of_scope", "unavailable"):
        expected = coverage["attempts"]["goals_by_status"][status]
        require((not source_available and expected is None) or
                (source_available and sum(counts[status] for counts in goals.values()) == expected),
                "prediction raw goals do not reconcile to source coverage")
    require(all((count is None and not source_available) or reasons[reason] == count
                for reason, count in coverage["attempts_by_reason"].items()) and
            not set(reasons) - set(coverage["attempts_by_reason"]),
            "prediction source reasons do not reconcile to source coverage")
    expected_games = {game["game_id"]: game for game in cohort["per_game"]}
    require([game["game_id"] for game in coverage["per_game"]] == list(document["game_dates"]),
            "evaluation original coverage game ledger changed")
    for game in coverage["per_game"]:
        gid = game["game_id"]
        if game["event_collection_available"]:
            require(game["attempts_by_status"] == expected_games[gid]["source_statuses"] and
                    all(goals[gid][status] == game["goals_by_status"][status]
                        for status in ("eligible", "out_of_scope", "unavailable")),
                    "prediction per-game source coverage differs")
        else:
            require(game["attempts_by_status"] is None and game["goals_by_status"] is None and
                    not sum(expected_games[gid]["source_statuses"].values()) and not sum(goals[gid].values()),
                    "unavailable source game must retain null coverage and no recognized rows")
    summary = summarize_component(rows(stream), document["game_dates"])
    require(json.dumps(summary, sort_keys=True, allow_nan=False) ==
            json.dumps({field: document[field] for field in summary}, sort_keys=True, allow_nan=False),
            "prediction stream and saved evaluation accounting disagree")
    audit_inputs = {field: document[field] for field in
                    ("purpose", "selection", "inputs", "game_dates", "preparation_identity")}
    audit_inputs.update(games=list(games.values()), attempts=[
        dict(game_id=row["game_id"], source_index=row["source_index"], event_id=row["event_id"],
             status=row["source_status"], reasons=row["source_reasons"], goal=row["goal"], blocked=row["blocked"])
        for row in rows(stream)])
    validate_outcome_audit(document["assessment_cohort_audit"], audit_inputs, cohort)
    return document


def compare(args):
    from hockey_stats.chance import validate_component
    from hockey_stats.chance_cohort import validate_cohort_document
    from chance_review import clean_implementation

    started = time.monotonic()
    evidence_path = Path(args.evidence).resolve(strict=True)
    evidence = read_json(evidence_path)
    require(evidence["schema_version"] == 1 and evidence["artifact_kind"] == "chance_component_screen"
            and evidence["purpose"] in ("research", "fixture_exercise"), "invalid screen evidence index")
    purpose = evidence["purpose"]
    protocol = evidence["protocol"]
    linked_path(protocol)
    inputs = read_json(linked_path(evidence["study_inputs"]))
    require(inputs["schema_version"] == 1 and inputs["purpose"] == purpose,
            "screen input identity mismatch")
    linked_path(inputs["specification"])
    linked_path(inputs["source_evidence"])
    config_path = linked_path(inputs["config"])
    config = read_json(config_path)
    anchors = [v["model"] for v in inputs["models"] if v["label"] == "anchor"]
    require(len(anchors) == 1, "screen inputs require exactly one saved anchor identity")
    anchor_reference = anchors[0]
    anchor = read_json(linked_path(anchor_reference))
    anchor_content_sha256 = hashlib.sha256(
        json.dumps(anchor, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    require(inputs["resampling"] == dict(draws=2000, seed=3032026, generator="PCG64",
                                         percentile_method="linear", calendar_days=[7, 14]),
            "screen resampling choices changed")
    cells = evidence["cells"]
    expected = {(w, r, q) for w in WINDOWS for r in RECIPES for q in QUANTITIES}
    keyed = {(c["window"], c["recipe"], c["quantity"]): c for c in cells}
    require(len(cells) == 12 and len(keyed) == 12 and set(keyed) == expected,
            "screen must contain exactly the fixed twelve cells")
    output = output_path(args.out, [str(evidence_path.parent), str(config_path.parent)])
    loaded, summaries = {}, []
    current_implementation = None
    for key, cell in keyed.items():
        window, recipe, quantity = key
        selected = inputs["selections"][window]
        training_ref = selected["history" if recipe == "recent_history" else "training"]
        assessment_ref = selected["assessment"]
        require(cell["training_selection"] == training_ref and cell["assessment_selection"] == assessment_ref,
                "fixed matrix training/assessment selections changed")
        training_path = linked_path(training_ref)
        linked_path(assessment_ref)
        training_cohort_ref, assessment_cohort_ref = cell["training_cohort"], cell["assessment_cohort"]
        training_cohort = validate_cohort_document(read_json(linked_path(training_cohort_ref)))
        assessment_cohort = validate_cohort_document(read_json(linked_path(assessment_cohort_ref)))
        require(all(cohort["definition"] == dict(mode="all_source_eligible", required_families=[]) and
                    cohort["quantity"] == quantity and cohort["purpose"] == purpose
                    for cohort in (training_cohort, assessment_cohort)),
                "the twelve-cell screen requires explicit all-source cohorts")
        require(cell["status"] in ("reused", "fitted", "failed"), "invalid screen cell status")
        reused = window == "development" and recipe == "baseline"
        if cell["status"] == "failed":
            require(not reused and cell["component"] is None and cell["evaluation"] is None and
                    cell["diagnostics"] is not None, "failed cell artifact references inconsistent")
            failed = read_json(linked_path(cell["diagnostics"]))
            require(failed["schema_version"] == 3 and
                    failed["preparation_identity"] == PREPARATION_IDENTITY and
                    failed["status"] == "failed" and failed["quantity"] == quantity and
                    failed["stage_design"]["families"] == ["game_additive", "recent_additive"] + (["recent_interactions"] if recipe == "context_interactions" else []) and
                    failed["config_identity"] == inputs["config"] and
                    failed["training_cohort_identity"] == training_cohort_ref and
                    failed["protocol_identity"] == protocol and
                    failed["purpose"] == purpose and failed["diagnostics"]["converged"] is False,
                    "failed cell diagnostics binding mismatch")
            require(next(v for v in failed["inputs"] if v["kind"] == "selection")["sha256"] == training_ref["sha256"],
                    "failed cell training identity mismatch")
            if purpose == "research":
                clean_implementation(failed["implementation"])
            loaded[key] = None
            summaries.append(dict(window=window, recipe=recipe, quantity=quantity, status="failed",
                                  diagnostics=cell["diagnostics"], resources=failed["resources"]))
            continue
        require(cell["status"] == ("reused" if reused else "fitted"), "fixed reused/fitted cell status mismatch")
        component = validate_component(read_json(linked_path(cell["component"])))
        require(component["training_cohort"]["definition"] == training_cohort["definition"] and
                component["training_cohort"]["membership_identity"] == (None if reused else training_cohort_ref) and
                training_cohort["selection"] == component["selection"] and
                training_cohort["inputs"] == component["inputs"] and
                training_cohort["game_dates"] == component["training_game_dates"],
                "component screen training cohort binding mismatch")
        require(component["purpose"] == purpose and component["quantity"] == quantity and
                component["layout"]["design"]["families"] == ["game_additive", "recent_additive"] + (["recent_interactions"] if recipe == "context_interactions" else []) and
                component["protocol_identity"] == protocol and component["config_identity"] == inputs["config"] and
                component["config"] == config, "component matrix/configuration binding mismatch")
        selection = read_json(training_path)
        for corpus in selection["corpora"]:
            corpus["path"] = str((training_path.parent / corpus["path"]).resolve(strict=True))
        selection["history_corpora"] = [
            str((training_path.parent / path).resolve(strict=True))
            for path in selection["history_corpora"]
        ]
        require(component["selection"] == selection and
                next(v for v in component["inputs"] if v["kind"] == "selection")["sha256"] == training_ref["sha256"],
                "component training selection binding mismatch")
        require((component["extraction"] is not None) == reused, "component extraction/fitting origin mismatch")
        if reused:
            require(component["extraction"]["model_content_sha256"] == anchor_content_sha256 and
                    component["implementation"] == anchor["implementation"],
                    "reused component is not the declared anchor extraction")
        evaluation = validate_evaluation(cell["evaluation"], cell["component"], assessment_ref,
                                         protocol, quantity, purpose, component=component,
                                         cohort_reference=assessment_cohort_ref,
                                         arm="baseline" if recipe == "baseline" else "sequence")
        require(not set(component["training_game_dates"]) & set(evaluation["game_dates"]) and
                min(evaluation["game_dates"].values()) > max(component["training_game_dates"].values()),
                "component assessment is overlapping or nonfuture")
        if purpose == "research":
            clean_implementation(evaluation["implementation"])
            clean_implementation(component["implementation"])
            actual = component["extraction"]["implementation"] if reused else component["implementation"]
            clean_implementation(actual)
            require(actual == evaluation["implementation"], "component/evaluation implementation mismatch")
            if current_implementation is None:
                current_implementation = actual
            require(actual == current_implementation, "screen implementations changed")
        loaded[key] = evaluation
        fit_resources = None
        require((cell["diagnostics"] is None) == reused, "fitted cell requires solve diagnostics; reused cell has no new solve")
        if not reused:
            fit_record = read_json(linked_path(cell["diagnostics"]))
            require(fit_record["schema_version"] == 3 and
                    fit_record["preparation_identity"] == component["preparation_identity"] and
                    fit_record["status"] == "fitted" and fit_record["diagnostics"] == component["diagnostics"] and
                    fit_record["purpose"] == purpose and fit_record["quantity"] == quantity and
                    fit_record["stage_design"] == component["layout"]["design"] and
                    fit_record["config_identity"] == inputs["config"] and
                    fit_record["training_cohort_identity"] == training_cohort_ref and
                    fit_record["protocol_identity"] == protocol and
                    fit_record["selection"] == component["selection"] and
                    fit_record["inputs"] == component["inputs"] and
                    fit_record["implementation"] == component["implementation"] and
                    fit_record["training_game_dates"] == component["training_game_dates"],
                    "fit diagnostics and component disagree")
            fit_resources = fit_record["resources"]
        summaries.append(dict(window=window, recipe=recipe, quantity=quantity, status=cell["status"],
                              component=cell["component"], evaluation=cell["evaluation"],
                              metrics=evaluation["metrics"], counts_by_status=evaluation["counts_by_status"],
                              fit_resources=fit_resources, evaluation_resources=evaluation["resources"]))
    comparisons = []
    for window in WINDOWS:
        for recipe in RECIPES[1:]:
            for quantity in QUANTITIES:
                baseline, changed = loaded[window, "baseline", quantity], loaded[window, recipe, quantity]
                paired = None
                if baseline is not None and changed is not None:
                    require(all(baseline[field] == changed[field] for field in
                                ("selection", "inputs", "game_dates", "coverage")),
                            "paired assessment source identities or coverage changed")
                    paired = compare_pair(baseline, changed)
                comparisons.append(dict(window=window, recipe=recipe, quantity=quantity,
                                        status="compared" if paired else "incomplete", comparison=paired))
    output.mkdir()
    document = dict(schema_version=1, artifact_kind="chance_component_comparison", purpose=purpose,
                    implementation=implementation(), evidence=identity(evidence_path), protocol=protocol,
                    study_inputs=evidence["study_inputs"], cells=summaries, comparisons=comparisons,
                    uncertainty=dict(draws=2000, seed=3032026, generator="PCG64",
                                     method="paired whole games and seven/fourteen calendar-day blocks; pooled sums/counts; empty units and final partial blocks retained; 95% linear-percentile intervals",
                                     limitation="pointwise intervals condition on fitted models; omit model-selection and fit uncertainty; undefined draws give null intervals without redraws"),
                    historical_calibration_reference_pp=dict(overall_goal=.25, subgroup_goal=1.0),
                    scientific_assessment="not_performed", resources=resources(started))
    write_json(output / "comparison.json", document)
    figures = save_figures(document, output)
    write_json(output / "completion.json", dict(schema_version=1, comparison=identity(output / "comparison.json"),
                                               figures=[identity(p) for p in figures], scientific_assessment="not_performed"))
    print(f"component comparison complete: {output}; scientific assessment not performed")
    return 0


def save_figures(document, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figures = []
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharex=True)
    for axis, quantity in zip(axes, QUANTITIES, strict=True):
        axis.axvline(0, color="black", lw=1)
        selected = [c for c in document["comparisons"] if c["quantity"] == quantity]
        for index, result in enumerate(selected):
            paired = result["comparison"]
            if paired is None:
                axis.text(0, index, "unavailable", ha="center")
                continue
            for offset, unit, color in ((-.15, "games", "C0"), (0, "calendar_7_day", "C1"),
                                        (.15, "calendar_14_day", "C2")):
                value = paired["delta"]["log_loss"][unit]
                point, interval = value["estimate"], value["interval"]
                if point is None:
                    continue
                if interval is not None:
                    axis.plot(interval, [index + offset] * 2, color=color)
                axis.plot(point, index + offset, "o",
                          color=color, fillstyle="full" if interval is not None else "none", ms=4)
        axis.set(yticks=range(len(selected)), yticklabels=[f"{c['window']} / {c['recipe']}" for c in selected],
                 title=quantity, xlabel="changed − baseline mean goal log loss\n(nats / applicable attempt)")
    fig.suptitle("later-game component screen; whole-game (blue), 7-day (orange), 14-day (green) intervals")
    fig.text(.5, .01, "pointwise 95% intervals condition on fitted models; hollow points have undefined draws; lower is better", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, .94))
    path = output / "paired-loss.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    figures.append(path)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for axis, quantity in zip(axes, QUANTITIES, strict=True):
        for reference in (-.25, .25):
            axis.axhline(reference, color="gray", linestyle="--", lw=.8)
        axis.axhline(0, color="black", lw=1)
        selected = [c for c in document["cells"] if c["quantity"] == quantity]
        for index, cell in enumerate(selected):
            if cell["status"] != "failed":
                axis.plot(index, cell["metrics"]["predicted_minus_observed_pp"], "o", color="C0")
        axis.set(xticks=range(len(selected)), xticklabels=[f"{c['window']}\n{c['recipe']}" for c in selected],
                 title=quantity, ylabel="predicted − observed goal rate (percentage points)")
        axis.tick_params(axis="x", labelrotation=45, labelsize=7)
    fig.suptitle("later-game pooled calibration; component populations differ")
    fig.text(.5, .01, "dashed ±0.25 pp lines: historical 03e overall goal margin; reference only, no new admission rule", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, .94))
    path = output / "pooled-calibration.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    figures.append(path)
    max_bin_count = max((b["count"] for cell in document["cells"] if cell["status"] != "failed"
                         for b in cell["metrics"]["calibration"] if b["count"]), default=1)
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), sharex=True, sharey=True)
    for row, window in enumerate(WINDOWS):
        for column, quantity in enumerate(QUANTITIES):
            axis = axes[row, column]
            axis.axhline(0, color="black", lw=1)
            for reference in (-1, 1):
                axis.axhline(reference, color="gray", linestyle="--", lw=.8)
            for recipe in RECIPES:
                cell = next(c for c in document["cells"] if
                            (c["window"], c["quantity"], c["recipe"]) == (window, quantity, recipe))
                if cell["status"] == "failed":
                    continue
                bins = [b for b in cell["metrics"]["calibration"] if b["count"]]
                axis.scatter([b["predicted_rate"] for b in bins],
                             [100 * (b["predicted_rate"] - b["observed_rate"]) for b in bins],
                             s=[12 + 80 * math.sqrt(b["count"] / max_bin_count) for b in bins],
                             label=recipe, alpha=.75)
            axis.set(title=f"{window} / {quantity}", xlabel="mean predicted goal probability in own fixed bin",
                     ylabel="predicted − observed\n(percentage points)")
            axis.legend(fontsize=7)
    fig.suptitle("later-game fixed-bin calibration; each predictor defines its own twenty cohorts")
    fig.text(.5, .01, "marker area reflects √(bin count), with a visibility floor; one common scale; exact counts in comparison.json\n"
             "all nonempty bins retained; descriptive own cohorts; dashed ±1 pp historical subgroup goal margin is reference only",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .07, 1, .94), h_pad=3)
    path = output / "fixed-bin-calibration.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    figures.append(path)
    return figures


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    for command, options in (
        ("diagnose", ("evidence", "protocol", "out")),
        ("fit-component", ("selection", "cohort", "config", "quantity", "protocol", "out")),
        ("evaluate-component", ("selection", "cohort", "component", "arm", "protocol", "out")),
        ("compare", ("evidence", "out")),
    ):
        child = commands.add_parser(command, allow_abbrev=False)
        for option in options:
            choices = QUANTITIES if option == "quantity" else ("baseline", "sequence") if option == "arm" else None
            child.add_argument(f"--{option}", required=True, action=Once, choices=choices)
    args = parser.parse_args()
    try:
        return {"diagnose": diagnose, "fit-component": fit,
                "evaluate-component": evaluate, "compare": compare}[args.command](args)
    except (InputContractError, OSError, KeyError, TypeError, ValueError) as error:
        print(f"{args.command} failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
