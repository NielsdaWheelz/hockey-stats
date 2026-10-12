"""account for an explicit native corpus population without fitting or history preparation.

source receipts establish capture dispositions. native interpretation establishes
source meaning; shared chance preparation and encoding establish circumstance
availability. unavailable populations stay null and never become empty evidence.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

from hockey_stats.artifacts import implementation_identity, write_json
from hockey_stats.captures import (
    InputContractError, REFERENCE_SOURCES, SOURCES, read_capture,
    read_reference_capture, strict_json,
)
from hockey_stats.chance_cli import identity, output_path
from hockey_stats.chance_data import load_corpus, prepare_game_attempts
from hockey_stats.chance_features import (
    PREPARATION_IDENTITY, encode_stage_inputs, stage_design, validate_context,
)
from hockey_stats.cli import Once
from hockey_stats.interpret import interpret_game
from hockey_stats.reconstruct import reconstruct_game
from hockey_stats.references import interpret_references
from source_review import DENOMINATORS, count_rows, review_game_sources


STATUSES = ('eligible', 'out_of_scope', 'unavailable')
KINDS = ('goal', 'shot-on-goal', 'missed-shot', 'blocked-shot')
APPLICABILITY = ('eligible_unblocked', 'eligible_blocked', 'out_of_scope',
                 'unavailable', 'eligible_unblocked_goals')
SEASONS = ('20212022', '20222023', '20232024', '20242025', '20252026')
IDENTITY_FIELDS = ('game_id', 'season', 'game_type', 'game_date', 'away_team_id', 'home_team_id')


def require(condition, location, reason):
    if not condition:
        raise InputContractError(f'{location}: {reason}')


def same_json(left, right):
    # python equality conflates boolean/integer and integer/float json values.
    return (json.dumps(left, sort_keys=True, separators=(',', ':'), allow_nan=False) ==
            json.dumps(right, sort_keys=True, separators=(',', ':'), allow_nan=False))


def bound_json(path, kind, inputs):
    data = path.read_bytes()
    try:
        document = strict_json(data)
    except ValueError as error:
        raise InputContractError(f'{path}: invalid finite json: {error}') from error
    binding = {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest()}
    inputs.append({'kind': kind, **binding})
    return document, binding


def source_records(provenance, *, directory, sources, requested, reader, inputs):
    """bind all promised native receipt/body pairs to the stored interpretation."""
    require(isinstance(provenance, list), directory, 'source provenance array required')
    require(all(isinstance(row, dict) for row in provenance), directory, 'source provenance objects required')
    require(len(provenance) == len(sources) and {row.get('source') for row in provenance} == set(sources),
            directory, 'source provenance must cover the declared sources exactly once')
    saved = {row['source']: row for row in provenance}
    records = {}
    for source in sources:
        capture = reader(directory, source)
        receipt_path = capture.capture_path
        require(receipt_path.is_file(), receipt_path, 'promised complete retrieval lacks a source receipt')
        actual_requested = (capture.requested_season if source in REFERENCE_SOURCES
                            else capture.requested_game_id)
        require(actual_requested == requested, receipt_path, 'requested source identity disagrees with population')
        row = saved[source]
        actual = {'capture_path': str(receipt_path), 'requested_at': capture.requested_at,
                  'http_status': capture.http_status, 'body_sha256': capture.body_sha256}
        for field, value in actual.items():
            require(row.get(field) == value, receipt_path, f'stored {field} differs from actual native receipt/body')
        require(row.get('status') in ('parsed', 'unavailable', 'reference_only'), receipt_path,
                'stored interpretation status unsupported')
        require(row.get('reason') is None or isinstance(row['reason'], str), receipt_path,
                'stored interpretation reason must be text or null')
        if capture.reason is not None:
            require(row['status'] == 'unavailable' and row['reason'] == capture.reason,
                    receipt_path, 'native unavailable capture contradicts stored interpretation disposition')
        receipt_identity = identity(receipt_path)
        inputs.append({'kind': 'receipt', **receipt_identity})
        body_identity = None
        if capture.body_sha256 is not None:
            body_identity = {'path': str((receipt_path.parent / 'body.bin').resolve()),
                             'sha256': capture.body_sha256}
            inputs.append({'kind': 'body', **body_identity})
        records[source] = {
            'capture_state': 'captured' if capture.body_sha256 is not None else 'failed',
            'interpretation_status': row['status'],
            'requested_identity': actual_requested, 'requested_at': capture.requested_at,
            'http_status': capture.http_status, 'receipt': receipt_identity,
            'body': body_identity, 'reason': row['reason'],
        }
    return records


def sum_quantity(values):
    """a sum is known only over its available game contributions."""
    known = [value for value in values if value is not None]
    return {'value': sum(known) if known else None,
            'contributing_games': len(known), 'unavailable_games': len(values) - len(known)}


def game_counts(attempts, available, design, envelope, sources):
    """partition recognized observations; encoder failure never filters the population."""
    if not available:
        require(not attempts, envelope, 'unavailable collection produced attempts')
        return {'attempt_counts': None, 'goal_counts': None,
                'conversion_applicability': None, 'active_inputs': None}
    counts = Counter((row['status'], row['source_event']['type_key']) for row in attempts)
    require(all(status in STATUSES and kind in KINDS for status, kind in counts),
            envelope, 'prepared attempt status/kind outside native partition')
    applicability = dict.fromkeys(APPLICABILITY, 0)
    encoded, errors = 0, []
    for attempt in attempts:
        status = attempt['status']
        if status == 'eligible':
            key = 'eligible_blocked' if attempt['blocked'] else 'eligible_unblocked'
            applicability[key] += 1
            if attempt['blocked']:
                continue
            applicability['eligible_unblocked_goals'] += int(attempt['goal'])
            try:
                encode_stage_inputs(attempt, design, game_facts={}, player_game_facts={})
            except InputContractError as error:
                reason = str(error)
                prefix = f"{attempt['game_id']}:{attempt['source_index']}:r."
                family = next((name for name in design['families']
                               if reason.startswith(prefix + name + ':')), None)
                field = None
                if family is not None:
                    try:
                        validate_context(attempt['context'], family=family)
                    except InputContractError:
                        field = 'context'
                    else:
                        field = 'previous_event'
                errors.append({'game_id': attempt['game_id'], 'source_index': attempt['source_index'],
                    'event_id': attempt['event_id'], 'family': family, 'field': field, 'reason': reason,
                    'evidence_locators': [{'envelope': envelope, 'source': 'play-by-play',
                        'receipt': sources['play-by-play']['receipt'],
                        'path': f"/plays/{attempt['source_index']}"},
                        {'envelope': envelope, 'source': 'play-by-play',
                         'receipt': sources['play-by-play']['receipt'],
                         'path': f"/plays/{attempt['previous_event']['source_index']}"}
                        if attempt['previous_event'].get('source_index') is not None else
                        {'envelope': envelope, 'source': 'play-by-play',
                         'receipt': sources['play-by-play']['receipt'], 'path': '/plays'}]})
            else:
                encoded += 1
        else:
            applicability[status] += 1
    rows = [{'status': status, 'kind': kind, 'count': counts[status, kind]}
            for status in STATUSES for kind in KINDS]
    require(sum(row['count'] for row in rows) == len(attempts), envelope, 'attempt partition failed')
    require(sum(applicability[key] for key in APPLICABILITY[:4]) == len(attempts),
            envelope, 'conversion applicability partition failed')
    require(encoded + len(errors) == applicability['eligible_unblocked'], envelope, 'active input partition failed')
    return {'attempt_counts': rows, 'goal_counts': {status: counts[status, 'goal'] for status in STATUSES},
            'conversion_applicability': applicability,
            'active_inputs': {'encoded': encoded, 'error_count': len(errors), 'errors': errors}}


def reduce_games(rows):
    """reduce each quantity over its own availability, preserving the selected denominator."""
    attempts = [{'status': status, 'kind': kind,
                 'count': sum_quantity([None if row['attempt_counts'] is None else
                     next(item['count'] for item in row['attempt_counts']
                          if item['status'] == status and item['kind'] == kind) for row in rows])}
                for status in STATUSES for kind in KINDS]
    goals = {status: sum_quantity([None if row['goal_counts'] is None else row['goal_counts'][status]
                                  for row in rows]) for status in STATUSES}
    applicability = {key: sum_quantity([None if row['conversion_applicability'] is None else
                                        row['conversion_applicability'][key] for row in rows])
                     for key in APPLICABILITY}
    active = {key: sum_quantity([None if row['active_inputs'] is None else row['active_inputs'][key]
                                for row in rows]) for key in ('encoded', 'error_count')}
    coverage = {group: {field: sum_quantity([None if row['coverage'] is None else
                        row['coverage'][group][field] for row in rows]) for field in fields}
                for group, fields in (
                    ('time', ('known_seconds', 'five_on_five_seconds', 'other_seconds', 'unresolved_seconds')),
                    ('attempts', ('known_timed_attempts', 'five_on_five', 'other', 'unresolved',
                                  'linked_five_on_five', 'unclassified_events')),
                    ('locations', ('known_timed_attempts', 'normalized', 'missing_coordinates', 'unresolved_frame')),
                )}
    recognized = sum_quantity([None if row['attempt_counts'] is None else
                               sum(item['count'] for item in row['attempt_counts']) for row in rows])
    partition = [applicability[key]['value'] for key in APPLICABILITY[:4]]
    require((recognized['value'] is None and all(value is None for value in partition)) or
            (recognized['value'] == sum(partition)), 'season reduction', 'recognized/application totals disagree')
    require(active['encoded'] == applicability['eligible_unblocked'], 'season reduction',
            'active encoded rows disagree with eligible unblocked rows')
    for status in STATUSES:
        require(goals[status] == next(row['count'] for row in attempts
                                     if row['status'] == status and row['kind'] == 'goal'),
                'season reduction', 'goal partition failed')
    source_dispositions, source_reasons = Counter(), Counter()
    for row in rows:
        for source, record in row['sources'].items():
            source_dispositions[source, record['capture_state'], record['interpretation_status']] += 1
            if record['reason'] is not None:
                source_reasons[source, record['reason']] += 1
    results = {}
    checks = {}
    for source in ('play-by-play', 'boxscore'):
        source_results = [next((result for result in row['reported_results'] or []
                               if result['source'] == source), None) for row in rows]
        results[source] = {field: sum_quantity([None if result is None else result[field]
                                                for result in source_results])
                           for field in ('away_score', 'home_score', 'away_sog', 'home_sog')}
        source_checks = [next((check for check in row['timed_goal_checks'] or []
                              if check['source'] == source), None) for row in rows]
        checks[source] = {side: sum_quantity([None if check is None or check['observed'] is None else
                                              check['observed'][side] for check in source_checks])
                          for side in ('away', 'home')}
        checks[source]['status_games'] = dict(Counter('not_reviewed' if check is None else check['status']
                                                      for check in source_checks))
    return {
        'declared_games': len(rows), 'corpus_status_games': dict(Counter(row['corpus_status'] for row in rows)),
        'recognized_attempts': recognized, 'attempt_counts': attempts, 'goal_counts': goals,
        'conversion_applicability': applicability, 'active_inputs': active, 'native_coverage': coverage,
        'unclassified_events': sum_quantity([row['unclassified_events'] for row in rows]),
        'score_support_games': dict(Counter('not_prepared' if row['score_support'] is None else
                                          row['score_support'] for row in rows)),
        'source_dispositions': count_rows(source_dispositions, ('source', 'capture_state', 'interpretation_status')),
        'source_reasons': count_rows(source_reasons, ('source', 'reason')),
        'reported_results': results, 'recorded_timed_goal_checks': checks,
    }


def audit_selection(selection_path, output_value):
    inputs = []
    selection, selection_identity = bound_json(selection_path, 'selection', inputs)
    require(isinstance(selection, dict) and set(selection) ==
            {'schema_version', 'purpose', 'corpora', 'history_corpora'}, selection_path,
            'selection fields disagree with schema 2')
    require(type(selection['schema_version']) is int and selection['schema_version'] == 2,
            selection_path, 'selection schema 2 required')
    require(selection['purpose'] in ('fixture_exercise', 'research'), selection_path, 'unsupported purpose')
    require(selection['history_corpora'] == [], selection_path, 'source admission requires history_corpora=[]')
    require(isinstance(selection['corpora'], list) and bool(selection['corpora']),
            selection_path, 'nonempty explicit corpus selection required')
    roots = {str(selection_path.parent)}
    corpora, seen_paths, seen_ids, seen_seasons = [], set(), set(), set()
    for index, selected in enumerate(selection['corpora']):
        location = f'{selection_path}/corpora/{index}'
        require(isinstance(selected, dict) and set(selected) == {'path', 'game_ids'}, location,
                'explicit path and game_ids required')
        require(isinstance(selected['path'], str) and bool(selected['path']), location, 'nonempty corpus path required')
        path = (selection_path.parent / selected['path']).resolve(strict=True)
        require(path not in seen_paths, location, 'duplicate corpus path')
        seen_paths.add(path)
        ids = selected['game_ids']
        require(isinstance(ids, list) and bool(ids), location, 'nonempty game_ids array required')
        for gid in ids:
            require(isinstance(gid, str) and re.fullmatch(r'[0-9]{10}', gid) is not None,
                    location, 'ten-digit string game id required')
            require(gid not in seen_ids, location, f'duplicate selected game id {gid}')
            seen_ids.add(gid)
        document, inventory, ledger = load_corpus(path, inputs)
        corpus_identity = {field: inputs[-1][field] for field in ('path', 'sha256')}
        require(set(ids) <= inventory.keys(), path, 'selected game absent from inventory')
        season = document['reference']['requested_season']
        require(season not in seen_seasons, path, 'one current corpus per season required')
        seen_seasons.add(season)
        if selection['purpose'] == 'research':
            require(set(ids) == inventory.keys(), path, 'research requires every official inventory game exactly once')
        require(isinstance(document.get('games_root'), str) and bool(document['games_root']), path,
                'native games_root required')
        games_root = Path(document['games_root']).resolve(strict=True)
        require(games_root.is_dir(), games_root, 'native game input root must be a directory')
        provenance = document['reference']['inputs']
        reference_root = Path(provenance[0]['capture_path']).parent.parent.resolve(strict=True)
        require(reference_root.is_dir(), reference_root, 'native reference root must be a directory')
        roots.update((str(path.parent), str(games_root), str(reference_root)))
        for gid in ids:
            raw_path = ledger[gid].get('capture_path')
            require(isinstance(raw_path, str) and bool(raw_path), path, f'{gid}: native capture_path required')
            roots.add(str(Path(raw_path).resolve()))
        corpora.append((path, corpus_identity, document, inventory, ledger, ids, reference_root, games_root))
    if selection['purpose'] == 'research':
        require(seen_seasons == set(SEASONS), selection_path, 'research requires all five 2021–22 through 2025–26 seasons')
    output = output_path(output_value, sorted(roots))
    implementation = implementation_identity()
    design = stage_design('r', ['game_additive', 'recent_additive', 'recent_interactions'],
                          core_layout={'prefix': [], 'suffix': [], 'slices': {}}, trait_assumptions=[])
    require(len(design['columns']) == 65 and design['family_slices'] ==
            {'game_additive': [0, 10], 'recent_additive': [10, 29], 'recent_interactions': [29, 65]},
            'circumstance design', 'current 65-column circumstance contract changed')
    references, per_game, review_counts, review_lists = {}, [], {}, defaultdict(list)
    type_counts, reason_counts = defaultdict(Counter), defaultdict(Counter)
    for corpus_path, corpus_identity, corpus, inventory, ledger, ids, reference_root, games_root in corpora:
        reference = corpus['reference']
        season = reference['requested_season']
        sources = source_records(reference['inputs'], directory=reference_root,
            sources=REFERENCE_SOURCES, requested=season, reader=read_reference_capture, inputs=inputs)
        require(same_json(interpret_references(reference_root), reference), corpus_path,
                'stored reference differs from current native rederivation')
        dates = [entry['game_date'] for entry in inventory.values()]
        references[season] = {
            'sources': sources, 'captured_expected_count': reference['season']['reported_regular_games'],
            'unique_inventory_count': len(inventory),
            'inventory_date_range': {'first': min(dates), 'last': max(dates)},
            'inventory_checks': reference['checks'],
            'inventory_issues': [issue for issue in reference['issues']
                                 if issue['source'] in ('season-summary', 'season-games')],
            'reference_issues': reference['issues'],
            'bio_collections': reference['bio_collections'],
            'bio_observation_rows': len(reference['bio_observations']),
        }
        ledger_indices = {row['game_id']: index for index, row in enumerate(corpus['games'])}
        for gid in ids:
            entry, ledger_row = inventory[gid], ledger[gid]
            status = ledger_row['status']
            require(status != 'input_error', f'{corpus_path}/games/{gid}',
                    f"input_error: {ledger_row['reason']}")
            raw_path = Path(ledger_row['capture_path']).resolve()
            require(raw_path == (games_root / gid).resolve(), corpus_path,
                    f'{gid}: stored capture path differs from native corpus lookup')
            game = {'game_id': gid, 'season': season, 'status': status, 'reason': ledger_row['reason'],
                    'corpus_path': str(corpus_path), 'output_path': ledger_row['output_path']}
            row = {'season': season, 'game_id': gid, 'game_date': entry['game_date'],
                   'corpus_status': status, 'reason': ledger_row['reason'], 'envelope': None,
                   'sources': {}, 'coverage': None, 'score_support': None, 'score_issues': None,
                   'event_collection_available': None, 'unclassified_events': None,
                   'attempt_counts': None, 'goal_counts': None, 'conversion_applicability': None,
                   'active_inputs': None, 'reported_results': None, 'timed_goal_checks': None,
                   'venues': None, 'issues': []}
            document, evidence, attempts = None, None, []
            if status == 'missing_capture':
                require(ledger_row['output_path'] is None and ledger_row.get('coverage') is None,
                        corpus_path, f'{gid}: missing capture must have no envelope or coverage')
                require(not raw_path.exists() and not (games_root / gid).is_symlink(), raw_path,
                        'stored missing_capture is no longer a missing capture directory')
                row['sources'] = {source: {'capture_state': None, 'interpretation_status': None,
                    'requested_identity': None, 'requested_at': None, 'http_status': None,
                    'receipt': None, 'body': None, 'reason': ledger_row['reason']} for source in SOURCES}
            else:
                relative = ledger_row['output_path']
                require(isinstance(relative, str) and bool(relative) and not Path(relative).is_absolute(),
                        corpus_path, f'{gid}: relative envelope path required')
                envelope_path = (corpus_path.parent / relative).resolve(strict=True)
                require(envelope_path.is_relative_to(corpus_path.parent), envelope_path,
                        'game envelope must remain within its corpus directory')
                document, envelope_identity = bound_json(envelope_path, 'game', inputs)
                row['envelope'] = envelope_identity
                require(isinstance(document, dict) and type(document.get('schema_version')) is int
                        and document['schema_version'] == 4 and
                        isinstance(document.get('interpreted'), dict) and
                        isinstance(document.get('reconstruction'), dict), envelope_path,
                        'game envelope schema 4 with interpreted/reconstruction objects required')
                interpreted = document['interpreted']
                require(interpreted['requested_game_id'] == gid, envelope_path,
                        'requested game/inventory disagreement')
                row['sources'] = source_records(interpreted['inputs'], directory=raw_path,
                    sources=SOURCES, requested=gid, reader=read_capture, inputs=inputs)
                if status in ('identity_unavailable', 'identity_mismatch'):
                    current = interpret_game(raw_path)
                    require(same_json(current, interpreted) and
                            same_json(reconstruct_game(current), document['reconstruction']),
                            envelope_path, 'identity-gap envelope differs from exact native rederivation')
                    actual_game = current['game']
                    conflicts = [] if actual_game is None else [field for field in IDENTITY_FIELDS
                                                               if actual_game[field] != entry[field]]
                    actual_status = ('identity_unavailable' if actual_game is None else
                                     'identity_mismatch' if conflicts else 'reconstructed')
                    expected_reason = ('completed regular-season identity unavailable; inspect game diagnostic'
                        if actual_game is None else 'inventory/game disagreement: ' + ', '.join(conflicts))
                    require(status == actual_status and ledger_row['reason'] == expected_reason
                            and ledger_row.get('coverage') is None, envelope_path,
                            'native identity disposition/reason/coverage differs from stored corpus row')
                    row['issues'].append({'code': status, 'source': 'corpus',
                        'path': f'/games/{ledger_indices[gid]}', 'corpus': corpus_identity,
                        'message': expected_reason,
                        'conflicting_fields': conflicts, 'envelope': envelope_identity})
                else:
                    require(status == 'reconstructed' and ledger_row['reason'] is None,
                            corpus_path, f'{gid}: invalid reconstructed ledger disposition')
                    prepared = prepare_game_attempts(document, envelope_path, entry)
                    attempts, evidence = prepared['attempts'], prepared['evidence']
                    unclassified = prepared['unclassified_events']
                    del prepared
                    require(same_json(ledger_row.get('coverage'), evidence['source_coverage']), envelope_path,
                            'corpus coverage disagrees with bound reconstruction')
                    row.update({'coverage': evidence['source_coverage'],
                        'score_support': evidence['score_support'], 'score_issues': evidence['score_issues'],
                        'event_collection_available': evidence['event_collection_available'],
                        'unclassified_events': unclassified
                            if evidence['event_collection_available'] else None,
                        'reported_results': interpreted['reported_results'],
                        'timed_goal_checks': [check for check in interpreted['checks']
                                             if check['name'] == 'timed_goals']})
                    row.update(game_counts(attempts, evidence['event_collection_available'], design,
                                           envelope_identity, row['sources']))
                    for layer in ('interpreted', 'reconstruction'):
                        row['issues'].extend({'envelope': envelope_identity, 'layer': layer,
                            'issue_index': index, **issue} for index, issue in enumerate(document[layer]['issues']))
                    venue_conflicts = [issue for issue in row['issues']
                                       if issue['code'] == 'recording_field_conflict' and issue['path'] == '/recording/venue']
                    row['venues'] = [{'source': observation['source'],
                        'supplied_name': observation['source_fields']['values']['venue'],
                        'source_fields': observation['source_fields'], 'conflicts': venue_conflicts}
                        for observation in interpreted['recording_observations']]
                    for attempt in attempts:
                        type_counts[season][attempt['status'], attempt['source_event']['type_key'],
                            attempt['source_event']['shot_type'], attempt['shot_type_evidence']['status'],
                            attempt['shot_type'], attempt['model_shot_type']] += 1
                        for reason in attempt['reasons']:
                            reason_counts[season][attempt['status'], attempt['source_event']['type_key'], reason] += 1
            review = review_game_sources(document, attempts, game=game,
                                         envelope_identity=row['envelope'], evidence=evidence)
            for name, records in review['counts'].items():
                if name not in review_counts:
                    review_counts[name] = Counter()
                for record in records:
                    key = tuple((field, value) for field, value in record.items() if field != 'count')
                    review_counts[name][key] += record['count']
            for name, records in review.items():
                if name != 'counts':
                    review_lists[name].extend(records)
            per_game.append(row)
    errors = [error for row in per_game if row['active_inputs'] is not None
              for error in row['active_inputs']['errors']]
    if errors:
        output.mkdir()
        write_json(output / 'failure-diagnostics.json', {'schema_version': 1, 'purpose': selection['purpose'],
            'status': 'failed', 'implementation': implementation, 'selection': selection_identity,
            'scientific_assessment': 'not_performed', 'active_input_errors': errors})
        raise InputContractError(f'{len(errors)} applicable rows failed active encoding; diagnostics written to {output}')
    counts = {}
    for season in sorted(seen_seasons):
        rows = [row for row in per_game if row['season'] == season]
        counts[season] = reduce_games(rows)
        counts[season]['type_strata'] = count_rows(type_counts[season],
            ('status', 'kind', 'api_reported_type', 'type_evidence_status', 'canonical_type', 'model_type'))
        counts[season]['attempt_reasons'] = count_rows(reason_counts[season], ('status', 'kind', 'reason'))
        counts[season]['venue_review_games'] = {
            'reviewed': sum(row['venues'] is not None for row in rows),
            'not_reviewed': sum(row['venues'] is None for row in rows),
        }
        venue_groups = defaultdict(list)
        for row in rows:
            for venue in row['venues'] or []:
                venue_groups[venue['source'], venue['supplied_name']].append(row)
        counts[season]['venue_strata'] = [{'source': source, 'supplied_name': name,
            'game_count': len(group), 'recognized_attempts': sum_quantity([
                None if row['attempt_counts'] is None else sum(item['count'] for item in row['attempt_counts'])
                for row in group]),
            'conversion_applicability': {key: sum_quantity([None if row['conversion_applicability'] is None else
                row['conversion_applicability'][key] for row in group]) for key in APPLICABILITY},
            'conflict_games': [row['game_id'] for row in group if any(
                venue['source'] == source and venue['conflicts'] for venue in row['venues'])]}
            for (source, name), group in sorted(venue_groups.items(), key=lambda item: repr(item[0]))]
    source_review = {'schema_version': 1, 'denominators': DENOMINATORS,
                    'counts': {name: [dict(key, count=value) for key, value in
                        sorted(counter.items(), key=lambda item: repr(item[0]))]
                        for name, counter in review_counts.items()}, **dict(review_lists)}
    limitations = [
        {'code': 'retrospective_sources', 'reason': 'retrieval-dated public exports do not establish information available in the modeled year'},
        {'code': 'circumstance_availability_only', 'reason': '65-column encoding measures current circumstance availability; no fit, actor, geometry or penalty assessment'},
        {'code': 'recorded_goals_only', 'reason': 'reported results, recorded timed-goal checks and eligible conversion goals have separate denominators; exports are not independent physical measurements'},
        {'code': 'source_strata', 'reason': 'source-specific venue/type frequencies may overlap; differences do not establish bias'},
        {'code': 'bio_effective_time_unknown', 'reason': 'bios are retrieval-dated reference observations; current affiliation does not establish historical membership or pre-event availability'},
    ]
    for season, totals in counts.items():
        for status, count in totals['corpus_status_games'].items():
            if status != 'reconstructed':
                limitations.append({'code': status, 'season': season, 'games': count,
                    'reason': 'inventory rows retained; core populations and source review unavailable; required future inputs need separate settlement'})
        unavailable = totals['recognized_attempts']['unavailable_games']
        if unavailable:
            limitations.append({'code': 'attempt_population_unavailable', 'season': season, 'games': unavailable,
                'reason': 'recognized-attempt, goal, applicability and active counts are null for these games'})
        for source in SOURCES:
            gaps = sum(record['count'] for record in totals['source_dispositions']
                       if record['source'] == source and
                       record['interpretation_status'] in ('unavailable', 'reference_only'))
            if gaps:
                limitations.append({'code': 'source_interpretation_gap', 'season': season,
                    'source': source, 'games': gaps,
                    'reason': 'this source cannot supply its full interpreted facts; other available exports do not replace its missing evidence'})
        for collection in references[season]['bio_collections']:
            if not collection['complete']:
                limitations.append({'code': 'bio_collection_unavailable_or_incomplete', 'season': season,
                    'source': collection['source'], 'reason': 'absent historical player references cannot be established'})
    require(len(per_game) == len(seen_ids) and {row['game_id'] for row in per_game} == seen_ids,
            selection_path, 'declared population reconciliation failed')
    report = {'schema_version': 1, 'purpose': selection['purpose'], 'status': 'complete',
        'implementation': implementation, 'preparation_identity': PREPARATION_IDENTITY,
        'selection': selection_identity, 'inputs': inputs,
        'circumstance_design': {**design, 'assessment': 'circumstance_availability'},
        'references': references, 'per_game': per_game, 'counts': counts,
        'source_review': source_review, 'limitations': limitations, 'scientific_assessment': 'not_performed'}
    output.mkdir()
    write_json(output / 'admission-audit.json', report)
    return report, output


def main():
    parser = argparse.ArgumentParser(description='audit explicit native corpus sources and active circumstances without fitting',
                                     allow_abbrev=False)
    parser.add_argument('--selection', required=True, action=Once)
    parser.add_argument('--out', required=True, action=Once)
    args = parser.parse_args()
    try:
        report, output = audit_selection(Path(args.selection).resolve(strict=True), args.out)
        gaps = sum(row['corpus_status'] != 'reconstructed' or row['attempt_counts'] is None
                   for row in report['per_game'])
        unavailable_sources = sum(record['interpretation_status'] == 'unavailable'
                                  for row in report['per_game'] for record in row['sources'].values())
        print(f"audit written: {len(report['per_game'])} declared games; "
              f"{gaps} population gaps; {unavailable_sources} unavailable game sources; "
              f"0 active encoding errors; {output}")
        return 0
    except (InputContractError, OSError, ValueError, TypeError, KeyError, IndexError) as error:
        print(f'corpus admission failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
