"""temporary composition binding/parser/source-preservation controls; no main data read."""
import ast
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[1];product=WORK/'var/v1-08-product/replacement'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
h=load('composition_binding',product/'verify-real-execution-compose.py')
s=load('selection_binding',product/'prepare-real-score-selection.py')
assert h.SCORES==s.EXPECTED and h.STATES==s.STATES and h.FINAL_STATE==s.FINAL_STATE
assert h.SCORES['20252026']=='40e23b35ac9c8458229b076150366960c4a25d7a92ae028d2b45dc39c89104fc'
assert h.STATES['20252026']=='59e3432df70366c4e058007f4396be7737f76afada4fad96c84896dd12a6f276'
original=subprocess.check_output(['git','show','58ca52df2d9409d1e788b07a916f8b51b9826187:var/v1-08-product/replacement/verify-real-execution-compose.py'],cwd=WORK,text=True)
def functions(source):return {node.name:ast.dump(node,include_attributes=False) for node in ast.parse(source).body if isinstance(node,ast.FunctionDef)}
a,b=functions(original),functions((product/'verify-real-execution-compose.py').read_text())
preserved=[name for name in a if name!='main'];assert all(a[name]==b[name] for name in preserved)
scratch=Path(tempfile.mkdtemp(prefix='execution-compose-cutover-',dir=HERE))
argv=['verify-real-execution-compose.py','--expected-manifest-sha256','a'*64,'--expected-selection-sha256','pending','--out-check',str(scratch/'unused.json')]
with patch.object(sys,'argv',argv),patch.object(h,'sha',side_effect=AssertionError('metadata read before parser refusal')):
    try:h.main()
    except AssertionError as error:assert str(error)!='metadata read before parser refusal'
    else:raise AssertionError('pending selection passed parser')
class ReachedStubHash(Exception):pass
calls=[]
def first_hash(path):
    assert path==h.OUTPUT/'manifest.json';calls.append(str(path));raise ReachedStubHash
argv[4]='b'*64
with patch.object(sys,'argv',argv),patch.object(h,'sha',first_hash):
    try:h.main()
    except ReachedStubHash:pass
    else:raise AssertionError('valid parser did not reach expected saved output hash owner')
assert len(calls)==1
path=product/'real-compose-execution-command.sh';command=path.read_text()
subprocess.run(['zsh','-n',str(path)],check=True)
assert "expected_selection_sha256=''" in command
assert 'accepted_score_receipt_sha256=8f9163b53c07c264ef59d651bf4860b04333b70a61ec4a19abc7bd4fecfa1953' in command
assert command.index('[ "${#expected_final_score_sha256}"')<command.index('cd /Users')<command.index('set -C')
new=shlex.split(next(line for line in command.splitlines() if line.startswith('/usr/bin/time')))
old_command=subprocess.check_output(['git','show','58ca52df2d9409d1e788b07a916f8b51b9826187:var/v1-08-product/replacement/real-compose-execution-command.sh'],cwd=WORK,text=True)
old=shlex.split(next(line for line in old_command.splitlines() if line.startswith('/usr/bin/time')))
expanded=[word.replace('$compose_root',str(h.CAMPAIGN)).replace('$compose_output',str(h.OUTPUT)) for word in new]
assert expanded[expanded.index('summarize'):]==old[old.index('summarize'):]
assert 'fit' not in new and 'score' not in new and 'publish' not in new
print(json.dumps(dict(status='passed',scope='source AST/static pins, syntax and STUB hash/parser only; no actual selection/composition/score/source/strict reader/arrays/publication',
    preserved_streaming_and_accounting_functions=preserved,selector_and_checker_same_five_bindings=True,
    pending_selection_refused_before_reads=True,valid_parser_stub_hash_calls=len(calls),composition_held_before_io=True,
    producer_summarize_arguments_unchanged=True,scratch=str(scratch)),indent=2))
