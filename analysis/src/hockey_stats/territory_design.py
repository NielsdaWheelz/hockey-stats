"""inferred longitudinal paths, directed risk and the retained-5v5 shift reference."""

from collections import Counter
from dataclasses import dataclass, field
import hashlib
import json
from math import fsum, isfinite
from pathlib import Path
import resource
import sys
from time import perf_counter

import numpy as np
from scipy.sparse import csr_matrix

from .input_locations import input_path
from .analysis_data import read_prepared_game
from .artifacts import require
from .chance_cli import identity, read_json
from .coaches import read_coaches
from .elapsed_design import actor_columns, actor_matrix, transform_context
from .execution_history import _value
from .mechanism_design import _prepared_inputs, mechanism_membership
from .reconstruct import REPORT_CODES

ZONES = ('DZ', 'NZ', 'OZ')
STARTS = (*ZONES, 'on_the_fly')
AGE_CUTS = (0, 10, 20, 40, 60, 90)
ROLE_NAMES = dict(entry=('entry_offense', 'entry_prevention'), exit=('exit_offense', 'zone_retention'))
CONTEXT_AXES = tuple(
    [dict(name=f'home_period:{side}:{period}', continuous=False, unit='indicator')
     for side in ('home', 'away') for period in ('1', '2', '3', 'OT')]
    + [dict(name=f'score:{score}', continuous=False, unit='indicator')
       for score in ('-3', '-2', '-1', '0', '1', '2', '3', 'unknown')]
    + [dict(name=f'{role}:missing_coach', continuous=False, unit='indicator')
       for role in ('attacking', 'defending')]
    + [dict(name=f'period3_score:{score}', continuous=False, unit='indicator') for score in (0, 1, 2)])
_RECIPE_DEFINITION = dict(version='territory-v1-11-1',
    equation='sum(seconds*exp(log((crossings+.5)/(seconds+30))+X*beta))-sum(count*eta)+.5*sum(precision*(beta-mean)^2)',
    context=[axis['name'] for axis in CONTEXT_AXES],
    priors=dict(player_entry_sd=.25, player_carry_sd=.10, coach_entry_sd=.10, coach_carry_sd=.05, context_sd=1, intercept_sd=2,
                history='per head and role; last positive risk; carry sd multiplied by sqrt(year gap); no age drift'),
    paths='source-order corroborated live anchors; linear home-attack x; split blue lines, memberships, contexts; conflicting clock anchors within the same supported continuous live span invalidate adjacent bridges; episode and source/report reset barriers separate conflict groups; unknown flat blue line; left-limit crossings',
    masks='mechanism_membership identity/strength union once; no ordinary-attempt/value/location-imputation masks; source/report reset barriers',
    nuisance='terminal carry only to first known stopping reset; coalesced individual ages; skater-slot risk; same-clock checked 5v5 restart; unknown outcomes censored',
    smoothing=dict(w_d='(count+.5)/(seconds+30)', h='(ended+.5)/(decidable+1)', R='(count+.5)/(row_total+1.5)', starts='unsmoothed'),
    solver=dict(maxiter=10000, ftol=1e-15, gtol=1e-6, maxcor=10, final_continuation=dict(ftol=1e-16, gtol=1e-7)))
TERRITORY_RECIPE = dict(name='territory-v1-11-1', version='territory-v1-11-1', definition=_RECIPE_DEFINITION,
    sha256=hashlib.sha256(json.dumps(_RECIPE_DEFINITION, sort_keys=True, separators=(',', ':')).encode()).hexdigest())


@dataclass
class TerritoryHeadDesign:
    season: str
    columns: tuple
    X_time: csr_matrix
    X_event: csr_matrix
    context_time: np.ndarray
    context_event: np.ndarray
    exposure_seconds: np.ndarray
    event_counts: np.ndarray
    time_keys: tuple
    event_keys: tuple
    transforms: dict


@dataclass
class TerritoryDesign:
    purpose: str
    season: str
    prepared: dict
    coaches: dict
    training_cutoff: str | None
    players: tuple
    player_facts: dict
    coach_ids: tuple
    heads: dict
    nuisance: dict
    coverage: dict
    recipe: dict
    resources: dict = field(default_factory=dict)

    @property
    def family(self):
        return 'territory'


def _zone(x):
    return None if x in (-25, 25) else 0 if x < -25 else 2 if x > 25 else 1


def _five(segment):
    members = segment['membership']
    return all(members.get(side + '_skaters') is not None and len(members[side + '_skaters']) == 5
        and members.get(side + '_goalies') is not None and len(members[side + '_goalies']) == 1 for side in ('home', 'away'))


def _children(game, membership, period, start, end):
    """a bridge may not infer across any unsupported membership interval."""
    segments = {row['segment_index']: row for row in game['segments'] or []}
    rows = []
    for chunk in game['chunks'] or []:
        segment = segments[chunk['segment_index']]
        if segment['period_number'] != period or segment['segment_index'] not in membership['included_segments'] or not _five(segment):
            continue
        left, right = max(start, chunk['start_seconds']), min(end, chunk['end_seconds'])
        if left < right:
            rows.append((left, right, segment, chunk))
    rows.sort(key=lambda row: row[:2])
    cursor = start
    for left, right, _, _ in rows:
        if left != cursor:
            return []
        cursor = right
    return rows if cursor == end else []


def territory_paths(game, membership):
    """return disjoint movement and proxy-tagged nuisance paths in home frame."""
    events = game['events'] or []
    if game['events'] is None or game['game']['report_rows'] is None:
        return dict(movement=[], nuisance=[], crossings=[], dispositions=[], exclusions=[dict(reason='source_collection_unavailable')], terminal_tails=[], report_barriers=[])
    indexes = Counter(row['source']['event_id'] for row in events)
    orders = Counter(row['source']['sort_order'] for row in events)
    period_sides = {}
    for row in events:
        source = row['source']
        if source.get('home_team_defending_side') in ('left', 'right'):
            period_sides.setdefault(source['period_number'], set()).add(source['home_team_defending_side'])
    used_reports = Counter(row['native']['report_source_index'] for row in game['associations'] or []
        if row['native'] is not None and row['native']['match_status'] == 'matched')
    report_barriers = [row for row in game['game']['report_rows'] or []
        if used_reports[row['source_index']] != 1 and (row['event_code'] in ('STOP', 'FAC', 'PENL', 'GOAL', 'PEND', 'GEND')
            or row['event_code'] not in set(REPORT_CODES.values()) | {'PGSTR', 'PGEND', 'ANTHEM', 'CHL', 'GOFF', 'GON'})]
    anchors, barriers, dispositions = [], [], []
    attempts = {row['source_index']: row['details'] for row in game.get('attempts') or []}
    kinds = {'faceoff', 'shot-on-goal', 'missed-shot', 'goal', 'blocked-shot', 'hit', 'giveaway', 'takeaway'}
    resets = {'faceoff', 'stoppage', 'penalty', 'goal', 'period-end', 'game-end'}
    for pos, event in enumerate(events):
        source, geometry = event['source'], event['geometry']
        clock = source['elapsed_seconds']
        valid = (source['kind_valid'] and source['timed_period'] is True and source['period_number'] in (1, 2, 3, 4)
            and clock is not None and isfinite(clock) and clock >= 0 and _value(event['chronology'], 'order_index') is not None
            and source['event_id'] is not None and indexes[source['event_id']] == 1
            and source['sort_order'] is not None and orders[source['sort_order']] == 1
            and source.get('home_team_defending_side') in ('left', 'right') and len(period_sides.get(source['period_number'], ())) == 1)
        x = _value(geometry, 'x_ft')
        frame = _value(geometry, 'frame')
        if x is not None and (not isfinite(x) or not -100 <= x <= 100 or frame != 'home_attack'):
            valid = False
        if not valid or source['type_key'] in resets:
            barriers.append((pos, event, not valid))
        episode = _value(event['chronology'], 'episode_index')
        ordinary = source['type_key'] not in ('shot-on-goal', 'missed-shot', 'goal') or _value(attempts.get(source['source_index']), 'physical_status') == 'ordinary'
        anchor_valid = valid and ordinary and source['type_key'] in kinds and x is not None and episode is not None
        if anchor_valid:
            anchors.append(dict(position=pos, source_index=source['source_index'], period=source['period_number'], seconds=clock,
                x=x, episode=episode, kind=source['type_key']))
        reasons = []
        if not source['kind_valid'] or not ordinary:
            reasons.append('event_kind_unresolved')
        if source['timed_period'] is not True or source['period_number'] not in (1, 2, 3, 4) or clock is None or not isfinite(clock) or clock < 0:
            reasons.append('clock_unresolved')
        if _value(event['chronology'], 'order_index') is None or source['event_id'] is None or indexes[source['event_id']] != 1 or source['sort_order'] is None or orders[source['sort_order']] != 1:
            reasons.append('source_order_unresolved')
        if source.get('home_team_defending_side') not in ('left', 'right') or len(period_sides.get(source['period_number'], ())) != 1 or x is not None and frame != 'home_attack':
            reasons.append('orientation_unresolved')
        dispositions.append(dict(source_index=source['source_index'], usable_anchor=bool(anchor_valid),
            reason=None if valid else 'source_clock_order_or_frame_unresolved', territory_reasons=sorted(set(reasons))))
    conflicts = set()
    clock_groups = []
    for anchor in anchors:
        previous = clock_groups[-1][-1] if clock_groups else None
        same_span = previous is not None and all(anchor[key] == previous[key] for key in ('period', 'seconds', 'episode'))
        if same_span:
            same_span = previous['kind'] != 'goal' and anchor['kind'] != 'faceoff' and not any(
                previous['position'] < pos < anchor['position'] for pos, _, _ in barriers)
        if same_span:
            same_span = not any((row['period_number'] is None or row['period_number'] == anchor['period']) and
                (row['elapsed_seconds'] is None or row['elapsed_seconds'] == anchor['seconds']) for row in report_barriers)
        if not same_span:
            clock_groups.append([])
        clock_groups[-1].append(anchor)
    for group in clock_groups:
        if len({row['x'] for row in group}) > 1:
            conflicts.update(row['position'] for row in group)
    movement, exclusions = [], []
    for left, right in zip(anchors, anchors[1:]):
        reason = None
        if left['position'] in conflicts or right['position'] in conflicts:
            reason = 'contradictory_equal_clock_anchors'
        elif left['episode'] != right['episode'] or left['period'] != right['period'] or right['seconds'] <= left['seconds']:
            reason = 'different_live_span_or_nonpositive_time'
        elif any(left['position'] <= pos <= right['position'] and (bad or left['position'] < pos < right['position']
                or pos == left['position'] and left['kind'] == 'goal') for pos, _, bad in barriers):
            reason = 'source_reset_or_unknown_barrier'
        elif any((row['period_number'] is None or row['period_number'] == left['period']) and
                (row['elapsed_seconds'] is None or left['seconds'] <= row['elapsed_seconds'] <= right['seconds']) for row in report_barriers):
            reason = 'report_only_reset_or_unknown_barrier'
        children = _children(game, membership, left['period'], left['seconds'], right['seconds']) if reason is None else []
        if reason is None and not children:
            reason = 'strength_or_membership_barrier'
        if reason:
            exclusion = dict(left=left['source_index'], right=right['source_index'], seconds=max(0, right['seconds']-left['seconds']), reason=reason)
            if reason == 'different_live_span_or_nonpositive_time':
                backward = right['period'] < left['period'] or right['period'] == left['period'] and right['seconds'] < left['seconds']
                exclusion['territory_reasons'] = ['clock_unresolved'] if backward else []
            exclusions.append(exclusion)
            continue
        duration, distance = right['seconds']-left['seconds'], right['x']-left['x']
        blue = [left['seconds']+(x-left['x'])*duration/distance for x in (-25, 25)
                if distance and min(left['x'], right['x']) < x < max(left['x'], right['x'])]
        for start, end, segment, chunk in children:
            cuts = sorted({start, end, *(t for t in blue if start < t < end)})
            for a, b in zip(cuts, cuts[1:]):
                zone = _zone(left['x']+distance*((a+b)/2-left['seconds'])/duration)
                if zone is None:
                    exclusions.append(dict(left=left['source_index'], right=right['source_index'], seconds=b-a, reason='positive_duration_on_blue_line'))
                    continue
                movement.append(dict(period_number=left['period'], start_seconds=a, end_seconds=b, zone=zone,
                    segment_index=segment['segment_index'], chunk_index=chunk['chunk_index'], episode_index=left['episode'],
                    left_source_index=left['source_index'], right_source_index=right['source_index'], kind='interpolated'))
    crossings = []
    for risk_index, (left, right) in enumerate(zip(movement, movement[1:])):
        if left['period_number'] != right['period_number'] or left['episode_index'] != right['episode_index'] or left['end_seconds'] != right['start_seconds'] or abs(left['zone']-right['zone']) != 1:
            continue
        before, after = left['zone'], right['zone']
        head = 'entry' if before == 1 else 'exit'
        side = 'home' if (before, after) in ((0, 1), (1, 2)) else 'away'
        crossings.append(dict(period_number=left['period_number'], seconds=left['end_seconds'], from_zone=before, to_zone=after,
            head=head, attacking_side=side, risk_index=risk_index, segment_index=left['segment_index'], chunk_index=left['chunk_index'],
            crossing_key=f"{game['game_id']}:{left['period_number']}:{left['end_seconds']!r}:{before}:{after}"))
    nuisance = list(movement)
    tails = []
    for episode in game['episodes'] or []:
        within = [row for row in anchors if row['episode'] == episode['episode_index'] and row['position'] not in conflicts]
        if not within or episode['end_reason'] not in ('reset', 'terminal'):
            continue
        last = within[-1]
        terminal = next((row for row in events if row['source']['source_index'] == episode['end_source_index']), None)
        if terminal is None or terminal['source']['type_key'] not in ('stoppage', 'penalty', 'goal', 'period-end', 'game-end'):
            continue
        stop_pos = next(i for i, row in enumerate(events) if row is terminal)
        end = terminal['source']['elapsed_seconds']
        if end is None or end <= last['seconds'] or _zone(last['x']) is None:
            continue
        if any(last['position'] < pos <= stop_pos for pos in conflicts) or any(last['position'] < pos <= stop_pos and (bad or pos < stop_pos) for pos, _, bad in barriers):
            continue
        if any((row['period_number'] is None or row['period_number'] == last['period']) and
                (row['elapsed_seconds'] is None or last['seconds'] <= row['elapsed_seconds'] <= end) for row in report_barriers):
            continue
        children = _children(game, membership, last['period'], last['seconds'], end)
        for start, finish, segment, chunk in children:
            nuisance.append(dict(period_number=last['period'], start_seconds=start, end_seconds=finish, zone=_zone(last['x']),
                segment_index=segment['segment_index'], chunk_index=chunk['chunk_index'], episode_index=last['episode'],
                left_source_index=last['source_index'], right_source_index=terminal['source']['source_index'], kind='terminal_carry'))
        if children:
            tails.append(dict(period_number=last['period'], anchor_source_index=last['source_index'], stop_source_index=terminal['source']['source_index'], seconds=end-last['seconds']))
    nuisance.sort(key=lambda row: (row['period_number'], row['start_seconds']))
    reason_mapping = {
        'contradictory_equal_clock_anchors': ['conflicting_anchors'],
        'source_reset_or_unknown_barrier': ['event_kind_unresolved'],
        'report_only_reset_or_unknown_barrier': ['report_barrier_unresolved'],
        'strength_or_membership_barrier': ['membership_or_horizon_unavailable'],
        'positive_duration_on_blue_line': ['zone_unavailable']}
    for row in exclusions:
        if row['reason'] != 'different_live_span_or_nonpositive_time':
            row['territory_reasons'] = reason_mapping[row['reason']]
    for row in dispositions:
        if any(anchor['source_index'] == row['source_index'] and anchor['position'] in conflicts for anchor in anchors):
            row['territory_reasons'] = sorted(set(row['territory_reasons']) | {'conflicting_anchors'})
    return dict(movement=movement, nuisance=nuisance, crossings=crossings, dispositions=dispositions, exclusions=exclusions, terminal_tails=tails,
        report_barriers=[dict(source_index=row['source_index'], period_number=row['period_number'], seconds=row['elapsed_seconds'], code=row['event_code']) for row in report_barriers])


def _age_known(shift, game):
    return not any(game['issues'][i]['code'] == 'participation_start_left_censored' for i in shift['issue_indices'])


def nuisance_statistics(game, paths, membership):
    """count slot risks, decidable endpoints, team restarts and actual new shifts."""
    counts = {key: np.zeros(shape, dtype=float if key == 'risk_seconds' else np.int64) for key, shape in (
        ('risk_seconds', (3, 6)), ('whistles', (3, 6)), ('live_endings', (3, 6)),
        ('decidable_whistles', (3, 6)), ('ended_whistles', (3, 6)),
        ('restart_counts', (3, 3)), ('start_counts', (4,)), ('on_the_fly_zone_counts', (3,)))}
    segments = {row['segment_index']: row for row in game['segments'] or []}
    shifts = game['player_shifts'] or []
    events = game['events'] or []
    by_source = {row['source']['source_index']: row for row in events}
    positions = {row['source']['source_index']: i for i, row in enumerate(events)}
    identity = game['game']['identity'] or game['game']['inventory']
    exclusions, trials, pairs, starts = [], [], [], []
    path_slot_seconds = 10*fsum(row['end_seconds']-row['start_seconds'] for row in paths['nuisance'])
    terminal_carry_slot_seconds = 10*fsum(row['end_seconds']-row['start_seconds'] for row in paths['nuisance'] if row['kind'] == 'terminal_carry')
    known_age_carry_slot_seconds, unknown_age_slot_seconds = 0., 0.
    for path in paths['nuisance']:
        segment = segments[path['segment_index']]
        for side in ('home', 'away'):
            zone = path['zone'] if side == 'home' else 2-path['zone']
            for player in segment['membership'][side+'_skaters']:
                selected = [shift for shift in shifts if str(shift['player_id']) == str(player) and shift['period_number'] == path['period_number']
                    and shift['start_seconds'] <= path['start_seconds'] < path['end_seconds'] <= shift['end_seconds'] and _age_known(shift, game)]
                if len(selected) != 1:
                    unknown_age_slot_seconds += path['end_seconds']-path['start_seconds']
                    continue
                shift = selected[0]
                cuts = sorted({path['start_seconds'], path['end_seconds'], *(shift['start_seconds']+age for age in AGE_CUTS[1:]
                    if path['start_seconds'] < shift['start_seconds']+age < path['end_seconds'])})
                for left, right in zip(cuts, cuts[1:]):
                    b = int(np.searchsorted(AGE_CUTS[1:], (left+right)/2-shift['start_seconds'], side='right'))
                    counts['risk_seconds'][zone, b] += right-left
                    if path['kind'] == 'terminal_carry':
                        known_age_carry_slot_seconds += right-left
    endpoints = {}
    for episode in game['episodes'] or []:
        if episode['end_reason'] not in ('reset', 'terminal'):
            continue
        end = by_source.get(episode['end_source_index'])
        if end is None or end['source']['elapsed_seconds'] is None:
            continue
        key = (episode['period_number'], end['source']['elapsed_seconds'])
        endpoints.setdefault(key, []).append(end)
    stopped = set(endpoints)
    checked_starts = {row['start_source_index'] for row in game['episodes'] or [] if row['start_kind'] == 'faceoff'}
    action_kinds = {'hit', 'giveaway', 'takeaway', 'shot-on-goal', 'missed-shot', 'blocked-shot', 'goal'}
    for (period, clock), closing in sorted(endpoints.items()):
        terminal = min(closing, key=lambda row: positions[row['source']['source_index']])
        restart, reason = None, 'restart_unproved'
        for event in events[positions[terminal['source']['source_index']]+1:]:
            source = event['source']
            if source['period_number'] != period or source['elapsed_seconds'] != clock or not source['kind_valid'] or _value(event['chronology'], 'order_index') is None:
                if source['type_key'] == 'faceoff' and source['period_number'] == period and source['elapsed_seconds'] is not None and source['elapsed_seconds'] != clock:
                    reason = 'restart_clock_mismatch'
                break
            if source['type_key'] in action_kinds or source['type_key'] in ('period-end', 'game-end'):
                break
            if source['type_key'] == 'faceoff':
                if source['source_index'] in checked_starts:
                    restart = event
                break
        if terminal['source']['type_key'] in ('period-end', 'game-end'):
            restart = None
            reason = 'period_or_game_end'
        left = [row for row in paths['nuisance'] if row['period_number'] == period and row['start_seconds'] < clock <= row['end_seconds']]
        right = [row for row in segments.values() if row['period_number'] == period and row['start_seconds'] <= clock < row['end_seconds']
            and row['segment_index'] in membership['included_segments'] and _five(row)]
        # unmatched reset rows prevent an api-only instantaneous restart claim.
        if any(row['period_number'] in (None, period) and row['seconds'] in (None, clock) for row in paths['report_barriers']):
            restart = None
            reason = 'report_barrier_unresolved'
        if restart is None or len(left) != 1 or len(right) != 1:
            exclusions.append(dict(kind='censored_endpoint', period_number=period, seconds=clock, reason=reason if restart is None else 'membership_or_horizon_unavailable'))
            continue
        restart_zone = _zone(_value(restart['geometry'], 'x_ft')) if _value(restart['geometry'], 'x_ft') is not None else None
        if restart_zone is None:
            exclusions.append(dict(kind='censored_endpoint', period_number=period, seconds=clock, reason='zone_unavailable'))
            continue
        path, after = left[0], right[0]
        before = segments[path['segment_index']]
        for side in ('home', 'away'):
            zone = path['zone'] if side == 'home' else 2-path['zone']
            target = restart_zone if side == 'home' else 2-restart_zone
            counts['restart_counts'][zone, target] += 1
            pairs.append(dict(period_number=period, seconds=clock, side=side, zone=zone, restart_zone=target))
            unknown_age, unknown_endpoint = False, False
            for player in before['membership'][side+'_skaters']:
                selected = [shift for shift in shifts if str(shift['player_id']) == str(player) and shift['period_number'] == period
                    and shift['start_seconds'] < clock <= shift['end_seconds'] and _age_known(shift, game)]
                if len(selected) != 1:
                    unknown_age = True
                    continue
                shift = selected[0]
                # a terminal event belongs to the age bin immediately before it.
                age = clock-shift['start_seconds']
                b = int(np.searchsorted(AGE_CUTS[1:], age, side='left'))
                counts['whistles'][zone, b] += 1
                present = str(player) in set(map(str, after['membership'][side+'_skaters']))
                outcome = 'ended' if shift['end_seconds'] == clock and not present else 'continued' if shift['end_seconds'] > clock and present else 'unknown'
                unknown_endpoint |= outcome == 'unknown'
                if outcome != 'unknown':
                    counts['decidable_whistles'][zone, b] += 1
                    counts['ended_whistles'][zone, b] += outcome == 'ended'
                trials.append(dict(player_id=str(player), period_number=period, seconds=clock, zone=zone, age_bin=b, outcome=outcome))
            if unknown_age:
                exclusions.append(dict(kind='censored_endpoint', period_number=period, seconds=clock, reason='shift_age_unavailable'))
            if unknown_endpoint:
                exclusions.append(dict(kind='censored_endpoint', period_number=period, seconds=clock, reason='shift_endpoint_unresolved'))
    for shift in shifts:
        player, period = str(shift['player_id']), shift['period_number']
        side = next((side for side in ('home', 'away') if shift['team_id'] == identity[side+'_team_id']), None)
        if side is None or not _age_known(shift, game):
            continue
        clock = shift['end_seconds']
        if (period, clock) not in stopped:
            before = [row for row in paths['nuisance'] if row['period_number'] == period and row['start_seconds'] < clock <= row['end_seconds']]
            after = [row for row in paths['nuisance'] if row['period_number'] == period and row['start_seconds'] <= clock < row['end_seconds']]
            if len(before) == len(after) == 1:
                left_members = set(map(str, segments[before[0]['segment_index']]['membership'][side+'_skaters']))
                right_members = set(map(str, segments[after[0]['segment_index']]['membership'][side+'_skaters']))
                if player in left_members and player not in right_members:
                    zone = before[0]['zone'] if side == 'home' else 2-before[0]['zone']
                    b = int(np.searchsorted(AGE_CUTS[1:], clock-shift['start_seconds'], side='left'))
                    counts['live_endings'][zone, b] += 1
        clock, kind = shift['start_seconds'], _value(shift['start'], 'kind')
        right = [row for row in segments.values() if row['period_number'] == period and row['start_seconds'] <= clock < row['end_seconds']
            and row['segment_index'] in membership['included_segments'] and _five(row) and player in set(map(str, row['membership'][side+'_skaters']))]
        zone = None
        if len(right) == 1 and kind == 'faceoff':
            event_index = _value(shift['start'], 'event_source_index')
            event = by_source.get(event_index)
            if event_index in checked_starts and event is not None and event['source']['elapsed_seconds'] == clock:
                x = _value(event['geometry'], 'x_ft')
                zone = _zone(x) if x is not None else None
                if zone is not None and side == 'away':
                    zone = 2-zone
        elif len(right) == 1 and kind == 'on_the_fly':
            live = [row for row in paths['nuisance'] if row['period_number'] == period and row['start_seconds'] <= clock < row['end_seconds']]
            if len(live) == 1:
                zone = live[0]['zone'] if side == 'home' else 2-live[0]['zone']
        if zone is None:
            exclusions.append(dict(kind='excluded_start', player_id=player, period_number=period, seconds=clock, reason='zone_unavailable' if kind in ('faceoff', 'on_the_fly') and len(right) == 1 else 'shift_endpoint_unresolved'))
            continue
        start = 3 if kind == 'on_the_fly' else zone
        counts['start_counts'][start] += 1
        if start == 3:
            counts['on_the_fly_zone_counts'][zone] += 1
        starts.append(dict(player_id=player, period_number=period, seconds=clock, start_type=STARTS[start], zone=zone))
    # endpoint reasons describe physical groups; a reason shared by both teams
    # counts once and never invents an endpoint for an unlocatable gap.
    dedup = {(row['period_number'], row['seconds'], row['reason']): row for row in exclusions if row['kind'] == 'censored_endpoint'}
    exclusions = [row for row in exclusions if row['kind'] != 'censored_endpoint']+list(dedup.values())
    require(abs(float(counts['risk_seconds'].sum())+unknown_age_slot_seconds-path_slot_seconds) <= 1e-9+1e-9*path_slot_seconds, 'nuisance known/unknown-age slot time fails closure')
    return dict(**counts, trials=trials, restart_pairs=pairs, starts=starts, exclusions=exclusions,
        path_slot_seconds=path_slot_seconds, terminal_carry_slot_seconds=terminal_carry_slot_seconds,
        known_age_terminal_carry_slot_seconds=known_age_carry_slot_seconds, unknown_age_slot_seconds=unknown_age_slot_seconds,
        terminal_lags=[row['seconds'] for row in paths['terminal_tails']])


def _context(side, period, score, coach):
    other = 'away' if side == 'home' else 'home'
    margin = score[side]-score[other] if score.get(side) is not None and score.get(other) is not None else None
    level = str(max(-3, min(3, margin))) if margin is not None else 'unknown'
    values = {f'home_period:{side}:{period if period <= 3 else "OT"}': 1., f'score:{level}': 1.,
        'attacking:missing_coach': float(coach[side]['coach_id'] is None),
        'defending:missing_coach': float(coach[other]['coach_id'] is None)}
    for value in (0, 1, 2):
        values[f'period3_score:{value}'] = float(period == 3 and margin == value)
    return [values.get(axis['name'], 0.) for axis in CONTEXT_AXES], margin


def prepare_territory(prepared, coaches, season):
    """stream each selected game once into both heads and annual nuisance counts."""
    started = perf_counter()
    prepared, selected, players, facts, prepared_ref = _prepared_inputs(prepared, season)
    coach_path = input_path(coaches, strict=True)
    coach_data = read_coaches(coach_path, prepared['purpose'])
    coach_games = {row['game_id']: row for row in coach_data['games'] if row['season'] == season}
    require(set(selected['selected_game_ids']) <= set(coach_games), 'coaches omit selected territory games')
    coach_ref = dict(purpose=prepared['purpose'], **identity(coach_path), selected_game_ids=list(selected['selected_game_ids']))
    coach_ids = tuple(sorted(row['coach_id'] for row in read_json(coach_path.parent/'identities.json')['coaches']))
    actors = [col for col in actor_columns(players, coach_ids) if col.get('kind') != 'actor' or col.get('subblock') == 'base']
    rows = {head: dict(time=[], event=[]) for head in ('entry', 'exit')}
    coverage = {p: dict(included_seconds=0., crossings=0, roles={role: dict(risk_seconds=0., crossings=0) for pair in ROLE_NAMES.values() for role in pair}) for p in players}
    games, dates, nuisance_games = [], [], []
    for game_id in selected['selected_game_ids']:
        game = read_prepared_game(prepared, season, game_id)
        require(game['game']['identity'] is None or all(game['game']['identity'][key] == coach_games[game_id][key] for key in ('home_team_id', 'away_team_id')), 'territory coach team identity differs')
        membership = mechanism_membership(game)
        paths = territory_paths(game, membership)
        nuisance_games.append(nuisance_statistics(game, paths, membership))
        segments = {row['segment_index']: row for row in game['segments'] or []}
        chunks = {row['chunk_index']: row for row in game['chunks'] or []}
        # the physical path is disjoint; qualification counts its union once.
        risk_rows = {}
        for risk_index, path in enumerate(paths['movement']):
            segment = segments[path['segment_index']]
            duration = path['end_seconds']-path['start_seconds']
            for side in ('home', 'away'):
                for player in segment['membership'][side+'_skaters']:
                    require(str(player) in coverage, 'territory participant missing from annual identity axis')
                    coverage[str(player)]['included_seconds'] += duration
            head = 'entry' if path['zone'] == 1 else 'exit'
            sides = ('home', 'away') if head == 'entry' else ('home',) if path['zone'] == 0 else ('away',)
            for side in sides:
                other = 'away' if side == 'home' else 'home'
                raw, margin = _context(side, path['period_number'], chunks[path['chunk_index']]['score']['values'], coach_games[game_id])
                key = dict(game_id=game_id, period_number=path['period_number'], start_seconds=path['start_seconds'], end_seconds=path['end_seconds'],
                    segment_index=path['segment_index'], chunk_index=path['chunk_index'], attacking_side=side,
                    attacking_players=list(map(str, segment['membership'][side+'_skaters'])), defending_players=list(map(str, segment['membership'][other+'_skaters'])),
                    zone=path['zone'], left_source_index=path['left_source_index'], right_source_index=path['right_source_index'])
                risk_row = (key, duration, raw, margin, path['period_number'])
                rows[head]['time'].append(risk_row)
                risk_rows[(risk_index, side, head)] = risk_row
                for role, member_key in zip(ROLE_NAMES[head], ('attacking_players', 'defending_players'), strict=True):
                    for player in key[member_key]:
                        coverage[player]['roles'][role]['risk_seconds'] += duration
        for crossing in paths['crossings']:
            path = paths['movement'][crossing['risk_index']]
            side, head = crossing['attacking_side'], crossing['head']
            risk_row = risk_rows.get((crossing['risk_index'], side, head))
            require(risk_row is not None, 'inferred crossing has no unique left-limit risk row')
            key, _, raw, margin, period = risk_row
            rows[head]['event'].append((dict(key, **crossing), 1, raw, margin, period))
            for role, member_key in zip(ROLE_NAMES[head], ('attacking_players', 'defending_players'), strict=True):
                for player in key[member_key]:
                    coverage[player]['roles'][role]['crossings'] += 1
                    coverage[player]['crossings'] += 1
        games.append(dict(game_id=game_id, **paths, membership_reasons=membership['reasons'], excluded_segment_union=sorted(membership['excluded_segments']),
            unquantified_gap=membership['unquantified_gap'], physical_known_seconds=fsum(row['end_seconds']-row['start_seconds'] for row in paths['movement'])))
        dates.append(game['game']['inventory']['game_date'])
    heads = {}
    for head, selected_rows in rows.items():
        time, event = selected_rows['time'], selected_rows['event']
        seconds = np.asarray([row[1] for row in time], dtype=float)
        counts = np.asarray([row[1] for row in event], dtype=np.int64)
        raw_time = np.asarray([row[2] for row in time], dtype=float).reshape(-1, len(CONTEXT_AXES))
        raw_event = np.asarray([row[2] for row in event], dtype=float).reshape(-1, len(CONTEXT_AXES))
        context_time, context_event, moments = transform_context(raw_time, raw_event, seconds, [False]*len(CONTEXT_AXES))
        transforms = dict(axes=[dict(axis, location=moment['location'], scale=moment['scale'],
            available_seconds=moment['available_hours'], missing_seconds=moment['missing_hours'])
            for axis, moment in zip(CONTEXT_AXES, moments, strict=True)])
        columns = tuple(actors+[dict(kind='context', name=axis['name']) for axis in CONTEXT_AXES])
        transforms['design_sha256'] = hashlib.sha256(json.dumps(dict(recipe=TERRITORY_RECIPE['sha256'], head=head, columns=columns, transforms=transforms), sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        heads[head] = TerritoryHeadDesign(season, columns, actor_matrix(time, actors, coach_games, family='territory'), actor_matrix(event, actors, coach_games, family='territory'),
            context_time, context_event, seconds, counts, tuple(row[0] for row in time), tuple(row[0] for row in event), transforms)
    shapes = dict(risk_seconds=(3, 6), whistles=(3, 6), live_endings=(3, 6), decidable_whistles=(3, 6), ended_whistles=(3, 6), restart_counts=(3, 3), start_counts=(4,), on_the_fly_zone_counts=(3,))
    nuisance = {key: sum((row[key] for row in nuisance_games), start=np.zeros(shape, dtype=float if key == 'risk_seconds' else np.int64)).tolist() for key, shape in shapes.items()}
    nuisance.update(path_slot_seconds=fsum(row['path_slot_seconds'] for row in nuisance_games),
        terminal_carry_slot_seconds=fsum(row['terminal_carry_slot_seconds'] for row in nuisance_games),
        known_age_terminal_carry_slot_seconds=fsum(row['known_age_terminal_carry_slot_seconds'] for row in nuisance_games),
        unknown_age_slot_seconds=fsum(row['unknown_age_slot_seconds'] for row in nuisance_games),
        terminal_lags=[lag for row in nuisance_games for lag in row['terminal_lags']],
        games=[dict(game_id=game['game_id'], **{key: value for key, value in row.items() if key not in shapes}) for game, row in zip(games, nuisance_games, strict=True)])
    physical = fsum(row['physical_known_seconds'] for row in games)
    slot = fsum(row['included_seconds'] for row in coverage.values())
    require(abs(slot-10*physical) <= 1e-9+1e-9*max(slot, 10*physical), 'territory physical/player-slot time mismatch')
    nz_seconds = fsum(row['end_seconds']-row['start_seconds'] for game in games for row in game['movement'] if row['zone'] == 1)
    end_seconds = physical-nz_seconds
    require(abs(float(heads['entry'].exposure_seconds.sum())-2*nz_seconds) <= 1e-9+1e-9*2*nz_seconds, 'entry directed/physical risk mismatch')
    require(abs(float(heads['exit'].exposure_seconds.sum())-end_seconds) <= 1e-9+1e-9*end_seconds, 'exit directed/physical risk mismatch')
    role_seconds = {role: fsum(row['roles'][role]['risk_seconds'] for row in coverage.values()) for pair in ROLE_NAMES.values() for role in pair}
    for head, roles in ROLE_NAMES.items():
        expected = 5*float(heads[head].exposure_seconds.sum())
        for role in roles:
            require(abs(role_seconds[role]-expected) <= 1e-9+1e-9*expected, 'territory per-role slot time fails closure')
    summary = dict(purpose=prepared['purpose'], season=season, players=coverage, qualification=coverage, games=games,
        physical_known_seconds=physical, player_slot_seconds=slot, neutral_zone_seconds=nz_seconds, end_zone_seconds=end_seconds, role_slot_seconds=role_seconds,
        directed_entry_seconds=float(heads['entry'].exposure_seconds.sum()), directed_exit_seconds=float(heads['exit'].exposure_seconds.sum()),
        crossings=sum(len(row['crossings']) for row in games))
    return TerritoryDesign(prepared['purpose'], season, prepared_ref, coach_ref, max(dates) if dates else None,
        players, facts, coach_ids, heads, nuisance, summary, TERRITORY_RECIPE,
        dict(preparation_seconds=perf_counter()-started, preparation_peak_resident_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*(1 if sys.platform == 'darwin' else 1024),
            preparation_memory_scope='process high-water mark through single-pass source preparation; not incremental allocation'))
