"""publish saved penalty and shooter-choice projections through the current exchange."""

from ast import literal_eval
from copy import deepcopy
import hashlib
from pathlib import Path
from time import perf_counter

from .input_locations import input_path, same_input_reference
from . import analysis_publication as publication
from .artifacts import implementation_identity, linked_path, require, require_number, write_json
from .captures import InputContractError, strict_json
from .chance_cli import identity, output_path
from .descriptive import estimate


def _method(family, year, state, annuals, selection, minor, minor_binding, diagnostic):
    years = [item for item in annuals if item <= year]
    inputs = [dict(role='prepared',sha256=selection['prepared']['sha256'],seasons=years),
              dict(role='source_results',sha256=selection['source_results']['sha256'],seasons=[year]),
              *[dict(role='annual_state',sha256=identity(annuals[item][family].path/'manifest.json')['sha256'],seasons=[item]) for item in years]]
    if family == 'penalties':
        inputs.append(dict(role='coaches',sha256=selection['coaches']['sha256'],seasons=years))
    binding = identity(state.path/'manifest.json')
    evidence = [dict(uri=binding['path'],sha256=binding['sha256'])]
    if minor is not None:
        evidence.append(dict(uri=minor_binding['path'],sha256=minor_binding['sha256']))
        evidence.extend(minor['valuation']['inputs'].values())
    summary = (f"baseline {state.head['status']}; numerical sensitivity {diagnostic['status']}; "
               'optimizer accuracy unknown; in-sample diagnostics are not held-out accuracy; calibrated uncertainty not estimated')
    rate_diagnostic = diagnostic.get('rate',diagnostic)
    if rate_diagnostic is not None and rate_diagnostic.get('projection_maximum') is not None:
        summary += (f"; maximum standardized movement {rate_diagnostic['projection_maximum']} and actual fitting-row movement "
                    f"{rate_diagnostic['fitting_row_maximum']} {'awards/hour' if family == 'penalties' else 'fraction'}; "
                    f"comparison budget {rate_diagnostic['budget']}")
    value_diagnostic = diagnostic.get('value')
    if value_diagnostic is not None:
        summary += (f"; maximum penalty-value movement {value_diagnostic['maximum_goals_per_hour']} goals/hour and "
                    f"{value_diagnostic['maximum_goals_per_1000_minutes']} goals per 1000 minutes; budgets 1e-4 and 1e-3 respectively")
    if family == 'penalties':
        population = 'genuine 5v5 two-direction ordinary-minor team awards; both goalies; independent matched membership and award exclusions'
        reference = 'frozen league-centered virtual team; one focal drawing/taking player; positive taking means more team penalties; isolated two-minute value uses mixed hypothetical ev/pp and source-pooled sh references'
        limitations = ['ordinary MIN/BEN two-minute net team counts after opposing cancellation; not named-person responsibility or all penalty minutes',
            'the isolated-minor value omits overlap, 5v3, regulation truncation and focal specialty skill; negative value is retained',
            'source-pooled sh circumstances differ from hypothetical ev/pp references; sh goals do not terminate the opportunity']
    else:
        population = 'ordinary physical team attempts in seven strengths; actual attacking skater candidates; conditional on an attempt occurring'
        reference = 'same-position focal slot in fixed common F/D unit; fitted reporting role offsets; all other player deviations zero'
        limitations = ['shared seven-state shooter coefficient is not observed shot share, finishing, shot volume or causal isolation',
            'selected-state qualifying minutes are separate from pooled candidate information; zero-state-time projections are hypothetical',
            'unknown position has no standardized F/D projection; fixed role weights, units and age-neutral priors are initial assumptions']
    return dict(method_id=f'{family}-v1-10-{year}',family=family,purpose=selection['purpose'],recipe_id=f'{family}-v1-10-1',
        design_sha256=state.manifest['design_identity'],input_sha256=hashlib.sha256(publication.json_bytes(inputs)).hexdigest(),
        fit_seasons=years,training_cutoff=state.manifest['training_cutoff'],target='ordinary-minor drawing/taking rate and value contrasts' if family == 'penalties' else 'conditional share of team attempts',
        population=population,reference=reference,limitations=[*limitations,summary,'conditional point-history borrowing; no calibrated intervals or scientific ability admission'],
        evidence=evidence,inputs=inputs,reference_id='isolated-minor-league-centered-v1' if family == 'penalties' else 'shooter-common-unit-v1',
        support_policy_id='penalty-independent-membership-awards-v1' if family == 'penalties' else 'shootiness-independent-qualification-pooled-candidates-v1',
        assessment=dict(status='experimental',findings=[dict(quantities=[f'{"skater_penalties" if family == "penalties" else "skater_shootiness"}.{field}'
            for field in publication.ESTIMATE_FIELDS['skater_penalties' if family == 'penalties' else 'skater_shootiness']],population=population,summary=summary,evidence=evidence)]))


def _datum(value, state, method, person, *, valuation=None, unknown_position=False):
    if value is not None:
        return estimate(value)
    status = state.head['status']
    reason = 'failed_fit' if status == 'failed' else 'no_exposure' if status == 'unavailable' else 'missing_source' if unknown_position else valuation['reason']
    require(reason in ('failed_fit','no_exposure','missing_source'), 'missing mechanism estimate has no declared prerequisite reason')
    result = estimate(None,reason=reason,explanation='saved mechanism prerequisite unavailable: '+reason)
    result['reason_detail']['evidence'] = [dict(kind='method',id=method),*person['source']]
    return result


def _rows(family, year, state, people, method, minor, facts):
    projections = {(row['player_id'],row.get('strength')):row for row in state.projections}
    support = {row['player_id']:row for row in state.support}
    require(len(projections) == len(state.projections) and len(support) == len(state.support), 'duplicate mechanism projection/support')
    annual = identity(state.path/'manifest.json')
    penalty_reference = hashlib.sha256(publication.json_bytes(dict(penalty_reference=state.reference['sha256'],minor_reference=minor['reference_id'],
        valuation=minor['valuation'],units='awards_per_hour_and_goals_per_isolated_minor'))).hexdigest() if family == 'penalties' else None
    for person in people:
        player = person['player_id']
        require(player in support, 'published skater lacks saved mechanism support')
        saved = support[player]
        coefficient = saved['coefficient_support']
        for strength in ((None,) if family == 'penalties' else sorted(publication.EXECUTION_STRENGTHS)):
            require((player,strength) in projections, 'published skater lacks saved mechanism projection')
            projection = projections[player,strength]
            selected = saved if strength is None else next(row for row in saved['states'] if row['strength'] == strength)
            qualification = dict(included_seconds=selected['included_seconds'],events=coefficient['likelihood_events'],eligible_weight=coefficient['information_weight'],
                known_excluded_seconds=selected['known_excluded_seconds'],unquantified_gap=selected['unquantified_gap'],reason_counts=[],inferred_inputs=[],
                current_season_information=coefficient['current_season_information'],prior_only=coefficient['prior_only'],prior_seasons=coefficient['prior_seasons'])
            evidence = dict(annual_state=dict(uri=annual['path'],sha256=annual['sha256']),coefficient_support=coefficient,reference_id=projection['reference_id'])
            if family == 'penalties':
                require(player in facts and facts[player]['availability'] == 'provided', 'modeled penalty row requires authoritative recorded facts')
                factual = facts[player]['data']['recorded_penalties']['focal']
                valuation = minor['valuation']
                values = {key:_datum(projection[key],state,method,person) for key in ('drawn_per60','taken_per60')}
                for role,sign in (('drawn',1),('taken',-1)):
                    value = sign*projection[role+'_per60']*valuation['V_goals'] if projection[role+'_per60'] is not None and valuation['available'] else None
                    values[role+'_value_per60'] = _datum(value,state,method,person,valuation=valuation)
                evidence['reference_id'] = penalty_reference
                evidence.update(neutral_per60=projection['neutral_per60'],drawn_complete_per60=projection['drawn_complete_per60'],
                    taken_complete_per60=projection['taken_complete_per60'],valuation=valuation)
                values.update({f'recorded_{key}':factual[key] for key in ('drawn','taken','served')})
            else:
                values = {key:_datum(projection[key],state,method,person,unknown_position=projection['position_group'] == 'unknown')
                          for key in ('probability','neutral_probability','difference')}
                evidence.update(position_group=projection['position_group'],reference_unit=projection['reference_unit'],states=saved['states'])
            row = dict(season=year,player_id=player,result=dict(availability='provided',explanation=None,
                data=dict(**values,support=qualification,method_id=method,evidence=evidence)))
            if strength is not None:
                row['strength'] = strength
            yield row


def compose_mechanisms(existing_results, selection_path, output):
    from .mechanism_state import read_mechanism_selection, read_mechanism_state, read_minor_reference
    from .player_mechanisms import reduce_minor_reference, propagate_penalty_probe

    began = perf_counter()
    existing = publication.read_results(Path(existing_results))
    selection = read_mechanism_selection(selection_path,existing.manifest['purpose'])
    source_binding = identity(existing.directory/'manifest.json')
    require(same_input_reference(selection['source_results'], source_binding), 'selected current-schema mechanism donor differs')
    require(selection['prepared']['sha256'] == existing.manifest['prepared_sha256'], 'mechanism donor preparation differs')
    for record in existing.manifest['families']:
        if record['family'] in ('penalties','shootiness') and record['availability'] == 'provided':
            table = 'skater_penalties' if record['family'] == 'penalties' else 'skater_shootiness'
            require(all(row['result']['availability'] == 'not_computed' for row in existing.rows(record['tables'][table],table,record['family'])),
                    'conflicting computed mechanism rows in donor')
    annuals = {}
    for item in selection['years']:
        year = item['season']
        annuals[year] = {}
        for family in ('penalties','shootiness'):
            binding = item[family]
            require(identity(Path(binding['path'])) == binding, 'selected mechanism annual digest differs')
            state = read_mechanism_state(Path(binding['path']),selection['purpose'],family,narrow=True)
            require(state.manifest['season'] == year and all(state.manifest['prepared'][key] == value for key,value in selection['prepared'].items()), 'mechanism annual source/year differs')
            if family == 'penalties':
                require(all(state.manifest['coaches'][key] == value for key,value in selection['coaches'].items()), 'mechanism annual coaches differ')
            annuals[year][family] = state
        for name in ('ev_state','st_state'):
            manifest = strict_json(input_path(item[name]['path'], strict=True).read_bytes())
            require(manifest['season'] == year and manifest['prepared']['sha256'] == selection['prepared']['sha256']
                    and manifest['valued']['sha256'] == item['execution_score']['sha256'], 'minor input numerical lineage differs')
        for family in ('ev','st'):
            candidates = [method for method in existing.catalogs['method'].values() if method['family'] == 'spatial' and year in method['fit_seasons']
                and any(input['role'] == 'annual_state' and input['sha256'] == item[family+'_state']['sha256'] and input['seasons'] == [year] for input in method['inputs'])]
            if year in existing.manifest['seasons']:
                require(candidates, 'selected minor reference state differs from donor numerical lineage')
    require(set(existing.manifest['seasons']) <= set(annuals), 'mechanism annual selection omits published year')
    for record in existing.manifest['families']:
        family,year = record['family'],record['season']
        if family not in ('penalties','shootiness'):
            continue
        published = {player for (season,player),person in existing.people.items() if season == year and person['kind'] == 'skater'}
        state = annuals[year][family]
        require(published <= {row['player_id'] for row in state.support}
                and published <= {row['player_id'] for row in state.projections}, 'published skater lacks saved mechanism coordinates')
        if family == 'penalties':
            factual = next(item for item in existing.manifest['families'] if item['season'] == year and item['family'] == 'descriptive')
            require(factual['availability'] == 'provided', 'mechanism donor lacks authoritative recorded penalty facts')

    output = output_path(str(output),[str(existing.directory),str(Path(selection_path).resolve())])
    if selection['purpose'] == 'real':
        require(output.is_relative_to('/Volumes/Expansion/hockey-stats'), 'real mechanism outputs must be external')
    output.mkdir()
    manifest = deepcopy(existing.manifest)
    manifest['producer'] = implementation_identity()
    methods = dict(existing.catalogs['method'])
    minor_references, minor_bindings, diagnostics = {}, {}, {}
    for item in selection['years']:
        year = item['season']
        if item['minor_reference'] is None:
            minor = reduce_minor_reference(Path(selection['prepared']['path']).parent,Path(item['execution_score']['path']),
                Path(item['ev_state']['path']),Path(item['st_state']['path']),output=output/f'{year}-minor-reference')
        else:
            minor = read_minor_reference(Path(item['minor_reference']['path']),selection['purpose'],year,
                expected_inputs=dict(prepared=selection['prepared'],**{key:item[key] for key in ('execution_score','ev_state','st_state')}))
        minor_references[year] = minor
        minor_bindings[year] = identity(output/f'{year}-minor-reference/minor-reference.json') if item['minor_reference'] is None else item['minor_reference']
        diagnostics[year] = {family:(annuals[year][family].probe['comparison'] if annuals[year][family].probe is not None else dict(status='not_assessed',reason='earlier_annual')) for family in ('penalties','shootiness')}
        if year == selection['years'][-1]['season']:
            diagnostics[year]['penalties'] = propagate_penalty_probe(annuals[year]['penalties'],minor)
    for record in manifest['families']:
        family,year = record['family'],record['season']
        if family not in ('penalties','shootiness'):
            for member in record['tables'].values():
                publication.copy_result_member(existing.directory,member,output)
            continue
        table = 'skater_penalties' if family == 'penalties' else 'skater_shootiness'
        state = annuals[year][family]
        method = _method(family,year,state,annuals,selection,minor_references[year] if family == 'penalties' else None,minor_bindings[year] if family == 'penalties' else None,diagnostics[year][family])
        require(method['method_id'] not in methods, 'mechanism method identity conflicts')
        methods[method['method_id']] = method
        people = sorted((person for (season,_),person in existing.people.items() if season == year and person['kind'] == 'skater'),key=lambda person:person['player_id'])
        factual_family = next(item for item in existing.manifest['families'] if item['season'] == year and item['family'] == 'descriptive')
        facts = {row['player_id']:row['result'] for row in existing.rows(factual_family['tables']['skater_descriptive'],'skater_descriptive','descriptive')} if family == 'penalties' else {}
        member = publication.write_result_member(output,f'{year}-{family}-{table}.jsonl',_rows(family,year,state,people,method['method_id'],minor_references[year],facts),table)
        record.update(availability='provided',explanation=None,tables={table:member})
    for name in ('people','sources','supports'):
        publication.copy_result_member(existing.directory,manifest['catalogs'][name],output)
    manifest['catalogs']['methods'] = publication.write_result_member(output,'methods.jsonl',sorted(methods.values(),key=lambda row:row['method_id']),'methods')
    write_json(output/'manifest.json.incomplete',manifest)
    publication.read_results(output,'manifest.json.incomplete')
    (output/'manifest.json.incomplete').rename(output/'manifest.json')
    write_json(output/'mechanism-composition.json',dict(schema_version=1,kind='mechanism_composition',purpose=selection['purpose'],
        source_results=source_binding,selection=identity(Path(selection_path).resolve()),output=identity(output/'manifest.json'),
        minor_references=minor_references,minor_reference_bindings=minor_bindings,diagnostics=diagnostics,resources=dict(wall_seconds=perf_counter()-began,
            output_member_bytes=sum((output/member['path']).stat().st_size for member in [*manifest['catalogs'].values(),
                *(member for record in manifest['families'] for member in record['tables'].values())])),
        preserved='all unrelated table members copied byte-for-byte; catalog records preserved; no ledger or territory estimate completed'))
    return manifest


def _territory_nuisance_coverage(raw):
    from collections import Counter
    from math import ceil,fsum
    import numpy as np
    from .territory_evidence import REASONS
    risk=np.asarray(raw['risk_seconds']);decidable=np.asarray(raw['decidable_whistles'])
    restart=np.asarray(raw['restart_counts']);lags=sorted(raw['terminal_lags'])
    censored=Counter(row['reason'] for game in raw['games'] for row in game['exclusions'] if row['kind']=='censored_endpoint')
    require(set(censored)<=set(REASONS),'territory censored endpoint lacks a declared reason mapping')
    prior_cells=[dict(process=process,zone=zone,age_lower=age)
        for process,denominator in (('w',risk),('d',risk),('h',decidable))
        for z,zone in enumerate(('D','N','O')) for b,age in enumerate((0,10,20,40,60,90)) if denominator[z,b]==0]
    return dict(path_slot_seconds=raw['path_slot_seconds'],terminal_carry_slot_seconds=raw['terminal_carry_slot_seconds'],
        whistle_risk_slot_seconds=fsum(risk.ravel()),whistle_incidences=int(np.asarray(raw['whistles']).sum()),
        live_end_risk_slot_seconds=fsum(risk.ravel()),live_end_incidences=int(np.asarray(raw['live_endings']).sum()),
        decidable_whistle_trials=int(decidable.sum()),ended_whistle_trials=int(np.asarray(raw['ended_whistles']).sum()),
        restart_pairs=int(restart.sum()),start_counts=[int(v) for v in raw['start_counts']],
        on_the_fly_zone_counts=[int(v) for v in raw['on_the_fly_zone_counts']],terminal_tails=len(lags),
        terminal_lag_seconds=None if not lags else dict(p50=lags[ceil(.5*len(lags))-1],p90=lags[ceil(.9*len(lags))-1],
            p99=lags[ceil(.99*len(lags))-1],max=lags[-1]),
        censored_endpoints=[dict(reason=reason,count=count) for reason,count in sorted(censored.items())],
        prior_only_cells=prior_cells,prior_only_restart_rows=[zone for z,zone in enumerate(('D','N','O')) if restart[z].sum()==0])


def _territory_datum(value,status,method,person):
    if value is not None:return estimate(float(value))
    reason='failed_fit' if status=='failed' else 'no_exposure' if status=='unavailable' else 'missing_source'
    datum=estimate(None,reason=reason,explanation='inferred territory prerequisite unavailable: '+reason)
    datum['reason_detail']['evidence']=[dict(kind='method',id=method),*person['source']]
    return datum


def _territory_rows(year,state,reference,people,method_id):
    from .territory import ROLES
    from .territory_evidence import reference_body
    from .artifacts import json_values
    baseline=reference['variants']['baseline'];computed=baseline['successor_available'];shift_computed=baseline['shift_available']
    hazards={row['player_id']:row for row in state.projections};support={row['player_id']:row for row in state.support}
    values={row['player_id']:row for row in baseline.get('values',[])}
    annual=identity(state.path/'manifest.json');manifest=reference['manifest']
    bind=lambda value:dict(uri=value['path'],sha256=value['sha256'])
    coverage=_territory_nuisance_coverage(state.design.nuisance)
    scalar_rows=[];map_rows=[];reference_id=None
    from .observed_spatial import cells
    geometry=cells()
    for person in people:
        player=person['player_id'];require(player in hazards and player in support,'published skater lacks territory state coordinates')
        selected=support[player];qualification=selected['qualification'];seconds=qualification['included_seconds']
        gap=any(game['unquantified_gap'] for game in state.coverage['games'])
        role_evidence={};role_data={};coefficient_rows=[]
        for role in ROLES:
            coefficient=selected['roles'][role]
            coefficient=dict(status=coefficient['status'],current_season_information=coefficient['current_season_information'],
                prior_only=coefficient['prior_only'],prior_kind=coefficient['prior_kind'],prior_anchor_season=coefficient['prior_anchor_season'],
                prior_seasons=coefficient['prior_seasons'],likelihood_events=coefficient['crossings'],information_weight=coefficient['risk_seconds'])
            coefficient_rows.append(coefficient)
            role_support=dict(included_seconds=seconds,events=coefficient['likelihood_events'],eligible_weight=coefficient['information_weight'],
                known_excluded_seconds=None,unquantified_gap=gap,reason_counts=[],inferred_inputs=sorted(['territory']+
                    (['historical_borrowing'] if coefficient['prior_seasons'] else [])),current_season_information=coefficient['current_season_information'],
                prior_only=coefficient['prior_only'],prior_seasons=coefficient['prior_seasons'])
            saved=hazards[player]['roles'][role]
            hazard_key='opponent_exit_hazard_per_second' if role=='zone_retention' else 'opponent_entry_hazard_per_second' if role=='entry_prevention' else 'hazard_per_second'
            role_data[role]={hazard_key:_territory_datum(saved['hazard_per_second'],saved['status'],method_id,person),
                'one_second_probability':_territory_datum(saved['one_second_probability'],saved['status'],method_id,person),'support':role_support}
            role_evidence[role]=dict(coefficient_support=coefficient,neutral_hazard_per_second=saved['neutral_hazard_per_second'],
                neutral_one_second_probability=saved['neutral_one_second_probability'])
        prior_years=sorted({year for row in coefficient_rows for year in row['prior_seasons']})
        main_support=dict(included_seconds=seconds,events=qualification['crossings'],eligible_weight=seconds,
            known_excluded_seconds=None,unquantified_gap=gap,reason_counts=[],inferred_inputs=sorted(['territory']+
                (['historical_borrowing'] if prior_years else [])),
            current_season_information=all(row['current_season_information'] for row in coefficient_rows),
            prior_only=all(row['status']=='complete' and row['prior_only'] for row in coefficient_rows),prior_seasons=prior_years)
        shift=None;successor=None
        if shift_computed:
            neutral=baseline['neutral'];value=values[player];nuisance=baseline['nuisance']
            shift=dict(initial_start_probabilities=nuisance['start_probabilities'],initial_on_the_fly_zone_probabilities=nuisance['on_the_fly_zone_mixture'],
                neutral_end_probabilities=neutral['end_probabilities'],focal_end_probabilities=value['end_probabilities'],
                end_difference=value['end_probability_difference'],neutral_occupancy_seconds=neutral['bin_occupancy_seconds'],
                mean_shift_seconds=neutral['mean_shift_seconds'],shifts_per_1000_minutes=neutral['shifts_per_1000_minutes'],
                survival_at_90=neutral['survival_at_90'],tail_time_fraction=neutral['tail_time_fraction'])
        if computed:
            G=baseline['successor_reference'];successor=dict(for_goals_per_shift=G['G'][0],against_goals_per_shift=G['G'][1],
                for_absolute_terms_goals_per_shift=G['absolute_term_scales'][0],against_absolute_terms_goals_per_shift=G['absolute_term_scales'][1])
        status='failed' if any(head['status']=='failed' for head in state.heads.values()) else 'unavailable' if any(head['status']=='unavailable' for head in state.heads.values()) else 'complete'
        reason=None if computed else manifest['panel_problem'] or baseline['reason']
        evidence=json_values(dict(annual_state=bind(annual),prepared=bind(state.manifest['prepared']),qualification_seconds=seconds,roles=role_evidence,
            nuisance_coverage=coverage,shift_reference=dict(available=shift_computed,reason=None if shift_computed else reason,receipt=bind(identity(reference['path'])),data=shift),
            successor_reference=dict(available=computed,reason=reason,ev_state=bind(manifest['ev_state']),
                panel=None if manifest['panel'] is None else bind(manifest['panel']),data=successor)))
        evidence['reference_id']=publication.reference_digest(reference_body(evidence,year,state.manifest['purpose'],'territory-v1-11-1'))
        if reference_id is None:reference_id=evidence['reference_id']
        require(reference_id==evidence['reference_id'],'territory common reference varies across players')
        data=dict(**role_data,support=main_support,method_id=method_id,evidence=evidence)
        for side,field in enumerate(('ice_won_goals_per_basket','ice_lost_goals_per_basket')):
            data[field]=_territory_datum(values[player]['values'][side] if computed else None,status,method_id,person)
        scalar_rows.append(dict(season=year,player_id=player,result=dict(availability='provided',explanation=None,data=data)))
        for side,kind in enumerate(('ice_won','ice_lost')):
            scalar=data['ice_won_goals_per_basket' if side==0 else 'ice_lost_goals_per_basket'];native=values[player]['maps'][side] if computed else None
            display=None
            if native is not None:
                mass=publication.native_display_mass(native)
                display=[dict(cell_id=cell['cell_id'],mass=float(value),density_per100sqft=float(100*value/cell['area_sqft']))
                    for cell,value in zip(geometry,mass,strict=True)]
            map_rows.append(dict(season=year,player_id=player,map_kind=kind,strength='5v5',view='effect',result=dict(availability='provided',explanation=None,
                data=dict(grid_id='native656',unit='goals_per_basket',reference='neutral five-player unit; successor goals per 1000 5v5 minutes; inferred territory',
                    cells=None if native is None else [dict(cell_id=i,value=float(value)) for i,value in enumerate(native)],display_cells=display,
                    integrated_value=scalar['value'],unavailable_reason=scalar['unavailable_reason'],reason_detail=scalar['reason_detail'],
                    support=main_support,method_id=method_id))))
    map_rows.sort(key=lambda row:tuple(row[key] for key in publication.KEYS['analysis_map']))
    return scalar_rows,map_rows,reference_id


def _territory_summary(statuses, diagnostics, limits):
    if all(status == 'complete' for status in statuses.values()):
        baseline = 'baseline entry and exit completed'
    else:
        baseline = 'baseline ' + ', '.join(f'{head} {status}' for head, status in statuses.items())
    statements = [baseline]
    if diagnostics == dict(status='unassessed', reason='earlier_annual'):
        statements.append('earlier annual sensitivity unassessed')
    else:
        publication.fields(diagnostics, ('entry', 'exit', 'joint'))
        measures = dict(hazard_per_hour=('hazard', limits['hazard_per_hour']),
                        probability=('probability', limits['probability']),
                        value_goals=('successor value', limits['goals']),
                        map_l1_goals=('map movement', limits['goals']))
        movements = (*measures, 'mean_shift_seconds', 'tail_time_fraction')
        groups = {}
        for variant in ('entry', 'exit', 'joint'):
            row = diagnostics[variant]
            publication.fields(row, ('status', 'reason', *movements))
            if row['status'] == 'unassessed':
                require(row['reason'] == 'baseline_or_diagnostic_incomplete' and all(row[key] is None for key in movements),
                        'invalid unassessed territory sensitivity')
                result = 'were unassessed because a baseline or diagnostic was incomplete'
            else:
                require(row['reason'] is None, 'assessed territory sensitivity has an unavailable reason')
                for key in movements:
                    require_number(row[key], key, low=0)
                exceeded = [label for key, (label, budget) in measures.items() if row[key] > budget]
                within = [label for key, (label, budget) in measures.items() if row[key] <= budget]
                require(row['status'] == ('exceeded' if exceeded else 'within_budget'), 'territory sensitivity verdict differs from bound budget')
                result = 'found that ' + ' and '.join(filter(None, (
                    f'{_prose_list(exceeded)} exceeded budget' if exceeded else None,
                    f'{_prose_list(within)} stayed within budget' if within else None)))
            groups.setdefault(result, []).append(variant)
        statements.extend(f'{_prose_list(variants)} diagnostics {result}'
                          for result, variants in groups.items())
    statements.extend(('terminal zone carry is a proxy', 'optimizer accuracy unknown', 'uncertainty not estimated'))
    return '. '.join(statements) + '.'


def _prose_list(labels):
    return labels[0] if len(labels) == 1 else ', '.join(labels[:-1]) + ' and ' + labels[-1]


def _territory_method(year,state,annuals,selection,reference,reference_id,inherited_methods):
    years=[season for season in annuals if season<=year];manifest=reference['manifest']
    inputs=[dict(role='annual_state',sha256=identity(annuals[season].path/'manifest.json')['sha256'],seasons=[season]) for season in years]
    inputs.extend(dict(role=role,sha256=binding['sha256'],seasons=[year]) for role,binding in
        (('prepared',selection['prepared']),('coaches',selection['coaches']),('source_results',selection['source_results']),
         ('ev_state',manifest['ev_state']),('successor_panel',manifest['panel']),('derivation',identity(reference['path']))) if binding is not None)
    inputs.append(dict(role='territory_reference',sha256=reference_id,seasons=[year]))
    bindings=[identity(state.path/'manifest.json'),selection['prepared'],selection['coaches'],manifest['ev_state'],identity(reference['path'])]
    if manifest['panel'] is not None:bindings.append(manifest['panel'])
    evidence=[dict(uri=binding['path'],sha256=binding['sha256']) for binding in bindings]
    evidence.append(dict(uri='urn:territory-reference:'+reference_id,sha256=reference_id))
    for inherited in inherited_methods:
        for binding in inherited['evidence']:
            if binding not in evidence:evidence.append(binding)
    summary = _territory_summary({name: state.heads[name]['status'] for name in ('entry', 'exit')},
                                 reference['diagnostics'], state.manifest['recipe']['diagnostic_limits'])
    population='genuine 5v5 between-anchor known-path participation; viewing qualification uses its union, role likelihood uses zone-specific seconds'
    return dict(method_id=f'territory-v1-11-{year}',family='territory',purpose=selection['purpose'],recipe_id='territory-v1-11-1',
        design_sha256=hashlib.sha256(publication.json_bytes(state.manifest['design_identity'])).hexdigest(),
        input_sha256=hashlib.sha256(publication.json_bytes(inputs)).hexdigest(),fit_seasons=years,training_cutoff=state.manifest['training_cutoff'],
        target='four inferred conditional movement subskills and successor-start chance-value footprint',population=population,
        reference='five neutral players per side, neutral residual coaches and zero centered context; replace one successor slot; 1000 5v5 minutes',
        limitations=['linear interpolation misses out-and-back movement; block contacts are not release locations; no tracked entries or possession',
            'terminal carry to a supported whistle is a labeled nuisance proxy and can mislocate the puck; transition fitting excludes tails',
            'fixed substitution, ignorable 5v5 censoring, shared neutral survival and one-slot successor approximation are assumptions',
            'positive ice lost is more successor goals against; four movement subskills are not extra ledger terms; no causal isolation',
            'last-supported raw point-history borrowing omits prior uncertainty',summary,
            *dict.fromkeys(limit for inherited in inherited_methods for limit in inherited['limitations'])],
        evidence=evidence,inputs=inputs,reference_id='neutral-unit-territory-successor-v1',support_policy_id='territory-known-path-union-role-risk-v1',
        assessment=dict(status='experimental',findings=[dict(quantities=sorted(field for field in publication.QUANTITY_PATHS if field.startswith('skater_territory.')),
            population=population,summary=summary,evidence=evidence)]))


def _territory_diagnostic_sources(method, year):
    from .territory import HEADS, territory_recipe
    from .territory_design import TERRITORY_RECIPE

    bindings = {}
    documents = {}
    for role, name in (('annual_state', 'manifest.json'), ('derivation', 'reference.json')):
        selected = [item['sha256'] for item in method['inputs'] if item['role'] == role and item['seasons'] == [year]]
        require(len(selected) == 1, f'{year}: expected one territory {role} input')
        evidence = [item for item in method['evidence']
                    if item['sha256'] == selected[0] and Path(item['uri']).is_absolute() and Path(item['uri']).name == name]
        require(len(evidence) == 1, f'{year}: expected one territory {role} evidence binding')
        bindings[role] = dict(path=evidence[0]['uri'], sha256=selected[0])
        documents[role] = strict_json(linked_path(bindings[role]).read_bytes())
    annual, reference = documents['annual_state'], documents['derivation']
    for doc, kind in ((annual, 'territory_state'), (reference, 'territory_successor_reference')):
        require(type(doc) is dict and type(doc.get('schema_version')) is int and doc['schema_version'] == 1
                and doc.get('kind') == kind and doc.get('season') == year and doc.get('purpose') == method['purpose'],
                f'{year}: territory {kind} identity differs')
    require(same_input_reference(reference['annual_state'], bindings['annual_state'])
            and annual['recipe'] == territory_recipe(TERRITORY_RECIPE)
            and method['recipe_id'] == annual['recipe']['id'] and method['training_cutoff'] == annual['training_cutoff']
            and method['design_sha256'] == hashlib.sha256(publication.json_bytes(annual['design_identity'])).hexdigest(),
            f'{year}: territory diagnostic lineage differs')
    publication.fields(annual['heads'], HEADS)
    for head in annual['heads'].values():
        publication.fields(head, ('status', 'path'))
        require(head['status'] in ('complete', 'unavailable', 'failed') and head['path'] == 'heads.json',
                f'{year}: invalid territory baseline head')
    diagnostics = reference['diagnostics']
    earlier = diagnostics == dict(status='unassessed', reason='earlier_annual')
    publication.fields(reference['projections'], ('baseline',) if earlier else ('baseline', *HEADS, 'joint'))
    require(method['purpose'] != 'real' or earlier == (year < publication.SEASONS[-1]),
            f'{year}: territory diagnostic years differ')
    return bindings, {head: annual['heads'][head]['status'] for head in HEADS}, diagnostics, annual['recipe']['diagnostic_limits']


def _unchanged_method_digest(source, changed):
    digest = hashlib.sha256()
    catalog = publication.member_path(source.directory, source.manifest['catalogs']['methods'])
    with catalog.open('rb') as rows:
        for line in rows:
            if strict_json(line)['method_id'] not in changed:
                digest.update(line)
    return digest.hexdigest()


def _territory_correction(source):
    methods = source.catalogs['method']
    corrected = dict(methods)
    changes = []
    for year in source.manifest['seasons']:
        method_id = f'territory-v1-11-{year}'
        method = methods.get(method_id)
        require(method is not None and method['family'] == 'territory' and method['purpose'] == source.manifest['purpose']
                and method['fit_seasons'][-1:] == [year] and len(method['assessment']['findings']) == 1
                and method['assessment']['findings'][0]['quantities'] == sorted(
                    field for field in publication.QUANTITY_PATHS if field.startswith('skater_territory.'))
                and len(method['limitations']) > 5, f'{year}: unexpected territory method')
        bindings, statuses, diagnostics, limits = _territory_diagnostic_sources(method, year)
        summary = _territory_summary(statuses, diagnostics, limits)
        original = method['limitations'][5]
        prefix = 'baseline ' + ','.join(f'{head}:{status}' for head, status in statuses.items()) + '; sensitivity '
        suffix = '; optimizer accuracy unknown; uncertainty not estimated'
        require(original == method['assessment']['findings'][0]['summary'] and len(original) <= 8192
                and original.startswith(prefix) and original.endswith(suffix), f'{year}: territory donor summary differs')
        try:
            literal = literal_eval(original[len(prefix):-len(suffix)])
            matches = type(literal) is dict and publication.json_bytes(literal) == publication.json_bytes(diagnostics)
        except (ValueError, SyntaxError, TypeError, RecursionError) as error:
            raise InputContractError(f'{year}: invalid territory diagnostic literal') from error
        require(matches, f'{year}: territory donor diagnostics differ from bound reference')
        row = deepcopy(method)
        row['limitations'][5] = row['assessment']['findings'][0]['summary'] = summary
        corrected[method_id] = row
        changes.append(dict(method_id=method_id, paths=['/limitations/5', '/assessment/findings/0/summary',
            '/evidence/-', '/assessment/findings/0/evidence/-'], before=original, after=summary, sources=bindings,
            before_sha256=hashlib.sha256(publication.json_bytes(method)).hexdigest(),
            after_without_receipt_sha256=hashlib.sha256(publication.json_bytes(row)).hexdigest()))
    unchanged = dict(catalogs={key: value for key, value in source.manifest['catalogs'].items() if key != 'methods'},
        families=source.manifest['families'],
        nonowned_methods_sha256=_unchanged_method_digest(source, {change['method_id'] for change in changes}))
    receipt = dict(schema_version=1, kind='territory_diagnostic_prose_correction',
                   donor=identity(source.directory/'manifest.json'), changes=changes, unchanged=unchanged)
    return receipt, corrected


def correct_territory_metadata(results, output):
    """prove old bound prose before copying members to one attributed successor."""
    source = publication.read_result_catalogs(results)
    ids = [f'territory-v1-11-{year}' for year in source.manifest['seasons']]
    evidence = []
    for key in ids:
        row = source.catalogs['method'].get(key)
        if row and row['evidence'] and row['evidence'][-1]['uri'].endswith('-territory-correction.json'):
            evidence.append(row['evidence'][-1])
    if evidence:
        require(len(evidence) == len(ids) and all(item == evidence[0] for item in evidence),
                'territory correction is partial or binds different receipts')
        binding = evidence[0]
        receipt = strict_json(linked_path(dict(path=binding['uri'], sha256=binding['sha256'])).read_bytes())
        require(type(receipt) is dict and type(receipt.get('donor')) is dict, 'invalid territory correction receipt')
        donor_manifest = linked_path(receipt['donor'])
        require(donor_manifest.name == 'manifest.json', 'unexpected territory donor manifest name')
        donor = publication.read_result_catalogs(donor_manifest.parent)
    else:
        donor = source
    expected_receipt, methods = _territory_correction(donor)
    if evidence:
        expected_receipt['donor'] = receipt['donor']
        require(publication.json_bytes(receipt) == publication.json_bytes(expected_receipt), 'territory correction receipt differs')
    else:
        output = output_path(str(output), [str(source.directory)])
        if source.manifest['purpose'] == 'real':
            require(output.is_relative_to('/Volumes/Expansion/hockey-stats'), 'real territory outputs must be external')
        receipt_path = output.with_name(output.name + '-territory-correction.json')
        write_json(receipt_path, expected_receipt)
        binding = dict(uri=str(receipt_path), sha256=identity(receipt_path)['sha256'])
    for key in ids:
        methods[key]['evidence'].append(binding)
        methods[key]['assessment']['findings'][0]['evidence'].append(binding)
    if evidence:
        original = donor.manifest
        actual = source.manifest
        require(methods == source.catalogs['method']
                and {key: value for key, value in actual.items() if key not in ('producer', 'catalogs')}
                    == {key: value for key, value in original.items() if key not in ('producer', 'catalogs')}
                and {key: value for key, value in actual['catalogs'].items() if key != 'methods'} == expected_receipt['unchanged']['catalogs']
                and _unchanged_method_digest(source, set(ids)) == expected_receipt['unchanged']['nonowned_methods_sha256'],
                'territory successor differs outside its allowed correction')
        publication.read_results(source.directory)
        return source.directory/'manifest.json'
    publication._write_method_successor(source, methods.values(), output)
    return output/'manifest.json'


def compose_territory(current_results,selection_path,output):
    """fill territory serially, retaining only compact annual history metadata."""
    from .territory_state import (read_territory_selection,read_territory_state,write_territory_reference,read_territory_reference)
    from .spatial_state import read_spatial_start_context
    from .spatial_rates import project_successor_panel
    from .chance_cli import read_json
    began=perf_counter();existing=publication.read_results(Path(current_results))
    selection=read_territory_selection(selection_path,existing.manifest['purpose']);source=identity(existing.directory/'manifest.json')
    require(same_input_reference(selection['source_results'],source) and selection['prepared']['sha256']==existing.manifest['prepared_sha256'],
            'territory current donor/preparation selection differs')
    annuals={};inherited={}
    for item in selection['years']:
        annuals[item['season']]=read_territory_state(item['territory_state']['path'],selection['purpose'],narrow=True)
        ev=read_json(Path(item['ev_state']['path']))
        require(ev['season']==item['season'] and ev['purpose']==selection['purpose'] and ev['prepared']['sha256']==selection['prepared']['sha256'],
                'territory ev annual lineage differs')
        prefix={(year['season'],year['ev_state']['sha256']) for year in selection['years'] if year['season']<=item['season']}
        inherited[item['season']]=[method for method in existing.catalogs['method'].values() if method['family']=='spatial'
            and method['fit_seasons'] and method['fit_seasons'][-1]==item['season'] and prefix <= {
                (value['seasons'][0],value['sha256']) for value in method['inputs']
                if value['role']=='annual_state' and len(value['seasons'])==1}]
        if item['season'] in existing.manifest['seasons']:
            require(inherited[item['season']],'territory selected ev differs from donor accepted spatial lineage')
    require(set(existing.manifest['seasons'])<=set(annuals),'territory selection omits a published annual')
    for record in existing.manifest['families']:
        if record['family']!='territory':continue
        if record['availability']=='provided':
            for table,member in record['tables'].items():
                require(all(row['result']['availability']=='not_computed' for row in existing.rows(member,table,'territory')),
                    'territory donor conflicts with already-computed owned rows')
    output=output_path(str(output),[str(existing.directory),str(Path(selection_path).resolve())])
    if selection['purpose']=='real':require(output.is_relative_to('/Volumes/Expansion/hockey-stats'),'real territory outputs must be external')
    output.mkdir()
    manifest=deepcopy(existing.manifest);manifest['producer']=implementation_identity();methods=dict(existing.catalogs['method'])
    territorial={record['season']:record for record in manifest['families'] if record['family']=='territory'}
    for record in manifest['families']:
        if record['family']=='territory':continue
        for member in record['tables'].values():publication.copy_result_member(existing.directory,member,output)
    key_counts={};reference_bindings={};reference_costs={}
    for item in selection['years']:
        year=item['season'];state=read_territory_state(item['territory_state']['path'],selection['purpose'])
        if item['successor_reference'] is None:
            panel=None;panel_problem=None
            try:
                context=read_spatial_start_context(item['ev_state']['path'],selection['purpose'])
                panel=project_successor_panel(context)
                del context
            except FileNotFoundError as error:
                # absent saved spatial members withhold value, preserving a valid shift process.
                panel_problem=f'saved successor spatial member unavailable: {error}'
            reference=write_territory_reference(output/(year+'-reference'),state,panel,ev_binding=item['ev_state'],panel_problem=panel_problem)
            del panel
        else:reference=read_territory_reference(item['successor_reference']['path'],state,item['ev_state'])
        reference_bindings[year]=identity(reference['path']);reference_costs[year]=reference['manifest']['resources']
        if year in territorial:
            method_id=f'territory-v1-11-{year}'
            people=sorted((person for (season,_),person in existing.people.items() if season==year and person['kind']=='skater'),key=lambda p:p['player_id'])
            scalars,maps,reference_id=_territory_rows(year,state,reference,people,method_id)
            method=_territory_method(year,state,annuals,selection,reference,reference_id,inherited[year])
            require(method_id not in methods,'territory method identity conflicts');methods[method_id]=method
            territorial[year].update(availability='provided',explanation=None,tables={
                'skater_territory':publication.write_result_member(output,year+'-territory.jsonl',scalars,'skater_territory'),
                'analysis_map':publication.write_result_member(output,year+'-territory-maps.jsonl',maps,'analysis_map')})
            key_counts[year]=dict(skater_territory=len(scalars),analysis_map=len(maps))
            del scalars,maps
        del state,reference
    for name in ('people','sources','supports'):publication.copy_result_member(existing.directory,manifest['catalogs'][name],output)
    manifest['catalogs']['methods']=publication.write_result_member(output,'methods.jsonl',sorted(methods.values(),key=lambda row:row['method_id']),'methods')
    write_json(output/'manifest.json.incomplete',manifest);publication.read_results(output,'manifest.json.incomplete')
    (output/'manifest.json.incomplete').rename(output/'manifest.json')
    write_json(output/'territory-composition.json',dict(schema_version=1,kind='territory_composition',purpose=selection['purpose'],source_results=source,
        selection=identity(Path(selection_path).resolve()),output=identity(output/'manifest.json'),key_counts=key_counts,
        annuals=[dict(season=item['season'],territory_state=item['territory_state'],ev_state=item['ev_state'],successor_reference=reference_bindings[item['season']])
            for item in selection['years']],resources=dict(wall_seconds=perf_counter()-began,annual_references=reference_costs),
        preserved='all inherited numerical/factual table members copied byte-for-byte; catalogs retained; no ledger completion'))
    return manifest
