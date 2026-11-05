"""one held real year-two completion; three preserved heads, no numerical solve."""
import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

WORK=Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
CAMPAIGN=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01')
SOURCE=CAMPAIGN/'real/spatial/20222023'
OUTPUT=CAMPAIGN/'real/spatial/20222023-complete-01'
PREVIOUS=CAMPAIGN/'real/spatial/20212022'
PREPARED=Path('/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02')
COACHES=Path('/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json')
VALUED=CAMPAIGN/'real/scores/20222023'
ORIGINAL_TREE='2866624de84c2f1a4881e9cee516db3f5530e3ba'
INTERRUPTION=WORK/'docs/research/spatial-v1-08/receipts/real-second-spatial-interruption.json'
INTERRUPTION_SHA='0bc1f5cb3b09ed326b8176ad35b41d51d868ab1ac72ebef1bad52dd35692c684'
RECONNECTION=WORK/'docs/research/spatial-v1-08/receipts/real-second-spatial-reconnection-preflight.json'


def git(*args):return subprocess.check_output(['git',*args],cwd=WORK,text=True).strip()


def source_proof():
    """source text and grouping extraction proof; no model or artifact evaluation."""
    proof={}
    for module,changed in (('spatial_rates',{'fit_head','fit_spatial'}),('spatial_state',set())):
        old=subprocess.check_output(['git','show',f'{ORIGINAL_TREE}:src/hockey_stats/{module}.py'],cwd=WORK).decode()
        current=(WORK/f'analysis/src/hockey_stats/{module}.py').read_text()
        old_nodes=ast.parse(old).body;new_nodes=ast.parse(current).body
        old_functions={n.name:ast.get_source_segment(old,n) for n in old_nodes if isinstance(n,ast.FunctionDef)}
        new_functions={n.name:ast.get_source_segment(current,n) for n in new_nodes if isinstance(n,ast.FunctionDef)}
        for name,body in old_functions.items():
            if name not in changed:assert new_functions[name]==body, f'numerical/source body changed: {module}.{name}'
        old_fixed=[n for n in old_nodes if isinstance(n,(ast.Assign,ast.ClassDef))]
        new_fixed={getattr(n,'name',None) or ast.dump(n.targets[0]):n for n in new_nodes if isinstance(n,(ast.Assign,ast.ClassDef))}
        for node in old_fixed:assert ast.dump(node)==ast.dump(new_fixed[getattr(node,'name',None) or ast.dump(node.targets[0])])
        proof[module]=dict(original_file_sha256=sha256(old.encode()).hexdigest(),current_file_sha256=sha256(current.encode()).hexdigest(),unchanged_functions={n:sha256(body.encode()).hexdigest() for n,body in old_functions.items() if n not in changed})
        if module=='spatial_rates':
            old_head=old_functions['fit_head'];left=old_head.index('    work = None\n');right=old_head.index('    options = CONTINUATION',left);work=old_head[left:right]
            assert new_functions['fit_head']==old_head[:left]+'    work = _head_work(design, head)\n'+old_head[right:]
            assert new_functions['_head_work']=='def _head_work(design, head):\n'+work+'    return work'
            marker='    if ((design.purpose'
            assert old_functions['fit_spatial'][old_functions['fit_spatial'].index(marker):]==new_functions['fit_spatial'][new_functions['fit_spatial'].index(marker):]
    old_lock=subprocess.check_output(['git','show',f'{ORIGINAL_TREE}:uv.lock'],cwd=WORK)
    assert (WORK/'analysis/uv.lock').read_bytes()==old_lock
    proof['lock_sha256']=sha256(old_lock).hexdigest()
    return proof


def preflight(expected_head,expected_tree,reconnection_sha):
    assert git('rev-parse','HEAD')==expected_head and git('rev-parse','HEAD:analysis')==expected_tree
    assert git('status','--porcelain','--untracked-files=all','--','analysis')==''
    assert set(git('diff','--name-only',ORIGINAL_TREE,expected_tree).splitlines())=={'src/hockey_stats/spatial_rates.py','src/hockey_stats/spatial_state.py'}
    proof=source_proof()
    assert sha256(INTERRUPTION.read_bytes()).hexdigest()==INTERRUPTION_SHA
    assert sha256(RECONNECTION.read_bytes()).hexdigest()==reconnection_sha
    interruption=json.loads(INTERRUPTION.read_bytes());reconnection=json.loads(RECONNECTION.read_bytes())
    assert interruption['analysis_tree']==ORIGINAL_TREE and interruption['output']==str(SOURCE) and not (SOURCE/'manifest.json').exists() and not OUTPUT.exists()
    assert all(value=='complete' for value in interruption['head_status'].values())
    for row in [*reconnection['verified_preserved_files'],*reconnection['verified_input_manifests'],interruption['launch']]:
        assert sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256'], row['path']
    import numpy as np
    import scipy
    from scipy import version
    runtime=dict(python=sys.version.split()[0],numpy=np.__version__,scipy=scipy.__version__,scipy_git_revision=version.git_revision)
    assert runtime==reconnection['runtime'], 'reconnection runtime differs'
    source_files={str(Path(row['path']).relative_to(SOURCE)):row['sha256'] for row in interruption['preserved_head_files']}
    inputs={key:{name:next(row for row in reconnection['verified_input_manifests'] if row['path']==str(path))[name] for name in ('path','sha256')} for key,path in (('prepared',PREPARED/'manifest.json'),('coaches',COACHES),('valued',VALUED/'manifest.json'),('previous',PREVIOUS/'manifest.json'))}
    origin=dict(analysis_tree=ORIGINAL_TREE,inputs=inputs,launch={name:interruption['launch'][name] for name in ('path','sha256')},
        interruption=dict(path=str(INTERRUPTION),sha256=INTERRUPTION_SHA),reconnection=dict(path=str(RECONNECTION),sha256=reconnection_sha),
        run_records=[{name:row[name] for name in ('path','sha256')} for row in interruption['run_records']])
    return source_files,origin,dict(source_equivalence=proof,reconnection_runtime=runtime,
        runtime_limit='reconnection evidence only; original annual producer/runtime snapshot and original design/moments were not saved',
        original_fit_launch_head=Path(str(SOURCE)+'-launch-head.txt').read_text().strip())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--expected-head',required=True);parser.add_argument('--expected-analysis-tree',required=True)
    parser.add_argument('--expected-reconnection-sha256',required=True);args=parser.parse_args()
    began=perf_counter();files,origin,evidence=preflight(args.expected_head,args.expected_analysis_tree,args.expected_reconnection_sha256)
    evidence['input_identity_preflight_wall_seconds']=perf_counter()-began
    evidence['original_fit_evidence']=origin
    preflight_path=Path(str(OUTPUT)+'-completion-preflight.json')
    with preflight_path.open('x') as stream:json.dump(evidence,stream,indent=2,allow_nan=False);stream.write('\n')
    print('completion pins accepted; source rebuild started',flush=True)
    from hockey_stats.analysis_data import read_prepared
    from hockey_stats.spatial_design import prepare_spatial
    from hockey_stats.spatial_state import read_spatial_state
    from hockey_stats.spatial_rates import complete_spatial
    read_started=perf_counter();previous=read_spatial_state(PREVIOUS,'real');prepared=read_prepared(PREPARED,'real');read_wall=perf_counter()-read_started
    design=prepare_spatial(prepared,COACHES,VALUED,'20222023');design.resources['input_read_wall_seconds']=read_wall
    design.resources['input_identity_preflight_wall_seconds']=evidence['input_identity_preflight_wall_seconds']
    print('source rebuild complete; preserved heads and three exact anchors follow',flush=True)
    result=complete_spatial(design,previous,SOURCE,OUTPUT,expected_files=files,expected_inputs=origin['inputs'])
    print(json.dumps(dict(status='completion_written_canonical_read_passed_pending_saved_history_acceptance',manifest=str(result.path/'manifest.json'),wall_seconds=perf_counter()-began)),flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
