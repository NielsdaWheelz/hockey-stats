"""held actual native csv check, adapted from the accepted fixture download check."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, json, resource, sqlite3, time

project = Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
campaign = Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01')
database = campaign / 'real/candidate/player-analysis.sqlite'
expected_database_sha256 = '12d738d0eee0694a76f266c5b48284a035365cc837d8de1667a765443369ef5b'
expected_publication_id = '53d900fd-7926-4841-89aa-c3a73bdf4b08'
expected_database_stat = (13356376064, 1794001967301147330)  # accepted (bytes, mtime_ns), supplied by root; no duplicate database rehash.
downloads = {
    'burns_history': 'WITHHELD_ACTUAL_BURNS_HISTORY_CSV_PATH',
    'same_distribution': 'WITHHELD_ACTUAL_BURNS_PETRY_DISTRIBUTION_CSV_PATH',
    'mixed_distribution': 'WITHHELD_ACTUAL_BURNS_PERRY_DISTRIBUTION_CSV_PATH',
    'hodgson_history': 'WITHHELD_ACTUAL_HODGSON_HISTORY_CSV_PATH',
    'wilson_history': 'WITHHELD_ACTUAL_WILSON_HISTORY_CSV_PATH',
    'visible_table': 'WITHHELD_ACTUAL_VISIBLE_BURNS_TABLE_CSV_PATH',
}
# fixed selected journeys; root must use these exact controls for these downloaded files.
years = ['20232024', '20242025', '20252026']
metric = 'spatial.5v5.defense_xg_per60'
field = 'defense_xg_per60'
history_ids = {'burns_history': '8470613', 'hodgson_history': '8478173', 'wilson_history': '8475253'}
distribution_ids = {'same_distribution': ['8470613', '8473507'], 'mixed_distribution': ['8470613', '8470621']}
peer_min = 0
# visible table: final year, spatial/5v5, q=brent burns, position=d, team=21, min=0,
# peers=position, peerMin=0; any selected sort has the same one-person row order.
visible_id = '8470613'
manifest_sha = 'a40ca1c0291579b773db22294f26998f154309b2b65926f00f901331ef0b17d5'
case_sha = '89bae2a6e69591c97d0283ddee74f819a9195b3c2e9ba1f38f25dfc74d033845'


def main():
    # every concrete candidate/download identity is required BEFORE any stat/read/connect.
    assert len(expected_database_sha256) == 64 and all(c in '0123456789abcdef' for c in expected_database_sha256), 'accepted real database digest withheld; no i/o'
    assert expected_publication_id and 'WITHHELD' not in expected_publication_id, 'accepted real publication id withheld; no i/o'
    assert isinstance(expected_database_stat, tuple) and len(expected_database_stat) == 2 and all(isinstance(n, int) and n > 0 for n in expected_database_stat), 'accepted real database stat withheld; no i/o'
    assert all(isinstance(p, str) and p.startswith('/Users/nnandal/Downloads/') and 'WITHHELD' not in p for p in downloads.values()), 'actual download paths withheld; no i/o'
    assert len(set(downloads.values())) == len(downloads), 'actual downloads must be distinct'
    started = time.perf_counter()
    read_scope = []
    def identity(p):
        raw = p.read_bytes()
        return dict(path=str(p), bytes=len(raw), mtime_ns=p.stat().st_mtime_ns, sha256=hashlib.sha256(raw).hexdigest())
    def read_json(p, digest, lines=False):
        raw = p.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == digest, p
        read_scope.append(dict(path=str(p), bytes=len(raw), sha256=digest))
        return [json.loads(line) for line in raw.splitlines()] if lines else json.loads(raw)
    cases = read_json(project / 'docs/research/spatial-v1-08/receipts/real-product-case-selection-01.json', case_sha)
    assert cases['combined_manifest_sha256'] == manifest_sha
    source = campaign / 'real/results'
    manifest = read_json(source / 'manifest.json', manifest_sha)
    member = manifest['catalogs']['methods']
    source_methods = {m['method_id']: m for m in read_json(source / member['path'], member['sha256'], True)}
    source_rows = {}
    estimate_fields = [f'{role}_{q}_per60{suffix}' for role in ['offense', 'defense'] for q in ['attempts', 'xg'] for suffix in ['', '_complete', '_neutral']] + [f'{role}_{q}_relative_percent' for role in ['offense', 'defense'] for q in ['attempts', 'xg']]
    for year in years:
        family = next(r for r in manifest['families'] if r['family'] == 'spatial' and r['season'] == year)
        member = family['tables']['skater_spatial']
        source_rows[year] = {r['player_id']: r['result']['data'] for r in read_json(source / member['path'], member['sha256'], True) if r['strength'] == '5v5'}
    dbstat = database.stat()
    assert (dbstat.st_size, dbstat.st_mtime_ns) == expected_database_stat
    connection = sqlite3.connect('file:' + str(database) + '?mode=ro&immutable=1', uri=True)
    connection.row_factory = sqlite3.Row
    pub = dict(connection.execute('select publication_id,purpose,schema_version,population_version from publication').fetchone())
    assert (pub['publication_id'], pub['purpose'], pub['schema_version']) == (expected_publication_id, 'real', 8)
    corpora = {r['season']: r['corpus_sha256'] for r in connection.execute('select season,corpus_sha256 from season')}
    assert sorted(corpora) == years
    stored, methods = {}, {}
    for year in years:
        rows = connection.execute("select s.player_id,s.method_id,s.availability,s.payload_json,p.display_name,p.reported_position,p.teams_json from skater_spatial s join person p using(season,player_id) where s.season=? and s.strength='5v5' and p.kind='skater'", (year,)).fetchall()
        stored[year] = {r['player_id']: {**dict(r), 'data': json.loads(r['payload_json'])} for r in rows}
        for pid, row in stored[year].items():
            assert row['availability'] == 'provided'
            mid = row['method_id']
            if mid not in methods:
                methods[mid] = json.loads(connection.execute('select payload_json from analysis_method where method_id=?', (mid,)).fetchone()[0])
                assert methods[mid] == source_methods[mid]
    # exact v2 metadata supplies warning strings, evidence and seven-quantity findings.
    # verify scope without inventing a paraphrase or treating an adjustment finding as scalar evidence.
    for year in years:
        method = methods['spatial-v1-08-' + year]
        assert len(method['limitations']) == {'20232024': 6, '20242025': 7, '20252026': 8}[year]
        findings = method['assessment']['findings']
        scalar = [f for f in findings if any(q.startswith('skater_spatial.') for q in f['quantities'])]
        adjustment = [f for f in findings if any(q.startswith('adjustment_decomposition.') for q in f['quantities'])]
        assert len(scalar) == 1 and len(adjustment) == (0 if year == years[0] else 1)
        assert len(scalar[0]['quantities']) == 16
        if adjustment:
            assert set(adjustment[0]['quantities']) == {'adjustment_decomposition.' + f for f in ['baseline', 'self', 'teammates', 'opponents', 'coaching_other_context', 'numerical_residual', 'factual_prediction']}
            assert adjustment[0]['summary'] == method['limitations'][-1]
        volume_warning = methods['spatial-v1-08-20252026']['limitations'][-2]
        assert (volume_warning in method['limitations']) == (year == years[-1])
        assert (volume_warning in scalar[0]['summary']) == (year == years[-1])
    def position(record):
        p = record['reported_position']
        return 'd' if p == 'D' else 'f' if p in ['C', 'L', 'R', 'F'] else None
    def meaning(record):
        m = methods[record['method_id']]
        return (m['recipe_id'], m['reference_id'], m['support_policy_id'])
    def cohort(year, record, selected_field=field):
        return {pid: r for pid, r in stored[year].items() if position(r) == position(record) and position(r) is not None and meaning(r) == meaning(record) and r['data'][selected_field]['value'] is not None and r['data']['support']['included_seconds'] is not None and r['data']['support']['included_seconds'] > 0 and r['data']['support']['included_seconds'] >= peer_min * 60}
    paths = {name: Path(path) for name, path in downloads.items()}
    identities = {name: identity(p) for name, p in paths.items()}
    exports = {name: list(csv.DictReader(p.open(newline=''))) for name, p in paths.items()}
    checked, absent, source_checked = [], [], set()
    def check_row(row, expected_field=field):
        year, pid = row['season'], row['player_id']
        context = (year, pid, expected_field)
        def eq(key, value):
            assert row[key] == value, (context, key, row[key], value)
        def scalar(key, value):
            assert (row[key] == '' if value is None else float(row[key]) == value), (context, key)
        for key, value in [('publication_id', expected_publication_id), ('purpose', 'real'), ('corpus_sha256', corpora[year]), ('metric_id', 'spatial.5v5.' + expected_field), ('spatial_strength', '5v5'), ('api_strength', '')]:
            eq(key, value)
        if pid not in stored[year]:
            eq('value_status', 'absent'); eq('value_reason', 'player is absent from selected season'); eq('standing_reason', 'absent season')
            for key in ['value', 'display_value', 'percentile', 'included_seconds', 'qualification_seconds', 'known_excluded_seconds', 'prior_only', 'current_season_information']:
                eq(key, '')
            for key in ['spatial_detail', 'uncertainty', 'support_reason_counts', 'inferred_inputs', 'prior_seasons']:
                assert json.loads(row[key]) is None
            assert json.loads(row['method_evidence']) == []
            absent.append(dict(season=year, player_id=pid)); return
        record = stored[year][pid]; data = record['data']; support = data['support']; estimate = data[expected_field]; method = methods[record['method_id']]
        original = source_rows[year][pid]
        for key in [*estimate_fields, 'support', 'method_id']:
            assert data[key] == original[key], (context, key)
        source_checked.add((year, pid))
        role = expected_field.split('_')[0]; quantity = 'attempts' if '_attempts_' in expected_field else 'xg'
        quartet = dict(difference=data[f'{role}_{quantity}_per60'], complete=data[f'{role}_{quantity}_per60_complete'], neutral=data[f'{role}_{quantity}_per60_neutral'], relative_percent=data[f'{role}_{quantity}_relative_percent'])
        for key, value in [('player_kind', 'skater'), ('display_name', record['display_name']), ('position', record['reported_position']), ('unit', '%' if expected_field.endswith('relative_percent') else quantity + '_per60'), ('value_status', 'provided' if estimate['value'] is not None else 'unavailable'), ('value_reason', estimate['unavailable_reason'] or ''), ('uncertainty_status', estimate['uncertainty']['kind']), ('qualification_basis', 'spatial.5v5.support.included_seconds'), ('reference_id', method['reference_id']), ('support_policy_id', method['support_policy_id']), ('numeric_reference', method['reference']), ('population', method['population']), ('direction', 'positive means more against; higher percentile means higher rate' if role == 'defense' else 'positive means more for; higher percentile means higher rate')]:
            eq(key, value)
        eq('display_unit', '%' if expected_field.endswith('relative_percent') else quantity + ' per 60 min')
        eq('construction', 'experimental conditional seasonal estimate')
        eq('incompatible_peer_count', '0')
        for key in ['value', 'display_value']:
            scalar(key, estimate['value'])
        for key, value in [('included_seconds', support['included_seconds']), ('qualification_seconds', support['included_seconds']), ('known_excluded_seconds', support['known_excluded_seconds'])]:
            scalar(key, value)
        for key, value in [('value_reason_detail', estimate['reason_detail']), ('uncertainty', estimate['uncertainty']), ('spatial_detail', quartet), ('teams', json.loads(record['teams_json'])), ('method_ids', [record['method_id']]), ('method_limitations', method['limitations']), ('method_evidence', [dict(method_id=record['method_id'], evidence=method['evidence'])]), ('support_reason_counts', support['reason_counts']), ('inferred_inputs', support['inferred_inputs']), ('prior_seasons', support['prior_seasons'])]:
            assert json.loads(row[key]) == value, (context, key)
        for key in ['unquantified_gap', 'prior_only', 'current_season_information']:
            assert (None if row[key] == '' else json.loads(row[key])) == support[key]
        for phrase in ['aggregate support', 'games with a located excluded segment', 'a prior-only magnitude comes from the prior']:
            assert phrase in row['spatial_support_meaning']
        members = cohort(year, record, expected_field)
        eq('cutoff_minutes', str(peer_min)); eq('cohort_n', str(len(members))); eq('peer_group', 'reported defense' if position(record) == 'd' else 'reported forwards')
        if estimate['value'] is not None and pid in members:
            values = [r['data'][expected_field]['value'] for r in members.values()]
            percentile = 100 * (sum(v < estimate['value'] for v in values) + sum(v == estimate['value'] for v in values) / 2) / len(values)
            scalar('percentile', percentile); eq('standing_reason', ''); eq('member', 'true')
        else:
            eq('percentile', '')
            reason = estimate['unavailable_reason'] if estimate['value'] is None else 'qualification unavailable' if support['included_seconds'] is None else 'no exposure' if support['included_seconds'] <= 0 else 'below cutoff'
            eq('standing_reason', reason)
        checked.append(dict(season=year, player_id=pid, field=expected_field, value=estimate['value'], peer_n=len(members), prior_only=support['prior_only']))
    for artifact, pid in history_ids.items():
        rows = exports[artifact]
        assert [(r['season'], r['player_id']) for r in rows] == [(y, pid) for y in years]
        for row in rows: check_row(row)
    for artifact, ids in distribution_ids.items():
        expected = set()
        for pid in ids:
            expected.update(cohort(years[-1], stored[years[-1]][pid]))
        expected.update(ids)
        rows = exports[artifact]
        assert len(rows) == len(expected) and {r['player_id'] for r in rows} == expected
        assert all(r['season'] == years[-1] for r in rows)
        for row in rows: check_row(row)
    table = exports['visible_table']
    selector_fields = [f'{role}_{q}' for role in ['offense', 'defense'] for q in ['attempts_per60', 'xg_per60', 'attempts_relative_percent', 'xg_relative_percent']]
    columns = ['minutes', *['spatial.5v5.' + f for f in selector_fields]]
    assert len(table) == 9 and [r['column_id'] for r in table] == columns
    for index, row in enumerate(table):
        assert (row['player_id'], row['season'], row['table'], row['strength'], row['row_order'], row['column_order']) == (visible_id, years[-1], 'spatial', '5v5', '1', str(index + 1))
        if index:
            check_row(row, selector_fields[index-1]); continue
        observed = connection.execute('select included_seconds,known_excluded_seconds,attempts_for,attempts_against,for_per60,against_per60,coverage_status,reason_codes_json from player_season where season=? and player_id=?', (years[-1], visible_id)).fetchone()
        support = dict(observed); support['reason_codes'] = json.loads(support.pop('reason_codes_json'))
        assert float(row['value']) == observed['included_seconds'] and float(row['display_value']) == observed['included_seconds'] / 60
        assert row['unit'] == 'seconds' and row['display_unit'] == 'minutes' and row['metric_id'] == ''
        assert json.loads(row['metadata_evidence']) == dict(observed_support=support, population_version=pub['population_version'])
    assert len(absent) == 3  # hodgson2023 and wilson2023/2024 are actual published gaps.
    hodgson = exports['hodgson_history'][1]
    assert hodgson['prior_only'] == 'true' and hodgson['qualification_seconds'] == '0' and hodgson['percentile'] == ''
    connection.close()
    assert (database.stat().st_size, database.stat().st_mtime_ns) == expected_database_stat
    assert all(identity(paths[name]) == old for name, old in identities.items())
    receipt = dict(kind='replacement-real-actual-native-csv-download-check', status='passed actual downloaded csv bytes against accepted source/candidate metadata; root png/native acceptance remains separate', recorded_at_utc=datetime.now(timezone.utc).isoformat(), publication_id=expected_publication_id,
                   database=dict(path=str(database), accepted_sha256=expected_database_sha256, bytes=dbstat.st_size, mtime_ns=dbstat.st_mtime_ns, connection='mode=ro&immutable=1', digest_reused_not_recomputed=True),
                   case_receipt_sha256=case_sha, combined_manifest_sha256=manifest_sha, actual_downloads=identities, row_counts={k:len(v) for k,v in exports.items()}, selected_rows=checked, absent_rows=absent,
                   source_metadata_reads=read_scope, source_exported_scalar_records_checked=len(source_checked), source_estimate_fields_per_record=16,
                   annual_method_limitations={y:methods['spatial-v1-08-'+y]['limitations'] for y in years}, method_evidence={mid:m['evidence'] for mid,m in methods.items()},
                   controller=dict(path=str(Path(__file__)), sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
                   resources=dict(wall_seconds=time.perf_counter()-started, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                   limits=['no browser/PNG pixel/layout/export-click action by controller', 'cohort membership and midpoint percentiles independently checked; distribution locale name ordering not independently replayed', 'actual source/dist binding and root measured render/export cost remain separately supplied native evidence', 'source scalar binding covers exported player-years only; no whole-candidate acceptance claim', 'no map/array/source-game/model/state reader/strict database scan/objective/fit/API/server/activation action'])
    output = campaign / 'real/actual-native-csv-check-01.json'
    with output.open('x') as f:
        json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps(dict(status='passed', receipt=str(output), sha256=hashlib.sha256(output.read_bytes()).hexdigest(), row_counts=receipt['row_counts'])))


if __name__ == '__main__':
    main()
