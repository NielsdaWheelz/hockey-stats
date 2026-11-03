"""temporary explicit diagnostic/repair trace cap policy checks."""
from pathlib import Path
import tempfile
import numpy as np
from hockey_stats.execution_trace import Evaluations,DiagnosticStop
scratch=Path(tempfile.mkdtemp(prefix='u-repair-caps-',dir=Path(__file__).parent))
def objective(x,d,a,r=None,*,addends):
    addends.append(0.);return 0.,np.zeros_like(x)
def observed(name,**kwargs):
    folder=scratch/name;folder.mkdir();return Evaluations(folder,objective,**kwargs)
normal=observed('diagnostic',limit=256,native_limit=64);normal.native=True
for _ in range(64):normal(np.zeros(1),None,None)
try:normal(np.zeros(1),None,None)
except DiagnosticStop:pass
else:raise AssertionError('diagnostic native64 cap changed')
repair=observed('repair',limit=None,native_limit=None);repair.native=True
for _ in range(257):repair(np.zeros(1),None,None)
assert repair.native_calls==257 and len(repair.calls)==257
print('passed: diagnostic native64 remains literal; explicit repair None caps permit calls beyond256/64')
