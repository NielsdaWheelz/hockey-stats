"""four fresh, manually selected conversion fits; no scientific admission."""

import argparse
from copy import deepcopy
from decimal import Decimal, localcontext
import math
from pathlib import Path
import sys
import time

import numpy as np

from hockey_stats.artifacts import write_json
from hockey_stats.captures import InputContractError
from hockey_stats.chance import validate_component, validate_config
from hockey_stats.chance_cli import identity, output_path, read_json
from hockey_stats.chance_data import prepare
from hockey_stats.chance_features import PREPARATION_IDENTITY
from hockey_stats.cli import Once
from chance_development import (
    compare_pair, evaluate as component_evaluate, fit as component_fit,
    implementation, paired_rows, resources, validate_evaluation,
)
from chance_review import agrees, clean_implementation, linked_path, require

WINDOWS = ("development", "season_transfer")
ARMS = ("baseline", "sequence")
QUANTITY = "unblocked_conversion"
BASELINE = ["game_additive", "recent_additive", "recent_interactions"]
DEFINITION = dict(mode="selected_family_complete", required_families=["sequence"])
DEADBAND = 1e-10
RESAMPLING = dict(draws=2000, seed=3032026, generator="PCG64",
                  percentile_method="linear", calendar_days=[7, 14])
ANCHORS = dict(
    kernel_distance_ft=20, kernel_direction_strength=4,
    ridge_origin_base=.25, ridge_cell=.25, ridge_benchmark=.25,
    ridge_origin_factor=1, ridge_type_cell=1, smooth_origin=4, smooth_cell=4,
    ridge_context=4, ridge_shooter=4, change_shooter=16,
    ridge_goalie=16, change_goalie=64, optimizer_max_iterations=2000,
    optimizer_ftol=1e-10, optimizer_gtol=1e-6, em_max_iterations=2000,
    em_relative_tolerance=1e-8, em_posterior_tolerance=1e-6,
    objective_decrease_tolerance=1e-10,
)
REPORT_GROUPS = (
    "recent_context", "model_type", "sequence_index", "calendar_month", "role",
    "actor_support:shooter", "actor_support:goalie",
)
LIMITATIONS = [
    "membership requires source-eligible unblocked attempts and verified encodable defending-sequence facts; selective omissions leave representativeness unproved",
    "omitted-row baseline predictions come from the common-trained baseline; no separate all-source baseline was fitted",
    "95% intervals are conditional on fitted models and omit fitting, selection and origin uncertainty; all three seasons were already research-exposed",
    "the four-term sequence package combines index contrasts and elapsed age; it does not isolate possession, pressure, fatigue or a causal coefficient",
    "recorded coordinates and continuity facts are proxies; physical release truth, material player impact, admission and publication are not established",
    "four fresh solves preserve matched initialization and actor counts at the cost of recomputation; inactive supported feature code is retained",
]


def validate_recipe(config):
    """literal settings and two family lists constitute the whole experiment."""
    validate_config(config)
    require(config["trait_assumptions"] == [], "sequence recipes require no trait assumptions")
    require(all(config[key] == value for key, value in ANCHORS.items()),
            "sequence recipe numerical settings differ from the frozen anchors")
    for stage in ("origin", "u", "unblocked", "all_attempt"):
        require(config["stage_families"][stage] == ["game_additive", "recent_additive"],
                "inactive stages must retain their declared families")
    selected = config["stage_families"]["r"]
    require(selected in (BASELINE, BASELINE + ["sequence"]),
            "sequence study requires the fixed baseline or sequence recipe")
    return "baseline" if selected == BASELINE else "sequence"


def validate_report_inputs(document):
    require(isinstance(document, dict) and set(document) ==
            {"schema_version", "purpose", "windows", "resampling"} and
            type(document["schema_version"]) is int and document["schema_version"] == 1 and
            document["purpose"] in ("research", "fixture_exercise"),
            "schema-1 sequence report inputs required")
    require(document["resampling"] == RESAMPLING and
            all(type(document["resampling"][field]) is int for field in ("draws", "seed")) and
            all(type(value) is int for value in document["resampling"]["calendar_days"]),
            "sequence resampling settings changed")
    require(isinstance(document["windows"], dict) and set(document["windows"]) == set(WINDOWS),
            "sequence study requires exactly the two declared windows")
    for window in WINDOWS:
        cells = document["windows"][window]
        require(isinstance(cells, dict) and set(cells) == set(ARMS),
                "sequence study requires exactly baseline and sequence in each window")
        for cell in cells.values():
            require(isinstance(cell, dict) and set(cell) == {
                "status", "config", "training_cohort", "assessment_cohort", "fit",
                "evaluation", "failure", "stop_reason",
            }, "unexpected sequence cell fields")
            status = cell["status"]
            require(status in ("complete", "failed", "not_run"), "invalid sequence cell status")
            for field in ("config", "training_cohort", "assessment_cohort", "fit", "evaluation", "failure"):
                reference = cell[field]
                require(reference is None or isinstance(reference, dict) and
                        set(reference) == {"path", "sha256"}, "located artifact identity required")
            if status == "complete":
                require(all(cell[field] is not None for field in
                            ("config", "training_cohort", "assessment_cohort", "fit", "evaluation"))
                        and cell["failure"] is None and cell["stop_reason"] is None,
                        "complete cell requires both successful completions and no failure")
            else:
                require(isinstance(cell["stop_reason"], str) and bool(cell["stop_reason"].strip())
                        and cell["evaluation"] is None,
                        "incomplete cell requires an explicit stop reason and no evaluation completion")
                if status == "failed":
                    require(cell["failure"] is not None, "failed cell requires located failure evidence")
                else:
                    require(cell["fit"] is None, "not-run cell cannot claim a fit completion")
    stopped = False
    for window in WINDOWS:
        for arm in ARMS:
            status = document["windows"][window][arm]["status"]
            require(not stopped or status == "not_run", "a numerical/source/resource stop must stop later cells")
            stopped = status != "complete"
        before = document["windows"][window]["baseline"]
        after = document["windows"][window]["sequence"]
        for partition in ("training_cohort", "assessment_cohort"):
            require(before[partition] is None or after[partition] is None or before[partition] == after[partition],
                    "matched arms must reference the same external cohort")
    return document


def decision(comparisons, *, purpose):
    if purpose == "fixture_exercise":
        return "not_assessed", "fixture_only"
    require(purpose == "research", "unsupported sequence report purpose")
    if any(comparisons[window] is None for window in WINDOWS):
        return "incomplete", "no_supported_next_fit"
    primary = [comparisons[window]["delta"]["log_loss"] for window in WINDOWS]
    points = [record["games"]["estimate"] for record in primary]
    if any(value is None for value in points):
        return "incomplete", "no_supported_next_fit"
    require(all(type(value) in (int, float) and math.isfinite(value) for value in points),
            "primary point estimates must be finite")
    improvements = [value < -DEADBAND for value in points]
    direction = ("consistent_direction" if all(improvements) else
                 "no_improvement" if not any(improvements) else "mixed_direction")
    defined = all(record[unit]["interval"] is not None
                  for record in primary for unit in ("games", "calendar_7_day", "calendar_14_day"))
    nominated = (direction == "consistent_direction" and defined and
                 all(record["games"]["interval"][1] < -DEADBAND for record in primary) and
                 not any(record[unit]["interval"][0] > DEADBAND
                         for record in primary for unit in ("calendar_7_day", "calendar_14_day")))
    return direction, "research_integration" if nominated else "no_supported_next_fit"


def selection_reference(cohort):
    references = [value for value in cohort["inputs"] if value["kind"] == "selection"]
    require(len(references) == 1, "cohort requires exactly one located selection")
    reference = {key: references[0][key] for key in ("path", "sha256")}
    path = linked_path(reference)
    selected = read_json(path)
    require(isinstance(selected, dict) and set(selected) ==
            {"schema_version", "purpose", "corpora", "history_corpora"} and
            type(selected["schema_version"]) is int and selected["schema_version"] == 2 and
            selected["history_corpora"] == [], "sequence selection requires schema 2 and empty history")
    for corpus in selected["corpora"]:
        corpus["path"] = str((path.parent / corpus["path"]).resolve(strict=True))
    require(selected == cohort["selection"], "cohort selection content differs from its located input")
    return reference


def selected_inventory(cohort):
    """bind chronology to admitted inventory dates, including every empty game."""
    by_season, selected, dates = {}, {}, {}
    for entry in cohort["selection"]["corpora"]:
        references = [value for value in cohort["inputs"]
                      if value["kind"] == "corpus" and value["path"] == entry["path"]]
        require(len(references) == 1, "selected corpus lacks a unique consumed-byte identity")
        manifest = read_json(linked_path(references[0]))
        inventory = manifest["reference"]["inventory"]
        indexed = {value["game_id"]: value for value in inventory}
        require(len(indexed) == len(inventory), "duplicate admitted inventory game")
        season = manifest["reference"]["requested_season"]
        require(all(value["season"] == season for value in inventory),
                "admitted inventory season disagreement")
        if season in by_season:
            require(by_season[season] == indexed, "conflicting admitted season inventories")
        by_season[season] = indexed
        ids = entry["game_ids"]
        require(len(set(ids)) == len(ids) and not set(ids) & set(dates) and set(ids) <= set(indexed),
                "invalid explicit selected inventory keys")
        selected.setdefault(season, set()).update(ids)
        dates.update({gid: indexed[gid]["game_date"] for gid in ids})
    require(dates == cohort["game_dates"], "cohort dates differ from selected admitted inventory dates")
    return by_season, selected


def read_cohort(reference, purpose):
    from hockey_stats.chance_cohort import validate_cohort_document

    cohort = read_json(linked_path(reference))
    validate_cohort_document(cohort)
    require(cohort["purpose"] == purpose and cohort["quantity"] == QUANTITY and
            cohort["definition"] == DEFINITION and
            cohort["preparation_identity"] == PREPARATION_IDENTITY,
            "sequence cohort purpose, quantity, definition or preparation identity mismatch")
    selection_reference(cohort)
    selected_inventory(cohort)
    return cohort


def validate_window(window, training, assessment, purpose):
    require(not set(training["game_dates"]) & set(assessment["game_dates"]) and
            min(assessment["game_dates"].values()) > max(training["game_dates"].values()),
            "assessment keys must be disjoint and every date later than training")
    if purpose == "fixture_exercise":
        return
    train_inventory, train_ids = selected_inventory(training)
    assess_inventory, assess_ids = selected_inventory(assessment)
    inventories = dict(train_inventory)
    for season, values in assess_inventory.items():
        require(season not in inventories or inventories[season] == values,
                "training and assessment admitted inventories differ")
        inventories[season] = values
    if window == "development":
        require(set(inventories) == {"20232024", "20242025"},
                "development requires exactly its two source seasons")
        expected_train = {"20232024": set(inventories["20232024"]), "20242025": {
            gid for gid, row in inventories["20242025"].items() if row["game_date"] < "2025-01-01"}}
        expected_assess = {"20242025": set(inventories["20242025"]) - expected_train["20242025"]}
        counts = (1912, 712)
    else:
        require(set(inventories) == {"20232024", "20242025", "20252026"},
                "season transfer requires exactly its three source seasons")
        expected_train = {season: set(inventories[season]) for season in ("20232024", "20242025")}
        expected_assess = {"20252026": set(inventories["20252026"])}
        counts = (2624, 1312)
    require(train_ids == expected_train and assess_ids == expected_assess and
            (len(training["game_dates"]), len(assessment["game_dates"])) == counts,
            "research selections differ from the fixed complete chronological windows")


def training_window(training):
    """reject undeclared research fitting populations before a native solve."""
    inventories, selected = selected_inventory(training)
    require(set(inventories) == {"20232024", "20242025"},
            "research training must use the fixed two source seasons")
    development = {"20232024": set(inventories["20232024"]), "20242025": {
        gid for gid, row in inventories["20242025"].items() if row["game_date"] < "2025-01-01"}}
    transfer = {season: set(inventories[season]) for season in ("20232024", "20242025")}
    if selected == development and len(training["game_dates"]) == 1912:
        return "development"
    require(selected == transfer and len(training["game_dates"]) == 2624,
            "research training selection is neither declared chronological window")
    return "season_transfer"


def cohort_command(args):
    from hockey_stats.chance_cohort import component_cohort, outcome_audit

    started = time.monotonic()
    selection = Path(args.selection).resolve(strict=True)
    protocol = Path(args.protocol).resolve(strict=True)
    prepared = prepare(selection)
    require(prepared["selection"]["history_corpora"] == [], "sequence cohort requires empty history")
    cohort = component_cohort(prepared, quantity=QUANTITY, required_families=["sequence"])
    audit = outcome_audit(prepared, cohort)
    output = output_path(args.output, prepared["input_roots"] +
                         [str(selection.parent), str(protocol.parent)])
    output.mkdir()
    write_json(output / "cohort.json", cohort)
    write_json(output / "audit.json", audit)
    write_json(output / "completion.json", dict(
        schema_version=1, artifact_kind="chance_sequence_cohort_completion", purpose=prepared["purpose"],
        protocol=identity(protocol), selection=identity(selection), cohort=identity(output / "cohort.json"),
        audit=identity(output / "audit.json"), resources=resources(started),
        scientific_assessment="not_performed"))
    print(f"sequence cohort complete: {output}; scientific assessment not performed")
    return 0


def fit_command(args):
    config = read_json(Path(args.config).resolve(strict=True))
    validate_recipe(config)
    cohort = read_cohort(identity(Path(args.cohort).resolve(strict=True)),
                         read_json(Path(args.selection).resolve(strict=True))["purpose"])
    require(cohort["definition"] == DEFINITION, "sequence fitting requires the common complete-case cohort")
    if cohort["purpose"] == "research":
        training_window(cohort)
    args.out, args.quantity = args.output, QUANTITY
    return component_fit(args)


def evaluate_command(args):
    component = validate_component(read_json(Path(args.component).resolve(strict=True)))
    require(component["quantity"] == QUANTITY and validate_recipe(component["config"]) == args.arm and
            component["training_cohort"]["definition"] == DEFINITION and
            component["extraction"] is None,
            "sequence evaluation requires the declared freshly fitted arm")
    if component["purpose"] == "research":
        training = read_cohort(component["training_cohort"]["membership_identity"], "research")
        assessment = read_cohort(identity(Path(args.cohort).resolve(strict=True)), "research")
        validate_window(training_window(training), training, assessment, "research")
    args.out = args.output
    return component_evaluate(args)


def validate_audit(audit, cohort):
    from hockey_stats.chance_cohort import validate_outcome_audit_document

    return validate_outcome_audit_document(audit, cohort)


def independent_loss(left, right, reported):
    """subtract stored native log losses in decimal arithmetic, then pool once."""
    total, count, identical = Decimal(0), 0, 0
    with localcontext() as context:
        context.prec = 60
        for before, after in paired_rows(left, right):
            if before["study_inclusion"] != "included":
                continue
            field = "log_p" if before["observed"] else "log_not_p"
            total += Decimal.from_float(float(before[field])) - Decimal.from_float(float(after[field]))
            count += 1
            identical += before["log_p"] == after["log_p"] and before["log_not_p"] == after["log_not_p"]
        estimate = float(total / count) if count else None
    require((estimate is None and reported is None) or
            (estimate is not None and reported is not None and agrees(estimate, reported) and
             (estimate < -DEADBAND) == (reported < -DEADBAND)),
            "independent native log-loss arithmetic or deadband direction disagrees")
    require(identical != count or reported in (None, 0),
            "identical native predictions must have exactly zero paired loss")
    return dict(method="60-digit decimal subtraction of saved log probabilities, pooled by included count",
                count=count, identical_prediction_count=identical, independent_delta=estimate,
                reported_delta=reported, difference=estimate - reported if count else None)


def failure_evidence(reference, inputs, protocol, *, coverage, cohorts):
    """a manual failure receipt may explicitly bind already completed preflight audits."""
    path = linked_path(reference)
    if path.suffix == ".log":
        return None  # the explicit log format makes no structured accounting claim.
    require(path.suffix == ".json", "failure evidence must declare .json diagnostics/receipt or .log format")
    document = read_json(path)
    require(isinstance(document, dict), "structured failure evidence must be an object")
    if document.get("artifact_kind") == "chance_component_fit":
        require(type(document["schema_version"]) is int and document["schema_version"] == 3 and
                document["status"] == "failed", "schema-3 failed native fit diagnostics required")
        return document
    require(set(document) == {"schema_version", "artifact_kind", "purpose", "protocol",
                              "diagnostics", "log", "stop_reason", "cohorts"} and
            type(document["schema_version"]) is int and document["schema_version"] == 1 and
            document["artifact_kind"] == "chance_sequence_failure" and
            document["purpose"] == inputs["purpose"] and document["protocol"] == protocol and
            isinstance(document["stop_reason"], str) and bool(document["stop_reason"].strip()) and
            (document["diagnostics"] is not None or document["log"] is not None),
            "sequence failure receipt binding mismatch")
    require(set(document["cohorts"]) == set(WINDOWS), "failure receipt requires both explicit windows")
    for window in WINDOWS:
        require(set(document["cohorts"][window]) == {"training", "assessment"},
                "failure receipt requires both explicit cohort partitions")
        for partition in ("training", "assessment"):
            completion_reference = document["cohorts"][window][partition]
            if completion_reference is None:
                continue
            completion = read_json(linked_path(completion_reference))
            expected = inputs["windows"][window]["baseline"][f"{partition}_cohort"]
            require(expected is not None and completion["cohort"] == expected and
                    inputs["windows"][window]["sequence"][f"{partition}_cohort"] == expected and
                    set(completion) == {"schema_version", "artifact_kind", "purpose", "protocol",
                                        "selection", "cohort", "audit", "resources", "scientific_assessment"} and
                    type(completion["schema_version"]) is int and completion["schema_version"] == 1 and
                    completion["artifact_kind"] == "chance_sequence_cohort_completion" and
                    completion["purpose"] == inputs["purpose"] and completion["protocol"] == protocol and
                    completion["scientific_assessment"] == "not_performed",
                    "failure receipt preflight completion binding mismatch")
            cohort = read_cohort(completion["cohort"], inputs["purpose"])
            require(completion["selection"] == selection_reference(cohort),
                    "failure receipt preflight selection identity mismatch")
            audit = validate_audit(read_json(linked_path(completion["audit"])), cohort)
            previous = coverage[window].get(partition)
            require(previous is None or previous == audit, "failure receipt preflight outcome audits disagree")
            coverage[window][partition], cohorts[window, partition] = audit, cohort
    if document["log"] is not None:
        linked_path(document["log"])
    if document["diagnostics"] is None:
        return None
    diagnostic = read_json(linked_path(document["diagnostics"]))
    require(diagnostic["artifact_kind"] == "chance_component_fit" and
            type(diagnostic["schema_version"]) is int and diagnostic["schema_version"] == 3 and
            diagnostic["status"] == "failed", "failure receipt diagnostics require a failed native fit")
    return diagnostic


def report_command(args):
    started = time.monotonic()
    inputs_path = Path(args.inputs).resolve(strict=True)
    protocol = identity(Path(args.protocol).resolve(strict=True))
    inputs = validate_report_inputs(read_json(inputs_path))
    purpose = inputs["purpose"]
    output = output_path(args.output, [str(inputs_path.parent), str(Path(protocol["path"]).parent)])
    cells, comparisons, coverage = {}, {}, {window: {} for window in WINDOWS}
    fitted_implementation = None
    cohorts, failures = {}, {}
    for window in WINDOWS:
        for arm in ARMS:
            reference = inputs["windows"][window][arm]["failure"]
            if reference is not None:
                key = reference["path"], reference["sha256"]
                if key not in failures:
                    failures[key] = failure_evidence(reference, inputs, protocol, coverage=coverage, cohorts=cohorts)
    for window in WINDOWS:
        cells[window] = {}
        for arm in ARMS:
            cell = inputs["windows"][window][arm]
            record = deepcopy(cell)
            config = None if cell["config"] is None else read_json(linked_path(cell["config"]))
            require(config is None or validate_recipe(config) == arm, "cell config declares another recipe")
            training = None if cell["training_cohort"] is None else read_cohort(cell["training_cohort"], purpose)
            assessment = None if cell["assessment_cohort"] is None else read_cohort(cell["assessment_cohort"], purpose)
            if training is not None and assessment is not None:
                validate_window(window, training, assessment, purpose)
                for partition, cohort in (("training", training), ("assessment", assessment)):
                    key = window, partition
                    require(key not in cohorts or cohorts[key] == cohort,
                            "matched arms must bind exactly the same cohort document and keys")
                    cohorts[key] = cohort
            if cell["failure"] is not None:
                linked_path(cell["failure"])
            record.update(diagnostics=None, fit_resources=None, evaluation_resources=None,
                          metrics=None, omitted_baseline=None)
            if cell["fit"] is None:
                failed = None if cell["failure"] is None else failures[cell["failure"]["path"], cell["failure"]["sha256"]]
                if cell["status"] == "failed" and failed is not None:
                    require(training is not None and config is not None and
                            failed["purpose"] == purpose and failed["quantity"] == QUANTITY and
                            failed["protocol_identity"] == protocol and failed["config_identity"] == cell["config"] and
                            failed["training_cohort_identity"] == cell["training_cohort"] and
                            failed["preparation_identity"] == PREPARATION_IDENTITY and
                            failed["selection"] == training["selection"] and failed["inputs"] == training["inputs"] and
                            failed["training_game_dates"] == training["game_dates"] and
                            failed["stage_design"]["families"] == config["stage_families"]["r"] and
                            failed["diagnostics"]["converged"] is False,
                            "failed native fit diagnostics/config/source/cohort binding mismatch")
                    audit = validate_audit(failed["training_cohort_audit"], training)
                    previous = coverage[window].get("training")
                    require(previous is None or previous == audit, "failed native fit preflight audit changed")
                    coverage[window]["training"] = audit
                    record.update(diagnostics=failed["diagnostics"], fit_resources=failed["resources"])
                cells[window][arm] = record
                continue
            completion = read_json(linked_path(cell["fit"]))
            require(set(completion) == {
                        "artifact_kind", "schema_version", "purpose", "protocol", "config",
                        "selection", "preparation_identity", "training_cohort", "fit", "component",
                        "scientific_assessment",
                    } and type(completion["schema_version"]) is int and completion["schema_version"] == 3 and
                    completion["artifact_kind"] == "chance_component_fit_completion" and
                    completion["purpose"] == purpose and completion["protocol"] == protocol and
                    completion["config"] == cell["config"] and
                    completion["selection"] == selection_reference(training) and
                    completion["preparation_identity"] == PREPARATION_IDENTITY and
                    completion["training_cohort"] == cell["training_cohort"] and
                    completion["scientific_assessment"] == "not_performed",
                    "schema-3 successful fit completion binding mismatch")
            component_reference = completion["component"]
            component = validate_component(read_json(linked_path(component_reference)))
            fit_record = read_json(linked_path(completion["fit"]))
            require(training is not None and config is not None and component["purpose"] == purpose and
                    component["quantity"] == QUANTITY and component["config"] == config and
                    component["config_identity"] == cell["config"] and
                    component["protocol_identity"] == protocol and component["extraction"] is None and
                    component["training_cohort"]["definition"] == DEFINITION and
                    component["training_cohort"]["membership_identity"] == cell["training_cohort"] and
                    component["selection"] == training["selection"] and
                    component["inputs"] == training["inputs"] and
                    component["training_game_dates"] == training["game_dates"],
                    "fresh native fit/config/training cohort/protocol binding mismatch")
            require(fit_record["schema_version"] == 3 and fit_record["status"] == "fitted" and
                    fit_record["diagnostics"] == component["diagnostics"] and
                    all(fit_record[field] == component[field] for field in (
                        "purpose", "quantity", "config_identity", "protocol_identity", "selection",
                        "inputs", "implementation", "training_game_dates", "preparation_identity")) and
                    fit_record["stage_design"] == component["layout"]["design"],
                    "fit diagnostics do not reconcile to the completed native component")
            require(fit_record["training_cohort_identity"] == cell["training_cohort"],
                    "fit diagnostics bind another training cohort")
            require(component["diagnostics"]["converged"] is True,
                    "successful completion contains a nonconverged component")
            training_audit = validate_audit(fit_record["training_cohort_audit"], training)
            require(0 < training_audit["included"]["goals"] < training_audit["included"]["attempts"],
                    "each common training cohort requires both recorded goal outcomes")
            if purpose == "research":
                clean_implementation(component["implementation"])
                require(fitted_implementation is None or fitted_implementation == component["implementation"],
                        "four fresh fits must use one frozen implementation")
                fitted_implementation = component["implementation"]
            existing = coverage[window].get("training")
            require(existing is None or existing == training_audit,
                    "matched-arm training outcome audits disagree")
            coverage[window]["training"] = training_audit
            record.update(component=component_reference, diagnostics=component["diagnostics"],
                          fit_resources=fit_record["resources"], training_cohort=cell["training_cohort"],
                          training_actor_counts={field: component["layout"][field] for field in
                                                 ("shooters", "goalies", "shooter_counts", "goalie_counts", "seasons")})
            if cell["evaluation"] is not None:
                evaluated = read_json(linked_path(cell["evaluation"]))
                require(set(evaluated) == {
                            "artifact_kind", "schema_version", "purpose", "protocol", "selection",
                            "preparation_identity", "training_cohort", "assessment_cohort", "component",
                            "evaluation", "attempts", "arm", "scientific_assessment",
                        } and type(evaluated["schema_version"]) is int and evaluated["schema_version"] == 3 and
                        evaluated["artifact_kind"] == "chance_component_evaluation_completion" and
                        evaluated["purpose"] == purpose and evaluated["protocol"] == protocol and
                        evaluated["selection"] == selection_reference(assessment) and
                        evaluated["preparation_identity"] == PREPARATION_IDENTITY and
                        evaluated["training_cohort"] == cell["training_cohort"] and
                        evaluated["assessment_cohort"] == cell["assessment_cohort"] and
                        evaluated["component"] == component_reference and evaluated["arm"] == arm and
                        evaluated["scientific_assessment"] == "not_performed",
                        "schema-3 successful evaluation completion binding mismatch")
                evaluation = validate_evaluation(
                    evaluated["evaluation"], component_reference, selection_reference(assessment),
                    protocol, QUANTITY, purpose, component=component,
                    cohort_reference=cell["assessment_cohort"], arm=arm)
                require(evaluation["implementation"] == component["implementation"],
                        "fit and evaluation implementations differ")
                require(evaluated["attempts"] == evaluation["attempts"],
                        "evaluation completion binds another prediction stream")
                assessment_audit = validate_audit(evaluation["assessment_cohort_audit"], assessment)
                existing = coverage[window].get("assessment")
                require(existing is None or existing == assessment_audit,
                        "matched-arm assessment outcome audits disagree")
                coverage[window]["assessment"] = assessment_audit
                record.update(evaluation_document=evaluated["evaluation"], metrics=evaluation["metrics"],
                              omitted_baseline=evaluation["omitted_baseline"],
                              evaluation_resources=evaluation["resources"], _evaluation=evaluation)
            cells[window][arm] = record
        baseline, sequence = cells[window]["baseline"], cells[window]["sequence"]
        comparison = None
        if baseline["status"] == sequence["status"] == "complete":
            require(baseline["training_cohort"] == sequence["training_cohort"] and
                    baseline["assessment_cohort"] == sequence["assessment_cohort"] and
                    baseline["training_actor_counts"] == sequence["training_actor_counts"],
                    "matched arms have different cohort identities or included actor counts")
            before, after = baseline.pop("_evaluation"), sequence.pop("_evaluation")
            require(all(before[field] == after[field] for field in
                        ("selection", "inputs", "game_dates", "coverage", "cohort", "assessment_cohort_audit")),
                    "paired assessment identities, source coverage or cohort accounting differ")
            comparison = compare_pair(before, after)
            comparison["paired_groups"] = {name: comparison["paired_groups"][name] for name in REPORT_GROUPS}
            comparison["changed_own_groups"] = {name: comparison["changed_own_groups"][name] for name in REPORT_GROUPS}
            before_metric, after_metric = comparison["baseline_metrics"], comparison["changed_metrics"]
            delta = comparison["delta"]["log_loss"]["games"]["estimate"]
            comparison["arithmetic_verification"] = independent_loss(
                linked_path(before["attempts"]), linked_path(after["attempts"]), delta)
            comparison.update(relative_log_loss_change=delta / before_metric["log_loss"]
                              if before_metric["log_loss"] else None,
                              change_absolute_pooled_residual_pp=
                              abs(after_metric["predicted_minus_observed_pp"]) -
                              abs(before_metric["predicted_minus_observed_pp"])
                              if before_metric["count"] else None)
        for record in cells[window].values():
            record.pop("_evaluation", None)
        comparisons[window] = comparison
    direction, recommendation = decision(comparisons, purpose=purpose)
    if purpose == "research" and fitted_implementation is not None:
        require(implementation() == fitted_implementation,
                "report must use the same frozen implementation as all four fitted models")
    all_season = None
    partitions = (("development", "training"), ("development", "assessment"),
                  ("season_transfer", "assessment"))
    if all(partition in coverage[window] for window, partition in partitions):
        keys = [set(cohorts[window, partition]["game_dates"]) for window, partition in partitions]
        require(not keys[0] & keys[1] and not keys[0] & keys[2] and not keys[1] & keys[2],
                "distinct-season source audit partitions overlap")
        all_season = {population: {
            field: sum(coverage[window][partition][population][field] for window, partition in partitions)
            for field in ("attempts", "goals")}
            for population in ("source_applicable", "included", "omitted")}
        all_season["games"] = sum(len(key) for key in keys)
        if purpose == "research":
            require(all_season == dict(source_applicable=dict(attempts=264711, goals=15709),
                                       included=dict(attempts=256248, goals=15113),
                                       omitted=dict(attempts=8463, goals=596), games=3936),
                    "distinct-source preflight totals do not reconcile to the frozen 03k receipt")
    document = dict(
        schema_version=1, artifact_kind="chance_sequence_result", purpose=purpose,
        inputs=identity(inputs_path), protocol=protocol, implementation=implementation(),
        quantity=QUANTITY, population="recorded goal conversion on common included source-eligible unblocked attempts",
        direction=direction, recommendation=recommendation,
        scientific_assessment="not_admitted" if purpose == "research" else "not_performed",
        execution_status="complete" if all(comparisons[window] is not None for window in WINDOWS) else "incomplete",
        coverage=dict(windows=coverage, distinct_source_all_season=all_season), cells=cells,
        comparisons=comparisons, resampling=RESAMPLING,
        arithmetic_deadband_nats_per_attempt=DEADBAND, limitations=LIMITATIONS,
        resources=resources(started),
    )
    output.mkdir()
    figure = save_figure(document, output)
    document["figure"] = identity(figure)
    document["resources"].update(resources(started), figure_bytes=figure.stat().st_size)
    write_json(output / "result.json", document)
    write_json(output / "completion.json", dict(
        schema_version=1, artifact_kind="chance_sequence_report_completion", purpose=purpose,
        inputs=identity(inputs_path), protocol=protocol, result=identity(output / "result.json"),
        figure=identity(figure), scientific_assessment=document["scientific_assessment"]))
    print(f"sequence report complete: {output}; {direction}; {recommendation}")
    return 0


def save_figure(document, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(3, 2, figsize=(12, 10), sharex="row", sharey="row",
                                gridspec_kw=dict(height_ratios=[1, 1.5, 1]))
    colors = dict(baseline="#555555", sequence="#176b87")
    for column, window in enumerate(WINDOWS):
        comparison = document["comparisons"][window]
        axes[0, column].axvline(0, color="#333333", lw=.8)
        axes[1, column].axhline(0, color="#333333", lw=.8)
        axes[0, column].set_title(window.replace("_", " "))
        axes[0, column].set_yticks([0, 1, 2], ["whole game", "7-day block", "14-day block"])
        axes[0, column].set_xlabel("sequence − baseline log loss, nats/included attempt")
        axes[1, column].set_xlim(0, 1)
        axes[2, column].set_xlabel("baseline probability bin; identical membership for both arms")
        if comparison is None:
            for row in range(3):
                axes[row, column].text(.5, .5, "comparison incomplete", transform=axes[row, column].transAxes,
                                       ha="center", va="center")
            continue
        for index, unit in enumerate(("games", "calendar_7_day", "calendar_14_day")):
            value = comparison["delta"]["log_loss"][unit]
            if value["estimate"] is not None:
                axes[0, column].plot(value["estimate"], index, "o", color=colors["sequence"], ms=5)
            if value["interval"] is not None:
                axes[0, column].hlines(index, *value["interval"], color=colors["sequence"], lw=1.3)
            else:
                axes[0, column].annotate("interval undefined", (value["estimate"] or 0, index),
                                         xytext=(6, 8 if index == 0 else -13),
                                         textcoords="offset points", fontsize=7)
        bins = comparison["paired_calibration"]
        xs = [(bucket["lower"] + bucket["upper"]) / 2 for bucket in bins]
        for arm, key in (("baseline", "baseline"), ("sequence", "changed")):
            residuals = [bucket[key]["predicted_minus_observed_pp"]
                         if bucket[key]["count"] else np.nan for bucket in bins]
            axes[1, column].plot(xs, residuals, "o-", color=colors[arm], ms=3, lw=.7, label=arm)
        counts = [bucket["baseline"]["count"] for bucket in bins]
        axes[2, column].bar(xs, counts, width=.042, color="#b5b5b5")
        for x, count in zip(xs, counts, strict=True):
            if count:
                axes[2, column].annotate(f"n={count:,}", (x, count), xytext=(0, 3),
                                         textcoords="offset points", fontsize=6, rotation=90, ha="center")
        axes[2, column].set_yscale("symlog", linthresh=1)
        metric = comparison["baseline_metrics"]
        axes[1, column].set_title(f"paired baseline bins; n={metric['count']:,}; goals={metric['observed_positive_count']:,}",
                                  fontsize=9)
        axes[1, column].legend(fontsize=8)
    axes[1, 0].set_ylabel("predicted − observed, percentage points")
    axes[2, 0].set_ylabel("included attempts per baseline bin")
    caption = (
        "recorded goal conversion on common included source-eligible unblocked attempts. lower loss is better.\n"
        "95% intervals are conditional on fitted models; paired pooled sums/counts, 2,000 PCG64 draws per method.\n"
        "bin panels are descriptive and share baseline membership within each window; own-arm bins remain separate in result.json.\n"
        "missing sequence rows are omitted selectively; baseline omission predictions are common-trained. coordinates/continuity are recorded proxies, not physical release truth."
    )
    if document["purpose"] == "fixture_exercise":
        caption = "fixture software exercise; scientific assessment not performed.\n" + caption
    figure.tight_layout(rect=(0, .13, 1, 1))
    figure.text(.025, .015, caption, fontsize=8, va="bottom")
    path = output / "sequence.png"
    figure.savefig(path, dpi=180)
    plt.close(figure)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    options = {
        "cohort": ("selection", "protocol", "output"),
        "fit": ("selection", "cohort", "config", "protocol", "output"),
        "evaluate": ("selection", "cohort", "component", "protocol", "output"),
        "report": ("inputs", "protocol", "output"),
    }
    for name, required in options.items():
        child = commands.add_parser(name, allow_abbrev=False)
        for option in required:
            child.add_argument(f"--{option}", required=True, action=Once)
        if name == "evaluate":
            child.add_argument("--arm", choices=ARMS, required=True, action=Once)
    args = parser.parse_args()
    try:
        return {"cohort": cohort_command, "fit": fit_command,
                "evaluate": evaluate_command, "report": report_command}[args.command](args)
    except (InputContractError, OSError, KeyError, TypeError, ValueError, OverflowError) as error:
        print(f"sequence {args.command} failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
