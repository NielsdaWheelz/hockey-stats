"""saved-only numerical/native/provenance audit; no training evaluator or solver."""
from collections import Counter
from fractions import Fraction as Q
import hashlib
import inspect
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import numpy as np
import scipy
from scipy.optimize import _lbfgsb, _lbfgsb_py

WORK=Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
CAPTURE=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01')
ROOT=CAPTURE/'repair-01'
file_identities={}
def readbytes(path):
    p=Path(path);data=p.read_bytes()
    if p.is_relative_to(ROOT):file_identities[str(p.relative_to(ROOT))]=dict(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
    return data
def sha(path):return hashlib.sha256(readbytes(path)).hexdigest()
def read(path):return json.loads(readbytes(path))
def decode(v):
    if isinstance(v,list):return [decode(x) for x in v]
    if isinstance(v,dict):
        if set(v)=={'hex','classification'}:
            assert v['classification']=='finite';return float.fromhex(v['hex'])
        if set(v)=={'numerator','denominator','rounded'}:
            q=Q(int(v['numerator']),int(v['denominator']));assert float(q).hex()==v['rounded'];return q
        return {k:decode(x) for k,x in v.items()}
    return v
def arr(path):return np.load(io.BytesIO(readbytes(path)),allow_pickle=False)
def snap(path):
    with np.load(io.BytesIO(readbytes(path)),allow_pickle=False) as z:return {k:z[k] for k in z.files}
def bits(a,b):
    a,b=np.asarray(a),np.asarray(b);return a.dtype==b.dtype and a.shape==b.shape and a.tobytes()==b.tobytes()
def exact(a):return sum((Q.from_float(float(x)) for x in a),Q())
def linked(ref):assert sha(ref['path'])==ref['sha256']
def array_digest(coeff):
    h=hashlib.sha256();h.update(json.dumps(['coefficients',coeff.dtype.str,list(coeff.shape)],separators=(',',':')).encode());h.update(coeff.tobytes());return h.hexdigest()

report=read(ROOT/'repair.json');basic=read(ROOT/'basic-qualification.json');qualification=read(ROOT/'qualification/qualification.json');summary=decode(read(ROOT/'continuation-result.json'));raw=decode(read(ROOT/'raw-native-result.json'))
assert report['status']=='qualified' and report['eligible_endpoint'] and report['assembly_performed'] is False
for key in ('inputs','diagnosis','basic_receipt','probability_qualification'):linked(report[key])
assert report['inputs']['sha256']=='031975b95114fbe62c0e468ebdf16d6170c27f15407b7df71ff0b08e18517a6c'
assert report['diagnosis']['sha256']=='115da4fe4c18912b74b1970f1825a4338f0f54c6ccd9f0cfb3f7e10dfa026af1'
assert report['probability_qualification']['sha256']=='2514390196a9e827caaecd67ece0b28cdb069fa5efb7bd339a93970ffd4f9aec'
assert report['execution_fit_sha256']==sha(WORK/'analysis/src/hockey_stats/execution_fit.py')=='2f872b2f0cc9c613e37d28c3a865d0bb410e8ba7302a3798d639b5161178b7f3'
assert report['trace_owner_sha256']==sha(report['trace_owner_path'])=='89af29e14de76a3a8f332b3753c5640d9b6c825f493719163dd687b7b824bc13'
assert report['repair_source_sha256']==sha(WORK/'var/v1-08-replacement/repair_execution_u.py')=='9ddb1425196328fff332f5ba1da91a231d77fce233fe48565e883b9e594d9c69'
launch=(CAPTURE/'repair-01-launch-head.txt').read_text().strip();assert launch=='b85ba959a29971c996f40ec10f3f8d83875e5412'
for ref in ['HEAD',launch]:assert subprocess.check_output(['git','rev-parse',ref+':analysis'],cwd=WORK,text=True).strip()=='fc716257eb118d1a091472cde4b214e8bca1f753'
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=all','--','analysis'],cwd=WORK,text=True).strip()
assert (CAPTURE/'repair-01-launch-analysis-status.txt').read_bytes()==b''
for filename in ('repair-01-launch-helper-sha256.txt','repair-01-launch-trace-sha256.txt','repair-01-launch-diagnostic-helper-sha256.txt','repair-01-launch-command-sha256.txt','repair-01-launch-inputs-sha256.txt','repair-01-launch-acceptance-sha256.txt'):
    for line in (CAPTURE/filename).read_text().splitlines():
        digest,path=line.split(maxsplit=1);p=Path(path);p=p if p.is_absolute() else WORK/p;assert sha(p)==digest
identity=read(ROOT/'native-identity.json');assert scipy.__version__==identity['scipy']=='1.18.1' and np.__version__==identity['numpy']=='2.5.3'
assert sha(_lbfgsb.__file__)==identity['native_module_sha256']
assert hashlib.sha256(inspect.getsource(_lbfgsb_py._minimize_lbfgsb).encode()).hexdigest()==identity['python_wrapper_sha256']
meta=read(CAPTURE/'inputs/inputs.json');input_manifest=read(CAPTURE/'inputs/manifest.json')
assert sha(CAPTURE/'inputs/inputs.json')==input_manifest['inputs']['sha256']
assert qualification['donor']==meta['metadata']['donor'];linked(qualification['donor'])
donor=Path(qualification['donor']['path']).parent;donor_manifest=read(donor/'manifest.json')
for member in donor_manifest['files']:assert sha(donor/member['path'])==member['sha256']
assert meta['metadata']['baseline_head']==read(donor/'heads/u.json')
assert meta['metadata']['incoming_ledger']==read(Path(meta['metadata']['previous']['path']).parent/'heads/u.json')['ledger']
selector=read(donor/'resolution/baseline.json')['selector']
assert selector==meta['selector']==qualification['frozen_selector']
assert len(selector['keys'])==256 and len(selector['fixture_witnesses'])==1 and len(selector['requirements'])==48
assert all(r['disposition'] in ('actual','fixture') for r in selector['requirements'])
assert [p['key'] for p in meta['probes']]==selector['keys']+[p['key'] for p in selector['fixture_witnesses']]
completion=read(WORK/'docs/research/spatial-v1-08/receipts/u-capture-diagnosis-completion.json')
assert len(completion['preserved_donor_npz'])==7
for reference in completion['preserved_donor_npz']:
    assert sha(reference['path'])==reference['sha256'] and Path(reference['path']).stat().st_size==reference['bytes']
for reference in qualification['members'].values():linked(reference)
head=read(qualification['members']['metadata']['path']);coeff=snap(qualification['members']['arrays']['path'])['coefficients']
initial=snap(donor/'heads/u.npz')['coefficients']
print('source/code/input/diagnosis/donor/selector/receipt pins pass',file=sys.stderr,flush=True)

paths=sorted(ROOT.glob('evaluation-[0-9][0-9][0-9]'));assert len(paths)==650
points=[];duplicates=[];byx={};by_response={}
for i,path in enumerate(paths):
    record=decode(read(path/'record.json'));x=arr(path/'x.npy');g=arr(path/'gradient.npy');terms=arr(path/'addends.npy')
    assert record['number']==i and record['status']=='finite' and x.dtype==g.dtype==terms.dtype==np.float64 and x.shape==g.shape==initial.shape==(3420,)
    assert all(np.isfinite(v).all() for v in (x,g,terms)) and math.isfinite(record['loss'])
    ref=exact(terms);assert ref==record['reference'] and bits(float(ref),record['loss']) and record['signed_accumulation_discrepancy']==Q.from_float(record['loss'])-ref
    point=dict(record,x=x,g=g,terms=terms,ref=ref);points.append(point)
    if x.tobytes() in byx:
        old=points[byx[x.tobytes()]];assert bits(old['g'],g) and bits(old['terms'],terms) and bits(old['loss'],record['loss']);duplicates.append((old['number'],i))
    else:byx[x.tobytes()]=i
    signature=(x.tobytes(),g.tobytes(),np.float64(record['loss']).tobytes());by_response.setdefault(signature,[]).append(i)
    if i%200==0:print('exact saved evaluations checked:',i+1,file=sys.stderr,flush=True)
anchor=points[0]
assert bits(anchor['x'],initial) and bits(anchor['g'],arr(CAPTURE/'diagnosis/evaluation-000/gradient.npy')) and bits(anchor['terms'],arr(CAPTURE/'diagnosis/evaluation-000/addends.npy'))
assert bits(anchor['x'],arr(CAPTURE/'diagnosis/evaluation-000/x.npy'))
assert anchor['loss'].hex()=='0x1.10246c4d7d6cap+16'
rawx=arr(ROOT/'raw-native-endpoint.npy');rawg=arr(ROOT/'raw-native-gradient.npy');completed=arr(ROOT/'completed-continuation-endpoint.npy')
assert bits(completed,coeff) and np.isfinite(rawx).all() and np.isfinite(rawg).all() and not np.array_equal(rawx,initial) and not np.array_equal(completed,initial)
assert bits(points[648]['x'],initial) and points[648]['phase']=='qualification_fresh_saved_start'
assert bits(points[649]['x'],rawx) and points[649]['phase']=='qualification_fresh_raw_endpoint'
assert points[649]['loss']<points[648]['loss'] and bits(raw['fun'],points[649]['loss']) and bits(rawg,points[649]['g'])
assert (raw['success'],raw['status'],raw['nit'],raw['nfev'],raw['njev'])==(True,0,588,645,645)
assert hashlib.sha256(rawx.tobytes()).hexdigest()==raw['endpoint_sha256']
assert 'RELATIVE REDUCTION' in raw['message']
comparison=qualification['comparison']
assert bits(float(abs(rawx-initial).max()),basic['raw_coefficient_max_change']) and bits(float(abs(completed-initial).max()),basic['completed_coefficient_max_change'])
assert bits(float(np.linalg.norm(completed-initial)),comparison['coefficient_l2_change'])
assert bits(float(abs(rawg).max()),basic['raw_gradient_max']) and bits(float(abs(rawg-anchor['g']).max()),basic['raw_gradient_max_change'])
assert basic['passed'] and all(v is True for v in basic['checks'].values()) and basic==report['basic_qualification']
assert basic['fresh_start_objective']==points[648]['loss'] and basic['fresh_raw_endpoint_objective']==points[649]['loss']
contract=basic['qualification'];assert qualification['numerical_qualification']==dict(contract,basic_receipt=report['basic_receipt'])
assert array_digest(coeff)==contract['completed_coefficients_sha256']=='c76c976c28739606abd267a3d1e6e467737f9cff11240a0db02ac90b9691916b'
assert contract['accepted_native_iterations']==contract['accepted_callbacks']==588
assert all(contract[k] is True for k in ['native_success','raw_endpoint_moved','completed_endpoint_moved'])
assert head['status']=='complete' and head['selected_start']=='continuation' and head['starts']==summary['starts']
assert summary['status']=='complete' and summary['requested_starts']==['continuation'] and summary['selected_start']=='continuation' and len(summary['starts'])==1
for k,v in summary['comparison'].items():
    if isinstance(v,float):assert bits(v,comparison[k])
    else:assert v==comparison[k]
# independently reproduce prior-only completion, means, centers and inherited ledger.
actors=meta['actors'];expected_completed=rawx.copy()
for actor in actors:
    if not actor['likelihood_support']:expected_completed[actor['index']]=float(actor['mean']+np.dot(actor['age_delta'],expected_completed[actor['age_indices']]))
assert bits(expected_completed,completed)
oldhead=read(donor/'heads/u.json')
for name in ['head','target','design','actors','origin','arrays']:assert head[name]==oldhead[name],name
for current,old,actor in zip(head['priors'],oldhead['priors'],actors,strict=True):
    assert {k:v for k,v in current.items() if k!='prior_mean'}=={k:v for k,v in old.items() if k!='prior_mean'}
    assert bits(current['prior_mean'],float(actor['mean']+np.dot(actor['age_delta'],completed[actor['age_indices']])))
expected_actors=[dict(actor,prior_mean=float(actor['mean']+np.dot(actor['age_delta'],completed[actor['age_indices']]))) for actor in actors]
assert expected_actors==summary['actors']
for block,center in head['centers'].items():
    rows=[a for a in head['actors'] if a['block']==block];weight=sum(a['center_weight'] for a in rows)
    value=float(sum(a['center_weight']*completed[a['index']] for a in rows)/weight if weight else 0.)
    assert center==dict(value=value,weight=float(weight),prior_only=not bool(weight))
ledger={(a['block'],str(a['id'])):dict(a) for a in meta['metadata']['incoming_ledger']}
for actor in actors:
    if actor['likelihood_support']:ledger[actor['block'],str(actor['id'])]=dict(block=actor['block'],id=actor['id'],coefficient=float(completed[actor['index']]),season='20252026',role=actor['role'],age=actor['age'])
assert head['ledger']==sorted(ledger.values(),key=lambda a:(a['block'],str(a['id'])))
print('650 sums/repeats, fresh strict decrease, actual raw/completed motion and all reference/history accounting pass',file=sys.stderr,flush=True)

# every complete native snapshot, response and accepted callback is independently bound.
previous=None;accepted=[];consumed=[];native_controls=set();event_count=0
for i in range(1234):
    info=read(ROOT/f'native-{i:03d}.json');before=snap(ROOT/f'native-{i:03d}-before.npz');after=snap(ROOT/f'native-{i:03d}-after.npz')
    assert info['number']==i and info['status']=='complete' and info['before_task']==before['task'].tolist() and info['after_task']==after['task'].tolist()
    assert int(before['m'])==int(after['m'])==10 and int(before['maxls'])==int(after['maxls'])==20
    assert np.all(before['nbd']==0) and np.all(after['nbd']==0) and bits(float(before['pgtol']),1e-7)
    assert bits(float(before['factr'])*np.finfo(np.float64).eps,1e-16)
    if previous is not None:
        for key in before:
            if key not in ['f','gradient']:assert bits(before[key],previous[key]),(i,key)
    if info['before_task'] in ([3,301],[3,302]):
        signature=(before['x'].tobytes(),before['gradient'].tobytes(),before['f'].tobytes())
        candidates=by_response[signature];idx=info['consumed_evaluation'];assert idx in candidates and 1<=idx<=645
        consumed.append(idx)
    elif previous is not None:
        assert bits(before['f'],previous['f']) and bits(before['gradient'],previous['gradient'])
    if int(after['task'][0])==1:
        callback=arr(ROOT/f'callback-{len(accepted):03d}.npy');assert bits(callback,after['x'])
        assert int(after['isave'][29])==len(accepted)+1;accepted.append(callback)
    previous=after;event_count+=1
    if i%400==0:print('native saved transitions checked:',i+1,file=sys.stderr,flush=True)
assert event_count==report['native_events']==1234 and len(accepted)==report['callbacks']==588
assert len(list(ROOT.glob('callback-*.npy')))==588 and bits(accepted[-1],rawx)
assert bits(previous['x'],rawx) and bits(previous['gradient'],rawg) and bits(previous['f'],raw['fun'])
assert consumed==sorted(consumed) and set(consumed)==set(range(1,646))
assert report['full_objective_calls']==report['resources']['full_objective_calls']==650 and report['native_objective_calls']==645
assert report['native_limit_overruns']==dict(iterations=0,evaluations=0) and report['native_evaluation_count_matches'] is True
assert report['native_limits']==dict(maxiter=10000,maxfun=15000,maxls=20,ftol=1e-16,gtol=1e-7)
assert report['added_global_evaluation_cap'] is None and report['added_native_evaluation_cap'] is None
# bind every remaining trace/control file and keep a sorted file identity receipt locally.
for path in ROOT.rglob('*'):
    if path.is_file() and str(path.relative_to(ROOT)) not in file_identities:sha(path)
assert sum(v['bytes'] for name,v in file_identities.items() if name!='repair.json')==report['trace_bytes_excluding_final_receipt']==2259013571
for ref in ['inputs','diagnosis','basic_receipt','probability_qualification']:linked(report[ref])
assert (CAPTURE/'repair-01-exit.txt').read_text()=='0\n'
log=(CAPTURE/'repair-01.log').read_text();assert '470.93 real' in log and '3329949696  maximum resident set size' in log and '3308522328  peak memory footprint' in log
assert report['resources']['peak_memory_bytes']==3329949696
assert report['resources']['qualification_wall_seconds']==qualification['wall_seconds']
assert not (ROOT/'manifest.json').exists()
output=WORK/'var/v1-08-replacement/u-exact-repair-saved-independent-file-identities.json'
output.write_text(json.dumps(dict(sorted(file_identities.items())),indent=2)+'\n')
result=dict(status='passed',scope='saved numerical/native/provenance audit only; no objective, source reconstruction, native call, score or assembly',launch_head=launch,analysis_tree='fc716257eb118d1a091472cde4b214e8bca1f753',repair_receipt_sha256=sha(ROOT/'repair.json'),probability_qualification_sha256=report['probability_qualification']['sha256'],full_objective_calls=650,native_full_calls=645,native_events=1234,accepted_native_iterations=len(accepted),callbacks=588,native_consumed_responses=len(consumed),identical_input_repeat_pairs=duplicates,raw_endpoint_sha256=raw['endpoint_sha256'],completed_coefficients_sha256=array_digest(coeff),fresh_saved_start=points[648]['loss'],fresh_raw_endpoint=points[649]['loss'],strict_objective_decrease=points[649]['loss']-points[648]['loss'],raw_max_change=float(abs(rawx-initial).max()),completed_max_change=float(abs(completed-initial).max()),completed_l2_change=float(np.linalg.norm(completed-initial)),raw_gradient_max=float(abs(rawg).max()),raw_gradient_max_change=float(abs(rawg-anchor['g']).max()),prior_only_completed_coordinates=int(np.count_nonzero(rawx!=completed)),source_metadata_unchanged=True,retained_npz_members_checked=7,all_selector_requirements_available=48,trace_files_hashed=len(file_identities),trace_bytes_excluding_final_receipt=report['trace_bytes_excluding_final_receipt'],file_identities_path=str(output),file_identities_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),command_wall_seconds=470.93,peak_resident_bytes=3329949696,peak_footprint_bytes=3308522328,assembly_performed=False)
print(json.dumps(result,indent=2))
