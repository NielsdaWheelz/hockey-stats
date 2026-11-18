"""annual on-ice minor intensity and conditional shooter allocation.

raw coordinates carry across years; reporting centers alter only the reference.
qualification time and conditional-choice information have different owners.
"""
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import resource
from time import perf_counter

import numpy as np
from scipy.special import logsumexp

from .artifacts import require
from .captures import InputContractError
from .chance import solve_logistic
from .chance_cli import identity

from .mechanism_design import STATES,ROLES
UNITS = ((3,2),(4,1),(4,1),(3,1),(2,2),(1,2),(1,2))
SOLVER = dict(maxiter=10000,ftol=1e-15,gtol=1e-6,maxcor=10)
CONTINUATION = dict(maxiter=10000,ftol=1e-16,gtol=1e-7,maxcor=10)


def body_digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def mechanism_recipe(family, design_recipe):
    require(family in ('penalties','shootiness'),'unknown mechanism family')
    body = dict(id=f'{family}-v1-10-1',design=design_recipe,solver=SOLVER,continuation=CONTINUATION,
                history='last-likelihood-supported-raw-coordinate; entry-or-carry; age-neutral',
                diagnostic_policy='completed-baselines-experimental-with-disclosed-sensitivity')
    if family == 'penalties':
        body.update(likelihood='sum E_hours*exp(log(r)+X*b)-sum residual_count*(log(r)+X*b)',
            offset='r=(qualified_awards+1)/(directed_hours+1)',
            player_sd=dict(entry=.25,carry_per_sqrt_year=.10),coach_sd=dict(entry=.10,carry_per_sqrt_year=.05),
            context_sd=1.,intercept_sd=2.,centering='role-slot time; applicable coach time; context=0',
            reference='insert one focal skater in drawing or taking role; complete-neutral awards/hour',
            minor='T=2/60; tau=-expm1(-a*T)/a (T at a=0); V=(a-e_f-b+e_a)*tau; taken_value=-taken_difference*V',
            diagnostic_limits=dict(rate_per_hour=1e-4,value_per_1000_minutes=1e-3))
    else:
        body.update(likelihood='sum multiplicity*(logsumexp(log(w)+role_offset+b)-winner_logit)',
            weights=dict(F='(2/3)/n_F',D='(1/3)/n_D',unknown='1/unit_size'),
            roles=list(ROLES),states=list(STATES),role_contrast=[[1,0],[0,1],[-1,-1]],role_offset_sd=1.,
            player_sd=dict(entry=.5,carry_per_sqrt_year=.2),batch_choices=4096,reference_units=[list(u) for u in UNITS],
            centering='pooled candidate incidence per role; transfer mean into reporting offsets without zero-sum reset',
            reference='one focal same-position slot; normalize complete unit; difference=p-p0',
            diagnostic_limits=dict(probability_fraction=1e-5))
    return dict(**body,sha256=body_digest(body))


def scalar_predictor(design, beta, kind):
    """predict on ``time`` or ``event`` rows using the declared coefficient axis.

    X_kind holds the sparse intercept/actor prefix; context_kind holds the
    dense context suffix. beta uses that same concatenated order. exposure
    and its units belong to the caller and do not enter this predictor.
    """
    actor = getattr(design,'X_'+kind)
    return np.asarray(actor@beta[:actor.shape[1]]).ravel()+getattr(design,'context_'+kind)@beta[actor.shape[1]:]


def _adjoint(design, residual, kind):
    return np.concatenate((np.asarray(getattr(design,'X_'+kind).T@residual).ravel(),
                           getattr(design,'context_'+kind).T@residual))


def scalar_intensity_objective(beta, design, mean, precision, log_rate, exposure):
    """poisson intensity with explicit caller-owned exposure units."""
    with np.errstate(over='raise',invalid='raise'):
        time_eta = log_rate+scalar_predictor(design,beta,'time')
        event_eta = log_rate+scalar_predictor(design,beta,'event')
        intensity = np.exp(time_eta)
        residual = exposure*intensity
        delta = beta-mean
        value = float(np.sum(residual)-np.dot(design.event_counts,event_eta)+.5*np.dot(precision*delta,delta))
        gradient = _adjoint(design,residual,'time')-_adjoint(design,design.event_counts,'event')+precision*delta
    require(np.all(intensity>0) and math.isfinite(value) and np.isfinite(gradient).all(),
            'nonfinite or nonpositive scalar intensity/objective/gradient')
    return value,gradient


def penalty_objective(beta, design, mean, precision, log_rate):
    """poisson process likelihood: event multiplicities are counts, never hours."""
    return scalar_intensity_objective(beta,design,mean,precision,log_rate,design.exposure_hours)


def actor_prior(last, season, entry_sd, carry_sd):
    """last-supported raw coordinates supply one entry-or-carry prior."""
    gap=None if last is None else int(season[:4])-int(last['season'][:4])
    require(gap is None or gap>0,'actor history is not strictly earlier')
    mean=0. if last is None else last['coefficient']
    precision=1/entry_sd**2 if gap is None else 1/(carry_sd**2*gap)
    require(math.isfinite(mean) and math.isfinite(precision) and precision>0,'invalid actor prior')
    return mean,precision,gap


def _choice_logits(beta, design, start, end):
    begin,finish = design.choice_offsets[start],design.choice_offsets[end]
    local_offsets = design.choice_offsets[start:end+1]-begin
    sizes = np.diff(local_offsets)
    choices = np.repeat(np.arange(end-start),sizes)
    roles = design.candidate_roles[begin:finish]
    counts = np.bincount(choices*3+roles,minlength=(end-start)*3).reshape(-1,3)
    weight = np.empty(len(roles))
    for role,mass in ((0,2/3),(1,1/3)):
        selected = roles == role
        weight[selected] = mass/counts[choices[selected],role]
    unknown = roles == 2
    weight[unknown] = 1/sizes[choices[unknown]]
    contrasts = beta[len(design.players):].reshape(7,2)
    offsets = np.column_stack((contrasts,-contrasts.sum(axis=1)))
    logits = np.log(weight)+offsets[design.choice_states[start:end][choices],roles]+beta[design.candidate_ids[begin:finish]]
    maximum = np.maximum.reduceat(logits,local_offsets[:-1])
    shifted = np.exp(logits-maximum[choices])
    normalizers = np.add.reduceat(shifted,local_offsets[:-1])
    probabilities = shifted/normalizers[choices]
    require(np.isfinite(logits).all() and np.isfinite(probabilities).all()
            and np.allclose(np.add.reduceat(probabilities,local_offsets[:-1]),1.,rtol=1e-13,atol=1e-13),
            'invalid shooter-choice probabilities')
    return begin,finish,local_offsets,choices,roles,logits,maximum+np.log(normalizers),probabilities


def shooter_probabilities(beta, design):
    values = np.empty(len(design.candidate_ids))
    for start in range(0,len(design.multiplicities),4096):
        result = _choice_logits(beta,design,start,min(start+4096,len(design.multiplicities)))
        values[result[0]:result[1]] = result[-1]
    return values


def shooter_objective(beta, design, mean, precision):
    players = len(design.players)
    delta = beta[:players]-mean
    offsets = beta[players:].reshape(7,2)
    third = -offsets.sum(axis=1)
    value = .5*np.dot(precision*delta,delta)+.5*(np.sum(offsets*offsets)+np.dot(third,third))
    gradient = np.zeros_like(beta)
    gradient[:players] = precision*delta
    gradient[players:] = (offsets-third[:,None]).ravel()
    for start in range(0,len(design.multiplicities),4096):
        end = min(start+4096,len(design.multiplicities))
        begin,finish,local,choices,roles,logits,normalizers,probabilities = _choice_logits(beta,design,start,end)
        winners = design.winner_indices[start:end]-begin
        multiplicity = design.multiplicities[start:end]
        value += np.dot(multiplicity,normalizers-logits[winners])
        residual = probabilities*multiplicity[choices]
        residual[winners] -= multiplicity
        np.add.at(gradient,design.candidate_ids[begin:finish],residual)
        role_gradient = np.bincount(design.choice_states[start:end][choices]*3+roles,
            weights=residual,minlength=21).reshape(7,3)
        gradient[players:] += (role_gradient[:,:2]-role_gradient[:,2,None]).ravel()
    require(math.isfinite(value) and np.isfinite(gradient).all(),'nonfinite shooter objective/gradient')
    return float(value),gradient


def minor_value(a,b,e_f,e_a):
    rates = (a,b,e_f,e_a)
    require(all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in rates),'invalid minor reference rates')
    T = 2/60
    tau = T if a == 0 else -math.expm1(-a*T)/a
    return dict(T_hours=T,tau_hours=tau,V_goals=(a-e_f-b+e_a)*tau)


def _actor_key(row):
    return row['block'],str(row['id']),row['subblock']


def _support(design, family):
    if family == 'shootiness':
        candidate_choices = np.repeat(np.arange(len(design.multiplicities)),np.diff(design.choice_offsets))
        incidence = np.bincount(design.candidate_ids,weights=design.multiplicities[candidate_choices],minlength=len(design.players))
        return {i:dict(information_weight=float(n),likelihood_events=int(n)) for i,n in enumerate(incidence)}
    time = np.asarray(design.X_time.T@design.exposure_hours).ravel()
    events = np.asarray(design.X_event.T@design.event_counts).ravel()
    return {i:dict(information_weight=float(time[i]),likelihood_events=int(events[i]))
            for i,col in enumerate(design.columns) if col['kind']=='actor'}


def annual_priors(design, family, ledger):
    previous = {_actor_key(row):row for row in ledger}
    require(len(previous)==len(ledger),'duplicate last-supported mechanism actor')
    support = _support(design,family)
    if family=='penalties':
        by_player={}
        for index,col in enumerate(design.columns):
            if col['kind']=='actor' and col['block'].endswith('_player'):
                by_player.setdefault(str(col['id']),[]).append(index)
        for indices in by_player.values():
            require(len(indices)==2,'penalty player role axes differ')
            incident=sum(support[i]['likelihood_events'] for i in indices)
            for i in indices:support[i]['likelihood_events']=incident
    columns = ([dict(kind='actor',block='shooter_player',id=p,subblock='base') for p in design.players]
               if family=='shootiness' else design.columns)
    size = len(design.players)+14 if family=='shootiness' else len(columns)
    mean,precision = np.zeros(size),np.ones(size)
    rows = []
    for index,column in enumerate(columns):
        if column['kind']!='actor':
            precision[index] = .25 if column['kind']=='intercept' else 1.
            continue
        last = previous.get(_actor_key(column))
        player = column['block'].endswith('_player')
        entry,carry = ((.5,.2) if family=='shootiness' else (.25,.1) if player else (.1,.05))
        mean[index],precision[index],gap = actor_prior(last,design.season,entry,carry)
        info = support[index]
        rows.append(dict(index=index,block=column['block'],id=str(column['id']),subblock=column['subblock'],
            **info,current_season_information=info['information_weight']>0 or info['likelihood_events']>0,
            prior_only=not(info['information_weight']>0 or info['likelihood_events']>0),
            prior_kind='entry' if last is None else 'carry',prior_anchor_season=None if last is None else last['season'],
            prior_seasons=[] if last is None else last['support_seasons'],mean=float(mean[index]),precision=float(precision[index])))
    require(np.isfinite(mean).all() and np.isfinite(precision).all() and np.all(precision>0),'invalid mechanism prior')
    if family=='penalties':
        attack = {r['id']:r for r in rows if r['block']=='attacking_player'}
        defend = {r['id']:r for r in rows if r['block']=='defending_player'}
        require(set(attack)==set(defend)==set(design.players),'penalty roles do not cover roster')
        for player in design.players:
            for key in ('information_weight','likelihood_events','current_season_information','prior_only','prior_kind','prior_anchor_season','prior_seasons'):
                left,right = attack[player][key],defend[player][key]
                require(math.isclose(left,right,rel_tol=1e-11,abs_tol=1e-11) if key=='information_weight' else left==right,
                        f'penalty role information/history mismatch: {player}:{key}')
    return rows,mean,precision


def _center(design,family,beta,log_rate):
    if family=='shootiness':
        count = len(design.players)
        incidence = _support(design,family)
        player_roles = [ROLES.index(design.player_facts[p]['position_group']) for p in design.players]
        centered = beta[:count].copy()
        contrasts = beta[count:].reshape(7,2)
        offsets = np.column_stack((contrasts,-contrasts.sum(axis=1)))
        centers = []
        for role in range(3):
            indices = [i for i,r in enumerate(player_roles) if r==role]
            weights = np.array([incidence[i]['information_weight'] for i in indices])
            total = float(weights.sum())
            center = float(np.dot(weights,beta[indices])/total) if total>0 else 0.
            centered[indices] -= center
            offsets[:,role] += center
            centers.append(dict(role=ROLES[role],mean=center,candidate_incidence=total))
        reference = dict(kind='conditional-shooter-choice',units='fraction',states=list(STATES),roles=list(ROLES),
            reference_units=[dict(strength=s,forwards=u[0],defenders=u[1]) for s,u in zip(STATES,UNITS,strict=True)],
            role_offsets=offsets.tolist(),context='one same-position focal slot; all other player deviations zero')
        # candidate role is authoritative; reporting transfer must preserve even unknown-role probabilities.
        for begin in range(0,len(design.multiplicities),4096):
            end=min(begin+4096,len(design.multiplicities))
            a,b=design.choice_offsets[begin],design.choice_offsets[end]
            raw_logits=_choice_logits(beta,design,begin,end)[5]
            role_centers=np.array([row['mean'] for row in centers])
            reporting_logits=raw_logits+centered[design.candidate_ids[a:b]]-beta[design.candidate_ids[a:b]]+role_centers[design.candidate_roles[a:b]]
            require(np.allclose(raw_logits,reporting_logits,rtol=1e-12,atol=1e-12),'shooter reporting transform changes logits')
        return centers,reference,centered
    total = float(design.exposure_hours.sum())
    incidence = np.asarray(design.X_time.T@design.exposure_hours).ravel()
    neutral_eta = log_rate+float(beta[0])
    centers=[]
    centered=beta.copy()
    groups={}
    for i,col in enumerate(design.columns):
        if col['kind']=='actor':groups.setdefault((col['block'],col['subblock']),[]).append(i)
    for (block,subblock),indices in groups.items():
        weight=float(incidence[indices].sum())
        center=float(np.dot(incidence[indices],beta[indices])/weight) if weight>0 else 0.
        applicability=weight/total
        neutral_eta+=center*applicability
        centered[indices]-=center
        centers.append(dict(block=block,subblock=subblock,mean=center,weight_hours=weight,
                            reference_applicability=applicability,reference_offset=center*applicability))
    neutral=math.exp(neutral_eta)
    require(math.isfinite(neutral) and neutral>0,'invalid neutral penalty intensity')
    reference=dict(kind='ordinary-minor-team-award-intensity',units='awards_per_hour',neutral_per60=neutral,
        log_rate=log_rate,neutral_predictor=neutral_eta,player_slots_per_role=5,context='centered context zero; elapsed coach applicability')
    return centers,reference,centered


def project_mechanism(design,family,head,beta=None):
    complete=head['status']=='complete'
    centers,reference,centered=(_center(design,family,beta,head['reference']['log_rate'] if family=='penalties' else None) if complete
        else (None,dict(kind='unavailable',family=family,units='awards_per_hour' if family=='penalties' else 'fraction'),None))
    reference=dict(reference,season=design.season)
    reference['sha256']=body_digest(reference)
    priors={r['id']:r for r in head['priors'] if r['block']==('attacking_player' if family=='penalties' else 'shooter_player')}
    projections,supports=[],[]
    for i,player in enumerate(design.players):
        prior=priors[player]
        qualification=design.coverage['qualification'][player]
        info=dict(status=head['status'],current_season_information=prior['current_season_information'],
            prior_only=prior['prior_only'] if complete else False,prior_kind=prior['prior_kind'] if complete else None,
            prior_anchor_season=prior['prior_anchor_season'] if complete else None,
            prior_seasons=prior['prior_seasons'] if complete else [],
            likelihood_events=prior['likelihood_events'],
            information_weight=prior['information_weight'])
        states=[]
        if family=='shootiness':
            raw_states=qualification['states']
            states=([dict(strength=s,**raw_states[s]) for s in STATES] if isinstance(raw_states,dict) else raw_states)
            require([row['strength'] for row in states]==list(STATES),'shootiness state qualification order differs')
        supports.append(dict(player_id=player,coefficient_support=info,
            included_seconds=float(qualification.get('included_seconds',sum(r['included_seconds'] for r in states))),
            known_excluded_seconds=float(qualification.get('known_excluded_seconds',sum(r['known_excluded_seconds'] for r in states))),
            unquantified_gap=bool(qualification.get('unquantified_gap',any(r['unquantified_gap'] for r in states))),states=states))
        if family=='penalties':
            positions={col['block']:j for j,col in enumerate(design.columns) if col['kind']=='actor' and str(col['id'])==player and col['subblock']=='base'}
            neutral=reference['neutral_per60'] if complete else None
            drawn=neutral*math.exp(float(centered[positions['attacking_player']])) if complete else None
            taken=neutral*math.exp(float(centered[positions['defending_player']])) if complete else None
            projections.append(dict(player_id=player,season=design.season,drawn_per60=None if drawn is None else drawn-neutral,
                taken_per60=None if taken is None else taken-neutral,drawn_complete_per60=drawn,taken_complete_per60=taken,
                neutral_per60=neutral,reference_id=reference['sha256']))
        else:
            position=design.player_facts[player]['position_group']
            for state,(forwards,defenders) in zip(STATES,UNITS,strict=True):
                p=p0=None
                if complete and position!='unknown':
                    role=ROLES.index(position)
                    unit_roles=np.array([0]*forwards+[1]*defenders)
                    logits=np.array([math.log((2/3)/forwards)]*forwards+[math.log((1/3)/defenders)]*defenders)
                    logits+=np.asarray(reference['role_offsets'])[STATES.index(state),unit_roles]
                    slot=0 if role==0 else forwards
                    p0=float(math.exp(logits[slot]-logsumexp(logits)))
                    logits[slot]+=centered[i]
                    p=float(math.exp(logits[slot]-logsumexp(logits)))
                projections.append(dict(player_id=player,season=design.season,strength=state,position_group=position,
                    probability=p,neutral_probability=p0,difference=None if p is None else p-p0,
                    reference_unit=dict(forwards=forwards,defenders=defenders),reference_id=reference['sha256']))
    return projections,supports,reference,centers


def _compress_penalty(design):
    replacements={}
    for kind,weight in (('time','exposure_hours'),('event','event_counts')):
        actor=getattr(design,'X_'+kind)
        context=getattr(design,'context_'+kind)
        weights=getattr(design,weight)
        groups={};indices=[];totals=[];locators=[]
        for row in range(actor.shape[0]):
            start,end=actor.indptr[row:row+2]
            key=(actor.indices[start:end].tobytes(),actor.data[start:end].tobytes(),context[row].tobytes())
            index=groups.get(key)
            if index is None:
                groups[key]=len(indices);indices.append(row);totals.append(float(weights[row]));locators.append([getattr(design,kind+'_keys')[row]])
            else:
                totals[index]+=float(weights[row]);locators[index].append(getattr(design,kind+'_keys')[row])
        replacements['X_'+kind]=actor[indices]
        replacements['context_'+kind]=context[indices]
        replacements[weight]=np.asarray(totals,dtype=np.float64)
        replacements[kind+'_keys']=tuple(dict(source_rows=group) for group in locators)
    return replace(design,**replacements)


def _compress_shootiness(design):
    groups={};selected=[];multiplicities=[];locators=[]
    for row,state in enumerate(design.choice_states):
        start,end=design.choice_offsets[row:row+2]
        key=(int(state),design.candidate_ids[start:end].tobytes(),design.candidate_roles[start:end].tobytes(),int(design.winner_indices[row]-start))
        index=groups.get(key)
        if index is None:
            groups[key]=len(selected);selected.append(row);multiplicities.append(int(design.multiplicities[row]));locators.append([design.choice_keys[row]])
        else:
            multiplicities[index]+=int(design.multiplicities[row]);locators[index].append(design.choice_keys[row])
    offsets=[0];players=[];roles=[];winners=[]
    for row in selected:
        start,end=design.choice_offsets[row:row+2]
        winners.append(offsets[-1]+int(design.winner_indices[row]-start))
        players.extend(design.candidate_ids[start:end]);roles.extend(design.candidate_roles[start:end]);offsets.append(len(players))
    return replace(design,choice_offsets=np.asarray(offsets,dtype=np.int64),candidate_ids=np.asarray(players,dtype=np.int64),
        candidate_roles=np.asarray(roles,dtype=np.int64),choice_states=design.choice_states[selected],
        winner_indices=np.asarray(winners,dtype=np.int64),multiplicities=np.asarray(multiplicities,dtype=np.int64),
        choice_keys=tuple(dict(source_rows=group) for group in locators))


def _fit_head(design,family,incoming,*,initial=None,tightened=False):
    priors,mean,precision=annual_priors(design,family,incoming)
    log_rate=math.log((float(design.event_counts.sum())+1)/(float(design.exposure_hours.sum())+1)) if family=='penalties' else None
    head=dict(status='incomplete',reasons=[],priors=priors,ledger=list(incoming),centers=None,
        reference=None if log_rate is None else dict(log_rate=log_rate),objective=None,solver=None,diagnostics=None)
    no_information=not np.any(design.exposure_hours>0) if family=='penalties' else not len(design.multiplicities)
    if no_information:
        head.update(status='unavailable',reasons=['no_exposure' if family=='penalties' else 'no_choices'])
        return head,{},None
    objective=(lambda b:penalty_objective(b,design,mean,precision,log_rate)) if family=='penalties' else (
        lambda b:shooter_objective(b,design,mean[:len(design.players)],precision[:len(design.players)]))
    options=CONTINUATION if tightened else SOLVER
    began=perf_counter()
    try:
        coefficients,solver=solve_logistic(objective,mean if initial is None else initial,
            maxiter=options['maxiter'],ftol=options['ftol'],gtol=options['gtol'],maxcor=options['maxcor'])
        for prior in priors:
            if prior['prior_only']:coefficients[prior['index']]=prior['mean']
        value,gradient=objective(coefficients)
        solver.update(options=options,gradient_inf_norm=float(np.max(np.abs(gradient))),
            achieved_gtol=bool(np.max(np.abs(gradient))<=options['gtol']),wall_seconds=perf_counter()-began,
            peak_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        head.update(solver=solver,objective=dict(penalized_loss=value,gradient_inf_norm=solver['gradient_inf_norm']))
        if not solver['converged']:
            head.update(status='failed',reasons=['optimizer_failed'])
            return head,{},None
        head['status']='complete'
        ledger={_actor_key(row):dict(row) for row in incoming}
        for row in priors:
            if row['current_season_information']:
                ledger[_actor_key(row)]=dict(block=row['block'],id=row['id'],subblock=row['subblock'],
                    coefficient=float(coefficients[row['index']]),season=design.season,support_seasons=row['prior_seasons']+[design.season])
        head['ledger']=[ledger[k] for k in sorted(ledger)]
        projections,support,reference,centers=project_mechanism(design,family,head,coefficients)
        head['centers'],head['reference']=centers,reference
        if family=='penalties':
            expected=float(np.dot(design.exposure_hours,np.exp(log_rate+scalar_predictor(design,coefficients,'time'))))
            head['diagnostics']=dict(kind='in_sample_not_held_out',expected_awards=expected,observed_awards=float(design.event_counts.sum()))
        else:
            probability=shooter_probabilities(coefficients,design)
            choice_indices=np.repeat(np.arange(len(design.multiplicities)),np.diff(design.choice_offsets))
            expected=np.bincount(design.choice_states[choice_indices]*3+design.candidate_roles,
                weights=probability*design.multiplicities[choice_indices],minlength=21).reshape(7,3)
            actual=np.bincount(design.choice_states*3+design.candidate_roles[design.winner_indices],
                weights=design.multiplicities,minlength=21).reshape(7,3)
            head['diagnostics']=dict(kind='in_sample_not_held_out',choices=int(design.multiplicities.sum()),
                states=[dict(strength=s,expected_by_role=e.tolist(),observed_by_role=a.tolist()) for s,e,a in zip(STATES,expected,actual,strict=True)])
        return head,dict(coefficients=coefficients),(projections,support,reference)
    except (InputContractError,FloatingPointError,OverflowError,ValueError) as error:
        head.update(status='failed',reasons=[f'numerical_domain_failure:{type(error).__name__}:{error}'],ledger=list(incoming),
            centers=None,reference=None,diagnostics=None)
        return head,{},None


def compare_mechanism_probe(design,family,baseline,probe,baseline_rows,probe_rows):
    def unassessed(reason):
        return dict(status='unassessed',reason=reason,projection_maximum=None,fitting_row_maximum=None,
                    worst_projection=None,worst_fitting_row=None,penalty_value_status='unassessed' if family=='penalties' else None)
    if baseline['status']!='complete' or probe['status']!='complete':return unassessed('baseline_or_probe_incomplete')
    for variant in (baseline,probe):
        coefficients=variant.get('arrays',{}).get('coefficients')
        if coefficients is None or not np.isfinite(coefficients).all():return unassessed('absent_or_nonfinite_coefficients')

    fields=('drawn_per60','taken_per60','drawn_complete_per60','taken_complete_per60','neutral_per60') if family=='penalties' else (
        'probability','neutral_probability','difference')
    maximum=0.;worst=None
    for left,right in zip(baseline_rows,probe_rows,strict=True):
        require((left['player_id'],left.get('strength'))==(right['player_id'],right.get('strength')),'probe projection keys differ')
        for key in fields:
            if left[key] is not None:
                if any(type(v) not in (int,float) or not math.isfinite(v) for v in (left[key],right[key])):
                    return unassessed('nonfinite_projection')
                movement=abs(left[key]-right[key])
                if movement>maximum:maximum,worst=movement,dict(player_id=left['player_id'],strength=left.get('strength'),field=key)
    if family=='penalties':
        before=np.exp(baseline['head']['reference']['log_rate']+scalar_predictor(design,baseline['arrays']['coefficients'],'time'))
        after=np.exp(probe['head']['reference']['log_rate']+scalar_predictor(design,probe['arrays']['coefficients'],'time'))
        event_before=np.exp(baseline['head']['reference']['log_rate']+scalar_predictor(design,baseline['arrays']['coefficients'],'event'))
        event_after=np.exp(probe['head']['reference']['log_rate']+scalar_predictor(design,probe['arrays']['coefficients'],'event'))
        movements=np.concatenate((abs(before-after),abs(event_before-event_after)))
    else:
        movements=abs(shooter_probabilities(baseline['arrays']['coefficients'],design)-shooter_probabilities(probe['arrays']['coefficients'],design))
    if not np.isfinite(movements).all():return unassessed('nonfinite_fitting_rows')
    index=int(np.argmax(movements)) if len(movements) else None
    actual=float(movements[index]) if index is not None else 0.
    worst_row=None
    if index is not None and family=='penalties':
        time_rows=design.X_time.shape[0]
        kind='time' if index<time_rows else 'event'
        row=index if kind=='time' else index-time_rows
        worst_row=dict(axis=kind+'_rows',row=row,source_rows=getattr(design,kind+'_keys')[row])
    elif index is not None:
        choice=int(np.searchsorted(design.choice_offsets,index,side='right')-1)
        worst_row=dict(axis='candidates',candidate_index=index,choice_index=choice,
            choice_candidate_slot=index-int(design.choice_offsets[choice]),player_id=design.players[design.candidate_ids[index]],
            source_rows=design.choice_keys[choice])
    budget=1e-4 if family=='penalties' else 1e-5
    return dict(status='exceeded' if max(maximum,actual)>budget else 'within_budget',reason=None,
        projection_maximum=maximum,fitting_row_maximum=actual,worst_projection=worst,worst_fitting_row=worst_row,
        budget=budget,penalty_value_status='unassessed' if family=='penalties' else None)


def fit_mechanism(design,previous,output,*,final_year=False):
    from .mechanism_design import PenaltyDesign
    from .mechanism_state import MechanismState,read_mechanism_state,write_mechanism_state,validate_design
    family='penalties' if isinstance(design,PenaltyDesign) else 'shootiness'
    began=perf_counter()
    validate_design(design)
    previous_state=None
    if previous is not None:
        previous_state=previous if isinstance(previous,MechanismState) else read_mechanism_state(previous,design.purpose,family,narrow=True)
        require(previous_state.manifest['purpose']==design.purpose and previous_state.manifest['family']==family
            and previous_state.manifest['recipe']==mechanism_recipe(family,design.recipe),'mechanism predecessor purpose/family/recipe differs')
        for source in ('prepared','coaches') if family=='penalties' else ('prepared',):
            require(all(previous_state.manifest[source][key]==getattr(design,source)[key] for key in ('path','sha256')),
                    f'mechanism predecessor {source} binding differs')
        require(previous_state.manifest['season']==f'{int(design.season[:4])-1}{design.season[:4]}'
                and previous_state.head['status']=='complete','mechanism predecessor is not the exact completed prior year')
    require(design.purpose!='real' or (design.season=='20212022')==(previous_state is None),'real mechanism chronology differs')
    design=_compress_penalty(design) if family=='penalties' else _compress_shootiness(design)
    incoming=[] if previous_state is None else previous_state.head['ledger']
    head,arrays,projected=_fit_head(design,family,incoming)
    if projected is None:
        projected=project_mechanism(design,family,head)[:3]
    projections,support,reference=projected
    head['reference']=reference
    probe=None
    if final_year:
        if head['status']=='complete':
            probe_head,probe_arrays,probe_projected=_fit_head(design,family,incoming,initial=arrays['coefficients'],tightened=True)
            probe_rows=[] if probe_projected is None else probe_projected[0]
            baseline=dict(status=head['status'],head=head,arrays=arrays)
            variant=dict(status=probe_head['status'],head=probe_head,arrays=probe_arrays)
            comparison=compare_mechanism_probe(design,family,baseline,variant,projections,probe_rows)
            probe=dict(head=probe_head,arrays=probe_arrays,projections=probe_rows,reference=None if probe_projected is None else probe_projected[2],comparison=comparison)
        else:
            probe=dict(head=None,arrays={},projections=[],reference=None,comparison=dict(status='unassessed',reason='baseline_incomplete',projection_maximum=None,fitting_row_maximum=None,
                worst_projection=None,worst_fitting_row=None,penalty_value_status='unassessed' if family=='penalties' else None))
    resources=dict(wall_seconds=perf_counter()-began,peak_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        coordinates=len(design.columns) if family=='penalties' else len(design.players)+14,
        baseline_solves=int(head['status']!='unavailable'),diagnostic_solves=int(probe is not None and probe['head'] is not None),
        preparation=design.resources,wall_scope='fit/projection/diagnostic before artifact writing; preparation separately reported')
    return write_mechanism_state(Path(output),design,family,previous_state,head,arrays,projections,support,reference,probe,resources)


def reduce_minor_reference(prepared,execution_score,ev_saved,st_saved,*,output):
    """reduce matched shorthanded neutral mass; no rescoring or advantage-mask reuse."""
    from .analysis_data import PreparedManifest,read_prepared,read_prepared_game
    from .artifacts import write_json
    from .chance_cli import read_json
    from .execution_history import _value
    from .execution_scores import ExecutionScores,read_execution_scores
    from .mechanism_design import mechanism_membership,choice_population,_affected
    from .reconstruct import report_membership,roster_identities
    from .spatial_rates import ST_RECIPE
    from .spatial_state import SavedSpatialEvidence,read_saved_spatial_evidence
    if not isinstance(prepared,PreparedManifest):
        p=Path(prepared);purpose=read_json(p/'manifest.json' if p.is_dir() else p)['purpose'];prepared=read_prepared(p,purpose)
    purpose=prepared['purpose']
    scores=execution_score if isinstance(execution_score,ExecutionScores) else read_execution_scores(execution_score,purpose)
    season=scores.manifest['season']
    ev=ev_saved if isinstance(ev_saved,SavedSpatialEvidence) else read_saved_spatial_evidence(ev_saved,purpose)
    st=st_saved if isinstance(st_saved,SavedSpatialEvidence) else read_saved_spatial_evidence(st_saved,purpose,expected_family='st',expected_recipe=ST_RECIPE)
    selected=next((r for r in prepared['seasons'] if r['season']==season),None)
    require(selected is not None,'minor reference prepared season absent')
    expected_prepared=dict(purpose=purpose,**identity(prepared.directory/'manifest.json'),
                          members=[r for r in prepared['files'] if r['season']==season])
    require(scores.manifest['prepared']==expected_prepared,'minor reference score preparation differs')
    score_binding=identity(scores.path)
    for saved in (ev,st):
        require(saved.manifest['season']==season and saved.manifest['purpose']==purpose
            and saved.manifest['prepared']==expected_prepared,'minor reference saved annual lineage differs')
        require({k:saved.manifest['valued'][k] for k in ('path','sha256')}==score_binding,'minor reference saved score lineage differs')
    def neutral(saved,role,strength=None):
        values=[r['values'][role]['xg']['neutral'] for r in saved.projections if strength is None or r.get('strength')==strength]
        require(values,'minor reference saved neutral projection absent')
        if any(v is None for v in values):
            require(all(v is None for v in values),'minor reference repeated neutral availability differs')
            return None
        require(all(math.isfinite(v) and v>=0 and math.isclose(v,values[0],rel_tol=1e-10,abs_tol=1e-10) for v in values),
                'minor reference repeated neutral rates differ')
        return float(values[0])
    a=neutral(st,'offense','5v4');e_f=neutral(ev,'offense');e_a=neutral(ev,'defense')
    scored={r['key']:r for r in scores.events()}
    game_receipts=[];included_seconds=0.;excluded_seconds=0.;mass=0.;attempt_count=0;gap=False
    for game_id in selected['selected_game_ids']:
        game=read_prepared_game(prepared,season,game_id)
        membership=mechanism_membership(game)
        segments={r['segment_index']:r for r in game['segments'] or []}
        short_segments={index:segment for index,segment in segments.items()
            if len(segment['membership']['home_goalies'])==len(segment['membership']['away_goalies'])==1
            and sorted((len(segment['membership']['home_skaters']),len(segment['membership']['away_skaters'])))==[4,5]}
        excluded=set(membership['excluded_segments'])&set(short_segments)
        # these source gaps cannot establish zero short-handed responses; shot-value defects do not enter.
        for reason_record in game['ordinary_attempt_support']['reasons']:
            if reason_record['code'] in ('source_unavailable','count_accounting_conflict'):
                excluded.update(set(reason_record['affected_segment_indices'])&set(short_segments))
        assignments={r['source_index']:r for r in game['ordinary_attempt_support']['events'] or []}
        attempts={r['source_index']:r for r in game['attempts'] or []}
        events={r['source']['source_index']:r for r in game['events'] or []}
        retained=[];dispositions=[]
        reports={row['source_index']:row for row in game['game']['report_rows'] or []}
        roster=roster_identities([row for person in (game['people'] or {}).values() for row in person['roster']])
        game_identity=game['game']['identity'] or game['game']['inventory']
        for report_only in game['ordinary_attempt_support']['report_only'] or []:
            report=reports[report_only['report_source_index']]
            if report['period_number']==5 or report['penalty_shot'] is True:continue
            reported_members,invalid=report_membership(report,game_identity,roster,[])
            shooting_side=next((side for side in ('home','away') if report['shooting_team_id']==game_identity[side+'_team_id']),None)
            proven_other=False
            if not invalid and shooting_side is not None and all(len(reported_members[s+'_goalies'])==1 for s in ('home','away')):
                other='away' if shooting_side=='home' else 'home'
                proven_other=(len(reported_members[shooting_side+'_skaters']),len(reported_members[other+'_skaters']))!=(4,5)
            implicated=set(report_only['affected_segment_indices'])&set(short_segments)
            if not proven_other:excluded.update(implicated)
            dispositions.append(dict(report_source_index=report['source_index'],status='proved_nonsh_report' if proven_other else 'unmatched_possible_sh_report',
                segments=[] if proven_other else sorted(implicated)))
        for assigned in game['ordinary_attempt_support']['events'] or []:
            index=assigned['source_index']
            if index in attempts or assigned['disposition']=='not_applicable':continue
            event=events.get(index)
            implicated=set(_affected(list(segments.values()),None if event is None else event['source']['period_number'],
                None if event is None else event['source']['elapsed_seconds']))&set(short_segments)
            excluded.update(implicated)
            dispositions.append(dict(source_index=index,status='unresolved_possible_attempt',segments=sorted(implicated)))
        for choice in choice_population(game):
            index=choice['source_index'];attempt=attempts[index];details=attempt['details'];key=f'{game_id}:{index}'
            if _value(details,'physical_status')=='outside_population':continue
            if choice['strength'] is not None and choice['strength']!='4v5':
                dispositions.append(dict(source_index=index,status='outside_shorthanded_population',segments=[]));continue
            assignment=assignments.get(index);segment_index=None if assignment is None else assignment['segment_index']
            if segment_index is not None:
                require(segment_index in segments,'minor reference attempt segment absent')
                implicated={segment_index}&set(short_segments)
            else:
                event=events.get(index)
                period=None if event is None else event['source']['period_number']
                clock=None if event is None else event['source']['elapsed_seconds']
                implicated=set(_affected(list(segments.values()),period,clock))&set(short_segments)
            if not implicated and choice['strength'] is None:continue
            if (choice['status']!='included' and choice['reason']!='goalie_attempt') or choice['strength']!='4v5' or segment_index not in short_segments:
                excluded.update(implicated);dispositions.append(dict(source_index=index,status='ambiguous_potential_shorthanded',segments=sorted(implicated)));continue
            segment=segments[segment_index];side=choice['attacking_side'];other='away' if side=='home' else 'home'
            require(len(segment['membership'][side+'_skaters'])==4 and len(segment['membership'][other+'_skaters'])==5,
                    f'{key}: shorthanded source/segment strength contradict')
            state=attempt['feature_facts']['state']
            consistent=all(sorted(_value(state,k) or [])==sorted(segment['membership'][k])
                           for k in ('home_skaters','away_skaters','home_goalies','away_goalies'))
            if not consistent:
                excluded.update(implicated);dispositions.append(dict(source_index=index,status='membership_assignment_unresolved',segments=sorted(implicated)));continue
            score=scored.get(key);outcome=_value(details,'outcome')
            if score is not None:
                require(score['key']==key and score['game_id']==game_id and score['source_index']==index,
                        f'{key}: execution score key lineage differs')
                require(score['physical_state'] is None or tuple(score['physical_state'])==(4,5,1,1),f'{key}: execution score state lineage differs')
                require(score['shooter_id'] is None or score['shooter_id']==choice['shooter_id'],f'{key}: execution score shooter lineage differs')
                require(score['outcome'] is None or score['outcome']==outcome,f'{key}: execution score outcome lineage differs')
            if score is None or score['status']!='complete':
                excluded.update(implicated);dispositions.append(dict(source_index=index,status='neutral_score_unavailable',segments=sorted(implicated)));continue
            value=score['prefixes']['neutral']['uqrg']
            require(type(value) in (int,float) and math.isfinite(value) and 0<=value<=1,f'{key}: invalid saved neutral mass')
            retained.append((segment_index,key,float(value)))
            dispositions.append(dict(source_index=index,status='matched_neutral',segments=[segment_index]))
        # missing collections cannot prove zero events for a known shorthanded interval.
        if game['attempts'] is None or game['events'] is None:
            excluded.update(short_segments)
        seconds=sum(s['end_seconds']-s['start_seconds'] for i,s in short_segments.items() if i not in excluded)
        removed=sum(s['end_seconds']-s['start_seconds'] for i,s in short_segments.items() if i in excluded)
        kept=[(key,v) for segment,key,v in retained if segment not in excluded]
        subtotal=math.fsum(v for key,v in kept)
        included_seconds+=seconds;excluded_seconds+=removed;mass+=subtotal;attempt_count+=len(kept);gap|=membership['unquantified_gap']
        game_receipts.append(dict(game_id=game_id,included_seconds=seconds,known_excluded_seconds=removed,
            excluded_segments=sorted(excluded),attempts=len(kept),neutral_goal_mass=subtotal,
            retained_keys=[key for key,v in kept],dispositions=dispositions,unquantified_gap=membership['unquantified_gap']))
    b=mass/(included_seconds/3600) if included_seconds>0 else None
    bindings=dict(prepared=identity(prepared.directory/'manifest.json'),execution_score=score_binding,
                  ev_state=identity(ev.path/'manifest.json'),st_state=identity(st.path/'manifest.json'))
    sh_support=dict(included_seconds=float(included_seconds),attempts=attempt_count,neutral_goal_mass=float(mass),
                    known_excluded_seconds=float(excluded_seconds),unquantified_gap=bool(gap))
    receipt=dict(schema_version=1,kind='shorthanded_neutral_reduction',purpose=purpose,season=season,inputs=bindings,
        sh_support=sh_support,games=game_receipts,construction='proved shooting-side 4v5; independent native membership; whole maximal-segment exclusion for ambiguous potential response or missing neutral score; zero-event time retained')
    root=Path(output).resolve();root.mkdir(parents=True,exist_ok=False)
    write_json(root/'source-reduction.json',receipt)
    reduction=identity(root/'source-reduction.json')
    available=all(v is not None for v in (a,b,e_f,e_a))
    reason=None if available else 'no_exposure' if b is None else 'failed_fit' if any(saved.manifest['heads'][i]['status']!='complete' for saved in (ev,st) for i in range(3)) else 'missing_source'
    tau=None if a is None else (2/60 if a==0 else -math.expm1(-a*2/60)/a)
    valuation=dict(available=available,reason=reason,a=a,b=b,e_f=e_f,e_a=e_a,T_hours=2/60,tau_hours=tau,
        V_goals=None if not available else minor_value(a,b,e_f,e_a)['V_goals'],sh_support=sh_support,
        inputs={key:dict(uri=ref['path'],sha256=ref['sha256']) for key,ref in dict(ev_state=bindings['ev_state'],st_state=bindings['st_state'],execution_score=score_binding,reduction=reduction).items()})
    reference=dict(schema_version=1,kind='isolated_minor_reference',purpose=purpose,season=season,valuation=valuation,
        construction='isolated two-minute ordinary minor; pp goal ends opportunity, sh goal does not; source-pooled sh circumstances mixed with hypothetical neutral ev/pp; no overlaps, 5v3, regulation truncation or focal specialty skill')
    reference['reference_id']=body_digest(reference)
    write_json(root/'minor-reference.json',reference)
    from .mechanism_state import read_minor_reference
    return read_minor_reference(root/'minor-reference.json',purpose,season,expected_inputs=bindings)


def propagate_penalty_probe(state,minor_reference):
    """complete the saved diagnostic in goals once the external value reference exists."""
    probe=state.probe
    if probe is None:
        return dict(status='not_assessed',reason='earlier_annual',rate=None,value=None)
    rate=probe['comparison']
    valuation=minor_reference['valuation']
    if rate['status']=='unassessed' or not valuation['available']:
        return dict(status='exceeded' if rate['status']=='exceeded' else 'unassessed',reason='probe_or_minor_value_unavailable',rate=rate,value=None)
    value=valuation['V_goals'];maximum=0.;worst=None
    for baseline,variant in zip(state.projections,probe['projections'],strict=True):
        require(baseline['player_id']==variant['player_id'],'penalty probe player axes differ')
        for role in ('drawn','taken'):
            change=abs(baseline[role+'_per60']-variant[role+'_per60'])*abs(value)
            if change>maximum:maximum,worst=change,dict(player_id=baseline['player_id'],role=role)
    prospective=maximum*1000/60
    finding='exceeded' if rate['status']=='exceeded' or maximum>1e-4 or prospective>1e-3 else 'within_budget'
    return dict(status=finding,reason=None,rate=rate,value=dict(maximum_goals_per_hour=maximum,
        maximum_goals_per_1000_minutes=prospective,worst=worst,goals_per_hour_budget=1e-4,goals_per_1000_minutes_budget=1e-3,
        minor_reference_id=minor_reference['reference_id']))
