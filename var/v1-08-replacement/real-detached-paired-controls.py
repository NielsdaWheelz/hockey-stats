"""finite paired one-byte checks for the accepted real detached profile."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

REPO=Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
ROOT=Path('/Volumes/Expansion/hockey-stats')
REAL=ROOT/'runs/execution-spatial-replacement-20261031-01/real'
PROFILE=REPO/'var/v1-08-replacement/real-detached.sb'
PROFILE_SHA='6964a1c0588a891dcb9db8f749fbe0855b454333a71a00e62b280ef755a3f53e'
ASSET=REPO/'app/dist/node/server/main.js'
ASSET_SHA='9efd1fd25621be10a3032ca65718fb45f7cdcb6a7c7b91bd8c571eb4bf052e05'
DATABASE=REAL/'candidate/player-analysis.sqlite'
VERIFICATION=REAL/'candidate/verification.json'
OUTPUT=REAL/'detached-paired-controls-01.json'
DENIED=(
 ('raw',ROOT/'raw/fresh-20260930/captures/2025021108/landing/body.bin'),
 ('captures',ROOT/'captures/2025021108/play-report/body.bin'),
 ('factual',ROOT/'factual/facts-v1-03-20261024-02/facts.stdout'),
 ('references',ROOT/'references/20252026/season-games/body.bin'),
 ('chance',ROOT/'chance/03b-20260930/assessments/confirmation-stronger_origin_prior.json'),
 ('archive',ROOT/'archive/local-research-20261020/duplicate-verified.json'),
 ('corpora',ROOT/'corpora/03b-20260930-capacity-20232024/corpus.json'),
 ('prepared',ROOT/'prepared/evidence-v1-01-02-native-support-check.json'),
 ('coaches',ROOT/'runs/coaches-v1-02-20261022-01/real-closeout.json'),
 ('execution',ROOT/'runs/execution-v1-06-20261026-01/fixture/factual-availability-main-parity.json'),
 ('local_preparation',Path('/Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6/manifest.json')),
 ('local_coaches',Path('/Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json')),
 ('primary_checkout_source',Path('/Users/nnandal/Documents/code/hockey-stats/app/src/server/main.ts')),
 ('local_results_copy',REPO/'var/v1-08-product/synthetic-state-interface/exchange/manifest.json'),
 ('analysis_source',REPO/'analysis/src/hockey_stats/spatial_composition.py'),
 ('fixture',REPO/'fixtures/README.md'),
 ('research',REPO/'docs/brief.md'),
 ('state_20212022',REAL/'spatial/20212022/manifest.json'),
 ('state_20222023',REAL/'spatial/20222023-complete-01/manifest.json'),
 ('state_20232024',REAL/'spatial/20232024/manifest.json'),
 ('state_20242025',REAL/'spatial/20242025/manifest.json'),
 ('state_20252026',REAL/'spatial/20252026/manifest.json'),
 ('state_selection',REAL/'states-selection.json'),
 ('results',REAL/'results/manifest.json'),
 ('candidate_verification',VERIFICATION),
)
READ="""import hashlib,json,sys
try:
 with open(sys.argv[1],'rb',buffering=0) as f: byte=f.read(1)
 if len(byte)!=1: raise RuntimeError('empty target')
 print(json.dumps({'ok':True,'byte_sha256':hashlib.sha256(byte).hexdigest()}))
except OSError as error:
 print(json.dumps({'ok':False,'errno':error.errno}));sys.exit(1)
"""


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def read_one(path,inside):
    argv=['/usr/bin/python3','-c',READ,str(path)]
    if inside: argv=['/usr/bin/sandbox-exec','-f',str(PROFILE),*argv]
    result=subprocess.run(argv,capture_output=True,text=True,timeout=30)
    try: body=json.loads(result.stdout)
    except json.JSONDecodeError: raise AssertionError(f'non-json read result: {path}: {result.stderr}')
    return result.returncode,body


def stat(path):
    value=path.stat();return f'{value.st_size}:{int(value.st_mtime)}'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--database-sha256',required=True)
    parser.add_argument('--database-stat',required=True)
    parser.add_argument('--verification-sha256',required=True)
    args=parser.parse_args()
    assert re.fullmatch('[0-9a-f]{64}',args.database_sha256) and re.fullmatch('[0-9a-f]{64}',args.verification_sha256)
    assert re.fullmatch('[0-9]+:[0-9]+',args.database_stat)
    assert not OUTPUT.exists()
    assert sha(PROFILE)==PROFILE_SHA and sha(ASSET)==ASSET_SHA
    assert sha(VERIFICATION)==args.verification_sha256 and stat(DATABASE)==args.database_stat
    checks=[]
    for role,path in DENIED:
        outside,outer=read_one(path,False);inside,inner=read_one(path,True)
        assert outside==0 and outer.get('ok') is True, f'outside read failed: {path}'
        assert inside==1 and inner==dict(ok=False,errno=1), f'inside read not EPERM: {path}'
        checks.append(dict(role=role,path=str(path),outside='one byte read',inside='EPERM'))
    positives=[]
    for role,path in (('built_asset',ASSET),('accepted_database',DATABASE)):
        outside,outer=read_one(path,False);inside,inner=read_one(path,True)
        assert outside==inside==0 and outer.get('ok') is True and inner==outer, f'positive read differs: {path}'
        positives.append(dict(role=role,path=str(path),outside='one byte read',inside='same byte read'))
    assert sha(PROFILE)==PROFILE_SHA and sha(ASSET)==ASSET_SHA
    assert sha(VERIFICATION)==args.verification_sha256 and stat(DATABASE)==args.database_stat
    report=dict(status='paired_reads_passed_pending_runtime_acceptance',profile=dict(path=str(PROFILE),sha256=PROFILE_SHA),
        database=dict(path=str(DATABASE),accepted_sha256=args.database_sha256,stat=args.database_stat,
                      hash_scope='accepted publication identity recorded; database not rehashed by one-byte control'),
        verification=dict(path=str(VERIFICATION),sha256=args.verification_sha256),asset=dict(path=str(ASSET),sha256=ASSET_SHA),
        denied=checks,positive=positives,server_started=False,scope='finite named files only; no directory discovery or claim of exhaustive denial')
    with OUTPUT.open('x') as f: json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(dict(status=report['status'],output=str(OUTPUT))))


if __name__=='__main__': main()
