"""04h's finite pooled-history risk and penalty-selection diagnosis."""

import argparse
from dataclasses import dataclass
from pathlib import Path
import os
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
    fit_pooled_shape, pooled_shape_grid, shape_mean, validate_pooling_basis,
)
from hockey_stats.attribution_data import (
    RegularizationSourceSlice, exposure_centering, pool_shape_likelihood, read_regularization_source_record,
    read_regularization_source_slice,
)
from hockey_stats.attribution_prediction import (
    current_player_rows, deployment_gram, expected_excess_prediction_terms,
    realized_shape_errors,
)
from hockey_stats.attribution_simulation import (
    independent_truths, known_shape_moments, paired_truths, shape_operators,
)
from hockey_stats.captures import InputContractError
from hockey_stats.chance_cli import identity, output_path, read_json


SPEC = Path(__file__).resolve().parents[2] / "docs/specs/04h-attribution-resolution.md"
RESEARCH_ROOT = Path("/Volumes/Expansion/hockey-stats/runs")
SOURCE_RESULT_SHA256 = "84bb4d034bb2213ce8b1cf0cf91fe54713fa7ba797e684f329838b16d05266a6"
SOURCE_PROTOCOL_SHA256 = "9e8266d1b0f7883d284e677be1e607f3cd8593264c3a5e95e9909acbfb3b8ef2"
CONTEXT_SHA256 = "8b1f9bfd2ba48acf81f7c23db97d5e37c81bc2e17cec86666f0aece4551a49ac"
BASIS_SHA256 = "649a49ecba19de5df609d6980d9de76491afa13e9108df0d8e6500659886cc51"
POPULATIONS = ("sparse", "diffuse", "null")
LAWS = ("gaussian", "game_pace")
SEASONS = tuple(f"{year}{year + 1}" for year in range(2021, 2026))
CELLS = tuple(("paired" if population == "null" else "independent", population, law)
              for population in POPULATIONS for law in LAWS)
VARIANCES = (0., *np.power(10., np.arange(-8., .25, .5)).tolist())
CONDITIONS = (
    dict(name="base", alpha=1., copies=1, columns=list(range(40))),
    dict(name="half_effect", alpha=.5, copies=1, columns=list(range(40))),
    dict(name="double_games", alpha=1., copies=2, columns=list(range(40))),
    dict(name="broad", alpha=1., copies=1, columns=list(range(11))),
)
TARGETS = ("twelve_region_vector", "within_20_ft", "lateral_redistribution")
SOURCE_SCORES = ("R_control", "R_zero", "P_control", "P_zero")
PARTITIONS = ("offense", "attempts_allowed", "physically_active", "physically_inactive",
              "entrant_32_offense", "entrant_32_attempts_allowed", "entrant_33_offense",
              "entrant_33_attempts_allowed", "returner_8_offense", "returner_8_attempts_allowed")
RULES = dict(
    cells=[dict(family=family, population=population, law=law) for family, population, law in CELLS],
    seasons=list(SEASONS), conditions=list(CONDITIONS), prior_variances=list(VARIANCES),
    targets=list(TARGETS), rate=40., recovery_denominator=64, final_player_rank=60,
    adaptive_conditions=["base", "broad"], null_conditions=["base", "double_games", "broad"],
    null_aliases=dict(half_effect="base"),
    selection=dict(training="gaussian working marginal likelihood", reference="mean exact twelve-region calibration risk",
                   tie_order="smaller prior variance", continuous_refinement=False),
    bootstrap=dict(resamples=10000, seed=40901, population_ids=dict(sparse=0, diffuse=1, null=2),
                   law_ids=dict(gaussian=0, game_pace=1), bit_generator="PCG64", interval=[.025, .975],
                   quantile="linear", shared_indices=True),
    numerical=dict(equation_residual_max=1e-8, atol=1e-10, rtol=1e-8,
                   research_probes=[[100, "base"], [199, "broad"]], fixture_probes=[[1, "base"], [1, "broad"]]),
    units="squared attempts per 60 team minutes", admission="not_admitted", nomination=None, handoff=None,
)
LIMITS = [
    "four teams with eight slots per team and randomized deployment are a conditional synthetic design",
    "the inseparable players 26 and 31 contribute their identifiable average with weight two; their difference is not_estimable",
    "player 8 returns in a different slot with a potentially changed physical field; constant pooling is misspecified",
    "entrants 32 and 33 borrow no predecessor observations; retired players remain nuisance rows",
    "eleven spatial modes omit physical detail; the player target remains the full identifiable space",
    "annual and pooled contrasts change temporal assumptions and penalty selection; eleven modes also change representation",
    "game doubling means independent complete game copies with independent pace, not longer exposure under shared pace",
    "known-law fixed-family risks are conditional expected risks, not lower bounds for other estimators or player intervals",
    "adaptive realized errors include response selection; fixed-variance formulas do not describe them",
    "mean-risk intervals condition on the calibration set and selected reference; reference-selection uncertainty is omitted",
    "these previously examined cases supply no fresh confirmation and no equivalence or noninferiority claim",
    "real spatial deployment information is unavailable; similar minutes do not imply similar lineup information",
    "spatial inverse-share-weighted prediction does not assess fitted volume or complete-intensity validity",
    "no result admits chance valuation, calibrated uncertainty, real-player recovery or published player ability",
]


@dataclass(frozen=True)
class Prepared:
    reference: dict
    document: dict
    protocol: dict
    source: RegularizationSourceSlice


def _budget(purpose):
    n = 100 if purpose == "research" else 1
    return dict(cells=6, outer_ids=2*n, calibration_per_cell=n, assessment_per_cell=n,
                nonnull_grid_records=576*n, analytic_null_grid_records=108,
                pooled_point_fits=12*n, annual_control_histories=6*n,
                annual_control_states=30*n, eigensolve_probes=12,
                new_responses=0, new_annual_fits=0)


def _cost(started, process_started, root=None):
    return dict(**resources(started), process_seconds=time.process_time()-process_started,
                output_bytes=sum(path.stat().st_size for path in root.rglob("*") if path.is_file()) if root else 0,
                output_bytes_scope="tree_before_current_manifest_serialization")


def _split(purpose):
    n = 100 if purpose == "research" else 1
    return dict(calibration=list(range(n)), assessment=list(range(n, 2*n)))


def _context(path):
    reference = identity(Path(path).resolve(strict=True))
    require(reference["sha256"] == CONTEXT_SHA256, "04a contextual result digest differs")
    document = read_json(linked_path(reference))
    annual = [row for row in document["population"]["annual"] if row["population"] == "unblocked_spatial"]
    exposure = [row for row in document["resolution"]["exposure_quartiles"] if row["benchmark"] == "unblocked_spatial"]
    require([row["season"] for row in annual] == list(SEASONS)
            and {row["role"] for row in exposure} == {"offense", "suppression"}, "04a context population differs")
    return reference, dict(annual=[{name: row[name] for name in
        ("season", "current_players", "league_team_rate_per_60", "team_seconds", "recorded_attempts")} for row in annual],
        exposure_quartiles=[dict(benchmark=row["benchmark"], role=row["role"],
            cutpoints_seconds=row["cutpoints_seconds"], groups=[{key: group[key] for key in
                ("quartile", "players", "minimum_seconds", "maximum_seconds")} for group in row["groups"]])
            for row in exposure], synthetic_mean_minutes=742.5, synthetic_rate=40.,
        final_median_minutes=exposure[0]["cutpoints_seconds"][1]/60.,
        meaning="context only; equal minutes do not imply equal lineup information", real_spatial_deployment_spectrum="unavailable")


def _source(source_result, purpose):
    reference = identity(Path(source_result).resolve(strict=True))
    if purpose == "research":
        require(reference["sha256"] == SOURCE_RESULT_SHA256, "04g result digest differs from the pinned research source")
    source = read_regularization_source_slice(reference, CELLS, _split(purpose)["assessment"])
    require(source.result["purpose"] == purpose, "source purpose differs from execution purpose")
    if purpose == "research":
        require(source.result["protocol"]["sha256"] == SOURCE_PROTOCOL_SHA256
                and source.basis.sha256 == BASIS_SHA256, "04g source protocol or semantic basis differs")
    validate_pooling_basis(source.basis)
    shape_operators(source.W)
    return source


def _inventory(source):
    return dict(cells=[dict(family=family, population=population, law=law, **source.cells[(family, population, law)])
                       for family, population, law in CELLS],
                assessment_records=[dict(family=row["family"], population=row["population"], law=row["law"], outer=row["outer"],
                    statistics=row["statistics"], history=row["annual"]["history"],
                    truth_sha256=row["truth_sha256"], saved_scores=row["saved_scores"]) for row in source.records])


def _geometry(source):
    W, near, lateral = shape_operators(source.W)
    return dict(native=ordered_array_digest(dict(p=source.basis.p)),
                basis=source.basis.sha256,
                regions=ordered_array_digest(dict(W=W, within_20_ft=near, lateral_redistribution=lateral)),
                entities=ordered_array_digest({SEASONS[i]: np.asarray(design["players"], dtype=np.int64)
                                               for i, design in enumerate(source.training)}))


def prepare(source_result, real_context, purpose, output):
    started, process_started = time.monotonic(), time.process_time()
    require(purpose in ("research", "fixture_exercise"), "invalid preparation purpose")
    source = _source(source_result, purpose)
    context_ref, context = _context(real_context)
    root = output_path(str(output), [str(Path(source.reference["path"]).parent),
                                     *source.input_roots])
    if purpose == "research":
        require(root.is_relative_to(RESEARCH_ROOT) and root.name.startswith("attribution-04h-"),
                "research outputs require an exclusive external attribution-04h directory")
    root.mkdir()
    snapshot = root/"spec-snapshot.md"
    with snapshot.open("xb") as destination:
        destination.write(SPEC.read_bytes())
    consumed = dict(source_result=source.reference, source_protocol=source.result["protocol"],
                    source_prepared=source.result["prepared"], source_assessment=source.result["assessment"],
                    spec_snapshot=identity(snapshot), real_context=context_ref)
    inventory, geometry = _inventory(source), _geometry(source)
    context["synthetic_mean_minutes"] = float(source.training[-1]["player_exposure"].mean()/60)
    fields = dict(**RULES, split=_split(purpose), budget=_budget(purpose), geometry=geometry,
                  source_inventory=inventory, source_producer=source.result["implementation"],
                  context=context, target_rank=source.protocol["recovery_receipts"][-1]["rank"],
                  source_exposure="research_exposed" if purpose == "research" else "fixture_exercise")
    protocol = artifact("attribution_resolution_protocol", purpose, consumed, schema_version=5,
                        **consumed, **fields, resources=_cost(started, process_started, root))
    protocol_path = root/"protocol.json"
    write_json(protocol_path, json_values(protocol))
    document = artifact("attribution_resolution_prepared", purpose,
                        dict(protocol=identity(protocol_path), **consumed), schema_version=5,
                        protocol=identity(protocol_path), **consumed, **fields,
                        resources=_cost(started, process_started, root))
    path = root/"prepared.json"
    write_json(path, json_values(document))
    return identity(path)


def read_prepared(path):
    reference = identity(Path(path).resolve(strict=True))
    document = read_artifact(path, "attribution_resolution_prepared", expected_schema=5)
    protocol = read_artifact(linked_path(document["protocol"]), "attribution_resolution_protocol", expected_schema=5)
    purpose = document["purpose"]
    source = _source(linked_path(document["source_result"]), purpose)
    context_ref, context = _context(linked_path(document["real_context"]))
    context["synthetic_mean_minutes"] = float(source.training[-1]["player_exposure"].mean()/60)
    expected = dict(**RULES, split=_split(purpose), budget=_budget(purpose), geometry=_geometry(source),
                    source_inventory=_inventory(source), source_producer=source.result["implementation"],
                    context=context, target_rank=source.protocol["recovery_receipts"][-1]["rank"],
                    source_exposure="research_exposed" if purpose == "research" else "fixture_exercise")
    require(protocol["purpose"] == purpose and document["real_context"] == context_ref
            and all(document.get(name) == protocol.get(name) == json_values(value) for name, value in expected.items())
            and document["context"] == context,
            "04h prepared science, inventory, geometry or contextual contract differs")
    require(document["consumed"] == dict(protocol=document["protocol"], **protocol["consumed"])
            and all(document[name] == value for name, value in protocol["consumed"].items())
            and document["source_result"] == source.reference,
            "04h prepared parents differ")
    return Prepared(reference, document, protocol, source)


def _truths(source, population, outer):
    from hockey_stats.attribution_simulation import truth_digest

    truths = (paired_truths if population == "null" else independent_truths)(source.training, source.basis.p, population, outer)
    family = "paired" if population == "null" else "independent"
    for law in LAWS:
        saved = source.cells[(family, population, law)]["truths"][outer]
        require(saved["outer"] == outer and saved["truth_sha256"] == truth_digest(truths)
                and saved["activation"] == [truth["pairs" if family == "paired" else "activation"] for truth in truths],
                "deterministic physical truth differs from its selected source manifest")
    return truths


def _fixed_curves(moments, K_values, B, p, J, S, operators, true_raw, evaluation, xbar):
    R = p[:, None]*B
    recovery = {name: np.empty((len(VARIANCES), len(TARGETS)))
                for name in ("risk", "bias_squared", "sampling_variance", "zero_risk")}
    prediction, coupling = np.empty(len(VARIANCES)), np.empty(len(VARIANCES))
    F = J @ S
    gram = deployment_gram(evaluation["X"], evaluation["si"], evaluation["e"], len(xbar))
    for index, K in enumerate(K_values):
        for target, (V, covariance) in enumerate(zip(operators, moments["covariances"], strict=True)):
            D, truth = R.T @ V, J @ true_raw @ V
            error = F @ K @ moments["m"] @ D-truth
            bias = 40.**2/64 * float(np.sum(error**2))
            variance = 40.**2/64 * float(np.sum((F @ K @ covariance)*(F @ K)))
            require(variance >= -1e-10, "negative collapsed recovery sampling variance")
            recovery["bias_squared"][index, target] = bias
            recovery["sampling_variance"][index, target] = max(0., variance)
            recovery["risk"][index, target] = bias+max(0., variance)
            recovery["zero_risk"][index, target] = 40.**2/64 * float(np.sum(truth**2))
        terms = expected_excess_prediction_terms(gram, xbar, true_raw, S, K, moments["m"],
            moments["prediction_covariance"], moments["context_cross_score"], p=p, B=B)
        prediction[index], coupling[index] = terms["delta"], terms["coupling"]
    return dict(**recovery, prediction_excess=prediction, coupling=coupling)


def _active(truth, players):
    if "active" in truth:
        return truth["active"]
    positions, n = {player: i for i, player in enumerate(players)}, len(players)
    active = np.zeros(2*n, dtype=bool)
    for pair in truth["pairs"]:
        for player in pair["players"]:
            active[int(pair["role"] == "defense")*n+positions[player]] = pair["active"]
    return active


def _close(actual, expected, label):
    actual, expected = np.asarray(actual), np.asarray(expected)
    require(actual.shape == expected.shape and np.allclose(actual, expected, atol=1e-10, rtol=1e-8),
            label+": source score reconciliation failed")
    return float(np.max(np.abs(actual-expected), initial=0.))


def _probe(pooled, state, grid, moments, B, p, J, operators, truth, evaluation, population):
    eigenvalues, eigenvectors = np.linalg.eigh(pooled.H)
    K_values, objectives = [], []
    for a in VARIANCES:
        K = np.zeros_like(pooled.H) if a == 0 else (eigenvectors*(a/(1+a*eigenvalues))) @ eigenvectors.T
        K_values.append(K)
        objectives.append(0. if a == 0 else B.shape[1]*np.log1p(a*eigenvalues).sum()
                          -np.sum(pooled.score*(K @ pooled.score)))
    winner = int(np.argmin(objectives))
    centered = exposure_centering(pooled.u) @ (K_values[winner] @ pooled.score)
    curves = _fixed_curves(moments, K_values, B, p, J, pooled.selections[-1], operators,
                           truth["raw"], evaluation, population.xbar)
    primary = _fixed_curves(moments, grid.covariances, B, p, J, pooled.selections[-1], operators,
                            truth["raw"], evaluation, population.xbar)
    P = exposure_centering(pooled.u)
    covariance = P @ K_values[winner] @ P.T
    current_maps = pooled.target_selection @ centered @ pooled.R.T
    ybar_h = population.ybar-population.ybar.sum(axis=1, keepdims=True)*p
    context = ybar_h-population.xbar @ current_maps
    actual_maps = pooled.target_selection @ state.Theta @ pooled.R.T
    eigen_means = P @ (np.asarray(K_values) @ pooled.score)
    factor_means = P @ (grid.covariances @ pooled.score)
    eigen_covariances = P @ np.asarray(K_values) @ P.T
    factor_covariances = P @ grid.covariances @ P.T
    eigen_maps = pooled.target_selection @ eigen_means @ pooled.R.T
    factor_maps = pooled.target_selection @ factor_means @ pooled.R.T
    eigen_context = ybar_h-population.xbar @ eigen_maps
    factor_context = ybar_h-population.xbar @ factor_maps
    identity_matrix = np.eye(len(pooled.H))
    covariance_residuals = [0. if a == 0 else float(np.linalg.norm((pooled.H+identity_matrix/a) @ K-identity_matrix)
        /max(1., np.linalg.norm(identity_matrix))) for a, K in zip(VARIANCES, K_values, strict=True)]
    mean_residuals = [0. if a == 0 else float(np.linalg.norm((pooled.H+identity_matrix/a) @ (K @ pooled.score)-pooled.score)
        /max(1., np.linalg.norm(pooled.score))) for a, K in zip(VARIANCES, K_values, strict=True)]
    all_predictions_agree, maximum_grid_prediction_difference = True, 0.
    for index in range(len(VARIANCES)):
        for start in range(0, len(evaluation["si"]), 256):
            X, si = evaluation["X"][start:start+256], evaluation["si"][start:start+256]
            eigen_prediction = pooled.r*(eigen_context[index][si]+X @ eigen_maps[index])
            factor_prediction = pooled.r*(factor_context[index][si]+X @ factor_maps[index])
            all_predictions_agree = all_predictions_agree and np.allclose(eigen_prediction, factor_prediction, atol=1e-10, rtol=1e-8)
            maximum_grid_prediction_difference = max(maximum_grid_prediction_difference,
                float(np.max(np.abs(eigen_prediction-factor_prediction))))
    selected_predictions_agree, maximum_prediction_difference = True, 0.
    for start in range(0, len(evaluation["si"]), 256):
        X, si = evaluation["X"][start:start+256], evaluation["si"][start:start+256]
        eigen_prediction = pooled.r*(context[si]+X @ current_maps)
        actual_prediction = pooled.r*(state.A[si]+X @ actual_maps)
        selected_predictions_agree = selected_predictions_agree and np.allclose(eigen_prediction, actual_prediction, atol=1e-10, rtol=1e-8)
        maximum_prediction_difference = max(maximum_prediction_difference,
                                           float(np.max(np.abs(eigen_prediction-actual_prediction))))
    checks = dict(covariance=np.allclose(K_values, grid.covariances, atol=1e-10, rtol=1e-8),
                  objectives=np.allclose(objectives, state.objectives, atol=1e-10, rtol=1e-8),
                  winning_objective=np.isclose(objectives[winner], state.objectives[int(np.argmin(state.objectives))], atol=1e-10, rtol=1e-8),
                  all_grid_posterior=np.allclose(eigen_means, factor_means, atol=1e-10, rtol=1e-8),
                  all_grid_centered_covariance=np.allclose(eigen_covariances, factor_covariances, atol=1e-10, rtol=1e-8),
                  all_grid_context=np.allclose(eigen_context, factor_context, atol=1e-10, rtol=1e-8),
                  all_grid_predictions=all_predictions_agree,
                  equations=max(covariance_residuals+mean_residuals) <= 1e-8,
                  posterior=np.allclose(centered, state.Theta, atol=1e-10, rtol=1e-8),
                  centered_covariance=np.allclose(covariance, state.V, atol=1e-10, rtol=1e-8),
                  context=np.allclose(context, state.A, atol=1e-10, rtol=1e-8),
                  predictions=selected_predictions_agree,
                  risk=all(np.allclose(curves[name], primary[name], atol=1e-10, rtol=1e-8) for name in curves))
    return dict(winner=VARIANCES[winner], training_winner=state.a, changed_winner=VARIANCES[winner] != state.a,
                checks={name: bool(value) for name, value in checks.items()}, verified=all(checks.values()),
                maximum_covariance_difference=float(np.max(np.abs(np.asarray(K_values)-grid.covariances))),
                maximum_objective_difference=float(np.max(np.abs(np.asarray(objectives)-state.objectives))),
                maximum_coefficient_difference=float(np.max(np.abs(centered-state.Theta))),
                maximum_prediction_difference=maximum_prediction_difference,
                maximum_grid_coefficient_difference=float(np.max(np.abs(eigen_means-factor_means))),
                maximum_grid_prediction_difference=maximum_grid_prediction_difference,
                covariance_equation_relative_residuals=covariance_residuals,
                mean_equation_relative_residuals=mean_residuals,
                maximum_risk_difference=float(np.max(np.abs(curves["risk"]-primary["risk"]))))


def fit(prepared, population, law, output):
    started, process_started = time.monotonic(), time.process_time()
    prepared = read_prepared(prepared)
    source, document = prepared.source, prepared.document
    require(population in POPULATIONS and law in LAWS, "invalid 04h cell")
    family = "paired" if population == "null" else "independent"
    records = [row for row in source.records if (row["family"], row["population"], row["law"]) == (family, population, law)]
    assessment_ids, n = document["split"]["assessment"], len(document["split"]["assessment"])
    require([row["outer"] for row in records] == assessment_ids, "cell assessment records are missing, duplicated or reordered")
    root = output_path(str(output), source.input_roots)
    if document["purpose"] == "research":
        require(root.is_relative_to(Path(document["protocol"]["path"]).parent), "fit output must be beneath its prepared run")
    root.mkdir()
    operators, J = shape_operators(source.W), source.recovery[-1]
    fixed_populations = source.fixed_populations
    pools = {d: pool_shape_likelihood(fixed_populations, source.basis, tuple(range(d)), SEASONS[-1]) for d in (40, 11)}
    grids = {(40, copies): pooled_shape_grid(copies*pools[40].H, VARIANCES) for copies in (1, 2)}
    grids[(11, 1)] = pooled_shape_grid(pools[11].H, VARIANCES)
    null = population == "null"
    condition_indices = [0, 2, 3] if null else list(range(4))
    prefix = () if null else (2*n,)
    arrays = {name: np.empty((*prefix, len(condition_indices), len(VARIANCES), 3))
              for name in ("risk", "bias_squared", "sampling_variance", "zero_risk")}
    arrays.update({name: np.empty((*prefix, len(condition_indices), len(VARIANCES)))
                   for name in ("prediction_excess", "coupling")})
    moments_by_probe = {}
    for outer in ([0] if null else range(2*n)):
        truths = _truths(source, population, outer)
        for ci, condition_id in enumerate(condition_indices):
            condition = CONDITIONS[condition_id]
            d, copies, alpha = len(condition["columns"]), condition["copies"], condition["alpha"]
            pool, B = pools[d], source.basis.B[:, condition["columns"]]
            moments = known_shape_moments(source.training, truths, pool.selections, B, source.basis.p,
                law=law, alpha=alpha, copies=copies, operators=operators)
            _close(moments["H"], copies*pool.H, "known-law information")
            values = _fixed_curves(moments, grids[(d, copies)].covariances,
                B, source.basis.p, J, pool.selections[-1], operators, alpha*truths[-1]["raw"],
                source.evaluation[-1], fixed_populations[-1].xbar)
            for name, value in values.items():
                arrays[name][ci if null else (outer, ci)] = value
            if condition_id in (0, 3) and (null or outer in (n, 2*n-1)):
                moments_by_probe[(outer, d)] = moments
    calibration_indices = {}
    for ci, condition_id in enumerate(condition_indices):
        values = arrays["risk"][ci, :, 0] if null else arrays["risk"][:n, ci, :, 0].mean(axis=0)
        calibration_indices[CONDITIONS[condition_id]["name"]] = int(np.argmin(values))
    if null:
        require(all(index == 0 for index in calibration_indices.values()), "analytic null must select exact zero")
    arrays["calibration_index"] = np.asarray(list(calibration_indices.values()), dtype=np.int64)
    arrays["annual_risk"] = np.empty((n, 3))
    arrays["annual_prediction_excess"] = np.empty(n)
    arrays["annual_coupling"] = np.empty(n)
    arrays["annual_region_error"] = np.empty((n, 64, 12))
    arrays["annual_functional_error"] = np.empty((n, 64, 2))
    arrays["physical_active"] = np.empty((n, 64), dtype=bool)
    arrays["truth_regions"] = np.empty((n, 64, 12))
    arrays["truth_functionals"] = np.empty((n, 64, 2))
    arrays["assessment_zero_risk"] = np.empty((n, 3))
    arrays["source_control_scores"] = np.empty((n, 4))
    for d in (40, 11):
        arrays.update({f"{name}_{d}": np.empty(shape) for name, shape in (
            ("selected_a", (n,)), ("objectives", (n, 18)), ("Theta", (n, 68, d)),
            ("V", (n, 68, 68)), ("context", (n, 6, 656)), ("adaptive_risk", (n, 3)),
            ("adaptive_prediction_excess", (n,)), ("adaptive_coupling", (n,)),
            ("adaptive_region_error", (n, 64, 12)), ("adaptive_functional_error", (n, 64, 2)),
            ("projection_region_error", (n, 64, 12)), ("projection_functional_error", (n, 64, 2)),
            ("omitted_detail", (n, 3)))})
    source_audit, probes, solve_receipts = [], [], []
    evaluation = source.evaluation[-1]
    gram = deployment_gram(evaluation["X"], evaluation["si"], evaluation["e"],
                           len(source.training[-1]["strata"]))
    for index, record in enumerate(records):
        outer = record["outer"]
        populations, states = read_regularization_source_record(source, record)
        audit = [dict(season=season, control=reference,
                      shape_equation_relative_residual=state.shape.diagnostics["equation_relative_residual"],
                      volume_equation_relative_residual=state.volume.diagnostics["equation_relative_residual"],
                      scale=dict(a=state.shape.a, q=state.shape.q, status=state.shape.scale["status"],
                                 own_reasons=state.shape.scale["own_reasons"],
                                 inherited_limitation=state.shape.scale["inherited_limitation"]))
                 for season, reference, state in zip(SEASONS, record["annual"]["history"], states, strict=True)]
        truths = _truths(source, population, outer)
        current, truth = populations[-1], truths[-1]
        control = states[-1]
        maps = shape_mean(control)[current_player_rows(control, current.player_ids)]
        scoring = dict(p=source.basis.p, xbar=current.xbar, ybar=current.ybar,
            true_raw=truth["raw"], true_centered=truth["centered"], true_context=truth["context"],
            J=J, operators=operators, gram=gram)
        annual = realized_shape_errors(maps, control.shape.A, **scoring)
        saved = record["saved_scores"]
        source_audit.append(dict(outer=outer, annual=audit,
            residuals={name: _close(value, saved[name], "saved "+name) for name, value in (
                ("R_control", annual["risk"][0]), ("R_zero", annual["zero_risk"][0]),
                ("P_control", annual["prediction"]), ("P_zero", annual["prediction_zero"]))}))
        for name in ("risk", "prediction_excess", "coupling", "region_error", "functional_error"):
            arrays["annual_"+name][index] = annual[name]
        arrays["source_control_scores"][index] = [saved[name] for name in SOURCE_SCORES]
        arrays["physical_active"][index] = _active(truth, current.player_ids)
        arrays["truth_regions"][index] = 40.*J @ truth["raw"] @ operators[0]
        arrays["truth_functionals"][index] = np.hstack([40.*J @ truth["raw"] @ V for V in operators[1:]])
        arrays["assessment_zero_risk"][index] = annual["zero_risk"]
        for d in (40, 11):
            pool = pool_shape_likelihood(populations, source.basis, tuple(range(d)), SEASONS[-1])
            require(np.array_equal(pool.H, pools[d].H), "response changed pooled fixed information")
            state = fit_pooled_shape(pool, VARIANCES, grid=grids[(d, 1)])
            solve_receipts.append(dict(outer=outer, spatial_modes=d, **state.diagnostics))
            B, R = source.basis.B[:, :d], source.basis.p[:, None]*source.basis.B[:, :d]
            maps = pool.selections[-1] @ state.Theta @ R.T
            scored = realized_shape_errors(maps, state.A, **scoring)
            for name, value in (("selected_a", state.a), ("objectives", state.objectives), ("Theta", state.Theta),
                                ("V", state.V), ("context", state.A)):
                arrays[f"{name}_{d}"][index] = value
            for name in ("risk", "prediction_excess", "coupling", "region_error", "functional_error"):
                arrays[f"adaptive_{name}_{d}"][index] = scored[name]
            projected = truth["raw"] @ B @ R.T
            projection_errors = [40.*J @ (projected-truth["raw"]) @ V for V in operators]
            arrays[f"projection_region_error_{d}"][index] = projection_errors[0]
            arrays[f"projection_functional_error_{d}"][index] = np.hstack(projection_errors[1:])
            arrays[f"omitted_detail_{d}"][index] = [np.sum(error**2)/64 for error in projection_errors]
            if (d == 40 and outer == n) or (d == 11 and outer == 2*n-1):
                probe_moments = moments_by_probe[(0 if null else outer, d)]
                probe = _probe(pool, state, grids[(d, 1)], probe_moments,
                    B, source.basis.p, J, operators, truth, source.evaluation[-1], current)
                probes.append(dict(outer=outer, condition="base" if d == 40 else "broad", **probe))
    binding = write_arrays(root, "cell.npz", arrays)
    axes = _array_axes(null, n)
    require(list(arrays) == list(axes), "cell array declarations and ordering differ")
    manifest = artifact("attribution_resolution_fit", document["purpose"],
        dict(prepared=prepared.reference, protocol=document["protocol"], source_result=source.reference, arrays=binding["arrays"]),
        schema_version=5, prepared=prepared.reference, protocol=document["protocol"], source_result=source.reference,
        source_producer=source.result["implementation"], family=family, population=population, law=law,
        split=document["split"], conditions=[CONDITIONS[i]["name"] for i in condition_indices],
        null_aliases=dict(half_effect="base") if null else {}, arrays=binding, axes=axes,
        targets=list(TARGETS), prior_variances=list(VARIANCES), source_score_names=list(SOURCE_SCORES),
        basis_columns={str(d): list(range(d)) for d in (40, 11)},
        current_player_ids=list(source.training[-1]["players"]),
        union_player_ids=list(pools[40].player_ids), geometry=document["geometry"],
        calibration_selection={name: dict(index=index, prior_variance=VARIANCES[index], loss="mean exact twelve-region risk",
             truth_ids=[] if null else document["split"]["calibration"], analytic_null=null)
             for name, index in calibration_indices.items()},
        source_control_audit=source_audit, probes=probes, pooled_equations=solve_receipts,
        grid_equations={f"{d}_spatial_modes_{copies}_independent_copies": grid.diagnostics
                        for (d, copies), grid in grids.items()},
        costs=dict(nonnull_grid_records=0 if null else 2*n*4*18,
                   analytic_null_grid_records=3*18 if null else 0,
                   pooled_point_fits=2*n, annual_control_histories=n, annual_control_states=5*n,
                   eigensolve_probes=len(probes), new_responses=0, new_annual_fits=0),
        resources=_cost(started, process_started, root), admission="not_admitted", nomination=None, handoff=None)
    path = root/"fit.json"
    write_json(path, json_values(manifest))
    return identity(path)


def _array_axes(null, n):
    fixed = (["condition", "prior_variance"] if null else ["outer", "condition", "prior_variance"])
    axes = {name: [*fixed, "target"] for name in ("risk", "bias_squared", "sampling_variance", "zero_risk")}
    axes.update({name: fixed for name in ("prediction_excess", "coupling")})
    axes["calibration_index"] = ["condition"]
    axes.update(annual_risk=["assessment_outer", "target"], annual_prediction_excess=["assessment_outer"],
        annual_coupling=["assessment_outer"],
        annual_region_error=["assessment_outer", "current_role_player", "region"],
        annual_functional_error=["assessment_outer", "current_role_player", "functional"],
        physical_active=["assessment_outer", "current_role_player"],
        truth_regions=["assessment_outer", "current_role_player", "region"],
        truth_functionals=["assessment_outer", "current_role_player", "functional"],
        assessment_zero_risk=["assessment_outer", "target"], source_control_scores=["assessment_outer", "source_score"])
    for d in (40, 11):
        axes.update({f"{name}_{d}": value for name, value in (
            ("selected_a", ["assessment_outer"]), ("objectives", ["assessment_outer", "prior_variance"]),
            ("Theta", ["assessment_outer", "union_role_player", f"spatial_mode_{d}"]),
            ("V", ["assessment_outer", "union_role_player", "union_role_player"]),
            ("context", ["assessment_outer", "final_context", "native_cell"]),
            ("adaptive_risk", ["assessment_outer", "target"]), ("adaptive_prediction_excess", ["assessment_outer"]),
            ("adaptive_coupling", ["assessment_outer"]),
            ("adaptive_region_error", ["assessment_outer", "current_role_player", "region"]),
            ("adaptive_functional_error", ["assessment_outer", "current_role_player", "functional"]),
            ("projection_region_error", ["assessment_outer", "current_role_player", "region"]),
            ("projection_functional_error", ["assessment_outer", "current_role_player", "functional"]),
            ("omitted_detail", ["assessment_outer", "target"]))})
    return axes


def _shapes(null, n):
    lengths = dict(outer=2*n, condition=3 if null else 4, prior_variance=18, target=3,
                   assessment_outer=n, current_role_player=64, union_role_player=68,
                   region=12, functional=2, source_score=4, spatial_mode_40=40,
                   spatial_mode_11=11, final_context=6, native_cell=656)
    return {name: tuple(lengths[axis] for axis in axes) for name, axes in _array_axes(null, n).items()}


def _read_fits(prepared, fits):
    require(len(fits) == 6, "assessment requires six explicit cell manifests")
    documents, references, values, seen = [], [], [], set()
    n = len(prepared.document["split"]["assessment"])
    for path in fits:
        reference = identity(Path(path).resolve(strict=True))
        document = read_artifact(path, "attribution_resolution_fit", expected_schema=5)
        cell = (document["family"], document["population"], document["law"])
        require(cell in CELLS and cell not in seen and document["purpose"] == prepared.document["purpose"]
                and document["prepared"] == prepared.reference and document["protocol"] == prepared.document["protocol"]
                and document["source_result"] == prepared.source.reference
                and document["source_producer"] == prepared.source.result["implementation"]
                and document["geometry"] == prepared.document["geometry"]
                and document["split"] == prepared.document["split"]
                and document["prior_variances"] == list(VARIANCES) and document["targets"] == list(TARGETS)
                and document["basis_columns"] == {str(d): list(range(d)) for d in (40, 11)}
                and document["source_score_names"] == list(SOURCE_SCORES)
                and document["current_player_ids"] == list(prepared.source.training[-1]["players"])
                and document["union_player_ids"] == sorted({player for design in prepared.source.training for player in design["players"]})
                and document["consumed"] == dict(prepared=document["prepared"], protocol=document["protocol"],
                    source_result=document["source_result"], arrays=document["arrays"]["arrays"]),
                "duplicate, foreign or mismatched 04h cell manifest")
        null = cell[1] == "null"
        arrays = load_arrays(document["arrays"])
        require(document["axes"] == _array_axes(null, n) and list(arrays) == list(document["axes"])
                and all(array.shape == _shapes(null, n)[name] for name, array in arrays.items()),
                "cell array names, dimensions or declared axes differ")
        require(all(array.dtype == np.dtype("int64") if name == "calibration_index" else
                    array.dtype == np.dtype("bool") if name == "physical_active" else array.dtype == np.dtype("float64")
                    for name, array in arrays.items()), "cell array dtype differs from scientific contract")
        require(document["conditions"] == (["base", "double_games", "broad"] if null else [row["name"] for row in CONDITIONS])
                and document["null_aliases"] == (dict(half_effect="base") if null else {})
                and [row["outer"] for row in document["source_control_audit"]] == document["split"]["assessment"]
                and [(row["outer"], row["condition"]) for row in document["probes"]]
                    == [(n, "base"), (2*n-1, "broad")]
                and len(document["pooled_equations"]) == 2*n
                and [(row["outer"], row["spatial_modes"]) for row in document["pooled_equations"]]
                    == [(outer, d) for outer in document["split"]["assessment"] for d in (40, 11)]
                and all(max(row["mean_equation_relative_residuals"]) <= 1e-8
                        and row["equation_relative_residual"] <= 1e-8 for row in document["pooled_equations"])
                and np.all(arrays["risk"] >= 0) and np.all(arrays["zero_risk"] >= 0)
                and np.allclose(arrays["risk"], arrays["bias_squared"]+arrays["sampling_variance"], atol=1e-10, rtol=1e-8),
                "cell conditions, audit, probe count or risk accounting differs")
        source_records = [row for row in prepared.source.records
                          if tuple(row[name] for name in ("family", "population", "law")) == cell]
        source_scores = np.asarray([[row["saved_scores"][name] for name in SOURCE_SCORES] for row in source_records])
        require(np.array_equal(arrays["source_control_scores"], source_scores)
                and np.allclose(arrays["annual_risk"][:, 0], source_scores[:, 0], atol=1e-10, rtol=1e-8)
                and np.allclose(arrays["assessment_zero_risk"][:, 0], source_scores[:, 1], atol=1e-10, rtol=1e-8)
                and np.allclose(arrays["annual_prediction_excess"], source_scores[:, 2]-source_scores[:, 3], atol=1e-10, rtol=1e-8),
                "annual control arrays differ from the selected saved assessment scores")
        require(document["costs"] == dict(nonnull_grid_records=0 if null else 2*n*4*18,
                    analytic_null_grid_records=54 if null else 0, pooled_point_fits=2*n,
                    annual_control_histories=n, annual_control_states=5*n, eigensolve_probes=2,
                    new_responses=0, new_annual_fits=0), "cell work differs from its exact finite budget")
        for ci, condition in enumerate(document["conditions"]):
            means = arrays["risk"][ci, :, 0] if null else arrays["risk"][:n, ci, :, 0].mean(axis=0)
            selected = int(np.argmin(means))
            require(document["calibration_selection"][condition]["index"] == arrays["calibration_index"][ci] == selected
                    and document["calibration_selection"][condition]["prior_variance"] == VARIANCES[selected],
                    "fixed reference differs from calibration-only selection")
        seen.add(cell)
        documents.append(document)
        references.append(reference)
        values.append(arrays)
    require(seen == set(CELLS), "incomplete six-cell inventory")
    order = sorted(range(6), key=lambda i: CELLS.index((documents[i]["family"], documents[i]["population"], documents[i]["law"])))
    return [(documents[i], references[i], values[i]) for i in order]


def _summary(values, weights, *, root=None, denominator=None):
    values = np.asarray(values)
    mean = values.mean(axis=0)
    draws = weights @ values
    if denominator is not None:
        divisor, draw_divisor = np.asarray(denominator).mean(axis=0), weights @ np.asarray(denominator)
        if np.any(divisor == 0):
            return dict(mean=None, lower=None, upper=None, reason="zero truth has no recovery ratio")
        mean, draws = mean/divisor, draws/draw_divisor
    if root is not None:
        mean, draws = np.sqrt(mean/root), np.sqrt(draws/root)
    lower, upper = np.quantile(draws, [.025, .975], axis=0, method="linear")
    return dict(mean=float(mean), lower=float(lower), upper=float(upper))


def _analytic(value, *, root=None, denominator=None):
    if denominator == 0:
        return dict(mean=None, lower=None, upper=None, reason="zero truth has no recovery ratio")
    mean = value if denominator is None else value/denominator
    if root is not None:
        mean = np.sqrt(mean/root)
    return dict(mean=float(mean), lower=None, upper=None, reason="analytic null has no outer sampling interval")


def _partitions(arrays, players, weights, population, law, condition, arm, d):
    region = arrays["annual_region_error" if arm == "annual" else f"adaptive_region_error_{d}"]
    functional = arrays["annual_functional_error" if arm == "annual" else f"adaptive_functional_error_{d}"]
    squared = np.stack((np.sum(region**2, axis=2), functional[:, :, 0]**2, functional[:, :, 1]**2), axis=2)/64
    n, positions = len(players), {player: i for i, player in enumerate(players)}
    masks = [np.tile(np.arange(2*n) < n, (len(squared), 1)), np.tile(np.arange(2*n) >= n, (len(squared), 1)),
             arrays["physical_active"], ~arrays["physical_active"]]
    for player in (32, 33, 8):
        for role in range(2):
            mask = np.zeros_like(arrays["physical_active"])
            mask[:, role*n+positions[player]] = True
            masks.append(mask)
    rows = []
    for name, mask in zip(PARTITIONS, masks, strict=True):
        for ti, target in enumerate(TARGETS):
            row = dict(population=population, law=law, condition=condition, arm=arm,
                       spatial_modes=40 if arm == "annual" else d, partition=name, target=target,
                       risk=_summary((squared*mask[:, :, None]).sum(axis=1)[:, ti], weights))
            if ti > 0:
                actual = (arrays["truth_functionals"][:, :, ti-1]*mask).sum(axis=1)/64
                error = (functional[:, :, ti-1]*mask).sum(axis=1)/64
                row.update(truth_mean=_summary(actual, weights), signed_error=_summary(error, weights),
                           fitted_mean=_summary(actual+error, weights))
            rows.append(row)
    return rows


def _cell_summaries(document, arrays):
    population, law, n = document["population"], document["law"], len(document["split"]["assessment"])
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([40901, POPULATIONS.index(population), LAWS.index(law)])))
    indices = rng.integers(0, n, size=(10000, n))
    weights = np.zeros((10000, n))
    np.add.at(weights, (np.repeat(np.arange(10000), n), indices.ravel()), 1./n)
    curves, comparisons, selections, partitions = [], [], [], []
    null = population == "null"
    for ci, condition in enumerate(document["conditions"]):
        choice = document["calibration_selection"][condition]
        fixed = {name: value[ci] if null else value[n:, ci] for name, value in arrays.items()
                 if name in ("risk", "bias_squared", "sampling_variance", "zero_risk", "prediction_excess", "coupling")}
        for ai, a in enumerate(VARIANCES):
            for ti, target in enumerate(TARGETS):
                summary = (lambda value: _analytic(value)) if null else (lambda value: _summary(value, weights))
                R, zero = fixed["risk"][ai, ti] if null else fixed["risk"][:, ai, ti], fixed["zero_risk"][ai, ti] if null else fixed["zero_risk"][:, ai, ti]
                row = dict(population=population, law=law, condition=condition, prior_variance=a, target=target,
                           calibration_selected=ai == choice["index"], analytic_null=null,
                           **{name: summary(fixed[name][ai, ti] if null else fixed[name][:, ai, ti])
                              for name in ("risk", "bias_squared", "sampling_variance", "zero_risk")},
                           prediction_excess=summary(fixed["prediction_excess"][ai] if null else fixed["prediction_excess"][:, ai]),
                           coupling=summary(fixed["coupling"][ai] if null else fixed["coupling"][:, ai]))
                row["rms"] = _analytic(R, root=12 if ti == 0 else 1) if null else _summary(R, weights, root=12 if ti == 0 else 1)
                row["ratio"] = _analytic(R, denominator=zero) if null else _summary(R, weights, denominator=zero)
                curves.append(row)
        selection = dict(population=population, law=law, condition=condition,
                         fixed_variance=choice["prior_variance"], calibration_ids=choice["truth_ids"],
                         selection_loss=choice["loss"], analytic_null=null)
        if condition not in ("base", "broad"):
            selection["adaptive"] = dict(status="not_run", reason="condition has fixed-family curves only")
            selections.append(selection)
            continue
        d = 40 if condition == "base" else 11
        adaptive = arrays[f"selected_a_{d}"]
        selection["adaptive"] = dict(status="run", counts=[dict(prior_variance=a, count=int(np.count_nonzero(adaptive == a))) for a in VARIANCES],
                                     lower_endpoint=int(np.count_nonzero(adaptive == 0)), upper_endpoint=int(np.count_nonzero(adaptive == 1.)))
        selections.append(selection)
        reference_risks = np.repeat(fixed["risk"][choice["index"]][None, :], n, axis=0) if null else fixed["risk"][:, choice["index"]]
        reference_prediction = np.repeat(fixed["prediction_excess"][choice["index"]], n) if null else fixed["prediction_excess"][:, choice["index"]]
        zero = arrays["assessment_zero_risk"]
        for arm, risks, prediction in (
            ("annual", arrays["annual_risk"], arrays["annual_prediction_excess"]),
            ("adaptive", arrays[f"adaptive_risk_{d}"], arrays[f"adaptive_prediction_excess_{d}"]),
            ("fixed_reference", reference_risks, reference_prediction),
            ("zero", zero, np.zeros(n))):
            for ti, target in enumerate(TARGETS):
                R, Z = risks[:, ti], zero[:, ti]
                analytic = null and arm in ("fixed_reference", "zero")
                summarize = (lambda value: _analytic(value[0])) if analytic else (lambda value: _summary(value, weights))
                row = dict(population=population, law=law, condition=condition, target=target, arm=arm,
                    spatial_modes=40 if arm == "annual" else d, calculation="expected fixed-family" if arm == "fixed_reference" else "realized saved-response" if arm in ("annual", "adaptive") else "physical zero-map",
                    risk=summarize(R), zero_risk=summarize(Z), prediction_excess=summarize(prediction),
                    historical_margin=summarize(.75*Z-R),
                    rms=_analytic(R[0], root=12 if ti == 0 else 1) if analytic else _summary(R, weights, root=12 if ti == 0 else 1),
                    ratio=_analytic(R[0], denominator=Z[0]) if analytic else _summary(R, weights, denominator=Z))
                if arm == "adaptive":
                    total_errors = [arrays[f"adaptive_region_error_{d}"],
                                    arrays[f"adaptive_functional_error_{d}"][:, :, :1],
                                    arrays[f"adaptive_functional_error_{d}"][:, :, 1:]]
                    projection_errors = [arrays[f"projection_region_error_{d}"],
                                         arrays[f"projection_functional_error_{d}"][:, :, :1],
                                         arrays[f"projection_functional_error_{d}"][:, :, 1:]]
                    estimation_error = total_errors[ti]-projection_errors[ti]
                    projected_estimation_risk = np.sum(estimation_error**2, axis=(1, 2))/64
                    cross = 2*np.sum(estimation_error*projection_errors[ti], axis=(1, 2))/64
                    _close(R, projected_estimation_risk+arrays[f"omitted_detail_{d}"][:, ti]+cross,
                           "spatial projection signed recovery accounting")
                    row.update(annual_minus_pooled=_summary(arrays["annual_risk"][:, ti]-R, weights),
                               annual_minus_pooled_prediction=_summary(arrays["annual_prediction_excess"]-prediction, weights),
                               adaptive_minus_reference=_summary(R-reference_risks[:, ti], weights),
                               adaptive_minus_reference_prediction=_summary(prediction-reference_prediction, weights),
                               omitted_detail=_summary(arrays[f"omitted_detail_{d}"][:, ti], weights),
                               projected_estimation_risk=_summary(projected_estimation_risk, weights),
                               projection_estimation_cross=_summary(cross, weights),
                               coupling=_summary(arrays[f"adaptive_coupling_{d}"], weights))
                elif arm == "annual":
                    row["coupling"] = _summary(arrays["annual_coupling"], weights)
                comparisons.append(row)
        for arm in ("annual", "adaptive"):
            partitions.extend(_partitions(arrays, document["current_player_ids"], weights, population, law, condition, arm, d))
    return curves, comparisons, selections, partitions


def assess(prepared, fits, output):
    started, process_started = time.monotonic(), time.process_time()
    prepared = read_prepared(prepared)
    cells = _read_fits(prepared, fits)
    root = output_path(str(output), prepared.source.input_roots)
    if prepared.document["purpose"] == "research":
        require(root.is_relative_to(Path(prepared.document["protocol"]["path"]).parent), "assessment output must be beneath its prepared run")
    root.mkdir()
    curves, comparisons, selections, partitions = [], [], [], []
    for document, _, arrays in cells:
        cell_curves, cell_comparisons, cell_selections, cell_partitions = _cell_summaries(document, arrays)
        curves.extend(cell_curves)
        comparisons.extend(cell_comparisons)
        selections.extend(cell_selections)
        partitions.extend(cell_partitions)
    totals = {name: sum(document["costs"][name] for document, _, _ in cells) for name in cells[0][0]["costs"]}
    require(all(value == prepared.document["budget"][name] for name, value in totals.items()), "executed work does not reconcile to frozen budget")
    null_cells = {document["law"]: arrays for document, _, arrays in cells if document["population"] == "null"}
    null_equality = all(np.allclose(null_cells["gaussian"][name], null_cells["game_pace"][name], atol=1e-10, rtol=1e-8)
                        for name in ("risk", "bias_squared", "sampling_variance", "zero_risk", "prediction_excess", "coupling"))
    verified = null_equality and all(probe["verified"] for document, _, _ in cells for probe in document["probes"])
    references = [reference for _, reference, _ in cells]
    consumed = dict(prepared=prepared.reference, protocol=prepared.document["protocol"], source_result=prepared.source.reference,
                    **{f"fit_{index:02d}": reference for index, reference in enumerate(references)})
    fields = dict(prepared=prepared.reference, protocol=prepared.document["protocol"], fits=references,
        execution_status="complete", numerical_status="verified" if verified else "unresolved",
        study_status="diagnosed" if verified else "numerically_unresolved", nomination=None, admission="not_admitted", handoff=None,
        curves=curves, comparisons=comparisons, selections=selections, partitions=partitions,
        exact_completeness=dict(**totals, cells=6), costs=dict(fits=[document["resources"] for document, _, _ in cells]),
        numerical=dict(analytic_null_law_equality=null_equality,
                       probes=[dict(population=document["population"], law=document["law"], **probe)
                               for document, _, _ in cells for probe in document["probes"]],
                       equations=[dict(population=document["population"], law=document["law"], grids=document["grid_equations"])
                                  for document, _, _ in cells]),
        real_context=prepared.document["context"], target_rank=prepared.document["target_rank"],
        source_status=dict(numerical_status=prepared.source.result["numerical_status"],
                           controls=[dict(population=document["population"], law=document["law"],
                                          audit=document["source_control_audit"]) for document, _, _ in cells]),
        # this frozen inventory's reviewed scientific judgment; verification only permits release.
        next_question="penalty_selection" if verified and prepared.document["purpose"] == "research" else "unresolved",
        limits=LIMITS,
        null_aliases=dict(half_effect="base"), interval_meaning="mean experimental risk conditional on designs, calibration set and chosen reference; not individual-player precision",
        units=RULES["units"], purpose=prepared.document["purpose"])
    from attribution_resolution_report import render_reports
    report = render_reports(root, fields)
    require(set(report) == {"reports", "figures", "next_question"}
            and report["next_question"] in ("temporal_selection", "penalty_selection", "resolution_evidence", "unresolved"),
            "report result contract differs")
    fields.pop("purpose")
    fields.update(report)
    fields["next_question"] = report["next_question"] if verified and prepared.document["purpose"] == "research" else "unresolved"
    assessment = artifact("attribution_resolution_assessment", prepared.document["purpose"], consumed,
                          schema_version=5, **fields, resources=_cost(started, process_started, root))
    assessment_path = root/"assessment.json"
    write_json(assessment_path, json_values(assessment))
    result = artifact("attribution_resolution_result", prepared.document["purpose"],
        dict(assessment=identity(assessment_path), **consumed,
             **{f"report_{i:02d}": reference for i, reference in enumerate(report["reports"])},
             **{f"figure_{i:02d}": reference for i, reference in enumerate(report["figures"])}),
        schema_version=5, assessment=identity(assessment_path), prepared=prepared.reference, protocol=prepared.document["protocol"],
        consumed_fits=references, **{key: assessment[key] for key in ("execution_status", "numerical_status", "study_status", "next_question", "nomination", "admission", "handoff", "exact_completeness", "reports", "figures", "limits")},
        source_producer=prepared.source.result["implementation"], resources=_cost(started, process_started, root))
    path = root/"result.json"
    write_json(path, json_values(result))
    return identity(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    preparation = commands.add_parser("prepare")
    preparation.add_argument("--source-result", required=True)
    preparation.add_argument("--real-context", required=True)
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
        reference = {"prepare": prepare, "fit": fit, "assess": assess}[command](**arguments)
    except (InputContractError, OSError, ValueError, KeyError, np.linalg.LinAlgError) as error:
        print(str(error), file=sys.stderr)
        return 1
    import json
    print(json.dumps(reference, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
