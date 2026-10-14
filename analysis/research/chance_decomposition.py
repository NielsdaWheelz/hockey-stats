"""manual native conversion decomposition; completed research is not admission."""

import argparse
from copy import deepcopy
import hashlib
from itertools import zip_longest
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

from hockey_stats.artifacts import write_json
from hockey_stats.captures import InputContractError
from hockey_stats.chance import (
    component_prediction_context, predict_component, validate_component,
)
from hockey_stats.chance_cli import identity, output_path, read_json
from hockey_stats.chance_cohort import (
    component_cohort, outcome_audit, target_audit, validate_cohort,
    validate_cohort_document, validate_outcome_audit, validate_outcome_audit_document,
    validate_target_audit,
)
from hockey_stats.chance_data import prepare_core
from hockey_stats.chance_evaluation import (
    binary_record, diagnostic_groups, summarize_component,
)
from hockey_stats.chance_features import PREPARATION_IDENTITY
from hockey_stats.chance_targets import (
    DECOMPOSITION_QUANTITIES as QUANTITIES, component_target, recorded_on_net,
)
from hockey_stats.cli import Once
from chance_development import (
    compare_paired_records, component_setup, fit_prepared, implementation,
    predict_component_rows, resources, rows, source_identities, validate_evaluation,
    validate_prepared_selection,
)
from chance_history import (
    DEADBAND, DEFINITION, FAMILIES, REPORT_GROUPS, RESAMPLING, WINDOWS,
    read_cohort as read_direct_cohort, selection_reference, validate_population,
    validate_recipe, validate_window, verify_component,
)
from chance_review import agrees, clean_implementation, linked_path, require

METRICS = ("on_net", "goal_given_on_net", "composed_goal")
DIRECT = "unblocked_conversion"
SOURCE_RESULT_SHA256 = "7f846890843811a10386f5da40818ac0e914ac27436d8e29678f3a91e3cfc123"
CONFIG_REFERENCE = dict(
    path="/Volumes/Expansion/hockey-stats/runs/chance-03n-20261013/inputs/config.json",
    sha256="1a52e1bbb5d9ef736b6781c18cfa66bf3c869817c6da8b6e9d9c741b417c1bf2",
)
SELECTION_ROOT = Path("/Volumes/Expansion/hockey-stats/runs/chance-03n-20261013/inputs")
SELECTIONS = {
    "development-short-training.json": ("c4b8918f44a88a0bdbc53ed9bfd37f196850cf18823a44e6dbe752118532de5a", 87618),
    "development-assessment.json": ("30a6e0ae1338e2b68a8d89101d8e0b5e537ee6c4357f78ca5f7a5974aea32791", 31658),
    "season_transfer-short-training.json": ("7b78ea4aaa7bbf0afa7c9f94bd8f54ffeabca51b45a079fe44e293b0a1627db9", 119276),
    "season_transfer-assessment.json": ("c99b1e8e43b6d807f3ea326cd87b0e3843fe11ff8da7d601c14a31cc91965905", 56111),
}
REUSE_WINDOW_FIELDS = {
    "fit", "evaluation", "training_selection", "assessment_selection",
    "training_cohort", "assessment_cohort",
}
ROW_FIELDS = {
    "schema_version", "game_id", "source_index", "event_id", "game_date", "season",
    "source_identity", "source_status", "source_reasons", "study_inclusion",
    "study_reasons", "status", "blocked", "goal", "on_net", "diagnostic_groups",
    "stages", "composed_goal",
}
STAGE_FIELDS = {
    "metric_applicable", "observed", "log_p", "log_not_p", "season_basis",
    "state_season", "actor_evidence",
}
ASSESSMENT_FIELDS = {
    "schema_version", "artifact_kind", "purpose", "protocol", "implementation",
    "selection", "inputs", "preparation_identity", "game_dates", "coverage",
    "cohorts", "components", "target_audits", "attempts", "metrics", "groups",
    "per_game", "resources", "scientific_assessment",
}
SOURCE_GROUPS = (
    "original_type", "model_type", "recent_context", "recent_kind", "recent_team",
    "recent_delay", "home_away", "role", "calendar_month", "sequence_index",
)
LIMITATIONS = [
    "two independent coefficient sets and the smaller conditional population change effective shrinkage; this is an estimator package comparison, not causal isolation of factorization",
    "recorded on-net and goal labels are source classifications; shot-on-goal does not distinguish freezes, rebounds or in-play outcomes",
    "both stages extrapolate to all eligible unblocked attempts, including observed misses; recorded location/type/context are not live pre-release predictors",
    "95% intervals condition on two reused direct controls and four stage fits, omit fitting/selection/source uncertainty and perform no bootstrap fits",
    "research-exposed chronological windows overlap in training and are not independent confirmation; source coordinate, membership, type-recording and coverage limitations remain",
    "native annual actor effects borrow through fixed penalties; unseen actor residuals are zero and 2025–26 uses the latest fitted states; nuisance actor logits are not player ability cards",
    "native success can use relative-objective stopping before gradient tolerance; the arithmetic deadband is neither a solver-error bound nor a useful-effect guarantee",
    "unchanged tip/deflection actor treatment, mirror pooling and further layers remain separate experiments; no scientific admission, integration, 04 or publication follows",
    "later opportunity reference standardization must average the product over one joint actor reference; separately averaged layer probabilities cannot generally be multiplied",
    "external-only fit storage accepts manual rerun risk after interrupted work; completed expensive fits retain their original paths",
]


def artifact_roots(value):
    """locate bound input parents before choosing an exclusive output directory."""
    if isinstance(value, dict):
        if set(value) == {"path", "sha256"}:
            return [str(linked_path(value).parent)]
        return [root for item in value.values() for root in artifact_roots(item)]
    if isinstance(value, list):
        return [root for item in value for root in artifact_roots(item)]
    return []


def completion(reference, kind, extra, *, purpose, protocol=None):
    document = read_json(linked_path(reference))
    common = {"schema_version", "artifact_kind", "purpose", "implementation", "scientific_assessment"}
    require(isinstance(document, dict) and set(document) == common | set(extra) and
            type(document["schema_version"]) is int and document["schema_version"] == 1 and
            document["artifact_kind"] == f"chance_decomposition_{kind}_completion" and
            document["purpose"] == purpose and document["scientific_assessment"] == "not_performed" and
            (protocol is None or document["protocol"] == protocol),
            f"invalid decomposition {kind} completion schema or bindings")
    if purpose == "research":
        clean_implementation(document["implementation"])
    artifact_roots({key: document[key] for key in extra})
    return document


def read_bundle(reference, prepared, quantity):
    path = linked_path(reference)
    cohort = validate_cohort_document(read_json(path))
    require(cohort["purpose"] == prepared["purpose"] and cohort["quantity"] == quantity and
            cohort["definition"] == DEFINITION and cohort["preparation_identity"] == PREPARATION_IDENTITY,
            "decomposition cohort purpose/quantity/definition/preparation mismatch")
    validate_cohort(cohort, prepared)
    selected = selection_reference(cohort)
    validate_prepared_selection(prepared, linked_path(selected))
    audit = read_json(path.with_name("outcome_audit.json"))
    validate_outcome_audit_document(audit, cohort)
    validate_outcome_audit(audit, prepared, cohort)
    target_path = path.with_name("target_audit.json")
    target = read_json(target_path)
    validate_target_audit(target, prepared, cohort,
                          selection_identity=selected, cohort_identity=reference)
    if prepared["purpose"] == "research":
        path = Path(selected["path"])
        expected = SELECTIONS.get(path.name)
        require(path.parent == SELECTION_ROOT and expected is not None and
                selected["sha256"] == expected[0] and target["counts"]["on_net"] == expected[1],
                "research target source selection/on-net counts differ from the independently frozen audit")
    return cohort, audit, target, identity(target_path)


def verify_pair(prepared, cohorts, audits, *, window=None, partition=None):
    q, g = (cohorts[quantity] for quantity in QUANTITIES)
    require(q["game_dates"] == g["game_dates"] and q["inputs"] == g["inputs"] and
            q["selection"] == g["selection"], "stage cohorts bind different source selections")
    for attempt, qrow, grow in zip(prepared["attempts"], q["rows"], g["rows"], strict=True):
        require((qrow["study_inclusion"] == "included" and
                 component_target(attempt, QUANTITIES[0]) is True) ==
                (grow["study_inclusion"] == "included"),
                f"{attempt['game_id']}:{attempt['source_index']}: q positives differ from g included keys")
    validate_population(q, audits[QUANTITIES[0]], window=window, partition=partition)


def cohort_command(args):
    started = time.monotonic()
    selection = Path(args.selection).resolve(strict=True)
    prepared = prepare_core(selection)
    validate_prepared_selection(prepared, selection)
    if prepared["purpose"] == "research":
        expected = SELECTIONS.get(selection.name)
        require(selection.parent == SELECTION_ROOT and expected is not None and
                identity(selection)["sha256"] == expected[0],
                "research cohort requires an immutable original short selection")
    output = output_path(args.out, prepared["input_roots"] + [str(selection.parent)])
    cohorts = {quantity: component_cohort(prepared, quantity=quantity, required_families=[])
               for quantity in QUANTITIES}
    audits = {quantity: outcome_audit(prepared, cohort) for quantity, cohort in cohorts.items()}
    verify_pair(prepared, cohorts, audits)
    output.mkdir()
    cohort_refs, outcome_refs, target_refs = {}, {}, {}
    for quantity in QUANTITIES:
        destination = output / quantity
        destination.mkdir()
        write_json(destination / "cohort.json", cohorts[quantity])
        cohort_refs[quantity] = identity(destination / "cohort.json")
        write_json(destination / "outcome_audit.json", audits[quantity])
        outcome_refs[quantity] = identity(destination / "outcome_audit.json")
        document = target_audit(prepared, cohorts[quantity], selection_identity=identity(selection),
                                cohort_identity=cohort_refs[quantity])
        write_json(destination / "target_audit.json", document)
        target_refs[quantity] = identity(destination / "target_audit.json")
        read_bundle(cohort_refs[quantity], prepared, quantity)
    write_json(output / "completion.json", dict(
        schema_version=1, artifact_kind="chance_decomposition_cohort_completion",
        purpose=prepared["purpose"], implementation=implementation(),
        scientific_assessment="not_performed", selection=identity(selection),
        cohorts=cohort_refs, outcome_audits=outcome_refs, target_audits=target_refs))
    print(f"decomposition cohorts complete: {output}; scientific assessment not performed")
    return 0


def validate_reuse_inputs(document):
    require(isinstance(document, dict) and set(document) ==
            {"schema_version", "purpose", "source_result", "config", "windows"} and
            type(document["schema_version"]) is int and document["schema_version"] == 1 and
            document["purpose"] in ("research", "fixture_exercise") and
            isinstance(document["windows"], dict) and set(document["windows"]) == set(WINDOWS),
            "schema-1 fixed decomposition reuse inputs required")
    artifact_roots({key: document[key] for key in ("source_result", "config")})
    source = read_json(linked_path(document["source_result"]))
    require(source["schema_version"] == 1 and source["artifact_kind"] == "chance_history_result" and
            source["purpose"] == document["purpose"] and source["execution_status"] == "complete" and
            source["quantity"] == DIRECT,
            "control source result must be the completed native history study")
    linked_path(source["protocol"])
    linked_path(source["inputs"])
    if document["purpose"] == "research":
        require(document["source_result"]["sha256"] == SOURCE_RESULT_SHA256 and
                document["config"] == CONFIG_REFERENCE,
                "research direct reuse must bind the immutable 03n result and config")
        clean_implementation(source["implementation"])
    validate_recipe(read_json(linked_path(document["config"])))
    source_inputs = read_json(linked_path(source["inputs"]))
    for window in WINDOWS:
        entry = document["windows"][window]
        require(isinstance(entry, dict) and set(entry) == REUSE_WINDOW_FIELDS,
                "control reuse requires both complete fixed window binding chains")
        artifact_roots(entry)
        cell = source["cells"][window]["short"]
        require(cell["status"] == "complete" and cell["config"] == document["config"] and
                all(entry[field] == cell[field] == source_inputs["windows"][window]["short"][field]
                    for field in ("fit", "evaluation", "training_cohort", "assessment_cohort")),
                "reuse control references differ from original result/input bindings")
        if document["purpose"] == "research":
            require(entry["training_selection"]["path"] ==
                    str(SELECTION_ROOT / f"{window}-short-training.json") and
                    entry["assessment_selection"]["path"] ==
                    str(SELECTION_ROOT / f"{window}-assessment.json"),
                    "research reuse changed the original short selections")
    return source


def read_fit(reference, cohort_reference, cohort, audit, *, config, protocol, quantity, purpose,
             expected_implementation=None):
    document = read_json(linked_path(reference))
    require(isinstance(document, dict) and set(document) == {
        "artifact_kind", "schema_version", "purpose", "protocol", "config", "selection",
        "preparation_identity", "training_cohort", "fit", "component", "scientific_assessment",
    } and type(document["schema_version"]) is int and document["schema_version"] == 3 and
        document["artifact_kind"] == "chance_component_fit_completion" and
        document["purpose"] == purpose and document["protocol"] == protocol and
        document["config"] == config and document["selection"] == selection_reference(cohort) and
        document["preparation_identity"] == PREPARATION_IDENTITY and
        document["training_cohort"] == cohort_reference and document["scientific_assessment"] == "not_performed",
        "native fit completion schema/binding mismatch")
    component = validate_component(read_json(linked_path(document["component"])))
    fit = read_json(linked_path(document["fit"]))
    require(component["purpose"] == purpose and component["quantity"] == quantity and
            component["extraction"] is None and component["config_identity"] == config and
            component["protocol_identity"] == protocol and
            component["training_cohort"]["membership_identity"] == cohort_reference and
            component["training_cohort"]["definition"] == DEFINITION and
            component["training_cohort"]["excluded_count"] == 0 and
            component["training_game_dates"] == cohort["game_dates"] and
            component["diagnostics"]["converged"] is True and
            component["config"] == validate_recipe(read_json(linked_path(config))) and
            all(component[field] == cohort[field] for field in
                ("purpose", "selection", "inputs", "preparation_identity")),
            "native fitted component target/config/protocol/source mismatch")
    require(fit["schema_version"] == 3 and fit["artifact_kind"] == "chance_component_fit" and
            fit["status"] == "fitted" and fit["diagnostics"] == component["diagnostics"] and
            fit["training_cohort_identity"] == cohort_reference and
            fit["training_cohort_audit"] == audit and
            fit["stage_design"] == component["layout"]["design"] and
            all(fit[field] == component[field] for field in (
                "purpose", "quantity", "config_identity", "protocol_identity", "selection", "inputs",
                "implementation", "preparation_identity", "training_game_dates")) and
            (expected_implementation is None or component["implementation"] == expected_implementation),
            "native fit source/design/diagnostics/implementation mismatch")
    if purpose == "research":
        clean_implementation(component["implementation"])
    return document, component, fit


def reuse_command(args):
    started = time.monotonic()
    inputs_path = Path(args.inputs).resolve(strict=True)
    protocol_path = Path(args.protocol).resolve(strict=True)
    inputs = read_json(inputs_path)
    source = validate_reuse_inputs(inputs)
    purpose, protocol = inputs["purpose"], identity(protocol_path)
    current = implementation()
    if purpose == "research":
        clean_implementation(current)
    roots = [str(inputs_path.parent), str(protocol_path.parent)] + artifact_roots(inputs)
    checks, verifications = {}, {}
    config = validate_recipe(read_json(linked_path(inputs["config"])))
    for window in WINDOWS:
        entry = inputs["windows"][window]
        training, training_audit = read_direct_cohort(entry["training_cohort"], purpose)
        assessment, assessment_audit = read_direct_cohort(entry["assessment_cohort"], purpose)
        require(selection_reference(training) == entry["training_selection"] and
                selection_reference(assessment) == entry["assessment_selection"],
                "control cohort/selection identity changed")
        validate_window(window, "short", training, assessment, training_audit, assessment_audit)
        fitted, component, fit = read_fit(
            entry["fit"], entry["training_cohort"], training, training_audit,
            config=inputs["config"], protocol=source["protocol"], quantity=DIRECT,
            purpose=purpose, expected_implementation=source["implementation"])
        original = source["cells"][window]["short"]
        require(fitted["component"] == original["component"], "original direct component identity changed")
        objective, source_roots = verify_component(component, fitted["component"], training,
                                                   entry["training_cohort"], source["protocol"])
        roots.extend(source_roots)
        prepared = prepare_core(linked_path(entry["training_selection"]))
        validate_cohort(training, prepared)
        validate_outcome_audit(training_audit, prepared, training)
        q = component_cohort(prepared, quantity=QUANTITIES[0], required_families=[])
        require(all(left == right for left, right in zip(training["rows"], q["rows"], strict=True)) and
                training["counts"] == q["counts"],
                "extended q membership/source/order differs from immutable direct membership")
        layout, data, centers, edges, initial = component_setup(
            prepared, q, config, inputs["config"], protocol, None)
        require(data is not None and initial is not None and
                layout == {key: value for key, value in component["layout"].items() if key != "coefficients"} and
                data["scalar"].shape == (training["counts"]["included_count"], 65) and
                not np.any(initial[1:]),
                "q/direct numerical layout, actor counts or initialization differs")
        positives = sum(component_target(attempt, QUANTITIES[0]) is True
                        for attempt in prepared["attempts"] if attempt["status"] == "eligible")
        require(int(data["target"].sum()) == positives and
                int(data["goal"].sum()) == training_audit["included"]["goals"] and
                agrees(float(initial[0]), math.log(positives / (len(data["target"]) - positives))),
                "q target response, preserved source goals or empirical intercept mismatch")
        checks[window] = dict(
            selection_source_order_labels=True, native_numerical_contract=True,
            q_direct_layout_actor_counts=True, training=training_audit,
            assessment=assessment_audit, design_sha256=hashlib.sha256(json.dumps(
                layout["design"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
            scalar_columns=65)
        del prepared, layout, data, centers, edges, initial
        prepared = prepare_core(linked_path(entry["assessment_selection"]))
        evaluated = read_json(linked_path(entry["evaluation"]))
        require(isinstance(evaluated, dict) and set(evaluated) == {
            "artifact_kind", "schema_version", "purpose", "protocol", "selection", "preparation_identity",
            "training_cohort", "assessment_cohort", "component", "evaluation", "attempts", "arm",
            "scientific_assessment",
        } and evaluated["schema_version"] == 3 and
            evaluated["artifact_kind"] == "chance_component_evaluation_completion" and
            evaluated["purpose"] == purpose and evaluated["protocol"] == source["protocol"] and
            evaluated["selection"] == entry["assessment_selection"] and
            evaluated["training_cohort"] == entry["training_cohort"] and
            evaluated["assessment_cohort"] == entry["assessment_cohort"] and
            evaluated["component"] == fitted["component"] and evaluated["arm"] == "short" and
            evaluated["preparation_identity"] == PREPARATION_IDENTITY and
            evaluated["scientific_assessment"] == "not_performed",
            "original direct evaluation completion binding mismatch")
        evaluation = validate_evaluation(
            evaluated["evaluation"], fitted["component"], entry["assessment_selection"],
            source["protocol"], DIRECT, purpose, component=component,
            cohort_reference=entry["assessment_cohort"], arm="short", prepared=prepared)
        require(evaluated["evaluation"] == original["evaluation_document"] and
                evaluated["attempts"] == evaluation["attempts"] and
                evaluation["implementation"] == source["implementation"] and
                evaluation["assessment_cohort_audit"] == assessment_audit and
                evaluation["metrics"] == original["metrics"],
                "original direct stream/evaluation/provenance changed")
        maximum, count = 0.0, 0
        for saved, reproduced in zip_longest(rows(linked_path(evaluation["attempts"])),
                predict_component_rows(component, prepared, assessment,
                                       component_identity=fitted["component"], arm="short")):
            require(saved is not None and reproduced is not None and set(saved) == set(reproduced),
                    "reused prediction stream shape/length changed")
            for field in saved:
                if field in ("log_p", "log_not_p", "probability") and saved[field] is not None:
                    require(agrees(saved[field], reproduced[field]),
                            "extended native prediction differs from immutable direct control")
                    maximum = max(maximum, abs(saved[field] - reproduced[field]))
                else:
                    require(saved[field] == reproduced[field],
                            "extended direct prediction keys/dispositions/support/descriptors changed")
            count += 1
        prediction = dict(
            schema_version=1, purpose=purpose, component=fitted["component"],
            selection=entry["assessment_selection"], cohort=entry["assessment_cohort"],
            evaluation=evaluated["evaluation"], attempts=evaluation["attempts"],
            source_protocol=source["protocol"], source_implementation=source["implementation"],
            implementation=current, recognized_count=count, max_abs_numerical_difference=maximum,
            exact_keys_dispositions_support=True, aggregate_reconciliation=True, agrees=True)
        verifications[window] = dict(objective=objective, predictions=prediction)
        del prepared
    output = output_path(args.out, roots)
    output.mkdir()
    verification_refs = {}
    for window in WINDOWS:
        verification_refs[window] = {}
        for kind, document in verifications[window].items():
            path = output / f"verification-{window}-{kind}.json"
            write_json(path, document)
            verification_refs[window][kind] = identity(path)
    document = dict(
        schema_version=1, artifact_kind="chance_decomposition_control_reuse", purpose=purpose,
        source_result=inputs["source_result"], config=inputs["config"], windows=inputs["windows"],
        protocol=protocol, implementation=current, source_protocol=source["protocol"],
        source_implementation=source["implementation"], checks=checks,
        verification=verification_refs, resources=resources(started))
    write_json(output / "reuse.json", document)
    write_json(output / "completion.json", dict(
        schema_version=1, artifact_kind="chance_decomposition_reuse_completion", purpose=purpose,
        protocol=protocol, implementation=current, reuse=identity(output / "reuse.json"),
        scientific_assessment="not_performed"))
    print(f"direct control reuse complete: {output}; no fit performed")
    return 0


def read_reuse(reference, *, purpose, protocol, config=None):
    completed = completion(reference, "reuse", {"protocol", "reuse"}, purpose=purpose, protocol=protocol)
    document = read_json(linked_path(completed["reuse"]))
    require(isinstance(document, dict) and set(document) == {
        "schema_version", "artifact_kind", "purpose", "source_result", "config", "windows",
        "protocol", "implementation", "source_protocol", "source_implementation", "checks",
        "verification", "resources",
    } and type(document["schema_version"]) is int and document["schema_version"] == 1 and
        document["artifact_kind"] == "chance_decomposition_control_reuse" and
        document["purpose"] == purpose and document["protocol"] == protocol and
        document["implementation"] == completed["implementation"] == implementation() and
        (config is None or config == document["config"]) and
        set(document["checks"]) == set(document["verification"]) == set(WINDOWS),
        "invalid completed direct reuse receipt or frozen implementation")
    source = validate_reuse_inputs({key: document[key] for key in
                                   ("schema_version", "purpose", "source_result", "config", "windows")})
    require(document["source_protocol"] == source["protocol"] and
            document["source_implementation"] == source["implementation"],
            "direct reuse restamped original control provenance")
    for window in WINDOWS:
        require(set(document["verification"][window]) == {"objective", "predictions"},
                "direct reuse requires objective and prediction verification for both windows")
        objective = read_json(linked_path(document["verification"][window]["objective"]))
        predicted = read_json(linked_path(document["verification"][window]["predictions"]))
        control = source["cells"][window]["short"]
        original_evaluation = read_json(linked_path(control["evaluation_document"]))
        require(objective["purpose"] == purpose and objective["component"] == control["component"] and
                objective["cohort"] == document["windows"][window]["training_cohort"] and
                objective["selection"] == document["windows"][window]["training_selection"] and
                objective["config"] == document["config"] and
                objective["protocol"] == source["protocol"] and
                objective["implementation"] == document["implementation"] and
                objective["agrees"] is True and agrees(objective["saved_objective"], objective["replayed_objective"]) and
                objective["saved_objective"] == control["diagnostics"]["objective"] and
                all(type(objective[field]) in (int, float) and math.isfinite(objective[field])
                    for field in ("saved_objective", "replayed_objective", "difference", "gradient_max_abs")) and
                objective["gradient_max_abs"] >= 0 and
                agrees(objective["difference"], objective["replayed_objective"] - objective["saved_objective"]) and
                predicted["purpose"] == purpose and predicted["component"] == control["component"] and
                predicted["selection"] == document["windows"][window]["assessment_selection"] and
                predicted["cohort"] == document["windows"][window]["assessment_cohort"] and
                predicted["evaluation"] == control["evaluation_document"] and
                predicted["attempts"] == original_evaluation["attempts"] and
                predicted["source_protocol"] == source["protocol"] and
                predicted["source_implementation"] == source["implementation"] and
                predicted["implementation"] == document["implementation"] and predicted["agrees"] is True and
                type(predicted["recognized_count"]) is int and
                predicted["recognized_count"] == document["checks"][window]["assessment"]["recognized_count"] and
                type(predicted["max_abs_numerical_difference"]) in (int, float) and
                math.isfinite(predicted["max_abs_numerical_difference"]) and
                predicted["max_abs_numerical_difference"] >= 0 and
                predicted["exact_keys_dispositions_support"] is True and
                predicted["aggregate_reconciliation"] is True,
                "direct reuse verification binding or agreement mismatch")
    return document


def fit_command(args):
    started = time.monotonic()
    selection = Path(args.selection).resolve(strict=True)
    cohort_path = Path(args.cohort).resolve(strict=True)
    config_path = Path(args.config).resolve(strict=True)
    protocol_path = Path(args.protocol).resolve(strict=True)
    reuse_path = Path(args.reuse).resolve(strict=True)
    validate_recipe(read_json(config_path))
    selected = read_json(selection)
    reuse = read_reuse(identity(reuse_path), purpose=selected["purpose"],
                       protocol=identity(protocol_path), config=identity(config_path))
    require(identity(selection) == reuse["windows"][args.window]["training_selection"],
            "new stage fit changed the reused direct training selection")
    output_path(args.out, artifact_roots(reuse) + [str(reuse_path.parent)])
    prepared = prepare_core(selection)
    cohort, audit, target, _ = read_bundle(identity(cohort_path), prepared, args.quantity)
    q = component_cohort(prepared, quantity=QUANTITIES[0], required_families=[])
    validate_population(q, outcome_audit(prepared, q), window=args.window, partition="short")
    return fit_prepared(args, prepared, started=started)


def compose_logs(q, g):
    """evaluate the same 1-q*g identity using its numerically resolved tail.

    log1p(-exp(log_p)) preserves the complement sign for p <= 1/2.
    the stage-complement sum retains the failure tail when p approaches one
    and native log_p can round to -0.0. neither branch clips probabilities.
    """
    binary_record(0, q["log_p"], q["log_not_p"])
    binary_record(0, g["log_p"], g["log_not_p"])
    log_p = q["log_p"] + g["log_p"]
    log_not_p = (math.log1p(-math.exp(log_p)) if log_p <= -math.log(2) else
                 float(np.logaddexp(q["log_not_p"], q["log_p"] + g["log_not_p"])))
    result = dict(log_p=log_p, log_not_p=log_not_p)
    binary_record(0, result["log_p"], result["log_not_p"])
    return result


def composed_rows(prepared, cohorts, components):
    contexts = {quantity: component_prediction_context(
        component, feature_games=prepared["feature_games"],
        feature_player_games=prepared["feature_player_games"])
        for quantity, component in components.items()}
    sources = source_identities(prepared)
    for attempt, qmember, gmember in zip(prepared["attempts"], cohorts[QUANTITIES[0]]["rows"],
                                        cohorts[QUANTITIES[1]]["rows"], strict=True):
        gid = attempt["game_id"]
        included = qmember["study_inclusion"] == "included"
        row = dict(
            schema_version=1, game_id=gid, source_index=attempt["source_index"],
            event_id=attempt["event_id"], game_date=prepared["game_dates"][gid],
            season=attempt["season"], source_identity=sources[gid],
            **{field: qmember[field] for field in
               ("source_status", "source_reasons", "study_inclusion", "study_reasons")},
            status=("predicted" if included else "not_applicable"
                    if attempt["status"] == "eligible" else attempt["status"]),
            blocked=attempt["blocked"], goal=attempt["goal"], on_net=recorded_on_net(attempt),
            diagnostic_groups=diagnostic_groups(attempt, prepared["game_dates"][gid], {}),
            stages={}, composed_goal=None)
        for quantity, member in ((QUANTITIES[0], qmember), (QUANTITIES[1], gmember)):
            stage = dict(metric_applicable=False, observed=None, log_p=None, log_not_p=None,
                         season_basis=None, state_season=None, actor_evidence=None)
            if included:
                observed = component_target(attempt, quantity)
                stage.update(predict_component(components[quantity], attempt, contexts[quantity]),
                             metric_applicable=member["study_inclusion"] == "included",
                             observed=int(observed) if observed is not None else None)
            row["stages"][quantity] = stage
        if included:
            row["composed_goal"] = compose_logs(*(row["stages"][quantity] for quantity in QUANTITIES))
        yield row


def metric_rows(stream, metric):
    """an explicit binary scoring view; serialized source/composition rows stay intact."""
    for row in stream:
        if metric == "composed_goal":
            applicable = row["status"] == "predicted"
            predicted = row["composed_goal"]
            observed = int(row["goal"]) if applicable else None
            groups = row["diagnostic_groups"]
        else:
            quantity = QUANTITIES[0] if metric == "on_net" else QUANTITIES[1]
            stage = row["stages"][quantity]
            applicable = stage["metric_applicable"]
            predicted = stage if applicable else None
            observed = stage["observed"] if applicable else None
            groups = dict(row["diagnostic_groups"], **{
                f"actor_support:{actor}": stage["actor_evidence"][actor]["basis"]
                if stage["actor_evidence"] is not None else None for actor in ("shooter", "goalie")})
        status = ("predicted" if applicable else "not_applicable"
                  if row["source_status"] == "eligible" else row["source_status"])
        yield dict(
            game_id=row["game_id"], source_index=row["source_index"], status=status,
            reasons=row["source_reasons"], source_status=row["source_status"],
            source_reasons=row["source_reasons"],
            study_inclusion=("included" if applicable else "not_applicable"
                             if row["source_status"] == "eligible" else "source_excluded"),
            study_reasons=[], applicable=(row["on_net"] is True if metric == "goal_given_on_net"
                                         else not row["blocked"]), observed=observed,
            log_p=None if predicted is None else predicted["log_p"],
            log_not_p=None if predicted is None else predicted["log_not_p"],
            probability=None if predicted is None else math.exp(predicted["log_p"]),
            diagnostic_groups=groups)


def summaries(stream_path, game_dates):
    result = {}
    for metric in METRICS:
        kwargs = dict(outcome="on_net" if metric == "on_net" else "goal")
        if metric == "composed_goal":
            kwargs["group_categories"] = SOURCE_GROUPS
        result[metric] = summarize_component(metric_rows(rows(stream_path), metric), game_dates, **kwargs)
    return result


def read_stage_component(reference, quantity, protocol, purpose):
    component = validate_component(read_json(linked_path(reference)))
    require(component["quantity"] == quantity and component["purpose"] == purpose and
            component["protocol_identity"] == protocol and component["extraction"] is None and
            component["diagnostics"]["converged"] is True and
            component["training_cohort"]["definition"] == DEFINITION and
            component["training_cohort"]["excluded_count"] == 0 and
            component["implementation"] == implementation(),
            "assessment requires the converged native stage under the frozen protocol/code")
    validate_recipe(component["config"])
    if purpose == "research":
        require(component["config_identity"] == CONFIG_REFERENCE,
                "research stage changed immutable numerical config")
        clean_implementation(component["implementation"])
    return component


def evaluate_command(args):
    started = time.monotonic()
    selection = Path(args.selection).resolve(strict=True)
    protocol_path = Path(args.protocol).resolve(strict=True)
    protocol = identity(protocol_path)
    prepared = prepare_core(selection)
    validate_prepared_selection(prepared, selection)
    component_refs = {
        QUANTITIES[0]: identity(Path(args.on_net_component).resolve(strict=True)),
        QUANTITIES[1]: identity(Path(args.conversion_component).resolve(strict=True)),
    }
    cohort_refs = {
        QUANTITIES[0]: identity(Path(args.cohort_on_net).resolve(strict=True)),
        QUANTITIES[1]: identity(Path(args.cohort_conversion).resolve(strict=True)),
    }
    components, cohorts, audits, target_refs = {}, {}, {}, {}
    roots = prepared["input_roots"] + [str(selection.parent), str(protocol_path.parent)] + \
        artifact_roots(dict(components=component_refs, cohorts=cohort_refs))
    for quantity in QUANTITIES:
        component = read_stage_component(component_refs[quantity], quantity, protocol, prepared["purpose"])
        cohort, audit, target, target_reference = read_bundle(cohort_refs[quantity], prepared, quantity)
        training = validate_cohort_document(read_json(linked_path(component["training_cohort"]["membership_identity"])))
        require(training["quantity"] == quantity and training["game_dates"] == component["training_game_dates"] and
                selection_reference(training) == next({key: value[key] for key in ("path", "sha256")}
                    for value in component["inputs"] if value["kind"] == "selection") and
                not set(training["game_dates"]) & set(cohort["game_dates"]) and
                min(cohort["game_dates"].values()) > max(training["game_dates"].values()),
                "stage assessment dates must follow disjoint bound training")
        if prepared["purpose"] == "research":
            require(selection_reference(training)["path"] ==
                    str(SELECTION_ROOT / f"{args.window}-short-training.json") and
                    identity(selection)["path"] == str(SELECTION_ROOT / f"{args.window}-assessment.json"),
                    "assessment stage/window uses the wrong fixed selection")
        components[quantity], cohorts[quantity], audits[quantity], target_refs[quantity] = \
            component, cohort, audit, target_reference
    require(components[QUANTITIES[0]]["config_identity"] == components[QUANTITIES[1]]["config_identity"] and
            components[QUANTITIES[0]]["training_game_dates"] == components[QUANTITIES[1]]["training_game_dates"],
            "two stage models changed config or training population")
    verify_pair(prepared, cohorts, audits, window=args.window, partition="assessment")
    output = output_path(args.out, roots)
    output.mkdir()
    with (output / "attempts.jsonl").open("x", encoding="utf-8") as destination:
        for row in composed_rows(prepared, cohorts, components):
            destination.write(json.dumps(row, allow_nan=False) + "\n")
    summary = summaries(output / "attempts.jsonl", prepared["game_dates"])
    require(summary["on_net"]["metrics"]["count"] == summary["composed_goal"]["metrics"]["count"] ==
            cohorts[QUANTITIES[0]]["counts"]["included_count"] and
            summary["goal_given_on_net"]["metrics"]["count"] == cohorts[QUANTITIES[1]]["counts"]["included_count"] and
            summary["on_net"]["metrics"]["observed_positive_count"] ==
            summary["goal_given_on_net"]["metrics"]["count"] and
            summary["goal_given_on_net"]["metrics"]["observed_positive_count"] ==
            summary["composed_goal"]["metrics"]["observed_positive_count"],
            "composed stage U/O/U denominators or observed counts do not reconcile")
    document = dict(
        schema_version=1, artifact_kind="chance_decomposition_assessment", purpose=prepared["purpose"],
        protocol=protocol, implementation=implementation(), selection=identity(selection),
        **{field: prepared[field] for field in ("inputs", "preparation_identity", "game_dates", "coverage")},
        cohorts=cohort_refs, components=component_refs, target_audits=target_refs,
        attempts=identity(output / "attempts.jsonl"),
        **{field: {metric: summary[metric][field] for metric in METRICS}
           for field in ("metrics", "groups", "per_game")},
        resources=resources(started), scientific_assessment="not_performed")
    write_json(output / "assessment.json", document)
    write_json(output / "completion.json", dict(
        schema_version=1, artifact_kind="chance_decomposition_assessment_completion", purpose=prepared["purpose"],
        protocol=protocol, implementation=implementation(), selection=identity(selection),
        components=component_refs, cohorts=cohort_refs, target_audits=target_refs,
        assessment=identity(output / "assessment.json"), attempts=document["attempts"],
        scientific_assessment="not_performed"))
    print(f"decomposition assessment complete: {output}; scientific assessment not performed")
    return 0


def validate_assessment(reference, *, purpose, protocol, components, component_refs, selection):
    completed = completion(reference, "assessment", {
        "protocol", "selection", "components", "cohorts", "target_audits", "assessment", "attempts",
    }, purpose=purpose, protocol=protocol)
    document = read_json(linked_path(completed["assessment"]))
    require(isinstance(document, dict) and set(document) == ASSESSMENT_FIELDS and
            type(document["schema_version"]) is int and document["schema_version"] == 1 and
            document["artifact_kind"] == "chance_decomposition_assessment" and
            document["purpose"] == purpose and document["protocol"] == protocol and
            document["implementation"] == completed["implementation"] == implementation() and
            document["selection"] == completed["selection"] == selection and
            document["components"] == completed["components"] == component_refs and
            document["cohorts"] == completed["cohorts"] and
            document["target_audits"] == completed["target_audits"] and
            document["attempts"] == completed["attempts"] and
            document["scientific_assessment"] == "not_performed" and
            all(isinstance(document[field], dict) and set(document[field]) == set(QUANTITIES)
                for field in ("components", "cohorts", "target_audits")) and
            all(isinstance(document[field], dict) and set(document[field]) == set(METRICS)
                for field in ("metrics", "groups", "per_game")),
            "composed assessment schema/completion/source/stage binding mismatch")
    prepared = prepare_core(linked_path(selection))
    validate_prepared_selection(prepared, linked_path(selection))
    require(all(document[field] == prepared[field] for field in
                ("purpose", "inputs", "preparation_identity", "game_dates", "coverage")),
            "composed assessment changed original preparation/coverage")
    cohorts, audits, targets = {}, {}, {}
    for quantity in QUANTITIES:
        cohort, audit, target, target_reference = read_bundle(document["cohorts"][quantity], prepared, quantity)
        require(document["target_audits"][quantity] == target_reference,
                "assessment target audit is not the actual cohort sibling")
        cohorts[quantity], audits[quantity], targets[quantity] = cohort, audit, target
    verify_pair(prepared, cohorts, audits)
    for saved, expected in zip_longest(rows(linked_path(document["attempts"])),
                                       composed_rows(prepared, cohorts, components)):
        require(saved is not None and expected is not None and set(saved) == ROW_FIELDS and
                type(saved["schema_version"]) is int and saved["schema_version"] == 1 and
                isinstance(saved["stages"], dict) and set(saved["stages"]) == set(QUANTITIES),
                "composed stream shape/order/length mismatch")
        for field in ROW_FIELDS - {"stages", "composed_goal"}:
            require(saved[field] == expected[field],
                    f"{expected['game_id']}:{expected['source_index']}: composed source labels/descriptors/dispositions changed")
        for quantity in QUANTITIES:
            stage, actual = saved["stages"][quantity], expected["stages"][quantity]
            require(isinstance(stage, dict) and set(stage) == STAGE_FIELDS and
                    type(stage["metric_applicable"]) is bool and
                    (stage["observed"] is None or type(stage["observed"]) is int),
                    "composed stage schema/label applicability mismatch")
            for field in STAGE_FIELDS:
                if field in ("log_p", "log_not_p") and actual[field] is not None:
                    require(type(stage[field]) in (int, float) and math.isfinite(stage[field]) and
                            agrees(stage[field], actual[field]),
                            "saved stage prediction differs from native source/design/coefficients")
                else:
                    require(stage[field] == actual[field],
                            "saved stage target/basis/actor evidence differs from original source/component")
        if expected["composed_goal"] is None:
            require(saved["composed_goal"] is None, "prediction outside U must be null")
        else:
            require(isinstance(saved["composed_goal"], dict) and
                    set(saved["composed_goal"]) == {"log_p", "log_not_p"}, "invalid composed goal log fields")
            composed = compose_logs(*(saved["stages"][quantity] for quantity in QUANTITIES))
            require(all(type(saved["composed_goal"][field]) in (int, float) and
                        math.isfinite(saved["composed_goal"][field]) and
                        agrees(saved["composed_goal"][field], expected["composed_goal"][field]) and
                        agrees(saved["composed_goal"][field], composed[field])
                        for field in composed), "saved product arithmetic or native stage predictions changed")
    summary = summaries(linked_path(document["attempts"]), prepared["game_dates"])
    for field in ("metrics", "groups", "per_game"):
        require(document[field] == {metric: summary[metric][field] for metric in METRICS},
                "composed saved metrics/groups/game sums differ from the actual stream")
    for metric, quantity in (("on_net", QUANTITIES[0]), ("goal_given_on_net", QUANTITIES[1])):
        require(summary[metric]["metrics"]["count"] == targets[quantity]["counts"]["included_count"] and
                summary[metric]["metrics"]["observed_positive_count"] == targets[quantity]["counts"]["target_positive"],
                "stage scoring denominator/positives differ from source target audit")
    require(summary["composed_goal"]["metrics"]["count"] == targets[QUANTITIES[0]]["counts"]["unblocked"] and
            summary["composed_goal"]["metrics"]["observed_positive_count"] == targets[QUANTITIES[0]]["counts"]["goals"] and
            not any(key.startswith("actor_support:") for key in summary["composed_goal"]["groups"]),
            "composed goal scoring or own-arm group scope changed")
    return document, summary, targets, prepared["input_roots"]


def paired_records(direct_path, composed_path):
    """pair full original-order U evidence; direct owns support and probability bins."""
    for before, composed in zip_longest(rows(direct_path), rows(composed_path)):
        require(before is not None and composed is not None and
                all(before[field] == composed[field] for field in (
                    "game_id", "source_index", "event_id", "game_date", "season", "source_identity",
                    "source_status", "source_reasons", "study_inclusion", "study_reasons", "status",
                    "blocked", "goal")) and
                {key: value for key, value in before["diagnostic_groups"].items()
                 if not key.startswith("actor_support:")} == composed["diagnostic_groups"],
                "direct/composed full stream source keys/order/labels/dispositions differ")
        after = next(metric_rows([composed], "composed_goal"))
        yield before, after


def validate_report_inputs(document):
    require(isinstance(document, dict) and set(document) ==
            {"schema_version", "purpose", "reuse", "config", "windows", "resampling"} and
            type(document["schema_version"]) is int and document["schema_version"] == 1 and
            document["purpose"] in ("research", "fixture_exercise") and
            document["resampling"] == RESAMPLING and
            type(document["resampling"]["draws"]) is int and
            type(document["resampling"]["seed"]) is int and
            all(type(value) is int for value in document["resampling"]["calendar_days"]) and
            isinstance(document["windows"], dict) and set(document["windows"]) == set(WINDOWS),
            "schema-1 fixed decomposition report inputs required")
    records = [(document["reuse"], {"completion"})]
    for window in WINDOWS:
        cells = document["windows"][window]
        require(isinstance(cells, dict) and set(cells) == {*QUANTITIES, "assessment"},
                "report requires both stages and the assessment in both fixed windows")
        records.extend((cells[quantity], {"cohort", "target_audit", "fit"}) for quantity in QUANTITIES)
        records.append((cells["assessment"], {"completion"}))
    stopped = False
    for record, artifacts in records:
        require(isinstance(record, dict) and set(record) ==
                {"status", "failure", "stop_reason"} | artifacts and
                record["status"] in ("complete", "failed", "not_run"),
                "invalid decomposition execution cell schema/status")
        for field in artifacts | {"failure"}:
            value = record[field]
            require(value is None or isinstance(value, dict) and set(value) == {"path", "sha256"},
                    "execution artifacts require exact located path/sha256 identities")
        require(not stopped or record["status"] == "not_run",
                "source/numerical/i/o failure must stop later cells in canonical order")
        if record["status"] == "complete":
            require(all(record[field] is not None for field in artifacts) and
                    record["failure"] is None and record["stop_reason"] is None,
                    "completed execution cell requires all promised artifacts and no failure")
        else:
            require(isinstance(record["stop_reason"], str) and bool(record["stop_reason"].strip()) and
                    (record["status"] != "failed" or record["failure"] is not None) and
                    record.get("completion") is None and record.get("fit") is None,
                    "incomplete execution requires located failure/reason and no successful completion")
            if record["status"] == "not_run":
                require(record["failure"] is None, "not-run cell cannot claim an attempted failure")
            stopped = True
    artifact_roots(document)
    validate_recipe(read_json(linked_path(document["config"])))
    if document["purpose"] == "research":
        require(document["config"] == CONFIG_REFERENCE, "research report changed the immutable recipe")
    return document


def decision(comparisons, *, purpose):
    if purpose == "fixture_exercise":
        return "not_assessed", "fixture_only", None
    require(purpose == "research", "unsupported decomposition report purpose")
    if any(comparisons.get(window) is None for window in WINDOWS):
        return "incomplete", "no_supported_representation", None
    primary = [comparisons[window]["delta"]["log_loss"] for window in WINDOWS]
    points = [value["games"]["estimate"] for value in primary]
    if any(value is None for value in points):
        return "incomplete", "no_supported_representation", None
    require(all(type(value) in (int, float) and math.isfinite(value) for value in points),
            "primary estimates must be finite")
    direction = ("decomposed_direction" if all(value < -DEADBAND for value in points) else
                 "direct_direction" if all(value > DEADBAND for value in points) else
                 "within_arithmetic_deadband" if all(-DEADBAND <= value <= DEADBAND for value in points) else
                 "mixed_direction")
    defined = all(value[unit]["interval"] is not None
                  for value in primary for unit in ("games", "calendar_7_day", "calendar_14_day"))
    nomination = None
    if (defined and direction == "decomposed_direction" and
            all(value["games"]["interval"][1] < -DEADBAND for value in primary) and
            not any(value[unit]["interval"][0] > DEADBAND
                    for value in primary for unit in ("calendar_7_day", "calendar_14_day"))):
        nomination = "decomposed"
    if (defined and direction == "direct_direction" and
            all(value["games"]["interval"][0] > DEADBAND for value in primary) and
            not any(value[unit]["interval"][1] < -DEADBAND
                    for value in primary for unit in ("calendar_7_day", "calendar_14_day"))):
        nomination = "direct"
    return direction, "supported_representation" if nomination else "no_supported_representation", nomination


def report_command(args):
    started = time.monotonic()
    inputs_path = Path(args.inputs).resolve(strict=True)
    protocol_path = Path(args.protocol).resolve(strict=True)
    protocol = identity(protocol_path)
    inputs = validate_report_inputs(read_json(inputs_path))
    purpose = inputs["purpose"]
    roots = [str(inputs_path.parent), str(protocol_path.parent)] + artifact_roots(inputs)
    reuse = None
    if inputs["reuse"]["status"] == "complete":
        reuse = read_reuse(inputs["reuse"]["completion"], purpose=purpose, protocol=protocol,
                           config=inputs["config"])
        roots.extend(artifact_roots(reuse))
    cells, coverage, comparisons, stage_diagnostics, receipts = {}, {}, {}, {}, {}
    frozen = None
    for window in WINDOWS:
        cells[window], coverage[window], stage_diagnostics[window] = {}, {}, None
        components, component_refs = {}, {}
        training_selection = None
        for quantity in QUANTITIES:
            cell = inputs["windows"][window][quantity]
            record = dict(deepcopy(cell), component=None, design=None, diagnostics=None,
                          verification=None, fit_resources=None, training_actor_counts=None,
                          target_counts=None)
            cohort, audit = None, None
            if cell["cohort"] is not None:
                declared = validate_cohort_document(read_json(linked_path(cell["cohort"])))
                selected = selection_reference(declared)
                require(training_selection is None or training_selection == selected,
                        "stage training selections differ within a fixed window")
                training_selection = selected
                require(reuse is None or selected == reuse["windows"][window]["training_selection"],
                        "reported stage training differs from reused direct selection")
                prepared = prepare_core(linked_path(selected))
                cohort, audit, target, target_reference = read_bundle(cell["cohort"], prepared, quantity)
                require(cell["target_audit"] == target_reference,
                        "reported training target audit must be the actual sibling")
                q = component_cohort(prepared, quantity=QUANTITIES[0], required_families=[])
                validate_population(q, outcome_audit(prepared, q), window=window, partition="short")
                record["target_counts"] = target["counts"]
                if quantity == QUANTITIES[0]:
                    coverage[window]["training"] = target
                roots.extend(prepared["input_roots"])
                del prepared, q
            else:
                require(cell["target_audit"] is None, "target audit cannot claim an absent cohort")
            if cell["status"] == "complete":
                require(reuse is not None and cohort is not None,
                        "new fitted stage requires successful bound direct reuse and target cohort")
                completed, component, fit = read_fit(
                    cell["fit"], cell["cohort"], cohort, audit, config=inputs["config"],
                    protocol=protocol, quantity=quantity, purpose=purpose,
                    expected_implementation=reuse["implementation"])
                require(frozen is None or frozen == component["implementation"],
                        "all stage fits require one frozen implementation")
                frozen = component["implementation"]
                verification, source_roots = verify_component(
                    component, completed["component"], cohort, cell["cohort"], protocol)
                roots.extend(source_roots)
                design = component["layout"]["design"]
                design_hash = hashlib.sha256(json.dumps(
                    design, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
                verification.update(
                    artifact_kind="chance_decomposition_objective_verification", quantity=quantity,
                    fit=cell["fit"], target_audit=cell["target_audit"], design_sha256=design_hash)
                receipts[window, quantity] = verification
                record.update(
                    component=completed["component"],
                    design=dict(sha256=design_hash,
                        stage=design["stage"], families=design["families"],
                        circumstance_columns=design["circumstance_columns"], slices=design["slices"],
                        coefficient_count=component["layout"]["size"]),
                    diagnostics=component["diagnostics"], fit_resources=fit["resources"],
                    training_actor_counts={field: component["layout"][field] for field in
                                           ("seasons", "shooter_counts", "goalie_counts")})
                components[quantity], component_refs[quantity] = component, completed["component"]
            elif cell["status"] == "failed":
                linked_path(cell["failure"])
            cells[window][quantity] = record
        assessment_cell = inputs["windows"][window]["assessment"]
        cells[window]["assessment"] = dict(deepcopy(assessment_cell), assessment=None, attempts=None,
                                           resources=None, metrics=None)
        comparison = None
        if assessment_cell["status"] == "complete":
            require(reuse is not None and set(components) == set(QUANTITIES),
                    "complete composed assessment requires both complete new native fits")
            assessment, summary, targets, source_roots = validate_assessment(
                assessment_cell["completion"], purpose=purpose, protocol=protocol,
                components=components, component_refs=component_refs,
                selection=reuse["windows"][window]["assessment_selection"])
            roots.extend(source_roots)
            coverage[window]["assessment"] = targets[QUANTITIES[0]]
            completed = read_json(linked_path(assessment_cell["completion"]))
            cells[window]["assessment"].update(
                assessment=completed["assessment"], attempts=assessment["attempts"],
                resources=assessment["resources"], metrics=assessment["metrics"])
            old = reuse["windows"][window]
            direct_completed = read_json(linked_path(old["evaluation"]))
            direct_fit = read_json(linked_path(old["fit"]))
            direct_component = validate_component(read_json(linked_path(direct_fit["component"])))
            direct = validate_evaluation(
                direct_completed["evaluation"], direct_fit["component"], old["assessment_selection"],
                reuse["source_protocol"], DIRECT, purpose, component=direct_component,
                cohort_reference=old["assessment_cohort"], arm="short")
            require(direct["implementation"] == reuse["source_implementation"] and
                    direct["game_dates"] == assessment["game_dates"] and
                    direct["inputs"] == assessment["inputs"] and
                    direct["coverage"] == assessment["coverage"],
                    "paired direct/composed source provenance/coverage changed")
            changed = dict(game_dates=assessment["game_dates"], **summary["composed_goal"])
            comparison = compare_paired_records(direct, changed,
                paired_records(linked_path(direct["attempts"]), linked_path(assessment["attempts"])))
            comparison["paired_groups"] = {category: comparison["paired_groups"][category]
                                            for category in REPORT_GROUPS}
            before, after = comparison["baseline_metrics"], comparison["changed_metrics"]
            point = comparison["delta"]["log_loss"]["games"]["estimate"]
            comparison.update(
                baseline="direct", changed="decomposed", role_mapping=dict(baseline="direct", changed="decomposed"),
                group_definition="direct owns paired actor-support groups and probability bins; stage-own support and composed-own bins remain separate",
                own_arm_calibration=dict(direct=before["calibration"], decomposed=after["calibration"]),
                relative_log_loss_change=point / before["log_loss"] if before["log_loss"] else None,
                change_absolute_pooled_residual_pp=(abs(after["predicted_minus_observed_pp"]) -
                    abs(before["predicted_minus_observed_pp"])) if before["count"] else None,
                direct_evaluation=direct_completed["evaluation"], composed_assessment=completed["assessment"])
            stage_diagnostics[window] = {
                metric: dict(population="U" if metric == "on_net" else "O", descriptive_only=True,
                             metrics=assessment["metrics"][metric], groups=assessment["groups"][metric],
                             per_game=assessment["per_game"][metric],
                             component=component_refs[QUANTITIES[0] if metric == "on_net" else QUANTITIES[1]])
                for metric in ("on_net", "goal_given_on_net")}
            del components, direct_component
        elif assessment_cell["status"] == "failed":
            linked_path(assessment_cell["failure"])
        comparisons[window] = comparison
    if frozen is not None:
        require(frozen == implementation(), "report/objective replay changed frozen fitting code")
    direction, recommendation, nomination = decision(comparisons, purpose=purpose)
    executed = inputs["reuse"]["status"] == "complete" and all(
        inputs["windows"][window][key]["status"] == "complete"
        for window in WINDOWS for key in (*QUANTITIES, "assessment"))
    output = output_path(args.out, roots)
    output.mkdir()
    for (window, quantity), receipt in receipts.items():
        path = output / f"verification-{window}-{quantity}.json"
        write_json(path, receipt)
        cells[window][quantity]["verification"] = identity(path)
    reuse_record = deepcopy(inputs["reuse"])
    if reuse is not None:
        reuse_record.update(
            receipt=read_json(linked_path(inputs["reuse"]["completion"]))["reuse"],
            source_result=reuse["source_result"], source_protocol=reuse["source_protocol"],
            source_implementation=reuse["source_implementation"], controls=reuse["windows"],
            verification=reuse["verification"], resources=reuse["resources"])
    document = dict(
        schema_version=1, artifact_kind="chance_decomposition_result", purpose=purpose,
        inputs=identity(inputs_path), protocol=protocol, implementation=implementation(), reuse=reuse_record,
        horizon="short", population="recorded goal probabilities on all source-eligible unblocked 5v5 assessment attempts",
        diagnostic_scope=dict(sequence_index="not_prepared", paired_groups=list(REPORT_GROUPS),
                              stage_populations=dict(on_net="U", goal_given_on_net="O", composed_goal="U")),
        direction=direction, recommendation=recommendation, nominated_representation=nomination,
        scientific_assessment="not_admitted" if purpose == "research" else "not_performed",
        execution_status="complete" if executed and direction != "incomplete" else "incomplete",
        coverage=coverage, cells=cells, comparisons=comparisons, stage_diagnostics=stage_diagnostics,
        resampling=RESAMPLING, arithmetic_deadband_nats_per_attempt=DEADBAND, limitations=LIMITATIONS,
        resources=dict(report=resources(started)), figures={})
    document["figures"] = save_figures(document, output)
    document["resources"]["report"].update(resources(started),
        figure_bytes=sum(linked_path(reference).stat().st_size for reference in document["figures"].values()))
    write_json(output / "result.json", document)
    write_json(output / "completion.json", dict(
        schema_version=1, artifact_kind="chance_decomposition_report_completion", purpose=purpose,
        protocol=protocol, implementation=implementation(), inputs=identity(inputs_path),
        result=identity(output / "result.json"), figures=document["figures"], scientific_assessment="not_performed"))
    print(f"decomposition report complete: {output}; {document['execution_status']}; {direction}; {recommendation}")
    return 0


def save_figures(document, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    destination = output / "figures"
    destination.mkdir()
    colors = dict(direct="#555555", decomposed="#176b87")
    figure, axes = plt.subplots(2, 2, figsize=(13, 8), sharex="col", sharey="col",
                                gridspec_kw=dict(width_ratios=[1, 1.5]))
    for row, window in enumerate(WINDOWS):
        loss, calibration = axes[row]
        loss.axvline(0, color="#333333", lw=.8)
        calibration.axhline(0, color="#333333", lw=.8)
        loss.set_title(window.replace("_", " "))
        loss.set_yticks([0, 1, 2], ["whole game", "7-day block", "14-day block"])
        loss.set_xlabel("decomposed − direct goal log loss\nnats / eligible unblocked attempt")
        loss.xaxis.set_major_locator(MaxNLocator(nbins=4))
        loss.ticklabel_format(axis="x", style="sci", scilimits=(-3, 3), useOffset=False, useMathText=True)
        calibration.set_xlim(0, 1)
        calibration.set_xlabel("direct probability bin; shared membership")
        calibration.set_ylabel("predicted − observed\npercentage points")
        comparison = document["comparisons"][window]
        if comparison is None:
            for axis in (loss, calibration):
                axis.text(.5, .5, "comparison incomplete", transform=axis.transAxes, ha="center", va="center")
            continue
        for index, unit in enumerate(("games", "calendar_7_day", "calendar_14_day")):
            value = comparison["delta"]["log_loss"][unit]
            if value["estimate"] is not None:
                loss.plot(value["estimate"], index, "o", color=colors["decomposed"], ms=5)
            if value["interval"] is not None:
                loss.hlines(index, *value["interval"], color=colors["decomposed"], lw=1.3)
            else:
                loss.annotate(f"interval undefined\n{value['undefined_draws']:,}/2,000 draws had no attempts",
                              (.98, index), xycoords=("axes fraction", "data"),
                              xytext=(0, 8 if index < 2 else -14), textcoords="offset points",
                              ha="right", va="bottom" if index < 2 else "top", fontsize=7,
                              bbox=dict(facecolor="white", edgecolor="none", pad=.4))
        bins = comparison["paired_calibration"]
        xs = [(bucket["lower"] + bucket["upper"]) / 2 for bucket in bins]
        for arm, key in (("direct", "baseline"), ("decomposed", "changed")):
            residuals = [bucket[key]["predicted_minus_observed_pp"] if bucket[key]["count"] else np.nan
                         for bucket in bins]
            calibration.plot(xs, residuals, "o-", color=colors[arm], ms=3, lw=.8, label=arm)
        for x, bucket in zip(xs, bins, strict=True):
            if bucket["baseline"]["count"]:
                edge, below = x >= .85, .85 <= x < .95
                calibration.annotate(f"n={bucket['baseline']['count']:,}",
                    (x, bucket["baseline"]["predicted_minus_observed_pp"]),
                    xytext=(-3 if edge else 3, -8 if below else 8), textcoords="offset points",
                    ha="right" if edge else "left", va="top" if below else "bottom",
                    fontsize=6, rotation=60,
                    arrowprops=dict(arrowstyle="-", lw=.3) if edge else None)
        metric = comparison["baseline_metrics"]
        calibration.set_title(f"direct-defined bins; n={metric['count']:,}; goals={metric['observed_positive_count']:,}", fontsize=9)
        calibration.margins(y=.25)
        calibration.legend(fontsize=8)
    caption = (
        "recorded goal scores on U; negative loss delta favors decomposition. intervals condition on two direct controls and four stage fits.\n"
        "2,000 paired pooled draws for each game/7-day/14-day method per window; no bootstrap fits; shared direct bins/support groups.\n"
        "own-arm bins remain separate tables. two coefficient sets and smaller conditional support change effective shrinkage; no admission."
    )
    if document["purpose"] == "fixture_exercise":
        caption = "fixture software exercise; scientific assessment not performed.\n" + caption
    figure.tight_layout(rect=(0, .14, 1, 1), h_pad=3)
    figure.text(.025, .015, caption, fontsize=8, va="bottom")
    comparison_path = destination / "comparison.png"
    figure.savefig(comparison_path, dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(2, 2, figsize=(13, 8), sharex="col", sharey="col")
    for row, window in enumerate(WINDOWS):
        for column, metric in enumerate(("on_net", "goal_given_on_net")):
            axis = axes[row, column]
            axis.axhline(0, color="#333333", lw=.8)
            axis.set_xlim(0, 1)
            axis.set_xlabel("mean own-bin prediction")
            axis.set_ylabel("predicted − observed\npercentage points")
            population = "U" if column == 0 else "O"
            axis.set_title(f"{window.replace('_', ' ')}; {'q: on-net' if column == 0 else 'g: goal given on-net'} on {population}")
            diagnostics = document["stage_diagnostics"][window]
            if diagnostics is None:
                axis.text(.5, .5, "stage assessment incomplete", transform=axis.transAxes, ha="center", va="center")
                continue
            stage = diagnostics[metric]["metrics"]
            buckets = [bucket for bucket in stage["calibration"] if bucket["count"]]
            xs = [bucket["predicted_rate"] for bucket in buckets]
            ys = [100 * (bucket["predicted_rate"] - bucket["observed_rate"]) for bucket in buckets]
            axis.scatter(xs, ys, s=16, color=colors["decomposed"])
            for x, y, bucket in zip(xs, ys, buckets, strict=True):
                edge, below = x >= .85, .85 <= x < .95
                axis.annotate(f"n={bucket['count']:,}", (x, y),
                              xytext=(-3 if edge else 3, -6 if below else 6), textcoords="offset points",
                              ha="right" if edge else "left", va="top" if below else "bottom",
                              fontsize=6, rotation=45,
                              arrowprops=dict(arrowstyle="-", lw=.3) if edge else None)
            axis.text(.03, .04, f"n={stage['count']:,}; positives={stage['observed_positive_count']:,}",
                      transform=axis.transAxes, fontsize=9)
            axis.margins(y=.25)
    caption = (
        "stage calibration is descriptive on its own target population: q uses all eligible unblocked U; g uses recorded on-net O.\n"
        "twenty own-probability bins; empty bins omitted from points; common axes within each column; no stage score ranking or intervals.\n"
        "both stages still predict every U row, including misses; own actor support remains separate. no physical validation or model admission."
    )
    if document["purpose"] == "fixture_exercise":
        caption = "fixture software exercise; scientific assessment not performed.\n" + caption
    figure.tight_layout(rect=(0, .14, 1, 1), h_pad=3)
    figure.text(.025, .015, caption, fontsize=8, va="bottom")
    stages_path = destination / "stages.png"
    figure.savefig(stages_path, dpi=180)
    plt.close(figure)
    return dict(comparison=identity(comparison_path), stages=identity(stages_path))


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    options = {
        "cohort": ("selection", "out"),
        "reuse": ("inputs", "protocol", "out"),
        "fit": ("selection", "cohort", "config", "protocol", "reuse", "window", "quantity", "out"),
        "evaluate": ("selection", "cohort-on-net", "cohort-conversion", "on-net-component",
                     "conversion-component", "protocol", "window", "out"),
        "report": ("inputs", "protocol", "out"),
    }
    for name, required in options.items():
        child = commands.add_parser(name, allow_abbrev=False)
        for option in required:
            choices = WINDOWS if option == "window" else QUANTITIES if option == "quantity" else None
            child.add_argument(f"--{option}", required=True, action=Once, choices=choices)
    args = parser.parse_args()
    try:
        return {"cohort": cohort_command, "reuse": reuse_command, "fit": fit_command,
                "evaluate": evaluate_command, "report": report_command}[args.command](args)
    except (InputContractError, OSError, KeyError, TypeError, ValueError, OverflowError, IndexError,
            AttributeError, ZeroDivisionError) as error:
        print(f"decomposition {args.command} failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
