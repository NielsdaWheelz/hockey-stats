"""04e's frozen paired populations, physical truths and mean-risk comparison."""

import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import sys
import time

for _thread in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_thread] = "1"

import numpy as np

from hockey_stats.artifacts import (
    artifact, implementation, json_values, linked_path, load_arrays,
    ordered_array_digest, read_artifact, require, resources, write_arrays, write_json,
)
from hockey_stats.chance_cli import identity, output_path
from hockey_stats.captures import InputContractError
from hockey_stats.attribution_data import POOLING_STAT_FIELDS as STAT_FIELDS
from hockey_stats.attribution_prediction import current_player_rows, deployment_gram, prediction_loss
from hockey_stats.attribution_simulation import PAIR_SLOTS, paired_truths, shape_regions, truth_digest
from hockey_stats.shot_origins import grid

SPEC = Path(__file__).resolve().parents[2] / "docs/specs/04e-attribution-pooling.md"
OLD_ROOT = Path("/Volumes/Expansion/hockey-stats/runs/attribution-04c-20261016")
RESEARCH_ROOT = Path("/Volumes/Expansion/hockey-stats/runs")
SEASONS = tuple(f"{year}{year + 1}" for year in range(2021, 2026))
POPULATIONS = ("sparse", "diffuse", "null")
LAWS = ("gaussian", "game_pace")
ARMS = ("graph_40ft", "graph_two_band_80ft")
BENCHMARK = "unblocked_spatial"
BASIS_FILE_SHA = "67d7ee706f1d8d251cc68a0d22378e67e1961b2ac53fb764bfc0efdff11d43fc"
BASIS_SHA = "649a49ecba19de5df609d6980d9de76491afa13e9108df0d8e6500659886cc51"
DESIGN_FIELDS = ("offense", "defense", "seconds", "si", "u", "player_exposure", "home_teams",
                 "away_teams", "row_game_ids")
UPDATES_PER_DATASET = dict(datasets=1, histories=2, annual_states=10, volume_updates=5, shape_updates=15)
ARRAY_UNITS = dict(statistics="original residualized count-unit sufficient statistics; ordered current offense/defense rows",
                   probe_means="relative league team rate; original all-seen offense/defense rows; one native context")
RULES = dict(
    seasons=list(SEASONS), populations=list(POPULATIONS), laws=list(LAWS), representations=list(ARMS),
    source_kind="synthetic", annual_rate=40.,
    seeds=dict(design_train=40600, design_eval=40601, physical_fields=40602, activation=40603,
               responses=40604, paired_bootstrap=40605, bit_generator="PCG64", index_base=0),
    bands=dict(low=list(range(11)), high=list(range(11, 40)), nominal_wavelength_feet=80,
               cutoff=float((2 * np.pi / 80) ** 2), ranks=[11, 29]),
    truths=dict(pair_slots=PAIR_SLOTS, role_order=["offense", "defense"], amplitude=.10,
                lobe_draw_order=["x1", "y1", "w1", "x2", "y2", "w2"],
                x_bounds=[0, 80], y_bounds=[-30, 30], width_bounds=[20, 40],
                centering="separately by role under training u; one compensated native context",
                absent="no truth for carried-only rows", scalar_effect=0.),
    criteria=dict(recovery_fraction=.75, prediction_gain_cost=.01, interval=[.025, .975],
                  quantile="linear", bootstrap_resamples=10000, denominator=30, primary_year=5,
                  strict_positive=[False, True, True, False], null_gate=False),
    rank_policy=dict(tau="100*n*eps*lambda_max", sensitivity=[.1, 1., 10.], null_tolerance=1e-8),
    numerical=dict(relative_tolerance=1e-8, movement_max=1e-4, probe_outer=0, probe_years=[1, 5],
                   refinement=dict(xatol=1e-6, maxiter=80), history_rerun=False),
    examples=dict(year=5, outer=0, both_laws=True,
                  identities=["sparse_team0_offense_first_active", "sparse_team0_offense_first_inactive",
                              "diffuse_team0_defense_first_pair", "diffuse_team3_offense_inseparable"]),
    figure_contracts=dict(recovery_prediction="all sixteen bounds; adjacent inactive/null absolute risks",
                          spatial="actual truth/control/candidate common native scales; low/high regional contributions"),
    admission="not_admitted", handoff=None,
)
LIMITATIONS = [
    "one additional covariance and scale process; gaussian band independence is a working assumption",
    "fixed training/evaluation deployment designs and training exposure references limit generalization",
    "broad physical lobe families do not establish useful recovery for every hockey effect",
    "slot-based entry/return transitions stress changing player truth",
    "working player uncertainty is unvalidated; monte carlo intervals concern mean risks only",
    "additive complete fitted rates may be negative and are never clipped",
    "synthetic nomination does not establish real-hockey identification, chance valuation or admission",
    "native pixels and an 80-foot nominal cutoff do not establish native precision",
    "inseparable player differences remain unsupported by the likelihood despite finite prior estimates",
]


def _rng(seed):
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed)))



def example_pairs(truth):
    pairs = [pair for pair in truth["pairs"] if pair["team"] == 0 and pair["role"] == "offense"]
    return [next(pair["pair"] for pair in pairs if pair["active"]),
            next(pair["pair"] for pair in pairs if not pair["active"])]


def _example_identities(sparse_truth):
    selected = example_pairs(sparse_truth)
    examples = []
    for label, pair_id in zip(("first_active", "first_inactive"), selected, strict=True):
        pair = next(pair for pair in sparse_truth["pairs"]
                    if pair["team"] == 0 and pair["role"] == "offense" and pair["pair"] == pair_id)
        examples.append(dict(name="sparse_team0_offense_" + label, population="sparse", **pair))
    examples.extend([
        dict(name="diffuse_team0_defense_first_pair", population="diffuse", team=0, role="defense", pair=0,
             players=[32, 1], active=True, expected_estimable=True),
        dict(name="diffuse_team3_offense_inseparable", population="diffuse", team=3, role="offense", pair=1,
             players=[26, 31], active=True, expected_estimable=False),
    ])
    return examples


def _activation_digest(truths):
    return ordered_array_digest({str(year): np.array([[pair["team"], int(pair["role"] == "defense"), pair["pair"],
                                                     *pair["players"], int(pair["active"])] for pair in truth["pairs"]], dtype=np.int64)
                                 for year, truth in enumerate(truths)})


def criterion_status(lower, upper, strict):
    supported = lower > 0 if strict else lower >= 0
    failed = upper <= 0 if strict else upper < 0
    if supported:
        return "supported"
    if failed:
        return "failed"
    return "inconclusive"


def criterion_rows(records, population, law):
    """paired whole-history bootstrap; risks are averaged before any comparison."""
    require(population in POPULATIONS[:2] and law in LAWS and bool(records), "invalid primary criterion cell")
    names = ("R_zero", "R_control", "R_candidate", "P_zero", "P_control", "P_candidate")
    values = np.array([[row[name] for name in names] for row in records], dtype=float)
    require(np.isfinite(values).all() and np.all(values >= 0), "criterion risks must be finite and nonnegative")
    draws = _rng([40605, POPULATIONS.index(population), LAWS.index(law)]).integers(
        0, len(records), size=(10000, len(records)))
    rz, rc, rb, pz, pc, pb = values.T
    contrasts = np.column_stack((.75 * rz - rb, rc - rb, pz - pc, .01 * (pz - pc) - (pb - pc)))
    boot = contrasts[draws].mean(axis=1)
    bounds = np.quantile(boot, [.025, .975], axis=0, method="linear")
    labels = ("regional_recovery_25pct", "regional_improvement", "positive_control_prediction_gain", "prediction_gain_retention_99pct")
    return [dict(population=population, law=law, criterion=name, mean=float(contrasts[:, i].mean()),
                 lower=float(bounds[0, i]), upper=float(bounds[1, i]), strict_positive=strict,
                 status=criterion_status(bounds[0, i], bounds[1, i], strict), n=len(records),
                 resamples=10000, seed=[40605, POPULATIONS.index(population), LAWS.index(law)],
                 units="squared attempts per 60 team minutes")
            for i, (name, strict) in enumerate(zip(labels, (False, True, True, False), strict=True))]


def risk_ratios(means):
    gain = means["P_zero"] - means["P_control"]
    return dict(recovery_ratio=dict(value=means["R_candidate"] / means["R_zero"] if means["R_zero"] > 0 else None,
                                    reason=None if means["R_zero"] > 0 else "zero_truth_risk"),
                prediction_gain_retention=dict(value=(means["P_zero"] - means["P_candidate"]) / gain if gain > 0 else None,
                                               reason=None if gain > 0 else "nonpositive_control_gain"))


def _design_arrays(train, evaluation, W):
    arrays = {f"{name}_{year}_{field}": design[field]
              for name, designs in (("train", train), ("evaluation", evaluation))
              for year, design in enumerate(designs) for field in DESIGN_FIELDS}
    arrays.update(centers=grid()[0], W=W)
    return arrays


def _fixed_designs(p, purpose):
    from hockey_stats.attribution_simulation import paired_designs

    repetitions, stints = (16, 50) if purpose == "research" else (2, 6)
    histories = []
    for seed in (40600, 40601):
        designs = paired_designs(np.random.Generator(np.random.PCG64(seed)), repetitions=repetitions,
                                 stints_per_game=stints, purpose=purpose)
        for design in designs:
            design["p"] = p
        histories.append(designs)
    for train, evaluation in zip(*histories, strict=True):
        require(train["players"] == evaluation["players"] and train["strata"] == evaluation["strata"]
                and np.array_equal(train["home_teams"], evaluation["home_teams"])
                and np.array_equal(train["away_teams"], evaluation["away_teams"])
                and not np.array_equal(train["offense"], evaluation["offense"]), "independent design contract changed")
    return histories


def _old_geometry():
    from hockey_stats.attribution import read_shape_basis

    result_path, protocol_path = OLD_ROOT / "assessment/result.json", OLD_ROOT / "inputs/protocol.json"
    result = read_artifact(result_path, "attribution_recovery_result")
    read_artifact(protocol_path, "attribution_recovery_protocol")
    require(result["model_protocol"] == identity(protocol_path), "original 04c protocol/result chain differs")
    reference = result["evidence"]["prepared"]
    prepared = read_artifact(linked_path(reference), "attribution_recovery_prepared")
    require(prepared["model_protocol"] == identity(protocol_path)
            and prepared["basis"]["sha256"] == BASIS_FILE_SHA and prepared["basis_sha256"] == BASIS_SHA,
            "04e requires the exact original saved basis")
    basis = read_shape_basis(prepared)
    return basis, prepared, dict(original_protocol=identity(protocol_path), original_result=identity(result_path),
                                 original_prepared=reference, basis=prepared["basis"])


def _cost(started, process_started):
    return dict(**resources(started), process_seconds=time.process_time() - process_started)


def _budgets(outer_count):
    return dict(outer_per_cell=outer_count, datasets=6 * outer_count, fitted_histories=12 * outer_count,
                annual_states=60 * outer_count, volume_updates=30 * outer_count, shape_updates=90 * outer_count,
                annual_probes=24, shape_block_probes=36, bootstrap_resamples=10000, replacements=0, nested_refits=0)


def prepare(purpose, output):
    from hockey_stats.attribution import build_shape_basis, validate_pooling_basis

    started, process_started = time.monotonic(), time.process_time()
    require(purpose in ("research", "fixture_exercise"), "unknown preparation purpose")
    if purpose == "research":
        basis, original, parents = _old_geometry()
    else:
        basis = build_shape_basis(grid(), np.full(656, 1 / 656))
        original, parents = {}, {}
    validate_pooling_basis(basis)
    train, evaluation = _fixed_designs(basis.p, purpose)
    W, regions = shape_regions()
    design_arrays = _design_arrays(train, evaluation, W)
    root = output_path(str(output), [str(OLD_ROOT)])
    if purpose == "research":
        require(root.is_relative_to(RESEARCH_ROOT) and root.name.startswith("attribution-04e-"),
                "research preparation requires a new external attribution-04e directory")
    root.mkdir()
    if purpose == "fixture_exercise":
        binding = write_arrays(root, "synthetic-basis.npz", dict(B=basis.B, p=basis.p, eigenvalues=basis.eigenvalues))
        original["basis_shapes"] = binding["array_shapes"]
        parents["basis"] = binding["arrays"]
    snapshot = root / "spec-snapshot.md"
    with snapshot.open("xb") as destination:
        destination.write(SPEC.read_bytes())
    protocol_path = root / "protocol.json"
    outer_count = 200 if purpose == "research" else 2
    protocol = artifact("attribution_pooling_protocol", purpose, dict(**parents, spec_snapshot=identity(snapshot)),
        schema_version=4, spec_snapshot=identity(snapshot), **parents, **json_values(RULES),
        budgets=_budgets(outer_count),
        design=dict(name="paired_direct_research" if purpose == "research" else "paired_12_games_6_stints_fixture",
                    games_per_year=len(train[0]["game_ids"]), stints_per_game=len(train[0]["seconds"]) // (2 * len(train[0]["game_ids"])),
                    train_sha256=ordered_array_digest(_design_arrays(train, [], W)),
                    evaluation_sha256=ordered_array_digest(_design_arrays([], evaluation, W))),
        design_sha256=ordered_array_digest(design_arrays), basis_sha256=basis.sha256,
        basis_source="original_04c" if purpose == "research" else "explicit_synthetic_uniform_fixture",
        regions=list(regions), output_root=str(root), limitations=LIMITATIONS, resources=_cost(started, process_started))
    write_json(protocol_path, json_values(protocol))
    bindings = write_arrays(root, "designs.npz", design_arrays)
    document = artifact("attribution_pooling_prepared", purpose,
        dict(protocol=identity(protocol_path), basis=parents["basis"], spec_snapshot=identity(snapshot), designs=bindings["arrays"]),
        schema_version=4, protocol=identity(protocol_path), spec_snapshot=identity(snapshot),
        basis=parents["basis"], basis_shapes=original["basis_shapes"], basis_sha256=basis.sha256,
        designs=bindings, design_sha256=protocol["design_sha256"], seasons=list(SEASONS),
        years=[dict(season=season, players=list(design["players"]), strata=design["strata"])
               for season, design in zip(SEASONS, train, strict=True)], regions=list(regions),
        examples=_example_identities(paired_truths(train, basis.p, "sparse", 0)[-1]),
        units=dict(response="count units; gaussian may be signed/fractional", shape="relative league team rate",
                   risk="squared attempts per 60 team minutes", rate="attempts per 60 team minutes"),
        resources=_cost(started, process_started), admission="not_admitted", handoff=None)
    path = root / "prepared.json"
    write_json(path, json_values(document))
    return identity(path)


def read_prepared(path, *, source=None):
    from hockey_stats.attribution import read_pooling_source

    source = read_pooling_source(path) if source is None else source
    require(Path(path).resolve(strict=True) == Path(source.reference["path"]), "prepared path differs from validated source")
    document, protocol, basis = source.prepared, source.protocol, source.basis
    require(document["purpose"] == protocol["purpose"] and document["spec_snapshot"] == protocol["spec_snapshot"]
            and all(protocol.get(name) == expected for name, expected in json_values(RULES).items())
            and protocol["basis_sha256"] == document["basis_sha256"]
            and protocol["basis"] == document["basis"]
            and document["seasons"] == list(SEASONS) and protocol["limitations"] == LIMITATIONS,
            "prepared scientific protocol or original geometry identity differs")
    if document["purpose"] == "research":
        require(document["basis_sha256"] == BASIS_SHA and document["basis"]["sha256"] == BASIS_FILE_SHA
                and protocol["basis_source"] == "original_04c", "research basis differs from the original 04c evidence")
    else:
        require(protocol["basis_source"] == "explicit_synthetic_uniform_fixture", "fixture basis source changed")
    expected_count = 200 if document["purpose"] == "research" else 2
    require(protocol["budgets"] == _budgets(expected_count), "frozen dataset budget changed")
    require(document["consumed"] == dict(protocol=document["protocol"], basis=document["basis"],
            spec_snapshot=document["spec_snapshot"], designs=document["designs"]["arrays"]), "prepared consumed parents differ")
    if document["purpose"] == "research":
        require(document["implementation"] == protocol["implementation"], "prepared producer differs from frozen protocol")
    train, evaluation = _fixed_designs(basis.p, document["purpose"])
    W, regions = shape_regions()
    arrays = load_arrays(document["designs"])
    expected = _design_arrays(train, evaluation, W)
    require(list(arrays) == list(expected) and all(np.array_equal(arrays[name], expected[name]) for name in expected)
            and ordered_array_digest(arrays) == document["design_sha256"] == protocol["design_sha256"]
            and document["regions"] == protocol["regions"] == list(regions)
            and document["years"] == json_values([dict(season=season, players=list(design["players"]), strata=design["strata"])
                                                    for season, design in zip(SEASONS, train, strict=True)]),
            "saved train/evaluation design, player order or region operator changed")
    require(document["examples"] == _example_identities(paired_truths(train, basis.p, "sparse", 0)[-1]),
            "frozen example identities differ from response-independent activation")
    require(protocol["design"] == dict(
        name="paired_direct_research" if document["purpose"] == "research" else "paired_12_games_6_stints_fixture",
        games_per_year=len(train[0]["game_ids"]),
        stints_per_game=len(train[0]["seconds"]) // (2 * len(train[0]["game_ids"])),
        train_sha256=ordered_array_digest(_design_arrays(train, [], W)),
        evaluation_sha256=ordered_array_digest(_design_arrays([], evaluation, W))), "frozen deployment design policy changed")
    return document, protocol, basis, train, evaluation, W


def _scale_summary(block):
    return dict(a=block.a, q=block.q, **{name: block.scale[name] for name in
                ("selected", "status", "own_reasons", "inherited_limitation")},
                bound_selected=block.scale["selected"]["variance"] in (1e-8, 1.))


def annual_losses(control, candidate, population, training, evaluation, truth, basis, W):
    """actual truth and training gauge; all identifiable pairs share denominator thirty."""
    from hockey_stats.attribution import complete_rates, shape_mean
    from hockey_stats.attribution_data import centered_estimability, exposure_centering, likelihood_spectrum

    rows = current_player_rows(control, training["players"])
    require(control.player_ids == candidate.player_ids and control.current_player_ids == candidate.current_player_ids
            and np.array_equal(control.u, candidate.u) and np.array_equal(control.p, candidate.p)
            and all(np.array_equal(getattr(control.volume, name), getattr(candidate.volume, name))
                    for name in ("M", "V", "A", "prior_mean", "prior_covariance")), "paired annual source/volume differs")
    H = np.zeros((len(control.volume.M),) * 2)
    H[np.ix_(rows, rows)] = population.H
    P = exposure_centering(control.u)
    spectrum = likelihood_spectrum(H)
    positions = {player: i for i, player in enumerate(control.player_ids)}
    pairs, c_vectors = [], []
    for pair in truth["pairs"]:
        c = np.zeros(len(control.volume.M))
        offset = len(positions) if pair["role"] == "defense" else 0
        c[offset + positions[pair["players"][0]]] = 1
        c[offset + positions[pair["players"][1]]] = -1
        rank = centered_estimability(H, P, c, spectrum=spectrum)
        expected = "available" if pair["expected_estimable"] else "not_estimable"
        require(rank["status"] == expected, "unexpected pair estimability: " + str(pair))
        pairs.append(dict(**pair, estimability=rank))
        c_vectors.append(c)
    require(len(pairs) == 32 and sum(pair["expected_estimable"] for pair in pairs) == 30,
            "pair inventory must have exactly thirty estimable and two inseparable contrasts")
    C = np.array(c_vectors)
    C_current = C[:, rows]
    true_contrasts = 40 * C_current @ truth["centered"]
    true_regional = true_contrasts @ W
    projected = truth["centered"] @ basis.B @ basis.R.T
    projected_regional = 40 * C_current @ projected @ W
    estimable = np.array([pair["expected_estimable"] for pair in pairs])
    active = np.array([pair["active"] for pair in pairs])
    true_energy = np.sum(true_regional ** 2, axis=1)
    record = dict(R_zero=float(true_energy[estimable].sum() / 30), pairs=pairs,
                  denominator=30, truth_native_energy=float(np.sum(true_contrasts[estimable] ** 2) / 30),
                  projected_truth_regional_error=float(np.sum((projected_regional[estimable] - true_regional[estimable]) ** 2) / 30),
                  projected_truth_native_error=float(np.sum((40 * C_current @ projected - true_contrasts)[estimable] ** 2) / 30),
                  truth_active_count=int(np.count_nonzero(estimable & active)),
                  truth_inactive_count=int(np.count_nonzero(estimable & ~active)))
    gram = deployment_gram(evaluation["X"], evaluation["si"], evaluation["e"], len(evaluation["strata"]))
    yh = population.ybar - population.ybar.sum(axis=1, keepdims=True) * basis.p
    record["P_zero"] = prediction_loss(gram, yh - truth["context"], -truth["centered"], p=basis.p)
    current_positions = {player: i for i, player in enumerate(training["players"])}
    transitions = [player for player in (32, 33) if control.season_index >= 2 and player in current_positions]
    if control.season_index >= 3 and 8 in current_positions:
        transitions.append(8)
    for arm, state in (("control", control), ("candidate", candidate)):
        maps = shape_mean(state)
        current = maps[rows]
        error = 40 * (C @ maps) @ W - true_regional
        errors = np.sum(error ** 2, axis=1)
        total = float(errors[estimable].sum() / 30)
        active_risk = float(errors[estimable & active].sum() / 30)
        inactive_risk = float(errors[estimable & ~active].sum() / 30)
        require(abs(total - active_risk - inactive_risk) <= 1e-10 * max(1., total), "active/inactive risks do not reconcile")
        record["R_" + arm] = total
        record["P_" + arm] = prediction_loss(gram, state.shape.A - truth["context"], current - truth["centered"], p=basis.p)
        partition = dict(active=active_risk, inactive=inactive_risk)
        for role in ("offense", "defense"):
            mask = estimable & np.array([pair["role"] == role for pair in pairs])
            partition[role] = float(errors[mask].sum() / 30)
        relative_volume = state.volume.M[rows, 0]
        columns = np.array([[positions[player] for player in attacking]
                            + [len(positions) + positions[player] for player in defending]
                            for attacking, defending in zip(evaluation["offense"], evaluation["defense"], strict=True)])
        negative_cells, negative_rows, minimum = 0, 0, None
        for start in range(0, len(columns), 256):
            rates = complete_rates(state, columns[start:start + 256], evaluation["si"][start:start + 256])
            negative_cells += int(np.count_nonzero(rates < 0))
            negative_rows += int(np.count_nonzero(np.any(rates < 0, axis=1)))
            minimum = float(rates.min()) if minimum is None else min(minimum, float(rates.min()))
        diagnostics = dict(
            regional_partition=partition, false_map_regional_rms=float(np.sqrt(inactive_risk)),
            native_shape_error=float(np.sum((40 * (C @ maps) - true_contrasts)[estimable] ** 2) / 30),
            projected_regional_shape_error=float(np.sum((40 * (C @ maps) @ W - projected_regional)[estimable] ** 2) / 30),
            projected_native_shape_error=float(np.sum((40 * (C @ maps) - 40 * C_current @ projected)[estimable] ** 2) / 30),
            complete_native_pair_error=float(np.sum((40 * (C @ maps + (C @ state.volume.M) * basis.p) - true_contrasts)[estimable] ** 2) / 30),
            false_map_maximum_regional_norm=float(np.max(np.sqrt(errors[estimable & ~active]), initial=0.)),
            native_shape_prediction_error=prediction_loss(gram, state.shape.A - truth["context"], current - truth["centered"]),
            complete_rate_prediction_error=prediction_loss(gram,
                state.shape.A + state.volume.A * basis.p - basis.p - truth["context"],
                current + relative_volume[:, None] * basis.p - truth["centered"]),
            volume_player_mean_square=float(np.mean((40 * relative_volume) ** 2)),
            volume_scale=_scale_summary(state.volume), negative_cells=negative_cells, negative_rows=negative_rows,
            evaluated_cells=int(len(columns) * len(basis.p)), evaluated_rows=len(columns), minimum_complete_rate=minimum,
            transitions=[dict(player=player, role=("offense", "defense")[role],
                event=("return" if state.season_index == 3 else "post_return") if player == 8 else
                      ("entry" if state.season_index == 2 else "post_entry"),
                event_year=4 if player == 8 else 3,
                regional_squared_error=float(np.sum((40 * (current[index] - truth["centered"][index]) @ W) ** 2)))
                for player in transitions for role in range(2)
                for index in [role * len(training["players"]) + current_positions[player]]],
            shape_scales=(dict(low=_scale_summary(state.shape.low), high=_scale_summary(state.shape.high))
                          if arm == "candidate" else dict(all=_scale_summary(state.shape))),
            inseparable=[dict(role=pair["role"], players=pair["players"], status="not_estimable",
                              regional_squared_error=float(errors[i]), evidence="unsupported prior allocation")
                         for i, pair in enumerate(pairs) if not pair["expected_estimable"]])
        record[arm] = diagnostics
    return record


def _populations(train, truths, protocol_sha, population, law, outer):
    from hockey_stats.attribution_data import statistic_digest, synthetic_population, weighted_population
    from hockey_stats.attribution_simulation import synthetic_response

    populations, response_digests, statistics = {}, [], {}
    source_id = f"synthetic:04e:{population}:{law}:{outer}:{BENCHMARK}"
    for year, (design, truth) in enumerate(zip(train, truths, strict=True)):
        seed = [40604, POPULATIONS.index(population), LAWS.index(law), outer, year]
        rates = 40 * (design["p"] + design["X"] @ truth["raw"])
        responses = synthetic_response(design, rates, law, _rng(seed))
        response_sha = ordered_array_digest(dict(response=responses))
        grouped, refs = synthetic_population(design, responses, year, protocol_sha, LAWS.index(law), outer,
                                             population_id=source_id)
        fitted_population = weighted_population(grouped, np.ones(len(grouped.game_ids)), refs)
        populations[(BENCHMARK, SEASONS[year])] = (grouped, refs)
        response_digests.append(dict(year=year + 1, season=SEASONS[year], seed=seed, sha256=response_sha,
                                     sufficient_statistics_sha256=statistic_digest(fitted_population)))
        statistics.update({SEASONS[year] + "_" + name: np.asarray(getattr(fitted_population, name)) for name in STAT_FIELDS})
        del responses
    return populations, response_digests, statistics


def _numerical_failures(receipt):
    return [row for row in receipt["annual"] if row["status"] != "complete"]


def fit(prepared, population, law, start, stop, output):
    from hockey_stats.attribution import bounded_pooling_resolution_check, read_pooling_source, read_pooling_statistics, write_pooling_annual
    from hockey_stats.attribution_data import weighted_population
    from hockey_stats.attribution_uncertainty import RefitInputs, annual_receipts, exact_duplicate_groups, fit_history

    started, process_started = time.monotonic(), time.process_time()
    prepared_path = Path(prepared).resolve(strict=True)
    source_context = read_pooling_source(prepared_path)
    document, protocol, basis, train, evaluation, W = read_prepared(prepared_path, source=source_context)
    require(population in POPULATIONS and law in LAWS and type(start) is int and type(stop) is int
            and 0 <= start < stop <= protocol["budgets"]["outer_per_cell"], "fit range or population identity differs")
    root = output_path(str(output), [])
    require(root.is_relative_to(Path(protocol["output_root"])), "fit output escaped the frozen study root")
    if document["purpose"] == "research":
        require(implementation() == protocol["implementation"], "fit producer differs from frozen protocol")
    root.mkdir()
    records = []
    for outer in range(start, stop):
        outer_started, outer_process = time.monotonic(), time.process_time()
        directory = root / f"outer-{outer:03d}"
        directory.mkdir()
        truths = paired_truths(train, basis.p, population, outer)
        # evaluation uses the training-centered truth and its compensated context.
        for design, truth in zip(evaluation, truths, strict=True):
            require(np.all(40 * (basis.p + design["X"] @ truth["raw"]) > 0), "evaluation truth has invalid rates")
        populations, digests, arrays = _populations(train, truths, document["protocol"]["sha256"], population, law, outer)
        stats_binding = write_arrays(directory, "statistics.npz", arrays)
        statistics_context = read_pooling_statistics(stats_binding["arrays"], source_context)
        groups = exact_duplicate_groups(populations, list(SEASONS), benchmarks=(BENCHMARK,))
        inputs = RefitInputs(dict(seasons=list(SEASONS)), protocol, populations, None, groups, "synthetic")
        weights = {season: np.ones(len(populations[(BENCHMARK, season)][0].game_ids)) for season in SEASONS}
        control_receipt, control = fit_history(inputs, [], benchmarks=(BENCHMARK,), game_multipliers=weights,
            representation=ARMS[0], basis=basis, model_protocol_sha256=document["protocol"]["sha256"], prior_policy="history")
        require(control_receipt["status"] == "complete", "control numerical execution incomplete: " + str(_numerical_failures(control_receipt)))
        candidate_receipt, candidate = fit_history(inputs, [], benchmarks=(BENCHMARK,), game_multipliers=weights,
            representation=ARMS[1], basis=basis, model_protocol_sha256=document["protocol"]["sha256"],
            prior_policy="history", shared_volume=control)
        require(candidate_receipt["status"] == "complete", "candidate numerical execution incomplete: " + str(_numerical_failures(candidate_receipt)))
        histories, losses, probes, probe_arrays = {arm: [] for arm in ARMS}, [], [], {}
        previous_refs = {arm: None for arm in ARMS}
        for year, season in enumerate(SEASONS):
            key = (BENCHMARK, season)
            grouped, refs = populations[key]
            annual_population = weighted_population(grouped, weights[season], refs)
            states = [control[key], candidate[key]]
            require(states[0].volume is states[1].volume, "candidate did not share the explicit immutable volume block")
            losses.append(dict(year=year + 1, **annual_losses(*states, annual_population, train[year], evaluation[year], truths[year], basis, W)))
            alternate = []
            for arm, history, state in zip(ARMS, (control, candidate), states, strict=True):
                previous = history.get((BENCHMARK, SEASONS[year - 1])) if year else None
                ref = write_pooling_annual(state, source_context, previous_refs[arm], directory / f"{arm}-{season}",
                    population=population, law=law, outer=outer, response_sha256=digests[year]["sha256"],
                    statistics=statistics_context, shared_volume=histories[ARMS[0]][-1] if arm == ARMS[1] else None,
                    previous_state=previous, shared_volume_state=control[key] if arm == ARMS[1] else None)
                previous_refs[arm] = ref["path"]
                histories[arm].append(ref)
                if outer == 0 and year in (0, 4):
                    positions = {player: i for i, player in enumerate(state.player_ids)}
                    projections = []
                    for pair in truths[year]["pairs"]:
                        if not pair["expected_estimable"]:
                            continue
                        c = np.zeros(2 * len(positions))
                        offset = len(positions) if pair["role"] == "defense" else 0
                        c[offset + positions[pair["players"][0]]] = 1
                        c[offset + positions[pair["players"][1]]] = -1
                        projections.extend((c, weights, "shape") for weights in W.T)
                    altered, probe = bounded_pooling_resolution_check(annual_population, previous, state, regions=W,
                                                                       projections=tuple(projections))
                    alternate.append(altered)
                    prefix = f"year_{year + 1}_{arm}_"
                    if arm == ARMS[0]:
                        probe_arrays[prefix + "Theta"] = altered.shape.Theta
                    else:
                        probe_arrays[prefix + "low_Theta"] = altered.shape.low.Theta
                        probe_arrays[prefix + "high_Theta"] = altered.shape.high.Theta
                    probe_arrays[prefix + "A"] = altered.shape.A
                    probes.append(dict(population=population, law=law, outer=outer, year=year + 1, arm=arm, **probe))
            if alternate:
                alternate_losses = annual_losses(*alternate, annual_population, train[year], evaluation[year], truths[year], basis, W)
                for probe in probes[-2:]:
                    probe["loss_movement"] = {name: alternate_losses[name] - losses[-1][name]
                                               for name in ("R_control", "R_candidate", "P_control", "P_candidate")}
                    probe["probed_losses"] = {name: alternate_losses[name] for name in
                                               ("R_zero", "R_control", "R_candidate", "P_zero", "P_control", "P_candidate")}
        records.append(dict(outer=outer, population=population, law=law, status="complete", truth_sha256=truth_digest(truths),
            activation=[truth["pairs"] for truth in truths], activation_sha256=_activation_digest(truths),
            responses=digests, statistics=stats_binding,
            annual=histories, losses=losses, numerical_probes=probes,
            probe_means=write_arrays(directory, "probe-means.npz", probe_arrays) if probe_arrays else None,
            history_receipts={arm: dict(status=receipt["status"], annual=annual_receipts(receipt["annual"]), resources=receipt["resources"])
                              for arm, receipt in ((ARMS[0], control_receipt), (ARMS[1], candidate_receipt))},
            resources=_cost(outer_started, outer_process)))
    consumed = dict(prepared=identity(prepared_path), protocol=document["protocol"], basis=document["basis"],
                    designs=document["designs"]["arrays"], spec_snapshot=document["spec_snapshot"])
    result = artifact("attribution_pooling_fit", document["purpose"], consumed, schema_version=4,
        **consumed, basis_sha256=basis.sha256, design_sha256=document["design_sha256"], population=population, law=law,
        range=dict(start=start, stop=stop), records=records, status="complete", resources=_cost(started, process_started),
        cost={name: (stop - start) * count for name, count in UPDATES_PER_DATASET.items()}, array_units=ARRAY_UNITS,
        admission="not_admitted", handoff=None)
    path = root / "fit.json"
    write_json(path, json_values(result))
    return identity(path)


def fit_inventory(paths, prepared_reference, prepared_document, protocol):
    """six exact disjoint range inventories; an absent draw is never a scientific failure."""
    expected = protocol["budgets"]["outer_per_cell"]
    records, references, documents, ids = [], [], [], set()
    for path in paths:
        reference = identity(Path(path).resolve(strict=True))
        require(reference not in references, "duplicate fit manifest")
        document = read_artifact(path, "attribution_pooling_fit", expected_schema=4)
        parents = dict(prepared=prepared_reference, protocol=prepared_document["protocol"], basis=prepared_document["basis"],
                       designs=prepared_document["designs"]["arrays"], spec_snapshot=prepared_document["spec_snapshot"])
        require(document["purpose"] == prepared_document["purpose"] and document["consumed"] == parents
                and all(document[name] == reference for name, reference in parents.items())
                and document["basis_sha256"] == prepared_document["basis_sha256"]
                and document["design_sha256"] == prepared_document["design_sha256"]
                and document["status"] == "complete" and document["population"] in POPULATIONS
                and document["law"] in LAWS, "fit identity, source chain or completeness differs")
        if document["purpose"] == "research":
            require(document["implementation"] == protocol["implementation"], "fit implementation differs from frozen producer")
        start, stop = document["range"]["start"], document["range"]["stop"]
        require(type(start) is int and type(stop) is int and 0 <= start < stop <= expected
                and [row["outer"] for row in document["records"]] == list(range(start, stop)),
                "fit range is invalid or its ordered records are incomplete")
        require(document["cost"] == {name: (stop - start) * count for name, count in UPDATES_PER_DATASET.items()}
                and document["array_units"] == ARRAY_UNITS, "fit update inventory or array units differ")
        for row in document["records"]:
            key = (document["population"], document["law"], row["outer"])
            require(key not in ids and row["population"] == key[0] and row["law"] == key[1]
                    and row["status"] == "complete", "duplicate, overlapping or mismatched outer record")
            ids.add(key)
            records.append(row)
        references.append(reference)
        documents.append(document)
    require(ids == {(population, law, outer) for population in POPULATIONS for law in LAWS for outer in range(expected)},
            "assessment requires exact disjoint coverage of every frozen population/law/outer")
    require(all(sum(document["cost"][name] for document in documents) == 6 * expected * count
                for name, count in UPDATES_PER_DATASET.items()), "total fitted update inventory differs")
    return sorted(records, key=lambda row: (POPULATIONS.index(row["population"]), LAWS.index(row["law"]), row["outer"])), references, documents


def _same_losses(actual, expected):
    for name in ("R_zero", "R_control", "R_candidate", "P_zero", "P_control", "P_candidate"):
        require(np.isfinite(expected[name]) and abs(actual[name] - expected[name]) <= 1e-8 * (1 + abs(actual[name])),
                "saved annual loss does not reproduce: " + name)
    for arm in ("control", "candidate"):
        for name, value in actual[arm]["regional_partition"].items():
            require(abs(value - expected[arm]["regional_partition"][name]) <= 1e-8 * (1 + abs(value)),
                    "saved risk partition does not reproduce")


def _restored_probe(state, arrays, year, population):
    from hockey_stats.attribution import shape_mean

    prefix = f"year_{year}_{state.representation}_"
    A = arrays[prefix + "A"]
    require(A.shape == state.shape.A.shape, "probed native context shape differs")
    if state.representation == ARMS[0]:
        theta = arrays[prefix + "Theta"]
        require(theta.shape == state.shape.Theta.shape, "probed control coefficient shape differs")
        shape = replace(state.shape, Theta=theta, A=A)
    else:
        low, high = arrays[prefix + "low_Theta"], arrays[prefix + "high_Theta"]
        require(low.shape == state.shape.low.Theta.shape and high.shape == state.shape.high.Theta.shape,
                "probed band coefficient shape differs")
        shape = replace(state.shape, low=replace(state.shape.low, Theta=low),
                        high=replace(state.shape.high, Theta=high), A=A)
    restored = replace(state, shape=shape)
    maps = shape_mean(restored)
    n = len(state.player_ids)
    centered = [state.u @ maps[role * n:(role + 1) * n] for role in range(2)]
    current = maps[current_player_rows(state, state.current_player_ids)]
    yh = population.ybar - population.ybar.sum(axis=1, keepdims=True) * population.p
    context = yh - population.xbar @ current
    require(np.max(np.abs(centered)) <= 1e-8 and np.max(np.abs(maps.sum(axis=1))) <= 1e-8
            and np.max(np.abs(context - A)) <= 1e-8 * (1 + np.max(np.abs(context))),
            "probed means changed the training exposure gauge, zero sums or single native context")
    return restored


def _probe_movements(original, altered, truth, W):
    from hockey_stats.attribution import project, shape_mean

    selected = current_player_rows(original, original.current_player_ids)
    delta = shape_mean(altered)[selected] - shape_mean(original)[selected]
    movement = dict(native_cells=float(np.max(np.abs(delta))), regions=float(np.max(np.abs(delta @ W))),
                    scalars=float(np.max(np.abs(delta.sum(axis=1)))), requested_projections=0.)
    positions = {player: i for i, player in enumerate(original.player_ids)}
    for pair in truth["pairs"]:
        if not pair["expected_estimable"]:
            continue
        c = np.zeros(2 * len(positions))
        offset = len(positions) if pair["role"] == "defense" else 0
        c[offset + positions[pair["players"][0]]] = 1
        c[offset + positions[pair["players"][1]]] = -1
        for weights in W.T:
            old, _ = project(original, c, weights, estimand="shape")
            new, _ = project(altered, c, weights, estimand="shape")
            movement["requested_projections"] = max(movement["requested_projections"], abs(new - old) / original.r)
    return movement


def _joint_decision(rows, numerical_verified):
    if any(row["status"] == "failed" for row in rows):
        status = "criteria_failed"
    elif any(row["status"] == "inconclusive" for row in rows):
        status = "criteria_inconclusive"
    else:
        status = "nominate_two_band"
    if not numerical_verified:
        return dict(study_status="numerical_resolution_withheld", nomination=None,
                    criterion_decision=status, admission="not_admitted", handoff=None)
    return dict(study_status=status, nomination=ARMS[1] if status == "nominate_two_band" else None,
                criterion_decision=status, admission="not_admitted", handoff=None)


def _summaries(records):
    names = ("R_zero", "R_control", "R_candidate", "P_zero", "P_control", "P_candidate")
    result = []
    for population in POPULATIONS:
        for law in LAWS:
            selected = [row for row in records if row["population"] == population and row["law"] == law]
            means = {name: float(np.mean([row[name] for row in selected])) for name in names}
            diagnostics = {arm: {name: float(np.mean([row[arm]["regional_partition"][name] for row in selected]))
                                 for name in ("active", "inactive", "offense", "defense")}
                           for arm in ("control", "candidate")}
            scale_diagnostics = {}
            for arm, bands in (("control", ("all",)), ("candidate", ("low", "high"))):
                scale_diagnostics[arm] = {}
                for band in bands:
                    scales = [row[arm]["shape_scales"][band] for row in selected]
                    variances = [scale["selected"]["variance"] for scale in scales]
                    scale_diagnostics[arm][band] = dict(median_selected_variance=float(np.median(variances)),
                        minimum=float(min(variances)), maximum=float(max(variances)),
                        endpoint_count=sum(scale["bound_selected"] for scale in scales),
                        inherited_limitation_count=sum(scale["inherited_limitation"] for scale in scales), n=len(scales))
            result.append(dict(population=population, law=law, n=len(selected), means=means,
                differences=dict(regional_control_minus_candidate=means["R_control"] - means["R_candidate"],
                                 prediction_candidate_minus_control=means["P_candidate"] - means["P_control"]),
                diagnostics=diagnostics, scale_diagnostics=scale_diagnostics,
                false_map_regional_rms={arm: float(np.sqrt(diagnostics[arm]["inactive"])) for arm in ("control", "candidate")},
                diagnostic_meaning="year-five risks; false-map rms uses the all-thirty denominator; innovation-scale summaries include all bound selections; full paths in secondary records",
                ratios=None if population == "null" else risk_ratios(means),
                ratio_reason="null_has_no_recovery_or_retention_ratio" if population == "null" else None))
    return result


def assess(prepared, fits, output):
    from hockey_stats.attribution import read_pooling_annual, read_pooling_source, read_pooling_statistics, validate_pooling_probe
    from hockey_stats.attribution_data import pooling_population, statistic_digest

    started, process_started = time.monotonic(), time.process_time()
    prepared_path = Path(prepared).resolve(strict=True)
    source_context = read_pooling_source(prepared_path)
    document, protocol, basis, train, evaluation, W = read_prepared(prepared_path, source=source_context)
    originals, references, manifests = fit_inventory(fits, identity(prepared_path), document, protocol)
    root = output_path(str(output), [])
    require(root.is_relative_to(Path(protocol["output_root"])), "assessment output escaped the frozen study root")
    if document["purpose"] == "research":
        require(implementation() == protocol["implementation"], "assessment producer differs from frozen protocol")
    primary, secondary, probe_records, examples = [], [], [], []
    for record in originals:
        population, law, outer = (record[name] for name in ("population", "law", "outer"))
        truths = paired_truths(train, basis.p, population, outer)
        require(record["truth_sha256"] == truth_digest(truths) and record["activation_sha256"] == _activation_digest(truths)
                and record["activation"] == [truth["pairs"] for truth in truths]
                and list(record["annual"]) == list(ARMS) and all(len(record["annual"][arm]) == 5 for arm in ARMS)
                and len(record["responses"]) == 5 and len(record["losses"]) == 5, "truth or annual identity/completeness differs")
        statistics_context = read_pooling_statistics(record["statistics"]["arrays"], source_context)
        probes = record["numerical_probes"]
        expected_probes = [(year, arm) for year in (1, 5) for arm in ARMS] if outer == 0 else []
        require([(probe["year"], probe["arm"]) for probe in probes] == expected_probes
                and (record["probe_means"] is not None) == (outer == 0)
                and all(probe["population"] == population and probe["law"] == law and probe["outer"] == 0 for probe in probes),
                "bounded numerical probe source or inventory differs")
        probe_arrays = load_arrays(record["probe_means"]) if outer == 0 else {}
        expected_names = [f"year_{year}_{arm}_" + name for year in (1, 5) for arm in ARMS
                          for name in (("Theta", "A") if arm == ARMS[0] else ("low_Theta", "high_Theta", "A"))] if outer == 0 else []
        require(list(probe_arrays) == expected_names, "compact probed-mean names/order differ")
        previous_states = {arm: None for arm in ARMS}
        for year, season in enumerate(SEASONS):
            response = record["responses"][year]
            source = pooling_population(source_context, statistics_context, population, law, outer, season)
            require(response["year"] == year + 1 and response["season"] == season
                    and response["seed"] == [40604, POPULATIONS.index(population), LAWS.index(law), outer, year]
                    and response["sufficient_statistics_sha256"] == statistic_digest(source), "response seed or sufficient-statistic identity differs")
            states = []
            for arm in ARMS:
                reference = record["annual"][arm][year]
                annual = read_artifact(linked_path(reference), "attribution_pooling_annual", expected_schema=4)
                require(annual["prepared"] == identity(prepared_path) and annual["population"] == population
                        and annual["law"] == law and annual["outer"] == outer and annual["season"] == season
                        and annual["representation"] == arm and annual["response_sha256"] == response["sha256"]
                        and annual["statistics"] == record["statistics"]["arrays"], "annual arm/source/response identity differs")
                state = read_pooling_annual(reference["path"], source=source_context, previous=previous_states[arm],
                    shared_volume=(record["annual"][ARMS[0]][year], states[0]) if arm == ARMS[1] else None,
                    statistics=statistics_context)
                previous_states[arm] = (reference, state)
                states.append(state)
            losses = annual_losses(*states, source, train[year], evaluation[year], truths[year], basis, W)
            _same_losses(losses, record["losses"][year])
            if outer == 0 and year in (0, 4):
                altered = [_restored_probe(state, probe_arrays, year + 1, source) for state in states]
                altered_losses = annual_losses(*altered, source, train[year], evaluation[year], truths[year], basis, W)
                for arm, original, changed in zip(ARMS, states, altered, strict=True):
                    probe = next(probe for probe in probes if probe["year"] == year + 1 and probe["arm"] == arm)
                    validate_pooling_probe(probe, original)
                    movements = _probe_movements(original, changed, truths[year], W)
                    require(all(abs(value - probe["maximum_league_relative_current_player_movement"][name]) <= 1e-8 * (1 + abs(value))
                                for name, value in movements.items()), "probed means do not reproduce recorded movements")
                    for name in ("R_zero", "R_control", "R_candidate", "P_zero", "P_control", "P_candidate"):
                        require(abs(altered_losses[name] - probe["probed_losses"][name]) <= 1e-8 * (1 + abs(altered_losses[name])),
                                "probed means do not reproduce altered risks")
                        if name in probe["loss_movement"]:
                            movement = altered_losses[name] - losses[name]
                            require(abs(movement - probe["loss_movement"][name]) <= 1e-8 * (1 + abs(movement)),
                                    "probed risk movement does not reproduce")
            output_row = dict(population=population, law=law, outer=outer, year=year + 1, **losses)
            secondary.append(output_row)
            if year == 4:
                primary.append(output_row)
                if outer == 0:
                    examples.extend(_example_arrays(document, population, law, truths[year], states))
        probe_records.extend(probes)
    rows, substituted_rows = [], []
    for population in POPULATIONS[:2]:
        for law in LAWS:
            records = [row for row in primary if row["population"] == population and row["law"] == law]
            rows.extend(criterion_rows(records, population, law))
            selected_probes = [probe for probe in probe_records if probe["population"] == population and probe["law"] == law and probe["year"] == 5]
            require(len(selected_probes) == 2 and selected_probes[0]["probed_losses"] == selected_probes[1]["probed_losses"],
                    "final numerical probe losses differ between paired receipts")
            substituted = [dict(row, **selected_probes[0]["probed_losses"]) if row["outer"] == 0 else row for row in records]
            substituted_rows.extend(criterion_rows(substituted, population, law))
    require(len(rows) == 16 and len(probe_records) == 24
            and sum(len(probe["blocks"]) for probe in probe_records) == 36, "criterion or numerical probe inventory differs")
    classes_unchanged = all(old["status"] == new["status"] for old, new in zip(rows, substituted_rows, strict=True))
    numerical_verified = all(probe["status"] == "verified" for probe in probe_records) and classes_unchanged
    decision = _joint_decision(rows, numerical_verified)
    if document["purpose"] == "fixture_exercise":
        decision.update(study_status="fixture_exercise", nomination=None)
    summaries = _summaries(primary)
    root.mkdir()
    figure_paths = _figures(root, rows, summaries, examples, W, document["purpose"])
    consumed = dict(prepared=identity(prepared_path), protocol=document["protocol"], basis=document["basis"],
                    designs=document["designs"]["arrays"], spec_snapshot=document["spec_snapshot"],
                    **{f"fit_{i:03d}": reference for i, reference in enumerate(references)})
    assessment = artifact("attribution_pooling_assessment", document["purpose"], consumed, schema_version=4,
        prepared=identity(prepared_path), protocol=document["protocol"], fits=references,
        spec_snapshot=document["spec_snapshot"],
        execution_status="complete" if numerical_verified else "incomplete",
        records=primary, secondary=secondary, criterion_rows=rows, summaries=summaries,
        numerical=dict(status="verified" if numerical_verified else "withheld", annual_probes=24, shape_block_probes=36,
                       probes=probe_records, substituted_criterion_rows=substituted_rows, classes_unchanged=classes_unchanged),
        costs={name: sum(manifest["cost"][name] for manifest in manifests) for name in manifests[0]["cost"]},
        fit_resources=[manifest["resources"] for manifest in manifests], figures=figure_paths,
        **decision, limitations=LIMITATIONS, resources=_cost(started, process_started))
    assessment_path = root / "assessment.json"
    write_json(assessment_path, json_values(assessment))
    result = artifact("attribution_pooling_result", document["purpose"], dict(assessment=identity(assessment_path), **consumed),
        schema_version=4, execution_status=assessment["execution_status"], **decision, criterion_rows=rows,
        numerical_status=assessment["numerical"]["status"], assessment=identity(assessment_path), prepared=identity(prepared_path),
        protocol=document["protocol"], consumed_fits=references, summaries=summaries, costs=assessment["costs"],
        spec_snapshot=document["spec_snapshot"],
        limitations=LIMITATIONS, figures=figure_paths,
        monte_carlo_interval_meaning="mean risks over fresh physical truths and training responses, conditional on fixed designs and references; no player interval calibration",
        resources=_cost(started, process_started))
    result_path = root / "result.json"
    write_json(result_path, json_values(result))
    _decision_text(root, result)
    return identity(result_path)


def _example_arrays(document, population, law, truth, states):
    from hockey_stats.attribution import shape_mean

    result = []
    for example in document["examples"]:
        if example["population"] != population:
            continue
        actual = next(pair for pair in truth["pairs"] if pair["team"] == example["team"]
                      and pair["role"] == example["role"] and pair["pair"] == example["pair"])
        require(all(actual[name] == example[name] for name in actual), "frozen example no longer matches activation/roster")
        state = states[0]
        positions = {player: i for i, player in enumerate(state.player_ids)}
        current = {player: i for i, player in enumerate(state.current_player_ids)}
        c, c_current = np.zeros(2 * len(positions)), np.zeros(2 * len(current))
        role = int(example["role"] == "defense")
        for player, coefficient in zip(example["players"], (1, -1), strict=True):
            c[role * len(positions) + positions[player]] = coefficient
            c_current[role * len(current) + current[player]] = coefficient
        result.append(dict(name=example["name"], law=law, population=population, players=example["players"],
            evidence="estimable" if example["expected_estimable"] else "unsupported prior allocation; not estimable",
            truth=40 * c_current @ truth["centered"], control=40 * c @ shape_mean(states[0]),
            candidate=40 * c @ shape_mean(states[1]),
            low=40 * c @ states[1].shape.low.Theta @ states[1].basis.R[:, :11].T,
            high=40 * c @ states[1].shape.high.Theta @ states[1].basis.R[:, 11:].T))
    return result


def _figures(output, rows, summaries, examples, W, purpose):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    title_prefix = "fixture exercise — " if purpose == "fixture_exercise" else ""
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    figure = plt.figure(figsize=(15, 17), constrained_layout=True)
    layout = figure.add_gridspec(4, 2, height_ratios=[2, 2, 1.5, 1.5])
    colors = dict(supported="#24724b", failed="#b23a3d", inconclusive="#8b6914")
    criterion_titles = (
        ("regional_recovery_25pct", "at least 25% lower regional error than zero"),
        ("regional_improvement", "supported regional improvement over control"),
        ("positive_control_prediction_gain", "positive control prediction gain"),
        ("prediction_gain_retention_99pct", "retain at least 99% of control prediction gain"),
    )
    for panel, (criterion, title) in enumerate(criterion_titles):
        axes = figure.add_subplot(layout[panel // 2, panel % 2])
        selected = [row for row in rows if row["criterion"] == criterion]
        for i, row in enumerate(selected):
            axes.plot([row["lower"], row["upper"]], [i, i], color=colors[row["status"]], linewidth=2)
            axes.plot(row["mean"], i, "o", color=colors[row["status"]], markersize=4)
            axes.annotate(f"[{row['lower']:.4g}, {row['upper']:.4g}]", (row["upper"], i),
                          xytext=(4, 0), textcoords="offset points", va="center", fontsize=7)
        axes.axvline(0, color="#777777", linewidth=.8)
        axes.set_yticks(range(len(selected)), [f"{row['population']} / {row['law']}" for row in selected])
        axes.invert_yaxis()
        axes.margins(x=.35, y=.08)
        axes.set_xlabel("criterion contrast; squared attempts per 60 team minutes")
        axes.set_title(title)
    axes = figure.add_subplot(layout[2, :])
    axes.axis("off")
    cells = []
    for summary in summaries:
        means = summary["means"]
        cells.append([summary["population"], summary["law"], str(summary["n"]),
            f"{means['R_zero']:.5g}", f"{means['R_control']:.5g}", f"{means['R_candidate']:.5g}",
            f"{summary['diagnostics']['control']['inactive']:.5g}", f"{summary['diagnostics']['candidate']['inactive']:.5g}",
            f"{means['P_zero']:.5g}", f"{means['P_control']:.5g}", f"{means['P_candidate']:.5g}"])
    table = axes.table(cellText=cells, colLabels=["population", "noise", "n", "regional\nzero", "regional\ncontrol", "regional\ncandidate",
        "inactive\ncontrol", "inactive\ncandidate", "prediction\nzero", "prediction\ncontrol", "prediction\ncandidate"],
        loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 2.2)
    axes.set_title("adjacent diagnostics: absolute risks; inactive terms use the same /30 denominator; null has no ratio or gate", pad=12)
    axes = figure.add_subplot(layout[3, :])
    axes.axis("off")
    cells = []
    for summary in summaries:
        scales = [summary["scale_diagnostics"][arm][band] for arm, band in
                  (("control", "all"), ("candidate", "low"), ("candidate", "high"))]
        cells.append([summary["population"], summary["law"],
            f"{summary['false_map_regional_rms']['control']:.4g}", f"{summary['false_map_regional_rms']['candidate']:.4g}",
            *[f"{scale['median_selected_variance']:.4g}" for scale in scales],
            " / ".join(str(scale["endpoint_count"]) for scale in scales)])
    table = axes.table(cellText=cells, colLabels=["population", "noise", "false-map rms\ncontrol", "false-map rms\ncandidate",
        "median q\ncontrol", "median q\nlow", "median q\nhigh", "bound counts\ncontrol / low / high"], loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 2.2)
    axes.set_title("false-map magnitudes and pooling: year-five innovation variances; all bounds retained; full five-year paths in assessment", pad=12)
    figure.suptitle(title_prefix + "recovery and prediction cost\npaired 95% monte carlo intervals; fixed deployment/reference scope; no player interval calibration\ngreen: supported; red: failed; ochre: inconclusive", fontsize=13)
    first = output / "recovery-prediction-cost.png"
    figure.savefig(first, dpi=160, bbox_inches="tight", pad_inches=.15)
    plt.close(figure)
    order = ["sparse_team0_offense_first_active", "sparse_team0_offense_first_inactive",
             "diffuse_team0_defense_first_pair", "diffuse_team3_offense_inseparable"]
    examples = sorted(examples, key=lambda example: (order.index(example["name"]), LAWS.index(example["law"])))
    require(len(examples) == 8, "frozen spatial example inventory differs")
    figure, axes = plt.subplots(8, 4, figsize=(17, 23), constrained_layout=True)
    centers = grid()[0]
    maximum = max(float(np.max(np.abs(example[name]))) for example in examples for name in ("truth", "control", "candidate"))
    region_max = max(float(np.max(np.abs(example[name] @ W))) for example in examples for name in ("truth", "control", "candidate", "low", "high"))
    for row, example in enumerate(examples):
        for column, name in enumerate(("truth", "control", "candidate")):
            colored = axes[row, column].scatter(centers[:, 0], centers[:, 1], c=example[name], s=18, marker="s", cmap="RdBu_r", vmin=-maximum, vmax=maximum)
            axes[row, column].set(xlim=(-100, 100), ylim=(-43, 43), aspect="equal", xticks=[-100, 0, 100], yticks=[-40, 0, 40])
            axes[row, column].set_title(name if row == 0 else "", fontsize=11)
        description = example["name"].replace("_", " ") + f"\n{example['players'][0]} − {example['players'][1]} / {example['law']}\n{example['evidence']}"
        axes[row, 0].set_ylabel(description, fontsize=8)
        regional = axes[row, 3]
        for name, color, linestyle in (("truth", "#222222", "-"), ("control", "#3678a6", "-"),
                                       ("candidate", "#d27722", "-"), ("low", "#24724b", "--"), ("high", "#9254a8", ":")):
            regional.plot(np.arange(12), example[name] @ W, label=name, color=color, linestyle=linestyle, linewidth=1.1)
        regional.axhline(0, color="#999999", linewidth=.6)
        regional.set(ylim=(-region_max * 1.1, region_max * 1.1), xticks=np.arange(.5, 12, 2),
                     xticklabels=["behind", "outside", "0–10", "10–20", "20–40", "40+"],
                     xlabel="regions; each pair: negative / positive y")
        regional.tick_params(axis="x", labelsize=6)
        if row == 0:
            regional.set_title("regional contrasts / candidate bands")
            regional.legend(ncol=3, fontsize=7)
    figure.colorbar(colored, ax=axes[:, :3], location="bottom", shrink=.5, aspect=60,
                    label="signed attempts per 60 team minutes per native cell; defense is allowed-attempt sign")
    figure.suptitle(title_prefix + f"spatial changes: year 5, outer 0; activation-selected examples\ncommon native scale ±{maximum:.4g} attempts/60 per cell; regional scale shared; native pixels do not imply native precision", fontsize=13)
    second = output / "spatial-changes.png"
    figure.savefig(second, dpi=150, bbox_inches="tight", pad_inches=.15)
    plt.close(figure)
    arrays = write_arrays(output, "spatial-examples.npz", {f"example_{i}_{name}": example[name]
        for i, example in enumerate(examples) for name in ("truth", "control", "candidate", "low", "high")})
    return dict(recovery_prediction=identity(first), spatial_changes=identity(second), spatial_examples=arrays,
                example_order=[{key: example[key] for key in ("name", "law", "population", "players", "evidence")} for example in examples],
                units="attempts per 60 team minutes; defense retains allowed-attempt sign")


def _decision_text(output, result):
    rows = result["criterion_rows"]
    text = f"# 04e — two spatial pooling bands\n\nexecution: {result['execution_status']}. study: **{result['study_status']}**. "
    text += f"nomination: {result['nomination'] or 'none'}. admission: not_admitted. handoff: null.\n\n"
    if result["purpose"] == "fixture_exercise":
        text += "this is a detached fixture exercise. it cannot satisfy research acceptance or support scientific nomination.\n\n"
    text += "the claim concerns mean regional recovery and fresh-deployment shape prediction under fixed synthetic deployment/reference conditions. "
    text += "all 30 estimable pairs count; inactive false maps consume the same error budget. the two inseparable role contrasts remain unsupported. "
    text += "monte carlo intervals concern mean risks over varying truths and training responses, not individual-player uncertainty.\n\n"
    text += "[primary table](primary-table.md) · [recovery and prediction cost](recovery-prediction-cost.png) · [spatial changes](spatial-changes.png)\n\n"
    text += "null and inactive-pair risks qualify interpretation without a retrospective null veto. "
    text += "a better pooling rule cannot create information absent from co-deployment.\n\n"
    for summary in result["summaries"]:
        if summary["population"] != "null":
            continue
        means = summary["means"]
        text += f"null {summary['law']}: regional error is {means['R_control']:.6g} for control and {means['R_candidate']:.6g} for candidate; "
        text += f"prediction error is {means['P_control']:.6g} and {means['P_candidate']:.6g}. "
        text += "these absolute errors qualify the conclusion and have no ratio or nomination gate.\n\n"
    text += "secondary assessment records retain years one through four, transition-event labels, actual/projected truth comparisons, scale paths, native/complete-rate error and negative fitted rates.\n\n"
    text += "tradeoffs: " + "; ".join(LIMITATIONS) + ".\n"
    with (output / "decision.md").open("x") as destination:
        destination.write(text)
    table = "| population | law | criterion / diagnostic | mean / control | lower / candidate | upper | status |\n|---|---|---|---:|---:|---:|---|\n"
    for row in rows:
        table += f"| {row['population']} | {row['law']} | {row['criterion']} | {row['mean']:.8g} | {row['lower']:.8g} | {row['upper']:.8g} | {row['status']} |\n"
    for summary in result["summaries"]:
        table += f"| {summary['population']} | {summary['law']} | inactive regional risk (/30) | {summary['diagnostics']['control']['inactive']:.8g} | {summary['diagnostics']['candidate']['inactive']:.8g} | — | diagnostic |\n"
        table += f"| {summary['population']} | {summary['law']} | false-map regional rms (/30) | {summary['false_map_regional_rms']['control']:.8g} | {summary['false_map_regional_rms']['candidate']:.8g} | — | diagnostic |\n"
        scales = [summary["scale_diagnostics"][arm][band] for arm, band in
                  (("control", "all"), ("candidate", "low"), ("candidate", "high"))]
        table += f"| {summary['population']} | {summary['law']} | median year-five innovation variance | {scales[0]['median_selected_variance']:.8g} | low {scales[1]['median_selected_variance']:.8g}; high {scales[2]['median_selected_variance']:.8g} | — | diagnostic |\n"
        table += f"| {summary['population']} | {summary['law']} | bound-selection counts | {scales[0]['endpoint_count']} | low {scales[1]['endpoint_count']}; high {scales[2]['endpoint_count']} | — | diagnostic |\n"
        if summary["population"] == "null":
            for risk in ("R", "P"):
                table += f"| null | {summary['law']} | absolute {risk} risk; no ratio/gate | {summary['means'][risk + '_control']:.8g} | {summary['means'][risk + '_candidate']:.8g} | — | diagnostic |\n"
    with (output / "primary-table.md").open("x") as destination:
        destination.write(table)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--purpose", required=True, choices=("research", "fixture_exercise"))
    prepare_parser.add_argument("--output", required=True)
    fit_parser = commands.add_parser("fit")
    fit_parser.add_argument("--prepared", required=True)
    fit_parser.add_argument("--population", required=True, choices=POPULATIONS)
    fit_parser.add_argument("--law", required=True, choices=LAWS)
    fit_parser.add_argument("--start", required=True, type=int)
    fit_parser.add_argument("--stop", required=True, type=int)
    fit_parser.add_argument("--output", required=True)
    assess_parser = commands.add_parser("assess")
    assess_parser.add_argument("--prepared", required=True)
    assess_parser.add_argument("--fits", required=True, nargs="+")
    assess_parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            reference = prepare(args.purpose, args.output)
        elif args.command == "fit":
            reference = fit(args.prepared, args.population, args.law, args.start, args.stop, args.output)
        else:
            reference = assess(args.prepared, args.fits, args.output)
        print(json.dumps(json_values(reference)))
        return 0
    except (InputContractError, OSError, KeyError, TypeError, ValueError, np.linalg.LinAlgError, FloatingPointError) as error:
        print("incomplete execution: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
