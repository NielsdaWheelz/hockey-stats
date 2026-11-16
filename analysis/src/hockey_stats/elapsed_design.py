"""shared elapsed context, exposure transforms and player/coach encoding."""

from math import fsum

import numpy as np
from scipy.sparse import csr_matrix

from .analysis_context import shift_start_precedes_event
from .artifacts import require
from .execution_history import _value

STARTS = ('offensive', 'neutral', 'defensive', 'on_the_fly', 'unknown')
AGES = ('0:10', '10:20', '20:40', '40:60', '60:90', '90+', 'unknown')
REST = ('00', '01', '10', '11', 'unknown')
TRANSITIONS = ('none', 'previously_advantaged', 'previously_shorthanded', 'unknown')
CURRENT = ('toi_all_seconds', 'toi_5v5_seconds', 'attempts', 'goals', 'shifts_begun', 'shifts_completed')
DATED = ('ice_appearances', 'toi_all_seconds', 'toi_5v5_seconds', 'shifts', 'attempts', 'goals', 'sog')
WORKLOAD_PARTS = ('complete_mean', 'partial_known_mean', 'complete_fraction', 'partial_fraction', 'missing_fraction')
SCORE = tuple(str(i) for i in range(-3, 4)) + ('unknown',)
BANDS = (*range(6), 'OT')
COACH_SUBBLOCKS = ('base', *[f'score:{i}' for i in range(-2, 3)], 'shell')
ST_STATES = ('5v4', '5v3', '4v3')

def workload_values(records, counter):
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


def context_axes(family='ev'):
    axes = []
    def add(name, continuous=False, unit='fraction'):
        axes.append(dict(name=name, continuous=continuous, unit=unit))
    for side in ('home', 'away'):
        for period in ('1', '2', '3', 'OT'):
            add(f'home_period:{side}:{period}')
    for score in SCORE:
        if family == 'st':
            add(f'score:{score}')
        else:
            for band in BANDS:
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


CONTEXT_AXES = context_axes()
ST_CONTEXT_AXES = context_axes('st')


def age_bin(value):
    if value is None:
        return 'unknown'
    return AGES[int(np.searchsorted((10, 20, 40, 60, 90), value, side='right'))]


def elapsed_context(game, segment, chunk, side, coach_game, score, transition, *, focal_order=None, focal_seconds=None, order_by_source=None, family='ev'):
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
            age = age_bin(_value(context['shift_age_seconds'], 'value'))
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
                for part, value in zip(WORKLOAD_PARTS, workload_values(records, counter), strict=True):
                    raw[f'{role}:{scope}:{counter}:{part}'] = value
    exists, short = _value(transition, 'exists'), _value(transition, 'prior_shorthanded_side')
    level = 'none' if exists is False else 'unknown' if exists is None or short is None else (
        'previously_shorthanded' if short == side else 'previously_advantaged')
    raw[f'transition:{level}'] = 1.
    return [raw.get(axis['name'], 0.) for axis in (ST_CONTEXT_AXES if family == 'st' else CONTEXT_AXES)], margin


def transform_context(time, event, exposure, continuous):
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


def actor_columns(players, coaches, *, family='ev'):
    columns = ([dict(kind='intercept', name=f'intercept:{state}') for state in ST_STATES]
               if family == 'st' else [dict(kind='intercept', name='intercept')])
    for role in ('attacking', 'defending'):
        for actor in players:
            columns.append(dict(kind='actor', name=f'{role}_player:{actor}', block=role + '_player', id=actor, subblock='base'))
        for subblock in (('base',) if family == 'st' else COACH_SUBBLOCKS):
            for actor in coaches:
                columns.append(dict(kind='actor', name=f'{role}_coach:{subblock}:{actor}', block=role + '_coach', id=actor, subblock=subblock))
    return columns


def actor_matrix(rows, columns, coach_games, *, family='ev'):
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


