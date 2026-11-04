"""one existing saved fixture sanity run for the new independent audit."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

WORK=Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
ROOT=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20212022')
OUTPUT=ROOT.parents[1]/'independent-first-spatial-audit-01'
manifest=json.loads((ROOT/'manifest.json').read_bytes())
assert manifest['purpose']=='fixture' and manifest['season']=='20212022' and manifest['previous'] is None
assert not OUTPUT.exists()
sha=hashlib.sha256((ROOT/'manifest.json').read_bytes()).hexdigest()
script=WORK/'var/v1-08-replacement/independent_first_spatial_audit.py'
command=[sys.executable,str(script),'--input',str(ROOT),'--expected-manifest-sha256',sha,'--purpose','fixture','--out',str(OUTPUT)]
run=subprocess.run(command,cwd=WORK)
assert run.returncode==0
report=json.loads((OUTPUT/'audit.json').read_bytes())
assert report['status']=='passed_saved_first_year_audit' and report['purpose']=='fixture'
assert report['calls']==dict(independent_objectives=dict(volume=1,shape=1,quality=1),production_evaluator=0,production_reader=0,native_fit=0,source_pass=0,probes=0)
for head,data in report['heads'].items():
    assert max(data['component_absolute_differences'].values())<=1e-8
    assert abs(data['gradient_norm_difference'])<=1e-8
assert report['target_boundary']['events']==report['design']['event_rows'] and report['target_boundary']['origin_rows']==report['design']['origin_rows']
assert len(report['actual_context_examples'])==2
print(json.dumps(dict(status='passed',scope='one saved first-year fixture only; no fit/source/probe/production owner call',input_manifest_sha256=sha,output=str(OUTPUT),audit_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),report_sha256=hashlib.sha256((OUTPUT/'audit.json').read_bytes()).hexdigest(),fixture=report),indent=2))
