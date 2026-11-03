"""temporary raw-native endpoint qualification contract, no objective call."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import numpy as np
spec=importlib.util.spec_from_file_location('u_repair',Path(__file__).with_name('repair_execution_u.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
initial=np.array([0.,2.]);raw=np.array([.1,2.]);completed=raw.copy()
def check(**changes):
    args=dict(native=SimpleNamespace(success=True,status=0,nit=1,fun=9.,jac=np.ones(2),x=raw),
        callbacks=1,accepted_native_iterations=1,initial=initial,completed=completed,
        start_value=10.,endpoint_value=9.)
    args.update(changes)
    return m.endpoint_qualification(**args)
assert check()['passed']
for changes in (
    dict(endpoint_value=10.),dict(endpoint_value=11.),
    dict(native=SimpleNamespace(success=True,status=0,nit=1,fun=9.,jac=np.ones(2),x=initial)),
    dict(completed=initial),dict(callbacks=0),dict(accepted_native_iterations=0),
    dict(native=SimpleNamespace(success=False,status=2,nit=1,fun=9.,jac=np.ones(2),x=raw)),
    dict(native=SimpleNamespace(success=True,status=0,nit=0,fun=9.,jac=np.ones(2),x=raw)),
    dict(completed=np.array([np.nan,2.])),dict(start_value=np.inf),
):assert not check(**changes)['passed'],changes
# a mean-fill-only change cannot turn the unchanged raw endpoint into movement.
native=SimpleNamespace(success=True,status=0,nit=1,fun=9.,jac=np.ones(2),x=initial)
assert not check(native=native,completed=raw)['passed']
print('passed: accepted strict improvement only; flat/worse/zero/fill-only/fill-erased/nonfinite/incomplete/native-observation failures refused')
