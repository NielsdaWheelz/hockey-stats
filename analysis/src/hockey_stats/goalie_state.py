"""strict, detached two-head goalie artifacts; base execution files stay immutable."""

from dataclasses import dataclass, replace
from datetime import date
from hashlib import sha256
import json
import math
from pathlib import Path

import numpy as np

from .input_locations import input_path
from .artifacts import clean_implementation, digest, require, require_fields, write_arrays, write_json
from .captures import InputContractError
from .chance_cli import identity, read_json
from .execution_state import (
    coefficient_array_contract, read_coefficient_arrays, require_finite_state,
    require_nonnegative, require_state_reference, season_start_year, state_member_path,
    validate_actor_history, validate_design, validate_solve_record,
)

HEADS = ('h', 'd')
MANIFEST_KEYS = 'schema_version kind purpose season recipe implementation prepared coaches base_state base_scores previous training_cutoff heads files resources'.split()
HEAD_KEYS = 'head target target_kind target_mass keys design actors priors centers ledger arrays starts selected_start diagnostics status reasons'.split()
TARGET_KEYS = 'key game_id source_index outcome physical_status goalie_id physical_state h_label h_reason successor_key target_score_sha256 d_target d_reason h_included d_included h_exclusions'.split()
RESOURCE_KEYS = 'wall_seconds peak_memory_bytes design_wall_seconds input_read_wall_seconds dimensions solve_counts probe_solve_counts output_bytes'.split()


@dataclass(frozen=True)
class GoalieState:
    path: Path
    manifest: dict
    heads: dict
    arrays: dict
    coverage: dict
    usage: str = 'annual'
    probes: dict | None = None


def _hash(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(',', ':'),allow_nan=False).encode()).hexdigest()


def _sample(value, fractional):
    require_fields(value, 'attempts positive class_fraction mean_predicted_probability mean_imputation_weighted_negative_log_likelihood mean_outcome_only_negative_log_likelihood reliability origin_mass_error expanded_rows candidate_branches base_matrix_nonzeros batches'.split(), 'goalie in-sample')
    for key in ('attempts','expanded_rows','candidate_branches','base_matrix_nonzeros','batches'):
        require(type(value[key]) is int and value[key] >= 0, 'invalid goalie diagnostic count')
    positive, count = value['positive'], value['attempts']
    require(type(positive) in ((int,float) if fractional else (int,)) and 0 < positive < count
            and value['class_fraction'] == positive/count, 'goalie target mass differs')
    require(type(value['reliability']) is list and len(value['reliability']) == 20, 'goalie reliability bins differ')
    for index,row in enumerate(value['reliability']):
        require_fields(row, ('lower','upper','count','observed_positive','predicted_mass'), 'goalie reliability bin')
        require(row['lower']==index/20 and row['upper']==(index+1)/20 and type(row['count']) is int
                and 0 <= row['observed_positive'] <= row['count']
                and row['lower']*row['count']-1e-10 <= row['predicted_mass'] <= row['upper']*row['count']+1e-10,
                'invalid goalie reliability bin')
    require(sum(r['count'] for r in value['reliability']) == count
            and math.isclose(sum(r['observed_positive'] for r in value['reliability']),positive,rel_tol=1e-12,abs_tol=1e-12)
            and math.isclose(sum(r['predicted_mass'] for r in value['reliability'])/count,
                             value['mean_predicted_probability'],rel_tol=1e-12,abs_tol=1e-12),
            'goalie reliability mass accounting differs')
    for key in ('mean_imputation_weighted_negative_log_likelihood','mean_outcome_only_negative_log_likelihood','origin_mass_error'):
        require_nonnegative(value[key],key)


def _head(metadata, head, arrays, season, *, probe=False):
    from .goalie import TARGETS, DEFINITION

    require_fields(metadata,HEAD_KEYS,'goalie head')
    require_finite_state(metadata,'goalie head')
    require(metadata['head']==head and head in HEADS and metadata['target']==TARGETS[head]
            and metadata['target_kind']==DEFINITION['target_kinds'][head], 'goalie head target differs')
    require(metadata['status'] in ('complete','unavailable') and type(metadata['reasons']) is list
            and all(type(v) is str and v for v in metadata['reasons']), 'invalid goalie head status')
    keys=metadata['keys']
    require(type(keys) is list and len(keys)==len(set(keys)) and all(type(k) is str and k for k in keys),
            'invalid goalie likelihood keys')
    require_nonnegative(metadata['target_mass'],'goalie target mass')
    require(metadata['target_mass'] <= len(keys), 'target mass exceeds likelihood count')
    require(type(metadata['diagnostics']) is dict and type(metadata['starts']) is list,'missing goalie diagnostics')
    require(metadata['diagnostics']['requested_starts'] == (['continuation'] if probe else ['zero','prior_mean']),
            'goalie start policy differs')
    require_nonnegative(metadata['diagnostics']['wall_seconds'],'goalie head wall time')
    for row in metadata['starts']:
        if row.get('deduplicated_to') is not None:
            require_fields(row,('name','deduplicated_to'),'goalie deduplicated start')
            require(not probe and row==dict(name='prior_mean',deduplicated_to='zero'), 'invalid goalie deduplication')
        else:
            require_fields(row,'name deduplicated_to converged status termination iterations evaluations objective gradient_max inner_solves objective_trace em_iterations responsibility_change'.split(),'goalie solve')
            validate_solve_record(row,head,probe)
    if metadata['starts']:
        require([r['name'] for r in metadata['starts']]==metadata['diagnostics']['requested_starts'],
                'goalie starts omit requested solve')
    complete=metadata['status']=='complete'
    if not complete:
        expected_reason='empty_head' if not keys else 'single_class_head' if metadata['target_mass'] in (0.,len(keys)) else 'no_completed_start'
        require(metadata['reasons']==[expected_reason] and (bool(metadata['starts'])==(expected_reason=='no_completed_start')),
                'goalie unavailable disposition contradicts target support/solve attempts')
        require_fields(metadata['diagnostics'],('requested_starts','wall_seconds'),'unavailable goalie diagnostics')
        require(not arrays and metadata['arrays'] is None and metadata['selected_start'] is None
                and metadata['centers'] is None and bool(metadata['reasons']), 'unavailable goalie head carries endpoint')
        require(not any(r.get('converged') for r in metadata['starts']), 'unavailable goalie head has completed start')
        validate_design(metadata,{'coefficients':np.zeros(metadata['design']['size'])})
        validate_actor_history(metadata,None,season)
        return
    require(not metadata['reasons'] and set(arrays)=={'coefficients'}
            and set(metadata['centers'])=={'shooter','goalie','setter','attacking_coach','defending_coach'},
            'complete goalie head lacks fitted state')
    validate_design(metadata,arrays)
    validate_actor_history(metadata,arrays['coefficients'],season)
    completed=[r for r in metadata['starts'] if r.get('converged')]
    require(bool(completed),'complete goalie head has no completed solve')
    best=min(completed,key=lambda r:r['objective'])
    require(metadata['selected_start']==best['name'], 'goalie selected start is not lower completed objective')
    diagnostics=metadata['diagnostics']
    require({k:v for k,v in diagnostics.items() if k not in ('in_sample','requested_starts','wall_seconds')}
            == {k:v for k,v in best.items() if k not in ('name','deduplicated_to')}, 'goalie selected diagnostics differ')
    _sample(diagnostics['in_sample'],head=='d')
    sample=diagnostics['in_sample']
    require(sample['attempts']==len(keys) and sample['positive']==metadata['target_mass'], 'goalie likelihood diagnostics differ from targets')
    from .execution_fit import penalty
    design=metadata['design']
    numerical=dict(map_indices=design['map_indices'],native_neighbors=design['native_neighbors'],
                   circumstance_indices=design['circumstance_indices'],
                   age_indices=[i for roles in design['age_indices_by_block_role'].values() for pair in roles.values() for i in pair])
    prior_by_key={(r['block'],r['id']):r for r in metadata['priors']}
    actors=[dict(r,**{k:v for k,v in prior_by_key[r['block'],r['id']].items() if k not in ('block','id')}) for r in metadata['actors']]
    value,_=penalty(arrays['coefficients'],numerical,actors)
    expected=sample['attempts']*sample['mean_imputation_weighted_negative_log_likelihood']+value
    require(math.isclose(diagnostics['objective'],expected,rel_tol=1e-8,abs_tol=1e-8),
            'goalie objective differs from likelihood and penalties')
    require_finite_state(metadata,'goalie head')


def write_goalie_head(output,metadata,arrays,season,*,probe=False,name=None):
    head=metadata['head']; name=name or head
    metadata['arrays']=coefficient_array_contract(arrays) if arrays else None
    _head(metadata,head,arrays,season,probe=probe)
    if arrays:
        write_arrays(Path(output),f'heads/{name}.npz',arrays)
    write_json(Path(output)/f'heads/{name}.json',metadata)


def freeze_goalie_baseline(output,manifest,heads,targets,selector):
    """freeze exact design, targets, priors and baseline before any continuation."""
    descriptor=dict(schema_version=1,kind='goalie-baseline',purpose=manifest['purpose'],season=manifest['season'],
        recipe_sha256=manifest['recipe']['sha256'],base_scores=manifest['base_scores'],
        target_sha256=_hash(list(targets)),selector=selector,
        heads={h:dict(metadata_sha256=identity(Path(output)/f'heads/{h}.json')['sha256'],
                      coefficient_sha256=None if heads[h]['status']!='complete' else identity(Path(output)/f'heads/{h}.npz')['sha256'],
                      design_sha256=_hash(heads[h]['design']),prior_sha256=_hash(heads[h]['priors'])) for h in HEADS})
    write_json(Path(output)/'baseline.json',descriptor)
    return dict(path='baseline.json',sha256=identity(Path(output)/'baseline.json')['sha256'])


def write_goalie_probe(output,head,baseline,metadata,arrays,comparison,season):
    name=head+'-tight'
    write_goalie_head(output,metadata,arrays,season,probe=True,name=name)
    return dict(status='assessed' if metadata['status']=='complete' else 'unassessed',
                reason=None if metadata['status']=='complete' else 'continuation_'+metadata['reasons'][0],
                baseline=baseline,head_path=f'heads/{name}.json',array_path=f'heads/{name}.npz' if arrays else None,
                comparison=comparison)


def _manifest(value,purpose):
    from .goalie import RECIPE
    from .execution_design import RECIPE as BASE_RECIPE

    require_fields(value,MANIFEST_KEYS,'goalie manifest')
    require_finite_state(value,'goalie manifest')
    require(value['schema_version']==1 and type(value['schema_version']) is int and value['kind']=='goalie-continuation'
            and purpose in ('real','fixture') and value['purpose']==purpose,'goalie state version/purpose differs')
    year=season_start_year(value['season'])
    require(2021<=year<=2025 and value['recipe']==RECIPE,'goalie recipe/season differs')
    for name,keys in (('prepared',('purpose','path','sha256','members')),('coaches',('purpose','path','sha256','selected_game_ids'))):
        require_fields(value[name],keys,'goalie '+name)
        require_state_reference(value[name],name)
        require(value[name]['purpose']==purpose,'goalie input purpose differs')
    members=value['prepared']['members']
    require(type(members) is list,'missing goalie prepared members')
    for row in members:
        require_fields(row,('kind','season','game_id','path','sha256'),'goalie prepared member')
        digest(row['sha256'])
        require(row['season']==value['season'] and row['kind'] in ('game','people'),'goalie prepared member season differs')
    games=[r['game_id'] for r in members if r['kind']=='game']
    require(len(games)==len(set(games)) and sum(r['kind']=='people' for r in members)==1
            and value['coaches']['selected_game_ids']==games,'goalie prepared/coach game axis differs')
    require_fields(value['base_scores'],('path','sha256'),'goalie base scores')
    require_state_reference(value['base_scores'],'goalie base scores')
    base=value['base_state']
    require_fields(base,('path','sha256','season','purpose','recipe_sha256','usage','previous'),'goalie base state')
    require_state_reference(base,'goalie base state')
    require(base['season']==value['season'] and base['purpose']==purpose and base['usage']=='annual'
            and base['recipe_sha256']==BASE_RECIPE['sha256'],'goalie base-state identity differs')
    if base['previous'] is not None:
        require_fields(base['previous'],('path','sha256'),'base predecessor'); require_state_reference(base['previous'],'base predecessor')
    previous=value['previous']
    if previous is None:
        require(purpose!='real' or year==2021,'real goalie chain must start in 20212022')
    else:
        require_fields(previous,('path','sha256','season','purpose','recipe_sha256','usage'),'goalie previous')
        require_state_reference(previous,'goalie previous')
        require(previous['season']==f'{year-1}{year}' and previous['purpose']==purpose
                and previous['recipe_sha256']==RECIPE['sha256'] and previous['usage']=='annual', 'goalie chronology differs')
    cutoff=date.fromisoformat(value['training_cutoff'])
    require(year<=cutoff.year<=year+1,'goalie training cutoff outside season')
    producer=value['implementation']
    require_fields(producer,('git_commit','git_dirty','python_version','numpy_version','scipy_version','lockfile_sha256'),'goalie implementation')
    require(type(producer['git_commit']) is str and len(producer['git_commit'])==40
            and all(c in '0123456789abcdef' for c in producer['git_commit']) and type(producer['git_dirty']) is bool
            and all(type(producer[k]) is str and producer[k] for k in ('python_version','numpy_version','scipy_version')),
            'invalid goalie implementation identity')
    digest(producer['lockfile_sha256'])
    if purpose=='real':
        clean_implementation(producer)
    costs=value['resources']; require_fields(costs,RESOURCE_KEYS,'goalie resources')
    for key in ('wall_seconds','design_wall_seconds','input_read_wall_seconds'):
        require_nonnegative(costs[key],key)
    for key in ('peak_memory_bytes','output_bytes'):
        require(type(costs[key]) is int and costs[key]>=0,'invalid goalie resource count')
    for key in ('dimensions','solve_counts','probe_solve_counts'):
        require(type(costs[key]) is dict and set(costs[key])==set(HEADS)
                and all(type(v) is int and v>=0 for v in costs[key].values()),'invalid goalie resource head axes')
    require(all(v in (0,1) for v in costs['probe_solve_counts'].values()),'more than one goalie probe solve')
    require(type(value['heads']) is dict and set(value['heads'])==set(HEADS),'goalie heads must be exactly h/d')


def validate_goalie_target(row,manifest):
    """validate one detached keyed target using its annual input bindings."""
    games=set(manifest['coaches']['selected_game_ids'])
    require_fields(row,TARGET_KEYS,'goalie target')
    require(row['game_id'] in games and type(row['source_index']) is int and row['source_index']>=0
            and row['key']==row['game_id']+':'+str(row['source_index']),'invalid goalie focal key')
    require(row['outcome'] in ('block','miss','save','goal',None) and row['physical_status'] in ('ordinary','outside_population','unresolved'),
            'invalid goalie source outcome/status')
    require(row['goalie_id'] is None or type(row['goalie_id']) is int and row['goalie_id']>0,'invalid goalie target actor')
    state=row['physical_state']
    require(state is None or type(state) is list and len(state)==4 and all(type(v) is int for v in state)
            and state[0]>=0 and state[1]>=0 and state[2]>=0 and state[3]>=0,'invalid target physical state')
    require(row['h_label'] is None or type(row['h_label']) is bool,'invalid recorded occurrence label')
    require((row['h_label'] is None)==(row['h_reason'] is not None)
            and (row['h_reason'] is None or type(row['h_reason']) is str and bool(row['h_reason'])),'invalid h reason')
    require(row['successor_key'] is None or type(row['successor_key']) is str
            and row['successor_key'].startswith(row['game_id']+':') and row['successor_key']!=row['key'], 'invalid successor key')
    if row['successor_key'] is not None:
        suffix=row['successor_key'].removeprefix(row['game_id']+':')
        require(suffix.isascii() and suffix.isdecimal() and str(int(suffix))==suffix,'noncanonical goalie successor source index')
    require(row['target_score_sha256']==manifest['base_scores']['sha256'],'goalie target score identity differs')
    require(type(row['h_exclusions']) is list and all(type(v) is str and v for v in row['h_exclusions'])
            and len(row['h_exclusions'])==len(set(row['h_exclusions']))
            and type(row['h_included']) is bool and type(row['d_included']) is bool,'invalid goalie likelihood disposition')
    require(row['h_included']==(not row['h_exclusions']),'h inclusion contradicts exclusions')
    if row['h_included']:
        require(row['outcome']=='save' and row['physical_status']=='ordinary' and row['goalie_id'] is not None
                and state is not None and 3<=state[0]<=6 and 3<=state[1]<=6 and state[2] in (0,1) and state[3]==1
                and type(row['h_label']) is bool,'unsupported occurrence likelihood row')
    danger=row['d_target']
    if row['d_included']:
        require(row['h_included'] and row['h_label'] is True and row['successor_key'] is not None
                and type(danger) in (int,float) and math.isfinite(danger) and 0<=danger<=1
                and row['d_reason'] is None,'invalid fractional danger target')
    else:
        require(danger is None and type(row['d_reason']) is str and bool(row['d_reason']),'missing danger target became zero')


def _coverage(value,manifest,heads):
    from .goalie import target_coverage

    require_fields(value,('targets','summary'),'goalie target coverage')
    targets=value['targets']; require(type(targets) is list,'missing goalie target rows')
    keys=[]; games=set(manifest['coaches']['selected_game_ids'])
    for row in targets:
        validate_goalie_target(row,manifest)
        keys.append(row['key'])
    require(len(keys)==len(set(keys)),'duplicate goalie focal target keys')
    for head in HEADS:
        selected=[r for r in targets if r[head+'_included']]
        require(heads[head]['keys']==[r['key'] for r in selected]
                and math.isclose(heads[head]['target_mass'],sum(float(r['h_label'] if head=='h' else r['d_target']) for r in selected),
                                 rel_tol=1e-12,abs_tol=1e-12),'goalie head target rows/mass differ')
        counts={}
        for row in selected:
            actor=str(row['goalie_id']); counts[actor]=counts.get(actor,0)+1
        for actor in heads[head]['actors']:
            if actor['block']=='goalie':
                require(actor['likelihood_support']==counts.get(actor['id'],0),'goalie actor likelihood support differs')
    require(value['summary']==target_coverage(targets,manifest['season']),'goalie coverage reductions differ')
    require_finite_state(value,'goalie target coverage')


def write_goalie_state(output,manifest,heads,arrays,targets,summary,probes):
    output=Path(output)
    write_json(output/'coverage.json',dict(targets=list(targets),summary=summary),compact=True)
    if not probes:
        probes={head:dict(status='not_assessed_for_annual_state',reason='only final selected annual is probed') for head in HEADS}
    write_json(output/'numerical.json',dict(heads=probes))
    roles={'coverage.json':'coverage','numerical.json':'numerical','baseline.json':'baseline'}
    roles.update({f'heads/{h}.json':'head:'+h for h in HEADS})
    roles.update({f'heads/{h}.npz':'coefficients:'+h for h in HEADS})
    roles.update({f'heads/{h}-tight.json':'probe-head:'+h for h in HEADS})
    roles.update({f'heads/{h}-tight.npz':'probe-coefficients:'+h for h in HEADS})
    files=[dict(role=roles[p.relative_to(output).as_posix()],path=p.relative_to(output).as_posix(),sha256=identity(p)['sha256'])
           for p in sorted(output.rglob('*')) if p.is_file()]
    manifest['heads']={h:dict(path=f'heads/{h}.json',sha256=identity(output/f'heads/{h}.json')['sha256']) for h in HEADS}
    manifest['files']=files
    manifest['resources']['output_bytes']=sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
    _manifest(manifest,manifest['purpose'])
    state = _read_goalie_state(output/'manifest.json',manifest,manifest['purpose'])
    write_json(output/'manifest.json',manifest)
    return state


def _read_goalie_state(path,manifest,expected_purpose):
    try:
        _manifest(manifest,expected_purpose)
        root=path.parent; files=manifest['files']; require(type(files) is list,'missing goalie state members')
        by_role={}
        for row in files:
            require_fields(row,('role','path','sha256'),'goalie member')
            require(row['role'] not in by_role,'duplicate goalie member role')
            member=state_member_path(root,row['path']); digest(row['sha256'])
            require(identity(member)['sha256']==row['sha256'],'goalie member digest differs')
            by_role[row['role']]=row
        require(len({r['path'] for r in files})==len(files),'duplicate goalie member path')
        heads,arrays={},{}
        expected={'coverage','numerical'}
        for head in HEADS:
            ref=manifest['heads'][head]; require_fields(ref,('path','sha256'),'goalie head reference')
            record=by_role.get('head:'+head)
            require(record is not None and ref=={k:record[k] for k in ('path','sha256')}
                    and ref['path']==f'heads/{head}.json','goalie head role differs')
            expected.add('head:'+head)
            metadata=read_json(root/ref['path']); heads[head]=metadata
            if metadata['arrays'] is None:
                arrays[head]={}
            else:
                expected.add('coefficients:'+head)
                record=by_role.get('coefficients:'+head)
                require(record is not None and record['path']==f'heads/{head}.npz','missing goalie coefficient member')
                arrays[head]=read_coefficient_arrays(root/record['path'],metadata['arrays'])
            _head(metadata,head,arrays[head],manifest['season'])
        coverage=read_json(root/by_role['coverage']['path']); _coverage(coverage,manifest,heads)
        require(by_role['coverage']['path']=='coverage.json' and by_role['numerical']['path']=='numerical.json','goalie fixed member path differs')
        numerical=read_json(root/by_role['numerical']['path']); require_fields(numerical,('heads',),'goalie numerical')
        require(set(numerical['heads'])==set(HEADS),'goalie probe axes differ')
        baseline=None
        if 'baseline' in by_role:
            expected.add('baseline'); require(by_role['baseline']['path']=='baseline.json','goalie baseline path differs')
            baseline=read_json(root/'baseline.json')
            _baseline(baseline,manifest,heads,coverage,by_role)
        if manifest['purpose']=='real':
            require((baseline is not None)==(manifest['season']=='20252026'),
                    'real goalie baseline descriptor must exist exactly for final annual')
        for head,record in numerical['heads'].items():
            if record['status'] in ('not_run','not_assessed_for_annual_state'):
                require_fields(record,('status','reason'),'goalie unassessed probe')
                require(type(record['reason']) is str and bool(record['reason']),'missing goalie probe reason')
                require((record['status']=='not_run')==(baseline is not None),'goalie probe annual status differs')
                require(manifest['resources']['probe_solve_counts'][head]==0,'unrun goalie probe claims solve')
                if record['status']=='not_run':
                    require(heads[head]['status']=='unavailable','completed baseline omitted required probe')
                continue
            require_fields(record,('status','reason','baseline','head_path','array_path','comparison'),'goalie probe')
            require(baseline is not None and record['status'] in ('assessed','unassessed')
                    and record['baseline']==dict(path='baseline.json',sha256=by_role['baseline']['sha256'])
                    and manifest['resources']['probe_solve_counts'][head]==1,'goalie probe baseline/count differs')
            expected.add('probe-head:'+head)
            member=by_role.get('probe-head:'+head)
            require(member is not None and record['head_path']==member['path']==f'heads/{head}-tight.json','goalie probe head path differs')
            probe=read_json(root/member['path']); values={}
            if record['array_path'] is not None:
                expected.add('probe-coefficients:'+head)
                member=by_role.get('probe-coefficients:'+head)
                require(member is not None and member['path']==record['array_path']==f'heads/{head}-tight.npz','goalie probe arrays differ')
                values=read_coefficient_arrays(root/member['path'],probe['arrays'])
            _head(probe,head,values,manifest['season'],probe=True)
            require(probe['keys']==heads[head]['keys'] and probe['target_mass']==heads[head]['target_mass']
                    and probe['design']==heads[head]['design']
                    and [{k:v for k,v in r.items() if k!='prior_mean'} for r in probe['priors']]
                    == [{k:v for k,v in r.items() if k!='prior_mean'} for r in heads[head]['priors']],
                    'goalie probe changed design/targets/priors')
            require((record['status']=='assessed')==(probe['status']=='complete')
                    and (record['reason'] is None)==(probe['status']=='complete'),'false goalie probe assessment')
            validate_goalie_probe_comparison(record['comparison'],probe['status']=='complete')
            require(record['comparison']['contexts']==len(baseline['selector']['keys']),
                    'goalie pointwise comparison differs from frozen selector')
        require(set(by_role)==expected,'unknown or missing goalie member roles')
        return GoalieState(path,manifest,heads,arrays,coverage,probes=numerical['heads'])
    except (KeyError,TypeError,ValueError,IndexError,AttributeError) as error:
        if isinstance(error,InputContractError):
            raise
        raise InputContractError(f'malformed goalie state: {error}') from error


def validate_goalie_baseline_descriptor(value,purpose,season,recipe_sha256,base_scores,targets):
    """check a detached descriptor against validated annual targets and identities."""
    require_fields(value,('schema_version','kind','purpose','season','recipe_sha256','base_scores','target_sha256','selector','heads'),'goalie frozen baseline')
    require_finite_state(value,'goalie frozen baseline')
    require(purpose in ('real','fixture') and 2021<=season_start_year(season)<=2025
            and (purpose!='real' or season=='20252026'),'invalid goalie frozen baseline scope')
    require(type(value['schema_version']) is int and value['schema_version']==1
            and value['kind']=='goalie-baseline' and value['purpose']==purpose
            and value['season']==season and value['recipe_sha256']==recipe_sha256
            and value['base_scores']==base_scores and value['target_sha256']==_hash(targets),
            'goalie baseline target/identity differs')
    digest(value['recipe_sha256']); digest(value['target_sha256'])
    require_fields(value['base_scores'],('path','sha256'),'goalie baseline base scores')
    require_state_reference(value['base_scores'],'goalie baseline base scores')
    require(type(value['heads']) is dict and set(value['heads'])==set(HEADS),'baseline head axes differ')
    for row in value['heads'].values():
        require_fields(row,('metadata_sha256','coefficient_sha256','design_sha256','prior_sha256'),'goalie baseline head')
        for key in ('metadata_sha256','design_sha256','prior_sha256'):
            digest(row[key])
        if row['coefficient_sha256'] is not None:
            digest(row['coefficient_sha256'])
    selector=value['selector']; require_fields(selector,('policy','keys','requirements'),'goalie probe selector')
    keys=selector['keys']; known={r['key'] for r in targets}
    require(type(keys) is list and len(keys)<=256 and len(keys)==len(set(keys)) and set(keys)<=known
            and keys==sorted(keys,key=lambda k:(k.split(':')[0],int(k.split(':')[1]))),'invalid goalie frozen keys')
    require(selector['policy']=='deterministic source-key coverage then fill; maximum256; all656 origins per context'
            and type(selector['requirements']) is list,'goalie selector policy differs')
    requirements=[]
    for row in selector['requirements']:
        require_fields(row,('requirement','key'),'goalie selector requirement')
        require(type(row['requirement']) is str and row['requirement'] and (row['key'] is None or row['key'] in keys),
                'goalie selector witness absent')
        requirements.append(row['requirement'])
    require(len(requirements)==len(set(requirements)),'duplicate goalie selector requirement')
    fixed={*('type:'+str(i) for i in range(6)),'tip','missingness','h:false','h:true','d_low','d_high','low_support:h','low_support:d'}
    require(fixed <= set(requirements),'missing fixed goalie selector requirements')
    for name in set(requirements)-fixed:
        parts=name.split(':')
        require(len(parts)==2 and parts[0]=='state','unknown goalie selector requirement')
        axis=parts[1].split(',')
        require(len(axis)==3 and all(s.isascii() and s.isdecimal() and str(int(s))==s for s in axis)
                and int(axis[0]) in (3,4,5,6) and int(axis[1]) in (3,4,5,6) and int(axis[2]) in (0,1),
                'invalid goalie selector strength requirement')



def _baseline(value,manifest,heads,coverage,by_role):
    validate_goalie_baseline_descriptor(value,manifest['purpose'],manifest['season'],manifest['recipe']['sha256'],
                                        manifest['base_scores'],coverage['targets'])
    for head,row in value['heads'].items():
        coefficient=by_role.get('coefficients:'+head)
        require(row==dict(metadata_sha256=by_role['head:'+head]['sha256'],
                          coefficient_sha256=None if coefficient is None else coefficient['sha256'],
                          design_sha256=_hash(heads[head]['design']),prior_sha256=_hash(heads[head]['priors'])),
                'goalie baseline design/prior/coefficients differ')


def validate_goalie_probe_comparison(value,complete):
    """check one frozen-head continuation diagnostic without opening its arrays."""
    base='base_objective base_gradient_max optimizer_maxiter optimizer_ftol optimizer_gtol optimizer_maxfun coefficient_max_change coefficient_l2_change status contexts origin_rows maximum_probability_change maximum_joint_change pointwise_threshold compared_probability_rows compared_joint_rows'.split()
    final='tightened_objective objective_change tightened_gradient_max gradient_max_change'.split()
    require_fields(value,base+(final if complete else []),'goalie probe comparison')
    require(value['optimizer_maxiter']==10000 and value['optimizer_ftol']==1e-16 and value['optimizer_gtol']==1e-7 and value['optimizer_maxfun']==15000
            and value['pointwise_threshold']==1e-5 and type(value['contexts']) is int and 0<=value['contexts']<=256
            and value['origin_rows']==656*value['contexts'] and value['status']==('assessed' if complete else 'unassessed'),
            'goalie probe comparison controls differ')
    for key,count_key in (('maximum_probability_change','compared_probability_rows'),('maximum_joint_change','compared_joint_rows')):
        count=value[count_key]
        require(type(count) is int and 0<=count<=2*value['origin_rows'] and count%656==0,
                'goalie comparison row count differs')
        require((value[key] is None)==(count==0) and (value[key] is None
                or complete and type(value[key]) in (float,int) and 0<=value[key]<=1),
                'goalie comparison movement assessment differs')
        require(complete or count==0,'unfinished probe claims evaluated comparison')
    require(not complete or value['compared_probability_rows']>0,'completed pointwise probe has no comparison rows')
    require_finite_state(value,'goalie probe comparison')


def read_goalie_baseline(state):
    """return the checked frozen descriptor and its explicit contained-file identity."""
    require(isinstance(state,GoalieState) and state.usage=='annual','goalie baseline needs original annual state')
    by_role={row['role']:row for row in state.manifest['files']}
    record=by_role.get('baseline')
    require(record is not None and record['path']=='baseline.json','annual goalie state has no frozen final-year baseline')
    path=state_member_path(state.path.parent,record['path'])
    reference=identity(path)
    require(reference['sha256']==record['sha256'],'goalie baseline member digest differs')
    value=read_json(path)
    _baseline(value,state.manifest,state.heads,state.coverage,by_role)
    return value,reference


def read_goalie_probe(state,head):
    """return a completed diagnostic variant without promoting it to annual state."""
    require(isinstance(state,GoalieState) and head in HEADS,'invalid goalie probe selection')
    record=state.probes[head]
    if record['status']!='assessed':
        return None
    metadata=read_json(state.path.parent/record['head_path'])
    arrays=read_coefficient_arrays(state.path.parent/record['array_path'],metadata['arrays'])
    return replace(state,heads=dict(state.heads,**{head:metadata}),arrays=dict(state.arrays,**{head:arrays}),usage=head+'-tight')


def read_goalie_state(path,expected_purpose):
    """check saved axes/targets/history; provenance paths are not reopened."""
    path=input_path(path, strict=True)
    path=path/'manifest.json' if path.is_dir() else path
    require(path.name=='manifest.json','goalie state locator must be manifest.json')
    return _read_goalie_state(path,read_json(path),expected_purpose)
