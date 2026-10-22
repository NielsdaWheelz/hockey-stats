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
from hockey_stats.publication import _check_season, _selection, _stored

SPEC = Path(__file__).resolve().parents[2] / 'docs/specs/02d-source-exposure-consistency.md'
POLICY = 'strict_interior_other_strength_v1'
SEASONS = ('20232024', '20242025', '20252026')
TARGETS = frozenset(str(g) for g in range(2024021235, 2024021292))
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
METRICS = ('for_per60', 'against_per60', 'personal_shots_on_goal_per60',
           'personal_goals_per60', 'personal_primary_assists_per60')


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
                if k not in ('capture_path', 'requested_at', 'interpretation', 'implementation')}
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
            if row.get('status') == 'parsed' and row.get('body_sha256') is None:
                return dict(source_status='unresolved', reason=f'{label}_body_identity_unavailable')
            if row.get('body_sha256') is not None:
                digest(row['body_sha256'])
        if not value['interpreted'].get('game'):
            return dict(source_status='unresolved', reason=f'{label}_game_identity_unavailable')
    left = {r['source']: r for r in observed['interpreted']['inputs']}
    right = {r['source']: r for r in frozen['interpreted']['inputs']}
    for source in SOURCES:
        if _admission(left[source]) != _admission(right[source]):
            differences.append(source)
    if _admission(observed['interpreted']) != _admission(frozen['interpreted']):
        differences.append('interpreted_admission')
    if observed.get('reconstruction') != frozen.get('reconstruction'):
        differences.append('native_admission')
    return dict(source_status='different_frozen_evidence' if differences else 'concordant',
                reason='bound_bodies_or_admission_differ' if differences else None,
                differences=differences)


def intersect_runs(runs, segments, events, population):
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
    for row in selected:
        index = row['segment_index']
        duration = row['end'] - row['start']
        masks = row['masks'][population]
        require(isinstance(masks, list), 'frozen mask must be an array')
        counts = row['counts']
        assigned = by_segment[index]
        total = 0
        for side in ('away', 'home'):
            relevant = [e for e in assigned if e['side'] == side and e[population] != 'out_of_scope']
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
                require(Counter(e['cell_id'] for e in relevant) == expected_cells,
                        'frozen spatial counts differ from exact event assignment')
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
    return dict(newly_excluded_physical_seconds=losses, newly_excluded_directed_seconds=2*losses,
        newly_excluded_player_seconds=10*losses, already_excluded_physical_seconds=prior,
        already_excluded_directed_seconds=2*prior, already_excluded_player_seconds=10*prior,
        newly_excluded_attempts=len(lost), already_excluded_attempts=len(excluded),
        newly_excluded_player_for=len(lost)*5, newly_excluded_player_against=len(lost)*5,
        affected_players=[dict(player_id=pid, lost_seconds=seconds) for pid, seconds in sorted(players.items())],
        lost_retained_events=lost, already_excluded_events=excluded, segments=ledger_receipts)
