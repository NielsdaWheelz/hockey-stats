"""two source-bound goalie continuation heads and pure saved-state evaluation."""

from dataclasses import dataclass, field, replace
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.special import expit

from .artifacts import implementation, linked_path, require, resources
from .analysis_data import PreparedManifest
from .chance_cli import identity, output_path
from .execution_design import (RECIPE as EXECUTION_RECIPE, prepare_execution_sources,
                               build_head_design, predictor_matrix)
from .execution_fit import fit_head, continue_head

HEADS = ('h', 'd')
TARGETS = dict(h='saved attempt: immediately next recorded same-team ordinary attempt within five seconds',
               d='positive recorded reattempt: fully neutral successor all-attempt opportunity')
DEFINITION = dict(version='goalie-continuation-v1-07-1', heads=TARGETS,
                  encoding=dict(execution_recipe_sha256=EXECUTION_RECIPE['sha256'],
                                formula='q/r geometry, circumstances and actors; own eligible-row moments and supports; no setter'),
                  target_kinds=dict(h='binary', d='fractional'),
                  history='head-specific raw last-supported entry-or-carry; exact prior-only completion',
                  solver=dict(maxiter=10000, ftol=1e-15, gtol=1e-6, maxfun=15000,
                              continuation=dict(maxiter=10000, ftol=1e-16, gtol=1e-7, maxfun=15000)),
                  sensitivity=dict(pointwise_threshold=1e-5, summary_threshold=1e-4,
                                   policy='diagnostic, completed baseline is retained; no automatic retry'),
                  reference='virtual neutral actor residuals; fixed neutral saved-shot branch weighting')
RECIPE = dict(name='experimental-v1', version=DEFINITION['version'],
              sha256=sha256(json.dumps(DEFINITION, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
              definition=DEFINITION)


@dataclass
class GoalieDesign:
    purpose: str
    season: str
    prepared: dict
    coaches: dict
    base_state: dict
    base_scores: dict
    training_cutoff: str
    seasons: tuple
    predictors: tuple
    heads: dict
    targets: tuple
    coverage: dict
    source_games: tuple
    resources: dict = field(default_factory=dict)
    recipe: dict = field(default_factory=lambda: RECIPE)
    execution_state: object = None
    execution_scores: object = None


@dataclass(frozen=True)
class GoalieInputs:
    purpose: str
    season: str
    prepared: dict
    coaches: dict
    base_state: dict
    base_scores: dict
    training_cutoff: str
    seasons: tuple
    predictors: tuple
    targets: tuple
    coverage: dict
    source_games: tuple
    people: dict
    source_actors: dict
    head_keys: dict
    resources: dict
    recipe: dict
    execution_state: object
    execution_scores: object


def prepare_goalie_scoring(prepared, coaches, annual_execution_scores, season):
    """replay source predictors once, binding each danger target to saved base scores."""
    from .execution_scores import ExecutionScores, read_execution_scores
    from .descriptive import reduce_goalie_game

    started = perf_counter()
    require(isinstance(prepared, PreparedManifest), 'goalie needs a checked prepared manifest')
    scores = annual_execution_scores
    if not isinstance(scores, ExecutionScores):
        scores = read_execution_scores(scores, prepared['purpose'])
    require(scores.manifest['season'] == season and scores.manifest['purpose'] == prepared['purpose'],
            'goalie base-score season/purpose differs')
    source = prepare_execution_sources(prepared, coaches, season, game_reducer=reduce_goalie_game)
    require(scores.manifest['prepared'] == source.prepared and scores.manifest['coaches'] == source.coaches,
            'goalie preparation/coaches differ from base scores')
    # fit/score bind the base manifest explicitly; detached state readers never reopen it.
    base = scores.manifest['state']
    base_path = linked_path({key: base[key] for key in ('path', 'sha256')})
    from .execution_state import read_execution_state
    execution_state = read_execution_state(base_path, source.purpose)
    score_ref = identity(scores.path)
    event_rows = list(scores.events())
    valued = {row['key']: row for row in event_rows}
    require(len(valued) == len(event_rows), 'duplicate base event target keys')
    targets = _target_rows(source.source_rows,valued,score_ref['sha256'])
    coverage = target_coverage(targets, season)
    head_keys = {h:tuple(r['key'] for r in targets if r[h+'_included']) for h in HEADS}
    return GoalieInputs(source.purpose, season, source.prepared, source.coaches, dict(base), score_ref,
                        source.training_cutoff, source.seasons, source.predictors, tuple(targets),
                        coverage, source.source_games, source.people, source.source_actors, head_keys,
                        dict(design_wall_seconds=perf_counter()-started, input_read_wall_seconds=0.),
                        RECIPE, execution_state, scores)


def prepare_goalie(prepared, coaches, annual_execution_scores, season):
    """construct independent likelihood designs from the shared source/target inputs."""
    inputs = prepare_goalie_scoring(prepared, coaches, annual_execution_scores, season)
    started = perf_counter()
    targets = {row['key']:row for row in inputs.targets}
    responses = [dict(h=float(targets[p.key]['h_label']) if targets[p.key]['h_included'] else None,
                      d=targets[p.key]['d_target'], observed_setter=-1) for p in inputs.predictors]
    heads = {head:build_head_design(head,inputs.predictors,responses,inputs.people,inputs.source_actors) for head in HEADS}
    for head in HEADS:
        heads[head]['target_kind'] = DEFINITION['target_kinds'][head]
    measured = dict(inputs.resources,design_wall_seconds=inputs.resources['design_wall_seconds']+perf_counter()-started)
    return GoalieDesign(inputs.purpose,inputs.season,inputs.prepared,inputs.coaches,inputs.base_state,inputs.base_scores,
                        inputs.training_cutoff,inputs.seasons,inputs.predictors,heads,inputs.targets,inputs.coverage,
                        inputs.source_games,measured,RECIPE,inputs.execution_state,inputs.execution_scores)


def _target_rows(source_rows,valued,score_sha256):
    """join immediate source labels to exact saved successor targets, without fitting."""
    targets = []
    for row in source_rows:
        key = row['key']
        reasons = list(row['predictor_reasons'])
        goalie = row['goalie_identity']['player_id']
        if goalie is None:
            reasons.append(row['goalie_identity']['reason'])
        if row['outcome'] != 'save':
            reasons.append('requires_saved_attempt')
        if row['h_label'] is None:
            reasons.append('immediate_reattempt_label_unavailable')
        reasons = list(dict.fromkeys(reasons))
        h_included = not reasons
        successor = valued.get(row['successor_key'])
        danger, danger_reason = None, None
        if not h_included:
            danger_reason = 'focal_occurrence_population_unavailable'
        elif row['h_label'] is not True:
            danger_reason = 'requires_positive_recorded_reattempt'
        elif successor is None or successor['status'] != 'complete':
            danger_reason = 'successor_execution_score_unavailable'
        else:
            danger = successor['prefixes']['neutral']['uqrg']
            require(type(danger) in (int, float) and np.isfinite(danger) and 0 <= danger <= 1,
                    'invalid fully neutral successor danger target')
        target = dict(key=key, game_id=row['game_id'], source_index=row['source_index'],
                      outcome=row['outcome'], physical_status=row['physical_status'], goalie_id=goalie,
                      physical_state=row['physical_state'], h_label=row['h_label'],
                      h_reason=None if row['h_problem'] is None else row['h_problem']['reason'],
                      successor_key=row['successor_key'], target_score_sha256=score_sha256,
                      d_target=danger, d_reason=danger_reason,
                      h_included=h_included, d_included=danger is not None,
                      h_exclusions=reasons)
        targets.append(target)
    return tuple(targets)


def target_coverage(targets, season):
    """head, exact state and goalie counts retain separate likelihood populations."""
    groups = {}
    for row in targets:
        state = tuple(row['physical_state']) if row['physical_state'] is not None else None
        for head in HEADS:
            key = head, state, row['goalie_id']
            group = groups.setdefault(key, dict(head=head, season=season,
                physical_state=None if state is None else list(state), goalie_id=row['goalie_id'],
                included=0, excluded=0, target_mass=0., known_positives=0, valued_positives=0,
                exclusion_reasons={}))
            included = row[head+'_included']
            group['included' if included else 'excluded'] += 1
            group['known_positives'] += int(row['h_label'] is True)
            group['valued_positives'] += int(row['d_included'])
            if included:
                group['target_mass'] += float(row['h_label'] if head == 'h' else row['d_target'])
            else:
                reasons = row['h_exclusions'] if head == 'h' else [row['d_reason']]
                for reason in reasons:
                    group['exclusion_reasons'][reason] = group['exclusion_reasons'].get(reason, 0)+1
    return dict(season=season, attempts=len(targets), groups=list(groups.values()))


def _goalie_logits(state,predictors,origin_cells,blocks):
    from .goalie_state import GoalieState

    require(isinstance(state,GoalieState),'goalie evaluation needs checked saved state')
    cells=np.asarray(origin_cells)
    require(cells.ndim==1 and cells.dtype.kind in ('i','u') and len(cells)==len(predictors)
            and np.all((cells>=0)&(cells<656)),'invalid goalie origin cells')
    result={}
    for head in HEADS:
        metadata=state.heads[head]
        if metadata['status']!='complete':
            result[head]=None
            continue
        offsets=np.empty(len(predictors))
        start=0
        supported=True
        while start<len(predictors):
            predictor=predictors[start]
            end=start+1
            while end<len(predictors) and predictors[end] is predictor:
                end+=1
            for block,axis in metadata['design']['actor_indices'].items():
                if block in blocks or block=='shooter' and predictor.tip:
                    continue
                actor=predictor.actors.get(block)
                if actor is not None and actor not in axis or actor is None and not block.endswith('coach'):
                    supported=False
                    break
            if not supported:
                break
            offsets[start:end]=sum(metadata['centers'][block]['value']
                for block in metadata['design']['actor_indices'] if block in blocks
                and not (block=='shooter' and predictor.tip)
                and not (block.endswith('coach') and predictor.actors.get(block) is None))
            start=end
        if not supported:
            result[head]=None
            continue
        matrix=predictor_matrix(metadata['design'],predictors,cells,omit_actors=blocks)
        result[head]=np.asarray(matrix@state.arrays[head]['coefficients']).ravel()+offsets
        require(result[head].shape==cells.shape and np.isfinite(result[head]).all(),'invalid goalie logits')
    return result


def goalie_logits(state,focal_predictors,origin_cells,neutralize=()):
    """evaluate one focal context at explicit origins; unavailable heads remain absent."""
    blocks=set(neutralize)
    require(blocks<={'shooter','setter','goalie','coaching','attacking_coach','defending_coach'},
            'unknown goalie neutralization group')
    if 'coaching' in blocks:
        blocks.update(('attacking_coach','defending_coach'))
    require(len(origin_cells)>0,'goalie focal evaluation needs at least one origin')
    return _goalie_logits(state,[focal_predictors]*len(origin_cells),origin_cells,blocks)


def goalie_reference_logits(state,predictors,origin_cells):
    """evaluate aligned origin rows with all applicable actor residuals neutral."""
    return _goalie_logits(state,predictors,origin_cells,
                         {'shooter','goalie','attacking_coach','defending_coach'})


def goalie_probabilities(state, focal_predictors, origin_cells, neutralize=()):
    values = goalie_logits(state, focal_predictors, origin_cells, neutralize)
    return tuple(None if values[head] is None else expit(values[head]) for head in HEADS)


def _metadata(design, result, incoming, season):
    from .execution import _centered_state

    history = {(r['block'], str(r['id'])): r for r in incoming}
    actors, priors = [], []
    for row in result['actors']:
        actors.append({key: row[key] for key in ('index','block','id','role','age','source_support',
                                                'likelihood_support','center_weight','prior_only')})
        prior = {key: row.get(key) for key in ('block','id','mean','precision','age_delta',
                                              'age_indices','transition_reason','prior_mean')}
        prior['last_supported'] = history.get((row['block'], str(row['id'])))
        priors.append(prior)
    complete = result['status'] == 'complete'
    centers, ledger = _centered_state(result, incoming, season) if complete else (None, incoming)
    return dict(head=design['head'], target=TARGETS[design['head']], target_kind=design['target_kind'],
                target_mass=float(design['target'].sum()), keys=design['keys'],
                design=design['design'], actors=actors, priors=priors, centers=centers, ledger=ledger,
                arrays=None, starts=result['starts'], selected_start=result['selected_start'],
                diagnostics=dict(result.get('diagnostics', {}), requested_starts=result['requested_starts'],
                                 wall_seconds=result['wall_seconds']), status=result['status'], reasons=result['reasons'])


def _selector(design):
    ordered = sorted((p for p in design.predictors if p.actors['goalie'] is not None),
                     key=lambda p: (p.key.split(':')[0], int(p.key.split(':')[1])))
    targets = {row['key']: row for row in design.targets}
    selected, requirements = {}, []
    def select(name, candidates):
        witness = next(iter(candidates), None)
        requirements.append(dict(requirement=name, key=None if witness is None else witness.key))
        if witness is not None and len(selected) < 256:
            selected[witness.key] = witness
    for strength in sorted({tuple(p.context['strength']) for p in ordered}):
        select('state:'+','.join(map(str,strength)), (p for p in ordered if tuple(p.context['strength']) == strength))
    for kind in range(6):
        select('type:'+str(kind), (p for p in ordered if p.shot_type == kind))
    select('tip', (p for p in ordered if p.tip))
    select('missingness', (p for p in ordered if any(v['status'] == 'unavailable' for v in p.context['features'].values())))
    for label in (False, True):
        select('h:'+str(label).lower(), (p for p in ordered if targets[p.key]['h_label'] is label))
    positive = [p for p in ordered if targets[p.key]['d_target'] is not None]
    for name, reverse in (('d_low',False),('d_high',True)):
        ranked = sorted(positive, key=lambda p: targets[p.key]['d_target'], reverse=reverse)
        select(name, ranked)
    for head in HEADS:
        sparse = sorted((r for r in design.heads[head]['actors'] if r['block']=='goalie'),
                        key=lambda r: (r['likelihood_support'], r['id']))
        select('low_support:'+head, (p for p in ordered if sparse and p.actors['goalie']==sparse[0]['id']))
    for predictor in ordered:
        if len(selected) == 256:
            break
        selected[predictor.key] = predictor
    keys = sorted(selected, key=lambda k: (k.split(':')[0],int(k.split(':')[1])))
    return dict(policy='deterministic source-key coverage then fill; maximum256; all656 origins per context',
                keys=keys, requirements=requirements), tuple(selected[key] for key in keys)


def fit_goalie_year(design, previous, output):
    """save baselines before bounded final-year probes; failures retain incoming history."""
    from .goalie_state import (GoalieState, read_goalie_state, write_goalie_head,
                               write_goalie_state, freeze_goalie_baseline, write_goalie_probe)

    require(isinstance(design, GoalieDesign) and design.recipe == RECIPE, 'unsupported goalie design')
    first = '20212022' if design.purpose == 'real' else min(design.seasons)
    if design.season == first:
        require(previous is None, 'first selected goalie season forbids previous state')
    else:
        require(previous is not None, 'later goalie season requires previous annual state')
        if not isinstance(previous, GoalieState):
            previous = read_goalie_state(previous, design.purpose)
        year = int(design.season[:4])
        require(previous.usage == 'annual' and previous.manifest['season'] == f'{year-1}{year}'
                and previous.manifest['recipe'] == RECIPE
                and all(previous.manifest[name][key] == getattr(design,name)[key]
                        for name in ('prepared','coaches') for key in ('path','sha256','purpose')),
                'goalie predecessor lineage differs')
        require(design.base_state['previous']=={key:previous.manifest['base_state'][key] for key in ('path','sha256')},
                'goalie base execution predecessor differs')
    roots = [str(Path(design.prepared['path']).parent),str(Path(design.coaches['path']).parent),
             str(Path(design.base_scores['path']).parent)]
    if previous is not None:
        roots.append(str(previous.path.parent))
    output = output_path(str(output), roots)
    if design.purpose=='real':
        require(output.is_relative_to('/Volumes/Expansion/hockey-stats'),'expensive real outputs must be external')
    output.mkdir()
    (output/'heads').mkdir()
    started = perf_counter()
    heads, arrays = {}, {}
    for head in HEADS:
        incoming = [] if previous is None else previous.heads[head]['ledger']
        result = fit_head(design.heads[head], incoming)
        heads[head] = _metadata(design.heads[head], result, incoming, design.season)
        arrays[head] = {} if result['status'] != 'complete' else dict(coefficients=result['coefficients'])
        write_goalie_head(output, heads[head], arrays[head], design.season)
    predecessor = None if previous is None else dict(identity(previous.path), season=previous.manifest['season'],
                    purpose=design.purpose, recipe_sha256=RECIPE['sha256'], usage='annual')
    manifest = dict(schema_version=1,kind='goalie-continuation',purpose=design.purpose,season=design.season,
                    recipe=RECIPE,implementation=implementation(),prepared=design.prepared,coaches=design.coaches,
                    base_state=design.base_state,base_scores=design.base_scores,previous=predecessor,
                    training_cutoff=design.training_cutoff,resources={})
    probes = {}
    final = design.season == ('20252026' if design.purpose == 'real' else max(design.seasons))
    if final:
        selector, predictors = _selector(design)
        baseline = freeze_goalie_baseline(output, manifest, heads, design.targets, selector)
        base_state = GoalieState(output/'manifest.json',manifest,heads,arrays,dict(targets=list(design.targets),summary=design.coverage))
        for head in HEADS:
            if heads[head]['status'] != 'complete':
                probes[head] = dict(status='not_run',reason='baseline_'+heads[head]['reasons'][0])
                continue
            incoming = [] if previous is None else previous.heads[head]['ledger']
            result = continue_head(design.heads[head],incoming,arrays[head]['coefficients'])
            metadata = _metadata(design.heads[head],result,incoming,design.season)
            probe_arrays = {} if result['status'] != 'complete' else dict(coefficients=result['coefficients'])
            comparison = {key:value for key,value in result['comparison'].items()
                          if key not in ('em_maxiter','em_relative_tolerance','em_responsibility_tolerance')}
            comparison['optimizer_maxfun'] = 15000
            comparison.update(status='unassessed',contexts=len(predictors),origin_rows=656*len(predictors),
                              maximum_probability_change=None,maximum_joint_change=None,pointwise_threshold=1e-5,
                              compared_probability_rows=0,compared_joint_rows=0)
            if result['status'] == 'complete':
                changed_heads = dict(heads,**{head:metadata}); changed_arrays = dict(arrays,**{head:probe_arrays})
                variant = replace(base_state,heads=changed_heads,arrays=changed_arrays)
                changes, joint = [], []
                for predictor in predictors:
                    for neutralize in ((),('shooter','goalie','coaching')):
                        left = goalie_probabilities(base_state,predictor,np.arange(656),neutralize)
                        right = goalie_probabilities(variant,predictor,np.arange(656),neutralize)
                        index = HEADS.index(head)
                        if left[index] is not None and right[index] is not None:
                            changes.append(float(np.max(np.abs(left[index]-right[index]))))
                        if all(x is not None for x in left+right):
                            joint.append(float(np.max(np.abs(left[0]*left[1]-right[0]*right[1]))))
                comparison.update(status='assessed',maximum_probability_change=max(changes) if changes else None,
                                  maximum_joint_change=max(joint) if joint else None,
                                  compared_probability_rows=656*len(changes),compared_joint_rows=656*len(joint))
            probes[head] = write_goalie_probe(output,head,baseline,metadata,probe_arrays,comparison,design.season)
    measured = resources(started)
    measured.update(design_wall_seconds=design.resources['design_wall_seconds'],
                    input_read_wall_seconds=design.resources['input_read_wall_seconds'],
                    dimensions={h:design.heads[h]['size'] for h in HEADS},
                    solve_counts={h:sum(r.get('deduplicated_to') is None for r in heads[h]['starts']) for h in HEADS},
                    probe_solve_counts={h:int(final and heads[h]['status']=='complete') for h in HEADS},
                    output_bytes=0)
    manifest['resources'] = measured
    return write_goalie_state(output,manifest,heads,arrays,design.targets,design.coverage,probes)
