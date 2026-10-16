"""immutable recorded-count evidence and game-local sufficient statistics.

revision preparation reads the corrected 04a population, preserves its rows and
ledgers, and derives native shape and grouped raw moments. positive game weights
recompute context residualization while original references remain fixed.
"""

import hashlib
import math
import time
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path
from typing import TypedDict

import numpy as np
from scipy import sparse

from .artifacts import (
    clean_implementation,
    implementation,
    linked_path,
    require,
    resources,
    rows,
    write_json,
)
from .chance_cli import identity, output_path, read_json

POPULATIONS = ("all_attempts", "unblocked_spatial")
RESEARCH_SEASONS = tuple(f"{year}{year + 1}" for year in range(2021, 2026))


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


def _write_arrays(path: Path, arrays: dict) -> tuple[ArtifactReference, dict]:
    require(
        all(np.isfinite(value).all() for value in arrays.values()),
        "nonfinite revision array",
    )
    with path.open("xb") as destination:
        np.savez(destination, **arrays)
    return identity(path), {name: list(value.shape) for name, value in arrays.items()}


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


def prepare_revision(
    prepared: Path | str, protocol: Path | str, out: Path | str
) -> ArtifactReference:
    """derive native shape/game moments while retaining all original evidence."""
    started = time.monotonic()
    source_path, protocol_path = (
        Path(prepared).resolve(strict=True),
        Path(protocol).resolve(strict=True),
    )
    source_ref, protocol_ref = identity(source_path), identity(protocol_path)
    frozen, source = read_json(protocol_path), read_json(source_path)
    validate_revision_protocol(frozen)
    require(
        source_ref == frozen["baseline_prepared"]
        and source["schema_version"] == 1
        and source["kind"] == "attribution_prepared"
        and source["purpose"] == frozen["purpose"]
        and source["seasons"] == frozen["seasons"]
        and source["populations"] == list(POPULATIONS),
        "revision requires its explicitly bound original preparation",
    )
    current_implementation = implementation()
    if frozen["purpose"] == "research":
        clean_implementation(current_implementation)
        require(
            frozen["implementation"] == current_implementation,
            "research revision implementation differs from frozen protocol",
        )
    checked = set()

    def check_links(value):
        if isinstance(value, dict):
            if "path" in value and "sha256" in value:
                reference = {name: value[name] for name in ("path", "sha256")}
                key = (reference["path"], reference["sha256"])
                if key not in checked:
                    linked_path(reference)
                    checked.add(key)
            else:
                for nested in value.values():
                    check_links(nested)
        elif isinstance(value, list):
            for nested in value:
                check_links(nested)

    check_links(source)
    controls = []
    if frozen["baseline_fits"] is not None:
        chains = read_json(linked_path(frozen["baseline_fits"]))
        require(
            chains["schema_version"] == 1
            and chains["kind"] == "attribution_chains"
            and chains["prepared"] == source_ref
            and chains["protocol"] == source["protocol"],
            "corrected control chains differ from original evidence",
        )
        for row in chains["annual"]:
            state = read_json(linked_path(row["reference"]))
            require(
                state["prepared"] == source_ref
                and state["protocol"] == source["protocol"]
                and state["benchmark"] == row["benchmark"]
                and state["season"] == row["season"],
                "control state differs from its source chain",
            )
            check_links(state)
            controls.append(
                {
                    "benchmark": row["benchmark"],
                    "season": row["season"],
                    "state": row["reference"],
                }
            )
        require(
            [(row["benchmark"], row["season"]) for row in controls]
            == [
                (population, season)
                for population in POPULATIONS
                for season in source["seasons"]
            ],
            "control chains do not contain exactly the ordered annual states",
        )
    if frozen["baseline_result"] is not None:
        result = read_json(linked_path(frozen["baseline_result"]))
        require(
            result["status"] == "research_complete"
            and result["evidence"]["prepared"] == source_ref
            and result["evidence"]["chains"] == frozen["baseline_fits"],
            "revision baseline result does not bind corrected completed evidence",
        )
        linked_path(result["evidence"]["assessment"])
    inventory = {season: [] for season in source["seasons"]}
    for row in rows(Path(source["ledgers"]["coverage"]["path"])):
        require(row["season"] in inventory, "source coverage has an undeclared season")
        inventory[row["season"]].append(row["game_id"])
    for season, games in inventory.items():
        require(
            len(games) == len(set(games)) == source["games_by_season"][season],
            "source coverage does not reconcile inventory games",
        )
        games.sort()
    output = output_path(str(out), [str(source_path.parent), str(protocol_path.parent)])
    require(
        output.is_relative_to(Path(frozen["output_root"]).resolve()),
        "revision output differs from frozen root",
    )
    if frozen["purpose"] == "research":
        require(
            output.is_relative_to(Path("/Volumes/Expansion/hockey-stats")),
            "research revision outputs must remain external",
        )
    output.mkdir()
    first = next(
        row
        for row in source["annual"]
        if row["population"] == "unblocked_spatial"
        and row["season"] == source["seasons"][0]
    )
    first_arrays = _read_arrays(Path(first["arrays"]["path"]), first["shapes"])
    p = (first_arrays["response_counts"] + 0.5) / (
        first_arrays["response_counts"].sum() + 0.5 * 656
    )
    require(
        p.shape == (656,) and np.all(p > 0),
        "source spatial reference is not the native positive shape",
    )
    annual_documents = []
    for annual in source["annual"]:
        require(
            annual["status"] == "prepared",
            "revision requires all original annual populations",
        )
        benchmark, season = annual["population"], annual["season"]
        arrays = _read_arrays(Path(annual["arrays"]["path"]), annual["shapes"])
        exposure = arrays["player_exposure"]
        reference_arrays = {
            "u": exposure / exposure.sum(),
            "player_exposure": exposure,
            "response_counts": arrays["response_counts"],
        }
        if benchmark == "unblocked_spatial":
            reference_arrays["p"] = p
        references = AnnualReferences(
            benchmark,
            season,
            source["seasons"].index(season),
            protocol_ref["sha256"],
            source["population_ids"][benchmark],
            tuple(annual["players"]),
            tuple(tuple(row) for row in annual["strata"]),
            annual["r"],
            reference_arrays["u"],
            reference_arrays.get("p"),
            exposure,
            arrays["response_counts"],
        )
        grouped = group_observations(
            rows(Path(annual["rows"]["path"])), references, tuple(inventory[season])
        )
        require(
            grouped.row_count == annual["row_count"],
            "grouped row count differs from original evidence",
        )
        population = weighted_population(
            grouped, np.ones(len(grouped.game_ids)), references
        )
        errors = {
            name: float(
                np.max(np.abs(getattr(population, name) - arrays[name]))
                / (1 + np.max(np.abs(arrays[name])))
            )
            for name in ("H", "T", "yy", "xbar", "ybar", "stratum_weight")
        }
        require(
            max(errors.values()) <= 1e-8,
            "unit game weights do not recover original annual statistics",
        )
        grouped_arrays = {"stratum_e": grouped.stratum_e, "Q_t": grouped.Q_t}
        if grouped.Q_h is not None:
            grouped_arrays["Q_h"] = grouped.Q_h
        for name in ("H_e", "T_raw", "stratum_x", "stratum_n"):
            matrix = getattr(grouped, name)
            grouped_arrays.update(
                {
                    name + "_data": matrix.data,
                    name + "_indices": matrix.indices,
                    name + "_indptr": matrix.indptr,
                }
            )
        prefix = benchmark + "-" + season
        grouped_ref, grouped_shapes = _write_arrays(
            output / (prefix + "-grouped.npz"), grouped_arrays
        )
        reference_ref, reference_shapes = _write_arrays(
            output / (prefix + "-references.npz"), reference_arrays
        )
        statistics = {
            name: arrays[name]
            for name in ("H", "T", "yy", "xbar", "ybar", "stratum_weight")
        }
        if population.shape_yy is not None:
            statistics["shape_yy"] = np.asarray(population.shape_yy)
        statistic_ref, statistic_shapes = _write_arrays(
            output / (prefix + "-statistics.npz"), statistics
        )
        annual_documents.append(
            dict(
                annual,
                grouped=grouped_ref,
                grouped_shapes=grouped_shapes,
                references=reference_ref,
                reference_shapes=reference_shapes,
                statistics=statistic_ref,
                statistic_shapes=statistic_shapes,
                game_ids=inventory[season],
                membership_signatures=list(grouped.membership_signatures),
                unit_weight_errors=errors,
            )
        )
    document = dict(
        source,
        schema_version=2,
        kind="attribution_revision_prepared",
        implementation=current_implementation,
        protocol=protocol_ref,
        baseline_prepared=source_ref,
        baseline_controls=controls,
        annual=annual_documents,
        reference_contract="fixed original r,u,positive first-season p; original response counts and player exposure",
        grouped_contract="per inventory game sparse unresidualized H_e,T_raw,X_s,N_s and E_s,Q_t,Q_h; c-order columns",
        resources=resources(started),
    )
    write_json(output / "prepared.json", document)
    return identity(output / "prepared.json")
