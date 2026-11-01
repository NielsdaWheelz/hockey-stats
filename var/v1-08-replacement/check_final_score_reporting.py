"""temporary pure final-report controls over accepted fixture JSON; never main."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from math import nextafter, inf
from pathlib import Path
from time import perf_counter

WORK = Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
FIXTURE = Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture')
HELPER = WORK / 'var/v1-08-replacement/accept_real_score_20252026.py'
OUT = WORK / 'var/v1-08-replacement/final-score-reporting-controls.json'


def main():
    began = perf_counter()
    source = HELPER.read_text()
    ast.parse(source)
    spec = importlib.util.spec_from_file_location('held_final_score', HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.read_execution_scores = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('strict reader must stay uncalled'))
    score = helper.read(FIXTURE / 'scores/20252026/manifest.json')
    annual = helper.read(FIXTURE / 'execution/20252026/manifest.json')
    assert helper.sha(FIXTURE / 'scores/20252026/manifest.json') == '80f61f0dc1941042c5bf1e3488fdaaed9cc0fb303670f6780558ff11a603072a'
    annual_sha = helper.sha(FIXTURE / 'execution/20252026/manifest.json')
    assert annual_sha == '5223976602e9a45e66e3e6160ba502cf01b0c39969e2360fa2c0c4384623e047'
    resolution = helper.bound_json(FIXTURE / 'scores/20252026', score, 'resolution.json')
    baseline = helper.bound_json(FIXTURE / 'execution/20252026', annual, 'resolution/baseline.json')
    baseline_ref = {key: resolution['baseline'][key] for key in ('path', 'sha256')}
    assert helper.sha(FIXTURE / 'execution/20252026/resolution/baseline.json') == baseline_ref['sha256']
    first = resolution['probes'][0]
    # scaffolding supplies independent function inputs without reading events,
    # projections or model arrays. it does not independently verify their values.
    keys = resolution['event_probes']['actual_keys']
    bins = first['actual_keys']['baseline_danger']
    danger_values = [value for name, value in (('<.05', .01), ('[.05,.15)', .1), ('>=.15', .2)) for _ in range(bins.get(name, 0))]
    actual_events = {key: dict(prefixes={name: dict(uqrg=row['baseline']/len(keys))
        for name, row in first['actual_keys']['expected_sums'].items()},
        conditional_probabilities=dict(neutral_on_net_goal_probability=value))
        for key, value in zip(keys, danger_values, strict=True)}
    kwargs = dict(annual_sha=annual_sha, baseline_ref=baseline_ref, annual_selector=baseline['selector'],
        annual_heads={row['head']: dict(resolution=dict(status='passed', baseline=baseline_ref, probe=row['probe'])) for row in resolution['probes']},
        panel_records=score['panels'],
        panels={row['panel_id']: dict(rows=row['events'], new={'neutral.'+key: value for key, value in row['baseline'].items()})
                for row in first['neutral_panels']},
        actual_events=actual_events,
        projection_values={tuple(row['pair']): {key: None if value is None else 0. for key, value in row['scalar_absolute_changes'].items()}
                           for row in first['pairs']})
    result = helper.check_final_propagation(resolution, **kwargs)
    assert len(result['heads']) == 4 and len(result['focal_selector']['pairs']) == 38
    assert len(result['focal_selector']['requirements']) == 45
    assert sum(row['disposition'] == 'unavailable' for row in result['focal_selector']['requirements']) == 5
    refusals = []
    for name in ('probability_budget', 'annual_binding', 'probe_binding', 'panel_delta', 'pair_maximum', 'pair_nullability', 'pair_order'):
        changed = deepcopy(resolution)
        if name == 'probability_budget':
            changed['probes'][0]['maximum_changes']['actual_probability'] = nextafter(1e-5, inf)
        elif name == 'annual_binding':
            changed['baseline']['annual_manifest_sha256'] = '0'*64
        elif name == 'probe_binding':
            changed['probes'][0]['probe']['sha256'] = '0'*64
        elif name == 'panel_delta':
            changed['probes'][0]['neutral_panels'][0]['uqrg_change'] = .1
        elif name == 'pair_maximum':
            changed['probes'][0]['maximum_changes']['per100'] = .0009
        elif name == 'pair_nullability':
            row = changed['probes'][0]['pairs'][0]['scalar_absolute_changes']
            field = next(iter(row))
            row[field] = 0. if row[field] is None else None
        else:
            changed['probes'][0]['pairs'][:2] = reversed(changed['probes'][0]['pairs'][:2])
        try:
            helper.check_final_propagation(changed, **kwargs)
        except AssertionError:
            refusals.append(name)
        else:
            raise AssertionError('malformed record accepted: '+name)
    receipt = dict(kind='held-final-score-reporting-controls', status='passed', recorded_at_utc=datetime.now(timezone.utc).isoformat(),
        helper=helper.identity(HELPER), checker=helper.identity(Path(__file__).resolve()),
        fixture_inputs=[helper.identity(FIXTURE / branch) for branch in ('scores/20252026/manifest.json', 'scores/20252026/resolution.json',
                       'execution/20252026/manifest.json', 'execution/20252026/resolution/baseline.json')],
        green=dict(heads=4, neutral_panels_per_head=32, actual_keys=len(keys), synthetic_witnesses=len(resolution['event_probes']['fixture_witnesses']),
            distinct_focal_pairs=38, requirements=45, unavailable_focal_requirements=5, malformed_refusals=refusals),
        scope='actual accepted fixture resolution/selector metadata plus synthetic baseline input scaffolding; reporting arithmetic, joins and refusal controls only; not independent fixture event/projection or predictor validation',
        execution=dict(helper_main=0, full_score_strict_reads=0, state_strict_reads=0, event_or_projection_reads=0, array_reads=0, source_passes=0, fits=0, scores=0),
        wall_seconds=perf_counter()-began)
    with OUT.open('x') as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
