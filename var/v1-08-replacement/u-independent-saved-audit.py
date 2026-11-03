"""read-only independent arithmetic audit; never imports a project evaluator."""
from fractions import Fraction as Q
import hashlib
import inspect
import json
import math
from pathlib import Path
import re
import subprocess
import numpy as np
import scipy
from scipy.optimize import _lbfgsb, _lbfgsb_py

WORK=Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
ROOT=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01')
D=ROOT/'diagnosis'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def decode(v):
    if isinstance(v,list):return [decode(x) for x in v]
    if isinstance(v,dict):
        if set(v)=={'hex','classification'}:
            assert v['classification']=='finite';return float.fromhex(v['hex'])
        if set(v)=={'numerator','denominator','rounded'}:
            q=Q(int(v['numerator']),int(v['denominator']));assert float(q).hex()==v['rounded'];return q
        return {k:decode(x) for k,x in v.items()}
    return v
def bits(a,b):
    a,b=np.asarray(a),np.asarray(b)
    return a.dtype==b.dtype and a.shape==b.shape and a.tobytes()==b.tobytes()
def arr(p):return np.load(p,allow_pickle=False)
def snap(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def exact_sum(a):return sum(map(lambda v:Q.from_float(float(v)),a),Q())
def eq_fields(actual,expected):
    assert actual.keys()==expected.keys(),(actual.keys(),expected.keys())
    for k,v in actual.items():
        if isinstance(v,float):assert bits(v,expected[k]),(k,v,expected[k])
        else:assert v==expected[k],(k,v,expected[k])

pins={
'var/v1-08-replacement/capture_execution_u.py':'e42f7be944a5350a9096b953559835cddbeb6f9a2081113f01eae32131951d5c',
'var/v1-08-replacement/diagnose_execution_u.py':'2142a218e9759c9103db29e728605efaf7492363efd888cd2c019b956f51ec4d',
'var/v1-08-replacement/consumed_start_check.py':'ef4995e579855950cab475cc2ac237f6ce22538429cc1f04d675b48838a6fca4',
'var/v1-08-replacement/real-u-capture-command.sh':'1e88d781780e16bf85d32d7d11060a2afaa6306eccbdd98e5c3ca3b2f1116c0a'}
for p,h in pins.items():assert sha(WORK/p)==h
assert subprocess.check_output(['git','rev-parse','HEAD:analysis'],cwd=WORK,text=True).strip()=='54e41d821b1cc12fb262be4c42d6898a610c37fe'
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=all','--','analysis'],cwd=WORK,text=True).strip()
launch=read(ROOT/'capture-start.json');reload=read(ROOT/'capture-reloaded.json')
assert launch['actual_launch_head']=='17791dd73223ab0046b40ecf1674ca8f5f6c562e'
assert subprocess.check_output(['git','rev-parse',launch['actual_launch_head']+':analysis'],cwd=WORK,text=True).strip()==launch['reviewed_analysis_tree']=='54e41d821b1cc12fb262be4c42d6898a610c37fe'
for k,p in [('capture','capture_execution_u.py'),('diagnosis','diagnose_execution_u.py'),('source_observer','consumed_start_check.py')]:assert launch[k]['sha256']==pins['var/v1-08-replacement/'+p]
manifest=read(ROOT/'inputs/manifest.json')
assert sha(ROOT/'inputs/manifest.json')=='031975b95114fbe62c0e468ebdf16d6170c27f15407b7df71ff0b08e18517a6c'==reload['bundle']['sha256']
refs=[manifest['inputs'],manifest['arrays'],manifest['fixed'],*manifest['batches']]
assert len(manifest['batches'])==6748
assert [r['path'] for r in manifest['batches']]==[f'batches/{i:05d}.npz' for i in range(6748)]
for ref in refs:
    p=ROOT/'inputs'/ref['path'];assert p.resolve().is_relative_to((ROOT/'inputs').resolve());assert p.stat().st_size==ref['bytes'];assert sha(p)==ref['sha256']
assert sum(r['bytes'] for r in refs)==manifest['payload_bytes']==reload['payload_bytes']==1856985404
meta=read(ROOT/'inputs/inputs.json')
assert meta['metadata']['bindings']==launch['bindings']
for reference in launch['bindings'].values():assert sha(reference['path'])==reference['sha256']
for k in ['donor','previous','source_check']:
    reference=meta['metadata'][k];assert sha(reference['path'])==reference['sha256']
donor=Path(meta['metadata']['donor']['path']).parent
saved_head=read(donor/'heads/u.json');assert meta['metadata']['baseline_head']==saved_head
previous=Path(meta['metadata']['previous']['path']).parent
assert meta['metadata']['incoming_ledger']==read(previous/'heads/u.json')['ledger']
selector=read(donor/'resolution/baseline.json')['selector'];assert meta['selector']==selector
assert len(selector['keys'])==256 and len(selector['requirements'])==48 and len(selector['fixture_witnesses'])==1
assert [p['key'] for p in meta['probes']]==selector['keys']+[p['key'] for p in selector['fixture_witnesses']]
assert selector['synthetic_geometry']['types']==['wrist','snap','slap','backhand','tip','other'] and selector['synthetic_geometry']['cells']==list(range(656))
source=read(ROOT/'source-check.json');expected=read(launch['bindings']['source_report']['path'])
for key in source:
    if key!='observer_seconds':assert source[key]==expected[key],key
assert source['source_context_sha256']==meta['metadata']['source_context_sha256']=='f96ee4a0eadeb2f5caa44db999c71b9ad0e6a178b8a3812f9895019dcdb065a3'
assert source['source_response_sha256']==meta['metadata']['source_response_sha256']=='63e224a6d8ac06729882bd05b1dcd817df49d39000fb8559817e0e1d01feef04'
# selected small baseline/layout vectors only; never fixed/dynamic csr arrays.
with np.load(ROOT/'inputs/head.npz',allow_pickle=False) as z:
    initial=z['initial'];maps=z['map_indices'];circ=z['circumstance_indices'];ages=z['age_indices']
assert initial.shape==(3420,) and meta['design']['size']==3420 and len(meta['design']['keys'])==151381
with np.load(donor/'heads/u.npz',allow_pickle=False) as z:assert bits(initial,z['coefficients'])
print('pins, every captured payload digest, donor/history/source metadata and frozen selector pass',flush=True)

report=decode(read(D/'diagnosis.json'));directions_report=decode(read(D/'direction-evidence.json'))
assert report['directions']==directions_report
assert report['bundle_manifest_sha256']==reload['bundle']['sha256']
folders=sorted(D.glob('evaluation-[0-9][0-9][0-9]'))
assert len(folders)==208
points=[];identities={};repeated=[]
for i,p in enumerate(folders):
    record=decode(read(p/'record.json'));x=arr(p/'x.npy');g=arr(p/'gradient.npy');terms=arr(p/'addends.npy')
    assert record['number']==i and record['status']=='finite' and x.shape==g.shape==initial.shape
    assert all(np.isfinite(v).all() for v in (x,g,terms)) and math.isfinite(record['loss'])
    assert terms.dtype==np.float64 and terms.ndim==1
    q=exact_sum(terms);assert q==record['reference']
    assert Q.from_float(record['loss'])-q==record['signed_accumulation_discrepancy']
    item=dict(record,x=x,g=g,terms=terms,q=q);points.append(item)
    key=x.tobytes()
    if key in identities:
        first=points[identities[key]]
        assert bits(first['g'],g) and bits(first['terms'],terms) and bits(first['loss'],record['loss'])
        repeated.append((identities[key],i))
    else:identities[key]=i
anchor=points[0];g=anchor['g']
assert bits(initial,anchor['x']) and bits(anchor['loss'],69668.42305740231) and bits(float(abs(g).max()),0.002770559377087478)
assert all(bits(points[i]['x'],initial) for i in (0,1,2))
assert report['capture_validation']['objective_bits']==np.float64(anchor['loss']).tobytes().hex()
assert report['capture_validation']['gradient_max_bits']==np.float64(abs(g).max()).tobytes().hex()
# regenerate all direction membership, sign rules and exact floating endpoints.
names=meta['design']['design']['coefficient_names'];actors=meta['actors'];supported=[a['index'] for a in actors if a['likelihood_support']]
order=['gradient','largest_gradient_coordinate','intercept','base_maps','type_maps','circumstances','supported_shooter_actors','attacking_coaches','defending_coaches','ages','supported_actor_age','prior_only','all']
groups=dict(base_maps=maps[0],type_maps=maps[1:].ravel(),circumstances=circ,ages=ages,supported_actor_age=supported+list(ages),prior_only=[a['index'] for a in actors if not a['likelihood_support']],all=range(len(names)))
for name,block in [('supported_shooter_actors','shooter'),('attacking_coaches','attacking_coach'),('defending_coaches','defending_coach')]:groups[name]=[a['index'] for a in actors if a['block']==block and a['likelihood_support']]
steps=[1e-1,1e-2,1e-3,1e-4,1e-5,1e-6,1e-7];cursor=3;windows={};bad=[]
for name in order:
    v=np.zeros(len(names),dtype=np.float64)
    if name=='gradient':v[:]=g
    elif name=='largest_gradient_coordinate':v[int(np.argmax(abs(g)))]=1.
    elif name=='intercept':v[names.index('intercept')]=1.
    else:
        for index in sorted(set(groups[name])):v[index]=1. if hashlib.sha256((name+'\0'+names[index]).encode()).digest()[0]&1==0 else -1.
    norm=np.linalg.norm(v);rec=directions_report[name]
    if norm==0:assert rec['status']=='unavailable_empty_group';continue
    v/=norm;assert bits(v,arr(D/f'direction-{name}.npy'))
    analytic=float(np.dot(g,v));assert bits(analytic,rec['analytic'])
    slopes=[]
    for h in steps:
        end=[]
        for sign in (1.,-1.):
            point=points[cursor];assert bits(point['x'],initial+(sign*h)*v)
            assert point['phase']==f'{name}:h={h}:sign={sign}'
            end.append(point);cursor+=1
            if name=='gradient' and h==1e-3:
                assert bits(point['x'],points[cursor]['x']);cursor+=1
        p,m=end
        ordinary=Q.from_float(float((p['loss']-m['loss'])/(2*h)))
        ref=(p['q']-m['q'])/Q.from_float(float(2*h))
        saved=rec['points'][len(slopes)]
        assert saved['plus']==p['number'] and saved['minus']==m['number'] and saved['D']==ordinary and saved['R']==ref and bits(saved['h'],h)
        slopes.append((ordinary,ref))
    calculated=[]
    for i in range(1,6):
        noise=abs(slopes[i][0]-slopes[i][1]);trend=max(abs(slopes[i][1]-slopes[i-1][1]),abs(slopes[i][1]-slopes[i+1][1]));budget=noise+trend;gap=Q.from_float(analytic)-slopes[i][1]
        row=dict(index=i,h=steps[i],ordinary=slopes[i][0],reference=slopes[i][1],signed_discrepancy=gap,outer_error=noise,truncation_trend=trend,empirical_budget=budget,outside=abs(gap)>budget,contains_analytic=abs(gap)<=budget,excludes_zero=abs(slopes[i][1])>budget)
        eq_fields(row,rec['scales'][i-1]);calculated.append(row)
    resolved=unresolved=None
    for a,b in zip(calculated,calculated[1:]):
        if unresolved is None and a['outside'] and b['outside'] and a['signed_discrepancy']*b['signed_discrepancy']>0:unresolved=[a['index'],b['index']]
        if resolved is None and a['contains_analytic'] and b['contains_analytic'] and a['excludes_zero'] and b['excludes_zero']:resolved=[a['index'],b['index']]
    assert rec['resolved_window']==resolved and rec['unresolved_window']==unresolved
    windows[name]=dict(resolved=resolved,unresolved=unresolved)
    if unresolved is not None:bad.append(name)
assert cursor==187 and not bad and windows['gradient']['resolved']==[4,5]
print('208 exact component sums, all repeats, 182 finite-difference endpoints and frozen windows pass',flush=True)

# native binding uses snapshots alone, with no observer import or solver call.
identity=read(D/'native-identity.json')
assert scipy.__version__==identity['scipy']=='1.18.1' and np.__version__==identity['numpy']=='2.5.3'
assert identity['source_commit']=='e4e854eaa8f18d807cd3496028e257e36caa93cc'
assert sha(_lbfgsb.__file__)==identity['native_module_sha256']
assert hashlib.sha256(inspect.getsource(_lbfgsb_py._minimize_lbfgsb).encode()).hexdigest()==identity['python_wrapper_sha256']
events=[]
for i in range(22):
    info=read(D/f'native-{i:03d}.json');before=snap(D/f'native-{i:03d}-before.npz');after=snap(D/f'native-{i:03d}-after.npz')
    assert info['number']==i and info['status']=='complete' and info['before_task']==before['task'].tolist() and info['after_task']==after['task'].tolist()
    assert int(before['m'])==int(after['m'])==10 and int(before['maxls'])==int(after['maxls'])==20
    assert np.all(before['nbd']==0) and np.all(after['nbd']==0)
    assert bits(float(before['pgtol']),1e-7)
    assert bits(float(before['factr'])*np.finfo(np.float64).eps,1e-16)
    if i:
        for key in before:
            if key not in ['f','gradient']:assert bits(events[-1]['after'][key],before[key]),(i,key)
    event=dict(info=info,before=before,after=after)
    if info['before_task'] in ([3,301],[3,302]):
        candidates=[p for p in points[188:207] if bits(p['x'],before['x']) and bits(p['g'],before['gradient']) and bits(p['loss'],before['f'])]
        assert candidates
        idx=info['consumed_evaluation'];assert any(p['number']==idx for p in candidates)
        event['point']=points[idx]
    events.append(event)
first=events[1]['after'];n=len(initial);direction=first['wa'][int(first['isave'][12]):int(first['isave'][12])+n];start=first['wa'][int(first['isave'][13]):int(first['isave'][13])+n]
assert bits(start,initial) and bits(direction,np.subtract(np.subtract(initial,g),initial))
assert int(first['isave'][29])==0 and int(first['isave'][27])==0 and int(first['isave'][30])==0 and bits(float(first['dsave'][0]),1.) and int(first['lsave'][1])==0
f1a=f1b=0.
for value in g:
    neg=float(-value);f1a=float(f1a-float(neg*neg));f1b=math.fma(-neg,neg,f1b)
assert all(math.isfinite(f) and f!=0 and float(-f/float(-f))==1. for f in (f1a,f1b))
direction_saved=decode(read(D/'native-first-direction-evidence.json'))
assert bits(f1a,direction_saved['f1_separate']) and bits(f1b,direction_saved['f1_fma'])
assert np.count_nonzero(direction!=-g)==direction_saved['different_from_ideal_coordinates']==2052
assert bits(float(np.linalg.norm(direction+g)/np.linalg.norm(g)),direction_saved['relative_ideal_residual'])
assert bits(np.dot(g,direction),direction_saved['analytic_gradient_dot_native_direction'])
assert bits(-np.dot(g,g),direction_saved['ideal_negative_gradient_squared_norm'])
trials=[];saved_trials=decode(read(D/'trial-evidence.json'))
for request,consume in zip(events,events[1:]):
    a=request['after'];b=consume['before'];c=consume['after']
    if a['task'].tolist()!=[3,302]:continue
    assert bits(a['x'],b['x'])
    p=consume['point'];ds=a['dsave'];step=float(ds[13]);gdold=float(ds[14]);gd=float(c['dsave'][10]);gtest=float(.001*gdold)
    d=a['wa'][int(a['isave'][12]):int(a['isave'][12])+n];s=a['wa'][int(a['isave'][13]):int(a['isave'][13])+n]
    assert bits(d,direction) and bits(s,initial) and bits(float(ds[1]),anchor['loss']) and bits(float(ds[20]),anchor['loss']) and bits(float(ds[17]),gtest)
    # accept either compiler expression form for the actual vector construction.
    separate=s+step*d;fused=np.array([math.fma(step,float(v),float(x)) for v,x in zip(d,s)])
    assert np.all((p['x']==separate)|(p['x']==fused))
    start_candidates=[v for v in points[:p['number']+1] if bits(v['x'],s) and bits(v['loss'],float(ds[1]))];startp=start_candidates[-1]
    orig=[float(ds[1])+float(step*gtest),math.fma(step,gtest,float(ds[1]))]
    refstart=float(startp['q']);reftrial=float(p['q']);refthresholds=[refstart+float(step*gtest),math.fma(step,gtest,refstart)]
    om=[p['loss']-v for v in orig];rm=[reftrial-v for v in refthresholds]
    exact=p['q']-startp['q'];limit=Q.from_float(step)*Q.from_float(gtest);curvature=float(.9*(-gdold))-abs(gd)
    displaced=not np.array_equal(p['x'],s)
    positive=bool(displaced and step>0 and gdold<0 and all(v>0 for v in om) and all(v<0 for v in rm) and exact<limit and curvature>0)
    item=dict(positive_witness=positive,associated=True,displaced=displaced,step=step,gdold=gdold,gd=gd,gtest=gtest,original_thresholds=orig,rounded_reference_thresholds=refthresholds,original_margins=om,rounded_margins=rm,exact_decrease=exact,exact_limit=limit,exact_margin=exact-limit,curvature_margin=curvature,signed_accumulation_discrepancy=Q.from_float(p['loss'])-p['q'],start_accumulation_discrepancy=Q.from_float(startp['loss'])-startp['q'],search_start_evaluation=startp['number'],request_event=request['info']['number'],consumption_event=consume['info']['number'],response_evaluation=p['number'])
    eq_fields(item,saved_trials[len(trials)]);trials.append(item)
assert len(trials)==len(saved_trials)==20
witness=next(t for t in trials if t['positive_witness']);assert witness==report['first_positive_witness']
assert (witness['request_event'],witness['consumption_event'],witness['response_evaluation'],witness['search_start_evaluation'])==(2,3,190,188)
assert all(bits(x,2**-31) for x in witness['original_margins']) and all(bits(x,-1.5*2**-35) for x in witness['rounded_margins'])
raw=decode(read(D/'raw-native-result.json'));rawx=arr(D/'raw-native-endpoint.npy');rawg=arr(D/'raw-native-gradient.npy')
assert (raw['success'],raw['status'],raw['nit'],raw['nfev'],raw['njev'])==(False,2,0,19,19)
assert bits(raw['fun'],anchor['loss']) and bits(rawx,initial) and sha(D/'raw-native-endpoint.npy')
assert hashlib.sha256(rawx.tobytes()).hexdigest()==raw['endpoint_sha256']
assert bits(rawx,events[-1]['after']['x']) and bits(rawg,events[-1]['after']['gradient']) and bits(rawg,g)
assert not list(D.glob('callback-*.npy')) and report['callbacks']==0
assert report['full_objective_calls']==208<=256 and report['native_objective_calls']==19<=64 and report['native_events']==22
assert report['status']=='arithmetic_repair_permitted' and report['reproduced'] and not report['eligible_endpoint']
assert len(points[188:207])==raw['nfev']
tracebytes=sum(p.stat().st_size for p in D.rglob('*') if p.is_file() and p.name!='diagnosis.json')
assert tracebytes==report['trace_bytes_excluding_final_receipt']==64194026
assert (ROOT.parent/'u-repair-01-exit.txt').read_text()=='0\n'
assert (ROOT.parent/'u-repair-01-launch-analysis-status.txt').read_bytes()==b''
assert (ROOT.parent/'u-repair-01-launch-head.txt').read_text().strip()==launch['actual_launch_head']
assert (ROOT.parent/'u-repair-01-launch-analysis-tree.txt').read_text().strip()==launch['reviewed_analysis_tree']
for name,key in [('capture','capture_execution_u.py'),('diagnosis','diagnose_execution_u.py')]:assert (ROOT.parent/f'u-repair-01-launch-{name}-sha256.txt').read_text().split()[0]==pins['var/v1-08-replacement/'+key]
assert report['wall_seconds']>0 and reload['reload_wall_seconds']>0
log=(ROOT.parent/'u-repair-01.log').read_text()
assert '7163.67 real' in log and '19359678464  maximum resident set size' in log and '20272201328  peak memory footprint' in log
result=dict(status='passed',scope='saved-only independent audit; no evaluator, source reconstruction, solve, score or campaign mutation',bundle_manifest_sha256=sha(ROOT/'inputs/manifest.json'),pins=pins,physical_rows=151381,dimension=3420,batches=6748,payload_bytes=manifest['payload_bytes'],trace_bytes_excluding_final_receipt=tracebytes,total_campaign_file_bytes=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()),full_calls=208,native_full_calls=19,native_events=22,native_trials=20,native_cache_reuses=2,repeat_pairs=repeated,windows=windows,first_witness={k:(str(v) if isinstance(v,Q) else v) for k,v in witness.items()},all_positive_trial_events=[t['request_event'] for t in trials if t['positive_witness']],raw_endpoint_unchanged=True,eligible_endpoint=False,source_code_frozen=True,selector_actual=256,selector_fixture=1,selector_requirements=48,wall_seconds=7163.67,peak_resident_bytes=19359678464,peak_footprint_bytes=20272201328)
print(json.dumps(result,indent=2))
