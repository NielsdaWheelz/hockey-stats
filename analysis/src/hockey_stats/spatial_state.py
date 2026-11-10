"""strict detached annual positive-spatial artifacts and numerical probes."""

from dataclasses import dataclass, fields
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
from time import perf_counter

import numpy as np
from scipy.sparse import csr_matrix

from .artifacts import digest, ordered_array_digest, require, rows, write_arrays, write_json
from .captures import InputContractError
from .chance_cli import identity, read_json
from .spatial_design import (SpatialDesign, SpecialTeamsDesign, RECIPE as DESIGN_RECIPE, ST_RECIPE as ST_DESIGN_RECIPE,
    CONTEXT_AXES, ST_CONTEXT_AXES, ST_STATES, ST_ROLE_COUNTS, _actor_columns)
from .spatial_rates import HEADS, ROLES, QUANTITIES, ADJUSTMENTS, RECIPE, annual_priors, centered_reference, _conditional_mean, _unpack

CORE_ARRAYS=('basis','exposure_hours','event_offsets','origin_cells','origin_weights','neutral_goal_probability','context_time','context_event')
DESIGN_ARRAYS=CORE_ARRAYS+(
               'X_time_data','X_time_indices','X_time_indptr','X_time_shape',
               'X_event_data','X_event_indices','X_event_indptr','X_event_shape')
MANIFEST_KEYS='schema_version kind purpose season recipe_id recipe design_identity implementation prepared coaches valued previous basis_identity training_cutoff heads files resources'.split()
ST_MANIFEST_KEYS = MANIFEST_KEYS + ['family', 'basis_source']
HEAD_KEYS='head status reasons priors ledger centers reference_predictor age_curves objective solver diagnostics resources'.split()


@dataclass(frozen=True)
class SpatialState:
    path: Path
    manifest: dict
    design: SpatialDesign
    heads: dict
    head_arrays: dict
    projections: list
    projection_arrays: dict
    adjustments: list
    coefficient_support: list
    reference: dict

    @property
    def probes(self):
        bound={member['path'] for member in self.manifest['files']}
        if 'probes/baseline.json' not in bound:
            return None
        comparisons={head:read_json(self.path/f'probes/{head}-comparison.json') for head in HEADS}
        if isinstance(self.design, SpecialTeamsDesign):
            joint = read_json(self.path / 'probes/joint-comparison.json')
            statuses = [value['status'] for value in [*comparisons.values(), joint]]
            status = 'exceeded' if 'exceeded' in statuses else 'unassessed' if 'unassessed' in statuses else 'within_budget'
            return dict(status=status, heads=comparisons, joint=joint)
        return dict(status='passed' if all(c['status']=='passed' for c in comparisons.values()) else 'failed',heads=comparisons)


def _closed(value, keys, label):
    require(type(value) is dict and set(value)==set(keys), f'{label}: invalid fields')


def _finite(value,label):
    if type(value) is dict:
        require(all(type(key) is str for key in value),f'{label}: non-string key')
        for item in value.values(): _finite(item,label)
    elif type(value) is list:
        for item in value: _finite(item,label)
    else:
        require(value is None or type(value) in (str,int,float,bool),f'{label}: invalid json value')
        require(type(value) is not float or math.isfinite(value),f'{label}: nonfinite json')


def _season(value):
    require(type(value) is str and re.fullmatch(r'20\d{2}20\d{2}',value)
            and int(value[4:])==int(value[:4])+1,'invalid spatial season')
    return int(value[:4])


def _binding(value,label):
    require(type(value) is dict and {'path','sha256'}<=value.keys(),f'{label}: missing binding')
    path=Path(value['path'])
    require(type(value['path']) is str and path.is_absolute() and '..' not in path.parts
            and str(path)==value['path'],f'{label}: noncanonical locator')
    digest(value['sha256']);_finite(value,label)


def _member(root,value):
    require(type(value) is str and bool(value),'invalid spatial member locator')
    part=Path(value)
    require(not part.is_absolute() and part.as_posix()==value and all(p not in ('.','..') for p in part.parts),
            'noncanonical spatial member locator')
    path=(root/part).resolve(strict=True)
    require(root in path.parents and path.is_file(),'spatial member escapes artifact')
    return path


def read_spatial_basis(path):
    """read one checked basis member, retaining the archive's declared provenance."""
    root = Path(path).resolve(strict=True)
    manifest_path = root / 'manifest.json' if root.is_dir() else root
    manifest = read_json(manifest_path)
    _closed(manifest, MANIFEST_KEYS, 'basis donor manifest')
    require(manifest['schema_version'] == 1 and manifest['kind'] == 'spatial_state'
            and manifest['purpose'] in ('real', 'fixture') and manifest['recipe'] == RECIPE,
            'basis donor is not an accepted ev state')
    _finite(manifest, 'basis donor manifest')
    _season(manifest['season'])
    require(manifest['recipe_id'] == 'experimental-v1', 'basis donor recipe identity differs')
    digest(manifest['design_identity'])
    for name in ('prepared', 'coaches', 'valued'):
        _binding(manifest[name], 'basis donor ' + name)
        require(manifest[name].get('purpose') == manifest['purpose'], 'basis donor source purpose differs')
    require(manifest['valued'].get('season') == manifest['season'], 'basis donor target year differs')
    require(type(manifest['heads']) is list and [row.get('head') for row in manifest['heads']] == list(HEADS),
            'basis donor head declarations differ')
    for row in manifest['heads']:
        _closed(row, ('head', 'status', 'arrays'), 'basis donor head')
        require(row['status'] == 'complete' and type(row['arrays']) is dict and set(row['arrays']) == {'coefficients'},
                'basis donor does not declare a completed baseline family')
        contract = row['arrays']['coefficients']
        _closed(contract, ('shape', 'dtype'), 'basis donor coefficient declaration')
        require(contract['dtype'] == np.dtype('float64').str and type(contract['shape']) is list
                and len(contract['shape']) == 1 and type(contract['shape'][0]) is int and contract['shape'][0] > 0,
                'basis donor coefficient declaration differs')
    require(type(manifest['files']) is list and len({row.get('path') for row in manifest['files']}) == len(manifest['files']),
            'basis donor duplicate members')
    if manifest['purpose'] == 'real':
        require(manifest['season'] == '20212022' and identity(manifest_path)['sha256'] ==
                '3b7b51339b5ebb00a340a3f593347adf3a72ee137ad24739abd582b8290a5509',
                'real basis donor does not match pinned first ev state')
    descriptors = [row for row in manifest['files'] if row.get('role') == 'design_arrays']
    require(len(descriptors) == 1 and descriptors[0]['path'] == 'design.npz', 'basis donor archive member differs')
    archive = descriptors[0]
    _closed(archive, ('role', 'path', 'sha256'), 'basis donor archive')
    digest(archive['sha256'])
    basis_path = _member(manifest_path.parent, archive['path'])
    try:
        with np.load(basis_path, allow_pickle=False) as saved:
            require('basis' in saved.files, 'basis donor archive has no basis')
            basis = saved['basis']
    except (ValueError, TypeError, KeyError) as error:
        raise InputContractError('invalid basis donor archive') from error
    _validate_basis(basis, manifest['basis_identity'])
    if manifest['purpose'] == 'real':
        require(manifest['basis_identity']['array_sha256'] ==
                '4fa1d565e939dae706a7f3fa0d060b06b647602ba32d2850174b80c6267fa42b',
                'real basis array differs from accepted ev lineage')
    return basis, dict(manifest['basis_identity'])


def _validate_basis(basis, basis_identity):
    require(type(basis) is np.ndarray and basis.dtype == np.dtype('float64') and basis.shape == (656, 40)
            and np.isfinite(basis).all(), 'invalid native forty-mode basis')
    require(np.max(np.abs(basis.mean(axis=0))) < 1e-10
            and np.allclose(basis.T @ basis / 656, np.eye(40), atol=1e-10, rtol=0),
            'uniform basis is not centered orthonormal')
    _closed(basis_identity, ('sha256', 'array_sha256', 'reference', 'modes'), 'basis identity')
    digest(basis_identity['sha256'])
    require(basis_identity['reference'] == 'uniform-native-656' and basis_identity['modes'] == 40
            and basis_identity['array_sha256'] == ordered_array_digest({'basis': basis}), 'native basis byte identity differs')


def _arrays(design):
    result={name:np.asarray(getattr(design,name)) for name in CORE_ARRAYS}
    if isinstance(design, SpecialTeamsDesign):
        result.update(state_time=design.state_time, state_event=design.state_event)
    for name in ('X_time','X_event'):
        matrix=getattr(design,name).tocsr()
        result.update({name+'_data':np.asarray(matrix.data,dtype=np.float64),
                       name+'_indices':np.asarray(matrix.indices,dtype=np.int64),
                       name+'_indptr':np.asarray(matrix.indptr,dtype=np.int64),
                       name+'_shape':np.asarray(matrix.shape,dtype=np.int64)})
    return result


def _design_document(design, arrays):
    excluded=set(CORE_ARRAYS)|{'X_time','X_event','resources','state_time','state_event'}
    body={field.name:getattr(design,field.name) for field in fields(type(design)) if field.name not in excluded}
    for key in ('players','coach_ids','columns','time_keys','event_keys'):
        body[key]=list(body[key])
    return dict(schema_version=1,kind='spatial_st_design' if isinstance(design, SpecialTeamsDesign) else 'spatial_design',definition=body,
                arrays=_array_contract(arrays),array_digest=ordered_array_digest(arrays))


def _array_contract(arrays):
    return {name:dict(shape=list(value.shape),dtype=value.dtype.str) for name,value in arrays.items()}


def _read_arrays(path,contract):
    require(type(contract) is dict and bool(contract),'missing spatial array contract')
    try:
        with np.load(path,allow_pickle=False) as saved:
            require(saved.files==list(contract),'spatial array names/order differ')
            arrays={name:saved[name] for name in saved.files}
    except (ValueError,TypeError,KeyError) as error:
        raise InputContractError('invalid spatial numeric arrays') from error
    require(all(value.dtype in (np.dtype('float64'),np.dtype('int64')) and np.isfinite(value).all() for value in arrays.values()),
            'nonfinite or invalid spatial array dtype')
    require(contract==_array_contract(arrays),'spatial array shape/dtype differs')
    return arrays


def _restore_design(document,arrays,resources):
    _closed(document,('schema_version','kind','definition','arrays','array_digest'),'spatial design')
    require(document['schema_version']==1 and document['kind'] in ('spatial_design','spatial_st_design'),'invalid spatial design schema')
    st = document['kind'] == 'spatial_st_design'
    design_type = SpecialTeamsDesign if st else SpatialDesign
    array_names = CORE_ARRAYS + (('state_time', 'state_event') if st else ()) + DESIGN_ARRAYS[len(CORE_ARRAYS):]
    require(list(arrays)==list(array_names) and document['array_digest']==ordered_array_digest(arrays),'spatial design array identity differs')
    body=dict(document['definition'])
    expected={field.name for field in fields(design_type)}-set(CORE_ARRAYS)-{'X_time','X_event','resources','state_time','state_event'}
    _closed(body,expected,'spatial design definition')
    for name in ('X_time','X_event'):
        data,indices,indptr,shape=[arrays[name+'_'+suffix] for suffix in ('data','indices','indptr','shape')]
        require(data.ndim==indices.ndim==indptr.ndim==shape.ndim==1 and len(shape)==2
                and np.all(shape>=0) and len(data)==len(indices) and len(indptr)==shape[0]+1
                and indptr[0]==0 and indptr[-1]==len(data) and np.all(np.diff(indptr)>=0)
                and np.all((indices>=0)&(indices<shape[1])),'invalid spatial csr structure')
        require(data.dtype==np.dtype('float64') and all(a.dtype==np.dtype('int64') for a in (indices,indptr,shape)),
                'invalid spatial csr dtype')
        matrix=csr_matrix((data,indices,indptr),shape=tuple(shape))
        require(matrix.has_canonical_format,'spatial matrix has unsorted or duplicate coordinates')
        body[name]=matrix
    body.update({name:arrays[name] for name in CORE_ARRAYS})
    body['resources']=resources
    for name in ('players','coach_ids','columns','time_keys','event_keys'):
        body[name]=tuple(body[name])
    if st:
        body.update(state_time=arrays['state_time'], state_event=arrays['state_event'])
    design=design_type(**body)
    validate_design(design)
    return design


def validate_design(design):
    """saved source identities and exact finite designs suffice without upstream io."""
    family = 'st' if isinstance(design, SpecialTeamsDesign) else 'ev'
    st = family == 'st'
    axes = ST_CONTEXT_AXES if st else CONTEXT_AXES
    recipe = ST_DESIGN_RECIPE if st else DESIGN_RECIPE
    intercept_count = 3 if st else 1
    require(design.purpose in ('real','fixture'),'invalid spatial purpose')
    _season(design.season)
    for name in ('prepared','coaches','valued'):
        _binding(getattr(design,name),name)
        require(getattr(design,name).get('purpose')==design.purpose,f'{name}: spatial purpose differs')
    require(design.valued.get('season')==design.season,'spatial valued target season differs')
    players=design.players
    require(type(players) is tuple and len(set(players))==len(players) and list(players)==sorted(players)
            and all(type(p) is str and p for p in players),'invalid spatial roster axis')
    require(set(design.player_facts)==set(players),'spatial player facts do not cover roster')
    for row in design.player_facts.values():
        _closed(row,('position_group','age_days'),'player facts')
        require(row['position_group'] in ('F','D',None),'invalid spatial position')
        age=row['age_days'];require(age is None or type(age) in (int,float) and math.isfinite(age) and age>=0,'invalid spatial age')
    require(len(set(design.coach_ids))==len(design.coach_ids) and list(design.coach_ids)==sorted(design.coach_ids),'invalid coach axis')
    require(design.recipe==recipe,'spatial fixed design definition differs')
    columns=design.columns
    expected_columns=_actor_columns(design.players,design.coach_ids,family=family)+[dict(kind='context',name=axis['name']) for axis in axes]
    require(list(columns)==expected_columns,'spatial fixed column order/definition differs')
    _closed(design.transforms,('axes','design_sha256'),'spatial transforms')
    require(len(design.transforms['axes'])==len(axes),'spatial transform axis cardinality differs')
    total_hours=float(design.exposure_hours.sum())
    for axis,transform in zip(axes,design.transforms['axes'],strict=True):
        require({key:transform[key] for key in axis}==axis and set(transform)==set(axis)|{'location','scale','available_hours','missing_hours'},'spatial transform axis definition differs')
        require(all(type(transform[key]) in (int,float) and math.isfinite(transform[key]) for key in ('location','scale','available_hours','missing_hours'))
                and transform['scale']>0 and transform['available_hours']>=0 and transform['missing_hours']>=-1e-12
                and abs(transform['available_hours']+transform['missing_hours']-total_hours)<1e-9,
                'invalid spatial transform moments')
        require(axis['continuous'] or transform['scale']==1.,'categorical contrast was scaled')
        require(transform['available_hours']>0 or (transform['location']==0 and transform['scale']==1),'all-absent context has invented moments')
    expected_transform_hash=hashlib.sha256(json.dumps(dict(recipe=recipe['sha256'],columns=columns,transforms={'axes':design.transforms['axes']}),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    require(design.transforms['design_sha256']==expected_transform_hash,'spatial design definition digest differs')
    require(list(columns[:intercept_count]) == _actor_columns((), (), family=family), 'invalid spatial intercepts')
    require(len({c['name'] for c in columns})==len(columns),'duplicate spatial columns')
    actor_keys=set()
    for column in columns[intercept_count:]:
        if column['kind']=='actor':
            _closed(column,('kind','name','block','id','subblock'),'actor column')
            require(column['block'] in ('attacking_player','defending_player','attacking_coach','defending_coach'),'invalid actor block')
            if column['block'].endswith('_player'):
                require(column['id'] in players and column['subblock']=='base','invalid spatial player coordinate')
            else:
                require(column['id'] in design.coach_ids and column['subblock'] in (('base',) if st else ('base','score:-2','score:-1','score:0','score:1','score:2','shell')),'invalid spatial coach coordinate')
            key=(column['block'],column['id'],column['subblock']);require(key not in actor_keys,'duplicate spatial actor');actor_keys.add(key)
        else:
            _closed(column,('kind','name'),'context column');require(column['kind']=='context','invalid spatial column kind')
    expected={(side+'_player',p,'base') for side in ('attacking','defending') for p in players}
    expected|={(side+'_coach',c,g) for side in ('attacking','defending') for c in design.coach_ids
               for g in (('base',) if st else ('base','score:-2','score:-1','score:0','score:1','score:2','shell'))}
    require(actor_keys==expected,'spatial actor axes omit or invent roster/gate coordinates')
    n=len(design.exposure_hours);ne=len(design.event_offsets)-1;d=len(columns)
    actor_count=len(_actor_columns(design.players,design.coach_ids,family=family))
    require(design.X_time.shape==(n,actor_count) and design.X_event.shape==(ne,actor_count),'spatial actor matrix dimensions differ')
    require(design.context_time.shape==(n,d-actor_count) and design.context_event.shape==(ne,d-actor_count)
            and design.context_time.dtype==design.context_event.dtype==np.dtype('float64')
            and np.isfinite(design.context_time).all() and np.isfinite(design.context_event).all(),'invalid spatial dense context matrices')
    centered=np.asarray(design.context_time.T@design.exposure_hours).ravel()
    require(np.all(np.abs(centered)<=1e-9*(1+float(design.exposure_hours.sum()))),'elapsed context is not training-exposure centered')
    require(len(design.time_keys)==n and len(design.event_keys)==ne,'spatial source locator cardinality differs')
    require(design.exposure_hours.dtype==np.dtype('float64') and design.exposure_hours.ndim==1
            and np.isfinite(design.exposure_hours).all() and np.all(design.exposure_hours>0),'invalid positive spatial exposure')
    require(design.event_offsets.dtype==np.dtype('int64') and design.event_offsets.ndim==1 and len(design.event_offsets)>0
            and design.event_offsets[0]==0 and np.all(np.diff(design.event_offsets)>0),'invalid ragged spatial offsets')
    no=int(design.event_offsets[-1])
    require(design.origin_cells.dtype==np.dtype('int64') and design.origin_cells.shape==(no,)
            and np.all((design.origin_cells>=0)&(design.origin_cells<656)),'invalid spatial origin cells')
    for name in ('origin_weights','neutral_goal_probability'):
        a=getattr(design,name);require(a.dtype==np.dtype('float64') and a.shape==(no,) and np.isfinite(a).all()
                                  and np.all((a>=0)&(a<=1)),f'invalid spatial {name}')
    if ne:
        require(np.allclose(np.add.reduceat(design.origin_weights,design.event_offsets[:-1]),1.,rtol=0,atol=1e-12),'spatial origin mass differs from one')
    for matrix in (design.X_time,design.X_event):
        require(matrix.dtype==np.dtype('float64') and matrix.has_canonical_format and np.isfinite(matrix.data).all()
                and np.all(matrix.data==1.),'invalid physical sparse actor incidence')
        require(np.all(np.asarray(matrix[:, :intercept_count].sum(axis=1)).ravel() == 1), 'spatial intercept incidence differs')
    if st:
        require(design.state_time.dtype == design.state_event.dtype == np.dtype('int64')
                and design.state_time.shape == (n,) and design.state_event.shape == (ne,)
                and np.all((design.state_time >= 0) & (design.state_time < 3))
                and np.all((design.state_event >= 0) & (design.state_event < 3)), 'invalid special-teams state axes')
    actors={key:i for i,c in enumerate(columns) if c['kind']=='actor' for key in [(c['block'],c['id'],c['subblock'])]}
    for matrix,keys,label in ((design.X_time,design.time_keys,'elapsed'),(design.X_event,design.event_keys,'event')):
        seen=set()
        for i,key in enumerate(keys):
            require(type(key) is dict and {'game_id','segment_index','chunk_index','source_index','attacking_side','attacking_players','defending_players'}<=key.keys(),'missing spatial source locator')
            locator=(key['game_id'],key['segment_index'],key['chunk_index'],key['source_index'],key['attacking_side'])
            require(locator not in seen,'duplicate spatial source row');seen.add(locator)
            require(key['attacking_side'] in ('home','away'),'invalid directed spatial side')
            if st:
                state_index = int((design.state_time if label == 'elapsed' else design.state_event)[i])
                require(key.get('physical_state') == ST_STATES[state_index], 'special-teams source state differs')
                require(matrix[i, state_index] == 1, 'special-teams state/intercept incidence differs')
            for side in ('attacking','defending'):
                members=key[side+'_players']
                require(type(members) is list and len(members)==len(set(members))==(ST_ROLE_COUNTS[state_index][0 if side == 'attacking' else 1] if st else 5) and set(members)<=set(players),'invalid physical role membership')
                expected_indices={actors[(side+'_player',p,'base')] for p in members}
                row=matrix[i]
                actual={int(j) for j,v in zip(row.indices,row.data) if columns[j].get('block')==side+'_player' and v!=0}
                require(actual==expected_indices,'spatial membership/actor design differs')
            require(set(key['attacking_players']).isdisjoint(key['defending_players']),'player on both directed sides')
    physical_events=[(key['game_id'],key['source_index']) for key in design.event_keys]
    require(len(physical_events)==len(set(physical_events)),'physical attempt enters both spatial directions')
    if st:
        identities = [(key['game_id'], key['segment_index'], key['chunk_index']) for key in design.time_keys]
        require(len(identities) == len(set(identities)), 'special-teams physical interval enters twice')
    reciprocal={}
    for i,key in (() if st else enumerate(design.time_keys)):
        identity=(key['game_id'],key['segment_index'],key['chunk_index'])
        other=reciprocal.pop(identity,None)
        if other is None:
            reciprocal[identity]=(i,key)
        else:
            j,prior=other
            require(prior['attacking_side']!=key['attacking_side']
                    and prior['attacking_players']==key['defending_players'] and prior['defending_players']==key['attacking_players']
                    and design.exposure_hours[i]==design.exposure_hours[j],'directed spatial elapsed reciprocity differs')
    require(not reciprocal,'spatial physical chunks do not have two directions')
    _validate_basis(design.basis, design.basis_identity)
    offsets = design.annual_offsets
    _closed(offsets, ('r', 'pi', 'qbar'), 'annual offsets')
    rate, pi, q = (np.asarray(offsets[key]) for key in ('r', 'pi', 'qbar'))
    expected_shape = (3, 656) if st else (656,)
    require(rate.shape == ((3,) if st else ()) and np.isfinite(rate).all() and np.all(rate > 0)
            and pi.shape == q.shape == expected_shape and np.isfinite(pi).all() and np.isfinite(q).all()
            and np.all(pi > 0) and np.all(np.abs(pi.sum(axis=-1) - 1) < 1e-12)
            and np.all((q > 0) & (q < 1)), 'invalid annual spatial offsets')
    mass = np.bincount(design.origin_cells, weights=design.origin_weights, minlength=656)
    neutral = np.bincount(design.origin_cells, weights=design.origin_weights * design.neutral_goal_probability, minlength=656)
    hours = float(design.exposure_hours.sum())
    pi_pool = (mass + 1 / 656) / (ne + 1)
    rate_pool = (ne + 1) / (hours + 1)
    quality_pool = (neutral.sum() + .5) / (ne + 1)
    for state_index in (range(3) if st else (None,)):
        if st:
            time_mask, event_mask = design.state_time == state_index, design.state_event == state_index
            count, state_hours = int(event_mask.sum()), float(design.exposure_hours[time_mask].sum())
            require(state_hours > 0 or count == 0, 'special-teams orphan events have no state exposure')
            origin_mask = np.repeat(event_mask, np.diff(design.event_offsets))
            state_mass = np.bincount(design.origin_cells[origin_mask], weights=design.origin_weights[origin_mask], minlength=656)
            state_neutral = np.bincount(design.origin_cells[origin_mask], weights=(design.origin_weights * design.neutral_goal_probability)[origin_mask], minlength=656)
            actual_rate, actual_pi, actual_q = rate[state_index], pi[state_index], q[state_index]
        else:
            count, state_hours, state_mass, state_neutral = ne, hours, mass, neutral
            actual_rate, actual_pi, actual_q = rate, pi, q
        expected_pi = (state_mass + 10 * pi_pool) / (count + 10)
        expected_rate = (count + rate_pool) / (state_hours + 1)
        qmean = (state_neutral.sum() + 10 * quality_pool) / (count + 10)
        expected_q = (state_neutral + 10 * expected_pi * qmean) / (state_mass + 10 * expected_pi)
        require(abs(actual_rate - expected_rate) < 1e-12 * (1 + expected_rate)
                and np.allclose(actual_pi, expected_pi, atol=1e-14, rtol=1e-12)
                and np.allclose(actual_q, expected_q, atol=1e-14, rtol=1e-12), 'annual offsets differ from retained target/exposure')
    require(design.coverage['attempts'] == ne and abs(design.coverage['origin_mass'] - ne) < 1e-9
            and abs(design.coverage['directed_included_hours'] - hours) < 1e-9
            and abs((1 if st else 2) * design.coverage['physical_included_hours'] - hours) < 1e-9,
            'spatial coverage mass/time identity differs')
    if st:
        from .analysis_publication import close

        _binding(design.basis_source, 'special-teams basis source')
        _closed(design.basis_source, ('path', 'sha256', 'archive'), 'special-teams basis source')
        _binding(design.basis_source['archive'], 'basis archive declared provenance')
        require([row['state'] for row in design.coverage['states']] == list(ST_STATES), 'special-teams coverage state axis differs')
        state_support = design.coverage['state_support']
        require(type(state_support) is list and [row.get('state') for row in state_support] == list(ST_STATES),
                'special-teams baseline evidence states differ')
        for index, row in enumerate(design.coverage['states']):
            _closed(row, ('state','included_hours','attacking_slot_hours','defending_slot_hours','origin_mass','neutral_chance_mass','attempts','state_extrapolated'), 'special-teams state coverage')
            state_hours = float(design.exposure_hours[design.state_time == index].sum())
            require(abs(row['included_hours'] - state_hours) < 1e-9
                    and row['attempts'] == int((design.state_event == index).sum())
                    and row['state_extrapolated'] == (state_hours == 0), 'special-teams state coverage differs')
            origins = np.repeat(design.state_event == index, np.diff(design.event_offsets))
            require(abs(row['origin_mass'] - float(design.origin_weights[origins].sum())) < 1e-9
                    and abs(row['neutral_chance_mass'] - float((design.origin_weights * design.neutral_goal_probability)[origins].sum())) < 1e-9,
                    'special-teams state origin/neutral mass differs')
            for role_index, role in enumerate(('attacking', 'defending')):
                require(abs(row[role + '_slot_hours'] - ST_ROLE_COUNTS[index][role_index] * state_hours) < 1e-9,
                        'special-teams state slot-hours differ')
            evidence = state_support[index]
            _closed(evidence, ('state','physical_seconds','directed_seconds','attempts','origin_weight',
                              'baseline_current_information'), 'special-teams baseline evidence')
            for key in ('physical_seconds','directed_seconds','origin_weight'):
                require(type(evidence[key]) in (int,float) and math.isfinite(evidence[key]) and evidence[key] >= 0,
                        'invalid special-teams baseline evidence count/time')
            require(type(evidence['attempts']) is int and evidence['attempts'] == row['attempts']
                    and close(evidence['physical_seconds'], row['included_hours'] * 3600)
                    and evidence['directed_seconds'] == evidence['physical_seconds']
                    and close(evidence['origin_weight'], row['origin_mass']),
                    'special-teams baseline evidence differs from state coverage')
            flags = evidence['baseline_current_information']
            _closed(flags, HEADS, 'special-teams baseline information')
            require(all(type(value) is bool for value in flags.values()) and flags == dict(
                volume=evidence['directed_seconds'] > 0 or evidence['attempts'] > 0,
                shape=evidence['origin_weight'] > 0, quality=evidence['origin_weight'] > 0),
                'special-teams baseline information differs from retained exposure')
        actor_indexes = {(column['block'], column['id']): index for index, column in enumerate(design.columns)
                         if column['kind'] == 'actor' and column['block'].endswith('_player')}
        from .spatial_rates import actor_support
        supports = [actor_support(design, state=index) for index in range(3)]
        for player in design.players:
            for role, block in (('offense', 'attacking_player'), ('defense', 'defending_player')):
                declared = design.coverage['players'][player]['roles'][role]
                state_names = ST_STATES if role == 'offense' else tuple(name[::-1] for name in ST_STATES)
                require(set(declared) == {'common', *state_names}, 'special-teams focal support states differ')
                index = actor_indexes[(block, player)]
                for state_index, state_name in enumerate(state_names):
                    actual = supports[state_index][index]
                    value = declared[state_name]
                    require(abs(value['included_seconds'] - actual['included_seconds']) < 1e-8 * (1 + actual['included_seconds'])
                            and value['events'] == actual['likelihood_events'], 'special-teams focal state support differs from physical design')
                require(abs(declared['common']['included_seconds'] - sum(declared[name]['included_seconds'] for name in state_names)) < 1e-8 * (1 + declared['common']['included_seconds'])
                        and declared['common']['events'] == sum(declared[name]['events'] for name in state_names),
                        'special-teams common support is not the same-role physical union')
    digest(design.transforms['design_sha256'])


def validate_head(metadata, arrays, design):
    _closed(metadata,HEAD_KEYS,'spatial head');_finite(metadata,'spatial head')
    head=metadata['head'];require(head in HEADS,'invalid spatial head')
    require(metadata['status'] in ('complete','failed','unavailable'),'invalid spatial head status')
    require(type(metadata['reasons']) is list and all(type(r) is str and r for r in metadata['reasons']),'invalid head reasons')
    require((metadata['status']=='complete')==(not bool(metadata['reasons'])),'spatial head reason/status differs')
    prior_rows=metadata['priors'];require(type(prior_rows) is list,'missing spatial priors')
    for row in metadata['ledger']+[p['last_supported'] for p in prior_rows if p.get('last_supported') is not None]:
        _closed(row,('block','id','subblock','coefficient','season','position_group','age','support_seasons'),'last-supported spatial record')
        key=(row['block'],row['id'],row['subblock'])
        require(row['block'] in ('attacking_player','defending_player','attacking_coach','defending_coach')
                and type(row['id']) is str and row['id'] and row['subblock'] in (('base',) if isinstance(design, SpecialTeamsDesign) else ('base','score:-2','score:-1','score:0','score:1','score:2','shell')),'invalid historical actor identity')
        require(_season(row['season'])<=_season(design.season),'future spatial carry record')
        require(row['position_group'] in ('F','D',None) and (row['age'] is None or type(row['age']) in (int,float) and row['age']>=0),'invalid carried age/position')
        coefficient=np.asarray(row['coefficient'])
        require(coefficient.shape==({'volume':1,'shape':40,'quality':41}[head],) and np.isfinite(coefficient).all(),'invalid carried spatial coordinates')
        years=row['support_seasons']
        require(type(years) is list and years and years==sorted(set(years)) and years[-1]==row['season']
                and all(_season(year)<=_season(row['season']) for year in years),'invalid supported spatial seasons')
    ledger_keys=[(r['block'],r['id'],r['subblock']) for r in metadata['ledger']]
    require(len(ledger_keys)==len(set(ledger_keys)) and ledger_keys==sorted(ledger_keys),'spatial carry ledger order/uniqueness differs')
    # the incoming ledger is explicit in each prior; untouched absent actors are
    # retained in the output ledger without making them current observations.
    incoming={}
    for row in metadata['ledger']:
        if row['season']!=design.season: incoming[(row['block'],row['id'],row['subblock'])]=row
    for prior in prior_rows:
        last=prior['last_supported']
        if last is not None: incoming[(last['block'],last['id'],last['subblock'])]=last
    expected=annual_priors(design,head,list(incoming.values()))
    require(len(expected)==len(prior_rows),'spatial prior axes differ')
    for actual,wanted in zip(prior_rows,expected,strict=True):
        require({k:v for k,v in actual.items() if k!='prior_mean'}==wanted,'spatial prior/support/history contract differs')
    if metadata['status']!='complete':
        require(not arrays and metadata['centers'] is None and metadata['reference_predictor'] is None,'unavailable head has usable coefficients')
        require(all(row['season']!=design.season for row in metadata['ledger']),'unavailable head advances history')
        return
    require(set(arrays)=={'coefficients'} and arrays['coefficients'].dtype==np.dtype('float64')
            and arrays['coefficients'].ndim==1 and np.isfinite(arrays['coefficients']).all(),'invalid fitted spatial vector')
    beta,age=_unpack(arrays['coefficients'],design,head)
    if isinstance(design, SpecialTeamsDesign):
        for state_index in range(3):
            informed = bool(np.any(design.state_time == state_index)) if head == 'volume' else bool(np.any(design.state_event == state_index))
            require(informed or np.all(beta[state_index] == 0), 'unsupported special-teams intercept leaves static zero prior')
    expected_curves=None if head!='volume' else dict(reference_age=27.,scale_years=10.,ridge_precision=64.,
        curves=[dict(role=role,position_group=position,coefficients=age[start:start+2].tolist())
                for role,position,start in (('offense','F',0),('offense','D',2),('defense','F',4),('defense','D',6))])
    require(metadata['age_curves']==expected_curves,'spatial fitted age curves differ')
    ledger={(row['block'],row['id'],row['subblock']):row for row in metadata['ledger']}
    require(len(ledger)==len(metadata['ledger']),'duplicate spatial carry ledger')
    require({key for key,row in ledger.items() if row['season']==design.season}
            =={(p['block'],p['id'],p['subblock']) for p in prior_rows if p['current_season_information']},'spatial ledger current supported axes differ')
    for prior in prior_rows:
        mean=_conditional_mean(prior,age)
        require(prior['prior_mean']==mean.tolist(),'spatial conditional prior mean differs')
        key=(prior['block'],prior['id'],prior['subblock'])
        if prior['prior_only']:
            require(np.array_equal(beta[prior['index']],mean) and ledger.get(key)==prior['last_supported'],'prior-only coefficient advances history or leaves its conditional mean')
        else:
            wanted=dict(block=prior['block'],id=prior['id'],subblock=prior['subblock'],coefficient=beta[prior['index']].tolist(),
                        season=design.season,position_group=prior['position_group'],age=prior['age'],support_seasons=prior['prior_seasons']+[design.season])
            require(ledger.get(key)==wanted,'supported ledger differs from raw fitted coordinate')
    centers,reference,vector=centered_reference(design,head,beta)
    require(metadata['centers']==centers and metadata['reference_predictor']==reference.tolist(),'spatial centering/applicability transfer differs')
    solver=metadata['solver'];require(type(solver) is dict and solver['converged'] is True,'failed solver presented as complete')
    require(solver['options'] in (RECIPE['solver'],RECIPE['continuation']) and solver['raw_gradient_inf_norm']>=0,'invalid spatial solver controls/gradient')
    require(metadata['objective']['total']==metadata['objective']['likelihood']+metadata['objective']['penalty'],'spatial objective accounting differs')


def read_completed_spatial_heads(source, design, incoming, expected_files):
    """read pinned ordinary components against the rebuilt design and accepted history."""
    source=Path(source).resolve();names=[f'heads/{head}{suffix}' for head in HEADS for suffix in ('.json','.npz')]
    require(type(expected_files) is dict and set(expected_files)==set(names),'completed spatial head inventory differs')
    require(set(incoming)==set(HEADS),'completed spatial incoming heads differ')
    heads,arrays,files={},{},[]
    for head in HEADS:
        for suffix in ('.json','.npz'):
            name=f'heads/{head}{suffix}';digest(expected_files[name]);member=identity(source/name)
            require(member['sha256']==expected_files[name],'completed spatial head digest differs');files.append(member)
        metadata=read_json(source/f'heads/{head}.json')
        size=len(design.columns)*{'volume':1,'shape':40,'quality':41}[head]+(8 if head=='volume' else 0)
        values=_read_arrays(source/f'heads/{head}.npz',{'coefficients':dict(shape=[size],dtype=np.dtype('float64').str)})
        validate_head(metadata,values,design)
        require(metadata['head']==head and metadata['status']=='complete' and metadata['solver']['options']==RECIPE['solver']
                and metadata['solver']['maxfun']==15000 and metadata['solver']['maxls']==20,'completed spatial head is not an ordinary successful fit')
        expected=annual_priors(design,head,incoming[head])
        require([{k:v for k,v in row.items() if k!='prior_mean'} for row in metadata['priors']]==expected,
                'completed spatial priors differ from accepted predecessor')
        prior_keys={(row['block'],row['id'],row['subblock']) for row in expected if row['current_season_information']}
        old={(row['block'],row['id'],row['subblock']):row for row in incoming[head]}
        ledger={(row['block'],row['id'],row['subblock']):row for row in metadata['ledger']}
        require(set(ledger)==set(old)|prior_keys and all(ledger[key]==value for key,value in old.items() if key not in prior_keys),
                'completed spatial older/absent anchors differ from accepted predecessor')
        heads[head]=metadata;arrays[head]=values
    return heads,arrays,files


def copy_completed_spatial_heads(source, output, files):
    folder=Path(output)/'heads';folder.mkdir()
    for member in files:
        original=Path(member['path']);require(original.parent==Path(source)/'heads','completed spatial source locator differs')
        destination=folder/original.name
        with original.open('rb') as src,destination.open('xb') as dst:shutil.copyfileobj(src,dst)
        require(identity(destination)['sha256']==member['sha256'],'copied spatial head bytes differ')


def write_spatial_head(output, metadata, arrays):
    folder=Path(output)/'heads';folder.mkdir(exist_ok=True)
    head=metadata['head']
    write_json(folder/f'{head}.json',metadata)
    if arrays: write_arrays(folder,f'{head}.npz',arrays)


def _write_rows(path,values):
    with path.open('x',encoding='utf-8') as destination:
        for value in values:
            _finite(value,'spatial row')
            destination.write(json.dumps(value,allow_nan=False,separators=(',',':'))+'\n')


def write_spatial_state(state, projections):
    began=perf_counter();root=state.path
    design=state.design;validate_design(design)
    arrays=_arrays(design);document=_design_document(design,arrays)
    write_arrays(root,'design.npz',arrays);write_json(root/'design.json',document)
    write_json(root/'coverage.json',design.coverage)
    write_json(root/'reference.json',projections.reference)
    write_json(root/'diagnostics.json',projections.diagnostics)
    _write_rows(root/'projections.jsonl',projections.rows)
    _write_rows(root/'adjustments.jsonl',projections.adjustments)
    _write_rows(root/'coefficient-support.jsonl',projections.coefficient_support)
    write_arrays(root,'projections.npz',projections.arrays)
    members=[('design','design.json'),('design_arrays','design.npz'),('coverage','coverage.json'),
             ('reference','reference.json'),('projection_diagnostics','diagnostics.json'),
             ('projections','projections.jsonl'),('adjustments','adjustments.jsonl'),
             ('coefficient_support','coefficient-support.jsonl'),('projection_arrays','projections.npz')]
    head_rows=[]
    for head in HEADS:
        metadata,values=state.heads[head],state.head_arrays[head]
        validate_head(metadata,values,design)
        if not (root/'heads'/f'{head}.json').exists(): write_spatial_head(root,metadata,values)
        require(read_json(root/'heads'/f'{head}.json')==metadata,'saved expensive head differs')
        head_rows.append(dict(head=head,status=metadata['status'],arrays=_array_contract(values)))
        members.append(('head_metadata',f'heads/{head}.json'))
        if values: members.append(('head_arrays',f'heads/{head}.npz'))
    manifest=dict(state.manifest)
    manifest['heads']=head_rows
    manifest['files']=[dict(role=role,path=path,sha256=identity(root/path)['sha256']) for role,path in members]
    manifest['resources']=dict(manifest['resources'],projection=projections.diagnostics,
                               output_bytes=sum((root/path).stat().st_size for _,path in members),
                               write_wall_seconds=perf_counter()-began)
    write_json(root/'manifest.json',manifest)
    return read_spatial_state(root,manifest['purpose'], expected_family='st' if isinstance(design, SpecialTeamsDesign) else 'ev')


def _validate_projections(state):
    from .spatial_rates import project_spatial
    expected=project_spatial(state,actual_context=False)
    require(state.projections==expected.rows and state.reference==expected.reference,'saved spatial standardized projection/reference differs')
    require(state.coefficient_support==expected.coefficient_support,'saved spatial head-support records differ')
    arrays=state.projection_arrays
    require(set(arrays)=={'rates','adjustments'} and arrays['rates'].shape==expected.arrays['rates'].shape
            and np.array_equal(arrays['rates'],expected.arrays['rates']),'saved native spatial contrast differs')
    adjustment_maps=arrays['adjustments']
    if isinstance(state.design, SpecialTeamsDesign):
        _validate_special_teams_adjustments(state)
        return
    require(adjustment_maps.shape==(len(state.design.players),2,2,7,656),'invalid native adjustment axes')
    require(len(state.adjustments)==len(state.design.players)*2,'adjustment row cardinality differs')
    for index,row in enumerate(state.adjustments):
        i,r=divmod(index,2)
        _closed(row,('season','player_id','role','available','reason','exposure_seconds','map_index','attempts','xg'),'adjustment')
        require(row['season']==state.manifest['season'] and row['player_id']==state.design.players[i]
                and row['role']==ROLES[r] and row['map_index']==[i,r],'adjustment identity/order differs')
        for qi,q in enumerate(QUANTITIES):
            _closed(row[q],ADJUSTMENTS,'adjustment scalars')
            if row['available']:
                support=next(v for v in state.coefficient_support if v['player_id']==row['player_id'] and v['role']==row['role'] and v['head']=='volume')
                require(row['reason'] is None and row['exposure_seconds']>0 and abs(row['exposure_seconds']-support['included_seconds'])<1e-8*(1+row['exposure_seconds']),'available adjustment exposure differs from role support')
                values=adjustment_maps[i,r,qi]
                require(np.all(values[[0,6]]>0),'invalid complete adjustment rates')
                neutral=arrays['rates'][i,r,qi,0]
                require(np.all(np.abs(values[0]-neutral)<=1e-10*(1+np.abs(neutral))),'actual-context empty coalition differs from frozen neutral reference')
                if qi==1:
                    require(np.all(values[[0,6]]<=adjustment_maps[i,r,0,[0,6]]),'actual-context chance exceeds complete attempt rate')
                require(all(abs(row[q][name]-float(values[k].sum()))<=1e-11*(1+abs(row[q][name])) for k,name in enumerate(ADJUSTMENTS)),
                        'adjustment map/scalar identity differs')
                residual=values[6]-values[:5].sum(axis=0)
                require(np.all(np.abs(residual-values[5])<=1e-10*(1+np.abs(values[6])+np.abs(values[:6]).sum(axis=0))),
                        'saved adjustment closure differs')
            else:
                require(row['reason']!='no_exposure' or row['exposure_seconds']==0,'no-exposure adjustment has physical time')
                require(type(row['reason']) is str and row['reason'] and all(v is None for v in row[q].values())
                        and np.all(adjustment_maps[i,r,qi]==0),'unavailable adjustment fabricates rates')


def _validate_special_teams_adjustments(state):
    from .analysis_publication import close
    from .spatial_rates import ST_STRENGTHS
    maps = state.projection_arrays['adjustments']
    rates = state.projection_arrays['rates']
    require(maps.shape == (len(state.design.players), 4, 2, 2, 7, 656), 'invalid special-teams native adjustment axes')
    require(len(state.adjustments) == len(state.design.players) * 8, 'special-teams adjustment cardinality differs')
    for index, row in enumerate(state.adjustments):
        i, remainder = divmod(index, 8)
        s, r = divmod(remainder, 2)
        _closed(row, ('season','player_id','role','strength','available','reason','exposure_seconds','map_index',
                      'states','attempts','xg'), 'special-teams adjustment')
        require(type(row['available']) is bool and row['season'] == state.manifest['season'] and row['player_id'] == state.design.players[i]
                and row['role'] == ROLES[r] and row['strength'] == ST_STRENGTHS[s][r]
                and row['map_index'] == [i, s, r], 'special-teams adjustment identity/order differs')
        states = row['states']
        expected_states = list(ST_STATES) if s == 0 else [ST_STATES[s - 1]]
        support = state.design.coverage['players'][row['player_id']]['roles'][row['role']]['common' if s == 0 else row['strength']]
        exposure = support['included_seconds']
        if row['available']:
            require(type(states) is list and [value.get('state') for value in states] == expected_states,
                    'special-teams actual states differ')
            for value in states:
                _closed(value, ('state','seconds','weight'), 'special-teams actual-state exposure')
            require(row['reason'] is None and exposure > 0 and abs(row['exposure_seconds'] - exposure) < 1e-8 * (1 + exposure),
                    'available specialty adjustment exposure differs from support')
            for value in states:
                selector = value['state'] if r == 0 else value['state'][::-1]
                seconds = state.design.coverage['players'][row['player_id']]['roles'][row['role']][selector]['included_seconds']
                require(type(value['seconds']) in (int,float) and math.isfinite(value['seconds']) and value['seconds'] >= 0
                        and close(value['seconds'], seconds)
                        and type(value['weight']) in (int,float) and math.isfinite(value['weight']) and 0 <= value['weight'] <= 1
                        and close(value['weight'], value['seconds'] / row['exposure_seconds']),
                        'actual specialty mixture differs from focal state exposure')
            require(close(sum(value['seconds'] for value in states), row['exposure_seconds'])
                    and close(sum(value['weight'] for value in states), 1),
                    'actual specialty state exposure/weights do not close')
        else:
            require(type(row['reason']) is str and row['reason']
                    and states is None and row['exposure_seconds'] == (0 if row['reason'] == 'no_exposure' else None),
                    'unavailable specialty adjustment invents exposure or weights')
        for qi, quantity in enumerate(QUANTITIES):
            _closed(row[quantity], ADJUSTMENTS, 'special-teams adjustment scalars')
            values = maps[i, s, r, qi]
            if not row['available']:
                require(all(value is None for value in row[quantity].values()) and np.all(values == 0),
                        'unavailable specialty adjustment fabricates rates')
                continue
            require(np.all(values[[0, 6]] > 0), 'invalid complete specialty adjustment rate')
            baseline = (sum(value['weight'] * rates[i, t + 1, r, qi, 0] for t, value in enumerate(states))
                        if s == 0 else rates[i, s, r, qi, 0])
            require(np.all(np.abs(values[0] - baseline) <= 1e-10 * (1 + np.abs(baseline))),
                    'actual specialty baseline differs from focal-time state mixture')
            if qi == 1:
                require(np.all(values[[0, 6]] <= maps[i, s, r, 0, [0, 6]]), 'actual specialty chance exceeds attempt rate')
            require(all(abs(row[quantity][name] - float(values[k].sum())) <= 1e-11 * (1 + abs(row[quantity][name]))
                        for k, name in enumerate(ADJUSTMENTS)), 'specialty adjustment map/scalar identity differs')
            if s == 0:
                terms = np.asarray([value['weight'] * maps[i, t + 1, r, qi] for t, value in enumerate(states)])
                mixture = terms.sum(axis=0)
                require(np.all(np.abs(values - mixture) <= 1e-10 * (1 + np.abs(values) + np.abs(terms).sum(axis=0))),
                        'common specialty adjustments differ from focal-time exact-state mixture')
            residual = values[6] - values[:5].sum(axis=0)
            require(np.all(np.abs(residual - values[5]) <= 1e-10 * (1 + np.abs(values[6]) + np.abs(values[:6]).sum(axis=0))),
                    'saved specialty adjustment closure differs')


def read_spatial_state(path,expected_purpose, *, expected_family='ev'):
    root=Path(path).resolve(strict=True)
    if root.is_file():require(root.name=='manifest.json','expected spatial manifest');root=root.parent
    require(expected_family in ('ev', 'st'), 'invalid expected spatial family')
    st = expected_family == 'st'
    manifest=read_json(root/'manifest.json');_closed(manifest,ST_MANIFEST_KEYS if st else MANIFEST_KEYS,'spatial manifest');_finite(manifest,'spatial manifest')
    require(manifest['schema_version']==1 and manifest['kind']==('spatial_st_state' if st else 'spatial_state') and manifest['purpose']==expected_purpose
            and expected_purpose in ('real','fixture'),'invalid spatial state schema/purpose')
    year=_season(manifest['season'])
    from .spatial_rates import ST_RECIPE
    require(manifest['recipe_id']=='experimental-v1' and manifest['recipe']==(ST_RECIPE if st else RECIPE),'spatial recipe differs')
    if st:
        require(manifest['family'] == 'st', 'special-teams family differs')
        _binding(manifest['basis_source'], 'special-teams basis source')
    digest(manifest['design_identity'])
    for key in ('prepared','coaches','valued'):_binding(manifest[key],key)
    previous=manifest['previous']
    if previous is not None:
        _closed(previous,('path','sha256','season','purpose','usage'),'spatial predecessor');_binding(previous,'spatial predecessor')
        require(previous['purpose']==expected_purpose and previous['season']==f'{year-1}{year}' and previous['usage']=='annual','invalid spatial predecessor chain')
    else:require(expected_purpose!='real' or manifest['season']=='20212022','missing real spatial predecessor')
    files=manifest['files'];require(type(files) is list and bool(files),'missing spatial member manifest')
    paths=[]
    for member in files:
        _closed(member,('role','path','sha256'),'spatial member');digest(member['sha256'])
        require(type(member['role']) is str and member['role'],'invalid spatial member role')
        path=_member(root,member['path']);require(identity(path)['sha256']==member['sha256'],'spatial member digest differs');paths.append(member['path'])
    require(len(paths)==len(set(paths)),'duplicate spatial members')
    roles={'design.json':'design','design.npz':'design_arrays','coverage.json':'coverage','reference.json':'reference',
           'diagnostics.json':'projection_diagnostics','projections.jsonl':'projections','adjustments.jsonl':'adjustments',
           'coefficient-support.jsonl':'coefficient_support','projections.npz':'projection_arrays',
           'annual-baseline-manifest.json':'annual_baseline_manifest','probes/baseline.json':'probe_baseline',
           'probes/rows.json':'probe_rows','probes/requirements.json':'probe_requirements'}
    if st:
        roles.update({'probes/joint-comparison.json':'probe_joint_comparison'})
    for head in HEADS:
        roles.update({f'heads/{head}.json':'head_metadata',f'heads/{head}.npz':'head_arrays',
                      f'probes/{head}.json':'probe_metadata',f'probes/{head}.npz':'probe_arrays',
                      **({f'probes/{head}-attempt.json':'probe_attempt'} if st else {}),
                      f'probes/{head}-comparison.json':'probe_comparison',f'probes/{head}-projections.npz':'probe_projections',
                      f'probes/{head}-projections.jsonl':'probe_projection_rows'})
    require(all(roles.get(member['path'])==member['role'] for member in files),'unknown or misidentified spatial member role')
    required={'design.json','design.npz','coverage.json','reference.json','diagnostics.json','projections.jsonl','adjustments.jsonl','coefficient-support.jsonl','projections.npz'}
    require(required<=set(paths),'incomplete spatial member set')
    expected_paths=set(required)
    require([row.get('head') for row in manifest['heads']]==list(HEADS),'spatial head axis/order differs')
    for descriptor in manifest['heads']:
        head=descriptor['head'];expected_paths.add(f'heads/{head}.json')
        if descriptor['arrays']:expected_paths.add(f'heads/{head}.npz')
    if 'probes/baseline.json' in paths:
        expected_paths|={'annual-baseline-manifest.json','probes/baseline.json','probes/rows.json','probes/requirements.json'}
        if st:
            expected_paths.add('probes/joint-comparison.json')
        for head in HEADS:
            expected_paths|={f'probes/{head}.json',f'probes/{head}-comparison.json'}
            if st:
                expected_paths.add(f'probes/{head}-attempt.json')
        require(expected_paths<=set(paths),'unbound required spatial probe/head member')
        for head in HEADS:
            if read_json(root/f'probes/{head}.json')['status']=='complete':
                expected_paths.add(f'probes/{head}.npz')
                comparison = read_json(root/f'probes/{head}-comparison.json')
                if (not st or all(row['status'] == 'complete' for row in manifest['heads'])
                        and comparison.get('reason') != 'diagnostic_projection_numerical_domain_failure'):
                    expected_paths|={f'probes/{head}-projections.npz',f'probes/{head}-projections.jsonl'}
    require(set(paths)==expected_paths,'spatial member inventory differs from complete head/probe statuses')
    unbound={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='manifest.json'}-set(paths)
    # an interrupted numerical continuation must leave its already accepted
    # annual state readable. its unbound progress is never consumed as evidence.
    require(not unbound or ('probes/baseline.json' not in paths and all(p.startswith('probes/') or p=='annual-baseline-manifest.json' for p in unbound)),
            'unlisted spatial member outside unfinished probe progress')
    document=read_json(root/'design.json')
    design_arrays=_read_arrays(root/'design.npz',document['arrays'])
    design=_restore_design(document,design_arrays,manifest['resources']['design'])
    require(isinstance(design, SpecialTeamsDesign) == st, 'spatial manifest/design family differs')
    if st:
        require(design.basis_source == manifest['basis_source'], 'special-teams basis source differs')
    require(design.transforms['design_sha256']==manifest['design_identity'] and design.basis_identity==manifest['basis_identity']
            and design.coverage==read_json(root/'coverage.json'),'spatial design/manifest/coverage identity differs')
    for key in ('prepared','coaches','valued','season','purpose','training_cutoff'):
        require(getattr(design,key)==manifest[key],'spatial design source/training binding differs')
    require([row['head'] for row in manifest['heads']]==list(HEADS),'spatial head axis/order differs')
    heads,head_arrays={},{}
    for descriptor in manifest['heads']:
        _closed(descriptor,('head','status','arrays'),'spatial head descriptor')
        head=descriptor['head'];require(f'heads/{head}.json' in paths,'unbound head metadata')
        metadata=read_json(root/f'heads/{head}.json')
        values=_read_arrays(root/f'heads/{head}.npz',descriptor['arrays']) if descriptor['arrays'] else {}
        require(metadata['head']==head and metadata['status']==descriptor['status'],'spatial head status differs')
        validate_head(metadata,values,design);heads[head]=metadata;head_arrays[head]=values
    rates_shape=(len(design.players),4,2,2,3,656) if st else (len(design.players),2,2,3,656)
    adjustment_shape=(len(design.players),4,2,2,7,656) if st else (len(design.players),2,2,7,656)
    projection_arrays=_read_arrays(root/'projections.npz',dict(rates=dict(shape=list(rates_shape),dtype='<f8'),adjustments=dict(shape=list(adjustment_shape),dtype='<f8')))
    state=SpatialState(root,manifest,design,heads,head_arrays,list(rows(root/'projections.jsonl')),projection_arrays,
                       list(rows(root/'adjustments.jsonl')),list(rows(root/'coefficient-support.jsonl')),read_json(root/'reference.json'))
    _validate_projections(state)
    if any(p.startswith('probes/') for p in paths):_validate_probes(state)
    return state


def _validate_probes(state):
    from .spatial_rates import HEADS, compare_probe, probe_descriptor, select_probe_rows
    root=state.path/'probes'
    baseline=read_json(root/'baseline.json')
    require(baseline==probe_descriptor(state),'probe baseline differs from immutable annual coefficients')
    annual=read_json(state.path/'annual-baseline-manifest.json')
    require(all(annual[key]==state.manifest[key] for key in (ST_MANIFEST_KEYS if isinstance(state.design, SpecialTeamsDesign) else MANIFEST_KEYS) if key not in ('files','resources'))
            and all(member in state.manifest['files'] for member in annual['files']),'frozen accepted annual baseline differs')
    selected=read_json(root/'rows.json')
    require(type(selected) is list and len(selected)<=256 and selected==select_probe_rows(state),'invalid frozen numerical probe row keys/selection')
    st = isinstance(state.design, SpecialTeamsDesign)
    names = ([f'state:{strength}:{role}' for strength in ST_STATES for role in ROLES] if st else []) + ['boundary_goals','missing_optional_inputs','entries','returns','trades','sparse_support']
    variants, variant_arrays = dict(state.heads), dict(state.head_arrays)
    all_variants = True
    requirements=[dict(requirement=name,disposition='actual' if any(name in row['requirements'] for row in selected) else 'no_matching_context',
                      key=next((row['key'] for row in selected if name in row['requirements']),None))
                  for name in names]
    require(read_json(root/'requirements.json')==requirements,'frozen probe requirement dispositions differ')
    for head in HEADS:
        metadata=read_json(root/f'{head}.json');comparison=read_json(root/f'{head}-comparison.json')
        require(metadata['head']==head,'probe head identity differs')
        contract={'coefficients':dict(shape=list(state.head_arrays[head]['coefficients'].shape),dtype='<f8')} if metadata['status']=='complete' else {}
        arrays=_read_arrays(root/f'{head}.npz',contract) if metadata['status']=='complete' else {}
        validate_head(metadata,arrays,state.design)
        if st:
            attempt = read_json(root / f'{head}-attempt.json')
            _closed(attempt, ('status', 'reason'), 'special-teams probe attempt')
            expected_attempt = dict(status='attempted', reason=None) if state.heads[head]['status'] == 'complete' else dict(status='not_run', reason='baseline_head_not_complete')
            require(attempt == expected_attempt, 'special-teams continuation attempt differs from baseline status')
            all_variants &= (attempt['status'] == 'attempted' and metadata['status'] == 'complete'
                             and comparison.get('reason') != 'diagnostic_projection_numerical_domain_failure')
            if arrays:
                variants[head], variant_arrays[head] = metadata, arrays
        if arrays and (not st or all(value['status'] == 'complete' for value in state.heads.values())
                       and comparison.get('reason') != 'diagnostic_projection_numerical_domain_failure'):
            from dataclasses import replace
            from .spatial_rates import project_spatial
            heads=dict(state.heads);heads[head]=metadata
            head_arrays=dict(state.head_arrays);head_arrays[head]=arrays
            changed=project_spatial(replace(state,heads=heads,head_arrays=head_arrays),actual_context=False)
            saved=_read_arrays(root/f'{head}-projections.npz',{'rates':dict(shape=list(changed.arrays['rates'].shape),dtype='<f8')})
            require(np.array_equal(saved['rates'],changed.arrays['rates']) and list(rows(root/f'{head}-projections.jsonl'))==changed.rows,'saved probe projection differs')
        require(metadata['solver'] is None or metadata['solver']['options']==RECIPE['continuation']
                or st and attempt['status']=='not_run' and metadata == state.heads[head], 'probe stopping differs')
        expected=compare_probe(state,head,metadata,arrays,selected)
        if st and state.heads[head]['status'] != 'complete':
            expected = dict(status='unassessed', reason='baseline_head_not_complete', maxima=None,
                failures=[dict(head=head, reasons=state.heads[head]['reasons'])])
        require(expected==comparison,'numerical probe maxima/locators differ')
    if st:
        from dataclasses import replace
        from .spatial_rates import _compare_st_variant
        expected = (_compare_st_variant(state, replace(state, heads=variants, head_arrays=variant_arrays), selected)
                    if all_variants else dict(status='unassessed', reason='one_or_more_continuations_unavailable', maxima=None, failures=[]))
        require(read_json(root / 'joint-comparison.json') == expected, 'joint special-teams probe comparison differs')


def bind_spatial_probes(state,probes):
    """extend final evidence after preserving the independently readable baseline."""
    root=state.path
    baseline_path=root/'annual-baseline-manifest.json'
    with baseline_path.open('xb') as destination:
        destination.write((root/'manifest.json').read_bytes())
    manifest=dict(state.manifest)
    files=list(manifest['files'])+[dict(role='annual_baseline_manifest',path=baseline_path.name,sha256=identity(baseline_path)['sha256'])]
    for path in ('probes/baseline.json','probes/rows.json','probes/requirements.json'):
        files.append(dict(role='probe_baseline' if path.endswith('baseline.json') else 'probe_requirements' if path.endswith('requirements.json') else 'probe_rows',path=path,sha256=identity(root/path)['sha256']))
    if isinstance(state.design, SpecialTeamsDesign):
        files.append(dict(role='probe_joint_comparison', path='probes/joint-comparison.json', sha256=identity(root/'probes/joint-comparison.json')['sha256']))
    for head in HEADS:
        if isinstance(state.design, SpecialTeamsDesign):
            path=f'probes/{head}-attempt.json'
            files.append(dict(role='probe_attempt', path=path, sha256=identity(root/path)['sha256']))
        for suffix,role in (('.json','probe_metadata'),('.npz','probe_arrays'),('-comparison.json','probe_comparison'),('-projections.npz','probe_projections'),('-projections.jsonl','probe_projection_rows')):
            path=f'probes/{head}{suffix}'
            if (root/path).exists():files.append(dict(role=role,path=path,sha256=identity(root/path)['sha256']))
    manifest['files']=files
    manifest['resources']=dict(manifest['resources'],probe_wall_seconds=sum(probes['heads'][h]['metadata']['resources']['wall_seconds'] for h in HEADS),
                               output_bytes=sum((root/member['path']).stat().st_size for member in files))
    temporary=root/'manifest-final.json'
    write_json(temporary,manifest)
    temporary.replace(root/'manifest.json')
    return read_spatial_state(root,manifest['purpose'], expected_family='st' if isinstance(state.design, SpecialTeamsDesign) else 'ev')
