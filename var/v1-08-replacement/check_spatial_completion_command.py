"""temporary held-shell and adapter orchestration controls; all inputs are tiny stubs."""
from contextlib import redirect_stdout
from hashlib import sha256
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

here=Path(__file__).resolve().parent;source=(here/'real-20222023-spatial-completion-command.sh.held').read_text()
scratch=Path(tempfile.mkdtemp(prefix='spatial-completion-command-',dir=here));results=[]
assert len(shlex.split(source.split('for spatial_path in ',1)[1].split('; do',1)[0]))==15
for mode in ('pending_review','pass','adapter_exit3','wrong_input','occupied_output','occupied_preflight','dirty_analysis'):
 root=scratch/mode;work=root/'work';work.mkdir(parents=True);campaign=root/'campaign'
 paths=dict(spatial_campaign=campaign,spatial_prepared=root/'prepared',spatial_coaches=root/'coaches/coaches.json',spatial_valued=campaign/'real/scores/20222023',spatial_previous=campaign/'real/spatial/20212022',completion_adapter=work/'var/v1-08-replacement/complete_real_spatial_20222023.py')
 script=source.replace('/Users/nnandal/Documents/code/hockey-stats-v1-08',str(work))
 for literal,path in (('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01',campaign),('/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02',paths['spatial_prepared']),('/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json',paths['spatial_coaches'])):script=script.replace(literal,str(path))
 assert '/Volumes/' not in script
 if mode=='pending_review':
  shell=work/'command.sh';shell.write_text(script);done=subprocess.run(['/bin/zsh',str(shell)],cwd=root,capture_output=True,text=True)
  assert done.returncode==1 and 'review pending' in done.stderr and not campaign.exists();results.append(dict(mode=mode,exit=done.returncode,adapter_called=False));continue
 members={}
 for line in source.splitlines():
  if not line.startswith('spatial_pin '):continue
  _,name,digest=shlex.split(line)
  if name.startswith('$'):
   variable=name[1:].split('/')[0];tail=name[len(variable)+1:].lstrip('/');path=paths[variable]/tail if tail else paths[variable]
  else:path=work/name
  path.parent.mkdir(parents=True,exist_ok=True);path.write_text('tiny pin '+name+'\n');members[name]=path
  if not digest.startswith('$'):script=script.replace(digest,sha256(path.read_bytes()).hexdigest())
 script=script.replace('WITHHELD_REVIEWED_COMPLETION_ADAPTER_SHA256',sha256(paths['completion_adapter'].read_bytes()).hexdigest())
 stub=work/'analysis/.venv/bin/python';stub.parent.mkdir(parents=True);stub.write_text('#!/bin/sh\nprintf invoked > "$COMPLETION_MARKER"\nprintf "%s\\n" "$@" > "$COMPLETION_ARGV"\nexit "$COMPLETION_EXIT"\n');stub.chmod(0o755)
 (work/'analysis/fixed.txt').write_text('fixed source\n')
 def git(*args):return subprocess.check_output(['git',*args],cwd=work,text=True).strip()
 git('init','-q');git('config','user.email','fixture@example.invalid');git('config','user.name','fixture');git('add','analysis');git('commit','-q','-m','fixture')
 tree=git('rev-parse','HEAD:analysis');head=git('rev-parse','HEAD');script=script.replace('WITHHELD_REVIEWED_COMPLETION_ANALYSIS_TREE',tree)
 original=campaign/'real/spatial/20222023';(original/'heads').mkdir(parents=True);(original/'heads/volume.json').write_text('original preserved head\n');Path(str(original)+'-exit.txt').write_text('130\n')
 protected={path:sha256(path.read_bytes()).hexdigest() for path in [original/'heads/volume.json',Path(str(original)+'-exit.txt')]}
 output=campaign/'real/spatial/20222023-complete-01'
 if mode=='wrong_input':members['$spatial_valued/manifest.json'].write_text('wrong input\n')
 if mode=='occupied_output':output.mkdir()
 if mode=='occupied_preflight':Path(str(output)+'-completion-preflight.json').write_text('occupied\n')
 if mode=='dirty_analysis':(work/'analysis/unreviewed.py').write_text('changed\n')
 shell=work/'command.sh';shell.write_text(script);marker=root/'called';argv=root/'argv'
 done=subprocess.run(['/bin/zsh',str(shell)],cwd=root,capture_output=True,text=True,env=dict(os.environ,COMPLETION_MARKER=str(marker),COMPLETION_ARGV=str(argv),COMPLETION_EXIT='3' if mode=='adapter_exit3' else '0'))
 if mode in ('pass','adapter_exit3'):
  expected=3 if mode=='adapter_exit3' else 0
  assert done.returncode==expected and marker.exists(),(mode,done.stderr)
  assert Path(str(output)+'-exit.txt').read_text().strip()==str(expected) and Path(str(output)+'-finish.txt').exists()
  reconnection=members['docs/research/spatial-v1-08/receipts/real-second-spatial-reconnection-preflight.json']
  assert argv.read_text().splitlines()==[str(paths['completion_adapter']),'--expected-head',head,'--expected-analysis-tree',tree,'--expected-reconnection-sha256',sha256(reconnection.read_bytes()).hexdigest()]
 else:assert done.returncode!=0 and not marker.exists() and not Path(str(output)+'-start.txt').exists(),(mode,done.stderr)
 assert all(sha256(path.read_bytes()).hexdigest()==digest for path,digest in protected.items())
 results.append(dict(mode=mode,exit=done.returncode,adapter_called=marker.exists(),old_partial_untouched=True))

# the fixed adapter composes the ordinary source owners once, without any real read.
spec=importlib.util.spec_from_file_location('completion_adapter',here/'complete_real_spatial_20222023.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
from hockey_stats import analysis_data, spatial_design, spatial_rates, spatial_state
calls=[];output=scratch/'adapter-output';design=SimpleNamespace(resources={});previous=object();files={'stub':'sha'};origin={'inputs':{'stub':'binding'}}
def preflight(*args):assert args==('b'*40,'a'*40,'c'*64);calls.append('preflight');return files,origin,{}
def read_previous(*args):assert args==(adapter.PREVIOUS,'real');calls.append('previous');return previous
def read_prepared(*args):assert args==(adapter.PREPARED,'real');calls.append('prepared');return 'prepared'
def prepare(*args):assert args==('prepared',adapter.COACHES,adapter.VALUED,'20222023');calls.append('design');return design
def complete(*args,**kwargs):assert args==(design,previous,adapter.SOURCE,output) and kwargs==dict(expected_files=files,expected_inputs=origin['inputs']);calls.append('complete');return SimpleNamespace(path=output)
with patch.object(adapter,'preflight',preflight),patch.object(adapter,'OUTPUT',output),patch.object(analysis_data,'read_prepared',read_prepared),patch.object(spatial_state,'read_spatial_state',read_previous),patch.object(spatial_design,'prepare_spatial',prepare),patch.object(spatial_rates,'complete_spatial',complete),patch.object(sys,'argv',['adapter','--expected-head','b'*40,'--expected-analysis-tree','a'*40,'--expected-reconnection-sha256','c'*64]),redirect_stdout(io.StringIO()):assert adapter.main()==0
assert calls==['preflight','previous','prepared','design','complete'] and Path(str(output)+'-completion-preflight.json').exists()
print(json.dumps(dict(status='passed',scope='scratch shell/pins/git/native stubs and adapter owner-call stubs only; no actual source/design/array/model/reader',shell_controls=results,adapter_calls=calls,scratch=str(scratch)),indent=2))
