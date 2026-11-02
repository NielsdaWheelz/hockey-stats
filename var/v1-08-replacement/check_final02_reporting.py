"""tiny pure reporting controls; no campaign artifacts or strict reader calls."""
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path


path = Path(__file__).with_name('accept_real_execution_20252026_final_02.py')
spec = importlib.util.spec_from_file_location('final02_check', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
tree = ast.parse(path.read_text())
main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
assignment = next(node for node in ast.walk(main) if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == 'numerical_handoff' for target in node.targets))
handoff = compile(ast.Expression(assignment.value), str(path), 'eval')
baseline = dict(path='resolution/baseline.json', sha256='0'*64)
comparison = dict(optimizer_maxiter=10000, optimizer_ftol=1e-16, optimizer_gtol=1e-7,
                  em_maxiter=100, em_relative_tolerance=1e-9, em_responsibility_tolerance=1e-7,
                  coefficient_max_change=0.01, coefficient_l2_change=0.02)
start = dict(name='continuation', deduplicated_to=None, converged=False, inner_solves=[],
             objective=1., gradient_max=.1, objective_trace=[1.], termination='synthetic native failure')
failure = dict(status='failed', baseline=baseline, reasons=['no_completed_start'], comparison=comparison,
               diagnostics=dict(requested_starts=['continuation'], selected_start=None, starts=[start], wall_seconds=.1))
reported = module.report_resolution('u', failure, None, baseline, 1)
assert reported['status'] == 'failed' and not reported['probability_comparison_available']
assert reported['diagnostics']['starts'] == [start]
nonfinite = deepcopy(failure)
nonfinite['comparison'].update(coefficient_max_change=None, coefficient_l2_change=None)
nonfinite['diagnostics']['starts'][0].update(objective=None, gradient_max=None, objective_trace=[])
json.dumps(module.report_resolution('u', nonfinite, None, baseline, 1), allow_nan=False)
passed = dict(status='passed', baseline=baseline, probe=dict(path='resolution/u.json', sha256='1'*64),
              comparison=dict(comparison, maximum_probability_change=1e-6))
probe = dict(usage='numerical_probe', head='u', baseline=baseline, arrays={}, comparison=passed['comparison'],
             metadata=dict(selected_start='continuation', starts=[dict(start, converged=True)]))
complete = module.report_resolution('u', passed, probe, baseline, 1)
coverage_failed = deepcopy(passed)
coverage_failed['status'] = 'failed'
assert module.report_resolution('u', coverage_failed, probe, baseline, 1)['status'] == 'failed'
assert eval(handoff, {}, dict(command_exit=0, probe_heads={head: complete for head in module.HEADS})) == 'passed'
assert eval(handoff, {}, dict(command_exit=1, probe_heads={head: complete for head in module.HEADS})) == 'failed'
assert eval(handoff, {}, dict(command_exit=0, probe_heads=dict(u=reported, q=complete, r=complete, g=complete))) == 'failed'
rejected = []
for name, candidate, count in [('native count mismatch', failure, 2), ('pending resolution', dict(failure, status='pending'), 1)]:
    try:
        module.report_resolution('u', candidate, None, baseline, count)
    except AssertionError:
        rejected.append(name)
    else:
        raise AssertionError(name)
original = path.with_name('accept_real_execution_20252026.py')
assert hashlib.sha256(original.read_bytes()).hexdigest() == '462902780f77787e1b79923abd70ccc4a471b5da7a1b90d55ff7e770e61abb02'
calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
assert sum(isinstance(node.func, ast.Name) and node.func.id == 'read_execution_state' for node in calls) == 1
assert not any(isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
               and node.func.value.id == 'np' and node.func.attr == 'load' for node in calls)
print(json.dumps(dict(status='passed', scope='pure synthetic continuation reporting and the actual handoff expression; no main, campaign artifact, source, array or strict read',
                      cases=['finite native failure retained', 'nullable movement serializes', 'passed probe reported',
                             'failed completed-probe result retained', 'four passes plus exit0 pass',
                             'exit1 remains failed', 'one failed resolution remains failed'],
                      rejected=rejected, historical_helper_unchanged=True, strict_read_call_sites=1, explicit_np_load_call_sites=0), indent=2))
