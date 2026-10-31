"""temporary post-solve failure-state contract check."""
from dataclasses import replace
import hashlib
import importlib.util
from pathlib import Path
import tempfile
from unittest.mock import patch

from hockey_stats.captures import InputContractError
from hockey_stats.spatial_rates import fit_spatial, head_diagnostics
from hockey_stats.spatial_state import read_spatial_state

spec=importlib.util.spec_from_file_location('tiny',Path(__file__).with_name('state_integration.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
d=module.design()
with tempfile.TemporaryDirectory(prefix='spatial-failed-head-') as directory:
    root=Path(directory)
    previous=fit_spatial(d,None,root/'previous')
    previous_digest=hashlib.sha256((previous.path/'manifest.json').read_bytes()).hexdigest()
    later=replace(d,season='20222023',valued=dict(d.valued,season='20222023'),
                  training_cutoff='2023-01-01',coverage=dict(d.coverage,season='20222023'),
                  player_facts={p:dict(position_group='F',age_days=27*365.2425) for p in d.players})
    def fail_volume(design,head,beta):
        if head=='volume':raise InputContractError('deliberate post-solve diagnostic failure')
        return head_diagnostics(design,head,beta)
    with patch('hockey_stats.spatial_rates.head_diagnostics',side_effect=fail_volume):
        state=fit_spatial(later,previous,root/'failed')
    assert state.heads['volume']['status']=='failed' and not state.head_arrays['volume']
    assert state.heads['volume']['ledger']==previous.heads['volume']['ledger']
    assert all(state.heads['volume'][key] is None for key in ('centers','reference_predictor','age_curves'))
    assert state.heads['volume']['solver']['converged'] and state.heads['volume']['objective'] is not None
    assert 'deliberate post-solve diagnostic failure' in state.heads['volume']['reasons'][0]
    assert all(not row['available'] and row['values']['offense']['xg']['complete'] is None for row in state.projections)
    assert all(row['prior_kind'] is None and row['included_seconds'] is None for row in state.coefficient_support if row['head']=='volume')
    read_spatial_state(state.path,'fixture')
    assert hashlib.sha256((previous.path/'manifest.json').read_bytes()).hexdigest()==previous_digest
print('post-solve failure remains strict-readable, unavailable and history-preserving: green')
