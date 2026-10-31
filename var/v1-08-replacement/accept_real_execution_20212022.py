"""one saved-state acceptance read; no fitting, scoring or upstream source reads."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import resource
import subprocess
from time import perf_counter

import numpy as np
from hockey_stats.execution_state import read_execution_state

WORK = Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
NEW = Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution/20212022')
OLD = Path('/Volumes/Expansion/hockey-stats/runs/execution-v1-05-20261025-02/20212022')
REPORT = NEW.parent.parent / 'fit-20212022-source-check.json'
ANALYSIS = 'c2412ac713b8c60e808dd71771f0812224b94439'

def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()

def read(path):
    return json.loads(path.read_bytes())

began = perf_counter()
state = read_execution_state(NEW, 'real')
strict_seconds = perf_counter()-began
print(json.dumps(dict(strict_read='passed', wall_seconds=strict_seconds)), flush=True)
manifest = state.manifest
assert digest(state.path) == '7c740083469c9a16edf6d73552ea18b89425a52b2ea7f4deeea41f79a5043e61'
assert manifest['season'] == '20212022' and manifest['previous'] is None
assert manifest['recipe']['sha256'] == '47691110ac34bf7d63cdc32664335bd6579a5953545f0cefa8ebf0257bf88674'
assert digest(REPORT) == '2a1e41e1b64dabe30d2e000559e49fe2106f54e494855bbd9629d7e346b025df'
report = read(REPORT)
assert report['status'] == 'passed' and report['before_head_construction'] and report['known_expected'] == report['known_checked'] == 54
assert state.coverage['heads'] == report['head_admission']
assert digest(OLD/'manifest.json') == '592dce62062443311ea504cd10c7304b73be10441b6d558e91ca635663940953'
original = read(OLD/'manifest.json')
assert manifest['prepared'] == original['prepared'] and manifest['coaches'] == original['coaches'] and manifest['training_cutoff'] == original['training_cutoff']
old_files = {row['path']: row['sha256'] for row in original['files']}
heads = {}
for head in ('u', 'q', 'r', 'g'):
    current = state.heads[head]
    old_path = OLD/f'heads/{head}.json'
    assert digest(old_path) == old_files[f'heads/{head}.json']
    old = read(old_path)
    beta = state.arrays[head]['coefficients']
    old_arrays_path = OLD/f'heads/{head}.npz'
    assert digest(old_arrays_path) == old_files[f'heads/{head}.npz']
    with np.load(old_arrays_path, allow_pickle=False) as saved:
        assert saved.files == ['coefficients']
        old_beta = saved['coefficients']
    assert beta.dtype == old_beta.dtype == np.dtype('float64') and beta.shape == old_beta.shape
    assert current['design']['coefficient_names'] == old['design']['coefficient_names']
    assert current['design']['columns'] == old['design']['columns'] and current['design']['actor_indices'] == old['design']['actor_indices']
    assert current['actors'] == old['actors']
    assert current['status'] == 'complete' and not current['reasons'] and current['resolution'] == {'status': 'not_applicable'}
    actors = {(row['block'], row['id']): row for row in current['actors']}
    priors = {(row['block'], row['id']): row for row in current['priors']}
    ledger = {(row['block'], row['id']): row for row in current['ledger']}
    old_ledger = {(row['block'], row['id']): row for row in old['ledger']}
    supported = {key for key, row in actors.items() if row['likelihood_support'] > 0}
    assert set(priors) == set(actors) and set(ledger) == supported == set(old_ledger)
    for key, actor in actors.items():
        prior = priors[key]
        precision = 16. if actor['block'] == 'goalie' else 256. if actor['block'].endswith('coach') else 4.
        assert prior == dict(block=actor['block'], id=actor['id'], mean=0., precision=precision, age_delta=[], age_indices=[], transition_reason='entry', prior_mean=0., last_supported=None)
        if actor['prior_only']:
            assert beta[actor['index']] == 0. and key not in ledger
        else:
            assert ledger[key] == dict(block=actor['block'], id=actor['id'], coefficient=float(beta[actor['index']]), season='20212022', role=actor['role'], age=actor['age'])
    age_indices = [i for roles in current['design']['age_indices_by_block_role'].values() for indices in roles.values() for i in indices]
    assert all(beta[i] == 0. for i in age_indices)
    center_error = 0.
    for block, center in current['centers'].items():
        rows = [row for row in actors.values() if row['block'] == block]
        weight = sum(row['center_weight'] for row in rows)
        expected = sum(row['center_weight']*float(beta[row['index']]) for row in rows)/weight if weight else 0.
        assert abs(weight-center['weight']) < 1e-9 and center['prior_only'] == (weight == 0)
        center_error = max(center_error, abs(expected-center['value']))
    assert center_error < 1e-12
    population = report['head_populations'][head]
    keys = [row['key'] for row in state.coverage['attempts'] if row['heads'][head]['included']]
    key_sha = hashlib.sha256(json.dumps(keys, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert key_sha == population['key_sha256']
    n = population['physical_attempts']
    assert len(keys) == n == current['diagnostics']['in_sample']['attempts'] == old['diagnostics']['in_sample']['attempts']
    assert current['diagnostics']['in_sample']['positive'] == old['diagnostics']['in_sample']['positive'] == report['head_admission'][head]['class:1']
    unavailable = sum(value for key, value in population['dispositions'].items() if key.startswith('unavailable:'))
    start_fields = ('shooter_start_zone:offensive', 'shooter_start_zone:neutral', 'shooter_start_zone:defensive')
    for field in start_fields:
        support = current['design']['feature_support'][field]
        assert support['unavailable_attempts'] == unavailable and support['available_weight'] == n-unavailable and support['structural_absence_attempts'] == 0
    indicator = current['design']['feature_support']['unavailable:shooter_shift_start']
    assert indicator['available_weight'] == n and indicator['unavailable_attempts'] == 0
    diag = current['diagnostics']
    assert diag['converged'] and math.isfinite(diag['objective']) and math.isfinite(diag['gradient_max'])
    assert current['selected_start'] == 'zero' and [row['name'] for row in current['starts']] == ['zero', 'prior_mean'] and current['starts'][1]['deduplicated_to'] == 'zero'
    selected = current['starts'][0]
    native = selected['inner_solves'] if head == 'g' else [selected]
    assert native and all(row['converged'] and row['iterations'] <= 10000 for row in native)
    if head == 'g':
        assert diag['em_iterations'] == len(native) <= 100 and diag['relative_objective_change'] <= 1e-8 and diag['responsibility_change'] <= 1e-6
        assert all(row['increase'] <= row['allowed'] for row in diag['objective_increases'])
        assert all(after-before <= 1e-10*(1+abs(before)) for before, after in zip(diag['objective_trace'], diag['objective_trace'][1:]))
    difference = beta-old_beta
    largest = int(np.argmax(np.abs(difference)))
    heads[head] = dict(status='complete', dimension=len(beta), physical_attempts=n, positive_labels=report['head_admission'][head]['class:1'], actor_rows=len(actors), prior_only_rows=sum(row['prior_only'] for row in actors.values()), ledger_rows=len(ledger), entry_only_no_old_history=True, first_year_age_coefficients_zero=True, maximum_center_error=center_error, current_unavailable_start_attempts=unavailable, original_unavailable_start_attempts=old['design']['feature_support'][start_fields[0]]['unavailable_attempts'], all_source_report_counts_keys_support_weights_match=True, selected_start='zero', prior_mean_start='deduplicated_to_zero', objective=diag['objective'], original_objective=old['diagnostics']['objective'], raw_gradient_max=diag['gradient_max'], termination=diag['termination'], iterations=diag['iterations'], evaluations=diag['evaluations'], em_iterations=diag['em_iterations'], em_responsibility_change=diag.get('responsibility_change'), em_relative_objective_change=diag.get('relative_objective_change'), em_allowed_objective_increases=diag.get('objective_increases', []), native_solve_count=len(native), coefficient_comparison=dict(max_abs=float(np.max(np.abs(difference))), l2=float(np.linalg.norm(difference)), changed_coordinates=int(np.count_nonzero(difference)), largest_coordinate=current['design']['coefficient_names'][largest], old_value=float(old_beta[largest]), new_value=float(beta[largest]), interpretation='descriptive coordinate difference under changed start encoding; no equivalence, prediction-stability or scientific-quality margin'), original_metadata_sha256=old_files[f'heads/{head}.json'], original_arrays_sha256=old_files[f'heads/{head}.npz'])
assert manifest['resources']['solve_counts'] == {head: row['native_solve_count'] for head, row in heads.items()}
assert manifest['resources']['resolution_solve_counts'] == dict.fromkeys(heads, 0)
assert manifest['recipe']['definition']['solver'] == dict(maxiter=10000, ftol=1e-15, gtol=1e-6, em_maxiter=100, em_objective=1e-8, em_responsibility=1e-6, continuation=dict(ftol=1e-16, gtol=1e-7, em_objective=1e-9, em_responsibility=1e-7))
source_review = WORK/'docs/research/spatial-v1-08/receipts/replacement-real-execution-20212022-source-metadata-review.json'
assert read(source_review)['status'].startswith('passed')
launch = NEW.parent
launch_head = (launch/'20212022-launch-head.txt').read_text().strip()
producer_head = manifest['implementation']['git_commit']
assert all(subprocess.check_output(['git', 'rev-parse', head+':analysis'], cwd=WORK, text=True).strip() == ANALYSIS for head in (launch_head, producer_head, 'HEAD'))
assert not manifest['implementation']['git_dirty'] and not subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all', '--', 'analysis'], cwd=WORK, text=True)
assert (launch/'20212022-exit.txt').read_text().strip() == '0'
log = (launch/'20212022.log').read_text()
timing = re.search(r'(\d+\.\d+) real\s+(\d+\.\d+) user\s+(\d+\.\d+) sys', log)
rss = int(re.search(r'(\d+)\s+maximum resident set size', log).group(1))
footprint = int(re.search(r'(\d+)\s+peak memory footprint', log).group(1))
member_bytes = sum((NEW/row['path']).stat().st_size for row in manifest['files'])
assert member_bytes == manifest['resources']['output_bytes'] == 202150506
receipt = dict(kind='replacement-first-real-execution-saved-state-acceptance', status='computational_acceptance_passed; no blocker; scoring and successor remain held for root review', recorded_at_utc=datetime.now(timezone.utc).isoformat(), manifest=dict(path=str(state.path), sha256=digest(state.path)), purpose='real', season='20212022', previous=None, recipe= {key:manifest['recipe'][key] for key in ('name', 'version', 'sha256')}, strict_read=dict(status='passed', invocations_here=1, wall_seconds=strict_seconds, upstream_source_reads=0), heads=heads, source_report=dict(path=str(REPORT), sha256=digest(REPORT), head_keys_counts_unavailable_weights_match_actual_saved_state=True), source_design_independent_review=dict(path=str(source_review), sha256=digest(source_review), status='clear', scope='exact196154100bytecoverage core identity; only three start-support records and declared transform text differ; nonstart design/population/labels/actors/setter weights unchanged', limits='no original raw context digest; no exact original shared-indicator binary-one statistic'), history=dict(entry_only=True, no_old_coefficients_or_raw_means_used_as_priors=True, actor_support_axes_equal_original=True, supported_ledger_keys_equal_original=True, actual_supported_coefficients_are_new=True, zero_info_coefficients_zero_no_ledger=True, first_year_age_parameters_zero=True), numerical_limits=dict(baseline=manifest['recipe']['definition']['solver'], native_defaults=dict(maxfun=15000,maxls=20,history=10), first_year_final_probes=0, policy='accepted native ftol completion plus finite arrays/diagnostics; raw gradient is recorded, not rejected solely for exceeding gtol', final_real_resolution='four fixed final20252026continuations remain required; no first-year tighter probe introduced'), resources=dict(whole_command_wall_seconds=float(timing[1]), user_seconds=float(timing[2]), system_seconds=float(timing[3]), maximum_resident_bytes=rss, peak_memory_footprint_bytes=footprint, producer=manifest['resources'], producer_wall_scope='before completion manifest; distinct from whole6200.96second command', saved_member_bytes=member_bytes, annual_including_manifest_bytes=member_bytes+state.path.stat().st_size, readback_process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss), launch=dict(start=(launch/'20212022-start.txt').read_text().strip(), finish=(launch/'20212022-finish.txt').read_text().strip(), exit=0, launch_head=launch_head, producer_head=producer_head, analysis_tree=ANALYSIS, analysis_clean=True, log_sha256=digest(launch/'20212022.log')), limits=['in-sample objectives and coefficient deltas do not establish calibration, robust ability or causal isolation','source unavailable counters overlap and are not all timing failures; unresolved-binding scope/classification remains with its focused receipts','one completed annual is measured cost, not a remaining-campaign forecast'], scope='one new strict saved-state read plus original four saved metadata/coefficient arrays and source-report metadata only; no fit, score, prepared game/source pass or original state admission', next='bind actual completed manifest digest into held first score/year2scripts; root reviews and alone launches first score; year2waits fit-score parity')
output = WORK/'docs/research/spatial-v1-08/receipts/replacement-real-execution-20212022-completion.json'
with output.open('x') as destination:
    json.dump(receipt, destination, indent=2)
    destination.write('\n')
print(json.dumps(dict(status=receipt['status'], receipt=str(output), sha256=digest(output), strict_read_seconds=strict_seconds, heads={key:{name:value[name] for name in ('objective','raw_gradient_max','termination','native_solve_count','maximum_center_error','coefficient_comparison')} for key,value in heads.items()}), indent=2), flush=True)
