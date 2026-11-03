"""temporary tiny/source-backed u capture controls; no real source or fit."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

import numpy as np

from hockey_stats import execution_design as ed
from hockey_stats.analysis_data import read_prepared
from hockey_stats.captures import InputContractError
from hockey_stats.execution_fit import annual_priors, objective
from hockey_stats.execution_inputs import write_u_bundle, load_u_bundle

HERE = Path(__file__).parent
scratch = Path(tempfile.mkdtemp(prefix='u-input-controls-', dir=HERE))
features = {name: dict(status='available', value=0., kind='numeric', condition='flag:'+name)
            for family in ('recent_geometry', 'off_wing') for name in ed._columns(family)}
predictors = tuple(ed.ExecutionPredictor('tiny:'+str(i), i%6, i%656, i%2==0, i%6==5,
    dict(shooter='1', goalie='2', attacking_coach='a', defending_coach='d'), {},
    (ed.SetterCandidate(None, 'none', .2), ed.SetterCandidate('3', 'skater', .8)),
    dict(features=deepcopy(features), candidate=dict(previous_x=20.+i, previous_y=float(i), hand=1.),
         strength=(5,5,1), attacking_skaters=['1','3'], attacking_goalies=[])) for i in range(16))
labels = [dict(u=float(i%2), q=None, r=None, g=None, observed_setter=-1) for i in range(16)]
head = ed._head_design('u', predictors, labels, {})
ledger = [dict(block='shooter', id='1', coefficient=.3, role=None, age=None)]
actors = annual_priors(head, ledger)
initial = np.linspace(-.03,.04,head['size'],dtype=np.float64)
selector = dict(keys=[p.key for p in predictors[:2]], fixture_witnesses=[dict(key=predictors[2].key, source_key='tiny:0')],
    requirements=[dict(requirement='tiny', key='tiny:0', disposition='actual')], synthetic_geometry=dict(types=list(ed.TYPES), cells=list(range(656))))
metadata = dict(purpose='fixture', season='20252026', incoming_ledger=ledger, source_context_sha256='0'*64,
    source_response_sha256='1'*64, recipe=ed.RECIPE, head_support=head['actors'])
probes = predictors[:3]
path = write_u_bundle(scratch/'bundle', head, actors=actors, initial=initial, metadata=metadata, selector=selector, probes=probes)
loaded = load_u_bundle(path)
assert loaded['metadata'] == metadata and loaded['selector'] == selector
assert [asdict(p) for p in loaded['probes']] == [asdict(p) for p in probes]
assert loaded['actors'] == actors and np.array_equal(loaded['initial'].view(np.uint64),initial.view(np.uint64))
assert loaded['design']['design'] == head['design'] and loaded['design']['keys'] == head['keys']
def same(a,b):
    assert a.dtype==b.dtype and a.shape==b.shape and a.tobytes()==b.tobytes()
def csr_same(a,b):
    assert a.shape==b.shape
    for name in ('data','indices','indptr'):same(getattr(a,name),getattr(b,name))
csr_same(head['fixed_matrix'],loaded['design']['fixed_matrix'])
left=list(head['batches']());right=list(loaded['design']['batches']())
assert len(left)==len(right)>1
for a,b in zip(left,right,strict=True):
    assert list(a)==list(b)
    for key in a:
        if key=='dynamic_matrix':csr_same(a[key],b[key])
        elif isinstance(a[key],np.ndarray):same(a[key],b[key])
        else:assert a[key]==b[key]
for name in ('target','rows','weight','map_indices','native_neighbors','circumstance_indices','age_indices','setter_mean_indices','setter_mean_weights'):
    same(head[name],loaded['design'][name])
for beta in (initial,np.zeros_like(initial),initial*7.):
    a=objective(beta,head,actors);b=objective(beta,loaded['design'],loaded['actors'])
    assert np.float64(a[0]).tobytes()==np.float64(b[0]).tobytes();same(a[1],b[1])
# signed origins/weights and physical batching survive serialization exactly.
assert sum(len(b['row']) for b in left)==8*656+8
assert [b['origin_cell'].tolist() for b in left]==[b['origin_cell'].tolist() for b in right]
# missing/member-digest/type failures use ordinary bound-array validation.
manifest=json.loads(path.read_text())
member=scratch/'bundle'/manifest['batches'][0]['path'];original=member.read_bytes();member.unlink()
try:load_u_bundle(path)
except (InputContractError,OSError):pass
else:raise AssertionError('missing member accepted')
member.write_bytes(original+b'x')
try:load_u_bundle(path)
except InputContractError:pass
else:raise AssertionError('digest mismatch accepted')
member.write_bytes(original)
with np.load(member,allow_pickle=False) as arrays:changed={name:arrays[name] for name in arrays.files}
changed['row']=changed['row'].astype(np.float64)
with member.open('wb') as stream:np.savez(stream,**changed)
manifest['batches'][0]['sha256']=hashlib.sha256(member.read_bytes()).hexdigest()
path.write_text(json.dumps(manifest))
try:load_u_bundle(path)
except InputContractError:pass
else:raise AssertionError('rebound wrong row type accepted')
# source-backed fixture extraction shares one canonical builder and cannot build q/r/g.
prepared=read_prepared('/Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6','fixture')
coaches='/Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json'
original_head=ed._head_design;calls=[]
def only_u(name,*args,**kwargs):
    assert name=='u';calls.append(name);return original_head(name,*args,**kwargs)
with patch.object(ed,'_head_design',only_u):
    selected=ed.prepare_execution(prepared,coaches,ed.RECIPE,'20252026',training_heads=('u',))
assert calls==['u'] and list(selected.heads)==['u']
assert all(name in selected.coverage['heads'] for name in ed.HEADS)
source_head=selected.heads['u'];source_actors=annual_priors(source_head,[])
source_initial=np.linspace(-.01,.01,source_head['size'],dtype=np.float64)
source_path=write_u_bundle(scratch/'source-bundle',source_head,actors=source_actors,initial=source_initial,
    metadata=dict(purpose='fixture',season='20252026',incoming_ledger=[]),selector={},probes=selected.predictors[:2])
source_loaded=load_u_bundle(source_path)
source_before=objective(source_initial,source_head,source_actors)
source_after=objective(source_initial,source_loaded['design'],source_loaded['actors'])
assert np.float64(source_before[0]).tobytes()==np.float64(source_after[0]).tobytes()
same(source_before[1],source_after[1])
for selection in ((),('u','u'),('x',)):
    with patch.object(ed,'read_prepared',side_effect=AssertionError('invalid selection read source')):
        try:ed.prepare_execution(prepared,coaches,ed.RECIPE,'20252026',training_heads=selection)
        except InputContractError:pass
        else:raise AssertionError('invalid training head selection accepted')
print(json.dumps(dict(status='passed',scope='tiny canonical builder/objectives plus nine-game fixture extraction; no real source or native solve',
    batch_sizes=[len(b['row']) for b in left],physical_rows=len(head['target']),dimension=head['size'],
    objective_gradient_bit_equal_points=3,source_backed_roundtrip_objective_gradient_bit_equal=True,fixture_predictors=len(selected.predictors),fixture_training_heads=calls,
    typed_csr_roundtrip=True,frozen_probes_roundtrip=True,missing_digest_type_refusals=True,scratch=str(scratch)),indent=2))
