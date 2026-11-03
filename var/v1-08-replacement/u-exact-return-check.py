"""temporary exact-u return and frozen penalty/gradient controls."""
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import ast
import json
import subprocess
from unittest.mock import patch

import numpy as np
from scipy.sparse import csr_matrix
from hockey_stats import execution_fit as ef

here=Path(__file__).parent
trace=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/diagnosis')
terms=[np.load(trace/f'evaluation-{i:03d}/addends.npy',allow_pickle=False) for i in (188,190)]
# hash values are independently pinned below with full saved member bytes.
assert sha256((trace/'evaluation-188/addends.npy').read_bytes()).hexdigest()=='ee37262d8ab24eb1ba1b076f9f7bb345d59923a70ae9dbdaac29c179c1979d97'
assert sha256((trace/'evaluation-190/addends.npy').read_bytes()).hexdigest()=='927b09627aed58d7e272c302ca8568028b0a398c234663ed940d204f8597c9e9'
empty=dict(head='u',target=np.empty(0),fixed_matrix=csr_matrix((0,2)),batches=lambda:iter(()))
for values in terms+[np.array([1e16,1.,-1e16]),np.array([1.,2**-53,2**-53])]:
    before=values.tobytes()
    gradient=np.array([.25,-.5])
    def penalty(beta,design,actors,*,addends=None):
        if addends is not None:addends.extend(float(v) for v in values)
        f=0.
        for v in values:f+=float(v)
        return f,gradient.copy()
    expected=float(sum((Fraction.from_float(float(v)) for v in values),Fraction()))
    with patch.object(ef,'penalty',penalty):
        f,g=ef.objective(np.zeros(2),empty,[])
        assert np.float64(f).tobytes()==np.float64(expected).tobytes(),(f.hex(),expected.hex())
        observed=[123.]
        f2,g2=ef.objective(np.zeros(2),empty,[],addends=observed)
    assert np.float64(f2).tobytes()==np.float64(expected).tobytes()
    assert g.tobytes()==gradient.tobytes()==g2.tobytes()
    assert observed[0]==123. and np.array(observed[1:]).tobytes()==values.tobytes()
    assert values.tobytes()==before
print('passed: frozen real baseline/winner addends and cancellation reduce exactly through tiny empty-batch public objective')
# the checked diagnostic penalty and every gradient statement remain unchanged.
source=subprocess.check_output(['git','show','f175e47:analysis/src/hockey_stats/execution_fit.py'],text=True)
current=Path(ef.__file__).read_text()
def functions(text):return {node.name:node for node in ast.parse(text).body if isinstance(node,ast.FunctionDef)}
old,new=functions(source),functions(current)
assert ast.get_source_segment(source,old['penalty'])==ast.get_source_segment(current,new['penalty'])
def gradient_statements(tree):
    return [ast.dump(node) for node in ast.walk(tree) if isinstance(node,(ast.Assign,ast.AugAssign))
            and ('gradient' in ast.unparse(node).split('=')[0] or 'residual' in ast.unparse(node).split('=')[0])]
assert gradient_statements(old['objective'])==gradient_statements(new['objective'])
legacy={}
source=source.replace('from .chance import','from hockey_stats.chance import').replace('from .execution_design import','from hockey_stats.execution_design import')
exec(compile(source,'checked-diagnostic-objective','exec'),legacy)
from hockey_stats.execution_inputs import load_u_bundle
bundle=load_u_bundle(here/'u-capture-fixture-i9lihlc7/inputs/manifest.json')
for scale in (0.,1.,-.1):
    x=bundle['initial']*scale
    original_terms=[];repaired_terms=[]
    _,original_gradient=legacy['objective'](x,bundle['design'],bundle['actors'],addends=original_terms)
    repaired,repaired_gradient=ef.objective(x,bundle['design'],bundle['actors'],addends=repaired_terms)
    assert np.array(original_terms).tobytes()==np.array(repaired_terms).tobytes()
    assert original_gradient.tobytes()==repaired_gradient.tobytes()
    assert np.float64(repaired).tobytes()==np.float64(float(sum((Fraction.from_float(v) for v in original_terms),Fraction()))).tobytes()
print('passed: penalty source/gradient statements unchanged; three source-backed fixture gradient/addend contracts')
# q/r keep the identical binary-loss path without the u reduction.
for head in ('q','r'):
    other=dict(bundle['design'],head=head)
    x=bundle['initial']
    expected,expected_gradient=legacy['objective'](x,other,bundle['actors'])
    actual,actual_gradient=ef.objective(x,other,bundle['actors'])
    assert np.float64(expected).tobytes()==np.float64(actual).tobytes()
    assert expected_gradient.tobytes()==actual_gradient.tobytes()
print('passed: q/r ordinary loss and full-gradient bits unchanged')
