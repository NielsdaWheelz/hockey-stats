"""temporary scratch-only year-three wrapper controls; native process is a shell stub."""
from hashlib import sha256
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

here=Path(__file__).resolve().parent;command=here/'real-20232024-spatial-command.sh.held';source=command.read_text()
subprocess.run(['/bin/zsh','-n',str(command)],check=True)
assert len(shlex.split(source.split('for spatial_path in ',1)[1].split('; do',1)[0]))==14
assert source.index('WITHHELD_ACCEPTED_SPATIAL_20222023_MANIFEST_SHA256')<source.index('cd /Users')
scratch=Path(tempfile.mkdtemp(prefix='spatial-third-shell-',dir=here));results=[]
for mode in ('pending_predecessor','pass','native_exit3','wrong_previous','occupied_output','occupied_log','dirty_analysis'):
    root=scratch/mode;work=root/'work';work.mkdir(parents=True)
    campaign=root/'campaign'
    locations=dict(spatial_prepared=root/'prepared',spatial_coaches=root/'coaches/coaches.json',spatial_campaign=campaign,
                   spatial_valued=campaign/'real/scores/20232024',spatial_previous=campaign/'real/spatial/20222023')
    script=source.replace('/Users/nnandal/Documents/code/hockey-stats-v1-08',str(work))
    for literal,path in (('/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02',locations['spatial_prepared']),
        ('/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json',locations['spatial_coaches']),
        ('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01',campaign)):
        script=script.replace(literal,str(path))
    assert '/Volumes/' not in script
    if mode=='pending_predecessor':
        shell=work/'command.sh';shell.write_text(script)
        done=subprocess.run(['/bin/zsh',str(shell)],cwd=root,capture_output=True,text=True)
        assert done.returncode==1 and 'pin withheld' in done.stderr and not campaign.exists()
        results.append(dict(mode=mode,exit=done.returncode,native_stub_invoked=False));continue
    members={}
    for line in source.splitlines():
        if not line.startswith('spatial_pin '):continue
        _,name,digest=shlex.split(line)
        if name.startswith('$'):
            variable=name[1:].split('/')[0];tail=name[len(variable)+1:].lstrip('/')
            path=locations[variable]/tail if tail else locations[variable]
        else:path=work/name
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text('tiny source binding '+name+'\n')
        if not digest.startswith('$'):script=script.replace(digest,sha256(path.read_bytes()).hexdigest())
        members[name]=path
    expected_previous=sha256(members['$spatial_previous/manifest.json'].read_bytes()).hexdigest()
    script=script.replace('WITHHELD_ACCEPTED_SPATIAL_20222023_MANIFEST_SHA256',expected_previous)
    stub=work/'analysis/.venv/bin/python';stub.parent.mkdir(parents=True)
    stub.write_text('#!/bin/sh\nprintf stub > "$SPATIAL_THIRD_MARKER"\nprintf "%s\\n" "$@" > "$SPATIAL_THIRD_ARGV"\nexit "$SPATIAL_THIRD_EXIT"\n');stub.chmod(0o755)
    (work/'analysis/fixed.txt').write_text('fixed source\n')
    def git(*args):return subprocess.check_output(['git',*args],cwd=work,text=True).strip()
    git('init','-q');git('config','user.email','fixture@example.invalid');git('config','user.name','fixture')
    git('add','analysis');git('commit','-q','-m','fixture source');tree=git('rev-parse','HEAD:analysis')
    script=script.replace('2866624de84c2f1a4881e9cee516db3f5530e3ba',tree)
    output=campaign/'real/spatial/20232024'
    if mode=='wrong_previous':members['$spatial_previous/manifest.json'].write_text('wrong prior\n')
    if mode=='occupied_output':output.mkdir()
    if mode=='occupied_log':Path(str(output)+'.log').write_text('occupied\n')
    if mode=='dirty_analysis':(work/'analysis/unreviewed.py').write_text('changed\n')
    shell=work/'command.sh';shell.write_text(script);marker=root/'native-stub';argv=root/'argv'
    env=dict(os.environ,SPATIAL_THIRD_MARKER=str(marker),SPATIAL_THIRD_ARGV=str(argv),SPATIAL_THIRD_EXIT='3' if mode=='native_exit3' else '0')
    done=subprocess.run(['/bin/zsh',str(shell)],cwd=root,env=env,capture_output=True,text=True)
    if mode in ('pass','native_exit3'):
        expected=3 if mode=='native_exit3' else 0
        assert done.returncode==expected and marker.exists(),(mode,done.stderr)
        assert Path(str(output)+'-exit.txt').read_text().strip()==str(expected) and Path(str(output)+'-finish.txt').exists()
        assert argv.read_text().splitlines()==['-m','hockey_stats.analysis_cli','fit','--family','spatial','--prepared',str(locations['spatial_prepared']),
            '--coaches',str(locations['spatial_coaches']),'--valued',str(locations['spatial_valued']),'--season','20232024',
            '--previous',str(locations['spatial_previous']),'--out',str(output)]
    else:assert done.returncode!=0 and not marker.exists() and not Path(str(output)+'-start.txt').exists(),(mode,done.stderr)
    results.append(dict(mode=mode,exit=done.returncode,native_stub_invoked=marker.exists()))
print(json.dumps(dict(status='passed',scope='all actual paths/pins replaced by scratch metadata/git and shell stubs; no real source/fit/reader/model/array call',
    predecessor_is_spatial_not_execution=True,canonical_year_three_output=True,controls=results,scratch=str(scratch)),indent=2))
