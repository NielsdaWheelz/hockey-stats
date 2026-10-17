"""04i's observable regional penalty selection and paired assessment."""

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import sys
import time

for _thread in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_thread] = "1"

import numpy as np

from hockey_stats.artifacts import (
    artifact, json_values, linked_path, load_arrays, ordered_array_digest,
    read_artifact, require, resources, write_arrays, write_json,
)
from hockey_stats.attribution import (
    fit_pooled_shape, pooled_shape_at, pooled_shape_grid, regional_penalty_scores,
)
from hockey_stats.attribution_data import (
    ResolutionSourceSlice, exposure_centering, likelihood_spectrum, pool_shape_likelihood,
    read_regularization_source_populations, read_resolution_assessment,
    read_resolution_control, read_resolution_source_slice,
)
from hockey_stats.attribution_prediction import deployment_gram, realized_shape_errors
from hockey_stats.attribution_simulation import independent_truths, paired_truths, shape_operators, truth_digest
from hockey_stats.captures import InputContractError
from hockey_stats.chance_cli import identity, output_path


SPEC = Path(__file__).resolve().parents[2]/"docs/specs/04i-attribution-selection.md"
RESEARCH_ROOT = Path("/Volumes/Expansion/hockey-stats/runs")
SOURCE_RESULT_SHA256 = "c962c9d4c38c86150fceff15036c1f19bc5bfea897127b7fd08d4f929cdcdbb7"
SOURCE_PREPARED_SHA256 = "d20303ab13bc2d4282f4498756bcf48d83a2326f9adc4a8d49f2b23b274b5f85"
SOURCE_PROTOCOL_SHA256 = "a09a39d789274c0c4e3abb2814ce2ae67569c4da15839b2d54db74811c2f6fb1"
POPULATIONS = ("sparse", "diffuse", "null")
LAWS = ("gaussian", "game_pace")
CELLS = tuple(("paired" if population == "null" else "independent", population, law)
              for population in POPULATIONS for law in LAWS)
SEASONS = tuple(f"{year}{year+1}" for year in range(2021, 2026))
VARIANCES = (0., *np.power(10., np.arange(-8., .25, .5)).tolist())
TARGETS = ("twelve_region_vector", "within_20_ft", "lateral_redistribution")
PARTITIONS = ("offense", "attempts_allowed", "physically_active", "physically_inactive",
              "entrant_32_offense", "entrant_32_attempts_allowed", "entrant_33_offense",
              "entrant_33_attempts_allowed", "returner_8_offense", "returner_8_attempts_allowed")
RULES = dict(
    cells=[dict(family=f, population=p, law=l) for f, p, l in CELLS], seasons=list(SEASONS),
    basis_columns=list(range(11)), prior_variances=list(VARIANCES), rate=40., recovery_denominator=64,
    targets=list(TARGETS), selection="final-season native regional covariance penalty; gaussian working noise",
    score_terms=["norm_term", "cross_term", "correction_term"], tie_order="smaller prior variance",
    prediction_gain_retention=.99, diagnostic_vetoes=False,
    bootstrap=dict(resamples=10000, seed=41001, population_ids=dict(sparse=0, diffuse=1, null=2),
        law_ids=dict(gaussian=0, game_pace=1), bit_generator="PCG64", interval=[.025, .975],
        quantile="linear", shared_indices=True),
    numerical=dict(equation_residual_max=1e-8, atol=1e-10, rtol=1e-8,
        research_probe_ids=[100, 199], fixture_probe_ids=[1], cutoff_factors=[.1, 1., 10.]),
    units="(redistributed recorded unblocked attempts per 60 team minutes)^2",
    nomination=None, admission="not_admitted", handoff=None,
)
LIMITS = [
    "the gaussian working covariance can be misspecified under non-null game pace",
    "the final-season unregularized regional reference is noisy; the selected minimum is not unbiased selected-estimator risk",
    "constant history can misrepresent changing players; eleven modes omit physical native detail",
    "a regional benefit does not establish uniform functional or player recovery",
    "the strict 99% gain-retention policy may remain unresolved with 100 exposed records per cell",
    "intervals describe mean experimental performance conditional on fixed designs and exposed truth populations; no player intervals or simultaneous bands",
    "the inseparable 26/31 average retains weight two; its individual difference remains unavailable",
    "spatial prediction does not establish complete-rate validity, real-player recovery, calibrated uncertainty or supported chance valuation",
    "no nomination, model admission or publication follows from developmental progress",
]


@dataclass(frozen=True)
class Prepared:
    reference: dict
    document: dict
    protocol: dict
    source: ResolutionSourceSlice


def _ids(purpose):
    return tuple(range(100, 200)) if purpose == "research" else (1,)


def _budget(purpose):
    n = len(_ids(purpose))
    return dict(cells=6, statistic_histories=6*n, annual_likelihoods=30*n,
        candidate_grid_evaluations=108*n, candidate_fits=6*n, control_replays=6*n,
        eigensolve_probes=12 if purpose == "research" else 6, new_responses=0, new_annual_fits=0)


def _cost(started, process_started, root):
    return dict(**resources(started), process_seconds=time.process_time()-process_started,
        output_bytes=sum(path.stat().st_size for path in root.rglob("*") if path.is_file()),
        output_bytes_scope="tree_before_current_manifest_serialization")


def _source(reference, purpose):
    require(purpose in ("research", "fixture_exercise"), "invalid study purpose")
    if purpose == "research":
        require(reference["sha256"] == SOURCE_RESULT_SHA256, "04h result differs from pinned research source")
    source = read_resolution_source_slice(reference, CELLS, _ids(purpose))
    require(source.result["purpose"] == purpose, "source and execution purposes differ")
    if purpose == "research":
        require(source.result["prepared"]["sha256"] == SOURCE_PREPARED_SHA256
            and source.result["protocol"]["sha256"] == SOURCE_PROTOCOL_SHA256,
            "04h prepared/protocol identities differ")
    shape_operators(source.source.W)
    return source


def _geometry(source):
    data = source.source
    W, near, lateral = shape_operators(data.W)
    return dict(native=ordered_array_digest(dict(p=data.basis.p)), basis=data.basis.sha256,
        regions=ordered_array_digest(dict(W=W, within_20_ft=near, lateral_redistribution=lateral)),
        recovery=ordered_array_digest(dict(J=data.recovery[-1])),
        identities=ordered_array_digest({season: np.asarray(design["players"], dtype=np.int64)
            for season, design in zip(SEASONS, data.training, strict=True)}),
        grid=ordered_array_digest(dict(prior_variances=np.asarray(VARIANCES))),
        rule=hashlib.sha256(json.dumps(RULES, sort_keys=True, separators=(",", ":")).encode()).hexdigest())


def _parents(source):
    return dict(source_result=source.reference, source_prepared=source.result["prepared"],
        source_protocol=source.result["protocol"], statistic_result=source.source.reference,
        **{f"control_{index:02d}": source.controls[cell]["reference"] for index, cell in enumerate(CELLS)})


def _inventory(source):
    return [dict(family=row["family"], population=row["population"], law=row["law"],
        outer=row["outer"], statistics=row["statistics"]["arrays"]) for row in source.source.records]


def prepare(source_result, purpose, output):
    started, process_started = time.monotonic(), time.process_time()
    source = _source(identity(Path(source_result).resolve(strict=True)), purpose)
    root = output_path(str(output), list(source.input_roots))
    require(root.is_relative_to(RESEARCH_ROOT) and any(part.startswith("attribution-04i-") for part in root.parts),
        "04i outputs require an external attribution-04i run directory")
    root.mkdir()
    snapshot = root/"spec-snapshot.md"
    with snapshot.open("xb") as destination:
        destination.write(SPEC.read_bytes())
    parents = dict(**_parents(source), spec_snapshot=identity(snapshot))
    geometry = _geometry(source)
    fields = dict(source_result=source.reference, source_producer=source.result["implementation"],
        statistic_producer=source.source.result["implementation"], geometry=geometry,
        outer_ids=list(_ids(purpose)), budget=_budget(purpose),
        target_rank=source.source.protocol["recovery_receipts"][-1]["rank"])
    protocol = artifact("attribution_selection_protocol", purpose, parents, schema_version=5,
        **fields, rules=RULES, selected_statistics=_inventory(source),
        source_exposure="research_exposed" if purpose == "research" else "fixture_exercise",
        resources=_cost(started, process_started, root))
    protocol_path = root/"protocol.json"
    write_json(protocol_path, json_values(protocol))
    document = artifact("attribution_selection_prepared", purpose,
        dict(protocol=identity(protocol_path), **parents), schema_version=5,
        protocol=identity(protocol_path), **fields, resources=_cost(started, process_started, root))
    path = root/"prepared.json"
    write_json(path, json_values(document))
    return identity(path)


def read_prepared(path):
    reference = identity(Path(path).resolve(strict=True))
    document = read_artifact(path, "attribution_selection_prepared", expected_schema=5)
    protocol = read_artifact(linked_path(document["protocol"]), "attribution_selection_protocol", expected_schema=5)
    purpose = document["purpose"]
    source = _source(document["source_result"], purpose)
    fields = dict(source_result=source.reference, source_producer=source.result["implementation"],
        statistic_producer=source.source.result["implementation"], geometry=_geometry(source),
        outer_ids=list(_ids(purpose)), budget=_budget(purpose),
        target_rank=source.source.protocol["recovery_receipts"][-1]["rank"])
    require(protocol["purpose"] == purpose
        and all(document.get(name) == protocol.get(name) == value for name, value in fields.items())
        and protocol["rules"] == RULES and protocol["selected_statistics"] == _inventory(source)
        and protocol["source_exposure"] == ("research_exposed" if purpose == "research" else "fixture_exercise")
        and protocol["consumed"] == dict(**_parents(source), spec_snapshot=protocol["consumed"]["spec_snapshot"])
        and document["consumed"] == dict(protocol=document["protocol"], **protocol["consumed"]),
        "04i prepared rules, source inventory, geometry or parent bindings differ")
    return Prepared(reference, document, protocol, source)


def _close(actual, expected, label):
    actual, expected = np.asarray(actual), np.asarray(expected)
    require(actual.shape == expected.shape and np.allclose(actual, expected, atol=1e-10, rtol=1e-8),
        label+": saved eleven-mode control differs")
    return float(np.max(np.abs(actual-expected), initial=0.))


def _probe(pool, grid, scored, state, J, W, evaluation):
    """independently enumerate every candidate with the pooled eigensystem."""
    values, vectors = np.linalg.eigh((pool.H+pool.H.T)/2)
    Ks = np.stack([np.zeros_like(pool.H) if a == 0 else
        (vectors*(a/(1+a*values))) @ vectors.T for a in VARIANCES])
    final, S, Q, p, R = pool.target, pool.target_selection, pool.score, pool.p, pool.R
    eigenvalues, eigenvectors, _, masks = likelihood_spectrum(final.H)
    Hplus = (eigenvectors[:, masks[1]]/eigenvalues[masks[1]]) @ eigenvectors[:, masks[1]].T
    T_h = final.T-final.T.sum(axis=1, keepdims=True)*p
    D, U = R.T @ W, J @ Hplus @ T_h @ W
    factor = pool.r**2/64
    A = J @ S @ Ks @ Q @ D
    terms = dict(norm_term=factor*np.sum(A*A, axis=(1, 2)),
        cross_term=-2*factor*np.sum(A*U, axis=(1, 2)),
        correction_term=2*factor*np.sum(D*D)*np.trace(J @ S @ Ks @ S.T @ J.T, axis1=1, axis2=2))
    scores = sum(terms.values())
    winner, actual_winner = int(np.argmin(scores)), int(np.argmin(scored["scores"]))
    P = exposure_centering(pool.u)
    means, factor_means = P @ Ks @ Q, P @ grid.covariances @ Q
    covariances, factor_covariances = P @ Ks @ P.T, P @ grid.covariances @ P.T
    maps, factor_maps = S @ means @ R.T, S @ factor_means @ R.T
    yh = final.ybar-final.ybar.sum(axis=1, keepdims=True)*p
    contexts, factor_contexts = yh-final.xbar @ maps, yh-final.xbar @ factor_maps
    checks = {name: bool(np.allclose(terms[name], scored[name], atol=1e-10, rtol=1e-8)) for name in terms}
    checks.update(scores=bool(np.allclose(scores, scored["scores"], atol=1e-10, rtol=1e-8)),
        covariances=bool(np.allclose(Ks, grid.covariances, atol=1e-10, rtol=1e-8)),
        coefficients=bool(np.allclose(means, factor_means, atol=1e-10, rtol=1e-8)),
        centered_covariances=bool(np.allclose(covariances, factor_covariances, atol=1e-10, rtol=1e-8)),
        contexts=bool(np.allclose(contexts, factor_contexts, atol=1e-10, rtol=1e-8)),
        selected_coefficients=bool(np.allclose(factor_means[actual_winner], state.Theta, atol=1e-10, rtol=1e-8)),
        selected_covariance=bool(np.allclose(factor_covariances[actual_winner], state.V, atol=1e-10, rtol=1e-8)),
        selected_context=bool(np.allclose(factor_contexts[actual_winner], state.A, atol=1e-10, rtol=1e-8)),
        winning_score=bool(np.isclose(scores[winner], scored["scores"][actual_winner], atol=1e-10, rtol=1e-8)))
    maximum_prediction_difference, maximum_selected_prediction_difference = 0., 0.
    checks.update(predictions=True, selected_predictions=True)
    for start in range(0, len(evaluation["si"]), 256):
        X, si = evaluation["X"][start:start+256], evaluation["si"][start:start+256]
        eigen_prediction = pool.r*(contexts[:, si]+X @ maps)
        factor_prediction = pool.r*(factor_contexts[:, si]+X @ factor_maps)
        selected_prediction = pool.r*(state.A[si]+X @ (S @ state.Theta @ R.T))
        checks["predictions"] &= bool(np.allclose(eigen_prediction, factor_prediction, atol=1e-10, rtol=1e-8))
        checks["selected_predictions"] &= bool(np.allclose(eigen_prediction[winner], selected_prediction, atol=1e-10, rtol=1e-8))
        maximum_prediction_difference = max(maximum_prediction_difference,
            float(np.max(np.abs(eigen_prediction-factor_prediction), initial=0.)))
        maximum_selected_prediction_difference = max(maximum_selected_prediction_difference,
            float(np.max(np.abs(eigen_prediction[winner]-selected_prediction), initial=0.)))
    I = np.eye(len(pool.H))
    residuals = [0. if a == 0 else float(np.linalg.norm((pool.H+I/a) @ (K @ Q)-Q)/max(1., np.linalg.norm(Q)))
        for a, K in zip(VARIANCES, Ks, strict=True)]
    covariance_residuals = [0. if a == 0 else float(np.linalg.norm((pool.H+I/a) @ K-I)/max(1., np.linalg.norm(I)))
        for a, K in zip(VARIANCES, Ks, strict=True)]
    checks["equations"] = max(residuals+covariance_residuals) <= 1e-8
    return dict(winner=winner, factor_winner=actual_winner, changed_winner=winner != actual_winner,
        checks=checks, verified=all(checks.values()), mean_equation_relative_residuals=residuals,
        covariance_equation_relative_residuals=covariance_residuals,
        maximum_score_difference=float(np.max(np.abs(scores-scored["scores"]))),
        maximum_coefficient_difference=float(np.max(np.abs(means-factor_means))),
        maximum_covariance_difference=float(np.max(np.abs(covariances-factor_covariances))),
        maximum_context_difference=float(np.max(np.abs(contexts-factor_contexts))),
        maximum_prediction_difference=maximum_prediction_difference,
        maximum_selected_prediction_difference=maximum_selected_prediction_difference)


def _fit_axes():
    axes = dict(outer_ids=["outer"])
    axes.update({name: ["outer", "prior_variance"] for name in ("scores", "norm_term", "cross_term", "correction_term")})
    axes.update(selected_index=["outer"], selected_a=["outer"],
        Theta=["outer", "union_role_player", "spatial_mode"],
        V=["outer", "union_role_player", "union_role_player"], context=["outer", "final_context", "native_cell"])
    return axes


def _fit_shapes(n):
    lengths = dict(outer=n, prior_variance=18, union_role_player=68, spatial_mode=11, final_context=6, native_cell=656)
    return {name: tuple(lengths[axis] for axis in axes) for name, axes in _fit_axes().items()}


def _valid_residuals(values):
    return all(type(value) in (int, float) and np.isfinite(value) and 0 <= value <= 1e-8 for value in values)


def fit(prepared, population, law, output):
    started, process_started = time.monotonic(), time.process_time()
    prepared = read_prepared(prepared)
    document, selected = prepared.document, prepared.source
    source = selected.source
    require(population in POPULATIONS and law in LAWS, "invalid 04i cell")
    cell = ("paired" if population == "null" else "independent", population, law)
    records = [row for row in source.records if tuple(row[name] for name in ("family", "population", "law")) == cell]
    ids, n = document["outer_ids"], len(document["outer_ids"])
    require([row["outer"] for row in records] == ids, "selected statistic histories are incomplete or reordered")
    root = output_path(str(output), list(selected.input_roots))
    require(root.is_relative_to(Path(document["protocol"]["path"]).parent), "fit output must be beneath its prepared run")
    root.mkdir()
    control = read_resolution_control(selected, cell)
    fixed_pool = pool_shape_likelihood(source.fixed_populations, source.basis, tuple(range(11)), SEASONS[-1])
    grid = pooled_shape_grid(fixed_pool.H, VARIANCES)
    arrays = {name: np.empty(shape, dtype=np.int64 if name in ("outer_ids", "selected_index") else np.float64)
        for name, shape in _fit_shapes(n).items()}
    arrays["outer_ids"][:] = ids
    replay, equations, probes = [], [], []
    probe_ids = RULES["numerical"]["research_probe_ids" if document["purpose"] == "research" else "fixture_probe_ids"]
    for index, record in enumerate(records):
        populations, _ = read_regularization_source_populations(source, record)
        pool = pool_shape_likelihood(populations, source.basis, tuple(range(11)), SEASONS[-1])
        require(np.array_equal(pool.H, grid.H) and pool.player_ids == fixed_pool.player_ids,
            "response changed fixed pooled information or ordered identities")
        marginal = fit_pooled_shape(pool, VARIANCES, grid=grid)
        replay_values = (("objectives", marginal.objectives), ("selected_a", marginal.a),
            ("Theta", marginal.Theta), ("V", marginal.V), ("context", marginal.A))
        replay.append(dict(outer=record["outer"],
            maxima={name: _close(actual, control[name+"_11"][index], name) for name, actual in replay_values},
            tolerance_fractions={name: float(np.max(np.abs(actual-control[name+"_11"][index])/
                (1e-10+1e-8*np.abs(control[name+"_11"][index])), initial=0.)) for name, actual in replay_values}))
        final, J = populations[-1], source.recovery[-1]
        T_h = final.T-final.T.sum(axis=1, keepdims=True)*pool.p
        scored = regional_penalty_scores(final.H, T_h, pool.target_selection, J, pool.p, pool.B,
            source.W, pool.score, grid, pool.r)
        winner = int(np.argmin(scored["scores"]))
        state = pooled_shape_at(pool, grid, winner)
        for name in ("scores", "norm_term", "cross_term", "correction_term"):
            arrays[name][index] = scored[name]
        for name, value in (("selected_index", winner), ("selected_a", state.a),
                ("Theta", state.Theta), ("V", state.V), ("context", state.A)):
            arrays[name][index] = value
        centered = J @ pool.target_selection @ state.Theta @ pool.R.T @ source.W
        uncentered = J @ pool.target_selection @ state.beta @ pool.R.T @ source.W
        centering_residual = float(np.max(np.abs(centered-uncentered), initial=0.))
        require(np.allclose(centered, uncentered, atol=1e-10, rtol=1e-8), "union centering changed regional scoring target")
        equations.append(dict(outer=record["outer"], selector=scored["diagnostics"],
            candidate=state.diagnostics, control=marginal.diagnostics, centered_native_maximum_difference=centering_residual))
        if record["outer"] in probe_ids:
            probes.append(dict(outer=record["outer"], **_probe(pool, grid, scored, state, J, source.W, source.evaluation[-1])))
    binding = write_arrays(root, "cell.npz", arrays)
    parents = dict(prepared=prepared.reference, protocol=document["protocol"], source_result=selected.reference,
        control=selected.controls[cell]["reference"], arrays=binding["arrays"])
    manifest = artifact("attribution_selection_fit", document["purpose"], parents, schema_version=5,
        **{name: value for name, value in parents.items() if name != "arrays"}, arrays=binding,
        family=cell[0], population=population, law=law, outer_ids=ids, axes=_fit_axes(),
        basis_columns=list(range(11)), prior_variances=list(VARIANCES), geometry=document["geometry"],
        current_player_ids=list(fixed_pool.current_player_ids), union_player_ids=list(fixed_pool.player_ids),
        source_producer=selected.result["implementation"], control_replay=replay, equations=equations,
        grid_equations=grid.diagnostics, probes=probes,
        costs=dict(statistic_histories=n, annual_likelihoods=5*n, candidate_grid_evaluations=18*n,
            candidate_fits=n, control_replays=n, eigensolve_probes=len(probes), new_responses=0, new_annual_fits=0),
        resources=_cost(started, process_started, root), nomination=None, admission="not_admitted", handoff=None)
    path = root/"fit.json"
    write_json(path, json_values(manifest))
    return identity(path)


def _read_fits(prepared, fits):
    require(len(fits) == 6, "assessment requires six explicit fit manifests")
    cells = {}
    n, ids = len(prepared.document["outer_ids"]), prepared.document["outer_ids"]
    expected_probe_ids = RULES["numerical"]["research_probe_ids" if prepared.document["purpose"] == "research" else "fixture_probe_ids"]
    for path in fits:
        reference = identity(Path(path).resolve(strict=True))
        document = read_artifact(path, "attribution_selection_fit", expected_schema=5)
        cell = tuple(document[name] for name in ("family", "population", "law"))
        require(cell in CELLS and cell not in cells, "duplicate or foreign fit cell")
        require(document["purpose"] == prepared.document["purpose"]
            and document["prepared"] == prepared.reference and document["protocol"] == prepared.document["protocol"]
            and document["source_result"] == prepared.source.reference
            and document["control"] == prepared.source.controls[cell]["reference"]
            and document["source_producer"] == prepared.source.result["implementation"]
            and document["outer_ids"] == ids and document["prior_variances"] == list(VARIANCES)
            and document["basis_columns"] == list(range(11)) and document["geometry"] == prepared.document["geometry"]
            and document["current_player_ids"] == list(prepared.source.source.training[-1]["players"])
            and document["union_player_ids"] == sorted({p for design in prepared.source.source.training for p in design["players"]})
            and document["consumed"] == dict(prepared=prepared.reference, protocol=document["protocol"],
                source_result=prepared.source.reference, control=document["control"], arrays=document["arrays"]["arrays"])
            and document["nomination"] is None and document["admission"] == "not_admitted" and document["handoff"] is None,
            "fit purpose, parents, target identities or rule differ")
        arrays = load_arrays(document["arrays"])
        require(document["axes"] == _fit_axes() and list(arrays) == list(document["axes"])
            and all(value.shape == _fit_shapes(n)[name] for name, value in arrays.items())
            and all(value.dtype == np.dtype("int64" if name in ("outer_ids", "selected_index") else "float64")
                for name, value in arrays.items()) and arrays["outer_ids"].tolist() == ids,
            "fit array names, axes, dimensions, types or outer ids differ")
        index, scores = arrays["selected_index"], arrays["scores"]
        require(np.all((index >= 0) & (index < 18)) and np.array_equal(arrays["selected_a"], np.asarray(VARIANCES)[index])
            and np.all(scores[:, 0] == 0) and all(np.all(arrays[name][:, 0] == 0)
                for name in ("norm_term", "cross_term", "correction_term"))
            and np.allclose(scores, arrays["norm_term"]+arrays["cross_term"]+arrays["correction_term"], atol=1e-10, rtol=1e-8)
            and all(np.all(scores[i, selected] <= scores[i]) and not np.any(scores[i, :selected] == scores[i, selected])
                for i, selected in enumerate(index))
            and np.all(arrays["norm_term"] >= 0) and np.all(arrays["correction_term"] >= -1e-10),
            "fit signed score accounting, exact zero, selected state or tie order differs")
        require([row["outer"] for row in document["control_replay"]] == ids
            and [row["outer"] for row in document["equations"]] == ids
            and [row["outer"] for row in document["probes"]] == expected_probe_ids
            and document["costs"] == dict(statistic_histories=n, annual_likelihoods=5*n, candidate_grid_evaluations=18*n,
                candidate_fits=n, control_replays=n, eigensolve_probes=len(expected_probe_ids), new_responses=0, new_annual_fits=0),
            "fit replay, numerical receipts or work inventory differs")
        grid = document["grid_equations"]
        require(len(grid["covariance_equation_relative_residuals"]) == 18
            and _valid_residuals([grid["equation_relative_residual"], *grid["covariance_equation_relative_residuals"]]),
            "fit fixed-grid equation receipts differ")
        for row in document["equations"]:
            selector = row["selector"]
            require(selector["rank"] == prepared.document["target_rank"]
                and selector["rank_at_tau_factors"] == [prepared.document["target_rank"]]*3
                and selector["cutoff_factors"] == [.1, 1., 10.]
                and type(selector["tau"]) in (int, float) and np.isfinite(selector["tau"]) and selector["tau"] >= 0
                and len(selector["mean_equation_relative_residuals"]) == 18
                and _valid_residuals([selector["reference_equation_relative_residual"],
                    *selector["mean_equation_relative_residuals"], row["centered_native_maximum_difference"]]),
                "fit regional reference rank, cutoff or equation receipt differs")
            for arm in ("candidate", "control"):
                receipt = row[arm]
                require(len(receipt["mean_equation_relative_residuals"]) == 18
                    and _valid_residuals([receipt["equation_relative_residual"], receipt["grid_equation_relative_residual"],
                        *receipt["mean_equation_relative_residuals"]]), "fit state equation receipts differ")
        for row in document["control_replay"]:
            require(set(row["maxima"]) == set(row["tolerance_fractions"]) == {"objectives", "selected_a", "Theta", "V", "context"}
                and all(type(value) in (int, float) and np.isfinite(value) and value >= 0 for value in row["maxima"].values())
                and all(type(value) in (int, float) and np.isfinite(value) and 0 <= value <= 1
                    for value in row["tolerance_fractions"].values()), "fit control replay receipt differs")
        for probe in document["probes"]:
            require(type(probe["verified"]) is bool and bool(probe["checks"])
                and all(type(value) is bool for value in probe["checks"].values())
                and probe["verified"] == all(probe["checks"].values())
                and len(probe["mean_equation_relative_residuals"]) == len(probe["covariance_equation_relative_residuals"]) == 18
                and _valid_residuals([*probe["mean_equation_relative_residuals"], *probe["covariance_equation_relative_residuals"]]),
                "fit independent probe receipts differ")
        cells[cell] = document, reference, arrays
    require(set(cells) == set(CELLS), "incomplete six-cell fit inventory")
    return [cells[cell] for cell in CELLS]


def criterion_status(summary):
    if summary["lower"] > 0:
        return "supported"
    if summary["upper"] < 0:
        return "failed"
    return "inconclusive"


def progress_status(criteria, numerical_status, purpose):
    if numerical_status != "verified":
        return "numerically_unresolved"
    if purpose == "fixture_exercise":
        return "inconclusive"
    if "failed" in criteria:
        return "failed"
    return "supported" if all(status == "supported" for status in criteria) else "inconclusive"


def _summary(values, weights, *, root=None, denominator=None):
    values = np.asarray(values)
    mean, draws = values.mean(), weights @ values
    if denominator is not None:
        divisor, draw_divisor = np.asarray(denominator).mean(), weights @ denominator
        if divisor == 0:
            return dict(mean=None, lower=None, upper=None, reason="zero truth has no recovery ratio")
        mean, draws = mean/divisor, draws/draw_divisor
    if root is not None:
        mean, draws = np.sqrt(mean/root), np.sqrt(draws/root)
    lower, upper = np.quantile(draws, [.025, .975], method="linear")
    return dict(mean=float(mean), lower=float(lower), upper=float(upper))


def _truths(source, population, outer):
    truths = (paired_truths if population == "null" else independent_truths)(source.training, source.basis.p, population, outer)
    family = "paired" if population == "null" else "independent"
    for law in LAWS:
        saved = source.cells[(family, population, law)]["truths"][outer]
        require(saved["outer"] == outer and saved["truth_sha256"] == truth_digest(truths)
            and saved["activation"] == [truth["pairs" if family == "paired" else "activation"] for truth in truths],
            "reconstructed physical truth differs from selected source evidence")
    return truths


def _active(truth, players):
    if "active" in truth:
        return truth["active"]
    positions, n = {player: i for i, player in enumerate(players)}, len(players)
    active = np.zeros(2*n, dtype=bool)
    for pair in truth["pairs"]:
        for player in pair["players"]:
            active[int(pair["role"] == "defense")*n+positions[player]] = pair["active"]
    return active


def _assessment_arrays(n):
    arrays = dict(outer_ids=np.empty(n, dtype=np.int64), candidate_selected_index=np.empty(n, dtype=np.int64),
        candidate_selected_a=np.empty(n), candidate_selected_score=np.empty(n), control_selected_a=np.empty(n),
        physical_active=np.empty((n, 64), dtype=bool),
        truth_regions=np.empty((n, 64, 12)), truth_functionals=np.empty((n, 64, 2)),
        zero_risk=np.empty((n, 3)), prediction_zero=np.empty(n), omitted_detail=np.empty((n, 3)),
        projection_region_error=np.empty((n, 64, 12)), projection_functional_error=np.empty((n, 64, 2)))
    for arm in ("candidate", "control"):
        arrays.update({f"{arm}_{name}": np.empty(shape) for name, shape in (
            ("region_error", (n, 64, 12)), ("functional_error", (n, 64, 2)),
            ("risk", (n, 3)), ("prediction", (n,)), ("prediction_excess", (n,)), ("coupling", (n,)))})
    return arrays


def _assessment_axes():
    axes = dict(outer_ids=["outer"], candidate_selected_index=["outer"], candidate_selected_a=["outer"],
        candidate_selected_score=["outer"], control_selected_a=["outer"], physical_active=["outer", "current_role_player"],
        truth_regions=["outer", "current_role_player", "region"], truth_functionals=["outer", "current_role_player", "functional"],
        zero_risk=["outer", "target"], prediction_zero=["outer"], omitted_detail=["outer", "target"],
        projection_region_error=["outer", "current_role_player", "region"],
        projection_functional_error=["outer", "current_role_player", "functional"])
    for arm in ("candidate", "control"):
        axes.update({f"{arm}_{name}": value for name, value in (
            ("region_error", ["outer", "current_role_player", "region"]),
            ("functional_error", ["outer", "current_role_player", "functional"]), ("risk", ["outer", "target"]),
            ("prediction", ["outer"]), ("prediction_excess", ["outer"]), ("coupling", ["outer"]))})
    return axes


def _cell_summary(document, arrays, purpose):
    population, law, n = document["population"], document["law"], len(arrays["outer_ids"])
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([41001, POPULATIONS.index(population), LAWS.index(law)])))
    indices = rng.integers(0, n, size=(10000, n))
    weights = np.zeros((10000, n))
    np.add.at(weights, (np.repeat(np.arange(10000), n), indices.ravel()), 1./n)
    candidate, baseline, zero = arrays["candidate_risk"][:, 0], arrays["control_risk"][:, 0], arrays["zero_risk"][:, 0]
    candidate_gain, control_gain = -arrays["candidate_prediction_excess"], -arrays["control_prediction_excess"]
    benefit, margin = baseline-candidate, candidate_gain-.99*control_gain
    row = dict(population=population, law=law, records=n,
        regional_benefit=_summary(benefit, weights), control_gain=_summary(control_gain, weights),
        candidate_gain=_summary(candidate_gain, weights), retention_margin=_summary(margin, weights),
        prediction_cost=_summary(arrays["candidate_prediction"]-arrays["control_prediction"], weights),
        prediction_allowance=_summary(.01*control_gain, weights), zero_risk=_summary(zero, weights))
    for arm, values in (("candidate", candidate), ("control", baseline)):
        row.update({f"{arm}_risk": _summary(values, weights), f"{arm}_rms": _summary(values, weights, root=12),
            f"{arm}_ratio": _summary(values, weights, denominator=zero),
            f"{arm}_historical_margin": _summary(.75*zero-values, weights),
            f"{arm}_prediction": _summary(arrays[f"{arm}_prediction"], weights),
            f"{arm}_coupling": _summary(arrays[f"{arm}_coupling"], weights)})
    row["criteria"] = {name: "not_applicable" if population == "null" else
        "inconclusive" if purpose == "fixture_exercise" else criterion_status(row[metric])
        for name, metric in (("regional_benefit", "regional_benefit"), ("positive_control_gain", "control_gain"),
            ("prediction_retention", "retention_margin"))}
    row["progress_status"] = "not_applicable" if population == "null" else progress_status(list(row["criteria"].values()), "verified", purpose)
    row["reason"] = "diagnostic_only" if population == "null" else "fixture_cannot_support_research_progress" if purpose == "fixture_exercise" else None
    diagnostics = []
    players = document["current_player_ids"]
    positions, m = {p: i for i, p in enumerate(players)}, len(players)
    masks = [np.broadcast_to(np.arange(64) < m, (n, 64)), np.broadcast_to(np.arange(64) >= m, (n, 64)),
        arrays["physical_active"], ~arrays["physical_active"]]
    for player in (32, 33, 8):
        for role in range(2):
            mask = np.zeros((n, 64), dtype=bool)
            mask[:, role*m+positions[player]] = True
            masks.append(mask)
    for ti, target in enumerate(TARGETS):
        candidate_risk, control_risk, Z = arrays["candidate_risk"][:, ti], arrays["control_risk"][:, ti], arrays["zero_risk"][:, ti]
        diagnostics.append(dict(population=population, law=law, kind="target", target=target, partition="all",
            candidate_risk=_summary(candidate_risk, weights), control_risk=_summary(control_risk, weights),
            benefit=_summary(control_risk-candidate_risk, weights), zero_risk=_summary(Z, weights),
            candidate_rms=_summary(candidate_risk, weights, root=12 if ti == 0 else 1),
            control_rms=_summary(control_risk, weights, root=12 if ti == 0 else 1),
            omitted_detail=_summary(arrays["omitted_detail"][:, ti], weights)))
        projection = arrays["projection_region_error"] if ti == 0 else arrays["projection_functional_error"][:, :, ti-1:ti]
        for arm in ("candidate", "control"):
            error = arrays[f"{arm}_region_error"] if ti == 0 else arrays[f"{arm}_functional_error"][:, :, ti-1:ti]
            estimation = error-projection
            estimation_risk, cross = np.sum(estimation**2, axis=(1, 2))/64, 2*np.sum(estimation*projection, axis=(1, 2))/64
            require(np.allclose(arrays[f"{arm}_risk"][:, ti], estimation_risk+arrays["omitted_detail"][:, ti]+cross,
                atol=1e-10, rtol=1e-8), "omitted-detail signed recovery accounting differs")
            diagnostics.append(dict(population=population, law=law, kind="omitted_detail", target=target, arm=arm,
                projected_estimation_risk=_summary(estimation_risk, weights),
                omitted_detail=_summary(arrays["omitted_detail"][:, ti], weights), signed_cross=_summary(cross, weights)))
        for partition, mask in zip(PARTITIONS, masks, strict=True):
            errors = [arrays[f"{arm}_region_error"] if ti == 0 else arrays[f"{arm}_functional_error"][:, :, ti-1:ti]
                for arm in ("candidate", "control")]
            risks = [np.sum(error**2*mask[:, :, None], axis=(1, 2))/64 for error in errors]
            diagnostic = dict(population=population, law=law, kind="partition", target=target, partition=partition,
                candidate_risk=_summary(risks[0], weights), control_risk=_summary(risks[1], weights),
                benefit=_summary(risks[1]-risks[0], weights))
            if ti > 0:
                truth_mean = (arrays["truth_functionals"][:, :, ti-1]*mask).sum(axis=1)/64
                diagnostic["truth_mean"] = _summary(truth_mean, weights)
                for arm, error in zip(("candidate", "control"), errors, strict=True):
                    signed = (error[:, :, 0]*mask).sum(axis=1)/64
                    diagnostic[f"{arm}_signed_error"] = _summary(signed, weights)
                    diagnostic[f"{arm}_fitted_mean"] = _summary(truth_mean+signed, weights)
            diagnostics.append(diagnostic)
    selected_scores = arrays["candidate_selected_score"]
    diagnostics.append(dict(population=population, law=law, kind="selected_score", target=TARGETS[0],
        score=_summary(selected_scores, weights), realized_error_minus_zero=_summary(candidate-zero, weights),
        post_selection_optimism=_summary(candidate-zero-selected_scores, weights),
        meaning="selected scores are not post-selection unbiased error or player precision"))
    selections = dict(population=population, law=law,
        candidate=[dict(prior_variance=a, count=int(np.count_nonzero(arrays["candidate_selected_a"] == a))) for a in VARIANCES],
        control=[dict(prior_variance=a, count=int(np.count_nonzero(arrays["control_selected_a"] == a))) for a in VARIANCES],
        candidate_zero=int(np.count_nonzero(arrays["candidate_selected_a"] == 0)), candidate_upper=int(np.count_nonzero(arrays["candidate_selected_a"] == 1)),
        control_zero=int(np.count_nonzero(arrays["control_selected_a"] == 0)), control_upper=int(np.count_nonzero(arrays["control_selected_a"] == 1)))
    return row, diagnostics, selections


def assess(prepared, fits, output):
    started, process_started = time.monotonic(), time.process_time()
    prepared = read_prepared(prepared)
    fitted_cells = _read_fits(prepared, fits)
    selected, purpose = prepared.source, prepared.document["purpose"]
    source = selected.source
    root = output_path(str(output), list(selected.input_roots))
    require(root.is_relative_to(Path(prepared.document["protocol"]["path"]).parent), "assessment output must be beneath its prepared run")
    root.mkdir()
    cells, diagnostics, selections, bindings, reconciliation = [], [], [], [], []
    operators, J, p = shape_operators(source.W), source.recovery[-1], source.basis.p
    gram = deployment_gram(source.evaluation[-1]["X"], source.evaluation[-1]["si"], source.evaluation[-1]["e"], 6)
    B, R = source.basis.B[:, :11], source.basis.p[:, None]*source.basis.B[:, :11]
    fixed_pool = pool_shape_likelihood(source.fixed_populations, source.basis, tuple(range(11)), SEASONS[-1])
    for document, reference, fitted in fitted_cells:
        cell = tuple(document[name] for name in ("family", "population", "law"))
        control = read_resolution_control(selected, cell)
        saved = read_resolution_assessment(selected, cell)
        records = [row for row in source.records if tuple(row[name] for name in ("family", "population", "law")) == cell]
        arrays = _assessment_arrays(len(records))
        arrays["outer_ids"][:] = fitted["outer_ids"]
        arrays["candidate_selected_index"][:] = fitted["selected_index"]
        arrays["candidate_selected_a"][:] = fitted["selected_a"]
        arrays["candidate_selected_score"][:] = fitted["scores"][np.arange(len(records)), fitted["selected_index"]]
        arrays["control_selected_a"][:] = control["selected_a_11"]
        for index, record in enumerate(records):
            populations, _ = read_regularization_source_populations(source, record)
            current = populations[-1]
            truth = _truths(source, cell[1], record["outer"])[-1]
            arrays["physical_active"][index] = _active(truth, current.player_ids)
            arrays["truth_regions"][index] = 40.*J @ truth["raw"] @ operators[0]
            arrays["truth_functionals"][index] = np.hstack([40.*J @ truth["raw"] @ V for V in operators[1:]])
            projected = truth["raw"] @ B @ R.T
            projection = [40.*J @ (projected-truth["raw"]) @ V for V in operators]
            arrays["projection_region_error"][index] = projection[0]
            arrays["projection_functional_error"][index] = np.hstack(projection[1:])
            arrays["omitted_detail"][index] = [np.sum(error**2)/64 for error in projection]
            for arm, theta, context in (("candidate", fitted["Theta"][index], fitted["context"][index]),
                    ("control", control["Theta_11"][index], control["context_11"][index])):
                maps = fixed_pool.target_selection @ theta @ R.T
                scored = realized_shape_errors(maps, context, p=p, xbar=current.xbar, ybar=current.ybar,
                    true_raw=truth["raw"], true_centered=truth["centered"], true_context=truth["context"],
                    J=J, operators=operators, gram=gram, rate=40.)
                for name in ("region_error", "functional_error", "risk", "prediction", "prediction_excess", "coupling"):
                    arrays[f"{arm}_{name}"][index] = scored[name]
                arrays["zero_risk"][index], arrays["prediction_zero"][index] = scored["zero_risk"], scored["prediction_zero"]
        maxima = {name: _close(arrays[actual], saved[name], name) for actual, name in (
            ("control_risk", "adaptive_risk_11"), ("control_prediction_excess", "adaptive_prediction_excess_11"),
            ("control_coupling", "adaptive_coupling_11"), ("control_region_error", "adaptive_region_error_11"),
            ("control_functional_error", "adaptive_functional_error_11"), ("zero_risk", "assessment_zero_risk"),
            ("omitted_detail", "omitted_detail_11"), ("projection_region_error", "projection_region_error_11"),
            ("projection_functional_error", "projection_functional_error_11"))}
        reconciliation.append(dict(population=cell[1], law=cell[2], maxima=maxima))
        row, adjacent, selection = _cell_summary(document, arrays, purpose)
        cells.append(row)
        diagnostics.extend(adjacent)
        selections.append(selection)
        binding = write_arrays(root, f"{cell[1]}-{cell[2]}.npz", arrays)
        require(list(arrays) == list(_assessment_axes()), "assessment array declarations differ")
        bindings.append(dict(population=cell[1], law=cell[2], arrays=binding, axes=_assessment_axes()))
    totals = {name: sum(document["costs"][name] for document, _, _ in fitted_cells) for name in fitted_cells[0][0]["costs"]}
    require(dict(cells=6, **totals) == prepared.document["budget"], "completed work differs from frozen budget")
    numerical_status = "verified" if all(probe["verified"] for document, _, _ in fitted_cells for probe in document["probes"]) else "unresolved"
    criteria = [status for row in cells if row["population"] != "null" for status in row["criteria"].values()]
    status = progress_status(criteria, numerical_status, purpose)
    parents = dict(prepared=prepared.reference, protocol=prepared.document["protocol"], source_result=selected.reference,
        **{f"fit_{i:02d}": reference for i, (_, reference, _) in enumerate(fitted_cells)},
        **{f"errors_{i:02d}": row["arrays"]["arrays"] for i, row in enumerate(bindings)})
    fields = dict(prepared=prepared.reference, protocol=prepared.document["protocol"], source_result=selected.reference,
        fits=[reference for _, reference, _ in fitted_cells], execution_status="complete", numerical_status=numerical_status,
        progress_status=status, cells=cells, diagnostics=diagnostics, selections=selections, errors=bindings,
        exact_completeness=dict(cells=6, **totals), reconciliation=reconciliation,
        numerical=dict(probes=[dict(population=document["population"], law=document["law"], **probe)
            for document, _, _ in fitted_cells for probe in document["probes"]],
            equations=[dict(population=document["population"], law=document["law"], grid=document["grid_equations"],
                records=document["equations"]) for document, _, _ in fitted_cells]),
        target_rank=prepared.document["target_rank"], units=RULES["units"], limits=LIMITS,
        interval_meaning="mean experimental performance across complete outer records; conditional on fixed designs and exposed truth populations",
        costs=dict(fits=[document["resources"] for document, _, _ in fitted_cells]),
        source_producer=selected.result["implementation"], nomination=None, admission="not_admitted", handoff=None)
    from attribution_selection_report import render_reports
    report = render_reports(root, dict(purpose=purpose, **fields))
    fields.update(report)
    assessment = artifact("attribution_selection_assessment", purpose, parents, schema_version=5,
        **fields, resources=_cost(started, process_started, root))
    path = root/"assessment.json"
    write_json(path, json_values(assessment))
    result = artifact("attribution_selection_result", purpose,
        dict(assessment=identity(path), **parents,
            **{f"report_{i:02d}": reference for i, reference in enumerate(report["reports"])},
            **{f"figure_{i:02d}": reference for i, reference in enumerate(report["figures"])}), schema_version=5,
        assessment=identity(path), prepared=prepared.reference, protocol=prepared.document["protocol"],
        **{name: fields[name] for name in ("execution_status", "numerical_status", "progress_status", "cells",
            "exact_completeness", "reports", "figures", "limits", "source_producer", "nomination", "admission", "handoff")},
        resources=_cost(started, process_started, root))
    path = root/"result.json"
    write_json(path, json_values(result))
    return identity(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    preparation = commands.add_parser("prepare")
    preparation.add_argument("--source-result", required=True)
    preparation.add_argument("--purpose", choices=("research", "fixture_exercise"), required=True)
    preparation.add_argument("--output", required=True)
    fitting = commands.add_parser("fit")
    fitting.add_argument("--prepared", required=True)
    fitting.add_argument("--population", choices=POPULATIONS, required=True)
    fitting.add_argument("--law", choices=LAWS, required=True)
    fitting.add_argument("--output", required=True)
    assessment = commands.add_parser("assess")
    assessment.add_argument("--prepared", required=True)
    assessment.add_argument("--fits", nargs="+", required=True)
    assessment.add_argument("--output", required=True)
    arguments = vars(parser.parse_args(argv))
    command = arguments.pop("command")
    try:
        reference = dict(prepare=prepare, fit=fit, assess=assess)[command](**arguments)
    except (InputContractError, OSError, ValueError, KeyError, np.linalg.LinAlgError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(reference, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
