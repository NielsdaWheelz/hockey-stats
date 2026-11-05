"""small saved-run receipts for the four known remaining real spatial annuals; no model calls."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from time import perf_counter

CAMPAIGN=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01')
ANALYSIS='38ec706cb505ea3d9936518dd119869e7695200b'
RECIPE='04a9c15d868a764744c796fb82065f2d95d2efa27914f12ecb871806ccc91e8b'
PREPARED='/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json'
PREPARED_SHA='63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c'
COACHES='/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json'
COACHES_SHA='102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0'
HEADS=('volume','shape','quality')
SOLVER=dict(maxiter=10000,ftol=1e-15,gtol=1e-6,maxcor=10)
CONTINUATION=dict(maxiter=10000,ftol=1e-16,gtol=1e-7,maxcor=10)
STATE_PATHS={'20212022':'real/spatial/20212022','20222023':'real/spatial/20222023-complete-01','20232024':'real/spatial/20232024','20242025':'real/spatial/20242025','20252026':'real/spatial/20252026'}
SCORES=dict(zip(('20222023','20232024','20242025','20252026'),(
 '296ae0173fb1256ddb91d14eee5a917d76c3e88f92cc3556a8647b1f10a8da20',
 'f13a1136c3df857a83d9f37aa10b919b64934e240515c3a8d5e2c556a778b238',
 '86e346f82d874748215f582c1a4445ab75b01358dd61d37fa4082254879c62de',
 '40e23b35ac9c8458229b076150366960c4a25d7a92ae028d2b45dc39c89104fc')))
EXECUTION={
 '20222023':('real/execution/20222023/manifest.json','eb52909e32d051b205e9cd6ccdcb8227371202d469a52357cfb926c94cff599c'),
 '20232024':('real/execution/20232024/manifest.json','dd8b638dd8eb3e8af25722f53f633202b5fa28ef3ce81ec45bb9a180d9f09bfa'),
 '20242025':('real/execution/20242025/manifest.json','1ba2c8af310d12239d6cabb89ee6cc92b6b98bd95e6834b4f44e303802a44cfe'),
 '20252026':('real/u-repair-01/assembled-01/20252026/manifest.json','59e3432df70366c4e058007f4396be7737f76afada4fad96c84896dd12a6f276')}


def checked_json(path,expected):
    assert re.fullmatch('[0-9a-f]{64}',expected), 'unavailable expected digest'
    raw=path.read_bytes();assert sha256(raw).hexdigest()==expected, f'digest differs: {path}'
    return json.loads(raw)


def checksum_rows(text):
    rows={}
    for line in text.splitlines():
        fields=line.split(None,1);assert len(fields)==2 and re.fullmatch('[0-9a-f]{64}',fields[0]), 'invalid checksum record'
        digest,path=fields;assert path not in rows, 'duplicate checksum path';rows[path]=digest
    assert rows, 'empty checksum record'
    return rows


def saved_run_receipt(current,previous,expected,previous_expected,command_expected):
    began=perf_counter();current,previous=Path(current),Path(previous)
    manifest=checked_json(current/'manifest.json',expected);old=checked_json(previous/'manifest.json',previous_expected)
    year=manifest['season'];assert year in SCORES and manifest['kind']==old['kind']=='spatial_state' and manifest['purpose']==old['purpose']=='real'
    previous_year=f'{int(year[:4])-1}{year[:4]}'
    assert current==CAMPAIGN/STATE_PATHS[year] and previous==CAMPAIGN/STATE_PATHS[previous_year]
    assert old['season']==previous_year
    assert manifest['previous']==dict(path=str(previous/'manifest.json'),sha256=previous_expected,season=old['season'],purpose='real',usage='annual')
    for name,path,digest in (('prepared',PREPARED,PREPARED_SHA),('coaches',COACHES,COACHES_SHA),('valued',str(CAMPAIGN/'real/scores'/year/'manifest.json'),SCORES[year])):
        assert manifest[name]['path']==path and manifest[name]['sha256']==digest, f'{name} binding differs'
    assert manifest['valued']['season']==year
    texts={};run_records=[]
    for suffix in ('-exit.txt','-start.txt','-finish.txt','-shell.pid','-launch-head.txt','-launch-analysis-tree.txt','-launch-analysis-status.txt','-launch-command-sha256.txt','-launch-inputs-sha256.txt','-launch-acceptance-sha256.txt','-launch-spatial-recipe.txt','.log'):
        path=Path(str(current)+suffix);raw=path.read_bytes();texts[suffix]=raw.decode()
        run_records.append(dict(path=str(path),sha256=sha256(raw).hexdigest()))
    completion_preflight=None
    if year=='20222023':
        path=Path(str(current)+'-completion-preflight.json');raw=path.read_bytes()
        completion_preflight=dict(path=str(path),sha256=sha256(raw).hexdigest(),evidence=json.loads(raw))
    assert texts['-exit.txt'].strip()=='0', 'producer exit is not successful'
    assert texts['-launch-analysis-tree.txt'].strip()==ANALYSIS and texts['-launch-analysis-status.txt']=='', 'launch source differs'
    assert texts['-launch-spatial-recipe.txt'].strip()==RECIPE, 'launch recipe differs'
    launch_head=texts['-launch-head.txt'].strip();assert re.fullmatch('[0-9a-f]{40}',launch_head)
    assert texts['-start.txt'].strip() and texts['-finish.txt'].strip() and int(texts['-shell.pid'])>0
    command=checksum_rows(texts['-launch-command-sha256.txt']);assert len(command)==1 and list(command.values())==[command_expected]
    execution_path,execution_sha=EXECUTION[year]
    inputs={PREPARED:PREPARED_SHA,COACHES:COACHES_SHA,str(CAMPAIGN/'real/scores'/year/'manifest.json'):SCORES[year],str(previous/'manifest.json'):previous_expected,str(CAMPAIGN/execution_path):execution_sha}
    assert checksum_rows(texts['-launch-inputs-sha256.txt'])==inputs, 'launch input pins differ'
    acceptance=checksum_rows(texts['-launch-acceptance-sha256.txt'])
    assert [row['head'] for row in manifest['heads']]==list(HEADS) and all(row['status']=='complete' for row in manifest['heads'])
    bound={row['path']:row['sha256'] for row in manifest['files']};heads={};probes={}
    for name in HEADS:
        data=checked_json(current/f'heads/{name}.json',bound[f'heads/{name}.json'])
        assert data['head']==name and data['status']=='complete' and data['reasons']==[]
        solver=data['solver'];assert solver['converged'] is True and solver['options']==SOLVER and solver['maxfun']==15000 and solver['maxls']==20
        heads[name]={key:data[key] for key in ('status','reasons','solver','objective','resources')}
    if year!='20252026':
        assert not any(name.startswith('probes/') for name in bound) and not (current/'probes').exists(), 'unexpected earlier-year probes'
    else:
        for name in HEADS:
            data=checked_json(current/f'probes/{name}.json',bound[f'probes/{name}.json'])
            comparison=checked_json(current/f'probes/{name}-comparison.json',bound[f'probes/{name}-comparison.json'])
            assert data['head']==name and data['status']=='complete' and data['solver']['converged'] is True
            assert data['solver']['options']==CONTINUATION and data['solver']['maxfun']==15000 and data['solver']['maxls']==20
            assert comparison['status']=='passed' and comparison['failures']==[], 'final numerical probe is not passed'
            probes[name]=dict(metadata=dict(path=f'probes/{name}.json',sha256=bound[f'probes/{name}.json']),solver=data['solver'],comparison=comparison,comparison_sha256=bound[f'probes/{name}-comparison.json'])
    log=texts['.log'];timing=re.findall(r'([\d.]+) real\s+([\d.]+) user\s+([\d.]+) sys',log)
    rss=re.findall(r'(\d+)\s+maximum resident set size',log);footprint=re.findall(r'(\d+)\s+peak memory footprint',log)
    return dict(kind='remaining-real-spatial-saved-run-receipt',status='saved_run_passed_pending_history_audit_and_root_acceptance',season=year,
        manifest=dict(path=str(current/'manifest.json'),sha256=expected),previous=manifest['previous'],implementation=manifest['implementation'],
        inputs={key:manifest[key] for key in ('prepared','coaches','valued')},launch=dict(exit=0,head=launch_head,analysis_tree=ANALYSIS,
            start=texts['-start.txt'].strip(),finish=texts['-finish.txt'].strip(),shell_pid=int(texts['-shell.pid']),command=command,input_pins=inputs,acceptance_pins=acceptance,recipe=RECIPE),
        heads=heads,probes=probes,producer_resources=manifest['resources'],run_records=run_records,completion_preflight=completion_preflight,
        whole_command=dict(timing=None if not timing else dict(zip(('wall_seconds','user_seconds','system_seconds'),map(float,timing[-1]))),maximum_resident_bytes=None if not rss else int(rss[-1]),peak_memory_footprint_bytes=None if not footprint else int(footprint[-1])),
        metadata_readback_wall_seconds=perf_counter()-began,
        scope='small saved json and run records only; canonical writer owns numerical accounting, full member validation and projections; independent history audit owns raw history, ages, centers and rates; no extra model/reader call')


def write_receipt(current,previous,expected,previous_expected,command_expected,output):
    output=Path(output);assert not output.exists(), 'receipt output occupied'
    assert not output.resolve().is_relative_to(Path(current).resolve()) and not output.resolve().is_relative_to(Path(previous).resolve()), 'receipt must be outside saved annuals'
    result=saved_run_receipt(current,previous,expected,previous_expected,command_expected)
    with output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True);parser.add_argument('--previous',type=Path,required=True)
    parser.add_argument('--expected-manifest-sha256',required=True);parser.add_argument('--expected-previous-manifest-sha256',required=True)
    parser.add_argument('--expected-command-sha256',required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    result=write_receipt(args.input,args.previous,args.expected_manifest_sha256,args.expected_previous_manifest_sha256,args.expected_command_sha256,args.out)
    print(json.dumps(dict(status=result['status'],receipt=str(args.out))));return 0


if __name__=='__main__':raise SystemExit(main())
