"""saved coefficients/predictors and shared pure branches; independent maxima reduction."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from hockey_stats.execution import execution_branch_probabilities
from hockey_stats.execution_design import ExecutionPredictor,SetterCandidate
from hockey_stats.execution_state import ExecutionState

WORK=Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
CAPTURE=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01')
ROOT=CAPTURE/'repair-01'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def values(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
q=read(ROOT/'qualification/qualification.json');assert sha(ROOT/'qualification/qualification.json')=='2514390196a9e827caaecd67ece0b28cdb069fa5efb7bd339a93970ffd4f9aec'
meta=read(CAPTURE/'inputs/inputs.json');assert sha(CAPTURE/'inputs/inputs.json')==read(CAPTURE/'inputs/manifest.json')['inputs']['sha256']
donor_path=Path(q['donor']['path']);assert sha(donor_path)==q['donor']['sha256'];dm=read(donor_path)
heads={h:read(donor_path.parent/f'heads/{h}.json') for h in ['u','q','r','g']}
arrays={h:values(donor_path.parent/f'heads/{h}.npz') for h in heads}
for h in heads:
    for suffix in ['json','npz']:
        name=f'heads/{h}.{suffix}';ref=next(r for r in dm['files'] if r['path']==name);assert sha(donor_path.parent/name)==ref['sha256']
assert heads['u']==meta['metadata']['baseline_head']
base=ExecutionState(donor_path,dm,heads,arrays,{})
for ref in q['members'].values():assert sha(ref['path'])==ref['sha256']
newheads=dict(heads,u=read(q['members']['metadata']['path']));newarrays=dict(arrays,u=values(q['members']['arrays']['path']))
variant=replace(base,heads=newheads,arrays=newarrays,usage='numerical_probe')
selector=read(donor_path.parent/'resolution/baseline.json')['selector'];assert selector==meta['selector']==q['frozen_selector']
assert len(selector['requirements'])==48 and all(r['disposition'] in ['actual','fixture'] for r in selector['requirements'])
assert selector['synthetic_geometry']['types']==['wrist','snap','slap','backhand','tip','other'] and selector['synthetic_geometry']['cells']==list(range(656))
probes=[]
for saved in meta['probes']:
    record=dict(saved,setter_prior=tuple(SetterCandidate(**c) for c in saved['setter_prior']))
    record['context']=dict(saved['context'],strength=tuple(saved['context']['strength']))
    probes.append(ExecutionPredictor(**record))
assert [p.key for p in probes]==selector['keys']+[p['key'] for p in selector['fixture_witnesses']]
assert selector['synthetic_geometry']['context_key']==probes[0].key
results={'head_maximum_changes':dict.fromkeys(['u','q','r','g'],0.),'terminal_maximum_changes':dict.fromkeys(['block','miss','stopped','continuing','goal'],0.)}
locators={'maximum_probability_change':None,'head_maximum_changes':{},'terminal_maximum_changes':{}}
maximum=0.;origins=branches=compared=0
# independently select the first maximum in c order, then the first comparison on ties.
def inspect_values(family,name,left,right,p,cells,neutral,branch_axis):
    global maximum
    assert left.shape==right.shape and np.isfinite(left).all() and np.isfinite(right).all()
    delta=np.abs(left-right);largest=float(delta.max());flat=int(np.flatnonzero(delta.ravel()==largest)[0]);index=np.unravel_index(flat,delta.shape)
    branch=int(index[1]) if delta.ndim==2 else None
    location=dict(key=p.key,population='synthetic' if p.key.startswith('synthetic:') else 'fixture' if p.key.startswith('synthetic-resolution:') else 'actual',execution='fully_neutral' if neutral else 'actual',shot_type=int(p.shot_type),neutralize=list(neutral),origin_cell=int(cells[index[0]]),setter_branch=branch,setter_kind=branch_axis[branch].kind if branch is not None else None,setter_actor_id=branch_axis[branch].actor_id if branch is not None else None,quantity=name,left=float(left[index]),right=float(right[index]),change=largest)
    if name not in locators[family] or largest>results[family][name]:locators[family][name]=location
    if locators['maximum_probability_change'] is None or largest>maximum:locators['maximum_probability_change']=dict(location,family=family)
    results[family][name]=max(results[family][name],largest);maximum=max(maximum,largest)
def compare(p,cells,neutral):
    global origins,branches,compared
    left=execution_branch_probabilities(base,p,cells,neutral);right=execution_branch_probabilities(variant,p,cells,neutral)
    assert left.origin_cells==right.origin_cells==tuple(map(int,cells)) and left.setter_branches==right.setter_branches
    assert np.array_equal(left.prior_probabilities,right.prior_probabilities)
    origins+=len(cells);branches+=len(cells)*len(left.setter_branches);compared+=1
    for name in ['u','q','r','g']:inspect_values('head_maximum_changes',name,getattr(left,name),getattr(right,name),p,cells,neutral,left.setter_branches)
    for name in ['block','miss','stopped','continuing','goal']:inspect_values('terminal_maximum_changes',name,left.terminal_probabilities[name],right.terminal_probabilities[name],p,cells,neutral,left.setter_branches)
neutralizations=[(),('shooter','setter','goalie','coaching')]
for i,p in enumerate(probes):
    cells=np.arange(656,dtype=np.int64) if p.blocked else np.array([p.proxy_cell],dtype=np.int64)
    for neutral in neutralizations:compare(p,cells,neutral)
    if i%80==0:print('saved probe contexts recomputed:',i+1,file=sys.stderr,flush=True)
for shot_type,name in enumerate(selector['synthetic_geometry']['types']):
    p=replace(probes[0],key='synthetic:'+name,shot_type=shot_type,tip=name=='tip',blocked=False)
    for neutral in neutralizations:compare(p,np.asarray(selector['synthetic_geometry']['cells'],dtype=np.int64),neutral)
results.update(maximum_probability_change=maximum,evaluated_origins=origins,evaluated_branches=branches)
for key,value in results.items():assert value==q['comparison'][key],key
assert locators==q['locators']
assert origins==123666 and branches==1132870 and compared==526
assert all(results['head_maximum_changes'][h]==0. for h in ['q','r','g'])
assert maximum==3.98377414095874e-6<=1e-5 and q['probability_passed'] is True
print(json.dumps(dict(status='passed',scope='separate saved numerical audit: shared pure branch evaluator and independent maximum/tie/locator reduction only; no training objective, gradient, fit, source reconstruction, probe selection, score command or assembly',qualification_sha256=sha(ROOT/'qualification/qualification.json'),saved_actual_probes=256,saved_fixture_probes=1,available_requirements=48,compared_context_neutralizations=compared,results=results,locators=locators,all_locators_exact=True,assembly_performed=False),indent=2))
