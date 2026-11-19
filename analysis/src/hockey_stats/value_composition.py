"""compose the common-workload ledger from selected, already-saved evidence."""

from copy import deepcopy
from hashlib import sha256
from math import fsum
from pathlib import Path
from resource import getrusage, RUSAGE_SELF
from time import perf_counter

from . import analysis_publication as publication
from .analysis_data import read_prepared, read_reported_usage, validate_reported_usage
from .artifacts import implementation_identity, linked_path, require, write_json
from .captures import strict_json
from .chance_cli import identity, output_path
from .descriptive import estimate
from .execution_scores import read_execution_score_events
from .input_locations import input_path, same_input_reference
from .mechanism_state import read_mechanism_state, read_minor_reference
from .player_mechanisms import reduce_shorthanded_reference, validate_shorthanded_reference
from .player_value import (
    STATES, TERMS, WORKLOAD, build_depth_groups, build_state_references, compose_depth_reference,
    compose_player_value, execution_panel, ledger_close, ledger_values,
)
from .value_evidence import ledger_dependencies, validate_ledger_year
from .territory_state import read_saved_territory_values


def _receipt(binding):
    return dict(uri=binding['path'], sha256=binding['sha256'])


def _binding(receipt):
    return dict(path=receipt['uri'], sha256=receipt['sha256'])


def _read(path):
    return strict_json(input_path(path, strict=True).read_bytes())


def _selection(path, source, manifest):
    selection = _read(path)
    publication.fields(selection, ('schema_version', 'purpose', 'prepared', 'source_results', 'years'))
    require(type(selection['schema_version']) is int and selection['schema_version'] == 1
            and selection['purpose'] == manifest['purpose']
            and same_input_reference(selection['source_results'], source)
            and selection['prepared']['sha256'] == manifest['prepared_sha256'],
            'ledger selection purpose or donor/preparation differs')
    require(type(selection['years']) is list
            and [row['season'] for row in selection['years']] == manifest['seasons'], 'ledger years differ')
    bindings = [selection['prepared']]
    for item in selection['years']:
        publication.fields(item, ('season', 'execution_score', 'penalty_state', 'shootiness_state',
            'territory_diagnostics', 'usage_reduction', 'shorthanded_reduction'))
        required = ('execution_score', 'penalty_state', 'shootiness_state')
        require(all(item[key] is not None for key in required), 'missing ledger state binding')
        require(item['season'] == '20252026' or item['territory_diagnostics'] is None,
                'territory diagnostics require the final year')
        if selection['purpose'] == 'real' and item['season'] == '20252026':
            require(item['territory_diagnostics'] is not None, 'real final-year territory diagnostics required')
        bindings.extend(item[key] for key in item if key != 'season' and item[key] is not None)
    for binding in bindings:
        publication.fields(binding, ('path', 'sha256'))
        linked_path(binding)
    return selection


def _provided(rows):
    return next((row['data'] for row in rows if row['availability'] == 'provided'), None)


def _pool(strength, support, reduction):
    seconds = support['included_seconds']
    rate = estimate(3600 * support['attempts'] / seconds) if seconds else estimate(
        None, reason='no_exposure',
        explanation='no matched source-pooled shorthanded time')
    return rate, dict(kind='source_pool', strength=strength, reduction=reduction, **support)


def _common(sources, minor, sh, reduction, shootiness, saved_panels):
    spatial = sources['skater_spatial']
    pp = _provided(row for (_, state), row in spatial.items() if state == 'pp')
    require(pp is not None, 'ledger requires the saved physical pp mixture')
    weights = {row['strength']: row['weight'] for row in pp['state_weights']}
    attempts = {}
    panels = {}
    for strength in STATES:
        if strength in ('5v5', *publication.SPATIAL_STATES):
            rows = [row for (_, state), row in spatial.items() if state == strength]
            require(rows, 'ledger lacks spatial state rows')
            donor = _provided(rows)
            if donor is None:
                neutral = estimate(None, reason='not_computed', explanation=rows[0]['explanation'])
            else:
                neutral = donor['offense_attempts_per60_neutral']
            attempts[strength] = (neutral, dict(kind='spatial', strength=strength,
                method_id=donor['method_id'] if donor else None, quantity='offense_attempts_per60_neutral'))
        elif strength == '4v5':
            attempts[strength] = _pool(strength, minor['sh_support'], minor['inputs']['reduction'])
        else:
            attempts[strength] = _pool(strength, sh['strengths'][strength]['sh_support'], _receipt(reduction))
        rows = [row for (_, state), row in sources['skater_execution'].items() if state == strength]
        saved = saved_panels[strength]
        panel = next((execution_panel(row) for row in rows if row['availability'] == 'provided'),None)
        if panel is None:
            panel = dict(panel_id=saved['panel_id'],opportunities=saved['events'],setup_weight=.8*saved['events'])
        require(panel['panel_id'] == saved['panel_id'] and panel['opportunities'] == saved['events']
                and ledger_close(panel['setup_weight'],.8*saved['events'],(.8*saved['events'],)),
                'ledger common execution panel differs from bound score')
        panels[strength] = panel
    problem = None
    if shootiness.reference['kind'] == 'unavailable':
        failed = shootiness.head['status'] == 'failed'
        problem = estimate(None, reason='failed_fit' if failed else 'no_exposure',
                           explanation='saved annual shootiness reference is unavailable')
        if failed:
            failed_row = _provided(sources['skater_shootiness'].values())
            require(failed_row is not None, 'failed shootiness state lacks bound donor method')
            problem['reason_detail']['evidence'] = [dict(kind='method', id=failed_row['method_id'])]
    return weights, attempts, panels, problem


def _movement(player_results, variant_results, base_positions, variant_positions, affected):
    quantities = {}

    def compare(key, before, after, subject):
        require((before is None) == (after is None), 'saved diagnostic changes value availability')
        if before is None:
            return
        change = abs(fsum((after, -before)))
        item = quantities.setdefault(key, dict(maximum_goals=0., worst=None, compared=0))
        item['compared'] += 1
        if change > item['maximum_goals']:
            item.update(maximum_goals=change, worst=subject)

    for pid, before in player_results.items():
        after = variant_results[pid]
        for term in TERMS:
            for basis in ('league_goals', 'replacement_goals'):
                compare(f'{term}.{basis}', before['components'][term][basis]['value'],
                        after['components'][term][basis]['value'], pid)
        for basis in ('league_goals', 'replacement_goals'):
            compare(f'penalties_combined.{basis}', before['penalties_combined'][basis]['value'],
                    after['penalties_combined'][basis]['value'], pid)
        for key in ('league_total', 'replacement_total'):
            compare(key, before[key]['value'], after[key]['value'], pid)
    for pos in ('F', 'D'):
        before, after = base_positions[pos]['components'], variant_positions[pos]['components']
        for term in TERMS:
            compare(f'{pos}.reference.{term}', before and before[term], after and after[term], pos)
        compare(f'{pos}.reference.total', fsum(before.values()) if before else None,
                fsum(after.values()) if after else None, pos)
    for item in quantities.values():
        item['exceeds_budget'] = item['maximum_goals'] > 1e-3
    assessed = any(f'{term}.league_goals' in quantities for term in affected)
    return dict(status='exceeded' if any(item['exceeds_budget'] for item in quantities.values()) else
                'within_budget' if assessed else 'unassessed',
                reason=None if assessed else 'no comparable affected term',
                budget_goals=1e-3, quantities=quantities)


def _replace_values(row, values, *, reference_id=None, position=None):
    require(row['availability'] == 'provided', 'saved diagnostic has no donor row')
    data = dict(row['data'])
    for key, value in values.items():
        require((data[key]['value'] is None) == (value is None), 'saved baseline and variant are incompatible')
        if value is not None:
            data[key] = estimate(value)
    if reference_id is not None:
        require(data['evidence']['position_group'] == position, 'shootiness probe changes annual role')
        data['evidence'] = dict(data['evidence'], reference_id=reference_id)
    return dict(row, data=data)


def _diagnostics(year, selected, source, people, components, positions, fixed_members,
                 league, player_results, common, penalty, minor, shootiness):
    weights, attempts, panels, problem = common
    diagnostics = {}
    if year != '20252026':
        require(selected['territory_diagnostics'] is None, 'earlier annual territory diagnostic is unassessed')
        return dict(status='unassessed', reason='earlier annual')
    for name, state in (('penalties', penalty), ('shootiness', shootiness)):
        probe = state.probe
        if probe is None or not probe['projections'] or (name == 'penalties' and not minor['available']):
            diagnostics[name] = dict(status='unassessed', reason='saved compatible projection unavailable')
            continue
        vectors = {}
        if name == 'penalties':
            probe_rows = {r['player_id']:r for r in probe['projections']}
            for pid in people:
                spatial, execution, shooter, baseline, territory = components(pid)
                variant = baseline
                if baseline['availability'] == 'provided':
                    r = probe_rows[pid]
                    values = {f'{role}_value_per60': sign * r[f'{role}_per60'] * minor['V_goals'] if r[f'{role}_per60'] is not None else None
                              for role, sign in (('drawn', 1), ('taken', -1))}
                    variant = _replace_values(baseline, values)
                vectors[pid] = compose_player_value(spatial, execution, shooter, variant, territory, source)['league']
        else:
            probe_rows = {(r['player_id'], r['strength']):r for r in probe['projections']}
            ref = probe['reference']
            variant_common = build_state_references(weights, attempts, panels, ref, None)
            for pid in people:
                spatial, execution, shooter, penalties, territory = components(pid)
                variant = {}
                for strength in STATES:
                    if shooter[strength]['availability'] != 'provided':
                        variant[strength] = shooter[strength]
                        continue
                    r = probe_rows[pid,strength]
                    variant[strength] = _replace_values(shooter[strength],
                        {key:r[key] for key in ('probability', 'neutral_probability')},
                        reference_id=ref['sha256'], position=r['position_group'])
                vectors[pid] = compose_player_value(spatial, execution, variant, penalties, territory, variant_common)['league']
        depth = {pos:compose_depth_reference(members, vectors) for pos,members in fixed_members.items()}
        values = {pid:ledger_values(vector, positions[pid]['group'], depth, vectors) for pid,vector in vectors.items()}
        affected = ('penalties_drawn','penalties_taken') if name == 'penalties' else ('finishing','setting')
        diagnostics[name] = _movement(player_results, values, league, depth, affected)
    territory_binding = selected['territory_diagnostics']
    if territory_binding is None:
        diagnostics['territory'] = dict(status='unassessed', reason='saved compatible projection unavailable')
        return diagnostics
    exemplar = next(components(pid)[-1]['data']['evidence'] for pid in people
                    if components(pid)[-1]['availability'] == 'provided')
    evidence = exemplar['successor_reference']
    expected = dict(purpose=selected['purpose'], season=year, annual_state=_binding(exemplar['annual_state']),
        ev_state=_binding(evidence['ev_state']), panel=None if evidence['panel'] is None else _binding(evidence['panel']))
    variants = read_saved_territory_values(territory_binding, expected)
    saved = _read(territory_binding['path'])['diagnostics']
    statuses = {row['status'] for row in saved.values()}
    diagnostics['territory_upstream'] = dict(status='exceeded' if 'exceeded' in statuses else
        'within_budget' if statuses == {'within_budget'} else 'unassessed')
    baseline = variants.pop('baseline')
    if baseline is None:
        require(selected['purpose'] != 'real' and all(
            row['availability'] != 'provided' or all(row['data'][f'ice_{term}_goals_per_basket']['value'] is None
                for term in ('won','lost')) for row in (components(pid)[-1] for pid in people)),
            'selected territory diagnostic baseline differs from donor availability')
        require(all(rows is None for rows in variants.values()), 'territory variant lacks a comparable baseline')
        diagnostics['territory'] = dict(status='unassessed',reason='saved baseline unavailable')
        return diagnostics
    for pid in people:
        territory = components(pid)[-1]
        if territory['availability'] != 'provided':
            continue
        data = territory['data']
        actual = [data[f'ice_{term}_goals_per_basket']['value'] for term in ('won', 'lost')]
        require(pid in baseline and all((a is None and b is None) or (a is not None and b is not None and ledger_close(a,b,(b,)))
                    for a,b in zip(actual, baseline[pid], strict=True)), 'territory diagnostic baseline differs from donor scalar')
    for name, rows in variants.items():
        if rows is None:
            require(selected['purpose'] != 'real', 'accepted real territory variant is unavailable')
            diagnostics[f'territory_{name}'] = dict(status='unassessed', reason='saved projection unavailable')
            continue
        vectors = {}
        for pid in people:
            spatial, execution, shooter, penalties, territory = components(pid)
            if territory['availability'] == 'provided':
                territory = _replace_values(territory, dict(zip(
                    ('ice_won_goals_per_basket', 'ice_lost_goals_per_basket'), rows[pid], strict=True)))
            vectors[pid] = compose_player_value(spatial, execution, shooter, penalties, territory, source)['league']
        depth = {pos:compose_depth_reference(members, vectors) for pos,members in fixed_members.items()}
        values = {pid:ledger_values(vector, positions[pid]['group'], depth, vectors) for pid,vector in vectors.items()}
        diagnostics[f'territory_{name}'] = _movement(player_results, values, league, depth, ('ice_won','ice_lost'))
    return diagnostics


def _method(year, purpose, annual, source_methods, meaning, selection, diagnostics, score, additional_bindings):
    limits = [
        'experimental common-workload component index with uncertainty unestimated',
        '5v5, pp and pk minutes are hypothetical common workloads and can include prior-supported roles',
        'the allocation uses an ordinary team-attempt rate that may include recorded goalie attempts across skater slots',
        'creation times own execution and penalty-created minutes times own special-teams skill are omitted',
        'depth averages regularized estimates using complete team-position groups and one fixed weight per player',
        'execution and spatial aggregate numerical accuracy remain unassessed',
    ]
    years = sorted({year for method in source_methods for year in method['fit_seasons']})
    cutoffs = [method['training_cutoff'] for method in source_methods if method['training_cutoff'] is not None]
    semantic = publication.reference_digest(dict(components=[list(row) for row in sorted(meaning)], workload=WORKLOAD,
        depth_policy='fixed-complete-team-position-12F-6D-common-seconds-v1'))
    bindings = [
        *(dict(role=role, sha256=ref['sha256'], seasons=[year])
          for role,ref in zip(('prepared', 'source_results', 'derivation', 'derivation', 'annual_state'),
                              annual['inputs'].values(), strict=True)),
        dict(role='derivation', sha256=annual['reference_id'], seasons=[year]),
        dict(role='execution_score',sha256=score['sha256'],seasons=[year]),
    ]
    for method in source_methods:
        for binding in method['inputs']:
            if binding not in bindings:
                bindings.append(binding)
    evidence = [*annual['inputs'].values(), score, *additional_bindings, selection,
        dict(uri=f"urn:hockey-stats:ledger-reference:{year}", sha256=annual['reference_id'])]
    for method in source_methods:
        for binding in method['evidence']:
            if binding not in evidence:
                evidence.append(binding)
    target = 'goals over 1,000 5v5, 100 pp and 100 pk minutes'
    quantity_paths = sorted(path for path in publication.QUANTITY_PATHS if path.startswith('value_ledger.'))
    finding = 'aggregate optimizer accuracy and calibrated uncertainty remain unassessed'
    if year == '20252026':
        statuses = ', '.join(f"{name.replace('_', ' ')} {result['status'].replace('_', ' ')}"
                             for name,result in diagnostics.items() if name != 'territory_upstream')
        finding += f'. saved ledger sensitivity at 0.001 goals marks {statuses}'
    findings = [dict(quantities=quantity_paths, population=target, summary=finding, evidence=evidence)]
    for family, components in {
        'spatial':('five_on_five_offense','five_on_five_defense','power_play_offense','penalty_kill_defense','finishing','setting'),
        'execution':('finishing','setting'), 'shootiness':('finishing','setting'),
        'penalties':('penalties_drawn','penalties_taken'), 'territory':('ice_won','ice_lost')
    }.items():
        constituent = [method for method in source_methods if method['family'] == family and method['assessment']['findings']]
        if not constituent:
            continue
        affected = [path for path in quantity_paths if path.endswith('_total')
                    or any(f'.{term}.' in path for term in components)
                    or family == 'penalties' and '.penalties_combined.' in path]
        wording = {
            'spatial':'spatial values inherit the saved reference and optimizer limits',
            'execution':'execution has saved selected-pair sensitivity evidence and unassessed downstream accuracy',
            'shootiness':'conditional shooter share depends on fitted role offsets and fixed unit composition',
            'penalties':'isolated-minor valuation uses a mixed reference and omits overlaps',
            'territory':'territory uses an inferred terminal-zone carry',
        }[family]
        if family == 'territory':
            status = diagnostics.get('territory_upstream', {}).get('status', 'unassessed')
            wording += f'. inherited territory sensitivity {status.replace("_"," ")}'
        upstream_evidence = {receipt['uri']:receipt for item in constituent for receipt in item['evidence']}
        findings.append(dict(quantities=affected,population=target,summary=wording,
                             evidence=list(upstream_evidence.values())))
    return dict(method_id=annual['method_id'], family='ledger', purpose=purpose, recipe_id='value-v1-12-1',
        design_sha256=semantic, input_sha256=sha256(
            publication.json_bytes(bindings)).hexdigest(),
        fit_seasons=years, training_cutoff=max(cutoffs, default=None), target=target,
        population='skater-season over fixed common workload; depth ranks use complete reported team-position groups',
        reference='league-standardized component index and annual F/D roster-depth means',
        limitations=limits, evidence=evidence, inputs=bindings, reference_id=semantic,
        support_policy_id='complete-team-position-fixed-depth-v1',
        assessment=dict(status='experimental', findings=findings))


def _component_meanings(sources, methods):
    meanings = {}
    for table, upstream in sources.items():
        for key, row in upstream.items():
            axis = table, key[1] if isinstance(key,tuple) else ''
            labels = meanings.setdefault(axis,set())
            if row['availability'] == 'provided':
                method = methods[row['data']['method_id']]
                labels.add(tuple(method[field] for field in ('recipe_id','reference_id','support_policy_id')))
    return meanings


def compose_value(current_results, selection_path, output):
    """assemble a complete current exchange while preserving every inherited table member."""
    began = perf_counter()
    current_results = input_path(current_results, strict=True)
    source = identity(current_results/'manifest.json')
    manifest = _read(source['path'])
    require(manifest.get('schema_version') == 6 and manifest.get('kind') == 'player_analysis_results',
            'ledger requires a current exchange 6 donor')
    selection = _selection(selection_path, source, manifest)
    purpose = selection['purpose']
    existing = publication.read_result_catalogs(current_results)
    for record in existing.manifest['families']:
        if record['family'] != 'ledger':
            continue
        for table, member in record['tables'].items():
            require(all(row['result']['availability'] == 'not_computed' for row in existing.rows(member,table,'ledger')),
                    'ledger donor conflicts with computed owned rows')
    prepared = read_prepared(selection['prepared']['path'], purpose)
    state_roots = [str(Path(item[key]['path']).parent) for item in selection['years']
                   for key in ('execution_score','penalty_state','shootiness_state','territory_diagnostics')
                   if item[key] is not None]
    output = output_path(str(output), [str(current_results), str(prepared.directory), *state_roots])
    if purpose == 'real':
        require(output.is_relative_to('/Volumes/Expansion/hockey-stats/runs'), 'real ledger output must use external runs')
    output.mkdir()
    artifacts = output/'value'
    artifacts.mkdir()
    method_catalog = dict(existing.catalogs['method'])
    years = existing.manifest['seasons']
    bound_sources = {year:publication.ledger_sources(existing,year) for year in years}
    by_year = {year:_component_meanings(sources,method_catalog) for year,sources in bound_sources.items()}
    meanings_by_axis = {axis:set().union(*(values[axis] for values in by_year.values()))
                        for axis in by_year[years[0]]}
    annuals = {}
    for selected in selection['years']:
        started = perf_counter()
        year = selected['season']
        sources = bound_sources.pop(year)
        people = sorted(pid for (season,pid),person in existing.people.items()
                        if season == year and person['kind'] == 'skater')
        require(people, 'ledger year has no published skaters')
        usage_binding = selected['usage_reduction']
        if usage_binding is None:
            usage = read_reported_usage(prepared, year)
            path = artifacts/f'{year}-usage.json'
            write_json(path, usage, compact=True)
            usage_binding = identity(path)
        else:
            usage = _read(usage_binding['path'])
            validate_reported_usage(usage, prepared, year)
        scores = read_execution_score_events(selected['execution_score']['path'],purpose)
        require(scores.manifest['season'] == year
                and scores.manifest['prepared']['sha256'] == selection['prepared']['sha256'],
                'execution scores differ from ledger year/preparation')
        sh_binding = selected['shorthanded_reduction']
        if sh_binding is None:
            sh = reduce_shorthanded_reference(prepared,scores)
            path = artifacts/f'{year}-shorthanded.json'
            write_json(path, sh, compact=True)
            sh_binding = identity(path)
        else:
            sh = _read(sh_binding['path'])
            validate_shorthanded_reference(sh,prepared,scores)
        source_seconds = perf_counter()-started
        mechanism = {}
        for family,selector in (('penalties','penalty_state'), ('shootiness','shootiness_state')):
            state = read_mechanism_state(selected[selector]['path'],purpose,family,narrow=True)
            require(state.manifest['season']==year and state.manifest['prepared']['sha256']==selection['prepared']['sha256'],
                    f'{family} selection differs from ledger year/preparation')
            projections = {(r['player_id'],r.get('strength')):r for r in state.projections}
            upstream = sources['skater_'+family]
            for key,row in upstream.items():
                if row['availability'] != 'provided':
                    continue
                data = row['data']
                require(same_input_reference(_binding(data['evidence']['annual_state']),selected[selector]),
                        f'{family} stored donor state differs')
                value = projections[key if isinstance(key,tuple) else (key,None)]
                for field in ('probability','neutral_probability') if family == 'shootiness' else ('drawn_per60','taken_per60'):
                    require(data[field]['value'] == value[field], f'{family} saved baseline differs from donor')
            mechanism[family] = state
        penalty = _provided(sources['skater_penalties'].values())
        require(penalty is not None, 'the bound 4v5 minor opportunity is required')
        minor = penalty['evidence']['valuation']
        minor_inputs = minor['inputs']
        require(same_input_reference(_binding(minor_inputs['execution_score']), selected['execution_score']),
                '4v5 minor counts/time bind another execution score')
        for strength,key in (('5v5','ev_state'), ('pp','st_state')):
            source_row = _provided(row for (_,state),row in sources['spatial_evidence'].items() if state == strength)
            require(source_row is not None and same_input_reference(_binding(source_row['annual_state']), _binding(minor_inputs[key])),
                    f'{strength} spatial and 4v5 minor lineages differ')
        minor_path = input_path(minor_inputs['reduction']['uri'], strict=True).parent/'minor-reference.json'
        accepted_minor = read_minor_reference(minor_path,purpose,year,expected_inputs=dict(
            prepared=selection['prepared'], execution_score=selected['execution_score'],
            ev_state=_binding(minor_inputs['ev_state']), st_state=_binding(minor_inputs['st_state'])))
        require(accepted_minor['valuation'] == minor, 'accepted minor reference differs from donor')
        shooter = mechanism['shootiness']
        saved_score = _receipt(selected['execution_score'])
        for table in ('skater_execution','skater_spatial'):
            method_ids = {row['data']['method_id'] for row in sources[table].values() if row['availability'] == 'provided'}
            for id_ in method_ids:
                upstream = method_catalog[id_]
                require(any(same_input_reference(_binding(receipt),selected['execution_score'])
                            for receipt in upstream['evidence']) if table == 'skater_execution' else
                        any(item['role'] == 'opportunity_panel' and item['sha256'] == saved_score['sha256']
                            for item in upstream['inputs']), 'ledger donor opportunity panel uses another score')
        descriptors = {(str(panel['state']['attacking_skaters'])+'v'+str(panel['state']['defending_skaters'])):panel
                       for panel in scores.manifest['panels'] if panel['state']['attacking_goalies'] == 1
                       and panel['state']['defending_goalies'] == 1}
        common = _common(sources,minor,sh,sh_binding,shooter,descriptors)
        refs = build_state_references(*common[:3], shooter.reference, common[3])
        groups,fixed_members = build_depth_groups(usage)
        depth_positions = usage['positions']
        positions = {pid:depth_positions.get(pid,dict(group='unknown', mixed=False, forward_seconds=0,
                         defense_seconds=0,unknown_seconds=0,missing_time_records=0)) for pid in people}

        def components(pid):
            return (
                {strength:sources['skater_spatial'][pid,strength] for strength in publication.SPATIAL_STRENGTHS},
                {strength:sources['skater_execution'][pid,strength] for strength in STATES},
                {strength:sources['skater_shootiness'][pid,strength] for strength in STATES},
                sources['skater_penalties'][pid], sources['skater_territory'][pid],
            )

        players = {pid:compose_player_value(*components(pid),refs) for pid in people}
        vectors = {pid:row['league'] for pid,row in players.items()}
        depth = {pos:compose_depth_reference(members,vectors) for pos,members in fixed_members.items()}
        inputs = {key:_receipt(binding) for key,binding in (
            ('prepared',selection['prepared']),('source_results',source),('usage_reduction',usage_binding),
            ('shorthanded_reduction',sh_binding),('shootiness_state',selected['shootiness_state']))}
        annual = dict(season=year,method_id=f'value-v1-12-{year}',inputs=inputs,
                      state_references=refs,groups=groups,positions=depth)
        annual['reference_id'] = publication.reference_digest(annual)
        player_results = {pid:ledger_values(vectors[pid],positions[pid]['group'],depth,vectors) for pid in people}
        if year == '20252026':
            territory_methods = {r['data']['method_id'] for r in sources['skater_territory'].values()
                                 if r['availability'] == 'provided'}
            declared = {(receipt['uri'],receipt['sha256']) for id_ in territory_methods for receipt in method_catalog[id_]['evidence']
                        if any(item['role'] == 'derivation' and item['sha256'] == receipt['sha256']
                               and item['seasons'] == [year] for item in method_catalog[id_]['inputs'])}
            require(len(declared) <= 1, 'territory donor disagrees on saved annual diagnostics')
            if selected['territory_diagnostics'] is not None:
                require(any(same_input_reference(dict(path=path,sha256=sha), selected['territory_diagnostics'])
                            for path,sha in declared), 'territory diagnostic selection differs from donor')
            elif declared:
                path,sha = next(iter(declared))
                try:
                    saved = _read(linked_path(dict(path=path,sha256=sha)))
                except FileNotFoundError:
                    saved = None
                require(saved is None or not any(row['successor_available'] for name,row in saved['projections'].items()
                            if name != 'baseline'), 'saved fixture territory variants require selection')
        diagnostics = _diagnostics(year,dict(selected,purpose=purpose),refs,people,components,positions,
            fixed_members,depth,player_results,common,mechanism['penalties'],minor,shooter)
        inherited_ids = sorted({row['data']['method_id'] for table in sources.values()
                                for row in table.values() if row['availability'] == 'provided'})
        # A withheld state inherits a definition only when every available year agrees.
        meanings = set()
        for axis, local in by_year[year].items():
            known = meanings_by_axis[axis]
            labels = local or (known if len(known) == 1 else ())
            meanings.update((*axis,*label) for label in labels)
        method = _method(year,purpose,annual,[method_catalog[id_] for id_ in inherited_ids],meanings,
            _receipt(identity(Path(selection_path).absolute())),diagnostics,saved_score,
            [_receipt(selected[key]) for key in ('penalty_state','territory_diagnostics')
             if selected[key] is not None])
        require(method['method_id'] not in method_catalog, 'ledger method identity conflicts')
        method_catalog[method['method_id']] = method

        rows = []
        for pid in people:
            spatial, execution, shooting, penalties, territory = components(pid)
            spatial_evidence = {strength:sources['spatial_evidence'][pid,strength] for strength in publication.SPATIAL_STRENGTHS}
            deps, support = ledger_dependencies(spatial,spatial_evidence,execution,shooting,penalties,territory,method_catalog)
            evidence = dict(annual_reference_id=annual['reference_id'],depth_position=positions[pid],
                unit_position=players[pid]['unit_position'],inputs=deps,
                execution_states=players[pid]['execution_states'],dependency_support=support)
            data = dict(reference_minutes=WORKLOAD,**player_results[pid],method_id=method['method_id'],evidence=evidence)
            rows.append(dict(season=year,player_id=pid,result=dict(availability='provided',explanation=None,data=data)))
        reference = dict(season=year,result=dict(availability='provided',explanation=None,data=annual))
        catalogs = dict(existing.catalogs,method=method_catalog)
        publication.validate_catalog('methods',method,purpose,catalogs,existing.manifest['prepared_sha256'])
        publication.validate_row('ledger_reference',reference,'ledger',catalogs,existing.people)
        for row in rows:
            publication.validate_row('value_ledger',row,'ledger',catalogs,existing.people)
        inventory = {}
        for game in usage['games']:
            for team in game['team_ids']:
                inventory.setdefault(team,set()).add(game['game_id'])
        validate_ledger_year(reference['result'],{row['player_id']:row['result'] for row in rows},sources,catalogs,inventory)
        reference_member = publication.write_result_member(output,f'{year}-ledger-reference.jsonl',[reference],'ledger_reference')
        value_member = publication.write_result_member(output,f'{year}-value-ledger.jsonl',rows,'value_ledger')
        details = dict(schema_version=1,kind='value_reference',purpose=purpose,season=year,
            reference=reference_member, annual_reference_id=annual['reference_id'], inputs=inputs)
        reference_document = artifacts/f'{year}-reference.json'
        write_json(reference_document,details)
        annuals[year] = dict(reference_id=annual['reference_id'], reference=identity(reference_document), tables=dict(ledger_reference=reference_member,value_ledger=value_member),
            depth={pos:dict(available=depth[pos]['available'],members=depth[pos]['member_count'],seconds=depth[pos]['total_seconds'],
                excluded_groups=[g['team_id'] for g in groups if g['position']==pos and g['status']=='excluded'],
                missing_vectors=depth[pos]['missing_vectors']) for pos in ('F','D')},
            diagnostics=diagnostics,source_seconds=source_seconds,total_seconds=perf_counter()-started)
        print(f'{year} ledger references: {[(pos,d["available"],d["members"],d["seconds"]) for pos,d in annuals[year]["depth"].items()]}',
              flush=True)
    manifest = deepcopy(existing.manifest)
    manifest['producer'] = implementation_identity()
    for family in manifest['families']:
        if family['family'] == 'ledger':
            family.update(availability='provided',explanation=None,tables=annuals[family['season']]['tables'])
            continue
        for member in family['tables'].values():
            publication.copy_result_member(existing.directory, member, output)
    for name in ('people','sources','supports'):
        publication.copy_result_member(existing.directory,manifest['catalogs'][name],output)
    manifest['catalogs']['methods'] = publication.write_result_member(output,'methods.jsonl',
        sorted(method_catalog.values(),key=lambda row:row['method_id']),'methods')
    staged = output/'manifest.json.incomplete'
    write_json(staged,manifest)
    publication.read_results(output,staged.name)
    staged.rename(output/'manifest.json')
    write_json(output/'value-results.json',dict(schema_version=1,kind='value_results',purpose=purpose,
        input_selection=identity(Path(selection_path).absolute()),source_results=source,output=identity(output/'manifest.json'),
        annuals=annuals, resources=dict(wall_seconds=perf_counter()-began,peak_memory_bytes=getrusage(RUSAGE_SELF).ru_maxrss,
            output_bytes=sum(path.stat().st_size for path in output.rglob('*') if path.is_file()))))
    return manifest
