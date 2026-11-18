"""finite two-head territory artifacts, independent of raw source availability."""
from dataclasses import dataclass, fields
from pathlib import Path
from math import isfinite
from time import perf_counter

import numpy as np
from scipy.sparse import csr_matrix

from .input_locations import input_path, same_input_reference
from .artifacts import (require,require_fields,require_number,require_season_label,digest,
    write_json,write_jsonl,write_arrays,load_arrays,ordered_array_digest,json_values,rows,implementation)
from .chance_cli import identity,read_json
from .territory_design import TerritoryDesign,TerritoryHeadDesign,TERRITORY_RECIPE,CONTEXT_AXES
from .territory import (HEADS,territory_recipe,annual_territory_priors,project_hazards,close,smooth_nuisance,
    center_head,territory_objective,_actor_key)
from .execution_state import require_state_reference,state_member_path

MANIFEST_KEYS='schema_version kind purpose season recipe design_identity implementation prepared coaches previous training_cutoff heads files resources'.split()
HEAD_KEYS='status reasons priors ledger centers reference objective solver diagnostics'.split()
ARRAYS=('context_time','context_event','exposure_seconds','event_counts')


@dataclass(frozen=True)
class TerritoryState:
    path: Path
    manifest: dict
    heads: dict
    design: TerritoryDesign | None
    coefficients: dict
    probes: dict
    projections: list
    support: list
    coverage: dict


def _finite(value):
    if isinstance(value,dict):
        for child in value.values():_finite(child)
    elif isinstance(value,(tuple,list)):
        for child in value:_finite(child)
    elif isinstance(value,float):require(isfinite(value),'nonfinite territory document')


def validate_design(design):
    require(design.purpose in ('real','fixture'),'invalid territory purpose');require_season_label(design.season)
    require(design.recipe==TERRITORY_RECIPE,'territory source recipe differs')
    require(set(design.heads)==set(HEADS),'territory head axes differ')
    require(tuple(sorted(set(design.players)))==tuple(design.players) and set(design.player_facts)==set(design.players),
            'territory player axis differs')
    require(set(design.coverage['players'])==set(design.players),'territory qualification axis differs')
    for source in ('prepared','coaches'):
        binding=getattr(design,source);require_state_reference(binding,'territory '+source)
        require_fields(binding,('path','sha256','purpose','members') if source=='prepared' else
            ('path','sha256','purpose','selected_game_ids'),'territory '+source+' binding')
        require(binding['purpose']==design.purpose,'territory input purpose differs')
    for name,head in design.heads.items():
        require(head.season==design.season,'territory head season differs')
        require(head.X_time.shape[0]==len(head.exposure_seconds)==len(head.time_keys)
            and head.X_event.shape[0]==len(head.event_counts)==len(head.event_keys),'territory response rows differ')
        width=head.X_time.shape[1];context=len(head.columns)-width
        require(head.X_event.shape[1]==width and head.context_time.shape==(len(head.exposure_seconds),context)
            and head.context_event.shape==(len(head.event_counts),context),'territory feature axes differ')
        require(head.exposure_seconds.ndim==head.event_counts.ndim==1 and np.all(head.exposure_seconds>0)
            and np.all(head.event_counts>0) and np.all(head.event_counts==np.floor(head.event_counts)),
            'invalid territory seconds/crossings')
        require(len(head.exposure_seconds)>0 or not len(head.event_counts),'territory crossings lack risk')
        require(len({col['name'] for col in head.columns})==len(head.columns) and head.columns[0]['kind']=='intercept',
                'territory column axis differs')
        from .elapsed_design import actor_columns
        actors=[col for col in actor_columns(design.players,design.coach_ids)
            if col.get('kind')!='actor' or col.get('subblock')=='base']
        expected=tuple(actors+[dict(kind='context',name=axis['name']) for axis in CONTEXT_AXES])
        require(head.columns==expected,'territory declared actor/context recipe differs')
        require_fields(head.transforms,('axes','design_sha256'),'territory transforms')
        require(len(head.transforms['axes'])==len(CONTEXT_AXES),'territory context transform axis differs')
        for axis,transform in zip(CONTEXT_AXES,head.transforms['axes'],strict=True):
            require_fields(transform,(*axis.keys(),'location','scale','available_seconds','missing_seconds'),'territory context transform')
            require(all(transform[key]==value for key,value in axis.items()) and transform['scale']==1.,
                    'territory categorical scale differs')
            require_number(transform['location'],'territory context location');require_number(transform['available_seconds'],'territory context risk',low=0)
            require_number(transform['missing_seconds'],'territory context missing risk',low=0)
        digest(head.transforms['design_sha256'])
        for matrix in (head.X_time,head.X_event):
            require(isinstance(matrix,csr_matrix),'territory actor matrix is not csr');matrix.check_format(full_check=True)
            require(matrix.has_canonical_format and np.isfinite(matrix.data).all() and np.all(matrix.data>=0),
                    'invalid territory sparse matrix')
            require(np.array_equal(np.asarray(matrix[:,0].todense()).ravel(),np.ones(matrix.shape[0])),
                    'territory intercept differs')
            for role in ('attacking_player','defending_player'):
                indices=[i for i,col in enumerate(head.columns[:width]) if col['kind']=='actor' and col['block']==role]
                require({str(head.columns[i]['id']) for i in indices}==set(design.players),'territory actor roster differs')
                require(np.all(np.asarray(matrix[:,indices].sum(axis=1)).ravel()==5),'territory player slots differ')
        for array in (head.context_time,head.context_event,head.exposure_seconds,head.event_counts):
            require(array.dtype.kind in 'iuf' and np.isfinite(array).all(),'nonfinite territory design array')
        annual_territory_priors(design,head,[])
    smooth_nuisance(design.nuisance)
    _finite(json_values(design.coverage))


def _head_arrays(head):
    arrays={key:np.asarray(getattr(head,key)) for key in ARRAYS}
    for kind in ('time','event'):
        matrix=getattr(head,'X_'+kind)
        for part in ('data','indices','indptr'):arrays[f'X_{kind}_{part}']=getattr(matrix,part)
        arrays[f'X_{kind}_shape']=np.array(matrix.shape,dtype=np.int64)
    return arrays


def _design_document(root,design):
    document={field.name:json_values(getattr(design,field.name)) for field in fields(TerritoryDesign)
        if field.name not in ('heads','nuisance','coverage')}
    document['heads']={}
    digests={}
    for name in HEADS:
        head=design.heads[name];arrays=_head_arrays(head)
        doc={field.name:json_values(getattr(head,field.name)) for field in fields(TerritoryHeadDesign)
            if field.name not in (*ARRAYS,'X_time','X_event')}
        doc['arrays']=write_arrays(root,name+'-design.npz',arrays)
        document['heads'][name]=doc;digests[name]=ordered_array_digest(arrays)
    write_json(root/'design.json',document)
    return dict(metadata=identity(root/'design.json')['sha256'],arrays=digests)


def write_territory_state(root,design,previous,heads,coefficients,probes,projections,support,resources):
    validate_design(design);began=perf_counter();root=root.resolve();root.mkdir(parents=True,exist_ok=False)
    design_identity=_design_document(root,design)
    write_json(root/'heads.json',heads);write_json(root/'nuisance.json',json_values(design.nuisance))
    write_json(root/'coverage.json',json_values(design.coverage));write_jsonl(root/'projections.jsonl',projections)
    write_jsonl(root/'support.jsonl',support)
    coefficient_doc=None if not coefficients else write_arrays(root,'coefficients.npz',coefficients)
    probe_doc={}
    for name,probe in probes.items():
        probe_doc[name]=dict(head=probe['head'],reason=probe['reason'],arrays=None if probe['coefficients'] is None else
            write_arrays(root,name+'-probe.npz',dict(coefficients=probe['coefficients'])))
    write_json(root/'numerical.json',dict(coefficients=coefficient_doc,probes=probe_doc))
    filenames=['design.json','entry-design.npz','exit-design.npz','heads.json','nuisance.json','coverage.json',
        'projections.jsonl','support.jsonl','numerical.json']
    if coefficients:filenames.append('coefficients.npz')
    filenames.extend(name+'-probe.npz' for name,probe in probes.items() if probe['coefficients'] is not None)
    members=[dict(path=name,sha256=identity(root/name)['sha256'],bytes=(root/name).stat().st_size) for name in filenames]
    previous_binding=None if previous is None else dict(**identity(previous.path/'manifest.json'),season=previous.manifest['season'],
        purpose=previous.manifest['purpose'],recipe_sha256=previous.manifest['recipe']['sha256'])
    manifest=dict(schema_version=1,kind='territory_state',purpose=design.purpose,season=design.season,
        recipe=territory_recipe(design.recipe),design_identity=design_identity,implementation=implementation(),prepared=design.prepared,
        coaches=design.coaches,previous=previous_binding,training_cutoff=design.training_cutoff,
        heads={name:dict(status=heads[name]['status'],path='heads.json') for name in HEADS},files=members,
        resources=dict(resources,write_wall_seconds=perf_counter()-began,output_bytes=sum(row['bytes'] for row in members)))
    write_json(root/'manifest.json',manifest)
    return read_territory_state(root,design.purpose)


def _validate_head(head,manifest,name,*,diagnostic=False):
    require_fields(head,HEAD_KEYS,'territory head')
    require(head['status'] in ('complete','failed','unavailable') and head['status']==manifest['heads'][name]['status'],
            'territory head status differs')
    require(type(head['reasons']) is list and all(type(v) is str and v for v in head['reasons'])
        and (not head['reasons'])==(head['status']=='complete'),'territory head reasons differ')
    keys=set()
    for row in head['ledger']:
        require_fields(row,('block','id','subblock','coefficient','season','support_seasons'),'territory ledger')
        key=(row['block'],row['id'],row['subblock'])
        require(key not in keys and row['block'] in ('attacking_player','defending_player','attacking_coach','defending_coach')
            and type(row['id']) is str and row['id'] and row['subblock']=='base','invalid territory ledger actor');keys.add(key)
        require_number(row['coefficient'],'territory history coefficient');require_season_label(row['season'])
        years=row['support_seasons']
        require(type(years) is list and years==sorted(set(years)) and years and years[-1]==row['season']
            and all(year<=manifest['season'] for year in years),'territory history chronology differs')
        for year in years:require_season_label(year)
    prior_keys=set()
    for row in head['priors']:
        require_fields(row,('index','block','id','subblock','information_weight','likelihood_events','current_season_information',
            'prior_only','prior_kind','prior_anchor_season','prior_seasons','mean','precision'),'territory prior')
        key=(row['block'],row['id'],row['subblock'])
        require(key not in prior_keys and type(row['index']) is int and row['index']>=0,'duplicate territory prior');prior_keys.add(key)
        require_number(row['information_weight'],'territory prior risk',low=0)
        require(type(row['likelihood_events']) is int and row['likelihood_events']>=0,'invalid territory prior crossings')
        require(type(row['current_season_information']) is bool and type(row['prior_only']) is bool
            and row['current_season_information']==(row['information_weight']>0) and row['prior_only']!=row['current_season_information']
            and (row['information_weight']>0 or row['likelihood_events']==0),'territory prior information differs')
        require(row['prior_kind'] in ('entry','carry'),'invalid territory prior kind')
        years=row['prior_seasons'];require(years==sorted(set(years)) and all(year<manifest['season'] for year in years),'invalid territory prior years')
        require((row['prior_anchor_season'] is None and not years) if row['prior_kind']=='entry' else
            (years and row['prior_anchor_season']==years[-1]),'territory prior anchor differs')
        require_number(row['mean'],'territory prior mean');require_number(row['precision'],'territory prior precision',low=0)
        require(row['precision']>0,'territory prior precision is zero')
    if head['status']=='complete':
        require(head['solver'] is not None and head['solver']['converged'] is True and head['reference'] is not None
            and head['centers'] is not None and head['diagnostics'] is not None,'completed territory head lacks numerical evidence')
        require_fields(head['reference'],('log_rate','neutral_predictor','neutral_per_second','units','player_slots_per_side','context'),
            'territory hazard reference')
        require(head['reference']['units']=='crossings_per_second' and head['reference']['player_slots_per_side']==5,
                'territory reference units/slots differ')
        require_number(head['reference']['neutral_per_second'],'territory neutral rate',low=0)
        require(head['reference']['neutral_per_second']>0,'territory neutral rate is zero')
    else:require(head['centers'] is None and head['reference'] is None,'incomplete territory head has complete reference')
    if head['solver'] is not None:
        from .player_mechanisms import SOLVER,CONTINUATION
        solver=head['solver']
        require_fields(solver,('converged','status','termination','iterations','evaluations','objective','options','gradient_inf_norm',
            'achieved_gtol','wall_seconds','peak_memory_bytes'),'territory solver')
        require(type(solver['converged']) is bool and type(solver['achieved_gtol']) is bool and type(solver['status']) is int
            and type(solver['termination']) is str and solver['termination'],'invalid territory native solver')
        for key in ('iterations','evaluations'):require(type(solver[key]) is int and solver[key]>=0,'invalid territory solver count')
        for key in ('gradient_inf_norm','wall_seconds','peak_memory_bytes'):require_number(solver[key],'territory solver scalar',low=0)
        require_number(solver['objective'],'territory solver objective')
        require(solver['options']==(CONTINUATION if diagnostic else SOLVER)
            and solver['achieved_gtol']==(solver['gradient_inf_norm']<=solver['options']['gtol']),
                'territory solver tolerance differs')
    if head['objective'] is not None:
        require_fields(head['objective'],('penalized_loss','gradient_inf_norm'),'territory objective')
    if head['centers'] is not None:
        for center in head['centers']:
            require_fields(center,('block','subblock','mean','weight_seconds','reference_applicability','reference_offset'),
                'territory reporting center')
    if head['diagnostics'] is not None:
        require_fields(head['diagnostics'],('kind','observed_crossings','expected_crossings','directed_risk_seconds',
            'minimum_hazard_per_second','maximum_hazard_per_second','zone_support'),'territory fit diagnostics')
        require([row['zone'] for row in head['diagnostics']['zone_support']]==[0,1,2],'territory diagnostic zone axis differs')
        for row in head['diagnostics']['zone_support']:
            require_fields(row,('zone','directed_risk_seconds','observed_crossings','expected_crossings'),'territory zone diagnostic')
    _finite(head)


def _read_arrays(document,member):
    require_fields(document,('arrays','array_shapes'),'territory array descriptor')
    require_fields(document['arrays'],('path','sha256'),'territory array binding')
    require(same_input_reference(document['arrays'],identity(member)),'territory array descriptor member differs')
    for row in document['array_shapes']:require_fields(row,('name','shape','dtype'),'territory array axis')
    return load_arrays(document)


def _validate_fitted(design,name,head,beta,incoming):
    prior_rows,mean,precision=annual_territory_priors(design,design.heads[name],incoming)
    require(head['priors']==prior_rows,'territory saved prior/support differs')
    expected={_actor_key(row):row for row in incoming}
    if head['status']=='complete':
        require(beta is not None and beta.shape==(len(design.heads[name].columns),),'territory coefficient shape differs')
        for prior in prior_rows:
            if prior['current_season_information']:
                expected[_actor_key(prior)]=dict(block=prior['block'],id=prior['id'],subblock=prior['subblock'],
                    coefficient=float(beta[prior['index']]),season=design.season,support_seasons=prior['prior_seasons']+[design.season])
            else:require(beta[prior['index']]==prior['mean'],'territory prior-only coordinate differs from conditional mean')
        centers,reference,_=center_head(design,design.heads[name],beta,head['reference']['log_rate'])
        require(head['centers']==centers and head['reference']==reference,'territory saved reporting transform differs')
        log_rate=np.log((float(design.heads[name].event_counts.sum())+.5)/(float(design.heads[name].exposure_seconds.sum())+30))
        require(close(head['reference']['log_rate'],float(log_rate)),'territory offset differs')
        value,gradient=territory_objective(beta,design.heads[name],mean,precision,head['reference']['log_rate'])
        require(close(value,head['objective']['penalized_loss'])
            and close(float(np.max(abs(gradient))),head['objective']['gradient_inf_norm']),'territory saved objective differs')
    require(head['ledger']==[expected[k] for k in sorted(expected)],'territory last-supported raw ledger differs')


def read_territory_state(path,purpose,*,narrow=False):
    path=input_path(path, strict=True);path=path/'manifest.json' if path.is_dir() else path
    manifest=read_json(path);require_fields(manifest,MANIFEST_KEYS,'territory manifest')
    require(type(manifest['schema_version']) is int and manifest['schema_version']==1 and manifest['kind']=='territory_state'
        and manifest['purpose']==purpose and purpose in ('real','fixture'),'territory schema/kind/purpose differs')
    require_season_label(manifest['season']);require(manifest['recipe']==territory_recipe(TERRITORY_RECIPE),'territory recipe differs')
    require_fields(manifest['design_identity'],('metadata','arrays'),'territory design identity')
    require_fields(manifest['design_identity']['arrays'],HEADS,'territory design array identities')
    digest(manifest['design_identity']['metadata'])
    for value in manifest['design_identity']['arrays'].values():digest(value)
    require_fields(manifest['heads'],HEADS,'territory heads')
    for value in manifest['heads'].values():
        require_fields(value,('status','path'),'territory head binding');require(value['path']=='heads.json','territory head path differs')
    for key in ('prepared','coaches'):
        require_state_reference(manifest[key],'territory '+key);require(manifest[key]['purpose']==purpose,'territory bound input purpose differs')
        require_fields(manifest[key],('path','sha256','purpose','members') if key=='prepared' else
            ('path','sha256','purpose','selected_game_ids'),'territory '+key+' binding')
    previous=manifest['previous']
    if previous is not None:
        require_fields(previous,('path','sha256','season','purpose','recipe_sha256'),'territory predecessor')
        require_state_reference(previous,'territory predecessor')
        require(previous['purpose']==purpose and previous['recipe_sha256']==manifest['recipe']['sha256']
            and previous['season']==f"{int(manifest['season'][:4])-1}{manifest['season'][:4]}",'territory predecessor identity differs')
    if purpose=='real':require((manifest['season']=='20212022')==(previous is None),'territory saved chronology differs')
    root=path.parent;members={}
    for member in manifest['files']:
        require_fields(member,('path','sha256','bytes'),'territory member');digest(member['sha256'])
        name=member['path'];require(type(name) is str and Path(name).name==name and name not in members,'invalid territory member path')
        require(type(member['bytes']) is int and member['bytes']>=0,'territory member byte count differs')
        member_path=root/name
        if not narrow or name=='heads.json':
            member_path=state_member_path(root,name)
            require(member_path.stat().st_size==member['bytes'] and identity(member_path)['sha256']==member['sha256'],
                    'territory member identity differs')
        members[name]=member_path
    required={'design.json','entry-design.npz','exit-design.npz','heads.json','nuisance.json','coverage.json','projections.jsonl','support.jsonl','numerical.json'}
    require(required<=set(members) and set(members)<=required|{'coefficients.npz','entry-probe.npz','exit-probe.npz'},'territory member set differs')
    heads=read_json(members['heads.json']);require_fields(heads,HEADS,'territory numerical heads')
    for name in HEADS:_validate_head(heads[name],manifest,name)
    if narrow:
        _finite(manifest)
        return TerritoryState(root,manifest,heads,None,{}, {},[],[],{})
    numerical=read_json(members['numerical.json']);require_fields(numerical,('coefficients','probes'),'territory numerical files')
    coefficients={} if numerical['coefficients'] is None else _read_arrays(numerical['coefficients'],members['coefficients.npz'])
    require(set(coefficients)=={name for name in HEADS if heads[name]['status']=='complete'},'territory completed coefficient axes differ')
    probes={}
    require(set(numerical['probes']) in (set(),set(HEADS)),'territory diagnostic head axes differ')
    for name,probe in numerical['probes'].items():
        require_fields(probe,('head','reason','arrays'),'territory diagnostic')
        beta=None
        if probe['arrays'] is not None:
            arrays=_read_arrays(probe['arrays'],members[name+'-probe.npz']);require(set(arrays)=={'coefficients'},'territory probe coefficient axis differs');beta=arrays['coefficients']
        if probe['head'] is not None:
            probe_manifest=dict(manifest,heads={**manifest['heads'],name:dict(status=probe['head']['status'],path='heads.json')})
            _validate_head(probe['head'],probe_manifest,name,diagnostic=True)
            require((probe['head']['status']=='complete')==(beta is not None),'territory diagnostic completion differs')
        else:require(beta is None and probe['reason']=='baseline_incomplete','missing territory diagnostic reason differs')
        probes[name]=dict(head=probe['head'],coefficients=beta,reason=probe['reason'])
    projections=list(rows(members['projections.jsonl']));support=list(rows(members['support.jsonl']));coverage=read_json(members['coverage.json'])
    _finite(manifest);_finite(projections);_finite(support);_finite(coverage)
    design=None
    if not narrow:
        doc=read_json(members['design.json'])
        require_fields(doc,[field.name for field in fields(TerritoryDesign) if field.name not in ('nuisance','coverage')],'territory design metadata')
        require(manifest['design_identity']['metadata']==identity(members['design.json'])['sha256'],'territory design identity differs')
        source_heads={}
        for name,head in doc['heads'].items():
            metadata_keys=[field.name for field in fields(TerritoryHeadDesign) if field.name not in (*ARRAYS,'X_time','X_event')]
            require_fields(head,(*metadata_keys,'arrays'),'territory head design metadata')
            arrays=_read_arrays(head['arrays'],members[name+'-design.npz']);expected=set(ARRAYS)|{f'X_{kind}_{part}' for kind in ('time','event') for part in ('data','indices','indptr','shape')}
            require(set(arrays)==expected and ordered_array_digest(arrays)==manifest['design_identity']['arrays'][name],
                    'territory source array axes/identity differ')
            matrices={}
            for kind in ('time','event'):
                matrices['X_'+kind]=csr_matrix((arrays[f'X_{kind}_data'],arrays[f'X_{kind}_indices'],arrays[f'X_{kind}_indptr']),
                    shape=tuple(arrays[f'X_{kind}_shape']))
            metadata={key:head[key] for key in metadata_keys}
            for key in ('columns','time_keys','event_keys'):metadata[key]=tuple(metadata[key])
            source_heads[name]=TerritoryHeadDesign(**metadata,**matrices,**{key:arrays[key] for key in ARRAYS})
        values={key:value for key,value in doc.items() if key!='heads'}
        values['players']=tuple(values['players']);values['coach_ids']=tuple(values['coach_ids'])
        design=TerritoryDesign(**values,heads=source_heads,nuisance=read_json(members['nuisance.json']),coverage=coverage)
        require(all(getattr(design,key)==manifest[key] for key in ('purpose','season','prepared','coaches','training_cutoff')),
                'territory saved design lineage differs');validate_design(design)
        for name in HEADS:
            require(name not in coefficients or coefficients[name].shape==(len(design.heads[name].columns),),
                    'territory coefficient shape differs')
        predecessor=None if previous is None else read_territory_state(previous['path'],purpose,narrow=True)
        if predecessor is not None:
            require(identity(predecessor.path/'manifest.json')['sha256']==previous['sha256'],'territory predecessor binding differs')
        for name in HEADS:
            incoming=[] if predecessor is None else predecessor.heads[name]['ledger']
            _validate_fitted(design,name,heads[name],coefficients.get(name),incoming)
            if name in probes and probes[name]['head'] is not None:
                _validate_fitted(design,name,probes[name]['head'],probes[name]['coefficients'],incoming)
        expected_rows,expected_support=project_hazards(design,heads,coefficients)
        require(projections==expected_rows and support==expected_support,'territory saved hazard/support projections differ')
    return TerritoryState(root,manifest,heads,design,coefficients,probes,projections,support,coverage)


def read_territory_selection(path,purpose):
    """check an explicit chronological selection without searching for artifacts."""
    from .artifacts import linked_path
    selection=read_json(Path(path))
    require_fields(selection,('schema_version','purpose','prepared','coaches','source_results','years'),'territory selection')
    require(type(selection['schema_version']) is int and selection['schema_version']==1
        and selection['purpose']==purpose and purpose in ('real','fixture'),'territory selection schema/purpose differs')
    for key in ('prepared','coaches','source_results'):
        require_fields(selection[key],('path','sha256'),'territory selection binding');linked_path(selection[key])
    years=selection['years'];require(type(years) is list and years,'territory selection years missing')
    labels=[item['season'] for item in years]
    for label in labels:require_season_label(label)
    require(labels==sorted(set(labels)) and all(int(b[:4])-int(a[:4])==1 for a,b in zip(labels,labels[1:])),
            'territory selected years are not consecutive')
    require(purpose!='real' or labels==['20212022','20222023','20232024','20242025','20252026'],
            'real territory selection requires all five years')
    previous=None
    for item in years:
        require_fields(item,('season','territory_state','ev_state','successor_reference'),'territory selected annual')
        for key in ('territory_state','ev_state','successor_reference'):
            if key=='successor_reference' and item[key] is None:continue
            require_fields(item[key],('path','sha256'),'territory selected annual binding');linked_path(item[key])
        state=read_territory_state(item['territory_state']['path'],purpose,narrow=True)
        require(state.manifest['season']==item['season'],'territory selected annual season differs')
        for key in ('prepared','coaches'):
            require({field:state.manifest[key][field] for field in ('path','sha256')}==selection[key],
                    'territory selection source lineage differs')
        predecessor=state.manifest['previous']
        require((predecessor is None)==(previous is None),'territory selected predecessor presence differs')
        if previous is not None:
            require({field:predecessor[field] for field in ('path','sha256')}==previous,'territory selection skips exact predecessor')
        previous=item['territory_state']
    return selection


def write_territory_reference(root,state,panel,*,ev_binding=None,panel_problem=None):
    """derive baseline and sole saved diagnostics once; fits remain immutable."""
    from .territory import project_territory,compare_territory_variants
    import resource
    began=perf_counter();root=Path(root).resolve();root.mkdir(parents=True,exist_ok=False)
    annual=identity(state.path/'manifest.json')
    panel_binding=None
    require((panel is None)==(type(panel_problem) is str and bool(panel_problem.strip())),
            'missing territory panel requires a located reason')
    if panel is not None:
        array_names=('neutral_xg','complete_xg','contrast_xg')
        panel_arrays=write_arrays(root,'panel.npz',{key:np.asarray(panel[key]) for key in array_names})
        actual_ev_binding={key:panel['ev_state'][key] for key in ('path','sha256')}
        require(ev_binding is None or same_input_reference(ev_binding,actual_ev_binding),'territory panel explicit ev binding differs')
        ev_binding=actual_ev_binding
        panel_doc=dict(schema_version=1,kind='territory_successor_panel',purpose=state.manifest['purpose'],season=state.manifest['season'],
            ev_state=ev_binding,units=panel['units'],axes=panel['axes'],arrays=panel_arrays,resources=panel['resources'],implementation=implementation())
        write_json(root/'panel.json',panel_doc);panel_binding=identity(root/'panel.json')
    require_fields(ev_binding,('path','sha256'),'territory projection ev binding');require_state_reference(ev_binding,'territory projection ev binding')
    variants={};diagnostics={}
    for variant in ('baseline','entry','exit','joint') if state.probes else ('baseline',):
        result=project_territory(state,panel,variant=variant);variants[variant]=result
        if variant!='baseline':diagnostics[variant]=compare_territory_variants(state,variants['baseline'],result)
    if not state.probes:diagnostics=dict(status='unassessed',reason='earlier_annual')
    records={}
    for variant,result in variants.items():
        document={key:value for key,value in result.items() if key not in ('values','nuisance','successor_reference')}
        reference=result.get('successor_reference')
        document['successor_reference']=None if reference is None else {key:value for key,value in reference.items() if key!='contrast'}
        value_arrays=None
        if result['shift_available']:
            fields_to_save=('end_probabilities','end_probability_difference')
            if result['successor_available']:fields_to_save=(*fields_to_save,'maps','values','raw_G_values','raw_G_allowance','map_sum_allowance')
            value_arrays=write_arrays(root,variant+'-values.npz',{key:np.stack([row[key] for row in result['values']])
                for key in fields_to_save})
        document['players']=[row['player_id'] for row in result.get('values',[])]
        document['values_arrays']=value_arrays
        write_json(root/(variant+'.json'),json_values(document));records[variant]=identity(root/(variant+'.json'))
    manifest=dict(schema_version=1,kind='territory_successor_reference',purpose=state.manifest['purpose'],season=state.manifest['season'],
        annual_state=annual,ev_state=ev_binding,panel=panel_binding,panel_problem=panel_problem,projections=records,diagnostics=json_values(diagnostics),
        resources=dict(projection_wall_seconds=perf_counter()-began,output_bytes=sum(path.stat().st_size for path in root.iterdir()),
            peak_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),implementation=implementation())
    write_json(root/'reference.json',manifest)
    return dict(path=root/'reference.json',manifest=manifest,panel=panel,variants=variants,diagnostics=diagnostics)


def read_territory_reference(path,state,ev_binding):
    """reuse an exact projection; validate native accounting without source replay."""
    from .artifacts import linked_path
    from .territory import successor_reference,successor_value,project_hazards
    path=input_path(path, strict=True);document=read_json(path)
    require_fields(document,('schema_version','kind','purpose','season','annual_state','ev_state','panel','panel_problem','projections','diagnostics',
        'resources','implementation'),'territory successor reference')
    require(type(document['schema_version']) is int and document['schema_version']==1 and document['kind']=='territory_successor_reference'
        and document['purpose']==state.manifest['purpose'] and document['season']==state.manifest['season']
        and same_input_reference(document['annual_state'],identity(state.path/'manifest.json'))
        and same_input_reference(document['ev_state'],ev_binding),
            'territory successor reference lineage differs')
    panel=None
    require((document['panel'] is None)==(type(document['panel_problem']) is str and bool(document['panel_problem'].strip())),
            'territory saved panel unavailable reason differs')
    if document['panel'] is not None:
        panel_doc=read_json(linked_path(document['panel']))
        require_fields(panel_doc,('schema_version','kind','purpose','season','ev_state','units','axes','arrays','resources','implementation'),
            'territory successor panel')
        require(type(panel_doc['schema_version']) is int and panel_doc['schema_version']==1 and panel_doc['kind']=='territory_successor_panel' and same_input_reference(panel_doc['ev_state'],ev_binding)
            and panel_doc['purpose']==document['purpose'] and panel_doc['season']==document['season'],
                'territory successor panel lineage differs')
        require(panel_doc['units']=='xg_mass_per_hour_per_cell' and panel_doc['axes']==dict(side=['for','against'],
            start=['DZ','NZ','OZ','on_the_fly'],age=[0,10,20,40,60,90],cells=656),'territory panel units/axes differ')
        panel=dict(**{key:panel_doc[key] for key in ('ev_state','units','axes','resources')},
            **_read_arrays(panel_doc['arrays'],path.parent/'panel.npz'))
        require(set(panel)=={'neutral_xg','complete_xg','contrast_xg','ev_state','units','axes','resources'},'territory successor panel arrays differ')
        require(panel['neutral_xg'].shape==(656,) and panel['complete_xg'].shape==panel['contrast_xg'].shape==(2,4,6,656)
            and np.all(panel['neutral_xg']>0) and np.all(panel['complete_xg']>0)
            and np.allclose(panel['complete_xg']-panel['neutral_xg'],panel['contrast_xg'],rtol=1e-9,atol=1e-9),
                'territory successor panel domains/arithmetic differ')
    variants={}
    expected_variants=('baseline','entry','exit','joint') if state.probes else ('baseline',)
    require(set(document['projections'])==set(expected_variants),'territory successor diagnostic variant set differs')
    for name,binding in document['projections'].items():
        result=read_json(linked_path(binding));_finite(result)
        require(type(result['shift_available']) is bool and type(result['successor_available']) is bool
            and (not result['successor_available'] or result['shift_available']), 'territory projection availability flags differ')
        if result['shift_available']:
            require_fields(result,('status','reason','variant','shift_available','successor_available','hazards','support','neutral','successor_reference','players','values_arrays'),
                'completed territory projection')
            require(result['variant']==name and result['players']==list(state.design.players),'territory projection player/variant axes differ')
            projected_heads=dict(state.heads);projected_coefficients=dict(state.coefficients)
            for head in HEADS:
                if name in (head,'joint'):
                    projected_heads[head]=state.probes[head]['head'];projected_coefficients[head]=state.probes[head]['coefficients']
            expected_hazards,expected_support=project_hazards(state.design,projected_heads,projected_coefficients)
            require(result['hazards']==expected_hazards and result['support']==expected_support,'territory projected hazard/support metadata differs')
            neutral=result['neutral']
            require_fields(neutral,('end_probabilities','bin_occupancy_seconds','mean_shift_seconds','shifts_per_1000_minutes',
                'survival_at_90','tail_time_fraction'),'territory neutral shift projection')
            end=np.asarray(neutral['end_probabilities']);occupancy=np.asarray(neutral['bin_occupancy_seconds'])
            require(end.shape==(4,) and np.isfinite(end).all() and np.all((end>=0)&(end<=1)) and close(float(end.sum()),1.)
                and occupancy.shape==(6,) and np.isfinite(occupancy).all() and np.all(occupancy>=0),'territory neutral shift probability/time domains differ')
            for seconds,width in zip(occupancy[:5],(10,10,20,20,30),strict=True):
                require(seconds<=width or close(float(seconds),width),'territory occupancy exceeds finite age bin')
            mean=neutral['mean_shift_seconds'];n0=neutral['shifts_per_1000_minutes']
            require_number(mean,'territory neutral mean',low=0);require_number(n0,'territory neutral workload',low=0)
            require(mean>0 and n0>0 and close(float(occupancy.sum()),mean) and close(n0,60000/mean)
                and close(neutral['tail_time_fraction'],float(occupancy[5]/mean)),'territory neutral duration/workload arithmetic differs')
            require_number(neutral['survival_at_90'],'territory neutral survival',low=0,high=1)
            require_number(neutral['tail_time_fraction'],'territory neutral tail fraction',low=0,high=1)
            arrays=_read_arrays(result.pop('values_arrays'),path.parent/(name+'-values.npz'))
            expected_shapes=dict(end_probabilities=(4,),end_probability_difference=(4,))
            if result['successor_available']:
                expected_shapes.update(maps=(2,656),values=(2,),raw_G_values=(2,),raw_G_allowance=(2,),map_sum_allowance=(2,))
            require(set(arrays)==set(expected_shapes),'territory projection value fields differ')
            for key,shape in expected_shapes.items():
                require(arrays[key].shape==(len(state.design.players),*shape),'territory projection native axes differ')
            reference=None
            if result['successor_available']:
                require(panel is not None and result['status']=='complete' and result['reason'] is None,'territory complete successor prerequisite differs')
                reference=successor_reference(result['neutral'],panel)
                require_fields(result['successor_reference'],('G_maps','G','absolute_term_scales'),'territory successor numerical projection')
                for key in ('G_maps','G','absolute_term_scales'):
                    require(np.asarray(result['successor_reference'][key]).shape==reference[key].shape
                        and np.allclose(reference[key],result['successor_reference'][key],rtol=1e-9,atol=1e-9),
                        'territory saved successor reference arithmetic differs')
            else:require(result['status']=='unavailable' and result['reason'] and result['successor_reference'] is None,'territory unavailable successor reason differs')
            values=[]
            for index,player in enumerate(result.pop('players')):
                focal=dict(end_probabilities=arrays['end_probabilities'][index])
                require(np.all((focal['end_probabilities']>=0)&(focal['end_probabilities']<=1))
                    and close(float(focal['end_probabilities'].sum()),1.),'territory focal probability domain differs')
                checked=(successor_value(result['neutral'],focal,reference) if reference is not None else
                    dict(end_probabilities=focal['end_probabilities'],end_probability_difference=np.asarray(focal['end_probabilities'])-np.asarray(result['neutral']['end_probabilities'])))
                for key in expected_shapes:
                    require(np.allclose(checked[key],arrays[key][index],rtol=1e-9,atol=1e-9),'territory saved native accounting differs')
                values.append(dict(player_id=player,season=document['season'],**{key:arrays[key][index] for key in expected_shapes}))
            result['values']=values;result['successor_reference']=reference
        else:
            expected=('status','reason','variant','shift_available','successor_available','successor_reference','players','values_arrays')
            if result['status']=='unavailable':expected=(*expected,'hazards','support')
            require_fields(result,expected,'unavailable territory projection')
            require(result['variant']==name and result['status'] in ('unavailable','unassessed')
                and result['successor_reference'] is None and result['values_arrays'] is None and result['players']==[],
                    'invalid unavailable territory projection')
            result.pop('values_arrays');result.pop('players')
        result['nuisance']=smooth_nuisance(state.design.nuisance);variants[name]=result
    from .territory import compare_territory_variants
    expected_diagnostics=({name:compare_territory_variants(state,variants['baseline'],variants[name]) for name in expected_variants if name!='baseline'}
        if state.probes else dict(status='unassessed',reason='earlier_annual'))
    require(document['diagnostics']==json_values(expected_diagnostics),'territory diagnostic receipt differs from saved variants')
    _finite(document)
    return dict(path=path,manifest=document,panel=panel,variants=variants,diagnostics=document['diagnostics'])
