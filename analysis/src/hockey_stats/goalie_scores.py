"""annual goalie projections and matched evidence; saved readers never reopen inputs."""

from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
from math import fsum, isclose, isfinite
from pathlib import Path
import resource
from time import perf_counter

import numpy as np
from scipy.special import expit, log_expit, logsumexp

from .input_locations import input_path, same_input_reference
from .artifacts import (
    digest, implementation, json_line, read_jsonl, require, require_count,
    require_fields, require_number, require_season_label, write_json, write_jsonl,
)
from .captures import InputContractError
from .chance_cli import identity, output_path, read_json
from .analysis_publication import ESTIMATE_FIELDS, GOALIE_STRENGTHS, KEYS, native_display_mass

HEADS = ('h', 'd')
BASE_HEADS = ('q', 'r', 'g')
CONTINUATION = ('recorded_reattempt_probability', 'reattempt_neutral_goal_probability', 'followup_danger')
FIELDS = ESTIMATE_FIELDS['goalie_result']
DEPENDENCIES = dict(stopping_goals_per100_on_net=('r','g'), miss_probability=('q',),
                    recorded_stop_probability=('q','r'), conversion_probability=('q','r','g'),
                    recorded_reattempt_probability=('h',), reattempt_neutral_goal_probability=('h','d'),
                    followup_danger=('h','d'))
PUBLIC_TABLES = ('goalie_result', 'goalie_observed', 'analysis_map', 'execution_breakdown', 'goalie_evidence_map', 'goalie_danger')
TYPES = ('wrist', 'snap', 'slap', 'backhand', 'tip', 'other')
GROUPED_TYPES = ('all', 'wrist_snap', 'slap', 'tip', 'backhand', 'other')
DANGER = ('<.05', '[.05,.15)', '>=.15')
POPULATIONS = ('unblocked', 'on_net')
MANIFEST_KEYS = ('schema_version','kind','purpose','season','recipe','implementation','prepared','coaches','state',
                 'base_state','base_scores','training_cutoff','files','coverage','resources','numerical_sensitivity')
MEMBERS = {'people.jsonl':'person', 'catalogs.json':'catalogs', 'event_values.jsonl':'event',
           'source_games.jsonl':'source_game', 'targets.jsonl':'target', 'projections.jsonl':'projection', 'coverage.json':'coverage',
           'sensitivity.json':'sensitivity', **{table+'.jsonl':table for table in PUBLIC_TABLES}}
REFERENCE = 'fixed annual shot-context panel; all execution residuals neutral except the focal goalie; defending-team strength'


def constituent_states(strength):
    require(strength in (*GOALIE_STRENGTHS, 'covered_all'), 'unknown goalie strength')
    return ('5v5','4v4','3v3') if strength == 'ev' else ('4v5','3v5','3v4') if strength == 'pk' else (strength,)


def state_selected(state, strength):
    if state is None or len(state) != 4 or state[3] != 1:
        return False
    if strength == 'covered_all':
        return True
    return state[2] == 1 and f'{state[1]}v{state[0]}' in constituent_states(strength)


def _log_sum(values):
    return float(logsumexp(values)) if len(values) else -np.inf


def _mass(log_value):
    return float(np.exp(log_value))


def _ratio(numerator, denominator):
    return None if denominator == -np.inf else float(np.exp(numerator-denominator))


def _saved_logs(values):
    return [None if value == -np.inf else float(value) for value in values]


def _restore_logs(values):
    return np.array([-np.inf if value is None else value for value in values])


def _continuation_levels(logs):
    w,h,hd=logs
    return dict(recorded_reattempt_probability=_ratio(h,w),
                reattempt_neutral_goal_probability=_ratio(hd,h),followup_danger=_ratio(hd,w))


def _levels(prefix, continuation):
    a,b,c,d = prefix
    return dict(miss_probability=None if a == -np.inf else float(-np.expm1(b-a)),
                recorded_stop_probability=None if b == -np.inf else float(-np.expm1(c-b)),
                conversion_probability=_ratio(d,c),**_continuation_levels(continuation))


def _estimate(value, method, *, reason='no_exposure', explanation='the selected population has no supported positive denominator'):
    return dict(value=value,unavailable_reason=None if value is not None else reason,
                reason_detail=None if value is not None else dict(explanation=explanation,
                    evidence=[] if reason == 'no_exposure' else [dict(kind='method',id=method)]+([dict(kind='source',id=method.replace('goalie-v1-07-','goalie-source-v1-07-'))] if reason == 'missing_source' else [])),
                uncertainty=dict(kind='not_estimated'))


def _support(n=0, *, weight=None, seconds=None, gap=False, reasons=(), current=None, prior_only=False, years=(), inferred=()):
    return dict(included_seconds=seconds,events=n,eligible_weight=n if weight is None else weight,
                known_excluded_seconds=None,unquantified_gap=gap,
                reason_counts=[dict(code=code,count=count) for code,count in sorted(Counter(reasons).items())],
                inferred_inputs=sorted(set(inferred)),current_season_information=bool(n) if current is None else current,
                prior_only=prior_only,prior_seasons=sorted(set(years)))


def _actor_evidence(state, design, player, heads):
    records, keys, effects = {}, {}, {}
    for head in heads:
        metadata = state.heads[head]
        actor = next((row for row in metadata['actors'] if row['block'] == 'goalie' and str(row['id']) == player), None)
        complete = metadata['status'] == 'complete' and actor is not None
        prior = next((row for row in metadata['priors'] if row['block'] == 'goalie' and str(row['id']) == player), {})
        historical = prior.get('last_supported')
        years = [] if historical is None else [historical['season']]
        likelihood = set()
        if complete:
            likelihood = {row['key'] for row in design.targets if row[head+'_included'] and str(row['goalie_id']) == player}
        records[head] = dict(available=complete, likelihood_events=len(likelihood),
                            prior_only=bool(complete and actor['prior_only']), prior_seasons=years,
                            reason=None if complete else 'head_incomplete' if metadata['status'] != 'complete' else 'actor_coefficient_unavailable')
        keys[head] = likelihood
        effects[head] = None if not complete else float(state.arrays[head]['coefficients'][actor['index']]-metadata['centers']['goalie']['value'])
    return records, keys, effects


def _base_actor_evidence(state, player, event_values):
    records, keys, effects = {}, {}, {}
    for head in BASE_HEADS:
        metadata = state.heads[head]
        actor = next((row for row in metadata['actors'] if row['block'] == 'goalie' and str(row['id']) == player), None)
        available = actor is not None and metadata['status'] == 'complete'
        prior = next((row for row in metadata['priors'] if row['block'] == 'goalie' and str(row['id']) == player), {})
        historical = prior.get('last_supported')
        likelihood = {row['key'] for row in event_values.values() if row['goalie_id'] == player and row['heads'][head]['included']} if available else set()
        records[head] = dict(available=available, likelihood_events=len(likelihood), prior_only=bool(available and actor['prior_only']),
                            prior_seasons=[] if historical is None else [historical['season']],
                            reason=None if available else 'actor_coefficient_unavailable')
        keys[head] = likelihood
        effects[head] = None if not available else float(state.arrays[head]['coefficients'][actor['index']]-metadata['centers']['goalie']['value'])
    return records, keys, effects


def _panel_continuation(state, panel, predictors):
    from .goalie import goalie_reference_logits
    offsets = panel.arrays['event_offsets']
    length = len(panel.arrays['origin_cells'])
    result = {head:np.empty(length) if state.heads[head]['status'] == 'complete' else None for head in HEADS}
    for start in range(0,length,65536):
        end = min(length,start+65536)
        indices = np.searchsorted(offsets,np.arange(start,end),side='right')-1
        rows = [predictors[panel.events[index]['key']] for index in indices]
        evaluated=goalie_reference_logits(state,rows,panel.arrays['origin_cells'][start:end])
        for head in HEADS:
            if result[head] is not None:
                require(evaluated[head] is not None,'completed goalie head lacks neutral panel evaluation')
                result[head][start:end]=evaluated[head]
    return result


def _panel_projections(panel, continuation, effects_by_player):
    """reduce one panel in origin order; retain only each goalie's scalar/cell sums.

    continuation contains the panel's fully neutral h/d logits. effects_by_player maps
    goalie ids to centered q/r/g/h/d residuals; unavailable residuals remain none.
    """
    if not effects_by_player:
        return {}
    require(set(continuation) == set(HEADS), 'goalie head axes differ')
    for effects in effects_by_player.values():
        require(set(effects) == {'q','r','g','h','d'}, 'goalie head axes differ')
    totals = {player:dict(prefixes={'focal':np.full(4,-np.inf)},
        continuation={'focal':np.full(3,-np.inf)},positive=np.full(656,-np.inf),negative=np.full(656,-np.inf))
        for player in effects_by_player}
    neutral_prefix = np.full(4,-np.inf)
    neutral_continuation = np.full(3,-np.inf)
    arrays = panel.arrays
    length = len(arrays['origin_cells'])
    for start in range(0,length,65536):
        end = min(length,start+65536)
        event = np.searchsorted(arrays['event_offsets'],np.arange(start,end),side='right')-1
        upstream = np.asarray(arrays['neutral_upstream_logits'][start:end],dtype=np.float64)
        goal = np.asarray(arrays['neutral_goal_logits'][start:end],dtype=np.float64)
        setup = np.asarray(arrays['setup_weights'][event],dtype=np.float64)
        weights = np.asarray(arrays['origin_weights'][start:end],dtype=np.float64)
        n = len(weights)
        require(upstream.shape == (n,3) and goal.shape == setup.shape == (n,2)
                and np.isfinite(upstream).all() and np.isfinite(goal).all()
                and np.isfinite(setup).all() and np.all(setup > 0)
                and np.allclose(setup.sum(axis=1),1,rtol=0,atol=1e-15)
                and weights.shape == (n,) and np.isfinite(weights).all() and np.all(weights >= 0),
                'invalid goalie reference branches')
        logits = {head:None if values is None else values[start:end] for head,values in continuation.items()}
        for head,values in logits.items():
            require(values is None or np.shape(values) == (n,) and np.isfinite(values).all(), head+': invalid neutral logits')
        with np.errstate(divide='ignore'):
            logs = np.log(weights)
        log_setup = np.log(setup)
        neutral_upstream = log_expit(upstream)
        neutral_goal = log_expit(goal)
        cumulative = np.cumsum(neutral_upstream,axis=1)
        prefix = np.array([*(_log_sum(logs+cumulative[:,i]) for i in range(3)),
                           _log_sum(logs+cumulative[:,2]+logsumexp(log_setup+neutral_goal,axis=1))])
        neutral_prefix = np.logaddexp(neutral_prefix,prefix)
        # fixed saved-shot reference; independent of the focal goalie.
        saved = logs+neutral_upstream[:,0]+neutral_upstream[:,1]+logsumexp(
            log_setup+np.logaddexp(log_expit(-upstream[:,2,None]),
                                  neutral_upstream[:,2,None]+log_expit(-goal)),axis=1)
        w = _log_sum(saved)
        h = None if logits['h'] is None else log_expit(logits['h']+0.)
        d = None if logits['d'] is None else log_expit(logits['d']+0.)
        mass = np.array([w,-np.inf if h is None else _log_sum(saved+h),
                         -np.inf if h is None or d is None else _log_sum(saved+h+d)])
        neutral_continuation = np.logaddexp(neutral_continuation,mass)
        neutral_rg = neutral_upstream[:,2,None]+neutral_goal
        log_base = logs+neutral_upstream[:,0]+neutral_upstream[:,1]
        for player,effects in effects_by_player.items():
            focal_upstream = upstream.copy()
            for index,head in ((1,'q'),(2,'r')):
                if effects[head] is not None:
                    focal_upstream[:,index] += effects[head]
            focal_goal = goal+(effects['g'] or 0.)
            focal_upstream_logs = log_expit(focal_upstream)
            focal_goal_logs = log_expit(focal_goal)
            cumulative = np.cumsum(focal_upstream_logs,axis=1)
            prefix = np.array([*(_log_sum(logs+cumulative[:,i]) for i in range(3)),
                               _log_sum(logs+cumulative[:,2]+logsumexp(log_setup+focal_goal_logs,axis=1))])
            own = totals[player]
            own['prefixes']['focal'] = np.logaddexp(own['prefixes']['focal'],prefix)
            h = None if logits['h'] is None or effects['h'] is None else log_expit(logits['h']+effects['h'])
            d = None if logits['d'] is None or effects['d'] is None else log_expit(logits['d']+effects['d'])
            mass = np.array([w,-np.inf if h is None else _log_sum(saved+h),
                             -np.inf if h is None or d is None else _log_sum(saved+h+d)])
            own['continuation']['focal'] = np.logaddexp(own['continuation']['focal'],mass)
            # cancellation precedes setup/origin integration; focal q stays excluded.
            focal_rg = log_expit(focal_upstream[:,2,None])+focal_goal_logs
            high = np.maximum(neutral_rg,focal_rg)
            delta = np.exp(high)*(-np.expm1(np.minimum(neutral_rg,focal_rg)-high))
            delta *= np.sign(neutral_rg-focal_rg)
            delta = np.sum(setup*delta,axis=1)
            positive = np.where(delta > 0,delta,0.)
            negative = np.where(delta < 0,-delta,0.)
            with np.errstate(divide='ignore'):
                stopping = log_base+np.log(positive),log_base+np.log(negative)
            for name,values in zip(('positive','negative'),stopping,strict=True):
                np.logaddexp.at(own[name],arrays['origin_cells'][start:end],values)
    # these common arrays are complete; pooling reads them without mutation.
    for own in totals.values():
        own['prefixes']['neutral'] = neutral_prefix
        own['continuation']['neutral'] = neutral_continuation
    return totals


def _pool_projection(pieces):
    totals = dict(prefixes={name:np.full(4,-np.inf) for name in ('neutral','focal')},
                  continuation={name:np.full(3,-np.inf) for name in ('neutral','focal')},
                  positive=np.full(656,-np.inf),negative=np.full(656,-np.inf))
    for piece in pieces:
        for group in ('prefixes','continuation'):
            for name in ('neutral','focal'):
                totals[group][name] = np.logaddexp(totals[group][name],piece[group][name])
        for name in ('positive','negative'):
            totals[name] = np.logaddexp(totals[name],piece[name])
    return totals


def _finish_projection(season, player, strength, panels, pooled, evidence, likelihood_keys, elapsed):
    neutral = _levels(pooled['prefixes']['neutral'],pooled['continuation']['neutral'])
    focal = _levels(pooled['prefixes']['focal'],pooled['continuation']['focal'])
    for field,heads in DEPENDENCIES.items():
        if field == 'stopping_goals_per100_on_net':
            continue
        if any(evidence[head]['reason'] == 'head_incomplete' for head in heads):
            neutral[field] = None
        if any(not evidence[head]['available'] for head in heads):
            focal[field] = None
    b = pooled['prefixes']['neutral'][1]
    cells = None
    if b != -np.inf and all(evidence[head]['available'] for head in ('r','g')):
        cells = 100*(np.exp(pooled['positive']-b)-np.exp(pooled['negative']-b))
    values = dict(stopping_goals_per100_on_net=None if cells is None else fsum(cells),**focal)
    for field in focal:
        values[field+'_difference'] = None if focal[field] is None or neutral[field] is None else focal[field]-neutral[field]
    support, unavailable = {}, {}
    reference_denominators = dict(miss_probability=pooled['prefixes']['neutral'][0],recorded_stop_probability=b,
        conversion_probability=pooled['prefixes']['neutral'][2],stopping_goals_per100_on_net=b,
        recorded_reattempt_probability=pooled['continuation']['neutral'][0],followup_danger=pooled['continuation']['neutral'][0],
        reattempt_neutral_goal_probability=pooled['continuation']['neutral'][1])
    for field in FIELDS:
        base = field.removesuffix('_difference')
        heads = DEPENDENCIES[base]
        available = all(evidence[head]['available'] for head in heads)
        current = set().union(*(likelihood_keys[head] for head in heads))
        years = sorted({year for head in heads for year in evidence[head]['prior_seasons']})
        if not available:
            values[field] = None
        prior_only = available and all(evidence[head]['prior_only'] for head in heads)
        all_current = available and all(bool(likelihood_keys[head]) for head in heads)
        support[field] = _support(len(current),weight=_mass(reference_denominators[base]),
            seconds=None if elapsed is None else elapsed['included_seconds'],
            gap=True if elapsed is None else elapsed['unquantified_gap'],current=all_current,prior_only=prior_only,years=years,
            inferred=(['historical_borrowing'] if years else [])
                +(['blocked_origin'] if any(row['origins'] > row['events'] for row in panels) else [])
                +(['setter'] if base not in ('miss_probability','recorded_stop_probability') and any(row['events'] for row in panels) else []))
        if base == 'reattempt_neutral_goal_probability' and evidence['h']['reason'] == 'head_incomplete':
            support[field]['eligible_weight'] = None
        if elapsed is not None:
            for name in ('known_excluded_seconds','reason_counts'):
                support[field][name] = elapsed[name]
        if values[field] is None:
            failed = [head for head in heads if evidence[head]['reason'] == 'head_incomplete']
            absent = [head for head in heads if evidence[head]['reason'] == 'actor_coefficient_unavailable']
            unavailable[field] = dict(reason='failed_fit' if failed else 'missing_source' if absent else 'no_exposure',
                explanation='required annual heads did not complete: '+','.join(failed) if failed else
                    'focal goalie coefficients are unavailable in heads: '+','.join(absent) if absent else
                    'the common reference has no mathematical denominator for '+base)
    masses = {group:{name:dict(log_masses=_saved_logs(pooled[group][name]),masses=[_mass(value) for value in pooled[group][name]])
                     for name in ('neutral','focal')} for group in ('prefixes','continuation')}
    for index,heads in ((1,('q',)),(2,('q','r')),(3,('q','r','g'))):
        if not all(evidence[head]['available'] for head in heads):
            masses['prefixes']['focal']['masses'][index] = None
            masses['prefixes']['focal']['log_masses'][index] = None
    for name in ('neutral','focal'):
        for index,heads in ((1,('h',)),(2,('h','d'))):
            available = all(evidence[head]['reason'] != 'head_incomplete' for head in heads) if name == 'neutral' else all(evidence[head]['available'] for head in heads)
            if not available:
                masses['continuation'][name]['masses'][index] = None
                masses['continuation'][name]['log_masses'][index] = None
    return dict(season=season,player_id=player,strength=strength,values=values,neutral_values=neutral,
                masses=masses,coefficient_support=evidence,support=support,panels=panels,unavailable=unavailable),cells


def _event_values(design, state, base_state, base_events):
    from .execution import execution_branch_probabilities, integrated_log_prefixes
    from .execution_design import origins_for
    from .goalie import goalie_logits
    predictors = {predictor.key:predictor for predictor in design.predictors}
    targets = {row['key']:row for row in design.targets}
    for game in design.source_games:
        for source in game['events']:
            key = f"{source['game_id']}:{source['source_index']}"
            base = base_events.get(key)
            target = targets.get(key)
            require(target is not None, 'source event has no goalie target disposition')
            paired = source['status'] == 'included' and source['outcome'] != 'block' and source['model_type'] in TYPES and base is not None and base['status'] == 'complete'
            if paired:
                require(source['goalie_id'] == base['goalie_id'] and source['state'] == base['physical_state']
                        and source['outcome'] == base['outcome'] and source['model_type'] == base['shot_type'],
                        'goalie source/base score identity, state, outcome or model type differs')
            predictor = predictors.get(key)
            stages = {}
            if paired and predictor is not None:
                cells, weights = origins_for(predictor)
                prediction = execution_branch_probabilities(base_state,predictor,cells,('goalie',))
                logs = integrated_log_prefixes(prediction,weights)
                expected = dict(miss=float(-np.expm1(logs['uq']-logs['u'])),
                    recorded_stop=float(-np.expm1(logs['uqr']-logs['uq'])),conversion=float(np.exp(logs['uqrg']-logs['uqr'])))
            else:
                expected = dict.fromkeys(('miss','recorded_stop','conversion'))
            on_net = source['outcome'] in ('save','goal')
            labels = dict(miss=int(source['outcome'] == 'miss') if source['status'] == 'included' and source['outcome'] != 'block' else None,
                recorded_stop=int(source['recorded_stop']) if on_net and source['recorded_stop'] is not None else None,
                conversion=int(source['outcome'] == 'goal') if on_net and source['recorded_stop'] is False else None,
                reattempt=int(source['recorded_reattempt']) if source['outcome'] == 'save' and source['recorded_reattempt'] is not None else None,
                next_attempt_danger=target['d_target'])
            continuation = dict.fromkeys(HEADS)
            if predictor is not None and source['outcome'] == 'save':
                logits = goalie_logits(state,predictor,np.array([predictor.proxy_cell]),('goalie',))
                continuation = {head:None if logits[head] is None else float(expit(logits[head][0])) for head in HEADS}
            expected.update(reattempt=continuation['h'],next_attempt_danger=continuation['d'])
            for stage in labels:
                label, probability = labels[stage], expected[stage]
                stages[stage] = dict(response=label,prediction=probability,
                    reason='label_unavailable' if label is None else (('h_failed_fit' if stage == 'reattempt' and state.heads['h']['status'] != 'complete' else 'd_failed_fit' if stage == 'next_attempt_danger' and state.heads['d']['status'] != 'complete' else 'prediction_unavailable') if probability is None else None))
            actor_continuation=dict.fromkeys(HEADS)
            if predictor is not None and source['outcome'] == 'save':
                actor_logits=goalie_logits(state,predictor,np.array([predictor.proxy_cell]))
                actor_continuation={head:None if actor_logits[head] is None else float(expit(actor_logits[head][0])) for head in HEADS}
            conditional = base['conditional_probabilities'] if paired else None
            yield dict(season=design.season,game_id=source['game_id'],source_index=source['source_index'],key=key,
                goalie_id=source['goalie_id'],physical_state=source['state'],outcome=source['outcome'],shot_type=source['model_type'],
                source_status=source['status'],base_status=None if base is None else base['status'],paired=paired,
                origin_cell=source['origin_cell'],on_net_probability=None if conditional is None else conditional['neutral_goalie_on_net_goal_probability'],
                unblocked_probability=None if conditional is None else conditional['neutral_goalie_unblocked_goal_probability'],
                neutral_on_net_probability=None if conditional is None else conditional['neutral_on_net_goal_probability'],stages=stages,
                continuation_probabilities=dict(actor=actor_continuation,neutral_goalie=continuation),
                base_heads=None if base is None else base['heads'],
                exclusions=[] if paired else ['source_unavailable'] if source['status'] != 'included' else
                    ['blocked_outside_paired_unblocked'] if source['outcome'] == 'block' else ['modeled_type_unavailable'] if source['model_type'] not in TYPES else ['base_score_unavailable'])


def _actual_state(state):
    return dict(attacking_skaters=state[0],defending_skaters=state[1],
                attacking_goalie_present=bool(state[2]),defending_goalie_present=bool(state[3]))


def _paired_rows(events, population):
    return [row for row in events if row['paired'] and (population == 'unblocked' or row['outcome'] in ('save','goal'))]


def _totals(events, population):
    selected = _paired_rows(events,population)
    return dict(attempts=len(selected),goals=sum(row['outcome'] == 'goal' for row in selected),
                expected_goals=fsum(row[population+'_probability'] for row in selected))


def _paired_evidence(events, league, population, method):
    totals = _totals(events,population)
    n, goals, expected = (totals[key] for key in ('attempts','goals','expected_goals'))
    league_n, league_expected = league['attempts'],league['expected_goals']
    mean = expected/n if n else None
    league_mean = league_expected/league_n if league_n else None
    result = dict(attempts=n,goals=goals,expected_goals=expected,
        goals_saved_above_expected=_estimate(expected-goals,method),
        goals_per100_expected=_estimate(100*goals/expected if expected > 0 else None,method),
        mean_goal_probability=_estimate(mean,method),league_mean_goal_probability=_estimate(league_mean,method),
        difficulty_relative_percent=_estimate(100*(mean/league_mean-1) if mean is not None and league_mean is not None and league_mean > 0 else None,method),
        support=_support(n,inferred=['setter'] if n or league_n else ()),method_id=method)
    if population == 'on_net':
        result['expected_save_fraction'] = _estimate(None if mean is None else 1-mean,method)
    return result


def _stage_evidence(events):
    result = {}
    for stage in ('miss','recorded_stop','conversion','reattempt','next_attempt_danger'):
        selected = [row['stages'][stage] for row in events if row['source_status'] == 'included'
                    and row['stages'][stage]['response'] is not None and row['stages'][stage]['prediction'] is not None]
        numerator = 'fractional_response_sum' if stage == 'next_attempt_danger' else 'success_count'
        response = fsum(row['response'] for row in selected) if stage == 'next_attempt_danger' else sum(row['response'] for row in selected)
        result[stage] = {numerator:response,'eligible_count':len(selected),
                        'matched_expected_sum':fsum(row['prediction'] for row in selected),
                        'support':_support(len(selected),inferred=['setter'] if selected and stage in ('conversion','next_attempt_danger') else ())}
    return result


def _source_counts(events, source, method, *, unavailable=False, gap=False, reasons=()):
    rows = [row for row in events if row['source_status'] == 'included' and row['outcome'] != 'block']
    counts = Counter(row['outcome'] for row in rows)
    n, on_net = len(rows),counts['save']+counts['goal']
    reasons=list(reasons)
    if (unavailable or gap) and 'source_unavailable' not in reasons:
        reasons.append('source_unavailable')
    return dict(unblocked_attempts=None if unavailable else n,misses=None if unavailable else counts['miss'],
        shots_on_goal=None if unavailable else on_net,saves=None if unavailable else counts['save'],
        goals_against=None if unavailable else counts['goal'],
        save_percentage=_estimate(counts['save']/on_net if on_net and not unavailable else None,method,
            reason='missing_source' if unavailable else 'no_exposure',explanation='the source collection is unavailable or this identity has no dated game evidence' if unavailable else 'no supported on-net source attempts'),
        support=_support(n,gap=unavailable or gap,reasons=reasons),provenance=source)


def _reported_counts(goalies, strength, source, method, *, unassigned=0):
    category = 'all' if strength == 'covered_all' else strength if strength in ('ev','pk') else None
    counts, coverage = {}, {}
    for field in ('shots_on_goal','saves','goals_against'):
        values = [] if category is None else [row['reported_counts'][category][field] for row in goalies]
        supported = [value for value in values if value is not None]
        counts[field] = sum(supported) if supported else None
        coverage[field] = len(supported)
    counts.update(unblocked_attempts=None,misses=None)
    # each total uses only its independently reported field; the fraction needs a matched pair.
    paired = [] if category is None else [row['reported_counts'][category] for row in goalies
              if row['reported_counts'][category]['shots_on_goal'] is not None and row['reported_counts'][category]['saves'] is not None]
    denominator = sum(row['shots_on_goal'] for row in paired)
    fraction = sum(row['saves'] for row in paired)/denominator if denominator else None
    if fraction is not None and (counts['shots_on_goal'] != denominator or counts['saves'] != sum(row['saves'] for row in paired)):
        fraction = None
    reasons=['source_unavailable'] if not goalies or category is None or any(value < len(goalies) for value in coverage.values()) else []
    if not goalies and unassigned:
        reasons=[]
    reasons+=['unassigned_player_games','source_unavailable']*unassigned
    counts.update(save_percentage=_estimate(fraction,method),support=_support(len(goalies),gap=bool(reasons),reasons=reasons),provenance=source)
    return counts


def _usage_rows(goalies, method, source, unassigned, unassigned_by_team, *, team_id=None):
    selected = [row for row in goalies if team_id is None or row['team'] is not None and row['team']['id'] == team_id]
    timed = [row for row in selected if row['reported_seconds'] is not None]
    positive = sum(row['reported_seconds'] > 0 for row in timed)
    seconds = sum(row['reported_seconds'] for row in timed) if timed else None
    shifts = [row['reported_shifts'] for row in selected if row['reported_shifts'] is not None]
    reasons=['source_unavailable'] if len(timed)<len(selected) or not selected and not unassigned else []
    reasons+=['unassigned_player_games','source_unavailable']*unassigned
    value = dict(positive_toi_appearances=positive,reported_seconds=seconds,
                 minutes_per_appearance=_estimate(seconds/(60*positive) if positive else None,method),
                 reported_shifts=sum(shifts) if shifts else None,listed_games=len(selected),supported_games=len(timed),
                 missing_games=len(selected)-len(timed),support=_support(len(timed),gap=bool(reasons),reasons=reasons))
    if team_id is not None:
        value['team_id'] = team_id
    else:
        value.update(teams=[_usage_rows(selected,method,source,len(unassigned_by_team.get(team,[])),{},team_id=team) for team in sorted({row['team']['id'] for row in selected if row['team'] is not None})],provenance=source)
    return value


def _summary_evidence(events, league, source, method, *, missing=False, gap=False, reasons=()):
    state_groups = defaultdict(list)
    for row in events:
        if row['source_status'] == 'included' and row['physical_state'] is not None:
            state_groups[tuple(row['physical_state'])].append(row)
    result = dict(source_counts=_source_counts(events,source,method,unavailable=missing,gap=gap,reasons=reasons),
        on_net_evidence=_paired_evidence(events,league['populations']['on_net'],'on_net',method),
        unblocked_evidence=_paired_evidence(events,league['populations']['unblocked'],'unblocked',method),
        stage_evidence=_stage_evidence(events),actual_states=[],provenance=source)
    for state, rows in sorted(state_groups.items()):
        reference = league['states'][state]
        result['actual_states'].append(dict(state=_actual_state(state),source_counts=_source_counts(rows,source,method,gap=gap,reasons=reasons),
            on_net_evidence=_paired_evidence(rows,reference['on_net'],'on_net',method),
            unblocked_evidence=_paired_evidence(rows,reference['unblocked'],'unblocked',method),stage_evidence=_stage_evidence(rows)))
    return result


def _row(year, player, payload, **selectors):
    return dict(season=year,player_id=player,**selectors,result=dict(availability='provided',explanation=None,data=payload))


def _modeled_rows(projection, cells, method):
    year, player, strength = (projection[key] for key in ('season','player_id','strength'))
    estimates = {}
    for field,value in projection['values'].items():
        missing = projection['unavailable'].get(field,{})
        estimates[field] = _estimate(value,method,reason=missing.get('reason','no_exposure'),
                                    explanation=missing.get('explanation','the common panel is empty'))
    yield 'goalie_result',enrich_goalie_row(_row(year,player,dict(**estimates,support=projection['support'],method_id=method),
        strength=strength),projection,method)
    from .observed_spatial import cells as geometry
    missing = projection['unavailable'].get('stopping_goals_per100_on_net',{})
    data = dict(grid_id='native656',unit='goals_per100_on_net',reference=REFERENCE,
        cells=None if cells is None else [dict(cell_id=index,value=float(value)) for index,value in enumerate(cells)],
        display_cells=None,integrated_value=projection['values']['stopping_goals_per100_on_net'],
        unavailable_reason=missing.get('reason'),reason_detail=None if cells is not None else estimates['stopping_goals_per100_on_net']['reason_detail'],
        support=projection['support']['stopping_goals_per100_on_net'],method_id=method)
    if cells is not None:
        display = native_display_mass(cells)
        data['display_cells'] = [dict(cell_id=shape['cell_id'],mass=float(value),density_per100sqft=float(100*value/shape['area_sqft']))
                                 for shape,value in zip(geometry(),display,strict=True)]
    yield 'analysis_map',_row(year,player,data,strength=strength,map_kind='goalie_stopping',view='effect')


def _type_selected(event, shot_type):
    return shot_type == 'all' or event['shot_type'] in (('wrist','snap') if shot_type == 'wrist_snap' else (shot_type,))


def _league_references(events):
    """reduce ordered annual events once per strength/state/type/population reference."""
    result = {}
    for strength in (*GOALIE_STRENGTHS,'covered_all'):
        selected = [row for row in events if state_selected(row['physical_state'],strength)]
        states = defaultdict(list)
        for row in selected:
            states[tuple(row['physical_state'])].append(row)
        populations = {population:_totals(selected,population) for population in POPULATIONS}
        types = {'all':populations}
        for shot_type in GROUPED_TYPES[1:]:
            rows = [row for row in selected if _type_selected(row,shot_type)]
            types[shot_type] = {population:_totals(rows,population) for population in POPULATIONS}
        result[strength] = dict(populations=populations,
            states={state:{population:_totals(rows,population) for population in POPULATIONS}
                    for state,rows in states.items()},types=types)
    return result


def _mass_states(events,population):
    grouped = defaultdict(list)
    for row in _paired_rows(events,population):
        grouped[tuple(row['physical_state'])].append(row)
    return [dict(state=_actual_state(state),**_totals(rows,population),support=_support(len(rows),inferred=['setter'])) for state,rows in sorted(grouped.items())]


def _evidence_map(events,league_totals,population,method):
    from .observed_spatial import cells as geometry
    selected = _paired_rows(events,population)
    native = np.zeros((656,3));unmapped = np.zeros(3)
    for row in selected:
        mass = np.array([int(row['outcome'] == 'goal'),row[population+'_probability'],1.])
        if row['origin_cell'] is None:
            unmapped += mass
        else:
            native[row['origin_cell']] += mass
    totals = _totals(events,population)
    display = np.column_stack([native_display_mass(native[:,index]) for index in range(3)]) if selected else np.zeros((668,3))
    result = dict(native_cells=[dict(cell_id=index,goals=int(mass[0]),expected_goals=float(mass[1]),attempts=int(mass[2]))
                                for index,mass in enumerate(native)],
        unmapped=dict(goals=int(unmapped[0]),expected_goals=float(unmapped[1]),attempts=int(unmapped[2])),totals=totals,
        league_goals=league_totals['goals'],league_expected_goals=league_totals['expected_goals'],display_cells=[],
        reference='matched actual offense with virtual neutral goalie; positive ratio is more goals allowed per expected goal than matched league',
        support=_support(len(selected),inferred=['setter'] if selected or league_totals['attempts'] else ()),
        method_id=method,actual_states=_mass_states(events,population))
    league_rate=league_totals['goals']/league_totals['expected_goals'] if league_totals['expected_goals'] > 0 else 0.
    for shape,(goals,expected,n) in zip(geometry(),display,strict=True):
        ratio = 100*((goals/expected)/league_rate-1) if expected > 0 and league_rate > 0 else None
        result['display_cells'].append(dict(cell_id=shape['cell_id'],goals=float(goals),expected_goals=float(expected),attempts=float(n),
            mass_saved=float(expected-goals),ratio=None if ratio is None else float(ratio),unavailable_reason='no_exposure' if ratio is None else None))
    return result


def _danger_histogram(events,population,method):
    edges=[index/100 for index in range(101)]
    counts = [0]*100;goals=[0]*100;expected=[[] for _ in range(100)]
    for row in _paired_rows(events,population):
        probability = row[population+'_probability']
        index = min(99,int(np.searchsorted(edges,probability,side='right'))-1)
        counts[index] += 1
        goals[index] += int(row['outcome'] == 'goal')
        expected[index].append(probability)
    return dict(edges=edges,attempt_counts=counts,goal_mass=goals,
        expected_goal_mass=[fsum(values) for values in expected],totals=_totals(events,population),
        support=_support(sum(counts),inferred=['setter'] if any(counts) else ()),method_id=method,actual_states=_mass_states(events,population))


def _breakdown(events,kind,stratum,method):
    selected = [row for row in _paired_rows(events,'unblocked') if row['shot_type'] == stratum] if kind == 'shot_type' else [
        row for row in _paired_rows(events,'unblocked') if (DANGER[0] if row['neutral_on_net_probability'] < .05 else
            DANGER[1] if row['neutral_on_net_probability'] < .15 else DANGER[2]) == stratum]
    totals = _totals(selected,'unblocked')
    n,goals,expected=(totals[key] for key in ('attempts','goals','expected_goals'))
    return dict(events=n,eligible_weight=n,observed_successes=goals,expected_successes=expected,
        probability=_estimate(expected/n if n else None,method),effect=_estimate((expected-goals)/n if n else None,method),
        support=_support(n,inferred=['setter'] if n else ()),method_id=method)


def _observed_summary(strength,events,league,coverage,source,method):
    games=coverage['actor_games']
    unassigned=len(coverage['unassigned_games'])
    data=_summary_evidence(events,league,source,method,missing=coverage['source_counts_unavailable'],
                           gap=coverage['unquantified_gap'],reasons=coverage['reasons'])
    data.update(reported_boxscore_counts=_reported_counts([actor for _,actor in games],strength,source,method,unassigned=unassigned),
        starts=sum(actor['start_status']=='start' for _,actor in games),
        relief_appearances=sum(actor['start_status']=='relief' for _,actor in games),
        unknown_start_status=sum(actor['start_status']=='unknown' for _,actor in games),
        reported_usage=_usage_rows([actor for _,actor in games],method,source,unassigned,coverage['unassigned_by_team']),
        coverage=_support(len(events),gap=coverage['unquantified_gap'],reasons=coverage['reasons']),games=[])
    for game,actor in games:
        if actor['team'] is None:continue
        rows=[row for row in events if row['game_id']==game['game_id']]
        game_data=_summary_evidence(rows,league,source,method,missing=not game['source_events_available'],gap=actor['source_events_gap'])
        game_data.update(game_id=game['game_id'],date=game['date'],team=actor['team'],opponent=actor['opponent'],
            start_status=actor['start_status'],reported_seconds=actor['reported_seconds'],
            reported_boxscore_counts=_reported_counts([actor],strength,source,method))
        data['games'].append(game_data)
    return data


def _observed_rows(year,person,events,league_references,source_games,source,method):
    from .descriptive import goalie_source_coverage
    player=person['player_id']
    coverage=goalie_source_coverage(person,source_games)
    for strength in (*GOALIE_STRENGTHS,'covered_all'):
        selected=[row for row in events if state_selected(row['physical_state'],strength)]
        league=league_references[strength]
        yield 'goalie_observed',_row(year,player,_observed_summary(strength,selected,league,coverage,source,method),strength=strength)
        for population in POPULATIONS:
            yield 'goalie_danger',_row(year,player,_danger_histogram(selected,population,method),strength=strength,population=population)
            for shot_type in GROUPED_TYPES:
                own_type=[row for row in selected if _type_selected(row,shot_type)]
                yield 'goalie_evidence_map',_row(year,player,_evidence_map(own_type,league['types'][shot_type][population],population,method),
                    strength=strength,population=population,type=shot_type)
        if strength!='covered_all':
            for kind,axis in (('shot_type',TYPES),('danger',DANGER)):
                for stratum in axis:
                    yield 'execution_breakdown',_row(year,player,_breakdown(selected,kind,stratum,method),
                        strength=strength,kind=kind,stratum=stratum)


def _project_variants(design, states, base_state, base_scores, people, participation, base_events):
    from .execution_scores import read_panel
    predictors = {row.key:row for row in design.predictors}
    players = [row['player_id'] for row in people]
    evidence = {}
    for player in players:
        common = _base_actor_evidence(base_state,player,base_events)
        for name,state in states.items():
            current = _actor_evidence(state,design,player,HEADS)
            evidence[name,player] = tuple(dict(common[index],**current[index]) for index in range(3))
    pieces = {name:{player:{} for player in players} for name in states}
    panel_records = {}
    for strength in GOALIE_STRENGTHS[:9]:
        defending,attacking = map(int,strength.split('v'))
        panel = read_panel(base_scores,(attacking,defending,1,1))
        panel_records[strength] = dict(panel_id=panel.panel_id,physical_state=[attacking,defending,1,1],
            events=len(panel.events),origins=len(panel.arrays['origin_cells']),
            events_sha256=next(row['sha256'] for row in base_scores.manifest['files'] if row['path'] == f'panels/{attacking}v{defending}g1.jsonl'),
            arrays_sha256=next(row['sha256'] for row in base_scores.manifest['files'] if row['path'] == f'panels/{attacking}v{defending}g1.npz'))
        for event in panel.events:
            require(event['key'] in predictors and predictors[event['key']].shot_type == TYPES.index(event['shot_type'])
                    and predictors[event['key']].tip == event['tip']
                    and tuple(predictors[event['key']].context['strength']) == panel.strength,
                    'replayed panel predictor key/state/type/tip differs')
        for name,state in states.items():
            continuation = _panel_continuation(state,panel,predictors)
            effects = {player:evidence[name,player][2] for player in players}
            for player,piece in _panel_projections(panel,continuation,effects).items():
                pieces[name][player][strength] = piece
    for name in states:
        for player in players:
            for strength in GOALIE_STRENGTHS:
                members = constituent_states(strength)
                pooled = _pool_projection([pieces[name][player][member] for member in members])
                coefficients,keys,_ = evidence[name,player]
                projection,cells = _finish_projection(design.season,player,strength,[panel_records[member] for member in members],
                    pooled,coefficients,keys,participation.get((player,strength)))
                yield name,projection,cells


def _continuation_event_variant(events, design, variant):
    from .goalie import goalie_logits
    predictors = {row.key:row for row in design.predictors}
    for row in events:
        result = dict(row,stages={key:dict(value) for key,value in row['stages'].items()})
        predictor = predictors.get(row['key'])
        if predictor is not None and row['outcome'] == 'save':
            logits = goalie_logits(variant,predictor,np.array([predictor.proxy_cell]),('goalie',))
            for head,stage in (('h','reattempt'),('d','next_attempt_danger')):
                probability = None if logits[head] is None else float(expit(logits[head][0]))
                result['stages'][stage]['prediction'] = probability
                result['stages'][stage]['reason'] = ('label_unavailable' if result['stages'][stage]['response'] is None else
                    'prediction_unavailable' if probability is None else None)
        yield result


def _stage_summaries(events):
    groups = defaultdict(list)
    for row in events:
        if row['source_status'] != 'included' or row['goalie_id'] is None:
            continue
        for strength in (*GOALIE_STRENGTHS,'covered_all'):
            if not state_selected(row['physical_state'],strength):
                continue
            for game in (None,row['game_id']):
                for state in (None,tuple(row['physical_state'])):
                    for stage in ('reattempt','next_attempt_danger'):
                        evidence = row['stages'][stage]
                        if evidence['response'] is not None and evidence['prediction'] is not None:
                            groups[row['goalie_id'],strength,game,state,stage].append(evidence['prediction'])
    return {key:dict(count=len(values),expected_sum=fsum(values),mean=fsum(values)/len(values)) for key,values in groups.items()}


POINTWISE_ROUNDOFF = 32*np.finfo(np.float64).eps
VARIANTS = (('h-tight',('h',)),('d-tight',('d',)),('h+d-tight',HEADS))


def _pointwise_comparisons(state,variants,predictors):
    from .goalie import goalie_probabilities
    maxima={name:dict.fromkeys((*HEADS,'joint')) for name,_ in VARIANTS}
    counts={name:dict.fromkeys((*HEADS,'joint'),0) for name,_ in VARIANTS}
    cells=np.arange(656,dtype=np.int64)
    for predictor in predictors:
        if not variants:
            break
        for neutralize in ((),('shooter','goalie','coaching')):
            baseline=goalie_probabilities(state,predictor,cells,neutralize)
            for name,variant in variants.items():
                changed=goalie_probabilities(variant,predictor,cells,neutralize)
                for index,head in enumerate(HEADS):
                    if baseline[index] is not None and changed[index] is not None:
                        movement=float(np.max(np.abs(changed[index]-baseline[index])))
                        maxima[name][head]=max(maxima[name][head] or 0.,movement)
                        counts[name][head]+=len(cells)
                if all(value is not None for value in (*baseline,*changed)):
                    movement=float(np.max(np.abs(changed[0]*changed[1]-baseline[0]*baseline[1])))
                    maxima[name]['joint']=max(maxima[name]['joint'] or 0.,movement)
                    counts[name]['joint']+=len(cells)
    result={}
    for name,_ in VARIANTS:
        available=sum(count>0 for count in counts[name].values())
        status='assessed' if available==3 else 'partially_assessed' if available else 'unassessed'
        result[name]=dict(status=status,reason=None if status=='assessed' else
            'one or more frozen head/joint comparisons are unavailable' if available else
            'no completed diagnostic endpoint or supported frozen comparison',
            contexts=len(predictors),origin_rows=656*len(predictors),compared_rows=counts[name],
            maximum_absolute_change=maxima[name],flagged={head:None if value is None else value>1e-5 for head,value in maxima[name].items()})
    return result


def _sensitivity(state, variants, baseline_projections, changed_projections, events, design):
    annual = all(row['status'] == 'not_assessed_for_annual_state' for row in state.probes.values())
    if annual:
        return dict(status='not_assessed_for_annual_state',summary_threshold=1e-4,pointwise_threshold=1e-5,variants=[])
    from .goalie_state import read_goalie_baseline
    descriptor,baseline_binding=read_goalie_baseline(state)
    lookup={row.key:row for row in design.predictors}
    keys=descriptor['selector']['keys']
    require(all(key in lookup for key in keys),'frozen goalie context is absent from bound source replay')
    predictors=tuple(lookup[key] for key in keys)
    pointwise=_pointwise_comparisons(state,variants,predictors)
    probes={head:dict(baseline_status=state.heads[head]['status'],probe_status=state.probes[head]['status'],
                     reason=state.probes[head].get('reason'),comparison=state.probes[head].get('comparison')) for head in HEADS}
    for head in HEADS:
        if probes[head]['probe_status']!='assessed':continue
        actual=pointwise[head+'-tight'];saved=probes[head]['comparison']
        for field,saved_field,count_field in ((head,'maximum_probability_change','compared_probability_rows'),
                                              ('joint','maximum_joint_change','compared_joint_rows')):
            require(actual['compared_rows'][field]==saved[count_field], 'frozen goalie comparison row counts differ from saved individual probe')
            left,right=actual['maximum_absolute_change'][field],saved[saved_field]
            require(left is None and right is None or left is not None and right is not None and abs(left-right)<=POINTWISE_ROUNDOFF,
                    'frozen goalie comparison differs from saved individual probe beyond float64 roundoff')
    frozen=dict(baseline=baseline_binding,descriptor=descriptor,head_probes=probes,roundoff_tolerance=POINTWISE_ROUNDOFF,
                references=['actor','neutral'],origins_per_context=656)
    baseline_stages = _stage_summaries(events)
    comparisons = []
    for name,required in VARIANTS:
        if name not in variants:
            comparisons.append(dict(variant=name,status='unassessed',reason='a required tighter head has no completed diagnostic endpoint',
                unavailable_heads=[head for head in required if state.probes[head]['status'] != 'assessed'],
                projections=[],actual_summaries=[],maximum_probability_change=None,flagged=False,pointwise=pointwise[name]))
            continue
        rows,changes = [],[]
        for key,baseline in sorted(baseline_projections.items()):
            changed = changed_projections[name][key]
            values = []
            for field in (*CONTINUATION,*(field+'_difference' for field in CONTINUATION)):
                left,right = baseline['values'][field],changed['values'][field]
                difference = None if left is None or right is None else abs(right-left)
                if difference is not None:
                    changes.append(difference)
                values.append(dict(field=field,baseline=left,variant=right,absolute_change=difference))
            neutral_values=[]
            for field in CONTINUATION:
                left,right=baseline['neutral_values'][field],changed['neutral_values'][field]
                difference=None if left is None or right is None else abs(right-left)
                if difference is not None:
                    changes.append(difference)
                neutral_values.append(dict(field=field,baseline=left,variant=right,absolute_change=difference))
            for field in FIELDS:
                if field.removesuffix('_difference') not in CONTINUATION:
                    require(baseline['values'][field] == changed['values'][field], 'goalie continuation changed a base-stage projection')
            rows.append(dict(player_id=key[0],strength=key[1],values=values,neutral_values=neutral_values,
                baseline_masses=baseline['masses']['continuation'],variant_masses=changed['masses']['continuation']))
        variant_events=list(_continuation_event_variant(events,design,variants[name]))
        variant_stages=_stage_summaries(variant_events)
        require(set(variant_stages)==set(baseline_stages),'continuation changed matched stage populations')
        actual=[]
        for key,left in sorted(baseline_stages.items(),key=lambda row:repr(row[0])):
            right=variant_stages[key]
            require(left['count']==right['count'],'continuation changed matched stage count')
            difference=abs(right['mean']-left['mean']);changes.append(difference)
            actual.append(dict(player_id=key[0],strength=key[1],game_id=key[2],physical_state=None if key[3] is None else list(key[3]),
                stage=key[4],count=left['count'],baseline_mean=left['mean'],variant_mean=right['mean'],absolute_change=difference,
                baseline_expected_sum=left['expected_sum'],variant_expected_sum=right['expected_sum'],
                expected_mass_change=right['expected_sum']-left['expected_sum']))
        maximum=max(changes,default=0.)
        comparisons.append(dict(variant=name,status='assessed',reason=None,unavailable_heads=[],projections=rows,
            actual_summaries=actual,maximum_probability_change=maximum,flagged=maximum>1e-4,pointwise=pointwise[name]))
    return dict(status='assessed' if all(row['status']=='assessed' for row in comparisons) else 'partially_assessed'
                if any(row['status']=='assessed' for row in comparisons) else 'unassessed',
                summary_threshold=1e-4,pointwise_threshold=1e-5,variants=comparisons,frozen_contexts=frozen)


def _method(design, state, sensitivity, projection_member):
    import hashlib
    from .analysis_publication import json_bytes
    method_id='goalie-v1-07-'+design.season
    history=[year for year in design.seasons if year<=design.season]
    inputs=[dict(role='prepared',sha256=design.prepared['sha256'],seasons=history),
            dict(role='coaches',sha256=design.coaches['sha256'],seasons=history),
            dict(role='annual_state',sha256=identity(state.path)['sha256'],seasons=[design.season]),
            dict(role='opportunity_panel',sha256=design.base_scores['sha256'],seasons=[design.season])]
    previous=state.manifest['previous']
    if previous is not None:
        inputs.append(dict(role='predecessor',sha256=previous['sha256'],seasons=[previous['season']]))
    evidence=[dict(uri=str(state.path),sha256=identity(state.path)['sha256']),
              dict(uri=str(projection_member),sha256=identity(projection_member)['sha256']),
              dict(uri=str(projection_member.parent/'sensitivity.json'),sha256=identity(projection_member.parent/'sensitivity.json')['sha256']),
              dict(uri=design.base_scores['path'],sha256=design.base_scores['sha256'])]
    maximum=max((row['maximum_probability_change'] for row in sensitivity['variants']
                 if row['maximum_probability_change'] is not None),default=None)
    numerical=('not assessed for this annual state; remaining optimizer accuracy is unknown' if sensitivity['status']=='not_assessed_for_annual_state'
               else sensitivity['status']+'; '+('no completed summary probability comparison' if maximum is None else 'maximum summary probability movement '+str(maximum))+'; remaining optimizer accuracy is unknown')
    if sensitivity['status']!='not_assessed_for_annual_state':
        if maximum is not None:
            numerical+='; '+('summary sensitivity flagged above 1e-4' if any(row['flagged'] for row in sensitivity['variants']) else
                'no assessed summary exceeds 1e-4')
        pointwise=[maximum for row in sensitivity['variants'] for maximum in row['pointwise']['maximum_absolute_change'].values() if maximum is not None]
        numerical+='; '+('no completed frozen pointwise comparison' if not pointwise else
            'maximum frozen pointwise h/d/joint probability movement '+str(max(pointwise))+'; '+
            ('frozen pointwise sensitivity flagged above 1e-5' if any(flag is True for row in sensitivity['variants'] for flag in row['pointwise']['flagged'].values()) else
             'no assessed frozen pointwise comparison exceeds 1e-5'))
    baseline_status='; '.join(head+': '+state.heads[head]['status']+(' ('+', '.join(state.heads[head]['reasons'])+')' if state.heads[head]['reasons'] else '') for head in HEADS)
    limits=['baseline head status: '+baseline_status,
        'goalie execution breakdown uses paired unblocked attempts: observed successes means goals allowed; effect=(expected goals-goals allowed)/N is recorded goals saved per unblocked attempt, not isolated ability',
        'evidence maps retain additive expected-minus-goal mass; ratios are nonadditive and positive means more goals allowed per expected goal than matched league',
        'positively supported annual team affiliation is only a possible-participation coverage reference; missing dated goalie identities leave located gaps without invented games, starts, reported counts or listed-game denominators',
        'official reported fields retain independently supported game subsets and field-specific coverage in source evidence; these splits do not establish exact-state or both-goalie totals',
        'experimental seasonal point estimates, not held-out forecasts or causal isolation; no calibrated intervals',
        'inherited base probabilities, saved-shot weights and generated next-danger targets retain a pre-outcome inferred setter/setup mixture; this is neither an observed pass nor a setter coefficient in h/d',
        'recorded reattempt means the immediately next recorded same-team ordinary attempt within five seconds; this proxy is not tracking, passing or proven goalie rebound control',
        'conditional danger learns fully neutral successor all-attempt targets on the valued positive subset; selection and base-target uncertainty are omitted',
        'current information requires every contributing head to have current likelihood support; partial priors are distinct from all-head current evidence; prior-only coefficients may be evaluated',
        'fixed head-specific entry/carry shrinkage, raw last-supported history and point-prior assumptions can lag changes',
        'stopping-map location texture follows common shot-context weighting and the shared model; it is not independently fitted goalie-specific location coefficients',
        'cross-strength coefficient information and historical borrowing are distinct from current supported role exposure, which supplies cohort minutes only',
        'ev pools 5v5/4v4/3v3; pk pools goalie-perspective 4v5/3v5/3v4; reference panel masses pool before normalization, independent of actual goalie usage',
        'numerical sensitivity: '+numerical+'; completed original baselines are retained under the diagnostic-only 0.01 percentage-point policy',
        'source counts, actual-offense/neutral-goalie paired evidence and common-panel modeled skills have different populations and references; covered-all is supported coverage, not gap-free all-situations']
    return dict(method_id=method_id,family='goalie',recipe_id=design.recipe['name']+':'+design.recipe['version'],
        design_sha256=identity(state.path)['sha256'],input_sha256=hashlib.sha256(json_bytes(inputs)).hexdigest(),
        fit_seasons=history,training_cutoff=design.training_cutoff,
        target='stopping and six separately conditioned seasonal goalie skills; actual matched evidence remains descriptive',
        population='selected-year goalies, including unused backups; head-specific saved-attempt likelihood populations; each field records the union of its contributing current likelihood keys',
        reference='common-panel focal goalie versus zero actor residuals: miss given unblocked; recorded stop given on-net; conversion given on-net and no recorded stop; reattempt given neutral saved-shot opportunity; next danger given recorded reattempt; joint follow-up danger per neutral saved-shot opportunity. stopping is favorable-positive goals saved per100 common on-net opportunities and excludes focal q. h*d is averaged jointly using fixed neutral saved-shot weights. raw probabilities increase with the named event; focal-minus-neutral differences are fractions. actual evidence keeps offense/coaches and neutralizes only goalie. next-attempt targets neutralize every actor.',
        limitations=limits,evidence=evidence,purpose=design.purpose,inputs=inputs,reference_id='goalie-v1-07-neutral-execution',
        support_policy_id='goalie-v1-07-head-union-and-exact-elapsed',assessment=dict(status='experimental',findings=[dict(
            quantities=[*(f'goalie_result.{field}' for field in FIELDS),'goalie_observed.stage_evidence.reattempt','goalie_observed.stage_evidence.next_attempt_danger'],
            population='all selected annual goalies and declared common-panel/actual matched populations',summary='; '.join(limits),evidence=evidence)]))


def _coverage(target_summary, source_games, people, events, row_counts, head_status):
    from .descriptive import goalie_source_coverage
    source={row['key']:row for row in events}
    source_keys={key for key,row in source.items() if row['source_status']=='included'}
    numerical={key for key,row in source.items() if row['base_status']=='complete'}
    paired={row['key'] for row in events if row['paired']}
    stage=[]
    for name in ('miss','recorded_stop','conversion','reattempt','next_attempt_danger'):
        groups=defaultdict(Counter)
        for row in events:
            record=row['stages'][name]
            state=None if row['physical_state'] is None else tuple(row['physical_state'])
            group=groups[row['goalie_id'],state]
            group['source_events']+=1
            if record['response'] is not None:
                group['known_labels']+=1
                if record['prediction'] is not None:
                    group['matched']+=1
                else:
                    group['prediction_unavailable']+=1
            else:
                group['label_unavailable']+=1
        for (player,state),counts in sorted(groups.items(),key=lambda row:repr(row[0])):
            stage.append(dict(stage=name,goalie_id=player,physical_state=None if state is None else list(state),
                source_events=counts['source_events'],known_labels=counts['known_labels'],matched=counts['matched'],
                prediction_unavailable=counts['prediction_unavailable'],label_unavailable=counts['label_unavailable']))
    return dict(targets=target_summary,events=len(events),source_included=len(source_keys),paired_unblocked=len(paired),
        baseline_head_status=head_status,
        team_unavailable_games=sorted([row for person in people for row in goalie_source_coverage(person,source_games)['unassigned_games']],
            key=lambda row:(row['game_id'],row['player_id'],row['reason'])),
        stage_prediction_reasons=[dict(code=code,count=count) for code,count in sorted(Counter(value['reason'] for row in events
            for value in row['stages'].values() if value['prediction'] is None and value['response'] is not None).items())],
        source_only=sorted(source_keys-numerical),numerical_only=sorted(numerical-source_keys),stage_dispositions=stage,
        event_exclusions=[dict(code=code,count=count) for code,count in sorted(Counter(reason for row in events for reason in row['exclusions']).items())],
        row_counts=dict(sorted(row_counts.items())))


def score_goalie(state, prepared, coaches, annual_execution_scores, output):
    """one source replay, unchanged base panels, streamed publication rows, then manifest-last."""
    from contextlib import ExitStack
    from dataclasses import replace
    from .analysis_data import PreparedManifest, read_prepared
    from .descriptive import goalie_source_season
    from .goalie import prepare_goalie_scoring
    from .goalie_state import GoalieState, read_goalie_state, read_goalie_probe
    started=perf_counter()
    if not isinstance(state,GoalieState):
        state_path=input_path(state,strict=True)
        header=read_json(state_path/'manifest.json' if state_path.is_dir() else state_path)
        require(type(header) is dict and header.get('purpose') in ('real','fixture'),'invalid goalie state manifest purpose')
        state=read_goalie_state(state,header['purpose'])
    require(state.usage=='annual','goalie scores require the original annual baseline')
    if not isinstance(prepared,PreparedManifest):
        prepared=read_prepared(prepared,state.manifest['purpose'])
    output=output_path(str(output),[str(prepared.directory),str(state.path.parent),str(input_path(coaches).parent)])
    if state.manifest['purpose']=='real':
        require(output.is_relative_to('/Volumes/Expansion/hockey-stats'),'expensive real outputs must be external')
    design=prepare_goalie_scoring(prepared,coaches,annual_execution_scores,state.manifest['season'])
    for name in ('prepared','coaches','base_state','base_scores'):
        require(same_input_reference(state.manifest[name],getattr(design,name)),'goalie scoring '+name+' binding differs')
    require(list(design.targets)==state.coverage['targets'],'goalie scoring target replay differs from fitted targets')
    source=goalie_source_season(prepared,design.season,list(design.source_games))
    base_state,base_scores=design.execution_state,design.execution_scores
    base_events={row['key']:row for row in base_scores.events()}
    events=list(_event_values(design,state,base_state,base_events))
    require(set(base_events) <= {row['key'] for row in events},'base score event is absent from source replay')
    input_seconds=perf_counter()-started
    variants={}
    for head in HEADS:
        if state.probes[head]['status']=='assessed':
            variants[head+'-tight']=read_goalie_probe(state,head)
    if set(variants)=={'h-tight','d-tight'}:
        variants['h+d-tight']=replace(state,heads=dict(variants['h-tight'].heads,d=variants['d-tight'].heads['d']),
            arrays=dict(variants['h-tight'].arrays,d=variants['d-tight'].arrays['d']),usage='h+d-tight')
    states=dict(baseline=state,**variants)
    output.mkdir()
    write_jsonl(output/'people.jsonl',source['people'])
    write_jsonl(output/'source_games.jsonl',design.source_games)
    write_jsonl(output/'event_values.jsonl',events)
    write_jsonl(output/'targets.jsonl',design.targets)
    method='goalie-v1-07-'+design.season
    baseline_projections={};baseline_maps={};changed_projections={name:{} for name in variants};counts=Counter()
    projection_started=perf_counter()
    with ExitStack() as stack:
        handles={table:stack.enter_context((output/(table+'.jsonl')).open('xb')) for table in PUBLIC_TABLES}
        projections=stack.enter_context((output/'projections.jsonl').open('xb'))
        for name,projection,cells in _project_variants(design,states,base_state,base_scores,source['people'],source['participation'],base_events):
            key=projection['player_id'],projection['strength']
            if name!='baseline':
                require(cells is None and baseline_maps[key] is None or cells is not None and baseline_maps[key] is not None
                        and np.array_equal(cells,baseline_maps[key]),'goalie continuation changed a native stopping map')
                changed_projections[name][key]=projection
                continue
            baseline_projections[key]=projection
            if variants:
                baseline_maps[key]=cells
            projections.write(json_line(projection))
            for table,row in _modeled_rows(projection,cells,method):
                handles[table].write(json_line(row));counts[table]+=1
        by_player=defaultdict(list)
        for row in events:
            if row['goalie_id'] is not None:
                by_player[row['goalie_id']].append(row)
        source_ref=dict(kind='source',id=source['sources'][0]['source_id'])
        league_references=_league_references(events)
        for person in source['people']:
            player=person['player_id']
            for table,row in _observed_rows(design.season,person,by_player[player],league_references,design.source_games,source_ref,method):
                handles[table].write(json_line(row));counts[table]+=1
    projection_seconds=perf_counter()-projection_started
    sensitivity_started=perf_counter()
    sensitivity=_sensitivity(state,variants,baseline_projections,changed_projections,events,design)
    write_json(output/'sensitivity.json',sensitivity)
    coverage=_coverage(design.coverage,design.source_games,source['people'],events,counts,{head:state.heads[head]['status'] for head in HEADS})
    write_json(output/'coverage.json',coverage)
    catalogs=dict(sources=source['sources'],methods=[_method(design,state,sensitivity,output/'projections.jsonl')],supports=[])
    write_json(output/'catalogs.json',catalogs)
    files=[dict(path=path,sha256=identity(output/path)['sha256'],role=role) for path,role in sorted(MEMBERS.items())]
    previous=state.manifest['previous']
    state_binding=dict(identity(state.path),season=design.season,purpose=design.purpose,recipe_sha256=design.recipe['sha256'],
        previous=None if previous is None else {key:previous[key] for key in ('path','sha256')})
    manifest=dict(schema_version=1,kind='goalie-scores',purpose=design.purpose,season=design.season,recipe=design.recipe,
        implementation=implementation(),prepared=design.prepared,coaches=design.coaches,state=state_binding,
        base_state=design.base_state,base_scores=design.base_scores,training_cutoff=design.training_cutoff,files=files,
        coverage=dict(path='coverage.json'),resources=dict(wall_seconds=perf_counter()-started,input_read_wall_seconds=input_seconds,
            projection_wall_seconds=projection_seconds,sensitivity_wall_seconds=perf_counter()-sensitivity_started,validation_wall_seconds=0.,
            peak_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            output_bytes=sum((output/path).stat().st_size for path in MEMBERS)),
        numerical_sensitivity=dict(status=sensitivity['status'],path='sensitivity.json'))
    validation_started=perf_counter()
    result=_validate_scores(output/'manifest.json',manifest,design.purpose)
    manifest['resources']['validation_wall_seconds']=perf_counter()-validation_started
    manifest['resources']['wall_seconds']=perf_counter()-started
    manifest['resources']['peak_memory_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    write_json(output/'manifest.json',manifest)
    return result


@dataclass(frozen=True)
class GoalieScores:
    path: Path
    manifest: dict
    people: dict
    catalogs: dict
    coverage: dict
    numerical_sensitivity: dict
    projections: dict

    def rows(self,table):
        """yield contiguous ascending person groups; selectors retain their declared native order."""
        require(table in PUBLIC_TABLES,'unknown goalie score table')
        for row in read_jsonl(self.path.parent/(table+'.jsonl')):
            if table=='goalie_result':
                row=enrich_goalie_row(row,self.projections.get((row['player_id'],row['strength'])),
                    'goalie-v1-07-'+self.manifest['season'])
            yield row


@dataclass(frozen=True)
class GoalieProjectionEvidence:
    path: Path
    manifest: dict
    projections: dict


def read_goalie_projection_evidence(score_manifest,expected_binding):
    """read only one selected annual manifest and its published projection proof."""
    from .execution_design import RECIPE as BASE_RECIPE
    require_fields(expected_binding,('season','purpose','prepared_sha256','score_sha256','method','base_method','player_ids'),
                   'goalie projection selection')
    path=input_path(score_manifest, strict=True)
    path=path/'manifest.json' if path.is_dir() else path
    require(path.name=='manifest.json','goalie projection locator must be manifest.json')
    digest(expected_binding['score_sha256']);digest(expected_binding['prepared_sha256'])
    require(identity(path)['sha256']==expected_binding['score_sha256'],'selected goalie score digest differs')
    manifest=read_json(path)
    _score_manifest(manifest,expected_binding['purpose'])
    year=expected_binding['season']
    require(manifest['season']==year and manifest['prepared']['sha256']==expected_binding['prepared_sha256'],
            'selected goalie projection year/preparation differs')
    method,base_method=expected_binding['method'],expected_binding['base_method']
    require(method['method_id']=='goalie-v1-07-'+year and method['family']=='goalie' and method['purpose']==manifest['purpose']
            and method['design_sha256']==manifest['state']['sha256'],'published goalie method/state differs')
    require(method['recipe_id']==manifest['recipe']['name']+':'+manifest['recipe']['version']
            and method['training_cutoff']==manifest['training_cutoff']
            and method['reference_id']=='goalie-v1-07-neutral-execution'
            and method['support_policy_id']=='goalie-v1-07-head-union-and-exact-elapsed',
            'published goalie method meaning differs')
    inputs={row['role']:row for row in method['inputs']}
    require(len(inputs)==len(method['inputs']),'duplicate goalie method input role')
    for role,member in (('prepared','prepared'),('coaches','coaches'),('annual_state','state'),('opportunity_panel','base_scores')):
        require(role in inputs and inputs[role]['sha256']==manifest[member]['sha256'] and year in inputs[role]['seasons'],
                'published goalie method input differs: '+role)
    require(base_method['method_id']=='execution-v1-06-'+year and base_method['family']=='execution'
            and base_method['purpose']==manifest['purpose'],'goalie corrected execution method differs')
    require(base_method['recipe_id']==BASE_RECIPE['name']+':'+BASE_RECIPE['version']
            and base_method['training_cutoff']==manifest['training_cutoff']
            and base_method['reference_id']=='reference-execution-zero'
            and base_method['support_policy_id']=='execution-v1-06-matched-reference-v1',
            'goalie corrected execution method meaning differs')
    require(any(row['role']=='annual_state' and row['seasons']==[year] and row['sha256']==manifest['base_state']['sha256']
                for row in base_method['inputs']),'goalie corrected execution state differs')
    require(any(row['sha256']==manifest['base_scores']['sha256'] and row['uri']==manifest['base_scores']['path']
                for row in base_method['evidence']),'goalie target is not the published corrected execution')
    require(any(row['role']=='coaches' and row['sha256']==manifest['coaches']['sha256'] for row in base_method['inputs']),
            'goalie/combined execution coaches differ')
    files=manifest['files'];require(type(files) is list,'missing goalie score members')
    members={}
    for row in files:
        require_fields(row,('path','sha256','role'),'goalie score member')
        require(row['path'] in MEMBERS and row['path'] not in members and row['role']==MEMBERS[row['path']],
                'unknown/duplicate/cross-wired goalie score member')
        digest(row['sha256']);members[row['path']]=row
    require(set(members)==set(MEMBERS),'goalie score member omitted')
    projection=path.parent/'projections.jsonl'
    require(any(row['uri']==str(projection) and row['sha256']==members['projections.jsonl']['sha256'] for row in method['evidence']),
            'published goalie method does not bind the selected projection')
    require(identity(projection)['sha256']==members['projections.jsonl']['sha256'],'selected goalie projection digest differs')
    people=expected_binding['player_ids']
    require(type(people) is list and people==sorted(set(people)) and all(type(player) is str and player.isdigit() for player in people),
            'invalid selected goalie population')
    projections={}
    for row in read_jsonl(projection):
        validate_goalie_projection(row,year)
        key=row['player_id'],row['strength']
        require(key not in projections,'duplicate selected goalie projection')
        projections[key]=row
    require(set(projections)=={(player,strength) for player in people for strength in GOALIE_STRENGTHS},
            'selected goalie projection matrix differs')
    return GoalieProjectionEvidence(path,manifest,projections)


def read_goalie_scores(path,expected_purpose):
    """read and validate only members contained in this annual score artifact."""
    try:
        path=input_path(path, strict=True)
        path=path/'manifest.json' if path.is_dir() else path
        require(path.name=='manifest.json','goalie scores locator must be manifest.json')
        return _validate_scores(path,read_json(path),expected_purpose)
    except (KeyError,TypeError,ValueError,IndexError,AttributeError) as error:
        if isinstance(error,InputContractError):
            raise
        raise InputContractError('malformed goalie scores: '+str(error)) from error


def _score_manifest(value,purpose):
    from datetime import date
    from .goalie import RECIPE
    from .execution_design import RECIPE as BASE_RECIPE
    from .execution_state import require_state_reference
    require_fields(value,MANIFEST_KEYS,'goalie score manifest')
    require(type(value['schema_version']) is int and value['schema_version']==1 and value['kind']=='goalie-scores',
            'invalid goalie score schema')
    require(purpose in ('real','fixture') and value['purpose']==purpose,'goalie score purpose differs')
    year=require_season_label(value['season'])
    require(year in ('20212022','20222023','20232024','20242025','20252026'),'goalie score year outside scope')
    require(value['recipe']==RECIPE,'goalie score recipe differs')
    for name,keys in (('prepared',('path','sha256','purpose','members')),('coaches',('path','sha256','purpose','selected_game_ids')),
                      ('base_state',('path','sha256','season','purpose','recipe_sha256','usage','previous')),
                      ('base_scores',('path','sha256')),('state',('path','sha256','season','purpose','recipe_sha256','previous'))):
        require_fields(value[name],keys,'goalie score '+name);require_state_reference(value[name],name)
    require(value['prepared']['purpose']==value['coaches']['purpose']==purpose,'goalie source purposes differ')
    games=[];member_keys=[]
    for row in value['prepared']['members']:
        require_fields(row,('kind','season','game_id','path','sha256'),'goalie prepared member')
        require(row['kind'] in ('game','people') and row['season']==year,'goalie prepared member year/kind differs')
        digest(row['sha256']);member_keys.append((row['kind'],row['game_id']))
        if row['kind']=='game':games.append(row['game_id'])
    require(len(member_keys)==len(set(member_keys)) and ('people',None) in member_keys
            and value['coaches']['selected_game_ids']==games,'goalie selected source game bindings differ')
    for name,recipe in (('base_state',BASE_RECIPE),('state',RECIPE)):
        row=value[name]
        require(row['purpose']==purpose and row['season']==year and row['recipe_sha256']==recipe['sha256'],name+' annual binding differs')
        if row['previous'] is not None:
            require_fields(row['previous'],('path','sha256'),name+' predecessor');require_state_reference(row['previous'],name+' predecessor')
        elif purpose=='real':
            require(year=='20212022',name+' real chain omitted predecessor')
    require(value['base_state']['usage']=='annual','goalie base state is not annual')
    cutoff=date.fromisoformat(value['training_cutoff'])
    require(int(year[:4])<=cutoff.year<=int(year[4:]),'goalie score cutoff outside season')
    producer=value['implementation']
    require_fields(producer,('git_commit','git_dirty','python_version','numpy_version','scipy_version','lockfile_sha256'),'goalie score implementation')
    require(type(producer['git_commit']) is str and len(producer['git_commit'])==40
            and all(c in '0123456789abcdef' for c in producer['git_commit']) and type(producer['git_dirty']) is bool,
            'invalid goalie score implementation identity')
    for key in ('python_version','numpy_version','scipy_version'):
        require(type(producer[key]) is str and producer[key],'missing goalie dependency identity')
    digest(producer['lockfile_sha256'])
    if purpose=='real':
        from .artifacts import clean_implementation
        clean_implementation(producer)
    require(value['coverage']==dict(path='coverage.json'),'goalie coverage role differs')
    require_fields(value['numerical_sensitivity'],('status','path'),'goalie sensitivity binding')
    require(value['numerical_sensitivity']['path']=='sensitivity.json','goalie sensitivity role differs')
    costs=value['resources'];require_fields(costs,('wall_seconds','input_read_wall_seconds','projection_wall_seconds','sensitivity_wall_seconds','validation_wall_seconds','peak_memory_bytes','output_bytes'),'goalie score resources')
    for key,val in costs.items():
        require_number(val,key,low=0.) if key.endswith('seconds') else require_count(val,key)


def _validate_event_value(row,manifest,source,target):
    fields=('season','game_id','source_index','key','goalie_id','physical_state','outcome','shot_type','source_status','base_status','paired',
            'origin_cell','on_net_probability','unblocked_probability','neutral_on_net_probability','stages','continuation_probabilities','base_heads','exclusions')
    require_fields(row,fields,'goalie event values')
    require(row['season']==manifest['season'] and row['key']==f"{row['game_id']}:{row['source_index']}"
            and row['key']==target['key'],'goalie numerical focal identity differs')
    for left,right in (('goalie_id','goalie_id'),('physical_state','state'),('outcome','outcome'),('shot_type','model_type'),
                       ('source_status','status'),('origin_cell','origin_cell')):
        require(row[left]==source[right],'goalie numerical/source '+left+' differs')
    require(row['base_status'] in (None,'complete','excluded') and type(row['paired']) is bool,'invalid goalie pair disposition')
    paired=source['status']=='included' and source['outcome']!='block' and source['model_type'] in TYPES and row['base_status']=='complete'
    require(row['paired']==paired,'goalie pair population differs')
    for key in ('on_net_probability','unblocked_probability','neutral_on_net_probability'):
        value=row[key]
        applicable=paired and (key!='on_net_probability' or row['outcome'] in ('save','goal'))
        require((value is not None)==applicable,'goalie conditional probability population differs')
        if value is not None:require_number(value,key,low=0.,high=1.)
    require(type(row['exclusions']) is list and all(type(code) is str and code for code in row['exclusions'])
            and bool(row['exclusions']) is not paired,'goalie pair exclusion reason differs')
    require(row['base_heads'] is None or type(row['base_heads']) is dict and set(row['base_heads'])=={'u','q','r','g'},'invalid base head disposition axis')
    if row['base_heads'] is not None:
        for value in row['base_heads'].values():
            require_fields(value,('included','target','reasons'),'base likelihood disposition')
            require(type(value['included']) is bool and type(value['reasons']) is list and
                    (value['target'] in (0.,1.) and type(value['target']) is float and not value['reasons'] if value['included'] else
                     value['target'] is None and bool(value['reasons'])),'invalid base likelihood disposition')
    require_fields(row['continuation_probabilities'],('actor','neutral_goalie'),'continuation references')
    for values in row['continuation_probabilities'].values():
        require_fields(values,HEADS,'continuation heads')
        for key,value in values.items():
            if value is not None:require_number(value,key,low=0.,high=1.)
    require_fields(row['stages'],('miss','recorded_stop','conversion','reattempt','next_attempt_danger'),'goalie stages')
    expected_labels=dict(miss=int(source['outcome']=='miss') if source['status']=='included' and source['outcome']!='block' else None,
        recorded_stop=int(source['recorded_stop']) if source['outcome'] in ('save','goal') and source['recorded_stop'] is not None else None,
        conversion=int(source['outcome']=='goal') if source['outcome'] in ('save','goal') and source['recorded_stop'] is False else None,
        reattempt=int(source['recorded_reattempt']) if source['outcome']=='save' and source['recorded_reattempt'] is not None else None,
        next_attempt_danger=target['d_target'])
    for key,value in row['stages'].items():
        require_fields(value,('response','prediction','reason'),'goalie matched stage')
        require(value['response']==expected_labels[key],'goalie stage response differs from source label/target')
        if value['prediction'] is not None:require_number(value['prediction'],key,low=0.,high=1.)
        require((value['reason'] is None)==(value['response'] is not None and value['prediction'] is not None), 'goalie stage disposition differs')
    for head,stage in (('h','reattempt'),('d','next_attempt_danger')):
        require(row['stages'][stage]['prediction']==row['continuation_probabilities']['neutral_goalie'][head], 'continuation event stage/reference differs')


def _validate_mass_record(record,size):
    require_fields(record,('log_masses','masses'),'goalie reference mass')
    require(type(record['masses']) is list and type(record['log_masses']) is list
            and len(record['masses'])==len(record['log_masses'])==size,'goalie reference mass axis differs')
    for log_value,mass in zip(record['log_masses'],record['masses'],strict=True):
        if mass is None:
            require(log_value is None,'unsupported goalie mass retained a log')
        else:
            require_number(mass,'goalie reference mass',low=0.)
            require(log_value is None and mass==0. or type(log_value) in (int,float) and isfinite(log_value)
                    and log_value<=np.log(np.finfo(float).max)
                    and isclose(mass,float(np.exp(log_value)),rel_tol=1e-12,abs_tol=0.),'goalie log/reference mass differs')
    for index in range(1,size):
        left,right=record['masses'][index-1:index+1]
        if right is None:continue
        require(left is not None,'goalie downstream mass exists without its conditioning mass')
        earlier,later=record['log_masses'][index-1:index+1]
        require(later is None or earlier is not None and later<=earlier,'goalie reference log mass increases')


def projection_evidence(projection):
    """the finite saved proof carried by an ordinary goalie result."""
    return deepcopy({field:projection[field] for field in ('neutral_values','masses','coefficient_support','panels')})


def enrich_goalie_row(row,projection,method_id):
    """attach a bound saved proof without changing any inherited estimate or support."""
    result=row['result']
    if result['availability']!='provided':
        require(result['data'] is None,'pending goalie result retained a payload')
        return deepcopy(row)
    require(projection is not None,'provided goalie result has no bound projection proof')
    require(all(row[field]==projection[field] for field in ('season','player_id','strength')),
            'goalie result/projection selector differs')
    validate_goalie_projection(projection,row['season'])
    data=result['data']
    require(data['method_id']==method_id,'goalie result method differs from its selected proof')
    require(data['support']==projection['support'],'goalie result support differs from its selected proof')
    for field in FIELDS:
        estimate=data[field]
        missing=projection['unavailable'].get(field)
        require(estimate['value']==projection['values'][field],'goalie result estimate differs from its selected proof: '+field)
        require(estimate['unavailable_reason']==(None if missing is None else missing['reason']),
                'goalie result unavailable reason differs from its selected proof: '+field)
        require(estimate['reason_detail'] is None if missing is None else estimate['reason_detail'] is not None
                and estimate['reason_detail']['explanation']==missing['explanation'],
                'goalie result unavailable explanation differs from its selected proof: '+field)
    evidence=projection_evidence(projection)
    require('evidence' not in data or data['evidence']==evidence,'goalie result retained conflicting saved evidence')
    enriched=deepcopy(row)
    enriched['result']['data']['evidence']=evidence
    return enriched


def validate_goalie_projection(row,season):
    """check the saved conditional algebra without original events or fit arrays."""
    from .analysis_publication import support
    require_fields(row,('season','player_id','strength','values','neutral_values','masses','coefficient_support','support','panels','unavailable'),'goalie projection')
    require_season_label(season)
    require(row['season']==season and type(row['player_id']) is str and row['player_id'].isdigit()
            and row['strength'] in GOALIE_STRENGTHS,
            'goalie projection identity differs')
    require_fields(row['values'],FIELDS,'goalie projection values');require_fields(row['support'],FIELDS,'goalie projection supports')
    require_fields(row['neutral_values'],DEPENDENCIES.keys()-{'stopping_goals_per100_on_net'},'goalie neutral levels')
    for field,value in row['neutral_values'].items():
        if value is not None:require_number(value,'goalie neutral '+field,low=0.,high=1.)
    require_fields(row['coefficient_support'],(*BASE_HEADS,*HEADS),'goalie coefficient heads')
    for head,record in row['coefficient_support'].items():
        require_fields(record,('available','likelihood_events','prior_only','prior_seasons','reason'),'goalie coefficient support')
        require(type(record['available']) is bool and type(record['prior_only']) is bool,'invalid goalie coefficient availability')
        require_count(record['likelihood_events'],'goalie likelihood count')
        require(record['reason'] in (None,'head_incomplete','actor_coefficient_unavailable') and (record['reason'] is None)==record['available'],
                'goalie coefficient unavailable reason differs')
        require(type(record['prior_seasons']) is list and record['prior_seasons']==sorted(set(record['prior_seasons'])), 'invalid goalie prior years')
        for year in record['prior_seasons']:
            require_season_label(year);require(year<season,'goalie coefficient carries future history')
        require(record['available'] or record['likelihood_events']==0,'unavailable goalie coefficient retained likelihood support')
        require(record['prior_only']==(record['available'] and record['likelihood_events']==0),'goalie coefficient prior-only support differs')
    require_fields(row['masses'],('prefixes','continuation'),'goalie projection mass groups')
    for group,size in (('prefixes',4),('continuation',3)):
        require_fields(row['masses'][group],('neutral','focal'),'goalie mass references')
        for name,record in row['masses'][group].items():
            _validate_mass_record(record,size)
            for index,mass in enumerate(record['masses']):
                if group=='prefixes':
                    available=name=='neutral' or index==0 or all(row['coefficient_support'][head]['available'] for head in BASE_HEADS[:index])
                else:
                    heads=HEADS[:index]
                    available=all(row['coefficient_support'][head]['reason']!='head_incomplete' for head in heads) if name=='neutral' else all(row['coefficient_support'][head]['available'] for head in heads)
                require((mass is not None)==available,'goalie reference mass availability differs from its contributing heads')
    require(all(row['masses']['continuation']['neutral'][field][0]==row['masses']['continuation']['focal'][field][0]
                for field in ('masses','log_masses')),'goalie focal continuation changed the fixed neutral saved-shot reference')
    for name in ('neutral','focal'):
        expected=_levels(_restore_logs(row['masses']['prefixes'][name]['log_masses']),
                         _restore_logs(row['masses']['continuation'][name]['log_masses']))
        for field,heads in DEPENDENCIES.items():
            if field=='stopping_goals_per100_on_net':continue
            available=all(row['coefficient_support'][head]['reason']!='head_incomplete' for head in heads) if name=='neutral' else all(row['coefficient_support'][head]['available'] for head in heads)
            actual=row['neutral_values'][field] if name=='neutral' else row['values'][field]
            value=expected[field] if available else None
            require(actual is None and value is None or actual is not None and value is not None and isclose(actual,value,rel_tol=1e-12,abs_tol=1e-15),
                    'goalie level differs from its integrated conditional masses')
    denominators=dict(miss_probability=row['masses']['prefixes']['neutral']['masses'][0],
        recorded_stop_probability=row['masses']['prefixes']['neutral']['masses'][1],
        stopping_goals_per100_on_net=row['masses']['prefixes']['neutral']['masses'][1],
        conversion_probability=row['masses']['prefixes']['neutral']['masses'][2],
        recorded_reattempt_probability=row['masses']['continuation']['neutral']['masses'][0],
        followup_danger=row['masses']['continuation']['neutral']['masses'][0],
        reattempt_neutral_goal_probability=row['masses']['continuation']['neutral']['masses'][1])
    for field,value in row['values'].items():
        require(row['support'][field]['eligible_weight']==denominators[field.removesuffix('_difference')],
                'goalie support denominator is not the neutral unnormalized reference mass')
        if value is not None:require_number(value,field,low=None if field.endswith('_difference') or field.startswith('stopping_') else 0.,
                                      high=None if field.endswith('_difference') or field.startswith('stopping_') else 1.)
        support(row['support'][field])
        heads=DEPENDENCIES[field.removesuffix('_difference')]
        available=all(row['coefficient_support'][head]['available'] for head in heads)
        require(value is None or available,'goalie unsupported dependency produced a value')
        require(row['support'][field]['current_season_information']==
                (available and all(row['coefficient_support'][head]['likelihood_events']>0 for head in heads)), 'goalie field likelihood support differs')
        require(row['support'][field]['prior_only']==(available and all(row['coefficient_support'][head]['prior_only'] for head in heads)),
                'goalie field prior-only dependencies differ')
        require(row['support'][field]['prior_seasons']==sorted({year for head in heads for year in row['coefficient_support'][head]['prior_seasons']}),
                'goalie field prior years differ from its contributing heads')
        if field.endswith('_difference'):
            base=field.removesuffix('_difference')
            expected=None if row['values'][base] is None or row['neutral_values'][base] is None else row['values'][base]-row['neutral_values'][base]
            require(value is None and expected is None or value is not None and expected is not None
                    and isclose(value,expected,rel_tol=1e-12,abs_tol=1e-15),'goalie focal-minus-neutral difference differs')
    require(set(row['unavailable'])=={field for field,value in row['values'].items() if value is None},'goalie unavailable selector matrix differs')
    for value in row['unavailable'].values():
        require_fields(value,('reason','explanation'),'goalie unavailable reason')
        require(value['reason'] in ('no_exposure','failed_fit','missing_source') and type(value['explanation']) is str and value['explanation'],
                'invalid goalie unavailable detail')
    require(type(row['panels']) is list and len(row['panels'])==len(constituent_states(row['strength'])),'goalie panel mixture size differs')
    for record,strength in zip(row['panels'],constituent_states(row['strength']),strict=True):
        require_fields(record,('panel_id','physical_state','events','origins','events_sha256','arrays_sha256'),'goalie panel identity')
        defending,attacking=map(int,strength.split('v'))
        require(type(record['physical_state']) is list and len(record['physical_state'])==4
                and all(type(value) is int for value in record['physical_state']),'invalid goalie panel physical state')
        require(record['physical_state']==[attacking,defending,1,1] and record['panel_id']==f'execution-v1-06-1:{season}:{attacking},{defending},1',
                'goalie panel defending orientation differs')
        require_count(record['events'],'goalie panel events');require_count(record['origins'],'goalie panel origins')
        digest(record['events_sha256']);digest(record['arrays_sha256'])


def _validate_projection(row,manifest,people,likelihood_index):
    validate_goalie_projection(row,manifest['season'])
    require(row['player_id'] in people,'unknown goalie projection person')
    likelihood={head:likelihood_index.get((row['player_id'],head),set()) if record['available'] else set()
                for head,record in row['coefficient_support'].items()}
    for head,record in row['coefficient_support'].items():
        require(record['likelihood_events']==len(likelihood[head]),'goalie coefficient likelihood key count differs')
    for field in FIELDS:
        heads=DEPENDENCIES[field.removesuffix('_difference')]
        require(row['support'][field]['events']==len(set().union(*(likelihood[head] for head in heads))),
                'goalie field likelihood union differs')


def _validate_frozen_contexts(value,manifest,targets):
    import hashlib
    import json
    from .goalie_state import validate_goalie_baseline_descriptor, validate_goalie_probe_comparison
    require_fields(value,('baseline','descriptor','head_probes','roundoff_tolerance','references','origins_per_context'),'goalie frozen contexts')
    require_fields(value['baseline'],('path','sha256'),'goalie frozen baseline reference')
    require(value['baseline']['path']==str(Path(manifest['state']['path']).parent/'baseline.json'),'goalie frozen baseline locator differs')
    digest(value['baseline']['sha256'])
    descriptor=value['descriptor']
    encoded=(json.dumps(descriptor,allow_nan=False,indent=2)+'\n').encode()
    require(hashlib.sha256(encoded).hexdigest()==value['baseline']['sha256'],'copied goalie baseline descriptor digest differs')
    validate_goalie_baseline_descriptor(descriptor,manifest['purpose'],manifest['season'],manifest['recipe']['sha256'],manifest['base_scores'],targets)
    require(value['roundoff_tolerance']==POINTWISE_ROUNDOFF and value['references']==['actor','neutral']
            and value['origins_per_context']==656,'goalie pointwise arithmetic/reference contract differs')
    require_fields(value['head_probes'],HEADS,'goalie frozen head dispositions')
    for head,record in value['head_probes'].items():
        require_fields(record,('baseline_status','probe_status','reason','comparison'),'goalie frozen head probe')
        require(record['baseline_status'] in ('complete','unavailable') and record['probe_status'] in ('assessed','unassessed','not_run'),
                'invalid goalie frozen baseline/probe disposition')
        require((descriptor['heads'][head]['coefficient_sha256'] is not None)==(record['baseline_status']=='complete'),
                'goalie frozen baseline coefficient availability differs')
        if record['probe_status']=='not_run':
            require(record['baseline_status']=='unavailable' and type(record['reason']) is str and record['reason']
                    and record['comparison'] is None,'unavailable goalie baseline invented a probe')
        else:
            complete=record['probe_status']=='assessed'
            require(record['baseline_status']=='complete' and (record['reason'] is None if complete else
                    type(record['reason']) is str and record['reason']),'goalie completed baseline/probe reason differs')
            validate_goalie_probe_comparison(record['comparison'],complete)
            require(record['comparison']['contexts']==len(descriptor['selector']['keys']),'goalie individual probe frozen context count differs')


def _validate_pointwise(value,contexts,available):
    require_fields(value,('status','reason','contexts','origin_rows','compared_rows','maximum_absolute_change','flagged'),'goalie frozen pointwise comparison')
    require(value['contexts']==contexts and type(value['contexts']) is int and value['origin_rows']==656*contexts,'goalie pointwise context/origin counts differ')
    for key in ('compared_rows','maximum_absolute_change','flagged'):
        require_fields(value[key],(*HEADS,'joint'),'goalie pointwise '+key)
    assessed=0
    for field,count in value['compared_rows'].items():
        require(type(count) is int and 0<=count<=2*value['origin_rows'] and count%656==0,'goalie pointwise compared origin count differs')
        maximum=value['maximum_absolute_change'][field]
        require((maximum is None)==(count==0),'goalie pointwise missing evidence became zero error')
        if count:
            require_number(maximum,'goalie pointwise maximum',low=0.,high=1.);assessed+=1
            require(available and type(value['flagged'][field]) is bool and value['flagged'][field]==(maximum>1e-5),
                    'goalie pointwise flag or unavailable endpoint differs')
        else:
            require(value['flagged'][field] is None,'unassessed goalie pointwise movement has a numerical flag')
    h,d,joint=(value['compared_rows'][key] for key in ('h','d','joint'))
    require(max(0,h+d-2*value['origin_rows'])<=joint<=min(h,d),'goalie joint pointwise rows do not intersect head rows')
    expected='assessed' if assessed==3 else 'partially_assessed' if assessed else 'unassessed'
    require(value['status']==expected and (value['reason'] is None if assessed==3 else type(value['reason']) is str and value['reason']),
            'goalie pointwise assessed status differs')


def _validate_sensitivity(value,manifest,people,projections,baseline_actual,targets):
    final=value.get('status')!='not_assessed_for_annual_state'
    if manifest['purpose']=='real':
        require(final==(manifest['season']=='20252026'),'real final-year goalie sensitivity cannot be omitted or claimed for an earlier year')
    require_fields(value,('status','summary_threshold','pointwise_threshold','variants',*(('frozen_contexts',) if final else ())), 'goalie sensitivity')
    require(value['summary_threshold']==1e-4 and value['pointwise_threshold']==1e-5,'goalie sensitivity thresholds differ')
    require(value['status'] in ('not_assessed_for_annual_state','assessed','partially_assessed','unassessed')
            and value['status']==manifest['numerical_sensitivity']['status'],'goalie sensitivity disposition differs')
    require(type(value['variants']) is list,'missing goalie sensitivity variants')
    if value['status']=='not_assessed_for_annual_state':
        require(value['variants']==[],'earlier goalie year claims diagnostic comparisons')
        return
    require([row['variant'] for row in value['variants']]==['h-tight','d-tight','h+d-tight'],'goalie sensitivity variant axis differs')
    _validate_frozen_contexts(value['frozen_contexts'],manifest,targets)
    frozen=value['frozen_contexts'];contexts=len(frozen['descriptor']['selector']['keys'])
    assessed=0
    for variant in value['variants']:
        require_fields(variant,('variant','status','reason','unavailable_heads','projections','actual_summaries','maximum_probability_change','flagged','pointwise'),
                'goalie sensitivity comparison')
        required=dict(VARIANTS)[variant['variant']]
        missing=[head for head in required if frozen['head_probes'][head]['probe_status']!='assessed']
        require(variant['unavailable_heads']==missing and (variant['status']=='assessed')==(not missing),
                'goalie variant failed/unassessed dependency disposition differs')
        _validate_pointwise(variant['pointwise'],contexts,not missing)
        if variant['status']=='unassessed':
            require(type(variant['reason']) is str and variant['reason'] and variant['unavailable_heads']
                    and variant['projections']==variant['actual_summaries']==[]
                    and variant['maximum_probability_change'] is None and variant['flagged'] is False,'unassessed goalie comparison invented evidence')
            continue
        require(variant['status']=='assessed' and variant['reason'] is None and variant['unavailable_heads']==[], 'invalid assessed goalie sensitivity')
        assessed+=1;keys=set();changes=[]
        for row in variant['projections']:
            require_fields(row,('player_id','strength','values','neutral_values','baseline_masses','variant_masses'),'goalie sensitivity projection')
            key=row['player_id'],row['strength'];require(key in projections and key not in keys,'goalie comparison identity duplicate/unknown');keys.add(key)
            for group,fields in (('values',(*CONTINUATION,*(field+'_difference' for field in CONTINUATION))),('neutral_values',CONTINUATION)):
                require(type(row[group]) is list and [v['field'] for v in row[group]]==list(fields),'goalie comparison field axis differs')
                for item in row[group]:
                    require_fields(item,('field','baseline','variant','absolute_change'),'goalie comparison value')
                    baseline=projections[key][group][item['field']]
                    require(item['baseline']==baseline,'goalie comparison baseline differs')
                    if baseline is None or item['variant'] is None:
                        require(item['absolute_change'] is None,'unavailable goalie comparison invented a delta')
                    else:
                        change=abs(item['variant']-baseline)
                        require(item['absolute_change']==change,'goalie sensitivity difference arithmetic differs');changes.append(change)
            require(row['baseline_masses']==projections[key]['masses']['continuation'],'goalie comparison baseline denominators differ')
            for group in ('baseline_masses','variant_masses'):
                require_fields(row[group],('neutral','focal'),'goalie comparison references')
                for record in row[group].values():
                    _validate_mass_record(record,3)
            expected={}
            for reference,record in row['variant_masses'].items():
                baseline=row['baseline_masses'][reference]
                require([mass is None for mass in record['masses']]==[mass is None for mass in baseline['masses']],
                        'goalie diagnostic variant changed coefficient applicability')
                require(all(record[field][0]==baseline[field][0] for field in ('masses','log_masses')),
                        'goalie diagnostic variant changed fixed neutral saved-shot reference mass')
                expected[reference]=_continuation_levels(_restore_logs(record['log_masses']))
                if record['masses'][1] is None:
                    expected[reference]=dict.fromkeys(CONTINUATION)
                elif record['masses'][2] is None:
                    expected[reference]['reattempt_neutral_goal_probability']=None
                    expected[reference]['followup_danger']=None
            for group,reference in (('neutral_values','neutral'),('values','focal')):
                for item in row[group]:
                    field=item['field'];base=field.removesuffix('_difference')
                    expected_value=expected[reference][base]
                    if field.endswith('_difference'):
                        neutral=expected['neutral'][base]
                        expected_value=None if expected_value is None or neutral is None else expected_value-neutral
                    actual=item['variant']
                    if actual is not None:require_number(actual,'goalie diagnostic variant probability/difference',low=-1. if field.endswith('_difference') else 0.,high=1.)
                    require(actual is None and expected_value is None or actual is not None and expected_value is not None
                            and isclose(actual,expected_value,rel_tol=1e-12,abs_tol=1e-15),
                            'goalie diagnostic variant level/difference differs from saved continuation masses')
        require(keys==set(projections),'goalie sensitivity omitted a published goalie-strength')
        actual_keys=set()
        for row in variant['actual_summaries']:
            require_fields(row,('player_id','strength','game_id','physical_state','stage','count','baseline_mean','variant_mean','absolute_change',
                         'baseline_expected_sum','variant_expected_sum','expected_mass_change'),'goalie actual sensitivity')
            require(row['player_id'] in people and row['strength'] in (*GOALIE_STRENGTHS,'covered_all')
                    and row['stage'] in ('reattempt','next_attempt_danger'),'invalid goalie actual comparison key')
            key=(row['player_id'],row['strength'],row['game_id'],None if row['physical_state'] is None else tuple(row['physical_state']),row['stage'])
            require(key in baseline_actual and key not in actual_keys,'unknown/duplicate goalie actual comparison');actual_keys.add(key)
            require(row['count']==baseline_actual[key]['count'] and row['baseline_mean']==baseline_actual[key]['mean']
                    and row['baseline_expected_sum']==baseline_actual[key]['expected_sum'],'goalie actual sensitivity baseline differs')
            require(type(row['count']) is int and row['count']>0,'empty matched sensitivity summary')
            for field in ('baseline_mean','variant_mean'):require_number(row[field],field,low=0.,high=1.)
            require(isclose(row['baseline_mean']*row['count'],row['baseline_expected_sum'],rel_tol=1e-12)
                    and isclose(row['variant_mean']*row['count'],row['variant_expected_sum'],rel_tol=1e-12)
                    and row['expected_mass_change']==row['variant_expected_sum']-row['baseline_expected_sum']
                    and row['absolute_change']==abs(row['variant_mean']-row['baseline_mean']),'goalie actual sensitivity arithmetic differs')
            changes.append(row['absolute_change'])
        require(actual_keys==set(baseline_actual),'goalie sensitivity omitted a nonempty actual evidence summary')
        maximum=max(changes,default=0.)
        require(variant['maximum_probability_change']==maximum and variant['flagged']==(maximum>1e-4),'goalie sensitivity maximum/flag differs')
    require(value['status']==('assessed' if assessed==3 else 'partially_assessed' if assessed else 'unassessed'),'goalie sensitivity overall disposition differs')
    comparisons={row['variant']:row for row in value['variants']}
    for head in HEADS:
        record=frozen['head_probes'][head]
        if record['probe_status']!='assessed':continue
        pointwise=comparisons[head+'-tight']['pointwise'];saved=record['comparison']
        for field,maximum,count in ((head,'maximum_probability_change','compared_probability_rows'),('joint','maximum_joint_change','compared_joint_rows')):
            require(pointwise['compared_rows'][field]==saved[count],'goalie saved/new frozen comparison row counts differ')
            left,right=pointwise['maximum_absolute_change'][field],saved[maximum]
            require(left is None and right is None or left is not None and right is not None and abs(left-right)<=POINTWISE_ROUNDOFF,
                    'goalie individual frozen comparison differs beyond float64 roundoff')
        unchanged='d' if head=='h' else 'h'
        require(pointwise['maximum_absolute_change'][unchanged] in (None,0.),'one-head goalie probe changed the independent other head')
    combined=comparisons['h+d-tight']
    if combined['status']=='assessed':
        require(all(combined['pointwise']['compared_rows']['joint']==comparisons[head+'-tight']['pointwise']['compared_rows']['joint']
                    for head in HEADS),'combined goalie pointwise comparison changed joint applicability')
        for head in HEADS:
            individual=comparisons[head+'-tight']['pointwise'];joint=combined['pointwise']
            require(joint['compared_rows'][head]==individual['compared_rows'][head]
                    and joint['maximum_absolute_change'][head]==individual['maximum_absolute_change'][head],
                    'combined goalie probe changed an independently evaluated head')


def _check_actual_evidence(table,row,selected,league,source_coverage,method,source):
    data=row['result']['data'];strength=row['strength']
    if table=='execution_breakdown':
        require(data==_breakdown(selected,row['kind'],row['stratum'],method),'saved goalie breakdown differs from keyed paired events')
        return
    if table in ('goalie_evidence_map','goalie_danger'):
        population=row['population']
        if table=='goalie_evidence_map':
            selected=[event for event in selected if _type_selected(event,row['type'])]
        require(data['totals']==_totals(selected,population) and data['actual_states']==_mass_states(selected,population),
                'goalie distribution totals differ from keyed matched attempts')
        if table=='goalie_danger':
            require(data==_danger_histogram(selected,population,method),'saved goalie danger bins differ from keyed probabilities')
        else:
            native=np.zeros((656,3));unmapped=np.zeros(3)
            for event in _paired_rows(selected,population):
                mass=[int(event['outcome']=='goal'),event[population+'_probability'],1]
                if event['origin_cell'] is None:unmapped+=mass
                else:native[event['origin_cell']]+=mass
            for index,item in enumerate(data['native_cells']):
                require([item[key] for key in ('goals','expected_goals','attempts')]==list(native[index]),'goalie native evidence deposit differs')
            require([data['unmapped'][key] for key in ('goals','expected_goals','attempts')]==list(unmapped),'goalie unmapped evidence differs')
            totals=league['types'][row['type']][population]
            require(data['league_goals']==totals['goals'] and data['league_expected_goals']==totals['expected_goals'],'goalie matched type/population league differs')
        return
    if table!='goalie_observed':return
    require(data==_observed_summary(strength,selected,league,source_coverage,source,method),
            'goalie season/game evidence differs from checked source assignments and matched events')


def _validate_scores(path,manifest,expected_purpose):
    from . import analysis_publication as public
    from .descriptive import validate_goalie_source_game, goalie_source_coverage
    from .execution_state import require_finite_state
    from .goalie import target_coverage
    from .goalie_state import validate_goalie_target
    _score_manifest(manifest,expected_purpose)
    root=path.parent;files=manifest['files'];require(type(files) is list,'missing goalie score members')
    bound={}
    for row in files:
        require_fields(row,('path','sha256','role'),'goalie score member')
        require(row['path'] in MEMBERS and row['path'] not in bound and row['role']==MEMBERS[row['path']],'unknown/duplicate/cross-wired goalie score member')
        digest(row['sha256']);member=(root/row['path']).resolve(strict=True)
        require(root in member.parents and member.is_file(),'goalie score member escapes artifact')
        require(identity(member)['sha256']==row['sha256'],'goalie score member digest differs');bound[row['path']]=member
    require(set(bound)==set(MEMBERS),'goalie score member omitted')
    actual={str(member.relative_to(root)) for member in root.rglob('*') if member.is_file() and member!=path}
    require(actual==set(MEMBERS),'unbound files in goalie scores')
    require(manifest['resources']['output_bytes']==sum(member.stat().st_size for member in bound.values()),'goalie saved byte cost differs')
    catalogs=read_json(root/'catalogs.json');require_fields(catalogs,('sources','methods','supports'),'goalie score catalogs')
    lookups={key:{} for key in ('source','method','support')}
    for table,singular in (('sources','source'),('methods','method'),('supports','support')):
        require(type(catalogs[table]) is list,'missing goalie catalog')
        for row in catalogs[table]:
            public.validate_catalog(table,row,expected_purpose,lookups,manifest['prepared']['sha256'])
            key=row[singular+'_id'];require(key not in lookups[singular],'duplicate goalie catalog identity');lookups[singular][key]=row
    people={};person_keys={}
    for row in read_jsonl(root/'people.jsonl'):
        public.validate_catalog('people',row,expected_purpose,lookups,manifest['prepared']['sha256'])
        require(row['season']==manifest['season'] and row['kind']=='goalie' and row['player_id'] not in people,'invalid/duplicate goalie annual person')
        people[row['player_id']]=row;person_keys[row['season'],row['player_id']]=row
    source_games=list(read_jsonl(root/'source_games.jsonl'));source_events={}
    require([game['game_id'] for game in source_games]==manifest['coaches']['selected_game_ids'],'goalie source game order differs')
    for game in source_games:
        validate_goalie_source_game(game)
        require(game['season']==manifest['season'],'goalie source game year differs')
        for row in game['events']:
            key=f"{game['game_id']}:{row['source_index']}";require(key not in source_events,'duplicate source focal key');source_events[key]=row
    targets={}
    for row in read_jsonl(root/'targets.jsonl'):
        validate_goalie_target(row,manifest)
        require(row['key'] in source_events and row['key'] not in targets,'unknown/duplicate goalie score target');targets[row['key']]=row
    require(set(targets)==set(source_events),'goalie source/target keys differ')
    events={}
    for row in read_jsonl(root/'event_values.jsonl'):
        require(row['key'] in source_events and row['key'] not in events,'unknown/duplicate goalie score event')
        _validate_event_value(row,manifest,source_events[row['key']],targets[row['key']]);events[row['key']]=row
    require(set(events)==set(source_events),'goalie event/source keys differ')
    likelihood_index=defaultdict(set)
    for key,target in targets.items():
        for head in HEADS:
            if target[head+'_included']:
                likelihood_index[str(target['goalie_id']),head].add(key)
    for key,event in events.items():
        if event['base_heads'] is not None and event['goalie_id'] is not None:
            for head in BASE_HEADS:
                if event['base_heads'][head]['included']:
                    likelihood_index[event['goalie_id'],head].add(key)
    projections={}
    for row in read_jsonl(root/'projections.jsonl'):
        _validate_projection(row,manifest,people,likelihood_index)
        key=row['player_id'],row['strength'];require(key not in projections,'duplicate goalie projection');projections[key]=row
    require(set(projections)=={(player,strength) for player in people for strength in GOALIE_STRENGTHS},'goalie projection matrix incomplete')
    sensitivity=read_json(root/'sensitivity.json');_validate_sensitivity(sensitivity,manifest,people,projections,_stage_summaries(list(events.values())),list(targets.values()))
    require_finite_state(sensitivity,'goalie sensitivity')
    league_references=_league_references(events.values())
    by_selector=defaultdict(list)
    for row in events.values():
        for strength in (*GOALIE_STRENGTHS,'covered_all'):
            if row['goalie_id'] is not None and state_selected(row['physical_state'],strength):
                by_selector[row['goalie_id'],strength].append(row)
    source_coverage={player:goalie_source_coverage(person,source_games) for player,person in people.items()}
    counts=Counter();seen=defaultdict(set)
    method='goalie-v1-07-'+manifest['season'];source=dict(kind='source',id='goalie-source-v1-07-'+manifest['season'])
    require(method in lookups['method'] and source['id'] in lookups['source'],'goalie fixed method/source identities absent')
    for table in PUBLIC_TABLES:
        previous_player=None
        for row in read_jsonl(root/(table+'.jsonl')):
            require(previous_player is None or previous_player<=row['player_id'],'goalie score person groups are not ascending/contiguous')
            previous_player=row['player_id']
            if table=='goalie_result':
                row=enrich_goalie_row(row,projections.get((row['player_id'],row['strength'])),method)
            public.validate_row(table,row,'goalie',lookups,person_keys)
            require(row['season']==manifest['season'] and row['result']['availability']=='provided','goalie score row must be provided in its annual scope')
            key=tuple(row[field] for field in KEYS[table]);require(key not in seen[table],'duplicate goalie public selector');seen[table].add(key);counts[table]+=1
            if table=='goalie_result':
                projection=projections[row['player_id'],row['strength']];payload=row['result']['data']
                require(payload['support']==projection['support'] and payload['evidence']==projection_evidence(projection)
                        and all(payload[field]['value']==projection['values'][field] for field in FIELDS),
                        'goalie public scalar/support differs from saved projection')
            elif table=='analysis_map':
                require(row['result']['data']['integrated_value']==projections[row['player_id'],row['strength']]['values']['stopping_goals_per100_on_net'],
                        'goalie map scalar differs from saved projection')
            else:
                _check_actual_evidence(table,row,by_selector[row['player_id'],row['strength']],league_references[row['strength']],source_coverage[row['player_id']],method,source)
        expected={tuple([manifest['season'],player,*selectors]) for player in people for selectors in public.required_keys(table,'goalie')}
        require(seen[table]==expected,'goalie public required selector matrix incomplete: '+table)
    coverage=read_json(root/'coverage.json')
    require_fields(coverage,('targets','events','source_included','paired_unblocked','baseline_head_status','team_unavailable_games',
                     'stage_prediction_reasons','source_only','numerical_only','stage_dispositions','event_exclusions','row_counts'),'goalie score coverage')
    require_fields(coverage['baseline_head_status'],HEADS,'goalie baseline dispositions')
    require(all(value in ('complete','unavailable') for value in coverage['baseline_head_status'].values()),'invalid goalie baseline status')
    require(coverage==_coverage(target_coverage(list(targets.values()),manifest['season']),source_games,list(people.values()),list(events.values()),counts,coverage['baseline_head_status']),
            'goalie saved coverage differs from source/target/numerical members')
    return GoalieScores(path,manifest,people,catalogs,coverage,sensitivity,projections)
