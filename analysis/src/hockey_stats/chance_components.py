"""native component setup, source binding and saved-fit verification.

study policy stays with each study; these operations retain native quantities,
cohorts and diagnostics and never infer scientific support.
"""

import math
from pathlib import Path
import sys
import time

import numpy as np

from .artifacts import (
    agrees, clean_implementation, implementation, linked_path, require, resources, write_json,
)
from .chance_cli import identity, output_path, read_json
from .chance_features import PREPARATION_IDENTITY


def common(prepared):
    return dict(schema_version=3, purpose=prepared["purpose"], implementation=implementation(),
                inputs=prepared["inputs"], selection=prepared["selection"],
                game_dates=prepared["game_dates"], coverage=prepared["coverage"],
                preparation_identity=prepared["preparation_identity"],
                scientific_assessment="not_performed")


def source_identities(prepared):
    sources = {}
    for value in prepared["inputs"]:
        if value["kind"] == "game":
            gid = Path(value["path"]).stem
            require(gid not in sources and gid in prepared["game_dates"],
                    "duplicate or unselected game source identity")
            sources[gid] = value
    return sources


def validate_prepared_selection(prepared, selection):
    """bind a supplied native preparation to the actual selection bytes."""
    reference = identity(selection)
    require([value for value in prepared["inputs"] if value["kind"] == "selection"] ==
            [dict(kind="selection", **reference)], "prepared selection identity mismatch")
    document = read_json(selection)
    for corpus in document["corpora"]:
        corpus["path"] = str((selection.parent / corpus["path"]).resolve(strict=True))
    document["history_corpora"] = [
        str((selection.parent / path).resolve(strict=True))
        for path in document["history_corpora"]
    ]
    require(prepared["selection"] == document and prepared["purpose"] == document["purpose"] and
            prepared["preparation_identity"] == PREPARATION_IDENTITY,
            "prepared selection content or preparation identity mismatch")


def component_inputs(prepared, cohort, config, config_reference, protocol_reference, cohort_reference):
    from .chance import compile_component_design

    metadata = dict(common(prepared), config_identity=config_reference,
                    protocol_identity=protocol_reference, training_cohort_identity=cohort_reference,
                    training_game_dates=prepared["game_dates"],
                    training_game_ids=list(prepared["game_dates"]),
                    training_dates=sorted(set(prepared["game_dates"].values())))
    included = [attempt for attempt, membership in zip(prepared["attempts"], cohort["rows"], strict=True)
                if membership["study_inclusion"] == "included"]
    design = compile_component_design(included, config, quantity=cohort["quantity"],
                                      seasons=[game["season"] for game in prepared["games"]])
    return dict(
        attempts=[attempt for attempt in prepared["attempts"] if attempt["status"] == "eligible"],
        config=config, metadata=metadata, quantity=cohort["quantity"], design=design,
        training_cohort=cohort, feature_games=prepared["feature_games"],
        feature_player_games=prepared["feature_player_games"],
    )


def component_setup(prepared, cohort, config, config_reference, protocol_reference, cohort_reference):
    """encode the cohort's literal binary quantity through the production setup."""
    from .chance import prepare_component_fit

    return prepare_component_fit(**component_inputs(
        prepared, cohort, config, config_reference, protocol_reference, cohort_reference))


def fit_prepared(args, prepared, *, started=None):
    """write one native fit from an explicitly supplied source preparation."""
    from .chance import fit_component
    from .chance_cohort import outcome_audit, validate_cohort

    if started is None:
        started = time.monotonic()
    selection = Path(args.selection).resolve(strict=True)
    cohort_path = Path(args.cohort).resolve(strict=True)
    config_path = Path(args.config).resolve(strict=True)
    protocol = Path(args.protocol).resolve(strict=True)
    validate_prepared_selection(prepared, selection)
    cohort = validate_cohort(read_json(cohort_path), prepared)
    require(cohort["quantity"] == args.quantity, "training cohort quantity mismatch")
    output = output_path(args.out, prepared["input_roots"] +
                         [str(p.parent) for p in (selection, cohort_path, config_path, protocol)])
    inputs = component_inputs(prepared, cohort, read_json(config_path), identity(config_path),
                             identity(protocol), identity(cohort_path))
    output.mkdir()
    component, diagnostics = fit_component(**inputs, constraint="untied")
    document = dict(inputs["metadata"], artifact_kind="chance_component_fit", quantity=args.quantity,
                    stage_design=inputs["design"], training_cohort_audit=outcome_audit(prepared, cohort),
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


def selection_reference(cohort):
    """return the unique original selection after checking its resolved content."""
    references = [value for value in cohort["inputs"] if value["kind"] == "selection"]
    require(len(references) == 1, "cohort requires one consumed selection identity")
    reference = {key: references[0][key] for key in ("path", "sha256")}
    path = linked_path(reference)
    selected = read_json(path)
    require(isinstance(selected, dict) and set(selected) ==
            {"schema_version", "purpose", "corpora", "history_corpora"} and
            type(selected["schema_version"]) is int and selected["schema_version"] == 2 and
            selected["purpose"] == cohort["purpose"], "invalid native cohort selection")
    for entry in selected["corpora"]:
        entry["path"] = str((path.parent / entry["path"]).resolve(strict=True))
    selected["history_corpora"] = [str((path.parent / value).resolve(strict=True))
                                  for value in selected["history_corpora"]]
    require(selected == cohort["selection"], "consumed selection differs from cohort selection")
    return reference


def read_component_bundle(bundle, prepared, quantity):
    """rejoin explicitly bound cohort and target audits to the original source."""
    from .chance_cohort import validate_cohort, validate_outcome_audit, validate_target_audit

    require(isinstance(bundle, dict) and set(bundle) == {"cohort", "outcome_audit", "target_audit"},
            "component bundle requires cohort, outcome audit and target audit references")
    cohort = validate_cohort(read_json(linked_path(bundle["cohort"])), prepared)
    require(cohort["quantity"] == quantity and
            cohort["definition"] == dict(mode="all_source_eligible", required_families=[]),
            "component bundle requires the declared all-source target cohort")
    selected = selection_reference(cohort)
    validate_prepared_selection(prepared, linked_path(selected))
    audit = validate_outcome_audit(read_json(linked_path(bundle["outcome_audit"])), prepared, cohort)
    target = validate_target_audit(read_json(linked_path(bundle["target_audit"])), prepared, cohort,
                                   selection_identity=selected, cohort_identity=bundle["cohort"])
    return cohort, audit, target


def verify_decomposition_pair(prepared, cohorts):
    """q positives are exactly g's training/assessment population, in source order."""
    from .chance_targets import DECOMPOSITION_QUANTITIES, component_target

    require(set(cohorts) == set(DECOMPOSITION_QUANTITIES),
            "decomposition requires both native target cohorts")
    q, g = (cohorts[quantity] for quantity in DECOMPOSITION_QUANTITIES)
    require(all(q[field] == g[field] for field in
                ("purpose", "game_dates", "inputs", "selection", "preparation_identity")) and
            all(cohort["definition"] == dict(mode="all_source_eligible", required_families=[]) and
                cohort["counts"]["excluded_count"] == 0 for cohort in (q, g)),
            "stage cohorts must bind the same complete source selection")
    for attempt, qrow, grow in zip(prepared["attempts"], q["rows"], g["rows"], strict=True):
        require((qrow["study_inclusion"] == "included" and
                 component_target(attempt, DECOMPOSITION_QUANTITIES[0]) is True) ==
                (grow["study_inclusion"] == "included"),
                f"{attempt['game_id']}:{attempt['source_index']}: q positives differ from g included keys")


def read_component_fit(reference, cohort_reference, cohort, audit, *, coverage, config, protocol, quantity,
                       purpose, expected_implementation=None):
    """validate one completed native fit without imposing a study's recipe policy."""
    from .chance import validate_component, validate_config

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
    native_config = read_json(linked_path(config))
    validate_config(native_config)
    require(component["purpose"] == purpose and component["quantity"] == quantity == cohort["quantity"] and
            component["extraction"] is None and component["config_identity"] == config and
            component["protocol_identity"] == protocol and
            component["training_cohort"] == dict(
                definition=cohort["definition"], membership_identity=cohort_reference,
                **{field: cohort["counts"][field] for field in
                   ("source_applicable_count", "included_count", "excluded_count")}) and
            component["training_game_dates"] == cohort["game_dates"] and
            component["diagnostics"]["converged"] is True and component["config"] == native_config and
            all(component[field] == cohort[field] for field in
                ("purpose", "selection", "inputs", "preparation_identity")),
            "native fitted component target/config/protocol/source mismatch")
    require(isinstance(fit, dict) and set(fit) == {
        "schema_version", "purpose", "implementation", "inputs", "selection", "game_dates",
        "coverage", "preparation_identity", "scientific_assessment", "config_identity",
        "protocol_identity", "training_cohort_identity", "training_game_dates", "training_game_ids",
        "training_dates", "artifact_kind", "quantity", "stage_design", "training_cohort_audit",
        "diagnostics", "status", "resources",
    } and type(fit["schema_version"]) is int and fit["schema_version"] == 3 and
            fit["artifact_kind"] == "chance_component_fit" and fit["status"] == "fitted" and
            fit["diagnostics"] == component["diagnostics"] and
            fit["training_cohort_identity"] == cohort_reference and fit["training_cohort_audit"] == audit and
            fit["stage_design"] == component["layout"]["design"] and
            fit["scientific_assessment"] == "not_performed" and
            fit["game_dates"] == component["training_game_dates"] and
            fit["coverage"] == coverage and
            all(fit[field] == component[field] for field in (
                "purpose", "quantity", "config_identity", "protocol_identity", "selection", "inputs",
                "implementation", "preparation_identity", "training_game_dates", "training_game_ids",
                "training_dates")) and
            (expected_implementation is None or component["implementation"] == expected_implementation),
            "native fit source/design/diagnostics/implementation mismatch")
    if purpose == "research":
        clean_implementation(component["implementation"])
    return document, component, fit


def objective_replay(component, prepared, cohort, *, component_reference, cohort_reference,
                     protocol, parameterization=None):
    """replay one saved objective and its gradient through the native setup.

    callers supply source preparation already reconciled to the cohort. an
    explicit parameterization is regenerated and its free gradient is reported;
    the native full gradient is retained for historical receipt consumers.
    """
    from .chance import (
        component_objective, free_coefficients, project_gradient, validate_component,
        validate_spatial_parameterization,
    )

    validate_component(component)
    require(component["quantity"] == cohort["quantity"] and
            component["protocol_identity"] == protocol and
            component["training_cohort"]["membership_identity"] == cohort_reference,
            "objective replay component/cohort/protocol mismatch")
    layout, data, centers, edges, initial = component_setup(
        prepared, cohort, component["config"], component["config_identity"], protocol, cohort_reference)
    require(data is not None and initial is not None and
            layout == {key: value for key, value in component["layout"].items()
                       if key not in ("coefficients", "diagnostics")},
            "replayed source/encoding/design/actor layout differs from saved component")
    beta = np.asarray(component["layout"]["coefficients"])
    replayed, gradient = component_objective(beta, data, layout, component["config"], edges, centers)
    saved = component["diagnostics"]["objective"]
    require(math.isfinite(replayed) and np.isfinite(gradient).all() and agrees(saved, replayed),
            "saved native objective does not agree with replay")
    receipt = dict(schema_version=1, purpose=prepared["purpose"], component=component_reference,
                   selection=selection_reference(cohort), cohort=cohort_reference,
                   config=component["config_identity"], protocol=protocol, implementation=implementation(),
                   saved_objective=saved, replayed_objective=float(replayed), difference=float(replayed - saved),
                   gradient_max_abs=float(np.max(np.abs(gradient))), agrees=True)
    if parameterization is not None:
        expected = validate_spatial_parameterization(layout, centers, parameterization)
        free_coefficients(beta, expected)
        free_gradient = project_gradient(gradient, expected)
        require(np.isfinite(free_gradient).all(), "nonfinite projected objective gradient")
        receipt.update(free_gradient_max=float(np.max(np.abs(free_gradient))),
                       full_count=expected["full_count"], free_count=expected["free_count"])
    return receipt
