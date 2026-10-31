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
from scipy.sparse import csr_matrix, vstack

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



def _linear(design,beta,kind,rows=None):
    actor=getattr(design,'X_'+kind)
    context=getattr(design,'context_'+kind)
    split=actor.shape[1]
    if rows is not None:
        actor,context=actor[rows],context[rows]
    return np.asarray(actor@beta[:split])+np.asarray(context@beta[split:])


def _adjoint(design,residual,kind,rows=None):
    actor=getattr(design,'X_'+kind)
    context=getattr(design,'context_'+kind)
    if rows is not None:
        actor,context=actor[rows],context[rows]
    return np.vstack((np.asarray(actor.T@residual),np.asarray(context.T@residual)))

def actor_support(design):
    """sparse reductions once per head, never one dense elapsed vector per actor."""
    time = design.X_time.tocsc()
    event = design.X_event.tocsc()
    actor_indices = [i for i,c in enumerate(design.columns) if c['kind']=='actor']
    require(np.all(time[:,actor_indices].data >= 0) and np.all(event[:,actor_indices].data >= 0),
            'negative actor applicability')
    seconds = np.asarray(time.T@design.exposure_hours).ravel()*3600
    incidence = event.copy()
    incidence.data = (incidence.data>0).astype(float)
    events = np.asarray(incidence.sum(axis=0)).ravel()
    event_mass = np.add.reduceat(design.origin_weights, design.event_offsets[:-1]) if event.shape[0] else np.zeros(0)
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
    count = len(design.columns)*_width(head)
    beta = np.asarray(flat[:count]).reshape(len(design.columns), _width(head))
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
        key=hasher.digest()
        target=None
        for candidate in groups.get(key,()):
            prior=indices[candidate];a,b=x.indptr[prior:prior+2]
            if np.array_equal(x.indices[left:right],x.indices[a:b]) and np.array_equal(x.data[left:right],x.data[a:b]) and np.array_equal(context[row],context[prior]):
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
        rows,exposure=(None,design.exposure_hours) if work is None else work['volume']
        eta=math.log(offsets['r'])+_linear(design,beta,'time',rows).ravel()
        with np.errstate(over='raise', invalid='raise', under='raise'):
            rates = np.exp(eta)
        require(np.all(rates > 0) and np.isfinite(rates).all(), 'invalid spatial volume rate')
        event_eta = math.log(offsets['r'])+_linear(design,beta,'event').ravel()
        likelihood = float(np.dot(exposure, rates)-event_eta.sum())
        gradient+=_adjoint(design,(exposure*rates)[:,None],'time',rows)
        gradient-=_adjoint(design,np.ones((design.X_event.shape[0],1)),'event')
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
            if head == 'shape':
                logits = np.log(offsets['pi'])+predictor@design.basis.T
                logp = logits-logsumexp(logits, axis=1)[:, None]
                likelihood -= float(np.dot(weight, logp[rows, cells]))
                residual = np.exp(logp)
                np.add.at(residual, (rows, cells), -weight)
                row_gradient = residual@design.basis
            else:
                qbar = np.asarray(offsets['qbar'])
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
    return np.r_[beta.ravel(), age] if head == 'volume' else beta.ravel()


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
                    priors=priors, ledger=list(incoming), centers=None, reference_predictor=None,
                    objective=None, solver=None, diagnostics=None, resources=None)
    if reason:
        metadata['resources'] = dict(wall_seconds=perf_counter()-began, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return metadata, {}
    work = None
    if head == 'volume':
        representatives,exposure = _volume_groups(design)
        work={'volume':(representatives,exposure)}
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
        metadata['status'], metadata['reasons'] = 'failed', [f'numerical_domain_failure:{type(error).__name__}:{error}']
        arrays = {}
    metadata['resources'] = dict(wall_seconds=perf_counter()-began, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                                dimensions=dict(rows=design.X_time.shape[0] if head == 'volume' else design.X_event.shape[0],
                                                features=len(design.columns), coordinates=size,
                                                grouped_time_rows=None if work is None else len(work['volume'][0])))
    return metadata, arrays


def centered_reference(design, head, beta):
    """freeze every applicability mean; coach gates never enter a plain intercept."""
    exposure = float(design.exposure_hours.sum())
    require(exposure > 0, 'reference requires positive elapsed exposure')
    incidence = np.asarray(design.X_time.T@design.exposure_hours).ravel()
    vector = np.zeros(len(design.columns))
    centers = []
    reference = np.zeros(_width(head))
    groups = {}
    for index, column in enumerate(design.columns):
        if column['kind'] == 'intercept':
            vector[index] = 1.
            reference += beta[index]
        elif column['kind'] == 'actor':
            groups.setdefault((column['block'],column['subblock']), []).append(index)
            vector[index] = incidence[index]/exposure
    for (block, subblock), indices in groups.items():
        weight = float(incidence[indices].sum())
        mean = np.sum(beta[indices]*incidence[indices,None], axis=0)/weight if weight else np.zeros(_width(head))
        applicability = weight/exposure
        transferred = mean*applicability
        reference += transferred
        centers.append(dict(block=block,subblock=subblock,indices=indices,weight_hours=weight,
                            mean=mean.tolist(),reference_applicability=applicability,
                            reference_offset=transferred.tolist(),reason=None if weight else 'zero_applicable_time'))
    require(np.allclose(vector@beta,reference,rtol=1e-12,atol=1e-12), 'centered reference transfer differs')
    return centers, reference, vector


def evaluate_rates(design, predictors):
    """evaluate all three heads jointly; never clip positive physical rates."""
    v = np.asarray(predictors['volume'])
    s = np.asarray(predictors['shape'])
    q = np.asarray(predictors['quality'])
    offsets = design.annual_offsets
    eta = math.log(offsets['r'])+v[...,0]
    shape = np.log(offsets['pi'])+s@design.basis.T
    logp = shape-logsumexp(shape,axis=-1)[...,None]
    qbar = np.asarray(offsets['qbar'])
    quality_eta = np.log(qbar)-np.log1p(-qbar)+q[...,:1]+q[...,1:]@design.basis.T
    with np.errstate(over='raise',invalid='raise',under='ignore'):
        attempts = np.exp(eta[...,None]+logp)
        quality = expit(quality_eta)
        chance = np.exp(eta[...,None]+logp+log_expit(quality_eta))
    require(np.isfinite(attempts).all() and np.isfinite(chance).all()
            and np.all(attempts>0) and np.all(chance>0) and np.all(chance<=attempts),
            'invalid positive complete spatial rates')
    return np.stack((attempts,chance),axis=-2)


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
        eta = math.log(design.annual_offsets['r'])+_linear(design,beta,'time').ravel()
        expected = design.exposure_hours*np.exp(eta)
        return dict(population='retained directed 5v5 time and uniquely assigned physical attempts',
                    attempts=design.X_event.shape[0],hours=float(design.exposure_hours.sum()),
                    predicted_attempts=float(expected.sum()),residual=float(design.X_event.shape[0]-expected.sum()),
                    largest_complete_rates=np.sort(np.exp(eta))[-10:].tolist())
    loss = 0.
    expected_location = np.zeros(656)
    actual_location = np.bincount(design.origin_cells,weights=design.origin_weights,minlength=656)
    bins = [dict(lower=i/10,upper=(i+1)/10,origin_weight=0.,target_mass=0.,predicted_mass=0.) for i in range(10)]
    for start in range(0,design.X_event.shape[0],4096):
        stop = min(start+4096,design.X_event.shape[0])
        linear = _linear(design,beta,'event',slice(start,stop))
        left,right = design.event_offsets[start],design.event_offsets[stop]
        rows = np.repeat(np.arange(stop-start),np.diff(design.event_offsets[start:stop+1]))
        cells,weight = design.origin_cells[left:right],design.origin_weights[left:right]
        if head == 'shape':
            eta = np.log(design.annual_offsets['pi'])+linear@design.basis.T
            logp = eta-logsumexp(eta,axis=1)[:,None]
            loss -= float(np.dot(weight,logp[rows,cells]))
            expected_location += np.exp(logp).sum(axis=0)
        else:
            qbar=np.asarray(design.annual_offsets['qbar'])
            eta=np.log(qbar)-np.log1p(-qbar)+linear[:,:1]+linear[:,1:]@design.basis.T
            probability=expit(eta[rows,cells]);target=design.neutral_goal_probability[left:right]
            for i in range(10):
                mask=(probability>=i/10)&((probability<(i+1)/10) if i<9 else (probability<=1))
                bins[i]['origin_weight']+=float(weight[mask].sum())
                bins[i]['target_mass']+=float(np.dot(weight[mask],target[mask]))
                bins[i]['predicted_mass']+=float(np.dot(weight[mask],probability[mask]))
    return (dict(population='retained physical attempts with fractional native origins',
                 cross_entropy=loss/float(design.origin_weights.sum()),
                 native_location_residual=(actual_location-expected_location).tolist()) if head=='shape'
            else dict(population='retained origin-weighted fixed neutral opportunity probabilities',calibration=bins))


def _role_column(block):
    return 'offense' if block == 'attacking_player' else 'defense'


def _projection_support(state, design, player):
    source = dict(design.coverage.get('players',{}).get(player,{}))
    reasons=source.get('reason_counts',{})
    source['reason_counts']=[dict(code=key,count=reasons[key]) for key in sorted(reasons)] if isinstance(reasons,dict) else reasons
    inferred=set(source.get('inferred_inputs',[]))
    if source.get('events',0)>0:inferred.add('setter')
    source['inferred_inputs']=sorted(inferred)
    priors = [row for head in HEADS for row in state.heads[head]['priors']
              if row['block'].endswith('_player') and row['id']==player and row['subblock']=='base']
    if any(row['prior_kind']=='carry' for row in priors):source['inferred_inputs']=sorted(set(source['inferred_inputs'])|{'historical_borrowing'})
    source.update(eligible_weight=None,
                  current_season_information=any(row['current_season_information'] for row in priors),
                  prior_only=bool(priors) and all(row['prior_only'] for row in priors),
                  prior_seasons=sorted({year for row in priors for year in row['prior_seasons']}))
    return source


def _coefficient_support(state, design):
    result=[]
    for player in design.players:
        for role in ROLES:
            block=('attacking' if role=='offense' else 'defending')+'_player'
            for head in HEADS:
                metadata=state.heads[head]
                prior=next((r for r in metadata['priors'] if r['block']==block and r['id']==player and r['subblock']=='base'),None)
                available=metadata['status']=='complete' and prior is not None
                result.append(dict(season=design.season,player_id=player,role=role,head=head,available=available,
                    included_seconds=prior['included_seconds'] if available else None,
                    likelihood_events=prior['likelihood_events'] if available else None,
                    eligible_origin_weight=prior['eligible_origin_weight'] if available else None,
                    current_season_information=prior['current_season_information'] if available else None,
                    prior_only=prior['prior_only'] if available else None,
                    prior_kind=prior['prior_kind'] if available else None,
                    prior_anchor_season=prior['prior_anchor_season'] if available else None,
                    prior_seasons=prior['prior_seasons'] if available else [],
                    reason=None if available else 'missing_actor_coefficient' if prior is None else ':'.join(metadata['reasons'])))
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
        group[3]=factual-references[head]-group[:3].sum(axis=0)
        result[head]=group
    return result


def context_coalitions(design, betas, references, centers, row, player, role, by_actor=None):
    groups=_context_groups(design,betas,references,centers,row,player,role,by_actor)
    predictors={head:np.asarray([references[head]+groups[head][[g for g in range(4) if subset&(1<<g)]].sum(axis=0)
                                 for subset in range(16)]) for head in HEADS}
    return evaluate_rates(design,predictors)


def _actual_adjustments(design, betas, references, centers):
    """batch exact contexts, sharing factual/player predictors before nonlinear work."""
    player_index={player:i for i,player in enumerate(design.players)}
    actor_indices={_actor_key(c):i for i,c in enumerate(design.columns) if c['kind']=='actor'}
    center_by_head={head:{(c['block'],c['subblock']):np.asarray(c['mean']) for c in centers[head]} for head in HEADS}
    maps=np.zeros((len(design.players),2,2,7,656))
    seconds=np.zeros((len(design.players),2))
    representatives,exposure=_volume_groups(design)
    weights=FOUR_GROUP_WEIGHTS
    # 16 elapsed rows contain 160 focal contexts. each subset creates only a
    # batch×40 predictor and batch×656 cell arrays, then accumulates and releases.
    for start in range(0,len(representatives),16):
        selected=representatives[start:start+16]
        hours=exposure[start:start+16]
        pi,ri,context_weight=[],[],[]
        grouped={head:[] for head in HEADS}
        factual={head:_linear(design,betas[head],'time',selected) for head in HEADS}
        for j,row in enumerate(selected):
            key=design.time_keys[row]
            for role_index,role in enumerate(ROLES):
                own='attacking' if role=='offense' else 'defending'
                other='defending' if role=='offense' else 'attacking'
                own_indices=[actor_indices[(own+'_player',str(p),'base')] for p in key[own+'_players']]
                other_indices=[actor_indices[(other+'_player',str(p),'base')] for p in key[other+'_players']]
                for head in HEADS:
                    beta=betas[head]
                    own_mean=center_by_head[head][(own+'_player','base')]
                    other_mean=center_by_head[head][(other+'_player','base')]
                    own_sum=beta[own_indices].sum(axis=0)-5*own_mean
                    other_sum=beta[other_indices].sum(axis=0)-5*other_mean
                    context=factual[head][j]-references[head]-own_sum-other_sum
                    for index in own_indices:
                        self_effect=beta[index]-own_mean
                        grouped[head].append(np.stack((self_effect,own_sum-self_effect,other_sum,context)))
                for player in key[own+'_players']:
                    pi.append(player_index[str(player)]);ri.append(role_index);context_weight.append(hours[j])
        pi=np.asarray(pi);ri=np.asarray(ri);context_weight=np.asarray(context_weight)
        grouped={head:np.asarray(value) for head,value in grouped.items()}
        accumulated=np.zeros((len(pi),2,7,656))
        for subset in range(16):
            selected_groups=[g for g in range(4) if subset&(1<<g)]
            predictors={head:references[head]+grouped[head][:,selected_groups].sum(axis=1) for head in HEADS}
            rate=evaluate_rates(design,predictors)
            if subset==0: accumulated[:,:,0]=rate
            if subset==15: accumulated[:,:,6]=rate
            for group in range(4): accumulated[:,:,group+1]+=weights[group,subset]*rate
        accumulated[:,:,5]=accumulated[:,:,6]-accumulated[:,:,:5].sum(axis=2)
        tolerance=1e-10*(1+np.abs(accumulated[:,:,6])+np.abs(accumulated[:,:,:5]).sum(axis=2))
        require(np.all(np.abs(accumulated[:,:,5])<=tolerance),'batched exact context allocations do not close')
        np.add.at(maps,(pi,ri),context_weight[:,None,None,None]*accumulated)
        np.add.at(seconds,(pi,ri),context_weight*3600)
    rows=[]
    for i,player in enumerate(design.players):
        for r,role in enumerate(ROLES):
            available=bool(seconds[i,r]>0)
            if available:
                maps[i,r]/=seconds[i,r]/3600
                values=maps[i,r].sum(axis=-1)
                terms=maps[i,r,:,:5].sum(axis=1)+maps[i,r,:,5]
                require(np.all(np.abs(terms-maps[i,r,:,6])<=1e-10*(1+np.abs(maps[i,r,:,6])+np.abs(maps[i,r,:,:6]).sum(axis=1))),
                        'time-weighted native adjustment closure differs')
                require(np.all(np.abs(values[:,:6].sum(axis=1)-values[:,6])<=1e-10*(1+np.abs(values[:,6])+np.abs(values[:,:6]).sum(axis=1))),
                        'time-weighted scalar adjustment closure differs')
            rows.append(dict(season=design.season,player_id=player,role=role,available=available,
                reason=None if available else 'no_exposure',exposure_seconds=float(seconds[i,r]),map_index=[i,r],
                **{q:{name:float(maps[i,r,qi,j].sum()) if available else None for j,name in enumerate(ADJUSTMENTS)}
                   for qi,q in enumerate(QUANTITIES)}))
    return rows,maps


def project_spatial(state, design=None, *, actual_context=True):
    began=perf_counter()
    design=state.design if design is None else design
    require(design.season==state.manifest['season'] and design.purpose==state.manifest['purpose'],
            'projection design season/purpose differs')
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
    diagnostics=dict(wall_seconds=perf_counter()-began,players=len(design.players),actual_context=actual_context,
                     peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                     largest_complete_rates=[] if not complete else np.sort(maps[:,:,:,1].sum(axis=-1).ravel())[-20:].tolist(),
                     largest_absolute_contrasts=[] if not complete else np.sort(np.abs(maps[:,:,:,2].sum(axis=-1)).ravel())[-20:].tolist())
    return SpatialProjections(rows,{'rates':maps,'adjustments':adjustment_maps},adjustments,support,reference,diagnostics)


def fit_spatial(design, previous_state, output, *, final_year=False):
    """fit one annual family and preserve it before any numerical continuation."""
    from .spatial_state import SpatialState, write_spatial_state, validate_design
    began=perf_counter()
    if previous_state is not None:
        require(previous_state.manifest['purpose']==design.purpose and all(previous_state.heads[h]['status']=='complete' for h in HEADS),
                'incomplete or mismatched spatial predecessor')
        require(int(design.season[:4])==int(previous_state.manifest['season'][:4])+1,'spatial predecessor is not consecutive')
        require(previous_state.manifest['prepared']['sha256']==design.prepared['sha256']
                and previous_state.manifest['coaches']['sha256']==design.coaches['sha256'], 'spatial predecessor source owners differ')
        require(design.basis is None or np.allclose(design.basis,previous_state.design.basis,atol=1e-12,rtol=0),'spatial basis rotated between years')
        design=replace(design,basis=previous_state.design.basis.copy(),basis_identity=previous_state.design.basis_identity)
    elif design.purpose=='real':
        require(design.season=='20212022','real spatial chain must begin in 20212022')
    validate_design(design)
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
    manifest=dict(schema_version=1,kind='spatial_state',purpose=design.purpose,season=design.season,
                  recipe_id='experimental-v1',recipe=RECIPE,design_identity=design.transforms['design_sha256'],
                  implementation=implementation(),prepared=design.prepared,coaches=design.coaches,valued=design.valued,
                  previous=None if previous_state is None else dict(identity(previous_state.path/'manifest.json'),
                      season=previous_state.manifest['season'],purpose=design.purpose,usage='annual'),
                  basis_identity=design.basis_identity,training_cutoff=design.training_cutoff,heads=[],files=[],
                  resources=dict(design=design.resources,fit_wall_seconds=perf_counter()-began,
                                 peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    state=SpatialState(output,manifest,design,heads,arrays,[],{},[],[],{})
    projections=project_spatial(state)
    baseline=write_spatial_state(state,projections)
    if ((design.purpose=='real' and design.season=='20252026') or final_year) and all(heads[h]['status']=='complete' for h in HEADS):
        from .spatial_state import bind_spatial_probes
        return bind_spatial_probes(baseline,run_numerical_probes(baseline,projections))
    return baseline



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
    priors={row['id']:row for row in state.heads['volume']['priors'] if row['block']=='attacking_player'}
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
                        prior=priors[player]
                        requirements=[]
                        if key.get('boundary_goal'):requirements.append('boundary_goals')
                        if key.get('optional_missing'):requirements.append('missing_optional_inputs')
                        if prior['prior_kind']=='entry':requirements.append('entries')
                        if prior['prior_kind']=='carry' and int(design.season[:4])-int(prior['prior_anchor_season'][:4])>1:requirements.append('returns')
                        if len(teams[player])>1:requirements.append('trades')
                        if prior['included_seconds']<300*60:requirements.append('sparse_support')
                        row=dict(kind=kind,index=index,key=key,role=role,player_id=player,requirements=requirements)
                        order=_probe_sort(key,role,player)
                        for name in requirements:
                            old=witnesses.get(name)
                            if old is None or order<_probe_sort(old['key'],old['role'],old['player_id']):witnesses[name]=row
                        yield row
    fill=heapq.nsmallest(256,candidates(),key=lambda row:_probe_sort(row['key'],row['role'],row['player_id']))
    selected={}
    for name in ('boundary_goals','missing_optional_inputs','entries','returns','trades','sparse_support'):
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
        groups=_context_groups(view,betas,references,centers,row['index'],row['player_id'],row['role'],by_actor)
        predictors={head:np.asarray([references[head]+groups[head][[g for g in range(4) if subset&(1<<g)]].sum(axis=0)
                                      for subset in range(16)]) for head in HEADS}
        rates=evaluate_rates(design,predictors)
        shape=np.log(design.annual_offsets['pi'])+predictors['shape']@design.basis.T
        shape=np.exp(shape-logsumexp(shape,axis=1)[:,None])
        qbar=np.asarray(design.annual_offsets['qbar'])
        quality=expit(np.log(qbar)-np.log1p(-qbar)+predictors['quality'][:,:1]+predictors['quality'][:,1:]@design.basis.T)
        yield row,rates,spatial_shapley(rates),shape,quality



def _standardized_probabilities(state):
    design=state.design
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
        else:
            qbar=np.asarray(design.annual_offsets['qbar'])
            values[head]=expit(np.log(qbar)-np.log1p(-qbar)+predictors[:,:1]+predictors[:,1:]@design.basis.T).reshape(len(design.players),2,656)
    return values

def compare_probe(state,head,metadata,arrays,selected):
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


def run_numerical_probes(state,projections=None):
    """one continuation per head; source keys and baseline freeze before solving."""
    from .artifacts import write_json,write_arrays
    folder=state.path/'probes';folder.mkdir()
    baseline=probe_descriptor(state)
    selected=select_probe_rows(state)
    write_json(folder/'baseline.json',baseline)
    write_json(folder/'rows.json',selected)
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
