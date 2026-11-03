"""temporary final-score pin/source-parity/parser controls; no score or data pass."""
import ast
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[1]
helper_path=HERE/'accept_real_score_20252026.py'
spec=importlib.util.spec_from_file_location('final_score_cutover',helper_path)
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
TREE='fc716257eb118d1a091472cde4b214e8bca1f753'
STATE='/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/assembled-01/20252026/manifest.json'
STATE_SHA='59e3432df70366c4e058007f4396be7737f76afada4fad96c84896dd12a6f276'
assert h.ANALYSIS==TREE and h.OBSERVER=='ef4995e579855950cab475cc2ac237f6ce22538429cc1f04d675b48838a6fca4'
assert str(h.STATE)==STATE and h.STATE_SHA==STATE_SHA
assert str(h.OLD).endswith('/current-04/scores/20252026')
assert h.FIT_SOURCE.name=='fit-20252026-final-02-source-check.json'
assert h.FIT_SOURCE_SHA=='59f4b00827ea736f0a374ba6f32a1ce7003f5f9ab7a131b84d5e4971f0624e9d'
scratch=Path(tempfile.mkdtemp(prefix='final-score-cutover-',dir=HERE))
original=subprocess.check_output(['git','show','2519567e9f65b1e6b8f1f7e2c49a19c94763411c:var/v1-08-replacement/accept_real_score_20252026.py'],cwd=WORK,text=True)
def functions(source):return {node.name:ast.dump(node,include_attributes=False) for node in ast.parse(source).body if isinstance(node,ast.FunctionDef)}
before,after=functions(original),functions(helper_path.read_text())
preserved=[name for name in before if name!='main']
assert all(before[name]==after[name] for name in preserved)
# accepted small source report only; no game, source pass, score or numerical arrays.
fit=h.read(h.FIT_SOURCE)
source=deepcopy(fit);source['observer_seconds']+=1.;source['command']=['score','synthetic-control']
parity=h.check_source_parity(fit,source)
assert all(parity.values()) and set(parity)==set(fit)-{'command','observer_seconds'}
refused=[]
for mode in ('first_witness','extra_field','fingerprint','known_census'):
    changed=deepcopy(source)
    if mode=='first_witness':changed['first_witnesses'][0]['key']='synthetic-wrong:1'
    elif mode=='extra_field':changed['unexpected']='synthetic'
    elif mode=='fingerprint':changed['source_context_sha256']='0'*64
    else:changed['known_expected']=54
    try:h.check_source_parity(fit,changed)
    except AssertionError:refused.append(mode)
    else:raise AssertionError('changed source report accepted: '+mode)
# malformed identity must stop before any saved-score or source/report read.
argv=['accept_real_score_20252026.py','--expected-manifest-sha256','a'*64,'--expected-state-sha256','0'*64,
      '--expected-source-sha256','b'*64,'--expected-fit-source-sha256',h.FIT_SOURCE_SHA,'--out-check',str(scratch/'unused.json')]
with patch.object(sys,'argv',argv),patch.object(Path,'read_text',side_effect=AssertionError('read before fixed state pin refusal')), \
     patch.object(h,'read_execution_scores',side_effect=AssertionError('strict reader called before fixed state pin refusal')):
    try:h.main()
    except AssertionError as error:assert not str(error).startswith(('read before','strict reader'))
    else:raise AssertionError('wrong annual pin accepted')
# valid parser/preflight reaches exactly one STUB strict reader; it never reads scores.
new=scratch/'score';new.mkdir();(new/'manifest.json').write_text('{"kind":"synthetic-stub"}\n')
(scratch/'score-20252026.exit').write_text('0\n')
(scratch/'score-20252026-launch-checker-sha256.txt').write_text(h.sha(helper_path)+'  '+str(helper_path)+'\n')
manifest_sha=h.sha(new/'manifest.json');argv[2]=manifest_sha;argv[4]=STATE_SHA
class ReachedStubReader(Exception):pass
calls=[]
def stub(path,purpose):
    assert path==new and purpose=='real';calls.append((str(path),purpose));raise ReachedStubReader
with patch.object(sys,'argv',argv),patch.object(h,'CAMPAIGN',scratch),patch.object(h,'NEW',new),patch.object(h,'read_execution_scores',stub):
    try:h.main()
    except ReachedStubReader:pass
    else:raise AssertionError('preflight failed to reach saved-score owner')
assert len(calls)==1
command_path=HERE/'real-20252026-score-command.sh';command=command_path.read_text()
subprocess.run(['zsh','-n',str(command_path)],check=True)
assert '=PENDING' not in command and f'score_state_sha={STATE_SHA}' in command
assert 'score_state=$score_root/u-repair-01/assembled-01/20252026' in command and f'score_tree={TREE}' in command
line=shlex.split(next(line for line in command.splitlines() if line.startswith('/usr/bin/time')))
assert line[5:]==['var/v1-08-replacement/consumed_start_check.py','--out-check','$score_root/score-20252026-source-check.json','--',
    'score','--family','execution','--prepared','/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02',
    '--coaches','/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json',
    '--state','$score_state','--out','$score_output','>','$score_root/score-20252026.log','2>&1']
assert '--known-census' not in line and '--previous' not in line and 'fit' not in line
assert 'score_status=$?' in command and 'exit "$score_status"' in command
print(json.dumps(dict(status='passed',scope='accepted small source metadata, pure comparisons and parser/STUB-reader preflight, shell syntax/static command; no real game/source pass, score, strict reader, projection or arrays',
    analysis_tree=TREE,state_path=STATE,state_sha256=STATE_SHA,preserved_functions=preserved,source_parity_fields=list(parity),
    source_refusals=refused,wrong_annual_refused_before_reads=True,strict_reader_stub_calls=len(calls),
    helper=h.identity(helper_path),command=h.identity(command_path),scratch=str(scratch)),indent=2))
