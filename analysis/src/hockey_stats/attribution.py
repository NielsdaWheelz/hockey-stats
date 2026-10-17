"""annual volume and zero-sum shape with independent full row covariances.

player columns are offense then defense. positive defense is opponent creation.
references are evidence, not fitted parameters. one owner fits and projects both
blocks; the shared-volume estimator survives only as a named scientific control.
"""

from dataclasses import dataclass
from functools import cached_property
import hashlib
import math
from pathlib import Path
import time
from typing import Literal

import numpy as np
from scipy.linalg import cho_solve, eigh, solve_triangular
from scipy.optimize import minimize_scalar

from .artifacts import (
    clean_implementation, implementation, linked_path, load_arrays, read_artifact, require, resources,
    write_arrays, write_json,
)
from .chance_cli import identity, output_path, read_json

from .attribution_data import (
    POPULATIONS,
    RevisionPopulation,
    read_recovery_prepared,
    read_revision_prepared,
)


@dataclass(frozen=True)
class ShapeBasis:
    B: np.ndarray
    p: np.ndarray
    eigenvalues: np.ndarray
    sha256: str

    @cached_property
    def R(self) -> np.ndarray:
        return self.p[:, None] * self.B


def _basis_identity(B: np.ndarray, p: np.ndarray, eigenvalues: np.ndarray) -> str:
    from .shot_origins import grid

    digest = hashlib.sha256()
    for value in (*grid(), p, B, eigenvalues):
        digest.update(np.ascontiguousarray(value).tobytes())
    return digest.hexdigest()


def build_shape_basis(geometry: tuple[np.ndarray, np.ndarray], p: np.ndarray) -> ShapeBasis:
    """one fixed 40-foot graph space, whitened in the original reference measure."""
    from .shot_origins import grid

    centers, edges = geometry
    expected_centers, expected_edges = grid()
    p = np.asarray(p, dtype=float)
    require(
        np.array_equal(centers, expected_centers)
        and np.array_equal(edges, expected_edges)
        and centers.shape == (656, 2)
        and p.shape == (656,)
        and np.isfinite(p).all()
        and np.all(p > 0)
        and math.isclose(float(p.sum()), 1, rel_tol=0, abs_tol=1e-12),
        "shape basis requires the fixed native grid and positive original shares",
    )
    laplacian = np.zeros((656, 656))
    laplacian[edges[:, 0], edges[:, 1]] = -1
    laplacian[edges[:, 1], edges[:, 0]] = -1
    np.fill_diagonal(laplacian, -laplacian.sum(axis=1))
    eigenvalues, eigenvectors = eigh(laplacian / 25, check_finite=False)
    cutoff = (2 * math.pi / 40) ** 2
    require(
        abs(eigenvalues[0]) <= 1e-12
        and eigenvalues[1] > 1e-12
        and eigenvalues[40] < cutoff - 1e-8
        and eigenvalues[41] > cutoff + 1e-8
        and np.count_nonzero((eigenvalues > 1e-12) & (eigenvalues <= cutoff)) == 40,
        "shape basis rank or cutoff separation differs from the frozen geometry",
    )
    F = eigenvectors[:, 1:41] - p @ eigenvectors[:, 1:41]
    factor = np.linalg.cholesky(F.T @ (p[:, None] * F))
    B = solve_triangular(factor, F.T, lower=True, check_finite=False).T
    require(
        np.max(np.abs(p @ B)) <= 1e-10
        and np.max(np.abs(B.T @ (p[:, None] * B) - np.eye(40))) <= 1e-10,
        "shape basis centering or whitening failed",
    )
    selected = eigenvalues[1:41].copy()
    return ShapeBasis(B, p.copy(), selected, _basis_identity(B, p, selected))


def read_shape_basis(prepared: dict) -> ShapeBasis:
    """read the one saved basis; do not recompute eigenvector signs in a history."""
    arrays = load_arrays(dict(arrays=prepared["basis"], array_shapes=prepared["basis_shapes"]))
    require(list(arrays) == ["B", "p", "eigenvalues"], "saved shape basis array order differs")
    B, p, eigenvalues = arrays["B"], arrays["p"], arrays["eigenvalues"]
    require(
        B.shape == (656, 40) and p.shape == (656,) and eigenvalues.shape == (40,)
        and np.all(p > 0) and math.isclose(float(p.sum()), 1, rel_tol=0, abs_tol=1e-12)
        and np.all(eigenvalues > 0) and np.all(np.diff(eigenvalues) >= 0)
        and eigenvalues[-1] < (2 * math.pi / 40) ** 2 - 1e-8
        and np.max(np.abs(p @ B)) <= 1e-10
        and np.max(np.abs(B.T @ (p[:, None] * B) - np.eye(40))) <= 1e-10
        and _basis_identity(B, p, eigenvalues) == prepared["basis_sha256"],
        "saved shape basis geometry, whitening or identity differs",
    )
    return ShapeBasis(B, p, eigenvalues, prepared["basis_sha256"])


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
class GraphShapeState:
    Theta: np.ndarray
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
    source_protocol_sha256: str
    model_protocol_sha256: str
    representation: Literal["native_04b", "graph_40ft"]
    basis: ShapeBasis | None
    population_id: str
    player_ids: tuple[int, ...]
    current_player_ids: tuple[int, ...]
    entrant_ids: tuple[int, ...]
    carried_only_ids: tuple[int, ...]
    volume: BlockState
    shape: BlockState | GraphShapeState | None
    r: float
    u: np.ndarray
    p: np.ndarray | None
    response_counts: np.ndarray | None


@dataclass(frozen=True)
class ControlAnnual:
    """frozen schema-1 control; strict rate signs use its original map arrays."""

    state: AnnualState
    original_M: np.ndarray
    original_A: np.ndarray


def read_native_04b_embedded_annual(
    record: dict, arrays: dict[str, np.ndarray], *, source_protocol_sha256: str,
    model_protocol_sha256: str, population_id: str, season_index: int,
) -> AnnualState:
    """saved 04b synthetic point blocks; their omitted response totals remain missing."""
    require(record["benchmark"] == "unblocked_spatial", "embedded native control must be explicitly spatial")
    players = tuple(record["player_ids"])
    n = len(players)
    prefix = record["volume"]["array_prefix"]
    require(prefix.endswith("_volume") and record["shape"]["array_prefix"] == prefix[:-7] + "_shape",
            "embedded native control block prefixes differ")
    base = prefix[:-7]
    u, p = arrays[base + "_u"], arrays[base + "_p"]
    require(players == tuple(sorted(set(players))) and u.shape == (n,) and p.shape == (656,)
            and np.isfinite(u).all() and np.isfinite(p).all() and np.all(p > 0)
            and abs(float(p.sum()) - 1) <= 1e-12 and abs(float(u.sum()) - 1) <= 1e-12,
            "embedded native control references or order differ")
    blocks = {}
    for name, width in (("volume", 1), ("shape", 656)):
        block = record[name]
        block_prefix = block["array_prefix"]
        values = {field: arrays[block_prefix + "_" + field]
                  for field in ("M", "V", "A", "prior_mean", "prior_covariance")}
        require(values["M"].shape == values["prior_mean"].shape == (2 * n, width)
                and values["V"].shape == values["prior_covariance"].shape == (2 * n, 2 * n)
                and values["A"].ndim == 2 and values["A"].shape[1] == width
                and all(np.isfinite(value).all() for value in values.values()),
                "embedded native control arrays differ")
        blocks[name] = BlockState(**values, **{field: block[field] for field in ("a", "q", "scale", "diagnostics")})
    return AnnualState(record["benchmark"], record["season"], season_index, source_protocol_sha256,
        model_protocol_sha256, "native_04b", None, population_id, players, tuple(record["current_player_ids"]),
        tuple(record["entrant_ids"]), tuple(record["carried_only_ids"]), blocks["volume"], blocks["shape"],
        record["r"], u, p, None)


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


def _coefficient_mean(block: BlockState | GraphShapeState) -> np.ndarray:
    return block.Theta if isinstance(block, GraphShapeState) else block.M


def _prior(
    players: tuple[int, ...], previous: AnnualState | None, block: BlockState | GraphShapeState | None, width: int
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
    M0[selected] = _coefficient_mean(block)
    return M0, covariance, selected


class _ScaleProblem:
    """cache response contractions once; each scale candidate solves row space."""

    def __init__(self, H, T, yy, M0, base_covariance, innovation_indices, p, *, basis=None):
        self.H, self.T, self.M0 = H, T, M0
        self.base_covariance, self.innovation_indices = base_covariance, innovation_indices
        self.b = T - H @ M0
        self.rank = basis.B.shape[1] if basis is not None else (1 if p is None else len(p) - 1)
        self.reduced = basis is not None
        if self.reduced:
            self.zz = float(yy - 2 * np.sum(M0 * T) + np.sum(M0 * (H @ M0)))
        elif p is None:
            self.zz = float(yy - 2 * M0[:, 0] @ T[:, 0] + M0[:, 0] @ H @ M0[:, 0])
        else:
            self.zz = float(yy - 2 * np.sum(M0 * T / p) + np.sum(M0 * (H @ M0) / p))
        self.B = self.b @ self.b.T if self.reduced else (None if p is None else (self.b / p) @ self.b.T)
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
            logdet = self.rank * 2 * np.log(np.diag(factor)).sum()
            # native 04b retains its original addition/selection arithmetic.
            value = float(logdet - contraction if self.reduced else logdet + self.zz - contraction)
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
        if self.reduced:
            self.curve[-1]["full_objective"] = float(value + self.zz) if error is None else None
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


def _center(M, V, A, weights, response_map=None):
    n = len(weights)
    off_mean, def_mean = weights @ M[:n], weights @ M[n:]
    M[:n] -= off_mean
    M[n:] -= def_mean
    compensation = off_mean + def_mean
    A += 5 * (compensation if response_map is None else compensation @ response_map.T)
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
    H, T, ybar, xbar, M0, covariance, previous, weights, p, variance, scale, started, *, basis=None
) -> BlockState | GraphShapeState:
    M, V, diagnostics = _posterior(H, T, M0, covariance)
    response_map = None if basis is None else basis.R
    native = M if response_map is None else M @ response_map.T
    M, V, A = _center(M, V, ybar - xbar @ native, weights, response_map)
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
        native = M if response_map is None else M @ response_map.T
        diagnostics["zero_sum_mean_residual"] = float(np.max(np.abs(native.sum(axis=1))))
        require(diagnostics["zero_sum_mean_residual"] <= 1e-8, "shape mean is not zero sum")
    state_type = BlockState if basis is None else GraphShapeState
    return state_type(
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
    H, T, yy, ybar, xbar, M0, base_covariance, innovation_indices, previous, weights, p, *, basis=None
) -> BlockState | GraphShapeState:
    started = time.monotonic()
    problem = _ScaleProblem(H, T, yy, M0, base_covariance, innovation_indices, p, basis=basis)
    inherited = previous is not None and previous.scale["status"] == "scale_unresolved"
    variance, scale = _select_scale(problem, inherited)
    return _block_at_scale(
        H, T, ybar, xbar, M0, problem.covariance(variance), previous, weights, p, variance, scale, started,
        basis=basis,
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
            and population.protocol_sha256 == previous.source_protocol_sha256
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


def _fit(
    population: "RevisionPopulation", previous: AnnualState | None, shared_volume: bool,
    *, representation: Literal["native_04b", "graph_40ft"], basis: ShapeBasis | None,
    model_protocol_sha256: str,
) -> AnnualState:
    require(
        (representation == "native_04b" and basis is None)
        or (
            representation == "graph_40ft"
            and basis is not None
            and population.p is not None
            and np.array_equal(population.p, basis.p)
            and basis.B.shape == (656, 40)
        ),
        "annual shape representation and fixed basis disagree",
    )
    require(
        bool(model_protocol_sha256)
        and (previous is None or (
            previous.model_protocol_sha256 == model_protocol_sha256
            and previous.representation == representation
            and ((basis is None and previous.basis is None)
                 or (basis is not None and previous.basis is not None
                     and basis.sha256 == previous.basis.sha256))
        )),
        "preceding annual state changed model protocol or shape basis",
    )
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
        width = len(p) if basis is None else basis.B.shape[1]
        M0, base, innovations = _prior(players, previous, prior_shape, width)
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
                H, Th if basis is None else Th @ basis.B, population.shape_yy,
                yh, xbar, M0, base, innovations, prior_shape, weights, p, basis=basis,
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
        model_protocol_sha256,
        representation,
        basis,
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
    """named native-04b scientific control, preserving its scale arithmetic."""
    return _fit(population, previous, False, representation="native_04b", basis=None,
                model_protocol_sha256=population.protocol_sha256)


def fit_recovery_year(
    population: RevisionPopulation, previous: AnnualState | None,
    *, representation: Literal["native_04b", "graph_40ft"], basis: ShapeBasis | None,
    model_protocol_sha256: str,
) -> AnnualState:
    """fit one explicitly selected representation against unchanged source references."""
    return _fit(population, previous, False, representation=representation, basis=basis,
                model_protocol_sha256=model_protocol_sha256)


def fit_shared_volume_control(population: "RevisionPopulation", previous: AnnualState | None) -> AnnualState:
    """scientific 04a control only: both blocks use the volume-selected scale."""
    return _fit(population, previous, True, representation="native_04b", basis=None,
                model_protocol_sha256=population.protocol_sha256)


def shape_mean(state: AnnualState) -> np.ndarray:
    """native relative shape; graph coefficients are decoded only at this boundary."""
    require(state.shape is not None, "scalar annual state has no spatial shape")
    if state.representation == "native_04b":
        require(isinstance(state.shape, BlockState) and state.basis is None,
                "native shape state has incompatible representation")
        return state.shape.M
    require(isinstance(state.shape, GraphShapeState) and state.basis is not None,
            "graph shape state has incompatible representation")
    return state.shape.Theta @ state.basis.R.T


def map_mean(state: AnnualState) -> np.ndarray:
    return state.volume.M if state.p is None else state.volume.M * state.p + shape_mean(state)


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
            mean = coefficients @ _coefficient_mean(block)[selected]
            variance = float(coefficients @ block.V[np.ix_(selected, selected)] @ coefficients)
            moments.append((mean, variance, block.diagnostics["covariance_rounding_tolerance"]))
    return c, moments


def project(
    state: AnnualState, player_contrast: np.ndarray, response_weights: np.ndarray,
    *, estimand: Literal["shape", "volume", "complete_rate"] = "complete_rate",
) -> tuple[float, float]:
    """physical mean and raw working variance for one joint linear projection."""
    c, moments = _row_moments(state, player_contrast)
    v = np.asarray(response_weights, dtype=float)
    k = 1 if state.p is None else len(state.p)
    require(v.shape == (k,) and np.isfinite(v).all(), "invalid response functional")
    require(estimand in ("shape", "volume", "complete_rate"), "unknown attribution estimand")
    require(state.p is not None or estimand != "shape", "scalar state has no shape estimand")
    if state.p is None:
        mean = state.r * moments[0][0][0] * v[0]
        variance = state.r**2 * moments[0][1] * v[0] ** 2
    else:
        # subtracting a constant exploits the exact zero-sum contract and makes
        # an all-ones functional exactly the fitted volume, even in roundoff.
        shifted = v - v[0]
        center = float(state.p @ shifted)
        volume = float(v[0] + center)
        if estimand == "shape":
            volume = 0.0
            shifted = shifted - center
            center = 0.0
        if estimand == "volume":
            shifted = np.zeros_like(shifted)
            center = 0.0
        if state.representation == "graph_40ft":
            response = state.basis.R.T @ shifted
            response_variance = float(response @ response)
        else:
            response = shifted
            response_variance = float(state.p @ (shifted - center) ** 2)
        mean = state.r * (moments[0][0][0] * volume + moments[1][0] @ response)
        variance = state.r**2 * (moments[0][1] * volume**2 + moments[1][1] * response_variance)
    tolerance = state.r**2 * float(c @ c) * float(v @ v) * sum(row[2] for row in moments)
    require(
        math.isfinite(mean) and math.isfinite(variance) and variance >= -tolerance,
        "invalid attribution projection variance",
    )
    return float(mean), float(variance)


def project_interval(
    state: AnnualState, player_contrast: np.ndarray, response_weights: np.ndarray,
    *, estimand: Literal["shape", "volume", "complete_rate"] = "complete_rate",
) -> dict:
    mean, variance = project(state, player_contrast, response_weights, estimand=estimand)
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


def project_native(
    state: AnnualState, player_contrast: np.ndarray,
    *, estimand: Literal["shape", "volume", "complete_rate"] = "complete_rate",
) -> dict:
    """all native cells, with the same two contracted row covariance terms."""
    c, moments = _row_moments(state, player_contrast)
    require(estimand in ("shape", "volume", "complete_rate"), "unknown attribution estimand")
    require(state.p is not None or estimand != "shape", "scalar state has no shape estimand")
    if state.p is None:
        mean = state.r * moments[0][0]
        variance = np.array([state.r**2 * moments[0][1]])
    else:
        if state.representation == "graph_40ft":
            R = state.basis.R
            native_shape = moments[1][0] @ R.T
            shape_variance = np.sum(R**2, axis=1)
        else:
            native_shape = moments[1][0]
            shape_variance = state.p * (1 - state.p)
        volume_mean = moments[0][0][0] * state.p if estimand != "shape" else np.zeros_like(state.p)
        volume_variance = moments[0][1] * state.p**2 if estimand != "shape" else np.zeros_like(state.p)
        if estimand == "volume":
            native_shape = np.zeros_like(state.p)
            shape_variance = np.zeros_like(state.p)
        mean = state.r * (volume_mean + native_shape)
        variance = state.r**2 * (volume_variance + moments[1][1] * shape_variance)
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
    shape = (
        state.shape.Theta[columns].sum(axis=1) @ state.basis.R.T
        if state.representation == "graph_40ft" else state.shape.M[columns].sum(axis=1)
    )
    return state.r * (volume * state.p + state.shape.A[contexts] + shape)


def negative_rate_summaries(batches, reference_rates: dict[str, float]) -> dict:
    """summarize several fixed models while reading each source batch once."""
    require(bool(reference_rates) and all(math.isfinite(rate) and rate > 0 for rate in reference_rates.values()),
            "negative-rate assessment requires positive references")
    totals = {name: dict(seconds=0., negative_seconds=0., negative_cell_seconds=0., negative_mass=0.,
                        negative_rows=0, negative_cells=0, rows=0, minimum_total=math.inf,
                        minimum_cell=math.inf, complete_example=None, cell_example=None, cells=None)
              for name in reference_rates}
    for fitted_rates, seconds, locators in batches:
        require(set(fitted_rates) == set(reference_rates), "rate diagnostic model set changed")
        for name, rates in fitted_rates.items():
            total = totals[name]
            require(rates.ndim == 2 and seconds.shape == (len(rates),) and len(locators) == len(rates)
                    and np.isfinite(rates).all() and np.isfinite(seconds).all() and np.all(seconds > 0),
                    "invalid fitted-rate diagnostic batch")
            require(total["cells"] is None or rates.shape[1] == total["cells"],
                    "fitted-rate response width changed")
            total["cells"] = rates.shape[1]
            scalar = rates.sum(axis=1)
            cell_negatives = (rates < 0).sum(axis=1)
            total["rows"] += len(rates)
            total["seconds"] += float(seconds.sum())
            total["negative_rows"] += int(np.sum(scalar < 0))
            total["negative_cells"] += int(cell_negatives.sum())
            total["negative_seconds"] += float(seconds @ (scalar < 0))
            total["negative_cell_seconds"] += float(seconds @ cell_negatives)
            total["negative_mass"] += float(seconds @ np.maximum(-rates, 0).sum(axis=1))
            row = int(np.argmin(scalar))
            if scalar[row] < total["minimum_total"]:
                total["minimum_total"] = float(scalar[row])
                total["complete_example"] = dict(row=locators[row], rate=total["minimum_total"])
            row, cell = np.unravel_index(np.argmin(rates), rates.shape)
            if rates[row, cell] < total["minimum_cell"]:
                total["minimum_cell"] = float(rates[row, cell])
                total["cell_example"] = dict(row=locators[int(row)], cell_id=int(cell), rate=total["minimum_cell"])
    result = {}
    for name, total in totals.items():
        require(total["rows"] > 0 and total["seconds"] > 0, "negative-rate assessment requires admitted rows")
        result[name] = dict(
            rows=total["rows"], team_seconds=total["seconds"],
            negative_complete_rates=total["negative_rows"], negative_cell_rates=total["negative_cells"],
            minimum_complete_rate=total["minimum_total"], minimum_cell_rate=total["minimum_cell"],
            minimum_complete_example=total["complete_example"], minimum_cell_example=total["cell_example"],
            exposure_weighted_negative_complete_frequency=total["negative_seconds"] / total["seconds"],
            exposure_weighted_negative_cell_frequency=total["negative_cell_seconds"] / (total["seconds"] * total["cells"]),
            negative_mass=total["negative_mass"] / (reference_rates[name] * total["seconds"]),
        )
    return result


def negative_rate_summary(batches, reference_rate: float) -> dict:
    return negative_rate_summaries((({"model": rates}, seconds, locators)
                                    for rates, seconds, locators in batches), {"model": reference_rate})["model"]


def _rate_row_batches(player_ids: tuple[int, ...], count_rows, strata: list):
    n = len(player_ids)
    positions = {player: i for i, player in enumerate(player_ids)}
    contexts = {tuple(value): i for i, value in enumerate(strata)}
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
            yield np.asarray(columns), np.asarray(context_ids), np.asarray(seconds), locators
            columns, context_ids, seconds, locators = [], [], [], []
    if columns:
        yield np.asarray(columns), np.asarray(context_ids), np.asarray(seconds), locators


def negative_rates(state: AnnualState, count_rows, strata: list) -> dict:
    return negative_rate_summary(
        (
            (complete_rates(state, columns, contexts), seconds, locators)
            for columns, contexts, seconds, locators in _rate_row_batches(
                state.player_ids, count_rows, strata
            )
        ),
        state.r,
    )


def control_negative_rates(control: ControlAnnual, count_rows, strata: list) -> dict:
    """evaluate the frozen control's original arithmetic, including exact zeros."""
    state = control.state
    return negative_rate_summary(
        (
            (
                state.r * (control.original_A[contexts] + control.original_M[columns].sum(axis=1)),
                seconds,
                locators,
            )
            for columns, contexts, seconds, locators in _rate_row_batches(
                state.player_ids, count_rows, strata
            )
        ),
        state.r,
    )


def compare_negative_rates(candidate: AnnualState, native_04b: AnnualState, native_04a: ControlAnnual,
                           count_rows, strata: list) -> dict:
    """one original ledger pass; each historical control keeps its own strict-sign arithmetic."""
    require(candidate.player_ids == native_04b.player_ids == native_04a.state.player_ids
            and candidate.r == native_04b.r == native_04a.state.r,
            "rate comparison requires the same original player and rate references")

    def batches():
        for columns, contexts, seconds, locators in _rate_row_batches(candidate.player_ids, count_rows, strata):
            yield dict(graph_40ft=complete_rates(candidate, columns, contexts),
                       native_04b=complete_rates(native_04b, columns, contexts),
                       native_04a=native_04a.state.r * (
                           native_04a.original_A[contexts] + native_04a.original_M[columns].sum(axis=1))), seconds, locators

    return negative_rate_summaries(batches(),
                                  {name: candidate.r for name in ("graph_40ft", "native_04b", "native_04a")})


def read_control_annual(path: Path | str) -> ControlAnnual:
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
    state = AnnualState(
        document["benchmark"],
        document["season"],
        document["season_index"],
        document["protocol"]["sha256"],
        document["protocol"]["sha256"],
        "native_04b",
        None,
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

    return ControlAnnual(state, values["M"], values["A"])


def read_native_04b_annual(path: Path | str) -> AnnualState:
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
    previous = read_native_04b_annual(previous_path) if previous_path is not None else None
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
        document["protocol"]["sha256"],
        "native_04b",
        None,
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


def _recovery_source(prepared: Path) -> tuple[dict, dict, dict]:
    document = read_recovery_prepared(prepared)
    source = read_revision_prepared(linked_path(document["source_prepared"]))
    protocol = read_artifact(linked_path(document["model_protocol"]), "attribution_recovery_protocol")
    return document, source, protocol


def annual_arrays(state: AnnualState) -> tuple[dict, dict[str, np.ndarray]]:
    """one coefficient/block serialization for annual files and embedded point histories."""
    require(state.response_counts is not None, "active annual artifacts require original response totals")
    values = dict(u=state.u, response_counts=state.response_counts)
    if state.p is not None:
        values["p"] = state.p
    blocks = {}
    for name in ("volume", "shape"):
        block = getattr(state, name)
        if block is None:
            blocks[name] = None
            continue
        mean_name = "Theta" if isinstance(block, GraphShapeState) else "M"
        values[name + "_" + mean_name] = _coefficient_mean(block)
        for field in ("V", "A", "prior_mean", "prior_covariance"):
            values[name + "_" + field] = getattr(block, field)
        blocks[name] = dict(a=block.a, q=block.q, scale=block.scale, diagnostics=block.diagnostics)
    return blocks, values


def write_recovery_annual(
    state: AnnualState, prepared: Path | str, previous: Path | str | None, out: Path | str,
    *, source_kind: Literal["recorded"], control_replay: dict | None = None,
    resolution_check: dict | None = None,
) -> dict:
    """write schema 3 with separate source preparation and model protocol bindings."""
    prepared_path = Path(prepared).resolve(strict=True)
    document, source, protocol = _recovery_source(prepared_path)
    require(source_kind == "recorded" and state.source_protocol_sha256 == source["protocol"]["sha256"]
            and state.model_protocol_sha256 == document["model_protocol"]["sha256"],
            "annual state changed source or model protocol")
    annual = next(row for row in source["annual"]
                  if row["population"] == state.benchmark and row["season"] == state.season)
    positions = {player: i for i, player in enumerate(state.player_ids)}
    with np.load(linked_path(annual["references"]), allow_pickle=False) as references:
        u = np.zeros(len(positions))
        require(state.current_player_ids == tuple(annual["players"]),
                "recorded annual current population differs")
        u[[positions[player] for player in state.current_player_ids]] = references["u"]
        require(state.population_id == source["population_ids"][state.benchmark]
                and state.season_index == source["seasons"].index(state.season) and state.r == annual["r"]
                and np.array_equal(state.u, u)
                and np.array_equal(state.response_counts, references["response_counts"])
                and (state.p is None or np.array_equal(state.p, references["p"])),
                "recorded annual original source references differ")
    previous_path = Path(previous).resolve(strict=True) if previous is not None else None
    output = output_path(str(out), [str(prepared_path.parent),
                                  *([str(previous_path.parent)] if previous_path else [])])
    require(output.is_relative_to(Path(protocol["output_root"]).resolve()),
            "annual output differs from frozen recovery root")
    producer = implementation()
    if document["purpose"] == "research":
        clean_implementation(producer)
        require(producer == protocol["implementation"]
                and output.is_relative_to(Path("/Volumes/Expansion/hockey-stats/runs")),
                "research annual implementation or external root differs")
    basis = state.basis
    require((state.representation == "native_04b" and basis is None)
            or (state.representation == "graph_40ft" and basis is not None
                and basis.sha256 == document["basis_sha256"]),
            "annual basis differs from recovery preparation")
    blocks, values = annual_arrays(state)
    output.mkdir()
    arrays = write_arrays(output, "state.npz", values)
    write_json(output / "annual.json", dict(
        schema_version=3, kind="attribution_recovery_annual", purpose=document["purpose"],
        implementation=producer, prepared=identity(prepared_path),
        source_prepared=document["source_prepared"], model_protocol=document["model_protocol"],
        consumed=dict(prepared=identity(prepared_path), source_prepared=document["source_prepared"],
                      model_protocol=document["model_protocol"],
                      previous=identity(previous_path) if previous_path is not None else None,
                      basis=document["basis"] if basis is not None else None),
        source_kind=source_kind,
        representation=state.representation,
        basis=document["basis"] if basis is not None else None,
        basis_shapes=document["basis_shapes"] if basis is not None else None,
        basis_sha256=basis.sha256 if basis is not None else None,
        previous=identity(previous_path) if previous_path is not None else None,
        benchmark=state.benchmark, season=state.season, season_index=state.season_index,
        population_id=state.population_id, player_ids=state.player_ids,
        current_player_ids=state.current_player_ids, entrant_ids=state.entrant_ids,
        carried_only_ids=state.carried_only_ids, r=state.r, strata=annual["strata"],
        volume=blocks["volume"], shape=blocks["shape"], **arrays,
        control_replay=control_replay, shape_resolution_check=resolution_check,
        units=dict(M="relative league team rate", Theta="whitened relative shape coefficient",
                   V="relative-rate-squared full row covariance", A="relative league native team rate",
                   r="attempts per 60 team minutes", u="fixed original exposure share",
                   p="fixed positive first-season native share"),
    ))
    return identity(output / "annual.json")


def read_recovery_annual(path: Path | str) -> AnnualState:
    """schema 3 exclusively; source and chronological model contracts are independent."""
    document = read_json(Path(path).resolve(strict=True))
    require(type(document.get("schema_version")) is int and document["schema_version"] == 3
            and document.get("kind") == "attribution_recovery_annual" and document.get("source_kind") == "recorded",
            "expected recovery annual state")
    prepared, source, protocol = _recovery_source(linked_path(document["prepared"]))
    require(document["source_prepared"] == prepared["source_prepared"]
            and document["model_protocol"] == prepared["model_protocol"]
            and document["purpose"] == prepared["purpose"],
            "annual source preparation or model protocol differs")
    require(document.get("consumed") == {name: document[name] for name in
                                         ("prepared", "source_prepared", "model_protocol", "previous", "basis")},
            "annual consumed identities differ")
    if document["purpose"] == "research":
        clean_implementation(document["implementation"])
        require(document["implementation"] == protocol["implementation"],
                "annual producer differs from frozen recovery protocol")
    representation = document["representation"]
    if representation == "graph_40ft":
        require(document["benchmark"] == "unblocked_spatial"
                and all(document[name] == prepared[name] for name in ("basis", "basis_shapes", "basis_sha256")),
                "graph annual changed its fixed basis")
        basis = read_shape_basis(prepared)
    else:
        require(representation == "native_04b" and document["basis"] is None
                and document["basis_shapes"] is None and document["basis_sha256"] is None,
                "native annual cannot carry a graph basis")
        basis = None
    previous_path = linked_path(document["previous"]) if document["previous"] is not None else None
    previous = read_recovery_annual(previous_path) if previous_path is not None else None
    if previous_path is not None:
        prior_document = read_json(previous_path)
        require(all(prior_document[name] == document[name]
                    for name in ("prepared", "source_prepared", "model_protocol", "purpose",
                                 "population_id", "benchmark", "representation", "basis_sha256")),
                "annual lineage changed source, model or representation")
    annuals = [row for row in source["annual"]
               if row["population"] == document["benchmark"] and row["season"] == document["season"]]
    require(len(annuals) == 1, "annual source population is absent or duplicated")
    annual = annuals[0]
    players, current = tuple(document["player_ids"]), tuple(document["current_player_ids"])
    require(players == tuple(sorted(set(players))) and current == tuple(annual["players"])
            and document["carried_only_ids"] == sorted(set(players) - set(current))
            and document["entrant_ids"] == sorted(set(current) - (set(previous.player_ids) if previous else set()))
            and set(players) == set(current) | (set(previous.player_ids) if previous else set())
            and document["strata"] == annual["strata"] and document["r"] == annual["r"]
            and document["population_id"] == source["population_ids"][document["benchmark"]]
            and document["season_index"] == source["seasons"].index(document["season"])
            and ((previous is None and document["season_index"] == 0)
                 or (previous is not None and document["season_index"] == previous.season_index + 1
                     and int(document["season"][:4]) == int(previous.season[:4]) + 1)),
            "annual source order or chronology differs")
    n, s = len(players), len(annual["strata"])
    k = 1 if document["benchmark"] == "all_attempts" else 656
    shapes = dict(u=(n,), response_counts=(k,))
    if k > 1:
        shapes["p"] = (k,)
    for name in ("volume", "shape"):
        if name == "shape" and k == 1:
            require(document[name] is None, "scalar annual cannot contain shape")
            continue
        require(document[name] is not None, "annual block is absent")
        graph = name == "shape" and representation == "graph_40ft"
        shapes[name + ("_Theta" if graph else "_M")] = (2 * n, 40 if graph else (1 if name == "volume" else k))
        shapes[name + "_V"] = (2 * n, 2 * n)
        shapes[name + "_A"] = (s, 1 if name == "volume" else k)
        shapes[name + "_prior_mean"] = shapes[name + ("_Theta" if graph else "_M")]
        shapes[name + "_prior_covariance"] = (2 * n, 2 * n)
    values = load_arrays(document)
    require(list(values) == list(shapes) and all(value.shape == shapes[name] for name, value in values.items()),
            "annual ordered array shapes differ")
    with np.load(linked_path(annual["references"]), allow_pickle=False) as references:
        positions = {player: i for i, player in enumerate(players)}
        u = np.zeros(n)
        u[[positions[player] for player in current]] = references["u"]
        require(np.array_equal(values["u"], u)
                and np.array_equal(values["response_counts"], references["response_counts"])
                and (k == 1 or np.array_equal(values["p"], references["p"]))
                and (basis is None or np.array_equal(basis.p, references["p"])),
                "annual original references differ")
    blocks = {}
    for name in ("volume", "shape"):
        if document[name] is None:
            blocks[name] = None
            continue
        graph = name == "shape" and basis is not None
        metadata = document[name]
        prior = None if previous is None else getattr(previous, name)
        width = 40 if graph else (1 if name == "volume" else k)
        M0, covariance, selected = _prior(players, previous, prior, width)
        variance = metadata["scale"]["selected"]["variance"]
        require(math.isfinite(variance) and 1e-8 <= variance <= 1
                and metadata["a"] == (variance if prior is None else prior.a)
                and metadata["q"] == (None if prior is None else variance),
                "annual scale lineage differs")
        covariance[selected, selected] += variance
        require(np.array_equal(values[name + "_prior_mean"], M0)
                and np.array_equal(values[name + "_prior_covariance"], covariance),
                "annual prior carry differs")
        M = values[name + ("_Theta" if graph else "_M")]
        V, A = values[name + "_V"], values[name + "_A"]
        tolerance = metadata["diagnostics"]["covariance_rounding_tolerance"]
        require(math.isfinite(tolerance) and tolerance >= 0
                and np.max(np.abs(V - V.T)) <= tolerance and np.min(np.diag(V)) >= -tolerance
                and np.max(np.abs(u @ M[:n])) <= 1e-8 and np.max(np.abs(u @ M[n:])) <= 1e-8,
                "annual covariance or exposure centering differs")
        if name == "shape":
            native = M @ basis.R.T if graph else M
            require(np.max(np.abs(native.sum(axis=1))) <= 1e-8 and np.max(np.abs(A.sum(axis=1))) <= 1e-8,
                    "annual shape or native context is not zero sum")
        state_type = GraphShapeState if graph else BlockState
        blocks[name] = state_type(M, V, A, M0, covariance, metadata["a"], metadata["q"],
                                  metadata["scale"], metadata["diagnostics"])
    return AnnualState(document["benchmark"], document["season"], document["season_index"],
                       source["protocol"]["sha256"], document["model_protocol"]["sha256"], representation, basis,
                       document["population_id"], players, current, tuple(document["entrant_ids"]),
                       tuple(document["carried_only_ids"]), blocks["volume"], blocks["shape"], document["r"],
                       values["u"], values.get("p"), values["response_counts"])


def bounded_shape_resolution_check(
    population: RevisionPopulation, previous: AnnualState | None, state: AnnualState,
    *, regions: np.ndarray | None = None,
    projections: tuple[tuple[np.ndarray, np.ndarray, str], ...] = (),
) -> dict:
    """one conditional tightening of the saved shape fit; incoming priors stay fixed."""
    from dataclasses import replace
    from .chance_evaluation import REGION_NAMES, compound_regions
    from .shot_origins import grid

    require(state.shape is not None and population.p is not None, "shape resolution requires spatial state")
    players, H, T, xbar, u = _annual_inputs(population, previous)
    prior = None if previous is None else previous.shape
    basis = state.basis
    width = len(population.p) if basis is None else basis.B.shape[1]
    M0, base, indices = _prior(players, previous, prior, width)
    require(np.array_equal(M0, state.shape.prior_mean), "resolution check changed incoming mean")
    Th = T - T.sum(axis=1, keepdims=True) * population.p
    if basis is not None:
        Th = Th @ basis.B
    yh = population.ybar - population.ybar.sum(axis=1, keepdims=True) * population.p
    problem = _ScaleProblem(H, Th, population.shape_yy, M0, base, indices, population.p, basis=basis)
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
        basis=basis,
    )
    alternative = replace(state, shape=changed)
    positions = {player: i for i, player in enumerate(state.player_ids)}
    n = len(state.player_ids)
    current = [positions[player] for player in state.current_player_ids]
    current = np.asarray(current + [n + i for i in current])
    delta = shape_mean(alternative)[current] - shape_mean(state)[current]
    cell_change = float(np.max(np.abs(delta)))
    scalar_change = float(np.max(np.abs(delta.sum(axis=1))))
    if regions is None:
        require(basis is None, "graph resolution check requires the study's fixed regional operator")
        region_ids = compound_regions(grid()[0])
        regions = np.column_stack([region_ids == index for index in range(len(REGION_NAMES))]).astype(float)
    require(regions.shape[0] == len(population.p) and np.isfinite(regions).all(),
            "invalid resolution region operator")
    region_change = float(np.max(np.abs(delta @ regions)))
    changed_labels = dict(
        native_zero_exclusion=0, regional_zero_exclusion=0, scalar_zero_exclusion=0, scalar_meaningful_band=0
    )
    interval_change = 0.0
    # all current-player cell and region working labels are recomputed from the
    # same public projection owner. these are diagnostics, not a new gate.
    for index in current:
        c = np.zeros(2 * n)
        c[index] = 1
        old, new = project_native(state, c), project_native(alternative, c)
        interval_change = max(interval_change, float(np.max(np.abs(new["lower"] - old["lower"])) / state.r),
                              float(np.max(np.abs(new["upper"] - old["upper"])) / state.r))
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
    requested_change = 0.0
    for c, v, estimand in projections:
        old = project_interval(state, c, v, estimand=estimand)
        new = project_interval(alternative, c, v, estimand=estimand)
        requested_change = max(requested_change, abs(new["mean"] - old["mean"]) / state.r)
        interval_change = max(interval_change, abs(new["lower"] - old["lower"]) / state.r,
                              abs(new["upper"] - old["upper"]) / state.r)
    numerical_complete = all(row["objective"] is not None for row in problem.curve) and (
        refinement is None or refinement["success"])
    return dict(
        status="verified"
        if numerical_complete and max(cell_change, scalar_change, region_change, requested_change) <= 1e-4
        else "withheld",
        scope="conditional_per_fit_fixed_incoming_prior_not_propagated_history_or_coverage_bound",
        saved_winner=winner,
        rechecked_candidates=problem.curve,
        tightened_refinement=refinement,
        selected=selected,
        saved_scale_status={name: saved[name] for name in
                            ("status", "own_reasons", "inherited_limitation")},
        maximum_league_relative_current_player_movement=dict(
            native_cells=cell_change, scalars=scalar_change, regions=region_change,
            requested_projections=requested_change,
        ),
        maximum_league_relative_working_interval_movement=interval_change,
        tolerance=1e-4,
        working_label_changes=changed_labels,
        diagnostics=changed.diagnostics,
    )


def read_native_04b_fits(path: Path | str) -> tuple[dict, dict[tuple[str, str], AnnualState]]:
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
        state = read_native_04b_annual(annual_path)
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
