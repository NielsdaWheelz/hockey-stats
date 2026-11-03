"""temporary frozen evidence arithmetic checks; no real inputs."""
import importlib.util
from pathlib import Path
from fractions import Fraction
import numpy as np
spec=importlib.util.spec_from_file_location('u_diagnosis',Path(__file__).with_name('diagnose_execution_u.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.reference([1e16,1.,-1e16])==Fraction(1)
# exact linear slopes produce adjacent resolved windows; biased analytic slopes stop.
points=[dict(D=Fraction(2),R=Fraction(2)) for _ in m.STEPS]
a=m.direction_evidence(points,2.)
assert a['resolved_window']==[1,2] and a['unresolved_window'] is None
assert m.direction_evidence(points,3.)['unresolved_window']==[1,2]
assert m.direction_evidence(points,0.)['unresolved_window']==[1,2]
flat=[dict(D=Fraction(0),R=Fraction(0)) for _ in m.STEPS]
assert m.direction_evidence(flat,0.)['resolved_window'] is None
# strict same-trial original rejection, exact and rounded acceptance, native curvature.
s=100.;r=Fraction.from_float(s);step=1.;gdold=-1e-10
t=r-Fraction(1,2**40)
w=m.trial_evidence(s,r,s,t,step,gdold,0.,True,True)
assert w['positive_witness']
for changes in [dict(displaced=False),dict(associated=False),dict(step=0.),dict(gdold=0.),dict(gd=-1e-10),dict(trial_reference=r)]:
    args=dict(start_loss=s,start_reference=r,trial_loss=s,trial_reference=t,step=step,gdold=gdold,gd=0.,displaced=True,associated=True)
    args.update(changes)
    assert not m.trial_evidence(**args)['positive_witness']
print('passed: rational sum, adjacent windows, defect/flat/zero/wrong association/curvature refusals')
