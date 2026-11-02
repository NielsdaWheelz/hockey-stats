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
assert reported['resolution_evidence'] == 'failed_finite_positive_motion'
zero_motion = deepcopy(failure)
zero_motion['comparison'].update(coefficient_max_change=0., coefficient_l2_change=0.)
zero_motion['diagnostics']['starts'][0]['iterations'] = 0
zero_report = module.report_resolution('u', zero_motion, None, baseline, 1)
assert zero_report['status'] == 'failed' and zero_report['resolution_evidence'] == 'failed_zero_motion_uninformative'
nonfinite = deepcopy(failure)
nonfinite['comparison'].update(coefficient_max_change=None, coefficient_l2_change=None)
nonfinite['diagnostics']['starts'][0].update(objective=None, gradient_max=None, objective_trace=[])
nonfinite_report = module.report_resolution('u', nonfinite, None, baseline, 1)
assert nonfinite_report['resolution_evidence'] == 'failed_movement_unavailable'
json.dumps(nonfinite_report, allow_nan=False)
passed = dict(status='passed', baseline=baseline, probe=dict(path='resolution/u.json', sha256='1'*64),
              comparison=dict(comparison, maximum_probability_change=1e-6))
probe = dict(usage='numerical_probe', head='u', baseline=baseline, arrays={}, comparison=passed['comparison'],
             metadata=dict(selected_start='continuation', starts=[dict(start, converged=True)]))
complete = module.report_resolution('u', passed, probe, baseline, 1)
passed_zero, zero_probe = deepcopy(passed), deepcopy(probe)
passed_zero['comparison'].update(coefficient_max_change=0., coefficient_l2_change=0., maximum_probability_change=0.)
zero_probe['comparison'] = passed_zero['comparison']
zero_probe['metadata']['starts'][0]['iterations'] = 0
passed_zero_report = module.report_resolution('u', passed_zero, zero_probe, baseline, 1)
assert passed_zero_report['status'] == 'passed' and passed_zero_report['resolution_evidence'] == 'passed_zero_motion_uninformative'
assert passed_zero_report['uninformative_pass_requires_root_decision']
assert eval(handoff, {}, dict(command_exit=0, probe_heads=dict(u=passed_zero_report, q=complete, r=complete, g=complete))) == 'passed'
coverage_failed = deepcopy(passed)
coverage_failed['status'] = 'failed'
assert module.report_resolution('u', coverage_failed, probe, baseline, 1)['status'] == 'failed'
assert eval(handoff, {}, dict(command_exit=0, probe_heads={head: complete for head in module.HEADS})) == 'passed'
assert eval(handoff, {}, dict(command_exit=1, probe_heads={head: complete for head in module.HEADS})) == 'failed'
assert eval(handoff, {}, dict(command_exit=0, probe_heads=dict(u=reported, q=complete, r=complete, g=complete))) == 'failed'
assert eval(handoff, {}, dict(command_exit=0, probe_heads=dict(u=zero_report, q=complete, r=complete, g=complete))) == 'failed'
rejected = []
for name, candidate, count in [('native count mismatch', failure, 2), ('pending resolution', dict(failure, status='pending'), 1)]:
    try:
        module.report_resolution('u', candidate, None, baseline, count)
    except AssertionError:
        rejected.append(name)
    else:
        raise AssertionError(name)
source_reference = dict(path='/synthetic/source-check.json', sha256='2'*64)
baseline_starts = [dict(start, name=name, converged=True) for name in ('zero', 'prior_mean')]
baseline_metadata = dict(design=dict(size=2), starts=baseline_starts)
side = dict(kind='temporary-u-baseline-start-gap', head='u', purpose='real', season='20252026',
            analysis_tree=module.ANALYSIS, recipe_sha256=module.RECIPE, source_check=source_reference,
            command=['synthetic'], dimension=2, endpoint_order=['zero', 'prior_mean'],
            starts=[{key: row[key] for key in ('name', 'converged', 'deduplicated_to', 'objective')} for row in baseline_starts],
            availability='available', reason=None, coefficient_max_change=0., coefficient_l2_change=0.)
assert module.report_baseline_gap(side, baseline_metadata, source_reference, ['synthetic'])['availability'] == 'available'
side_unavailable, incomplete_metadata = deepcopy(side), deepcopy(baseline_metadata)
side_unavailable.update(availability='unavailable', reason='incomplete_or_deduplicated_start', coefficient_max_change=None, coefficient_l2_change=None)
side_unavailable['starts'][1]['converged'] = False
incomplete_metadata['starts'][1]['converged'] = False
assert module.report_baseline_gap(side_unavailable, incomplete_metadata, source_reference, ['synthetic'])['availability'] == 'unavailable'
try:
    module.report_baseline_gap(side, baseline_metadata, dict(source_reference, sha256='3'*64), ['synthetic'])
except AssertionError:
    rejected.append('side report source identity mismatch')
else:
    raise AssertionError('side source identity mismatch accepted')
original = path.with_name('accept_real_execution_20252026.py')
assert hashlib.sha256(original.read_bytes()).hexdigest() == '462902780f77787e1b79923abd70ccc4a471b5da7a1b90d55ff7e770e61abb02'
calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
assert sum(isinstance(node.func, ast.Name) and node.func.id == 'read_execution_state' for node in calls) == 1
assert not any(isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
               and node.func.value.id == 'np' and node.func.attr == 'load' for node in calls)
print(json.dumps(dict(status='passed', scope='pure synthetic continuation reporting and the actual handoff expression; no main, campaign artifact, source, array or strict read',
                      cases=['finite native failure retained', 'nullable movement serializes', 'passed probe reported',
                             'zero-motion native failure is uninformative and remains failed',
                             'passed zero motion remains literal passed but uninformative and requires a root decision',
                             'zero baseline-start gap is diagnostic only', 'unavailable baseline-start gap is retained',
                             'failed completed-probe result retained', 'four passes plus exit0 pass',
                             'exit1 remains failed', 'one failed resolution remains failed'],
                      rejected=rejected, historical_helper_unchanged=True, strict_read_call_sites=1, explicit_np_load_call_sites=0), indent=2))
