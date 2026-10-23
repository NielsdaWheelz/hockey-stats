"""annual execution fitting and one saved-state branch-probability interface."""

from dataclasses import dataclass, replace
from math import fsum, factorial
from itertools import product
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.special import expit, logsumexp, log_expit

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
    log_prefixes: dict
    goal_log_likelihoods: tuple


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
    """evaluate the same joint engine used by references and exact coalitions."""
    groups = tuple(neutralize)
    require(len(groups) == len(set(groups)) and set(groups) <= set(GROUPS),
            'invalid neutral execution groups')
    context = _execution_context(state, predictors, origin_cells)
    subset = sum(1 << i for i, group in enumerate(GROUPS) if group not in groups)
    return _coalition_prediction(context, subset)


def _execution_base_logits(state, predictors, cells, blocks):
    from .execution_design import predictor_matrix

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
    return logits


GROUPS = ('shooter', 'setter', 'goalie', 'coaching')
PREFIXES = ('u', 'uq', 'uqr', 'uqrg')
PUBLIC_STRENGTHS = ('5v5', '5v4', '5v3', '4v3', '4v5', '3v5', '3v4')
STAGE_FIELDS = ('avoid_block_probability', 'on_net_probability',
                'recorded_stop_probability', 'conversion_probability')
FINISHING = 'finishing_goals_per100_attempts'
SETTING = 'setting_goals_per100_assisted_opportunities'


@dataclass(frozen=True)
class ExecutionPanel:
    panel_id: str
    season: str
    strength: tuple
    events: tuple
    arrays: dict
    coefficient_support: dict
    support_keys: dict


def integrated_prefixes(prediction, origin_weights):
    """integrate joint prefixes, never a product of marginal stage means."""
    weights = np.asarray(origin_weights, dtype=np.float64)
    prior = np.asarray(prediction.prior_probabilities, dtype=np.float64)
    n = len(prediction.origin_cells)
    require(weights.shape == (n,) and np.isfinite(weights).all() and np.all(weights >= 0)
            and abs(fsum(weights)-1.) <= 1e-12, 'invalid origin integration mass')
    require(prior.ndim == 1 and len(prior) > 0 and np.isfinite(prior).all()
            and np.all(prior >= 0) and abs(fsum(prior)-1.) <= 1e-12, 'invalid setter integration mass')
    for head in HEADS:
        values = np.asarray(getattr(prediction, head))
        shape = (n, len(prior)) if head == 'g' else (n,)
        require(values.shape == shape and np.isfinite(values).all()
                and np.all((values >= 0) & (values <= 1)), 'invalid stage probabilities')
    return {name:float(_weighted_probability(np.exp(prediction.log_prefixes[name]), weights, axis=0))
            for name in PREFIXES}


def reference_goal_probability(state, predictors, origin_cells):
    """return the virtual-neutral goal mixture at each requested origin."""
    prediction = execution_branch_probabilities(state, predictors, origin_cells, GROUPS)
    return _weighted_probability(prediction.terminal_probabilities['goal'], prediction.prior_probabilities, axis=1)


def execution_shapley(coalitions):
    """exact four-group allocations; trailing axes are origin/candidate branches."""
    values = np.asarray(coalitions, dtype=np.float64)
    require(values.ndim >= 1 and values.shape[0] == 16 and np.isfinite(values).all()
            and np.all((values >= 0) & (values <= 1)), 'invalid sixteen-coalition probabilities')
    result = np.zeros((4, *values.shape[1:]), dtype=np.float64)
    for group in range(4):
        bit = 1 << group
        for subset in range(16):
            if subset & bit:
                continue
            size = subset.bit_count()
            weight = factorial(size) * factorial(3-size) / 24
            result[group] += weight * (values[subset | bit] - values[subset])
    require(np.allclose(result.sum(axis=0), values[15]-values[0], rtol=0, atol=2e-15),
            'execution allocation does not close')
    return result


def _coefficient_support(state, design):
    """recover physical likelihood-key sets instead of counting structural flags."""
    predictors = {p.key: p for p in design.predictors}
    keys, metadata = {}, {}
    observed = design.observed_setters
    candidate_keys = {}
    coupled = set()
    for head in HEADS:
        for key in design.heads[head]['keys']:
            predictor = predictors[key]
            if not predictor.tip:
                candidate_keys.setdefault(('shooter',predictor.actors['shooter'],head),set()).add(key)
            if head != 'g':
                continue
            label = observed[key]
            for j,candidate in enumerate(predictor.setter_prior):
                if label >= 0 and label != j:
                    continue
                if candidate.kind == 'skater':
                    candidate_keys.setdefault(('setter',candidate.actor_id,head),set()).add(key)
                elif candidate.kind in ('unknown','goalie'):
                    coupled.add(key)
    mean_ids = {actor for actor,index in state.heads['g']['design']['actor_indices']['setter'].items()
                if index in state.heads['g']['design']['setter_mean_indices']}
    for head in HEADS:
        priors = {(p['block'], str(p['id'])): p for p in state.heads[head]['priors']}
        for actor in state.heads[head]['actors']:
            block, actor_id = actor['block'], str(actor['id'])
            if block not in ('shooter', 'setter'):
                continue
            candidate = candidate_keys.get((block,actor_id,head),set())
            mean = coupled if block == 'setter' and actor_id in mean_ids else set()
            union = candidate | mean
            prior = priors.get((block, actor_id), {})
            historical = prior.get('last_supported')
            years = [historical['season']] if historical is not None else []
            record = dict(available=True, likelihood_events=len(union),
                          prior_only=actor['prior_only'], prior_seasons=years, reason=None)
            if block == 'setter':
                record.update(candidate_events=len(candidate), mean_coupled_events=len(mean))
            keys[block, actor_id, head] = frozenset(union)
            metadata[block, actor_id, head] = record
    return metadata, keys, observed


def _neutral_panel_logits(state, predictor, cells):
    blocks = {'shooter', 'setter', 'goalie', 'attacking_coach', 'defending_coach'}
    logits = _execution_base_logits(state, predictor, cells, blocks)
    metadata = state.heads['g']
    setup = state.arrays['g']['coefficients'][metadata['design']['setup_index']]
    setup += metadata['centers']['setter']['value']
    return np.column_stack([logits[h] for h in ('u','q','r')]), np.column_stack((logits['g'], logits['g']+setup))


def score_execution(state, prepared_game, coaches):
    """score one checked annual design and retain all recognized dispositions."""
    design = prepared_game
    require(isinstance(state, ExecutionState) and isinstance(design, ExecutionDesign),
            'execution scoring requires a checked state and annual execution design')
    require(state.manifest['season'] == design.season and state.manifest['purpose'] == design.purpose
            and state.manifest['recipe'] == design.recipe
            and state.manifest['prepared'] == design.prepared
            and state.manifest['coaches'] == design.coaches,
            'execution state/design binding differs')
    require(all(state.heads[h]['status'] == 'complete' for h in HEADS), 'execution family is incomplete')
    require(coaches is None or coaches == design.coaches, 'scoring coach identity differs')
    metadata, support_keys, observed_setters = _coefficient_support(state, design)
    selected = {p.key: p for p in design.predictors}
    events, setters, shares = [], [], []
    pieces = {strength: [] for strength in product(range(3,7), range(3,7), (0,1))}
    for disposition in sorted(design.coverage['attempts'],key=lambda r:(r['game_id'],r['source_index'])):
        key = disposition['key']
        result = score_execution_event(state,selected.get(key),disposition,
            facts=design.scoring_facts.get(key),observed_setter=observed_setters.get(key,-1))
        events.append(result['event'])
        setters.extend(result['setters'])
        shares.extend(result['shares'])
        if result['panel_piece'] is not None:
            pieces[tuple(result['event']['physical_state'][:3])].append(result['panel_piece'])
    panels = {}
    for strength, rows in pieces.items():
        lengths = [len(r[1]) for r in rows]
        arrays = dict(event_offsets=np.asarray([0,*np.cumsum(lengths)],dtype=np.int64),
                      origin_cells=np.concatenate([r[1] for r in rows]) if rows else np.empty(0,dtype=np.int64),
                      origin_weights=np.concatenate([r[2] for r in rows]) if rows else np.empty(0,dtype=np.float64),
                      neutral_upstream_logits=np.concatenate([r[3] for r in rows]) if rows else np.empty((0,3),dtype=np.float64),
                      neutral_goal_logits=np.concatenate([r[4] for r in rows]) if rows else np.empty((0,2),dtype=np.float64),
                      setup_weights=np.tile(np.array([.2,.8]),(len(rows),1)))
        panel_id = 'execution-v1-06-1:'+design.season+':'+','.join(map(str,strength))
        panels[strength] = ExecutionPanel(panel_id,design.season,strength,tuple(r[0] for r in rows),arrays,metadata,support_keys)
    return dict(events=events,setters=setters,shares=shares,panels=panels)


def _joint_log_prefixes(upstream, goal, prior):
    logs = np.cumsum(log_expit(upstream), axis=1)
    with np.errstate(divide='ignore'):
        log_prior = np.log(prior)
    success = logsumexp(log_expit(goal) + log_prior, axis=1)
    failure = logsumexp(log_expit(-goal) + log_prior, axis=1)
    goal_log = logs[:, 2] + log_expit(success - failure)
    return np.column_stack((logs, goal_log))


def _weighted_probability(values, weights, axis):
    """integrate a unit-mass law through its success and failure masses."""
    success = np.sum(values * weights, axis=axis)
    failure = np.sum((1. - values) * weights, axis=axis)
    return success / (success + failure)


def _projection_chunks(panel, applicable_by_event=None):
    """bound transient logit arrays while preserving every origin and its source weight."""
    arrays = panel.arrays
    offsets = arrays['event_offsets']
    first = 0
    while first < len(panel.events):
        last = max(first + 1, int(np.searchsorted(offsets, offsets[first] + 65536, side='right')) - 1)
        start, end = offsets[first], offsets[last]
        event = np.repeat(np.arange(first, last), np.diff(offsets[first:last + 1]))
        starts = offsets[first:last] - start
        yield start, end, first, last, event, starts, None if applicable_by_event is None else applicable_by_event[event]
        first = last


def _projection_neutral(panel, retain_origin_values=True):
    arrays = panel.arrays
    rows = len(arrays['origin_cells'])
    neutral_uqr = np.empty(rows) if retain_origin_values else None
    neutral_goal = np.empty(rows) if retain_origin_values else None
    neutral_setup = np.empty(rows) if retain_origin_values else None
    event_weight_mass = np.empty(len(panel.events))
    masses = np.empty((len(panel.events), 4))
    setup_masses = np.empty(len(panel.events))
    log_mass = np.full(4, -np.inf)
    for start, end, first, last, event, starts, _ in _projection_chunks(panel):
        goal = arrays['neutral_goal_logits'][start:end]
        setup = arrays['setup_weights'][event]
        weights = arrays['origin_weights'][start:end]
        logs = _joint_log_prefixes(arrays['neutral_upstream_logits'][start:end], goal, setup)
        log_mass = np.logaddexp(log_mass, _integrated_log_columns(logs, weights))
        denominators = np.add.reduceat(weights, starts)
        event_weight_mass[first:last] = denominators
        probabilities = np.exp(logs)
        for head in range(4):
            masses[first:last, head] = np.add.reduceat(weights * probabilities[:, head], starts) / denominators
        setup_probability = np.exp(logs[:, 2]) * expit(goal[:, 1])
        setup_masses[first:last] = (arrays['setup_weights'][first:last, 1]
                                   * np.add.reduceat(weights * setup_probability, starts) / denominators)
        if retain_origin_values:
            neutral_uqr[start:end] = logs[:, 2]
            neutral_goal[start:end] = probabilities[:, 3]
            neutral_setup[start:end] = setup_probability * setup[:, 1]
    totals = np.array([fsum(masses[:, head]) for head in range(4)])
    return (totals, fsum(setup_masses),
            _levels_from_log_masses(log_mass, len(panel.events), totals[0]) if panel.events else (None,) * 4,
            event_weight_mass, neutral_uqr, neutral_goal, neutral_setup)


def _projection_focal(panel, effects, setter_effect, setup_weight, applicable_by_event,
                      event_weight_mass, neutral_uqr, neutral_goal, neutral_setup):
    arrays = panel.arrays
    count = len(panel.events)
    log_mass = np.full(4, -np.inf)
    masses = np.empty((count, 4))
    setup_masses = np.empty(count)
    finishing_map = np.zeros(656)
    setting_map = np.zeros(656)
    shooter_delta = np.asarray([0. if effect is None else effect for effect in effects])
    for start, end, first, last, event, starts, applicable in _projection_chunks(panel, applicable_by_event):
        weights = arrays['origin_weights'][start:end]
        normalized_weights = weights / event_weight_mass[event]
        cells = arrays['origin_cells'][start:end]
        upstream = arrays['neutral_upstream_logits'][start:end].copy()
        goal = arrays['neutral_goal_logits'][start:end].copy()
        upstream += applicable[:, None] * shooter_delta[:3]
        goal += applicable[:, None] * shooter_delta[3]
        logs = _joint_log_prefixes(upstream, goal, arrays['setup_weights'][event])
        log_mass = np.logaddexp(log_mass, _integrated_log_columns(logs, weights))
        probabilities = np.exp(logs)
        for head in range(4):
            masses[first:last, head] = (np.add.reduceat(weights * probabilities[:, head], starts)
                                        / event_weight_mass[first:last])
        if count:
            finishing_map += np.bincount(cells, weights=100 * normalized_weights *
                (probabilities[:, 3] - neutral_goal[start:end]) / count, minlength=656)
        if setter_effect is not None:
            setup_probability = np.exp(neutral_uqr[start:end]) * expit(
                arrays['neutral_goal_logits'][start:end, 1] + setter_effect)
            setup_masses[first:last] = (arrays['setup_weights'][first:last, 1]
                * np.add.reduceat(weights * setup_probability, starts) / event_weight_mass[first:last])
            if setup_weight:
                setting_map += np.bincount(cells, weights=100 * normalized_weights *
                    (setup_probability * arrays['setup_weights'][event, 1]
                     - neutral_setup[start:end]) / setup_weight, minlength=656)
    totals = np.array([fsum(masses[:, head]) for head in range(4)])
    return (totals, fsum(setup_masses) if setter_effect is not None else 0.,
            _levels_from_log_masses(log_mass, count, totals[0]) if count else (None,) * 4,
            finishing_map, setting_map)


def summarize_execution(state, panel, people, participation):
    """project each focal actor onto the unchanged exact-state common panel."""
    require(isinstance(state,ExecutionState) and isinstance(panel,ExecutionPanel)
            and state.manifest['season'] == panel.season, 'execution projection state/panel differs')
    require(panel.strength[2] == 1 and f'{panel.strength[0]}v{panel.strength[1]}' in PUBLIC_STRENGTHS,
            'panel is not a public skater strength')
    strength = f'{panel.strength[0]}v{panel.strength[1]}'
    arrays = panel.arrays
    n = len(panel.events)
    neutral_mass, neutral_setup_mass, neutral_levels, event_weight_mass, neutral_uqr, neutral_goal, neutral_setup = _projection_neutral(panel)
    neutral_mass = [float(value) for value in neutral_mass]
    setup_weight = fsum(arrays['setup_weights'][:,1])
    has_blocked_origins = bool(np.any(np.diff(arrays['event_offsets']) > 1))
    applicable_by_event = np.asarray([not row['tip'] for row in panel.events], dtype=bool)
    fields = (FINISHING,SETTING,*STAGE_FIELDS,*(name+'_difference' for name in STAGE_FIELDS))
    for person in people:
        if person['kind'] != 'skater':
            continue
        player = str(person['player_id'])
        coefficient_support = dict(shooter={},setter={})
        effects = []
        for block,heads in (('shooter',HEADS),('setter',('g',))):
            for head in heads:
                record = panel.coefficient_support.get((block,player,head))
                if record is None:
                    record = dict(available=False,likelihood_events=None,prior_only=None,
                                  prior_seasons=[],reason='actor_coefficient_unavailable')
                    if block == 'setter':
                        record.update(candidate_events=None,mean_coupled_events=None)
                coefficient_support[block][head] = dict(record)
                if block == 'shooter':
                    axis = state.heads[head]['design']['actor_indices']['shooter']
                    effects.append(None if not record['available'] else
                        float(state.arrays[head]['coefficients'][axis[player]]-state.heads[head]['centers']['shooter']['value']))
        setter_available = coefficient_support['setter']['g']['available']
        setter_effect = None
        if setter_available:
            axis = state.heads['g']['design']['actor_indices']['setter']
            setter_effect = float(state.arrays['g']['coefficients'][axis[player]]-state.heads['g']['centers']['setter']['value'])
        focal_raw, setting_raw, focal_levels, finishing_map, setting_map = _projection_focal(
            panel,effects,setter_effect,setup_weight,applicable_by_event,
            event_weight_mass,neutral_uqr,neutral_goal,neutral_setup)
        focal_mass = [float(focal_raw[head]) if all(value is not None for value in effects[:head+1])
                      else None for head in range(4)]
        setting_mass = setting_raw if setter_available else None
        values = dict.fromkeys(fields)
        native_maps = dict(finishing=None,setting=None)
        if n and focal_mass[3] is not None:
            native_maps['finishing'] = finishing_map
            values[FINISHING] = fsum(native_maps['finishing'])
        if setup_weight and setter_available:
            native_maps['setting'] = setting_map
            values[SETTING] = fsum(native_maps['setting'])
        levels = list(focal_levels)
        for j in range(4):
            if not all(value is not None for value in effects[:j+1]):
                levels[j] = None
        for field,level,baseline in zip(STAGE_FIELDS,levels,neutral_levels,strict=True):
            values[field] = level
            values[field+'_difference'] = None if level is None or baseline is None else level-baseline
        support,unavailable = {},{}
        for field in fields:
            head_count = 4 if field == FINISHING else 1 if field == SETTING else STAGE_FIELDS.index(field.removesuffix('_difference'))+1
            terms = [('setter','g')] if field == SETTING else [('shooter',head) for head in HEADS[:head_count]]
            records = [coefficient_support[block][head] for block,head in terms]
            complete = all(record['available'] for record in records)
            current_keys = set().union(*(panel.support_keys[block,player,head] for block,head in terms)) if complete else None
            prior_only = complete and all(record['prior_only'] for record in records)
            years = sorted({year for record in records for year in record['prior_seasons']})
            elapsed = participation.get((player,strength))
            inferred = []
            if has_blocked_origins:
                inferred.append('blocked_origin')
            if years:
                inferred.append('historical_borrowing')
            if field == SETTING or head_count == 4:
                inferred.append('setter')
            support[field] = dict(included_seconds=None if elapsed is None else elapsed['included_seconds'],
                events=None if current_keys is None else len(current_keys),eligible_weight=None,
                known_excluded_seconds=None if elapsed is None else elapsed.get('known_excluded_seconds'),
                unquantified_gap=True if elapsed is None else elapsed.get('unquantified_gap',False),
                reason_counts=[] if elapsed is None else elapsed.get('reason_counts',[]),
                inferred_inputs=inferred,
                current_season_information=bool(current_keys),prior_only=bool(prior_only),prior_seasons=years)
            if values[field] is None:
                if not n:
                    unavailable[field] = dict(reason='no_exposure',explanation='the exact-state common panel has no supported physical attempts')
                elif not complete:
                    unavailable[field] = dict(reason='missing_source',explanation='a required focal actor coefficient is absent from the checked annual state')
                else:
                    unavailable[field] = dict(reason='no_exposure',explanation='the required stage has zero mathematical probability mass')
        yield dict(season=panel.season,player_id=player,strength=strength,values=values,
                   reference_panel=dict(panel_id=panel.panel_id,opportunities=n,setup_weight=setup_weight,
                       neutral=dict(zip(PREFIXES,neutral_mass,strict=True)),
                       focal_shooter=dict(zip(PREFIXES,focal_mass,strict=True)),
                       setting_setup=dict(neutral_goal_mass=neutral_setup_mass,focal_goal_mass=setting_mass)),
                   coefficient_support=coefficient_support,support=support,native_maps=native_maps,unavailable=unavailable)


def _execution_context(state, predictor, origin_cells):
    require(isinstance(state,ExecutionState), 'prediction requires a checked execution state')
    cells = np.asarray(origin_cells)
    require(cells.ndim == 1 and len(cells) > 0 and cells.dtype.kind in 'iu'
            and np.all((cells >= 0) & (cells < 656)), 'invalid explicit origin cells')
    require(all(state.heads[h]['status'] == 'complete' for h in HEADS), 'execution family has unavailable heads')
    candidates = tuple(predictor.setter_prior)
    require(bool(candidates), 'empty setter prior')
    prior = np.asarray([c.probability for c in candidates],dtype=np.float64)
    require(np.isfinite(prior).all() and np.all(prior > 0) and abs(fsum(prior)-1) <= 1e-12,
            'invalid setter prior mass')
    none = [c for c in candidates if c.kind == 'none']
    require(len(none) == 1 and none[0].actor_id is None and none[0].probability == .2,
            'setter prior has invalid none branch')
    signatures = [(c.kind,c.actor_id) for c in candidates]
    require(len(set(signatures)) == len(signatures) and all(kind in ('none','unknown','goalie','skater') for kind,_ in signatures),
            'duplicate or invalid setter branches')
    require(all(actor is None for kind,actor in signatures if kind in ('none','unknown'))
            and all(type(actor) is str and bool(actor) for kind,actor in signatures if kind in ('goalie','skater')),
            'invalid setter branch identity')
    require(not any(kind == 'unknown' for kind,_ in signatures) or len(candidates) == 2,
            'unknown setter mixes with an incomplete declared universe')
    upstream, goal = _neutral_panel_logits(state,predictor,cells)
    residuals = {group:np.zeros(4) for group in ('shooter','goalie','coaching')}
    for h,head in enumerate(HEADS):
        metadata = state.heads[head]
        for block in ('shooter','goalie','attacking_coach','defending_coach'):
            if block not in metadata['design']['actor_indices'] or block == 'shooter' and predictor.tip:
                continue
            actor = predictor.actors.get(block)
            if actor is None:
                continue
            index = metadata['design']['actor_indices'][block][actor]
            group = 'coaching' if block.endswith('coach') else block
            residuals[group][h] += state.arrays[head]['coefficients'][index]-metadata['centers'][block]['value']
    setter_delta = np.zeros(len(candidates))
    for j,candidate in enumerate(candidates):
        if candidate.kind == 'skater':
            axis = state.heads['g']['design']['actor_indices']['setter']
            require(candidate.actor_id in axis, 'unknown setter id '+candidate.actor_id)
            setter_delta[j] = state.arrays['g']['coefficients'][axis[candidate.actor_id]]-state.heads['g']['centers']['setter']['value']
        elif candidate.kind == 'goalie':
            require(candidate.actor_id in state.heads['g']['design']['actor_indices']['goalie'], 'unknown goalie setter identity')
    return dict(cells=cells,candidates=candidates,prior=prior,upstream=upstream,goal=goal,
                setup_columns=np.array([int(c.kind != 'none') for c in candidates]),
                residuals=residuals,setter_delta=setter_delta)


def _coalition_prediction(context, subset):
    upstream = context['upstream'].copy()
    goal = context['goal'][:,context['setup_columns']].copy()
    for bit,group in ((1,'shooter'),(4,'goalie'),(8,'coaching')):
        if subset & bit:
            delta = context['residuals'][group]
            upstream += delta[:3]
            goal += delta[3]
    if subset & 2:
        goal += context['setter_delta']
    u,q,r = expit(upstream).T
    g = expit(goal)
    logs = _joint_log_prefixes(upstream,goal,context['prior'])
    log_goal = logs[:,2,None]+log_expit(goal)
    broadcast = lambda a:np.broadcast_to(a[:,None],g.shape)
    terminal = dict(block=broadcast(expit(-upstream[:,0])),
                    miss=broadcast(np.exp(logs[:,0]+log_expit(-upstream[:,1]))),
                    stopped=broadcast(np.exp(logs[:,1]+log_expit(-upstream[:,2]))),
                    continuing=np.exp(logs[:,2,None]+log_expit(-goal)),goal=np.exp(log_goal))
    require(all(np.isfinite(v).all() and np.all((v >= 0)&(v <= 1)) for v in terminal.values())
            and np.allclose(sum(terminal.values()),1,rtol=0,atol=5e-15), 'invalid execution probability mass')
    log_prefixes = {name:logs[:,j] for j,name in enumerate(PREFIXES)}
    return BranchPrediction(tuple(map(int,context['cells'])),context['candidates'],context['prior'],u,q,r,g,terminal,
                            log_prefixes,(log_expit(-goal),log_expit(goal)))


def integrated_log_prefixes(prediction, origin_weights):
    require(prediction.log_prefixes is not None, 'stable integration requires evaluated logits')
    weights = np.asarray(origin_weights,dtype=np.float64)
    require(weights.shape == (len(prediction.origin_cells),) and np.isfinite(weights).all()
            and np.all(weights >= 0) and abs(fsum(weights)-1) <= 1e-12, 'invalid origin integration mass')
    logs = _integrated_log_columns(np.column_stack([prediction.log_prefixes[name] for name in PREFIXES]), weights)
    return dict(zip(PREFIXES, map(float, logs), strict=True))


def conditional_goal_probability(prediction, origin_weights, denominator):
    require(denominator in ('u','uq','uqr'), 'invalid execution conditional denominator')
    logs = integrated_log_prefixes(prediction,origin_weights)
    # finite logits give strictly positive mathematical mass. underflow in the
    # stored unconditional float does not erase a representable conditional.
    return float(np.exp(logs['uqrg']-logs[denominator]))


def select_execution_resolution_pairs(projections, people, panels, events=()):
    """freeze the specified bounded focal union before any tighter propagation."""
    people = {str(p['player_id']):p for p in people}
    best = {}
    requirements = []
    tip_support = {}
    for event in events:
        state = event['physical_state']
        if event['status'] != 'complete' or state[2:] not in ((1,1),[1,1]):
            continue
        strength = f'{state[0]}v{state[1]}'
        if strength not in PUBLIC_STRENGTHS:
            continue
        pair = (event['shooter_id'],strength)
        total,tips = tip_support.get(pair,(0,0))
        tip_support[pair] = (total+1,tips+int(event['shot_type']=='tip'))
    def offer(name, order, pair):
        if name not in best or order < best[name][0]:
            best[name] = (order,pair)
    for projection in projections:
        strength = projection['strength']
        player = projection['player_id']
        tie = (PUBLIC_STRENGTHS.index(strength),player)
        pair = (player,strength)
        require((int(strength[0]),int(strength[2]),1) in panels,
                'execution resolution pair lacks its exact-state panel')
        values = projection['values']
        for field,label in ((FINISHING,'finishing'),(SETTING,'setting')):
            value = values[field]
            if value is not None:
                offer(f'{label}:{strength}:min',(value,*tie),pair)
                offer(f'{label}:{strength}:max',(-value,*tie),pair)
        for field in STAGE_FIELDS:
            value = values[field]
            if value is not None:
                offer(field+':min',(value,*tie),pair)
                offer(field+':max',(-value,*tie),pair)
        role = people[player].get('position_group')
        if role in ('F','D'):
            for block,field in (('shooter',FINISHING),('setter',SETTING)):
                if values[field] is None:
                    continue
                support = projection['support'][field]
                events = support['events']
                if events is not None and events > 0:
                    offer(f'{role}:{block}:smallest_positive_support',(events,*tie),pair)
                if support['prior_only']:
                    offer(f'{role}:{block}:first_prior_only',tie,pair)
        total,tips = tip_support.get(pair,(0,0))
        if total and values[FINISHING] is not None:
            fraction = tips/total
            offer('largest_tip_supported_fraction',(-fraction,*tie),pair)
    names = [f'{label}:{strength}:{side}' for strength in PUBLIC_STRENGTHS
             for label in ('finishing','setting') for side in ('min','max')]
    names += [f'{role}:{block}:{kind}' for role in ('F','D') for block in ('shooter','setter')
              for kind in ('smallest_positive_support','first_prior_only')]
    names += [field+':'+side for field in STAGE_FIELDS for side in ('min','max')]
    names += ['largest_tip_supported_fraction']
    selected = set()
    for name in names:
        pair = best[name][1] if name in best else None
        requirements.append(dict(requirement=name,pair=None if pair is None else list(pair),
                                 disposition='unavailable' if pair is None else 'selected'))
        if pair is not None:
            selected.add(pair)
    require(len(selected) <= 45, 'execution resolution selector exceeds bound')
    return dict(pairs=[list(pair) for pair in sorted(selected,key=lambda pair:(PUBLIC_STRENGTHS.index(pair[1]),pair[0]))],
                requirements=requirements,
                tip_fraction_definition='focal shooter full-joint exact-strength physical tip attempts / all focal full-joint exact-strength physical attempts; zero denominator unavailable',
                scope='bounded focal pairs; every baseline panel row; no all-player error bound')


def reevaluate_execution_panel(state, panel, design):
    """change saved logits only; frozen source membership and masses stay exact."""
    from .execution_design import origins_for
    require(state.manifest['season'] == panel.season == design.season
            and state.manifest['prepared'] == design.prepared
            and state.manifest['coaches'] == design.coaches
            and state.manifest['recipe'] == design.recipe, 'execution probe binding differs')
    predictors = {p.key:p for p in design.predictors}
    upstream,goal = [],[]
    for index,row in enumerate(panel.events):
        predictor = predictors[row['key']]
        require(tuple(predictor.context['strength']) == panel.strength, 'execution probe physical state differs')
        cells,weights = origins_for(predictor)
        start,end = panel.arrays['event_offsets'][index:index+2]
        require(np.array_equal(cells,panel.arrays['origin_cells'][start:end])
                and np.array_equal(weights,panel.arrays['origin_weights'][start:end]),
                'execution probe changed origin membership or mass')
        u,g = _neutral_panel_logits(state,predictor,cells)
        upstream.append(u); goal.append(g)
    arrays = dict(panel.arrays)
    arrays['neutral_upstream_logits'] = np.concatenate(upstream) if upstream else np.empty((0,3))
    arrays['neutral_goal_logits'] = np.concatenate(goal) if goal else np.empty((0,2))
    # the checked tighter variant changes coefficients/centers, never actor
    # axes, labels, candidates or prior lineage. support sets remain baseline.
    return replace(panel,arrays=arrays)


def compare_execution_projections(baseline, variant):
    """measure the frozen pair's full-panel scalar and native-map movements."""
    require(all(baseline[k] == variant[k] for k in ('season','player_id','strength'))
            and baseline['reference_panel']['panel_id'] == variant['reference_panel']['panel_id'],
            'execution resolution compares different pairs or panels')
    scalar_changes = {}
    passed = True
    for field,left in baseline['values'].items():
        right = variant['values'][field]
        require((left is None) == (right is None), 'execution probe changed scalar availability')
        change = None if left is None else abs(right-left)
        scalar_changes[field] = change
        tolerance = 1e-3 if field in (FINISHING,SETTING) else 1e-5
        passed = passed and (change is None or change <= tolerance)
    maps = {}
    for kind,left in baseline['native_maps'].items():
        right = variant['native_maps'][kind]
        require((left is None) == (right is None), 'execution probe changed map availability')
        maps[kind] = None if left is None else fsum(np.abs(right-left))
        passed = passed and (maps[kind] is None or maps[kind] <= 1e-3)
    return dict(status='passed' if passed else 'failed',scalar_absolute_changes=scalar_changes,
                native_map_l1_changes=maps,
                neutral_panel_goal_mass_change=variant['reference_panel']['neutral']['uqrg']-baseline['reference_panel']['neutral']['uqrg'])


def score_execution_event(state, predictor, disposition=None, *, facts=None, observed_setter=-1):
    """score one physical or explicitly synthetic predictor through all coalitions."""
    from .execution_design import origins_for
    from .chance import TYPES
    season = state.manifest['season']
    if disposition is None:
        parts = predictor.key.split(':')
        source_index = int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else 0
        disposition = dict(key=predictor.key,game_id=parts[0],source_index=source_index,
            outcome='block' if predictor.blocked else None,full_probability_context=True,pointer=None,
            heads={head:dict(included=False,target=None,reasons=[]) for head in HEADS})
    key = disposition['key']
    actors = {} if predictor is None else predictor.actors
    strength = None if predictor is None else tuple(predictor.context['strength'])
    setters,shares = [],[]
    identity = dict(season=season, game_id=disposition['game_id'], source_index=disposition['source_index'])
    row = dict(identity, key=key, shooter_id=actors.get('shooter'), goalie_id=actors.get('goalie'),
               attacking_coach_id=actors.get('attacking_coach'), defending_coach_id=actors.get('defending_coach'),
               physical_state=None if strength is None else (*strength, 1),
               shot_type=None if predictor is None else TYPES[predictor.shot_type], outcome=disposition['outcome'],
               heads=disposition['heads'], status='excluded', reasons=[], prefixes=None,
               coalition_goal_mass=None, conditional_probabilities=None)
    row.update(facts or {})
    if not disposition['full_probability_context']:
        reasons = sorted({reason for h in HEADS for reason in disposition['heads'][h]['reasons']
                          if reason not in ('requires_unblocked','requires_on_net','immediate_stop_label_unavailable','recorded_stopped_save')})
        row['reasons'] = [dict(code=reason, game_id=identity['game_id'], source_index=identity['source_index'],
                               pointer=disposition['pointer']) for reason in reasons]
        require(bool(row['reasons']), 'excluded execution event lacks a reason')
        return dict(event=row,setters=[],shares=[],panel_piece=None)
    cells, weights = origins_for(predictor)
    # evaluate the four sparse designs once per physical attempt. residual
    # changes are constant across origins; all coalitions reuse these logits.
    context = _execution_context(state, predictor, cells)
    neutral_upstream, neutral_goal = context['upstream'], context['goal']
    candidates, prior = context['candidates'], context['prior']
    coalitions = np.empty((16,len(cells),len(candidates)))
    prefixes = {}
    conditionals = {}
    actual_prediction = None
    for subset in range(16):
        prediction = _coalition_prediction(context, subset)
        coalitions[subset] = prediction.terminal_probabilities['goal']
        if subset in (0,11,15):
            name = {0:'neutral',11:'neutral_goalie',15:'actor'}[subset]
            prefixes[name] = integrated_prefixes(prediction, weights)
            conditionals[name] = {denominator:conditional_goal_probability(prediction,weights,denominator)
                                  for denominator in ('u','uq')}
        if subset == 15:
            actual_prediction = prediction
    allocation = execution_shapley(coalitions)
    coalition_mass = [float(_weighted_probability(
        _weighted_probability(values, prior, axis=1), weights, axis=0)) for values in coalitions]
    # these three entries are the same saved quantities, not independent
    # reductions with a second rounding identity.
    for subset,name in ((0,'neutral'),(11,'neutral_goalie'),(15,'actor')):
        coalition_mass[subset] = prefixes[name]['uqrg']
    unblocked = disposition['outcome'] != 'block'
    on_net = disposition['outcome'] in ('save','goal')
    conditional_probabilities = dict(
        actor_unblocked_goal_probability=conditionals['actor']['u'] if unblocked else None,
        actor_on_net_goal_probability=conditionals['actor']['uq'] if on_net else None,
        neutral_goalie_on_net_goal_probability=conditionals['neutral_goalie']['uq'] if on_net else None,
        neutral_on_net_goal_probability=conditionals['neutral']['uq'],
        neutral_goalie_unblocked_goal_probability=conditionals['neutral_goalie']['u'])
    row.update(status='complete', prefixes=prefixes, coalition_goal_mass=coalition_mass,
               conditional_probabilities=conditional_probabilities)
    joint_mass = fsum(weights) * fsum(prior)
    for group, recipient, index in (('shooter',actors['shooter'],0),('goalie',actors['goalie'],2),('coach','coaching_context',3)):
        shares.append(dict(identity, group=group, recipient_id=recipient,
                           goals=fsum(weights*(allocation[index] @ prior)) / joint_mass))
    observed = observed_setter
    posterior = None
    if disposition['heads']['g']['included']:
        if observed >= 0:
            posterior = np.zeros(len(prior)); posterior[observed] = 1.
        else:
            likelihood = actual_prediction.goal_log_likelihoods[int(disposition['heads']['g']['target'])]
            with np.errstate(divide='ignore'):
                log_weights = np.log(weights)
            log_joint = np.log(prior)+logsumexp(log_weights[:,None]+likelihood,axis=0)
            posterior = np.exp(log_joint-logsumexp(log_joint))
    for j, candidate in enumerate(candidates):
        recipient = candidate.actor_id if candidate.kind in ('skater','goalie') else candidate.kind
        setters.append(dict(identity, candidate_id=recipient, pre_outcome_weight=float(prior[j]),
                            posterior_weight=None if posterior is None else float(posterior[j]), recorded_assist_evidence=[]))
        amount = fsum(weights*allocation[1,:,j])*prior[j] / joint_mass
        if candidate.kind != 'skater':
            require(abs(amount) <= 2e-15, 'non-skater setter receives execution credit')
            amount = 0.
        shares.append(dict(identity, group='setter', recipient_id=recipient, goals=float(amount)))
    require(abs(fsum(s['goals'] for s in shares[-(len(candidates)+3):])-(coalition_mass[15]-coalition_mass[0])) <= 3e-14,
            'integrated event execution allocation does not close')
    role_actor = next((a['role'] for a in state.heads['g']['actors']
                       if a['block'] == 'shooter' and a['id'] == actors['shooter']),None)
    panel_row = dict(identity, key=key, shot_type=TYPES[predictor.shot_type], tip=predictor.tip,
                     role=role_actor, hand=predictor.context['candidate']['hand'],
                     attacking_coach_applicable=actors['attacking_coach'] is not None,
                     defending_coach_applicable=actors['defending_coach'] is not None)
    return dict(event=row,setters=setters,shares=shares,panel_piece=(panel_row,cells,weights,neutral_upstream,neutral_goal))


def neutral_panel_masses(panel):
    """reduce saved neutral logits without interpreting any fitted coefficient."""
    masses, setup_goal, levels, _, _, _, _ = _projection_neutral(panel, retain_origin_values=False)
    return dict(prefixes={name: float(value) for name, value in zip(PREFIXES, masses, strict=True)},
                setup_goal_mass=setup_goal,
                stage_levels=dict(zip(STAGE_FIELDS, levels, strict=True)))


def neutral_panel_event_masses(panel):
    """stream per-physical-event neutral reductions under saved origin/setup mass."""
    arrays = panel.arrays
    for index, event in enumerate(panel.events):
        start, end = arrays['event_offsets'][index:index + 2]
        upstream = arrays['neutral_upstream_logits'][start:end]
        goal = arrays['neutral_goal_logits'][start:end]
        setup = arrays['setup_weights'][index]
        weights = arrays['origin_weights'][start:end]
        logs = _joint_log_prefixes(upstream, goal, setup)
        masses = _integrated_log_columns(logs, weights)
        setup_goal = float(setup[1] * _weighted_probability(
            np.exp(logs[:, 2]) * expit(goal[:, 1]), weights, axis=0))
        yield dict(key=event['key'],
                   prefixes={name: float(_weighted_probability(np.exp(logs[:, j]), weights, axis=0))
                             for j, name in enumerate(PREFIXES)},
                   setup_goal_mass=setup_goal,
                   neutral_on_net_goal_probability=float(np.exp(masses[3] - masses[1])))


def _integrated_log_columns(log_prefixes, weights):
    with np.errstate(divide='ignore'):
        log_weights = np.log(weights)
    return logsumexp(log_weights[:, None] + log_prefixes, axis=0)


def _levels_from_log_masses(logs, opportunities, unblocked_mass):
    return (float(unblocked_mass / opportunities),
            float(np.exp(logs[1] - logs[0])),
            float(-np.expm1(logs[2] - logs[1])),
            float(np.exp(logs[3] - logs[2])))
