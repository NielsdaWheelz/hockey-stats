"""annual execution fitting and one saved-state branch-probability interface."""

from dataclasses import dataclass, replace
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.special import expit

from .artifacts import implementation, require, resources, write_json
from .chance_cli import identity, output_path
from .execution_design import RECIPE, ExecutionDesign, ExecutionPredictor, SetterCandidate
from .execution_state import (HEADS, ExecutionState, read_execution_state,
                              read_execution_probe, write_execution_state, write_execution_head,
                              freeze_execution_baseline, write_execution_probe)


@dataclass(frozen=True)
class BranchPrediction:
    origin_cells: tuple
    setter_branches: tuple
    prior_probabilities: np.ndarray
    u: np.ndarray
    q: np.ndarray
    r: np.ndarray
    g: np.ndarray
    terminal_probabilities: dict


def prepare_execution(base_prepared, coaches, recipe, season):
    from .execution_design import prepare_execution as prepare
    return prepare(base_prepared, coaches, recipe, season)


def _centered_state(result, previous_ledger, season):
    """keep raw coordinates and last observed history; centers are references."""
    actors = result['actors']
    coefficients = result['coefficients']
    centers = {}
    for block in ('shooter', 'goalie', 'setter', 'attacking_coach', 'defending_coach'):
        selected = [row for row in actors if row['block'] == block]
        weight = sum(row['center_weight'] for row in selected)
        center = (sum(row['center_weight'] * coefficients[row['index']] for row in selected) / weight
                  if weight else 0.)
        centers[block] = dict(value=float(center), weight=float(weight), prior_only=not bool(weight))
    ledger = {(row['block'], str(row['id'])): dict(row) for row in previous_ledger}
    for row in actors:
        if row['likelihood_support']:
            ledger[(row['block'], str(row['id']))] = dict(
                block=row['block'], id=row['id'], coefficient=float(coefficients[row['index']]),
                season=season, role=row['role'], age=row['age'])
    return centers, sorted(ledger.values(), key=lambda row: (row['block'], str(row['id'])))


def _metadata(design, result, incoming, season):
    from .execution_design import TARGETS

    actors = []
    priors = []
    history = {(row['block'], str(row['id'])): row for row in incoming}
    for row in result['actors']:
        actors.append({key: (row.get('prior_only', row['likelihood_support'] == 0) if key == 'prior_only' else row[key]) for key in ('index', 'block', 'id', 'role', 'age',
                                               'source_support', 'likelihood_support',
                                               'center_weight', 'prior_only')})
        priors.append({key: row.get(key) for key in ('block', 'id', 'mean', 'precision',
                                                  'age_delta', 'age_indices', 'transition_reason', 'prior_mean')})
        priors[-1]['last_supported'] = history.get((row['block'], str(row['id'])))
    complete = result['status'] == 'complete'
    centers, ledger = _centered_state(result, incoming, season) if complete else (None, incoming)
    return dict(head=design['head'], target=TARGETS[design['head']], design=design['design'],
                actors=actors, priors=priors, centers=centers, ledger=ledger,
                origin=dict(cells=656, distance_ft=20., direction_strength=4.,
                            law='uniform-release-forward-kernel'), arrays=None,
                starts=result['starts'], selected_start=result['selected_start'],
                diagnostics=dict(result.get('diagnostics', {}), requested_starts=result['requested_starts'],
                                 wall_seconds=result['wall_seconds']),
                resolution=dict(status='pending' if season == '20252026' else 'not_applicable'),
                status=result['status'], reasons=result['reasons'])


def _previous(design, previous, recipe):
    selected = list(design.seasons)
    first = '20212022' if design.purpose == 'real' else (min(selected) if selected else design.season)
    if design.season == first:
        require(previous is None, 'first selected execution season forbids previous state')
        return None
    require(previous is not None, 'later execution season requires previous annual state')
    if not isinstance(previous, ExecutionState):
        previous = read_execution_state(previous, design.purpose)
    require(previous.usage == 'annual' and previous.manifest['purpose'] == design.purpose
            and all(previous.heads[h]['status'] == 'complete' for h in HEADS), 'previous state is not a completed annual family')
    year = int(design.season[:4])
    require(previous.manifest['season'] == f'{year-1}{year}'
            and previous.manifest['recipe'] == recipe
            and all(previous.manifest[name][field] == getattr(design, name)[field]
                    for name in ('prepared', 'coaches') for field in ('path', 'sha256', 'purpose')), 'previous annual lineage differs')
    return previous


def fit_execution_year(design, previous_state, recipe, output):
    from .execution_design import RECIPE
    from .execution_fit import fit_head

    require(recipe == RECIPE, 'unsupported execution recipe definition')
    previous = _previous(design, previous_state, recipe)
    input_roots = [str(Path(design.prepared['path']).parent), str(Path(design.coaches['path']).parent)]
    if previous is not None:
        input_roots.append(str(previous.path.parent))
    output = output_path(str(output), input_roots)
    output.mkdir()
    (output / 'heads').mkdir()
    started = perf_counter()
    heads, arrays = {}, {}
    for head in HEADS:
        incoming = [] if previous is None else previous.heads[head]['ledger']
        result = fit_head(design.heads[head], incoming)
        heads[head] = _metadata(design.heads[head], result, incoming, design.season)
        if result['status'] == 'complete':
            arrays[head] = dict(coefficients=result['coefficients'])
        write_execution_head(output, heads[head], arrays.get(head, {}), design.season)
    prior = None if previous is None else dict(identity(previous.path), season=previous.manifest['season'],
                  purpose=previous.manifest['purpose'], recipe_sha256=recipe['sha256'], usage='annual')
    measured = resources(started)
    measured.update(design_wall_seconds=design.resources['design_wall_seconds'],
                    input_read_wall_seconds=design.resources['input_read_wall_seconds'],
                    fit_wall_seconds=measured['wall_seconds'],
                    wall_scope='initial_input_read+prepare_execution+fit_and_members_before_completion_manifest', output_bytes=0,
                    origin_rows={head: heads[head]['diagnostics'].get('in_sample',{}).get('expanded_rows') for head in HEADS},
                    candidate_branches={head: heads[head]['diagnostics'].get('in_sample',{}).get('candidate_branches') for head in HEADS},
                    resolution_solve_counts={head:0 for head in HEADS}, dimensions={head: design.heads[head]['size'] for head in HEADS},
                    solve_counts={head: sum((len(row.get('inner_solves', [])) if head == 'g' else 1)
                                           for row in heads[head]['starts'] if row.get('deduplicated_to') is None)
                                  for head in HEADS})
    manifest = dict(schema_version=1, kind='execution-state', purpose=design.purpose,
                    season=design.season, recipe=recipe, implementation=implementation(),
                    prepared=design.prepared, coaches=design.coaches, previous=prior,
                    training_cutoff=design.training_cutoff, resources=measured)
    if design.season == '20252026' and all(heads[h]['status'] == 'complete' for h in HEADS):
        _resolve_final_year(design, previous, output, manifest, heads, arrays)
    manifest['resources']['fit_wall_seconds'] = perf_counter() - started
    manifest['resources']['wall_seconds'] = sum(manifest['resources'][key] for key in ('input_read_wall_seconds','design_wall_seconds','fit_wall_seconds'))
    return write_execution_state(output, manifest, heads, arrays, design.coverage, _reserved=True)


def _resolution_selector(design):
    """cover ordered marginal requirements, then fill by physical source key."""
    key_order = lambda key: (key.split(':')[0], int(key.split(':')[1]))
    coverage = {row['key']:row for row in design.coverage['attempts']}
    predictors = sorted((p for p in design.predictors if coverage[p.key]['full_probability_context']), key=lambda p: key_order(p.key))
    withheld = sorted((p for p in design.predictors if not coverage[p.key]['full_probability_context']), key=lambda p:key_order(p.key))
    selected, requirements, fixture_probes, fixture_witnesses = {}, [], [], []
    def choose(name, predicate, block=None, actor=None):
        witness = next((p for p in predictors if predicate(p)), None)
        if witness is not None:
            requirements.append(dict(requirement=name, key=witness.key, disposition='actual'))
            if len(selected) < 256:
                selected[witness.key] = witness
            return
        if block is not None:
            from .execution_design import build_resolution_witness
            built = build_resolution_witness(design, name, block, actor)
            if built is not None:
                predictor, attribution = built
                requirements.append(dict(requirement=name, key=predictor.key, disposition='fixture'))
                if predictor.key not in {probe.key for probe in fixture_probes}:
                    fixture_probes.append(predictor)
                    fixture_witnesses.append(dict(key=predictor.key, attribution=attribution))
                return
        requirements.append(dict(requirement=name, key=None, disposition='unavailable'))
    for strength in sorted({tuple(p.context['strength']) for p in predictors}):
        choose('strength:' + ','.join(map(str, strength)), lambda p, strength=strength: tuple(p.context['strength']) == strength)
    from .chance import TYPES
    for shot_type, name in enumerate(TYPES):
        choose('type:' + name, lambda p, shot_type=shot_type: p.shot_type == shot_type)
    attempts = {row['key']: row for row in design.coverage['attempts']}
    def outcome(p):
        return attempts[p.key]['outcome']
    for label in ('block', 'miss', 'save', 'goal'):
        choose('outcome:' + label, lambda p, label=label: outcome(p) == label)
    choose('missing_context', lambda p: any(row['status'] == 'unavailable' for row in p.context['features'].values()))
    choose('tip', lambda p: p.tip)
    choose('off_ice_setter', lambda p: any(c.kind == 'skater' and c.actor_id not in p.context['attacking_skaters'] for c in p.setter_prior))
    choose('incomplete_setter', lambda p: not p.context['setter_universe_complete'])
    for head in HEADS:
        for block in ('shooter', 'goalie', 'setter', 'attacking_coach', 'defending_coach'):
            actors = [row for row in design.heads[head]['actors'] if row['block'] == block]
            if not actors:
                continue
            sparse = min(actors, key=lambda row: (row['likelihood_support'], str(row['id'])))
            actor = str(sparse['id'])
            choose('sparse:' + head + ':' + block + ':' + actor,
                   lambda p, block=block, actor=actor: any(c.actor_id == actor for c in p.setter_prior) if block == 'setter' else p.actors.get(block) == actor and (block != 'shooter' or not p.tip), block, actor)
    for predictor in predictors:
        if len(selected) >= 256:
            break
        selected[predictor.key] = predictor
    ordered = tuple(selected[key] for key in sorted(selected, key=key_order))
    selector = dict(policy='strength,type,outcome,missing,tip,off-ice,incomplete,sparse; first (game_id,integer_source_index); numeric source-key fill; maximum256 actual',
                    purpose=design.purpose, requirements=requirements, keys=[p.key for p in ordered],
                    population=dict(eligible_contexts=len(predictors), withheld_contexts=[dict(key=p.key,reason='individual_goalie_identity_unavailable',strength=p.context['strength']) for p in withheld]),
                    fixture_witnesses=fixture_witnesses,
                    synthetic_geometry=dict(context_key=ordered[0].key if ordered else None,
                                            types=list(TYPES), cells=list(range(656)), execution=['actual', 'neutral']))
    return selector, ordered + tuple(fixture_probes)


def _probability_comparison(base, variant, probes):
    maximum = 0.
    by_head = {head: 0. for head in HEADS}
    by_terminal = {name: 0. for name in ('block', 'miss', 'stopped', 'continuing', 'goal')}
    origins, branch_count = 0, 0
    def compare(predictor, cells, neutralize):
        nonlocal maximum, origins, branch_count
        left = execution_branch_probabilities(base, predictor, cells, neutralize)
        right = execution_branch_probabilities(variant, predictor, cells, neutralize)
        require(np.array_equal(left.prior_probabilities, right.prior_probabilities), 'resolution changed setter priors')
        origins += len(cells)
        branch_count += len(cells) * len(left.setter_branches)
        for head in HEADS:
            delta = float(np.max(np.abs(getattr(left, head)-getattr(right, head))))
            by_head[head] = max(by_head[head], delta)
            maximum = max(maximum, delta)
        for name in by_terminal:
            delta = float(np.max(np.abs(left.terminal_probabilities[name]-right.terminal_probabilities[name])))
            by_terminal[name] = max(by_terminal[name], delta)
            maximum = max(maximum, delta)
    for predictor in probes:
        cells = np.arange(656, dtype=np.int64) if predictor.blocked else np.asarray([predictor.proxy_cell], dtype=np.int64)
        for neutralize in ((), ('shooter', 'setter', 'goalie', 'coaching')):
            compare(predictor, cells, neutralize)
    from .chance import TYPES
    if probes:
        context = probes[0]
        for shot_type, name in enumerate(TYPES):
            synthetic = replace(context, key='synthetic:' + name, shot_type=shot_type, tip=name == 'tip', blocked=False)
            for neutralize in ((), ('shooter', 'setter', 'goalie', 'coaching')):
                compare(synthetic, np.arange(656, dtype=np.int64), neutralize)
    return dict(maximum_probability_change=maximum, head_maximum_changes=by_head,
                terminal_maximum_changes=by_terminal, evaluated_origins=origins,
                evaluated_branches=branch_count)


def _resolve_final_year(design, previous, output, manifest, heads, arrays):
    from .execution_fit import continue_head

    selector, probes = _resolution_selector(design)
    require(bool(probes), 'complete final family has no supported numerical probes')
    descriptor = freeze_execution_baseline(output, manifest, heads, selector)
    baseline = ExecutionState(output / 'manifest.json', manifest, dict(heads), dict(arrays), design.coverage)
    for head in HEADS:
        incoming = [] if previous is None else previous.heads[head]['ledger']
        result = continue_head(design.heads[head], incoming, arrays[head]['coefficients'])
        manifest['resources']['resolution_solve_counts'][head] = sum((len(row.get('inner_solves',[])) if head == 'g' else 1) for row in result['starts'] if row.get('deduplicated_to') is None)
        if result['status'] == 'complete':
            metadata = _metadata(design.heads[head], result, incoming, design.season)
            metadata['arrays'] = heads[head]['arrays']
            alternate_heads, alternate_arrays = dict(heads), dict(arrays)
            alternate_heads[head] = metadata
            alternate_arrays[head] = dict(coefficients=result['coefficients'])
            variant = replace(baseline, heads=alternate_heads, arrays=alternate_arrays, usage='numerical_probe')
            comparison = dict(result['comparison'], **_probability_comparison(baseline, variant, probes))
            reference = write_execution_probe(output, descriptor, metadata, alternate_arrays[head], comparison)
            status = 'passed' if comparison['maximum_probability_change'] <= 1e-5 and all(row['disposition'] != 'unavailable' for row in selector['requirements']) else 'failed'
            heads[head]['resolution'] = dict(status=status, baseline=descriptor, probe=reference, comparison=comparison)
        else:
            heads[head]['resolution'] = dict(status='failed', baseline=descriptor,
                                            reasons=result['reasons'], diagnostics=result.get('diagnostics', {}))
        # this directory has no completion manifest. replace only the small head
        # metadata; the completed baseline coefficient file remains untouched.
        path = output / f'heads/{head}.json'
        path.unlink()
        write_json(path, heads[head])


def execution_branch_probabilities(state, predictors, origin_cells, neutralize=()):
    """evaluate pre-outcome setter priors and preserve five-way probability mass."""
    from .execution_design import predictor_matrix

    require(isinstance(state, ExecutionState), 'prediction requires a checked execution state')
    groups = tuple(neutralize)
    require(len(groups) == len(set(groups)) and set(groups) <= {'shooter', 'setter', 'goalie', 'coaching'},
            'invalid neutral execution groups')
    cells = np.asarray(origin_cells)
    require(cells.ndim == 1 and len(cells) > 0 and cells.dtype.kind in 'iu'
            and np.all((cells >= 0) & (cells < 656)), 'invalid explicit origin cells')
    require(all(state.heads[h]['status'] == 'complete' for h in HEADS), 'execution family has unavailable heads')
    blocks = set(groups) - {'coaching'}
    if 'coaching' in groups:
        blocks.update(('attacking_coach', 'defending_coach'))
    logits = {}
    for head in HEADS:
        metadata = state.heads[head]
        beta = state.arrays[head]['coefficients']
        for block, axis in metadata['design']['actor_indices'].items():
            if block == 'setter':
                continue
            actor_id = predictors.actors.get(block)
            require(actor_id is None and block.endswith('coach') or actor_id in axis, 'unknown or missing execution actor ' + block)
        scoring = beta.copy()
        for actor in metadata['actors']:
            if actor['block'] in blocks:
                scoring[actor['index']] = metadata['centers'][actor['block']]['value']
        matrix = predictor_matrix(metadata['design'], [predictors] * len(cells), cells)
        logits[head] = np.asarray(matrix @ scoring).ravel()
        require(logits[head].shape == (len(cells),) and np.isfinite(logits[head]).all(), 'invalid evaluated logits')
    candidates = tuple(predictors.setter_prior)
    require(bool(candidates), 'empty setter prior')
    def value(candidate, key):
        return candidate[key] if isinstance(candidate, dict) else getattr(candidate, key)
    prior = np.asarray([value(row, 'probability') for row in candidates], dtype=np.float64)
    require(np.isfinite(prior).all() and np.all(prior > 0) and abs(prior.sum()-1.) <= 1e-12, 'invalid setter prior mass')
    none = [row for row in candidates if value(row,'kind') == 'none']
    require(len(none) == 1 and value(none[0],'actor_id') is None and value(none[0],'probability') == .2, 'setter prior has invalid none branch')
    signatures = [(value(row,'kind'),value(row,'actor_id')) for row in candidates]
    require(len(set(signatures)) == len(signatures) and all(kind in ('none','unknown','goalie','skater') for kind,_ in signatures), 'duplicate or invalid setter branches')
    require(all(actor is None for kind,actor in signatures if kind in ('none','unknown'))
            and all(type(actor) is str and bool(actor) for kind,actor in signatures if kind in ('goalie','skater')), 'invalid setter branch identity')
    require(not any(kind == 'unknown' for kind,_ in signatures) or len(candidates) == 2, 'unknown setter mixes with an incomplete declared universe')
    metadata = state.heads['g']
    beta = state.arrays['g']['coefficients']
    actor_axis = {(row['block'], str(row['id'])): row['index'] for row in metadata['actors']}
    setup = beta[metadata['design']['setup_index']]
    setter_center = metadata['centers']['setter']['value']
    mean_indices = metadata['design']['setter_mean_indices']
    mean_weights = metadata['design']['setter_mean_weights']
    mean = float(np.dot(beta[mean_indices], mean_weights))
    branch_logits = np.repeat(logits['g'][:, None], len(candidates), axis=1)
    for column, candidate in enumerate(candidates):
        kind = value(candidate, 'kind')
        if kind == 'none':
            continue
        branch_logits[:, column] += setup
        if kind in ('unknown', 'goalie'):
            if kind == 'goalie':
                require(value(candidate,'actor_id') in metadata['design']['actor_indices']['goalie'], 'unknown goalie setter identity')
            coefficient = mean
        else:
            actor_id = str(value(candidate, 'actor_id'))
            require(('setter', actor_id) in actor_axis, f'unknown setter id {actor_id}')
            coefficient = beta[actor_axis['setter', actor_id]]
        branch_logits[:, column] += setter_center if 'setter' in blocks else coefficient
    u, q, r = (expit(logits[h]) for h in ('u', 'q', 'r'))
    g = expit(branch_logits)
    uq = u[:, None] * q[:, None]
    uqr = uq * r[:, None]
    broadcast = lambda a: np.broadcast_to(a[:, None], g.shape).copy()
    terminal = dict(block=broadcast(1-u), miss=broadcast(u*(1-q)),
                    stopped=broadcast(u*q*(1-r)), continuing=uqr*(1-g), goal=uqr*g)
    require(all(np.isfinite(v).all() and np.all((v >= 0) & (v <= 1)) for v in terminal.values())
            and np.allclose(sum(terminal.values()), 1., rtol=0., atol=5e-15), 'invalid execution probability mass')
    return BranchPrediction(tuple(map(int, cells)), candidates, prior, u, q, r, g, terminal)
