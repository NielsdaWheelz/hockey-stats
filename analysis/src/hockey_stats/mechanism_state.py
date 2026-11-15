"""finite annual mechanism artifacts and source-independent projection reads."""
from dataclasses import dataclass, fields
from datetime import date
from pathlib import Path
import math
from time import perf_counter

import numpy as np
from scipy.sparse import csr_matrix

from .artifacts import (digest, ordered_array_digest, require, require_fields, require_number,
    require_season_label, write_arrays, load_arrays, write_json, write_jsonl, rows, json_values, linked_path, implementation)
from .chance_cli import identity, read_json
from .execution_state import require_finite_state, require_state_reference, state_member_path
from .mechanism_design import PenaltyDesign,ShootinessDesign,PENALTY_RECIPE,SHOOTINESS_RECIPE
from .player_mechanisms import (STATES,UNITS,ROLES,body_digest,mechanism_recipe,annual_priors,project_mechanism)

MANIFEST_KEYS='schema_version kind purpose family season recipe design_identity implementation prepared coaches previous training_cutoff head files resources'.split()
HEAD_KEYS='status reasons priors ledger centers reference objective solver diagnostics'.split()
PENALTY_ARRAYS=('context_time','context_event','exposure_hours','event_counts')
SHOOTER_ARRAYS=('choice_offsets','candidate_ids','candidate_roles','choice_states','winner_indices','multiplicities')


@dataclass(frozen=True)
class MechanismState:
    path: Path
    manifest: dict
    head: dict
    design: PenaltyDesign | ShootinessDesign | None
    arrays: dict
    projections: list
    support: list
    reference: dict
    coverage: dict
    probe: dict | None = None


def _binding(value,label,*,nullable=False):
    if value is None:
        require(nullable,f'{label}: missing binding')
        return
    require_state_reference(value,label)


def _validate_inputs(prepared,coaches,purpose,season,family):
    require_fields(prepared,('purpose','path','sha256','members'),'mechanism prepared binding')
    _binding(prepared,'prepared');require(prepared['purpose']==purpose,'mechanism prepared purpose differs')
    keys=[]
    for member in prepared['members']:
        require_fields(member,('kind','season','game_id','path','sha256'),'mechanism prepared member')
        digest(member['sha256'])
        require(member['season']==season and member['kind'] in ('game','people'),'mechanism prepared member year/kind differs')
        keys.append((member['kind'],member['game_id']))
    require(len(keys)==len(set(keys)) and ('people',None) in keys,'mechanism prepared members duplicate/missing')
    if family=='penalties':
        require_fields(coaches,('purpose','path','sha256','selected_game_ids'),'mechanism coach binding')
        _binding(coaches,'coaches')
        require(coaches['purpose']==purpose and coaches['selected_game_ids']==[row['game_id'] for row in prepared['members'] if row['kind']=='game'],
                'mechanism coach purpose/game selection differs')
    else:require(coaches is None,'shootiness coach binding must be null')


def _recipe(family):
    return mechanism_recipe(family,PENALTY_RECIPE if family=='penalties' else SHOOTINESS_RECIPE)


def _design_arrays(design):
    arrays={name:np.asarray(getattr(design,name)) for name in (PENALTY_ARRAYS if design.family=='penalties' else SHOOTER_ARRAYS)}
    if design.family=='penalties':
        for kind in ('time','event'):
            matrix=getattr(design,'X_'+kind)
            for part in ('data','indices','indptr'):arrays[f'X_{kind}_{part}']=getattr(matrix,part)
            arrays[f'X_{kind}_shape']=np.asarray(matrix.shape,dtype=np.int64)
    return arrays


def validate_design(design):
    require(design.purpose in ('real','fixture'),'invalid mechanism design purpose')
    require_season_label(design.season)
    expected=PENALTY_RECIPE if design.family=='penalties' else SHOOTINESS_RECIPE
    require(design.recipe==expected,'mechanism source recipe differs')
    require(tuple(sorted(set(design.players)))==tuple(design.players) and all(type(p) is str and p for p in design.players),
            'mechanism player axis is not sorted unique text')
    require(set(design.player_facts)==set(design.players),'mechanism player facts axis differs')
    require(all(row['position_group'] in ROLES for row in design.player_facts.values()),'invalid mechanism prepared position')
    for name,values in _design_arrays(design).items():
        require(values.dtype.kind in 'iuf' and np.isfinite(values).all(),f'{name}: invalid numeric array')
    require(design.coverage['purpose']==design.purpose and design.coverage['season']==design.season
        and design.coverage['players']==design.coverage['qualification']
        and set(design.coverage['qualification'])==set(design.players),'mechanism coverage identity/roster differs')
    if design.family=='penalties':
        require(design.coaches is not None,'penalty coach source missing')
        require(design.X_time.shape[0]==len(design.exposure_hours)==len(design.time_keys)
            and design.X_event.shape[0]==len(design.event_counts)==len(design.event_keys),'penalty response axes differ')
        for matrix in (design.X_time,design.X_event):
            require(isinstance(matrix,csr_matrix),'penalty actor matrix must be csr')
            matrix.check_format(full_check=True)
            require(matrix.has_canonical_format,'penalty actor csr is not canonical')
        require(design.exposure_hours.ndim==design.event_counts.ndim==1,'penalty response dimensions differ')
        width=design.X_time.shape[1]
        require(design.X_event.shape[1]==width and design.context_time.shape==(len(design.exposure_hours),len(design.columns)-width)
            and design.context_event.shape==(len(design.event_counts),len(design.columns)-width),'penalty feature dimensions differ')
        require(len({c['name'] for c in design.columns})==len(design.columns) and design.columns[0]['kind']=='intercept',
            'penalty column axis differs')
        require(np.all(design.exposure_hours>0) and np.all(design.event_counts>0)
            and np.all(design.event_counts==np.floor(design.event_counts)),'penalty response/hours invalid')
        require(np.all(design.X_time.data>=0) and np.all(design.X_event.data>=0),'negative actor incidence')
        coverage=design.coverage
        require_fields(coverage,('purpose','season','qualification','players','games','physical_included_hours','directed_included_hours','qualified_awards','player_slot_hours'),'penalty coverage')
        require(math.isclose(float(design.exposure_hours.sum()),coverage['physical_included_hours']*2,rel_tol=1e-10,abs_tol=1e-10)
            and math.isclose(float(design.exposure_hours.sum()),coverage['directed_included_hours'],rel_tol=1e-10,abs_tol=1e-10),
            'penalty physical/directed exposure differs')
        require(float(design.event_counts.sum())==coverage['qualified_awards'] and (len(design.exposure_hours)>0 or not len(design.event_counts)),
                'penalty counts lack matching qualified response/exposure')
        require(math.isclose(coverage['player_slot_hours'],sum(r['included_seconds'] for r in coverage['qualification'].values())/3600,rel_tol=1e-10,abs_tol=1e-8)
            and math.isclose(coverage['player_slot_hours'],coverage['physical_included_hours']*10,rel_tol=1e-10,abs_tol=1e-8),
            'penalty actual player slot-time differs')
        for matrix in (design.X_time,design.X_event):
            require(np.array_equal(np.asarray(matrix[:,0].todense()).ravel(),np.ones(matrix.shape[0])),'penalty intercept incidence differs')
            for role in ('attacking_player','defending_player'):
                indices=[i for i,col in enumerate(design.columns[:width]) if col['kind']=='actor' and col['block']==role]
                require(np.all(np.asarray(matrix[:,indices].sum(axis=1)).ravel()==5),'penalty actual player slots differ')
        # the same physical population must support both role histories.
        prior_rows,_,_=annual_priors(design,'penalties',[])
        for prior in prior_rows:
            if prior['block']!='attacking_player':continue
            evidence=design.coverage['qualification'][prior['id']]
            require_fields(evidence,('included_seconds','known_excluded_seconds','unquantified_gap','events','reason_counts'),'penalty qualification')
            require(math.isclose(evidence['included_seconds'],prior['information_weight']*3600,rel_tol=1e-10,abs_tol=1e-8)
                and evidence['events']==prior['likelihood_events'],'penalty source/player likelihood support differs')
    else:
        require(design.coaches is None,'shootiness must not bind coaches')
        count=len(design.multiplicities);candidates=len(design.candidate_ids)
        require(design.choice_offsets.dtype.kind in 'iu' and design.choice_offsets.shape==(count+1,)
            and design.choice_offsets[0]==0 and design.choice_offsets[-1]==candidates
            and np.all(np.diff(design.choice_offsets)>0),'choice offsets do not partition candidates')
        require(design.candidate_roles.shape==(candidates,) and design.choice_states.shape==(count,)
            and design.winner_indices.shape==(count,) and len(design.choice_keys)==count,'choice array axes differ')
        require(all(getattr(design,name).dtype.kind in 'iu' for name in SHOOTER_ARRAYS[:-1]),'noninteger shooter indices')
        require(np.all((design.candidate_ids>=0)&(design.candidate_ids<len(design.players)))
            and np.all((design.candidate_roles>=0)&(design.candidate_roles<3))
            and np.all((design.choice_states>=0)&(design.choice_states<7)),'choice candidate/state index outside axis')
        require(np.all((design.winner_indices>=design.choice_offsets[:-1])&(design.winner_indices<design.choice_offsets[1:])),
            'choice winner outside own unit')
        require(np.all(design.multiplicities>0) and np.all(design.multiplicities==np.floor(design.multiplicities)),
            'invalid choice multiplicities')
        require_fields(design.coverage,('purpose','season','qualification','players','games','included_choices','candidate_incidence','personal_attempts','states'),'shootiness coverage')
        require(int(design.multiplicities.sum())==design.coverage['included_choices']==design.coverage['personal_attempts']
            and int(np.dot(np.diff(design.choice_offsets),design.multiplicities))==design.coverage['candidate_incidence'],
            'shootiness candidate/choice accounting differs')
        expected_roles=np.asarray([ROLES.index(design.player_facts[p]['position_group']) for p in design.players])
        require(np.array_equal(design.candidate_roles,expected_roles[design.candidate_ids]),'candidate role differs from fixed prepared position')
        choice_axis=np.repeat(np.arange(count),np.diff(design.choice_offsets))
        by_state=np.bincount(design.candidate_ids*7+design.choice_states[choice_axis],weights=design.multiplicities[choice_axis],minlength=len(design.players)*7).reshape(-1,7)
        personal=np.bincount(design.candidate_ids[design.winner_indices]*7+design.choice_states,weights=design.multiplicities,minlength=len(design.players)*7).reshape(-1,7)
        for index,player in enumerate(design.players):
            qualification=design.coverage['qualification'][player]
            require_fields(qualification,('states',),'shootiness qualification')
            require_fields(qualification['states'],STATES,'shootiness qualification states')
            for state_index,state in enumerate(STATES):
                evidence=qualification['states'][state]
                require_fields(evidence,('included_seconds','known_excluded_seconds','unquantified_gap','team_choices','personal_attempts','excluded_possible_choices'),'shootiness state qualification')
                require(evidence['team_choices']==by_state[index,state_index] and evidence['personal_attempts']==personal[index,state_index],
                        'shootiness source/candidate response support differs')
        for start,end in zip(design.choice_offsets[:-1],design.choice_offsets[1:],strict=True):
            require(len(set(design.candidate_ids[start:end]))==end-start,'duplicate candidate in one unit')
    for name in ('prepared','coaches'):_binding(getattr(design,name),name,nullable=name=='coaches' and design.family=='shootiness')


def _write_design(root,design):
    arrays=_design_arrays(design)
    archive=write_arrays(root,'arrays.npz',arrays)
    excluded=set(arrays)|{'X_time','X_event','resources'}
    values={field.name:json_values(getattr(design,field.name)) for field in fields(design) if field.name not in excluded}
    axes=dict(players=list(design.players),states=list(STATES),roles=list(ROLES))
    if design.family=='penalties':
        axes.update(columns=values['columns'],time_rows=values['time_keys'],event_rows=values['event_keys'],
                    context_columns=values['columns'][design.X_time.shape[1]:])
    else:axes.update(choices=values['choice_keys'],candidates='choice_offsets partition candidate_ids; winner_indices are global candidate indices')
    document=dict(schema_version=1,family=design.family,metadata=values,axes=axes,arrays=archive,
                  numerical_identity=ordered_array_digest(arrays))
    write_json(root/'design.json',document)
    return body_digest(document)


def _read_design(root,expected_identity):
    document=read_json(root/'design.json')
    require_fields(document,('schema_version','family','metadata','axes','arrays','numerical_identity'),'mechanism design')
    require(document['schema_version']==1 and document['family'] in ('penalties','shootiness'),'invalid mechanism design schema/family')
    require(body_digest(document)==expected_identity,'mechanism design identity differs')
    archive=document['arrays'];require_fields(archive,('arrays','array_shapes'),'mechanism array contract')
    require(archive['arrays']==identity(root/'arrays.npz'),'mechanism design array binding differs from owned member')
    for shape in archive['array_shapes']:require_fields(shape,('name','shape','dtype'),'mechanism saved array shape')
    arrays=load_arrays(archive)
    require(ordered_array_digest(arrays)==document['numerical_identity'],'mechanism numerical identity differs')
    values=document['metadata']
    constructor=PenaltyDesign if document['family']=='penalties' else ShootinessDesign
    excluded=set(PENALTY_ARRAYS if document['family']=='penalties' else SHOOTER_ARRAYS)|{'X_time','X_event','resources'}
    require_fields(values,[f.name for f in fields(constructor) if f.name not in excluded],'mechanism design metadata')
    restored=dict(values)
    for name in ('players','coach_ids','columns','time_keys','event_keys','choice_keys'):
        if name in restored:restored[name]=tuple(restored[name])
    for name in (PENALTY_ARRAYS if document['family']=='penalties' else SHOOTER_ARRAYS):restored[name]=arrays[name]
    if document['family']=='penalties':
        for kind in ('time','event'):
            prefix='X_'+kind
            restored[prefix]=csr_matrix((arrays[prefix+'_data'],arrays[prefix+'_indices'],arrays[prefix+'_indptr']),shape=tuple(arrays[prefix+'_shape']))
    design=constructor(**restored)
    axes=dict(players=list(design.players),states=list(STATES),roles=list(ROLES))
    if design.family=='penalties':
        axes.update(columns=values['columns'],time_rows=values['time_keys'],event_rows=values['event_keys'],context_columns=values['columns'][design.X_time.shape[1]:])
    else:axes.update(choices=values['choice_keys'],candidates='choice_offsets partition candidate_ids; winner_indices are global candidate indices')
    require(document['axes']==axes,'mechanism explicit array axes differ')
    require(list(arrays)==list(_design_arrays(design)),'mechanism design array inventory differs')
    validate_design(design)
    return design


def _member(root,name,role):
    path=root/name
    binding=identity(path)
    return dict(role=role,path=name,sha256=binding['sha256'],bytes=path.stat().st_size)


def write_mechanism_state(root,design,family,previous,head,arrays,projections,support,reference,probe,resources):
    validate_design(design)
    began=perf_counter()
    root=root.resolve();root.mkdir(parents=True,exist_ok=False)
    design_identity=_write_design(root,design)
    write_json(root/'head.json',head)
    if arrays:write_arrays(root,'coefficients.npz',arrays)
    write_jsonl(root/'projections.jsonl',projections)
    write_jsonl(root/'support.jsonl',support)
    write_json(root/'reference.json',reference)
    write_json(root/'coverage.json',design.coverage)
    if probe is not None:
        probe_doc={key:json_values(value) for key,value in probe.items() if key!='arrays'}
        write_json(root/'probe.json',probe_doc)
        if probe['arrays']:write_arrays(root,'probe-coefficients.npz',probe['arrays'])
    names=[('design.json','design'),('arrays.npz','design_arrays'),('head.json','head'),('projections.jsonl','projections'),
        ('support.jsonl','support'),('reference.json','reference'),('coverage.json','coverage')]
    if arrays:names.append(('coefficients.npz','coefficients'))
    if probe is not None:
        names.append(('probe.json','probe'))
        if probe['arrays']:names.append(('probe-coefficients.npz','probe_coefficients'))
    predecessor=None if previous is None else dict(**identity(previous.path/'manifest.json'),season=previous.manifest['season'],
        purpose=previous.manifest['purpose'],family=family,recipe_sha256=previous.manifest['recipe']['sha256'])
    manifest=dict(schema_version=1,kind='player_mechanism_state',purpose=design.purpose,family=family,season=design.season,
        recipe=_recipe(family),design_identity=design_identity,implementation=implementation(),prepared=design.prepared,
        coaches=design.coaches,previous=predecessor,training_cutoff=design.training_cutoff,head=dict(status=head['status'],path='head.json'),
        files=[_member(root,name,role) for name,role in names],resources=resources)
    manifest['resources']=dict(resources,output_bytes=sum(item['bytes'] for item in manifest['files']),write_wall_seconds=perf_counter()-began)
    write_json(root/'manifest.json',manifest)
    return read_mechanism_state(root,design.purpose,family)


def _validate_head(head,manifest):
    require_fields(head,HEAD_KEYS,'mechanism head')
    require(head['status'] in ('complete','failed','unavailable') and head['status']==manifest['head']['status'],'mechanism head status differs')
    require(type(head['reasons']) is list and all(type(v) is str and v for v in head['reasons']), 'invalid mechanism head reasons')
    require((not head['reasons'])==(head['status']=='complete'),'mechanism head reasons/status differ')
    require(type(head['priors']) is list and type(head['ledger']) is list,'invalid mechanism annual history')
    blocks=('attacking_player','defending_player','attacking_coach','defending_coach') if manifest['family']=='penalties' else ('shooter_player',)
    subblocks=('base','score:-2','score:-1','score:0','score:1','score:2','shell')
    ledger_keys=set()
    for row in head['ledger']:
        require_fields(row,('block','id','subblock','coefficient','season','support_seasons'),'mechanism ledger row')
        require(row['block'] in blocks and type(row['id']) is str and row['id'] and row['subblock'] in subblocks
            and (not row['block'].endswith('_player') or row['subblock']=='base'),'invalid mechanism ledger actor')
        key=(row['block'],row['id'],row['subblock']);require(key not in ledger_keys,'duplicate mechanism ledger actor');ledger_keys.add(key)
        require_number(row['coefficient'],'mechanism carried coefficient')
        require_season_label(row['season'])
        years=row['support_seasons']
        for year in years:require_season_label(year)
        require(type(years) is list and years==sorted(set(years)) and years and years[-1]==row['season']
            and all(year<=manifest['season'] for year in years),'mechanism ledger chronology differs')
    require(len({r['index'] for r in head['priors']})==len(head['priors'])
        and len({(r['block'],r['id'],r['subblock']) for r in head['priors']})==len(head['priors']),'duplicate mechanism prior actor/index')
    for row in head['priors']:
        require_fields(row,('index','block','id','subblock','information_weight','likelihood_events','current_season_information',
            'prior_only','prior_kind','prior_anchor_season','prior_seasons','mean','precision'),'mechanism actor prior')
        require(type(row['index']) is int and 0<=row['index']<manifest['resources']['coordinates']
            and row['block'] in blocks and type(row['id']) is str and row['id'] and row['subblock'] in subblocks
            and (not row['block'].endswith('_player') or row['subblock']=='base'),'invalid mechanism prior actor/index')
        require_number(row['information_weight'],'mechanism prior weight',low=0)
        require(type(row['likelihood_events']) is int and row['likelihood_events']>=0,'invalid mechanism prior events')
        require(type(row['current_season_information']) is bool and type(row['prior_only']) is bool,'invalid mechanism prior flag types')
        require(row['current_season_information']==(row['information_weight']>0 or row['likelihood_events']>0)
            and row['prior_only']==(not row['current_season_information']),'mechanism prior information flags differ')
        for year in row['prior_seasons']:require_season_label(year)
        require(row['prior_kind'] in ('entry','carry') and row['prior_seasons']==sorted(set(row['prior_seasons']))
            and all(year<manifest['season'] for year in row['prior_seasons']),'mechanism prior years differ')
        require((row['prior_anchor_season'] is None and not row['prior_seasons']) if row['prior_kind']=='entry' else (
            row['prior_seasons'] and row['prior_anchor_season']==row['prior_seasons'][-1]),'mechanism prior anchor differs')
        require_number(row['mean'],'mechanism prior mean');require_number(row['precision'],'mechanism precision',low=0)
        require(row['precision']>0,'mechanism precision must be positive')
    if head['solver'] is not None:
        solver=head['solver']
        require_fields(solver,('converged','status','termination','iterations','evaluations','objective','options','gradient_inf_norm',
            'achieved_gtol','wall_seconds','peak_memory_bytes'),'mechanism solver')
        require(type(solver['converged']) is bool and type(solver['achieved_gtol']) is bool and type(solver['status']) is int
            and type(solver['termination']) is str and solver['termination'],'mechanism native solver fields differ')
        for key in ('iterations','evaluations'):
            require(type(solver[key]) is int and solver[key]>=0,'invalid mechanism native solver count')
        for key in ('gradient_inf_norm','wall_seconds','peak_memory_bytes'):require_number(solver[key],'mechanism solver scalar',low=0)
        require_number(solver['objective'],'mechanism solver objective')
        from .player_mechanisms import SOLVER,CONTINUATION
        require(solver['options'] in (SOLVER,CONTINUATION),'mechanism solver tolerances differ')
        require(solver['achieved_gtol']==(solver['gradient_inf_norm']<=solver['options']['gtol']), 'mechanism achieved tolerance differs')
    if head['objective'] is not None:
        require_fields(head['objective'],('penalized_loss','gradient_inf_norm'),'mechanism objective')
        require_number(head['objective']['penalized_loss'],'mechanism objective loss')
        require_number(head['objective']['gradient_inf_norm'],'mechanism objective gradient',low=0)
    if head['diagnostics'] is not None:
        diagnostic=head['diagnostics']
        require(diagnostic['kind']=='in_sample_not_held_out','mechanism diagnostic interpretation differs')
        if manifest['family']=='penalties':
            require_fields(diagnostic,('kind','expected_awards','observed_awards'),'penalty in-sample diagnostics')
            for key in ('expected_awards','observed_awards'):require_number(diagnostic[key],'penalty diagnostic total',low=0)
        else:
            require_fields(diagnostic,('kind','choices','states'),'shootiness in-sample diagnostics')
            require(type(diagnostic['choices']) is int and diagnostic['choices']>=0
                and [r['strength'] for r in diagnostic['states']]==list(STATES),'shootiness diagnostic state axis differs')
            for row in diagnostic['states']:
                require_fields(row,('strength','expected_by_role','observed_by_role'),'shootiness state diagnostics')
                require(len(row['expected_by_role'])==len(row['observed_by_role'])==3,'shootiness diagnostic role axis differs')
                for key in ('expected_by_role','observed_by_role'):
                    for scalar in row[key]:require_number(scalar,'shootiness role diagnostic',low=0)
    if head['status']=='complete':
        require(type(head['solver']) is dict and head['solver']['converged'] is True and head['centers'] is not None
            and head['reference'] is not None and head['objective'] is not None,'completed mechanism head lacks numerical proof')
    else:require(head['centers'] is None,'incomplete mechanism head has centers')


def _validate_projection_evidence(manifest,head,reference,projections,support):
    require(type(reference) is dict and 'sha256' in reference,'missing mechanism reference digest')
    digest(reference['sha256']);require(body_digest({k:v for k,v in reference.items() if k!='sha256'})==reference['sha256'],'mechanism reference digest differs')
    require(reference['season']==manifest['season'] and reference==head['reference'],'mechanism reference year/head differs')
    complete=head['status']=='complete';family=manifest['family']
    if complete and family=='penalties':
        require_fields(reference,('kind','units','neutral_per60','log_rate','neutral_predictor','player_slots_per_role','context','season','sha256'),'penalty reference')
        for key in ('neutral_per60','log_rate','neutral_predictor'):require_number(reference[key],'penalty reference scalar')
        require(type(reference['player_slots_per_role']) is int,'penalty reference slot type differs')
        require(reference['kind']=='ordinary-minor-team-award-intensity' and reference['units']=='awards_per_hour'
            and reference['player_slots_per_role']==5 and math.isclose(reference['neutral_per60'],math.exp(reference['neutral_predictor']),rel_tol=1e-12,abs_tol=0),
            'penalty neutral reference differs')
    elif complete:
        require_fields(reference,('kind','units','states','roles','reference_units','role_offsets','context','season','sha256'),'shootiness reference')
        require(reference['kind']=='conditional-shooter-choice' and reference['units']=='fraction'
            and reference['states']==list(STATES) and reference['roles']==list(ROLES)
            and reference['reference_units']==[dict(strength=s,forwards=u[0],defenders=u[1]) for s,u in zip(STATES,UNITS,strict=True)]
            and np.asarray(reference['role_offsets']).shape==(7,3),'shootiness reference axes differ')
        for offsets in reference['role_offsets']:
            for offset in offsets:require_number(offset,'shootiness reporting offset')
        for unit in reference['reference_units']:
            require_fields(unit,('strength','forwards','defenders'),'shootiness reference unit')
            require(type(unit['forwards']) is int and type(unit['defenders']) is int,'shootiness reference slot types differ')
    else:
        require_fields(reference,('kind','family','units','season','sha256'),'unavailable mechanism reference')
        require(reference['kind']=='unavailable' and reference['family']==family,'unavailable mechanism reference family differs')
    players=[row['player_id'] for row in support]
    require(players==sorted(set(players)),'mechanism support player axis differs')
    prior_by_role={(r['block'],r['id']):r for r in head['priors'] if r['subblock']=='base'}
    for row in support:
        require_fields(row,('player_id','coefficient_support','included_seconds','known_excluded_seconds','unquantified_gap','states'),'mechanism support')
        coefficient=row['coefficient_support']
        require_fields(coefficient,('status','current_season_information','prior_only','prior_kind','prior_anchor_season','prior_seasons',
            'likelihood_events','information_weight'),'mechanism coefficient support')
        prior=prior_by_role.get(('attacking_player' if family=='penalties' else 'shooter_player',row['player_id']))
        require(prior is not None,'mechanism support has no matching annual prior')
        expected_coefficient=dict(status=head['status'],current_season_information=prior['current_season_information'],
            prior_only=prior['prior_only'] if complete else False,prior_kind=prior['prior_kind'] if complete else None,
            prior_anchor_season=prior['prior_anchor_season'] if complete else None,prior_seasons=prior['prior_seasons'] if complete else [],
            likelihood_events=prior['likelihood_events'],information_weight=prior['information_weight'])
        require(coefficient==expected_coefficient and all(type(coefficient[k]) is bool for k in ('current_season_information','prior_only')),
                'mechanism support differs from annual prior/status')
        if family=='penalties':
            other=prior_by_role.get(('defending_player',row['player_id']))
            require(other is not None and all(other[k]==prior[k] for k in ('information_weight','likelihood_events','current_season_information',
                'prior_only','prior_kind','prior_anchor_season','prior_seasons')),'penalty role histories differ')
        for key in ('included_seconds','known_excluded_seconds'):require_number(row[key],'mechanism support seconds',low=0)
        require(type(row['unquantified_gap']) is bool,'invalid mechanism gap flag')
        require_number(coefficient['information_weight'],'mechanism information weight',low=0)
        require(type(coefficient['likelihood_events']) is int and coefficient['likelihood_events']>=0,'invalid mechanism likelihood events')
        if family=='shootiness':
            require([r['strength'] for r in row['states']]==list(STATES),'shootiness qualification state axis differs')
            for state in row['states']:
                require_fields(state,('strength','included_seconds','known_excluded_seconds','unquantified_gap','team_choices','personal_attempts','excluded_possible_choices'),
                    'shootiness exact-state support')
                for key in ('included_seconds','known_excluded_seconds'):require_number(state[key],'shootiness seconds',low=0)
                for key in ('team_choices','personal_attempts','excluded_possible_choices'):
                    require(type(state[key]) is int and state[key]>=0,'invalid shootiness count')
                require(type(state['unquantified_gap']) is bool and state['personal_attempts']<=state['team_choices'],'personal attempts exceed team choices or invalid gap')
            events=sum(r['team_choices'] for r in row['states'])
            require(coefficient['likelihood_events']==events and coefficient['information_weight']==events,'shootiness pooled support differs')
        else:
            require(not row['states'] and math.isclose(row['included_seconds'],coefficient['information_weight']*3600,rel_tol=1e-10,abs_tol=1e-8),
                    'penalty physical support differs')
    expected=[(p,s) for p in players for s in STATES] if family=='shootiness' else [(p,None) for p in players]
    require([(r['player_id'],r.get('strength')) for r in projections]==expected,'mechanism projection key inventory differs')
    for row in projections:
        require(row['season']==manifest['season'] and row['reference_id']==reference['sha256'],'mechanism projection reference/year differs')
        if family=='penalties':
            require_fields(row,('player_id','season','drawn_per60','taken_per60','drawn_complete_per60','taken_complete_per60','neutral_per60','reference_id'),
                'penalty projection')
            for key in ('drawn_per60','taken_per60','drawn_complete_per60','taken_complete_per60','neutral_per60'):
                if row[key] is not None:require_number(row[key],'penalty projection scalar')
                require((row[key] is not None)==complete,'penalty projection availability differs')
            if complete:
                require(row['neutral_per60']==reference['neutral_per60'] and min(row['neutral_per60'],row['drawn_complete_per60'],row['taken_complete_per60'])>0,
                    'invalid penalty complete intensity')
                for role in ('drawn','taken'):
                    require(math.isclose(row[role+'_per60'],row[role+'_complete_per60']-row['neutral_per60'],rel_tol=1e-10,abs_tol=1e-10),
                        'penalty complete-minus-neutral differs')
        else:
            require_fields(row,('player_id','season','strength','position_group','probability','neutral_probability','difference','reference_unit','reference_id'),
                'shootiness projection')
            require(row['position_group'] in ROLES and row['reference_unit']==dict(zip(('forwards','defenders'),UNITS[STATES.index(row['strength'])],strict=True)),
                'shootiness reference unit/position differs')
            require_fields(row['reference_unit'],('forwards','defenders'),'shootiness projection unit')
            require(all(type(v) is int for v in row['reference_unit'].values()),'shootiness unit count types differ')
            for key in ('probability','neutral_probability','difference'):
                if row[key] is not None:require_number(row[key],'shootiness projection scalar')
            available=complete and row['position_group']!='unknown'
            require(all((row[key] is not None)==available for key in ('probability','neutral_probability','difference')),'shootiness probability availability differs')
            if available:
                require(0<=row['probability']<=1 and 0<=row['neutral_probability']<=1
                    and math.isclose(row['difference'],row['probability']-row['neutral_probability'],rel_tol=1e-10,abs_tol=1e-10),
                    'shootiness probability closure differs')


def _read_mechanism_state(path,purpose,family,*,narrow=False):
    root=Path(path).resolve(strict=True)
    if root.is_file():require(root.name=='manifest.json','expected mechanism manifest');root=root.parent
    manifest=read_json(root/'manifest.json');require_fields(manifest,MANIFEST_KEYS,'mechanism manifest')
    require_finite_state(manifest,'mechanism manifest')
    require(type(manifest['schema_version']) is int and manifest['schema_version']==1 and manifest['kind']=='player_mechanism_state'
        and manifest['purpose']==purpose and purpose in ('real','fixture') and manifest['family']==family
        and family in ('penalties','shootiness'),'mechanism schema/purpose/family differs')
    require_season_label(manifest['season']);require(manifest['recipe']==_recipe(family),'mechanism recipe differs');digest(manifest['design_identity'])
    _validate_inputs(manifest['prepared'],manifest['coaches'],purpose,manifest['season'],family)
    require((manifest['coaches'] is None)==(family=='shootiness'),'mechanism coach family contract differs')
    require(manifest['training_cutoff'] is None or type(manifest['training_cutoff']) is str and int(manifest['season'][:4])<=date.fromisoformat(manifest['training_cutoff']).year<=int(manifest['season'][4:]),'mechanism training cutoff differs')
    previous=manifest['previous']
    if previous is not None:
        require_fields(previous,('path','sha256','season','purpose','family','recipe_sha256'),'mechanism predecessor')
        _binding(previous,'predecessor')
        require(previous['season']==f'{int(manifest["season"][:4])-1}{manifest["season"][:4]}' and previous['purpose']==purpose
            and previous['family']==family and previous['recipe_sha256']==manifest['recipe']['sha256'],'mechanism predecessor chronology/family differs')
    else:require(purpose!='real' or manifest['season']=='20212022','real mechanism predecessor missing')
    require_fields(manifest['resources'],('wall_seconds','peak_memory_bytes','coordinates','baseline_solves','diagnostic_solves','preparation','wall_scope','output_bytes','write_wall_seconds'),'mechanism resources')
    for key in ('wall_seconds','peak_memory_bytes','coordinates','baseline_solves','diagnostic_solves','output_bytes','write_wall_seconds'):
        require_number(manifest['resources'][key],'mechanism resource',low=0)
    require_fields(manifest['implementation'],('git_commit','git_dirty','python_version','numpy_version','scipy_version','lockfile_sha256'),'mechanism implementation')
    digest(manifest['implementation']['lockfile_sha256'])
    require_fields(manifest['head'],('status','path'),'mechanism head descriptor');require(manifest['head']['path']=='head.json','mechanism head path differs')
    members={}
    for item in manifest['files']:
        require_fields(item,('role','path','sha256','bytes'),'mechanism member');digest(item['sha256'])
        require(item['path'] not in members and type(item['bytes']) is int and item['bytes']>=0,'duplicate/invalid mechanism member')
        members[item['path']]=item
    roles={'design.json':'design','arrays.npz':'design_arrays','head.json':'head','projections.jsonl':'projections','support.jsonl':'support','reference.json':'reference','coverage.json':'coverage','coefficients.npz':'coefficients','probe.json':'probe','probe-coefficients.npz':'probe_coefficients'}
    require(all(name in roles and item['role']==roles[name] for name,item in members.items()),'mechanism member role/path differs')
    expected={'design.json','arrays.npz','head.json','projections.jsonl','support.jsonl','reference.json','coverage.json'}
    if manifest['head']['status']=='complete':expected.add('coefficients.npz')
    if 'probe.json' in members:expected.add('probe.json')
    if 'probe-coefficients.npz' in members:
        require('probe.json' in members,'orphan mechanism probe coefficients');expected.add('probe-coefficients.npz')
    if purpose=='real':require(('probe.json' in members)==(manifest['season']=='20252026'),'real mechanism diagnostic year differs')
    require(set(members)==expected,'mechanism member inventory differs')
    consume=({'head.json','projections.jsonl','support.jsonl','reference.json','coverage.json'} | ({'probe.json'} if 'probe.json' in members else set())) if narrow else expected
    for name in consume:
        path=state_member_path(root,name);item=members[name]
        require(path.stat().st_size==item['bytes'] and identity(path)['sha256']==item['sha256'],'mechanism member digest/bytes differ')
    head=read_json(root/'head.json');_validate_head(head,manifest)
    reference=read_json(root/'reference.json');projections=list(rows(root/'projections.jsonl'));support=list(rows(root/'support.jsonl'));coverage=read_json(root/'coverage.json')
    for value in (head,reference,projections,support,coverage):require_finite_state(value,'mechanism saved evidence')
    _validate_projection_evidence(manifest,head,reference,projections,support)
    design=None;arrays={};probe=None
    if not narrow:
        design=_read_design(root,manifest['design_identity'])
        require(design.family==family and design.purpose==purpose and design.season==manifest['season']
            and design.prepared==manifest['prepared'] and design.coaches==manifest['coaches'] and design.coverage==coverage,
            'mechanism design/manifest identity differs')
        if head['status']=='complete':
            with np.load(root/'coefficients.npz',allow_pickle=False) as archive:
                require(archive.files==['coefficients'],'mechanism coefficient axes differ');arrays={'coefficients':archive['coefficients']}
            width=len(design.columns) if family=='penalties' else len(design.players)+14
            require(arrays['coefficients'].shape==(width,) and arrays['coefficients'].dtype==np.dtype('float64')
                and np.isfinite(arrays['coefficients']).all(),'mechanism coefficient array differs')
            for prior in head['priors']:
                ledger={(r['block'],r['id'],r['subblock']):r for r in head['ledger']}
                carried=ledger.get((prior['block'],prior['id'],prior['subblock']))
                if prior['current_season_information']:
                    require(carried is not None and carried['season']==manifest['season']
                        and carried['support_seasons']==prior['prior_seasons']+[manifest['season']]
                        and carried['coefficient']==float(arrays['coefficients'][prior['index']]),'mechanism raw coefficient ledger differs')
                else:
                    require(float(arrays['coefficients'][prior['index']])==prior['mean'],'uninformed actor is not at conditional prior mean')
                    require((carried is None) if prior['prior_kind']=='entry' else carried is not None
                        and carried['season']==prior['prior_anchor_season'] and carried['support_seasons']==prior['prior_seasons']
                        and carried['coefficient']==prior['mean'],'mechanism uninformed actor refreshes history')
            saved=project_mechanism(design,family,head,arrays['coefficients'])
            require(saved[0]==projections and saved[1]==support and saved[2]==reference and saved[3]==head['centers'],
                    'mechanism coefficients do not reproduce saved projections/reference/support')
    if 'probe.json' in members:
        probe=read_json(root/'probe.json');require_fields(probe,('head','projections','reference','comparison'),'mechanism probe')
        require_finite_state(probe,'mechanism probe')
        require(type(probe['comparison']) is dict and probe['comparison']['status'] in ('within_budget','exceeded','unassessed'),
                'invalid mechanism diagnostic verdict')
        if probe['head'] is None:
            require('probe-coefficients.npz' not in members and not probe['projections'] and probe['reference'] is None and probe['comparison']['status']=='unassessed',
                    'absent mechanism probe claims results')
        else:
            descriptor=dict(manifest,head=dict(status=probe['head']['status'],path='head.json'))
            _validate_head(probe['head'],descriptor)
            if probe['head']['status']=='complete':
                require('probe-coefficients.npz' in members and len(probe['projections'])==len(projections)
                    and probe['reference']==probe['head']['reference'],'completed mechanism probe lacks saved results')
                _validate_projection_evidence(descriptor,probe['head'],probe['reference'],probe['projections'],support)
            else:require('probe-coefficients.npz' not in members and not probe['projections'],'failed probe has completed coefficients/results')
        if not narrow and 'probe-coefficients.npz' in members:
            with np.load(root/'probe-coefficients.npz',allow_pickle=False) as archive:
                require(archive.files==['coefficients'],'mechanism probe arrays differ');probe['arrays']={'coefficients':archive['coefficients']}
            require(probe['arrays']['coefficients'].shape==arrays['coefficients'].shape
                and probe['arrays']['coefficients'].dtype==np.dtype('float64')
                and np.isfinite(probe['arrays']['coefficients']).all(),'mechanism probe coefficient contract differs')
            projected=project_mechanism(design,family,probe['head'],probe['arrays']['coefficients'])
            require(projected[0]==probe['projections'] and projected[2]==probe['reference'] and projected[3]==probe['head']['centers'],
                    'mechanism probe coefficients do not reproduce projections/reference')
            from .player_mechanisms import compare_mechanism_probe
            comparison=compare_mechanism_probe(design,family,dict(status=head['status'],head=head,arrays=arrays),
                dict(status=probe['head']['status'],head=probe['head'],arrays=probe['arrays']),projections,probe['projections'])
            require(comparison==probe['comparison'],'mechanism probe movement/verdict differs')
    return MechanismState(root,manifest,head,design,arrays,projections,support,reference,coverage,probe)


def _validate_history_chain(state,previous):
    incoming={} if previous is None else {(r['block'],r['id'],r['subblock']):r for r in previous.head['ledger']}
    outgoing={(r['block'],r['id'],r['subblock']):r for r in state.head['ledger']}
    expected=dict(incoming)
    for prior in state.head['priors']:
        key=(prior['block'],prior['id'],prior['subblock']);last=incoming.get(key)
        require(prior['prior_kind']==('entry' if last is None else 'carry') and prior['mean']==(0. if last is None else last['coefficient'])
            and prior['prior_anchor_season']==(None if last is None else last['season'])
            and prior['prior_seasons']==([] if last is None else last['support_seasons']), 'mechanism selected raw prior anchor differs')
        player=prior['block'].endswith('_player')
        entry,carry=((.5,.2) if state.manifest['family']=='shootiness' else (.25,.1) if player else (.1,.05))
        gap=None if last is None else int(state.manifest['season'][:4])-int(last['season'][:4])
        precision=1/entry**2 if gap is None else 1/(carry**2*gap)
        require(prior['precision']==precision,'mechanism selected entry/carry precision differs')
        if state.head['status']=='complete' and prior['current_season_information']:
            require(key in outgoing,'mechanism completed supported actor missing from history')
            row=outgoing[key]
            require(row['season']==state.manifest['season'] and row['support_seasons']==prior['prior_seasons']+[state.manifest['season']],
                    'mechanism selected supported chronology differs')
            expected[key]=row
    require(outgoing==expected,'mechanism selected ledger lost/refreshed unsupported incoming history')


def _read_mechanism_selection(path,purpose):
    selection=read_json(Path(path))
    require_fields(selection,('schema_version','purpose','prepared','coaches','source_results','execution_scores','years'),'mechanism selection')
    require_finite_state(selection,'mechanism selection')
    require(selection['schema_version']==1 and selection['purpose']==purpose and purpose in ('real','fixture'),'mechanism selection schema/purpose differs')
    for key in ('prepared','coaches','source_results','execution_scores'):
        require_fields(selection[key],('path','sha256'),'mechanism selection binding');linked_path(selection[key])
    years=selection['years'];require(type(years) is list and years,'mechanism selection years missing')
    labels=[r['season'] for r in years]
    for label in labels:require_season_label(label)
    require(labels==sorted(set(labels)) and all(int(b[:4])-int(a[:4])==1 for a,b in zip(labels,labels[1:])),
            'mechanism selection years are not consecutive')
    require(purpose!='real' or labels==['20212022','20222023','20232024','20242025','20252026'],'real mechanism selection needs all five years')
    score_selection=read_json(linked_path(selection['execution_scores']))
    require_fields(score_selection,('schema_version','purpose','prepared_sha256','scores'),'mechanism execution score selection')
    require(score_selection['schema_version']==1 and score_selection['purpose']==purpose
        and score_selection['prepared_sha256']==selection['prepared']['sha256'],'mechanism score selection lineage differs')
    require([r['season'] for r in score_selection['scores']]==labels,'mechanism score selection years differ')
    for item,score in zip(years,score_selection['scores'],strict=True):
        require_fields(score,('season','path','sha256'),'mechanism score selection annual')
        require(item['execution_score']=={k:score[k] for k in ('path','sha256')},'mechanism annual score differs from selected chain')
    previous={'penalties':None,'shootiness':None};prior_states={'penalties':None,'shootiness':None}
    for row in years:
        require_fields(row,('season','penalties','shootiness','execution_score','ev_state','st_state','minor_reference'),'mechanism selection year')
        for key in ('penalties','shootiness','execution_score','ev_state','st_state','minor_reference'):
            if key=='minor_reference' and row[key] is None:continue
            require_fields(row[key],('path','sha256'),'mechanism selected annual binding');linked_path(row[key])
        for family in ('penalties','shootiness'):
            state=read_mechanism_state(row[family]['path'],purpose,family,narrow=True)
            require(state.manifest['season']==row['season'],'mechanism selected state year differs')
            require({k:state.manifest['prepared'][k] for k in ('path','sha256')}==selection['prepared']
                and (family=='shootiness' or {k:state.manifest['coaches'][k] for k in ('path','sha256')}==selection['coaches']),
                'mechanism selected source lineage differs')
            _validate_history_chain(state,prior_states[family])
            prior_states[family]=state
            actual=state.manifest['previous']
            require((actual is None)==(previous[family] is None),'mechanism selected predecessor presence differs')
            if actual is not None:
                require({k:actual[k] for k in ('path','sha256')}==previous[family],'mechanism selection is not exact predecessor chain')
            previous[family]=row[family]
    return selection


def _read_minor_reference(path,purpose,season,*,expected_inputs=None):
    """validate a saved valuation and its separate matched-source receipt."""
    from .player_mechanisms import minor_value
    path=Path(path).resolve(strict=True)
    value=read_json(path)
    require_fields(value,('schema_version','kind','purpose','season','valuation','construction','reference_id'),'minor reference')
    require_finite_state(value,'minor reference')
    require(value['schema_version']==1 and value['kind']=='isolated_minor_reference' and value['purpose']==purpose
        and value['season']==season,'minor reference identity differs')
    require_season_label(season);digest(value['reference_id'])
    require(body_digest({k:v for k,v in value.items() if k!='reference_id'})==value['reference_id'],'minor reference digest differs')
    valuation=value['valuation']
    require_fields(valuation,('available','reason','a','b','e_f','e_a','T_hours','tau_hours','V_goals','sh_support','inputs'),'minor valuation')
    require(type(valuation['available']) is bool and valuation['T_hours']==2/60,'invalid minor availability/duration')
    require_fields(valuation['inputs'],('ev_state','st_state','execution_score','reduction'),'minor inputs')
    for key,binding in valuation['inputs'].items():
        require_fields(binding,('uri','sha256'),'minor evidence binding')
        _binding(dict(path=binding['uri'],sha256=binding['sha256']),key)
    reduction=valuation['inputs']['reduction']
    reduction_path=linked_path(dict(path=reduction['uri'],sha256=reduction['sha256']))
    receipt=read_json(reduction_path)
    require_fields(receipt,('schema_version','kind','purpose','season','inputs','sh_support','games','construction'),'minor reduction receipt')
    require_finite_state(receipt,'minor reduction receipt')
    require(receipt['schema_version']==1 and receipt['kind']=='shorthanded_neutral_reduction' and receipt['purpose']==purpose
        and receipt['season']==season and receipt['sh_support']==valuation['sh_support'],'minor reduction identity/support differs')
    require_fields(receipt['inputs'],('prepared','execution_score','ev_state','st_state'),'minor reduction source identities')
    for key,binding in receipt['inputs'].items():
        require_fields(binding,('path','sha256'),'minor reduction source');_binding(binding,key)
    for key in ('execution_score','ev_state','st_state'):
        require(receipt['inputs'][key]==dict(path=valuation['inputs'][key]['uri'],sha256=valuation['inputs'][key]['sha256']),
                'minor reference/reduction lineage differs')
    if expected_inputs is not None:require(receipt['inputs']==expected_inputs,'minor reduction selected source lineage differs')
    support=valuation['sh_support']
    require_fields(support,('included_seconds','attempts','neutral_goal_mass','known_excluded_seconds','unquantified_gap'),'minor sh support')
    for key in ('included_seconds','neutral_goal_mass','known_excluded_seconds'):require_number(support[key],'minor support',low=0)
    require(type(support['attempts']) is int and support['attempts']>=0 and type(support['unquantified_gap']) is bool
        and support['neutral_goal_mass']<=support['attempts'],'invalid minor source counts/mass')
    require(type(receipt['games']) is list and len({r['game_id'] for r in receipt['games']})==len(receipt['games']),'minor reduction duplicate game')
    for key in ('included_seconds','known_excluded_seconds','neutral_goal_mass'):
        require(math.isclose(math.fsum(r[key] for r in receipt['games']),support[key],rel_tol=1e-10,abs_tol=1e-8),'minor game reductions do not sum')
    require(sum(r['attempts'] for r in receipt['games'])==support['attempts']
        and any(r['unquantified_gap'] for r in receipt['games'])==support['unquantified_gap'],'minor game count/gap reduction differs')
    for key in ('a','b','e_f','e_a','tau_hours'):
        if valuation[key] is not None:require_number(valuation[key],'minor rate/time',low=0)
    b=valuation['b'];seconds=support['included_seconds']
    require((b is not None)==(seconds>0),'minor b availability differs from matched exposure')
    if b is not None:require(math.isclose(b,support['neutral_goal_mass']/(seconds/3600),rel_tol=1e-10,abs_tol=1e-10),'minor b mass/time differs')
    a=valuation['a'];tau=valuation['tau_hours']
    require((tau is not None)==(a is not None),'minor survival availability differs')
    if a is not None:
        expected=2/60 if a==0 else -math.expm1(-a*2/60)/a
        require(math.isclose(tau,expected,rel_tol=1e-10,abs_tol=1e-10),'minor survival equation differs')
    available=all(valuation[k] is not None for k in ('a','b','e_f','e_a'))
    require(valuation['available']==available,'minor valuation availability differs')
    if available:
        require(valuation['reason'] is None and valuation['V_goals'] is not None
            and math.isclose(valuation['V_goals'],minor_value(a,b,valuation['e_f'],valuation['e_a'])['V_goals'],rel_tol=1e-10,abs_tol=1e-10),
            'minor signed value equation differs')
    else:require(type(valuation['reason']) is str and valuation['reason'] and valuation['V_goals'] is None,'missing minor unavailable reason')
    return value


def read_mechanism_state(path,purpose,family,*,narrow=False):
    try:
        return _read_mechanism_state(path,purpose,family,narrow=narrow)
    except (KeyError,TypeError,ValueError,IndexError,AttributeError,OverflowError) as error:
        from .captures import InputContractError
        if isinstance(error,InputContractError):raise
        raise InputContractError(f'malformed mechanism state: {error}') from error


def read_mechanism_selection(path,purpose):
    try:
        return _read_mechanism_selection(path,purpose)
    except (KeyError,TypeError,ValueError,IndexError,AttributeError,OverflowError) as error:
        from .captures import InputContractError
        if isinstance(error,InputContractError):raise
        raise InputContractError(f'malformed mechanism selection: {error}') from error


def read_minor_reference(path,purpose,season,*,expected_inputs=None):
    try:
        return _read_minor_reference(path,purpose,season,expected_inputs=expected_inputs)
    except (KeyError,TypeError,ValueError,IndexError,AttributeError,OverflowError) as error:
        from .captures import InputContractError
        if isinstance(error,InputContractError):raise
        raise InputContractError(f'malformed minor reference: {error}') from error
