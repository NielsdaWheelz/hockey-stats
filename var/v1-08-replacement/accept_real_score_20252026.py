"""one year-five saved-score read and old/new accounting; no source pass."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
from itertools import groupby, permutations, zip_longest
import json
from math import fsum, isfinite
from pathlib import Path
import re
import resource
import subprocess
from time import perf_counter

import numpy as np
from hockey_stats.execution_scores import FIELDS, HEADS, PREFIXES, STAGES, STATE_FIELDS, STRENGTHS, _near, read_execution_scores

WORK = Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
CAMPAIGN = Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real')
NEW = CAMPAIGN / 'scores/20252026'
OLD = Path('/Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/current-04/scores/20252026')
ANALYSIS = 'c2412ac713b8c60e808dd71771f0812224b94439'
PREVIOUS = '1ba2c8af310d12239d6cabb89ee6cc92b6b98bd95e6834b4f44e303802a44cfe'
RECIPE = '47691110ac34bf7d63cdc32664335bd6579a5953545f0cefa8ebf0257bf88674'
OBSERVER = '286b34dd95ae9cf60a562ad9ec6426000d04a9e658ee3977b7b88080099fedaf'
REFERENCES = ('actor', 'neutral', 'neutral_goalie')
GROUPS = ('shooter', 'setter', 'goalie', 'coach')
PARITY_FIELDS = ('source_context_sha256', 'source_response_sha256', 'source_contexts', 'dispositions',
                 'all_strength_dispositions', 'eligibility_counts', 'head_admission', 'head_populations')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def identity(path):
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def read(path):
    return json.loads(path.read_bytes())


def bound_json(root, manifest, name):
    payload = (root / name).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == next(row['sha256'] for row in manifest['files'] if row['path'] == name)
    return json.loads(payload)


def rows(root, manifest, name):
    """hash each original/current jsonl as it is consumed, without a second pass."""
    expected = next(row['sha256'] for row in manifest['files'] if row['path'] == name)
    hashed = hashlib.sha256()
    with (root / name).open('rb') as stream:
        for line in stream:
            hashed.update(line)
            yield json.loads(line)
    assert hashed.hexdigest() == expected, name


def paired(left, right):
    absent = object()
    for a, b in zip_longest(left, right, fillvalue=absent):
        assert a is not absent and b is not absent, 'saved populations differ in length'
        yield a, b


def probability_fields(row):
    values = {}
    for reference in REFERENCES:
        p = row['prefixes'][reference]
        values.update({f'{reference}.prefix.{name}': value for name, value in p.items()})
        terminal = (1-p['u'], p['u']-p['uq'], p['uq']-p['uqr'], p['uqr']-p['uqrg'], p['uqrg'])
        values.update({f'{reference}.terminal.{name}': value for name, value in
                       zip(('one_minus_u', 'u_minus_uq', 'uq_minus_uqr', 'uqr_minus_uqrg', 'uqrg'), terminal)})
    for name, value in row['conditional_probabilities'].items():
        reference = 'neutral_goalie' if name.startswith('neutral_goalie_') else 'neutral' if name.startswith('neutral_') else 'actor'
        values[f'{reference}.conditional.{name}'] = value
    values.update({f'coalition.{i}': value for i, value in enumerate(row['coalition_goal_mass'])})
    return values


def movement_record():
    return dict(event_maxima=[], numeric_cells=0, null_cells=0, absolute=None, relative=None, zero_baseline_to_nonzero=0, zero_example=None)


def offer(record, locator, old, new):
    delta = new-old
    located = dict(locator, old=old, new=new, signed_change=delta)
    absolute = abs(delta)
    if record['absolute'] is None or absolute > record['absolute']['absolute_change']:
        record['absolute'] = dict(located, absolute_change=absolute)
    if old == 0 and new != 0:
        record['zero_baseline_to_nonzero'] += 1
        if record['zero_example'] is None:
            record['zero_example'] = located
    else:
        relative = absolute/abs(old) if old else 0.
        if record['relative'] is None or relative > record['relative']['relative_change']:
            record['relative'] = dict(located, relative_change=relative)
    record['numeric_cells'] += 1
    return absolute


def summarize(record):
    maxima = record.pop('event_maxima')
    return dict(record, events=len(maxima), event_maximum_absolute_quantiles=None if not maxima else
                dict(zip(('p50', 'p90', 'p99', 'max'), map(float, np.quantile(maxima, [.5, .9, .99, 1.])))))


def check_final_propagation(resolution, *, annual_sha, baseline_ref, annual_selector, annual_heads,
                            panel_records, panels, actual_events, projection_values):
    """reaggregate saved records; no predictor, variant array or source evaluation."""
    budgets = dict(probability=1e-5, per100=1e-3, map_l1=1e-3)
    assert resolution['status'] == 'passed' and resolution['tolerances'] == budgets
    assert resolution['baseline'] == dict(baseline_ref, annual_manifest_sha256=annual_sha)
    event_probes = resolution['event_probes']
    geometry = annual_selector['synthetic_geometry']
    assert geometry['cells'] == list(range(656)) and geometry['execution'] == ['actual', 'neutral']
    assert event_probes == dict(actual_keys=annual_selector['keys'],
        fixture_witnesses=[row['key'] for row in annual_selector['fixture_witnesses']],
        synthetic_geometry=dict(context_key=geometry['context_key'], types=geometry['types'], cells=656))
    keys = event_probes['actual_keys']
    assert 0 < len(keys) <= 256 and len(set(keys)) == len(keys) and set(actual_events) == set(keys)
    baseline_sums = {name: fsum(actual_events[key]['prefixes'][name]['uqrg'] for key in keys) for name in REFERENCES}
    danger = Counter()
    for key in keys:
        value = actual_events[key]['conditional_probabilities']['neutral_on_net_goal_probability']
        danger['<.05' if value < .05 else '[.05,.15)' if value < .15 else '>=.15'] += 1
    selector = resolution['selector']
    pairs = [tuple(pair) for pair in selector['pairs']]
    names = [f'{label}:{strength}:{side}' for strength in STRENGTHS
             for label in ('finishing', 'setting') for side in ('min', 'max')]
    names += [f'{role}:{block}:{kind}' for role in ('F', 'D') for block in ('shooter', 'setter')
              for kind in ('smallest_positive_support', 'first_prior_only')]
    names += [field+':'+side for field in STAGES for side in ('min', 'max')]
    names += ['largest_tip_supported_fraction']
    assert [row['requirement'] for row in selector['requirements']] == names
    assert len(pairs) <= 45 and len(set(pairs)) == len(pairs)
    assert pairs == sorted(pairs, key=lambda pair: (STRENGTHS.index(pair[1]), pair[0]))
    assert set(pairs) <= projection_values.keys()
    for requirement in selector['requirements']:
        assert requirement['disposition'] in ('selected', 'unavailable')
        assert (requirement['pair'] is None) == (requirement['disposition'] == 'unavailable')
    assert {tuple(row['pair']) for row in selector['requirements'] if row['pair'] is not None} == set(pairs)
    assert len(panel_records) == 32 and list(panels) == [row['panel_id'] for row in panel_records]
    public_panels = {f"{row['state']['attacking_skaters']}v{row['state']['defending_skaters']}": row['panel_id']
                     for row in panel_records if row['state']['attacking_goalies'] == 1}
    assert [row['head'] for row in resolution['probes']] == list(HEADS)
    heads = {}
    for probe in resolution['probes']:
        head = probe['head']
        annual_resolution = annual_heads[head]['resolution']
        assert annual_resolution['status'] == 'passed' and annual_resolution['baseline'] == baseline_ref
        assert probe['status'] == 'passed' and probe['probe'] == annual_resolution['probe']
        actual = probe['actual_keys']
        assert actual['population']['keys'] == len(keys) and actual['baseline_danger'] == dict(danger)
        assert type(actual['danger_crossings']) is int and 0 <= actual['danger_crossings'] <= len(keys)
        assert set(actual['expected_sums']) == set(REFERENCES)
        for name, value in actual['expected_sums'].items():
            assert value['baseline'] == baseline_sums[name]
            assert isfinite(value['variant']) and 0 <= value['variant'] <= len(keys)
            assert value['change'] == value['variant']-value['baseline']
        assert [row['panel_id'] for row in probe['neutral_panels']] == list(panels)
        panel_changes = {}
        for row, record in zip(probe['neutral_panels'], panel_records, strict=True):
            panel = panels[row['panel_id']]
            assert row['events'] == panel['rows'] == record['events']
            assert set(row['baseline']) == set(row['variant']) == set(PREFIXES)
            for prefix in PREFIXES:
                expected = panel['new'].get('neutral.'+prefix, 0.)
                assert _near(row['baseline'][prefix], expected, record['origins'])
                assert isfinite(row['variant'][prefix]) and 0 <= row['variant'][prefix] <= row['events']
            assert row['uqrg_change'] == row['variant']['uqrg']-row['baseline']['uqrg']
            panel_changes[row['panel_id']] = row['uqrg_change']
        assert [tuple(row['pair']) for row in probe['pairs']] == pairs
        maxima = dict(stage=0., per100=0., map_l1=0.)
        for comparison, pair in zip(probe['pairs'], pairs, strict=True):
            assert comparison['status'] == 'passed'
            changes = comparison['scalar_absolute_changes']
            assert set(changes) == set(FIELDS)
            for field in FIELDS:
                value = changes[field]
                assert (value is None) == (projection_values[pair][field] is None)
                if value is not None:
                    kind = 'per100' if field in FIELDS[:2] else 'stage'
                    assert isfinite(value) and 0 <= value <= budgets['per100' if kind == 'per100' else 'probability']
                    maxima[kind] = max(maxima[kind], value)
            assert set(comparison['native_map_l1_changes']) == {'finishing', 'setting'}
            for kind, field in zip(('finishing', 'setting'), FIELDS[:2], strict=True):
                value = comparison['native_map_l1_changes'][kind]
                assert (value is None) == (projection_values[pair][field] is None)
                if value is not None:
                    assert isfinite(value) and 0 <= value <= budgets['map_l1']
                    maxima['map_l1'] = max(maxima['map_l1'], value)
            assert comparison['neutral_panel_goal_mass_change'] == panel_changes[public_panels[pair[1]]]
        saved = probe['maximum_changes']
        assert set(saved) == {'actual_probability', 'synthetic_probability', 'posterior_diagnostic', *maxima}
        assert all(saved[kind] == value for kind, value in maxima.items())
        for kind in ('actual_probability', 'synthetic_probability'):
            assert isfinite(saved[kind]) and 0 <= saved[kind] <= budgets['probability']
        assert saved['posterior_diagnostic'] is None or (isfinite(saved['posterior_diagnostic']) and 0 <= saved['posterior_diagnostic'] <= 1)
        heads[head] = dict(status='passed', probe=probe['probe'], producer_saved_maximum_changes=saved,
            independently_reaggregated_pair_maxima=maxima, actual_keys=actual,
            neutral_panels=[dict(panel_id=key, events=panels[key]['rows'], signed_goal_change=value)
                            for key, value in panel_changes.items()], compared_pairs=len(pairs))
    return dict(status='passed', baseline=resolution['baseline'], budgets=budgets, heads=heads,
        event_selector=dict(actual_keys=len(keys), keys_sha256=hashlib.sha256(json.dumps(keys, separators=(',', ':')).encode()).hexdigest(),
            fixture_witnesses=event_probes['fixture_witnesses'], synthetic_geometry=event_probes['synthetic_geometry'],
            annual_requirements=annual_selector['requirements'],
            annual_requirement_dispositions=dict(Counter(row['disposition'] for row in annual_selector['requirements']))),
        focal_selector=selector,
        independent_scope='saved event baseline sums/danger bins; all32 panel baseline sums and signed delta arithmetic; frozen pair membership/nullability and aggregate maxima from saved pair summaries',
        producer_saved_scope='actual/synthetic probability maxima, posterior diagnostic, variant sums, per-pair scalar deltas/map l1 and danger crossings depend on unsaved variant predictions; not independently recomputed here',
        limits='all-event coverage applies to neutral panel sums only; bounded event/pair checks are not seasonwide actor per-event or all-player bounds; no posterior threshold or fixed total-xg budget')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--expected-manifest-sha256', required=True)
    parser.add_argument('--expected-state-sha256', required=True)
    parser.add_argument('--expected-source-sha256', required=True)
    parser.add_argument('--expected-fit-source-sha256', required=True)
    parser.add_argument('--out-check', type=Path, required=True)
    args = parser.parse_args()
    assert not args.out_check.exists()
    assert all(re.fullmatch('[0-9a-f]{64}', value) for value in
               (args.expected_manifest_sha256, args.expected_state_sha256, args.expected_source_sha256, args.expected_fit_source_sha256))
    assert (CAMPAIGN / 'score-20252026.exit').read_text().strip() == '0'
    assert sha(NEW / 'manifest.json') == args.expected_manifest_sha256
    began = perf_counter()
    scores = read_execution_scores(NEW, 'real')
    strict_seconds = perf_counter()-began
    print(json.dumps(dict(strict_read='passed', wall_seconds=strict_seconds)), flush=True)
    current, original = scores.manifest, read(OLD / 'manifest.json')
    assert sha(OLD / 'manifest.json') == '580f85fb2844fabf1d05d26e707438600e9e504fe005410406dd790c2e2ba56c'
    assert current['season'] == original['season'] == '20252026' and current['purpose'] == original['purpose'] == 'real'
    assert all(current[name] == original[name] for name in ('prepared', 'coaches', 'training_cutoff', 'panels', 'scoring_version'))
    assert current['recipe']['sha256'] == RECIPE and current['state']['sha256'] == args.expected_state_sha256
    assert current['state']['path'] == str(CAMPAIGN / 'execution/20252026/manifest.json')
    assert sha(Path(current['state']['path'])) == args.expected_state_sha256
    assert current['state']['previous'] == dict(path=str(CAMPAIGN / 'execution/20242025/manifest.json'), sha256=PREVIOUS)
    assert current['prepared']['sha256'] == '63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c'
    assert current['coaches']['sha256'] == '102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0'
    for name in ('people.jsonl', 'coach_ids.jsonl'):
        old_hash = next(row['sha256'] for row in original['files'] if row['path'] == name)
        assert old_hash == next(row['sha256'] for row in current['files'] if row['path'] == name) == sha(OLD / name)
    assert scores.coverage == read(OLD / 'coverage.json')
    assert sha(OLD / 'coverage.json') == next(row['sha256'] for row in original['files'] if row['path'] == 'coverage.json')
    assert scores.resolution['status'] == current['numerical_resolution']['status'] == 'passed'
    annual_root = Path(current['state']['path']).parent
    annual = read(annual_root / 'manifest.json')
    assert all(annual[name] == current[name] for name in ('purpose', 'season', 'prepared', 'coaches', 'recipe', 'training_cutoff'))
    assert annual['previous']['sha256'] == PREVIOUS
    annual_heads = {head: bound_json(annual_root, annual, f'heads/{head}.json') for head in HEADS}
    baseline_ref = annual_heads['u']['resolution']['baseline']
    baseline = bound_json(annual_root, annual, baseline_ref['path'])
    assert sha(annual_root / baseline_ref['path']) == baseline_ref['sha256']
    assert baseline['identity'] == {key: value for key, value in annual.items() if key not in ('heads', 'files', 'resources')}
    for head in HEADS:
        metadata = annual_heads[head]
        assert metadata['status'] == 'complete' and metadata['resolution']['status'] == 'passed'
        assert metadata['resolution']['baseline'] == baseline_ref
        reference = metadata['resolution']['probe']
        document = bound_json(annual_root, annual, reference['path'])
        assert reference['sha256'] == sha(annual_root / reference['path'])
        assert document['usage'] == 'numerical_probe' and document['head'] == head and document['baseline'] == baseline_ref
        assert document['comparison'] == metadata['resolution']['comparison']
        assert document['arrays']['sha256'] == next(row['sha256'] for row in annual['files'] if row['path'] == document['arrays']['path'])
    actual_keys = set(scores.resolution['event_probes']['actual_keys'])
    actual_events = {}
    fit_source_path = CAMPAIGN / 'fit-20252026-source-check.json'
    source_path = CAMPAIGN / 'score-20252026-source-check.json'
    assert sha(fit_source_path) == args.expected_fit_source_sha256 and sha(source_path) == args.expected_source_sha256
    fit_source, source = read(fit_source_path), read(source_path)
    for report in (fit_source, source):
        assert report['status'] == 'passed' and report['before_head_construction']
        assert report['purpose'] == 'real' and report['season'] == '20252026' and report['recipe_sha256'] == RECIPE
        assert report['known_expected'] == report['known_checked'] == 0 and report['known_witnesses'] == []
    parity = {field: fit_source[field] == source[field] for field in PARITY_FIELDS}
    assert all(parity.values())
    assert source['command'] == ['score', '--family', 'execution', '--prepared', str(Path(current['prepared']['path']).parent),
                                 '--coaches', current['coaches']['path'], '--state', str(CAMPAIGN / 'execution/20252026'), '--out', str(NEW)]
    named = {row['key'] for row in source['first_witnesses']
             if all(row['consumed'][name]['status'] == 'unavailable' for name in
                    ('shooter_start_zone:offensive', 'shooter_start_zone:neutral', 'shooter_start_zone:defensive'))}
    strata = {name: {group: movement_record() for group in (*REFERENCES, 'coalition', 'all')}
              for name in ('all_complete', 'located_unavailable_witnesses', 'remainder_excluding_named_witnesses')}
    stratum_counts = Counter()
    seen, named_complete, named_excluded = set(), set(), []
    panels = {row['panel_id']: dict(rows=0, old=defaultdict(list), new=defaultdict(list)) for row in current['panels']}
    panel_ids = {tuple(row['state'][name] for name in STATE_FIELDS): row['panel_id'] for row in current['panels']}
    # enumerate all 24 orders independently of the production factorial-weight owner.
    weights = np.zeros((4, 16), dtype=float)
    for order in permutations(range(4)):
        subset = 0
        for group in order:
            weights[group, subset] -= 1/24
            subset |= 1 << group
            weights[group, subset] += 1/24
    shares = [iter(groupby(rows(root, manifest, 'shares.jsonl'), key=lambda row: (row['game_id'], row['source_index'])))
              for root, manifest in ((OLD, original), (NEW, current))]
    setters = [iter(groupby(rows(root, manifest, 'setters.jsonl'), key=lambda row: (row['game_id'], row['source_index'])))
               for root, manifest in ((OLD, original), (NEW, current))]
    closure_max = permutation_max = 0.
    recognized = complete = branches = share_rows = 0
    head_counts = {head: Counter() for head in HEADS}
    identity_fields = ('season', 'game_id', 'source_index', 'key', 'shooter_id', 'goalie_id', 'attacking_coach_id',
                       'defending_coach_id', 'physical_state', 'shot_type', 'outcome', 'heads', 'status', 'reasons')
    for old, new in paired(rows(OLD, original, 'events.jsonl'), scores.events()):
        recognized += 1
        assert all(old[name] == new[name] for name in identity_fields), new['key']
        for head, disposition in new['heads'].items():
            head_counts[head]['included' if disposition['included'] else 'excluded'] += 1
            if disposition['included']:
                head_counts[head]['class:'+str(int(disposition['target']))] += 1
        if new['key'] in named:
            seen.add(new['key'])
        if new['status'] != 'complete':
            assert old == new
            if new['key'] in named:
                named_excluded.append(dict(key=new['key'], reasons=new['reasons']))
            continue
        complete += 1
        key = new['key']
        if key in actual_keys:
            actual_events[key] = new
        if key in named:
            named_complete.add(key)
        populations = ['all_complete', 'located_unavailable_witnesses' if key in named else 'remainder_excluding_named_witnesses']
        for population in populations:
            stratum_counts[population] += 1
        old_values, new_values = probability_fields(old), probability_fields(new)
        assert old_values.keys() == new_values.keys()
        event_maxima = {group: 0. for group in (*REFERENCES, 'coalition', 'all')}
        for field, before in old_values.items():
            after = new_values[field]
            assert (before is None) == (after is None), (key, field)
            group = field.split('.')[0]
            if before is None:
                for population in populations:
                    for name in (group, 'all'):
                        strata[population][name]['null_cells'] += 1
                continue
            for population in populations:
                for name in (group, 'all'):
                    offer(strata[population][name], dict(key=key, physical_state=new['physical_state'], field=field), before, after)
            event_maxima[group] = max(event_maxima[group], abs(after-before))
            event_maxima['all'] = max(event_maxima['all'], abs(after-before))
        for population in populations:
            for group, value in event_maxima.items():
                strata[population][group]['event_maxima'].append(value)
        panel = panels[panel_ids[tuple(new['physical_state'])]]
        panel['rows'] += 1
        for label, event in (('old', old), ('new', new)):
            for prefix in PREFIXES:
                panel[label]['neutral.'+prefix].append(event['prefixes']['neutral'][prefix])
            for reference in ('actor', 'neutral_goalie'):
                panel[label][reference+'.uqrg'].append(event['prefixes'][reference]['uqrg'])
        order = (new['game_id'], new['source_index'])
        candidate_rows = []
        for iterator in setters:
            parent, values = next(iterator)
            assert parent == order
            candidate_rows.append(list(values))
        for before, after in paired(*candidate_rows):
            assert all(before[name] == after[name] for name in before if name != 'posterior_weight')
            assert (before['posterior_weight'] is None) == (after['posterior_weight'] is None)
        branches += len(candidate_rows[1])
        allocations = []
        for iterator, event in zip(shares, (old, new)):
            parent, values = next(iterator)
            assert parent == order
            values = list(values)
            allocations.append(values)
            closure_max = max(closure_max, abs(fsum(row['goals'] for row in values)-
                                              (event['prefixes']['actor']['uqrg']-event['prefixes']['neutral']['uqrg'])))
            for i, group in enumerate(GROUPS):
                expected = fsum(float(weight)*mass for weight, mass in zip(weights[i], event['coalition_goal_mass']))
                actual = fsum(row['goals'] for row in values if row['group'] == group)
                permutation_max = max(permutation_max, abs(expected-actual))
        assert [(row['group'], row['recipient_id']) for row in allocations[0]] == [(row['group'], row['recipient_id']) for row in allocations[1]]
        share_rows += len(allocations[1])
    assert seen == named and complete == scores.coverage['complete'] and recognized == scores.coverage['recognized']
    for head, counts in head_counts.items():
        assert all(count == source['head_admission'][head][name] for name, count in counts.items())
    assert closure_max <= 3e-14 and permutation_max <= 3e-14
    assert all(next(iterator, None) is None for iterator in (*shares, *setters))
    for panel in panels.values():
        for label in ('old', 'new'):
            panel[label] = {key: fsum(values) for key, values in panel[label].items()}
    print(json.dumps(dict(events='passed', recognized=recognized, complete=complete, closure_max=closure_max,
                          independent_24_order_group_error=permutation_max)), flush=True)
    projection_values = {}
    scalar_changes = defaultdict(movement_record)
    projections = 0
    public = {f"{row['state']['attacking_skaters']}v{row['state']['defending_skaters']}": row
              for row in current['panels'] if row['state']['attacking_goalies'] == 1
              and f"{row['state']['attacking_skaters']}v{row['state']['defending_skaters']}" in ('5v5','5v4','5v3','4v3','4v5','3v5','3v4')}
    for old, new in paired(rows(OLD, original, 'projections.jsonl'), scores.projections()):
        projections += 1
        assert all(old[name] == new[name] for name in ('season', 'player_id', 'strength', 'unavailable', 'coefficient_support', 'support'))
        panel_record = public[new['strength']]
        for label, row in (('old', old), ('new', new)):
            reference = row['reference_panel']
            assert reference['panel_id'] == panel_record['panel_id'] and reference['opportunities'] == panels[reference['panel_id']]['rows']
            for prefix in PREFIXES:
                expected = panels[reference['panel_id']][label].get('neutral.'+prefix, 0.)
                assert _near(reference['neutral'][prefix], expected, panel_record['origins'])
        for field, before in old['values'].items():
            after = new['values'][field]
            assert (before is None) == (after is None)
            record = scalar_changes[field]
            if before is None:
                record['null_cells'] += 1
            else:
                change = offer(record, dict(player_id=new['player_id'], strength=new['strength'], field=field), before, after)
                record['event_maxima'].append(change)
        projection_values[new['player_id'], new['strength']] = new['values']
    scalar_summaries = {}
    for field, record in scalar_changes.items():
        summary = summarize(record)
        summary['available_projection_pairs'] = summary.pop('events')
        summary['scalar_absolute_change_quantiles'] = summary.pop('event_maximum_absolute_quantiles')
        scalar_summaries[field] = summary
    map_changes = {kind: dict(l1_values=[], unavailable_pairs=0, maximum=None) for kind in ('finishing', 'setting')}
    maps = 0
    for old, new in paired(rows(OLD, original, 'maps.jsonl'), rows(NEW, current, 'maps.jsonl')):
        maps += 1
        assert all(old[name] == new[name] for name in ('season', 'player_id', 'strength', 'map_kind', 'panel_id'))
        assert (old['cells'] is None) == (new['cells'] is None)
        record = map_changes[new['map_kind']]
        if new['cells'] is None:
            record['unavailable_pairs'] += 1
            continue
        field = 'finishing_goals_per100_attempts' if new['map_kind'] == 'finishing' else 'setting_goals_per100_assisted_opportunities'
        assert fsum(old['cells']) == old['integrated_value'] and fsum(new['cells']) == new['integrated_value']
        assert new['integrated_value'] == projection_values[new['player_id'], new['strength']][field]
        l1 = fsum(abs(after-before) for before, after in zip(old['cells'], new['cells'], strict=True))
        record['l1_values'].append(l1)
        if record['maximum'] is None or l1 > record['maximum']['native_map_l1']:
            cell = int(np.argmax(np.abs(np.asarray(new['cells'])-old['cells'])))
            record['maximum'] = dict(player_id=new['player_id'], strength=new['strength'], map_kind=new['map_kind'], native_map_l1=l1,
                                     old_integrated=old['integrated_value'], new_integrated=new['integrated_value'],
                                     largest_cell=cell, old_cell=old['cells'][cell], new_cell=new['cells'][cell])
    propagation = check_final_propagation(scores.resolution, annual_sha=args.expected_state_sha256,
        baseline_ref=baseline_ref, annual_selector=baseline['selector'], annual_heads=annual_heads,
        panel_records=current['panels'], panels=panels, actual_events=actual_events, projection_values=projection_values)
    launch_head = (CAMPAIGN / 'score-20252026-launch-head.txt').read_text().strip()
    assert (CAMPAIGN / 'score-20252026-launch-analysis-tree.txt').read_text().strip() == ANALYSIS
    assert not (CAMPAIGN / 'score-20252026-launch-analysis-status.txt').read_text()
    assert (CAMPAIGN / 'score-20252026-launch-observer-sha256.txt').read_text().split()[0] == OBSERVER
    assert (CAMPAIGN / 'score-20252026-launch-state-sha256.txt').read_text().split()[0] == args.expected_state_sha256
    assert (CAMPAIGN / 'score-20252026-expected-recipe-sha256.txt').read_text().strip() == RECIPE
    for name in ('prepared', 'coaches'):
        assert (CAMPAIGN / f'score-20252026-launch-{name}-sha256.txt').read_text().split()[0] == current[name]['sha256']
    for head in (launch_head, current['implementation']['git_commit'], 'HEAD'):
        assert subprocess.check_output(['git', 'rev-parse', head+':analysis'], cwd=WORK, text=True).strip() == ANALYSIS
    assert not current['implementation']['git_dirty']
    assert not subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all', '--', 'analysis'], cwd=WORK, text=True)
    assert sha(WORK / 'var/v1-08-replacement/consumed_start_check.py') == OBSERVER
    log_path = CAMPAIGN / 'score-20252026.log'
    log = log_path.read_text()
    timing = re.search(r'(\d+\.\d+) real\s+(\d+\.\d+) user\s+(\d+\.\d+) sys', log)
    assert timing
    member_bytes = sum((NEW / row['path']).stat().st_size for row in current['files'])
    assert member_bytes == current['resources']['output_bytes']
    assert maps == 2*projections == 2*current['resources']['projections']
    assert current['resources']['recognized_events'] == recognized and current['resources']['complete_events'] == complete
    assert current['resources']['setter_branches'] == branches
    assert current['resources']['projected_skaters'] == len({pid for pid,strength in projection_values})
    assert current['resources']['origin_rows'] == sum(row['origins'] for row in current['panels'])
    receipt = dict(kind='replacement-real-year5-score-saved-artifact-acceptance', status='saved_artifact_checks_passed; root independent acceptance pending',
        recorded_at_utc=datetime.now(timezone.utc).isoformat(), manifest=identity(NEW / 'manifest.json'), original_manifest=identity(OLD / 'manifest.json'),
        recipe={name: current['recipe'][name] for name in ('name', 'version', 'sha256')}, state=current['state'],
        strict_read=dict(invocations_here=1, status='passed', wall_seconds=strict_seconds, all32panels=True, upstream_source_reads=0),
        source_parity=dict(fields=parity, fit_report=identity(fit_source_path), score_report=identity(source_path)),
        final_propagation=propagation,
        population=dict(recognized=recognized, complete=complete, excluded=recognized-complete,
                        heads={head:dict(head_counts[head], physical_attempts=source['head_populations'][head]['physical_attempts'],
                                         key_sha256=source['head_populations'][head]['key_sha256'],
                                         eligibility_counts=source['head_populations'][head]['eligibility_counts']) for head in HEADS},
                        labels_statuses_reasons_identities_exact_original=True, coverage_exact_original=True,
                        source_contexts=source['source_contexts'], physical5v5_events=public['5v5']['events'],
                        projections=projections, maps=maps, setter_branches=branches, share_rows=share_rows),
        accounting=dict(share_closure_max=closure_max, independent24order_group_error=permutation_max,
                        native_map_scalar_closure='all available old/new saved maps exact', neutral_panel_sums='all seven published panels reconcile event sums to every projection; strict reader covers all32 saved logits'),
        probability_movement={population: dict(rows=stratum_counts[population], groups={group: summarize(record) for group, record in groups.items()})
                              for population, groups in strata.items()},
        movement_definition=dict(absolute='abs(new-old); quantiles of each event maximum across the named probability fields',
                                 relative='abs(new-old)/abs(old); 0 to 0 is 0 by convention; zero baseline to nonzero cells recorded separately and have no finite relative ceiling',
                                 fields='all saved prefix/conditional probabilities, goal masses for 16 coalitions, and terminal partitions reconstructed from prefixes; u is avoid-block, only uqrg is goal',
                                 partition='saved unavailable first witnesses and every other complete row; no census or inference of missingness from probability movement'),
        aggregate_missingness=dict(eligibility_counts=source['eligibility_counts'],
                                  unavailable_by_head={head:sum(value for name,value in source['head_populations'][head]['dispositions'].items()
                                                                if name.startswith('unavailable:')) for head in HEADS},
                                  exact_newly_masked_key_stratum_available=False, unavailable_both_key_stratum_available=False,
                                  located_witnesses=dict(named=len(named), all_recognized=True, complete=sorted(named_complete), excluded=named_excluded)),
        panel_goal_sums=[dict(panel_id=key, events=value['rows'], old=value['old'], new=value['new'],
                             signed_goal_change={reference:value['new'].get(reference+'.uqrg',0.)-value['old'].get(reference+'.uqrg',0.) for reference in REFERENCES})
                         for key, value in panels.items()],
        standardized_scalar_movement=scalar_summaries,
        native_map_l1_movement={kind:dict(available_pairs=len(record['l1_values']), unavailable_pairs=record['unavailable_pairs'],
                                        quantiles=dict(zip(('p50','p90','p99','max'), map(float,np.quantile(record['l1_values'],[.5,.9,.99,1.])))) if record['l1_values'] else None,
                                        maximum=record['maximum']) for kind,record in map_changes.items()},
        resources=dict(whole_command_wall_seconds=float(timing[1]), user_seconds=float(timing[2]), system_seconds=float(timing[3]),
                       maximum_resident_bytes=int(re.search(r'(\d+)\s+maximum resident set size',log).group(1)),
                       peak_memory_footprint_bytes=int(re.search(r'(\d+)\s+peak memory footprint',log).group(1)),
                       producer=current['resources'], producer_wall_scope=current['resources']['wall_scope'],
                       member_bytes=member_bytes, complete_bytes=member_bytes+(NEW / 'manifest.json').stat().st_size,
                       checker_wall_seconds=perf_counter()-began, checker_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        launch=dict(head=launch_head, producer_head=current['implementation']['git_commit'], analysis_tree=ANALYSIS, observer_sha256=OBSERVER,
                    start=(CAMPAIGN / 'score-20252026-start.txt').read_text().strip(), finish=(CAMPAIGN / 'score-20252026-finish.txt').read_text().strip(), exit=0, log=identity(log_path)),
        checker=identity(Path(__file__).resolve()),
        limits=['old/new movement is descriptive recipe/history sensitivity; current 2025 masking and changed earlier raw history effects are not isolated; bounded propagation is a separate numerical check, not a scientific-quality margin',
                'no year 5 known-key census; aggregate counters and located saved witnesses do not identify every newly masked key or the unavailable-both stratum',
                'all complete scored rows and nullable fields are covered; this is no all-player or individual ability error bound',
                'saved coalition arithmetic does not independently reconstruct source predictors, logits or every origin; strict validation retains those saved-array relationships',
                'eligibility counters overlap; missing binding and saved-witness residual limits remain; no new count or movement threshold',
                'final propagation covers frozen event keys, synthetic rows, selected focal pairs and all32 neutral panel sums; no seasonwide actor per-event or all-player bound'],
        access='one new strict read; original manifest-bound saved events/setters/shares/projections/maps and coverage, final annual/probe JSON metadata and reports/launch metadata; no source game, fit, rescore, source pass or production edit',
        next='root reviews completed year 5 score; later stages remain held until explicit release')
    with args.out_check.open('x') as stream:
        json.dump(receipt, stream, allow_nan=False, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=receipt['status'], receipt=identity(args.out_check), complete=complete, located_complete=len(named_complete),
                          all_probability_max=receipt['probability_movement']['all_complete']['groups']['all']['absolute'],
                          checker_wall_seconds=receipt['resources']['checker_wall_seconds'])), flush=True)


if __name__ == '__main__':
    main()
