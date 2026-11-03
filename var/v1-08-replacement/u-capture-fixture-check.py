"""temporary full fixture capture, donor metadata and numerical reload integration."""
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import numpy as np

from hockey_stats import execution_design as ed
from hockey_stats.analysis_data import read_prepared
from hockey_stats.execution_fit import objective
from hockey_stats.execution_inputs import load_u_bundle
from hockey_stats.execution_state import read_execution_state

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('fixture_capture',HERE/'capture_execution_u.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
root=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture')
prepared=read_prepared('/Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6','fixture')
coaches='/Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json'
previous=read_execution_state(root/'execution/20242025','fixture')
donor=read_execution_state(root/'execution/20252026','fixture')
expected=json.loads((root/'fit-20252026-source-check.json').read_text())
scratch=Path(tempfile.mkdtemp(prefix='u-capture-fixture-',dir=HERE))
original=ed._head_design;constructed=[];canonical={}
def head(name,*args,**kwargs):
    assert name=='u';constructed.append(name)
    result=original(name,*args,**kwargs);canonical.update(result);return result
with patch.object(ed,'_head_design',head):
    path=module.capture(prepared,coaches,previous,donor,expected,scratch,{'scope':'fixture only'})
loaded=load_u_bundle(path)
assert constructed==['u'] and 'attempts' not in loaded['metadata']['coverage']
assert loaded['metadata']['anchor_objective']==donor.heads['u']['resolution']['comparison']['base_objective']
assert loaded['metadata']['anchor_gradient_max']==donor.heads['u']['resolution']['comparison']['base_gradient_max']
assert loaded['metadata']['incoming_ledger']==previous.heads['u']['ledger']
selector=json.loads((donor.path.parent/'resolution/baseline.json').read_text())['selector']
assert loaded['selector']==selector
assert [p.key for p in loaded['probes']]==selector['keys']+[row['key'] for row in selector['fixture_witnesses']]
a=objective(loaded['initial'],canonical,loaded['actors'])
b=objective(loaded['initial'],loaded['design'],loaded['actors'])
assert np.float64(a[0]).tobytes()==np.float64(b[0]).tobytes()
assert a[1].dtype==b[1].dtype and a[1].tobytes()==b[1].tobytes()
assert np.float64(b[0]).tobytes()==np.float64(loaded['metadata']['anchor_objective']).tobytes()
assert np.float64(np.max(np.abs(b[1]))).tobytes()==np.float64(loaded['metadata']['anchor_gradient_max']).tobytes()
print(json.dumps(dict(status='passed',scope='full nine-game fixture donor/history/source/capture/reload; no real source or native solve',
    canonical_training_heads=constructed,source_contexts=expected['source_contexts'],physical_rows=len(loaded['design']['target']),
    frozen_actual_probes=len(selector['keys']),frozen_fixture_witnesses=len(selector['fixture_witnesses']),
    source_context_sha256=loaded['metadata']['source_context_sha256'],source_response_sha256=loaded['metadata']['source_response_sha256'],
    donor_actor_priors_support_layout_and_coverage_exact=True,objective_and_full_gradient_bits_equal=True,
    reloaded_saved_objective_and_gradient_max_bits_equal=True,payload_bytes=json.loads(path.read_text())['payload_bytes'],scratch=str(scratch)),indent=2))
