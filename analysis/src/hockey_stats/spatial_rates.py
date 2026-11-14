"""positive annual attempt volume, spatial shape and neutral opportunity quality.

raw coefficients own history. exposure centers own reporting. the reference is
an elapsed linear predictor, and exact context allocations are a separate view.
"""

from dataclasses import dataclass, replace
import hashlib
import heapq
import json
import math
from pathlib import Path
import resource
from time import perf_counter

import numpy as np
from scipy.special import expit, log_expit, logsumexp

from .artifacts import implementation, ordered_array_digest, require
from .chance import solve_logistic
from .chance_cli import identity
from .coalitions import FOUR_GROUP_WEIGHTS, four_group_allocation
from .captures import InputContractError

HEADS = ('volume', 'shape', 'quality')
ROLES = ('offense', 'defense')
QUANTITIES = ('attempts', 'xg')
ADJUSTMENTS = ('baseline', 'self', 'teammates', 'opponents', 'coaching_other_context', 'residual', 'factual')
SOLVER = dict(maxiter=10000, ftol=1e-15, gtol=1e-6, maxcor=10)
CONTINUATION = dict(maxiter=10000, ftol=1e-16, gtol=1e-7, maxcor=10)
RECIPE = dict(name='experimental-v1', version='positive-spatial-v1-08-1',
              heads=list(HEADS), modes=40, batch_size=4096,
              solver=SOLVER, continuation=CONTINUATION,
              support_policy='ordinary-attempt-segment-valued-two-direction-v1')
ST_RECIPE = dict(RECIPE, version='positive-spatial-st-v1-09-1',
                 support_policy='ordinary-attempt-segment-valued-advantaged-only-v1',
                 states=['5v4', '5v3', '4v3'],
                 diagnostic_policy='completed-baselines-experimental-with-disclosed-sensitivity')
ST_STRENGTHS = (('pp', 'pk'), ('5v4', '4v5'), ('5v3', '3v5'), ('4v3', '3v4'))


def _is_st(design):
    return getattr(design, 'family', 'ev') == 'st'


def _row_offsets(design, kind, rows=None):
    offsets = design.annual_offsets
    if not _is_st(design):
        return offsets
    states = getattr(design, 'state_' + kind)
    if rows is not None:
        states = states[rows]
    return {name: np.asarray(offsets[name])[states] for name in ('r', 'pi', 'qbar')}


@dataclass(frozen=True)
class SpatialProjections:
    rows: list
    arrays: dict
    adjustments: list
    coefficient_support: list
    reference: dict
    diagnostics: dict


def _width(head):
    return {'volume': 1, 'shape': 40, 'quality': 41}[head]


def _actor_key(column):
    return column['block'], str(column['id']), column['subblock']



def _linear_parts(actor,context,beta):
    split=actor.shape[1]
    return np.asarray(actor@beta[:split])+np.asarray(context@beta[split:])


def _adjoint_parts(actor,context,residual):
    return np.vstack((np.asarray(actor.T@residual),np.asarray(context.T@residual)))


def _linear(design,beta,kind,rows=None):
    actor=getattr(design,'X_'+kind)
    context=getattr(design,'context_'+kind)
    if rows is not None:actor,context=actor[rows],context[rows]
    return _linear_parts(actor,context,beta)


def _adjoint(design,residual,kind,rows=None):
    actor=getattr(design,'X_'+kind)
    context=getattr(design,'context_'+kind)
    if rows is not None:actor,context=actor[rows],context[rows]
    return _adjoint_parts(actor,context,residual)


def actor_support(design, *, state=None):
    """sparse reductions once per head, never one dense elapsed vector per actor."""
    time = design.X_time.tocsc()
    event = design.X_event.tocsc()
    exposure = design.exposure_hours
    event_rows = None
    if state is not None:
        require(_is_st(design) and state in (0,1,2), 'invalid exact support state')
        time_rows = design.state_time == state
        event_rows = design.state_event == state
        time, event, exposure = time[time_rows], event[event_rows], exposure[time_rows]
    actor_indices = [i for i,c in enumerate(design.columns) if c['kind']=='actor']
    require(np.all(time[:,actor_indices].data >= 0) and np.all(event[:,actor_indices].data >= 0),
            'negative actor applicability')
    seconds = np.asarray(time.T@exposure).ravel()*3600
    incidence = event.copy()
    incidence.data = (incidence.data>0).astype(float)
    events = np.asarray(incidence.sum(axis=0)).ravel()
    event_mass = np.add.reduceat(design.origin_weights, design.event_offsets[:-1]) if design.X_event.shape[0] else np.zeros(0)
    if event_rows is not None:
        event_mass = event_mass[event_rows]
    mass = np.asarray(event.T@event_mass).ravel()
    return {i:dict(included_seconds=float(seconds[i]),likelihood_events=int(events[i]),
                   eligible_origin_weight=float(mass[i]),time_incidence=bool(seconds[i]>0),
                   event_incidence=bool(events[i]>0)) for i in actor_indices}


def annual_priors(design, head, ledger):
    """one entry or last-supported carry penalty per actor/subblock."""
    previous = {_actor_key(row): row for row in ledger}
    require(len(previous) == len(ledger), 'duplicate last-supported spatial actor')
    width = _width(head)
    rows = []
    support_by_index = actor_support(design)
    for index, column in enumerate(design.columns):
        if column['kind'] != 'actor':
            continue
        support = support_by_index[index]
        info = ((support['time_incidence'] or support['event_incidence']) if head == 'volume'
                else support['eligible_origin_weight'] > 0)
        last = previous.get(_actor_key(column))
        player = column['block'].endswith('_player')
        facts = design.player_facts[str(column['id'])] if player else {}
        position = facts.get('position_group')
        age_days = facts.get('age_days')
        age = None if age_days is None else age_days/365.2425
        mean = np.zeros(width) if last is None else np.asarray(last['coefficient'], dtype=float)
        require(mean.shape == (width,) and np.isfinite(mean).all(), 'historical spatial coordinate differs')
        gap = None if last is None else int(design.season[:4])-int(last['season'][:4])
        require(gap is None or gap > 0, 'spatial history is not strictly earlier')
        precision = (16. if player else 100.) if last is None else (100. if player else 400.)/gap
        scales = np.full(width, precision*40.)
        if head != 'shape':
            scales[0] = precision
        age_delta, age_indices = [], []
        reason = 'entry' if last is None else 'age_neutral'
        if head == 'volume' and player and last is not None:
            if position not in ('F','D') or last['position_group'] != position:
                reason = 'missing_or_changed_role'
            elif age is None or last['age'] is None:
                reason = 'missing_age'
            else:
                now, old = (age-27)/10, (last['age']-27)/10
                age_delta = [now-old, now*now-old*old]
                start = (0 if column['block'] == 'attacking_player' else 4) + (0 if position == 'F' else 2)
                age_indices = [start, start+1]
                reason = 'age_carry'
        rows.append(dict(index=index, block=column['block'], id=str(column['id']),
                         subblock=column['subblock'], position_group=position, age=age,
                         **support, current_season_information=bool(info), prior_only=not bool(info),
                         mean=mean.tolist(), precision=scales.tolist(),
                         prior_kind='entry' if last is None else 'carry',
                         prior_anchor_season=None if last is None else last['season'],
                         prior_seasons=[] if last is None else list(last['support_seasons']),
                         last_supported=last, age_delta=age_delta, age_indices=age_indices,
                         transition_reason=reason))
    return rows


def _conditional_mean(prior, age):
    result = np.asarray(prior['mean'], dtype=float).copy()
    if prior['age_indices']:
        result[0] += np.dot(prior['age_delta'], age[prior['age_indices']])
    return result


def _unpack(flat, design, head):
    count=len(design.columns)*_width(head)
    flat=np.asarray(flat)
    require(flat.ndim==1 and len(flat)==count+(8 if head=='volume' else 0)
            and flat.dtype.kind in 'fi' and np.isfinite(flat).all(),'invalid spatial coefficient cardinality or domain')
    beta=flat[:count].reshape(len(design.columns),_width(head))
    age = np.asarray(flat[count:]) if head == 'volume' else np.zeros(8)
    require(age.shape == (8,), 'invalid spatial age coordinate')
    return beta, age


def _penalty(beta, age, design, head, priors):
    precision = np.zeros_like(beta)
    for i, column in enumerate(design.columns):
        if column['kind'] == 'actor':
            continue
        scalar = .25 if column['kind'] == 'intercept' else 1.
        spatial = 40. if column['kind'] == 'intercept' else 160.
        precision[i] = spatial
        if head != 'shape':
            precision[i, 0] = scalar
    gradient = precision*beta
    value = .5*float(np.sum(gradient*beta))
    age_gradient = 64.*age if head == 'volume' else np.zeros(8)
    if head == 'volume':
        value += 32.*float(np.dot(age, age))
    for prior in priors:
        # profiling no-information coefficients removes their quadratic and all
        # false age information; fill them after the supported fit is solved.
        if prior['prior_only']:
            continue
        difference = beta[prior['index']]-_conditional_mean(prior, age)
        scaled = difference*np.asarray(prior['precision'])
        value += .5*float(np.dot(difference, scaled))
        gradient[prior['index']] += scaled
        if prior['age_indices']:
            age_gradient[prior['age_indices']] -= scaled[0]*np.asarray(prior['age_delta'])
    return value, gradient, age_gradient


def _volume_groups(design):
    """digest candidates, then compare exact actor/context rows before grouping."""
    x=design.X_time.tocsr()
    context=design.context_time
    groups,indices,exposure={},[],[]
    for row in range(x.shape[0]):
        left,right=x.indptr[row:row+2]
        hasher=hashlib.sha256()
        hasher.update(x.indices[left:right].tobytes());hasher.update(x.data[left:right].tobytes())
        hasher.update(context[row].tobytes())
        if _is_st(design):
            hasher.update(np.asarray(design.state_time[row], dtype=np.int64).tobytes())
        key=hasher.digest()
        target=None
        for candidate in groups.get(key,()):
            prior=indices[candidate];a,b=x.indptr[prior:prior+2]
            if (not _is_st(design) or design.state_time[row] == design.state_time[prior]) and np.array_equal(x.indices[left:right],x.indices[a:b]) and np.array_equal(x.data[left:right],x.data[a:b]) and np.array_equal(context[row],context[prior]):
                target=candidate;break
        if target is None:
            groups.setdefault(key,[]).append(len(indices));indices.append(row);exposure.append(float(design.exposure_hours[row]))
        else:exposure[target]+=float(design.exposure_hours[row])
    return np.asarray(indices,dtype=np.int64),np.asarray(exposure)


def head_objective(flat, design, head, priors, work=None, *, components=False):
    """summed convex likelihood and proper penalties with analytic gradients."""
    beta, age = _unpack(flat, design, head)
    penalty, gradient, age_gradient = _penalty(beta, age, design, head, priors)
    likelihood = 0.
    offsets = design.annual_offsets
    if head == 'volume':
        actor,context,exposure=(design.X_time,design.context_time,design.exposure_hours) if work is None else work['volume']
        if _is_st(design):
            states = design.state_time if work is None else work['volume_states']
            log_rate = np.log(np.asarray(offsets['r'])[states])
            event_log_rate = float(np.log(np.asarray(offsets['r'])[design.state_event]).sum())
        else:
            log_rate = math.log(offsets['r'])
            event_log_rate = design.X_event.shape[0] * log_rate
        eta=log_rate+_linear_parts(actor,context,beta).ravel()
        with np.errstate(over='raise', invalid='raise', under='raise'):
            rates = np.exp(eta)
        require(np.all(rates > 0) and np.isfinite(rates).all(), 'invalid spatial volume rate')
        event_sum=_adjoint(design,np.ones((design.X_event.shape[0],1)),'event') if work is None else work['volume_event_sum']
        likelihood=float(np.dot(exposure,rates)-event_log_rate-np.sum(event_sum*beta))
        gradient+=_adjoint_parts(actor,context,(exposure*rates)[:,None])
        gradient-=event_sum
    else:
        n = design.X_event.shape[0]
        for start in range(0, n, 4096):
            stop = min(start+4096, n)
            row_slice=slice(start,stop)
            predictor=_linear(design,beta,'event',row_slice)
            left, right = int(design.event_offsets[start]), int(design.event_offsets[stop])
            rows = np.repeat(np.arange(stop-start), np.diff(design.event_offsets[start:stop+1]))
            cells = design.origin_cells[left:right]
            weight = design.origin_weights[left:right]
            batch_offsets = _row_offsets(design, 'event', row_slice)
            if head == 'shape':
                logits = np.log(batch_offsets['pi'])+predictor@design.basis.T
                logp = logits-logsumexp(logits, axis=1)[:, None]
                likelihood -= float(np.dot(weight, logp[rows, cells]))
                residual = np.exp(logp)
                np.add.at(residual, (rows, cells), -weight)
                row_gradient = residual@design.basis
            else:
                qbar = np.asarray(batch_offsets['qbar'])
                logits = np.log(qbar)-np.log1p(-qbar)+predictor[:, :1]+predictor[:, 1:]@design.basis.T
                origin_eta = logits[rows, cells]
                target = design.neutral_goal_probability[left:right]
                likelihood -= float(np.dot(weight, target*log_expit(origin_eta)+(1-target)*log_expit(-origin_eta)))
                residual = np.zeros_like(logits)
                np.add.at(residual, (rows, cells), weight*(expit(origin_eta)-target))
                row_gradient = np.column_stack((residual.sum(axis=1), residual@design.basis))
            gradient+=_adjoint(design,row_gradient,'event',row_slice)
    require(math.isfinite(likelihood+penalty) and np.isfinite(gradient).all()
            and np.isfinite(age_gradient).all(), 'nonfinite spatial objective')
    flat_gradient = gradient.ravel()
    if head == 'volume':
        flat_gradient = np.r_[flat_gradient, age_gradient]
    if components:
        return dict(likelihood=float(likelihood), penalty=float(penalty), total=float(likelihood+penalty))
    return float(likelihood+penalty), flat_gradient


def _complete_prior_only(flat, design, head, priors):
    beta, age = _unpack(flat, design, head)
    beta = beta.copy()
    for prior in priors:
        if prior['prior_only']:
            beta[prior['index']] = _conditional_mean(prior, age)
    if _is_st(design):
        for state in range(3):
            informed = (np.any(design.exposure_hours[design.state_time == state] > 0)
                        if head == 'volume' else np.any(design.state_event == state))
            if not informed:
                beta[state] = 0.
    return np.r_[beta.ravel(), age] if head == 'volume' else beta.ravel()


def _head_work(design, head):
    work = None
    if head == 'volume':
        representatives,exposure = _volume_groups(design)
        unchanged=len(representatives)==design.X_time.shape[0]
        work={'volume':(design.X_time if unchanged else design.X_time[representatives],
                        design.context_time if unchanged else design.context_time[representatives],exposure),
              'volume_event_sum':_adjoint(design,np.ones((design.X_event.shape[0],1)),'event')}
        if _is_st(design):
            work['volume_states'] = design.state_time[representatives]
    return work


def fit_head(design, head, incoming, *, initial=None, tightened=False):
    began = perf_counter()
    priors = annual_priors(design, head, incoming)
    size = len(design.columns)*_width(head)+(8 if head == 'volume' else 0)
    if initial is None:
        initial = np.zeros(size)
        beta, age = _unpack(initial, design, head)
        for prior in priors:
            beta[prior['index']] = _conditional_mean(prior, age)
    reason = ('no_positive_exposure' if head == 'volume' and not np.any(design.exposure_hours > 0)
              else 'no_event_origin_weight' if head != 'volume' and not len(design.origin_weights) else None)
    metadata = dict(head=head, status='unavailable' if reason else 'incomplete', reasons=[] if reason is None else [reason],
                    priors=priors, ledger=list(incoming), centers=None, reference_predictor=None, age_curves=None,
                    objective=None, solver=None, diagnostics=None, resources=None)
    if reason:
        metadata['resources'] = dict(wall_seconds=perf_counter()-began, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return metadata, {}
    work = _head_work(design, head)
    options = CONTINUATION if tightened else SOLVER
    trace = []
    def objective(flat):
        value, gradient = head_objective(flat, design, head, priors, work)
        trace.append((float(value), float(np.max(np.abs(gradient)))))
        return value, gradient
    try:
        coefficients, solve = solve_logistic(objective, initial, maxiter=options['maxiter'],
                                             ftol=options['ftol'], gtol=options['gtol'])
        coefficients = _complete_prior_only(coefficients, design, head, priors)
        value, gradient = head_objective(coefficients, design, head, priors, work)
        solve.update(options=options, maxfun=15000, maxls=20, raw_gradient_inf_norm=float(np.max(np.abs(gradient))),
                     trace_summary=dict(evaluations=len(trace), initial=list(trace[0]), final=list(trace[-1]),
                                        minimum_objective=min(t[0] for t in trace)))
        metadata['solver'] = solve
        metadata['objective'] = head_objective(coefficients, design, head, priors, work, components=True)
        if not solve['converged']:
            metadata['status'] = 'failed'
            metadata['reasons'] = ['optimizer_failed']
            arrays = {}
        else:
            metadata['status'] = 'complete'
            beta, age = _unpack(coefficients, design, head)
            if head=='volume':
                metadata['age_curves']=dict(reference_age=27.,scale_years=10.,ridge_precision=64.,
                    curves=[dict(role=role,position_group=position,coefficients=age[start:start+2].tolist())
                            for role,position,start in (('offense','F',0),('offense','D',2),('defense','F',4),('defense','D',6))])
            ledger = {_actor_key(row): dict(row) for row in incoming}
            for prior in priors:
                prior['prior_mean'] = _conditional_mean(prior, age).tolist()
                if not prior['prior_only']:
                    ledger[_actor_key(prior)] = dict(block=prior['block'], id=prior['id'], subblock=prior['subblock'],
                        coefficient=beta[prior['index']].tolist(), season=design.season,
                        position_group=prior['position_group'], age=prior['age'],
                        support_seasons=prior['prior_seasons']+[design.season])
            metadata['ledger'] = [ledger[key] for key in sorted(ledger)]
            centers, reference, vector = centered_reference(design, head, beta)
            metadata['centers'], metadata['reference_predictor'] = centers, reference.tolist()
            arrays = {'coefficients': np.asarray(coefficients, dtype=np.float64)}
            metadata['diagnostics'] = head_diagnostics(design, head, beta)
    except (FloatingPointError, OverflowError, ValueError, InputContractError) as error:
        metadata.update(status='failed',reasons=[f'numerical_domain_failure:{type(error).__name__}:{error}'],
                        ledger=list(incoming),centers=None,reference_predictor=None,age_curves=None,diagnostics=None)
        for prior in priors:
            prior.pop('prior_mean',None)
        arrays = {}
    metadata['resources'] = dict(wall_seconds=perf_counter()-began, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                                dimensions=dict(rows=design.X_time.shape[0] if head == 'volume' else design.X_event.shape[0],
                                                features=len(design.columns), coordinates=size,
                                                grouped_time_rows=None if work is None else work['volume'][0].shape[0]))
    return metadata, arrays


def centered_reference(design, head, beta):
    """freeze every applicability mean; coach gates never enter a plain intercept."""
    exposure = float(design.exposure_hours.sum())
    require(exposure > 0, 'reference requires positive elapsed exposure')
    incidence = np.asarray(design.X_time.T@design.exposure_hours).ravel()
    special = _is_st(design)
    vector = np.zeros((3, len(design.columns))) if special else np.zeros(len(design.columns))
    centers = []
    reference = np.zeros((3, _width(head))) if special else np.zeros(_width(head))
    groups = {}
    for index, column in enumerate(design.columns):
        if column['kind'] == 'intercept':
            if special:
                vector[index, index] = 1.
                reference[index] += beta[index]
            else:
                vector[index] = 1.
                reference += beta[index]
        elif column['kind'] == 'actor':
            groups.setdefault((column['block'],column['subblock']), []).append(index)
            if not special:
                vector[index] = incidence[index]/exposure
    for (block, subblock), indices in groups.items():
        weight = float(incidence[indices].sum())
        mean = np.sum(beta[indices]*incidence[indices,None], axis=0)/weight if weight else np.zeros(_width(head))
        if special:
            applicability = (np.asarray([counts[0 if block == 'attacking_player' else 1]
                                         for counts in design.role_counts], dtype=float)
                             if block.endswith('_player') else np.full(3, weight/exposure))
            for state in range(3):
                vector[state, indices] = incidence[indices]/weight*applicability[state] if weight else 0.
            transferred = applicability[:, None]*mean
        else:
            applicability = weight/exposure
            transferred = mean*applicability
        reference += transferred
        centers.append(dict(block=block,subblock=subblock,indices=indices,weight_hours=weight,
                            mean=mean.tolist(),reference_applicability=applicability.tolist() if special else applicability,
                            reference_offset=transferred.tolist(),reason=None if weight else 'zero_applicable_time'))
    require(np.allclose(vector@beta,reference,rtol=1e-12,atol=1e-12), 'centered reference transfer differs')
    return centers, reference, vector


def _rates_from_logits(log_volume,shape_logits,quality_logits):
    """one positive-rate owner for raw and shared native-logit projections."""
    log_volume=np.asarray(log_volume)
    logp=shape_logits-logsumexp(shape_logits,axis=-1)[...,None]
    with np.errstate(over='raise',invalid='raise',under='ignore'):
        attempts=np.exp(log_volume[...,None]+logp)
        chance=np.exp(log_volume[...,None]+logp+log_expit(quality_logits))
    require(np.isfinite(attempts).all() and np.isfinite(chance).all()
            and np.all(attempts>0) and np.all(chance>0) and np.all(chance<=attempts),
            'invalid positive complete spatial rates')
    return np.stack((attempts,chance),axis=-2)


def evaluate_rates(design,predictors, *, state=None):
    """evaluate all three heads jointly; never clip positive physical rates."""
    v=np.asarray(predictors['volume'])
    s=np.asarray(predictors['shape'])
    q=np.asarray(predictors['quality'])
    offsets=design.annual_offsets
    if _is_st(design):
        require(state is not None, 'special-teams projection requires an exact physical state')
        offsets = {name:np.asarray(offsets[name])[state] for name in ('r','pi','qbar')}
        log_rate = np.log(offsets['r'])
    else:
        log_rate = math.log(offsets['r'])
    eta=log_rate+v[...,0]
    shape=np.log(offsets['pi'])+s@design.basis.T
    qbar=np.asarray(offsets['qbar'])
    quality_eta=np.log(qbar)-np.log1p(-qbar)+q[...,:1]+q[...,1:]@design.basis.T
    return _rates_from_logits(eta,shape,quality_eta)


def spatial_shapley(coalitions):
    values = np.asarray(coalitions,dtype=float)
    require(np.isfinite(values).all() and np.all(values>0), 'invalid positive rate coalitions')
    allocations = four_group_allocation(values)
    terms = np.r_[values[:1],allocations]
    residual = values[15]-terms.sum(axis=0)
    tolerance = 1e-10*(1+np.abs(values[15])+np.abs(terms).sum(axis=0))
    require(np.all(np.abs(residual)<=tolerance), 'spatial rate allocation does not close')
    return allocations


def head_diagnostics(design, head, beta):
    if head == 'volume':
        offset = _row_offsets(design, 'time')['r']
        eta = (np.log(offset) if _is_st(design) else math.log(offset))+_linear(design,beta,'time').ravel()
        expected = design.exposure_hours*np.exp(eta)
        result = dict(population=('retained advantaged-side physical time and attempts' if _is_st(design)
                                  else 'retained directed 5v5 time and uniquely assigned physical attempts'),
                    attempts=design.X_event.shape[0],hours=float(design.exposure_hours.sum()),
                    predicted_attempts=float(expected.sum()),residual=float(design.X_event.shape[0]-expected.sum()),
                    largest_complete_rates=[dict(key=design.time_keys[int(i)],attempts_per_hour=float(np.exp(eta[i]))) for i in np.argsort(eta)[-10:]])
        if _is_st(design):
            result['states'] = [dict(state=state, hours=float(design.exposure_hours[design.state_time == s].sum()),
                                    attempts=int(np.sum(design.state_event == s)),
                                    predicted_attempts=float(expected[design.state_time == s].sum()),
                                    residual=float(np.sum(design.state_event == s)-expected[design.state_time == s].sum()))
                                for s,state in enumerate(('5v4','5v3','4v3'))]
        return result
    loss = 0.
    expected_location = np.zeros(656)
    actual_location = np.bincount(design.origin_cells,weights=design.origin_weights,minlength=656)
    bins = [dict(lower=i/10,upper=(i+1)/10,origin_weight=0.,target_mass=0.,predicted_mass=0.) for i in range(10)]
    special = _is_st(design)
    if special:
        state_loss = np.zeros(3)
        state_actual = np.zeros((3,656))
        state_expected = np.zeros((3,656))
        state_bins = [[dict(row) for row in bins] for _ in range(3)]
    for start in range(0,design.X_event.shape[0],4096):
        stop = min(start+4096,design.X_event.shape[0])
        linear = _linear(design,beta,'event',slice(start,stop))
        left,right = design.event_offsets[start],design.event_offsets[stop]
        rows = np.repeat(np.arange(stop-start),np.diff(design.event_offsets[start:stop+1]))
        cells,weight = design.origin_cells[left:right],design.origin_weights[left:right]
        offsets = _row_offsets(design, 'event', slice(start, stop))
        if special:
            event_states = design.state_event[start:stop]
            origin_states = event_states[rows]
            state_actual += np.bincount(origin_states*656+cells,weights=weight,minlength=3*656).reshape(3,656)
        if head == 'shape':
            eta = np.log(offsets['pi'])+linear@design.basis.T
            logp = eta-logsumexp(eta,axis=1)[:,None]
            loss -= float(np.dot(weight,logp[rows,cells]))
            expected_location += np.exp(logp).sum(axis=0)
            if special:
                state_loss += np.bincount(origin_states,weights=-weight*logp[rows,cells],minlength=3)
                np.add.at(state_expected,event_states,np.exp(logp))
        else:
            qbar=np.asarray(offsets['qbar'])
            eta=np.log(qbar)-np.log1p(-qbar)+linear[:,:1]+linear[:,1:]@design.basis.T
            probability=expit(eta[rows,cells]);target=design.neutral_goal_probability[left:right]
            for i in range(10):
                mask=(probability>=i/10)&((probability<(i+1)/10) if i<9 else (probability<=1))
                bins[i]['origin_weight']+=float(weight[mask].sum())
                bins[i]['target_mass']+=float(np.dot(weight[mask],target[mask]))
                bins[i]['predicted_mass']+=float(np.dot(weight[mask],probability[mask]))
                if special:
                    for state_index in range(3):
                        state_mask = mask & (origin_states == state_index)
                        row = state_bins[state_index][i]
                        row['origin_weight'] += float(weight[state_mask].sum())
                        row['target_mass'] += float(np.dot(weight[state_mask],target[state_mask]))
                        row['predicted_mass'] += float(np.dot(weight[state_mask],probability[state_mask]))
    result = (dict(population='retained physical attempts with fractional native origins',
                 events=design.X_event.shape[0],eligible_origin_weight=float(design.origin_weights.sum()),
                 cross_entropy=loss/float(design.origin_weights.sum()),
                 native_location_residual=(actual_location-expected_location).tolist()) if head=='shape'
            else dict(population='retained origin-weighted fixed neutral opportunity probabilities',
                      events=design.X_event.shape[0],eligible_origin_weight=float(design.origin_weights.sum()),
                      target_neutral_chance_mass=float(np.dot(design.origin_weights,design.neutral_goal_probability)),calibration=bins))
    if special:
        result['states'] = []
        for s,name in enumerate(('5v4','5v3','4v3')):
            mass = float(state_actual[s].sum())
            result['states'].append(dict(state=name,events=int(np.sum(design.state_event==s)),eligible_origin_weight=mass,
                **(dict(cross_entropy=float(state_loss[s]/mass) if mass else None,
                        native_location_residual=(state_actual[s]-state_expected[s]).tolist()) if head=='shape'
                   else dict(calibration=state_bins[s]))))
    return result


def _projection_support(state, design, player, role=None, strength=None):
    source = dict(design.coverage.get('players',{}).get(player,{}))
    if _is_st(design):
        require(role in ROLES and strength is not None, 'special-teams support needs focal role and selector')
        source = dict(source['roles'][role]['common' if strength in ('pp','pk') else strength])
    reasons=source.get('reason_counts',{})
    source['reason_counts']=[dict(code=key,count=reasons[key]) for key in sorted(reasons)] if isinstance(reasons,dict) else reasons
    inferred=set(source.get('inferred_inputs',[]))
    if source.get('events',0)>0:inferred.add('setter')
    source['inferred_inputs']=sorted(inferred)
    priors = [row for head in HEADS for row in state.heads[head]['priors']
              if row['block'].endswith('_player') and row['id']==player and row['subblock']=='base'
              and (role is None or row['block']==('attacking' if role=='offense' else 'defending')+'_player')]
    if any(row['prior_kind']=='carry' for row in priors):source['inferred_inputs']=sorted(set(source['inferred_inputs'])|{'historical_borrowing'})
    source.update(eligible_weight=None,
                  current_season_information=any(row['current_season_information'] for row in priors),
                  prior_only=bool(priors) and all(row['prior_only'] for row in priors),
                  prior_seasons=sorted({year for row in priors for year in row['prior_seasons']}))
    return source


def _coefficient_support(state, design):
    result=[]
    by_state = [actor_support(design,state=s) for s in range(3)] if _is_st(design) else None
    for player in design.players:
        for role in ROLES:
            block=('attacking' if role=='offense' else 'defending')+'_player'
            for head in HEADS:
                metadata=state.heads[head]
                prior=next((r for r in metadata['priors'] if r['block']==block and r['id']==player and r['subblock']=='base'),None)
                available=metadata['status']=='complete' and prior is not None
                row = dict(season=design.season,player_id=player,role=role,head=head,available=available,
                    included_seconds=prior['included_seconds'] if available else None,
                    likelihood_events=prior['likelihood_events'] if available else None,
                    eligible_origin_weight=prior['eligible_origin_weight'] if available else None,
                    current_season_information=prior['current_season_information'] if available else None,
                    prior_only=prior['prior_only'] if available else None,
                    prior_kind=prior['prior_kind'] if available else None,
                    prior_anchor_season=prior['prior_anchor_season'] if available else None,
                    prior_seasons=prior['prior_seasons'] if available else [],
                    reason=None if available else 'missing_actor_coefficient' if prior is None else ':'.join(metadata['reasons']))
                if by_state is not None:
                    row['state_support'] = None
                    if available:
                        row['state_support'] = [dict(state=ST_STRENGTHS[s+1][0],
                            **{key:support[prior['index']][key] for key in
                               ('included_seconds','likelihood_events','eligible_origin_weight')})
                            for s,support in enumerate(by_state)]
                result.append(row)
    return result


def _context_groups(design, betas, references, centers, row, player, role, by_actor=None):
    """four departures from the frozen reference in raw predictor coordinates."""
    key=design.time_keys[row]
    own='attacking' if role=='offense' else 'defending'
    other='defending' if role=='offense' else 'attacking'
    if by_actor is None:
        by_actor={_actor_key(c):i for i,c in enumerate(design.columns) if c['kind']=='actor'}
    result={}
    for head in HEADS:
        beta=betas[head]
        width=_width(head)
        group=np.zeros((4,width))
        actor_centers={(c['block'],c['subblock']):np.asarray(c['mean']) for c in centers[head]}
        focal_index=by_actor[(own+'_player',player,'base')]
        group[0]=beta[focal_index]-actor_centers[(own+'_player','base')]
        for teammate in key[own+'_players']:
            if str(teammate)!=player:
                group[1]+=beta[by_actor[(own+'_player',str(teammate),'base')]]-actor_centers[(own+'_player','base')]
        for opponent in key[other+'_players']:
            group[2]+=beta[by_actor[(other+'_player',str(opponent),'base')]]-actor_centers[(other+'_player','base')]
        factual=_linear(design,beta,'time',slice(row,row+1)).ravel()
        reference = references[head][design.state_time[row]] if _is_st(design) else references[head]
        group[3]=factual-reference-group[:3].sum(axis=0)
        result[head]=group
    return result


def context_coalitions(design, betas, references, centers, row, player, role, by_actor=None):
    groups=_context_groups(design,betas,references,centers,row,player,role,by_actor)
    state = int(design.state_time[row]) if _is_st(design) else None
    predictors={head:np.asarray([(references[head][state] if state is not None else references[head])+groups[head][[g for g in range(4) if subset&(1<<g)]].sum(axis=0)
                                 for subset in range(16)]) for head in HEADS}
    return evaluate_rates(design,predictors,state=state)


def _actual_adjustments(design, betas, references, centers):
    """stream exact subsets; each state's reference stays with its focal hours."""
    special = _is_st(design)
    player_index = {player:i for i,player in enumerate(design.players)}
    actor_indices = {_actor_key(c):i for i,c in enumerate(design.columns) if c['kind']=='actor'}
    center_by_head = {head:{(c['block'],c['subblock']):np.asarray(c['mean']) for c in centers[head]} for head in HEADS}
    maps = np.zeros((len(design.players),4,2,2,7,656) if special else (len(design.players),2,2,7,656))
    seconds = np.zeros((len(design.players),4,2) if special else (len(design.players),2))
    representatives,exposure = _volume_groups(design)
    weights = FOUR_GROUP_WEIGHTS
    qbar = np.asarray(design.annual_offsets['qbar'])
    if special:
        native_reference = dict(volume=np.log(design.annual_offsets['r'])+references['volume'][:,0],
            shape=np.log(design.annual_offsets['pi'])+references['shape']@design.basis.T,
            quality=np.log(qbar)-np.log1p(-qbar)+references['quality'][:,:1]+references['quality'][:,1:]@design.basis.T)
    else:
        native_reference = dict(volume=math.log(design.annual_offsets['r'])+references['volume'][0],
            shape=np.log(design.annual_offsets['pi'])+references['shape']@design.basis.T,
            quality=np.log(qbar)-np.log1p(-qbar)+references['quality'][0]+references['quality'][1:]@design.basis.T)
    # each subset creates only batch x forty and batch x native-cell arrays.
    for start in range(0,len(representatives),16):
        selected = representatives[start:start+16]
        hours = exposure[start:start+16]
        pi,ri,si,context_weight = [],[],[],[]
        grouped = {head:[] for head in HEADS}
        factual = {head:_linear(design,betas[head],'time',selected) for head in HEADS}
        for j,row in enumerate(selected):
            key = design.time_keys[row]
            state = int(design.state_time[row]) if special else None
            for role_index,role in enumerate(ROLES):
                own = 'attacking' if role=='offense' else 'defending'
                other = 'defending' if role=='offense' else 'attacking'
                own_indices = [actor_indices[(own+'_player',str(p),'base')] for p in key[own+'_players']]
                other_indices = [actor_indices[(other+'_player',str(p),'base')] for p in key[other+'_players']]
                for head in HEADS:
                    beta = betas[head]
                    own_mean = center_by_head[head][(own+'_player','base')]
                    other_mean = center_by_head[head][(other+'_player','base')]
                    own_sum = beta[own_indices].sum(axis=0)-len(own_indices)*own_mean
                    other_sum = beta[other_indices].sum(axis=0)-len(other_indices)*other_mean
                    reference = references[head][state] if special else references[head]
                    context = factual[head][j]-reference-own_sum-other_sum
                    for index in own_indices:
                        self_effect = beta[index]-own_mean
                        grouped[head].append(np.stack((self_effect,own_sum-self_effect,other_sum,context)))
                for player in key[own+'_players']:
                    pi.append(player_index[str(player)])
                    ri.append(role_index)
                    if special: si.append(state)
                    context_weight.append(hours[j])
        pi,ri,si,context_weight = np.asarray(pi),np.asarray(ri),np.asarray(si),np.asarray(context_weight)
        grouped = {head:np.asarray(value) for head,value in grouped.items()}
        native_groups = dict(volume=grouped['volume'][...,0],
            shape=(grouped['shape'].reshape(-1,40)@design.basis.T).reshape(len(pi),4,656),
            quality=grouped['quality'][...,:1]+(grouped['quality'][...,1:].reshape(-1,40)@design.basis.T).reshape(len(pi),4,656))
        accumulated = np.zeros((len(pi),2,7,656))
        for subset in range(16):
            selected_groups = [g for g in range(4) if subset&(1<<g)]
            native = {head:(native_reference[head][si] if special else native_reference[head])
                      +native_groups[head][:,selected_groups].sum(axis=1) for head in HEADS}
            rate = _rates_from_logits(native['volume'],native['shape'],native['quality'])
            if subset==0: accumulated[:,:,0] = rate
            if subset==15: accumulated[:,:,6] = rate
            for group in range(4): accumulated[:,:,group+1] += weights[group,subset]*rate
        accumulated[:,:,5] = accumulated[:,:,6]-accumulated[:,:,:5].sum(axis=2)
        tolerance = 1e-10*(1+np.abs(accumulated[:,:,6])+np.abs(accumulated[:,:,:5]).sum(axis=2))
        require(np.all(np.abs(accumulated[:,:,5])<=tolerance),'batched exact context allocations do not close')
        indexes = (pi,si+1,ri) if special else (pi,ri)
        np.add.at(maps,indexes,context_weight[:,None,None,None]*accumulated)
        np.add.at(seconds,indexes,context_weight*3600)
    if special:
        # these remain integrated rates until divided by the player's own hours.
        maps[:,0] = maps[:,1:].sum(axis=1)
        seconds[:,0] = seconds[:,1:].sum(axis=1)
    rows = []
    for i,player in enumerate(design.players):
        for s in range(4 if special else 1):
            for r,role in enumerate(ROLES):
                index = (i,s,r) if special else (i,r)
                elapsed = float(seconds[index])
                available = elapsed>0
                selected_map = maps[index]
                if available:
                    selected_map /= elapsed/3600
                    values = selected_map.sum(axis=-1)
                    tolerance = 1e-10*(1+np.abs(selected_map[:,6])+np.abs(selected_map[:,:6]).sum(axis=1))
                    require(np.all(np.abs(selected_map[:,:6].sum(axis=1)-selected_map[:,6])<=tolerance),
                            'time-weighted native adjustment closure differs')
                    require(np.all(np.abs(values[:,:6].sum(axis=1)-values[:,6])<=1e-10*(1+np.abs(values[:,6])+np.abs(values[:,:6]).sum(axis=1))),
                            'time-weighted scalar adjustment closure differs')
                row = dict(season=design.season,player_id=player,role=role,available=available,
                    reason=None if available else 'no_exposure',exposure_seconds=elapsed,map_index=list(index),
                    **{q:{name:float(selected_map[qi,j].sum()) if available else None for j,name in enumerate(ADJUSTMENTS)}
                       for qi,q in enumerate(QUANTITIES)})
                if special:
                    row['strength'] = ST_STRENGTHS[s][r]
                    row['states'] = None
                    if available:
                        row['states'] = [dict(state=ST_STRENGTHS[t+1][0], seconds=float(seconds[i,t+1,r]),
                            weight=float(seconds[i,t+1,r]/elapsed)) for t in range(3)] if s == 0 else [
                            dict(state=ST_STRENGTHS[s][0], seconds=elapsed, weight=1.)]
                rows.append(row)
    return rows,maps


def project_spatial(state, design=None, *, actual_context=True):
    began=perf_counter()
    design=state.design if design is None else design
    require(design.season==state.manifest['season'] and design.purpose==state.manifest['purpose'],
            'projection design season/purpose differs')
    if _is_st(design):
        return _project_special_teams(state, design, actual_context=actual_context)
    complete=all(state.heads[head]['status']=='complete' for head in HEADS)
    support=_coefficient_support(state,design)
    rows=[]
    maps=np.zeros((len(design.players),2,2,3,656))
    reference=dict(kind='virtual elapsed linear design',units='per_hour',player_slots_per_role=5,
                   context='all centered non-actor coordinates zero',basis_identity=design.basis_identity,
                   annual_offsets=design.annual_offsets,heads={})
    betas,references,centers={},{},{}
    if complete:
        for head in HEADS:
            beta,_=_unpack(state.head_arrays[head]['coefficients'],design,head)
            centers[head],references[head],vector=centered_reference(design,head,beta)
            betas[head]=beta
            reference['heads'][head]=dict(vector=vector.tolist(),predictor=references[head].tolist(),centers=centers[head])
        neutral=evaluate_rates(design,references)
    reference_id=hashlib.sha256(json.dumps(reference,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    reference['sha256']=reference_id
    actor_indices={_actor_key(column):i for i,column in enumerate(design.columns) if column['kind']=='actor'}
    for i,player in enumerate(design.players):
        values={}
        reason=None if complete else 'incomplete_annual_family'
        for r,role in enumerate(ROLES):
            block=('attacking' if role=='offense' else 'defending')+'_player'
            focal={}
            if complete:
                require((block,player,'base') in actor_indices, 'roster actor lacks fitted coordinate')
                for head in HEADS:
                    mean=next(c['mean'] for c in centers[head] if (c['block'],c['subblock'])==(block,'base'))
                    focal[head]=references[head]+betas[head][actor_indices[(block,player,'base')]]-np.asarray(mean)
                rate=evaluate_rates(design,focal)
                maps[i,r,:,0]=neutral;maps[i,r,:,1]=rate;maps[i,r,:,2]=rate-neutral
            values[role]={q:{'difference':float(maps[i,r,qi,2].sum()) if complete else None,
                              'complete':float(maps[i,r,qi,1].sum()) if complete else None,
                              'neutral':float(maps[i,r,qi,0].sum()) if complete else None,
                              'relative_percent':float(100*maps[i,r,qi,2].sum()/maps[i,r,qi,0].sum()) if complete else None}
                          for qi,q in enumerate(QUANTITIES)}
        rows.append(dict(season=design.season,player_id=player,available=complete,reason=reason,values=values,
                         support=_projection_support(state,design,player),reference_id=reference_id,
                         units='per_hour',uncertainty='not_estimated'))
    if complete and actual_context:
        adjustments,adjustment_maps=_actual_adjustments(design,betas,references,centers)
    else:
        adjustment_maps=np.zeros((len(design.players),2,2,7,656))
        adjustments=[dict(season=design.season,player_id=p,role=r,available=False,
                         reason='not_evaluated' if complete else 'incomplete_annual_family',exposure_seconds=None,
                         map_index=[i,j],**{q:{k:None for k in ADJUSTMENTS} for q in QUANTITIES})
                     for i,p in enumerate(design.players) for j,r in enumerate(ROLES)]
    largest_rates,largest_contrasts=[],[]
    if complete:
        scalars=maps.sum(axis=-1)
        for kind,output in ((1,largest_rates),(2,largest_contrasts)):
            selected=scalars[:,:,:,kind]
            ordering=selected if kind==1 else np.abs(selected)
            for flat in np.argsort(ordering.ravel())[-20:]:
                i,r,q=np.unravel_index(flat,selected.shape)
                output.append(dict(player_id=design.players[i],role=ROLES[r],quantity=QUANTITIES[q],
                    reference_kind='complete_focal' if kind==1 else 'focal_minus_neutral',
                    value=float(selected[i,r,q]),units='per_hour'))
    diagnostics=dict(wall_seconds=perf_counter()-began,players=len(design.players),actual_context=actual_context,
                     population='all retained season-roster skaters, including available prior-only standardized projections',
                     reference_id=reference_id,assessment='in-sample construction diagnostics; no held-out performance claim',
                     peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                     largest_complete_rates=largest_rates,largest_absolute_contrasts=largest_contrasts)
    return SpatialProjections(rows,{'rates':maps,'adjustments':adjustment_maps},adjustments,support,reference,diagnostics)


def _project_special_teams(state, design, *, actual_context):
    began = perf_counter()
    complete = all(state.heads[head]['status']=='complete' for head in HEADS)
    support = _coefficient_support(state, design)
    rows = []
    maps = np.zeros((len(design.players),4,2,2,3,656))
    hours = np.asarray([design.exposure_hours[design.state_time==s].sum() for s in range(3)])
    league_weights = hours/hours.sum() if hours.sum()>0 else np.zeros(3)
    reference = dict(kind='virtual centered linear predictor by physical state',units='per_hour',
        states=['5v4','5v3','4v3'],player_slots_by_state=[list(c) for c in design.role_counts],
        context='all pooled-centered non-actor coordinates zero; pooled known-coach applicability',
        basis_identity=design.basis_identity,annual_offsets=design.annual_offsets,
        state_weights=[dict(state=ST_STRENGTHS[s+1][0],weight=float(league_weights[s])) for s in range(3)],heads={})
    betas,references,centers = {},{},{}
    if complete:
        for head in HEADS:
            beta,_ = _unpack(state.head_arrays[head]['coefficients'],design,head)
            centers[head],references[head],vector = centered_reference(design,head,beta)
            betas[head] = beta
            reference['heads'][head] = dict(vector=vector.tolist(),predictor=references[head].tolist(),centers=centers[head])
        neutral = evaluate_rates(design,references,state=np.arange(3))
    reference_id = hashlib.sha256(json.dumps(reference,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    reference['sha256'] = reference_id
    actor_indices = {_actor_key(column):i for i,column in enumerate(design.columns) if column['kind']=='actor'}
    for i,player in enumerate(design.players):
        for r,role in enumerate(ROLES):
            block = ('attacking' if role=='offense' else 'defending')+'_player'
            if complete:
                require((block,player,'base') in actor_indices, 'roster actor lacks specialty coordinate')
                focal = {}
                for head in HEADS:
                    mean = next(c['mean'] for c in centers[head] if (c['block'],c['subblock'])==(block,'base'))
                    focal[head] = references[head]+betas[head][actor_indices[(block,player,'base')]]-np.asarray(mean)
                rate = evaluate_rates(design,focal,state=np.arange(3))
                maps[i,1:,r,:,0] = neutral
                maps[i,1:,r,:,1] = rate
                maps[i,1:,r,:,2] = rate-neutral
                maps[i,0,r,:,:2] = np.einsum('s,sqkc->qkc',league_weights,maps[i,1:,r,:,:2])
                maps[i,0,r,:,2] = maps[i,0,r,:,1]-maps[i,0,r,:,0]
            for s in range(4):
                strength = ST_STRENGTHS[s][r]
                weights = ([dict(state=ST_STRENGTHS[t+1][r],weight=float(league_weights[t])) for t in range(3)]
                           if s==0 else [dict(state=strength,weight=1.)])
                values = {selected_role:{q:{key:None for key in ('difference','complete','neutral','relative_percent')}
                                        for q in QUANTITIES} for selected_role in ROLES}
                if complete:
                    for qi,q in enumerate(QUANTITIES):
                        scalar = maps[i,s,r,qi].sum(axis=-1)
                        relative = float(100*scalar[2]/scalar[0])
                        require(np.isfinite(scalar).all() and math.isfinite(relative), 'nonfinite special-teams scalar projection')
                        values[role][q] = dict(difference=float(scalar[2]),complete=float(scalar[1]),
                            neutral=float(scalar[0]),relative_percent=relative)
                rows.append(dict(season=design.season,player_id=player,strength=strength,role=role,
                    available=complete,reason=None if complete else 'incomplete_annual_family',values=values,
                    support=_projection_support(state,design,player,role,strength),reference_id=reference_id,
                    state_weights=weights,map_index=[i,s,r],units='per_hour',uncertainty='not_estimated'))
    if complete and actual_context:
        adjustments,adjustment_maps = _actual_adjustments(design,betas,references,centers)
    else:
        adjustment_maps = np.zeros((len(design.players),4,2,2,7,656))
        adjustments = [dict(season=design.season,player_id=p,strength=ST_STRENGTHS[s][r],role=role,
            available=False,reason='not_evaluated' if complete else 'incomplete_annual_family',
            exposure_seconds=None,map_index=[i,s,r],states=None,
            **{q:{k:None for k in ADJUSTMENTS} for q in QUANTITIES})
            for i,p in enumerate(design.players) for s in range(4) for r,role in enumerate(ROLES)]
    extremes = []
    if complete:
        scalars = maps.sum(axis=-1)
        for kind in (1,2):
            values = scalars[...,kind]
            for flat in np.argsort(np.abs(values).ravel())[-20:]:
                i,s,r,q = np.unravel_index(flat,values.shape)
                extremes.append(dict(player_id=design.players[i],strength=ST_STRENGTHS[s][r],role=ROLES[r],
                    quantity=QUANTITIES[q],kind='complete' if kind==1 else 'difference',value=float(values[i,s,r,q])))
    diagnostics = dict(wall_seconds=perf_counter()-began,players=len(design.players),actual_context=actual_context,
        population='every identified annual roster skater, each specialist role, exact states and common league mixture',
        reference_id=reference_id,assessment='in-sample construction diagnostics; no held-out performance claim',
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,extreme_projections=extremes)
    if complete and actual_context:
        cancellations=[]
        largest_terms=[]
        for row in adjustments:
            if not row['available']:continue
            for q in QUANTITIES:
                values=row[q]
                absolute=sum(abs(values[name]) for name in ADJUSTMENTS[:5])
                locator=dict(player_id=row['player_id'],strength=row['strength'],role=row['role'],quantity=q)
                cancellations.append(dict(locator,absolute_terms_per_hour=absolute,
                    factual_per_hour=values['factual'],cancellation_per_hour=max(0.,absolute-abs(values['factual']))))
                for term in ADJUSTMENTS[:5]:
                    largest_terms.append(dict(locator,term=term,value=values[term]))
        diagnostics['largest_allocation_cancellations']=sorted(cancellations,key=lambda row:row['cancellation_per_hour'])[-20:]
        diagnostics['largest_absolute_allocation_terms']=sorted(largest_terms,key=lambda row:abs(row['value']))[-20:]
    return SpatialProjections(rows,{'rates':maps,'adjustments':adjustment_maps},adjustments,support,reference,diagnostics)


def _annual_design(design, previous_state, *, basis_source=None):
    from .spatial_state import validate_design
    special = _is_st(design)
    if special:
        require((previous_state is None) == (basis_source is not None),
                'first specialty year requires only an accepted ev basis; later years require only their st predecessor')
    if previous_state is not None:
        require(previous_state.manifest['purpose']==design.purpose and all(previous_state.heads[h]['status']=='complete' for h in HEADS),
                'incomplete or mismatched spatial predecessor')
        if special:
            require(previous_state.manifest.get('family')=='st' and previous_state.manifest['recipe']==ST_RECIPE,
                    'specialty predecessor family/recipe differs')
        require(int(design.season[:4])==int(previous_state.manifest['season'][:4])+1,'spatial predecessor is not consecutive')
        require(previous_state.manifest['prepared']['sha256']==design.prepared['sha256']
                and previous_state.manifest['coaches']['sha256']==design.coaches['sha256'], 'spatial predecessor source owners differ')
        same_basis = (design.basis is None or (np.array_equal(design.basis,previous_state.design.basis) if special
                      else np.allclose(design.basis,previous_state.design.basis,atol=1e-12,rtol=0)))
        require(same_basis,'spatial basis rotated between years')
        design=replace(design,basis=previous_state.design.basis.copy(),basis_identity=previous_state.design.basis_identity)
        if special:
            design=replace(design,basis_source=previous_state.design.basis_source)
    elif design.purpose=='real':
        require(design.season=='20212022','real spatial chain must begin in 20212022')
    if special and basis_source is not None:
        from .spatial_state import read_spatial_basis
        from .chance_cli import read_json
        path=Path(basis_source).resolve()
        if path.is_dir(): path=path/'manifest.json'
        basis,basis_identity=read_spatial_basis(path)
        source_manifest=read_json(path)
        require(source_manifest['purpose']==design.purpose and source_manifest['season']==design.season,
                'specialty basis donor purpose or first year differs')
        member=next(row for row in source_manifest['files'] if row['path']=='design.npz')
        source=dict(identity(path),archive=dict(path=str(path.parent/'design.npz'),sha256=member['sha256']))
        design=replace(design,basis=basis,basis_identity=basis_identity,basis_source=source)
    validate_design(design)
    return design


def _finish_spatial_annual(design, previous_state, output, heads, arrays, resources):
    from .spatial_state import SpatialState, write_spatial_state
    special=_is_st(design)
    manifest=dict(schema_version=1,kind='spatial_st_state' if special else 'spatial_state',purpose=design.purpose,season=design.season,
                  recipe_id='experimental-v1',recipe=ST_RECIPE if special else RECIPE,design_identity=design.transforms['design_sha256'],
                  implementation=implementation(),prepared=design.prepared,coaches=design.coaches,valued=design.valued,
                  previous=None if previous_state is None else dict(identity(previous_state.path/'manifest.json'),
                      season=previous_state.manifest['season'],purpose=design.purpose,usage='annual'),
                  basis_identity=design.basis_identity,training_cutoff=design.training_cutoff,heads=[],files=[],
                  resources=resources)
    if special:
        manifest.update(family='st',basis_source=design.basis_source)
    state=SpatialState(output,manifest,design,heads,arrays,[],{},[],[],{})
    projections=project_spatial(state)
    return write_spatial_state(state,projections)


def fit_spatial(design, previous_state, output, *, basis_source=None, final_year=False):
    """fit one annual family and preserve it before any numerical continuation."""
    began=perf_counter()
    if _is_st(design):
        from .chance_cli import output_path
        roots=[str(Path(getattr(design,name)['path']).parent) for name in ('prepared','coaches','valued')]
        if previous_state is not None:roots.append(str(previous_state.path))
        if basis_source is not None:
            basis_path=Path(basis_source).resolve()
            roots.append(str(basis_path if basis_path.is_dir() else basis_path.parent))
        output=output_path(str(output),roots)
    design=_annual_design(design,previous_state,basis_source=basis_source)
    output=Path(output).resolve()
    require(not output.exists(),'spatial output already exists')
    if design.purpose=='real':
        require(output.is_relative_to('/Volumes/Expansion/hockey-stats'),'expensive real outputs must be external')
    output.mkdir(parents=True)
    heads,arrays={},{}
    for head in HEADS:
        incoming=[] if previous_state is None else previous_state.heads[head]['ledger']
        heads[head],arrays[head]=fit_head(design,head,incoming)
        # preserve each completed expensive head even if a later head fails.
        from .spatial_state import write_spatial_head
        write_spatial_head(output,heads[head],arrays[head])
    baseline=_finish_spatial_annual(design,previous_state,output,heads,arrays,
        dict(design=design.resources,fit_wall_seconds=perf_counter()-began,
             peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    if ((design.purpose=='real' and design.season=='20252026') or final_year) and (_is_st(design) or all(heads[h]['status']=='complete' for h in HEADS)):
        from .spatial_state import bind_spatial_probes
        return bind_spatial_probes(baseline,run_numerical_probes(baseline))
    return baseline


def complete_spatial(design, previous_state, source, output, *, expected_files, expected_inputs):
    """complete preserved ordinary heads; no solve, refill or numerical continuation."""
    from .spatial_state import read_completed_spatial_heads, copy_completed_spatial_heads
    began=perf_counter();source=Path(source).resolve();output=Path(output).resolve()
    require(previous_state is not None,'completed spatial heads require an accepted predecessor')
    require(not output.exists() and output!=source and not output.is_relative_to(source),'spatial completion output already exists or overlaps its source')
    if design.purpose=='real': require(output.is_relative_to('/Volumes/Expansion/hockey-stats'),'expensive real outputs must be external')
    design=_annual_design(design,previous_state)
    inputs={key:{name:getattr(design,key)[name] for name in ('path','sha256')} for key in ('prepared','coaches','valued')}
    inputs['previous']=identity(previous_state.path/'manifest.json')
    require(expected_inputs==inputs,'completed spatial original input bindings differ')
    heads,arrays,files=read_completed_spatial_heads(source,design,
        {head:previous_state.heads[head]['ledger'] for head in HEADS},expected_files)
    load_wall=perf_counter()-began;check_started=perf_counter();anchors={}
    for head in HEADS:
        work=_head_work(design,head)
        grouped=None if work is None else work['volume'][0].shape[0]
        require(grouped==heads[head]['resources']['dimensions']['grouped_time_rows'],'completed spatial grouping differs')
        value,gradient=head_objective(arrays[head]['coefficients'],design,head,heads[head]['priors'],work)
        norm=float(np.max(np.abs(gradient)))
        require(value==heads[head]['objective']['total'] and norm==heads[head]['solver']['raw_gradient_inf_norm'],
                'completed spatial objective/gradient anchor differs')
        anchors[head]=dict(objective=heads[head]['objective'],raw_gradient_inf_norm=norm,full_evaluations=1,grouped_time_rows=grouped)
    check_wall=perf_counter()-check_started
    copy_started=perf_counter();output.mkdir(parents=True)
    copy_completed_spatial_heads(source,output,files)
    copy_wall=perf_counter()-copy_started
    completion=dict(source_files=files,anchors=anchors,
        reconstruction_limit='original design and moments were not saved; deterministic input reconstruction and exact head checks do not establish old/new design-byte equality')
    resources=dict(design=design.resources,fit_wall_seconds=0.,new_solver_calls=0,new_probe_calls=0,
        head_load_validation_wall_seconds=load_wall,consistency_wall_seconds=check_wall,head_copy_wall_seconds=copy_wall,
        retained_head_wall_seconds=sum(heads[head]['resources']['wall_seconds'] for head in HEADS),
        retained_head_resources={head:heads[head]['resources'] for head in HEADS},
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        peak_rss_scope='new process through restored-head qualification/copy; excludes fresh projection/write/canonical read',
        completion=completion)
    return _finish_spatial_annual(design,previous_state,output,heads,arrays,resources)




def probe_descriptor(state):
    """immutable fitted baseline, excluding final probe receipts and resource totals."""
    return dict(schema_version=1,purpose=state.manifest['purpose'],season=state.manifest['season'],
                recipe=state.manifest['recipe'],prepared=state.manifest['prepared'],coaches=state.manifest['coaches'],
                valued=state.manifest['valued'],previous=state.manifest['previous'],
                design_identity=state.manifest['design_identity'],basis_identity=state.manifest['basis_identity'],
                heads={head:dict(metadata_sha256=hashlib.sha256(json.dumps(state.heads[head],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),
                                 arrays_sha256=ordered_array_digest(state.head_arrays[head])) for head in HEADS})


def _probe_sort(key,role,player):
    return (key['game_id'],key['segment_index'],key['chunk_index'],
            -1 if key['source_index'] is None else key['source_index'],role,player)


def select_probe_rows(state):
    """first physical key for each written requirement, then source-key fill."""
    design=state.design
    special=_is_st(design)
    priors={(row['block'],row['id']):row for row in state.heads['volume']['priors'] if row['block'].endswith('_player')}
    entry_actors,return_actors=set(),set()
    for head in (HEADS if special else ('volume',)):
        for prior in state.heads[head]['priors']:
            if not prior['block'].endswith('_player'):continue
            actor=(prior['block'],prior['id'])
            if prior['prior_kind']=='entry':entry_actors.add(actor)
            elif prior['prior_kind']=='carry' and int(design.season[:4])-int(prior['prior_anchor_season'][:4])>1:return_actors.add(actor)
    teams={p:set() for p in design.players}
    for key in design.time_keys:
        for side in ('attacking','defending'):
            for player in key[side+'_players']:
                team=key.get(side+'_team_id')
                if team is not None: teams[str(player)].add(team)
    witnesses={}
    def candidates():
        for kind,keys in (('time',design.time_keys),('event',design.event_keys)):
            for index,key in enumerate(keys):
                for role,side in (('defense','defending'),('offense','attacking')):
                    for player in map(str,key[side+'_players']):
                        actor=((side if special else 'attacking')+'_player',player)
                        prior=priors[actor]
                        requirements=[]
                        if special:
                            physical_state=int((design.state_time if kind=='time' else design.state_event)[index])
                            requirements.append(f'state:{ST_STRENGTHS[physical_state+1][0]}:{role}')
                        if key.get('boundary_goal'):requirements.append('boundary_goals')
                        if key.get('optional_missing'):requirements.append('missing_optional_inputs')
                        if actor in entry_actors:requirements.append('entries')
                        if actor in return_actors:requirements.append('returns')
                        if len(teams[player])>1:requirements.append('trades')
                        if prior['included_seconds']<(50 if special else 300)*60:requirements.append('sparse_support')
                        row=dict(kind=kind,index=index,key=key,role=role,player_id=player,requirements=requirements)
                        order=_probe_sort(key,role,player)
                        for name in requirements:
                            old=witnesses.get(name)
                            if old is None or order<_probe_sort(old['key'],old['role'],old['player_id']):witnesses[name]=row
                        yield row
    fill=heapq.nsmallest(256,candidates(),key=lambda row:_probe_sort(row['key'],row['role'],row['player_id']))
    selected={}
    names=([f'state:{physical}:{role}' for physical in ('5v4','5v3','4v3') for role in ROLES] if special else [])
    names+=['boundary_goals','missing_optional_inputs','entries','returns','trades','sparse_support']
    for name in names:
        witness=witnesses.get(name)
        if witness is not None:selected[(witness['kind'],witness['index'],witness['role'],witness['player_id'])]=witness
    for row in fill:
        if len(selected)>=256:break
        selected.setdefault((row['kind'],row['index'],row['role'],row['player_id']),row)
    return sorted(selected.values(),key=lambda r:_probe_sort(r['key'],r['role'],r['player_id']))



def _probe_contexts(state,selected):
    design=state.design
    betas,references,centers={},{},{}
    for head in HEADS:
        betas[head],_=_unpack(state.head_arrays[head]['coefficients'],design,head)
        centers[head],references[head],_=centered_reference(design,head,betas[head])
    by_actor={_actor_key(c):i for i,c in enumerate(design.columns) if c['kind']=='actor'}
    for row in selected:
        view=design
        if row['kind']=='event':
            view=replace(design,X_time=design.X_event,context_time=design.context_event,time_keys=design.event_keys)
            if _is_st(design):view=replace(view,state_time=design.state_event)
        groups=_context_groups(view,betas,references,centers,row['index'],row['player_id'],row['role'],by_actor)
        exact_state=int(view.state_time[row['index']]) if _is_st(design) else None
        predictors={head:np.asarray([(references[head][exact_state] if exact_state is not None else references[head])+groups[head][[g for g in range(4) if subset&(1<<g)]].sum(axis=0)
                                      for subset in range(16)]) for head in HEADS}
        rates=evaluate_rates(design,predictors,state=exact_state)
        offsets=design.annual_offsets if exact_state is None else {name:np.asarray(design.annual_offsets[name])[exact_state] for name in ('r','pi','qbar')}
        shape=np.log(offsets['pi'])+predictors['shape']@design.basis.T
        shape=np.exp(shape-logsumexp(shape,axis=1)[:,None])
        qbar=np.asarray(offsets['qbar'])
        quality=expit(np.log(qbar)-np.log1p(-qbar)+predictors['quality'][:,:1]+predictors['quality'][:,1:]@design.basis.T)
        yield row,rates,spatial_shapley(rates),shape,quality



def _standardized_probabilities(state):
    design=state.design
    if _is_st(design):
        values={}
        actors={_actor_key(c):i for i,c in enumerate(design.columns) if c['kind']=='actor'}
        for head in ('shape','quality'):
            beta,_=_unpack(state.head_arrays[head]['coefficients'],design,head)
            centers,reference,_=centered_reference(design,head,beta)
            mean={(c['block'],c['subblock']):np.asarray(c['mean']) for c in centers}
            residual=np.asarray([[beta[actors[(block,p,'base')]]-mean[(block,'base')]
                                  for block in ('attacking_player','defending_player')] for p in design.players])
            predictors=reference[None,:,None,:]+residual[:,None,:,:]
            if head=='shape':
                eta=np.log(design.annual_offsets['pi'])[None,:,None,:]+predictors@design.basis.T
                values[head]=np.exp(eta-logsumexp(eta,axis=-1)[...,None])
                eta=np.log(design.annual_offsets['pi'])+reference@design.basis.T
                values['neutral_'+head]=np.exp(eta-logsumexp(eta,axis=-1)[:,None])
            else:
                qbar=np.asarray(design.annual_offsets['qbar'])
                offset=np.log(qbar)-np.log1p(-qbar)
                values[head]=expit(offset[None,:,None,:]+predictors[...,:1]+predictors[...,1:]@design.basis.T)
                values['neutral_'+head]=expit(offset+reference[:,:1]+reference[:,1:]@design.basis.T)
        return values
    actors={_actor_key(c):i for i,c in enumerate(design.columns) if c['kind']=='actor'}
    values={}
    for head in ('shape','quality'):
        beta,_=_unpack(state.head_arrays[head]['coefficients'],design,head)
        centers,reference,_=centered_reference(design,head,beta)
        mean={(c['block'],c['subblock']):np.asarray(c['mean']) for c in centers}
        predictors=[]
        for player in design.players:
            for block in ('attacking_player','defending_player'):
                predictors.append(reference+beta[actors[(block,player,'base')]]-mean[(block,'base')])
        predictors=np.asarray(predictors)
        if head=='shape':
            eta=np.log(design.annual_offsets['pi'])+predictors@design.basis.T
            values[head]=np.exp(eta-logsumexp(eta,axis=1)[:,None]).reshape(len(design.players),2,656)
            neutral_eta=np.log(design.annual_offsets['pi'])+reference@design.basis.T
            values['neutral_'+head]=np.exp(neutral_eta-logsumexp(neutral_eta))
        else:
            qbar=np.asarray(design.annual_offsets['qbar'])
            values[head]=expit(np.log(qbar)-np.log1p(-qbar)+predictors[:,:1]+predictors[:,1:]@design.basis.T).reshape(len(design.players),2,656)
            values['neutral_'+head]=expit(np.log(qbar)-np.log1p(-qbar)+reference[0]+reference[1:]@design.basis.T)
    return values

def compare_probe(state,head,metadata,arrays,selected):
    if _is_st(state.design):
        if metadata['status']!='complete':
            return dict(status='unassessed',reason='continuation_failed',maxima=None,
                        failures=[dict(head=head,reasons=metadata['reasons'])])
        heads=dict(state.heads);heads[head]=metadata
        head_arrays=dict(state.head_arrays);head_arrays[head]=arrays
        return _compare_st_variant(state,replace(state,heads=heads,head_arrays=head_arrays),selected)
    if metadata['status']!='complete':
        return dict(status='failed',reason='continuation_failed',maxima=None,failures=[dict(head=head,reasons=metadata['reasons'])])
    variant_heads=dict(state.heads);variant_heads[head]=metadata
    variant_arrays=dict(state.head_arrays);variant_arrays[head]=arrays
    variant=replace(state,heads=variant_heads,head_arrays=variant_arrays)
    baseline=project_spatial(state,actual_context=False)
    changed=project_spatial(variant,actual_context=False)
    # locators name the actual maximal entry; no selection of benign examples.
    maxima={}
    failures=[]
    def record(name,values,limit,locator):
        values=np.asarray(values)
        flat=int(np.argmax(np.abs(values))) if values.size else 0
        magnitude=0. if not values.size else float(np.abs(values).ravel()[flat])
        item=dict(value=magnitude,limit=limit,locator=locator(np.unravel_index(flat,values.shape)) if values.size else None)
        if name not in maxima or magnitude>maxima[name]['value']:maxima[name]=item
        if magnitude>limit:failures.append(dict(quantity=name,**item))
    base_probability=_standardized_probabilities(state)
    changed_probability=_standardized_probabilities(variant)
    for name in ('shape','quality'):
        record('standardized_'+name+'_probability',changed_probability[name]-base_probability[name],1e-5,
               lambda i:dict(player_id=state.design.players[i[0]],role=ROLES[i[1]],cell=int(i[2])))
        record('neutral_'+name+'_probability',changed_probability['neutral_'+name]-base_probability['neutral_'+name],1e-5,lambda i:dict(kind='neutral',cell=int(i[0])))
    delta=changed.arrays['rates']-baseline.arrays['rates']
    record('standardized_scalar_per_hour',delta.sum(axis=-1),1e-4,
           lambda i:dict(player_id=state.design.players[i[0]],role=ROLES[i[1]],quantity=QUANTITIES[i[2]],kind=('neutral','complete','difference')[i[3]]))
    record('standardized_native_map_l1',np.abs(delta).sum(axis=-1),1e-4,
           lambda i:dict(player_id=state.design.players[i[0]],role=ROLES[i[1]],quantity=QUANTITIES[i[2]],kind=('neutral','complete','difference')[i[3]]))
    record('prospective_1000_minute_goals',delta[:,:,1,2].sum(axis=-1)*(1000/60),1e-3,
           lambda i:dict(player_id=state.design.players[i[0]],role=ROLES[i[1]]))
    for base,probe in zip(_probe_contexts(state,selected),_probe_contexts(variant,selected),strict=True):
        row,rate,allocation,shape,quality=base
        _,changed_rate,changed_allocation,changed_shape,changed_quality=probe
        locator=lambda i:dict(kind=row['kind'],key=row['key'],player_id=row['player_id'],role=row['role'],coordinate=list(map(int,i)))
        record('shape_probability',changed_shape-shape,1e-5,locator)
        record('quality_probability',changed_quality-quality,1e-5,locator)
        record('coalition_scalar_per_hour',(changed_rate-rate).sum(axis=-1),1e-4,locator)
        record('coalition_native_map_l1',np.abs(changed_rate-rate).sum(axis=-1),1e-4,locator)
        record('allocation_scalar_per_hour',(changed_allocation-allocation).sum(axis=-1),1e-4,locator)
        record('allocation_native_map_l1',np.abs(changed_allocation-allocation).sum(axis=-1),1e-4,locator)
    return dict(status='passed' if not failures else 'failed',reason=None if not failures else 'numerical_movement_exceeds_budget',
                maxima=maxima,failures=failures)


def _compare_st_variant(state, variant, selected):
    if not all(state.heads[h]['status']=='complete' and variant.heads[h]['status']=='complete' for h in HEADS):
        return dict(status='unassessed',reason='incomplete_baseline_family',maxima=None,failures=[])
    baseline=project_spatial(state,actual_context=False)
    stage='variant_projection'
    try:
        changed=project_spatial(variant,actual_context=False)
        maxima,failures={},[]
        def record(name,values,limit,locator):
            values=np.asarray(values)
            flat=int(np.argmax(np.abs(values))) if values.size else 0
            magnitude=float(np.abs(values).ravel()[flat]) if values.size else 0.
            item=dict(value=magnitude,limit=limit,locator=locator(np.unravel_index(flat,values.shape)) if values.size else None)
            if name not in maxima or magnitude>maxima[name]['value']:maxima[name]=item
            if magnitude>limit:failures.append(dict(quantity=name,**item))
        stage='baseline_probabilities'
        before=_standardized_probabilities(state)
        stage='variant_probabilities'
        after=_standardized_probabilities(variant)
        for name in ('shape','quality'):
            record('standardized_'+name+'_probability',after[name]-before[name],1e-5,
                lambda i:dict(player_id=state.design.players[i[0]],state=ST_STRENGTHS[i[1]+1][i[2]],role=ROLES[i[2]],cell=int(i[3])))
            record('neutral_'+name+'_probability',after['neutral_'+name]-before['neutral_'+name],1e-5,
                lambda i:dict(state=ST_STRENGTHS[i[0]+1][0],kind='neutral',cell=int(i[1])))
        delta=changed.arrays['rates']-baseline.arrays['rates']
        def locator(i):
            return dict(player_id=state.design.players[i[0]],strength=ST_STRENGTHS[i[1]][i[2]],
                        role=ROLES[i[2]],quantity=QUANTITIES[i[3]],kind=('neutral','complete','difference')[i[4]])
        record('standardized_scalar_per_hour',delta.sum(axis=-1),1e-4,locator)
        record('standardized_native_map_l1',np.abs(delta).sum(axis=-1),1e-4,locator)
        record('prospective_100_minute_goals',delta[:,0,:,1,2].sum(axis=-1)*(100/60),1e-3,
            lambda i:dict(player_id=state.design.players[i[0]],role=ROLES[i[1]],
                          ledger_sign=1 if i[1]==0 else -1))
        baseline_contexts=_probe_contexts(state,selected)
        variant_contexts=_probe_contexts(variant,selected)
        stage='baseline_context'
        for base in baseline_contexts:
            stage='variant_context'
            probe=next(variant_contexts)
            row,rate,allocation,shape,quality=base
            _,changed_rate,changed_allocation,changed_shape,changed_quality=probe
            context_locator=lambda i:dict(kind=row['kind'],key=row['key'],player_id=row['player_id'],role=row['role'],coordinate=list(map(int,i)))
            record('shape_probability',changed_shape-shape,1e-5,context_locator)
            record('quality_probability',changed_quality-quality,1e-5,context_locator)
            record('coalition_scalar_per_hour',(changed_rate-rate).sum(axis=-1),1e-4,context_locator)
            record('coalition_native_map_l1',np.abs(changed_rate-rate).sum(axis=-1),1e-4,context_locator)
            record('allocation_scalar_per_hour',(changed_allocation-allocation).sum(axis=-1),1e-4,context_locator)
            record('allocation_native_map_l1',np.abs(changed_allocation-allocation).sum(axis=-1),1e-4,context_locator)
            stage='baseline_context'
        return dict(status='exceeded' if failures else 'within_budget',
                    reason='numerical_movement_exceeds_diagnostic_flags' if failures else None,
                    maxima=maxima,failures=failures)

    except (FloatingPointError, OverflowError, InputContractError) as error:
        if not stage.startswith('variant_'):
            raise
        if isinstance(error, InputContractError) and str(error) not in (
                'invalid positive complete spatial rates', 'nonfinite special-teams scalar projection'):
            raise
        return dict(status='unassessed',reason='diagnostic_projection_numerical_domain_failure',maxima=None,
                    failures=[dict(stage=stage,error_type=type(error).__name__,message=str(error))])


def _run_st_probes(state):
    from .artifacts import write_json,write_arrays
    from .spatial_state import _write_rows
    folder=state.path/'probes'
    folder.mkdir()
    baseline=probe_descriptor(state)
    selected=select_probe_rows(state)
    names=[f'state:{physical}:{role}' for physical in ('5v4','5v3','4v3') for role in ROLES]
    names+=['boundary_goals','missing_optional_inputs','entries','returns','trades','sparse_support']
    write_json(folder/'baseline.json',baseline)
    write_json(folder/'rows.json',selected)
    write_json(folder/'requirements.json',[dict(requirement=name,
        disposition='actual' if any(name in row['requirements'] for row in selected) else 'no_matching_context',
        key=next((row['key'] for row in selected if name in row['requirements']),None)) for name in names])
    result=dict(baseline=baseline,rows=selected,heads={})
    variant_heads,variant_arrays=dict(state.heads),dict(state.head_arrays)
    for head in HEADS:
        if state.heads[head]['status']!='complete':
            comparison=dict(status='unassessed',reason='baseline_head_not_complete',maxima=None,
                            failures=[dict(head=head,reasons=state.heads[head]['reasons'])])
            metadata,arrays=state.heads[head],{}
            attempt=dict(status='not_run',reason='baseline_head_not_complete')
        else:
            incoming={_actor_key(r):r for r in state.heads[head]['ledger'] if r['season']!=state.design.season}
            incoming.update({_actor_key(p['last_supported']):p['last_supported'] for p in state.heads[head]['priors']
                             if p['last_supported'] is not None})
            metadata,arrays=fit_head(state.design,head,list(incoming.values()),
                initial=state.head_arrays[head]['coefficients'],tightened=True)
            comparison=compare_probe(state,head,metadata,arrays,selected)
            attempt=dict(status='attempted',reason=None)
        write_json(folder/f'{head}.json',metadata)
        write_json(folder/f'{head}-attempt.json',attempt)
        if arrays:
            write_arrays(folder,f'{head}.npz',arrays)
            variant_heads[head],variant_arrays[head]=metadata,arrays
            if all(state.heads[h]['status']=='complete' for h in HEADS) and comparison['reason']!='diagnostic_projection_numerical_domain_failure':
                heads=dict(state.heads);heads[head]=metadata
                values=dict(state.head_arrays);values[head]=arrays
                changed=project_spatial(replace(state,heads=heads,head_arrays=values),actual_context=False)
                write_arrays(folder,f'{head}-projections.npz',{'rates':changed.arrays['rates']})
                _write_rows(folder/f'{head}-projections.jsonl',changed.rows)
        write_json(folder/f'{head}-comparison.json',comparison)
        result['heads'][head]=dict(metadata=metadata,arrays=arrays,comparison=comparison,attempt=attempt)
    all_variants=all(result['heads'][head]['attempt']['status']=='attempted'
                     and result['heads'][head]['metadata']['status']=='complete'
                     and result['heads'][head]['comparison']['reason']!='diagnostic_projection_numerical_domain_failure'
                     for head in HEADS)
    joint=(_compare_st_variant(state,replace(state,heads=variant_heads,head_arrays=variant_arrays),selected)
           if all_variants else dict(status='unassessed',reason='one_or_more_continuations_unavailable',maxima=None,failures=[]))
    write_json(folder/'joint-comparison.json',joint)
    result['joint']=joint
    return result


def run_numerical_probes(state):
    """one continuation per head; source keys and baseline freeze before solving."""
    if _is_st(state.design):
        return _run_st_probes(state)
    from .artifacts import write_json,write_arrays
    folder=state.path/'probes';folder.mkdir()
    baseline=probe_descriptor(state)
    selected=select_probe_rows(state)
    write_json(folder/'baseline.json',baseline)
    write_json(folder/'rows.json',selected)
    write_json(folder/'requirements.json',[dict(requirement=name,disposition='actual' if any(name in row['requirements'] for row in selected) else 'no_matching_context',
                 key=next((row['key'] for row in selected if name in row['requirements']),None))
                 for name in ('boundary_goals','missing_optional_inputs','entries','returns','trades','sparse_support')])
    result=dict(baseline=baseline,rows=selected,heads={})
    for head in HEADS:
        incoming=[r['last_supported'] for r in state.heads[head]['priors'] if r['last_supported'] is not None]
        # retain absent historical actors as well as the entering actors' anchors.
        incoming_by_key={_actor_key(r):r for r in state.heads[head]['ledger'] if r['season']!=state.design.season}
        incoming_by_key.update({_actor_key(r):r for r in incoming})
        metadata,arrays=fit_head(state.design,head,list(incoming_by_key.values()),
                                 initial=state.head_arrays[head]['coefficients'],tightened=True)
        comparison=compare_probe(state,head,metadata,arrays,selected)
        write_json(folder/f'{head}.json',metadata)
        if arrays:write_arrays(folder,f'{head}.npz',arrays)
        if arrays:
            from .spatial_state import _write_rows
            changed_heads=dict(state.heads);changed_heads[head]=metadata
            changed_arrays=dict(state.head_arrays);changed_arrays[head]=arrays
            changed=project_spatial(replace(state,heads=changed_heads,head_arrays=changed_arrays),actual_context=False)
            write_arrays(folder,f'{head}-projections.npz',{'rates':changed.arrays['rates']})
            _write_rows(folder/f'{head}-projections.jsonl',changed.rows)
        write_json(folder/f'{head}-comparison.json',comparison)
        result['heads'][head]=dict(metadata=metadata,arrays=arrays,comparison=comparison)
    return result
