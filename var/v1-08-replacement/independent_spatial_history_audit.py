"""bounded saved-history audit for the four remaining v1-08 real annuals."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import sys
from time import perf_counter

import numpy as np

from independent_first_spatial_audit import (
    HEADS, WIDTHS, ROLES, QUANTITIES, SOLVER, sha, read, json_rows,
    digest_arrays, rates, compare_rate,
)

YEARS=('20222023','20232024','20242025','20252026')
SUPPORT=('included_seconds','likelihood_events','eligible_origin_weight','time_incidence','event_incidence')


def key(row):
    return row['block'],row['id'],row['subblock']


def records(rows):
    result={key(row):row for row in rows}
    assert len(result)==len(rows), 'duplicate actor/subblock'
    return result


def unpack(metadata,flat,head):
    assert flat.dtype==np.dtype('float64') and flat.ndim==1 and np.isfinite(flat).all()
    count=len(flat)-(8 if head=='volume' else 0)
    assert count>0 and count%WIDTHS[head]==0
    beta=flat[:count].reshape(-1,WIDTHS[head])
    age=flat[count:] if head=='volume' else np.zeros(8)
    assert metadata['head']==head and metadata['status']=='complete' and metadata['reasons']==[]
    priors=metadata['priors'];records(priors)
    assert [p['index'] for p in priors]==list(range(1,len(priors)+1)) and len(priors)<len(beta)
    assert all(p['index']<len(beta) for p in priors)
    return beta,age


def check_history(current,previous,beta,old_beta,age,head,season,previous_season):
    """the accepted previous ledger is the induction boundary, including older anchors."""
    incoming=records(previous['ledger']);outgoing=records(current['ledger'])
    old_priors=records(previous['priors']);priors=records(current['priors'])
    for ledger in (incoming,outgoing):
        assert list(ledger)==sorted(ledger), 'ledger order differs'
        for row in ledger.values():
            years=row['support_seasons']
            assert years and years==sorted(set(years)) and years[-1]==row['season']
            assert row['season']<= (previous_season if ledger is incoming else season)
            assert all('20212022'<=year<=row['season'] for year in years)
    old_fresh={k for k,p in old_priors.items() if p['current_season_information']}
    assert {k for k,row in incoming.items() if row['season']==previous_season}==old_fresh
    for k in old_fresh:
        p=old_priors[k];row=incoming[k]
        assert row['coefficient']==old_beta[p['index']].tolist(), 'previous fresh ledger/raw npz differs'
        assert row['position_group']==p['position_group'] and row['age']==p['age']
        assert row['support_seasons']==p['prior_seasons']+[previous_season]
    kinds=Counter();gaps=Counter();transitions=Counter();max_mean_difference=max_age_shift=0.;nonzero_age_means=0
    for k,p in priors.items():
        last=incoming.get(k);player=p['block'].endswith('_player');width=WIDTHS[head]
        assert p['last_supported']==last, 'incoming raw anchor differs'
        seconds,events,mass=(p[n] for n in SUPPORT[:3])
        assert np.isfinite([seconds,events,mass]).all() and seconds>=0 and events>=0 and mass>=0
        assert type(events) is int and p['time_incidence'] is (seconds>0) and p['event_incidence'] is (events>0)
        info=bool((seconds>0 or events>0) if head=='volume' else mass>0)
        assert p['current_season_information'] is info and p['prior_only'] is (not info)
        kind='entry' if last is None else 'carry';gap=None if last is None else int(season[:4])-int(last['season'][:4])
        assert gap is None or gap>0
        assert p['prior_kind']==kind and p['prior_anchor_season']==(None if last is None else last['season'])
        assert p['prior_seasons']==([] if last is None else last['support_seasons'])
        mean=np.zeros(width) if last is None else np.asarray(last['coefficient'])
        assert mean.shape==(width,) and np.isfinite(mean).all() and p['mean']==mean.tolist()
        precision=(16. if player else 100.) if last is None else (100. if player else 400.)/gap
        expected_precision=np.full(width,precision*40.)
        if head!='shape':expected_precision[0]=precision
        assert p['precision']==expected_precision.tolist()
        indices=[];delta=[];reason='entry' if last is None else 'age_neutral'
        if head=='volume' and player and last is not None:
            if p['position_group'] not in ('F','D') or p['position_group']!=last['position_group']:
                reason='missing_or_changed_role'
            elif p['age'] is None or last['age'] is None:reason='missing_age'
            else:
                now=(p['age']-27.)/10.;before=(last['age']-27.)/10.
                delta=[now-before,now*now-before*before]
                start=(0 if p['block']=='attacking_player' else 4)+(0 if p['position_group']=='F' else 2)
                indices=[start,start+1];reason='age_carry'
        assert p['age_indices']==indices and p['age_delta']==delta and p['transition_reason']==reason
        conditional=mean.copy()
        if indices:conditional[0]+=delta[0]*age[indices[0]]+delta[1]*age[indices[1]]
        shift=float(abs(conditional[0]-mean[0]));max_age_shift=max(max_age_shift,shift);nonzero_age_means+=int(shift>0)
        actual=np.asarray(p['prior_mean'])
        assert actual.shape==(width,) and np.isfinite(actual).all()
        assert np.allclose(actual,conditional,rtol=1e-13,atol=1e-13), 'conditional age mean differs'
        max_mean_difference=max(max_mean_difference,float(np.max(abs(actual-conditional))))
        if not info:
            assert np.allclose(beta[p['index']],conditional,rtol=1e-13,atol=1e-13), 'prior-only profile differs'
            assert outgoing.get(k)==last, 'prior-only history advanced'
        else:
            expected=dict(block=p['block'],id=p['id'],subblock=p['subblock'],coefficient=beta[p['index']].tolist(),
                          season=season,position_group=p['position_group'],age=p['age'],support_seasons=p['prior_seasons']+[season])
            assert outgoing.get(k)==expected, 'fresh ledger/raw npz differs'
        kinds[kind]+=1;transitions[reason]+=1
        if gap is not None:gaps[str(gap)]+=1
    supported={k for k,p in priors.items() if p['current_season_information']}
    assert set(outgoing)==set(incoming)|supported
    assert {k for k,row in outgoing.items() if row['season']==season}==supported
    assert all(outgoing[k]==row for k,row in incoming.items() if k not in supported), 'absent/unsupported anchor changed'
    curves=None if head!='volume' else dict(reference_age=27.,scale_years=10.,ridge_precision=64.,
        curves=[dict(role=role,position_group=position,coefficients=age[start:start+2].tolist())
                for role,position,start in (('offense','F',0),('offense','D',2),('defense','F',4),('defense','D',6))])
    assert current['age_curves']==curves, 'packed volume age curves differ'
    return dict(entry_rows=kinds['entry'],carry_rows=kinds['carry'],carry_gaps=dict(gaps),transitions=dict(transitions),
                fresh_supported_rows=len(supported),prior_only_rows=len(priors)-len(supported),
                absent_anchors_retained=sum(k not in priors for k in incoming),
                previous_fresh_npz_rows=len(old_fresh),previous_older_ledger_anchors=len(incoming)-len(old_fresh),
                maximum_conditional_mean_difference=max_mean_difference,maximum_absolute_age_coefficient=float(abs(age).max()),
                nonzero_age_adjusted_means=nonzero_age_means,maximum_absolute_age_mean_shift=max_age_shift)


def check_reference(metadata,beta,reference,head):
    priors=metadata['priors'];width=WIDTHS[head];incidence=np.zeros(len(beta));groups={}
    for p in priors:
        incidence[p['index']]=p['included_seconds']/3600.
        groups.setdefault((p['block'],p['subblock']),[]).append(p['index'])
    attacking=groups['attacking_player','base'];defending=groups['defending_player','base']
    hours=float(incidence[attacking].sum())/5.
    assert hours>0 and np.isclose(incidence[defending].sum()/5.,hours,rtol=1e-12,atol=1e-12)
    vector=incidence/hours;vector[0]=1.;predictor=vector@beta
    centers={};assert len(metadata['centers'])==len(groups)
    for saved,(group,indices) in zip(metadata['centers'],groups.items(),strict=True):
        assert (saved['block'],saved['subblock'])==group and saved['indices']==indices
        weight=float(incidence[indices].sum());mean=(incidence[indices,None]*beta[indices]).sum(axis=0)/weight if weight else np.zeros(width)
        for actual,expected in ((saved['weight_hours'],weight),(saved['mean'],mean),
                                (saved['reference_applicability'],weight/hours),(saved['reference_offset'],mean*(weight/hours))):
            assert np.allclose(actual,expected,rtol=1e-12,atol=1e-12), 'saved center/applicability differs'
        assert saved['reason']==(None if weight else 'zero_applicable_time')
        centers[group]=mean
    assert np.allclose(predictor,metadata['reference_predictor'],rtol=1e-12,atol=1e-12)
    frozen=reference['heads'][head]
    assert frozen['centers']==metadata['centers']
    assert np.allclose(frozen['predictor'],predictor,rtol=1e-12,atol=1e-12)
    assert np.allclose(frozen['vector'],vector,rtol=1e-12,atol=1e-12)
    return predictor,centers,hours


def check_projections(heads,betas,references,centers,reference,rows,saved,basis,season):
    players=[p['id'] for p in heads['volume']['priors'] if p['block']=='attacking_player' and p['subblock']=='base']
    assert players==sorted(set(players)) and [r['player_id'] for r in rows]==players
    assert saved.dtype==np.dtype('float64') and saved.shape==(len(players),2,2,3,656) and np.isfinite(saved).all()
    neutral=rates(references,reference['annual_offsets'],basis);max_map=max_scalar=0.
    by_head={h:records(heads[h]['priors']) for h in HEADS}
    for i,row in enumerate(rows):
        player=players[i]
        assert row['season']==season and row['available'] is True and row['reason'] is None
        assert row['reference_id']==reference['sha256'] and row['units']=='per_hour' and row['uncertainty']=='not_estimated'
        player_priors=[by_head[h][(side+'_player',player,'base')] for h in HEADS for side in ('attacking','defending')]
        support=row['support']
        assert support['current_season_information'] is any(p['current_season_information'] for p in player_priors)
        assert support['prior_only'] is all(p['prior_only'] for p in player_priors)
        assert support['prior_seasons']==sorted({year for p in player_priors for year in p['prior_seasons']})
        if any(p['prior_kind']=='carry' for p in player_priors):assert 'historical_borrowing' in support['inferred_inputs']
        for ri,role in enumerate(ROLES):
            block=('attacking' if role=='offense' else 'defending')+'_player'
            predictors={h:references[h]+betas[h][by_head[h][block,player,'base']['index']]-centers[h][block,'base'] for h in HEADS}
            focal=rates(predictors,reference['annual_offsets'],basis)
            max_map=max(max_map,compare_rate(np.stack((neutral,focal,focal-neutral),axis=1),saved[i,ri]))
            for qi,q in enumerate(QUANTITIES):
                expected=dict(neutral=float(neutral[qi].sum()),complete=float(focal[qi].sum()),difference=float((focal[qi]-neutral[qi]).sum()),
                              relative_percent=float(100*(focal[qi]-neutral[qi]).sum()/neutral[qi].sum()))
                assert set(row['values'][role][q])==set(expected)
                for name,value in expected.items():
                    stored=row['values'][role][q][name]
                    assert np.isfinite(stored) and abs(value-stored)<=1e-11*(1+abs(stored)), 'standardized scalar differs'
                    max_scalar=max(max_scalar,abs(value-stored))
    return dict(players=len(players),roles=2,maximum_native_difference=max_map,maximum_scalar_difference=max_scalar)


def check_input_bindings(manifest,old):
    """common artifact identities are shared; member selections belong to each year."""
    for name in ('prepared','coaches'):
        assert all(manifest[name][field]==old[name][field] for field in ('purpose','path','sha256')), 'common input identity differs'
    for annual in (old,manifest):
        season=annual['season'];prepared=annual['prepared'];coaches=annual['coaches']
        assert prepared['purpose']==coaches['purpose']==annual['purpose']=='real'
        members=prepared['members'];games=coaches['selected_game_ids']
        assert type(members) is list and type(games) is list and bool(games)
        assert len(games)==len(set(games)) and all(gid[:4]+str(int(gid[:4])+1)==season for gid in games), 'duplicate or cross-season selected game'
        keys=[(row['kind'],row['season'],row['game_id']) for row in members]
        expected={('people',season,None)}|{('game',season,gid) for gid in games}
        assert len(keys)==len(set(keys)) and set(keys)==expected, 'annual prepared/coach membership differs'


def audit(root,previous,expected,previous_expected):
    began=perf_counter();assert sha(root/'manifest.json')==expected and sha(previous/'manifest.json')==previous_expected
    manifest=read(root/'manifest.json');old=read(previous/'manifest.json');season=manifest['season']
    assert season in YEARS and old['season']==str(int(season[:4])-1)+season[:4]
    assert manifest['kind']==old['kind']=='spatial_state' and manifest['purpose']==old['purpose']=='real'
    assert manifest['previous']==dict(path=str(previous/'manifest.json'),sha256=previous_expected,season=old['season'],purpose='real',usage='annual')
    assert manifest['recipe']==old['recipe'] and manifest['recipe']['solver']==SOLVER
    assert manifest['recipe']['heads']==list(HEADS) and manifest['recipe']['modes']==40
    assert manifest['basis_identity']==old['basis_identity'] and manifest['valued']['season']==season
    check_input_bindings(manifest,old)
    checked=[]
    def member(folder,document,name,loader):
        wanted=next(r['sha256'] for r in document['files'] if r['path']==name)
        assert sha(folder/name)==wanted
        checked.append(dict(path=str(folder/name),sha256=wanted,bytes=(folder/name).stat().st_size))
        return loader(folder/name)
    def coefficients(path):
        with np.load(path,allow_pickle=False) as z:
            assert z.files==['coefficients'];return z['coefficients']
    reference=member(root,manifest,'reference.json',read)
    assert reference['kind']=='virtual elapsed linear design' and reference['units']=='per_hour' and reference['player_slots_per_role']==5
    assert reference['context']=='all centered non-actor coordinates zero' and reference['basis_identity']==manifest['basis_identity']
    body={k:v for k,v in reference.items() if k!='sha256'}
    assert reference['sha256']==hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    offsets=reference['annual_offsets'];pi=np.asarray(offsets['pi']);qbar=np.asarray(offsets['qbar'])
    assert np.isfinite(offsets['r']) and offsets['r']>0 and pi.shape==qbar.shape==(656,)
    assert np.isfinite(pi).all() and np.isfinite(qbar).all() and np.all(pi>0) and abs(pi.sum()-1)<1e-12 and np.all((qbar>0)&(qbar<1))
    # only these two npy members are read; archive digests remain canonical-validation evidence.
    with np.load(root/'design.npz',allow_pickle=False) as z:basis=z['basis']
    assert basis.dtype==np.dtype('float64') and basis.shape==(656,40) and np.isfinite(basis).all()
    assert digest_arrays({'basis':basis})==manifest['basis_identity']['array_sha256']
    assert np.max(abs(basis.mean(axis=0)))<1e-10 and np.allclose(basis.T@basis/656,np.eye(40),rtol=0,atol=1e-10)
    with np.load(root/'projections.npz',allow_pickle=False) as z:saved=z['rates']
    selected=[dict(path=str(root/name),member=field,array_sha256=digest_arrays({field:value}),archive_sha256=next(r['sha256'] for r in manifest['files'] if r['path']==name),
                   archive_integrity='canonical writer/read validation; this audit reads only the named npy member')
              for name,field,value in [('design.npz','basis',basis),('projections.npz','rates',saved)]]
    heads={};betas={};references={};centers={};history={};hours={};axes=None;support=None
    for head in HEADS:
        current=member(root,manifest,f'heads/{head}.json',read);prior=member(previous,old,f'heads/{head}.json',read)
        flat=member(root,manifest,f'heads/{head}.npz',coefficients);old_flat=member(previous,old,f'heads/{head}.npz',coefficients)
        beta,age=unpack(current,flat,head);old_beta,_=unpack(prior,old_flat,head)
        current_axes=[(p['index'],key(p),p['position_group'],p['age']) for p in current['priors']]
        current_support=[tuple(p[n] for n in SUPPORT) for p in current['priors']]
        if axes is None:axes=current_axes;support=current_support
        assert current_axes==axes and current_support==support and len(beta)==len(reference['heads'][head]['vector'])
        history[head]=check_history(current,prior,beta,old_beta,age,head,season,old['season'])
        references[head],centers[head],hours[head]=check_reference(current,beta,reference,head)
        solver=current['solver'];assert solver['converged'] is True and solver['options']==SOLVER and solver['maxfun']==15000 and solver['maxls']==20
        assert np.isfinite(solver['raw_gradient_inf_norm']) and solver['raw_gradient_inf_norm']>=0
        objective=current['objective'];assert np.isfinite(list(objective.values())).all() and objective['total']==objective['likelihood']+objective['penalty']
        history[head].update(solver=solver,objective=objective)
        heads[head]=current;betas[head]=beta
    assert all(np.isclose(v,hours['volume'],rtol=1e-12,atol=1e-12) for v in hours.values())
    rows=member(root,manifest,'projections.jsonl',lambda path:list(json_rows(path)))
    projection=check_projections(heads,betas,references,centers,reference,rows,saved,basis,season)
    return dict(kind='independent-spatial-annual-saved-history-audit',status='passed_pending_root_acceptance',season=season,
                audit_code_sha256=sha(Path(__file__)),primitive_code_sha256=sha(Path(__file__).with_name('independent_first_spatial_audit.py')),
                manifest=dict(path=str(root/'manifest.json'),sha256=expected),previous=dict(path=str(previous/'manifest.json'),sha256=previous_expected),
                rehashed_small_members=checked,selected_array_members=selected,basis_identity=manifest['basis_identity'],
                history=history,reference=dict(derived_directed_hours=hours['volume'],exposure_owner='saved head included_seconds metadata; source/design reconciliation remains canonical/prior proof'),
                standardized_projections=projection,
                resources=dict(wall_seconds=perf_counter()-began,peak_resident_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)),
                calls=dict(source=0,production_reader=0,production_evaluator=0,objective=0,gradient=0,native_fit=0,probe=0,actual_allocations=0),
                limits=['accepted previous ledger is the raw-history induction boundary; older anchors are not compared to profiled previous npz rows',
                        'only basis/rates npy members read from the two larger archives; whole-archive integrity belongs to canonical validation',
                        'current saved head support/exposure/age facts are inputs; no original design or source reconciliation repeated',
                        'no objective/gradient recomputation, stronger gradient gate, continuation or actual-context allocation'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True);parser.add_argument('--previous',type=Path,required=True)
    parser.add_argument('--expected-manifest-sha256',required=True);parser.add_argument('--expected-previous-manifest-sha256',required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    output=args.out.resolve();assert output.is_relative_to('/Volumes/Expansion/hockey-stats') and not output.exists()
    output.mkdir()
    try:
        report=audit(args.input.resolve(),args.previous.resolve(),args.expected_manifest_sha256,args.expected_previous_manifest_sha256)
        (output/'audit.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        print(json.dumps(dict(status=report['status'],season=report['season'],report=str(output/'audit.json'))))
    except BaseException as error:
        (output/'audit-failure.json').write_text(json.dumps(dict(status='failed',error_type=type(error).__name__,error=str(error)),indent=2)+'\n');raise


if __name__=='__main__':main()
