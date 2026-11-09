"""read only six saved jsonl files; no package/model/array/source reader imports."""
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path

ROOT = Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real')
TERMS = ('baseline', 'self', 'teammates', 'opponents', 'coaching_other_context')
KEYS = TERMS + ('numerical_residual', 'factual_prediction')
RENAME = dict(numerical_residual='residual', factual_prediction='factual')
files = []


def rows(path):
    digest = hashlib.sha256()
    count = 0
    with path.open('rb') as source:
        for line in source:
            digest.update(line)
            count += 1
            yield count, json.loads(line)
    files.append(dict(path=str(path), sha256=digest.hexdigest(), rows=count))


def close(a, b):
    return math.isfinite(a) and math.isfinite(b) and abs(a-b) <= 1e-9 + 1e-9*max(abs(a), abs(b))


report = []
for season in ('20232024', '20242025', '20252026'):
    canonical_path = ROOT / 'spatial' / season / 'adjustments.jsonl'
    canonical = {(row['player_id'], row['role']): row for _, row in rows(canonical_path)}
    path = ROOT / 'results' / f'{season}-spatial-adjustment_decomposition.jsonl'
    failures, mismatches, unavailable = [], [], 0
    checked = 0
    maxima = dict(closure_error=0., closure_over_spec_bound=0., residual_expression_error=0.,
                  residual_expression_over_current_bound=0., absolute_residual=0.)
    for line, row in rows(path):
        if row['strength'] != '5v5':
            continue
        assert row['result']['availability'] == 'provided'
        values = {key: row['result']['data'][key]['value'] for key in KEYS}
        direction, quantity, _ = row['target'].split('_', 2)
        role = 'offense' if direction == 'for' else 'defense'
        saved = canonical.get((row['player_id'], role))
        expected = {key: saved[quantity][RENAME.get(key, key)] if saved is not None else None for key in KEYS}
        if values != expected:
            mismatches.append(dict(line=line, player_id=row['player_id'], target=row['target'], values=values, expected=expected))
        if any(value is None for value in values.values()):
            unavailable += 1
            continue
        checked += 1
        terms = [values[key] for key in TERMS]
        residual, factual = values['numerical_residual'], values['factual_prediction']
        unadjusted = sum(terms)
        total = sum(terms + [residual])
        closure_error = abs(total-factual)
        expression_error = abs(residual-(factual-unadjusted))
        expression_bound = 1e-9+1e-9*max(abs(residual), abs(factual-unadjusted))
        magnitude_bound = 1e-9+1e-9*max(abs(unadjusted), abs(factual))
        spec_bound = 1e-10*(1+abs(factual)+sum(abs(value) for value in terms+[residual]))
        first = close(total, factual)
        second = close(residual, factual-unadjusted)
        third = abs(residual) <= magnitude_bound
        measures = dict(closure_error=closure_error, closure_over_spec_bound=closure_error/spec_bound,
            residual_expression_error=expression_error, residual_expression_over_current_bound=expression_error/expression_bound,
            absolute_residual=abs(residual))
        for key, value in measures.items():
            maxima[key] = max(maxima[key], value)
        if not (first and second and third) or closure_error > spec_bound:
            with localcontext() as context:
                context.prec = 80
                decimal_terms = [Decimal.from_float(value) for value in terms]
                decimal_sum = sum(decimal_terms)
                decimal_error = Decimal.from_float(residual)-(Decimal.from_float(factual)-decimal_sum)
            failures.append(dict(line=line, player_id=row['player_id'], target=row['target'], values=values,
                canonical_scalar_exact=values == expected,
                current_checks=dict(closure=first, residual_expression=second, residual_magnitude=third),
                unadjusted_sum=unadjusted, total_sum=total, fsum_unadjusted=math.fsum(terms),
                fsum_total=math.fsum(terms+[residual]), factual_minus_sum=factual-unadjusted,
                factual_minus_fsum=factual-math.fsum(terms), closure_error=closure_error,
                current_closure_bound=1e-9+1e-9*max(abs(total),abs(factual)),
                residual_expression_error=expression_error, current_residual_expression_bound=expression_bound,
                current_residual_magnitude_bound=magnitude_bound, spec_closure_bound=spec_bound,
                spec_closure_pass=closure_error <= spec_bound,
                decimal_exact_float_unadjusted_sum=str(decimal_sum), decimal_exact_float_residual_expression_error=str(decimal_error)))
    report.append(dict(season=season, numeric_rows=checked, unavailable_rows=unavailable,
        publication_canonical_scalar_mismatch_count=len(mismatches), mismatches=mismatches,
        failed_rows=len(failures), current_failed_rows=sum(not all(row['current_checks'].values()) for row in failures),
        spec_failed_rows=sum(not row['spec_closure_pass'] for row in failures), maxima=maxima, failures=failures))

print(json.dumps(dict(scope='saved scalar jsonl only; no arrays/model/state/source/fit readers; no output mutation',
    files=files, seasons=report), indent=2, allow_nan=False))
