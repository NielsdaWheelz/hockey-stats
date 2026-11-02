"""focused pure native-side binding control; no native, source or artifact call."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

path = Path(__file__).with_name('accept_real_execution_20252026_final_02.py')
spec = importlib.util.spec_from_file_location('native_reporting_check', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
source = dict(path='/synthetic/source-check.json', sha256='0'*64)
start = dict(status=0, termination='synthetic native return', iterations=0, evaluations=21,
             converged=False, objective=2.)
side = dict(kind='temporary-u-continuation-native-result', head='u', purpose='real', season='20252026',
            analysis_tree=module.ANALYSIS, recipe_sha256=module.RECIPE, source_check=source,
            command=['synthetic'], dimension=2,
            requested_solver=dict(method='L-BFGS-B', jac=True, options=dict(maxiter=10000, ftol=1e-16, gtol=1e-7)),
            native_result=dict(success=True, status=0, message=start['termination'], nit=0, nfev=21,
                               fun=1., fun_classification='finite'))
metadata = dict(design=dict(size=2))
report = module.report_native_continuation(side, metadata, start, source, ['synthetic'])
assert report['native_result']['success'] and report['saved_converged'] is False
assert report['native_result']['fun'] != report['saved_recomputed_objective']
nonfinite = deepcopy(side)
nonfinite['native_result'].update(success=False, status=2, fun=None, fun_classification='nan')
assert module.report_native_continuation(nonfinite, metadata, dict(start, status=2), source, ['synthetic'])['native_result']['fun_classification'] == 'nan'
rejected = []
for name, field, value in [('status mismatch', 'status', 1), ('invalid fun classification', 'fun_classification', 'missing')]:
    invalid = deepcopy(side)
    invalid['native_result'][field] = value
    try:
        module.report_native_continuation(invalid, metadata, start, source, ['synthetic'])
    except AssertionError:
        rejected.append(name)
    else:
        raise AssertionError(name)
print(json.dumps(dict(status='passed', helper_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                      scope='focused synthetic native-side binding only; no main, native optimizer, source, campaign artifact, array or strict reader invoked',
                      cases=['raw success true may have saved convergence false', 'native fun differs from recomputed objective', 'nan native fun stays null and separately classified'],
                      rejected=rejected), indent=2))
