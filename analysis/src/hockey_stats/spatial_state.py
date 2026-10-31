"""strict detached annual positive-spatial artifacts and numerical probes."""

from dataclasses import dataclass, fields
import hashlib
import json
import math
from pathlib import Path
import re
from time import perf_counter

import numpy as np
from scipy.sparse import csr_matrix

from .artifacts import digest, ordered_array_digest, require, rows, write_arrays, write_json
from .captures import InputContractError
from .chance_cli import identity, read_json
from .spatial_design import SpatialDesign, RECIPE as DESIGN_RECIPE, CONTEXT_AXES, _actor_columns
from .spatial_rates import HEADS, ROLES, QUANTITIES, ADJUSTMENTS, RECIPE, annual_priors, centered_reference, _conditional_mean, _unpack

CORE_ARRAYS=('basis','exposure_hours','event_offsets','origin_cells','origin_weights','neutral_goal_probability','context_time','context_event')
DESIGN_ARRAYS=CORE_ARRAYS+(
               'X_time_data','X_time_indices','X_time_indptr','X_time_shape',
               'X_event_data','X_event_indices','X_event_indptr','X_event_shape')
MANIFEST_KEYS='schema_version kind purpose season recipe_id recipe design_identity implementation prepared coaches valued previous basis_identity training_cutoff heads files resources'.split()
HEAD_KEYS='head status reasons priors ledger centers reference_predictor objective solver diagnostics resources'.split()


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


def _arrays(design):
    result={name:np.asarray(getattr(design,name)) for name in CORE_ARRAYS}
    for name in ('X_time','X_event'):
        matrix=getattr(design,name).tocsr()
        result.update({name+'_data':np.asarray(matrix.data,dtype=np.float64),
                       name+'_indices':np.asarray(matrix.indices,dtype=np.int64),
                       name+'_indptr':np.asarray(matrix.indptr,dtype=np.int64),
                       name+'_shape':np.asarray(matrix.shape,dtype=np.int64)})
    return result


def _design_document(design, arrays):
    excluded=set(CORE_ARRAYS)|{'X_time','X_event','resources'}
    body={field.name:getattr(design,field.name) for field in fields(SpatialDesign) if field.name not in excluded}
    for key in ('players','coach_ids','columns','time_keys','event_keys'):
        body[key]=list(body[key])
    return dict(schema_version=1,kind='spatial_design',definition=body,
                arrays=_array_contract(arrays),array_digest=ordered_array_digest(arrays))


def design_identity(design):
    arrays=_arrays(design)
    body=_design_document(design,arrays)
    return hashlib.sha256(json.dumps(body,allow_nan=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


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
    require(document['schema_version']==1 and document['kind']=='spatial_design','invalid spatial design schema')
    require(list(arrays)==list(DESIGN_ARRAYS) and document['array_digest']==ordered_array_digest(arrays),'spatial design array identity differs')
    body=dict(document['definition'])
    expected={field.name for field in fields(SpatialDesign)}-set(CORE_ARRAYS)-{'X_time','X_event','resources'}
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
    design=SpatialDesign(**body)
    validate_design(design)
    return design


def validate_design(design):
    """saved source identities and exact finite designs suffice without upstream io."""
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
    require(design.recipe==DESIGN_RECIPE,'spatial fixed design definition differs')
    columns=design.columns
    expected_columns=_actor_columns(design.players,design.coach_ids)+[dict(kind='context',name=axis['name']) for axis in CONTEXT_AXES]
    require(list(columns)==expected_columns,'spatial fixed column order/definition differs')
    _closed(design.transforms,('axes','design_sha256'),'spatial transforms')
    require(len(design.transforms['axes'])==len(CONTEXT_AXES),'spatial transform axis cardinality differs')
    total_hours=float(design.exposure_hours.sum())
    for axis,transform in zip(CONTEXT_AXES,design.transforms['axes'],strict=True):
        require({key:transform[key] for key in axis}==axis and set(transform)==set(axis)|{'location','scale','available_hours','missing_hours'},'spatial transform axis definition differs')
        require(all(type(transform[key]) in (int,float) and math.isfinite(transform[key]) for key in ('location','scale','available_hours','missing_hours'))
                and transform['scale']>0 and transform['available_hours']>=0 and transform['missing_hours']>=-1e-12
                and abs(transform['available_hours']+transform['missing_hours']-total_hours)<1e-9,
                'invalid spatial transform moments')
        require(axis['continuous'] or transform['scale']==1.,'categorical contrast was scaled')
        require(transform['available_hours']>0 or (transform['location']==0 and transform['scale']==1),'all-absent context has invented moments')
    expected_transform_hash=hashlib.sha256(json.dumps(dict(recipe=DESIGN_RECIPE['sha256'],columns=columns,transforms={'axes':design.transforms['axes']}),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    require(design.transforms['design_sha256']==expected_transform_hash,'spatial design definition digest differs')
    require(bool(columns) and columns[0]==dict(kind='intercept',name='intercept'),'invalid spatial intercept')
    require(len({c['name'] for c in columns})==len(columns),'duplicate spatial columns')
    actor_keys=set()
    for column in columns[1:]:
        if column['kind']=='actor':
            _closed(column,('kind','name','block','id','subblock'),'actor column')
            require(column['block'] in ('attacking_player','defending_player','attacking_coach','defending_coach'),'invalid actor block')
            if column['block'].endswith('_player'):
                require(column['id'] in players and column['subblock']=='base','invalid spatial player coordinate')
            else:
                require(column['id'] in design.coach_ids and column['subblock'] in ('base','score:-2','score:-1','score:0','score:1','score:2','shell'),'invalid spatial coach coordinate')
            key=(column['block'],column['id'],column['subblock']);require(key not in actor_keys,'duplicate spatial actor');actor_keys.add(key)
        else:
            _closed(column,('kind','name'),'context column');require(column['kind']=='context','invalid spatial column kind')
    expected={(side+'_player',p,'base') for side in ('attacking','defending') for p in players}
    expected|={(side+'_coach',c,g) for side in ('attacking','defending') for c in design.coach_ids
               for g in ('base','score:-2','score:-1','score:0','score:1','score:2','shell')}
    require(actor_keys==expected,'spatial actor axes omit or invent roster/gate coordinates')
    n=len(design.exposure_hours);ne=len(design.event_offsets)-1;d=len(columns)
    actor_count=len(_actor_columns(design.players,design.coach_ids))
    require(design.X_time.shape==(n,actor_count) and design.X_event.shape==(ne,actor_count),'spatial actor matrix dimensions differ')
    require(design.context_time.shape==(n,d-actor_count) and design.context_event.shape==(ne,d-actor_count)
            and design.context_time.dtype==design.context_event.dtype==np.dtype('float64')
            and np.isfinite(design.context_time).all() and np.isfinite(design.context_event).all(),'invalid spatial dense context matrices')
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
        require(matrix.dtype==np.dtype('float64') and matrix.has_canonical_format and np.isfinite(matrix.data).all(),'invalid finite spatial sparse matrix')
        require(np.all(np.asarray(matrix[:,0].toarray()).ravel()==1),'spatial intercept incidence differs')
    actors={key:i for i,c in enumerate(columns) if c['kind']=='actor' for key in [(c['block'],c['id'],c['subblock'])]}
    for matrix,keys,label in ((design.X_time,design.time_keys,'elapsed'),(design.X_event,design.event_keys,'event')):
        seen=set()
        for i,key in enumerate(keys):
            require(type(key) is dict and {'game_id','segment_index','chunk_index','source_index','attacking_side','attacking_players','defending_players'}<=key.keys(),'missing spatial source locator')
            locator=(key['game_id'],key['segment_index'],key['chunk_index'],key['source_index'],key['attacking_side'])
            require(locator not in seen,'duplicate spatial source row');seen.add(locator)
            require(key['attacking_side'] in ('home','away'),'invalid directed spatial side')
            for side in ('attacking','defending'):
                members=key[side+'_players']
                require(type(members) is list and len(members)==len(set(members))==5 and set(members)<=set(players),'invalid physical five-skater membership')
                expected_indices={actors[(side+'_player',p,'base')] for p in members}
                row=matrix[i]
                actual={int(j) for j,v in zip(row.indices,row.data) if columns[j].get('block')==side+'_player' and v!=0}
                require(actual==expected_indices and all(matrix[i,j]==1 for j in actual),'spatial membership/actor design differs')
            require(set(key['attacking_players']).isdisjoint(key['defending_players']),'player on both directed sides')
    basis=design.basis
    require(type(basis) is np.ndarray and basis.dtype==np.dtype('float64') and basis.shape==(656,40) and np.isfinite(basis).all(),'invalid native forty-mode basis')
    require(np.max(np.abs(basis.mean(axis=0)))<1e-10 and np.allclose(basis.T@basis/656,np.eye(40),atol=1e-10,rtol=0),'uniform basis is not centered orthonormal')
    _finite(design.basis_identity,'basis identity')
    require(design.basis_identity.get('array_sha256')==ordered_array_digest({'basis':basis}),'native basis byte identity differs')
    for value in design.basis_identity.values():
        if type(value) is str and len(value)==64: digest(value)
    offsets=design.annual_offsets;_closed(offsets,('r','pi','qbar'),'annual offsets')
    require(type(offsets['r']) in (int,float) and math.isfinite(offsets['r']) and offsets['r']>0,'invalid annual rate offset')
    pi=np.asarray(offsets['pi']);q=np.asarray(offsets['qbar'])
    require(pi.shape==q.shape==(656,) and np.isfinite(pi).all() and np.isfinite(q).all()
            and np.all(pi>0) and abs(pi.sum()-1)<1e-12 and np.all((q>0)&(q<1)),'invalid annual spatial offsets')
    mass=np.bincount(design.origin_cells,weights=design.origin_weights,minlength=656)
    neutral=np.bincount(design.origin_cells,weights=design.origin_weights*design.neutral_goal_probability,minlength=656)
    expected_pi=(mass+10*(mass+1/656)/(ne+1))/(ne+10)
    hours=float(design.exposure_hours.sum());expected_r=(ne+(ne+1)/(hours+1))/(hours+1)
    qm=(neutral.sum()+10*(neutral.sum()+.5)/(ne+1))/(ne+10)
    expected_q=(neutral+10*expected_pi*qm)/(mass+10*expected_pi)
    require(abs(offsets['r']-expected_r)<1e-12*(1+expected_r) and np.allclose(pi,expected_pi,atol=1e-14,rtol=1e-12)
            and np.allclose(q,expected_q,atol=1e-14,rtol=1e-12),'annual offsets differ from retained target/exposure')
    require(design.coverage['attempts']==ne and abs(design.coverage['origin_mass']-ne)<1e-9
            and abs(design.coverage['directed_included_hours']-hours)<1e-9
            and abs(2*design.coverage['physical_included_hours']-hours)<1e-9,'spatial coverage mass/time identity differs')
    digest(design.transforms['design_sha256'])


def validate_head(metadata, arrays, design):
    _closed(metadata,HEAD_KEYS,'spatial head');_finite(metadata,'spatial head')
    head=metadata['head'];require(head in HEADS,'invalid spatial head')
    require(metadata['status'] in ('complete','failed','unavailable'),'invalid spatial head status')
    require(type(metadata['reasons']) is list and all(type(r) is str and r for r in metadata['reasons']),'invalid head reasons')
    require((metadata['status']=='complete')==(not bool(metadata['reasons'])),'spatial head reason/status differs')
    prior_rows=metadata['priors'];require(type(prior_rows) is list,'missing spatial priors')
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
    ledger={(row['block'],row['id'],row['subblock']):row for row in metadata['ledger']}
    require(len(ledger)==len(metadata['ledger']),'duplicate spatial carry ledger')
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


def write_spatial_state(state, projections, *, probes=None):
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
    if probes is not None:
        folder=root/'probes';folder.mkdir()
        write_json(folder/'baseline.json',probes['baseline']);write_json(folder/'rows.json',probes['rows'])
        members.extend((('probe_baseline','probes/baseline.json'),('probe_rows','probes/rows.json')))
        for head in HEADS:
            probe=probes['heads'][head]
            write_json(folder/f'{head}.json',probe['metadata'])
            if probe['arrays']: write_arrays(folder,f'{head}.npz',probe['arrays'])
            write_json(folder/f'{head}-comparison.json',probe['comparison'])
            members.extend((('probe_metadata',f'probes/{head}.json'),('probe_comparison',f'probes/{head}-comparison.json')))
            if probe['arrays']:members.append(('probe_arrays',f'probes/{head}.npz'))
    manifest=dict(state.manifest)
    manifest['heads']=head_rows
    manifest['files']=[dict(role=role,path=path,sha256=identity(root/path)['sha256']) for role,path in members]
    manifest['resources']=dict(manifest['resources'],projection=projections.diagnostics,
                               output_bytes=sum((root/path).stat().st_size for _,path in members),
                               write_wall_seconds=perf_counter()-began)
    write_json(root/'manifest.json',manifest)
    return read_spatial_state(root,manifest['purpose'])


def _validate_projections(state):
    from .spatial_rates import project_spatial
    expected=project_spatial(state,actual_context=False)
    require(state.projections==expected.rows and state.reference==expected.reference,'saved spatial standardized projection/reference differs')
    require(state.coefficient_support==expected.coefficient_support,'saved spatial head-support records differ')
    arrays=state.projection_arrays
    require(set(arrays)=={'rates','adjustments'} and arrays['rates'].shape==expected.arrays['rates'].shape
            and np.array_equal(arrays['rates'],expected.arrays['rates']),'saved native spatial contrast differs')
    adjustment_maps=arrays['adjustments']
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
                require(all(abs(row[q][name]-float(values[k].sum()))<=1e-11*(1+abs(row[q][name])) for k,name in enumerate(ADJUSTMENTS)),
                        'adjustment map/scalar identity differs')
                residual=values[6]-values[:5].sum(axis=0)
                require(np.all(np.abs(residual-values[5])<=1e-10*(1+np.abs(values[6])+np.abs(values[:6]).sum(axis=0))),
                        'saved adjustment closure differs')
            else:
                require(row['reason']!='no_exposure' or row['exposure_seconds']==0,'no-exposure adjustment has physical time')
                require(type(row['reason']) is str and row['reason'] and all(v is None for v in row[q].values())
                        and np.all(adjustment_maps[i,r,qi]==0),'unavailable adjustment fabricates rates')


def read_spatial_state(path,expected_purpose):
    began=perf_counter();root=Path(path).resolve(strict=True)
    if root.is_file():require(root.name=='manifest.json','expected spatial manifest');root=root.parent
    manifest=read_json(root/'manifest.json');_closed(manifest,MANIFEST_KEYS,'spatial manifest');_finite(manifest,'spatial manifest')
    require(manifest['schema_version']==1 and manifest['kind']=='spatial_state' and manifest['purpose']==expected_purpose
            and expected_purpose in ('real','fixture'),'invalid spatial state schema/purpose')
    year=_season(manifest['season'])
    require(manifest['recipe_id']=='experimental-v1' and manifest['recipe']==RECIPE,'spatial recipe differs')
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
    required={'design.json','design.npz','coverage.json','reference.json','diagnostics.json','projections.jsonl','adjustments.jsonl','coefficient-support.jsonl','projections.npz'}
    require(required<=set(paths),'incomplete spatial member set')
    document=read_json(root/'design.json')
    design_arrays=_read_arrays(root/'design.npz',document['arrays'])
    design=_restore_design(document,design_arrays,manifest['resources']['design'])
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
    rates_shape=(len(design.players),2,2,3,656);adjustment_shape=(len(design.players),2,2,7,656)
    projection_arrays=_read_arrays(root/'projections.npz',dict(rates=dict(shape=list(rates_shape),dtype='<f8'),adjustments=dict(shape=list(adjustment_shape),dtype='<f8')))
    state=SpatialState(root,manifest,design,heads,head_arrays,list(rows(root/'projections.jsonl')),projection_arrays,
                       list(rows(root/'adjustments.jsonl')),list(rows(root/'coefficient-support.jsonl')),read_json(root/'reference.json'))
    _validate_projections(state)
    if any(p.startswith('probes/') for p in paths):_validate_probes(state)
    return state


def _validate_probes(state):
    from .spatial_rates import HEADS, compare_probe, probe_descriptor
    root=state.path/'probes'
    baseline=read_json(root/'baseline.json')
    require(baseline==probe_descriptor(state),'probe baseline differs from immutable annual coefficients')
    selected=read_json(root/'rows.json')
    require(type(selected) is list and len(selected)<=256,'invalid frozen numerical probe rows')
    for head in HEADS:
        metadata=read_json(root/f'{head}.json');comparison=read_json(root/f'{head}-comparison.json')
        require(metadata['head']==head,'probe head identity differs')
        contract={'coefficients':dict(shape=list(state.head_arrays[head]['coefficients'].shape),dtype='<f8')}
        arrays=_read_arrays(root/f'{head}.npz',contract) if metadata['status']=='complete' else {}
        validate_head(metadata,arrays,state.design)
        if arrays:
            from dataclasses import replace
            from .spatial_rates import project_spatial
            heads=dict(state.heads);heads[head]=metadata
            head_arrays=dict(state.head_arrays);head_arrays[head]=arrays
            changed=project_spatial(replace(state,heads=heads,head_arrays=head_arrays),actual_context=False)
            saved=_read_arrays(root/f'{head}-projections.npz',{'rates':dict(shape=list(changed.arrays['rates'].shape),dtype='<f8')})
            require(np.array_equal(saved['rates'],changed.arrays['rates']) and list(rows(root/f'{head}-projections.jsonl'))==changed.rows,'saved probe projection differs')
        require(metadata['solver'] is None or metadata['solver']['options']==RECIPE['continuation'],'probe stopping differs')
        expected=compare_probe(state,head,metadata,arrays,selected)
        require(expected==comparison,'numerical probe maxima/locators differ')


def bind_spatial_probes(state,probes):
    """extend final evidence after preserving the independently readable baseline."""
    root=state.path
    baseline_path=root/'annual-baseline-manifest.json'
    with baseline_path.open('xb') as destination:
        destination.write((root/'manifest.json').read_bytes())
    manifest=dict(state.manifest)
    files=list(manifest['files'])+[dict(role='annual_baseline_manifest',path=baseline_path.name,sha256=identity(baseline_path)['sha256'])]
    for path in ('probes/baseline.json','probes/rows.json'):
        files.append(dict(role='probe_baseline' if path.endswith('baseline.json') else 'probe_rows',path=path,sha256=identity(root/path)['sha256']))
    for head in HEADS:
        for suffix,role in (('.json','probe_metadata'),('.npz','probe_arrays'),('-comparison.json','probe_comparison'),('-projections.npz','probe_projections'),('-projections.jsonl','probe_projection_rows')):
            path=f'probes/{head}{suffix}'
            if (root/path).exists():files.append(dict(role=role,path=path,sha256=identity(root/path)['sha256']))
    manifest['files']=files
    manifest['resources']=dict(manifest['resources'],probe_wall_seconds=sum(probes['heads'][h]['metadata']['resources']['wall_seconds'] for h in HEADS))
    temporary=root/'manifest-final.json'
    write_json(temporary,manifest)
    temporary.replace(root/'manifest.json')
    return read_spatial_state(root,manifest['purpose'])
