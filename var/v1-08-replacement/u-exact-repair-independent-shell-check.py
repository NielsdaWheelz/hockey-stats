"""independent scratch substitution of the single real repair launch shell."""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile

work=Path.cwd();source=work/'var/v1-08-replacement/real-u-repair-command.sh';script=source.read_text()
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash=='8fe1dfae57333aa74ee0032a1b1f75be2dc15ba297d35bd22ff84c0252d9e752'
for shell in ['zsh','sh']:subprocess.run([shell,'-n',str(source)],check=True)
values={}
for line in script.splitlines():
    match=re.fullmatch(r'(repair_\w+)=(.*)',line)
    if match and not match[2].startswith(('$(', '${')):values[match[1]]=match[2]
def expand(s):
    for _ in range(3):s=re.sub(r'\$(repair_\w+)',lambda m:values[m[1]],s)
    return s
pins={}
for line in script.splitlines():
    if line.startswith('repair_pin '):
        _,path,digest=shlex.split(line);path=expand(path);digest=expand(digest)
        actual=Path(path) if Path(path).is_absolute() else work/path
        assert hashlib.sha256(actual.read_bytes()).hexdigest()==digest,(path,digest)
        pins[path]=digest
assert len(pins)==17
scratch=Path(tempfile.mkdtemp(prefix='u-exact-repair-shell-',dir=work/'var/v1-08-replacement'));binpath=scratch/'bin';binpath.mkdir();capture=scratch/'capture';capture.mkdir()
oldcapture=values['repair_capture']
substituted_pins={p.replace(oldcapture,str(capture)):d for p,d in pins.items()}
mapfile=scratch/'pins.json';mapfile.write_text(json.dumps(substituted_pins))
def executable(name,text):
    path=binpath/name;path.write_text(text);path.chmod(0o755);return path
executable('git','''#!/bin/sh
case "$*" in
'rev-parse HEAD') echo aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ;;
'rev-parse HEAD:analysis') echo fc716257eb118d1a091472cde4b214e8bca1f753 ;;
'status --porcelain --untracked-files=all -- analysis') if [ "$U_DIRTY" = 1 ]; then echo ' M analysis/example'; fi ;;
*) exit 81 ;;
esac
''')
executable('shasum','''#!/usr/bin/env python3
import hashlib,json,os,sys
from pathlib import Path
pins=json.loads(Path(os.environ['U_PINS']).read_text())
for name in sys.argv[2:]:
 if name in pins:digest=pins[name]
 else:
  p=Path(name);assert p.is_relative_to(Path(os.environ['U_SCRATCH']));digest=hashlib.sha256(p.read_bytes()).hexdigest()
 if os.environ.get('U_BAD_PIN')=='1' and name=='var/v1-08-replacement/repair_execution_u.py':digest='0'*64
 print(digest+'  '+name)
''')
runner=executable('fake-repair','''#!/bin/sh
printf 'scratch-only standin arguments: %s\\n' "$*"
printf invoked > "$U_INVOKED"
exit "$U_EXIT"
''')
original='/usr/bin/time -l env PYTHONPATH=analysis/src analysis/.venv/bin/python var/v1-08-replacement/repair_execution_u.py'
assert script.count(original)==1
base=script.replace('repair_capture='+oldcapture,'repair_capture='+str(capture)).replace(original,'/usr/bin/time -l '+str(runner))
# zsh startup prepends homebrew; establish standin resolution after startup.
base=base.replace('set -eu\n', 'set -eu\nPATH='+shlex.quote(str(binpath)+':'+os.environ['PATH'])+'\nexport PATH\n',1)
assert 'assemble_u_repair' not in script
results=[]
for mode,code in [('success',0),('stop',1),('other_failure',7),('badpin',0),('dirty',0)]:
    root=capture/mode;test=scratch/(mode+'.sh');test.write_text(base.replace('repair_root=$repair_capture/repair-01','repair_root='+str(root)))
    marker=scratch/(mode+'.invoked')
    env=dict(os.environ,PATH=str(binpath)+':'+os.environ['PATH'],U_PINS=str(mapfile),U_SCRATCH=str(scratch),U_EXIT=str(code),U_INVOKED=str(marker),U_BAD_PIN='1' if mode=='badpin' else '0',U_DIRTY='1' if mode=='dirty' else '0')
    r=subprocess.run(['zsh',str(test)],env=env,capture_output=True,text=True)
    if mode in ('badpin','dirty'):
        assert r.returncode==1 and not marker.exists() and not list(capture.glob(mode+'*'))
        if mode=='badpin':assert 'pin mismatch:' in r.stderr
    else:
        assert r.returncode==code and marker.is_file() and Path(str(root)+'-exit.txt').read_text()==str(code)+'\n'
        suffixes=['.log','-start.txt','-finish.txt','-exit.txt','-shell.pid','-launch-head.txt','-launch-analysis-tree.txt','-launch-helper-sha256.txt','-launch-trace-sha256.txt','-launch-diagnostic-helper-sha256.txt','-launch-command-sha256.txt','-launch-analysis-status.txt','-launch-inputs-sha256.txt','-launch-acceptance-sha256.txt']
        assert all(Path(str(root)+suffix).is_file() for suffix in suffixes)
        assert Path(str(root)+'-launch-head.txt').read_text().strip()=='a'*40
        oldlog=Path(str(root)+'.log').read_bytes();again=subprocess.run(['zsh',str(test)],env=env,capture_output=True,text=True)
        assert again.returncode==1 and 'occupied path:' in again.stderr and Path(str(root)+'.log').read_bytes()==oldlog
    results.append(dict(mode=mode,expected_status=1 if mode in ('badpin','dirty') else code,actual_status=r.returncode,standin_called=marker.exists()))
print(json.dumps(dict(status='passed',source_command_sha256=source_hash,scope='actual pins read as bytes; scratch-substituted shell, git/hash/repair standins only; no real repair, evaluator, native solve, source reconstruction or campaign write',pins_checked=len(pins),actual_exit_and_receipt_statuses_preserved=True,all_receipts_present=True,occupied_paths_preserve_logs=True,pin_and_dirty_analysis_refused_before_receipts_and_standin=True,results=results,scratch=str(scratch)),indent=2))
