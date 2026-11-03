"""temporary scratch-only shell-flow checks; model executable is a shell stub."""
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile

here=Path(__file__).parent.resolve()
command=here/'real-u-repair-command.sh'
source=command.read_text()
subprocess.run(['/bin/zsh','-n',str(command)],check=True)
scratch=Path(tempfile.mkdtemp(prefix='u-repair-shell-',dir=here))
old_work='/Users/nnandal/Documents/code/hockey-stats-v1-08'
old_capture='/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01'
outcomes=[]
for mode in ('pass','native_exit3','occupied_output','occupied_log','occupied_exit','dirty_analysis','changed_helper','changed_input','changed_acceptance'):
    root=scratch/mode;work=root/'work';work.mkdir(parents=True)
    capture=root/'capture';capture.mkdir()
    script=source.replace(old_work,str(work)).replace(old_capture,str(capture))
    members={}
    for line in source.splitlines():
        if not line.startswith('repair_pin '):continue
        _,name,expected=shlex.split(line)
        if name.startswith('$repair_capture/'):
            path=capture/name.removeprefix('$repair_capture/')
        elif name.startswith('/'):
            path=root/'external'/sha256(name.encode()).hexdigest()[:12]
            script=script.replace(name,str(path))
        else:path=work/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('scratch-only pinned member: '+name+'\n')
        digest=sha256(path.read_bytes()).hexdigest()
        members[name]=path
        if expected.startswith('$'):
            variable=expected[1:]
            script=re.sub(r'^'+variable+r'=\w+$',variable+'='+digest,script,flags=re.MULTILINE)
        else:script=script.replace(expected,digest)
    assert '/Volumes/' not in script and old_work not in script.replace(str(scratch),'<scratch>')
    stub=work/'analysis/.venv/bin/python';stub.parent.mkdir(parents=True)
    stub.write_text('#!/bin/sh\nprintf stub > "$U_REPAIR_SHELL_MARKER"\nexit "$U_REPAIR_SHELL_EXIT"\n')
    stub.chmod(0o755)
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=work,text=True).strip()
    git('init','-q');git('config','user.email','fixture@example.invalid');git('config','user.name','fixture')
    git('add','analysis');git('commit','-q','-m','fixture analysis')
    tree=git('rev-parse','HEAD:analysis')
    script=script.replace('fc716257eb118d1a091472cde4b214e8bca1f753',tree)
    # advancing only docs must retain the fixed analysis while recording actual head.
    (work/'docs-only.txt').write_text('docs-only advance\n')
    git('add','docs-only.txt');git('commit','-q','-m','fixture docs advance')
    head=git('rev-parse','HEAD')
    if mode=='occupied_output':(capture/'repair-01').mkdir()
    if mode=='occupied_log':(capture/'repair-01.log').write_text('occupied\n')
    if mode=='occupied_exit':(capture/'repair-01-exit.txt').write_text('occupied\n')
    if mode=='dirty_analysis':(work/'analysis/unreviewed.py').write_text('unreviewed\n')
    if mode=='changed_helper':members['var/v1-08-replacement/repair_execution_u.py'].write_text('changed\n')
    if mode=='changed_input':members['$repair_capture/inputs/manifest.json'].write_text('changed\n')
    if mode=='changed_acceptance':members['docs/research/spatial-v1-08/reviews/u-diagnosis-saved-review.md'].write_text('changed\n')
    shell=work/'command.sh';shell.write_text(script)
    marker=root/'model-stub-invoked'
    env=dict(os.environ,U_REPAIR_SHELL_MARKER=str(marker),U_REPAIR_SHELL_EXIT='3' if mode=='native_exit3' else '0')
    actual=subprocess.run(['/bin/zsh',str(shell)],cwd=root,env=env,capture_output=True,text=True)
    if mode in ('pass','native_exit3'):
        expected=3 if mode=='native_exit3' else 0
        assert actual.returncode==expected,(mode,actual.stderr)
        assert marker.read_text()=='stub'
        assert (capture/'repair-01-exit.txt').read_text().strip()==str(expected)
        assert (capture/'repair-01-finish.txt').is_file()
        assert (capture/'repair-01-launch-head.txt').read_text().strip()==head
        assert (capture/'repair-01-launch-analysis-tree.txt').read_text().strip()==tree
        assert (capture/'repair-01-launch-analysis-status.txt').read_text()==''
    else:
        assert actual.returncode!=0,(mode,actual.stderr)
        assert not marker.exists(),mode
        assert not (capture/'repair-01-start.txt').exists(),mode
    outcomes.append(dict(mode=mode,exit_code=actual.returncode,model_stub_invoked=marker.exists()))
print(json.dumps(dict(status='passed',scope='scratch-only substituted paths/pins/git and model shell stub; no real cli, model, source or array pass',
    command_sha256=sha256(command.read_bytes()).hexdigest(),syntax_checked=True,controls=outcomes,scratch=str(scratch)),indent=2))
