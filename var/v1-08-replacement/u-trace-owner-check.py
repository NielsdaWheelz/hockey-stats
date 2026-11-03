"""temporary mechanical ownership check; no model or source inputs."""
import ast
from pathlib import Path
from hockey_stats import execution_trace as trace
from hockey_stats.execution_trace import Evaluations,NativeObserver

here=Path(__file__).parent
before=ast.parse((here/'u-trace-before-extraction.py').read_text())
after=ast.parse(Path(trace.__file__).read_text())
old={node.name:node for node in before.body if isinstance(node,(ast.ClassDef,ast.FunctionDef))}
new={node.name:node for node in after.body if isinstance(node,(ast.ClassDef,ast.FunctionDef))}
for name in ('encoded','save_json','reference','same_bits','assert_repeat','DiagnosticStop','NativeObserver'):
    assert ast.dump(old[name])==ast.dump(new[name]),name
for old_method,new_method in zip(old['Evaluations'].body,new['Evaluations'].body,strict=True):
    if isinstance(old_method,ast.FunctionDef) and old_method.name=='__init__':
        assert [ast.dump(node) for node in old_method.body]==[ast.dump(node) for node in new_method.body]
        assert new_method.args.defaults==[]
        assert [node.arg for node in new_method.args.kwonlyargs]==['limit','native_limit']
        assert new_method.args.kw_defaults==[None,None]
    else:assert ast.dump(old_method)==ast.dump(new_method)
assert Evaluations.__module__=='hockey_stats.execution_trace'
assert NativeObserver.__module__=='hockey_stats.execution_trace'
for name in ('directions','direction_evidence','trial_evidence','gradient_direction_evidence','diagnose'):
    assert name not in new,name
print('passed: trace methods/helpers unchanged; package owns explicit caps; study retains all verdict/direction policy')
