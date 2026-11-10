"""matched source support and fixed elapsed encoding for positive 5v5 rates."""

from dataclasses import dataclass, field
from functools import cache
import hashlib
import json
from math import fsum
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.sparse import csr_matrix, vstack

from .analysis_data import PreparedManifest, read_prepared, read_prepared_game, read_prepared_people
from .analysis_context import shift_start_precedes_event
from .artifacts import ordered_array_digest, require
from .attribution import build_shape_basis
from .chance_cli import identity, read_json
from .coaches import read_coaches
from .execution import iter_neutral_origins
from .execution_history import _value
from .execution_scores import ExecutionScores, read_execution_scores, read_panel
from .shot_origins import grid

STARTS = ('offensive', 'neutral', 'defensive', 'on_the_fly', 'unknown')
AGES = ('0:10', '10:20', '20:40', '40:60', '60:90', '90+', 'unknown')
REST = ('00', '01', '10', '11', 'unknown')
TRANSITIONS = ('none', 'previously_advantaged', 'previously_shorthanded', 'unknown')
CURRENT = ('toi_all_seconds', 'toi_5v5_seconds', 'attempts', 'goals', 'shifts_begun', 'shifts_completed')
DATED = ('ice_appearances', 'toi_all_seconds', 'toi_5v5_seconds', 'shifts', 'attempts', 'goals', 'sog')
WORKLOAD_PARTS = ('complete_mean', 'partial_known_mean', 'complete_fraction', 'partial_fraction', 'missing_fraction')
DEFINITION = dict(version='spatial-v1-08-4', support_policy='ordinary-attempt-segment-valued-union-1',
    roles=['attacking', 'defending'], coach_subblocks=['base', *[f'score:{i}' for i in range(-2, 3)], 'shell'],
    home_period=['home:1', 'home:2', 'home:3', 'home:OT', 'away:1', 'away:2', 'away:3', 'away:OT'],
    score=[str(i) for i in range(-3, 4)] + ['unknown'], bands=list(range(6)) + ['OT'],
    starts=list(STARTS), ages=list(AGES), rest=list(REST), transition=list(TRANSITIONS),
    transition_frame='one attacking-frame block; opposite defending indicators are exact duplicates',
    current_workload=list(CURRENT), dated_workload=list(DATED), workload_parts=list(WORKLOAD_PARTS),
    centering='matched directed elapsed exposure; available-only means; absent transformed zero',
    scaling='continuous exposure standard deviation; categorical scale one; zero variance scale one',
    event='saved elapsed covariates with authoritative pre-event score and saved pre-event strength transition; no following-chunk reset state',
    event_shift_start='faceoff requires saved anchor chronology strictly before focal order; on-the-fly requires saved shift start clock strictly before focal clock; future/equal/unresolved becomes unknown start preserving saved shift age; elapsed starts unchanged',
    units='seconds before standardization',
    reference='virtual centered linear design; five neutral slots per player role', modes=40,
    penalties=dict(player_entry=16., player_carry=100., coach_entry=100., coach_carry=400.,
                   context=1., context_shape=160., intercept=.25, intercept_shape=40., age=64.))
RECIPE = dict(name='experimental-v1', version=DEFINITION['version'], definition=DEFINITION,
              sha256=hashlib.sha256(json.dumps(DEFINITION, sort_keys=True, separators=(',', ':')).encode()).hexdigest())


@dataclass
class SpatialDesign:
    purpose: str
    season: str
    prepared: dict
    coaches: dict
    valued: dict
    training_cutoff: str | None
    players: tuple
    player_facts: dict
    coach_ids: tuple
    columns: tuple
    X_time: csr_matrix
    X_event: csr_matrix
    context_time: np.ndarray
    context_event: np.ndarray
    exposure_hours: np.ndarray
    time_keys: tuple
    event_keys: tuple
    event_offsets: np.ndarray
    origin_cells: np.ndarray
    origin_weights: np.ndarray
    neutral_goal_probability: np.ndarray
    transforms: dict
    coverage: dict
    recipe: dict
    resources: dict = field(default_factory=dict)
    basis: np.ndarray | None = None
    basis_identity: dict = field(default_factory=dict)
    annual_offsets: dict = field(default_factory=dict)

ST_STATES = ('5v4', '5v3', '4v3')
ST_ROLE_COUNTS = ((5, 4), (5, 3), (4, 3))
ST_DEFINITION = dict(DEFINITION, version='spatial-st-v1-09-1',
    support_policy='ordinary-attempt-segment-valued-advantaged-union-1',
    coach_subblocks=['base'], score_clock=False,
    state_order=list(ST_STATES), role_counts=[list(value) for value in ST_ROLE_COUNTS],
    centering='pooled matched physical special-teams exposure; available-only means; absent transformed zero',
    reference='virtual centered linear design; exact physical state player slot counts')
ST_RECIPE = dict(name='experimental-v1', version=ST_DEFINITION['version'], definition=ST_DEFINITION,
    sha256=hashlib.sha256(json.dumps(ST_DEFINITION, sort_keys=True, separators=(',', ':')).encode()).hexdigest())


@dataclass
class SpecialTeamsDesign(SpatialDesign):
    state_time: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=np.int64))
    state_event: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=np.int64))
    basis_source: dict = field(default_factory=dict)

    @property
    def family(self):
        return 'st'

    @property
    def role_counts(self):
        return ST_ROLE_COUNTS


def _workload_values(records, counter):
    """complete and partial members are disjoint; a known zero is evidence."""
    complete, partial = [], []
    for record in records:
        value, known = _value(record, counter), _value(record, 'known_' + counter)
        if value is not None:
            complete.append(value)
        elif known is not None:
            partial.append(known)
    count = len(records)
    require(count > 0, 'workload requires physical unit members')
    return (fsum(complete) / len(complete) if complete else np.nan,
            fsum(partial) / len(partial) if partial else np.nan,
            len(complete) / count, len(partial) / count, (count - len(complete) - len(partial)) / count)


def _context_axes(family='ev'):
    axes = []
    def add(name, continuous=False, unit='fraction'):
        axes.append(dict(name=name, continuous=continuous, unit=unit))
    for side in ('home', 'away'):
        for period in ('1', '2', '3', 'OT'):
            add(f'home_period:{side}:{period}')
    for score in DEFINITION['score']:
        if family == 'st':
            add(f'score:{score}')
        else:
            for band in DEFINITION['bands']:
                add(f'score_band:{score}:{band}')
    for role in ('attacking', 'defending'):
        add(f'{role}:missing_coach')
        for start in STARTS:
            for age in AGES:
                add(f'{role}:start_age:{start}:{age}')
        for rest in REST:
            add(f'{role}:rest:{rest}')
        for scope, counters in (('current', CURRENT), ('days_7', DATED), ('days_14', DATED)):
            for counter in counters:
                for part in WORKLOAD_PARTS:
                    add(f'{role}:{scope}:{counter}:{part}', part.endswith('mean'),
                        'seconds' if counter.startswith('toi_') and part.endswith('mean') else
                        'count' if part.endswith('mean') else 'fraction')
    for transition in TRANSITIONS:
        add(f'transition:{transition}')
    return tuple(axes)


CONTEXT_AXES = _context_axes()
ST_CONTEXT_AXES = _context_axes('st')


def _age_bin(value):
    if value is None:
        return 'unknown'
    return AGES[int(np.searchsorted((10, 20, 40, 60, 90), value, side='right'))]


def _context(game, segment, chunk, side, coach_game, score, transition, *, focal_order=None, focal_seconds=None, order_by_source=None, family='ev'):
    other = 'away' if side == 'home' else 'home'
    period = segment['period_number']
    period_label = str(period) if period <= 3 else 'OT'
    band = int((period - 1) * 2 + chunk['start_seconds'] // 600) if period <= 3 else 'OT'
    # a terminal event uses its final child's left endpoint, including its time band.
    margin = score.get(side) - score.get(other) if score.get(side) is not None and score.get(other) is not None else None
    score_level = str(max(-3, min(3, margin))) if margin is not None else 'unknown'
    score_column = f'score:{score_level}' if family == 'st' else f'score_band:{score_level}:{band}'
    raw = {f'home_period:{side}:{period_label}': 1., score_column: 1.}
    members = {str(row['player_id']): row for row in chunk['member_contexts']}
    shifts = game['player_shifts'] or []
    for role, source_side in (('attacking', side), ('defending', other)):
        ids = [str(p) for p in segment['membership'][source_side + '_skaters']]
        require(len(ids) in (3, 4, 5) if family == 'st' else len(ids) == 5, 'invalid physical unit size')
        raw[f'{role}:missing_coach'] = float(coach_game[source_side]['coach_id'] is None)
        for player in ids:
            context = members[player]
            index = context['player_shift_index']
            shift = shifts[index] if index is not None else None
            start = _value(shift['start'], 'kind') if shift else None
            if start in ('faceoff', 'on_the_fly') and order_by_source is not None and not shift_start_precedes_event(
                    start, shift['start_seconds'], focal_seconds,
                    order_by_source.get(_value(shift['start'], 'event_source_index')), focal_order):
                start = 'unknown'
            zone = _value(shift['start'], 'zone') if shift else None
            start = zone if start == 'faceoff' and zone in STARTS[:3] else 'on_the_fly' if start == 'on_the_fly' else 'unknown'
            age = _age_bin(_value(context['shift_age_seconds'], 'value'))
            name = f'{role}:start_age:{start}:{age}'
            raw[name] = raw.get(name, 0.) + 1 / len(ids)
            person = (game['people'] or {}).get(player, {})
            rest = person.get('calendar_rest', {})
            one, two = _value(rest, 'prior_one_date'), _value(rest, 'prior_two_date')
            rest_level = f'{int(one)}{int(two)}' if one is not None and two is not None else 'unknown'
            name = f'{role}:rest:{rest_level}'
            raw[name] = raw.get(name, 0.) + 1 / len(ids)
        for scope, counters in (('current', CURRENT), ('days_7', DATED), ('days_14', DATED)):
            records = [members[p]['elapsed_prefix'] if scope == 'current' else
                       (game['people'] or {}).get(p, {}).get('workload', {}).get(scope, {}) for p in ids]
            for counter in counters:
                for part, value in zip(WORKLOAD_PARTS, _workload_values(records, counter), strict=True):
                    raw[f'{role}:{scope}:{counter}:{part}'] = value
    exists, short = _value(transition, 'exists'), _value(transition, 'prior_shorthanded_side')
    level = 'none' if exists is False else 'unknown' if exists is None or short is None else (
        'previously_shorthanded' if short == side else 'previously_advantaged')
    raw[f'transition:{level}'] = 1.
    return [raw.get(axis['name'], 0.) for axis in (ST_CONTEXT_AXES if family == 'st' else CONTEXT_AXES)], margin


def _transform_context(time, event, exposure, continuous):
    """transform owned raw matrices in place; absent means become centered zero."""
    time, event = np.asarray(time, dtype=float), np.asarray(event, dtype=float)
    result, event_result = time, event
    moments = []
    total = float(exposure.sum())
    for col, scale_column in enumerate(continuous):
        present = np.isfinite(time[:, col])
        weight = float(exposure[present].sum())
        values = time[present, col]
        anchor = float(values[0]) if weight else 0.
        location = anchor + float(exposure[present] @ (values - anchor) / weight) if weight else 0.
        variance = float(exposure[present] @ ((values - location) ** 2) / weight) if weight else 0.
        scale = float(np.sqrt(variance)) if scale_column and variance > 0 else 1.
        result[:, col] = np.where(present, (time[:, col] - location) / scale, 0.)
        event_result[:, col] = np.where(np.isfinite(event[:, col]), (event[:, col] - location) / scale, 0.)
        moments.append(dict(location=location, scale=scale, available_hours=weight, missing_hours=total - weight))
    return result, event_result, moments


def _physical_5v5(membership):
    return all(len(membership[side + '_skaters']) == 5 and len(membership[side + '_goalies']) == 1
               for side in ('home', 'away'))


def _specialty_state(membership):
    if any(len(membership[side + '_goalies']) != 1 for side in ('home', 'away')):
        return None
    home, away = (len(membership[side + '_skaters']) for side in ('home', 'away'))
    counts = (max(home, away), min(home, away))
    if counts not in ST_ROLE_COUNTS:
        return None
    return ST_STATES[ST_ROLE_COUNTS.index(counts)], 'home' if home > away else 'away'


def _collect_game(game, coach_game, scored, targets, *, family='ev'):
    """consume saved assignments; added target exclusions apply to complete segments."""
    require(family in ('ev', 'st'), 'unknown spatial family')
    axes = ST_CONTEXT_AXES if family == 'st' else CONTEXT_AXES
    eligible = (lambda membership: _specialty_state(membership) is not None) if family == 'st' else _physical_5v5
    game_id = game['game_id']
    support = game['ordinary_attempt_support']
    segments = {row['segment_index']: row for row in game['segments'] or []}
    children = {row['chunk_index']: row for row in game['chunks'] or []}
    events = {row['source']['source_index']: row for row in game['events'] or []}
    event_orders = {index: _value(row.get('chronology'), 'order_index') for index, row in events.items()}
    attempts = {row['source_index']: row for row in game['attempts'] or []}
    saved_segments = {row['segment_index']: row for row in support['segments'] or []}
    require(set(saved_segments) == set(segments), f'{game_id}: saved support segment keys differ')
    base = {index for index, row in saved_segments.items() if row['disposition'] != 'included'}
    added, reasons, kept_events = set(), [], []
    ignored_shorthanded = []
    for ordinal, assigned in enumerate(support['events'] or []):
        index, segment_index = assigned['source_index'], assigned['segment_index']
        if assigned['disposition'] != 'included' or segment_index is None:
            continue
        require(segment_index in segments and assigned['chunk_index'] in children,
                f'{game_id}:{index}: saved source assignment does not resolve')
        segment, chunk = segments[segment_index], children[assigned['chunk_index']]
        require(chunk['segment_index'] == segment_index, f'{game_id}:{index}: source chunk/segment disagree')
        if not eligible(segment['membership']):
            continue
        require(index in attempts and index in events, f'{game_id}:{index}: saved attempt/event join missing')
        attempt, event = attempts[index], events[index]
        state, details = attempt['feature_facts']['state'], attempt['details']
        key = f'{game_id}:{index}'
        side = _value(state, 'home_away')
        if family == 'st':
            _, advantaged = _specialty_state(segment['membership'])
            if side in ('home', 'away') and side != advantaged:
                team = game['game']['identity'][side + '_team_id']
                if _value(details, 'shooting_team_id') == _value(state, 'shooting_team_id') == team:
                    ignored_shorthanded.append(index)
                    continue
        else:
            require(key in scored, f'{key}: execution source key absent')
        score = scored.get(key)
        if score is not None:
            require(score['source_index'] == index and score['game_id'] == game_id,
                    f'{key}: execution source identity differs')
        if family == 'st' and score is not None:
            outcome, shooter = _value(details, 'outcome'), _value(details, 'physical_shooter_id')
            require(score.get('outcome') is None or outcome is None or score['outcome'] == outcome, f'{key}: execution outcome binding differs')
            require(score.get('shooter_id') is None or shooter is None or score['shooter_id'] == str(shooter), f'{key}: execution shooter binding differs')
        problem = []
        if _value(details, 'physical_status') != 'ordinary': problem.append('physical_attempt_unresolved')
        if _value(details, 'outcome') not in ('block', 'miss', 'save', 'goal'): problem.append('outcome_unresolved')
        if side not in ('home', 'away') or family == 'st' and side != advantaged: problem.append('shooting_team_unresolved')
        if side in ('home', 'away'):
            expected_team = game['game']['identity'][side + '_team_id']
            if _value(details, 'shooting_team_id') != expected_team or _value(state, 'shooting_team_id') != expected_team:
                problem.append('shooting_team_unresolved')
            shooter = _value(details, 'physical_shooter_id')
            if shooter is None or shooter not in segment['membership'][side + '_skaters'] + segment['membership'][side + '_goalies']:
                problem.append('shooter_unresolved')
        for source_side in ('home', 'away'):
            for kind in ('skaters', 'goalies'):
                authoritative = _value(state, source_side + '_' + kind)
                if authoritative is None or sorted(authoritative) != sorted(segment['membership'][source_side + '_' + kind]):
                    problem.append('authoritative_membership_inconsistent')
        if score is not None and score['status'] == 'complete':
            if side in ('home', 'away'):
                other = 'away' if side == 'home' else 'home'
                source_members = [_value(state, source_side + '_' + kind)
                                  for kind in ('skaters', 'goalies') for source_side in (side, other)]
                if all(members is not None for members in source_members):
                    require(tuple(score['physical_state']) == tuple(len(members) for members in source_members),
                            f'{key}: execution physical state differs from authoritative event membership')
            require(score['outcome'] == _value(details, 'outcome') and score['shooter_id'] == str(_value(details, 'physical_shooter_id')),
                    f'{key}: execution outcome/shooter join differs')
            expected_state = (*ST_ROLE_COUNTS[ST_STATES.index(_specialty_state(segment['membership'])[0])], 1, 1) if family == 'st' else (5, 5, 1, 1)
            if tuple(score['physical_state']) == expected_state:
                require(key in targets, f'{key}: complete execution event missing from exact physical panel')
            else:
                require(family != 'st', f'{key}: execution physical state differs from assigned advantaged state')
                require(key not in targets, f'{key}: non5v5 execution event appears in physical 5v5 panel')
                problem.append('authoritative_membership_inconsistent')
        else:
            require(key not in targets, f'{key}: unavailable execution event appears in panel')
            problem.append('joint_neutral_value_unavailable')
        if problem:
            added.add(segment_index)
            reasons.append(dict(key=key, segment_index=segment_index, chunk_index=assigned['chunk_index'],
                                reasons=sorted(set(problem)), pointer=f'/ordinary_attempt_support/events/{ordinal}'))
        else:
            kept_events.append((assigned, attempt, event, side, targets[key]))
    excluded = base | added
    time_rows, event_rows = [], []
    for chunk in children.values():
        segment = segments[chunk['segment_index']]
        if segment['segment_index'] in excluded or not eligible(segment['membership']):
            continue
        seconds = chunk['end_seconds'] - chunk['start_seconds']
        require(seconds > 0, f'{game_id}: nonpositive saved elapsed chunk')
        sides = (_specialty_state(segment['membership'])[1],) if family == 'st' else ('home', 'away')
        for side in sides:
            raw, margin = _context(game, segment, chunk, side, coach_game, chunk['score']['values'], chunk['strength_transition'], family=family)
            other = 'away' if side == 'home' else 'home'
            key = dict(game_id=game_id, segment_index=segment['segment_index'], chunk_index=chunk['chunk_index'],
                       source_index=None, attacking_side=side, attacking_players=list(map(str, segment['membership'][side + '_skaters'])),
                       defending_players=list(map(str, segment['membership'][other + '_skaters'])),
                       attacking_team_id=game['game']['identity'][side + '_team_id'],
                       defending_team_id=game['game']['identity'][other + '_team_id'],
                       optional_missing=any(not np.isfinite(value) or value > 0 and (
                           ':unknown' in axis['name'] or axis['name'].endswith('missing_coach'))
                           for axis, value in zip(axes, raw, strict=True)))
            if family == 'st': key['physical_state'] = _specialty_state(segment['membership'])[0]
            time_rows.append((key, seconds / 3600, raw, margin, segment['period_number']))
    for assigned, attempt, event, side, target in kept_events:
        if assigned['segment_index'] in excluded:
            continue
        segment, chunk = segments[assigned['segment_index']], children[assigned['chunk_index']]
        raw, margin = _context(game, segment, chunk, side, coach_game, event['pre_score']['values'],
                               event['context']['strength_transition'], focal_order=event_orders[assigned['source_index']],
                               focal_seconds=event['source']['elapsed_seconds'],
                               order_by_source=event_orders, family=family)
        other = 'away' if side == 'home' else 'home'
        key = dict(game_id=game_id, segment_index=segment['segment_index'], chunk_index=chunk['chunk_index'],
                   source_index=assigned['source_index'], attacking_side=side,
                   attacking_players=list(map(str, segment['membership'][side + '_skaters'])),
                   defending_players=list(map(str, segment['membership'][other + '_skaters'])),
                   attacking_team_id=game['game']['identity'][side + '_team_id'],
                   defending_team_id=game['game']['identity'][other + '_team_id'],
                   inferred_origin=_value(attempt['details'], 'outcome') == 'block',
                   boundary_goal=_value(attempt['details'], 'outcome') == 'goal' and (
                       event['pre_score']['values'] != chunk['score']['values'] or
                       event['source']['elapsed_seconds'] in (segment['start_seconds'], segment['end_seconds'])),
                   optional_missing=any(not np.isfinite(value) or value > 0 and (
                       ':unknown' in axis['name'] or axis['name'].endswith('missing_coach'))
                       for axis, value in zip(axes, raw, strict=True)))
        if family == 'st': key['physical_state'] = _specialty_state(segment['membership'])[0]
        event_rows.append((key, target, raw, margin, segment['period_number']))
    retained = [chunk for chunk in children.values() if chunk['segment_index'] not in excluded
                and eligible(segments[chunk['segment_index']]['membership'])]
    physical = fsum(chunk['end_seconds'] - chunk['start_seconds'] for chunk in retained) / 3600
    physical_keys = {(game_id, chunk['segment_index'], chunk['chunk_index']) for chunk in retained}
    for side in (() if family == 'st' else ('home', 'away')):
        directed = [row for row in time_rows if row[0]['attacking_side'] == side]
        require(len(directed) == len(physical_keys) and
                {(row[0]['game_id'], row[0]['segment_index'], row[0]['chunk_index']) for row in directed} == physical_keys
                and abs(fsum(row[1] for row in directed) - physical) <= 1e-10 * (1 + physical),
                f'{game_id}: {side} directed exposure differs from saved physical chunks')
    if family == 'st':
        require(len(time_rows) == len(physical_keys) and abs(fsum(row[1] for row in time_rows) - physical) <= 1e-10 * (1 + physical),
                f'{game_id}: advantaged exposure differs from saved physical chunks')
    expected_events = {assigned['source_index'] for assigned, *_ in kept_events if assigned['segment_index'] not in excluded}
    require(len(event_rows) == len(expected_events) and {row[0]['source_index'] for row in event_rows} == expected_events,
            f'{game_id}: physical attempts not assigned once to their attacking direction')
    lost = {str(p): 0. for segment in segments.values() for p in
            segment['membership']['home_skaters'] + segment['membership']['away_skaters']}
    player_reasons = {p: set() for p in lost}
    segment_reason_codes = {}
    for segment in segments.values():
        if segment['segment_index'] in excluded and eligible(segment['membership']):
            seconds = segment['end_seconds'] - segment['start_seconds']
            codes = {support['reasons'][i]['code'] for i in saved_segments[segment['segment_index']].get('reason_indices', [])}
            for reason in reasons:
                if reason['segment_index'] == segment['segment_index']:
                    codes.update('value_unavailable' if code == 'joint_neutral_value_unavailable' else
                                 'event_exposure_conflict' if code == 'authoritative_membership_inconsistent' else
                                 'event_evidence_unresolved' for code in reason['reasons'])
            segment_reason_codes[segment['segment_index']] = codes
            for side in ('home', 'away'):
                for p in segment['membership'][side + '_skaters']:
                    lost[str(p)] += seconds
                    player_reasons[str(p)].update(codes)
    lost_events = [row['source_index'] for row in support['events'] or [] if row['segment_index'] in excluded
                   and eligible(segments[row['segment_index']]['membership'])]
    directions = {side: dict(included_hours=fsum(row[1] for row in time_rows if row[0]['attacking_side'] == side) if family == 'st' else physical,
        attempts=sum(row[0]['attacking_side'] == side for row in event_rows),
        origin_mass=fsum(float(row[1]['origin_weights'].sum()) for row in event_rows if row[0]['attacking_side'] == side),
        neutral_chance_mass=fsum(float(row[1]['origin_weights'] @ row[1]['neutral_goal_probability'])
                               for row in event_rows if row[0]['attacking_side'] == side)) for side in ('home', 'away')}
    coverage = dict(game_id=game_id, physical_included_hours=physical,
        directed_included_hours=physical if family == 'st' else 2 * physical, attempts=len(event_rows),
        directions=directions, known_lost_physical_hours=fsum(segment['end_seconds'] - segment['start_seconds']
            for index, segment in segments.items() if index in excluded and eligible(segment['membership'])) / 3600,
        known_lost_event_source_indices=lost_events,
        player_reason_codes={p: sorted(codes) for p, codes in player_reasons.items() if codes},
        base_excluded_segments=sorted(base), added_excluded_segments=sorted(added),
        excluded_segment_union=sorted(excluded), added_reasons=reasons, base_reasons=support['reasons'],
        known_lost_seconds=lost, unquantified_gap=game['game']['ledger']['status'] != 'reconstructed' or
            any(not row['affected_segment_indices'] for row in support['reasons']))

    if family == 'st':
        coverage['ignored_shorthanded_event_source_indices'] = ignored_shorthanded
        coverage['states'] = []
        for state_name, (attacking, defending) in zip(ST_STATES, ST_ROLE_COUNTS, strict=True):
            hours = fsum(row[1] for row in time_rows if row[0]['physical_state'] == state_name)
            selected_events = [row for row in event_rows if row[0]['physical_state'] == state_name]
            coverage['states'].append(dict(state=state_name, included_hours=hours,
                attacking_slot_hours=attacking * hours, defending_slot_hours=defending * hours,
                attempts=len(selected_events), origin_mass=fsum(float(row[1]['origin_weights'].sum()) for row in selected_events),
                neutral_chance_mass=fsum(float(row[1]['origin_weights'] @ row[1]['neutral_goal_probability']) for row in selected_events),
                state_extrapolated=hours == 0))
        coverage['attacking_slot_hours'] = fsum(row['attacking_slot_hours'] for row in coverage['states'])
        coverage['defending_slot_hours'] = fsum(row['defending_slot_hours'] for row in coverage['states'])
        coverage['role_known_lost_seconds'] = {}
        role_reason_codes = {}
        for segment in segments.values():
            state = _specialty_state(segment['membership'])
            if segment['segment_index'] not in excluded or state is None:
                continue
            state_name, attacking_side = state
            for role, side in (('offense', attacking_side), ('defense', 'away' if attacking_side == 'home' else 'home')):
                selector = state_name if role == 'offense' else state_name[::-1]
                for player in segment['membership'][side + '_skaters']:
                    values = coverage['role_known_lost_seconds'].setdefault(str(player), {}).setdefault(role, {})
                    values[selector] = values.get(selector, 0.) + segment['end_seconds'] - segment['start_seconds']
                    role_reason_codes.setdefault(str(player), {}).setdefault(role, {}).setdefault(selector, set()).update(segment_reason_codes[segment['segment_index']])
        coverage['role_reason_codes'] = {player: {role: {selector: sorted(codes) for selector, codes in states.items()}
            for role, states in roles.items()} for player, roles in role_reason_codes.items()}
        known_advantaged, known_shorthanded, ambiguous = [], [], []
        for assigned in support['events'] or []:
            if assigned['segment_index'] not in excluded or assigned['segment_index'] not in segments:
                continue
            state = _specialty_state(segments[assigned['segment_index']]['membership'])
            if state is None:
                continue
            attempt = attempts.get(assigned['source_index'])
            side = _value(attempt['feature_facts']['state'], 'home_away') if attempt else None
            team = game['game']['identity'].get(str(side) + '_team_id')
            known_side = side in ('home', 'away') and _value(attempt['details'], 'shooting_team_id') == _value(attempt['feature_facts']['state'], 'shooting_team_id') == team
            (known_advantaged if known_side and side == state[1] else known_shorthanded if known_side else ambiguous).append(assigned['source_index'])
        coverage['known_lost_advantaged_event_source_indices'] = known_advantaged
        coverage['known_lost_ambiguous_event_source_indices'] = ambiguous
        coverage['ignored_shorthanded_event_source_indices'] = sorted(set(ignored_shorthanded) | set(known_shorthanded))
        coverage['known_lost_event_source_indices'] = sorted(known_advantaged + ambiguous)
    return time_rows, event_rows, coverage


@cache
def _basis():
    basis = build_shape_basis(grid(), np.full(656, 1 / 656))
    return basis.B, dict(sha256=basis.sha256, array_sha256=ordered_array_digest({'basis': basis.B}),
                         reference='uniform-native-656', modes=40)


def _actor_columns(players, coaches, *, family='ev'):
    columns = ([dict(kind='intercept', name=f'intercept:{state}') for state in ST_STATES]
               if family == 'st' else [dict(kind='intercept', name='intercept')])
    for role in ('attacking', 'defending'):
        for actor in players:
            columns.append(dict(kind='actor', name=f'{role}_player:{actor}', block=role + '_player', id=actor, subblock='base'))
        for subblock in (ST_DEFINITION if family == 'st' else DEFINITION)['coach_subblocks']:
            for actor in coaches:
                columns.append(dict(kind='actor', name=f'{role}_coach:{subblock}:{actor}', block=role + '_coach', id=actor, subblock=subblock))
    return columns


def _actor_matrix(rows, columns, coach_games, *, family='ev'):
    axis = {(col['block'], col['id'], col['subblock']): i for i, col in enumerate(columns) if col['kind'] == 'actor'}
    data, indices, indptr = [], [], [0]
    for row in rows:
        key, _, _, margin, period = row
        side = key['attacking_side']
        other = 'away' if side == 'home' else 'home'
        entries = {ST_STATES.index(key['physical_state']) if family == 'st' else 0: 1.}
        for role, source_side, sign in (('attacking', side, 1), ('defending', other, -1)):
            for actor in key[role + '_players']:
                require((role + '_player', actor, 'base') in axis, f'{actor}: physical member missing from skater roster axis')
                entries[axis[role + '_player', actor, 'base']] = 1.
            coach = coach_games[key['game_id']][source_side]['coach_id']
            if coach is not None:
                entries[axis[role + '_coach', coach, 'base']] = 1.
                team_margin = margin * sign if margin is not None else None
                if family == 'ev' and team_margin in range(-2, 3):
                    entries[axis[role + '_coach', coach, f'score:{team_margin}']] = 1.
                if family == 'ev' and period == 3 and team_margin in (0, 1, 2):
                    entries[axis[role + '_coach', coach, 'shell']] = 1.
        for index, value in sorted(entries.items()):
            indices.append(index); data.append(value)
        indptr.append(len(data))
    return csr_matrix((data, indices, indptr), shape=(len(rows), len(columns)), dtype=np.float64)


def prepare_spatial(prepared, coaches, valued, season, *, family='ev'):
    """read each prepared game once and bind the exact accepted execution target."""
    require(family in ('ev', 'st'), 'unknown spatial family')
    axes = ST_CONTEXT_AXES if family == 'st' else CONTEXT_AXES
    recipe = ST_RECIPE if family == 'st' else RECIPE
    started = perf_counter()
    if not isinstance(prepared, PreparedManifest):
        path = Path(prepared)
        purpose = read_json(path / 'manifest.json' if path.is_dir() else path)['purpose']
        prepared = read_prepared(path, purpose)
    purpose = prepared['purpose']
    selected = next((row for row in prepared['seasons'] if row['season'] == season), None)
    require(selected is not None, 'spatial season not selected in preparation')
    coach_path = Path(coaches).resolve()
    coach_data = read_coaches(coach_path, purpose)
    coach_games = {row['game_id']: row for row in coach_data['games'] if row['season'] == season}
    require(set(selected['selected_game_ids']) <= set(coach_games), 'coaches omit selected prepared games')
    coach_ref = dict(purpose=purpose, **identity(coach_path), selected_game_ids=list(selected['selected_game_ids']))
    prepared_ref = dict(purpose=purpose, **identity(prepared.directory / 'manifest.json'),
                        members=[row for row in prepared['files'] if row['season'] == season])
    scores = valued if isinstance(valued, ExecutionScores) else read_execution_scores(valued, purpose, physical_state=(5, 5, 1, 1) if family == 'ev' else (5, 4, 1, 1))
    require(scores.manifest['season'] == season and scores.manifest['purpose'] == purpose,
            'spatial valued season/purpose differs')
    require(scores.manifest['prepared'] == prepared_ref and scores.manifest['coaches'] == coach_ref,
            'spatial preparation/coach bindings differ from execution targets')
    states = [(*counts, 1, 1) for counts in ST_ROLE_COUNTS] if family == 'st' else [(5, 5, 1, 1)]
    targets = {}
    for physical_state in states:
        panel = read_panel(scores, physical_state)
        targets.update((row['key'], row) for row in iter_neutral_origins(panel))
    scored = {row['key']: row for row in scores.events()}
    people = {str(_value(row, 'player_id')): row for row in read_prepared_people(prepared, season)['people']}
    players = tuple(sorted(p for p, row in people.items() if _value(row, 'position_group') != 'G'))
    player_facts = {p: dict(position_group=_value(people[p], 'position_group'), age_days=_value(people[p], 'age_days')) for p in players}
    coach_ids = tuple(sorted(row['coach_id'] for row in read_json(coach_path.parent / 'identities.json')['coaches']))
    actor_columns = _actor_columns(players, coach_ids, family=family)
    time_keys, event_keys, exposure, time_actors, event_actors, raw_time, raw_event = [], [], [], [], [], [], []
    cells, weights, probabilities, offsets, game_coverage, dates = [], [], [], [0], [], []
    input_bytes = 0
    qualification = {p: dict(included_seconds=0., events=0, known_excluded_seconds=0., unquantified_gap=False,
                            reason_counts={}, inferred_inputs=[]) for p in players}
    if family == 'st':
        for support in qualification.values():
            support['roles'] = {role: {selector: dict(included_seconds=0., events=0, known_excluded_seconds=0.,
                unquantified_gap=False, reason_counts={}, inferred_inputs=[]) for selector in ('common', *selectors)}
                for role, selectors in (('offense', ST_STATES), ('defense', tuple(state[::-1] for state in ST_STATES)))}
    for game_id in selected['selected_game_ids']:
        game = read_prepared_game(prepared, season, game_id)
        input_bytes += next(row['bytes'] if 'bytes' in row else (prepared.directory / row['path']).stat().st_size
                            for row in prepared['files'] if row['kind'] == 'game' and row['game_id'] == game_id)
        require(game['game']['identity'] is None or all(game['game']['identity'][field] == coach_games[game_id][field]
                for field in ('home_team_id', 'away_team_id')), f'{game_id}: dated coach team identity differs')
        dates.append(game['game']['inventory']['game_date'])
        times, events, coverage = _collect_game(game, coach_games[game_id], scored, targets, family=family)
        source = next(row for row in prepared['files'] if row['kind'] == 'game' and row['game_id'] == game_id)
        coverage['source'] = dict(path=str(prepared.directory / source['path']), sha256=source['sha256'])
        coverage['possible_gap_player_ids'] = sorted((game['people'] or {}).keys()) if coverage['unquantified_gap'] else []
        game_coverage.append(coverage)
        time_keys.extend(row[0] for row in times); event_keys.extend(row[0] for row in events)
        exposure.extend(row[1] for row in times)
        time_actors.append(_actor_matrix(times, actor_columns, coach_games, family=family))
        event_actors.append(_actor_matrix(events, actor_columns, coach_games, family=family))
        raw_time.append(np.asarray([row[2] for row in times], dtype=np.float64).reshape(-1, len(axes)))
        raw_event.append(np.asarray([row[2] for row in events], dtype=np.float64).reshape(-1, len(axes)))
        for key, hours, *_ in times:
            if family == 'st' or key['attacking_side'] == 'home':
                for p in key['attacking_players'] + key['defending_players']: qualification[p]['included_seconds'] += hours * 3600
        for key, target, *_ in events:
            cells.append(target['cells']); weights.append(target['origin_weights']); probabilities.append(target['neutral_goal_probability'])
            offsets.append(offsets[-1] + len(target['cells']))
            for p in key['attacking_players'] + key['defending_players']:
                qualification[p]['events'] += 1
                if key['inferred_origin']: qualification[p]['inferred_inputs'] = ['blocked_origin']
        for p in players:
            qualification[p]['known_excluded_seconds'] += coverage['known_lost_seconds'].get(p, 0.)
            for code in coverage['player_reason_codes'].get(p, []):
                qualification[p]['reason_counts'][code] = qualification[p]['reason_counts'].get(code, 0) + 1
            # missing whole-game evidence cannot establish who was on ice.
            qualification[p]['unquantified_gap'] |= p in coverage['possible_gap_player_ids']
        if family == 'st':
            for key, hours, *_ in times:
                for role, membership in (('offense', 'attacking_players'), ('defense', 'defending_players')):
                    selector = key['physical_state'] if role == 'offense' else key['physical_state'][::-1]
                    for player in key[membership]:
                        for selected_state in ('common', selector):
                            qualification[player]['roles'][role][selected_state]['included_seconds'] += hours * 3600
            for key, *_ in events:
                for role, membership in (('offense', 'attacking_players'), ('defense', 'defending_players')):
                    selector = key['physical_state'] if role == 'offense' else key['physical_state'][::-1]
                    for player in key[membership]:
                        for selected_state in ('common', selector):
                            support = qualification[player]['roles'][role][selected_state]
                            support['events'] += 1
                            if key['inferred_origin']: support['inferred_inputs'] = ['blocked_origin']
            for player in players:
                for role, selectors in qualification[player]['roles'].items():
                    lost_by_state = coverage['role_known_lost_seconds'].get(player, {}).get(role, {})
                    for selector, support in selectors.items():
                        lost = fsum(lost_by_state.values()) if selector == 'common' else lost_by_state.get(selector, 0.)
                        support['known_excluded_seconds'] += lost
                        support['unquantified_gap'] |= player in coverage['possible_gap_player_ids']
                        if lost:
                            state_codes = coverage['role_reason_codes'].get(player, {}).get(role, {})
                            codes = {code for values in state_codes.values() for code in values} if selector == 'common' else set(state_codes.get(selector, []))
                            for code in codes:
                                support['reason_counts'][code] = support['reason_counts'].get(code, 0) + 1
        del game
    exposure = np.asarray(exposure, dtype=np.float64)
    require((family == 'st' or len(exposure) > 0) and np.all(exposure > 0), 'spatial season has no positive supported elapsed exposure')
    continuous = [axis['continuous'] for axis in axes]
    context_time, context_event = np.vstack(raw_time), np.vstack(raw_event)
    raw_time.clear(); raw_event.clear()
    context_time, context_event, moments = _transform_context(context_time, context_event, exposure, continuous)
    columns = tuple(actor_columns + [dict(kind='context', name=axis['name']) for axis in axes])
    X_time = vstack(time_actors, format='csr')
    X_event = vstack(event_actors, format='csr')
    del time_actors, event_actors
    origin_cells = np.concatenate(cells) if cells else np.empty(0, dtype=np.int64)
    origin_weights = np.concatenate(weights) if weights else np.empty(0, dtype=np.float64)
    q0 = np.concatenate(probabilities) if probabilities else np.empty(0, dtype=np.float64)
    mass = np.bincount(origin_cells, weights=origin_weights, minlength=656)
    neutral = np.bincount(origin_cells, weights=origin_weights * q0, minlength=656)
    attempts, hours = len(event_keys), float(exposure.sum())
    pi_pool = (mass + 1 / 656) / (attempts + 1)
    pi = (mass + 10 * pi_pool) / (attempts + 10)
    pooled_rate = (attempts + 1) / (hours + 1)
    rate = (attempts + pooled_rate) / (hours + 1)
    pooled_quality = (float(neutral.sum()) + .5) / (attempts + 1)
    qmean = (float(neutral.sum()) + 10 * pooled_quality) / (attempts + 10)
    qbar = (neutral + 10 * pi * qmean) / (mass + 10 * pi)
    annual_offsets = dict(r=rate, pi=pi.tolist(), qbar=qbar.tolist())
    state_time = np.asarray([ST_STATES.index(key['physical_state']) for key in time_keys], dtype=np.int64) if family == 'st' else None
    state_event = np.asarray([ST_STATES.index(key['physical_state']) for key in event_keys], dtype=np.int64) if family == 'st' else None
    if family == 'st':
        rates, shares, qualities = [], [], []
        for state_index in range(3):
            selected_events = state_event == state_index
            selected_origins = np.repeat(selected_events, np.diff(offsets))
            state_mass = np.bincount(origin_cells[selected_origins], weights=origin_weights[selected_origins], minlength=656)
            state_neutral = np.bincount(origin_cells[selected_origins], weights=(origin_weights * q0)[selected_origins], minlength=656)
            count = int(selected_events.sum())
            state_hours = float(exposure[state_time == state_index].sum())
            require(state_hours > 0 or count == 0, 'special-teams orphan events have no retained state exposure')
            state_pi = (state_mass + 10 * pi_pool) / (count + 10)
            state_qmean = (float(state_neutral.sum()) + 10 * pooled_quality) / (count + 10)
            rates.append((count + pooled_rate) / (state_hours + 1))
            shares.append(state_pi.tolist())
            qualities.append(((state_neutral + 10 * state_pi * state_qmean) / (state_mass + 10 * state_pi)).tolist())
        annual_offsets = dict(r=rates, pi=shares, qbar=qualities)
    basis, basis_identity = _basis() if family == 'ev' and season == prepared['seasons'][0]['season'] else (None, {})
    transforms = dict(axes=[dict(axis, **moment) for axis, moment in zip(axes, moments, strict=True)])
    definition_hash = hashlib.sha256(json.dumps(dict(recipe=recipe['sha256'], columns=columns, transforms=transforms),
                                                sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    transforms['design_sha256'] = definition_hash
    for player in qualification.values():
        player['reason_counts'] = [dict(code=code, count=count) for code, count in sorted(player['reason_counts'].items())]
        if family == 'st':
            for selectors in player['roles'].values():
                for support in selectors.values():
                    support['reason_counts'] = [dict(code=code, count=count) for code, count in sorted(support['reason_counts'].items())]
    coverage = dict(purpose=purpose, season=season, games=game_coverage, players=qualification,
                    player_reason_count_unit='games with a located excluded segment, once per reason code',
                    physical_included_hours=hours if family == 'st' else hours / 2, directed_included_hours=hours, attempts=attempts,
                    origin_mass=float(origin_weights.sum()), neutral_chance_mass=float(neutral.sum()),
                    supported_players=sum(row['included_seconds'] > 0 or row['events'] > 0 for row in qualification.values()),
                    zero_information_roster_players=sum(row['included_seconds'] == 0 and row['events'] == 0 for row in qualification.values()),
                    optional_missingness={axis['name']: dict(absent_mean_hours=moment['missing_hours'],
                        unknown_fraction_hours=moment['location'] * hours if ':unknown' in axis['name'] or
                        axis['name'].endswith('missing_coach') else None)
                        for axis, moment in zip(axes, moments, strict=True)},
                    unassigned_gap_game_ids=[row['game_id'] for row in game_coverage
                                             if row['unquantified_gap'] and not row['possible_gap_player_ids']])
    if family == 'st':
        coverage['states'] = []
        for state_index, state_name in enumerate(ST_STATES):
            state_rows = [game['states'][state_index] for game in game_coverage]
            coverage['states'].append(dict(state=state_name,
                **{key: fsum(row[key] for row in state_rows) for key in ('included_hours', 'attacking_slot_hours', 'defending_slot_hours', 'origin_mass', 'neutral_chance_mass')},
                attempts=sum(row['attempts'] for row in state_rows),
                state_extrapolated=not any(row['included_hours'] > 0 for row in state_rows)))
        coverage['attacking_slot_hours'] = fsum(row['attacking_slot_hours'] for row in coverage['states'])
        coverage['defending_slot_hours'] = fsum(row['defending_slot_hours'] for row in coverage['states'])
        coverage['ignored_shorthanded_attempts'] = sum(len(row['ignored_shorthanded_event_source_indices']) for row in game_coverage)
    resources = dict(design_wall_seconds=perf_counter() - started, input_read_bytes=input_bytes,
                     time_rows=X_time.shape[0], event_rows=X_event.shape[0], columns=len(columns),
                     actor_columns=X_time.shape[1], context_columns=context_time.shape[1],
                     design_bytes=sum(array.nbytes for array in (X_time.data, X_time.indices, X_time.indptr,
                         X_event.data, X_event.indices, X_event.indptr, context_time, context_event,
                         exposure, origin_cells, origin_weights, q0)))
    design_type = SpecialTeamsDesign if family == 'st' else SpatialDesign
    extra = dict(state_time=state_time, state_event=state_event) if family == 'st' else {}
    return design_type(purpose, season, prepared_ref, coach_ref, dict(identity(scores.path), season=season, purpose=purpose),
        max(dates, default=None), players, player_facts, coach_ids, columns, X_time, X_event, context_time, context_event, exposure,
        tuple(time_keys), tuple(event_keys), np.asarray(offsets, dtype=np.int64), origin_cells, origin_weights, q0,
        transforms, coverage, recipe, resources, basis, basis_identity, annual_offsets, **extra)
