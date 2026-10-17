"""the reused 04a synthetic lineup construction; no fitting or study decisions."""

from itertools import combinations

import numpy as np
from scipy import sparse

from .artifacts import require


def synthetic_counts(design: dict, case_id: int, outer_id: int, year_index: int) -> np.ndarray:
    """the original 04c response stream; callers supply its fixed design and ids."""
    require(type(case_id) is int and case_id in (0, 1) and type(outer_id) is int and outer_id >= 0,
            "invalid synthetic response identity")
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([40430, case_id, outer_id, year_index])))
    means = design["e"][:, None] * design["mu"]
    if case_id == 0:
        return rng.normal(means, np.sqrt(design["e"][:, None] * 40 * design["p"]))
    responses = np.empty_like(means)
    for game in range(96):
        pace = rng.gamma(shape=2, scale=.5)
        rows = slice(100 * game, 100 * (game + 1))
        responses[rows] = rng.poisson(pace * means[rows])
    return responses


def synthetic_designs() -> dict[str, list[dict]]:
    """the original 04a lineup stream; its mixed pass precedes the paired pass."""
    rng = np.random.Generator(np.random.PCG64(40400))
    designs = {}
    for case in ("mixed", "paired"):
        years = []
        for year in range(5):
            active = [list(range(team * 8, team * 8 + 8)) for team in range(4)]
            if year >= 2:
                active[0][0], active[1][0] = 32, 33
            if year >= 3:
                active[1][1] = 8
            players = tuple(sorted(player for team in active for player in team))
            positions = {player: i for i, player in enumerate(players)}
            n = len(players)
            offense, defense, seconds, contexts, home_teams, away_teams = [], [], [], [], [], []
            for repetition in range(16):
                for first, second in combinations(range(4), 2):
                    home, away = (first, second) if repetition % 2 == 0 else (second, first)
                    home_teams.append(home)
                    away_teams.append(away)
                    for stint in range(50):
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
                              game_ids=tuple(range(96)), row_game_ids=np.repeat(np.arange(96), 100),
                              u=exposure / exposure.sum()))
        designs[case] = years
    return designs
