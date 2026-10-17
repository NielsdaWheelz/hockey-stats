"""shared synthetic designs, physical truths and exact known-law moments."""

from itertools import combinations

import numpy as np
from scipy import sparse

from .artifacts import ordered_array_digest, require
from .chance_evaluation import REGION_NAMES, compound_regions
from .shot_origins import grid


PAIR_SLOTS = (((0, 1), (2, 3), (4, 5), (6, 7)),) * 3 + (((0, 1), (2, 7), (3, 4), (5, 6)),)


def synthetic_counts(design: dict, case_id: int, outer_id: int, year_index: int) -> np.ndarray:
    """the original 04c response stream; callers supply its fixed design and ids."""
    require(type(case_id) is int and case_id in (0, 1) and type(outer_id) is int and outer_id >= 0,
            "invalid synthetic response identity")
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([40430, case_id, outer_id, year_index])))
    return synthetic_response(design, design["mu"], ("gaussian", "game_pace")[case_id], rng)


def synthetic_response(design: dict, rates: np.ndarray, law: str, rng: np.random.Generator) -> np.ndarray:
    """draw one explicit response stream in game/stint/direction/native-cell order."""
    exposure, shares = design["e"], design["p"]
    require(isinstance(rng, np.random.Generator) and law in ("gaussian", "game_pace")
            and exposure.ndim == 1 and shares.shape == (656,)
            and rates.shape == (len(exposure), len(shares))
            and np.isfinite(rates).all() and np.all(rates > 0)
            and np.isfinite(exposure).all() and np.all(exposure > 0)
            and np.isfinite(shares).all() and np.all(shares > 0)
            and abs(float(shares.sum()) - 1) <= 1e-12,
            "invalid explicit synthetic response law or generating rates")
    means = exposure[:, None] * rates
    if law == "gaussian":
        return rng.normal(means, np.sqrt(design["e"][:, None] * 40 * design["p"]))
    responses = np.empty_like(means)
    row_games = np.asarray(design["row_game_ids"])
    games = design["game_ids"]
    require(row_games.shape == (len(exposure),) and games == tuple(sorted(set(games)))
            and np.array_equal(np.unique(row_games), games)
            and np.all(row_games[1:] >= row_games[:-1]),
            "synthetic game rows differ from the ordered game inventory")
    for game in games:
        pace = rng.gamma(shape=2, scale=.5)
        rows = row_games == game
        responses[rows] = rng.poisson(pace * means[rows])
    return responses


def synthetic_designs() -> dict[str, list[dict]]:
    """the original 04a lineup stream; its mixed pass precedes the paired pass."""
    rng = np.random.Generator(np.random.PCG64(40400))
    return {case: _lineup_history(rng, case, 16, 50) for case in ("mixed", "paired")}


def paired_designs(rng: np.random.Generator, *, repetitions: int = 16,
                   stints_per_game: int = 50, purpose: str = "research") -> list[dict]:
    """direct paired history; fixture reductions must carry their declared purpose."""
    require(isinstance(rng, np.random.Generator) and purpose in ("research", "fixture_exercise")
            and type(repetitions) is int and 1 <= repetitions <= 16
            and type(stints_per_game) is int and 3 <= stints_per_game <= 50
            and (purpose == "fixture_exercise" or (repetitions == 16 and stints_per_game == 50)),
            "paired design requires the research schedule or an explicit smaller fixture")
    years = _lineup_history(rng, "paired", repetitions, stints_per_game)
    for design in years:
        del design["scalar_ticks"]
        design["synthetic_design"] = dict(purpose=purpose, repetitions=repetitions,
                                          stints_per_game=stints_per_game)
    return years


def synthetic_rosters(year: int) -> list[list[int]]:
    """the five-year team-slot identities, including entry and return."""
    require(type(year) is int and 0 <= year < 5, "synthetic roster year must be 0 through 4")
    active = [list(range(team * 8, team * 8 + 8)) for team in range(4)]
    if year >= 2:
        active[0][0], active[1][0] = 32, 33
    if year >= 3:
        active[1][1] = 8
    return active


def _lineup_history(rng: np.random.Generator, case: str, repetitions: int,
                    stints_per_game: int) -> list[dict]:
    years = []
    for year in range(5):
        active = synthetic_rosters(year)
        players = tuple(sorted(player for team in active for player in team))
        positions = {player: i for i, player in enumerate(players)}
        n = len(players)
        offense, defense, seconds, contexts, home_teams, away_teams = [], [], [], [], [], []
        for repetition in range(repetitions):
            for first, second in combinations(range(4), 2):
                home, away = (first, second) if repetition % 2 == 0 else (second, first)
                home_teams.append(home)
                away_teams.append(away)
                for stint in range(stints_per_game):
                    lineups = {}
                    for team in (away, home):
                        if case == "paired" and team == 3:
                            remainder = [player for player in active[team] if player not in (26, 31)]
                            lineup = ([26, 31, *rng.choice(remainder, 3, replace=False)]
                                      if rng.random() < 5 / 8 else rng.choice(remainder, 5, replace=False))
                        else:
                            lineup = rng.choice(active[team], 5, replace=False)
                        lineups[team] = sorted(int(player) for player in lineup)
                    for side, attack, defend in (("away", away, home), ("home", home, away)):
                        offense.append(lineups[attack])
                        defense.append(lineups[defend])
                        seconds.append((15, 30, 45)[stint % 3])
                        contexts.append((side, str(1 + stint % 3), 0))
        offense, defense = np.asarray(offense, dtype=np.int64), np.asarray(defense, dtype=np.int64)
        seconds = np.asarray(seconds, dtype=float)
        strata = tuple(sorted(set(contexts)))
        strata_positions = {value: i for i, value in enumerate(strata)}
        si = np.asarray([strata_positions[value] for value in contexts], dtype=np.int64)
        indices = np.array([[positions[player] for player in attacking]
                            + [n + positions[player] for player in defending]
                            for attacking, defending in zip(offense, defense, strict=True)])
        X = sparse.csr_matrix((np.ones(indices.size),
                               (np.repeat(np.arange(len(indices)), 10), indices.ravel())),
                              shape=(len(indices), 2 * n))
        offense_ticks = np.tile(np.array([-4, -2, 0, 0, 0, 0, 2, 4], dtype=np.int64), 4)
        defense_ticks = np.tile(np.array([2, 0, -2, 0, 4, 0, -4, 0], dtype=np.int64), 4)
        if year >= 3:
            offense_ticks[1] += 1
        offense_ticks = np.concatenate((offense_ticks, [2, 0]))
        defense_ticks = np.concatenate((defense_ticks, [0, 0]))
        scalar_ticks = np.concatenate((offense_ticks[list(players)], defense_ticks[list(players)]))
        exposure = np.asarray(X[:, :n].T @ seconds).ravel()
        years.append(dict(players=players, offense=offense, defense=defense, seconds=seconds,
                          strata=strata, si=si, X=X, scalar_ticks=scalar_ticks,
                          home_teams=np.asarray(home_teams), away_teams=np.asarray(away_teams),
                          e=seconds / 3600, player_exposure=exposure,
                          game_ids=tuple(range(6 * repetitions)),
                          row_game_ids=np.repeat(np.arange(6 * repetitions), 2 * stints_per_game),
                          u=exposure / exposure.sum()))
    return years



def _truth_rng(seed):
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed)))


def _physical_lobe(centers, p, seed, amplitude):
    rng = _truth_rng(seed)
    x1, y1, w1 = rng.uniform(0, 80), rng.uniform(-30, 30), rng.uniform(20, 40)
    x2, y2, w2 = rng.uniform(0, 80), rng.uniform(-30, 30), rng.uniform(20, 40)
    g0 = (np.exp(-np.sum((centers - [x1, y1]) ** 2, axis=1) / (2 * w1 ** 2))
          - np.exp(-np.sum((centers - [x2, y2]) ** 2, axis=1) / (2 * w2 ** 2)))
    centered = g0 - p @ g0
    normalizer = float(np.max(np.abs(centered)))
    require(np.isfinite(normalizer) and normalizer > 0, "invalid physical lobe normalization")
    return amplitude * p * centered / normalizer


def independent_truths(designs, p, population, outer):
    """draw physical slot fields before any response; no fitted directions enter."""
    require(population in ("sparse", "diffuse") and type(outer) is int and outer >= 0,
            "invalid independent truth identity")
    centers, fields, activation = grid()[0], {}, []
    for team in range(4):
        for role in range(2):
            slots = sorted(_truth_rng([40803, outer, team, role]).choice(8, 2, replace=False).tolist())
            if population == "diffuse":
                slots = list(range(8))
            activation.append(dict(team=team, role=("offense", "defense")[role], slots=slots))
            for slot in range(8):
                fields[(team, role, slot)] = _physical_lobe(centers, p, [40802, outer, team, role, slot], .09)
    truths = []
    for year, design in enumerate(designs):
        rosters, players = synthetic_rosters(year), design["players"]
        require(players == tuple(sorted(player for team in rosters for player in team)),
                "independent physical roster differs from fixed deployment")
        positions, n = {player: i for i, player in enumerate(players)}, len(players)
        raw, active = np.zeros((2 * n, len(p))), np.zeros(2 * n, dtype=bool)
        for row in activation:
            role, team = int(row["role"] == "defense"), row["team"]
            for slot in row["slots"]:
                index = role * n + positions[rosters[team][slot]]
                raw[index], active[index] = fields[(team, role, slot)], True
        means = np.array([design["u"] @ raw[role * n:(role + 1) * n] for role in range(2)])
        centered = raw - np.repeat(means, n, axis=0)
        context = 5 * means.sum(axis=0)
        floor = dict(sparse=.64, diffuse=.10)[population]
        rates = 40 * (p + design["X"] @ raw)
        require(np.isfinite(raw).all() and np.isfinite(centered).all() and np.isfinite(context).all()
                and np.max(np.abs(raw.sum(axis=1))) <= 1e-12
                and np.max(np.abs(centered.sum(axis=1))) <= 1e-12
                and all(np.max(np.abs(design["u"] @ centered[role*n:(role+1)*n])) <= 1e-12
                        for role in range(2))
                and np.all(rates > 0) and np.all(rates >= floor * 40 * p - 1e-12)
                and np.max(np.abs(rates - 40 * (p + context + design["X"] @ centered))) <= 1e-12,
                "independent truth positivity, normalization or role compensation failed")
        truths.append(dict(raw=raw, centered=centered, context=context, activation=activation, active=active))
    return truths


def paired_truths(designs, p, population, outer):
    """physical fields precede response draws and have no basis-dependent selection."""
    require(population in ("sparse", "diffuse", "null") and type(outer) is int and outer >= 0, "invalid truth identity")
    centers = grid()[0]
    fields, active = {}, {}
    for team in range(4):
        for role in range(2):
            selected = int(_truth_rng([40603, outer, team, role]).integers(0, 4))
            for pair in range(4):
                fields[(team, role, pair)] = _physical_lobe(centers, p, [40602, outer, team, role, pair], .10)
                active[(team, role, pair)] = population == "diffuse" or (population == "sparse" and pair == selected)
    truths = []
    for year, design in enumerate(designs):
        rosters = synthetic_rosters(year)
        players = design["players"]
        positions, n = {player: i for i, player in enumerate(players)}, len(players)
        require(players == tuple(sorted(player for team in rosters for player in team)),
                "physical truth roster differs from fixed design")
        raw = np.zeros((2 * n, len(p)))
        pairs = []
        for team, roster in enumerate(rosters):
            for role in range(2):
                for pair, slots in enumerate(PAIR_SLOTS[team]):
                    first, second = (roster[slot] for slot in slots)
                    is_active = active[(team, role, pair)]
                    if is_active:
                        raw[role * n + positions[first]] = fields[(team, role, pair)]
                        raw[role * n + positions[second]] = -fields[(team, role, pair)]
                    pairs.append(dict(team=team, role=("offense", "defense")[role], pair=pair,
                                      players=[first, second], active=is_active,
                                      expected_estimable=[first, second] != [26, 31]))
        centered = raw.copy()
        means = np.array([design["u"] @ raw[role * n:(role + 1) * n] for role in range(2)])
        for role in range(2):
            centered[role * n:(role + 1) * n] -= means[role]
        context = 5 * means.sum(axis=0)
        rates = 40 * (p + design["X"] @ raw)
        floor = dict(sparse=.8, diffuse=.4, null=1.)[population]
        require(np.isfinite(raw).all() and np.max(np.abs(raw.sum(axis=1))) <= 1e-12
                and np.max(np.abs(centered.sum(axis=1))) <= 1e-12
                and np.all(rates > 0) and np.all(rates >= floor * 40 * p - 1e-12)
                and np.max(np.abs(rates - 40 * (p + context + design["X"] @ centered))) <= 1e-12,
                "physical truth positivity, zero sums or reference compensation failed")
        truths.append(dict(raw=raw, centered=centered, context=context, pairs=pairs))
    return truths


def truth_digest(truths):
    return ordered_array_digest({f"{year}_{name}": truth[name] for year, truth in enumerate(truths)
                                 for name in ("raw", "centered", "context")})


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


def _residual_noise_gram(X, Z, xbar, weights):
    """contract scalar row variances against the original residualized design."""
    raw = (X.T @ X.multiply(weights[:, None])).toarray()
    context_x = (Z.T @ X.multiply(weights[:, None])).toarray()
    cross = context_x.T @ xbar
    moment = raw - cross - cross.T + xbar.T @ (np.asarray(Z.T @ weights)[:, None] * xbar)
    return (moment + moment.T) / 2


def known_shape_moments(designs, truths, selections, B, p, *, r=40., law,
                        alpha=1., copies=1, operators):
    """exact pooled score contractions, conditional on positive physical means.

    each design owns H/xbar from its original exposure residualization. selections
    map ordered union rows to that year's current rows. truths contain uncentered
    physical `raw` maps; their exposure means must not be discarded. operators
    score native maps. context_cross_score has union rows by final-year strata.
    copies repeats complete independent games, including independent pace draws.
    no response or covariance over recorded native counts is constructed.
    """
    require(law in ("gaussian", "game_pace") and np.isfinite(r) and r > 0
            and np.isfinite(alpha) and 0 < alpha <= 1
            and type(copies) is int and copies >= 1
            and len(designs) == len(truths) == len(selections) > 0
            and B.ndim == 2 and p.shape == (B.shape[0],) and B.shape[1] > 0
            and np.isfinite(p).all() and np.all(p > 0) and abs(float(p.sum())-1) <= 1e-12
            and np.isfinite(B).all()
            and np.allclose(p @ B, 0., atol=1e-10, rtol=0.)
            and np.allclose(B.T @ (p[:, None]*B), np.eye(B.shape[1]), atol=1e-10, rtol=1e-8),
            "invalid known-law shape moment contract")
    n, d = selections[0].shape[1], B.shape[1]
    R = p[:, None]*B
    require(bool(operators) and all(V.ndim == 2 and V.shape[0] == len(p)
            and V.shape[1] > 0 and np.isfinite(V).all() for V in operators),
            "native scoring operators must be finite matrices")
    projected = tuple(R.T @ V for V in operators)
    # the last contraction is the inverse-share prediction metric, D=I.
    metrics = np.column_stack([np.sum((B @ D)**2, axis=1) for D in projected]
                              + [np.sum(B**2, axis=1)])
    H, m = np.zeros((n, n)), np.zeros((n, d))
    covariances = [np.zeros_like(H) for _ in operators]
    prediction_covariance = np.zeros_like(H)
    f = np.zeros((n, len(designs[-1]["strata"])))
    for year, (design, truth, S) in enumerate(zip(designs, truths, selections, strict=True)):
        X = sparse.csr_matrix(design["X"])
        e, si, xbar, M = design["e"], design["si"], design["xbar"], truth["raw"]
        require(S.shape == (X.shape[1], n) and M.shape == (X.shape[1], len(p))
                and e.shape == si.shape == (X.shape[0],)
                and xbar.shape == (len(design["strata"]), X.shape[1])
                and design["H"].shape == (X.shape[1], X.shape[1])
                and np.isfinite(S).all() and np.isfinite(M).all()
                and np.isfinite(e).all() and np.all(e > 0) and np.isfinite(xbar).all()
                and np.isfinite(design["H"]).all() and np.isfinite(X.data).all()
                and si.dtype.kind in "iu" and np.all((0 <= si) & (si < len(xbar)))
                and np.max(np.abs(M.sum(axis=1)), initial=0.) <= 1e-10,
                "known-law annual geometry or physical truth differs")
        H += S.T @ design["H"] @ S
        m += S.T @ design["H"] @ (alpha*M @ B)
        if law == "gaussian":
            continue
        Z = sparse.csr_matrix((np.ones(len(si)), (np.arange(len(si)), si)),
                              shape=(len(si), len(xbar)))
        # use the orthonormal gaussian baseline plus physical-mean perturbations.
        # at null these are exactly zero, so both laws have identical curves.
        diagonal = (r*e)[:, None] * (alpha * (X @ (M @ metrics)))
        for index, covariance in enumerate(covariances):
            covariance += S.T @ _residual_noise_gram(X, Z, xbar, diagonal[:, index]) @ S
        prediction_covariance += S.T @ _residual_noise_gram(X, Z, xbar, diagonal[:, -1]) @ S
        final = year == len(designs)-1
        if final:
            context_weights = np.asarray(Z.T @ diagonal[:, -1])
            cross = (X.T @ Z.multiply(diagonal[:, -1, None])).toarray() - xbar.T*context_weights
            f += S.T @ cross
        projected_means = (r*e)[:, None] * (alpha * (X @ (M @ B)))
        games, row_games = design["game_ids"], np.asarray(design["row_game_ids"])
        require(row_games.shape == e.shape and games == tuple(sorted(set(games)))
                and np.array_equal(np.unique(row_games), games),
                "known-law game inventory differs from complete directional rows")
        for game in games:
            rows = row_games == game
            context = np.asarray(Z[rows].T @ projected_means[rows])
            q = S.T @ (X[rows].T @ projected_means[rows] - xbar.T @ context)
            for D, covariance in zip(projected, covariances, strict=True):
                value = q @ D
                covariance += .5 * (value @ value.T)
            prediction_covariance += .5 * (q @ q.T)
            if final:
                f += .5 * (q @ context.T)
        if final:
            E = np.asarray(Z.T @ e)
            require(np.all(E > 0), "final training context has no exposure")
            f /= r*E
    for D, covariance in zip(projected, covariances, strict=True):
        covariance += float(np.sum(D**2))*H
        covariance *= copies
    prediction_covariance += d*H
    result = dict(H=copies*H, m=copies*m, covariances=tuple(covariances),
                  prediction_covariance=copies*prediction_covariance, context_cross_score=f)
    require(all(np.isfinite(value).all() for value in
                (result["H"], result["m"], prediction_covariance, f, *covariances)),
            "known-law score moments are nonfinite")
    return result
