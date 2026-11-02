"""held saved exchange copy/accounting check; no strict, source or array replay."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from itertools import groupby, zip_longest
import json
import math
from pathlib import Path
import re
import resource
from time import perf_counter

from hockey_stats.analysis_publication import EXECUTION_STRENGTHS, KEYS

WORK = Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
CAMPAIGN = Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real')
OUTPUT = CAMPAIGN / 'execution-results'
FACTS = Path('/Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/facts-04')
OBSERVED = FACTS.parent / 'observed-selection.json'
FACTS_SHA = '786b2899b72347e2cbbdb89d24d01e174abf8923fc07e07649fc2bcfdf1967eb'
OBSERVED_SHA = '5b6e3f0b8ae736260070549677a59bbf648ebab9a916729333eeb577611331e9'
PREPARED = '63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c'
COACHES = '102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0'
RECIPE = '47691110ac34bf7d63cdc32664335bd6579a5953545f0cefa8ebf0257bf88674'
VALUED = {'neutral_all_attempt_value', 'neutral_locatable_unblocked_value'}
FIELDS = ('finishing_goals_per100_attempts', 'setting_goals_per100_assisted_opportunities',
          'avoid_block_probability', 'on_net_probability', 'recorded_stop_probability', 'conversion_probability',
          'avoid_block_probability_difference', 'on_net_probability_difference',
          'recorded_stop_probability_difference', 'conversion_probability_difference')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def identity(path):
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def read(path):
    return json.loads(path.read_bytes())


def rows(root, member):
    hashed, count = hashlib.sha256(), 0
    with (root / member['path']).open('rb') as stream:
        for line in stream:
            hashed.update(line)
            count += 1
            yield json.loads(line)
    assert hashed.hexdigest() == member['sha256']
    assert 'rows' not in member or count == member['rows']


def paired(left, right):
    absent = object()
    for before, after in zip_longest(left, right, fillvalue=absent):
        assert before is not absent and after is not absent
        yield before, after


def table(manifest, year, family, name):
    return next(row for row in manifest['families'] if (row['season'], row['family']) == (year, family))['tables'][name]


def check_preserved_family(prior, current):
    assert (current['season'], current['family']) == (prior['season'], prior['family'])
    if prior['family'] not in ('execution', 'evidence', 'microstats') or (not prior['tables'] and prior['family'] != 'execution'):
        assert current == prior
    if prior['family'] == 'evidence':
        for name, member in prior['tables'].items():
            if name not in ('interval_fact', 'interval_location', 'context_coverage'):
                assert current['tables'].get(name) == member


def compare_intervals(before, after, name):
    """original ordered rows remain exact; additions are only valued populations."""
    before = iter(before)
    current = next(before, None)
    retained = added = 0
    for row in after:
        key = tuple(row[field] for field in KEYS[name])
        old_key = None if current is None else tuple(current[field] for field in KEYS[name])
        if key == old_key:
            assert row == current
            retained += 1
            current = next(before, None)
        else:
            assert old_key is None or key < old_key
            assert row['population'] in VALUED
            added += 1
    assert current is None
    return dict(original_rows_exact=retained, added_valued_rows=added)


def index_score_members(root, annual):
    """two fixed offset catalogs; never retain the native arrays or whole rows."""
    catalogs, counts = {}, {}
    for name in ('projections.jsonl', 'maps.jsonl'):
        member = next(row for row in annual['files'] if row['path'] == name)
        offsets, hashed = {}, hashlib.sha256()
        with (root / name).open('rb') as stream:
            while True:
                offset = stream.tell()
                line = stream.readline()
                if not line:
                    break
                hashed.update(line)
                row = json.loads(line)
                key = (row['player_id'], row['strength'])
                if name == 'maps.jsonl':
                    key += (row['map_kind'],)
                assert key not in offsets
                offsets[key] = offset
        assert hashed.hexdigest() == member['sha256']
        catalogs[name] = offsets
        counts[name] = dict(rows=len(offsets), bytes=(root / name).stat().st_size)
    assert len(catalogs['projections.jsonl']) == annual['resources']['projections']
    assert len(catalogs['maps.jsonl']) == 2*annual['resources']['projections']
    return catalogs, counts


def at_offset(stream, offset):
    stream.seek(offset)
    return json.loads(stream.readline())


def check_datum(actual, value, reason, explanation, method, source):
    detail = None if value is not None else dict(explanation=explanation,
        evidence=[dict(kind='method', id=method), source])
    assert actual == dict(value=value, unavailable_reason=None if value is not None else reason,
                         reason_detail=detail, uncertainty=dict(kind='not_estimated'))


def check_copied_map(row, raw, projection, method):
    field, unit = (FIELDS[0], 'goals_per100_attempts') if row['map_kind'] == 'finishing' else (FIELDS[1], 'goals_per100_assisted_opportunities')
    assert row['map_kind'] in ('finishing', 'setting') and row['view'] == 'effect'
    assert row['result']['availability'] == 'provided' and row['result']['explanation'] is None
    data, scalar = row['result']['data'], projection[field]
    assert data['grid_id'] == 'native656' and data['unit'] == unit and data['reference'] == 'reference-execution-zero'
    assert data['method_id'] == method and data['support'] == projection['support'][field]
    assert data['integrated_value'] == scalar['value']
    assert data['unavailable_reason'] == scalar['unavailable_reason'] and data['reason_detail'] == scalar['reason_detail']
    if raw is None:
        assert scalar['value'] is None and data['cells'] is None and data['display_cells'] is None
        return
    assert (raw['season'], raw['player_id'], raw['strength'], raw['map_kind']) == (row['season'], row['player_id'], row['strength'], row['map_kind'])
    assert raw['panel_id'] == projection['reference_panel']['panel_id']
    assert raw['integrated_value'] == data['integrated_value']
    assert (raw['cells'] is None) == (data['cells'] is None)
    if raw['cells'] is None:
        assert data['cells'] is None and data['display_cells'] is None
    else:
        assert [cell['cell_id'] for cell in data['cells']] == list(range(656))
        assert [cell['value'] for cell in data['cells']] == raw['cells']
        assert data['display_cells'] is not None and len(data['display_cells']) == 668


def check_projections_maps(year, manifest, annual, people):
    root = CAMPAIGN / 'scores' / year
    offsets, sizes = index_score_members(root, annual)
    copied_pairs, copied_maps = set(), set()
    published_players = set()
    projection_groups = groupby(rows(OUTPUT, table(manifest, year, 'execution', 'skater_execution')), lambda row: row['player_id'])
    map_groups = groupby(rows(OUTPUT, table(manifest, year, 'execution', 'analysis_map')), lambda row: row['player_id'])
    missing = maps = 0
    with (root / 'projections.jsonl').open('rb') as raw_projection, (root / 'maps.jsonl').open('rb') as raw_map:
        for (player, projections), (map_player, maps_for_player) in paired(projection_groups, map_groups):
            assert player == map_player and player not in published_players
            published_players.add(player)
            current = {}
            for row in projections:
                pair = row['player_id'], row['strength']
                data = row['result']['data']
                assert row['season'] == year and row['strength'] not in current
                assert row['result']['availability'] == 'provided' and data['method_id'] == f'execution-v1-06-{year}'
                current[row['strength']] = data
                source = people[year, player]['source'][0]
                if pair in offsets['projections.jsonl']:
                    raw = at_offset(raw_projection, offsets['projections.jsonl'][pair])
                    assert (raw['season'], raw['player_id'], raw['strength']) == (year, *pair)
                    for field in FIELDS:
                        value = raw['values'][field]
                        unavailable = raw['unavailable'].get(field)
                        check_datum(data[field], value, unavailable['reason'] if value is None else 'no_exposure',
                                    unavailable['explanation'] if value is None else 'available', data['method_id'], source)
                    assert all(data[field] == raw[field] for field in ('reference_panel', 'coefficient_support', 'support'))
                    copied_pairs.add(pair)
                else:
                    missing += 1
                    empty = data['reference_panel']['opportunities'] == 0
                    explanation = ('the exact-state common panel has no supported physical attempts' if empty else
                        'the factual skater has no saved annual projection because its prepared person kind is not resolved as skater; this does not establish coefficient absence')
                    for field in FIELDS:
                        check_datum(data[field], None, 'no_exposure' if empty else 'missing_source', explanation, data['method_id'], source)
                        assert data['support'][field]['current_season_information'] is False
                        assert data['support'][field]['prior_only'] is False and data['support'][field]['prior_seasons'] == []
                    assert all(record['available'] is False and record['reason'] == 'focal_projection_unavailable_for_prepared_kind'
                               for block in data['coefficient_support'].values() for record in block.values())
            assert set(current) == set(EXECUTION_STRENGTHS)
            seen = set()
            for row in maps_for_player:
                key = player, row['strength'], row['map_kind']
                raw = at_offset(raw_map, offsets['maps.jsonl'][key]) if key in offsets['maps.jsonl'] else None
                assert key not in seen
                seen.add(key)
                check_copied_map(row, raw, current[row['strength']], f'execution-v1-06-{year}')
                if raw is not None:
                    copied_maps.add(key)
                maps += 1
            assert len(seen) == 2*len(current)
    assert published_players == {player for (season, player), person in people.items()
                                 if season == year and person['kind'] == 'skater'}
    return dict(copied_projections_exact=len(copied_pairs), factual_only_unavailable_projections=missing,
        copied_native_maps_exact=len(copied_maps), public_maps=maps,
        raw_only_projection_rows=len(offsets['projections.jsonl'].keys()-copied_pairs),
        raw_only_map_rows=len(offsets['maps.jsonl'].keys()-copied_maps), source_index_passes=sizes,
        live_payload_scope='one player projection group and one656-cell map; offset keys only survive between players',
        display_scope='derived display geometry/transport and upstream numerical map-scalar mathematics retain producer strict validation; this checker independently joins every copied native cell/scalar/support to its saved source')


def check_event_bridges(year, manifest, annual, receipt):
    root = CAMPAIGN / 'scores' / year
    readers = {
        'source': rows(OUTPUT, table(manifest, year, 'evidence', 'attempt_fact')),
        'score': rows(root, next(row for row in annual['files'] if row['path'] == 'events.jsonl')),
        'value': rows(OUTPUT, table(manifest, year, 'execution', 'attempt_value')),
        'raw_setter': rows(root, next(row for row in annual['files'] if row['path'] == 'setters.jsonl')),
        'setter': rows(OUTPUT, table(manifest, year, 'execution', 'attempt_setter')),
        'raw_share': rows(root, next(row for row in annual['files'] if row['path'] == 'shares.jsonl')),
        'share': rows(OUTPUT, table(manifest, year, 'execution', 'attempt_execution_share')),
    }
    groups = {name: iter(groupby(stream, lambda row: row['game_id'])) for name, stream in readers.items()}
    heads = {name: next(stream, None) for name, stream in groups.items()}
    partitions = {name: iter(receipt[name]) for name in ('intersection', 'source_only', 'numerical_only')}
    counts = dict.fromkeys((*partitions, 'numeric_values', 'null_values', 'setter_rows', 'share_rows', 'assist_annotations'), 0)
    unvalued = {(row['game_id'], row['source_index']): row for row in receipt['unvalued_source_attempts']}
    while heads['source'] is not None or heads['score'] is not None:
        game = min(heads[name][0] for name in ('source', 'score') if heads[name] is not None)
        batch = {}
        for name in readers:
            head = heads[name]
            assert head is None or head[0] >= game
            batch[name] = list(head[1]) if head is not None and head[0] == game else []
            if head is not None and head[0] == game:
                heads[name] = next(groups[name], None)
        source = {row['source_index']: row for row in batch['source']}
        scored = {row['source_index']: row for row in batch['score']}
        values = {row['source_index']: row for row in batch['value']}
        assert set(source) == set(values)
        for index in sorted(source.keys() | scored.keys()):
            name = 'intersection' if index in source and index in scored else 'source_only' if index in source else 'numerical_only'
            assert next(partitions[name]) == [game, index]
            counts[name] += 1
        for index, row in values.items():
            fact, physical = source[index], scored.get(index)
            complete = physical is not None and physical['status'] == 'complete'
            assert row['support_id'] == fact['support_id'] and row['method_id'] == f'execution-v1-06-{year}'
            if not complete:
                omitted = unvalued.pop((game, index))
                assert omitted['model_reasons'] == (physical['reasons'] if physical else [])
                assert omitted['reason'] == ('not_applicable' if omitted['physical_status'] == 'outside_population' else 'missing_source')
            for field in ('actor_all_attempt_opportunity', 'neutral_all_attempt_opportunity', 'actor_unblocked_goal_probability', 'actor_on_net_goal_probability', 'neutral_goalie_on_net_goal_probability'):
                applies = not (fact['outcome'] == 'block' and field == 'actor_unblocked_goal_probability'
                    or fact['outcome'] in ('block', 'miss') and field in ('actor_on_net_goal_probability', 'neutral_goalie_on_net_goal_probability'))
                value = (physical['prefixes']['actor' if field.startswith('actor') else 'neutral']['uqrg'] if field.endswith('all_attempt_opportunity')
                         else physical['conditional_probabilities'][field]) if complete and applies else None
                reason = 'not_applicable' if not applies else omitted['reason'] if not complete else 'no_exposure'
                explanation = ('conditional probability is outside its observed stage' if not applies else
                    'zero mathematical conditioning mass' if complete else
                    'source outcome is outside the physical ordinary-attempt population' if omitted['physical_status'] == 'outside_population' else
                    '; '.join(item['code'] for item in physical['reasons']) if physical else 'source key has no numerical event disposition')
                check_datum(row[field], value, reason, explanation, row['method_id'], fact['source'])
                counts['null_values' if value is None else 'numeric_values'] += 1
        expected = [row for row in batch['raw_setter'] if row['source_index'] in source]
        for raw, public in paired(expected, batch['setter']):
            before, after = dict(raw), dict(public)
            before.pop('recorded_assist_evidence')
            evidence = after.pop('recorded_assist_evidence')
            assert before == after
            fact = source[public['source_index']]
            assert evidence in ([], [fact['source']]) and (not evidence or fact['outcome'] == 'goal')
            counts['assist_annotations'] += bool(evidence)
            counts['setter_rows'] += 1
        expected = [row for row in batch['raw_share'] if row['source_index'] in source]
        for raw, public in paired(expected, batch['share']):
            assert raw == public
            counts['share_rows'] += 1
    assert all(head is None for head in heads.values())
    assert not unvalued and all(next(stream, None) is None for stream in partitions.values())
    return counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-manifest-sha256', required=True)
    parser.add_argument('--expected-selection-sha256', required=True)
    parser.add_argument('--out-check', type=Path, required=True)
    args = parser.parse_args()
    assert all(re.fullmatch('[0-9a-f]{64}', value) for value in (args.expected_manifest_sha256, args.expected_selection_sha256))
    assert not args.out_check.exists()
    began = perf_counter()
    assert sha(OUTPUT / 'manifest.json') == args.expected_manifest_sha256
    assert sha(CAMPAIGN / 'scores-selection.json') == args.expected_selection_sha256
    assert sha(FACTS / 'manifest.json') == FACTS_SHA and sha(OBSERVED) == OBSERVED_SHA
    manifest, original, selection = read(OUTPUT / 'manifest.json'), read(FACTS / 'manifest.json'), read(CAMPAIGN / 'scores-selection.json')
    assert manifest['purpose'] == selection['purpose'] == 'real'
    assert manifest['seasons'] == ['20232024', '20242025', '20252026']
    assert all(manifest[key] == original[key] for key in ('purpose', 'seasons', 'prepared_sha256', 'observed_bindings'))
    assert manifest['prepared_sha256'] == selection['prepared_sha256'] == PREPARED
    assert {row['season']: row['corpus_sha256'] for row in manifest['observed_bindings']} == {row['season']: row['sha256'] for row in read(OBSERVED)['corpora']}
    unchanged, pending = [], []
    for prior in original['families']:
        current = next(row for row in manifest['families'] if (row['season'], row['family']) == (prior['season'], prior['family']))
        check_preserved_family(prior, current)
        if not prior['tables'] and prior['family'] != 'execution':
            pending.append([prior['season'], prior['family']])
        for name, member in prior['tables'].items():
            if current['tables'].get(name) == member:
                assert sha(OUTPUT / member['path']) == member['sha256']
                unchanged.append(dict(season=prior['season'], family=prior['family'], table=name, rows=member['rows'], bytes=(OUTPUT / member['path']).stat().st_size))
    for name in ('people', 'sources'):
        assert manifest['catalogs'][name] == original['catalogs'][name]
        assert sha(OUTPUT / manifest['catalogs'][name]['path']) == original['catalogs'][name]['sha256']
    people = {(row['season'], row['player_id']): row for row in rows(OUTPUT, manifest['catalogs']['people'])}
    old_methods = {row['method_id']: row for row in rows(FACTS, original['catalogs']['methods'])}
    methods = {row['method_id']: row for row in rows(OUTPUT, manifest['catalogs']['methods'])}
    removed = {f'factual-pending-reference-{year}-opportunity' for year in manifest['seasons']}
    assert old_methods.keys()-methods.keys() == removed
    assert all(methods[key] == row for key, row in old_methods.items() if key not in removed)
    old_supports = {row['support_id']: row for row in rows(FACTS, original['catalogs']['supports'])}
    supports = {row['support_id']: row for row in rows(OUTPUT, manifest['catalogs']['supports'])}
    assert all(supports[key] == row for key, row in old_supports.items())
    annuals, pins, previous = {}, {}, None
    assert [row['season'] for row in selection['scores']] == ['20212022', '20222023', '20232024', '20242025', '20252026']
    for item in selection['scores']:
        year = item['season']
        path = CAMPAIGN / 'scores' / year / 'manifest.json'
        assert item['path'] == str(path) and sha(path) == item['sha256']
        annual = read(path)
        assert annual['purpose'] == 'real' and annual['season'] == year
        assert annual['prepared']['sha256'] == PREPARED and annual['coaches']['sha256'] == COACHES and annual['recipe']['sha256'] == RECIPE
        assert annual['state']['previous'] == previous
        assert annual['numerical_resolution']['status'] == ('passed' if year == '20252026' else 'not_applicable')
        previous = {key: annual['state'][key] for key in ('path', 'sha256')}
        annuals[year], pins[year] = annual, item['sha256']
    checks = []
    for year in manifest['seasons']:
        annual = annuals[year]
        evidence_path = OUTPUT / f'{year}-execution-composition.json'
        receipt = read(evidence_path)
        assert receipt['source_results_sha256'] == FACTS_SHA and receipt['scores_sha256'] == pins[year]
        for method_id in (f'execution-v1-06-{year}', f'reference-xg-v1-06-{year}'):
            method = methods[method_id]
            assert method['recipe_id'] == 'experimental-v1:execution-v1-05-2' and method['design_sha256'] == pins[year]
            assert method['training_cutoff'] == annual['training_cutoff'] and method['fit_seasons'] == [season for season in annuals if season <= year]
            assert method['evidence'] == [dict(uri=str(CAMPAIGN / 'scores' / year / 'manifest.json'), sha256=pins[year]),
                dict(uri=str(FACTS / 'manifest.json'), sha256=FACTS_SHA), dict(uri=str(evidence_path), sha256=sha(evidence_path))]
            history = [season for season in annuals if season <= year]
            panels = [row for row in annual['files'] if row['role'] in ('panel_arrays', 'panel_events')]
            panel_sha = hashlib.sha256(json.dumps(panels, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()).hexdigest()
            assert method['inputs'] == [dict(role='prepared', sha256=PREPARED, seasons=history),
                dict(role='coaches', sha256=COACHES, seasons=history),
                dict(role='opportunity_panel', sha256=panel_sha, seasons=[year]),
                dict(role='source_results', sha256=FACTS_SHA, seasons=[year]),
                *[dict(role='annual_state', sha256=annuals[season]['state']['sha256'], seasons=[season]) for season in history]]
            assert method['reference_id'] == 'reference-execution-zero' and method['support_policy_id'] == 'execution-v1-06-matched-reference-v1'
        intervals = {name: compare_intervals(rows(FACTS, table(original, year, 'evidence', name)), rows(OUTPUT, table(manifest, year, 'evidence', name)), name)
                     for name in ('interval_fact', 'interval_location')}
        raw_coverage = 0
        for old, new in paired(rows(FACTS, table(original, year, 'evidence', 'context_coverage')), rows(OUTPUT, table(manifest, year, 'evidence', 'context_coverage'))):
            assert (old['player_id'], old['population']) == (new['player_id'], new['population'])
            if old['population'] not in VALUED:
                assert old == new
                raw_coverage += 1
        microstats = xg_available = 0
        for old, new in paired(rows(FACTS, table(original, year, 'microstats', 'skater_microstats')), rows(OUTPUT, table(manifest, year, 'microstats', 'skater_microstats'))):
            left, right = deepcopy(old), deepcopy(new)
            left['result']['data'].pop('reference_xg_per60')
            xg = right['result']['data'].pop('reference_xg_per60')
            assert left == right and xg['construction'] == 'model_valued' and xg['provenance'] == dict(id=f'reference-xg-v1-06-{year}', kind='method')
            if xg['value'] is not None:
                assert xg['denominator'] > 0 and math.isclose(xg['value'], 3600*xg['numerator']/xg['denominator'], rel_tol=1e-10, abs_tol=1e-10)
                xg_available += 1
            microstats += 1
        checks.append(dict(season=year, intervals=intervals, nonvalued_coverage_exact=raw_coverage,
            nonowned_microstats_exact=microstats, reference_xg_available_rate_arithmetic=xg_available,
            source_score_bridges=check_event_bridges(year, manifest, annual, receipt),
            copied_projections_maps=check_projections_maps(year, manifest, annual, people)))
        print(json.dumps(checks[-1]), flush=True)
    assert (CAMPAIGN / 'compose-execution.exit').read_text().strip() == '0'
    log = (CAMPAIGN / 'compose-execution.log').read_text()
    timing = re.search(r'(\d+\.\d+) real\s+(\d+\.\d+) user\s+(\d+\.\d+) sys', log)
    assert timing
    result = dict(kind='replacement-real-execution-compose-saved-check', status='saved copy/accounting checks passed; independent and root acceptance pending',
        recorded_at_utc=datetime.now(timezone.utc).isoformat(), manifest=identity(OUTPUT / 'manifest.json'), facts=identity(FACTS / 'manifest.json'),
        selection=identity(CAMPAIGN / 'scores-selection.json'), observed=identity(OBSERVED), producer=manifest['producer'],
        preservation=dict(unchanged_tables=unchanged, retained_factual_methods=len(old_methods)-len(removed), retained_supports=len(old_supports), pending_families=pending),
        seasons=checks, cost=dict(whole_command_wall_seconds=float(timing[1]), producer_log=identity(CAMPAIGN / 'compose-execution.log'),
            producer_peak_rss_bytes=int(re.search(r'(\d+)\s+maximum resident set size', log).group(1)),
            producer_peak_footprint_bytes=int(re.search(r'(\d+)\s+peak memory footprint', log).group(1)),
            checker_wall_seconds=perf_counter()-began, checker_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        size=dict(complete_artifact_bytes=sum(path.stat().st_size for path in OUTPUT.rglob('*') if path.is_file())), checker=identity(Path(__file__).resolve()),
        limits=['saved-row copy/accounting and source-score joins only; no raw game or predictor reconstruction, NPZ load or new strict artifact read',
            'every copied native map/projection value and support is joined to its accepted saved score row; upstream numerical map-scalar and derived display-transform math retain existing producer validation and later real API checks',
            'recorded assist annotations are restricted to matching factual goal evidence; official source-assist chronology is not independently rederived here',
            'factual-only projections remain explicitly unavailable; raw-only score rows are reported; no scientific admission, ability bound, activation or spatial pin cutover'])
    with args.out_check.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=result['status'], receipt=identity(args.out_check))), flush=True)


if __name__ == '__main__':
    main()
