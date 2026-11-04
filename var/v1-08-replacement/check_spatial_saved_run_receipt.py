"""temporary tiny saved-run bundles; no production, source or array reads."""
from contextlib import redirect_stdout
import io
import sys
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('saved_run_receipt',here/'write_spatial_saved_run_receipt.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
scratch=Path(tempfile.mkdtemp(prefix='spatial-run-receipt-',dir=here));h.CAMPAIGN=scratch
command_sha='a'*64;head='b'*40

def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,allow_nan=False)+'\n')
def bundle(year):
 campaign=Path(tempfile.mkdtemp(prefix='case-',dir=scratch));h.CAMPAIGN=campaign
 current=campaign/'real/spatial'/year;previous=campaign/'real/spatial'/f'{int(year[:4])-1}{year[:4]}'
 previous.mkdir(parents=True,exist_ok=True);write(previous/'manifest.json',dict(kind='spatial_state',purpose='real',season=previous.name))
 previous_sha=sha256((previous/'manifest.json').read_bytes()).hexdigest()
 manifest=dict(kind='spatial_state',purpose='real',season=year,previous=dict(path=str(previous/'manifest.json'),sha256=previous_sha,season=previous.name,purpose='real',usage='annual'),
  prepared=dict(path=h.PREPARED,sha256=h.PREPARED_SHA),coaches=dict(path=h.COACHES,sha256=h.COACHES_SHA),
  valued=dict(path=str(campaign/'real/scores'/year/'manifest.json'),sha256=h.SCORES[year],season=year),
  implementation=dict(git_commit='c'*40,git_dirty=False),heads=[],files=[],resources={'producer':'copied'})
 for name in h.HEADS:
  data=dict(head=name,status='complete',reasons=[],solver=dict(converged=True,options=h.SOLVER,maxfun=15000,maxls=20,raw_gradient_inf_norm=.01),objective=dict(total=3.,likelihood=2.,penalty=1.),resources={'head':'copied'})
  path=current/f'heads/{name}.json';write(path,data)
  manifest['heads'].append(dict(head=name,status='complete'))
  manifest['files'].append(dict(path=f'heads/{name}.json',sha256=sha256(path.read_bytes()).hexdigest()))
 if year=='20252026':
  for name in h.HEADS:
   for suffix,data in (('.json',dict(head=name,status='complete',solver=dict(converged=True,options=h.CONTINUATION,maxfun=15000,maxls=20))),('-comparison.json',dict(status='passed',reason=None,maxima={},failures=[]))):
    path=current/f'probes/{name}{suffix}';write(path,data);manifest['files'].append(dict(path=f'probes/{name}{suffix}',sha256=sha256(path.read_bytes()).hexdigest()))
 write(current/'manifest.json',manifest)
 expected={h.PREPARED:h.PREPARED_SHA,h.COACHES:h.COACHES_SHA,str(campaign/'real/scores'/year/'manifest.json'):h.SCORES[year],str(previous/'manifest.json'):previous_sha,
  str(campaign/h.EXECUTION[year][0]):h.EXECUTION[year][1]}
 records={'-exit.txt':'0\n','-start.txt':'2026-01-01T00:00:00Z\n','-finish.txt':'2026-01-01T00:01:00Z\n','-shell.pid':'123\n',
  '-launch-head.txt':head+'\n','-launch-analysis-tree.txt':h.ANALYSIS+'\n','-launch-analysis-status.txt':'',
  '-launch-command-sha256.txt':command_sha+'  /synthetic/command.sh\n','-launch-inputs-sha256.txt':''.join(f'{sha}  {p}\n' for p,sha in expected.items()),
  '-launch-acceptance-sha256.txt':'d'*64+'  /synthetic/accepted.json\n','-launch-spatial-recipe.txt':h.RECIPE+'\n',
  '.log':'4.5 real 6.0 user 7.0 sys\n123456 maximum resident set size\n234567 peak memory footprint\n'}
 for suffix,value in records.items():Path(str(current)+suffix).write_text(value)
 return current,previous,manifest,previous_sha

def inspect(current,previous,manifest,previous_sha):
 write(current/'manifest.json',manifest);expected=sha256((current/'manifest.json').read_bytes()).hexdigest()
 original_bytes=Path.read_bytes;original_text=Path.read_text
 def small_bytes(path,*args,**kwargs):assert (path.suffix=='.json' or path.name.startswith(current.name+'-') or path.name==current.name+'.log') and path.is_relative_to(scratch);return original_bytes(path,*args,**kwargs)
 def run_text(path,*args,**kwargs):assert path.is_relative_to(scratch);return original_text(path,*args,**kwargs)
 with patch.object(Path,'read_bytes',small_bytes),patch.object(Path,'read_text',run_text):
  return h.saved_run_receipt(current,previous,expected,previous_sha,command_sha)

passed=[]
for year in h.SCORES:
 current,previous,manifest,previous_sha=bundle(year);r=inspect(current,previous,manifest,previous_sha)
 assert r['status']=='saved_run_passed_pending_history_audit_and_root_acceptance' and r['launch']['head']==head and r['implementation']['git_commit']=='c'*40
 assert r['whole_command']['maximum_resident_bytes']==123456 and r['whole_command']['peak_memory_footprint_bytes']==234567
 assert len(r['probes'])==(3 if year=='20252026' else 0)
 passed.append(year)
refused=[]
for defect in ('current_manifest_pin','previous_manifest_pin','wrong_valued','wrong_previous','head_incomplete','head_control','head_digest','probe_early','probe_missing','probe_failed','wrong_source','dirty_source','wrong_command','wrong_inputs','bad_exit','wrong_recipe','occupied_receipt'):
 year='20252026' if defect.startswith('probe_') and defect!='probe_early' else '20232024'
 current,previous,m,previous_sha=bundle(year)
 if defect=='wrong_valued':m['valued']['sha256']='0'*64
 elif defect=='wrong_previous':m['previous']['sha256']='0'*64
 elif defect in ('head_incomplete','head_control'):
  path=current/'heads/volume.json';data=json.loads(path.read_text())
  if defect=='head_incomplete':data['status']='failed';m['heads'][0]['status']='failed'
  else:data['solver']['options']['maxiter']=1
  write(path,data);m['files'][0]['sha256']=sha256(path.read_bytes()).hexdigest()
 elif defect=='head_digest':m['files'][0]['sha256']='0'*64
 elif defect=='probe_early':(current/'probes').mkdir(exist_ok=True)
 elif defect=='probe_missing':m['files']=[row for row in m['files'] if row['path']!='probes/quality-comparison.json']
 elif defect=='probe_failed':
  path=current/'probes/volume-comparison.json';write(path,dict(status='failed'));next(row for row in m['files'] if row['path']=='probes/volume-comparison.json')['sha256']=sha256(path.read_bytes()).hexdigest()
 else:
  suffix={'wrong_source':'-launch-analysis-tree.txt','dirty_source':'-launch-analysis-status.txt','wrong_command':'-launch-command-sha256.txt','wrong_inputs':'-launch-inputs-sha256.txt','bad_exit':'-exit.txt','wrong_recipe':'-launch-spatial-recipe.txt'}.get(defect)
  if suffix:
   replacement='3\n' if defect=='bad_exit' else '0'*64+'  /synthetic/command.sh\n' if defect=='wrong_command' else Path(str(current)+suffix).read_text().replace(h.SCORES[year],'0'*64) if defect=='wrong_inputs' else 'wrong\n'
   Path(str(current)+suffix).write_text(replacement)
 try:
  if defect in ('current_manifest_pin','previous_manifest_pin'):
   write(current/'manifest.json',m);expected=sha256((current/'manifest.json').read_bytes()).hexdigest()
   h.saved_run_receipt(current,previous,'0'*64 if defect=='current_manifest_pin' else expected,'0'*64 if defect=='previous_manifest_pin' else previous_sha,command_sha)
  elif defect=='occupied_receipt':
   output=scratch/'occupied.json';output.write_text('preserve\n');h.write_receipt(current,previous,'0'*64,previous_sha,command_sha,output)
  else:inspect(current,previous,m,previous_sha)
 except (AssertionError,KeyError,FileExistsError):refused.append(defect)
 else:raise AssertionError('admitted '+defect)
current,previous,m,previous_sha=bundle('20242025');Path(str(current)+'.log').write_text('without time metrics\n')
r=inspect(current,previous,m,previous_sha);assert r['whole_command']==dict(timing=None,maximum_resident_bytes=None,peak_memory_footprint_bytes=None)
output=Path(str(current)+'-saved-metadata-acceptance.json');expected=sha256((current/'manifest.json').read_bytes()).hexdigest()
argv=['write_spatial_saved_run_receipt.py','--input',str(current),'--previous',str(previous),'--expected-manifest-sha256',expected,'--expected-previous-manifest-sha256',previous_sha,'--expected-command-sha256',command_sha,'--out',str(output)]
with patch.object(sys,'argv',argv),redirect_stdout(io.StringIO()):assert h.main()==0
assert json.loads(output.read_text())['status']==r['status']
try:h.write_receipt(current,previous,expected,previous_sha,command_sha,current/'unlisted-receipt.json')
except AssertionError:pass
else:raise AssertionError('receipt placed inside preserved state')
print(json.dumps(dict(status='passed',scope='tiny synthetic json/run records only; no real/fixture source, model, arrays, production reader or math calls',seasons=passed,refusals=refused,missing_resource_metrics_are_null=True,producer_and_launch_head_remain_distinct=True,small_json_only=True,explicit_cli_fresh_receipt=True,inside_state_output_refused=True,scratch=str(scratch)),indent=2))
