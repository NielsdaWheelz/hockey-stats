"""audit admitted source rows and prepared populations without fitting.

review schema 1 keeps three denominators separate: interpreted source rows,
matched api events, and prepared attempts (including explicit exclusions).
counts are stratified rows; count is the number of records with those exact
dimensions. source locators refer to the consumed reconstruction envelopes.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
from pathlib import Path
import sys

from hockey_stats.artifacts import implementation_identity, write_json
from hockey_stats.captures import InputContractError, strict_json
from hockey_stats.chance_cli import output_path
from hockey_stats.chance_data import prepare
from hockey_stats.cli import Once
from hockey_stats.reconstruct import REPORT_CODES, canonical_shot_type


DENOMINATORS = {
    'api_events': 'all interpreted api events in selected admitted games',
    'report_rows': 'all interpreted report rows, including unjoined rows',
    'prepared_attempts': 'recognized attempts, including excluded and unavailable records',
    'landing_rows': 'all interpreted scoring-summary rows, including deficient and duplicate rows',
    'goal_modifier_evidence': 'reconstructed api goals, including unmatched shootout goals',
}


def count_rows(counter, fields):
    return [dict(zip(fields, key), count=count)
            for key, count in sorted(counter.items(), key=lambda row: repr(row[0]))]


_COUNT_FIELDS = {
    'api_events': ('season', 'kind', 'kind_valid', 'match_status'),
    'report_rows': ('season', 'event_code', 'shot_type', 'match_status'),
    'prepared_attempts': ('season', 'kind', 'match_status', 'type_evidence_status', 'shot_type', 'status'),
    'landing_availability': ('season', 'status'),
    'landing_rows': ('season', 'period_type', 'goal_modifier'),
    'goal_modifier_evidence': ('season', 'period_type', 'status', 'reported_value'),
    'shot_type_observations': ('season', 'kind', 'source', 'reported_value'),
}

_LOCATED_FIELDS = (
    'landing_requests', 'same_clock_groups', 'attributed_cases', 'unknown_tokens',
    'score_unavailable', 'penalty_shot_exclusions', 'located_source_issues',
    'unmatched_shootout_events',
)


def review_game_sources(document, attempts, *, game, envelope_identity, evidence):
    """review one bound game; the caller verifies envelope bytes and identity."""
    counts = {name: Counter() for name in _COUNT_FIELDS}
    located = {name: [] for name in _LOCATED_FIELDS}
    gid, season = game['game_id'], game['season']
    if game['status'] != 'reconstructed':
        counts['landing_availability'][season, 'not_reviewed'] += 1
        located['landing_requests'].append({'game_id': gid, 'status': 'not_reviewed',
            'reason': game['reason'], 'corpus_status': game['status']})
    else:
        path = envelope_identity['path']
        if evidence['score_support'] == 'unavailable':
            located['score_unavailable'].append({'game_id': gid, 'issues': evidence['score_issues']})
        attempts = {row['source_index']: row for row in attempts}
        interpreted, reconstructed = document['interpreted'], document['reconstruction']
        for layer, issues in (('interpreted', interpreted['issues']), ('reconstruction', reconstructed['issues'])):
            for index, issue in enumerate(issues):
                if (issue['source'] in ('landing', 'play-report') or issue['code'] in (
                        'shooting_owner_disagreement', 'shot_type_conflict', 'shot_type_unsupported')):
                    located['located_source_issues'].append({'game_id': gid, 'season': season, 'envelope_path': path,
                                          'layer': layer, 'issue_index': index, **issue})
        receipt = next(row for row in interpreted['inputs'] if row['source'] == 'landing')
        counts['landing_availability'][season, receipt['status']] += 1
        located['landing_requests'].append({'game_id': gid, 'corpus_status': game['status'], **receipt})
        recon = {row['source_index']: row for row in reconstructed['events'] or []}
        reports = {row['source_index']: row for row in interpreted['report_rows'] or []}
        joined_reports = defaultdict(list)
        landing_evidence = defaultdict(list)
        api_groups, report_groups = defaultdict(list), defaultdict(list)
        for row in reports.values():
            if (row['period_number'] in (1, 2, 3, 4) and row['elapsed_seconds'] is not None
                    and row['event_code'] in REPORT_CODES.values()):
                report_groups[row['period_number'], row['elapsed_seconds'], row['event_code']].append(row)
        for event in interpreted['events'] or []:
            index = event['source_index']
            row = recon[index]
            kind = event['type_key']
            counts['api_events'][season, kind, event['kind_valid'], row['match_status']] += 1
            if row['report_source_index'] is not None:
                joined_reports[row['report_source_index']].append(index)
            if ((event['kind_valid'] or row['shot_type_evidence'] is not None) and event['timed_period'] is True
                    and event['elapsed_seconds'] is not None and kind in REPORT_CODES):
                api_groups[event['period_number'], event['elapsed_seconds'], REPORT_CODES[kind]].append(event)
            locator = {'game_id': gid, 'envelope_path': path,
                       'api_path': f'/plays/{index}', 'event_id': event['event_id'],
                       'report_source_index': row['report_source_index'],
                       'report_row_id': reports[row['report_source_index']]['row_id']
                           if row['report_source_index'] is not None else None}
            type_evidence = row['shot_type_evidence']
            if type_evidence is not None:
                counts['shot_type_observations'][season, kind, 'api', type_evidence['api_value']] += 1
                if type_evidence['status'] in ('report_only', 'conflict', 'unsupported'):
                    located['attributed_cases'].append({**locator, 'kind': 'shot_type', 'evidence': type_evidence})
                if type_evidence['api_value'] is not None and canonical_shot_type(type_evidence['api_value']) is None:
                    located['unknown_tokens'].append({**locator, 'source': 'play-by-play',
                                    'field': 'shot_type', 'value': type_evidence['api_value']})
            modifier = row['goal_modifier_evidence']
            if modifier is not None:
                if modifier['source_path'] is not None:
                    landing_evidence[modifier['source_path']].append({'api_source_index': index, **modifier})
                counts['goal_modifier_evidence'][season, event['period_type'],
                    modifier['status'], modifier['reported_value']] += 1
                if modifier['status'] != 'reported' or modifier['reported_value'] != 'none':
                    located['attributed_cases'].append({**locator, 'kind': 'goal_modifier', 'evidence': modifier})
            attempt = attempts.get(index)
            if attempt is not None:
                counts['prepared_attempts'][season, kind, row['match_status'],
                    attempt['shot_type_evidence']['status'], attempt['shot_type'], attempt['status']] += 1
            report_penalty = (row['report_source_index'] is not None
                              and reports[row['report_source_index']]['penalty_shot'] is True)
            landing_penalty = (modifier is not None and modifier['status'] == 'reported'
                               and modifier['reported_value'] == 'penalty-shot')
            if attempt is not None and (report_penalty or landing_penalty):
                located['penalty_shot_exclusions'].append({**locator, 'report_penalty_shot': report_penalty,
                    'landing_penalty_shot': landing_penalty, 'status': attempt['status'],
                    'reasons': attempt['reasons'], 'goal_modifier_evidence': modifier})
            if (attempt is not None and event['timed_period'] is False
                    and row['match_status'] != 'matched'):
                located['unmatched_shootout_events'].append({**locator, 'kind': kind,
                    'match_status': row['match_status'], 'status': attempt['status'],
                    'goal_modifier_evidence': modifier})
        for row in reports.values():
            count_key = (season, row['event_code'], row['shot_type'],
                         'matched' if row['source_index'] in joined_reports else 'unmatched')
            counts['report_rows'][count_key] += 1
            if row['event_code'] in ('GOAL', 'SHOT', 'MISS', 'BLOCK'):
                counts['shot_type_observations'][season, row['event_code'], 'report', row['shot_type']] += 1
            if row['shot_type'] is not None and canonical_shot_type(row['shot_type']) is None:
                located['unknown_tokens'].append({'game_id': gid, 'envelope_path': path, 'source': 'play-report',
                    'source_path': f"/rows/{row['source_index']}[{row['row_id']}]",
                    'field': 'shot_type', 'value': row['shot_type']})
        landing = interpreted['landing_goals'] or []
        for row in landing:
            value = row['goal_modifier']
            counts['landing_rows'][season, row['period_type'], value] += 1
            if value is not None and value not in ('none', 'own-goal', 'awarded', 'penalty-shot'):
                located['unknown_tokens'].append({'game_id': gid, 'envelope_path': path, 'source': 'landing',
                                'source_path': row['source_path'], 'field': 'goal_modifier', 'value': value})
            joined_evidence = landing_evidence[row['source_path']]
            if not any(item['status'] in ('reported', 'missing', 'unsupported') for item in joined_evidence):
                located['attributed_cases'].append({'game_id': gid, 'envelope_path': path, 'kind': 'unjoined_landing_row',
                              'source_path': row['source_path'], 'event_id': row['event_id'],
                              'goal_evidence': joined_evidence})
        keys = list(api_groups) + [key for key in report_groups if key not in api_groups]
        for key in keys:
            events = api_groups.get(key, [])
            candidates = report_groups.get(key, [])
            if len(events) < 2 and len(candidates) < 2:
                continue
            statuses = Counter(recon[event['source_index']]['match_status'] for event in events)
            group = {'game_id': gid, 'season': season, 'envelope_path': path, 'period_number': key[0],
                     'elapsed_seconds': key[1], 'event_code': key[2],
                     'api_size': len(events), 'report_size': len(candidates),
                     'match_status_counts': dict(statuses),
                     'outcome': 'no_api_event' if not events else next(iter(statuses)) if len(statuses) == 1 else 'mixed',
                     'api_source_indices': [event['source_index'] for event in events],
                     'report_rows': [{'source_index': row['source_index'], 'row_id': row['row_id']}
                                     for row in candidates]}
            located['same_clock_groups'].append(group)
    return {'counts': {name: count_rows(counter, _COUNT_FIELDS[name])
                       for name, counter in counts.items()}, **located}


def review_sources(prepared):
    counts = {name: Counter() for name in _COUNT_FIELDS}
    located = {name: [] for name in _LOCATED_FIELDS}
    envelopes = {entry['path']: entry for entry in prepared['inputs'] if entry['kind'] == 'game'}
    evidence = {row['game_id']: row for row in prepared['coverage']['per_game']}
    attempts = defaultdict(list)
    for row in prepared['attempts']:
        attempts[row['game_id']].append(row)
    for game in prepared['games']:
        document, envelope_identity = None, None
        game_attempts, game_evidence = [], None
        if game['status'] == 'reconstructed':
            path = str((Path(game['corpus_path']).parent / game['output_path']).resolve())
            if path not in envelopes:
                raise InputContractError(f'{path}: game envelope absent from prepared inputs')
            data = Path(path).read_bytes()
            envelope_identity = envelopes[path]
            if hashlib.sha256(data).hexdigest() != envelope_identity['sha256']:
                raise InputContractError(f'{path}: envelope bytes changed after preparation; rerun against stable inputs')
            document = strict_json(data)
            game_attempts = attempts[game['game_id']]
            game_evidence = evidence[game['game_id']]
        review = review_game_sources(document, game_attempts, game=game,
            envelope_identity=envelope_identity, evidence=game_evidence)
        for name, rows in review['counts'].items():
            for row in rows:
                counts[name][tuple(row[field] for field in _COUNT_FIELDS[name])] += row['count']
        for name in located:
            located[name].extend(review[name])
    return {'counts': {name: count_rows(counter, _COUNT_FIELDS[name])
                       for name, counter in counts.items()}, **located}


def main():
    parser = argparse.ArgumentParser(description='review admitted source evidence without fitting',
                                     allow_abbrev=False)
    parser.add_argument('--selection', required=True, action=Once)
    parser.add_argument('--out', required=True, action=Once)
    args = parser.parse_args()
    try:
        selection = Path(args.selection).resolve(strict=True)
        prepared = prepare(selection)
        output = output_path(args.out, prepared['input_roots'])
        review = {'schema_version': 1, 'purpose': prepared['purpose'],
                  'implementation': implementation_identity(), 'inputs': prepared['inputs'],
                  'selection': prepared['selection'], 'coverage': prepared['coverage'],
                  'denominators': DENOMINATORS,
                  **review_sources(prepared)}
        output.mkdir()
        write_json(output / 'review.json', review)
        print(f"source review: {prepared['purpose'].replace('_', ' ')}; saved to {output}")
        return 0
    except (InputContractError, OSError, ValueError, TypeError, KeyError, IndexError) as error:
        print(f'source review failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
