"""annual recorded-rate posterior with complete player covariance.

player columns are offense followed by defense. positive defense means more
opponent attempts. centering changes the coordinate system, not predictions.
response projections retain covariance; no cell/player independence shortcut.
"""

from dataclasses import dataclass
import math
from pathlib import Path
import time

import numpy as np
from scipy.linalg import cho_solve, solve_triangular
from scipy.optimize import minimize_scalar

from .artifacts import clean_implementation, implementation, linked_path, require, resources, rows, write_json
from .chance_cli import identity, output_path, read_json


@dataclass(frozen=True)
class AnnualPopulation:
    benchmark: str
    season: str
    season_index: int
    protocol_sha256: str
    population_id: str
    player_ids: tuple[int, ...]
    H: np.ndarray
    T: np.ndarray
    yy: float
    r: float
    xbar: np.ndarray
    ybar: np.ndarray
    stratum_weight: np.ndarray
    player_exposure: np.ndarray
    response_counts: np.ndarray


@dataclass(frozen=True)
class AnnualState:
    benchmark: str
    season: str
    season_index: int
    protocol_sha256: str
    population_id: str
    player_ids: tuple[int, ...]
    current_player_ids: tuple[int, ...]
    entrant_ids: tuple[int, ...]
    carried_only_ids: tuple[int, ...]
    M: np.ndarray
    V: np.ndarray
    S: np.ndarray
    A: np.ndarray
    r: float
    a: float
    q: float | None
    centering_weights: np.ndarray
    scale: dict
    diagnostics: dict
    prior_mean: np.ndarray
    prior_covariance: np.ndarray
    response_counts: np.ndarray


def _posterior(H: np.ndarray, T: np.ndarray, M0: np.ndarray,
               V0: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    """solve one proper prior using cholesky factors, retaining full covariance."""
    L = np.linalg.cholesky(V0)
    K = np.eye(len(H)) + L.T @ H @ L
    factor = np.linalg.cholesky(K)
    intermediate = solve_triangular(factor, L.T, lower=True, check_finite=False)
    U = solve_triangular(factor.T, intermediate, lower=False, check_finite=False)
    residual = float(np.linalg.norm(K @ U - L.T, ord=np.inf) /
                     (1 + np.linalg.norm(K, ord=np.inf) * np.linalg.norm(U, ord=np.inf)
                      + np.linalg.norm(L.T, ord=np.inf)))
    require(math.isfinite(residual) and residual <= 1e-8, "posterior equation residual exceeds 1e-8")
    V = intermediate.T @ intermediate
    M = M0 + V @ (T - H @ M0)
    require(np.isfinite(M).all() and np.isfinite(V).all(), "nonfinite annual posterior")
    symmetry = float(np.max(np.abs(V - V.T)))
    tolerance = float(1e-10 * max(1, np.linalg.norm(V, ord=np.inf)))
    require(symmetry <= tolerance, "posterior covariance is asymmetric")
    return M, V, dict(equation_relative_residual=residual, covariance_symmetry=symmetry,
                     covariance_rounding_tolerance=tolerance)


def fit_year(population: AnnualPopulation, previous_state: AnnualState | None) -> AnnualState:
    """fit one annual state; no mutation, future data, fallback or prior inversion."""
    started = time.monotonic()
    current = population.player_ids
    require(current == tuple(sorted(set(current))) and bool(current), "current player ids must be sorted and unique")
    require(population.benchmark in ("all_attempts", "unblocked_spatial"), "unknown attribution benchmark")
    require(type(population.season_index) is int and population.season_index >= 0, "invalid annual sequence index")
    require(type(population.season) is str and len(population.season) == 8 and population.season.isdigit()
            and int(population.season[4:]) == int(population.season[:4]) + 1,
            "annual season requires its eight-digit native identity")
    ncurrent, k = len(current), population.T.shape[1]
    h = len(population.stratum_weight)
    expected = {"H": (2*ncurrent, 2*ncurrent), "T": (2*ncurrent, k),
                "xbar": (h, 2*ncurrent), "ybar": (h, k), "stratum_weight": (h,),
                "player_exposure": (ncurrent,), "response_counts": (k,)}
    for name, shape in expected.items():
        value = getattr(population, name)
        require(isinstance(value, np.ndarray) and value.shape == shape and np.isfinite(value).all(),
                "invalid annual population array " + name)
    require((population.benchmark == "all_attempts" and k == 1)
            or (population.benchmark == "unblocked_spatial" and k in (4, 656)), "invalid response grid dimension")
    require(math.isfinite(population.yy) and math.isfinite(population.r) and population.r > 0
            and np.all(population.player_exposure > 0) and np.all(population.stratum_weight > 0),
            "annual population requires positive admitted exposure and reference rate")
    require(np.allclose(population.H, population.H.T, rtol=1e-10, atol=1e-10), "annual cross-product is asymmetric")
    if previous_state is None:
        require(population.season_index == 0, "later annual fit requires its immediately preceding state")
        players = current
        S = (np.ones((1, 1)) if k == 1 else np.diag(
            (population.response_counts + .5) / (population.response_counts.sum() + .5*k)))
        require(np.isfinite(S).all() and np.all(np.diag(S) > 0)
                and math.isclose(float(S.sum()), 1, rel_tol=1e-12, abs_tol=1e-12),
                "first-season response covariance is not a positive normalized shape")
    else:
        require(population.season_index == previous_state.season_index + 1
                and int(population.season[:4]) == int(previous_state.season[:4]) + 1
                and population.benchmark == previous_state.benchmark
                and population.protocol_sha256 == previous_state.protocol_sha256
                and population.population_id == previous_state.population_id
                and previous_state.M.shape[1] == k, "incompatible or nonconsecutive preceding annual state")
        players = tuple(sorted(set(previous_state.player_ids) | set(current)))
        S = previous_state.S.copy()
    n = len(players)
    index = {player: i for i, player in enumerate(players)}
    selected = np.array([index[player] for player in current] + [n + index[player] for player in current])
    H, T, xbar = np.zeros((2*n, 2*n)), np.zeros((2*n, k)), np.zeros((h, 2*n))
    H[np.ix_(selected, selected)] = population.H
    T[selected] = population.T
    xbar[:, selected] = population.xbar
    M0 = np.zeros((2*n, k))
    if previous_state is None:
        base_covariance = np.zeros((2*n, 2*n))
        innovation_indices = np.arange(2*n)
        entrants = current
    else:
        old = [index[player] for player in previous_state.player_ids]
        innovation_indices = np.array(old + [n + i for i in old])
        base_covariance = np.eye(2*n) * previous_state.a
        base_covariance[np.ix_(innovation_indices, innovation_indices)] = previous_state.V
        M0[innovation_indices] = previous_state.M
        entrants = tuple(player for player in current if player not in previous_state.player_ids)
    scalar_mean, scalar_T = M0.sum(axis=1), T.sum(axis=1)
    b = scalar_T - H @ scalar_mean
    zz = float(population.yy - 2 * scalar_mean @ scalar_T + scalar_mean @ H @ scalar_mean)
    curve = []

    def objective(exponent: float, phase: str = "refinement") -> float:
        variance = 10.0 ** float(exponent)
        covariance = base_covariance.copy()
        covariance[innovation_indices, innovation_indices] += variance
        error, solve_residual = None, None
        try:
            L = np.linalg.cholesky(covariance)
            K = np.eye(2*n) + L.T @ H @ L
            factor = np.linalg.cholesky(K)
            rhs = L.T @ b
            solution = cho_solve((factor, True), rhs, check_finite=False)
            solve_residual = float(np.linalg.norm(K @ solution - rhs, ord=np.inf) /
                (1 + np.linalg.norm(K, ord=np.inf) * np.linalg.norm(solution, ord=np.inf)
                 + np.linalg.norm(rhs, ord=np.inf)))
            if not math.isfinite(solve_residual) or solve_residual > 1e-8:
                error = "scale objective equation residual exceeds 1e-8"
            value = float(2 * np.log(np.diag(factor)).sum() + zz - rhs @ solution)
            if not math.isfinite(value):
                error = "nonfinite objective"
        except np.linalg.LinAlgError as failure:
            error, value = str(failure), math.inf
        curve.append(dict(exponent=float(exponent), variance=variance,
                          objective=value if error is None else None, phase=phase, error=error,
                          equation_relative_residual=solve_residual if solve_residual is not None and math.isfinite(solve_residual) else None))
        return value if error is None else math.inf

    coarse = [(float(exponent), objective(float(exponent), "coarse")) for exponent in np.arange(-8, .1, .5)]
    valid_interior = [(exponent, value) for exponent, value in coarse[1:-1] if math.isfinite(value)]
    refinement = None
    if valid_interior:
        best_exponent = min(valid_interior, key=lambda row: (row[1], row[0]))[0]
        fit = minimize_scalar(objective, bounds=(best_exponent - .5, best_exponent + .5), method="bounded",
                              options={"xatol": 1e-4, "maxiter": 40})
        refinement = dict(success=bool(fit.success), message=str(fit.message), evaluations=int(fit.nfev),
                          bounds=[best_exponent - .5, best_exponent + .5], exponent=float(fit.x) if math.isfinite(fit.x) else None)
    valid = [row for row in curve if row["objective"] is not None]
    require(bool(valid), "no valid numerical scale state; dependent chain stopped")
    winner = min(valid, key=lambda row: (row["objective"], row["variance"]))
    unresolved = []
    if winner["exponent"] in (-8, 0):
        unresolved.append("endpoint_winner")
    if refinement is None or not refinement["success"]:
        unresolved.append("refinement_failed")
    if any(row["phase"] == "refinement" and row["objective"] is None for row in curve):
        unresolved.append("nonfinite_refinement")
    covariance = base_covariance.copy()
    covariance[innovation_indices, innovation_indices] += winner["variance"]
    M, V, diagnostics = _posterior(H, T, M0, covariance)
    A = population.ybar - xbar @ M
    weights = np.zeros(n)
    weights[[index[player] for player in current]] = population.player_exposure
    weights /= weights.sum()
    off_mean, def_mean = weights @ M[:n], weights @ M[n:]
    M[:n] -= off_mean
    M[n:] -= def_mean
    A += 5 * (off_mean + def_mean)
    centered = np.empty_like(V)
    for start in (0, n):
        for stop in (0, n):
            block = V[start:start+n, stop:stop+n]
            left, right = weights @ block, block @ weights
            centered[start:start+n, stop:stop+n] = block - left[None, :] - right[:, None] + weights @ right
    V = centered
    symmetry = float(np.max(np.abs(V - V.T)))
    tolerance = float(1e-10 * max(1, np.linalg.norm(V, ord=np.inf)))
    require(symmetry <= tolerance and np.min(np.diag(V)) >= -tolerance, "invalid centered covariance")
    diagnostics.update(centered_covariance_symmetry=symmetry, covariance_rounding_tolerance=tolerance,
                       centered_mean_residual=float(max(np.max(np.abs(weights @ M[:n])), np.max(np.abs(weights @ M[n:])))),
                       resources=resources(started))
    inherited = previous_state is not None and previous_state.scale["status"] == "scale_unresolved"
    competing = [dict(exponent=exponent, objective=value) for i, (exponent, value) in enumerate(coarse)
                 if math.isfinite(value) and (i == 0 or value <= coarse[i-1][1])
                 and (i == len(coarse)-1 or value <= coarse[i+1][1])]
    scale = dict(status="scale_unresolved" if unresolved or inherited else "resolved",
                 own_reasons=unresolved, inherited_limitation=inherited, curve=curve,
                 competing_coarse_minima=competing, refinement=refinement, selected=dict(winner))
    return AnnualState(population.benchmark, population.season, population.season_index,
        population.protocol_sha256, population.population_id, players, current, entrants,
        tuple(player for player in players if player not in current), M, V, S, A, population.r,
        winner["variance"] if previous_state is None else previous_state.a,
        None if previous_state is None else winner["variance"], weights, scale, diagnostics,
        M0, covariance, population.response_counts.copy())


def contrast(state: AnnualState, player_contrast: np.ndarray,
             response_weights: np.ndarray) -> tuple[float, float]:
    """physical mean/variance for one joint player/response linear contrast."""
    c, v = np.asarray(player_contrast, dtype=float), np.asarray(response_weights, dtype=float)
    require(c.shape == (len(state.M),) and v.shape == (state.M.shape[1],)
            and np.isfinite(c).all() and np.isfinite(v).all(), "invalid attribution contrast dimensions")
    selected = np.flatnonzero(c)
    coefficients = c[selected]
    mean = float(state.r * coefficients @ state.M[selected] @ v)
    row_variance = float(coefficients @ state.V[np.ix_(selected, selected)] @ coefficients)
    variance = float(state.r**2 * row_variance * (v @ state.S @ v))
    tolerance = state.diagnostics["covariance_rounding_tolerance"] * state.r**2 * float(c @ c) * float(v @ v)
    require(math.isfinite(mean) and math.isfinite(variance) and variance >= -tolerance,
            "invalid attribution contrast variance")
    return mean, variance


def contrast_interval(state: AnnualState, player_contrast: np.ndarray,
                      response_weights: np.ndarray) -> dict:
    """pointwise interval with explicit, bounded covariance roundoff handling."""
    mean, variance = contrast(state, player_contrast, response_weights)
    c, v = np.asarray(player_contrast, dtype=float), np.asarray(response_weights, dtype=float)
    tolerance = state.diagnostics["covariance_rounding_tolerance"] * state.r**2 * float(c @ c) * float(v @ v)
    interval_variance = 0.0 if variance < 0 else variance
    half = 1.959963984540054 * math.sqrt(interval_variance)
    result = dict(mean=mean, variance=variance, lower=mean-half, upper=mean+half,
                  interval_variance=interval_variance, variance_rounded_to_zero=variance < 0,
                  variance_rounding_tolerance=tolerance)
    return result


def load_population(prepared_path: Path | str, benchmark: str, season: str) -> AnnualPopulation:
    """load one bound annual sufficient-statistic set; no pickle or row materialization."""
    path = Path(prepared_path).resolve(strict=True)
    document = read_json(path)
    require(type(document["schema_version"]) is int and document["schema_version"] == 1
            and document["kind"] == "attribution_prepared",
            "expected attribution prepared manifest")
    linked_path(document["protocol"])
    matches = [row for row in document["annual"] if row["population"] == benchmark and row["season"] == season]
    require(len(matches) == 1 and matches[0]["status"] == "prepared", "annual population unavailable")
    annual = matches[0]
    with np.load(linked_path(annual["arrays"]), allow_pickle=False) as arrays:
        require(set(arrays.files) == set(annual["shapes"]), "annual statistic array names differ")
        values = {name: arrays[name] for name in arrays.files}
    require(all(list(values[name].shape) == shape for name, shape in annual["shapes"].items()),
            "annual statistic shapes differ")
    return AnnualPopulation(benchmark, season, document["seasons"].index(season), document["protocol"]["sha256"],
                            document["population_ids"][benchmark], tuple(annual["players"]),
                            values["H"], values["T"], float(values["yy"]), annual["r"], values["xbar"],
                            values["ybar"], values["stratum_weight"], values["player_exposure"], values["response_counts"])


def read_annual(path: Path | str) -> AnnualState:
    """read a completed finite annual state and its bound arrays."""
    document = read_json(Path(path).resolve(strict=True))
    require(type(document["schema_version"]) is int and document["schema_version"] == 1
            and document["kind"] == "attribution_annual", "expected completed annual attribution state")
    linked_path(document["protocol"])
    linked_path(document["prepared"])
    if document["previous"] is not None:
        linked_path(document["previous"])
    prepared = read_json(linked_path(document["prepared"]))
    candidates = [row for row in prepared["annual"] if row["population"] == document["benchmark"]
                  and row["season"] == document["season"]]
    require(len(candidates) == 1, "saved annual population absent from preparation")
    annual = candidates[0]
    players, current = document["player_ids"], document["current_player_ids"]
    require(players == sorted(set(players)) and current == sorted(set(current))
            and set(current) <= set(players) and current == annual["players"]
            and document["carried_only_ids"] == sorted(set(players) - set(current))
            and document["strata"] == annual["strata"] and document["r"] == annual["r"]
            and document["season_index"] == prepared["seasons"].index(document["season"])
            and document["protocol"] == prepared["protocol"]
            and document["population_id"] == prepared["population_ids"][document["benchmark"]],
            "saved annual identity/order differs from its prepared population")
    n = len(players)
    k = 1 if document["benchmark"] == "all_attempts" else 656
    shapes = dict(M=[2*n, k], V=[2*n, 2*n], S=[k, k], A=[len(annual["strata"]), k],
                  centering_weights=[n], prior_mean=[2*n, k], response_counts=[k])
    require(document["shapes"] == shapes, "saved annual shapes disagree with its population")
    with np.load(linked_path(document["arrays"]), allow_pickle=False) as arrays:
        require(set(arrays.files) == set(shapes), "annual array names differ")
        values = {name: arrays[name] for name in arrays.files}
    for name, shape in shapes.items():
        require(list(values[name].shape) == shape and np.isfinite(values[name]).all(), "invalid saved annual array " + name)
    positions = {player: i for i, player in enumerate(players)}
    weights = np.zeros(n)
    with np.load(linked_path(annual["arrays"]), allow_pickle=False) as source_arrays:
        weights[[positions[player] for player in current]] = source_arrays["player_exposure"]
        require(np.array_equal(values["response_counts"], source_arrays["response_counts"]), "saved league counts differ")
    weights /= weights.sum()
    require(np.array_equal(weights, values["centering_weights"]), "saved centering exposure differs")
    require(math.isfinite(document["a"]) and 1e-8 <= document["a"] <= 1, "invalid saved initial variance")
    covariance = np.eye(2*n) * document["a"]
    if document["previous"] is None:
        expected_S = np.ones((1, 1)) if k == 1 else np.diag((values["response_counts"] + .5) /
            (values["response_counts"].sum() + .5*k))
        require(document["season_index"] == 0 and document["q"] is None and players == current
                and document["entrant_ids"] == current and np.all(values["prior_mean"] == 0)
                and np.array_equal(values["S"], expected_S)
                and document["a"] == document["scale"]["selected"]["variance"],
                "first annual state has incompatible prior")
    else:
        previous_document = read_json(linked_path(document["previous"]))
        require(previous_document["season_index"] + 1 == document["season_index"]
                and int(previous_document["season"][:4]) + 1 == int(document["season"][:4])
                and all(previous_document[key] == document[key]
                        for key in ("benchmark", "protocol", "population_id", "prepared", "a"))
                and math.isfinite(document["q"]) and 1e-8 <= document["q"] <= 1
                and document["entrant_ids"] == sorted(set(current) - set(previous_document["player_ids"]))
                and set(players) == set(current) | set(previous_document["player_ids"])
                and document["q"] == document["scale"]["selected"]["variance"],
                "saved annual previous-state lineage differs")
        with np.load(linked_path(previous_document["arrays"]), allow_pickle=False) as previous_arrays:
            previous_V, previous_M, previous_S = previous_arrays["V"], previous_arrays["M"], previous_arrays["S"]
        old = [positions[player] for player in previous_document["player_ids"]]
        old = np.array(old + [n + i for i in old])
        expected_prior_mean = np.zeros((2*n, k))
        expected_prior_mean[old] = previous_M
        require(previous_V.shape == (len(old), len(old)) and np.array_equal(previous_S, values["S"])
                and np.array_equal(expected_prior_mean, values["prior_mean"]), "saved annual carried prior differs")
        covariance[np.ix_(old, old)] = previous_V + document["q"] * np.eye(len(old))
    return AnnualState(document["benchmark"], document["season"], document["season_index"],
        document["protocol"]["sha256"], document["population_id"], tuple(document["player_ids"]),
        tuple(document["current_player_ids"]), tuple(document["entrant_ids"]), tuple(document["carried_only_ids"]),
        values["M"], values["V"], values["S"], values["A"], document["r"], document["a"], document["q"],
        values["centering_weights"], document["scale"], document["diagnostics"], values["prior_mean"],
        covariance, values["response_counts"])


def negative_rate_summary(batches) -> dict:
    """summarize signed complete/cell rate batches with exposure weights."""
    total_seconds = negative_seconds = negative_cell_seconds = 0.0
    negative_rows = negative_cells = row_count = 0
    minimum_total = minimum_cell = math.inf
    cells = None
    for rates, seconds in batches:
        require(rates.ndim == 2 and seconds.shape == (len(rates),) and np.isfinite(rates).all()
                and np.isfinite(seconds).all() and np.all(seconds > 0), "invalid fitted-rate diagnostic batch")
        require(cells is None or rates.shape[1] == cells, "fitted-rate response width changed")
        cells = rates.shape[1]
        scalar = rates.sum(axis=1)
        cell_negatives = (rates < 0).sum(axis=1)
        row_count += len(rates)
        total_seconds += float(seconds.sum())
        negative_rows += int(np.sum(scalar < 0))
        negative_cells += int(cell_negatives.sum())
        negative_seconds += float(seconds @ (scalar < 0))
        negative_cell_seconds += float(seconds @ cell_negatives)
        minimum_total, minimum_cell = min(minimum_total, float(scalar.min())), min(minimum_cell, float(rates.min()))
    require(row_count > 0 and total_seconds > 0, "negative-rate assessment requires admitted rows")
    return dict(rows=row_count, negative_complete_rates=negative_rows, negative_cell_rates=negative_cells,
                minimum_complete_rate=minimum_total, minimum_cell_rate=minimum_cell,
                exposure_weighted_negative_complete_frequency=negative_seconds/total_seconds,
                exposure_weighted_negative_cell_frequency=negative_cell_seconds/(total_seconds*cells))


def negative_rates(state: AnnualState, count_rows, strata: list) -> dict:
    """stream complete fitted row/cell rates; report negatives without clipping."""
    n = len(state.player_ids)
    positions = {player: i for i, player in enumerate(state.player_ids)}
    stratum_index = {tuple(value): i for i, value in enumerate(strata)}

    def batches():
        indices, contexts, seconds = [], [], []
        for row in count_rows:
            indices.append([positions[player] for player in row["offense"]]
                           + [n + positions[player] for player in row["defense"]])
            contexts.append(stratum_index[tuple(row["stratum"])])
            seconds.append(row["seconds"])
            if len(indices) == 128:
                yield state.r * (state.A[contexts] + state.M[indices].sum(axis=1)), np.asarray(seconds)
                indices, contexts, seconds = [], [], []
        if indices:
            yield state.r * (state.A[contexts] + state.M[indices].sum(axis=1)), np.asarray(seconds)

    return negative_rate_summary(batches())


def validate_model_rules(protocol: dict) -> None:
    """the frozen protocol describes the one supported model, not tunable options."""
    scale_rules = protocol["scale"]
    require(scale_rules["selection"] == "population_matched_scalar_restricted_gaussian_marginal_likelihood"
            and scale_rules["variance_bounds"] == [1e-8, 1.0]
            and scale_rules["coarse_exponents"] == list(np.arange(-8, .1, .5))
            and scale_rules["refinement"] == dict(method="bounded", xatol=1e-4, maxiter=40,
                bracket="best_interior_coarse_neighbors", repetitions=1)
            and scale_rules["ties"] == "smaller_variance" and scale_rules["solve_relative_residual_max"] == 1e-8,
            "frozen scale rules differ from the implemented estimator")
    design = protocol["design"]
    require(design["centering"] == "current_admitted_player_exposure"
            and design["annual_borrowing"] == "age_neutral_complete_mean_and_covariance"
            and design["scalar_response_covariance"] == 1
            and design["spatial_response_covariance"] == "first_season_half_count_cell_shares"
            and design["half_count"] == .5, "frozen model rules differ from the implemented estimator")


def fit_prepared_year(prepared: Path | str, benchmark: str, season: str,
                      previous: Path | str | None, out: Path | str) -> dict:
    """write one annual completion last; earlier completed states remain untouched."""
    prepared_path = Path(prepared).resolve(strict=True)
    document = read_json(prepared_path)
    protocol = read_json(linked_path(document["protocol"]))
    validate_model_rules(protocol)
    current_implementation = implementation()
    if document["purpose"] == "research":
        clean_implementation(current_implementation)
        require(current_implementation == protocol["implementation"], "fit implementation differs from frozen protocol")
    population = load_population(prepared_path, benchmark, season)
    previous_path = Path(previous).resolve(strict=True) if previous is not None else None
    previous_state = read_annual(previous_path) if previous_path else None
    if previous_path is not None:
        require(read_json(previous_path)["prepared"] == identity(prepared_path),
                "preceding state was fitted from a different prepared artifact")
    output = output_path(str(out), [str(prepared_path.parent)] + ([str(previous_path.parent)] if previous_path else []))
    require(output.is_relative_to(Path(protocol["output_root"]).resolve()), "fit output differs from frozen root")
    if document["purpose"] == "research":
        require(output.is_relative_to(Path("/Volumes/Expansion/hockey-stats")), "research fits must remain external")
    output.mkdir()
    state = fit_year(population, previous_state)
    annual = next(row for row in document["annual"] if row["population"] == benchmark and row["season"] == season)
    diagnostics = dict(state.diagnostics, negative_rates=negative_rates(
        state, rows(linked_path(annual["rows"])), annual["strata"]))
    arrays = {name: getattr(state, name) for name in
              ("M", "V", "S", "A", "centering_weights", "prior_mean", "response_counts")}
    array_path = output / "state.npz"
    with array_path.open("xb") as destination:
        np.savez(destination, **arrays)
    result = dict(schema_version=1, kind="attribution_annual", purpose=document["purpose"],
        implementation=current_implementation, protocol=document["protocol"], prepared=identity(prepared_path),
        previous=identity(previous_path) if previous_path else None, population_id=state.population_id,
        benchmark=benchmark, season=season, season_index=state.season_index,
        player_ids=state.player_ids, current_player_ids=state.current_player_ids,
        entrant_ids=state.entrant_ids, carried_only_ids=state.carried_only_ids,
        r=state.r, a=state.a, q=state.q, scale=state.scale, diagnostics=diagnostics,
        strata=annual["strata"], arrays=identity(array_path),
        shapes={name: list(value.shape) for name, value in arrays.items()},
        units=dict(M="relative league team rate", V="relative-rate-squared row covariance",
                   S="normalized response covariance shape", A="relative league team rate",
                   r="attempts per 60 team minutes", a="relative-rate squared", q="relative-rate squared",
                   centering_weights="current admitted player exposure share", response_counts="recorded attempts",
                   prior_mean="relative league team rate"))
    write_json(output / "annual.json", result)
    return identity(output / "annual.json")
