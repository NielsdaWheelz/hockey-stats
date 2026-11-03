"""tiny complete diagnosis over injected frozen inputs; no source/design pass."""
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import numpy as np
from hockey_stats import execution_fit,execution_inputs,chance,execution_trace
from hockey_stats.execution_design import DEFINITION

spec=importlib.util.spec_from_file_location('u_diagnosis',Path(__file__).with_name('diagnose_execution_u.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
scratch=Path(tempfile.mkdtemp(prefix='u-e2e-',dir=Path(__file__).parent))
manifest=scratch/'manifest.json';manifest.write_text('{}\n')
names=['intercept']+[f'base:orbit:{i}' for i in range(6)]+['circumstance:x','age:x','shooter:x','attacking_coach:x','defending_coach:x','shooter:prior']
size=len(names)
actors=[dict(block=block,index=index,id=str(index),likelihood_support=support,role='F',age=27.)
    for block,index,support in [('shooter',9,1.),('attacking_coach',10,1.),('defending_coach',11,1.),('shooter',12,0.)]]
design=dict(head='u',size=size,design=dict(coefficient_names=names),actors=actors,
    map_indices=np.arange(1,7).reshape(6,1),circumstance_indices=[7],age_indices=[8],
    age_indices_by_block_role={'shooter':{'F':[8]}})
actors=execution_fit.annual_priors(design,[])
initial=np.ones(size)
gradient=np.arange(1,size+1,dtype=np.float64)*m.ANCHOR_GMAX/size
bundle=dict(design=design,actors=actors,initial=initial,metadata=dict(incoming_ledger=[]))

def objective(x,d,a,r=None,*,addends=None):
    delta=x-initial
    f=m.ANCHOR_LOSS+float(np.dot(gradient,delta))+.5*float(np.dot(delta,delta))
    g=gradient+delta
    if addends is not None:addends.append(f)
    return f,g

def continuation(d,ledger,start):
    s=DEFINITION['solver'];c=s['continuation']
    endpoint,result=chance.solve_logistic(lambda x:execution_fit.objective(x,d,actors),start,
        maxiter=s['maxiter'],ftol=c['ftol'],gtol=c['gtol'])
    return dict(endpoints=dict(continuation=endpoint))
with patch.object(execution_inputs,'load_u_bundle',return_value=bundle), \
     patch.object(execution_fit,'objective',objective), \
     patch.object(execution_fit,'continue_head',continuation):
    report=m.diagnose(manifest,scratch/'successful-native-must-stop')
assert report['reason']=='original_failure_unreproduced',report
assert report['status']=='stopped' and not report['eligible_endpoint']
assert report['full_objective_calls']<=256
assert (scratch/'successful-native-must-stop/raw-native-endpoint.npy').exists()
assert (scratch/'successful-native-must-stop/trial-evidence.json').exists()
assert report['full_objective_calls']==len(list((scratch/'successful-native-must-stop').glob('evaluation-*')))
# an anchor failure stops before any native observation.
def wrong(x,d,a,r=None,*,addends):
    addends.append(1.);return 1.,np.ones_like(x)
with patch.object(execution_inputs,'load_u_bundle',return_value=bundle),patch.object(execution_fit,'objective',wrong):
    bad=m.diagnose(manifest,scratch/'bad-anchor')
assert bad['reason']=='reloaded_anchor_mismatch' and bad['full_objective_calls']==1
# a changed identical-input response stops on the first duplicate, before the screen.
calls=[]
def unstable(x,d,a,r=None,*,addends):
    f,g=objective(x,d,a,r,addends=addends)
    if calls:g=g.copy();g[0]=np.nextafter(g[0],np.inf)
    calls.append(1)
    return f,g
with patch.object(execution_inputs,'load_u_bundle',return_value=bundle),patch.object(execution_fit,'objective',unstable):
    bad=m.diagnose(manifest,scratch/'unstable')
assert bad['reason']=='nonrepeatable_objective_gradient_or_addends' and bad['full_objective_calls']==2
print(json.dumps(dict(status='passed',successful_native_refused=True,anchor_failure_refused=True,
    duplicate_gradient_change_refused=True,full_calls=report['full_objective_calls'],scratch=str(scratch))))
from scipy.optimize import OptimizeResult
for mode,movement in [('flat_moving_pass',.01),('zero_motion_pass',0.)]:
    def fake_native(fn,x,**kwargs):
        f,g=fn(x)
        endpoint=x+movement
        kwargs['callback'](endpoint)
        return OptimizeResult(success=True,status=0,nit=1,nfev=1,njev=1,fun=f,
            x=endpoint,jac=g,message='synthetic native pass with flat reported loss')
    with patch.object(execution_inputs,'load_u_bundle',return_value=bundle), \
         patch.object(execution_fit,'objective',objective), \
         patch.object(execution_fit,'continue_head',continuation), \
         patch.object(execution_trace,'chance_minimize',fake_native):
        refused=m.diagnose(manifest,scratch/mode)
    assert refused['reason']=='original_failure_unreproduced' and not refused['eligible_endpoint']
    assert np.array_equal(np.load(scratch/mode/'raw-native-endpoint.npy'),initial+movement)
print('passed: flat-moving and zero-motion native passes remain diagnostic and are refused')
