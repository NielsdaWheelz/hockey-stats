"""annual volume and zero-sum shape with independent full row covariances.

player columns are offense then defense. positive defense is opponent creation.
references are evidence, not fitted parameters. one owner fits and projects both
blocks; the shared-volume estimator survives only as a named scientific control.
"""

from dataclasses import dataclass
import math
from pathlib import Path
import time

import numpy as np
from scipy.linalg import cho_solve, solve_triangular
from scipy.optimize import minimize_scalar

from .artifacts import clean_implementation, implementation, linked_path, require, resources, write_json
from .chance_cli import identity, output_path, read_json

from .attribution_data import (
    POPULATIONS,
    RevisionPopulation,
    load_revision_population,
    read_revision_prepared,
)


@dataclass(frozen=True)
class BlockState:
    M: np.ndarray
    V: np.ndarray
    A: np.ndarray
    prior_mean: np.ndarray
    prior_covariance: np.ndarray
    a: float
    q: float | None
    scale: dict
    diagnostics: dict


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
    volume: BlockState
    shape: BlockState | None
    r: float
    u: np.ndarray
    p: np.ndarray | None
    response_counts: np.ndarray


def _factor(H: np.ndarray, covariance: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # numpy returns the triangular factor alone. scipy's cho_factor retains an
    # unspecified opposite triangle, which is not part of a covariance factor.
    L = np.linalg.cholesky(covariance)
    K = np.eye(len(H)) + L.T @ H @ L
    return L, K, np.linalg.cholesky(K)


def _equation_residual(K: np.ndarray, solution: np.ndarray, rhs: np.ndarray) -> float:
    residual = float(
        np.linalg.norm(K @ solution - rhs, ord=np.inf)
        / (
            1
            + np.linalg.norm(K, ord=np.inf) * np.linalg.norm(solution, ord=np.inf)
            + np.linalg.norm(rhs, ord=np.inf)
        )
    )
    return residual


def _covariance(L: np.ndarray, K: np.ndarray, factor: np.ndarray) -> tuple[np.ndarray, float]:
    intermediate = solve_triangular(factor, L.T, lower=True, check_finite=False)
    solution = solve_triangular(factor.T, intermediate, lower=False, check_finite=False)
    residual = _equation_residual(K, solution, L.T)
    return intermediate.T @ intermediate, residual


def _posterior(
    H: np.ndarray, T: np.ndarray, M0: np.ndarray, V0: np.ndarray
) -> tuple[np.ndarray, np.ndarray, dict]:
    """a proper prior is factored, never a centered posterior covariance."""
    L, K, factor = _factor(H, V0)
    V, residual = _covariance(L, K, factor)
    M = M0 + V @ (T - H @ M0)
    require(np.isfinite(M).all() and np.isfinite(V).all(), "nonfinite annual posterior")
    normal = np.eye(len(H)) + V0 @ H
    mean_residual = _equation_residual(normal, M - M0, V0 @ (T - H @ M0))
    covariance_residual = _equation_residual(normal, V, V0)
    require(
        all(
            math.isfinite(value) and value <= 1e-8 for value in (residual, mean_residual, covariance_residual)
        ),
        "original posterior equation residual exceeds 1e-8",
    )
    symmetry = float(np.max(np.abs(V - V.T)))
    tolerance = float(1e-10 * max(1, np.linalg.norm(V, ord=np.inf)))
    require(symmetry <= tolerance, "posterior covariance is asymmetric")
    return (
        M,
        V,
        dict(
            equation_relative_residual=max(residual, mean_residual, covariance_residual),
            cholesky_equation_relative_residual=residual,
            original_mean_equation_relative_residual=mean_residual,
            original_covariance_equation_relative_residual=covariance_residual,
            covariance_symmetry=symmetry,
            covariance_rounding_tolerance=tolerance,
        ),
    )


def _prior(
    players: tuple[int, ...], previous: AnnualState | None, block: BlockState | None, width: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = len(players)
    M0 = np.zeros((2 * n, width))
    if previous is None:
        return M0, np.zeros((2 * n, 2 * n)), np.arange(2 * n)
    require(block is not None, "preceding annual block is missing")
    positions = {player: i for i, player in enumerate(players)}
    old = [positions[player] for player in previous.player_ids]
    selected = np.array(old + [n + i for i in old])
    covariance = np.eye(2 * n) * block.a
    covariance[np.ix_(selected, selected)] = block.V
    M0[selected] = block.M
    return M0, covariance, selected


class _ScaleProblem:
    """cache response contractions once; each scale candidate solves row space."""

    def __init__(self, H, T, yy, M0, base_covariance, innovation_indices, p):
        self.H, self.T, self.M0 = H, T, M0
        self.base_covariance, self.innovation_indices = base_covariance, innovation_indices
        self.b = T - H @ M0
        self.rank = 1 if p is None else len(p) - 1
        if p is None:
            self.zz = float(yy - 2 * M0[:, 0] @ T[:, 0] + M0[:, 0] @ H @ M0[:, 0])
        else:
            self.zz = float(yy - 2 * np.sum(M0 * T / p) + np.sum(M0 * (H @ M0) / p))
        self.B = None if p is None else (self.b / p) @ self.b.T
        self.curve = []

    def covariance(self, variance):
        covariance = self.base_covariance.copy()
        covariance[self.innovation_indices, self.innovation_indices] += variance
        return covariance

    def objective(self, exponent, phase="refinement"):
        variance = 10.0 ** float(exponent)
        error, residual = None, None
        try:
            L, K, factor = _factor(self.H, self.covariance(variance))
            if self.B is None:
                rhs = L.T @ self.b[:, 0]
                solution = cho_solve((factor, True), rhs, check_finite=False)
                residual = _equation_residual(K, solution, rhs)
                contraction = rhs @ solution
            else:
                V, residual = _covariance(L, K, factor)
                contraction = np.sum(V * self.B.T)
            if not math.isfinite(residual) or residual > 1e-8:
                error = "scale objective equation residual exceeds 1e-8"
            value = float(self.rank * 2 * np.log(np.diag(factor)).sum() + self.zz - contraction)
            if not math.isfinite(value):
                error = "nonfinite objective"
        except np.linalg.LinAlgError as failure:
            error, value = str(failure), math.inf
        self.curve.append(
            dict(
                exponent=float(exponent),
                variance=variance,
                objective=value if error is None else None,
                phase=phase,
                error=error,
                equation_relative_residual=residual
                if residual is not None and math.isfinite(residual)
                else None,
            )
        )
        return value if error is None else math.inf


def _select_scale(problem: _ScaleProblem, inherited: bool) -> tuple[float, dict]:
    coarse = [
        (float(exponent), problem.objective(float(exponent), "coarse"))
        for exponent in np.arange(-8, 0.1, 0.5)
    ]
    interior = [(exponent, value) for exponent, value in coarse[1:-1] if math.isfinite(value)]
    refinement = None
    if interior:
        exponent = min(interior, key=lambda row: (row[1], row[0]))[0]
        fit = minimize_scalar(
            problem.objective,
            bounds=(exponent - 0.5, exponent + 0.5),
            method="bounded",
            options={"xatol": 1e-4, "maxiter": 40},
        )
        refinement = dict(
            success=bool(fit.success),
            message=str(fit.message),
            evaluations=int(fit.nfev),
            bounds=[exponent - 0.5, exponent + 0.5],
            exponent=float(fit.x) if math.isfinite(fit.x) else None,
        )
    valid = [row for row in problem.curve if row["objective"] is not None]
    require(bool(valid), "no valid numerical scale state; dependent chain stopped")
    winner = min(valid, key=lambda row: (row["objective"], row["variance"]))
    unresolved = []
    if winner["exponent"] in (-8, 0):
        unresolved.append("endpoint_winner")
    if refinement is None or not refinement["success"]:
        unresolved.append("refinement_failed")
    if any(row["phase"] == "refinement" and row["objective"] is None for row in problem.curve):
        unresolved.append("nonfinite_refinement")
    competing = [
        dict(exponent=exponent, objective=value)
        for i, (exponent, value) in enumerate(coarse)
        if math.isfinite(value)
        and (i == 0 or value <= coarse[i - 1][1])
        and (i == len(coarse) - 1 or value <= coarse[i + 1][1])
    ]
    return winner["variance"], dict(
        status="scale_unresolved" if unresolved or inherited else "resolved",
        own_reasons=unresolved,
        inherited_limitation=inherited,
        curve=problem.curve,
        competing_coarse_minima=competing,
        refinement=refinement,
        selected=dict(winner),
    )


def _center(M, V, A, weights):
    n = len(weights)
    off_mean, def_mean = weights @ M[:n], weights @ M[n:]
    M[:n] -= off_mean
    M[n:] -= def_mean
    A += 5 * (off_mean + def_mean)
    centered = np.empty_like(V)
    for start in (0, n):
        for stop in (0, n):
            block = V[start : start + n, stop : stop + n]
            left, right = weights @ block, block @ weights
            centered[start : start + n, stop : stop + n] = (
                block - left[None, :] - right[:, None] + weights @ right
            )
    return M, centered, A


def _block_at_scale(
    H, T, ybar, xbar, M0, covariance, previous, weights, p, variance, scale, started
) -> BlockState:
    M, V, diagnostics = _posterior(H, T, M0, covariance)
    M, V, A = _center(M, V, ybar - xbar @ M, weights)
    symmetry = float(np.max(np.abs(V - V.T)))
    tolerance = float(1e-10 * max(1, np.linalg.norm(V, ord=np.inf)))
    require(symmetry <= tolerance and np.min(np.diag(V)) >= -tolerance, "invalid centered covariance")
    n = len(weights)
    diagnostics.update(
        centered_covariance_symmetry=symmetry,
        covariance_rounding_tolerance=tolerance,
        centered_mean_residual=float(max(np.max(np.abs(weights @ M[:n])), np.max(np.abs(weights @ M[n:])))),
        resources=resources(started),
    )
    if p is not None:
        diagnostics["zero_sum_mean_residual"] = float(np.max(np.abs(M.sum(axis=1))))
        require(diagnostics["zero_sum_mean_residual"] <= 1e-8, "shape mean is not zero sum")
    return BlockState(
        M,
        V,
        A,
        M0,
        covariance,
        variance if previous is None else previous.a,
        None if previous is None else variance,
        scale,
        diagnostics,
    )


def _fit_block(
    H, T, yy, ybar, xbar, M0, base_covariance, innovation_indices, previous, weights, p
) -> BlockState:
    started = time.monotonic()
    problem = _ScaleProblem(H, T, yy, M0, base_covariance, innovation_indices, p)
    inherited = previous is not None and previous.scale["status"] == "scale_unresolved"
    variance, scale = _select_scale(problem, inherited)
    return _block_at_scale(
        H, T, ybar, xbar, M0, problem.covariance(variance), previous, weights, p, variance, scale, started
    )


def _annual_inputs(population: "RevisionPopulation", previous: AnnualState | None):
    current = population.player_ids
    require(
        current == tuple(sorted(set(current))) and bool(current),
        "current player ids must be sorted and unique",
    )
    require(population.benchmark in ("all_attempts", "unblocked_spatial"), "unknown attribution benchmark")
    require(
        type(population.season_index) is int and population.season_index >= 0, "invalid annual sequence index"
    )
    require(
        type(population.season) is str
        and len(population.season) == 8
        and population.season.isdigit()
        and int(population.season[4:]) == int(population.season[:4]) + 1,
        "annual season requires native identity",
    )
    nc, k, h = len(current), population.T.shape[1], len(population.stratum_weight)
    expected = dict(
        H=(2 * nc, 2 * nc),
        T=(2 * nc, k),
        xbar=(h, 2 * nc),
        ybar=(h, k),
        stratum_weight=(h,),
        player_exposure=(nc,),
        response_counts=(k,),
        u=(nc,),
    )
    for name, shape in expected.items():
        value = getattr(population, name)
        require(
            isinstance(value, np.ndarray) and value.shape == shape and np.isfinite(value).all(),
            "invalid annual population array " + name,
        )
    require(
        (
            population.benchmark == "all_attempts"
            and k == 1
            and population.p is None
            and population.shape_yy is None
        )
        or (
            population.benchmark == "unblocked_spatial"
            and k == 656
            and population.p is not None
            and population.p.shape == (k,)
            and np.isfinite(population.p).all()
            and np.all(population.p > 0)
            and math.isclose(float(population.p.sum()), 1, rel_tol=0, abs_tol=1e-12)
            and population.shape_yy is not None
            and math.isfinite(population.shape_yy)
        ),
        "invalid response reference",
    )
    require(
        math.isfinite(population.yy)
        and math.isfinite(population.r)
        and population.r > 0
        and np.all(population.player_exposure > 0)
        and np.all(population.stratum_weight > 0)
        and np.all(population.u > 0)
        and math.isclose(float(population.u.sum()), 1, rel_tol=0, abs_tol=1e-12),
        "annual population requires positive admitted exposure and fixed references",
    )
    require(
        np.allclose(population.H, population.H.T, rtol=1e-10, atol=1e-10),
        "annual cross-product is asymmetric",
    )
    require(
        np.allclose(population.xbar[:, :nc].sum(1), 5, rtol=0, atol=1e-10)
        and np.allclose(population.xbar[:, nc:].sum(1), 5, rtol=0, atol=1e-10),
        "context design is not five skaters per role",
    )
    if previous is None:
        require(population.season_index == 0, "later annual fit requires immediately preceding state")
        players = current
    else:
        require(
            population.season_index == previous.season_index + 1
            and int(population.season[:4]) == int(previous.season[:4]) + 1
            and population.benchmark == previous.benchmark
            and population.protocol_sha256 == previous.protocol_sha256
            and population.population_id == previous.population_id
            and (
                (population.p is None and previous.p is None)
                or (
                    population.p is not None
                    and previous.p is not None
                    and np.array_equal(population.p, previous.p)
                )
            ),
            "incompatible or nonconsecutive preceding annual state",
        )
        players = tuple(sorted(set(previous.player_ids) | set(current)))
    n = len(players)
    positions = {player: i for i, player in enumerate(players)}
    selected = np.array(
        [positions[player] for player in current] + [n + positions[player] for player in current]
    )
    H, T, xbar = np.zeros((2 * n, 2 * n)), np.zeros((2 * n, k)), np.zeros((h, 2 * n))
    H[np.ix_(selected, selected)] = population.H
    T[selected] = population.T
    xbar[:, selected] = population.xbar
    weights = np.zeros(n)
    weights[[positions[player] for player in current]] = population.u
    return players, H, T, xbar, weights


def _fit(population: "RevisionPopulation", previous: AnnualState | None, shared_volume: bool) -> AnnualState:
    players, H, T, xbar, weights = _annual_inputs(population, previous)
    p = population.p
    prior_volume = None if previous is None else previous.volume
    M0, base, innovations = _prior(players, previous, prior_volume, 1)
    volume = _fit_block(
        H,
        T.sum(axis=1, keepdims=True),
        population.yy,
        population.ybar.sum(axis=1, keepdims=True),
        xbar,
        M0,
        base,
        innovations,
        prior_volume,
        weights,
        None,
    )
    shape = None
    if p is not None:
        Th = T - T.sum(axis=1, keepdims=True) * p
        yh = population.ybar - population.ybar.sum(axis=1, keepdims=True) * p
        prior_shape = None if previous is None else previous.shape
        M0, base, innovations = _prior(players, previous, prior_shape, len(p))
        if shared_volume:
            covariance = base.copy()
            covariance[innovations, innovations] += volume.scale["selected"]["variance"]
            shape = _block_at_scale(
                H,
                Th,
                yh,
                xbar,
                M0,
                covariance,
                prior_shape,
                weights,
                p,
                volume.scale["selected"]["variance"],
                volume.scale,
                time.monotonic(),
            )
        else:
            shape = _fit_block(
                H, Th, population.shape_yy, yh, xbar, M0, base, innovations, prior_shape, weights, p
            )
    entrants = (
        population.player_ids
        if previous is None
        else tuple(player for player in population.player_ids if player not in previous.player_ids)
    )
    return AnnualState(
        population.benchmark,
        population.season,
        population.season_index,
        population.protocol_sha256,
        population.population_id,
        players,
        population.player_ids,
        entrants,
        tuple(player for player in players if player not in population.player_ids),
        volume,
        shape,
        population.r,
        weights,
        None if p is None else p.copy(),
        population.response_counts.copy(),
    )


def fit_revision_year(population: "RevisionPopulation", previous: AnnualState | None) -> AnnualState:
    """fit independent volume/shape borrowing; references are supplied explicitly."""
    return _fit(population, previous, False)


def fit_shared_volume_control(population: "RevisionPopulation", previous: AnnualState | None) -> AnnualState:
    """scientific 04a control only: both blocks use the volume-selected scale."""
    return _fit(population, previous, True)


def map_mean(state: AnnualState) -> np.ndarray:
    return state.volume.M if state.p is None else state.volume.M * state.p + state.shape.M


def context_mean(state: AnnualState) -> np.ndarray:
    return state.volume.A if state.p is None else state.volume.A * state.p + state.shape.A


def _row_moments(state: AnnualState, player_contrast: np.ndarray):
    c = np.asarray(player_contrast, dtype=float)
    require(c.shape == (len(state.volume.M),) and np.isfinite(c).all(), "invalid player contrast")
    selected = np.flatnonzero(c)
    coefficients = c[selected]
    moments = []
    for block in (state.volume, state.shape):
        if block is not None:
            mean = coefficients @ block.M[selected]
            variance = float(coefficients @ block.V[np.ix_(selected, selected)] @ coefficients)
            moments.append((mean, variance, block.diagnostics["covariance_rounding_tolerance"]))
    return c, moments


def project(
    state: AnnualState, player_contrast: np.ndarray, response_weights: np.ndarray
) -> tuple[float, float]:
    """physical mean and raw working variance for one joint linear projection."""
    c, moments = _row_moments(state, player_contrast)
    v = np.asarray(response_weights, dtype=float)
    k = 1 if state.p is None else len(state.p)
    require(v.shape == (k,) and np.isfinite(v).all(), "invalid response functional")
    if state.p is None:
        mean = state.r * moments[0][0][0] * v[0]
        variance = state.r**2 * moments[0][1] * v[0] ** 2
    else:
        # subtracting a constant exploits the exact zero-sum contract and makes
        # an all-ones functional exactly the fitted volume, even in roundoff.
        shifted = v - v[0]
        center = float(state.p @ shifted)
        volume = float(v[0] + center)
        response_variance = float(state.p @ (shifted - center) ** 2)
        mean = state.r * (moments[0][0][0] * volume + moments[1][0] @ shifted)
        variance = state.r**2 * (moments[0][1] * volume**2 + moments[1][1] * response_variance)
    tolerance = state.r**2 * float(c @ c) * float(v @ v) * sum(row[2] for row in moments)
    require(
        math.isfinite(mean) and math.isfinite(variance) and variance >= -tolerance,
        "invalid attribution projection variance",
    )
    return float(mean), float(variance)


def project_interval(state: AnnualState, player_contrast: np.ndarray, response_weights: np.ndarray) -> dict:
    mean, variance = project(state, player_contrast, response_weights)
    c, v = np.asarray(player_contrast, dtype=float), np.asarray(response_weights, dtype=float)
    tolerance = (
        state.r**2
        * float(c @ c)
        * float(v @ v)
        * sum(
            block.diagnostics["covariance_rounding_tolerance"]
            for block in (state.volume, state.shape)
            if block is not None
        )
    )
    interval_variance = max(variance, 0.0)
    half = 1.959963984540054 * math.sqrt(interval_variance)
    return dict(
        mean=mean,
        variance=variance,
        lower=mean - half,
        upper=mean + half,
        interval_variance=interval_variance,
        variance_rounded_to_zero=variance < 0,
        variance_rounding_tolerance=tolerance,
    )


def project_native(state: AnnualState, player_contrast: np.ndarray) -> dict:
    """all native cells, with the same two contracted row covariance terms."""
    c, moments = _row_moments(state, player_contrast)
    if state.p is None:
        mean = state.r * moments[0][0]
        variance = np.array([state.r**2 * moments[0][1]])
    else:
        mean = state.r * (moments[0][0][0] * state.p + moments[1][0])
        variance = state.r**2 * (moments[0][1] * state.p**2 + moments[1][1] * state.p * (1 - state.p))
    tolerance = state.r**2 * float(c @ c) * sum(row[2] for row in moments)
    require(
        np.isfinite(mean).all() and np.isfinite(variance).all() and np.all(variance >= -tolerance),
        "invalid native projection variance",
    )
    interval_variance = np.maximum(variance, 0.0)
    half = 1.959963984540054 * np.sqrt(interval_variance)
    return dict(
        mean=mean,
        variance=variance,
        lower=mean - half,
        upper=mean + half,
        interval_variance=interval_variance,
        variance_rounded_to_zero=variance < 0,
        variance_rounding_tolerance=tolerance,
    )


def complete_rates(
    state: AnnualState, player_column_indices: np.ndarray, context_indices: np.ndarray
) -> np.ndarray:
    """complete physical row rates; signed additive values are never clipped."""
    columns, contexts = np.asarray(player_column_indices), np.asarray(context_indices)
    require(
        columns.ndim == 2 and columns.shape[1] == 10 and contexts.shape == (len(columns),),
        "complete rates require five offense and five defense columns per row",
    )
    volume = state.volume.A[contexts] + state.volume.M[columns].sum(axis=1)
    if state.p is None:
        return state.r * volume
    return state.r * (volume * state.p + state.shape.A[contexts] + state.shape.M[columns].sum(axis=1))


def negative_rate_summary(batches, reference_rate: float) -> dict:
    """one streamed summary, including located extrema and weighted negative mass."""
    total_seconds = negative_seconds = negative_cell_seconds = negative_mass = 0.0
    negative_rows = negative_cells = row_count = 0
    minimum_total = minimum_cell = math.inf
    complete_example = cell_example = None
    cells = None
    for rates, seconds, locators in batches:
        require(
            rates.ndim == 2
            and seconds.shape == (len(rates),)
            and len(locators) == len(rates)
            and np.isfinite(rates).all()
            and np.isfinite(seconds).all()
            and np.all(seconds > 0),
            "invalid fitted-rate diagnostic batch",
        )
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
        negative_mass += float(seconds @ np.maximum(-rates, 0).sum(axis=1))
        row = int(np.argmin(scalar))
        if scalar[row] < minimum_total:
            minimum_total = float(scalar[row])
            complete_example = dict(row=locators[row], rate=minimum_total)
        row, cell = np.unravel_index(np.argmin(rates), rates.shape)
        if rates[row, cell] < minimum_cell:
            minimum_cell = float(rates[row, cell])
            cell_example = dict(row=locators[int(row)], cell_id=int(cell), rate=minimum_cell)
    require(
        row_count > 0 and total_seconds > 0 and math.isfinite(reference_rate) and reference_rate > 0,
        "negative-rate assessment requires admitted rows and positive reference",
    )
    return dict(
        rows=row_count,
        team_seconds=total_seconds,
        negative_complete_rates=negative_rows,
        negative_cell_rates=negative_cells,
        minimum_complete_rate=minimum_total,
        minimum_cell_rate=minimum_cell,
        minimum_complete_example=complete_example,
        minimum_cell_example=cell_example,
        exposure_weighted_negative_complete_frequency=negative_seconds / total_seconds,
        exposure_weighted_negative_cell_frequency=negative_cell_seconds / (total_seconds * cells),
        negative_mass=negative_mass / (reference_rate * total_seconds),
    )


def negative_rates(state: AnnualState, count_rows, strata: list) -> dict:
    n = len(state.player_ids)
    positions = {player: i for i, player in enumerate(state.player_ids)}
    contexts = {tuple(value): i for i, value in enumerate(strata)}

    def batches():
        columns, context_ids, seconds, locators = [], [], [], []
        for row in count_rows:
            columns.append(
                [positions[player] for player in row["offense"]]
                + [n + positions[player] for player in row["defense"]]
            )
            context_ids.append(contexts[tuple(row["stratum"])])
            seconds.append(row["seconds"])
            locators.append(
                {
                    key: row[key]
                    for key in ("game_id", "period", "start", "end", "attacking_team", "segment_index")
                    if key in row
                }
            )
            if len(columns) == 128:
                yield (
                    complete_rates(state, np.asarray(columns), np.asarray(context_ids)),
                    np.asarray(seconds),
                    locators,
                )
                columns, context_ids, seconds, locators = [], [], [], []
        if columns:
            yield (
                complete_rates(state, np.asarray(columns), np.asarray(context_ids)),
                np.asarray(seconds),
                locators,
            )

    return negative_rate_summary(batches(), state.r)


def read_control_annual(path: Path | str) -> AnnualState:
    """the only schema-1 path: read an immutable corrected scientific control."""
    document = read_json(Path(path).resolve(strict=True))
    require(
        type(document["schema_version"]) is int
        and document["schema_version"] == 1
        and document["kind"] == "attribution_annual",
        "expected completed annual attribution state",
    )
    linked_path(document["protocol"])
    linked_path(document["prepared"])
    if document["previous"] is not None:
        linked_path(document["previous"])
    prepared = read_json(linked_path(document["prepared"]))
    candidates = [
        row
        for row in prepared["annual"]
        if row["population"] == document["benchmark"] and row["season"] == document["season"]
    ]
    require(len(candidates) == 1, "saved annual population absent from preparation")
    annual = candidates[0]
    players, current = document["player_ids"], document["current_player_ids"]
    require(
        players == sorted(set(players))
        and current == sorted(set(current))
        and set(current) <= set(players)
        and current == annual["players"]
        and document["carried_only_ids"] == sorted(set(players) - set(current))
        and document["strata"] == annual["strata"]
        and document["r"] == annual["r"]
        and document["season_index"] == prepared["seasons"].index(document["season"])
        and document["protocol"] == prepared["protocol"]
        and document["population_id"] == prepared["population_ids"][document["benchmark"]],
        "saved annual identity/order differs from its prepared population",
    )
    n = len(players)
    k = 1 if document["benchmark"] == "all_attempts" else 656
    shapes = dict(
        M=[2 * n, k],
        V=[2 * n, 2 * n],
        S=[k, k],
        A=[len(annual["strata"]), k],
        centering_weights=[n],
        prior_mean=[2 * n, k],
        response_counts=[k],
    )
    require(document["shapes"] == shapes, "saved annual shapes disagree with its population")
    with np.load(linked_path(document["arrays"]), allow_pickle=False) as arrays:
        require(set(arrays.files) == set(shapes), "annual array names differ")
        values = {name: arrays[name] for name in arrays.files}
    for name, shape in shapes.items():
        require(
            list(values[name].shape) == shape and np.isfinite(values[name]).all(),
            "invalid saved annual array " + name,
        )
    positions = {player: i for i, player in enumerate(players)}
    weights = np.zeros(n)
    with np.load(linked_path(annual["arrays"]), allow_pickle=False) as source_arrays:
        weights[[positions[player] for player in current]] = source_arrays["player_exposure"]
        require(
            np.array_equal(values["response_counts"], source_arrays["response_counts"]),
            "saved league counts differ",
        )
    weights /= weights.sum()
    require(np.array_equal(weights, values["centering_weights"]), "saved centering exposure differs")
    require(math.isfinite(document["a"]) and 1e-8 <= document["a"] <= 1, "invalid saved initial variance")
    covariance = np.eye(2 * n) * document["a"]
    if document["previous"] is None:
        expected_S = (
            np.ones((1, 1))
            if k == 1
            else np.diag((values["response_counts"] + 0.5) / (values["response_counts"].sum() + 0.5 * k))
        )
        require(
            document["season_index"] == 0
            and document["q"] is None
            and players == current
            and document["entrant_ids"] == current
            and np.all(values["prior_mean"] == 0)
            and np.array_equal(values["S"], expected_S)
            and document["a"] == document["scale"]["selected"]["variance"],
            "first annual state has incompatible prior",
        )
    else:
        previous_path = linked_path(document["previous"])
        read_control_annual(previous_path)
        previous_document = read_json(previous_path)
        require(
            previous_document["season_index"] + 1 == document["season_index"]
            and int(previous_document["season"][:4]) + 1 == int(document["season"][:4])
            and all(
                previous_document[key] == document[key]
                for key in ("benchmark", "protocol", "population_id", "prepared", "a")
            )
            and math.isfinite(document["q"])
            and 1e-8 <= document["q"] <= 1
            and document["entrant_ids"] == sorted(set(current) - set(previous_document["player_ids"]))
            and set(players) == set(current) | set(previous_document["player_ids"])
            and document["q"] == document["scale"]["selected"]["variance"],
            "saved annual previous-state lineage differs",
        )
        with np.load(linked_path(previous_document["arrays"]), allow_pickle=False) as previous_arrays:
            previous_V, previous_M, previous_S = (
                previous_arrays["V"],
                previous_arrays["M"],
                previous_arrays["S"],
            )
        old = [positions[player] for player in previous_document["player_ids"]]
        old = np.array(old + [n + i for i in old])
        expected_prior_mean = np.zeros((2 * n, k))
        expected_prior_mean[old] = previous_M
        require(
            previous_V.shape == (len(old), len(old))
            and np.array_equal(previous_S, values["S"])
            and np.array_equal(expected_prior_mean, values["prior_mean"]),
            "saved annual carried prior differs",
        )
        covariance[np.ix_(old, old)] = previous_V + document["q"] * np.eye(len(old))
    p = None if k == 1 else np.diag(values["S"]).copy()
    volume = BlockState(
        values["M"].sum(axis=1, keepdims=True),
        values["V"],
        values["A"].sum(axis=1, keepdims=True),
        values["prior_mean"].sum(axis=1, keepdims=True),
        covariance,
        document["a"],
        document["q"],
        document["scale"],
        document["diagnostics"],
    )
    shape = (
        None
        if p is None
        else BlockState(
            values["M"] - volume.M * p,
            values["V"],
            values["A"] - volume.A * p,
            values["prior_mean"] - volume.prior_mean * p,
            covariance,
            document["a"],
            document["q"],
            document["scale"],
            document["diagnostics"],
        )
    )
    require(
        np.allclose(
            values["V"], values["V"].T, rtol=0, atol=document["diagnostics"]["covariance_rounding_tolerance"]
        ),
        "control covariance is asymmetric",
    )
    return AnnualState(
        document["benchmark"],
        document["season"],
        document["season_index"],
        document["protocol"]["sha256"],
        document["population_id"],
        tuple(players),
        tuple(current),
        tuple(document["entrant_ids"]),
        tuple(document["carried_only_ids"]),
        volume,
        shape,
        document["r"],
        values["centering_weights"],
        p,
        values["response_counts"],
    )


def _control_replay(state: AnnualState, control: AnnualState) -> dict:
    require(
        state.player_ids == control.player_ids
        and state.current_player_ids == control.current_player_ids
        and state.entrant_ids == control.entrant_ids
        and state.carried_only_ids == control.carried_only_ids
        and state.benchmark == control.benchmark
        and state.season == control.season
        and state.population_id == control.population_id
        and state.r == control.r,
        "control replay identity differs",
    )
    comparisons = {}
    for name in ("M", "V", "A", "prior_mean", "prior_covariance"):
        new, old = getattr(state.volume, name), getattr(control.volume, name)
        require(new.shape == old.shape, "control replay shape differs: " + name)
        comparisons[name] = float(np.max(np.abs(new - old)) / (1 + np.max(np.abs(old))))
    comparisons["u"] = float(np.max(np.abs(state.u - control.u)) / (1 + np.max(np.abs(control.u))))
    require(max(comparisons.values()) <= 1e-8, "scalar/volume control replay exceeds 1e-8")
    return dict(
        status="verified",
        relative_maximum_absolute_errors=comparisons,
        tolerance=1e-8,
        entry_variance_absolute_error=abs(state.volume.a - control.volume.a),
        innovation_variance_absolute_error=None
        if state.volume.q is None
        else abs(state.volume.q - control.volume.q),
    )


def write_annual(
    state: AnnualState,
    prepared: Path | str,
    previous: Path | str | None,
    out: Path | str,
    *,
    control=None,
    control_replay=None,
    resolution_check=None,
) -> dict:
    """save native block arrays and their complete consumed lineage, completion last."""
    prepared_path = Path(prepared).resolve(strict=True)
    source = read_revision_prepared(prepared_path)
    protocol = read_json(linked_path(source["protocol"]))
    annual = next(
        row
        for row in source["annual"]
        if row["population"] == state.benchmark and row["season"] == state.season
    )
    previous_path = Path(previous).resolve(strict=True) if previous is not None else None
    output = output_path(
        str(out), [str(prepared_path.parent)] + ([str(previous_path.parent)] if previous_path else [])
    )
    require(
        output.is_relative_to(Path(protocol["output_root"]).resolve()),
        "annual output differs from frozen root",
    )
    current_implementation = implementation()
    if source["purpose"] == "research":
        clean_implementation(current_implementation)
        require(
            current_implementation == protocol["implementation"]
            and output.is_relative_to(Path("/Volumes/Expansion/hockey-stats")),
            "research annual implementation/root differs",
        )
    output.mkdir()
    values = dict(u=state.u, response_counts=state.response_counts)
    if state.p is not None:
        values["p"] = state.p
    blocks = {}
    for name in ("volume", "shape"):
        block = getattr(state, name)
        if block is None:
            blocks[name] = None
            continue
        for field in ("M", "V", "A", "prior_mean", "prior_covariance"):
            values[name + "_" + field] = getattr(block, field)
        blocks[name] = dict(a=block.a, q=block.q, scale=block.scale, diagnostics=block.diagnostics)
    arrays_path = output / "state.npz"
    with arrays_path.open("xb") as destination:
        np.savez(destination, **values)
    document = dict(
        schema_version=2,
        kind="attribution_revision_annual",
        purpose=source["purpose"],
        implementation=current_implementation,
        protocol=source["protocol"],
        prepared=identity(prepared_path),
        previous=identity(previous_path) if previous_path else None,
        control=control,
        population_id=state.population_id,
        benchmark=state.benchmark,
        season=state.season,
        season_index=state.season_index,
        player_ids=state.player_ids,
        current_player_ids=state.current_player_ids,
        entrant_ids=state.entrant_ids,
        carried_only_ids=state.carried_only_ids,
        r=state.r,
        strata=annual["strata"],
        volume=blocks["volume"],
        shape=blocks["shape"],
        arrays=identity(arrays_path),
        shapes={name: list(value.shape) for name, value in values.items()},
        control_replay=control_replay,
        shape_resolution_check=resolution_check,
        units=dict(
            M="relative league team rate",
            V="relative-rate-squared full row covariance",
            A="relative league team rate",
            r="attempts per 60 team minutes",
            u="fixed original exposure share",
            p="fixed positive first-season native share",
            prior_mean="relative league team rate",
            prior_covariance="relative-rate-squared full row covariance",
        ),
    )
    write_json(output / "annual.json", document)
    return identity(output / "annual.json")


def read_annual(path: Path | str) -> AnnualState:
    """read schema 2 exclusively; block priors must match the preceding state."""
    document = read_json(Path(path).resolve(strict=True))
    require(
        type(document["schema_version"]) is int
        and document["schema_version"] == 2
        and document["kind"] == "attribution_revision_annual",
        "expected revision annual state",
    )
    source = read_revision_prepared(linked_path(document["prepared"]))
    annual = next(
        row
        for row in source["annual"]
        if row["population"] == document["benchmark"] and row["season"] == document["season"]
    )
    controls = {(row["benchmark"], row["season"]): row["state"] for row in source["baseline_controls"]}
    require(
        document["control"] == controls.get((document["benchmark"], document["season"])),
        "annual control binding differs from frozen source",
    )
    if document["control"] is not None:
        linked_path(document["control"])
    if source["purpose"] == "research":
        protocol = read_json(linked_path(source["protocol"]))
        clean_implementation(document["implementation"])
        require(
            document["implementation"] == protocol["implementation"],
            "annual implementation differs from frozen protocol",
        )
    previous_path = linked_path(document["previous"]) if document["previous"] is not None else None
    previous = read_annual(previous_path) if previous_path is not None else None
    if previous_path is not None:
        previous_document = read_json(previous_path)
        require(
            all(
                previous_document[name] == document[name]
                for name in ("protocol", "prepared", "population_id", "purpose", "benchmark")
            ),
            "annual lineage changed source/model",
        )
    players, current = tuple(document["player_ids"]), tuple(document["current_player_ids"])
    require(
        players == tuple(sorted(set(players)))
        and current == tuple(annual["players"])
        and document["carried_only_ids"] == sorted(set(players) - set(current))
        and document["entrant_ids"]
        == sorted(set(current) - (set(previous.player_ids) if previous else set()))
        and set(players) == set(current) | (set(previous.player_ids) if previous else set())
        and document["strata"] == annual["strata"]
        and document["r"] == annual["r"]
        and document["season_index"] == source["seasons"].index(document["season"])
        and document["protocol"] == source["protocol"]
        and document["purpose"] == source["purpose"]
        and document["population_id"] == source["population_ids"][document["benchmark"]],
        "annual source identity/order differs",
    )
    require(
        (previous is None and document["season_index"] == 0)
        or (
            previous is not None
            and document["season_index"] == previous.season_index + 1
            and int(document["season"][:4]) == int(previous.season[:4]) + 1
        ),
        "annual sequence is not consecutive",
    )
    n = len(players)
    k = 1 if document["benchmark"] == "all_attempts" else 656
    shapes = dict(u=[n], response_counts=[k])
    if k > 1:
        shapes["p"] = [k]
    for name in ("volume", "shape"):
        if name == "shape" and k == 1:
            require(document[name] is None, "scalar annual cannot have a shape block")
            continue
        require(document[name] is not None, "annual block is missing")
        width = 1 if name == "volume" else k
        shapes.update(
            {
                name + "_" + field: shape
                for field, shape in dict(
                    M=[2 * n, width],
                    V=[2 * n, 2 * n],
                    A=[len(annual["strata"]), width],
                    prior_mean=[2 * n, width],
                    prior_covariance=[2 * n, 2 * n],
                ).items()
            }
        )
    require(document["shapes"] == shapes, "annual array shapes differ")
    with np.load(linked_path(document["arrays"]), allow_pickle=False) as arrays:
        require(set(arrays.files) == set(shapes), "annual array names differ")
        values = {name: arrays[name] for name in arrays.files}
    require(
        all(list(value.shape) == shapes[name] and np.isfinite(value).all() for name, value in values.items()),
        "annual arrays are nonfinite or incorrectly shaped",
    )
    with np.load(linked_path(annual["references"]), allow_pickle=False) as references:
        positions = {player: i for i, player in enumerate(players)}
        u = np.zeros(n)
        u[[positions[player] for player in current]] = references["u"]
        require(
            np.array_equal(values["u"], u)
            and np.array_equal(values["response_counts"], references["response_counts"])
            and (k == 1 or np.array_equal(values["p"], references["p"])),
            "annual fixed references differ",
        )
    blocks = {}
    for name in ("volume", "shape"):
        if document[name] is None:
            blocks[name] = None
            continue
        metadata = document[name]
        prior_block = None if previous is None else getattr(previous, name)
        M0, base, selected = _prior(players, previous, prior_block, 1 if name == "volume" else k)
        variance = metadata["scale"]["selected"]["variance"]
        require(
            math.isfinite(variance)
            and 1e-8 <= variance <= 1
            and metadata["a"] == (variance if prior_block is None else prior_block.a)
            and metadata["q"] == (None if prior_block is None else variance),
            "annual scale lineage differs",
        )
        base[selected, selected] += variance
        require(
            np.array_equal(values[name + "_prior_mean"], M0)
            and np.array_equal(values[name + "_prior_covariance"], base),
            "annual prior carry differs",
        )
        V = values[name + "_V"]
        M = values[name + "_M"]
        tolerance = metadata["diagnostics"]["covariance_rounding_tolerance"]
        require(
            np.max(np.abs(V - V.T)) <= tolerance
            and np.min(np.diag(V)) >= -tolerance
            and np.max(np.abs(u @ M[:n])) <= 1e-8
            and np.max(np.abs(u @ M[n:])) <= 1e-8,
            "annual covariance/centering contract failed",
        )
        if name == "shape":
            require(
                np.max(np.abs(M.sum(axis=1))) <= 1e-8
                and np.max(np.abs(values[name + "_A"].sum(axis=1))) <= 1e-8,
                "annual shape is not zero sum",
            )
        blocks[name] = BlockState(
            M,
            V,
            values[name + "_A"],
            M0,
            base,
            metadata["a"],
            metadata["q"],
            metadata["scale"],
            metadata["diagnostics"],
        )
    return AnnualState(
        document["benchmark"],
        document["season"],
        document["season_index"],
        document["protocol"]["sha256"],
        document["population_id"],
        players,
        current,
        tuple(document["entrant_ids"]),
        tuple(document["carried_only_ids"]),
        blocks["volume"],
        blocks["shape"],
        document["r"],
        values["u"],
        values.get("p"),
        values["response_counts"],
    )


def bounded_shape_resolution_check(
    population: RevisionPopulation, previous: AnnualState | None, state: AnnualState
) -> dict:
    """one conditional tightening of the saved shape fit; incoming priors stay fixed."""
    from dataclasses import replace
    from .chance_evaluation import REGION_NAMES, compound_regions
    from .shot_origins import grid

    require(state.shape is not None and population.p is not None, "shape resolution requires spatial state")
    players, H, T, xbar, u = _annual_inputs(population, previous)
    prior = None if previous is None else previous.shape
    M0, base, indices = _prior(players, previous, prior, len(population.p))
    require(np.array_equal(M0, state.shape.prior_mean), "resolution check changed incoming mean")
    Th = T - T.sum(axis=1, keepdims=True) * population.p
    yh = population.ybar - population.ybar.sum(axis=1, keepdims=True) * population.p
    problem = _ScaleProblem(H, Th, population.shape_yy, M0, base, indices, population.p)
    saved = state.shape.scale
    winner = saved["selected"]
    coarse = [
        row
        for row in saved["curve"]
        if row["phase"] == "coarse" and row["objective"] is not None and row["exponent"] != winner["exponent"]
    ]
    nearest = sorted(coarse, key=lambda row: (abs(row["exponent"] - winner["exponent"]), row["exponent"]))[:2]
    for row in [winner] + nearest:
        problem.objective(row["exponent"], "independent_recheck")
    refinement = None
    if saved["refinement"] is not None:
        bounds = saved["refinement"]["bounds"]
        fit = minimize_scalar(
            problem.objective, bounds=bounds, method="bounded", options={"xatol": 1e-6, "maxiter": 80}
        )
        refinement = dict(
            bounds=bounds,
            success=bool(fit.success),
            message=str(fit.message),
            evaluations=int(fit.nfev),
            exponent=float(fit.x) if math.isfinite(fit.x) else None,
            xatol=1e-6,
            maxiter=80,
        )
    valid = [row for row in saved["curve"] + problem.curve if row["objective"] is not None]
    selected = min(valid, key=lambda row: (row["objective"], row["variance"]))
    changed = _block_at_scale(
        H,
        Th,
        yh,
        xbar,
        M0,
        problem.covariance(selected["variance"]),
        prior,
        u,
        population.p,
        selected["variance"],
        saved,
        time.monotonic(),
    )
    alternative = replace(state, shape=changed)
    positions = {player: i for i, player in enumerate(state.player_ids)}
    n = len(state.player_ids)
    current = [positions[player] for player in state.current_player_ids]
    current = np.asarray(current + [n + i for i in current])
    delta = changed.M[current] - state.shape.M[current]
    cell_change = float(np.max(np.abs(delta)))
    scalar_change = float(np.max(np.abs(delta.sum(axis=1))))
    region_ids = compound_regions(grid()[0])
    regions = np.column_stack([region_ids == index for index in range(len(REGION_NAMES))]).astype(float)
    region_change = float(np.max(np.abs(delta @ regions)))
    changed_labels = dict(
        native_zero_exclusion=0, regional_zero_exclusion=0, scalar_zero_exclusion=0, scalar_meaningful_band=0
    )
    # all current-player cell and region working labels are recomputed from the
    # same public projection owner. these are diagnostics, not a new gate.
    for index in current:
        c = np.zeros(2 * n)
        c[index] = 1
        old, new = project_native(state, c), project_native(alternative, c)
        changed_labels["native_zero_exclusion"] += int(
            np.count_nonzero(
                ((old["lower"] > 0) != (new["lower"] > 0)) | ((old["upper"] < 0) != (new["upper"] < 0))
            )
        )
        for v in regions.T:
            old, new = project_interval(state, c, v), project_interval(alternative, c, v)
            changed_labels["regional_zero_exclusion"] += int(
                (old["lower"] > 0) != (new["lower"] > 0) or (old["upper"] < 0) != (new["upper"] < 0)
            )
        old, new = (
            project_interval(state, c, np.ones(len(population.p))),
            project_interval(alternative, c, np.ones(len(population.p))),
        )
        changed_labels["scalar_zero_exclusion"] += int(
            (old["lower"] > 0) != (new["lower"] > 0) or (old["upper"] < 0) != (new["upper"] < 0)
        )
        band = 0.05 * state.r

        def label(interval):
            return (
                interval["lower"] > band,
                interval["upper"] < -band,
                interval["lower"] >= -band and interval["upper"] <= band,
            )

        changed_labels["scalar_meaningful_band"] += int(label(old) != label(new))
    numerical_complete = all(
        row["objective"] is not None for row in problem.curve if row["phase"] == "independent_recheck"
    ) and (refinement is None or refinement["success"])
    return dict(
        status="verified"
        if numerical_complete and max(cell_change, scalar_change, region_change) <= 1e-4
        else "withheld",
        scope="conditional_per_fit_fixed_incoming_prior_not_propagated_history_or_coverage_bound",
        saved_winner=winner,
        rechecked_candidates=problem.curve,
        tightened_refinement=refinement,
        selected=selected,
        maximum_league_relative_current_player_movement=dict(
            native_cells=cell_change, scalars=scalar_change, regions=region_change
        ),
        tolerance=1e-4,
        working_label_changes=changed_labels,
        diagnostics=changed.diagnostics,
    )


def fit_prepared(prepared: Path | str, out: Path | str) -> dict:
    """fit the explicit two-population chronology and bind one completed manifest."""
    started = time.monotonic()
    prepared_path = Path(prepared).resolve(strict=True)
    source = read_revision_prepared(prepared_path)
    protocol = read_json(linked_path(source["protocol"]))
    current_implementation = implementation()
    if source["purpose"] == "research":
        clean_implementation(current_implementation)
        require(
            current_implementation == protocol["implementation"],
            "fit implementation differs from frozen protocol",
        )
    controls = {(row["benchmark"], row["season"]): row["state"] for row in source["baseline_controls"]}
    output = output_path(
        str(out), [str(prepared_path.parent)] + [str(linked_path(ref).parent) for ref in controls.values()]
    )
    require(
        output.is_relative_to(Path(protocol["output_root"]).resolve()), "fit output differs from frozen root"
    )
    if source["purpose"] == "research":
        require(
            output.is_relative_to(Path("/Volumes/Expansion/hockey-stats")),
            "research fits must remain external",
        )
    output.mkdir()
    completed = []
    for benchmark in POPULATIONS:
        previous = previous_path = None
        for index, season in enumerate(source["seasons"]):
            population = load_revision_population(prepared_path, benchmark, season)
            state = fit_revision_year(population, previous)
            control_ref = controls.get((benchmark, season))
            control_replay = (
                _control_replay(state, read_control_annual(linked_path(control_ref)))
                if control_ref is not None
                else None
            )
            resolution = None
            if benchmark == "unblocked_spatial" and index in (0, len(source["seasons"]) - 1):
                resolution = bounded_shape_resolution_check(population, previous, state)
            reference = write_annual(
                state,
                prepared_path,
                previous_path,
                output / f"{benchmark}-{season}",
                control=control_ref,
                control_replay=control_replay,
                resolution_check=resolution,
            )
            completed.append(dict(benchmark=benchmark, season=season, state=reference, control=control_ref))
            previous, previous_path = state, linked_path(reference)
    write_json(
        output / "fits.json",
        dict(
            schema_version=2,
            kind="attribution_revision_fits",
            purpose=source["purpose"],
            implementation=current_implementation,
            protocol=source["protocol"],
            prepared=identity(prepared_path),
            baseline_prepared=source["baseline_prepared"],
            population_ids=source["population_ids"],
            populations=list(POPULATIONS),
            seasons=source["seasons"],
            annual=completed,
            baseline_controls=source["baseline_controls"],
            status="complete",
            resources=resources(started),
        ),
    )
    return identity(output / "fits.json")


def read_fits(path: Path | str) -> tuple[dict, dict[tuple[str, str], AnnualState]]:
    """consume exactly the manifest's states; never infer a completed directory."""
    document = read_json(Path(path).resolve(strict=True))
    require(
        type(document["schema_version"]) is int
        and document["schema_version"] == 2
        and document["kind"] == "attribution_revision_fits"
        and document["status"] == "complete",
        "expected completed revision fits manifest",
    )
    source = read_revision_prepared(linked_path(document["prepared"]))
    require(
        all(
            document[key] == source[key]
            for key in (
                "protocol",
                "baseline_prepared",
                "population_ids",
                "populations",
                "seasons",
                "baseline_controls",
                "purpose",
            )
        ),
        "fits differ from prepared source/model",
    )
    expected = [(benchmark, season) for benchmark in POPULATIONS for season in source["seasons"]]
    require(
        [(row["benchmark"], row["season"]) for row in document["annual"]] == expected,
        "fits must bind exactly the ordered annual populations",
    )
    controls = {(row["benchmark"], row["season"]): row["state"] for row in source["baseline_controls"]}
    result = {}
    for row in document["annual"]:
        key = (row["benchmark"], row["season"])
        annual_path = linked_path(row["state"])
        annual = read_json(annual_path)
        require(
            annual["prepared"] == document["prepared"]
            and annual["protocol"] == document["protocol"]
            and row["control"] == controls.get(key) == annual["control"],
            "fits annual binding differs",
        )
        state = read_annual(annual_path)
        require((state.benchmark, state.season) == key, "fits annual identity differs")
        if state.season_index > 0:
            prior = next(
                item["state"]
                for item in document["annual"]
                if item["benchmark"] == state.benchmark
                and source["seasons"].index(item["season"]) == state.season_index - 1
            )
            require(annual["previous"] == prior, "fits annual predecessor differs")
        result[key] = state
    return document, result
