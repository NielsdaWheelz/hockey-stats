"""focused use of the frozen saved-sum rounding contract; no project calls."""
import hashlib,json
from math import log
from pathlib import Path

WORK=Path('/Users/nnandal/Documents/code/hockey-stats-v1-08');C=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real');NEW=C/'scores/20252026';OLD=Path('/Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/current-04/scores/20252026')
facts=json.loads((WORK/'var/v1-08-replacement/independent-final-score-saved-checked-facts.json').read_text());manifest=json.loads((NEW/'manifest.json').read_text());resolution=json.loads((NEW/'resolution.json').read_text());canonical=json.loads((C/'score-20252026-saved-acceptance.json').read_text())
assert facts['status']=='passed' and facts['panel_goal_sums']==canonical['panel_goal_sums']
# exact literal contract from frozen execution_scores._log_error/_near; no new tolerance.
def near(x,y,terms):
    left=0. if x<=0 else (abs(log(x))+2*terms+8)*2.**-52
    right=0. if y<=0 else (abs(log(y))+2*terms+8)*2.**-52
    return abs(x-y)<=(left+right)*max(x,y)+2.**-1072
panels={r['panel_id']:r for r in facts['panel_goal_sums']};origins={r['panel_id']:r['origins'] for r in manifest['panels']};checked=0;max_error=0.
for root,label in [(OLD,'old'),(NEW,'new')]:
    with (root/'projections.jsonl').open() as stream:
        for line in stream:
            row=json.loads(line);ref=row['reference_panel'];panel=panels[ref['panel_id']]
            for prefix in ['u','uq','uqr','uqrg']:
                expected=panel[label].get('neutral.'+prefix,0.);actual=ref['neutral'][prefix];assert near(expected,actual,origins[ref['panel_id']]);max_error=max(max_error,abs(expected-actual));checked+=1
for probe in resolution['probes']:
    for row in probe['neutral_panels']:
        for prefix in ['u','uq','uqr','uqrg']:
            expected=panels[row['panel_id']]['new'].get('neutral.'+prefix,0.);actual=row['baseline'][prefix];assert near(expected,actual,origins[row['panel_id']]);max_error=max(max_error,abs(expected-actual));checked+=1
print(json.dumps(dict(status='passed',scope='focused saved reference/propagation sum check using the unchanged frozen rounding contract, no reader/evaluator/source/score',comparisons=checked,max_absolute_sum_rounding_difference=max_error,canonical_panel_sums_exact=True,contract='abs(left-right)<=(_log_error(left,terms)+_log_error(right,terms))*max(left,right)+2**-1072; _log_error=(abs(log(mass))+2*terms+8)*2**-52 for positive mass else0'),indent=2))
