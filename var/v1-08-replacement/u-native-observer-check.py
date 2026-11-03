"""tiny actual pinned-scipy pairing, partial traces and cap checks."""
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import numpy as np
from hockey_stats import chance
from hockey_stats.execution_design import DEFINITION

spec=importlib.util.spec_from_file_location('u_diagnosis',Path(__file__).with_name('diagnose_execution_u.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
scratch=Path(tempfile.mkdtemp(prefix='u-native-pairing-',dir=Path(__file__).parent))
initial=np.array([.3,-.2,1.])
def objective(x,design=None,actors=None,responsibilities=None,*,addends=None):
    loss=float(np.dot(x*x,np.array([.0013,.0057,.0122]))/2)
    gradient=x*np.array([.0013,.0057,.0122])
    if addends is not None:addends.append(loss)
    return loss,gradient
solver=DEFINITION['solver'];continuation=solver['continuation']
options=dict(maxiter=solver['maxiter'],ftol=continuation['ftol'],gtol=continuation['gtol'])
plain=chance.minimize(lambda x:objective(x),initial,jac=True,method='L-BFGS-B',options=options)
folder=scratch/'native';folder.mkdir()
evaluations=m.Evaluations(folder,objective,limit=256,native_limit=64)
observer=m.NativeObserver(folder,evaluations,initial)
with patch.object(chance,'minimize',observer.minimize),patch.object(m._lbfgsb,'setulb',observer):
    actual=chance.solve_logistic(lambda x:evaluations(x,None,None),initial,**options)
raw=observer.result
assert raw is not None and len(observer.trials)>0 and observer.callbacks>0
assert m.same_bits(raw.x,plain.x) and m.same_bits(raw.jac,plain.jac) and m.same_bits(raw.fun,plain.fun)
assert raw.nfev==plain.nfev and raw.nit==plain.nit and raw.status==plain.status
for trial in observer.trials:
    response=evaluations.calls[trial['response']]
    assert m.same_bits(response['x'],trial['x'])
    assert m.same_bits(trial['native_gtest'],1e-3*trial['gdold'])
    assert m.same_bits(trial['native_finit'],trial['fold'])
    assert np.isclose(trial['gd'],np.dot(response['gradient'],trial['direction']),rtol=1e-14,atol=1e-30)
    assert trial['step']>0
# bound refusal occurs before another evaluation; a failed/nonfinite call remains counted.
folder=scratch/'cap';folder.mkdir()
bounded=m.Evaluations(folder,objective,limit=1,native_limit=64)
bounded(initial,None,None)
try:bounded(initial,None,None)
except m.DiagnosticStop as e:assert str(e)=='full_objective_cap'
else:raise AssertionError('cap ignored')
assert len(bounded.calls)==1
folder=scratch/'nonfinite';folder.mkdir()
def nonfinite(x,d,a,r,*,addends):
    addends.append(float('nan'));return float('nan'),np.zeros_like(x)
failed=m.Evaluations(folder,nonfinite,limit=256,native_limit=64)
try:failed(initial,None,None)
except m.DiagnosticStop:pass
else:raise AssertionError('nonfinite accepted')
assert failed.calls[0]['status']=='nonfinite'
assert json.loads((folder/'evaluation-000/record.json').read_text())['status']=='nonfinite'
# stale response and request mismatch cannot be treated as same-trial evidence.
observer.pending=dict(x=initial+1)
try:observer.evaluated(dict(x=initial))
except m.DiagnosticStop:pass
else:raise AssertionError('stale request accepted')
print(json.dumps(dict(status='passed',plain_and_observed_native_bits_equal=True,
    native_requests=len(observer.events),trials=len(observer.trials),
    full_calls=len(evaluations.calls),scratch=str(scratch))))
first_gradient=evaluations.calls[0]['gradient']
proof=m.gradient_direction_evidence(observer.first_state,initial,first_gradient,observer.first_direction)
assert proof['resolved'] and proof['guards']['cauchy_unit_step']
assert proof['different_from_ideal_coordinates']>0
wrong=observer.first_direction.copy();wrong[0]=np.nextafter(wrong[0],np.inf)
assert not m.gradient_direction_evidence(observer.first_state,initial,first_gradient,wrong)['resolved']
changed={k:v.copy() for k,v in observer.first_state.items()};changed['isave'][29]=1
assert not m.gradient_direction_evidence(changed,initial,first_gradient,observer.first_direction)['resolved']
print('passed: exact pinned cauchy construction; perturbed direction and nonzero iteration refused')
folder=scratch/'native-cap';folder.mkdir()
bounded=m.Evaluations(folder,objective,limit=256,native_limit=64)
bounded.native=True
for i in range(64):bounded(initial,None,None)
try:bounded(initial,None,None)
except m.DiagnosticStop as e:assert str(e)=='full_objective_cap'
else:raise AssertionError('native cap ignored')
assert bounded.native_calls==64 and len(bounded.calls)==64
print('passed: native full-objective cap refuses call65 before evaluation')
