"""04d: information, frozen-path transmission and fixed-grid gaussian diagnostics."""
import argparse
from collections import defaultdict
import hashlib
import io
import os
from pathlib import Path
import sys
import time

for _thread in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[_thread] = '1'

import numpy as np

from hockey_stats.artifacts import (artifact, clean_implementation, implementation, json_values,
    require, resources, write_arrays, write_json)
from hockey_stats.chance_cli import identity, output_path, read_json
from hockey_stats.captures import strict_json
from hockey_stats.attribution_data import (
    centered_estimability, exposure_centering as _centering, likelihood_spectrum as _rank,
)

SPEC = Path(__file__).resolve().parents[2] / 'docs/specs/04d-attribution-diagnosis.md'
RESEARCH_ROOT = Path('/Volumes/Expansion/hockey-stats/runs')
CASES = ('gaussian', 'game_pace')
REPRESENTATIONS = ('graph_40ft', 'native_04b')
SEASONS = tuple(f'{year}{year+1}' for year in range(2021, 2026))
VARIANCES = tuple(float(10. ** exponent) for exponent in np.arange(-8., .01, .5))
PROBES = ('fitted', 'frozen', 'incoming', 'carry', 'current', 'one_step',
          'actual_minus_frozen', 'incoming_to_updated', 'saved_incoming', 'one_step_minus_saved_incoming')
PROBE_MEANINGS = dict(
    fitted='actual saved centered annual fitted mean',
    frozen='recursive frozen-path mean-response intervention under the current exposure reference',
    incoming='embedded preceding frozen mean; retains its preceding exposure reference',
    carry='(P-K) incoming; signed current-reference carry contribution',
    current='centered covariance times current truth score; signed current-reference contribution',
    one_step='mean response using the actual saved incoming mean, under the current exposure reference',
    actual_minus_frozen='actual fitted mean minus recursive frozen intervention; need not average to zero',
    incoming_to_updated='frozen minus raw embedded incoming; includes current-reference recentering',
    saved_incoming='actual saved proper-prior mean; retains its preceding exposure reference',
    one_step_minus_saved_incoming='one-step mean response minus raw saved incoming; includes current-reference recentering',
)
UNITS = 'attempts/60 team minutes'
SQUARED_UNITS = 'squared attempts/60 team minutes'
EXACT = dict(result='a87d04c30205eb707b9dbf6ee3fd83f44da73617e12d674a445c228d65c9e747',
    prepared='59261bd10f874bb0d19146e7f22948a9a6b2dac511e00d73d4842dca8529f724',
    means='88a8d36fc492a4c891c3c8471b83be62976245aac93cf82b128f392485d30f48',
    design='d173ca19ee4b6aef94fd3f7b6397cd01028d979c731a368a399825515c7c4dcc',
    basis='67d7ee706f1d8d251cc68a0d22378e67e1961b2ac53fb764bfc0efdff11d43fc')
RANK_POLICY = dict(tau='100*n*eps*lambda_max', sensitivity=[.1, 1., 10.], null_tolerance=1e-8,
    negative_eigenvalue='below_minus_tau_is_failure', instability='numerically_unresolved')
FIGURE_CONTRACTS = dict(
    representation_information='actual and projected broad/local/rough native truth; shared within-pattern scale; graph/native likelihood precision and null statuses distinct from exposure constraints',
    transmission_scale_pressure='five-year saved and frozen-path broad diagnostics; entrant/returner/null controls outer zero; paired fixed-grid objective differences and gaussian regional risk')
LIMITATIONS = [
    'known-truth synthetic results do not identify real players',
    'gaussian likelihood precision and risk do not validate game-pace uncertainty',
    'frozen-path mean-response interventions hold adaptive selected covariance paths fixed; they are not conditional expectations given scales',
    'actual minus frozen-path values need not average to zero and are not an independent error source',
    'global pooling may rationally sacrifice sparse contrasts; oracle risk cannot select deployable scales',
    'reference shares remain conditioned on; additive-rate, volume, positivity, source robustness and chance valuation remain separate',
    'no nomination, admission, handoff or automatic next study follows',
]

INTERPRETATION_RULES = [
    'geometric projection establishes representability only; retain omitted actual truth',
    'null components and gaussian variance establish identification or precision costs under the declared design and law',
    'weak frozen transmission establishes conditional suppression, not inappropriate shrinkage',
    'criterion/risk disagreement may motivate pooling/objective alignment, never a selected replacement',
    'signed carry is conditional evidence for particular years, never unconditional temporal risk',
    'incomplete reconciliation or unstable rank stops affected interpretation']


def _bound(reference: dict, kind: str | None = None, *, arrays=False):
    """one payload read hashes and decodes a bound document or archive."""
    require(isinstance(reference, dict) and set(reference) == {'path', 'sha256'}
            and Path(reference['path']).is_absolute(), 'explicit absolute artifact reference required')
    path = Path(reference['path']).resolve(strict=True)
    payload = path.read_bytes()
    require(hashlib.sha256(payload).hexdigest() == reference['sha256'], f'{path}: linked artifact digest mismatch')
    if arrays:
        with np.load(io.BytesIO(payload), allow_pickle=False) as archive:
            value = {name: archive[name] for name in archive.files}
        require(all(a.dtype.kind in 'biuf' and np.isfinite(a).all() for a in value.values()),
                'source archive must contain finite numeric arrays')
    else:
        value = strict_json(payload)
        if kind is not None:
            require(isinstance(value, dict) and type(value.get('schema_version')) is int and value.get('schema_version') == 3 and value.get('kind') == kind
                and value.get('purpose') in ('research', 'fixture_exercise'), 'incorrect schema-3 ' + kind)
            if value['purpose'] == 'research':
                clean_implementation(value['implementation'])
    return value, len(payload)


def _close(actual, expected, message):
    actual, expected = np.asarray(actual), np.asarray(expected)
    require(actual.shape == expected.shape and np.isfinite(actual).all() and np.isfinite(expected).all(), message)
    residual = float(np.max(np.abs(actual - expected))) if actual.size else 0.
    scale = 1. + float(np.max(np.abs(expected))) if expected.size else 1.
    require(residual <= 1e-8 * scale, message)
    return residual / scale


def requests(saved_requests: list[dict]) -> list[dict]:
    """new year projections retain original coefficients and scalar functionals exactly."""
    table = [('offense_radial_3_minus_4_shape', range(1, 6), 'primary'),
        ('offense_lateral_10_minus_11_shape', range(1, 6), 'primary'),
        ('offense_local_18_minus_19_shape', (1, 5), 'stress'),
        ('offense_rough_20_minus_21_shape', (1, 5), 'stress'),
        ('offense_entrant_32_shape', (3, 4, 5), 'transition'),
        ('defense_entrant_33_shape', (3, 4, 5), 'transition'),
        ('offense_returner_8_shape', (2, 3, 4, 5), 'transition'),
        ('offense_pair_26_minus_31_shape', range(1, 6), 'null_control'),
        ('offense_pair_26_plus_31_shape', range(1, 6), 'paired_sum')]
    functionals = {}
    for functional in ('radial', 'lateral'):
        matches = [row for row in saved_requests if row.get('estimand') == 'shape'
                   and row.get('functional') == functional]
        require(matches and all(row['weights'] == matches[0]['weights'] for row in matches),
                'saved scalar functional identity differs')
        functionals[functional] = matches[0]['weights']
    result = []
    for name, years, group in table:
        source = [row for row in saved_requests if row['name'] == name and row['estimand'] == 'shape']
        require(source, 'saved shape request missing: ' + name)
        first = source[0]
        for year in years:
            result.append(dict(name=name, year=year, season=SEASONS[year - 1], role=first['role'],
                coefficients=first['coefficients'], group=group, functionals=functionals,
                status='not_assessed' if 'returner_8' in name and year == 3 else 'available',
                reason='absent_current_player_no_truth' if 'returner_8' in name and year == 3 else None))
    require(len(result) == 34 and len({(r['name'], r['year']) for r in result}) == 34,
            '04d request inventory differs')
    return result


def _inputs(baseline_reference):
    """small fixed manifests are separate from the once-only outer stream."""
    result, count = _bound(baseline_reference, 'attribution_recovery_result')
    require(result['completion'] == 'complete' and result['recommendation'] == 'mean_recovery_failed',
            '04d requires the frozen failed 04c mean stage')
    refs = {name: result['evidence'][name] for name in ('prepared', 'means')}
    prepared, size = _bound(refs['prepared'], 'attribution_recovery_prepared')
    count += size
    means, size = _bound(refs['means'], 'attribution_recovery_means')
    count += size
    model, size = _bound(prepared['model_protocol'], 'attribution_recovery_protocol')
    count += size
    saved_requests, size = _bound(prepared['requests'])
    count += size
    require(means['prepared'] == refs['prepared'] and means['model_protocol'] == prepared['model_protocol']
        and means['basis'] == prepared['basis'] and means['basis_sha256'] == prepared['basis_sha256']
        and means['requests'] == prepared['requests'] and means['request_sha256'] == prepared['request_sha256']
        and means['purpose'] == prepared['purpose'] == model['purpose'] == result['purpose']
        and result['model_protocol'] == prepared['model_protocol']
        and result['model_implementation'] == model['implementation'] == prepared['implementation'] == means['implementation']
        and means['status'] == 'complete' and not means['incomplete_ids']
        and prepared['seasons'] == list(SEASONS), '04c evidence chain differs or is incomplete')
    refs.update(model_protocol=prepared['model_protocol'], requests=prepared['requests'],
                design=prepared['synthetic_design']['arrays'], basis=prepared['basis'])
    require(all(result['consumed'][name] == refs[name] for name in ('prepared', 'means'))
        and all(prepared['consumed'][name] == prepared[name] for name in ('source_prepared', 'diagnosis', 'model_protocol', 'requests'))
        and all(means['consumed'][name] == means[name] for name in ('prepared', 'source_prepared', 'model_protocol', 'requests')),
        '04c consumed references disagree with declared source fields')
    if result['purpose'] == 'research':
        require(baseline_reference['sha256'] == EXACT['result']
            and all(refs[name]['sha256'] == EXACT[name] for name in ('prepared', 'means', 'design', 'basis')),
            '04d evidence differs from the exact selected 04c artifacts')
        clean_implementation(result['model_implementation'])
    return result, prepared, means, model, saved_requests, refs, count


def freeze_protocol(baseline_result, out, *, outer_per_case=400):
    started, process_started = time.monotonic(), time.process_time()
    baseline = identity(Path(baseline_result).resolve(strict=True))
    result, prepared, means, model, old_requests, refs, count = _inputs(baseline)
    require(type(outer_per_case) is int and 0 < outer_per_case <= 400
        and means['expected_outer_per_case'] == outer_per_case, 'explicit outer budget differs from saved evidence')
    if result['purpose'] == 'research':
        require(outer_per_case == 400, 'research denominator must retain all 800 original paths')
    output = output_path(str(out), [str(Path(baseline['path']).parent)])
    if result['purpose'] == 'research':
        require(output.is_relative_to(RESEARCH_ROOT), 'research protocol must remain external-only')
    output.mkdir()
    snapshot = output / 'spec-snapshot.md'
    spec_payload = SPEC.read_bytes()
    count += len(spec_payload)
    with snapshot.open('xb') as destination:
        destination.write(spec_payload)
    spec_reference = identity(snapshot)
    count += Path(baseline['path']).stat().st_size
    protocol = artifact('attribution_information_protocol', result['purpose'],
        dict(baseline_result=baseline, spec_snapshot=spec_reference, **refs),
        baseline_result=baseline, model_implementation=result['model_implementation'],
        model_protocol=prepared['model_protocol'], spec_snapshot=spec_reference,
        source_kind='synthetic', units=dict(shape=UNITS, squared_error=SQUARED_UNITS),
        output_root=str(output.parent), representations=list(REPRESENTATIONS), cases=list(CASES),
        outer_ids=list(range(outer_per_case)), years=list(range(1, 6)), seasons=list(SEASONS),
        requests=requests(old_requests), variance_grid=list(VARIANCES), rank_policy=RANK_POLICY,
        numerical_relative_tolerance=1e-8, probes=list(PROBES), probe_meanings=PROBE_MEANINGS,
        budgets=dict(outer_manifests=2 * outer_per_case, outer_archives=2 * outer_per_case,
            annual_states=20 * outer_per_case, annual_designs=5, analytic_states=34,
            response_arrays=10, replay_paths=[dict(case=case, outer=0) for case in CASES],
            new_draws=0, fits=0, scale_selections=0, bootstrap=0),
        geometry=dict(grid=prepared['grid'], basis_sha256=prepared['basis_sha256'],
            reference='original positive native shares', truth='saved annual truth_shape arrays', regions=prepared['regions']),
        array_shapes=[], figure_contracts=FIGURE_CONTRACTS,
        interpretation_rules=INTERPRETATION_RULES,
        limitations=LIMITATIONS, resources=dict(**resources(started),
            process_seconds=time.process_time() - process_started, bytes_read=count,
            bytes_read_scope='consumed fixed manifests and exact spec, including baseline identity hash',
            generated_artifact_bytes_read=len(spec_payload)), admission='not_admitted', handoff=None)
    path = output / 'protocol.json'
    write_json(path, json_values(protocol))
    return identity(path)


def validate_protocol(protocol, baseline_reference):
    require(protocol['kind'] == 'attribution_information_protocol' and protocol['baseline_result'] == baseline_reference
        and protocol['representations'] == list(REPRESENTATIONS) and protocol['cases'] == list(CASES)
        and protocol['seasons'] == list(SEASONS) and protocol['years'] == list(range(1, 6))
        and protocol['variance_grid'] == list(VARIANCES) and protocol['rank_policy'] == RANK_POLICY
        and protocol['numerical_relative_tolerance'] == 1e-8 and protocol['probes'] == list(PROBES)
        and protocol['probe_meanings'] == PROBE_MEANINGS
        and protocol['figure_contracts'] == FIGURE_CONTRACTS and protocol['limitations'] == LIMITATIONS
        and protocol['interpretation_rules'] == INTERPRETATION_RULES
        and protocol['source_kind'] == 'synthetic'
        and protocol['units'] == dict(shape=UNITS, squared_error=SQUARED_UNITS)
        and protocol['array_shapes'] == [],
        'frozen 04d scientific policy differs')
    spec_path = Path(protocol['spec_snapshot']['path']).resolve(strict=True)
    payload = spec_path.read_bytes()
    require(hashlib.sha256(payload).hexdigest() == protocol['spec_snapshot']['sha256']
        and payload == SPEC.read_bytes(), 'frozen exact 04d spec snapshot differs')
    if protocol['purpose'] == 'research':
        require(protocol['outer_ids'] == list(range(400)), 'research outer identities changed')
        clean_implementation(protocol['implementation'])
        require(implementation() == protocol['implementation'], 'diagnostic producer differs from frozen clean protocol')
    return len(payload) * 2


def pattern_metrics(estimate, truth):
    estimate, truth = np.asarray(estimate), np.asarray(truth)
    error = estimate - truth
    energy = float(truth @ truth)
    return dict(squared_error=float(error @ error), truth_energy=energy,
        normalized_squared_error=float(error @ error) / energy if energy > 0 else None,
        truth_alignment=float(estimate @ truth) / energy if energy > 0 else None,
        ratio_status='available' if energy > 0 else 'not_assessed',
        ratio_reason=None if energy > 0 else 'zero_truth_energy')


def _coefficient(request, players):
    positions = {player: i for i, player in enumerate(players)}
    require(all(player in positions for player, _ in request['coefficients']), 'request player outside ordered state')
    c = np.zeros(2 * len(players))
    offset = len(players) if request['role'] == 'defense' else 0
    for player, value in request['coefficients']:
        c[offset + positions[player]] += value
    return c


def _information(H, P, c, spectra, S, W, scalar_vectors, truth, r):
    information = centered_estimability(H, P, c, spectrum=spectra)
    precision = information['contrast_information_inverse']
    regional_variance = r * r * precision * float(np.trace(W.T @ S @ W)) if precision is not None else None
    energy = float((truth @ W) @ (truth @ W))
    return dict(**information,
        regional_total_variance=regional_variance,
        variance_to_actual_truth_energy=regional_variance / energy if regional_variance is not None and energy > 0 else None,
        scalar_variances={name: r * r * precision * float(v @ S @ v) if precision is not None else None
                          for name, v in scalar_vectors.items()},
        exposure_reference_constraints=2, constraints_are_not_likelihood_information=True,
        units=SQUARED_UNITS, supplied_oracle_information='fixed gaussian observation law; H_raw additionally knows context')


def fixed_risk(update, H, P, c, native_transform, W, S, r, actual_truth):
    """regional gaussian risk at an already evaluated fixed-prior state."""
    V = update.uncentered_covariance
    d = P.T @ c
    prediction = r * c @ update.mean @ native_transform @ W
    bias = prediction - actual_truth
    sampling = r * r * float(d @ V @ H @ V @ d) * float(np.trace(W.T @ S @ W))
    return dict(expected_error=float(bias @ bias) + sampling, squared_bias=float(bias @ bias),
                gaussian_variance=sampling, regional_mean=prediction.tolist(), units=SQUARED_UNITS)


def _grid(design, basis, request_rows):
    from hockey_stats.attribution import fixed_shape_update, shape_objective_terms
    H, p, W, r = design['H'], design['p'], design['W'], 40.
    P = _centering(design['u'])
    result = []
    for representation in REPRESENTATIONS:
        graph = representation == 'graph_40ft'
        theta = design['truth_shape'] @ basis.B if graph else design['truth_shape']
        transform = basis.R.T if graph else np.eye(len(p))
        S = basis.R @ basis.R.T if graph else np.diag(p) - np.outer(p, p)
        q = basis.B.shape[1] if graph else len(p) - 1
        Q = H @ theta
        signal = Q @ Q.T if graph else (Q / p) @ Q.T
        first_objective = None
        for variance in VARIANCES:
            terms = shape_objective_terms(H, variance * np.eye(len(H)), signal,
                response_rank=q, response_metric='graph_identity' if graph else 'native_inverse_share',
                noise_contraction=q * H)
            require(all(np.isfinite(terms[name]) for name in ('determinant', 'signal', 'noise', 'objective', 'equation_relative_residual'))
                and terms['equation_relative_residual'] <= 1e-8, 'fixed-grid objective numerical failure')
            if first_objective is None:
                first_objective = terms['objective']
            update = fixed_shape_update(H, np.zeros_like(theta), variance * np.eye(len(H)), Q, design['u'])
            risks = []
            for request in request_rows:
                if request['year'] != 1 or request['group'] != 'primary':
                    continue
                c = _coefficient(request, design['players'])
                actual = 40 * c @ design['truth_shape'] @ W
                risk = fixed_risk(update, H, P, c, transform, W, S, 40., actual)
                energy = float(actual @ actual)
                risks.append(dict(request=request['name'], **risk, actual_truth_energy=energy,
                    normalized_expected_error=risk['expected_error'] / energy if energy > 0 else None))
            result.append(dict(representation=representation, case='gaussian', outer=None, year=1, request=None,
                probe='fixed_variance', variance=variance, objective_difference=terms['objective'] - first_objective,
                ** terms, risks=risks, supplied_oracle_information='saved native truth and gaussian generator',
                fixed='first-year design/truth/reference; zero incoming mean; aI prior', changed='fixed variance grid only'))
    require(len(result) == 34, 'analytic state budget differs')
    return result


def _load_outer(reference, prepared, means, basis, designs, case_id, outer_id):
    from hockey_stats.attribution import read_recovery_embedded_annual
    outer, count = _bound(reference, 'attribution_recovery_mean_outer')
    require(type(outer['case_id']) is int and type(outer['outer_id']) is int
        and type(case_id) is int and type(outer_id) is int
        and outer['case_id'] == case_id and outer['outer_id'] == outer_id and outer['case'] == CASES[case_id]
        and outer['prepared'] == means['prepared'] and outer['model_protocol'] == prepared['model_protocol']
        and outer['source_prepared'] == prepared['source_prepared'] and outer['source_kind'] == 'synthetic'
        and outer['basis'] == prepared['basis'] and outer['basis_sha256'] == prepared['basis_sha256']
        and outer['requests'] == prepared['requests'] and outer['request_sha256'] == prepared['request_sha256']
        and outer['purpose'] == prepared['purpose'] and outer['status'] == 'complete' and outer['error'] is None
        and outer['response_seeds'] == [[40430, case_id, outer_id, year] for year in range(5)]
        and outer['implementation'] == means['implementation']
        and all(outer['consumed'][name] == outer[name] for name in ('prepared', 'source_prepared', 'model_protocol', 'requests')), 'outer source identity, order or completion differs')
    arrays, size = _bound(outer['arrays'], arrays=True)
    count += size
    shapes = outer['array_shapes']
    require(list(arrays) == [row['name'] for row in shapes] and len(arrays) == len(shapes)
        and all(list(arrays[row['name']].shape) == row['shape']
                and arrays[row['name']].dtype.str == row['dtype'] for row in shapes),
        'outer archive ordered array contract differs')
    require(set(outer['point_records']) == set(REPRESENTATIONS), 'outer representations differ')
    states = {}
    for representation in REPRESENTATIONS:
        previous = None
        chain = []
        require(len(outer['point_records'][representation]) == 5, 'outer annual state denominator differs')
        for year, (record, design) in enumerate(zip(outer['point_records'][representation], designs, strict=True)):
            state = read_recovery_embedded_annual(record, arrays, representation=representation,
                basis=basis if representation == 'graph_40ft' else None,
                source_prepared=prepared['source_prepared'], source_protocol=prepared['source_protocol'],
                model_protocol=prepared['model_protocol'],
                basis_reference=prepared['basis'] if representation == 'graph_40ft' else None,
                population_id=f'synthetic:04c:{case_id}:{outer_id}:unblocked_spatial',
                season_index=year, season=SEASONS[year], current_player_ids=tuple(design['players']),
                current_u=design['u'], p=design['p'], strata=tuple(tuple(s) for s in design['strata']), previous=previous)
            chain.append(state)
            previous = state
        states[representation] = chain
    return outer, arrays, states, count


def _summary(values):
    values = np.asarray(values)
    return dict(n=len(values), mean=values.mean(axis=0).tolist(),
        quantile_probabilities=[.05, .5, .95], quantiles=np.quantile(values, [.05, .5, .95], axis=0, method='linear').tolist(),
        meaning='distribution of original path diagnostics; not confidence intervals')


def _reconcile_summaries(result, means, pattern_accumulators, transition_accumulators, gains):
    receipts = []
    for reported in result['point_diagnostics']['patterns']:
        key = (CASES.index(reported['case']), reported['year'], reported['contrast'], reported['representation'])
        a = pattern_accumulators[key]
        n = a['n']
        truth = a['truth']
        complete_truth = a['complete_truth']
        require(n == reported['observed_outer'] == reported['expected_outer'], '04c pattern denominator differs')
        for name, sum_vector, error_sum, target in (
            ('shape_native', a['shape_sum'], a['shape_error'], truth),
            ('shape_regions', a['shape_sum'] @ a['W'], a['region_error'], truth @ a['W']),
            ('complete_native', a['complete_sum'], a['complete_error'], complete_truth)):
            average = sum_vector / n
            bias = average - target
            bias2 = float(bias @ bias)
            mse = error_sum / n
            expected = dict(n=n, bias_squared=bias2, sampling_variation=mse - bias2, mean_squared_error=mse,
                truth_energy=float(target @ target), normalized_mean_squared_error=mse / float(target @ target)
                    if target @ target > 0 else None,
                mean_pattern_attenuation=float(average @ target) / float(target @ target) if target @ target > 0 else None)
            residuals = []
            for field, value in expected.items():
                if value is None:
                    require(reported[name][field] is None, '04c zero-energy ratio differs')
                else:
                    residuals.append(_close(value, reported[name][field], '04c reported ' + name + '/' + field + ' differs'))
            receipts.append(dict(kind='04c_pattern', case=reported['case'], year=key[1], request=key[2],
                representation=key[3], probe=name, n=n, maximum_relative_residual=max(residuals)))
        for field, value in dict(shape_rmse_native=np.sqrt(a['shape_error'] / n),
            shape_rmse_regions=np.sqrt(a['region_error'] / n), complete_rmse_native=np.sqrt(a['complete_error'] / n),
            complete_zero_baseline_native_squared_error=float(complete_truth @ complete_truth),
            same_fitted_volume_only_native_squared_error=a['volume_only_error'] / n).items():
            _close(value, reported[field], '04c reported pattern scalar differs')
    require(len(pattern_accumulators) == len(result['point_diagnostics']['patterns']) == 32,
            '04c pattern summary inventory differs')
    for reported in means['gate']['rules']:
        values = gains[(reported['case_id'], reported['contrast'], reported['baseline'])]
        require(len(values) == reported['n'], '04c primary gain denominator differs')
        residual = _close(np.mean([v[0] for v in values]), reported['mean_baseline_error'], '04c baseline mean differs')
        residual = max(residual, _close(np.mean([v[1] for v in values]), reported['mean_candidate_error'], '04c candidate mean differs'))
        residual = max(residual, _close(np.mean([v[0] - v[1] for v in values]), reported['mean_gain'], '04c paired mean gain differs'))
        matches = [row for row in result['rule_matrix'] if row.get('phase') == 'means'
            and row.get('case_id') == reported['case_id'] and row.get('contrast') == reported['contrast']
            and row.get('baseline') == reported['baseline']]
        require(len(matches) == 1 and all(matches[0][k] == v for k, v in reported.items()),
                '04c reported primary rule differs from its bound mean artifact')
        receipts.append(dict(kind='04c_primary_gain', case=reported['case'], request=reported['contrast'],
            baseline=reported['baseline'], n=len(values), maximum_relative_residual=residual,
            bootstrap='not_recomputed; original bound percentile interval and verdict preserved'))
    require(len(gains) == 8, '04c primary gain inventory differs')
    for reported in result['point_diagnostics']['transitions_and_matched_volume']:
        a = transition_accumulators[(reported['case'], reported['key'])]
        require(a['n'] == reported['observed_outer'] == reported['expected_outer'], '04c transition denominator differs')
        residual = _close(a['truth'], reported['truth'], '04c transition truth differs')
        residual = max(residual, _close(a['error'] / a['n'], reported['point_bias'], '04c transition bias differs'))
        residual = max(residual, _close(np.sqrt(a['error2'] / a['n']), reported['point_rmse'], '04c transition rmse differs'))
        receipts.append(dict(kind='04c_transition', case=reported['case'], request=reported['key'], n=a['n'],
                             maximum_relative_residual=residual))
    require(len(transition_accumulators) == len(result['point_diagnostics']['transitions_and_matched_volume']),
            '04c transition summary inventory differs')
    return receipts


def diagnose(baseline_result, protocol, out):
    from hockey_stats.attribution import fixed_shape_update, decode_shape_basis, shape_mean
    from hockey_stats.attribution_data import (decode_recovery_design, embed_recovery_information,
        synthetic_population, statistic_digest, weighted_population)
    from hockey_stats.attribution_simulation import synthetic_counts
    from hockey_stats.artifacts import ordered_array_digest
    from hockey_stats.attribution_uncertainty import request_key

    started, process_started = time.monotonic(), time.process_time()
    baseline_ref = identity(Path(baseline_result).resolve(strict=True))
    protocol_ref = identity(Path(protocol).resolve(strict=True))
    frozen, bytes_read = _bound(protocol_ref, 'attribution_information_protocol')
    bytes_read += sum(Path(ref['path']).stat().st_size for ref in (baseline_ref, protocol_ref))
    bytes_read += validate_protocol(frozen, baseline_ref)
    result, prepared, means, model, old_requests, refs, count = _inputs(baseline_ref)
    bytes_read += count
    require(frozen['purpose'] == result['purpose'] and frozen['requests'] == requests(old_requests)
        and frozen['consumed'] == dict(baseline_result=baseline_ref, spec_snapshot=frozen['spec_snapshot'], **refs)
        and frozen['model_implementation'] == result['model_implementation']
        and frozen['model_protocol'] == prepared['model_protocol']
        and frozen['geometry'] == dict(grid=prepared['grid'], basis_sha256=prepared['basis_sha256'],
            reference='original positive native shares', truth='saved annual truth_shape arrays', regions=prepared['regions']),
        'protocol source/request identity differs')
    outer_ids = frozen['outer_ids']
    n = len(outer_ids)
    require(all(type(value) is int for value in outer_ids), 'outer ids must be explicit integers')
    expected_budgets = dict(outer_manifests=2 * n, outer_archives=2 * n, annual_states=20 * n, annual_designs=5,
        analytic_states=34, response_arrays=10, replay_paths=[dict(case=c, outer=0) for c in CASES],
        new_draws=0, fits=0, scale_selections=0, bootstrap=0)
    require(all(type(frozen['budgets'][name]) is int for name in expected_budgets if name != 'replay_paths')
        and frozen['budgets'] == expected_budgets and outer_ids == list(range(n))
        and means['expected_outer_per_case'] == n, 'frozen finite budget differs')
    require([(row['case_id'], row['outer_id']) for row in means['outers']]
        == [(case, outer) for case in range(2) for outer in outer_ids],
        'outer identities are missing, duplicated or reordered')
    basis_arrays, count = _bound(refs['basis'], arrays=True)
    bytes_read += count
    design_arrays, count = _bound(refs['design'], arrays=True)
    bytes_read += count
    require(list(basis_arrays) == [row['name'] for row in prepared['basis_shapes']]
        and all(list(basis_arrays[row['name']].shape) == row['shape']
                and basis_arrays[row['name']].dtype.str == row['dtype'] for row in prepared['basis_shapes']),
        'saved basis ordered array shape contract differs')
    basis = decode_shape_basis(basis_arrays, basis_sha256=prepared['basis_sha256'])
    designs = decode_recovery_design(prepared, model, design_arrays)
    del basis_arrays, design_arrays
    request_rows = frozen['requests']
    active = [i for i, row in enumerate(request_rows) if row['status'] == 'available']
    active_position = {index: position for position, index in enumerate(active)}
    p, W = designs[0]['p'], designs[0]['W']
    width = len(p)
    S = {'native_04b': np.diag(p) - np.outer(p, p), 'graph_40ft': basis.R @ basis.R.T}
    scalar_names = ('radial', 'lateral')
    vectors = np.column_stack((W, *[np.asarray(request_rows[0]['functionals'][name]) for name in scalar_names]))
    projections = np.empty((2, n, 2, len(active), len(PROBES), 14))
    native_sums = np.zeros((2, 2, len(active), len(PROBES), width))
    native_examples = np.empty_like(native_sums)
    truths = np.empty((len(active), width))
    geometry = []
    information = []
    request_metrics = []
    state_receipts = []
    outer_receipts = []
    replays = []
    modes = []
    curves = defaultdict(list)
    patterns = {}
    transitions = {}
    gains = defaultdict(list)
    old_by_key = {request_key(row): row for row in old_requests}
    unresolved = []
    annual_count = 0
    replay_count = 0
    spectra = {}
    all_seen = ()
    information_designs = []
    for year, design in enumerate(designs):
        all_seen = tuple(sorted(set(all_seen) | set(design['players'])))
        raw, H, u = embed_recovery_information(design, all_seen)
        P = _centering(u)
        _close(H @ P, H, 'H P differs from H')
        spectra[year] = (all_seen, raw, H, u, P, _rank(raw), _rank(H))
        for probe, spectrum in (('context_known', spectra[year][5]), ('context_adjusted', spectra[year][6])):
            eigenvalues, eigenvectors, tau, masks = spectrum
            information_designs.append(dict(year=year + 1, probe=probe, ordered_player_ids=list(all_seen),
                row_order='offense then defense', eigenvalues=eigenvalues.tolist(), tau=tau,
                rank_at_tau_factors=[int(mask.sum()) for mask in masks],
                null_directions=eigenvectors[:, ~masks[1]].T.tolist(),
                exposure_reference_constraints=dict(count=2, weights=u.tolist(),
                    meaning='one weighted reference equation per role, separate from likelihood null directions')))
        for index, request in enumerate(request_rows):
            if request['year'] != year + 1:
                continue
            if request['status'] != 'available':
                information.append(dict(year=year + 1, request=request['name'], representation=None, case=None,
                    outer=None, probe='likelihood', status='not_assessed', reason=request['reason'], truth=None))
                continue
            c_current = _coefficient(request, design['players'])
            actual = 40 * c_current @ design['truth_shape']
            projected = (actual @ basis.B) @ basis.R.T
            truths[active_position[index]] = actual
            geometry.append(dict(year=year + 1, request=request['name'], representation='graph_40ft', case=None, outer=None,
                probe='geometric_oracle', status='available', native=pattern_metrics(projected, actual),
                regional=pattern_metrics(projected @ W, actual @ W), actual_regions=(actual @ W).tolist(),
                projected_regions=(projected @ W).tolist(), units=UNITS,
                supplied_oracle_information='actual saved native truth; weighted graph geometry',
                fixed='native truth/reference/grid', changed='weighted geometric projection only'))
            c = _coefficient(request, all_seen)
            for representation in REPRESENTATIONS:
                for probe, Hprobe, spec in (('context_known', raw, spectra[year][5]), ('context_adjusted', H, spectra[year][6])):
                    row = _information(Hprobe, P, c, spec, S[representation], W,
                        {name: np.asarray(request['functionals'][name]) for name in scalar_names}, actual, 40.)
                    information.append(dict(year=year + 1, request=request['name'], representation=representation,
                        case=None, outer=None, probe=probe, **row))
                    if row['status'] == 'numerically_unresolved':
                        unresolved.append(dict(mechanism='numerical_rank', year=year + 1, request=request['name'],
                            representation=representation, probe=probe, status='numerically_unresolved'))
    analytic = _grid(designs[0], basis, request_rows)
    for outer_ref in means['outers']:
        case_id, outer_id = outer_ref['case_id'], outer_ref['outer_id']
        outer, arrays, states, count = _load_outer(outer_ref['manifest'], prepared, means, basis, designs, case_id, outer_id)
        bytes_read += count
        receipt_start = len(state_receipts)
        replay_populations = {}
        if outer_id == 0:
            for year, design in enumerate(designs):
                response_design = dict(design, mu=40 * (design['p'] + design['X'] @ design['truth_map']))
                responses = synthetic_counts(response_design, case_id, outer_id, year)
                del response_design
                response_digest = ordered_array_digest(dict(responses=responses))
                require(outer['response_digests'][year] == dict(season=SEASONS[year], sha256=response_digest),
                        'selected original response replay digest differs')
                grouped, references = synthetic_population(design, responses, year, prepared['source_protocol']['sha256'], case_id, outer_id)
                population = weighted_population(grouped, np.ones(len(grouped.game_ids)), references)
                statistic = statistic_digest(population)
                require(outer['statistic_digests'][year] == dict(season=SEASONS[year], sha256=statistic),
                        'selected original sufficient-statistic replay digest differs')
                replays.append(dict(case=CASES[case_id], outer=outer_id, year=year + 1,
                    response_sha256=response_digest, statistic_sha256=statistic, status='available'))
                replay_populations[year] = population
                replay_count += 1
                del responses, grouped
        for rep_id, representation in enumerate(REPRESENTATIONS):
            previous_F = None
            previous_ids = ()
            for year, (state, design) in enumerate(zip(states[representation], designs, strict=True)):
                players, raw, H, u, P, _, _ = spectra[year]
                require(state.player_ids == players and np.array_equal(state.u, u), 'saved all-seen/reference order differs')
                theta = design['truth_shape'] @ basis.B if representation == 'graph_40ft' else design['truth_shape']
                current_score = design['H'] @ theta
                score = np.zeros((len(H), theta.shape[1]))
                current_indices = np.array([players.index(player) for player in design['players']])
                selected = np.r_[current_indices, len(players) + current_indices]
                score[selected] = current_score
                incoming = np.zeros_like(score)
                if previous_F is not None:
                    old_indices = np.array([players.index(player) for player in previous_ids])
                    incoming[np.r_[old_indices, len(players) + old_indices]] = previous_F
                update = fixed_shape_update(H, incoming, state.shape.prior_covariance, score, u)
                residual = _close(update.covariance, state.shape.V, 'saved shape covariance does not reconcile')
                residual = max(residual, _close(P.T @ score, score, "P' Q differs from Q"))
                carry = (P - update.gain) @ incoming
                current = update.covariance @ score
                F = update.mean
                residual = max(residual, _close(carry + current, F, 'frozen carry/current identity differs'))
                one_step = (P - update.gain) @ state.shape.prior_mean + current
                fitted = state.shape.Theta if representation == 'graph_40ft' else state.shape.M
                values = (fitted, F, incoming, carry, current, one_step, fitted - F, F - incoming,
                        state.shape.prior_mean, one_step - state.shape.prior_mean)
                factor = np.linalg.cholesky(state.shape.prior_covariance)
                eigenvalues = np.linalg.eigvalsh(factor.T @ H @ factor)
                require(float(eigenvalues[0]) >= - 1e-8 * (1 + float(eigenvalues[- 1])),
                        'prior-standardized information has negative eigenvalue')
                modes.append(dict(representation=representation, case=CASES[case_id], outer=outer_id, year=year + 1,
                    probe='prior_standardized_modes', eigenvalues=eigenvalues.tolist(),
                    transfer=(eigenvalues / (1 + eigenvalues)).tolist(),
                    meaning='prior-standardized directions; not individual player gains'))
                scale = state.shape.scale
                state_receipts.append(dict(representation=representation, case=CASES[case_id], outer=outer_id, year=year + 1,
                    status='available', entry_variance=state.shape.a, innovation_variance=state.shape.q,
                    selected=scale['selected'], endpoint='endpoint_winner' in scale['own_reasons'],
                    inherited=scale['inherited_limitation'], scale_status=scale['status'],
                    maximum_relative_residual=residual, equation_relative_residual=update.diagnostics['equation_relative_residual'], entrant_ids=list(state.entrant_ids), carried_only_ids=list(state.carried_only_ids)))
                annual_count += 1
                if year == 0:
                    coarse = [row for row in scale['curve'] if row['phase'] == 'coarse']
                    require(len(coarse) == 17 and [row['variance'] for row in coarse] == list(VARIANCES)
                        and all(row['error'] is None for row in coarse), 'original first-year grid differs')
                    objective = np.array([row['objective'] for row in coarse])
                    curves[(case_id, representation)].append(objective - objective[0])
                for index, request in enumerate(request_rows):
                    if request['year'] != year + 1 or request['status'] != 'available':
                        continue
                    pos = active_position[index]
                    c = _coefficient(request, players)
                    coefficient_values = np.stack([40 * c @ value for value in values])
                    native = coefficient_values @ basis.R.T if representation == 'graph_40ft' else coefficient_values
                    projections[case_id, outer_id, rep_id, pos] = native @ vectors
                    native_sums[case_id, rep_id, pos] += native
                    if outer_id == 0:
                        native_examples[case_id, rep_id, pos] = native
                if outer_id == 0:
                    population = replay_populations[year]
                    native_score = population.T - population.T.sum(axis=1, keepdims=True) * p
                    replay_score = np.zeros_like(score)
                    replay_score[selected] = native_score @ basis.B if representation == 'graph_40ft' else native_score
                    replay = fixed_shape_update(H, state.shape.prior_mean, state.shape.prior_covariance, replay_score, u)
                    residual = _close(replay.mean, fitted, 'selected saved shape mean replay differs')
                    xbar = np.zeros((len(population.xbar), len(H)))
                    xbar[:, selected] = population.xbar
                    yh = population.ybar - population.ybar.sum(axis=1, keepdims=True) * p
                    replay_native = replay.mean @ basis.R.T if representation == 'graph_40ft' else replay.mean
                    residual = max(residual, _close(yh - xbar @ replay_native, state.shape.A,
                        'selected saved shape context replay differs'))
                    volume_score = np.zeros((len(H), 1))
                    volume_score[selected] = population.T.sum(axis=1, keepdims=True)
                    volume = fixed_shape_update(H, state.volume.prior_mean, state.volume.prior_covariance, volume_score, u)
                    residual = max(residual, _close(volume.mean, state.volume.M, 'selected saved volume mean replay differs'))
                    residual = max(residual, _close(volume.covariance, state.volume.V, 'selected saved volume covariance replay differs'))
                    residual = max(residual, _close(population.ybar.sum(axis=1, keepdims=True) - xbar @ volume.mean, state.volume.A,
                        'selected saved volume context replay differs'))
                    response_part = replay.mean - one_step
                    residual = max(residual, _close(fitted - F, (one_step - F) + response_part,
                        'selected actual/frozen/saved-incoming response decomposition differs'))
                    replays.append(dict(representation=representation, case=CASES[case_id], outer=outer_id, year=year + 1,
                        probe='posterior_context_and_mean_response', status='available', maximum_relative_residual=residual,
                        shape_equation_relative_residual=replay.diagnostics['equation_relative_residual'],
                        volume_equation_relative_residual=volume.diagnostics['equation_relative_residual']))
                previous_F = F
                previous_ids = players
        metric_keys = [(row['year'], row['contrast'], row['representation']) for row in outer['error_metrics']]
        require(len(metric_keys) == 16 and set(metric_keys) == {(year, contrast, representation)
            for year in (1, 5) for contrast in ('radial', 'lateral', 'local', 'rough') for representation in REPRESENTATIONS},
            'saved original metric identities are missing or duplicated')
        for metric in outer['error_metrics']:
            year = metric['year']
            representation = metric['representation']
            contrast = metric['contrast']
            state = states[representation][year - 1]
            design = designs[year - 1]
            pair = dict(radial=(3, 4), lateral=(10, 11), local=(18, 19), rough=(20, 21))[contrast]
            request = dict(role='offense', coefficients=[[pair[0], 1], [pair[1], - 1]])
            c = _coefficient(request, state.player_ids)
            ct = _coefficient(request, design['players'])
            fitted = 40 * c @ shape_mean(state)
            truth = 40 * ct @ design['truth_shape']
            volume = 40 * float(c @ state.volume.M[:, 0])
            true_volume = 40 * float(ct @ design['truth_scalar'])
            complete = fitted + volume * p
            complete_truth = truth + true_volume * p
            for name, actual in dict(native_shape_error=float((fitted - truth) @ (fitted - truth)),
                region_shape_error=float(((fitted - truth) @ W) @ ((fitted - truth) @ W)),
                region_shape_truth_energy=float((truth @ W) @ (truth @ W)), native_shape_truth_energy=float(truth @ truth)).items():
                _close(actual, metric[name], '04c saved original map metric differs')
            _close(fitted, arrays[f'{representation}_{year}_{contrast}_shape'], 'saved primary native shape differs from state')
            _close(complete, arrays[f'{representation}_{year}_{contrast}_complete'], 'saved complete map differs from state')
            _close(truth, arrays[f'truth_{year}_{contrast}_shape'], 'saved truth differs from bound annual arrays')
            key = (case_id, year, contrast, representation)
            if key not in patterns:
                patterns[key] = dict(n=0, shape_sum=np.zeros(width), complete_sum=np.zeros(width), shape_error=0.,
                    region_error=0., complete_error=0., volume_only_error=0., truth=truth, complete_truth=complete_truth, W=W)
            a = patterns[key]
            a['n'] += 1
            a['shape_sum'] += fitted
            a['complete_sum'] += complete
            a['shape_error'] += float((fitted - truth) @ (fitted - truth))
            a['region_error'] += metric['region_shape_error']
            a['complete_error'] += float((complete - complete_truth) @ (complete - complete_truth))
            comparator = volume * p - complete_truth
            a['volume_only_error'] += float(comparator @ comparator)
        for contrast in ('radial', 'lateral'):
            rows = [row for row in outer['error_metrics'] if row['year'] == 5 and row['contrast'] == contrast]
            candidate = next(row['region_shape_error'] for row in rows if row['representation'] == 'graph_40ft')
            native = next(row['region_shape_error'] for row in rows if row['representation'] == 'native_04b')
            energy = rows[0]['region_shape_truth_energy']
            gains[(case_id, contrast, 'zero_shape')].append((energy, candidate))
            gains[(case_id, contrast, 'native_04b')].append((native, candidate))
        for row in outer['projections']['graph_40ft']:
            request = old_by_key[row['key']]
            if request['group'] not in ('annual_transition', 'volume'):
                continue
            state = states['graph_40ft'][SEASONS.index(request['season'])]
            c = _coefficient(request, state.player_ids)
            estimated = 40 * float(c @ state.volume.M[:, 0]) if request['estimand'] == 'volume' else 40 * float(c @ shape_mean(state) @ np.asarray(request['weights']))
            _close(estimated, row['mean'], 'saved 04c transition/volume projection differs')
            design = designs[SEASONS.index(request['season'])]
            ct = _coefficient(request, design['players'])
            true_value = 40 * float(ct @ design['truth_scalar']) if request['estimand'] == 'volume' else 40 * float(ct @ design['truth_shape'] @ np.asarray(request['weights']))
            _close(true_value, row['truth'], 'saved 04c transition truth differs from saved annual truth arrays')
            key = (outer['case'], row['key'])
            if key not in transitions:
                transitions[key] = dict(n=0, error=0., error2=0., truth=row['truth'])
            a = transitions[key]
            require(a['truth'] == row['truth'], 'saved transition truth changed')
            delta = estimated - row['truth']
            a['n'] += 1
            a['error'] += delta
            a['error2'] += delta * delta
        outer_receipts.append(dict(case=CASES[case_id], outer=outer_id, manifest=outer_ref['manifest'], arrays=outer['arrays'],
            manifest_and_archive_reads=1, bytes_read=count, annual_states=len(state_receipts) - receipt_start, status='available'))
        del outer, arrays, states, replay_populations
    reconciliations = _reconcile_summaries(result, means, patterns, transitions, gains)
    curve_rows = []
    for (case_id, representation), values in curves.items():
        values = np.stack(values)
        require(len(values) == n, 'paired curve denominator differs')
        for j, variance in enumerate(VARIANCES):
            samples = values[:, j]
            curve_rows.append(dict(case=CASES[case_id], representation=representation, outer=None, year=1,
                request=None, probe='paired_saved_objective_difference', variance=variance, n=n,
                mean=float(samples.mean()), monte_carlo_standard_error=float(samples.std(ddof=1) / np.sqrt(n)) if case_id == 0 and n > 1 else None,
                mcse_status='available' if case_id == 0 and n > 1 else 'not_assessed',
                mcse_reason=None if case_id == 0 and n > 1 else 'single_path_fixture' if case_id == 0 else 'game_pace_precision_outside_scope',
                meaning='within-path difference from a=1e-8; gaussian matched expectation only' if case_id == 0
                    else 'game-pace observations; no matched gaussian precision claim'))
    distributions = []
    for case_id, case in enumerate(CASES):
        for rep_id, representation in enumerate(REPRESENTATIONS):
            for pos, index in enumerate(active):
                request = request_rows[index]
                truth = truths[pos] @ W
                for probe_id, probe in enumerate(PROBES):
                    values = projections[case_id,:, rep_id, pos, probe_id]
                    distributions.append(dict(case=case, representation=representation, year=request['year'],
                        request=request['name'], probe=probe, status='available',
                        likelihood_status=next(row['status'] for row in information if row['request'] == request['name']
                            and row['year'] == request['year'] and row['representation'] == representation and row['probe'] == 'context_adjusted'),
                        units=UNITS, **_summary(values)))
                    metric_values = [pattern_metrics(value[: 12], truth) for value in values]
                    request_metrics.append(dict(case=case, representation=representation, year=request['year'],
                        request=request['name'], probe=probe, status='available',
                        likelihood_status=next(row['status'] for row in information if row['request'] == request['name']
                            and row['year'] == request['year'] and row['representation'] == representation and row['probe'] == 'context_adjusted'),
                        units=SQUARED_UNITS,
                        truth_energy=float(truth @ truth), squared_error=_summary([v['squared_error'] for v in metric_values]),
                        normalized_squared_error=_summary([v['normalized_squared_error'] for v in metric_values]) if truth @ truth > 0 else None,
                        truth_alignment=_summary([v['truth_alignment'] for v in metric_values]) if truth @ truth > 0 else None,
                        ratio_reason=None if truth @ truth > 0 else 'zero_truth_energy'))
    require(annual_count == 20 * n and replay_count == 10 and len(outer_receipts) == 2 * n, 'complete finite accounting differs')
    output = output_path(str(out), [str(Path(ref['path']).parent) for ref in (baseline_ref, protocol_ref)])
    require(output.is_relative_to(Path(frozen['output_root'])), 'diagnosis differs from the frozen output root')
    if frozen['purpose'] == 'research':
        require(output.is_relative_to(RESEARCH_ROOT), 'research diagnosis must remain external-only')
    output.mkdir()
    binding = write_arrays(output, 'diagnostics.npz', dict(path_projections=projections,
        aggregate_native=native_sums / n, outer_zero_native=native_examples, actual_native_truth=truths,
        projected_native_truth=(truths @ basis.B) @ basis.R.T,
        W=W, p=p, centers=designs[0]['centers']))
    diagnostic = artifact('attribution_information_diagnosis', frozen['purpose'],
        dict(protocol=protocol_ref, baseline_result=baseline_ref, spec_snapshot=frozen['spec_snapshot'], **refs),
        protocol=protocol_ref, baseline_result=baseline_ref, spec_snapshot=frozen['spec_snapshot'],
        output_root=frozen['output_root'],
        model_implementation=result['model_implementation'], model_protocol=prepared['model_protocol'],
        source_kind='synthetic', units=dict(shape=UNITS, squared_error=SQUARED_UNITS),
        status='incomplete' if unresolved else 'complete', requests=request_rows, active_request_indices=active,
        probes=list(PROBES), probe_meanings=PROBE_MEANINGS, functionals=[*prepared['regions'], *scalar_names], representations=list(REPRESENTATIONS), cases=list(CASES),
        geometry=geometry, information=information, information_designs=information_designs, distributions=distributions, request_metrics=request_metrics,
        fixed_grid=analytic, saved_curve_differences=curve_rows, state_receipts=state_receipts,
        prior_standardized_modes=modes, outer_receipts=outer_receipts, replay_receipts=replays,
        reconciliations=reconciliations, unresolved=unresolved, reference_truth_identity=frozen['geometry'],
        information_receipts=[dict(year=year + 1, **design['information_reconciliation']) for year, design in enumerate(designs)],
        accounting=dict(outer_manifests=len(outer_receipts), outer_archives=len(outer_receipts), annual_states=annual_count,
            annual_designs=5, analytic_states=len(analytic), response_arrays=replay_count, new_draws=0, fits=0,
            scale_selections=0, bootstrap=0), array_axes=dict(path_projections=['case', 'outer', 'representation', 'active_request', 'probe', 'functional'],
            aggregate_native=['case', 'representation', 'active_request', 'probe', 'cell'],
            outer_zero_native=['case', 'representation', 'active_request', 'probe', 'cell'], actual_native_truth=['active_request', 'cell']),
        metric_contract=dict(reference='annual outputs use the original current-player exposure reference; raw incoming probes retain their preceding reference',
            truth='saved native annual truth arrays; carried-only rows have no current truth',
            supplied_oracles='actual synthetic truth and, where named, known context or gaussian observation law',
            fixed='original designs, references, scales and full covariance histories', changed='noise-removed or actual-incoming mean-response interventions only',
            shape='zero-sum native allocation; attempts/60 team minutes',
            quantiles='5/50/95 percent distributions of diagnostics across original paths within each case and year, not confidence intervals'),
        limitations=LIMITATIONS, resources=dict(**resources(started), process_seconds=time.process_time() - process_started,
            bytes_read=bytes_read, outer_stream_bytes_read=sum(row['bytes_read'] for row in outer_receipts),
            bytes_read_scope='all consumed payload reads including initial identity hashes and exact spec validation; original outer manifests and archives each once'),
        admission='not_admitted', handoff=None, **binding)
    path = output / 'diagnosis.json'
    write_json(path, json_values(diagnostic))
    return identity(path)


def _figures(diagnosis, arrays, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plt.rcParams.update({'font.size': 9, 'axes.titlesize': 10, 'axes.labelsize': 8, 'legend.fontsize': 7})
    centers = arrays['centers']
    active = diagnosis['active_request_indices']
    requests_ = diagnosis['requests']
    position = {index: pos for pos, index in enumerate(active)}
    rows = [next((index, row) for index, row in enumerate(requests_) if row['year'] == 5 and token in row['name'])
          for token in ('radial_3_minus_4', 'lateral_10_minus_11', 'local_18_minus_19', 'rough_20_minus_21')]
    fig, axes = plt.subplots(3, 4, figsize=(17, 10), gridspec_kw={'height_ratios': [1, 1, 1.25]})
    for col, (index, request) in enumerate(rows):
        pos = position[index]
        truth = arrays['actual_native_truth'][pos]
        projection = arrays['projected_native_truth'][pos]
        bound = max(float(np.max(np.abs(truth))), float(np.max(np.abs(projection))))
        for row, (name, values) in enumerate((('actual native truth', truth), ('graph geometric projection', projection))):
            ax = axes[row, col]
            points = ax.scatter(centers[:, 0], centers[:, 1], c=values, cmap='RdBu_r', vmin=- bound, vmax=bound,
                marker='s', s=14, linewidths=0)
            ax.set_aspect('equal')
            ax.set_xlim(- 100, 100)
            ax.set_ylim(- 43, 43)
            ax.set_title(request['name'].removeprefix('offense_').removesuffix('_shape') + '\n' + name)
            ax.set_xlabel('feet')
            ax.set_ylabel('feet')
            fig.colorbar(points, ax=ax, shrink=.65, label=UNITS)
        ax = axes[2, col]
        ax.axis('off')
        geo = next(row for row in diagnosis['geometry'] if row['request'] == request['name'] and row['year'] == 5)
        lines = ['year five; one symmetric scale per pattern',
            f"geometric normalized error: native {geo['native']['normalized_squared_error']:.4g}",
            f"regional {geo['regional']['normalized_squared_error']:.4g}",
            'likelihood precision / actual regional truth energy:']
        for representation in REPRESENTATIONS:
            for probe in ('context_known', 'context_adjusted'):
                row = next(row for row in diagnosis['information'] if row['request'] == request['name']
                    and row['year'] == 5 and row['representation'] == representation and row['probe'] == probe)
                ratio = row['variance_to_actual_truth_energy']
                label = f'{ratio:.3g}' if ratio is not None else row['status']
                lines.append(f"{representation}, {probe}: {label}")
                lines.append(f"rank {row['rank']}/{row['dimension']}; null projection {row['null_projection']:.2g}")
        lines.extend(['two exposure-reference constraints are separate',
                      'from likelihood null directions; see directional table'])
        ax.text(0, 1, '\n'.join(lines), va='top', fontsize=8)
    execution_label = 'fixture exercise; ' if diagnosis['purpose'] == 'fixture_exercise' else ''
    if diagnosis['status'] != 'complete':
        execution_label += 'execution incomplete; affected rank states unresolved; '
    fig.suptitle(execution_label + 'representation and likelihood information: synthetic offense contrasts\n'
        'original exposure-weighted reference; positive shape means attempt creation; weighted geometry is not achieved recovery', fontsize=13)
    fig.text(.5, .015, 'gaussian precision assumes the stated working observation law; context-known information is an oracle comparison. '
        'projected truth never replaces actual truth. scales differ between patterns.', ha='center', fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, .92))
    first = output / 'representation-information.png'
    fig.savefig(first, dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(4, 4, figsize=(19, 17))
    distributions = {(row['case'], row['representation'], row['request'], row['year'], row['probe']): row
                   for row in diagnosis['distributions']}
    paths = arrays['path_projections']
    n = paths.shape[1]
    for row, token in enumerate(('radial_3_minus_4', 'lateral_10_minus_11')):
        scalar = 12 + row
        for col, (case, representation) in enumerate((c, r) for c in CASES for r in REPRESENTATIONS):
            ax = axes[row, col]
            name = 'offense_' + token + '_shape'
            for probe, color in (('fitted', 'black'), ('frozen', 'tab:blue'), ('carry', 'tab:green'), ('current', 'tab:red')):
                values = [distributions[(case, representation, name, year, probe)] for year in range(1, 6)]
                mean = np.array([v['mean'][scalar] for v in values])
                quantiles = np.array([v['quantiles'] for v in values])[:,:, scalar]
                ax.plot(range(1, 6), mean, label=probe, color=color, marker='o', markersize=3)
                if probe in ('fitted', 'frozen'):
                    ax.fill_between(range(1, 6), quantiles[:, 0], quantiles[:, 2], color=color, alpha=.12)
                    ax.plot(range(1, 6), quantiles[:, 1], color=color, linestyle=':', linewidth=.8)
            truth = []
            for year in range(1, 6):
                index = next(index for index, request in enumerate(requests_) if request['name'] == name and request['year'] == year)
                pos = position[index]
                weights = np.asarray(requests_[index]['functionals']['radial' if row == 0 else 'lateral'])
                truth.append(arrays['actual_native_truth'][pos] @ weights)
            ax.plot(range(1, 6), truth, label='actual truth', color='tab:purple', linestyle='--')
            ax.set_title(f'{case} / {representation}\n' + token)
            ax.set_xticks(range(1, 6))
            ax.set_xlabel('synthetic year')
            ax.set_ylabel(UNITS)
            ax.legend(loc='best', ncol=2)
    for row in range(2):
        lower = min(ax.get_ylim()[0] for ax in axes[row])
        upper = max(ax.get_ylim()[1] for ax in axes[row])
        for ax in axes[row]:
            ax.set_ylim(lower, upper)
    controls = [('offense_entrant_32_shape', 'radial', 'entrant 32 offense'),
        ('defense_entrant_33_shape', 'lateral', 'entrant 33 defense; positive = opponent creation'),
        ('offense_returner_8_shape', 'radial', 'returner 8 offense; year three absent / no truth')]
    for col, (name, functional, title) in enumerate(controls):
        ax = axes[2, col]
        scalar = 12 if functional == 'radial' else 13
        selected = [(index, r) for index, r in enumerate(requests_) if r['name'] == name]
        years = [r['year'] for _, r in selected]
        for rep_id, representation in enumerate(REPRESENTATIONS):
            for probe_id, probe, style in ((0, 'fitted', '-'), (1, 'frozen', '--')):
                values = [paths[0, 0, rep_id, position[index], probe_id, scalar]
                        if r['status'] == 'available' else np.nan for index, r in selected]
                ax.plot(years, values, linestyle=style, marker='o', label=representation + ' ' + probe)
        truth = [arrays['actual_native_truth'][position[index]] @ np.asarray(r['functionals'][functional])
               if r['status'] == 'available' else np.nan for index, r in selected]
        ax.plot(years, truth, color='black', linestyle=':', label='actual truth')
        ax.set_title(title.replace('; ', '\n') + '\ngaussian outer zero; saved ' + functional + ' functional', fontsize=8)
        ax.set_xticks(years)
        ax.set_xlabel('synthetic year')
        ax.set_ylabel(UNITS)
        ax.legend(loc='best')
    ax = axes[2, 3]
    for name, label, color in (('offense_pair_26_minus_31_shape', 'difference: not estimable', 'tab:red'),
                            ('offense_pair_26_plus_31_shape', 'sum: separate functional', 'tab:blue')):
        indices = [next(index for index, r in enumerate(requests_) if r['name'] == name and r['year'] == year) for year in range(1, 6)]
        for probe_id, probe, style in ((0, 'fitted', '-'), (1, 'frozen', '--')):
            ax.plot(range(1, 6), [paths[0, 0, 0, position[index], probe_id, 13] for index in indices],
                color=color, linestyle=style, marker='o', label=label + ' ' + probe)
        weights = np.asarray(requests_[indices[0]]['functionals']['lateral'])
        ax.plot(range(1, 6), [arrays['actual_native_truth'][position[index]] @ weights for index in indices],
            color=color, linestyle=':', label=label + ' actual truth')
    ax.set_title('paired 26/31; prior-supplied allocation is not evidence\ngraph / gaussian outer zero; saved lateral functional', fontsize=8)
    ax.set_xlabel('synthetic year')
    ax.set_ylabel(UNITS)
    ax.set_xticks(range(1, 6))
    ax.legend(loc='best')
    for col, representation in enumerate(REPRESENTATIONS):
        ax = axes[3, col]
        analytic = [row for row in diagnosis['fixed_grid'] if row['representation'] == representation]
        ax.semilogx(VARIANCES, [row['objective_difference'] for row in analytic], label='gaussian analytic expectation', color='black')
        for case, color in (('gaussian', 'tab:blue'), ('game_pace', 'tab:orange')):
            rows_ = [row for row in diagnosis['saved_curve_differences'] if row['representation'] == representation and row['case'] == case]
            mean = np.array([row['mean'] for row in rows_])
            ax.semilogx(VARIANCES, mean, label=case + ' paired saved mean', color=color, linestyle='--')
            if case == 'gaussian' and n > 1:
                se = np.array([row['monte_carlo_standard_error'] for row in rows_])
                ax.fill_between(VARIANCES, mean - se, mean + se, color=color, alpha=.18, label='mean ± 1 monte carlo se')
        ax.set_title(representation + ' first-year criterion differences\nreference a=1e-8; levels across representations incomparable')
        lowest = min(analytic, key=lambda row: row['objective_difference'])
        ax.text(.03, .97, f"lowest enumerated expectation: a={lowest['variance']:.3g}",
            transform=ax.transAxes, va='top', fontsize=7)
        ax.set_xlabel('fixed prior variance a')
        ax.set_ylabel('objective difference')
        ax.legend(loc='best')
    for col, token in enumerate(('radial_3_minus_4', 'lateral_10_minus_11'), start=2):
        ax = axes[3, col]
        for representation in REPRESENTATIONS:
            rows_ = [row for row in diagnosis['fixed_grid'] if row['representation'] == representation]
            risks = [next(risk for risk in row['risks'] if token in risk['request']) for row in rows_]
            best = int(np.argmin([risk['expected_error'] for risk in risks]))
            ax.semilogx(VARIANCES, [risk['expected_error'] for risk in risks],
                label=f'{representation}; lowest enumerated a={VARIANCES[best]:.3g}', marker='.', markersize=3)
        ax.set_title(token + ' first-year gaussian regional risk\ntruth-informed oracle diagnostic; no selected replacement')
        ax.set_xlabel('fixed prior variance a')
        ax.set_ylabel(SQUARED_UNITS)
        ax.legend(loc='best')
    fig.suptitle(execution_label + 'frozen-path transmission and fixed-grid scale pressure\n'
        'selected covariance histories held fixed; these interventions are not expectations conditional on scales', fontsize=14)
    fig.text(.5, .012, f'shading/dots in annual panels: 5/50/95% distribution of {n} original path diagnostics per case, not confidence intervals. '
        'carry/current are signed computational contrasts, not independent sources of error. transition/null examples are outer zero only.',
        ha='center', fontsize=8)
    fig.tight_layout(rect=(0, .035, 1, .95))
    second = output / 'transmission-scale-pressure.png'
    fig.savefig(second, dpi=150)
    plt.close(fig)
    return [dict(name='representation_information', reference=identity(first)),
            dict(name='transmission_scale_pressure', reference=identity(second))]


def assess(diagnosis, out):
    """only compact diagnosis outputs inform the explanation and figures."""
    started, process_started = time.monotonic(), time.process_time()
    diagnosis_ref = identity(Path(diagnosis).resolve(strict=True))
    diagnosed, bytes_read = _bound(diagnosis_ref, 'attribution_information_diagnosis')
    bytes_read += Path(diagnosis_ref['path']).stat().st_size
    arrays, count = _bound(diagnosed['arrays'], arrays=True)
    bytes_read += count
    require(list(arrays) == [row['name'] for row in diagnosed['array_shapes']]
        and all(list(arrays[row['name']].shape) == row['shape'] and arrays[row['name']].dtype.str == row['dtype']
            for row in diagnosed['array_shapes']), 'diagnostic compact array identity differs')
    output = output_path(str(out), [str(Path(diagnosis_ref['path']).parent)])
    require(output.is_relative_to(Path(diagnosed['output_root'])), 'assessment differs from the frozen output root')
    if diagnosed['purpose'] == 'research':
        require(output.is_relative_to(RESEARCH_ROOT), 'research assessment must remain external-only')
    output.mkdir()
    refs = dict(geometry=diagnosis_ref, information=diagnosis_ref, transmission=diagnosis_ref, fixed_grid=diagnosis_ref)
    complete = diagnosed['status'] == 'complete' and not diagnosed['unresolved']
    findings = []
    if complete:
        geometry = diagnosed['geometry']
        primary = [row for row in geometry if 'radial_3_minus_4' in row['request'] or 'lateral_10_minus_11' in row['request']]
        findings.append(dict(mechanism='representation', evidence_refs=[refs['geometry']],
            observation='weighted graph projection preserves broad truth with the measured omitted component; local and rough residuals remain separately reported',
            metrics=dict(primary_regional_normalized_error_range=[min(row['regional']['normalized_squared_error'] for row in primary),
                max(row['regional']['normalized_squared_error'] for row in primary)]),
            contrary_evidence='representability alone supplies neither observation information nor achieved recovery',
            scope='original native truth and fixed graph geometry', limitations=['projection need not minimize regional error']))
        adjusted = [row for row in diagnosed['information'] if row['probe'] == 'context_adjusted' and row['status'] != 'not_assessed']
        primary_names = {'offense_radial_3_minus_4_shape', 'offense_lateral_10_minus_11_shape'}
        precision = [{key: row[key] for key in ('year', 'request', 'representation', 'probe', 'status',
                    'null_projection', 'regional_total_variance', 'variance_to_actual_truth_energy')}
                   for row in diagnosed['information'] if row['request'] in primary_names]
        findings.append(dict(mechanism='likelihood_information', evidence_refs=[refs['information']],
            observation='contrast-specific null projections and gaussian likelihood variances separate deployment identification from exposure-reference constraints',
            metrics=dict(status_counts={status: sum(row['status'] == status for row in adjusted)
                for status in ('available', 'not_estimable', 'zero_functional', 'numerically_unresolved')},
                primary_contrast_precision=precision),
            contrary_evidence='an estimable paired sum does not identify either individual; known context is an oracle',
            scope='five separate annual fixed designs; no constant-effect five-year pooling',
            limitations=['precision is conditional on the gaussian law and the represented component; omitted truth bias remains']))
        metrics = {(row['case'], row['representation'], row['year'], row['request'], row['probe']): row
                 for row in diagnosed['request_metrics']}
        distribution = {(row['case'], row['representation'], row['year'], row['request'], row['probe']): row
                      for row in diagnosed['distributions']}
        transmission = []
        for case in CASES:
            for representation in REPRESENTATIONS:
                for name in sorted(primary_names):
                    functional = 12 if 'radial' in name else 13
                    for year in range(1, 6):
                        prefix = (case, representation, year, name)
                        entry = dict(case=case, representation=representation, year=year, request=name,
                            functional='radial' if functional == 12 else 'lateral', units=UNITS)
                        for probe in ('fitted', 'frozen'):
                            value = metrics[(*prefix, probe)]
                            entry[probe] = dict(mean_normalized_regional_squared_error=value['normalized_squared_error']['mean']
                                if value['normalized_squared_error'] is not None else None,
                                mean_regional_truth_alignment=value['truth_alignment']['mean']
                                if value['truth_alignment'] is not None else None)
                        entry['signed_scalar_means'] = {probe: distribution[(*prefix, probe)]['mean'][functional]
                            for probe in ('fitted', 'frozen', 'carry', 'current', 'incoming', 'saved_incoming',
                                'one_step', 'incoming_to_updated', 'one_step_minus_saved_incoming', 'actual_minus_frozen')}
                        transmission.append(entry)
        findings.append(dict(mechanism='selected_scale_transmission', evidence_refs=[refs['transmission']],
            observation='saved means, recursive frozen interventions and actual-incoming one-step interventions reconcile under all selected covariance histories',
            metrics=dict(primary_transmission=transmission, annual_states=diagnosed['accounting']['annual_states'],
                maximum_covariance_reconciliation_residual=max(row['maximum_relative_residual'] for row in diagnosed['state_receipts']),
                maximum_posterior_equation_residual=max(row['equation_relative_residual'] for row in diagnosed['state_receipts'])),
            contrary_evidence='selected scales depend on noisy responses; actual-minus-frozen remainders need not average to zero',
            scope='conditional computational contrasts, with signed carry/current and all-year distributions',
            limitations=['these are not conditional expectations given scales or a percentage-of-blame decomposition']))
        locations = []
        for representation in REPRESENTATIONS:
            rows = [row for row in diagnosed['fixed_grid'] if row['representation'] == representation]
            objective = min(rows, key=lambda row: row['objective_difference'])
            for name in ('offense_radial_3_minus_4_shape', 'offense_lateral_10_minus_11_shape'):
                best = min(rows, key=lambda row: next(r for r in row['risks'] if r['request'] == name)['expected_error'])
                locations.append(dict(representation=representation, request=name, criterion_grid_minimum=objective['variance'],
                    oracle_risk_grid_minimum=best['variance'], different_grid_locations=objective['variance'] != best['variance']))
        findings.append(dict(mechanism='first_year_scale_pressure', evidence_refs=[refs['fixed_grid']],
            observation='the exact gaussian determinant/signal/noise expectation and paired saved coarse-curve differences are compared at the existing 34 fixed states',
            metrics=dict(grid_descriptions=locations),
            contrary_evidence='a global criterion can rationally sacrifice sparse primary contrasts; monte carlo differences are not an equivalence test',
            scope='first year only; actual truth enters oracle risk; game-pace curves are observations only',
            limitations=['later priors are response-dependent; no variance is selected and game-pace sampling precision remains unresolved']))
        question = (dict(question='does the global shared-scale objective sacrifice broad primary contrasts through pooling, and would that tradeoff persist across prospectively chosen independent patterns?',
            evidence_refs=[refs['fixed_grid'], refs['transmission']],
            contrary_evidence='global prediction can rationally favor a different risk tradeoff; current risk is truth-informed and sparse',
            discriminating_check='prospectively specify a practical prediction-cost budget and independent synthetic broad-pattern population; compare global objective pressure with their contrast risks without retrospectively choosing thresholds')
            if any(row['different_grid_locations'] for row in locations) else None)
        unresolved = ['game-pace sampling precision and the reason for its comparative failure are not established by gaussian moment diagnostics',
                    'real-deployment identification, adaptive-selection uncertainty and unconditional annual-borrowing risk remain outside this known-truth diagnosis']
    else:
        question = None
        unresolved = diagnosed['unresolved']
    figures = _figures(diagnosed, arrays, output)
    result = artifact('attribution_information_result', diagnosed['purpose'],
        dict(diagnosis=diagnosis_ref, diagnostic_arrays=diagnosed['arrays'], protocol=diagnosed['protocol'], spec_snapshot=diagnosed['spec_snapshot']),
        protocol=diagnosed['protocol'], spec_snapshot=diagnosed['spec_snapshot'],
        model_implementation=diagnosed['model_implementation'], model_protocol=diagnosed['model_protocol'],
        source_kind='synthetic', units=diagnosed['units'], array_shapes=[], reference_truth_identity=diagnosed['reference_truth_identity'],
        execution_status='complete' if complete else 'incomplete', findings=findings, unresolved=unresolved,
        recommended_next_question=question, nomination=None, admission='not_admitted', handoff=None,
        figures=figures, figure_contracts=FIGURE_CONTRACTS, limitations=LIMITATIONS,
        accounting=diagnosed['accounting'], resources=dict(**resources(started), process_seconds=time.process_time() - process_started,
            bytes_read=bytes_read, bytes_read_scope='diagnosis identity hash, diagnosis json and compact diagnosis archive only'))
    path = output / 'result.json'
    write_json(path, json_values(result))
    return identity(path)


def main():
    from hockey_stats.captures import InputContractError
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    diagnostic = commands.add_parser('diagnose')
    diagnostic.add_argument('--baseline-result', required=True)
    diagnostic.add_argument('--protocol', required=True)
    diagnostic.add_argument('--out', required=True)
    assessment = commands.add_parser('assess')
    assessment.add_argument('--diagnosis', required=True)
    assessment.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        reference = diagnose(args.baseline_result, args.protocol, args.out) if args.command == 'diagnose' else assess(args.diagnosis, args.out)
    except (InputContractError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(reference['path'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
