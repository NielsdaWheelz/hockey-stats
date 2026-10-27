"""source-backed factual cards over prepared evidence and observed receipts."""

from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
import hashlib
import math
from typing import Iterable, Literal, NotRequired, TypedDict

from .analysis_records import PreparedGame, PreparedPeople, PreparedEvent, Association
from .observed import Metrics, PlayerGame, ObservedResult

from .artifacts import require
from .analysis_publication import CONTEXT_POPULATIONS, FAMILY_TABLES, KEYS
from .shot_origins import in_rink
from .scoring_credits import actor_issue

_MEMBERS = ('away_skaters', 'home_skaters', 'away_goalies', 'home_goalies')
_GROUPS = ('ev', 'pp', 'pk', 'other', 'five_on_five')
_FIVE = (5, 5, True, True)


class ObservedGameReceipt(TypedDict):
    game_id: str
    status: str
    source_inputs: list[dict]
    event_dispositions: list[dict]
    deployment_pairs: list[dict]
    segments: NotRequired[list[dict]]
    spatial_masks: NotRequired[list[dict]]
    spatial_event_dispositions: NotRequired[list[dict]]
    native_checks: NotRequired[list[dict]]


class PersonIdentity(TypedDict):
    player_id: str
    kind: Literal['skater', 'goalie']
    reported_position: str | None


class SourceIds(TypedDict):
    facts: str
    p: str
    u: str
    h: str
    b: str
    tracking: str
    skating: str


class SupportProjection(TypedDict):
    segments: list[dict]
    prepared_segment_indices: dict[int, int]
    events: dict[int, PreparedEvent]
    associations: dict[int, Association]
    dressed_teams: dict[str, str]
    actor_identities: dict[int, dict]


class RecordedEvidence(TypedDict):
    attempt_fact: list[dict]
    dressed_game: list[dict]
    interval_fact: list[dict]
    interval_player: list[dict]
    interval_location: list[dict]
    projection: SupportProjection
    dispositions: list[dict]
    masks: dict[str, set[int]]


class GameReduction(TypedDict):
    season: str
    game_id: str
    people: dict[str, dict]
    physical: dict[str, Counter]
    teams: tuple[str, str]
    penalty_ledger: list[dict]
    credit_issues: list[dict]
    dispositions: list[dict]
    deployment_gap: bool


class SeasonSummary(TypedDict):
    skater_descriptive: list[dict]
    skater_context: list[dict]
    context_coverage: list[dict]


def estimate(value, *, reason='no_exposure', explanation='no supported positive denominator'):
    return dict(value=value, unavailable_reason=None if value is not None else reason,
                reason_detail=None if value is not None else dict(explanation=explanation,
                    evidence=[]),
                uncertainty=dict(kind='not_estimated'))


def support(seconds=None, *, events=None, excluded=0, gap=False, reasons=()):
    counts = Counter(reasons)
    return dict(included_seconds=seconds, events=events, eligible_weight=None,
                known_excluded_seconds=excluded, unquantified_gap=gap,
                reason_counts=[dict(code=k, count=v) for k, v in sorted(counts.items())],
                inferred_inputs=[], current_season_information=True, prior_only=False, prior_seasons=[])


def project_support(prepared_game: PreparedGame, observed_game_receipt: ObservedGameReceipt) -> SupportProjection:
    """join the two segment axes by native identity and verify their full content."""
    require(prepared_game['game_id'] == observed_game_receipt['game_id'], 'observed/prepared game differs')
    segments = observed_game_receipt['segments'] if observed_game_receipt['status'] == 'reconstructed' else []
    projection = _project_segments(prepared_game, segments)
    for row in observed_game_receipt.get('event_dispositions', []):
        require(row['source_index'] in projection['events'], 'observed source event missing from preparation')
    return projection


def _project_segments(prepared_game, segments):
    """keep native membership identity authoritative for both evidence consumers."""
    prepared = prepared_game['segments'] or []
    by_native = {tuple(row['native_interval_indices']): row for row in prepared}
    require(len(by_native) == len(prepared), 'duplicate prepared native segment identity')
    mapping = {}
    for index, row in enumerate(segments):
        match = by_native.get(tuple(row['interval_indices']))
        require(match is not None and all(row[k] == match[k] for k in ('period_number','start_seconds','end_seconds'))
                and all(sorted(row[k]) == sorted(match['membership'][k] or []) for k in _MEMBERS),
                f"{prepared_game['game_id']}: observed/prepared interval identity differs")
        mapping[index] = match['segment_index']
    events = {row['source']['source_index']: row for row in prepared_game['events'] or []}
    require(len(events) == len(prepared_game['events'] or []), 'duplicate prepared source index')
    dressed = _dressed(prepared_game)
    identities = _actor_identities(prepared_game,dressed)
    return dict(segments=segments, prepared_segment_indices=mapping, events=events,dressed_teams=dressed,actor_identities=identities,
                associations={row['source_index']: row for row in prepared_game['associations'] or []})


def state_tuple(membership, side='away'):
    other = 'home' if side == 'away' else 'away'
    if any(membership[k] is None for k in _MEMBERS):
        return None
    return (len(membership[side+'_skaters']), len(membership[other+'_skaters']),
            bool(membership[side+'_goalies']), bool(membership[other+'_goalies']))


def state_record(state):
    return dict(zip(('attacking_skaters','defending_skaters','attacking_goalie_present','defending_goalie_present'), state))


def strength_group(state):
    attacking_skaters, defending_skaters, attacking_goalie_present, defending_goalie_present = state
    if attacking_goalie_present and defending_goalie_present:
        if attacking_skaters == defending_skaters and attacking_skaters in (3,4,5):
            return 'ev'
        if (attacking_skaters,defending_skaters) in ((5,4),(5,3),(4,3)):
            return 'pp'
        if (defending_skaters,attacking_skaters) in ((5,4),(5,3),(4,3)):
            return 'pk'
    return 'other'


def _dressed(prepared_game):
    """dated roster or boxscore identity, with contradictory teams left unresolved."""
    game = prepared_game['game']['inventory']
    result = {}
    for pid, person in (prepared_game['people'] or {}).items():
        rows = person['roster'] + person['boxscore']
        teams = {row['team_id'] for row in rows if row['player_id'] == int(pid)}
        value = person['people']['values']
        if (len(teams) == 1 and next(iter(teams)) in (game['away_team_id'], game['home_team_id'])
                and value['team_id'] == next(iter(teams)) and 'team_id' not in person['people']['problems']):
            result[str(pid)] = str(next(iter(teams)))
    return result


def _actor_identities(prepared_game, dressed):
    from .reconstruct import roster_identities
    identities = roster_identities([row for person in (prepared_game['people'] or {}).values() for row in person['roster']])
    return {pid:row for pid,row in identities.items() if dressed.get(str(pid)) == str(row['team_id'])}


def _valid_membership(segment, teams, dressed, identities, people):
    for side,team in zip(('away','home'),teams):
        for kind in ('skaters','goalies'):
            ids = segment['membership'][side+'_'+kind]
            if ids is None or len(ids) != len(set(ids)) or len(ids) > (1 if kind == 'goalies' else 6):
                return False
            for raw_pid in ids:
                actor = identities.get(raw_pid)
                if str(raw_pid) not in people or dressed.get(str(raw_pid)) != team or actor is None:
                    return False
                position = actor['reported_position']
                if kind == 'goalies' and position != 'G' or kind == 'skaters' and position not in ('C','L','R','D','F'):
                    return False
    return True


def execution_participation(prepared_game: PreparedGame) -> dict:
    """exact-strength elapsed qualification, independent of modeled attempts."""
    from .analysis_publication import EXECUTION_STRENGTHS

    identity = prepared_game['game']['identity'] or prepared_game['game']['inventory']
    teams = (str(identity['away_team_id']),str(identity['home_team_id']))
    dressed = _dressed(prepared_game)
    identities = _actor_identities(prepared_game,dressed)
    segments = prepared_game['segments'] or []
    valid_segments = {s['segment_index'] for s in segments if _valid_membership(
        s,teams,dressed,identities,prepared_game['people'] or {})}
    available = bool(valid_segments) and bool(prepared_game['game']['periods'])
    gap = not available or any(p['status'] != 'supported' for p in prepared_game['game']['periods'] or []) or any(
        row['classification'] == 'unresolved' for row in prepared_game['game']['native_intervals'] or [])
    result = {(str(pid),strength):support(0 if available else None,gap=gap,
              reasons=['elapsed_unavailable'] if gap else ())
              for pid,actor in identities.items() if actor['reported_position'] in ('C','L','R','D','F')
              for strength in EXECUTION_STRENGTHS}
    for segment in segments:
        valid = segment['segment_index'] in valid_segments
        seconds = segment['end_seconds']-segment['start_seconds']
        for side in ('away','home'):
            state = state_tuple(segment['membership'],side)
            if state is None or not all(state[2:]):
                continue
            strength = f'{state[0]}v{state[1]}'
            if strength not in EXECUTION_STRENGTHS:
                continue
            for pid in segment['membership'][side+'_skaters']:
                metric = result.get((str(pid),strength))
                if metric is None:
                    continue
                if valid:
                    metric['included_seconds'] += seconds
                else:
                    metric['known_excluded_seconds'] += seconds
                    reasons = Counter({r['code']:r['count'] for r in metric['reason_counts']})
                    reasons['membership_unavailable'] += 1
                    metric['reason_counts'] = [dict(code=k,count=v) for k,v in sorted(reasons.items())]
    for metric in result.values():
        metric['current_season_information'] = bool(metric['included_seconds'])
    return result


def summarize_execution_participation(game_supports: Iterable[dict]) -> dict:
    """sum source qualification; numerical consumers own coefficient information."""
    totals = {}
    for game in game_supports:
        for key,metric in game.items():
            total = totals.setdefault(key,dict(support(None),reason_counts=Counter()))
            if metric['included_seconds'] is not None:
                total['included_seconds'] = (total['included_seconds'] or 0)+metric['included_seconds']
            total['known_excluded_seconds'] += metric['known_excluded_seconds'] or 0
            total['unquantified_gap'] |= metric['unquantified_gap'] or metric['included_seconds'] is None
            total['reason_counts'].update({r['code']:r['count'] for r in metric['reason_counts']})
    for metric in totals.values():
        metric['reason_counts'] = [dict(code=k,count=v) for k,v in sorted(metric['reason_counts'].items())]
        metric['current_season_information'] = bool(metric['included_seconds'])
    return totals


def recorded_evidence(prepared_game: PreparedGame, observed_game_receipt: ObservedGameReceipt,
                      source_ids: SourceIds, support_ids: dict[str, str]) -> RecordedEvidence:
    """one physical interval projection supplies both summaries and stored facts."""
    projection = project_support(prepared_game, observed_game_receipt)
    year, gid = prepared_game['season'], prepared_game['game_id']
    identity = prepared_game['game']['identity'] or prepared_game['game']['inventory']
    away, home = str(identity['away_team_id']), str(identity['home_team_id'])
    source = dict(kind='source', id=source_ids['facts'])
    rows = {key: [] for key in ('attempt_fact','dressed_game','interval_fact','interval_player','interval_location')}
    rows['dressed_game'] = [dict(season=year, player_id=pid, game_id=gid, team_id=team, source=source)
                            for pid, team in sorted(_dressed(prepared_game).items())]
    attempts = {row['source_index']: row for row in prepared_game['attempts'] or []}
    dispositions = []
    reports = {r['source_index']: r for r in prepared_game['game']['report_rows'] or []}
    for index, record in sorted(projection['events'].items()):
        event = record['source']
        if event['type_key'] not in ('goal','shot-on-goal','missed-shot','blocked-shot'):
            continue
        association = projection['associations'].get(index)
        native = association['native'] if association else None
        modifier = native.get('goal_modifier_evidence') if native else None
        report = reports.get(native['report_source_index']) if native else None
        penalty_shot = report is not None and report['penalty_shot'] is True or modifier is not None and modifier['status'] == 'reported' and modifier['reported_value'] == 'penalty-shot'
        if not event['kind_valid'] or event['timed_period'] is not True or event['elapsed_seconds'] is None or penalty_shot:
            dispositions.append(dict(source_index=index, status='outside_population', reason='penalty_shot' if penalty_shot else 'unsupported_timed_kind'))
            continue
        attempt = attempts.get(index)
        detail = attempt['details']['values'] if attempt else {}
        outcome = {'goal':'goal','shot-on-goal':'save','missed-shot':'miss','blocked-shot':'block'}[event['type_key']]
        geometry = record['geometry']['values']
        x, y = geometry['x_ft'], geometry['y_ft']
        # prepared geometry is in home-attack orientation; source-event display is
        # in the shooting team's attacking orientation, once and only once.
        team = detail.get('shooting_team_id') or event['shooting_team_id']
        team = team if team in (int(away),int(home)) else None
        if str(team) == away and x is not None and y is not None:
            x, y = -x, -y
        if x is None or y is None or not in_rink(x,y):
            x = y = None
        location = 'unavailable' if x is None else 'block_contact' if outcome == 'block' else 'reported_event'
        membership = None
        if native is not None:
            membership = {k:native[k] for k in _MEMBERS}
        state = state_tuple(membership, 'home' if str(team) == home else 'away') if membership is not None and team in (int(away), int(home)) else None
        immediate = attempt['immediate_outcomes'] if attempt else None
        values = immediate['values'] if immediate else {}
        def label(key):
            value = values.get(key)
            problem = immediate['problems'].get(key, {}) if immediate else {}
            return value, None if value is not None else problem.get('reason', 'recorded immediate outcome unavailable')
        stop, stop_reason = label('recorded_goalie_stop')
        again, again_reason = label('reattempt_within_5s')
        rows['attempt_fact'].append(dict(season=year,game_id=gid,source_index=index,event_id=event['event_id'],
            period_number=event['period_number'],time_seconds=event['elapsed_seconds'],team_id=str(team) if team is not None else None,
            shooter_id=str(detail['physical_shooter_id']) if detail.get('physical_shooter_id') is not None else None,
            goalie_id=str(detail['opposing_goalie_id']) if detail.get('opposing_goalie_id') is not None else None,
            actual_state=state_record(state) if state is not None else None,outcome=outcome,shot_type=event['shot_type'],
            x_ft=x,y_ft=y,location_kind=location,recorded_stop=stop,recorded_stop_reason=stop_reason,
            recorded_reattempt=again,recorded_reattempt_reason=again_reason,support_id=support_ids['source_supported_attempts'],source=source))
    all_mask = {i for i,s in enumerate(projection['segments']) if s['excluded_reasons']}
    spatial_mask = {r['segment_index'] for r in observed_game_receipt.get('spatial_masks', [])}
    goal_mask = set(all_mask)
    counts = Counter()
    for disposition in observed_game_receipt.get('event_dispositions', []):
        if disposition['status'] != 'included':
            continue
        event = projection['events'][disposition['source_index']]['source']
        target, team = disposition['segment_index'], str(event['shooting_team_id'])
        counts[target,team,'attempts'] += 1
        if event['type_key'] in ('goal','shot-on-goal'):
            counts[target,team,'on_net'] += 1
        if event['type_key'] == 'goal':
            counts[target,team,'goals'] += 1
    # team accounting is deliberately independent of personal attribution.
    for check in observed_game_receipt.get('native_checks', []):
        if check['name'] in ('timed_goals','timed_shots') and check['status'] == 'mismatch':
            goal_mask.update(range(len(projection['segments'])))
    cells = Counter()
    for row in observed_game_receipt.get('spatial_event_dispositions', []):
        if row['status'] == 'included':
            cells[row['segment_index'],row['team_id'],row['cell_id']] += 1
    horizons = {p['period_number']:p['end_seconds'] for p in prepared_game['game']['periods'] or [] if p['status'] == 'supported'}
    for index, segment in enumerate(projection['segments']):
        interval = f"{segment['period_number']}:{segment['start_seconds']}:{segment['end_seconds']}"
        masks = {'recorded_all_attempts':all_mask,'recorded_goals':goal_mask,'recorded_locatable_unblocked':spatial_mask}
        included = [population for population,mask in masks.items() if index not in mask]
        if not included:
            continue
        require(segment['period_number'] in horizons, 'supported observed interval lacks period horizon')
        for side, team, opponent in (('away',away,home),('home',home,away)):
            for pid in segment[side+'_skaters']:
                rows['interval_player'].append(dict(season=year,game_id=gid,interval_id=interval,team_id=team,player_id=str(pid)))
            for population in included:
                kind = 'attempts' if population == 'recorded_all_attempts' else 'goals'
                for_mass = sum(v for (i,t,c),v in cells.items() if i == index and t == team) if population == 'recorded_locatable_unblocked' else counts[index,team,kind]
                against_mass = sum(v for (i,t,c),v in cells.items() if i == index and t == opponent) if population == 'recorded_locatable_unblocked' else counts[index,opponent,kind]
                rows['interval_fact'].append(dict(season=year,game_id=gid,interval_id=interval,team_id=team,population=population,
                    period_number=segment['period_number'],start_seconds=segment['start_seconds'],end_seconds=segment['end_seconds'],
                    period_horizon_seconds=horizons[segment['period_number']],support_id=support_ids[population],
                    for_mass=for_mass,against_mass=against_mass,on_net_for=counts[index,team,'on_net'] if population == 'recorded_goals' else None,
                    on_net_against=counts[index,opponent,'on_net'] if population == 'recorded_goals' else None))
                if population == 'recorded_locatable_unblocked':
                    for cell in sorted({c for i,t,c in cells if i == index}):
                        rows['interval_location'].append(dict(season=year,game_id=gid,interval_id=interval,team_id=team,population=population,
                            cell_id=cell,for_mass=cells[index,team,cell],against_mass=cells[index,opponent,cell]))
    rows.update(projection=projection, dispositions=dispositions, masks=dict(recorded_all_attempts=all_mask,recorded_goals=goal_mask,recorded_locatable_unblocked=spatial_mask))
    return rows


def valued_evidence(prepared_game: PreparedGame, factual_evidence_rows: dict,
                    keyed_scores: Iterable[dict], support_ids: dict[str, str]) -> dict:
    """value saved factual support without reconstructing an observed receipt.

    native intervals supply identity and known exclusions; saved directed rows
    decide the starting population. an unusable attempt removes its whole
    interval from both sides, including its exposure and every other value.
    """
    from .reconstruct import five_on_five_segments
    from .observed_spatial import cell_id

    year, gid = prepared_game['season'], prepared_game['game_id']
    populations = {'neutral_all_attempt_value': 'recorded_all_attempts',
                   'neutral_locatable_unblocked_value': 'recorded_locatable_unblocked'}
    projection = _project_segments(prepared_game, five_on_five_segments(prepared_game['game']['native_intervals']))
    segments = projection['segments']
    identities = projection['actor_identities']
    identity = prepared_game['game']['identity'] or prepared_game['game']['inventory']
    teams = (str(identity['away_team_id']), str(identity['home_team_id']))
    intervals = {f"{s['period_number']}:{s['start_seconds']}:{s['end_seconds']}": i for i,s in enumerate(segments)}
    require(len(intervals) == len(segments), 'duplicate native factual interval')
    members = defaultdict(set)
    for row in factual_evidence_rows.get('interval_player', []):
        require((row['season'],row['game_id']) == (year,gid), 'mixed factual interval membership game')
        members[row['interval_id'],row['team_id']].add(row['player_id'])
    bases = {pop: {} for pop in populations}
    for row in factual_evidence_rows.get('interval_fact', []):
        require((row['season'],row['game_id']) == (year,gid), 'mixed factual interval game')
        index = intervals.get(row['interval_id'])
        require(index is not None, 'factual interval has no native identity')
        segment = segments[index]
        require(all(row[k] == segment[k] for k in ('period_number','start_seconds','end_seconds')),
                'factual/native interval bounds differ')
        require(row['team_id'] in teams, 'factual interval has foreign team')
        side = 'away' if row['team_id'] == teams[0] else 'home'
        require(members[row['interval_id'],row['team_id']] == {str(p) for p in segment[side+'_skaters']},
                'factual/native interval membership differs')
        for pop, base in populations.items():
            if row['population'] == base:
                key = (index,row['team_id'])
                require(key not in bases[pop], 'duplicate factual interval population')
                bases[pop][key] = row
    masks = {pop: defaultdict(set) for pop in populations}
    for pop, rows in bases.items():
        for index in range(len(segments)):
            available = [team for team in teams if (index,team) in rows]
            require(len(available) in (0,2), 'unpaired factual interval population')
            if not available:
                masks[pop][index].add('event_evidence_unresolved')
    ordinary = prepared_game['ordinary_attempt_support']
    prepared_segments = {s['segment_index']: s for s in prepared_game['segments'] or []}
    ordinary_segments = {r['segment_index']: r for r in ordinary['segments'] or []}
    for index, segment in enumerate(segments):
        prepared_index = projection['prepared_segment_indices'][index]
        checked = ordinary_segments.get(prepared_index)
        if checked is None or checked['disposition'] != 'included':
            codes = {ordinary['reasons'][i]['code'] for i in checked['reason_indices']} if checked else {'source_unavailable'}
            for pop in populations:
                masks[pop][index].update(codes or {'event_evidence_unresolved'})
    source = {}
    for row in factual_evidence_rows.get('attempt_fact', []):
        require((row['season'],row['game_id']) == (year,gid), 'mixed factual attempt game')
        require(row['source_index'] not in source, 'duplicate factual source index')
        source[row['source_index']] = row
    scores = {}
    for row in keyed_scores.values() if isinstance(keyed_scores, dict) else keyed_scores:
        require((row['season'],row['game_id']) == (year,gid), 'mixed scored attempt game')
        require(row['source_index'] not in scores, 'duplicate numerical source index')
        scores[row['source_index']] = row
    attempts = {r['source_index']: r for r in prepared_game['attempts'] or []}
    assignments = {r['source_index']: r for r in ordinary['events'] or []}
    candidates, dispositions = [], []
    for source_index, row in sorted(source.items()):
        record = projection['events'].get(source_index)
        require(record is not None, 'factual source event missing from preparation')
        event = record['source']
        require((row['period_number'],row['time_seconds']) == (event['period_number'],event['elapsed_seconds'])
                and row['outcome'] == {'goal':'goal','shot-on-goal':'save','missed-shot':'miss','blocked-shot':'block'}.get(event['type_key']),
                'factual source event differs from preparation')
        association = projection['associations'].get(source_index)
        native = association['native'] if association else None
        native_ids = set(native['interval_indices']) if native is not None else set()
        targets = [i for i,s in enumerate(segments) if native_ids.intersection(s['interval_indices'])]
        assignment = assignments.get(source_index)
        matched = (assignment is not None and assignment['disposition'] == 'included'
                   and assignment['segment_index'] in prepared_segments and len(targets) == 1
                   and projection['prepared_segment_indices'][targets[0]] == assignment['segment_index'])
        if not matched:
            # a positively assigned other-strength event does not erase adjacent
            # five-on-five time. unknown assignment follows the located owner.
            targets = [] if native is not None and native['classification'] == 'other' else _locate(
                event, [dict(s,segment_index=i) for i,s in enumerate(segments)])
        score = scores.get(source_index)
        detail = attempts.get(source_index, {}).get('details', {}).get('values', {})
        reason = None
        if not matched:
            reason = 'ambiguous_assignment'
        elif detail.get('physical_status') != 'ordinary':
            reason = 'physical_attempt_unavailable'
        elif score is None or score['status'] != 'complete':
            reason = 'model_value_unavailable'
        else:
            team = event['shooting_team_id']
            role = 'scorer' if event['type_key'] == 'goal' else 'shooter'
            segment = segments[targets[0]]
            member_map = {int(t): segment[side+'_skaters'] + segment[side+'_goalies']
                          for side,t in zip(('away','home'),teams)}
            issue = actor_issue(event, identities, {role:team}, member_map)
            shooter = detail.get('physical_shooter_id')
            if (issue is not None or team not in member_map or detail.get('shooting_team_id') != team
                    or event.get('owner_team_id') is not None and event['owner_team_id'] != team
                    or shooter != event['roles'].get(role) or row['shooter_id'] != str(shooter)
                    or row['team_id'] != str(team) or str(score['shooter_id']) != str(shooter)):
                reason = issue or 'physical_shooter_conflict'
        applicable = list(populations) if row['outcome'] != 'block' else ['neutral_all_attempt_value']
        if reason is None:
            value = score['prefixes']['neutral']['uqrg']
            require(type(value) in (int,float) and math.isfinite(value) and 0 <= value <= 1,
                    'invalid neutral all-attempt opportunity')
            candidates.append(dict(source_index=source_index,interval_index=targets[0],player_id=str(shooter),
                                   team_id=str(team),opportunity=value,source=row))
        else:
            for pop in applicable:
                for index in targets:
                    masks[pop][index].add('value_unavailable' if reason == 'model_value_unavailable' else
                                          'ambiguous_assignment' if reason == 'ambiguous_assignment' else 'identity_conflict')
        dispositions.append(dict(source_index=source_index,status='eligible' if reason is None else 'excluded',
                                 reason=reason,model_reasons=score.get('reasons',[]) if score else [],
                                 affected_interval_ids=[next(k for k,v in intervals.items() if v==i) for i in targets]))
        if reason is None and identities[shooter]['reported_position'] == 'G':
            dispositions[-1].update(personal_status='not_applicable',personal_reason='personal_shooter_not_skater')
    masses, cells = defaultdict(list), defaultdict(list)
    personal = []
    for candidate in candidates:
        index, team, value = candidate['interval_index'],candidate['team_id'],candidate['opportunity']
        row = candidate['source']
        if index not in masks['neutral_all_attempt_value']:
            if identities[int(candidate['player_id'])]['reported_position'] != 'G':
                personal.append(dict({k:v for k,v in candidate.items() if k != 'source'},
                                     inferred_inputs=['blocked_origin','setter'] if row['outcome'] == 'block' else ['setter']))
            masses['neutral_all_attempt_value',index,team].append(value)
        if row['outcome'] != 'block' and index not in masks['neutral_locatable_unblocked_value']:
            require(row['location_kind'] == 'reported_event' and row['x_ft'] is not None and row['y_ft'] is not None,
                    'locatable factual population lacks recorded unblocked location')
            masses['neutral_locatable_unblocked_value',index,team].append(value)
            cells[index,team,cell_id(row['x_ft'],row['y_ft'])].append(value)
    facts, locations = [], []
    recorded_cells = {(r['interval_id'],r['team_id'],r['cell_id']):r for r in factual_evidence_rows.get('interval_location', [])
                      if r['population'] == 'recorded_locatable_unblocked'}
    for pop, rows in bases.items():
        for (index,team), row in sorted(rows.items()):
            if index in masks[pop]:
                continue
            opponent = teams[1] if team == teams[0] else teams[0]
            require(len(masses[pop,index,team]) == row['for_mass'] and len(masses[pop,index,opponent]) == row['against_mass'],
                    f"{gid}:{row['interval_id']}:{team}:{pop}: valued/recorded attempt count differs")
            facts.append(dict(row,population=pop,support_id=support_ids[pop],
                              for_mass=math.fsum(masses[pop,index,team]),against_mass=math.fsum(masses[pop,index,opponent]),
                              on_net_for=None,on_net_against=None))
            if pop == 'neutral_locatable_unblocked_value':
                cell_ids = {c for i,t,c in cells if i == index} | {c for interval,t,c in recorded_cells if interval == row['interval_id']}
                for cell in sorted(cell_ids):
                    old = recorded_cells.get((row['interval_id'],team,cell),{})
                    require(len(cells[index,team,cell]) == old.get('for_mass',0) and len(cells[index,opponent,cell]) == old.get('against_mass',0),
                            f"{gid}:{row['interval_id']}:{team}:{cell}: valued/recorded cell count differs")
                    locations.append(dict(season=year,game_id=gid,interval_id=row['interval_id'],team_id=team,population=pop,
                        cell_id=cell,for_mass=math.fsum(cells[index,team,cell]),against_mass=math.fsum(cells[index,opponent,cell])))
    baseline = {(r['player_id'],r['population']):r for r in factual_evidence_rows.get('context_coverage', [])}
    coverage = []
    gap = (prepared_game['game']['native_intervals'] is None or prepared_game['game']['periods'] is None
           or any(r['status'] != 'supported' for r in prepared_game['game']['periods'] or [])
           or any(r['classification'] == 'unresolved' for r in prepared_game['game']['native_intervals'] or []))
    dressed = factual_evidence_rows.get('dressed_game', [])
    for person in dressed:
        pid = person['player_id']
        actor = identities.get(int(pid))
        if actor is None or actor['reported_position'] not in ('C','L','R','D','F'):
            continue
        for pop, base in populations.items():
            excluded, reasons = 0, Counter()
            for index,codes in masks[pop].items():
                segment = segments[index]
                if int(pid) in segment['away_skaters'] + segment['home_skaters']:
                    excluded += segment['end_seconds'] - segment['start_seconds']
                    reasons.update(codes)
            old = baseline.get((pid,base), {})
            coverage.append(dict(season=year,player_id=pid,population=pop,availability='provided',explanation=None,
                known_excluded_seconds=excluded,unquantified_gap=gap or old.get('unquantified_gap',False),
                reason_counts=[dict(code=k,count=v) for k,v in sorted(reasons.items())],
                source_ids=old.get('source_ids',[]),method_ids=[]))
    return dict(season=year,game_id=gid,interval_fact=facts,interval_location=locations,
                interval_player=factual_evidence_rows.get('interval_player',[]),dressed_game=dressed,
                context_coverage=coverage,personal=personal,dispositions=dispositions,
                reconciliation=dict(intersection=sorted(source.keys() & scores.keys()),
                    source_only=sorted(source.keys() - scores.keys()),numerical_only=sorted(scores.keys() - source.keys())))


def _reported(person):
    rows = person['boxscore']
    # repeated identical dated rows still describe one player-game-team.
    if rows and all(row == rows[0] for row in rows):
        rows = rows[:1]
    if len(rows) != 1:
        return dict(seconds=None, shifts=None)
    return dict(seconds=rows[0]['toi_seconds'], shifts=rows[0]['shift_count'])


def _locate(event, segments):
    period = event['period_number'] if event['period_number'] in (1,2,3,4) else None
    clock = event['elapsed_seconds'] if event['timed_period'] is True else None
    return [row['segment_index'] for row in segments if (period is None or row['period_number'] == period)
            and (clock is None or row['start_seconds'] <= clock <= row['end_seconds'])]


def reduce_game(prepared_game: PreparedGame, observed_game: list[PlayerGame],
                recorded: RecordedEvidence) -> GameReduction:
    """reduce each family on its own support; no family erases another's time."""
    year, gid = prepared_game['season'], prepared_game['game_id']
    identity = prepared_game['game']['identity'] or prepared_game['game']['inventory']
    teams = (str(identity['away_team_id']), str(identity['home_team_id']))
    dressed = recorded['projection']['dressed_teams']
    people = {}
    for pid,team in dressed.items():
        people[pid] = dict(team_id=team,reported=_reported(prepared_game['people'][pid]),
            usage=Counter(),scoring={},unclassified=Counter(),starts=Counter(),score=Counter(),
            penalties={},context={},issues=[],scoring_excluded=Counter(),scoring_reasons=defaultdict(list))
    segments = prepared_game['segments'] or []
    valid_segments = {s['segment_index'] for s in segments if _valid_membership(
        s,teams,dressed,recorded['projection']['actor_identities'],prepared_game['people'] or {})}
    elapsed_available = bool(valid_segments) and bool(prepared_game['game']['periods'])
    # strength usage is elapsed membership, independent of ordinary attempts.
    for segment in segments:
        if segment['segment_index'] not in valid_segments:
            continue
        duration = segment['end_seconds'] - segment['start_seconds']
        for side in ('away','home'):
            state = state_tuple(segment['membership'], side)
            if state is None:
                continue
            for raw_pid in segment['membership'][side+'_skaters']:
                pid = str(raw_pid)
                if pid in people:
                    people[pid]['usage'][state] += duration
    support_rows = prepared_game['ordinary_attempt_support']
    ordinary = {row['segment_index'] for row in support_rows['segments'] or [] if row['disposition'] == 'included'}
    assignments = {row['source_index']:row for row in support_rows['events'] or []}
    events = recorded['projection']['events']
    credits = {row['source_index']:row for row in prepared_game['credits'] or []}
    outside_credits = {r['source_index'] for r in recorded['dispositions'] if r['reason'] == 'penalty_shot'}
    credit_mask = set()
    credit_issues = []
    for index, credit in credits.items():
        event = events[index]['source']
        if event['type_key'] not in ('goal','shot-on-goal') or index in outside_credits or event['timed_period'] is False:
            continue
        assignment = assignments.get(index)
        role = 'scorer' if event['type_key'] == 'goal' else 'shooter'
        roles = {role:event['shooting_team_id']}
        if credit['primary_assister_id'] is not None:
            roles['assist1'] = event['shooting_team_id']
        issue = actor_issue(event, recorded['projection']['actor_identities'], roles)
        if credit['status'] == 'unresolved' or issue is not None:
            targets = ([assignment['segment_index']] if assignment and assignment['segment_index'] is not None
                       else _locate(event, segments))
            if assignment and assignment['disposition'] == 'not_applicable':
                continue
            credit_mask.update(targets)
            credit_issues.append(dict(source_index=index,reason=issue or credit['reason'],affected_segment_indices=targets))
    good = ordinary - credit_mask
    scoring_available = bool(good & valid_segments) and prepared_game['events'] is not None
    ordinary_rows = {r['segment_index']:r for r in support_rows['segments'] or []}
    for segment in segments:
        index = segment['segment_index']
        if index not in valid_segments:
            continue
        duration = segment['end_seconds'] - segment['start_seconds']
        for side in ('away','home'):
            state = state_tuple(segment['membership'], side)
            if state == _FIVE or state is None:
                continue
            for raw_pid in segment['membership'][side+'_skaters']:
                pid = str(raw_pid)
                if pid not in people:
                    continue
                person = people[pid]
                if index in good:
                    person['scoring'].setdefault(state, Counter())['seconds'] += duration
                else:
                    person['scoring_excluded'][state] += duration
                    row = ordinary_rows.get(index)
                    codes = [support_rows['reasons'][i]['code'] for i in row['reason_indices']] if row else ['source_unavailable']
                    if index in credit_mask:
                        codes.append('personal_credit_unresolved')
                    person['scoring_reasons'][state].extend(codes or ['event_evidence_unresolved'])
    invalid_credits = {r['source_index'] for r in credit_issues}
    for index, credit in credits.items():
        event = events[index]['source']
        if index in invalid_credits:
            continue
        if event['type_key'] != 'goal' or credit['status'] != 'credited' or index in outside_credits or event['timed_period'] is False:
            continue
        assignment = assignments.get(index)
        association = recorded['projection']['associations'].get(index)
        native = association['native'] if association else None
        if native is None or event['shooting_team_id'] not in (int(teams[0]),int(teams[1])):
            state = None
        else:
            state = state_tuple({k:native[k] for k in _MEMBERS}, 'away' if str(event['shooting_team_id']) == teams[0] else 'home')
        if state == _FIVE:
            continue
        for field, key in (('scorer_or_shooter_id','goals'),('primary_assister_id','assists')):
            raw_pid = credit[field]
            if raw_pid is None or str(raw_pid) not in people:
                continue
            person = people[str(raw_pid)]
            if state is None:
                person['unclassified'][key] += 1
            elif assignment and assignment['disposition'] == 'included' and assignment['segment_index'] in good:
                person['scoring'].setdefault(state, Counter())[key] += 1
            else:
                person['issues'].append(dict(source_index=index,state=state_record(state),reason='credit_without_matched_elapsed_support',role=key))
    old_by_pid = {row.player_id:row for row in observed_game}
    for pid, person in people.items():
        old = old_by_pid.get(pid)
        person['old'] = old
        person['elapsed_available'] = elapsed_available
        person['starts_available'] = elapsed_available and prepared_game['player_shifts'] is not None
        person['score_available'] = elapsed_available and prepared_game['chunks'] is not None
        person['scoring_available'] = scoring_available
    # the original coalesced shift start must lie within a supported
    # five-on-five segment; a later strength transition cannot create a start.
    five_segments = [s for s in segments if s['segment_index'] in valid_segments and state_tuple(s['membership']) == _FIVE]
    for shift in prepared_game['player_shifts'] or []:
        pid = str(shift['player_id'])
        if pid not in people:
            continue
        eligible = [s for s in five_segments if s['period_number'] == shift['period_number']
                    and s['start_seconds'] <= shift['start_seconds'] < s['end_seconds']
                    and shift['player_id'] in s['membership']['away_skaters'] + s['membership']['home_skaters']]
        if not eligible:
            continue
        value = shift['start']['values']
        key = value['zone'] if value['kind'] == 'faceoff' and value['zone'] is not None else 'on_the_fly' if value['kind'] == 'on_the_fly' else 'unknown'
        people[pid]['starts'][key] += 1
    for chunk in prepared_game['chunks'] or []:
        segment = segments[chunk['segment_index']]
        if segment['segment_index'] not in valid_segments or state_tuple(segment['membership']) != _FIVE:
            continue
        duration = chunk['end_seconds'] - chunk['start_seconds']
        score = chunk['score']['values']
        for side in ('away','home'):
            own, against = score[side], score['home' if side == 'away' else 'away']
            key = 'unknown' if own is None or against is None else 'leading' if own > against else 'trailing' if own < against else 'tied'
            for raw_pid in segment['membership'][side+'_skaters']:
                if str(raw_pid) in people:
                    people[str(raw_pid)]['score'][key] += duration
    penalty_roles = {'taken':'penalty_committed_by','drawn':'penalty_drawn_by','served':'penalty_served_by'}
    invalid = {role:set() for role in penalty_roles}
    ledger = []
    usable = prepared_game['events'] is not None and all(e['source']['kind_valid'] for e in prepared_game['events'] or [])
    for pid, person in people.items():
        person['penalties'] = {role:dict(count=0,categories=Counter(),eligible=usable) for role in penalty_roles}
    for index, record in events.items():
        event = record['source']
        if event['type_key'] != 'penalty' or not event['kind_valid']:
            continue
        team = str(event['owner_team_id']) if event['owner_team_id'] is not None else None
        opponent = teams[1] if team == teams[0] else teams[0] if team == teams[1] else None
        receipt = dict(source_index=index,type=event['penalty_type'],description=event['penalty_description'],duration_minutes=event['penalty_duration_minutes'],roles={})
        for role,key in penalty_roles.items():
            expected = opponent if role == 'drawn' else team
            pid = event['roles'].get(key)
            bench = role == 'taken' and key not in event['roles'] and event['penalty_type'] == 'BEN'
            if key not in event['roles'] and (role in ('drawn','served') or bench):
                disposition = 'not_recorded'
            elif pid is not None and str(pid) in dressed and dressed[str(pid)] == expected:
                disposition = 'attributed'
                target = people[str(pid)]['penalties'][role]
                target['count'] += 1
                target['categories'][event['penalty_type'] or 'type_unavailable'] += 1
            else:
                disposition = 'unresolved'
                invalid[role].update((expected,) if expected in teams else teams)
            receipt['roles'][role] = dict(player_id=pid,disposition=disposition)
        ledger.append(receipt)
    for person in people.values():
        for role in penalty_roles:
            if person['team_id'] in invalid[role]:
                person['penalties'][role]['eligible'] = False
    # focal on/off and dressed-team references use the same directed rows sent
    # to the api. league sums each physical team side once.
    members = defaultdict(set)
    for row in recorded['interval_player']:
        members[row['interval_id'],row['team_id']].add(row['player_id'])
    physical = {pop:Counter() for pop in CONTEXT_POPULATIONS[:3]}
    team_physical = {(team,pop):Counter() for team in teams for pop in CONTEXT_POPULATIONS[:3]}
    for row in recorded['interval_fact']:
        pop,team = row['population'],row['team_id']
        masses = Counter(seconds=row['end_seconds']-row['start_seconds'],for_count=row['for_mass'],against_count=row['against_mass'])
        if pop == 'recorded_goals':
            masses.update(on_net_for=row['on_net_for'],on_net_against=row['on_net_against'])
        physical[pop].update(masses)
        team_physical[team,pop].update(masses)
        for pid,person in people.items():
            if person['team_id'] != team:
                continue
            which = 'on' if pid in members[row['interval_id'],team] else 'off'
            person['context'].setdefault((pop,which), Counter()).update(masses)
    for pid,person in people.items():
        for pop in CONTEXT_POPULATIONS[:3]:
            person['context'][pop,'team'] = team_physical[person['team_id'],pop]
        person['coverage'] = {}
        for pop,mask in recorded['masks'].items():
            excluded = sum(s['end_seconds']-s['start_seconds'] for i,s in enumerate(recorded['projection']['segments'])
                           if i in mask and int(pid) in s['away_skaters']+s['home_skaters'])
            old = person['old']
            reasons = list(old.spatial.reason_codes if pop == 'recorded_locatable_unblocked' else old.reason_codes) if old else ['unassigned_player_games']
            gap = not elapsed_available or old is None or bool(set(reasons) & {'required_source_unavailable','elapsed_membership_unresolved','period_horizon_unavailable','unassigned_player_games','roster_identity_unresolved','shift_source_empty'})
            team_excluded = sum(s['end_seconds']-s['start_seconds'] for i,s in enumerate(recorded['projection']['segments']) if i in mask)
            person['coverage'][pop] = dict(excluded=excluded,excluded_off=team_excluded-excluded,excluded_team=team_excluded,gap=gap,reasons=reasons)
    return dict(season=year,game_id=gid,people=people,physical=physical,teams=teams,
                penalty_ledger=ledger,credit_issues=credit_issues,dispositions=recorded['dispositions'],
                deployment_gap=not elapsed_available or prepared_game['chunks'] is None or prepared_game['player_shifts'] is None or any(r['classification'] == 'unresolved' for r in prepared_game['game']['native_intervals'] or []))


def _usage(rows, *, team_id=None):
    known = [r['seconds'] for r in rows if r['seconds'] is not None]
    appearances = sum(s > 0 for s in known)
    shifts = [r['shifts'] for r in rows]
    reasons = ['required_source_unavailable'] * (len(rows)-len(known))
    reasons += ['reported_shifts_unavailable'] * sum(s is None for s in shifts)
    seconds = sum(known) if known else None
    result = dict(positive_toi_appearances=appearances,reported_seconds=seconds,
        minutes_per_appearance=estimate(seconds/(60*appearances) if seconds is not None and appearances else None),
        reported_shifts=sum(shifts) if rows and all(s is not None for s in shifts) else None,
        listed_games=len(rows),supported_games=len(known),missing_games=len(rows)-len(known),
        support=support(seconds,gap=len(known)!=len(rows),reasons=reasons))
    if team_id is not None:
        result['team_id'] = team_id
    return result


def _scoring(counts, seconds, *, excluded=0, reasons=(), gap=False):
    goals, assists = counts
    points = goals+assists if goals is not None and assists is not None else None
    return dict(goals=goals,primary_assists=assists,primary_points=points,seconds=seconds,
                goals_per60=estimate(3600*goals/seconds if seconds and goals is not None else None),
                primary_assists_per60=estimate(3600*assists/seconds if seconds and assists is not None else None),
                primary_points_per60=estimate(3600*points/seconds if seconds and points is not None else None),
                support=support(seconds,excluded=excluded,gap=gap,reasons=reasons))


def _context(masses, coverage=None, *, goals=False):
    seconds = masses['seconds']
    unknown = not seconds and (coverage or {}).get('gap',False)
    result = dict(for_count=None if unknown else masses['for_count'],against_count=None if unknown else masses['against_count'],seconds=seconds,
        for_per60=estimate(3600*masses['for_count']/seconds if seconds else None),
        against_per60=estimate(3600*masses['against_count']/seconds if seconds else None),
        share_minus_half=estimate(100*(masses['for_count']/(masses['for_count']+masses['against_count'])-.5)
                                 if masses['for_count']+masses['against_count'] else None),
        support=support(seconds,excluded=(coverage or {}).get('excluded',0),gap=(coverage or {}).get('gap',False),reasons=(coverage or {}).get('reasons',())))
    if goals:
        result.update(on_net_for=None if unknown else masses['on_net_for'],on_net_against=None if unknown else masses['on_net_against'])
    return result


def _conversion(masses, coverage=None):
    goals_for,goals_against,on_net_for,on_net_against = (masses[k] for k in ('for_count','against_count','on_net_for','on_net_against'))
    unknown = not masses['seconds'] and (coverage or {}).get('gap',False)
    return dict(goals_for=None if unknown else goals_for,goals_against=None if unknown else goals_against,
                on_net_for=None if unknown else on_net_for,on_net_against=None if unknown else on_net_against,
                shooting_for=estimate(goals_for/on_net_for if on_net_for else None),
                shooting_against=estimate(goals_against/on_net_against if on_net_against else None),
                save_fraction=estimate(1-goals_against/on_net_against if on_net_against else None),
                support=support(masses['seconds'],excluded=(coverage or {}).get('excluded',0),gap=(coverage or {}).get('gap',False),reasons=(coverage or {}).get('reasons',())))


def _penalty_summary(rows, *, gap=False):
    eligible = [row for row in rows if row['eligible'] and row['seconds'] is not None and row['seconds'] > 0]
    seconds = sum(row['seconds'] for row in eligible)
    categories = Counter()
    for row in eligible:
        categories.update(row['categories'])
    count = sum(row['count'] for row in eligible) if eligible else None
    return dict(count=count,reported_seconds=seconds if eligible else None,
                per1000minutes=estimate(60000*count/seconds if seconds and count is not None else None),
                categories=[dict(code=k,count=v) for k,v in sorted(categories.items())],
                support=support(seconds if eligible else None,events=count,gap=gap or len(eligible)!=len(rows),
                                reasons=['event_evidence_unresolved'] * sum(not r['eligible'] for r in rows)
                                + ['required_source_unavailable'] * sum(r['seconds'] is None for r in rows)))


def _deployment(starts, score, gap=False, *, starts_available=True,score_available=True):
    start_total = sum(starts.values())
    known = sum(score[k] for k in ('leading','tied','trailing'))
    all_seconds = known + score['unknown']
    return dict(shift_starts={k:dict(count=starts[k] if starts_available else None,share=estimate(starts[k]/start_total if start_total else None))
                             for k in ('offensive','neutral','defensive','on_the_fly','unknown')},
                score={k:dict(seconds=score[k] if score_available else None,share=estimate(score[k]/(all_seconds if k == 'unknown' else known)
                                                           if (all_seconds if k == 'unknown' else known) else None))
                       for k in ('leading','tied','trailing','unknown')},support=support(all_seconds,gap=gap))


def _counterparts(pid, pairs, usage, positions, bands, focal: Metrics | None):
    result = {}
    focal_gap = focal is None or bool(set(focal.reason_codes) & {
        'required_source_unavailable','elapsed_membership_unresolved','period_horizon_unavailable',
        'roster_identity_unresolved','unassigned_player_games','shift_source_empty','player_toi_conflict',
    })
    for relation,key in (('teammate','teammates'),('opponent','opponents')):
        weights = Counter()
        for row in pairs:
            if row.relation == relation and pid in (row.player_a,row.player_b):
                weights[row.player_b if row.player_a == pid else row.player_a] += row.shared_seconds
        def group(role=None):
            selected = {p:s for p,s in weights.items() if role is None or positions.get(p) == role}
            known = {p:s for p,s in selected.items() if usage.get(p) is not None and (role is None or p in bands)}
            all_seconds, known_seconds = sum(selected.values()),sum(known.values())
            weight_gap = known_seconds != all_seconds or any(positions.get(p) is None for p in weights)
            reasons = list(focal.reason_codes) if focal is not None else ['source_unavailable']
            if weight_gap:
                reasons.append('context_unavailable')
            coverage = support(focal.included_seconds if focal is not None else None,
                               excluded=focal.known_excluded_seconds if focal is not None else None,
                               gap=focal_gap or weight_gap,reasons=reasons)
            row = dict(usage_minutes_per_appearance=estimate(sum(s*usage[p] for p,s in known.items())/known_seconds if known_seconds else None),
                known_slot_seconds=known_seconds,all_slot_seconds=all_seconds,unique_counterparts=len(selected),
                coverage=coverage)
            if role is not None:
                n = 4 if role == 'F' else 3
                row['bands'] = [dict(band=i,counterparts=sum(bands[p] == i for p in known),slot_seconds=sum(s for p,s in known.items() if bands[p] == i)) for i in range(1,n+1)]
                row['mean_band_index'] = estimate(sum(s*bands[p] for p,s in known.items())/known_seconds if known_seconds else None)
            return row
        row = group()
        row.update(forward=group('F'),defense=group('D'))
        result[key] = row
    return result


def summarize_season(people: list[PersonIdentity], game_reductions: Iterable[GameReduction],
                     observed_result: ObservedResult, source_ids: SourceIds) -> SeasonSummary:
    """compact season accumulation; retain separate physical and player units."""
    source_id = source_ids['facts']
    people_by_id = {p['player_id']:p for p in people if p['kind'] == 'skater'}
    accumulated = {}
    for pid in people_by_id:
        accumulated[pid] = dict(reported=[],team_reported=defaultdict(list),usage=Counter(),usage_games=Counter(),
            scoring={},scoring_excluded=Counter(),scoring_reasons=defaultdict(list),unclassified=Counter(),starts=Counter(),score=Counter(),context=defaultdict(Counter),
            coverage={pop:dict(excluded=0,excluded_off=0,excluded_team=0,gap=False,reasons=[]) for pop in CONTEXT_POPULATIONS[:3]},
            penalties={scope:{role:[] for role in ('drawn','taken','served')} for scope in ('focal','team')},
            team_starts=Counter(),team_score=Counter(),gap=False,elapsed_available=False,starts_available=False,score_available=False,scoring_available=False,team_starts_available=False,team_score_available=False)
    league_context = defaultdict(Counter)
    league_coverage = {}
    for population in CONTEXT_POPULATIONS[:3]:
        spatial = population == 'recorded_locatable_unblocked'
        reasons = [code for game in observed_result.games for code in (game.spatial_reason_codes if spatial else game.reason_codes)]
        league_coverage[population] = dict(excluded=2*sum(game.spatial_known_excluded_seconds if spatial else game.known_excluded_seconds for game in observed_result.games),
            gap=any(game.horizon_unavailable or game.known_unresolved_seconds > 0 for game in observed_result.games),reasons=reasons)
    league_deployment_gap = False
    league_starts_available = league_score_available = False
    league_penalty_gap = any('required_source_unavailable' in game.reason_codes for game in observed_result.games)
    league_starts, league_score = Counter(),Counter()
    league_penalties = {role:[] for role in ('drawn','taken','served')}
    team_ids = {team for g in observed_result.games for team in (g.away_team_id,g.home_team_id)}
    for game in game_reductions:
        team_ids.update(game['teams'])
        league_deployment_gap |= game['deployment_gap']
        for pop,masses in game['physical'].items():
            league_context[pop].update(masses)
        team_starts,team_score = defaultdict(Counter),defaultdict(Counter)
        team_penalties = {team:{role:[] for role in league_penalties} for team in game['teams']}
        for pid,person in game['people'].items():
            if pid not in people_by_id:
                continue
            team = person['team_id']
            league_starts_available |= person['starts_available']
            league_score_available |= person['score_available']
            team_starts[team].update(person['starts'])
            team_score[team].update(person['score'])
            for role, row in person['penalties'].items():
                value = dict(row,seconds=person['reported']['seconds'])
                team_penalties[team][role].append(value)
                league_penalties[role].append(value)
        for team in game['teams']:
            league_starts.update(team_starts[team])
            league_score.update(team_score[team])
        for pid, person in game['people'].items():
            if pid not in accumulated:
                continue
            acc = accumulated[pid]
            acc['elapsed_available'] |= person['elapsed_available']
            acc['team_starts_available'] |= any(p['team_id'] == person['team_id'] and p['starts_available'] for p in game['people'].values())
            acc['team_score_available'] |= any(p['team_id'] == person['team_id'] and p['score_available'] for p in game['people'].values())
            acc['starts_available'] |= person['starts_available']
            acc['score_available'] |= person['score_available']
            acc['scoring_available'] |= person['scoring_available']
            acc['reported'].append(person['reported'])
            acc['team_reported'][person['team_id']].append(person['reported'])
            acc['usage'].update(person['usage'])
            acc['usage_games'].update(state for state,s in person['usage'].items() if s > 0)
            # group appearances count games, not exact-state appearances.
            for group in _GROUPS:
                seconds = sum(s for state,s in person['usage'].items() if state == _FIVE if group == 'five_on_five') if group == 'five_on_five' else sum(s for state,s in person['usage'].items() if strength_group(state) == group)
                if seconds:
                    acc['usage_games'][group] += 1
            for state,counts in person['scoring'].items():
                acc['scoring'].setdefault(state,Counter()).update(counts)
            acc['scoring_excluded'].update(person['scoring_excluded'])
            for state,reasons in person['scoring_reasons'].items():
                acc['scoring_reasons'][state].extend(reasons)
            acc['unclassified'].update(person['unclassified'])
            acc['starts'].update(person['starts'])
            acc['score'].update(person['score'])
            acc['team_starts'].update(team_starts[person['team_id']])
            acc['team_score'].update(team_score[person['team_id']])
            for selector,masses in person['context'].items():
                acc['context'][selector].update(masses)
            for pop,row in person['coverage'].items():
                for key in ('excluded','excluded_off','excluded_team'):
                    acc['coverage'][pop][key] += row[key]
                acc['coverage'][pop]['gap'] |= row['gap']
                acc['coverage'][pop]['reasons'].extend(row['reasons'])
                acc['gap'] |= row['gap']
            for role,row in person['penalties'].items():
                acc['penalties']['focal'][role].append(dict(row,seconds=person['reported']['seconds']))
                acc['penalties']['team'][role].extend(team_penalties[person['team_id']][role])
    usage_by_id = {pid:_usage(acc['reported']) for pid,acc in accumulated.items()}
    usage_means = {pid:row['minutes_per_appearance']['value'] for pid,row in usage_by_id.items()}
    positions = {pid:'D' if p['reported_position'] == 'D' else 'F' if p['reported_position'] in ('C','L','R','F') else None for pid,p in people_by_id.items()}
    bands = {}
    count_teams = len(team_ids)
    for role in ('F','D'):
        ordered = sorted((p for p in usage_means if positions[p] == role and usage_means[p] is not None),key=lambda p:(-usage_means[p],int(p)))
        width, maximum = (3*count_teams,4) if role == 'F' else (2*count_teams,3)
        for rank,pid in enumerate(ordered):
            bands[pid] = min(maximum,rank//width+1) if width else maximum
    old = {row.player_id:row for row in observed_result.player_seasons}
    descriptive, contexts, coverage_rows = [],[],[]
    year = observed_result.season
    for pid,acc in sorted(accumulated.items()):
        reported = usage_by_id[pid]
        reported.update(teams=[_usage(rows,team_id=team) for team,rows in sorted(acc['team_reported'].items())],provenance=dict(kind='source',id=source_id))
        states = set(acc['usage']) | set(acc['scoring']) | set(acc['scoring_excluded']) | {_FIVE}
        strength = {}
        for state in sorted(states):
            seconds = acc['usage'][state] if acc['elapsed_available'] else None
            appearances = acc['usage_games'][state]
            strength[state] = dict(seconds=seconds,appearances=appearances,minutes_per_appearance=estimate(seconds/(60*appearances) if seconds is not None and appearances else None),support=support(seconds,gap=acc['gap']))
        strength_usage = {group:dict(seconds=sum(v['seconds'] for s,v in strength.items() if (s == _FIVE if group == 'five_on_five' else strength_group(s) == group)) if acc['elapsed_available'] else None,
                                    appearances=acc['usage_games'][group]) for group in _GROUPS}
        for row in strength_usage.values():
            row.update(minutes_per_appearance=estimate(row['seconds']/(60*row['appearances']) if row['seconds'] is not None and row['appearances'] else None),support=support(row['seconds'],gap=acc['gap']))
        strength_usage['states'] = [dict(row,state=state_record(state)) for state,row in sorted(strength.items())]
        scoring = {}
        for state in states:
            row = acc['scoring'].get(state,Counter())
            unknown = not row['seconds'] and not row['goals'] and not row['assists'] and (acc['scoring_excluded'][state] > 0 or not acc['scoring_available'])
            scoring[state] = _scoring((None,None) if unknown else (row['goals'],row['assists']),
                row['seconds'] if acc['scoring_available'] else None,excluded=acc['scoring_excluded'][state],
                reasons=acc['scoring_reasons'][state],gap=acc['gap'] or unknown)
        personal = old[pid].personal if pid in old else None
        scoring[_FIVE] = _scoring((personal.goals,personal.primary_assists),personal.included_seconds,
                                 excluded=personal.known_excluded_seconds,reasons=personal.reason_codes,gap=bool(set(personal.reason_codes) & {'required_source_unavailable','elapsed_membership_unresolved','period_horizon_unavailable','unassigned_player_games','roster_identity_unresolved','shift_source_empty'})) if personal else _scoring((None,None),None,gap=True,reasons=['unassigned_player_games'])
        scoring_by_strength = {'five_on_five':scoring[_FIVE]}
        for group in ('ev','pp','pk','other'):
            members = [row for state,row in scoring.items() if strength_group(state) == group]
            known_members = [r for r in members if r['goals'] is not None and r['primary_assists'] is not None and r['seconds'] is not None]
            checked_empty = not members and acc['scoring_available'] and acc['elapsed_available']
            counts = tuple(sum(r[key] for r in known_members) if known_members or checked_empty else None for key in ('goals','primary_assists'))
            seconds = sum(r['seconds'] for r in known_members) if known_members or checked_empty else None
            if not acc['scoring_available'] and group != 'ev':
                counts,seconds = (None,None),None
            scoring_by_strength[group] = _scoring(counts,seconds,gap=acc['gap'] or len(known_members)!=len(members),excluded=sum(r['support']['known_excluded_seconds'] for r in members),
                                                   reasons=[q['code'] for r in members for q in r['support']['reason_counts']])
        scoring_by_strength['states'] = [dict(row,state=state_record(state)) for state,row in sorted(scoring.items())]
        g,a = acc['unclassified']['goals'],acc['unclassified']['assists']
        unclassified_known = acc['scoring_available'] or g > 0 or a > 0
        scoring_by_strength['unclassified'] = dict(goals=g if unclassified_known else None,primary_assists=a if unclassified_known else None,primary_points=g+a if unclassified_known else None,support=support(None,gap=acc['gap'] or not unclassified_known))
        on_off = {}
        for pop in ('recorded_all_attempts','recorded_goals'):
            on_off[pop] = {scope:_context(league_context[pop] if scope == 'league' else acc['context'][pop,scope],league_coverage[pop] if scope == 'league' else dict(acc['coverage'][pop],excluded=acc['coverage'][pop]['excluded_off' if scope == 'off' else 'excluded']),goals=pop == 'recorded_goals') for scope in ('on','off','league')}
        conversion = {scope:_conversion(league_context['recorded_goals'] if scope == 'league' else acc['context']['recorded_goals','on' if scope == 'focal' else 'team'],league_coverage['recorded_goals'] if scope == 'league' else dict(acc['coverage']['recorded_goals'],excluded=acc['coverage']['recorded_goals']['excluded_team' if scope == 'team' else 'excluded'])) for scope in ('focal','team','league')}
        penalties = {scope:{role:_penalty_summary(league_penalties[role] if scope == 'league' else acc['penalties'][scope][role],gap=league_penalty_gap if scope == 'league' else False) for role in league_penalties} for scope in ('focal','team','league')}
        deployment = dict(focal=_deployment(acc['starts'],acc['score'],acc['gap'],starts_available=acc['starts_available'],score_available=acc['score_available']),team=_deployment(acc['team_starts'],acc['team_score'],acc['gap'],starts_available=acc['team_starts_available'],score_available=acc['team_score_available']),league=_deployment(league_starts,league_score,league_deployment_gap,starts_available=league_starts_available,score_available=league_score_available))
        payload = dict(reported_usage=reported,strength_usage=strength_usage,scoring_by_strength=scoring_by_strength,
            on_off_attempts=on_off['recorded_all_attempts'],on_off_goals=on_off['recorded_goals'],on_ice_conversion=conversion,
            recorded_penalties=penalties,deployment=deployment,provenance=dict(kind='source',id=source_id))
        descriptive.append(dict(season=year,player_id=pid,result=dict(availability='provided',explanation=None,data=payload)))
        context = _counterparts(pid,observed_result.player_season_pairs,usage_means,positions,bands,old.get(pid))
        context['provenance'] = dict(kind='source',id=source_id)
        contexts.append(dict(season=year,player_id=pid,result=dict(availability='provided',explanation=None,data=context)))
        for pop in CONTEXT_POPULATIONS:
            pending = pop.startswith('neutral_')
            cov = acc['coverage'].get(pop,{})
            reasons = Counter(cov.get('reasons',[]))
            coverage_rows.append(dict(season=year,player_id=pid,population=pop,availability='not_computed' if pending else 'provided',
                explanation='neutral model valuation is not computed in factual reductions' if pending else None,
                known_excluded_seconds=None if pending else cov['excluded'],unquantified_gap=True if pending else cov['gap'],
                reason_counts=[] if pending else [dict(code=k,count=v) for k,v in sorted(reasons.items())],source_ids=[source_id],method_ids=[]))
    return dict(skater_descriptive=descriptive,skater_context=contexts,context_coverage=sorted(coverage_rows,key=lambda r:tuple(r[k] for k in KEYS['context_coverage'])))


def resolve_people(prepared_people: PreparedPeople, observed_result: ObservedResult,
                   source_id: str, affiliations: dict[str, dict[str, str | None]]) -> list[dict]:
    """preserve observed identity and enrich only dated, nonconflicting facts."""
    old_people = {p.player_id:p for p in observed_result.players}
    old_rows = {p.player_id:p for p in observed_result.player_seasons}
    rows = []
    for fact in prepared_people['people']:
        values = fact['values']
        pid = str(values['player_id'])
        old = old_people.get(pid)
        group = 'D' if old and old.reported_position == 'D' else 'F' if old else values['position_group']
        if group not in ('F','D','G'):
            continue
        position = old.reported_position if old else 'G' if group == 'G' else values['reported_positions'][0] if len(values['reported_positions']) == 1 else None
        if position not in ('C','L','R','D','F','G'):
            position = None
        teams = {r['id']:dict(r) for r in old_rows[pid].teams} if pid in old_rows else {}
        for team, abbreviation in affiliations.get(pid, {}).items():
            if team not in teams:
                teams[team] = dict(id=team,abbreviation=abbreviation)
        birth = values['birth_date']
        age_date = values['age_reference_date']
        row = dict(season=prepared_people['season'],player_id=pid,kind='goalie' if group == 'G' else 'skater',
            display_name=old.display_name if old else values['name'],reported_position=position,
            teams=[teams[k] for k in sorted(teams)],source=[dict(kind='source',id=source_id)],
            birth_date=birth,age_as_of=age_date,age_years=(date.fromisoformat(age_date)-date.fromisoformat(birth)).days/365.25 if birth else None,
            height_cm=values['height_cm'],handedness=values['shoots_catches'],
            sweater_numbers=[dict(team_id=str(s['team_id']),game_id=s['game_id'],number=str(s['number'])) for s in values['sweaters']],
            identity_support=dict(problems=[],evidence=[dict(kind='source',id=source_id)]))
        field_names = {'name':'display_name','shoots_catches':'handedness','reported_positions':'reported_position','team_ids':'teams','age_days':'age_years'}
        for field,problem in fact['problems'].items():
            target = field_names.get(field,field)
            if target in ('display_name','birth_date','age_years','height_cm','handedness','sweater_numbers','reported_position','teams','age_as_of'):
                row['identity_support']['problems'].append(dict(field=target,code=problem.get('code',problem.get('status','unavailable')),explanation=problem.get('reason') or 'prepared identity observation unavailable or conflicting'))
        existing = {p['field'] for p in row['identity_support']['problems']}
        for field in ('display_name','reported_position','birth_date','age_years','height_cm','handedness','teams'):
            if (row[field] is None or field == 'teams' and not row[field]) and field not in existing:
                row['identity_support']['problems'].append(dict(field=field,code='source_unavailable',explanation='no resolved dated source observation'))
        rows.append(row)
    require(set(old_people) <= {r['player_id'] for r in rows}, 'prepared people lost an observed skater')
    return sorted(rows,key=lambda r:(r['season'],r['player_id']))


def _catalogs(manifest, prepared_sha, observed_selection):
    from .analysis_publication import json_bytes
    purpose = manifest['purpose']
    sources,methods,supports = [],[],[]
    mappings = {}
    for selected in observed_selection['corpora']:
        year = selected['season']
        source_ids = dict(facts=f'factual-{year}',tracking=f'tracking-unavailable-{year}',skating=f'skating-unadmitted-{year}')
        source_ids.update({key:f'factual-{key}-{year}' for key in ('p','u','h','b')})
        support_ids = {pop:f'{year}-{pop}' for pop in ('source_supported_attempts',*CONTEXT_POPULATIONS[:3])}
        pending = f'factual-pending-reference-{year}'
        mappings[year] = source_ids,support_ids,pending
        sources.append(dict(source_id=source_ids['facts'],label='prepared recorded facts and matched native observed support',purpose=purpose,
            origin='source_capture',acquisition='admitted',construction='recorded',population='dated regular-season source evidence; explicitly matched factual populations',
            definition='reported usage uses known boxscore seconds; recorded penalties are source-attributed infraction credits, counted once per event; counterpart usage is a shared-seconds deployment proxy with focal matched five-on-five elapsed support and separately retained known/all slot weights; empirical standing is relative placement with missing weight visible, not a precision claim; observed five-on-five populations retain their original owner',
            receipts=[dict(uri=str(manifest.directory/'manifest.json'),sha256=prepared_sha),dict(uri=selected['path'],sha256=selected['sha256'])],
            limitations=['recorded facts do not establish causal ability','missing identity, event, time and role evidence retains separate coverage','penalty optional absent roles do not prove nobody drew or served the infraction','penalty team and league references pool eligible skater player-games; goalie credits remain source ledger evidence']))
        definitions = {
            'p': ('matched personal goal and primary-assist credits', 'exact existing observed personal five-on-five mask, counts, seconds and historical credit reconciliation; no new credit rule changes its population'),
            'u': ('matched personal unblocked attempts', 'goal, save and miss credits on saved ordinary five-on-five support with corroborated physical shooter/scorer identity and shooting-team membership; actor conflict removes both sides of the located segment; coordinates are not required'),
            'h': ('matched recorded hits', 'valid five-on-five elapsed membership and usable api/report event collections; every api hit and report HIT is uniquely associated, with hitter on owner team and hittee on opponent; conflicts mask both sides of the located segment independently of attempts'),
            'b': ('matched credited block opportunities', 'own credited blocks divided by opponent ordinary attempts while present on saved ordinary five-on-five support; opposing shooter/blocker identity and membership required; conflict removes both sides of the located segment, without a coordinate requirement'),
        }
        for key,(label,definition) in definitions.items():
            sources.append(dict(source_id=source_ids[key],label=label,purpose=purpose,origin='source_capture',acquisition='admitted',construction='recorded',
                population=label+'; regular-season five-on-five with both goalies present',definition=definition,
                receipts=[dict(uri=str(manifest.directory/'manifest.json'),sha256=prepared_sha),dict(uri=selected['path'],sha256=selected['sha256'])],
                limitations=['family-local matched count and elapsed support; zero denominator remains unavailable','recorded actions do not establish player ability']))
        for kind,limitation in (('tracking','no admitted observed tracking windows, pass links, possession transitions, retrievals or player puck actions'),('skating','v1-04 observed successful http 200 detail responses; skating acquisition deferred; no admitted measurements, player-season context or checked census')):
            sources.append(dict(source_id=source_ids[kind],label=f'{kind} source limitation',purpose=purpose,origin='source_capture',
                acquisition='not_acquired' if kind == 'tracking' else 'access_unverified',construction='recorded',population='recorded tracking windows' if kind == 'tracking' else 'all-situations source-season skating aggregates',
                definition=limitation,receipts=[],limitations=[limitation]))
        inputs = [dict(role='prepared',sha256=prepared_sha,seasons=[r['season'] for r in manifest['seasons']])]
        reference_method = dict(method_id=pending+'-opportunity',family='microstats',recipe_id='pending-reference-opportunity-v1',design_sha256=None,
            input_sha256=hashlib.sha256(json_bytes(inputs)).hexdigest(),fit_seasons=[],training_cutoff=None,target='reference expected goals over source-supported opportunities',population='regular-season five-on-five observed opportunities',reference='zero residual execution; not computed',limitations=['v1-06 owns reference opportunity valuation; no fitted state or probabilities exist here'],
            evidence=[dict(uri=str(manifest.directory/'manifest.json'),sha256=prepared_sha)],purpose=purpose,inputs=inputs,
            reference_id='reference-execution-zero',support_policy_id='factual-pending-reference-v1',assessment=dict(status='experimental',findings=[dict(quantities=['skater_microstats.reference_xg_per60'],population='regular-season five-on-five opportunities',summary='reference valuation not computed',evidence=[dict(uri=str(manifest.directory/'manifest.json'),sha256=prepared_sha)])]))
        methods.append(reference_method)
        methods.append(dict(reference_method,method_id=pending,recipe_id='pending-primary-pass-reference-v1',
            target='reference expected goals from observed primary passes',population='unavailable observed primary-pass links and matching tracked windows',
            limitations=['primary-pass observations and matching tracked windows are not acquired'],
            assessment=dict(status='experimental',findings=[dict(quantities=['skater_microstats.primary_pass_xg_per60'],
                population='unavailable observed primary-pass links and matching tracked windows',summary='primary pass observations not acquired',
                evidence=[dict(uri=str(manifest.directory/'manifest.json'),sha256=prepared_sha)])])))
        for population,identity in support_ids.items():
            supports.append(dict(support_id=identity,season=year,population_id=population,policy_id=f'factual-{population}-v1',
                definition='source-supported timed attempt evidence' if population == 'source_supported_attempts' else 'existing observed interval support; recorded goals add only paired goal/on-net accounting exclusions',source_ids=[source_ids['facts']],method_ids=[]))
    return dict(sources=sorted(sources,key=lambda r:r['source_id']),methods=sorted(methods,key=lambda r:r['method_id']),supports=sorted(supports,key=lambda r:r['support_id'])),mappings


def build_factual_results(prepared: Path, observed: Path, output: Path) -> dict:
    """produce fixed factual results from pinned preparation and native selection."""
    from .analysis_data import read_prepared, read_prepared_game, read_prepared_people
    from .analysis_publication import write_results
    from .publication import read_selection
    from .observed import aggregate
    from .captures import strict_json
    from . import microstats

    _,_,selection,paths = read_selection(observed)
    manifest = read_prepared(prepared,selection['purpose'])
    prepared_sha = hashlib.sha256((manifest.directory/'manifest.json').read_bytes()).hexdigest()
    prepared_selection = strict_json((manifest.directory/'selection.json').read_bytes())
    selected = {r['season']:r for r in prepared_selection['seasons']}
    for row in selection['corpora']:
        require(row['season'] in selected and row['sha256'] == selected[row['season']]['sha256'], 'observed/prepared corpus binding differs')
    catalogs,mappings = _catalogs(manifest,prepared_sha,selection)
    catalogs['people'] = []
    def families():
        for binding,path in zip(selection['corpora'],paths):
            year = binding['season']
            source_ids,support_ids,pending = mappings[year]
            observed_result = aggregate(path,selection['purpose'],year,binding['sha256'])
            season = next(r for r in manifest['seasons'] if r['season'] == year)
            games = sorted(season['selected_game_ids'])
            receipts = {r['game_id']:r for r in observed_result.receipt['games']}
            require(set(games) <= {g.game_id for g in observed_result.games}, 'prepared games absent from observed inventory')
            require(all(row['status'] == 'missing_capture' and not row['source_inputs']
                        for gid,row in receipts.items() if gid not in games), 'observed source evidence omitted from preparation')
            old_games = defaultdict(list)
            for row in observed_result.player_games:
                old_games[row.game_id].append(row)
            game_reductions,micro_reductions = [],[]
            factual_receipts = []
            affiliations = defaultdict(dict)
            for gid in games:
                game = read_prepared_game(manifest,year,gid)
                receipt = receipts[gid]
                require(game['game']['inputs'] == receipt['source_inputs'], f'{gid}: prepared/observed source receipts differ')
                identity = game['game']['identity']
                for pid,team in _dressed(game).items():
                    abbreviation = identity['away_team_abbrev' if int(team) == identity['away_team_id'] else 'home_team_abbrev'] if identity else None
                    previous = affiliations[pid].get(team)
                    require(previous is None or abbreviation is None or previous == abbreviation, f'{gid}: dated team abbreviation conflict')
                    affiliations[pid][team] = abbreviation if abbreviation is not None else previous
                recorded = recorded_evidence(game,receipt,source_ids,support_ids)
                reduced = reduce_game(game,old_games[gid],recorded)
                micro_reduced = microstats.reduce_game(game,receipt)
                game_reductions.append(reduced)
                micro_reductions.append(micro_reduced)
                factual_receipts.append(dict(game_id=gid,status=receipt['status'],
                    credit_issues=reduced['credit_issues'],penalty_ledger=reduced['penalty_ledger'],
                    credit_dispositions=[dict(player_id=pid,unclassified=dict(person['unclassified']),unmatched=person['issues'])
                                         for pid,person in reduced['people'].items() if person['unclassified'] or person['issues']],
                    zero_toi_penalty_credits=[dict(player_id=pid,role=role,count=value['count'],categories=dict(value['categories']))
                        for pid,person in reduced['people'].items() if person['reported']['seconds'] == 0
                        for role,value in person['penalties'].items() if value['count']],
                    evidence_dispositions=recorded['dispositions'],
                    microstats={key:{k:v for k,v in value.items() if k != 'players'} for key,value in micro_reduced['families'].items()},
                    microstat_support={key:dict(included_player_seconds=sum(v['seconds'] for v in value['players'].values()),
                        excluded_player_seconds=sum(v['excluded_seconds'] for v in value['players'].values()),
                        count=sum(v['count'] for v in value['players'].values()),opportunities=sum(v['opportunities'] for v in value['players'].values()))
                        for key,value in micro_reduced['families'].items()}))
            from .artifacts import write_json
            receipt_path = Path(output)/f'{year}-factual-receipt.json'
            write_json(receipt_path,dict(season=year,prepared_sha256=prepared_sha,corpus_sha256=binding['sha256'],games=factual_receipts))
            receipt_hash = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
            for source in catalogs['sources']:
                if source['source_id'] in {source_ids[k] for k in ('facts','p','u','h','b')}:
                    source['receipts'].append(dict(uri=str(receipt_path.resolve()),sha256=receipt_hash))
            del factual_receipts
            people = resolve_people(read_prepared_people(manifest,year),observed_result,source_ids['facts'],affiliations)
            catalogs['people'].extend(people)
            summary = summarize_season(people,game_reductions,observed_result,source_ids)
            del game_reductions
            micro = microstats.summarize_season(people,micro_reductions,observed_result,source_ids,pending,pending+'-opportunity')
            del micro_reductions
            records = [dict(season=year,family='descriptive',availability='provided',explanation=None,
                tables={k:summary[k] for k in FAMILY_TABLES['descriptive']})]
            records.append(dict(season=year,family='microstats',availability='provided',explanation=None,tables=dict(skater_microstats=micro)))
            def evidence_games():
                for gid in games:
                    game = read_prepared_game(manifest,year,gid)
                    rows = recorded_evidence(game,receipts[gid],source_ids,support_ids)
                    yield dict(game_id=gid, **{table:sorted(rows[table],key=lambda r:tuple(r[k] for k in KEYS[table]))
                        for table in ('attempt_fact','interval_fact','interval_player','interval_location')},
                        dressed_game=rows['dressed_game'])
            records.append(dict(season=year,family='evidence',availability='provided',explanation=None,
                tables=dict(context_coverage=summary['context_coverage']),game_ids=games,game_rows=evidence_games()))
            for family in FAMILY_TABLES:
                if family not in ('descriptive','microstats','evidence'):
                    records.append(dict(season=year,family=family,availability='not_computed',explanation=f'{family} estimation is outside factual reductions; its assigned numerical producer remains pending',tables={}))
            yield from sorted(records,key=lambda r:r['family'])
    result_selection = dict(purpose=selection['purpose'],seasons=[r['season'] for r in selection['corpora']],
                            observed_bindings=selection['corpora'],prepared_sha256=prepared_sha)
    # bindings contain a native locator in the command selection; the fixed
    # exchange binds only season and corpus digest.
    result_selection['observed_bindings'] = [dict(season=r['season'],corpus_sha256=r['sha256']) for r in selection['corpora']]
    return write_results(result_selection,catalogs,families(),Path(output))
