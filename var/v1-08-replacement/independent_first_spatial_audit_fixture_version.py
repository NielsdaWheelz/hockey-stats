"""independent first-year saved spatial audit; no project imports or native solve."""
import argparse
from collections import Counter,defaultdict
import hashlib
from itertools import permutations
import json
from math import fsum,log
from pathlib import Path
import resource
import sys
from time import perf_counter

import numpy as np
from scipy.sparse import csr_matrix
from scipy.special import expit,logsumexp

HEADS=('volume','shape','quality');WIDTHS=dict(volume=1,shape=40,quality=41)
ROLES=('offense','defense');QUANTITIES=('attempts','xg')
ADJUSTMENTS=('baseline','self','teammates','opponents','coaching_other_context','residual','factual')
SOLVER=dict(maxiter=10000,ftol=1e-15,gtol=1e-6,maxcor=10)
BATCH=4096

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(path):return json.loads(Path(path).read_bytes())
def json_rows(path):
    with Path(path).open() as f:
        for line in f:yield json.loads(line)
def arrays(path,contract=None):
    with np.load(path,allow_pickle=False) as z:
        if contract is not None:assert z.files==list(contract)
        result={name:z[name] for name in z.files}
    if contract is not None:
        for name,v in result.items():assert list(v.shape)==contract[name]['shape'] and v.dtype.str==contract[name]['dtype']
    assert all(v.dtype.kind in 'if' and np.isfinite(v).all() for v in result.values())
    return result
def digest_arrays(values):
    h=hashlib.sha256()
    for name,v in values.items():
        h.update(json.dumps([name,v.dtype.str,list(v.shape)],separators=(',',':')).encode());h.update(v.tobytes(order='C'))
    return h.hexdigest()
def near_mass(a,b,terms):
    # frozen execution_scores._log_error/_near contract, also for a scalar cell.
    a,b=np.asarray(a),np.asarray(b)
    with np.errstate(divide='ignore',invalid='ignore'):
        ea=np.where(a>0,(np.abs(np.log(a))+2*terms+8)*2.**-52,0.)
        eb=np.where(b>0,(np.abs(np.log(b))+2*terms+8)*2.**-52,0.)
    return np.abs(a-b)<=(ea+eb)*np.maximum(a,b)+2.**-1072

def compare_rate(actual,expected):
    # existing positive-rate allocation closure scale; no probability-domain gate.
    error=np.abs(actual-expected);scale=1+np.abs(actual)+np.abs(expected)
    assert np.all(error<=1e-10*scale)
    return float(error.max(initial=0.))

def linear(actor,context,beta):
    split=actor.shape[1];return np.asarray(actor@beta[:split])+context@beta[split:]
def accumulate_gradient(gradient,actor,context,residual):
    split=actor.shape[1];gradient[:split]+=np.asarray(actor.T@residual);gradient[split:]+=context.T@residual

def independent_objective(data,definition,head,beta,age,information):
    """one endpoint F/fullG; first-year entry penalties, without production helpers."""
    w=WIDTHS[head];precision=np.zeros_like(beta)
    for i,column in enumerate(definition['columns']):
        if column['kind']=='actor':
            if information[i]:
                base=16. if column['block'].endswith('_player') else 100.
                precision[i]=base*40
                if head!='shape':precision[i,0]=base
        else:
            precision[i]=40. if column['kind']=='intercept' else 160.
            if head!='shape':precision[i,0]=.25 if column['kind']=='intercept' else 1.
    penalty=.5*float(np.sum(precision*beta*beta))+(32.*float(np.dot(age,age)) if head=='volume' else 0.)
    gradient=precision*beta;age_gradient=64.*age
    likelihood=0.;offsets=definition['annual_offsets'];basis=data['basis']
    Xt,Xe=data['Xt'],data['Xe'];Ct,Ce=data['context_time'],data['context_event'];E=data['exposure_hours']
    diagnostics={}
    if head=='volume':
        time_eta=log(offsets['r'])+linear(Xt,Ct,beta).ravel()
        event_eta=log(offsets['r'])+linear(Xe,Ce,beta).ravel()
        with np.errstate(over='raise',invalid='raise',under='raise'):rate=np.exp(time_eta)
        assert np.all(rate>0)
        expected=E*rate
        # every original time row is retained: this checks the grouped producer path.
        likelihood=float(np.sum(expected)-np.sum(event_eta))
        accumulate_gradient(gradient,Xt,Ct,expected[:,None])
        accumulate_gradient(gradient,Xe,Ce,-np.ones((Xe.shape[0],1)))
        diagnostics=dict(predicted_attempts=float(expected.sum()),residual=float(Xe.shape[0]-expected.sum()))
    else:
        shape_expected=np.zeros(656);quality_bins=np.zeros((10,3))
        for start in range(0,Xe.shape[0],BATCH):
            stop=min(start+BATCH,Xe.shape[0]);actor=Xe[start:stop];context=Ce[start:stop]
            predictor=linear(actor,context,beta);a,b=map(int,data['event_offsets'][[start,stop]])
            counts=np.diff(data['event_offsets'][start:stop+1]);row=np.repeat(np.arange(stop-start),counts)
            cell=data['origin_cells'][a:b];weight=data['origin_weights'][a:b]
            if head=='shape':
                logits=np.log(offsets['pi'])+predictor@basis.T;logp=logits-logsumexp(logits,axis=1)[:,None];p=np.exp(logp)
                likelihood-=float(np.dot(weight,logp[row,cell]))
                observed=np.zeros_like(p);np.add.at(observed,(row,cell),weight)
                # project expected/observed separately, unlike the production residual path.
                residual=p@basis-observed@basis
                shape_expected+=p.sum(axis=0)
            else:
                qbar=np.asarray(offsets['qbar']);logits=np.log(qbar)-np.log1p(-qbar)+predictor[:,:1]+predictor[:,1:]@basis.T
                eta=logits[row,cell];target=data['neutral_goal_probability'][a:b];p=expit(eta)
                likelihood+=float(np.dot(weight,target*np.logaddexp(0.,-eta)+(1-target)*np.logaddexp(0.,eta)))
                cell_residual=np.zeros_like(logits);np.add.at(cell_residual,(row,cell),weight*(p-target))
                residual=np.column_stack((np.bincount(row,weights=weight*(p-target),minlength=stop-start),cell_residual@basis))
                for i in range(10):
                    mask=(p>=i/10)&((p<(i+1)/10) if i<9 else p<=1)
                    quality_bins[i]+=[float(weight[mask].sum()),float(np.dot(weight[mask],target[mask])),float(np.dot(weight[mask],p[mask]))]
            accumulate_gradient(gradient,actor,context,residual)
        if head=='shape':
            mass=np.bincount(data['origin_cells'],weights=data['origin_weights'],minlength=656)
            diagnostics=dict(cross_entropy=likelihood/float(data['origin_weights'].sum()),native_location_residual=(mass-shape_expected).tolist())
        else:diagnostics=dict(target_neutral_chance_mass=float(np.dot(data['origin_weights'],data['neutral_goal_probability'])),calibration=quality_bins.tolist())
    flat=np.r_[gradient.ravel(),age_gradient] if head=='volume' else gradient.ravel()
    assert np.isfinite(flat).all() and np.isfinite(likelihood+penalty)
    return dict(likelihood=likelihood,penalty=penalty,total=likelihood+penalty),flat,diagnostics

def rates(predictors,offsets,basis):
    v=np.asarray(predictors['volume']);s=np.asarray(predictors['shape']);q=np.asarray(predictors['quality'])
    logits=np.log(offsets['pi'])+s@basis.T;logp=logits-logsumexp(logits,axis=-1)[...,None]
    qbar=np.asarray(offsets['qbar']);eta_q=np.log(qbar)-np.log1p(-qbar)+q[...,:1]+q[...,1:]@basis.T
    log_attempts=log(offsets['r'])+v[...,0,None]+logp
    with np.errstate(over='raise',invalid='raise',under='ignore'):
        attempts=np.exp(log_attempts);chance=np.exp(log_attempts-np.logaddexp(0.,-eta_q))
    assert np.isfinite(attempts).all() and np.isfinite(chance).all() and np.all(attempts>0) and np.all(chance>0) and np.all(chance<=attempts)
    return np.stack((attempts,chance),axis=-2)

def check_target_join(definition,data,purpose):
    """one saved 5v5 panel read and complete retained native-row join."""
    reference=definition['valued'];path=Path(reference['path']);manifest=read(path)
    assert manifest['purpose']==purpose and manifest['season']=='20212022' and sha(path)==reference['sha256']
    files={r['path']:r['sha256'] for r in manifest['files']}
    panel=next(p for p in manifest['panels'] if p['state']==dict(attacking_skaters=5,defending_skaters=5,attacking_goalies=1,defending_goalies=1))
    root=path.parent
    for name in [panel['events_path'],panel['arrays_path'],'events.jsonl']:assert sha(root/name)==files[name]
    panel_rows=list(json_rows(root/panel['events_path']));a=arrays(root/panel['arrays_path'])
    positions={r['key']:i for i,r in enumerate(panel_rows)};wanted={f"{k['game_id']}:{k['source_index']}" for k in definition['event_keys']}
    assert wanted<=positions.keys()
    expected={r['key']:r['prefixes']['neutral']['uqrg'] for r in json_rows(root/'events.jsonl') if r['key'] in wanted}
    assert set(expected)==wanted
    # pre-outcome setup weights; normalized success/failure mixture, no setters/posteriors.
    probability=np.empty(len(a['origin_cells']),dtype=np.float64)
    for start in range(0,len(probability),262144):
        stop=min(start+262144,len(probability));rows=np.searchsorted(a['event_offsets'][1:],np.arange(start,stop),side='right')
        upstream=a['neutral_upstream_logits'][start:stop];goal=a['neutral_goal_logits'][start:stop];prior=a['setup_weights'][rows]
        with np.errstate(divide='ignore'):lp=np.log(prior)
        success=logsumexp(-np.logaddexp(0.,-goal)+lp,axis=1);failure=logsumexp(-np.logaddexp(0.,goal)+lp,axis=1)
        probability[start:stop]=np.exp(-np.logaddexp(0.,-upstream).sum(axis=1)-np.logaddexp(0.,-(success-failure)))
    maximum=mass_maximum=0.;observed=blocked=0
    for i,key in enumerate(definition['event_keys']):
        name=f"{key['game_id']}:{key['source_index']}";j=positions[name];left,right=map(int,data['event_offsets'][i:i+2]);p,q=map(int,a['event_offsets'][j:j+2])
        assert data['origin_cells'][left:right].tobytes()==a['origin_cells'][p:q].tobytes() and data['origin_weights'][left:right].tobytes()==a['origin_weights'][p:q].tobytes()
        predicted=probability[p:q];saved=data['neutral_goal_probability'][left:right]
        assert np.all(near_mass(predicted,saved,5));maximum=max(maximum,float(np.max(np.abs(predicted-saved))))
        mass=fsum(float(x)*float(w) for x,w in zip(predicted,data['origin_weights'][left:right]));assert bool(near_mass(mass,expected[name],right-left));mass_maximum=max(mass_maximum,abs(mass-expected[name]))
        if right-left==1:observed+=1
        else:assert right-left==656;blocked+=1
    return dict(status='passed',scope='all retained native cells/weights/targets joined to the saved 5v5 pre-outcome neutral panel; no source/evaluator',valued_manifest=reference,events=len(wanted),observed_origin_events=observed,blocked_origin_events=blocked,origin_rows=len(data['origin_cells']),maximum_native_probability_difference=maximum,maximum_integrated_mass_difference=mass_maximum,rounding_contract='existing execution log-mass near comparison; five primitive probability terms per native cell, origin count for integrated mass')

def audit(root,expected,purpose,output):
    began=perf_counter();manifest=read(root/'manifest.json')
    assert sha(root/'manifest.json')==expected and manifest['purpose']==purpose and manifest['season']=='20212022' and manifest['previous'] is None
    assert [r['head'] for r in manifest['heads']]==list(HEADS) and len(manifest['files'])==15 and not any(r['path'].startswith('probes/') for r in manifest['files'])
    assert all(r['status']=='complete' for r in manifest['heads'])
    members=[]
    for ref in manifest['files']:
        path=root/ref['path'];assert path.resolve().is_relative_to(root.resolve()) and sha(path)==ref['sha256'];members.append(dict(ref,bytes=path.stat().st_size))
    document=read(root/'design.json');definition=document['definition'];data=arrays(root/'design.npz',document['arrays']);assert digest_arrays(data)==document['array_digest']
    assert definition['purpose']==purpose and definition['season']=='20212022'
    for key in ['prepared','coaches','valued','basis_identity']:assert definition[key]==manifest[key]
    for name,alias in [('X_time','Xt'),('X_event','Xe')]:
        data[alias]=csr_matrix((data[name+'_data'],data[name+'_indices'],data[name+'_indptr']),shape=tuple(data[name+'_shape']))
        assert data[alias].has_canonical_format and np.all(data[alias].data==1.)
    Xt,Xe=data['Xt'],data['Xe'];E=data['exposure_hours'];basis=data['basis'];H=float(E.sum());ne=Xe.shape[0]
    assert np.all(E>0) and basis.shape==(656,40) and np.max(abs(basis.mean(axis=0)))<1e-10 and np.allclose(basis.T@basis/656,np.eye(40),rtol=0,atol=1e-10)
    assert len(definition['time_keys'])==Xt.shape[0] and len(definition['event_keys'])==ne and len(definition['columns'])==Xt.shape[1]+data['context_time'].shape[1]
    assert np.all(abs(data['context_time'].T@E)<=1e-9*(1+H))
    mass_per_event=np.add.reduceat(data['origin_weights'],data['event_offsets'][:-1]);assert np.allclose(mass_per_event,1.,rtol=0,atol=1e-12)
    assert np.all((data['neutral_goal_probability']>=0)&(data['neutral_goal_probability']<=1))
    offsets=definition['annual_offsets'];mass=np.bincount(data['origin_cells'],weights=data['origin_weights'],minlength=656);chance=np.bincount(data['origin_cells'],weights=data['origin_weights']*data['neutral_goal_probability'],minlength=656)
    pi=(mass+10*(mass+1/656)/(ne+1))/(ne+10);r=(ne+(ne+1)/(H+1))/(H+1);qm=(chance.sum()+10*(chance.sum()+.5)/(ne+1))/(ne+10);qbar=(chance+10*pi*qm)/(mass+10*pi)
    assert abs(offsets['r']-r)<1e-12*(1+r) and np.allclose(offsets['pi'],pi,atol=1e-14,rtol=1e-12) and np.allclose(offsets['qbar'],qbar,atol=1e-14,rtol=1e-12)
    coverage=read(root/'coverage.json');assert coverage==definition['coverage']
    assert abs(coverage['directed_included_hours']-H)<1e-9 and abs(2*coverage['physical_included_hours']-H)<1e-9 and coverage['attempts']==ne and abs(coverage['origin_mass']-ne)<1e-9
    by_actor={(c['block'],str(c['id']),c['subblock']):i for i,c in enumerate(definition['columns']) if c['kind']=='actor'}
    game_time=defaultdict(lambda:defaultdict(list));event_game=defaultdict(lambda:defaultdict(list));physical={};seen_events=set()
    for matrix,keys,kind in [(Xt,definition['time_keys'],'time'),(Xe,definition['event_keys'],'event')]:
        for i,key in enumerate(keys):
            for side in ['attacking','defending']:
                indices={by_actor[side+'_player',str(p),'base'] for p in key[side+'_players']};assert len(indices)==5
                row=matrix[i];actual={int(j) for j in row.indices if definition['columns'][j].get('block')==side+'_player'};assert actual==indices
            if kind=='time':
                identity=(key['game_id'],key['segment_index'],key['chunk_index']);other=physical.pop(identity,None)
                if other is None:physical[identity]=(i,key)
                else:
                    j,k=other;assert key['attacking_side']!=k['attacking_side'] and key['attacking_players']==k['defending_players'] and key['defending_players']==k['attacking_players'] and E[i]==E[j]
                game_time[key['game_id']][key['attacking_side']].append(float(E[i]))
            else:
                identity=(key['game_id'],key['source_index']);assert identity not in seen_events;seen_events.add(identity);event_game[key['game_id']][key['attacking_side']].append(i)
    assert not physical
    for game in coverage['games']:
        gid=game['game_id'];excluded=set(game['base_excluded_segments'])|set(game['added_excluded_segments']);assert excluded==set(game['excluded_segment_union'])
        assert not any(k['segment_index'] in excluded for k in definition['time_keys'] if k['game_id']==gid)
        assert abs(fsum(game['known_lost_seconds'].values())/3600-10*game['known_lost_physical_hours'])<=1e-10*(1+10*game['known_lost_physical_hours'])
        assert not set(game['known_lost_event_source_indices'])&{s for g,s in seen_events if g==gid}
        for side in ['home','away']:
            assert abs(fsum(game_time[gid][side])-game['physical_included_hours'])<=1e-10*(1+game['physical_included_hours'])
            indices=event_game[gid][side];assert len(indices)==game['directions'][side]['attempts']
    print('saved structure, exposure/coverage, basis and annual offsets pass',flush=True)
    target=check_target_join(definition,data,purpose)
    print('full saved target-panel join passes',flush=True)
    incidence=np.asarray(Xt.T@E).ravel();seconds=incidence*3600;counts=np.bincount(Xe.indices,minlength=Xe.shape[1]);origin_info=np.asarray(Xe.T@mass_per_event).ravel()
    coefficients={};betas={};references={};centers={};heads={};numeric={};reference=read(root/'reference.json');saved_projection=arrays(root/'projections.npz');rows=list(json_rows(root/'projections.jsonl'));support=list(json_rows(root/'coefficient-support.jsonl'));adjustments=list(json_rows(root/'adjustments.jsonl'))
    assert len(rows)==len(definition['players']) and len(support)==len(rows)*6 and len(adjustments)==len(rows)*2
    for head in HEADS:
        metadata=read(root/f'heads/{head}.json');flat=arrays(root/f'heads/{head}.npz')['coefficients'];w=WIDTHS[head];size=len(definition['columns'])*w;beta=flat[:size].reshape(-1,w);age=flat[size:] if head=='volume' else np.zeros(8)
        assert age.shape==(8,) and np.all(age==0.) and metadata['solver']['converged'] and metadata['solver']['options']==SOLVER and metadata['solver']['maxfun']==15000 and metadata['solver']['maxls']==20
        info={};priors={p['index']:p for p in metadata['priors']};ledger={(p['block'],p['id'],p['subblock']):p for p in metadata['ledger']}
        for index,p in priors.items():
            c=definition['columns'][index];current=bool((seconds[index]>0 or counts[index]>0) if head=='volume' else origin_info[index]>0);info[index]=current
            assert p['prior_kind']=='entry' and p['prior_anchor_season'] is None and p['prior_seasons']==[] and p['last_supported'] is None and p['age_delta']==[] and p['age_indices']==[] and p['transition_reason']=='entry'
            assert p['prior_only'] is (not current) and p['current_season_information'] is current and all(v==0. for v in p['mean']+p['prior_mean'])
            precision=16. if c['block'].endswith('_player') else 100.;expected_precision=np.full(w,40*precision)
            if head!='shape':expected_precision[0]=precision
            assert p['precision']==expected_precision.tolist() and p['likelihood_events']==int(counts[index])
            assert np.isclose(p['included_seconds'],seconds[index],rtol=1e-12,atol=1e-12) and np.isclose(p['eligible_origin_weight'],origin_info[index],rtol=1e-12,atol=1e-12)
            key=(p['block'],p['id'],p['subblock'])
            if current:assert ledger[key]['coefficient']==beta[index].tolist() and ledger[key]['season']=='20212022' and ledger[key]['support_seasons']==['20212022']
            else:assert np.all(beta[index]==0.) and key not in ledger
        assert len(ledger)==sum(info.values())
        component,g,diagnostics=independent_objective(data,definition,head,beta,age,info)
        gradient_path=output/f'{head}-independent-gradient.npy';np.save(gradient_path,g,allow_pickle=False)
        numeric[head]=dict(independent_evaluations=1,components=component,saved_components=metadata['objective'],component_absolute_differences={k:abs(v-metadata['objective'][k]) for k,v in component.items()},recomputed_gradient_inf_norm=float(abs(g).max()),recorded_gradient_inf_norm=metadata['solver']['raw_gradient_inf_norm'],gradient_norm_difference=float(abs(g).max())-metadata['solver']['raw_gradient_inf_norm'],full_recomputed_gradient=dict(path=str(gradient_path),sha256=sha(gradient_path),shape=list(g.shape)),limitation='saved full gradient is absent; no coordinatewise gradient comparison or new stationarity gate',diagnostics=diagnostics)
        vector=np.zeros(len(beta));vector[0]=1.;vector[1:Xt.shape[1]]=incidence[1:]/H;ref=vector@beta
        assert np.allclose(ref,metadata['reference_predictor'],rtol=1e-12,atol=1e-12)
        center={}
        for saved in metadata['centers']:
            idx=saved['indices'];weight=float(incidence[idx].sum());mean=np.sum(beta[idx]*incidence[idx,None],axis=0)/weight if weight else np.zeros(w)
            assert np.allclose(mean,saved['mean'],rtol=1e-12,atol=1e-12) and np.isclose(saved['reference_applicability'],weight/H,rtol=1e-12,atol=1e-12)
            assert np.allclose(saved['reference_offset'],mean*(weight/H),rtol=1e-12,atol=1e-12);center[saved['block'],saved['subblock']]=mean
        assert np.allclose(ref,reference['heads'][head]['predictor'],rtol=1e-12,atol=1e-12) and np.allclose(vector,reference['heads'][head]['vector'],rtol=1e-12,atol=1e-12)
        coefficients[head]=flat;betas[head]=beta;references[head]=ref;centers[head]=center;heads[head]=metadata
        print('independent endpoint F/fullG and entry/history/reference:',head,flush=True)
    reference_body={k:v for k,v in reference.items() if k!='sha256'};assert reference['sha256']==hashlib.sha256(json.dumps(reference_body,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    neutral=rates(references,offsets,basis);max_map_error=max_scalar_error=0.
    for i,(player,row) in enumerate(zip(definition['players'],rows,strict=True)):
        assert row['player_id']==player and row['available'] and row['reference_id']==reference['sha256'] and row['units']=='per_hour'
        for ri,role in enumerate(ROLES):
            block=('attacking' if role=='offense' else 'defending')+'_player';index=by_actor[block,player,'base'];predictor={h:references[h]+betas[h][index]-centers[h][block,'base'] for h in HEADS};focal=rates(predictor,offsets,basis)
            actual=np.stack((neutral,focal,focal-neutral),axis=1);max_map_error=max(max_map_error,compare_rate(actual,saved_projection['rates'][i,ri]))
            for qi,q in enumerate(QUANTITIES):
                values=dict(neutral=float(neutral[qi].sum()),complete=float(focal[qi].sum()),difference=float((focal[qi]-neutral[qi]).sum()),relative_percent=float(100*(focal[qi]-neutral[qi]).sum()/neutral[qi].sum()))
                for name,v in values.items():
                    stored=row['values'][role][q][name];assert abs(v-stored)<=1e-11*(1+abs(stored));max_scalar_error=max(max_scalar_error,abs(v-stored))
    for s in support:
        side='attacking' if s['role']=='offense' else 'defending';index=by_actor[side+'_player',s['player_id'],'base'];p=next(v for v in heads[s['head']]['priors'] if v['index']==index)
        assert s['prior_kind']=='entry' and s['prior_anchor_season'] is None and s['prior_seasons']==[] and s['available']
        for key in ['included_seconds','likelihood_events','eligible_origin_weight','current_season_information','prior_only']:assert s[key]==p[key]
    print('all standardized native projections/scalars and per-head support pass',flush=True)
    examples=[];orders=list(permutations(range(4)))
    for ri,role in enumerate(ROLES):
        own='attacking' if role=='offense' else 'defending';other='defending' if role=='offense' else 'attacking'
        eligible=[(float(seconds[by_actor[own+'_player',p,'base']]),p) for p in definition['players'] if seconds[by_actor[own+'_player',p,'base']]>0];exposure,player=min(eligible)
        index=by_actor[own+'_player',player,'base'];selected=Xt[:,index].nonzero()[0];total=np.zeros((2,7,656));weight=0.
        for row_index in selected:
            key=definition['time_keys'][int(row_index)];group={}
            for h in HEADS:
                beta=betas[h];a=centers[h][own+'_player','base'];b=centers[h][other+'_player','base'];self_effect=beta[index]-a
                mates=sum((beta[by_actor[own+'_player',str(p),'base']]-a for p in key[own+'_players'] if str(p)!=player),np.zeros(WIDTHS[h]));opponents=sum((beta[by_actor[other+'_player',str(p),'base']]-b for p in key[other+'_players']),np.zeros(WIDTHS[h]))
                factual=linear(Xt[row_index:row_index+1],data['context_time'][row_index:row_index+1],beta).ravel();group[h]=np.stack((self_effect,mates,opponents,factual-references[h]-self_effect-mates-opponents))
            predictors={h:np.stack([references[h]+sum((group[h][g] for g in range(4) if mask&(1<<g)),np.zeros(WIDTHS[h])) for mask in range(16)]) for h in HEADS};coalitions=rates(predictors,offsets,basis);allocation=np.zeros((4,2,656))
            for ordering in orders:
                before=0
                for g in ordering:
                    after=before|(1<<g);allocation[g]+=(coalitions[after]-coalitions[before])/24;before=after
            values=np.concatenate((coalitions[:1],allocation,np.zeros((1,2,656)),coalitions[15:16]),axis=0).transpose(1,0,2);values[:,5]=values[:,6]-values[:,:5].sum(axis=1)
            total+=float(E[row_index])*values;weight+=float(E[row_index])
        total/=weight;pi=definition['players'].index(player);saved=saved_projection['adjustments'][pi,ri];error=compare_rate(total,saved)
        assert abs(weight*3600-exposure)<=1e-8*(1+exposure)
        scalar_error=0.;saved_row=adjustments[pi*2+ri];assert saved_row['player_id']==player and saved_row['role']==role and saved_row['available']
        for qi,q in enumerate(QUANTITIES):
            for k,name in enumerate(ADJUSTMENTS):
                own_value=float(total[qi,k].sum());saved_value=saved_row[q][name];assert abs(own_value-saved_value)<=1e-10*(1+abs(saved_value)+abs(own_value));scalar_error=max(scalar_error,abs(own_value-saved_value))
        examples.append(dict(player_id=player,role=role,selection='smallest positive included seconds, then player id',directed_rows=len(selected),included_seconds=exposure,maximum_native_difference=error,maximum_scalar_difference=scalar_error))
    zero=0
    for i,row in enumerate(adjustments):
        if row['reason']=='no_exposure':assert row['exposure_seconds']==0 and all(v is None for q in QUANTITIES for v in row[q].values()) and np.all(saved_projection['adjustments'][i//2,i%2]==0);zero+=1
    print('two low-time direct24-order actual-context examples pass',flush=True)
    return dict(status='passed_saved_first_year_audit',purpose=purpose,season='20212022',manifest=dict(path=str(root/'manifest.json'),sha256=expected),members=members,member_bytes=sum(r['bytes'] for r in members),design=dict(time_rows=Xt.shape[0],event_rows=ne,origin_rows=len(data['origin_cells']),columns=len(definition['columns']),actor_columns=Xt.shape[1],context_columns=data['context_time'].shape[1],physical_hours=coverage['physical_included_hours'],directed_hours=H,neutral_chance_mass=float(chance.sum()),roster_players=len(definition['players']),base_excluded_segments=sum(len(g['base_excluded_segments']) for g in coverage['games']),added_excluded_segments=sum(len(g['added_excluded_segments']) for g in coverage['games']),known_lost_physical_hours=fsum(g['known_lost_physical_hours'] for g in coverage['games']),known_lost_events=sum(len(g['known_lost_event_source_indices']) for g in coverage['games']),unassigned_gap_game_ids=coverage['unassigned_gap_game_ids']),target_boundary=target,heads=numeric,standardized_projections=dict(players=len(rows),roles=2,maximum_native_difference=max_map_error,maximum_scalar_difference=max_scalar_error),actual_context_examples=examples,no_exposure_adjustment_rows=zero,producer_resources=manifest['resources'],audit_resources=dict(wall_seconds=perf_counter()-began,peak_resident_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)),limits=['one independent F/fullG at each saved endpoint; full original gradients are not saved, so only components and recorded norm can be compared','no stronger gradient convergence gate or final-year numerical resolution claim','actual-context reconstruction covers the two declared low-time role examples, not all players','all retained target rows joined to saved valued numeric evidence; no original source extraction repeated'],calls=dict(independent_objectives={h:1 for h in HEADS},production_evaluator=0,production_reader=0,native_fit=0,source_pass=0,probes=0))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True);parser.add_argument('--expected-manifest-sha256',required=True);parser.add_argument('--purpose',choices=['fixture','real'],required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    root=args.input.resolve();output=args.out.resolve();assert output.is_relative_to('/Volumes/Expansion/hockey-stats') and not output.exists();output.mkdir()
    try:
        result=audit(root,args.expected_manifest_sha256,args.purpose,output)
        (output/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        print(json.dumps(dict(status=result['status'],report=str(output/'audit.json'))))
    except BaseException as error:
        (output/'audit-failure.json').write_text(json.dumps(dict(status='failed',error_type=type(error).__name__,error=str(error)),indent=2)+'\n');raise

if __name__=='__main__':main()
