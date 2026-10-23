"""annual execution score artifacts and their strict detached reader."""

from collections import Counter
from dataclasses import dataclass, replace
from datetime import date
import json
from math import fsum, isclose, isfinite, log
from pathlib import Path
import re
import resource
from time import perf_counter

import numpy as np

from .artifacts import digest, implementation, require
from .captures import InputContractError, strict_json
from .chance_cli import identity, output_path, read_json
from .execution_composition import compose_results  # spec interface; composition owns its implementation

SCORING_VERSION = 'execution-v1-06-1'
HEADS = ('u', 'q', 'r', 'g')
PREFIXES = ('u', 'uq', 'uqr', 'uqrg')
TYPES = ('wrist', 'snap', 'slap', 'backhand', 'tip', 'other')
OUTCOMES = ('block', 'miss', 'save', 'goal')
STRENGTHS = ('5v5', '5v4', '5v3', '4v3', '4v5', '3v5', '3v4')
STATE_FIELDS = ('attacking_skaters', 'defending_skaters', 'attacking_goalies', 'defending_goalies')
PANEL_STATES = tuple((a, d, g) for a in range(3, 7) for d in range(3, 7) for g in (0, 1))
ARRAYS = ('event_offsets', 'origin_cells', 'origin_weights', 'neutral_upstream_logits', 'neutral_goal_logits', 'setup_weights')
FINISHING = 'finishing_goals_per100_attempts'
SETTING = 'setting_goals_per100_assisted_opportunities'
STAGES = ('avoid_block_probability', 'on_net_probability', 'recorded_stop_probability', 'conversion_probability')
FIELDS = (FINISHING, SETTING, *STAGES, *(name + '_difference' for name in STAGES))
CONDITIONALS = {'actor_unblocked_goal_probability': ('actor', 'u'), 'actor_on_net_goal_probability': ('actor', 'uq'),
                'neutral_goalie_on_net_goal_probability': ('neutral_goalie', 'uq'),
                'neutral_on_net_goal_probability': ('neutral', 'uq'), 'neutral_goalie_unblocked_goal_probability': ('neutral_goalie', 'u')}
DANGER = ('<.05', '[.05,.15)', '>=.15')
REASONS = ('not_applicable', 'no_exposure', 'missing_source', 'failed_fit', 'not_computed')
TOLERANCES = dict(probability=1e-5, per100=1e-3, map_l1=1e-3)
TINY = float(np.finfo(float).tiny)
ULP = 2. ** -52
MANIFEST_KEYS = ('schema_version', 'kind', 'purpose', 'season', 'scoring_version', 'recipe', 'implementation', 'prepared',
                 'coaches', 'state', 'training_cutoff', 'panels', 'files', 'coverage', 'resources', 'numerical_resolution')
SINGLE_MEMBERS = {'events.jsonl': 'event', 'setters.jsonl': 'setter', 'shares.jsonl': 'share', 'people.jsonl': 'person',
                  'coach_ids.jsonl': 'coach', 'projections.jsonl': 'projection', 'maps.jsonl': 'map',
                  'coverage.json': 'coverage', 'resolution.json': 'resolution'}
RESOURCE_KEYS = ('wall_seconds', 'input_read_wall_seconds', 'design_wall_seconds', 'scoring_wall_seconds',
                 'projection_wall_seconds', 'resolution_wall_seconds', 'write_wall_seconds', 'wall_scope',
                 'peak_memory_bytes', 'output_bytes', 'panel_array_bytes', 'recognized_events', 'complete_events',
                 'origin_rows', 'setter_branches', 'projections', 'projected_skaters')
WALL_SCOPE = 'input read+prepare_execution+scoring+streamed projection+resolution+members before completion manifest'
NOT_FINAL = dict(status='not_applicable', explanation='bounded propagation applies only to the final annual state')


def _closed(value, keys, label):
    require(type(value) is dict and set(value) == set(keys), f'{label}: invalid fields')


def _number(value, label, *, low=None, high=None):
    require(type(value) in (int, float) and isfinite(value) and (low is None or value >= low)
            and (high is None or value <= high), f'{label}: invalid number')
    return value


def _count(value, label):
    require(type(value) is int and value >= 0, f'{label}: invalid count')
    return value


def _id(value, label):
    require(value is None or type(value) is str and bool(value), f'{label}: invalid identity')
    return value


def _log_error(mass, terms):
    """relative rounding bound of a mass computed as exp of a log-domain sum of `terms` terms.

    each accumulation step adds at most ~2 ulp of absolute log error and exp turns
    absolute log error into relative error, scaled by |log mass|.
    """
    return 0. if mass <= 0 else (abs(log(mass)) + 2 * terms + 8) * ULP


def _near(left, right, terms):
    """two log-domain integrations of the same saved quantity agree within their rounding."""
    return abs(left - right) <= (_log_error(left, terms) + _log_error(right, terms)) * max(left, right) + 2. ** -1072


def _represents(value, numerator, denominator, terms, *, complement=False):
    """a saved ratio against its saved masses wherever the denominator is a normal float.

    a subnormal or zero numerator is quantized by at most 2**-1075, an absolute error
    below ULP once divided by a normal denominator; a subnormal denominator cannot
    represent the ratio, and the stable saved ratio then stands on its own.
    """
    if denominator < TINY:
        return True
    ratio = numerator / denominator
    error = (_log_error(numerator, terms) + _log_error(denominator, terms) + 2 * ULP) * ratio + _log_error(value, terms) * value + ULP
    return abs(value - (1 - ratio if complement else ratio)) <= error


def _season_label(season):
    require(type(season) is str and re.fullmatch(r'20\d{2}20\d{2}', season) is not None
            and int(season[4:]) == int(season[:4]) + 1, 'invalid season')
    return season


def _line(value):
    return json.dumps(value, allow_nan=False, separators=(',', ':')).encode() + b'\n'


def _write_jsonl(path, values):
    with path.open('xb') as target:
        for value in values:
            target.write(_line(value))


def _write_document(path, value):
    with path.open('x', encoding='utf-8') as target:
        target.write(json.dumps(value, allow_nan=False, indent=2) + '\n')


def _decode(path, number, line):
    require(line.endswith(b'\n') and line.strip(), f'{path.name}:{number}: incomplete or blank record')
    try:
        value = strict_json(line)
    except ValueError as error:
        raise InputContractError(f'{path.name}:{number}: invalid finite json: {error}') from error
    require(type(value) is dict, f'{path.name}:{number}: record must be an object')
    return value


def _jsonl(path):
    with path.open('rb') as source:
        for number, line in enumerate(source, 1):
            yield _decode(path, number, line)


def _panel_name(state):
    return '{}v{}g{}'.format(*state)


def _state_record(state):
    return dict(zip(STATE_FIELDS, state, strict=True))


def _public(state):
    label = f'{state[0]}v{state[1]}'
    return label if state[2] == 1 and label in STRENGTHS else None


def _danger(value):
    return DANGER[0] if value < .05 else DANGER[1] if value < .15 else DANGER[2]


DISCREPANCY = 'reported_primary_assistant_outside_pre_outcome_candidate_universe'


def _discrepancies(attempts):
    """located assists outside the frozen pre-outcome universe, copied from the checked design coverage."""
    return [dict(key=row['key'], game_id=row['game_id'], source_index=row['source_index'], code=row['setter_discrepancy'],
                 pointer=row['pointer'])
            for row in sorted(attempts, key=lambda row: (row['game_id'], row['source_index'])) if row['setter_discrepancy'] is not None]


def _coverage(purpose, season, events, panels):
    """one disposition summary, written by the producer and recomputed by the reader."""
    reasons, heads, outcomes, types, states, games = Counter(), Counter(), Counter(), Counter(), Counter(), {}
    for event in events:
        complete = event['status'] == 'complete'
        game = games.setdefault(event['game_id'], Counter())
        game['recognized'] += 1
        game['complete' if complete else 'excluded'] += 1
        outcomes[f"{event['outcome']}:{event['status']}"] += 1
        for head in HEADS:
            heads[f"{head}:{'included' if event['heads'][head]['included'] else 'excluded'}"] += 1
        if complete:
            types[event['shot_type']] += 1
            states[_panel_name(event['physical_state'][:3])] += 1
        else:
            reasons.update({row['code'] for row in event['reasons']})
    recognized = sum(game['recognized'] for game in games.values())
    complete = sum(game['complete'] for game in games.values())
    return dict(purpose=purpose, season=season, recognized=recognized, complete=complete, excluded=recognized - complete,
                reasons=[dict(code=code, count=count) for code, count in sorted(reasons.items())],
                heads=dict(sorted(heads.items())), outcomes=dict(sorted(outcomes.items())), types=dict(sorted(types.items())),
                states=dict(sorted(states.items())),
                games=[dict(game_id=game_id, recognized=row['recognized'], complete=row['complete'], excluded=row['excluded'])
                       for game_id, row in sorted(games.items())],
                panels=[dict(panel_id=row['panel_id'], events=row['events']) for row in panels])


def _event_row(event):
    row = dict(event)
    if row['physical_state'] is not None:
        row['physical_state'] = list(row['physical_state'])
    return row


def _projection_row(projection):
    return {key: projection[key] for key in ('season', 'player_id', 'strength', 'values', 'unavailable', 'reference_panel',
                                             'coefficient_support', 'support')}


def _map_rows(projection):
    for kind, field in (('finishing', FINISHING), ('setting', SETTING)):
        cells = projection['native_maps'][kind]
        yield dict(season=projection['season'], player_id=projection['player_id'], strength=projection['strength'],
                   map_kind=kind, panel_id=projection['reference_panel']['panel_id'],
                   cells=None if cells is None else [float(value) for value in cells],
                   integrated_value=None if cells is None else projection['values'][field])


def _probe_changes(left, right):
    """model-probability and share movement plus separate posterior sensitivity."""
    require(left['event']['status'] == right['event']['status'] == 'complete', 'probe event is not completely scored')
    changes = [0.]
    terminals = lambda p: (1 - p['u'], p['u'] - p['uq'], p['uq'] - p['uqr'], p['uqr'] - p['uqrg'], p['uqrg'])
    for name in ('actor', 'neutral', 'neutral_goalie'):
        a, b = left['event']['prefixes'][name], right['event']['prefixes'][name]
        changes += [abs(a[key] - b[key]) for key in PREFIXES]
        changes += [abs(x - y) for x, y in zip(terminals(a), terminals(b), strict=True)]
    changes += [abs(a - b) for a, b in zip(left['event']['coalition_goal_mass'], right['event']['coalition_goal_mass'], strict=True)]
    for name in CONDITIONALS:
        a, b = left['event']['conditional_probabilities'][name], right['event']['conditional_probabilities'][name]
        require((a is None) == (b is None), 'probe changed conditional applicability')
        if a is not None:
            changes.append(abs(a - b))
    shares = lambda rows: {(row['group'], row['recipient_id']): row['goals'] for row in rows}
    a, b = shares(left['shares']), shares(right['shares'])
    require(a.keys() == b.keys(), 'probe changed share recipients')
    changes += [abs(a[key] - b[key]) for key in a]
    require([(r['candidate_id'], r['pre_outcome_weight']) for r in left['setters']]
            == [(r['candidate_id'], r['pre_outcome_weight']) for r in right['setters']], 'probe changed pre-outcome setter priors')
    posterior = [abs(x['posterior_weight'] - y['posterior_weight']) for x, y in zip(left['setters'], right['setters'], strict=True)
                 if x['posterior_weight'] is not None]
    return max(changes), max(posterior, default=None)


def _actual_probe_summary(baseline, variant, keys):
    """expected sums and fixed neutral danger membership on the exact frozen source keys."""
    sums = lambda rows, name: fsum(row['event']['prefixes'][name]['uqrg'] for row in rows)
    bins = lambda rows: [_danger(row['event']['conditional_probabilities']['neutral_on_net_goal_probability']) for row in rows]
    before, after = bins(baseline), bins(variant)
    return dict(population=dict(keys=len(keys), definition='frozen v1-05 actual final-season probe source keys'),
                expected_sums={name: dict(baseline=sums(baseline, name), variant=sums(variant, name),
                                          change=sums(variant, name) - sums(baseline, name)) for name in ('actor', 'neutral', 'neutral_goalie')},
                baseline_danger=dict(Counter(before)),
                danger_crossings=sum(x != y for x, y in zip(before, after, strict=True)))


def _resolve(state, design, scored, records, people, participation):
    """bounded propagation of the four saved v1-05 tighter heads; no new solve."""
    from . import execution
    from .execution_design import build_resolution_witness
    from .execution_state import read_execution_probe

    for head in HEADS:
        require(state.heads[head]['resolution']['status'] == 'passed', f'v1-05 {head} probe did not pass')
    reference = state.heads['u']['resolution']['baseline']
    baseline_path = state.path.parent / reference['path']
    require(identity(baseline_path)['sha256'] == reference['sha256'], 'frozen v1-05 probe baseline differs')
    selector = read_json(baseline_path)['selector']
    pairs = execution.select_execution_resolution_pairs(records, people, scored['panels'], events=scored['events'])
    predictors = {p.key: p for p in design.predictors}
    dispositions = {row['key']: row for row in design.coverage['attempts']}
    actual = [(key, predictors[key], dispositions[key]) for key in selector['keys']]
    synthetic = []
    for row in selector['requirements']:
        if row['disposition'] == 'fixture' and row['key'] not in {key for key, _, _ in synthetic}:
            _, _, block, actor = row['requirement'].split(':')
            built = build_resolution_witness(design, row['requirement'], block, actor)
            require(built is not None and built[0].key == row['key'], 'frozen synthetic witness cannot be rebuilt')
            synthetic.append((row['key'], built[0], None))
    require([key for key, _, _ in synthetic] == [row['key'] for row in selector['fixture_witnesses']], 'synthetic witnesses differ from the frozen selector')
    context = predictors[selector['synthetic_geometry']['context_key']]
    for shot_type, name in enumerate(TYPES):
        for cell in range(656):
            synthetic.append((f'synthetic:{name}:{cell}', replace(context, key=f'synthetic:{name}:{cell}', shot_type=shot_type,
                                                                   tip=name == 'tip', blocked=False, proxy_cell=cell), None))

    def score(variant, probes):
        return [execution.score_execution_event(variant, predictor, disposition,
                                                facts=design.scoring_facts.get(key) if disposition else None,
                                                observed_setter=design.observed_setters.get(key, -1) if disposition else -1)
                for key, predictor, disposition in probes]

    baseline_actual, baseline_synthetic = score(state, actual), score(state, synthetic)
    selected = [tuple(pair) for pair in pairs['pairs']]
    focal = {}
    for strength in STRENGTHS:
        players = [p for p in people if (p['player_id'], strength) in set(selected)]
        panel = scored['panels'][(int(strength[0]), int(strength[2]), 1)]
        for row in execution.summarize_execution(state, panel, players, participation):
            focal[row['player_id'], strength] = row
    baseline_panels = {key: execution.neutral_panel_masses(panel) for key, panel in scored['panels'].items()}
    probes, passed = [], True
    for head in HEADS:
        variant = read_execution_probe(state, head)
        variant_actual, variant_synthetic = score(variant, actual), score(variant, synthetic)
        actual_changes = [_probe_changes(a, b) for a, b in zip(baseline_actual, variant_actual, strict=True)]
        synthetic_changes = [_probe_changes(a, b) for a, b in zip(baseline_synthetic, variant_synthetic, strict=True)]
        comparisons, panels = [], []
        for key in PANEL_STATES:
            panel = execution.reevaluate_execution_panel(variant, scored['panels'][key], design)
            masses = execution.neutral_panel_masses(panel)
            panels.append(dict(panel_id=panel.panel_id, events=len(panel.events),
                               baseline=baseline_panels[key]['prefixes'], variant=masses['prefixes'],
                               uqrg_change=masses['prefixes']['uqrg'] - baseline_panels[key]['prefixes']['uqrg']))
            strength = _public(key)
            players = [p for p in people if (p['player_id'], strength) in set(selected)]
            for row in execution.summarize_execution(variant, panel, players, participation) if players else ():
                comparisons.append(dict(pair=[row['player_id'], strength],
                                        **execution.compare_execution_projections(focal[row['player_id'], strength], row)))
        comparisons.sort(key=lambda row: selected.index(tuple(row['pair'])))
        changes = dict(
            actual_probability=max((c[0] for c in actual_changes), default=0.),
            synthetic_probability=max((c[0] for c in synthetic_changes), default=0.),
            posterior_diagnostic=max((c[1] for c in actual_changes + synthetic_changes if c[1] is not None), default=None),
            stage=max((c['scalar_absolute_changes'][f] for c in comparisons for f in FIELDS[2:]
                       if c['scalar_absolute_changes'][f] is not None), default=0.),
            per100=max((c['scalar_absolute_changes'][f] for c in comparisons for f in (FINISHING, SETTING)
                        if c['scalar_absolute_changes'][f] is not None), default=0.),
            map_l1=max((c['native_map_l1_changes'][k] for c in comparisons for k in ('finishing', 'setting')
                        if c['native_map_l1_changes'][k] is not None), default=0.))
        status = 'passed' if (max(changes['actual_probability'], changes['synthetic_probability'], changes['stage']) <= TOLERANCES['probability']
                              and changes['per100'] <= TOLERANCES['per100'] and changes['map_l1'] <= TOLERANCES['map_l1']
                              and [tuple(c['pair']) for c in comparisons] == selected
                              and all(c['status'] == 'passed' for c in comparisons)) else 'failed'
        passed &= status == 'passed'
        probes.append(dict(head=head, status=status, probe=state.heads[head]['resolution']['probe'], maximum_changes=changes,
                           actual_keys=_actual_probe_summary(baseline_actual, variant_actual, selector['keys']),
                           neutral_panels=panels, pairs=comparisons))
    return dict(status='passed' if passed else 'failed', baseline=dict(reference, annual_manifest_sha256=identity(state.path)['sha256']),
                selector=pairs,
                event_probes=dict(actual_keys=selector['keys'], fixture_witnesses=[row['key'] for row in selector['fixture_witnesses']],
                                  synthetic_geometry=dict(context_key=context.key, types=list(TYPES), cells=656)),
                probes=probes, tolerances=TOLERANCES,
                scope='frozen bounded pairs and probe keys; no seasonwide actor or all-player error bound')


def write_execution_scores(prepared, coaches, state, output):
    """score one checked annual state; members, internal validation, then the completion manifest."""
    from .analysis_data import read_prepared, read_prepared_game, read_prepared_people
    from .descriptive import execution_participation, summarize_execution_participation
    from . import execution
    from .execution_design import RECIPE
    from .execution_state import read_execution_state

    started = perf_counter()
    prepared_manifest = read_json(Path(prepared) / 'manifest.json' if Path(prepared).is_dir() else Path(prepared))
    require(type(prepared_manifest) is dict and prepared_manifest.get('purpose') in ('real', 'fixture'), 'invalid prepared manifest purpose')
    purpose = prepared_manifest['purpose']
    prepared = read_prepared(prepared, purpose)
    state = read_execution_state(state, purpose)
    require(state.usage == 'annual' and all(state.heads[h]['status'] == 'complete' for h in HEADS), 'scoring requires a complete annual state')
    season = state.manifest['season']
    input_seconds = perf_counter() - started
    output = output_path(str(output), [str(prepared.directory), str(Path(coaches).resolve().parent), str(state.path.parent)])
    began = perf_counter()
    design = execution.prepare_execution(prepared, coaches, RECIPE, season)
    design_seconds = perf_counter() - began
    began = perf_counter()
    scored = execution.score_execution(state, design, None)
    scoring_seconds = perf_counter() - began
    output.mkdir()
    (output / 'panels').mkdir()
    files, panels = [], []
    def bind(path, role):
        files.append(dict(path=path, sha256=identity(output / path)['sha256'], role=role))
    began = perf_counter()
    _write_jsonl(output / 'events.jsonl', (_event_row(event) for event in scored['events']))
    bind('events.jsonl', 'event')
    key = lambda row: (row['season'], row['game_id'], row['source_index'])
    _write_jsonl(output / 'setters.jsonl', sorted(scored['setters'], key=lambda row: (*key(row), row['candidate_id'])))
    bind('setters.jsonl', 'setter')
    _write_jsonl(output / 'shares.jsonl', sorted(scored['shares'], key=lambda row: (*key(row), row['group'], row['recipient_id'])))
    bind('shares.jsonl', 'share')
    people = sorted((dict(season=season, player_id=str(fact['values']['player_id']),
                          kind={'F': 'skater', 'D': 'skater', 'G': 'goalie'}.get(fact['values']['position_group']),
                          position_group=fact['values']['position_group'], name=fact['values']['name'])
                     for fact in read_prepared_people(prepared, season)['people']), key=lambda row: row['player_id'])
    _write_jsonl(output / 'people.jsonl', people)
    bind('people.jsonl', 'person')
    selected = next(row['selected_game_ids'] for row in prepared['seasons'] if row['season'] == season)
    coach_rows = read_json(Path(design.coaches['path']).parent / 'identities.json')['coaches']
    used = {row[side]['coach_id'] for row in read_json(Path(design.coaches['path']))['games']
            if row['season'] == season and row['game_id'] in selected for side in ('home', 'away')} - {None}
    _write_jsonl(output / 'coach_ids.jsonl', sorted((dict(coach_id=row['coach_id'], display_name=row['display_name'])
                                                     for row in coach_rows if row['coach_id'] in used), key=lambda row: row['coach_id']))
    bind('coach_ids.jsonl', 'coach')
    for state_key in PANEL_STATES:
        panel = scored['panels'][state_key]
        name = _panel_name(state_key)
        _write_jsonl(output / f'panels/{name}.jsonl', panel.events)
        bind(f'panels/{name}.jsonl', 'panel_events')
        with (output / f'panels/{name}.npz').open('xb') as target:
            np.savez(target, **{array: panel.arrays[array] for array in ARRAYS})
        bind(f'panels/{name}.npz', 'panel_arrays')
        panels.append(dict(state=_state_record((*state_key, 1)), panel_id=panel.panel_id, events_path=f'panels/{name}.jsonl',
                           arrays_path=f'panels/{name}.npz', events=len(panel.events), origins=len(panel.arrays['origin_cells'])))
    write_seconds = perf_counter() - began
    began = perf_counter()
    participation = summarize_execution_participation(execution_participation(read_prepared_game(prepared, season, game_id))
                                                      for game_id in selected)
    # projections and maps stream panel by panel; only scalar selector records stay in memory.
    records = []
    with (output / 'projections.jsonl').open('xb') as projection_file, (output / 'maps.jsonl').open('xb') as map_file:
        for strength in STRENGTHS:
            panel = scored['panels'][(int(strength[0]), int(strength[2]), 1)]
            for projection in execution.summarize_execution(state, panel, people, participation):
                row = _projection_row(projection)
                projection_file.write(_line(row))
                for map_row in _map_rows(projection):
                    map_file.write(_line(map_row))
                records.append(row)
    bind('projections.jsonl', 'projection')
    bind('maps.jsonl', 'map')
    projection_seconds = perf_counter() - began
    began = perf_counter()
    resolution = _resolve(state, design, scored, records, people, participation) if season == '20252026' else NOT_FINAL
    resolution_seconds = perf_counter() - began
    _write_document(output / 'resolution.json', resolution)
    bind('resolution.json', 'resolution')
    if resolution['status'] == 'failed':
        raise InputContractError(f'{output}: final-year numerical propagation failed ('
                                 + '; '.join(f"{row['head']} {row['status']} {row['maximum_changes']}" for row in resolution['probes'])
                                 + '); resolution.json retained without a completion manifest')
    _write_document(output / 'coverage.json', dict(_coverage(purpose, season, scored['events'], panels),
                                                   setter_discrepancies=_discrepancies(design.coverage['attempts'])))
    bind('coverage.json', 'coverage')
    previous = state.manifest['previous']
    measured = dict(input_read_wall_seconds=input_seconds, design_wall_seconds=design_seconds, scoring_wall_seconds=scoring_seconds,
                    projection_wall_seconds=projection_seconds, resolution_wall_seconds=resolution_seconds,
                    write_wall_seconds=write_seconds, wall_scope=WALL_SCOPE,
                    peak_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    output_bytes=sum((output / row['path']).stat().st_size for row in files),
                    panel_array_bytes=sum(array.nbytes for panel in scored['panels'].values() for array in panel.arrays.values()),
                    recognized_events=len(scored['events']), complete_events=sum(e['status'] == 'complete' for e in scored['events']),
                    origin_rows=sum(row['origins'] for row in panels), setter_branches=len(scored['setters']),
                    projections=len(records), projected_skaters=len({row['player_id'] for row in records}))
    measured['wall_seconds'] = perf_counter() - started
    manifest = dict(schema_version=1, kind='execution-scores', purpose=purpose, season=season, scoring_version=SCORING_VERSION,
                    recipe=state.manifest['recipe'], implementation=implementation(), prepared=state.manifest['prepared'],
                    coaches=state.manifest['coaches'],
                    state=dict(identity(state.path), season=season, purpose=purpose, recipe_sha256=state.manifest['recipe']['sha256'],
                               usage='annual', previous=None if previous is None else {k: previous[k] for k in ('path', 'sha256')}),
                    training_cutoff=state.manifest['training_cutoff'], panels=panels, files=files,
                    coverage=dict(path='coverage.json'), resources=dict(sorted(measured.items())),
                    numerical_resolution=dict(status=resolution['status'], path='resolution.json'))
    manifest = strict_json(_line(manifest))
    scores = _validate(output / 'manifest.json', manifest, purpose)
    _write_document(output / 'manifest.json', manifest)
    return scores


@dataclass(frozen=True)
class ExecutionScores:
    path: Path
    manifest: dict
    people: dict
    coaches: dict
    coverage: dict
    resolution: dict
    map_offsets: dict

    def _member(self, role):
        return self.path.parent / next(row['path'] for row in self.manifest['files'] if row['role'] == role)

    def events(self):
        return _jsonl(self._member('event'))

    def setters(self):
        return _jsonl(self._member('setter'))

    def shares(self):
        return _jsonl(self._member('share'))

    def projections(self):
        return _jsonl(self._member('projection'))

    def native_map(self, player_id, strength, kind):
        path = self._member('map')
        with path.open('rb') as source:
            source.seek(self.map_offsets[player_id, strength, kind])
            return _decode(path, 0, source.readline())


def read_execution_scores(path, expected_purpose):
    """validate saved internal relationships only; provenance locators are never reopened."""
    try:
        path = Path(path).resolve(strict=True)
        path = path / 'manifest.json' if path.is_dir() else path
        require(path.name == 'manifest.json', 'execution scores locator must be manifest.json')
        return _validate(path, read_json(path), expected_purpose)
    except (KeyError, TypeError, ValueError, IndexError, AttributeError) as error:
        if isinstance(error, InputContractError):
            raise
        raise InputContractError(f'malformed execution scores: {error}') from error


def _manifest(value, purpose):
    from .execution_design import RECIPE
    _closed(value, MANIFEST_KEYS, 'score manifest')
    require(value['schema_version'] == 1 and type(value['schema_version']) is int and value['kind'] == 'execution-scores'
            and value['scoring_version'] == SCORING_VERSION, 'invalid execution score schema')
    require(purpose in ('real', 'fixture') and value['purpose'] == purpose, 'execution score purpose differs')
    season = _season_label(value['season'])
    require(season in ('20212022', '20222023', '20232024', '20242025', '20252026'), 'season outside execution scope')
    require(value['recipe'] == RECIPE, 'execution recipe definition differs')
    require(type(value['implementation']) is dict and bool(value['implementation']), 'missing implementation identity')
    _closed(value['prepared'], ('purpose', 'path', 'sha256', 'members'), 'prepared binding')
    _closed(value['coaches'], ('purpose', 'path', 'sha256', 'selected_game_ids'), 'coach binding')
    for name in ('prepared', 'coaches'):
        require(value[name]['purpose'] == purpose and type(value[name]['path']) is str and Path(value[name]['path']).is_absolute(), f'{name}: invalid binding')
        digest(value[name]['sha256'])
    members = value['prepared']['members']
    require(type(members) is list, 'invalid prepared members')
    for row in members:
        _closed(row, ('kind', 'season', 'game_id', 'path', 'sha256'), 'prepared member')
        require(row['season'] == season and row['kind'] in ('game', 'people'), 'cross-season prepared member')
        digest(row['sha256'])
    games = [row['game_id'] for row in members if row['kind'] == 'game']
    require(len(set(games)) == len(games) and value['coaches']['selected_game_ids'] == games
            and sum(row['kind'] == 'people' for row in members) == 1, 'prepared/coach selected games differ')
    state = value['state']
    _closed(state, ('path', 'sha256', 'season', 'purpose', 'recipe_sha256', 'usage', 'previous'), 'state binding')
    digest(state['sha256'])
    require(type(state['path']) is str and Path(state['path']).is_absolute() and Path(state['path']).name == 'manifest.json'
            and state['season'] == season and state['purpose'] == purpose and state['recipe_sha256'] == RECIPE['sha256']
            and state['usage'] == 'annual', 'invalid state binding')
    if state['previous'] is None:
        require(purpose != 'real' or season == '20212022', 'real score chain must begin at 20212022')
    else:
        _closed(state['previous'], ('path', 'sha256'), 'previous state')
        digest(state['previous']['sha256'])
    try:
        cutoff = date.fromisoformat(value['training_cutoff'])
    except (TypeError, ValueError) as error:
        raise InputContractError('invalid training cutoff') from error
    require(int(season[:4]) <= cutoff.year <= int(season[4:]), 'training cutoff outside season')
    require(type(value['panels']) is list and len(value['panels']) == len(PANEL_STATES), 'panels must enumerate all 32 states')
    for row, key in zip(value['panels'], PANEL_STATES):
        _closed(row, ('state', 'panel_id', 'events_path', 'arrays_path', 'events', 'origins'), 'panel binding')
        require(row['state'] == _state_record((*key, 1)) and row['panel_id'] == f'{SCORING_VERSION}:{season}:' + ','.join(map(str, key))
                and row['events_path'] == f'panels/{_panel_name(key)}.jsonl' and row['arrays_path'] == f'panels/{_panel_name(key)}.npz',
                'panel binding differs from its exact state')
        _count(row['events'], 'panel events')
        _count(row['origins'], 'panel origins')
    require(value['coverage'] == dict(path='coverage.json'), 'coverage member binding differs')
    resolution = value['numerical_resolution']
    _closed(resolution, ('status', 'path'), 'numerical resolution')
    require(resolution['path'] == 'resolution.json' and resolution['status'] == ('passed' if season == '20252026' else 'not_applicable'),
            'final annual scores need passed propagation; earlier years are not applicable')
    costs = value['resources']
    _closed(costs, RESOURCE_KEYS, 'resources')
    require(costs['wall_scope'] == WALL_SCOPE, 'resource wall-time scope differs')
    for key in RESOURCE_KEYS:
        if key.endswith('wall_seconds'):
            _number(costs[key], key, low=0.)
        elif key != 'wall_scope':
            _count(costs[key], key)


def _prefix(value, label, upper):
    _closed(value, PREFIXES, label)
    previous = upper
    for key in PREFIXES:
        _number(value[key], label, low=0., high=previous)
        previous = value[key]


def _event(row, games, people, coaches, season):
    _closed(row, ('season', 'game_id', 'source_index', 'key', 'shooter_id', 'goalie_id', 'attacking_coach_id', 'defending_coach_id',
                  'physical_state', 'shot_type', 'outcome', 'heads', 'status', 'reasons', 'prefixes', 'coalition_goal_mass',
                  'conditional_probabilities'), 'event')
    require(row['season'] == season and row['game_id'] in games and type(row['source_index']) is int and row['source_index'] >= 0
            and row['key'] == f"{row['game_id']}:{row['source_index']}", 'event source key differs')
    for field in ('shooter_id', 'goalie_id'):
        require(_id(row[field], field) is None or row[field] in people, f'event {field} does not resolve to a selected person')
    for field in ('attacking_coach_id', 'defending_coach_id'):
        require(_id(row[field], field) is None or row[field] in coaches, f'event {field} does not resolve to a bound coach')
    state = row['physical_state']
    require(state is None or type(state) is list and len(state) == 4 and all(type(x) is int and x >= 0 for x in state), 'invalid physical state')
    require(row['shot_type'] in (None, *TYPES) and row['outcome'] in (None, *OUTCOMES), 'invalid event type/outcome')
    _closed(row['heads'], HEADS, 'event heads')
    for head in HEADS:
        record = row['heads'][head]
        _closed(record, ('included', 'target', 'reasons'), 'head disposition')
        require(type(record['included']) is bool and type(record['reasons']) is list
                and all(type(reason) is str and reason for reason in record['reasons'])
                and (record['target'] in (0., 1.) and type(record['target']) is float and not record['reasons']
                     if record['included'] else record['target'] is None and bool(record['reasons'])), 'invalid head disposition')
    if row['status'] == 'excluded':
        require(row['prefixes'] is None and row['coalition_goal_mass'] is None and row['conditional_probabilities'] is None
                and type(row['reasons']) is list and bool(row['reasons']), 'excluded event invents values or lacks reasons')
        for reason in row['reasons']:
            _closed(reason, ('code', 'game_id', 'source_index', 'pointer'), 'located reason')
            require(type(reason['code']) is str and reason['code'] and reason['game_id'] == row['game_id']
                    and reason['source_index'] == row['source_index'] and type(reason['pointer']) is str
                    and reason['pointer'].startswith('/attempts/'), 'reason is not located at its event')
        return
    require(row['status'] == 'complete' and row['reasons'] == [] and None not in (row['shooter_id'], row['goalie_id'], state,
            row['shot_type'], row['outcome']), 'complete event lacks its full-joint facts')
    require(3 <= state[0] <= 6 and 3 <= state[1] <= 6 and state[2] in (0, 1) and state[3] == 1
            and people[row['goalie_id']]['kind'] == 'goalie', 'complete event lies outside the scored population')
    _closed(row['prefixes'], ('actor', 'neutral', 'neutral_goalie'), 'event prefixes')
    for name in ('actor', 'neutral', 'neutral_goalie'):
        _prefix(row['prefixes'][name], f'{name} prefix', 1.)
    masses = row['coalition_goal_mass']
    require(type(masses) is list and len(masses) == 16, 'coalition masses need sixteen subsets')
    for mass in masses:
        _number(mass, 'coalition goal mass', low=0., high=1.)
    for index, name in ((0, 'neutral'), (11, 'neutral_goalie'), (15, 'actor')):
        require(masses[index] == row['prefixes'][name]['uqrg'], f'coalition {index} differs from {name} goal prefix')
    conditional = row['conditional_probabilities']
    _closed(conditional, CONDITIONALS, 'conditional probabilities')
    applicable = dict(actor_unblocked_goal_probability=row['outcome'] != 'block', actor_on_net_goal_probability=row['outcome'] in ('save', 'goal'),
                      neutral_goalie_on_net_goal_probability=row['outcome'] in ('save', 'goal'),
                      neutral_on_net_goal_probability=True, neutral_goalie_unblocked_goal_probability=True)
    for name, (prefix, denominator) in CONDITIONALS.items():
        require((conditional[name] is not None) == applicable[name], f'{name} outside its observed population')
        if conditional[name] is not None:
            _number(conditional[name], name, low=0., high=1.)
            require(_represents(conditional[name], row['prefixes'][prefix]['uqrg'], row['prefixes'][prefix][denominator],
                                656 if row['outcome'] == 'block' else 1), f'{name} differs from its integrated prefixes')


def _validate(path, manifest, expected_purpose):
    """check one complete artifact from an in-memory manifest before or after it is written."""
    from .execution import ExecutionPanel, neutral_panel_event_masses, neutral_panel_masses

    root = path.parent
    _manifest(manifest, expected_purpose)
    season = manifest['season']
    files = manifest['files']
    require(type(files) is list, 'invalid score members')
    expected = dict(SINGLE_MEMBERS)
    for row in manifest['panels']:
        expected[row['events_path']] = 'panel_events'
        expected[row['arrays_path']] = 'panel_arrays'
    bound = {}
    for row in files:
        _closed(row, ('path', 'sha256', 'role'), 'member binding')
        digest(row['sha256'])
        require(row['path'] not in bound and expected.get(row['path']) == row['role'], 'duplicate, unknown or cross-wired score member')
        member = (root / row['path']).resolve(strict=True)
        require(root in member.parents and member.is_file(), 'score member escapes its artifact')
        require(identity(member)['sha256'] == row['sha256'], f"{row['path']}: score member digest differs")
        bound[row['path']] = member
    require(set(bound) == set(expected), 'score members omitted')
    actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p != path}
    require(actual == set(bound), 'unbound files in execution scores')
    require(manifest['resources']['output_bytes'] == sum(p.stat().st_size for p in bound.values()), 'saved output bytes differ')
    games = set(manifest['coaches']['selected_game_ids'])
    people, previous = {}, None
    for row in _jsonl(root / 'people.jsonl'):
        _closed(row, ('season', 'player_id', 'kind', 'position_group', 'name'), 'person')
        require(row['season'] == season and type(row['player_id']) is str and row['player_id'].isdigit()
                and (previous is None or previous < row['player_id'])
                and row['kind'] in ('skater', 'goalie', None) and row['position_group'] in ('F', 'D', 'G', None)
                and row['kind'] == {'F': 'skater', 'D': 'skater', 'G': 'goalie'}.get(row['position_group'])
                and (row['name'] is None or type(row['name']) is str), 'invalid or unordered selected-year person')
        people[row['player_id']] = row
        previous = row['player_id']
    coaches = {}
    for row in _jsonl(root / 'coach_ids.jsonl'):
        _closed(row, ('coach_id', 'display_name'), 'coach')
        require(type(row['coach_id']) is str and row['coach_id'] and row['coach_id'] not in coaches
                and type(row['display_name']) is str and row['display_name'], 'invalid bound coach')
        coaches[row['coach_id']] = row
    complete, previous, events = {}, None, []
    for row in _jsonl(root / 'events.jsonl'):
        _event(row, games, people, coaches, season)
        key = (row['game_id'], row['source_index'])
        require(previous is None or previous < key, 'events duplicate or are not ordered by source key')
        previous = key
        events.append(dict(key=row['key'], game_id=row['game_id'], status=row['status'], outcome=row['outcome'], heads=row['heads'],
                           shot_type=row['shot_type'], physical_state=row['physical_state'], reasons=row['reasons']))
        if row['status'] == 'complete':
            complete[row['key']] = dict(state=tuple(row['physical_state']), outcome=row['outcome'], shot_type=row['shot_type'],
                                        shooter=row['shooter_id'], goalie=row['goalie_id'], g=row['heads']['g']['included'],
                                        coaches=(row['attacking_coach_id'], row['defending_coach_id']),
                                        neutral=row['prefixes']['neutral'], actor_goal=row['prefixes']['actor']['uqrg'],
                                        neutral_goalie_goal=row['prefixes']['neutral_goalie']['uqrg'],
                                        neutral_on_net=row['conditional_probabilities']['neutral_on_net_goal_probability'])
    coverage = read_json(root / 'coverage.json')
    require(type(coverage) is dict and {k: v for k, v in coverage.items() if k != 'setter_discrepancies'}
            == _coverage(expected_purpose, season, events, manifest['panels']), 'coverage differs from saved event dispositions')
    discrepancies, keys = coverage.get('setter_discrepancies'), {row['key'] for row in events}
    require(type(discrepancies) is list, 'coverage lacks located setter discrepancies')
    previous = None
    for row in discrepancies:
        _closed(row, ('key', 'game_id', 'source_index', 'code', 'pointer'), 'setter discrepancy')
        order = (row['game_id'], row['source_index'])
        require(row['key'] in keys and row['key'] == f"{row['game_id']}:{row['source_index']}" and (previous is None or previous < order)
                and row['code'] == DISCREPANCY and type(row['pointer']) is str and re.fullmatch(r'/attempts/\d+', row['pointer']) is not None,
                'invalid, unknown or unordered setter discrepancy')
        previous = order
    del events
    setters, previous = {}, None
    for row in _jsonl(root / 'setters.jsonl'):
        _closed(row, ('season', 'game_id', 'source_index', 'candidate_id', 'pre_outcome_weight', 'posterior_weight', 'recorded_assist_evidence'), 'setter')
        key = f"{row['game_id']}:{row['source_index']}"
        order = (row['game_id'], row['source_index'], row['candidate_id'])
        require(row['season'] == season and key in complete and (previous is None or previous < order), 'setter parent/order invalid')
        previous = order
        candidate = row['candidate_id']
        require(candidate in ('none', 'unknown') or candidate in people and candidate not in (complete[key]['shooter'], complete[key]['goalie']),
                'setter candidate does not resolve or repeats the shooter or defending goalie')
        _number(row['pre_outcome_weight'], 'setter prior', low=0., high=1.)
        require(row['posterior_weight'] is None or _number(row['posterior_weight'], 'setter posterior', low=0., high=1.) is not None,
                'invalid setter posterior')
        require(row['recorded_assist_evidence'] == [], 'scores carry no recorded assist evidence')
        setters.setdefault(key, []).append(row)
    require(set(setters) == set(complete), 'complete events and setter parents differ')
    for key, rows in setters.items():
        weights = {row['candidate_id']: row['pre_outcome_weight'] for row in rows}
        require(weights.get('none') == .2 and isclose(fsum(weights.values()), 1., abs_tol=1e-12)
                and ('unknown' not in weights or len(weights) == 2), 'setter prior is not .2 none/.8 setup')
        posteriors = [row['posterior_weight'] for row in rows]
        require(all(p is None for p in posteriors) if not complete[key]['g'] else
                all(p is not None for p in posteriors) and isclose(fsum(posteriors), 1., abs_tol=1e-12), 'setter posterior applicability differs')
    shares, previous = {}, None
    for row in _jsonl(root / 'shares.jsonl'):
        _closed(row, ('season', 'game_id', 'source_index', 'group', 'recipient_id', 'goals'), 'share')
        key = f"{row['game_id']}:{row['source_index']}"
        order = (row['game_id'], row['source_index'], row['group'], row['recipient_id'])
        require(row['season'] == season and key in complete and (previous is None or previous < order), 'share parent/order invalid')
        previous = order
        _number(row['goals'], 'share goals', low=-1., high=1.)
        shares.setdefault(key, []).append(row)
    require(set(shares) == set(complete), 'complete events and share parents differ')
    for key, rows in shares.items():
        event = complete[key]
        recipients = {(row['group'], row['recipient_id']) for row in rows}
        expected_recipients = {('shooter', event['shooter']), ('goalie', event['goalie']), ('coach', 'coaching_context')}
        expected_recipients |= {('setter', row['candidate_id']) for row in setters[key]}
        require(recipients == expected_recipients and len(rows) == len(expected_recipients), 'share recipients differ from event actors and setter candidates')
        for row in rows:
            if row['group'] == 'setter' and (row['recipient_id'] in ('none', 'unknown') or people[row['recipient_id']]['kind'] == 'goalie'):
                require(row['goals'] == 0., 'none, unknown or goalie setter receives execution credit')
        require(isclose(fsum(row['goals'] for row in rows), event['actor_goal'] - event['neutral']['uqrg'], rel_tol=0, abs_tol=3e-14),
                'event shares do not close actor minus neutral')
    del setters, shares
    panel_of, neutral = {}, {}
    for record in manifest['panels']:
        state = tuple(record['state'][k] for k in STATE_FIELDS)
        rows = list(_jsonl(root / record['events_path']))
        with np.load(root / record['arrays_path'], allow_pickle=False) as saved:
            require(saved.files == list(ARRAYS), 'panel array names/order differ')
            arrays = {name: saved[name] for name in saved.files}
        n, length = len(rows), len(arrays['origin_cells'])
        shapes = dict(event_offsets=((n + 1,), np.int64), origin_cells=((length,), np.int64), origin_weights=((length,), np.float64),
                      neutral_upstream_logits=((length, 3), np.float64), neutral_goal_logits=((length, 2), np.float64),
                      setup_weights=((n, 2), np.float64))
        require(all(arrays[name].shape == shape and arrays[name].dtype == dtype and np.isfinite(arrays[name]).all()
                    for name, (shape, dtype) in shapes.items()), 'panel arrays differ from their fixed shapes, dtypes or finiteness')
        require(record['events'] == n and record['origins'] == length, 'panel counts differ from members')
        offsets = arrays['event_offsets']
        require(offsets[0] == 0 and offsets[-1] == length and np.all(np.diff(offsets) >= 1), 'panel offsets do not partition rows')
        require(np.all((arrays['origin_cells'] >= 0) & (arrays['origin_cells'] < 656)) and np.all(arrays['origin_weights'] >= 0)
                and np.all(arrays['setup_weights'] == np.array([.2, .8])), 'invalid panel origin cells, masses or setup law')
        for index, row in enumerate(rows):
            _closed(row, ('season', 'game_id', 'source_index', 'key', 'shot_type', 'tip', 'role', 'hand',
                          'attacking_coach_applicable', 'defending_coach_applicable'), 'panel event')
            event = complete.get(row['key'])
            require(event is not None and row['key'] not in panel_of and row['season'] == season
                    and row['key'] == f"{row['game_id']}:{row['source_index']}", 'panel row is not a unique complete event')
            require(event['state'] == (*state[:3], 1), 'panel row differs from its exact physical state')
            require(row['shot_type'] == event['shot_type'] and row['tip'] is (event['shot_type'] == 'tip')
                    and row['role'] in ('F', 'D', 'G', None) and type(row['hand']) in (int, type(None))
                    and row['attacking_coach_applicable'] is (event['coaches'][0] is not None)
                    and row['defending_coach_applicable'] is (event['coaches'][1] is not None), 'panel row tags differ from its event')
            start, end = offsets[index], offsets[index + 1]
            cells = arrays['origin_cells'][start:end]
            require(np.array_equal(cells, np.arange(656)) if event['outcome'] == 'block' else len(cells) == 1,
                    'panel rows need one point origin or all 656 block origins')
            require(isclose(fsum(arrays['origin_weights'][start:end]), 1., abs_tol=1e-12), 'panel origin masses do not sum to one')
            panel_of[row['key']] = record['panel_id']
        panel = ExecutionPanel(record['panel_id'], season, state[:3], tuple(rows), arrays, {}, {})
        for reduced in neutral_panel_event_masses(panel):
            event = complete[reduced['key']]
            terms = 656 if event['outcome'] == 'block' else 1
            require(all(_near(reduced['prefixes'][k], event['neutral'][k], terms) for k in PREFIXES)
                    and _near(reduced['neutral_on_net_goal_probability'], event['neutral_on_net'], terms),
                    'saved panel logits differ from the event neutral prefixes')
        if _public(state[:3]) is not None:
            cell_rows = int(np.bincount(arrays['origin_cells'], minlength=656).max()) if length else 0
            neutral[_public(state[:3])] = dict(record=record, rows=n, origins=length, cell_rows=cell_rows, masses=neutral_panel_masses(panel))
    require(set(panel_of) == set(complete), 'complete events and panel membership differ')
    offsets = _projections(root, season, people, neutral)
    resolution = read_json(root / 'resolution.json')
    if season != '20252026':
        require(resolution == NOT_FINAL, 'earlier annual scores cannot claim propagation')
    else:
        _resolution(resolution, people, complete)
    return ExecutionScores(path, manifest, people, coaches, coverage, resolution, offsets)


def _resolution(value, people, complete):
    """bind the saved propagation receipt to its frozen selector and probe populations."""
    _closed(value, ('status', 'baseline', 'selector', 'event_probes', 'probes', 'tolerances', 'scope'), 'resolution')
    require(value['status'] == 'passed' and value['tolerances'] == TOLERANCES, 'final annual scores need a passed bounded propagation')
    _closed(value['baseline'], ('path', 'sha256', 'annual_manifest_sha256'), 'resolution baseline')
    selector = value['selector']
    _closed(selector, ('pairs', 'requirements', 'tip_fraction_definition', 'scope'), 'resolution selector')
    pairs = [tuple(pair) for pair in selector['pairs']]
    require(len(pairs) <= 45 and len(set(pairs)) == len(pairs)
            and pairs == sorted(pairs, key=lambda pair: (STRENGTHS.index(pair[1]), pair[0]))
            and all(people.get(player, {}).get('kind') == 'skater' for player, _ in pairs), 'invalid frozen focal pairs')
    selected = set()
    for row in selector['requirements']:
        _closed(row, ('requirement', 'pair', 'disposition'), 'pair requirement')
        require(row['disposition'] in ('selected', 'unavailable') and (row['pair'] is None) == (row['disposition'] == 'unavailable'),
                'invalid pair requirement')
        if row['pair'] is not None:
            selected.add(tuple(row['pair']))
    require(selected == set(pairs), 'frozen pairs differ from their requirements')
    probes = value['event_probes']
    _closed(probes, ('actual_keys', 'fixture_witnesses', 'synthetic_geometry'), 'event probes')
    keys = probes['actual_keys']
    require(type(keys) is list and 0 < len(keys) <= 256 and len(set(keys)) == len(keys) and set(keys) <= set(complete),
            'actual probe keys are not unique complete source events')
    require(probes['synthetic_geometry'] == dict(context_key=keys[0], types=list(TYPES), cells=656)
            and all(type(key) is str and key.startswith('synthetic-resolution:') for key in probes['fixture_witnesses']),
            'synthetic probe population differs')
    baseline_sums = dict(actor=fsum(complete[key]['actor_goal'] for key in keys),
                         neutral=fsum(complete[key]['neutral']['uqrg'] for key in keys),
                         neutral_goalie=fsum(complete[key]['neutral_goalie_goal'] for key in keys))
    bins = Counter(_danger(complete[key]['neutral_on_net']) for key in keys)
    require([row['head'] for row in value['probes']] == list(HEADS), 'resolution heads differ')
    for row in value['probes']:
        _closed(row, ('head', 'status', 'probe', 'maximum_changes', 'actual_keys', 'neutral_panels', 'pairs'), 'head propagation')
        changes = row['maximum_changes']
        _closed(changes, ('actual_probability', 'synthetic_probability', 'posterior_diagnostic', 'stage', 'per100', 'map_l1'), 'maximum changes')
        require(row['status'] == 'passed'
                and max(changes['actual_probability'], changes['synthetic_probability'], changes['stage']) <= TOLERANCES['probability']
                and changes['per100'] <= TOLERANCES['per100'] and changes['map_l1'] <= TOLERANCES['map_l1'],
                'resolution claims a failed comparison passed')
        summary = row['actual_keys']
        require(summary['population']['keys'] == len(keys) and summary['baseline_danger'] == dict(bins)
                and all(summary['expected_sums'][name]['baseline'] == baseline_sums[name] for name in baseline_sums),
                'actual-key propagation population differs from saved events')
        require(len(row['neutral_panels']) == len(PANEL_STATES), 'neutral propagation omits exact physical panels')
        require([tuple(c['pair']) for c in row['pairs']] == pairs and all(c['status'] == 'passed' for c in row['pairs']),
                'pair comparisons differ from the frozen selector')


def _support(value, label):
    _closed(value, ('included_seconds', 'events', 'eligible_weight', 'known_excluded_seconds', 'unquantified_gap', 'reason_counts',
                    'inferred_inputs', 'current_season_information', 'prior_only', 'prior_seasons'), label)
    require(value['eligible_weight'] is None and all(value[k] is None or _number(value[k], label, low=0.) is not None
                                                     for k in ('included_seconds', 'known_excluded_seconds'))
            and (value['events'] is None or _count(value['events'], label) is not None)
            and all(type(value[k]) is bool for k in ('unquantified_gap', 'current_season_information', 'prior_only'))
            and type(value['reason_counts']) is list
            and all(type(r) is dict and set(r) == {'code', 'count'} and type(r['code']) is str and type(r['count']) is int and r['count'] > 0
                    for r in value['reason_counts'])
            and type(value['inferred_inputs']) is list and value['inferred_inputs'] == sorted(set(value['inferred_inputs']))
            and set(value['inferred_inputs']) <= {'blocked_origin', 'setter', 'historical_borrowing'}
            and type(value['prior_seasons']) is list and value['prior_seasons'] == sorted(set(value['prior_seasons'])), f'{label}: invalid support')
    require(not value['prior_only'] or not value['current_season_information'], f'{label}: prior-only support claims current information')


def _coefficient(value, label, setter):
    keys = ('available', 'likelihood_events', 'prior_only', 'prior_seasons', 'reason') + (('candidate_events', 'mean_coupled_events') if setter else ())
    _closed(value, keys, label)
    require(type(value['prior_seasons']) is list and value['prior_seasons'] == sorted(set(value['prior_seasons'])), f'{label}: invalid prior seasons')
    if value['available']:
        require(value['available'] is True and type(value['prior_only']) is bool
                and (value['likelihood_events'] is None) == (value['reason'] is not None), f'{label}: invalid coefficient support')
        if value['likelihood_events'] is not None:
            _count(value['likelihood_events'], label)
        if setter and value['likelihood_events'] is not None:
            candidate, mean = _count(value['candidate_events'], label), _count(value['mean_coupled_events'], label)
            require(max(candidate, mean) <= value['likelihood_events'] <= candidate + mean, f'{label}: setter union differs')
    else:
        require(value['available'] is False and value['likelihood_events'] is None and value['prior_only'] is None
                and value['prior_seasons'] == [] and type(value['reason']) is str and value['reason']
                and (not setter or value['candidate_events'] is None and value['mean_coupled_events'] is None), f'{label}: absent coefficient invents support')


def _projections(root, season, people, panels):
    skaters = sorted(pid for pid, row in people.items() if row['kind'] == 'skater')
    expected = iter([(pid, strength) for strength in STRENGTHS for pid in skaters])
    values = {}
    for row in _jsonl(root / 'projections.jsonl'):
        _closed(row, ('season', 'player_id', 'strength', 'values', 'unavailable', 'reference_panel', 'coefficient_support', 'support'), 'projection')
        require(row['season'] == season and (row['player_id'], row['strength']) == next(expected, None), 'projections omit, repeat or misorder skater strengths')
        panel = row['reference_panel']
        _closed(panel, ('panel_id', 'opportunities', 'setup_weight', 'neutral', 'focal_shooter', 'setting_setup'), 'reference panel')
        bound = panels[row['strength']]
        n, common, terms = bound['rows'], bound['masses'], bound['origins']
        require(panel['panel_id'] == bound['record']['panel_id'] and panel['opportunities'] == n
                and isclose(_number(panel['setup_weight'], 'setup weight', low=0.), .8 * n, rel_tol=1e-12, abs_tol=1e-12), 'reference panel denominators differ')
        _prefix(panel['neutral'], 'neutral panel', n)
        setup = panel['setting_setup']
        _closed(setup, ('neutral_goal_mass', 'focal_goal_mass'), 'setting setup')
        require(all(_near(panel['neutral'][k], common['prefixes'][k], terms) for k in PREFIXES)
                and _near(setup['neutral_goal_mass'], common['setup_goal_mass'], terms), 'projection neutral masses differ from saved panel logits')
        _closed(panel['focal_shooter'], PREFIXES, 'focal panel')
        previous = n
        for key in PREFIXES:
            mass = panel['focal_shooter'][key]
            require(mass is None or previous is not None and _number(mass, 'focal mass', low=0., high=previous) is not None, 'focal prefix nullability/order invalid')
            previous = mass
        _number(setup['neutral_goal_mass'], 'neutral setup mass', low=0., high=panel['setup_weight'])
        require(setup['neutral_goal_mass'] <= panel['neutral']['uqrg'] * (1 + 1e-12)
                and (setup['focal_goal_mass'] is None or _number(setup['focal_goal_mass'], 'focal setup mass', low=0., high=panel['setup_weight']) is not None),
                'setting setup mass outside its panel')
        support = row['coefficient_support']
        _closed(support, ('shooter', 'setter'), 'coefficient support')
        _closed(support['shooter'], HEADS, 'shooter coefficient support')
        _closed(support['setter'], ('g',), 'setter coefficient support')
        for head in HEADS:
            _coefficient(support['shooter'][head], f'shooter {head}', False)
        _coefficient(support['setter']['g'], 'setter g', True)
        chain, available = [], True
        for head, key in zip(HEADS, PREFIXES):
            available = available and support['shooter'][head]['available']
            chain.append(available)
            require((panel['focal_shooter'][key] is not None) == available, 'focal prefix availability differs from coefficient support')
        require((setup['focal_goal_mass'] is not None) == support['setter']['g']['available'], 'setting mass availability differs from setter support')
        _closed(row['values'], FIELDS, 'projection values')
        _closed(row['support'], FIELDS, 'projection support')
        require(type(row['unavailable']) is dict and set(row['unavailable']) == {f for f in FIELDS if row['values'][f] is None},
                'unavailable reasons differ from null values')
        for field in FIELDS:
            _support(row['support'][field], field)
            if row['values'][field] is None:
                reason = row['unavailable'][field]
                _closed(reason, ('reason', 'explanation'), 'unavailable value')
                require(reason['reason'] in REASONS and type(reason['explanation']) is str and reason['explanation'], 'invalid unavailable reason')
            else:
                level = field in STAGES
                _number(row['values'][field], field, low=0. if level else None, high=1. if level else None)
        focal, base = panel['focal_shooter'], panel['neutral']
        # the scalar sums per-origin contributions (sequential within a cell, exact
        # across cells) while each mass is a log-domain integral: both roundings bound it.
        closures = ((FINISHING, None if focal['uqrg'] is None or not n else (focal['uqrg'], base['uqrg'], n)),
                    (SETTING, None if setup['focal_goal_mass'] is None or not panel['setup_weight'] else
                     (setup['focal_goal_mass'], setup['neutral_goal_mass'], panel['setup_weight'])))
        for field, closure in closures:
            actual = row['values'][field]
            if closure is not None:
                left, right, denominator = closure
                error = 100 * ((bound['cell_rows'] + 4) * ULP * (left + right)
                               + _log_error(left, terms) * left + _log_error(right, terms) * right) / denominator
            require((actual is None) == (closure is None) and (actual is None or abs(actual - 100 * (left - right) / denominator) <= error),
                    f'{field} does not close to its panel masses')
        ratios = ((focal['u'], n), (focal['uq'], focal['u']), (focal['uqr'], focal['uq']), (focal['uqrg'], focal['uqr']))
        for index, field in enumerate(STAGES):
            level, difference = row['values'][field], row['values'][field + '_difference']
            neutral_level = common['stage_levels'][field]
            require(level is None or chain[index] and n, f'{field} exists without its focal coefficient chain or panel')
            require((difference is None) == (level is None or neutral_level is None)
                    and (difference is None or abs(difference - (level - neutral_level))
                         <= _log_error(level, terms) * level + _log_error(neutral_level, terms) * neutral_level + 4 * ULP),
                    f'{field} difference differs from the common neutral stage')
            require(level is None or _represents(level, *ratios[index], terms, complement=field == 'recorded_stop_probability'),
                    f'{field} differs from its focal panel masses')
        values[row['player_id'], row['strength']] = (row['values'][FINISHING], row['values'][SETTING], panel['panel_id'])
    require(next(expected, None) is None, 'projections omit selected skater strengths')
    expected = iter([(pid, strength, kind) for strength in STRENGTHS for pid in skaters for kind in ('finishing', 'setting')])
    offsets = {}
    path = root / 'maps.jsonl'
    with path.open('rb') as source:
        number = 0
        while True:
            offset = source.tell()
            line = source.readline()
            if not line:
                break
            number += 1
            row = _decode(path, number, line)
            _closed(row, ('season', 'player_id', 'strength', 'map_kind', 'panel_id', 'cells', 'integrated_value'), 'map')
            selector = (row['player_id'], row['strength'], row['map_kind'])
            require(row['season'] == season and selector == next(expected, None), 'maps omit, repeat or misorder projections')
            offsets[selector] = offset
            finishing, setting, panel_id = values[row['player_id'], row['strength']]
            scalar = finishing if row['map_kind'] == 'finishing' else setting
            require(row['panel_id'] == panel_id, 'map references another panel')
            if row['cells'] is None:
                require(scalar is None and row['integrated_value'] is None, 'unavailable map has values or available scalar lacks map')
            else:
                require(type(row['cells']) is list and len(row['cells']) == 656
                        and all(type(v) in (int, float) and isfinite(v) for v in row['cells']), 'native map needs 656 finite cells')
                require(scalar is not None and row['integrated_value'] == scalar == fsum(row['cells']), 'native map mass differs from its scalar')
    require(next(expected, None) is None, 'maps omit selected projections')
    return offsets
