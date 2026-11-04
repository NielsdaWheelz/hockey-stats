"""temporary scratch-only first-spatial shell controls; executable is a shell stub."""
from hashlib import sha256
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

here=Path(__file__).parent.resolve();command=here/'real-20212022-spatial-command.sh';source=command.read_text()
subprocess.run(['/bin/zsh','-n',str(command)],check=True)
scratch=Path(tempfile.mkdtemp(prefix='spatial-first-shell-',dir=here));outcomes=[]
for mode in ('pass','native_exit3','occupied_output','occupied_log','occupied_exit','occupied_metadata','dirty_analysis','changed_input','changed_acceptance'):
    root=scratch/mode;work=root/'work';work.mkdir(parents=True)
    locations={'spatial_prepared':root/'prepared','spatial_coaches':root/'coaches/coaches.json','spatial_campaign':root/'campaign'}
    locations['spatial_valued']=locations['spatial_campaign']/'real/scores/20212022'
    script=source.replace('/Users/nnandal/Documents/code/hockey-stats-v1-08',str(work))
    original={'spatial_prepared':'/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02',
        'spatial_coaches':'/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json',
        'spatial_campaign':'/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01'}
    for name,path in original.items():script=script.replace(path,str(locations[name]))
    members={}
    for line in source.splitlines():
        if not line.startswith('spatial_pin '):continue
        _,name,digest=shlex.split(line)
        if name.startswith('$'):
            variable=name[1:].split('/')[0];tail=name[len(variable)+1:].lstrip('/')
            path=locations[variable]/tail if tail else locations[variable]
        else:path=work/name
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text('scratch pinned metadata: '+name+'\n')
        script=script.replace(digest,sha256(path.read_bytes()).hexdigest());members[name]=path
    assert '/Volumes/' not in script
    stub=work/'analysis/.venv/bin/python';stub.parent.mkdir(parents=True)
    stub.write_text('#!/bin/sh\nprintf stub > "$U_SPATIAL_SHELL_MARKER"\nprintf "%s\\n" "$@" > "$U_SPATIAL_SHELL_ARGV"\nexit "$U_SPATIAL_SHELL_EXIT"\n');stub.chmod(0o755)
    (work/'analysis/fixture.txt').write_text('fixture analysis\n')
    def git(*args):return subprocess.check_output(['git',*args],cwd=work,text=True).strip()
    git('init','-q');git('config','user.email','fixture@example.invalid');git('config','user.name','fixture')
    git('add','analysis');git('commit','-q','-m','fixture analysis');tree=git('rev-parse','HEAD:analysis')
    script=script.replace('fc716257eb118d1a091472cde4b214e8bca1f753',tree)
    (work/'docs.txt').write_text('docs advance\n');git('add','docs.txt');git('commit','-q','-m','fixture docs')
    head=git('rev-parse','HEAD');output=locations['spatial_campaign']/'real/spatial/20212022'
    output.parent.mkdir(parents=True)
    run=Path(str(output)+'-resume-01')
    old_records={}
    for suffix in ('.log','-start.txt','-finish.txt','-exit.txt','-shell.pid','-launch-head.txt','-launch-analysis-tree.txt','-launch-analysis-status.txt','-launch-command-sha256.txt','-launch-inputs-sha256.txt','-launch-acceptance-sha256.txt','-launch-spatial-recipe.txt'):
        path=Path(str(output)+suffix);path.write_text('130\n' if suffix=='-exit.txt' else 'preserved interrupted evidence '+suffix+'\n')
        old_records[path]=sha256(path.read_bytes()).hexdigest()
    if mode=='occupied_output':output.mkdir()
    if mode=='occupied_log':Path(str(run)+'.log').write_text('occupied\n')
    if mode=='occupied_exit':Path(str(run)+'-exit.txt').write_text('occupied\n')
    if mode=='occupied_metadata':Path(str(run)+'-saved-metadata-acceptance.json').write_text('occupied\n')
    if mode=='dirty_analysis':(work/'analysis/new.py').write_text('unreviewed\n')
    if mode=='changed_input':members['$spatial_valued/manifest.json'].write_text('changed\n')
    if mode=='changed_acceptance':members['docs/research/spatial-v1-08/receipts/replacement-real-score-20212022-completion.json'].write_text('changed\n')
    shell=work/'command.sh';shell.write_text(script);marker=root/'stub-invoked';argv=root/'argv.txt'
    env=dict(os.environ,U_SPATIAL_SHELL_MARKER=str(marker),U_SPATIAL_SHELL_ARGV=str(argv),U_SPATIAL_SHELL_EXIT='3' if mode=='native_exit3' else '0')
    actual=subprocess.run(['/bin/zsh',str(shell)],cwd=root,env=env,capture_output=True,text=True)
    if mode in ('pass','native_exit3'):
        expected=3 if mode=='native_exit3' else 0
        assert actual.returncode==expected,(mode,actual.stderr)
        assert marker.is_file() and Path(str(run)+'-finish.txt').is_file()
        assert Path(str(run)+'-exit.txt').read_text().strip()==str(expected)
        assert Path(str(run)+'-launch-head.txt').read_text().strip()==head
        assert Path(str(run)+'-launch-analysis-tree.txt').read_text().strip()==tree
        assert Path(str(run)+'-launch-analysis-status.txt').read_text()==''
        args=argv.read_text().splitlines()
        assert args==['-m','hockey_stats.analysis_cli','fit','--family','spatial','--prepared',str(locations['spatial_prepared']),
            '--coaches',str(locations['spatial_coaches']),'--valued',str(locations['spatial_valued']),'--season','20212022','--out',str(output)]
    else:
        assert actual.returncode!=0 and not marker.exists(),(mode,actual.stderr)
        assert not Path(str(run)+'-start.txt').exists()
    assert all(sha256(path.read_bytes()).hexdigest()==digest for path,digest in old_records.items())
    outcomes.append(dict(mode=mode,exit=actual.returncode,model_stub_invoked=marker.exists(),original_interrupted_records_unchanged=len(old_records)))
print(json.dumps(dict(status='passed',scope='all real paths/pins replaced by scratch metadata and tiny git; python is a shell stub; no real cli/source/game/array/model/strict-reader calls',
    command_sha256=sha256(command.read_bytes()).hexdigest(),syntax_checked=True,restart_records_only=True,canonical_output_unchanged=True,controls=outcomes,scratch=str(scratch)),indent=2))
