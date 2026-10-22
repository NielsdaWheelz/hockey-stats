"""immutable recorded-count evidence and game-local sufficient statistics.

the original preparation and grouped evidence remain read-only. positive game
weights recompute context residualization while original references remain fixed.
active recovery preparation binds its separate model protocol explicitly.
"""

import hashlib
import json
import math
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

import numpy as np
from scipy import sparse

from .artifacts import (
    clean_implementation,
    digest,
    linked_path,
    load_arrays,
    ordered_array_digest,
    require,
)
from .chance_cli import read_json

if TYPE_CHECKING:
    from .attribution import AnnualState, PoolingSource, PoolingStatistics, ShapeBasis, ShapeCoefficientLikelihood

POPULATIONS = ("all_attempts", "unblocked_spatial")
RESEARCH_SEASONS = tuple(f"{year}{year + 1}" for year in range(2021, 2026))
POOLING_STAT_FIELDS = ("H", "T", "yy", "shape_yy", "xbar", "ybar", "stratum_weight", "player_exposure",
                       "response_counts", "u", "p", "r", "player_ids")


class ArtifactReference(TypedDict):
    path: str
    sha256: str


@dataclass(frozen=True)
class DeploymentDesign:
    """response-free annual information in current-player offense/defense order."""

    season: str
    player_ids: tuple[int, ...]
    strata: tuple[tuple, ...]
    H: np.ndarray
    xbar: np.ndarray
    stratum_weight: np.ndarray
    player_exposure: np.ndarray
    u: np.ndarray
    p: np.ndarray
    r: float
    source_refs: dict

    def __post_init__(self):
        n, s = len(self.player_ids), len(self.strata)
        shapes = ((self.H, (2*n, 2*n)), (self.xbar, (s, 2*n)),
                  (self.stratum_weight, (s,)), (self.player_exposure, (n,)),
                  (self.u, (n,)), (self.p, (656,)))
        require(isinstance(self.season, str) and len(self.season) == 8 and self.season.isdigit()
                and int(self.season[4:]) == int(self.season[:4])+1
                and n > 0 and self.player_ids == tuple(sorted(set(self.player_ids)))
                and all(type(player) is int for player in self.player_ids)
                and s > 0 and self.strata == tuple(sorted(set(self.strata)))
                and math.isfinite(self.r) and self.r > 0 and isinstance(self.source_refs, dict)
                and all(isinstance(value, np.ndarray) and value.dtype == np.dtype("float64")
                        and value.shape == shape and np.isfinite(value).all() for value, shape in shapes),
                "deployment design identity, axes or finite float64 arrays differ")
        require(np.all(self.player_exposure > 0) and np.all(self.stratum_weight > 0)
                and np.all(self.u > 0) and abs(float(self.u.sum())-1) <= 1e-12
                and np.allclose(self.u, self.player_exposure/self.player_exposure.sum(), rtol=1e-12, atol=1e-12)
                and np.all(self.p > 0) and abs(float(self.p.sum())-1) <= 1e-12
                and np.allclose(self.H, self.H.T, rtol=1e-10, atol=1e-10)
                and np.allclose(self.xbar[:, :n].sum(axis=1), 5., rtol=0, atol=1e-10)
                and np.allclose(self.xbar[:, n:].sum(axis=1), 5., rtol=0, atol=1e-10),
                "deployment exposure, reference, context means or information differ")


@dataclass(frozen=True)
class GroupedDeploymentDesign:
    """response-free game moments; sparse columns are flattened in c order."""

    game_ids: tuple
    H_e: sparse.csr_matrix
    stratum_x: sparse.csr_matrix
    stratum_e: np.ndarray
    source_refs: dict


def _selected_deployment_arrays(reference: ArtifactReference, shapes: dict,
                                names: tuple[str, ...]) -> dict[str, np.ndarray]:
    """verify the whole archive while decoding only named design members."""
    with np.load(linked_path(reference), allow_pickle=False) as source:
        require(set(source.files) == set(shapes) and set(names).issubset(shapes),
                "deployment archive names differ from bound axes")
        arrays = {name: source[name] for name in names}
    require(all(list(value.shape) == shapes[name] and value.dtype.kind in "biuf"
                and np.isfinite(value).all() for name, value in arrays.items()),
            "selected deployment array shape or finite values differ")
    return arrays


def read_real_deployment_designs(result_ref: ArtifactReference,
                               seasons: tuple[str, ...]) -> tuple[DeploymentDesign, ...]:
    """select corrected real spatial geometry; response/fit references are not followed."""
    result = read_json(linked_path(result_ref))
    require(result["kind"] == "attribution_revision_result" and result["schema_version"] == 2
            and result["purpose"] == "research" and result["completion"] == "complete",
            "real deployment requires the completed corrected revision result")
    clean_implementation(result["implementation"])
    prepared_ref = result["evidence"]["prepared"]
    prepared = read_json(linked_path(prepared_ref))
    require(prepared["kind"] == "attribution_revision_prepared" and prepared["schema_version"] == 2
            and prepared["purpose"] == "research" and tuple(prepared["seasons"]) == tuple(seasons),
            "real deployment preparation differs from selected seasons")
    clean_implementation(prepared["implementation"])
    baseline_ref = prepared["baseline_prepared"]
    baseline = read_json(linked_path(baseline_ref))
    require(baseline["kind"] == "attribution_prepared" and baseline["schema_version"] == 1
            and baseline["purpose"] == "research" and baseline["seasons"] == prepared["seasons"]
            and baseline["design"] == prepared["design"]
            and all(prepared["design"][name] is True for name in
                    ("paired_team_direction_masks", "zero_event_segments", "matched_spatial_exclusion")),
            "real deployment changed corrected source populations or direction masks")
    clean_implementation(baseline["implementation"])
    annual = [row for row in prepared["annual"] if row["population"] == "unblocked_spatial"]
    original = [row for row in baseline["annual"] if row["population"] == "unblocked_spatial"]
    require([row["season"] for row in annual] == list(seasons)
            and [row["season"] for row in original] == list(seasons),
            "real deployment annual spatial inventory differs")
    designs, reference = [], None
    for row, source in zip(annual, original, strict=True):
        require(all(row[name] == value for name, value in source.items())
                and row["status"] == "prepared" and row["reason"] is None
                and type(row["row_count"]) is int and row["row_count"] > 0,
                "real deployment changed corrected annual identity or coverage")
        statistics = _selected_deployment_arrays(row["statistics"], row["statistic_shapes"],
                                                ("H", "xbar", "stratum_weight"))
        references = _selected_deployment_arrays(row["references"], row["reference_shapes"],
                                               ("u", "player_exposure", "p"))
        p = references["p"]
        if reference is None:
            reference = p
        require(np.array_equal(p, reference), "real annual deployment native references differ")
        design = DeploymentDesign(row["season"], tuple(row["players"]), tuple(map(tuple, row["strata"])),
            statistics["H"], statistics["xbar"], statistics["stratum_weight"],
            references["player_exposure"], references["u"], p, row["r"],
            dict(result=result_ref, prepared=prepared_ref, baseline_prepared=baseline_ref,
                 statistics=row["statistics"], references=row["references"], row_count=row["row_count"],
                 coverage=row["coverage"], masks=prepared["design"], team_seconds=row["team_seconds"],
                 population_id=prepared["population_ids"]["unblocked_spatial"]))
        deployment_accounting(design)
        designs.append(design)
    return tuple(designs)


def read_grouped_deployment_design(design: DeploymentDesign) -> GroupedDeploymentDesign:
    """verify the selected archive and decode only its three design moments."""
    prepared = read_json(linked_path(design.source_refs["prepared"]))
    matches = [row for row in prepared["annual"]
               if row["population"] == "unblocked_spatial" and row["season"] == design.season]
    require(len(matches) == 1, "grouped deployment annual identity is unavailable")
    annual = matches[0]
    require(annual["status"] == "prepared" and annual["reason"] is None
            and tuple(annual["players"]) == design.player_ids
            and tuple(map(tuple, annual["strata"])) == design.strata
            and annual["r"] == design.r and annual["statistics"] == design.source_refs["statistics"]
            and annual["references"] == design.source_refs["references"],
            "grouped deployment changed its selected annual design")
    names = ("H_e_data", "H_e_indices", "H_e_indptr", "stratum_x_data",
             "stratum_x_indices", "stratum_x_indptr", "stratum_e")
    arrays = _selected_deployment_arrays(annual["grouped"], annual["grouped_shapes"], names)
    g, n, s = len(annual["game_ids"]), 2*len(design.player_ids), len(design.strata)
    matrices = {}
    for name, width in (("H_e", n*n), ("stratum_x", s*n)):
        data, indices, indptr = (arrays[name+suffix] for suffix in ("_data", "_indices", "_indptr"))
        require(data.dtype == np.dtype("float64") and indices.dtype.kind in "iu"
                and indptr.dtype.kind in "iu" and data.ndim == indices.ndim == indptr.ndim == 1
                and len(data) == len(indices) and indptr.shape == (g+1,)
                and indptr[0] == 0 and indptr[-1] == len(data)
                and np.all(indptr[1:] >= indptr[:-1])
                and np.all((0 <= indices) & (indices < width)),
                "grouped deployment sparse storage differs from its declared axes")
        matrices[name] = sparse.csr_matrix((data, indices, indptr), shape=(g, width))
    grouped = GroupedDeploymentDesign(tuple(annual["game_ids"]), matrices["H_e"],
        matrices["stratum_x"], arrays["stratum_e"],
        dict(prepared=design.source_refs["prepared"], grouped=annual["grouped"], decoded_members=list(names)))
    grouped_deployment_accounting(design, grouped)
    return grouped


def grouped_deployment_accounting(design: DeploymentDesign, grouped: GroupedDeploymentDesign) -> dict:
    """reconcile game exposure and residualization with the selected annual data."""
    g, n, s = len(grouped.game_ids), 2*len(design.player_ids), len(design.strata)
    require(g > 0 and grouped.game_ids == tuple(sorted(set(grouped.game_ids)))
            and sparse.isspmatrix_csr(grouped.H_e) and sparse.isspmatrix_csr(grouped.stratum_x)
            and grouped.H_e.shape == (g, n*n) and grouped.stratum_x.shape == (g, s*n)
            and grouped.H_e.dtype == grouped.stratum_x.dtype == np.dtype("float64")
            and grouped.stratum_e.shape == (g, s) and grouped.stratum_e.dtype == np.dtype("float64")
            and all(np.isfinite(value).all() and np.all(value >= 0) for value in
                    (grouped.H_e.data, grouped.stratum_x.data, grouped.stratum_e)),
            "grouped deployment game inventory, finite moments or axes differ")
    A = np.asarray(grouped.H_e.sum(axis=0)).reshape(n, n)
    context = np.asarray(grouped.stratum_x.sum(axis=0)).reshape(s, n)
    exposure = grouped.stratum_e.sum(axis=0)
    require(np.all(exposure > 0), "grouped deployment context has no exposure")
    xbar = context/exposure[:, None]
    H = design.r*(A-xbar.T @ context)
    errors = dict(information_relative=float(np.linalg.norm(H-design.H)/max(1., np.linalg.norm(design.H))),
        xbar_max_absolute=float(np.max(np.abs(xbar-design.xbar))),
        stratum_weight_relative=float(np.linalg.norm(design.r*exposure-design.stratum_weight)
                                      /max(1., np.linalg.norm(design.stratum_weight))),
        player_exposure_max_absolute=float(np.max(np.abs(3600*np.diag(A)
                                         -np.tile(design.player_exposure, 2)))))
    require(errors["information_relative"] <= 1e-10 and errors["xbar_max_absolute"] <= 1e-10
            and errors["stratum_weight_relative"] <= 1e-10
            and errors["player_exposure_max_absolute"] <= 1e-6,
            "grouped deployment totals differ from annual information, context or exposure")
    return errors


def grouped_deployment_from_rows(design: DeploymentDesign, arrays: dict[str, np.ndarray]
                                 ) -> GroupedDeploymentDesign:
    """contract explicit synthetic rows into the same response-free game boundary."""
    offense, defense, seconds, si, row_games = (arrays[name] for name in
        ("offense", "defense", "seconds", "si", "row_game_ids"))
    n, s, m = 2*len(design.player_ids), len(design.strata), len(seconds)
    columns = np.column_stack((np.searchsorted(design.player_ids, offense),
                               n//2+np.searchsorted(design.player_ids, defense)))
    X = sparse.csr_matrix((np.ones(columns.size), (np.repeat(np.arange(m), 10), columns.ravel())),
                          shape=(m, n))
    Z = sparse.csr_matrix((np.ones(m), (np.arange(m), si)), shape=(m, s))
    game_ids, moments, context, exposure = tuple(np.unique(row_games).tolist()), [], [], []
    for game in game_ids:
        rows = row_games == game
        e = seconds[rows]/3600
        moments.append((X[rows].T @ X[rows].multiply(e[:, None])).reshape((1, n*n)))
        context.append((Z[rows].T @ X[rows].multiply(e[:, None])).reshape((1, s*n)))
        exposure.append(np.asarray(Z[rows].T @ e).ravel())
    grouped = GroupedDeploymentDesign(game_ids, sparse.vstack(moments, format="csr"),
        sparse.vstack(context, format="csr"), np.asarray(exposure), design.source_refs)
    grouped_deployment_accounting(design, grouped)
    return grouped


def deployment_design_from_rows(*, season: str, player_ids: tuple[int, ...], strata: tuple[tuple, ...],
                                arrays: dict[str, np.ndarray], p: np.ndarray, r: float,
                                source_refs: dict) -> DeploymentDesign:
    """contract paired training rows without responses or a likelihood-fit adapter."""
    offense, defense, seconds, si = (arrays[name] for name in ("offense", "defense", "seconds", "si"))
    row_games, m, n = arrays["row_game_ids"], len(seconds), len(player_ids)
    require(n > 0 and player_ids == tuple(sorted(set(player_ids)))
            and all(type(player) is int for player in player_ids)
            and bool(strata) and strata == tuple(sorted(set(strata)))
            and m > 0 and m % 2 == 0 and offense.shape == defense.shape == (m, 5)
            and offense.dtype == defense.dtype == si.dtype == row_games.dtype == np.dtype("int64")
            and seconds.shape == si.shape == row_games.shape == (m,)
            and seconds.dtype == np.dtype("float64") and np.isfinite(seconds).all()
            and np.all(seconds > 0) and np.array_equal(seconds, np.rint(seconds))
            and np.all((0 <= si) & (si < len(strata)))
            and np.all(row_games[1:] >= row_games[:-1])
            and tuple(np.unique(np.r_[offense.ravel(), defense.ravel()]).tolist()) == player_ids
            and np.all(np.diff(np.sort(offense, axis=1), axis=1) > 0)
            and np.all(np.diff(np.sort(defense, axis=1), axis=1) > 0)
            and not np.any(offense[:, :, None] == defense[:, None, :])
            and np.array_equal(offense[::2], defense[1::2])
            and np.array_equal(defense[::2], offense[1::2])
            and np.array_equal(seconds[::2], seconds[1::2])
            and np.array_equal(row_games[::2], row_games[1::2]),
            "deployment rows changed paired direction, integral duration, player or context axes")
    columns = np.column_stack((np.searchsorted(player_ids, offense), n+np.searchsorted(player_ids, defense)))
    X = sparse.csr_matrix((np.ones(columns.size), (np.repeat(np.arange(m), 10), columns.ravel())),
                          shape=(m, 2*n))
    exposure = np.asarray(X.T @ seconds).ravel()
    require(np.array_equal(exposure[:n], arrays["player_exposure"])
            and np.array_equal(exposure[n:], arrays["player_exposure"])
            and np.array_equal(arrays["u"], exposure[:n]/exposure[:n].sum()),
            "deployment rows changed saved exposure or exposure reference")
    weights = r*seconds/3600
    stratum_weight = np.bincount(si, weights=weights, minlength=len(strata))
    require(np.all(stratum_weight > 0), "deployment context has no training exposure")
    Z = sparse.csr_matrix((np.ones(m), (np.arange(m), si)), shape=(m, len(strata)))
    xbar = (Z.T @ X.multiply(weights[:, None])).toarray()/stratum_weight[:, None]
    H = (X.T @ X.multiply(weights[:, None])).toarray()-xbar.T @ (stratum_weight[:, None]*xbar)
    return DeploymentDesign(season, player_ids, strata, H, xbar, stratum_weight,
                            arrays["player_exposure"], arrays["u"], p, r, source_refs)


def read_synthetic_deployment_designs(result_ref: ArtifactReference, seasons: tuple[str, ...],
                                    expected_p: np.ndarray) -> tuple[DeploymentDesign, ...]:
    """follow the selected resolution ancestry to its single original training design."""
    result = _read_selected_artifact(result_ref, "attribution_resolution_result", 5)
    require(result["purpose"] == "research" and result["execution_status"] == "complete"
            and result["numerical_status"] == "verified" and result["prepared"] == result["consumed"]["prepared"],
            "synthetic deployment requires the completed selected resolution result")
    resolution = _read_selected_artifact(result["prepared"], "attribution_resolution_prepared", 5)
    regularization_ref = result["consumed"]["source_result"]
    require(resolution["source_result"] == regularization_ref,
            "synthetic resolution changed its selected regularization source")
    regularization = _read_selected_artifact(regularization_ref, "attribution_regularization_result", 5)
    require(regularization["purpose"] == "research" and regularization["execution_status"] == "complete"
            and regularization["numerical_status"] == "verified"
            and resolution["source_prepared"] == regularization["prepared"],
            "synthetic deployment regularization binding differs")
    selected = _read_selected_artifact(regularization["prepared"], "attribution_regularization_prepared", 5)
    prepared_ref = selected["source_prepared"]
    prepared = _read_selected_artifact(prepared_ref, "attribution_pooling_prepared", 4)
    require(prepared["purpose"] == selected["purpose"] == resolution["purpose"] == "research"
            and tuple(prepared["seasons"]) == tuple(seasons)
            and [row["season"] for row in prepared["years"]] == list(seasons)
            and selected["designs"] == prepared["designs"]["arrays"] and selected["basis"] == prepared["basis"]
            and selected["source_design_sha256"] == prepared["design_sha256"],
            "synthetic deployment changed original design, basis or annual identity")
    digest(prepared["design_sha256"])
    basis_shapes = {row["name"]: row["shape"] for row in prepared["basis_shapes"]}
    p = _selected_deployment_arrays(prepared["basis"], basis_shapes, ("p",))["p"]
    require(np.array_equal(p, expected_p), "synthetic deployment differs from the first-real native reference")
    names = ("offense", "defense", "seconds", "si", "u", "player_exposure", "row_game_ids")
    selected_names = tuple(f"train_{year}_{name}" for year in range(len(seasons)) for name in names)+("centers", "W")
    shapes = {row["name"]: row["shape"] for row in prepared["designs"]["array_shapes"]}
    require(len(shapes) == len(prepared["designs"]["array_shapes"]), "synthetic design member names repeat")
    arrays = _selected_deployment_arrays(prepared["designs"]["arrays"], shapes, selected_names)
    from .attribution_simulation import shape_operators
    from .shot_origins import grid

    require(np.array_equal(arrays["centers"], grid()[0]), "synthetic deployment changed native cell centers")
    shape_operators(arrays["W"])
    training_digest = ordered_array_digest(arrays)
    designs = []
    for year, row in enumerate(prepared["years"]):
        current = {name: arrays[f"train_{year}_{name}"] for name in names}
        source_refs = dict(result=result_ref, resolution_prepared=result["prepared"],
            regularization_result=regularization_ref, regularization_prepared=regularization["prepared"],
            prepared=prepared_ref, designs=prepared["designs"]["arrays"], basis=prepared["basis"],
            full_design_identity=prepared["design_sha256"], selected_training_digest=training_digest,
            row_count=len(current["seconds"]), games=len(np.unique(current["row_game_ids"])),
            coverage=dict(training_deployment_only=True), masks=dict(paired_team_direction_masks=True,
                zero_event_segments=True), population_id="synthetic:training:unblocked_spatial")
        design = deployment_design_from_rows(season=row["season"], player_ids=tuple(row["players"]),
            strata=tuple(map(tuple, row["strata"])), arrays=current, p=p, r=resolution["rate"], source_refs=source_refs)
        deployment_accounting(design)
        designs.append(design)
    return tuple(designs)


def deployment_accounting(design: DeploymentDesign) -> dict:
    """recover checked integer overlap; directed exposure includes both team rows."""
    n = len(design.player_ids)
    seconds = 3600*(design.H+design.xbar.T @ (design.stratum_weight[:, None]*design.xbar))/design.r
    rounded = np.rint(seconds)
    residual = float(np.max(np.abs(seconds-rounded)))
    require(residual <= 1e-6 and np.all(rounded >= 0),
            "deployment overlap does not recover nonnegative integral source seconds")
    seconds = rounded.astype(np.int64)
    same, opponent = seconds[:n, :n], seconds[:n, n:]
    require(np.array_equal(seconds[n:, n:], same) and np.array_equal(same, same.T)
            and np.array_equal(opponent, opponent.T) and np.all(np.diag(opponent) == 0)
            and np.array_equal(seconds[n:, :n], opponent.T)
            and np.array_equal(np.diag(seconds), np.tile(design.player_exposure, 2))
            and np.all(same <= design.player_exposure[:, None])
            and np.all(opponent <= design.player_exposure[:, None])
            and np.array_equal(same.sum(axis=1), 5*design.player_exposure)
            and np.array_equal(opponent.sum(axis=1), 5*design.player_exposure),
            "deployment overlap violates paired-role or player-exposure accounting")
    directed = int(design.player_exposure.sum())/5
    require(directed.is_integer() and int(directed) % 2 == 0
            and math.isclose(float(design.stratum_weight.sum())*3600/design.r, directed,
                             rel_tol=1e-10, abs_tol=1e-10)
            and ("team_seconds" not in design.source_refs or design.source_refs["team_seconds"] == directed),
            "deployment total exposure disagrees with directed team time")
    return dict(same_team_seconds=same, opponent_seconds=opponent,
                directed_team_seconds=int(directed), physical_elapsed_seconds=int(directed)//2,
                reconstruction_residuals=dict(maximum_integer_seconds=residual,
                    total_seconds=abs(float(design.stratum_weight.sum())*3600/design.r-directed)))


def physical_history_information(designs: tuple[DeploymentDesign, ...]) -> tuple:
    """sum annual physical information with separate context nuisance means."""
    require(bool(designs) and all(int(a.season[:4])+1 == int(b.season[:4])
                                for a, b in zip(designs, designs[1:]))
            and all(np.array_equal(design.p, designs[0].p) for design in designs),
            "physical history requires chronological annual designs and one native reference")
    players = tuple(sorted({player for design in designs for player in design.player_ids}))
    positions, n = {player: i for i, player in enumerate(players)}, len(players)
    L, selections = np.zeros((2*n, 2*n)), []
    for design in designs:
        current = np.array([positions[player] for player in design.player_ids])
        columns = np.r_[current, n+current]
        S = np.zeros((len(columns), 2*n))
        S[np.arange(len(columns)), columns] = 1
        L[np.ix_(columns, columns)] += design.H/design.r**2
        selections.append(S)
    return players, tuple(selections), L


@dataclass(frozen=True)
class AnnualReferences:
    """fixed source design and annual references, never reestimated in a refit."""

    benchmark: str
    season: str
    season_index: int
    protocol_sha256: str
    population_id: str
    player_ids: tuple[int, ...]
    strata: tuple[tuple, ...]
    r: float
    u: np.ndarray
    p: np.ndarray | None
    player_exposure: np.ndarray
    response_counts: np.ndarray


@dataclass(frozen=True)
class GroupedPopulation:
    """unresidualized moments; sparse rows are inventory games in ``game_ids``.

    flattened columns use c order. only a weighted contraction materializes a
    global player cross-product; no game stores a dense global hessian.
    membership signatures describe the exact observed same-role row support.
    """

    game_ids: tuple
    H_e: sparse.csr_matrix
    T_raw: sparse.csr_matrix
    stratum_e: np.ndarray
    stratum_x: sparse.csr_matrix
    stratum_n: sparse.csr_matrix
    Q_t: np.ndarray | None
    Q_h: np.ndarray | None
    membership_signatures: tuple[str, ...]
    row_count: int
    correction_identity: dict | None = None


@dataclass(frozen=True)
class RevisionPopulation:
    """one residualized weighted annual likelihood with fixed references."""

    benchmark: str
    season: str
    season_index: int
    protocol_sha256: str
    population_id: str
    player_ids: tuple[int, ...]
    strata: tuple[tuple, ...]
    H: np.ndarray
    T: np.ndarray
    yy: float
    shape_yy: float | None
    r: float
    xbar: np.ndarray
    ybar: np.ndarray
    stratum_weight: np.ndarray
    player_exposure: np.ndarray
    response_counts: np.ndarray
    u: np.ndarray
    p: np.ndarray | None


@dataclass(frozen=True)
class PooledShapeLikelihood:
    """constant identity effects with separately residualized annual contexts."""

    player_ids: tuple[int, ...]
    current_player_ids: tuple[int, ...]
    selections: tuple[np.ndarray, ...]
    target_selection: np.ndarray
    H: np.ndarray
    score: np.ndarray
    r: float
    p: np.ndarray
    u: np.ndarray
    B: np.ndarray
    R: np.ndarray
    basis_columns: tuple[int, ...]
    target: RevisionPopulation
    source_identity: dict


def pool_shape_likelihood(
    populations: tuple[RevisionPopulation, ...], basis: "ShapeBasis",
    columns: tuple[int, ...], target_season: str,
) -> PooledShapeLikelihood:
    """align physical identities before summing native annual shape scores."""
    populations, columns = tuple(populations), tuple(columns)
    require(bool(populations) and bool(columns)
            and columns == tuple(sorted(set(columns)))
            and all(type(column) is int and 0 <= column < basis.B.shape[1] for column in columns)
            and target_season == populations[-1].season
            and all(current.season_index + 1 == following.season_index
                    and int(current.season[:4]) + 1 == int(following.season[:4])
                    for current, following in zip(populations, populations[1:])),
            "pooled shape requires chronological annual likelihoods and explicit saved columns")
    first, target = populations[0], populations[-1]
    require(first.p is not None and np.array_equal(first.p, basis.p)
            and basis.B.shape == (656, 40) and basis.p.shape == (656,)
            and np.isfinite(basis.B).all() and np.all(basis.p > 0)
            and abs(float(basis.p.sum()) - 1) <= 1e-12,
            "pooled shape basis or native reference differs")
    players = tuple(sorted({player for population in populations for player in population.player_ids}))
    positions, n = {player: i for i, player in enumerate(players)}, len(players)
    B = basis.B[:, columns]
    H, score, selections = np.zeros((2*n, 2*n)), np.zeros((2*n, len(columns))), []
    identities = []
    for population in populations:
        current, m = population.player_ids, len(population.player_ids)
        require(m > 0 and len(set(current)) == m and all(type(player) is int for player in current)
                and population.benchmark == "unblocked_spatial" and population.r == first.r
                and population.protocol_sha256 == first.protocol_sha256
                and population.population_id == first.population_id and np.array_equal(population.p, basis.p)
                and population.H.shape == (2*m, 2*m) and population.T.shape == (2*m, 656)
                and population.xbar.shape == (len(population.strata), 2*m)
                and population.ybar.shape == (len(population.strata), 656)
                and population.u.shape == (m,)
                and all(np.isfinite(value).all() for value in
                        (population.H, population.T, population.xbar, population.ybar, population.u))
                and np.allclose(population.H, population.H.T, rtol=1e-10, atol=1e-10),
                "pooled shape annual identity, reference or moments differ")
        S = np.zeros((2*m, 2*n))
        rows = np.array([positions[player] for player in current])
        S[np.arange(2*m), np.r_[rows, n+rows]] = 1
        T_h = population.T - population.T.sum(axis=1, keepdims=True) * basis.p
        H += S.T @ population.H @ S
        score += S.T @ T_h @ B
        selections.append(S)
        identities.append(dict(season=population.season, population_id=population.population_id,
                               protocol_sha256=population.protocol_sha256,
                               statistics_sha256=statistic_digest(population), player_ids=current))
    u = np.zeros(n)
    u[[positions[player] for player in target.player_ids]] = target.u
    exposure_centering(u)
    likelihood_spectrum(H)
    return PooledShapeLikelihood(players, target.player_ids, tuple(selections), selections[-1],
        H, score, first.r, basis.p, u, B, basis.p[:, None]*B, columns, target,
        dict(annual=identities, basis_sha256=basis.sha256, basis_columns=list(columns),
             target_season=target_season))


def decode_saved_population(
    arrays: dict[str, np.ndarray], *, benchmark: str, season: str, season_index: int,
    source_protocol_sha256: str, population_id: str, player_ids: tuple[int, ...],
    strata: tuple[tuple, ...], expected_p: np.ndarray, expected_r: float,
) -> RevisionPopulation:
    """decode the compact spatial likelihood without inventing response rows."""
    digest(source_protocol_sha256)
    n, s = len(player_ids), len(strata)
    shapes = dict(H=(2*n, 2*n), T=(2*n, 656), yy=(), shape_yy=(), xbar=(s, 2*n), ybar=(s, 656),
                  stratum_weight=(s,), player_exposure=(n,), response_counts=(656,), u=(n,), p=(656,),
                  r=(), player_ids=(n,))
    require(benchmark == "unblocked_spatial" and bool(population_id)
            and type(season_index) is int and season_index >= 0
            and isinstance(season, str) and len(season) == 8 and season.isdigit()
            and int(season[4:]) == int(season[:4]) + 1
            and bool(player_ids) and player_ids == tuple(sorted(set(player_ids)))
            and bool(strata) and strata == tuple(sorted(set(strata)))
            and list(arrays) == list(POOLING_STAT_FIELDS)
            and all(isinstance(arrays[name], np.ndarray) and arrays[name].shape == shape
                    and arrays[name].dtype == np.dtype("int64" if name == "player_ids" else "float64")
                    and np.isfinite(arrays[name]).all()
                    for name, shape in shapes.items()),
            "saved spatial statistic fields, shapes, order or identity differ")
    require(arrays["player_ids"].dtype.kind in "iu"
            and tuple(arrays["player_ids"].tolist()) == player_ids
            and expected_p.shape == (656,) and np.isfinite(expected_p).all()
            and np.all(expected_p > 0) and abs(float(expected_p.sum()) - 1) <= 1e-12
            and np.array_equal(arrays["p"], expected_p)
            and math.isfinite(expected_r) and expected_r > 0 and float(arrays["r"]) == expected_r
            and np.all(arrays["player_exposure"] > 0) and np.all(arrays["stratum_weight"] > 0)
            and np.all(arrays["u"] > 0) and abs(float(arrays["u"].sum()) - 1) <= 1e-12
            and np.allclose(arrays["u"], arrays["player_exposure"] / arrays["player_exposure"].sum(),
                            rtol=1e-12, atol=1e-12)
            and np.allclose(arrays["stratum_weight"] @ arrays["ybar"], arrays["response_counts"],
                            rtol=1e-10, atol=1e-10)
            and np.allclose(arrays["xbar"][:, :n].sum(axis=1), 5., rtol=0, atol=1e-10)
            and np.allclose(arrays["xbar"][:, n:].sum(axis=1), 5., rtol=0, atol=1e-10)
            and np.allclose(arrays["H"], arrays["H"].T, rtol=1e-10, atol=1e-10),
            "saved spatial player order, fixed references or information differ")
    return RevisionPopulation(benchmark, season, season_index, source_protocol_sha256, population_id,
        player_ids, strata, arrays["H"], arrays["T"], float(arrays["yy"]), float(arrays["shape_yy"]),
        expected_r, arrays["xbar"], arrays["ybar"], arrays["stratum_weight"], arrays["player_exposure"],
        arrays["response_counts"], arrays["u"], arrays["p"])


def pooling_population(source: "PoolingSource", statistics: "PoolingStatistics", population: str,
                       law: str, outer: int, season: str) -> RevisionPopulation:
    """decode one bound schema-4 annual likelihood in its original reference/order."""
    prepared = source.prepared
    require(population in ("sparse", "diffuse", "null") and law in ("gaussian", "game_pace")
            and type(outer) is int and 0 <= outer < source.protocol["budgets"]["outer_per_cell"],
            "pooling annual population/law/outer differs")
    require(statistics.prepared_sha256 == source.reference["sha256"]
            and prepared["seasons"] == [row["season"] for row in prepared["years"]]
            and list(statistics.arrays) == [annual["season"] + "_" + name
                                           for annual in prepared["years"] for name in POOLING_STAT_FIELDS],
            "pooling sufficient statistics changed preparation or annual field order")
    years = [row for row in prepared["years"] if row["season"] == season]
    require(len(years) == 1, "pooling annual season absent or duplicated")
    annual = years[0]
    players, strata = tuple(annual["players"]), tuple(map(tuple, annual["strata"]))
    values = {name: statistics.arrays[season + "_" + name] for name in POOLING_STAT_FIELDS}
    return decode_saved_population(values, benchmark="unblocked_spatial", season=season,
        season_index=prepared["seasons"].index(season), source_protocol_sha256=prepared["protocol"]["sha256"],
        population_id=f"synthetic:04e:{population}:{law}:{outer}:unblocked_spatial",
        player_ids=players, strata=strata, expected_p=source.basis.p, expected_r=40.)


@dataclass(frozen=True)
class RegularizationSourceSlice:
    """named 04g evidence; only assessment records retain response references."""

    reference: ArtifactReference
    result: dict
    prepared: dict
    protocol: dict
    context: "PoolingSource"
    basis: "ShapeBasis"
    training: tuple[dict, ...]
    evaluation: tuple[dict, ...]
    W: np.ndarray
    recovery: tuple[np.ndarray, ...]
    records: tuple[dict, ...]
    cells: dict[tuple[str, str, str], dict]
    fixed_populations: tuple[RevisionPopulation, ...]
    consumed: dict
    input_roots: tuple[str, ...]
    inventory: dict


def _read_selected_artifact(reference: ArtifactReference, kind: str, schema: int) -> dict:
    """bind named metadata without traversing unrelated historical consumed links."""
    return _selected_artifact_metadata(read_json(linked_path(reference)), kind, schema)


def _selected_artifact_metadata(document: dict, kind: str, schema: int) -> dict:
    require(isinstance(document, dict) and type(document.get("schema_version")) is int
            and document["schema_version"] == schema and document.get("kind") == kind
            and document.get("purpose") in ("research", "fixture_exercise")
            and isinstance(document.get("consumed"), dict), f"expected schema-{schema} {kind}")
    if document["purpose"] == "research":
        clean_implementation(document["implementation"])
    return document


@dataclass(frozen=True)
class HistoryPrecedingMean:
    """a verified archive's selected mean and metadata, never a reconstructed state."""

    player_ids: tuple[int, ...]
    current_player_ids: tuple[int, ...]
    Theta: np.ndarray
    metadata: dict


@dataclass(frozen=True)
class HistorySourceSlice:
    reference: ArtifactReference
    result: dict
    prepared: dict
    protocol: dict
    assessment: dict
    basis: "ShapeBasis"
    geometry: dict
    final_year: dict
    final_arrays: dict
    cells: tuple[str, ...]
    records: tuple[int, ...]
    fits: dict
    fit_metadata: dict
    consumed: dict
    read_accounting: dict


def _history_selected_arrays(document: dict, names: tuple[str, ...], accounting: dict) -> dict:
    """hash one archive once, then decode only allowlisted complete members."""
    shapes = document["array_shapes"]
    require(isinstance(shapes, list) and len({row["name"] for row in shapes}) == len(shapes)
            and len(set(names)) == len(names) and set(names).issubset(row["name"] for row in shapes),
            "history selected member inventory differs")
    path = linked_path(document["arrays"])
    accounting["verified_bytes"] += path.stat().st_size
    accounting["archive_count"] += 1
    with np.load(path, allow_pickle=False) as archive:
        require(archive.files == [row["name"] for row in shapes], "history archive member order differs")
        arrays = {name: archive[name] for name in names}
    declarations = {row["name"]: row for row in shapes}
    require(all(list(value.shape) == declarations[name]["shape"]
                and value.dtype.str == declarations[name]["dtype"] and value.dtype.kind in "biuf"
                and np.isfinite(value).all() for name, value in arrays.items()),
            "history selected member axes, dtype or finite values differ")
    accounting["decoded_bytes"] += sum(value.nbytes for value in arrays.values())
    accounting["decoded_members"].extend(names)
    return arrays


def read_history_source_slice(result_ref: ArtifactReference | Path | str) -> HistorySourceSlice:
    """bind 04k's finite saved inventory without following generators or old fits."""
    from .attribution import decode_shape_basis, validate_shape_history_identity

    if isinstance(result_ref, (Path, str)):
        from .chance_cli import identity

        result_path = Path(result_ref).resolve(strict=True)
        result_ref = identity(result_path)
        result = _selected_artifact_metadata(read_json(result_path), "attribution_history_result", 1)
    else:
        result = _read_selected_artifact(result_ref, "attribution_history_result", 1)
    purpose = result["purpose"]
    require(result["execution_status"] == "complete" and result["numerical_status"] == "verified"
            and result["study_status"] == ("diagnosed" if purpose == "research" else "fixture_verified")
            and result["nomination"] is None and result["admission"] == "not_admitted"
            and result["handoff"] is None and set(result["consumed"]) == {"prepared", "protocol", "assessment"},
            "history source result is not the completed bound diagnosis")
    refs = result["consumed"]
    if purpose == "research":
        require(result_ref["sha256"] == "88404a3f624f741e316f251f9fa0b928f6850c2460044f66e2ae3322a32d95fa"
                and refs["prepared"]["sha256"] == "9878ef0d199997976327ad5c9ec1e615a956b4bc84458431cc0c85fc57e943cd"
                and refs["protocol"]["sha256"] == "6f72e59b9d8d8e1899b7e1632f09d7c3795e8365b97baffe4070fd2dd6cff5d9"
                and refs["assessment"]["sha256"] == "1275fc420b2eb80dfa936a8f2e95ce3329724598aab5fb6a3f98fa2cb619e96e",
                "research history source differs from the pinned 04k evidence")
    prepared = _read_selected_artifact(refs["prepared"], "attribution_history_prepared", 1)
    protocol = _read_selected_artifact(refs["protocol"], "attribution_history_protocol", 1)
    assessment = _read_selected_artifact(refs["assessment"], "attribution_history_assessment", 1)
    fields = ("sources", "seasons", "years", "basis_sha256", "records", "inventory", "assignments",
              "truth_counts", "partitions", "positivity_lower_bound", "region_names", "factor_checks",
              "geometry_sha256", "budget", "arrays", "array_shapes")
    require(all(document["purpose"] == purpose for document in (prepared, protocol, assessment))
            and prepared["protocol"] == refs["protocol"]
            and all(prepared[name] == protocol[name] for name in fields)
            and prepared["consumed"] == dict(prepared["sources"], protocol=refs["protocol"], geometry=prepared["arrays"])
            and {name: protocol["consumed"][name] for name in prepared["sources"]} == prepared["sources"]
            and assessment["prepared"] == assessment["consumed"]["prepared"] == refs["prepared"]
            and assessment["protocol"] == assessment["consumed"]["protocol"] == refs["protocol"]
            and assessment["execution_status"] == "complete" and assessment["numerical_status"] == "verified"
            and all(result["inventory"][name] == assessment["inventory"][name] for name in assessment["inventory"]),
            "history source purpose, parent or preparation/protocol/assessment binding differs")
    cells = ("gaussian_half", "gaussian_base", "gaussian_double", "gaussian_null", "game_shared_base")
    records = tuple(range(20 if purpose == "research" else 2))
    years = prepared["years"]
    seasons = prepared["seasons"]
    require(len(years) == (5 if purpose == "research" else 3)
            and seasons == [row["season"] for row in years]
            and all(isinstance(season, str) and len(season) == 8 and season.isdigit()
                    and int(season[4:]) == int(season[:4]) + 1 for season in seasons)
            and all(int(right[:4]) == int(left[:4]) + 1 for left, right in zip(seasons, seasons[1:]))
            and (purpose != "research" or tuple(seasons) == RESEARCH_SEASONS)
            and tuple(prepared["records"]) == records
            and protocol["rules"]["cells"] == [dict(id=cell, amplitude=amplitude,
                noise="working_gaussian_plus_game_shared_mean" if cell == "game_shared_base" else "working_gaussian")
                for cell, amplitude in zip(cells, (.5, 1., 2., 0., 1.), strict=True)]
            and protocol["rules"]["carry"] == "unchanged centered relative-rate mean and covariance; no rate rescaling",
            "history source chronology, records, cell amplitudes or carry convention differs")
    expected = [dict(cell=cell, record=record, path=f"{cell}/{record}/fit.json")
                for cell in cells for record in records]
    require(prepared["inventory"] == expected
            and assessment["inventory"]["pair_paths"] == [row["path"] for row in expected]
            and set(assessment["consumed"]) == {"prepared", "protocol", *(f"fit_{i:03d}" for i in range(len(expected)))}
            and prepared["budget"]["pairs"] == len(expected)
            and prepared["budget"]["scores"] == len(expected)*len(years)
            and prepared["budget"]["states"] == len(expected)*(len(years)+1),
            "history source finite pair inventory differs")
    for index, year in enumerate(years):
        players = year["player_ids"]
        require(players == sorted(set(players)) and players and all(type(player) is int for player in players)
                and year["prefix"] == f"year_{index}" and math.isfinite(year["r"]) and year["r"] > 0
                and year["strata"] == sorted(map(list, set(map(tuple, year["strata"])))),
                "history source annual identity axes or rate differ")
    final = years[-1]
    n, prefix = len(final["player_ids"]), final["prefix"]
    names = ("B", "p", "eigenvalues", "W", "near", "lateral") + tuple(prefix+"_"+name for name in
        ("H", "u", "p", "truth", "centered_truth", "stratum_weight", "player_exposure"))
    accounting = dict(verified_bytes=sum(Path(ref["path"]).stat().st_size for ref in (result_ref, *refs.values())),
                      decoded_bytes=0, archive_count=0, manifest_count=4, decoded_members=[], pairs_read=[])
    geometry = _history_selected_arrays(prepared, names, accounting)
    basis = decode_shape_basis({name: geometry[name] for name in ("B", "p", "eigenvalues")},
                               basis_sha256=prepared["basis_sha256"])
    arrays = {name.removeprefix(prefix+"_"): value for name, value in geometry.items() if name.startswith(prefix+"_")}
    required_shapes = dict(H=(2*n, 2*n), u=(n,), p=(656,), truth=(2*n, 656), centered_truth=(2*n, 656),
                           stratum_weight=(len(final["strata"]),), player_exposure=(n,))
    require(all(value.shape == required_shapes[name] and value.dtype == np.dtype("float64") for name, value in arrays.items())
            and geometry["W"].shape == (656, 12) and geometry["near"].shape == geometry["lateral"].shape == (656, 1)
            and np.array_equal(arrays["p"], basis.p) and np.all(arrays["u"] > 0)
            and np.all(arrays["player_exposure"] > 0) and np.all(arrays["stratum_weight"] > 0)
            and np.allclose(arrays["u"], arrays["player_exposure"]/arrays["player_exposure"].sum(), rtol=1e-12, atol=1e-12)
            and np.allclose(arrays["H"], arrays["H"].T, rtol=1e-8, atol=1e-10)
            and math.isclose(final["directed_hours"], float(arrays["stratum_weight"].sum()/final["r"]), rel_tol=1e-12)
            and (purpose != "research" or n == 940),
            "history final geometry, native reference or current population differs")
    validate_shape_history_identity(exposure_centering(arrays["u"]) @ arrays["truth"], arrays["centered_truth"], "source_centered_truth")
    union = sorted({player for year in years for player in year["player_ids"]})
    assignments = prepared["assignments"]
    require(len(assignments) == 2*len(union)
            and {(row["role"], row["player_id"]) for row in assignments} ==
                {(role, player) for role in ("offense", "defense") for player in union}
            and all(row["trajectory"] in ("stable", "reversal", "onset", "no_prior_observation")
                    and row["template"] in ("radial", "lateral")
                    and row["current"] is (row["player_id"] in final["player_ids"]) for row in assignments),
            "history final/union assignment axes differ")
    for row in assignments:
        observed = [year["season"] for year in years if row["player_id"] in year["player_ids"]]
        prior = row["player_id"] in {player for year in years[:-1] for player in year["player_ids"]}
        require(row["observed_seasons"] == observed and row["first_observed_season"] == observed[0]
                and row["prior_observation"] is prior
                and row["return_after_absence"] is (row["current"] and prior and row["player_id"] not in years[-2]["player_ids"])
                and (row["trajectory"] == "no_prior_observation") is (row["current"] and not prior),
                "history saved observation flags differ from declared chronology")
    fits = {(row["cell"], row["record"]): assessment["consumed"][f"fit_{i:03d}"] for i, row in enumerate(expected)}
    require(len({(ref["path"], ref["sha256"]) for ref in fits.values()}) == len(expected),
            "history paired fit references are duplicated")
    fit_metadata = {key: _read_selected_artifact(ref, "attribution_history_fit", 1) for key, ref in fits.items()}
    accounting["manifest_count"] += len(fits)
    accounting["verified_bytes"] += sum(Path(ref["path"]).stat().st_size for ref in fits.values())
    require(all(document["purpose"] == purpose and (document["cell"], document["record"]) == key
                and document["prepared"] == refs["prepared"] and document["protocol"] == refs["protocol"]
                and document["consumed"] == dict(prepared=refs["prepared"], protocol=refs["protocol"],
                                                   geometry=prepared["arrays"])
                for key, document in fit_metadata.items()),
            "history named fit manifest source or pair identity differs")
    require(len({document["arrays"]["path"] for document in fit_metadata.values()}) == len(fits),
            "history named fit archives are duplicated")
    consumed = dict(source_result=result_ref, source_prepared=refs["prepared"], source_protocol=refs["protocol"],
                    source_assessment=refs["assessment"], geometry=prepared["arrays"])
    return HistorySourceSlice(result_ref, result, prepared, protocol, assessment, basis, geometry,
                              final, arrays, cells, records, fits, fit_metadata, consumed, accounting)


def read_history_final_record(source: HistorySourceSlice, cell: str, record: int) -> dict:
    """decode final pairs and one preceding mean; earlier covariances/scores stay closed."""
    from .attribution import ShapeCoefficientState, validate_shape_history_identity, validate_shape_scale_receipt

    require(cell in source.cells and type(record) is int and record in source.records,
            "history pair is outside the bound finite inventory")
    require([cell, record] not in source.read_accounting["pairs_read"],
            "history pair was already read in this command")
    reference = source.fits[cell, record]
    document = source.fit_metadata[cell, record]
    accounting = source.read_accounting
    years = source.prepared["years"]
    final, previous_index, independent = len(years)-1, len(years)-2, len(years)
    require(document["purpose"] == source.result["purpose"] and document["cell"] == cell and document["record"] == record
            and document["prepared"] == source.consumed["source_prepared"]
            and document["protocol"] == source.consumed["source_protocol"]
            and document["consumed"] == dict(prepared=document["prepared"], protocol=document["protocol"],
                                               geometry=source.prepared["arrays"])
            and document["score_count"] == len(years) and document["state_count"] == len(years)+1
            and len(document["states"]) == len(years)+1 and len(document["generation"]) == len(years),
            "history selected pair source or finite state inventory differs")
    rows = document["states"]
    shape_rows, scales = [], []
    for year, annual in enumerate(years):
        shape_rows.append(dict(name=f"year_{year}_Q", shape=[2*len(annual["player_ids"]), 40], dtype="<f8"))
    for index, row in enumerate(rows):
        annual = years[min(index, final)]
        old_ids = () if index in (0, independent) else tuple(rows[index-1]["player_ids"])
        players = sorted(set(annual["player_ids"]) | set(old_ids))
        parent = None if index in (0, independent) else dict(index=index-1, sha256=rows[index-1]["sha256"])
        digest(row["sha256"])
        require(row["index"] == index and row["season"] == annual["season"]
                and row["arm"] == ("independent" if index == independent else "borrowing")
                and row["player_ids"] == players and row["current_player_ids"] == annual["player_ids"]
                and row["entrant_ids"] == sorted(set(annual["player_ids"]) - set(old_ids))
                and row["carried_only_ids"] == sorted(set(players) - set(annual["player_ids"]))
                and row["parent"] == parent and row["r"] == annual["r"] and row["basis_sha256"] == source.basis.sha256
                and row["source_identity"]["prepared"] == source.consumed["source_prepared"]
                and row["source_identity"]["season"] == annual["season"],
                "history selected state identity, chronology, parent or role axes differ")
        digest(row["source_identity"]["score_sha256"])
        previous_receipt = None if index in (0, independent) else rows[index-1]["scale"]
        validate_shape_scale_receipt(row["scale"], previous_receipt)
        variance = row["scale"]["selected"]["variance"]
        require(row["a"] == (variance if index in (0, independent) else rows[index-1]["a"])
                and row["q"] == (None if index in (0, independent) else variance)
                and all(set(point) == {"exponent", "variance", "objective", "phase", "error", "equation_relative_residual"}
                        and point["objective"] is not None and point["equation_relative_residual"] is not None
                        and 0 <= point["equation_relative_residual"] <= 1e-8 for point in row["scale"]["curve"]),
                "history selected scale lineage or numerical receipt differs")
        n = len(players)
        for name, shape in (("Theta", [2*n, 40]), ("V", [2*n, 2*n]), ("uncentered_Theta", [2*n, 40]),
                            ("centering_shift", [40]), ("u", [n])):
            shape_rows.append(dict(name=f"state_{index}_{name}", shape=shape, dtype="<f8"))
        scales.append(dict(cell=cell, record=record, state_index=index, season=row["season"], arm=row["arm"],
            a=row["a"], q=row["q"], selected_exponent=row["scale"]["selected"]["exponent"],
            **{name: row["scale"][name] for name in ("status", "own_reasons", "inherited_limitation")}))
    require(document["array_shapes"] == shape_rows
            and document["scale_objective_evaluations"] == sum(len(row["scale"]["curve"]) for row in rows),
            "history pair ordered archive axes or scale-read accounting differs")
    names = (f"year_{final}_Q", f"state_{previous_index}_Theta") + tuple(
        f"state_{index}_{name}" for index in (final, independent)
        for name in ("Theta", "V", "uncentered_Theta", "centering_shift", "u"))
    arrays = _history_selected_arrays(document, names, accounting)
    accounting["pairs_read"].append([cell, record])
    Q = arrays[f"year_{final}_Q"]
    score_digest = ordered_array_digest(dict(Q=Q))
    states, indices, metadata = {}, {}, {}
    for index in (final, independent):
        row = rows[index]
        values = {name: arrays[f"state_{index}_{name}"] for name in
                  ("Theta", "V", "uncentered_Theta", "centering_shift", "u")}
        require(ordered_array_digest(values) == row["sha256"]
                and row["source_identity"] == dict(prepared=source.consumed["source_prepared"],
                    season=source.final_year["season"], score_sha256=score_digest),
                "history final state compound digest or final score identity differs")
        players = tuple(row["player_ids"])
        current = [players.index(player) for player in source.final_year["player_ids"]]
        expected_u = np.zeros(len(players))
        expected_u[current] = source.final_arrays["u"]
        require(np.array_equal(values["u"], expected_u), "history final exposure reference differs")
        raw = values["uncentered_Theta"]
        n = len(players)
        off, defense = expected_u @ raw[:n], expected_u @ raw[n:]
        validate_shape_history_identity(np.vstack((raw[:n]-off, raw[n:]-defense)), values["Theta"], "saved_centered_mean")
        validate_shape_history_identity(off+defense, values["centering_shift"], "saved_centering_compensation")
        V = values["V"]
        covariance_reference = np.vstack((expected_u @ V[:n], expected_u @ V[n:]))
        require(np.allclose(V, V.T, rtol=1e-8, atol=1e-10)
                and np.min(np.diag(V)) >= -1e-10*max(1., np.linalg.norm(V))
                and np.linalg.norm(covariance_reference)/max(1., np.linalg.norm(V)) <= 1e-8,
                "history saved covariance symmetry or exposure centering differs")
        arm = row["arm"]
        states[arm] = ShapeCoefficientState(season=row["season"], player_ids=players,
            current_player_ids=tuple(row["current_player_ids"]), entrant_ids=tuple(row["entrant_ids"]),
            carried_only_ids=tuple(row["carried_only_ids"]), r=row["r"], a=row["a"], q=row["q"],
            basis_sha256=row["basis_sha256"], source_identity=row["source_identity"], scale=row["scale"],
            diagnostics=row["diagnostics"], **values)
        indices[arm] = np.asarray(current + [n+i for i in current], dtype=np.int64)
        metadata[arm] = row
    previous_row = rows[previous_index]
    previous = HistoryPrecedingMean(tuple(previous_row["player_ids"]), tuple(previous_row["current_player_ids"]),
                                   arrays[f"state_{previous_index}_Theta"], previous_row)
    m0 = np.zeros_like(Q)
    n, old_n = len(source.final_year["player_ids"]), len(previous.player_ids)
    for position, player in enumerate(source.final_year["player_ids"]):
        if player in previous.player_ids:
            old = previous.player_ids.index(player)
            m0[position], m0[n+position] = previous.Theta[old], previous.Theta[old_n+old]
    # its compound digest is bound by the verified archive and final parent;
    # theta alone cannot recompute the predecessor's complete state digest.
    require(metadata["borrowing"]["parent"] == dict(index=previous_index, sha256=previous_row["sha256"]),
            "history preceding mean is not the declared final parent")
    return dict(**states, previous=previous, Q=Q, m0=m0, current_indices=indices,
                final_metadata=metadata, scales=scales, reference=reference, arrays=document["arrays"])


def read_regularization_source_slice(
    result_ref: ArtifactReference, cells: tuple[tuple[str, str, str], ...], assessment_ids: tuple[int, ...],
) -> RegularizationSourceSlice:
    """read six named manifests and selected final scores, never the complete 04f inventory."""
    from .attribution import PoolingSource, read_shape_basis, validate_pooling_basis
    from .attribution_simulation import shape_regions
    from .shot_origins import grid

    cells, assessment_ids = tuple(map(tuple, cells)), tuple(assessment_ids)
    allowed = {("paired" if population == "null" else "independent", population, law)
               for population in ("sparse", "diffuse", "null") for law in ("gaussian", "game_pace")}
    require(set(cells) == allowed and len(cells) == 6 and bool(assessment_ids)
            and assessment_ids == tuple(sorted(set(assessment_ids)))
            and all(type(outer) is int for outer in assessment_ids),
            "04g source slice requires six explicit cells and ordered unique assessment ids")
    result = _read_selected_artifact(result_ref, "attribution_regularization_result", 5)
    purpose = result["purpose"]
    require(result["execution_status"] == "complete"
            and result["numerical_status"] in (("verified", "numerically_unresolved")
                                             if purpose == "fixture_exercise" else ("verified",))
            and result["nomination"] is None and result["admission"] == "not_admitted" and result["handoff"] is None
            and all(result[name] == result["consumed"][name] for name in ("prepared", "protocol", "assessment")),
            "04g selected result is incomplete or changed its named parent bindings")
    prepared = _read_selected_artifact(result["prepared"], "attribution_regularization_prepared", 5)
    protocol = _read_selected_artifact(result["protocol"], "attribution_regularization_protocol", 5)
    n = 200 if purpose == "research" else 2
    require(prepared["purpose"] == protocol["purpose"] == purpose
            and prepared["protocol"] == result["protocol"]
            and prepared["budget"] == protocol["budget"] and protocol["budget"]["outer_per_cell"] == n
            and assessment_ids == (tuple(range(100, 200)) if purpose == "research" else (1,))
            and protocol["seasons"] == list(RESEARCH_SEASONS)
            and protocol["families"] == ["paired", "independent"]
            and protocol["populations"] == ["sparse", "diffuse", "null"]
            and protocol["laws"] == ["gaussian", "game_pace"]
            and protocol["policies"] == ["history", "population_history"]
            and protocol["representation"] == "graph_40ft" and protocol["rate"] == 40
            and protocol["shared_null"] == "paired"
            and all(prepared[name] == protocol[name] for name in
                    ("source_prepared", "source_protocol", "basis", "designs", "basis_sha256",
                     "source_design_sha256", "recovery_receipts"))
            and prepared["operators"]["arrays"] == protocol["operators"],
            "04g selected preparation, truth ordering, laws or assessment split differs")
    require(all(result["consumed"][name] == prepared[name] for name in
                ("source_result", "source_prepared", "basis", "designs", "spec_snapshot"))
            and result["consumed"]["operators"] == prepared["operators"]["arrays"],
            "04g result changed its named evidence references")
    if purpose == "research":
        require(result_ref["sha256"] == "84bb4d034bb2213ce8b1cf0cf91fe54713fa7ba797e684f329838b16d05266a6"
                and result["protocol"]["sha256"] == "9e8266d1b0f7883d284e677be1e607f3cd8593264c3a5e95e9909acbfb3b8ef2"
                and result["implementation"] == prepared["implementation"] == protocol["implementation"],
                "research requires the committed 04g result, protocol and source producer")
        named = {
            ("independent", "diffuse", "game_pace"): "c4181ad60710eda3a7861e31ee84c691a00a2467dd870cf13be7ff7ce4c0124f",
            ("independent", "diffuse", "gaussian"): "2090a03c258957fbb14f90bb8b7c77dc8ba6baf9a39f893c0bdc57e9595c9274",
            ("independent", "sparse", "game_pace"): "4d5e9ceef16b6a9feb67dd529fb6333cc1f48727c5449799a449cb219544a9a3",
            ("independent", "sparse", "gaussian"): "f5cc99497783f2891cf6b70f76eae842bde42c573809db97ac01dbf960fa4438",
            ("paired", "null", "game_pace"): "6cb091e00485526b0417752b10e43a054b50165b18bfa2882331a99ba2a0bdaa",
            ("paired", "null", "gaussian"): "1f04e03130c398e37e895fa3f9ce6517454553868f98bf8c3712a2d05aed0e64",
        }
        selected = {cell: [ref for ref in result["consumed_fits"] if ref["sha256"] == sha]
                    for cell, sha in named.items()}
        require(all(len(refs) == 1 for refs in selected.values()), "named research fit manifest is absent or duplicated")
        selected = {cell: refs[0] for cell, refs in selected.items()}
    else:
        rows = result["selected_cells"]
        selected = {(row["family"], row["population"], row["law"]): row["fit"] for row in rows}
        require(len(rows) == len(selected) == 6 and set(selected) == allowed
                and all(ref in result["consumed_fits"] for ref in selected.values()),
                "fixture source requires six explicitly named schema-5 fit references")
    source_prepared = _read_selected_artifact(prepared["source_prepared"], "attribution_pooling_prepared", 4)
    source_protocol = _read_selected_artifact(prepared["source_protocol"], "attribution_pooling_protocol", 4)
    require(source_prepared["purpose"] == source_protocol["purpose"] == purpose
            and source_prepared["protocol"] == prepared["source_protocol"]
            and source_prepared["basis"] == prepared["basis"]
            and source_prepared["designs"]["arrays"] == prepared["designs"]
            and source_prepared["basis_sha256"] == prepared["basis_sha256"] == source_protocol["basis_sha256"]
            and source_prepared["design_sha256"] == prepared["source_design_sha256"] == source_protocol["design_sha256"]
            and source_prepared["seasons"] == [row["season"] for row in source_prepared["years"]] == list(RESEARCH_SEASONS),
            "04g named source basis, design or chronological reference differs")
    basis = read_shape_basis(source_prepared)
    validate_pooling_basis(basis)
    require(purpose != "research" or basis.sha256 == "649a49ecba19de5df609d6980d9de76491afa13e9108df0d8e6500659886cc51",
            "research basis differs from the frozen semantic identity")
    context = PoolingSource(prepared["source_prepared"], source_prepared, source_protocol, basis)
    arrays = load_arrays(source_prepared["designs"])
    fields = ("offense", "defense", "seconds", "si", "u", "player_exposure", "home_teams", "away_teams", "row_game_ids")
    require(list(arrays) == [f"{name}_{year}_{field}" for name in ("train", "evaluation")
                            for year in range(5) for field in fields]+["centers", "W"]
            and ordered_array_digest(arrays) == source_prepared["design_sha256"]
            and np.array_equal(arrays["centers"], grid()[0]), "named design archive order or identity differs")
    W, regions = shape_regions()
    require(np.array_equal(arrays["W"], W) and source_prepared["regions"] == list(regions),
            "named twelve-region operator differs")
    histories = []
    for name in ("train", "evaluation"):
        designs = []
        for year, annual in enumerate(source_prepared["years"]):
            design = {field: arrays[f"{name}_{year}_{field}"] for field in fields}
            players, strata = tuple(annual["players"]), tuple(map(tuple, annual["strata"]))
            positions, row_count = {player: i for i, player in enumerate(players)}, len(design["seconds"])
            require(len(players) == len(set(players)) == 32 and players == tuple(sorted(players))
                    and all(design[field].dtype == np.dtype("float64" if field in
                        ("seconds", "u", "player_exposure") else "int64") for field in fields)
                    and design["offense"].shape == design["defense"].shape == (row_count, 5)
                    and design["si"].shape == design["row_game_ids"].shape == (row_count,)
                    and np.all(design["seconds"] > 0) and np.all((design["si"] >= 0) & (design["si"] < len(strata)))
                    and all(len(set(row)) == 5 and set(row).issubset(players)
                            for field in ("offense", "defense") for row in design[field]),
                    "named design player order, rows or dtypes differ")
            X = np.zeros((row_count, 64))
            for role, field in enumerate(("offense", "defense")):
                indices = np.array([[positions[int(player)] for player in row] for row in design[field]])
                X[np.arange(row_count)[:, None], role*32+indices] = 1
            e, si = design["seconds"]/3600, design["si"]
            weights = np.bincount(si, weights=e, minlength=len(strata))
            xbar = np.stack([np.average(X[si == s], axis=0, weights=e[si == s]) for s in range(len(strata))])
            Z = X-xbar[si]
            exposure = design["seconds"]@X[:, :32]
            require(np.allclose(exposure, design["player_exposure"], rtol=1e-12, atol=1e-12)
                    and np.allclose(design["u"], exposure/exposure.sum(), rtol=1e-12, atol=1e-12),
                    "named design exposure reference differs from its complete rows")
            design.update(players=players, strata=strata, e=e, X=X, p=basis.p,
                          H=40*Z.T@(e[:, None]*Z), xbar=xbar, stratum_weight=40*weights,
                          game_ids=tuple(np.unique(design["row_game_ids"]).tolist()))
            designs.append(design)
        histories.append(tuple(designs))
    operator_arrays = load_arrays(prepared["operators"])
    require(list(operator_arrays) == [season+"_J" for season in RESEARCH_SEASONS], "named recovery operator order differs")
    recovery = []
    for year, design in enumerate(histories[0]):
        J, receipt = identifiable_recovery_operator(design["H"], design["u"], design["players"],
            inseparable_groups=((26, 31),), expected_rank=60 if purpose == "research" else protocol["recovery_receipts"][year]["rank"])
        saved = operator_arrays[RESEARCH_SEASONS[year]+"_J"]
        require(saved.shape == (64, 64) and saved.dtype == np.dtype("float64")
                and np.allclose(saved, J, rtol=1e-8, atol=1e-10)
                and receipt["rank_at_tau_factors"] == protocol["recovery_receipts"][year]["rank_at_tau_factors"],
                "named recovery operator, inseparable average or cutoff sensitivity differs")
        recovery.append(saved)
    assessment = _read_selected_artifact(result["assessment"], "attribution_regularization_assessment", 5)
    require(assessment["purpose"] == purpose and assessment["prepared"] == result["prepared"]
            and assessment["protocol"] == result["protocol"]
            and assessment["fits"] == result["consumed_fits"]
            and assessment["execution_status"] == "complete"
            and assessment["numerical_status"] == result["numerical_status"],
            "named 04g assessment changed its completion or source bindings")
    score_rows = {}
    for row in assessment["records"]:
        key = tuple(row[name] for name in ("family", "population", "law", "outer", "year"))
        if key[:3] in allowed and key[3] in assessment_ids and key[4] == 5:
            require(key not in score_rows, "selected source assessment record is duplicated")
            score_rows[key] = {name: row[name] for name in ("R_control", "R_zero", "P_control", "P_zero")}
            require(row["denominator"] == 64 and all(type(value) in (int, float) and math.isfinite(value)
                    for value in score_rows[key].values()), "selected source assessment score or denominator differs")
    require(set(score_rows) == {(*cell, outer, 5) for cell in cells for outer in assessment_ids},
            "selected source final-year assessment record is missing")
    consumed = dict(source_result=result_ref, source_prepared=result["prepared"], source_protocol=result["protocol"],
        pooling_prepared=prepared["source_prepared"], pooling_protocol=prepared["source_protocol"],
        basis=prepared["basis"], designs=prepared["designs"], operators=prepared["operators"]["arrays"],
        source_assessment=result["assessment"])
    records, manifests = [], {}
    parents = dict(prepared=result["prepared"], protocol=result["protocol"], source_result=prepared["source_result"],
        source_prepared=prepared["source_prepared"], basis=prepared["basis"], designs=prepared["designs"],
        operators=prepared["operators"]["arrays"], spec_snapshot=prepared["spec_snapshot"])
    for index, cell in enumerate(cells):
        reference = selected[cell]
        require(reference in result["consumed_fits"], "selected manifest is not a named source fit")
        document = _read_selected_artifact(reference, "attribution_regularization_fit", 5)
        require(document["purpose"] == purpose and tuple(document[name] for name in ("family", "population", "law")) == cell
                and document["status"] == "complete" and document["range"] == dict(start=0, stop=n)
                and document["consumed"] == parents and all(document[name] == value for name, value in parents.items())
                and [row["outer"] for row in document["records"]] == list(range(n))
                and (purpose != "research" or document["implementation"] == protocol["implementation"]),
                "selected manifest source, cell, outer inventory or producer differs")
        truths = []
        for row in document["records"]:
            require(tuple(row[name] for name in ("family", "population", "law")) == cell and row["status"] == "complete",
                    "selected dataset identity differs from its manifest")
            digest(row["truth_sha256"])
            digest(row["activation_sha256"])
            truths.append({name: row[name] for name in
                ("family", "population", "law", "outer", "truth_sha256", "activation", "activation_sha256")})
            if row["outer"] in assessment_ids:
                require(len(row["annual"]["history"]) == len(row["responses"]) == 5,
                        "selected annual control chain is incomplete")
                records.append(dict(truths[-1], statistics=row["statistics"], responses=row["responses"],
                    annual=dict(history=row["annual"]["history"]), saved_scores=score_rows[(*cell, row["outer"], 5)]))
        manifests[cell] = dict(reference=reference, truths=truths)
        consumed[f"selected_fit_{index}"] = reference
    source = RegularizationSourceSlice(result_ref, result, prepared, protocol, context, basis,
        histories[0], histories[1], W, tuple(recovery), tuple(records), manifests, (), consumed,
        tuple(sorted({str(Path(ref["path"]).parent) for ref in consumed.values()})),
        dict(cells=6, truth_records=6*n, assessment_histories=6*len(assessment_ids),
             assessment_annual_states=30*len(assessment_ids)))
    from dataclasses import replace
    return replace(source, fixed_populations=read_regularization_source_populations(source, records[0])[0])


def read_regularization_source_populations(
    source: RegularizationSourceSlice, record: dict,
) -> tuple[tuple[RevisionPopulation, ...], "PoolingStatistics"]:
    """decode one selected annual-summary history without opening fitted states."""
    from .attribution import PoolingStatistics

    require(record in source.records, "record is not in the selected assessment inventory")
    arrays = load_arrays(record["statistics"])
    require(list(arrays) == [season+"_"+name for season in RESEARCH_SEASONS for name in POOLING_STAT_FIELDS],
            "selected source sufficient-statistic names or annual order differs")
    populations = []
    paired = record["family"] == "paired"
    require((paired and record["population"] == "null")
            or (not paired and record["family"] == "independent" and record["population"] in ("sparse", "diffuse")),
            "source record requires explicit paired-null or independent contract")
    for year, season in enumerate(RESEARCH_SEASONS):
        design = source.training[year]
        population = decode_saved_population({name: arrays[season+"_"+name] for name in POOLING_STAT_FIELDS},
            benchmark="unblocked_spatial", season=season, season_index=year,
            source_protocol_sha256=(source.context.prepared["protocol"] if paired else source.result["protocol"])["sha256"],
            population_id=(f"synthetic:04e:null:{record['law']}:{record['outer']}:unblocked_spatial" if paired else
                f"synthetic:04g:independent:{record['population']}:{record['law']}:{record['outer']}:unblocked_spatial"),
            player_ids=design["players"], strata=design["strata"], expected_p=source.basis.p, expected_r=40.)
        response = record["responses"][year]
        require(response["year"] == year+1 and response["season"] == season
                and response["seed"] == [40604 if paired else 40804,
                    ("sparse", "diffuse", "null").index(record["population"]),
                    ("gaussian", "game_pace").index(record["law"]), record["outer"], year]
                and response["sufficient_statistics_sha256"] == statistic_digest(population)
                and all(np.allclose(getattr(population, name), design[name], rtol=1e-10, atol=1e-10)
                        for name in ("H", "xbar", "u", "player_exposure", "stratum_weight")),
                "selected source response identity or fixed deployment moments differ")
        digest(response["sha256"])
        populations.append(population)
    return tuple(populations), PoolingStatistics(record["statistics"]["arrays"], source.context.reference["sha256"], arrays)


def read_regularization_source_record(
    source: RegularizationSourceSlice, record: dict,
) -> tuple[tuple[RevisionPopulation, ...], tuple["AnnualState", ...]]:
    """stream one selected history through its named schema, with explicit predecessors."""
    from .attribution import read_pooling_annual, read_regularization_annual

    require(record in source.records, "record is not in the selected assessment inventory")
    populations, statistics = read_regularization_source_populations(source, record)
    states, previous = [], None
    for year, population in enumerate(populations):
        reference = record["annual"]["history"][year]
        path = linked_path(reference)
        document = read_json(path)
        require(all(document[name] == record[name] for name in ("population", "law", "outer"))
                and document["season"] == population.season and document["season_index"] == year
                and document["representation"] == "graph_40ft"
                and document["response_sha256"] == record["responses"][year]["sha256"]
                and document["previous"] == (None if previous is None else previous[0]),
                "selected source annual case, response or explicit predecessor differs")
        if record["family"] == "paired":
            state = read_pooling_annual(path, source=source.context, previous=previous, statistics=statistics)
        else:
            require(document["family"] == "independent" and document["prior_policy"] == "history",
                    "selected independent control changed family or prior policy")
            state = read_regularization_annual(path, population=population, basis=source.basis,
                prepared=source.result["prepared"], protocol=source.result["protocol"],
                source=source.prepared["source_prepared"], statistics=record["statistics"]["arrays"],
                basis_reference=source.prepared["basis"], previous=previous, shared_volume=None)
        states.append(state)
        previous = (reference, state)
    return populations, tuple(states)


@dataclass(frozen=True)
class ResolutionSourceSlice:
    """six named eleven-mode controls and their selected original summaries."""

    reference: ArtifactReference
    result: dict
    prepared: dict
    protocol: dict
    source: RegularizationSourceSlice
    controls: dict[tuple[str, str, str], dict]
    consumed: dict
    input_roots: tuple[str, ...]


def read_resolution_source_slice(
    result_ref: ArtifactReference, cells: tuple[tuple[str, str, str], ...], assessment_ids: tuple[int, ...],
) -> ResolutionSourceSlice:
    """bind selected 04h controls without annual-state or calibration-array reads."""
    cells, assessment_ids = tuple(map(tuple, cells)), tuple(assessment_ids)
    allowed = {("paired" if population == "null" else "independent", population, law)
               for population in ("sparse", "diffuse", "null") for law in ("gaussian", "game_pace")}
    require(len(cells) == 6 and set(cells) == allowed, "04h source requires six explicit distinct cells")
    result = _read_selected_artifact(result_ref, "attribution_resolution_result", 5)
    purpose = result["purpose"]
    n = 100 if purpose == "research" else 1
    fits = result.get("consumed_fits")
    require(isinstance(fits, list) and len(fits) == 6
            and all(isinstance(row, dict) and set(row) == {"path", "sha256"}
                    and isinstance(row["path"], str) and isinstance(row["sha256"], str) for row in fits)
            and len({(row["path"], row["sha256"]) for row in fits}) == 6,
            "04h source requires six distinct control references")
    require(assessment_ids == tuple(range(n, 2*n))
            and all(type(outer) is int for outer in assessment_ids)
            and result["execution_status"] == "complete"
            and result["numerical_status"] in (("verified",) if purpose == "research" else ("verified", "unresolved"))
            and result["nomination"] is None and result["admission"] == "not_admitted" and result["handoff"] is None
            and all(result[name] == result["consumed"][name] for name in ("prepared", "protocol", "assessment")),
            "04h result, assessment ids or six-control inventory differs")
    if purpose == "research":
        require(result_ref["sha256"] == "c962c9d4c38c86150fceff15036c1f19bc5bfea897127b7fd08d4f929cdcdbb7"
                and result["prepared"]["sha256"] == "d20303ab13bc2d4282f4498756bcf48d83a2326f9adc4a8d49f2b23b274b5f85"
                and result["protocol"]["sha256"] == "a09a39d789274c0c4e3abb2814ce2ae67569c4da15839b2d54db74811c2f6fb1",
                "research requires the committed 04h result, preparation and protocol")
    prepared = _read_selected_artifact(result["prepared"], "attribution_resolution_prepared", 5)
    protocol = _read_selected_artifact(result["protocol"], "attribution_resolution_protocol", 5)
    variances = [0., *np.power(10., np.arange(-8., .25, .5)).tolist()]
    split = dict(calibration=list(range(n)), assessment=list(assessment_ids))
    require(prepared["purpose"] == protocol["purpose"] == purpose
            and prepared["protocol"] == result["protocol"]
            and prepared["consumed"] == dict(protocol=result["protocol"], **protocol["consumed"])
            and all(prepared[name] == value for name, value in protocol["consumed"].items())
            and all(prepared[name] == protocol[name] for name in
                    ("source_result", "source_prepared", "source_protocol", "source_assessment", "source_producer",
                     "geometry", "target_rank", "source_inventory"))
            and all(prepared[name] == protocol[name] == value for name, value in
                    dict(split=split, seasons=list(RESEARCH_SEASONS), prior_variances=variances, rate=40.,
                         recovery_denominator=64).items())
            and result["consumed"]["source_result"] == prepared["source_result"],
            "04h selected source, chronology, grid, geometry or parent bindings differ")
    source = read_regularization_source_slice(prepared["source_result"], cells, assessment_ids)
    require(source.result["purpose"] == purpose
            and prepared["source_prepared"] == source.result["prepared"]
            and prepared["source_protocol"] == source.result["protocol"]
            and prepared["source_assessment"] == source.result["assessment"]
            and prepared["source_producer"] == result["source_producer"] == source.result["implementation"]
            and prepared["target_rank"] == source.protocol["recovery_receipts"][-1]["rank"]
            and (purpose != "research" or prepared["target_rank"] == prepared["final_player_rank"] == 60),
            "04h original source producer, final rank or native reference differs")
    from .attribution_simulation import shape_regions
    _, region_names = shape_regions()
    near = np.asarray([name.startswith(("in_zone_0_10_", "in_zone_10_20_")) for name in region_names], dtype=float)
    lateral = np.asarray([.5 if name.endswith("positive_y") else -.5 for name in region_names])
    geometry = dict(native=ordered_array_digest(dict(p=source.basis.p)), basis=source.basis.sha256,
        regions=ordered_array_digest(dict(W=source.W, within_20_ft=(source.W@near)[:, None],
                                         lateral_redistribution=(source.W@lateral)[:, None])),
        entities=ordered_array_digest({RESEARCH_SEASONS[year]: np.asarray(design["players"], dtype=np.int64)
                                       for year, design in enumerate(source.training)}))
    require(prepared["geometry"] == geometry, "04h selected region operators or ordered player geometry differs")
    inventory = prepared["source_inventory"]["assessment_records"]
    selected_records = {tuple(row[name] for name in ("family", "population", "law", "outer")): row for row in inventory}
    require(len(inventory) == len(selected_records) == 6*n
            and all(selected_records[tuple(row[name] for name in ("family", "population", "law", "outer"))]
                    == dict(family=row["family"], population=row["population"], law=row["law"], outer=row["outer"],
                            statistics=row["statistics"], history=row["annual"]["history"],
                            truth_sha256=row["truth_sha256"], saved_scores=row["saved_scores"])
                    for row in source.records),
            "04h selected source summaries, identities or assessment records differ")
    players = list(source.training[-1]["players"])
    union = sorted({player for design in source.training for player in design["players"]})
    require(len(players) == 32 and len(union) == 34 and len(source.training[-1]["strata"]) == 6,
            "04h selected current/union player or final context dimensions differ")
    controls = {}
    for reference in fits:
        document = _read_selected_artifact(reference, "attribution_resolution_fit", 5)
        cell = tuple(document[name] for name in ("family", "population", "law"))
        require(cell in allowed and cell not in controls and document["purpose"] == purpose
                and document["prepared"] == result["prepared"] and document["protocol"] == result["protocol"]
                and document["source_result"] == source.reference
                and document["source_producer"] == source.result["implementation"]
                and document["geometry"] == prepared["geometry"] and document["split"] == split
                and document["prior_variances"] == variances and document["basis_columns"]["11"] == list(range(11))
                and document["current_player_ids"] == players and document["union_player_ids"] == union
                and document["consumed"] == dict(prepared=result["prepared"], protocol=result["protocol"],
                    source_result=source.reference, arrays=document["arrays"]["arrays"])
                and reference in result["consumed"].values()
                and document["nomination"] is None and document["admission"] == "not_admitted" and document["handoff"] is None,
                "duplicate, foreign or mismatched selected eleven-mode control")
        linked_path(document["arrays"]["arrays"])
        controls[cell] = dict(reference=reference, document=document)
    require(set(controls) == allowed, "04h selected control inventory is incomplete")
    controls = {cell: controls[cell] for cell in cells}
    consumed = dict(source_result=result_ref, source_prepared=result["prepared"], source_protocol=result["protocol"],
                    **{f"control_{index}": controls[cell]["reference"] for index, cell in enumerate(cells)})
    roots = {*source.input_roots, *(str(Path(ref["path"]).parent) for ref in consumed.values())}
    return ResolutionSourceSlice(result_ref, result, prepared, protocol, source, controls, consumed, tuple(sorted(roots)))


def _read_resolution_arrays(source: ResolutionSourceSlice, cell: tuple[str, str, str], axes: dict) -> dict:
    """decode only explicitly named assessment arrays in the shared 04h archive."""
    require(cell in source.controls, "control cell is not in the selected inventory")
    document = source.controls[cell]["document"]
    binding = document["arrays"]
    require(isinstance(binding, dict) and set(binding) == {"arrays", "array_shapes"}
            and isinstance(binding["array_shapes"], list), "selected control array binding differs")
    shapes = binding["array_shapes"]
    require(all(isinstance(row, dict) and set(row) == {"name", "shape", "dtype"}
                and isinstance(row["name"], str) for row in shapes)
            and len({row["name"] for row in shapes}) == len(shapes),
            "selected control archive declares duplicate arrays")
    declared = {row["name"]: row for row in shapes}
    lengths = dict(assessment_outer=len(document["split"]["assessment"]), prior_variance=18, union_role_player=68,
                   current_role_player=64, spatial_mode_11=11, final_context=6, native_cell=656,
                   target=3, region=12, functional=2)
    require(all(name in declared and document["axes"].get(name) == axis
                and declared[name]["shape"] == [lengths[value] for value in axis]
                and declared[name]["dtype"] == np.dtype("float64").str for name, axis in axes.items()),
            "selected eleven-mode control fields, shapes, dtypes or declared axes differ")
    with np.load(linked_path(binding["arrays"]), allow_pickle=False) as archive:
        require(archive.files == [row["name"] for row in shapes], "selected archive array order differs")
        arrays = {name: archive[name] for name in axes}
    require(all(value.dtype == np.dtype("float64") and list(value.shape) == declared[name]["shape"]
                and np.isfinite(value).all() for name, value in arrays.items()),
            "selected eleven-mode control arrays differ from their declarations")
    return arrays


def read_resolution_control(source: ResolutionSourceSlice, cell: tuple[str, str, str]) -> dict:
    """read only the five training-fit arrays; truth-derived assessment stays separate."""
    arrays = _read_resolution_arrays(source, cell, dict(
        objectives_11=["assessment_outer", "prior_variance"], selected_a_11=["assessment_outer"],
        Theta_11=["assessment_outer", "union_role_player", "spatial_mode_11"],
        V_11=["assessment_outer", "union_role_player", "union_role_player"],
        context_11=["assessment_outer", "final_context", "native_cell"]))
    variances = np.asarray(source.prepared["prior_variances"])
    require(np.array_equal(arrays["selected_a_11"], variances[np.argmin(arrays["objectives_11"], axis=1)]),
            "selected eleven-mode variance differs from the unchanged marginal selector")
    return arrays


def read_resolution_assessment(source: ResolutionSourceSlice, cell: tuple[str, str, str]) -> dict:
    """read named eleven-mode realized diagnostics, never fixed-risk/calibration arrays."""
    return _read_resolution_arrays(source, cell, dict(
        adaptive_risk_11=["assessment_outer", "target"], adaptive_prediction_excess_11=["assessment_outer"],
        adaptive_coupling_11=["assessment_outer"],
        adaptive_region_error_11=["assessment_outer", "current_role_player", "region"],
        adaptive_functional_error_11=["assessment_outer", "current_role_player", "functional"],
        assessment_zero_risk=["assessment_outer", "target"], omitted_detail_11=["assessment_outer", "target"],
        projection_region_error_11=["assessment_outer", "current_role_player", "region"],
        projection_functional_error_11=["assessment_outer", "current_role_player", "functional"]))


def group_observations(
    observations, references: AnnualReferences, game_ids: tuple
) -> GroupedPopulation:
    """group factual sparse rows or explicitly synthetic dense count matrices.

    rows for a game must be contiguous; inventory order is independent of row
    order. dense signed/noninteger responses are synthetic inputs, not captures.
    """
    require(
        game_ids == tuple(sorted(set(game_ids))) and bool(game_ids),
        "grouped statistics require sorted unique inventory games",
    )
    players = references.player_ids
    n, k, s = 2 * len(players), len(references.response_counts), len(references.strata)
    require(
        players == tuple(sorted(set(players)))
        and bool(players)
        and (
            (references.benchmark == "all_attempts" and references.p is None and k == 1)
            or (
                references.benchmark == "unblocked_spatial"
                and references.p is not None
                and k == 656
            )
        )
        and references.strata == tuple(sorted(set(references.strata)))
        and s > 0,
        "invalid grouped population reference design",
    )
    require(
        references.u.shape == (len(players),)
        and np.isfinite(references.u).all()
        and np.all(references.u > 0)
        and math.isclose(float(references.u.sum()), 1, rel_tol=1e-12)
        and references.player_exposure.shape == (len(players),)
        and np.isfinite(references.player_exposure).all()
        and np.all(references.player_exposure > 0)
        and np.isfinite(references.response_counts).all(),
        "invalid fixed annual references",
    )
    if references.p is not None:
        require(
            references.p.shape == (656,)
            and np.isfinite(references.p).all()
            and np.all(references.p > 0)
            and math.isclose(float(references.p.sum()), 1, rel_tol=1e-12),
            "shape reference must be positive and normalized",
        )
    positions = {player: index for index, player in enumerate(players)}
    strata = {value: index for index, value in enumerate(references.strata)}
    inventory = {game: index for index, game in enumerate(game_ids)}
    dimensions = {"H_e": n * n, "T_raw": n * k, "stratum_x": s * n, "stratum_n": s * k}
    pieces = {name: [None] * len(game_ids) for name in dimensions}
    se = np.zeros((len(game_ids), s))
    qt = np.zeros(len(game_ids))
    qh = None if references.p is None else np.zeros(len(game_ids))
    signatures = [hashlib.sha256() for _ in range(n)]
    observed = set()
    row_count = 0
    for game, game_rows in groupby(observations, key=lambda row: row["game_id"]):
        require(
            game in inventory and game not in observed,
            "count rows require unique contiguous inventory-game groups",
        )
        observed.add(game)
        batch = list(game_rows)
        gi = inventory[game]
        e = np.array([row["seconds"] / 3600 for row in batch])
        require(
            np.isfinite(e).all() and np.all(e > 0),
            "grouped rows require positive exposure",
        )
        indices = np.array(
            [
                [positions[player] for player in row["offense"]]
                + [len(players) + positions[player] for player in row["defense"]]
                for row in batch
            ],
            dtype=np.int64,
        )
        require(
            indices.shape == (len(batch), 10)
            and all(len(set(values)) == 10 for values in indices),
            "grouped rows require five distinct skaters per direction",
        )
        si = np.array([strata[tuple(row["stratum"])] for row in batch])
        X = sparse.csr_matrix(
            (
                np.ones(indices.size),
                (np.repeat(np.arange(len(batch)), 10), indices.ravel()),
            ),
            shape=(len(batch), n),
        )
        Z = sparse.csr_matrix(
            (np.ones(len(batch)), (np.arange(len(batch)), si)), shape=(len(batch), s)
        )
        if isinstance(batch[0]["counts"], np.ndarray):
            values = np.asarray([row["counts"] for row in batch])
            require(
                values.shape == (len(batch), k) and np.isfinite(values).all(),
                "invalid synthetic dense response matrix",
            )
            N = sparse.csr_matrix(values)
        else:
            ni, nj, nv = [], [], []
            for index, row in enumerate(batch):
                for cell, count in row["counts"]:
                    require(
                        type(cell) is int and 0 <= cell < k and math.isfinite(count),
                        "invalid sparse response cell/count",
                    )
                    ni.append(index)
                    nj.append(cell)
                    nv.append(count)
            N = sparse.csr_matrix((nv, (ni, nj)), shape=(len(batch), k))
        total = np.asarray(N.sum(axis=1)).ravel()
        se[gi] = np.asarray(Z.T @ e).ravel()
        qt[gi] = np.sum(total * total / e)
        if qh is not None:
            qh[gi] = np.sum((N.multiply(N) @ (1 / references.p) - total * total) / e)
        moments = {
            "H_e": X.T @ X.multiply(e[:, None]),
            "T_raw": X.T @ N,
            "stratum_x": Z.T @ X.multiply(e[:, None]),
            "stratum_n": Z.T @ N,
        }
        for name, moment in moments.items():
            coo = moment.tocoo()
            flat = coo.row.astype(np.int64) * moment.shape[1] + coo.col
            order = np.argsort(flat)
            pieces[name][gi] = (flat[order], coo.data[order])
        for index, members in enumerate(indices):
            marker = (row_count + index).to_bytes(8, "little")
            for player in members:
                signatures[player].update(marker)
        row_count += len(batch)
    require(row_count > 0, "grouped population has no admitted observations")
    matrices = {}
    for name, width in dimensions.items():
        entries = pieces[name]
        indptr = np.cumsum(
            [0] + [0 if value is None else len(value[0]) for value in entries]
        )
        columns = np.concatenate([value[0] for value in entries if value is not None])
        values = np.concatenate([value[1] for value in entries if value is not None])
        matrices[name] = sparse.csr_matrix(
            (values, columns, indptr), shape=(len(game_ids), width)
        )
    return GroupedPopulation(
        game_ids,
        matrices["H_e"],
        matrices["T_raw"],
        se,
        matrices["stratum_x"],
        matrices["stratum_n"],
        qt,
        qh,
        tuple(value.hexdigest() for value in signatures),
        row_count,
    )


def weighted_population(
    grouped: GroupedPopulation, game_weights: np.ndarray, references: AnnualReferences
) -> RevisionPopulation:
    """recompute weighted context residualization from raw game moments once."""
    a = np.asarray(game_weights, dtype=float)
    require(
        a.shape == (len(grouped.game_ids),) and np.isfinite(a).all() and np.all(a > 0),
        "game multipliers must be finite and positive in inventory order",
    )
    n, k, s = (
        2 * len(references.player_ids),
        len(references.response_counts),
        len(references.strata),
    )
    require(
        grouped.H_e.shape == (len(a), n * n)
        and grouped.T_raw.shape == (len(a), n * k)
        and grouped.stratum_x.shape == (len(a), s * n)
        and grouped.stratum_n.shape == (len(a), s * k)
        and grouped.stratum_e.shape == (len(a), s)
        and grouped.Q_t is not None and grouped.Q_t.shape == (len(a),),
        "grouped moments disagree with annual reference dimensions",
    )
    E = a @ grouped.stratum_e
    X = np.asarray(a @ grouped.stratum_x).reshape(s, n)
    N = np.asarray(a @ grouped.stratum_n).reshape(s, k)
    require(
        math.isfinite(references.r) and references.r > 0 and np.all(E > 0),
        "weighted population requires positive fixed rate and context exposure",
    )
    xbar = X / E[:, None]
    H = references.r * (np.asarray(a @ grouped.H_e).reshape(n, n) - X.T @ xbar)
    T = np.asarray(a @ grouped.T_raw).reshape(n, k) - X.T @ (N / E[:, None])
    totals = N.sum(axis=1)
    yy = float((a @ grouped.Q_t - np.sum(totals * totals / E)) / references.r)
    shape_yy = None
    if references.p is not None:
        p = references.p
        require(
            p.shape == (k,)
            and np.isfinite(p).all()
            and np.all(p > 0)
            and math.isclose(float(p.sum()), 1, rel_tol=1e-12, abs_tol=1e-12)
            and grouped.Q_h is not None
            and grouped.Q_h.shape == (len(a),),
            "spatial population requires fixed positive native shares and shape quadratic",
        )
        shape_yy = float(
            (
                a @ grouped.Q_h
                - np.sum((np.sum(N * N / p, axis=1) - totals * totals) / E)
            )
            / references.r
        )
    require(
        np.isfinite(H).all()
        and np.isfinite(T).all()
        and math.isfinite(yy)
        and (shape_yy is None or math.isfinite(shape_yy)),
        "nonfinite weighted annual statistics",
    )
    return RevisionPopulation(
        references.benchmark,
        references.season,
        references.season_index,
        references.protocol_sha256,
        references.population_id,
        references.player_ids,
        references.strata,
        H,
        T,
        yy,
        shape_yy,
        references.r,
        xbar,
        N / (references.r * E[:, None]),
        references.r * E,
        references.player_exposure,
        references.response_counts,
        references.u,
        references.p,
    )


def load_recovery_design(prepared: dict, model_protocol: dict) -> list[dict]:
    """load the saved synthetic archive through its ordered array contract."""
    return decode_recovery_design(prepared, model_protocol, load_arrays(prepared["synthetic_design"]))


def decode_recovery_design(prepared: dict, model_protocol: dict, arrays: dict[str, np.ndarray]) -> list[dict]:
    """decode 04c's saved synthetic truth and design; never regenerate either.

    callers validate the enclosing evidence references. information is rebuilt
    once per year through the shared grouped residualization and independently
    checked against the complete row calculation. no responses are generated.
    """
    require(type(prepared["schema_version"]) is int and prepared["schema_version"] == 3
            and prepared["kind"] == "attribution_recovery_prepared"
            and prepared["seasons"] == list(RESEARCH_SEASONS)
            and prepared["purpose"] == model_protocol["purpose"]
            and prepared["source_prepared"] == model_protocol["source_prepared"]
            and prepared["source_protocol"] == model_protocol["source_protocol"]
            and prepared["request_sha256"] == model_protocol["request_sha256"],
            "fixed synthetic preparation differs from its original model protocol")
    shapes = prepared["synthetic_design"]["array_shapes"]
    require(list(arrays) == [row["name"] for row in shapes]
            and all(list(arrays[row["name"]].shape) == row["shape"]
                    and arrays[row["name"]].dtype.str == row["dtype"]
                    and arrays[row["name"]].dtype.kind in "biuf"
                    and np.isfinite(arrays[row["name"]]).all() for row in shapes),
            "fixed synthetic ordered array contract differs")
    names = ("offense", "defense", "seconds", "si", "u", "scalar_ticks", "truth_scalar", "truth_shape",
             "truth_map", "player_exposure", "home_teams", "away_teams")
    require(list(arrays) == [f"year_{year}_{name}" for year in range(5) for name in names] + ["p", "centers", "W"]
            and ordered_array_digest(arrays) == model_protocol["synthetic_design_sha256"],
            "fixed synthetic design/truth order or identity changed")
    p, centers, W = (arrays[name] for name in ("p", "centers", "W"))
    from .shot_origins import grid

    require(p.shape == (656,) and np.all(p > 0) and abs(float(p.sum()) - 1) <= 1e-12
            and np.array_equal(centers, grid()[0]) and W.shape == (656, 12)
            and np.array_equal(W.sum(axis=1), np.ones(656)) and np.all(W >= 0),
            "fixed synthetic geometry, native shares or regions changed")
    require(len(prepared["synthetic_years"]) == 5, "fixed synthetic annual denominator changed")
    designs = []
    for year, annual in enumerate(prepared["synthetic_years"]):
        players = tuple(annual["players"])
        strata = tuple(tuple(value) for value in annual["strata"])
        require(annual["season"] == RESEARCH_SEASONS[year]
                and players == tuple(sorted(set(players))) and len(players) == 32
                and strata == tuple(sorted(set(strata))) and len(strata) == 6,
                "fixed synthetic player, context or annual order changed")
        design = {name: arrays[f"year_{year}_{name}"] for name in names}
        expected_shapes = dict(offense=(9600, 5), defense=(9600, 5), seconds=(9600,), si=(9600,),
            u=(32,), scalar_ticks=(64,), truth_scalar=(64,), truth_shape=(64, 656), truth_map=(64, 656),
            player_exposure=(32,), home_teams=(96,), away_teams=(96,))
        require(all(value.shape == expected_shapes[name]
                    and value.dtype.str == ("<i8" if name in ("offense", "defense", "si", "scalar_ticks", "home_teams", "away_teams") else "<f8")
                    for name, value in design.items()), "fixed synthetic array shapes or dtypes changed")
        offense, defense, seconds, si = (design[name] for name in ("offense", "defense", "seconds", "si"))
        require(np.all(seconds > 0) and np.all((0 <= si) & (si < len(strata)))
                and tuple(sorted(set(offense.ravel()) | set(defense.ravel()))) == players
                and all(len(set(attacking)) == len(set(defending)) == 5
                        and not set(attacking) & set(defending)
                        for attacking, defending in zip(offense, defense, strict=True)),
                "fixed synthetic lineup or context rows invalid")
        positions = {player: index for index, player in enumerate(players)}
        indices = np.array([[positions[player] for player in attacking]
                            + [len(players) + positions[player] for player in defending]
                            for attacking, defending in zip(offense, defense, strict=True)])
        X = sparse.csr_matrix((np.ones(indices.size), (np.repeat(np.arange(len(indices)), 10), indices.ravel())),
                              shape=(len(indices), 2 * len(players)))
        exposure = np.asarray(X[:, :len(players)].T @ seconds).ravel()
        require(np.array_equal(exposure, design["player_exposure"])
                and np.array_equal(np.asarray(X[:, len(players):].T @ seconds).ravel(), exposure)
                and np.array_equal(design["u"], exposure / exposure.sum())
                and np.array_equal(design["truth_map"], design["truth_scalar"][:, None] * p + design["truth_shape"])
                and np.max(np.abs(design["truth_shape"].sum(axis=1))) <= 1e-12
                and all(np.max(np.abs(design["u"] @ design["truth_shape"][offset:offset + len(players)])) <= 1e-12
                        for offset in (0, len(players))), "fixed synthetic exposure, reference or truth contract changed")
        mu = 40 * (p + X @ design["truth_map"])
        require(np.all(mu > 0) and float(mu.min()) == annual["minimum_generating_rate"],
                "fixed synthetic generating rate changed")
        del mu
        design.update(players=players, strata=strata, X=X, e=seconds / 3600, p=p, W=W, centers=centers,
                      game_ids=tuple(range(96)), row_game_ids=np.repeat(np.arange(96), 100))
        # empty sparse response cells recover design information without
        # generating or materializing a native response matrix.
        references = AnnualReferences("unblocked_spatial", RESEARCH_SEASONS[year], year,
            prepared["source_protocol"]["sha256"], "synthetic:04c:information", players, strata,
            40., design["u"], p, exposure, np.zeros(656))
        rows = (dict(game_id=int(design["row_game_ids"][i]), offense=offense[i], defense=defense[i],
                     seconds=float(seconds[i]), stratum=strata[int(si[i])], counts=[])
                for i in range(len(seconds)))
        grouped = group_observations(rows, references, design["game_ids"])
        population = weighted_population(grouped, np.ones(len(grouped.game_ids)), references)
        H_raw = 40 * np.asarray(np.ones(len(grouped.game_ids)) @ grouped.H_e).reshape(X.shape[1], X.shape[1])
        dense = X.toarray()
        E = np.bincount(si, weights=design["e"], minlength=len(strata))
        direct_xbar = np.stack([design["e"][si == index] @ dense[si == index] / E[index]
                               for index in range(len(strata))])
        centered = dense - direct_xbar[si]
        residuals = dict(raw_information=float(np.max(np.abs(H_raw - 40 * dense.T @ (design["e"][:, None] * dense)))),
            information=float(np.max(np.abs(population.H - 40 * centered.T @ (design["e"][:, None] * centered)))),
            context_means=float(np.max(np.abs(population.xbar - direct_xbar))))
        require(max(residuals.values()) <= 1e-8, "grouped and direct fixed-design context information disagree")
        design.update(H_raw=H_raw, H=population.H, xbar=population.xbar, information_reconciliation=residuals)
        designs.append(design)
    return designs


def embed_recovery_information(design: dict, all_seen_player_ids: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """embed current information/reference weights; absent rows have no evidence."""
    players = design["players"]
    require(all_seen_player_ids == tuple(sorted(set(all_seen_player_ids)))
            and set(players).issubset(all_seen_player_ids), "saved all-seen player order changed")
    n = len(all_seen_player_ids)
    current = [all_seen_player_ids.index(player) for player in players]
    rows = current + [n + index for index in current]
    H_raw, H = np.zeros((2 * n, 2 * n)), np.zeros((2 * n, 2 * n))
    H_raw[np.ix_(rows, rows)], H[np.ix_(rows, rows)] = design["H_raw"], design["H"]
    u = np.zeros(n)
    u[current] = design["u"]
    return H_raw, H, u


def synthetic_population(design: dict, responses: np.ndarray, season_index: int,
                         source_protocol_sha: str, case_id: int, outer_id: int, *,
                         population_id: str | None = None) -> tuple[GroupedPopulation, AnnualReferences]:
    """contract one existing synthetic annual response into shared game moments."""
    require(type(season_index) is int and 0 <= season_index < len(RESEARCH_SEASONS)
            and responses.shape == (len(design["seconds"]), 656) and np.isfinite(responses).all(),
            "invalid fixed synthetic annual response")
    require(population_id is None or (isinstance(population_id, str) and population_id.startswith("synthetic:")),
            "synthetic population requires an explicit synthetic identity")
    references = AnnualReferences("unblocked_spatial", RESEARCH_SEASONS[season_index], season_index,
        source_protocol_sha, population_id if population_id is not None else
        f"synthetic:04c:{case_id}:{outer_id}:unblocked_spatial", design["players"],
        design["strata"], 40., design["u"].copy(), design["p"].copy(), design["player_exposure"].copy(), responses.sum(axis=0))
    rows = (dict(game_id=int(design["row_game_ids"][i]), offense=design["offense"][i], defense=design["defense"][i],
                 seconds=float(design["seconds"][i]), stratum=design["strata"][int(design["si"][i])], counts=responses[i])
            for i in range(len(responses)))
    return group_observations(rows, references, design["game_ids"]), references


def statistic_digest(population: RevisionPopulation) -> str:
    """the original 04c ordered unit-weight statistic identity."""
    return ordered_array_digest({name: np.asarray(getattr(population, name)) for name in
        ("H", "T", "yy", "shape_yy", "xbar", "ybar", "stratum_weight", "u", "p")})


def exposure_centering(u: np.ndarray) -> np.ndarray:
    """the role-wise exposure gauge; carried-only player rows have zero weight."""
    require(u.ndim == 1 and len(u) > 0 and np.isfinite(u).all() and np.all(u >= 0)
            and abs(float(u.sum()) - 1) <= 1e-12, "invalid exposure-centering reference")
    return np.kron(np.eye(2), np.eye(len(u)) - np.ones((len(u), 1)) * u)


def likelihood_spectrum(H: np.ndarray) -> tuple:
    """04d's likelihood rank and declared cutoff-sensitivity calculation."""
    require(H.ndim == 2 and H.shape[0] == H.shape[1] and len(H) > 0 and np.isfinite(H).all(),
            "likelihood information must be a finite nonempty square matrix")
    values, vectors = np.linalg.eigh((H + H.T) / 2)
    tau = 100 * len(H) * np.finfo(float).eps * max(float(values[-1]), 0.)
    require(float(values[0]) >= -tau, "likelihood information has a negative eigenvalue below -tau")
    masks = [values > factor * tau for factor in (.1, 1., 10.)]
    return values, vectors, tau, masks


def contrast_information(L: np.ndarray, D: np.ndarray, spectrum=None) -> list[dict]:
    """evaluate columns of already centered/aligned contrasts in one eigensystem."""
    require(L.ndim == 2 and L.shape[0] == L.shape[1] and len(L) > 0 and np.isfinite(L).all()
            and D.ndim == 2 and D.shape[0] == len(L) and np.isfinite(D).all(),
            "contrasts differ from ordered finite likelihood information")
    values, vectors, tau, masks = likelihood_spectrum(L) if spectrum is None else spectrum
    require(values.shape == (len(L),) and vectors.shape == L.shape and len(masks) == 3
            and all(mask.shape == values.shape and mask.dtype == np.dtype(bool) for mask in masks),
            "likelihood spectrum differs from ordered information")
    norms = np.linalg.norm(D, axis=0)
    statuses, nulls, precisions = [], [], []
    for index, mask in enumerate(masks):
        if index and np.array_equal(mask, masks[index-1]):
            statuses.append(statuses[-1])
            nulls.append(nulls[-1])
            precisions.append(precisions[-1])
            continue
        retained = vectors[:, mask]
        projected = retained.T @ D
        residuals = np.linalg.norm(D-retained @ projected, axis=0)
        null = np.divide(residuals, norms, out=np.zeros_like(norms), where=norms != 0)
        statuses.append(["zero_functional" if norm == 0 else "not_estimable" if value > 1e-8 else "available"
                         for norm, value in zip(norms, null, strict=True)])
        nulls.append(null)
        precisions.append(np.sum(projected**2/values[mask, None], axis=0))
    ranks = [int(mask.sum()) for mask in masks]
    results = []
    for column, norm in enumerate(norms):
        cutoff_statuses = [status[column] for status in statuses]
        stable = len(set(cutoff_statuses)) == 1 and len(set(ranks)) == 1
        status = cutoff_statuses[1] if stable else "numerically_unresolved"
        results.append(dict(status=status, rank=ranks[1], dimension=len(L), nullity=len(L)-ranks[1],
            tau=tau, rank_at_tau_factors=ranks, null_projection=float(nulls[1][column]),
            null_at_tau_factors=[float(null[column]) for null in nulls], status_at_tau_factors=cutoff_statuses,
            centered_functional_norm=float(norm),
            contrast_information_inverse=float(precisions[1][column]) if status == "available" else None))
    return results


def centered_estimability(H: np.ndarray, P: np.ndarray, c: np.ndarray, *, spectrum=None) -> dict:
    """test a centered functional against likelihood information, never its prior."""
    require(P.shape == H.shape and c.shape == (len(H),)
            and np.isfinite(P).all() and np.isfinite(c).all(),
            "centered functional differs from ordered likelihood information")
    return contrast_information(H, (P.T @ c)[:, None], spectrum)[0]


def identifiable_recovery_operator(
    H: np.ndarray, u: np.ndarray, player_ids: tuple[int, ...], *,
    inseparable_groups: tuple[tuple[int, ...], ...], expected_rank: int | None = None,
) -> tuple[np.ndarray, dict]:
    """the full likelihood-identified, exposure-centered player metric and entity audit."""
    n = len(player_ids)
    members = [player for group in inseparable_groups for player in group]
    require(player_ids == tuple(sorted(set(player_ids))) and n > 0 and H.shape == (2*n, 2*n)
            and u.shape == (n,) and len(members) == len(set(members))
            and all(len(group) > 1 and group == tuple(sorted(set(group)))
                    and set(group).issubset(player_ids) for group in inseparable_groups),
            "identifiable recovery player order or inseparable groups differ")
    P = exposure_centering(u)
    spectrum = likelihood_spectrum(H)
    values, vectors, tau, masks = spectrum
    ranks = [int(mask.sum()) for mask in masks]
    require(len(set(ranks)) == 1 and (expected_rank is None or ranks[1] == expected_rank),
            "identifiable recovery likelihood rank is unstable or differs from its declared target")
    E = vectors[:, masks[1]] @ vectors[:, masks[1]].T
    J = P @ E
    by_player = {player: group for group in inseparable_groups for player in group}
    entity_rows, entities, weights, nulls, differences = [], [], [], [], []
    for role_index, role in enumerate(("offense", "defense")):
        offset = role_index * n
        common = np.zeros(2*n)
        common[offset:offset+n] = 1
        nulls.append(common)
        for player in player_ids:
            group = by_player.get(player, (player,))
            if player != group[0]:
                continue
            row = np.zeros(2*n)
            row[[offset + player_ids.index(member) for member in group]] = 1 / len(group)
            centered = row @ P
            status = centered_estimability(H, P, row, spectrum=spectrum)
            require(status["status"] == "available", "declared recovery entity is not likelihood estimable")
            entity_rows.append(centered)
            weights.append(len(group))
            entities.append(dict(role=role, players=list(group), weight=len(group), status="available"))
            for member in group[1:]:
                difference = np.zeros(2*n)
                difference[offset + player_ids.index(group[0])] = 1
                difference[offset + player_ids.index(member)] = -1
                nulls.append(difference)
                status = centered_estimability(H, P, difference, spectrum=spectrum)
                require(status["status"] == "not_estimable", "inseparable player difference became estimable")
                differences.append(dict(role=role, players=[group[0], member], status="not_estimable",
                                        null_projection=status["null_projection"]))
    entity_operator = np.stack(entity_rows)
    null_basis = np.stack(nulls, axis=1)
    expected_nullity = null_basis.shape[1]
    null_residual = float(np.linalg.norm(H @ null_basis, ord=2) / max(1., np.linalg.norm(H, ord=2)))
    annihilation = float(np.linalg.norm(J @ null_basis, ord=2))
    metric = entity_operator.T @ (np.asarray(weights)[:, None] * entity_operator)
    equivalence = float(np.linalg.norm(J.T @ J - metric, ord=2) / max(1., np.linalg.norm(metric, ord=2)))
    _, singular, right = np.linalg.svd(J, full_matrices=False)
    rank = int(np.count_nonzero(singular > 1e-8))
    row_projector = right[:rank].T @ right[:rank]
    span = float(np.linalg.norm(row_projector - E, ord=2))
    require(2*n - ranks[1] == expected_nullity and rank == ranks[1]
            and null_residual <= 1e-10 and annihilation <= 1e-8
            and equivalence <= 1e-8 and span <= 1e-8,
            "identifiable recovery entity metric, null space or complete span differs")
    return J, dict(rank=ranks[1], dimension=2*n, denominator=2*n, tau=tau,
        rank_at_tau_factors=ranks, cutoff_factors=[.1, 1., 10.], entities=entities,
        entity_operator=entity_operator.tolist(), entity_weights=weights,
        inseparable_differences=differences, expected_nullity=expected_nullity,
        likelihood_null_relative_residual=null_residual, null_annihilation_residual=annihilation,
        entity_metric_relative_residual=equivalence, row_span_residual=span,
        positive_eigenvalue_minimum=float(values[masks[1]].min()))


REVISION_RULES = {
    "blocks": {
        "all_attempts": ["volume"],
        "unblocked_spatial": ["volume", "shape"],
        "shape_rank": 655,
        "volume_response_covariance": "p_p_transpose",
        "shape_response_covariance": "diag_p_minus_p_p_transpose",
        "prior": "independent_volume_shape_full_row_covariance",
        "annual_transition": "age_neutral_complete_mean_covariance",
    },
    "scale": {
        "variance_bounds": [1e-8, 1.0],
        "coarse_exponents": list(np.arange(-8, 0.1, 0.5)),
        "refinement": {
            "method": "bounded",
            "xatol": 1e-4,
            "maxiter": 40,
            "bracket": "best_interior_coarse_neighbors",
            "repetitions": 1,
        },
        "ties": "smaller_variance",
        "volume_objective": "matched_scalar_restricted_gaussian_marginal_likelihood",
        "shape_objective": "rank_655_zero_sum_restricted_gaussian_marginal_likelihood",
        "solve_relative_residual_max": 1e-8,
    },
    "references": {
        "r": "original_annual_team_rate",
        "u": "original_annual_admitted_player_exposure",
        "p": "corrected_04a_positive_first_season_native_shares",
        "fixed_across_refits": True,
        "source_population_identity": "unchanged_04a_population_id",
    },
    "seeds": {
        "bit_generator": "PCG64",
        "design": 40400,
        "response": 40420,
        "synthetic_refit": 40421,
        "real_refit": 40422,
        "paired_error": 40423,
        "index_base": 0,
        "order": ["sorted_game", "stint", "direction", "native_cell"],
    },
    "intervals": {
        "level": 0.95,
        "working": "gaussian_conditional",
        "refit": "basic_game_refit",
        "quantile_method": "linear",
        "weights": "independent_Exp1_normalized_per_inventory_season",
        "reference_uncertainty": False,
        "failed_draw_replacement": False,
        "exact_duplicate_guard": "not_data_identified",
    },
    "generator": {
        "cases": ["gaussian", "game_pace"],
        "design": "04a_paired",
        "teams": 4,
        "skaters_per_team": 8,
        "games_per_season": 96,
        "stints_per_game": 50,
        "seasons": 5,
        "native_cells": 656,
        "references": {"unblocked": 40, "all_attempts": 55},
        "paired_players": [26, 31],
        "entrants": [32, 33],
        "returner": 8,
        "change_player": 1,
        "shape_players": {"broad": [3, 4], "local": [18, 19]},
        "shape_amplitude": 0.1,
        "pace": {"shape": 2, "scale": 0.5},
        "centering": "known_design_exposure_before_counts",
        "positive_means": "required_without_clipping_or_redraw",
    },
    "criteria": {
        "shape": "paired_95_percent_percentile_interval_lower_gt_zero",
        "coverage": {
            "method": "wilson_two_sided_95",
            "floor": 0.90,
            "nomination_cells": 12,
        },
        "false_claim": {
            "method": "wilson_two_sided_95",
            "ceiling": 0.10,
            "nomination_cells": 8,
            "denominator": "all_200_outer_replicates",
            "meaningful_band": 0.05,
            "strict": True,
        },
        "null": "no_empirical_claim_with_exact_null_component",
        "numerical_control_tolerance": 1e-8,
        "conditional_shape_resolution_max": 1e-4,
        "admission": "not_admitted",
        "handoff": None,
    },
    "budgets": {
        "real_refits": 200,
        "outer_per_case": 200,
        "inner_refits": 200,
        "paired_error_resamples": 10000,
        "new_shape_fits": 5,
        "replayed_control_states": 10,
    },
}
REVISION_BASELINE = {
    "path": "/Volumes/Expansion/hockey-stats/runs/attribution-04a-20261014-02/prepared/prepared.json",
    "sha256": "b771cdc1784a72cf0db6be47b9eb0f597af542bb9cace1f339ba40002265cd8a",
}
REVISION_BASELINE_FITS = {
    "path": "/Volumes/Expansion/hockey-stats/runs/attribution-04a-20261014-02/inputs/chains.json",
    "sha256": "dc68f420858d55b3b141cb5e0e0f2a2f1a3ff34795a9e6971a93870aa0bac325",
}


def validate_revision_protocol(protocol: dict) -> None:
    """accept the frozen study, or explicitly reduced fixture budgets only."""
    required = {
        "schema_version",
        "kind",
        "purpose",
        "implementation",
        "spec_snapshot",
        "baseline_prepared",
        "baseline_result",
        "baseline_fits",
        "seasons",
        "populations",
        "output_root",
        *REVISION_RULES,
    }
    require(
        type(protocol) is dict
        and set(protocol) == required
        and type(protocol["schema_version"]) is int
        and protocol["schema_version"] == 2
        and protocol["kind"] == "attribution_revision_protocol"
        and protocol["purpose"] in ("research", "fixture_exercise"),
        "invalid revision protocol",
    )
    require(
        protocol["populations"] == list(POPULATIONS)
        and protocol["seasons"] == list(RESEARCH_SEASONS),
        "revision years/populations differ from study",
    )
    for name, expected in REVISION_RULES.items():
        actual = protocol[name]
        if name == "budgets" and protocol["purpose"] == "fixture_exercise":
            require(
                type(actual) is dict
                and set(actual) == set(expected)
                and all(
                    type(actual[key]) is int and 0 < actual[key] <= expected[key]
                    for key in expected
                ),
                "fixture budgets must be explicit positive reductions",
            )
        else:
            require(actual == expected, "frozen revision rules differ: " + name)
    for name in ("spec_snapshot", "baseline_prepared"):
        linked_path(protocol[name])
    for name in ("baseline_result", "baseline_fits"):
        if protocol[name] is not None:
            linked_path(protocol[name])
        else:
            require(
                protocol["purpose"] == "fixture_exercise",
                "research requires corrected " + name,
            )
    require(
        type(protocol["output_root"]) is str
        and Path(protocol["output_root"]).is_absolute(),
        "revision output root must be absolute",
    )
    if protocol["purpose"] == "research":
        require(
            protocol["baseline_prepared"] == REVISION_BASELINE
            and protocol["baseline_fits"] == REVISION_BASELINE_FITS,
            "research requires the exact corrected 04a preparation and controls",
        )


def _load_arrays(reference: ArtifactReference, shapes: dict) -> dict[str, np.ndarray]:
    return _read_arrays(linked_path(reference), shapes)


def _read_arrays(path: Path, shapes: dict) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as source:
        require(
            set(source.files) == set(shapes), "array names disagree with bound shapes"
        )
        arrays = {name: source[name] for name in source.files}
    require(
        all(
            list(value.shape) == shapes[name] and np.isfinite(value).all()
            for name, value in arrays.items()
        ),
        "invalid bound numerical array",
    )
    return arrays


def read_revision_prepared(path: Path | str) -> dict:
    """read schema 2 only; source schema 1 is an explicitly bound control."""
    document = read_json(Path(path).resolve(strict=True))
    require(
        type(document) is dict
        and type(document.get("schema_version")) is int
        and document["schema_version"] == 2
        and document.get("kind") == "attribution_revision_prepared",
        "expected revision prepared manifest",
    )
    protocol = read_json(linked_path(document["protocol"]))
    validate_revision_protocol(protocol)
    require(
        document["purpose"] == protocol["purpose"]
        and document["seasons"] == protocol["seasons"]
        and document["populations"] == protocol["populations"]
        and document["baseline_prepared"] == protocol["baseline_prepared"]
        and (
            document["purpose"] == "fixture_exercise"
            or document["implementation"] == protocol["implementation"]
        ),
        "revision preparation differs from frozen evidence",
    )
    baseline = read_json(linked_path(document["baseline_prepared"]))
    for name in (
        "population_ids",
        "seasons",
        "target_season",
        "populations",
        "grid",
        "design",
        "games_by_season",
        "pairs",
        "ledgers",
    ):
        require(
            document[name] == baseline[name],
            "revision changed source evidence: " + name,
        )
    expected = [
        (population, season)
        for population in POPULATIONS
        for season in document["seasons"]
    ]
    require(
        [(row["population"], row["season"]) for row in document["annual"]] == expected,
        "revision annual population order differs",
    )
    controls = []
    if protocol["baseline_fits"] is not None:
        chains = read_json(linked_path(protocol["baseline_fits"]))
        controls = [
            {
                "benchmark": row["benchmark"],
                "season": row["season"],
                "state": row["reference"],
            }
            for row in chains["annual"]
        ]
    require(
        document["baseline_controls"] == controls,
        "revision control identities differ from frozen evidence",
    )
    for original, annual in zip(baseline["annual"], document["annual"], strict=True):
        require(
            all(annual[name] == value for name, value in original.items()),
            "revision changed original annual evidence",
        )
        require(
            annual["game_ids"] == sorted(set(annual["game_ids"]))
            and len(annual["game_ids"])
            == document["games_by_season"][annual["season"]],
            "revision game inventory differs",
        )
    return document


def read_recovery_prepared(path: Path | str) -> dict:
    """active 04c source/model boundary; the original preparation keeps its own protocol."""
    from .artifacts import load_arrays, read_artifact

    document = read_artifact(path, "attribution_recovery_prepared")
    source_path = linked_path(document["source_prepared"])
    source = read_revision_prepared(source_path)
    protocol = read_artifact(linked_path(document["model_protocol"]), "attribution_recovery_protocol")
    diagnosis = read_artifact(linked_path(document["diagnosis"]), "attribution_recovery_diagnosis")
    require(document["purpose"] == protocol["purpose"] == diagnosis["purpose"] == source["purpose"]
            and document["source_prepared"] == protocol["source_prepared"] == diagnosis["source_prepared"]
            and document["source_protocol"] == protocol["source_protocol"] == source["protocol"]
            and document["diagnosis"] == protocol["diagnosis"]
            and diagnosis["status"] == "complete" and diagnosis["gate"]["status"] == "proceed"
            and document["seasons"] == source["seasons"] == protocol["seasons"]
            and document["source_population_ids"] == source["population_ids"]
            and document["grid"] == source["grid"],
            "recovery preparation changed diagnosed source, model or reference identity")
    require(document["original_annual"] == [
        dict(population=row["population"], season=row["season"], references=row["references"], rows=row["rows"])
        for row in source["annual"]], "recovery preparation changed original annual references or ledgers")
    if document["purpose"] == "research":
        require(document["implementation"] == protocol["implementation"],
                "recovery preparation producer differs from frozen model")
        require(Path(path).resolve(strict=True).is_relative_to(Path(protocol["output_root"]))
                and Path(protocol["output_root"]).is_relative_to(Path("/Volumes/Expansion/hockey-stats/runs")),
                "research preparation escaped frozen external output root")
    linked_path(document["basis"])
    require(document["basis_shapes"] == [dict(name="B", shape=[656, 40], dtype="<f8"),
            dict(name="p", shape=[656], dtype="<f8"), dict(name="eigenvalues", shape=[40], dtype="<f8")],
            "recovery basis ordered shapes differ")
    basis_arrays = load_arrays(dict(arrays=document["basis"], array_shapes=document["basis_shapes"]))
    first_spatial = next(row for row in source["annual"]
                         if row["population"] == "unblocked_spatial" and row["season"] == source["seasons"][0])
    references = _load_arrays(first_spatial["references"], first_spatial["reference_shapes"])
    require(np.array_equal(basis_arrays["p"], references["p"]),
            "recovery basis changed the original native reference")
    return document


def load_grouped_population(
    prepared: Path | str, benchmark: str, season: str
) -> tuple[GroupedPopulation, AnnualReferences]:
    """load one annual game-moment block and its fixed reference contract."""
    document = read_revision_prepared(prepared)
    matches = [
        row
        for row in document["annual"]
        if row["population"] == benchmark and row["season"] == season
    ]
    require(
        len(matches) == 1 and matches[0]["status"] == "prepared",
        "revision annual population unavailable",
    )
    annual = matches[0]
    arrays = _load_arrays(annual["grouped"], annual["grouped_shapes"])
    ref = _load_arrays(annual["references"], annual["reference_shapes"])
    n, k, s, g = (
        2 * len(annual["players"]),
        len(ref["response_counts"]),
        len(annual["strata"]),
        len(annual["game_ids"]),
    )
    widths = {"H_e": n * n, "T_raw": n * k, "stratum_x": s * n, "stratum_n": s * k}
    matrices = {
        name: sparse.csr_matrix(
            (
                arrays[name + "_data"],
                arrays[name + "_indices"],
                arrays[name + "_indptr"],
            ),
            shape=(g, width),
        )
        for name, width in widths.items()
    }
    grouped = GroupedPopulation(
        tuple(annual["game_ids"]),
        matrices["H_e"],
        matrices["T_raw"],
        arrays["stratum_e"],
        matrices["stratum_x"],
        matrices["stratum_n"],
        arrays["Q_t"],
        arrays.get("Q_h"),
        tuple(annual["membership_signatures"]),
        annual["row_count"],
    )
    references = AnnualReferences(
        benchmark,
        season,
        document["seasons"].index(season),
        document["protocol"]["sha256"],
        document["population_ids"][benchmark],
        tuple(annual["players"]),
        tuple(tuple(value) for value in annual["strata"]),
        annual["r"],
        ref["u"],
        ref.get("p"),
        ref["player_exposure"],
        ref["response_counts"],
    )
    return grouped, references


def load_revision_population(
    prepared: Path | str, benchmark: str, season: str
) -> RevisionPopulation:
    """load the unit-weight likelihood without reading the original row files."""
    document = read_revision_prepared(prepared)
    matches = [
        row
        for row in document["annual"]
        if row["population"] == benchmark and row["season"] == season
    ]
    require(
        len(matches) == 1 and matches[0]["status"] == "prepared",
        "revision annual population unavailable",
    )
    annual = matches[0]
    values = _load_arrays(annual["statistics"], annual["statistic_shapes"])
    ref = _load_arrays(annual["references"], annual["reference_shapes"])
    return RevisionPopulation(
        benchmark,
        season,
        document["seasons"].index(season),
        document["protocol"]["sha256"],
        document["population_ids"][benchmark],
        tuple(annual["players"]),
        tuple(tuple(row) for row in annual["strata"]),
        values["H"],
        values["T"],
        float(values["yy"]),
        float(values["shape_yy"]) if "shape_yy" in values else None,
        annual["r"],
        values["xbar"],
        values["ybar"],
        values["stratum_weight"],
        ref["player_exposure"],
        ref["response_counts"],
        ref["u"],
        ref.get("p"),
    )


@dataclass(frozen=True)
class EmpiricalSource:
    """validated counted game moments and their original annual coordinate axes."""

    basis: "ShapeBasis"
    seasons: tuple[str, ...]
    grouped: tuple[GroupedPopulation, ...]
    references: tuple[AnnualReferences, ...]
    annual: tuple[dict, ...]
    game_dates: dict[str, str]
    game_coverage: dict[str, dict]
    source_identity: dict


@dataclass(frozen=True)
class EmpiricalTraining:
    """selected training moments; player exposure is seconds, rates are per hour."""

    likelihood: "ShapeCoefficientLikelihood"
    game_ids: tuple
    source_player_ids: tuple[int, ...]
    strata: tuple[tuple, ...]
    source_strata: tuple[tuple, ...]
    xbar: np.ndarray
    nbar: np.ndarray
    player_exposure: np.ndarray
    directed_hours: float
    response_counts: np.ndarray
    source_identity: dict


def _empirical_grouped(annual: dict, path: Path) -> GroupedPopulation:
    """decode raw moments only; response self energy is neither read nor invented."""
    names = ("stratum_e",) + tuple(name+suffix for name in
        ("H_e", "T_raw", "stratum_x", "stratum_n") for suffix in ("_data", "_indices", "_indptr"))
    with np.load(path, allow_pickle=False) as source:
        require(set(source.files) == set(annual["grouped_shapes"]), "empirical grouped archive members differ")
        arrays = {name: source[name] for name in names}
    require(all(list(value.shape) == annual["grouped_shapes"][name] and np.isfinite(value).all()
                for name, value in arrays.items()), "empirical grouped member shape or finiteness differs")
    g, n, s, k = len(annual["game_ids"]), 2*len(annual["players"]), len(annual["strata"]), 656
    matrices = {}
    for name, width in (("H_e", n*n), ("T_raw", n*k), ("stratum_x", s*n), ("stratum_n", s*k)):
        data, indices, indptr = (arrays[name+suffix] for suffix in ("_data", "_indices", "_indptr"))
        require(data.dtype == np.dtype("float64") and indices.dtype.kind in "iu" and indptr.dtype.kind in "iu"
                and data.ndim == indices.ndim == indptr.ndim == 1 and len(data) == len(indices)
                and indptr.shape == (g+1,) and indptr[0] == 0 and indptr[-1] == len(data)
                and np.all(indptr[1:] >= indptr[:-1]) and np.all((0 <= indices) & (indices < width))
                and np.all(data >= 0), "empirical sparse moment storage or nonnegative values differ: "+name)
        matrices[name] = sparse.csr_matrix((data, indices, indptr), shape=(g, width))
        require(matrices[name].has_canonical_format, "empirical sparse moments are not canonical: "+name)
    require(arrays["stratum_e"].dtype == np.dtype("float64") and arrays["stratum_e"].shape == (g, s)
            and np.all(arrays["stratum_e"] >= 0), "empirical context exposure differs")
    # response self energy is unavailable at this selected-array boundary.
    return GroupedPopulation(tuple(annual["game_ids"]), matrices["H_e"], matrices["T_raw"],
        arrays["stratum_e"], matrices["stratum_x"], matrices["stratum_n"], None, None,
        tuple(annual["membership_signatures"]), annual["row_count"])


def read_empirical_source(result_ref: ArtifactReference, basis_ref: ArtifactReference,
                          corpus_ref: ArtifactReference) -> EmpiricalSource:
    """read only the frozen corrected count chain, first-year basis and date inventory."""
    from .attribution import decode_shape_basis
    from .corpus_inputs import load_corpus

    require(result_ref["sha256"] == "d0c0f6a7af3888cd0d0920d152f322447a984cbc20edac596aa70f60dbb0f2de"
            and basis_ref == dict(path="/Volumes/Expansion/hockey-stats/runs/attribution-04c-20261016/prepared/basis.npz",
                                  sha256="67d7ee706f1d8d251cc68a0d22378e67e1961b2ac53fb764bfc0efdff11d43fc")
            and corpus_ref == dict(path="/Volumes/Expansion/hockey-stats/corpora/03m-20261010/20252026/corpus.json",
                                   sha256="8229fc6686fa03c4f6cc00d68d68aac1d1d2b83d6950d56eeebb7c9fc923fd43"),
            "empirical research requires its exact result, spatial basis and date corpus")
    checked = {}

    def path(reference):
        key = reference["path"]
        if key not in checked:
            checked[key] = (reference["sha256"], linked_path(reference))
        require(checked[key][0] == reference["sha256"], "empirical source binds conflicting file digests")
        return checked[key][1]

    result = read_json(path(result_ref))
    require(result["kind"] == "attribution_revision_result" and result["schema_version"] == 2
            and result["purpose"] == "research" and result["completion"] == "complete",
            "empirical source requires the completed corrected 04b result")
    clean_implementation(result["implementation"])
    clean_implementation(result["model_implementation"])
    prepared_ref = result["evidence"]["prepared"]
    require(prepared_ref == dict(path="/Volumes/Expansion/hockey-stats/runs/attribution-04b-20261015/prepared/prepared.json",
                                sha256="fbc40ab798493be6fcc7068ea52eb43831ad725fb89d7a4c87242f689cb7d17b"),
            "empirical source changed corrected preparation")
    prepared = read_json(path(prepared_ref))
    require(prepared["kind"] == "attribution_revision_prepared" and prepared["schema_version"] == 2
            and prepared["purpose"] == "research" and tuple(prepared["seasons"]) == RESEARCH_SEASONS,
            "empirical preparation kind, purpose or years differ")
    clean_implementation(prepared["implementation"])
    baseline_ref = prepared["baseline_prepared"]
    require(baseline_ref == REVISION_BASELINE, "empirical source changed original preparation")
    baseline = read_json(path(baseline_ref))
    require(baseline["kind"] == "attribution_prepared" and baseline["schema_version"] == 1
            and baseline["purpose"] == "research", "empirical original preparation identity differs")
    clean_implementation(baseline["implementation"])
    original_protocol = read_json(path(baseline["protocol"]))
    revision_protocol = read_json(path(prepared["protocol"]))
    clean_implementation(original_protocol["implementation"])
    clean_implementation(revision_protocol["implementation"])
    require(result["protocol"] == prepared["protocol"]
            and revision_protocol["baseline_prepared"] == baseline_ref
            and original_protocol["selection"] == baseline["selection"] == prepared["selection"]
            and original_protocol["seasons"] == baseline["seasons"] == prepared["seasons"]
            and baseline["design"] == prepared["design"]
            and all(original_protocol["design"][name] == value for name, value in baseline["design"].items())
            and original_protocol["design"]["spatial_response_covariance"] == "first_season_half_count_cell_shares"
            and original_protocol["design"]["half_count"] == .5
            and all(prepared["design"][name] is True for name in
                    ("paired_team_direction_masks", "zero_event_segments", "matched_spatial_exclusion")),
            "empirical source changed original population, direction masks or reference lineage")
    selection = read_json(path(baseline["selection"]))
    require(prepared["inputs"] == baseline["inputs"] and all(prepared[name] == baseline[name] for name in
            ("population_ids", "grid", "games_by_season", "target_season", "populations", "design_sha256")),
            "empirical preparation changed original source or coverage identity")
    bound_corpora = [{key: row[key] for key in ("path", "sha256")} for row in baseline["inputs"]
                    if row["kind"] == "corpus"]
    require(corpus_ref in bound_corpora and len(bound_corpora) == 5
            and selection["kind"] == "attribution_selection" and selection["schema_version"] == 1
            and selection["purpose"] == "research"
            and any(row["season"] == RESEARCH_SEASONS[-1] and row["corpus_path"] == corpus_ref["path"]
                    for row in selection["corpora"]),
            "empirical date corpus is absent from the frozen source selection")
    corpus_inputs = []
    corpus, inventory, _ = load_corpus(Path(corpus_ref["path"]).resolve(strict=True), corpus_inputs)
    require(corpus_inputs[0]["sha256"] == corpus_ref["sha256"]
            and corpus["reference"]["requested_season"] == RESEARCH_SEASONS[-1]
            and len(inventory) == 1312, "empirical final date corpus digest or admitted inventory differs")
    checked[corpus_ref["path"]] = (corpus_ref["sha256"], Path(corpus_ref["path"]))
    annual = tuple(row for row in prepared["annual"] if row["population"] == "unblocked_spatial")
    original = tuple(row for row in baseline["annual"] if row["population"] == "unblocked_spatial")
    require(tuple(row["season"] for row in annual) == tuple(row["season"] for row in original) == RESEARCH_SEASONS,
            "empirical annual spatial inventory differs")
    grouped, references = [], []
    for year, (row, old) in enumerate(zip(annual, original, strict=True)):
        require(all(row[name] == value for name, value in old.items()) and row["status"] == "prepared"
                and row["reason"] is None and row["players"] == sorted(set(row["players"]))
                and row["strata"] == sorted(map(list, set(map(tuple, row["strata"]))))
                and row["game_ids"] == sorted(set(row["game_ids"]))
                and len(row["game_ids"]) == baseline["games_by_season"][row["season"]],
                "empirical corrected annual axes, source identity or coverage differ")
        values = _read_arrays(path(row["references"]), row["reference_shapes"])
        references.append(AnnualReferences("unblocked_spatial", row["season"], year,
            baseline["protocol"]["sha256"], prepared["population_ids"]["unblocked_spatial"],
            tuple(row["players"]), tuple(map(tuple, row["strata"])), row["r"], values["u"], values["p"],
            values["player_exposure"], values["response_counts"]))
        grouped.append(_empirical_grouped(row, path(row["grouped"])))
    require(tuple(sorted(inventory)) == grouped[-1].game_ids,
            "empirical grouped inventory differs from all admitted games, including zero-time games")
    from .artifacts import rows

    coverage = {}
    for row in rows(path(baseline["ledgers"]["coverage"])):
        if row["season"] == RESEARCH_SEASONS[-1]:
            game = row["game_id"]
            require(game in inventory and game not in coverage, "empirical coverage game is absent or duplicated")
            coverage[game] = dict(row["populations"]["unblocked_spatial"], native_coverage=row["native_coverage"],
                score_failures=row["score_failures"], unknown_horizon_periods=row["unknown_horizon_periods"])
    require(set(coverage) == set(inventory), "empirical coverage does not include every admitted final game")
    for index, game in enumerate(grouped[-1].game_ids):
        directed_seconds = 3600*float(grouped[-1].stratum_e[index].sum())
        counts = float(grouped[-1].stratum_n[index].sum())
        require(math.isclose(directed_seconds, 2*coverage[game]["retained_seconds"], rel_tol=0, abs_tol=1e-7)
                and counts == coverage[game]["retained_attempts"],
                "empirical game moments disagree with original matched spatial coverage: "+game)
    with np.load(path(basis_ref), allow_pickle=False) as source:
        basis_arrays = {name: source[name] for name in source.files}
    basis = decode_shape_basis(basis_arrays,
        basis_sha256="649a49ecba19de5df609d6980d9de76491afa13e9108df0d8e6500659886cc51")
    require(all(np.array_equal(reference.p, basis.p) for reference in references)
            and np.array_equal(references[0].p, (references[0].response_counts+.5)
                               /(references[0].response_counts.sum()+.5*656)),
            "empirical spatial reference is not the wholly training first-season half-count reference")
    source_identity = dict(source_result=result_ref, prepared=prepared_ref, baseline_prepared=baseline_ref,
        basis=basis_ref, corpus=corpus_ref, original_protocol=baseline["protocol"],
        revision_protocol=prepared["protocol"], selection=baseline["selection"],
        basis_sha256=basis.sha256, first_reference_season=RESEARCH_SEASONS[0],
        population_id=prepared["population_ids"]["unblocked_spatial"],
        coverage_ledger=baseline["ledgers"]["coverage"],
        decoded_grouped_members=["H_e", "T_raw", "stratum_e", "stratum_x", "stratum_n"])
    return EmpiricalSource(basis, RESEARCH_SEASONS, tuple(grouped), tuple(references), annual,
        {game: row["game_date"] for game, row in inventory.items()}, coverage, source_identity)


def _selected_training(grouped: GroupedPopulation, references: AnnualReferences,
                       train_ids: tuple, basis: "ShapeBasis") -> tuple:
    """contract selected whole games, estimating every annual reference from training."""
    from .attribution import ShapeCoefficientLikelihood

    ids = tuple(train_ids)
    n, s, k = 2*len(references.player_ids), len(references.strata), len(basis.p)
    require(bool(ids) and ids == tuple(sorted(set(ids))) and set(ids).issubset(grouped.game_ids)
            and grouped.game_ids == tuple(sorted(set(grouped.game_ids)))
            and grouped.H_e.shape == (len(grouped.game_ids), n*n)
            and grouped.T_raw.shape == (len(grouped.game_ids), n*k)
            and grouped.stratum_x.shape == (len(grouped.game_ids), s*n)
            and grouped.stratum_n.shape == (len(grouped.game_ids), s*k)
            and grouped.stratum_e.shape == (len(grouped.game_ids), s)
            and references.benchmark == "unblocked_spatial" and np.array_equal(references.p, basis.p),
            "empirical training games, native reference or moment axes differ")
    positions = {game: index for index, game in enumerate(grouped.game_ids)}
    rows = np.array([positions[game] for game in ids])
    E = grouped.stratum_e[rows].sum(axis=0)
    C = np.asarray(grouped.stratum_x[rows].sum(axis=0)).reshape(s, n)
    N = np.asarray(grouped.stratum_n[rows].sum(axis=0)).reshape(s, k)
    A = np.asarray(grouped.H_e[rows].sum(axis=0)).reshape(n, n)
    K = np.asarray(grouped.T_raw[rows].sum(axis=0)).reshape(n, k)
    require(all(np.isfinite(value).all() and np.all(value >= 0) for value in (A, C, E, N, K))
            and np.array_equal(N, np.rint(N)) and np.array_equal(K, np.rint(K)),
            "empirical training requires finite nonnegative counted moments")
    hours = float(E.sum())
    require(hours > 0 and float(N.sum()) > 0, "empirical training has no retained exposure or attempts")
    role_exposure = np.diag(A)
    require(np.allclose(role_exposure[:n//2], role_exposure[n//2:], rtol=1e-12, atol=1e-12)
            and np.allclose(A, A.T, rtol=1e-12, atol=1e-12),
            "empirical training changed paired player exposure or moment symmetry")
    active = np.flatnonzero(role_exposure[:n//2] > 0)
    columns = np.r_[active, n//2+active]
    contexts = np.flatnonzero(E > 0)
    omitted = E == 0
    require(not np.any(C[omitted]) and not np.any(N[omitted]),
            "empirical zero-exposure context contains player exposure or attempts")
    require(np.allclose(C.sum(axis=1), 10*E, rtol=1e-10, atol=1e-10)
            and np.allclose(A.sum(axis=1), 10*role_exposure, rtol=1e-10, atol=1e-10)
            and np.allclose(K.sum(axis=0), 10*N.sum(axis=0), rtol=0, atol=1e-8),
            "empirical training player/context count or exposure accounting differs")
    A, C, K = A[np.ix_(columns, columns)], C[np.ix_(contexts, columns)], K[columns]
    E, N = E[contexts], N[contexts]
    xbar, nbar, r = C/E[:, None], N/E[:, None], float(N.sum()/hours)
    H = r*(A-C.T @ xbar)
    T = K-C.T @ nbar
    Q = (T-T.sum(axis=1)[:, None]*basis.p) @ basis.B
    exposure = 3600*role_exposure[active]
    u = exposure/exposure.sum()
    player_ids = tuple(references.player_ids[index] for index in active)
    strata = tuple(references.strata[index] for index in contexts)
    identity = dict(population_id=references.population_id, source_protocol_sha256=references.protocol_sha256,
        season=references.season, training_game_ids=list(ids), source_player_ids=list(references.player_ids),
        source_contexts=list(map(list, references.strata)), basis_sha256=basis.sha256,
        references="selected_training_rate_exposure_context; fixed_first_season_spatial_reference")
    if grouped.correction_identity is not None:
        identity["source_correction"] = grouped.correction_identity
    likelihood = ShapeCoefficientLikelihood(references.season, player_ids, H, Q, u, r, basis, identity)
    require(np.isfinite(H).all() and np.isfinite(Q).all() and Q.shape == (2*len(active), 40)
            and np.allclose(xbar[:, :len(active)].sum(axis=1), 5., rtol=0, atol=1e-10)
            and np.allclose(xbar[:, len(active):].sum(axis=1), 5., rtol=0, atol=1e-10),
            "empirical training finite coefficient score or five-player context means differ")
    return (EmpiricalTraining(likelihood, ids, references.player_ids, strata, references.strata,
        xbar, nbar, exposure, hours, N.sum(axis=0), identity),
        dict(rows=rows,T=T,context_totals=N.sum(axis=1),context_exposure=E))


def empirical_training(grouped: GroupedPopulation, references: AnnualReferences,
                       train_ids: tuple, basis: "ShapeBasis") -> EmpiricalTraining:
    """derive the shape likelihood from selected raw counted-game moments."""
    return _selected_training(grouped,references,train_ids,basis)[0]


def empirical_game_moments(grouped: GroupedPopulation, references: AnnualReferences, game_id) -> dict:
    """one game's sparse raw moments on the complete original player/context axes."""
    require(game_id in grouped.game_ids, "empirical evaluation game absent from grouped inventory")
    index = grouped.game_ids.index(game_id)
    n, s, k = 2*len(references.player_ids), len(references.strata), len(references.response_counts)
    return dict(E=grouped.stratum_e[index], C=grouped.stratum_x[index].reshape((s, n)).tocsr(),
        A=grouped.H_e[index].reshape((n, n)).tocsr(), N=grouped.stratum_n[index].toarray().reshape(s, k),
        K=grouped.T_raw[index].reshape((n, k)).tocsr(), p=references.p,
        context_ids=references.strata, player_ids=references.player_ids)


def read_empirical_fixture(path: Path | str) -> EmpiricalSource:
    """read literal counted rows; fixture evidence cannot enter the research reader."""
    from .attribution import decode_shape_basis
    from .chance_cli import identity

    path = Path(path).resolve(strict=True)
    document = read_json(path)
    require(document["kind"] == "attribution_empirical_fixture" and document["schema_version"] == 1
            and document["purpose"] == "fixture_exercise" and len(document["years"]) == 3
            and document["seasons"] == [year["season"] for year in document["years"]],
            "empirical fixture requires three explicit synthetic counted seasons")

    def reference(value):
        return dict(path=str((path.parent/value["path"]).resolve(strict=True)), sha256=value["sha256"])

    for value in document["sources"].values():
        linked_path(reference(value))
    basis_ref = reference(document["basis"]["arrays"])
    with np.load(linked_path(basis_ref), allow_pickle=False) as source:
        basis = decode_shape_basis({name: source[name] for name in source.files},
            basis_sha256=document["basis"]["basis_sha256"])
    data_ref = reference(document["arrays"])
    arrays = load_arrays(dict(arrays=data_ref, array_shapes=document["array_shapes"]))
    grouped, references, annual, coverage = [], [], [], {}
    fixture_ref = identity(path)
    for year, row in enumerate(document["years"]):
        prefix = f"year_{year}_"
        offense, defense, seconds, si, games, counts = (arrays[prefix+name] for name in
            ("offense", "defense", "seconds", "si", "row_game_ids", "counts"))
        players, strata, game_ids = tuple(row["players"]), tuple(map(tuple, row["strata"])), tuple(row["game_ids"])
        m, n = len(seconds), len(players)
        require(players == tuple(sorted(set(players))) and strata == tuple(sorted(set(strata)))
                and game_ids == tuple(sorted(set(game_ids))) and m > 0 and m % 2 == 0
                and offense.shape == defense.shape == (m, 5) and counts.shape == (m, 656)
                and games.shape == si.shape == seconds.shape == (m,)
                and all(value.dtype == np.dtype("int64") for value in (offense, defense, si, games, counts))
                and seconds.dtype == np.dtype("float64") and np.all(seconds > 0)
                and np.array_equal(seconds, np.rint(seconds)) and np.all(counts >= 0)
                and np.all((0 <= si) & (si < len(strata)))
                and np.all(np.diff(np.sort(offense, axis=1), axis=1) > 0)
                and np.all(np.diff(np.sort(defense, axis=1), axis=1) > 0)
                and not np.any(offense[:, :, None] == defense[:, None, :])
                and np.array_equal(offense[::2], defense[1::2])
                and np.array_equal(defense[::2], offense[1::2])
                and np.array_equal(seconds[::2], seconds[1::2]) and np.array_equal(games[::2], games[1::2])
                and np.all(games[1:] >= games[:-1]) and set(map(str, games)).issubset(game_ids)
                and tuple(np.unique(np.r_[offense.ravel(), defense.ravel()]).tolist()) == players,
                "empirical fixture changed nonnegative integer counts, paired rows or ordered axes")
        exposure = np.array([seconds[(offense == player).any(axis=1)].sum() for player in players])
        require(np.all(exposure > 0), "empirical fixture source player has no exposure")
        response_counts = counts.sum(axis=0).astype(float)
        refs = AnnualReferences("unblocked_spatial", row["season"], year, fixture_ref["sha256"],
            data_ref["sha256"], players, strata, float(response_counts.sum()/(seconds.sum()/3600)),
            exposure/exposure.sum(), basis.p, exposure, response_counts)
        observations = (dict(game_id=str(games[i]), offense=offense[i].tolist(), defense=defense[i].tolist(),
            seconds=float(seconds[i]), stratum=strata[int(si[i])], counts=counts[i]) for i in range(m))
        moments = group_observations(observations, refs, game_ids)
        references.append(refs)
        grouped.append(moments)
        totals = dict(supported_seconds=float(seconds.sum()/2), retained_seconds=float(seconds.sum()/2),
            excluded_seconds=0., recognized_attempts=int(counts.sum()), retained_attempts=int(counts.sum()),
            excluded_attempts=0, measured_games=len(game_ids), unresolved_membership_seconds=0,
            unknown_horizon_games=0)
        annual.append(dict(row, coverage=totals, references=data_ref, grouped=data_ref,
            source="explicitly synthetic integer counted rows", team_seconds=float(seconds.sum()),
            total_count=int(counts.sum())))
        if year == 2:
            for game, E, N in zip(game_ids, moments.stratum_e, np.asarray(moments.stratum_n.sum(axis=1)).ravel(), strict=True):
                sec = 1800*float(E.sum())
                coverage[game] = dict(supported_seconds=sec, retained_seconds=sec, excluded_seconds=0.,
                    recognized_attempts=int(N), retained_attempts=int(N), excluded_attempts=0,
                    unresolved_membership_seconds=0, unknown_horizon_periods=[], score_failures=[],
                    source="explicitly synthetic counted stints")
    dates = {game: document["game_dates"][game] for game in grouped[-1].game_ids}
    require(all(isinstance(value, str) for value in dates.values()), "empirical fixture dates are missing")
    source_identity = dict(fixture=fixture_ref, arrays=data_ref, basis=basis_ref,
        basis_sha256=basis.sha256, first_reference_season=document["seasons"][0],
        population_id=data_ref["sha256"], source="explicitly synthetic integer counted stints")
    return EmpiricalSource(basis, tuple(document["seasons"]), tuple(grouped), tuple(references),
        tuple(annual), dates, coverage, source_identity)


def complete_grouped(annual: dict, path: Path) -> GroupedPopulation:
    """decode recorded moments with the scalar self energy required for volume."""
    from dataclasses import replace

    grouped = _empirical_grouped(annual, path)
    with np.load(path, allow_pickle=False) as archive:
        require(
            "Q_t" in archive.files and "Q_t" in annual["grouped_shapes"],
            "complete rates require retained scalar response energy",
        )
        energy = archive["Q_t"]
        require(
            "Q_h" in archive.files,
            "complete archive lacks retained shape response energy",
        )
        shape_energy = archive["Q_h"]
    require(
        energy.dtype == np.dtype("float64")
        and energy.shape == (len(grouped.game_ids),)
        and list(energy.shape) == annual["grouped_shapes"]["Q_t"]
        and np.isfinite(energy).all()
        and np.all(energy >= 0),
        "complete scalar response energy differs from its declared axes",
    )
    require(
        shape_energy.dtype == np.dtype("float64")
        and shape_energy.shape == energy.shape
        and np.isfinite(shape_energy).all()
        and np.all(shape_energy >= 0),
        "complete shape response energy differs",
    )
    return replace(
        grouped,
        Q_t=energy,
        Q_h=shape_energy,
        correction_identity=annual.get("correction_identity"),
    )


def complete_training(grouped, references, train_ids, basis):
    """derive shape and scalar likelihoods from the same selected counted support."""
    from .attribution import ScalarCoefficientLikelihood

    shape, selected = _selected_training(grouped, references, train_ids, basis)
    require(
        grouped.Q_t is not None
        and grouped.Q_t.shape == (len(grouped.game_ids),)
        and grouped.Q_t.dtype == np.dtype("float64")
        and np.isfinite(grouped.Q_t).all()
        and np.all(grouped.Q_t >= 0),
        "complete rates require finite retained scalar energy",
    )
    raw_energy = float(
        (
            grouped.Q_t[selected["rows"]].sum()
            - np.sum(selected["context_totals"] ** 2 / selected["context_exposure"])
        )
        / shape.likelihood.r
    )
    subtraction_scale = float(
        (
            grouped.Q_t[selected["rows"]].sum()
            + np.sum(selected["context_totals"] ** 2 / selected["context_exposure"])
        )
        / shape.likelihood.r
    )
    roundoff_budget = 32 * np.finfo(np.float64).eps * subtraction_scale
    require(
        np.isfinite(raw_energy) and raw_energy >= -roundoff_budget,
        "complete residual scalar energy is materially negative or nonfinite",
    )
    energy = 0.0 if raw_energy < 0 else raw_energy
    scalar_identity = dict(
        shape.source_identity,
        scalar_energy=dict(
            raw=raw_energy,
            normalized=energy,
            roundoff_budget=roundoff_budget,
            rule="normalize negative subtraction roundoff within 32 epsilon times uncancelled energy scale",
        ),
    )
    scalar = ScalarCoefficientLikelihood(
        references.season,
        shape.likelihood.player_ids,
        shape.likelihood.H,
        selected["T"].sum(axis=1)[:, None],
        energy,
        shape.likelihood.u,
        shape.likelihood.r,
        scalar_identity,
    )
    return shape, scalar


def subtract_zero_count_rows(
    grouped,
    references,
    exclusions,
    *,
    membership_signatures=None,
    correction_identity=None,
):
    """subtract finite complete zero-count rows; retained response moments are immutable."""
    from dataclasses import replace

    require(bool(exclusions), "source correction has no specified rows")
    keys = set()
    for row in exclusions:
        key = (
            row["game_id"],
            row["period"],
            row["segment_index"],
            row["attacking_team"],
        )
        require(
            key not in keys
            and row["season"] == references.season
            and row["population"] == "unblocked_spatial"
            and row["counts"] == []
            and row["end"] - row["start"] == row["seconds"]
            and row["seconds"] > 0
            and row["game_id"] in grouped.game_ids
            and tuple(row["stratum"]) in references.strata
            and len(row["offense"]) == len(row["defense"]) == 5
            and len(set(row["offense"] + row["defense"])) == 10
            and set(row["offense"] + row["defense"]).issubset(references.player_ids),
            "source exclusion locator, count or complete row contract differs",
        )
        keys.add(key)
    require(
        membership_signatures is not None
        and len(membership_signatures) == 2 * len(references.player_ids)
        and correction_identity is not None,
        "corrected row support and correction identity are required",
    )
    ordered = sorted(exclusions, key=lambda row: row["game_id"])
    delta = group_observations(iter(ordered), references, grouped.game_ids)
    matrices = {}
    for name in ("H_e", "stratum_x"):
        matrix = (getattr(grouped, name) - getattr(delta, name)).tocsr()
        require(
            np.all(matrix.data >= -1e-12),
            "source correction exceeds original design exposure",
        )
        matrix.data[matrix.data < 0] = 0
        matrix.eliminate_zeros()
        matrices[name] = matrix
    E = grouped.stratum_e - delta.stratum_e
    require(np.all(E >= -1e-12), "source correction exceeds original context exposure")
    E[E < 0] = 0
    return replace(
        grouped,
        H_e=matrices["H_e"],
        stratum_x=matrices["stratum_x"],
        stratum_e=E,
        row_count=grouped.row_count - len(exclusions),
        membership_signatures=tuple(membership_signatures),
        correction_identity=correction_identity,
    )


def decode_coefficient_state(row, component="shape"):
    """decode one named saved coefficient state without selecting or fitting it."""
    from .attribution import ShapeCoefficientState, ScalarCoefficientState

    values = load_arrays(row)
    fields = ("season", "r", "a", "q", "source_identity", "scale", "diagnostics")
    metadata = {name: row[name] for name in fields}
    metadata.update(
        {
            name: tuple(row[name])
            for name in (
                "player_ids",
                "current_player_ids",
                "entrant_ids",
                "carried_only_ids",
            )
        }
    )
    if component == "shape":
        return ShapeCoefficientState(
            **metadata, basis_sha256=row["basis_sha256"], **values
        )
    require(component == "volume", "unknown coefficient component")
    return ScalarCoefficientState(**metadata, **values)


def coefficient_state_row(
    state, index, arm, parent, likelihood, arrays, component="shape"
):
    """serialize the state metadata shared by the finite selected components."""
    row = dict(
        index=index,
        arm=arm,
        season=state.season,
        player_ids=state.player_ids,
        current_player_ids=state.current_player_ids,
        entrant_ids=state.entrant_ids,
        carried_only_ids=state.carried_only_ids,
        r=state.r,
        a=state.a,
        q=state.q,
        **({"basis_sha256": state.basis_sha256} if component == "shape" else {}),
        source_identity=state.source_identity,
        parent=parent,
        likelihood=likelihood,
        scale=state.scale,
        diagnostics=state.diagnostics,
        **arrays,
    )
    return row


def read_complete_fixture(path):
    """read five literal synthetic histories and their independently named exclusions."""
    from dataclasses import replace
    from .attribution import decode_shape_basis
    from .chance_cli import identity

    path = Path(path).resolve(strict=True)
    document = read_json(path)
    require(
        document["kind"] == "attribution_complete_fixture"
        and document["schema_version"] == 1
        and document["purpose"] == "fixture_exercise"
        and len(document["years"]) == 5,
        "complete fixture requires five explicit counted seasons",
    )

    def ref(value):
        return dict(
            path=str((path.parent / value["path"]).resolve(strict=True)),
            sha256=value["sha256"],
        )

    basis_ref = ref(document["basis"]["arrays"])
    with np.load(linked_path(basis_ref), allow_pickle=False) as archive:
        basis = decode_shape_basis(
            {name: archive[name] for name in archive.files},
            basis_sha256=document["basis"]["basis_sha256"],
        )
    data_ref = ref(document["arrays"])
    arrays = load_arrays(dict(arrays=data_ref, array_shapes=document["array_shapes"]))
    grouped, references, annual, all_rows = [], [], [], []
    for index, year in enumerate(document["years"]):
        prefix = f"year_{index}_"
        offense, defense, seconds, si, games, counts = (
            arrays[prefix + name]
            for name in (
                "offense",
                "defense",
                "seconds",
                "si",
                "row_game_ids",
                "counts",
            )
        )
        require(
            offense.shape == defense.shape == (len(seconds), 5)
            and counts.shape == (len(seconds), 656)
            and np.all(seconds > 0)
            and np.isfinite(seconds).all()
            and np.all(counts >= 0)
            and counts.dtype == np.dtype("int64")
            and np.array_equal(offense[::2], defense[1::2])
            and np.array_equal(defense[::2], offense[1::2])
            and np.array_equal(seconds[::2], seconds[1::2])
            and np.array_equal(games[::2], games[1::2]),
            "complete fixture counted row axes differ",
        )
        players = tuple(year["players"])
        strata = tuple(map(tuple, year["strata"]))
        exposure = np.array(
            [seconds[(offense == player).any(axis=1)].sum() for player in players]
        )
        totals = counts.sum(axis=0).astype(float)
        refs = AnnualReferences(
            "unblocked_spatial",
            year["season"],
            index,
            data_ref["sha256"],
            data_ref["sha256"],
            players,
            strata,
            float(totals.sum() / (seconds.sum() / 3600)),
            exposure / exposure.sum(),
            basis.p,
            exposure,
            totals,
        )
        rows = []
        for i in range(len(seconds)):
            nz = np.flatnonzero(counts[i])
            rows.append(
                dict(
                    population="unblocked_spatial",
                    season=year["season"],
                    game_id=str(games[i]),
                    period=1,
                    start=i // 2 * 300,
                    end=i // 2 * 300 + float(seconds[i]),
                    segment_index=i // 2,
                    attacking_team=int(si[i]) + 1,
                    offense=offense[i].tolist(),
                    defense=defense[i].tolist(),
                    seconds=float(seconds[i]),
                    stratum=list(strata[int(si[i])]),
                    counts=[[int(cell), int(counts[i, cell])] for cell in nz],
                )
            )
        moments = group_observations(iter(rows), refs, tuple(year["game_ids"]))
        references.append(refs)
        grouped.append(moments)
        all_rows.append(rows)
        annual.append(
            dict(
                year,
                coverage=dict(measured_games=len(year["game_ids"])),
                references=data_ref,
                grouped=data_ref,
            )
        )
    source_identity = dict(
        fixture=identity(path),
        arrays=data_ref,
        basis=basis_ref,
        basis_sha256=basis.sha256,
        source="explicitly synthetic integer counted histories",
    )
    coverage = {
        game: dict(
            retained_seconds=1800 * float(grouped[-1].stratum_e[i].sum()),
            retained_attempts=int(grouped[-1].stratum_n[i].sum()),
        )
        for i, game in enumerate(grouped[-1].game_ids)
    }
    original = EmpiricalSource(
        basis,
        tuple(document["seasons"]),
        tuple(grouped),
        tuple(references),
        tuple(annual),
        document["game_dates"],
        coverage,
        source_identity,
    )
    exclusions = []
    for locator in document["exclusions"]:
        matches = [
            row
            for rows in all_rows
            for row in rows
            if all(row[name] == value for name, value in locator.items())
        ]
        require(
            len(matches) == 1 and matches[0]["counts"] == [],
            "fixture exclusion not an exact zero-count row",
        )
        exclusions.append(matches[0])
    corrected = list(grouped)
    for index, refs in enumerate(references):
        selected = [row for row in exclusions if row["season"] == refs.season]
        if selected:
            retained = [row for row in all_rows[index] if row not in selected]
            replay = group_observations(iter(retained), refs, grouped[index].game_ids)
            correction_identity = dict(
                kind="synthetic_zero_count_exclusion",
                counted_arrays_sha256=data_ref["sha256"],
                rows_sha256=hashlib.sha256(
                    json.dumps(selected, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            )
            corrected[index] = subtract_zero_count_rows(
                grouped[index],
                refs,
                selected,
                membership_signatures=replay.membership_signatures,
                correction_identity=correction_identity,
            )
            verify_grouped_population(corrected[index], replay)
    receipt = dict(
        rows=exclusions,
        directed_seconds=sum(row["seconds"] for row in exclusions),
        physical_seconds=sum(row["seconds"] for row in exclusions) / 2,
        count_loss=0,
        source="explicit synthetic correction",
    )
    metadata = dict(document, rows=all_rows)
    return replace(original, grouped=tuple(corrected)), original, receipt, metadata


COMPLETE_SOURCE_SHA = "3e17a6323c2ad67b40e65e2c9a5c4e290d896f640bbf95726b20dc558ff30b08"
COMPLETE_AUDIT_SHA = "b307e0d1f90989865afb8c2465d272d3351198c7cc2a16074b24dee4ffaffe30"
COMPLETE_IMPACT_SHA = "f308b2f0c6c77e2f66562c7277af666b105a372d7b18089bd8138f92648953c4"
COMPLETE_EXCLUSIONS = (
    ("20232024", "2023020041", 2, 236, 1167, 1200, (30, 8)),
    ("20232024", "2023020685", 3, 372, 939, 992, (2, 52)),
    ("20242025", "2024020186", 3, 325, 657, 703, (14, 52)),
)


def read_complete_source(result_ref, audit_ref):
    """bind accepted 02d evidence and subtract only the six authorized frozen rows."""
    from dataclasses import replace
    from .artifacts import rows

    require(
        result_ref["sha256"] == COMPLETE_SOURCE_SHA
        and audit_ref["sha256"] == COMPLETE_AUDIT_SHA,
        "complete rates require the frozen 04m result and accepted final 02d audit",
    )
    result = read_json(linked_path(result_ref))
    audit = read_json(linked_path(audit_ref))
    require(
        result["kind"] == "attribution_empirical_result"
        and result["schema_version"] == 1
        and result["execution_status"] == "complete"
        and result["purpose"] == "research",
        "complete source requires the completed frozen empirical result",
    )
    clean_implementation(result["implementation"])
    clean_implementation(audit["implementation"])
    require(
        audit["kind"] == "source_exposure_result"
        and audit["execution_status"] == "complete"
        and audit["research_impact"] == "verified"
        and audit["policy_id"] == "strict_interior_other_strength_v1"
        and audit["recovery_status"] == "no_recovery"
        and audit["recovery"]["recovered_games"] == 0,
        "complete source audit is interim, changed, or reports recovery",
    )
    impact_ref = audit["outputs"]["research-impact.json"]
    require(
        impact_ref["sha256"] == COMPLETE_IMPACT_SHA,
        "complete source research-impact identity differs",
    )
    oracle_ref = dict(
        path="/Users/nnandal/Documents/code/hockey-stats-local/source-02d-20261021/review/research-impact-oracle.json",
        sha256="cf5f1ab4f57d0c4d6232cc5dcce0a862894c0c8ed8ddd79f1296fc1dd726a3d8",
    )
    oracle = read_json(linked_path(oracle_ref))
    require(
        oracle["totals"]["unblocked_spatial"]["newly_lost_directed_seconds"] == 264
        and oracle["totals"]["unblocked_spatial"]["newly_lost_row_counts"] == 0,
        "corroborating frozen source oracle differs",
    )
    impact = read_json(linked_path(impact_ref))
    require(
        impact["kind"] == "source_exposure_research_impact"
        and impact["schema_version"] == 1
        and impact["research_impact"] == "verified"
        and impact["policy_id"] == audit["policy_id"]
        and impact["unresolved"] == [],
        "accepted source impact is incomplete",
    )
    assessment_ref = result["consumed"]["assessment"]
    assessment = read_json(linked_path(assessment_ref))
    require(
        assessment["kind"] == "attribution_empirical_assessment"
        and assessment["execution_status"] == "complete",
        "complete frozen empirical assessment is unavailable",
    )
    clean_implementation(assessment["implementation"])
    prepared_ref = assessment["prepared"]
    prepared = read_json(linked_path(prepared_ref))
    fit_ref = assessment["fit"]
    fit = read_json(linked_path(fit_ref))
    clean_implementation(prepared["implementation"])
    clean_implementation(fit["implementation"])
    require(
        prepared["kind"] == "attribution_empirical_prepared"
        and fit["kind"] == "attribution_empirical_fit"
        and prepared["purpose"] == fit["purpose"] == "research"
        and fit["prepared"] == prepared_ref
        and fit["execution_status"] == "complete"
        and fit["state_count"] == len(fit["states"]) == 6
        and len(assessment["probes"]) == 6
        and prepared["sources"] == result["source_references"],
        "complete original preparation, fit or probe inventory differs",
    )
    original = read_empirical_source(
        prepared["sources"]["source_result"],
        prepared["sources"]["basis"],
        prepared["sources"]["corpus"],
    )
    grouped = tuple(
        complete_grouped(row, linked_path(row["grouped"])) for row in original.annual
    )
    original = replace(original, grouped=grouped)
    baseline = read_json(linked_path(original.source_identity["baseline_prepared"]))
    ledger_refs = {
        row["season"]: row["reference"]
        for row in impact["references"]["directed_rows"]
        if row["population"] == "unblocked_spatial"
    }
    expected = {
        game: (season, period, segment, start, end, teams)
        for season, game, period, segment, start, end, teams in COMPLETE_EXCLUSIONS
    }
    affected = {}
    for game in impact["games"]:
        require(
            game["source_status"] == "concordant",
            "source impact includes nonconcordant source evidence",
        )
        incidents = game["incidents"]
        for incident in incidents:
            require(
                incident["source_status"] == "concordant"
                and incident["differences"] == [],
                "accepted impact incident changed its source evidence",
            )
            spatial = incident["populations"]["unblocked_spatial"]
            if spatial["newly_excluded_physical_seconds"]:
                require(
                    game["game_id"] in expected
                    and spatial["newly_excluded_attempts"] == 0
                    and spatial["already_excluded_physical_seconds"] == 0
                    and spatial["lost_retained_events"] == [],
                    "accepted source audit specifies an unexpected correction",
                )
                affected.setdefault(game["game_id"], []).append(incident)
    require(
        set(affected) == set(expected),
        "accepted source audit omits a frozen correction",
    )
    exclusions = []
    support_signatures = {}
    affected_rows = {}
    for season in ("20232024", "20242025"):
        bound = next(
            row
            for row in baseline["annual"]
            if row["population"] == "unblocked_spatial" and row["season"] == season
        )
        require(
            ledger_refs[season] == bound["rows"],
            "accepted source audit changed original spatial ledger",
        )
        annual_index = original.seasons.index(season)
        refs = original.references[annual_index]
        positions = {player: index for index, player in enumerate(refs.player_ids)}
        old_signatures = [hashlib.sha256() for _ in range(2 * len(refs.player_ids))]
        new_signatures = [hashlib.sha256() for _ in old_signatures]
        old_count = new_count = 0
        for row in rows(linked_path(ledger_refs[season])):
            columns = [positions[player] for player in row["offense"]]
            columns += [
                len(refs.player_ids) + positions[player] for player in row["defense"]
            ]
            old_marker = old_count.to_bytes(8, "little")
            for column in columns:
                old_signatures[column].update(old_marker)
            old_count += 1
            excluded = (
                row["game_id"] in expected
                and (row["period"], row["segment_index"])
                == expected[row["game_id"]][1:3]
            )
            if not excluded:
                new_marker = new_count.to_bytes(8, "little")
                for column in columns:
                    new_signatures[column].update(new_marker)
                new_count += 1
            if row["game_id"] not in expected:
                continue
            affected_rows.setdefault(row["game_id"], []).append(row)
            _, period, segment, start, end, teams = expected[row["game_id"]]
            if row["period"] == period and row["segment_index"] == segment:
                require(
                    row["start"] == start
                    and row["end"] == end
                    and row["seconds"] == end - start
                    and row["attacking_team"] in teams
                    and row["counts"] == [],
                    "frozen source exclusion locator, duration or zero-count evidence differs",
                )
                incidents = affected[row["game_id"]]
                require(
                    len(incidents) == 2
                    and {entry["state"] for entry in incidents}
                    == {"original", "selected"},
                    "accepted source correction does not bind both concordant states",
                )
                for incident in incidents:
                    runs = [
                        run
                        for run in incident["runs"]
                        if run["period_number"] == period
                        and run["start_seconds"] == start
                        and run["end_seconds"] == end
                    ]
                    require(
                        len(runs) == 1, "accepted source correction endpoints differ"
                    )
                    run = runs[0]
                    side = row["stratum"][0]
                    require(
                        side in ("away", "home")
                        and row["offense"] == run[side + "_skaters"]
                        and row["defense"]
                        == run[("home" if side == "away" else "away") + "_skaters"],
                        "accepted source correction lineup differs",
                    )
                    segments = incident["populations"]["unblocked_spatial"]["segments"]
                    require(
                        any(
                            value["segment_index"] == segment
                            and value["period"] == period
                            and value["start"] == start
                            and value["end"] == end
                            and value["pre_mask_attempts"] == 0
                            and row["stratum"]
                            == [
                                side,
                                str(period),
                                max(
                                    -3,
                                    min(
                                        3,
                                        value["score_difference"]
                                        if side == "home"
                                        else -value["score_difference"],
                                    ),
                                ),
                            ]
                            for value in segments
                        ),
                        "accepted source correction spatial segment differs",
                    )
                exclusions.append(row)
        require(
            old_count == original.grouped[annual_index].row_count
            and tuple(item.hexdigest() for item in old_signatures)
            == original.grouped[annual_index].membership_signatures,
            "original spatial ledger row support differs from grouped membership signatures",
        )
        support_signatures[season] = tuple(item.hexdigest() for item in new_signatures)
    require(
        len(exclusions) == 6
        and len({(row["game_id"], row["attacking_team"]) for row in exclusions}) == 6
        and sum(row["seconds"] for row in exclusions) == 264,
        "frozen six-row correction inventory differs",
    )
    corrected = list(grouped)
    for index, refs in enumerate(original.references):
        selected = [row for row in exclusions if row["season"] == refs.season]
        if selected:
            correction_identity = dict(
                kind="finite_zero_count_exclusion",
                source_audit_sha256=audit_ref["sha256"],
                original_grouped_sha256=original.annual[index]["grouped"]["sha256"],
                rows_sha256=hashlib.sha256(
                    json.dumps(selected, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            )
            corrected[index] = subtract_zero_count_rows(
                grouped[index],
                refs,
                selected,
                membership_signatures=support_signatures[refs.season],
                correction_identity=correction_identity,
            )
    game_replays = []
    for game, batch in affected_rows.items():
        year = original.seasons.index(batch[0]["season"])
        refs = original.references[year]
        before = group_observations(iter(batch), refs, (game,))
        retained = [row for row in batch if row not in exclusions]
        after = group_observations(iter(retained), refs, (game,))
        before_errors = verify_grouped_game(before, grouped[year], refs, game)
        after_errors = verify_grouped_game(after, corrected[year], refs, game)
        game_replays.append(
            dict(
                game_id=game,
                before_errors=before_errors,
                after_errors=after_errors,
                original_rows=len(batch),
                retained_rows=len(retained),
            )
        )
    receipt = dict(
        source_result=result_ref,
        source_audit=audit_ref,
        research_impact=impact_ref,
        corroborating_oracle=oracle_ref,
        policy_id=audit["policy_id"],
        rows=exclusions,
        directed_seconds=264,
        physical_seconds=132,
        count_loss=0,
        changed_seasons=["20232024", "20242025"],
        final_assessment_unchanged=True,
        affected_game_replays=game_replays,
        membership_support="original hashes verified; corrected hashes recomputed during existing ledger scan",
        old_grouped=[row["grouped"] for row in original.annual],
    )
    metadata = dict(
        prepared=prepared,
        prepared_ref=prepared_ref,
        fit=fit,
        fit_ref=fit_ref,
        assessment=assessment,
        assessment_ref=assessment_ref,
        train_ids=prepared["train_ids"],
        assessment_ids=prepared["assessment_ids"],
        inventory=prepared["inventory"],
        months=prepared["months"],
        row_references={
            row["season"]: row["rows"]
            for row in baseline["annual"]
            if row["population"] == "unblocked_spatial"
        },
    )
    return replace(original, grouped=tuple(corrected)), original, receipt, metadata


def iter_complete_rows(source, metadata, assessment_ids):
    """replay original final held-out support once, including zero-event directed rows."""
    from .artifacts import rows

    selected = set(assessment_ids)
    if "rows" in metadata:
        yield from (row for row in metadata["rows"][-1] if row["game_id"] in selected)
    else:
        reference = metadata["row_references"][source.seasons[-1]]
        for row in rows(linked_path(reference)):
            if row["game_id"] in selected:
                yield row


def reconcile_complete_rows(row_iterator, grouped, references, assessment_ids, receipt):
    """stream one game at a time and independently reconcile all five raw moments."""
    seen = set()
    count = 0
    seconds = 0.0
    attempts = 0
    errors = {name: 0.0 for name in ("A", "C", "E", "N", "K")}
    for game, iterator in groupby(row_iterator, key=lambda row: row["game_id"]):
        require(
            game in assessment_ids and game not in seen,
            "held-out row replay duplicates or adds a game",
        )
        batch = list(iterator)
        seen.add(game)
        actual = group_observations(iter(batch), references, (game,))
        expected = empirical_game_moments(grouped, references, game)
        n, s, k = (
            2 * len(references.player_ids),
            len(references.strata),
            len(references.response_counts),
        )
        for key, name, shape in (
            ("A", "H_e", (n, n)),
            ("C", "stratum_x", (s, n)),
            ("N", "stratum_n", (s, k)),
            ("K", "T_raw", (n, k)),
        ):
            difference = getattr(actual, name)[0].reshape(shape) - expected[key]
            value = (
                float(np.max(np.abs(difference.data)))
                if sparse.issparse(difference) and difference.nnz
                else (
                    float(np.max(np.abs(difference)))
                    if not sparse.issparse(difference)
                    else 0.0
                )
            )
            errors[key] = max(errors[key], value)
        errors["E"] = max(
            errors["E"], float(np.max(np.abs(actual.stratum_e[0] - expected["E"])))
        )
        require(
            max(errors.values()) <= 1e-10,
            "held-out row replay differs from grouped raw moments",
        )
        count += len(batch)
        seconds += sum(row["seconds"] for row in batch)
        attempts += sum(sum(value for _, value in row["counts"]) for row in batch)
        yield from batch
    for game in set(assessment_ids) - seen:
        require(
            float(grouped.stratum_e[grouped.game_ids.index(game)].sum()) == 0,
            "positive-exposure held-out game absent from row replay",
        )
    receipt.update(
        status="verified",
        rows=count,
        directed_seconds=seconds,
        retained_counts=attempts,
        moment_max_absolute_errors=errors,
        zero_time_games=sorted(set(assessment_ids) - seen),
        inventory_games=len(assessment_ids),
    )


def read_coefficient_chain(trainings, document):
    """validate saved annual equations, records, parents and source likelihood identity."""
    from .attribution import validate_shape_coefficient_state

    require(
        len(document["states"]) == len(trainings) + 1,
        "saved coefficient chain inventory differs",
    )
    states = []
    for index, row in enumerate(document["states"]):
        independent = index == len(trainings)
        likelihood = (trainings[-1] if independent else trainings[index]).likelihood
        parent = (
            None
            if independent or index == 0
            else document["states"][index - 1]["record"]
        )
        record = read_coefficient_record(row["record"])
        require(
            record == {name: value for name, value in row.items() if name != "record"}
            and row["index"] == index
            and row["season"] == likelihood.season
            and row["arm"] == ("independent" if independent else "borrowing")
            and row["parent"] == parent,
            "saved coefficient record, annual selection or incoming parent differs",
        )
        state = decode_coefficient_state(row)
        validate_shape_coefficient_state(
            likelihood, None if independent or index == 0 else states[-1], state
        )
        states.append(state)
    return tuple(states)


def exact_shape_reuse_proofs(original_trainings, corrected_trainings, fit_document):
    """prove the finite first-two and final-independent unchanged likelihood contracts."""
    proofs = []
    for index in (0, 1, len(original_trainings)):
        year = min(index, len(original_trainings) - 1)
        old, new = original_trainings[year], corrected_trainings[year]
        fields = ("H", "Q", "u")
        require(
            old.likelihood.player_ids == new.likelihood.player_ids
            and old.likelihood.r == new.likelihood.r
            and old.likelihood.basis.sha256 == new.likelihood.basis.sha256
            and old.source_identity == new.source_identity
            and old.game_ids == new.game_ids
            and old.strata == new.strata
            and all(
                np.array_equal(
                    getattr(old.likelihood, name), getattr(new.likelihood, name)
                )
                for name in fields
            )
            and np.array_equal(old.xbar, new.xbar)
            and np.array_equal(old.nbar, new.nbar),
            "selected shape reuse changes likelihood arrays, references or axes",
        )
        row = fit_document["states"][index]
        parent = (
            None
            if index in (0, len(original_trainings))
            else fit_document["states"][index - 1]["record"]
        )
        require(row["parent"] == parent, "selected shape reuse incoming parent differs")
        proofs.append(
            dict(
                index=index,
                season=new.likelihood.season,
                arm=row["arm"],
                record=row["record"],
                original_parent=parent,
                selected_parent=parent,
                likelihood_arrays_equal=True,
                ids_rate_exposure_basis_reference_equal=True,
                incoming_parent_equal=True,
            )
        )
    return proofs


def _fixture_reference(reference, root):
    return dict(
        path=str((root / reference["path"]).resolve(strict=True)),
        sha256=reference["sha256"],
    )


def read_coefficient_record(reference):
    """resolve the explicit portable-fixture record schema at its own boundary."""
    record = read_json(linked_path(reference))
    if record.get("reference_mode") == "fixture_relative_v1":
        root = Path(reference["path"]).parent
        record = dict(
            record,
            arrays=_fixture_reference(record["arrays"], root),
            parent=None
            if record["parent"] is None
            else _fixture_reference(record["parent"], root),
        )
    return record


def read_complete_fixture_controls(fixture, original):
    document = read_json(Path(fixture))
    root = Path(fixture).absolute().parent
    reference = _fixture_reference(document["controls"], root)
    controls = read_json(linked_path(reference))
    require(
        controls["kind"] == "attribution_complete_fixture_controls"
        and controls["schema_version"] == 1
        and controls["purpose"] == "fixture_exercise"
        and _fixture_reference(controls["source"], root)
        == original.source_identity["arrays"],
        "fixture controls differ from explicit counted arrays",
    )
    states = []
    for row in controls["states"]:
        require(
            row["reference_mode"] == "fixture_relative_v1",
            "fixture state reference mode differs",
        )
        selected = dict(
            row,
            arrays=_fixture_reference(row["arrays"], root),
            record=_fixture_reference(row["record"], root),
            parent=None
            if row["parent"] is None
            else _fixture_reference(row["parent"], root),
        )
        states.append(selected)
    probes = []
    for probe in controls["probes"]:
        alternative = probe["alternative"]
        probes.append(
            dict(
                probe,
                alternative=dict(
                    alternative,
                    arrays=_fixture_reference(alternative["arrays"], root),
                    parent=None
                    if alternative["parent"] is None
                    else _fixture_reference(alternative["parent"], root),
                ),
            )
        )
    return dict(controls, states=states, probes=probes), reference


def verify_grouped_population(actual, expected):
    """check a corrected archive against independently rebuilt complete row moments."""
    errors = {}
    require(
        actual.game_ids == expected.game_ids
        and actual.row_count == expected.row_count
        and actual.membership_signatures == expected.membership_signatures,
        "corrected raw moment inventory or same-role row support differs",
    )
    for name in ("H_e", "T_raw", "stratum_x", "stratum_n"):
        difference = getattr(actual, name) - getattr(expected, name)
        errors[name] = float(np.max(np.abs(difference.data))) if difference.nnz else 0.0
    for name in ("stratum_e", "Q_t", "Q_h"):
        left, right = getattr(actual, name), getattr(expected, name)
        require(
            left is not None and right is not None,
            "corrected raw moment energy is missing",
        )
        errors[name] = float(np.max(np.abs(left - right)))
    require(
        max(errors.values()) <= 1e-8,
        "corrected raw moments differ from literal row reconstruction",
    )
    return errors


def verify_grouped_game(actual, expected, references, game):
    """reconcile complete one-game row moments to one bound annual grouped row."""
    index = expected.game_ids.index(game)
    errors = {}
    for name in ("H_e", "T_raw", "stratum_x", "stratum_n"):
        difference = getattr(actual, name)[0] - getattr(expected, name)[index]
        errors[name] = float(np.max(np.abs(difference.data))) if difference.nnz else 0.0
    for name in ("stratum_e", "Q_t", "Q_h"):
        left, right = getattr(actual, name), getattr(expected, name)
        require(
            left is not None and right is not None,
            "bound game response energy is missing",
        )
        errors[name] = float(np.max(np.abs(left[0] - right[index])))
    require(
        max(errors.values()) <= 1e-8,
        "affected game original/corrected raw moments differ from full row replay",
    )
    return errors


CONTEXT_SOURCE_SHA = "7245ab4873945ebaa0b58d0cd46a11ab9087e1196b4c1258770b304a7664ae6f"
CONTEXT_SOURCE_BINDINGS = dict(
    prepared="26ecaa961af968e936067ff31002283150bc7278adba7b7121e52c936358c902",
    protocol="1dae2c1f696b14c3af7456b25534d3c0f6fdb30775788ca4599dc0eeee17121a",
    correction="41fd7c3a5b79dee24e91335ca2eda0132feffa0120b5266f0e0c386037daad27",
    fit="154f6e6324e3144eb6aa74aebcaabc2b6a860e123faca4b297328a087329bbcb",
    assessment="748b3634ce966e607fbd1d3e9bbd29c9f0ce2c84d662b797f23228725d48d558")



def read_context_source(result_ref):
    """bind 04n and follow its accepted finite correction and original capture ledgers."""
    require(result_ref["sha256"] == CONTEXT_SOURCE_SHA, "temporal context requires the exact frozen 04n result")
    result = read_json(linked_path(result_ref))
    require(result["kind"] == "attribution_complete_result" and result["schema_version"] == 1
            and result["purpose"] == "research" and result["execution_status"] == "complete",
            "temporal source requires a completed research result")
    clean_implementation(result["implementation"])
    assessment_ref = result["consumed"]["assessment"]
    require(assessment_ref["sha256"] == CONTEXT_SOURCE_BINDINGS["assessment"], "frozen 04n assessment identity differs")
    assessment = read_json(linked_path(assessment_ref))
    prepared_ref, fit_ref = assessment["prepared"], assessment["fit"]
    require(prepared_ref["sha256"] == CONTEXT_SOURCE_BINDINGS["prepared"] and fit_ref["sha256"] == CONTEXT_SOURCE_BINDINGS["fit"],
            "frozen 04n preparation or control fit identity differs")
    prepared, fit = read_json(linked_path(prepared_ref)), read_json(linked_path(fit_ref))
    for document in (assessment, prepared, fit): clean_implementation(document["implementation"])
    require(prepared["protocol"]["sha256"] == CONTEXT_SOURCE_BINDINGS["protocol"]
            and prepared["correction"]["sha256"] == CONTEXT_SOURCE_BINDINGS["correction"]
            and prepared["source_result"]["sha256"] == COMPLETE_SOURCE_SHA
            and prepared["source_audit"]["sha256"] == COMPLETE_AUDIT_SHA
            and fit["prepared"] == prepared_ref and fit["execution_status"] == "complete",
            "frozen source protocol, correction or incoming control contract differs")
    linked_path(prepared["protocol"])
    correction = read_json(linked_path(prepared["correction"]))
    source, _, rebuilt_correction, metadata = read_complete_source(prepared["source_result"], prepared["source_audit"])
    require({key: value for key, value in correction.items() if key != "corrected_archives"} == rebuilt_correction,
            "accepted finite correction differs from frozen 04n")
    from dataclasses import replace

    frozen_grouped = list(source.grouped)
    corrected_receipts = []
    require([row["season"] for row in correction["corrected_archives"]] == ["20232024", "20242025"],
            "frozen correction archive seasons differ")
    for row in correction["corrected_archives"]:
        index = source.seasons.index(row["season"])
        require(tuple(row["players"]) == source.references[index].player_ids
                and tuple(map(tuple, row["strata"])) == source.references[index].strata
                and tuple(row["game_ids"]) == source.grouped[index].game_ids,
                "frozen corrected archive axes differ")
        saved = complete_grouped(row, linked_path(row["grouped"]))
        errors = verify_grouped_population(source.grouped[index], saved)
        require(all(error == 0 for error in errors.values()), "frozen corrected archive differs from exact finite correction")
        frozen_grouped[index] = saved
        corrected_receipts.append(dict(season=row["season"], archive=row["grouped"], exact=True))
    source = replace(source, grouped=tuple(frozen_grouped))
    baseline = read_json(linked_path(source.source_identity["baseline_prepared"]))
    require(sum(len(g.game_ids) for g in source.grouped) == 6560 and len(prepared["train_ids"]) == 1051
            and len(prepared["assessment_ids"]) == 261 and source.seasons == tuple(prepared["seasons"]),
            "temporal source inventory or split differs from frozen study")
    metadata.update(controls_fit=fit, controls_assessment=assessment, controls_fit_reference=fit_ref,
        controls_assessment_reference=assessment_ref, source_result=result_ref, source_prepared=prepared,
        source_prepared_reference=prepared_ref, correction=correction, correction_reference=prepared["correction"],
        events_reference=baseline["ledgers"]["events"], segments_reference=baseline["ledgers"]["segments"],
        corrected_archive_receipts=corrected_receipts)
    return source, metadata


def read_context_fixture(path, *, require_controls=True):
    """read the five literal counted, timed histories; fixture setup never fits here."""
    from .attribution import decode_shape_basis
    from .attribution_context import BASIS_COLUMNS
    from .artifacts import rows
    from .chance_cli import identity

    path = Path(path).resolve(strict=True)
    document = read_json(path)
    require(document["kind"] == "attribution_context_fixture" and document["schema_version"] == 1
            and document["purpose"] == "fixture_exercise" and len(document["years"]) == 5
            and document["basis_columns"] == list(BASIS_COLUMNS), "temporal fixture schema, history or basis differs")
    def ref(value):
        require(set(value) == {"path", "sha256"} and not Path(value["path"]).is_absolute(),
                "fixture reference requires a declared relative path and sha256")
        return dict(path=str((path.parent/value["path"]).resolve(strict=True)), sha256=value["sha256"])
    basis_ref = ref(document["basis"]["arrays"])
    with np.load(linked_path(basis_ref), allow_pickle=False) as data:
        basis = decode_shape_basis({name: data[name] for name in data.files}, basis_sha256=document["basis"]["basis_sha256"])
    arrays_ref = ref(document["arrays"])
    arrays = load_arrays(dict(arrays=arrays_ref, array_shapes=document["array_shapes"]))
    rows_ref, events_ref, segments_ref = (ref(document[name]) for name in ("rows", "events", "segments"))
    all_rows = list(rows(linked_path(rows_ref)))
    all_events, all_segments = list(rows(linked_path(events_ref))), list(rows(linked_path(segments_ref)))
    grouped, references, annual, rows_by_year = [], [], [], []
    excluded = []
    for index, year in enumerate(document["years"]):
        batch = [row for row in all_rows if row["season"] == year["season"]]
        players, strata = tuple(year["players"]), tuple(map(tuple, year["strata"]))
        exposure = np.array([sum(row["seconds"] for row in batch if player in row["offense"]) for player in players])
        totals = np.zeros(656)
        for row in batch:
            for cell, count in row["counts"]: totals[cell] += count
        refs = AnnualReferences("unblocked_spatial", year["season"], index, arrays_ref["sha256"], arrays_ref["sha256"],
            players, strata, float(totals.sum()/(sum(row["seconds"] for row in batch)/3600)),
            exposure/exposure.sum(), basis.p, exposure, totals)
        original = group_observations(iter(batch), refs, tuple(year["game_ids"]))
        exclusions = [row for row in batch if any(all(row[k] == v for k, v in locator.items())
                                               for locator in document["exclusions"])]
        require(all(not row["counts"] for row in exclusions), "fixture correction contains a recorded attempt")
        retained = [row for row in batch if row not in exclusions]
        corrected = original
        if exclusions:
            replay = group_observations(iter(retained), refs, original.game_ids)
            correction_identity = dict(kind="synthetic_zero_count_exclusion", counted_arrays_sha256=arrays_ref["sha256"],
                rows_sha256=hashlib.sha256(json.dumps(exclusions, sort_keys=True, separators=(",", ":")).encode()).hexdigest())
            corrected = subtract_zero_count_rows(original, refs, exclusions,
                membership_signatures=replay.membership_signatures, correction_identity=correction_identity)
            verify_grouped_population(corrected, replay)
        grouped.append(corrected); references.append(refs); excluded.extend(exclusions); rows_by_year.append(batch)
        annual.append(dict(year, coverage=dict(measured_games=len(year["game_ids"])), grouped=arrays_ref, references=arrays_ref))
    require(len(excluded) == 6 and sum(row["seconds"] for row in excluded) == 264,
            "temporal fixture correction does not contain the six fixed zero-count rows")
    correction = dict(rows=excluded, directed_seconds=264, physical_seconds=132, count_loss=0,
        source="explicit synthetic finite zero-count exclusion")
    coverage = {game: dict(retained_seconds=1800*float(grouped[-1].stratum_e[i].sum()),
        retained_attempts=int(grouped[-1].stratum_n[i].sum())) for i, game in enumerate(grouped[-1].game_ids)}
    source_identity = dict(fixture=identity(path), arrays=arrays_ref, basis=basis_ref, basis_sha256=basis.sha256,
        source="explicitly synthetic timed integer counted histories")
    source = EmpiricalSource(basis, tuple(document["seasons"]), tuple(grouped), tuple(references), tuple(annual),
        document["game_dates"], coverage, source_identity)
    metadata = dict(rows=rows_by_year, events=all_events, segments=all_segments,
        events_reference=events_ref, segments_reference=segments_ref,
        row_references={year["season"]: rows_ref for year in document["years"]},
        correction=correction, correction_reference=dict(path=str(path), sha256=identity(path)["sha256"]),
        inventory=document["inventory"], train_ids=document["train_ids"], assessment_ids=document["assessment_ids"],
        months=document["months"], expected_arrays=arrays, fixture_document=document)
    if require_controls:
        control_ref = ref(document["controls"])
        controls = read_json(linked_path(control_ref))
        require(controls["kind"] == "attribution_context_fixture_controls" and controls["schema_version"] == 1
                and controls["purpose"] == "fixture_exercise" and ref(controls["counted_arrays"]) == arrays_ref,
                "temporal fixture controls differ from literal counted input")
        states, probes = [], []
        for row in controls["states"]:
            require(row["reference_mode"] == "fixture_relative_v1", "fixture state reference mode differs")
            states.append(dict(row, arrays=ref(row["arrays"]), record=ref(row["record"]),
                               parent=None if row["parent"] is None else ref(row["parent"])))
        for probe in controls["probes"]:
            alternative = probe["alternative"]
            probes.append(dict(probe, alternative=dict(alternative, arrays=ref(alternative["arrays"]),
                parent=None if alternative["parent"] is None else ref(alternative["parent"]))))
        controls = dict(controls, states=states, probes=probes)
        metadata.update(controls_fit=controls, controls_assessment=controls,
            controls_fit_reference=control_ref, controls_assessment_reference=control_ref)
    return source, metadata



def verify_context_control_training(trainings, metadata):
    """require exact equality with all five frozen 04n coarse likelihoods and references."""
    prepared = metadata["source_prepared"]
    arrays = load_arrays(prepared)
    require(len(trainings) == len(prepared["years"]) == 5, "frozen coarse training year inventory differs")
    receipts = []
    for training, row in zip(trainings, prepared["years"], strict=True):
        coarse, scalar = training.coarse_training, training.coarse_scalar_likelihood
        require(training.season == row["season"] and list(coarse.likelihood.player_ids) == row["player_ids"]
                and list(coarse.source_player_ids) == row["source_player_ids"]
                and list(map(list, coarse.strata)) == row["strata"]
                and list(map(list, coarse.source_strata)) == row["source_strata"]
                and list(coarse.game_ids) == row["game_ids"] and training.r == row["r"]
                and coarse.directed_hours == row["directed_hours"]
                and coarse.source_identity == row["source_identity"]
                and scalar.source_identity == row["scalar_source_identity"],
                "frozen coarse training annual axes, identity or references differ")
        values = dict(H=coarse.likelihood.H, Q=coarse.likelihood.Q, u=coarse.likelihood.u,
            xbar=coarse.xbar, nbar=coarse.nbar, player_exposure=coarse.player_exposure,
            response_counts=coarse.response_counts, scalar_score=scalar.score,
            scalar_energy=np.array(scalar.energy))
        for name, value in values.items():
            require(np.array_equal(value, arrays[row["prefix"]+"_"+name]),
                    "frozen 04n coarse training array differs: "+row["season"]+"/"+name)
        require(np.array_equal(training.basis.p, arrays["p"])
                and np.array_equal(training.basis.B, arrays["B"])
                and np.array_equal(training.basis.eigenvalues, arrays["eigenvalues"]),
                "frozen first-season spatial reference differs")
        receipt = dict(status="exact", season=training.season, prepared=metadata["source_prepared_reference"],
            arrays=prepared["arrays"], array_names=list(values), axes_rate_hours_source_identity_exact=True,
            spatial_reference_exact=True, corrected_archives=metadata["corrected_archive_receipts"])
        training.receipt["frozen_coarse_equivalence"] = receipt
        receipts.append(receipt)
    return receipts
