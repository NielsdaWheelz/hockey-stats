"""04c's bound diagnosis, fixed truths, staged recovery and scoped decisions."""

import argparse
from collections import Counter, defaultdict
import math
import os
from pathlib import Path
import sys
import time

for _thread_variable in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_thread_variable] = "1"

import numpy as np

from hockey_stats.artifacts import (
    clean_implementation, implementation, json_values, linked_path, require, resources,
    write_json, write_arrays, load_arrays, artifact, read_artifact, ordered_array_digest,
)
from hockey_stats.attribution_simulation import synthetic_counts
from hockey_stats.chance_cli import identity, output_path, read_json
from hockey_stats.chance_evaluation import REGION_NAMES, compound_regions
from hockey_stats.shot_origins import grid

SEASONS = tuple(f"{year}{year + 1}" for year in range(2021, 2026))
CASES = ("gaussian", "game_pace")
RESEARCH_ROOT = Path("/Volumes/Expansion/hockey-stats/runs")
SPEC = Path(__file__).resolve().parents[2] / "docs/specs/04c-attribution-recovery.md"
BASELINE_DIGESTS = {
    "prepared": "fbc40ab798493be6fcc7068ea52eb43831ad725fb89d7a4c87242f689cb7d17b",
    "fits": "356fe332cd0c8d3786140db41c99e739ba4a807c519ddb7c1ab6a876a7a580fc",
    "simulation": "6075a4de7ca5449a2e66e2b7b6bd7caca7d81e6c4dedc29a12d328f627250863",
    "assessment": "a2a3347f29d1c0cde218e4ddec2175946f45c71a4a7306d7b441966d48d6319b",
}
FIGURE_CONTRACTS = {
    "diagnosis": {
        "maps": "actual shape truth, outer-mean fitted shape and bias on one shared scale; attempts/60 team minutes",
        "accounting": "native volume, shape and signed cross-term squared-error contributions; same fitted volume-only comparator",
        "mechanism": "twelve-region squared bias versus sampling variation, all saved outer datasets; point versus weighted scale/interval behavior",
    },
    "recovery": {
        "means": "eight paired broad-shape error comparisons with denominators and monte carlo intervals",
        "intervals": "four primary coverage cells; nominal .95 distinct from developmental .90 floor; transition/null/stress limits visible",
        "early_stop": "unreached claims labeled not_run with the exact stopping reason; no fabricated candidate maps",
    },
    "representation_limits": {
        "maps": "actual truth, geometric projection and fitted broad/local/rough shapes; gaussian outer zero, year five; shared scales",
        "real": "only conditional fixed real examples; research point associations, no real refit intervals",
    },
}
PROTOCOL_RULES = dict(
    seasons=list(SEASONS), populations=["unblocked_spatial"],
    basis_rule=dict(name="graph_40ft", spacing_feet=5, cutoff=(2 * np.pi / 40) ** 2, rank=40,
                    geometry="cardinal adjacency, one constant mode excluded", response_selection=False),
    seeds=dict(design=40400, response=40430, refit=40431, paired_error=40432, bit_generator="PCG64"),
    generator=dict(design="unchanged paired after mixed", games=96, stints=50, cases=list(CASES), annual_rate=40,
                   truth="fixed 04c spec table, separately exposure centered"),
    criteria=dict(mean="all_eight_paired_error_95_percentile_lower_gt_zero", coverage="all_four_95_wilson_lower_ge_0.90",
                  nominal_coverage=.95, developmental_floor=.90, numerical_tolerance=1e-8, resolution_movement_max=1e-4),
    interval=dict(kind="basic_game_refit", quantile="linear", no_working_variance=True),
    admission="not_admitted", handoff=None,
)
RESEARCH_BUDGETS = dict(outer_per_case=400, inner_refits=200, paired_error_resamples=10000, workers=4)


def validate_protocol(document: dict) -> None:
    require(set(document) == {"schema_version", "kind", "purpose", "implementation", "consumed", "diagnosis",
        "spec_snapshot", "source_prepared", "source_protocol", "old_evidence", "output_root", "budgets",
        "grid", "reference", "request_sha256", "synthetic_design_sha256", *PROTOCOL_RULES},
        "frozen model protocol fields differ")
    require(all(document[name] == expected for name, expected in PROTOCOL_RULES.items()),
            "frozen model protocol scientific rules differ")
    budgets = document["budgets"]
    require(isinstance(budgets, dict) and set(budgets) == set(RESEARCH_BUDGETS)
            and all(type(budgets[name]) is int and 0 < budgets[name] <= expected
                    for name, expected in RESEARCH_BUDGETS.items()), "invalid explicit stage budgets")
    if document["purpose"] == "research":
        require(budgets == RESEARCH_BUDGETS, "research stage budgets changed")
        require(Path(document["output_root"]).is_absolute()
                and Path(document["output_root"]).is_relative_to(RESEARCH_ROOT), "research output root changed")
    diagnosed = read_artifact(linked_path(document["diagnosis"]), "attribution_recovery_diagnosis")
    require(document["purpose"] == diagnosed["purpose"] and diagnosed["status"] == "complete"
            and diagnosed["gate"]["status"] == "proceed" and document["source_prepared"] == diagnosed["source_prepared"]
            and document["old_evidence"] == diagnosed["old_evidence"] and document["spec_snapshot"] == diagnosed["spec_snapshot"],
            "frozen protocol changed the diagnosis or its source evidence")
    source = read_json(linked_path(document["source_prepared"]))
    reference = next(row["references"] for row in source["annual"]
                     if row["population"] == "unblocked_spatial" and row["season"] == SEASONS[0])
    require(document["grid"] == source["grid"] and document["reference"] == reference,
            "frozen geometry or original reference identity changed")
    linked_path(reference)


def shape_regions() -> tuple[np.ndarray, tuple[str, ...]]:
    centers = grid()[0]
    regions = compound_regions(centers)
    W = np.zeros((len(centers), 12))
    for region in range(6):
        member = regions == region
        W[:, 2 * region] = member * np.where(centers[:, 1] < 0, 1., np.where(centers[:, 1] == 0, .5, 0.))
        W[:, 2 * region + 1] = member * np.where(centers[:, 1] > 0, 1., np.where(centers[:, 1] == 0, .5, 0.))
    require(W.shape == (656, 12) and np.array_equal(W.sum(axis=1), np.ones(656)),
            "twelve shape regions must partition the original grid")
    names = tuple(f"{region}_{side}" for region in REGION_NAMES for side in ("negative_y", "positive_y"))
    return W, names


def error_decomposition(estimated_volume: float, estimated_shape: np.ndarray,
                        true_volume: float, true_shape: np.ndarray, p: np.ndarray) -> dict:
    """inputs are already in attempts/60; shape's zero sum does not remove the cross term."""
    delta_t = estimated_volume - true_volume
    delta_h = estimated_shape - true_shape
    complete_error = delta_t * p + delta_h
    volume = float(delta_t ** 2 * (p @ p))
    shape = float(delta_h @ delta_h)
    cross = float(2 * delta_t * (p @ delta_h))
    total = float(complete_error @ complete_error)
    residual = abs(total - volume - shape - cross)
    require(residual <= 1e-8 * (1 + abs(total) + abs(volume) + abs(shape) + abs(cross)),
            "native squared-error decomposition does not reconcile")
    volume_only_error = estimated_volume * p - (true_volume * p + true_shape)
    return dict(complete_native_squared_error=total, volume_native_squared_error=volume,
                shape_native_squared_error=shape, cross_term=cross,
                same_fitted_volume_only_native_squared_error=float(volume_only_error @ volume_only_error),
                pure_volume_squared_error=float(delta_t ** 2), decomposition_absolute_residual=residual)


def shape_recovery(estimates: np.ndarray, truth: np.ndarray) -> dict:
    require(estimates.ndim == 2 and estimates.shape[0] > 0 and estimates.shape[1:] == truth.shape
            and np.isfinite(estimates).all() and np.isfinite(truth).all(), "invalid shape recovery population")
    mean = estimates.mean(axis=0)
    bias = mean - truth
    bias2 = float(bias @ bias)
    variation = float(np.mean(np.sum((estimates - mean) ** 2, axis=1)))
    mse = float(np.mean(np.sum((estimates - truth) ** 2, axis=1)))
    residual = abs(mse - bias2 - variation)
    require(residual <= 1e-8 * (1 + mse), "bias plus variation does not equal mean squared error")
    energy = float(truth @ truth)
    return dict(n=len(estimates), bias_squared=bias2, sampling_variation=variation,
                mean_squared_error=mse, decomposition_absolute_residual=residual, truth_energy=energy,
                normalized_mean_squared_error=mse / energy if energy > 0 else None,
                normalized_unavailable_reason=None if energy > 0 else "zero_truth_energy",
                mean_pattern_attenuation=float(mean @ truth) / energy if energy > 0 else None,
                bias_dominates_variation=bias2 > variation)


def _old_arrays(reference: dict, shapes: dict) -> dict:
    with np.load(linked_path(reference), allow_pickle=False) as arrays:
        require(set(arrays.files) == set(shapes), "saved 04b array names differ")
        values = {name: arrays[name] for name in arrays.files}
    require(all(list(value.shape) == shapes[name] and value.dtype.kind in "biuf" and np.isfinite(value).all()
                for name, value in values.items()), "saved 04b arrays are nonfinite or incorrectly shaped")
    return values


def _old_document(reference: dict, kind: str, purpose: str) -> dict:
    document = read_json(linked_path(reference))
    require(type(document.get("schema_version")) is int and document["schema_version"] == 2
            and document.get("kind") == kind and document.get("purpose") == purpose,
            "incorrect saved 04b artifact: " + kind)
    if purpose == "research":
        clean_implementation(document["implementation"])
    return document


def _close(actual, expected, message: str) -> float:
    actual, expected = np.asarray(actual), np.asarray(expected)
    require(actual.shape == expected.shape and np.isfinite(actual).all() and np.isfinite(expected).all(), message)
    residual = float(np.max(np.abs(actual - expected))) if actual.size else 0.
    scale = 1 + float(np.max(np.abs(expected))) if expected.size else 1.
    require(residual <= 1e-8 * scale, message)
    return residual


def _scale_receipt(block: dict) -> dict:
    scale = block["scale"]
    return dict(entry_variance=block["a"], innovation_variance=block["q"], status=scale["status"],
                selected=scale["selected"], own_reasons=scale["own_reasons"],
                inherited_limitation=scale["inherited_limitation"])


def diagnose(baseline_result: Path | str, out: Path | str) -> dict:
    """reconcile immutable 04b states before choosing whether 04c's mechanism is supported."""
    from hockey_stats.attribution import project_interval, read_native_04b_embedded_annual
    from hockey_stats.attribution_uncertainty import basic_interval

    started, process_started = time.monotonic(), time.process_time()
    result_path = Path(baseline_result).resolve(strict=True)
    result = read_json(result_path)
    purpose = result.get("purpose")
    require(result.get("schema_version") == 2 and result.get("kind") == "attribution_revision_result"
            and purpose in ("research", "fixture_exercise") and result.get("completion") == "complete",
            "diagnosis needs the completed saved 04b result")
    producer = implementation()
    if purpose == "research":
        clean_implementation(producer)
        clean_implementation(result["implementation"])
        clean_implementation(result["model_implementation"])
    evidence = {name: result["evidence"][name] for name in BASELINE_DIGESTS}
    if purpose == "research":
        require(all(evidence[name]["sha256"] == digest for name, digest in BASELINE_DIGESTS.items()),
                "diagnosis differs from the exact 04b evidence selected by the specification")
    prepared, fits, simulation, assessment = [
        _old_document(evidence[name], kind, purpose) for name, kind in (
            ("prepared", "attribution_revision_prepared"), ("fits", "attribution_revision_fits"),
            ("simulation", "attribution_revision_recovery"), ("assessment", "attribution_revision_assessment"))]
    protocol_ref = result["protocol"]
    protocol = _old_document(protocol_ref, "attribution_revision_protocol", purpose)
    require(all(document["protocol"] == protocol_ref for document in (prepared, fits, simulation, assessment))
            and fits["prepared"] == simulation["prepared"] == assessment["prepared"] == evidence["prepared"]
            and assessment["fits"] == evidence["fits"] and assessment["simulation"] == evidence["simulation"]
            and fits["status"] == simulation["status"] == assessment["status"] == "complete",
            "saved 04b evidence chain differs or is incomplete")
    require(list(SEASONS) == prepared["seasons"] == fits["seasons"] == protocol["seasons"]
            and prepared["population_ids"] == fits["population_ids"] == assessment["source_population_ids"],
            "saved seasons or source population identities changed")
    require(fits["implementation"] == simulation["implementation"] == result["model_implementation"]
            and assessment["implementation"] == result["implementation"], "saved model/reporting producer identities differ")
    if purpose == "research":
        require(sum(prepared["games_by_season"].values()) == 6560, "saved inventory must retain all 6,560 games")
    expected_annual = [(population, season) for population in ("all_attempts", "unblocked_spatial") for season in SEASONS]
    require([(row["population"], row["season"]) for row in prepared["annual"]] == expected_annual
            and [(row["benchmark"], row["season"]) for row in fits["annual"]] == expected_annual,
            "saved annual population order differs")
    source_refs, real_annual_refs, real_references = [], [], {}
    for source_row, fit_row in zip(prepared["annual"], fits["annual"], strict=True):
        key = (source_row["population"], source_row["season"])
        require(len(source_row["game_ids"]) == prepared["games_by_season"][key[1]]
                and source_row["game_ids"] == sorted(set(source_row["game_ids"])), "saved annual game inventory differs")
        reference_arrays = _old_arrays(source_row["references"], source_row["reference_shapes"])
        for name in ("rows", "arrays", "grouped", "statistics"):
            linked_path(source_row[name])
        real_references[key] = reference_arrays
        source_refs.append(dict(population=key[0], season=key[1], references=source_row["references"],
                                rows=source_row["rows"], game_ids=source_row["game_ids"], r=source_row["r"]))
        annual = _old_document(fit_row["state"], "attribution_revision_annual", purpose)
        require(annual["prepared"] == evidence["prepared"] and annual["protocol"] == protocol_ref
                and annual["control"] == fit_row["control"] and annual["population_id"] == prepared["population_ids"][key[0]]
                and annual["season"] == key[1] and annual["benchmark"] == key[0], "saved real annual identity differs")
        # Original arrays are bound and retained; no reinterpretation or real refit is needed for this diagnosis.
        linked_path(annual["arrays"])
        control = read_json(linked_path(fit_row["control"]))
        require(control.get("schema_version") == 1 and control["benchmark"] == key[0]
                and control["season"] == key[1], "saved corrected 04a control differs")
        linked_path(control["arrays"])
        real_annual_refs.append(dict(population=key[0], season=key[1], state=fit_row["state"], control=fit_row["control"]))
    generator = _old_document(simulation["generator"], "attribution_revision_synthetic_design", purpose)
    require(generator["protocol"] == protocol_ref and generator["prepared"] == evidence["prepared"],
            "saved synthetic design differs from selected evidence")
    design = _old_arrays(generator["arrays"], generator["shapes"])
    p = design["p"]
    require(p.shape == (656,) and np.all(p > 0) and abs(float(p.sum()) - 1) <= 1e-12
            and np.array_equal(design["centers"], grid()[0])
            and np.array_equal(p, real_references[("unblocked_spatial", SEASONS[0])]["p"]),
            "original native geometry/reference changed")
    for season in SEASONS:
        require(np.array_equal(p, real_references[("unblocked_spatial", season)]["p"]),
                "original annual native reference changed")
    W, region_names = shape_regions()
    expected_outer = protocol["budgets"]["outer_per_case"]
    inner = protocol["budgets"]["inner_refits"]
    require(simulation["expected_outer_per_case"] == expected_outer and simulation["inner_refits"] == inner
            and (purpose == "fixture_exercise" or expected_outer == inner == 200), "saved recovery budget changed")
    expected_ids = {(case, outer) for case in range(2) for outer in range(expected_outer)}
    completed = [tuple(row) for row in simulation["completed_outer_ids"]]
    require(len(completed) == len(set(completed)) and set(completed) == expected_ids
            and not simulation["error_outer_ids"] and len(simulation["outer"]) == len(expected_ids),
            "saved recovery denominator is incomplete or duplicated")
    truth, truth_volumes = {}, {}
    for year in range(5):
        scalar, shape, maps = [design[f"year_{year}_truth_{name}"] for name in ("scalar", "shape", "map")]
        _close(shape.sum(axis=1), np.zeros(len(shape)), "saved generating shape is not zero sum")
        _close(maps, scalar[:, None] * p + shape, "saved generating map does not reconcile")
        players = generator["years"][year]["players"]
        for name, pair in (("broad", (3, 4)), ("local", (18, 19))):
            left, right = players.index(pair[0]), players.index(pair[1])
            truth[(name, year + 1)] = 40 * (shape[left] - shape[right])
            truth_volumes[(name, year + 1)] = 40 * float(scalar[left] - scalar[right])
    summaries, decompositions, intervals, scales, reconciled = [], [], [], [], []
    shape_intervals = []
    weighted_variances = defaultdict(list)
    weighted_statuses = Counter()
    estimated_shapes = {(case, name, year): [] for case in CASES for name in ("broad", "local") for year in (1, 5)}
    seen, residuals = set(), []
    for outer_ref in simulation["outer"]:
        outer = _old_document(outer_ref, "attribution_revision_outer_recovery", purpose)
        case, outer_id = outer["case"], outer["outer_id"]
        key = (CASES.index(case), outer_id)
        require(key in expected_ids and key not in seen and outer["status"] == "complete" and outer["error"] is None
                and outer["protocol"] == protocol_ref and outer["prepared"] == evidence["prepared"]
                and outer["design"] == simulation["generator"] and outer["implementation"] == simulation["implementation"]
                and outer["response_seeds"] == [[40420, key[0], outer_id, year] for year in range(5)],
                "saved outer identity, seed or completion changed")
        seen.add(key)
        require(outer["inner_completed_ids"] == list(range(inner)) and not outer["inner_error_ids"]
                and [row["draw_id"] for row in outer["inner_diagnostics"]] == list(range(inner))
                and all(row["status"] == "complete" and row["error"] is None for row in outer["inner_diagnostics"]),
                "saved weighted refit denominator differs")
        arrays = _old_arrays(outer["arrays"], outer["shapes"])
        states = {}
        for estimator in ("revision", "control"):
            rows = outer["annual"][estimator]
            require([(row["benchmark"], row["season"]) for row in rows] == expected_annual,
                    "saved outer annual order differs")
            for row in rows:
                population, season = row["benchmark"], row["season"]
                year = SEASONS.index(season)
                ids, current = row["player_ids"], row["current_player_ids"]
                prior_ids = [] if year == 0 else states[(estimator, population, SEASONS[year - 1])]["player_ids"]
                require(ids == sorted(set(ids)) and current == generator["years"][year]["players"]
                        and set(ids) == set(current) | set(prior_ids)
                        and row["entrant_ids"] == sorted(set(current) - set(prior_ids))
                        and row["carried_only_ids"] == sorted(set(ids) - set(current))
                        and row["r"] == (55. if population == "all_attempts" else 40.), "saved point-state identity changed")
                prefix = f"{estimator}_{population}_{season}"
                expected_u = np.zeros(len(ids))
                expected_u[[ids.index(player) for player in current]] = design[f"year_{year}_u"]
                require(np.array_equal(arrays[prefix + "_u"], expected_u), "saved outer annual exposure reference changed")
                if population == "unblocked_spatial":
                    require(np.array_equal(arrays[prefix + "_p"], p), "saved outer native shares changed")
                for block_name in ("volume", "shape"):
                    block = row[block_name]
                    if block is None:
                        require(population == "all_attempts" and block_name == "shape", "missing saved point block")
                        continue
                    block_prefix = block["array_prefix"]
                    width = 1 if block_name == "volume" else 656
                    require(arrays[block_prefix + "_M"].shape == (2 * len(ids), width)
                            and arrays[block_prefix + "_V"].shape == (2 * len(ids), 2 * len(ids))
                            and arrays[block_prefix + "_prior_mean"].shape == (2 * len(ids), width)
                            and arrays[block_prefix + "_prior_covariance"].shape == (2 * len(ids), 2 * len(ids))
                            and arrays[block_prefix + "_A"].shape == (len(generator["years"][year]["strata"]), width),
                            "saved block dimensions differ")
                    covariance = arrays[block_prefix + "_V"]
                    residuals.append(_close(covariance, covariance.T, "saved covariance is asymmetric"))
                    require(block["scale"]["selected"]["variance"] == (block["a"] if year == 0 else block["q"]),
                            "saved selected variance does not match the annual scale")
                    if block_name == "shape":
                        residuals.append(_close(arrays[block_prefix + "_M"].sum(axis=1), np.zeros(2 * len(ids)),
                                                 "saved shape is not zero sum"))
                    for numerical in ("equation_relative_residual", "original_mean_equation_relative_residual",
                                      "original_covariance_equation_relative_residual"):
                        require(0 <= block["diagnostics"][numerical] <= 1e-8, "saved equation check failed")
                    if estimator == "revision" and population == "unblocked_spatial":
                        scales.append(dict(case=case, outer=outer_id, year=year + 1, block=block_name,
                                           **_scale_receipt(block)))
                states[(estimator, population, season)] = row
        for year, season in enumerate(SEASONS):
            current = generator["years"][year]["players"]
            n = len(current)
            point_maps = {}
            for estimator in ("revision", "control"):
                row = states[(estimator, "unblocked_spatial", season)]
                ids = row["player_ids"]
                indices = [ids.index(player) + offset * len(ids) for offset in (0, 1) for player in current]
                volume = arrays[row["volume"]["array_prefix"] + "_M"][indices, 0]
                shape = arrays[row["shape"]["array_prefix"] + "_M"][indices]
                maps = volume[:, None] * p + shape
                point_maps[estimator] = maps
                errors = maps - design[f"year_{year}_truth_map"]
                saved_name = f"all_player_{'control_' if estimator == 'control' else ''}bias_{season}"
                residuals.append(_close(arrays[saved_name], errors, "saved all-player map errors differ"))
                for population, rate in (("all_attempts", 55.), ("unblocked_spatial", 40.)):
                    scalar_row = states[(estimator, population, season)]
                    scalar_ids = scalar_row["player_ids"]
                    scalar_indices = [scalar_ids.index(player) + offset * len(scalar_ids) for offset in (0, 1) for player in current]
                    scalar_error = rate * (arrays[scalar_row["volume"]["array_prefix"] + "_M"][scalar_indices, 0]
                                           - design[f"year_{year}_truth_scalar"])
                    scalar_name = f"all_player_scalar_{population}_{season}_{'control_' if estimator == 'control' else ''}error"
                    residuals.append(_close(arrays[scalar_name], scalar_error, "saved all-player scalar errors differ"))
            all_metric = [row for row in outer["map_metrics"] if row["year"] == year + 1 and row["contrast"] == "all_current_players"]
            require(len(all_metric) == 1, "saved all-player metric missing or duplicated")
            for estimator in ("revision", "control"):
                value = float(1600 * np.sum((point_maps[estimator] - design[f"year_{year}_truth_map"]) ** 2) / (2 * n))
                residuals.append(_close(value, all_metric[0][estimator], "saved all-player metric differs"))
                residuals.append(_close(value / 1600, all_metric[0][estimator + "_relative"],
                                         "saved all-player relative metric differs"))
            if year not in (0, 4):
                continue
            for name, pair in (("broad", (3, 4)), ("local", (18, 19))):
                left, right = current.index(pair[0]), current.index(pair[1])
                metrics = [row for row in outer["map_metrics"] if row["year"] == year + 1 and row["contrast"] == name]
                require(len(metrics) == 1, "saved fixed contrast metric missing or duplicated")
                truth_map = truth_volumes[(name, year + 1)] * p + truth[(name, year + 1)]
                residuals.append(_close(arrays[f"{name}_{year + 1}_truth"], truth_map, "saved contrast truth unit differs"))
                truth_energy = float(truth_map @ truth_map)
                residuals.append(_close(truth_energy, metrics[0]["truth_energy"], "saved contrast truth energy differs"))
                residuals.append(_close(metrics[0]["control"] - metrics[0]["revision"], metrics[0]["paired_reduction"],
                                         "saved paired error reduction differs"))
                for estimator in ("revision", "control"):
                    complete_map = 40 * (point_maps[estimator][left] - point_maps[estimator][right])
                    residuals.append(_close(arrays[f"{name}_{year + 1}_{estimator}"], complete_map,
                                             "saved contrast fitted-map unit differs"))
                    row = states[(estimator, "unblocked_spatial", season)]
                    ids = row["player_ids"]
                    i, j = ids.index(pair[0]), ids.index(pair[1])
                    volume_M = arrays[row["volume"]["array_prefix"] + "_M"]
                    shape_M = arrays[row["shape"]["array_prefix"] + "_M"]
                    estimated_volume = float(40 * (volume_M[i, 0] - volume_M[j, 0]))
                    estimated_shape = 40 * (shape_M[i] - shape_M[j])
                    decomposition = error_decomposition(estimated_volume, estimated_shape,
                        truth_volumes[(name, year + 1)], truth[(name, year + 1)], p)
                    residuals.append(_close(decomposition["complete_native_squared_error"], metrics[0][estimator],
                                             "saved contrast metric does not reconcile"))
                    residuals.append(_close(decomposition["pure_volume_squared_error"], metrics[0][estimator + "_pure_volume_error"],
                                             "saved pure-volume metric does not reconcile"))
                    residuals.append(_close(decomposition["complete_native_squared_error"] / 1600,
                        metrics[0][estimator + "_relative"], "saved contrast relative error differs"))
                    require(truth_energy > 0, "saved nonzero contrast unexpectedly has zero truth energy")
                    residuals.append(_close(decomposition["complete_native_squared_error"] / truth_energy,
                        metrics[0][estimator + "_normalized"], "saved contrast normalized error differs"))
                    decompositions.append(dict(case=case, outer=outer_id, year=year + 1, contrast=name,
                                               estimator=estimator, **decomposition))
                    if estimator == "revision":
                        estimated_shapes[(case, name, year + 1)].append(estimated_shape)
                        residuals.append(_close(arrays[f"{name}_{year + 1}_error"], complete_map - truth_map,
                                                 "saved fixed contrast error array differs"))
                cell_rows = [row for row in outer["cells"] if row["benchmark"] == "unblocked_spatial"
                             and row["year"] == year + 1 and row["contrast"] == name]
                require(len(cell_rows) == 7, "saved fixed contrast interval cells differ")
                intervals.extend(dict(case=case, outer=outer_id, year=year + 1, contrast=name,
                                      functional=row["functional"], estimand="complete_rate", truth=row["truth"],
                                      mean=row["mean"], working=row["working"], refit=row["refit"])
                                 for row in cell_rows)
                native_requests = [row for row in outer["inner_projections"]
                    if row["request"]["name"] == name and row["request"]["season"] == season
                    and row["request"]["benchmark"] == "unblocked_spatial"
                    and row["request"]["functional"] == "native"]
                require(len(native_requests) == 1, "saved joint native refit request missing or duplicated")
                native_request = native_requests[0]
                require(native_request["request"]["coefficients"] == [[pair[0], 1], [pair[1], -1]]
                        and native_request["request"]["role"] == "offense"
                        and np.array_equal(arrays[native_request["draw_ids"]], np.arange(inner)),
                        "saved joint native refit request or draw order changed")
                joint_draws = arrays[native_request["array"]]
                require(joint_draws.shape == (inner, 656), "saved joint native refit draw dimensions differ")
                shape_draws = joint_draws - joint_draws.sum(axis=1, keepdims=True) * p
                point = read_native_04b_embedded_annual(states[("revision", "unblocked_spatial", season)], arrays,
                    source_protocol_sha256=protocol_ref["sha256"], model_protocol_sha256=protocol_ref["sha256"],
                    population_id=f"synthetic:04b:{key[0]}:{outer_id}:unblocked_spatial", season_index=year)
                c = np.zeros(2 * len(point.player_ids))
                c[point.player_ids.index(pair[0])], c[point.player_ids.index(pair[1])] = 1, -1
                native_truth = truth[(name, year + 1)]
                peak = int(np.argmax(np.abs(native_truth)))
                functionals = [(region_names[index], vector) for index, vector in enumerate(W.T)]
                functionals.append((f"max_true_shape_cell_{peak}", np.eye(1, 656, peak).ravel()))
                for functional, vector in functionals:
                    vector = vector - p @ vector
                    working = project_interval(point, c, vector, estimand="shape")
                    projected_draws = shape_draws @ vector
                    refit = basic_interval(working["mean"], projected_draws)
                    shape_intervals.append(dict(case=case, outer=outer_id, year=year + 1, contrast=name,
                        functional=functional, estimand="shape", truth=float(native_truth @ vector),
                        mean=working["mean"], working=working, refit=refit,
                        joint_draws=inner, units="attempts/60 team minutes"))
        for draw in outer["inner_diagnostics"]:
            require(draw["seeds"] == [dict(season=season, seed=[40421, key[0], outer_id, draw["draw_id"], year])
                                      for year, season in enumerate(SEASONS)], "saved weighted-search seeds differ")
            require([(row["benchmark"], row["season"]) for row in draw["annual"]] ==
                    [(population, season) for season in SEASONS for population in ("all_attempts", "unblocked_spatial")]
                    and all(row["status"] == "complete" for row in draw["annual"]),
                    "saved weighted annual-state denominator differs")
            for row in draw["annual"]:
                if row["benchmark"] == "unblocked_spatial":
                    for block in ("volume", "shape"):
                        value = row[block]
                        year = SEASONS.index(row["season"]) + 1
                        weighted_variances[(case, year, block)].append(value["selected"]["variance"])
                        weighted_statuses[(case, year, block, value["status"],
                                           bool(value["inherited_limitation"]), tuple(value["own_reasons"]))] += 1
        reconciled.append(dict(case=case, outer=outer_id, manifest=outer_ref, arrays=outer["arrays"],
                               annual_states=20, inner_histories=inner, status="complete"))
    require(seen == expected_ids, "saved recovery outer denominator changed")
    arrays = dict(p=p, W=W)
    for (case, name, year), values in estimated_shapes.items():
        estimates = np.stack(values)
        native_truth = truth[(name, year)]
        regional_truth = native_truth @ W
        regional = estimates @ W
        summaries.append(dict(case=case, contrast=name, year=year, estimand="shape",
                              units="squared attempts/60 team minutes", regions=shape_recovery(regional, regional_truth),
                              native=shape_recovery(estimates, native_truth)))
        prefix = f"{case}_{name}_{year}"
        arrays.update({prefix + "_truth": native_truth, prefix + "_estimated_shapes": estimates,
                       prefix + "_mean_shape": estimates.mean(axis=0), prefix + "_bias": estimates.mean(axis=0) - native_truth})
    gate_rows = [row for row in summaries if row["contrast"] == "broad" and row["year"] == 5]
    proceed = all(row["regions"]["bias_dominates_variation"] for row in gate_rows)
    require(len(gate_rows) == 2, "diagnosis gate is missing a noise case")
    output = output_path(str(out), [str(result_path.parent)] + [str(linked_path(ref).parent) for ref in evidence.values()])
    if purpose == "research":
        require(output.is_relative_to(RESEARCH_ROOT), "research diagnosis must remain external-only")
    output.mkdir()
    spec_path = output / "spec-snapshot.md"
    with spec_path.open("xb") as destination:
        destination.write(SPEC.read_bytes())
    scale_counts = Counter((row["case"], "point", row["block"], row["status"],
                            bool(row["inherited_limitation"])) for row in scales)
    weighted_summary = [dict(case=case, year=year, block=block, n=len(values),
        scale_kind="entry" if year == 1 else "innovation",
        selected_variance_quantiles=dict(zip(("minimum", "q025", "median", "q975", "maximum"),
                                            np.quantile(values, [0, .025, .5, .975, 1], method="linear"), strict=True)))
        for (case, year, block), values in sorted(weighted_variances.items())]
    interval_summaries = {"complete_rate": [], "shape": []}
    for estimand, rows in (("complete_rate", intervals), ("shape", shape_intervals)):
        for case in CASES:
            for year in (1, 5):
                for name in ("broad", "local"):
                    selected = [row for row in rows if row["case"] == case
                                and row["year"] == year and row["contrast"] == name]
                    for functional in sorted({row["functional"] for row in selected}):
                        cell = [row for row in selected if row["functional"] == functional]
                        require(len(cell) == expected_outer, "saved interval denominator differs")
                        entry = dict(case=case, year=year, contrast=name, functional=functional,
                                     estimand=estimand, n=expected_outer, units="attempts/60 team minutes")
                        for kind in ("working", "refit"):
                            require(all(row[kind] is not None for row in cell), "saved fixed interval missing")
                            entry[kind] = dict(
                                mean_width=float(np.mean([row[kind]["upper"] - row[kind]["lower"] for row in cell])),
                                mean_center_minus_truth=float(np.mean([(row[kind]["upper"] + row[kind]["lower"]) / 2
                                                                      - row["truth"] for row in cell])),
                                covered=sum(row[kind]["lower"] <= row["truth"] <= row[kind]["upper"] for row in cell))
                        interval_summaries[estimand].append(entry)
    consumed = dict(baseline_result=identity(result_path), spec_snapshot=identity(spec_path),
                    **evidence, baseline_protocol=protocol_ref, baseline_generator=simulation["generator"])
    document = artifact("attribution_recovery_diagnosis", purpose, consumed,
        spec_snapshot=identity(spec_path), model_protocol=None, old_evidence=evidence,
        old_producers=dict(model=result["model_implementation"], reporting=result["implementation"]),
        source_prepared=evidence["prepared"], source_references=source_refs, real_annual=real_annual_refs,
        source_population_ids=prepared["population_ids"], grid=prepared["grid"], regions=list(region_names),
        reconciliation=dict(status="complete", expected_outer_per_case=expected_outer, inner_refits=inner,
                            outer=reconciled, annual_states=len(reconciled) * 20,
                            maximum_absolute_metric_residual=max(residuals, default=0.)),
        shape_recovery=summaries, native_error_decomposition=decompositions,
        point_scale_evidence=scales, weighted_scale_evidence=weighted_summary,
        weighted_scale_statuses=[dict(case=key[0], year=key[1], block=key[2], status=key[3],
             inherited_limitation=key[4], own_reasons=list(key[5]), count=value)
             for key, value in sorted(weighted_statuses.items())],
        scale_statuses=[dict(case=key[0], fit=key[1], block=key[2], status=key[3],
             inherited_limitation=key[4], count=value) for key, value in sorted(scale_counts.items())],
        interval_evidence=interval_summaries["complete_rate"], shape_interval_evidence=interval_summaries["shape"],
        figure_contracts=FIGURE_CONTRACTS,
        gate=dict(status="proceed" if proceed else "stop", rule="final_year_broad_regional_bias_squared_gt_variation_in_both_cases",
                  cases=gate_rows, reason="bias_dominated_broad_failure" if proceed else "mechanism_not_supported"),
        status="complete", recommendation="proceed" if proceed else "mechanism_not_supported",
        admission="not_admitted", handoff=None,
        limitations=["descriptive bias domination does not prove the fixed basis repairs the mechanism",
                    "native errors include a signed cross term under nonuniform reference shares",
                    "saved working/basic intervals describe complete rates; shape recovery is separated here",
                    "saved point and weighted searches have different data weights; different optima alone do not establish a numerical bug",
                    "scale endpoint and inherited limitations remain in all denominators"],
        **write_arrays(output, "diagnosis.npz", arrays),
        resources=dict(**resources(started), process_seconds=time.process_time() - process_started))
    write_json(output / "diagnosis.json", json_values(document))
    return identity(output / "diagnosis.json")



def native_designs(p: np.ndarray) -> list[dict]:
    """fixed 04c truths on the unchanged paired lineup stream; no responses enter the design."""
    from hockey_stats.attribution_simulation import synthetic_designs

    centers = grid()[0]
    require(p.shape == (656,) and np.isfinite(p).all() and np.all(p > 0)
            and abs(float(p.sum()) - 1) <= 1e-12, "synthetic shares must be positive original native shares")
    order = np.lexsort((np.arange(len(p)), np.sum((centers - [89, 0]) ** 2, axis=1)))
    stop = int(np.searchsorted(np.cumsum(p[order]), .5, side="left")) + 1
    radial = -np.ones(656)
    radial[order[:stop]] = 1
    lateral = (centers[:, 0] > 25) * centers[:, 1] / 42.5
    local = (np.exp(-np.sum((centers - [80, 15]) ** 2, axis=1) / 200)
             - np.exp(-np.sum((centers - [80, -15]) ** 2, axis=1) / 200))
    rough = ((centers[:, 0] > 25) * np.sin(2 * np.pi * (centers[:, 0] + 100) / 20)
             * np.cos(2 * np.pi * centers[:, 1] / 20))
    patterns = {}
    for name, values in (("radial", radial), ("lateral", lateral), ("local", local), ("rough", rough)):
        centered = values - p @ values
        patterns[name] = p * centered / np.max(np.abs(centered))
    designs = synthetic_designs()["paired"]
    for year, design in enumerate(designs):
        n = len(design["players"])
        positions = {player: i for i, player in enumerate(design["players"])}
        scalar = design["scalar_ticks"].astype(float) / 40
        shape = np.zeros((2 * n, 656))
        for pair, pattern, amplitude in (((3, 4), "radial", .10), ((10, 11), "lateral", .10),
                                          ((18, 19), "local", .10), ((20, 21), "rough", .05),
                                          ((26, 31), "lateral", .05)):
            shape[positions[pair[0]]] = amplitude * patterns[pattern]
            shape[positions[pair[1]]] = -amplitude * patterns[pattern]
        if year >= 2:
            shape[positions[32]] = .05 * patterns["radial"]
            shape[n + positions[33]] = .05 * patterns["lateral"]
        if year >= 3:
            shape[positions[8]] = .05 * patterns["radial"]
        for offset in (0, n):
            scalar[offset:offset + n] -= design["u"] @ scalar[offset:offset + n]
            shape[offset:offset + n] -= design["u"] @ shape[offset:offset + n]
        truth_map = scalar[:, None] * p + shape
        mu = 40 * (p + design["X"] @ truth_map)
        require(np.isfinite(mu).all() and np.all(mu > 0),
                "fixed generating rates must be strictly positive without clipping or redrawing")
        _close(shape.sum(axis=1), np.zeros(2 * n), "generating shape does not sum to zero")
        _close(truth_map.sum(axis=1), scalar, "generating map does not sum to scalar truth")
        design.update(truth_scalar=scalar, truth_shape=shape, truth_map=truth_map, mu=mu, p=p.copy())
    return designs


def synthetic_populations(designs: list[dict], case_id: int, outer_id: int,
                          source_protocol_sha: str) -> tuple[dict, list[dict]]:
    from hockey_stats.attribution_data import synthetic_population

    populations, digests = {}, []
    for year, design in enumerate(designs):
        responses = synthetic_counts(design, case_id, outer_id, year)
        digests.append(dict(season=SEASONS[year], sha256=ordered_array_digest(dict(responses=responses))))
        populations[("unblocked_spatial", SEASONS[year])] = synthetic_population(
            design, responses, year, source_protocol_sha, case_id, outer_id)
    return populations, digests


def statistic_digests(populations: dict) -> list[dict]:
    from hockey_stats.attribution_data import statistic_digest, weighted_population

    result = []
    for season in SEASONS:
        grouped, references = populations[("unblocked_spatial", season)]
        population = weighted_population(grouped, np.ones(len(grouped.game_ids)), references)
        result.append(dict(season=season, sha256=statistic_digest(population)))
    return result


def scalar_truth_fraction(design: dict, role: str, coefficients):
    from fractions import Fraction

    n = len(design["players"])
    offset = n if role == "defense" else 0
    ticks = design["scalar_ticks"][offset:offset + n]
    exposures = design["player_exposure"].astype(np.int64)
    require(np.array_equal(exposures, design["player_exposure"]), "synthetic exposure lost exact integer seconds")
    center = Fraction(sum(int(e) * int(t) for e, t in zip(exposures, ticks, strict=True)),
                      40 * sum(int(e) for e in exposures))
    return sum((coefficient * (Fraction(int(ticks[design["players"].index(player)]), 40) - center)
                for player, coefficient in coefficients), Fraction())


def recovery_requests(designs: list[dict], p: np.ndarray, W: np.ndarray) -> list[dict]:
    centers = grid()[0]
    radial = (np.linalg.norm(centers - [89, 0], axis=1) <= 20).astype(float)
    lateral = (centers[:, 0] > 25) * np.sign(centers[:, 1])
    radial -= p @ radial
    lateral -= p @ lateral
    _, region_names = shape_regions()
    vectors = [(name, W[:, i] - p @ W[:, i]) for i, name in enumerate(region_names)]
    vectors += [("radial", radial), ("lateral", lateral)]
    requests = []
    def append(year, role, coefficients, name, group, assigned=None, peak=False):
        selected = list(vectors)
        if group == "annual_transition":
            selected = selected[:12] + [(assigned, radial if assigned == "radial" else lateral)]
        if peak:
            design = designs[year]
            n = len(design["players"])
            offset = n if role == "defense" else 0
            truth = sum((coefficient * design["truth_shape"][offset + design["players"].index(player)]
                         for player, coefficient in coefficients), np.zeros(656))
            cell = int(np.argmax(np.abs(truth)))
            vector = np.eye(1, 656, cell).ravel()
            vector -= p @ vector
            selected += [(f"max_true_shape_cell_{cell}", vector)]
        for functional, vector in selected:
            primary = year == 4 and role == "offense" and ((name == "radial_3_minus_4" and functional == "radial")
                       or (name == "lateral_10_minus_11" and functional == "lateral"))
            requests.append(dict(name=f"{role}_{name}_shape", benchmark="unblocked_spatial", season=SEASONS[year],
                role=role, coefficients=coefficients, functional=functional, estimand="shape", weights=vector.tolist(),
                group=group, primary_coverage=bool(primary), negate=False))
    for year in (0, 4):
        for name, pair in (("radial_3_minus_4", (3, 4)), ("lateral_10_minus_11", (10, 11)),
                           ("local_18_minus_19", (18, 19)), ("rough_20_minus_21", (20, 21))):
            append(year, "offense", [[pair[0], 1], [pair[1], -1]], name, "shape_pair", peak=True)
        append(year, "offense", [[26, 1], [31, 1]], "pair_26_plus_31", "paired_sum")
    for year in range(5):
        for name, coefficients in (("player_26", [[26, 1]]), ("player_31", [[31, 1]]),
                                   ("pair_26_minus_31", [[26, 1], [31, -1]])):
            append(year, "offense", coefficients, name, "exact_null")
    for year, role, player, name, assigned in ((2, "offense", 32, "entrant_32", "radial"),
        (2, "defense", 33, "entrant_33", "lateral"), (3, "offense", 8, "returner_8", "radial")):
        append(year, role, [[player, 1]], name, "annual_transition", assigned)
    for year, role, coefficients, name in ((4, "offense", [[2, 1], [5, -1]], "pair_2_minus_5"),
        (4, "offense", [[6, 1], [2, -1]], "pair_6_minus_2"), (4, "offense", [[7, 1], [2, -1]], "pair_7_minus_2"),
        (2, "offense", [[32, 1]], "entrant_32"), (2, "defense", [[33, 1]], "entrant_33"),
        (3, "offense", [[8, 1]], "returner_8")):
        requests.append(dict(name=f"{role}_{name}_volume", benchmark="unblocked_spatial", season=SEASONS[year],
            role=role, coefficients=coefficients, functional="scalar", estimand="volume", group="volume",
            primary_coverage=False, negate=False))
    from hockey_stats.attribution_uncertainty import request_key
    require(len({request_key(request) for request in requests}) == len(requests), "duplicate recovery projection requests")
    require(sum(request["primary_coverage"] for request in requests) == 2, "primary coverage request contract changed")
    return requests


def truth_for_request(designs: list[dict], request: dict):
    design = designs[SEASONS.index(request["season"])]
    n = len(design["players"])
    offset = n if request["role"] == "defense" else 0
    coefficients = request["coefficients"]
    if request["estimand"] == "volume":
        return 40 * float(scalar_truth_fraction(design, request["role"], coefficients))
    values = design["truth_shape"] if request["estimand"] == "shape" else design["truth_map"]
    native = 40 * sum((coefficient * values[offset + design["players"].index(player)]
                       for player, coefficient in coefficients), np.zeros(656))
    return native if request["functional"] == "native" else float(native @ np.asarray(request["weights"]))


def freeze_protocol(baseline_prepared: Path | str, diagnosis: Path | str, out: Path | str, *,
                    output_root: Path | str, budgets: dict | None = None) -> dict:
    from hockey_stats.attribution_data import read_revision_prepared
    from hockey_stats.attribution_uncertainty import request_identity

    diagnosis_path = Path(diagnosis).resolve(strict=True)
    diagnosed = read_artifact(diagnosis_path, "attribution_recovery_diagnosis")
    require(diagnosed["status"] == "complete" and diagnosed["gate"]["status"] == "proceed",
            "frozen model protocol requires a complete diagnosis supporting the mechanism")
    source_path = Path(baseline_prepared).resolve(strict=True)
    source = read_revision_prepared(source_path)
    require(identity(source_path) == diagnosed["source_prepared"], "model protocol changed the diagnosed source preparation")
    selected_budgets = dict(RESEARCH_BUDGETS)
    if budgets is not None:
        require(diagnosed["purpose"] == "fixture_exercise", "research budgets cannot be changed")
        require(set(budgets) == set(selected_budgets) and all(type(value) is int and value > 0 for value in budgets.values())
                and budgets["workers"] <= 4, "invalid bounded fixture budgets")
        selected_budgets = budgets
    root = Path(output_root).resolve(strict=True)
    if diagnosed["purpose"] == "research":
        require(root.is_relative_to(RESEARCH_ROOT), "research protocol output root must remain external-only")
    path = output_path(str(out), [str(source_path.parent), str(diagnosis_path.parent)])
    if diagnosed["purpose"] == "research":
        require(path.is_relative_to(root), "research protocol file escaped its frozen external root")
    reference = next(row for row in source["annual"]
                     if row["population"] == "unblocked_spatial" and row["season"] == SEASONS[0])
    p = _old_arrays(reference["references"], reference["reference_shapes"])["p"]
    designs = native_designs(p)
    W, _ = shape_regions()
    document = artifact("attribution_recovery_protocol", diagnosed["purpose"],
        dict(diagnosis=identity(diagnosis_path), spec_snapshot=diagnosed["spec_snapshot"], source_prepared=identity(source_path)),
        diagnosis=identity(diagnosis_path), spec_snapshot=diagnosed["spec_snapshot"],
        source_prepared=identity(source_path), source_protocol=source["protocol"], old_evidence=diagnosed["old_evidence"],
        grid=source["grid"], reference=reference["references"],
        request_sha256=request_identity(recovery_requests(designs, p, W)),
        synthetic_design_sha256=ordered_array_digest(synthetic_design_arrays(designs, W)),
        output_root=str(root), budgets=selected_budgets, **PROTOCOL_RULES)
    validate_protocol(document)
    write_json(path, json_values(document))
    return identity(path)


def synthetic_design_arrays(designs: list[dict], W: np.ndarray) -> dict:
    arrays = {f"year_{year}_{name}": design[name] for year, design in enumerate(designs)
              for name in ("offense", "defense", "seconds", "si", "u", "scalar_ticks", "truth_scalar", "truth_shape", "truth_map",
                           "player_exposure", "home_teams", "away_teams")}
    arrays.update(p=designs[0]["p"], centers=grid()[0], W=W)
    return arrays


def prepare(baseline_prepared: Path | str, diagnosis: Path | str, protocol: Path | str,
            out: Path | str) -> dict:
    from hockey_stats.attribution import build_shape_basis
    from hockey_stats.attribution_data import read_revision_prepared
    from hockey_stats.attribution_uncertainty import request_identity

    started, process_started = time.monotonic(), time.process_time()
    source_path, diagnosis_path, protocol_path = [Path(value).resolve(strict=True)
                                               for value in (baseline_prepared, diagnosis, protocol)]
    source = read_revision_prepared(source_path)
    diagnosed = read_artifact(diagnosis_path, "attribution_recovery_diagnosis")
    frozen = read_artifact(protocol_path, "attribution_recovery_protocol")
    validate_protocol(frozen)
    require(frozen["purpose"] == diagnosed["purpose"] and frozen["diagnosis"] == identity(diagnosis_path)
            and frozen["source_prepared"] == diagnosed["source_prepared"] == identity(source_path)
            and diagnosed["status"] == "complete" and diagnosed["gate"]["status"] == "proceed",
            "preparation differs from passed diagnosis or frozen source")
    if frozen["purpose"] == "research":
        require(implementation() == frozen["implementation"], "preparation producer differs from frozen model protocol")
    output = output_path(str(out), [str(path.parent) for path in (source_path, diagnosis_path, protocol_path)])
    require(output.is_relative_to(Path(frozen["output_root"])), "preparation differs from frozen output root")
    first = next(row for row in source["annual"] if row["population"] == "unblocked_spatial" and row["season"] == SEASONS[0])
    references = _old_arrays(first["references"], first["reference_shapes"])
    p = references["p"]
    basis = build_shape_basis(grid(), p)
    designs = native_designs(p)
    W, region_names = shape_regions()
    requests = recovery_requests(designs, p, W)
    design_arrays = synthetic_design_arrays(designs, W)
    require(request_identity(requests) == frozen["request_sha256"]
            and ordered_array_digest(design_arrays) == frozen["synthetic_design_sha256"],
            "prepared design, truth or requests differ from the frozen protocol")
    output.mkdir()
    basis_arrays = write_arrays(output, "basis.npz", dict(B=basis.B, p=basis.p, eigenvalues=basis.eigenvalues))
    design_binding = write_arrays(output, "design.npz", design_arrays)
    request_path = output / "requests.json"
    write_json(request_path, requests)
    document = artifact("attribution_recovery_prepared", frozen["purpose"],
        dict(source_prepared=identity(source_path), diagnosis=identity(diagnosis_path), model_protocol=identity(protocol_path),
             spec_snapshot=frozen["spec_snapshot"], requests=identity(request_path)),
        source_prepared=identity(source_path), source_protocol=source["protocol"], model_protocol=identity(protocol_path),
        diagnosis=identity(diagnosis_path), seasons=list(SEASONS), source_population_ids=source["population_ids"],
        original_annual=[dict(population=row["population"], season=row["season"], references=row["references"], rows=row["rows"])
                        for row in source["annual"]],
        basis=basis_arrays["arrays"], basis_shapes=basis_arrays["array_shapes"], basis_sha256=basis.sha256,
        synthetic_design=design_binding, synthetic_years=[dict(season=SEASONS[year], players=list(design["players"]),
            strata=design["strata"], minimum_generating_rate=float(design["mu"].min())) for year, design in enumerate(designs)],
        requests=identity(request_path), request_sha256=request_identity(requests), regions=list(region_names),
        grid=source["grid"], resources=dict(**resources(started), process_seconds=time.process_time()-process_started),
        admission="not_admitted", handoff=None)
    path = output / "prepared.json"
    write_json(path, json_values(document))
    return identity(path)


def read_prepared(path: Path | str) -> tuple[dict, dict, object, list[dict]]:
    from hockey_stats.attribution import read_shape_basis
    from hockey_stats.attribution_data import read_recovery_prepared
    from hockey_stats.attribution_uncertainty import request_identity

    document = read_recovery_prepared(path)
    protocol = read_artifact(linked_path(document["model_protocol"]), "attribution_recovery_protocol")
    validate_protocol(protocol)
    basis = read_shape_basis(document)
    saved_design = load_arrays(document["synthetic_design"])
    designs = native_designs(basis.p)
    W, names = shape_regions()
    for year, design in enumerate(designs):
        require(document["synthetic_years"][year]["players"] == list(design["players"]), "prepared synthetic player order changed")
        for name in ("offense", "defense", "seconds", "si", "u", "scalar_ticks", "truth_scalar", "truth_shape", "truth_map",
                     "player_exposure", "home_teams", "away_teams"):
            require(np.array_equal(saved_design[f"year_{year}_{name}"], design[name]), "prepared synthetic design/truth changed")
    require(np.array_equal(saved_design["p"], basis.p) and np.array_equal(saved_design["W"], W)
            and np.array_equal(saved_design["centers"], grid()[0]) and document["regions"] == list(names),
            "prepared geometry/reference/region identity changed")
    requests = read_json(linked_path(document["requests"]))
    require(requests == recovery_requests(designs, basis.p, W) and request_identity(requests) == document["request_sha256"],
            "prepared joint projection request identity changed")
    require(document["request_sha256"] == protocol["request_sha256"]
            and ordered_array_digest(saved_design) == protocol["synthetic_design_sha256"],
            "prepared design or requests differ from frozen protocol identities")
    return document, protocol, basis, designs


def point_chains(inputs, model_protocol_sha256: str, basis) -> tuple[dict, dict]:
    from hockey_stats.attribution_uncertainty import fit_history

    states, receipts = {}, {}
    weights = {season: np.ones(len(inputs.populations[("unblocked_spatial", season)][0].game_ids)) for season in SEASONS}
    for representation in ("native_04b", "graph_40ft"):
        receipt, chain = fit_history(inputs, [], benchmarks=("unblocked_spatial",), game_multipliers=weights,
            representation=representation, basis=basis if representation == "graph_40ft" else None,
            model_protocol_sha256=model_protocol_sha256, prior_policy="history")
        states[representation], receipts[representation] = chain, receipt
    return states, receipts


def _point_outer(prepared_reference: dict, case_id: int, outer_id: int, output: Path) -> dict:
    from hockey_stats.attribution import annual_arrays, bounded_shape_resolution_check, shape_mean
    from hockey_stats.attribution_data import weighted_population
    from hockey_stats.attribution_uncertainty import RefitInputs, exact_duplicate_groups, project_requests

    started, process_started = time.monotonic(), time.process_time()
    prepared_path = linked_path(prepared_reference)
    document, protocol, basis, designs = read_prepared(prepared_path)
    if document["purpose"] == "research":
        require(implementation() == protocol["implementation"], "point producer differs from frozen model protocol")
    populations, response_digests = synthetic_populations(designs, case_id, outer_id, document["source_protocol"]["sha256"])
    statistics = statistic_digests(populations)
    groups = exact_duplicate_groups(populations, list(SEASONS), benchmarks=("unblocked_spatial",))
    inputs = RefitInputs(dict(seasons=list(SEASONS)), protocol, populations, None, groups, "synthetic")
    states, receipts = point_chains(inputs, document["model_protocol"]["sha256"], basis)
    complete = all(value["status"] == "complete" for value in receipts.values())
    requests = read_json(linked_path(document["requests"]))
    projections, point_records, arrays, metrics, probes = {}, {}, {}, [], []
    W, _ = shape_regions()
    for representation, chain in states.items():
        records, projected = [], []
        previous_record = None
        for (benchmark, season), state in chain.items():
            year = SEASONS.index(season)
            blocks, values = annual_arrays(state)
            prefix = f"{representation}_{season}_"
            arrays.update({prefix + name: value for name, value in values.items()})
            record = dict(schema_version=3, kind="attribution_recovery_annual", representation=representation,
                source_kind="synthetic", season=season, season_index=year, benchmark=benchmark,
                source_prepared=document["source_prepared"], source_protocol=document["source_protocol"],
                model_protocol=document["model_protocol"], population_id=state.population_id,
                basis=document["basis"] if representation == "graph_40ft" else None,
                basis_sha256=document["basis_sha256"] if representation == "graph_40ft" else None,
                player_ids=list(state.player_ids), current_player_ids=list(state.current_player_ids),
                entrant_ids=list(state.entrant_ids), carried_only_ids=list(state.carried_only_ids),
                previous=previous_record, array_prefix=prefix, r=state.r,
                strata=populations[(benchmark, season)][1].strata, **blocks)
            records.append(record)
            previous_record = dict(representation=representation, season=season)
            selected_requests = [request for request in requests if request["season"] == season]
            projected.extend(project_requests(state, selected_requests, groups[(benchmark, season)]))
            if representation == "graph_40ft" and outer_id == 0 and year in (0, 4):
                c_vectors = []
                positions = {player: i for i, player in enumerate(state.player_ids)}
                for request in selected_requests:
                    c = np.zeros(2 * len(positions))
                    offset = len(positions) if request["role"] == "defense" else 0
                    for player, coefficient in request["coefficients"]:
                        c[offset + positions[player]] += coefficient
                    v = np.asarray(request["weights"]) if "weights" in request else np.ones(656)
                    c_vectors.append((c, v, request["estimand"]))
                grouped, references = populations[(benchmark, season)]
                population = weighted_population(grouped, np.ones(len(grouped.game_ids)), references)
                previous = chain.get((benchmark, SEASONS[year - 1])) if year else None
                probe = bounded_shape_resolution_check(population, previous, state, regions=W,
                                                        projections=tuple(c_vectors))
                probes.append(dict(case_id=case_id, outer_id=outer_id, year=year + 1, **probe))
        point_records[representation] = records
        projections[representation] = [dict(
            {name: row[name] for name in ("key", "status", "reason", "mean", "working", "r", "duplicate_groups")},
            truth=truth_for_request(designs, row["request"]), units="attempts/60 team minutes",
            estimand=row["request"]["estimand"], refit=None, refit_reason="not_run_in_mean_stage") for row in projected]
    if complete:
        for season in SEASONS:
            native = states["native_04b"][("unblocked_spatial", season)]
            candidate = states["graph_40ft"][("unblocked_spatial", season)]
            require(native.r == candidate.r and np.array_equal(native.p, candidate.p)
                    and np.array_equal(native.u, candidate.u)
                    and native.player_ids == candidate.player_ids, "paired point references or row order changed")
            require(all(np.array_equal(getattr(native.volume, field), getattr(candidate.volume, field))
                        for field in ("M", "V", "A", "prior_mean", "prior_covariance"))
                    and native.volume.scale == candidate.volume.scale,
                    "paired point fits changed the common volume arithmetic")
        for year in (0, 4):
            season = SEASONS[year]
            design = designs[year]
            for contrast, pair in (("radial", (3, 4)), ("lateral", (10, 11)), ("local", (18, 19)), ("rough", (20, 21))):
                left, right = (design["players"].index(player) for player in pair)
                true_shape = 40 * (design["truth_shape"][left] - design["truth_shape"][right])
                true_volume = 40 * (design["truth_scalar"][left] - design["truth_scalar"][right])
                arrays[f"truth_{year + 1}_{contrast}_shape"] = true_shape
                arrays[f"truth_{year + 1}_{contrast}_complete"] = true_volume * basis.p + true_shape
                for representation, chain in states.items():
                    state = chain[("unblocked_spatial", season)]
                    positions = {player: i for i, player in enumerate(state.player_ids)}
                    i, j = (positions[player] for player in pair)
                    fitted_shape = 40 * (shape_mean(state)[i] - shape_mean(state)[j])
                    fitted_volume = 40 * float(state.volume.M[i, 0] - state.volume.M[j, 0])
                    arrays[f"{representation}_{year + 1}_{contrast}_shape"] = fitted_shape
                    arrays[f"{representation}_{year + 1}_{contrast}_complete"] = fitted_volume * basis.p + fitted_shape
                    errors = error_decomposition(fitted_volume, fitted_shape, true_volume, true_shape, basis.p)
                    metrics.append(dict(case_id=case_id, outer_id=outer_id, year=year + 1, contrast=contrast,
                        representation=representation, native_shape_error=errors["shape_native_squared_error"],
                        region_shape_error=float(np.sum(((fitted_shape - true_shape) @ W) ** 2)),
                        region_shape_truth_energy=float(np.sum((true_shape @ W) ** 2)),
                        native_shape_truth_energy=float(true_shape @ true_shape), **errors))
    point_errors = [dict(representation=name, error=value["error"], failed=value["failed"])
                    for name, value in receipts.items() if value["status"] != "complete"]
    bindings = write_arrays(output, f"{CASES[case_id]}-{outer_id:03d}.npz", arrays) if arrays else {}
    record = artifact("attribution_recovery_mean_outer", document["purpose"],
        dict(prepared=prepared_reference, source_prepared=document["source_prepared"],
             model_protocol=document["model_protocol"], requests=document["requests"]),
        prepared=prepared_reference, source_prepared=document["source_prepared"], source_kind="synthetic",
        model_protocol=document["model_protocol"], basis=document["basis"], basis_sha256=document["basis_sha256"],
        requests=document["requests"], request_sha256=document["request_sha256"],
        case=CASES[case_id], case_id=case_id, outer_id=outer_id, response_digests=response_digests,
        response_seeds=[[40430, case_id, outer_id, year] for year in range(5)], statistic_digests=statistics,
        status="complete" if complete else "incomplete", error=None if complete else point_errors,
        point_records=point_records, projections=projections, error_metrics=metrics,
        duplicate_groups=[dict(benchmark=key[0], season=key[1], groups=value) for key, value in groups.items()],
        numerical_resolution=probes, point_resources={name: value["resources"] for name, value in receipts.items()},
        resources=dict(**resources(started), process_seconds=time.process_time() - process_started), **bindings)
    path = output / f"{CASES[case_id]}-{outer_id:03d}.json"
    write_json(path, json_values(record))
    return dict(case_id=case_id, outer_id=outer_id, manifest=identity(path))


def mean_gate(records: list[dict], protocol: dict) -> dict:
    expected = protocol["budgets"]["outer_per_case"]
    n_resamples = protocol["budgets"]["paired_error_resamples"]
    ids = [(row["case_id"], row["outer_id"]) for row in records]
    complete = len(ids) == len(set(ids)) and set(ids) == {(case, outer) for case in range(2) for outer in range(expected)}
    complete = complete and all(row["status"] == "complete" for row in records)
    if not complete:
        return dict(status="incomplete", rules=[], reason="incomplete_point_dataset_denominator")
    rules = []
    for case_id in range(2):
        selected = sorted((row for row in records if row["case_id"] == case_id), key=lambda row: row["outer_id"])
        for contrast_id, contrast in enumerate(("radial", "lateral")):
            candidate, native, zero = [], [], []
            for outer in selected:
                metrics = [row for row in outer["error_metrics"] if row["year"] == 5 and row["contrast"] == contrast]
                require(len(metrics) == 2 and {row["representation"] for row in metrics} == {"native_04b", "graph_40ft"},
                        "primary mean comparison missing or duplicated")
                candidate.append(next(row["region_shape_error"] for row in metrics if row["representation"] == "graph_40ft"))
                native.append(next(row["region_shape_error"] for row in metrics if row["representation"] == "native_04b"))
                zero.append(metrics[0]["region_shape_truth_energy"])
            for baseline_id, (baseline, errors) in enumerate((("zero_shape", zero), ("native_04b", native))):
                differences = np.asarray(errors) - candidate
                rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([40432, case_id, contrast_id, baseline_id])))
                sampled = differences[rng.integers(0, expected, size=(n_resamples, expected))].mean(axis=1)
                lower, upper = np.quantile(sampled, [.025, .975], method="linear")
                status = "supported" if lower > 0 else "failed" if upper <= 0 else "inconclusive"
                rules.append(dict(case=CASES[case_id], case_id=case_id, contrast=contrast, baseline=baseline,
                    n=expected, resamples=n_resamples, seed=[40432, case_id, contrast_id, baseline_id],
                    estimand="twelve_region_shape_squared_error", units="squared attempts/60 team minutes",
                    mean_baseline_error=float(np.mean(errors)), mean_candidate_error=float(np.mean(candidate)),
                    mean_gain=float(differences.mean()), percentile_95=[float(lower), float(upper)], status=status))
    status = "failed" if any(row["status"] == "failed" for row in rules) else (
             "supported" if all(row["status"] == "supported" for row in rules) else "inconclusive")
    return dict(status=status, rules=rules,
                reason="all_eight_directional_gains_supported" if status == "supported" else "mean_recovery_" + status)


def pilot_means(prepared: Path | str, out: Path | str) -> dict:
    from concurrent.futures import ProcessPoolExecutor
    import multiprocessing

    started, process_started = time.monotonic(), time.process_time()
    prepared_path = Path(prepared).resolve(strict=True)
    document, protocol, _, _ = read_prepared(prepared_path)
    if document["purpose"] == "research":
        require(implementation() == protocol["implementation"], "mean producer differs from frozen model protocol")
    output = output_path(str(out), [str(prepared_path.parent)])
    require(output.is_relative_to(Path(protocol["output_root"])), "mean output differs from frozen root")
    output.mkdir()
    count = protocol["budgets"]["outer_per_case"]
    jobs = [(identity(prepared_path), case, outer, output) for case in range(2) for outer in range(count)]
    workers = protocol["budgets"]["workers"]
    if workers == 1:
        refs = [_point_outer(*job) for job in jobs]
    else:
        with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as pool:
            refs = list(pool.map(_point_outer_job, jobs, chunksize=1, buffersize=workers))
    records = [read_artifact(linked_path(row["manifest"]), "attribution_recovery_mean_outer") for row in refs]
    gate = mean_gate(records, protocol)
    probes = [probe for row in records for probe in row["numerical_resolution"]]
    numerical_complete = len(probes) == 4 and all(probe["status"] == "verified" for probe in probes)
    status = "complete" if gate["status"] != "incomplete" and numerical_complete else "incomplete"
    recommendation = "incomplete" if status == "incomplete" else (
        "mean_recovery_supported" if gate["status"] == "supported" else "mean_recovery_" + gate["status"])
    if not numerical_complete:
        gate = dict(status="incomplete", rules=gate["rules"], reason="bounded_numerical_resolution_failed_or_incomplete")
    document = artifact("attribution_recovery_means", document["purpose"],
        dict(prepared=identity(prepared_path), source_prepared=document["source_prepared"],
             model_protocol=document["model_protocol"], requests=document["requests"]),
        prepared=identity(prepared_path), source_prepared=document["source_prepared"], model_protocol=document["model_protocol"],
        basis=document["basis"], basis_sha256=document["basis_sha256"], requests=document["requests"],
        request_sha256=document["request_sha256"], outers=refs, expected_outer_per_case=count,
        completed_ids=[[row["case_id"], row["outer_id"]] for row in records if row["status"] == "complete"],
        incomplete_ids=[[row["case_id"], row["outer_id"]] for row in records if row["status"] != "complete"],
        gate=gate, status=status, recommendation=recommendation,
        numerical_resolution=dict(status="passed" if numerical_complete else "incomplete", probes=probes),
        execution=dict(workers=workers, numerical_threads_per_worker=1, response_policy="one original stream shared by both estimators"),
        resources=dict(**resources(started), process_seconds=time.process_time() - process_started,
                       worker_process_seconds=sum(row["resources"]["process_seconds"] for row in records)),
        limitations=["directional gain is not an independently justified practical map-accuracy margin",
                     "complete rates and local/rough shapes remain secondary diagnostics"],
        admission="not_admitted", handoff=None)
    path = output / "means.json"
    write_json(path, json_values(document))
    return identity(path)


def _point_outer_job(arguments: tuple) -> dict:
    return _point_outer(*arguments)

def coverage_support(covered: int, total: int) -> dict:
    """the specified pointwise wilson rule; missing execution never shrinks total."""
    require(type(covered) is int and type(total) is int and 0 <= covered <= total and total > 0,
            "invalid coverage numerator or denominator")
    z = 1.959963984540054
    rate = covered / total
    denominator = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denominator
    half = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total)) / denominator
    lower, upper = center - half, center + half
    return dict(covered=covered, n=total, rate=rate, wilson=[lower, upper],
                status="supported" if lower >= .90 else "failed" if upper < .90 else "inconclusive",
                nominal_coverage=.95, developmental_floor=.90)


def interval_record(point: dict, truth: float, draws: np.ndarray, *, expected_draws: int,
                    full_history_complete: bool) -> dict:
    """one fixed scalar functional, with exact-null abstention distinct from zero."""
    from hockey_stats.attribution_uncertainty import basic_interval, meaningful_claim

    draws = np.asarray(draws, dtype=float)
    require(draws.ndim == 1 and np.isfinite(draws).all() and math.isfinite(truth)
            and type(expected_draws) is int and expected_draws > 0 and len(draws) <= expected_draws,
            "invalid scalar refit interval population")
    record = dict(key=point["key"], request={name: value for name, value in point["request"].items() if name != "weights"}, truth=truth,
                  units="attempts per 60 team minutes", point=point["mean"], status=point["status"],
                  reason=point["reason"], working=None, refit=None,
                  expected_draws=expected_draws, completed_draws=len(draws),
                  full_history_complete=full_history_complete, raw_spread=None)
    if point["mean"] is None:
        return record
    estimate = float(point["mean"])
    require(math.isfinite(estimate), "nonfinite point projection")
    unidentified = point["status"] == "not_data_identified"
    prior = point["working"]
    working = dict(kind="working_conditional", lower=float(prior["lower"]), upper=float(prior["upper"]),
                   width=float(prior["upper"] - prior["lower"]), bias=estimate - truth,
                   covered=bool(prior["lower"] <= truth <= prior["upper"]), prior_conditioned=unidentified)
    working["wrong_sign_zero_exclusion"] = (None if unidentified else
        bool((prior["lower"] > 0 and truth <= 0) or (prior["upper"] < 0 and truth >= 0)))
    record["working"] = working
    if len(draws):
        record["raw_spread"] = dict(n=len(draws), mean=float(draws.mean()),
                                    standard_deviation=float(draws.std()),
                                    minimum=float(draws.min()), maximum=float(draws.max()))
    if unidentified:
        record["reason"] = "persistent_same_role_co_deployment_null_component"
        return record
    if len(draws) != expected_draws or not full_history_complete:
        record.update(status="incomplete", reason="missing_or_error_inner_histories")
        return record
    interval = basic_interval(estimate, draws)
    lower, upper = float(interval["lower"]), float(interval["upper"])
    record["refit"] = dict(kind=interval["kind"], lower=lower, upper=upper, width=upper - lower,
                           quantile_025=float(interval["quantile_025"]),
                           quantile_975=float(interval["quantile_975"]), bias=estimate - truth,
                           covered=bool(lower <= truth <= upper),
                           wrong_sign_zero_exclusion=bool((lower > 0 and truth <= 0)
                                                         or (upper < 0 and truth >= 0)),
                           prior_conditioned=False)
    if point["request"]["estimand"] == "volume":
        for kind in ("working", "refit"):
            record[kind]["meaningful_scalar_label"] = meaningful_claim(
                record[kind]["lower"] / point["r"], record[kind]["upper"] / point["r"])
    return record


def _interval_outer(task: tuple[str, dict, str]) -> dict:
    """regenerate responses once, retain grouped moments, then execute fixed full histories."""
    from hockey_stats.attribution_data import read_revision_prepared
    from hockey_stats.attribution_uncertainty import (
        RefitInputs, annual_receipts, exact_duplicate_groups, refit_history,
        request_identity, request_key,
    )
    from hockey_stats.captures import InputContractError

    prepared_name, outer_ref, output_name = task
    started, process_started = time.monotonic(), time.process_time()
    prepared_path = Path(prepared_name).resolve(strict=True)
    prepared, protocol, basis, designs = read_prepared(prepared_path)
    source = read_revision_prepared(linked_path(prepared["source_prepared"]))
    original = read_artifact(linked_path(outer_ref["manifest"]), "attribution_recovery_mean_outer")
    case_id, outer_id = outer_ref["case_id"], outer_ref["outer_id"]
    require(original["case_id"] == case_id and original["outer_id"] == outer_id
            and original["status"] == "complete" and original["source_kind"] == "synthetic"
            and original["prepared"] == identity(prepared_path)
            and original["model_protocol"] == prepared["model_protocol"]
            and original["source_prepared"] == prepared["source_prepared"]
            and original["basis"] == prepared["basis"] and original["basis_sha256"] == basis.sha256
            and original["requests"] == prepared["requests"],
            "interval outer differs from the paired mean dataset")
    if prepared["purpose"] == "research":
        require(implementation() == protocol["implementation"] == original["implementation"],
                "interval or saved point producer differs from frozen model")
    requests = recovery_requests(designs, basis.p, shape_regions()[0])
    requests_sha256 = request_identity(requests)
    require(original["request_sha256"] == requests_sha256,
            "interval requests differ from saved point requests")
    point_rows = original["projections"]["graph_40ft"]
    point_by_key = {row["key"]: row for row in point_rows}
    keys = [request_key(request) for request in requests]
    require(len(point_by_key) == len(point_rows) and set(point_by_key) == set(keys),
            "saved point request identities differ")
    point_by_key = {key: dict(point_by_key[key], request=request)
                    for key, request in zip(keys, requests, strict=True)}
    require(all(point_by_key[key]["truth"] == float(truth_for_request(designs, request))
                for key, request in zip(keys, requests, strict=True)),
            "saved point truth differs from fixed generating truth")
    # Source preparation was resolved before synthetic generation; absence cannot select another input mode.
    populations, response_digests = synthetic_populations(designs, case_id, outer_id, source["protocol"]["sha256"])
    require(response_digests == original["response_digests"]
            and statistic_digests(populations) == original["statistic_digests"],
            "regenerated response or unit-weight statistics differ from paired points")
    groups = exact_duplicate_groups(populations, list(SEASONS), benchmarks=("unblocked_spatial",))
    inputs = RefitInputs(dict(purpose=prepared["purpose"], seasons=list(SEASONS)), protocol,
                         populations, None, groups, "synthetic")
    inner = protocol["budgets"]["inner_refits"]
    values = np.zeros((inner, len(requests)))
    available = np.zeros((inner, len(requests)), dtype=bool)
    weights = {season: np.zeros((inner, len(populations[("unblocked_spatial", season)][0].game_ids)))
               for season in SEASONS}
    weight_available = np.zeros((inner, len(SEASONS)), dtype=bool)
    receipts, completed, errors = [], [], []
    for draw_id in range(inner):
        seeds = [[40431, case_id, outer_id, draw_id, year] for year in range(5)]
        try:
            draw = refit_history(inputs, draw_id, requests, benchmarks=("unblocked_spatial",),
                                 year_seeds=seeds, representation="graph_40ft", basis=basis,
                                 model_protocol_sha256=prepared["model_protocol"]["sha256"])
            rows = {row["key"]: row for row in draw["projections"]}
            require(draw["draw_id"] == draw_id and len(rows) == len(draw["projections"])
                    and set(rows) <= set(keys), "duplicate or changed inner projection identity")
            for index, (key, request) in enumerate(zip(keys, requests, strict=True)):
                if key not in rows:
                    continue
                row = rows[key]
                require(row["request"] == request and row["status"] == point_by_key[key]["status"]
                        and row["mean"] is not None and np.asarray(row["mean"]).shape == ()
                        and math.isfinite(float(row["mean"])), "changed inner request, status or projection shape")
                values[draw_id, index] = row["mean"]
                available[draw_id, index] = True
            for year, season in enumerate(SEASONS):
                if season in draw["weights"]:
                    weights[season][draw_id] = draw["weights"][season]
                    weight_available[draw_id, year] = True
            complete = draw["status"] == "complete" and bool(available[draw_id].all())
            receipts.append(dict(draw_id=draw_id, status="complete" if complete else "error",
                                 error=draw["error"], seeds=draw["seeds"],
                                 annual=annual_receipts(draw["annual"]), resources=draw["resources"]))
        except (InputContractError, np.linalg.LinAlgError, FloatingPointError) as error:
            complete = False
            receipts.append(dict(draw_id=draw_id, status="error", error=str(error),
                                 seeds=[dict(season=season, seed=seed)
                                        for season, seed in zip(SEASONS, seeds, strict=True)], annual=[]))
        (completed if complete else errors).append(draw_id)
    records = []
    for index, request in enumerate(requests):
        key = request_key(request)
        truth = float(truth_for_request(designs, request))
        record = interval_record(point_by_key[key], truth, values[available[:, index], index],
                                 expected_draws=inner, full_history_complete=not errors and len(completed) == inner)
        if request["estimand"] == "volume":
            fraction = scalar_truth_fraction(designs[SEASONS.index(request["season"])],
                                             request["role"], request["coefficients"])
            record["exact_relative_truth"] = [fraction.numerator, fraction.denominator]
            record["relative_truth"] = float(fraction)
        records.append(record)
    output = Path(output_name)
    output.mkdir()
    arrays = write_arrays(output, "intervals.npz", dict(projections=values, projection_available=available,
                          weight_available=weight_available,
                          **{f"weights_year_{year}": weights[season] for year, season in enumerate(SEASONS)}))
    result = artifact("attribution_recovery_interval_outer", prepared["purpose"],
                      dict(prepared=identity(prepared_path), means=outer_ref["manifest"],
                           model_protocol=prepared["model_protocol"]),
                      prepared=identity(prepared_path), model_protocol=prepared["model_protocol"],
                      source_kind="synthetic", case_id=case_id, case=CASES[case_id], outer_id=outer_id,
                      request_sha256=requests_sha256, requests=prepared["requests"], response_digests=response_digests,
                      statistic_digests=original["statistic_digests"], expected_inner=inner,
                      completed_inner_ids=completed, error_inner_ids=errors, inner=receipts,
                      records=records, status="complete" if not errors else "incomplete",
                      reason=None if not errors else "missing_or_error_inner_histories", **arrays,
                      resources=dict(**resources(started), process_seconds=time.process_time() - process_started))
    write_json(output / "intervals.json", json_values(result))
    return dict(case_id=case_id, outer_id=outer_id, manifest=identity(output / "intervals.json"))


def interval_summaries(outers: list[dict], requests: list[dict], expected_outer: int) -> list[dict]:
    """all declared diagnostics; only four named cells enter the primary intersection."""
    from hockey_stats.attribution_uncertainty import request_key

    result = []
    for case_id in range(2):
        selected = [outer for outer in outers if outer["case_id"] == case_id]
        for request in requests:
            key = request_key(request)
            records = []
            for outer in selected:
                rows = [row for row in outer["records"] if row["key"] == key]
                require(len(rows) == 1 and rows[0]["request"] == {name: value for name, value in request.items() if name != "weights"},
                        "outer interval request differs")
                records.append(rows[0])
            null = bool(records) and all(row["status"] == "not_data_identified" for row in records)
            complete = len(records) == expected_outer and all(row["status"] == "available" for row in records)
            summary = dict(case_id=case_id, case=CASES[case_id], key=key, request={name: value for name, value in request.items() if name != "weights"},
                           primary=bool(request["primary_coverage"]), expected_outer=expected_outer,
                           completed_outer=sum(row["status"] == "available" for row in records),
                           status="not_data_identified" if null else "complete" if complete else "incomplete",
                           truth=records[0]["truth"] if records else None,
                           working=None, refit=None, raw_spread=None)
            if records:
                require(all(row["truth"] == records[0]["truth"] for row in records),
                        "truth changed between outer datasets")
                summary["bias"] = float(np.mean([row["point"] - row["truth"] for row in records]))
                if null:
                    spread = [row["raw_spread"]["standard_deviation"] for row in records if row["raw_spread"] is not None]
                    summary["raw_spread"] = dict(mean_inner_standard_deviation=float(np.mean(spread)) if spread else None,
                                                 n=len(spread), unavailable_reason=None if spread else "no_completed_projection_draws")
                for kind in ("working", "refit"):
                    cells = [row[kind] for row in records if row[kind] is not None]
                    if not cells:
                        continue
                    covered = sum(int(row["covered"]) for row in cells)
                    coverage = (None if null else coverage_support(covered, expected_outer)
                                if len(cells) == expected_outer else
                                dict(covered=covered, n=expected_outer, assessed=len(cells), rate=None, wilson=None,
                                     status="incomplete", reason="missing_outer_intervals",
                                     nominal_coverage=.95, developmental_floor=.90))
                    summary[kind] = dict(coverage=coverage, n=len(cells),
                                         mean_width=float(np.mean([row["width"] for row in cells])),
                                         prior_conditioned=null,
                                         wrong_sign_zero_exclusions=None if null else
                                         sum(int(row["wrong_sign_zero_exclusion"]) for row in cells))
                    if len(cells) != expected_outer:
                        summary[kind]["status"] = "incomplete"
                    else:
                        summary[kind]["status"] = "prior_conditioned_diagnostic" if null else "complete"
            result.append(summary)
    return result


def pilot_intervals(prepared: Path | str, means: Path | str, out: Path | str) -> dict:
    """only a complete supported paired-mean stage may spend the frozen refit budget."""
    from concurrent.futures import ProcessPoolExecutor
    from hockey_stats.attribution_uncertainty import request_identity
    from hockey_stats.captures import InputContractError

    started, process_started = time.monotonic(), time.process_time()
    prepared_path, means_path = Path(prepared).resolve(strict=True), Path(means).resolve(strict=True)
    document, protocol, basis, designs = read_prepared(prepared_path)
    point = read_artifact(means_path, "attribution_recovery_means")
    if document["purpose"] == "research":
        require(implementation() == protocol["implementation"] == point["implementation"],
                "interval or mean producer differs from frozen model")
    requests = recovery_requests(designs, basis.p, shape_regions()[0])
    expected_outer, inner = protocol["budgets"]["outer_per_case"], protocol["budgets"]["inner_refits"]
    expected_ids = {(case, outer) for case in range(2) for outer in range(expected_outer)}
    ids = [(row["case_id"], row["outer_id"]) for row in point["outers"]]
    require(point["prepared"] == identity(prepared_path) and point["model_protocol"] == document["model_protocol"]
            and point["purpose"] == document["purpose"] and point["status"] == "complete"
            and point["gate"]["status"] == "supported" and len(point["gate"]["rules"]) == 8
            and all(row["status"] == "supported" for row in point["gate"]["rules"])
            and point["numerical_resolution"]["status"] == "passed"
            and point["request_sha256"] == request_identity(requests)
            and len(ids) == len(set(ids)) and set(ids) == expected_ids,
            "intervals require complete supported paired means with unchanged requests and numerical checks")
    output = output_path(str(out), [str(prepared_path.parent), str(means_path.parent)])
    require(output.is_relative_to(Path(protocol["output_root"]).resolve())
            and (document["purpose"] != "research" or output.is_relative_to(RESEARCH_ROOT)),
            "interval output differs from frozen external root")
    output.mkdir()
    tasks = [(str(prepared_path), row, str(output / f"case-{row['case_id']}-outer-{row['outer_id']:03d}"))
             for row in point["outers"]]
    outers, failed = [], []
    workers = protocol["budgets"]["workers"]
    require(type(workers) is int and 1 <= workers <= 4, "interval workers differ from bounded budget")
    if workers == 1:
        for task in tasks:
            try:
                outers.append(_interval_outer(task))
            except (InputContractError, np.linalg.LinAlgError, FloatingPointError, OSError) as error:
                failed.append(dict(case_id=task[1]["case_id"], outer_id=task[1]["outer_id"], error=str(error)))
    else:
        import multiprocessing
        with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as executor:
            futures = [(task, executor.submit(_interval_outer, task)) for task in tasks]
            for task, future in futures:
                try:
                    outers.append(future.result())
                except (InputContractError, np.linalg.LinAlgError, FloatingPointError, OSError) as error:
                    failed.append(dict(case_id=task[1]["case_id"], outer_id=task[1]["outer_id"], error=str(error)))
    loaded = [read_artifact(linked_path(row["manifest"]), "attribution_recovery_interval_outer") for row in outers]
    # Reconcile identity sets rather than aligning independent lists by position.
    actual = [(row["case_id"], row["outer_id"]) for row in loaded]
    require(len(actual) == len(set(actual)) and set(actual) | {(row["case_id"], row["outer_id"]) for row in failed} == expected_ids,
            "interval outer denominator does not reconcile")
    for row in loaded:
        require(row["request_sha256"] == request_identity(requests)
                and len(row["inner"]) == inner
                and [draw["draw_id"] for draw in row["inner"]] == list(range(inner))
                and sorted(row["completed_inner_ids"] + row["error_inner_ids"]) == list(range(inner)),
                "interval draw denominator or request identity differs")
    summaries = interval_summaries(loaded, requests, expected_outer)
    primary = [row for row in summaries if row["primary"]]
    require(len(primary) == 4, "interval nomination requires exactly four declared primary cells")
    complete = not failed and all(row["status"] == "complete" for row in loaded)
    decision = ("incomplete" if not complete else
                "uncertainty_failed" if any(row["refit"]["coverage"]["status"] == "failed" for row in primary) else
                "uncertainty_inconclusive" if any(row["refit"]["coverage"]["status"] == "inconclusive" for row in primary) else
                "nominate_broad_shape")
    primary_rules = [dict(case=row["case"], case_id=row["case_id"], key=row["key"], request=row["request"],
                          **(row["refit"]["coverage"] if row["refit"] is not None else
                             dict(covered=None, n=expected_outer, rate=None, wilson=None, status="incomplete",
                                  reason="missing_outer_intervals"))) for row in primary]
    result = artifact("attribution_recovery_intervals", document["purpose"],
                      dict(prepared=identity(prepared_path), means=identity(means_path),
                           source_prepared=document["source_prepared"], basis=document["basis"],
                           model_protocol=document["model_protocol"], requests=document["requests"]),
                      prepared=identity(prepared_path), means=identity(means_path),
                      source_prepared=document["source_prepared"], basis=document["basis"],
                      basis_sha256=document["basis_sha256"],
                      model_protocol=document["model_protocol"], requests=document["requests"],
                      request_sha256=request_identity(requests), outers=outers, error_outer_ids=failed,
                      expected_outer_per_case=expected_outer, expected_inner=inner,
                      expected_histories=2 * expected_outer * inner,
                      completed_histories=sum(len(row["completed_inner_ids"]) for row in loaded),
                      error_histories=sum(len(row["error_inner_ids"]) for row in loaded),
                      unavailable_histories=len(failed) * inner,
                      summaries=summaries, primary=primary, status="complete" if complete else "incomplete",
                      recommendation=decision, gate=dict(status="incomplete" if not complete else
                          "supported" if decision == "nominate_broad_shape" else
                          "failed" if decision == "uncertainty_failed" else "inconclusive",
                          rules=primary_rules), admission="not_admitted", handoff=None,
                      resources=dict(**resources(started), process_seconds=time.process_time() - process_started,
                                     worker_process_seconds=sum(row["resources"]["process_seconds"] for row in loaded),
                                     maximum_worker_memory_bytes=max((row["resources"]["peak_memory_bytes"] for row in loaded), default=0),
                                     workers=workers, numerical_threads_per_worker=1))
    write_json(output / "intervals.json", json_values(result))
    return identity(output / "intervals.json")


def _passed_stage(path, kind, prepared_reference, prepared_document):
    document = read_artifact(path, kind)
    require(document['prepared'] == prepared_reference
            and document['source_prepared'] == prepared_document['source_prepared']
            and document['model_protocol'] == prepared_document['model_protocol']
            and document['basis_sha256'] == prepared_document['basis_sha256']
            and document['request_sha256'] == prepared_document['request_sha256']
            and document['purpose'] == prepared_document['purpose'],
            'stage source/model/basis/request identity differs from preparation')
    require(document['status'] == 'complete' and document['gate']['status'] == 'supported',
            'dependent stage requires complete supported prerequisites')
    require(len(document['gate']['rules']) == (8 if kind == 'attribution_recovery_means' else 4)
            and all(row['status'] == 'supported' for row in document['gate']['rules']),
            'dependent stage requires every named rule supported')
    if document['purpose'] == 'research':
        require(document['implementation'] == prepared_document['implementation'],
                'prerequisite stage producer differs from frozen model')
    protocol = read_artifact(linked_path(prepared_document['model_protocol']), 'attribution_recovery_protocol')
    count = protocol['budgets']['outer_per_case']
    expected_ids = {(case, outer) for case in range(2) for outer in range(count)}
    actual_ids = [(row['case_id'], row['outer_id']) for row in document['outers']]
    require(len(actual_ids) == len(set(actual_ids)) and set(actual_ids) == expected_ids
            and document['expected_outer_per_case'] == count, 'supported stage outer denominator differs')
    if kind == 'attribution_recovery_means':
        require({tuple(row) for row in document['completed_ids']} == expected_ids
                and len(document['completed_ids']) == len(expected_ids) and not document['incomplete_ids']
                and document['numerical_resolution']['status'] == 'passed',
                'supported mean stage has incomplete execution or numerical checks')
    else:
        histories = 2 * count * protocol['budgets']['inner_refits']
        require(document['expected_histories'] == document['completed_histories'] == histories
                and document['expected_inner'] == protocol['budgets']['inner_refits']
                and document['error_histories'] == document['unavailable_histories'] == 0
                and not document['error_outer_ids'], 'supported interval history denominator differs')
    return document


def fit_real(prepared: Path | str, means: Path | str, intervals: Path | str, out: Path | str) -> dict:
    from hockey_stats.attribution import (
        bounded_shape_resolution_check, compare_negative_rates, context_mean, map_mean,
        read_control_annual, read_native_04b_fits, write_recovery_annual,
    )
    from hockey_stats.attribution_data import load_grouped_population, read_revision_prepared, weighted_population
    from hockey_stats.attribution_uncertainty import RefitInputs, exact_duplicate_groups, fit_history
    from hockey_stats.artifacts import rows

    started, process_started = time.monotonic(), time.process_time()
    prepared_path, means_path, intervals_path = [Path(value).resolve(strict=True) for value in (prepared, means, intervals)]
    document, protocol, basis, _ = read_prepared(prepared_path)
    if document['purpose'] == 'research':
        require(implementation() == protocol['implementation'], 'real producer differs from frozen model protocol')
    prepared_reference = identity(prepared_path)
    mean_document = _passed_stage(means_path, 'attribution_recovery_means', prepared_reference, document)
    interval_document = _passed_stage(intervals_path, 'attribution_recovery_intervals', prepared_reference, document)
    require(interval_document['means'] == identity(means_path)
            and mean_document['numerical_resolution']['status'] == 'passed',
            'real fit requires the same supported mean and refit history')
    source_path = linked_path(document['source_prepared'])
    source = read_revision_prepared(source_path)
    diagnosis = read_artifact(linked_path(document['diagnosis']), 'attribution_recovery_diagnosis')
    old_fits, old_states = read_native_04b_fits(linked_path(diagnosis['old_evidence']['fits']))
    old_assessment = read_json(linked_path(diagnosis['old_evidence']['assessment']))
    output = output_path(str(out), [str(path.parent) for path in (prepared_path, means_path, intervals_path)])
    require(output.is_relative_to(Path(protocol['output_root'])), 'real output differs from frozen root')
    output.mkdir()
    populations = {('unblocked_spatial', season): load_grouped_population(source_path, 'unblocked_spatial', season)
                   for season in SEASONS}
    groups = exact_duplicate_groups(populations, list(SEASONS), benchmarks=('unblocked_spatial',))
    inputs = RefitInputs(dict(seasons=list(SEASONS)), protocol, populations, document['source_prepared'], groups, 'recorded')
    weights = {season: np.ones(len(populations[('unblocked_spatial', season)][0].game_ids)) for season in SEASONS}
    receipt, states = fit_history(inputs, [], benchmarks=('unblocked_spatial',), game_multipliers=weights,
        representation='graph_40ft', basis=basis, model_protocol_sha256=document['model_protocol']['sha256'],
        prior_policy='history')
    W, _ = shape_regions()
    annual, probes, replay, diagnostics, arrays = [], [], [], [], {}
    previous_path = previous_state = None
    controls = {(row['benchmark'], row['season']): row['state'] for row in source['baseline_controls']}
    for year, season in enumerate(SEASONS):
        key = ('unblocked_spatial', season)
        if key not in states:
            break
        state, native = states[key], old_states[key]
        require(state.player_ids == native.player_ids and state.current_player_ids == native.current_player_ids
                and state.entrant_ids == native.entrant_ids and state.carried_only_ids == native.carried_only_ids
                and state.r == native.r and np.array_equal(state.u, native.u) and np.array_equal(state.p, native.p)
                and np.array_equal(state.response_counts, native.response_counts),
                'real chain changed original source references or player chronology')
        volume_errors = {field: _close(getattr(state.volume, field), getattr(native.volume, field),
                         'real spatial volume replay differs')
                         for field in ('M', 'V', 'A', 'prior_mean', 'prior_covariance')}
        volume_errors['selected_variance'] = _close(state.volume.scale['selected']['variance'],
            native.volume.scale['selected']['variance'], 'real volume scale replay differs')
        accounting = dict(map_to_volume=_close(map_mean(state).sum(1), state.volume.M[:, 0], 'real map-volume accounting failed'),
            context_to_volume=_close(context_mean(state).sum(1), state.volume.A[:, 0], 'real context-volume accounting failed'))
        n = len(state.player_ids)
        for role, offset in (('offense', 0), ('defense', n)):
            accounting[role + '_centering'] = _close(state.u @ map_mean(state)[offset:offset+n],
                np.zeros(656), 'real player centering failed')
        source_row = next(row for row in source['annual'] if (row['population'], row['season']) == key)
        original_control = read_control_annual(linked_path(controls[key]))
        negative = compare_negative_rates(state, native, original_control,
                                          rows(linked_path(source_row['rows'])), source_row['strata'])
        require(all(value['rows'] == source_row['row_count'] and value['team_seconds'] == source_row['team_seconds']
                    for value in negative.values()), 'real diagnostic count/time differs from original source population')
        expected = next(row for row in old_assessment['annual'] if (row['benchmark'], row['season']) == key)
        for name, field in (('native_04b', 'revision_negative_rates'), ('native_04a', 'control_negative_rates')):
            saved = expected[field]
            for count in ('rows', 'negative_complete_rates', 'negative_cell_rates'):
                require(negative[name][count] == saved[count], 'historical strict sign diagnostic changed')
            for field_name in ('team_seconds', 'minimum_complete_rate', 'minimum_cell_rate',
                'exposure_weighted_negative_complete_frequency', 'exposure_weighted_negative_cell_frequency', 'negative_mass'):
                _close(negative[name][field_name], saved[field_name], 'historical diagnostic arithmetic changed')
            for example in ('minimum_complete_example', 'minimum_cell_example'):
                actual_example, expected_example = negative[name][example], saved[example]
                require({k:v for k,v in actual_example.items() if k != 'rate'}
                        == {k:v for k,v in expected_example.items() if k != 'rate'}, 'historical extremum locator changed')
                _close(actual_example['rate'], expected_example['rate'], 'historical extremum rate changed')
        probe = None
        if year in (0, 4):
            positions = {player: i for i, player in enumerate(state.player_ids)}
            requested = []
            for role, offset in (('offense', 0), ('defense', n)):
                for player in (8476460, 8478398, 8480336, 8480800):
                    if player not in state.current_player_ids:
                        continue
                    c = np.zeros(2*n)
                    c[offset + positions[player]] = 1
                    for vector in W.T:
                        requested.append((c, vector, 'shape'))
            grouped, references = populations[key]
            population = weighted_population(grouped, weights[season], references)
            probe = bounded_shape_resolution_check(population, previous_state, state, regions=W, projections=tuple(requested))
            probes.append(dict(year=year+1, **probe))
        annual_ref = write_recovery_annual(state, prepared_path, previous_path,
            output / season, source_kind='recorded', control_replay=volume_errors, resolution_check=probe)
        annual.append(dict(season=season, state=annual_ref))
        replay.append(dict(season=season, volume=volume_errors, accounting=accounting,
                           all_attempts_control=next(row['state'] for row in old_fits['annual']
                               if row['benchmark'] == 'all_attempts' and row['season'] == season)))
        diagnostics.append(dict(season=season, source_rows=source_row['rows'], source_reference=source_row['references'],
            recorded_count=source_row['total_count'], matched_team_seconds=source_row['team_seconds'], models=negative))
        previous_path, previous_state = linked_path(annual_ref), state
    examples = []
    if ('unblocked_spatial', SEASONS[-1]) in states:
        state = states[('unblocked_spatial', SEASONS[-1])]
        positions = {player: i for i, player in enumerate(state.player_ids)}
        for role, offset in (('offense', 0), ('defense', len(positions))):
            for player in (8476460, 8478398, 8480336, 8480800):
                prefix = f'{role}_{player}'
                if player not in state.current_player_ids:
                    examples.append(dict(role=role, player_id=player, status='unavailable', reason='player_not_currently_observed'))
                    continue
                from hockey_stats.attribution import project_native
                c = np.zeros(2*len(positions))
                c[offset+positions[player]] = 1
                for estimand in ('shape', 'complete_rate'):
                    values = project_native(state, c, estimand=estimand)
                    for field in ('mean', 'lower', 'upper'):
                        arrays[f'{prefix}_{estimand}_{field}'] = values[field]
                examples.append(dict(role=role, player_id=player, status='available', array_prefix=prefix,
                    meaning='research point association; working intervals condition on sources, references, basis and selected scales'))
    complete = receipt['status'] == 'complete' and len(annual) == 5 and len(probes) == 2 and all(p['status'] == 'verified' for p in probes)
    if receipt['status'] != 'complete':
        reason = 'real_point_chain_failed'
    elif len(annual) != 5:
        reason = 'incomplete_annual_point_chain'
    elif not complete:
        reason = 'bounded_numerical_resolution_failed_or_incomplete'
    else:
        reason = 'complete_point_chain_and_bounded_resolution'
    result = artifact('attribution_recovery_real', document['purpose'],
        dict(prepared=prepared_reference, source_prepared=document['source_prepared'], model_protocol=document['model_protocol'],
             means=identity(means_path), intervals=identity(intervals_path), baseline_fits=diagnosis['old_evidence']['fits']),
        prepared=prepared_reference, source_prepared=document['source_prepared'], model_protocol=document['model_protocol'],
        basis=document['basis'], basis_sha256=document['basis_sha256'], request_sha256=document['request_sha256'],
        means=identity(means_path), intervals=identity(intervals_path), annual=annual,
        status='complete' if complete else 'incomplete', reason=reason, error=receipt['error'], scalar_volume_replay=replay,
        native_diagnostics=diagnostics, numerical_resolution=probes, point_examples=examples,
        real_refit_intervals=None, scope='research point associations; additive complete-rate inadequacy remains visible',
        admission='not_admitted', handoff=None,
        resources=dict(**resources(started), process_seconds=time.process_time()-process_started),
        **(write_arrays(output, 'real.npz', arrays) if arrays else {}))
    write_json(output / 'real.json', json_values(result))
    return identity(output / 'real.json')

def _point_diagnostics(means: dict, prepared: dict, designs: list[dict]) -> dict:
    from hockey_stats.attribution_uncertainty import request_key

    W, _ = shape_regions()
    expected = means['expected_outer_per_case']
    requests = read_json(linked_path(prepared['requests']))
    by_key = {request_key(request): request for request in requests}
    estimates, truths, complete_maps, metrics, transition_rows = {}, {}, {}, {}, {}
    ids = []
    for reference in means['outers']:
        outer = read_artifact(linked_path(reference['manifest']), 'attribution_recovery_mean_outer')
        key = (reference['case_id'], reference['outer_id'])
        require(key == (outer['case_id'], outer['outer_id']) and key not in ids
                and outer['prepared'] == means['prepared'] and outer['model_protocol'] == means['model_protocol']
                and outer['basis_sha256'] == means['basis_sha256'] and outer['request_sha256'] == means['request_sha256'],
                'point diagnostic dataset or representation identity differs')
        ids.append(key)
        if outer['status'] != 'complete':
            continue
        arrays = load_arrays(outer)
        for year in (1, 5):
            for contrast in ('radial', 'lateral', 'local', 'rough'):
                truth = arrays[f'truth_{year}_{contrast}_shape']
                complete_truth = arrays[f'truth_{year}_{contrast}_complete']
                for representation in ('graph_40ft', 'native_04b'):
                    group = (key[0], year, contrast, representation)
                    require(group not in truths or np.array_equal(truths[group], truth), 'point diagnostic truth changed')
                    truths[group] = truth
                    estimates.setdefault(group, []).append(arrays[f'{representation}_{year}_{contrast}_shape'])
                    complete_maps.setdefault(group, []).append((arrays[f'{representation}_{year}_{contrast}_complete'], complete_truth))
                    metric = [row for row in outer['error_metrics'] if row['year'] == year
                              and row['contrast'] == contrast and row['representation'] == representation]
                    require(len(metric) == 1, 'point diagnostic error record is missing or duplicated')
                    metrics.setdefault(group, []).append(metric[0])
        for row in outer['projections']['graph_40ft']:
            request = by_key[row['key']]
            if request['group'] in ('annual_transition', 'volume'):
                transition_rows.setdefault((key[0], row['key']), []).append(row)
    patterns = []
    for group, values in sorted(estimates.items()):
        case_id, year, contrast, representation = group
        truth = truths[group]
        fitted = np.stack(values)
        error_rows = metrics[group]
        maps = complete_maps[group]
        full_truth = maps[0][1]
        full_estimates = np.stack([row[0] for row in maps])
        shape_native = shape_recovery(fitted, truth)
        shape_regions_result = shape_recovery(fitted @ W, truth @ W)
        complete_native = shape_recovery(full_estimates, full_truth)
        patterns.append(dict(case=CASES[case_id], year=year, contrast=contrast, representation=representation,
            expected_outer=expected, observed_outer=len(values), status='complete' if len(values) == expected else 'incomplete',
            shape_native=shape_native, shape_regions=shape_regions_result, complete_native=complete_native,
            complete_zero_baseline_native_squared_error=float(full_truth @ full_truth),
            same_fitted_volume_only_native_squared_error=float(np.mean([
                row['same_fitted_volume_only_native_squared_error'] for row in error_rows])),
            shape_rmse_native=float(np.sqrt(shape_native['mean_squared_error'])),
            shape_rmse_regions=float(np.sqrt(shape_regions_result['mean_squared_error'])),
            complete_rmse_native=float(np.sqrt(complete_native['mean_squared_error']))))
    transitions = []
    for (case_id, key), rows in sorted(transition_rows.items()):
        request = by_key[key]
        truth = truth_for_request(designs, request)
        require(all(row['truth'] == truth for row in rows), 'transition truth changed from fixed design')
        errors = np.array([row['mean']-truth for row in rows])
        entry = dict(case=CASES[case_id], key=key, request={name:value for name,value in request.items() if name != 'weights'},
                     expected_outer=expected, observed_outer=len(rows), truth=truth,
                     units='attempts per 60 team minutes', status='complete' if len(rows) == expected else 'incomplete',
                     point_bias=float(errors.mean()), point_rmse=float(np.sqrt(np.mean(errors**2))),
                     interval_recovery='see refit stage; point diagnostics do not establish coverage')
        if request['estimand'] == 'volume':
            fraction = scalar_truth_fraction(designs[SEASONS.index(request['season'])], request['role'], request['coefficients'])
            entry.update(exact_relative_truth=[fraction.numerator,fraction.denominator], relative_truth=float(fraction),
                         meaningful_scalar_band=.05, scalar_nomination=None)
        transitions.append(entry)
    return dict(patterns=patterns, transitions_and_matched_volume=transitions,
                expected_outer_per_case=expected, observed_datasets=len(ids),
                estimands='actual shape and complete rates; geometric projected truth is not the assessment target')


def _recovery_figures(diagnosis: dict, means: dict | None, intervals: dict | None,
                      real: dict | None, prepared: dict | None, output: Path, reason: str) -> list[dict]:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    from hockey_stats.attribution import read_shape_basis

    centers = grid()[0]
    purpose_label = 'fixture exercise / ' if diagnosis['purpose'] == 'fixture_exercise' else 'research / '
    figures = []
    saved = load_arrays(diagnosis)

    def draw_map(ax, values, limit, title):
        image = ax.scatter(centers[:, 0], centers[:, 1], c=values, cmap='coolwarm',
                           vmin=-limit, vmax=limit, marker='s', s=9, linewidths=0, rasterized=True)
        ax.set(xlim=(-100, 100), ylim=(-43, 43), aspect='equal', title=title)
        ax.set_xlabel('rink x (ft)')
        ax.set_ylabel('rink y (ft)')
        ax.tick_params(labelsize=7)
        return image

    fig = plt.figure(figsize=(15, 14), layout='constrained')
    layout = GridSpec(6, 3, figure=fig, height_ratios=[1, 1, 1, 1, 1.4, 1.3])
    selections = [(case, pattern) for case in CASES for pattern in ('broad', 'local')]
    limit = max(float(np.max(np.abs(saved[f'{case}_{pattern}_5_{suffix}'])))
                for case, pattern in selections for suffix in ('truth', 'mean_shape', 'bias'))
    map_axes = []
    for row, (case, pattern) in enumerate(selections):
        for column, (suffix, label) in enumerate((('truth', 'actual truth'), ('mean_shape', 'outer-mean fitted shape'), ('bias', 'bias'))):
            ax = fig.add_subplot(layout[row, column])
            image = draw_map(ax, saved[f'{case}_{pattern}_5_{suffix}'], limit, f'{case} / {pattern} / year 5 / {label}')
            map_axes.append(ax)
    fig.colorbar(image, ax=map_axes, shrink=.5, label='shape contrast: attempts/60 team minutes')
    ax = fig.add_subplot(layout[4, :2])
    x = np.arange(4)
    selected_errors = [row for row in diagnosis['native_error_decomposition'] if row['year'] == 5 and row['estimator'] == 'revision']
    for offset, (field, label) in enumerate((('volume_native_squared_error', 'volume'), ('shape_native_squared_error', 'shape'), ('cross_term', 'cross term'))):
        values = [np.mean([row[field] for row in selected_errors if row['case'] == case and row['contrast'] == pattern])
                  for case, pattern in selections]
        ax.bar(x + (offset-1)*.24, values, width=.24, label=label)
    ax.axhline(0, color='black', linewidth=.6)
    ax.set_xticks(x, [f'{case}\n{pattern}' for case, pattern in selections])
    ax.set_ylabel('mean native squared error contribution\n(squared attempts/60 team minutes)')
    ax.set_title('complete-map error = volume + shape + signed cross term')
    ax.legend(fontsize=8)
    ax = fig.add_subplot(layout[4, 2])
    gate = diagnosis['gate']['cases']
    for index, row in enumerate(gate):
        ax.bar(index-.17, row['regions']['bias_squared'], width=.34, color='#35647a', label='squared bias' if index == 0 else None)
        ax.bar(index+.17, row['regions']['sampling_variation'], width=.34, color='#b35b32', label='variation' if index == 0 else None)
    ax.set_xticks(range(len(gate)), [row['case'] for row in gate])
    ax.set_yscale('log')
    ax.set_ylabel('twelve-region squared shape error (log scale)')
    ax.set_title('broad year-five diagnosis')
    ax.legend(fontsize=8)
    ax = fig.add_subplot(layout[5, :])
    ax.axis('off')
    weighted = diagnosis['weighted_scale_evidence']
    lines = []
    for case in CASES:
        point = [row for row in diagnosis['point_scale_evidence'] if row['case'] == case and row['block'] == 'shape' and row['year'] == 5]
        refit = next(row for row in weighted if row['case'] == case and row['block'] == 'shape' and row['year'] == 5)
        endpoints = sum('endpoint_winner' in row['own_reasons'] for row in point)
        inherited = sum(row['inherited_limitation'] for row in point)
        quantiles = refit['selected_variance_quantiles']
        lines.append(f"{case}: shape point endpoints {endpoints}/{len(point)}, inherited flags {inherited}/{len(point)}; "
                     f"weighted innovation variance median {quantiles['median']:.4g}, 2.5–97.5% {quantiles['q025']:.4g}–{quantiles['q975']:.4g}.")
        peak = next(row for row in diagnosis['shape_interval_evidence'] if row['case'] == case
                    and row['contrast'] == 'broad' and row['year'] == 5 and row['functional'].startswith('max_true_shape_cell_'))
        lines.append(f"shape-only peak intervals (n={peak['n']}): working width {peak['working']['mean_width']:.4g}, "
                     f"center − truth {peak['working']['mean_center_minus_truth']:.4g}; basic width {peak['refit']['mean_width']:.4g}, "
                     f"center − truth {peak['refit']['mean_center_minus_truth']:.4g} attempts/60 team minutes.")
    ax.text(0, .95, '\n'.join(lines) + '\n\nall saved years 1 and 5 are reconciled in the diagnosis artifact. maps above are outer means, not individual fits.\n'
            'original complete-rate intervals and their joint shape-only projections are reported separately.\n'
            'different point and weighted optima alone do not establish a bug. bias domination does not prove pooling repairs it.',
            transform=ax.transAxes, va='top', fontsize=9, linespacing=1.5)
    fig.suptitle(purpose_label + '04c diagnosis: saved native-04b spatial recovery', fontsize=15)
    path = output / 'diagnosis.png'
    fig.savefig(path, dpi=150)
    plt.close(fig)
    figures.append(dict(name='diagnosis', reference=identity(path)))

    fig = plt.figure(figsize=(15, 9), layout='constrained')
    recovery_layout = GridSpec(2, 2, figure=fig, height_ratios=[4, 1], width_ratios=[1.35, 1])
    axes = [fig.add_subplot(recovery_layout[0, column]) for column in range(2)]
    footer = fig.add_subplot(recovery_layout[1, :])
    footer.axis('off')
    if means is None or not means['gate']['rules']:
        axes[0].axis('off')
        status = 'not_run' if means is None else 'incomplete'
        axes[0].text(.05, .75, f'mean recovery: {status}\n{reason}', transform=axes[0].transAxes, fontsize=12)
    else:
        rules = means['gate']['rules']
        for index, row in enumerate(rules):
            lower, upper = row['percentile_95']
            axes[0].plot([lower, upper], [index, index], color='#35647a', linewidth=2)
            axes[0].plot(row['mean_gain'], index, 'o', color='#163c50')
        axes[0].set_yticks(range(len(rules)), [f"{row['case']} / {row['contrast']} / {row['baseline']}\n{row['status']} (n={row['n']})" for row in rules])
        axes[0].axvline(0, color='black', linewidth=.8)
        axes[0].invert_yaxis()
        axes[0].set_xlabel('baseline − graph shape squared error\nsquared attempts/60 team minutes; paired percentile 95% intervals')
        axes[0].set_title('eight primary shape-error comparisons' + (' / stage incomplete' if means['status'] != 'complete' else ''))
    if intervals is None:
        axes[1].axis('off')
        axes[1].text(.05, .8, f'refit recovery: not_run\n{reason}\n\nnominal intervals: .95 pointwise\ndevelopmental coverage floor: .90\n\ntransition, local, rough and exact-null\ninterval diagnostics: not_run',
                     transform=axes[1].transAxes, fontsize=11, linespacing=1.5)
    else:
        rules = intervals['gate']['rules']
        for index, row in enumerate(rules):
            if row['wilson'] is None:
                continue
            lower, upper = row['wilson']
            axes[1].plot([lower, upper], [index, index], color='#35647a', linewidth=2)
            axes[1].plot(row['rate'], index, 'o', color='#163c50')
        axes[1].set_yticks(range(len(rules)), [f"{row['case']} / {row['request']['functional']}\n{row['status']} ({row['covered']}/{row['n']})" for row in rules])
        axes[1].set_xlim(0, 1.01)
        axes[1].axvline(.90, color='#b35b32', linestyle='--', label='.90 developmental floor')
        axes[1].axvline(.95, color='#555555', linestyle=':', label='.95 nominal pointwise')
        axes[1].set_xlabel('coverage of actual truth; two-sided 95% wilson intervals')
        axes[1].set_title('four primary coverage cells')
        axes[1].legend(fontsize=8)
    if intervals is None:
        secondary = f'transition, local, rough and exact-null refit diagnostics: not_run / {reason}'
    else:
        lines = []
        for group, display in (('annual_transition', 'entry/return'), ('local', 'local'), ('rough', 'rough'), ('exact_null', 'inseparable individuals/difference')):
            selected = [row for row in intervals['summaries'] if
                        (row['request']['group'] == group if group in ('annual_transition', 'exact_null')
                         else group in row['request']['name'])]
            counts = Counter('not_data_identified' if row['status'] == 'not_data_identified' else
                row['refit']['coverage']['status'] if row['refit'] is not None else 'incomplete' for row in selected)
            lines.append(display + ': ' + ', '.join(f'{count} {status}' for status, count in sorted(counts.items())))
        secondary = f"secondary diagnostic cells (n={intervals['expected_outer_per_case']} outer datasets per cell):\n" + '\n'.join(lines)
    if real is not None:
        secondary += '\nreal points: positive offense means creation; positive defense means opponent creation; no real refit intervals.'
    footer.text(0, .95, secondary + '\nsecondary cells describe limitations; they do not change the four-cell nomination.',
                transform=footer.transAxes, va='top', fontsize=9, linespacing=1.4)
    fig.suptitle(purpose_label + '04c recovery: directional gains and pointwise uncertainty', fontsize=15)
    path = output / 'recovery.png'
    fig.savefig(path, dpi=150)
    plt.close(fig)
    figures.append(dict(name='recovery', reference=identity(path)))

    point = None
    if means is not None:
        selected = [row['manifest'] for row in means['outers'] if row['case_id'] == 0 and row['outer_id'] == 0]
        if len(selected) == 1:
            outer = read_artifact(linked_path(selected[0]), 'attribution_recovery_mean_outer')
            if outer['status'] == 'complete':
                point = load_arrays(outer)
    if point is None:
        fig, ax = plt.subplots(figsize=(10, 4), layout='constrained')
        ax.axis('off')
        fig.suptitle(purpose_label + '04c representation limits', fontsize=14)
        status = 'not_run' if means is None else 'incomplete'
        ax.text(.05, .8, f'representation examples: {status}\n{reason}\n\nno complete gaussian outer-zero final-year state is available.', transform=ax.transAxes, fontsize=12)
    else:
        basis = read_shape_basis(prepared)
        patterns = ('radial', 'lateral', 'local', 'rough')
        maps = []
        for pattern in patterns:
            truth = point[f'truth_5_{pattern}_shape']
            projected = (truth @ basis.B) @ basis.R.T
            fitted = point[f'graph_40ft_5_{pattern}_shape']
            maps.append((truth, projected, fitted))
        real_rows = real is not None and real['status'] == 'complete'
        fig = plt.figure(figsize=(15, 15 if real_rows else 11), layout='constrained')
        layout = GridSpec(6 if real_rows else 4, 12, figure=fig)
        limit = max(float(np.max(np.abs(values))) for row in maps for values in row)
        axes = []
        for row, (pattern, values) in enumerate(zip(patterns, maps, strict=True)):
            for column, (name, array) in enumerate(zip(('actual truth', 'geometric projection', 'one fitted pattern'), values, strict=True)):
                ax = fig.add_subplot(layout[row, 4*column:4*(column+1)])
                image = draw_map(ax, array, limit, f'{pattern} / {name}')
                axes.append(ax)
        fig.colorbar(image, ax=axes, shrink=.5, label='shape contrast: attempts/60 team minutes')
        if real_rows:
            real_arrays = load_arrays(real)
            real_limit = max((float(np.max(np.abs(real_arrays[row['array_prefix']+'_shape_mean'])))
                              for row in real['point_examples'] if row['status'] == 'available'), default=1.)
            for role_index, role in enumerate(('offense', 'defense')):
                for column, player in enumerate((8476460, 8478398, 8480336, 8480800)):
                    ax = fig.add_subplot(layout[4+role_index, 3*column:3*(column+1)])
                    row = next(row for row in real['point_examples'] if row['role'] == role and row['player_id'] == player)
                    if row['status'] == 'available':
                        real_image = draw_map(ax, real_arrays[row['array_prefix']+'_shape_mean'], real_limit,
                                              f'{role} / {player} / research point')
                    else:
                        ax.axis('off')
                        ax.text(.05, .6, f'{role} / {player}\nunavailable', transform=ax.transAxes)
            if any(row['status'] == 'available' for row in real['point_examples']):
                fig.colorbar(real_image, ax=fig.axes[-8:], shrink=.5, label='real point shape association: attempts/60 team minutes')
        title = purpose_label + '04c representation limits: gaussian outer zero, year five\n40-foot nominal wavelength; actual truth remains the assessment target; no real refit intervals'
        if real_rows:
            title += '\nreal points: positive offense means creation; positive defense means opponent creation'
        fig.suptitle(title, fontsize=14)
    path = output / 'representation-limits.png'
    fig.savefig(path, dpi=150)
    plt.close(fig)
    figures.append(dict(name='representation_limits', reference=identity(path)))
    return figures


def assess(diagnosis: Path | str, out: Path | str, *, prepared=None, means=None, intervals=None, real=None) -> dict:
    started, process_started = time.monotonic(), time.process_time()
    diagnosis_path = Path(diagnosis).resolve(strict=True)
    diagnosed = read_artifact(diagnosis_path, 'attribution_recovery_diagnosis')
    require(diagnosed['status'] == 'complete', 'assessment requires a reconciled diagnosis')
    paths = {name: Path(value).resolve(strict=True) for name, value in
             (('prepared',prepared),('means',means),('intervals',intervals),('real',real)) if value is not None}
    require('prepared' in paths or not any(name in paths for name in ('means','intervals','real')),
            'later stages require their explicit preparation')
    require('means' in paths or not any(name in paths for name in ('intervals','real')),
            'later stages require their explicit mean pilot')
    require('intervals' in paths or 'real' not in paths, 'real point stage requires explicit refit evidence')
    documents, protocol, prepared_document = {}, None, None
    stages = dict(diagnosis=dict(status='complete', reason=diagnosed['gate']['reason']))
    recommendation = 'incomplete'
    complete, stopping_reason = False, 'assigned_model_stages_not_completed'
    nomination = None
    if diagnosed['gate']['status'] == 'stop':
        require(not paths, 'diagnosis stop cannot consume unreached model stages')
        complete, recommendation, stopping_reason = True, 'mechanism_not_supported', 'mechanism_not_supported'
    elif 'prepared' in paths:
        prepared_document, protocol, _, designs = read_prepared(paths['prepared'])
        require(prepared_document['diagnosis'] == identity(diagnosis_path)
                and prepared_document['source_prepared'] == diagnosed['source_prepared']
                and prepared_document['purpose'] == diagnosed['purpose'], 'assessment preparation differs from diagnosis')
        stages['prepared'] = dict(status='complete', reason='fixed_basis_and_truth_bound_before_responses')
        for name, kind in (('means','attribution_recovery_means'),('intervals','attribution_recovery_intervals'),('real','attribution_recovery_real')):
            if name not in paths:
                break
            document = read_artifact(paths[name], kind)
            require(document['prepared'] == identity(paths['prepared'])
                    and document['source_prepared'] == prepared_document['source_prepared']
                    and document['model_protocol'] == prepared_document['model_protocol']
                    and document['basis_sha256'] == prepared_document['basis_sha256']
                    and document['request_sha256'] == prepared_document['request_sha256']
                    and document['purpose'] == prepared_document['purpose'], 'assessment stage source/model/request identity differs')
            if document['purpose'] == 'research':
                require(document['implementation'] == protocol['implementation'],
                        'saved model stage producer differs from frozen protocol')
            if name == 'intervals':
                _passed_stage(paths['means'], 'attribution_recovery_means', identity(paths['prepared']), prepared_document)
                require(document['means'] == identity(paths['means']), 'refit stage differs from its supported matched mean pilot')
            if name == 'real':
                _passed_stage(paths['intervals'], 'attribution_recovery_intervals', identity(paths['prepared']), prepared_document)
                require(document['intervals'] == identity(paths['intervals'])
                        and document['means'] == identity(paths['means']), 'real stage was not reached by supported matched refits')
            documents[name] = document
            stages[name] = dict(status=document['status'], reason=document['reason'] if name == 'real' else document['recommendation'])
        mean_document = documents.get('means')
        interval_document = documents.get('intervals')
        real_document = documents.get('real')
        if mean_document is not None and mean_document['status'] == 'complete':
            mean_status = mean_document['gate']['status']
            if mean_status in ('failed','inconclusive'):
                require(interval_document is None and real_document is None, 'mean stop cannot consume later evidence')
                complete, recommendation = True, 'mean_recovery_'+mean_status
                stopping_reason = recommendation
            elif interval_document is not None and interval_document['status'] == 'complete':
                interval_status = interval_document['gate']['status']
                if interval_status in ('failed','inconclusive'):
                    require(real_document is None, 'uncertainty stop cannot consume a real fit')
                    complete, recommendation = True, 'uncertainty_'+interval_status
                    stopping_reason = recommendation
                elif interval_status == 'supported':
                    _passed_stage(paths['means'], 'attribution_recovery_means', identity(paths['prepared']), prepared_document)
                    _passed_stage(paths['intervals'], 'attribution_recovery_intervals', identity(paths['prepared']), prepared_document)
                    nomination = 'nominate_broad_shape'
                    complete = real_document is not None and real_document['status'] == 'complete'
                    recommendation = nomination if complete else 'incomplete'
                    stopping_reason = ('conditional_real_point_stage_complete' if complete else
                        real_document['reason'] if real_document is not None else 'conditional_real_point_stage_not_run')
        for name in ('means','intervals'):
            if name in documents and documents[name]['status'] != 'complete':
                stopping_reason = name+'_execution_or_numerical_incomplete'
    for name in ('prepared','means','intervals','real'):
        if name not in stages:
            stages[name] = dict(status='not_run', reason=stopping_reason)
    rule_matrix = []
    for phase, count in (('means',8),('intervals',4)):
        if phase in documents:
            rules = documents[phase]['gate']['rules']
            require(len(rules) == count or documents[phase]['status'] == 'incomplete', 'assessment rule matrix denominator differs')
            rule_matrix.extend(dict(phase=phase, **rule) for rule in rules)
        else:
            rule_matrix.append(dict(phase=phase, status='not_run', reason=stages[phase]['reason'], expected_rules=count))
    output = output_path(str(out), [str(diagnosis_path.parent)] + [str(path.parent) for path in paths.values()])
    if diagnosed['purpose'] == 'research':
        require(output.is_relative_to(RESEARCH_ROOT), 'research assessment must remain external-only')
    output.mkdir()
    figures = _recovery_figures(diagnosed, documents.get('means'), documents.get('intervals'),
                               documents.get('real'), prepared_document, output, stopping_reason)
    point_diagnostics = (_point_diagnostics(documents['means'], prepared_document, designs)
                         if 'means' in documents else None)
    limitations = [
        'shape allocation is separated from attempt volume; directional gain is not a practical accuracy margin',
        '40 feet is a nominal basis wavelength, not demonstrated cell accuracy; omitted directions have no model variance',
        'original native shares remain estimated but conditioned on and can imprint texture',
        'refits vary fitted histories and scales, not sources, reference estimation, topology or cross-game dependence',
        'two offensive patterns do not validate every player, defense shape, entrant, local or rough signal',
        'nominal .95 pointwise intervals are assessed against a .90 developmental floor, not simultaneous calibration',
        'inseparable individual players and their difference remain not_data_identified',
        'native additive complete rates remain unconstrained; no clipping, intensity-model or causal claim',
        'new real-player refit intervals, source/deployment robustness and supported chance valuation remain pending',
        'no scientific result is a publication handoff',
    ]
    consumed = dict(diagnosis=identity(diagnosis_path), spec_snapshot=diagnosed['spec_snapshot'],
                    **{name:identity(path) for name,path in paths.items()})
    result = artifact('attribution_recovery_result', diagnosed['purpose'], consumed,
        model_implementation=None if protocol is None else protocol['implementation'],
        model_protocol=None if prepared_document is None else prepared_document['model_protocol'],
        spec_snapshot=diagnosed['spec_snapshot'], evidence={name:ref for name,ref in consumed.items() if name != 'spec_snapshot'},
        completion='complete' if complete else 'incomplete', stages=stages, rule_matrix=rule_matrix,
        recommendation=recommendation, nomination=nomination,
        claim_scope='developmental broad offensive relative-shape recovery under fixed synthetic assumptions',
        real_refit_intervals=None, figures=figures, figure_contracts=FIGURE_CONTRACTS,
        point_diagnostics=point_diagnostics,
        limitations=limitations, admission='not_admitted', handoff=None,
        costs={name:document['resources'] for name,document in
               [('diagnosis',diagnosed),*([('prepared',prepared_document)] if prepared_document is not None else []),*documents.items()]},
        resources=dict(**resources(started), process_seconds=time.process_time()-process_started))
    write_json(output / 'result.json', json_values(result))
    return identity(output / 'result.json')


def main() -> int:
    from hockey_stats.captures import InputContractError
    from hockey_stats.cli import Once

    parser = argparse.ArgumentParser(description="04c broad-shape recovery study", allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    fields = {
        "diagnose": ("baseline-result", "out"),
        "prepare": ("baseline-prepared", "diagnosis", "protocol", "out"),
        "pilot-means": ("prepared", "out"),
        "pilot-intervals": ("prepared", "means", "out"),
        "fit-real": ("prepared", "means", "intervals", "out"),
        "assess": ("diagnosis", "out"),
    }
    for command, names in fields.items():
        child = commands.add_parser(command, allow_abbrev=False)
        for name in names:
            child.add_argument("--" + name, required=True, action=Once)
        if command == "assess":
            for name in ("prepared", "means", "intervals", "real"):
                child.add_argument("--" + name, action=Once)
    args = parser.parse_args()
    try:
        if args.command == "diagnose":
            reference = diagnose(args.baseline_result, args.out)
        elif args.command == "prepare":
            reference = prepare(args.baseline_prepared, args.diagnosis, args.protocol, args.out)
        elif args.command == "pilot-means":
            reference = pilot_means(args.prepared, args.out)
        elif args.command == "pilot-intervals":
            reference = pilot_intervals(args.prepared, args.means, args.out)
        elif args.command == "fit-real":
            reference = fit_real(args.prepared, args.means, args.intervals, args.out)
        else:
            reference = assess(args.diagnosis, args.out, prepared=args.prepared, means=args.means,
                               intervals=args.intervals, real=args.real)
        print(reference["path"])
        return 0
    except (InputContractError, OSError, ValueError, np.linalg.LinAlgError) as error:
        print(f"{args.command} failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
