"""one pinned saved u assembly; no source rebuild or numerical evaluation."""
import argparse
import json
from pathlib import Path
import resource
import subprocess
import sys
from time import perf_counter

from hockey_stats.artifacts import digest, require, write_json
from hockey_stats.chance_cli import identity
from hockey_stats.execution_u_repair import assemble_u_repair

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[1]
RUN=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01')
CAPTURE=RUN/'real/u-repair-01'
REPAIR=CAPTURE/'repair-01/repair.json'
OUTPUT=CAPTURE/'assembled-01/20252026'
ANALYSIS_TREE='fc716257eb118d1a091472cde4b214e8bca1f753'
PINS={
    REPAIR:'28c6d3b9a3f1261191085dd52831e7572103d46f62c2a667fcbbd1ecb53abdf1',
    CAPTURE/'repair-01/qualification/qualification.json':'2514390196a9e827caaecd67ece0b28cdb069fa5efb7bd339a93970ffd4f9aec',
    CAPTURE/'repair-01/basic-qualification.json':'02cd47ca8a11217a7fac05e6af8121b356831e78a06beeb1ceed42eeb9956aab',
    CAPTURE/'inputs/manifest.json':'031975b95114fbe62c0e468ebdf16d6170c27f15407b7df71ff0b08e18517a6c',
    CAPTURE/'diagnosis/diagnosis.json':'115da4fe4c18912b74b1970f1825a4338f0f54c6ccd9f0cfb3f7e10dfa026af1',
    CAPTURE/'source-check.json':'9f1351a2cf619e32a7ebeb487a4dda4b3892dcb005b7f2ded917a71354509aa7',
    CAPTURE/'capture-reloaded.json':'a10365297148c215f764bb2cde5178602a5eda13563fca36f6345bfd4f7fb9f6',
    RUN/'real/execution-final-02/20252026/manifest.json':'cb075d5e59aea61589411e4573db7192c45fddd8265a807c2c39c2084b504e22',
    RUN/'real/execution/20242025/manifest.json':'1ba2c8af310d12239d6cabb89ee6cc92b6b98bd95e6834b4f44e303802a44cfe',
    Path('/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json'):'63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c',
    Path('/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json'):'102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0',
    WORK/'analysis/src/hockey_stats/execution_u_repair.py':'4c7dfb499cccca81735594389a510850dba68aad700776059500fb7a05cb6522',
    WORK/'analysis/src/hockey_stats/execution_state.py':'2f65ae947777eefee441af15e7609d3cae2edb5375bc9f99a85a4cf82e57cf14',
    HERE/'repair_execution_u.py':'9ddb1425196328fff332f5ba1da91a231d77fce233fe48565e883b9e594d9c69',
    WORK/'analysis/src/hockey_stats/execution_trace.py':'89af29e14de76a3a8f332b3753c5640d9b6c825f493719163dd687b7b824bc13',
    HERE/'diagnose_execution_u.py':'031f30d640c0d526e35d8d862803718c1f565ee99ca2ef5638b9e36df3f25ca1',
    WORK/'docs/research/spatial-v1-08/reviews/u-diagnosis-saved-review.md':'2e04c4a6331c2a36f176e0e307b0f520a5255d19cb23513935f13da9b80ecdbd',
    WORK/'docs/research/spatial-v1-08/receipts/u-capture-diagnosis-completion.json':'6950fed6a7593168e9554515387debcc9e0d02b091d71995f57a00272da623d9',
    WORK/'docs/research/spatial-v1-08/execution-u-exact-sum-repair.md':'6beb304528f63ecb335ddab57e9baa9eb31be5099471cb5033d5810e0515abb7',
}


def saved_audit(state, donor_path, qualification, launch_head):
    """inspect saved bytes/json and the already checked state; never strict-read again."""
    donor_path=Path(donor_path);donor=json.loads(donor_path.read_text())
    output=state.path.parent;original=donor_path.parent
    members={row['path']:row['sha256'] for row in donor['files']}
    paths=[f'heads/{head}.npz' for head in ('u','q','r','g')]+[f'resolution/{head}.npz' for head in ('q','r','g')]
    retained=[]
    for name in paths:
        old=identity(original/name);new=identity(output/name)
        require(old['sha256']==new['sha256']==members[name], 'assembly retained bytes differ: '+name)
        retained.append(dict(path=name,sha256=new['sha256']))
    for head in ('u','q','r','g'):
        old=json.loads((original/f'heads/{head}.json').read_text())
        require({key:value for key,value in old.items() if key!='resolution'} ==
                {key:value for key,value in state.heads[head].items() if key!='resolution'}, 'assembly baseline metadata differs: '+head)
        require(state.heads[head]['resolution']['status']=='passed','assembled head lacks passing resolution')
    for head in ('q','r','g'):
        old=json.loads((original/f'resolution/{head}.json').read_text())
        new=json.loads((output/f'resolution/{head}.json').read_text())
        require({key:value for key,value in old.items() if key!='baseline'} ==
                {key:value for key,value in new.items() if key!='baseline'} and old['baseline']!=new['baseline'],
                'assembly retained probe metadata/comparison differs: '+head)
    before=json.loads((original/'resolution/baseline.json').read_text())
    after=json.loads((output/'resolution/baseline.json').read_text())
    require(after['selector']==before['selector'] and after['heads']==before['heads'], 'assembly baseline definitions/selector differ')
    require(after['identity']['implementation']==state.manifest['implementation']
            and state.manifest['implementation']['git_commit']==launch_head
            and state.manifest['implementation']['git_dirty'] is False, 'assembly implementation identity is not the launch source')
    require(all(state.manifest[key]==donor[key] for key in ('purpose','season','recipe','prepared','coaches','previous','training_cutoff')),
            'assembly changed baseline lineage or population')
    require(state.usage=='annual' and state.heads['u']['resolution']['comparison']==qualification['comparison']
            and qualification['comparison']['maximum_probability_change']<=1e-5, 'assembled u comparison differs')
    require(state.manifest['u_repair']['retained_members']==retained, 'assembly retained provenance differs')
    return dict(retained_members=retained,baseline_metadata_outside_resolution_exact=True,
        qrg_probe_metadata_and_comparisons_exact=True,selector_and_head_definition_hashes_exact=True,
        history_and_population_exact=True,ordinary_score_consumer_eligible=True,
        strict_read_owner='write_execution_state',strict_reads_of_assembled_family=1,extra_strict_reads=0,
        full_objective_calls=0,probability_comparisons=0,native_calls=0,source_passes=0)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repair',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--expected-launch-head',required=True)
    parser.add_argument('--expected-helper-sha256',required=True)
    parser.add_argument('--acceptance',required=True,type=Path)
    parser.add_argument('--acceptance-sha256',required=True)
    args=parser.parse_args();started=perf_counter()
    require(Path.cwd().resolve()==WORK,'assembly must run in the isolated v1-08 checkout')
    require(args.repair==REPAIR and args.output==OUTPUT,'assembly repair/output locators differ')
    require(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==args.expected_launch_head,'assembly launch head changed')
    require(subprocess.check_output(['git','rev-parse','HEAD:analysis'],text=True).strip()==ANALYSIS_TREE,'assembly analysis tree differs')
    require(not subprocess.check_output(['git','status','--porcelain','--untracked-files=all','--','analysis'],text=True).strip(),'assembly analysis tree is dirty')
    require(identity(Path(__file__))['sha256']==args.expected_helper_sha256,'assembly helper differs')
    digest(args.acceptance_sha256)
    require(args.acceptance.is_absolute() and identity(args.acceptance)['sha256']==args.acceptance_sha256,'saved repair acceptance differs')
    require(not OUTPUT.parent.exists(),'assembly destination or side receipts already exist')
    pinned=[]
    for path,sha in PINS.items():
        reference=identity(path);require(reference['sha256']==sha,'assembly input/source pin differs: '+str(path));pinned.append(reference)
    report=json.loads(REPAIR.read_text())
    qualification=json.loads(Path(report['probability_qualification']['path']).read_text())
    require(report['status']=='qualified' and report['eligible_endpoint'] is True and qualification['probability_passed'] is True,
            'saved repair is not qualified')
    OUTPUT.parent.mkdir()
    write_json(OUTPUT.parent/'assembly-start.json',dict(actual_launch_head=args.expected_launch_head,
        reviewed_analysis_tree=ANALYSIS_TREE,helper=identity(Path(__file__)),acceptance=identity(args.acceptance),pins=pinned,
        repair=identity(REPAIR),output=str(OUTPUT)))
    try:
        print('saved u assembly started',flush=True)
        state=assemble_u_repair(REPAIR,OUTPUT)
        print('canonical assembly and strict read complete',flush=True)
        audit_started=perf_counter();audit=saved_audit(state,qualification['donor']['path'],qualification,args.expected_launch_head)
        audit.update(manifest=identity(state.path),saved_byte_audit_wall_seconds=perf_counter()-audit_started)
        write_json(OUTPUT.parent/'assembly-saved-audit.json',audit)
        write_json(OUTPUT.parent/'assembly-result.json',dict(status='assembled_and_saved_byte_audited',manifest=identity(state.path),
            saved_audit=identity(OUTPUT.parent/'assembly-saved-audit.json'),wall_seconds=perf_counter()-started,
            process_peak_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
            scope='canonical saved assembly plus its one strict read, then byte/json audit; no numerical or source reconstruction'))
        print(json.dumps(dict(status='assembled_and_saved_byte_audited',manifest=str(state.path))))
        return 0
    except BaseException as error:
        write_json(OUTPUT.parent/'assembly-failure.json',dict(status='stopped; no automatic successor',error_type=type(error).__name__,error=str(error)))
        raise


if __name__=='__main__':raise SystemExit(main())
