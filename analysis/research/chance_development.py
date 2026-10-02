"""bounded, manual component research; completion never means scientific approval."""

import argparse
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
from hockey_stats.chance_evaluation import (
    PROBABILITY_POPULATIONS, PROBABILITY_SUMS, binary_record, diagnostic_groups,
    summarize_component,
)
from hockey_stats.cli import Once
from chance_review import agrees, calendar_blocks, linked_path, ratio_interval, require

QUANTITIES = ("unblocked_conversion", "all_attempt_recorded_context")
WINDOWS = ("development", "season_transfer")
RECIPES = ("baseline", "context_interactions", "recent_history")
PAIR_FIELDS = (
    "game_id", "source_index", "event_id", "game_date", "season", "source_identity",
    "status", "reasons", "applicable", "observed", "blocked", "goal",
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
    return dict(schema_version=1, purpose=prepared["purpose"], implementation=implementation(),
                inputs=prepared["inputs"], selection=prepared["selection"],
                game_dates=prepared["game_dates"], coverage=prepared["coverage"],
                scientific_assessment="not_performed")


def prediction_row(attempt, prepared, sources):
    gid = attempt["game_id"]
    return dict(
        schema_version=1, game_id=gid, source_index=attempt["source_index"],
        event_id=attempt["event_id"], game_date=prepared["game_dates"][gid],
        season=attempt["season"], source_identity=sources[gid],
        status=attempt["status"], reasons=attempt["reasons"],
        blocked=attempt["blocked"], goal=attempt["goal"],
    )


def source_identities(prepared):
    return {Path(v["path"]).stem: v for v in prepared["inputs"] if v["kind"] == "game"}


def prediction_check(row):
    require(type(row["source_index"]) is int and row["source_index"] >= 0,
            "invalid attempt source index")
    require(row["status"] in ("predicted", "not_applicable", "out_of_scope", "unavailable"),
            "invalid component prediction status")
    require(type(row["applicable"]) is bool, "invalid component applicability")
    require(type(row["blocked"]) is bool and type(row["goal"]) is bool and
            not (row["blocked"] and row["goal"]), "invalid recorded block/goal labels")
    if row["status"] == "predicted":
        require(row["applicable"] and type(row["observed"]) is int and
                row["observed"] == int(row["goal"]), "invalid predicted label")
        record = binary_record(row["observed"], row["log_p"], row["log_not_p"])
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
    from hockey_stats.chance import fit_component

    started = time.monotonic()
    selection = Path(args.selection).resolve(strict=True)
    config_path = Path(args.config).resolve(strict=True)
    protocol = Path(args.protocol).resolve(strict=True)
    prepared = prepare(selection)
    output = output_path(args.out, prepared["input_roots"] +
                         [str(selection.parent), str(config_path.parent), str(protocol.parent)])
    metadata = dict(common(prepared), config_identity=identity(config_path),
                    protocol_identity=identity(protocol), training_game_dates=prepared["game_dates"],
                    training_game_ids=list(prepared["game_dates"]),
                    training_dates=sorted(set(prepared["game_dates"].values())))
    output.mkdir()
    component, diagnostics = fit_component(
        [r for r in prepared["attempts"] if r["status"] == "eligible"],
        read_json(config_path), metadata, quantity=args.quantity, features=args.features,
    )
    document = dict(metadata, artifact_kind="chance_component_fit", quantity=args.quantity,
                    feature_set=args.features, diagnostics=diagnostics,
                    status="fitted" if component is not None else "failed", resources=resources(started))
    write_json(output / "fit.json", document)
    if component is None:
        print(f"component fit failed; diagnostics saved to {output}", file=sys.stderr)
        return 1
    write_json(output / "component.json", component)
    write_json(output / "completion.json", dict(
        artifact_kind="chance_component_fit_completion", schema_version=1,
        fit=identity(output / "fit.json"), component=identity(output / "component.json"),
        scientific_assessment="not_performed"))
    print(f"component fit complete: {output}; scientific assessment not performed")
    return 0


def evaluate(args):
    from hockey_stats.chance import validate_component, component_prediction_context, predict_component

    started = time.monotonic()
    selection = Path(args.selection).resolve(strict=True)
    component_path = Path(args.component).resolve(strict=True)
    component = validate_component(read_json(component_path))
    prepared = prepare(selection)
    require(component["purpose"] == prepared["purpose"], "component and selection purposes disagree")
    training = component["training_game_dates"]
    require(not set(training) & set(prepared["game_dates"]), "assessment game ids overlap training")
    require(min(prepared["game_dates"].values()) > max(training.values()),
            "assessment dates must follow all training dates")
    output = output_path(args.out, prepared["input_roots"] +
                         [str(selection.parent), str(component_path.parent)])
    output.mkdir()
    context = component_prediction_context(component)
    sources = source_identities(prepared)
    component_identity = identity(component_path)
    with (output / "attempts.jsonl").open("x", encoding="utf-8") as destination:
        for attempt in prepared["attempts"]:
            row = prediction_row(attempt, prepared, sources)
            applicable = component["quantity"] != "unblocked_conversion" or not attempt["blocked"]
            row.update(quantity=component["quantity"], component=component_identity,
                       applicable=applicable, observed=None, log_p=None, log_not_p=None,
                       probability=None, season_basis=None, state_season=None, actor_evidence=None)
            if attempt["status"] == "eligible":
                row["status"] = "predicted" if applicable else "not_applicable"
                if applicable:
                    prediction = predict_component(component, attempt, context)
                    row.update(prediction, observed=int(attempt["goal"]),
                               probability=math.exp(prediction["log_p"]))
            row["diagnostic_groups"] = diagnostic_groups(
                attempt, row["game_date"], row["actor_evidence"] or
                {actor: dict(basis=None) for actor in ("shooter", "goalie")})
            destination.write(json.dumps(row, allow_nan=False) + "\n")
    document = dict(common(prepared), artifact_kind="chance_component_evaluation",
                    quantity=component["quantity"], component=component_identity,
                    protocol=component["protocol_identity"], selection_identity=identity(selection),
                    attempts=identity(output / "attempts.jsonl"),
                    **summarize_component(rows(output / "attempts.jsonl"), prepared["game_dates"]),
                    resources=resources(started))
    write_json(output / "evaluation.json", document)
    write_json(output / "completion.json", dict(
        schema_version=1, artifact_kind="chance_component_evaluation_completion",
        evaluation=identity(output / "evaluation.json"), scientific_assessment="not_performed"))
    print(f"component evaluation complete: {output}; scientific assessment not performed")
    return 0


def factual_component_rows(path, quantity, predictor, cohort=None):
    for row in rows(path):
        if cohort is not None and (row["game_id"], row["source_index"]) not in cohort:
            continue
        value = row["predictions"].get(predictor)
        applicable = quantity != "unblocked_conversion" or not row["blocked"]
        yield dict(row, applicable=applicable, diagnostic_groups=row["predictor_groups"][predictor],
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
        require(assessment["schema_version"] == 3, "historical assessment schema 3 required")
        model_path = linked_path(assessment["model"])
        model = validate_model(read_json(model_path))
        context = prediction_context(model)
        model_identity = identity(model_path)
        components, component_contexts = {}, {}
        for quantity in QUANTITIES:
            component = extract_component(model, quantity=quantity)
            component["protocol_identity"] = identity(protocol)
            components[quantity] = component
            component_contexts[quantity] = component_prediction_context(component)
        require(model["purpose"] == "research", "fixture candidate cannot supply scientific diagnosis")
        for population, origin in (("training", model), ("assessment", assessment)):
            selection_ref = next(v for v in origin["inputs"] if v["kind"] == "selection")
            selection_path = linked_path(selection_ref)
            if str(selection_path) not in prepared_cache:
                prepared_cache[str(selection_path)] = prepare(selection_path)
            prepared = prepared_cache[str(selection_path)]
            require(not any(output.is_relative_to(Path(root)) for root in prepared["input_roots"]),
                    "diagnosis output must be outside source input directories")
            require(all(prepared[field] == origin[field] for field in ("selection", "inputs", "game_dates", "coverage")),
                    "saved original population identity changed")
            stream = output / f"{population}-{entry['label']}.jsonl"
            sources = source_identities(prepared)
            extraction_errors = {q: dict(max_abs_log_probability_difference=0.0,
                                         max_abs_probability_difference=0.0) for q in QUANTITIES}
            with stream.open("x", encoding="utf-8") as destination:
                for attempt in prepared["attempts"]:
                    row = prediction_row(attempt, prepared, sources)
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
    left = linked_path(baseline["attempts"])
    right = linked_path(changed["attempts"])
    paired_summary = summarize_component(
        (dict(after, diagnostic_groups=before["diagnostic_groups"])
         for before, after in paired_rows(left, right)), baseline["game_dates"])
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
    return dict(delta=results, baseline_metrics=baseline["metrics"], changed_metrics=changed["metrics"],
                paired_groups=groups,
                group_definition="baseline component defines actor-support memberships for both predictors; own calibration bins remain separate",
                changed_own_groups=changed["groups"], counts_by_status=changed["counts_by_status"])


def validate_evaluation(reference, component_reference, selection_reference, protocol, quantity, purpose):
    document = read_json(linked_path(reference))
    require(document["schema_version"] == 1 and
            document["artifact_kind"] == "chance_component_evaluation" and
            document["purpose"] == purpose and document["quantity"] == quantity and
            document["scientific_assessment"] == "not_performed" and
            document["component"] == component_reference and document["protocol"] == protocol and
            document["selection_identity"] == selection_reference,
            "component evaluation binding mismatch")
    selection_path = linked_path(selection_reference)
    selection = read_json(selection_path)
    for corpus in selection["corpora"]:
        corpus["path"] = str((selection_path.parent / corpus["path"]).resolve(strict=True))
    require(document["selection"] == selection, "evaluation selection content mismatch")
    require([v["game_id"] for v in document["per_game"]] == list(document["game_dates"]),
            "evaluation selected/per-game identities mismatch")
    stream = linked_path(document["attempts"])
    sources = source_identities(document)
    seen = set()
    for row in rows(stream):
        prediction_check(row)
        key = row["game_id"], row["source_index"]
        require(key not in seen and row["game_id"] in document["game_dates"],
                "duplicate or unselected component prediction key")
        seen.add(key)
        require(row["component"] == component_reference and row["quantity"] == quantity and
                row["source_identity"] == sources[row["game_id"]] and
                row["game_date"] == document["game_dates"][row["game_id"]],
                "component prediction source/model identity mismatch")
    summary = summarize_component(rows(stream), document["game_dates"])
    require(summary == {field: document[field] for field in summary},
            "prediction stream and saved evaluation accounting disagree")
    return document


def compare(args):
    from hockey_stats.chance import validate_component
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
        require(cell["status"] in ("reused", "fitted", "failed"), "invalid screen cell status")
        reused = window == "development" and recipe == "baseline"
        if cell["status"] == "failed":
            require(not reused and cell["component"] is None and cell["evaluation"] is None and
                    cell["diagnostics"] is not None, "failed cell artifact references inconsistent")
            failed = read_json(linked_path(cell["diagnostics"]))
            require(failed["status"] == "failed" and failed["quantity"] == quantity and
                    failed["feature_set"] == ("recent_interactions" if recipe == "context_interactions" else "additive") and
                    failed["config_identity"] == inputs["config"] and
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
        require(component["purpose"] == purpose and component["quantity"] == quantity and
                component["feature_set"] == ("recent_interactions" if recipe == "context_interactions" else "additive") and
                component["protocol_identity"] == protocol and component["config_identity"] == inputs["config"] and
                component["config"] == config, "component matrix/configuration binding mismatch")
        selection = read_json(training_path)
        for corpus in selection["corpora"]:
            corpus["path"] = str((training_path.parent / corpus["path"]).resolve(strict=True))
        require(component["selection"] == selection and
                next(v for v in component["inputs"] if v["kind"] == "selection")["sha256"] == training_ref["sha256"],
                "component training selection binding mismatch")
        require((component["extraction"] is not None) == reused, "component extraction/fitting origin mismatch")
        if reused:
            require(component["extraction"]["model_content_sha256"] == anchor_content_sha256 and
                    component["implementation"] == anchor["implementation"],
                    "reused component is not the declared anchor extraction")
        evaluation = validate_evaluation(cell["evaluation"], cell["component"], assessment_ref,
                                         protocol, quantity, purpose)
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
            require(fit_record["status"] == "fitted" and fit_record["diagnostics"] == component["diagnostics"] and
                    fit_record["purpose"] == purpose and fit_record["quantity"] == quantity and
                    fit_record["feature_set"] == component["feature_set"] and
                    fit_record["config_identity"] == inputs["config"] and
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
                 title=quantity, xlabel="changed − baseline mean goal log loss (nats / applicable attempt)")
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
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
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
                axis.plot([b["predicted_rate"] for b in bins],
                          [100 * (b["predicted_rate"] - b["observed_rate"]) for b in bins],
                          "o-", label=recipe, ms=3)
            axis.set(title=f"{window} / {quantity}", xlabel="mean predicted goal probability in own fixed bin",
                     ylabel="predicted − observed goal rate (percentage points)")
            axis.legend(fontsize=7)
    fig.suptitle("later-game fixed-bin calibration; each predictor defines its own twenty cohorts")
    fig.text(.5, .01, "empty bins omitted; descriptive residuals, no joint bin comparison; dashed ±1 pp historical subgroup goal margin is reference only", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, .94))
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
        ("fit-component", ("selection", "config", "quantity", "features", "protocol", "out")),
        ("evaluate-component", ("selection", "component", "out")),
        ("compare", ("evidence", "out")),
    ):
        child = commands.add_parser(command, allow_abbrev=False)
        for option in options:
            choices = QUANTITIES if option == "quantity" else ("additive", "recent_interactions") if option == "features" else None
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
