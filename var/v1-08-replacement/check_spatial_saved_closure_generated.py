"""generated controls for saved-checker context closure."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('check',Path(__file__).with_name('verify_real_spatial_compose.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def check(values):
    adjustment={'attempts':dict(zip(m.TERMS.values(),values)),'reason':None}
    data={name:dict(value=value,unavailable_reason=None,reason_detail=None,uncertainty=dict(kind='not_estimated')) for name,value in zip(m.TERMS,values)}
    data['method_id']='m'
    return m.check_context(data,adjustment,'attempts','m',{'source':[]})

assert check([1e8,-1e8,0.,0.,0.,0.,.001]) is False
assert check([3.,1.,2.,-1.,0.,0.,5.]) is False
for values in ([1e8,-1e8,0.,0.,0.,1.,0.],[1e308,1e308,0.,0.,0.,0.,0.]):
    try: check(values)
    except AssertionError: pass
    else: raise AssertionError('out-of-budget or nonfinite arithmetic accepted')
print('generated cancellation, normal, out-of-budget and nonfinite controls passed')
