"""compose saved positive 5v5 projections without rebuilding other families."""

from copy import deepcopy
from dataclasses import dataclass
import hashlib
from pathlib import Path
from time import perf_counter

from . import analysis_publication as publication
from .artifacts import implementation_identity, require, write_json
from .captures import strict_json
from .chance_cli import identity
from .descriptive import estimate

YEARS = ('20212022', '20222023', '20232024', '20242025', '20252026')
REFERENCE = 'spatial-league-centered-virtual-v1'
POLICY = 'ordinary-attempt-segment-valued-two-direction-v1'
ACCEPTED_RESULTS = Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution-results')
ACCEPTED_RESULTS_SHA256 = '3441f784c11eb6a8eda38800806b8e4dc68e06e8587c91db24c5dffaadae4347'
ACCEPTED_VALUED = dict(zip(YEARS, (
    '37263bfc650a06f09adc2c64588c19d3b61cd1e9cdb65dc2ba71a8f88ed5ca8d',
    '296ae0173fb1256ddb91d14eee5a917d76c3e88f92cc3556a8647b1f10a8da20',
    'f13a1136c3df857a83d9f37aa10b919b64934e240515c3a8d5e2c556a778b238',
    '86e346f82d874748215f582c1a4445ab75b01358dd61d37fa4082254879c62de',
    '40e23b35ac9c8458229b076150366960c4a25d7a92ae028d2b45dc39c89104fc',
)))


@dataclass(frozen=True)
class _AnnualProjection:
    path: Path
    manifest: dict
    projections: list
    projection_arrays: dict
    adjustments: list



def _accepted_source(results):
    """the accepted exchange pins facts; independently added families may survive."""
    if results.manifest['purpose'] != 'real':
        return
    path = ACCEPTED_RESULTS / 'manifest.json'
    require(identity(path)['sha256'] == ACCEPTED_RESULTS_SHA256, 'accepted v1-06 result manifest digest differs')
    accepted = strict_json(path.read_bytes())
    for key in ('purpose', 'seasons', 'observed_bindings', 'prepared_sha256'):
        require(results.manifest[key] == accepted[key], f'accepted v1-06 {key} differs')
    for name in ('people', 'sources'):
        require(results.manifest['catalogs'][name] == accepted['catalogs'][name], f'accepted v1-06 {name} differ')
    inherited = {(row['season'], row['family']): row for row in results.manifest['families']}
    for row in accepted['families']:
        if row['family'] != 'spatial' and row['availability'] == 'provided':
            require(inherited[row['season'], row['family']] == row, f'accepted v1-06 {row["family"]} differs')
    for name, catalog, key in (('methods', 'method', 'method_id'), ('supports', 'support', 'support_id')):
        member = accepted['catalogs'][name]
        source = publication.member_path(ACCEPTED_RESULTS, member)
        require(identity(source)['sha256'] == member['sha256'], f'accepted v1-06 {name} digest differs')
        with source.open('rb') as stream:
            for line in stream:
                row = strict_json(line)
                require(results.catalogs[catalog].get(row[key]) == row, f'accepted v1-06 {key} differs')


def _product_admission(path, selection_path, purpose):
    """validate the study's explicit use decision and bound evidence, not its judgment."""
    require((path is not None) == (purpose == 'real'),
            'real spatial composition requires --product-admission; fixture composition forbids it')
    if path is None:
        return None
    path = Path(path).absolute()
    document = strict_json(path.read_bytes())
    publication.fields(document, ('schema_version', 'kind', 'purpose', 'decision', 'season', 'selection', 'baseline',
        'original_precision', 'policy', 'consequence_result', 'consequence_review', 'optimizer_accuracy', 'content_warning'))
    require(type(document['schema_version']) is int and document['schema_version'] == 1
            and document['kind'] == 'spatial_private_experimental_admission' and document['purpose'] == 'real'
            and document['decision'] == 'admit_saved_baseline' and document['season'] == YEARS[-1]
            and document['optimizer_accuracy'] == 'unknown', 'invalid spatial product admission')
    publication.text(document['content_warning'])
    precision = document['original_precision']
    publication.fields(precision, ('status', 'comparisons'))
    publication.fields(precision['comparisons'], ('volume', 'shape', 'quality'))
    require(precision['status'] in ('passed', 'failed'), 'invalid original spatial precision status')
    evidence = [dict(uri=str(path), sha256=identity(path)['sha256'])]
    for name in ('selection', 'baseline', 'policy', 'consequence_result', 'consequence_review', 'volume', 'shape', 'quality'):
        reference = precision['comparisons'][name] if name in precision['comparisons'] else document[name]
        publication.fields(reference, ('path', 'sha256', 'status') if name in precision['comparisons'] else ('path', 'sha256'))
        publication.digest(reference['sha256'])
        require(type(reference['path']) is str and Path(reference['path']).is_absolute(), 'spatial admission reference must be absolute')
        target = Path(reference['path'])
        require(target.is_file() and identity(target)['sha256'] == reference['sha256'], 'spatial admission evidence digest differs')
        if name in precision['comparisons']:
            require(reference['status'] in ('passed', 'failed'), 'invalid original spatial head precision status')
        evidence.append(dict(uri=reference['path'], sha256=reference['sha256']))
    require(document['selection'] == identity(Path(selection_path).absolute()), 'spatial admission selection differs')
    require(precision['status'] == ('passed' if all(r['status'] == 'passed' for r in precision['comparisons'].values()) else 'failed'),
            'original spatial aggregate precision status differs')
    return dict(season=document['season'], warning=document['content_warning'], baseline=document['baseline'],
                precision=precision, evidence=evidence)


def _states(selection_path, results, admission=None):
    from .spatial_state import read_spatial_state

    selection = strict_json(Path(selection_path).read_bytes())
    require((admission is not None) == (results.manifest['purpose'] == 'real'), 'spatial product admission purpose differs')
    publication.fields(selection, ('schema_version', 'purpose', 'prepared_sha256', 'states'))
    require(type(selection['schema_version']) is int and selection['schema_version'] == 1
            and selection['purpose'] == results.manifest['purpose']
            and selection['prepared_sha256'] == results.manifest['prepared_sha256'], 'spatial selection purpose/preparation differs')
    require(type(selection['states']) is list and selection['states'], 'missing spatial states')
    annuals, years = {}, []
    for item in selection['states']:
        publication.fields(item, ('season', 'path', 'sha256'))
        publication.digest(item['sha256'])
        require(item['season'] in YEARS and type(item['path']) is str and Path(item['path']).is_absolute(), 'invalid spatial annual selection')
        path = Path(item['path'])
        path = path / 'manifest.json' if path.is_dir() else path
        require(identity(path)['sha256'] == item['sha256'], 'spatial annual manifest digest differs')
        state = read_spatial_state(path, selection['purpose'])
        manifest = state.manifest
        require(manifest['season'] == item['season'] and manifest['prepared']['sha256'] == selection['prepared_sha256'], 'spatial annual season/preparation differs')
        require(all(state.heads[head]['status'] == 'complete' for head in ('volume', 'shape', 'quality')), 'selected spatial annual family is incomplete')
        if selection['purpose'] == 'real':
            require(manifest['valued']['sha256'] == ACCEPTED_VALUED[item['season']], 'spatial target is not the accepted v1-06 score')
            if item['season'] == YEARS[-1]:
                probes = state.probes
                require(probes is not None and set(probes['heads']) == {'volume', 'shape', 'quality'}, 'final real spatial numerical probes are incomplete')
                members = {member['path']: member for member in manifest['files']}
                for name, reference in [('baseline', admission['baseline']), *admission['precision']['comparisons'].items()]:
                    member = 'probes/baseline.json' if name == 'baseline' else f'probes/{name}-comparison.json'
                    require(member in members and reference['path'] == str(state.path / member)
                            and reference['sha256'] == members[member]['sha256'], 'spatial admission probe binding differs')
                    if name != 'baseline':
                        require(reference['status'] == probes['heads'][name]['status'], 'spatial admission original head status differs')
                require(admission['precision']['status'] == probes['status'], 'spatial admission original precision status differs')
            else:
                require(state.probes is None, 'earlier real spatial year has an unexpected numerical probe')
        years.append(item['season'])
        display = item['season'] in results.manifest['seasons']
        annuals[item['season']] = _AnnualProjection(state.path, manifest,
            state.projections if display else [], state.projection_arrays if display else {},
            state.adjustments if display else [])
        # the detached reader checked the design and heads; publication only
        # retains their saved projections. release each design before the next.
        del state
    require(years == sorted(set(years)) and years == list(YEARS[YEARS.index(years[0]):YEARS.index(years[-1]) + 1]), 'spatial states must be unique ordered consecutive years')
    require(selection['purpose'] != 'real' or years == list(YEARS), 'real spatial composition requires all five years')
    require(set(results.manifest['seasons']) <= set(years), 'spatial selection omits a displayed year')
    require(annuals[years[0]].manifest['previous'] is None, 'first selected spatial year has undeclared history')
    for left, right in zip(years, years[1:]):
        before, after = annuals[left], annuals[right]
        previous = after.manifest['previous']
        require(previous is not None and previous['sha256'] == identity(before.path / 'manifest.json')['sha256']
                and Path(previous['path']).resolve() == (before.path / 'manifest.json').resolve(), 'spatial state history chain differs')
        require(all(after.manifest[key] == before.manifest[key] for key in ('recipe_id', 'recipe', 'basis_identity')), 'spatial recipe/basis differs between years')
        require(all(after.manifest[key]['sha256'] == before.manifest[key]['sha256'] for key in ('prepared', 'coaches')), 'spatial preparation/coaches differ between years')
    for year in results.manifest['seasons']:
        method = results.catalogs['method'].get(f'execution-v1-06-{year}')
        state = annuals[year]
        require(method is not None and any(r['sha256'] == state.manifest['valued']['sha256'] for r in method['evidence']), 'spatial target is not bound to published execution')
        require(any(r['role'] == 'coaches' and r['sha256'] == state.manifest['coaches']['sha256'] for r in method['inputs']), 'spatial/published execution coaches differ')
    return selection, annuals


def _datum(value, method, person, *, reason=None):
    why = 'failed_fit' if reason == 'incomplete_annual_family' else 'no_exposure' if reason == 'no_exposure' else 'missing_source'
    result = estimate(value, reason=why, explanation=reason or 'saved spatial projection unavailable for this published skater')
    if value is None:
        result['reason_detail']['evidence'] = [dict(kind='method', id=method), *person['source']]
    return result


def _method(year, state, annuals, results, source_sha, receipt, admission=None):
    manifest = state.manifest
    years = [y for y in annuals if y <= year]
    inputs = [dict(role='prepared', sha256=manifest['prepared']['sha256'], seasons=years),
              dict(role='coaches', sha256=manifest['coaches']['sha256'], seasons=years),
              dict(role='opportunity_panel', sha256=manifest['valued']['sha256'], seasons=[year]),
              dict(role='source_results', sha256=source_sha, seasons=[year]),
              *[dict(role='annual_state', sha256=identity(annuals[y].path / 'manifest.json')['sha256'], seasons=[y]) for y in years]]
    support_file = next(r for r in manifest['files'] if r['role'] == 'coefficient_support')
    evidence = [dict(uri=str(state.path / 'manifest.json'), sha256=identity(state.path / 'manifest.json')['sha256']),
                dict(uri=str(state.path / support_file['path']), sha256=support_file['sha256']), receipt]
    warning = []
    if admission is not None and year == admission['season']:
        evidence.extend(admission['evidence'])
        warning.append(admission['warning'])
    return dict(method_id=f'spatial-v1-08-{year}', family='spatial', recipe_id=manifest['recipe_id'] + ':' + manifest['recipe']['version'],
                design_sha256=manifest['design_identity'], input_sha256=hashlib.sha256(publication.json_bytes(inputs)).hexdigest(),
                fit_seasons=years, training_cutoff=manifest['training_cutoff'],
                target='positive 5v5 attempt and neutral-execution chance rate differences',
                population='common matched ordinary 5v5 elapsed membership and physical attempts; both goalies present',
                reference='frozen hypothetical league-centered design; five neutral slots per role, centered context, exposure-mean coach applicability and virtual neutral execution; insert one focal player jointly in all three heads',
                limitations=['experimental conditional seasonal estimates; not causal effects, calibrated ability claims or held-out forecasts',
                             'historical point borrowing and inferred blocked origins omit history and origin uncertainty; calibrated intervals are not estimated',
                             'defensive positive differences mean more against; higher percentiles mean higher rates, not greater benefit',
                             'aggregate support is the common matched physical-time population and any contributing focal information; it does not establish current evidence for each volume, shape or quality term',
                             'spatial support reason counts are games with a located excluded segment, counted once per reason code; codes can overlap within a game',
                             'head support is saved in the bound receipt; structured head and actual-context adjustment presentation remain separate work', *warning],
                evidence=evidence, purpose=results.manifest['purpose'], inputs=inputs, reference_id=REFERENCE, support_policy_id=POLICY,
                assessment=dict(status='experimental', findings=[dict(quantities=[f'skater_spatial.{field}' for field in publication.ESTIMATE_FIELDS['skater_spatial']],
                    population='matched current-season 5v5 and fixed historical conditional priors',
                    summary='; '.join(['experimental point estimates with aggregate qualification only; predictive calibration, recovery, causal isolation and calibrated uncertainty are not established', *warning]), evidence=evidence)]))


def _season_tables(year, state, people, method):
    from .observed_spatial import cells

    projections = {r['player_id']: (i, r) for i, r in enumerate(state.projections)}
    adjustments = {(r['player_id'], r['role']): r for r in state.adjustments}
    unknown_support = dict(included_seconds=None, events=None, eligible_weight=None, known_excluded_seconds=None,
                           unquantified_gap=True, reason_counts=[],
                           inferred_inputs=[], current_season_information=False, prior_only=False, prior_seasons=[])
    display_shapes = cells()
    pending = dict(availability='not_computed', explanation='special-team spatial estimation awaits v1-09', data=None)

    def payload(person):
        selected = projections.get(person['player_id'])
        projection = selected[1] if selected else None
        reason = projection['reason'] if projection else 'published skater has no saved prepared-roster coefficient; no neutral substitution'
        values = {}
        for role in ('offense', 'defense'):
            for quantity in ('attempts', 'xg'):
                saved = projection['values'][role][quantity] if projection else dict.fromkeys(('difference', 'complete', 'neutral', 'relative_percent'))
                for key, suffix in (('difference', 'per60'), ('complete', 'per60_complete'), ('neutral', 'per60_neutral'), ('relative_percent', 'relative_percent')):
                    values[f'{role}_{quantity}_{suffix}'] = _datum(saved[key], method, person, reason=reason)
        return values | dict(state_weights=[dict(strength='5v5', weight=1.)], support=projection['support'] if projection else unknown_support, method_id=method)

    def scalars():
        for person in people:
            for (strength,) in sorted(publication.required_keys('skater_spatial', 'spatial')):
                yield dict(season=year, player_id=person['player_id'], strength=strength,
                           result=dict(availability='provided', explanation=None, data=payload(person)) if strength == '5v5' else pending)

    def maps():
        for person in people:
            data = payload(person)
            selected = projections.get(person['player_id'])
            for kind, strength, view in sorted(publication.required_keys('analysis_map', 'spatial')):
                if strength != '5v5':
                    result = pending
                else:
                    role, quantity = kind.split('_')
                    field = f'{kind}_per60' + ('_complete' if view == 'complete' else '')
                    value = data[field]
                    native = None
                    if selected and selected[1]['available']:
                        native = state.projection_arrays['rates'][selected[0], ('offense', 'defense').index(role), ('attempts', 'xg').index(quantity), 1 if view == 'complete' else 2]
                    require((native is None) == (value['value'] is None), 'spatial map/scalar availability differs')
                    display = None
                    if native is not None:
                        transported = publication.native_display_mass(native)
                        display = [dict(cell_id=c['cell_id'], mass=float(m), density_per100sqft=float(100*m/c['area_sqft'])) for c, m in zip(display_shapes, transported, strict=True)]
                    result = dict(availability='provided', explanation=None, data=dict(grid_id='native656', unit='attempts_per60' if quantity == 'attempts' else 'xg_per60', reference=REFERENCE,
                        cells=None if native is None else [dict(cell_id=i, value=float(v)) for i, v in enumerate(native)], display_cells=display,
                        integrated_value=value['value'], unavailable_reason=value['unavailable_reason'], reason_detail=value['reason_detail'], support=data['support'], method_id=method))
                yield dict(season=year, player_id=person['player_id'], map_kind=kind, strength=strength, view=view, result=result)

    def decomposition():
        for person in people:
            for strength, target in sorted(publication.required_keys('adjustment_decomposition', 'spatial')):
                if strength != '5v5':
                    result = pending
                else:
                    direction, quantity, _ = target.split('_', 2)
                    row = adjustments.get((person['player_id'], 'offense' if direction == 'for' else 'defense'))
                    saved = row[quantity] if row else {}
                    reason = row['reason'] if row else 'published skater has no saved actual-context projection'
                    values = {public: _datum(saved.get(native), method, person, reason=reason)
                              for public, native in (('baseline', 'baseline'), ('self', 'self'), ('teammates', 'teammates'), ('opponents', 'opponents'),
                                                     ('coaching_other_context', 'coaching_other_context'), ('numerical_residual', 'residual'), ('factual_prediction', 'factual'))}
                    result = dict(availability='provided', explanation=None, data=values | dict(method_id=method))
                yield dict(season=year, player_id=person['player_id'], strength=strength, target=target, result=result)
    return dict(skater_spatial=scalars(), analysis_map=maps(), adjustment_decomposition=decomposition())


def compose_results(existing_results, state_selection, output, *, product_admission=None):
    """copy checked inherited bytes, write owned rows, then strict-read one exchange."""
    from .chance_cli import output_path

    started = perf_counter()
    existing = publication.read_results(Path(existing_results))
    admission = _product_admission(product_admission, state_selection, existing.manifest['purpose'])
    _accepted_source(existing)
    selection, annuals = _states(state_selection, existing, admission)
    for record in existing.manifest['families']:
        if record['family'] == 'spatial' and record['availability'] == 'provided':
            require(all(row['result']['availability'] == 'not_computed'
                        for table, member in record['tables'].items()
                        for row in existing.rows(member, table, 'spatial')), 'source spatial family is already computed')
    output = output_path(str(output), [str(existing.directory), *[str(s.path) for s in annuals.values()]])
    if existing.manifest['purpose'] == 'real':
        require(output.is_relative_to('/Volumes/Expansion/hockey-stats'), 'expensive real outputs must be external')
    output.mkdir()
    manifest = deepcopy(existing.manifest)
    manifest['producer'] = implementation_identity()
    source_sha = identity(existing.directory / 'manifest.json')['sha256']
    methods = dict(existing.catalogs['method'])

    def copy_member(member):
        source = publication.member_path(existing.directory, member)
        destination = output / member['path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        with source.open('rb') as src, destination.open('xb') as dest:
            while chunk := src.read(1024 * 1024):
                digest.update(chunk)
                dest.write(chunk)
        require(digest.hexdigest() == member['sha256'], 'inherited member digest differs during copy')

    def write_member(path, rows, table):
        sha = hashlib.sha256()
        previous, count = None, 0
        with (output / path).open('xb') as stream:
            for row in rows:
                key = tuple(row[k] for k in publication.KEYS[table])
                require(previous is None or previous < key, 'spatial producer rows must be sorted and unique')
                encoded = publication.json_bytes(row) + b'\n'
                stream.write(encoded)
                sha.update(encoded)
                previous, count = key, count + 1
        return dict(path=path, sha256=sha.hexdigest(), rows=count)

    for record in manifest['families']:
        if record['family'] != 'spatial':
            for member in record['tables'].values():
                copy_member(member)
            continue
        year = record['season']
        state = annuals[year]
        people = sorted((p for (season, _), p in existing.people.items() if season == year and p['kind'] == 'skater'), key=lambda p: p['player_id'])
        published, fitted = {p['player_id'] for p in people}, {r['player_id'] for r in state.projections}
        receipt = dict(season=year, source_results=dict(path=str(existing.directory / 'manifest.json'), sha256=source_sha),
                       state=dict(path=str(state.path / 'manifest.json'), sha256=identity(state.path / 'manifest.json')['sha256']),
                       intersection=sorted(published & fitted), published_only=sorted(published - fitted), fitted_only=sorted(fitted - published),
                       missing_projection='every required published skater is emitted; absence retains a located unavailable reason, never a neutral player')
        receipt_path = output / f'{year}-spatial-composition.json'
        write_json(receipt_path, receipt)
        method = _method(year, state, annuals, existing, source_sha, dict(uri=str(receipt_path), sha256=identity(receipt_path)['sha256']), admission)
        require(method['method_id'] not in methods, 'spatial method identity already exists')
        methods[method['method_id']] = method
        tables = _season_tables(year, state, people, method['method_id'])
        record.update(availability='provided', explanation=None, tables={table: write_member(f'{year}-spatial-{table}.jsonl', rows, table) for table, rows in tables.items()})
    for name in ('people', 'sources', 'supports'):
        copy_member(manifest['catalogs'][name])
    manifest['catalogs']['methods'] = write_member('methods.jsonl', sorted(methods.values(), key=lambda row: row['method_id']), 'methods')
    write_json(output / 'manifest.json.incomplete', manifest)
    read_started = perf_counter()
    publication._read_results(output, 'manifest.json.incomplete')
    strict_read_seconds = perf_counter() - read_started
    (output / 'manifest.json.incomplete').rename(output / 'manifest.json')
    write_json(output / 'composition-resources.json', dict(wall_seconds=perf_counter() - started, strict_read_wall_seconds=strict_read_seconds,
               inherited_files='streamed byte for byte; no non-spatial reserialization or source reconstruction',
               state_selection=dict(path=str(Path(state_selection).resolve()), sha256=identity(state_selection)['sha256']),
               output_member_bytes=sum((output / member['path']).stat().st_size
                                       for member in [*manifest['catalogs'].values(),
                                                      *(member for record in manifest['families'] for member in record['tables'].values())])))
    return manifest
