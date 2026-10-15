"""manual 04a preparation, fitting, recovery and descriptive assessment."""

import argparse
from collections import Counter
from itertools import combinations
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy import sparse
from scipy.special import expit, logit
from scipy.stats import norm

from hockey_stats.artifacts import clean_implementation, implementation, linked_path, require, resources, rows, write_json
from hockey_stats.attribution import (
    AnnualPopulation, AnnualState, contrast_interval, fit_prepared_year, fit_year, negative_rate_summary, read_annual, validate_model_rules,
)
from hockey_stats.attribution_data import POPULATIONS, prepare_attribution
from hockey_stats.attribution_valuation import prepare_reference, read_reference, location_transport, transport_state
from hockey_stats.chance_evaluation import REGION_NAMES, compound_regions
from hockey_stats.shot_origins import grid
from hockey_stats.chance_cli import identity, output_path, read_json


SHARES = np.array([.1, .2, .3, .4])
SEASONS = tuple(f"{year}{year + 1}" for year in range(2021, 2026))


def synthetic_designs() -> dict[str, list[dict]]:
    """freeze two explicitly synthetic designs; count stress reuses mixed lineups."""
    rng = np.random.Generator(np.random.PCG64(40400))
    designs = {}
    for case in ("mixed", "paired"):
        years = []
        for year in range(5):
            active = [list(range(team*8, team*8+8)) for team in range(4)]
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
                                lineup = ([26, 31, *rng.choice(remainder, 3, replace=False)] if rng.random() < 5/8
                                          else rng.choice(remainder, 5, replace=False))
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
            X = sparse.csr_matrix((np.ones(indices.size), (np.repeat(np.arange(len(indices)), 10), indices.ravel())),
                                  shape=(len(indices), 2*n))
            offense_ticks = np.tile(np.array([-4, -2, 0, 0, 0, 0, 2, 4], dtype=np.int64), 4)
            defense_ticks = np.tile(np.array([2, 0, -2, 0, 4, 0, -4, 0], dtype=np.int64), 4)
            if year >= 3:
                offense_ticks[1] += 1
            offense_ticks = np.concatenate((offense_ticks, [2, 0]))
            defense_ticks = np.concatenate((defense_ticks, [0, 0]))
            scalar_ticks = np.concatenate((offense_ticks[list(players)], defense_ticks[list(players)]))
            spatial_ticks = scalar_ticks[:, None] * np.array([1, 2, 3, 4])
            truth_scalar = scalar_ticks / 40
            truth_spatial = truth_scalar[:, None] * SHARES
            for player in players:
                if player < 32 and player % 8 in (3, 4):
                    direction = 1 if player % 8 == 3 else -1
                    truth_spatial[positions[player]] += np.array([.025, -.025, 0, 0]) * direction
                    spatial_ticks[positions[player]] += np.array([10, -10, 0, 0]) * direction
            mu = np.column_stack((40 * (SHARES + X @ truth_spatial), 15 * (1 + X @ truth_scalar)))
            require(np.isfinite(mu).all() and np.all(mu > 0), "synthetic generating means must be positive without clipping")
            e = seconds / 3600
            se = np.bincount(si, weights=e, minlength=len(strata))
            xe = np.vstack([np.asarray(X[si == index].T @ e[si == index]).ravel() for index in range(len(strata))])
            xbar = xe / se[:, None]
            H_e = (X.T @ X.multiply(e[:, None])).toarray() - xe.T @ xbar
            years.append(dict(players=players, offense=offense, defense=defense, seconds=seconds,
                strata=strata, si=si, X=X, truth_scalar=truth_scalar, truth_spatial=truth_spatial,
                truth_blocked=truth_scalar.copy(), truth_scalar_ticks=scalar_ticks, truth_spatial_ticks=spatial_ticks, mu=mu, home_teams=np.asarray(home_teams), away_teams=np.asarray(away_teams),
                e=e, stratum_e=se, stratum_xe=xe, xbar=xbar, H_e=H_e,
                player_exposure=np.asarray(X[:, :n].T @ seconds).ravel()))
        designs[case] = years
    return designs


def synthetic_counts(design: dict, case: str, rng: np.random.Generator) -> np.ndarray:
    """draw in replicate/year/game/stint/team/cell order; blocked is column four."""
    means = design["e"][:, None] * design["mu"]
    if case in ("mixed", "paired"):
        variances = design["e"][:, None] * np.array([4, 8, 12, 16, 15])
        return rng.normal(means, np.sqrt(variances))
    require(case == "count_stress", "unknown synthetic case")
    counts = np.empty_like(means)
    for game in range(96):
        pace = rng.gamma(shape=2, scale=.5)
        counts[100*game:100*(game+1)] = rng.poisson(pace * means[100*game:100*(game+1)])
    return counts


def sufficient_population(design: dict, counts: np.ndarray, benchmark: str, season_index: int,
                          protocol_sha: str, population_id: str) -> AnnualPopulation:
    """synthetic matrix responses deliberately bypass factual integer-count schemas."""
    N = counts.sum(axis=1, keepdims=True) if benchmark == "all_attempts" else counts[:, :4]
    e, se, xe = design["e"], design["stratum_e"], design["stratum_xe"]
    rate = float(N.sum() / e.sum())
    require(rate > 0 and math.isfinite(rate), "synthetic realized reference rate must be positive")
    sn = np.vstack([N[design["si"] == index].sum(axis=0) for index in range(len(se))])
    T = np.asarray(design["X"].T @ N) - xe.T @ (sn / se[:, None])
    yy = float((np.sum(N.sum(axis=1)**2/e) - np.sum(sn.sum(axis=1)**2/se)) / rate)
    return AnnualPopulation(benchmark, SEASONS[season_index], season_index, protocol_sha, population_id,
        design["players"], rate*design["H_e"], T, yy, rate, design["xbar"], sn/(rate*se[:, None]),
        rate*se, design["player_exposure"], N.sum(axis=0))


def meaningful_status(lower: float, upper: float) -> str:
    if lower > .05:
        return "meaningful_positive"
    if upper < -.05:
        return "meaningful_negative"
    if lower >= -.05 and upper <= .05:
        return "within_meaningful_band"
    return "unresolved"


def scalar_contrast(state: AnnualState, player_contrast: np.ndarray) -> dict:
    """the study's meaningful band applies only to matched scalar recorded rates."""
    result = contrast_interval(state, player_contrast, np.ones(state.M.shape[1]))
    result.update(relative_mean=result["mean"] / state.r, relative_lower=result["lower"] / state.r,
                  relative_upper=result["upper"] / state.r)
    result["status"] = meaningful_status(result["relative_lower"], result["relative_upper"])
    return result


def wilson(successes: int, total: int) -> list[float] | None:
    if total == 0:
        return None
    z = float(norm.ppf(.975))
    proportion = successes / total
    denominator = 1 + z*z/total
    center = (proportion + z*z/(2*total)) / denominator
    half = z*math.sqrt(proportion*(1-proportion)/total + z*z/(4*total*total)) / denominator
    return [center-half, center+half]


def recovery_contrasts() -> list[dict]:
    """fixed named contrasts; unavailable retired players retain null results."""
    result = []
    for player in range(34):
        for role in ("offense", "defense"):
            result.append(dict(name=f"player_{player}_{role}", role=role, coefficients=[(player, 1)],
                               group="entrant" if player in (32, 33) else "returner" if player == 8 else "original"))
    for role, pairs in (("offense", ((2, 3), (6, 2), (7, 2))), ("defense", ((1, 3), (0, 1), (4, 1)))):
        for left, right in pairs:
            result.append(dict(name=f"{role}_{left}_minus_{right}", role=role,
                               coefficients=[(left, 1), (right, -1)], group="fixed_pair"))
    result.extend((dict(name="offense_3_minus_4", role="offense", coefficients=[(3, 1), (4, -1)], group="zero_sum_spatial"),
                   dict(name="offense_26_plus_31", role="offense", coefficients=[(26, 1), (31, 1)], group="paired_sum"),
                   dict(name="offense_26_minus_31", role="offense", coefficients=[(26, 1), (31, -1)], group="paired_difference")))
    return result


def simulate(protocol: Path | str, out: Path | str) -> dict:
    """execute the frozen recovery study; retain scientific failures as results."""
    started = time.monotonic()
    protocol_path = Path(protocol).resolve(strict=True)
    frozen = read_json(protocol_path)
    protocol_reference = identity(protocol_path)
    require(type(frozen["schema_version"]) is int and frozen["schema_version"] == 1 and frozen["kind"] == "attribution_protocol", "invalid simulation protocol")
    validate_model_rules(frozen)
    current_implementation = implementation()
    if frozen["purpose"] == "research":
        clean_implementation(current_implementation)
        require(current_implementation == frozen["implementation"], "simulation implementation differs from frozen protocol")
    generator = frozen["generator"]
    expected = dict(cases=["mixed", "paired", "count_stress"], years=5, bit_generator="PCG64", design_seed=40400,
        response_seed_base=40401, draw_order=["replicate", "year", "game", "stint", "team", "cell"],
        teams=4, active_skaters_per_team=8, games_per_year=96, stints_per_game=50,
        durations_seconds=[15, 30, 45], home_assignment="balanced", schedule="balanced_round_robin",
        score_difference=0, periods="cycling_regulation", cell_shares=[.1, .2, .3, .4],
        unblocked_rate_per60=40, blocked_rate_per60=15,
        offense_truth=[-.10, -.05, 0, 0, 0, 0, .05, .10], defense_truth=[.05, 0, -.05, 0, .10, 0, -.10, 0],
        zero_sum_offense=dict(offset_3=[.025, -.025, 0, 0], offset_4=[-.025, .025, 0, 0]),
        year3_replacements=[[0, 32], [8, 33]], year4_replacements=[[9, 8]],
        entrant_offense={"32": .05, "33": 0}, entrant_defense=0,
        player1_offense_change=dict(from_year=4, amount=.025), paired_players=[26, 31],
        paired_inclusion_probability=.625, count_stress_game_pace=dict(distribution="gamma", shape=2, scale=.5),
        offense_pairs=[[2, 3], [6, 2], [7, 2]], defense_pairs=[[1, 3], [0, 1], [4, 1]],
        spatial_pair=[3, 4], coverage_unit="replicate", scale_selection="every_replicate_year_chain",
        gaussian_count_variances=["e*40*share_j", "e*15"], cell_draw_order=[0, 1, 2, 3, "blocked"],
        count_stress_pace_draw="one draw immediately before each game counts, shared by both teams and all stints",
        lineup_draw_order=["year", "game", "stint", "team"],
        design_reuse="fixed across replicates; mixed and count_stress share lineups", design_case_order=["mixed", "paired"],
        matchup_order="lexicographic team pairs, 16 repetitions; alternate home assignment each repetition",
        team_draw_order=["away", "home"], duration_cycle="restart 15,30,45 at stint zero in each game",
        period_cycle="1,2,3 by stint index, restarting each game")
    require(all(generator.get(key) == value for key, value in expected.items()), "frozen synthetic generator differs from implementation")
    replicates = generator["replicates_per_case"]
    require(type(replicates) is int and (replicates == 200 if frozen["purpose"] == "research" else 1 <= replicates <= 200),
            "research simulation requires exactly 200 replicates per case")
    output = output_path(str(out), [str(protocol_path.parent)])
    require(output.is_relative_to(Path(frozen["output_root"]).resolve()), "simulation output differs from frozen root")
    if frozen["purpose"] == "research":
        require(output.is_relative_to(Path("/Volumes/Expansion/hockey-stats")), "research simulation must remain external")
    output.mkdir()
    designs = synthetic_designs()
    arrays = {f"{case}_{year}_{name}": design[name]
              for case, years in designs.items() for year, design in enumerate(years)
              for name in ("offense", "defense", "seconds", "si", "home_teams", "away_teams", "mu",
                           "truth_scalar", "truth_spatial", "truth_blocked", "truth_scalar_ticks", "truth_spatial_ticks")}
    array_path = output / "synthetic-design.npz"
    with array_path.open("xb") as destination:
        np.savez(destination, **arrays)
    design_manifest = dict(schema_version=1, kind="attribution_synthetic_design", implementation=current_implementation,
        protocol=protocol_reference, arrays=identity(array_path), shapes={key: list(value.shape) for key, value in arrays.items()},
        years={case: [dict(season=SEASONS[year], players=design["players"], strata=design["strata"],
                          minimum_generating_rate=float(design["mu"].min())) for year, design in enumerate(years)]
               for case, years in designs.items()},
        count_stress_design="mixed", row_order="game/stint/away then home/cell; blocked is response column four",
        units=dict(seconds="synthetic seconds", mu="attempts per 60", truth="relative generating baseline rate",
                   truth_scalar_ticks="1/40 of generating baseline rate", truth_spatial_ticks="1/400 of generating baseline rate"),
        source_meaning="explicitly synthetic lineups, cells and gaussian/count responses; no source captures")
    write_json(output / "synthetic-design.json", design_manifest)
    summaries = {}
    checks = recovery_contrasts()
    diagnostic_path = output / "annual-diagnostics.jsonl"
    scale_counts = Counter()
    with diagnostic_path.open("x") as diagnostic_file:
        for case_index, case in enumerate(("mixed", "paired", "count_stress")):
            rng = np.random.Generator(np.random.PCG64(40401 + case_index))
            years = designs["paired" if case == "paired" else "mixed"]
            for replicate in range(replicates):
                previous = {benchmark: None for benchmark in ("all_attempts", "unblocked_spatial")}
                for year, design in enumerate(years):
                    counts = synthetic_counts(design, case, rng)
                    for benchmark in ("all_attempts", "unblocked_spatial"):
                        population = sufficient_population(design, counts, benchmark, year,
                            protocol_reference["sha256"], f"synthetic:{case}:{benchmark}")
                        state = fit_year(population, previous[benchmark])
                        previous[benchmark] = state
                        k, n = state.M.shape[1], len(state.player_ids)
                        positions = {player: i for i, player in enumerate(state.player_ids)}
                        current = [positions[player] for player in design["players"]]
                        selected = np.asarray(current + [n + i for i in current])
                        rates = state.r * (design["X"] @ state.M[selected] + state.A[design["si"]])
                        negatives = negative_rate_summary([(rates, design["seconds"])])
                        scale_counts[(case, benchmark, state.scale["status"])] += 1
                        diagnostic = dict(case=case, replicate=replicate, year=year+1, benchmark=benchmark,
                            r=state.r, a=state.a, q=state.q, scale=state.scale, diagnostics=state.diagnostics,
                            negative_rates=negatives, response_minimum=float(counts.min()))
                        diagnostic_file.write(json.dumps(diagnostic, allow_nan=False, separators=(",", ":")) + "\n")
                        current_positions = {player: i for i, player in enumerate(design["players"])}
                        exposure_seconds = design["player_exposure"].astype(np.int64)
                        require(np.array_equal(exposure_seconds, design["player_exposure"]), "synthetic exposure must be integer seconds")
                        total_player_seconds = int(exposure_seconds.sum())
                        responses = [("scalar", np.ones(k))]
                        if k > 1:
                            responses.extend((f"cell_{cell}", np.eye(k)[cell]) for cell in range(k))
                        truth_functionals = {}
                        for response_name, _ in responses:
                            baseline, denominator, ticks = ((55 if k == 1 else 40, 40, design["truth_scalar_ticks"])
                                if response_name == "scalar" else
                                (40, 400, design["truth_spatial_ticks"][:, int(response_name.removeprefix("cell_"))]))
                            role_totals = [sum(int(seconds) * int(ticks[offset+i]) for i, seconds in enumerate(exposure_seconds))
                                           for offset in (0, len(design["players"]))]
                            truth_functionals[response_name] = (baseline, denominator, ticks, role_totals)
                        for check in checks:
                            available = all(player in design["players"] for player, _ in check["coefficients"])
                            c = np.zeros(2*n)
                            if available:
                                for player, coefficient in check["coefficients"]:
                                    c[positions[player] + (n if check["role"] == "defense" else 0)] = coefficient
                            for response_name, response in responses:
                                key = (case, benchmark, year+1, check["name"], response_name)
                                if key not in summaries:
                                    summaries[key] = dict(case=case, benchmark=benchmark, year=year+1,
                                        contrast=check, response=response_name, n=0, unavailable=0,
                                        error_sum=0.0, squared_error_sum=0.0, relative_error_sum=0.0,
                                        relative_squared_error_sum=0.0, width_sum=0.0, relative_width_sum=0.0,
                                        coverage=0, false_directional=0, false_meaningful=0, false_within_band=0,
                                        statuses=Counter(), truth_minimum=math.inf, truth_maximum=-math.inf,
                                        variance_minimum=math.inf, variance_maximum=-math.inf,
                                        rounded_variances=0, maximum_rounding_tolerance=0.0)
                                summary = summaries[key]
                                if not available:
                                    summary["unavailable"] += 1
                                    continue
                                interval = scalar_contrast(state, c) if response_name == "scalar" else contrast_interval(state, c, response)
                                mean, variance = interval["mean"], interval["variance"]
                                lower, upper = interval["lower"], interval["upper"]
                                half = (upper - lower)/2
                                baseline, denominator, ticks, role_totals = truth_functionals[response_name]
                                role_index = 1 if check["role"] == "defense" else 0
                                role_offset = role_index * len(design["players"])
                                coefficient_sum = sum(coefficient for _, coefficient in check["coefficients"])
                                numerator = sum(coefficient * int(ticks[current_positions[player]+role_offset])
                                                for player, coefficient in check["coefficients"]) * total_player_seconds
                                numerator -= coefficient_sum * role_totals[role_index]
                                actual = baseline * numerator / (denominator * total_player_seconds)
                                summary["variance_minimum"] = min(summary["variance_minimum"], variance)
                                summary["variance_maximum"] = max(summary["variance_maximum"], variance)
                                summary["rounded_variances"] += interval["variance_rounded_to_zero"]
                                summary["maximum_rounding_tolerance"] = max(summary["maximum_rounding_tolerance"],
                                                                             interval["variance_rounding_tolerance"])
                                error = mean-actual
                                summary["n"] += 1
                                summary["error_sum"] += error
                                summary["squared_error_sum"] += error*error
                                summary["relative_error_sum"] += error/state.r
                                summary["relative_squared_error_sum"] += (error/state.r)**2
                                summary["width_sum"] += 2*half
                                summary["relative_width_sum"] += 2*half/state.r
                                summary["coverage"] += lower <= actual <= upper
                                summary["false_directional"] += (lower > 0 and actual <= 0) or (upper < 0 and actual >= 0)
                                summary["truth_minimum"] = min(summary["truth_minimum"], actual)
                                summary["truth_maximum"] = max(summary["truth_maximum"], actual)
                                if response_name == "scalar":
                                    status = interval["status"]
                                    summary["statuses"][status] += 1
                                    summary["false_meaningful"] += (status == "meaningful_positive" and actual/state.r <= .05
                                        or status == "meaningful_negative" and actual/state.r >= -.05)
                                    summary["false_within_band"] += status == "within_meaningful_band" and abs(actual/state.r) > .05
    recovery_path = output / "recovery.jsonl"
    with recovery_path.open("x") as destination:
        for key, summary in sorted(summaries.items()):
            n = summary["n"]
            record = {key: summary[key] for key in ("case", "benchmark", "year", "contrast", "response", "n", "unavailable")}
            record.update(reason=None if n else "contrast includes a player not currently observed",
                bias=summary["error_sum"]/n if n else None, rmse=math.sqrt(summary["squared_error_sum"]/n) if n else None,
                relative_bias=summary["relative_error_sum"]/n if n else None,
                relative_rmse=math.sqrt(summary["relative_squared_error_sum"]/n) if n else None,
                mean_width=summary["width_sum"]/n if n else None,
                mean_relative_width=summary["relative_width_sum"]/n if n else None,
                truth_range=[summary["truth_minimum"], summary["truth_maximum"]] if n else None,
                raw_variance_range=[summary["variance_minimum"], summary["variance_maximum"]] if n else None,
                variance_rounded_to_zero_count=int(summary["rounded_variances"]),
                maximum_variance_rounding_tolerance=summary["maximum_rounding_tolerance"],
                statuses=dict(summary["statuses"]) if summary["response"] == "scalar" else None)
            for metric in ("coverage", "false_directional", "false_meaningful", "false_within_band"):
                applicable = metric not in ("false_meaningful", "false_within_band") or summary["response"] == "scalar"
                record[metric] = dict(count=int(summary[metric]), n=n, rate=summary[metric]/n if n else None,
                                      wilson_95=wilson(summary[metric], n)) if applicable else None
            destination.write(json.dumps(record, allow_nan=False, separators=(",", ":")) + "\n")
    result = dict(schema_version=1, kind="attribution_simulation", purpose=frozen["purpose"],
        implementation=current_implementation, protocol=protocol_reference,
        design=identity(output / "synthetic-design.json"), recovery=identity(recovery_path),
        annual_diagnostics=identity(diagnostic_path), replicates_per_case=replicates, years=5,
        annual_fits=3*replicates*5*2, scale_statuses=[dict(case=case, benchmark=benchmark, status=status, count=count)
            for (case, benchmark, status), count in sorted(scale_counts.items())],
        units=dict(effects="attempts per 60", relative_effects="share of realized league team rate"),
        interval_meaning="pointwise gaussian working posterior conditional on references, response shape and fitted scales",
        coverage_unit="one replicate per named contrast/year; no pooling of correlated players or years",
        row_contracts=dict(recovery="case/benchmark/year/contrast/response; each binomial n counts independent replicates",
                           annual_diagnostics="case/replicate/year/benchmark; fitted scale curve, numerical and signed-rate diagnostics"),
        source_meaning="explicitly synthetic matrices; gaussian count-unit responses may be signed and noninteger",
        admission="not_admitted", resources=resources(started))
    write_json(output / "simulation.json", result)
    return identity(output / "simulation.json")


def _coverage_tables(prepared: dict, output: Path) -> tuple[list, dict, dict]:
    """aggregate known losses without assigning unknown game time to players."""
    teams, players = {}, {}
    for game in rows(linked_path(prepared["ledgers"]["coverage"])):
        if game["populations"] is None:
            continue
        for team in game["teams"]:
            key = (team["population"], game["season"], team["team_id"])
            record = teams.setdefault(key, dict(benchmark=key[0], season=key[1], team_id=key[2],
                measured_games=0, score_unavailable_games=0, unknown_horizon_games=0,
                retained_seconds=0, excluded_seconds=0, unresolved_membership_seconds=0,
                retained_attempts=0, excluded_attempts=0))
            record["measured_games"] += 1
            record["score_unavailable_games"] += bool(game["score_failures"])
            record["unknown_horizon_games"] += bool(team["unknown_horizon_periods"])
            for name in ("retained_seconds", "excluded_seconds", "unresolved_membership_seconds",
                         "retained_attempts", "excluded_attempts"):
                record[name] += team[name]
        for player in game["players"]:
            key = (player["population"], game["season"], player["player_id"])
            record = players.setdefault(key, dict(benchmark=key[0], season=key[1], player_id=key[2], teams=set(),
                measured_games=0, score_unavailable_games=0, unknown_horizon_games=0, native_incomplete_games=0,
                native_exposure_unavailable_games=0, unknown_membership_games=0, retained_seconds=0, excluded_seconds=0,
                unresolved_membership_known_seconds=0, unassignable_team_membership_seconds=0,
                unknown_event_membership_attempts=0, for_retained=0, against_retained=0,
                for_excluded=0, against_excluded=0))
            record["teams"].add(player["team_id"])
            record["measured_games"] += 1
            record["score_unavailable_games"] += bool(game["score_failures"])
            record["unknown_horizon_games"] += bool(game["unknown_horizon_periods"])
            native = player["native_exposure"]
            record["native_exposure_unavailable_games"] += native is None
            record["native_incomplete_games"] += native is not None and not native["complete"]
            record["unknown_membership_games"] += player["unresolved_membership_seconds"] is None
            record["unassignable_team_membership_seconds"] += player["unknown_membership_seconds"]
            for name in ("retained_seconds", "excluded_seconds", "unresolved_membership_known_seconds",
                         "unknown_event_membership_attempts", "for_retained", "against_retained",
                         "for_excluded", "against_excluded"):
                record[name] += player[name]
    for record in players.values():
        record["teams"] = sorted(record["teams"])
        record["unresolved_membership_seconds"] = (None if record["unknown_membership_games"]
                                                   else record["unresolved_membership_known_seconds"])
    references = {}
    for name, records in (("coverage_teams", teams), ("coverage_players", players)):
        path = output / (name.replace("_", "-") + ".jsonl")
        with path.open("x") as destination:
            for key in sorted(records):
                destination.write(json.dumps(records[key], allow_nan=False, separators=(",", ":")) + "\n")
        references[name] = identity(path)
    seasons = []
    for annual in prepared["annual"]:
        scalar = next(row for row in prepared["annual"] if row["population"] == "all_attempts"
                      and row["season"] == annual["season"])
        spatial = next(row for row in prepared["annual"] if row["population"] == "unblocked_spatial"
                       and row["season"] == annual["season"])
        scalar_seconds, spatial_seconds = scalar["coverage"].get("retained_seconds", 0), spatial["coverage"].get("retained_seconds", 0)
        seasons.append(dict(benchmark=annual["population"], season=annual["season"],
            population_status=annual["status"], population_reason=annual["reason"], **annual["coverage"],
            common_spatial_fraction_of_scalar_seconds=spatial_seconds/scalar_seconds if scalar_seconds else None,
            common_spatial_fraction_reason=None if scalar_seconds else "no_scalar_exposure",
            scalar_attempts_on_spatial_exposure=spatial["coverage"].get("common_population_all_attempts", 0)))
    return seasons, references, players


def _assessed_contrast(state: AnnualState, c: np.ndarray, surfaces: dict | None,
                       transported: dict, regions: dict) -> dict:
    """one study contrast, with scalar policy and separate projection stresses."""
    result = dict(scalar=scalar_contrast(state, c), regions=None, valuation=None, scenarios=None)
    if state.benchmark == "all_attempts":
        return result
    result["regions"] = {name: contrast_interval(state, c, weights) for name, weights in regions.items()}
    if surfaces is not None:
        vectors = dict(surfaces, direct_minus_product=surfaces["direct"]-surfaces["product"])
        result["valuation"] = {name: contrast_interval(state, c, weights) for name, weights in vectors.items()}
    selected = np.flatnonzero(c)
    base_map = state.r * c[selected] @ state.M[selected]
    scenarios = {}
    for direction, moved in transported.items():
        moved_map = moved.r * c[selected] @ moved.M[selected]
        change = dict(scalar_delta=scalar_contrast(moved, c)["mean"]-result["scalar"]["mean"],
            map_l1_delta=float(np.abs(moved_map-base_map).sum()),
            map_max_abs_delta=float(np.abs(moved_map-base_map).max()),
            regions={}, valuation=None)
        for name, weights in regions.items():
            interval = contrast_interval(moved, c, weights)
            interval["mean_delta"] = interval["mean"]-result["regions"][name]["mean"]
            change["regions"][name] = interval
        if surfaces is not None:
            change["valuation"] = {}
            for name, weights in vectors.items():
                interval = contrast_interval(moved, c, weights)
                interval.update(mean_delta=interval["mean"]-result["valuation"][name]["mean"],
                    sign_changed=np.sign(interval["mean"]) != np.sign(result["valuation"][name]["mean"]))
                interval["sign_changed"] = bool(interval["sign_changed"])
                change["valuation"][name] = interval
        scenarios["location_"+direction] = change
    for shift, name in ((-.10, "logodds_minus_0.10"), (.10, "logodds_plus_0.10")):
        values = None
        if surfaces is not None:
            shifted = {key: expit(logit(value)+shift) for key, value in surfaces.items()}
            shifted["direct_minus_product"] = shifted["direct"]-shifted["product"]
            values = {}
            for key, weights in shifted.items():
                interval = contrast_interval(state, c, weights)
                interval.update(mean_delta=interval["mean"]-result["valuation"][key]["mean"],
                    sign_changed=bool(np.sign(interval["mean"]) != np.sign(result["valuation"][key]["mean"])))
                values[key] = interval
        scenarios[name] = dict(logodds_change=shift, valuation=values)
    result["scenarios"] = scenarios
    return result


def _assessment_figures(output: Path, prepared: dict, player_rows: list, pair_rows: list,
                        selected_maps: list, reference: dict) -> dict:
    """three static scientific figures, using only the frozen exposure-selected ids."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection

    selected = sorted({player for name in ("greatest_shared", "greatest_disjoint")
                       for player in (prepared["pairs"][name] or [])})
    figures = {}
    target = prepared["target_season"][:4] + "–" + prepared["target_season"][6:]
    figure, axes = plt.subplots(2, 2, figsize=(13, 9), layout="constrained")
    for i, benchmark in enumerate(POPULATIONS):
        for j, role in enumerate(("offense", "suppression")):
            axis = axes[i, j]
            candidates = []
            for player in selected:
                matches = [row for row in player_rows if row["benchmark"] == benchmark and row["role"] == role
                           and row["player_id"] == player]
                candidates.append(matches[0] if matches else dict(player_id=player, exposure_seconds=0,
                    status="unavailable", reason="player_not_currently_observed", scalar=None))
            candidates += [row for row in pair_rows if row["benchmark"] == benchmark and row["role"] == role]
            labels = []
            for index, row in enumerate(candidates):
                label = (f"{row['player_id']}  ({row['exposure_seconds']/3600:.1f} h)" if "player_id" in row
                         else (row["pair"].replace("greatest_", "") + f": {row['players'][0]} - {row['players'][1]}" if row["players"] is not None else "unavailable pair"))
                labels.append(label)
                if row["status"] == "available":
                    value = row["scalar"]
                    axis.errorbar(value["relative_mean"], index,
                        xerr=[[value["relative_mean"]-value["relative_lower"]],
                              [value["relative_upper"]-value["relative_mean"]]],
                        fmt="o", color="#1d5367", capsize=3, markersize=4)
                else:
                    axis.text(0, index, "unavailable", va="center", fontsize=8)
            axis.axvspan(-.05, .05, color="#dfe8e8", zorder=-1)
            axis.axvline(0, color="0.5", linewidth=.7)
            axis.set(yticks=range(len(labels)), yticklabels=labels,
                     title=benchmark.replace("_", " ") + " / " + role,
                     xlabel="effect / relevant league team rate; meaningful band ±0.05")
            axis.invert_yaxis()
            axis.grid(axis="x", alpha=.15)
            rate = next(row["r"] for row in prepared["annual"] if row["population"] == benchmark
                        and row["season"] == prepared["target_season"])
            if rate is not None:
                secondary = axis.secondary_xaxis("top", functions=(lambda x, r=rate: x*r, lambda x, r=rate: x/r))
                secondary.set_xlabel("attempts/60 effect")
    figure.suptitle(f"{target} 5v5: exposure-selected recorded-rate associations\npointwise 95% working intervals; not ability or causal effects")
    path = output / "scalar-contrasts.png"
    figure.savefig(path, dpi=180, bbox_inches="tight", pad_inches=.15)
    plt.close(figure)
    figures["scalar_contrasts"] = identity(path)

    figure, axes = plt.subplots(max(len(selected), 1), 2, figsize=(12, max(len(selected), 1)*2.8+1),
                                squeeze=False, layout="constrained")
    centers, _ = grid()
    corners = np.array([[-2.5, -2.5], [2.5, -2.5], [2.5, 2.5], [-2.5, 2.5]])
    polygons = centers[:, None, :] + corners
    magnitude = max((float(np.abs(row["map"]).max()) for row in selected_maps), default=0) or 1
    collection = None
    for i, player in enumerate(selected or [None]):
        for j, role in enumerate(("offense", "suppression")):
            axis = axes[i, j]
            matches = [row for row in selected_maps if row["player_id"] == player and row["role"] == role]
            if matches:
                row = matches[0]
                collection = PolyCollection(polygons, array=row["map"], cmap="RdBu_r", clim=(-magnitude, magnitude), linewidth=0)
                axis.add_collection(collection)
                scalar = row["scalar"]
                axis.set_title(f"{player} / {role}; sum {scalar['mean']:.2f} [{scalar['lower']:.2f}, {scalar['upper']:.2f}] attempts/60", fontsize=9)
            else:
                axis.text(0, 0, f"{player}: unavailable", ha="center")
            axis.plot([89], [0], marker="+", color="black", markersize=5)
            axis.set(xlim=(-100, 100), ylim=(-42.5, 42.5), xlabel="attacking x (feet)", ylabel="y (feet)", aspect="equal")
    if collection is not None:
        figure.colorbar(collection, ax=axes.ravel().tolist(), label="centered effect: attempts/60 in each native cell", shrink=.8)
    figure.suptitle(f"{target} 5v5: recorded unblocked associations on coordinate-complete exposure\ncommon axes/scales; not observed shot density; conditional scalar intervals")
    path = output / "maps.png"
    figure.savefig(path, dpi=180, bbox_inches="tight", pad_inches=.15)
    plt.close(figure)
    figures["maps"] = identity(path)

    figure, axes = plt.subplots(1, 2, figsize=(11, 5.8), layout="constrained")
    for axis, role in zip(axes, ("offense", "suppression"), strict=True):
        candidates = [row for row in player_rows if row["benchmark"] == "unblocked_spatial"
                      and row["role"] == role and row["status"] == "available" and row["valuation"] is not None]
        if candidates:
            direct = np.array([row["valuation"]["direct"]["mean"] for row in candidates])
            product = np.array([row["valuation"]["product"]["mean"] for row in candidates])
            axis.scatter(direct, product, s=13, alpha=.55, color="#1d5367")
            low, high = min(float(direct.min()), float(product.min()), 0), max(float(direct.max()), float(product.max()), 0)
            margin = (high-low)*.06 or .01
            axis.plot([low-margin, high+margin], [low-margin, high+margin], color="0.4", linewidth=1)
            axis.set(xlim=(low-margin, high+margin), ylim=(low-margin, high+margin))
        else:
            axis.text(.5, .5, "valuation unavailable: " + str(reference["reason"]), transform=axis.transAxes, ha="center", wrap=True)
        axis.set(title=role, xlabel="direct: provisional goals/60 effect", ylabel="product: provisional goals/60 effect", aspect="equal")
        axis.grid(alpha=.15)
    figure.suptitle(f"{target} 5v5: same maps, two unadmitted provisional valuations\nall current spatial players; equality line; disagreement is not error against truth")
    path = output / "valuation.png"
    figure.savefig(path, dpi=180, bbox_inches="tight", pad_inches=.15)
    plt.close(figure)
    figures["valuation"] = identity(path)
    return figures


def assess(prepared: Path | str, chains: Path | str, simulation: Path | str, out: Path | str) -> dict:
    """project completed evidence; no fitting and no automatic scientific verdict."""
    started = time.monotonic()
    prepared_path, chains_path, simulation_path = (Path(value).resolve(strict=True) for value in (prepared, chains, simulation))
    document, chain_document, simulation_document = map(read_json, (prepared_path, chains_path, simulation_path))
    require(type(document["schema_version"]) is int and document["schema_version"] == 1
            and document["kind"] == "attribution_prepared", "assessment requires prepared attribution evidence")
    prepared_reference = identity(prepared_path)
    protocol = read_json(linked_path(document["protocol"]))
    validate_model_rules(protocol)
    require(type(chain_document["schema_version"]) is int and chain_document["schema_version"] == 1
            and chain_document["kind"] == "attribution_chains" and chain_document["purpose"] == document["purpose"]
            and chain_document["protocol"] == document["protocol"] and chain_document["prepared"] == prepared_reference,
            "assessment chain identity differs from preparation")
    require(type(simulation_document["schema_version"]) is int and simulation_document["schema_version"] == 1
            and simulation_document["kind"] == "attribution_simulation"
            and simulation_document["purpose"] == document["purpose"] and simulation_document["protocol"] == document["protocol"],
            "assessment simulation identity differs from preparation")
    expected = dict(location_feet=5, goal_coordinate=[89, 0], directions=["toward", "away"],
        nearest_center="first_argmin_native_order", transport="A[dest,source]", keep_valuation_fixed=True,
        probability_logodds_changes=[-.10, .10], valuation_comparison=["direct", "product"], crossed_scenarios=False,
        meaningful_relative_difference=.05, interval="pointwise_95_percent_gaussian_working_posterior",
        reference="equal_weight_common_final_season_spatial_and_native_core_eligible_events_all_three_actors",
        exposure_summary=dict(quantiles=[.25, .5, .75], method="linear", population="all_current_observed_players",
                              selection="exposure_only; no minutes exclusion"))
    require(all(protocol["scenarios"].get(key) == value for key, value in expected.items()),
            "frozen assessment scenarios differ from implementation")
    current_implementation = implementation()
    if document["purpose"] == "research":
        clean_implementation(current_implementation)
        require(current_implementation == protocol["implementation"]
                and simulation_document["implementation"] == protocol["implementation"]
                and document["implementation"] == protocol["implementation"],
                "assessment/source implementation differs from frozen protocol")
    ordered = [(population, season) for population in POPULATIONS for season in document["seasons"]]
    require([(row["benchmark"], row["season"]) for row in chain_document["annual"]] == ordered,
            "assessment requires every population/season in chronological chain order")
    annual_statuses, final_states = [], {}
    for population in POPULATIONS:
        previous, unavailable = None, False
        for season in document["seasons"]:
            entry = next(row for row in chain_document["annual"] if row["benchmark"] == population and row["season"] == season)
            annual = next(row for row in document["annual"] if row["population"] == population and row["season"] == season)
            reason = "population_unavailable" if annual["status"] == "unavailable" else "preceding_population_unavailable" if unavailable else None
            require(entry["reason"] == reason and (entry["reference"] is None) == (reason is not None),
                    "chain missingness is not explained by scientifically unavailable preparation")
            status = dict(benchmark=population, season=season, reference=entry["reference"], reason=reason,
                          population_status=annual["status"], fit_status="unavailable" if reason else "completed")
            if reason is not None:
                unavailable = True
            else:
                path = linked_path(entry["reference"])
                fitted = read_json(path)
                require(fitted["prepared"] == prepared_reference and fitted["previous"] == previous
                        and fitted["benchmark"] == population and fitted["season"] == season
                        and fitted["purpose"] == document["purpose"]
                        and (document["purpose"] != "research" or fitted["implementation"] == protocol["implementation"]),
                        "completed annual artifact differs from the declared chain")
                state = read_annual(path)
                status.update(current_players=len(state.current_player_ids), carried_players=len(state.carried_only_ids),
                    entrants=len(state.entrant_ids), r=state.r, a=state.a, q=state.q,
                    scale_status=state.scale["status"], diagnostics=state.diagnostics)
                previous = entry["reference"]
                if season == document["target_season"]:
                    final_states[population] = state
            annual_statuses.append(status)
    recovery_path = linked_path(simulation_document["recovery"])
    linked_path(simulation_document["annual_diagnostics"])
    linked_path(simulation_document["design"])
    output = output_path(str(out), [str(path.parent) for path in (prepared_path, chains_path, simulation_path)])
    require(output.is_relative_to(Path(protocol["output_root"]).resolve()), "assessment differs from frozen output root")
    if document["purpose"] == "research":
        require(output.is_relative_to(Path("/Volumes/Expansion/hockey-stats")), "research assessment must remain external")
    output.mkdir()
    reference = prepare_reference(prepared_path, output / "reference")
    reference_document, surfaces = read_reference(reference["path"])
    coverage, tables, player_coverage = _coverage_tables(document, output)
    transports, transport_details = {}, {}
    spatial = final_states.get("unblocked_spatial")
    spatial_population = next(row for row in document["annual"] if row["population"] == "unblocked_spatial"
                              and row["season"] == document["target_season"])
    density = None
    if surfaces is not None:
        with np.load(linked_path(spatial_population["arrays"]), allow_pickle=False) as arrays:
            counts = arrays["response_counts"]
        density = spatial_population["r"] * counts / counts.sum()
    scenario_baselines = dict(base=dict(values=reference_document["league_baselines"], reason=reference_document["reason"]))
    for direction in ("toward", "away"):
        matrix, details = location_transport(direction)
        transport_details[direction] = details
        if spatial is not None:
            transports[direction] = transport_state(spatial, matrix)
        values = {name: float((matrix @ density) @ surface) for name, surface in surfaces.items()} if surfaces is not None else None
        scenario_baselines["location_"+direction] = dict(values=values, reason=reference_document["reason"])
    for shift, name in ((-.10, "logodds_minus_0.10"), (.10, "logodds_plus_0.10")):
        values = {key: float(density @ expit(logit(surface)+shift)) for key, surface in surfaces.items()} if surfaces is not None else None
        scenario_baselines[name] = dict(values=values, reason=reference_document["reason"])
    cell_regions = compound_regions(grid()[0])
    regions = {name: (cell_regions == index).astype(float) for index, name in enumerate(REGION_NAMES)}
    player_rows, pair_rows, selected_maps = [], [], []
    selected = {player for name in ("greatest_shared", "greatest_disjoint") for player in (document["pairs"][name] or [])}
    for population in POPULATIONS:
        annual = next(row for row in document["annual"] if row["population"] == population and row["season"] == document["target_season"])
        state = final_states.get(population)
        positions = {player: index for index, player in enumerate(state.player_ids)} if state is not None else {}
        for player in annual["players"]:
            observed = player_coverage[(population, annual["season"], player)]
            for role, sign in (("offense", 1), ("suppression", -1)):
                row = dict(benchmark=population, season=annual["season"], player_id=player, role=role,
                    exposure_seconds=observed["retained_seconds"],
                    observed_counts=dict(for_=observed["for_retained"], against=observed["against_retained"]),
                    status="available" if state is not None else "unavailable",
                    reason=None if state is not None else "annual_chain_unavailable", scalar=None, regions=None,
                    valuation=None, valuation_reason=reference_document["reason"] if population == "unblocked_spatial" else "not_spatial",
                    scenarios=None)
                if state is not None:
                    c = np.zeros(len(state.M))
                    c[positions[player] + (0 if role == "offense" else len(positions))] = sign
                    row.update(_assessed_contrast(state, c, surfaces, transports, regions))
                    if population == "unblocked_spatial" and player in selected:
                        index = positions[player] + (0 if role == "offense" else len(positions))
                        selected_maps.append(dict(player_id=player, role=role, map=sign*state.r*state.M[index], scalar=row["scalar"]))
                player_rows.append(row)
        for name in ("greatest_shared", "greatest_disjoint"):
            pair = document["pairs"][name]
            reason = ("pair_unavailable" if pair is None else "annual_chain_unavailable" if state is None
                      else "pair_player_not_currently_observed" if not set(pair) <= set(state.current_player_ids) else None)
            for role, sign in (("offense", 1), ("suppression", -1)):
                row = dict(benchmark=population, season=annual["season"], pair=name, players=pair, role=role,
                    status="available" if reason is None else "unavailable", reason=reason,
                    scalar=None, regions=None, valuation=None,
                    valuation_reason=reference_document["reason"] if population == "unblocked_spatial" else "not_spatial", scenarios=None)
                if reason is None:
                    c = np.zeros(len(state.M))
                    offset = 0 if role == "offense" else len(positions)
                    c[offset+positions[pair[0]]], c[offset+positions[pair[1]]] = sign, -sign
                    row.update(_assessed_contrast(state, c, surfaces, transports, regions))
                pair_rows.append(row)
    for name, records in (("players", player_rows), ("pairs", pair_rows)):
        path = output / (name + ".jsonl")
        with path.open("x") as destination:
            for row in records:
                destination.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")
        tables[name] = identity(path)
    map_path = output / "selected-maps.npz"
    maps = np.stack([row["map"] for row in selected_maps]) if selected_maps else np.empty((0, 656))
    with map_path.open("xb") as destination:
        np.savez(destination, maps=maps)
    exposure_summary = []
    for population in POPULATIONS:
        for role in ("offense", "suppression"):
            candidates = [row for row in player_rows if row["benchmark"] == population and row["role"] == role]
            cutpoints = np.quantile([row["exposure_seconds"] for row in candidates], [.25, .5, .75], method="linear") if candidates else np.array([])
            groups = []
            for index in range(4):
                members = [row for row in candidates if np.searchsorted(cutpoints, row["exposure_seconds"], side="right") == index]
                available = [row for row in members if row["status"] == "available"]
                widths = [row["scalar"]["relative_upper"]-row["scalar"]["relative_lower"] for row in available]
                groups.append(dict(quartile=index+1, players=len(members), available=len(available),
                    statuses=dict(Counter(row["scalar"]["status"] for row in available)),
                    median_relative_width=float(np.median(widths)) if widths else None,
                    minimum_seconds=min((row["exposure_seconds"] for row in members), default=None),
                    maximum_seconds=max((row["exposure_seconds"] for row in members), default=None)))
            exposure_summary.append(dict(benchmark=population, role=role, cutpoints_seconds=cutpoints.tolist(), groups=groups))
    recovery = list(rows(recovery_path))
    recovery_summary = []
    for case in ("mixed", "paired", "count_stress"):
        for population in POPULATIONS:
            for year in range(1, 6):
                available = [row for row in recovery if row["case"] == case and row["benchmark"] == population
                             and row["year"] == year and row["response"] == "scalar" and row["n"]]
                recovery_summary.append(dict(case=case, benchmark=population, year=year,
                    available_named_contrasts=len(available),
                    pointwise_coverage_rate_range=[min(row["coverage"]["rate"] for row in available),
                        max(row["coverage"]["rate"] for row in available)] if available else None,
                    median_relative_interval_width=float(np.median([row["mean_relative_width"] for row in available])) if available else None,
                    interpretation="descriptive across contrasts; each named row retains its own replicate denominator and wilson interval"))
    figures = _assessment_figures(output, document, player_rows, pair_rows, selected_maps, reference_document)
    result = dict(schema_version=1, kind="attribution_assessment", purpose=document["purpose"],
        implementation=current_implementation, protocol=document["protocol"], prepared=prepared_reference,
        chains=identity(chains_path), simulation=identity(simulation_path), reference=reference,
        annual=annual_statuses, coverage=coverage, game_coverage=document["ledgers"]["coverage"],
        pairs=document["pairs"], tables=tables, exposure_summary=exposure_summary,
        selected_maps=dict(reference=identity(map_path), shapes=dict(maps=list(maps.shape)),
            order=[dict(player_id=row["player_id"], role=row["role"]) for row in selected_maps]),
        recovery=dict(reference=simulation_document["recovery"], summaries=recovery_summary,
                      scale_statuses=simulation_document["scale_statuses"]),
        scenarios=dict(location=transport_details, probability_logodds_changes=[-.10, .10],
                       league_baselines=scenario_baselines,
                       crossed=False, interval_meaning="conditional intervals; scenario changes are separate unit stresses"),
        figures=figures, league_baselines=reference_document["league_baselines"],
        row_contracts=dict(players="final-season current observed player/role in population then stable-id order; recorded counts and fitted effects are separate",
            pairs="frozen pair/population/role; first id minus second, unavailable is null plus reason",
            coverage_teams="population/season/team; measured known losses, with unknown horizons counted separately",
            coverage_players="population/season/player across teams; unknown membership loss stays null, known partial loss remains separate"),
        units=dict(effects="attempts per 60; suppression is negative defense exactly once",
            relative_effects="share of the population annual league team rate", valuation="provisional goals per 60 effects",
            league_baselines="provisional goals per 60 team minutes",
            maps="centered recorded unblocked associations per native cell; not observed density",
            counts="recorded admitted on-ice attempts", exposure="known admitted seconds; unknown excluded duration is not zero"),
        limitations=["research-only recorded-rate associations, not published ability or causal effects",
            "selective coordinate-complete spatial exposure; no missing-at-random claim",
            "pointwise gaussian working intervals condition on references, response shape and fitted scales",
            "age-neutral borrowing, omitted deployment, unsmoothed cells and separable uncertainty",
            "negative fitted rates are retained; bound/refinement failures remain visible",
            "unadmitted provisional weights; chance/reference uncertainty and player type/context-mix credit omitted",
            "unit stresses are not truth-error bounds; consequence budgets remain open"],
        admission="not_admitted", handoff=None, resources=resources(started))
    write_json(output / "assessment.json", result)
    return identity(output / "assessment.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="manual research-only attribution commands", allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", allow_abbrev=False)
    for name in ("protocol", "selection", "out"):
        prepare.add_argument("--" + name, required=True)
    fit = commands.add_parser("fit-year", allow_abbrev=False)
    for name in ("prepared", "benchmark", "season", "out"):
        fit.add_argument("--" + name, required=True)
    fit.add_argument("--previous")
    simulation = commands.add_parser("simulate", allow_abbrev=False)
    for name in ("protocol", "out"):
        simulation.add_argument("--" + name, required=True)
    assessment = commands.add_parser("assess", allow_abbrev=False)
    for name in ("prepared", "chains", "simulation", "out"):
        assessment.add_argument("--" + name, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare_attribution(args.selection, args.protocol, args.out)
    elif args.command == "fit-year":
        result = fit_prepared_year(args.prepared, args.benchmark, args.season, args.previous, args.out)
    elif args.command == "simulate":
        result = simulate(args.protocol, args.out)
    else:
        result = assess(args.prepared, args.chains, args.simulation, args.out)
    print(json.dumps(result, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
