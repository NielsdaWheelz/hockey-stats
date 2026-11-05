"""temporary canonical tiny completion integration; no real or saved fixture reads."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import ModuleType

import numpy as np
from hockey_stats import spatial_rates as rates, spatial_state as state
from hockey_stats.captures import InputContractError
from hockey_stats.spatial_design import _actor_columns, CONTEXT_AXES, RECIPE

assert callable(rates.complete_spatial), 'completed-head boundary missing'
spec=importlib.util.spec_from_file_location('completion_tiny',Path('analysis/research/spatial_v1_08_checks/state_integration.py'))
tiny=importlib.util.module_from_spec(spec);spec.loader.exec_module(tiny)
# frozen ordinary source is the behavioral reference; no tests monkeypatch fit_head.
reference=ModuleType('hockey_stats._completion_original');reference.__package__='hockey_stats';sys.modules[reference.__name__]=reference
original=subprocess.check_output(['git','show','4dee763:analysis/src/hockey_stats/spatial_rates.py'])
exec(compile(original,'<frozen ordinary spatial source>','exec'),reference.__dict__)
scratch=Path(tempfile.mkdtemp(prefix='spatial-head-completion-',dir=Path(__file__).resolve().parent))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,allow_nan=False)+'\n')
d=tiny.design();previous=reference.fit_spatial(d,None,scratch/'previous')
players=tuple(sorted((set(d.players)-{'0'})|{'11'}));columns=tuple(_actor_columns(players,d.coach_ids)+[dict(kind='context',name=a['name']) for a in CONTEXT_AXES])
old={c['name']:i for i,c in enumerate(d.columns)};old_indices=[old[c['name'].replace(':11',':0')] for c in columns if c['kind']!='context']
def keys(rows):return tuple(dict(row,**{side+'_players':['11' if p=='0' else p for p in row[side+'_players']] for side in ('attacking','defending')}) for row in rows)
transforms=deepcopy(d.transforms);transforms['design_sha256']=hashlib.sha256(json.dumps(dict(recipe=RECIPE['sha256'],columns=columns,transforms={'axes':transforms['axes']}),sort_keys=True,separators=(',',':')).encode()).hexdigest()
coverage=deepcopy(d.coverage);coverage['season']='20222023';coverage['players']['11']=coverage['players'].pop('0')
xt,xe=d.X_time[:,old_indices],d.X_event[:,old_indices];xt.sort_indices();xe.sort_indices()
later=replace(d,season='20222023',valued=dict(d.valued,season='20222023'),players=players,columns=columns,X_time=xt,X_event=xe,
 player_facts={p:dict(position_group='F',age_days=27*365.2425) for p in players},time_keys=keys(d.time_keys),event_keys=keys(d.event_keys),transforms=transforms,coverage=coverage)
donor=reference.fit_spatial(later,previous,scratch/'donor')
ordinary=rates.fit_spatial(later,previous,scratch/'ordinary')
for h in rates.HEADS:
 assert donor.heads[h]['objective']==ordinary.heads[h]['objective'] and donor.heads[h]['solver']==ordinary.heads[h]['solver']
 assert np.array_equal(donor.head_arrays[h]['coefficients'],ordinary.head_arrays[h]['coefficients'])
for name in donor.projection_arrays:assert np.array_equal(donor.projection_arrays[name],ordinary.projection_arrays[name])
files={f'heads/{h}{suffix}':digest(donor.path/f'heads/{h}{suffix}') for h in rates.HEADS for suffix in ('.json','.npz')}
inputs={k:{n:ref[n] for n in ('path','sha256')} for k,ref in [('prepared',later.prepared),('coaches',later.coaches),('valued',later.valued),('previous',dict(path=str(previous.path/'manifest.json'),sha256=digest(previous.path/'manifest.json')))]}
counts={};
def profile(frame,event,arg):
 if event=='call' and frame.f_globals.get('__name__','').startswith('hockey_stats'):
  name=frame.f_code.co_name
  if name in ('fit_head','solve_logistic','run_numerical_probes','_complete_prior_only','head_objective','project_spatial','read_spatial_state'):counts[name]=counts.get(name,0)+1
sys.setprofile(profile)
try:completed=rates.complete_spatial(later,previous,donor.path,scratch/'completed',expected_files=files,expected_inputs=inputs)
finally:sys.setprofile(None)
assert counts.get('head_objective')==3 and all(counts.get(n,0)==0 for n in ('fit_head','solve_logistic','run_numerical_probes','_complete_prior_only')),counts
first_counts=dict(counts)
assert completed.probes is None and completed.manifest['resources']['fit_wall_seconds']==0
assert 'completion' not in completed.manifest
assert completed.manifest['resources']['completion']['source_files']==[dict(path=str(donor.path/name),sha256=files[name]) for name in files]
for name,expected in files.items():assert digest(donor.path/name)==digest(completed.path/name)==expected
for name in donor.projection_arrays:assert np.array_equal(donor.projection_arrays[name],completed.projection_arrays[name])
state.read_spatial_state(completed.path,'fixture')
refused=[]
for defect in ('wrong_input','wrong_prior','absent_anchor','objective','gradient','controls','grouped_rows','prior_only','dtype','file_pin','occupied'):
 source=scratch/defect;(source/'heads').mkdir(parents=True)
 for name in files:shutil.copyfile(donor.path/name,source/name)
 bad_design=later
 name='heads/volume.json' if defect=='grouped_rows' else 'heads/shape.json';data=json.loads((source/name).read_text())
 if defect=='wrong_input':bad_design=replace(later,valued=dict(later.valued,sha256='1'*64))
 elif defect=='wrong_prior':
  prior=next(p for p in data['priors'] if p['prior_kind']=='carry' and p['current_season_information']);prior['mean'][0]+=.1;prior['prior_mean'][0]+=.1;prior['last_supported']['coefficient'][0]+=.1
 elif defect=='absent_anchor':data['ledger']=[r for r in data['ledger'] if not (r['id']=='0' and r['block'].endswith('_player'))]
 elif defect=='objective':data['objective']['total']+=.1;data['objective']['likelihood']+=.1
 elif defect=='gradient':data['solver']['raw_gradient_inf_norm']+=.1
 elif defect=='controls':data['solver']['options']['maxiter']=1
 elif defect=='grouped_rows':data['resources']['dimensions']['grouped_time_rows']=0
 elif defect=='prior_only':
  coefficients=donor.head_arrays['shape']['coefficients'].copy();prior=next(p for p in data['priors'] if p['prior_only']);coefficients[prior['index']*40]+=.1
  np.savez_compressed(source/'heads/shape.npz',coefficients=coefficients)
 elif defect=='dtype':np.savez_compressed(source/'heads/shape.npz',coefficients=donor.head_arrays['shape']['coefficients'].astype(np.float32))
 write(source/name,data);expected={n:digest(source/n) for n in files}
 if defect=='file_pin':expected['heads/shape.json']='0'*64
 output=scratch/f'{defect}-out'
 if defect=='occupied':output.mkdir()
 before=dict(counts);sys.setprofile(profile)
 try:rates.complete_spatial(bad_design,previous,source,output,expected_files=expected,expected_inputs=inputs)
 except InputContractError:refused.append(defect)
 else:raise AssertionError('completion admitted '+defect)
 finally:sys.setprofile(None)
 assert counts.get('project_spatial',0)==before.get('project_spatial',0),defect
assert all(counts.get(n,0)==0 for n in ('fit_head','solve_logistic','run_numerical_probes','_complete_prior_only'))
print(json.dumps(dict(status='passed',scope='canonical tiny source-owned design fixture only; no real artifact/source/array/model pass',ordinary_path_preserved=True,canonical_completion_readback=True,exact_six_head_bytes=True,projection_arrays_equal=True,completion_first_call_counts={k:first_counts.get(k,0) for k in ('fit_head','solve_logistic','run_numerical_probes','_complete_prior_only','head_objective','project_spatial','read_spatial_state')},refusals=refused,scratch=str(scratch)),indent=2))
