"""publish saved penalty and shooter-choice projections through the current exchange."""

from copy import deepcopy
import hashlib
from pathlib import Path
from time import perf_counter

from . import analysis_publication as publication
from .artifacts import implementation_identity, require, write_json
from .captures import strict_json
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
    require(selection['source_results'] == source_binding, 'selected current-schema mechanism donor differs')
    require(selection['prepared']['sha256'] == existing.manifest['prepared_sha256'], 'mechanism donor preparation differs')
    conversion_path = existing.directory/'exchange4-conversion.json'
    descendant_binding = None
    converted_binding = source_binding
    if not conversion_path.exists():
        descendant_path = existing.directory/'goalie-composition.json'
        descendant = strict_json(descendant_path.read_bytes())
        publication.fields(descendant,('schema_version','kind','source_results','selection','output','inherited_members','goalie_members',
                                      'source_families','output_families','preserved','resources'))
        require(descendant['schema_version'] == 1 and descendant['kind'] == 'goalie-composition'
                and descendant['output'] == source_binding and descendant['output_families'] == existing.manifest['families'],
                'selected current-schema goalie descendant receipt differs')
        converted_binding = descendant['source_results']
        require(identity(Path(converted_binding['path'])) == converted_binding, 'selected goalie descendant parent differs')
        converted = strict_json(Path(converted_binding['path']).read_bytes())
        require(converted['schema_version'] == 4 and converted['purpose'] == selection['purpose'], 'goalie parent is not current exchange')
        require(all(existing.manifest[key] == converted[key] for key in ('purpose','seasons','observed_bindings','prepared_sha256')),
                'goalie descendant changed the inherited population')
        inherited = {(record['season'],record['family']):record for record in converted['families'] if record['family'] != 'goalie'}
        require(all(inherited[record['season'],record['family']] == record for record in existing.manifest['families'] if record['family'] != 'goalie'),
                'goalie descendant changed an unrelated family')
        require(existing.manifest['catalogs']['people'] == converted['catalogs']['people'], 'goalie descendant changed person identities')
        for name,key,catalog in (('sources','source_id','source'),('methods','method_id','method'),('supports','support_id','support')):
            member = converted['catalogs'][name]
            path = publication.member_path(Path(converted_binding['path']).parent,member)
            require(identity(path)['sha256'] == member['sha256'], 'goalie parent catalog digest differs')
            with path.open('rb') as stream:
                for line in stream:
                    original = strict_json(line)
                    require(existing.catalogs[catalog].get(original[key]) == original, 'goalie descendant changed inherited catalog evidence')
        conversion_path = Path(converted_binding['path']).parent/'exchange4-conversion.json'
        descendant_binding = identity(descendant_path)
    conversion = strict_json(conversion_path.read_bytes())
    publication.fields(conversion,('schema_version','kind','purpose','source_results','output','policy','synthetic_checked_facts','inherited_members'))
    require(conversion['schema_version'] == 1 and conversion['kind'] == 'attributed_exchange4_conversion'
            and conversion['purpose'] == selection['purpose'], 'invalid exchange4 donor conversion receipt')
    if selection['purpose'] == 'real':
        require(conversion['source_results']['sha256'] == '21de98fb8538632296a00e0650c9005f4a267b6a75bd6e09d541864f6f3836c3',
                'exchange4 donor is not the pinned complete g/ev/st successor')
    require(identity(Path(conversion['source_results']['path'])) == conversion['source_results'], 'original exchange3 donor binding differs')
    require(conversion['output'] == converted_binding, 'exchange4 donor conversion does not bind the selected current donor')
    conversion_binding = identity(conversion_path)
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
            manifest = strict_json(Path(item[name]['path']).read_bytes())
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
        table = 'skater_penalties' if family == 'penalties' else 'skater_shootiness'
        if record['availability'] == 'provided':
            require(all(row['result']['availability'] == 'not_computed' for row in existing.rows(record['tables'][table],table,family)),
                    'conflicting computed mechanism rows in donor')
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
        source_results=source_binding,source_conversion=conversion_binding,source_descendant=descendant_binding,selection=identity(Path(selection_path).resolve()),output=identity(output/'manifest.json'),
        minor_references=minor_references,minor_reference_bindings=minor_bindings,diagnostics=diagnostics,resources=dict(wall_seconds=perf_counter()-began,
            output_member_bytes=sum((output/member['path']).stat().st_size for member in [*manifest['catalogs'].values(),
                *(member for record in manifest['families'] for member in record['tables'].values())])),
        preserved='all unrelated table members copied byte-for-byte; catalog records preserved; no ledger or territory estimate completed'))
    return manifest
