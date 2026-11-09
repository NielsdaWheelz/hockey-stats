"""probability qualification and checked assembly for the single frozen u repair."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import resource
import sys
from time import perf_counter

import numpy as np

from .artifacts import implementation, linked_path, ordered_array_digest, require, write_json
from .chance_cli import identity
from .execution import _metadata, _probability_comparison
from .execution_fit import annual_priors, prior_mean, _complete_prior_only
from .execution_state import (_load_arrays, freeze_execution_baseline, read_execution_probe,
                              read_execution_state, write_execution_head, write_execution_probe, write_execution_state)


def _checked_numerical_qualification(basic, coefficients, iterations):
    require(type(basic) is dict and set(basic) == {'native_success', 'accepted_native_iterations', 'accepted_callbacks',
            'raw_endpoint_moved', 'fresh_start_objective', 'fresh_raw_endpoint_objective', 'completed_endpoint_moved',
            'completed_coefficients_sha256', 'basic_receipt'}, 'u qualification lacks the checked numerical contract')
    require(all(basic[name] is True for name in ('native_success', 'raw_endpoint_moved', 'completed_endpoint_moved'))
            and all(type(basic[name]) is int and basic[name] > 0 for name in ('accepted_native_iterations', 'accepted_callbacks'))
            and all(type(basic[name]) in (int, float) and np.isfinite(basic[name])
                    for name in ('fresh_start_objective', 'fresh_raw_endpoint_objective'))
            and basic['fresh_raw_endpoint_objective'] < basic['fresh_start_objective']
            and basic['completed_coefficients_sha256'] == ordered_array_digest({'coefficients': coefficients})
            and identity(Path(basic['basic_receipt']['path'])) == basic['basic_receipt'],
            'u qualification numerical evidence or endpoint binding differs')
    document = json.loads(Path(basic['basic_receipt']['path']).read_text())
    require(document['passed'] is True
            and basic['accepted_native_iterations'] == basic['accepted_callbacks'] == iterations
            and document['qualification'] == {key:value for key,value in basic.items() if key != 'basic_receipt'},
            'u inline numerical qualification differs from its receipt')


def qualify_u_bundle(bundle, result, output):
    """compare the completed u continuation against its exact frozen baseline."""
    began = perf_counter()
    require(result['status'] == 'complete' and result['requested_starts'] == ['continuation']
            and result['selected_start'] == 'continuation' and len(result['starts']) == 1
            and result['starts'][0]['converged'] is True and result['starts'][0]['iterations'] > 0,
            'u probability qualification needs a completed continuation with accepted movement')
    basic = result.get('u_repair_qualification')
    _checked_numerical_qualification(basic, result['coefficients'], result['starts'][0]['iterations'])
    source = bundle['metadata']
    require(identity(Path(source['donor']['path'])) == source['donor'], 'u qualification donor identity differs')
    donor = read_execution_state(source['donor']['path'], source['purpose'])
    require(source['baseline_head'] == donor.heads['u'] and source['recipe'] == donor.manifest['recipe']
            and source['season'] == donor.manifest['season'], 'u qualification baseline metadata differs')
    selector = json.loads((donor.path.parent / 'resolution/baseline.json').read_text())['selector']
    require(bundle['selector'] == selector, 'u qualification changed frozen selector')
    require([probe.key for probe in bundle['probes']] == selector['keys'] + [row['key'] for row in selector['fixture_witnesses']]
            and all(row['disposition'] in ('actual', 'fixture') for row in selector['requirements']),
            'u qualification lacks frozen probe requirements')
    coefficients = result['coefficients']
    require(type(coefficients) is np.ndarray and coefficients.dtype == np.float64
            and coefficients.shape == bundle['initial'].shape and np.isfinite(coefficients).all()
            and not np.array_equal(coefficients, bundle['initial']), 'u completed endpoint is invalid or unchanged')
    actors = annual_priors(bundle['design'], source['incoming_ledger'])
    require(_complete_prior_only(coefficients, actors).tobytes() == coefficients.tobytes(),
            'u endpoint did not complete prior-only actor means')
    for actor in actors:
        actor['prior_mean'] = prior_mean(actor, coefficients)
    require(actors == result['actors'], 'u continuation changed actor priors or support')
    metadata = _metadata(bundle['design'], dict(result, actors=actors), source['incoming_ledger'], source['season'])
    metadata['arrays'] = donor.heads['u']['arrays']
    heads, arrays = dict(donor.heads), dict(donor.arrays)
    heads['u'], arrays['u'] = metadata, dict(coefficients=coefficients)
    variant = replace(donor, heads=heads, arrays=arrays, usage='numerical_probe')
    locators = {}
    comparison = dict(result['comparison'], **_probability_comparison(donor, variant, bundle['probes'], locators=locators))
    require(all(comparison['head_maximum_changes'][head] == 0. for head in ('q', 'r', 'g')),
            'u qualification changed a fixed q/r/g branch')
    passed = comparison['maximum_probability_change'] <= 1e-5
    output = Path(output).resolve()
    output.mkdir()
    members = None
    if passed:
        (output / 'heads').mkdir()
        write_execution_head(output, metadata, arrays['u'], source['season'])
        members = {name: identity(output / f'heads/u.{suffix}') for name, suffix in (('metadata', 'json'), ('arrays', 'npz'))}
    path = output / 'qualification.json'
    write_json(path, dict(kind='execution-u-repair-probability-qualification', probability_passed=passed,
                         donor=source['donor'], numerical_qualification=basic, frozen_selector=selector, comparison=comparison, locators=locators,
                         members=members, wall_seconds=perf_counter()-began,
                         scope='completed u endpoint on frozen actual, attributed fixture and six-type/all-cell probes; numerical movement and fresh repaired objective checks belong to repair receipt'))
    return dict(probability_passed=passed, comparison=comparison, locators=locators,
                metadata=metadata, arrays=arrays['u'], receipt=path)


def assemble_u_repair(repair_path, output):
    """assemble only a qualified saved repair; never fit, compare or rebuild inputs."""
    read_started = perf_counter()
    repair_path = Path(repair_path).resolve(strict=True)
    report = json.loads(repair_path.read_text())
    require(report['status'] == 'qualified' and report['eligible_endpoint'] is True
            and report['assembly_performed'] is False, 'u repair is not qualified for assembly')
    for name in ('inputs', 'diagnosis', 'probability_qualification', 'basic_receipt'):
        linked_path(report[name])
    diagnosis = json.loads(Path(report['diagnosis']['path']).read_text())
    require(diagnosis['status'] == 'arithmetic_repair_permitted' and diagnosis['reproduced'] is True
            and diagnosis['first_positive_witness']['positive_witness'] is True
            and diagnosis['bundle_manifest_sha256'] == report['inputs']['sha256'], 'u assembly diagnosis/input binding differs')
    qualification_path = Path(report['probability_qualification']['path'])
    qualified = json.loads(qualification_path.read_text())
    require(qualified['kind'] == 'execution-u-repair-probability-qualification'
            and qualified['probability_passed'] is True and qualified['comparison']['maximum_probability_change'] <= 1e-5
            and qualified['numerical_qualification']['basic_receipt'] == report['basic_receipt'],
            'u assembly probability/basic qualification differs')
    linked_path(qualified['donor'])
    for reference in qualified['members'].values():
        linked_path(reference)
    metadata = json.loads(Path(qualified['members']['metadata']['path']).read_text())
    arrays = _load_arrays(Path(qualified['members']['arrays']['path']), metadata['arrays'])
    _checked_numerical_qualification(qualified['numerical_qualification'], arrays['coefficients'], metadata['starts'][0]['iterations'])
    donor = read_execution_state(qualified['donor']['path'], qualified['frozen_selector']['purpose'])
    descriptor = json.loads((donor.path.parent / 'resolution/baseline.json').read_text())
    require(descriptor['selector'] == qualified['frozen_selector'], 'u assembly changed frozen selector')
    retained_paths = [f'heads/{head}.npz' for head in ('u', 'q', 'r', 'g')] + [f'resolution/{head}.npz' for head in ('q', 'r', 'g')]
    retained = [dict(path=name, sha256=identity(donor.path.parent / name)['sha256']) for name in retained_paths]
    costs = report['resources']
    require(costs['qualification_wall_seconds'] == qualified['wall_seconds'], 'u assembly qualification cost differs')
    read_finished = perf_counter()
    assembly_started = read_finished
    actual = dict(input_read_wall_seconds=costs['input_read_wall_seconds'] + read_finished-read_started,
                  design_wall_seconds=0., fit_wall_seconds=costs['fit_wall_seconds'],
                  qualification_wall_seconds=costs['qualification_wall_seconds'], assembly_wall_seconds=0.,
                  peak_memory_bytes=max(costs['peak_memory_bytes'], resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                                        * (1 if sys.platform == 'darwin' else 1024)))
    manifest = deepcopy(donor.manifest)
    manifest['implementation'] = implementation()
    manifest['u_repair'] = dict(kind='execution-u-outer-sum-repair-1', donor=qualified['donor'],
        inputs=report['inputs'], diagnosis=report['diagnosis'], repair=identity(repair_path),
        qualification=report['probability_qualification'], retained_members=retained,
        baseline_heads=descriptor['heads'],
        selector_sha256=hashlib.sha256(json.dumps(descriptor['selector'], sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        donor_resources=deepcopy(donor.manifest['resources']), retained_component_counts=dict(baselines=4, qrg_probes=3),
        performed_solve_counts=dict(u=0, q=0, r=0, g=0), performed_resolution_solve_counts=dict(u=1, q=0, r=0, g=0),
        full_objective_calls=costs['full_objective_calls'])
    manifest['resources'].update(actual, wall_scope='input_read+u_repair+probability_qualification+assembly_before_completion_manifest')
    manifest['resources']['resolution_solve_counts']['u'] = 1
    output = Path(output).resolve()
    output.mkdir()
    (output / 'heads').mkdir()
    heads = deepcopy(donor.heads)
    for head in ('u', 'q', 'r', 'g'):
        heads[head]['resolution'] = dict(status='pending')
        write_execution_head(output, heads[head], donor.arrays[head], manifest['season'],
                             retained_arrays=identity(donor.path.parent / f'heads/{head}.npz'))
    baseline = freeze_execution_baseline(output, manifest, heads, descriptor['selector'])
    for head in ('u', 'q', 'r', 'g'):
        if head == 'u':
            probe_metadata, probe_arrays, comparison = metadata, arrays, qualified['comparison']
            retained_arrays = None
        else:
            probe = read_execution_probe(donor, head)
            probe_metadata, probe_arrays, comparison = probe.heads[head], probe.arrays[head], probe.probe['comparison']
            retained_arrays = identity(donor.path.parent / f'resolution/{head}.npz')
        reference = write_execution_probe(output, baseline, probe_metadata, probe_arrays, comparison, retained_arrays=retained_arrays)
        heads[head]['resolution'] = dict(status='passed', baseline=baseline, probe=reference, comparison=comparison)
        (output / f'heads/{head}.json').unlink()
        write_json(output / f'heads/{head}.json', heads[head])
    manifest['resources']['assembly_wall_seconds'] = perf_counter()-assembly_started
    manifest['resources']['wall_seconds'] = sum(manifest['resources'][name] for name in
        ('input_read_wall_seconds', 'design_wall_seconds', 'fit_wall_seconds', 'qualification_wall_seconds', 'assembly_wall_seconds'))
    return write_execution_state(output, manifest, heads, donor.arrays, donor.coverage, _reserved=True)
