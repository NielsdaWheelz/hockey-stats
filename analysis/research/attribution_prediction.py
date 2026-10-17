"""04f's bounded diagnosis of saved attribution prediction errors."""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys
import time

for _thread in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_thread] = "1"

import numpy as np

from hockey_stats.artifacts import (
    artifact, clean_implementation, digest, implementation, json_values, linked_path,
    read_artifact, require, resources, write_json,
)
from hockey_stats.attribution import (
    PoolingSource, ShapeBasis, read_pooling_annual, read_pooling_source, read_pooling_statistics, shape_mean,
)
from hockey_stats.attribution_data import pooling_population, statistic_digest
from hockey_stats.attribution_prediction import (
    current_player_rows, deployment_gram, excess_prediction_terms, prediction_inner, prediction_loss,
)
from hockey_stats.attribution_simulation import paired_truths, truth_digest
from hockey_stats.captures import InputContractError
from hockey_stats.chance_cli import identity, output_path, read_json
from attribution_pooling import (
    ARMS, LAWS, POPULATIONS, SEASONS, _activation_digest, fit_inventory,
    read_prepared,
)

SPEC = Path(__file__).resolve().parents[2] / "docs/specs/04f-attribution-prediction.md"
SOURCE_ROOT = Path("/Volumes/Expansion/hockey-stats/runs/attribution-04e-20261016")
SOURCE_RESULT_SHA256 = "b2b1b2225221bc3297556229ca6fb548c78494f7cc843ba90cb3e3f28e006c32"


@dataclass(frozen=True)
class PredictionSource:
    reference: dict
    result: dict
    context: PoolingSource
    prepared: dict
    protocol: dict
    basis: ShapeBasis
    training: list
    evaluation: list
    W: np.ndarray
    records: list[dict]
    consumed: dict
    input_roots: tuple[str, ...]
    inventory: dict


def read_source(source_result: Path | str) -> PredictionSource:
    """bind the original compact result and its exact source inventory; write nothing."""
    source_result = Path(source_result).resolve(strict=True)
    reference = identity(source_result)
    require(reference["sha256"] == SOURCE_RESULT_SHA256, "04f requires the exact committed 04e result")
    # read_artifact hashes its bound assessment without parsing the historical tree.
    result = read_artifact(source_result, "attribution_pooling_result", expected_schema=4)
    require(result["purpose"] == "research" and result["execution_status"] == "complete"
            and result["numerical_status"] == "verified" and result["study_status"] == "criteria_failed"
            and result["criterion_decision"] == "criteria_failed" and result["nomination"] is None
            and result["admission"] == "not_admitted" and result["handoff"] is None,
            "04e must retain its complete, verified, failed and unadmitted verdict")
    prepared_path = linked_path(result["prepared"])
    context = read_pooling_source(prepared_path)
    prepared, protocol, basis, training, evaluation, W = read_prepared(prepared_path, source=context)
    fits = result["consumed_fits"]
    parents = dict(assessment=result["assessment"], prepared=context.reference, protocol=prepared["protocol"],
                   basis=prepared["basis"], designs=prepared["designs"]["arrays"],
                   spec_snapshot=prepared["spec_snapshot"])
    expected = dict(**parents, **{f"fit_{i:03d}": value for i, value in enumerate(fits)})
    require(len(fits) == 7 and result["consumed"] == expected
            and result["prepared"] == context.reference and result["protocol"] == prepared["protocol"]
            and result["spec_snapshot"] == prepared["spec_snapshot"]
            and result["implementation"] == protocol["implementation"]
            and Path(protocol["output_root"]) == SOURCE_ROOT
            and all(Path(value["path"]).is_relative_to(SOURCE_ROOT)
                    for name, value in parents.items() if name != "basis")
            and all(Path(value["path"]).is_relative_to(SOURCE_ROOT) for value in fits),
            "04e result parents, producer, seven manifests or frozen root differ")

    original_parents = {name: protocol[name] for name in ("original_protocol", "original_result", "original_prepared")}
    require(protocol["consumed"] == dict(**original_parents, basis=prepared["basis"],
                                         spec_snapshot=prepared["spec_snapshot"]),
            "04e inherited parent bindings differ")
    old_protocol = read_artifact(linked_path(original_parents["original_protocol"]), "attribution_recovery_protocol")
    old_result = read_artifact(linked_path(original_parents["original_result"]), "attribution_recovery_result")
    old_prepared = read_artifact(linked_path(original_parents["original_prepared"]), "attribution_recovery_prepared")
    require(old_result["model_protocol"] == old_prepared["model_protocol"] == original_parents["original_protocol"]
            and old_result["evidence"]["prepared"] == old_result["consumed"]["prepared"] == original_parents["original_prepared"]
            and old_prepared["basis"] == prepared["basis"]
            and old_prepared["basis_sha256"] == prepared["basis_sha256"]
            and old_prepared["basis_shapes"] == prepared["basis_shapes"]
            and old_prepared["source_prepared"] == old_protocol["source_prepared"]
            and old_prepared["source_protocol"] == old_protocol["source_protocol"]
            and old_result["model_implementation"] == old_prepared["implementation"] == old_protocol["implementation"]
            and old_result["completion"] == "complete", "inherited 04c geometry/protocol/result chain differs")
    originals, fit_references, manifests = fit_inventory(
        [linked_path(value) for value in fits], context.reference, prepared, protocol)
    costs = dict(datasets=1200, histories=2400, annual_states=12000, volume_updates=6000, shape_updates=18000)
    require(fit_references == fits and result["costs"] == costs
            and all(sum(manifest["cost"][name] for manifest in manifests) == value for name, value in costs.items()),
            "04e compact result and fitted inventory costs differ")
    annual_paths, statistics_paths = [], []
    for record in originals:
        require(list(record["annual"]) == list(ARMS)
                and all(len(record["annual"][arm]) == len(SEASONS) for arm in ARMS)
                and len(record["responses"]) == len(record["losses"]) == len(SEASONS),
                "original annual, response or loss inventory is incomplete")
        statistics_paths.append(record["statistics"]["arrays"]["path"])
        annual_paths.extend(value["path"] for arm in ARMS for value in record["annual"][arm])
    require(len(originals) == len(statistics_paths) == len(set(statistics_paths)) == 1200
            and len(annual_paths) == len(set(annual_paths)) == 12000,
            "04f requires 1,200 distinct datasets and 12,000 distinct original annual states")
    consumed = dict(source_result=reference, **parents,
                    **{f"fit_{i:03d}": value for i, value in enumerate(fits)},
                    **{"04c_" + name: value for name, value in original_parents.items()})
    original_root = Path(original_parents["original_protocol"]["path"]).parents[1]
    input_roots = tuple(sorted({str(SOURCE_ROOT), str(original_root),
                               *(str(Path(value["path"]).parent) for value in consumed.values())}))
    inventory = dict(datasets=1200, annual_states=12000, final_states=2400, statistics_archives=1200, fit_manifests=7)
    return PredictionSource(reference, result, context, prepared, protocol, basis, training, evaluation, W,
                            originals, consumed, input_roots, inventory)


def iter_final_states(source: PredictionSource):
    """validate chronological original histories, yielding only the paired year-five states."""
    datasets, annual_states = 0, 0
    for record in source.records:
        population, law, outer = (record[name] for name in ("population", "law", "outer"))
        truths = paired_truths(source.training, source.basis.p, population, outer)
        require(record["truth_sha256"] == truth_digest(truths)
                and record["activation_sha256"] == _activation_digest(truths)
                and record["activation"] == [truth["pairs"] for truth in truths],
                "original truth or activation digests differ from the frozen seeds")
        statistics = read_pooling_statistics(record["statistics"]["arrays"], source.context)
        require(record["statistics"]["array_shapes"] == [dict(name=name, shape=list(value.shape), dtype=value.dtype.str)
                for name, value in statistics.arrays.items()], "statistic archive shape metadata differs")
        previous_states = {arm: None for arm in ARMS}
        for year, season in enumerate(SEASONS):
            response = record["responses"][year]
            annual_population = pooling_population(source.context, statistics, population, law, outer, season)
            digest(response["sha256"])
            require(response["year"] == year + 1 and response["season"] == season
                    and response["seed"] == [40604, POPULATIONS.index(population), LAWS.index(law), outer, year]
                    and response["sufficient_statistics_sha256"] == statistic_digest(annual_population),
                    "response seed or original sufficient-statistic lineage differs")
            states = {}
            for arm in ARMS:
                reference = record["annual"][arm][year]
                annual_path = linked_path(reference)
                annual = read_json(annual_path)
                require(annual["prepared"] == source.context.reference and annual["population"] == population
                        and annual["law"] == law and annual["outer"] == outer and annual["season"] == season
                        and annual["representation"] == arm and annual["response_sha256"] == response["sha256"]
                        and annual["statistics"] == statistics.reference,
                        "annual arm, source, response or statistic identity differs")
                state = read_pooling_annual(annual_path, source=source.context, previous=previous_states[arm],
                    shared_volume=(record["annual"][ARMS[0]][year], states[ARMS[0]]) if arm == ARMS[1] else None,
                    statistics=statistics)
                previous_states[arm] = (reference, state)
                states[arm] = state
                annual_states += 1
        datasets += 1
        yield record, annual_population, truths[-1], states
    require(datasets == source.inventory["datasets"] and annual_states == source.inventory["annual_states"],
            "completed source traversal differs from the frozen 1,200/12,000 inventory")


BANDS = ("low", "high", "omitted")
PARTS = ("test", "rest")


def _reconcile(actual, expected, label, residuals):
    actual, expected = np.asarray(actual), np.asarray(expected)
    require(actual.shape == expected.shape and np.isfinite(actual).all() and np.isfinite(expected).all()
            and np.all(np.abs(actual - expected) <= 1e-8 * (1 + np.abs(expected))),
            "04f reconciliation failed: " + label)
    residuals[label] = float(np.max(np.abs(actual - expected), initial=0.))


def _spatial_parts(values, basis):
    low = (values @ basis.B[:, :11]) @ basis.R[:, :11].T
    high = (values @ basis.B[:, 11:]) @ basis.R[:, 11:].T
    return dict(low=low, high=high,
                omitted=values - values.sum(axis=1, keepdims=True) * basis.p - low - high)


def _verify_spatial_parts(values, parts, basis, label, residuals):
    _reconcile(sum(parts.values()), values, label + "_projection_reconstruction", residuals)
    for band in BANDS:
        _reconcile(parts[band].sum(axis=1), np.zeros(len(values)), label + "_" + band + "_zero_sum", residuals)
    for left, right in (("low", "high"), ("low", "omitted"), ("high", "omitted")):
        cross = np.sum(parts[left] * parts[right] / basis.p, axis=1)
        _reconcile(cross, np.zeros(len(values)), label + "_" + left + "_" + right + "_metric_orthogonality", residuals)
    _reconcile(parts["omitted"] @ basis.B, np.zeros((len(values), 40)), label + "_omitted_projection", residuals)


def _pair_design(truth, players, residuals):
    positions = {player: i for i, player in enumerate(players)}
    C, inseparable, active, roles = [], [], [], []
    require(len(players) == 32 and len(truth["pairs"]) == 32, "04f requires the frozen thirty-two current players/pairs")
    for pair in truth["pairs"]:
        contrast = np.zeros(64)
        offset = 32 if pair["role"] == "defense" else 0
        contrast[offset + positions[pair["players"][0]]] = 1
        contrast[offset + positions[pair["players"][1]]] = -1
        if pair["expected_estimable"]:
            C.append(contrast)
            active.append(pair["active"])
            roles.append(pair["role"])
        else:
            require(pair["players"] == [26, 31], "04f unsupported pair differs from the frozen inseparable contrast")
            inseparable.append(contrast)
    C, inseparable = np.array(C), np.array(inseparable)
    require(C.shape == (30, 64) and inseparable.shape == (2, 64), "04f scored-pair inventory differs")
    J = .5 * C.T @ C
    _reconcile(C @ C.T, 2 * np.eye(30), "pair_disjointness", residuals)
    _reconcile(C @ J, C, "pair_test_projection", residuals)
    _reconcile(C @ (np.eye(64) - J), np.zeros_like(C), "pair_rest_projection", residuals)
    return C, inseparable, np.asarray(active, dtype=bool), np.asarray(roles)


def diagnose_record(states, population, training, evaluation, truth, basis, W, gram, *, direct=False):
    """year-five known-mean risks; no response generation, fitting or historical risks."""
    residuals = {}
    p, xbar, true_maps = basis.p, population.xbar, truth["centered"]
    yh = population.ybar - population.ybar.sum(axis=1, keepdims=True) * p
    noise_context = yh - truth["context"] - xbar @ true_maps
    C, inseparable, active, roles = _pair_design(truth, training["players"], residuals)
    require(basis.B.shape == (656, 40) and W.shape == (656, 12)
            and true_maps.shape == (64, 656) and list(states) == list(ARMS), "04f final-state or spatial dimensions differ")
    _reconcile(p @ basis.B, np.zeros(40), "basis_reference_centering", residuals)
    _reconcile(basis.B.T @ basis.R, np.eye(40), "basis_metric_orthogonality", residuals)
    _reconcile(np.sum(basis.R, axis=0), np.zeros(40), "basis_shape_zero_sum", residuals)
    _reconcile(xbar[:, :32].sum(axis=1), np.full(len(xbar), 5.), "training_offense_reference", residuals)
    _reconcile(xbar[:, 32:].sum(axis=1), np.full(len(xbar), 5.), "training_defense_reference", residuals)
    role_vectors = np.zeros((len(xbar) + 64, 2))
    role_vectors[:len(xbar)] = -5
    role_vectors[len(xbar):len(xbar) + 32, 0] = 1
    role_vectors[len(xbar) + 32:, 1] = 1
    _reconcile(gram @ role_vectors, np.zeros_like(role_vectors), "same_role_reference_shift_invariance", residuals)
    unsupported = np.vstack((-xbar @ inseparable.T, inseparable.T))
    _reconcile(gram @ unsupported, np.zeros_like(unsupported), "inseparable_evaluated_contribution", residuals)
    for name, values in (("truth", true_maps), ("source_mean", yh), ("noise", noise_context)):
        _reconcile(values.sum(axis=1), np.zeros(len(values)), name + "_zero_sum", residuals)
    noise = np.vstack((noise_context, np.zeros_like(true_maps)))
    true_correction = np.vstack((-xbar @ true_maps, true_maps))
    noise_energy = prediction_inner(gram, noise, noise, p=p)
    truth_coupling = 2 * prediction_inner(gram, noise, true_correction, p=p)
    true_bands, noise_bands = _spatial_parts(true_maps, basis), _spatial_parts(noise_context, basis)
    _verify_spatial_parts(true_maps, true_bands, basis, "truth", residuals)
    _verify_spatial_parts(noise_context, noise_bands, basis, "noise", residuals)
    true_pairs = C @ true_maps
    true_regions = 40 * true_pairs @ W
    zero_errors = np.sum(true_regions ** 2, axis=1)
    risks = dict(R_zero=float(zero_errors.sum() / 30),
                 P_zero=prediction_loss(gram, yh - truth["context"], -true_maps, p=p))
    zero_partition = dict(active=float(zero_errors[active].sum() / 30),
                          inactive=float(zero_errors[~active].sum() / 30),
                          offense=float(zero_errors[roles == "offense"].sum() / 30),
                          defense=float(zero_errors[roles == "defense"].sum() / 30))
    record = dict(risks=risks, reconstructed_risks={}, zero_regional_partition=zero_partition,
                  native_pair_zero=float(40 ** 2 / 30 * np.sum(true_pairs ** 2 / p)), arms={}, residuals=residuals,
                  pair_counts=dict(scored=30, active=int(active.sum()), inactive=int((~active).sum()), inseparable=2),
                  direct_verified=bool(direct))
    maps_by_arm = {}
    for label, arm in zip(("control", "candidate"), ARMS, strict=True):
        state = states[arm]
        maps = shape_mean(state)[current_player_rows(state, training["players"])]
        maps_by_arm[arm] = maps
        _reconcile(maps.sum(axis=1), np.zeros(64), arm + "_zero_sum", residuals)
        _reconcile(state.shape.A, yh - xbar @ maps, arm + "_saved_context", residuals)
        aggregate = dict(noise=noise_energy, truth_coupling=truth_coupling,
                         **excess_prediction_terms(gram, xbar, noise_context, true_maps, maps, p=p))
        pair_error = C @ (maps - true_maps)
        regional_errors = np.sum((40 * pair_error @ W) ** 2, axis=1)
        partition = dict(active=float(regional_errors[active].sum() / 30),
                         inactive=float(regional_errors[~active].sum() / 30),
                         offense=float(regional_errors[roles == "offense"].sum() / 30),
                         defense=float(regional_errors[roles == "defense"].sum() / 30))
        risks["R_" + label] = float(regional_errors.sum() / 30)
        risks["P_" + label] = prediction_loss(gram, state.shape.A - truth["context"], maps - true_maps, p=p)
        reconstructed = noise_energy + aggregate["error"] + aggregate["coupling"] - truth_coupling
        record["reconstructed_risks"]["P_" + label] = reconstructed
        _reconcile(reconstructed, risks["P_" + label], arm + "_prediction_reconstruction", residuals)
        _reconcile(aggregate["delta"], risks["P_" + label] - risks["P_zero"], arm + "_signed_excess", residuals)
        fitted_bands = _spatial_parts(maps, basis)
        _verify_spatial_parts(maps, fitted_bands, basis, arm, residuals)
        _reconcile(fitted_bands["omitted"], np.zeros_like(maps), arm + "_omitted_fitted_correction", residuals)
        joint = {}
        for band in BANDS:
            fitted, actual, b = fitted_bands[band], true_bands[band], noise_bands[band]
            fitted_test, actual_test = .5 * C.T @ (C @ fitted), .5 * C.T @ (C @ actual)
            n = np.vstack((b, np.zeros_like(maps)))
            components, corrections = {}, {}
            for part, v, t in (("test", fitted_test, actual_test),
                               ("rest", fitted - fitted_test, actual - actual_test)):
                vc, tc = np.vstack((-xbar @ v, v)), np.vstack((-xbar @ t, t))
                h = vc - tc
                E = prediction_inner(gram, h, h, p=p)
                S = prediction_inner(gram, tc, tc, p=p)
                I = 2 * prediction_inner(gram, n, vc, p=p)
                components[part] = dict(E=E, S=S, I=I, delta=E - S + I)
                corrections[part] = (h, tc)
            E_cross = 2 * prediction_inner(gram, corrections["test"][0], corrections["rest"][0], p=p)
            S_cross = 2 * prediction_inner(gram, corrections["test"][1], corrections["rest"][1], p=p)
            components["cross"] = dict(E=E_cross, S=S_cross, delta=E_cross - S_cross)
            components["delta"] = components["test"]["delta"] + components["rest"]["delta"] + E_cross - S_cross
            components["noise"] = prediction_inner(gram, n, n, p=p)
            t = np.vstack((-xbar @ actual, actual))
            v = np.vstack((-xbar @ fitted, fitted))
            components["P_zero"] = prediction_inner(gram, n - t, n - t, p=p)
            components["P_arm"] = prediction_inner(gram, n + v - t, n + v - t, p=p)
            _reconcile(components["delta"], components["P_arm"] - components["P_zero"],
                       arm + "_" + band + "_signed_excess", residuals)
            if band == "omitted":
                for part in PARTS:
                    _reconcile(components[part]["E"], components[part]["S"], arm + "_omitted_" + part + "_error_signal", residuals)
                    _reconcile(components[part]["I"], 0., arm + "_omitted_" + part + "_coupling", residuals)
                _reconcile(E_cross, S_cross, arm + "_omitted_cross_error_signal", residuals)
                _reconcile(components["delta"], 0., arm + "_omitted_cancellation", residuals)
            joint[band] = components
        for name, term in (("noise", "noise"), ("P_zero", "P_zero"), ("P_arm", "P_" + label), ("delta", "delta")):
            expected = aggregate[term] if term in aggregate else risks[term]
            _reconcile(sum(joint[band][name] for band in BANDS), expected, arm + "_spatial_" + name, residuals)
        for letter, name in (("E", "error"), ("S", "signal"), ("I", "coupling")):
            actual = sum(sum(joint[band][part][letter] for part in PARTS)
                         + (joint[band]["cross"][letter] if letter != "I" else 0.) for band in BANDS)
            _reconcile(actual, aggregate[name], arm + "_joint_" + name, residuals)
        record["arms"][arm] = dict(aggregate=aggregate, joint=joint, regional_partition=partition,
            native_pair_risk=float(40 ** 2 / 30 * np.sum(pair_error ** 2 / p)))
    record["reconstructed_risks"]["P_zero"] = noise_energy + record["arms"][ARMS[0]]["aggregate"]["signal"] - truth_coupling
    _reconcile(record["reconstructed_risks"]["P_zero"], risks["P_zero"], "baseline_prediction_reconstruction", residuals)
    record["reconstructed_risks"].update({name: risks[name] for name in ("R_zero", "R_control", "R_candidate")})
    if direct:
        _verify_direct_rows(record, evaluation, population, truth, basis, C, maps_by_arm, states)
    return record


def _verify_direct_rows(record, evaluation, population, truth, basis, C, maps_by_arm, states):
    """independent exposure-row contractions for the frozen first/last draws."""
    p, xbar, true_maps = basis.p, population.xbar, truth["centered"]
    yh = population.ybar - population.ybar.sum(axis=1, keepdims=True) * p
    b = yh - truth["context"] - xbar @ true_maps
    totals = {arm: dict(aggregate={name: 0. for name in record["arms"][arm]["aggregate"]},
                       joint={band: {part: {name: 0. for name in record["arms"][arm]["joint"][band][part]}
                                              for part in (*PARTS, "cross")} | dict(delta=0., noise=0., P_zero=0., P_arm=0.)
                              for band in BANDS}, P_zero=0., P_arm=0.) for arm in ARMS}
    scale = 40 ** 2 / evaluation["e"].sum()
    for start in range(0, len(evaluation["e"]), 256):
        X = evaluation["X"][start:start + 256]
        si, weights = evaluation["si"][start:start + 256], evaluation["e"][start:start + 256]
        z = X.toarray() - xbar[si]
        noise, t = b[si], z @ true_maps
        z_test = .5 * z @ C.T
        tb, nb = _spatial_parts(t, basis), _spatial_parts(noise, basis)
        tt = _spatial_parts(z_test @ (C @ true_maps), basis)
        def inner(left, right):
            return scale * float(np.sum(weights[:, None] * left * right / p))
        for arm in ARMS:
            v = z @ maps_by_arm[arm]
            h = v - t
            a = totals[arm]["aggregate"]
            a["noise"] += inner(noise, noise)
            a["truth_coupling"] += 2 * inner(noise, t)
            a["error"] += inner(h, h)
            a["signal"] += inner(t, t)
            a["coupling"] += 2 * inner(noise, v)
            a["delta"] += inner(h, h) - inner(t, t) + 2 * inner(noise, v)
            baseline = yh[si] - truth["context"] - X @ true_maps
            fitted = states[arm].shape.A[si] - truth["context"] + X @ (maps_by_arm[arm] - true_maps)
            totals[arm]["P_zero"] += inner(baseline, baseline)
            totals[arm]["P_arm"] += inner(fitted, fitted)
            vb = _spatial_parts(v, basis)
            vt = _spatial_parts(z_test @ (C @ maps_by_arm[arm]), basis)
            for band in BANDS:
                k = totals[arm]["joint"][band]
                errors, signals, deltas = {}, {}, []
                for part, vp, tp in (("test", vt[band], tt[band]),
                                      ("rest", vb[band] - vt[band], tb[band] - tt[band])):
                    hp = vp - tp
                    E, S, I = inner(hp, hp), inner(tp, tp), 2 * inner(nb[band], vp)
                    for name, value in (("E", E), ("S", S), ("I", I), ("delta", E - S + I)):
                        k[part][name] += value
                    errors[part], signals[part] = hp, tp
                    deltas.append(E - S + I)
                ec, sc = 2 * inner(errors["test"], errors["rest"]), 2 * inner(signals["test"], signals["rest"])
                for name, value in (("E", ec), ("S", sc), ("delta", ec - sc)):
                    k["cross"][name] += value
                k["delta"] += sum(deltas) + ec - sc
                k["noise"] += inner(nb[band], nb[band])
                k["P_zero"] += inner(nb[band] - tb[band], nb[band] - tb[band])
                k["P_arm"] += inner(nb[band] + vb[band] - tb[band], nb[band] + vb[band] - tb[band])
    for label, arm in zip(("control", "candidate"), ARMS, strict=True):
        for name, value in totals[arm]["aggregate"].items():
            _reconcile(value, record["arms"][arm]["aggregate"][name], "direct_" + arm + "_" + name, record["residuals"])
        for name, risk in (("P_zero", "P_zero"), ("P_arm", "P_" + label)):
            _reconcile(totals[arm][name], record["risks"][risk], "direct_" + arm + "_" + name, record["residuals"])
        for band in BANDS:
            for part in (*PARTS, "cross"):
                for name, value in totals[arm]["joint"][band][part].items():
                    _reconcile(value, record["arms"][arm]["joint"][band][part][name],
                               "direct_" + arm + "_" + band + "_" + part + "_" + name, record["residuals"])
            for name in ("delta", "noise", "P_zero", "P_arm"):
                _reconcile(totals[arm]["joint"][band][name], record["arms"][arm]["joint"][band][name],
                           "direct_" + arm + "_" + band + "_" + name, record["residuals"])


def summarize_records(records):
    """one fixed whole-record resample matrix serves every signed cell contrast."""
    risk_names = ("R_zero", "R_control", "R_candidate", "P_zero", "P_control", "P_candidate")
    arm_paths = [("aggregate", name) for name in ("noise", "truth_coupling", "error", "signal", "coupling", "delta")]
    arm_paths += [("regional_partition", name) for name in ("active", "inactive", "offense", "defense")]
    arm_paths += [("native_pair_risk",)]
    arm_paths += [("joint", band, part, name) for band in BANDS for part in PARTS for name in ("E", "S", "I", "delta")]
    arm_paths += [("joint", band, "cross", name) for band in BANDS for name in ("E", "S", "delta")]
    arm_paths += [("joint", band, name) for band in BANDS for name in ("delta", "noise", "P_zero", "P_arm")]
    paths = [(section, name) for section in ("original_risks", "risks", "reconstructed_risks") for name in risk_names]
    paths += [("zero_regional_partition", name) for name in ("active", "inactive", "offense", "defense")]
    paths += [("native_pair_zero",)]
    paths += [("arms", arm, *path) for arm in ARMS for path in arm_paths]
    summaries = []
    for population_id, population in enumerate(POPULATIONS):
        for law_id, law in enumerate(LAWS):
            selected = [row for row in records if row["population"] == population and row["law"] == law]
            require([row["outer"] for row in selected] == list(range(200)), "04f summaries require all 200 ordered paired records")
            columns = []
            for path in paths:
                values = []
                for row in selected:
                    value = row
                    for key in path:
                        value = value[key]
                    values.append(value)
                columns.append(values)
            values = np.asarray(columns, dtype=float).T
            arm_offset = len(paths) - len(ARMS) * len(arm_paths)
            differences = values[:, arm_offset + len(arm_paths):] - values[:, arm_offset:arm_offset + len(arm_paths)]
            differences = np.column_stack((differences, values[:, paths.index(("risks", "P_candidate"))] - values[:, paths.index(("risks", "P_control"))],
                                           values[:, paths.index(("risks", "R_candidate"))] - values[:, paths.index(("risks", "R_control"))]))
            combined = np.column_stack((values, differences))
            require(np.isfinite(combined).all(), "04f summary inputs must be finite")
            seed = [40605, population_id, law_id]
            draws = np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed))).integers(0, 200, size=(10000, 200))
            weights = np.zeros((10000, 200))
            np.add.at(weights, (np.arange(10000)[:, None], draws), 1 / 200)
            bounds = np.quantile(weights @ combined, [.025, .975], axis=0, method="linear")
            means = combined.mean(axis=0)
            trees = ({}, {})
            difference_paths = [*arm_paths, ("prediction_risk",), ("regional_risk",)]
            for index, path in enumerate([*paths, *difference_paths]):
                target = trees[0] if index < len(paths) else trees[1]
                for key in path[:-1]:
                    target = target.setdefault(key, {})
                target[path[-1]] = dict(mean=float(means[index]), lower=float(bounds[0, index]), upper=float(bounds[1, index]))
            summaries.append(dict(population=population, law=law, n=200, seed=seed, resamples=10000,
                                  metrics=trees[0], paired_difference=trees[1]))
    return summaries


def _report_number(value):
    return f"{value:.9g}"


def _report_interval(metric):
    return (f"{_report_number(metric['mean'])} "
            f"[{_report_number(metric['lower'])}, {_report_number(metric['upper'])}]")


def write_report(output, assessment):
    """render the frozen assessment; figures and prose consume its summaries only."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    summaries = assessment["summaries"]
    require([(cell["population"], cell["law"]) for cell in summaries]
            == [(population, law) for population in POPULATIONS for law in LAWS],
            "report cell order differs from the frozen inventory")
    accounting = [
        "# prediction accounting\n",
        "all values are means over 200 paired datasets per cell. units: squared attempts per 60 team minutes. "
        "`control` is `graph_40ft`; `candidate` is `graph_two_band_80ft`. `zero` retains the noisy training context. "
        "positive prediction excess means worse prediction.\n",
        "## original, direct and reconstructed risks\n",
        "regional recovery uses all thirty scored pair differences and twelve regions. prediction uses whole lineups, "
        "656 native cells and inverse-reference-share weights. reconstruction uses the frozen training reference.\n",
        "| population | law | risk | original | direct | reconstructed | direct − original | reconstructed − direct |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for cell in summaries:
        metrics = cell["metrics"]
        for name in ("R_zero", "R_control", "R_candidate", "P_zero", "P_control", "P_candidate"):
            original = metrics["original_risks"][name]["mean"]
            direct = metrics["risks"][name]["mean"]
            reconstructed = metrics["reconstructed_risks"][name]["mean"]
            accounting.append("| " + " | ".join((cell["population"], cell["law"], f"`{name}`",
                *(_report_number(value) for value in (original, direct, reconstructed,
                    direct - original, reconstructed - direct)))) + " |")
    accounting += [
        "\n## exact excess-risk accounting\n",
        "`signal` means known deployment-signal energy, not achievable headroom. the shared context-noise energy "
        "does not explain paired differences. coupling and all cross terms retain their signs.\n",
        "| population | law | arm | noise | error | signal | coupling | error − signal + coupling | direct excess | residual |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cell in summaries:
        metrics = cell["metrics"]
        for arm, suffix in zip(ARMS, ("control", "candidate"), strict=True):
            aggregate = metrics["arms"][arm]["aggregate"]
            direct = metrics["risks"]["P_" + suffix]["mean"] - metrics["risks"]["P_zero"]["mean"]
            accounting.append("| " + " | ".join((cell["population"], cell["law"], suffix,
                *(_report_number(aggregate[name]["mean"]) for name in ("noise", "error", "signal", "coupling", "delta")),
                _report_number(direct), _report_number(aggregate["delta"]["mean"] - direct))) + " |")
    accounting += [
        "\n## paired uncertainty\n",
        "entries are mean [0.025, 0.975] post-study monte carlo intervals from 10,000 whole-record resamples. "
        "all components and both arms reuse the same indices within each cell. intervals concern mean behavior over "
        "truth/training-response draws conditional on fixed deployments, references and synthetic families; "
        "they are neither simultaneous bounds nor calibrated player intervals. complete signed contrasts are resampled "
        "before quantiles; endpoints do not add. numerical residuals use tolerances, never these intervals.\n",
        "| population | law | arm | error | known deployment-signal energy | coupling | excess |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for cell in summaries:
        for arm, suffix in zip(ARMS, ("control", "candidate"), strict=True):
            aggregate = cell["metrics"]["arms"][arm]["aggregate"]
            accounting.append("| " + " | ".join((cell["population"], cell["law"], suffix,
                *(_report_interval(aggregate[name]) for name in ("error", "signal", "coupling", "delta")))) + " |")
    accounting += [
        "\nall following differences are candidate minus control. regional and native-pair risks use the same thirty "
        "contrasts, so their sign comparison changes spatial aggregation/weighting only; full prediction also changes "
        "which player combinations are scored. this bridge supplies no replacement loss or recovery gate.\n",
        "| population | law | error difference | coupling difference | prediction difference | regional difference | native-pair difference |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for cell in summaries:
        difference = cell["paired_difference"]
        accounting.append("| " + " | ".join((cell["population"], cell["law"],
            _report_interval(difference["aggregate"]["error"]),
            _report_interval(difference["aggregate"]["coupling"]),
            _report_interval(difference["prediction_risk"]),
            _report_interval(difference["regional_risk"]),
            _report_interval(difference["native_pair_risk"]))) + " |")
    accounting += [
        "\n## regional active/inactive error and the score bridge\n",
        "active and inactive terms both retain denominator thirty; neither is a conditional subgroup average. "
        "nulls remain beside the other cells. native-pair and lineup prediction retain inverse-reference-share weights.\n",
        "| population | law | arm | regional risk | active error | inactive error | native-pair risk | lineup prediction risk |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for cell in summaries:
        metrics = cell["metrics"]
        for suffix, arm in (("zero", None), ("control", ARMS[0]), ("candidate", ARMS[1])):
            partition = metrics["zero_regional_partition"] if arm is None else metrics["arms"][arm]["regional_partition"]
            native = metrics["native_pair_zero"] if arm is None else metrics["arms"][arm]["native_pair_risk"]
            accounting.append("| " + " | ".join((cell["population"], cell["law"], suffix,
                _report_interval(metrics["risks"]["R_" + suffix]), _report_interval(partition["active"]),
                _report_interval(partition["inactive"]), _report_interval(native),
                _report_interval(metrics["risks"]["P_" + suffix]))) + " |")
    accounting += [
        "\n## numerical reconciliation\n",
        "the risk table shows residuals of cell means. the assessment retains all per-dataset residuals and the fixed "
        "independent direct-row checks at outer 0 and 199 in every cell: 24 final states. every check uses "
        "`abs(actual-expected) <= 1e-8*(1+abs(expected))`; "
        "excess checks use the signed contrast as reference. exact identities, order and hashes remain exact.\n",
        "| population | law | residual | checked datasets | maximum absolute value |",
        "|---|---|---|---:|---:|",
    ]
    for cell in summaries:
        records = [record for record in assessment["records"]
                   if (record["population"], record["law"]) == (cell["population"], cell["law"])]
        for name in dict.fromkeys(name for record in records for name in record["residuals"]):
            checked = [record["residuals"][name] for record in records if name in record["residuals"]]
            maximum = max(abs(value) for value in checked)
            accounting.append(f"| {cell['population']} | {cell['law']} | `{name}` | {len(checked)} | {_report_number(maximum)} |")
    with (output / "accounting-table.md").open("x") as destination:
        destination.write("\n".join(accounting) + "\n")

    partition_table = [
        "# joint spatial/player accounting\n",
        "units: squared attempts per 60 team minutes. entries are mean [0.025, 0.975] paired whole-record intervals. "
        "`E` is error energy, `S` is known deployment-signal energy and `I` is signed context coupling. "
        "for test/rest rows `delta = E-S+I`; cross rows retain `E_cross-S_cross`, with no separate coupling. "
        "a band total is the complete sum of its two player partitions and signed cross term.\n",
        "test means the thirty scored disjoint pair contrasts. rest includes common effects, untested combinations "
        "and unsupported directions; it is not synonymous with unidentifiable effects. the player partitions are "
        "euclidean-orthogonal, not deployment-orthogonal, so their cross terms need not vanish. spatial bands are "
        "orthogonal under the checked inverse-reference-share metric. omitted fitted correction is zero: its error "
        "equals signal and its coupling/excess cancel, while omitted context may still contribute absolute risk.\n",
        "| population | law | arm | band | player partition | E | S | I | delta |",
        "|---|---|---|---|---|---:|---:|---:|---:|",
    ]
    for cell in summaries:
        for arm, suffix in zip(ARMS, ("control", "candidate"), strict=True):
            for band in ("low", "high", "omitted"):
                joint = cell["metrics"]["arms"][arm]["joint"][band]
                for player_partition in ("test", "rest", "cross"):
                    values = joint[player_partition]
                    partition_table.append("| " + " | ".join((cell["population"], cell["law"], suffix,
                        band, player_partition, _report_interval(values["E"]), _report_interval(values["S"]),
                        "—" if player_partition == "cross" else _report_interval(values["I"]),
                        _report_interval(values["delta"]))) + " |")
                partition_table.append("| " + " | ".join((cell["population"], cell["law"], suffix,
                    band, "total", "—", "—", "—", _report_interval(joint["delta"]))) + " |")
    partition_table += [
        "\n## absolute band risks and omitted cancellation\n",
        "these retain omitted absolute context risk beside its cancelled excess; band risks add under the checked spatial metric.\n",
        "| population | law | arm | band | context-noise energy | zero prediction risk | arm prediction risk | excess |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for cell in summaries:
        for arm, suffix in zip(ARMS, ("control", "candidate"), strict=True):
            for band in ("low", "high", "omitted"):
                values = cell["metrics"]["arms"][arm]["joint"][band]
                partition_table.append("| " + " | ".join((cell["population"], cell["law"], suffix, band,
                    *(_report_interval(values[name]) for name in ("noise", "P_zero", "P_arm", "delta")))) + " |")
    partition_table += [
        "\n## paired candidate-minus-control partition differences\n",
        "each interval resamples the complete signed difference before taking quantiles.\n",
        "| population | law | band | player partition | E difference | S difference | I difference | delta difference |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for cell in summaries:
        for band in ("low", "high", "omitted"):
            joint = cell["paired_difference"]["joint"][band]
            for player_partition in ("test", "rest", "cross"):
                values = joint[player_partition]
                partition_table.append("| " + " | ".join((cell["population"], cell["law"], band,
                    player_partition, _report_interval(values["E"]), _report_interval(values["S"]),
                    "—" if player_partition == "cross" else _report_interval(values["I"]),
                    _report_interval(values["delta"]))) + " |")
            partition_table.append("| " + " | ".join((cell["population"], cell["law"], band,
                "total", "—", "—", "—", _report_interval(joint["delta"]))) + " |")
    with (output / "partition-table.md").open("x") as destination:
        destination.write("\n".join(partition_table) + "\n")

    colors = ("#496b8a", "#b79a65", "#a17c9a")
    figure, axes = plt.subplots(3, 2, figsize=(14, 10), sharex=True)
    extent = 0.
    for axis, cell in zip(axes.flat, summaries, strict=True):
        labels = []
        for y, (arm, suffix) in enumerate(zip(ARMS, ("control", "candidate"), strict=True)):
            aggregate = cell["metrics"]["arms"][arm]["aggregate"]
            positive, negative = 0., 0.
            for value, color in zip((aggregate["error"]["mean"], -aggregate["signal"]["mean"],
                                     aggregate["coupling"]["mean"]), colors, strict=True):
                left = positive if value >= 0 else negative
                axis.barh(y, value, left=left, height=.36, color=color, edgecolor="white", linewidth=.6)
                if value >= 0:
                    positive += value
                else:
                    negative += value
            delta = aggregate["delta"]
            direct = cell["metrics"]["risks"]["P_" + suffix]["mean"] - cell["metrics"]["risks"]["P_zero"]["mean"]
            axis.plot([delta["lower"], delta["upper"]], [y, y], color="#202020", linewidth=1.1)
            axis.plot([delta["lower"], delta["lower"]], [y - .07, y + .07], color="#202020", linewidth=1.1)
            axis.plot([delta["upper"], delta["upper"]], [y - .07, y + .07], color="#202020", linewidth=1.1)
            axis.plot(direct, y, marker="D", color="#202020", markersize=5)
            labels.append(f"{suffix}\ndirect Δ={direct:.4g} [{delta['lower']:.4g}, {delta['upper']:.4g}]\n"
                f"E={aggregate['error']['mean']:.4g}; −S={-aggregate['signal']['mean']:.4g}; I={aggregate['coupling']['mean']:.4g}")
            extent = max(extent, abs(negative), abs(positive), abs(delta["lower"]), abs(delta["upper"]))
        axis.set_yticks([0, 1], labels, fontsize=9)
        axis.invert_yaxis()
        axis.set_title(f"{cell['population']} / {cell['law']}", loc="left", fontsize=12, pad=10)
        axis.axvline(0, color="#333333", linewidth=.9)
        axis.grid(axis="x", alpha=.15)
        axis.set_axisbelow(True)
        axis.spines[["top", "right", "left"]].set_visible(False)
        axis.tick_params(axis="y", length=0)
    for axis in axes.flat:
        axis.set_xlim(-1.08 * extent, 1.08 * extent)
    figure.suptitle("signed prediction excess: error − known deployment-signal energy + coupling", fontsize=15, y=.97)
    figure.supxlabel("squared attempts per 60 team minutes; positive excess means worse prediction", fontsize=11, y=.07)
    figure.legend(handles=[Patch(facecolor=color, label=label) for color, label in zip(colors,
        ("error", "− known deployment-signal energy", "signed context coupling"), strict=True)]
        + [Line2D([], [], color="#202020", marker="D", linestyle="none", label="direct total and paired interval")],
        loc="lower center", bbox_to_anchor=(.5, .015), ncol=4, frameon=False, fontsize=10)
    figure.subplots_adjust(left=.19, right=.98, top=.90, bottom=.13, wspace=.52, hspace=.54)
    figure.savefig(output / "prediction-accounting.png", dpi=170)
    plt.close(figure)

    differences = [cell["paired_difference"] for cell in summaries]
    regional_better = sum(cell["regional_risk"]["mean"] < 0 for cell in differences)
    prediction_worse = sum(cell["prediction_risk"]["mean"] > 0 for cell in differences)
    error_changes = [cell["aggregate"]["error"]["mean"] for cell in differences]
    coupling_changes = [cell["aggregate"]["coupling"]["mean"] for cell in differences]
    error_better = sum(value < 0 for value in error_changes)
    coupling_larger = sum(value > 0 for value in coupling_changes)
    native_better = sum(cell["native_pair_risk"]["mean"] < 0 for cell in differences)
    excesses = [cell["metrics"]["arms"][arm]["aggregate"]["delta"]["mean"]
                for cell in summaries for arm in ARMS]
    joint_changes = [(cell["paired_difference"]["joint"][band][part]["delta"]["mean"],
                      cell["population"], cell["law"], band, part)
                     for cell in summaries for band in ("low", "high") for part in ("test", "rest", "cross")]
    largest_joint = max(joint_changes, key=lambda item: abs(item[0]))
    omitted_baselines = [cell["metrics"]["arms"][ARMS[0]]["joint"]["omitted"]["P_zero"]["mean"]
                         for cell in summaries]
    decision = (
        "# attribution prediction diagnosis\n\n"
        "04e remains `criteria_failed,nomination:null,admission:not_admitted,handoff:null`. this diagnosis "
        "reconciles its saved year-five evidence; it selects no model.\n\n"
        f"the candidate improves regional pair recovery in {regional_better} of six cells, yet worsens complete-lineup "
        f"prediction in {prediction_worse}. both predictors' mean excess over the noisy training-context baseline ranges "
        f"from {_report_number(min(excesses))} to {_report_number(max(excesses))} squared attempts per 60 team minutes. "
        "the accounting is exact: excess equals error minus known deployment-signal energy plus signed context coupling. "
        "shared context-noise energy enters absolute risk but explains no paired excess by itself.\n\n"
        f"candidate-minus-control error changes range from {_report_number(min(error_changes))} to "
        f"{_report_number(max(error_changes))}; coupling changes range from {_report_number(min(coupling_changes))} "
        f"to {_report_number(max(coupling_changes))}. error falls in {error_better} cells and coupling rises in "
        f"{coupling_larger}; the shared signal cancels from this comparison. these are signed accounting terms, "
        "not causal blame or evidence that changing one component would help.\n\n"
        f"the largest absolute mean paired change among the fixed joint terms is {largest_joint[3]}/{largest_joint[4]} "
        f"in {largest_joint[1]}/{largest_joint[2]}: {_report_number(largest_joint[0])}. this descriptive maximum is "
        "not a mechanism-selection test. omitted-band baseline risk spans "
        f"{_report_number(min(omitted_baselines))} to {_report_number(max(omitted_baselines))}, while omitted excess cancels.\n\n"
        f"the same thirty contrasts improve under prediction's native spatial metric in {native_better} cells. "
        "that bridge separates regional aggregation/weighting from the additional lineup combinations. the joint "
        "tables retain low/high test/rest contributions and player cross terms. rest includes common effects, untested "
        "combinations and unsupported directions; it cannot be called unidentifiable. omitted fitted corrections "
        "are zero and their excess cancels, despite possible omitted absolute context error. nulls and inactive "
        "errors remain visible as contrary evidence to general recovery gains.\n\n"
        "the remedy remains unresolved; no successor is proposed. paired post-study monte carlo intervals concern "
        "mean behavior over the saved synthetic families conditional on fixed deployments and training references. "
        "they neither confirm a discovered cause nor establish calibrated player intervals, complete-rate positivity, "
        "chance valuation or real-hockey ability. no new responses, fits, scale searches or numerical probes were run.\n"
    )
    require(len(decision.split()) <= 500, "decision exceeds 500 words")
    with (output / "decision.md").open("x") as destination:
        destination.write(decision)
    return {name: identity(output / filename) for name, filename in (
        ("decision", "decision.md"), ("accounting_table", "accounting-table.md"),
        ("partition_table", "partition-table.md"), ("prediction_accounting", "prediction-accounting.png"))}


RISK_NAMES = ("R_zero", "R_control", "R_candidate", "P_zero", "P_control", "P_candidate")
UNITS = "squared attempts per 60 team minutes"
LIMITATIONS = [
    "saved-state accounting cannot prove a remedy or establish real-hockey identification",
    "known deployment-signal energy is not achievable headroom; signed coupling is not causal blame",
    "the player complement includes common effects, untested combinations and unsupported directions",
    "post-study monte carlo intervals concern mean behavior over truth/training-response draws conditional on fixed deployments, references and synthetic families",
    "intervals are not simultaneous bounds, calibrated player intervals or confirmation of a discovered cause",
    "complete-rate positivity, player intervals, chance valuation and publication remain separate requirements",
    "04e retains criteria_failed, no nomination, not_admitted and no handoff",
]


def _cost(started, process_started):
    return dict(**resources(started), process_seconds=time.process_time() - process_started)


def assess(source_result, output):
    """one read-only saved-evidence traversal, fixed accounting, paired summaries and report."""
    started, process_started = time.monotonic(), time.process_time()
    source = read_source(source_result)
    producer = implementation()
    clean_implementation(producer)
    root = output_path(str(output), list(source.input_roots))
    require(root.parent == Path("/Volumes/Expansion/hockey-stats/runs")
            and root.name.startswith("attribution-04f-"),
            "04f output must be a new exclusive external study directory")
    root.mkdir()
    snapshot = root / "spec-snapshot.md"
    with snapshot.open("xb") as destination:
        destination.write(SPEC.read_bytes())
    specification = identity(snapshot)
    consumed = {name if name == "source_result" else "source_" + name: reference
                for name, reference in source.consumed.items()}
    consumed["diagnostic_spec"] = specification
    protocol = artifact("attribution_prediction_protocol", "research", consumed, schema_version=4,
        source_result=source.reference, source_implementation=source.result["implementation"],
        spec_snapshot=specification,
        scope=dict(populations=list(POPULATIONS), laws=list(LAWS), arms=list(ARMS), outer=list(range(200)),
                   season=SEASONS[-1], lineage_seasons=list(SEASONS), order=["population", "law", "outer", "season"],
                   original_state_tags="preserved", response_generation=False, fitting=False, scale_search=False),
        units=UNITS, annual_rate=40., training_reference="original fixed training xbar, u and native p",
        projections=dict(spatial=dict(low=list(range(11)), high=list(range(11, 40)), omitted="zero-sum complement",
                                      ranks=[11, 29, 615], metric="inverse native reference share",
                                      formula="F_low=B_low R_low'; F_high=B_high R_high'; F_omitted=I-1p'-F_low-F_high"),
                         players=dict(dimension=64, scored_pairs=30, excluded_pairs=[[26, 31], [26, 31]],
                                      role_order=["offense", "defense"], formula="J_test=.5 C'C; J_rest=I-J_test",
                                      cross_terms="signed deployment interactions retained")),
        bootstrap=dict(resamples=10000, records_per_cell=200, bit_generator="PCG64",
                       seed="SeedSequence([40605,population_id,law_id])", populations=list(POPULATIONS), laws=list(LAWS),
                       quantiles=[.025, .975], method="linear", unit="one complete paired dataset",
                       shared_indices="both arms and all components within each cell",
                       paired_contrast="candidate minus control before resampling and quantiles"),
        numerical=dict(reconciliation="abs(actual-expected) <= 1e-8*(1+abs(expected))",
                       excess_reference="the signed contrast, not the common absolute risk",
                       ids_order_hashes="exact"),
        verification=dict(expected_inventory=source.inventory, direct_outer=[0, 199], direct_cells=6,
                          direct_final_states=24, original_six_risks=1200, regional_denominator=30,
                          fixed_checks=["source and response lineage", "current player identity selection", "saved context identity",
                                        "shape projection identities and inverse-share orthogonality", "omitted cancellation",
                                        "same-role reference shifts", "zero evaluated inseparable contrasts",
                                        "original compact means and active/inactive totals"]),
        limitations=LIMITATIONS)
    protocol_path = root / "protocol.json"
    write_json(protocol_path, json_values(protocol))
    protocol_reference = identity(protocol_path)
    gram = deployment_gram(source.evaluation[-1]["X"], source.evaluation[-1]["si"],
                           source.evaluation[-1]["e"], len(source.evaluation[-1]["strata"]))
    records, datasets, annual_states, final_states, statistics_paths = [], 0, 0, 0, set()
    for original, population, truth, states in iter_final_states(source):
        diagnostics = diagnose_record(states, population, source.training[-1], source.evaluation[-1],
                                      truth, source.basis, source.W, gram, direct=original["outer"] in (0, 199))
        saved = original["losses"][-1]
        diagnostics["original_risks"] = {name: saved[name] for name in RISK_NAMES}
        diagnostics["original_regional_partition"] = {}
        for name in RISK_NAMES:
            _reconcile(diagnostics["risks"][name], saved[name], "original_" + name, diagnostics["residuals"])
        for arm, label in zip(ARMS, ("control", "candidate"), strict=True):
            _reconcile(diagnostics["arms"][arm]["aggregate"]["delta"], saved["P_" + label] - saved["P_zero"],
                       "original_" + arm + "_signed_excess", diagnostics["residuals"])
            partition = saved[label]["regional_partition"]
            diagnostics["original_regional_partition"][arm] = partition
            for name in ("active", "inactive", "offense", "defense"):
                _reconcile(diagnostics["arms"][arm]["regional_partition"][name], partition[name],
                           "original_" + arm + "_regional_" + name, diagnostics["residuals"])
        for prefix in ("P", "R"):
            _reconcile(diagnostics["risks"][prefix + "_candidate"] - diagnostics["risks"][prefix + "_control"],
                       saved[prefix + "_candidate"] - saved[prefix + "_control"],
                       "original_" + prefix + "_paired_difference", diagnostics["residuals"])
        records.append(dict(population=original["population"], law=original["law"], outer=original["outer"],
            season=SEASONS[-1], statistics=original["statistics"]["arrays"],
            annual={arm: original["annual"][arm][-1] for arm in ARMS},
            truth_sha256=original["truth_sha256"], activation_sha256=original["activation_sha256"],
            response_sha256=original["responses"][-1]["sha256"], **diagnostics))
        datasets += 1
        annual_states += sum(len(references) for references in original["annual"].values())
        final_states += len(states)
        statistics_paths.add(original["statistics"]["arrays"]["path"])
        if datasets % 200 == 0:
            print(f"validated {datasets}/1200 paired datasets; {annual_states}/12000 annual states", file=sys.stderr)
    actual_inventory = dict(datasets=datasets, annual_states=annual_states, final_states=final_states,
                            statistics_archives=len(statistics_paths), fit_manifests=len(source.result["consumed_fits"]))
    direct_states = 2 * sum(record["direct_verified"] for record in records)
    require(actual_inventory == source.inventory and direct_states == 24
            and [(record["population"], record["law"], record["outer"], record["season"]) for record in records]
                == [(population, law, outer, SEASONS[-1]) for population in POPULATIONS for law in LAWS for outer in range(200)],
            "04f consumed or direct-verification inventory differs from its fixed protocol")
    summaries = summarize_records(records)
    aggregate_residuals = {}
    require([(cell["population"], cell["law"]) for cell in source.result["summaries"]]
            == [(cell["population"], cell["law"]) for cell in summaries], "04e compact cell order differs")
    for cell, original in zip(summaries, source.result["summaries"], strict=True):
        cell_name = cell["population"] + "_" + cell["law"] + "_"
        for name in RISK_NAMES:
            _reconcile(cell["metrics"]["risks"][name]["mean"], original["means"][name],
                       cell_name + name, aggregate_residuals)
        _reconcile(cell["paired_difference"]["prediction_risk"]["mean"],
                   original["differences"]["prediction_candidate_minus_control"],
                   cell_name + "paired_prediction_difference", aggregate_residuals)
        _reconcile(cell["paired_difference"]["regional_risk"]["mean"],
                   -original["differences"]["regional_control_minus_candidate"],
                   cell_name + "paired_regional_difference", aggregate_residuals)
        for arm, label in zip(ARMS, ("control", "candidate"), strict=True):
            for name in ("active", "inactive", "offense", "defense"):
                _reconcile(cell["metrics"]["arms"][arm]["regional_partition"][name]["mean"],
                           original["diagnostics"][label][name], cell_name + arm + "_" + name, aggregate_residuals)
    costs = dict(**actual_inventory, direct_final_states=direct_states, generated_responses=0,
                 new_fits=0, scale_searches=0, new_numerical_probes=0)
    assessment = artifact("attribution_prediction_assessment", "research",
        dict(protocol=protocol_reference, **consumed), schema_version=4, protocol=protocol_reference,
        source_result=source.reference, source_implementation=source.result["implementation"], spec_snapshot=specification,
        execution_status="complete", reconciliation="verified", records=records, summaries=summaries,
        aggregate_residuals=aggregate_residuals, costs=costs, units=UNITS, limitations=LIMITATIONS)
    reports = write_report(root, assessment)
    assessment.update(reports=reports, resources=_cost(started, process_started))
    assessment_path = root / "assessment.json"
    write_json(assessment_path, json_values(assessment))
    result = artifact("attribution_prediction_result", "research",
        dict(protocol=protocol_reference, assessment=identity(assessment_path), **consumed,
             **{"report_" + name: reference for name, reference in reports.items()}), schema_version=4,
        protocol=protocol_reference, assessment=identity(assessment_path), source_result=source.reference,
        source_implementation=source.result["implementation"], spec_snapshot=specification,
        execution_status="complete", reconciliation="verified", nomination=None, admission="not_admitted", handoff=None,
        counts=actual_inventory, costs=costs, summaries=summaries, reports=reports,
        units=UNITS, limitations=LIMITATIONS, resources=_cost(started, process_started))
    result_path = root / "result.json"
    write_json(result_path, json_values(result))
    return identity(result_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("assess", allow_abbrev=False)
    command.add_argument("--source-result", required=True)
    command.add_argument("--output", required=True)
    arguments = parser.parse_args(argv)
    try:
        reference = assess(arguments.source_result, arguments.output)
        print(json.dumps(json_values(reference)))
        return 0
    except (InputContractError, OSError, KeyError, TypeError, ValueError, np.linalg.LinAlgError, FloatingPointError) as error:
        print("incomplete execution: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
