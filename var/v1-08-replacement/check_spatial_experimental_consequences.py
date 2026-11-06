"""generated controls for saved-only consequence arithmetic."""
import importlib.util
from pathlib import Path
import numpy as np

p = Path(__file__).with_name('review_spatial_experimental_consequences.py')
spec = importlib.util.spec_from_file_location('review', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

assert m.midpoints(np.array([1., 1., 3.])).tolist() == [100/3, 100/3, 500/6]
r = m.reversals(np.array([1., 2., 3., 3.]), np.array([2., 1., 3., 4.]), ['a','b','c','d'])
assert r['strict_count'] == 1 and r['tie_to_strict_count'] == 1 and r['strict_to_tie_count'] == 0
assert r['examples'][0]['baseline_gap'] == 1 and r['examples'][0]['probe_gap'] == 1
assert m.percent_change(4., 2.) == 200.
assert m.percent_change(1., 0.) is None
assert m.normalized(np.array([0., 0.]), 0.).tolist() == [0., 0.]
assert m.rho(0., 0., 0.) == 0. and m.rho(0., 1., 1.) is None
assert m.pair_bound([(2., 3., 1.), (1., 2., 1.)], 'effect') == 2.
assert m.pair_bound([(0., 1., 1.)], 'complete') is None
s=m.distribution(np.array([-4., 0., 1., 3.]), ['a','b','c','d'])
assert s['count']==4 and s['signed_median']==.5 and s['absolute_max']==4. and s['maximum_locator']=='a'
print('generated arithmetic controls passed')

# generated projection rows, real geometry, cohort rules, and standalone figures.
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'analysis/src'))
from hockey_stats.observed_spatial import cells,cell_id,pooling
from hockey_stats.shot_origins import grid
geom=cells(); index={r['cell_id']:i for i,r in enumerate(geom)}
deposit=np.zeros((668,656))
for j,(x,y) in enumerate(grid()[0]): deposit[index[cell_id(float(x),float(y))],j]=1
transport=pooling()@deposit
ids=['1','2','3']; base=np.full((3,2,2,3,656),.001);base[:,:,:,2]=0.
probe=base.copy();probe[0,0,0,1,0]+=.001;probe[0,0,0,2,0]+=.001;probe[1,1,1,1,1]+=.0001;probe[1,1,1,2,1]+=.0001
public={p:dict(reported_position='C',teams=[{'id':'1'}]) for p in ids}
def rows(array,ref):
    out=[]
    for i,p in enumerate(ids):
        values={}
        for ri,role in enumerate(m.ROLES):
            values[role]={}
            for qi,q in enumerate(m.QUANTITIES):
                sums=array[i,ri,qi].sum(axis=-1)
                values[role][q]=dict(zip(m.KINDS,map(float,sums)))|dict(relative_percent=m.percent_change(sums[2],sums[0]))
        out.append(dict(player_id=p,season='20252026',available=True,reason=None,reference_id=ref,units='per_hour',uncertainty='not_estimated',support=dict(included_seconds=[18000,1,0][i],prior_only=i==2),values=values))
    return out
r0=rows(base,'b');r1=rows(probe,'p');assert m.check_projection(r0,base,'b')==ids
cohorts=m.cohorts(ids,r0,r1,public)
assert cohorts['300.f.offense.attempts.difference']['members']==['1']
assert cohorts['0.f.offense.attempts.difference']['members']==['1','2']
assert m.categories(ids,r0,[],public,[])==dict(regular='1',low_time='2',prior_only='3',entrant=None,traded=None)
data,summary,pairs=m.map_census(ids,base,probe,public,geom,transport)
assert summary['public.attempts.complete']['density']['absolute_max']>0
assert summary['public.attempts.effect']['sign_transitions']['zero_to_positive']>0
scalar=m.scalar_census(ids,r0,r1,public)['public.offense.attempts.complete']
assert scalar['maximum_change_context']['player_id']=='1' and scalar['baseline_reference_per_hour']['count']==3
assert pairs['attempts.complete'] is not None
cmp={'maxima':{'standardized_scalar_per_hour':{'locator':dict(player_id='1',role='offense',quantity='attempts',kind='complete')}}}
cases=m.select_figures(ids,public,data,geom,cmp)
assert len(cases)<=9 and any('original scalar failure' in c['selection'] for c in cases)
reasons='; '.join(c['selection'] for c in cases)
for q in m.QUANTITIES:
    for view in ('complete','effect'):
        assert f'worst published {q} {view} delta' in reasons
    assert f'smallest positive {q} effect extent' in reasons
for view in ('complete','effect'):
    assert f'worst published {view} norm' in reasons
with tempfile.TemporaryDirectory() as tmp:
    plots=m.render(cases,data,geom,Path(tmp))
    assert plots and all(Path(f['path']).stat().st_size>0 for p in plots for f in p['files'])
print('generated geometry, cohorts, census and figure controls passed')
