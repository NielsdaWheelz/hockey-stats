"""common-workload value and fixed reported-usage depth arithmetic."""

from collections import defaultdict
from math import exp, fsum, isfinite

from . import analysis_publication as publication
from .artifacts import require
from .descriptive import estimate
from .execution_design import setter_role_weight
from .player_mechanisms import ROLES, STATES, UNITS, unit_shooter_base_logits

TERMS = publication.LEDGER_COMPONENTS
WORKLOAD = dict(five_on_five=1000, power_play=100, penalty_kill=100)
POSITIONS = ('F', 'D')
DEPTH_CUTOFF = dict(F=12, D=6)
FINISHING = 'finishing_goals_per100_attempts'
SETTING = 'setting_goals_per100_assisted_opportunities'
NEUTRAL_ATTEMPTS = 'offense_attempts_per60_neutral'
PENALTY_TERMS = ('penalties_drawn', 'penalties_taken')


def ledger_close(value, expected, terms=()):
    if publication.close(value, expected):
        return True
    if not (isfinite(value) and isfinite(expected)):
        return False
    allowance = 64 * 2**-52 * fsum(abs(term) for term in terms)
    return abs(value - expected) <= 1e-9 + 1e-9 * max(abs(value), abs(expected)) + allowance


def _provided(value):
    require(isfinite(value), 'nonfinite ledger result')
    return estimate(value)


def _copied(value):
    return {**value, 'uncertainty': dict(kind='not_estimated')}


def _uncomputed(row):
    return estimate(None, reason='not_computed', explanation=row['explanation'])


def estimate_from_result(row, field):
    return _copied(row['data'][field]) if row['availability'] == 'provided' else _uncomputed(row)


def sum_estimates(values):
    values = tuple(values)
    missing = next((item for item in values if item['value'] is None), None)
    return _copied(missing) if missing is not None else _provided(fsum(item['value'] for item in values))


def _normalized_logits(roles, logits):
    center = max(logits[role] for role in roles)
    weights = [exp(logits[role] - center) for role in roles]
    total = fsum(weights)
    return [weight / total for weight in weights]


def _slots(unit):
    return ['F'] * unit['forwards'] + ['D'] * unit['defenders']


def slot_constants(unit, logits):
    """return baseline per-slot p and conditional remaining-neutral K by role."""
    roles = _slots(unit)
    full = _normalized_logits(roles, logits)
    constants = {}
    for position in POSITIONS:
        focal = roles.index(position)
        others = [i for i in range(len(roles)) if i != focal]
        normalized = _normalized_logits([roles[i] for i in others], logits)
        contributions = []
        for j, shooter_probability in zip(others, normalized, strict=True):
            weights = [setter_role_weight(roles[j], roles[i]) for i in range(len(roles)) if i != j]
            share = setter_role_weight(roles[j], position) / fsum(weights)
            contributions.append(shooter_probability * share)
        constants[position] = full[focal], fsum(contributions)
    return constants


def state_weights(pp_weights):
    require(set(pp_weights) == set(publication.SPATIAL_STATES)
            and all(isfinite(w) and 0 <= w <= 1 for w in pp_weights.values())
            and ledger_close(fsum(pp_weights.values()), 1., pp_weights.values()), 'invalid ledger pp state mixture')
    return {'5v5': 1., **pp_weights, **{
        pk: pp_weights[pp] for pk, pp in publication.SPATIAL_RECIPROCALS.items()
    }}


def workload_hours(strength, weight):
    minutes = WORKLOAD['five_on_five'] if strength == '5v5' else (
        WORKLOAD['power_play'] if strength in publication.SPATIAL_STATES else WORKLOAD['penalty_kill'])
    return minutes / 60 * weight


def build_state_references(pp_weights, attempts, panels, shootiness_reference, shootiness_problem):
    """compose shared annual constants from checked opportunity, panel and mechanism records."""
    weights = state_weights(pp_weights)
    completed = shootiness_reference is not None and shootiness_reference['kind'] == 'conditional-shooter-choice'
    if completed:
        require(shootiness_problem is None and shootiness_reference['states'] == list(STATES)
                and shootiness_reference['roles'] == list(ROLES)
                and len(shootiness_reference['reference_units']) == len(STATES)
                and len(shootiness_reference['role_offsets']) == len(STATES),
                'shootiness reference roles/states differ')
    else:
        require(shootiness_problem is not None and shootiness_problem['value'] is None
                and (shootiness_reference is None or shootiness_reference['kind'] == 'unavailable'),
                'missing annual shootiness reference requires its upstream unavailability')
    result = []
    for index, (strength, (forwards, defenders)) in enumerate(zip(STATES, UNITS, strict=True)):
        unit = dict(forwards=forwards, defenders=defenders)
        logits = None
        if completed:
            require(shootiness_reference['reference_units'][index] == dict(strength=strength, **unit),
                    'shootiness saved reference unit differs')
            offsets = shootiness_reference['role_offsets'][index]
            require(len(offsets) == len(ROLES) and all(isfinite(value) for value in offsets),
                    'invalid shootiness role offsets')
            raw = [fsum((base, offset)) for base, offset in
                   zip(unit_shooter_base_logits(forwards, defenders), offsets[:2], strict=True)]
            logits = {role: fsum((value, -max(raw))) for role, value in zip(POSITIONS, raw, strict=True)}
            constants = slot_constants(unit, logits)
            setting_K = {role: _provided(constants[role][1]) for role in POSITIONS}
        else:
            setting_K = {role: _copied(shootiness_problem) for role in POSITIONS}
        weight = weights[strength]
        rate, attempt_reference = attempts[strength]
        result.append(dict(strength=strength, hours=workload_hours(strength, weight), mixture_weight=weight,
            attempts_per_hour=_copied(rate), attempt_reference=attempt_reference, unit=unit,
            neutral_slot_logits=logits, setting_K=setting_K,
            shootiness_reference_id=None if shootiness_reference is None else shootiness_reference['sha256'],
            execution_panel=panels[strength]))
    return result


def execution_panel(row):
    """project the shared, non-focal portion of a provided execution panel."""
    if row['availability'] != 'provided':
        return None
    return {key: row['data']['reference_panel'][key] for key in ('panel_id', 'opportunities', 'setup_weight')}


def compose_player_value(spatial, execution, shootiness, penalties, territory, state_references):
    """return the component estimates and their seven-state construction evidence."""
    roles = {row['data']['evidence']['position_group'] for row in shootiness.values()
             if row['availability'] == 'provided'}
    require(len(roles) <= 1, 'provided shootiness rows disagree on annual unit role')
    unit_position = next(iter(roles), 'unknown')
    require(unit_position in ROLES, 'invalid annual shootiness unit role')
    weights = {row['strength']: row['mixture_weight'] for row in state_references}
    for row, strengths in (('pp', publication.SPATIAL_STATES), ('pk', tuple(publication.SPATIAL_RECIPROCALS))):
        if spatial[row]['availability'] == 'provided':
            saved = {item['strength']: item['weight'] for item in spatial[row]['data']['state_weights']}
            require(set(saved) == set(strengths) and all(ledger_close(saved[s], weights[s]) for s in strengths),
                    f'{row} ledger mixture differs from spatial')
    states = []
    for ref in state_references:
        strength = ref['strength']
        execution_row, shooter = execution[strength], shootiness[strength]
        p, finish, setting = estimate_from_result(shooter, 'probability'), estimate_from_result(execution_row, FINISHING), estimate_from_result(execution_row, SETTING)
        panel = ref['execution_panel']
        # A missing focal result can coexist with an annual panel supplied by another player.
        if execution_row['availability'] == 'provided':
            saved = execution_panel(execution_row)
            require(panel is not None and panel['panel_id'] == saved['panel_id']
                    and panel['opportunities'] == saved['opportunities']
                    and ledger_close(panel['setup_weight'],saved['setup_weight'],(saved['setup_weight'],)),
                    'ledger execution panel differs from focal row')
        if shooter['availability'] == 'provided':
            evidence = shooter['data']['evidence']
            require(evidence['reference_unit'] == ref['unit'] and evidence['reference_id'] == ref['shootiness_reference_id'],
                    'ledger shootiness unit or reference differs from focal row')
            p0 = shooter['data']['neutral_probability']['value']
            logits = ref['neutral_slot_logits']
            require((p0 is not None) == (logits is not None and unit_position in POSITIONS),
                    'ledger baseline shooter probability availability differs')
            if p0 is not None:
                slots = _slots(ref['unit'])
                calculated = _normalized_logits(slots, logits)[slots.index(unit_position)]
                require(ledger_close(p0, calculated), 'ledger baseline shooter probability differs')
        k = ref['setting_K'].get(unit_position, p)
        setter_share = next((item for item in (p, k) if item['value'] is None), None)
        if setter_share is None:
            require(unit_position in POSITIONS and 0 <= p['value'] <= 1 and 0 <= k['value'] <= 1,
                    'invalid ledger shooter or setter probability')
            setter_share = _provided(.8 * fsum((1., -p['value'])) * k['value'])
        hours = ref['hours']
        rate = ref['attempts_per_hour']
        contributions = []
        for skill, share in ((finish, p), (setting, setter_share)):
            if hours == 0:
                value = _provided(0.)
            else:
                missing = next((item for item in (rate, share, skill) if item['value'] is None), None)
                if missing is not None:
                    value = _copied(missing)
                else:
                    require(panel is not None and panel['opportunities'] > 0 and rate['value'] >= 0,
                            'defined ledger execution skill lacks its common panel or opportunity rate')
                    value = _provided(hours * rate['value'] * share['value'] * skill['value'] / 100)
            contributions.append(value)
        states.append(dict(strength=strength, use='active' if hours > 0 else 'omitted_zero_weight',
            shooter_probability=p, setter_share=_copied(setter_share), finishing_per100=finish, setting_per100=setting,
            finishing_goals=contributions[0], setting_goals=contributions[1]))

    league = {}
    for term, row, field, multiplier in (
        ('five_on_five_offense', spatial['5v5'], 'offense_xg_per60', WORKLOAD['five_on_five'] / 60),
        ('five_on_five_defense', spatial['5v5'], 'defense_xg_per60', -WORKLOAD['five_on_five'] / 60),
        ('power_play_offense', spatial['pp'], 'offense_xg_per60', WORKLOAD['power_play'] / 60),
        ('penalty_kill_defense', spatial['pk'], 'defense_xg_per60', -WORKLOAD['penalty_kill'] / 60),
        ('penalties_drawn', penalties, 'drawn_value_per60', WORKLOAD['five_on_five'] / 60),
        ('penalties_taken', penalties, 'taken_value_per60', WORKLOAD['five_on_five'] / 60),
        ('ice_won', territory, 'ice_won_goals_per_basket', 1),
        ('ice_lost', territory, 'ice_lost_goals_per_basket', -1),
    ):
        datum = estimate_from_result(row, field)
        league[term] = datum if datum['value'] is None else _provided(multiplier * datum['value'])
    for skill in ('finishing', 'setting'):
        league[skill] = sum_estimates(row[skill + '_goals'] for row in states)
    return dict(league={term: league[term] for term in TERMS}, execution_states=states, unit_position=unit_position)


def build_depth_groups(usage):
    """rank positive-time members of complete groups and freeze per-player weights."""
    groups = []
    by_position = {position: defaultdict(list) for position in POSITIONS}
    keys = set()
    for source in sorted(usage['groups'], key=lambda group: (group['team_id'], group['position'])):
        team, position = source['team_id'], source['position']
        key = team, position
        require(key not in keys and position in by_position, 'duplicate or invalid depth team-position group')
        keys.add(key)
        members = sorted(source['members'], key=lambda member: member['player_id'])
        require(len({member['player_id'] for member in members}) == len(members), 'duplicate depth rank candidate')
        cutoff = None
        ranks = {}
        if source['status'] == 'complete':
            ordered = sorted(members, key=lambda member: -member['known_team_seconds'])
            limit = DEPTH_CUTOFF[position]
            if len(ordered) >= limit:
                cutoff = ordered[limit - 1]['known_team_seconds']
            prior = None
            for index, member in enumerate(ordered, 1):
                player, seconds = member['player_id'], member['known_team_seconds']
                require(type(seconds) is int and seconds > 0 and member['complete']
                        and usage['positions'].get(player, {}).get('group') == position,
                        'complete team-position rank lacks resolved annual positive usage')
                if seconds != prior:
                    rank = index
                    prior = seconds
                ranks[player] = rank
                if rank > limit:
                    by_position[position][player].append(dict(team_id=team, seconds=seconds))
        else:
            require(source['status'] == 'excluded', 'invalid depth team-position status')
        group_members = []
        for member in members:
            rank = ranks.get(member['player_id'])
            group_members.append(dict(**member, rank=rank, depth=None if rank is None else rank > DEPTH_CUTOFF[position]))
        groups.append(dict(**source, cutoff_seconds=cutoff) | dict(members=group_members))
    fixed_members = {position: [
        dict(player_id=player, seconds=sum(team['seconds'] for team in teams), teams=teams)
        for player, teams in sorted(by_position[position].items())
    ] for position in POSITIONS}
    return groups, fixed_members


def compose_depth_reference(fixed_members, league_vectors):
    """use one normalized vector weight per annual player, or withhold the full reference."""
    total = sum(member['seconds'] for member in fixed_members)
    missing = []
    for member in fixed_members:
        player = member['player_id']
        require(type(member['seconds']) is int and member['seconds'] > 0 and player in league_vectors,
                'positive-weight depth member lacks a published league vector')
        vector = league_vectors[player]
        terms = [term for term in TERMS if vector[term]['value'] is None]
        if terms:
            missing.append(dict(player_id=player, terms=terms))
    available = total > 0 and not missing
    components = None
    if available:
        weights = [(league_vectors[member['player_id']], member['seconds'] / total) for member in fixed_members]
        components = {term: _provided(fsum(vector[term]['value'] * weight for vector, weight in weights))['value']
                      for term in TERMS}
    return dict(available=available, reason=None if available else 'missing_member_vectors' if missing else 'no_exposure',
                members=fixed_members, total_seconds=total, member_count=len(fixed_members),
                components=components, missing_vectors=missing)


def ledger_values(league, depth_position_group, positions, league_vectors):
    """project component comparisons and complete totals without changing the focal league vector."""
    reference = positions.get(depth_position_group)
    if reference is None:
        unavailable_reference = estimate(None, reason='not_applicable', explanation='no resolved annual depth position')
    elif not reference['available']:
        if reference['missing_vectors']:
            first = reference['missing_vectors'][0]
            unavailable_reference = _copied(league_vectors[first['player_id']][first['terms'][0]])
            detail = unavailable_reference['reason_detail']
            unavailable_reference['reason_detail'] = dict(detail, explanation=
                'the depth reference requires a member value that is unavailable. ' + detail['explanation'])
        else:
            unavailable_reference = estimate(None, reason='no_exposure', explanation='no eligible depth time')
    components = {}
    for term in TERMS:
        focal = league[term]
        if focal['value'] is None:
            replacement = _copied(focal)
        elif reference is None or not reference['available']:
            replacement = _copied(unavailable_reference)
        else:
            replacement = _provided(fsum((focal['value'], -reference['components'][term])))
        components[term] = dict(league_goals=focal, replacement_goals=replacement)
    return dict(components=components, league_total=sum_estimates(league[term] for term in TERMS),
        replacement_total=sum_estimates(components[term]['replacement_goals'] for term in TERMS),
        penalties_combined={key: sum_estimates(components[term][key] for term in PENALTY_TERMS)
                            for key in ('league_goals', 'replacement_goals')})
