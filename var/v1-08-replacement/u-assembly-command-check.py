"""temporary assembly CLI/shell and saved-byte audit controls; scratch only."""
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from hockey_stats.artifacts import write_json
from hockey_stats.captures import InputContractError
from hockey_stats.chance_cli import identity

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('u_assembly_cli',HERE/'assemble_execution_u.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
command_path=HERE/'real-u-assembly-command.sh';command=command_path.read_text()
subprocess.run(['zsh','-n',str(command_path)],check=True)
assert f'assembly_tree={m.ANALYSIS_TREE}' in command and f'assembly_helper_sha={identity(HERE/"assemble_execution_u.py")["sha256"]}' in command
assert f'assembly_root={m.OUTPUT.parent}' in command
assert 'assembly_head=$(git rev-parse HEAD)' in command
assert '=PENDING' not in command
assert 'assembly_acceptance=/Users/nnandal/Documents/code/hockey-stats-v1-08/docs/research/spatial-v1-08/reviews/u-exact-repair-saved-review.md' in command
assert 'assembly_acceptance_sha=836e772305415496e437c4319a8ae04fae46970d0b431e38a542ad1d5d7ffbdf' in command
assert 'keep the whole head, analysis and helper fixed from launch until this command exits' in command
for path,sha in m.PINS.items():assert 'assembly_pin '+str(path)+' '+sha in command
line=shlex.split(next(line for line in command.splitlines() if line.startswith('/usr/bin/time')))
assert line[:6]==['/usr/bin/time','-l','env','PYTHONPATH=analysis/src','analysis/.venv/bin/python','var/v1-08-replacement/assemble_execution_u.py']
assert line[6:]==['--repair','$assembly_repair','--output','$assembly_root/20252026','--expected-launch-head','$assembly_head',
    '--expected-helper-sha256','$assembly_helper_sha','--acceptance','$assembly_acceptance','--acceptance-sha256','$assembly_acceptance_sha','>','$assembly_root.log','2>&1']
scratch=Path(tempfile.mkdtemp(prefix='u-assembly-command-',dir=HERE))
old=scratch/'synthetic-donor';out=scratch/'synthetic-assembled'
for root in (old,out):
    (root/'heads').mkdir(parents=True);(root/'resolution').mkdir()
paths=[f'heads/{h}.npz' for h in ('u','q','r','g')]+[f'resolution/{h}.npz' for h in ('q','r','g')]
for name in paths:
    for root in (old,out):(root/name).write_bytes(('synthetic coefficient bytes '+name).encode())
retained=[dict(path=name,sha256=identity(old/name)['sha256']) for name in paths]
comparison={'maximum_probability_change':0.}
heads={}
for h in ('u','q','r','g'):
    source=dict(head=h,source_support={'synthetic':1},resolution={'status':'failed'})
    write_json(old/f'heads/{h}.json',source)
    heads[h]=dict(source,resolution=dict(status='passed',comparison=comparison))
for h in ('q','r','g'):
    body=dict(metadata={'head':h},comparison={'synthetic':0.},arrays={'path':f'resolution/{h}.npz'})
    write_json(old/f'resolution/{h}.json',dict(body,baseline={'sha256':'old'}))
    write_json(out/f'resolution/{h}.json',dict(body,baseline={'sha256':'new'}))
manifest=dict(purpose='fixture',season='20252026',recipe={'synthetic':True},prepared={},coaches={},previous={'synthetic':True},training_cutoff='2026-04-01')
write_json(old/'manifest.json',dict(manifest,files=retained))
launch_head='a'*40
current=dict(manifest,implementation=dict(git_commit=launch_head,git_dirty=False),u_repair={'retained_members':retained})
descriptor=dict(selector={'keys':['synthetic:1']},heads=[{'head':h,'synthetic':True} for h in heads])
write_json(old/'resolution/baseline.json',descriptor)
write_json(out/'resolution/baseline.json',dict(descriptor,identity={'implementation':current['implementation']}))
write_json(out/'manifest.json',{'kind':'synthetic-audit-control'})
state=SimpleNamespace(path=out/'manifest.json',manifest=current,heads=heads,usage='annual')
qualification={'comparison':comparison}
audit=m.saved_audit(state,old/'manifest.json',qualification,launch_head)
assert len(audit['retained_members'])==7 and audit['extra_strict_reads']==audit['full_objective_calls']==audit['probability_comparisons']==0
source=(out/'heads/u.npz').read_bytes();(out/'heads/u.npz').write_bytes(source+b'changed')
try:m.saved_audit(state,old/'manifest.json',qualification,launch_head)
except InputContractError:pass
else:raise AssertionError('changed retained bytes accepted')
(out/'heads/u.npz').write_bytes(source)
qpath=out/'resolution/q.json';source=qpath.read_bytes();changed=json.loads(source);changed['comparison']['synthetic']=1
qpath.write_text(json.dumps(changed))
try:m.saved_audit(state,old/'manifest.json',qualification,launch_head)
except InputContractError:pass
else:raise AssertionError('changed q probe comparison accepted')
qpath.write_bytes(source)
# main owner is stubbed, so no actual assembler/reader/evaluator can run.
repair=scratch/'repair.json';probability=scratch/'qualification.json';acceptance=scratch/'accepted-review.md'
acceptance.write_text('synthetic accepted review control\n')
write_json(probability,dict(probability_passed=True,donor={'path':str(old/'manifest.json')}))
write_json(repair,dict(status='qualified',eligible_endpoint=True,probability_qualification=identity(probability)))
pins={repair:identity(repair)['sha256'],probability:identity(probability)['sha256']}
helper_sha=identity(HERE/'assemble_execution_u.py')['sha256']
def git(args,**kwargs):
    assert kwargs=={'text':True}
    if args==['git','rev-parse','HEAD']:return launch_head+'\n'
    if args==['git','rev-parse','HEAD:analysis']:return m.ANALYSIS_TREE+'\n'
    assert args==['git','status','--porcelain','--untracked-files=all','--','analysis'];return ''
results=[]
for mode in ('passed','failed_assembly'):
    target=scratch/mode/'20252026';calls=[];stream=io.StringIO()
    def assemble(path,output):
        assert path==repair and output==target;calls.append('assemble_once')
        if mode=='failed_assembly':raise InputContractError('synthetic assembler stop')
        target.mkdir();write_json(target/'manifest.json',{'kind':'stubbed-assembly'})
        return SimpleNamespace(path=target/'manifest.json')
    def saved(*args):
        assert args[1:]==(str(old/'manifest.json'),json.loads(probability.read_text()),launch_head)
        calls.append('saved_byte_audit');return {'kind':'stubbed-saved-byte-audit'}
    argv=['assemble_execution_u.py','--repair',str(repair),'--output',str(target),'--expected-launch-head',launch_head,
        '--expected-helper-sha256',helper_sha,'--acceptance',str(acceptance),'--acceptance-sha256',identity(acceptance)['sha256']]
    with patch.object(m,'REPAIR',repair),patch.object(m,'OUTPUT',target),patch.object(m,'PINS',pins), \
         patch.object(m.subprocess,'check_output',git),patch.object(m,'assemble_u_repair',assemble),patch.object(m,'saved_audit',saved), \
         patch.object(sys,'argv',argv),redirect_stdout(stream):
        try:code=m.main()
        except InputContractError:
            assert mode=='failed_assembly';assert (target.parent/'assembly-failure.json').is_file();code=1
        else:assert mode=='passed' and type(code) is int and code==0
    assert calls==(['assemble_once','saved_byte_audit'] if mode=='passed' else ['assemble_once'])
    results.append(dict(mode=mode,exit_code=code,calls=calls))
# current pins are inspected as text/constants only; no real metadata or output roots opened.
assert m.PINS[m.REPAIR]=='28c6d3b9a3f1261191085dd52831e7572103d46f62c2a667fcbbd1ecb53abdf1'
assert m.PINS[m.CAPTURE/'repair-01/qualification/qualification.json']=='2514390196a9e827caaecd67ece0b28cdb069fa5efb7bd339a93970ffd4f9aec'
print(json.dumps(dict(status='passed',scope='shell syntax/static pins plus scratch synthetic saved-byte/json and stubbed main controls; no actual assembly, source, CSR, F/gradient, probability or native call',
    command=identity(command_path),helper=identity(HERE/'assemble_execution_u.py'),ordinary_saved_audit_changed_bytes_and_qrg_comparison_refused=True,
    one_assembly_call_and_no_extra_strict_read=True,main_controls=results,scratch=str(scratch)),indent=2))
