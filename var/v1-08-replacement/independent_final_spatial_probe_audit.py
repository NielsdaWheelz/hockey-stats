"""bounded saved final-probe audit; no production imports, evaluator or context replay."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import resource
import sys
from time import perf_counter

import numpy as np
from independent_first_spatial_audit import HEADS,ROLES,QUANTITIES,SOLVER,sha,read,json_rows,digest_arrays
from independent_spatial_history_audit import unpack,check_reference,check_projections

ROOT=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/spatial/20252026')
PREDECESSOR='74f35a1c9599335279954170693f7d3add11302bc83611fe14a368322870e6eb'
ACCEPTANCE=Path('/Users/nnandal/Documents/code/hockey-stats-v1-08/docs/research/spatial-v1-08/receipts/real-fourth-spatial-completion.json')
ACCEPTANCE_SHA='ff9885a3634fb3d75801308bddfc295f66f96beadf4ce2dddc5c3beba198929f'
CONTINUATION=dict(maxiter=10000,ftol=1e-16,gtol=1e-7,maxcor=10)
REQUIREMENTS=('boundary_goals','missing_optional_inputs','entries','returns','trades','sparse_support')
LIMITS=dict(standardized_shape_probability=1e-5,neutral_shape_probability=1e-5,
            standardized_quality_probability=1e-5,neutral_quality_probability=1e-5,
            standardized_scalar_per_hour=1e-4,standardized_native_map_l1=1e-4,prospective_1000_minute_goals=1e-3,
            shape_probability=1e-5,quality_probability=1e-5,coalition_scalar_per_hour=1e-4,coalition_native_map_l1=1e-4,
            allocation_scalar_per_hour=1e-4,allocation_native_map_l1=1e-4)
CONTEXT_SHAPES=dict(shape_probability=(16,656),quality_probability=(16,656),coalition_scalar_per_hour=(16,2),
                    coalition_native_map_l1=(16,2),allocation_scalar_per_hour=(4,2),allocation_native_map_l1=(4,2))
HEAD_KEYS=set('head status reasons priors ledger centers reference_predictor age_curves objective solver diagnostics resources'.split())


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def check_baseline(manifest,annual,descriptor,heads,flat):
    assert set(manifest)==set(annual)
    assert all(manifest[k]==annual[k] for k in manifest if k not in ('files','resources'))
    assert all(row in manifest['files'] for row in annual['files'])
    expected={k:manifest[k] for k in ('purpose','season','recipe','prepared','coaches','valued','previous','design_identity','basis_identity')}
    expected.update(schema_version=1,heads={h:dict(metadata_sha256=canonical_digest(heads[h]),arrays_sha256=digest_arrays({'coefficients':flat[h]})) for h in HEADS})
    assert descriptor==expected,'immutable baseline descriptor differs'


def check_selection(rows,requirements,players):
    assert type(rows) is list and len(rows)<=256
    identities=[];orders=[]
    for row in rows:
        assert set(row)=={'kind','index','key','role','player_id','requirements'}
        assert row['kind'] in ('time','event') and type(row['index']) is int and row['index']>=0
        key=row['key'];assert row['role'] in ROLES and row['player_id'] in players
        assert type(key['segment_index']) is int and key['segment_index']>=0 and type(key['chunk_index']) is int and key['chunk_index']>=0
        assert type(key['game_id']) is str and key['game_id'].startswith('2025')
        source=key['source_index'];assert source is None if row['kind']=='time' else type(source) is int and source>=0
        side='attacking' if row['role']=='offense' else 'defending';assert row['player_id'] in key[side+'_players']
        assert type(row['requirements']) is list and row['requirements']==[name for name in REQUIREMENTS if name in row['requirements']]
        identities.append((row['kind'],row['index'],row['role'],row['player_id']))
        orders.append((key['game_id'],key['segment_index'],key['chunk_index'],-1 if source is None else source,row['role'],row['player_id']))
    assert len(identities)==len(set(identities)) and orders==sorted(orders)
    expected=[dict(requirement=name,disposition='actual' if any(name in r['requirements'] for r in rows) else 'no_matching_context',key=next((r['key'] for r in rows if name in r['requirements']),None)) for name in REQUIREMENTS]
    assert requirements==expected,'saved-selection witness/disposition differs'


def check_head(metadata,flat,head,season,options,baseline=None):
    assert set(metadata)==HEAD_KEYS and metadata['head']==head
    beta,age=unpack(metadata,flat,head)
    if baseline is not None:
        assert [{k:v for k,v in p.items() if k!='prior_mean'} for p in metadata['priors']]==[{k:v for k,v in p.items() if k!='prior_mean'} for p in baseline['priors']], 'probe prior inputs differ'
    expected_curves=None if head!='volume' else dict(reference_age=27.,scale_years=10.,ridge_precision=64.,curves=[dict(role=r,position_group=p,coefficients=age[i:i+2].tolist()) for r,p,i in (('offense','F',0),('offense','D',2),('defense','F',4),('defense','D',6))])
    assert metadata['age_curves']==expected_curves
    ledger={(r['block'],r['id'],r['subblock']):r for r in metadata['ledger']};assert len(ledger)==len(metadata['ledger'])
    supported=set()
    for prior in metadata['priors']:
        mean=np.asarray(prior['mean'],dtype=float).copy()
        if prior['age_indices']:mean[0]+=np.dot(prior['age_delta'],age[prior['age_indices']])
        assert prior['prior_mean']==mean.tolist()
        key=tuple(prior[k] for k in ('block','id','subblock'))
        if prior['prior_only']:assert np.array_equal(beta[prior['index']],mean) and ledger.get(key)==prior['last_supported']
        else:
            supported.add(key)
            assert ledger[key]==dict(block=prior['block'],id=prior['id'],subblock=prior['subblock'],coefficient=beta[prior['index']].tolist(),season=season,position_group=prior['position_group'],age=prior['age'],support_seasons=prior['prior_seasons']+[season])
    assert {key for key,row in ledger.items() if row['season']==season}==supported
    if baseline is not None:
        old={(r['block'],r['id'],r['subblock']):r for r in baseline['ledger']}
        assert set(ledger)==set(old) and all(ledger[k]==v for k,v in old.items() if k not in supported),'probe older/absent ledger differs'
    solver=metadata['solver'];assert solver['converged'] is True and solver['options']==options and solver['maxfun']==15000 and solver['maxls']==20
    assert type(solver['iterations']) is int and solver['iterations']>=0 and type(solver['evaluations']) is int and solver['evaluations']>=0
    assert np.isfinite(solver['raw_gradient_inf_norm']) and solver['raw_gradient_inf_norm']>=0
    objective=metadata['objective'];assert set(objective)=={'likelihood','penalty','total'} and np.isfinite(list(objective.values())).all()
    assert objective['total']==objective['likelihood']+objective['penalty']
    return beta,age


def probabilities(players,heads,betas,references,offsets,basis):
    result={}
    for head in ('shape','quality'):
        axes={(p['block'],p['id'],p['subblock']):p['index'] for p in heads[head]['priors']}
        centers={(c['block'],c['subblock']):np.asarray(c['mean']) for c in heads[head]['centers']}
        predictors=np.asarray([references[head]+betas[head][axes[block,p,'base']]-centers[block,'base'] for p in players for block in ('attacking_player','defending_player')])
        if head=='shape':
            eta=np.log(offsets['pi'])+predictors@basis.T;neutral=np.log(offsets['pi'])+references[head]@basis.T
            weights=np.exp(eta-eta.max(axis=-1,keepdims=True));p=weights/weights.sum(axis=-1,keepdims=True)
            weights=np.exp(neutral-neutral.max());n=weights/weights.sum()
        else:
            qbar=np.asarray(offsets['qbar']);offset=np.log(qbar)-np.log1p(-qbar)
            eta=offset+predictors[:,:1]+predictors[:,1:]@basis.T;neutral=offset+references[head][0]+references[head][1:]@basis.T
            p=np.exp(-np.logaddexp(0.,-eta));n=np.exp(-np.logaddexp(0.,-neutral))
        assert np.isfinite(p).all() and np.isfinite(n).all() and np.all((p>=0)&(p<=1)) and np.all((n>=0)&(n<=1))
        result['standardized_'+head+'_probability']=p.reshape(len(players),2,656)
        result['neutral_'+head+'_probability']=n
    return result


def movements(base,changed,before,after):
    assert base.dtype==changed.dtype==np.dtype('float64') and base.shape==changed.shape and base.ndim==5 and base.shape[1:]==(2,2,3,656)
    assert np.isfinite(base).all() and np.isfinite(changed).all()
    delta=changed-base
    values={name:after[name]-before[name] for name in before}
    values.update(standardized_scalar_per_hour=delta.sum(axis=-1),standardized_native_map_l1=np.abs(delta).sum(axis=-1),prospective_1000_minute_goals=delta[:,:,1,2].sum(axis=-1)*(1000/60))
    return values


def reduce_maxima(players,values):
    result={}
    for name,array in values.items():
        expected=(len(players),2,656) if name.startswith('standardized_') and name.endswith('_probability') else (656,) if name.startswith('neutral_') else (len(players),2) if name=='prospective_1000_minute_goals' else (len(players),2,2,3)
        assert array.shape==expected and np.isfinite(array).all()
        flat=int(np.argmax(np.abs(array)));i=np.unravel_index(flat,array.shape)
        if name.startswith('neutral_'):locator=dict(kind='neutral',cell=int(i[0]))
        elif name.endswith('_probability'):locator=dict(player_id=players[i[0]],role=ROLES[i[1]],cell=int(i[2]))
        else:
            locator=dict(player_id=players[i[0]],role=ROLES[i[1]])
            if len(i)==4:locator.update(quantity=QUANTITIES[i[2]],kind=('neutral','complete','difference')[i[3]])
        result[name]=dict(value=float(abs(array.ravel()[flat])),limit=LIMITS[name],locator=locator)
    assert set(result)==set(LIMITS)-set(CONTEXT_SHAPES)
    return result


def locator_index(name,locator,players,selected):
    if name in CONTEXT_SHAPES:
        assert set(locator)=={'kind','key','player_id','role','coordinate'}
        assert any(all(locator[k]==row[k] for k in ('kind','key','player_id','role')) for row in selected),'locator outside frozen selected rows'
        coordinate=locator['coordinate'];assert type(coordinate) is list and len(coordinate)==2
        assert all(type(x) is int and 0<=x<size for x,size in zip(coordinate,CONTEXT_SHAPES[name],strict=True))
        return tuple(coordinate)
    if name.startswith('neutral_'):
        assert set(locator)=={'kind','cell'} and locator['kind']=='neutral';indices=(locator['cell'],);sizes=(656,)
    else:
        assert locator['player_id'] in players and locator['role'] in ROLES
        indices=(players.index(locator['player_id']),ROLES.index(locator['role']))
        if name.endswith('_probability'):assert set(locator)=={'player_id','role','cell'};indices+= (locator['cell'],);sizes=(len(players),2,656)
        elif name=='prospective_1000_minute_goals':assert set(locator)=={'player_id','role'};sizes=(len(players),2)
        else:
            assert set(locator)=={'player_id','role','quantity','kind'}
            indices+=(QUANTITIES.index(locator['quantity']),('neutral','complete','difference').index(locator['kind']));sizes=(len(players),2,2,3)
    assert all(type(int(x)) is int and 0<=x<size for x,size in zip(indices,sizes,strict=True))
    if 'cell' in locator:assert type(locator['cell']) is int
    return indices


def check_comparison(comparison,players,selected,values,replayed):
    assert set(comparison)=={'status','reason','maxima','failures'} and set(comparison['maxima'])==set(LIMITS)
    crossed=set();reports={}
    for name,item in comparison['maxima'].items():
        assert set(item)=={'value','limit','locator'} and type(item['value']) in (int,float) and np.isfinite(item['value']) and item['value']>=0 and item['limit']==LIMITS[name]
        index=locator_index(name,item['locator'],players,selected)
        if item['value']>LIMITS[name]:crossed.add(name)
        if name in CONTEXT_SHAPES:reports[name]=dict(scope='saved canonical magnitude/locator only; no independent actual-context replay',canonical=item)
        else:
            independent=replayed[name];at_locator=float(abs(values[name][index]))
            if not name.endswith('_probability'):assert independent==item,'saved-rate maximum/locator differs'
            if independent['value']==item['value']==0.:assert independent['locator']==item['locator'],'zero maximum is not the first c-order location'
            reports[name]=dict(scope='independent saved standardized replay',canonical=item,independent=independent,exact_value_agreement=independent['value']==item['value'],exact_locator_agreement=independent['locator']==item['locator'],literal_value_discrepancy=independent['value']-item['value'],independent_value_at_canonical_locator=at_locator,independent_exact_maximizer_count=int(np.count_nonzero(np.abs(values[name])==independent['value'])),canonical_locator_is_independent_exact_tie=at_locator==independent['value'],agreement_limit='no extra maximum-equality tolerance; unequal probability arithmetic is literal evidence for root review')
    failure_names=set()
    for item in comparison['failures']:
        assert set(item)=={'quantity','value','limit','locator'};name=item['quantity'];assert name in crossed and item['limit']==LIMITS[name]
        assert np.isfinite(item['value']) and LIMITS[name]<item['value']<=comparison['maxima'][name]['value']
        locator_index(name,item['locator'],players,selected);failure_names.add(name)
    assert failure_names==crossed and comparison['status']==('failed' if crossed else 'passed') and comparison['reason']==('numerical_movement_exceeds_budget' if crossed else None)
    independent_crossings=[name for name,item in replayed.items() if item['value']>LIMITS[name]]
    return dict(budgets_passed=not crossed and not independent_crossings,saved_crossings=sorted(crossed),independent_crossings=independent_crossings,maxima=reports)


def audit(root,expected):
    began=perf_counter();checked=[]
    assert sha(root/'manifest.json')==expected
    manifest=read(root/'manifest.json');members={r['path']:r for r in manifest['files']};assert len(members)==len(manifest['files'])
    def member(name,loader=read):
        path=root/name;assert sha(path)==members[name]['sha256'];checked.append(dict(path=str(path),sha256=members[name]['sha256'],bytes=path.stat().st_size));return loader(path)
    def vector(path):
        with np.load(path,allow_pickle=False) as z:assert z.files==['coefficients'];return z['coefficients']
    assert manifest['purpose']=='real' and manifest['season']=='20252026'
    assert manifest['recipe']['solver']==SOLVER and manifest['recipe']['continuation']==CONTINUATION
    assert manifest['previous']==dict(path=str(root.parent/'20242025'/'manifest.json'),sha256=PREDECESSOR,season='20242025',purpose='real',usage='annual')
    assert sha(ACCEPTANCE)==ACCEPTANCE_SHA
    accepted=read(ACCEPTANCE);assert accepted['eligible_as_annual_predecessor'] is True and accepted['manifest']['sha256']==PREDECESSOR
    annual=member('annual-baseline-manifest.json');descriptor=member('probes/baseline.json');selected=member('probes/rows.json');requirements=member('probes/requirements.json')
    heads={h:member(f'heads/{h}.json') for h in HEADS};flat={h:member(f'heads/{h}.npz',vector) for h in HEADS}
    check_baseline(manifest,annual,descriptor,heads,flat)
    players=[p['id'] for p in heads['volume']['priors'] if p['block']=='attacking_player' and p['subblock']=='base'];assert players==sorted(set(players))
    check_selection(selected,requirements,players)
    reference=member('reference.json');assert reference['sha256']==canonical_digest({k:v for k,v in reference.items() if k!='sha256'})
    assert reference['kind']=='virtual elapsed linear design' and reference['units']=='per_hour' and reference['player_slots_per_role']==5
    assert reference['context']=='all centered non-actor coordinates zero' and reference['basis_identity']==manifest['basis_identity']
    with np.load(root/'design.npz',allow_pickle=False) as z:basis=z['basis']
    assert basis.dtype==np.dtype('float64') and basis.shape==(656,40) and np.isfinite(basis).all() and digest_arrays({'basis':basis})==manifest['basis_identity']['array_sha256']
    assert np.max(abs(basis.mean(axis=0)))<1e-10 and np.allclose(basis.T@basis/656,np.eye(40),rtol=0,atol=1e-10)
    offsets=reference['annual_offsets'];assert offsets['r']>0 and np.isfinite(offsets['r'])
    assert np.asarray(offsets['pi']).shape==np.asarray(offsets['qbar']).shape==(656,) and np.all(np.asarray(offsets['pi'])>0) and abs(sum(offsets['pi'])-1)<1e-12 and np.all((np.asarray(offsets['qbar'])>0)&(np.asarray(offsets['qbar'])<1))
    with np.load(root/'projections.npz',allow_pickle=False) as z:base=z['rates']
    rows=member('projections.jsonl',lambda p:list(json_rows(p)));betas={};references={};centers={}
    for head in HEADS:
        betas[head],_=check_head(heads[head],flat[head],head,manifest['season'],SOLVER)
        references[head],centers[head],_=check_reference(heads[head],betas[head],reference,head)
    baseline_projection=check_projections(heads,betas,references,centers,reference,rows,base,basis,manifest['season'])
    before=probabilities(players,heads,betas,references,offsets,basis);probes={};passed=True
    for head in HEADS:
        metadata=member(f'probes/{head}.json');comparison=member(f'probes/{head}-comparison.json');assert metadata['head']==head
        if metadata['status']!='complete':
            assert set(metadata)==HEAD_KEYS and metadata['status'] in ('failed','unavailable') and metadata['centers'] is None and metadata['reference_predictor'] is None
            assert [{k:v for k,v in p.items() if k!='prior_mean'} for p in metadata['priors']]==[{k:v for k,v in p.items() if k!='prior_mean'} for p in heads[head]['priors']]
            assert metadata['solver'] is None or metadata['solver']['options']==CONTINUATION
            assert metadata['reasons'] and comparison==dict(status='failed',reason='continuation_failed',maxima=None,failures=[dict(head=head,reasons=metadata['reasons'])])
            probes[head]=dict(status='incomplete_not_qualified',metadata=metadata,comparison=comparison);passed=False;continue
        completed=member(f'probes/{head}.npz',vector);assert completed.shape==flat[head].shape
        beta,_=check_head(metadata,completed,head,manifest['season'],CONTINUATION,heads[head])
        variant_heads=dict(heads);variant_heads[head]=metadata;variant_betas=dict(betas);variant_betas[head]=beta
        variant_reference=deepcopy(reference);variant_reference['heads'][head].update(centers=metadata['centers'],predictor=metadata['reference_predictor']);variant_reference['sha256']=canonical_digest({k:v for k,v in variant_reference.items() if k!='sha256'})
        refs=dict(references);means=dict(centers);refs[head],means[head],_=check_reference(metadata,beta,variant_reference,head)
        def projection_array(path):
            with np.load(path,allow_pickle=False) as z:assert z.files==['rates'];return z['rates']
        changed=member(f'probes/{head}-projections.npz',projection_array);projection_rows=member(f'probes/{head}-projections.jsonl',lambda p:list(json_rows(p)))
        projection=check_projections(variant_heads,variant_betas,refs,means,variant_reference,projection_rows,changed,basis,manifest['season'])
        after=probabilities(players,variant_heads,variant_betas,refs,offsets,basis);values=movements(base,changed,before,after);replayed=reduce_maxima(players,values)
        comparison_result=check_comparison(comparison,players,selected,values,replayed);passed=passed and comparison_result['budgets_passed']
        delta=completed-flat[head]
        probes[head]=dict(status='pending_root_acceptance',comparison=comparison_result,standardized_projection=projection,
            completed_coefficient_movement=dict(maximum=float(abs(delta).max()),l2=float(np.linalg.norm(delta)),scope='completed endpoint includes age/prior-only completion; not reconstructed raw native movement'),
            native_solver=metadata['solver'],objective_component_deltas={k:metadata['objective'][k]-heads[head]['objective'][k] for k in ('likelihood','penalty','total')},descriptive_not_qualification='no movement, objective improvement or gradient gate added')
        del changed,projection_rows,after,values
    return dict(kind='independent-final-spatial-saved-probe-audit',status='pending_root_acceptance',bound_checks_passed=True,numerical_budgets_passed=passed,manifest=dict(path=str(root/'manifest.json'),sha256=expected),accepted_predecessor_root=dict(path=str(ACCEPTANCE),sha256=ACCEPTANCE_SHA),baseline_projection=baseline_projection,
        frozen_selection=dict(rows=len(selected),requirements=requirements,scope='uniqueness/order and dispositions/first witness within saved selection only; no global first-key/population/no-matching proof'),
        fields=dict(independently_replayed=list(LIMITS)[:7],saved_context_only=list(CONTEXT_SHAPES)),probes=probes,rehashed_members=checked,
        selected_large_members=[dict(path=str(root/name),member=key,selected_array_bytes=int(value.nbytes),selected_bytes_scope='decompressed array bytes, not measured archive disk IO',ordered_array_sha256=digest_arrays({key:value}),archive_sha256=members[name]['sha256'],archive_integrity='canonical validation; only this member read, full archive not rehashed') for name,key,value in (('design.npz','basis',basis),('projections.npz','rates',base))],
        code=dict(audit=sha(Path(__file__)),primitive=sha(Path(__file__).with_name('independent_first_spatial_audit.py')),history_helpers=sha(Path(__file__).with_name('independent_spatial_history_audit.py'))),
        resources=dict(wall_seconds=perf_counter()-began,peak_resident_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)),
        limits=['six actual-context maxima are saved canonical evidence, not independently replayed','probability replay uses independent arithmetic; literal discrepancies/ties require root review, not a tolerance rescue','source/full design/csr/context/objective/gradient/solver/probe/actual allocation not called','whole original design/projection archives not hashed or loaded; probe rates-only archives checked individually','coefficient/native/objective descriptors do not establish new optimum or scientific support'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--expected-manifest-sha256',required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    expected=args.expected_manifest_sha256
    assert len(expected)==64 and all(c in '0123456789abcdef' for c in expected),'final manifest pin withheld; no input/output access'
    output=args.out.resolve();assert output.is_relative_to('/Volumes/Expansion/hockey-stats') and not output.exists();output.mkdir()
    try:
        result=audit(ROOT,expected);(output/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        print(json.dumps(dict(status=result['status'],numerical_budgets_passed=result['numerical_budgets_passed'],report=str(output/'audit.json'))));return 0 if result['numerical_budgets_passed'] else 1
    except BaseException as error:
        (output/'audit-failure.json').write_text(json.dumps(dict(status='failed',error_type=type(error).__name__,error=str(error)),indent=2)+'\n');raise


if __name__=='__main__':raise SystemExit(main())
