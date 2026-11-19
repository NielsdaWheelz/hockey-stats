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

from .input_locations import input_path, same_input_reference
from .artifacts import require
from .captures import InputContractError
from .chance import solve_logistic
from .chance_cli import identity

from .mechanism_design import STATES,ROLES
UNITS = ((3,2),(4,1),(4,1),(3,1),(2,2),(1,2),(1,2))
SHOOTER_ROLE_MASS = (2/3, 1/3)
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
    for role,mass in enumerate(SHOOTER_ROLE_MASS):
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


def unit_shooter_base_logits(forwards, defenders):
    return tuple(math.log(mass/count) for mass,count in zip(SHOOTER_ROLE_MASS,(forwards,defenders),strict=True))


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
                    logits=np.asarray(unit_shooter_base_logits(forwards,defenders))[unit_roles]
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


def _shorthanded_inputs(prepared, scores):
    from .analysis_data import PreparedManifest
    from .execution_scores import ExecutionScoreEvents, ExecutionScores

    require(isinstance(prepared, PreparedManifest) and isinstance(scores, (ExecutionScoreEvents, ExecutionScores)),
            "checked preparation and execution score events required for shorthanded reduction")
    season = scores.manifest["season"]
    selected = next((row for row in prepared["seasons"] if row["season"] == season), None)
    require(selected is not None and scores.manifest["purpose"] == prepared["purpose"],
            "score/prepared shorthanded season or purpose differs")
    expected = dict(purpose=prepared["purpose"], **identity(prepared.directory / "manifest.json"),
                    members=[row for row in prepared["files"] if row["season"] == season])
    require(same_input_reference(scores.manifest["prepared"], expected)
            and scores.manifest["coaches"]["selected_game_ids"] == selected["selected_game_ids"],
            "score preparation or game membership differs")
    return season, selected, expected


_LEDGER_SHORTHANDED_CONSTRUCTION = "matched-exact-shorthanded-segments-v1"


def reduce_shorthanded_reference(prepared, scores, strengths=("3v5", "3v4")):
    """Reduce the missing shorthanded opportunities from two bound saved inputs."""
    strengths = tuple(strengths)
    require(strengths == ("3v5", "3v4"), "ledger shorthanded strengths differ")
    season, selected, prepared_ref = _shorthanded_inputs(prepared, scores)
    return dict(schema_version=1, kind="ledger_shorthanded_reduction", construction=_LEDGER_SHORTHANDED_CONSTRUCTION,
                purpose=prepared["purpose"],
                season=season, inputs=dict(prepared={k: prepared_ref[k] for k in ("path", "sha256")},
                                           execution_score=identity(scores.path)),
                strengths=_shorthanded_games(prepared, scores, selected, strengths))


def validate_shorthanded_reference(receipt, prepared, scores):
    """Validate a saved selected-state reduction using only its bound evidence."""
    from .artifacts import require_count, require_fields, require_number

    purpose = prepared["purpose"]
    season, selected, prepared_ref = _shorthanded_inputs(prepared, scores)
    require_fields(receipt, ("schema_version", "kind", "construction", "purpose", "season", "inputs", "strengths"),
                   "ledger shorthanded reduction")
    require(type(receipt["schema_version"]) is int and receipt["schema_version"] == 1
            and receipt["kind"] == "ledger_shorthanded_reduction"
            and (receipt["purpose"], receipt["season"]) == (purpose, season),
            "ledger shorthanded schema, purpose or season differs")
    require(receipt["construction"] == _LEDGER_SHORTHANDED_CONSTRUCTION,
            "ledger shorthanded construction differs")
    bindings = dict(prepared={k: prepared_ref[k] for k in ("path", "sha256")}, execution_score=identity(scores.path))
    require_fields(receipt["inputs"], bindings, "shorthanded bindings")
    require(all(same_input_reference(receipt["inputs"][key], binding) for key, binding in bindings.items()),
            "shorthanded prepared or execution score binding differs")
    require_fields(receipt["strengths"], ("3v5", "3v4"), "ledger shorthanded states")

    retained_by_strength = set()
    for strength, result in receipt["strengths"].items():
        require_fields(result, ("sh_support", "games"), strength)
        games = result["games"]
        require(type(games) is list and all(type(game) is dict for game in games)
                and [game.get("game_id") for game in games] == selected["selected_game_ids"],
                f"{strength}: selected shorthanded games differ")
        for game in games:
            game_id = game["game_id"]
            label = f"{game_id}/{strength}"
            require_fields(game, ("game_id", "included_seconds", "known_excluded_seconds", "excluded_segments",
                                  "attempts", "neutral_goal_mass", "retained_keys", "dispositions",
                                  "unquantified_gap", "segment_seconds", "retained_masses"), label)
            require(type(game["segment_seconds"]) is list, f"{label}: invalid segment durations")
            segment_seconds = {}
            for row in game["segment_seconds"]:
                require_fields(row, ("segment_index", "seconds"), label)
                index = row["segment_index"]
                require_count(index, label)
                require(index not in segment_seconds, f"{label}: duplicate physical segment")
                seconds = require_number(row["seconds"], label, low=0)
                require(seconds > 0, f"{label}: empty segment")
                segment_seconds[index] = seconds
            excluded = game["excluded_segments"]
            require(type(excluded) is list and all(type(index) is int and index in segment_seconds for index in excluded)
                    and excluded == sorted(set(excluded)), f"{label}: invalid excluded segment union")
            excluded = set(excluded)
            require(type(game["unquantified_gap"]) is bool and list(segment_seconds) == sorted(segment_seconds),
                    f"{label}: unordered physical segment or invalid gap")
            require(require_number(game["included_seconds"], label, low=0) ==
                    math.fsum(seconds for index, seconds in segment_seconds.items() if index not in excluded)
                    and require_number(game["known_excluded_seconds"], label, low=0) ==
                    math.fsum(segment_seconds[index] for index in excluded), f"{label}: time union differs")

            require(type(game["dispositions"]) is list, f"{label}: expected dispositions")
            expected, seen = [], set()
            for row in game["dispositions"]:
                require(type(row) is dict, f"{label}: invalid disposition")
                status = row.get("status")
                locator = "report_source_index" if status == "unmatched_possible_sh_report" else "source_index"
                require_fields(row, (locator, "status", "segments"), label)
                index = row[locator]
                require_count(index, label)
                key = locator, index
                require(key not in seen and type(row["segments"]) is list and bool(row["segments"])
                        and all(type(i) is int and i in segment_seconds for i in row["segments"])
                        and row["segments"] == sorted(set(row["segments"])),
                        f"{label}: duplicate or unbound attempt disposition")
                seen.add(key)
                if status == "matched_neutral":
                    require(len(row["segments"]) == 1, f"{label}: ambiguous matched attempt segment")
                    if row["segments"][0] not in excluded:
                        expected.append(f"{game_id}:{index}")
                else:
                    require(status in ("unmatched_possible_sh_report", "unresolved_possible_attempt",
                                        "ambiguous_potential_shorthanded", "membership_assignment_unresolved",
                                        "neutral_score_unavailable")
                            and all(i in excluded for i in row["segments"]),
                            f"{label}: unresolved attempt retained in matched time")
            require(game["retained_keys"] == expected and not retained_by_strength.intersection(expected),
                    f"{label}: retained attempt identity differs")
            retained_by_strength.update(expected)
            require_count(game["attempts"], label)
            weights = game["retained_masses"]
            require(type(weights) is list and len(weights) == len(expected) == game["attempts"],
                    f"{label}: retained attempt count differs")
            require(require_number(game["neutral_goal_mass"], label, low=0) ==
                    math.fsum(require_number(weight, label, low=0, high=1) for weight in weights),
                    f"{label}: retained neutral mass differs")

        support = result["sh_support"]
        expected = _shorthanded_support(games)
        require_fields(support, expected, strength)
        require_count(support["attempts"], strength)
        for field in ("included_seconds", "known_excluded_seconds", "neutral_goal_mass"):
            require_number(support[field], strength, low=0)
        require(type(support["unquantified_gap"]) is bool and support == expected,
                f"{strength}: saved shorthanded accounting differs")
    return receipt


def _shorthanded_games(prepared, scores, selected, strengths):
    from itertools import groupby
    from operator import itemgetter

    from .analysis_data import read_prepared_game

    season = selected["season"]
    game_ids = selected["selected_game_ids"]
    receipts = {state: {} for state in strengths}
    stream = groupby(scores.events(), key=itemgetter("game_id"))
    next_scored = next(stream, None)
    for game_id in sorted(game_ids):
        scored = {}
        if next_scored is not None:
            score_game, rows = next_scored
            require(score_game >= game_id, f"{score_game}: score game outside selected reduction")
            if score_game == game_id:
                previous = -1
                for row in rows:
                    index = row["source_index"]
                    require(previous < index and row["key"] == f"{game_id}:{index}"
                            and row["season"] == season, f"{game_id}: unordered or foreign score key")
                    scored[index] = row
                    previous = index
                next_scored = next(stream, None)
        game = read_prepared_game(prepared, season, game_id)
        for strength, receipt in _shorthanded_game(game, scored, strengths).items():
            receipts[strength][game_id] = receipt
    require(next_scored is None, "unconsumed game in shorthanded execution score stream")

    result = {}
    for strength, by_game in receipts.items():
        games = [by_game[game_id] for game_id in game_ids]
        support = _shorthanded_support(games)
        if strength == "4v5":
            # Preserve the accepted minor-reference accrual in its original date order.
            for field in ("included_seconds", "known_excluded_seconds", "neutral_goal_mass"):
                value = 0.
                for row in games:
                    value += row[field]
                support[field] = value
        result[strength] = dict(sh_support=support, games=games)
    return result


def _shorthanded_support(games):
    return dict(included_seconds=math.fsum(row["included_seconds"] for row in games),
                known_excluded_seconds=math.fsum(row["known_excluded_seconds"] for row in games),
                neutral_goal_mass=math.fsum(row["neutral_goal_mass"] for row in games),
                attempts=sum(row["attempts"] for row in games),
                unquantified_gap=any(row["unquantified_gap"] for row in games))


def _shorthanded_game(game, scored, strengths):
    from .execution_history import _value
    from .mechanism_design import _affected, choice_population, mechanism_membership
    from .reconstruct import report_membership, roster_identities

    game_id = game["game_id"]
    source = game["game"]
    support = game["ordinary_attempt_support"]
    segments = {row["segment_index"]: row for row in game["segments"] or ()}
    attempts = {row["source_index"]: row for row in game["attempts"] or ()}
    require(scored.keys() <= attempts.keys(), f"{game_id}: score key absent from native attempt population")
    membership = mechanism_membership(game)
    physical = {}
    for index, segment in segments.items():
        members = segment["membership"]
        if len(members["home_goalies"]) == len(members["away_goalies"]) == 1:
            physical[index] = tuple(sorted(len(members[side + "_skaters"]) for side in ("home", "away")))
    unsupported = set(membership["excluded_segments"])
    for reason in support["reasons"]:
        if reason["code"] in ("source_unavailable", "count_accounting_conflict"):
            unsupported.update(reason["affected_segment_indices"])
    if game["attempts"] is None or game["events"] is None:
        unsupported.update(segments)

    assignments = {row["source_index"]: row for row in support["events"] or ()}
    events = {row["source"]["source_index"]: row for row in game["events"] or ()}
    unassigned = {}
    for index, assignment in assignments.items():
        if index not in attempts and assignment["disposition"] != "not_applicable":
            event_source = events.get(index, {}).get("source", {})
            unassigned[index] = _affected(list(segments.values()), event_source.get("period_number"),
                                           event_source.get("elapsed_seconds"))

    report_index = {row["source_index"]: row for row in source["report_rows"] or ()}
    roster = roster_identities([row for person in (game["people"] or {}).values() for row in person["roster"]])
    identity = source["identity"] or source["inventory"]
    unmatched = []
    for report_only in support["report_only"] or ():
        report = report_index[report_only["report_source_index"]]
        if report["period_number"] == 5 or report["penalty_shot"] is True:
            continue
        members, invalid = report_membership(report, identity, roster, [])
        side = next((side for side in ("home", "away") if report["shooting_team_id"] == identity[side + "_team_id"]), None)
        state = None
        if not invalid and side is not None and all(len(members[s + "_goalies"]) == 1 for s in ("home", "away")):
            other = "away" if side == "home" else "home"
            state = (len(members[side + "_skaters"]), len(members[other + "_skaters"]))
        unmatched.append((report["source_index"], state, set(report_only["affected_segment_indices"])))

    exact_states = {strength: tuple(map(int, strength.split("v"))) for strength in strengths}
    complete_trace = strengths == ("4v5",)
    choices = choice_population(game) if complete_trace or set(physical.values()) & set(exact_states.values()) else ()
    result = {}
    for strength, counts in exact_states.items():
        short = {index for index, state in physical.items() if state == counts}
        excluded = unsupported & short
        dispositions, retained = [], []
        for index, state, implicated in unmatched:
            other_state = state is not None and state != counts
            affected = [] if other_state else sorted(implicated & short)
            excluded.update(affected)
            if complete_trace or affected:
                dispositions.append(dict(report_source_index=index, segments=affected,
                    status="proved_nonsh_report" if other_state else "unmatched_possible_sh_report"))
        for index, implicated in unassigned.items():
            affected = sorted(set(implicated) & short)
            excluded.update(affected)
            if complete_trace or affected:
                dispositions.append(dict(source_index=index, status="unresolved_possible_attempt", segments=affected))
        for choice in choices:
            index = choice["source_index"]
            attempt = attempts[index]
            details = attempt["details"]
            physical_status = _value(details, "physical_status")
            if physical_status == "outside_population":
                continue
            if complete_trace and choice["strength"] not in (None, strength):
                dispositions.append(dict(source_index=index, status="outside_shorthanded_population", segments=[]))
                continue
            assignment = assignments.get(index)
            segment_index = None if assignment is None else assignment["segment_index"]
            if segment_index is None:
                event_source = events.get(index, {}).get("source", {})
                implicated = set(_affected(list(segments.values()), event_source.get("period_number"),
                                           event_source.get("elapsed_seconds"))) & short
            else:
                require(segment_index in segments, "shorthanded attempt segment absent")
                implicated = {segment_index} & short
            state = attempt["feature_facts"]["state"]
            side = choice["attacking_side"]
            if complete_trace:
                if not implicated and choice["strength"] is None:
                    continue
            else:
                # Event lineup counts can conflict with native time. Only a
                # proved team on the long side can clear an implicated segment.
                if (physical_status == "ordinary" and side in ("away", "home")
                        and _value(details, "shooting_team_id") == _value(state, "shooting_team_id")
                        == identity[side + "_team_id"]):
                    implicated = {i for i in implicated
                                  if len(segments[i]["membership"][side + "_skaters"]) == counts[0]}
                if not implicated:
                    continue

            key = f"{game_id}:{index}"
            if ((choice["status"] != "included" and choice["reason"] != "goalie_attempt")
                    or choice["strength"] != strength or segment_index not in short):
                status = "ambiguous_potential_shorthanded"
            else:
                members = segments[segment_index]["membership"]
                other = "away" if side == "home" else "home"
                require((len(members[side + "_skaters"]), len(members[other + "_skaters"])) == counts,
                        f"{key}: shorthanded source/segment strength contradicts")
                if any(sorted(_value(state, k) or []) != sorted(members[k]) for k in members):
                    status = "membership_assignment_unresolved"
                else:
                    score = scored.get(index)
                    if score is not None:
                        require(score["physical_state"] is None or tuple(score["physical_state"]) == (*counts, 1, 1),
                                f"{key}: execution score state lineage differs")
                        require(score["shooter_id"] is None or score["shooter_id"] == choice["shooter_id"],
                                f"{key}: execution score shooter lineage differs")
                        require(score["outcome"] is None or score["outcome"] == _value(details, "outcome"),
                                f"{key}: execution score outcome lineage differs")
                    if score is None or score["status"] != "complete":
                        status = "neutral_score_unavailable"
                    else:
                        value = score["prefixes"]["neutral"]["uqrg"]
                        require(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1,
                                f"{key}: invalid saved neutral mass")
                        retained.append((segment_index, key, float(value)))
                        status = "matched_neutral"
            if status != "matched_neutral":
                excluded.update(implicated)
            dispositions.append(dict(source_index=index, status=status, segments=sorted(implicated)))

        kept = [(key, value) for index, key, value in retained if index not in excluded]
        duration = {index: segments[index]["end_seconds"] - segments[index]["start_seconds"] for index in short}
        add = sum if complete_trace else math.fsum
        receipt = dict(game_id=game_id, included_seconds=add(duration[i] for i in short - excluded),
            known_excluded_seconds=add(duration[i] for i in excluded), excluded_segments=sorted(excluded),
            attempts=len(kept), neutral_goal_mass=math.fsum(value for _, value in kept),
            retained_keys=[key for key, _ in kept], dispositions=dispositions,
            unquantified_gap=membership["unquantified_gap"])
        if not complete_trace:
            receipt["segment_seconds"] = [dict(segment_index=i, seconds=duration[i]) for i in sorted(short)]
            receipt["retained_masses"] = [value for _, value in kept]
        result[strength] = receipt
    return result


def reduce_minor_reference(prepared,execution_score,ev_saved,st_saved,*,output):
    """Reduce matched shorthanded neutral mass for the isolated-minor reference."""
    from .analysis_data import PreparedManifest,read_prepared
    from .artifacts import write_json
    from .chance_cli import read_json
    from .execution_scores import ExecutionScores,read_execution_scores
    from .spatial_rates import ST_RECIPE
    from .spatial_state import SavedSpatialEvidence,read_saved_spatial_evidence
    if not isinstance(prepared,PreparedManifest):
        p=input_path(prepared,strict=True);purpose=read_json(p/'manifest.json' if p.is_dir() else p)['purpose'];prepared=read_prepared(p,purpose)
    purpose=prepared['purpose']
    scores=execution_score if isinstance(execution_score,ExecutionScores) else read_execution_scores(execution_score,purpose)
    season,selected,expected_prepared=_shorthanded_inputs(prepared,scores)
    ev=ev_saved if isinstance(ev_saved,SavedSpatialEvidence) else read_saved_spatial_evidence(ev_saved,purpose)
    st=st_saved if isinstance(st_saved,SavedSpatialEvidence) else read_saved_spatial_evidence(st_saved,purpose,expected_family='st',expected_recipe=ST_RECIPE)
    score_binding=identity(scores.path)
    for saved in (ev,st):
        require(saved.manifest['season']==season and saved.manifest['purpose']==purpose
            and same_input_reference(saved.manifest['prepared'],expected_prepared),'minor reference saved annual lineage differs')
        require(same_input_reference({k:saved.manifest['valued'][k] for k in ('path','sha256')},score_binding),'minor reference saved score lineage differs')
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
    reduction=_shorthanded_games(prepared,scores,selected,('4v5',))['4v5']
    sh_support=reduction['sh_support']
    game_receipts=reduction['games']
    mass=sh_support['neutral_goal_mass'];included_seconds=sh_support['included_seconds']
    b=mass/(included_seconds/3600) if included_seconds>0 else None
    bindings=dict(prepared=identity(prepared.directory/'manifest.json'),execution_score=score_binding,
                  ev_state=identity(ev.path/'manifest.json'),st_state=identity(st.path/'manifest.json'))
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
