"""tiny synthetic history/refusal controls; no saved fixture or real artifact reads."""
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path

import numpy as np

import independent_spatial_history_audit as audit
import independent_first_spatial_audit as first


def row(block,actor,season,value,width,position='F',age=27.):
    return dict(block=block,id=actor,subblock='base',coefficient=[value]*width,season=season,
                position_group=position,age=age,support_seasons=[season])


def synthetic_history(head):
    width=audit.WIDTHS[head];season='20232024';previous_season='20222023'
    # the gap-two/only/absent rows retain old raw anchors, not previous profiled npz.
    anchors=[row('attacking_player','return',previous_season,.5,width,age=28.),
             row('attacking_player','gap2','20212022',.7,width),
             row('defending_player','changed',previous_season,.9,width,position='D',age=28.),
             row('defending_player','missing',previous_season,1.1,width,age=None),
             row('attacking_coach','coach',previous_season,1.3,width,position=None,age=None),
             row('defending_player','only','20212022',1.5,width,position='D'),
             row('attacking_player','absent','20212022',1.7,width)]
    incoming={audit.key(r):r for r in anchors};old_priors=[];old_beta=np.zeros((9,width))
    for i,last in enumerate(anchors,1):
        fresh=last['season']==previous_season
        old_priors.append(dict(**{k:last[k] for k in ('block','id','subblock','position_group','age')},index=i,
                               current_season_information=fresh,prior_seasons=[]))
        old_beta[i]=last['coefficient'] if fresh else np.full(width,123.)
    previous=dict(priors=old_priors,ledger=sorted(anchors,key=audit.key))
    age=np.array([2.,-1.,3.,-2.,4.,-3.,5.,-4.]) if head=='volume' else np.zeros(8)
    entries=[('attacking_player','return','F',29.,True),('attacking_player','gap2','F',29.,True),
             ('defending_player','changed','F',29.,True),('defending_player','missing','F',29.,True),
             ('attacking_coach','coach',None,None,True),('defending_player','only','D',29.,False),
             ('attacking_player','entry','D',29.,True),('attacking_player','entry_only','F',29.,False)]
    beta=np.zeros((10,width));priors=[];ledger=deepcopy(incoming)
    for i,(block,actor,position,now_age,info) in enumerate(entries,1):
        last=incoming.get((block,actor,'base'));player=block.endswith('_player')
        gap=None if last is None else int(season[:4])-int(last['season'][:4])
        precision=(16. if player else 100.) if last is None else (100. if player else 400.)/gap
        scales=[precision*40.]*width
        if head!='shape':scales[0]=precision
        delta=[];indices=[];reason='entry' if last is None else 'age_neutral'
        if head=='volume' and player and last is not None:
            if last['position_group']!=position:reason='missing_or_changed_role'
            elif last['age'] is None:reason='missing_age'
            else:
                z=(now_age-27.)/10.;old=(last['age']-27.)/10.
                delta=[z-old,z*z-old*old]
                start=(0 if block=='attacking_player' else 4)+(0 if position=='F' else 2)
                indices=[start,start+1];reason='age_carry'
        mean=[0.]*width if last is None else last['coefficient']
        conditional=list(mean)
        if indices:conditional[0]+=sum(delta[j]*float(age[indices[j]]) for j in range(2))
        p=dict(block=block,id=actor,subblock='base',index=i,position_group=position,age=now_age,
               included_seconds=3600. if info else 0.,likelihood_events=int(info),eligible_origin_weight=float(info),
               time_incidence=info,event_incidence=info,current_season_information=info,prior_only=not info,
               prior_kind='entry' if last is None else 'carry',prior_anchor_season=None if last is None else last['season'],
               prior_seasons=[] if last is None else last['support_seasons'],last_supported=last,mean=mean,
               precision=scales,age_delta=delta,age_indices=indices,transition_reason=reason,prior_mean=conditional)
        priors.append(p);beta[i]=np.full(width,2.+i) if info else conditional
        if info:ledger[audit.key(p)]=dict(block=block,id=actor,subblock='base',coefficient=beta[i].tolist(),season=season,
                                      position_group=position,age=now_age,support_seasons=p['prior_seasons']+[season])
    curves=None if head!='volume' else dict(reference_age=27.,scale_years=10.,ridge_precision=64.,
        curves=[dict(role=r,position_group=p,coefficients=age[s:s+2].tolist()) for r,p,s in
                [('offense','F',0),('offense','D',2),('defense','F',4),('defense','D',6)]])
    current=dict(priors=priors,ledger=[ledger[k] for k in sorted(ledger)],age_curves=curves)
    if head=='volume':
        assert abs(priors[0]['prior_mean'][0]-.67)<1e-15
        assert abs(priors[1]['prior_mean'][0]-1.06)<1e-15
        assert abs(priors[5]['prior_mean'][0]-2.34)<1e-15
    return current,previous,beta,old_beta,age,head,season,previous_season


history={h:audit.check_history(*synthetic_history(h)) for h in audit.HEADS}
assert history['volume']['carry_gaps']=={'1':4,'2':2} and history['volume']['absent_anchors_retained']==1
assert history['volume']['previous_older_ledger_anchors']==3
refused=[]
for name in ('conditional','packed_age','prior_only_profile','prior_only_ledger','absent_ledger',
             'fresh_raw','incoming_anchor','previous_fresh_raw','gap_precision','changed_role','duplicate'):
    arguments=list(synthetic_history('volume'));current,previous,beta,old_beta=arguments[:4]
    if name=='conditional':current['priors'][0]['prior_mean'][0]+=.01
    elif name=='packed_age':current['age_curves']['curves'][0]['coefficients'][0]+=.01
    elif name=='prior_only_profile':beta[6,0]+=.01
    elif name=='prior_only_ledger':next(r for r in current['ledger'] if r['id']=='only')['season']='20232024'
    elif name=='absent_ledger':current['ledger']=[r for r in current['ledger'] if r['id']!='absent']
    elif name=='fresh_raw':beta[1,0]+=.01
    elif name=='incoming_anchor':current['priors'][0]['last_supported']=dict(current['priors'][0]['last_supported'],age=27.)
    elif name=='previous_fresh_raw':old_beta[1,0]+=.01
    elif name=='gap_precision':current['priors'][1]['precision'][0]=100.
    elif name=='changed_role':current['priors'][2]['transition_reason']='age_carry'
    elif name=='duplicate':current['ledger'].append(deepcopy(current['ledger'][0]))
    try:audit.check_history(*arguments)
    except AssertionError:refused.append(name)
    else:raise AssertionError('corruption accepted: '+name)

# unchanged independent primitive rates, map scale and ordered basis hash.
assert audit.rates is first.rates and audit.compare_rate is first.compare_rate and audit.digest_arrays is first.digest_arrays
basis=np.sqrt(2.)*np.cos(np.pi*(np.arange(656)[:,None]+.5)*np.arange(1,41)[None,:]/656)
reference=dict(annual_offsets=dict(r=100.,pi=[1/656]*656,qbar=[.08]*656),heads={},sha256='synthetic')
heads={};betas={};predictors={};centers={}
for head in audit.HEADS:
    width=audit.WIDTHS[head];beta=np.arange(7*width,dtype=float).reshape(7,width)*1e-4
    priors=[dict(index=i,block=block,id=actor,subblock=sub,included_seconds=seconds,
                 current_season_information=True,prior_only=False,prior_seasons=['20222023'],prior_kind='carry')
            for i,block,actor,sub,seconds in [(1,'attacking_player','10','base',9000.),(2,'attacking_player','20','base',9000.),
                (3,'defending_player','10','base',9000.),(4,'defending_player','20','base',9000.),(5,'attacking_coach','30','shell',1800.)]]
    groups=[('attacking_player','base',[1,2]),('defending_player','base',[3,4]),('attacking_coach','shell',[5])]
    saved_centers=[];vector=np.array([1.,2.5,2.5,2.5,2.5,.5,0.]);ref=vector@beta
    for block,sub,indices in groups:
        weight=5. if len(indices)==2 else .5;mean=beta[indices].mean(axis=0)
        saved_centers.append(dict(block=block,subblock=sub,indices=indices,weight_hours=weight,mean=mean.tolist(),
                                  reference_applicability=weight,reference_offset=(mean*weight).tolist(),reason=None))
    metadata=dict(priors=priors,centers=saved_centers,reference_predictor=ref.tolist())
    reference['heads'][head]=dict(vector=vector.tolist(),predictor=ref.tolist(),centers=saved_centers)
    predictors[head],centers[head],hours=audit.check_reference(metadata,beta,reference,head)
    assert hours==1.;heads[head]=metadata;betas[head]=beta
rows=[];maps=[];neutral=audit.rates(predictors,reference['annual_offsets'],basis)
for player,index in [('10',1),('20',2)]:
    values={};role_maps=[]
    for ri,role in enumerate(audit.ROLES):
        block=('attacking' if ri==0 else 'defending')+'_player';axis=index+ri*2
        focal=audit.rates({h:predictors[h]+betas[h][axis]-centers[h][block,'base'] for h in audit.HEADS},reference['annual_offsets'],basis)
        role_maps.append(np.stack((neutral,focal,focal-neutral),axis=1));values[role]={}
        for qi,q in enumerate(audit.QUANTITIES):
            n=float(neutral[qi].sum());f=float(focal[qi].sum());d=float((focal[qi]-neutral[qi]).sum())
            values[role][q]=dict(neutral=n,complete=f,difference=d,relative_percent=100*d/n)
    maps.append(role_maps)
    rows.append(dict(player_id=player,season='20232024',available=True,reason=None,reference_id='synthetic',units='per_hour',
                     uncertainty='not_estimated',values=values,support=dict(current_season_information=True,prior_only=False,
                     prior_seasons=['20222023'],inferred_inputs=['historical_borrowing'])))
maps=np.asarray(maps);projections=audit.check_projections(heads,betas,predictors,centers,reference,rows,maps,basis,'20232024')
for name in ('center','scalar','native_rate'):
    try:
        if name=='center':
            bad=deepcopy(heads['volume']);bad['centers'][0]['reference_offset'][0]+=.01
            audit.check_reference(bad,betas['volume'],reference,'volume')
        else:
            badrows=deepcopy(rows);badmaps=maps.copy()
            if name=='scalar':badrows[0]['values']['offense']['attempts']['difference']+=.01
            else:badmaps[0,0,0,1,0]+=.01
            audit.check_projections(heads,betas,predictors,centers,reference,badrows,badmaps,basis,'20232024')
    except AssertionError:refused.append(name)
    else:raise AssertionError('corruption accepted: '+name)
print(json.dumps(dict(status='passed',scope='tiny in-memory synthetic history/reference/rates only; no saved fixture/real/source/model read',
    audit_sha256=hashlib.sha256(Path(audit.__file__).read_bytes()).hexdigest(),
    reused_primitives_sha256=hashlib.sha256(Path(first.__file__).read_bytes()).hexdigest(),
    unchanged_rates_source_sha256=hashlib.sha256(inspect.getsource(audit.rates).encode()).hexdigest(),
    history=history,standardized_projections=projections,refusals=refused),indent=2))
