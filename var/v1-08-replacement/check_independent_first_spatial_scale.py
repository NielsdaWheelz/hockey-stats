"""pure tiny digest/layout and coverage-index controls; no artifact/model reads."""
import ast
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).parent
oldpath=HERE/'independent_first_spatial_audit_fixture_version.py';path=HERE/'independent_first_spatial_audit.py'
oldsource=oldpath.read_text();source=path.read_text()
assert hashlib.sha256(oldsource.encode()).hexdigest()=='da16ddd8d1e272c10d5f23ad9cdfc785760819c856dab06740911cde27a4922e'
oldtree=ast.parse(oldsource);tree=ast.parse(source)
old={n.name:n for n in oldtree.body if isinstance(n,ast.FunctionDef)};new={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
for name in old:
    if name not in ['audit','digest_arrays']:assert ast.dump(old[name])==ast.dump(new[name]),name
# all numerical/reference/projection/allocation statements in audit remain exact.
def numerical_tail(node):
    start=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='target' for x in n.targets))
    # the final adjustment metadata oracle is the only allowed tail change.
    return [ast.dump(n) for n in node.body[start:] if not (isinstance(n,ast.For) and ast.unparse(n.iter)=='enumerate(adjustments)')]
assert numerical_tail(old['audit'])==numerical_tail(new['audit'])
# compile only hash functions and the changed collection/assert statements.
def function(node,env):
    namespace=dict(env);exec(compile(ast.Module(body=[node],type_ignores=[]),'independent-audit-control','exec'),namespace);return namespace[node.name]
old_digest=function(old['digest_arrays'],dict(hashlib=hashlib,json=json));digest=function(new['digest_arrays'],dict(hashlib=hashlib,json=json,np=np))
base=np.arange(120,dtype=np.float64).reshape(4,5,6)
cases={
 'c_float':base,'f_float':np.asfortranarray(base),'noncontiguous':base[:,::2,::-1],
 'negative_stride':base[::-1,::-1,::-1],'scalar':np.array(-0.),'empty_c':np.empty((0,5)),
 'empty_f':np.empty((3,0,2),order='F'),'empty_noncontiguous':base[:0,::2,::-1],
 'integer':np.arange(30,dtype=np.int64).reshape(5,6),'endian_noncontiguous':np.arange(60,dtype='>f8').reshape(6,10).T[::2],
 'float32_f':np.asfortranarray(np.arange(24,dtype=np.float32).reshape(4,6)),
 'bool':np.array([[True,False],[False,True]])[:,::-1],
 'complex_noncontiguous':(np.arange(30)+1j*np.arange(30)).reshape(5,6).T[:,::2],
 'signed_zero_special_bits':np.array([0.,-0.,np.nan,np.inf]),
 'multi_buffer_noncontiguous':np.arange(131074,dtype=np.float64)[::2],
 'multi_buffer_f':np.asfortranarray(np.arange(210000,dtype=np.float64).reshape(3,70000))}
for name,value in cases.items():assert digest({name:value})==old_digest({name:value}),name
assert digest(cases)==old_digest(cases)
assert digest(dict(reversed(list(cases.items()))))==old_digest(dict(reversed(list(cases.items()))))
assert digest(cases)!=digest(dict(reversed(list(cases.items()))))
class NoToBytes(np.ndarray):
    def tobytes(self,*args,**kwargs):raise AssertionError('whole-array tobytes called')
for value in [base,base.T,base[:,::2,::-1]]:digest({'guard':value.view(NoToBytes)})
# verify non-C buffers are bounded; C arrays hash directly through a memoryview.
original_sha=hashlib.sha256;updates=[]
class HashSpy:
    def __init__(self):self.inner=original_sha()
    def update(self,data):
        if isinstance(data,memoryview):updates.append(data.nbytes)
        self.inner.update(data)
    def hexdigest(self):return self.inner.hexdigest()
try:
    hashlib.sha256=HashSpy
    digest({'f':cases['multi_buffer_f'],'s':cases['multi_buffer_noncontiguous']})
finally:hashlib.sha256=original_sha
assert updates and max(updates)<=65536*8

# execute the actual collection statements from the existing single row walk.
audit=new['audit'];walk=next(n for n in audit.body if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple) and [x.id for x in n.target.elts]==['matrix','keys','kind'])
branch=next(n for n in walk.body[0].body if isinstance(n,ast.If) and ast.unparse(n.test)=="kind == 'time'")
def collector_statements(nodes):return [deepcopy(n) for n in nodes if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='add' and 'retained_' in ast.unparse(n)]
collect={'time':compile(ast.Module(body=collector_statements(branch.body),type_ignores=[]),'time-group-control','exec'),'event':compile(ast.Module(body=collector_statements(branch.orelse),type_ignores=[]),'event-group-control','exec')}
coverage_loop=next(n for n in audit.body if isinstance(n,ast.For) and ast.unparse(n.iter)=="coverage['games']")
assertions=[deepcopy(n) for n in coverage_loop.body if isinstance(n,ast.Assert) and 'retained_' in ast.unparse(n)]
assert len(assertions)==3 and all(not any(isinstance(x,(ast.ListComp,ast.SetComp,ast.GeneratorExp)) for x in ast.walk(n)) for n in assertions)
checks=compile(ast.Module(body=assertions,type_ignores=[]),'coverage-refusal-control','exec')
def groups(time,event):
    env=dict(retained_time_segments=defaultdict(set),retained_event_segments=defaultdict(set),retained_event_sources=defaultdict(set))
    for kind,keys in [('time',time),('event',event)]:
        for key in keys:exec(collect[kind],dict(key=key),env)
    return env

time=[dict(game_id='a',segment_index=1),dict(game_id='a',segment_index=1),dict(game_id='b',segment_index=2)]
event=[dict(game_id='a',segment_index=1,source_index=10),dict(game_id='b',segment_index=2,source_index=11)]
env=groups(time,event)
assert dict(env['retained_time_segments'])=={'a':{1},'b':{2}}
assert dict(env['retained_event_segments'])=={'a':{1},'b':{2}}
assert dict(env['retained_event_sources'])=={'a':{10},'b':{11}}
for gid in ['a','b','empty']:
    valid=dict(known_lost_event_source_indices=[11] if gid=='a' else [10])
    exec(checks,dict(set=set),dict(env,gid=gid,excluded={2} if gid=='a' else {1},game=valid))
refusals=[]
for mode,tm,ev,gid,excluded,lost in [
 ('time_segment',time,event,'a',{1},[]),
 ('event_only_segment',[],[dict(game_id='a',segment_index=3,source_index=12)],'a',{3},[]),
 ('retained_known_lost_event',time,event,'a',{2},[10])]:
    try:exec(checks,dict(set=set),dict(groups(tm,ev),gid=gid,excluded=excluded,game=dict(known_lost_event_source_indices=lost)))
    except AssertionError:refusals.append(mode)
    else:raise AssertionError('coverage corruption accepted: '+mode)
# The actual metadata oracle uses expected identity/exposure, never saved reason.
oracle=next(n for n in audit.body if isinstance(n,ast.For) and ast.unparse(n.iter)=='enumerate(adjustments)')
oracle_code=compile(ast.Module(body=[deepcopy(oracle)],type_ignores=[]),'adjustment-oracle-control','exec')
roles=('offense','defense');quantities=('attempts','xg');adjustment_names=('baseline','self','teammates','opponents','coaching_other_context','residual','factual')
rows=[]
for i,player in enumerate(['zero','positive']):
 for r,role in enumerate(roles):
  zero=i==0;rows.append(dict(season='20212022',player_id=player,role=role,map_index=[i,r],available=not zero,reason='no_exposure' if zero else None,exposure_seconds=0. if zero else 10.,**{q:{k:None if zero else 1. for k in adjustment_names} for q in quantities}))
base_projection=np.zeros((2,2,2,7,3));base_projection[1]=1.
actor_index={(side+'_player',player,'base'):i*2+r for i,player in enumerate(['zero','positive']) for r,side in enumerate(['attacking','defending'])}
def validate_oracle(values,projection):
 env=dict(np=np,definition=dict(players=['zero','positive'],season='20212022'),ROLES=roles,QUANTITIES=quantities,ADJUSTMENTS=adjustment_names,by_actor=actor_index,seconds=np.array([0.,0.,10.,10.]),saved_projection=dict(adjustments=projection),adjustments=values,zero=0)
 exec(oracle_code,env);return env['zero']
assert validate_oracle(deepcopy(rows),base_projection.copy())==2
oracle_refusals=[]
for mode in ['mislabeled_zero','positive_unavailable','swapped_identity','duplicate_identity','zero_nonzero_array']:
 values=deepcopy(rows);projection=base_projection.copy()
 if mode=='mislabeled_zero':values[0].update(available=True,reason=None)
 elif mode=='positive_unavailable':values[2].update(available=False,reason='missing')
 elif mode=='swapped_identity':values[0],values[1]=values[1],values[0]
 elif mode=='duplicate_identity':values[1]=deepcopy(values[0])
 else:projection[0,0,0,0,0]=1.
 try:validate_oracle(values,projection)
 except AssertionError:oracle_refusals.append(mode)
 else:raise AssertionError('adjustment corruption accepted: '+mode)
# CSR membership now uses one bounded view per row; verify exact old/new columns.
from scipy.sparse import csr_matrix
matrix=csr_matrix(np.array([[1.,0.,1.,0.],[0.,1.,0.,1.],[1.,1.,0.,0.]]))
for i in range(matrix.shape[0]):
 left,right=matrix.indptr[i:i+2];indices=matrix.indices[left:right]
 assert indices.tobytes()==matrix[i].indices.tobytes() and np.shares_memory(indices,matrix.indices)
assert not any(isinstance(n,ast.Subscript) and ast.unparse(n)=='matrix[i]' for n in ast.walk(walk))
print(json.dumps(dict(status='passed',scope='tiny pure numerical arrays and synthetic key collections only; no fixture/real artifact, source, model or optimizer call',old_fixture_audit_sha256=hashlib.sha256(oldsource.encode()).hexdigest(),audit_sha256=hashlib.sha256(source.encode()).hexdigest(),digest_cases=list(cases),digest_order_and_dtype_shape_bytes_exact=True,no_whole_array_tobytes=True,maximum_noncontiguous_buffer_bytes=max(updates),coverage_groups_separate_games_and_empty_cases=True,coverage_refusals=refusals,csr_membership_one_view_per_row=True,adjustment_oracle_refusals=oracle_refusals,adjustment_oracle_uses_derived_exposure=True,all_other_functions_ast_identical=True,numerical_reference_projection_allocation_statements_ast_identical=True),indent=2))
