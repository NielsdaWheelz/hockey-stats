"""exact frozen-event and polynomial exposure mathematics for temporal context.

raw game moments retain training-independent integrals. annual centering is
estimated from selected training exposure and applied unchanged to assessment.
"""

from dataclasses import dataclass
from itertools import groupby
from typing import TYPE_CHECKING

import numpy as np
from scipy import sparse

from .artifacts import linked_path, ordered_array_digest, require, rows
from .attribution_data import (AnnualReferences, EmpiricalTraining, GroupedPopulation,
    complete_training, empirical_game_moments, group_observations, verify_grouped_game)

if TYPE_CHECKING:
    from .attribution import ShapeCoefficientLikelihood, ScalarCoefficientLikelihood, ScalarScoreLikelihood

TEMPORAL_IDS = tuple(("temporal", str(k), b, j) for k in (1, 2, 3)
                     for b in ("constant", "lead", "trail") for j in (1, 2))
BASIS_COLUMNS = tuple(dict(period=k, score_factor=b, time_power=j) for _, k, b, j in TEMPORAL_IDS)


def _context(stratum):
    require(isinstance(stratum, (tuple, list)) and len(stratum) == 3
            and stratum[0] in ("away", "home") and stratum[1] in ("1", "2", "3", "overtime")
            and type(stratum[2]) is int and -3 <= stratum[2] <= 3,
            "temporal context requires side, timed period and clipped integer score")
    return (4 if stratum[1] == "overtime" else int(stratum[1])), stratum[2]


def temporal_basis(period: int, score: int, clock: float) -> np.ndarray:
    """fixed eighteen-column raw basis at an actual source clock; overtime is zero."""
    require(type(period) is int and period in (1, 2, 3, 4) and type(score) is int and -3 <= score <= 3
            and np.isfinite(clock) and 0 <= clock <= (1200 if period <= 3 else 300),
            "temporal basis period, clipped score or clock differs")
    out = np.zeros(18)
    if period <= 3:
        tau = (clock-600)/600
        out[(period-1)*6:period*6] = np.outer((1, max(score, 0), max(-score, 0)), (tau, tau*tau)).ravel()
    return out


def temporal_moments(period: int, score: int, start: float, end: float) -> tuple[np.ndarray, np.ndarray]:
    """integrate h0 and h0'h0 analytically in directed hours, through degree four."""
    temporal_basis(period, score, start)
    temporal_basis(period, score, end)
    require(end > start, "temporal interval must have positive duration")
    J, L = np.zeros(18), np.zeros((18, 18))
    if period <= 3:
        a, b = (start-600)/600, (end-600)/600
        moments = np.array([(b**(j+1)-a**(j+1))/(6*(j+1)) for j in range(5)])
        factors = np.repeat((1, max(score, 0), max(-score, 0)), 2)
        powers = np.tile((1, 2), 3)
        sl = slice((period-1)*6, period*6)
        J[sl] = factors*moments[powers]
        L[sl, sl] = factors[:, None]*factors[None, :]*moments[powers[:, None]+powers[None, :]]
    return J, L


def context_polynomial(stratum, start, M, strata) -> np.ndarray:
    """coefficients of [z,h] in local seconds x=t-start, ordered constant/linear/quadratic."""
    period, score = _context(stratum)
    strata = tuple(map(tuple, strata))
    require(tuple(stratum) in strata and M.shape == (len(strata), 18)
            and M.dtype == np.dtype("float64") and np.isfinite(M).all(),
            "context polynomial differs from training centering or context axis")
    temporal_basis(period, score, start)
    si = strata.index(tuple(stratum))
    out = np.zeros((len(strata)+18, 3))
    out[si, 0] = 1
    out[len(strata):, 0] = -M[si]
    if period <= 3:
        tau = (start-600)/600
        for b, factor in enumerate((1, max(score, 0), max(-score, 0))):
            offset = len(strata)+(period-1)*6+2*b
            out[offset] += factor*np.array((tau, 1/600, 0))
            out[offset+1] += factor*np.array((tau*tau, 2*tau/600, 1/360000))
    return out


@dataclass(frozen=True)
class ContextPopulation:
    """raw game moments in the frozen source player/context axes; no annual centering."""
    grouped: GroupedPopulation
    references: AnnualReferences
    J: np.ndarray
    L: np.ndarray
    P: sparse.csr_matrix
    Q: sparse.csr_matrix
    source_identity: dict
    receipt: dict

    def __post_init__(self):
        g, s, n = len(self.grouped.game_ids), len(self.references.strata), 2*len(self.references.player_ids)
        require(self.J.shape == (g, s, 18) and self.L.shape == (g, 18, 18)
                and self.J.dtype == self.L.dtype == np.dtype("float64")
                and self.P.shape == (g, 18*n) and self.Q.shape == (g, 18*656)
                and all(sparse.isspmatrix_csr(x) and x.has_canonical_format and x.dtype == np.dtype("float64")
                        and np.isfinite(x.data).all() for x in (self.P, self.Q))
                and np.isfinite(self.J).all() and np.isfinite(self.L).all(),
                "raw temporal moment axes, float64 storage or finite values differ")
        require(np.allclose(self.L, self.L.transpose(0, 2, 1), rtol=1e-12, atol=1e-12),
                "raw temporal exposure gram is asymmetric")


@dataclass(frozen=True)
class ContextTraining:
    """selected annual temporal likelihood and its fixed physical compensation geometry."""
    likelihood: "ShapeCoefficientLikelihood"
    scalar_likelihood: "ScalarScoreLikelihood"
    coarse_training: EmpiricalTraining
    coarse_scalar_likelihood: "ScalarCoefficientLikelihood"
    E: np.ndarray
    C0: np.ndarray
    N0: np.ndarray
    M: np.ndarray
    D: np.ndarray
    Ch: np.ndarray
    Nh: np.ndarray
    receipt: dict

    @property
    def season(self): return self.likelihood.season
    @property
    def player_ids(self): return self.likelihood.player_ids
    @property
    def strata(self): return self.coarse_training.strata
    @property
    def source_player_ids(self): return self.coarse_training.source_player_ids
    @property
    def game_ids(self): return self.coarse_training.game_ids
    @property
    def basis(self): return self.likelihood.basis
    @property
    def p(self): return self.basis.p
    @property
    def r(self): return self.likelihood.r
    @property
    def u(self): return self.likelihood.u
    @property
    def H(self): return self.likelihood.H
    @property
    def scalar_score(self): return self.scalar_likelihood.score
    @property
    def shape_score(self): return self.likelihood.Q
    @property
    def source_identity(self): return self.likelihood.source_identity
    @property
    def player_exposure(self): return self.coarse_training.player_exposure
    @property
    def directed_hours(self): return self.coarse_training.directed_hours
    @property
    def response_counts(self): return self.coarse_training.response_counts
    @property
    def xbar(self): return self.coarse_training.xbar
    @property
    def nbar(self): return self.coarse_training.nbar


def integrate_context_game(directed_rows, events, segments, references):
    """join accepted event assignments once and exhaust every retained per-cell count.

    event pre-scores are authoritative. the segment's accepted score-change
    chronology corroborates them without inventing an order among same-clock events.
    inclusive endpoints preserve the original assignment and add no exposure.
    """
    s, n = len(references.strata), 2*len(references.player_ids)
    J, L, P, Q = np.zeros((s, 18)), np.zeros((18, 18)), np.zeros((18, n)), np.zeros((18, 656))
    players = {p: i for i, p in enumerate(references.player_ids)}
    contexts = {c: i for i, c in enumerate(references.strata)}
    segments_by_id = {row["segment_index"]: row for row in segments}
    require(len(segments_by_id) == len(segments), "duplicate frozen segment index")
    joined, remaining = {}, {}
    for row in directed_rows:
        key = (row["game_id"], row["segment_index"], row["stratum"][0])
        require(key not in joined and tuple(row["stratum"]) in contexts
                and row["season"] == references.season and row["population"] == "unblocked_spatial",
                "directed context row identity or source axis differs")
        period, score = _context(row["stratum"])
        require(row["segment_index"] in segments_by_id, "directed row has no frozen segment")
        segment = segments_by_id[row["segment_index"]]
        side = row["stratum"][0]
        other = "home" if side == "away" else "away"
        require(all(row[k] == segment[k] for k in ("game_id", "season", "period", "start", "end"))
                and row["period"] == period and row["seconds"] == row["end"]-row["start"]
                and row["seconds"] > 0 and row["offense"] == segment[side+"_skaters"]
                and row["defense"] == segment[other+"_skaters"] and len(row["offense"]) == len(row["defense"]) == 5
                and len(set(row["offense"]+row["defense"])) == 10
                and all(p in players for p in row["offense"]+row["defense"]),
                "directed temporal row differs from its frozen segment, clock or lineup")
        # start-boundary goals are duplicated in both inclusive segment receipts.
        # segment.score already includes them and owns following elapsed time.
        state = segment["score"]
        starts = [change for change in segment["score_changes"] if change["elapsed_seconds"] == segment["start"]]
        require(not starts or (starts[-1]["post_score"] == state
                and all(left["post_score"] == right["pre_score"]
                        for left, right in zip(starts, starts[1:]))),
                "start-boundary score chronology differs from following elapsed state")
        last_clock = segment["start"]
        for change in segment["score_changes"]:
            clock = change["elapsed_seconds"]
            require(change["period"] == period and last_clock <= clock <= segment["end"],
                    "segment score-change chronology differs")
            if clock == segment["start"]:
                continue
            require(change["pre_score"] == state, "segment score-change pre-state differs")
            if clock > last_clock:
                require(max(-3, min(3, state[side]-state[other])) == score,
                        "positive-time clipped score changes within frozen row")
            last_clock, state = clock, change["post_score"]
        if last_clock < segment["end"] or not segment["score_changes"]:
            require(max(-3, min(3, state[side]-state[other])) == score,
                    "elapsed temporal exposure disagrees with frozen clipped score")
        j, l = temporal_moments(period, score, row["start"], row["end"])
        si = contexts[tuple(row["stratum"])]
        columns = [players[p] for p in row["offense"]]+[n//2+players[p] for p in row["defense"]]
        J[si] += j; L += l; P[:, columns] += j[:, None]
        require(all(type(cell) is int and type(count) is int and 0 <= cell < 656 and count > 0
                    for cell, count in row["counts"]) and len({c for c, _ in row["counts"]}) == len(row["counts"]),
                "retained row counts are not unique positive integer native counts")
        joined[key] = (row, segment)
        remaining[key] = dict(row["counts"])
    seen, endpoints, goals, simultaneous = set(), 0, 0, {}
    for event in events:
        if event["unblocked_spatial"] != "retained":
            continue
        locator = (event["game_id"], event["source_index"])
        key = (event["game_id"], event["assigned_segment"], event["side"])
        require(type(event["source_index"]) is int and event["source_index"] >= 0
                and locator not in seen and key in joined, "retained event has duplicate locator or no unique directed row")
        seen.add(locator)
        row, segment = joined[key]
        side, other = event["side"], "home" if event["side"] == "away" else "away"
        pre = event["pre_score"]
        require(isinstance(pre, dict) and set(pre) == {"away", "home"}
                and all(type(x) is int and x >= 0 for x in pre.values()), "event pre-score is unavailable")
        score = max(-3, min(3, pre[side]-pre[other]))
        require(event["season"] == row["season"] and event["period"] == row["period"]
                and row["start"] <= event["clock"] <= row["end"]
                and type(event["clock"]) is int and event["shooting_team_id"] == row["attacking_team"]
                and event["membership"][side+"_skaters"] == row["offense"]
                and event["membership"][other+"_skaters"] == row["defense"]
                and tuple(row["stratum"]) == (side, str(event["period"]) if event["period"] <= 3 else "overtime", score)
                and type(event["cell_id"]) is int and remaining[key].get(event["cell_id"], 0) > 0,
                "accepted event assignment differs from clock, membership, team, pre-score or native count")
        state = segment["score"]
        states_at_clock = [state]
        for change in segment["score_changes"]:
            if change["elapsed_seconds"] < event["clock"]:
                state = change["post_score"]; states_at_clock = [state]
            elif change["elapsed_seconds"] == event["clock"]:
                states_at_clock += [change["pre_score"], change["post_score"]]
        require(pre in states_at_clock, "event pre-score contradicts accepted score chronology")
        if event["type"] == "goal":
            matches = [c for c in segment["score_changes"] if c["source_index"] == event["source_index"]]
            require(len(matches) == 1 and matches[0]["pre_score"] == pre
                    and matches[0]["elapsed_seconds"] == event["clock"],
                    "goal pre-score is not its own frozen chronology state")
            goals += 1
        Q[:, event["cell_id"]] += temporal_basis(event["period"], score, event["clock"])
        remaining[key][event["cell_id"]] -= 1
        endpoints += int(event["clock"] in (row["start"], row["end"]))
        clock_key = (event["game_id"], event["period"], event["clock"])
        simultaneous[clock_key] = simultaneous.get(clock_key, 0)+1
    require(all(all(count == 0 for count in cells.values()) for cells in remaining.values()),
            "retained spatial event join does not exhaust frozen directed native counts")
    return J, L, sparse.csr_matrix(P.reshape(1, -1)), sparse.csr_matrix(Q.reshape(1, -1)), dict(
        retained_events=len(seen), directed_rows=len(directed_rows), inclusive_endpoint_events=endpoints,
        goals=goals, simultaneous_extra_events=sum(max(0, x-1) for x in simultaneous.values()))


def _rank_and_solve(D, right):
    require(D.shape == (18, 18) and D.dtype == np.dtype("float64") and np.isfinite(D).all()
            and np.allclose(D, D.T, rtol=1e-10, atol=1e-10) and np.all(np.diag(D) > 0),
            "temporal centered gram is nonfinite, asymmetric or lacks positive diagonal")
    scale = np.sqrt(np.diag(D))
    correlation = D/scale[:, None]/scale[None, :]
    eigenvalues = np.linalg.eigvalsh(correlation)
    threshold = 18*np.finfo(np.float64).eps*eigenvalues[-1]
    require(eigenvalues[0] > threshold, "temporal centered exposure does not support all eighteen columns")
    solved = np.linalg.solve(D, right)
    residual = float(np.linalg.norm(D@solved-right)/max(1., np.linalg.norm(right)))
    require(np.isfinite(solved).all() and residual <= 1e-8, "temporal centered solve is nonfinite or inaccurate")
    return solved, dict(correlation_eigenvalues=eigenvalues.tolist(), rank=18,
        rank_threshold=float(threshold), correlation_condition=float(eigenvalues[-1]/eigenvalues[0]),
        solve_relative_residual=residual)


def context_training(population, references, train_ids, basis):
    """residualize the fixed basis using training exposure, never assessment means."""
    from .attribution import ShapeCoefficientLikelihood, ScalarScoreLikelihood

    require(population.references.season == references.season
            and population.references.player_ids == references.player_ids
            and population.references.strata == references.strata,
            "temporal training references differ from raw population")
    grouped = population.grouped
    coarse, scalar = complete_training(grouped, references, tuple(train_ids), basis)
    gi = np.array([grouped.game_ids.index(game) for game in coarse.game_ids])
    s, n = len(references.strata), 2*len(references.player_ids)
    context_indices = np.array([references.strata.index(c) for c in coarse.strata])
    active = np.array([references.player_ids.index(p) for p in coarse.likelihood.player_ids])
    columns = np.r_[active, n//2+active]
    E = grouped.stratum_e[gi].sum(axis=0)[context_indices]
    C0 = np.asarray(grouped.stratum_x[gi].sum(axis=0)).reshape(s, n)[np.ix_(context_indices, columns)]
    N0 = np.asarray(grouped.stratum_n[gi].sum(axis=0)).reshape(s, 656)[context_indices]
    J = population.J[gi].sum(axis=0)[context_indices]
    L = population.L[gi].sum(axis=0)
    P = np.asarray(population.P[gi].sum(axis=0)).reshape(18, n)[:, columns]
    Q = np.asarray(population.Q[gi].sum(axis=0)).reshape(18, 656)
    M = J/E[:, None]
    D = L-J.T@M
    D = (D+D.T)/2
    Ch, Nh = P-M.T@C0, Q-M.T@N0
    solved, rank = _rank_and_solve(D, np.hstack((Ch, Nh)))
    nc = len(columns)
    H = coarse.likelihood.H-coarse.likelihood.r*Ch.T@solved[:, :nc]
    H = (H+H.T)/2
    T = np.asarray(grouped.T_raw[gi].sum(axis=0)).reshape(n, 656)[columns]-C0.T@(N0/E[:, None])-Ch.T@solved[:, nc:]
    score = T.sum(axis=1)[:, None]
    shape_score = T@basis.B
    gauges = np.zeros((nc, 2)); gauges[:nc//2, 0] = 1; gauges[nc//2:, 1] = 1
    errors = dict(training_centering=float(np.max(np.abs(J-E[:, None]*M))),
        spatial_centering=float(np.max(np.abs(basis.p@basis.B))),
        information_role_gauges=float(np.max(np.abs(H@gauges))/max(1., np.linalg.norm(H))),
        scalar_role_gauges=float(np.max(np.abs(gauges.T@score))/max(1., np.linalg.norm(score))),
        shape_role_gauges=float(np.max(np.abs(gauges.T@shape_score))/max(1., np.linalg.norm(shape_score))))
    require(all(value <= 1e-8 for value in errors.values())
            and np.allclose(C0/E[:, None], coarse.xbar, rtol=1e-8, atol=1e-10)
            and np.allclose(N0/E[:, None], coarse.nbar, rtol=1e-8, atol=1e-10),
            "temporal centering, spatial basis, role gauges or coarse references differ")
    identity_value = dict(coarse.source_identity, context_design="period_score_quadratic_18_v1",
        basis_columns=list(BASIS_COLUMNS), raw_temporal_identity=population.source_identity,
        centering="selected training exposure only", centering_sha256=ordered_array_digest(dict(M=M)))
    likelihood = ShapeCoefficientLikelihood(references.season, coarse.likelihood.player_ids, H,
        shape_score, coarse.likelihood.u, coarse.likelihood.r, basis, identity_value)
    scalar_likelihood = ScalarScoreLikelihood(references.season, likelihood.player_ids, H, score,
        likelihood.u, likelihood.r, identity_value)
    receipt = dict(rank=rank, algebra=errors, coarse_equivalence=population.receipt,
        units=dict(E="directed_hours", D="directed_hours", H="recorded_attempts", score="recorded_attempts"))
    return ContextTraining(likelihood, scalar_likelihood, coarse, scalar, E, C0, N0, M, D, Ch, Nh, receipt)


def context_game_moments(population, training, game_id):
    """general context gram and sparse player blocks using saved training centering."""
    refs, grouped = population.references, population.grouped
    game = empirical_game_moments(grouped, refs, game_id)
    index = grouped.game_ids.index(game_id)
    keep = np.array([refs.strata.index(c) for c in training.strata])
    omitted = sorted(set(range(len(refs.strata)))-set(keep))
    require(not omitted or (np.all(game["E"][omitted] == 0) and np.all(game["N"][omitted] == 0)
                           and game["C"][omitted].nnz == 0 and not np.any(population.J[index, omitted])),
            "positive-time assessment context is absent from training")
    E, C0, N0 = game["E"][keep], game["C"][keep], game["N"][keep]
    J, L, M = population.J[index, keep], population.L[index], training.M
    P = population.P[index].reshape((18, 2*len(refs.player_ids))).tocsr()
    Q = population.Q[index].toarray().reshape(18, 656)
    cross = J-E[:, None]*M
    D = L-J.T@M-M.T@J+M.T@(E[:, None]*M)
    G = np.block([[np.diag(E), cross], [cross.T, D]])
    C = sparse.vstack((C0, P-sparse.csr_matrix(M.T@C0)), format="csr")
    N = np.vstack((N0, Q-M.T@N0))
    result = dict(game_id=game_id, E=E, G=G, C=C, A=game["A"], N=N, K=game["K"],
        context_integral=np.r_[E, J.sum(axis=0)-E@M], directed_hours=float(E.sum()), p=refs.p,
        context_ids=training.strata+TEMPORAL_IDS, player_ids=refs.player_ids)
    validate_context_game(result)
    return result


def validate_context_game(game):
    """cross-check continuous moments once at their owning game boundary."""
    E, G, integral, C = (game[name] for name in ("E", "G", "context_integral", "C"))
    s, n = len(E), 2*len(game["player_ids"])
    require(E.dtype == G.dtype == integral.dtype == np.dtype("float64")
            and E.ndim == 1 and G.shape == (s+18, s+18) and integral.shape == (s+18,)
            and C.shape == (s+18, n) and np.all(E >= 0)
            and all(np.isfinite(value).all() for value in (E,G,integral,C.data))
            and np.allclose(G, G.T, rtol=1e-8, atol=1e-10)
            and np.allclose(G[:s,:s], np.diag(E), rtol=1e-8, atol=1e-10)
            and np.allclose(integral[:s], E, rtol=1e-8, atol=1e-10)
            and np.allclose(integral[s:], G[:s,s:].sum(axis=0), rtol=1e-8, atol=1e-10)
            and np.isclose(game["directed_hours"], E.sum(), rtol=1e-8, atol=1e-10)
            and all(np.allclose(np.asarray(C[:,sl].sum(axis=1)).ravel(), 5*integral,
                                rtol=1e-8, atol=1e-10) for sl in (slice(0,n//2),slice(n//2,n))),
            "continuous game gram, context integral, hours or five-player exposure differ")


def _game_groups(iterator, inventory):
    """stream frozen ledger groups once; empty inventory games remain explicit."""
    groups = iter(groupby(iterator, key=lambda row: row["game_id"]))
    current = next(groups, None)
    for game in inventory:
        require(current is None or current[0] >= game, "source ledger game order or inventory differs")
        if current is not None and current[0] == game:
            yield list(current[1])
            current = next(groups, None)
        else:
            yield []
    require(current is None, "source ledger has a game outside frozen inventory")


def iter_context_rows(source, metadata, season=None, game_ids=None):
    """corrected original directed rows, for bounded physical sign diagnostics."""
    selected = None if game_ids is None else set(game_ids)
    exclusions = {(r["game_id"], r["segment_index"], r["stratum"][0]): r for r in metadata["correction"]["rows"]}
    seasons = source.seasons if season is None else (season,)
    for season_value in seasons:
        if "rows" in metadata:
            iterator = iter(metadata["rows"][source.seasons.index(season_value)])
        else:
            iterator = rows(linked_path(metadata["row_references"][season_value]))
        for row in iterator:
            key = (row["game_id"], row["segment_index"], row["stratum"][0])
            if key in exclusions:
                require(row == exclusions[key], "corrected source exclusion payload differs")
                continue
            if selected is None or row["game_id"] in selected:
                yield row


def prepare_context_source(source, metadata):
    """integrate all corrected games and reconcile coarse frozen A/C/E/N/K first."""
    inventory = tuple(game for grouped in source.grouped for game in grouped.game_ids)
    if "events" in metadata:
        event_iterator = iter(metadata["events"])
        segment_iterator = iter(metadata["segments"])
    else:
        event_iterator = rows(linked_path(metadata["events_reference"]))
        segment_iterator = rows(linked_path(metadata["segments_reference"]))
    event_groups = iter(_game_groups(event_iterator, inventory))
    segment_groups = iter(_game_groups(segment_iterator, inventory))
    populations = []
    for grouped, refs in zip(source.grouped, source.references, strict=True):
        row_groups = _game_groups(iter_context_rows(source, metadata, refs.season), grouped.game_ids)
        js, ls, ps, qs, event_count, row_count = [], [], [], [], 0, 0
        endpoints = goals = simultaneous = 0
        errors = {name: 0. for name in ("H_e", "T_raw", "stratum_x", "stratum_n", "stratum_e", "Q_t", "Q_h")}
        for game, batch in zip(grouped.game_ids, row_groups, strict=True):
            events, segments = next(event_groups), next(segment_groups)
            j, l, p, q, receipt = integrate_context_game(batch, events, segments, refs)
            if batch:
                replay = group_observations(iter(batch), refs, (game,))
                actual = verify_grouped_game(replay, grouped, refs, game)
                for name, value in actual.items(): errors[name] = max(errors[name], value)
            else:
                gi = grouped.game_ids.index(game)
                require(not grouped.H_e[gi].nnz and not grouped.T_raw[gi].nnz
                        and not grouped.stratum_x[gi].nnz and not grouped.stratum_n[gi].nnz
                        and not np.any(grouped.stratum_e[gi]) and grouped.Q_t[gi] == grouped.Q_h[gi] == 0,
                        "zero-row inventory game contains frozen moments")
            js.append(j); ls.append(l); ps.append(p); qs.append(q)
            event_count += receipt["retained_events"]; row_count += len(batch)
            endpoints += receipt["inclusive_endpoint_events"]; goals += receipt["goals"]
            simultaneous += receipt["simultaneous_extra_events"]
        require(row_count == grouped.row_count and event_count == int(grouped.stratum_n.sum()),
                "temporal source changes corrected row or retained event support")
        receipt = dict(status="verified", game_count=len(grouped.game_ids), directed_rows=row_count,
            retained_events=event_count, inclusive_endpoint_events=endpoints, goals=goals,
            simultaneous_extra_events=simultaneous, coarse_moment_max_absolute_errors=errors)
        source_identity = dict(source=source.source_identity, correction=metadata["correction_reference"],
            season=refs.season, events=metadata["events_reference"], segments=metadata["segments_reference"],
            rows=metadata["row_references"][refs.season], fixed_basis_columns=list(BASIS_COLUMNS))
        populations.append(ContextPopulation(grouped, refs, np.asarray(js), np.asarray(ls),
            sparse.vstack(ps, format="csr"), sparse.vstack(qs, format="csr"), source_identity, receipt))
    require(next(event_groups, None) is None and next(segment_groups, None) is None,
            "temporal source did not consume frozen ledger inventory")
    return tuple(populations)




def context_population_arrays(population):
    """finite typed archive members, including original coarse energy for control checks."""
    grouped, refs = population.grouped, population.references
    result = dict(J=population.J, L=population.L, stratum_e=grouped.stratum_e,
        Q_t=grouped.Q_t, Q_h=grouped.Q_h, reference_u=refs.u, reference_p=refs.p,
        reference_player_exposure=refs.player_exposure, reference_response_counts=refs.response_counts)
    for name, matrix in (("P", population.P), ("Q", population.Q), ("H_e", grouped.H_e),
                          ("T_raw", grouped.T_raw), ("stratum_x", grouped.stratum_x), ("stratum_n", grouped.stratum_n)):
        for suffix, value in (("data", matrix.data), ("indices", matrix.indices), ("indptr", matrix.indptr)):
            result[name+"_"+suffix] = value
    return result


def context_population_row(population, prefix):
    refs = population.references
    return dict(prefix=prefix, season=refs.season, season_index=refs.season_index, players=list(refs.player_ids),
        strata=list(map(list, refs.strata)), game_ids=list(population.grouped.game_ids), r=refs.r,
        benchmark=refs.benchmark, protocol_sha256=refs.protocol_sha256, population_id=refs.population_id,
        membership_signatures=list(population.grouped.membership_signatures), row_count=population.grouped.row_count,
        correction_identity=population.grouped.correction_identity, source_identity=population.source_identity,
        receipt=population.receipt)


def _sparse_decode(arrays, name, shape):
    data, indices, indptr = (arrays[name+"_"+suffix] for suffix in ("data", "indices", "indptr"))
    require(data.dtype == np.dtype("float64") and indices.dtype.kind in "iu" and indptr.dtype.kind in "iu"
            and data.ndim == indices.ndim == indptr.ndim == 1 and len(data) == len(indices)
            and indptr.shape == (shape[0]+1,) and indptr[0] == 0 and indptr[-1] == len(data)
            and np.all(indptr[1:] >= indptr[:-1]) and np.all((0 <= indices) & (indices < shape[1]))
            and np.isfinite(data).all(), "temporal sparse archive storage differs: "+name)
    matrix = sparse.csr_matrix((data, indices, indptr), shape=shape)
    require(matrix.has_canonical_format, "temporal sparse archive is not canonical: "+name)
    return matrix


def decode_context_population(row, arrays):
    """decode exactly the explicit source axes; no source discovery or fallback reader."""
    players, strata, games = tuple(row["players"]), tuple(map(tuple, row["strata"])), tuple(row["game_ids"])
    n, s, g = 2*len(players), len(strata), len(games)
    require(players == tuple(sorted(set(players))) and all(type(p) is int for p in players)
            and strata == tuple(sorted(set(strata))) and games == tuple(sorted(set(games))),
            "temporal saved source axes are unordered or duplicated")
    for context in strata: _context(context)
    matrices = {name: _sparse_decode(arrays, name, (g, width)) for name, width in
        (("H_e", n*n), ("T_raw", n*656), ("stratum_x", s*n), ("stratum_n", s*656), ("P", 18*n), ("Q", 18*656))}
    refs = AnnualReferences(row["benchmark"], row["season"], row["season_index"], row["protocol_sha256"],
        row["population_id"], players, strata, row["r"], arrays["reference_u"], arrays["reference_p"],
        arrays["reference_player_exposure"], arrays["reference_response_counts"])
    grouped = GroupedPopulation(games, matrices["H_e"], matrices["T_raw"], arrays["stratum_e"],
        matrices["stratum_x"], matrices["stratum_n"], arrays["Q_t"], arrays["Q_h"],
        tuple(row["membership_signatures"]), row["row_count"], row["correction_identity"])
    result = ContextPopulation(grouped, refs, arrays["J"], arrays["L"], matrices["P"], matrices["Q"], row["source_identity"], row["receipt"])
    require(set(arrays) == set(context_population_arrays(result)), "temporal population archive members differ")
    for name, value in context_population_arrays(result).items():
        require(value.dtype.kind in "iuf" and np.isfinite(value).all(), "temporal population archive contains invalid values: "+name)
    require(grouped.stratum_e.shape == (g, s) and grouped.Q_t.shape == grouped.Q_h.shape == (g,)
            and grouped.stratum_e.dtype == grouped.Q_t.dtype == grouped.Q_h.dtype == np.dtype("float64")
            and refs.u.shape == refs.player_exposure.shape == (n//2,) and refs.p.shape == refs.response_counts.shape == (656,)
            and all(x.dtype == np.dtype("float64") and np.isfinite(x).all() for x in
                    (refs.u, refs.p, refs.player_exposure, refs.response_counts))
            and np.all(refs.u > 0) and np.all(refs.p > 0) and abs(refs.u.sum()-1) <= 1e-12
            and abs(refs.p.sum()-1) <= 1e-12 and np.isfinite(refs.r) and refs.r > 0
            and all(np.all(x >= 0) for x in (grouped.stratum_e, grouped.Q_t, grouped.Q_h,
                grouped.H_e.data, grouped.T_raw.data, grouped.stratum_x.data, grouped.stratum_n.data)),
            "temporal coarse archive exposure, references or response axes differ")
    return result


def context_training_arrays(training):
    coarse, scalar = training.coarse_training, training.coarse_scalar_likelihood
    return dict(H=training.H, Q=training.shape_score, scalar_score=training.scalar_score,
        u=training.u, E=training.E, C0=training.C0, N0=training.N0, M=training.M, D=training.D,
        Ch=training.Ch, Nh=training.Nh, coarse_H=coarse.likelihood.H, coarse_Q=coarse.likelihood.Q,
        coarse_scalar_score=scalar.score, coarse_scalar_energy=np.array([scalar.energy]),
        xbar=coarse.xbar, nbar=coarse.nbar, player_exposure=coarse.player_exposure,
        response_counts=coarse.response_counts)


def context_training_row(training, prefix):
    coarse = training.coarse_training
    return dict(prefix=prefix, season=training.season, players=list(training.player_ids),
        source_player_ids=list(coarse.source_player_ids), strata=list(map(list, training.strata)),
        source_strata=list(map(list, coarse.source_strata)), game_ids=list(training.game_ids),
        r=training.r, directed_hours=training.directed_hours, source_identity=training.source_identity,
        coarse_source_identity=coarse.source_identity, coarse_scalar_source_identity=training.coarse_scalar_likelihood.source_identity,
        receipt=training.receipt)


def decode_context_training(row, arrays, basis):
    from .attribution import ShapeCoefficientLikelihood, ScalarCoefficientLikelihood, ScalarScoreLikelihood

    players, strata = tuple(row["players"]), tuple(map(tuple, row["strata"]))
    n, s = 2*len(players), len(strata)
    shapes = dict(H=(n,n), Q=(n,40), scalar_score=(n,1), u=(n//2,), E=(s,), C0=(s,n), N0=(s,656),
        M=(s,18), D=(18,18), Ch=(18,n), Nh=(18,656), coarse_H=(n,n), coarse_Q=(n,40),
        coarse_scalar_score=(n,1), coarse_scalar_energy=(1,), xbar=(s,n), nbar=(s,656),
        player_exposure=(n//2,), response_counts=(656,))
    require(set(arrays) == set(shapes) and all(isinstance(v, np.ndarray) and v.shape == shapes[k]
        and v.dtype == np.dtype("float64") and np.isfinite(v).all() for k,v in arrays.items())
        and players == tuple(sorted(set(players))) and strata == tuple(sorted(set(strata)))
        and np.all(arrays["E"] > 0) and np.all(arrays["u"] > 0) and abs(arrays["u"].sum()-1) <= 1e-12
        and np.isfinite(row["r"]) and row["r"] > 0 and arrays["coarse_scalar_energy"][0] >= 0,
        "saved temporal training axes, float64 moments or references differ")
    shape = ShapeCoefficientLikelihood(row["season"], players, arrays["H"], arrays["Q"], arrays["u"], row["r"], basis, row["source_identity"])
    scalar = ScalarScoreLikelihood(row["season"], players, arrays["H"], arrays["scalar_score"], arrays["u"], row["r"], row["source_identity"])
    coarse_shape = ShapeCoefficientLikelihood(row["season"], players, arrays["coarse_H"], arrays["coarse_Q"], arrays["u"], row["r"], basis, row["coarse_source_identity"])
    coarse_scalar = ScalarCoefficientLikelihood(row["season"], players, arrays["coarse_H"], arrays["coarse_scalar_score"],
        float(arrays["coarse_scalar_energy"][0]), arrays["u"], row["r"], row["coarse_scalar_source_identity"])
    coarse = EmpiricalTraining(coarse_shape, tuple(row["game_ids"]), tuple(row["source_player_ids"]), strata,
        tuple(map(tuple,row["source_strata"])), arrays["xbar"], arrays["nbar"], arrays["player_exposure"],
        row["directed_hours"], arrays["response_counts"], row["coarse_source_identity"])
    _rank_and_solve(arrays["D"], np.hstack((arrays["Ch"], arrays["Nh"])))
    require(np.allclose(arrays["C0"]/arrays["E"][:,None], arrays["xbar"], rtol=1e-8, atol=1e-10)
            and np.allclose(arrays["N0"]/arrays["E"][:,None], arrays["nbar"], rtol=1e-8, atol=1e-10)
            and np.isclose(arrays["E"].sum(), row["directed_hours"], rtol=1e-8, atol=1e-10),
            "saved temporal training coarse compensation differs")
    return ContextTraining(shape, scalar, coarse, coarse_scalar, *(arrays[name] for name in ("E","C0","N0","M","D","Ch","Nh")), row["receipt"])


