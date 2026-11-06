"""temporary synthetic admission checks against the root-frozen receipt fields.

no saved model/source/publication is read. state and exchange readers, table generation,
strict result reading and the external-output location guard are mocked. the code under
test owns admission, state selection, method construction and ordinary output writing.
"""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from hockey_stats import analysis_cli, spatial_composition as composition, spatial_state, chance_cli
from hockey_stats.captures import InputContractError

YEARS = composition.YEARS
HEADS = ('volume', 'shape', 'quality')
WARNING = ('the original volume precision check failed; this review measures only the saved '
           'baseline/continuation difference; remaining optimizer accuracy is unknown')
CONTEXT_WARNINGS = {
    '20242025': 'synthetic 2024 actual-context allocation limitation; standardized sensitivity is a separate review',
    '20252026': 'synthetic 2025 actual-context allocation limitation; standardized sensitivity is a separate review',
}


def store(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + '\n')
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def exercise(root, purpose, mutation=None, with_receipt=True, expect_refusal=False, before_states=False):
    source = root / 'source'
    source.mkdir()
    prepared, coaches = 'a' * 64, 'b' * 64
    rows, annuals, comparisons = [], {}, {}
    baseline_arrays = object()
    previous = None
    for year in YEARS:
        folder = root / 'states' / year
        support = store(folder / 'coefficient-support.jsonl', {'synthetic': True})
        members = [dict(role='coefficient_support', path='coefficient-support.jsonl', sha256=support['sha256'])]
        probes = None
        if year == YEARS[-1]:
            baseline = store(folder / 'probes' / 'baseline.json', {'synthetic': 'baseline', 'season': year})
            members.append(dict(role='probe_baseline', path='probes/baseline.json', sha256=baseline['sha256']))
            heads = {}
            for head in HEADS:
                status = 'failed' if head == 'volume' else 'passed'
                heads[head] = dict(status=status, failures=['synthetic precision failure'] if status == 'failed' else [])
                reference = store(folder / 'probes' / f'{head}-comparison.json', heads[head])
                comparisons[head] = dict(reference, status=status)
                members.append(dict(role='probe_comparison', path=f'probes/{head}-comparison.json', sha256=reference['sha256']))
            probes = dict(status='failed', heads=heads)
        manifest = dict(season=year, purpose=purpose, prepared={'sha256': prepared}, coaches={'sha256': coaches},
                        valued={'sha256': composition.ACCEPTED_VALUED[year]}, recipe_id='experimental-v1',
                        recipe={'version': 'synthetic'}, basis_identity={'sha256': 'c' * 64},
                        design_identity='d' * 64, training_cutoff=f'{year[4:]}-06-30', previous=previous, files=members)
        reference = store(folder / 'manifest.json', manifest)
        rows.append(dict(season=year, **reference))
        previous = reference
        annuals[year] = SimpleNamespace(path=folder, manifest=manifest,
            heads={head: {'status': 'complete'} for head in HEADS}, probes=probes,
            projections=[], projection_arrays={'rates': baseline_arrays}, adjustments=[])
    selection = store(root / 'selection.json', dict(schema_version=1, purpose=purpose, prepared_sha256=prepared, states=rows))
    policy = store(root / 'policy.json', {'synthetic': 'frozen product policy'})
    consequence = store(root / 'consequence.json', {'status': 'computed_pending_materiality_review', 'synthetic': True})
    review = store(root / 'review.json', {'synthetic': 'independent prose review'})
    context_review = store(root / 'context-review.json', {'synthetic': 'actual-context diagnosis'})
    receipt = dict(schema_version=2, kind='spatial_private_experimental_admission', purpose='real',
        decision='admit_saved_baseline', season=YEARS[-1], selection=selection, baseline=baseline,
        original_precision={'status': 'failed', 'comparisons': comparisons}, policy=policy,
        consequence_result=consequence, consequence_review=review, optimizer_accuracy='unknown', content_warning=WARNING,
        actual_context_review=context_review, actual_context_warnings=dict(CONTEXT_WARNINGS))
    if mutation is not None:
        mutation(receipt)
    admission = store(root / 'admission.json', receipt)
    catalogs = {name: store(source / f'{name}.jsonl', {}) for name in ('people', 'sources', 'supports')}
    for member in catalogs.values():
        member['path'] = Path(member['path']).name
        member['rows'] = 1
    manifest = dict(purpose=purpose, prepared_sha256=prepared, seasons=list(YEARS[-3:]), catalogs=catalogs,
        families=[dict(season=year, family='spatial', availability='not_computed', tables={}) for year in YEARS[-3:]])
    store(source / 'manifest.json', manifest)
    methods = {f'execution-v1-06-{year}': dict(method_id=f'execution-v1-06-{year}',
        evidence=[{'sha256': composition.ACCEPTED_VALUED[year]}], inputs=[{'role': 'coaches', 'sha256': coaches}]) for year in YEARS[-3:]}
    existing = SimpleNamespace(directory=source, manifest=manifest, people={}, catalogs={'method': methods})
    output = root / 'output'
    reads, selected_paths = [], []

    def read_state(path, requested):
        assert requested == purpose
        reads.append(Path(path))
        return annuals[Path(path).parent.name]

    def tables(year, state, people, method):
        assert state.path == annuals[year].path, 'baseline state path was replaced'
        assert state.projection_arrays['rates'] is baseline_arrays, 'baseline projections were replaced'
        selected_paths.append(str(state.path))
        return {name: iter(()) for name in ('skater_spatial', 'analysis_map', 'adjustment_decomposition')}

    with ExitStack() as stack:
        stack.enter_context(patch.object(composition.publication, 'read_results', return_value=existing))
        stack.enter_context(patch.object(composition, '_accepted_source', return_value=None))
        stack.enter_context(patch.object(spatial_state, 'read_spatial_state', side_effect=read_state))
        stack.enter_context(patch.object(composition, '_season_tables', side_effect=tables))
        stack.enter_context(patch.object(composition.publication, '_read_results', return_value=None))
        stack.enter_context(patch.object(composition, 'implementation_identity', return_value={'synthetic': True}))
        stack.enter_context(patch.object(chance_cli, 'output_path', return_value=output))
        stack.enter_context(patch.object(Path, 'is_relative_to', return_value=True))
        arguments = {'product_admission': Path(admission['path'])} if with_receipt else {}
        try:
            composition.compose_results(source, Path(selection['path']), output, **arguments)
        except InputContractError as error:
            assert expect_refusal, f'valid input was refused: {error}'
            assert not output.exists(), 'refusal created output'
            assert not before_states or not reads, 'refusal occurred after state reads'
            return
        assert not expect_refusal, 'invalid/missing admission was accepted'

    published = [json.loads(line) for line in (output / 'methods.jsonl').read_text().splitlines()]
    spatial = {row['method_id']: row for row in published if row.get('family') == 'spatial'}
    assert selected_paths == [str(annuals[year].path) for year in YEARS[-3:]]
    for year in YEARS[-3:]:
        method = spatial[f'spatial-v1-08-{year}']
        composition.publication.validate_catalog('methods', method, purpose, {}, prepared)
        affected = purpose == 'real' and year == YEARS[-1]
        contextual = purpose == 'real' and year in CONTEXT_WARNINGS
        assert (WARNING in method['limitations']) == affected, 'warning missing or leaked to another year/purpose'
        for warning_year, warning in CONTEXT_WARNINGS.items():
            assert (warning in method['limitations']) == (contextual and year == warning_year), 'context warning missing or leaked'
            assert warning not in method['assessment']['findings'][0]['summary'], 'context warning attached to standardized quantities'
        evidence = method['evidence']
        assert len(evidence) == ({'20232024': 3, '20242025': 5, '20252026': 13}[year] if purpose == 'real' else 3)
        assert any(item['uri'] == str(annuals[year].path / 'manifest.json') for item in evidence)
        assert sum(item['uri'] == admission['path'] and item['sha256'] == admission['sha256'] for item in evidence) == int(contextual)
        assert sum(item['uri'] == context_review['path'] and item['sha256'] == context_review['sha256'] for item in evidence) == int(contextual)
        assert len(method['assessment']['findings']) == (2 if contextual else 1)
        assert len(method['assessment']['findings'][0]['evidence']) == (12 if affected else 3)
        assert (WARNING in method['assessment']['findings'][0]['summary']) == affected
        if contextual:
            finding = method['assessment']['findings'][1]
            assert finding['summary'] == CONTEXT_WARNINGS[year]
            assert set(finding['quantities']) == {f'adjustment_decomposition.{name}' for name in
                ('baseline', 'self', 'teammates', 'opponents', 'coaching_other_context', 'numerical_residual', 'factual_prediction')}
            assert finding['evidence'] == [dict(uri=reference['path'], sha256=reference['sha256']) for reference in (admission, context_review)]
        if affected:
            assert method['assessment']['status'] == 'experimental'
            assert any(item['uri'] == admission['path'] for finding in method['assessment']['findings'] for item in finding['evidence'])
            for reference in (policy, consequence, review, *comparisons.values()):
                assert any(item['uri'] == reference['path'] and item['sha256'] == reference['sha256'] for item in evidence)


def alter_path(receipt):
    receipt['baseline']['path'] = str(Path(receipt['baseline']['path']).parent / 'continuation.json')


def old_receipt(receipt):
    receipt['schema_version'] = 1
    del receipt['actual_context_review']
    del receipt['actual_context_warnings']


cases = (
    ('real receipt required before state reads', 'real', None, False, True, True),
    ('fixture rejects real receipt before state reads', 'fixture', None, True, True, True),
    ('fixture existing contract survives', 'fixture', None, False, False, False),
    ('explicit baseline admission with final-year evidence', 'real', None, True, False, False),
    ('old receipt schema refused', 'real', old_receipt, True, True, True),
    ('missing context review refused', 'real', lambda r: r.pop('actual_context_review'), True, True, True),
    ('missing context warning year refused', 'real', lambda r: r['actual_context_warnings'].pop('20242025'), True, True, True),
    ('blank context warning refused', 'real', lambda r: r['actual_context_warnings'].update({'20252026': ' '}), True, True, True),
    ('context review digest mismatch refused', 'real', lambda r: r['actual_context_review'].update(sha256='0' * 64), True, True, True),
    ('non-admission decision refused', 'real', lambda r: r.update(decision='deny_saved_baseline'), True, True, True),
    ('selection digest mismatch refused', 'real', lambda r: r['selection'].update(sha256='0' * 64), True, True, True),
    ('policy digest mismatch refused', 'real', lambda r: r['policy'].update(sha256='0' * 64), True, True, True),
    ('review digest mismatch refused', 'real', lambda r: r['consequence_review'].update(sha256='0' * 64), True, True, True),
    ('comparison digest mismatch refused', 'real', lambda r: r['original_precision']['comparisons']['volume'].update(sha256='0' * 64), True, True, False),
    ('comparison status mismatch refused', 'real', lambda r: r['original_precision']['comparisons']['volume'].update(status='passed'), True, True, False),
    ('aggregate precision status mismatch refused', 'real', lambda r: r['original_precision'].update(status='passed'), True, True, False),
    ('continuation cannot replace baseline', 'real', alter_path, True, True, False),
)
results = []
for name, purpose, mutation, with_receipt, refusal, early in cases:
    with tempfile.TemporaryDirectory(prefix='spatial-admission-synthetic-') as temporary:
        try:
            exercise(Path(temporary), purpose, mutation, with_receipt, refusal, early)
        except Exception as error:
            results.append(dict(case=name, status='red', error=f'{type(error).__name__}: {error}'))
        else:
            results.append(dict(case=name, status='passed'))

try:
    with patch.object(composition, 'compose_results', return_value={'purpose': 'real'}) as compose:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = analysis_cli.main(['summarize', '--family', 'spatial', '--results', '/synthetic/results',
                '--states', '/synthetic/selection.json', '--product-admission', '/synthetic/admission.json', '--out', '/synthetic/output'])
        assert result == 0
        assert compose.call_count == 1
        assert compose.call_args.kwargs == {'product_admission': Path('/synthetic/admission.json')}
except (Exception, SystemExit) as error:
    results.append(dict(case='cli forwards explicit receipt without opening inputs', status='red', error=f'{type(error).__name__}: {error}'))
else:
    results.append(dict(case='cli forwards explicit receipt without opening inputs', status='passed'))

try:
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        try:
            analysis_cli.main(['summarize', '--family', 'execution', '--prepared', '/synthetic/prepared',
                '--facts', '/synthetic/facts', '--scores', '/synthetic/scores', '--product-admission', '/synthetic/admission.json', '--out', '/synthetic/output'])
        except SystemExit as error:
            assert error.code == 2
        else:
            raise AssertionError('execution summarize accepted a spatial admission flag')
except Exception as error:
    results.append(dict(case='cli rejects receipt for execution', status='red', error=f'{type(error).__name__}: {error}'))
else:
    results.append(dict(case='cli rejects receipt for execution', status='passed'))
print(json.dumps(dict(scope='synthetic only; root-frozen receipt shape; no actual saved data or scientific verdict',
    cases=results, passed=sum(row['status'] == 'passed' for row in results), red=sum(row['status'] == 'red' for row in results)), indent=2))
raise SystemExit(1 if any(row['status'] == 'red' for row in results) else 0)
