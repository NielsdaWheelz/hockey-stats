"""temporary shared probability qualification checks on frozen fixture inputs."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import numpy as np

from hockey_stats import execution
from hockey_stats.artifacts import ordered_array_digest, write_json
from hockey_stats.chance_cli import identity
from hockey_stats.captures import InputContractError
from hockey_stats.execution_fit import annual_priors, prior_mean
from hockey_stats.execution_inputs import load_u_bundle
from hockey_stats.execution_state import read_execution_state, read_execution_probe
from hockey_stats.execution_u_repair import qualify_u_bundle

HERE=Path(__file__).parent
scratch=Path(tempfile.mkdtemp(prefix='u-qualification-controls-',dir=HERE))
path=HERE/'u-capture-fixture-tpii7f8u/inputs/manifest.json'
bundle=load_u_bundle(path)
donor=read_execution_state(bundle['metadata']['donor']['path'],'fixture')
probe=read_execution_probe(donor,'u');saved=probe.heads['u']
actors=annual_priors(bundle['design'],bundle['metadata']['incoming_ledger'])
for actor in actors:actor['prior_mean']=prior_mean(actor,probe.arrays['u']['coefficients'])
comparison=dict(probe.probe['comparison'])
for key in ('maximum_probability_change','head_maximum_changes','terminal_maximum_changes','evaluated_origins','evaluated_branches'):comparison.pop(key)
result=dict(status='complete',coefficients=probe.arrays['u']['coefficients'],actors=actors,
    starts=saved['starts'],selected_start=saved['selected_start'],requested_starts=['continuation'],
    diagnostics={key:value for key,value in saved['diagnostics'].items() if key not in ('requested_starts','wall_seconds')},
    wall_seconds=saved['diagnostics']['wall_seconds'],reasons=[],comparison=comparison)
basic=dict(native_success=True,accepted_native_iterations=saved['starts'][0]['iterations'],accepted_callbacks=saved['starts'][0]['iterations'],
    raw_endpoint_moved=True,fresh_start_objective=comparison['base_objective'],fresh_raw_endpoint_objective=comparison['tightened_objective'],
    completed_endpoint_moved=True,completed_coefficients_sha256=ordered_array_digest({'coefficients':result['coefficients']}))
write_json(scratch/'basic-fixture-contract.json',dict(kind='fixture-contract-control',passed=True,qualification=dict(basic)))
basic['basic_receipt']=identity(scratch/'basic-fixture-contract.json');result['u_repair_qualification']=basic
# existing evaluator and ordinary return schema must stay exact when locators are requested.
ordinary=execution._probability_comparison(donor,probe,bundle['probes'])
locators={};with_locators=execution._probability_comparison(donor,probe,bundle['probes'],locators=locators)
assert ordinary==with_locators=={key:value for key,value in probe.probe['comparison'].items() if key in ordinary}
assert set(locators)=={'maximum_probability_change','head_maximum_changes','terminal_maximum_changes'}
for family,values in (('head_maximum_changes',ordinary['head_maximum_changes']),('terminal_maximum_changes',ordinary['terminal_maximum_changes'])):
    for key,value in values.items():
        location=locators[family][key]
        assert location['change']==value and location['origin_cell'] in range(656)
        assert location['neutralize'] in ([],['shooter','setter','goalie','coaching'])
assert locators['maximum_probability_change']['change']==ordinary['maximum_probability_change']
# no full objective, fitting, source read or selector call belongs to qualification.
with patch.object(execution,'_resolution_selector',side_effect=AssertionError('probe reselection')):
    qualified=qualify_u_bundle(bundle,result,scratch/'passed')
assert qualified['probability_passed'] and qualified['comparison']==dict(comparison,**ordinary)
assert qualified['metadata']==saved and np.array_equal(qualified['arrays']['coefficients'],result['coefficients'])
assert qualified['locators']==locators and qualified['receipt'].is_file()
# a genuine large coefficient change must fail the same fixed probability budget.
bad=deepcopy(result);bad['coefficients']=result['coefficients'].copy();bad['coefficients'][0]+=.1
bad['u_repair_qualification']['completed_coefficients_sha256']=ordered_array_digest({'coefficients':bad['coefficients']})
write_json(scratch/'large-delta-fixture-contract.json',dict(passed=True,qualification={key:value for key,value in bad['u_repair_qualification'].items() if key!='basic_receipt'}))
bad['u_repair_qualification']['basic_receipt']=identity(scratch/'large-delta-fixture-contract.json')
for actor in bad['actors']:actor['prior_mean']=prior_mean(actor,bad['coefficients'])
failed=qualify_u_bundle(bundle,bad,scratch/'failed')
assert failed['probability_passed'] is False and failed['comparison']['maximum_probability_change']>1e-5
assert failed['locators']['maximum_probability_change']['change']==failed['comparison']['maximum_probability_change']
# frozen bindings and supported actor means cannot be silently replaced.
changed=dict(bundle,selector=deepcopy(bundle['selector']));changed['selector']['requirements'][0]['disposition']='unavailable'
try:qualify_u_bundle(changed,result,scratch/'changed-selector')
except InputContractError:pass
else:raise AssertionError('changed frozen selector accepted')
wrong=deepcopy(result)
prior_only=next((actor for actor in wrong['actors'] if not actor['likelihood_support']),None)
if prior_only:
    wrong['coefficients']=wrong['coefficients'].copy();wrong['coefficients'][prior_only['index']]+=1.
    wrong['u_repair_qualification']['completed_coefficients_sha256']=ordered_array_digest({'coefficients':wrong['coefficients']})
    write_json(scratch/'wrong-completion-fixture-contract.json',dict(passed=True,qualification={key:value for key,value in wrong['u_repair_qualification'].items() if key!='basic_receipt'}))
    wrong['u_repair_qualification']['basic_receipt']=identity(scratch/'wrong-completion-fixture-contract.json')
    try:qualify_u_bundle(bundle,wrong,scratch/'wrong-completion')
    except InputContractError:pass
    else:raise AssertionError('uncompleted prior-only actor accepted')
missing=dict(result);missing.pop('u_repair_qualification')
try:qualify_u_bundle(bundle,missing,scratch/'missing-basic')
except InputContractError:pass
else:raise AssertionError('arbitrary completed result bypassed basic numerical qualification')
print(json.dumps(dict(status='passed',scope='saved fixture bundle and checked donor/probe; no source reconstruction, solve or full objective',
    ordinary_comparison_exact=True,maxima_locators=True,missing_basic_contract_refused=True,passed_saved_fixture_probe=True,oversized_probability_change_refused=True,
    frozen_selector_refused=True,prior_only_completion_checked=prior_only is not None,scratch=str(scratch)),indent=2))
