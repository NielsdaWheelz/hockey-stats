"""saved-output consequence census. no model, design, context or source execution."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

import numpy as np

ROLES=('offense','defense')
QUANTITIES=('attempts','xg')
KINDS=('neutral','complete','difference')
HEADS=('volume','shape','quality')
ROOT=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real')
STATE=ROOT/'spatial/20252026'
EXCHANGE=ROOT/'execution-results'
REPO=Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
DOC=REPO/'docs/research/spatial-v1-08'
PINS={'manifest.json':'c74b313e2ac4ed0b1b8e09787de024b0febe7e98339879a06fb7537ff2398bab',
      'exchange':'3441f784c11eb6a8eda38800806b8e4dc68e06e8587c91db24c5dffaadae4347',
      'audit':'1fd73cf1fdc197a9ae6da87930c4865cb5943a9c8166c056b7b436fc331ac679',
      'policy':'4c0f136c46735f48ef76f8202f75388969d5484947faa33d868718b8ff2b0bbb',
      'scope':'e7be8b277996039e6a675c10a86e5153a564f01e9751f16b25477e8fd8f73b98'}


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(path.read_text())


def lines(path):
    with path.open() as f: return [json.loads(line) for line in f]


def percent_change(difference, neutral):
    return None if neutral==0 else 100*difference/neutral


def normalized(value, extent):
    return np.zeros_like(value) if extent==0 else value/extent


def rho(a,b,d):
    if min(a,b)>0: return d/min(a,b)
    return 0. if a==b==d==0 else None


def pair_bound(triples,view):
    values=[rho(*t) for t in triples]
    return None if any(v is None for v in values) else min(1. if view=='complete' else 2.,2*max(values,default=0.))


def distribution(values,locators):
    v=np.asarray(values,dtype=float)
    assert v.ndim==1 and len(v)==len(locators) and np.isfinite(v).all()
    if not len(v): return dict(count=0)
    a=np.abs(v); k=int(np.argmax(a))
    return dict(count=len(v),signed_min=float(v.min()),signed_median=float(np.median(v)),signed_max=float(v.max()),
                absolute_median=float(np.median(a)),absolute_p90=float(np.quantile(a,.9,method='linear')),
                absolute_p99=float(np.quantile(a,.99,method='linear')),absolute_max=float(a[k]),maximum_locator=locators[k])


def midpoints(values):
    values=np.asarray(values)
    order=np.argsort(values,kind='stable'); result=np.empty(len(values),dtype=float)
    i=0
    while i<len(values):
        j=i+1
        while j<len(values) and values[order[j]]==values[order[i]]: j+=1
        result[order[i:j]]=100*(i+(j-i)/2)/len(values); i=j
    return result


def reversals(before,after,ids):
    counts=dict(strict_count=0,tie_to_strict_count=0,strict_to_tie_count=0)
    examples=[]
    for i in range(len(ids)):
        for j in range(i+1,len(ids)):
            x=float(before[i]-before[j]);y=float(after[i]-after[j])
            if x*y<0:
                counts['strict_count']+=1
                examples.append(dict(players=[ids[i],ids[j]],baseline_gap=abs(x),probe_gap=abs(y)))
            elif x==0 and y!=0: counts['tie_to_strict_count']+=1
            elif x!=0 and y==0: counts['strict_to_tie_count']+=1
    examples.sort(key=lambda r:(-max(r['baseline_gap'],r['probe_gap']),r['players']))
    return counts|dict(maximum_baseline_gap=max((x['baseline_gap'] for x in examples),default=0.),
                       maximum_probe_gap=max((x['probe_gap'] for x in examples),default=0.),examples=examples[:20])


def check_projection(rows,arr,reference):
    ids=[r['player_id'] for r in rows]
    assert ids==sorted(set(ids)) and arr.shape==(len(ids),2,2,3,656) and arr.dtype==np.float64 and np.isfinite(arr).all()
    assert (arr[:,:,:,0:2]>0).all()
    for i,row in enumerate(rows):
        assert row['season']=='20252026' and row['available'] and row['reason'] is None and row['reference_id']==reference
        assert row['units']=='per_hour' and row['uncertainty']=='not_estimated'
        for ri,role in enumerate(ROLES):
            for qi,q in enumerate(QUANTITIES):
                vals=arr[i,ri,qi].sum(axis=-1); saved=row['values'][role][q]
                for ki,name in enumerate(KINDS):
                    assert abs(vals[ki]-saved[name])<=1e-11*(1+abs(saved[name]))
                p=percent_change(vals[2],vals[0]); assert p is not None and abs(p-saved['relative_percent'])<=1e-11*(1+abs(saved['relative_percent']))
    return ids


def scalar_census(ids,rows0,rows1,public):
    result={}
    for role in ROLES:
        for quantity in QUANTITIES:
            for kind in (*KINDS,'relative_percent'):
                key=f'{role}.{quantity}.{kind}'
                delta=np.array([b['values'][role][quantity][kind]-a['values'][role][quantity][kind] for a,b in zip(rows0,rows1,strict=True)])
                for name,indices in (('fitted',range(len(ids))),('public',[i for i,p in enumerate(ids) if p in public])):
                    indices=list(indices); values=delta[indices]; loc=[ids[i] for i in indices]
                    out=distribution(values,loc)
                    baseline=np.array([rows0[i]['values'][role][quantity][kind] for i in indices])
                    continuation=np.array([rows1[i]['values'][role][quantity][kind] for i in indices])
                    reference0=np.array([rows0[i]['values'][role][quantity]['neutral'] for i in indices])
                    reference1=np.array([rows1[i]['values'][role][quantity]['neutral'] for i in indices])
                    out['baseline_values']=distribution(baseline,loc)
                    out['probe_values']=distribution(continuation,loc)
                    out['baseline_reference_per_hour']=distribution(reference0,loc)
                    out['probe_reference_per_hour']=distribution(reference1,loc)
                    if indices:
                        k=int(np.argmax(np.abs(values)));i=indices[k]
                        out['maximum_change_context']=dict(player_id=ids[i],baseline=rows0[i]['values'][role][quantity],probe=rows1[i]['values'][role][quantity])
                    if kind!='relative_percent': out['per_1000_minutes']=distribution(values*(1000/60),loc)
                    result[f'{name}.{key}']=out
    return result


def cohorts(ids,rows0,rows1,public):
    out={}
    for cutoff in (0,300):
        for position,positions in (('f',('C','L','R','F')),('d',('D',))):
            indices=[i for i,p in enumerate(ids) if p in public and public[p]['reported_position'] in positions
                     and rows0[i]['support']['included_seconds'] is not None and rows0[i]['support']['included_seconds']>0
                     and rows0[i]['support']['included_seconds']>=cutoff*60]
            member_ids=[ids[i] for i in indices]
            for role in ROLES:
                for q in QUANTITIES:
                    for kind in ('difference','relative_percent'):
                        a=np.array([rows0[i]['values'][role][q][kind] for i in indices]);b=np.array([rows1[i]['values'][role][q][kind] for i in indices])
                        ranks0=midpoints(a);ranks1=midpoints(b)
                        out[f'{cutoff}.{position}.{role}.{q}.{kind}']=dict(members=member_ids,percentile_movement=distribution(ranks1-ranks0,member_ids),
                            standings=[dict(player_id=p,baseline=float(x),probe=float(y)) for p,x,y in zip(member_ids,ranks0,ranks1,strict=True)],
                            order=reversals(a,b,member_ids))
    return out


def categories(ids,rows,support,public,selected):
    eligible=[p for p in ids if p in public]; byid={r['player_id']:r for r in rows}
    def seconds(p): return byid[p]['support']['included_seconds']
    regular=[p for p in eligible if seconds(p) is not None and seconds(p)>=18000]
    low=sorted((seconds(p),p) for p in eligible if seconds(p) is not None and 0<seconds(p)<18000)
    prior=[p for p in eligible if seconds(p)==0 and byid[p]['support']['prior_only']]
    entrant=[]
    for p in eligible:
        s=[r for r in support if r['player_id']==p]
        if len(s)==6 and {(r['role'],r['head']) for r in s}=={(r,h) for r in ROLES for h in HEADS} and all(r['available'] and r['prior_kind']=='entry' for r in s): entrant.append(p)
    traded=[]
    for row in selected:
        p=row['player_id']
        if 'trades' in row['requirements'] and p in public and p in byid and len({x['id'] for x in public[p]['teams']})>=2:
            k=row['key']; key=(k['game_id'],k['segment_index'],k['chunk_index'],-1 if k['source_index'] is None else k['source_index'],row['role'],p)
            traded.append((p,key))
    return dict(regular=min(regular,default=None),low_time=low[0][1] if low else None,prior_only=min(prior,default=None),
                entrant=min(entrant,default=None),traded=min(traded)[0] if traded else None)


class MapLocators:
    def __init__(self,ids,indices,geometry): self.ids,self.indices,self.geometry=ids,indices,geometry
    def __len__(self): return len(self.indices)*2*668
    def __getitem__(self,index):
        player,rem=divmod(index,2*668); role,cell=divmod(rem,668)
        return dict(player_id=self.ids[self.indices[player]],role=ROLES[role],cell_id=self.geometry[cell]['cell_id'])


def map_census(ids,base,probe,public,geometry,transport):
    area=np.array([r['area_sqft'] for r in geometry]); data={}; summaries={}; pairs={}
    indices=[i for i,p in enumerate(ids) if p in public]
    for qi,q in enumerate(QUANTITIES):
        for ki,view in ((1,'complete'),(2,'effect')):
            # matrix multiplication uses the same fixed mass transport for every native map.
            x=base[:,:,qi,ki]@transport.T; y=probe[:,:,qi,ki]@transport.T
            assert np.allclose(x.sum(axis=-1),base[:,:,qi,ki].sum(axis=-1),rtol=1e-11,atol=1e-11)
            assert np.allclose(y.sum(axis=-1),probe[:,:,qi,ki].sum(axis=-1),rtol=1e-11,atol=1e-11)
            xd=100*x/area;yd=100*y/area
            a=np.max(np.abs(xd),axis=(1,2));b=np.max(np.abs(yd),axis=(1,2));d=np.max(np.abs(yd-xd),axis=(1,2))
            xn=np.divide(xd,a[:,None,None],out=np.zeros_like(xd),where=a[:,None,None]!=0)
            yn=np.divide(yd,b[:,None,None],out=np.zeros_like(yd),where=b[:,None,None]!=0)
            norm=yn-xn; data[q,view]=dict(x=xd,y=yd,delta=yd-xd,mass_delta=y-x,norm=norm,a=a,b=b,d=d)
            for name,which in (('fitted',list(range(len(ids)))),('public',indices)):
                loc=MapLocators(ids,which,geometry)
                density=(yd-xd)[which].ravel();mass=(y-x)[which].ravel(); normalized_delta=norm[which].ravel()
                triples=[(a[i],b[i],d[i]) for i in which]
                old=xd[which];new=yd[which]
                signs=dict(positive_to_negative=int(np.count_nonzero((old>0)&(new<0))),
                    negative_to_positive=int(np.count_nonzero((old<0)&(new>0))),
                    zero_to_positive=int(np.count_nonzero((old==0)&(new>0))),
                    zero_to_negative=int(np.count_nonzero((old==0)&(new<0))),
                    positive_to_zero=int(np.count_nonzero((old>0)&(new==0))),
                    negative_to_zero=int(np.count_nonzero((old<0)&(new==0))))
                summaries[f'{name}.{q}.{view}']=dict(density=distribution(density,loc),mass=distribution(mass,loc),normalized=distribution(normalized_delta,loc),sign_transitions=signs,
                    normalized_pair_bound=pair_bound(triples,view),trivial_range_bound=1. if view=='complete' else 2.,
                    undefined_rho=[ids[i] for i in which if rho(a[i],b[i],d[i]) is None])
            if len(indices)>=2:
                primary=min(indices,key=lambda i:(0 if rho(a[i],b[i],d[i]) is None else 1, -(rho(a[i],b[i],d[i]) or 0),ids[i]))
                others=[i for i in indices if i!=primary];positive=[i for i in others if max(a[i],b[i])>0]
                partner=min(positive,key=lambda i:(max(a[i],b[i]),ids[i])) if positive else min(others,key=lambda i:ids[i])
                A=max(a[primary],a[partner]);B=max(b[primary],b[partner])
                change=normalized(yd[[primary,partner]],B)-normalized(xd[[primary,partner]],A)
                pairs[f'{q}.{view}']=dict(players=[ids[primary],ids[partner]],baseline_scale=float(A),probe_scale=float(B),
                    max_normalized_movement=float(np.max(np.abs(change))))
            else: pairs[f'{q}.{view}']=None
    return data,summaries,pairs


def select_figures(ids,public,data,geometry,comparison):
    cases=[]
    def rankcase(q,v,metric):
        z=np.abs(data[q,v][metric]); candidates=[]
        for i,p in enumerate(ids):
            if p not in public: continue
            for ri in range(2):
                c=int(np.argmax(z[i,ri]));candidates.append((-float(z[i,ri,c]),p,ri,QUANTITIES.index(q),('complete','effect').index(v),geometry[c]['cell_id'],i,q,v))
        return min(candidates) if candidates else None
    def append_case(c,reason):
        if c is None: return
        _,p,ri,_,_,cell,i,q,v=c
        identity=(p,ri,q,v)
        if identity not in [(z['player_id'],z['role_index'],z['quantity'],z['view']) for z in cases]:
            cases.append(dict(player_id=p,index=i,role_index=ri,quantity=q,view=v,cell_id=cell,selection=reason,published=p in public))
        else:
            next(z for z in cases if (z['player_id'],z['role_index'],z['quantity'],z['view'])==identity)['selection']+='; '+reason
    for q in QUANTITIES:
        for view in ('complete','effect'):
            append_case(rankcase(q,view,'delta'),f'worst published {q} {view} delta')
    for view in ('complete','effect'):
        entries=[rankcase(q,view,'norm') for q in QUANTITIES]; entries=[x for x in entries if x is not None]
        append_case(min(entries) if entries else None,f'worst published {view} norm')
    for qi,q in enumerate(QUANTITIES):
        entries=[];a=data[q,'effect']['a'];b=data[q,'effect']['b']
        for i,p in enumerate(ids):
            extent=max(a[i],b[i])
            if p in public and extent>0: entries.append((float(extent),p,0,qi,1,geometry[0]['cell_id'],i,q,'effect'))
        append_case(min(entries) if entries else None,f'smallest positive {q} effect extent')
    loc=comparison['maxima']['standardized_scalar_per_hour']['locator'];p=loc['player_id'];i=ids.index(p)
    # a neutral maximum is visualized as the corresponding complete map, with the locator disclosed.
    view='effect' if loc['kind']=='difference' else 'complete'
    append_case((0.,p,ROLES.index(loc['role']),QUANTITIES.index(loc['quantity']),('complete','effect').index(view),geometry[0]['cell_id'],i,loc['quantity'],view),'original scalar failure '+json.dumps(loc,sort_keys=True))
    assert len(cases)<=9
    return cases


def render(cases,data,geometry,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle,FancyBboxPatch
    from matplotlib.collections import PatchCollection
    from matplotlib.colors import Normalize
    plots=[]
    patches=[Rectangle((r['y_min']+42.5,100-r['x_max']),r['y_max']-r['y_min'],r['x_max']-r['x_min']) for r in geometry]
    for number,case in enumerate(cases,1):
        z=data[case['quantity'],case['view']]; i=case['index'];ri=case['role_index'];x=z['x'][i,ri];y=z['y'][i,ri];delta=y-x
        A=float(z['a'][i]);B=float(z['b'][i]);D=float(np.max(np.abs(delta)))
        fig,axes=plt.subplots(1,5,figsize=(15,6),constrained_layout=True)
        for ax,values,extent,title,is_delta in zip(axes,(x,y,x,y,delta),(A,A,A,B,D),('baseline / common','probe / common','baseline / auto','probe / auto','probe − baseline'),(False,False,False,False,True),strict=True):
            e=extent if extent>0 else 1.;signed=case['view']=='effect' or is_delta
            norm=Normalize(vmin=-e if signed else 0,vmax=e,clip=True)
            collection=PatchCollection(patches,cmap='bwr' if signed else 'viridis',norm=norm,edgecolor='none');collection.set_array(values)
            ax.add_collection(collection);clip=FancyBboxPatch((0,0),85,200,boxstyle='round,pad=0,rounding_size=28',transform=ax.transData);collection.set_clip_path(clip)
            ax.set_xlim(0,85);ax.set_ylim(200,0);ax.set_aspect('equal');ax.axis('off')
            overflow=bool(np.any(np.abs(values)>extent)) if signed else bool(np.any(values>extent))
            ax.set_title(title+('\noverflow clipped' if overflow else '')+f'\nscale {extent:.8g}',fontsize=8)
            fig.colorbar(collection,ax=ax,shrink=.5,label='per 60 per 100 sq ft')
        fig.suptitle(f"{case['player_id']} / {ROLES[ri]} / {case['quantity']} / {case['view']}\nstudy palette; not an app renderer",fontsize=10)
        paths=[]
        for suffix in ('png','svg'):
            path=out/f'case-{number:02d}.{suffix}';fig.savefig(path,dpi=150);paths.append(dict(path=str(path),sha256=sha(path)))
        plt.close(fig);plots.append(case|dict(files=paths))
    return plots


def run(out):
    started=time.perf_counter();bound=[]
    def bind(path,expected):
        got=sha(path);assert got==expected, f'hash mismatch: {path}'
        bound.append(dict(path=str(path),sha256=got,bytes=path.stat().st_size))
    def file(path,expected):
        bind(path,expected);return load(path)
    bind(DOC/'experimental-use-policy.md',PINS['policy']);bind(DOC/'experimental-use-consequence-review.md',PINS['scope'])
    bind(DOC/'reviews/experimental-use-policy-review.md','84141a218c18320586d0578b9add6f2a73a27aec04f7555a6dc459a4e9c24495')
    manifest=file(STATE/'manifest.json',PINS['manifest.json']);members={x['path']:x for x in manifest['files']};assert len(members)==len(manifest['files'])
    def member(name,reader=load):
        path=STATE/name;bind(path,members[name]['sha256']);return reader(path)
    descriptor=member('probes/baseline.json')
    annual=member('annual-baseline-manifest.json');assert members['annual-baseline-manifest.json']['sha256']=='8ed907e6034945af251b05cbc28c1fd6a1c5b08315a0c520fc2efd80ffd2257f';assert all(annual[k]==manifest[k] for k in manifest if k not in ('files','resources'))
    assert all(x in manifest['files'] for x in annual['files'])
    reference=member('reference.json');heads={h:member(f'heads/{h}.json') for h in HEADS}
    changed_head=member('probes/volume.json');assert all(x['status']=='complete' for x in [*heads.values(),changed_head])
    comparisons={h:member(f'probes/{h}-comparison.json') for h in HEADS}
    selection=member('probes/rows.json');requirements=member('probes/requirements.json')
    support=member('coefficient-support.jsonl',lines)
    rows0=member('projections.jsonl',lines);rows1=member('probes/volume-projections.jsonl',lines)
    exchange=file(EXCHANGE/'manifest.json',PINS['exchange']);people_member=exchange['catalogs']['people'];people_path=EXCHANGE/people_member['path']
    assert not Path(people_member['path']).is_absolute() and '..' not in Path(people_member['path']).parts
    bind(people_path,people_member['sha256']);people=lines(people_path);assert len(people)==people_member['rows']
    public_rows=[p for p in people if p['season']=='20252026' and p['kind']=='skater'];public={p['player_id']:p for p in public_rows};assert len(public)==len(public_rows)
    audit=file(ROOT/'independent-final-spatial-probes-01/audit.json',PINS['audit'])
    assert audit['manifest']['sha256']==PINS['manifest.json'] and audit['bound_checks_passed'] and not audit['numerical_budgets_passed']
    goals={}
    for h in HEADS:
        c=comparisons[h]['maxima']['prospective_1000_minute_goals'];a=audit['probes'][h]['comparison']['maxima']['prospective_1000_minute_goals']
        assert c==a['canonical']==a['independent'] and c['limit']==.001 and c['value']<=.001
        goals[h]=c
    assert comparisons['volume']['status']=='failed' and comparisons['volume']['maxima']['standardized_scalar_per_hour']['value']>1e-4
    assert comparisons['volume']['maxima']['standardized_scalar_per_hour']==audit['probes']['volume']['comparison']['maxima']['standardized_scalar_per_hour']['canonical']
    # only the rates member is inflated; the original projection archive is not hashed.
    with np.load(STATE/'projections.npz',allow_pickle=False) as archive: base=archive['rates']
    probe_path=STATE/'probes/volume-projections.npz';bind(probe_path,members['probes/volume-projections.npz']['sha256'])
    with np.load(probe_path,allow_pickle=False) as archive:
        assert archive.files==['rates'];probe=archive['rates']
    variant=dict(reference);variant['heads']=dict(reference['heads']);variant['heads']['volume']=dict(reference['heads']['volume'])|dict(centers=changed_head['centers'],predictor=changed_head['reference_predictor'])
    variant.pop('sha256');variant_id=hashlib.sha256(json.dumps(variant,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    ref_id=hashlib.sha256(json.dumps({k:v for k,v in reference.items() if k!='sha256'},sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    assert ref_id==reference['sha256'];ids=check_projection(rows0,base,ref_id);assert check_projection(rows1,probe,variant_id)==ids
    assert all(a['support']==b['support'] and a['available']==b['available'] for a,b in zip(rows0,rows1,strict=True))
    own_goal=float(np.max(np.abs((probe[:,:,1,2]-base[:,:,1,2]).sum(axis=-1)*(1000/60))))
    assert own_goal==goals['volume']['value'] and own_goal<=.001
    categories_=categories(ids,rows0,support,public,selection)
    # pure published geometry primitive, not a state reader or model call.
    sys.path.insert(0,str(REPO/'analysis/src'))
    from hockey_stats.observed_spatial import cells,cell_id,pooling
    from hockey_stats.shot_origins import grid
    geometry=cells();ix={c['cell_id']:i for i,c in enumerate(geometry)}
    deposit=np.zeros((668,656))
    for j,(x,y) in enumerate(grid()[0]): deposit[ix[cell_id(float(x),float(y))],j]=1.
    transport=pooling()@deposit
    assert np.allclose(transport.sum(axis=0),1,rtol=0,atol=1e-14)
    data,maps,pairs=map_census(ids,base,probe,public,geometry,transport)
    exclusions={}
    for cutoff in (0,300):
        unavailable=[]
        for i,p in enumerate(ids):
            if p not in public: continue
            sec=rows0[i]['support']['included_seconds']; position=public[p]['reported_position']
            reason=('unknown_position' if position not in ('C','L','R','F','D') else 'missing_exposure' if sec is None else 'no_exposure' if sec<=0 else 'below_cutoff' if sec<cutoff*60 else None)
            if reason: unavailable.append(dict(player_id=p,reason=reason))
        exclusions[str(cutoff)]=unavailable
    figures=render(select_figures(ids,public,data,geometry,comparisons['volume']),data,geometry,out)
    rowidx={p:i for i,p in enumerate(ids)}
    category_rows={name:None if p is None else dict(player_id=p,support=rows0[rowidx[p]]['support'],baseline=rows0[rowidx[p]]['values'],probe=rows1[rowidx[p]]['values']) for name,p in categories_.items()}
    report=dict(status='computed_pending_materiality_review',original_volume_status=comparisons['volume']['status'],original_volume_comparison=comparisons['volume'],
        retained_goal_comparisons=goals,own_volume_1000_minute_max=own_goal,inputs=bound,
        selected_rates=[dict(path=str(STATE/'projections.npz'),member='rates.npy',shape=list(base.shape),dtype=str(base.dtype),sha256=hashlib.sha256(base.tobytes(order='C')).hexdigest(),scope='decompressed array bytes; full archive not rehashed'),
                        dict(path=str(probe_path),member='rates.npy',shape=list(probe.shape),dtype=str(probe.dtype),sha256=hashlib.sha256(probe.tobytes(order='C')).hexdigest(),scope='decompressed array bytes')],
        code=dict(path=__file__,sha256=sha(Path(__file__)),geometry={str(p):sha(p) for p in (REPO/'analysis/src/hockey_stats/observed_spatial.py',REPO/'analysis/src/hockey_stats/shot_origins.py')}),population=dict(fitted=len(ids),public=len(public),intersection=len(set(ids)&set(public)),
            fitted_only=sorted(set(ids)-set(public)),public_only=sorted(set(public)-set(ids))),
        reference=dict(baseline_id=ref_id,probe_id=variant_id,definition={k:v for k,v in reference.items() if k not in ('heads','sha256')}),
        frozen_requirements=requirements,categories=category_rows,cohort_exclusions=exclusions,scalars=scalar_census(ids,rows0,rows1,public),cohorts=cohorts(ids,rows0,rows1,public),
        maps=maps,pairs=pairs,figures=figures,quantile_convention='numpy linear',
        limits=['no production reader, model prediction, objective, gradient, solver, probe, source or context call',
                'baseline full projection archive not rehashed; prior canonical validation owns archive integrity',
                'six actual-context magnitudes retain canonical-only ownership',
                'saved differences do not bound optimizer error or establish scientific quality',
                'standalone study palettes and api scales do not establish a modeled application renderer'],
        resources=dict(wall_seconds=time.perf_counter()-started,peak_resident_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)))
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--expected-source-sha256',required=True);args=parser.parse_args()
    assert sha(Path(__file__))==args.expected_source_sha256
    out=args.out.absolute();assert out.is_relative_to(Path('/Volumes/Expansion/hockey-stats')) and not out.exists()
    out.mkdir(parents=False)
    report=run(out)
    (out/'review.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=report['status'],report=str(out/'review.json'))))


if __name__=='__main__': main()
