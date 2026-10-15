"""manual 04a preparation, annual fitting and fixed known-truth research exercise."""

import argparse
from collections import Counter
from itertools import combinations
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy import sparse
from scipy.stats import norm

from hockey_stats.artifacts import clean_implementation, implementation, linked_path, require, resources, write_json
from hockey_stats.attribution import (
    AnnualPopulation, contrast_interval, fit_prepared_year, fit_year, negative_rate_summary, validate_model_rules,
)
from hockey_stats.attribution_data import prepare_attribution
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


def scalar_contrast(state, player_contrast: np.ndarray) -> dict:
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
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare_attribution(args.selection, args.protocol, args.out)
    elif args.command == "fit-year":
        result = fit_prepared_year(args.prepared, args.benchmark, args.season, args.previous, args.out)
    else:
        result = simulate(args.protocol, args.out)
    print(json.dumps(result, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
