"""temporary canonical-output/resume-record binding controls; scratch metadata only."""
import ast
from contextlib import redirect_stdout
from hashlib import sha256
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

here=Path(__file__).resolve().parent;work=here.parents[1]
command=here/'real-20212022-spatial-command.sh';helper=here/'accept_real_spatial_20212022.py'
original_command=subprocess.check_output(['git','show','73e3789ee3ebb0dd32da85b322e81672d89c33c5:var/v1-08-replacement/real-20212022-spatial-command.sh'],cwd=work,text=True)
original_helper=subprocess.check_output(['git','show','73e3789ee3ebb0dd32da85b322e81672d89c33c5:var/v1-08-replacement/accept_real_spatial_20212022.py'],cwd=work,text=True)
assert sha256(original_command.encode()).hexdigest()=='fa97af900ff99ae01b747d3f344112645d71194980066bafd36dfd57251628fa'
assert sha256(original_helper.encode()).hexdigest()=='0d0cc40c44754347d5e6f93cfa05fa4f3d4e0015cf309edbbd55e799a80d9eab'
current=command.read_text()
a=next(line for line in original_command.splitlines() if line.startswith('/usr/bin/time'))
b=next(line for line in current.splitlines() if line.startswith('/usr/bin/time'))
assert a.split(' > ')[0]==b.split(' > ')[0]
assert [line for line in original_command.splitlines() if line.startswith('spatial_pin ')]==[line for line in current.splitlines() if line.startswith('spatial_pin ')]
def inspect_ast(source):return ast.dump(next(node for node in ast.parse(source).body if isinstance(node,ast.FunctionDef) and node.name=='inspect_first_year'),include_attributes=False)
assert inspect_ast(original_helper)==inspect_ast(helper.read_text())
spec=importlib.util.spec_from_file_location('resume_spatial_readback',helper);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
assert str(h.OUTPUT).endswith('/real/spatial/20212022') and str(h.RUN_STEM).endswith('/real/spatial/20212022-resume-01')
assert h.METADATA_RECEIPT==Path(str(h.RUN_STEM)+'-saved-metadata-acceptance.json')
assert h.SOLVER==dict(maxiter=10000,ftol=1e-15,gtol=1e-6,maxcor=10)
scratch=Path(tempfile.mkdtemp(prefix='spatial-resume-bindings-',dir=here));results=[]
for native_exit in (0,3):
    root=scratch/str(native_exit);root.mkdir()
    output=root/'20212022';run=Path(str(output)+'-resume-01');receipt=Path(str(run)+'-saved-metadata-acceptance.json')
    records={'-exit.txt':str(native_exit)+'\n','-start.txt':'resume start\n','-finish.txt':'resume finish\n',
        '-launch-analysis-tree.txt':h.ANALYSIS+'\n','-launch-analysis-status.txt':'','-launch-head.txt':'a'*40+'\n',
        '.log':'1.00 real 2.00 user 3.00 sys\n100 maximum resident set size\n90 peak memory footprint\n'}
    old={}
    for suffix,data in records.items():
        Path(str(run)+suffix).write_text(data)
        path=Path(str(output)+suffix);path.write_text('130\n' if suffix=='-exit.txt' else 'original interrupted evidence\n')
        old[path]=sha256(path.read_bytes()).hexdigest()
    calls=[]
    def inspect(path,**kwargs):
        assert path==output and kwargs==dict(purpose='real',prepared_sha256='63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c',
            coaches_sha256='102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0',valued_sha256='37263bfc650a06f09adc2c64588c19d3b61cd1e9cdb65dc2ba71a8f88ed5ca8d')
        calls.append(str(path));return dict(status='metadata_passed_pending_root_acceptance' if native_exit==0 else 'incomplete_annual',eligible_as_predecessor=native_exit==0)
    with patch.object(h,'OUTPUT',output),patch.object(h,'RUN_STEM',run),patch.object(h,'METADATA_RECEIPT',receipt),patch.object(h,'inspect_first_year',inspect),redirect_stdout(io.StringIO()):
        code=h.main()
        assert code==(0 if native_exit==0 else 1)
        saved=json.loads(receipt.read_text());assert saved['launch']['exit']==native_exit and saved['launch']['run_stem']==str(run)
        assert saved['launch']['start']=='resume start' and saved['launch']['finish']=='resume finish'
        assert saved['whole_command']['timing']==dict(wall_seconds=1.,user_seconds=2.,system_seconds=3.)
        before=receipt.read_bytes()
        try:h.main()
        except FileExistsError:pass
        else:raise AssertionError('metadata receipt overwritten')
        assert receipt.read_bytes()==before
    assert calls==[str(output),str(output)] and all(sha256(path.read_bytes()).hexdigest()==digest for path,digest in old.items())
    assert not output.exists()
    results.append(dict(native_exit=native_exit,readback_exit=code,canonical_output=str(output),run_stem=str(run),original_records_unchanged=len(old)))
print(json.dumps(dict(status='passed',scope='source AST/argv plus scratch run records and STUB inspect only; no actual source, fit, state, array, strict-reader or numerical calls',
    original_cli_argv_and_input_pins_exact=True,raw_inspect_ast_unchanged=True,solver_unchanged=True,fresh_receipt_refusal=True,
    command_sha256=sha256(command.read_bytes()).hexdigest(),helper_sha256=sha256(helper.read_bytes()).hexdigest(),controls=results,scratch=str(scratch)),indent=2))
