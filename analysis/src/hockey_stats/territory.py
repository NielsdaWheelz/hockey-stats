"""annual inferred movement hazards and common-survival successor value.

transition exposure is seconds. spatial panel mass is xg/hour/cell. successor
maps are goals per 1,000 5v5 minutes and never receive another workload factor.
"""
from dataclasses import replace
from math import exp, expm1, fsum, isfinite, log
from pathlib import Path
import resource
from time import perf_counter

import numpy as np
from scipy.linalg import expm, solve

from .artifacts import require
from .captures import InputContractError
from .chance import solve_logistic
from .player_mechanisms import (SOLVER, CONTINUATION, body_digest, actor_prior,
    scalar_intensity_objective, scalar_predictor)

HEADS=('entry','exit')
ROLES=('entry_offense','entry_prevention','exit_offense','zone_retention')
STARTS=('DZ','NZ','OZ','on_the_fly')
AGE_BINS=(0,10,20,40,60,90)


def close(a,b):
    return abs(a-b)<=1e-9+1e-9*max(abs(a),abs(b))


def territory_recipe(design_recipe):
    body=dict(id='territory-v1-11-1',design=design_recipe,solver=SOLVER,continuation=CONTINUATION,
        offset='(crossings+.5)/(directed_seconds+30)',
        loss='sum(seconds*exp(log(r)+X*beta))-sum(crossings*(log(r)+X*beta))+.5*sum(precision*(beta-mean)^2)',
        player_sd=dict(entry=.25,carry_per_sqrt_year=.10),coach_sd=dict(entry=.10,carry_per_sqrt_year=.05),
        context_sd=1.,intercept_sd=2.,history='separate-head-role-last-risk-supported-raw-coordinate; entry-or-carry',
        centering='own-head role-slot/applicable seconds; transfer offsets; zero centered context',
        shift='3-zone block exponential, 6 age bins, same-zone self-restart, linear-solve infinite tail',
        nuisance='w,d=(events+.5)/(seconds+30);h=(ended+.5)/(decidable+1);R=(count+.5)/(total+1.5)',
        successor='one-slot positive xg contrasts; common neutral survival; normalized-occupancy maximal-weight pivot',
        diagnostic_limits=dict(hazard_per_hour=1e-4,probability=1e-5,goals=1e-3))
    return dict(**body,sha256=body_digest(body))


def territory_objective(beta,design,mean,precision,log_rate):
    return scalar_intensity_objective(beta,design,mean,precision,log_rate,design.exposure_seconds)


def smooth_nuisance(raw):
    """freeze source denominators separately; missing aggregate support stays missing."""
    arrays={k:np.asarray(raw[k],dtype=float) for k in ('risk_seconds','whistles','live_endings',
        'decidable_whistles','ended_whistles','restart_counts','start_counts','on_the_fly_zone_counts')}
    for key,value in arrays.items():
        shape=(3,3) if key=='restart_counts' else (4,) if key=='start_counts' else (3,) if key=='on_the_fly_zone_counts' else (3,6)
        require(value.shape==shape and np.isfinite(value).all() and np.all(value>=0),f'invalid nuisance {key}')
        if key!='risk_seconds':require(np.all(value==np.floor(value)),f'noninteger nuisance {key}')
    risk=arrays['risk_seconds'];decidable=arrays['decidable_whistles'];ended=arrays['ended_whistles']
    require(np.all(ended<=decidable) and np.all(decidable<=arrays['whistles']),'nuisance whistle trial counts differ')
    require(not np.any((risk==0)&((arrays['whistles']>0)|(arrays['live_endings']>0))),'nuisance events lack risk')
    require(arrays['on_the_fly_zone_counts'].sum()==arrays['start_counts'][3],'on-the-fly starts lack matched zones')
    missing=[key for key,count in (('risk',risk.sum()),('decidable_whistles',decidable.sum()),
        ('restart_pairs',arrays['restart_counts'].sum()),('starts',arrays['start_counts'].sum())) if count<=0]
    if missing:return dict(status='unavailable',reasons=['missing_'+key for key in missing],raw=raw)
    starts=arrays['start_counts']/arrays['start_counts'].sum()
    mixture=None if starts[3]==0 else arrays['on_the_fly_zone_counts']/arrays['on_the_fly_zone_counts'].sum()
    initial=starts[:3].copy()
    if mixture is not None:initial+=starts[3]*mixture
    return dict(status='complete',reasons=[],raw=raw,w=(arrays['whistles']+.5)/(risk+30),
        d=(arrays['live_endings']+.5)/(risk+30),h=(ended+.5)/(decidable+1),
        R=(arrays['restart_counts']+.5)/(arrays['restart_counts'].sum(axis=1)[:,None]+1.5),
        start_probabilities=starts,on_the_fly_zone_mixture=mixture,initial_zone_probabilities=initial,
        prior_only=dict(w=(risk==0),d=(risk==0),h=(decidable==0),R=(arrays['restart_counts'].sum(axis=1)==0)))


def movement_generator(hazards):
    """own-team order: exit offense, entry offense, retention, prevention."""
    q=np.asarray(hazards,dtype=float)
    require(q.shape==(4,) and np.isfinite(q).all() and np.all(q>0),'invalid territory hazards')
    Q=np.array([[0,q[0],0],[q[3],0,q[1]],[0,q[2],0]])
    Q[np.diag_indices(3)]=-Q.sum(axis=1)
    return Q


def shift_process(Q,w,d,h,R,initial):
    """exact age-piecewise occupancy and absorption, including an infinite tail."""
    Q,w,d,h,R,alpha=(np.asarray(v,dtype=float) for v in (Q,w,d,h,R,initial))
    require(Q.shape==R.shape==(3,3) and w.shape==d.shape==h.shape==(3,6) and alpha.shape==(3,),
            'shift process axes differ')
    require(all(np.isfinite(v).all() for v in (Q,w,d,h,R,alpha)),'nonfinite shift process input')
    require(np.all(w>=0) and np.all(d>=0) and np.all((h>=0)&(h<=1)) and np.all((R>=0)&(R<=1))
        and np.all((alpha>=0)&(alpha<=1)) and close(fsum(alpha),1.),'invalid shift rates/probabilities')
    off=Q.copy();np.fill_diagonal(off,0)
    require(np.all(off>=0) and np.all(np.diag(Q)<=0),'invalid movement generator domain')
    for row in Q:require(abs(fsum(row))<=1e-12*max(1.,fsum(abs(row))),'movement generator does not close')
    require(all(close(fsum(row),1.) for row in R),'restart rows do not sum to one')
    end=np.zeros(4);occupancy=[];survival_at_90=None
    for b in range(6):
        B=np.column_stack((w[:,b,None]*h[:,b,None]*R,d[:,b]))
        T=off+w[:,b,None]*(1-h[:,b,None])*R
        np.fill_diagonal(T,0)
        np.fill_diagonal(T,-T.sum(axis=1)-d[:,b]-w[:,b]*h[:,b])
        for row,absorbing in zip(T,B,strict=True):
            require(abs(fsum(row)+fsum(absorbing))<=1e-12*max(1.,fsum(abs(row))+fsum(absorbing)),
                    'transient generator row does not close')
        if b<5:
            dt=AGE_BINS[b+1]-AGE_BINS[b]
            block=np.zeros((6,6));block[:3,:3]=T;block[:3,3:]=np.eye(3)
            transition=expm(block*dt)
            occupied=alpha@transition[:3,3:]
            following=alpha@transition[:3,:3]
        else:
            survival_at_90=fsum(alpha)
            occupied=solve((-T).T,alpha,assume_a='gen',check_finite=True)
            following=np.zeros(3)
        absorbed=occupied@B
        require(np.isfinite(occupied).all() and np.all(occupied>=0) and np.isfinite(absorbed).all()
            and np.all((absorbed>=0)&(absorbed<=1)) and np.isfinite(following).all()
            and np.all((following>=0)&(following<=1)),'invalid shift mass')
        require(close(fsum(alpha),fsum(absorbed)+fsum(following)),'shift bin mass does not close')
        end+=absorbed;occupancy.append(fsum(occupied));alpha=following
    mean=fsum(occupancy)
    require(isfinite(mean) and mean>0 and np.all((end>=0)&(end<=1)) and close(fsum(end),1.)
        and 0<=survival_at_90<=1 and 0<=occupancy[5]/mean<=1,'shift absorption/time does not close')
    n0=60000/mean
    require(isfinite(n0) and n0>0,'nonfinite reference shift workload')
    return dict(end_probabilities=end,bin_occupancy_seconds=np.asarray(occupancy),mean_shift_seconds=mean,
        shifts_per_1000_minutes=n0,survival_at_90=survival_at_90,tail_time_fraction=occupancy[5]/mean)


def stable_successor_map(difference,omega,contrast):
    """contract only used starts, centered before summation to preserve cancellation."""
    difference,omega,contrast=(np.asarray(v,dtype=float) for v in (difference,omega,contrast))
    require(difference.shape==(4,) and omega.shape==(6,) and contrast.shape==(2,4,6,656),
            'successor projection axes differ')
    require(all(np.isfinite(v).all() for v in (difference,omega,contrast)) and np.all(omega>=0)
        and close(fsum(omega),1.) and close(fsum(difference),0.),'invalid successor projection input')
    result=np.zeros((2,656))
    active=np.flatnonzero(difference)
    if not len(active):return result
    pivot=int(np.argmax(abs(difference)))
    for side in range(2):
        for cell in range(656):
            result[side,cell]=(1000/60)*fsum(float(omega[b])*fsum(float(difference[z])*
                (float(contrast[side,z,b,cell])-float(contrast[side,pivot,b,cell])) for z in active if z!=pivot)
                for b in range(6) if omega[b]!=0)
    require(np.isfinite(result).all(),'nonfinite successor map')
    return result


def successor_reference(process,panel):
    """bind native per-shift contrasts and uncanceled absolute term scales."""
    neutral=np.asarray(panel['neutral_xg'],dtype=float)
    complete=np.asarray(panel['complete_xg'],dtype=float)
    contrast=np.asarray(panel['contrast_xg'],dtype=float)
    require(neutral.shape==(656,) and complete.shape==contrast.shape==(2,4,6,656),'successor panel axes differ')
    require(all(np.isfinite(v).all() for v in (neutral,complete,contrast)) and np.all(neutral>0)
        and np.all(complete>0),'invalid successor xg panel')
    require(np.allclose(complete-neutral,contrast,rtol=1e-9,atol=1e-9),'successor panel contrast differs')
    W=np.asarray(process['bin_occupancy_seconds']);G=np.zeros((2,4,656));A=np.zeros((2,4))
    for side in range(2):
        for z in range(4):
            for cell in range(656):G[side,z,cell]=fsum(float(W[b]/3600)*float(contrast[side,z,b,cell]) for b in range(6))
            A[side,z]=fsum(float(W[b]/3600)*(abs(float(complete[side,z,b,c]))+abs(float(neutral[c])))
                for b in range(6) for c in range(656))
    require(np.isfinite(G).all() and np.isfinite(A).all() and np.all(A>=0),'nonfinite successor reference')
    scalars=np.array([[fsum(G[s,z]) for z in range(4)] for s in range(2)])
    require(np.all(abs(scalars)<=A+1e-9+1e-9*A),'successor G exceeds absolute term bound')
    return dict(G_maps=G,G=scalars,absolute_term_scales=A,contrast=contrast)


def successor_value(neutral,focal,reference):
    difference=np.asarray(focal['end_probabilities'])-np.asarray(neutral['end_probabilities'])
    require(close(fsum(difference),0.),'focal-neutral absorption difference does not sum to zero')
    omega=np.asarray(neutral['bin_occupancy_seconds'])/neutral['mean_shift_seconds']
    maps=stable_successor_map(difference,omega,reference['contrast'])
    n0=neutral['shifts_per_1000_minutes'];values=[];allowances=[];map_allowances=[];raw=[]
    for side in range(2):
        scalar=fsum(maps[side]);raw_value=n0*fsum(float(difference[z])*float(reference['G'][side,z]) for z in range(4) if difference[z]!=0)
        allowance=64*2.**-52*n0*fsum(abs(float(difference[z]))*float(reference['absolute_term_scales'][side,z]) for z in range(4))
        require(all(isfinite(value) for value in (scalar,raw_value,allowance)),'nonfinite successor scalar/accounting allowance')
        require(abs(scalar-raw_value)<=1e-9+1e-9*max(abs(scalar),abs(raw_value))+allowance,'raw-G successor accounting differs')
        values.append(scalar);raw.append(raw_value);allowances.append(allowance)
        map_allowances.append(64*2.**-52*fsum(abs(maps[side])))
    return dict(end_probabilities=focal['end_probabilities'],end_probability_difference=difference,
        maps=maps,values=np.asarray(values),raw_G_values=np.asarray(raw),raw_G_allowance=np.asarray(allowances),
        map_sum_allowance=np.asarray(map_allowances))


def _actor_key(row):
    return row['block'],str(row['id']),row['subblock']


def annual_territory_priors(design,head,ledger):
    previous={_actor_key(row):row for row in ledger}
    require(len(previous)==len(ledger),'duplicate territory history actor')
    incidence=np.asarray(head.X_time.T@head.exposure_seconds).ravel()
    counts=np.asarray(head.X_event.T@head.event_counts).ravel()
    mean=np.zeros(len(head.columns));precision=np.ones(len(head.columns));priors=[]
    for index,column in enumerate(head.columns):
        if column['kind']!='actor':
            precision[index]=.25 if column['kind']=='intercept' else 1.
            continue
        last=previous.get(_actor_key(column));player=column['block'].endswith('_player')
        mean[index],precision[index],gap=actor_prior(last,design.season,.25 if player else .1,.1 if player else .05)
        information=float(incidence[index]);events=int(counts[index])
        require(information>=0 and counts[index]==events and events>=0,'invalid territory actor information')
        require(information>0 or events==0,'territory actor crossings lack risk')
        supported=information>0
        priors.append(dict(index=index,block=column['block'],id=str(column['id']),subblock=column['subblock'],
            information_weight=information,likelihood_events=events,current_season_information=supported,prior_only=not supported,
            prior_kind='entry' if last is None else 'carry',prior_anchor_season=None if last is None else last['season'],
            prior_seasons=[] if last is None else last['support_seasons'],mean=float(mean[index]),precision=float(precision[index])))
    return priors,mean,precision


def center_head(design,head,beta,log_rate):
    total=fsum(head.exposure_seconds)
    require(total>0,'cannot center territory head without risk')
    incidence=np.asarray(head.X_time.T@head.exposure_seconds).ravel()
    centers=[];centered=beta.copy();eta=log_rate+float(beta[0]);groups={}
    for i,column in enumerate(head.columns):
        if column['kind']=='actor':groups.setdefault((column['block'],column['subblock']),[]).append(i)
    for (block,subblock),indices in groups.items():
        weight=fsum(incidence[indices]);center=float(np.dot(incidence[indices],beta[indices])/weight) if weight>0 else 0.
        applicability=weight/total;eta+=center*applicability;centered[indices]-=center
        centers.append(dict(block=block,subblock=subblock,mean=center,weight_seconds=weight,
            reference_applicability=applicability,reference_offset=center*applicability))
    neutral=exp(eta)
    require(isfinite(neutral) and neutral>0,'invalid neutral territory intensity')
    # the transferred reference is for zero centered context. the factual
    # predictor uses the actual applicable coach incidence on each risk row.
    for kind in ('time','event'):
        matrix=getattr(head,'X_'+kind);offset=np.zeros(matrix.shape[0])
        for center in centers:
            indices=groups[(center['block'],center['subblock'])]
            offset+=np.asarray(matrix[:,indices].sum(axis=1)).ravel()*center['mean']
        before=scalar_predictor(head,beta,kind)
        after=scalar_predictor(head,centered,kind)+offset
        require(np.allclose(before,after,rtol=1e-12,atol=1e-12),'territory centering changes factual prediction')
    return centers,dict(log_rate=log_rate,neutral_predictor=eta,neutral_per_second=neutral,
        units='crossings_per_second',player_slots_per_side=5,context='zero centered context; neutral residual coaches'),centered


def _compress_head(head):
    changes={}
    for kind,weight in (('time','exposure_seconds'),('event','event_counts')):
        actor=getattr(head,'X_'+kind);context=getattr(head,'context_'+kind);weights=getattr(head,weight)
        groups={};indices=[];totals=[];keys=[]
        for row in range(actor.shape[0]):
            begin,end=actor.indptr[row:row+2]
            key=(actor.indices[begin:end].tobytes(),actor.data[begin:end].tobytes(),context[row].tobytes())
            index=groups.get(key)
            if index is None:
                groups[key]=len(indices);indices.append(row);totals.append([float(weights[row])]);keys.append([getattr(head,kind+'_keys')[row]])
            else:totals[index].append(float(weights[row]));keys[index].append(getattr(head,kind+'_keys')[row])
        changes['X_'+kind]=actor[indices];changes['context_'+kind]=context[indices]
        changes[weight]=np.array([fsum(group) for group in totals],dtype=float)
        changes[kind+'_keys']=tuple(dict(source_rows=group) for group in keys)
    return replace(head,**changes)


def _fit_territory_head(design,head,incoming,*,initial=None,tightened=False):
    priors,mean,precision=annual_territory_priors(design,head,incoming)
    risk=fsum(head.exposure_seconds);events=fsum(head.event_counts)
    require(risk>0 or events==0,'territory crossings without head exposure')
    result=dict(status='unavailable' if risk==0 else 'failed',reasons=['no_exposure'] if risk==0 else [],
        priors=priors,ledger=list(incoming),centers=None,reference=None,objective=None,solver=None,diagnostics=None)
    if risk==0:return result,None
    log_rate=log((events+.5)/(risk+30));options=CONTINUATION if tightened else SOLVER
    objective=lambda b:territory_objective(b,head,mean,precision,log_rate)
    try:
        began=perf_counter()
        beta,solver=solve_logistic(objective,mean if initial is None else initial,**options)
        solver_wall_seconds=perf_counter()-began
        for prior in priors:
            if prior['prior_only']:beta[prior['index']]=prior['mean']
        value,gradient=objective(beta)
        solver.update(options=options,gradient_inf_norm=float(np.max(abs(gradient))),
            achieved_gtol=bool(np.max(abs(gradient))<=options['gtol']),wall_seconds=solver_wall_seconds,
            peak_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        result.update(solver=solver,objective=dict(penalized_loss=value,gradient_inf_norm=solver['gradient_inf_norm']))
        if not solver['converged']:
            result['reasons']=['optimizer_failed'];return result,None
        centers,reference,centered=center_head(design,head,beta,log_rate)
        ledger={_actor_key(row):dict(row) for row in incoming}
        for prior in priors:
            if prior['current_season_information']:
                ledger[_actor_key(prior)]=dict(block=prior['block'],id=prior['id'],subblock=prior['subblock'],
                    coefficient=float(beta[prior['index']]),season=design.season,support_seasons=prior['prior_seasons']+[design.season])
        predicted=np.exp(log_rate+scalar_predictor(head,beta,'time'))
        require(np.isfinite(predicted).all() and np.all(predicted>0),'invalid fitted territory hazards')
        zones={zone:dict(zone=zone,directed_risk_seconds=0.,observed_crossings=0,expected_crossings=0.) for zone in range(3)}
        for row,key in enumerate(head.time_keys):
            for source in key.get('source_rows',[key]):
                if 'zone' not in source:continue
                seconds=source['end_seconds']-source['start_seconds'];zone=zones[source['zone']]
                zone['directed_risk_seconds']+=seconds;zone['expected_crossings']+=seconds*predicted[row]
        for key in head.event_keys:
            for source in key.get('source_rows',[key]):
                if 'zone' in source:zones[source['zone']]['observed_crossings']+=1
        result.update(status='complete',reasons=[],ledger=[ledger[k] for k in sorted(ledger)],centers=centers,reference=reference,
            diagnostics=dict(kind='in_sample_not_held_out',observed_crossings=events,
                expected_crossings=fsum(head.exposure_seconds*predicted),directed_risk_seconds=risk,
                minimum_hazard_per_second=float(np.min(predicted)),maximum_hazard_per_second=float(np.max(predicted)),
                zone_support=list(zones.values())))
        return result,beta
    except (InputContractError,FloatingPointError,OverflowError,ValueError) as error:
        result.update(status='failed',reasons=[f'numerical_domain_failure:{type(error).__name__}:{error}'],
            ledger=list(incoming),centers=None,reference=None,diagnostics=None)
        return result,None


def project_hazards(design,heads,coefficients):
    projections=[];support=[];reported={}
    for name in HEADS:
        head=heads[name]
        if head['status']=='complete':
            centers,reference,beta=center_head(design,design.heads[name],coefficients[name],head['reference']['log_rate'])
            reported[name]=(reference,beta)
    for player in design.players:
        roles={};role_support={}
        for name,role_names in (('entry',('entry_offense','entry_prevention')),('exit',('exit_offense','zone_retention'))):
            head=heads[name];prior_map={row['id']+':'+row['block']:row for row in head['priors']}
            columns={str(col['id'])+':'+col['block']:i for i,col in enumerate(design.heads[name].columns) if col['kind']=='actor'}
            for block,role in zip(('attacking_player','defending_player'),role_names,strict=True):
                prior=prior_map[player+':'+block]
                neutral=focal=probability=neutral_probability=None
                if name in reported:
                    reference,beta=reported[name];neutral=reference['neutral_per_second']
                    focal=neutral*exp(float(beta[columns[player+':'+block]]))
                    require(isfinite(focal) and focal>0,'invalid focal territory hazard')
                    probability=exp(-focal) if block=='defending_player' else -expm1(-focal)
                    neutral_probability=exp(-neutral) if block=='defending_player' else -expm1(-neutral)
                roles[role]=dict(status=head['status'],reasons=head['reasons'],hazard_per_second=focal,neutral_hazard_per_second=neutral,
                    one_second_probability=probability,neutral_one_second_probability=neutral_probability)
                role_support[role]=dict(status=head['status'],risk_seconds=prior['information_weight'],crossings=prior['likelihood_events'],
                    current_season_information=prior['current_season_information'],prior_only=prior['prior_only'] if head['status']=='complete' else False,
                    prior_kind=prior['prior_kind'] if head['status']=='complete' else None,
                    prior_anchor_season=prior['prior_anchor_season'] if head['status']=='complete' else None,
                    prior_seasons=prior['prior_seasons'] if head['status']=='complete' else [])
        projections.append(dict(player_id=player,season=design.season,roles=roles))
        support.append(dict(player_id=player,season=design.season,roles=role_support,qualification=design.coverage['players'][player]))
    return projections,support


def fit_territory(design,previous,output,*,final_year=False):
    from .territory_state import TerritoryState,read_territory_state,validate_design,write_territory_state
    began=perf_counter();validate_design(design)
    predecessor=None if previous is None else previous if isinstance(previous,TerritoryState) else read_territory_state(previous,design.purpose,narrow=True)
    require(design.season!='20212022' or predecessor is None,'first territory annual rejects a predecessor')
    if predecessor is not None:
        require(predecessor.manifest['purpose']==design.purpose
            and predecessor.manifest['season']==f'{int(design.season[:4])-1}{design.season[:4]}'
            and all(predecessor.heads[h]['status']=='complete' for h in HEADS),'territory predecessor is not the completed prior annual')
        require(predecessor.manifest['recipe']==territory_recipe(design.recipe),'territory predecessor recipe differs')
        for key in ('prepared','coaches'):
            require(all(predecessor.manifest[key][field]==getattr(design,key)[field] for field in ('path','sha256')),
                    f'territory predecessor {key} binding differs')
    if design.purpose=='real':
        require((design.season=='20212022')==(predecessor is None),'real territory chronology differs')
        require(not final_year or design.season=='20252026','territory diagnostics require final annual')
    validation_wall_seconds=perf_counter()-began
    compression_began=perf_counter()
    design=replace(design,heads={name:_compress_head(design.heads[name]) for name in HEADS})
    compression_wall_seconds=perf_counter()-compression_began
    fit_began=perf_counter()
    heads={};coefficients={};probes={}
    for name in HEADS:
        incoming=[] if predecessor is None else predecessor.heads[name]['ledger']
        heads[name],beta=_fit_territory_head(design,design.heads[name],incoming)
        if beta is not None:coefficients[name]=beta
        if final_year:
            if beta is None:probes[name]=dict(head=None,coefficients=None,reason='baseline_incomplete')
            else:
                probe_head,probe_beta=_fit_territory_head(design,design.heads[name],incoming,initial=beta,tightened=True)
                probes[name]=dict(head=probe_head,coefficients=probe_beta,reason=None)
    fit_wall_seconds=perf_counter()-fit_began
    projection_began=perf_counter();projections,support=project_hazards(design,heads,coefficients)
    hazard_projection_wall_seconds=perf_counter()-projection_began
    solver_wall_seconds=dict(
        baseline={name:None if heads[name]['solver'] is None else heads[name]['solver']['wall_seconds'] for name in HEADS},
        diagnostic={name:None if name not in probes or probes[name]['head'] is None or probes[name]['head']['solver'] is None
            else probes[name]['head']['solver']['wall_seconds'] for name in HEADS})
    resources=dict(validation_wall_seconds=validation_wall_seconds,compression_wall_seconds=compression_wall_seconds,
        fit_wall_seconds=fit_wall_seconds,solver_wall_seconds=solver_wall_seconds,
        hazard_projection_wall_seconds=hazard_projection_wall_seconds,wall_seconds_before_writing=perf_counter()-began,
        peak_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        peak_memory_scope='process high-water sampled after hazard projection; includes preparation and earlier stages; later write/readback peaks excluded',
        solver_wall_scope='native solve_logistic call only; excludes prior construction, final gradient evaluation, centering and diagnostics',
        baseline_solves=sum(heads[name]['status']!='unavailable' for name in HEADS),
        diagnostic_solves=sum(probe['head'] is not None for probe in probes.values()),preparation=design.resources,
        wall_scope='validation, compression, head fitting and hazard projection timed separately; native solver time is nested within head fitting; preparation and artifact writing separately reported')
    return write_territory_state(Path(output),design,predecessor,heads,coefficients,probes,projections,support,resources)


def project_territory(state,successor_panel,*,variant='baseline'):
    """derive references and focal maps without rewriting an immutable annual fit."""
    require(variant in ('baseline','entry','exit','joint'),'unknown territory projection variant')
    design=state.design;require(design is not None,'territory projection requires saved compact design')
    heads=dict(state.heads);coefficients=dict(state.coefficients)
    if variant!='baseline':
        for name in HEADS:
            if variant not in (name,'joint'):continue
            probe=state.probes.get(name)
            if probe is None or probe['head'] is None or probe['head']['status']!='complete' or probe['coefficients'] is None:
                return dict(status='unassessed',reason=f'{name}_diagnostic_incomplete',variant=variant,
                    shift_available=False,successor_available=False)
            heads[name]=probe['head'];coefficients[name]=probe['coefficients']
    rows,support=project_hazards(design,heads,coefficients)
    nuisance=smooth_nuisance(design.nuisance)
    if not all(heads[name]['status']=='complete' for name in HEADS) or nuisance['status']!='complete':
        return dict(status='unavailable',reason='incomplete_movement_or_shift_reference',variant=variant,
            shift_available=False,successor_available=False,hazards=rows,support=support,nuisance=nuisance)
    neutral_hazards=[]
    for name in ('exit','entry','exit','entry'):
        neutral_hazards.append(center_head(design,design.heads[name],coefficients[name],heads[name]['reference']['log_rate'])[1]['neutral_per_second'])
    process=lambda hazards:shift_process(movement_generator(hazards),nuisance['w'],nuisance['d'],nuisance['h'],nuisance['R'],nuisance['initial_zone_probabilities'])
    try:
        neutral=process(neutral_hazards)
    except (InputContractError,FloatingPointError,OverflowError,ValueError,np.linalg.LinAlgError) as error:
        return dict(status='unavailable',reason=f'neutral_shift_process_invalid:{type(error).__name__}:{error}',variant=variant,
            shift_available=False,successor_available=False,hazards=rows,support=support,nuisance=nuisance)
    reference=None;reason='successor_panel_unavailable'
    if successor_panel is not None:
        try:
            reference=successor_reference(neutral,successor_panel);reason=None
        except (InputContractError,FloatingPointError,OverflowError,ValueError) as error:
            reason=f'successor_panel_invalid:{type(error).__name__}:{error}'
    shift_values=[]
    order=('exit_offense','entry_offense','zone_retention','entry_prevention')
    for row in rows:
        try:
            focal=process([row['roles'][role]['hazard_per_second'] for role in order])
        except (InputContractError,FloatingPointError,OverflowError,ValueError,np.linalg.LinAlgError) as error:
            return dict(status='unavailable',reason=f"focal_shift_process_invalid:{row['player_id']}:{type(error).__name__}:{error}",variant=variant,
                shift_available=False,successor_available=False,hazards=rows,support=support,nuisance=nuisance)
        shift_values.append(dict(player_id=row['player_id'],season=design.season,end_probabilities=focal['end_probabilities'],
            end_probability_difference=np.asarray(focal['end_probabilities'])-np.asarray(neutral['end_probabilities'])))
    values=shift_values
    if reference is not None:
        projected=[]
        try:
            for row in shift_values:
                projected.append(dict(player_id=row['player_id'],season=design.season,
                    **successor_value(neutral,row,reference)))
            values=projected
        except (InputContractError,FloatingPointError,OverflowError,ValueError) as error:
            reference=None;reason=f"successor_value_invalid:{row['player_id']}:{type(error).__name__}:{error}"
    return dict(status='complete' if reference is not None else 'unavailable',reason=reason,variant=variant,
        shift_available=True,successor_available=reference is not None,hazards=rows,support=support,nuisance=nuisance,
        neutral=neutral,successor_reference=reference,values=values)


def compare_territory_variants(state,baseline,variant):
    if baseline['status']!='complete' or variant['status']!='complete':
        return dict(status='unassessed',reason='baseline_or_diagnostic_incomplete',hazard_per_hour=None,
            probability=None,value_goals=None,map_l1_goals=None,mean_shift_seconds=None,tail_time_fraction=None)
    hazards=[];probabilities=[]
    for name in HEADS:
        if variant['variant'] not in (name,'joint'):continue
        head=state.design.heads[name];probe=state.probes[name]
        for kind in ('time','event'):
            before=np.exp(state.heads[name]['reference']['log_rate']+scalar_predictor(head,state.coefficients[name],kind))
            after=np.exp(probe['head']['reference']['log_rate']+scalar_predictor(head,probe['coefficients'],kind))
            hazards.extend(3600*abs(before-after));probabilities.extend(abs(np.exp(-before)-np.exp(-after)))
    for left,right in zip(baseline['hazards'],variant['hazards'],strict=True):
        require(left['player_id']==right['player_id'],'diagnostic hazard player axis differs')
        for role in ROLES:
            hazards.append(3600*abs(left['roles'][role]['hazard_per_second']-right['roles'][role]['hazard_per_second']))
            probabilities.append(abs(left['roles'][role]['one_second_probability']-right['roles'][role]['one_second_probability']))
            hazards.append(3600*abs(left['roles'][role]['neutral_hazard_per_second']-right['roles'][role]['neutral_hazard_per_second']))
            probabilities.append(abs(left['roles'][role]['neutral_one_second_probability']-right['roles'][role]['neutral_one_second_probability']))
    values=[];map_l1=[]
    probabilities.extend(abs(np.asarray(baseline['neutral']['end_probabilities'])-np.asarray(variant['neutral']['end_probabilities'])))
    for left,right in zip(baseline['values'],variant['values'],strict=True):
        require(left['player_id']==right['player_id'],'diagnostic value player axis differs')
        probabilities.extend(abs(np.asarray(left['end_probabilities'])-np.asarray(right['end_probabilities'])))
        values.extend(abs(left['values']-right['values']))
        map_l1.extend(fsum(abs(row)) for row in left['maps']-right['maps'])
    maxima=[max(items,default=0.) for items in (hazards,probabilities,values,map_l1)]
    require(all(isfinite(v) for v in maxima),'nonfinite territory diagnostic comparison')
    return dict(status='within_budget' if all(v<=limit for v,limit in zip(maxima,(1e-4,1e-5,1e-3,1e-3),strict=True)) else 'exceeded',
        reason=None,hazard_per_hour=float(maxima[0]),probability=float(maxima[1]),value_goals=float(maxima[2]),map_l1_goals=float(maxima[3]),
        mean_shift_seconds=abs(baseline['neutral']['mean_shift_seconds']-variant['neutral']['mean_shift_seconds']),
        tail_time_fraction=abs(baseline['neutral']['tail_time_fraction']-variant['neutral']['tail_time_fraction']))
