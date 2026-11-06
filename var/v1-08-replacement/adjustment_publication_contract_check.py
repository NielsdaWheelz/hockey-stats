"""temporary saved-row integration controls for the frozen unbounded-rate closure contract."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from hockey_stats import analysis_publication as publication
from hockey_stats.captures import InputContractError

ROOT = Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/results')
TERMS = ('baseline', 'self', 'teammates', 'opponents', 'coaching_other_context')
results = []
files = []
witness = None
saved_failures = []
checked = pending = numeric = 0


def validate(row):
    year = row['season']
    data = row['result']['data']
    methods = {} if data is None else {data['method_id']: dict(family='spatial', fit_seasons=[year],
        training_cutoff=year[4:]+'-06-30', design_sha256='a'*64, inputs=[])}
    sources = {} if data is None else {reference['id']: {} for key, estimate in data.items() if key != 'method_id'
        for reference in (estimate.get('reason_detail') or {}).get('evidence', []) if reference['kind'] == 'source'}
    publication.validate_row('adjustment_decomposition', row, 'spatial', {'method': methods, 'source': sources},
                             {(year, row['player_id']): {'kind': 'skater'}})


for year in ('20232024', '20242025', '20252026'):
    path = ROOT / f'{year}-spatial-adjustment_decomposition.jsonl'
    digest = hashlib.sha256()
    lines = 0
    with path.open('rb') as source:
        for line in source:
            digest.update(line)
            lines += 1
            row = json.loads(line)
            checked += 1
            if row['result']['data'] is None:
                pending += 1
            elif row['result']['data']['factual_prediction']['value'] is not None:
                numeric += 1
            if year == '20252026' and row['player_id'] == '8475718' and row['strength'] == '5v5' and row['target'] == 'against_attempts_per60':
                witness = row
            try:
                validate(row)
            except InputContractError as error:
                saved_failures.append(dict(season=year, line=lines, player_id=row['player_id'], target=row['target'], error=str(error)))
    files.append(dict(path=str(path), sha256=digest.hexdigest(), rows=lines))
assert witness is not None


def control(name, row, refused=False):
    try:
        validate(row)
    except InputContractError as error:
        results.append(dict(case=name, status='passed' if refused else 'red', error=str(error)))
    else:
        results.append(dict(case=name, status='red' if refused else 'passed'))


control('actual saved cancellation witness remains valid', witness)
normal = deepcopy(witness)
normal['player_id'] = '1'
values = dict(baseline=.1, self=.02, teammates=-.01, opponents=.03, coaching_other_context=.01,
              numerical_residual=0., factual_prediction=.15)
for key, value in values.items():
    normal['result']['data'][key]['value'] = value
control('normal unbounded-rate allocation remains valid', normal)
overflow = deepcopy(normal)
for key, value in zip(TERMS, (1e308, 1e308, -1e308, -1e308, 1.), strict=True):
    overflow['result']['data'][key]['value'] = value
overflow['result']['data']['factual_prediction']['value'] = 1.
control('finite inputs reject overflowed arithmetic and tolerance', overflow, refused=True)
tight = deepcopy(normal)
tight['result']['data']['numerical_residual']['value'] = 5e-10
control('normal row rejects residual above exact spec budget despite old close allowance', tight, refused=True)
closed_but_not_roundoff = deepcopy(normal)
closed_but_not_roundoff['result']['data']['numerical_residual']['value'] = 1e-6
closed_but_not_roundoff['result']['data']['factual_prediction']['value'] += 1e-6
control('exactly closing row rejects a non-roundoff residual', closed_but_not_roundoff, refused=True)
invalid = deepcopy(witness)
data = invalid['result']['data']
bound = 1e-10*(1+abs(data['factual_prediction']['value'])+sum(abs(data[key]['value']) for key in TERMS))
data['numerical_residual']['value'] = 2*bound
control('actual witness rejects residual above unchanged spec budget', invalid, refused=True)
results.append(dict(case='all saved adjustment rows validate', status='red' if saved_failures else 'passed',
                    checked=checked, numeric=numeric, pending=pending, failures=saved_failures))
print(json.dumps(dict(scope='saved publication JSONL plus labeled synthetic controls; full validate_row; no model/state/array/source reader or artifact mutation',
    files=files, witness_identity=dict(season=witness['season'], player_id=witness['player_id'], target=witness['target']),
    normal_spec_bound=1e-10*(1+abs(values['factual_prediction'])+sum(abs(values[key]) for key in TERMS)),
    witness_spec_bound=bound, controls=results, passed=sum(row['status']=='passed' for row in results),
    red=sum(row['status']=='red' for row in results)), indent=2))
raise SystemExit(1 if any(row['status']=='red' for row in results) else 0)
