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


def count_rows(counter, fields):
    return [dict(zip(fields, key), count=count)
            for key, count in sorted(counter.items(), key=lambda row: repr(row[0]))]


def review_sources(prepared):
    counts = {name: Counter() for name in (
        'api_events', 'report_rows', 'prepared_attempts', 'landing_availability',
        'landing_rows', 'goal_modifier_evidence', 'shot_type_observations',
    )}
    envelopes = {entry['path']: entry for entry in prepared['inputs'] if entry['kind'] == 'game'}
    requests, groups, cases, unknown, source_issues = [], [], [], [], []
    penalties, unmatched_shootout, score_gaps = [], [], []
    attempts = {(row['game_id'], row['source_index']): row for row in prepared['attempts']}
    for ledger in prepared['coverage']['per_game']:
        if ledger.get('score_support') == 'unavailable':
            score_gaps.append({'game_id': ledger['game_id'], 'issues': ledger['score_issues']})
    for game in prepared['games']:
        gid, season = game['game_id'], game['season']
        if game['status'] != 'reconstructed':
            counts['landing_availability'][season, 'not_reviewed'] += 1
            requests.append({'game_id': gid, 'status': 'not_reviewed',
                             'reason': game['reason'], 'corpus_status': game['status']})
            continue
        path = str((Path(game['corpus_path']).parent / game['output_path']).resolve())
        if path not in envelopes:
            raise InputContractError(f'{path}: game envelope absent from prepared inputs')
        data = Path(path).read_bytes()
        if hashlib.sha256(data).hexdigest() != envelopes[path]['sha256']:
            raise InputContractError(f'{path}: envelope bytes changed after preparation; rerun against stable inputs')
        document = strict_json(data)
        interpreted, reconstructed = document['interpreted'], document['reconstruction']
        for layer, issues in (('interpreted', interpreted['issues']), ('reconstruction', reconstructed['issues'])):
            for index, issue in enumerate(issues):
                if (issue['source'] in ('landing', 'play-report') or issue['code'] in (
                        'shooting_owner_disagreement', 'shot_type_conflict', 'shot_type_unsupported')):
                    source_issues.append({'game_id': gid, 'season': season, 'envelope_path': path,
                                          'layer': layer, 'issue_index': index, **issue})
        receipt = next(row for row in interpreted['inputs'] if row['source'] == 'landing')
        counts['landing_availability'][season, receipt['status']] += 1
        requests.append({'game_id': gid, 'corpus_status': game['status'], **receipt})
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
            evidence = row['shot_type_evidence']
            if evidence is not None:
                counts['shot_type_observations'][season, kind, 'api', evidence['api_value']] += 1
                if evidence['status'] in ('report_only', 'conflict', 'unsupported'):
                    cases.append({**locator, 'kind': 'shot_type', 'evidence': evidence})
                if evidence['api_value'] is not None and canonical_shot_type(evidence['api_value']) is None:
                    unknown.append({**locator, 'source': 'play-by-play',
                                    'field': 'shot_type', 'value': evidence['api_value']})
            modifier = row['goal_modifier_evidence']
            if modifier is not None:
                if modifier['source_path'] is not None:
                    landing_evidence[modifier['source_path']].append({'api_source_index': index, **modifier})
                counts['goal_modifier_evidence'][season, event['period_type'],
                    modifier['status'], modifier['reported_value']] += 1
                if modifier['status'] != 'reported' or modifier['reported_value'] != 'none':
                    cases.append({**locator, 'kind': 'goal_modifier', 'evidence': modifier})
            attempt = attempts.get((gid, index))
            if attempt is not None:
                counts['prepared_attempts'][season, kind, row['match_status'],
                    attempt['shot_type_evidence']['status'], attempt['shot_type'], attempt['status']] += 1
            report_penalty = (row['report_source_index'] is not None
                              and reports[row['report_source_index']]['penalty_shot'] is True)
            landing_penalty = (modifier is not None and modifier['status'] == 'reported'
                               and modifier['reported_value'] == 'penalty-shot')
            if attempt is not None and (report_penalty or landing_penalty):
                penalties.append({**locator, 'report_penalty_shot': report_penalty,
                    'landing_penalty_shot': landing_penalty, 'status': attempt['status'],
                    'reasons': attempt['reasons'], 'goal_modifier_evidence': modifier})
            if (attempt is not None and event['timed_period'] is False
                    and row['match_status'] != 'matched'):
                unmatched_shootout.append({**locator, 'kind': kind,
                    'match_status': row['match_status'], 'status': attempt['status'],
                    'goal_modifier_evidence': modifier})
        for row in reports.values():
            count_key = (season, row['event_code'], row['shot_type'],
                         'matched' if row['source_index'] in joined_reports else 'unmatched')
            counts['report_rows'][count_key] += 1
            if row['event_code'] in ('GOAL', 'SHOT', 'MISS', 'BLOCK'):
                counts['shot_type_observations'][season, row['event_code'], 'report', row['shot_type']] += 1
            if row['shot_type'] is not None and canonical_shot_type(row['shot_type']) is None:
                unknown.append({'game_id': gid, 'envelope_path': path, 'source': 'play-report',
                    'source_path': f"/rows/{row['source_index']}[{row['row_id']}]",
                    'field': 'shot_type', 'value': row['shot_type']})
        landing = interpreted['landing_goals'] or []
        for row in landing:
            value = row['goal_modifier']
            counts['landing_rows'][season, row['period_type'], value] += 1
            if value is not None and value not in ('none', 'own-goal', 'awarded', 'penalty-shot'):
                unknown.append({'game_id': gid, 'envelope_path': path, 'source': 'landing',
                                'source_path': row['source_path'], 'field': 'goal_modifier', 'value': value})
            evidence = landing_evidence[row['source_path']]
            if not any(item['status'] in ('reported', 'missing', 'unsupported') for item in evidence):
                cases.append({'game_id': gid, 'envelope_path': path, 'kind': 'unjoined_landing_row',
                              'source_path': row['source_path'], 'event_id': row['event_id'],
                              'goal_evidence': evidence})
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
            groups.append(group)
    fields = {
        'api_events': ('season', 'kind', 'kind_valid', 'match_status'),
        'report_rows': ('season', 'event_code', 'shot_type', 'match_status'),
        'prepared_attempts': ('season', 'kind', 'match_status', 'type_evidence_status', 'shot_type', 'status'),
        'landing_availability': ('season', 'status'),
        'landing_rows': ('season', 'period_type', 'goal_modifier'),
        'goal_modifier_evidence': ('season', 'period_type', 'status', 'reported_value'),
        'shot_type_observations': ('season', 'kind', 'source', 'reported_value'),
    }
    return {'counts': {name: count_rows(counter, fields[name]) for name, counter in counts.items()},
            'landing_requests': requests, 'same_clock_groups': groups,
            'attributed_cases': cases, 'unknown_tokens': unknown,
            'score_unavailable': score_gaps, 'penalty_shot_exclusions': penalties,
            'located_source_issues': source_issues,
            'unmatched_shootout_events': unmatched_shootout}


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
                  'denominators': {'api_events': 'all interpreted api events in selected admitted games',
                      'report_rows': 'all interpreted report rows, including unjoined rows',
                      'prepared_attempts': 'recognized attempts, including excluded and unavailable records',
                      'landing_rows': 'all interpreted scoring-summary rows, including deficient and duplicate rows',
                      'goal_modifier_evidence': 'reconstructed api goals, including unmatched shootout goals'},
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
