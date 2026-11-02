"""temporary injected saved-state regression; no optimizer or source input."""
import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from hockey_stats import execution, execution_fit, execution_state as saved
from hockey_stats.captures import InputContractError
from hockey_stats.chance import TYPES
from hockey_stats.execution_design import DEFINITION, FAMILIES, RECIPE, TARGETS
from hockey_stats.shot_origins import grid


def metadata(head, attempts, positive):
    cells, edges = grid()
    lookup = {tuple(point): i for i, point in enumerate(cells)}
    representatives = [min(i, lookup[x, -y]) for i, (x, y) in enumerate(cells)]
    orbits = {point: i for i, point in enumerate(sorted(set(representatives)))}
    mirror = [orbits[point] for point in representatives]
    names, maps = ['intercept'], []
    for label in ['base'] + ['type:' + value for value in TYPES[1:]]:
        offset = len(names)
        maps.append([offset + i for i in mirror])
        names.extend(label + ':orbit:' + str(i) for i in range(len(orbits)))
    blocks = ['shooter'] + ([] if head == 'u' else ['goalie']) + (['setter'] if head == 'g' else []) + ['attacking_coach', 'defending_coach']
    setup = len(names) if head == 'g' else None
    if head == 'g':
        names.append('setup')
    ages = {}
    for block in blocks:
        if not block.endswith('coach'):
            ages[block] = {}
            for role in ('F', 'D', 'G'):
                ages[block][role] = [len(names), len(names)+1]
                names.extend([f'age:{block}:{role}:linear', f'age:{block}:{role}:quadratic'])
    design = dict(size=len(names), coefficient_names=names, columns=[], means=[], active=[], conditions={},
                  availability_conditions={}, feature_support={}, map_indices=maps, native_neighbors=edges.tolist(),
                  mirror_cells=mirror, circumstance_indices=[], actor_indices={b: {} for b in blocks},
                  actor_role_reasons={b: {} for b in blocks}, age_indices_by_block_role=ages, setup_index=setup,
                  families=list(FAMILIES)+([] if head == 'u' else ['goalie_workload', 'goalie_calendar_rest']),
                  trait_assumptions=['reported_hand_stable_trait'], fixed_transforms=DEFINITION['fixed_transforms'],
                  penalties=DEFINITION['penalties'], setter_mean_indices=[], setter_mean_weights=[])
    objective = attempts * math.log(2.)
    native = dict(converged=True, status=0, termination='injected completed baseline', iterations=0,
                  evaluations=1, objective=objective)
    solve = dict(native, gradient_max=0., inner_solves=[], objective_trace=[objective], em_iterations=0,
                 responsibility_change=None)
    if head == 'g':
        solve.update(inner_solves=[native], objective_trace=[objective, objective], em_iterations=1,
                     responsibility_change=0., relative_objective_change=0., objective_increases=[])
    reliability = [dict(lower=i/20, upper=(i+1)/20, count=attempts if i == 10 else 0,
                        observed_positive=positive if i == 10 else 0, predicted_mass=attempts*.5 if i == 10 else 0.)
                   for i in range(20)]
    sample = dict(attempts=attempts, positive=positive, class_fraction=positive/attempts,
                  mean_predicted_probability=.5, mean_imputation_weighted_negative_log_likelihood=math.log(2.),
                  mean_outcome_only_negative_log_likelihood=math.log(2.), reliability=reliability,
                  origin_mass_error=0., expanded_rows=attempts, candidate_branches=0,
                  base_matrix_nonzeros=0, batches=1)
    return dict(head=head, target=TARGETS[head], design=design, actors=[], priors=[],
                centers={b: dict(value=0., weight=0., prior_only=True) for b in ['shooter', 'goalie', 'setter', 'attacking_coach', 'defending_coach']},
                ledger=[], origin=dict(cells=656, distance_ft=20., direction_strength=4., law='uniform-release-forward-kernel'),
                arrays=None, starts=[dict(name='zero', deduplicated_to=None, **solve), dict(name='prior_mean', deduplicated_to='zero')],
                selected_start='zero', diagnostics=dict(solve, requested_starts=['zero', 'prior_mean'], wall_seconds=.01, in_sample=sample),
                resolution=dict(status='pending'), status='complete', reasons=[])


def main(output, native_endpoint=None):
    output.mkdir()
    (output/'heads').mkdir()
    heads = {head: metadata(head, n, p) for head, n, p in zip(saved.HEADS, [5, 4, 3, 2], [4, 3, 2, 1])}
    arrays = {h: dict(coefficients=np.zeros(m['design']['size'], dtype=np.float64)) for h, m in heads.items()}
    member = dict(kind='game', season='20252026', game_id='synthetic', path='/synthetic/game.json', sha256='0'*64)
    prepared = dict(path='/synthetic/manifest.json', sha256='0'*64, purpose='fixture', members=[member, dict(kind='people', season='20252026', game_id=None, path='/synthetic/people.json', sha256='0'*64)])
    coaches = dict(path='/synthetic/coaches.json', sha256='0'*64, purpose='fixture', selected_game_ids=['synthetic'])
    rows = []
    for index, outcome in enumerate(['block', 'miss', 'save', 'save', 'goal']):
        records = {}
        for h, included, target in [('u', True, float(index > 0)), ('q', index > 0, float(index > 1)),
                                    ('r', index > 1, float(index > 2)), ('g', index > 2, float(index > 3))]:
            records[h] = dict(included=included, target=target if included else None, reasons=[] if included else ['synthetic condition absent'])
        rows.append(dict(key=f'synthetic:{index}', game_id='synthetic', source_index=index, pointer=f'/attempts/{index}',
                         outcome=outcome, full_probability_context=True,
                         goalie_identity=dict(status='identified', player_id=1, membership_id=1, dated_team_id=1, reported_position='G', reason=None, pointers=['/synthetic']),
                         heads=records, source_supported=True, candidate_universe_complete=True, setter_discrepancy=None, immediate_stop_known=True))
    coverage = dict(purpose='fixture', season='20252026', games=[dict(game_id='synthetic', game_date='2025-10-01', status='synthetic', recognized_attempts=5, prepared_member=member)],
                    attempts=rows, heads={h: dict(included=n, excluded=5-n, **{'class:0':1, 'class:1':n-1}) for h, n in zip(saved.HEADS, [5,4,3,2])},
                    optional_features={h: {} for h in saved.HEADS})
    names = ['type:'+name for name in TYPES]+['outcome:'+name for name in ['block','miss','save','goal']]+['missing_context','tip','off_ice_setter','incomplete_setter']
    selector = dict(policy='strength,type,outcome,missing,tip,off-ice,incomplete,sparse; first (game_id,integer_source_index); numeric source-key fill; maximum256 actual',
                    purpose='fixture', requirements=[dict(requirement=name, key=None, disposition='unavailable') for name in names], keys=['synthetic:0'],
                    population=dict(eligible_contexts=5, withheld_contexts=[]), fixture_witnesses=[],
                    synthetic_geometry=dict(context_key='synthetic:0', types=list(TYPES), cells=list(range(656)), execution=['actual','neutral']))
    manifest = dict(schema_version=1, kind='execution-state', purpose='fixture', season='20252026', recipe=deepcopy(RECIPE),
                    implementation=dict(kind='synthetic-injection'), prepared=prepared, coaches=coaches, previous=None, training_cutoff='2026-02-01',
                    resources=dict(wall_seconds=.1, input_read_wall_seconds=0., design_wall_seconds=0., fit_wall_seconds=.1,
                                   wall_scope='initial_input_read+prepare_execution+fit_and_members_before_completion_manifest', peak_memory_bytes=0, output_bytes=0,
                                   dimensions={h:m['design']['size'] for h,m in heads.items()}, solve_counts={h:1 for h in saved.HEADS},
                                   resolution_solve_counts={h:0 for h in saved.HEADS}, origin_rows={h:n for h,n in zip(saved.HEADS,[5,4,3,2])}, candidate_branches={h:0 for h in saved.HEADS}))
    injected = {}
    for h in saved.HEADS:
        objective = heads[h]['diagnostics']['objective']
        native = dict(converged=False, status=1, termination='injected native evaluation limit', iterations=3, evaluations=5, objective=objective)
        start = dict(name='continuation', deduplicated_to=None, **native, gradient_max=.25,
                     inner_solves=[], objective_trace=[objective], em_iterations=0, responsibility_change=None)
        if h == 'g':
            completed_inner=dict(native,converged=True,status=0,termination='injected completed first m-step')
            start.update(termination='setter em inner solve failed', inner_solves=[completed_inner,native], em_iterations=2,
                         iterations=6,evaluations=10,objective_trace=[objective,objective],responsibility_change=0.,
                         objective_increases=[], relative_objective_change=0.)
        stop=DEFINITION['solver']['continuation'];solver=DEFINITION['solver']
        injected[h]=dict(status='unavailable', reasons=['no_completed_start'], selected_start=None,
                         requested_starts=['continuation'], starts=[start], wall_seconds=.125, coefficients=None,
                         comparison=dict(base_objective=objective,base_gradient_max=0.,optimizer_maxiter=solver['maxiter'],
                                         optimizer_ftol=stop['ftol'],optimizer_gtol=stop['gtol'],em_maxiter=solver['em_maxiter'],
                                         em_relative_tolerance=stop['em_objective'],em_responsibility_tolerance=stop['em_responsibility'],
                                         coefficient_max_change=0.,coefficient_l2_change=0.))
        saved.write_execution_head(output, heads[h], arrays[h], '20252026')
    baseline_bytes = {str(p.relative_to(output)): p.read_bytes() for p in (output/'heads').glob('*.npz')}
    design=SimpleNamespace(heads={h:dict(head=h,actors=[],size=heads[h]['design']['size'],target=np.array([0.,1.])) for h in saved.HEADS},season='20252026',coverage=coverage)
    def no_solve(*args, **kwargs):
        raise AssertionError('optimizer or objective unexpectedly called')
    original_continue=execution_fit.continue_head
    native_calls=[]
    def continued(d, incoming, baseline):
        if d['head']!='u' or native_endpoint is None:return deepcopy(injected[d['head']])
        objective_value=heads['u']['diagnostics']['objective']
        endpoint=np.zeros_like(baseline)
        endpoint[:2]=[np.nan,np.inf] if native_endpoint=='nonfinite' else [3.,4.]
        if native_endpoint=='overflow':endpoint[:2]=[1e308,0.]
        def native(objective, initial, **options):
            assert options==dict(maxiter=10000,ftol=1e-16,gtol=1e-7)
            native_calls.append(options)
            return endpoint.copy(),dict(converged=False,status=2,termination='injected native abnormal return',iterations=1,evaluations=3,
                                        objective=None if native_endpoint in ('nonfinite','finite_bad_objective') else objective_value+.01)
        def objective(beta, *_):
            if not np.isfinite(beta).all() or native_endpoint=='finite_bad_objective' and np.any(beta):
                return float('nan'),np.full_like(beta,np.nan)
            return objective_value+(.01 if np.any(beta) else 0.),np.zeros_like(beta)
        with patch.object(execution_fit,'solve_logistic',native),patch.object(execution_fit,'objective',objective):
            result=original_continue(d,incoming,baseline)
        injected['u']=result
        return result
    with patch.object(execution_fit,'continue_head',continued), \
         patch.object(execution,'_resolution_selector',return_value=(selector,(object(),))), \
         patch.object(execution_fit,'solve_logistic',no_solve), patch.object(execution_fit,'objective',no_solve):
        execution._resolve_final_year(design,None,output,manifest,heads,arrays)
        state=saved.write_execution_state(output,manifest,heads,arrays,coverage,_reserved=True)
    for h in saved.HEADS:
        expected = dict(requested_starts=injected[h]['requested_starts'], starts=injected[h]['starts'],
                        selected_start=None, wall_seconds=injected[h]['wall_seconds'])
        assert state.heads[h]['resolution'].get('diagnostics')==expected, (h,'failed native start lost on saved-state round trip',state.heads[h]['resolution'])
        assert state.heads[h]['resolution']['comparison']==injected[h]['comparison']
        assert state.heads[h]['status']=='complete' and state.heads[h]['selected_start']=='zero'
        assert not (output/f'resolution/{h}.npz').exists() and not (output/f'resolution/{h}.json').exists()
    assert all((output/p).read_bytes()==b for p,b in baseline_bytes.items())
    if native_endpoint is not None:
        assert len(native_calls)==1 and injected['u']['coefficients'] is None
        comparison=state.heads['u']['resolution']['comparison']
        if native_endpoint=='nonfinite':
            assert injected['u']['starts'][0]['objective_trace']==[] and injected['u']['endpoints']=={}
            assert comparison['coefficient_max_change'] is comparison['coefficient_l2_change'] is None
        elif native_endpoint=='overflow':assert comparison['coefficient_max_change']==1e308 and comparison['coefficient_l2_change'] is None
        else:
            assert comparison['coefficient_max_change']==4. and comparison['coefficient_l2_change']==5.
            if native_endpoint=='finite_bad_objective':assert injected['u']['starts'][0]['objective_trace']==[]
    original_manifest_bytes=(output/'manifest.json').read_bytes()
    original_head_bytes={h:(output/f'heads/{h}.json').read_bytes() for h in saved.HEADS}
    original_manifest=json.loads(original_manifest_bytes)
    original_heads={h:json.loads(b) for h,b in original_head_bytes.items()}
    rejected=[]
    def reject(label, mutate, head='u', resource=False, resource_count=None):
        m=deepcopy(original_manifest);metadata=deepcopy(original_heads[head])
        mutate(m if resource else metadata['resolution'])
        if resource_count is not None:m['resources']['resolution_solve_counts'][head]=resource_count
        if not resource:
            (output/f'heads/{head}.json').write_text(json.dumps(metadata))
            digest=hashlib.sha256((output/f'heads/{head}.json').read_bytes()).hexdigest()
            next(r for r in m['files'] if r['path']==f'heads/{head}.json')['sha256']=digest
        m['resources']['output_bytes']=sum((output/r['path']).stat().st_size for r in m['files'])
        (output/'manifest.json').write_text(json.dumps(m))
        try:
            saved.read_execution_state(output,'fixture')
        except InputContractError as error:
            rejected.append(dict(case=label,reason=str(error)))
        else:
            raise AssertionError('strict reader accepted '+label)
        (output/f'heads/{head}.json').write_bytes(original_head_bytes[head])
        (output/'manifest.json').write_bytes(original_manifest_bytes)
    reject('empty diagnostics',lambda r:r.update(diagnostics={}))
    reject('missing starts',lambda r:r['diagnostics'].pop('starts'))
    reject('false convergence',lambda r:r['diagnostics']['starts'][0].update(converged=True))
    reject('wrong requested start',lambda r:r['diagnostics'].update(requested_starts=['zero']))
    reject('duplicate continuation',lambda r:r['diagnostics']['starts'].append(deepcopy(r['diagnostics']['starts'][0])))
    reject('deduplicated continuation',lambda r:r['diagnostics']['starts'][0].update(deduplicated_to='zero'))
    reject('missing deduplication record',lambda r:r['diagnostics']['starts'][0].pop('deduplicated_to'))
    reject('selected failed start',lambda r:r['diagnostics'].update(selected_start='continuation'))
    reject('missing termination',lambda r:r['diagnostics']['starts'][0].pop('termination'))
    for control in ['optimizer_maxiter','optimizer_ftol','optimizer_gtol','em_maxiter','em_relative_tolerance','em_responsibility_tolerance']:
        reject('changed '+control,lambda r,key=control:r['comparison'].update({key:2*r['comparison'][key]}))
    reject('invented probability comparison',lambda r:r['comparison'].update(maximum_probability_change=0.))
    reject('negative movement maximum',lambda r:r['comparison'].update(coefficient_max_change=-1.))
    reject('invalid movement norm',lambda r:r['comparison'].update(coefficient_l2_change='unknown'))
    reject('negative wall time',lambda r:r['diagnostics'].update(wall_seconds=-1.))
    reject('baseline objective mismatch',lambda r:r['comparison'].update(base_objective=1.))
    reject('wrong baseline reference',lambda r:r['baseline'].update(sha256='f'*64))
    reject('g em count mismatch',lambda r:r['diagnostics']['starts'][0].update(em_iterations=3),head='g')
    reject('g empty native solves',lambda r:r['diagnostics']['starts'][0].update(inner_solves=[],em_iterations=0),head='g',resource_count=0)
    reject('u resource count mismatch',lambda m:m['resources']['resolution_solve_counts'].update(u=2),resource=True)
    reject('g inner count mismatch',lambda m:m['resources']['resolution_solve_counts'].update(g=3),head='g',resource=True)
    saved.read_execution_state(output,'fixture')
    # a completed continuation may fail the coverage/probability gate and still
    # legitimately retain its probe; that existing shape must remain readable.
    probe_metadata=deepcopy(original_heads['u'])
    probe_metadata.update(resolution=dict(status='pending'),selected_start='continuation',
                          starts=[dict(probe_metadata['starts'][0],name='continuation')])
    probe_metadata['diagnostics']['requested_starts']=['continuation']
    comparison=dict(injected['u']['comparison'],tightened_objective=probe_metadata['diagnostics']['objective'],
                    objective_change=0.,tightened_gradient_max=0.,gradient_max_change=0.,coefficient_max_change=0.,coefficient_l2_change=0.,
                    maximum_probability_change=0.,head_maximum_changes={h:0. for h in saved.HEADS},
                    terminal_maximum_changes={h:0. for h in ['block','miss','stopped','continuing','goal']},
                    evaluated_origins=2*6*656,evaluated_branches=2*6*656)
    baseline=original_heads['u']['resolution']['baseline']
    reference=saved.write_execution_probe(output,baseline,probe_metadata,arrays['u'],comparison)
    annual=deepcopy(original_heads['u']);annual['resolution']=dict(status='failed',baseline=baseline,probe=reference,comparison=comparison)
    (output/'heads/u.json').write_text(json.dumps(annual))
    manifest=deepcopy(original_manifest)
    for relative in ['heads/u.json','resolution/u.json','resolution/u.npz']:
        reference=dict(path=relative,sha256=hashlib.sha256((output/relative).read_bytes()).hexdigest())
        existing=next((r for r in manifest['files'] if r['path']==relative),None)
        if existing is None:manifest['files'].append(reference)
        else:existing.update(reference)
    manifest['resources']['output_bytes']=sum((output/r['path']).stat().st_size for r in manifest['files'])
    (output/'manifest.json').write_text(json.dumps(manifest))
    with patch.object(execution_fit,'fit_head',no_solve),patch.object(execution_fit,'objective',no_solve):
        checked=saved.read_execution_state(output,'fixture')
    assert checked.heads['u']['resolution']['status']=='failed' and 'probe' in checked.heads['u']['resolution']
    return dict(status='passed',scope='synthetic injected failed continuation through actual resolution writer and strict state save/read; no optimizer/source inputs',
                passed_heads=list(saved.HEADS),negative_cases=rejected,baseline_npz_bytes_unchanged=True,
                nonconverged_probe_members=0,converged_failed_with_probe_control='accepted unchanged contract',
                native_result_path=native_endpoint,native_stub_calls=len(native_calls),
                retained_u_start=injected['u']['starts'][0],retained_u_comparison=injected['u']['comparison'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--native-endpoint',choices=['finite','nonfinite','finite_bad_objective','overflow']);args=parser.parse_args()
    print(json.dumps(main(args.out,args.native_endpoint),indent=2))
