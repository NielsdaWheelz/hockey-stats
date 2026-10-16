"""the frozen 04b generator, nested recovery execution and prospective claim rules."""

from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from itertools import chain
import math
from pathlib import Path
import time

import numpy as np

from hockey_stats.artifacts import clean_implementation, implementation, json_values, linked_path, require, resources, write_json
from hockey_stats.attribution_simulation import synthetic_designs
from hockey_stats.attribution_uncertainty import (
    RefitInputs, basic_interval, exact_duplicate_groups, project_requests, refit_history,
    request_key, meaningful_claim,
)
from hockey_stats.chance_cli import identity, output_path
from hockey_stats.chance_evaluation import REGION_NAMES, compound_regions
from hockey_stats.shot_origins import grid

SEASONS = tuple(f"{year}{year + 1}" for year in range(2021, 2026))
CASES = ("gaussian", "game_pace")


def native_designs(p: np.ndarray) -> list[dict]:
    """known centered truths on every native cell; no response-derived reference."""
    centers, _ = grid()
    p = np.asarray(p, dtype=float)
    require(p.shape == (656,) and np.isfinite(p).all() and np.all(p > 0)
            and abs(float(p.sum()) - 1) <= 1e-12, "synthetic native shares must be positive and normalized")
    order = np.lexsort((np.arange(len(p)), np.sum((centers - [89, 0]) ** 2, axis=1)))
    stop = int(np.searchsorted(np.cumsum(p[order]), .5, side="left")) + 1
    broad = -np.ones(len(p))
    broad[order[:stop]] = 1
    local = (np.exp(-np.sum((centers - [80, 15]) ** 2, axis=1) / 200)
             - np.exp(-np.sum((centers - [80, -15]) ** 2, axis=1) / 200))
    shapes = []
    for g in (broad, local):
        centered = g - p @ g
        shapes.append(.10 * p * centered / np.max(np.abs(centered)))
    years = synthetic_designs()["paired"]
    for year in years:
        n = len(year["players"])
        scalar = year["scalar_ticks"].astype(float) / 40
        shape = np.zeros((2 * n, len(p)))
        positions = {player: i for i, player in enumerate(year["players"])}
        shape[positions[3]], shape[positions[4]] = shapes[0], -shapes[0]
        shape[positions[18]], shape[positions[19]] = shapes[1], -shapes[1]
        for offset in (0, n):
            scalar[offset:offset + n] -= year["u"] @ scalar[offset:offset + n]
            shape[offset:offset + n] -= year["u"] @ shape[offset:offset + n]
        truth_map = scalar[:, None] * p + shape
        mu = np.column_stack((40 * (p + year["X"] @ truth_map),
                              15 * (1 + year["X"] @ scalar)))
        require(np.isfinite(mu).all() and np.all(mu > 0),
                "native generating rates must be positive without clipping or redrawing")
        require(np.max(np.abs(truth_map.sum(axis=1) - scalar)) <= 1e-14,
                "native truth map does not sum to centered scalar truth")
        year.update(truth_scalar=scalar, truth_shape=shape, truth_map=truth_map, mu=mu, p=p.copy())
    return years


def scalar_truth_fraction(design: dict, role: str, coefficients) -> Fraction:
    """integer exposure/tick algebra preserves the strict zero/five/ten-percent boundaries."""
    positions = {player: i for i, player in enumerate(design["players"])}
    n = len(positions)
    offset = n if role == "defense" else 0
    exposures = design["player_exposure"].astype(np.int64)
    require(np.array_equal(exposures, design["player_exposure"]), "synthetic exposure must retain exact seconds")
    ticks = design["scalar_ticks"][offset:offset + n]
    center = Fraction(sum(int(e) * int(t) for e, t in zip(exposures, ticks, strict=True)),
                      40 * sum(int(e) for e in exposures))
    return sum((coefficient * (Fraction(int(ticks[positions[player]]), 40) - center)
                for player, coefficient in coefficients), Fraction(0))


def scalar_truth(design: dict, role: str, coefficients) -> float:
    return float(scalar_truth_fraction(design, role, coefficients))


def synthetic_counts(design: dict, case_id: int, outer_id: int, year_index: int) -> np.ndarray:
    """separate response streams in sorted game/stint/direction/native-cell order."""
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([40420, case_id, outer_id, year_index])))
    means = design["e"][:, None] * design["mu"]
    if CASES[case_id] == "gaussian":
        variance = design["e"][:, None] * np.concatenate((40 * design["p"], [15]))
        return rng.normal(means, np.sqrt(variance))
    counts = np.empty_like(means)
    for game in range(96):
        pace = rng.gamma(shape=2, scale=.5)
        counts[100 * game:100 * (game + 1)] = rng.poisson(pace * means[100 * game:100 * (game + 1)])
    return counts


def wilson(successes: int, total: int) -> list[float] | None:
    if total == 0:
        return None
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    half = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return [center - half, center + half]


def coverage_support(covered: int, total: int) -> dict:
    interval = wilson(covered, total)
    status = ("supported" if interval[0] >= .90 else "failed" if interval[1] < .90 else "inconclusive")
    return dict(covered=covered, n=total, rate=covered / total, wilson=interval, status=status,
                nominal_coverage=.95, developmental_floor=.90)


def false_claims(theta: Fraction | float, lower: float, upper: float) -> dict:
    """one union event per replicate; a true five-percent boundary is not detection power."""
    band = Fraction(1, 20) if isinstance(theta, Fraction) else .05
    claim = meaningful_claim(lower, upper)
    values = dict(positive_zero_exclusion=lower > 0 and theta <= 0,
                  negative_zero_exclusion=upper < 0 and theta >= 0,
                  meaningful_positive=claim == "meaningful_positive" and theta <= band,
                  meaningful_negative=claim == "meaningful_negative" and theta >= -band,
                  within_meaningful_band=claim == "within_meaningful_band" and abs(theta) > band)
    return dict(**{key: bool(value) for key, value in values.items()}, any_false_claim=any(values.values()))


def false_claim_support(count: int, total: int) -> dict:
    interval = wilson(count, total)
    return dict(count=count, n=total, rate=count / total, wilson=interval,
                status="supported" if interval[1] <= .10 else "failed" if interval[0] > .10 else "inconclusive",
                developmental_ceiling=.10)


def recovery_requests() -> list[dict]:
    """frozen contrasts; native requests retain joint cell draws for regional projection."""
    requests = []
    for year in (0, 4):
        for name, pair in (("broad", (3, 4)), ("local", (18, 19))):
            requests.append(dict(name=name, benchmark="unblocked_spatial", season=SEASONS[year],
                                 role="offense", coefficients=[[pair[0], 1], [pair[1], -1]],
                                 functional="native", negate=False))
    scalar = [(4, "offense", [[2, 1], [5, -1]], "pair_2_minus_5", "volume"),
              (4, "offense", [[6, 1], [2, -1]], "pair_6_minus_2", "volume"),
              (4, "offense", [[7, 1], [2, -1]], "pair_7_minus_2", "volume"),
              (2, "offense", [[32, 1]], "entrant_32_offense", "annual_transition"),
              (2, "defense", [[33, 1]], "entrant_33_defense", "annual_transition"),
              (3, "offense", [[8, 1]], "returner_8_offense", "annual_transition")]
    for year in (0, 4):
        scalar += [(year, "offense", [[26, 1], [31, 1]], "pair_26_plus_31", "paired_sum"),
                   (year, "offense", [[26, 1], [31, -1]], "pair_26_minus_31", "exact_null")]
    for year in range(5):
        scalar += [(year, "offense", [[26, 1]], "player_26", "exact_null"),
                   (year, "offense", [[31, 1]], "player_31", "exact_null")]
    for benchmark in ("all_attempts", "unblocked_spatial"):
        for year, role, coefficients, name, group in scalar:
            requests.append(dict(name=name, benchmark=benchmark, season=SEASONS[year], role=role,
                                 coefficients=coefficients, functional="scalar", negate=False, group=group))
    return requests


def _synthetic_populations(designs: list[dict], case_id: int, outer_id: int,
                           protocol_sha: str) -> dict:
    from hockey_stats.attribution_data import AnnualReferences, group_observations

    populations = {}
    for year, design in enumerate(designs):
        counts = synthetic_counts(design, case_id, outer_id, year)
        for benchmark in ("all_attempts", "unblocked_spatial"):
            responses = counts.sum(axis=1, keepdims=True) if benchmark == "all_attempts" else counts[:, :656]
            references = AnnualReferences(benchmark, SEASONS[year], year, protocol_sha,
                f"synthetic:04b:{case_id}:{outer_id}:{benchmark}", design["players"], design["strata"],
                55. if benchmark == "all_attempts" else 40., design["u"].copy(),
                None if benchmark == "all_attempts" else design["p"].copy(),
                design["player_exposure"].copy(), responses.sum(axis=0))
            rows = (dict(game_id=int(design["row_game_ids"][index]),
                         offense=design["offense"][index], defense=design["defense"][index],
                         seconds=float(design["seconds"][index]),
                         stratum=design["strata"][int(design["si"][index])], counts=responses[index])
                    for index in range(len(responses)))
            populations[(benchmark, SEASONS[year])] = (group_observations(rows, references, design["game_ids"]),
                                                      references)
    return populations


def _base_chains(inputs: RefitInputs) -> tuple[dict, dict, dict | None]:
    from hockey_stats.attribution import fit_revision_year, fit_shared_volume_control
    from hockey_stats.attribution_data import weighted_population
    from hockey_stats.captures import InputContractError

    revision, control = {}, {}
    for benchmark in ("all_attempts", "unblocked_spatial"):
        previous_revision = previous_control = None
        for season in inputs.document["seasons"]:
            grouped, references = inputs.populations[(benchmark, season)]
            try:
                population = weighted_population(grouped, np.ones(len(grouped.game_ids)), references)
                previous_revision = fit_revision_year(population, previous_revision)
                revision[(benchmark, season)] = previous_revision
                previous_control = fit_shared_volume_control(population, previous_control)
                control[(benchmark, season)] = previous_control
            except (InputContractError, np.linalg.LinAlgError, FloatingPointError) as error:
                return revision, control, dict(benchmark=benchmark, season=season, error=str(error))
    return revision, control, None


def _project_chains(states: dict, requests: list[dict], groups: dict) -> dict:
    result = {}
    for (benchmark, season), state in states.items():
        selected = [request for request in requests
                    if request["benchmark"] == benchmark and request["season"] == season]
        for row in project_requests(state, selected, groups[(benchmark, season)]):
            result[row["key"]] = row
    return result


def _state_artifacts(states: dict, prefix: str, arrays: dict) -> list[dict]:
    annual = []
    for (benchmark, season), state in states.items():
        record = dict(benchmark=benchmark, season=season, player_ids=state.player_ids,
                      current_player_ids=state.current_player_ids, entrant_ids=state.entrant_ids,
                      carried_only_ids=state.carried_only_ids, r=state.r)
        for name in ("volume", "shape"):
            block = getattr(state, name)
            if block is None:
                record[name] = None
                continue
            key = f"{prefix}_{benchmark}_{season}_{name}"
            for field in ("M", "V", "A", "prior_mean", "prior_covariance"):
                arrays[f"{key}_{field}"] = getattr(block, field)
            record[name] = dict(array_prefix=key, a=block.a, q=block.q,
                                scale=block.scale, diagnostics=block.diagnostics)
        arrays[f"{prefix}_{benchmark}_{season}_u"] = state.u
        if state.p is not None:
            arrays[f"{prefix}_{benchmark}_{season}_p"] = state.p
        annual.append(record)
    return annual


def _short_annual(annual: list[dict]) -> list[dict]:
    result = []
    for row in annual:
        reduced = {key: row[key] for key in ("benchmark", "season", "status")}
        if row["status"] != "complete":
            reduced["error"] = row["error"]
        else:
            for name in ("volume", "shape"):
                reduced[name] = (None if row[name] is None else
                    {key: row[name]["scale"][key] for key in
                     ("status", "selected", "own_reasons", "inherited_limitation")})
                if reduced[name] is not None:
                    reduced[name]["numerical"] = {key: row[name]["diagnostics"][key] for key in (
                        "equation_relative_residual", "original_mean_equation_relative_residual",
                        "original_covariance_equation_relative_residual", "covariance_rounding_tolerance",
                        "centered_covariance_symmetry", "centered_mean_residual")}
        result.append(reduced)
    return result


def _cell_records(case_id: int, designs: list[dict], requests: list[dict], base: dict,
                  control: dict, inner_values: dict, complete: bool) -> list[dict]:
    regions = compound_regions(grid()[0])
    records = []
    for request in requests:
        key = request_key(request)
        row, old = base[key], control[key]
        year = SEASONS.index(request["season"])
        design = designs[year]
        r = row["r"]
        ratio = scalar_truth_fraction(design, request["role"], request["coefficients"])
        if request["functional"] == "native":
            positions = {player: i for i, player in enumerate(design["players"])}
            truth_map = r * sum((coefficient * design["truth_map"][positions[player]]
                                for player, coefficient in request["coefficients"]), np.zeros(656))
            peak = int(np.argmax(np.abs(truth_map)))
            functionals = [(f"peak_cell_{peak}", np.eye(1, 656, peak).ravel(), peak)]
            functionals += [(name, (regions == index).astype(float), None)
                            for index, name in enumerate(REGION_NAMES)]
        else:
            truth_map = None
            functionals = [("scalar", None, None)]
        for functional, vector, cell in functionals:
            if functional == "scalar":
                truth = r * float(ratio)
                estimate = float(row["mean"])
                working = row["working"]
                old_working = old["working"]
                draws = inner_values.get(key, [])
                group = request["group"]
            elif cell is not None:
                truth, estimate = float(truth_map[cell]), float(row["mean"][cell])
                working = {name: float(row["working"][name][cell]) for name in ("mean", "lower", "upper")}
                old_working = {name: float(old["working"][name][cell]) for name in ("mean", "lower", "upper")}
                draws = [value[cell] for value in inner_values.get(key, [])]
                group = f"native_shape_{request['name']}"
            else:
                truth, estimate = float(truth_map @ vector), float(row["mean"] @ vector)
                region_request = dict(request, functional=functional)
                working = base[request_key(region_request)]["working"]
                old_working = control[request_key(region_request)]["working"]
                draws = [float(value @ vector) for value in inner_values.get(key, [])]
                group = f"native_shape_{request['name']}"
            refit = (basic_interval(estimate, np.asarray(draws))
                     if complete and row["status"] == "available" else None)
            nomination = (functional.startswith("peak_cell_") and year == 4 or
                case_id == 1 and functional == "scalar" and (
                    group == "annual_transition" and request["benchmark"] == "unblocked_spatial" or
                    group == "volume" and request["benchmark"] == "all_attempts" or
                    request["name"] == "pair_7_minus_2" and request["benchmark"] == "unblocked_spatial" or
                    request["name"] == "pair_26_plus_31" and year == 4
                    and request["benchmark"] == "unblocked_spatial"))
            record = dict(name=f"{CASES[case_id]}/{request['benchmark']}/{year + 1}/{request['name']}/{functional}",
                          case=CASES[case_id], benchmark=request["benchmark"], year=year + 1,
                          contrast=request["name"], role=request["role"], coefficients=request["coefficients"],
                          functional=functional, group=group, nomination=bool(nomination), truth=truth,
                          relative_truth=float(ratio) if functional == "scalar" else None,
                          exact_relative_truth=([ratio.numerator, ratio.denominator] if functional == "scalar" else None),
                          mean=estimate, bias=estimate - truth, r=r, identification=row["status"],
                          reason=row["reason"], working=working, control_working=old_working, refit=refit,
                          refit_reason=row["reason"] if row["status"] != "available" else
                          None if complete else "incomplete_inner_refit_set")
            if draws:
                record["raw_refit_spread"] = dict(minimum=float(np.min(draws)), maximum=float(np.max(draws)),
                                                quantile_025=float(np.quantile(draws, .025, method="linear")),
                                                quantile_975=float(np.quantile(draws, .975, method="linear")), draws=len(draws))
            if functional == "scalar":
                record["false_claims"] = (None if refit is None else
                    false_claims(ratio, float(refit["lower"] / r), float(refit["upper"] / r)))
                record["working_false_claims"] = (false_claims(ratio, working["lower"] / r, working["upper"] / r)
                                                  if row["status"] == "available" else None)
                record["meaningful_claim"] = (None if refit is None else
                    meaningful_claim(float(refit["lower"] / r), float(refit["upper"] / r)))
            records.append(record)
    return records


def _map_metrics(designs: list[dict], revision: dict, control: dict) -> tuple[list[dict], dict]:
    from hockey_stats.attribution import project, project_native

    metrics, maps = [], {}
    for year, design in enumerate(designs):
        season = SEASONS[year]
        new, old = revision[("unblocked_spatial", season)], control[("unblocked_spatial", season)]
        positions = {player: i for i, player in enumerate(new.player_ids)}
        all_new, all_old = [], []
        for role, offset in (("offense", 0), ("defense", len(new.player_ids))):
            for player in design["players"]:
                c = np.zeros(2 * len(new.player_ids))
                c[offset + positions[player]] = 1
                all_new.append(project_native(new, c)["mean"] / 40)
                all_old.append(project_native(old, c)["mean"] / 40)
        all_new, all_old = np.asarray(all_new), np.asarray(all_old)
        error_new, error_old = all_new - design["truth_map"], all_old - design["truth_map"]
        metrics.append(dict(year=year + 1, contrast="all_current_players", unit="mean squared attempts/60 native map norm",
                            revision=float(1600 * np.sum(error_new ** 2) / len(all_new)),
                            control=float(1600 * np.sum(error_old ** 2) / len(all_old)),
                            revision_relative=float(np.sum(error_new ** 2) / len(all_new)),
                            control_relative=float(np.sum(error_old ** 2) / len(all_old))))
        maps[f"all_player_bias_{season}"] = error_new
        maps[f"all_player_control_bias_{season}"] = error_old
        for benchmark, rate in (("all_attempts", 55.), ("unblocked_spatial", 40.)):
            new_state, old_state = revision[(benchmark, season)], control[(benchmark, season)]
            state_positions = {player: index for index, player in enumerate(new_state.player_ids)}
            scalar_errors, old_scalar_errors = [], []
            for role in ("offense", "defense"):
                offset = len(new_state.player_ids) if role == "defense" else 0
                for player in design["players"]:
                    c = np.zeros(2 * len(new_state.player_ids))
                    c[offset + state_positions[player]] = 1
                    truth = rate * scalar_truth(design, role, [[player, 1]])
                    v = np.ones(1 if benchmark == "all_attempts" else 656)
                    scalar_errors.append(project(new_state, c, v)[0] - truth)
                    old_scalar_errors.append(project(old_state, c, v)[0] - truth)
            maps[f"all_player_scalar_{benchmark}_{season}_error"] = np.asarray(scalar_errors)
            maps[f"all_player_scalar_{benchmark}_{season}_control_error"] = np.asarray(old_scalar_errors)
        if year not in (0, 4):
            continue
        current = {player: i for i, player in enumerate(design["players"])}
        for name, (left, right) in (("broad", (3, 4)), ("local", (18, 19))):
            truth = design["truth_map"][current[left]] - design["truth_map"][current[right]]
            new_map, old_map = all_new[current[left]] - all_new[current[right]], all_old[current[left]] - all_old[current[right]]
            new_error, old_error = new_map - truth, old_map - truth
            c = np.zeros(2 * len(new.player_ids))
            c[positions[left]], c[positions[right]] = 1, -1
            true_volume = scalar_truth(design, "offense", [[left, 1], [right, -1]])
            metrics.append(dict(year=year + 1, contrast=name, unit="squared attempts/60 native map norm",
                revision=float(1600 * (new_error @ new_error)), control=float(1600 * (old_error @ old_error)),
                paired_reduction=float(1600 * (old_error @ old_error - new_error @ new_error)),
                truth_energy=float(1600 * (truth @ truth)), revision_normalized=float(new_error @ new_error / (truth @ truth)),
                control_normalized=float(old_error @ old_error / (truth @ truth)),
                revision_relative=float(new_error @ new_error), control_relative=float(old_error @ old_error),
                revision_pure_volume_error=float((project(new, c, np.ones(656))[0] - 40 * true_volume) ** 2),
                control_pure_volume_error=float((project(old, c, np.ones(656))[0] - 40 * true_volume) ** 2)))
            for kind, value in (("truth", truth), ("control", old_map), ("revision", new_map), ("error", new_error)):
                maps[f"{name}_{year + 1}_{kind}"] = 40 * value
    return metrics, maps


def _outer_recovery(designs: list[dict], protocol: dict, protocol_sha: str,
                    case_id: int, outer_id: int, output: Path) -> dict:
    started = time.monotonic()
    requests = recovery_requests()
    grouped = _synthetic_populations(designs, case_id, outer_id, protocol_sha)
    groups = exact_duplicate_groups(grouped, list(SEASONS))
    inputs = RefitInputs(dict(seasons=list(SEASONS)), protocol, grouped, None, groups)
    revised, controls, base_error = _base_chains(inputs)
    if base_error is not None:
        arrays = {}
        annual = dict(revision=_state_artifacts(revised, "revision", arrays),
                      control=_state_artifacts(controls, "control", arrays))
        array_path = output / f"{CASES[case_id]}-{outer_id:03d}.npz"
        with array_path.open("xb") as destination:
            np.savez(destination, **arrays)
        return dict(case=CASES[case_id], outer_id=outer_id, status="error", error=base_error,
                    arrays=identity(array_path), shapes={name: list(value.shape) for name, value in arrays.items()},
                    annual=annual, cells=[], map_metrics=[], inner_completed_ids=[], inner_error_ids=[],
                    completed_base_projections=list(_project_chains(revised, requests, groups).values()),
                    resources=resources(started))
    base_requests = list(requests)
    for request in requests:
        if request["functional"] == "native":
            base_requests.extend(dict(request, functional=name) for name in REGION_NAMES)
    base = _project_chains(revised, base_requests, groups)
    control = _project_chains(controls, base_requests, groups)
    arrays = {}
    annual = dict(revision=_state_artifacts(revised, "revision", arrays),
                  control=_state_artifacts(controls, "control", arrays))
    map_metrics, maps = _map_metrics(designs, revised, controls)
    arrays.update(maps)
    inner_values = {request_key(request): [] for request in requests}
    inner_ids = {request_key(request): [] for request in requests}
    completed, errors, diagnostics = [], [], []
    for draw_id in range(protocol["budgets"]["inner_refits"]):
        draw = refit_history(inputs, protocol, draw_id, requests, seed_prefix=[40421, case_id, outer_id])
        diagnostics.append(dict(draw_id=draw_id, status=draw["status"], error=draw["error"],
                                annual=_short_annual(draw["annual"]), seeds=draw["seeds"]))
        for season, weights in draw["weights"].items():
            arrays[f"weights_{draw_id}_{season}"] = weights
        if draw["status"] == "complete":
            completed.append(draw_id)
        else:
            errors.append(draw_id)
        for row in draw["projections"]:
            if row["mean"] is not None:
                inner_values[row["key"]].append(np.asarray(row["mean"]))
                inner_ids[row["key"]].append(draw_id)
    complete = not errors and len(completed) == protocol["budgets"]["inner_refits"]
    if complete:
        require(all(ids == list(range(protocol["budgets"]["inner_refits"])) for ids in inner_ids.values()),
                "complete recovery inner set omitted joint projection draws")
    projection_arrays = []
    for index, request in enumerate(requests):
        key = request_key(request)
        if inner_values[key]:
            arrays[f"inner_{index}"] = np.stack(inner_values[key])
            arrays[f"inner_ids_{index}"] = np.asarray(inner_ids[key], dtype=np.int64)
        projection_arrays.append(dict(request=request, array=f"inner_{index}" if inner_values[key] else None,
                                      draw_ids=f"inner_ids_{index}" if inner_values[key] else None))
    cells = _cell_records(case_id, designs, requests, base, control, inner_values, complete)
    null_rows = [row for row in cells if row["group"] == "exact_null"]
    null_correct = all(row["identification"] == "not_data_identified" and row["refit"] is None
                       and row["meaningful_claim"] is None for row in null_rows)
    require(null_correct, "synthetic exact-null contrast obtained an empirical claim")
    array_path = output / f"{CASES[case_id]}-{outer_id:03d}.npz"
    with array_path.open("xb") as destination:
        np.savez(destination, **arrays)
    return dict(case=CASES[case_id], outer_id=outer_id, status="complete" if complete else "error",
                error=None if complete else "incomplete_inner_refit_set", arrays=identity(array_path),
                shapes={name: list(value.shape) for name, value in arrays.items()},
                annual=annual, cells=cells, map_metrics=map_metrics,
                inner_completed_ids=completed, inner_error_ids=errors, inner_projections=projection_arrays,
                inner_diagnostics=diagnostics, null_handling=dict(status="passed", assessed=len(null_rows)),
                duplicate_groups=[dict(benchmark=benchmark, season=season, groups=values)
                                  for (benchmark, season), values in groups.items()], resources=resources(started))


def _coverage_summary(rows: list[dict], procedure: str, expected: int) -> dict:
    intervals = [row[procedure] for row in rows if row[procedure] is not None]
    covered = sum(row[procedure]["lower"] <= row["truth"] <= row[procedure]["upper"]
                  for row in rows if row[procedure] is not None)
    result = (coverage_support(covered, expected) if len(intervals) == expected else
              dict(covered=covered, n=expected, rate=None, wilson=None, status="inconclusive",
                   nominal_coverage=.95, developmental_floor=.90,
                   reason="not_data_identified" if rows[0]["identification"] == "not_data_identified" else
                   "incomplete_numerical_execution"))
    result.update(observed=len(intervals), mean_width=float(np.mean([value["upper"] - value["lower"]
                                                                   for value in intervals])) if intervals else None)
    return result


def summarize_recovery(outer: list[dict], protocol: dict) -> dict:
    """claim-by-claim denominators; diagnostics never enlarge the frozen nomination set."""
    expected = protocol["budgets"]["outer_per_case"]
    inner = protocol["budgets"]["inner_refits"]
    actual_ids = [(row["case"], row["outer_id"]) for row in outer]
    expected_ids = {(case, outer_id) for case in CASES for outer_id in range(expected)}
    require(len(actual_ids) == len(set(actual_ids)) and set(actual_ids) <= expected_ids,
            "recovery outer ids must be unique and within the frozen case/replicate budget")
    complete = (set(actual_ids) == expected_ids and all(row["status"] == "complete"
                and row["inner_completed_ids"] == list(range(inner)) for row in outer))
    bins = {}
    for record in outer:
        for cell in record["cells"]:
            bins.setdefault(cell["name"], []).append(cell)
    coverage, false_rows, matrix = [], [], []
    for name, cells in sorted(bins.items()):
        first = cells[0]
        summary = {key: first[key] for key in ("name", "case", "benchmark", "year", "contrast", "role",
            "coefficients", "functional", "group", "nomination", "truth", "relative_truth",
            "exact_relative_truth", "identification", "reason")}
        summary.update(working=_coverage_summary(cells, "working", expected),
                       control_working=_coverage_summary(cells, "control_working", expected),
                       refit=_coverage_summary(cells, "refit", expected),
                       bias=float(np.mean([row["bias"] for row in cells])),
                       rmse=math.sqrt(float(np.mean([row["bias"] ** 2 for row in cells]))),
                       control_bias=float(np.mean([row["control_working"]["mean"] - row["truth"] for row in cells])),
                       control_rmse=math.sqrt(float(np.mean([(row["control_working"]["mean"] - row["truth"]) ** 2
                                                            for row in cells]))))
        summary["working_interval_meaning"] = ("prior-conditioned diagnostic; not data identified"
            if first["identification"] == "not_data_identified" else "gaussian conditional working interval")
        coverage.append(summary)
        if summary["nomination"]:
            matrix.append(dict(name=name, group=summary["group"], rule="refit_coverage",
                               status=summary["refit"]["status"], evidence=summary["refit"]))
        if first["functional"] != "scalar":
            continue
        scalar = {key: summary[key] for key in ("name", "case", "benchmark", "year", "contrast", "group",
                                               "nomination", "relative_truth", "exact_relative_truth")}
        for procedure, field in (("refit", "false_claims"), ("working", "working_false_claims")):
            assertions = [row[field] for row in cells if row[field] is not None]
            count = sum(value["any_false_claim"] for value in assertions)
            result = (false_claim_support(count, expected) if len(assertions) == expected else
                      dict(count=count, n=expected, rate=None, wilson=None, status="inconclusive",
                           reason="not_data_identified" if first["identification"] == "not_data_identified" else
                           "incomplete_numerical_execution"))
            result.update(observed=len(assertions), components={key: sum(value[key] for value in assertions)
                          for key in ("positive_zero_exclusion", "negative_zero_exclusion", "meaningful_positive",
                                      "meaningful_negative", "within_meaningful_band")})
            scalar[procedure] = result
        available = [row for row in cells if row["refit"] is not None]
        scalar["usefulness"] = dict(n=expected, observed=len(available),
            zero_exclusion=sum(row["refit"]["lower"] > 0 or row["refit"]["upper"] < 0 for row in available),
            meaningful_separation=sum(row["meaningful_claim"] in ("meaningful_positive", "meaningful_negative")
                                      for row in available),
            near_zero_resolution=sum(row["meaningful_claim"] == "within_meaningful_band" for row in available),
            mean_relative_width=float(np.mean([(row["refit"]["upper"] - row["refit"]["lower"]) / row["r"]
                                               for row in available])) if available else None,
            interpretation="descriptive resolution at the exact declared truth; no universal power gate")
        false_rows.append(scalar)
        if summary["nomination"]:
            matrix.append(dict(name=name, group=summary["group"], rule="false_claim",
                               status=scalar["refit"]["status"], evidence=scalar["refit"]))
    shape_gains, error_metrics = [], []
    for case_id, case in enumerate(CASES):
        records = [row for row in outer if row["case"] == case]
        keys = sorted({(metric["year"], metric["contrast"]) for row in records for metric in row["map_metrics"]})
        for year, contrast in keys:
            values = [metric for row in records for metric in row["map_metrics"]
                      if metric["year"] == year and metric["contrast"] == contrast]
            error_metrics.append(dict(case=case, year=year, contrast=contrast, observed=len(values),
                n=expected, means={key: float(np.mean([value[key] for value in values])) for key in values[0]
                                   if key not in ("year", "contrast", "unit")}, unit=values[0]["unit"]))
        for contrast_id, contrast in enumerate(("broad", "local")):
            differences = np.asarray([metric["paired_reduction"] for row in records for metric in row["map_metrics"]
                                      if metric["year"] == 5 and metric["contrast"] == contrast])
            interval = None
            if len(differences) == expected:
                rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([40423, case_id, contrast_id])))
                draws = rng.integers(0, expected, size=(protocol["budgets"]["paired_error_resamples"], expected))
                interval = np.quantile(differences[draws].mean(axis=1), [.025, .975], method="linear").tolist()
            status = ("inconclusive" if interval is None else "supported" if interval[0] > 0 else
                      "failed" if interval[1] <= 0 else "inconclusive")
            row = dict(case=case, contrast=contrast, year=5, observed=len(differences), n=expected,
                mean_reduction=float(differences.mean()) if len(differences) else None,
                interval=interval, status=status, seed=[40423, case_id, contrast_id],
                resamples=protocol["budgets"]["paired_error_resamples"],
                unit="paired reduction in squared attempts/60 native map norm",
                reason=None if interval is not None else "incomplete_numerical_execution")
            shape_gains.append(row)
            matrix.append(dict(name=f"{case}/{contrast}/final_native_error_reduction", group=f"native_shape_{contrast}",
                               rule="shape_gain", status=status, evidence=row))
    nomination_coverage = [row for row in coverage if row["nomination"]]
    nomination_false = [row for row in false_rows if row["nomination"]]
    if complete:
        require(len(nomination_coverage) == 12 and len(nomination_false) == 8 and len(shape_gains) == 4,
                "frozen nomination cells differ from 12 coverage / 8 false-claim / 4 shape gains")
    null_records = [row for row in outer if "null_handling" in row]
    null_passed = (len(null_records) == 2 * expected
                   and all(row["null_handling"]["status"] == "passed" for row in null_records))
    if not complete:
        for row in coverage:
            for procedure in ("working", "control_working", "refit"):
                row[procedure].update(status="inconclusive", reason="incomplete_numerical_execution")
        for row in false_rows:
            for procedure in ("working", "refit"):
                row[procedure].update(status="inconclusive", reason="incomplete_numerical_execution")
        for row in shape_gains:
            row.update(status="inconclusive", reason="incomplete_numerical_execution")
        for row in matrix:
            row.update(status="inconclusive", reason="incomplete_numerical_execution")
    groups = []
    for group in ("native_shape_broad", "native_shape_local", "volume", "annual_transition", "paired_sum"):
        rules = [row for row in matrix if row["group"] == group]
        groups.append(dict(group=group, status="supported" if rules and all(row["status"] == "supported" for row in rules)
                           else "failed" if any(row["status"] == "failed" for row in rules) else "inconclusive",
                           rules=[row["name"] + "/" + row["rule"] for row in rules]))
    recommendation = None
    if complete:
        recommendation = ("nominate_revision" if null_passed and all(row["status"] == "supported" for row in matrix) else
                          "mixed" if any(row["status"] == "supported" for row in groups) else
                          "withheld" if any(row["status"] == "failed" for row in matrix) else "inconclusive")
    return dict(status="complete" if complete else "incomplete", support_matrix=matrix, shape_gains=shape_gains,
                coverage_cells=coverage, false_claim_cells=false_rows, error_metrics=error_metrics, claim_groups=groups,
                null_handling=dict(status="passed" if null_passed else "incomplete", outer_checked=len(null_records),
                                   expected_outer=2 * expected,
                                   meaning="individuals 26/31 and their difference retain prior-conditioned diagnostics only"),
                recommendation=recommendation)


def _outer_job(arguments: tuple) -> dict:
    """write each independent outer before returning it to the bounded process pool."""
    p, protocol, protocol_reference, prepared_reference, design_reference, case_id, outer_id, output = arguments
    current_implementation = implementation()
    if protocol["purpose"] == "research":
        clean_implementation(current_implementation)
        require(current_implementation == protocol["implementation"],
                "outer recovery implementation differs from frozen protocol")
    record = _outer_recovery(native_designs(p), protocol, protocol_reference["sha256"], case_id, outer_id, output)
    record.update(schema_version=2, kind="attribution_revision_outer_recovery", purpose=protocol["purpose"],
                  implementation=current_implementation, protocol=protocol_reference, prepared=prepared_reference,
                  design=design_reference, response_seeds=[[40420, case_id, outer_id, year] for year in range(5)])
    path = output / f"{CASES[case_id]}-{outer_id:03d}.json"
    write_json(path, json_values(record))
    return dict(record, reference=identity(path))


def simulate(prepared: Path | str, out: Path | str) -> dict:
    """execute the frozen two-case nested study; preserve each completed outer artifact."""
    from hockey_stats.attribution_data import load_grouped_population, read_revision_prepared
    from hockey_stats.chance_cli import read_json

    started = time.monotonic()
    prepared_path = Path(prepared).resolve(strict=True)
    document = read_revision_prepared(prepared_path)
    protocol = read_json(linked_path(document["protocol"]))
    current_implementation = implementation()
    if document["purpose"] == "research":
        clean_implementation(current_implementation)
        require(current_implementation == protocol["implementation"],
                "simulation implementation differs from frozen protocol")
    _, references = load_grouped_population(prepared_path, "unblocked_spatial", document["seasons"][0])
    designs = native_designs(references.p)
    output = output_path(str(out), [str(prepared_path.parent)])
    require(output.is_relative_to(Path(protocol["output_root"]).resolve()), "simulation output differs from frozen root")
    if document["purpose"] == "research":
        require(output.is_relative_to(Path("/Volumes/Expansion/hockey-stats")), "research simulation must remain external")
    output.mkdir()
    design_arrays = {f"year_{year}_{name}": design[name] for year, design in enumerate(designs)
                     for name in ("offense", "defense", "seconds", "si", "u", "scalar_ticks", "truth_scalar",
                                  "truth_map", "truth_shape", "player_exposure", "home_teams", "away_teams")}
    design_arrays.update(p=references.p, centers=grid()[0])
    design_path = output / "synthetic-design.npz"
    with design_path.open("xb") as destination:
        np.savez(destination, **design_arrays)
    design_document = dict(schema_version=2, kind="attribution_revision_synthetic_design", purpose=document["purpose"],
        implementation=implementation(), protocol=document["protocol"], prepared=identity(prepared_path),
        arrays=identity(design_path), shapes={name: list(value.shape) for name, value in design_arrays.items()},
        design_seed=40400, cases=list(CASES), row_order="sorted game/stint/away then home/native cell; blocked last",
        years=[dict(season=SEASONS[year], players=design["players"], strata=design["strata"],
                    minimum_generating_rate=float(design["mu"].min()), inventory_game_ids=design["game_ids"])
               for year, design in enumerate(designs)],
        references=dict(unblocked_rate=40, all_attempts_rate=55, p="fixed real first-season native shares",
                        u="known annual design exposure before counts"),
        truth_meaning="explicit synthetic centered recorded-rate association matrices; no raw captures",
        scalar_truth_unit="exact 1/40 ticks centered by integer player seconds before generating responses")
    write_json(output / "synthetic-design.json", json_values(design_document))
    outer_summaries, outer_refs, completed_ids, error_ids = [], [], [], []
    counts, inherited_counts = Counter(), Counter()
    exemplars = []
    descriptive_totals, descriptive_squares, descriptive_n = {}, {}, Counter()
    regions = compound_regions(grid()[0])
    jobs = [(references.p, protocol, document["protocol"], identity(prepared_path),
             identity(output / "synthetic-design.json"), case_id, outer_id, output)
            for case_id in range(2) for outer_id in range(protocol["budgets"]["outer_per_case"])]
    first = _outer_job(jobs[0])
    workers = min(4, len(jobs) - 1)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for record in chain([first], executor.map(_outer_job, jobs[1:], buffersize=4)):
            case, outer_id = record["case"], record["outer_id"]
            case_id = CASES.index(case)
            outer_refs.append(record["reference"])
            (completed_ids if record["status"] == "complete" else error_ids).append([case_id, outer_id])
            if "arrays" in record:
                with np.load(linked_path(record["arrays"]), allow_pickle=False) as arrays:
                    names = [name for name in arrays.files if name.startswith("all_player_")]
                    for name in names:
                        value = arrays[name]
                        key = (case, name)
                        descriptive_totals[key] = descriptive_totals.get(key, 0) + value
                        descriptive_squares[key] = descriptive_squares.get(key, 0) + value * value
                        descriptive_n[key] += 1
                        if name.startswith("all_player_bias_") or name.startswith("all_player_control_bias_"):
                            regional = 40 * np.column_stack([value[:, regions == index].sum(axis=1)
                                                            for index in range(len(REGION_NAMES))])
                            region_key = (case, name + "_regions")
                            descriptive_totals[region_key] = descriptive_totals.get(region_key, 0) + regional
                            descriptive_squares[region_key] = descriptive_squares.get(region_key, 0) + regional * regional
                            descriptive_n[region_key] += 1
                    for contrast in ("broad", "local") if record["status"] == "complete" else ():
                        for year in (1, 5):
                            for kind in ("revision", "control"):
                                value = arrays[f"{contrast}_{year}_{kind}"] - arrays[f"{contrast}_{year}_truth"]
                                key = (case, f"{contrast}_{year}_{kind}_map_error")
                                descriptive_totals[key] = descriptive_totals.get(key, 0) + value
                                descriptive_squares[key] = descriptive_squares.get(key, 0) + value * value
                                descriptive_n[key] += 1
            for draw in record.get("inner_diagnostics", []):
                for annual in draw["annual"]:
                    if annual["status"] == "complete":
                        for name in ("volume", "shape"):
                            if annual[name] is not None:
                                counts[(case, name, annual[name]["status"])] += 1
                                inherited_counts[(case, name)] += bool(annual[name]["inherited_limitation"])
            outer_summaries.append({key: record[key] for key in
                ("case", "outer_id", "status", "error", "cells", "map_metrics", "inner_completed_ids", "inner_error_ids")}
                | ({"null_handling": record["null_handling"]} if "null_handling" in record else {}))
            if outer_id == 0 and "arrays" in record and record["map_metrics"]:
                exemplars.append(dict(case=case, outer_id=0, arrays=record["arrays"],
                    maps=[dict(contrast=contrast, year=year,
                               truth=f"{contrast}_{year}_truth", control=f"{contrast}_{year}_control",
                               revision=f"{contrast}_{year}_revision", error=f"{contrast}_{year}_error")
                          for year in (1, 5) for contrast in ("broad", "local")]))
            print(f"{case} outer {outer_id}: {record['status']}; {record['resources']['wall_seconds']:.1f} seconds", flush=True)
    summary = summarize_recovery(outer_summaries, protocol)
    descriptive_arrays = {}
    for (case, name), total in descriptive_totals.items():
        descriptive_arrays[f"{case}_{name}_bias"] = total / descriptive_n[(case, name)]
        descriptive_arrays[f"{case}_{name}_rmse"] = np.sqrt(descriptive_squares[(case, name)] / descriptive_n[(case, name)])
    descriptive_path = output / "descriptive-recovery.npz"
    with descriptive_path.open("xb") as destination:
        np.savez(destination, **descriptive_arrays)
    summary.update(schema_version=2, kind="attribution_revision_recovery", purpose=document["purpose"],
        implementation=implementation(), protocol=document["protocol"], prepared=identity(prepared_path),
        generator=identity(output / "synthetic-design.json"), outer=outer_refs,
        completed_outer_ids=completed_ids, error_outer_ids=error_ids,
        expected_outer_per_case=protocol["budgets"]["outer_per_case"], inner_refits=protocol["budgets"]["inner_refits"],
        paired_error_resamples=protocol["budgets"]["paired_error_resamples"],
        execution=dict(workers=workers, worker_limit=4, buffered_jobs=4,
                       first_assigned_nested_trajectory=dict(case="gaussian", outer_id=0, resources=first["resources"]),
                       failure_policy="propagate worker failures; preserve completed outer artifacts; no replacement"),
        scale_statuses=[dict(case=case, block=block, status=status, count=count)
                        for (case, block, status), count in sorted(counts.items())],
        scale_searches=sum(counts.values()),
        unresolved_scale_searches=sum(count for (_, _, status), count in counts.items() if status == "scale_unresolved"),
        unresolved_scale_fraction=(sum(count for (_, _, status), count in counts.items() if status == "scale_unresolved")
                                   / sum(counts.values()) if counts else None),
        inherited_scale_limitations=[dict(case=case, block=block, count=count)
                                    for (case, block), count in sorted(inherited_counts.items())],
        figures_data=exemplars, coverage_unit="one independent outer replicate per named contrast/year/functional",
        descriptive_recovery=dict(arrays=identity(descriptive_path),
            shapes={name: list(value.shape) for name, value in descriptive_arrays.items()},
            counts=[dict(case=case, field=name, observed=count, n=protocol["budgets"]["outer_per_case"])
                    for (case, name), count in sorted(descriptive_n.items())],
            order=[dict(season=SEASONS[year], players=design["players"], roles=["offense", "defense"])
                   for year, design in enumerate(designs)], regions=list(REGION_NAMES),
            units=dict(native_all_player_bias="league-relative effect", scalar_and_regions="attempts per 60",
                       broad_local_map="attempts per 60"),
            meaning="point-estimate bias/rmse for all current players and fixed regions; no extra nomination gate"),
        interval_meaning="basic joint historical game-refit; conditional fixed references, not total ability uncertainty",
        resources=resources(started), admission="not_admitted", handoff=None)
    path = output / "simulation.json"
    write_json(path, json_values(summary))
    return identity(path)
