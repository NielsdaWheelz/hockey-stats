"""tiny saved-json year-two history and held-dispatch controls; no artifacts."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('second_spatial_metadata',here/'accept_real_spatial_20222023.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
scratch=Path(tempfile.mkdtemp(prefix='spatial-second-metadata-',dir=here))
previous=scratch/'20212022';current=scratch/'20222023'
for root in (previous,current):(root/'heads').mkdir(parents=True)
def write(path,value):path.write_text(json.dumps(value,allow_nan=False)+'\n')
def ledger(block,actor,width):return dict(block=block,id=actor,subblock='base',coefficient=[.5]*width,
    season='20212022',position_group='F' if block.endswith('_player') else None,age=27. if block.endswith('_player') else None,support_seasons=['20212022'])
old_heads={};new_heads={}
for head in h.HEADS:
    width={'volume':1,'shape':40,'quality':41}[head]
    old=[ledger('attacking_player',actor,width) for actor in ('a','p')]+[ledger('attacking_coach',actor,width) for actor in ('c','absent')]
    old.append(dict(ledger('attacking_coach','c',width),subblock='shell'))
    old.sort(key=lambda row:(row['block'],row['id'],row['subblock']))
    lookup={(row['block'],row['id'],row['subblock']):row for row in old}
    priors=[];out={key:deepcopy(row) for key,row in lookup.items()}
    for block,actor,subblock,info in (('attacking_player','a','base',True),('attacking_player','p','base',False),('attacking_player','new','base',True),('attacking_player','zero','base',False),('attacking_coach','c','base',True),('attacking_coach','c','shell',False)):
        last=lookup.get((block,actor,subblock));player=block.endswith('_player')
        scalar=(16. if player else 100.) if last is None else (100. if player else 400.)
        precision=[scalar*40]*width
        if head!='shape':precision[0]=scalar
        mean=[0.]*width if last is None else last['coefficient']
        delta=[.1,.01] if head=='volume' and player and last else []
        indices=[0,1] if delta else []
        reason='entry' if last is None else 'age_carry' if delta else 'age_neutral'
        prior=dict(block=block,id=actor,subblock=subblock,position_group='F' if player else None,age=28. if player else None,
            current_season_information=info,prior_only=not info,mean=mean,precision=precision,
            prior_kind='entry' if last is None else 'carry',prior_anchor_season=None if last is None else '20212022',
            prior_seasons=[] if last is None else ['20212022'],last_supported=last,age_delta=delta,age_indices=indices,transition_reason=reason,
            prior_mean=mean)
        # use the same represented arithmetic as the saved age-delta contract.
        if delta:
            now,earlier=(28.-27.)/10,(27.-27.)/10;prior['age_delta']=[now-earlier,now*now-earlier*earlier]
        priors.append(prior)
        if info:out[(block,actor,subblock)]=dict(block=block,id=actor,subblock=subblock,coefficient=[.6]*width,season='20222023',
            position_group=prior['position_group'],age=prior['age'],support_seasons=prior['prior_seasons']+['20222023'])
    old_heads[head]=dict(head=head,status='complete',ledger=old)
    new_heads[head]=dict(head=head,status='complete',reasons=[],priors=priors,ledger=[out[key] for key in sorted(out)],
        solver=dict(converged=True,options=h.SOLVER,maxfun=15000,maxls=20,raw_gradient_inf_norm=.001),
        objective=dict(total=3.,likelihood=2.,penalty=1.),resources={},age_curves=None)
base=dict(kind='spatial_state',purpose='fixture',recipe=dict(heads=list(h.HEADS),modes=40,solver=h.SOLVER),
    prepared=dict(path='/synthetic/prepared/manifest.json',sha256='1'*64),coaches=dict(path='/synthetic/coaches.json',sha256='2'*64),
    basis_identity={'synthetic':'fixed'},resources={})
def finalize(root,manifest,heads):
    value=deepcopy(manifest);value['heads']=[];value['files']=[]
    for head,data in heads.items():
        path=root/f'heads/{head}.json';write(path,data)
        value['heads'].append(dict(head=head,status=data['status']));value['files'].append(dict(path=f'heads/{head}.json',sha256=sha256(path.read_bytes()).hexdigest()))
    write(root/'manifest.json',value)
old=dict(base,season='20212022',previous=None,valued=dict(sha256='3'*64,season='20212022'))
finalize(previous,old,old_heads);previous_sha=sha256((previous/'manifest.json').read_bytes()).hexdigest()
new=dict(base,season='20222023',previous=dict(path=str(previous/'manifest.json'),sha256=previous_sha,season='20212022',purpose='fixture',usage='annual'),valued=dict(sha256='4'*64,season='20222023'))
finalize(current,new,new_heads)
kwargs=dict(purpose='fixture',previous_sha256=previous_sha,prepared_sha256='1'*64,coaches_sha256='2'*64,valued_sha256='4'*64)
result=h.inspect_second_year(current,previous,**kwargs)
assert result['eligible_as_predecessor'] and all(row['history']['carry_rows']==4 and row['history']['entry_rows']==2 for row in result['heads'].values())
refused=[]
for defect in ('last_supported','mean','precision','prior_only_advance','absent_ledger_dropped','anchor_gap','previous_binding'):
    changed=deepcopy(new_heads);manifest=deepcopy(new)
    head=changed['volume'];prior=next(row for row in head['priors'] if row['id']=='a')
    if defect=='last_supported':prior['last_supported']=dict(prior['last_supported'],coefficient=[9.])
    elif defect=='mean':prior['mean']=[9.]
    elif defect=='precision':prior['precision']=[16.]
    elif defect=='prior_only_advance':next(row for row in head['ledger'] if row['id']=='p')['season']='20222023'
    elif defect=='absent_ledger_dropped':head['ledger']=[row for row in head['ledger'] if row['id']!='absent']
    elif defect=='anchor_gap':prior['prior_anchor_season']='20202021'
    else:manifest['previous']['path']='/synthetic/execution/20212022/manifest.json'
    finalize(current,manifest,changed)
    try:h.inspect_second_year(current,previous,**kwargs)
    except AssertionError:refused.append(defect)
    else:raise AssertionError('bad history accepted: '+defect)
changed=deepcopy(new_heads);changed['volume'].update(status='failed',reasons=['synthetic_failure'],ledger=old_heads['volume']['ledger'],solver=None,objective=None)
finalize(current,new,changed)
assert h.inspect_second_year(current,previous,**kwargs)['eligible_as_predecessor'] is False
broken_old=deepcopy(old_heads);broken_old['volume']['status']='failed'
finalize(previous,old,broken_old)
broken_sha=sha256((previous/'manifest.json').read_bytes()).hexdigest();rebound=deepcopy(new);rebound['previous']['sha256']=broken_sha
finalize(current,rebound,new_heads)
try:h.inspect_second_year(current,previous,**dict(kwargs,previous_sha256=broken_sha))
except AssertionError:pass
else:raise AssertionError('incomplete spatial predecessor admitted')
with patch.object(Path,'read_bytes',side_effect=AssertionError('read before predecessor pin')),patch.object(Path,'read_text',side_effect=AssertionError('read before predecessor pin')):
    try:h.main()
    except AssertionError as error:assert str(error)=='accepted first spatial annual pin remains pending'
    else:raise AssertionError('held metadata helper entered real inputs')
print(json.dumps(dict(status='passed',scope='tiny synthetic saved JSON and held main guard only; no real/fixture artifact, model, source, fit, arrays, objective or strict reader',
    history_refusals=refused,carry_entry_gap_prioronly_absent_ledger=True,incomplete_annual_not_eligible=True,incomplete_predecessor_refused=True,coach_base_and_shell_history_independent=True,pending_main_refuses_before_io=True,scratch=str(scratch)),indent=2))
