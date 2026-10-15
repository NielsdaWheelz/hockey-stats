"""fixed mirror-pooling study; saved research evidence never admits a model."""

import argparse
import hashlib
from itertools import zip_longest
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

from hockey_stats.artifacts import (
    agrees, artifact_roots, clean_implementation, implementation, linked_path,
    require, resources, rows, write_json,
)
from hockey_stats.captures import InputContractError
from hockey_stats.chance import (
    component_probe_context, fit_component, free_coefficients, grid, predict_component,
    restricted_component_objective, solve_logistic, spatial_parameterization,
    validate_component, validate_config, validate_spatial_parameterization,
)
from hockey_stats.chance_cli import identity, output_path, read_json
from hockey_stats.chance_components import (
    component_inputs, component_setup, objective_replay, read_component_bundle,
    read_component_fit, validate_prepared_selection, verify_decomposition_pair,
)
from hockey_stats.chance_cohort import validate_cohort_document, validate_target_audit_document
from hockey_stats.chance_data import prepare_core
from hockey_stats.chance_evaluation import (
    COMPOSED_METRICS, add_binary, binary_metrics, binary_record, compare_paired_records,
    compose_logs, composed_rows, composed_summaries, finish_binary,
    metric_rows, paired_additive, paired_composed_rows, paired_samples,
    validate_composed_stream,
)
from hockey_stats.chance_targets import DECOMPOSITION_QUANTITIES as QUANTITIES
from hockey_stats.cli import Once

WINDOWS = ("development", "season_transfer")
ARMS = ("untied", "mirror_y")
COMMON = {"schema_version", "artifact_kind", "purpose", "implementation", "protocol"}
REUSE_FIELDS = {"source_result", "config", "windows", "checks", "resources"}
WINDOW_FIELDS = {"training_selection", "assessment_selection", "training", "assessment",
                 "control_fits", "control_assessment"}
PARAMETER_FIELDS = {"constraint", "quantity", "grid_sha256", "design_sha256", "full_to_free",
                    "full_count", "free_count", "full_spatial_count", "free_spatial_count",
                    "orbit_count", "centreline_count", "penalty", "cell_assignment"}
MAP_FIELDS = PARAMETER_FIELDS - {"quantity", "grid_sha256", "design_sha256"}
FIT_FIELDS = {"window", "quantity", "selection", "config", "cohort", "target_audit",
              "parameterization", "solver", "start_policy", "role", "status", "diagnostics",
              "objective_replay", "resources"}
ASSESSMENT_FIELDS = {"selection", "inputs", "preparation_identity", "game_dates", "coverage",
                     "cohorts", "components", "target_audits", "attempts", "metrics", "groups",
                     "per_game", "resources", "scientific_assessment"}
ASSESSMENT_COMPLETION_FIELDS = {"selection", "components", "cohorts", "target_audits",
                                "assessment", "attempts", "scientific_assessment"}
PRIMARY_SOLVER = dict(method="L-BFGS-B", maxiter=2000, ftol=1e-10, gtol=1e-6)
PROBE_SOLVER = dict(method="L-BFGS-B", maxiter=100, maxfun=400, maxls=20, ftol=1e-12, gtol=1e-8)
RESAMPLING = dict(draws=2000, seed=3032026, generator="PCG64", percentile_method="linear",
                  percentiles=[2.5, 97.5], calendar_days=[7, 14], bootstrap_fits=0)
SOURCE_RESULT_SHA256 = "77ebbcdf7b35101848d15415151a18bab3bdf40c36726d864e9ad616a2280848"
CONFIG_SHA256 = "1a52e1bbb5d9ef736b6781c18cfa66bf3c869817c6da8b6e9d9c741b417c1bf2"
SELECTIONS = {
    ("development", "training"): ("development-short-training.json", "c4b8918f44a88a0bdbc53ed9bfd37f196850cf18823a44e6dbe752118532de5a"),
    ("development", "assessment"): ("development-assessment.json", "30a6e0ae1338e2b68a8d89101d8e0b5e537ee6c4357f78ca5f7a5974aea32791"),
    ("season_transfer", "training"): ("season_transfer-short-training.json", "7b78ea4aaa7bbf0afa7c9f94bd8f54ffeabca51b45a079fe44e293b0a1627db9"),
    ("season_transfer", "assessment"): ("season_transfer-assessment.json", "c99b1e8e43b6d807f3ea326cd87b0e3843fe11ff8da7d601c14a31cc91965905"),
}
TOTALS = {
    ("development", "training"): (1912, 128679, 87618, 7614),
    ("development", "assessment"): (712, 49014, 31658, 2804),
    ("season_transfer", "training"): (2624, 177693, 119276, 10418),
    ("season_transfer", "assessment"): (1312, 87018, 56111, 5291),
}
COUNTS = {"development": {QUANTITIES[0]: 6159, QUANTITIES[1]: 6147},
          "season_transfer": {QUANTITIES[0]: 6335, QUANTITIES[1]: 6317}}
REPORT_GROUPS = ("recent_context", "model_type", "calendar_month", "role",
                 "actor_support:shooter", "actor_support:goalie")
LIMITATIONS = [
    "hard symmetry removes genuine left/right spatial differences; restricting the full penalty is not a new penalty optimum",
    "99% is retention of untied predictive gain over the fixed training-rate forecast, not accuracy or equivalence",
    "95% intervals condition on fitted models, the training reference and selected design; they omit fitting, source and selection uncertainty",
    "research-exposed chronological windows overlap in training and are not independent confirmation",
    "the bounded continuation measures local numerical stability, not distance to the optimum or certified optimization error",
    "fewer independent coefficients are not effective degrees of freedom, extra player components or evidence of player accuracy",
    "source coordinates, recorded outcomes, actor standardization, coverage and origin assumptions retain their prior limitations",
    "nearest-cell tie behavior and nonspatial predictors need not give reflection-equal complete predictions",
    "external-only expensive outputs retain accepted manual rerun risk; nomination is not admission or publication",
]


def study_output(value, roots, purpose):
    output = output_path(value, roots)
    require(purpose != "research" or output.is_relative_to(Path("/Volumes/Expansion/hockey-stats")),
            "research outputs must use the assigned external storage")
    return output


def envelope(kind, purpose, protocol, **fields):
    current = implementation()
    if purpose == "research":
        clean_implementation(current)
    return dict(schema_version=1, artifact_kind=f"chance_mirror_{kind}", purpose=purpose,
                implementation=current, protocol=protocol, **fields)


def document(reference, kind, fields, *, purpose, protocol):
    value = read_json(linked_path(reference))
    require(isinstance(value, dict) and set(value) == COMMON | set(fields) and
            type(value["schema_version"]) is int and value["schema_version"] == 1 and
            value["artifact_kind"] == f"chance_mirror_{kind}" and value["purpose"] == purpose and
            value["protocol"] == protocol and value["implementation"] == implementation(),
            f"invalid mirror {kind} schema, purpose, protocol or implementation")
    if purpose == "research":
        clean_implementation(value["implementation"])
    return value


def completed(reference, kind, fields, *, purpose, protocol):
    value = document(reference, f"{kind}_completion", set(fields) | {"scientific_assessment"},
                     purpose=purpose, protocol=protocol)
    require(value["scientific_assessment"] == "not_performed", "completion cannot assert scientific support")
    return value


def parameter_fields(component, constraint):
    layout = component["layout"]
    result = spatial_parameterization(layout, grid()[0], constraint)
    result.update(quantity=component["quantity"], **{
        f"{name}_sha256": hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                                    allow_nan=False).encode()).hexdigest()
        for name, value in (("grid", component["grid"]), ("design", layout["design"]))})
    return result


def read_parameter(reference, component, constraint, *, purpose, protocol):
    value = document(reference, "parameterization", PARAMETER_FIELDS, purpose=purpose, protocol=protocol)
    expected = parameter_fields(component, constraint)
    require({key: value[key] for key in PARAMETER_FIELDS} == expected,
            "parameterization differs from native grid/design/constraint")
    core = {key: value[key] for key in MAP_FIELDS}
    validate_spatial_parameterization(component["layout"], grid()[0], core)
    free_coefficients(component["layout"]["coefficients"], core)
    return core


def validate_reuse_inputs(value):
    require(isinstance(value, dict) and set(value) == {"schema_version", "purpose", "source_result", "config", "windows"}
            and type(value["schema_version"]) is int and value["schema_version"] == 1 and
            value["purpose"] in ("research", "fixture_exercise") and
            isinstance(value["windows"], dict) and set(value["windows"]) == set(WINDOWS),
            "invalid mirror reuse input schema")
    purpose = value["purpose"]
    config = validate_config(read_json(linked_path(value["config"])))
    source = None
    if purpose == "research":
        require(value["source_result"] is not None and value["source_result"]["sha256"] == SOURCE_RESULT_SHA256
                and value["config"] == dict(path="/Volumes/Expansion/hockey-stats/runs/chance-03n-20261013/inputs/config.json",
                                            sha256=CONFIG_SHA256), "research must bind the original 03o result/config")
        source = read_json(linked_path(value["source_result"]))
        require(source["artifact_kind"] == "chance_decomposition_result" and source["execution_status"] == "complete"
                and source["purpose"] == purpose, "original decomposition result is incomplete")
        clean_implementation(source["implementation"])
    else:
        require(value["source_result"] is None, "fixture controls have no research source result")
    require(config["trait_assumptions"] == [] and
            config["stage_families"]["r"] == ["game_additive", "recent_additive", "recent_interactions"] and
            all(config[key] == expected for key, expected in {
                "ridge_cell": .25, "ridge_type_cell": 1, "smooth_cell": 4, "ridge_context": 4,
                "ridge_shooter": 4, "change_shooter": 16, "ridge_goalie": 16, "change_goalie": 64,
                "optimizer_max_iterations": 2000, "optimizer_ftol": 1e-10, "optimizer_gtol": 1e-6}.items()),
            "mirror study requires the fixed native recipe")
    for window in WINDOWS:
        entry = value["windows"][window]
        require(isinstance(entry, dict) and set(entry) == WINDOW_FIELDS, "invalid reuse window fields")
        for partition in ("training", "assessment"):
            require(isinstance(entry[partition], dict) and set(entry[partition]) == set(QUANTITIES),
                    "both stage cohort bundles are required")
            require(all(isinstance(bundle, dict) and set(bundle) == {"cohort", "outcome_audit", "target_audit"}
                        for bundle in entry[partition].values()), "invalid source cohort bundle fields")
            if purpose == "research":
                filename, digest = SELECTIONS[window, partition]
                require(entry[f"{partition}_selection"] == dict(
                    path=f"/Volumes/Expansion/hockey-stats/runs/chance-03n-20261013/inputs/{filename}", sha256=digest),
                    "research changed an original selection")
        require(isinstance(entry["control_fits"], dict) and set(entry["control_fits"]) == set(QUANTITIES),
                "both original stage fit completions are required")
        if source is not None:
            for quantity in QUANTITIES:
                cell = source["cells"][window][quantity]
                require(cell["status"] == "complete" and cell["fit"] == entry["control_fits"][quantity] and
                        cell["cohort"] == entry["training"][quantity]["cohort"] and
                        cell["target_audit"] == entry["training"][quantity]["target_audit"],
                        "control fit/cohort/target differs from original result")
            require(source["cells"][window]["assessment"]["completion"] == entry["control_assessment"],
                    "control composed stream differs from original result")
    artifact_roots(value)
    return source, config


def partition_inputs(entry, partition, purpose, *, window):
    selection = linked_path(entry[f"{partition}_selection"])
    prepared = prepare_core(selection)
    validate_prepared_selection(prepared, selection)
    require(prepared["purpose"] == purpose, "selected source purpose mismatch")
    cohorts, audits, targets = {}, {}, {}
    for quantity in QUANTITIES:
        cohorts[quantity], audits[quantity], targets[quantity] = read_component_bundle(
            entry[partition][quantity], prepared, quantity)
    verify_decomposition_pair(prepared, cohorts)
    target = targets[QUANTITIES[0]]["counts"]
    counts = dict(games=len(prepared["game_dates"]), unblocked=target["unblocked"],
                  on_net=target["on_net"], goals=target["goals"])
    if purpose == "research":
        require(tuple(counts.values()) == TOTALS[window, partition], "original source population counts changed")
    return prepared, cohorts, audits, targets, counts


def read_control_assessment(reference, entry, components, component_refs, *, purpose, protocol,
                            prepared=None, cohorts=None, summarize=True):
    complete = read_json(linked_path(reference))
    require(isinstance(complete, dict) and set(complete) == COMMON | ASSESSMENT_COMPLETION_FIELDS and
            type(complete["schema_version"]) is int and complete["schema_version"] == 1 and complete["artifact_kind"] == "chance_decomposition_assessment_completion"
            and complete["purpose"] == purpose and complete["protocol"] == protocol and
            complete["scientific_assessment"] == "not_performed", "invalid original composed completion")
    saved = read_json(linked_path(complete["assessment"]))
    require(isinstance(saved, dict) and set(saved) == COMMON | ASSESSMENT_FIELDS and
            type(saved["schema_version"]) is int and saved["schema_version"] == 1 and saved["artifact_kind"] == "chance_decomposition_assessment" and
            saved["purpose"] == purpose and saved["protocol"] == protocol and
            saved["implementation"] == complete["implementation"] and
            saved["scientific_assessment"] == "not_performed" and
            all(saved[field] == complete[field] for field in
                ("selection", "components", "cohorts", "target_audits", "attempts")) and
            saved["components"] == component_refs and saved["selection"] == entry["assessment_selection"] and
            saved["cohorts"] == {q: entry["assessment"][q]["cohort"] for q in QUANTITIES} and
            saved["target_audits"] == {q: entry["assessment"][q]["target_audit"] for q in QUANTITIES},
            "original composed assessment bindings changed")
    if purpose == "research":
        clean_implementation(saved["implementation"])
    replay = None
    if prepared is not None:
        require(all(saved[field] == prepared[field] for field in
                    ("purpose", "inputs", "preparation_identity", "game_dates", "coverage")),
                "original assessment changed source preparation or coverage")
        replay = validate_composed_stream(linked_path(saved["attempts"]), prepared, cohorts, components)
    if summarize:
        summary = composed_summaries(linked_path(saved["attempts"]), saved["game_dates"])
        require(all(saved[field] == {metric: summary[metric][field] for metric in COMPOSED_METRICS}
                    for field in ("metrics", "groups", "per_game")), "original assessment summaries differ from stream")
    return saved, replay


def reuse_command(args):
    started = time.monotonic()
    inputs_path, protocol_path = Path(args.inputs).resolve(strict=True), Path(args.protocol).resolve(strict=True)
    inputs = read_json(inputs_path)
    source, config = validate_reuse_inputs(inputs)
    purpose, protocol = inputs["purpose"], identity(protocol_path)
    output = study_output(args.out, artifact_roots(inputs) + [str(inputs_path.parent), str(protocol_path.parent)], purpose)
    current = envelope("reuse", purpose, protocol)
    output.mkdir()
    checks = {}
    for window in WINDOWS:
        entry = inputs["windows"][window]
        prepared, cohorts, audits, targets, counts = partition_inputs(entry, "training", purpose, window=window)
        components, component_refs, objectives, parameterizations = {}, {}, {}, {}
        for quantity in QUANTITIES:
            original_completion = read_json(linked_path(entry["control_fits"][quantity]))
            original_protocol = original_completion["protocol"]
            if source is not None:
                require(original_protocol == source["protocol"], "control protocol differs from original result")
            completed_fit, component, _ = read_component_fit(
                entry["control_fits"][quantity], entry["training"][quantity]["cohort"], cohorts[quantity], audits[quantity],
                config=inputs["config"], protocol=original_protocol, quantity=quantity, purpose=purpose,
                expected_implementation=source["implementation"] if source else None, coverage=prepared["coverage"])
            components[quantity], component_refs[quantity] = component, completed_fit["component"]
            fields = parameter_fields(component, "untied")
            parameter_path = output / f"{window}-{quantity}-parameterization.json"
            write_json(parameter_path, envelope("parameterization", purpose, protocol, **fields))
            parameterizations[quantity] = identity(parameter_path)
            if purpose == "research":
                require(fields["full_count"] == COUNTS[window][quantity], "original control coefficient count changed")
            objectives[quantity] = objective_replay(
                component, prepared, cohorts[quantity], component_reference=completed_fit["component"],
                cohort_reference=entry["training"][quantity]["cohort"], protocol=original_protocol,
                parameterization={key: fields[key] for key in MAP_FIELDS})
        del prepared, cohorts, audits, targets
        prepared, cohorts, _, targets, assessment_counts = partition_inputs(entry, "assessment", purpose, window=window)
        original_protocol = read_json(linked_path(entry["control_assessment"]))["protocol"]
        require(all(component["protocol_identity"] == original_protocol for component in components.values()),
                "control stages and assessment use different original protocols")
        assessed, replay = read_control_assessment(
            entry["control_assessment"], entry, components, component_refs, purpose=purpose,
            protocol=original_protocol, prepared=prepared, cohorts=cohorts)
        checks[window] = dict(training=counts, assessment=assessment_counts,
                              objectives=objectives, parameterizations=parameterizations,
                              components=component_refs, original_protocol=original_protocol,
                              assessment_document=read_json(linked_path(entry["control_assessment"]))["assessment"],
                              attempts=assessed["attempts"], stream_replay=replay)
        del prepared, cohorts, targets, components
    current.update(source_result=inputs["source_result"], config=inputs["config"], windows=inputs["windows"],
                   checks=checks, resources=resources(started))
    write_json(output / "reuse.json", current)
    write_json(output / "completion.json", envelope("reuse_completion", purpose, protocol,
        reuse=identity(output / "reuse.json"), scientific_assessment="not_performed"))
    return 0


def read_reuse(reference, protocol):
    completion_value = read_json(linked_path(reference))
    purpose = completion_value.get("purpose")
    require(purpose in ("research", "fixture_exercise"), "invalid reuse purpose")
    complete = completed(reference, "reuse", {"reuse"}, purpose=purpose, protocol=protocol)
    value = document(complete["reuse"], "reuse", REUSE_FIELDS, purpose=purpose, protocol=protocol)
    validate_reuse_inputs(dict(schema_version=1, purpose=purpose,
                               **{key: value[key] for key in ("source_result", "config", "windows")}))
    require(isinstance(value["checks"], dict) and set(value["checks"]) == set(WINDOWS), "reuse receipts are incomplete")
    for window in WINDOWS:
        check = value["checks"][window]
        require(set(check) == {"training", "assessment", "objectives", "parameterizations", "components",
                               "original_protocol", "assessment_document", "attempts", "stream_replay"} and
                check["stream_replay"]["source_labels_dispositions_order"] == "verified" and
                check["stream_replay"]["native_predictions"] == "verified", "reuse source/objective receipts incomplete")
        require(all(isinstance(check[key], dict) and set(check[key]) == set(QUANTITIES)
                    for key in ("objectives", "parameterizations", "components")), "reuse requires exactly both stage receipts")
        artifact_roots(check)
        entry = value["windows"][window]
        components = {}
        for partition in ("training", "assessment"):
            targets, cohorts = {}, {}
            for quantity in QUANTITIES:
                bundle = entry[partition][quantity]
                cohorts[quantity] = validate_cohort_document(read_json(linked_path(bundle["cohort"])))
                targets[quantity] = validate_target_audit_document(read_json(linked_path(bundle["target_audit"])), cohorts[quantity])
                require(targets[quantity]["cohort"] == bundle["cohort"] and
                        targets[quantity]["selection"] == entry[f"{partition}_selection"] and
                        targets[quantity]["quantity"] == quantity, "reuse target audit belongs to a different source bundle")
            expected_counts = dict(games=len(cohorts[QUANTITIES[0]]["game_dates"]), **{
                key: targets[QUANTITIES[0]]["counts"][key] for key in ("unblocked", "on_net", "goals")})
            require(check[partition] == expected_counts and all(type(n) is int and n >= 0 for n in check[partition].values()),
                    "reuse population receipt differs from bound source target audit")
            if partition == "assessment":
                require(check["stream_replay"] == dict(recognized=len(cohorts[QUANTITIES[0]]["rows"]),
                    included=expected_counts["unblocked"], goals=expected_counts["goals"],
                    source_labels_dispositions_order="verified", native_predictions="verified", prediction_absolute_tolerance=1e-12),
                    "reuse ordered-stream receipt differs from actual source ledger")
        for quantity in QUANTITIES:
            complete_fit = read_json(linked_path(entry["control_fits"][quantity]))
            require(complete_fit["component"] == check["components"][quantity] and
                    complete_fit["protocol"] == check["original_protocol"] and
                    complete_fit["selection"] == entry["training_selection"] and complete_fit["config"] == value["config"] and
                    complete_fit["training_cohort"] == entry["training"][quantity]["cohort"],
                    "reuse control receipt differs from original native completion")
            component = validate_component(read_json(linked_path(check["components"][quantity])))
            components[quantity] = component
            parameterization = read_parameter(check["parameterizations"][quantity], component, "untied", purpose=purpose, protocol=protocol)
            validate_objective_receipt(check["objectives"][quantity], component, check["components"][quantity],
                                       entry["training"][quantity]["cohort"], parameterization)
        complete_assessment = read_json(linked_path(entry["control_assessment"]))
        assessed, _ = read_control_assessment(entry["control_assessment"], entry, components, check["components"],
            purpose=purpose, protocol=check["original_protocol"], summarize=False)
        require(check["assessment_document"] == complete_assessment["assessment"] and check["attempts"] == assessed["attempts"],
                "reuse source-stream receipt differs from original composed completion")
    return value


def fit_command(args):
    started = time.monotonic()
    protocol = identity(Path(args.protocol).resolve(strict=True))
    reuse_ref = identity(Path(args.reuse).resolve(strict=True))
    reuse = read_reuse(reuse_ref, protocol)
    purpose, entry = reuse["purpose"], reuse["windows"][args.window]
    prepared, cohorts, _, _, _ = partition_inputs(entry, "training", purpose, window=args.window)
    quantity = args.quantity
    config = read_json(linked_path(reuse["config"]))
    inputs = component_inputs(prepared, cohorts[quantity], config, reuse["config"], protocol,
                              entry["training"][quantity]["cohort"])
    output = study_output(args.out, prepared["input_roots"] + artifact_roots(reuse) + artifact_roots(reuse_ref) +
                          [str(Path(args.protocol).resolve().parent)], purpose)
    output.mkdir()
    component, diagnostics = fit_component(**inputs, constraint="mirror_y")
    if component is None:
        write_json(output / "fit.json", envelope("fit", purpose, protocol,
            window=args.window, quantity=quantity, selection=entry["training_selection"], config=reuse["config"],
            cohort=entry["training"][quantity]["cohort"], target_audit=entry["training"][quantity]["target_audit"],
            parameterization=None, solver=PRIMARY_SOLVER, start_policy="empirical_intercept", role="primary",
            status="failed", diagnostics=diagnostics, objective_replay=None, resources=resources(started)))
        return 1
    fields = parameter_fields(component, "mirror_y")
    if purpose == "research":
        require(fields["full_count"] == COUNTS[args.window][quantity] and
                fields["free_count"] == fields["full_count"] - 1848, "mirror coefficient count differs from fixed design")
    write_json(output / "parameterization.json", envelope("parameterization", purpose, protocol, **fields))
    write_json(output / "component.json", component)
    parameterization = identity(output / "parameterization.json")
    replay = objective_replay(component, prepared, cohorts[quantity],
        component_reference=identity(output / "component.json"), cohort_reference=entry["training"][quantity]["cohort"],
        protocol=protocol, parameterization={key: fields[key] for key in MAP_FIELDS})
    write_json(output / "fit.json", envelope("fit", purpose, protocol,
        window=args.window, quantity=quantity, selection=entry["training_selection"], config=reuse["config"],
        cohort=entry["training"][quantity]["cohort"], target_audit=entry["training"][quantity]["target_audit"],
        parameterization=parameterization, solver=PRIMARY_SOLVER, start_policy="empirical_intercept", role="primary",
        status="fitted", diagnostics=diagnostics, objective_replay=replay, resources=resources(started)))
    write_json(output / "completion.json", envelope("fit_completion", purpose, protocol,
        window=args.window, quantity=quantity, selection=entry["training_selection"], config=reuse["config"],
        cohort=entry["training"][quantity]["cohort"], target_audit=entry["training"][quantity]["target_audit"],
        parameterization=parameterization, component=identity(output / "component.json"),
        fit=identity(output / "fit.json"), scientific_assessment="not_performed"))
    return 0


def read_fit(reference, reuse, window, quantity, protocol):
    purpose, entry = reuse["purpose"], reuse["windows"][window]
    complete = completed(reference, "fit", {"window", "quantity", "selection", "config", "cohort", "target_audit",
                                            "parameterization", "component", "fit"}, purpose=purpose, protocol=protocol)
    saved = document(complete["fit"], "fit", FIT_FIELDS, purpose=purpose, protocol=protocol)
    expected = dict(window=window, quantity=quantity, selection=entry["training_selection"], config=reuse["config"],
                    cohort=entry["training"][quantity]["cohort"], target_audit=entry["training"][quantity]["target_audit"])
    require(all(saved[key] == complete[key] == value for key, value in expected.items()) and
            saved["parameterization"] == complete["parameterization"] and saved["solver"] == PRIMARY_SOLVER and
            saved["start_policy"] == "empirical_intercept" and saved["role"] == "primary" and saved["status"] == "fitted",
            "mirror primary fit source/solver/role differs")
    component = validate_component(read_json(linked_path(complete["component"])))
    cohort = read_json(linked_path(expected["cohort"]))
    require(component["purpose"] == purpose and component["quantity"] == quantity and
            component["protocol_identity"] == protocol and component["config_identity"] == reuse["config"] and
            component["config"] == read_json(linked_path(reuse["config"])) and
            component["implementation"] == complete["implementation"] and component["extraction"] is None and
            component["training_cohort"]["membership_identity"] == expected["cohort"] and
            component["diagnostics"] == saved["diagnostics"] and component["diagnostics"]["converged"] is True and
            all(component[key] == cohort[key] for key in ("selection", "inputs", "preparation_identity")) and
            component["training_game_dates"] == cohort["game_dates"], "native mirror component bindings differ")
    parameterization = read_parameter(complete["parameterization"], component, "mirror_y", purpose=purpose, protocol=protocol)
    validate_objective_receipt(saved["objective_replay"], component, complete["component"], expected["cohort"], parameterization)
    return complete, component, parameterization


def evaluate_command(args):
    started = time.monotonic()
    protocol = identity(Path(args.protocol).resolve(strict=True))
    reuse_ref = identity(Path(args.reuse).resolve(strict=True))
    reuse = read_reuse(reuse_ref, protocol)
    purpose, entry = reuse["purpose"], reuse["windows"][args.window]
    fits = {QUANTITIES[0]: identity(Path(args.on_net_fit).resolve(strict=True)),
            QUANTITIES[1]: identity(Path(args.conversion_fit).resolve(strict=True))}
    components, component_refs, parameters = {}, {}, {}
    for quantity in QUANTITIES:
        complete, components[quantity], _ = read_fit(fits[quantity], reuse, args.window, quantity, protocol)
        component_refs[quantity], parameters[quantity] = complete["component"], complete["parameterization"]
    prepared, cohorts, _, _, _ = partition_inputs(entry, "assessment", purpose, window=args.window)
    output = study_output(args.out, prepared["input_roots"] + artifact_roots(reuse) + artifact_roots(fits) +
                          artifact_roots(reuse_ref) + [str(Path(args.protocol).resolve().parent)], purpose)
    output.mkdir()
    stream = output / "attempts.jsonl"
    with stream.open("x", encoding="utf-8") as destination:
        for row in composed_rows(prepared, cohorts, components):
            destination.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")
    # this source replay is retained by the hashed completion; report joins it to the reused source stream.
    replay = validate_composed_stream(stream, prepared, cohorts, components)
    for _ in paired_composed_rows(linked_path(reuse["checks"][args.window]["attempts"]), stream):
        pass
    summary = composed_summaries(stream, prepared["game_dates"])
    fields = dict(selection=entry["assessment_selection"], components=component_refs,
                  cohorts={q: entry["assessment"][q]["cohort"] for q in QUANTITIES},
                  target_audits={q: entry["assessment"][q]["target_audit"] for q in QUANTITIES},
                  fits=fits, parameterizations=parameters, attempts=identity(stream), scientific_assessment="not_performed")
    fields["source_replay"] = dict(selection=fields["selection"], cohorts=fields["cohorts"],
                                 components=component_refs, parameterizations=parameters,
                                 attempts=fields["attempts"], checks=replay)
    write_json(output / "assessment.json", envelope("assessment", purpose, protocol, **fields,
        **{field: prepared[field] for field in ("inputs", "preparation_identity", "game_dates", "coverage")},
        **{field: {metric: summary[metric][field] for metric in COMPOSED_METRICS}
           for field in ("metrics", "groups", "per_game")}, resources=resources(started)))
    write_json(output / "completion.json", envelope("assessment_completion", purpose, protocol, **fields,
        window=args.window, assessment=identity(output / "assessment.json")))
    return 0

def read_assessment(reference, reuse, window, fits, protocol):
    purpose, entry = reuse["purpose"], reuse["windows"][window]
    complete = completed(reference, "assessment", ASSESSMENT_COMPLETION_FIELDS |
                         {"window", "fits", "parameterizations", "source_replay"} - {"scientific_assessment"},
                         purpose=purpose, protocol=protocol)
    saved = document(complete["assessment"], "assessment", ASSESSMENT_FIELDS | {"fits", "parameterizations", "source_replay"},
                     purpose=purpose, protocol=protocol)
    require(complete["window"] == window and saved["fits"] == complete["fits"] == fits and
            saved["scientific_assessment"] == "not_performed" and
            all(saved[key] == complete[key] for key in ASSESSMENT_COMPLETION_FIELDS - {"assessment"}) and
            saved["parameterizations"] == complete["parameterizations"] and
            saved["selection"] == entry["assessment_selection"] and
            saved["cohorts"] == {q: entry["assessment"][q]["cohort"] for q in QUANTITIES} and
            saved["target_audits"] == {q: entry["assessment"][q]["target_audit"] for q in QUANTITIES},
            "mirror assessment completion/source/fit binding differs")
    for quantity in QUANTITIES:
        fitted, _, _ = read_fit(fits[quantity], reuse, window, quantity, protocol)
        require(fitted["component"] == saved["components"][quantity] and
                fitted["parameterization"] == saved["parameterizations"][quantity],
                "assessment component/constraint differs from its primary fit")
    replay = saved["source_replay"]
    require(isinstance(replay, dict) and set(replay) ==
            {"selection", "cohorts", "components", "parameterizations", "attempts", "checks"} and
            replay == complete["source_replay"] and
            all(replay[key] == saved[key] for key in ("selection", "cohorts", "components", "parameterizations", "attempts")) and
            replay["checks"] == reuse["checks"][window]["stream_replay"] and
            all(type(replay["checks"][key]) is int for key in ("recognized", "included", "goals")),
            "assessment source/native prediction replay receipt differs")
    control = read_json(linked_path(reuse["checks"][window]["assessment_document"]))
    require(all(saved[field] == control[field] for field in
                ("purpose", "selection", "inputs", "preparation_identity", "game_dates", "coverage", "cohorts", "target_audits")),
            "assessment differs from verified source receipt")
    for _ in paired_composed_rows(linked_path(control["attempts"]), linked_path(saved["attempts"])):
        pass
    summary = composed_summaries(linked_path(saved["attempts"]), saved["game_dates"])
    require(all(saved[field] == {metric: summary[metric][field] for metric in COMPOSED_METRICS}
                for field in ("metrics", "groups", "per_game")), "assessment sums differ from its actual stream")
    return saved, summary


def matrix_inputs(path, *, report):
    value = read_json(path)
    fields = {"schema_version", "purpose", "reuse", "windows"} | ({"numerics"} if report else set())
    require(isinstance(value, dict) and set(value) == fields and type(value["schema_version"]) is int and
            value["schema_version"] == 1 and value["purpose"] in ("research", "fixture_exercise") and
            isinstance(value["windows"], dict) and set(value["windows"]) == set(WINDOWS), "invalid mirror matrix schema")
    cells = [value["reuse"]]
    for window in WINDOWS:
        require(isinstance(value["windows"][window], dict) and
                set(value["windows"][window]) == set(QUANTITIES) | {"assessment"}, "invalid fixed primary matrix cells")
        cells.extend(value["windows"][window][key] for key in (*QUANTITIES, "assessment"))
    if report:
        cells.append(value["numerics"])
    for cell in cells:
        require(isinstance(cell, dict) and set(cell) == {"status", "completion", "failure", "stop_reason"} and
                cell["status"] in ("complete", "failed", "not_run"), "invalid matrix completion cell")
        if cell["status"] == "complete":
            require(cell["completion"] is not None and cell["failure"] is None and cell["stop_reason"] is None,
                    "completed matrix cell requires one completion and no failure/reason")
            linked_path(cell["completion"])
        else:
            require(cell["completion"] is None and isinstance(cell["stop_reason"], str) and bool(cell["stop_reason"]),
                    "unfinished matrix cell requires a located reason")
            if cell["status"] == "failed":
                require(cell["failure"] is not None, "failed matrix cell requires a failure artifact")
                linked_path(cell["failure"])
            else:
                require(cell["failure"] is None, "not-run cell has no failed execution artifact")
    if not report:
        require(all(cell["status"] == "complete" for cell in cells), "numerics requires a completed primary matrix")
    return value


def classify_reference(result):
    d, c = result["D"], result["c"]
    if d is None or d <= 0 or any(
        result["intervals"][quantity][unit]["interval"] is None
        for quantity in ("D", "c") for unit in result["intervals"][quantity]
    ) or any(item["interval"][0] <= 0 for item in result["intervals"]["D"].values()):
        return "reference_unusable"
    if c <= 0 and all(item["interval"][1] <= 0 for item in result["intervals"]["c"].values()):
        return "within_budget"
    if c > 0 and all(item["interval"][0] > 0 for item in result["intervals"]["c"].values()):
        return "exceeds_budget"
    return "inconclusive"


def contrast(losses, counts, game_dates, samples):
    """the constant is fixed; its assessed additive loss stays inside every draw."""
    counts = np.asarray(counts, dtype=np.int64)
    constant, untied, mirror = (np.asarray(losses[key], dtype=float) for key in ("constant", "untied", "mirror_y"))
    require(all(array.shape == counts.shape for array in (constant, untied, mirror)) and
            all(np.isfinite(array).all() for array in (constant, untied, mirror)) and (counts >= 0).all(),
            "invalid complete paired game losses")
    numerators = dict(D=constant - untied, A=.01 * (constant - untied), delta=mirror - untied,
                      c=mirror - .99 * untied - .01 * constant)
    intervals = {key: paired_additive(value, counts, game_dates, samples=samples) for key, value in numerators.items()}
    n = int(counts.sum())
    result = dict(count=n, losses={key: float(np.sum(value) / n) if n else None for key, value in losses.items()},
                  **{key: value["games"]["estimate"] for key, value in intervals.items()}, intervals=intervals)
    result["status"] = classify_reference(result)
    result["reference_status"] = "unusable" if result["status"] == "reference_unusable" else "usable"
    return result


def primary_comparison(control, mirror, training, *, samples):
    p0 = training["goals"] / training["unblocked"]
    require(0 < p0 < 1, "training-rate constant requires both goal outcomes")
    ids, counts = list(control["game_dates"]), []
    losses = {key: [] for key in ("constant", "untied", "mirror_y")}
    for gid, before, after in zip(ids, control["per_game"]["composed_goal"], mirror["per_game"]["composed_goal"], strict=True):
        require(before["game_id"] == after["game_id"] == gid and
                before["metrics"]["count"] == after["metrics"]["count"] and
                before["metrics"]["observed_positive_count"] == after["metrics"]["observed_positive_count"],
                "paired per-game goal source accounting differs")
        n, goals = before["metrics"]["count"], before["metrics"]["observed_positive_count"]
        counts.append(n)
        losses["constant"].append(-goals * math.log(p0) - (n - goals) * math.log1p(-p0))
        losses["untied"].append(before["metrics"]["log_loss_sum"])
        losses["mirror_y"].append(after["metrics"]["log_loss_sum"])
    result = contrast(losses, counts, control["game_dates"], samples)
    result.update(p0=p0, population=dict(games=len(ids), unblocked=sum(counts),
                                        goals=control["metrics"]["composed_goal"]["observed_positive_count"],
                                        on_net=control["metrics"]["on_net"]["observed_positive_count"]))
    return result, losses, counts


def diagnostics(control, mirror):
    result = {}
    for metric in COMPOSED_METRICS:
        summaries = []
        for saved in (control, mirror):
            summary = dict(game_dates=saved["game_dates"], metrics=saved["metrics"][metric],
                           per_game=saved["per_game"][metric], counts_by_status={},
                           groups={key: value for key, value in saved["groups"][metric].items() if key in REPORT_GROUPS})
            summaries.append(summary)
        pairs = zip(metric_rows(rows(linked_path(control["attempts"])), metric),
                    metric_rows(rows(linked_path(mirror["attempts"])), metric), strict=True)
        compared = compare_paired_records(*summaries, pairs, resampling=False)
        result[metric] = dict(
            untied=summaries[0]["metrics"], mirror_y=summaries[1]["metrics"],
            own_groups=dict(untied=summaries[0]["groups"], mirror_y=summaries[1]["groups"]),
            paired_groups=compared["paired_groups"], paired_calibration=compared["paired_calibration"],
            paired_definition="untied probability bins and stage-specific actor support; product has no combined actor groups")
    return result


def combined_status(statuses):
    if any(value == "incomplete" for value in statuses):
        return "incomplete"
    if any(value == "exceeds_budget" for value in statuses):
        return "exceeds_budget"
    if any(value == "reference_unusable" for value in statuses):
        return "reference_unusable"
    return "within_budget" if all(value == "within_budget" for value in statuses) else "inconclusive"

PROBE_FIELDS = {"role", "window", "arm", "quantity", "source_fit", "source_component", "parameterization",
                "solver", "termination", "iterations", "evaluations", "coefficients", "objective",
                "free_gradient_max", "valid", "missing_reason"}


def endpoint_reason(termination, objective, initial_objective, finite):
    if not finite or objective is None or not math.isfinite(objective):
        return "nonfinite diagnostic endpoint"
    normal = termination["status"] == 0 and termination["converged"] and termination["message"].startswith("CONVERGENCE:")
    capped = termination["status"] == 1 and termination["message"] in (
        "STOP: TOTAL NO. OF ITERATIONS REACHED LIMIT", "STOP: TOTAL NO. OF F,G EVALUATIONS EXCEEDS LIMIT")
    if not (normal or capped):
        return "abnormal diagnostic termination"
    if objective > initial_objective and not agrees(objective, initial_objective):
        return "diagnostic training objective increased"
    return None


def probe_component(component, parameterization, prepared, cohort, *, source_fit, source_component,
                    parameter_reference, window, arm, protocol, output):
    layout, data, centers, edges, initial = component_setup(
        prepared, cohort, component["config"], component["config_identity"], component["protocol_identity"],
        component["training_cohort"]["membership_identity"])
    require(data is not None and initial is not None, "probe requires the source target population")
    require(layout == {key: value for key, value in component["layout"].items() if key not in ("coefficients", "diagnostics")},
            "probe source design or actor support changed")
    theta = free_coefficients(component["layout"]["coefficients"], parameterization)
    objective = lambda value: restricted_component_objective(value, data, layout, component["config"], edges, centers, parameterization)
    before, before_gradient = objective(theta)
    require(agrees(before, component["diagnostics"]["objective"]) and np.isfinite(before_gradient).all(),
            "probe start differs from saved native objective")
    endpoint, solved = solve_logistic(objective, theta, **{key: value for key, value in PROBE_SOLVER.items() if key != "method"})
    finite = bool(np.isfinite(endpoint).all())
    after, gradient = objective(endpoint) if finite else (None, None)
    finite = finite and after is not None and math.isfinite(after) and np.isfinite(gradient).all()
    termination = dict(status=solved["status"], message=solved["termination"], converged=solved["converged"])
    reason = endpoint_reason(termination, after, before, finite)
    if finite and (solved["objective"] is None or not agrees(after, solved["objective"])):
        reason = "solver endpoint objective differs from replay"
    fields = dict(role="numerical_probe", window=window, arm=arm, quantity=component["quantity"],
                  source_fit=source_fit, source_component=source_component, parameterization=parameter_reference,
                  solver=PROBE_SOLVER, termination=termination, iterations=solved["iterations"], evaluations=solved["evaluations"],
                  coefficients=endpoint[parameterization["full_to_free"]].tolist() if finite else None,
                  objective=float(after) if finite else None,
                  free_gradient_max=float(np.max(np.abs(gradient))) if finite else None,
                  valid=reason is None, missing_reason=reason)
    path = output / f"{window}-{arm}-{component['quantity']}.json"
    write_json(path, envelope("probe_state", prepared["purpose"], protocol, **fields))
    return dict(source_fit=source_fit, source_component=source_component, parameterization=parameter_reference,
                state=identity(path), checks=dict(original_objective=float(before),
                    original_free_gradient_max=float(np.max(np.abs(before_gradient))),
                    saved_objective=component["diagnostics"]["objective"], solver_objective=solved["objective"],
                    endpoint_objective=fields["objective"], objective_change=float(after - before) if finite else None,
                    valid=fields["valid"], missing_reason=reason)), fields


def movement_stream(path, window, prepared, components, parameterizations, states, control, mirror):
    """score diagnostic vectors with native arithmetic, retaining every original U key."""
    contexts = {arm: {quantity: component_probe_context(
        components[arm][quantity], states[arm][quantity]["coefficients"], parameterizations[arm][quantity],
        feature_games=prepared["feature_games"], feature_player_games=prepared["feature_player_games"])
        for quantity in QUANTITIES if states[arm][quantity]["valid"]} for arm in ARMS}
    with path.open("x", encoding="utf-8") as destination:
        for attempt, pair in zip(prepared["attempts"], paired_composed_rows(
                linked_path(control["attempts"]), linked_path(mirror["attempts"])), strict=True):
            before, after = pair
            require((attempt["game_id"], attempt["source_index"], attempt["event_id"], attempt["goal"], attempt["blocked"]) ==
                    (before["game_id"], before["source_index"], before["event_id"], before["goal"], before["blocked"]),
                    "diagnostic source keys or labels differ from primary evidence")
            if before["status"] != "predicted":
                continue
            arms = {}
            for arm, original in (("untied", before), ("mirror_y", after)):
                baseline = {quantity: {key: original["stages"][quantity][key] for key in ("log_p", "log_not_p")}
                            for quantity in QUANTITIES}
                baseline["composed_goal"] = original["composed_goal"]
                probed = {}
                for quantity in QUANTITIES:
                    prediction = predict_component(components[arm][quantity], attempt, contexts[arm][quantity]) if quantity in contexts[arm] else None
                    probed[quantity] = {key: prediction[key] for key in ("log_p", "log_not_p")} if prediction else None
                probed["composed_goal"] = compose_logs(*(probed[q] for q in QUANTITIES)) if all(probed[q] is not None for q in QUANTITIES) else None
                arms[arm] = dict(original=baseline, probed=probed,
                                 missing_reasons={q: states[arm][q]["missing_reason"] for q in QUANTITIES})
            row = dict(schema_version=1, window=window, **{key: before[key] for key in (
                "game_id", "source_index", "event_id", "game_date", "season", "source_identity", "goal", "on_net")}, arms=arms)
            destination.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")


def assess_movement(path, window, states, control, mirror, primary, original_losses, counts, samples):
    game_dates = control["game_dates"]
    game_index = {gid: i for i, gid in enumerate(game_dates)}
    losses = {arm: {state: np.zeros(len(game_dates)) for state in ("original", "probed")} for arm in ARMS}
    metrics = {arm: {state: {quantity: binary_metrics(calibration=False, outcome="on_net" if quantity == QUANTITIES[0] else "goal")
                             for quantity in (*QUANTITIES, "composed_goal")}
                     for state in ("original", "probed")} for arm in ARMS}
    changes = {arm: {quantity: [] for quantity in (*QUANTITIES, "composed_goal")} for arm in ARMS}
    absolute_loss_movement = dict.fromkeys(ARMS, 0.)
    valid = dict.fromkeys(ARMS, True)
    n = 0
    primaries = ((before, after) for before, after in paired_composed_rows(
        linked_path(control["attempts"]), linked_path(mirror["attempts"])) if before["status"] == "predicted")
    for row, pair in zip_longest(rows(path), primaries):
        require(row is not None and pair is not None and set(row) == {
            "schema_version", "window", "game_id", "source_index", "event_id", "game_date", "season",
            "source_identity", "goal", "on_net", "arms"} and type(row["schema_version"]) is int and row["schema_version"] == 1 and
            row["window"] == window and set(row["arms"]) == set(ARMS),
            "invalid numerical movement stream shape or length")
        before, after = pair
        require(all(row[key] == before[key] for key in
                    ("game_id", "source_index", "event_id", "game_date", "season", "source_identity", "goal", "on_net")),
                "numerical movement source keys/labels changed")
        n += 1
        index = game_index[row["game_id"]]
        for arm, original in (("untied", before), ("mirror_y", after)):
            view = row["arms"][arm]
            require(set(view) == {"original", "probed", "missing_reasons"} and
                    set(view["original"]) == set(view["probed"]) == set((*QUANTITIES, "composed_goal")) and
                    view["missing_reasons"] == {q: states[arm][q]["missing_reason"] for q in QUANTITIES} and
                    all((view["probed"][q] is not None) == states[arm][q]["valid"] for q in QUANTITIES),
                    "invalid numerical arm stream schema, validity or reasons")
            for quantity in (*QUANTITIES, "composed_goal"):
                saved = view["original"][quantity]
                expected = original["composed_goal"] if quantity == "composed_goal" else original["stages"][quantity]
                require(saved == {key: expected[key] for key in ("log_p", "log_not_p")}, "numerics changed original saved probabilities")
                probed = view["probed"][quantity]
                if probed is not None:
                    require(set(probed) == {"log_p", "log_not_p"}, "invalid probe probability fields")
                    binary_record(0, **probed)
                    changes[arm][quantity].append(abs(math.exp(probed["log_p"]) - math.exp(saved["log_p"])))
                else:
                    valid[arm] = False
                observed = int(row["on_net"]) if quantity == QUANTITIES[0] else int(row["goal"])
                if quantity == QUANTITIES[1] and not row["on_net"]:
                    continue
                for state in ("original", "probed"):
                    if view[state][quantity] is not None:
                        record = binary_record(observed, **view[state][quantity])
                        add_binary(metrics[arm][state][quantity], record)
                        if quantity == "composed_goal":
                            losses[arm][state][index] += record["log_loss_sum"]
                if quantity == "composed_goal" and probed is not None:
                    key = "log_p" if observed else "log_not_p"
                    absolute_loss_movement[arm] += abs(probed[key] - saved[key])
            if all(view["probed"][q] is not None for q in QUANTITIES):
                require(view["probed"]["composed_goal"] == compose_logs(*(view["probed"][q] for q in QUANTITIES)),
                        "probe product is not composed from its own stage probabilities")
            else:
                require(view["probed"]["composed_goal"] is None, "invalid probe arm cannot supply a product")
    require(n == sum(counts), "numerical movement omitted original U rows")
    probability_changes, metric_changes = {}, {}
    for arm in ARMS:
        require(np.allclose(losses[arm]["original"], original_losses[arm], rtol=1e-10, atol=1e-10),
                "numerical original game losses differ from primary evidence")
        probability_changes[arm], metric_changes[arm] = {}, {}
        for quantity in (*QUANTITIES, "composed_goal"):
            for state in ("original", "probed"):
                finish_binary(metrics[arm][state][quantity])
            values = changes[arm][quantity]
            probability_changes[arm][quantity] = dict(mean=float(np.mean(values)), p99=float(np.percentile(values, 99, method="linear")),
                                                       maximum=max(values)) if len(values) == n and n else None
            before, after = (metrics[arm][state][quantity] for state in ("original", "probed"))
            metric_changes[arm][quantity] = after["log_loss"] - before["log_loss"] if before["count"] == after["count"] and before["count"] else None
            if before["count"] != after["count"]:
                metrics[arm]["probed"][quantity] = None
    combinations = {}
    allowance = .10 * primary["A"] if primary["A"] is not None else None
    for mirror_state, control_state in (("original", "original"), ("probed", "original"), ("original", "probed"), ("probed", "probed")):
        key = f"m{int(mirror_state == 'probed')}c{int(control_state == 'probed')}"
        if (mirror_state == "probed" and not valid["mirror_y"]) or (control_state == "probed" and not valid["untied"]):
            combinations[key] = dict(comparison=None, point_shift=None, interval_shifts=None, classification_unchanged=False,
                                     missing_reason="one or more required diagnostic endpoints are invalid")
            continue
        result = contrast(dict(constant=original_losses["constant"], untied=losses["untied"][control_state],
                               mirror_y=losses["mirror_y"][mirror_state]), counts, game_dates, samples)
        shifts = {unit: [abs(a - b) for a, b in zip(result["intervals"]["c"][unit]["interval"], base["interval"], strict=True)]
                  if result["intervals"]["c"][unit]["interval"] is not None and base["interval"] is not None else None
                  for unit, base in primary["intervals"]["c"].items()}
        combinations[key] = dict(comparison=result, point_shift=abs(result["c"] - primary["c"]) if result["c"] is not None else None,
                                 interval_shifts=shifts, classification_unchanged=result["status"] == primary["status"], missing_reason=None)
    b = (absolute_loss_movement["mirror_y"] + .99 * absolute_loss_movement["untied"]) / n if all(valid.values()) and n else None
    reasons = []
    if primary["status"] == "reference_unusable":
        status = "reference_unusable"
        reasons.append("original reference is unusable for gain retention")
    else:
        if not all(valid.values()):
            reasons.append("one or more diagnostic endpoints are invalid")
        if b is None or allowance is None or b > allowance:
            reasons.append("absolute row-loss movement exceeds or cannot resolve ten percent of allowance")
        for key, item in combinations.items():
            if item["point_shift"] is None or item["point_shift"] > allowance or item["interval_shifts"] is None or any(
                value is None or any(v > allowance for v in value) for value in (item["interval_shifts"] or {}).values()
            ):
                reasons.append(f"{key} contrast point or interval movement exceeds or cannot resolve numerical allowance")
            if item["comparison"] is not None and not item["classification_unchanged"]:
                reasons.append(f"{key} changes reference usability or budget classification")
        status = "resolution_unestablished" if reasons else "stable_within_probe"
    ratio = b / primary["A"] if b is not None and primary["A"] is not None and primary["A"] > 0 else None
    return dict(metrics=metrics, probability_changes=probability_changes, loss_changes=metric_changes,
                B=b, A=primary["A"], B_over_A=ratio,
                B_over_A_missing_reason=None if ratio is not None else "invalid endpoint, empty population or nonpositive allowance",
                numerical_allowance=allowance, combinations=combinations,
                status=status, reasons=reasons)


def numerics_command(args):
    started = time.monotonic()
    inputs_path, protocol_path = Path(args.inputs).resolve(strict=True), Path(args.protocol).resolve(strict=True)
    inputs, protocol = matrix_inputs(inputs_path, report=False), identity(protocol_path)
    reuse = read_reuse(inputs["reuse"]["completion"], protocol)
    purpose = reuse["purpose"]
    require(inputs["purpose"] == purpose, "numerics matrix/reuse purpose differs")
    output = study_output(args.out, artifact_roots(inputs) + artifact_roots(reuse) + [str(inputs_path.parent), str(protocol_path.parent)], purpose)
    output.mkdir()
    probes, windows = {}, {}
    for window in WINDOWS:
        entry, cells = reuse["windows"][window], inputs["windows"][window]
        fits = {q: cells[q]["completion"] for q in QUANTITIES}
        mirror, _ = read_assessment(cells["assessment"]["completion"], reuse, window, fits, protocol)
        control = read_json(linked_path(reuse["checks"][window]["assessment_document"]))
        components, parameterizations, state_values = {}, {}, {}
        prepared, cohorts, _, _, _ = partition_inputs(entry, "training", purpose, window=window)
        for arm in ARMS:
            components[arm], parameterizations[arm], state_values[arm] = {}, {}, {}
            for quantity in QUANTITIES:
                if arm == "untied":
                    source_fit = entry["control_fits"][quantity]
                    source_component = reuse["checks"][window]["components"][quantity]
                    parameter_reference = reuse["checks"][window]["parameterizations"][quantity]
                    component = validate_component(read_json(linked_path(source_component)))
                    parameterization = read_parameter(parameter_reference, component, "untied", purpose=purpose, protocol=protocol)
                else:
                    source_fit = fits[quantity]
                    complete, component, parameterization = read_fit(source_fit, reuse, window, quantity, protocol)
                    source_component, parameter_reference = complete["component"], complete["parameterization"]
                components[arm][quantity], parameterizations[arm][quantity] = component, parameterization
                key = f"{window}/{arm}/{quantity}"
                probes[key], state_values[arm][quantity] = probe_component(
                    component, parameterization, prepared, cohorts[quantity], source_fit=source_fit,
                    source_component=source_component, parameter_reference=parameter_reference,
                    window=window, arm=arm, protocol=protocol, output=output)
        del prepared, cohorts
        prepared, cohorts, _, _, _ = partition_inputs(entry, "assessment", purpose, window=window)
        movement_path = output / f"{window}-movement.jsonl"
        movement_stream(movement_path, window, prepared, components, parameterizations, state_values, control, mirror)
        del prepared, cohorts
        samples = paired_samples(control["game_dates"])
        primary, losses, counts = primary_comparison(control, mirror, reuse["checks"][window]["training"], samples=samples)
        windows[window] = dict(movement=identity(movement_path),
            source_replay=dict(movement=identity(movement_path), untied=control["attempts"], mirror_y=mirror["attempts"],
                               states={arm: {q: probes[f"{window}/{arm}/{q}"]["state"] for q in QUANTITIES} for arm in ARMS},
                               source_labels_dispositions_order="verified", native_probe_predictions="verified"),
            **assess_movement(movement_path, window, state_values, control, mirror, primary, losses, counts, samples))
    write_json(output / "numerics.json", envelope("numerics", purpose, protocol, inputs=identity(inputs_path),
        probes=probes, windows=windows, resources=resources(started)))
    write_json(output / "completion.json", envelope("numerics_completion", purpose, protocol,
        numerics=identity(output / "numerics.json"), scientific_assessment="not_performed"))
    return 0

def validate_objective_receipt(value, component, component_reference, cohort_reference, parameterization):
    fields = {"schema_version", "purpose", "component", "selection", "cohort", "config", "protocol", "implementation",
              "saved_objective", "replayed_objective", "difference", "gradient_max_abs", "agrees",
              "free_gradient_max", "full_count", "free_count"}
    require(isinstance(value, dict) and set(value) == fields and type(value["schema_version"]) is int and value["schema_version"] == 1 and
            value["purpose"] == component["purpose"] and value["component"] == component_reference and
            value["cohort"] == cohort_reference and value["config"] == component["config_identity"] and
            value["protocol"] == component["protocol_identity"] and value["implementation"] == implementation() and
            value["saved_objective"] == component["diagnostics"]["objective"] and value["agrees"] is True and
            value["full_count"] == parameterization["full_count"] and value["free_count"] == parameterization["free_count"] and
            all(type(value[key]) in (int, float) and math.isfinite(value[key]) for key in
                ("saved_objective", "replayed_objective", "difference", "gradient_max_abs", "free_gradient_max")) and
            value["gradient_max_abs"] >= 0 and value["free_gradient_max"] >= 0 and
            agrees(value["replayed_objective"], value["saved_objective"]) and
            agrees(value["difference"], value["replayed_objective"] - value["saved_objective"]),
            "objective replay receipt source, dimensions or arithmetic differs")
    selection = [value for value in component["inputs"] if value["kind"] == "selection"]
    require(len(selection) == 1 and value["selection"] == {key: selection[0][key] for key in ("path", "sha256")},
            "objective replay selection differs from native source")


def read_numerics(reference, inputs, reuse, protocol):
    purpose = reuse["purpose"]
    complete = completed(reference, "numerics", {"numerics"}, purpose=purpose, protocol=protocol)
    saved = document(complete["numerics"], "numerics", {"inputs", "probes", "windows", "resources"}, purpose=purpose, protocol=protocol)
    matrix = matrix_inputs(linked_path(saved["inputs"]), report=False)
    require(matrix == {key: inputs[key] for key in ("schema_version", "purpose", "reuse", "windows")},
            "numerics completed a different primary matrix")
    expected_keys = [f"{window}/{arm}/{quantity}" for window in WINDOWS for arm in ARMS for quantity in QUANTITIES]
    require(isinstance(saved["probes"], dict) and set(saved["probes"]) == set(expected_keys) and
            isinstance(saved["windows"], dict) and set(saved["windows"]) == set(WINDOWS),
            "numerics must bind exactly eight diagnostic states and two windows")
    for window in WINDOWS:
        for arm in ARMS:
            for quantity in QUANTITIES:
                record = saved["probes"][f"{window}/{arm}/{quantity}"]
                require(set(record) == {"source_fit", "source_component", "parameterization", "state", "checks"},
                        "invalid probe receipt schema")
                if arm == "untied":
                    source_fit = reuse["windows"][window]["control_fits"][quantity]
                    component_reference = reuse["checks"][window]["components"][quantity]
                    parameter_reference = reuse["checks"][window]["parameterizations"][quantity]
                    component = validate_component(read_json(linked_path(component_reference)))
                    parameterization = read_parameter(parameter_reference, component, arm, purpose=purpose, protocol=protocol)
                else:
                    source_fit = inputs["windows"][window][quantity]["completion"]
                    fitted, component, parameterization = read_fit(source_fit, reuse, window, quantity, protocol)
                    component_reference, parameter_reference = fitted["component"], fitted["parameterization"]
                state = document(record["state"], "probe_state", PROBE_FIELDS, purpose=purpose, protocol=protocol)
                require(state["role"] == "numerical_probe" and state["window"] == window and state["arm"] == arm and
                        state["quantity"] == quantity and state["source_fit"] == record["source_fit"] == source_fit and
                        state["source_component"] == record["source_component"] == component_reference and
                        state["parameterization"] == record["parameterization"] == parameter_reference and
                        state["solver"] == PROBE_SOLVER and type(state["valid"]) is bool and
                        type(state["iterations"]) is int and 0 <= state["iterations"] <= 100 and
                        type(state["evaluations"]) is int and state["evaluations"] >= 0 and
                        isinstance(state["termination"], dict) and set(state["termination"]) == {"status", "message", "converged"} and
                        type(state["termination"]["status"]) is int and type(state["termination"]["converged"]) is bool and
                        isinstance(state["termination"]["message"], str), "invalid probe state role/source/solver dimensions")
                message = state["termination"]["message"]
                require(message != "STOP: TOTAL NO. OF ITERATIONS REACHED LIMIT" or state["iterations"] == PROBE_SOLVER["maxiter"],
                        "iteration-cap termination disagrees with recorded iterations")
                require(message != "STOP: TOTAL NO. OF F,G EVALUATIONS EXCEEDS LIMIT" or state["evaluations"] > PROBE_SOLVER["maxfun"],
                        "evaluation-cap termination disagrees with recorded evaluations")
                finite = state["coefficients"] is not None
                if finite:
                    free_coefficients(state["coefficients"], parameterization)
                    require(type(state["objective"]) in (int, float) and math.isfinite(state["objective"]), "invalid finite endpoint objective")
                    require(type(state["free_gradient_max"]) in (int, float) and math.isfinite(state["free_gradient_max"]) and
                            state["free_gradient_max"] >= 0, "invalid probe free gradient")
                else:
                    require(state["objective"] is None and state["free_gradient_max"] is None,
                            "nonfinite endpoint must retain null objective/gradient")
                check = record["checks"]
                require(set(check) == {"original_objective", "original_free_gradient_max", "saved_objective", "solver_objective",
                                       "endpoint_objective", "objective_change", "valid", "missing_reason"} and
                        check["saved_objective"] == component["diagnostics"]["objective"] and
                        agrees(check["original_objective"], check["saved_objective"]) and
                        check["endpoint_objective"] == state["objective"] and
                        check["valid"] == state["valid"] and check["missing_reason"] == state["missing_reason"] and
                        type(check["original_free_gradient_max"]) in (int, float) and
                        math.isfinite(check["original_free_gradient_max"]) and check["original_free_gradient_max"] >= 0 and
                        (check["objective_change"] is None if not finite else
                         type(check["objective_change"]) in (int, float) and math.isfinite(check["objective_change"]) and
                         agrees(check["objective_change"], state["objective"] - check["original_objective"])),
                        "probe replay receipt differs from original/endpoint objective")
                reason = endpoint_reason(state["termination"], state["objective"], check["original_objective"], finite)
                if finite and (check["solver_objective"] is None or not agrees(check["solver_objective"], state["objective"])):
                    reason = "solver endpoint objective differs from replay"
                require(state["valid"] == (reason is None) and state["missing_reason"] == reason,
                        "probe validity does not follow fixed numerical policy")
    return saved


def save_figures(result, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1, figsize=(11, 6), layout="constrained")
    colors = ("#28547a", "#8c5f20", "#377763")
    for axis, window in zip(axes, WINDOWS, strict=True):
        value = result["windows"][window]
        axis.axvline(0, color="#333333", lw=1, label="99% gain-retention boundary")
        axis.set_yticks((0, 1, 2), ("whole games", "7-day blocks", "14-day blocks"))
        axis.set_ylim(-.5, 2.5)
        axis.set_xlabel("c = mirror loss − .99 × untied loss − .01 × constant loss (nats/U)")
        if value["comparison"] is None:
            axis.text(.5, .5, "primary evidence incomplete", transform=axis.transAxes, ha="center")
            axis.set_title(window.replace("_", " "))
            continue
        comparison = value["comparison"]
        for index, (unit, interval) in enumerate(comparison["intervals"]["c"].items()):
            if interval["interval"] is None:
                axis.text(.02, index, f"undefined interval ({interval['undefined_draws']} zero-denominator draws)",
                          transform=axis.get_yaxis_transform(), va="center", fontsize=8)
            else:
                lower, upper = interval["interval"]
                axis.plot((lower, upper), (index, index), color=colors[index], lw=2)
                axis.plot(comparison["c"], index, "o", color=colors[index], ms=4)
        p = comparison["population"]
        axis.set_title(f"{window.replace('_', ' ')} · {comparison['status'].replace('_', ' ')} · U={p['unblocked']:,} / G={p['goals']:,} · "
                       f"control gain D={format(comparison['D'], '.6g') if comparison['D'] is not None else 'undefined'} · "
                       f"allowance A={format(comparison['A'], '.6g') if comparison['A'] is not None else 'undefined'} nats/U", fontsize=10)
    axes[0].legend(loc="lower right", fontsize=8)
    fig.suptitle("mirror pooling: cost relative to the allowed predictive gain\nnegative c supports staying within budget when the reference is usable", fontsize=12)
    fig.supxlabel("95% intervals condition on fitted models and the training reference; the continuation is not an optimization-error certificate.", fontsize=8)
    fig.savefig(output / "comparison.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex="col", sharey="col", layout="constrained")
    for row_index, window in enumerate(WINDOWS):
        value = result["windows"][window]
        for col, metric in enumerate(("on_net", "goal_given_on_net")):
            axis = axes[row_index, col]
            axis.axhline(0, color="#777777", lw=.7)
            axis.set_xlim(0, 1)
            axis.set_xlabel("untied probability bin; shared membership")
            axis.set_ylabel("predicted − observed (percentage points)")
            axis.set_title(f"{window.replace('_', ' ')} · {'q on U' if col == 0 else 'g on O'}")
            if value["diagnostics"] is None:
                axis.text(.5, .5, "primary evidence incomplete", transform=axis.transAxes, ha="center")
                continue
            bins = value["diagnostics"][metric]["paired_calibration"]
            for arm, name, color in (("baseline", "untied", "#28547a"), ("changed", "mirror", "#a54f3a")):
                selected = [bucket for bucket in bins if bucket[arm]["count"]]
                axis.plot([(bucket["lower"] + bucket["upper"]) / 2 for bucket in selected],
                          [bucket[arm]["predicted_minus_observed_pp"] for bucket in selected],
                          "o-", color=color, lw=.8, ms=3, label=name)
            for bucket in bins:
                if bucket["baseline"]["count"]:
                    axis.annotate(f"{bucket['baseline']['count']:,}",
                        ((bucket["lower"] + bucket["upper"]) / 2, bucket["baseline"]["predicted_minus_observed_pp"]),
                        xytext=(0, 5), textcoords="offset points", ha="center", fontsize=6)
            axis.margins(y=.3)
            axis.legend(fontsize=8)
    fig.suptitle("descriptive stage calibration · counts label the shared untied-defined bins", fontsize=12)
    fig.supxlabel("own-arm bins remain in the result tables. stage losses have different U/O targets and do not rank the stages.", fontsize=8)
    fig.savefig(output / "stages.png", dpi=180)
    plt.close(fig)
    return {name: identity(output / f"{name}.png") for name in ("comparison", "stages")}


def report_command(args):
    started = time.monotonic()
    inputs_path, protocol_path = Path(args.inputs).resolve(strict=True), Path(args.protocol).resolve(strict=True)
    inputs, protocol = matrix_inputs(inputs_path, report=True), identity(protocol_path)
    purpose = inputs["purpose"]
    reuse = read_reuse(inputs["reuse"]["completion"], protocol) if inputs["reuse"]["status"] == "complete" else None
    if reuse is not None:
        require(reuse["purpose"] == purpose, "report matrix/reuse purpose differs")
    output = study_output(args.out, artifact_roots(inputs) + (artifact_roots(reuse) if reuse else []) +
                          [str(inputs_path.parent), str(protocol_path.parent)], purpose)
    primary_complete = reuse is not None and all(inputs["windows"][window][key]["status"] == "complete"
        for window in WINDOWS for key in (*QUANTITIES, "assessment"))
    numerical = None
    if inputs["numerics"]["status"] == "complete":
        require(primary_complete, "completed numerics requires complete primary evidence")
        numerical = read_numerics(inputs["numerics"]["completion"], inputs, reuse, protocol)
    windows = {}
    for window in WINDOWS:
        cells = inputs["windows"][window]
        complete = reuse is not None and all(cells[key]["status"] == "complete" for key in (*QUANTITIES, "assessment"))
        value = dict(cells=cells, comparison=None, coverage=None, diagnostics=None,
                     parameter_counts=None, numerical_status="incomplete", numerical_reasons=["numerical evidence incomplete"])
        if reuse is not None:
            fitted = {}
            for quantity in QUANTITIES:
                if cells[quantity]["status"] == "complete":
                    fitted[quantity] = read_fit(cells[quantity]["completion"], reuse, window, quantity, protocol)
            if cells["assessment"]["status"] == "complete":
                require(len(fitted) == 2, "completed assessment requires both completed primary fits")
        if complete:
            fits = {q: cells[q]["completion"] for q in QUANTITIES}
            mirror, _ = read_assessment(cells["assessment"]["completion"], reuse, window, fits, protocol)
            control = read_json(linked_path(reuse["checks"][window]["assessment_document"]))
            samples = paired_samples(control["game_dates"])
            comparison, losses, counts = primary_comparison(control, mirror, reuse["checks"][window]["training"], samples=samples)
            value.update(comparison=comparison, coverage=mirror["coverage"], diagnostics=diagnostics(control, mirror),
                         parameter_counts={q: {key: fitted[q][2][key] for key in
                                               ("full_count", "free_count", "full_spatial_count", "free_spatial_count", "orbit_count", "centreline_count")}
                                           for q in QUANTITIES})
            if numerical is not None:
                saved = numerical["windows"][window]
                state_refs = {arm: {q: numerical["probes"][f"{window}/{arm}/{q}"]["state"] for q in QUANTITIES} for arm in ARMS}
                expected_receipt = dict(movement=saved["movement"], untied=control["attempts"], mirror_y=mirror["attempts"], states=state_refs,
                    source_labels_dispositions_order="verified", native_probe_predictions="verified")
                require(saved["source_replay"] == expected_receipt, "numerical movement replay receipt differs")
                states = {arm: {q: read_json(linked_path(state_refs[arm][q])) for q in QUANTITIES} for arm in ARMS}
                replayed = assess_movement(linked_path(saved["movement"]), window, states, control, mirror, comparison, losses, counts, samples)
                require(set(saved) == {"movement", "source_replay"} | set(replayed) and
                        all(saved[key] == item for key, item in replayed.items()),
                        "saved numerical movement/combination decision differs from exact paired replay")
                value.update(numerical_status=saved["status"], numerical_reasons=saved["reasons"])
        elif reuse is None:
            require(all(cells[key]["status"] != "complete" for key in (*QUANTITIES, "assessment")),
                    "completed primary cells require completed source reuse")
        windows[window] = value
    execution_complete = primary_complete and numerical is not None
    comparison_result = combined_status([value["comparison"]["status"] if value["comparison"] else "incomplete" for value in windows.values()])
    nominate = execution_complete and comparison_result == "within_budget" and all(
        value["numerical_status"] == "stable_within_probe" for value in windows.values())
    result = envelope("result", purpose, protocol, inputs=identity(inputs_path), reuse=inputs["reuse"], constraint="mirror_y",
        windows=windows, numerics=numerical, comparison_result=comparison_result if purpose == "research" else "not_assessed",
        recommendation=("nominate_mirror" if nominate else "no_supported_structure") if purpose == "research" else "fixture_only",
        nominated_structure="mirror_y" if nominate and purpose == "research" else None,
        scientific_assessment="not_admitted" if purpose == "research" else "not_performed",
        execution_status="complete" if execution_complete else "incomplete", resampling=RESAMPLING,
        limitations=LIMITATIONS, resources={}, figures={})
    output.mkdir()
    result["figures"] = save_figures(result, output)
    result["resources"] = resources(started)
    write_json(output / "result.json", result)
    write_json(output / "completion.json", envelope("report_completion", purpose, protocol,
        result=identity(output / "result.json"), figures=result["figures"], scientific_assessment="not_performed"))
    return 0


def main():
    parser = argparse.ArgumentParser(description="fixed mirror-pooling research commands", allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    options = {
        "reuse": ("inputs", "protocol", "out"),
        "fit": ("reuse", "protocol", "window", "quantity", "out"),
        "evaluate": ("reuse", "protocol", "window", "on-net-fit", "conversion-fit", "out"),
        "numerics": ("inputs", "protocol", "out"),
        "report": ("inputs", "protocol", "out"),
    }
    for name, flags in options.items():
        child = commands.add_parser(name, allow_abbrev=False)
        for flag in flags:
            kwargs = {"choices": WINDOWS} if flag == "window" else {"choices": QUANTITIES} if flag == "quantity" else {}
            child.add_argument(f"--{flag}", required=True, action=Once, **kwargs)
    args = parser.parse_args()
    try:
        command = {"reuse": reuse_command, "fit": fit_command, "evaluate": evaluate_command,
                   "numerics": numerics_command, "report": report_command}[args.command]
        result = command(args)
        if result == 0:
            print(f"mirror {args.command} complete: {Path(args.out).absolute()}; scientific assessment not performed")
        return result
    except (InputContractError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"mirror {args.command} failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
