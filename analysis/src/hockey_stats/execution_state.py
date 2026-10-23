"""strict, detached annual execution state and numerical-probe members."""

from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import date
import hashlib
import json
import math
from pathlib import Path
from time import perf_counter
import re

import numpy as np

from .artifacts import digest, require, write_arrays, write_json
from .captures import InputContractError
from .chance_cli import identity, output_path, read_json

HEADS = ('u', 'q', 'r', 'g')
MANIFEST_KEYS = 'schema_version kind purpose season recipe implementation prepared coaches previous training_cutoff heads files resources'.split()
HEAD_KEYS = 'head target design actors priors centers ledger origin arrays starts selected_start diagnostics resolution status reasons'.split()


@dataclass(frozen=True)
class ExecutionState:
    path: Path
    manifest: dict
    heads: dict
    arrays: dict
    coverage: dict
    usage: str = 'annual'
    probe: dict | None = None


def _closed(value, keys, label):
    require(type(value) is dict and set(value) == set(keys), f'{label}: invalid fields')


def _finite(value, label):
    if isinstance(value, dict):
        require(all(type(key) is str for key in value), f'{label}: non-text key')
        for item in value.values():
            _finite(item, label)
    elif isinstance(value, list):
        for item in value:
            _finite(item, label)
    else:
        require(value is None or type(value) in (bool, int, float, str), f'{label}: invalid json value')
        require(type(value) is not float or math.isfinite(value), f'{label}: nonfinite value')


def _season(value):
    require(type(value) is str and re.fullmatch(r'20\d{2}20\d{2}', value)
            and int(value[4:]) == int(value[:4]) + 1, 'invalid execution season')
    return int(value[:4])


def _reference(value, label):
    require(type(value) is dict and {'path', 'sha256'} <= value.keys(), f'{label}: missing reference')
    require(type(value['path']) is str and Path(value['path']).is_absolute()
            and str(Path(value['path'])) == value['path'] and '..' not in Path(value['path']).parts, f'{label}: invalid absolute locator')
    digest(value['sha256'])
    _finite(value, label)


def _member(root, value):
    require(type(value) is str and bool(value), 'invalid member path')
    part = Path(value)
    require(not part.is_absolute() and part.as_posix() == value
            and all(p not in ('.', '..') for p in part.parts), 'noncanonical member path')
    path = (root / part).resolve(strict=True)
    require(root in path.parents and path.is_file(), 'member escapes artifact or is not a file')
    return path


def _manifest(value, purpose):
    _closed(value, MANIFEST_KEYS, 'manifest')
    require(type(value['schema_version']) is int and value['schema_version'] == 1
            and value['kind'] == 'execution-state', 'invalid execution state schema')
    require(purpose in ('real', 'fixture') and value['purpose'] == purpose, 'execution purpose mismatch')
    year = _season(value['season'])
    require(value['season'] in ('20212022','20222023','20232024','20242025','20252026'), 'season outside execution scope')
    recipe = value['recipe']
    require(type(recipe) is dict and recipe.get('name') == 'experimental-v1'
            and recipe.get('version') == 'execution-v1-05-1', 'invalid execution recipe')
    from .execution_design import RECIPE
    require(recipe == RECIPE, 'execution recipe definition differs')
    for name in ('prepared', 'coaches'):
        _reference(value[name], name)
        require(value[name].get('purpose') == purpose, f'{name}: purpose mismatch')
    _closed(value['prepared'], ('purpose', 'path', 'sha256', 'members'), 'prepared binding')
    _closed(value['coaches'], ('purpose', 'path', 'sha256', 'selected_game_ids'), 'coach binding')
    members = value['prepared']['members']
    require(type(members) is list, 'missing prepared member bindings')
    keys = []
    for member in members:
        _closed(member, ('kind', 'season', 'game_id', 'path', 'sha256'), 'prepared member')
        digest(member['sha256'])
        require(member['season'] == value['season'] and member['kind'] in ('game', 'people'), 'cross-season prepared member')
        keys.append((member['kind'], member['game_id']))
    require(len(keys) == len(set(keys)) and ('people', None) in keys, 'duplicate/missing prepared members')
    require(value['coaches']['selected_game_ids'] == [member['game_id'] for member in members if member['kind'] == 'game'], 'coach selected game identities differ')
    previous = value['previous']
    if previous is None:
        require(purpose != 'real' or year == 2021, 'real chain must begin at 20212022')
    else:
        _closed(previous, ('path', 'sha256', 'season', 'purpose', 'recipe_sha256', 'usage'), 'previous')
        _reference(previous, 'previous')
        require(previous.get('season') == f'{year-1}{year}'
                and previous.get('purpose') == purpose
                and previous.get('recipe_sha256') == recipe['sha256']
                and previous.get('usage') == 'annual', 'invalid predecessor identity')
    require(type(value['training_cutoff']) is str, 'invalid training cutoff')
    try:
        cutoff = date.fromisoformat(value['training_cutoff'])
    except ValueError as error:
        raise InputContractError('invalid training cutoff') from error
    require(year <= cutoff.year <= year+1, 'training cutoff is outside season')
    require(type(value['implementation']) is dict and bool(value['implementation']), 'missing implementation identity')
    costs = value['resources']
    _closed(costs, 'wall_seconds input_read_wall_seconds design_wall_seconds fit_wall_seconds wall_scope peak_memory_bytes dimensions solve_counts resolution_solve_counts origin_rows candidate_branches output_bytes'.split(), 'resources')
    for key in ('wall_seconds','input_read_wall_seconds','design_wall_seconds','fit_wall_seconds'):
        _nonnegative(costs[key], key)
    require(costs['wall_scope'] == 'initial_input_read+prepare_execution+fit_and_members_before_completion_manifest'
            and costs['wall_seconds'] == sum(costs[key] for key in ('input_read_wall_seconds','design_wall_seconds','fit_wall_seconds')), 'resource wall-time scope differs')
    require(type(costs['peak_memory_bytes']) is int and costs['peak_memory_bytes'] >= 0
            and type(costs['output_bytes']) is int and costs['output_bytes'] >= 0, 'invalid memory/output bytes')
    for key in ('dimensions','solve_counts','resolution_solve_counts','origin_rows','candidate_branches'):
        require(type(costs[key]) is dict and set(costs[key]) == set(HEADS), 'resource head axes differ')
        require(all(type(v) is int and v >= 0 or v is None and key in ('origin_rows','candidate_branches') for v in costs[key].values()), 'invalid resource count')
    _finite(value, 'manifest')


def _actor_key(row):
    require(type(row) is dict and type(row.get('block')) is str and bool(row['block'])
            and row['block'] in ('shooter','goalie','setter','attacking_coach','defending_coach')
            and type(row.get('id')) is str and bool(row['id']),
            'invalid actor identity')
    return row['block'], str(row['id'])


def _rows(rows, label):
    require(type(rows) is list, f'{label}: expected rows')
    keys = [_actor_key(row) for row in rows]
    require(len(set(keys)) == len(keys), f'{label}: duplicate actor')
    return dict(zip(keys, rows))


def _nonnegative(value, label):
    require(type(value) in (float, int) and math.isfinite(value) and value >= 0, f'invalid {label}')


def _actors(metadata, coefficients, season):
    size = metadata['design']['size'] if coefficients is None else len(coefficients)
    actors = _rows(metadata['actors'], 'actors')
    priors = _rows(metadata['priors'], 'priors')
    ledger = _rows(metadata['ledger'], 'ledger')
    require(set(priors) == set(actors), 'prior axes differ from actor axes')
    expected_axes = {(block, str(actor)): index for block, axis in metadata['design']['actor_indices'].items() for actor, index in axis.items()}
    require({key: row['index'] for key, row in actors.items()} == expected_axes, 'actor metadata omits or changes live coordinates')
    for key, row in actors.items():
        _closed(row, 'index block id role age source_support likelihood_support center_weight prior_only'.split(), 'actor')
        require(type(row['index']) is int and 0 <= row['index'] < size, 'actor coordinate outside axis')
        for name in ('source_support', 'likelihood_support', 'center_weight'):
            _nonnegative(row[name], name)
        require(row['source_support'] > 0 and type(row['prior_only']) is bool
                and row['prior_only'] == (row['likelihood_support'] == 0), 'actor support/prior-only status differs')
        require(row['role'] in ('F', 'D', 'G', None), 'invalid actor role')
        age = row['age']
        require(age is None or type(age) in (int, float) and math.isfinite(age) and age >= 0, 'invalid actor age')
        require(metadata['design']['actor_indices'].get(row['block'], {}).get(str(row['id'])) == row['index'], 'actor identity differs from design axis')
        prior = priors[key]
        _closed(prior, 'block id mean precision age_delta age_indices transition_reason prior_mean last_supported'.split(), 'prior')
        last = prior['last_supported']
        if last is not None:
            _closed(last, 'block id coefficient season role age'.split(), 'last-supported state')
            require(_actor_key(last) == key and _season(last['season']) < _season(season), 'invalid last-supported identity/date')
        mean = 0. if last is None else last['coefficient']
        require(prior['mean'] == mean and type(mean) in (int, float) and math.isfinite(mean), 'prior carried mean differs')
        entry, carry = ((16., 64.) if row['block'] == 'goalie' else
                        (256., 1024.) if row['block'].endswith('coach') else (4., 16.))
        require(prior['precision'] == (entry if last is None else carry), 'prior entry/carry precision differs')
        role = row['role']
        age_carry = last is not None and not row['block'].endswith('coach') and role in ('F', 'D', 'G') and last['role'] == role and age is not None and last['age'] is not None
        if age_carry:
            now, old = (age-27)/10, (last['age']-27)/10
            expected_delta = [now-old, now**2-old**2]
            expected_indices = metadata['design']['age_indices_by_block_role'][row['block']][role]
        else:
            expected_delta, expected_indices = [], []
        require(prior['age_delta'] == expected_delta and prior['age_indices'] == expected_indices, 'prior age transition differs')
        expected_reason = ('entry' if last is None else 'age_neutral' if row['block'].endswith('coach')
                           else 'missing_or_changed_role' if role not in ('F','D','G') or last['role'] != role
                           else 'missing_age' if age is None or last['age'] is None else 'age_carry')
        require(prior['transition_reason'] == expected_reason, 'prior transition reason differs')
        if coefficients is None:
            require(prior['prior_mean'] is None and ledger.get(key) == last, 'unavailable head changes incoming history')
            continue
        actual_mean = mean + float(np.dot(expected_delta, coefficients[expected_indices]))
        require(prior['prior_mean'] == actual_mean, 'recalculated prior mean differs')
        if row['prior_only']:
            require(coefficients[row['index']] == actual_mean and ledger.get(key) == last, 'prior-only actor changes estimate/history')
        else:
            require(ledger.get(key) == dict(block=row['block'], id=row['id'], coefficient=float(coefficients[row['index']]), season=season, role=role, age=age), 'supported actor ledger differs from raw estimate')
    indices = [row['index'] for row in actors.values()]
    require(len(set(indices)) == len(indices), 'multiply addressed actor coordinate')
    current_keys = {key for key,row in ledger.items() if row['season'] == season}
    expected_current = set() if coefficients is None else {key for key,row in actors.items() if row['likelihood_support'] > 0}
    require(current_keys == expected_current, 'current-season ledger invents or omits a supported observation')
    for key, row in ledger.items():
        require(row['block'] in metadata['design']['actor_indices'], 'ledger block is not applicable to this head')
        _closed(row, 'block id coefficient season role age'.split(), 'ledger')
        require(type(row['coefficient']) in (int, float) and math.isfinite(row['coefficient']), 'invalid ledger coefficient')
        require(_season(row['season']) <= _season(season), 'future ledger observation')
        require(row['role'] in ('F', 'D', 'G', None), 'invalid ledger role')
    setter_rows = sorted((row for row in actors.values() if row['block'] == 'setter' and row['center_weight'] > 0), key=lambda row:str(row['id']))
    total_setter_weight = sum(row['center_weight'] for row in setter_rows)
    expected_indices = [row['index'] for row in setter_rows]
    expected_weights = [row['center_weight']/total_setter_weight for row in setter_rows]
    require(metadata['design']['setter_mean_indices'] == expected_indices
            and np.allclose(metadata['design']['setter_mean_weights'],expected_weights,rtol=1e-12,atol=1e-14), 'setter mean differs from fixed pre-outcome center weights')
    for block, record in (metadata['centers'] or {}).items():
        _closed(record, ('value', 'weight', 'prior_only'), 'actor center')
        selected = [row for row in actors.values() if row['block'] == block]
        weight = sum(row['center_weight'] for row in selected)
        center = sum(row['center_weight'] * coefficients[row['index']] for row in selected) / weight if weight else 0.
        require(record == dict(value=center, weight=weight, prior_only=not bool(weight)), 'actor center differs from fixed training weights')
    if coefficients is not None and metadata['head'] == 'g':
        mean = float(np.dot(coefficients[expected_indices], metadata['design']['setter_mean_weights']))
        require(abs(mean - metadata['centers']['setter']['value']) <= 1e-12, 'unknown setter mean has a nonzero centered residual')
    return actors


def _design(metadata, arrays):
    from .chance import TYPES
    from .execution_design import DEFINITION, FAMILIES
    from .shot_origins import grid

    design = metadata['design']
    _closed(design, 'size coefficient_names columns means active conditions availability_conditions feature_support map_indices native_neighbors mirror_cells circumstance_indices actor_indices actor_role_reasons age_indices_by_block_role setup_index families trait_assumptions fixed_transforms penalties setter_mean_indices setter_mean_weights'.split(), 'head design')
    coefficients = arrays.get('coefficients')
    require(coefficients is not None and coefficients.ndim == 1, 'missing coefficient vector')
    size = coefficients.size
    names = design['coefficient_names']
    require(type(design['size']) is int and design['size'] == size and type(names) is list
            and len(names) == size and len(set(names)) == size
            and all(type(name) is str and bool(name) for name in names), 'invalid coefficient axis')
    cells, edges = grid()
    by_point = {tuple(cell): i for i, cell in enumerate(cells)}
    representatives = [min(i, by_point[x, -y]) for i, (x, y) in enumerate(cells)]
    orbits = {point: i for i, point in enumerate(sorted(set(representatives)))}
    mirror = [orbits[point] for point in representatives]
    require(design['mirror_cells'] == mirror and design['native_neighbors'] == edges.tolist(), 'native geometry identity differs')
    expected_names = ['intercept']
    expected_maps = []
    for name in ['base'] + ['type:' + value for value in TYPES[1:]]:
        offset = len(expected_names)
        expected_maps.append([offset + i for i in mirror])
        expected_names.extend(name + ':orbit:' + str(i) for i in range(len(orbits)))
    require(design['map_indices'] == expected_maps, 'native map coordinate identity differs')
    columns = design['columns']
    require(type(columns) is list and all(type(name) is str for name in columns)
            and len(set(columns)) == len(columns), 'invalid circumstance names')
    start = len(expected_names)
    require(design['circumstance_indices'] == list(range(start, start+len(columns))), 'circumstance coordinate identity differs')
    expected_names.extend('circumstance:' + name for name in columns)
    for key in ('means', 'active'):
        require(type(design[key]) is list and len(design[key]) == len(columns), 'circumstance dimensions differ')
    require(all(type(v) in (float, int) and math.isfinite(v) for v in design['means'])
            and all(type(v) is bool for v in design['active']), 'invalid circumstance means/flags')
    require(set(design['conditions']) == set(columns) and set(design['feature_support']) == set(columns), 'feature support axes differ')
    expected_conditions = {}
    for name in columns:
        condition = design['conditions'][name]
        if not condition.startswith('flag:'):
            expected_conditions.setdefault(condition,[]).append(name)
    require(design['availability_conditions'] == expected_conditions, 'availability condition registry differs')
    require(all('unavailable:' + condition in columns
                and design['conditions']['unavailable:' + condition] == 'flag:' + condition for condition in expected_conditions), 'availability conditions do not own one explicit flag')
    blocks = ['shooter'] + ([] if metadata['head'] == 'u' else ['goalie']) + (['setter'] if metadata['head'] == 'g' else []) + ['attacking_coach', 'defending_coach']
    require(list(design['actor_indices']) == blocks, 'actor blocks differ from head applicability')
    require(type(design['actor_role_reasons']) is dict and set(design['actor_role_reasons']) == set(blocks), 'missing actor role provenance')
    for block in blocks:
        require(set(design['actor_role_reasons'][block]) == set(design['actor_indices'][block])
                and all(type(reason) is str and bool(reason) for reason in design['actor_role_reasons'][block].values()), 'actor role provenance axes differ')
    for block in blocks:
        axis = design['actor_indices'][block]
        require(type(axis) is dict and list(axis) == sorted(axis), 'actor axis is not canonical')
        for actor, index in axis.items():
            require(index == len(expected_names), 'actor coordinate identity differs')
            expected_names.append(block + ':' + actor)
    if metadata['head'] == 'g':
        require(design['setup_index'] == len(expected_names), 'setup coordinate differs')
        expected_names.append('setup')
    else:
        require(design['setup_index'] is None, 'setup in non-setting head')
    expected_age = {}
    for block in blocks:
        if block.endswith('coach'):
            continue
        expected_age[block] = {}
        for role in ('F', 'D', 'G'):
            expected_age[block][role] = [len(expected_names), len(expected_names)+1]
            expected_names.extend([f'age:{block}:{role}:linear', f'age:{block}:{role}:quadratic'])
    require(design['age_indices_by_block_role'] == expected_age and names == expected_names, 'coefficient ownership differs')
    require(design['fixed_transforms'] == DEFINITION['fixed_transforms'], 'fixed feature transforms differ')
    for name, support in design['feature_support'].items():
        _closed(support, ('available_weight','unavailable_attempts','structural_absence_attempts','active'), 'feature support')
        _nonnegative(support['available_weight'], 'feature available weight')
        require(all(type(support[key]) is int and support[key] >= 0 for key in ('unavailable_attempts','structural_absence_attempts'))
                and type(support['active']) is bool and support['active'] == design['active'][columns.index(name)]
                and type(design['conditions'][name]) is str, 'invalid feature support/condition')
    require(design['penalties'] == DEFINITION['penalties']
            and design['families'] == list(FAMILIES) + ([] if metadata['head'] == 'u' else ['goalie_workload', 'goalie_calendar_rest'])
            and design['trait_assumptions'] == ['reported_hand_stable_trait'], 'design recipe differs')
    indices, weights = design['setter_mean_indices'], design['setter_mean_weights']
    require(type(indices) is list and type(weights) is list and len(indices) == len(weights)
            and len(set(indices)) == len(indices) and set(indices) <= set(design['actor_indices'].get('setter', {}).values())
            and all(type(w) in (int, float) and math.isfinite(w) and w > 0 for w in weights)
            and (not weights or abs(sum(weights)-1.) <= 1e-12), 'invalid setter mean axis')
    return size


def _solve_record(row, head, tightened=False):
    required = {'converged','termination','iterations','evaluations','objective','gradient_max','inner_solves','objective_trace','em_iterations','responsibility_change'}
    if head == 'g':
        required.update(('objective_increases','relative_objective_change'))
    else:
        required.add('status')
    require(type(row) is dict and required <= row.keys(), 'incomplete optimizer diagnostics')
    require(type(row['converged']) is bool and type(row['termination']) is str and bool(row['termination'])
            and all(type(row[key]) is int and row[key] >= 0 for key in ('iterations','evaluations','em_iterations')), 'invalid optimizer termination/counts')
    require(type(row['inner_solves']) is list and type(row['objective_trace']) is list, 'invalid optimizer traces')
    if row['converged']:
        require(type(row['objective']) in (int,float) and math.isfinite(row['objective'])
                and type(row['gradient_max']) in (int,float) and row['gradient_max'] >= 0
                and bool(row['objective_trace']) and row['objective_trace'][-1] == row['objective'], 'invalid completed objective/gradient trace')
        if head == 'g':
            scale = .1 if tightened else 1.
            require(row['em_iterations'] == len(row['inner_solves']) > 0
                    and len(row['objective_trace']) == row['em_iterations'] + 1
                    and type(row['responsibility_change']) in (int,float) and 0 <= row['responsibility_change'] <= 1e-6 * scale
                    and type(row['relative_objective_change']) in (int,float) and 0 <= row['relative_objective_change'] <= 1e-8 * scale,
                    'false setter em completion')
            require(all(inner.get('converged') is True and {'status','termination','iterations','evaluations','objective'} <= inner.keys() for inner in row['inner_solves']), 'unfinished setter m-step')
            require(all(new-old <= 1e-10*(1+abs(old)) for old,new in zip(row['objective_trace'],row['objective_trace'][1:])), 'setter observed objective increased')
        else:
            require(row['status'] == 0 and row['em_iterations'] == 0 and not row['inner_solves']
                    and row['responsibility_change'] is None, 'invalid binary optimizer completion')


def _in_sample(value):
    _closed(value, 'attempts positive class_fraction mean_predicted_probability mean_imputation_weighted_negative_log_likelihood mean_outcome_only_negative_log_likelihood reliability origin_mass_error expanded_rows candidate_branches base_matrix_nonzeros batches'.split(), 'in-sample diagnostics')
    for key in ('attempts','positive','expanded_rows','candidate_branches','base_matrix_nonzeros','batches'):
        require(type(value[key]) is int and value[key] >= 0, 'invalid in-sample count')
    require(0 < value['positive'] < value['attempts'] and value['class_fraction'] == value['positive']/value['attempts'], 'in-sample class fraction differs')
    require(type(value['reliability']) is list and len(value['reliability']) == 20, 'reliability bins differ')
    for index, row in enumerate(value['reliability']):
        _closed(row, ('lower','upper','count','observed_positive','predicted_mass'), 'reliability bin')
        require(row['lower'] == index/20 and row['upper'] == (index+1)/20
                and type(row['count']) is int and type(row['observed_positive']) is int
                and 0 <= row['observed_positive'] <= row['count']
                and row['lower']*row['count']-1e-10 <= row['predicted_mass'] <= row['upper']*row['count']+1e-10, 'invalid reliability bin')
    require(sum(row['count'] for row in value['reliability']) == value['attempts']
            and sum(row['observed_positive'] for row in value['reliability']) == value['positive']
            and math.isclose(sum(row['predicted_mass'] for row in value['reliability'])/value['attempts'],value['mean_predicted_probability'],rel_tol=1e-12,abs_tol=1e-12), 'reliability physical-attempt accounting differs')
    for key in ('mean_imputation_weighted_negative_log_likelihood','mean_outcome_only_negative_log_likelihood','origin_mass_error'):
        _nonnegative(value[key], key)


def _head(metadata, head, arrays, season):
    _closed(metadata, HEAD_KEYS, f'head {head}')
    require(metadata['head'] == head and metadata['status'] in ('complete', 'unavailable'), 'cross-wired head')
    require(type(metadata['reasons']) is list and all(type(x) is str for x in metadata['reasons']), 'invalid head reasons')
    from .execution_design import TARGETS
    require(metadata['target'] == TARGETS[head], 'head target definition differs')
    require(metadata['origin'] == dict(cells=656, distance_ft=20., direction_strength=4., law='uniform-release-forward-kernel'), 'head origin law differs')
    require(type(metadata['diagnostics']) is dict and type(metadata['starts']) is list, 'missing solve diagnostics')
    resolution = metadata['resolution']
    require(type(resolution) is dict, 'missing resolution record')
    statuses = ('pending', 'passed', 'failed') if season == '20252026' else ('not_applicable',)
    require(resolution.get('status') in statuses, 'resolution status differs from season')
    if metadata['status'] == 'unavailable':
        require(not arrays and metadata['arrays'] is None and metadata['selected_start'] is None
                and metadata['centers'] is None and bool(metadata['reasons']), 'unavailable head carries fitted state')
        actors = _rows(metadata['actors'], 'actors')
        priors = _rows(metadata['priors'], 'priors')
        ledger = _rows(metadata['ledger'], 'ledger')
        require(set(actors) == set(priors), 'unavailable head prior axes differ')
        _design(metadata, {'coefficients': np.zeros(metadata['design']['size'], dtype=np.float64)})
        for key, prior in priors.items():
            require(prior.get('last_supported') == ledger.get(key), 'unavailable head changes prior history')
        require(all(_season(row['season']) < _season(season) for row in ledger.values()), 'unavailable head invents current estimate')
        _actors(metadata, None, season)
    else:
        require(not metadata['reasons'] and type(metadata['centers']) is dict
                and set(metadata['centers']) == {'shooter','goalie','setter','attacking_coach','defending_coach'}, 'completed head has unavailable state')
        require(set(arrays) == {'coefficients'}, 'unexpected fitted array')
        size = _design(metadata, arrays)
        _actors(metadata, arrays['coefficients'], season)
        selected = metadata['selected_start']
        require(type(selected) in (int, str), 'completed head has no selected start')
        complete = [row for row in metadata['starts'] if type(row) is dict and row.get('converged') is True]
        require(bool(complete), 'completed head has no completed optimizer')
        requested = metadata['diagnostics'].get('requested_starts')
        require(requested in (['zero','prior_mean'], ['continuation'])
                and [row.get('name') for row in metadata['starts']] == requested, 'requested/deduplicated start identities differ')
        for row in metadata['starts']:
            if row.get('deduplicated_to') is None:
                _solve_record(row, head, requested == ['continuation'])
            else:
                _closed(row, ('name','deduplicated_to'), 'deduplicated start')
                require(row['name'] == 'prior_mean' and row['deduplicated_to'] == 'zero', 'invalid start deduplication')
        chosen = [row for row in complete if row.get('name', row.get('label', row.get('index'))) == selected]
        require(len(chosen) == 1, 'selected start is not complete')
        objectives = [row.get('objective') for row in complete]
        require(all(type(x) in (int, float) and math.isfinite(x) for x in objectives), 'invalid completed objective')
        require(chosen[0]['objective'] == min(objectives), 'selected start is not objective minimum')
        require(selected == next(row['name'] for row in complete if row['objective'] == min(objectives)), 'selected start violates deterministic tie break')
        diagnostics = metadata['diagnostics']
        require({key: value for key,value in diagnostics.items() if key not in ('in_sample','requested_starts','wall_seconds')}
                == {key: value for key,value in chosen[0].items() if key not in ('name','deduplicated_to')}, 'selected diagnostics differ from completed start')
        _nonnegative(diagnostics.get('wall_seconds'), 'head wall time')
        _in_sample(diagnostics.get('in_sample'))
        from .execution_fit import penalty
        design = metadata['design']
        numerical_design = dict(map_indices=design['map_indices'], native_neighbors=design['native_neighbors'],
                                circumstance_indices=design['circumstance_indices'] + ([] if design['setup_index'] is None else [design['setup_index']]),
                                age_indices=[i for roles in design['age_indices_by_block_role'].values() for pair in roles.values() for i in pair])
        prior_by_key = {_actor_key(row): row for row in metadata['priors']}
        actor_terms = [dict(row, **{key:value for key,value in prior_by_key[_actor_key(row)].items() if key not in ('block','id')}) for row in metadata['actors']]
        penalty_value, _ = penalty(arrays['coefficients'], numerical_design, actor_terms)
        sample = diagnostics['in_sample']
        expected_objective = sample['attempts'] * sample['mean_imputation_weighted_negative_log_likelihood'] + penalty_value
        require(math.isclose(diagnostics['objective'], expected_objective, rel_tol=1e-8, abs_tol=1e-8), 'objective differs from likelihood and declared penalty')
    _finite(metadata, f'head {head}')


def _coverage(value, manifest, heads):
    _closed(value, ('purpose','season','games','attempts','heads','optional_features'), 'coverage')
    require(value['purpose'] == manifest['purpose'] and value['season'] == manifest['season'], 'coverage identity differs')
    require(type(value['games']) is list and type(value['attempts']) is list and set(value['heads']) == set(HEADS)
            and set(value['optional_features']) == set(HEADS), 'coverage axes differ')
    selected = [row for row in manifest['prepared']['members'] if row['kind'] == 'game']
    require([row['game_id'] for row in value['games']] == [row['game_id'] for row in selected], 'coverage omits selected games')
    attempts = value['attempts']
    require(len({row['key'] for row in attempts}) == len(attempts), 'duplicate physical attempt key')
    for game, member in zip(value['games'], selected, strict=True):
        _closed(game, ('game_id','game_date','status','recognized_attempts','prepared_member'), 'game coverage')
        require(game['prepared_member'] == member, 'coverage prepared-member identity differs')
        rows = [row for row in attempts if row['game_id'] == game['game_id']]
        require(game['recognized_attempts'] == len(rows), 'recognized attempt count differs')
        require([row['pointer'] for row in rows] == [f'/attempts/{i}' for i in range(len(rows))], 'located attempt partition differs')
    counts = {head: dict(included=0, excluded=0, **{'class:0':0, 'class:1':0}) for head in HEADS}
    selected_ids = {row['game_id'] for row in selected}
    for row in attempts:
        _closed(row, ('key','game_id','source_index','pointer','outcome','full_probability_context','goalie_identity','heads','source_supported','candidate_universe_complete','setter_discrepancy','immediate_stop_known'), 'attempt coverage')
        require(row['game_id'] in selected_ids and type(row['source_index']) is int and row['source_index'] >= 0
                and row['key'] == row['game_id'] + ':' + str(row['source_index']), 'attempt source key differs')
        require(set(row['heads']) == set(HEADS) and type(row['source_supported']) is bool
                and type(row['immediate_stop_known']) is bool
                and row['candidate_universe_complete'] in (None, True, False)
                and row['outcome'] in ('block','miss','save','goal',None), 'invalid attempt support')
        goalie = row['goalie_identity']
        _closed(goalie, ('status','player_id','membership_id','dated_team_id','reported_position','reason','pointers'), 'goalie identity')
        require(goalie['status'] in ('identified','unavailable','conflict')
                and all(item is None or type(item) is int and item > 0 for item in (goalie['player_id'],goalie['membership_id'],goalie['dated_team_id']))
                and (goalie['reported_position'] is None or type(goalie['reported_position']) is str)
                and type(goalie['pointers']) is list and bool(goalie['pointers'])
                and all(type(pointer) is str and pointer.startswith('/') for pointer in goalie['pointers']), 'invalid goalie identity facts')
        if goalie['status'] == 'identified':
            require(goalie['player_id'] is not None and goalie['player_id'] == goalie['membership_id']
                    and goalie['dated_team_id'] is not None and goalie['reason'] is None, 'unsupported individual goalie identity')
        else:
            require(goalie['player_id'] is None and type(goalie['reason']) is str and bool(goalie['reason']), 'unavailable goalie has a fitted identity')
        require(type(row['full_probability_context']) is bool
                and row['full_probability_context'] == (row['source_supported'] and goalie['status'] == 'identified'), 'full probability context differs from actor support')
        require(row['full_probability_context'] or not any(row['heads'][head]['included'] for head in ('q','r','g')), 'head includes unavailable individual goalie')
        for head in HEADS:
            record = row['heads'][head]
            _closed(record, ('included','target','reasons'), 'head disposition')
            require(type(record['included']) is bool and type(record['reasons']) is list, 'invalid head disposition')
            if record['included']:
                require(type(record['target']) in (int,float) and record['target'] in (0.,1.)
                        and not record['reasons'] and row['source_supported'], 'included attempt has invalid target/support')
                expected_target = (float(row['outcome'] != 'block') if head == 'u' else float(row['outcome'] in ('save','goal')) if head == 'q' else float(row['outcome'] == 'goal') if head == 'g' else 1. if row['outcome'] == 'goal' else record['target'])
                require(record['target'] == expected_target, 'head target contradicts recorded outcome')
                counts[head]['included'] += 1
                counts[head]['class:' + str(int(record['target']))] += 1
            else:
                require(record['target'] is None and bool(record['reasons']), 'excluded attempt has no located reason')
                counts[head]['excluded'] += 1
        for dependent, prior in (('q','u'),('r','q'),('g','r')):
            require(not row['heads'][dependent]['included'] or row['heads'][prior]['target'] == 1., 'head conditioning hierarchy differs')
    for head in HEADS:
        for key, count in counts[head].items():
            require(value['heads'][head].get(key,0) == count, 'coverage class/conditioning count differs')
        require(value['optional_features'][head] == heads[head]['design']['feature_support'], 'coverage feature support differs')
        if heads[head]['status'] == 'complete':
            require(counts[head]['class:0'] > 0 and counts[head]['class:1'] > 0, 'empty/single-class head claims completion')
            sample = heads[head]['diagnostics']['in_sample']
            require(sample['attempts'] == counts[head]['included'] and sample['positive'] == counts[head]['class:1'], 'in-sample diagnostics differ from coverage')
    _finite(value, 'coverage')


def _array_contract(arrays):
    return {name: {'shape': list(value.shape), 'dtype': 'float64', 'axes': ['coefficient']}
            for name, value in arrays.items()}


def _load_arrays(path, contract):
    require(type(contract) is dict and set(contract) == {'coefficients'}, 'invalid array contract')
    try:
        with np.load(path, allow_pickle=False) as saved:
            require(saved.files == list(contract), 'array names/order differ')
            arrays = {name: saved[name] for name in saved.files}
    except (ValueError, TypeError, KeyError) as error:
        raise InputContractError('invalid fitted arrays') from error
    require(all(value.dtype == np.dtype('float64') and np.isfinite(value).all() for value in arrays.values()), 'nonfinite or non-float64 fitted arrays')
    require(contract == _array_contract(arrays), 'array shape/dtype/axes differ')
    return arrays


def write_execution_head(output, metadata, arrays, season):
    """preserve a finished head before the next solve; no manifest yet."""
    head = metadata['head']
    metadata['arrays'] = _array_contract(arrays) if arrays else None
    _head(metadata, head, arrays, season)
    if arrays:
        write_arrays(Path(output), f'heads/{head}.npz', arrays)
    write_json(Path(output) / f'heads/{head}.json', metadata)


def _metadata_digest(metadata):
    body = {key: value for key, value in metadata.items() if key != 'resolution'}
    return hashlib.sha256(json.dumps(body, allow_nan=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _selector(value, manifest, heads, coverage):
    from .chance import TYPES
    _closed(value, ('policy','purpose','requirements','keys','population','fixture_witnesses','synthetic_geometry'), 'probe selector')
    require(value['policy'] == 'strength,type,outcome,missing,tip,off-ice,incomplete,sparse; first (game_id,integer_source_index); numeric source-key fill; maximum256 actual'
            and value['purpose'] == manifest['purpose'], 'probe selection policy differs')
    keys = value['keys']
    supported = {row['key'] for row in coverage['attempts'] if row['full_probability_context']}
    require(type(keys) is list and 0 < len(keys) <= 256 and len(set(keys)) == len(keys)
            and set(keys) <= supported
            and keys == sorted(keys,key=lambda key:(key.split(':')[0],int(key.split(':')[1]))), 'invalid frozen actual probe keys')
    population = value['population']
    _closed(population, ('eligible_contexts','withheld_contexts'), 'probe population')
    require(population['eligible_contexts'] == len(supported) and type(population['withheld_contexts']) is list, 'probe population count differs')
    withheld = [row for row in coverage['attempts'] if row['source_supported'] and not row['full_probability_context']]
    require([row['key'] for row in population['withheld_contexts']] == sorted((row['key'] for row in withheld), key=lambda key:(key.split(':')[0],int(key.split(':')[1]))), 'withheld probability contexts differ')
    withheld_strengths = {}
    for row in population['withheld_contexts']:
        _closed(row, ('key','reason','strength'), 'withheld probability context')
        require(row['reason'] == 'individual_goalie_identity_unavailable' and type(row['strength']) is list and len(row['strength']) == 3
                and row['strength'][0] in (3,4,5,6) and row['strength'][1] in (3,4,5,6) and row['strength'][2] in (0,1), 'invalid withheld probability context')
        name = 'strength:' + ','.join(map(str,row['strength']))
        withheld_strengths[name] = withheld_strengths.get(name,0)+1
    geometry = value['synthetic_geometry']
    _closed(geometry, ('context_key','types','cells','execution'), 'synthetic geometry probes')
    require(geometry == dict(context_key=keys[0], types=list(TYPES), cells=list(range(656)), execution=['actual','neutral']), 'synthetic geometry coverage differs')
    fixtures = value['fixture_witnesses']
    require(type(fixtures) is list, 'missing attributed fixture witnesses')
    fixture_keys = set()
    for record in fixtures:
        _closed(record, ('key','attribution'), 'fixture witness')
        require(type(record['key']) is str and record['key'].startswith('synthetic-resolution:')
                and record['key'] not in fixture_keys, 'invalid synthetic fixture key')
        fixture_keys.add(record['key'])
        attribution = record['attribution']
        require(type(attribution) is dict and attribution.get('kind') == 'synthetic'
                and attribution.get('source_key') in supported
                and type(attribution.get('reason')) is str and bool(attribution['reason'])
                and type(attribution.get('changed_fields')) is list and bool(attribution['changed_fields'])
                and type(attribution.get('actor')) is dict, 'unattributed synthetic fixture')
    requirements = value['requirements']
    require(type(requirements) is list and bool(requirements), 'missing numerical requirements')
    names = []
    for row in requirements:
        _closed(row, ('requirement','key','disposition'), 'probe requirement')
        require(type(row['requirement']) is str and bool(row['requirement']), 'invalid probe requirement name')
        names.append(row['requirement'])
        require(row['disposition'] in ('actual','fixture','unavailable'), 'invalid probe requirement disposition')
        expected = keys if row['disposition'] == 'actual' else fixture_keys if row['disposition'] == 'fixture' else (None,)
        require(row['key'] in expected, 'probe requirement has no checked witness')
    expected_names = {'type:' + name for name in TYPES} | {'outcome:' + name for name in ('block','miss','save','goal')} | {'missing_context','tip','off_ice_setter','incomplete_setter'}
    expected_names.update(key for key,count in coverage['heads']['u'].items() if key.startswith('strength:') and count > withheld_strengths.get(key,0))
    for head in HEADS:
        for block in ('shooter','goalie','setter','attacking_coach','defending_coach'):
            actors = [row for row in heads[head]['actors'] if row['block'] == block]
            if actors:
                actor = min(actors,key=lambda row:(row['likelihood_support'],str(row['id'])))
                expected_names.add('sparse:' + head + ':' + block + ':' + str(actor['id']))
    require(len(set(names)) == len(names) and set(names) == expected_names, 'frozen probe requirements omit or duplicate required cases')
    _finite(value, 'probe selector')


def _baseline_descriptor(manifest, heads, root):
    return dict(schema_version=1, kind='execution-baseline',
                identity={key: value for key, value in manifest.items() if key not in ('heads', 'files', 'resources')},
                heads=[dict(head=head, metadata_sha256=_metadata_digest(heads[head]),
                            arrays_sha256=identity(root / f'heads/{head}.npz')['sha256']) for head in HEADS])


def freeze_execution_baseline(output, manifest, heads, selector):
    """freeze the acyclic baseline derivation identity before tighter solves."""
    output = Path(output)
    require(all(heads[head]['status'] == 'complete' for head in HEADS), 'resolution requires a complete baseline family')
    (output / 'resolution').mkdir()
    descriptor = _baseline_descriptor(manifest, heads, output)
    descriptor['selector'] = selector
    write_json(output / 'resolution/baseline.json', descriptor)
    return dict(path='resolution/baseline.json', sha256=identity(output / 'resolution/baseline.json')['sha256'])


def write_execution_probe(output, baseline, metadata, arrays, comparison):
    """write one tightened state without promoting its coefficients."""
    output = Path(output)
    head = metadata['head']
    metadata = deepcopy(metadata)
    metadata['arrays'] = _array_contract(arrays)
    array_path = f'resolution/{head}.npz'
    write_arrays(output, array_path, arrays)
    document = dict(usage='numerical_probe', head=head, baseline=baseline,
                    metadata=metadata, arrays=dict(path=array_path, sha256=identity(output / array_path)['sha256']),
                    comparison=comparison)
    path = f'resolution/{head}.json'
    write_json(output / path, document)
    return dict(path=path, sha256=identity(output / path)['sha256'])


def write_execution_state(output, manifest, heads, arrays, coverage, *, probes=None, _reserved=False):
    """write checked members first and the completion manifest last."""
    began = perf_counter()
    require(probes is None, 'probes are written explicitly before the annual manifest')
    manifest, heads, coverage = deepcopy(manifest), deepcopy(heads), deepcopy(coverage)
    require(set(heads) == set(HEADS) and set(arrays) <= set(HEADS), 'invalid annual head axes')
    manifest['heads'] = []
    manifest['files'] = []
    _manifest(manifest, manifest.get('purpose'))
    for head in HEADS:
        values = arrays.get(head, {})
        require(all(type(value) is np.ndarray and value.dtype == np.dtype('float64')
                    and np.isfinite(value).all() for value in values.values()), 'arrays must be finite float64')
        heads[head]['arrays'] = _array_contract(values) if values else None
        _head(heads[head], head, values, manifest['season'])
    _coverage(coverage, manifest, heads)
    if _reserved:
        output = Path(output).resolve(strict=True)
        require(not (output / 'manifest.json').exists(), 'completion manifest already exists')
    else:
        output = output_path(str(output), [])
        output.mkdir()
        (output / 'heads').mkdir()
    write_json(output / 'coverage.json', coverage)
    paths = ['coverage.json']
    for head in HEADS:
        metadata_path = f'heads/{head}.json'
        arrays_path = f'heads/{head}.npz' if heads[head]['status'] == 'complete' else None
        if arrays_path is not None:
            if not _reserved:
                write_arrays(output, arrays_path, arrays[head])
            paths.append(arrays_path)
        if _reserved:
            require(read_json(output / metadata_path) == heads[head], 'saved head differs before completion')
        else:
            write_json(output / metadata_path, heads[head])
        paths.append(metadata_path)
        manifest['heads'].append(dict(head=head, status=heads[head]['status'], metadata_path=metadata_path, arrays_path=arrays_path))
    if (output / 'resolution/baseline.json').exists():
        paths.append('resolution/baseline.json')
        for head in HEADS:
            reference = heads[head]['resolution'].get('probe')
            if reference is not None:
                paths.extend((reference['path'], f'resolution/{head}.npz'))
    manifest['files'] = [dict(path=path, sha256=identity(output/path)['sha256']) for path in paths]
    manifest['resources']['output_bytes'] = sum((output / path).stat().st_size for path in paths)
    manifest['resources']['fit_wall_seconds'] += perf_counter() - began
    manifest['resources']['wall_seconds'] = sum(manifest['resources'][key] for key in ('input_read_wall_seconds','design_wall_seconds','fit_wall_seconds'))
    write_json(output / 'manifest.json', manifest)
    state = read_execution_state(output, manifest['purpose'])
    require(all(np.array_equal(state.arrays[head][name], value) for head, values in arrays.items() for name, value in values.items()), 'save/read changed fitted coefficients')
    return state


def _read_execution_state(path, expected_purpose):
    """read only saved members; input references never cause source reads."""
    path = Path(path).resolve(strict=True)
    if path.is_dir():
        path = path / 'manifest.json'
    require(path.name == 'manifest.json', 'execution completion locator must be manifest.json')
    root = path.parent
    manifest = read_json(path)
    _manifest(manifest, expected_purpose)
    require(type(manifest['files']) is list, 'missing member identities')
    files = {}
    for reference in manifest['files']:
        _closed(reference, ('path', 'sha256'), 'member reference')
        digest(reference['sha256'])
        require(reference['path'] not in files, 'duplicate member identity')
        member = _member(root, reference['path'])
        require(identity(member)['sha256'] == reference['sha256'], 'execution member hash differs')
        files[reference['path']] = member
    require(type(manifest['heads']) is list and [row.get('head') for row in manifest['heads']] == list(HEADS), 'invalid ordered heads')
    heads, arrays, addressed = {}, {}, ['coverage.json']
    for row in manifest['heads']:
        _closed(row, ('head', 'status', 'metadata_path', 'arrays_path'), 'head reference')
        head = row['head']
        require(row['metadata_path'] == f'heads/{head}.json', 'cross-wired metadata member')
        require(row['metadata_path'] in files, 'missing metadata identity')
        addressed.append(row['metadata_path'])
        metadata = read_json(files[row['metadata_path']])
        require(metadata.get('status') == row['status'], 'head status differs')
        values = {}
        if row['status'] == 'complete':
            require(row['arrays_path'] == f'heads/{head}.npz' and row['arrays_path'] in files, 'cross-wired coefficient member')
            addressed.append(row['arrays_path'])
            values = _load_arrays(files[row['arrays_path']], metadata.get('arrays'))
            arrays[head] = values
        else:
            require(row['arrays_path'] is None, 'unavailable head addresses coefficients')
        _head(metadata, head, values, manifest['season'])
        heads[head] = metadata
    if 'resolution/baseline.json' in files:
        descriptor = read_json(files['resolution/baseline.json'])
        expected = _baseline_descriptor(manifest, heads, root)
        require({key: value for key, value in descriptor.items() if key != 'selector'} == expected, 'baseline descriptor differs from annual family')
        _selector(descriptor.get('selector'), manifest, heads, read_json(files['coverage.json']))
        addressed.append('resolution/baseline.json')
        for head in HEADS:
            reference = heads[head]['resolution'].get('probe')
            if reference is not None:
                require(reference == dict(path=f'resolution/{head}.json', sha256=identity(files[f'resolution/{head}.json'])['sha256']), 'resolution probe binding differs')
                addressed.extend((reference['path'], f'resolution/{head}.npz'))
    else:
        require(all(heads[head]['resolution']['status'] not in ('passed', 'failed') for head in HEADS), 'resolution has no frozen baseline')
    require(len(addressed) == len(set(addressed)) and set(addressed) == set(files), 'orphan or multiply addressed member')
    actual = {str(member.relative_to(root)) for member in root.rglob('*') if member.is_file() and member != path}
    require(actual == set(files), 'unbound artifact members')
    coverage = read_json(files['coverage.json'])
    _coverage(coverage, manifest, heads)
    if manifest['previous'] is None:
        for head in HEADS:
            require(all(row['last_supported'] is None for row in heads[head]['priors'])
                    and all(row['season'] == manifest['season'] for row in heads[head]['ledger']), 'first annual state invents pre-chain history')
    costs = manifest['resources']
    require(costs['output_bytes'] == sum(member.stat().st_size for member in files.values()), 'saved output byte count differs')
    for head in HEADS:
        require(costs['dimensions'][head] == heads[head]['design']['size'], 'resource dimension differs')
        solve_count = sum((len(row.get('inner_solves',[])) if head == 'g' else 1) for row in heads[head]['starts'] if row.get('deduplicated_to') is None)
        require(costs['solve_counts'][head] == solve_count, 'actual solve count differs')
        sample = heads[head]['diagnostics'].get('in_sample',{})
        require(costs['origin_rows'][head] == sample.get('expanded_rows') and costs['candidate_branches'][head] == sample.get('candidate_branches'), 'resource branch/origin counts differ')
    state = ExecutionState(path, manifest, heads, arrays, coverage)
    for head in HEADS:
        if heads[head]['resolution'].get('probe') is not None:
            probe_state = read_execution_probe(state, head)
            solves = sum((len(row.get('inner_solves',[])) if head == 'g' else 1) for row in probe_state.heads[head]['starts'] if row.get('deduplicated_to') is None)
            require(costs['resolution_solve_counts'][head] == solves, 'resolution solve count differs')
        else:
            require(heads[head]['resolution']['status'] != 'passed', 'passed resolution has no probe')
            require(costs['resolution_solve_counts'][head] == 0 or heads[head]['resolution']['status'] == 'failed', 'unbound resolution solve count')
    return state


def read_execution_state(path, expected_purpose):
    """normalize malformed records into an explicit input-contract failure."""
    try:
        return _read_execution_state(path, expected_purpose)
    except (KeyError, TypeError, ValueError, IndexError, AttributeError) as error:
        if isinstance(error, InputContractError):
            raise
        raise InputContractError(f'malformed execution state: {error}') from error


def read_execution_probe(state, head):
    """return a tagged saved tighter-head variant; never a predecessor."""
    require(isinstance(state, ExecutionState) and state.usage == 'annual' and head in HEADS, 'invalid probe base')
    resolution = state.heads[head]['resolution']
    require(state.manifest['season'] == '20252026' and resolution['status'] in ('passed', 'failed')
            and 'probe' in resolution, 'no checked numerical probe')
    reference = resolution['probe']
    _closed(reference, ('path', 'sha256'), 'probe reference')
    digest(reference['sha256'])
    path = _member(state.path.parent, reference['path'])
    require(identity(path)['sha256'] == reference['sha256'], 'probe hash differs')
    probe = read_json(path)
    _closed(probe, ('usage', 'head', 'baseline', 'metadata', 'arrays', 'comparison'), 'probe')
    require(probe['usage'] == 'numerical_probe' and probe['head'] == head, 'probe head identity differs')
    baseline = probe['baseline']
    _closed(baseline, ('path', 'sha256'), 'probe baseline')
    require(baseline['path'] == 'resolution/baseline.json', 'probe baseline locator differs')
    baseline_path = _member(state.path.parent, baseline['path'])
    require(identity(baseline_path)['sha256'] == baseline['sha256'], 'probe baseline hash differs')
    array_ref = probe['arrays']
    _closed(array_ref, ('path', 'sha256'), 'probe array')
    digest(array_ref['sha256'])
    require(array_ref['path'] == f'resolution/{head}.npz', 'probe coefficient path differs')
    array_path = _member(state.path.parent, array_ref['path'])
    require(identity(array_path)['sha256'] == array_ref['sha256'], 'probe array hash differs')
    metadata = probe['metadata']
    values = _load_arrays(array_path, metadata['arrays'])
    require(all(metadata[key] == state.heads[head][key] for key in ('head', 'target', 'design', 'actors', 'origin')), 'probe changes annual objective/design')
    for prior, original in zip(metadata['priors'], state.heads[head]['priors'], strict=True):
        require({key: value for key, value in prior.items() if key != 'prior_mean'} == {key: value for key, value in original.items() if key != 'prior_mean'}, 'probe changes annual prior')
    _head(metadata, head, values, state.manifest['season'])
    comparison = probe['comparison']
    require(resolution.get('baseline') == baseline and resolution.get('comparison') == comparison, 'probe comparison/baseline differs from resolution record')
    _closed(comparison, 'base_objective base_gradient_max optimizer_maxiter optimizer_ftol optimizer_gtol em_maxiter em_relative_tolerance em_responsibility_tolerance tightened_objective objective_change tightened_gradient_max gradient_max_change coefficient_max_change coefficient_l2_change maximum_probability_change head_maximum_changes terminal_maximum_changes evaluated_origins evaluated_branches'.split(), 'resolution comparison')
    require(comparison['optimizer_maxiter'] == 2000 and comparison['optimizer_ftol'] == 1e-15
            and comparison['optimizer_gtol'] == 1e-7 and comparison['em_maxiter'] == 100
            and comparison['em_relative_tolerance'] == 1e-9 and comparison['em_responsibility_tolerance'] == 1e-7,
            'resolution did not use tenfold tighter tolerances')
    require(metadata['diagnostics']['requested_starts'] == ['continuation']
            and metadata['selected_start'] == 'continuation', 'resolution is not a completed continuation')
    require(set(comparison['head_maximum_changes']) == set(HEADS)
            and set(comparison['terminal_maximum_changes']) == {'block','miss','stopped','continuing','goal'}, 'probability comparison axes differ')
    deltas = list(comparison['head_maximum_changes'].values()) + list(comparison['terminal_maximum_changes'].values())
    require(all(type(delta) in (int,float) and math.isfinite(delta) and 0 <= delta <= 1 for delta in deltas)
            and comparison['maximum_probability_change'] == max(deltas), 'probability maximum differs from component maxima')
    require(type(comparison['evaluated_origins']) is int and comparison['evaluated_origins'] >= 2*6*656
            and type(comparison['evaluated_branches']) is int and comparison['evaluated_branches'] >= comparison['evaluated_origins'], 'incomplete numerical probability probe counts')
    for key in ('base_gradient_max','tightened_gradient_max','gradient_max_change','coefficient_max_change','coefficient_l2_change'):
        _nonnegative(comparison[key], key)
    baseline_coefficients = state.arrays[head]['coefficients']
    difference = values['coefficients']-baseline_coefficients
    require(comparison['coefficient_max_change'] == float(np.max(np.abs(difference)))
            and comparison['coefficient_l2_change'] == float(np.linalg.norm(difference)), 'coefficient comparison differs from saved arrays')
    require(math.isclose(comparison['base_objective'],state.heads[head]['diagnostics']['objective'],rel_tol=1e-12,abs_tol=1e-12)
            and comparison['tightened_objective'] == metadata['diagnostics']['objective']
            and comparison['objective_change'] == comparison['tightened_objective']-comparison['base_objective'], 'objective comparison differs from saved solves')
    descriptor = read_json(baseline_path)
    covered = all(row['disposition'] != 'unavailable' for row in descriptor['selector']['requirements'])
    passed = covered and comparison['maximum_probability_change'] <= 1e-5
    require((resolution['status'] == 'passed') == passed, 'false numerical resolution verdict')
    _finite(comparison, 'resolution comparison')
    heads, arrays = dict(state.heads), dict(state.arrays)
    heads[head], arrays[head] = metadata, values
    return replace(state, heads=heads, arrays=arrays, usage='numerical_probe',
                   probe=dict(probe, sha256=reference['sha256'], annual_manifest_sha256=identity(state.path)['sha256']))
