"""manual native short/expanded conversion-history study; no model admission."""

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import time

import numpy as np

from hockey_stats.artifacts import write_json
from hockey_stats.captures import InputContractError
from hockey_stats.chance import validate_component, validate_config
from hockey_stats.chance_cli import identity, output_path, read_json
from hockey_stats.chance_cohort import (
    component_cohort, outcome_audit, validate_cohort, validate_cohort_document,
    validate_outcome_audit, validate_outcome_audit_document,
)
from hockey_stats.chance_data import prepare_core
from hockey_stats.chance_features import PREPARATION_IDENTITY
from hockey_stats.cli import Once
from chance_development import (
    component_setup, compare_pair, evaluate_prepared, fit_prepared, implementation,
    paired_rows, resources, validate_evaluation,
)
from chance_review import agrees, clean_implementation, linked_path, require
from chance_sequence import independent_loss

WINDOWS = ("development", "season_transfer")
ARMS = ("short", "expanded")
QUANTITY = "unblocked_conversion"
FAMILIES = ["game_additive", "recent_additive", "recent_interactions"]
DEFINITION = dict(mode="all_source_eligible", required_families=[])
DEADBAND = 1e-10
CAPACITY_LIMIT_BYTES = 48 * 2**30
RESAMPLING = dict(draws=2000, seed=3032026, generator="PCG64",
                  percentile_method="linear", calendar_days=[7, 14])
SETTINGS = dict(
    kernel_distance_ft=20, kernel_direction_strength=4,
    ridge_origin_base=.25, ridge_cell=.25, ridge_benchmark=.25,
    ridge_origin_factor=1, ridge_type_cell=1, smooth_origin=4, smooth_cell=4,
    ridge_context=4, ridge_shooter=4, change_shooter=16,
    ridge_goalie=16, change_goalie=64, optimizer_max_iterations=2000,
    optimizer_ftol=1e-10, optimizer_gtol=1e-6, em_max_iterations=2000,
    em_relative_tolerance=1e-8, em_posterior_tolerance=1e-6,
    objective_decrease_tolerance=1e-10,
)
TOTALS = {
    ("development", "short"): (1912, 128679, 7614),
    ("development", "expanded"): (4536, 306041, 18471),
    ("development", "assessment"): (712, 49014, 2804),
    ("season_transfer", "short"): (2624, 177693, 10418),
    ("season_transfer", "expanded"): (5248, 355055, 21275),
    ("season_transfer", "assessment"): (1312, 87018, 5291),
}
REPORT_GROUPS = (
    "recent_context", "model_type", "calendar_month", "role",
    "actor_support:shooter", "actor_support:goalie",
)
SUPPORT = ("observed_in_state", "other_seasons_only", "unseen")
SOURCE_SELECTION = dict(
    path="/Volumes/Expansion/hockey-stats/runs/03m-20261010-03/inputs/selection.json",
    sha256="2e924d8ca08c4bd1191d4b3f9bfccbd4f795f8bc6283d39b5aed3c81c579bdac",
)
SOURCE_AUDIT = dict(
    path="/Volumes/Expansion/hockey-stats/runs/03m-20261010-03/audit/admission-audit.json",
    sha256="78d4034971e8d781ceb5dfa6af56b64ffb423e368027dc9c08a6701a4540b6d6",
)
MANIFEST_PATHS = {
    season: f"/Volumes/Expansion/hockey-stats/corpora/{run}/{season}/corpus.json"
    for season, run in (("20212022", "03m-20261010-02"), ("20222023", "03m-20261010"),
                        ("20232024", "03m-20261010"), ("20242025", "03m-20261010"),
                        ("20252026", "03m-20261010"))
}
LIMITATIONS = [
    "the native estimator-horizon package changes annual actor support, earliest seasonal reference, borrowing and likelihood-to-penalty balance; it does not isolate sample size",
    "fixed penalties are not fixed effective regularization; geometry/type/context are pooled and annual actor states are jointly fitted, not preceding-season prior propagation",
    "2025–26 predictions carry the latest fitted 2024–25 states; older-only actor states may be penalty-inferred and unseen actors contribute zero residual",
    "95% intervals condition on the four fitted models and omit fitting, selection and source uncertainty; chronological windows are research-exposed, not independent confirmations",
    "recorded goal probabilities and source coordinate/continuity proxies do not establish physical-origin accuracy, causal attribution, player value, peer parity or model admission",
    "native optimizer success may use relative objective reduction before gradient tolerance; the arithmetic deadband is neither a useful-effect threshold nor a solver-error bound",
    "capacity measures setup and one initial objective, not an optimized fit peak; external-only outputs accept manual rerun after an interrupted solve",
    "horizon nomination is conditional research evidence; horizon adoption, 03o, 04 and publication remain separately assigned",
]


def validate_recipe(config):
    validate_config(config)
    require(config["trait_assumptions"] == [] and
            all(config[key] == value for key, value in SETTINGS.items()),
            "history recipe differs from the fixed numerical settings")
    require(config["stage_families"]["r"] == FAMILIES and
            all(config["stage_families"][stage] == ["game_additive", "recent_additive"]
                for stage in ("origin", "u", "unblocked", "all_attempt")),
            "history core preparation supports only the declared three conversion families")
    return config


def selection_reference(cohort):
    references = [value for value in cohort["inputs"] if value["kind"] == "selection"]
    require(len(references) == 1, "cohort requires one consumed selection identity")
    reference = {key: references[0][key] for key in ("path", "sha256")}
    path = linked_path(reference)
    selected = read_json(path)
    require(isinstance(selected, dict) and set(selected) ==
            {"schema_version", "purpose", "corpora", "history_corpora"} and
            type(selected["schema_version"]) is int and selected["schema_version"] == 2 and
            selected["purpose"] == cohort["purpose"] and selected["history_corpora"] == [],
            "history study requires schema-2 explicit selections with empty history")
    for entry in selected["corpora"]:
        entry["path"] = str((path.parent / entry["path"]).resolve(strict=True))
    require(selected == cohort["selection"], "consumed selection differs from cohort selection")
    return reference


def admitted_corpora():
    """obtain manifest identities from the bound 03m audit, without re-admission."""
    selected = read_json(linked_path(SOURCE_SELECTION))
    audit = read_json(linked_path(SOURCE_AUDIT))
    require(audit["schema_version"] == 1 and audit["purpose"] == "research" and
            audit["status"] == "complete" and audit["selection"] == SOURCE_SELECTION and
            audit["preparation_identity"] == PREPARATION_IDENTITY and
            [entry["path"] for entry in selected["corpora"]] == list(MANIFEST_PATHS.values()),
            "bound 03m selection/audit disagree")
    references = {value["path"]: {key: value[key] for key in ("path", "sha256")}
                  for value in audit["inputs"] if value["kind"] == "corpus"}
    require(set(references) == set(MANIFEST_PATHS.values()) and
            references[MANIFEST_PATHS["20212022"]]["sha256"] ==
            "30eb12b290ccd9af9eae7ade8c7dcd5f285129b52b646eec3fced3e2628badc8",
            "03m audit must bind all five canonical manifest identities")
    return references


def selected_inventory(cohort):
    """bind exact inventory chronology, retaining every selected empty game."""
    canonical = admitted_corpora() if cohort["purpose"] == "research" else None
    inventories, selected, dates, previous_season = {}, {}, {}, None
    for entry in cohort["selection"]["corpora"]:
        references = [value for value in cohort["inputs"]
                      if value["kind"] == "corpus" and value["path"] == entry["path"]]
        require(len(references) == 1, "selected corpus lacks a unique consumed identity")
        reference = {key: references[0][key] for key in ("path", "sha256")}
        if canonical is not None:
            require(reference == canonical.get(entry["path"]), "research manifest identity changed")
        manifest = read_json(linked_path(reference))
        season = manifest["reference"]["requested_season"]
        inventory = manifest["reference"]["inventory"]
        indexed = {game["game_id"]: game for game in inventory}
        require(len(indexed) == len(inventory) and
                all(game["season"] == season for game in inventory) and
                (previous_season is None or season > previous_season),
                "inventory identity/season or corpus order disagreement")
        previous_season = season
        ids = entry["game_ids"]
        require(len(set(ids)) == len(ids) and set(ids) <= set(indexed) and
                not set(ids) & set(dates) and
                ids == sorted(ids, key=lambda gid: (indexed[gid]["game_date"], gid)),
                "selected game keys must be unique and in inventory date/id order")
        inventories[season], selected[season] = indexed, set(ids)
        dates.update({gid: indexed[gid]["game_date"] for gid in ids})
    require(list(dates.items()) == list(cohort["game_dates"].items()),
            "selected inventory order/dates differ from cohort")
    return inventories, selected


def expected_population(inventories, window, partition):
    if partition == "assessment":
        seasons = ["20242025"] if window == "development" else ["20252026"]
    else:
        seasons = (["20212022", "20222023"] if partition == "expanded" else []) + ["20232024", "20242025"]
    if set(inventories) != set(seasons):
        return None
    expected = {season: set(inventories[season]) for season in seasons}
    if window == "development":
        expected["20242025"] = {
            gid for gid, game in inventories["20242025"].items()
            if (game["game_date"] >= "2025-01-01") == (partition == "assessment")
        }
    return expected


def validate_population(cohort, audit, *, window=None, partition=None):
    inventories, selected = selected_inventory(cohort)
    require(audit["omitted"] == dict(attempts=0, goals=0) and
            audit["included"] == audit["source_applicable"],
            "history study must include all applicable source rows without feature omissions")
    if cohort["purpose"] == "fixture_exercise":
        return
    candidates = [(w, p) for w, p in TOTALS
                  if (window is None or w == window) and (partition is None or p == partition) and
                  expected_population(inventories, w, p) == selected]
    require(len(candidates) == 1, "research selection is not one of the exact six declared partitions")
    key = candidates[0]
    require((len(cohort["game_dates"]), audit["included"]["attempts"], audit["included"]["goals"]) == TOTALS[key],
            "research games/applicable rows/goals differ from the frozen totals")
    if key[1] != "assessment":
        require(0 < audit["included"]["goals"] < audit["included"]["attempts"],
                "training requires both binary goal outcomes")


def read_cohort(reference, purpose):
    path = linked_path(reference)
    cohort = validate_cohort_document(read_json(path))
    require(cohort["purpose"] == purpose and cohort["quantity"] == QUANTITY and
            cohort["definition"] == DEFINITION and
            cohort["preparation_identity"] == PREPARATION_IDENTITY,
            "history cohort purpose/quantity/definition/preparation mismatch")
    selection_reference(cohort)
    audit = validate_outcome_audit_document(read_json(path.with_name("outcome_audit.json")), cohort)
    return cohort, audit


def validate_window(window, arm, training, assessment, training_audit, assessment_audit):
    validate_population(training, training_audit, window=window, partition=arm)
    validate_population(assessment, assessment_audit, window=window, partition="assessment")
    require(not set(training["game_dates"]) & set(assessment["game_dates"]) and
            min(assessment["game_dates"].values()) > max(training["game_dates"].values()),
            "every assessment game/date must follow disjoint training")


def cohort_command(args):
    started = time.monotonic()
    selection = Path(args.selection).resolve(strict=True)
    protocol = Path(args.protocol).resolve(strict=True)
    prepared = prepare_core(selection)
    cohort = component_cohort(prepared, quantity=QUANTITY, required_families=[])
    audit = outcome_audit(prepared, cohort)
    validate_population(cohort, audit)
    output = output_path(args.out, prepared["input_roots"] + [str(selection.parent), str(protocol.parent)])
    output.mkdir()
    write_json(output / "cohort.json", cohort)
    write_json(output / "outcome_audit.json", audit)
    validate_cohort(read_json(output / "cohort.json"), prepared)
    validate_outcome_audit(read_json(output / "outcome_audit.json"), prepared, cohort)
    write_json(output / "completion.json", dict(
        schema_version=1, artifact_kind="chance_history_cohort_completion", purpose=prepared["purpose"],
        protocol=identity(protocol), selection=identity(selection), cohort=identity(output / "cohort.json"),
        outcome_audit=identity(output / "outcome_audit.json"), resources=resources(started),
        scientific_assessment="not_performed"))
    print(f"history cohort complete: {output}; scientific assessment not performed")
    return 0


def capacity_command(args):
    from hockey_stats.chance import component_objective

    started = time.monotonic()
    selection = Path(args.selection).resolve(strict=True)
    cohort_path = Path(args.cohort).resolve(strict=True)
    config_path = Path(args.config).resolve(strict=True)
    protocol = Path(args.protocol).resolve(strict=True)
    config = validate_recipe(read_json(config_path))
    prepared = prepare_core(selection)
    cohort, audit = read_cohort(identity(cohort_path), prepared["purpose"])
    validate_cohort(cohort, prepared)
    validate_outcome_audit(audit, prepared, cohort)
    validate_population(cohort, audit, window="season_transfer", partition="expanded")
    output = output_path(args.out, prepared["input_roots"] +
                         [str(path.parent) for path in (selection, cohort_path, config_path, protocol)])
    layout, data, centers, edges, initial = component_setup(
        prepared, cohort, config, identity(config_path), identity(protocol), identity(cohort_path))
    require(data is not None and initial is not None, "capacity setup requires goals and non-goals")
    value, gradient = component_objective(initial, data, layout, config, edges, centers)
    require(math.isfinite(value) and np.isfinite(initial).all() and np.isfinite(gradient).all(),
            "nonfinite native initial objective/gradient")
    require(data["scalar"].shape == (audit["included"]["attempts"], 65),
            "history recipe must encode all 65 scalar columns")
    initial_intercept = math.log(audit["included"]["goals"] /
                                 (audit["included"]["attempts"] - audit["included"]["goals"]))
    require(agrees(float(initial[0]), initial_intercept) and not np.any(initial[1:]),
            "native initialization must contain only the cohort empirical intercept")
    array_bytes = {name: int(array.nbytes) for name, array in data.items()}
    array_bytes.update(centers=int(centers.nbytes), edges=int(edges.nbytes),
                       initial=int(initial.nbytes), gradient=int(gradient.nbytes))
    slices = layout["design"]["slices"]
    document = dict(
        schema_version=1, artifact_kind="chance_history_capacity", purpose=prepared["purpose"],
        selection=identity(selection), cohort=identity(cohort_path), config=identity(config_path),
        protocol=identity(protocol), implementation=implementation(),
        preparation_identity=prepared["preparation_identity"], setup_status="valid",
        counts=dict(games=len(prepared["game_dates"]), **cohort["counts"],
                    goals=audit["included"]["goals"]), design=layout["design"],
        dimensions=dict(scalar_shape=list(data["scalar"].shape), seasons=layout["seasons"],
                        season_offsets=len(layout["seasons"]) - 1,
                        core_coefficients=slices["core"][1] - slices["core"][0],
                        shooter_actors=len(layout["shooters"]), goalie_actors=len(layout["goalies"]),
                        shooter_states=slices["shooter"][1] - slices["shooter"][0],
                        goalie_states=slices["goalie"][1] - slices["goalie"][0],
                        total_coefficients=layout["size"]), array_bytes=array_bytes,
        initial=dict(empirical_intercept=float(initial[0]), objective=float(value),
                     gradient_max_abs=float(np.max(np.abs(gradient)))),
        resources_before_serialization=resources(started),
    )
    output.mkdir()
    write_json(output / "capacity.json", document)
    require(read_json(config_path) == config and read_json(cohort_path) == cohort and
            read_json(output / "capacity.json") == document,
            "capacity/config/cohort serialization does not reconcile")
    validate_capacity_document(document, purpose=prepared["purpose"], protocol=identity(protocol))
    print(f"history capacity setup complete: {output}; final process footprint still requires measurement")
    return 0


def parse_timing_log(content):
    """extract the three final macos /usr/bin/time -l measurements."""
    patterns = dict(
        wall_seconds=r"^\s*([0-9]+(?:\.[0-9]+)?)\s+real\s+[0-9.]+\s+user\s+[0-9.]+\s+sys\s*$",
        peak_rss_bytes=r"^\s*([0-9]+)\s+maximum resident set size\s*$",
        peak_footprint_bytes=r"^\s*([0-9]+)\s+peak memory footprint\s*$",
    )
    values = {}
    for field, pattern in patterns.items():
        matches = re.findall(pattern, content, re.MULTILINE)
        require(len(matches) == 1, f"timing log requires exactly one final {field}")
        values[field] = float(matches[0]) if field == "wall_seconds" else int(matches[0])
    return values


def validate_capacity_document(document, *, purpose, protocol):
    require(isinstance(document, dict) and set(document) == {
        "schema_version", "artifact_kind", "purpose", "selection", "cohort", "config", "protocol",
        "implementation", "preparation_identity", "setup_status", "counts", "design", "dimensions",
        "array_bytes", "initial", "resources_before_serialization",
    } and type(document["schema_version"]) is int and document["schema_version"] == 1 and
        document["artifact_kind"] == "chance_history_capacity" and document["purpose"] == purpose and
        document["protocol"] == protocol and document["preparation_identity"] == PREPARATION_IDENTITY and
        document["setup_status"] == "valid", "invalid native history capacity schema/binding")
    for field in ("selection", "cohort", "config", "protocol"):
        require(isinstance(document[field], dict) and set(document[field]) == {"path", "sha256"},
                "capacity requires located artifact identities")
    validate_recipe(read_json(linked_path(document["config"])))
    cohort, audit = read_cohort(document["cohort"], purpose)
    require(document["selection"] == selection_reference(cohort), "capacity selection/cohort identity mismatch")
    validate_population(cohort, audit, window="season_transfer", partition="expanded")
    require(document["counts"] == dict(games=len(cohort["game_dates"]), **cohort["counts"],
                                        goals=audit["included"]["goals"]),
            "capacity source/cohort/outcome counts mismatch")
    dimensions, design = document["dimensions"], document["design"]
    size_fields = ("season_offsets", "core_coefficients", "shooter_actors", "goalie_actors",
                   "shooter_states", "goalie_states", "total_coefficients")
    require(isinstance(dimensions, dict) and set(dimensions) == {"scalar_shape", "seasons", *size_fields} and
            all(type(dimensions[field]) is int and dimensions[field] >= 0 for field in size_fields) and
            isinstance(dimensions["scalar_shape"], list) and len(dimensions["scalar_shape"]) == 2 and
            all(type(value) is int and value >= 0 for value in dimensions["scalar_shape"]),
            "capacity dimensions require exact nonnegative integer fields")
    slices = design["slices"]
    require(design["stage"] == "r" and design["families"] == FAMILIES and
            design["trait_assumptions"] == [] and design["preparation_identity"] == PREPARATION_IDENTITY and
            len(design["circumstance_columns"]) == 65 and
            dimensions["scalar_shape"] == [audit["included"]["attempts"], 65] and
            dimensions["seasons"] == design["core_layout"]["seasons"] and
            dimensions["season_offsets"] == len(dimensions["seasons"]) - 1 and
            dimensions["core_coefficients"] == slices["core"][1] - slices["core"][0] and
            dimensions["shooter_states"] == slices["shooter"][1] - slices["shooter"][0] and
            dimensions["goalie_states"] == slices["goalie"][1] - slices["goalie"][0] and
            dimensions["core_coefficients"] + 65 + dimensions["shooter_states"] +
            dimensions["goalie_states"] == dimensions["total_coefficients"] == len(design["columns"]) and
            all(dimensions[actor + "_states"] == dimensions[actor + "_actors"] * len(dimensions["seasons"])
                for actor in ("shooter", "goalie")),
            "capacity native design/dimensions mismatch")
    require(set(document["initial"]) == {"empirical_intercept", "objective", "gradient_max_abs"} and
            all(type(value) in (int, float) and math.isfinite(value) for value in document["initial"].values()) and
            document["initial"]["gradient_max_abs"] >= 0 and
            0 < audit["included"]["goals"] < audit["included"]["attempts"] and
            agrees(document["initial"]["empirical_intercept"], math.log(
                audit["included"]["goals"] / (audit["included"]["attempts"] - audit["included"]["goals"]))),
            "invalid capacity native initial arithmetic")
    attempts, goals = audit["included"]["attempts"], audit["included"]["goals"]
    probability = goals / attempts
    empirical_loss = -goals * math.log(probability) - (attempts - goals) * math.log1p(-probability)
    require(agrees(document["initial"]["objective"], empirical_loss),
            "capacity intercept-only objective does not reconcile to empirical binary loss")
    require(isinstance(document["array_bytes"], dict) and document["array_bytes"] and
            all(type(value) is int and value >= 0 for value in document["array_bytes"].values()) and
            document["array_bytes"]["scalar"] == audit["included"]["attempts"] * 65 * 8,
            "capacity array byte counts mismatch")
    measured = document["resources_before_serialization"]
    require(set(measured) == {"wall_seconds", "peak_memory_bytes"} and
            type(measured["wall_seconds"]) in (int, float) and math.isfinite(measured["wall_seconds"]) and
            measured["wall_seconds"] >= 0 and type(measured["peak_memory_bytes"]) is int and
            measured["peak_memory_bytes"] >= 0, "invalid pre-serialization capacity resources")
    if purpose == "research":
        clean_implementation(document["implementation"])
    return document


def validate_capacity(record, *, purpose, protocol):
    """operator prefit check and report check share the post-exit resource contract."""
    require(record["status"] == "complete", "capacity is not a completed operating pass")
    document = validate_capacity_document(read_json(linked_path(record["setup"])), purpose=purpose, protocol=protocol)
    measurement = read_json(linked_path(record["measurement"]))
    require(isinstance(measurement, dict) and set(measurement) == {
        "schema_version", "capacity", "timing_log", "argv", "exit_code", "wall_seconds",
        "peak_rss_bytes", "peak_footprint_bytes",
    } and type(measurement["schema_version"]) is int and measurement["schema_version"] == 1 and
        measurement["capacity"] == record["setup"] and
        type(measurement["exit_code"]) is int and measurement["exit_code"] == 0,
        "invalid post-exit capacity measurement/binding")
    extracted = parse_timing_log(linked_path(measurement["timing_log"]).read_text(encoding="utf-8"))
    require(all(type(measurement[field]) is int and measurement[field] == extracted[field]
                for field in ("peak_rss_bytes", "peak_footprint_bytes")) and
            type(measurement["wall_seconds"]) in (int, float) and
            math.isfinite(measurement["wall_seconds"]) and measurement["wall_seconds"] >= 0,
            "capacity measurement differs from final timing log or has invalid elapsed time")
    for field in ("capacity", "timing_log"):
        require(isinstance(measurement[field], dict) and set(measurement[field]) == {"path", "sha256"},
                "capacity measurement requires located artifact identities")
    argv = measurement["argv"]
    require(isinstance(argv, list) and len(argv) == 13 and
            all(isinstance(value, str) and value for value in argv) and
            Path(argv[1]).name == "chance_history.py" and argv[2] == "capacity",
            "capacity measurement requires the exact manual command argv")
    options = dict(zip(argv[3::2], argv[4::2], strict=True))
    require(len(options) == 5 and set(options) == {"--selection", "--cohort", "--config", "--protocol", "--out"} and
            all(options[f"--{field}"] == document[field]["path"]
                for field in ("selection", "cohort", "config", "protocol")) and
            options["--out"] == str(Path(record["setup"]["path"]).parent),
            "capacity timing argv does not bind the measured inputs/output")
    require(extracted["peak_rss_bytes"] <= CAPACITY_LIMIT_BYTES and
            extracted["peak_footprint_bytes"] <= CAPACITY_LIMIT_BYTES,
            "capacity exceeds the fixed 48-gib operating envelope")
    return document, measurement


def fit_command(args):
    started = time.monotonic()
    selection = Path(args.selection).resolve(strict=True)
    validate_recipe(read_json(Path(args.config).resolve(strict=True)))
    prepared = prepare_core(selection)
    cohort, audit = read_cohort(identity(Path(args.cohort).resolve(strict=True)), prepared["purpose"])
    validate_cohort(cohort, prepared)
    validate_outcome_audit(audit, prepared, cohort)
    validate_population(cohort, audit, window=args.window, partition=args.arm)
    args.quantity = QUANTITY
    return fit_prepared(args, prepared, started=started)


def evaluate_command(args):
    started = time.monotonic()
    component = validate_component(read_json(Path(args.component).resolve(strict=True)))
    validate_recipe(component["config"])
    require(component["quantity"] == QUANTITY and component["extraction"] is None and
            component["training_cohort"]["definition"] == DEFINITION and
            component["training_cohort"]["excluded_count"] == 0,
            "history evaluation requires a fresh full-source conversion component")
    prepared = prepare_core(Path(args.selection).resolve(strict=True))
    training, training_audit = read_cohort(component["training_cohort"]["membership_identity"], prepared["purpose"])
    assessment, assessment_audit = read_cohort(identity(Path(args.cohort).resolve(strict=True)), prepared["purpose"])
    validate_cohort(assessment, prepared)
    validate_outcome_audit(assessment_audit, prepared, assessment)
    validate_window(args.window, args.arm, training, assessment, training_audit, assessment_audit)
    return evaluate_prepared(args, prepared, started=started)


def validate_report_inputs(document):
    require(isinstance(document, dict) and set(document) ==
            {"schema_version", "purpose", "capacity", "windows", "resampling"} and
            type(document["schema_version"]) is int and document["schema_version"] == 1 and
            document["purpose"] in ("research", "fixture_exercise") and document["resampling"] == RESAMPLING and
            all(type(document["resampling"][field]) is int for field in ("draws", "seed")) and
            all(type(value) is int for value in document["resampling"]["calendar_days"]),
            "schema-1 history report inputs with fixed resampling required")
    capacity = document["capacity"]
    require(isinstance(capacity, dict) and set(capacity) ==
            {"status", "setup", "measurement", "failure", "stop_reason"} and
            capacity["status"] in ("complete", "failed", "not_run"), "invalid capacity input fields/status")
    require(isinstance(document["windows"], dict) and set(document["windows"]) == set(WINDOWS),
            "history report requires exactly both declared windows")
    records = [(capacity, ("setup", "measurement"))]
    for window in WINDOWS:
        cells = document["windows"][window]
        require(isinstance(cells, dict) and set(cells) == set(ARMS), "each window requires short and expanded")
        for arm in ARMS:
            cell = cells[arm]
            require(isinstance(cell, dict) and set(cell) == {
                "status", "config", "training_cohort", "assessment_cohort", "fit",
                "evaluation", "failure", "stop_reason",
            } and cell["status"] in ("complete", "failed", "not_run"), "invalid history cell fields/status")
            records.append((cell, ("config", "training_cohort", "assessment_cohort", "fit", "evaluation")))
        require(cells["short"]["assessment_cohort"] is None or cells["expanded"]["assessment_cohort"] is None or
                cells["short"]["assessment_cohort"] == cells["expanded"]["assessment_cohort"],
                "each assessment pair must bind one identical cohort identity")
    stopped = False
    configs = []
    for record, required in records:
        for field in (*required, "failure"):
            value = record[field]
            require(value is None or isinstance(value, dict) and set(value) == {"path", "sha256"},
                    "artifact references require located path/sha256 identities")
        status = record["status"]
        require(not stopped or status == "not_run", "a capacity/source/numerical stop must stop later cells")
        if status == "complete":
            require(all(record[field] is not None for field in required) and
                    record["failure"] is None and record["stop_reason"] is None,
                    "completed capacity/cell requires all successful artifacts and no failure")
        else:
            require(isinstance(record["stop_reason"], str) and bool(record["stop_reason"].strip()),
                    "incomplete execution requires an explicit stop reason")
            require(status != "failed" or record["failure"] is not None, "failure requires located evidence")
            if record is capacity:
                require(record["measurement"] is None and
                        (status != "not_run" or record["setup"] is None),
                        "incomplete capacity cannot claim a completed measurement")
            else:
                require(record["evaluation"] is None and (status != "not_run" or record["fit"] is None),
                        "unfinished cell cannot claim unfinished successful completions")
        stopped = status != "complete"
        if record is not capacity and record["config"] is not None:
            configs.append(record["config"])
    require(not configs or all(value == configs[0] for value in configs), "all four cells require one config identity")
    return document


def decision(comparisons, *, purpose):
    if purpose == "fixture_exercise":
        return "not_assessed", "fixture_only", None
    require(purpose == "research", "unsupported history report purpose")
    if any(comparisons[window] is None for window in WINDOWS):
        return "incomplete", "no_supported_horizon", None
    primary = [comparisons[window]["delta"]["log_loss"] for window in WINDOWS]
    points = [value["games"]["estimate"] for value in primary]
    if any(value is None for value in points):
        return "incomplete", "no_supported_horizon", None
    require(all(type(value) in (int, float) and math.isfinite(value) for value in points),
            "primary point estimates must be finite")
    direction = ("expanded_direction" if all(value < -DEADBAND for value in points) else
                 "short_direction" if all(value > DEADBAND for value in points) else
                 "within_arithmetic_deadband" if all(abs(value) <= DEADBAND for value in points) else
                 "mixed_direction")
    defined = all(value[unit]["interval"] is not None
                  for value in primary for unit in ("games", "calendar_7_day", "calendar_14_day"))
    nominated = None
    if (defined and direction == "expanded_direction" and
            all(value["games"]["interval"][1] < -DEADBAND for value in primary) and
            not any(value[unit]["interval"][0] > DEADBAND
                    for value in primary for unit in ("calendar_7_day", "calendar_14_day"))):
        nominated = "expanded"
    if (defined and direction == "short_direction" and
            all(value["games"]["interval"][0] > DEADBAND for value in primary) and
            not any(value[unit]["interval"][1] < -DEADBAND
                    for value in primary for unit in ("calendar_7_day", "calendar_14_day"))):
        nominated = "short"
    return direction, "supported_horizon" if nominated else "no_supported_horizon", nominated


def verify_component(component, component_reference, cohort, cohort_reference, protocol):
    """replay the saved objective once, through the production setup and objective."""
    from hockey_stats.chance import component_objective

    require(component["quantity"] == cohort["quantity"], "objective replay component/cohort quantity mismatch")
    selected = selection_reference(cohort)
    prepared = prepare_core(linked_path(selected))
    validate_cohort(cohort, prepared)
    layout, data, centers, edges, initial = component_setup(
        prepared, cohort, component["config"], component["config_identity"], protocol, cohort_reference)
    require(data is not None and initial is not None and
            layout == {key: value for key, value in component["layout"].items() if key != "coefficients"},
            "replayed source/encoding/design/actor layout differs from saved component")
    beta = np.asarray(component["layout"]["coefficients"])
    replayed, gradient = component_objective(beta, data, layout, component["config"], edges, centers)
    saved = component["diagnostics"]["objective"]
    require(math.isfinite(replayed) and np.isfinite(gradient).all() and agrees(saved, replayed),
            "saved native objective does not agree with replay")
    receipt = dict(schema_version=1, purpose=prepared["purpose"], component=component_reference,
                   selection=selected, cohort=cohort_reference, config=component["config_identity"],
                   protocol=protocol, implementation=implementation(), saved_objective=saved,
                   replayed_objective=float(replayed), difference=float(replayed - saved),
                   gradient_max_abs=float(np.max(np.abs(gradient))), agrees=True)
    return receipt, prepared["input_roots"]


def report_command(args):
    started = time.monotonic()
    inputs_path = Path(args.inputs).resolve(strict=True)
    protocol_path = Path(args.protocol).resolve(strict=True)
    protocol = identity(protocol_path)
    inputs = validate_report_inputs(read_json(inputs_path))
    purpose = inputs["purpose"]
    roots = [str(inputs_path.parent), str(protocol_path.parent)]
    capacity, measurement = None, None
    if inputs["capacity"]["status"] == "complete":
        capacity, measurement = validate_capacity(inputs["capacity"], purpose=purpose, protocol=protocol)
        roots.append(str(linked_path(measurement["timing_log"]).parent))
    for field in ("setup", "measurement", "failure"):
        if inputs["capacity"][field] is not None:
            roots.append(str(linked_path(inputs["capacity"][field]).parent))
    cells, comparisons, coverage, receipts = {}, {}, {}, {}
    training_cohorts = {}
    fitted_implementation = None
    for window in WINDOWS:
        cells[window], coverage[window] = {}, {}
        assessment_reference = None
        assessment_cohort = None
        assessment_audit = None
        assessment_prepared = None
        evaluations = {}
        for arm in ARMS:
            cell = inputs["windows"][window][arm]
            record = deepcopy(cell)
            record.update(component=None, design=None, diagnostics=None, verification=None,
                          fit_resources=None, evaluation_resources=None, metrics=None,
                          training_actor_counts=None, evaluation_document=None)
            for field in ("config", "training_cohort", "assessment_cohort", "fit", "evaluation", "failure"):
                if cell[field] is not None:
                    roots.append(str(linked_path(cell[field]).parent))
            config = None if cell["config"] is None else validate_recipe(read_json(linked_path(cell["config"])))
            training, training_audit = (None, None) if cell["training_cohort"] is None else read_cohort(
                cell["training_cohort"], purpose)
            assessment, audit = (None, None) if cell["assessment_cohort"] is None else read_cohort(
                cell["assessment_cohort"], purpose)
            if training is not None:
                validate_population(training, training_audit, window=window, partition=arm)
                coverage[window][arm + "_training"] = training_audit
                training_cohorts[window, arm] = training
            if assessment is not None:
                validate_population(assessment, audit, window=window, partition="assessment")
                if assessment_reference is None:
                    assessment_reference, assessment_cohort, assessment_audit = cell["assessment_cohort"], assessment, audit
                    assessment_prepared = prepare_core(linked_path(selection_reference(assessment)))
                    validate_cohort(assessment, assessment_prepared)
                    validate_outcome_audit(audit, assessment_prepared, assessment)
                    roots.extend(assessment_prepared["input_roots"])
                require(cell["assessment_cohort"] == assessment_reference and assessment == assessment_cohort and
                        audit == assessment_audit, "assessment cohort/order/outcomes changed across arms")
                coverage[window]["assessment"] = audit
            if training is not None and assessment is not None:
                validate_window(window, arm, training, assessment, training_audit, audit)
            if cell["fit"] is None:
                if cell["failure"] is not None:
                    failed_path = linked_path(cell["failure"])
                    if failed_path.suffix == ".json":
                        failed = read_json(failed_path)
                        if failed.get("artifact_kind") == "chance_component_fit":
                            require(training is not None and config is not None and failed["schema_version"] == 3 and
                                    failed["status"] == "failed" and failed["quantity"] == QUANTITY and
                                    failed["protocol_identity"] == protocol and failed["config_identity"] == cell["config"] and
                                    failed["training_cohort_identity"] == cell["training_cohort"] and
                                    failed["diagnostics"]["converged"] is False and
                                    all(failed[field] == training[field] for field in
                                        ("purpose", "selection", "inputs", "preparation_identity")) and
                                    failed["training_game_dates"] == training["game_dates"] and
                                    failed["stage_design"]["families"] == FAMILIES,
                                    "failed native diagnostics/config/source/cohort binding mismatch")
                            require(failed["training_cohort_audit"] == training_audit,
                                    "failed native fit outcome audit changed")
                            record.update(diagnostics=failed["diagnostics"], fit_resources=failed["resources"])
                cells[window][arm] = record
                continue
            completion = read_json(linked_path(cell["fit"]))
            require(set(completion) == {
                "artifact_kind", "schema_version", "purpose", "protocol", "config", "selection",
                "preparation_identity", "training_cohort", "fit", "component", "scientific_assessment",
            } and type(completion["schema_version"]) is int and completion["schema_version"] == 3 and
                completion["artifact_kind"] == "chance_component_fit_completion" and
                completion["purpose"] == purpose and completion["protocol"] == protocol and
                completion["config"] == cell["config"] and completion["training_cohort"] == cell["training_cohort"] and
                completion["selection"] == selection_reference(training) and
                completion["preparation_identity"] == PREPARATION_IDENTITY and
                completion["scientific_assessment"] == "not_performed",
                "successful native fit completion binding mismatch")
            component_reference = completion["component"]
            component = validate_component(read_json(linked_path(component_reference)))
            fit_record = read_json(linked_path(completion["fit"]))
            roots.extend(str(linked_path(completion[field]).parent) for field in ("component", "fit"))
            require(component["purpose"] == purpose and component["quantity"] == QUANTITY and
                    component["config"] == config and component["config_identity"] == cell["config"] and
                    component["protocol_identity"] == protocol and component["extraction"] is None and
                    component["training_cohort"]["definition"] == DEFINITION and
                    component["training_cohort"]["membership_identity"] == cell["training_cohort"] and
                    component["training_cohort"]["excluded_count"] == 0 and
                    all(component[field] == training[field] for field in
                        ("purpose", "selection", "inputs", "preparation_identity")) and
                    component["training_game_dates"] == training["game_dates"] and
                    component["diagnostics"]["converged"] is True,
                    "fresh native component/config/protocol/horizon binding mismatch")
            require(fit_record["schema_version"] == 3 and fit_record["artifact_kind"] == "chance_component_fit" and
                    fit_record["status"] == "fitted" and fit_record["diagnostics"] == component["diagnostics"] and
                    fit_record["training_cohort_identity"] == cell["training_cohort"] and
                    all(fit_record[field] == component[field] for field in (
                        "purpose", "quantity", "config_identity", "protocol_identity", "selection", "inputs",
                        "implementation", "preparation_identity", "training_game_dates")) and
                    fit_record["stage_design"] == component["layout"]["design"] and
                    fit_record["training_cohort_audit"] == training_audit,
                    "native fit diagnostics/design/outcomes differ from completed component")
            require(fitted_implementation is None or fitted_implementation == component["implementation"],
                    "all four cells require one frozen implementation")
            fitted_implementation = component["implementation"]
            require(capacity is not None and capacity["config"] == cell["config"] and
                    capacity["implementation"] == fitted_implementation,
                    "completed fits require the same capacity configuration/implementation")
            if purpose == "research":
                clean_implementation(fitted_implementation)
            receipt, source_roots = verify_component(component, component_reference, training,
                                                     cell["training_cohort"], protocol)
            receipts[window, arm] = receipt
            roots.extend(source_roots)
            design = component["layout"]["design"]
            record.update(component=component_reference,
                          design=dict(sha256=hashlib.sha256(json.dumps(
                              design, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
                                      stage=design["stage"], families=design["families"],
                                      circumstance_columns=design["circumstance_columns"],
                                      slices=design["slices"], coefficient_count=component["layout"]["size"]),
                          diagnostics=component["diagnostics"], fit_resources=fit_record["resources"],
                          training_actor_counts={field: component["layout"][field] for field in
                                                 ("seasons", "shooter_counts", "goalie_counts")})
            if window == "season_transfer" and arm == "expanded" and capacity is not None:
                require(capacity["implementation"] == fitted_implementation and
                        capacity["config"] == cell["config"] and capacity["cohort"] == cell["training_cohort"] and
                        capacity["selection"] == completion["selection"] and capacity["design"] == design,
                        "largest native fit differs from capacity setup identities/design")
            if cell["evaluation"] is not None:
                evaluated = read_json(linked_path(cell["evaluation"]))
                require(set(evaluated) == {
                    "artifact_kind", "schema_version", "purpose", "protocol", "selection", "preparation_identity",
                    "training_cohort", "assessment_cohort", "component", "evaluation", "attempts", "arm",
                    "scientific_assessment",
                } and type(evaluated["schema_version"]) is int and evaluated["schema_version"] == 3 and
                    evaluated["artifact_kind"] == "chance_component_evaluation_completion" and
                    evaluated["purpose"] == purpose and evaluated["protocol"] == protocol and
                    evaluated["selection"] == selection_reference(assessment) and
                    evaluated["preparation_identity"] == PREPARATION_IDENTITY and
                    evaluated["training_cohort"] == cell["training_cohort"] and
                    evaluated["assessment_cohort"] == cell["assessment_cohort"] and
                    evaluated["component"] == component_reference and evaluated["arm"] == arm and
                    evaluated["scientific_assessment"] == "not_performed",
                    "successful native evaluation completion binding mismatch")
                evaluation = validate_evaluation(
                    evaluated["evaluation"], component_reference, selection_reference(assessment),
                    protocol, QUANTITY, purpose, component=component,
                    cohort_reference=cell["assessment_cohort"], arm=arm, prepared=assessment_prepared)
                roots.extend(str(linked_path(evaluated[field]).parent) for field in ("evaluation", "attempts"))
                require(evaluation["implementation"] == fitted_implementation and
                        evaluated["attempts"] == evaluation["attempts"] and
                        evaluation["assessment_cohort_audit"] == audit and
                        all((group["value"] is None and group["metrics"] == evaluation["metrics"]) or
                            (group["value"] is not None and group["recognized_count"] == 0)
                            for group in evaluation["groups"]["sequence_index"]),
                        "evaluation implementation/stream/outcomes or core diagnostic scope changed")
                evaluations[arm] = evaluation
                record.update(evaluation_document=evaluated["evaluation"], metrics=evaluation["metrics"],
                              evaluation_resources=evaluation["resources"])
            cells[window][arm] = record
        comparison = None
        if all(cells[window][arm]["status"] == "complete" for arm in ARMS):
            short_cohort = training_cohorts[window, "short"]
            expanded_cohort = training_cohorts[window, "expanded"]
            short_training = short_cohort["game_dates"]
            expanded_training = expanded_cohort["game_dates"]
            require(set(short_training) < set(expanded_training) and
                    all(expanded_training[gid] == value for gid, value in short_training.items()) and
                    max(value for gid, value in expanded_training.items() if gid not in short_training) <
                    min(short_training.values()), "expanded horizon must add only earlier training games")
            require([member for member in expanded_cohort["rows"] if member["game_id"] in short_training] ==
                    short_cohort["rows"], "expanded training must preserve the entire ordered short cohort")
            before_counts = cells[window]["short"]["training_actor_counts"]
            after_counts = cells[window]["expanded"]["training_actor_counts"]
            for actor in ("shooter", "goalie"):
                before_actors, after_actors = (value[actor + "_counts"] for value in (before_counts, after_counts))
                require(set(before_actors) <= set(after_actors) and
                        all(after_actors[key]["by_season"][season] == counts["by_season"][season]
                            for key, counts in before_actors.items() for season in before_counts["seasons"]) and
                        all(not counts["by_season"][season] for key, counts in after_actors.items()
                            if key not in before_actors for season in before_counts["seasons"]),
                        "expanded actor counts must preserve every shared-year observation")
            short, expanded = evaluations["short"], evaluations["expanded"]
            require(all(short[field] == expanded[field] for field in
                        ("selection", "inputs", "game_dates", "coverage", "cohort", "assessment_cohort_audit")),
                    "paired assessment identities/order/coverage/outcomes changed")
            comparison = compare_pair(short, expanded)
            comparison["paired_groups"] = {name: comparison["paired_groups"][name] for name in REPORT_GROUPS}
            comparison["changed_own_groups"] = {name: comparison["changed_own_groups"][name] for name in REPORT_GROUPS}
            transitions = {actor: {(before, after): dict(short=before, expanded=after, count=0, goals=0)
                                   for before in SUPPORT for after in SUPPORT} for actor in ("shooter", "goalie")}
            for before, after in paired_rows(linked_path(short["attempts"]), linked_path(expanded["attempts"])):
                require(before["season_basis"] == after["season_basis"] and
                        before["state_season"] == after["state_season"],
                        "paired native season/carry-forward states changed")
                if before["study_inclusion"] != "included":
                    continue
                for actor in transitions:
                    old, new = (row["diagnostic_groups"][f"actor_support:{actor}"] for row in (before, after))
                    require(old in SUPPORT and new in SUPPORT and
                            before["actor_evidence"][actor]["basis"] == old and
                            after["actor_evidence"][actor]["basis"] == new,
                            "native actor-support evidence/descriptor disagreement")
                    bucket = transitions[actor][old, new]
                    bucket["count"] += 1
                    bucket["goals"] += before["observed"]
            allowed = {("observed_in_state", "observed_in_state"),
                       ("other_seasons_only", "other_seasons_only"),
                       ("unseen", "other_seasons_only"), ("unseen", "unseen")}
            for values in transitions.values():
                require(all(bucket["count"] == 0 for pair, bucket in values.items() if pair not in allowed) and
                        sum(bucket["count"] for bucket in values.values()) == short["metrics"]["count"] and
                        sum(bucket["goals"] for bucket in values.values()) == short["metrics"]["observed_positive_count"],
                        "support transitions contradict the nested horizons or applicable outcomes")
            delta = comparison["delta"]["log_loss"]["games"]["estimate"]
            arithmetic = independent_loss(linked_path(short["attempts"]), linked_path(expanded["attempts"]), delta)
            require(delta is None or (arithmetic["independent_delta"] > DEADBAND) == (delta > DEADBAND),
                    "independent positive arithmetic-deadband direction disagrees")
            before_metrics, after_metrics = comparison["baseline_metrics"], comparison["changed_metrics"]
            comparison.update(
                baseline="short", changed="expanded", role_mapping=dict(baseline="short", changed="expanded"),
                group_definition="short defines paired actor-support memberships and probability bins; expanded-own support is separate; transitions are descriptive",
                own_arm_calibration=dict(short=short["metrics"]["calibration"], expanded=expanded["metrics"]["calibration"]),
                support_transitions={actor: list(values.values()) for actor, values in transitions.items()},
                arithmetic_verification=arithmetic,
                relative_log_loss_change=delta / before_metrics["log_loss"] if before_metrics["log_loss"] else None,
                change_absolute_pooled_residual_pp=abs(after_metrics["predicted_minus_observed_pp"]) -
                abs(before_metrics["predicted_minus_observed_pp"]) if before_metrics["count"] else None,
            )
        comparisons[window] = comparison
        del assessment_prepared
    if purpose == "research" and fitted_implementation is not None:
        require(implementation() == fitted_implementation, "report/replay must use the frozen fitting implementation")
    distinct = None
    if "expanded_training" in coverage["season_transfer"] and "assessment" in coverage["season_transfer"]:
        training = training_cohorts["season_transfer", "expanded"]
        require(not set(training["game_dates"]) & set(assessment_cohort["game_dates"]),
                "distinct five-season accounting partitions overlap")
        audits = [coverage["season_transfer"][key] for key in ("expanded_training", "assessment")]
        distinct = dict(games=sum(record["games"] for audit in audits for record in audit["per_season"]),
                        per_season=[record for audit in audits for record in audit["per_season"]],
                        **{population: {field: sum(audit[population][field] for audit in audits)
                                       for field in ("attempts", "goals")}
                           for population in ("source_applicable", "included", "omitted")})
        if purpose == "research":
            require(distinct["games"] == 6560 and distinct["included"] == dict(attempts=442073, goals=26566) and
                    sum(record["source_statuses"]["unavailable"] for record in distinct["per_season"]) == 2601,
                    "distinct five-season source/applicable counts do not reconcile")
    direction, recommendation, nominated = decision(comparisons, purpose=purpose)
    output = output_path(args.out, roots)
    output.mkdir()
    for (window, arm), receipt in receipts.items():
        path = output / f"verification-{window}-{arm}.json"
        write_json(path, receipt)
        cells[window][arm]["verification"] = identity(path)
    document = dict(
        schema_version=1, artifact_kind="chance_history_result", purpose=purpose,
        inputs=identity(inputs_path), protocol=protocol, implementation=implementation(), quantity=QUANTITY,
        population="recorded goal probabilities on all source-eligible unblocked 5v5 assessment attempts",
        diagnostic_scope=dict(sequence_index="not_prepared", comparison_groups=list(REPORT_GROUPS)),
        direction=direction, recommendation=recommendation, nominated_horizon=nominated,
        scientific_assessment="not_admitted" if purpose == "research" else "not_performed",
        execution_status="complete" if capacity is not None and all(comparisons[window] is not None for window in WINDOWS) else "incomplete",
        coverage=dict(windows=coverage, distinct_five_seasons=distinct), cells=cells, comparisons=comparisons,
        resampling=RESAMPLING, arithmetic_deadband_nats_per_attempt=DEADBAND, limitations=LIMITATIONS,
        resources=dict(report=resources(started), capacity=deepcopy(inputs["capacity"]),
                       capacity_before_serialization=None if capacity is None else capacity["resources_before_serialization"],
                       capacity_after_exit=measurement, capacity_limit_bytes=CAPACITY_LIMIT_BYTES),
    )
    figure = save_figure(document, output)
    document["figure"] = identity(figure)
    document["resources"]["report"].update(resources(started), figure_bytes=figure.stat().st_size)
    write_json(output / "result.json", document)
    write_json(output / "completion.json", dict(
        schema_version=1, artifact_kind="chance_history_report_completion", purpose=purpose,
        inputs=identity(inputs_path), protocol=protocol, result=identity(output / "result.json"),
        figure=identity(figure), verifications=[cells[window][arm]["verification"]
                                             for window in WINDOWS for arm in ARMS
                                             if cells[window][arm]["verification"] is not None],
        execution_status=document["execution_status"], scientific_assessment=document["scientific_assessment"]))
    print(f"history report written: {output}; {document['execution_status']}; {direction}; {recommendation}")
    return 0


def save_figure(document, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(2, 2, figsize=(13, 8), sharex="col", sharey="col",
                                gridspec_kw=dict(width_ratios=[1, 1.5]))
    colors = dict(short="#555555", expanded="#176b87")
    for row, window in enumerate(WINDOWS):
        loss, calibration = axes[row]
        loss.axvline(0, color="#333333", lw=.8)
        calibration.axhline(0, color="#333333", lw=.8)
        loss.set_title(window.replace("_", " "))
        loss.set_yticks([0, 1, 2], ["whole game", "7-day block", "14-day block"])
        loss.set_xlabel("expanded − short log loss\nnats / eligible unblocked attempt")
        calibration.set_xlim(0, 1)
        calibration.set_xlabel("short probability bin; shared membership")
        calibration.set_ylabel("predicted − observed\npercentage points")
        comparison = document["comparisons"][window]
        if comparison is None:
            for axis in (loss, calibration):
                axis.text(.5, .5, "comparison incomplete", transform=axis.transAxes, ha="center", va="center")
            continue
        for index, unit in enumerate(("games", "calendar_7_day", "calendar_14_day")):
            value = comparison["delta"]["log_loss"][unit]
            if value["estimate"] is not None:
                loss.plot(value["estimate"], index, "o", color=colors["expanded"], ms=5)
            if value["interval"] is not None:
                loss.hlines(index, *value["interval"], color=colors["expanded"], lw=1.3)
            else:
                loss.annotate("interval undefined", (value["estimate"] or 0, index),
                              xytext=(6, 8 if index < 2 else -14), textcoords="offset points", fontsize=7)
        bins = comparison["paired_calibration"]
        xs = [(bucket["lower"] + bucket["upper"]) / 2 for bucket in bins]
        for arm, key in (("short", "baseline"), ("expanded", "changed")):
            residuals = [bucket[key]["predicted_minus_observed_pp"] if bucket[key]["count"] else np.nan
                         for bucket in bins]
            calibration.plot(xs, residuals, "o-", color=colors[arm], ms=3, lw=.8, label=arm)
        for x, bucket in zip(xs, bins, strict=True):
            if bucket["baseline"]["count"]:
                calibration.annotate(f"n={bucket['baseline']['count']:,}",
                                     (x, bucket["baseline"]["predicted_minus_observed_pp"]),
                                     xytext=(0, 8), textcoords="offset points", fontsize=6, rotation=60)
        metric = comparison["baseline_metrics"]
        calibration.set_title(f"short-defined bins; n={metric['count']:,}; goals={metric['observed_positive_count']:,}", fontsize=9)
        calibration.margins(y=.25)
        calibration.legend(fontsize=8)
    caption = (
        "recorded goal conversion on all source-eligible unblocked 5v5 attempts; negative loss delta favors expanded.\n"
        "95% intervals condition on four fitted models; 2,000 paired pooled game/7-day/14-day draws per window; no bootstrap fits.\n"
        "short defines paired bins and support groups; own-arm bins and descriptive support transitions remain separate machine tables.\n"
        "longer native history changes seasonal reference, actor support/borrowing and effective regularization; it does not isolate sample size."
    )
    if document["purpose"] == "fixture_exercise":
        caption = "fixture software exercise; scientific assessment not performed.\n" + caption
    figure.tight_layout(rect=(0, .14, 1, 1), h_pad=3)
    figure.text(.025, .015, caption, fontsize=8, va="bottom")
    path = output / "history.png"
    figure.savefig(path, dpi=180)
    plt.close(figure)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    options = {
        "cohort": ("selection", "protocol", "out"),
        "capacity": ("selection", "cohort", "config", "protocol", "out"),
        "fit": ("selection", "cohort", "config", "protocol", "window", "arm", "out"),
        "evaluate": ("selection", "cohort", "component", "protocol", "window", "arm", "out"),
        "report": ("inputs", "protocol", "out"),
    }
    for name, required in options.items():
        child = commands.add_parser(name, allow_abbrev=False)
        for option in required:
            choices = WINDOWS if option == "window" else ARMS if option == "arm" else None
            child.add_argument(f"--{option}", required=True, action=Once, choices=choices)
    args = parser.parse_args()
    try:
        return {"cohort": cohort_command, "capacity": capacity_command, "fit": fit_command,
                "evaluate": evaluate_command, "report": report_command}[args.command](args)
    except (InputContractError, OSError, KeyError, TypeError, ValueError, OverflowError, IndexError) as error:
        print(f"history {args.command} failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
