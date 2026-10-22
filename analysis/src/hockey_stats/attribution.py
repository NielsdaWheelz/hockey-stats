"""annual volume and zero-sum shape with independent full row covariances.

player columns are offense then defense. positive defense is opponent creation.
references are evidence, not fitted parameters. one owner fits and projects both
blocks; the shared-volume estimator survives only as a named scientific control.
"""

from dataclasses import dataclass, replace
from functools import cached_property
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Literal

import numpy as np
from scipy.linalg import cho_solve, eigh, solve_triangular
from scipy.optimize import minimize, minimize_scalar

from .artifacts import (
    artifact, clean_implementation, digest, implementation, linked_path, load_arrays,
    ordered_array_digest, read_artifact, require, resources,
    write_arrays, write_json,
)
from .chance_cli import identity, output_path, read_json
from .captures import InputContractError

from .attribution_data import (
    POPULATIONS,
    POOLING_STAT_FIELDS,
    PooledShapeLikelihood,
    RevisionPopulation,
    likelihood_spectrum,
    pooling_population,
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
    return decode_shape_basis(arrays, basis_sha256=prepared["basis_sha256"])


def decode_shape_basis(arrays: dict[str, np.ndarray], *, basis_sha256: str) -> ShapeBasis:
    """validate the fixed graph geometry from one already loaded ordered archive."""
    require(list(arrays) == ["B", "p", "eigenvalues"], "saved shape basis array order differs")
    B, p, eigenvalues = arrays["B"], arrays["p"], arrays["eigenvalues"]
    require(
        B.shape == (656, 40) and p.shape == (656,) and eigenvalues.shape == (40,)
        and np.all(p > 0) and math.isclose(float(p.sum()), 1, rel_tol=0, abs_tol=1e-12)
        and np.all(eigenvalues > 0) and np.all(np.diff(eigenvalues) >= 0)
        and eigenvalues[-1] < (2 * math.pi / 40) ** 2 - 1e-8
        and np.max(np.abs(p @ B)) <= 1e-10
        and np.max(np.abs(B.T @ (p[:, None] * B) - np.eye(40))) <= 1e-10
        and _basis_identity(B, p, eigenvalues) == basis_sha256,
        "saved shape basis geometry, whitening or identity differs",
    )
    return ShapeBasis(B, p, eigenvalues, basis_sha256)


def validate_pooling_basis(basis: ShapeBasis) -> dict:
    """verify the saved nested low space without changing its columns or signs."""
    from .shot_origins import grid

    decode_shape_basis(dict(B=basis.B, p=basis.p, eigenvalues=basis.eigenvalues),
                       basis_sha256=basis.sha256)
    cutoff = (2 * math.pi / 80) ** 2
    require(basis.eigenvalues[10] < cutoff - 1e-8
            and basis.eigenvalues[11] > cutoff + 1e-8
            and np.count_nonzero(basis.eigenvalues <= cutoff) == 11,
            "two-band cutoff rank or separation differs from the saved graph")
    centers, edges = grid()
    laplacian = np.zeros((len(centers), len(centers)))
    laplacian[edges[:, 0], edges[:, 1]] = -1
    laplacian[edges[:, 1], edges[:, 0]] = -1
    np.fill_diagonal(laplacian, -laplacian.sum(axis=1))
    values, vectors = eigh(laplacian / 25, subset_by_index=(0, 12), check_finite=False)
    require(np.allclose(values[1:12], basis.eigenvalues[:11], rtol=1e-8, atol=1e-10),
            "saved low-band eigenvalue ordering differs")
    expected = vectors[:, 1:12] - basis.p @ vectors[:, 1:12]
    expected, _ = np.linalg.qr(np.sqrt(basis.p)[:, None] * expected)
    actual = np.sqrt(basis.p)[:, None] * basis.B[:, :11]
    residual = float(np.linalg.norm(actual - expected @ (expected.T @ actual), ord=2))
    require(residual <= 1e-8, "saved first eleven columns are not the nested low graph space")
    return dict(low_rank=11, high_rank=29, cutoff=cutoff,
                low_largest_eigenvalue=float(basis.eigenvalues[10]),
                high_smallest_eigenvalue=float(basis.eigenvalues[11]),
                nested_subspace_relative_residual=residual, basis_sha256=basis.sha256)


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
    historical_prior_mean: np.ndarray | None = None
    historical_prior_covariance: np.ndarray | None = None


@dataclass(frozen=True)
class ShapeBandState:
    Theta: np.ndarray
    V: np.ndarray
    prior_mean: np.ndarray
    prior_covariance: np.ndarray
    a: float
    q: float | None
    scale: dict
    diagnostics: dict


@dataclass(frozen=True)
class TwoBandShapeState:
    low: ShapeBandState
    high: ShapeBandState
    A: np.ndarray
    diagnostics: dict


@dataclass(frozen=True)
class PoolingSource:
    reference: dict
    prepared: dict
    protocol: dict
    basis: ShapeBasis


@dataclass(frozen=True)
class PoolingStatistics:
    reference: dict
    prepared_sha256: str
    arrays: dict[str, np.ndarray]


POOLING_UNITS = dict(M="relative league team rate", Theta="whitened relative shape coefficient",
    V="relative-rate-squared full row covariance", A="relative league native team rate",
    r="attempts per 60 team minutes", u="fixed training exposure share", p="fixed positive native share")
POOLING_PROBE_SCOPE = "conditional_per_fit_fixed_incoming_prior_not_propagated_history_or_global_optimum"


@dataclass(frozen=True)
class ShapeUpdate:
    mean: np.ndarray
    covariance: np.ndarray
    gain: np.ndarray
    uncentered_covariance: np.ndarray
    diagnostics: dict


@dataclass(frozen=True)
class ShapeCoefficientLikelihood:
    """one current-player gaussian shape score, without response energy or context."""

    season: str
    player_ids: tuple[int, ...]
    H: np.ndarray
    Q: np.ndarray
    u: np.ndarray
    r: float
    basis: ShapeBasis
    source_identity: dict


@dataclass(frozen=True)
class ShapeCoefficientState:
    """centered annual coefficients; covariance covers every previously seen identity."""

    season: str
    player_ids: tuple[int, ...]
    current_player_ids: tuple[int, ...]
    entrant_ids: tuple[int, ...]
    carried_only_ids: tuple[int, ...]
    Theta: np.ndarray
    V: np.ndarray
    u: np.ndarray
    r: float
    a: float
    q: float | None
    basis_sha256: str
    source_identity: dict
    scale: dict
    diagnostics: dict
    uncentered_Theta: np.ndarray
    centering_shift: np.ndarray


@dataclass(frozen=True)
class ScalarCoefficientLikelihood:
    """matched spatial-count volume score and retained scalar response energy."""

    season: str
    player_ids: tuple[int, ...]
    H: np.ndarray
    score: np.ndarray
    energy: float
    u: np.ndarray
    r: float
    source_identity: dict


@dataclass(frozen=True)
class ScalarScoreLikelihood:
    """scalar working least-squares score, without an invented response energy."""

    season: str
    player_ids: tuple[int, ...]
    H: np.ndarray
    score: np.ndarray
    u: np.ndarray
    r: float
    source_identity: dict


@dataclass(frozen=True)
class ScalarCoefficientState:
    """annual league-relative volume; covariance includes every historical identity."""

    season: str
    player_ids: tuple[int, ...]
    current_player_ids: tuple[int, ...]
    entrant_ids: tuple[int, ...]
    carried_only_ids: tuple[int, ...]
    beta: np.ndarray
    V: np.ndarray
    u: np.ndarray
    r: float
    a: float
    q: float | None
    source_identity: dict
    scale: dict
    diagnostics: dict
    uncentered_beta: np.ndarray
    centering_shift: np.ndarray


@dataclass(frozen=True)
class _CoefficientUpdate:
    mean: np.ndarray
    covariance: np.ndarray
    uncentered_mean: np.ndarray
    uncentered_covariance: np.ndarray
    centering_shift: np.ndarray
    diagnostics: dict


@dataclass(frozen=True)
class AnnualState:
    benchmark: str
    season: str
    season_index: int
    source_protocol_sha256: str
    model_protocol_sha256: str
    representation: Literal["native_04b", "graph_40ft", "graph_two_band_80ft"]
    basis: ShapeBasis | None
    population_id: str
    player_ids: tuple[int, ...]
    current_player_ids: tuple[int, ...]
    entrant_ids: tuple[int, ...]
    carried_only_ids: tuple[int, ...]
    volume: BlockState
    shape: BlockState | GraphShapeState | TwoBandShapeState | None
    r: float
    u: np.ndarray
    p: np.ndarray | None
    response_counts: np.ndarray | None
    prior_policy: Literal["history", "population_history"]


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
        record["r"], u, p, None, "history")


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
    H: np.ndarray, T: np.ndarray, M0: np.ndarray, V0: np.ndarray,
    *, factorization: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """a proper prior is factored, never a centered posterior covariance."""
    L, K, factor = _factor(H, V0) if factorization is None else factorization
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


def _coefficient_mean(
    block: BlockState | GraphShapeState | ShapeBandState | ShapeCoefficientState | ScalarCoefficientState,
) -> np.ndarray:
    if isinstance(block, BlockState):
        return block.M
    return block.beta if isinstance(block, ScalarCoefficientState) else block.Theta


def _prior(
    players: tuple[int, ...], previous: AnnualState | ShapeCoefficientState | ScalarCoefficientState | None,
    block: BlockState | GraphShapeState | ShapeBandState | ShapeCoefficientState | ScalarCoefficientState | None, width: int
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


def population_history_prior(
    historical_mean: np.ndarray, historical_covariance: np.ndarray, population_precision: float,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """normalize the historical gaussian times one zero-centered population factor."""
    require(type(population_precision) in (int, float) and math.isfinite(population_precision)
            and population_precision >= 0 and historical_mean.ndim == 2
            and historical_covariance.shape == (len(historical_mean), len(historical_mean))
            and np.isfinite(historical_mean).all() and np.isfinite(historical_covariance).all()
            and np.allclose(historical_covariance, historical_covariance.T, rtol=1e-10, atol=1e-10),
            "invalid population-history prior")
    L = np.linalg.cholesky(historical_covariance)
    if population_precision == 0:
        return historical_mean, historical_covariance, dict(equation_relative_residual=0.)
    K = np.eye(len(L)) + population_precision * (L.T @ L)
    factor = np.linalg.cholesky(K)
    covariance, residual = _covariance(L, K, factor)
    mean = solve_triangular(L.T, cho_solve((factor, True), L.T @ historical_mean, check_finite=False),
                            lower=False, check_finite=False)
    normal = np.eye(len(L)) + population_precision * historical_covariance
    residual = max(residual, _equation_residual(normal, mean, historical_mean),
                   _equation_residual(normal, covariance, historical_covariance))
    require(np.isfinite(mean).all() and np.isfinite(covariance).all() and residual <= 1e-8,
            "population-history prior equation residual exceeds 1e-8")
    return mean, covariance, dict(equation_relative_residual=residual)


def population_history_objective(
    H: np.ndarray, score: np.ndarray, response_energy: float,
    prior_mean: np.ndarray, prior_covariance: np.ndarray,
) -> tuple[float, dict]:
    """full normalized gaussian marginal objective, including native energy once."""
    require(score.shape == prior_mean.shape and H.shape == prior_covariance.shape
            == (len(score), len(score)) and math.isfinite(response_energy)
            and all(np.isfinite(value).all() for value in (H, score, prior_mean, prior_covariance)),
            "invalid population-history objective")
    L, K, factor = _factor(H, prior_covariance)
    covariance, residual = _covariance(L, K, factor)
    b = score - H @ prior_mean
    determinant = float(score.shape[1] * 2 * np.log(np.diag(factor)).sum())
    mean_energy = float(-2 * np.sum(prior_mean * score) + np.sum(prior_mean * (H @ prior_mean)))
    contraction = float(np.sum(covariance * (b @ b.T).T))
    centered_energy = float(response_energy - 2 * np.sum(prior_mean * score)
                            + np.sum(prior_mean * (H @ prior_mean)))
    value = float(determinant - contraction + centered_energy)
    require(math.isfinite(value) and residual <= 1e-8,
            "population-history objective equation residual exceeds 1e-8")
    return value, dict(native_response_energy=float(response_energy), determinant=determinant,
                       prior_mean_energy=mean_energy, contraction=contraction,
                       equation_relative_residual=residual)


def shape_objective_terms(
    H: np.ndarray, prior_covariance: np.ndarray, signal_contraction: np.ndarray,
    *, response_rank: int, response_metric: Literal["graph_identity", "native_inverse_share"],
    noise_contraction: np.ndarray | None = None,
) -> dict:
    """fixed-prior determinant and response-metric contractions, without scale selection.

    the caller supplies Q Q' for graph coefficients or (Q / p) Q' for native
    zero-sum responses. expected gaussian criteria additionally supply q H as
    noise_contraction. the response-energy constant is deliberately excluded.
    callers own their existing numerical acceptance policy for the returned
    terms and equation residual; this function makes no scale decision.
    """
    n = len(H)
    require(type(response_rank) is int and response_rank > 0
            and response_metric in ("graph_identity", "native_inverse_share")
            and H.shape == prior_covariance.shape == signal_contraction.shape == (n, n)
            and all(np.isfinite(value).all() and np.allclose(value, value.T, rtol=1e-10, atol=1e-10)
                    for value in (H, prior_covariance, signal_contraction))
            and (noise_contraction is None or (
                noise_contraction.shape == (n, n) and np.isfinite(noise_contraction).all()
                and np.allclose(noise_contraction, noise_contraction.T, rtol=1e-10, atol=1e-10))),
            "invalid fixed shape objective contract")
    L, K, factor = _factor(H, prior_covariance)
    covariance, residual = _covariance(L, K, factor)
    determinant = float(response_rank * 2 * np.log(np.diag(factor)).sum())
    signal = float(np.sum(covariance * signal_contraction.T))
    noise = 0.0 if noise_contraction is None else float(np.sum(covariance * noise_contraction.T))
    return dict(determinant=determinant, signal=signal, noise=noise,
                objective=float(determinant - signal - noise),
                equation_relative_residual=residual,
                response_rank=response_rank, response_metric=response_metric)


class _ScaleProblem:
    """cache response contractions once; each scale candidate solves row space."""

    def __init__(self, H, T, yy, M0, base_covariance, innovation_indices, p, *, basis=None, response_rank=None):
        self.H, self.T, self.M0 = H, T, M0
        self.base_covariance, self.innovation_indices = base_covariance, innovation_indices
        self.b = T - H @ M0
        self.rank = response_rank if response_rank is not None else (
            basis.B.shape[1] if basis is not None else (1 if p is None else len(p) - 1))
        self.band = response_rank is not None
        self.reduced = basis is not None or response_rank is not None
        if yy is None:
            require(self.reduced, "absent response energy requires an explicit coefficient response rank")
            self.zz = None
        elif self.reduced:
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
            if self.B is None:
                L, K, factor = _factor(self.H, self.covariance(variance))
                rhs = L.T @ self.b[:, 0]
                solution = cho_solve((factor, True), rhs, check_finite=False)
                residual = _equation_residual(K, solution, rhs)
                contraction = rhs @ solution
                logdet = self.rank * 2 * np.log(np.diag(factor)).sum()
            else:
                terms = shape_objective_terms(
                    self.H, self.covariance(variance), self.B, response_rank=self.rank,
                    response_metric="graph_identity" if self.reduced else "native_inverse_share",
                )
                logdet, contraction = terms["determinant"], terms["signal"]
                residual = terms["equation_relative_residual"]
            if not math.isfinite(residual) or residual > 1e-8:
                error = "scale objective equation residual exceeds 1e-8"
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
        if self.reduced and self.zz is not None:
            self.curve[-1]["band_objective" if self.band else "full_objective"] = (
                float(value + self.zz) if error is None else None)
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


class _PopulationScaleProblem:
    """two bounded coordinates; inherited means change at every evaluation."""

    def __init__(self, H, score, response_energy, historical_mean, base_covariance, innovation_indices):
        self.H, self.score, self.response_energy = H, score, response_energy
        self.historical_mean, self.base_covariance = historical_mean, base_covariance
        self.innovation_indices = innovation_indices
        self.curve = []

    def priors(self, variance, population_precision):
        historical_covariance = self.base_covariance.copy()
        historical_covariance[self.innovation_indices, self.innovation_indices] += variance
        mean, covariance, receipt = population_history_prior(
            self.historical_mean, historical_covariance, population_precision)
        return mean, covariance, historical_covariance, receipt

    def objective(self, coordinates, phase="refinement"):
        x, t = map(float, coordinates)
        variance, population_precision = 10. ** x, 10. ** t - 1
        error, residual, value = None, None, math.inf
        try:
            mean, covariance, _, prior = self.priors(variance, population_precision)
            value, terms = population_history_objective(
                self.H, self.score, self.response_energy, mean, covariance)
            residual = max(prior["equation_relative_residual"], terms["equation_relative_residual"])
        except (np.linalg.LinAlgError, InputContractError, ValueError) as failure:
            error = str(failure)
        self.curve.append(dict(exponent=x, population_exponent=t, variance=variance,
            **{"lambda": population_precision}, objective=value if error is None else None,
            phase=phase, error=error, equation_relative_residual=residual))
        return value if error is None else math.inf


def _population_scale_key(row):
    return row["objective"], row["lambda"], row["variance"]


def _initial_population_scale(history_scale):
    return dict(history_scale, prior_policy="population_history",
        population_precision_status="not_estimated_initial_year", initial_history_scale=history_scale,
        limits=dict(exponent=[-8., 0.], population_exponent=[0., 0.], coarse_spacing=.5),
        curve=[dict(row, population_exponent=0., **{"lambda": 0.}) for row in history_scale["curve"]],
        selected=dict(history_scale["selected"], population_exponent=0., **{"lambda": 0.}))


def _select_population_scale(problem: _PopulationScaleProblem, inherited: bool) -> dict:
    for x in np.arange(-8, .1, .5):
        for t in np.arange(0, 8.1, .5):
            problem.objective((x, t), "coarse")
    coarse = [row for row in problem.curve if row["objective"] is not None]
    require(bool(coarse), "no valid population-history coarse scale")
    best_coarse = min(coarse, key=_population_scale_key)
    boundary = _ScaleProblem(problem.H, problem.score, problem.response_energy, problem.historical_mean,
        problem.base_covariance, problem.innovation_indices, None, response_rank=problem.score.shape[1])
    _, boundary_scale = _select_scale(boundary, inherited)
    for row in boundary.curve:
        problem.curve.append(dict(exponent=row["exponent"], population_exponent=0., variance=row["variance"],
            **{"lambda": 0.}, objective=row.get("band_objective"), phase="boundary_" + row["phase"],
            error=row["error"], equation_relative_residual=row["equation_relative_residual"]))
    bounds = [[max(-8., best_coarse["exponent"] - .5), min(0., best_coarse["exponent"] + .5)],
              [max(0., best_coarse["population_exponent"] - .5),
               min(8., best_coarse["population_exponent"] + .5)]]
    fit = minimize(problem.objective, [best_coarse["exponent"], best_coarse["population_exponent"]],
        method="Powell", bounds=bounds, options=dict(xtol=1e-4, ftol=1e-10, maxfev=160))
    refinement = dict(bounds=bounds, success=bool(fit.success), message=str(fit.message),
        evaluations=int(fit.nfev), coordinates=[float(value) for value in fit.x], xtol=1e-4, ftol=1e-10,
        maxfev=160)
    valid = [row for row in problem.curve if row["objective"] is not None]
    selected = min(valid, key=_population_scale_key)
    reasons = []
    if selected["exponent"] in (-8., 0.):
        reasons.append("variance_endpoint_winner")
    if selected["population_exponent"] == 8.:
        reasons.append("population_upper_endpoint_winner")
    if not refinement["success"]:
        reasons.append("refinement_failed")
    if any(row["phase"] == "refinement" and row["objective"] is None for row in problem.curve):
        reasons.append("nonfinite_refinement")
    return dict(status="scale_unresolved" if reasons or inherited else "resolved", own_reasons=reasons,
        inherited_limitation=inherited, prior_policy="population_history", population_precision_status="estimated",
        limits=dict(exponent=[-8., 0.], population_exponent=[0., 8.], coarse_spacing=.5),
        curve=problem.curve, best_coarse=dict(best_coarse), boundary=boundary_scale, refinement=refinement,
        selected=dict(selected))


def _center(M, V, weights, diagnostics):
    n = len(weights)
    off_mean, def_mean = weights @ M[:n], weights @ M[n:]
    M[:n] -= off_mean
    M[n:] -= def_mean
    compensation = off_mean + def_mean
    centered = np.empty_like(V)
    for start in (0, n):
        for stop in (0, n):
            block = V[start : start + n, stop : stop + n]
            left, right = weights @ block, block @ weights
            centered[start : start + n, stop : stop + n] = (
                block - left[None, :] - right[:, None] + weights @ right
            )
    symmetry = float(np.max(np.abs(centered - centered.T)))
    tolerance = float(1e-10 * max(1, np.linalg.norm(centered, ord=np.inf)))
    require(symmetry <= tolerance and np.min(np.diag(centered)) >= -tolerance,
            "invalid centered covariance")
    diagnostics.update(
        centered_covariance_symmetry=symmetry,
        covariance_rounding_tolerance=tolerance,
        centered_mean_residual=float(max(np.max(np.abs(weights @ M[:n])), np.max(np.abs(weights @ M[n:])))),
    )
    return M, centered, compensation


def _coefficient_update(H, score, prior_mean, prior_covariance, u, *, factorization=None) -> _CoefficientUpdate:
    mean, covariance, diagnostics = _posterior(
        H, score, prior_mean, prior_covariance, factorization=factorization)
    uncentered_mean = mean.copy()
    mean, centered, shift = _center(mean, covariance, u, diagnostics)
    return _CoefficientUpdate(mean, centered, uncentered_mean, covariance, shift, diagnostics)


def fixed_shape_update(
    H: np.ndarray, prior_mean: np.ndarray, prior_covariance: np.ndarray,
    score: np.ndarray, u: np.ndarray,
    *, factorization: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None,
) -> ShapeUpdate:
    """one proper-prior update and exposure reference; no fitted scale decision."""
    n = len(u)
    require(n > 0 and H.shape == prior_covariance.shape == (2 * n, 2 * n)
            and prior_mean.ndim == 2 and prior_mean.shape == score.shape
            and len(prior_mean) == 2 * n and np.all(u >= 0)
            and math.isclose(float(u.sum()), 1, rel_tol=0, abs_tol=1e-12)
            and all(np.isfinite(value).all() for value in (H, prior_mean, prior_covariance, score, u))
            and np.allclose(H, H.T, rtol=1e-10, atol=1e-10)
            and np.allclose(prior_covariance, prior_covariance.T, rtol=1e-10, atol=1e-10),
            "invalid fixed shape update contract")
    update = _coefficient_update(H, score, prior_mean, prior_covariance, u, factorization=factorization)
    return ShapeUpdate(update.mean, update.covariance, update.covariance @ H,
                       update.uncentered_covariance, update.diagnostics)


@dataclass(frozen=True)
class PooledShapeGrid:
    """explicit fixed-design factorizations shared across response records."""

    H: np.ndarray
    variances: tuple[float, ...]
    factorizations: tuple[tuple[np.ndarray, np.ndarray, np.ndarray] | None, ...]
    covariances: np.ndarray
    logdets: np.ndarray
    diagnostics: dict


@dataclass(frozen=True)
class PooledShapeState:
    """one fixed-grid state; working covariance is not player uncertainty."""

    a: float
    Theta: np.ndarray
    V: np.ndarray
    A: np.ndarray
    beta: np.ndarray
    K: np.ndarray
    basis_columns: tuple[int, ...]
    diagnostics: dict


@dataclass(frozen=True)
class PooledShapeFit(PooledShapeState):
    """a marginal-likelihood selection and its actual grid objectives."""

    objectives: np.ndarray


def pooled_shape_grid(H: np.ndarray, variances: tuple[float, ...]) -> PooledShapeGrid:
    """factor each finite prior once, retaining the exact zero-map endpoint."""
    variances = tuple(float(value) for value in variances)
    require(H.ndim == 2 and H.shape[0] == H.shape[1] and len(H) > 0
            and np.isfinite(H).all() and np.allclose(H, H.T, rtol=1e-10, atol=1e-10)
            and bool(variances) and variances[0] == 0
            and variances == tuple(sorted(set(variances)))
            and all(math.isfinite(value) and value >= 0 for value in variances),
            "pooled grid requires finite symmetric information and ordered nonnegative variances")
    identity_matrix = np.eye(len(H))
    factors, covariances, determinants, residuals = [], [], [], []
    for variance in variances:
        if variance == 0:
            factors.append(None)
            covariances.append(np.zeros_like(H))
            determinants.append(0.)
            residuals.append(0.)
            continue
        factorization = _factor(H, variance*identity_matrix)
        L, normal, factor = factorization
        covariance, _ = _covariance(L, normal, factor)
        residual = float(np.linalg.norm((H+identity_matrix/variance)@covariance-identity_matrix, ord="fro")
                         / max(1., np.linalg.norm(identity_matrix, ord="fro")))
        require(residual <= 1e-8 and np.isfinite(covariance).all(),
                "pooled covariance equation residual exceeds 1e-8")
        factors.append(factorization)
        covariances.append(covariance)
        determinants.append(float(2*np.log(np.diag(factor)).sum()))
        residuals.append(residual)
    return PooledShapeGrid(H, variances, tuple(factors), np.stack(covariances),
        np.array(determinants), dict(equation_relative_residual=max(residuals),
                                    covariance_equation_relative_residuals=residuals))


def _pooled_grid_means(score: np.ndarray, grid: PooledShapeGrid) -> tuple[np.ndarray, list[float]]:
    require(score.ndim == 2 and len(score) == len(grid.H) and np.isfinite(score).all(),
            "pooled score differs from its fixed grid")
    beta_grid = grid.covariances @ score
    identity_matrix = np.eye(len(grid.H))
    score_norm = max(1., np.linalg.norm(score, ord="fro"))
    residuals = [0. if a == 0 else float(np.linalg.norm((grid.H+identity_matrix/a)@beta-score,
                   ord="fro") / score_norm)
                 for a, beta in zip(grid.variances, beta_grid, strict=True)]
    require(np.isfinite(beta_grid).all() and max(residuals) <= 1e-8,
            "pooled mean equation residual exceeds 1e-8")
    return beta_grid, residuals


def pooled_shape_at(pooled: PooledShapeLikelihood, grid: PooledShapeGrid, index: int) -> PooledShapeState:
    """materialize one declared variance with the pooled exposure/context gauge."""
    require(isinstance(index, (int, np.integer)) and 0 <= index < len(grid.variances)
            and np.array_equal(grid.H, pooled.H)
            and pooled.score.shape == (len(pooled.H), len(pooled.basis_columns)),
            "fixed pooled state changed its grid, index or score")
    beta_grid, residuals = _pooled_grid_means(pooled.score, grid)
    variance, K, beta = grid.variances[index], grid.covariances[index], beta_grid[index]
    if variance == 0:
        Theta, V = np.zeros_like(beta), np.zeros_like(K)
        diagnostics = dict(equation_relative_residual=0., centered_mean_residual=0.)
    else:
        update = fixed_shape_update(pooled.H, np.zeros_like(beta), variance*np.eye(len(K)),
                                    pooled.score, pooled.u, factorization=grid.factorizations[index])
        Theta, V, diagnostics = update.mean, update.covariance, dict(update.diagnostics)
    target = pooled.target
    ybar_h = target.ybar - target.ybar.sum(axis=1, keepdims=True)*pooled.p
    A = ybar_h - target.xbar @ pooled.target_selection @ Theta @ pooled.R.T
    require(np.isfinite(A).all(), "pooled final context is nonfinite")
    diagnostics.update(grid_equation_relative_residual=grid.diagnostics["equation_relative_residual"],
        mean_equation_relative_residuals=residuals, selected_index=int(index),
        endpoint=index in (0, len(grid.variances)-1),
        zero_map=variance == 0, covariance_meaning="working_conditional_not_validated_uncertainty")
    return PooledShapeState(variance, Theta, V, A, beta, K, pooled.basis_columns, diagnostics)


def fit_pooled_shape(
    pooled: PooledShapeLikelihood, variances: tuple[float, ...], *, grid: PooledShapeGrid | None = None,
) -> PooledShapeFit:
    """select marginal likelihood using only pooled training moments."""
    variances = tuple(float(value) for value in variances)
    grid = pooled_shape_grid(pooled.H, variances) if grid is None else grid
    require(grid.variances == variances and np.array_equal(grid.H, pooled.H)
            and pooled.score.shape == (len(pooled.H), len(pooled.basis_columns)),
            "pooled fit changed its fixed grid or score")
    beta_grid, _ = _pooled_grid_means(pooled.score, grid)
    objectives = len(pooled.basis_columns)*grid.logdets - np.sum(pooled.score*beta_grid, axis=(1, 2))
    require(np.isfinite(objectives).all(), "pooled grid has a nonfinite marginal objective")
    index = min(range(len(variances)), key=lambda i: (objectives[i], variances[i]))
    state = pooled_shape_at(pooled, grid, index)
    return PooledShapeFit(state.a, state.Theta, state.V, state.A, state.beta, state.K,
                          state.basis_columns, state.diagnostics, objectives)


def regional_penalty_scores(H5, T_h5, S, J, p, B, W, Q, grid, r) -> dict:
    """signed fixed-candidate regional risk difference under working gaussian noise.

    the reference uses native final-season regions, including omitted modes and
    changed history. minimization does not make the selected score unbiased.
    """
    n, d = Q.shape
    current, cells = H5.shape[0], len(p)
    require(H5.shape == J.shape == (current, current) and T_h5.shape == (current, cells)
            and S.shape == (current, n) and grid.H.shape == (n, n)
            and B.shape == (cells, d) and W.ndim == 2 and W.shape[0] == cells and W.shape[1] > 0
            and all(np.isfinite(value).all() for value in (H5, T_h5, S, J, p, B, W, Q))
            and np.all(p > 0) and abs(float(p.sum())-1) <= 1e-12
            and np.allclose(H5, H5.T, rtol=1e-10, atol=1e-10)
            and np.max(np.abs(T_h5.sum(axis=1)), initial=0.) <= 1e-8
            and np.allclose(p @ B, 0., atol=1e-10, rtol=0.)
            and np.allclose(B.T @ (p[:, None]*B), np.eye(d), atol=1e-10, rtol=1e-8)
            and np.isfinite(r) and r > 0,
            "regional selector numeric arrays differ from their fixed geometry")
    values, vectors, tau, masks = likelihood_spectrum(H5)
    ranks = [int(mask.sum()) for mask in masks]
    require(len(set(ranks)) == 1, "regional reference likelihood rank is cutoff-sensitive")
    positive = masks[1]
    Hplus = (vectors[:, positive]/values[positive]) @ vectors[:, positive].T
    reference_residual = float(np.linalg.norm(J @ Hplus @ H5-J, ord="fro")
                               / max(1., np.linalg.norm(J, ord="fro")))
    require(reference_residual <= 1e-8, "regional reference is outside the final identifiable target")
    beta_grid, residuals = _pooled_grid_means(Q, grid)
    D = B.T @ (p[:, None]*W)
    U = J @ Hplus @ T_h5 @ W
    F = J @ S
    A = F @ beta_grid @ D
    scale = r**2/64
    norm_term = scale*np.sum(A**2, axis=(1, 2))
    cross_term = -2*scale*np.sum(A*U, axis=(1, 2))
    correction_term = 2*scale*float(np.sum(D**2))*np.trace(
        F @ grid.covariances @ F.T, axis1=1, axis2=2)
    scores = norm_term+cross_term+correction_term
    require(all(np.isfinite(value).all() for value in (norm_term, cross_term, correction_term, scores)),
            "regional selector has a nonfinite score term")
    return dict(scores=scores, norm_term=norm_term, cross_term=cross_term,
        correction_term=correction_term, diagnostics=dict(rank=ranks[1], tau=tau,
            cutoff_factors=[.1, 1., 10.], rank_at_tau_factors=ranks,
            reference_equation_relative_residual=reference_residual,
            mean_equation_relative_residuals=residuals))


def _block_at_scale(
    H, T, ybar, xbar, M0, covariance, previous, weights, p, variance, scale, started, *, basis=None
) -> BlockState | GraphShapeState:
    update = _coefficient_update(H, T, M0, covariance, weights)
    M, V, shift, diagnostics = update.mean, update.covariance, update.centering_shift, update.diagnostics
    response_map = None if basis is None else basis.R
    native = update.uncentered_mean if response_map is None else update.uncentered_mean @ response_map.T
    A = ybar - xbar @ native
    A += 5 * (shift if response_map is None else shift @ response_map.T)
    diagnostics["resources"] = resources(started)
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


def _population_block_at_scale(problem, previous, u, yh, xbar, basis, scale) -> GraphShapeState:
    selected = scale["selected"]
    mean, covariance, historical_covariance, prior_receipt = problem.priors(selected["variance"], selected["lambda"])
    update = fixed_shape_update(problem.H, mean, covariance, problem.score, u)
    native = update.mean @ basis.R.T
    context = yh - xbar @ native
    residual = float(max(np.max(np.abs(native.sum(axis=1))), np.max(np.abs(context.sum(axis=1)))))
    require(residual <= 1e-8, "population-history shape/context is not zero sum")
    diagnostics = dict(update.diagnostics, zero_sum_mean_residual=residual,
        population_prior=prior_receipt,
        historical_prior_sha256=ordered_array_digest(dict(mean=problem.historical_mean, covariance=historical_covariance)),
        effective_prior_sha256=ordered_array_digest(dict(mean=mean, covariance=covariance)))
    return GraphShapeState(update.mean, update.covariance, context, mean, covariance,
        previous.a, selected["variance"], scale, diagnostics, problem.historical_mean, historical_covariance)


def _band_at_scale(H, T, M0, covariance, previous, weights, variance, scale, started) -> ShapeBandState:
    update = _coefficient_update(H, T, M0, covariance, weights)
    update.diagnostics["resources"] = resources(started)
    return ShapeBandState(update.mean, update.covariance, M0, covariance,
                          variance if previous is None else previous.a,
                          None if previous is None else variance, scale, update.diagnostics)


def _two_band_shape(H, Th, yh, xbar, basis, low, high, response_energy) -> TwoBandShapeState:
    native = low.Theta @ basis.R[:, :11].T + high.Theta @ basis.R[:, 11:].T
    A = yh - xbar @ native
    residual = float(max(np.max(np.abs(native.sum(axis=1))), np.max(np.abs(A.sum(axis=1)))))
    require(residual <= 1e-8, "two-band shape/context is not zero sum")
    terms = {}
    for name, block, columns in (("low", low, slice(0, 11)), ("high", high, slice(11, 40))):
        score = Th @ basis.B[:, columns]
        prior = float(-2 * np.sum(block.prior_mean * score)
                      + np.sum(block.prior_mean * (H @ block.prior_mean)))
        terms[name] = dict(prior_mean_terms=prior,
                           reduced_objective=block.scale["selected"]["objective"])
    full = float(response_energy + sum(row["prior_mean_terms"] + row["reduced_objective"]
                                       for row in terms.values()))
    return TwoBandShapeState(low, high, A, dict(native_response_energy=float(response_energy),
        band_objective_terms=terms, full_objective=full, zero_sum_mean_residual=residual))


def annual_input_identity(population: RevisionPopulation) -> str:
    """bind a fitted volume block to the exact residualized likelihood and references."""
    metadata = [population.benchmark, population.season, population.season_index,
                population.protocol_sha256, population.population_id, population.player_ids, population.strata]
    arrays = {name: np.asarray(getattr(population, name)) for name in (
        "H", "T", "yy", "shape_yy", "r", "xbar", "ybar", "stratum_weight", "player_exposure",
        "response_counts", "u", "p") if getattr(population, name) is not None}
    return hashlib.sha256(json.dumps(metadata, separators=(",", ":")).encode()
                          + bytes.fromhex(ordered_array_digest(arrays))).hexdigest()


def _align_annual_information(current, previous_players, information, score, u):
    players = tuple(sorted(set(previous_players) | set(current)))
    n = len(players)
    positions = {player: i for i, player in enumerate(players)}
    selected = np.array([positions[player] for player in current]
                        + [n + positions[player] for player in current])
    H, Q = np.zeros((2 * n, 2 * n)), np.zeros((2 * n, score.shape[1]))
    H[np.ix_(selected, selected)] = information
    Q[selected] = score
    weights = np.zeros(n)
    weights[[positions[player] for player in current]] = u
    return players, H, Q, weights, selected


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
    players, H, T, weights, selected = _align_annual_information(
        current, () if previous is None else previous.player_ids,
        population.H, population.T, population.u)
    xbar = np.zeros((h, 2 * len(players)))
    xbar[:, selected] = population.xbar
    return players, H, T, xbar, weights


def validate_shape_history_identity(left: np.ndarray, right: np.ndarray, name: str) -> dict:
    """both elementwise and whole-array closure are required before aggregation."""
    require(isinstance(left, np.ndarray) and isinstance(right, np.ndarray)
            and left.shape == right.shape and left.size > 0
            and np.isfinite(left).all() and np.isfinite(right).all(),
            "shape history identity axes or finite values differ: " + name)
    difference = left - right
    residual = float(np.linalg.norm(difference) / max(1., np.linalg.norm(left), np.linalg.norm(right)))
    require(np.allclose(left, right, rtol=1e-8, atol=1e-10) and residual <= 1e-8,
            "shape history identity failed: " + name)
    return dict(relative_residual=residual, maximum_absolute_residual=float(np.max(np.abs(difference))))


def shape_history_carry(H: np.ndarray, V: np.ndarray, u: np.ndarray, m0: np.ndarray) -> dict:
    """conditional current-axis carry; the covariance is the saved centered posterior."""
    require(isinstance(u, np.ndarray) and u.ndim == 1 and len(u) > 0
            and np.isfinite(u).all() and np.all(u >= 0) and abs(float(u.sum()) - 1) <= 1e-12,
            "invalid shape history exposure reference")
    n = len(u)
    require(isinstance(m0, np.ndarray) and m0.ndim == 2 and m0.shape[0] == 2*n and m0.shape[1] > 0
            and np.isfinite(m0).all()
            and all(isinstance(value, np.ndarray) and value.shape == (2*n, 2*n)
                    and np.isfinite(value).all() for value in (H, V)),
            "shape history current axes or finite values differ")
    require(np.allclose(H, H.T, rtol=1e-8, atol=1e-10)
            and np.allclose(V, V.T, rtol=1e-8, atol=1e-10)
            and np.min(np.diag(V)) >= -1e-10 * max(1., np.linalg.norm(V)),
            "shape history information or centered covariance differs")
    gauges = np.kron(np.eye(2), np.ones((n, 1)))
    h_gauge = float(np.linalg.norm(H @ gauges) / max(1., np.linalg.norm(H)))
    v_reference = np.vstack((u @ V[:n], u @ V[n:]))
    v_residual = float(np.linalg.norm(v_reference) / max(1., np.linalg.norm(V)))
    require(max(h_gauge, v_residual) <= 1e-8,
            "shape history information gauge or covariance exposure centering differs")
    reference = np.vstack((m0[:n] - u @ m0[:n], m0[n:] - u @ m0[n:]))
    update = -(V @ (H @ m0))
    return dict(reference=reference, update=update,
                closure=dict(information_gauge_relative_residual=h_gauge,
                             covariance_centering_relative_residual=v_residual))


def decompose_shape_history(H: np.ndarray, Q: np.ndarray, Qbar: np.ndarray, m0: np.ndarray,
                            V: np.ndarray, u: np.ndarray, Theta: np.ndarray) -> dict:
    """account for one saved final mean without refitting or inverting its covariance.

    selections remain response-dependent; realized noise is neither independent
    of the other terms nor a sampling-variance estimate.
    """
    carry = shape_history_carry(H, V, u, m0)
    require(all(isinstance(value, np.ndarray) and value.shape == m0.shape
                and np.isfinite(value).all() for value in (Q, Qbar, Theta)),
            "shape history score or saved mean axes differ")
    n = len(u)
    closure = dict(carry["closure"])
    for name, score in (("score", Q), ("signal_score", Qbar)):
        residual = float(np.linalg.norm(np.vstack((score[:n].sum(axis=0), score[n:].sum(axis=0))))
                         / max(1., np.linalg.norm(score)))
        require(residual <= 1e-8, "shape history " + name + " does not annihilate role gauges")
        closure[name + "_gauge_relative_residual"] = residual
    signal = V @ Qbar
    noise = V @ (Q - Qbar)
    closure["saved_mean"] = validate_shape_history_identity(
        signal + noise + carry["reference"] + carry["update"], Theta, "saved_mean")
    return dict(signal=signal, noise=noise, carry_reference=carry["reference"],
                carry_update=carry["update"], closure=closure)


def _coefficient_inputs(likelihood, previous, score, width):
    """validate annual player-score axes, then align the shared historical prior."""
    current, n = likelihood.player_ids, len(likelihood.player_ids)
    require(isinstance(likelihood.season, str) and len(likelihood.season) == 8
            and likelihood.season.isdigit()
            and int(likelihood.season[4:]) == int(likelihood.season[:4]) + 1
            and n > 0 and current == tuple(sorted(set(current)))
            and all(type(player) is int for player in current)
            and math.isfinite(likelihood.r) and likelihood.r > 0
            and isinstance(likelihood.source_identity, dict) and bool(likelihood.source_identity),
            "coefficient likelihood requires actual season, sorted identities and source identity")
    for value, shape in ((likelihood.H, (2*n, 2*n)), (score, (2*n, width)), (likelihood.u, (n,))):
        require(isinstance(value, np.ndarray) and value.dtype == np.dtype("float64")
                and value.shape == shape and np.isfinite(value).all(),
                "coefficient likelihood axes or finite float64 arrays differ")
    require(np.all(likelihood.u > 0) and abs(float(likelihood.u.sum()) - 1) <= 1e-12
            and np.allclose(likelihood.H, likelihood.H.T, rtol=1e-10, atol=1e-10),
            "coefficient exposure or symmetric information differs")
    for start in (0, n):
        require(np.max(np.abs(likelihood.H[:, start:start+n].sum(axis=1)))
                    <= 1e-8 * (1 + np.linalg.norm(likelihood.H, ord=np.inf))
                and np.max(np.abs(score[start:start+n].sum(axis=0)))
                    <= 1e-8 * (1 + np.linalg.norm(score, ord=np.inf)),
                "coefficient likelihood does not annihilate role-constant gauges")
    if previous is not None:
        require(int(likelihood.season[:4]) == int(previous.season[:4]) + 1
                and "numerical_original_scale" not in previous.scale,
                "coefficient predecessor is nonconsecutive or a numerical alternative")
    players, H, aligned_score, weights, _ = _align_annual_information(
        current, () if previous is None else previous.player_ids, likelihood.H, score, likelihood.u)
    mean, base, indices = _prior(players, previous, previous, width)
    return players, H, aligned_score, weights, mean, base, indices


def _shape_coefficient_inputs(likelihood: ShapeCoefficientLikelihood, previous: ShapeCoefficientState | None):
    basis = likelihood.basis
    for value, shape in ((basis.B, (656, 40)), (basis.p, (656,))):
        require(isinstance(value, np.ndarray) and value.dtype == np.dtype("float64")
                and value.shape == shape and np.isfinite(value).all(),
                "shape coefficient likelihood axes or finite float64 arrays differ")
    require(np.all(basis.p > 0) and abs(float(basis.p.sum()) - 1) <= 1e-12
            and np.max(np.abs(basis.p @ basis.B)) <= 1e-10
            and np.max(np.abs(basis.B.T @ (basis.p[:, None] * basis.B) - np.eye(40))) <= 1e-10,
            "shape coefficient basis differs")
    if previous is not None:
        require(previous.basis_sha256 == basis.sha256, "shape coefficient predecessor changed basis")
    return _coefficient_inputs(likelihood, previous, likelihood.Q, 40)


def fit_shape_coefficients(
    likelihood: ShapeCoefficientLikelihood, previous: ShapeCoefficientState | None = None,
) -> ShapeCoefficientState:
    """select the existing annual graph prior from a score; absent energy stays absent."""
    started = time.monotonic()
    players, H, Q, u, mean, base, indices = _shape_coefficient_inputs(likelihood, previous)
    problem = _ScaleProblem(H, Q, None, mean, base, indices, likelihood.basis.p, basis=likelihood.basis)
    variance, scale = _select_scale(problem, previous is not None and previous.scale["status"] == "scale_unresolved")
    require(all(row["objective"] is not None for row in scale["curve"]),
            "shape coefficient scale solve failed; dependent chain stopped")
    update = _coefficient_update(H, Q, mean, problem.covariance(variance), u)
    update.diagnostics["zero_sum_mean_residual"] = float(
        np.max(np.abs((update.mean @ likelihood.basis.R.T).sum(axis=1))))
    require(update.diagnostics["zero_sum_mean_residual"] <= 1e-8, "shape coefficient mean is not zero sum")
    update.diagnostics["resources"] = resources(started)
    current = likelihood.player_ids
    entrants = current if previous is None else tuple(player for player in current if player not in previous.player_ids)
    return ShapeCoefficientState(likelihood.season, players, current, entrants,
        tuple(player for player in players if player not in current), update.mean, update.covariance, u,
        likelihood.r, variance if previous is None else previous.a, None if previous is None else variance,
        likelihood.basis.sha256, likelihood.source_identity, scale, update.diagnostics,
        update.uncentered_mean, update.centering_shift)


def _validate_shape_coefficient_state_at_variance(
    likelihood: ShapeCoefficientLikelihood, previous: ShapeCoefficientState | None, state: ShapeCoefficientState, variance: float,
) -> None:
    """check saved axes and posterior equations at one declared variance."""
    players, H, Q, u, mean, base, indices = _shape_coefficient_inputs(likelihood, previous)
    n = len(players)
    current = likelihood.player_ids
    entrants = current if previous is None else tuple(player for player in current if player not in previous.player_ids)
    require(state.season == likelihood.season and state.player_ids == players
            and state.current_player_ids == current and state.entrant_ids == entrants
            and state.carried_only_ids == tuple(player for player in players if player not in current)
            and state.r == likelihood.r and state.basis_sha256 == likelihood.basis.sha256
            and state.source_identity == likelihood.source_identity and np.array_equal(state.u, u),
            "shape coefficient state identity or annual alignment differs")
    for value, shape in ((state.Theta, (2*n, 40)), (state.V, (2*n, 2*n)),
                         (state.uncentered_Theta, (2*n, 40)), (state.centering_shift, (40,))):
        require(isinstance(value, np.ndarray) and value.dtype == np.dtype("float64")
                and value.shape == shape and np.isfinite(value).all(),
                "shape coefficient state axes or finite float64 arrays differ")
    require(state.a == (variance if previous is None else previous.a)
            and state.q == (None if previous is None else variance), "shape coefficient prior scale lineage differs")
    base[indices, indices] += variance
    _validate_coefficient_posterior(H, Q, u, mean, base, state.uncentered_Theta,
                                    state.Theta, state.V, state.centering_shift)

    return H, Q, u, mean, base


def validate_shape_coefficient_state(
    likelihood: ShapeCoefficientLikelihood, previous: ShapeCoefficientState | None, state: ShapeCoefficientState,
) -> None:
    """check saved axes, search and posterior equations without another selection or solve."""
    validate_shape_scale_receipt(state.scale, None if previous is None else previous.scale)
    require(all(set(row) == {"exponent", "variance", "objective", "phase", "error", "equation_relative_residual"}
                and row["objective"] is not None and row["equation_relative_residual"] is not None
                and 0 <= row["equation_relative_residual"] <= 1e-8 for row in state.scale["curve"]),
            "shape coefficient search contains response energy or a failed numerical solve")
    _validate_shape_coefficient_state_at_variance(likelihood, previous, state, state.scale["selected"]["variance"])


def _validate_coefficient_posterior(H, Q, u, mean, base, raw, centered_mean, covariance, shift):
    """check the original mean equation and gauge-projected covariance equation."""
    n = len(u)
    normal = np.eye(2*n) + base @ H
    mean_residual = _equation_residual(normal, raw - mean, base @ (Q - H @ mean))
    off, defense = u @ raw[:n], u @ raw[n:]
    centered = np.vstack((raw[:n] - off, raw[n:] - defense))
    require(np.allclose(centered_mean, centered, rtol=1e-10, atol=1e-10)
            and np.allclose(shift, off + defense, rtol=1e-10, atol=1e-10),
            "coefficient uncentered mean or compensation differs")
    # h annihilates the role gauges, so (i+p v0 h) v = p v0 p' checks
    # the retained centered covariance directly, without reconstructing a fit.
    normal -= np.eye(2*n)
    for start in (0, n):
        normal[start:start+n] -= u @ normal[start:start+n]
    normal += np.eye(2*n)
    _, centered_prior, _ = _center(np.zeros((2*n, 1)), base, u, {})
    covariance_residual = _equation_residual(normal, covariance, centered_prior)
    tolerance = 1e-10 * max(1, np.linalg.norm(covariance, ord=np.inf))
    require(max(mean_residual, covariance_residual) <= 1e-8
            and np.max(np.abs(covariance - covariance.T)) <= tolerance
            and np.min(np.diag(covariance)) >= -tolerance
            and max(np.max(np.abs(u @ centered_mean[:n])), np.max(np.abs(u @ centered_mean[n:]))) <= 1e-8
            and max(np.max(np.abs(u @ covariance[:n])), np.max(np.abs(u @ covariance[n:]))) <= tolerance,
            "coefficient saved posterior or centering equation differs")


def _conditional_scale_probe(problem: _ScaleProblem, saved: dict) -> dict:
    winner = saved["selected"]
    coarse = [row for row in saved["curve"] if row["phase"] == "coarse"
              and row["objective"] is not None and row["exponent"] != winner["exponent"]]
    nearest = sorted(coarse, key=lambda row: (abs(row["exponent"] - winner["exponent"]), row["exponent"]))[:2]
    for row in [winner] + nearest:
        problem.objective(row["exponent"], "independent_recheck")
    refinement = None
    if saved["refinement"] is not None:
        bounds = saved["refinement"]["bounds"]
        fit = minimize_scalar(problem.objective, bounds=bounds, method="bounded",
                              options={"xatol": 1e-6, "maxiter": 80})
        refinement = dict(bounds=bounds, success=bool(fit.success), message=str(fit.message),
            evaluations=int(fit.nfev), exponent=float(fit.x) if math.isfinite(fit.x) else None,
            xatol=1e-6, maxiter=80)
    valid = [row for row in saved["curve"] + problem.curve if row["objective"] is not None]
    selected = min(valid, key=lambda row: (row["objective"], row["variance"]))
    rechecks_match = all(new["objective"] is not None and math.isclose(
        new["objective"], old["objective"], rel_tol=1e-8, abs_tol=1e-10)
        for old, new in zip([winner] + nearest, problem.curve))
    return dict(saved_winner=winner, rechecked_candidates=problem.curve, tightened_refinement=refinement,
        selected=selected,
        saved_scale_status={key: saved[key] for key in ("status", "own_reasons", "inherited_limitation")},
        numerical_complete=rechecks_match and all(row["objective"] is not None for row in problem.curve)
            and (refinement is None or refinement["success"]))


def bounded_shape_coefficient_probe(
    likelihood: ShapeCoefficientLikelihood, previous: ShapeCoefficientState | None, state: ShapeCoefficientState,
) -> tuple[dict, ShapeCoefficientState]:
    """tighten the saved bracket once, conditional on the unchanged incoming history."""
    from .attribution_simulation import shape_regions

    validate_shape_coefficient_state(likelihood, previous, state)
    players, H, Q, u, mean, base, indices = _shape_coefficient_inputs(likelihood, previous)
    problem = _ScaleProblem(H, Q, None, mean, base, indices, likelihood.basis.p, basis=likelihood.basis)
    receipt = _conditional_scale_probe(problem, state.scale)
    variance = receipt["selected"]["variance"]
    update = _coefficient_update(H, Q, mean, problem.covariance(variance), u)
    alternative = replace(state, Theta=update.mean, V=update.covariance,
        q=None if previous is None else variance, a=variance if previous is None else previous.a,
        scale=dict(state.scale, selected=receipt["selected"], numerical_original_scale=state.scale),
        uncentered_Theta=update.uncentered_mean, centering_shift=update.centering_shift,
        diagnostics=update.diagnostics)
    n = len(players)
    current = [players.index(player) for player in state.current_player_ids]
    rows = current + [n + index for index in current]
    delta = (alternative.Theta[rows] - state.Theta[rows]) @ likelihood.basis.R.T
    regions, _ = shape_regions()
    movement = dict(native_cells=float(np.max(np.abs(delta))), regions=float(np.max(np.abs(delta @ regions))))
    receipt.update(status="verified" if receipt["numerical_complete"] and max(movement.values()) <= 1e-4
        else "numerically_unresolved", scope=POOLING_PROBE_SCOPE,
        maximum_league_relative_current_player_movement=movement, tolerance=1e-4,
        diagnostics=update.diagnostics)
    return receipt, alternative


def validate_shape_coefficient_probe(
    likelihood: ShapeCoefficientLikelihood, previous: ShapeCoefficientState | None,
    primary: ShapeCoefficientState, receipt: dict, alternative: ShapeCoefficientState,
) -> None:
    """verify a frozen conditional alternative; never select or propagate its history."""
    from .attribution_simulation import shape_regions

    validate_shape_coefficient_state(likelihood, previous, primary)
    saved = primary.scale
    require(set(receipt) == {"saved_winner", "rechecked_candidates", "tightened_refinement", "selected",
            "saved_scale_status", "numerical_complete", "status", "scope",
            "maximum_league_relative_current_player_movement", "tolerance", "diagnostics"}
        and receipt["saved_winner"] == saved["selected"]
        and receipt["saved_scale_status"] == {key: saved[key] for key in
            ("status", "own_reasons", "inherited_limitation")}
        and receipt["scope"] == POOLING_PROBE_SCOPE and receipt["tolerance"] == 1e-4
        and alternative.scale == dict(saved, selected=receipt["selected"], numerical_original_scale=saved),
        "frozen shape probe primary scale, scope or saved alternative binding differs")
    winner = saved["selected"]
    coarse = [row for row in saved["curve"] if row["phase"] == "coarse"
              and row["objective"] is not None and row["exponent"] != winner["exponent"]]
    nearest = sorted(coarse, key=lambda row: (abs(row["exponent"]-winner["exponent"]), row["exponent"]))[:2]
    expected = [winner] + nearest
    curve = receipt["rechecked_candidates"]
    require(len(curve) >= len(expected)
        and all(set(row) == {"exponent", "variance", "objective", "phase", "error", "equation_relative_residual"}
            and type(row["exponent"]) in (int, float) and -8 <= row["exponent"] <= 0
            and row["variance"] == 10.**row["exponent"] and row["error"] is None
            and type(row["objective"]) in (int, float) and math.isfinite(row["objective"])
            and row["equation_relative_residual"] is not None
            and 0 <= row["equation_relative_residual"] <= 1e-8 for row in curve)
        and all(new["phase"] == "independent_recheck" and new["exponent"] == old["exponent"]
            and math.isclose(new["objective"], old["objective"], rel_tol=1e-8, abs_tol=1e-10)
            for old, new in zip(expected, curve)), "frozen shape probe rechecks or finite solve receipts differ")
    refinement = receipt["tightened_refinement"]
    if saved["refinement"] is None:
        require(refinement is None and len(curve) == len(expected), "frozen shape probe added a refinement")
    else:
        require(refinement is not None and refinement["bounds"] == saved["refinement"]["bounds"]
            and refinement["xatol"] == 1e-6 and refinement["maxiter"] == 80
            and refinement["evaluations"] == len(curve)-len(expected) <= 80
            and all(row["phase"] == "refinement"
                and refinement["bounds"][0] <= row["exponent"] <= refinement["bounds"][1]
                for row in curve[len(expected):]), "frozen shape probe bracket or evaluation budget differs")
    selected = min(saved["curve"] + curve, key=lambda row: (row["objective"], row["variance"]))
    require(receipt["selected"] == selected
        and receipt["numerical_complete"] is (refinement is None or refinement["success"]),
        "frozen shape probe selected state or numerical completion differs")
    H, Q, u, mean, base = _validate_shape_coefficient_state_at_variance(
        likelihood, previous, alternative, selected["variance"])
    _, _, factor = _factor(H, base)
    logdet = float(2*np.log(np.diag(factor)).sum())
    objective = float(40*logdet - np.sum((Q-H @ mean)*(alternative.uncentered_Theta-mean)))
    require(math.isfinite(objective)
        and math.isclose(objective, selected["objective"], rel_tol=1e-8, abs_tol=1e-10)
        and alternative.diagnostics == receipt["diagnostics"],
        "frozen shape probe objective, response or posterior diagnostics differ")
    n = len(primary.player_ids)
    current = [primary.player_ids.index(player) for player in primary.current_player_ids]
    rows = current + [n+index for index in current]
    delta = (alternative.Theta[rows]-primary.Theta[rows]) @ likelihood.basis.R.T
    regions, _ = shape_regions()
    movement = dict(native_cells=float(np.max(np.abs(delta))), regions=float(np.max(np.abs(delta @ regions))))
    require(set(receipt["maximum_league_relative_current_player_movement"]) == set(movement)
        and all(math.isclose(receipt["maximum_league_relative_current_player_movement"][key], value,
            rel_tol=1e-10, abs_tol=1e-12) for key, value in movement.items())
        and receipt["status"] == ("verified" if receipt["numerical_complete"] and max(movement.values()) <= 1e-4
            else "numerically_unresolved"), "frozen shape probe physical movement or status differs")


def _scalar_coefficient_inputs(likelihood: ScalarCoefficientLikelihood, previous: ScalarCoefficientState | None):
    require(isinstance(likelihood, ScalarCoefficientLikelihood)
            and isinstance(likelihood.energy, (int, float)) and math.isfinite(likelihood.energy)
            and likelihood.energy >= 0, "scalar coefficient likelihood requires retained finite response energy")
    return _coefficient_inputs(likelihood, previous, likelihood.score, 1)


def _scalar_score_inputs(likelihood: ScalarScoreLikelihood, previous: ScalarCoefficientState | None):
    require(isinstance(likelihood, ScalarScoreLikelihood)
            and (previous is None or isinstance(previous, ScalarCoefficientState)),
            "scalar score requires its typed likelihood and scalar predecessor")
    return _coefficient_inputs(likelihood, previous, likelihood.score, 1)


def _fit_scalar_state(likelihood, previous, inputs, problem, started):
    players, H, score, u, mean, _, _ = inputs
    variance, scale = _select_scale(problem, previous is not None and previous.scale["status"] == "scale_unresolved")
    require(all(row["objective"] is not None for row in scale["curve"]),
            "scalar coefficient scale solve failed; dependent chain stopped")
    update = _coefficient_update(H, score, mean, problem.covariance(variance), u)
    update.diagnostics["resources"] = resources(started)
    current = likelihood.player_ids
    entrants = current if previous is None else tuple(player for player in current if player not in previous.player_ids)
    return ScalarCoefficientState(likelihood.season, players, current, entrants,
        tuple(player for player in players if player not in current), update.mean, update.covariance, u,
        likelihood.r, variance if previous is None else previous.a, None if previous is None else variance,
        likelihood.source_identity, scale, update.diagnostics, update.uncentered_mean, update.centering_shift)


def fit_scalar_coefficients(
    likelihood: ScalarCoefficientLikelihood, previous: ScalarCoefficientState | None = None,
) -> ScalarCoefficientState:
    """select the existing scalar annual prior on matched recorded spatial counts."""
    started = time.monotonic()
    inputs = _scalar_coefficient_inputs(likelihood, previous)
    _, H, score, _, mean, base, indices = inputs
    problem = _ScaleProblem(H, score, likelihood.energy, mean, base, indices, None)
    return _fit_scalar_state(likelihood, previous, inputs, problem, started)


def fit_scalar_score_coefficients(
    likelihood: ScalarScoreLikelihood, previous: ScalarCoefficientState | None = None,
) -> ScalarCoefficientState:
    """select the scalar annual prior from its energy-free scale contrast."""
    started = time.monotonic()
    inputs = _scalar_score_inputs(likelihood, previous)
    _, H, score, _, mean, base, indices = inputs
    problem = _ScaleProblem(H, score, None, mean, base, indices, None, response_rank=1)
    return _fit_scalar_state(likelihood, previous, inputs, problem, started)


def _validate_scalar_state_at_variance(likelihood, previous, state, variance, inputs):
    players, H, score, u, mean, base, indices = inputs
    n, current = len(players), likelihood.player_ids
    entrants = current if previous is None else tuple(player for player in current if player not in previous.player_ids)
    require(state.season == likelihood.season and state.player_ids == players
            and state.current_player_ids == current and state.entrant_ids == entrants
            and state.carried_only_ids == tuple(player for player in players if player not in current)
            and state.r == likelihood.r and state.source_identity == likelihood.source_identity
            and np.array_equal(state.u, u), "scalar coefficient state identity or annual alignment differs")
    for value, shape in ((state.beta, (2*n, 1)), (state.V, (2*n, 2*n)),
                         (state.uncentered_beta, (2*n, 1)), (state.centering_shift, (1,))):
        require(isinstance(value, np.ndarray) and value.dtype == np.dtype("float64")
                and value.shape == shape and np.isfinite(value).all(),
                "scalar coefficient state axes or finite float64 arrays differ")
    require(state.a == (variance if previous is None else previous.a)
            and state.q == (None if previous is None else variance), "scalar coefficient prior scale lineage differs")
    base = base.copy()
    base[indices, indices] += variance
    _validate_coefficient_posterior(H, score, u, mean, base, state.uncentered_beta,
                                    state.beta, state.V, state.centering_shift)
    return H, score, mean, base


def _validate_scalar_search(state, previous):
    validate_shape_scale_receipt(state.scale, None if previous is None else previous.scale)
    require(all(set(row) == {"exponent", "variance", "objective", "phase", "error", "equation_relative_residual"}
                and row["objective"] is not None and row["equation_relative_residual"] is not None
                and 0 <= row["equation_relative_residual"] <= 1e-8 for row in state.scale["curve"]),
            "scalar coefficient search contains a failed numerical solve or response energy")


def validate_scalar_coefficient_state(
    likelihood: ScalarCoefficientLikelihood, previous: ScalarCoefficientState | None, state: ScalarCoefficientState,
) -> None:
    """bind the saved scalar search, annual lineage, posterior and role references."""
    inputs = _scalar_coefficient_inputs(likelihood, previous)
    _validate_scalar_search(state, previous)
    H, score, mean, base = _validate_scalar_state_at_variance(
        likelihood, previous, state, state.scale["selected"]["variance"], inputs)
    # the solved mean gives the signal contraction without another posterior solve.
    _, _, factor = _factor(H, base)
    logdet = float(2*np.log(np.diag(factor)).sum())
    mean_score = float(2 * np.sum(mean * score))
    mean_energy = float(np.sum(mean * (H @ mean)))
    contraction = float(np.sum((score - H @ mean) * (state.uncentered_beta - mean)))
    contrast = float(logdet - mean_score + mean_energy - contraction)
    saved_contrast = state.scale["selected"]["objective"] - likelihood.energy
    # the saved full objective can lose ulps when response energy is much larger
    # than its scale-dependent contrast; it must not set a relative error budget.
    rounding = 8*np.finfo(float).eps*(abs(likelihood.energy)+abs(mean_score)+abs(mean_energy)+abs(contraction))
    require(math.isfinite(contrast)
            and math.isclose(contrast, saved_contrast, rel_tol=1e-8, abs_tol=max(1e-10, rounding)),
            "scalar coefficient selected objective differs from retained response energy")


def validate_scalar_score_coefficient_state(
    likelihood: ScalarScoreLikelihood, previous: ScalarCoefficientState | None, state: ScalarCoefficientState,
) -> None:
    """bind the energy-free search and the same annual posterior equations."""
    inputs = _scalar_score_inputs(likelihood, previous)
    _validate_scalar_search(state, previous)
    H, score, mean, base = _validate_scalar_state_at_variance(
        likelihood, previous, state, state.scale["selected"]["variance"], inputs)
    _, _, factor = _factor(H, base)
    objective = float(2*np.log(np.diag(factor)).sum()
                      - np.sum((score-H @ mean)*(state.uncentered_beta-mean)))
    require(math.isfinite(objective)
            and math.isclose(objective, state.scale["selected"]["objective"], rel_tol=1e-8, abs_tol=1e-10),
            "scalar score selected objective differs from gaussian_score_scale_contrast_v1")


def scalar_score_control_equivalence(
    likelihood: ScalarCoefficientLikelihood, previous: ScalarCoefficientState | None, state: ScalarCoefficientState,
) -> dict:
    """check an unchanged energy-bearing control at its saved scales, never reselect."""
    validate_scalar_coefficient_state(likelihood, previous, state)
    score_likelihood = ScalarScoreLikelihood(likelihood.season, likelihood.player_ids, likelihood.H,
        likelihood.score, likelihood.u, likelihood.r, likelihood.source_identity)
    inputs = _scalar_score_inputs(score_likelihood, previous)
    _, H, score, _, mean, base, indices = inputs
    _validate_scalar_state_at_variance(score_likelihood, previous, state,
        state.scale["selected"]["variance"], inputs)
    problem = _ScaleProblem(H, score, None, mean, base, indices, None, response_rank=1)
    mean_score = float(2*np.sum(mean*score))
    mean_energy = float(np.sum(mean*(H @ mean)))
    omitted = float(likelihood.energy-mean_score+mean_energy)
    winner = state.scale["selected"]
    coarse = [row for row in state.scale["curve"] if row["phase"] == "coarse"
              and row["exponent"] != winner["exponent"]]
    points = [winner] + sorted(coarse,
        key=lambda row: (abs(row["exponent"]-winner["exponent"]), row["exponent"]))[:2]
    comparisons = []
    for row in points:
        objective = problem.objective(row["exponent"], "fixed_control_equivalence")
        rounding = 8*np.finfo(float).eps*(abs(likelihood.energy)+abs(mean_score)+abs(mean_energy)
            +abs(objective)+abs(omitted))
        residual = abs((objective+omitted)-row["objective"])
        require(math.isfinite(objective) and math.isclose(objective, row["objective"]-omitted,
                rel_tol=1e-8, abs_tol=max(1e-10, rounding))
                and abs(row["objective"]-objective-omitted) <= max(1e-10, rounding),
                "saved scalar control differs from its score-only constant offset")
        comparisons.append(dict(exponent=row["exponent"], variance=row["variance"],
            saved_full_objective=row["objective"], score_objective=objective,
            saved_full_minus_score=float(row["objective"]-objective),
            omitted_constant_absolute_residual=float(abs(row["objective"]-objective-omitted)),
            full_reconstruction_absolute_residual=residual, rounding_allowance=rounding,
            equation_relative_residual=problem.curve[-1]["equation_relative_residual"]))
    return dict(objective_identity="gaussian_score_scale_contrast_v1",
        omitted_within_search_constant=omitted, fixed_saved_scales=comparisons,
        posterior_equivalence="verified by identical aligned score posterior and role-reference equations",
        original_state_and_scale_curve="unchanged", selection="not rerun")


def bounded_scalar_coefficient_probe(
    likelihood: ScalarCoefficientLikelihood, previous: ScalarCoefficientState | None, state: ScalarCoefficientState,
) -> tuple[dict, ScalarCoefficientState]:
    """tighten one saved scalar bracket with the incoming primary history fixed."""
    validate_scalar_coefficient_state(likelihood, previous, state)
    inputs = _scalar_coefficient_inputs(likelihood, previous)
    _, H, score, _, mean, base, indices = inputs
    problem = _ScaleProblem(H, score, likelihood.energy, mean, base, indices, None)
    return _scalar_probe(previous, state, inputs, problem)


def _scalar_probe(previous, state, inputs, problem):
    players, H, score, u, mean, _, _ = inputs
    receipt = _conditional_scale_probe(problem, state.scale)
    variance = receipt["selected"]["variance"]
    update = _coefficient_update(H, score, mean, problem.covariance(variance), u)
    alternative = replace(state, beta=update.mean, V=update.covariance,
        q=None if previous is None else variance, a=variance if previous is None else previous.a,
        scale=dict(state.scale, selected=receipt["selected"], numerical_original_scale=state.scale),
        uncentered_beta=update.uncentered_mean, centering_shift=update.centering_shift,
        diagnostics=update.diagnostics)
    n = len(players)
    current = [players.index(player) for player in state.current_player_ids]
    rows = current + [n + index for index in current]
    movement = dict(volume_relative=float(np.max(np.abs(alternative.beta[rows] - state.beta[rows]))))
    receipt.update(status="verified" if receipt["numerical_complete"] and movement["volume_relative"] <= 1e-4
        else "numerically_unresolved", scope=POOLING_PROBE_SCOPE,
        maximum_league_relative_current_player_movement=movement, tolerance=1e-4,
        diagnostics=update.diagnostics)
    return receipt, alternative


def bounded_scalar_score_coefficient_probe(
    likelihood: ScalarScoreLikelihood, previous: ScalarCoefficientState | None, state: ScalarCoefficientState,
) -> tuple[dict, ScalarCoefficientState]:
    """tighten the saved score-only scalar bracket with unchanged incoming history."""
    validate_scalar_score_coefficient_state(likelihood, previous, state)
    inputs = _scalar_score_inputs(likelihood, previous)
    _, H, score, _, mean, base, indices = inputs
    problem = _ScaleProblem(H, score, None, mean, base, indices, None, response_rank=1)
    return _scalar_probe(previous, state, inputs, problem)


def validate_scalar_score_coefficient_probe(
    likelihood: ScalarScoreLikelihood, previous: ScalarCoefficientState | None,
    primary: ScalarCoefficientState, receipt: dict, alternative: ScalarCoefficientState,
) -> None:
    """verify a saved score-only alternative without refitting or propagating it."""
    validate_scalar_score_coefficient_state(likelihood, previous, primary)
    _validate_scalar_probe(likelihood, previous, primary, receipt, alternative,
        _scalar_score_inputs(likelihood, previous), 0., 0.)


def validate_scalar_coefficient_probe(
    likelihood: ScalarCoefficientLikelihood, previous: ScalarCoefficientState | None,
    primary: ScalarCoefficientState, receipt: dict, alternative: ScalarCoefficientState,
) -> None:
    """verify an unchanged energy-bearing probe using its original full objective."""
    validate_scalar_coefficient_state(likelihood, previous, primary)
    inputs = _scalar_coefficient_inputs(likelihood, previous)
    _, H, score, _, mean, _, _ = inputs
    mean_score, mean_energy = float(2*np.sum(mean*score)), float(np.sum(mean*(H @ mean)))
    offset = float(likelihood.energy-mean_score+mean_energy)
    rounding = 8*np.finfo(float).eps*(abs(likelihood.energy)+abs(mean_score)+abs(mean_energy))
    _validate_scalar_probe(likelihood, previous, primary, receipt, alternative, inputs, offset, rounding)


def _validate_scalar_probe(likelihood, previous, primary, receipt, alternative, inputs, offset, rounding):
    saved = primary.scale
    require(set(receipt) == {"saved_winner", "rechecked_candidates", "tightened_refinement", "selected",
            "saved_scale_status", "numerical_complete", "status", "scope",
            "maximum_league_relative_current_player_movement", "tolerance", "diagnostics"}
        and receipt["saved_winner"] == saved["selected"]
        and receipt["saved_scale_status"] == {key: saved[key] for key in
            ("status", "own_reasons", "inherited_limitation")}
        and receipt["scope"] == POOLING_PROBE_SCOPE and receipt["tolerance"] == 1e-4
        and alternative.scale == dict(saved, selected=receipt["selected"], numerical_original_scale=saved),
        "frozen scalar score probe scope or primary binding differs")
    winner = saved["selected"]
    coarse = [row for row in saved["curve"] if row["phase"] == "coarse"
              and row["objective"] is not None and row["exponent"] != winner["exponent"]]
    expected = [winner] + sorted(coarse,
        key=lambda row: (abs(row["exponent"]-winner["exponent"]), row["exponent"]))[:2]
    curve = receipt["rechecked_candidates"]
    require(len(curve) >= len(expected)
        and all(set(row) == {"exponent", "variance", "objective", "phase", "error", "equation_relative_residual"}
            and type(row["exponent"]) in (int, float) and -8 <= row["exponent"] <= 0
            and row["variance"] == 10.**row["exponent"] and row["error"] is None
            and type(row["objective"]) in (int, float) and math.isfinite(row["objective"])
            and row["equation_relative_residual"] is not None
            and 0 <= row["equation_relative_residual"] <= 1e-8 for row in curve)
        and all(new["phase"] == "independent_recheck" and new["exponent"] == old["exponent"]
            and math.isclose(new["objective"], old["objective"], rel_tol=1e-8, abs_tol=1e-10)
            for old, new in zip(expected, curve)),
        "frozen scalar score probe rechecks or finite solve receipts differ")
    refinement = receipt["tightened_refinement"]
    if saved["refinement"] is None:
        require(refinement is None and len(curve) == len(expected), "frozen scalar score probe added a refinement")
    else:
        require(refinement is not None and refinement["bounds"] == saved["refinement"]["bounds"]
            and refinement["xatol"] == 1e-6 and refinement["maxiter"] == 80
            and refinement["evaluations"] == len(curve)-len(expected) <= 80
            and all(row["phase"] == "refinement"
                and refinement["bounds"][0] <= row["exponent"] <= refinement["bounds"][1]
                for row in curve[len(expected):]), "frozen scalar score probe bracket or budget differs")
    selected = min(saved["curve"] + curve, key=lambda row: (row["objective"], row["variance"]))
    require(receipt["selected"] == selected
        and receipt["numerical_complete"] is (refinement is None or refinement["success"]),
        "frozen scalar score probe selection or numerical completion differs")
    H, score, mean, base = _validate_scalar_state_at_variance(
        likelihood, previous, alternative, selected["variance"], inputs)
    _, _, factor = _factor(H, base)
    objective = float(2*np.log(np.diag(factor)).sum()
                      - np.sum((score-H @ mean)*(alternative.uncentered_beta-mean)))
    require(math.isfinite(objective)
        and math.isclose(objective, selected["objective"]-offset, rel_tol=1e-8,
            abs_tol=max(1e-10, rounding+8*np.finfo(float).eps*abs(objective)))
        and alternative.diagnostics == receipt["diagnostics"],
        "frozen scalar score probe objective or posterior diagnostics differ")
    n = len(primary.player_ids)
    current = [primary.player_ids.index(player) for player in primary.current_player_ids]
    rows = current + [n+index for index in current]
    movement = dict(volume_relative=float(np.max(np.abs(alternative.beta[rows]-primary.beta[rows]))))
    require(receipt["maximum_league_relative_current_player_movement"].keys() == movement.keys()
        and math.isclose(receipt["maximum_league_relative_current_player_movement"]["volume_relative"],
            movement["volume_relative"], rel_tol=1e-10, abs_tol=1e-12)
        and receipt["status"] == ("verified" if receipt["numerical_complete"]
            and movement["volume_relative"] <= 1e-4 else "numerically_unresolved"),
        "frozen scalar score probe physical movement or status differs")


def _fit(
    population: "RevisionPopulation", previous: AnnualState | None, shared_volume: bool,
    *, representation: Literal["native_04b", "graph_40ft", "graph_two_band_80ft"], basis: ShapeBasis | None,
    model_protocol_sha256: str, prior_policy: Literal["history", "population_history"],
    volume_source: AnnualState | None = None,
) -> AnnualState:
    require(prior_policy in ("history", "population_history")
            and (prior_policy == "history" or (representation == "graph_40ft" and not shared_volume)),
            "population-history requires the one-band graph shape")
    require(previous is None or not isinstance(previous.shape, GraphShapeState)
            or "numerical_original_scale" not in previous.shape.scale,
            "bounded numerical alternatives cannot become annual history")
    require(
        (representation == "native_04b" and basis is None)
        or (
            representation in ("graph_40ft", "graph_two_band_80ft")
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
            and previous.prior_policy == prior_policy
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
    if representation == "graph_two_band_80ft" or prior_policy == "population_history":
        require(volume_source is not None and volume_source.representation == "graph_40ft"
                and volume_source.prior_policy == "history"
                and volume_source.benchmark == population.benchmark
                and volume_source.season == population.season
                and volume_source.season_index == population.season_index
                and volume_source.source_protocol_sha256 == population.protocol_sha256
                and (prior_policy == "population_history"
                     or volume_source.model_protocol_sha256 == model_protocol_sha256)
                and volume_source.population_id == population.population_id
                and volume_source.player_ids == players
                and volume_source.current_player_ids == population.player_ids
                and np.array_equal(volume_source.u, weights)
                and np.array_equal(volume_source.p, population.p)
                and np.array_equal(volume_source.response_counts, population.response_counts)
                and volume_source.volume.diagnostics.get("population_sha256") == annual_input_identity(population),
                "candidate fit requires the explicit same-input control volume")
        volume = volume_source.volume
        variance = volume.scale["selected"]["variance"]
        base[innovations, innovations] += variance
        require(np.array_equal(volume.prior_mean, M0) and np.array_equal(volume.prior_covariance, base)
                and volume.a == (variance if prior_volume is None else prior_volume.a)
                and volume.q == (None if prior_volume is None else variance),
                "shared volume previous-state lineage differs")
    else:
        require(volume_source is None, "history control cannot accept a shared volume")
        volume = _fit_block(
            H, T.sum(axis=1, keepdims=True), population.yy,
            population.ybar.sum(axis=1, keepdims=True), xbar, M0, base, innovations,
            prior_volume, weights, None,
        )
        volume.diagnostics["population_sha256"] = annual_input_identity(population)
        for array in (volume.M, volume.V, volume.A, volume.prior_mean, volume.prior_covariance):
            array.setflags(write=False)
    shape = None
    if p is not None:
        Th = T - T.sum(axis=1, keepdims=True) * p
        yh = population.ybar - population.ybar.sum(axis=1, keepdims=True) * p
        prior_shape = None if previous is None else previous.shape
        if representation == "graph_two_band_80ft":
            require(prior_shape is None or isinstance(prior_shape, TwoBandShapeState),
                    "two-band annual prior changed shape variant")
            bands = []
            for name, columns in (("low", slice(0, 11)), ("high", slice(11, 40))):
                prior_band = None if prior_shape is None else getattr(prior_shape, name)
                width = columns.stop - columns.start
                M0, base, innovations = _prior(players, previous, prior_band, width)
                started = time.monotonic()
                problem = _ScaleProblem(H, Th @ basis.B[:, columns], 0., M0, base, innovations, p,
                                        response_rank=width)
                inherited = prior_band is not None and prior_band.scale["status"] == "scale_unresolved"
                variance, scale = _select_scale(problem, inherited)
                bands.append(_band_at_scale(H, problem.T, M0, problem.covariance(variance),
                                             prior_band, weights, variance, scale, started))
            shape = _two_band_shape(H, Th, yh, xbar, basis, *bands, population.shape_yy)
        else:
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
        elif prior_policy == "population_history":
            if previous is None:
                require(isinstance(volume_source.shape, GraphShapeState)
                        and volume_source.basis is not None and volume_source.basis.sha256 == basis.sha256,
                        "initial population-history requires the same-basis control shape")
                control_shape = volume_source.shape
                scale = _initial_population_scale(control_shape.scale)
                shape = replace(control_shape, scale=scale, historical_prior_mean=control_shape.prior_mean,
                                historical_prior_covariance=control_shape.prior_covariance)
            else:
                require(isinstance(prior_shape, GraphShapeState), "population-history prior changed shape variant")
                problem = _PopulationScaleProblem(H, Th @ basis.B, population.shape_yy, M0, base, innovations)
                scale = _select_population_scale(problem, prior_shape.scale["status"] == "scale_unresolved")
                shape = _population_block_at_scale(problem, prior_shape, weights, yh, xbar, basis, scale)
        elif representation != "graph_two_band_80ft":
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
        prior_policy,
    )


def fit_revision_year(population: "RevisionPopulation", previous: AnnualState | None) -> AnnualState:
    """named native-04b scientific control, preserving its scale arithmetic."""
    return _fit(population, previous, False, representation="native_04b", basis=None,
                model_protocol_sha256=population.protocol_sha256, prior_policy="history")


def fit_recovery_year(
    population: RevisionPopulation, previous: AnnualState | None,
    *, representation: Literal["native_04b", "graph_40ft", "graph_two_band_80ft"], basis: ShapeBasis | None,
    model_protocol_sha256: str, prior_policy: Literal["history", "population_history"],
    shared_volume: AnnualState | None = None,
) -> AnnualState:
    """fit one explicitly selected representation against unchanged source references."""
    return _fit(population, previous, False, representation=representation, basis=basis,
                model_protocol_sha256=model_protocol_sha256, prior_policy=prior_policy, volume_source=shared_volume)


def fit_shared_volume_control(population: "RevisionPopulation", previous: AnnualState | None) -> AnnualState:
    """scientific 04a control only: both blocks use the volume-selected scale."""
    return _fit(population, previous, True, representation="native_04b", basis=None,
                model_protocol_sha256=population.protocol_sha256, prior_policy="history")


def shape_mean(state: AnnualState) -> np.ndarray:
    """native relative shape; graph coefficients are decoded only at this boundary."""
    require(state.shape is not None, "scalar annual state has no spatial shape")
    if state.representation == "native_04b":
        require(isinstance(state.shape, BlockState) and state.basis is None,
                "native shape state has incompatible representation")
        return state.shape.M
    if state.representation == "graph_two_band_80ft":
        require(isinstance(state.shape, TwoBandShapeState) and state.basis is not None,
                "two-band shape state has incompatible representation")
        return (state.shape.low.Theta @ state.basis.R[:, :11].T
                + state.shape.high.Theta @ state.basis.R[:, 11:].T)
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
    blocks = (state.volume, state.shape.low, state.shape.high) if isinstance(state.shape, TwoBandShapeState) else (
        state.volume, state.shape)
    for block in blocks:
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
        if state.representation == "graph_two_band_80ft":
            response_low = state.basis.R[:, :11].T @ shifted
            response_high = state.basis.R[:, 11:].T @ shifted
            mean = state.r * (moments[0][0][0] * volume
                             + moments[1][0] @ response_low + moments[2][0] @ response_high)
            variance = state.r**2 * (moments[0][1] * volume**2
                        + moments[1][1] * float(response_low @ response_low)
                        + moments[2][1] * float(response_high @ response_high))
        elif state.representation == "graph_40ft":
            response = state.basis.R.T @ shifted
            response_variance = float(response @ response)
        else:
            response = shifted
            response_variance = float(state.p @ (shifted - center) ** 2)
        if state.representation != "graph_two_band_80ft":
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
    _, moments = _row_moments(state, c)
    tolerance = state.r**2 * float(c @ c) * float(v @ v) * sum(row[2] for row in moments)
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
        if state.representation == "graph_two_band_80ft":
            R_low, R_high = state.basis.R[:, :11], state.basis.R[:, 11:]
            native_shape = moments[1][0] @ R_low.T + moments[2][0] @ R_high.T
            native_shape_variance = (moments[1][1] * np.sum(R_low**2, axis=1)
                                     + moments[2][1] * np.sum(R_high**2, axis=1))
        elif state.representation == "graph_40ft":
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
        if state.representation == "graph_two_band_80ft":
            variance = state.r**2 * (volume_variance + (
                np.zeros_like(state.p) if estimand == "volume" else native_shape_variance))
        else:
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
    if state.representation == "graph_two_band_80ft":
        shape = (state.shape.low.Theta[columns].sum(axis=1) @ state.basis.R[:, :11].T
                 + state.shape.high.Theta[columns].sum(axis=1) @ state.basis.R[:, 11:].T)
    elif state.representation == "graph_40ft":
        shape = state.shape.Theta[columns].sum(axis=1) @ state.basis.R.T
    else:
        shape = state.shape.M[columns].sum(axis=1)
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
        "history",
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
        "history",
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
        if isinstance(block, TwoBandShapeState):
            values["shape_A"] = block.A
            metadata = dict(kind="two_band", diagnostics=block.diagnostics)
            for band_name in ("low", "high"):
                band = getattr(block, band_name)
                for field in ("Theta", "V", "prior_mean", "prior_covariance"):
                    values["shape_" + band_name + "_" + field] = getattr(band, field)
                metadata[band_name] = {field: getattr(band, field) for field in ("a", "q", "scale", "diagnostics")}
            blocks[name] = metadata
            continue
        mean_name = "Theta" if isinstance(block, GraphShapeState) else "M"
        values[name + "_" + mean_name] = _coefficient_mean(block)
        for field in ("V", "A", "prior_mean", "prior_covariance"):
            values[name + "_" + field] = getattr(block, field)
        blocks[name] = dict(a=block.a, q=block.q, scale=block.scale, diagnostics=block.diagnostics)
    return blocks, values


def bounded_pooling_resolution_check(
    population: RevisionPopulation, previous: AnnualState | None, state: AnnualState,
    *, regions: np.ndarray, projections: tuple[tuple[np.ndarray, np.ndarray, str], ...] = (),
) -> tuple[AnnualState, dict]:
    """tighten only the original local bracket, with fixed incoming band priors."""
    from dataclasses import replace

    require(state.representation in ("graph_40ft", "graph_two_band_80ft")
            and state.basis is not None and population.p is not None
            and regions.shape == (656, 12) and np.isfinite(regions).all(),
            "pooling resolution requires a named graph state and fixed regions")
    _validate_pooling_state(state, population, previous, state.basis)
    players, H, T, xbar, u = _annual_inputs(population, previous)
    require(players == state.player_ids and np.array_equal(u, state.u),
            "resolution population/player reference differs")
    Th = T - T.sum(axis=1, keepdims=True) * population.p
    yh = population.ybar - population.ybar.sum(axis=1, keepdims=True) * population.p
    bands = (("low", slice(0, 11)), ("high", slice(11, 40))) if isinstance(state.shape, TwoBandShapeState) else (
        ("shape", slice(0, 40)),)
    receipts, changed = {}, {}
    for name, columns in bands:
        block = state.shape if name == "shape" else getattr(state.shape, name)
        prior = None if previous is None else (previous.shape if name == "shape" else getattr(previous.shape, name))
        M0, base, indices = _prior(players, previous, prior, columns.stop - columns.start)
        require(np.array_equal(M0, block.prior_mean), "resolution check changed incoming mean")
        score = Th @ state.basis.B[:, columns]
        problem = _ScaleProblem(H, score, population.shape_yy if name == "shape" else 0., M0,
                                base, indices, population.p,
                                basis=state.basis if name == "shape" else None,
                                response_rank=None if name == "shape" else columns.stop - columns.start)
        covariance = problem.covariance(block.scale["selected"]["variance"])
        require(np.array_equal(covariance, block.prior_covariance), "resolution check changed incoming covariance")
        saved = block.scale
        receipts[name] = _conditional_scale_probe(problem, saved)
        selected = receipts[name]["selected"]
        scale = {**saved, "selected": selected}
        if name == "shape":
            changed[name] = _block_at_scale(H, score, yh, xbar, M0,
                problem.covariance(selected["variance"]), prior, u, population.p,
                selected["variance"], scale, time.monotonic(), basis=state.basis)
        else:
            changed[name] = _band_at_scale(H, score, M0, problem.covariance(selected["variance"]),
                prior, u, selected["variance"], scale, time.monotonic())
    shape = changed["shape"] if "shape" in changed else _two_band_shape(
        H, Th, yh, xbar, state.basis, changed["low"], changed["high"], population.shape_yy)
    alternative = replace(state, shape=shape)
    positions = {player: index for index, player in enumerate(players)}
    n = len(players)
    current = [positions[player] for player in state.current_player_ids]
    rows = current + [n + index for index in current]
    delta = shape_mean(alternative)[rows] - shape_mean(state)[rows]
    movement = dict(native_cells=float(np.max(np.abs(delta))),
                    regions=float(np.max(np.abs(delta @ regions))),
                    scalars=float(np.max(np.abs(delta.sum(axis=1)))), requested_projections=0.)
    for contrast, response, estimand in projections:
        old, _ = project(state, contrast, response, estimand=estimand)
        new, _ = project(alternative, contrast, response, estimand=estimand)
        movement["requested_projections"] = max(movement["requested_projections"], abs(new - old) / state.r)
    receipt = dict(status="verified" if all(row["numerical_complete"] for row in receipts.values())
            and max(movement["native_cells"], movement["regions"]) <= 1e-4 else "withheld",
        scope=POOLING_PROBE_SCOPE,
        blocks=receipts, maximum_league_relative_current_player_movement=movement, tolerance=1e-4)
    validate_pooling_probe(receipt, state)
    return alternative, receipt


def validate_pooling_probe(probe: dict, state: AnnualState) -> bool:
    """check the exact bounded receipt against its saved original scale process."""
    blocks = {"shape": state.shape} if state.representation == "graph_40ft" else (
        {"low": state.shape.low, "high": state.shape.high}
        if state.representation == "graph_two_band_80ft" and isinstance(state.shape, TwoBandShapeState) else {})
    require(bool(blocks) and list(probe["blocks"]) == list(blocks) and probe["scope"] == POOLING_PROBE_SCOPE
            and probe["tolerance"] == 1e-4, "pooling numerical probe representation, scope or policy differs")
    complete = True
    for name, block in blocks.items():
        receipt = probe["blocks"][name]
        require(set(receipt) == {"saved_winner", "rechecked_candidates", "tightened_refinement", "selected",
                                "saved_scale_status", "numerical_complete"},
                "pooling numerical probe block fields differ")
        saved = block.scale
        winner = saved["selected"]
        require(receipt["saved_winner"] == winner and receipt["saved_scale_status"] == {
                key: saved[key] for key in ("status", "own_reasons", "inherited_limitation")},
                "pooling numerical probe changed the saved winner or limitations")
        coarse = [row for row in saved["curve"] if row["phase"] == "coarse"
                  and row["objective"] is not None and row["exponent"] != winner["exponent"]]
        nearest = sorted(coarse, key=lambda row: (abs(row["exponent"] - winner["exponent"]), row["exponent"]))[:2]
        evaluations = receipt["rechecked_candidates"]
        rechecks = [row for row in evaluations if row["phase"] == "independent_recheck"]
        require(len(rechecks) == 3 and evaluations[:3] == rechecks
                and [row["exponent"] for row in rechecks] == [row["exponent"] for row in [winner] + nearest],
                "pooling numerical probe did not recheck the selected and two nearest coarse points")
        objective_field = "full_objective" if name == "shape" else "band_objective"
        expected_fields = {"exponent", "variance", "objective", "phase", "error", "equation_relative_residual", objective_field}
        for row in evaluations:
            require(set(row) == expected_fields and type(row["exponent"]) in (int, float)
                    and -8 <= row["exponent"] <= 0 and type(row["variance"]) in (int, float)
                    and row["variance"] == 10. ** row["exponent"]
                    and row["phase"] in ("independent_recheck", "refinement")
                    and (row["equation_relative_residual"] is None or (
                        type(row["equation_relative_residual"]) in (int, float)
                        and math.isfinite(row["equation_relative_residual"]) and row["equation_relative_residual"] >= 0))
                    and ((row["objective"] is None and row[objective_field] is None
                          and isinstance(row["error"], str) and bool(row["error"]))
                         or (row["error"] is None and type(row["objective"]) in (int, float)
                             and type(row[objective_field]) in (int, float) and math.isfinite(row["objective"])
                             and math.isfinite(row[objective_field]) and row["equation_relative_residual"] is not None
                             and row["equation_relative_residual"] <= 1e-8)),
                    "pooling numerical probe has an invalid bounded objective evaluation")
        for old, new in zip([winner] + nearest, rechecks, strict=True):
            require(new["objective"] is None or math.isclose(old["objective"], new["objective"], rel_tol=1e-8, abs_tol=1e-10),
                    "pooling numerical probe recheck differs from the saved objective")
        refinement, original = receipt["tightened_refinement"], saved["refinement"]
        refined = [row for row in evaluations if row["phase"] == "refinement"]
        require((refinement is None) == (original is None)
                and (refinement is not None or not refined), "pooling numerical probe changed refinement availability")
        if refinement is not None:
            require(set(refinement) == {"bounds", "success", "message", "evaluations", "exponent", "xatol", "maxiter"}
                    and refinement["bounds"] == original["bounds"]
                    and -8 <= refinement["bounds"][0] < refinement["bounds"][1] <= 0
                    and refinement["xatol"] == 1e-6 and refinement["maxiter"] == 80
                    and type(refinement["evaluations"]) is int and refinement["evaluations"] == len(refined) <= 80
                    and type(refinement["success"]) is bool and isinstance(refinement["message"], str)
                    and type(refinement["exponent"]) in (int, float) and math.isfinite(refinement["exponent"])
                    and refinement["bounds"][0] <= refinement["exponent"] <= refinement["bounds"][1]
                    and all(refinement["bounds"][0] <= row["exponent"] <= refinement["bounds"][1] for row in refined),
                    "pooling numerical probe changed its original bracket or tighter search budget")
        valid = [row for row in saved["curve"] + evaluations if row["objective"] is not None]
        require(receipt["selected"] == min(valid, key=lambda row: (row["objective"], row["variance"])),
                "pooling numerical probe selected a point outside the original and checked evaluations")
        numerical_complete = all(row["objective"] is not None for row in evaluations) and (
            refinement is None or refinement["success"])
        require(receipt["numerical_complete"] is numerical_complete,
                "pooling numerical probe completeness contradicts its evaluations")
        complete = complete and numerical_complete
    movement = probe["maximum_league_relative_current_player_movement"]
    require(set(movement) == {"native_cells", "regions", "scalars", "requested_projections"}
            and all(type(value) in (int, float) and math.isfinite(value) and value >= 0 for value in movement.values()),
            "pooling numerical probe movements are invalid")
    verified = complete and max(movement["native_cells"], movement["regions"]) <= 1e-4
    require(probe["status"] == ("verified" if verified else "withheld"),
            "pooling numerical probe status contradicts the specified native/regional movement limit")
    return verified


def read_pooling_source(path: Path | str) -> PoolingSource:
    """validate one fixed synthetic preparation before consuming annual states."""
    path = Path(path).resolve(strict=True)
    prepared = read_artifact(path, "attribution_pooling_prepared", expected_schema=4)
    protocol = read_artifact(linked_path(prepared["protocol"]), "attribution_pooling_protocol", expected_schema=4)
    require(prepared["purpose"] == protocol["purpose"]
            and prepared["spec_snapshot"] == protocol["spec_snapshot"]
            and all(prepared[name] == protocol[name] for name in ("basis", "basis_sha256", "design_sha256"))
            and prepared["consumed"] == dict(protocol=prepared["protocol"], basis=prepared["basis"],
                spec_snapshot=prepared["spec_snapshot"], designs=prepared["designs"]["arrays"])
            and prepared["implementation"] == protocol["implementation"]
            and prepared["seasons"] == [row["season"] for row in prepared["years"]]
            and prepared["seasons"] == protocol["seasons"]
            and prepared["seasons"] == [f"{year}{year+1}" for year in range(2021, 2026)]
            and len(prepared["years"]) == 5,
            "pooling preparation protocol, specification or annual inventory differs")
    require(ordered_array_digest(load_arrays(prepared["designs"])) == prepared["design_sha256"],
            "pooling preparation design bytes differ from the frozen protocol")
    basis = read_shape_basis(prepared)
    validate_pooling_basis(basis)
    return PoolingSource(identity(path), prepared, protocol, basis)


def read_pooling_statistics(reference: dict, source: PoolingSource) -> PoolingStatistics:
    """load one compact five-year dataset with exact original ordering and dtypes."""
    with np.load(linked_path(reference), allow_pickle=False) as archive:
        require(archive.files == [year["season"] + "_" + field
                                 for year in source.prepared["years"] for field in POOLING_STAT_FIELDS],
                "pooling sufficient-statistic names/order differ")
        arrays = {name: archive[name] for name in archive.files}
    require(all(np.isfinite(value).all() and value.dtype == np.dtype(
                "int64" if name.endswith("_player_ids") else "float64") for name, value in arrays.items()),
            "pooling sufficient-statistic dtype or finiteness differs")
    return PoolingStatistics(reference, source.reference["sha256"], arrays)


def _pooling_blocks(state: AnnualState) -> tuple[tuple[str, BlockState | GraphShapeState | ShapeBandState, int], ...]:
    require(state.representation in ("graph_40ft", "graph_two_band_80ft") and state.basis is not None,
            "pooling annual requires an explicitly named graph representation")
    if state.representation == "graph_40ft":
        require(isinstance(state.shape, GraphShapeState), "pooling control shape variant differs")
        return (("volume", state.volume, 1), ("shape", state.shape, 40))
    require(isinstance(state.shape, TwoBandShapeState), "pooling candidate shape variant differs")
    return (("volume", state.volume, 1), ("shape_low", state.shape.low, 11), ("shape_high", state.shape.high, 29))


def validate_shape_scale_receipt(scale: dict, previous_scale: dict | None) -> None:
    """validate a saved scale search and its explicit incoming limitation metadata."""
    require(set(scale) == {"status", "own_reasons", "inherited_limitation", "curve", "competing_coarse_minima",
                           "refinement", "selected"}, "pooling scale receipt fields differ")
    curve = scale["curve"]
    coarse = [row for row in curve if row["phase"] == "coarse"]
    require([row["exponent"] for row in coarse] == np.arange(-8, 0.1, .5).tolist()
            and all(type(row["exponent"]) in (int, float) and -8 <= row["exponent"] <= 0
                    and row["variance"] == 10. ** row["exponent"]
                    and row["phase"] in ("coarse", "refinement")
                    and ((row["objective"] is None and isinstance(row["error"], str))
                         or (row["error"] is None and type(row["objective"]) in (int, float)
                             and math.isfinite(row["objective"]))) for row in curve),
            "pooling scale grid, bounds or finite search receipt differs")
    valid = [row for row in curve if row["objective"] is not None]
    require(bool(valid) and scale["selected"] == min(valid, key=lambda row: (row["objective"], row["variance"])),
            "pooling selected scale differs from its original search")
    refinement = scale["refinement"]
    own = []
    if scale["selected"]["exponent"] in (-8, 0):
        own.append("endpoint_winner")
    if refinement is None or not refinement["success"]:
        own.append("refinement_failed")
    if any(row["phase"] == "refinement" and row["objective"] is None for row in curve):
        own.append("nonfinite_refinement")
    inherited = previous_scale is not None and previous_scale["status"] == "scale_unresolved"
    require(scale["own_reasons"] == own and scale["inherited_limitation"] is inherited
            and scale["status"] == ("scale_unresolved" if own or inherited else "resolved"),
            "pooling selected scale dropped its own or inherited numerical limitation")
    if refinement is not None:
        interior = [row for row in coarse[1:-1] if row["objective"] is not None]
        require(bool(interior), "pooling refinement has no original interior coarse point")
        center = min(interior, key=lambda row: (row["objective"], row["exponent"]))["exponent"]
        require(refinement["bounds"] == [center - .5, center + .5]
                and refinement["evaluations"] <= 40, "pooling original refinement bracket or budget changed")


def _validate_pooling_scale(scale: dict, problem: _ScaleProblem, previous) -> None:
    validate_shape_scale_receipt(scale, None if previous is None else previous.scale)
    value = problem.objective(scale["selected"]["exponent"], "saved_state_recheck")
    objective_field = "band_objective" if problem.band else "full_objective"
    require(math.isfinite(value) and math.isclose(value, scale["selected"]["objective"], rel_tol=1e-8, abs_tol=1e-10)
            and (not problem.reduced or math.isclose(problem.curve[-1][objective_field],
                scale["selected"][objective_field], rel_tol=1e-8, abs_tol=1e-10)),
            "pooling selected reduced/full objective differs from its saved likelihood")


def _validate_pooling_state(state: AnnualState, population: RevisionPopulation,
                            previous: AnnualState | None, basis: ShapeBasis) -> None:
    players, H, T, xbar, u = _annual_inputs(population, previous)
    require(state.benchmark == "unblocked_spatial" and state.season == population.season
            and state.season_index == population.season_index and state.player_ids == players
            and state.current_player_ids == population.player_ids
            and state.entrant_ids == tuple(player for player in population.player_ids
                                           if previous is None or player not in previous.player_ids)
            and state.carried_only_ids == tuple(player for player in players if player not in population.player_ids)
            and state.source_protocol_sha256 == state.model_protocol_sha256 == population.protocol_sha256
            and state.population_id == population.population_id and state.r == population.r
            and state.basis is not None and state.basis.sha256 == basis.sha256
            and np.array_equal(state.u, u) and np.array_equal(state.p, basis.p)
            and np.array_equal(state.p, population.p)
            and np.array_equal(state.response_counts, population.response_counts)
            and state.volume.diagnostics.get("population_sha256") == annual_input_identity(population),
            "pooling annual source references, response or identity differs")
    require(previous is None or (previous.representation == state.representation
            and previous.model_protocol_sha256 == state.model_protocol_sha256
            and previous.basis is not None and previous.basis.sha256 == state.basis.sha256),
            "pooling annual preceding representation/model differs")
    n = len(players)
    for name, block, width in _pooling_blocks(state):
        prior = None if previous is None else (previous.volume if name == "volume" else
                previous.shape if name == "shape" else getattr(previous.shape, name.removeprefix("shape_")))
        mean = _coefficient_mean(block)
        require(mean.shape == block.prior_mean.shape == (2 * n, width)
                and block.V.shape == block.prior_covariance.shape == (2 * n, 2 * n)
                and all(np.isfinite(array).all() for array in (mean, block.V, block.prior_mean, block.prior_covariance)),
                "pooling annual block shape or finiteness differs")
        variance = block.scale["selected"]["variance"]
        require(type(variance) in (int, float) and math.isfinite(variance) and 1e-8 <= variance <= 1,
                "pooling annual selected variance is invalid")
        M0, base, selected = _prior(players, previous, prior, width)
        covariance = base.copy()
        covariance[selected, selected] += variance
        score = T.sum(axis=1, keepdims=True) if name == "volume" else (
            T - T.sum(axis=1, keepdims=True) * population.p) @ basis.B[:,
                slice(0, 40) if name == "shape" else slice(0, 11) if name == "shape_low" else slice(11, 40)]
        problem = _ScaleProblem(H, score, population.yy if name == "volume" else
            population.shape_yy if name == "shape" else 0., M0, base, selected,
            None if name == "volume" else population.p, basis=basis if name == "shape" else None,
            response_rank=width if name.startswith("shape_") else None)
        _validate_pooling_scale(block.scale, problem, prior)
        tolerance = block.diagnostics["covariance_rounding_tolerance"]
        expected_tolerance = float(1e-10 * max(1, np.linalg.norm(block.V, ord=np.inf)))
        require(block.a == (variance if prior is None else prior.a)
                and block.q == (None if prior is None else variance)
                and np.array_equal(block.prior_mean, M0) and np.array_equal(block.prior_covariance, covariance)
                and tolerance == expected_tolerance
                and np.max(np.abs(block.V - block.V.T)) <= tolerance
                and np.min(np.linalg.eigvalsh(block.V)) >= -max(tolerance, 1e-12)
                and np.max(np.abs(u @ mean[:n])) <= 1e-8
                and np.max(np.abs(u @ mean[n:])) <= 1e-8
                and np.max(np.abs(u @ block.V[:n])) <= tolerance
                and np.max(np.abs(u @ block.V[n:])) <= tolerance,
                "pooling annual full covariance, centering or proper prior lineage differs")
        np.linalg.cholesky(block.prior_covariance)
    require(state.volume.A.shape == (len(population.strata), 1)
            and np.isfinite(state.volume.A).all()
            and state.shape.A.shape == (len(population.strata), 656)
            and np.isfinite(state.shape.A).all()
            and np.allclose(state.volume.A, population.ybar.sum(axis=1, keepdims=True) - xbar @ state.volume.M,
                            rtol=1e-8, atol=1e-10)
            and np.allclose(state.shape.A, population.ybar - population.ybar.sum(axis=1, keepdims=True) * population.p
                            - xbar @ shape_mean(state), rtol=1e-8, atol=1e-10)
            and np.max(np.abs(shape_mean(state).sum(axis=1))) <= 1e-8
            and np.max(np.abs(state.shape.A.sum(axis=1))) <= 1e-8,
            "pooling annual context shape/finiteness/conservation differs")
    if isinstance(state.shape, TwoBandShapeState):
        Th = T - T.sum(axis=1, keepdims=True) * population.p
        yh = population.ybar - population.ybar.sum(axis=1, keepdims=True) * population.p
        expected = _two_band_shape(H, Th, yh, xbar, basis, state.shape.low, state.shape.high, population.shape_yy)
        require(np.array_equal(state.shape.A, expected.A) and state.shape.diagnostics == expected.diagnostics,
                "pooling annual duplicated response energy or context differs")


def write_pooling_annual(
    state: AnnualState, prepared: PoolingSource | Path | str, previous: Path | str | None, out: Path | str,
    *, population: str, law: str, outer: int, response_sha256: str, statistics: PoolingStatistics | dict,
    shared_volume: dict | None = None, previous_state: AnnualState | None = None,
    shared_volume_state: AnnualState | None = None,
) -> dict:
    """write fresh schema-4 synthetic evidence; frozen schema-3 states stay separate."""
    started = time.monotonic()
    context = prepared if isinstance(prepared, PoolingSource) else read_pooling_source(prepared)
    source, protocol, basis = context.prepared, context.protocol, context.basis
    statistics = statistics if isinstance(statistics, PoolingStatistics) else read_pooling_statistics(statistics, context)
    original = pooling_population(context, statistics, population, law, outer, state.season)
    previous_path = None if previous is None else Path(previous).resolve(strict=True)
    require(previous_path is not None or previous_state is None, "initial annual cannot supply a preceding state")
    prior = previous_state if previous_state is not None else (
        None if previous_path is None else read_pooling_annual(previous_path, source=context, statistics=statistics))
    if previous_path is not None:
        prior_document = read_json(previous_path)
        require(prior_document["prepared"] == context.reference
                and prior_document["statistics"] == statistics.reference
                and prior_document["population"] == population and prior_document["law"] == law
                and prior_document["outer"] == outer and prior_document["representation"] == state.representation
                and prior_document["season"] == prior.season and prior_document["season_index"] == prior.season_index,
                "pooling writer preceding annual reference differs")
    _validate_pooling_state(state, original, prior, basis)
    digest(response_sha256)
    require(shared_volume is not None or shared_volume_state is None,
            "explicit shared volume state requires its annual reference")
    shared = shared_volume_state if shared_volume_state is not None else (
        None if shared_volume is None else read_pooling_annual(linked_path(shared_volume), source=context, statistics=statistics))
    if shared_volume is not None:
        shared_document = read_json(linked_path(shared_volume))
        require(shared_document["prepared"] == context.reference
                and shared_document["statistics"] == statistics.reference
                and shared_document["population"] == population and shared_document["law"] == law
                and shared_document["outer"] == outer and shared_document["season"] == state.season
                and shared_document["response_sha256"] == response_sha256,
                "pooling writer shared volume changed response/data lineage")
    require((state.representation == "graph_40ft" and shared is None)
            or (state.representation == "graph_two_band_80ft" and shared is not None
                and shared.representation == "graph_40ft" and shared.season == state.season
                and shared.population_id == state.population_id
                and all(np.array_equal(getattr(state.volume, field), getattr(shared.volume, field))
                        for field in ("M", "V", "A", "prior_mean", "prior_covariance"))
                and all(getattr(state.volume, field) == getattr(shared.volume, field)
                        for field in ("a", "q", "scale", "diagnostics"))),
            "pooling candidate shared-volume artifact differs")
    output = output_path(str(out), [])
    require(output.is_relative_to(Path(protocol["output_root"]).resolve())
            and (source["purpose"] != "research" or output.is_relative_to(Path("/Volumes/Expansion/hockey-stats/runs"))),
            "pooling annual output differs from its frozen root")
    blocks, values = annual_arrays(state)
    if state.representation == "graph_40ft":
        blocks["shape"] = dict(kind="one_band", **blocks["shape"])
    parents = dict(prepared=context.reference, protocol=source["protocol"],
                   previous=None if previous_path is None else identity(previous_path), statistics=statistics.reference,
                   shared_volume=shared_volume, basis=source["basis"], spec_snapshot=source["spec_snapshot"])
    output.mkdir()
    arrays = write_arrays(output, "state.npz", values)
    document = artifact("attribution_pooling_annual", source["purpose"], parents, schema_version=4,
        **parents, source_kind="synthetic", representation=state.representation, basis_shapes=source["basis_shapes"],
        basis_sha256=basis.sha256, design_sha256=source["design_sha256"], population=population, law=law, outer=outer,
        benchmark=state.benchmark, season=state.season, season_index=state.season_index,
        population_id=state.population_id, player_ids=state.player_ids, current_player_ids=state.current_player_ids,
        entrant_ids=state.entrant_ids, carried_only_ids=state.carried_only_ids, r=state.r, strata=original.strata,
        response_sha256=response_sha256, annual_input_sha256=annual_input_identity(original),
        volume=blocks["volume"], shape=blocks["shape"], **arrays,
        units=POOLING_UNITS,
        resources=resources(started))
    require(source["purpose"] != "research" or document["implementation"] == protocol["implementation"],
            "pooling annual producer differs from frozen protocol")
    write_json(output / "annual.json", document)
    return identity(output / "annual.json")


def read_pooling_annual(
    path: Path | str, *, source: PoolingSource | None = None,
    previous: tuple[dict, AnnualState] | None = None, shared_volume: tuple[dict, AnnualState] | None = None,
    statistics: PoolingStatistics | None = None,
) -> AnnualState:
    """strict schema 4, with explicit shape tags and exact chronological band priors."""
    document = read_artifact(path, "attribution_pooling_annual", expected_schema=4)
    context = read_pooling_source(linked_path(document["prepared"])) if source is None else source
    source, protocol, basis = context.prepared, context.protocol, context.basis
    require(document["prepared"] == context.reference
            and document["source_kind"] == "synthetic" and document["purpose"] == source["purpose"]
            and document["units"] == POOLING_UNITS
            and all(document[name] == source[name] for name in
                    ("protocol", "basis", "basis_shapes", "basis_sha256", "design_sha256", "spec_snapshot"))
            and document["consumed"] == {name: document[name] for name in
                    ("prepared", "protocol", "previous", "statistics", "shared_volume", "basis", "spec_snapshot")}
            and (source["purpose"] != "research" or document["implementation"] == protocol["implementation"]),
            "pooling annual preparation/producer/source binding differs")
    digest(document["response_sha256"])
    statistics = read_pooling_statistics(document["statistics"], context) if statistics is None else statistics
    require(statistics.reference == document["statistics"], "pooling annual statistics source differs")
    original = pooling_population(context, statistics, document["population"], document["law"],
                                   document["outer"], document["season"])
    require(document["annual_input_sha256"] == annual_input_identity(original)
            and document["strata"] == list(map(list, original.strata)),
            "pooling annual sufficient-statistic identity differs")
    require(previous is None or previous[0] == document["previous"],
            "explicit preceding annual reference differs")
    prior = previous[1] if previous is not None else (None if document["previous"] is None else
        read_pooling_annual(linked_path(document["previous"]), source=context, statistics=statistics))
    if document["previous"] is not None:
        prior_document = read_json(linked_path(document["previous"]))
        require(all(document[name] == prior_document[name] for name in
                    ("prepared", "protocol", "population", "law", "outer", "statistics", "representation")),
                "pooling annual chronological source lineage differs")
    players = tuple(document["player_ids"])
    n, s = len(players), len(original.strata)
    shapes = dict(u=(n,), response_counts=(656,), p=(656,), volume_M=(2*n, 1), volume_V=(2*n, 2*n),
                  volume_A=(s, 1), volume_prior_mean=(2*n, 1), volume_prior_covariance=(2*n, 2*n))
    shape_metadata = document["shape"]
    representation = document["representation"]
    if representation == "graph_40ft":
        require(set(shape_metadata) == {"kind", "a", "q", "scale", "diagnostics"}
                and shape_metadata["kind"] == "one_band", "pooling control shape tag differs")
        shapes.update(shape_Theta=(2*n, 40), shape_V=(2*n, 2*n), shape_A=(s, 656),
                      shape_prior_mean=(2*n, 40), shape_prior_covariance=(2*n, 2*n))
    else:
        require(representation == "graph_two_band_80ft" and set(shape_metadata) == {"kind", "low", "high", "diagnostics"}
                and shape_metadata["kind"] == "two_band", "pooling candidate shape tag differs")
        shapes["shape_A"] = (s, 656)
        for name, width in (("low", 11), ("high", 29)):
            shapes.update({"shape_" + name + "_" + field: shape for field, shape in
                dict(Theta=(2*n, width), V=(2*n, 2*n), prior_mean=(2*n, width), prior_covariance=(2*n, 2*n)).items()})
    values = load_arrays(document)
    require(list(values) == list(shapes) and all(values[name].shape == shape for name, shape in shapes.items()),
            "pooling annual array names/order/rank differ")
    blocks = {}
    names = ("volume", "shape") if representation == "graph_40ft" else ("volume", "shape_low", "shape_high")
    for name in names:
        metadata = document[name] if name in ("volume", "shape") else shape_metadata[name.removeprefix("shape_")]
        expected = {"a", "q", "scale", "diagnostics"} | ({"kind"} if name == "shape" else set())
        require(set(metadata) == expected, "pooling annual block metadata differs")
        fields = {field: metadata[field] for field in ("a", "q", "scale", "diagnostics")}
        fields.update({field: values[name + "_" + field] for field in ("V", "prior_mean", "prior_covariance")})
        if name == "volume":
            blocks[name] = BlockState(values["volume_M"], A=values["volume_A"], **fields)
        elif name == "shape":
            blocks[name] = GraphShapeState(values["shape_Theta"], A=values["shape_A"], **fields)
        else:
            blocks[name] = ShapeBandState(values[name + "_Theta"], **fields)
    shape = blocks["shape"] if representation == "graph_40ft" else TwoBandShapeState(
        blocks["shape_low"], blocks["shape_high"], values["shape_A"], shape_metadata["diagnostics"])
    state = AnnualState(document["benchmark"], document["season"], document["season_index"],
        document["protocol"]["sha256"], document["protocol"]["sha256"], representation, basis,
        document["population_id"], players, tuple(document["current_player_ids"]), tuple(document["entrant_ids"]),
        tuple(document["carried_only_ids"]), blocks["volume"], shape, document["r"], values["u"], values["p"],
        values["response_counts"], "history")
    _validate_pooling_state(state, original, prior, basis)
    if representation == "graph_40ft":
        require(document["shared_volume"] is None and shared_volume is None,
                "pooling control cannot bind another volume")
    else:
        require(document["shared_volume"] is not None, "pooling candidate shared volume is missing")
        shared_path = linked_path(document["shared_volume"])
        shared_document = read_json(shared_path)
        require(all(document[name] == shared_document[name] for name in
                ("prepared", "protocol", "population", "law", "outer", "statistics", "season", "response_sha256")),
                "pooling candidate changed shared response/data lineage")
        require(shared_volume is None or shared_volume[0] == document["shared_volume"],
                "explicit shared-volume annual reference differs")
        shared = shared_volume[1] if shared_volume is not None else read_pooling_annual(
            shared_path, source=context, statistics=statistics)
        require(shared.representation == "graph_40ft" and shared.player_ids == state.player_ids
                and all(np.array_equal(getattr(state.volume, field), getattr(shared.volume, field))
                        for field in ("M", "V", "A", "prior_mean", "prior_covariance"))
                and all(getattr(state.volume, field) == getattr(shared.volume, field)
                        for field in ("a", "q", "scale", "diagnostics")),
                "pooling candidate shared volume block differs")
        from dataclasses import replace
        state = replace(state, volume=shared.volume)
    for array in (state.volume.M, state.volume.V, state.volume.A, state.volume.prior_mean, state.volume.prior_covariance):
        array.setflags(write=False)
    return state


REGULARIZATION_UNITS = dict(POOLING_UNITS, historical_prior="proper pre-population full row gaussian",
    population_precision="inverse relative-rate-squared", objective="full native gaussian marginal objective")
REGULARIZATION_PROBE_SCOPE = "fixed_incoming_history_bounded_local_resolution_not_propagated_or_global_optimum"


def _regularization_probe_points(scale):
    best = scale["best_coarse"]
    points = [(scale["selected"]["exponent"], scale["selected"]["population_exponent"])]
    for dx in (-.5, 0., .5):
        for dt in (-.5, 0., .5):
            point = (best["exponent"] + dx, best["population_exponent"] + dt)
            if -8 <= point[0] <= 0 and 0 <= point[1] <= 8 and point not in points:
                points.append(point)
    return points


def _regularization_rechecks_match(saved, evaluations):
    originals = {(row["exponent"], row["population_exponent"]): row for row in saved["curve"]
                 if row["phase"] == "coarse"}
    winner = saved["selected"]
    originals[(winner["exponent"], winner["population_exponent"])] = winner
    return all(row["objective"] is not None and originals[(row["exponent"], row["population_exponent"])]["objective"] is not None
        and abs(row["objective"] - originals[(row["exponent"], row["population_exponent"])]["objective"])
            <= 1e-8 * (1 + abs(originals[(row["exponent"], row["population_exponent"])]["objective"]))
        for row in evaluations if row["phase"] == "independent_recheck")


def bounded_regularization_resolution_check(
    population: RevisionPopulation, previous: AnnualState, state: AnnualState, *, regions: np.ndarray,
) -> tuple[AnnualState, dict]:
    """probe the original box against the unchanged incoming candidate history."""
    require(state.prior_policy == "population_history" and state.season_index > 0
            and isinstance(state.shape, GraphShapeState) and state.basis is not None
            and regions.shape == (656, 12) and np.isfinite(regions).all()
            and "numerical_original_scale" not in state.shape.scale,
            "regularization probe requires an original later candidate and fixed regions")
    players, H, T, xbar, u = _annual_inputs(population, previous)
    require(players == state.player_ids and state.model_protocol_sha256 == previous.model_protocol_sha256
            and previous.prior_policy == "population_history", "regularization probe incoming history differs")
    Th = T - T.sum(axis=1, keepdims=True) * population.p
    yh = population.ybar - population.ybar.sum(axis=1, keepdims=True) * population.p
    M0, base, indices = _prior(players, previous, previous.shape, 40)
    problem = _PopulationScaleProblem(H, Th @ state.basis.B, population.shape_yy, M0, base, indices)
    _validate_population_scale(state.shape.scale, problem, previous.shape)
    problem.curve.clear()
    saved = state.shape.scale
    for point in _regularization_probe_points(saved):
        problem.objective(point, "independent_recheck")
    bounds = saved["refinement"]["bounds"]
    for x in np.arange(bounds[0][0], bounds[0][1] + .125, .25):
        for t in np.arange(bounds[1][0], bounds[1][1] + .125, .25):
            problem.objective((x, t), "quarter_step")
    fit = minimize(lambda pair: problem.objective(pair, "tightened_refinement"),
        [saved["best_coarse"]["exponent"], saved["best_coarse"]["population_exponent"]],
        method="Powell", bounds=bounds, options=dict(xtol=1e-6, ftol=1e-12, maxfev=320))
    refinement = dict(bounds=bounds, success=bool(fit.success), message=str(fit.message),
        evaluations=int(fit.nfev), coordinates=[float(value) for value in fit.x], xtol=1e-6, ftol=1e-12, maxfev=320)
    curve = saved["curve"] + problem.curve
    selected = min((row for row in curve if row["objective"] is not None), key=_population_scale_key)
    scale = dict(saved, curve=curve, selected=dict(selected), numerical_original_scale=saved)
    shape = _population_block_at_scale(problem, previous.shape, u, yh, xbar, state.basis, scale)
    alternative = replace(state, shape=shape)
    positions = {player: index for index, player in enumerate(players)}
    current = [positions[player] for player in state.current_player_ids]
    rows = current + [len(players) + index for index in current]
    delta = shape_mean(alternative)[rows] - shape_mean(state)[rows]
    movement = dict(native_cells=float(np.max(np.abs(delta))), regions=float(np.max(np.abs(delta @ regions))))
    complete = (all(row["objective"] is not None for row in problem.curve) and bool(fit.success)
                and _regularization_rechecks_match(saved, problem.curve))
    original_arrays = dict(Theta=state.shape.Theta, V=state.shape.V, A=state.shape.A)
    alternative_arrays = dict(Theta=shape.Theta, V=shape.V, A=shape.A)
    receipt = dict(status="verified" if complete and max(movement.values()) <= 1e-4 else "numerically_unresolved",
        scope=REGULARIZATION_PROBE_SCOPE, saved_winner=saved["selected"], best_coarse=saved["best_coarse"],
        evaluations=problem.curve, tightened_refinement=refinement, selected=dict(selected),
        original_state_sha256=ordered_array_digest(original_arrays),
        alternative_state_sha256=ordered_array_digest(alternative_arrays),
        maximum_league_relative_current_player_movement=movement, tolerance=1e-4, numerical_complete=complete)
    validate_regularization_probe(receipt, alternative)
    return alternative, receipt


def validate_regularization_probe(probe: dict, state: AnnualState) -> bool:
    """validate saved numerical evidence without evaluating or searching a parameter."""
    saved = state.shape.scale.get("numerical_original_scale", state.shape.scale)
    require(set(probe) in ({"status", "scope", "saved_winner", "best_coarse", "evaluations", "tightened_refinement",
                "selected", "original_state_sha256", "alternative_state_sha256",
                "maximum_league_relative_current_player_movement", "tolerance", "numerical_complete"},
            {"status", "scope", "saved_winner", "best_coarse", "evaluations", "tightened_refinement",
                "selected", "original_state_sha256", "alternative_state_sha256", "original_annual",
                "maximum_league_relative_current_player_movement", "tolerance", "numerical_complete"})
        and state.prior_policy == "population_history" and state.season_index > 0
        and probe["scope"] == REGULARIZATION_PROBE_SCOPE and probe["tolerance"] == 1e-4
        and probe["saved_winner"] == saved["selected"] and probe["best_coarse"] == saved["best_coarse"],
        "regularization probe scope, original selection or fields differ")
    evaluations = probe["evaluations"]
    rechecks = [row for row in evaluations if row["phase"] == "independent_recheck"]
    require([(row["exponent"], row["population_exponent"]) for row in rechecks] == _regularization_probe_points(saved)
        and evaluations[:len(rechecks)] == rechecks, "regularization probe omitted an original grid neighbor")
    for row in evaluations:
        require(set(row) == {"exponent", "population_exponent", "variance", "lambda", "objective", "phase", "error",
                            "equation_relative_residual"}
            and -8 <= row["exponent"] <= 0 and 0 <= row["population_exponent"] <= 8
            and row["variance"] == 10. ** row["exponent"] and row["lambda"] == 10. ** row["population_exponent"] - 1
            and row["phase"] in ("independent_recheck", "quarter_step", "tightened_refinement")
            and ((row["objective"] is None and isinstance(row["error"], str) and bool(row["error"]))
                or (row["error"] is None and type(row["objective"]) in (int, float) and math.isfinite(row["objective"])
                    and type(row["equation_relative_residual"]) in (int, float)
                    and 0 <= row["equation_relative_residual"] <= 1e-8)),
            "regularization probe contains an invalid evaluation")
    bounds = saved["refinement"]["bounds"]
    require([(row["exponent"], row["population_exponent"]) for row in evaluations if row["phase"] == "quarter_step"]
        == [(float(x), float(t)) for x in np.arange(bounds[0][0], bounds[0][1] + .125, .25)
            for t in np.arange(bounds[1][0], bounds[1][1] + .125, .25)],
        "regularization probe quarter-step grid differs from the original box")
    refinement = probe["tightened_refinement"]
    refined = [row for row in evaluations if row["phase"] == "tightened_refinement"]
    require(set(refinement) == {"bounds", "success", "message", "evaluations", "coordinates", "xtol", "ftol", "maxfev"}
        and refinement["bounds"] == bounds and refinement["xtol"] == 1e-6 and refinement["ftol"] == 1e-12
        and refinement["maxfev"] == 320 and refinement["evaluations"] == len(refined) <= 320
        and type(refinement["success"]) is bool and all(bounds[0][0] <= row["exponent"] <= bounds[0][1]
            and bounds[1][0] <= row["population_exponent"] <= bounds[1][1] for row in refined),
        "regularization probe tightened refinement changed its box or budget")
    curve = saved["curve"] + evaluations
    require(probe["selected"] == min((row for row in curve if row["objective"] is not None), key=_population_scale_key),
            "regularization probe winner is not the best finite original/probe evaluation")
    complete = (all(row["objective"] is not None for row in evaluations) and refinement["success"]
                and _regularization_rechecks_match(saved, evaluations))
    movement = probe["maximum_league_relative_current_player_movement"]
    require(set(movement) == {"native_cells", "regions"}
        and all(type(value) in (int, float) and math.isfinite(value) and value >= 0 for value in movement.values())
        and probe["numerical_complete"] is complete, "regularization probe completeness or movement is invalid")
    verified = complete and max(movement.values()) <= 1e-4
    require(probe["status"] == ("verified" if verified else "numerically_unresolved"),
            "regularization probe status contradicts its bounded numerical evidence")
    for name in ("original_state_sha256", "alternative_state_sha256"):
        digest(probe[name])
    key = "alternative_state_sha256" if "numerical_original_scale" in state.shape.scale else "original_state_sha256"
    require(probe[key] == ordered_array_digest(dict(Theta=state.shape.Theta, V=state.shape.V, A=state.shape.A)),
            "regularization probe native state identity differs")
    if "numerical_original_scale" in state.shape.scale:
        require(state.shape.scale["curve"] == curve and state.shape.scale["selected"] == probe["selected"],
                "regularization probe alternative differs from its evaluated state")
    if "original_annual" in probe:
        original = read_artifact(linked_path(probe["original_annual"]), "attribution_regularization_annual", expected_schema=5)
        arrays = load_arrays(original)
        require(original["shape"]["scale"] == saved and original["prior_policy"] == "population_history"
            and original["season"] == state.season and original["model_protocol_sha256"] == state.model_protocol_sha256
            and probe["original_state_sha256"] == ordered_array_digest(
                dict(Theta=arrays["shape_Theta"], V=arrays["shape_V"], A=arrays["shape_A"])),
            "regularization probe original annual source differs")
    return verified


def _validate_population_scale(scale: dict, problem: _PopulationScaleProblem, previous: GraphShapeState) -> None:
    original = scale.get("numerical_original_scale", scale)
    require(set(original) == {"status", "own_reasons", "inherited_limitation", "prior_policy",
        "population_precision_status", "limits", "curve", "best_coarse", "boundary", "refinement", "selected"}
        and original["prior_policy"] == "population_history" and original["population_precision_status"] == "estimated"
        and original["limits"] == dict(exponent=[-8., 0.], population_exponent=[0., 8.], coarse_spacing=.5),
        "population-history scale policy or bounds differ")
    curve = original["curve"]
    coarse = [row for row in curve if row["phase"] == "coarse"]
    require([(row["exponent"], row["population_exponent"]) for row in coarse]
            == [(float(x), float(t)) for x in np.arange(-8, .1, .5) for t in np.arange(0, 8.1, .5)],
            "population-history coarse grid differs")
    for row in scale["curve"]:
        require(set(row) == {"exponent", "population_exponent", "variance", "lambda", "objective", "phase", "error",
                            "equation_relative_residual"}
            and type(row["exponent"]) in (int, float) and -8 <= row["exponent"] <= 0
            and type(row["population_exponent"]) in (int, float) and 0 <= row["population_exponent"] <= 8
            and row["variance"] == 10. ** row["exponent"] and row["lambda"] == 10. ** row["population_exponent"] - 1
            and row["phase"] in ("coarse", "boundary_coarse", "boundary_refinement", "refinement",
                                  "independent_recheck", "quarter_step", "tightened_refinement")
            and ((row["objective"] is None and isinstance(row["error"], str) and bool(row["error"]))
                 or (row["error"] is None and type(row["objective"]) in (int, float)
                     and math.isfinite(row["objective"]) and type(row["equation_relative_residual"]) in (int, float)
                     and 0 <= row["equation_relative_residual"] <= 1e-8)),
            "population-history scale evaluation is invalid")
    finite = [row for row in coarse if row["objective"] is not None]
    require(bool(finite) and original["best_coarse"] == min(finite, key=_population_scale_key),
            "population-history best coarse point differs")
    best = original["best_coarse"]
    bounds = [[max(-8., best["exponent"] - .5), min(0., best["exponent"] + .5)],
              [max(0., best["population_exponent"] - .5), min(8., best["population_exponent"] + .5)]]
    refinement = original["refinement"]
    refined = [row for row in curve if row["phase"] == "refinement"]
    require(set(refinement) == {"bounds", "success", "message", "evaluations", "coordinates", "xtol", "ftol", "maxfev"}
        and refinement["bounds"] == bounds and refinement["xtol"] == 1e-4 and refinement["ftol"] == 1e-10
        and refinement["maxfev"] == 160 and type(refinement["success"]) is bool
        and refinement["evaluations"] == len(refined) <= 160
        and all(bounds[0][0] <= row["exponent"] <= bounds[0][1]
                and bounds[1][0] <= row["population_exponent"] <= bounds[1][1] for row in refined),
        "population-history bounded refinement differs")
    boundary_problem = _ScaleProblem(problem.H, problem.score, problem.response_energy, problem.historical_mean,
        problem.base_covariance, problem.innovation_indices, None, response_rank=problem.score.shape[1])
    _validate_pooling_scale(original["boundary"], boundary_problem, previous)
    translated = [dict(exponent=row["exponent"], population_exponent=0., variance=row["variance"],
        **{"lambda": 0.}, objective=row.get("band_objective"), phase="boundary_" + row["phase"],
        error=row["error"], equation_relative_residual=row["equation_relative_residual"])
        for row in original["boundary"]["curve"]]
    require([row for row in curve if row["phase"].startswith("boundary_")] == translated,
            "population-history zero-lambda boundary translation differs")
    require(original["selected"] == min((row for row in curve if row["objective"] is not None), key=_population_scale_key),
            "population-history selected point is not the finite objective minimum")
    reasons = []
    if original["selected"]["exponent"] in (-8., 0.):
        reasons.append("variance_endpoint_winner")
    if original["selected"]["population_exponent"] == 8.:
        reasons.append("population_upper_endpoint_winner")
    if not refinement["success"]:
        reasons.append("refinement_failed")
    if any(row["objective"] is None for row in refined):
        reasons.append("nonfinite_refinement")
    inherited = previous.scale["status"] == "scale_unresolved"
    require(original["own_reasons"] == reasons and original["inherited_limitation"] is inherited
        and original["status"] == ("scale_unresolved" if reasons or inherited else "resolved"),
        "population-history dropped an original numerical limitation")
    if original is not scale:
        require(set(scale) == set(original) | {"numerical_original_scale"}
                and scale["curve"][:len(curve)] == curve
                and all(scale[key] == original[key] for key in original if key not in ("curve", "selected")),
                "population-history probe changed the original search policy")
    require(scale["selected"] == min((row for row in scale["curve"] if row["objective"] is not None), key=_population_scale_key),
            "population-history probe selected an unevaluated point")
    chosen = scale["selected"]
    value = problem.objective((chosen["exponent"], chosen["population_exponent"]), "saved_state_recheck")
    require(math.isfinite(value) and math.isclose(value, chosen["objective"], rel_tol=1e-10, abs_tol=1e-10),
            "population-history selected full marginal objective differs")


def _validate_regularization_state(state, population, previous, basis, shared):
    players, H, T, xbar, u = _annual_inputs(population, previous)
    require(state.representation == "graph_40ft" and isinstance(state.shape, GraphShapeState)
        and state.prior_policy in ("history", "population_history") and state.basis is not None
        and state.basis.sha256 == basis.sha256 and state.season == population.season
        and state.season_index == population.season_index and state.benchmark == population.benchmark == "unblocked_spatial"
        and state.source_protocol_sha256 == population.protocol_sha256 and state.population_id == population.population_id
        and state.player_ids == players and state.current_player_ids == population.player_ids
        and state.entrant_ids == tuple(player for player in population.player_ids
                                      if previous is None or player not in previous.player_ids)
        and state.carried_only_ids == tuple(player for player in players if player not in population.player_ids)
        and state.r == population.r and np.array_equal(state.u, u) and np.array_equal(state.p, basis.p)
        and np.array_equal(state.p, population.p) and np.array_equal(state.response_counts, population.response_counts)
        and state.volume.diagnostics.get("population_sha256") == annual_input_identity(population)
        and (previous is None or (previous.prior_policy == state.prior_policy
            and previous.model_protocol_sha256 == state.model_protocol_sha256
            and previous.representation == state.representation and previous.basis.sha256 == basis.sha256)),
        "regularization annual source, model, player, reference or chronology differs")
    if state.prior_policy == "population_history":
        require(shared is not None and shared.prior_policy == "history" and shared.representation == "graph_40ft"
            and shared.season == state.season and shared.season_index == state.season_index
            and shared.source_protocol_sha256 == state.source_protocol_sha256 and shared.population_id == state.population_id
            and shared.player_ids == state.player_ids and shared.current_player_ids == state.current_player_ids
            and np.array_equal(shared.u, state.u) and np.array_equal(shared.p, state.p)
            and np.array_equal(shared.response_counts, state.response_counts)
            and all(np.array_equal(getattr(state.volume, field), getattr(shared.volume, field))
                    for field in ("M", "V", "A", "prior_mean", "prior_covariance"))
            and all(getattr(state.volume, field) == getattr(shared.volume, field)
                    for field in ("a", "q", "scale", "diagnostics")),
            "regularization candidate shared control volume differs")
    else:
        require(shared is None, "regularization history control cannot have a shared volume")
    Th = T - T.sum(axis=1, keepdims=True) * population.p
    yh = population.ybar - population.ybar.sum(axis=1, keepdims=True) * population.p
    for name, width, score in (("volume", 1, T.sum(axis=1, keepdims=True)), ("shape", 40, Th @ basis.B)):
        block = getattr(state, name)
        prior = None if previous is None else getattr(previous, name)
        M0, base, indices = _prior(players, previous, prior, width)
        variance = block.scale["selected"]["variance"]
        require(type(variance) in (int, float) and 1e-8 <= variance <= 1
            and block.a == (variance if prior is None else prior.a)
            and block.q == (None if prior is None else variance), "regularization annual variance lineage differs")
        historical_covariance = base.copy()
        historical_covariance[indices, indices] += variance
        if name == "shape" and state.prior_policy == "population_history":
            require(np.array_equal(block.historical_prior_mean, M0)
                    and np.array_equal(block.historical_prior_covariance, historical_covariance),
                    "regularization historical prior differs from this arm's previous state")
            if previous is None:
                require(block.scale == _initial_population_scale(shared.shape.scale)
                    and all(np.array_equal(getattr(block, field), getattr(shared.shape, field))
                            for field in ("Theta", "V", "A", "prior_mean", "prior_covariance")),
                    "regularization initial shape was not the unchanged control solve")
                mean, covariance = M0, historical_covariance
            else:
                problem = _PopulationScaleProblem(H, score, population.shape_yy, M0, base, indices)
                _validate_population_scale(block.scale, problem, prior)
                mean, covariance, _, _ = problem.priors(variance, block.scale["selected"]["lambda"])
        else:
            problem = _ScaleProblem(H, score, population.yy if name == "volume" else population.shape_yy,
                M0, base, indices, None if name == "volume" else population.p,
                basis=None if name == "volume" else basis)
            _validate_pooling_scale(block.scale, problem, prior)
            mean, covariance = M0, historical_covariance
            if name == "shape":
                require((block.historical_prior_mean is None or np.array_equal(block.historical_prior_mean, M0))
                    and (block.historical_prior_covariance is None
                         or np.array_equal(block.historical_prior_covariance, covariance)),
                    "history control historical and effective priors differ")
        require(np.array_equal(block.prior_mean, mean) and np.array_equal(block.prior_covariance, covariance),
                "regularization effective prior differs")
        posterior = fixed_shape_update(H, mean, covariance, score, u)
        context = (population.ybar.sum(axis=1, keepdims=True) if name == "volume" else yh) - xbar @ (
            posterior.mean if name == "volume" else posterior.mean @ basis.R.T)
        require(np.allclose(_coefficient_mean(block), posterior.mean, rtol=1e-10, atol=1e-12)
            and np.allclose(block.V, posterior.covariance, rtol=1e-10, atol=1e-12)
            and np.allclose(block.A, context, rtol=1e-10, atol=1e-12),
            "regularization posterior, full covariance or native context equation differs")


def _validate_regularization_parents(document, previous, shared_volume):
    if previous is not None:
        reference, state = previous
        parent = read_artifact(linked_path(reference), "attribution_regularization_annual", expected_schema=5)
        require(all(parent[name] == document[name] for name in
                ("prepared", "protocol", "source", "statistics", "basis", "family", "population", "law", "outer",
                 "prior_policy", "representation", "model_protocol_sha256", "source_protocol_sha256"))
            and parent["season"] == state.season and parent["season_index"] == state.season_index
            and parent["season_index"] + 1 == document["season_index"]
            and parent["numerical_probe"] is None
            and parent["player_ids"] == list(state.player_ids)
            and parent["volume"] == {field: getattr(state.volume, field) for field in ("a", "q", "scale", "diagnostics")}
            and parent["shape"] == {field: getattr(state.shape, field) for field in ("a", "q", "scale", "diagnostics")},
            "regularization previous annual reference is not this arm's immediately preceding evidence")
    if shared_volume is not None:
        reference, state = shared_volume
        # the caller selects the frozen or new decoder; this only binds its
        # explicitly supplied result to the referenced annual metadata.
        shared = read_json(linked_path(reference))
        require(shared["representation"] == "graph_40ft" and shared["population"] == document["population"]
            and shared["law"] == document["law"] and shared["outer"] == document["outer"]
            and shared["season"] == document["season"] and shared["season_index"] == document["season_index"]
            and shared["response_sha256"] == document["response_sha256"]
            and shared["annual_input_sha256"] == document["annual_input_sha256"]
            and shared["statistics"] == document["statistics"] and shared["basis"] == document["basis"]
            and shared["player_ids"] == list(state.player_ids)
            and shared["volume"] == document["volume"]
            and state.prior_policy == "history"
            and (state.model_protocol_sha256 != document["model_protocol_sha256"]
                 or (shared["prepared"] == document["prepared"] and shared["prior_policy"] == "history")),
            "regularization shared-control annual reference changed its response, statistics or volume")


def write_regularization_annual(
    state: AnnualState, out: Path | str, *, population: RevisionPopulation, basis: ShapeBasis,
    prepared: dict, protocol: dict, source: dict, statistics: dict, basis_reference: dict,
    previous: tuple[dict, AnnualState] | None, shared_volume: tuple[dict, AnnualState] | None,
    family: str, population_name: str, law: str, outer: int, response_sha256: str, purpose: str,
    numerical_probe: dict | None = None,
) -> dict:
    """write one schema-5 solve; source controls remain explicit schema-4 references."""
    prior = None if previous is None else previous[1]
    shared = None if shared_volume is None else shared_volume[1]
    _validate_regularization_state(state, population, prior, basis, shared)
    require(state.model_protocol_sha256 == protocol["sha256"] and family in ("paired", "independent")
            and population_name in ("sparse", "diffuse", "null") and law in ("gaussian", "game_pace")
            and not (family == "independent" and population_name == "null") and type(outer) is int and 0 <= outer < 200,
            "regularization annual case or model identity differs")
    digest(response_sha256)
    parents = dict(prepared=prepared, protocol=protocol, source=source, statistics=statistics, basis=basis_reference,
        previous=None if previous is None else previous[0], shared_volume=None if shared_volume is None else shared_volume[0])
    for reference in parents.values():
        if reference is not None:
            linked_path(reference)
    protocol_document = read_artifact(linked_path(protocol), "attribution_regularization_protocol", expected_schema=5)
    require(protocol_document["purpose"] == purpose, "regularization annual purpose differs from its protocol")
    output = output_path(str(out), [])
    require(output.is_relative_to(Path(protocol_document["output_root"]).resolve())
        and (purpose != "research" or output.is_relative_to(Path("/Volumes/Expansion/hockey-stats/runs"))),
        "regularization annual output differs from the frozen root")
    blocks, values = annual_arrays(state)
    values["shape_historical_prior_mean"] = state.shape.prior_mean if state.shape.historical_prior_mean is None else state.shape.historical_prior_mean
    values["shape_historical_prior_covariance"] = state.shape.prior_covariance if state.shape.historical_prior_covariance is None else state.shape.historical_prior_covariance
    historical = ordered_array_digest(dict(mean=values["shape_historical_prior_mean"], covariance=values["shape_historical_prior_covariance"]))
    effective = ordered_array_digest(dict(mean=state.shape.prior_mean, covariance=state.shape.prior_covariance))
    if numerical_probe is not None:
        require("original_annual" in numerical_probe, "saved numerical alternatives require the original annual reference")
        validate_regularization_probe(numerical_probe, state)
    require((numerical_probe is not None) == ("numerical_original_scale" in state.shape.scale),
            "regularization numerical alternative must retain its probe receipt")
    output.mkdir()
    arrays = write_arrays(output, "state.npz", values)
    document = artifact("attribution_regularization_annual", purpose, parents, schema_version=5,
        **parents, source_kind="synthetic", source_protocol_sha256=state.source_protocol_sha256,
        model_protocol_sha256=state.model_protocol_sha256, prior_policy=state.prior_policy,
        representation="graph_40ft", basis_sha256=basis.sha256, family=family, population=population_name,
        law=law, outer=outer, benchmark=state.benchmark, season=state.season, season_index=state.season_index,
        population_id=state.population_id, player_ids=state.player_ids, current_player_ids=state.current_player_ids,
        entrant_ids=state.entrant_ids, carried_only_ids=state.carried_only_ids, r=state.r, strata=population.strata,
        response_sha256=response_sha256, annual_input_sha256=annual_input_identity(population),
        historical_prior_sha256=historical, effective_prior_sha256=effective,
        volume=blocks["volume"], shape=blocks["shape"], numerical_probe=numerical_probe,
        units=REGULARIZATION_UNITS, admission="not_admitted", handoff=None, **arrays)
    _validate_regularization_parents(document, previous, shared_volume)
    require(purpose != "research" or document["implementation"] == protocol_document["implementation"],
            "regularization annual producer differs from its frozen protocol")
    write_json(output / "annual.json", document)
    return identity(output / "annual.json")


def read_regularization_annual(
    path: Path | str, *, population: RevisionPopulation, basis: ShapeBasis, prepared: dict, protocol: dict,
    source: dict, statistics: dict, basis_reference: dict, previous: tuple[dict, AnnualState] | None,
    shared_volume: tuple[dict, AnnualState] | None,
) -> AnnualState:
    """decode only schema 5 against caller-selected evidence and same-arm parents."""
    document = read_artifact(path, "attribution_regularization_annual", expected_schema=5)
    parents = dict(prepared=prepared, protocol=protocol, source=source, statistics=statistics, basis=basis_reference,
        previous=None if previous is None else previous[0], shared_volume=None if shared_volume is None else shared_volume[0])
    require(document["consumed"] == parents and all(document[name] == reference for name, reference in parents.items())
        and document["source_kind"] == "synthetic" and document["representation"] == "graph_40ft"
        and document["model_protocol_sha256"] == protocol["sha256"] and document["basis_sha256"] == basis.sha256
        and document["admission"] == "not_admitted" and document["handoff"] is None
        and document["units"] == REGULARIZATION_UNITS and document["annual_input_sha256"] == annual_input_identity(population)
        and document["strata"] == list(map(list, population.strata)), "regularization annual evidence binding differs")
    for reference in parents.values():
        if reference is not None:
            linked_path(reference)
    protocol_document = read_artifact(linked_path(protocol), "attribution_regularization_protocol", expected_schema=5)
    require(document["purpose"] == protocol_document["purpose"]
        and (document["purpose"] != "research" or document["implementation"] == protocol_document["implementation"]),
        "regularization annual producer differs from protocol")
    digest(document["response_sha256"])
    require(document["family"] in ("paired", "independent") and document["population"] in ("sparse", "diffuse", "null")
        and document["law"] in ("gaussian", "game_pace") and type(document["outer"]) is int and 0 <= document["outer"] < 200
        and not (document["family"] == "independent" and document["population"] == "null"),
        "regularization annual case differs")
    n, s = len(document["player_ids"]), len(population.strata)
    shapes = dict(u=(n,), response_counts=(656,), p=(656,), volume_M=(2*n, 1), volume_V=(2*n, 2*n),
        volume_A=(s, 1), volume_prior_mean=(2*n, 1), volume_prior_covariance=(2*n, 2*n),
        shape_Theta=(2*n, 40), shape_V=(2*n, 2*n), shape_A=(s, 656), shape_prior_mean=(2*n, 40),
        shape_prior_covariance=(2*n, 2*n), shape_historical_prior_mean=(2*n, 40),
        shape_historical_prior_covariance=(2*n, 2*n))
    values = load_arrays(document)
    require(list(values) == list(shapes) and all(values[name].shape == shape and values[name].dtype == np.dtype("float64")
        for name, shape in shapes.items()), "regularization annual array names/order/dtypes differ")
    blocks = {}
    for name in ("volume", "shape"):
        require(set(document[name]) == {"a", "q", "scale", "diagnostics"}, "regularization annual block fields differ")
        fields = {field: document[name][field] for field in ("a", "q", "scale", "diagnostics")}
        fields.update({field: values[name + "_" + field] for field in ("V", "A", "prior_mean", "prior_covariance")})
        blocks[name] = BlockState(values["volume_M"], **fields) if name == "volume" else GraphShapeState(
            values["shape_Theta"], **fields, historical_prior_mean=values["shape_historical_prior_mean"],
            historical_prior_covariance=values["shape_historical_prior_covariance"])
    state = AnnualState(document["benchmark"], document["season"], document["season_index"],
        document["source_protocol_sha256"], document["model_protocol_sha256"], "graph_40ft", basis,
        document["population_id"], tuple(document["player_ids"]), tuple(document["current_player_ids"]),
        tuple(document["entrant_ids"]), tuple(document["carried_only_ids"]), blocks["volume"], blocks["shape"],
        document["r"], values["u"], values["p"], values["response_counts"], document["prior_policy"])
    _validate_regularization_state(state, population, None if previous is None else previous[1], basis,
                                   None if shared_volume is None else shared_volume[1])
    _validate_regularization_parents(document, previous, shared_volume)
    require(document["historical_prior_sha256"] == ordered_array_digest(dict(mean=state.shape.historical_prior_mean,
        covariance=state.shape.historical_prior_covariance))
        and document["effective_prior_sha256"] == ordered_array_digest(dict(mean=state.shape.prior_mean,
        covariance=state.shape.prior_covariance)), "regularization annual prior identities differ")
    if document["numerical_probe"] is not None:
        validate_regularization_probe(document["numerical_probe"], state)
    require((document["numerical_probe"] is not None) == ("numerical_original_scale" in state.shape.scale),
            "regularization annual numerical alternative lost its receipt")
    if shared_volume is not None:
        state = replace(state, volume=shared_volume[1].volume)
    for array in (state.volume.M, state.volume.V, state.volume.A, state.volume.prior_mean, state.volume.prior_covariance):
        array.setflags(write=False)
    return state


def read_recovery_embedded_annual(
    record: dict, arrays: dict[str, np.ndarray], *,
    representation: Literal["native_04b", "graph_40ft"], basis: ShapeBasis | None,
    source_prepared: dict, source_protocol: dict, model_protocol: dict, basis_reference: dict | None,
    population_id: str, season_index: int, season: str, current_player_ids: tuple[int, ...],
    current_u: np.ndarray, p: np.ndarray, strata: tuple, previous: AnnualState | None,
) -> AnnualState:
    """decode one explicitly synthetic schema-3 row from an already loaded outer.

    the caller validates the enclosing artifact and referenced files once. this
    boundary checks its complete reference bindings, saved array order and exact
    annual prior carry; it never reads a standalone annual or guesses a format.
    """
    require(set(record) == {
        "schema_version", "kind", "representation", "source_kind", "season", "season_index",
        "benchmark", "source_prepared", "source_protocol", "model_protocol", "population_id",
        "basis", "basis_sha256", "player_ids", "current_player_ids", "entrant_ids",
        "carried_only_ids", "previous", "array_prefix", "r", "strata", "volume", "shape",
    } and type(record["schema_version"]) is int and record["schema_version"] == 3
            and record["kind"] == "attribution_recovery_annual" and record["source_kind"] == "synthetic"
            and record["representation"] == representation
            and record["benchmark"] == "unblocked_spatial"
            and record["source_prepared"] == source_prepared
            and record["source_protocol"] == source_protocol and record["model_protocol"] == model_protocol
            and record["population_id"] == population_id
            and type(season_index) is int and season_index >= 0
            and type(record["season_index"]) is int and record["season_index"] == season_index
            and record["season"] == season
            and len(season) == 8 and season.isdigit() and int(season[4:]) == int(season[:4]) + 1
            and record["r"] == 40 and tuple(map(tuple, record["strata"])) == tuple(map(tuple, strata)),
            "embedded recovery annual source/model identity differs")
    graph = representation == "graph_40ft"
    require((graph and basis is not None and record["basis"] == basis_reference
             and basis_reference is not None and record["basis_sha256"] == basis.sha256
             and basis.B.shape == (656, 40) and np.array_equal(basis.p, p))
            or (representation == "native_04b" and basis is None and basis_reference is None
                and record["basis"] is None and record["basis_sha256"] is None),
            "embedded recovery annual representation/basis differs")
    current = tuple(record["current_player_ids"])
    players = tuple(record["player_ids"])
    prior_players = () if previous is None else previous.player_ids
    require(bool(current) and current == current_player_ids == tuple(sorted(set(current)))
            and players == tuple(sorted(set(players)))
            and all(type(player) is int for player in (*players, *current,
                                                     *record["entrant_ids"], *record["carried_only_ids"]))
            and players == tuple(sorted(set(current) | set(prior_players)))
            and record["entrant_ids"] == sorted(set(current) - set(prior_players))
            and record["carried_only_ids"] == sorted(set(players) - set(current))
            and ((previous is None and season_index == 0 and record["previous"] is None)
                 or (previous is not None and season_index == previous.season_index + 1
                     and int(season[:4]) == int(previous.season[:4]) + 1
                     and record["previous"] == dict(representation=representation, season=previous.season)
                     and previous.benchmark == record["benchmark"]
                     and previous.source_protocol_sha256 == source_protocol["sha256"]
                     and previous.model_protocol_sha256 == model_protocol["sha256"]
                     and previous.population_id == population_id and previous.representation == representation
                     and np.array_equal(previous.p, p)
                     and ((basis is None and previous.basis is None)
                          or (basis is not None and previous.basis is not None
                              and basis.sha256 == previous.basis.sha256)))),
            "embedded recovery annual row order or chronology differs")
    n, s = len(players), len(strata)
    positions = {player: i for i, player in enumerate(players)}
    u = np.zeros(n)
    require(current_u.shape == (len(current),) and np.isfinite(current_u).all() and np.all(current_u > 0)
            and abs(float(current_u.sum()) - 1) <= 1e-12
            and p.shape == (656,) and np.isfinite(p).all() and np.all(p > 0)
            and abs(float(p.sum()) - 1) <= 1e-12,
            "embedded recovery annual original references differ")
    u[[positions[player] for player in current]] = current_u
    prefix = representation + "_" + season + "_"
    shapes = dict(u=(n,), response_counts=(656,), p=(656,))
    for name in ("volume", "shape"):
        width = 1 if name == "volume" else (40 if graph else 656)
        mean_name = "Theta" if name == "shape" and graph else "M"
        shapes[name + "_" + mean_name] = (2 * n, width)
        shapes[name + "_V"] = (2 * n, 2 * n)
        shapes[name + "_A"] = (s, 1 if name == "volume" else 656)
        shapes[name + "_prior_mean"] = (2 * n, width)
        shapes[name + "_prior_covariance"] = (2 * n, 2 * n)
    names = [prefix + name for name in shapes]
    require(record["array_prefix"] == prefix
            and [name for name in arrays if name.startswith(prefix)] == names
            and all(arrays[prefix + name].shape == shape and arrays[prefix + name].dtype.kind in "biuf"
                    and np.isfinite(arrays[prefix + name]).all() for name, shape in shapes.items())
            and np.array_equal(arrays[prefix + "u"], u) and np.array_equal(arrays[prefix + "p"], p),
            "embedded recovery annual ordered arrays or references differ")
    blocks = {}
    for name in ("volume", "shape"):
        metadata = record[name]
        require(isinstance(metadata, dict) and set(metadata) == {"a", "q", "scale", "diagnostics"},
                "embedded recovery annual block metadata differs")
        prior = None if previous is None else getattr(previous, name)
        width = 1 if name == "volume" else (40 if graph else 656)
        M0, covariance, selected = _prior(players, previous, prior, width)
        variance = metadata["scale"]["selected"]["variance"]
        require(math.isfinite(variance) and 1e-8 <= variance <= 1
                and metadata["a"] == (variance if prior is None else prior.a)
                and metadata["q"] == (None if prior is None else variance),
                "embedded recovery annual scale lineage differs")
        covariance[selected, selected] += variance
        block_prefix = prefix + name + "_"
        require(np.array_equal(arrays[block_prefix + "prior_mean"], M0)
                and np.array_equal(arrays[block_prefix + "prior_covariance"], covariance),
                "embedded recovery annual prior carry differs")
        M = arrays[block_prefix + ("Theta" if name == "shape" and graph else "M")]
        V, A = arrays[block_prefix + "V"], arrays[block_prefix + "A"]
        tolerance = metadata["diagnostics"]["covariance_rounding_tolerance"]
        require(math.isfinite(tolerance) and tolerance >= 0
                and np.max(np.abs(V - V.T)) <= tolerance and np.min(np.diag(V)) >= -tolerance
                and np.max(np.abs(u @ M[:n])) <= 1e-8 and np.max(np.abs(u @ M[n:])) <= 1e-8,
                "embedded recovery annual covariance or centering differs")
        if name == "shape":
            native = M @ basis.R.T if graph else M
            require(np.max(np.abs(native.sum(axis=1))) <= 1e-8 and np.max(np.abs(A.sum(axis=1))) <= 1e-8,
                    "embedded recovery annual shape/context is not zero sum")
        state_type = GraphShapeState if name == "shape" and graph else BlockState
        blocks[name] = state_type(M, V, A, M0, covariance, metadata["a"], metadata["q"],
                                  metadata["scale"], metadata["diagnostics"])
    return AnnualState(record["benchmark"], season, season_index, source_protocol["sha256"],
                       model_protocol["sha256"], representation, basis, population_id, players, current,
                       tuple(record["entrant_ids"]), tuple(record["carried_only_ids"]),
                       blocks["volume"], blocks["shape"], 40, u, p, arrays[prefix + "response_counts"], "history")


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
                       values["u"], values.get("p"), values["response_counts"], "history")


def bounded_shape_resolution_check(
    population: RevisionPopulation, previous: AnnualState | None, state: AnnualState,
    *, regions: np.ndarray | None = None,
    projections: tuple[tuple[np.ndarray, np.ndarray, str], ...] = (),
) -> dict:
    """one conditional tightening of the saved shape fit; incoming priors stay fixed."""
    from dataclasses import replace
    from .chance_evaluation import REGION_NAMES, compound_regions
    from .shot_origins import grid

    require(state.shape is not None and population.p is not None
            and state.representation in ("native_04b", "graph_40ft"),
            "one-band shape resolution requires a named native or graph control")
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
    probe = _conditional_scale_probe(problem, saved)
    selected = probe["selected"]
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
    return dict(
        status="verified"
        if probe["numerical_complete"] and max(cell_change, scalar_change, region_change, requested_change) <= 1e-4
        else "withheld",
        scope="conditional_per_fit_fixed_incoming_prior_not_propagated_history_or_coverage_bound",
        saved_winner=probe["saved_winner"],
        rechecked_candidates=probe["rechecked_candidates"],
        tightened_refinement=probe["tightened_refinement"],
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
