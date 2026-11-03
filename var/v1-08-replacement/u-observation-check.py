"""temporary controlled checks for the unchanged execution objective boundary."""
import numpy as np
from scipy.sparse import csr_matrix
from hockey_stats.execution_fit import objective

beta=np.array([.3,-.2,.7,.1])
design=dict(head='u',size=4,target=np.array([0.,1.]),
    map_indices=np.array([[1]]*6),native_neighbors=np.empty((0,2),dtype=np.int64),
    circumstance_indices=[2],age_indices=[3],
    fixed_matrix=csr_matrix([[1.,0.,.2,0.],[1.,0.,-.4,0.]]))
batches=[dict(row=np.array([0,1]),weight=np.array([1.,1.]),
    dynamic_matrix=csr_matrix([[0.,1.,0.,0.],[0.,1.,0.,0.]]))]
design['batches']=lambda:iter(batches)
actors=[dict(index=2,mean=.2,precision=4.,age_delta=[.1],age_indices=[3],likelihood_support=1.)]
f,g=objective(beta,design,actors)
terms=[]
observed,gradient=objective(beta,design,actors,addends=terms)
assert np.float64(f).tobytes()==np.float64(observed).tobytes()
assert g.tobytes()==gradient.tobytes()
assert len(terms)==5 and all(isinstance(v,float) for v in terms)
assert terms[-1]>0
print('passed: observational loss/gradient bits and original scalar addends')
# compare with the unchanged source before this observational edit, not merely
# the current implementation with its option disabled.
import subprocess
legacy={}
source=subprocess.check_output(['git','show','9d5c7be:analysis/src/hockey_stats/execution_fit.py'],text=True)
source=source.replace('from .chance import','from hockey_stats.chance import').replace('from .execution_design import','from hockey_stats.execution_design import')
exec(compile(source,'original-execution-fit','exec'),legacy)
for scale in (0.,1.,1e-8,1e4,-1.):
    x=beta*scale
    expected,expected_gradient=legacy['objective'](x,design,actors)
    terms=[]
    actual,actual_gradient=objective(x,design,actors,addends=terms)
    assert np.float64(expected).tobytes()==np.float64(actual).tobytes()
    assert expected_gradient.tobytes()==actual_gradient.tobytes()
print('passed: original source versus observed source loss/full-gradient bits at five scales')
from pathlib import Path
from hockey_stats.execution_inputs import load_u_bundle
bundle=load_u_bundle(Path(__file__).parent/'u-input-controls-qbvjfleq/source-bundle/manifest.json')
for scale in (0.,1.,-.1):
    x=bundle['initial']*scale
    expected,expected_gradient=legacy['objective'](x,bundle['design'],bundle['actors'])
    terms=[]
    actual,actual_gradient=objective(x,bundle['design'],bundle['actors'],addends=terms)
    assert np.float64(expected).tobytes()==np.float64(actual).tobytes()
    assert expected_gradient.tobytes()==actual_gradient.tobytes()
    assert len(terms)==3+sum(bool(a['likelihood_support']) for a in bundle['actors'])+sum(1 for _ in bundle['design']['batches']())
print('passed: reloaded source-backed fixture original/observed loss and full-gradient bits at three scales')
try:objective(beta,dict(design,head='g'),actors,addends=[])
except ValueError as error:assert str(error)=='scalar addend observation requires u'
else:raise AssertionError('unsupported observation head accepted')
