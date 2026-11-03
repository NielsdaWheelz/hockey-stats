"""temporary command/main dry controls: scratch files and stubbed numerical owners."""
from contextlib import redirect_stdout
from copy import deepcopy
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

import numpy as np
from scipy.sparse import csr_matrix

from hockey_stats.artifacts import write_json
from hockey_stats.captures import InputContractError
from hockey_stats.chance_cli import identity

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('u_capture_orchestration',HERE/'capture_execution_u.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
TREE='54e41d821b1cc12fb262be4c42d6898a610c37fe'
CAPTURE='e42f7be944a5350a9096b953559835cddbeb6f9a2081113f01eae32131951d5c'
DIAGNOSIS='2142a218e9759c9103db29e728605efaf7492363efd888cd2c019b956f51ec4d'
assert identity(HERE/'capture_execution_u.py')['sha256']==CAPTURE
assert identity(HERE/'diagnose_execution_u.py')['sha256']==DIAGNOSIS
assert identity(HERE/'consumed_start_check.py')['sha256']==module.OBSERVER_SHA
command_path=HERE/'real-u-capture-command.sh'
command=command_path.read_text()
assert f'capture_tree={TREE}' in command and f'capture_sha={CAPTURE}' in command and f'capture_diagnosis_sha={DIAGNOSIS}' in command
assert 'capture_commit=$(git rev-parse HEAD)' in command and '=PENDING' not in command
assert f'capture_root={module.OUTPUT}' in command
assert 'keep analysis, capture, diagnosis and source-observer code unchanged from launch until exit' in command
line=next(line for line in command.splitlines() if line.startswith('/usr/bin/time'))
words=shlex.split(line)
assert words[:7]==['/usr/bin/time','-l','env','PYTHONPATH=analysis/src','analysis/.venv/bin/python','var/v1-08-replacement/capture_execution_u.py','--expected-commit']
assert words[7:14]==['$capture_commit','--expected-analysis-tree','$capture_tree','--expected-capture-sha256','$capture_sha','--expected-diagnosis-sha256','$capture_diagnosis_sha']
expected_pins={
 'prepared':('/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json','63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c'),
 'coaches':('/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json','102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0'),
 'previous':('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution/20242025/manifest.json','1ba2c8af310d12239d6cabb89ee6cc92b6b98bd95e6834b4f44e303802a44cfe'),
 'donor':('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution-final-02/20252026/manifest.json','cb075d5e59aea61589411e4573db7192c45fddd8265a807c2c39c2084b504e22'),
 'source_report':('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/fit-20252026-final-02-source-check.json','59f4b00827ea736f0a374ba6f32a1ce7003f5f9ab7a131b84d5e4971f0624e9d')}
assert {key:(str(path),sha) for key,(path,sha) in module.PINS.items()}==expected_pins
assert all(path in command for path,sha in expected_pins.values())
# only shell syntax is executed; the real shell/cli is never launched.
subprocess.run(['zsh','-n',str(command_path)],check=True)
scratch=Path(tempfile.mkdtemp(prefix='u-orchestration-',dir=HERE))
report={'source_context_sha256':'f96ee4a0eadeb2f5caa44db999c71b9ad0e6a178b8a3812f9895019dcdb065a3',
        'source_response_sha256':'63e224a6d8ac06729882bd05b1dcd817df49d39000fb8559817e0e1d01feef04'}
pins={}
for name in expected_pins:
    path=scratch/(name+'.json');write_json(path,report if name=='source_report' else {'kind':'synthetic_orchestration'})
    pins[name]=(path,identity(path)['sha256'])
refs={name:identity(path) for name,(path,sha) in pins.items()}
previous=SimpleNamespace(path=pins['previous'][0],manifest=dict(season='20242025',recipe=module.ed.RECIPE,
    prepared=refs['prepared'],coaches=refs['coaches']),heads={name:dict(status='complete',ledger=[]) for name in module.ed.HEADS})
donor=SimpleNamespace(path=pins['donor'][0],manifest=dict(season='20252026',recipe=module.ed.RECIPE,
    previous=refs['previous'],prepared=refs['prepared'],coaches=refs['coaches']),heads={name:dict(status='complete',
    resolution=dict(status='failed' if name=='u' else 'passed',comparison=dict(base_objective=69668.42305740231,
    base_gradient_max=0.002770559377087478))) for name in module.ed.HEADS})
prepared=object();launch_head='a'*40
argv=['capture_execution_u.py','--expected-commit',launch_head,'--expected-analysis-tree',TREE,
      '--expected-capture-sha256',CAPTURE,'--expected-diagnosis-sha256',DIAGNOSIS]
def git(args,**kwargs):
    assert kwargs=={'text':True}
    if args==['git','rev-parse','HEAD']:return launch_head+'\n'
    if args==['git','rev-parse','HEAD:analysis']:return TREE+'\n'
    assert args==['git','status','--porcelain','--untracked-files=all','--','analysis'];return ''
results=[]
for status in ('arithmetic_repair_permitted','inconclusive'):
    output=scratch/status;calls=[]
    def state(path,purpose):
        assert purpose=='real';calls.append('read_'+('previous' if path==previous.path else 'donor'))
        assert path in (previous.path,donor.path);return previous if path==previous.path else donor
    def read(path,purpose):
        assert path==pins['prepared'][0] and purpose=='real';calls.append('read_prepared');return prepared
    def capture(checked,coaches,prior,saved,expected,destination,bindings):
        assert checked is prepared and coaches==pins['coaches'][0] and prior is previous and saved is donor
        assert expected==report and destination==output and bindings==refs
        calls.append('capture_stub')
        path=output/'inputs';path.mkdir();write_json(path/'manifest.json',dict(payload_bytes=0,batches=[{}]))
        return path/'manifest.json'
    def load(path):
        assert path==output/'inputs/manifest.json';calls.append('load_stub')
        return dict(metadata=dict(bindings=refs,incoming_ledger=[]),design=dict(target=np.zeros(1),fixed_matrix=csr_matrix((1,2))))
    def diagnose(path,destination):
        assert path==output/'inputs/manifest.json' and destination==output/'diagnosis'
        assert (output/'capture-reloaded.json').is_file();calls.append('diagnose_stub');return {'status':status}
    stream=io.StringIO()
    with patch.object(module,'OUTPUT',output),patch.object(module,'PINS',pins),patch.object(module.subprocess,'check_output',git), \
         patch.object(module,'read_execution_state',state),patch.object(module,'read_prepared',read), \
         patch.object(module,'capture',capture),patch.object(module,'load_u_bundle',load), \
         patch.dict(sys.modules,{'diagnose_execution_u':SimpleNamespace(diagnose=diagnose)}),patch.object(sys,'argv',argv),redirect_stdout(stream):
        code=module.main()
    assert type(code) is int and code==(0 if status=='arithmetic_repair_permitted' else 1)
    assert calls==['read_previous','read_donor','read_prepared','capture_stub','load_stub','diagnose_stub']
    lines=stream.getvalue().splitlines()
    assert lines[0]==f"u input bundle reloaded: {output/'inputs/manifest.json'}"
    assert json.loads(lines[1])==dict(status=status,bundle=str(output/'inputs/manifest.json'),diagnosis=str(output/'diagnosis'))
    assert json.loads((output/'capture-start.json').read_text())['actual_launch_head']==launch_head
    assert json.loads((output/'capture-reloaded.json').read_text())['objective_evaluations']==0
    results.append(dict(status=status,exit_code=code,owner_calls=calls))
# a mismatched scalar input pin stops before any prepared/state/source owner.
badpins=dict(pins);badpins['prepared']=(pins['prepared'][0],'0'*64)
with patch.object(module,'OUTPUT',scratch/'badpin'),patch.object(module,'PINS',badpins),patch.object(module.subprocess,'check_output',git), \
     patch.object(module,'read_execution_state',side_effect=AssertionError('state read before pin refusal')), \
     patch.object(module,'read_prepared',side_effect=AssertionError('prepared read before pin refusal')),patch.object(sys,'argv',argv):
    try:module.main()
    except InputContractError as error:assert str(error)=='capture input identity differs: prepared'
    else:raise AssertionError('wrong input pin accepted')
assert not (scratch/'badpin').exists()
print(json.dumps(dict(status='passed',scope='syntax/static shell inspection and main orchestration with scratch-only files, stubbed capture/load/diagnose; no real input read, shell launch, source pass or objective',
    command=identity(command_path),reviewed_analysis_tree=TREE,capture_sha256=CAPTURE,diagnosis_sha256=DIAGNOSIS,
    exact_real_input_path_and_digest_constants=True,syntax_checked_without_execution=True,main_status_controls=results,
    input_pin_refused_before_source_owners=True,scratch=str(scratch)),indent=2))
