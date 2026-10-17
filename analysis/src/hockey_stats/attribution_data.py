"""immutable recorded-count evidence and game-local sufficient statistics.

the original preparation and grouped evidence remain read-only. positive game
weights recompute context residualization while original references remain fixed.
active recovery preparation binds its separate model protocol explicitly.
"""

import hashlib
import math
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

import numpy as np
from scipy import sparse

from .artifacts import (
    digest,
    linked_path,
    load_arrays,
    ordered_array_digest,
    require,
)
from .chance_cli import read_json

if TYPE_CHECKING:
    from .attribution import PoolingSource, PoolingStatistics

POPULATIONS = ("all_attempts", "unblocked_spatial")
RESEARCH_SEASONS = tuple(f"{year}{year + 1}" for year in range(2021, 2026))
POOLING_STAT_FIELDS = ("H", "T", "yy", "shape_yy", "xbar", "ybar", "stratum_weight", "player_exposure",
                       "response_counts", "u", "p", "r", "player_ids")


class ArtifactReference(TypedDict):
    path: str
    sha256: str


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
    Q_t: np.ndarray
    Q_h: np.ndarray | None
    membership_signatures: tuple[str, ...]
    row_count: int


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
        and grouped.Q_t.shape == (len(a),),
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


def centered_estimability(H: np.ndarray, P: np.ndarray, c: np.ndarray, *, spectrum=None) -> dict:
    """test a centered functional against likelihood information, never its prior."""
    require(P.shape == H.shape and c.shape == (len(H),)
            and np.isfinite(P).all() and np.isfinite(c).all(),
            "centered functional differs from ordered likelihood information")
    values, vectors, tau, masks = likelihood_spectrum(H) if spectrum is None else spectrum
    require(values.shape == (len(H),) and vectors.shape == H.shape,
            "likelihood spectrum differs from ordered information")
    d = P.T @ c
    norm = float(np.linalg.norm(d))
    statuses, nulls, precisions = [], [], []
    for mask in masks:
        null = float(np.linalg.norm(d - vectors[:, mask] @ (vectors[:, mask].T @ d)) / norm) if norm else 0.
        statuses.append("zero_functional" if norm == 0 else "not_estimable" if null > 1e-8 else "available")
        nulls.append(null)
        precisions.append(float(np.sum((vectors[:, mask].T @ d) ** 2 / values[mask]))
                          if norm and statuses[-1] == "available" else None)
    stable = len(set(statuses)) == 1 and len({int(mask.sum()) for mask in masks}) == 1
    status = statuses[1] if stable else "numerically_unresolved"
    return dict(status=status, rank=int(masks[1].sum()), dimension=len(H),
        nullity=int(len(H) - masks[1].sum()), tau=tau,
        rank_at_tau_factors=[int(mask.sum()) for mask in masks], null_projection=nulls[1],
        null_at_tau_factors=nulls, status_at_tau_factors=statuses,
        centered_functional_norm=norm,
        contrast_information_inverse=precisions[1] if status == "available" else None)


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
