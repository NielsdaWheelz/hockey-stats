"""exercise actual reloaded source-backed fixture through all original wrappers."""
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import numpy as np
from hockey_stats.execution_inputs import load_u_bundle

here=Path(__file__).parent
spec=importlib.util.spec_from_file_location('u_diagnosis',here/'diagnose_execution_u.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
manifest=here/'u-capture-fixture-i9lihlc7/inputs/manifest.json'
bundle=load_u_bundle(manifest)
# fixture anchors remain fixture anchors; no real anchor/recipe is rewritten.
anchor=bundle['metadata']['anchor_objective'];gmax=bundle['metadata']['anchor_gradient_max']
scratch=Path(tempfile.mkdtemp(prefix='u-source-diagnosis-',dir=here))
with patch.object(m,'ANCHOR_LOSS',anchor),patch.object(m,'ANCHOR_GMAX',gmax):
    result=m.diagnose(manifest,scratch/'diagnosis')
assert result['capture_validation']['status']=='checked_reloaded_anchors',result
assert result['status']=='stopped' and not result['eligible_endpoint']
assert result['reason'] in ('original_failure_unreproduced','full_objective_cap'),result
assert result['full_objective_calls']<=256 and result['native_objective_calls']<=64
assert (scratch/'diagnosis/native-000-before.npz').is_file()
assert (scratch/'diagnosis/trial-evidence.json').is_file()
print(json.dumps(dict(status='passed',reason=result['reason'],
    full_calls=result['full_objective_calls'],native_calls=result['native_objective_calls'],
    original_wrappers=True,source_backed_fixture=True,scratch=str(scratch))))
