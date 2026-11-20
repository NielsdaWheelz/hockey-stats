"""closed detached ledger evidence, bound to the exact published dependency rows."""

from collections import defaultdict

from . import analysis_publication as publication
from .artifacts import require
from .player_mechanisms import ROLES, STATES, UNITS
from .player_value import (
    FINISHING, NEUTRAL_ATTEMPTS, PENALTY_TERMS, POSITIONS, SETTING, TERMS, WORKLOAD,
    build_depth_groups, compose_depth_reference, compose_player_value, estimate_from_result,
    ledger_close, ledger_values, slot_constants, state_weights, sum_estimates, workload_hours,
)

DEPTH_REASONS = frozenset((
    'schedule_unavailable', 'team_boxscore_unavailable', 'player_enumeration_unresolved',
    'identity_conflict', 'missing_toi', 'position_conflict', 'position_unavailable',
    'annual_position_tie', 'annual_position_incomplete',
))


def ledger_dependencies(spatial, spatial_evidence, execution, shootiness, penalties, territory, methods):
    """copy the finite upstream method and support projections for selected detail."""
    def input_ref(strength, row):
        if row['availability'] != 'provided':
            return dict(strength=strength, availability='not_computed', explanation=row['explanation'],
                        method_id=None, reference_id=None, support_policy_id=None)
        method = methods[row['data']['method_id']]
        return dict(strength=strength, availability='provided', explanation=None, method_id=method['method_id'],
                    reference_id=method['reference_id'], support_policy_id=method['support_policy_id'])

    spatial_strengths = publication.SPATIAL_STRENGTHS
    inputs = dict(spatial=[input_ref(s, spatial[s]) for s in spatial_strengths],
                  execution=[input_ref(s, execution[s]) for s in STATES],
                  shootiness=[input_ref(s, shootiness[s]) for s in STATES],
                  penalties=input_ref(None, penalties), territory=input_ref(None, territory))
    supports = dict(spatial=[], execution=[], shootiness=[], penalties=None, territory=None)
    for strength in spatial_strengths:
        row, evidence = spatial[strength]['data'], spatial_evidence[strength]['data']
        require((row is None) == (evidence is None), 'ledger spatial support lacks its matching scalar')
        roles = None if evidence is None else [dict(role=role['role'], coefficient_support=role['coefficient_support'])
                                                for role in evidence['roles']]
        supports['spatial'].append(dict(strength=strength, support=None if row is None else row['support'], roles=roles))
    for strength in STATES:
        row = execution[strength]['data']
        supports['execution'].append(dict(strength=strength,
            finishing=None if row is None else row['support'][FINISHING],
            setting=None if row is None else row['support'][SETTING],
            coefficient_support=None if row is None else row['coefficient_support'],
            panel_id=None if row is None else row['reference_panel']['panel_id']))
        row = shootiness[strength]['data']
        supports['shootiness'].append(dict(strength=strength, support=None if row is None else row['support'],
            coefficient_support=None if row is None else row['evidence']['coefficient_support']))
    if penalties['data'] is not None:
        supports['penalties'] = dict(support=penalties['data']['support'],
            coefficient_support=penalties['data']['evidence']['coefficient_support'])
    if territory['data'] is not None:
        supports['territory'] = dict(support=territory['data']['support'], roles=territory['data']['evidence']['roles'])
    return inputs, supports


def _binding(value):
    publication.fields(value, ('uri', 'sha256'))
    publication.text(value['uri'])
    publication.digest(value['sha256'])


def _estimate_shape(value, catalogs, *, probability=False, nonnegative=False):
    publication.estimate(value, catalogs, probability=probability, nonnegative=nonnegative)
    require(value['uncertainty']['kind'] == 'not_estimated', 'ledger does not estimate uncertainty')


def _array_axis(rows, key, axis):
    require(type(rows) is list and all(type(row) is dict and key in row for row in rows)
            and tuple(row[key] for row in rows) == tuple(axis), f'ledger {key} axis differs')


def _check_estimate(actual, expected, terms=()):
    value = actual['value']
    target = expected['value']
    require((value is None) == (target is None), 'ledger availability differs from its prerequisites')
    require({k: v for k, v in actual.items() if k != 'value'} == {k: v for k, v in expected.items() if k != 'value'},
            'ledger estimate reason or uncertainty differs from its prerequisites')
    require(value is None or ledger_close(value, target, terms or (target,)), 'ledger estimate differs from its accounting')


def _validate_state_references(value, catalogs):
    rows, inputs = value['state_references'], value['inputs']
    _array_axis(rows, 'strength', STATES)
    by_strength = {row['strength']: row for row in rows}
    weights = state_weights({state: by_strength[state]['mixture_weight'] for state in publication.SPATIAL_STATES})
    for row, (forwards, defenders) in zip(rows, UNITS, strict=True):
        strength = row['strength']
        publication.fields(row, ('strength','hours','mixture_weight','attempts_per_hour','attempt_reference','unit',
                                  'neutral_slot_logits','setting_K','shootiness_reference_id','execution_panel'))
        for key in ('hours', 'mixture_weight'):
            publication.number(row[key],minimum=0,maximum=WORKLOAD['five_on_five']/60 if key=='hours' else 1)
        expected_hours = workload_hours(strength, weights[strength])
        require(ledger_close(row['mixture_weight'], weights[strength], (weights[strength],))
                and (row['hours'] == 0) == (expected_hours == 0)
                and ledger_close(row['hours'], expected_hours, (expected_hours,)), 'ledger workload/reciprocal mixture differs')
        unit = row['unit']
        publication.fields(unit, ('forwards','defenders'))
        require(type(unit['forwards']) is int and type(unit['defenders']) is int
                and unit == dict(forwards=forwards, defenders=defenders), 'invalid ledger common slot unit')
        _estimate_shape(row['attempts_per_hour'], catalogs, nonnegative=True)
        attempt = row['attempt_reference']
        if strength == '5v5' or strength in publication.SPATIAL_STATES:
            publication.fields(attempt, ('kind','strength','method_id','quantity'))
            require(attempt['kind'] == 'spatial' and attempt['quantity'] == NEUTRAL_ATTEMPTS
                    and (attempt['method_id'] is None or attempt['method_id'] in catalogs['method']),
                    'invalid ledger spatial attempt reference')
        else:
            publication.fields(attempt, ('kind','strength','reduction','attempts','included_seconds','neutral_goal_mass',
                                         'known_excluded_seconds','unquantified_gap'))
            require(attempt['kind'] == 'source_pool' and type(attempt['unquantified_gap']) is bool,
                    'invalid ledger shorthanded opportunity reference')
            _binding(attempt['reduction'])
            for key in ('attempts','included_seconds','known_excluded_seconds','neutral_goal_mass'):
                publication.number(attempt[key],minimum=0,integer=key=='attempts')
            require(attempt['neutral_goal_mass'] <= attempt['attempts'], 'shorthanded neutral mass exceeds attempts')
            rate = row['attempts_per_hour']['value']
            seconds = attempt['included_seconds']
            if seconds > 0:
                expected_rate = 3600 * attempt['attempts'] / seconds
                require(rate is not None and ledger_close(rate, expected_rate, (expected_rate,)),
                        'ledger shorthanded rate differs from count/time')
            else:
                require(rate is None and attempt['attempts'] == 0
                        and row['attempts_per_hour']['unavailable_reason'] in ('no_exposure','missing_source'),
                        'ledger shorthanded rate lacks matched time')
            require(strength == '4v5' or attempt['reduction'] == inputs['shorthanded_reduction'],
                    'ledger shorthanded rate uses a different reduction')
        require(attempt['strength'] == strength, 'ledger attempt reference strength differs')
        panel = row['execution_panel']
        if panel is not None:
            publication.fields(panel, ('panel_id','opportunities','setup_weight'))
            publication.text(panel['panel_id'])
            publication.number(panel['opportunities'],minimum=0,integer=True)
            publication.number(panel['setup_weight'],minimum=0)
            require(ledger_close(panel['setup_weight'], .8 * panel['opportunities'], (.8 * panel['opportunities'],)),
                    'ledger mirrored setup mass differs')
        logits = row['neutral_slot_logits']
        reference_id = row['shootiness_reference_id']
        if reference_id is not None:
            publication.digest(reference_id)
        if logits is not None:
            publication.fields(logits, POSITIONS)
            for logit in logits.values():
                publication.number(logit)
            require(max(logits.values()) == 0 and reference_id is not None,
                    'neutral slot logits lack their centered shootiness reference')
        constants = None if logits is None else slot_constants(unit, logits)
        publication.fields(row['setting_K'], POSITIONS)
        for position, scalar in row['setting_K'].items():
            _estimate_shape(scalar, catalogs, probability=True)
            k = scalar['value']
            require((k is not None) == (constants is not None), 'ledger K availability differs from slot logits')
            if k is not None:
                require(ledger_close(k, constants[position][1], (constants[position][1],)),
                        'ledger K differs from neutral remaining-slot allocation')
    require(len({row['shootiness_reference_id'] for row in rows}) == 1
            and len({row['neutral_slot_logits'] is None for row in rows}) == 1,
            'ledger shootiness reference availability differs across strengths')
    if rows[0]['neutral_slot_logits'] is None:
        problem = rows[0]['setting_K']['F']
        require(all(row['setting_K'][role] == problem for row in rows for role in POSITIONS)
                and (problem['unavailable_reason'] == 'not_computed' if rows[0]['shootiness_reference_id'] is None
                     else problem['unavailable_reason'] in ('failed_fit','no_exposure')),
                'ledger unavailable setter coefficients lack one annual source reason')


def _validate_depth_shapes(value):
    groups, positions = value['groups'], value['positions']
    require(type(groups) is list, 'invalid ledger depth group list')
    keys = []
    for group in groups:
        publication.fields(group, ('team_id','position','status','reasons','inventory_games','supported_games',
            'known_seconds','missing_time_records','unquantified_gap','affected_games','affected_players','cutoff_seconds','members'))
        publication.identifier(group['team_id'])
        require(group['position'] in POSITIONS and group['status'] in ('complete','excluded'), 'invalid depth team group')
        keys.append((group['team_id'], group['position']))
        publication.strings(group['reasons'],ordered=True)
        require(set(group['reasons']) <= DEPTH_REASONS, 'invalid depth exclusion reason')
        for key in ('inventory_games','supported_games','known_seconds','missing_time_records'):
            publication.number(group[key],minimum=0,integer=True)
        require(type(group['unquantified_gap']) is bool and group['supported_games'] <= group['inventory_games'],
                'invalid depth completeness counts')
        for field in ('affected_games','affected_players'):
            publication.strings(group[field],ordered=True)
        for game in group['affected_games']:
            publication.game_id(game,value['season'])
        for player in group['affected_players']:
            publication.identifier(player)
        complete = group['status'] == 'complete'
        require(complete == (not group['reasons']) and (not complete or (not group['missing_time_records']
                and not group['unquantified_gap'] and group['supported_games'] == group['inventory_games'])),
                'depth group status differs from completeness')
        publication.number(group['cutoff_seconds'],minimum=1,integer=True,nullable=True)
        require(complete or group['cutoff_seconds'] is None, 'excluded depth group applies cutoff')
        require(type(group['members']) is list, 'invalid depth group members')
        member_keys = []
        for member in group['members']:
            publication.fields(member, ('player_id','known_team_seconds','complete','rank','depth'))
            publication.identifier(member['player_id'])
            member_keys.append(member['player_id'])
            publication.number(member['known_team_seconds'],minimum=1 if complete else 0,integer=True)
            publication.number(member['rank'],minimum=1,integer=True,nullable=not complete)
            require(type(member['complete']) is bool and (member['complete'] and type(member['depth']) is bool if complete
                    else member['rank'] is None and member['depth'] is None), 'invalid ranked depth member')
        require(member_keys == sorted(set(member_keys)), 'duplicate/unordered depth group members')
        if complete:
            require(group['known_seconds'] == sum(m['known_team_seconds'] for m in group['members']),
                    'complete depth group known time differs from member time')
    require(keys == sorted(set(keys)), 'duplicate/unordered ledger depth group matrix')
    require(set(keys) == {(team,role) for team,_ in keys for role in POSITIONS},
            'depth team lacks both position groups')
    publication.fields(positions, POSITIONS)
    for position in positions.values():
        publication.fields(position, ('available','reason','members','total_seconds','member_count','components','missing_vectors'))
        require(type(position['available']) is bool and type(position['members']) is list
                and type(position['missing_vectors']) is list, 'invalid depth reference availability/members')
        for key in ('total_seconds','member_count'):
            publication.number(position[key],minimum=0,integer=True)
        for member in position['members']:
            publication.fields(member, ('player_id','seconds','teams'))
            publication.identifier(member['player_id'])
            publication.number(member['seconds'],minimum=1,integer=True)
            require(type(member['teams']) is list and member['teams'], 'missing depth member team weights')
            for team in member['teams']:
                publication.fields(team, ('team_id','seconds'))
                publication.identifier(team['team_id'])
                publication.number(team['seconds'],minimum=1,integer=True)
        for row in position['missing_vectors']:
            publication.fields(row, ('player_id','terms'))
            publication.identifier(row['player_id'])
            require(type(row['terms']) is list and row['terms']
                    and row['terms'] == [term for term in TERMS if term in row['terms']], 'invalid depth missing-vector terms')
        if position['available']:
            require(position['reason'] is None and position['total_seconds'] > 0 and not position['missing_vectors'],
                    'invalid available depth reference')
            publication.fields(position['components'], TERMS)
            for component in position['components'].values():
                publication.number(component)
        else:
            require(position['components'] is None and position['reason'] == (
                'no_exposure' if position['total_seconds'] == 0 else 'missing_member_vectors'),
                'invalid unavailable depth reference')


def validate_ledger_payload(table, value, row, catalogs):
    """validate closed ledger envelopes before doing annual detached joins."""
    if table == 'ledger_reference':
        publication.fields(value, ('season','method_id','reference_id','inputs','state_references','groups','positions'))
        require(value['season'] == row['season'], 'ledger annual reference season differs')
        publication.digest(value['reference_id'])
        publication._method(value['method_id'], catalogs)
        method = catalogs['method'][value['method_id']]
        bindings = dict(prepared='prepared', source_results='source_results', usage_reduction='derivation',
                        shorthanded_reduction='derivation', shootiness_state='annual_state')
        publication.fields(value['inputs'], bindings)
        method_inputs = {(item['role'], item['sha256']) for item in method['inputs'] if row['season'] in item['seasons']}
        for key, role in bindings.items():
            binding = value['inputs'][key]
            _binding(binding)
            require(binding in method['evidence'] and (role, binding['sha256']) in method_inputs,
                    f'ledger method lacks its selected {key} binding')
        require(method['family'] == 'ledger' and ('derivation', value['reference_id']) in method_inputs
                and any(item['sha256'] == value['reference_id'] for item in method['evidence']),
                'ledger method lacks annual numerical reference')
        _validate_state_references(value, catalogs)
        _validate_depth_shapes(value)
        require(value['reference_id'] == publication.reference_digest({k: v for k, v in value.items() if k != 'reference_id'}),
                'ledger annual numerical reference digest differs')
        return

    publication.fields(value, ('reference_minutes','components','league_total','replacement_total','penalties_combined','method_id','evidence'))
    require(value['reference_minutes'] == WORKLOAD, 'wrong ledger reference workload')
    publication.fields(value['components'], TERMS)
    publication._method(value['method_id'], catalogs)
    require(catalogs['method'][value['method_id']]['family'] == 'ledger', 'ledger payload method family differs')
    for item in (*value['components'].values(), value['penalties_combined']):
        publication.fields(item, ('league_goals','replacement_goals'))
        for scalar in item.values():
            _estimate_shape(scalar,catalogs)
    for key in ('league_total','replacement_total'):
        _estimate_shape(value[key],catalogs)
    evidence = value['evidence']
    publication.fields(evidence, ('annual_reference_id','depth_position','unit_position','inputs','execution_states','dependency_support'))
    publication.digest(evidence['annual_reference_id'])
    require(evidence['unit_position'] in ROLES, 'invalid ledger shootiness unit position')
    depth = evidence['depth_position']
    fields = ('forward_seconds','defense_seconds','unknown_seconds','missing_time_records')
    publication.fields(depth, ('group','mixed',*fields))
    require(depth['group'] in ROLES and type(depth['mixed']) is bool, 'invalid annual depth position')
    for field in fields:
        publication.number(depth[field],minimum=0,integer=True)
    forward, defense = depth['forward_seconds'], depth['defense_seconds']
    require(not (forward > 0 and defense > 0) or depth['mixed'], 'depth position omits mixed-role usage')
    if depth['group'] != 'unknown':
        own, other = (forward,defense) if depth['group'] == 'F' else (defense,forward)
        require(depth['unknown_seconds'] == 0 and (own > 0 or depth['missing_time_records'] > 0)
                and (not depth['mixed'] and other == 0 or depth['mixed'] and own > other
                     and depth['missing_time_records'] == 0), 'recorded depth time disagrees with annual position')
    _array_axis(evidence['execution_states'],'strength',STATES)
    for state in evidence['execution_states']:
        fields = ('shooter_probability','setter_share','finishing_per100','setting_per100','finishing_goals','setting_goals')
        publication.fields(state, ('strength','use',*fields))
        require(state['use'] in ('active','omitted_zero_weight'), 'invalid ledger reference state use')
        for field in fields:
            _estimate_shape(state[field],catalogs,probability=field in ('shooter_probability','setter_share'))


def _compare_reference(actual, expected, league_vectors):
    require({k:v for k,v in actual.items() if k!='components'} == {k:v for k,v in expected.items() if k!='components'},
            'ledger depth members or availability differ from fixed team ranks')
    if expected['available']:
        for term in TERMS:
            contributions = [league_vectors[member['player_id']][term]['value'] * (member['seconds'] / expected['total_seconds'])
                             for member in expected['members']]
            require(ledger_close(actual['components'][term], expected['components'][term], contributions),
                    'ledger depth mean differs from common weights')


def _compare_player(actual, construction, positions, position, league_vectors):
    components = actual['components']
    execution_states = actual['evidence']['execution_states']
    league = {term: components[term]['league_goals'] for term in TERMS}
    for term in TERMS:
        expected = construction['league'][term]
        terms = ()
        if term in ('finishing','setting'):
            addends = [state[term+'_goals'] for state in execution_states]
            expected = sum_estimates(addends)
            if expected['value'] is not None:
                terms = [item['value'] for item in addends]
        _check_estimate(league[term], expected, terms)
    replacement = ledger_values(league,position,positions,league_vectors)['components']
    for term in TERMS:
        wanted = replacement[term]['replacement_goals']
        terms = (league[term]['value'], -positions[position]['components'][term]) if wanted['value'] is not None else ()
        _check_estimate(components[term]['replacement_goals'], wanted, terms)
    for kind in ('league','replacement'):
        key = kind + '_goals'
        for actual_estimate, terms in (
            (actual[kind+'_total'],TERMS),
            (actual['penalties_combined'][key],PENALTY_TERMS),
        ):
            addends = [components[term][key] for term in terms]
            expected = sum_estimates(addends)
            _check_estimate(actual_estimate,expected,
                            [item['value'] for item in addends] if expected['value'] is not None else ())


def validate_ledger_year(reference, players, source_rows, catalogs, team_inventory=None):
    """reconcile annual ledger rows to each same-player key, then check fixed reference and totals."""
    if reference['availability'] != 'provided':
        require(all(row['availability'] != 'provided' for row in players.values()),
                'provided ledger lacks its annual reference')
        return
    annual = reference['data']
    groups, states = annual['groups'], annual['state_references']
    method = catalogs['method'][annual['method_id']]
    score_inputs = [item for item in method['inputs'] if item['role'] == 'execution_score']
    require(len(score_inputs) <= 1, 'ledger has duplicate selected score bindings')
    selected_score = None
    if score_inputs:
        selected = score_inputs[0]
        selected_score = selected['sha256']
        require(selected['seasons'] == [annual['season']]
                and any(receipt['sha256'] == selected_score for receipt in method['evidence']),
                'ledger selected score lacks a same-year method receipt')
    weights = {item['strength']:item['mixture_weight'] for item in states}
    slot_baselines = {item['strength']:slot_constants(item['unit'],item['neutral_slot_logits'])
                      for item in states if item['neutral_slot_logits'] is not None}
    if team_inventory is not None:
        require({(group['team_id'],group['position']) for group in groups}
                == {(team,position) for team in team_inventory for position in POSITIONS},
                'ledger team-position matrix differs from season game inventory')
        for group in groups:
            games = team_inventory[group['team_id']]
            require(group['inventory_games'] == len(games) and set(group['affected_games']) <= set(games),
                    'ledger group game coverage differs from season game inventory')

    league_vectors, positions, constructions = {}, {}, {}
    group_seconds = defaultdict(int)
    for group in groups:
        if group['status'] == 'complete':
            for member in group['members']:
                group_seconds[member['player_id']] += member['known_team_seconds']
    for shared in states:
        attempt = shared['attempt_reference']
        if attempt['kind'] != 'spatial':
            continue
        strength = shared['strength']
        spatial_rows = source_rows['skater_spatial']
        supplied = [spatial_rows[player,strength] for player in players
                    if spatial_rows[player,strength]['availability'] == 'provided']
        donors = supplied or [spatial_rows[min(players),strength]]
        for donor in donors:
            require(attempt['method_id'] == (donor['data']['method_id'] if supplied else None),
                    'ledger neutral attempt reference differs from exact spatial method')
            _check_estimate(shared['attempts_per_hour'], estimate_from_result(donor, NEUTRAL_ATTEMPTS))
    supplied_panel, upstream_methods = set(), set()
    supplied_minor, supplied_shootiness = False, False
    for player, ledger in players.items():
        spatial = {s: source_rows['skater_spatial'][player,s] for s in publication.SPATIAL_STRENGTHS}
        spatial_evidence = {s: source_rows['spatial_evidence'][player,s] for s in publication.SPATIAL_STRENGTHS}
        execution = {s: source_rows['skater_execution'][player,s] for s in STATES}
        shootiness = {s: source_rows['skater_shootiness'][player,s] for s in STATES}
        penalties = source_rows['skater_penalties'][player]
        territory = source_rows['skater_territory'][player]
        for strength in ('pp','pk'):
            upstream = spatial[strength]
            if upstream['availability'] == 'provided':
                require(all(ledger_close(row['weight'],weights[row['strength']],(weights[row['strength']],))
                            for row in upstream['data']['state_weights']), 'ledger shared spatial mixture differs')
        for shared in states:
            strength = shared['strength']
            if execution[strength]['availability'] == 'provided':
                supplied_panel.add(strength)
                donor = execution[strength]['data']
                panel = donor['reference_panel']
                expected = shared['execution_panel']
                require(expected is not None and panel['panel_id'] == expected['panel_id']
                        and panel['opportunities'] == expected['opportunities']
                        and ledger_close(panel['setup_weight'],expected['setup_weight'],(expected['setup_weight'],)),
                        'ledger execution panel differs from published source')
                if selected_score is not None:
                    require(any(item['sha256'] == selected_score for item in catalogs['method'][donor['method_id']]['evidence']),
                            'ledger selected score differs from execution method')
            if shootiness[strength]['availability'] == 'provided':
                supplied_shootiness = True
                shooter = shootiness[strength]['data']
                status = shooter['evidence']['coefficient_support']['status']
                require(shooter['evidence']['annual_state'] == annual['inputs']['shootiness_state']
                        and (shared['neutral_slot_logits'] is not None) == (status == 'complete')
                        and shared['shootiness_reference_id'] == shooter['evidence']['reference_id'],
                        'ledger shared shooter reference differs from donor annual state')
                role = shooter['evidence']['position_group']
                constants = slot_baselines.get(strength,{})
                expected_p0 = constants.get(role,(None,None))[0]
                p0 = shooter['neutral_probability']['value']
                require((p0 is None) == (expected_p0 is None)
                        and (p0 is None or ledger_close(p0,expected_p0,(expected_p0,))),
                        'ledger neutral shooter probability differs from its shared unit')
                if status != 'complete':
                    expected_reason = 'failed_fit' if status == 'failed' else 'no_exposure'
                    require(shared['setting_K']['F']['unavailable_reason'] == expected_reason,
                            'ledger unavailable setter coefficients differ from the upstream solver status')
            attempt = shared['attempt_reference']
            if strength == '4v5' and penalties['availability'] == 'provided':
                supplied_minor = True
                valuation = penalties['data']['evidence']['valuation']
                require(attempt['reduction'] == valuation['inputs']['reduction'],
                        'ledger 4v5 reference does not reuse the saved minor reduction')
                if selected_score is not None:
                    require(valuation['inputs']['execution_score']['sha256'] == selected_score,
                            'ledger selected score differs from 4v5 minor source')
                for key, scalar in valuation['sh_support'].items():
                    require(ledger_close(attempt[key],scalar,(scalar,)) if type(scalar) is float else attempt[key] == scalar,
                            'ledger 4v5 support differs from saved minor reference')
        if ledger['availability'] != 'provided':
            continue
        data = ledger['data']
        evidence = data['evidence']
        require(data['method_id'] == annual['method_id'] and evidence['annual_reference_id'] == annual['reference_id'],
                'ledger row refers to a different annual reference or method')
        depth = evidence['depth_position']
        positions[player] = depth
        require(group_seconds[player] <= depth['forward_seconds'] + depth['defense_seconds'],
                'complete depth group time exceeds player annual reported seconds')
        dependencies, supports = ledger_dependencies(spatial,spatial_evidence,execution,shootiness,penalties,territory,catalogs['method'])
        require(dependencies == evidence['inputs'] and supports == evidence['dependency_support'],
                'ledger does not copy exact keyed upstream method/support evidence')
        for method_rows in (dependencies['spatial'], dependencies['execution'], dependencies['shootiness'],
                            (dependencies['penalties'], dependencies['territory'])):
            upstream_methods.update(row['method_id'] for row in method_rows if row['method_id'] is not None)
        construction = compose_player_value(spatial,execution,shootiness,penalties,territory,states)
        constructions[player] = construction
        require(evidence['unit_position'] == construction['unit_position'], 'ledger unit position differs from shootiness role')
        for actual, expected, shared in zip(evidence['execution_states'],construction['execution_states'],states,strict=True):
            for field, item in expected.items():
                if field in ('strength','use'):
                    require(item == actual[field], 'ledger execution construction selection differs')
                else:
                    _check_estimate(actual[field],item)
                if field in ('finishing_goals','setting_goals') and item['value'] == 0 and (
                        shared['hours'] == 0 or shared['attempts_per_hour']['value'] == 0):
                    require(actual[field]['value'] == 0, 'zero ledger workload or opportunity requires exact zero')
        league_vectors[player] = {term: data['components'][term]['league_goals'] for term in TERMS}
    for shared in states:
        require((shared['execution_panel'] is not None) == (selected_score is not None or shared['strength'] in supplied_panel),
                'ledger execution panel availability differs from its saved or published source')
    minor = next(row for row in states if row['strength']=='4v5')['attempt_reference']
    require(supplied_minor or minor['included_seconds'] == 0,
            'ledger 4v5 opportunity lacks a saved minor reference')
    for method_id in upstream_methods:
        upstream = catalogs['method'][method_id]
        require(method['purpose'] == upstream['purpose'] and set(upstream['fit_seasons']) <= set(method['fit_seasons'])
                and (upstream['training_cutoff'] is None or method['training_cutoff'] is not None
                     and upstream['training_cutoff'] <= method['training_cutoff']),
                'ledger method drops upstream fitting purpose, years or cutoff')

    regenerated, members = build_depth_groups(dict(groups=[
        {**{key:value for key,value in group.items() if key!='cutoff_seconds'}, 'members': [
            {key:value for key,value in member.items() if key not in ('rank','depth')} for member in group['members']]}
        for group in groups],positions=positions))
    require(regenerated == groups, 'ledger ranks/cutoffs differ from source-complete team time')
    for position in POSITIONS:
        expected = compose_depth_reference(members[position],league_vectors)
        _compare_reference(annual['positions'][position],expected,league_vectors)
    for player, construction in constructions.items():
        _compare_player(players[player]['data'],construction,annual['positions'],positions[player]['group'],league_vectors)
