"""annual goalie projections and matched evidence; saved readers never reopen inputs."""

from collections import Counter, defaultdict
from dataclasses import dataclass
from math import fsum, isclose, isfinite
from pathlib import Path
import resource
from time import perf_counter

import numpy as np
from scipy.special import expit, log_expit, logsumexp

from .artifacts import digest, implementation, require
from .captures import InputContractError
from .chance_cli import identity, output_path, read_json
from .execution_scores import _closed, _count, _jsonl, _line, _number, _season_label, _write_document, _write_jsonl
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


def reference_masses(upstream, goal, setup_weights, origin_weights, continuation, effects):
    """integrate identical origin × setup branches, preserving logs below float underflow.

    effects are the focal goalie's centered residuals; unavailable heads use none.
    continuation carries neutral h/d logits. prefix and continuation sums are unnormalized.
    """
    upstream = np.asarray(upstream, dtype=np.float64)
    goal = np.asarray(goal, dtype=np.float64)
    setup = np.asarray(setup_weights, dtype=np.float64)
    weights = np.asarray(origin_weights, dtype=np.float64)
    n = len(weights)
    require(upstream.shape == (n,3) and goal.shape == setup.shape == (n,2)
            and np.isfinite(upstream).all() and np.isfinite(goal).all()
            and np.isfinite(setup).all() and np.all(setup > 0)
            and np.allclose(setup.sum(axis=1),1,rtol=0,atol=1e-15)
            and weights.shape == (n,) and np.isfinite(weights).all() and np.all(weights >= 0),
            'invalid goalie reference branches')
    require(set(effects) == {'q','r','g','h','d'} and set(continuation) == set(HEADS), 'goalie head axes differ')
    for head, values in continuation.items():
        require(values is None or np.shape(values) == (n,) and np.isfinite(values).all(), head+': invalid neutral logits')
    with np.errstate(divide='ignore'):
        logs = np.log(weights)
    neutral_upstream = log_expit(upstream)
    neutral_goal = log_expit(goal)
    focal_upstream = upstream.copy()
    for index, head in ((1,'q'),(2,'r')):
        if effects[head] is not None:
            focal_upstream[:,index] += effects[head]
    focal_goal = goal + (effects['g'] or 0.)
    prefix = {}
    for name, first, last in (('neutral',neutral_upstream,neutral_goal),
                              ('focal',log_expit(focal_upstream),log_expit(focal_goal))):
        cumulative = np.cumsum(first,axis=1)
        prefix[name] = np.array([*(_log_sum(logs+cumulative[:,i]) for i in range(3)),
                                _log_sum(logs+cumulative[:,2]+logsumexp(np.log(setup)+last,axis=1))])
    # 1-r*g = (1-r) + r*(1-g). this remains positive when expit(r) rounds to one.
    saved = logs+neutral_upstream[:,0]+neutral_upstream[:,1]+logsumexp(
        np.log(setup)+np.logaddexp(log_expit(-upstream[:,2,None]),
                                  neutral_upstream[:,2,None]+log_expit(-goal)),axis=1)
    continuation_mass = {}
    for name in ('neutral','focal'):
        h = continuation['h']
        d = continuation['d']
        h = None if h is None or name == 'focal' and effects['h'] is None else log_expit(h+(effects['h'] if name == 'focal' else 0.))
        d = None if d is None or name == 'focal' and effects['d'] is None else log_expit(d+(effects['d'] if name == 'focal' else 0.))
        continuation_mass[name] = np.array([_log_sum(saved), -np.inf if h is None else _log_sum(saved+h),
                                           -np.inf if h is None or d is None else _log_sum(saved+h+d)])
    # signed per-origin stopping numerator. cancellation is taken before integration.
    neutral_rg = neutral_upstream[:,2,None]+neutral_goal
    focal_rg = log_expit(focal_upstream[:,2,None])+log_expit(focal_goal)
    high = np.maximum(neutral_rg,focal_rg)
    delta = np.exp(high)*(-np.expm1(np.minimum(neutral_rg,focal_rg)-high))
    delta *= np.sign(neutral_rg-focal_rg)
    delta = np.sum(setup*delta,axis=1)
    log_base = logs+neutral_upstream[:,0]+neutral_upstream[:,1]
    positive = np.where(delta > 0, delta, 0.)
    negative = np.where(delta < 0, -delta, 0.)
    with np.errstate(divide='ignore'):
        stopping = (log_base+np.log(positive),log_base+np.log(negative))
    return dict(prefixes=prefix,continuation=continuation_mass,stopping=stopping)


def _levels(prefix, continuation):
    a,b,c,d = prefix
    w,h,hd = continuation
    return dict(miss_probability=None if a == -np.inf else float(-np.expm1(b-a)),
                recorded_stop_probability=None if b == -np.inf else float(-np.expm1(c-b)),
                conversion_probability=_ratio(d,c),recorded_reattempt_probability=_ratio(h,w),
                reattempt_neutral_goal_probability=_ratio(hd,h),followup_danger=_ratio(hd,w))


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


def _projection_log_masses(panel, continuation, effects):
    arrays = panel.arrays
    length = len(arrays['origin_cells'])
    totals = dict(prefixes={name:np.full(4,-np.inf) for name in ('neutral','focal')},
                  continuation={name:np.full(3,-np.inf) for name in ('neutral','focal')},
                  positive=np.full(656,-np.inf),negative=np.full(656,-np.inf))
    for start in range(0,length,65536):
        end = min(length,start+65536)
        event = np.searchsorted(arrays['event_offsets'],np.arange(start,end),side='right')-1
        reduced = reference_masses(arrays['neutral_upstream_logits'][start:end],arrays['neutral_goal_logits'][start:end],
            arrays['setup_weights'][event],arrays['origin_weights'][start:end],
            {head:None if continuation[head] is None else continuation[head][start:end] for head in HEADS},effects)
        for group in ('prefixes','continuation'):
            for name in ('neutral','focal'):
                totals[group][name] = np.logaddexp(totals[group][name],reduced[group][name])
        for name,values in zip(('positive','negative'),reduced['stopping'],strict=True):
            np.logaddexp.at(totals[name],arrays['origin_cells'][start:end],values)
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
            inferred=(['historical_borrowing'] if years else [])+(['blocked_origin'] if any(row['origins'] > row['events'] for row in panels) else []))
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
        support=_support(n),method_id=method)
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
                        'matched_expected_sum':fsum(row['prediction'] for row in selected),'support':_support(len(selected))}
    return result


def _source_counts(events, source, method, *, unavailable=False, gap=False):
    rows = [row for row in events if row['source_status'] == 'included' and row['outcome'] != 'block']
    counts = Counter(row['outcome'] for row in rows)
    n, on_net = len(rows),counts['save']+counts['goal']
    return dict(unblocked_attempts=None if unavailable else n,misses=None if unavailable else counts['miss'],
        shots_on_goal=None if unavailable else on_net,saves=None if unavailable else counts['save'],
        goals_against=None if unavailable else counts['goal'],
        save_percentage=_estimate(counts['save']/on_net if on_net and not unavailable else None,method,
            reason='missing_source' if unavailable else 'no_exposure',explanation='the source collection is unavailable or this identity has no dated game evidence' if unavailable else 'no supported on-net source attempts'),
        support=_support(n,gap=unavailable or gap,reasons=['source_unavailable'] if unavailable or gap else ()),provenance=source)


def _reported_counts(goalies, strength, source, method):
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
    counts.update(save_percentage=_estimate(fraction,method),support=_support(len(goalies),gap=not goalies or any(value < len(goalies) for value in coverage.values()),
        reasons=['source_unavailable'] if not goalies or category is None or any(value < len(goalies) for value in coverage.values()) else ()),provenance=source)
    return counts


def _usage_rows(goalies, method, source, *, team_id=None):
    selected = [row for row in goalies if team_id is None or row['team'] is not None and row['team']['id'] == team_id]
    timed = [row for row in selected if row['reported_seconds'] is not None]
    positive = sum(row['reported_seconds'] > 0 for row in timed)
    seconds = sum(row['reported_seconds'] for row in timed) if timed else None
    shifts = [row['reported_shifts'] for row in selected if row['reported_shifts'] is not None]
    value = dict(positive_toi_appearances=positive,reported_seconds=seconds,
                 minutes_per_appearance=_estimate(seconds/(60*positive) if positive else None,method),
                 reported_shifts=sum(shifts) if shifts else None,listed_games=len(selected),supported_games=len(timed),
                 missing_games=len(selected)-len(timed),support=_support(len(timed),gap=not selected or len(timed)<len(selected),reasons=['source_unavailable'] if not selected else ()))
    if team_id is not None:
        value['team_id'] = team_id
    else:
        value.update(teams=[_usage_rows(selected,method,source,team_id=team) for team in sorted({row['team']['id'] for row in selected if row['team'] is not None})],provenance=source)
    return value


def _summary_evidence(events, league_events, source, method, *, missing=False, gap=False):
    state_groups = defaultdict(list)
    for row in events:
        if row['source_status'] == 'included' and row['physical_state'] is not None:
            state_groups[tuple(row['physical_state'])].append(row)
    result = dict(source_counts=_source_counts(events,source,method,unavailable=missing,gap=gap),
        on_net_evidence=_paired_evidence(events,_totals(league_events,'on_net'),'on_net',method),
        unblocked_evidence=_paired_evidence(events,_totals(league_events,'unblocked'),'unblocked',method),
        stage_evidence=_stage_evidence(events),actual_states=[],provenance=source)
    for state, rows in sorted(state_groups.items()):
        league = [row for row in league_events if row['physical_state'] == list(state)]
        result['actual_states'].append(dict(state=_actual_state(state),source_counts=_source_counts(rows,source,method,gap=gap),
            on_net_evidence=_paired_evidence(rows,_totals(league,'on_net'),'on_net',method),
            unblocked_evidence=_paired_evidence(rows,_totals(league,'unblocked'),'unblocked',method),stage_evidence=_stage_evidence(rows)))
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
    yield 'goalie_result',_row(year,player,dict(**estimates,support=projection['support'],method_id=method),strength=strength)
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


def _mass_states(events,population):
    grouped = defaultdict(list)
    for row in _paired_rows(events,population):
        grouped[tuple(row['physical_state'])].append(row)
    return [dict(state=_actual_state(state),**_totals(rows,population),support=_support(len(rows))) for state,rows in sorted(grouped.items())]


def _evidence_map(events,league,population,method):
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
    league_totals = _totals(league,population)
    display = np.column_stack([native_display_mass(native[:,index]) for index in range(3)]) if selected else np.zeros((668,3))
    result = dict(native_cells=[dict(cell_id=index,goals=int(mass[0]),expected_goals=float(mass[1]),attempts=int(mass[2]))
                                for index,mass in enumerate(native)],
        unmapped=dict(goals=int(unmapped[0]),expected_goals=float(unmapped[1]),attempts=int(unmapped[2])),totals=totals,
        league_goals=league_totals['goals'],league_expected_goals=league_totals['expected_goals'],display_cells=[],
        reference='matched actual offense with virtual neutral goalie; positive ratio is more goals allowed per expected goal than matched league',
        support=_support(len(selected)),method_id=method,actual_states=_mass_states(events,population))
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
        support=_support(sum(counts)),method_id=method,actual_states=_mass_states(events,population))


def _breakdown(events,kind,stratum,method):
    selected = [row for row in _paired_rows(events,'unblocked') if row['shot_type'] == stratum] if kind == 'shot_type' else [
        row for row in _paired_rows(events,'unblocked') if (DANGER[0] if row['neutral_on_net_probability'] < .05 else
            DANGER[1] if row['neutral_on_net_probability'] < .15 else DANGER[2]) == stratum]
    totals = _totals(selected,'unblocked')
    n,goals,expected=(totals[key] for key in ('attempts','goals','expected_goals'))
    return dict(events=n,eligible_weight=n,observed_successes=goals,expected_successes=expected,
        probability=_estimate(expected/n if n else None,method),effect=_estimate((expected-goals)/n if n else None,method),
        support=_support(n),method_id=method)


def _observed_rows(year,player,events,all_events,source_games,source,method):
    games = []
    for game in source_games:
        actor = next((row for row in game['goalies'] if row['player_id'] == player),None)
        if actor is not None:
            games.append((game,actor))
    for strength in (*GOALIE_STRENGTHS,'covered_all'):
        selected = [row for row in events if state_selected(row['physical_state'],strength)]
        league = [row for row in all_events if state_selected(row['physical_state'],strength)]
        missing = not games or all(not game['source_events_available'] for game,actor in games)
        data = _summary_evidence(selected,league,source,method,missing=missing,gap=any(actor['source_events_gap'] for _,actor in games))
        data.update(reported_boxscore_counts=_reported_counts([actor for _,actor in games],strength,source,method),
            starts=sum(actor['start_status']=='start' for _,actor in games),
            relief_appearances=sum(actor['start_status']=='relief' for _,actor in games),
            unknown_start_status=sum(actor['start_status']=='unknown' for _,actor in games),
            reported_usage=_usage_rows([actor for _,actor in games],method,source),
            coverage=_support(len(selected),gap=any(actor['source_events_gap'] for _,actor in games)),games=[])
        for game,actor in games:
            if actor['team'] is None:
                continue
            rows = [row for row in selected if row['game_id'] == game['game_id']]
            game_data = _summary_evidence(rows,league,source,method,missing=not game['source_events_available'],gap=actor['source_events_gap'])
            game_data.update(game_id=game['game_id'],date=game['date'],team=actor['team'],opponent=actor['opponent'],
                start_status=actor['start_status'],reported_seconds=actor['reported_seconds'],
                reported_boxscore_counts=_reported_counts([actor],strength,source,method))
            data['games'].append(game_data)
        yield 'goalie_observed',_row(year,player,data,strength=strength)
        for population in POPULATIONS:
            yield 'goalie_danger',_row(year,player,_danger_histogram(selected,population,method),strength=strength,population=population)
            for shot_type in GROUPED_TYPES:
                own_type = [row for row in selected if _type_selected(row,shot_type)]
                league_type = [row for row in league if _type_selected(row,shot_type)]
                yield 'goalie_evidence_map',_row(year,player,_evidence_map(own_type,league_type,population,method),
                    strength=strength,population=population,type=shot_type)
        if strength != 'covered_all':
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
            for player in players:
                pieces[name][player][strength] = _projection_log_masses(panel,continuation,evidence[name,player][2])
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


def _sensitivity(state, variants, baseline_projections, changed_projections, events, design):
    annual = all(row['status'] == 'not_assessed_for_annual_state' for row in state.probes.values())
    if annual:
        return dict(status='not_assessed_for_annual_state',summary_threshold=1e-4,pointwise_threshold=1e-5,variants=[])
    baseline_stages = _stage_summaries(events)
    comparisons = []
    for name,required in (('h-tight',('h',)),('d-tight',('d',)),('h+d-tight',HEADS)):
        if name not in variants:
            comparisons.append(dict(variant=name,status='unassessed',reason='a required tighter head has no completed diagnostic endpoint',
                unavailable_heads=[head for head in required if state.probes[head]['status'] != 'assessed'],
                projections=[],actual_summaries=[],maximum_probability_change=None,flagged=False))
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
            actual_summaries=actual,maximum_probability_change=maximum,flagged=maximum>1e-4))
    return dict(status='assessed' if all(row['status']=='assessed' for row in comparisons) else 'partially_assessed'
                if any(row['status']=='assessed' for row in comparisons) else 'unassessed',
                summary_threshold=1e-4,pointwise_threshold=1e-5,variants=comparisons)


def _method(design, state, sensitivity, projection_member):
    import hashlib
    from .analysis_publication import json_bytes
    method_id='goalie-v1-07-'+design.season
    inputs=[dict(role='prepared',sha256=design.prepared['sha256'],seasons=[design.season]),
            dict(role='coaches',sha256=design.coaches['sha256'],seasons=[design.season]),
            dict(role='annual_state',sha256=identity(state.path)['sha256'],seasons=[design.season]),
            dict(role='opportunity_panel',sha256=design.base_scores['sha256'],seasons=[design.season])]
    previous=state.manifest['previous']
    if previous is not None:
        inputs.append(dict(role='predecessor',sha256=previous['sha256'],seasons=[previous['season']]))
    evidence=[dict(uri=str(state.path),sha256=identity(state.path)['sha256']),
              dict(uri=str(projection_member),sha256=identity(projection_member)['sha256']),
              dict(uri=design.base_scores['path'],sha256=design.base_scores['sha256'])]
    maximum=max((row['maximum_probability_change'] for row in sensitivity['variants']
                 if row['maximum_probability_change'] is not None),default=None)
    numerical=('not assessed for this annual state; remaining optimizer accuracy is unknown' if sensitivity['status']=='not_assessed_for_annual_state'
               else sensitivity['status']+'; maximum assessed probability movement '+str(maximum)+'; remaining optimizer accuracy is unknown')
    baseline_status='; '.join(head+': '+state.heads[head]['status']+(' ('+', '.join(state.heads[head]['reasons'])+')' if state.heads[head]['reasons'] else '') for head in HEADS)
    limits=['baseline head status: '+baseline_status,
        'goalie execution breakdown uses paired unblocked attempts: observed successes means goals allowed; effect=(expected goals-goals allowed)/N is recorded goals saved per unblocked attempt, not isolated ability',
        'evidence maps retain additive expected-minus-goal mass; ratios are nonadditive and positive means more goals allowed per expected goal than matched league',
        'official reported fields retain independently supported game subsets and field-specific coverage in source evidence; these splits do not establish exact-state or both-goalie totals',
        'experimental seasonal point estimates, not held-out forecasts or causal isolation; no calibrated intervals',
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
        fit_seasons=[year for year in design.seasons if year<=design.season],training_cutoff=design.training_cutoff,
        target='stopping and six separately conditioned seasonal goalie skills; actual matched evidence remains descriptive',
        population='selected-year goalies, including unused backups; head-specific saved-attempt likelihood populations; each field records the union of its contributing current likelihood keys',
        reference='common-panel focal goalie versus zero actor residuals: miss given unblocked; recorded stop given on-net; conversion given on-net and no recorded stop; reattempt given neutral saved-shot opportunity; next danger given recorded reattempt; joint follow-up danger per neutral saved-shot opportunity. stopping is favorable-positive goals saved per100 common on-net opportunities and excludes focal q. h*d is averaged jointly using fixed neutral saved-shot weights. raw probabilities increase with the named event; focal-minus-neutral differences are fractions. actual evidence keeps offense/coaches and neutralizes only goalie. next-attempt targets neutralize every actor.',
        limitations=limits,evidence=evidence,purpose=design.purpose,inputs=inputs,reference_id='goalie-v1-07-neutral-execution',
        support_policy_id='goalie-v1-07-head-union-and-exact-elapsed',assessment=dict(status='experimental',findings=[dict(
            quantities=[*(f'goalie_result.{field}' for field in FIELDS),'goalie_observed.stage_evidence.reattempt','goalie_observed.stage_evidence.next_attempt_danger'],
            population='all selected annual goalies and declared common-panel/actual matched populations',summary='; '.join(limits),evidence=evidence)]))


def _coverage(target_summary, source_games, events, row_counts, head_status):
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
        team_unavailable_games=[dict(game_id=game['game_id'],player_id=row['player_id'],reason='dated_goalie_team_unavailable')
            for game in source_games for row in game['goalies'] if row['team'] is None],
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
        purpose=read_json(Path(state)/'manifest.json' if Path(state).is_dir() else Path(state))['purpose']
        state=read_goalie_state(state,purpose)
    require(state.usage=='annual','goalie scores require the original annual baseline')
    if not isinstance(prepared,PreparedManifest):
        prepared=read_prepared(prepared,state.manifest['purpose'])
    output=output_path(str(output),[str(prepared.directory),str(state.path.parent),str(Path(coaches).resolve().parent)])
    if state.manifest['purpose']=='real':
        require(output.is_relative_to('/Volumes/Expansion/hockey-stats'),'expensive real outputs must be external')
    design=prepare_goalie_scoring(prepared,coaches,annual_execution_scores,state.manifest['season'])
    for name in ('prepared','coaches','base_state','base_scores'):
        require(state.manifest[name]==getattr(design,name),'goalie scoring '+name+' binding differs')
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
    _write_jsonl(output/'people.jsonl',source['people'])
    _write_jsonl(output/'source_games.jsonl',design.source_games)
    _write_jsonl(output/'event_values.jsonl',events)
    _write_jsonl(output/'targets.jsonl',design.targets)
    method='goalie-v1-07-'+design.season
    baseline_projections={};changed_projections={name:{} for name in variants};counts=Counter()
    projection_started=perf_counter()
    with ExitStack() as stack:
        handles={table:stack.enter_context((output/(table+'.jsonl')).open('xb')) for table in PUBLIC_TABLES}
        projections=stack.enter_context((output/'projections.jsonl').open('xb'))
        for name,projection,cells in _project_variants(design,states,base_state,base_scores,source['people'],source['participation'],base_events):
            key=projection['player_id'],projection['strength']
            if name!='baseline':
                changed_projections[name][key]=projection
                continue
            baseline_projections[key]=projection
            projections.write(_line(projection))
            for table,row in _modeled_rows(projection,cells,method):
                handles[table].write(_line(row));counts[table]+=1
        by_player=defaultdict(list)
        for row in events:
            if row['goalie_id'] is not None:
                by_player[row['goalie_id']].append(row)
        source_ref=dict(kind='source',id=source['sources'][0]['source_id'])
        for person in source['people']:
            player=person['player_id']
            for table,row in _observed_rows(design.season,player,by_player[player],events,design.source_games,source_ref,method):
                handles[table].write(_line(row));counts[table]+=1
    projection_seconds=perf_counter()-projection_started
    sensitivity_started=perf_counter()
    sensitivity=_sensitivity(state,variants,baseline_projections,changed_projections,events,design)
    _write_document(output/'sensitivity.json',sensitivity)
    coverage=_coverage(design.coverage,design.source_games,events,counts,{head:state.heads[head]['status'] for head in HEADS})
    _write_document(output/'coverage.json',coverage)
    catalogs=dict(sources=source['sources'],methods=[_method(design,state,sensitivity,output/'projections.jsonl')],supports=[])
    _write_document(output/'catalogs.json',catalogs)
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
    _write_document(output/'manifest.json',manifest)
    return result


@dataclass(frozen=True)
class GoalieScores:
    path: Path
    manifest: dict
    people: dict
    catalogs: dict
    coverage: dict
    numerical_sensitivity: dict

    def rows(self,table):
        """yield contiguous ascending person groups; selectors retain their declared native order."""
        require(table in PUBLIC_TABLES,'unknown goalie score table')
        return _jsonl(self.path.parent/(table+'.jsonl'))


def read_goalie_scores(path,expected_purpose):
    """read and validate only members contained in this annual score artifact."""
    try:
        path=Path(path).resolve(strict=True)
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
    from .execution_state import _reference
    _closed(value,MANIFEST_KEYS,'goalie score manifest')
    require(type(value['schema_version']) is int and value['schema_version']==1 and value['kind']=='goalie-scores',
            'invalid goalie score schema')
    require(purpose in ('real','fixture') and value['purpose']==purpose,'goalie score purpose differs')
    year=_season_label(value['season'])
    require(year in ('20212022','20222023','20232024','20242025','20252026'),'goalie score year outside scope')
    require(value['recipe']==RECIPE,'goalie score recipe differs')
    for name,keys in (('prepared',('path','sha256','purpose','members')),('coaches',('path','sha256','purpose','selected_game_ids')),
                      ('base_state',('path','sha256','season','purpose','recipe_sha256','usage','previous')),
                      ('base_scores',('path','sha256')),('state',('path','sha256','season','purpose','recipe_sha256','previous'))):
        _closed(value[name],keys,'goalie score '+name);_reference(value[name],name)
    require(value['prepared']['purpose']==value['coaches']['purpose']==purpose,'goalie source purposes differ')
    games=[];member_keys=[]
    for row in value['prepared']['members']:
        _closed(row,('kind','season','game_id','path','sha256'),'goalie prepared member')
        require(row['kind'] in ('game','people') and row['season']==year,'goalie prepared member year/kind differs')
        digest(row['sha256']);member_keys.append((row['kind'],row['game_id']))
        if row['kind']=='game':games.append(row['game_id'])
    require(len(member_keys)==len(set(member_keys)) and ('people',None) in member_keys
            and value['coaches']['selected_game_ids']==games,'goalie selected source game bindings differ')
    for name,recipe in (('base_state',BASE_RECIPE),('state',RECIPE)):
        row=value[name]
        require(row['purpose']==purpose and row['season']==year and row['recipe_sha256']==recipe['sha256'],name+' annual binding differs')
        if row['previous'] is not None:
            _closed(row['previous'],('path','sha256'),name+' predecessor');_reference(row['previous'],name+' predecessor')
        elif purpose=='real':
            require(year=='20212022',name+' real chain omitted predecessor')
    require(value['base_state']['usage']=='annual','goalie base state is not annual')
    cutoff=date.fromisoformat(value['training_cutoff'])
    require(int(year[:4])<=cutoff.year<=int(year[4:]),'goalie score cutoff outside season')
    producer=value['implementation']
    _closed(producer,('git_commit','git_dirty','python_version','numpy_version','scipy_version','lockfile_sha256'),'goalie score implementation')
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
    _closed(value['numerical_sensitivity'],('status','path'),'goalie sensitivity binding')
    require(value['numerical_sensitivity']['path']=='sensitivity.json','goalie sensitivity role differs')
    costs=value['resources'];_closed(costs,('wall_seconds','input_read_wall_seconds','projection_wall_seconds','sensitivity_wall_seconds','validation_wall_seconds','peak_memory_bytes','output_bytes'),'goalie score resources')
    for key,val in costs.items():
        _number(val,key,low=0.) if key.endswith('seconds') else _count(val,key)


def _validate_event_value(row,manifest,source,target):
    fields=('season','game_id','source_index','key','goalie_id','physical_state','outcome','shot_type','source_status','base_status','paired',
            'origin_cell','on_net_probability','unblocked_probability','neutral_on_net_probability','stages','continuation_probabilities','base_heads','exclusions')
    _closed(row,fields,'goalie event values')
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
        if value is not None:_number(value,key,low=0.,high=1.)
    require(type(row['exclusions']) is list and all(type(code) is str and code for code in row['exclusions'])
            and bool(row['exclusions']) is not paired,'goalie pair exclusion reason differs')
    require(row['base_heads'] is None or type(row['base_heads']) is dict and set(row['base_heads'])=={'u','q','r','g'},'invalid base head disposition axis')
    if row['base_heads'] is not None:
        for value in row['base_heads'].values():
            _closed(value,('included','target','reasons'),'base likelihood disposition')
            require(type(value['included']) is bool and type(value['reasons']) is list and
                    (value['target'] in (0.,1.) and type(value['target']) is float and not value['reasons'] if value['included'] else
                     value['target'] is None and bool(value['reasons'])),'invalid base likelihood disposition')
    _closed(row['continuation_probabilities'],('actor','neutral_goalie'),'continuation references')
    for values in row['continuation_probabilities'].values():
        _closed(values,HEADS,'continuation heads')
        for key,value in values.items():
            if value is not None:_number(value,key,low=0.,high=1.)
    _closed(row['stages'],('miss','recorded_stop','conversion','reattempt','next_attempt_danger'),'goalie stages')
    expected_labels=dict(miss=int(source['outcome']=='miss') if source['status']=='included' and source['outcome']!='block' else None,
        recorded_stop=int(source['recorded_stop']) if source['outcome'] in ('save','goal') and source['recorded_stop'] is not None else None,
        conversion=int(source['outcome']=='goal') if source['outcome'] in ('save','goal') and source['recorded_stop'] is False else None,
        reattempt=int(source['recorded_reattempt']) if source['outcome']=='save' and source['recorded_reattempt'] is not None else None,
        next_attempt_danger=target['d_target'])
    for key,value in row['stages'].items():
        _closed(value,('response','prediction','reason'),'goalie matched stage')
        require(value['response']==expected_labels[key],'goalie stage response differs from source label/target')
        if value['prediction'] is not None:_number(value['prediction'],key,low=0.,high=1.)
        require((value['reason'] is None)==(value['response'] is not None and value['prediction'] is not None), 'goalie stage disposition differs')
    for head,stage in (('h','reattempt'),('d','next_attempt_danger')):
        require(row['stages'][stage]['prediction']==row['continuation_probabilities']['neutral_goalie'][head], 'continuation event stage/reference differs')


def _validate_projection(row,manifest,people,likelihood_index):
    from .analysis_publication import support
    _closed(row,('season','player_id','strength','values','neutral_values','masses','coefficient_support','support','panels','unavailable'),'goalie projection')
    require(row['season']==manifest['season'] and row['player_id'] in people and row['strength'] in GOALIE_STRENGTHS,
            'goalie projection identity differs')
    _closed(row['values'],FIELDS,'goalie projection values');_closed(row['support'],FIELDS,'goalie projection supports')
    _closed(row['neutral_values'],DEPENDENCIES.keys()-{'stopping_goals_per100_on_net'},'goalie neutral levels')
    _closed(row['coefficient_support'],(*BASE_HEADS,*HEADS),'goalie coefficient heads')
    likelihood={}
    for head,record in row['coefficient_support'].items():
        _closed(record,('available','likelihood_events','prior_only','prior_seasons','reason'),'goalie coefficient support')
        require(type(record['available']) is bool and type(record['prior_only']) is bool,'invalid goalie coefficient availability')
        _count(record['likelihood_events'],'goalie likelihood count')
        require(record['reason'] in (None,'head_incomplete','actor_coefficient_unavailable') and (record['reason'] is None)==record['available'],
                'goalie coefficient unavailable reason differs')
        require(type(record['prior_seasons']) is list and record['prior_seasons']==sorted(set(record['prior_seasons'])), 'invalid goalie prior years')
        for year in record['prior_seasons']:
            _season_label(year);require(year<manifest['season'],'goalie coefficient carries future history')
        likelihood[head]=likelihood_index.get((row['player_id'],head),set()) if record['available'] else set()
        require(record['likelihood_events']==len(likelihood[head]),'goalie coefficient likelihood key count differs')
    _closed(row['masses'],('prefixes','continuation'),'goalie projection mass groups')
    for group,size in (('prefixes',4),('continuation',3)):
        _closed(row['masses'][group],('neutral','focal'),'goalie mass references')
        for name,record in row['masses'][group].items():
            _closed(record,('log_masses','masses'),'goalie reference mass')
            require(type(record['masses']) is list and type(record['log_masses']) is list
                    and len(record['masses'])==len(record['log_masses'])==size,'goalie reference mass axis differs')
            for log_value,mass in zip(record['log_masses'],record['masses'],strict=True):
                if mass is None:
                    require(log_value is None,'unsupported goalie mass retained a log')
                else:
                    _number(mass,'goalie reference mass',low=0.)
                    require(log_value is None and mass==0. or type(log_value) in (int,float) and isfinite(log_value)
                            and isclose(mass,float(np.exp(log_value)),rel_tol=1e-12,abs_tol=0.),'goalie log/reference mass differs')
    for name in ('neutral','focal'):
        prefix=row['masses']['prefixes'][name]['masses']
        for left,right in zip(prefix,prefix[1:]):
            require(left is None or right is None or right<=left or isclose(right,left,rel_tol=1e-12),'goalie prefix mass increases')
        continuation=row['masses']['continuation'][name]['masses']
        for left,right in zip(continuation,continuation[1:]):
            require(left is None or right is None or right<=left or isclose(right,left,rel_tol=1e-12),'goalie continuation mass increases')
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
        if value is not None:_number(value,field,low=None if field.endswith('_difference') or field.startswith('stopping_') else 0.,
                                      high=None if field.endswith('_difference') or field.startswith('stopping_') else 1.)
        support(row['support'][field])
        heads=DEPENDENCIES[field.removesuffix('_difference')]
        available=all(row['coefficient_support'][head]['available'] for head in heads)
        require(value is None or available,'goalie unsupported dependency produced a value')
        current=set().union(*(likelihood[head] for head in heads))
        require(row['support'][field]['events']==len(current) and row['support'][field]['current_season_information']==
                (available and all(bool(likelihood[head]) for head in heads)), 'goalie field likelihood support differs')
        require(row['support'][field]['prior_only']==(available and all(row['coefficient_support'][head]['prior_only'] for head in heads)),
                'goalie field prior-only dependencies differ')
        if field.endswith('_difference') and value is not None:
            base=field.removesuffix('_difference')
            require(row['values'][base] is not None and row['neutral_values'][base] is not None
                    and isclose(value,row['values'][base]-row['neutral_values'][base],rel_tol=1e-12,abs_tol=1e-15),'goalie focal-minus-neutral difference differs')
    require(set(row['unavailable'])=={field for field,value in row['values'].items() if value is None},'goalie unavailable selector matrix differs')
    for value in row['unavailable'].values():
        _closed(value,('reason','explanation'),'goalie unavailable reason')
        require(value['reason'] in ('no_exposure','failed_fit','missing_source') and type(value['explanation']) is str and value['explanation'],
                'invalid goalie unavailable detail')
    require(type(row['panels']) is list and len(row['panels'])==len(constituent_states(row['strength'])),'goalie panel mixture size differs')
    for record,strength in zip(row['panels'],constituent_states(row['strength']),strict=True):
        _closed(record,('panel_id','physical_state','events','origins','events_sha256','arrays_sha256'),'goalie panel identity')
        defending,attacking=map(int,strength.split('v'))
        require(record['physical_state']==[attacking,defending,1,1] and record['panel_id']==f'execution-v1-06-1:{manifest["season"]}:{attacking},{defending},1',
                'goalie panel defending orientation differs')
        _count(record['events'],'goalie panel events');_count(record['origins'],'goalie panel origins')
        digest(record['events_sha256']);digest(record['arrays_sha256'])


def _validate_sensitivity(value,manifest,people,projections,baseline_actual):
    _closed(value,('status','summary_threshold','pointwise_threshold','variants'),'goalie sensitivity')
    require(value['summary_threshold']==1e-4 and value['pointwise_threshold']==1e-5,'goalie sensitivity thresholds differ')
    require(value['status'] in ('not_assessed_for_annual_state','assessed','partially_assessed','unassessed')
            and value['status']==manifest['numerical_sensitivity']['status'],'goalie sensitivity disposition differs')
    require(type(value['variants']) is list,'missing goalie sensitivity variants')
    if value['status']=='not_assessed_for_annual_state':
        require(value['variants']==[],'earlier goalie year claims diagnostic comparisons')
        return
    require([row['variant'] for row in value['variants']]==['h-tight','d-tight','h+d-tight'],'goalie sensitivity variant axis differs')
    assessed=0
    for variant in value['variants']:
        _closed(variant,('variant','status','reason','unavailable_heads','projections','actual_summaries','maximum_probability_change','flagged'),
                'goalie sensitivity comparison')
        if variant['status']=='unassessed':
            require(type(variant['reason']) is str and variant['reason'] and variant['unavailable_heads']
                    and set(variant['unavailable_heads'])<=set(HEADS) and variant['projections']==variant['actual_summaries']==[]
                    and variant['maximum_probability_change'] is None and variant['flagged'] is False,'unassessed goalie comparison invented evidence')
            continue
        require(variant['status']=='assessed' and variant['reason'] is None and variant['unavailable_heads']==[], 'invalid assessed goalie sensitivity')
        assessed+=1;keys=set();changes=[]
        for row in variant['projections']:
            _closed(row,('player_id','strength','values','neutral_values','baseline_masses','variant_masses'),'goalie sensitivity projection')
            key=row['player_id'],row['strength'];require(key in projections and key not in keys,'goalie comparison identity duplicate/unknown');keys.add(key)
            for group,fields in (('values',(*CONTINUATION,*(field+'_difference' for field in CONTINUATION))),('neutral_values',CONTINUATION)):
                require(type(row[group]) is list and [v['field'] for v in row[group]]==list(fields),'goalie comparison field axis differs')
                for item in row[group]:
                    _closed(item,('field','baseline','variant','absolute_change'),'goalie comparison value')
                    baseline=projections[key][group][item['field']]
                    require(item['baseline']==baseline,'goalie comparison baseline differs')
                    if baseline is None or item['variant'] is None:
                        require(item['absolute_change'] is None,'unavailable goalie comparison invented a delta')
                    else:
                        change=abs(item['variant']-baseline)
                        require(item['absolute_change']==change,'goalie sensitivity difference arithmetic differs');changes.append(change)
            require(row['baseline_masses']==projections[key]['masses']['continuation'],'goalie comparison baseline denominators differ')
            for group in ('baseline_masses','variant_masses'):
                _closed(row[group],('neutral','focal'),'goalie comparison references')
                for record in row[group].values():
                    _closed(record,('log_masses','masses'),'goalie comparison masses')
                    require(len(record['log_masses'])==len(record['masses'])==3,'goalie comparison continuation axis differs')
        require(keys==set(projections),'goalie sensitivity omitted a published goalie-strength')
        actual_keys=set()
        for row in variant['actual_summaries']:
            _closed(row,('player_id','strength','game_id','physical_state','stage','count','baseline_mean','variant_mean','absolute_change',
                         'baseline_expected_sum','variant_expected_sum','expected_mass_change'),'goalie actual sensitivity')
            require(row['player_id'] in people and row['strength'] in (*GOALIE_STRENGTHS,'covered_all')
                    and row['stage'] in ('reattempt','next_attempt_danger'),'invalid goalie actual comparison key')
            key=(row['player_id'],row['strength'],row['game_id'],None if row['physical_state'] is None else tuple(row['physical_state']),row['stage'])
            require(key in baseline_actual and key not in actual_keys,'unknown/duplicate goalie actual comparison');actual_keys.add(key)
            require(row['count']==baseline_actual[key]['count'] and row['baseline_mean']==baseline_actual[key]['mean']
                    and row['baseline_expected_sum']==baseline_actual[key]['expected_sum'],'goalie actual sensitivity baseline differs')
            require(type(row['count']) is int and row['count']>0,'empty matched sensitivity summary')
            for field in ('baseline_mean','variant_mean'):_number(row[field],field,low=0.,high=1.)
            require(isclose(row['baseline_mean']*row['count'],row['baseline_expected_sum'],rel_tol=1e-12)
                    and isclose(row['variant_mean']*row['count'],row['variant_expected_sum'],rel_tol=1e-12)
                    and row['expected_mass_change']==row['variant_expected_sum']-row['baseline_expected_sum']
                    and row['absolute_change']==abs(row['variant_mean']-row['baseline_mean']),'goalie actual sensitivity arithmetic differs')
            changes.append(row['absolute_change'])
        require(actual_keys==set(baseline_actual),'goalie sensitivity omitted a nonempty actual evidence summary')
        maximum=max(changes,default=0.)
        require(variant['maximum_probability_change']==maximum and variant['flagged']==(maximum>1e-4),'goalie sensitivity maximum/flag differs')
    require(value['status']==('assessed' if assessed==3 else 'partially_assessed' if assessed else 'unassessed'),'goalie sensitivity overall disposition differs')


def _check_actual_evidence(table,row,selected,league,source_games,method,source):
    data=row['result']['data'];strength=row['strength']
    if table=='execution_breakdown':
        require(data==_breakdown(selected,row['kind'],row['stratum'],method),'saved goalie breakdown differs from keyed paired events')
        return
    if table in ('goalie_evidence_map','goalie_danger'):
        population=row['population']
        if table=='goalie_evidence_map':
            selected=[event for event in selected if _type_selected(event,row['type'])]
            league=[event for event in league if _type_selected(event,row['type'])]
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
            totals=_totals(league,population)
            require(data['league_goals']==totals['goals'] and data['league_expected_goals']==totals['expected_goals'],'goalie matched type/population league differs')
        return
    if table!='goalie_observed':return
    actor_games=[(game,actor) for game in source_games for actor in game['goalies'] if actor['player_id']==row['player_id']]
    missing=not actor_games or all(not game['source_events_available'] for game,actor in actor_games)
    expected=_summary_evidence(selected,league,source,method,missing=missing,gap=any(actor['source_events_gap'] for _,actor in actor_games))
    for key in expected:
        require(data[key]==expected[key],'goalie season '+key+' differs from source/matched event reduction')
    require(data['reported_boxscore_counts']==_reported_counts([actor for _,actor in actor_games],strength,source,method),
            'goalie reported season field populations differ')
    expected_games={game['game_id']:(game,actor) for game,actor in actor_games if actor['team'] is not None}
    require({game['game_id'] for game in data['games']}==set(expected_games),'goalie game evidence membership differs')
    for game in data['games']:
        original,actor=expected_games[game['game_id']]
        game_events=[event for event in selected if event['game_id']==game['game_id']]
        expected=_summary_evidence(game_events,league,source,method,missing=not original['source_events_available'],gap=actor['source_events_gap'])
        for key in expected:
            require(game[key]==expected[key],'goalie game '+key+' differs from keyed physical events')
        require(game['reported_boxscore_counts']==_reported_counts([actor],strength,source,method)
                and game['start_status']==actor['start_status'] and game['reported_seconds']==actor['reported_seconds']
                and game['team']==actor['team'] and game['opponent']==actor['opponent'] and game['date']==original['date'],
                'goalie game usage/start/source facts differ')


def _validate_scores(path,manifest,expected_purpose):
    from . import analysis_publication as public
    from .descriptive import validate_goalie_source_game
    from .execution_state import _finite
    from .goalie import target_coverage
    from .goalie_state import validate_goalie_target
    _score_manifest(manifest,expected_purpose)
    root=path.parent;files=manifest['files'];require(type(files) is list,'missing goalie score members')
    bound={}
    for row in files:
        _closed(row,('path','sha256','role'),'goalie score member')
        require(row['path'] in MEMBERS and row['path'] not in bound and row['role']==MEMBERS[row['path']],'unknown/duplicate/cross-wired goalie score member')
        digest(row['sha256']);member=(root/row['path']).resolve(strict=True)
        require(root in member.parents and member.is_file(),'goalie score member escapes artifact')
        require(identity(member)['sha256']==row['sha256'],'goalie score member digest differs');bound[row['path']]=member
    require(set(bound)==set(MEMBERS),'goalie score member omitted')
    actual={str(member.relative_to(root)) for member in root.rglob('*') if member.is_file() and member!=path}
    require(actual==set(MEMBERS),'unbound files in goalie scores')
    require(manifest['resources']['output_bytes']==sum(member.stat().st_size for member in bound.values()),'goalie saved byte cost differs')
    catalogs=read_json(root/'catalogs.json');_closed(catalogs,('sources','methods','supports'),'goalie score catalogs')
    lookups={key:{} for key in ('source','method','support')}
    for table,singular in (('sources','source'),('methods','method'),('supports','support')):
        require(type(catalogs[table]) is list,'missing goalie catalog')
        for row in catalogs[table]:
            public.validate_catalog(table,row,expected_purpose,lookups,manifest['prepared']['sha256'])
            key=row[singular+'_id'];require(key not in lookups[singular],'duplicate goalie catalog identity');lookups[singular][key]=row
    people={};person_keys={}
    for row in _jsonl(root/'people.jsonl'):
        public.validate_catalog('people',row,expected_purpose,lookups,manifest['prepared']['sha256'])
        require(row['season']==manifest['season'] and row['kind']=='goalie' and row['player_id'] not in people,'invalid/duplicate goalie annual person')
        people[row['player_id']]=row;person_keys[row['season'],row['player_id']]=row
    source_games=list(_jsonl(root/'source_games.jsonl'));source_events={}
    require([game['game_id'] for game in source_games]==manifest['coaches']['selected_game_ids'],'goalie source game order differs')
    for game in source_games:
        validate_goalie_source_game(game)
        require(game['season']==manifest['season'],'goalie source game year differs')
        for row in game['events']:
            key=f"{game['game_id']}:{row['source_index']}";require(key not in source_events,'duplicate source focal key');source_events[key]=row
    targets={}
    for row in _jsonl(root/'targets.jsonl'):
        validate_goalie_target(row,manifest)
        require(row['key'] in source_events and row['key'] not in targets,'unknown/duplicate goalie score target');targets[row['key']]=row
    require(set(targets)==set(source_events),'goalie source/target keys differ')
    events={}
    for row in _jsonl(root/'event_values.jsonl'):
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
    for row in _jsonl(root/'projections.jsonl'):
        _validate_projection(row,manifest,people,likelihood_index)
        key=row['player_id'],row['strength'];require(key not in projections,'duplicate goalie projection');projections[key]=row
    require(set(projections)=={(player,strength) for player in people for strength in GOALIE_STRENGTHS},'goalie projection matrix incomplete')
    sensitivity=read_json(root/'sensitivity.json');_validate_sensitivity(sensitivity,manifest,people,projections,_stage_summaries(list(events.values())))
    _finite(sensitivity,'goalie sensitivity')
    by_selector=defaultdict(list);league_by_strength=defaultdict(list)
    for row in events.values():
        for strength in (*GOALIE_STRENGTHS,'covered_all'):
            if state_selected(row['physical_state'],strength):
                league_by_strength[strength].append(row)
                if row['goalie_id'] is not None:
                    by_selector[row['goalie_id'],strength].append(row)
    counts=Counter();seen=defaultdict(set)
    method='goalie-v1-07-'+manifest['season'];source=dict(kind='source',id='goalie-source-v1-07-'+manifest['season'])
    require(method in lookups['method'] and source['id'] in lookups['source'],'goalie fixed method/source identities absent')
    for table in PUBLIC_TABLES:
        previous_player=None
        for row in _jsonl(root/(table+'.jsonl')):
            require(previous_player is None or previous_player<=row['player_id'],'goalie score person groups are not ascending/contiguous')
            previous_player=row['player_id']
            public.validate_row(table,row,'goalie',lookups,person_keys)
            require(row['season']==manifest['season'] and row['result']['availability']=='provided','goalie score row must be provided in its annual scope')
            key=tuple(row[field] for field in KEYS[table]);require(key not in seen[table],'duplicate goalie public selector');seen[table].add(key);counts[table]+=1
            if table=='goalie_result':
                projection=projections[row['player_id'],row['strength']];payload=row['result']['data']
                require(payload['support']==projection['support'] and all(payload[field]['value']==projection['values'][field] for field in FIELDS),
                        'goalie public scalar/support differs from saved projection')
            elif table=='analysis_map':
                require(row['result']['data']['integrated_value']==projections[row['player_id'],row['strength']]['values']['stopping_goals_per100_on_net'],
                        'goalie map scalar differs from saved projection')
            else:
                _check_actual_evidence(table,row,by_selector[row['player_id'],row['strength']],league_by_strength[row['strength']],source_games,method,source)
        expected={tuple([manifest['season'],player,*selectors]) for player in people for selectors in public.required_keys(table,'goalie')}
        require(seen[table]==expected,'goalie public required selector matrix incomplete: '+table)
    coverage=read_json(root/'coverage.json')
    _closed(coverage,('targets','events','source_included','paired_unblocked','baseline_head_status','team_unavailable_games',
                     'stage_prediction_reasons','source_only','numerical_only','stage_dispositions','event_exclusions','row_counts'),'goalie score coverage')
    _closed(coverage['baseline_head_status'],HEADS,'goalie baseline dispositions')
    require(all(value in ('complete','unavailable') for value in coverage['baseline_head_status'].values()),'invalid goalie baseline status')
    require(coverage==_coverage(target_coverage(list(targets.values()),manifest['season']),source_games,list(events.values()),counts,coverage['baseline_head_status']),
            'goalie saved coverage differs from source/target/numerical members')
    return GoalieScores(path,manifest,people,catalogs,coverage,sensitivity)
