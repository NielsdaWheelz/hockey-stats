"""02d's three observed states and bounded frozen-support audit; no fitting."""

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import asdict
import hashlib
import heapq
import json
from pathlib import Path
import sqlite3
import sys
import time
from types import SimpleNamespace

from hockey_stats.artifacts import (
    clean_implementation, digest, implementation, linked_path, require, resources,
    write_json,
)
from hockey_stats.captures import InputContractError, SOURCES, read_capture, strict_json
from hockey_stats.chance_cli import identity, output_path, read_json
from hockey_stats.cli import Once
from hockey_stats.corpus_inputs import load_corpus
from hockey_stats.observed import aggregate
from hockey_stats.publication import check_season, read_selection, stored_row

SPEC = Path(__file__).resolve().parents[2] / 'docs/specs/02d-source-exposure-consistency.md'
POLICY = 'strict_interior_other_strength_v1'
SEASONS = ('20232024', '20242025', '20252026')
TARGETS = frozenset(str(g) for g in range(2024021235, 2024021292))
TRANSFER_SOURCES = frozenset(('play-by-play','play-report','shifts'))
BOUNDARIES = frozenset(('2025020202', '2025020611', '2025020620'))
BASELINE_SHA256 = '9469fc771dcffe6cb8e1c2e6d366f2259fc01f04b4b734ccbbd88a665ab02f56'
SELECTION_SHA256 = '920aad8d3faaa10101266843ca848e67f94f00e1ffc17e07c5654d78c157dbd4'
TABLES = {
    'player': ('player_id',), 'game': ('game_id',),
    'player_game': ('player_id', 'game_id'), 'player_season': ('player_id',),
    'spatial_cell': ('cell_id',), 'player_game_spatial': ('player_id', 'game_id', 'cell_id'),
    'player_season_spatial': ('player_id', 'cell_id'),
}
RESULT_FIELDS = {
    'player': 'players', 'game': 'games', 'player_game': 'player_games',
    'player_season': 'player_seasons', 'spatial_cell': 'spatial_cells',
    'player_game_spatial': 'player_game_spatial', 'player_season_spatial': 'player_season_spatial',
}
PHASES = (('policy_only', 0, 1), ('recovery', 1, 2), ('total', 0, 2))
def change(original, policy_only, selected):
    """available additive facts telescope exactly; missing facts never become zero."""
    values = (original, policy_only, selected)
    additive = all(v is None or type(v) is int for v in values)
    differences = [values[j] - values[i] if additive and values[i] is not None
                   and values[j] is not None else None for _, i, j in PHASES]
    if all(v is not None for v in differences):
        require(differences[2] == differences[0] + differences[1], 'additive decomposition differs')
    return dict(zip(('original', 'policy_only', 'selected'), values),
                policy_delta=differences[0], recovery_delta=differences[1], total_delta=differences[2],
                reason='unavailable_or_absent_state' if None in values else None)


def ledger_rows(reference, games):
    """verify the entire declared body while retaining only selected game rows."""
    require(type(reference) is dict and set(reference) == {'path', 'sha256'}, 'invalid ledger reference')
    digest(reference['sha256'])
    path = Path(reference['path'])
    require(path.is_absolute(), 'ledger path must be absolute')
    hasher = hashlib.sha256()
    with path.open('rb') as source:
        for index, line in enumerate(source, 1):
            hasher.update(line)
            try:
                row = strict_json(line)
            except ValueError as error:
                raise InputContractError(f'{path}:{index}: invalid ledger json') from error
            require(type(row) is dict and type(row.get('game_id')) is str,
                    f'{path}:{index}: invalid ledger game identity')
            if row['game_id'] in games:
                yield row
    require(hasher.hexdigest() == reference['sha256'], f'{path}: ledger digest mismatch')


def _admission(value):
    if isinstance(value, dict):
        return {k: _admission(v) for k, v in value.items()
                if k not in ('capture_path', 'requested_at', 'interpretation', 'implementation', 'message')}
    if isinstance(value, list):
        return [_admission(v) for v in value]
    return value


def source_concordance(observed, frozen):
    """compare bound body identities and admission facts, never path/date equality."""
    differences = []
    for label, value in (('observed', observed), ('frozen', frozen)):
        if not isinstance(value, dict) or not isinstance(value.get('interpreted'), dict):
            return dict(source_status='unresolved', reason=f'{label}_envelope_unavailable')
        inputs = value['interpreted'].get('inputs', [])
        if len(inputs) != 6 or {r.get('source') for r in inputs} != set(SOURCES):
            return dict(source_status='unresolved', reason=f'{label}_source_inventory_unavailable')
        for row in inputs:
            if row.get('source') in TRANSFER_SOURCES and row.get('status') != 'parsed':
                return dict(source_status='unresolved', reason=f'{label}_{row.get("source")}_unavailable')
            if row.get('status') == 'parsed' and row.get('body_sha256') is None:
                return dict(source_status='unresolved', reason=f'{label}_body_identity_unavailable')
            if row.get('body_sha256') is not None:
                digest(row['body_sha256'])
        if not value['interpreted'].get('game'):
            return dict(source_status='unresolved', reason=f'{label}_game_identity_unavailable')
    left = {r['source']: r for r in observed['interpreted']['inputs']}
    right = {r['source']: r for r in frozen['interpreted']['inputs']}
    for source in SOURCES:
        if any(left[source].get(k) != right[source].get(k)
               for k in ('body_sha256','status','http_status')):
            differences.append(source)
    # receipt reasons contain filesystem diagnostics; their structured state is compared above.
    admitted = lambda value: _admission({k:v for k,v in value['interpreted'].items() if k != 'inputs'})
    if admitted(observed) != admitted(frozen):
        differences.append('interpreted_admission')
    if _admission(observed.get('reconstruction')) != _admission(frozen.get('reconstruction')):
        differences.append('native_admission')
    return dict(source_status='different_frozen_evidence' if differences else 'concordant',
                reason='bound_bodies_or_admission_differ' if differences else None,
                differences=differences)


def intersect_runs(runs, segments, events, population, *, directed_rows=None, game=None):
    """intersect whole runs with the frozen ledger's score-split rows and masks."""
    require(population in ('all_attempts', 'unblocked_spatial'), 'unknown frozen population')
    runs = sorted({(r['period_number'], r['start_seconds'], r['end_seconds']) for r in runs})
    for i, (period, start, end) in enumerate(runs):
        require(type(period) is int and type(start) is int and type(end) is int and end > start,
                'invalid physical incident range')
        require(not i or period != runs[i-1][0] or start >= runs[i-1][2], 'overlapping incident ranges')
    selected = []
    for period, start, end in runs:
        rows = sorted((s for s in segments if s['period'] == period and s['start'] < end and s['end'] > start),
                      key=lambda s: s['start'])
        cursor = start
        for row in rows:
            require(row['start'] == cursor and row['end'] <= end and row['classification'] == 'five_on_five',
                    'incident does not align with frozen score/context-split boundaries')
            require(len(row['away_skaters']) == len(set(row['away_skaters'])) == 5
                    and len(row['home_skaters']) == len(set(row['home_skaters'])) == 5,
                    'frozen segment does not have ten distinct team skaters')
            cursor = row['end']
            selected.append(row)
        require(cursor == end, 'frozen ledger does not completely cover incident')
    require(len({s['segment_index'] for s in selected}) == len(selected), 'duplicate frozen segment')
    event_ids = [e['source_index'] for e in events]
    require(len(event_ids) == len(set(event_ids)), 'duplicate frozen event')
    by_segment = defaultdict(list)
    for event in events:
        if event['assigned_segment'] is not None:
            by_segment[event['assigned_segment']].append(event)
    losses, prior, lost, excluded, players = 0, 0, [], [], Counter()
    ledger_receipts = []
    directed_checked = 0
    directed_seconds = player_seconds = directed_counts = 0
    for row in selected:
        index = row['segment_index']
        duration = row['end'] - row['start']
        masks = row['masks'][population]
        require(isinstance(masks, list), 'frozen mask must be an array')
        if directed_rows is not None:
            directions = [r for r in directed_rows if r['segment_index'] == index]
            require(len(directions) == (0 if masks else 2), 'frozen directed-row mask/pair differs')
            require(masks or {r['stratum'][0] for r in directions} == {'away','home'},
                    'frozen directed-row side pair differs')
            for direction in directions:
                side = direction['stratum'][0]
                opponent = 'home' if side == 'away' else 'away'
                expected_counts = row['counts'][side][population]
                if population == 'all_attempts':
                    expected_counts = [[0,expected_counts]] if expected_counts else []
                require(direction['population'] == population and direction['period'] == row['period']
                        and direction['start'] == row['start'] and direction['end'] == row['end']
                        and direction['seconds'] == duration
                        and direction['offense'] == row[side+'_skaters']
                        and direction['defense'] == row[opponent+'_skaters']
                        and direction['counts'] == expected_counts,
                        'frozen directed-row range/membership/counts differ from segment')
                require(game is not None and direction['attacking_team'] == game[side+'_team_id']
                        and direction['stratum'][1] == (str(row['period']) if row['period'] <= 3 else 'overtime')
                        and direction['stratum'][2] == max(-3,min(3,-row['score_difference'] if side == 'away' else row['score_difference'])),
                        'frozen directed-row context differs')
                directed_checked += 1
                directed_seconds += direction['seconds']
                player_seconds += direction['seconds']*len(direction['offense'])
                directed_counts += sum(count for _,count in direction['counts'])
        counts = row['counts']
        assigned = by_segment[index]
        total = 0
        for side in ('away', 'home'):
            relevant = [e for e in assigned if e['side'] == side and e[population] in ('retained','excluded')]
            require(all(e['period'] == row['period'] and row['start'] <= e['clock'] <= row['end']
                        for e in relevant), 'frozen event assignment lies outside its segment')
            if population == 'all_attempts':
                expected = counts[side][population]
                require(type(expected) is int and expected >= 0 and len(relevant) == expected,
                        'frozen scalar counts differ from exact event assignment')
            else:
                cells = counts[side][population]
                expected_cells = Counter()
                for cell, count in cells:
                    require(type(cell) is int and type(count) is int and count > 0,
                            'invalid frozen sparse cell count')
                    require(cell not in expected_cells, 'duplicate frozen sparse cell')
                    expected_cells[cell] = count
                require(Counter(e['cell_id'] for e in relevant if e['cell_id'] is not None) == expected_cells,
                        'frozen spatial counts differ from exact event assignment')
                require(masks or all(e['cell_id'] is not None for e in relevant),
                        'retained spatial event has no allocated cell')
                expected = sum(expected_cells.values())
            require(all((e[population] == 'retained') == (not masks) for e in relevant),
                    'frozen event disposition disagrees with population mask')
            total += expected
            target = excluded if masks else lost
            target.extend(dict(source_index=e['source_index'], event_id=e['event_id'], segment_index=index,
                               side=side, cell_id=e.get('cell_id')) for e in relevant)
        if masks:
            prior += duration
        else:
            losses += duration
            for pid in row['away_skaters'] + row['home_skaters']:
                players[str(pid)] += duration
        ledger_receipts.append(dict(segment_index=index, period=row['period'], start=row['start'], end=row['end'],
            score=row.get('score'), score_difference=row.get('score_difference'), masks=masks,
            pre_mask_attempts=total, interval_indices=row.get('interval_indices')))
    if directed_rows is not None:
        require(directed_seconds == 2*losses and player_seconds == 10*losses and directed_counts == len(lost),
                'frozen directed/player/count loss does not conserve physical/event units')
    return dict(newly_excluded_physical_seconds=losses,
        newly_excluded_directed_seconds=directed_seconds if directed_rows is not None else 2*losses,
        newly_excluded_player_seconds=player_seconds if directed_rows is not None else 10*losses, already_excluded_physical_seconds=prior,
        already_excluded_directed_seconds=2*prior, already_excluded_player_seconds=10*prior,
        newly_excluded_attempts=len(lost), already_excluded_attempts=len(excluded),
        newly_excluded_player_for=len(lost)*5, newly_excluded_player_against=len(lost)*5,
        affected_players=[dict(player_id=pid, lost_seconds=seconds) for pid, seconds in sorted(players.items())],
        lost_retained_events=lost, already_excluded_events=excluded, segments=ledger_receipts,
        directed_rows_checked=directed_checked if directed_rows is not None else None)


def _read_database(path, version, purpose):
    connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute('PRAGMA query_only=ON')
        require(connection.execute('PRAGMA user_version').fetchone()[0] == version,
                f'{path}: expected pinned schema {version}')
        require([tuple(r) for r in connection.execute('PRAGMA integrity_check')] == [('ok',)],
                f'{path}: sqlite integrity check failed')
        require(not connection.execute('PRAGMA foreign_key_check').fetchall(), f'{path}: foreign keys differ')
        require(not Path(str(path) + '-wal').exists(), f'{path}: unexpected wal publication')
        meta = dict(connection.execute('SELECT * FROM publication').fetchone())
        require(connection.execute('SELECT count(*) FROM publication').fetchone()[0] == 1,
                'publication metadata must be unique')
        require(meta['schema_version'] == version and meta['purpose'] == purpose
                and meta['kind'] == 'observed_5v5' and meta['game_type'] == 2,
                'publication metadata differs')
        suffix = 'v1' if version == 4 else 'v2'
        require(meta['population_version'] == 'matched_attempts_' + suffix
                and meta['personal_population_version'] == 'matched_personal_credits_' + suffix
                and meta['spatial_population_version'] == 'matched_unblocked_locations_' + suffix
                and meta['spatial_display_version'] == 'rect5_gaussian10_v1', 'publication support versions differ')
        producer = strict_json(meta['producer_json'].encode())
        require(producer['git_dirty'] is False and isinstance(producer['git_commit'], str)
                and len(producer['git_commit']) == 40, 'publication producer must be clean and identified')
        require([r[0] for r in connection.execute('SELECT season FROM season ORDER BY season')] == list(SEASONS),
                'publication season inventory differs')
        return connection, meta
    except BaseException:
        connection.close()
        raise


def _receipts(database, selection):
    top_path = database.parent / 'verification.json'
    top = read_json(top_path)
    require(top['schema_version'] == 1 and top['kind'] == 'observed_publication_verification'
            and top['purpose'] == selection['purpose'], 'publication receipt contract differs')
    require(identity(database)['sha256'] == top['database']['sha256']
            and Path(top['database']['path']).resolve(strict=True) == database, 'publication receipt database differs')
    selected = top['selection']
    linked_path({k: selected[k] for k in ('path', 'sha256')})
    require(selected['document'] == selection, 'publication receipt selection differs')
    require([r['season'] for r in top['seasons']] == list(SEASONS), 'publication receipt seasons differ')
    receipts = {}
    for row in top['seasons']:
        reference = dict(path=str(database.parent / row['receipt']['path']), sha256=row['receipt']['sha256'])
        receipt = read_json(linked_path(reference))
        require(receipt['season'] == row['season'] and receipt['publication_id'] == top['publication_id']
                and receipt['corpus_sha256'] == row['corpus_sha256'], 'season receipt binding differs')
        receipts[row['season']] = (reference, receipt)
    return top, receipts


def _correspondence(original, selected, recovery):
    """the explicit recovery selection is the sole source of bundle replacements."""
    for old, new in zip(original['corpora'], selected['corpora']):
        require(old['season'] == new['season'], 'selected season order differs')
        if old['season'] != '20242025' or recovery['summary']['recovered_games'] == 0:
            require(old == new, 'unrecovered corpus selection changed')
    old_ref = next(r for r in original['corpora'] if r['season'] == '20242025')
    new_ref = next(r for r in selected['corpora'] if r['season'] == '20242025')
    old_path, new_path = (linked_path({k: ref[k] for k in ('path', 'sha256')}) for ref in (old_ref, new_ref))
    require(recovery['consumed']['corpus'] == {k:old_ref[k] for k in ('path','sha256')},
            'recovery original corpus reference differs from original selection')
    old_corpus, old_inventory, old_ledger = load_corpus(old_path, [])
    new_corpus, new_inventory, new_ledger = load_corpus(new_path, [])
    require(old_inventory == new_inventory and old_corpus['reference'] == new_corpus['reference'],
            'recovery changed inventory or season references')
    if recovery['summary']['recovered_games']:
        require(Path(new_corpus['games_root']) == Path(recovery['selected_games']),
                'selected corpus games root differs from recovery tree')
    unchanged = 0
    for row in recovery['games']:
        gid = row['game_id']
        chosen = Path(row['selected_path']).resolve(strict=True)
        require(Path(new_ledger[gid]['capture_path']).resolve(strict=True) == chosen,
                f'{gid}: selected corpus bundle differs from recovery tree')
        if row['disposition'] != 'recovered':
            require(old_ledger[gid]['status'] == new_ledger[gid]['status'], f'{gid}: unchanged native status differs')
            if old_ledger[gid]['output_path'] is not None:
                old = read_json(old_path.parent / old_ledger[gid]['output_path'])
                new = read_json(new_path.parent / new_ledger[gid]['output_path'])
                require(_admission(old) == _admission(new), f'{gid}: unchanged native facts differ')
            unchanged += 1
    return dict(inventory_games=len(new_inventory), unchanged_native_games=unchanged,
                recovered_games=recovery['summary']['recovered_games'], tree_checked=True)


def _result_rows(result, table):
    keys = TABLES[table]
    rows = getattr(result, RESULT_FIELDS[table])
    def key(row):
        row = row if isinstance(row, dict) else vars(row) if hasattr(row, '__dict__') else asdict(row)
        return tuple(row[k] for k in keys)
    for row in sorted(rows, key=key):
        yield stored_row(row, result.season)


def _sql_rows(connection, table, season):
    return (dict(r) for r in connection.execute(
        f'SELECT * FROM {table} WHERE season=? ORDER BY {",".join(TABLES[table])}', (season,)))


def _canonical(row):
    return {key: strict_json(value.encode()) if key.endswith('_json') and value is not None else value
            for key, value in row.items()}


def _verify_selected(connection, result, purpose):
    for table in TABLES:
        actual = iter(_sql_rows(connection, table, result.season))
        for expected in _result_rows(result, table):
            row = next(actual, None)
            require(row is not None and _canonical(row) == _canonical(expected),
                    f'{result.season}/{table}: final schema-5 readback differs')
        require(next(actual, None) is None, f'{result.season}/{table}: extra final rows')
    evidence = dict(connection.execute('SELECT * FROM season WHERE season=?', (result.season,)).fetchone())
    require(evidence['corpus_sha256'] == result.corpus_sha256
            and strict_json(evidence['coverage_json'].encode()) == result.coverage
            and strict_json(evidence['spatial_coverage_json'].encode()) == result.spatial_coverage
            and evidence['source_requested_min'] == result.source_requested_min
            and evidence['source_requested_max'] == result.source_requested_max
            and evidence['undated_sources'] == result.undated_sources
            and strict_json(evidence['source_implementations_json'].encode()) == list(result.source_implementations),
            f'{result.season}: final season evidence differs')
    return check_season(connection, result, purpose)


def _missing_spatial(table, key, connection, policy, season):
    pid = key[0]
    if table == 'player_game_spatial':
        parent_key = (pid, key[1])
        if policy is not None:
            parent = policy.get(parent_key)
        else:
            row = connection.execute('SELECT * FROM player_game WHERE season=? AND player_id=? AND game_id=?',
                                     (season, *parent_key)).fetchone()
            parent = dict(row) if row is not None else None
    else:
        if policy is not None:
            parent = policy.get((pid,))
        else:
            row = connection.execute('SELECT * FROM player_season WHERE season=? AND player_id=?',
                                     (season, pid)).fetchone()
            parent = dict(row) if row is not None else None
    if parent is None:
        return {}, 'entity_absent'
    available = parent['spatial_unblocked_for'] is not None
    return dict(for_count=0 if available else None, against_count=0 if available else None), (
        'sparse_zero' if available else 'spatial_support_unavailable')


def _quantity(field):
    support = 'personal' if field.startswith('personal_') else 'spatial' if field.startswith('spatial_') else 'on_ice'
    if field.startswith('league_'):
        support = 'spatial_reference'
    if 'second' in field:
        unit = 'seconds'
    elif 'density' in field or 'difference' in field:
        unit = 'attempts_per_60_per_100_square_feet'
    elif 'per60' in field:
        unit = 'attempts_per_60'
    elif 'count' in field or 'attempt' in field or field in ('personal_goals', 'personal_shots_on_goal', 'personal_primary_assists'):
        unit = 'recorded_counts'
    else:
        unit = 'status_or_identity'
    return support, unit


def _compare_tables(original, policy, selected, season, writer):
    """merge exact identities; sparse zeros require an available parent support."""
    changed = {phase: defaultdict(set) for phase, _, _ in PHASES}
    quantities = Counter()
    parent_policy = {
        'player_game_spatial': {(r.player_id, r.game_id): stored_row(r, season) for r in policy.player_games},
        'player_season_spatial': {(r.player_id,): stored_row(r, season) for r in policy.player_seasons},
    }
    for table, keys in TABLES.items():
        iterators = [_sql_rows(original, table, season), _result_rows(policy, table), _sql_rows(selected, table, season)]
        def tag(rows, state):
            for row in rows:
                yield tuple(row[k] for k in keys), state, row
        merged = heapq.merge(*(tag(rows, state) for state, rows in enumerate(iterators)), key=lambda r: (r[0], r[1]))
        import itertools
        for key, group in itertools.groupby(merged, key=lambda item: item[0]):
            states = [None, None, None]
            for _, state, row in group:
                require(states[state] is None, 'duplicate observed entity')
                states[state] = _canonical(row)
            identity_fields = dict(zip(keys, key))
            absent = [None, None, None]
            if table in parent_policy:
                for state in range(3):
                    if states[state] is None:
                        states[state], absent[state] = _missing_spatial(table, key,
                            original if state == 0 else selected, parent_policy[table] if state == 1 else None, season)
            fields = set().union(*(row.keys() for row in states if row is not None)) - set(keys) - {'season'}
            for field in sorted(fields):
                values = [row.get(field) if row is not None else None for row in states]
                if values[0] == values[1] == values[2]:
                    continue
                if season == '20252026' and any(type(v) in (int, float) for v in values):
                    raise InputContractError(f'{season}/{table}/{key}/{field}: unexpected numerical change')
                delta = change(*values)
                support, unit = _quantity(field)
                if 'second' in field:
                    unit = 'physical_seconds' if table == 'game' else 'player_seconds'
                if table in ('spatial_cell', 'player_game_spatial', 'player_season_spatial'):
                    support = 'spatial_reference' if table == 'spatial_cell' else 'spatial'
                entity = 'league_reference' if table == 'spatial_cell' else 'player_game' if table == 'player_game_spatial' else 'player_season' if table in ('player', 'player_season_spatial') else table
                for phase, before, after in PHASES:
                    if values[before] == values[after]:
                        continue
                    difference = delta[{'policy_only':'policy_delta','recovery':'recovery_delta','total':'total_delta'}[phase]]
                    reason = delta['reason'] or ('ratio_status_or_identity' if difference is None else None)
                    if absent[before] or absent[after]:
                        reason = ';'.join(v for v in (absent[before], absent[after]) if v)
                    writer.writerow(dict(phase=phase, entity=entity, season=season,
                        game_id=identity_fields.get('game_id'), player_id=identity_fields.get('player_id'),
                        cell_id=identity_fields.get('cell_id'), support=support, quantity=field.removesuffix('_json'),
                        unit=unit, before=_csv_value(values[before]), after=_csv_value(values[after]),
                        delta=difference, reason=reason,
                        original=_csv_value(values[0]), policy_only=_csv_value(values[1]), selected=_csv_value(values[2]),
                        component=table))
                    entity_key = tuple(identity_fields[k] for k in {
                        'game': ('game_id',), 'player_game': ('player_id','game_id'),
                        'player_season': ('player_id',), 'league_reference': ('cell_id',),
                    }[entity])
                    changed[phase][entity].add(entity_key)
                    quantities[phase] += 1
    return {phase: dict(changed_entities={name:len(ids) for name,ids in by_entity.items()},
                        changed_quantities=quantities[phase]) for phase, by_entity in changed.items()}


def _csv_value(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) if isinstance(value, (dict, list, bool)) else value


def _peers(players, summaries):
    """execute the application owner, then independently verify its exact convention."""
    import shutil
    import subprocess
    app = SPEC.parents[2] / 'app'
    pinned = Path.home() / '.local/share/mise/installs/node/24.21.0/bin/node'
    node = str(pinned) if pinned.is_file() else shutil.which('node')
    require(node is not None, 'peer owner requires pinned node 24.21.0')
    require(subprocess.run([node, '--version'], capture_output=True, text=True, check=True).stdout.strip() == 'v24.21.0',
            'peer owner requires pinned node 24.21.0')
    identities = {p['player_id']: p for p in players}
    rows = []
    for summary in summaries:
        row = _canonical(summary)
        personal = {k.removeprefix('personal_'): v for k,v in row.items() if k.startswith('personal_')}
        metrics = {k:v for k,v in row.items() if not k.startswith(('personal_', 'spatial_'))}
        rows.append(dict(player_id=row['player_id'], display_name=identities[row['player_id']]['display_name'],
                         reported_position=identities[row['player_id']]['reported_position'], metrics=metrics, personal=personal))
    script = """
import {readFileSync} from 'node:fs';
import {selectPeerGroups, observedStanding, observedMetrics} from './src/web/observed-comparison.ts';
const players=JSON.parse(readFileSync(0,'utf8'));
const selected=['f','d'].map(key=>players.find(p=>(p.reported_position==='D'?'d':'f')===key)).filter(Boolean);
const output=[];
for(const population of ['onIce','personal']) {
 const groups=selectPeerGroups(players,selected,{peers:'position',peerMin:300},population);
 for(const player of players) {
  const key=player.reported_position==='D'?'d':'f';
  const group=groups.find(g=>g.key===key);
  for(const metric of observedMetrics.filter(m=>m.population===population)) {
   const rate=metric.rate(player);
   const standing=observedStanding(rate,player.player_id,group,metric.key);
   output.push({player_id:player.player_id,position_group:key,metric:metric.key,population,
    rate,eligibility:standing.kind,percentile:standing.kind==='ranked'?standing.percentile:null,
    cohort_size:group.members.length});
  }
 }
}
process.stdout.write(JSON.stringify(output));
"""
    execution = subprocess.run([node, '--import', 'tsx', '--input-type=module', '--eval', script],
        cwd=app, input=json.dumps(rows, allow_nan=False), capture_output=True, text=True)
    require(execution.returncode == 0, 'application peer owner failed: ' + execution.stderr[-2000:])
    actual = strict_json(execution.stdout.encode())
    metric_names = dict(for60='for_per60', against60='against_per60', sog60='shots_on_goal_per60',
                        goals60='goals_per60', primaryAssists60='primary_assists_per60')
    index = {r['player_id']:r for r in rows}
    cohorts = {}
    for population, names in (('onIce', ('for_per60','against_per60')),
                              ('personal', ('shots_on_goal_per60','goals_per60','primary_assists_per60'))):
        for position in ('f','d'):
            members = [r for r in rows if ('d' if r['reported_position'] == 'D' else 'f') == position
                       and r['metrics' if population == 'onIce' else 'personal']['included_seconds'] >= 18000
                       and all(r['metrics' if population == 'onIce' else 'personal'][name] is not None for name in names)]
            cohorts[population,position] = members
    require(len(actual) == 5*len(rows) and len({(r['player_id'],r['metric']) for r in actual}) == len(actual),
            'application peer inventory differs')
    for row in actual:
        player = index[row['player_id']]
        support = 'metrics' if row['population'] == 'onIce' else 'personal'
        rate = player[support][metric_names[row['metric']]]
        position = 'd' if player['reported_position'] == 'D' else 'f'
        cohort = cohorts[row['population'],position]
        member = row['player_id'] in {p['player_id'] for p in cohort}
        eligibility = 'unavailable' if rate is None else 'ranked' if member else 'outside'
        distribution = sorted(p[support][metric_names[row['metric']]] for p in cohort)
        percentile = 100*((bisect_left(distribution,rate)+bisect_right(distribution,rate))/2)/len(cohort) if member else None
        require(row['position_group'] == position and row['rate'] == rate and row['eligibility'] == eligibility
                and row['percentile'] == percentile and row['cohort_size'] == len(cohort),
                'independent default peer arithmetic differs')
    return {(r['player_id'],r['metric']): r for r in actual}


def _peer_consequences(states, season, writer):
    keys = set().union(*(state.keys() for state in states))
    changes = Counter()
    for key in sorted(keys):
        values = [state.get(key) for state in states]
        for phase, i, j in PHASES:
            if values[i] == values[j]:
                continue
            before, after = values[i] or {}, values[j] or {}
            reason = 'entity_absent' if values[i] is None or values[j] is None else (
                'direct_rate_or_eligibility' if any(before.get(k) != after.get(k) for k in ('rate','eligibility','position_group'))
                else 'peer_reference_consequence')
            writer.writerow(dict(phase=phase, season=season, position_group_before=before.get('position_group'),
                position_group_after=after.get('position_group'), minute_cutoff=300, metric=key[1], player_id=key[0],
                eligibility_before=before.get('eligibility'), eligibility_after=after.get('eligibility'),
                rate_before=before.get('rate'), rate_after=after.get('rate'), percentile_before=before.get('percentile'),
                percentile_after=after.get('percentile'), cohort_size_before=before.get('cohort_size'),
                cohort_size_after=after.get('cohort_size'), reason=reason,
                original=_csv_value(values[0]), policy_only=_csv_value(values[1]), selected=_csv_value(values[2])))
            changes[phase] += 1
    return dict(changes)


def _verify_envelope(reference):
    path = linked_path(reference)
    envelope = read_json(path)
    require(envelope.get('schema_version') == 4, 'frozen source requires native schema 4')
    inputs = envelope['interpreted']['inputs']
    require(len(inputs) == 6 and {r['source'] for r in inputs} == set(SOURCES), 'native source inventory differs')
    for row in inputs:
        captured = read_capture(Path(row['capture_path']).parent.parent, row['source'])
        require(captured.body_sha256 == row['body_sha256'] and captured.http_status == row['http_status']
                and captured.requested_game_id == envelope['interpreted']['requested_game_id'],
                'bound envelope source identity differs from source body/receipt')
    return envelope


def _research_metadata(result_path):
    result = read_json(result_path)
    require(result['schema_version'] == 2 and result['kind'] == 'attribution_revision_result'
            and result['purpose'] == 'research', 'expected frozen 04b result')
    clean_implementation(result['implementation'])
    prepared_ref = result['evidence']['prepared']
    prepared = read_json(linked_path(prepared_ref))
    require(prepared['schema_version'] == 2 and prepared['kind'] == 'attribution_revision_prepared'
            and prepared['purpose'] == 'research', 'expected corrected frozen preparation')
    clean_implementation(prepared['implementation'])
    baseline_ref = prepared['baseline_prepared']
    baseline = read_json(linked_path(baseline_ref))
    require(baseline['schema_version'] == 1 and baseline['kind'] == 'attribution_prepared'
            and baseline['purpose'] == 'research', 'expected frozen baseline preparation')
    clean_implementation(baseline['implementation'])
    for field in ('selection', 'population_ids', 'seasons', 'populations', 'games_by_season', 'ledgers'):
        require(prepared[field] == baseline[field], 'corrected preparation changed source ledger binding: ' + field)
    protocol = read_json(linked_path(prepared['protocol']))
    require(protocol['baseline_prepared'] == baseline_ref and prepared['protocol'] == result['protocol'],
            '04b protocol/preparation source binding differs')
    require(prepared['populations'] == ['all_attempts', 'unblocked_spatial'], 'frozen populations differ')
    ledgers = prepared['ledgers']
    require(all(name in ledgers for name in ('segments','events','coverage')), 'frozen ledgers unavailable')
    # no annual arrays, grouped moments, references matrices, fits or refits are opened.
    return prepared, dict(result=identity(result_path), prepared=prepared_ref, baseline=baseline_ref,
                          protocol=prepared['protocol'], ledgers={k:ledgers[k] for k in ('segments','events','coverage')},
                          directed_rows=ledgers['rows'])


def _research_impact(result_path, incidents, output):
    """missing evidence stays pending; verified different evidence forbids projection."""
    game_ids = TARGETS | {r['game_id'] for r in incidents}
    report = dict(schema_version=1, kind='source_exposure_research_impact', policy_id=POLICY,
        research_impact='pending', references=dict(result=identity(result_path)) if result_path.is_file() else {},
        scope=dict(game_ids=sorted(game_ids), populations=['all_attempts','unblocked_spatial'],
                   incident_states=['original','selected'], counts='recorded attempts', physical_time='seconds',
                   directed_time='two attacking directions per physical second', player_time='ten skaters per physical second'),
        games=[], unresolved=[], hypothetical_reprocessing='unassessed', fitted_effects='unassessed',
        league_references='unassessed', scales='unassessed', predictive_consequences='unassessed')
    try:
        prepared, references = _research_metadata(result_path)
        report['references'] = references
        ledger = {}
        for name, reference in references['ledgers'].items():
            grouped = defaultdict(list)
            for row in ledger_rows(reference, game_ids):
                grouped[row['game_id']].append(row)
            ledger[name] = grouped
        years = {gid[:4]+str(int(gid[:4])+1) for gid in game_ids}
        selected_rows = [r for r in references['directed_rows'] if r['season'] in years]
        require({(r['population'],r['season']) for r in selected_rows}
                == {(p,y) for p in prepared['populations'] for y in years}
                and len(selected_rows) == len(years)*len(prepared['populations']),
                'required frozen directed-row ledger inventory differs')
        directed = defaultdict(lambda: defaultdict(list))
        for item in selected_rows:
            for row in ledger_rows(item['reference'],game_ids):
                require(row['population'] == item['population'] and row['season'] == item['season'],
                        'frozen directed-row population/season differs')
                directed[item['population']][row['game_id']].append(row)
        report['references']['directed_rows'] = selected_rows
        game_refs = {}
        for row in prepared['inputs']:
            if row['kind'] == 'game' and Path(row['path']).stem in game_ids:
                gid = Path(row['path']).stem
                require(gid not in game_refs, 'duplicate frozen input game')
                game_refs[gid] = {k:row[k] for k in ('path','sha256')}
        by_game = defaultdict(list)
        for row in incidents:
            by_game[row['game_id']].append(row)
        for gid in sorted(game_ids):
            coverage_rows = ledger['coverage'].get(gid, [])
            entry = dict(game_id=gid, missing_shift_target=gid in TARGETS, frozen_source=game_refs.get(gid),
                         frozen_disposition=None, incidents=[], source_status='unresolved')
            report['games'].append(entry)
            try:
                require(len(coverage_rows) == 1 and gid in game_refs, 'required frozen game/coverage evidence unavailable')
                coverage = coverage_rows[0]
                require(Path(coverage['source']).resolve(strict=True) == linked_path(game_refs[gid]),
                        'frozen coverage does not bind its original source envelope')
                frozen = _verify_envelope(game_refs[gid])
                require(frozen['interpreted']['requested_game_id'] == gid, 'frozen source game identity differs')
                entry['frozen_disposition'] = {k:coverage[k] for k in ('native_coverage','populations','unresolved_membership_seconds','unknown_horizon_periods')}
                entry['frozen_coverage'] = coverage
                if gid in TARGETS:
                    empty = any(c['name'] == 'shift_collection' and c['status'] == 'match'
                                and c['observed'] == c['expected'] == 0 for c in frozen['interpreted']['checks'])
                    entry['frozen_shift_source_empty'] = empty
                    if empty:
                        require(all(not directed[p].get(gid) and not any(
                            s['classification'] == 'five_on_five' and not s['masks'][p]
                            for s in ledger['segments'].get(gid,[])) for p in prepared['populations']),
                            'frozen empty-shift game has admitted segments or directed rows')
                for incident in by_game[gid]:
                    measured = {k:v for k,v in incident.items() if k != 'source'}
                    entry['incidents'].append(measured)
                    try:
                        observed = _verify_envelope(incident['source'])
                        concordance = source_concordance(observed, frozen)
                        measured.update(concordance)
                        measured['source'] = incident['source']
                        measured['populations'] = None
                        if concordance['source_status'] == 'concordant':
                            api = {e['source_index']:e for e in frozen['interpreted']['events'] or []}
                            native = {e['source_index']:e for e in frozen['reconstruction']['events'] or []}
                            for event in ledger['events'].get(gid, []):
                                source = api.get(event['source_index'])
                                reconstruction = native.get(event['source_index'])
                                require(source is not None and reconstruction is not None
                                        and event['event_id'] == source['event_id'] and event['type'] == source['type_key']
                                        and event['period'] == source['period_number'] and event['clock'] == source['elapsed_seconds']
                                        and event['classification'] == reconstruction['classification']
                                        and event['report_source_index'] == reconstruction['report_source_index']
                                        and event['interval_indices'] == reconstruction['interval_indices'],
                                        'frozen event ledger/source admission differs')
                            measured['populations'] = {population: intersect_runs(incident['runs'],
                                ledger['segments'].get(gid, []), ledger['events'].get(gid, []), population,
                                directed_rows=directed[population].get(gid, []),game=frozen['interpreted']['game'])
                                for population in prepared['populations']}
                        elif concordance['source_status'] == 'different_frozen_evidence':
                            measured['projection'] = 'not_transferred_different_frozen_evidence'
                        else:
                            report['unresolved'].append(dict(game_id=gid, state=incident['state'], reason=concordance['reason']))
                    except (InputContractError, OSError, KeyError, TypeError, ValueError) as error:
                        measured.update(source_status='unresolved', populations=None, reason=str(error))
                        report['unresolved'].append(dict(game_id=gid, state=incident['state'], reason=str(error)))
                statuses = {r['source_status'] for r in entry['incidents']}
                entry['source_status'] = 'unresolved' if 'unresolved' in statuses else (
                    'different_frozen_evidence' if 'different_frozen_evidence' in statuses else 'concordant')
            except (InputContractError, OSError, KeyError, TypeError, ValueError) as error:
                entry['reason'] = str(error)
                report['unresolved'].append(dict(game_id=gid, reason=str(error)))
        report['research_impact'] = 'pending' if report['unresolved'] else 'verified'
    except (InputContractError, OSError, KeyError, TypeError, ValueError) as error:
        report['unresolved'].append(dict(scope='required_frozen_metadata_or_full_ledger_hash', reason=str(error)))
    write_json(output / 'research-impact.json', report)
    return report


def _incident_inputs(states):
    """all empty targets and disagreement games require source comparison, even without lost runs."""
    games = set(TARGETS)
    for rows in states.values():
        for row in rows.values():
            if any(c['temporal_case'] == 'interior' or c['shift_relation'] == 'neither'
                   for c in row['receipt'].get('exposure_conflicts', [])):
                games.add(row['receipt']['game_id'])
    incidents, boundaries = [], []
    for state, rows in states.items():
        for gid, row in sorted(rows.items()):
            receipt = row['receipt']
            conflicts = receipt.get('exposure_conflicts', [])
            for conflict in conflicts:
                if conflict['temporal_case'] == 'boundary':
                    boundaries.append(dict(state=state, game_id=gid, **conflict))
            if gid not in games:
                continue
            run_indices = {index for c in conflicts if c['temporal_case'] == 'interior' for index in c['segment_indices']}
            incidents.append(dict(state=state, game_id=gid, source=row['source'],
                runs=[receipt['segments'][i] for i in sorted(run_indices)],
                source_locators=[c for c in conflicts if c['temporal_case'] == 'interior' or c['shift_relation'] == 'neither'],
                native_status=receipt['status'], missing_shift_target=gid in TARGETS))
    require(all((state,gid) in {(r['state'],r['game_id']) for r in incidents}
                for state in ('original','selected') for gid in games),
            'incident union lacks required observed state source evidence')
    return incidents, dict(diagnostics=boundaries, counts_by_state_relation=[
        dict(state=state, shift_relation=relation, events=count)
        for (state,relation),count in sorted(Counter((r['state'],r['shift_relation']) for r in boundaries).items())],
        interpretation='boundary before/after/both are membership diagnostics; neither marks disagreement; none removes time',
        required_examples=sorted(BOUNDARIES))


def _state_receipts(result):
    sources = {Path(row['path']).stem:{k:row[k] for k in ('path','sha256')}
               for row in result.receipt['consumed'] if row['kind'] == 'reconstruction'}
    return {row['game_id']:dict(receipt=row, source=sources.get(row['game_id'])) for row in result.receipt['games']}


def _season_summary(connection, season):
    games = [dict(r) for r in connection.execute('SELECT * FROM game WHERE season=?', (season,))]
    quantities = {}
    for prefix in ('','personal_','spatial_'):
        for name in ('included_seconds','known_excluded_seconds'):
            field = prefix+name
            quantities[field] = sum(row[field] for row in games)
    for field in ('away_attempts','home_attempts','spatial_away_unblocked','spatial_home_unblocked'):
        available = [row[field] for row in games if row[field] is not None]
        quantities[field] = dict(available_count_sum=sum(available) if available else None,
                                unavailable_games=sum(row[field] is None for row in games))
    return dict(inventory_games=len(games), physical=quantities)


def assess(args):
    """write fresh receipts and measured consequences, without activation or research reprocessing."""
    import csv
    from source_exposure import validate_recovery
    started = time.monotonic()
    producer = implementation()
    clean_implementation(producer)
    original_path, _, original, _ = read_selection(args.original_selection)
    selected_path, _, selection, _ = read_selection(args.selected_selection)
    require(original['purpose'] == selection['purpose'] == 'real', 'assessment requires real three-season selections')
    require(identity(original_path)['sha256'] == SELECTION_SHA256, 'original selection is not the pinned 05g input')
    baseline = Path(args.baseline).resolve(strict=True)
    candidate = Path(args.candidate).resolve(strict=True)
    require(baseline != candidate and identity(baseline)['sha256'] == BASELINE_SHA256,
            'baseline is not the pinned read-only schema-4 05g database')
    recovery_path = Path(args.recovery).resolve(strict=True)
    old_2024 = next(row for row in original['corpora'] if row['season'] == '20242025')
    recovery = validate_recovery(recovery_path, corpus_path=old_2024['path'])
    correspondence = _correspondence(original, selection, recovery)
    attribution_result = Path(args.attribution_result).absolute()
    inputs = dict(original_selection=identity(original_path), selected_selection=identity(selected_path),
                  baseline=identity(baseline), candidate=identity(candidate), recovery=identity(recovery_path),
                  attribution_result=identity(attribution_result) if attribution_result.is_file() else None)
    out = output_path(args.out, [str(baseline.parent),str(candidate.parent),str(recovery_path.parent),
        *(str(Path(r['path']).parent) for s in (original,selection) for r in s['corpora'])])
    out.mkdir()
    with (out/'spec.md').open('xb') as snapshot:
        snapshot.write(SPEC.read_bytes())
    original_top, original_receipts = _receipts(baseline, original)
    selected_top, selected_receipts = _receipts(candidate, selection)
    comparisons, peers, full_receipts, summaries = {}, {}, [], {}
    states = {'original':{}, 'selected':{}}
    delta_fields = ['phase','entity','season','game_id','player_id','cell_id','support','quantity','unit',
                    'before','after','delta','reason','original','policy_only','selected','component']
    peer_fields = ['phase','season','position_group_before','position_group_after','minute_cutoff','metric','player_id',
                   'eligibility_before','eligibility_after','rate_before','rate_after','percentile_before','percentile_after',
                   'cohort_size_before','cohort_size_after','reason','original','policy_only','selected']
    with closing(_read_database(baseline,4,'real')[0]) as old_db, closing(_read_database(candidate,5,'real')[0]) as new_db, \
         (out/'observed-deltas.csv').open('x',newline='') as deltas, (out/'peer-consequences.csv').open('x',newline='') as peer_file:
        delta_writer = csv.DictWriter(deltas,fieldnames=delta_fields); delta_writer.writeheader()
        peer_writer = csv.DictWriter(peer_file,fieldnames=peer_fields); peer_writer.writeheader()
        require(original_top['publication_id'] == old_db.execute('SELECT publication_id FROM publication').fetchone()[0]
                and selected_top['publication_id'] == new_db.execute('SELECT publication_id FROM publication').fetchone()[0],
                'publication receipt/database identity differs')
        for old_ref,new_ref in zip(original['corpora'], selection['corpora']):
            season = old_ref['season']
            receipt_ref, old_receipt = original_receipts[season]
            old_evidence = dict(old_db.execute('SELECT * FROM season WHERE season=?',(season,)).fetchone())
            require(old_evidence['corpus_sha256'] == old_ref['sha256'] == old_receipt['corpus_sha256'],
                    'pinned original corpus/receipt differs')
            check_season(old_db, SimpleNamespace(season=season, receipt=old_receipt,
                spatial_coverage=strict_json(old_evidence['spatial_coverage_json'].encode()),
                coverage=strict_json(old_evidence['coverage_json'].encode())), 'real')
            print(f'assessing {season}: authoritative policy-only aggregate', file=sys.stderr, flush=True)
            policy = aggregate(old_ref['path'],'real',season,old_ref['sha256'])
            policy_path = out / f'policy-only-{season}.json'
            write_json(policy_path, dict(schema_version=1,kind='source_exposure_policy_only_receipt',
                implementation=producer,policy_id=POLICY,corpus={k:old_ref[k] for k in ('path','sha256')},
                **policy.receipt,coverage=policy.coverage,spatial_coverage=policy.spatial_coverage))
            full_receipts.append(dict(season=season,state='policy_only',reference=identity(policy_path)))
            chosen = policy if old_ref == new_ref else aggregate(new_ref['path'],'real',season,new_ref['sha256'])
            checks = _verify_selected(new_db,chosen,'real')
            selected_ref, selected_receipt = selected_receipts[season]
            require(selected_receipt['games'] == chosen.receipt['games']
                    and selected_receipt['aggregate_identities'] == chosen.receipt['aggregate_identities'],
                    f'{season}: final candidate receipts differ from authoritative aggregation')
            comparisons[season] = _compare_tables(old_db,policy,new_db,season,delta_writer)
            peer_states = [_peers(list(_sql_rows(old_db,'player',season)), list(_sql_rows(old_db,'player_season',season))),
                _peers(list(_result_rows(policy,'player')),list(_result_rows(policy,'player_season'))),
                _peers(list(_sql_rows(new_db,'player',season)),list(_sql_rows(new_db,'player_season',season)))]
            peer_path = out/f'peer-states-{season}.json'
            write_json(peer_path,dict(season=season,states={name:list(rows.values()) for name,rows in
                zip(('original','policy_only','selected'),peer_states)},independent_arithmetic='passed'))
            peers[season] = dict(changes=_peer_consequences(peer_states,season,peer_writer),states=identity(peer_path))
            summaries[season] = dict(original=_season_summary(old_db,season),
                policy_only=policy.receipt['aggregate_identities'],selected=_season_summary(new_db,season),readback=checks)
            original_rows, chosen_rows = _state_receipts(policy), _state_receipts(chosen)
            states['original'].update(original_rows); states['selected'].update(chosen_rows)
            full_receipts.extend([dict(season=season,state='original',reference=receipt_ref),
                                  dict(season=season,state='selected',reference=selected_ref)])
            del policy, chosen, peer_states
    incidents, boundaries = _incident_inputs(states)
    write_json(out/'boundary-diagnostics.json',boundaries)
    research = _research_impact(attribution_result,incidents,out)
    # input files and clean producer must still be the identities assessed.
    require(implementation() == producer, 'assessment implementation changed during execution')
    for name,path in (('baseline',baseline),('candidate',candidate),('original_selection',original_path),
                      ('selected_selection',selected_path),('recovery',recovery_path)):
        require(identity(path) == inputs[name], f'{name}: assessment input changed during execution')
    report = dict(schema_version=1,kind='source_exposure_result',purpose='research',implementation=producer,
        spec=identity(out/'spec.md'),consumed=inputs,policy_id=POLICY,
        execution_status='complete' if research['research_impact']=='verified' else 'incomplete',candidate_status='ready',
        recovery_status=recovery['summary']['recovery_status'],recovery=recovery['summary'],
        correspondence=correspondence,observed_deltas=comparisons,peer_consequences=peers,season_summaries=summaries,
        receipts=full_receipts,research_impact=research['research_impact'],
        outputs={name:identity(out/name) for name in ('observed-deltas.csv','peer-consequences.csv',
            'research-impact.json','boundary-diagnostics.json')},
        activation='not_run',admission='not_admitted',handoff=None,resources=resources(started),
        limitations=['source support only; no physical truth or fitted-result sensitivity claim',
                    'recovery eligibility, fitted effects, research league references, scales and prediction remain unassessed',
                    'strict effect/browser acceptance is a separate root verification boundary'])
    write_json(out/'result.json',report)
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    for name in ('original-selection','selected-selection','baseline','candidate','recovery','attribution-result','out'):
        parser.add_argument('--'+name,required=True,action=Once)
    args=parser.parse_args(argv)
    try:
        result=assess(args)
        print(json.dumps({key:result[key] for key in ('execution_status','candidate_status','recovery_status','research_impact')}))
        return 0 if result['execution_status']=='complete' else 1
    except (InputContractError,OSError,ValueError,KeyError,TypeError) as error:
        print(f'source exposure assessment failed: {error}',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
