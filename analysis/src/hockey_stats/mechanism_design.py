"""source-qualified ordinary-minor opportunities and conditional shooter choices."""

from collections import Counter
from dataclasses import dataclass, field
import hashlib
import json
from math import fsum
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.sparse import csr_matrix

from .input_locations import input_path
from .analysis_data import PreparedManifest, read_prepared, read_prepared_game, read_prepared_people
from .artifacts import require
from .chance_cli import identity, read_json
from .coaches import read_coaches
from .descriptive import _dressed, _actor_identities, _valid_membership
from .elapsed_design import CONTEXT_AXES, actor_columns, actor_matrix, elapsed_context, transform_context
from .execution_history import _value
from .reconstruct import MEMBERSHIP_FIELDS, REPORT_CODES, membership_interval_link, report_membership, roster_identities

STATES = ('5v5', '5v4', '5v3', '4v3', '4v5', '3v5', '3v4')
ROLES = ('F', 'D', 'unknown')
REPEAT = ('none', 'repeat', 'switch', 'unknown')
PENALTY_AXES = (*CONTEXT_AXES, *(dict(name='repeat:' + value, continuous=False, unit='fraction') for value in REPEAT))


def _recipe(family):
    definition = dict(version=family + '-v1-10-1', family=family,
        source_policy='independent-native-membership-1', age='none', states=list(STATES),
        positions=list(ROLES), unknown='explicit; no position or missing-response imputation')
    if family == 'penalties':
        definition.update(population='genuine 5v5, both goalies; two directed opportunities per physical hour',
            response='source-complete MIN2/BEN2 group residual counts after opposing cancellation; MIS/GAM companions only',
            assignment='first source-ordered report full roster-checked membership; unique immediately-before maximal segment; before|both native link',
            exclusions='independent membership plus unresolved possible award maximal-segment union; no attempt/value mask',
            repeat='taking side relative to last source-qualified residual at any strength; one post-group update; unresolved makes unknown',
            context='full elapsed ev context and coach score/shell, freshly exposure centered/scaled; authoritative pre-event score; counters frozen at child boundary',
            equation='eta=log(r)+intercept+draw_players+take_players+coaches+context; loss=sum(hours*exp(eta))-sum(count*eta)+prior',
            offset='r=(qualified_awards+1)/(directed_hours+1)',
            priors=dict(player_entry_sd=.25,player_carry_sd_per_sqrt_year=.10,coach_entry_sd=.10,coach_carry_sd_per_sqrt_year=.05,context_sd=1.,intercept_sd=2.),
            carry='raw last likelihood-supported coordinate by actor/subblock; entry OR carry; directed roles share information years',
            reference='role-slot-time player centers; applicable-time coach centers transferred to intercept/context; centered context zero; one focal slot',
            value='T=2/60; tau=-expm1(-a*T)/a or T at a=0; V=(a-e_f-b+e_a)*tau; draw=rate_difference*V; take=-rate_difference*V')
    else:
        definition.update(population='ordinary physical team attempts including blocks/tips, both goalies, actual dated attacking skater candidates',
            equation='logit=log(w(role,state))+role_offset[role,state]+b_player; loss=sum(multiplicity*(logsumexp(logits)-winner_logit))+prior',
            role_weight='F:(2/3)/n_F; D:(1/3)/n_D; unknown:1/unit_size; absent role no candidates',
            role_contrasts='two per state; reconstructed F,D,unknown offsets sum to zero; sd 1 on all three offsets',
            priors=dict(player_entry_sd=.5,player_carry_sd_per_sqrt_year=.2),
            carry='raw last candidate-supported coordinate; minutes do not supply likelihood information',
            reference='candidate-incidence centers transferred to reporting role offsets without reimposing zero-sum; one same-position focal slot',
            units={'5v5':[3,2],'5v4':[4,1],'5v3':[4,1],'4v3':[3,1],'4v5':[2,2],'3v5':[1,2],'3v4':[1,2]},
            qualification='exact-state native membership seconds minus corroborated membership conflicts; independent of choice exclusions')
    definition['solver'] = dict(maxiter=10000,ftol=1e-15,gtol=1e-6,maxcor=10,final_continuation=dict(ftol=1e-16,gtol=1e-7),choice_batch_limit=4096)
    return dict(name=family + '-v1-10-1', version=family + '-v1-10-1', definition=definition,
        sha256=hashlib.sha256(json.dumps(definition,sort_keys=True,separators=(',',':')).encode()).hexdigest())

PENALTY_RECIPE = _recipe('penalties')
SHOOTINESS_RECIPE = _recipe('shootiness')


@dataclass
class PenaltyDesign:
    purpose: str
    season: str
    prepared: dict
    coaches: dict
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
    event_counts: np.ndarray
    time_keys: tuple
    event_keys: tuple
    transforms: dict
    coverage: dict
    recipe: dict
    resources: dict = field(default_factory=dict)

    @property
    def family(self):
        return 'penalties'


@dataclass
class ShootinessDesign:
    purpose: str
    season: str
    prepared: dict
    coaches: None
    training_cutoff: str | None
    players: tuple
    player_facts: dict
    choice_offsets: np.ndarray
    candidate_ids: np.ndarray
    candidate_roles: np.ndarray
    choice_states: np.ndarray
    winner_indices: np.ndarray
    multiplicities: np.ndarray
    choice_keys: tuple
    coverage: dict
    recipe: dict
    resources: dict = field(default_factory=dict)

    @property
    def family(self):
        return 'shootiness'


def shootiness_role(position):
    return 'F' if position in ('C','L','R','F') else 'D' if position == 'D' else 'unknown'


def repeat_state(previous, taking_side):
    return previous if previous in ('none','unknown') else 'repeat' if previous == taking_side else 'switch'


def classify_penalty_group(rows):
    """return source net awards; this does not establish elapsed assignment."""
    counts = dict(home=0,away=0)
    if not rows:
        return 'unresolved', counts
    unresolved, ordinary, nonordinary = False, False, False
    for row in rows:
        kind, duration, side = row['penalty_type'], row['penalty_duration_minutes'], row['owner_side']
        if not row['kind_valid'] or kind is None:
            unresolved = True
        elif kind in ('MIS','GAM'):
            continue
        elif kind in ('MIN','BEN') and duration == 2:
            ordinary = True
            if side not in counts:
                unresolved = True
            else:
                counts[side] += 1
        elif kind in ('MAJ','MAT','PS') or kind == 'MIN' and duration == 4:
            nonordinary = True
        else:
            unresolved = True
    if unresolved or ordinary and nonordinary:
        return 'unresolved', dict(home=0,away=0)
    if not ordinary:
        return 'outside_population', counts
    cancel = min(counts.values())
    counts = {side:count-cancel for side,count in counts.items()}
    return ('residual' if any(counts.values()) else 'cancelled'), counts


def mechanism_membership(game):
    """native membership/horizon support, minus corroborated identity/strength conflicts."""
    source = game['game']
    identity = source['identity'] or source['inventory']
    teams = (str(identity['away_team_id']),str(identity['home_team_id']))
    dressed = _dressed(game)
    identities = _actor_identities(game,dressed)
    periods = {row['period_number']:row for row in source['periods'] or []}
    excluded, reasons = set(), []
    for segment in game['segments'] or []:
        period = periods.get(segment['period_number'])
        valid = period is not None and period['status'] == 'supported' and period['end_seconds'] is not None and 0 <= segment['start_seconds'] < segment['end_seconds'] <= period['end_seconds']
        if not valid or not _valid_membership(segment,teams,dressed,identities,game['people'] or {}):
            excluded.add(segment['segment_index'])
            reasons.append(dict(code='membership_or_horizon_unavailable',affected_segment_indices=[segment['segment_index']]))
    # only these source-proved conflicts concern membership, not action/type/location/value.
    for row in game['ordinary_attempt_support']['reasons']:
        if row['code'] in ('identity_conflict','strength_conflict'):
            excluded.update(row['affected_segment_indices'])
            reasons.append(row)
    included = {row['segment_index'] for row in game['segments'] or []} - excluded
    gap = not source['periods'] or not game['segments'] or any(row['status'] != 'supported' for row in source['periods'] or []) or any(row['classification'] == 'unresolved' for row in source['native_intervals'] or [])
    return dict(included_segments=included,excluded_segments=excluded,reasons=reasons,unquantified_gap=gap)


def _affected(segments, period, clock):
    return [row['segment_index'] for row in segments if (period is None or row['period_number'] == period) and
        (clock is None or row['start_seconds'] <= clock <= row['end_seconds'])]


def penalty_groups(game):
    """classify complete source groups, preserving unresolved groups and original locators."""
    source = game['game']
    api = [row for row in game['events'] or [] if row['source']['type_key'] == 'penalty' or not row['source']['kind_valid']]
    known_codes = set(REPORT_CODES.values()) | {'PGSTR','PGEND','ANTHEM','CHL','GOFF','GON'}
    reports = [row for row in source['report_rows'] or [] if row['event_code'] == 'PENL' or row['event_code'] not in known_codes]
    api_groups, report_groups = {}, {}
    for row in api:
        native = row['source']
        api_groups.setdefault((native['period_number'],native['elapsed_seconds']),[]).append(row)
    for row in reports:
        report_groups.setdefault((row['period_number'],row['elapsed_seconds']),[]).append(row)
    all_api = [row['source'] for row in game['events'] or []]
    event_ids = Counter(row['event_id'] for row in all_api if row['event_id'] is not None)
    orders = Counter(row['sort_order'] for row in all_api if row['sort_order'] is not None)
    report_ids = Counter(row['row_id'] for row in source['report_rows'] or [])
    report_numbers = Counter(row['event_number'] for row in source['report_rows'] or [] if row['event_number'] is not None)
    identities = roster_identities([row for person in (game['people'] or {}).values() for row in person['roster']])
    identity = source['identity'] or source['inventory']
    segments = game['segments'] or []
    result = []
    keys = set(api_groups) | set(report_groups)
    for period, clock in sorted(keys,key=lambda x:(x[0] if x[0] is not None else -1,x[1] if x[1] is not None else -1)):
        events = sorted(api_groups.get((period,clock),[]),key=lambda row:row['source']['source_index'])
        report_rows = sorted(report_groups.get((period,clock),[]),key=lambda row:row['source_index'])
        reasons = []
        rows = []
        for event in events:
            row = event['source']
            side = next((side for side in ('home','away') if row['owner_team_id'] == identity[side+'_team_id']),None)
            rows.append(dict(row,owner_side=side))
        disposition, counts = classify_penalty_group(rows)
        if any(row['event_code'] != 'PENL' for row in report_rows):
            reasons.append('possible_penalty_report_kind_unresolved')
        if len(events) != len(report_rows) or not events:
            reasons.append('source_group_cardinality_unresolved')
        horizon = next((row['end_seconds'] for row in source['periods'] or [] if row['period_number'] == period and row['status'] == 'supported'),None)
        bad_clock = period is None or clock is None or clock < 0 or horizon is not None and clock > horizon or any(row['source']['timed_period'] is not True for row in events)
        if bad_clock:
            reasons.append('penalty_clock_unavailable')
        if any(row['source']['event_id'] is None or event_ids[row['source']['event_id']] != 1 or row['source']['sort_order'] is None or orders[row['source']['sort_order']] != 1 for row in events):
            reasons.append('api_identity_unresolved')
        if any(row['row_id'] is None or report_ids[row['row_id']] != 1 or row['event_number'] is None or report_numbers[row['event_number']] != 1 for row in report_rows):
            reasons.append('report_identity_unresolved')
        if disposition == 'unresolved' and not reasons:
            reasons.append('compound_or_unknown_penalty_kind')
        if reasons:
            disposition,counts = 'unresolved',dict(home=0,away=0)
        segment_index,chunk_index,relation = None,None,None
        assignment = 'not_applicable'
        if disposition == 'residual':
            member_issues = []
            membership,invalid = report_membership(report_rows[0],identity,identities,member_issues)
            if not invalid:
                relation,_ = membership_interval_link(membership,period,clock,source['native_intervals'],source['periods'])
                matches = [row for row in segments if row['period_number'] == period and row['start_seconds'] < clock <= row['end_seconds'] and row['membership'] == membership]
                if relation in ('before','both') and len(matches) == 1:
                    segment_index = matches[0]['segment_index']
                    children = [row for row in game['chunks'] or [] if row['segment_index'] == segment_index and row['start_seconds'] < clock <= row['end_seconds']]
                    if len(children) == 1:
                        chunk_index = children[0]['chunk_index']
            assignment = 'assigned' if chunk_index is not None else 'unresolved'
            if assignment == 'unresolved':
                reasons.append('pre_award_assignment_unresolved')
        result.append(dict(game_id=game['game_id'],period_number=period,clock_seconds=clock,
            source_indices=[row['source']['source_index'] for row in events],report_source_indices=[row['source_index'] for row in report_rows],
            api_locators=[f"/events/{row['source']['source_index']}/source" for row in events],
            report_locators=[f"/game/report_rows/{row['source_index']}[{row['row_id']}]" for row in report_rows],
            group_disposition=disposition,residual_counts=counts,elapsed_assignment=assignment,
            segment_index=segment_index,chunk_index=chunk_index,membership_relation=relation,reasons=reasons,
            affected_segment_indices=_affected(segments,period,None if bad_clock else clock) if disposition == 'unresolved' or assignment == 'unresolved' else []))
    # known clocks order report-only groups correctly. unlocatable api rows use
    # their source position; an unlocatable report has no defensible position.
    located = [row for row in result if row['period_number'] is not None and row['clock_seconds'] is not None]
    located.sort(key=lambda row:(row['period_number'],row['clock_seconds']))
    unlocated = [row for row in result if row not in located]
    for row in unlocated:
        index = min(row['source_indices']) if row['source_indices'] else None
        later = next((i for i,known in enumerate(located) if index is not None and known['source_indices'] and min(known['source_indices']) > index),0 if index is None else len(located))
        located.insert(later,row)
    result = located
    previous = 'none' if game['events'] is not None and source['report_rows'] is not None else 'unknown'
    for row in result:
        row['previous_taking_side'] = previous
        if row['group_disposition'] == 'residual':
            previous = next(side for side,count in row['residual_counts'].items() if count)
        elif row['group_disposition'] == 'unresolved':
            previous = 'unknown'
        row['next_taking_side'] = previous
    return result


def choice_population(game):
    """valid choices use actual source-checked members; invalid choices are independent."""
    identity = game['game']['identity'] or game['game']['inventory']
    teams = (str(identity['away_team_id']),str(identity['home_team_id']))
    dressed = _dressed(game)
    identities = _actor_identities(game,dressed)
    result = []
    for attempt in game['attempts'] or []:
        state,details = attempt['feature_facts']['state'],attempt['details']
        membership = {key:_value(state,key) for key in MEMBERSHIP_FIELDS}
        side = _value(state,'home_away')
        shooter = _value(details,'physical_shooter_id')
        status,reason,strength = 'excluded','physical_attempt_unresolved',None
        candidates = []
        known_candidates = []
        physical = _value(details,'physical_status')
        if side in ('home','away') and all(membership[key] is not None for key in MEMBERSHIP_FIELDS) and _value(details,'shooting_team_id') == _value(state,'shooting_team_id') == identity[side+'_team_id']:
            other = 'away' if side == 'home' else 'home'
            if all(len(membership[s+'_goalies']) == 1 for s in ('home','away')):
                strength = f"{len(membership[side+'_skaters'])}v{len(membership[other+'_skaters'])}"
        if physical == 'outside_population':
            status,reason = 'outside_population','not_ordinary'
        elif physical == 'ordinary' and side in ('home','away'):
            other = 'away' if side == 'home' else 'home'
            if all(membership[key] is not None for key in MEMBERSHIP_FIELDS):
                physical_strength = f"{len(membership[side+'_skaters'])}v{len(membership[other+'_skaters'])}"
                if any(len(membership[s+'_goalies']) != 1 for s in ('home','away')) or physical_strength not in STATES:
                    status,reason = 'outside_population','physical_strength_outside'
                elif not _valid_membership(dict(membership=membership),teams,dressed,identities,game['people'] or {}):
                    reason = 'dated_membership_unresolved'
                elif _value(details,'shooting_team_id') != identity[side+'_team_id'] or _value(state,'shooting_team_id') != identity[side+'_team_id']:
                    reason = 'shooting_team_unresolved'
                elif shooter in membership[side+'_goalies']:
                    status,reason = 'outside_population','goalie_attempt'
                elif shooter not in membership[side+'_skaters']:
                    reason = 'physical_shooter_unresolved'
                else:
                    status,reason,candidates = 'included',None,list(map(str,membership[side+'_skaters']))
        if side in ('home','away') and strength in STATES and all(membership[key] is not None for key in MEMBERSHIP_FIELDS) and _valid_membership(dict(membership=membership),teams,dressed,identities,game['people'] or {}):
            known_candidates = list(map(str,membership[side+'_skaters']))
        result.append(dict(game_id=game['game_id'],source_index=attempt['source_index'],
            locator=f"/attempts/{attempt['source_index']}",status=status,reason=reason,strength=strength,
            attacking_side=side,candidates=candidates,known_candidates=known_candidates,shooter_id=str(shooter) if shooter is not None else None))
    return result


def _prepared_inputs(prepared,season):
    if not isinstance(prepared,PreparedManifest):
        path = input_path(prepared, strict=True)
        purpose = read_json(path/'manifest.json' if path.is_dir() else path)['purpose']
        prepared = read_prepared(path,purpose)
    selected = next((row for row in prepared['seasons'] if row['season'] == season),None)
    require(selected is not None,'mechanism season not selected in preparation')
    people = {str(_value(row,'player_id')):row for row in read_prepared_people(prepared,season)['people']}
    players = tuple(sorted(p for p,row in people.items() if _value(row,'position_group') != 'G'))
    facts = {p:dict(position_group=shootiness_role(_value(people[p],'position_group'))) for p in players}
    ref = dict(purpose=prepared['purpose'],**identity(prepared.directory/'manifest.json'),members=[row for row in prepared['files'] if row['season'] == season])
    return prepared,selected,players,facts,ref


def _state_support():
    return dict(included_seconds=0.,known_excluded_seconds=0.,unquantified_gap=False,team_choices=0,personal_attempts=0,excluded_possible_choices=0)


def _qualification(game,membership,players,*,extra_excluded=()):
    result = {p:{state:_state_support() for state in STATES} for p in players}
    excluded = membership['excluded_segments'] | set(extra_excluded)
    for segment in game['segments'] or []:
        members = segment['membership']
        if any(members[key] is None for key in MEMBERSHIP_FIELDS) or any(len(members[side+'_goalies']) != 1 for side in ('home','away')):
            continue
        duration = segment['end_seconds']-segment['start_seconds']
        for side in ('home','away'):
            other = 'away' if side == 'home' else 'home'
            state = f"{len(members[side+'_skaters'])}v{len(members[other+'_skaters'])}"
            if state not in STATES:
                continue
            for player in members[side+'_skaters']:
                require(str(player) in result,'native skater missing from annual identity axis')
                result[str(player)][state]['known_excluded_seconds' if segment['segment_index'] in excluded else 'included_seconds'] += duration
    for player in (game['people'] or {}):
        if player in result:
            for value in result[player].values():
                value['unquantified_gap'] = membership['unquantified_gap']
    return result


def prepare_shootiness(prepared,season):
    started = perf_counter()
    prepared,selected,players,facts,prepared_ref = _prepared_inputs(prepared,season)
    player_axis = {p:i for i,p in enumerate(players)}
    qualification = {p:dict(states={state:_state_support() for state in STATES}) for p in players}
    offsets,ids,roles,states,winners,multiplicities,keys,games,dates = [0],[],[],[],[],[],[],[],[]
    for game_id in selected['selected_game_ids']:
        game = read_prepared_game(prepared,season,game_id)
        membership = mechanism_membership(game)
        supports = _qualification(game,membership,players)
        choices = choice_population(game)
        for choice in choices:
            if choice['status'] != 'included':
                if choice['status'] == 'excluded' and choice['strength'] in STATES:
                    for player in choice['known_candidates']:
                        if player in supports:
                            supports[player][choice['strength']]['excluded_possible_choices'] += 1
                continue
            strength = choice['strength']
            candidates = choice['candidates']
            require(all(p in player_axis for p in candidates),'choice candidate missing from annual identity axis')
            ids.extend(player_axis[p] for p in candidates)
            roles.extend(ROLES.index(facts[p]['position_group']) for p in candidates)
            states.append(STATES.index(strength))
            winners.append(offsets[-1]+candidates.index(choice['shooter_id']))
            multiplicities.append(1)
            offsets.append(len(ids))
            keys.append(choice)
            for p in candidates:
                supports[p][strength]['team_choices'] += 1
            supports[choice['shooter_id']][strength]['personal_attempts'] += 1
        for p in players:
            for state in STATES:
                for name,value in supports[p][state].items():
                    if name == 'unquantified_gap':
                        qualification[p]['states'][state][name] |= value
                    else:
                        qualification[p]['states'][state][name] += value
        parsed = {row['source_index'] for row in choices}
        unassigned = [dict(source='api',source_index=row['source_index'],reason='possible_attempt_without_physical_evidence',
            locator=f"/ordinary_attempt_support/events/{ordinal}",affected_segment_indices=[]) for ordinal,row in enumerate(game['ordinary_attempt_support']['events'] or [])
            if row['source_index'] not in parsed and row['disposition'] != 'not_applicable']
        reports = {row['source_index']:row for row in game['game']['report_rows'] or []}
        unassigned += [dict(source='report',report_source_index=row['report_source_index'],reason='unmatched_possible_attempt',
            locator=f"/ordinary_attempt_support/report_only/{ordinal}",affected_segment_indices=row['affected_segment_indices'])
            for ordinal,row in enumerate(game['ordinary_attempt_support']['report_only'] or [])
            if reports[row['report_source_index']]['period_number'] != 5 and reports[row['report_source_index']]['penalty_shot'] is not True]
        games.append(dict(game_id=game_id,choices=choices,unassigned_possible_choices=unassigned,
            excluded_possible_choices=sum(row['status'] == 'excluded' for row in choices)+len(unassigned),
            source_collection_gap=game['events'] is None or game['game']['report_rows'] is None or game['attempts'] is None,
            excluded_segments=sorted(membership['excluded_segments']),membership_reasons=membership['reasons'],unquantified_gap=membership['unquantified_gap']))
        dates.append(game['game']['inventory']['game_date'])
    coverage = dict(purpose=prepared['purpose'],season=season,qualification=qualification,players=qualification,games=games,
        included_choices=len(keys),candidate_incidence=len(ids),personal_attempts=len(keys),
        states=[dict(strength=state,team_choices=sum(row['strength'] == state for row in keys)) for state in STATES])
    return ShootinessDesign(prepared['purpose'],season,prepared_ref,None,max(dates) if dates else None,players,facts,
        np.asarray(offsets,dtype=np.int64),np.asarray(ids,dtype=np.int64),np.asarray(roles,dtype=np.int64),np.asarray(states,dtype=np.int64),
        np.asarray(winners,dtype=np.int64),np.asarray(multiplicities,dtype=np.int64),tuple(keys),coverage,SHOOTINESS_RECIPE,
        dict(preparation_seconds=perf_counter()-started))


def prepare_penalties(prepared,coaches,season):
    started = perf_counter()
    prepared,selected,players,facts,prepared_ref = _prepared_inputs(prepared,season)
    coach_path = input_path(coaches, strict=True)
    coach_data = read_coaches(coach_path,prepared['purpose'])
    coach_games = {row['game_id']:row for row in coach_data['games'] if row['season'] == season}
    require(set(selected['selected_game_ids']) <= set(coach_games),'coaches omit selected mechanism games')
    coach_ref = dict(purpose=prepared['purpose'],**identity(coach_path),selected_game_ids=list(selected['selected_game_ids']))
    coach_ids = tuple(sorted(row['coach_id'] for row in read_json(coach_path.parent/'identities.json')['coaches']))
    actors = actor_columns(players,coach_ids)
    qualification = {p:dict(included_seconds=0.,known_excluded_seconds=0.,unquantified_gap=False,events=0,reason_counts=[]) for p in players}
    time_rows,event_rows,game_coverage,dates = [],[],[],[]
    for game_id in selected['selected_game_ids']:
        game = read_prepared_game(prepared,season,game_id)
        require(game['game']['identity'] is None or all(game['game']['identity'][key] == coach_games[game_id][key] for key in ('home_team_id','away_team_id')),'mechanism coach team identity differs')
        membership = mechanism_membership(game)
        groups = penalty_groups(game)
        award_gap = game['events'] is None or game['game']['report_rows'] is None or any((row['group_disposition'] == 'unresolved' or row['elapsed_assignment'] == 'unresolved') and not row['affected_segment_indices'] for row in groups)
        segments = {row['segment_index']:row for row in game['segments'] or []}
        chunks = {row['chunk_index']:row for row in game['chunks'] or []}
        events = {row['source']['source_index']:row for row in game['events'] or []}
        event_orders = {index:_value(row['chronology'],'order_index') for index,row in events.items()}
        excluded = set(membership['excluded_segments'])
        if game['events'] is None or game['game']['report_rows'] is None:
            excluded.update(segments)
        for group in groups:
            excluded.update(group['affected_segment_indices'])
        supports = _qualification(game,membership,players,extra_excluded=excluded)
        for player in players:
            value = supports[player]['5v5']
            for key in ('included_seconds','known_excluded_seconds'):
                qualification[player][key] += value[key]
            qualification[player]['unquantified_gap'] |= value['unquantified_gap'] or (award_gap and player in (game['people'] or {}))
        # known clocks update elapsed context after the group, even if model exposure is excluded.
        updates = sorted([row for row in groups if row['period_number'] is not None and row['clock_seconds'] is not None],key=lambda row:(row['period_number'],row['clock_seconds']))
        physical = 0.
        for chunk in chunks.values():
            segment = segments[chunk['segment_index']]
            members = segment['membership']
            if segment['segment_index'] in excluded or any(len(members[side+'_skaters']) != 5 or len(members[side+'_goalies']) != 1 for side in ('home','away')):
                continue
            period = segment['period_number']
            boundaries = sorted({chunk['start_seconds'],chunk['end_seconds'],*(row['clock_seconds'] for row in updates if row['period_number'] == period and chunk['start_seconds'] < row['clock_seconds'] < chunk['end_seconds'])})
            for start,end in zip(boundaries,boundaries[1:]):
                require(end > start,'nonpositive mechanism child duration')
                # an unknown-clock group removes its entire period; later periods
                # retain its sequence update unless a later source-known award repairs it.
                prior = [row for row in groups if row['period_number'] is not None and
                    (row['period_number'] < period or row['period_number'] == period and
                     row['clock_seconds'] is not None and row['clock_seconds'] <= start)]
                previous = prior[-1]['next_taking_side'] if prior else ('none' if game['events'] is not None and game['game']['report_rows'] is not None else 'unknown')
                physical += (end-start)/3600
                for side in ('home','away'):
                    other = 'away' if side == 'home' else 'home'
                    raw,margin = elapsed_context(game,segment,chunk,side,coach_games[game_id],chunk['score']['values'],chunk['strength_transition'])
                    repeat = repeat_state(previous,other)
                    raw += [float(repeat == value) for value in REPEAT]
                    key = dict(game_id=game_id,segment_index=segment['segment_index'],chunk_index=chunk['chunk_index'],
                        start_seconds=start,end_seconds=end,source_index=None,attacking_side=side,
                        attacking_players=list(map(str,members[side+'_skaters'])),defending_players=list(map(str,members[other+'_skaters'])),
                        attacking_team_id=game['game']['identity'][side+'_team_id'],defending_team_id=game['game']['identity'][other+'_team_id'],repeat=repeat)
                    time_rows.append((key,(end-start)/3600,raw,margin,period))
        included_count = 0
        for group in groups:
            group['model_disposition'] = 'not_applicable'
            if group['group_disposition'] != 'residual':
                continue
            if group['elapsed_assignment'] != 'assigned' or group['segment_index'] in excluded:
                group['model_disposition'] = 'excluded'
                continue
            segment,chunk = segments[group['segment_index']],chunks[group['chunk_index']]
            members = segment['membership']
            if any(len(members[side+'_skaters']) != 5 or len(members[side+'_goalies']) != 1 for side in ('home','away')):
                group['model_disposition'] = 'outside_population'
                continue
            group['model_disposition'] = 'included'
            event = events[group['source_indices'][0]]
            order = event_orders[group['source_indices'][0]]
            for taking,count in group['residual_counts'].items():
                if not count:
                    continue
                side = 'away' if taking == 'home' else 'home'
                score = event['pre_score']['values'] if order is not None else dict(home=None,away=None)
                raw,margin = elapsed_context(game,segment,chunk,side,coach_games[game_id],score,event['context']['strength_transition'],
                    focal_order=order,focal_seconds=group['clock_seconds'],order_by_source=event_orders)
                repeat = repeat_state(group['previous_taking_side'],taking)
                raw += [float(repeat == value) for value in REPEAT]
                key = dict(game_id=game_id,segment_index=group['segment_index'],chunk_index=group['chunk_index'],
                    source_index=group['source_indices'][0],source_indices=group['source_indices'],report_source_indices=group['report_source_indices'],
                    attacking_side=side,attacking_players=list(map(str,members[side+'_skaters'])),defending_players=list(map(str,members[taking+'_skaters'])),
                    attacking_team_id=game['game']['identity'][side+'_team_id'],defending_team_id=game['game']['identity'][taking+'_team_id'],repeat=repeat)
                event_rows.append((key,count,raw,margin,segment['period_number']))
                included_count += count
                for player in key['attacking_players']+key['defending_players']:
                    qualification[player]['events'] += count
        game_coverage.append(dict(game_id=game_id,groups=groups,physical_included_hours=physical,directed_included_hours=2*physical,
            qualified_awards=included_count,excluded_segment_union=sorted(excluded),membership_reasons=membership['reasons'],
            known_lost_physical_hours=fsum(row['end_seconds']-row['start_seconds'] for row in segments.values() if row['segment_index'] in excluded and all(len(row['membership'][side+'_skaters']) == 5 and len(row['membership'][side+'_goalies']) == 1 for side in ('home','away')))/3600,
            unquantified_gap=membership['unquantified_gap'] or award_gap))
        dates.append(game['game']['inventory']['game_date'])
    hours = np.asarray([row[1] for row in time_rows],dtype=np.float64)
    counts = np.asarray([row[1] for row in event_rows],dtype=np.float64)
    raw_time = np.asarray([row[2] for row in time_rows],dtype=np.float64).reshape(-1,len(PENALTY_AXES))
    raw_event = np.asarray([row[2] for row in event_rows],dtype=np.float64).reshape(-1,len(PENALTY_AXES))
    context_time,context_event,moments = transform_context(raw_time,raw_event,hours,[axis['continuous'] for axis in PENALTY_AXES])
    transforms = dict(axes=[dict(axis,**moment) for axis,moment in zip(PENALTY_AXES,moments,strict=True)])
    columns = tuple(actors+[dict(kind='context',name=axis['name']) for axis in PENALTY_AXES])
    transforms['design_sha256'] = hashlib.sha256(json.dumps(dict(recipe=PENALTY_RECIPE['sha256'],columns=columns,transforms=transforms),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    coverage = dict(purpose=prepared['purpose'],season=season,qualification=qualification,players=qualification,games=game_coverage,
        physical_included_hours=float(hours.sum()/2),directed_included_hours=float(hours.sum()),qualified_awards=float(counts.sum()),
        player_slot_hours=fsum(value['included_seconds'] for value in qualification.values())/3600)
    require(abs(coverage['player_slot_hours']-10*coverage['physical_included_hours']) <= 1e-8*(1+coverage['player_slot_hours']),'penalty role-slot time does not reconcile to physical exposure')
    return PenaltyDesign(prepared['purpose'],season,prepared_ref,coach_ref,max(dates) if dates else None,players,facts,coach_ids,columns,
        actor_matrix(time_rows,actors,coach_games),actor_matrix(event_rows,actors,coach_games),context_time,context_event,hours,counts,
        tuple(row[0] for row in time_rows),tuple(row[0] for row in event_rows),transforms,coverage,PENALTY_RECIPE,
        dict(preparation_seconds=perf_counter()-started))
