"""one year-five saved-state acceptance read; no source pass, fit or scoring."""
import argparse
from collections import Counter
from copy import deepcopy
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
CAMPAIGN = Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real')
NEW = CAMPAIGN / 'execution/20252026'
PREVIOUS = CAMPAIGN / 'execution/20242025'
OLD = Path('/Volumes/Expansion/hockey-stats/runs/execution-v1-05-20261025-02/20252026')
ANALYSIS = 'c2412ac713b8c60e808dd71771f0812224b94439'
PREVIOUS_SHA = '1ba2c8af310d12239d6cabb89ee6cc92b6b98bd95e6834b4f44e303802a44cfe'
OLD_SHA = 'c736f1feb26df018465eb0032d51611ac07846e64de053bdd6a99e18026379be'
RECIPE = '47691110ac34bf7d63cdc32664335bd6579a5953545f0cefa8ebf0257bf88674'
OBSERVER = '286b34dd95ae9cf60a562ad9ec6426000d04a9e658ee3977b7b88080099fedaf'
HEADS = ('u', 'q', 'r', 'g')
START_FIELDS = ('shooter_start_zone:offensive', 'shooter_start_zone:neutral', 'shooter_start_zone:defensive')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def identity(path):
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest(path))


def read(path):
    return json.loads(path.read_bytes())


def bound_json(root, manifest, name):
    payload = (root / name).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == next(row['sha256'] for row in manifest['files'] if row['path'] == name)
    return json.loads(payload)


def actor_key(row):
    return row['block'], str(row['id'])


def expected_prior(actor, last, design, beta):
    """independently spell out entry/carry and the role-specific quadratic age mean."""
    block, role, age = actor['block'], actor['role'], actor['age']
    coach = block in ('attacking_coach', 'defending_coach')
    entry, carry = (16., 64.) if block == 'goalie' else (256., 1024.) if coach else (4., 16.)
    delta, indices = [], []
    reason = 'entry' if last is None else 'age_neutral'
    if last is not None and not coach:
        if role not in ('F', 'D', 'G') or last['role'] != role:
            reason = 'missing_or_changed_role'
        elif age is None or last['age'] is None:
            reason = 'missing_age'
        else:
            now, before = (age-27.)/10., (last['age']-27.)/10.
            delta = [now-before, now**2-before**2]
            indices = design['age_indices_by_block_role'][block][role]
            reason = 'age_carry'
    mean = 0. if last is None else last['coefficient']
    conditional = float(mean+np.dot(delta, beta[indices]))
    return dict(block=actor['block'], id=actor['id'], mean=mean, precision=entry if last is None else carry,
                age_delta=delta, age_indices=indices, transition_reason=reason, prior_mean=conditional, last_supported=last)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-manifest-sha256', required=True)
    parser.add_argument('--expected-source-sha256', required=True)
    parser.add_argument('--out-check', type=Path, required=True)
    args = parser.parse_args()
    assert all(re.fullmatch('[0-9a-f]{64}', value) for value in (args.expected_manifest_sha256, args.expected_source_sha256))
    assert not args.out_check.exists()
    assert (NEW.parent / '20252026-exit.txt').read_text().strip() == '0'
    assert digest(NEW / 'manifest.json') == args.expected_manifest_sha256
    began = perf_counter()
    state = read_execution_state(NEW, 'real')
    strict_seconds = perf_counter()-began
    print(json.dumps(dict(strict_read='passed', wall_seconds=strict_seconds)), flush=True)
    manifest = state.manifest
    assert digest(PREVIOUS / 'manifest.json') == PREVIOUS_SHA
    previous = read(PREVIOUS / 'manifest.json')
    assert digest(OLD / 'manifest.json') == OLD_SHA
    original = read(OLD / 'manifest.json')
    assert manifest['season'] == '20252026' and manifest['recipe']['sha256'] == RECIPE
    assert manifest['previous'] == dict(path=str(PREVIOUS / 'manifest.json'), sha256=PREVIOUS_SHA,
                                        season='20242025', purpose='real', recipe_sha256=RECIPE, usage='annual')
    assert all(manifest[name] == original[name] for name in ('prepared', 'coaches', 'training_cutoff'))
    assert manifest['prepared']['sha256'] == previous['prepared']['sha256'] == '63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c'
    assert manifest['coaches']['sha256'] == previous['coaches']['sha256'] == '102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0'
    source_path = CAMPAIGN / 'fit-20252026-source-check.json'
    assert digest(source_path) == args.expected_source_sha256
    source = read(source_path)
    assert source['status'] == 'passed' and source['before_head_construction'] and source['recipe_sha256'] == RECIPE
    assert source['purpose'] == 'real' and source['season'] == '20252026'
    assert source['known_expected'] == source['known_checked'] == 0 and not source['known_witnesses']
    assert source['command'] == ['fit', '--family', 'execution', '--prepared', str(Path(manifest['prepared']['path']).parent),
                                  '--coaches', manifest['coaches']['path'], '--season', '20252026', '--previous', str(PREVIOUS), '--out', str(NEW)]
    assert state.coverage['heads'] == source['head_admission']
    old_coverage = bound_json(OLD, original, 'coverage.json')
    original_optional = old_coverage.pop('optional_features')
    assert old_coverage == {key: value for key, value in state.coverage.items() if key != 'optional_features'}
    del old_coverage
    heads = {}
    for head in HEADS:
        current = state.heads[head]
        old = bound_json(OLD, original, f'heads/{head}.json')
        incoming_head = bound_json(PREVIOUS, previous, f'heads/{head}.json')
        assert current['status'] == 'complete' and not current['reasons'] and current['resolution']['status'] == 'passed'
        assert current['actors'] == old['actors'] and current['origin'] == old['origin'] and current['target'] == old['target']
        design, old_design = deepcopy(current['design']), deepcopy(old['design'])
        changes = [name for name in design['columns'] if design['feature_support'][name] != old_design['feature_support'][name]]
        assert set(changes) <= set(START_FIELDS)
        assert original_optional[head] == old['design']['feature_support']
        for item in (design, old_design):
            for field in START_FIELDS:
                item['feature_support'].pop(field)
            item['fixed_transforms'].pop('shift_start')
        assert design == old_design
        beta = state.arrays[head]['coefficients']
        actors = {actor_key(row): row for row in current['actors']}
        priors = {actor_key(row): row for row in current['priors']}
        incoming = {actor_key(row): row for row in incoming_head['ledger']}
        ledger = {actor_key(row): row for row in current['ledger']}
        old_priors = {actor_key(row): row for row in old['priors']}
        assert set(priors) == set(actors) == set(old_priors)
        assert set(ledger) == {actor_key(row) for row in old['ledger']}
        expected_ledger = dict(incoming)
        counts, transitions, gaps, witnesses, gap_witnesses = Counter(), Counter(), Counter(), {}, {}
        maximum_age_adjustment = maximum_prior_anchor_change = 0.
        for key, actor in actors.items():
            last = incoming.get(key)
            expected = expected_prior(actor, last, current['design'], beta)
            assert priors[key] == expected
            assert all(priors[key][name] == old_priors[key][name] for name in
                       ('precision', 'age_delta', 'age_indices', 'transition_reason'))
            maximum_prior_anchor_change = max(maximum_prior_anchor_change, abs(expected['mean']-old_priors[key]['mean']))
            maximum_age_adjustment = max(maximum_age_adjustment, abs(expected['prior_mean']-expected['mean']))
            counts['entry' if last is None else 'carry'] += 1
            transitions[expected['transition_reason']] += 1
            if last is not None:
                gap = 2025-int(last['season'][:4])
                assert gap in (1, 2, 3, 4)  # the accepted incoming ledger may retain 2021 through 2024 anchors.
                gaps[str(gap)] += 1
            assert actor['prior_only'] is (actor['likelihood_support'] == 0)
            if actor['prior_only']:
                counts['prior_only'] += 1
                assert float(beta[actor['index']]) == expected['prior_mean']
                assert ledger.get(key) == last
                witness_kind = 'prior_only_entry' if last is None else 'prior_only_carry'
            else:
                counts['supported_current'] += 1
                expected_ledger[key] = dict(block=actor['block'], id=actor['id'], coefficient=float(beta[actor['index']]),
                                            season='20252026', role=actor['role'], age=actor['age'])
                witness_kind = 'supported_entry' if last is None else 'supported_carry'
            witnesses.setdefault(witness_kind, dict(block=actor['block'], id=actor['id'], last_supported=last,
                                                    conditional_prior_mean=expected['prior_mean'], current_raw=float(beta[actor['index']]),
                                                    outgoing_ledger=ledger.get(key)))
            if last is not None:
                gap_witnesses.setdefault(str(gap), dict(block=actor['block'], id=actor['id'], last_supported=last,
                    current_age=actor['age'], transition_reason=expected['transition_reason'], age_delta=expected['age_delta'],
                    conditional_prior_mean=expected['prior_mean'], prior_only=actor['prior_only'], outgoing_ledger=ledger.get(key)))
        assert ledger == expected_ledger
        counts['incoming_absent_current'] = len(set(incoming)-set(actors))
        counts['preserved_incoming_ledger'] = sum(ledger.get(key) == row for key, row in incoming.items())
        counts['ledger_rows'] = len(ledger)
        if set(incoming)-set(actors):
            key = min(set(incoming)-set(actors))
            witnesses['absent_current_preserved'] = incoming[key]
        centers = {}
        for block, center in current['centers'].items():
            members = [row for row in actors.values() if row['block'] == block]
            weight = sum(row['center_weight'] for row in members)
            expected = sum(row['center_weight']*beta[row['index']] for row in members)/weight if weight else 0.
            assert center == dict(value=expected, weight=weight, prior_only=not bool(weight))
            centers[block] = center['value']
        population = source['head_populations'][head]
        keys = [row['key'] for row in state.coverage['attempts'] if row['heads'][head]['included']]
        assert len(keys) == population['physical_attempts'] == current['diagnostics']['in_sample']['attempts'] == old['diagnostics']['in_sample']['attempts']
        assert hashlib.sha256(json.dumps(keys, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == population['key_sha256']
        assert current['diagnostics']['in_sample']['positive'] == old['diagnostics']['in_sample']['positive'] == source['head_admission'][head]['class:1']
        unavailable = sum(value for name, value in population['dispositions'].items() if name.startswith('unavailable:'))
        assert sum(population['dispositions'].values()) == len(keys) == sum(population['all_strength_dispositions'].values())
        for field in START_FIELDS:
            assert current['design']['feature_support'][field] == dict(available_weight=float(len(keys)-unavailable),
                     unavailable_attempts=unavailable, structural_absence_attempts=0, active=True)
        indicator = current['design']['feature_support']['unavailable:shooter_shift_start']
        assert indicator == dict(available_weight=float(len(keys)), unavailable_attempts=0, structural_absence_attempts=0, active=True)
        diag = current['diagnostics']
        assert diag['converged'] and math.isfinite(diag['objective']) and math.isfinite(diag['gradient_max'])
        assert [row['name'] for row in current['starts']] == ['zero', 'prior_mean']
        completed = [row for row in current['starts'] if row.get('deduplicated_to') is None and row['converged']]
        selected = min(completed, key=lambda row: row['objective'])
        assert current['selected_start'] == selected['name'] and diag['objective'] == selected['objective']
        native_counts = []
        for start in current['starts']:
            if start.get('deduplicated_to') is not None:
                continue
            native = start['inner_solves'] if head == 'g' else [start]
            native_counts.append(len(native))
            if start['converged']:
                assert all(row['converged'] and row['iterations'] <= 10000 for row in native)
                if head == 'g':
                    assert start['em_iterations'] == len(native) <= 100 and start['relative_objective_change'] <= 1e-8 and start['responsibility_change'] <= 1e-6
                    assert all(row['increase'] <= row['allowed'] for row in start['objective_increases'])
                    assert all(after-before <= 1e-10*(1+abs(before)) for before, after in zip(start['objective_trace'], start['objective_trace'][1:]))
        assert manifest['resources']['solve_counts'][head] == sum(native_counts)
        heads[head] = dict(status='complete', actors=len(actors), dimension=len(beta), counts=dict(counts), transition_reasons=dict(transitions),
                           observed_carry_year_gaps=dict(gaps), gap_witnesses=gap_witnesses, witnesses=witnesses,
                           incoming_raw_ledger_and_outgoing_updates_exact=True,
                           maximum_conditional_age_adjustment=maximum_age_adjustment, maximum_incoming_anchor_change_vs_original=maximum_prior_anchor_change,
                           centers=centers, source_key_sha256=population['key_sha256'], physical_attempts=len(keys), positive=diag['in_sample']['positive'],
                           unavailable_start_attempts=unavailable, original_unavailable_start_attempts=old['design']['feature_support'][START_FIELDS[0]]['unavailable_attempts'],
                           changed_feature_support=changes, nonstart_design_and_population_exact_original=True,
                           source_eligibility_counts=population['eligibility_counts'], selected_start=current['selected_start'],
                           starts=[dict(name=row['name'], deduplicated_to=row.get('deduplicated_to'), converged=row.get('converged'), objective=row.get('objective'),
                                        termination=row.get('termination'), native_solves=0 if row.get('deduplicated_to') else len(row['inner_solves']) if head=='g' else 1)
                                   for row in current['starts']], objective=diag['objective'], raw_gradient_max=diag['gradient_max'],
                           termination=diag['termination'], iterations=diag['iterations'], evaluations=diag['evaluations'], em_iterations=diag['em_iterations'],
                           native_solves=sum(native_counts), age_coefficients={block:{role:[float(beta[i]) for i in indices] for role,indices in roles.items()}
                                                                            for block,roles in current['design']['age_indices_by_block_role'].items()})
        print(json.dumps(dict(head=head, status='passed', counts=dict(counts), source_eligibility_counts=population['eligibility_counts'])), flush=True)
    assert manifest['recipe']['definition']['solver'] == dict(maxiter=10000, ftol=1e-15, gtol=1e-6, em_maxiter=100,
              em_objective=1e-8, em_responsibility=1e-6, continuation=dict(ftol=1e-16,gtol=1e-7,em_objective=1e-9,em_responsibility=1e-7))
    # the one strict read above already checked all four probe arrays, their
    # coefficient deltas, exact objective/prior bindings and literal controls.
    # this section reports saved JSON only; it does not reopen probe arrays.
    baseline = bound_json(NEW, manifest, 'resolution/baseline.json')
    baseline_ref = dict(path='resolution/baseline.json', sha256=digest(NEW / 'resolution/baseline.json'))
    selector = baseline['selector']
    probe_heads = {}
    for head in HEADS:
        resolution = state.heads[head]['resolution']
        assert resolution['status'] == 'passed' and resolution['baseline'] == baseline_ref
        probe = bound_json(NEW, manifest, resolution['probe']['path'])
        assert probe['usage'] == 'numerical_probe' and probe['head'] == head and probe['baseline'] == baseline_ref
        metadata, comparison = probe['metadata'], probe['comparison']
        assert metadata['selected_start'] == 'continuation' and len(metadata['starts']) == 1
        start = metadata['starts'][0]
        assert start['name'] == 'continuation' and start['converged'] and start.get('deduplicated_to') is None
        native = len(start['inner_solves']) if head == 'g' else 1
        assert native == manifest['resources']['resolution_solve_counts'][head]
        assert resolution['comparison'] == comparison and comparison['maximum_probability_change'] <= 1e-5
        assert comparison['optimizer_maxiter'] == 10000 and comparison['optimizer_ftol'] == 1e-16 and comparison['optimizer_gtol'] == 1e-7
        assert comparison['em_maxiter'] == 100 and comparison['em_relative_tolerance'] == 1e-9 and comparison['em_responsibility_tolerance'] == 1e-7
        probe_heads[head] = dict(status='passed', metadata=resolution['probe'], arrays=probe['arrays'],
                                 continuation_starts=1, native_solves=native, comparison=comparison)
    assert len(probe_heads) == 4
    probes = dict(head_continuations=4, extra_probe_commands=0, baseline=baseline_ref,
                  baseline_inputs_metadata_and_array_bindings_checked_by_strict_reader=True,
                  baseline_coefficients_preserved=True, probe_coefficients_promoted=False,
                  coefficient_delta_scope='the strict reader independently recalculated maximum/l2 deltas from saved baseline/probe arrays; this reporting section did not load them again',
                  probability_scope='literal saved probability maxima and component records; no independent predictor/source/probability replay here and no all-season or all-player bound',
                  probability_margin=1e-5, heads=probe_heads,
                  selector=dict(policy=selector['policy'], actual_contexts=len(selector['keys']),
                                keys_sha256=hashlib.sha256(json.dumps(selector['keys'], separators=(',', ':')).encode()).hexdigest(),
                                first_actual_key=selector['keys'][0], last_actual_key=selector['keys'][-1],
                                fixture_witnesses=len(selector['fixture_witnesses']), requirements=len(selector['requirements']),
                                requirement_dispositions=dict(Counter(row['disposition'] for row in selector['requirements'])),
                                eligible_contexts=selector['population']['eligible_contexts'],
                                withheld_contexts=len(selector['population']['withheld_contexts']),
                                synthetic_geometry=dict(context_key=selector['synthetic_geometry']['context_key'],
                                    shot_types=len(selector['synthetic_geometry']['types']),
                                    native_cells=len(selector['synthetic_geometry']['cells']),
                                    execution=selector['synthetic_geometry']['execution'])))
    launch = NEW.parent
    launch_head = (launch / '20252026-launch-head.txt').read_text().strip()
    assert (launch / '20252026-launch-analysis-tree.txt').read_text().strip() == ANALYSIS
    assert not (launch / '20252026-launch-analysis-status.txt').read_text()
    assert (launch / '20252026-launch-previous-sha256.txt').read_text().split()[0] == PREVIOUS_SHA
    assert (launch / '20252026-launch-observer-sha256.txt').read_text().split()[0] == OBSERVER
    assert (launch / '20252026-expected-recipe-sha256.txt').read_text().strip() == RECIPE
    for name in ('prepared', 'coaches'):
        assert (launch / f'20252026-launch-{name}-sha256.txt').read_text().split()[0] == manifest[name]['sha256']
    for head in (launch_head, manifest['implementation']['git_commit'], 'HEAD'):
        assert subprocess.check_output(['git','rev-parse',head+':analysis'],cwd=WORK,text=True).strip() == ANALYSIS
    assert not manifest['implementation']['git_dirty'] and not subprocess.check_output(['git','status','--porcelain','--untracked-files=all','--','analysis'],cwd=WORK,text=True)
    assert digest(WORK / 'var/v1-08-replacement/consumed_start_check.py') == OBSERVER
    log_path = launch / '20252026.log'
    log = log_path.read_text()
    timing = re.search(r'(\d+\.\d+) real\s+(\d+\.\d+) user\s+(\d+\.\d+) sys',log)
    assert timing
    member_bytes = sum((NEW / row['path']).stat().st_size for row in manifest['files'])
    assert member_bytes == manifest['resources']['output_bytes']
    result = dict(kind='replacement-real-year5-saved-state-acceptance', status='saved_state_checks_passed; root independent acceptance pending',
        recorded_at_utc=datetime.now(timezone.utc).isoformat(), manifest=identity(state.path), previous=identity(PREVIOUS / 'manifest.json'), original=identity(OLD / 'manifest.json'),
        recipe={key:manifest['recipe'][key] for key in ('name','version','sha256')}, strict_read=dict(invocations_here=1,status='passed',wall_seconds=strict_seconds,upstream_source_reads=0),
        heads=heads, probes=probes, coverage=dict(original_core_exact=True, optional_start_support_matches_actual_head_metadata=True,
                                  recognized=len(state.coverage['attempts']), games=len(state.coverage['games'])),
        source=dict(report=identity(source_path), source_contexts=source['source_contexts'], known_expected=0, known_checked=0,
                    dispositions=source['dispositions'], eligibility_counts=source['eligibility_counts'], source_context_sha256=source['source_context_sha256'],
                    source_response_sha256=source['source_response_sha256'], observer_seconds=source['observer_seconds'], observer_scope='observe body only, not total wrapper overhead'),
        resources=dict(whole_command_wall_seconds=float(timing[1]),user_seconds=float(timing[2]),system_seconds=float(timing[3]),
                       maximum_resident_bytes=int(re.search(r'(\d+)\s+maximum resident set size',log).group(1)),
                       peak_memory_footprint_bytes=int(re.search(r'(\d+)\s+peak memory footprint',log).group(1)),producer=manifest['resources'],
                       producer_wall_scope=manifest['resources']['wall_scope'],member_bytes=member_bytes,complete_bytes=member_bytes+state.path.stat().st_size,
                       checker_wall_seconds=perf_counter()-began,checker_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        launch=dict(head=launch_head,producer_head=manifest['implementation']['git_commit'],analysis_tree=ANALYSIS,observer_sha256=OBSERVER,
                    start=(launch/'20252026-start.txt').read_text().strip(),finish=(launch/'20252026-finish.txt').read_text().strip(),exit=0,log=identity(log_path)),checker=identity(Path(__file__).resolve()),
        limits=['only accepted replacement 2024 raw last-supported ledger enters current priors, including any retained 2021 through 2023 anchors; original 2025 is comparison evidence, never a prior or fallback',
                'incoming gaps of one through four years are admissible; only actual counts and witnesses are reported; absent/prior-only actors do not advance history',
                'native ftol completion is accepted; raw gradients/objectives are recorded without a new gtol-only gate or scientific-quality claim',
                'saved metadata equality does not independently reconstruct every raw source feature; no original raw context digest exists',
                'missingness counters overlap and do not identify all newly masked keys; unresolved binding and unsaved alternative anchors have the existing stated limits',
                'exactly four final continuations are read from saved files; no new continuation, source or probability replay; final scoring propagation and all real spatial fits remain pending'],
        access='one new strict saved-state read; accepted replacement 2024 and original 2025 manifests/head metadata and original coverage only; no extra predecessor/original strict read, old arrays, source game, source pass, fit, score or production edit',
        next='root reviews completed year 5 state and explicitly releases the next ordinary stage')
    with args.out_check.open('x') as stream:
        json.dump(result,stream,allow_nan=False,indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=result['status'],receipt=identity(args.out_check),strict_read_seconds=strict_seconds,checker_wall_seconds=result['resources']['checker_wall_seconds'])),flush=True)


if __name__ == '__main__':
    main()
