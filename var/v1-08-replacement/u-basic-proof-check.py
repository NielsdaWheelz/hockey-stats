"""temporary basic-receipt pass/count binding controls without any evaluator."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile

import numpy as np

from hockey_stats.artifacts import ordered_array_digest, write_json
from hockey_stats.captures import InputContractError
from hockey_stats.chance_cli import identity
from hockey_stats.execution_u_repair import _checked_numerical_qualification

HERE=Path(__file__).parent
scratch=Path(tempfile.mkdtemp(prefix='u-basic-proof-',dir=HERE))
coefficients=np.array([.1,.2],dtype=np.float64)
contract=dict(native_success=True,accepted_native_iterations=2,accepted_callbacks=2,
    raw_endpoint_moved=True,fresh_start_objective=10.,fresh_raw_endpoint_objective=9.,
    completed_endpoint_moved=True,completed_coefficients_sha256=ordered_array_digest({'coefficients':coefficients}))
for mode in ('passed','failed_identical_contract','wrong_callback_count','wrong_start_count'):
    inline=deepcopy(contract)
    if mode=='wrong_callback_count':inline['accepted_callbacks']=1
    path=scratch/(mode+'.json');write_json(path,dict(passed=mode!='failed_identical_contract',qualification=deepcopy(inline)))
    inline['basic_receipt']=identity(path)
    try:_checked_numerical_qualification(inline,coefficients,1 if mode=='wrong_start_count' else 2)
    except InputContractError:assert mode!='passed'
    else:assert mode=='passed'
print(json.dumps(dict(status='passed',scope='tiny numerical contract/JSON/arraydigest only; no source, probability, objective or solve',
    failed_basic_identical_contract_refused=True,native_callback_and_start_iteration_counts_bound=True,scratch=str(scratch)),indent=2))
