"""compose checked annual execution and saved facts into one complete exchange."""

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
from math import fsum
from pathlib import Path

from . import analysis_publication as publication
from .analysis_data import read_prepared, read_prepared_game
from .artifacts import require
from .captures import strict_json
from .descriptive import estimate, support, valued_evidence, execution_participation, summarize_execution_participation
from .microstats import reduce_reference_xg, summarize_reference_xg

YEARS = ('20212022','20222023','20232024','20242025','20252026')
TYPES = ('wrist','snap','slap','backhand','tip','other')
DANGERS = ('<.05','[.05,.15)','>=.15')
VALUED = ('neutral_all_attempt_value','neutral_locatable_unblocked_value')
POLICY = 'execution-v1-06-matched-reference-v1'
REFERENCE = 'reference-execution-zero'


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _rows(facts, year, family, table):
    record = next(r for r in facts.manifest['families'] if (r['season'],r['family']) == (year,family))
    if table in record['tables']:
        yield from facts.rows(record['tables'][table],table,family)


def _datum(value, method, *, reason='no_exposure', explanation='no paired opportunities', source=None):
    result = estimate(value,reason=reason,explanation=explanation)
    if value is None:
        result['reason_detail']['evidence'] = [dict(kind='method',id=method)] + ([source] if source else [])
    return result


def _setter_evidence(setters, sources, credits):
    """annotate only corroborated recorded goal assists; never alter the prior."""
    rows,universes = [],defaultdict(set)
    for row in setters:
        key = row['game_id'],row['source_index']
        source = sources.get(key)
        if source is None:
            continue
        universes[key].add(row['candidate_id'])
        credit = credits.get(key)
        known = source['outcome'] == 'goal' and credit is not None and credit['status'] == 'credited'
        candidate = ('none' if credit['primary_assister_id'] is None else str(credit['primary_assister_id'])) if known else None
        rows.append(dict(row,recorded_assist_evidence=[source['source']] if candidate == row['candidate_id'] else []))
    discrepancies = []
    for key,candidates in sorted(universes.items()):
        credit = credits.get(key)
        if sources[key]['outcome'] != 'goal' or credit is None or credit['status'] != 'credited':
            continue
        candidate = 'none' if credit['primary_assister_id'] is None else str(credit['primary_assister_id'])
        if candidate not in candidates:
            discrepancies.append(dict(game_id=key[0],source_index=key[1],code='recorded_setter_outside_candidate_universe',
                recorded_primary_assister_id=credit['primary_assister_id'],candidate_ids=sorted(candidates)))
    return rows,discrepancies


def _check_source_score(source, score, attempt):
    """bind completed numerical evidence to the authoritative prepared fields."""
    details = attempt['details']['values']
    require(score['outcome'] == source['outcome'] and (source['shooter_id'] is None or str(score['shooter_id']) == source['shooter_id'])
            and (source['goalie_id'] is None or str(score['goalie_id']) == source['goalie_id']), 'scored/source physical outcome or actor differs')
    require(details['physical_status'] == 'ordinary' and str(details['physical_shooter_id']) == str(score['shooter_id']), 'complete score lacks corroborated prepared physical shooter')
    require(source['team_id'] is None or source['team_id'] == str(details['shooting_team_id']), 'scored/source shooting team differs')
    model_type = attempt['feature_facts']['geometry']['values']['recorded']['values']['model_shot_type']
    require(model_type is not None and model_type == score['shot_type'], 'scored/prepared shot type differs')
    if source['actual_state'] is not None:
        state = source['actual_state']
        require(tuple(score['physical_state']) == (state['attacking_skaters'],state['defending_skaters'],
                int(state['attacking_goalie_present']),int(state['defending_goalie_present'])), 'scored/source physical strength differs')


def _method(year, annual, prepared, facts, source_sha, inputs, family):
    method_id = f'{"execution" if family == "execution" else "reference-xg"}-v1-06-{year}'
    quantities = ([f'skater_execution.{field}' for field in publication.ESTIMATE_FIELDS['skater_execution']]
                  + [f'attempt_value.{field}' for field in publication.ESTIMATE_FIELDS['attempt_value']]) if family == 'execution' else ['skater_microstats.reference_xg_per60']
    evidence = [dict(uri=str(annual.path),sha256=_sha(annual.path)),
                dict(uri=str(facts.directory/'manifest.json'),sha256=source_sha)]
    return dict(method_id=method_id,family=family,recipe_id=annual.manifest['recipe']['name']+':execution-v1-06-1',
        design_sha256=_sha(annual.path),input_sha256=hashlib.sha256(publication.json_bytes(inputs)).hexdigest(),
        fit_seasons=[r['season'] for r in prepared['seasons'] if r['season'] <= year],
        training_cutoff=annual.manifest['training_cutoff'],target='common-panel execution contrasts' if family == 'execution' else 'personal reference-valued observed opportunity per60',
        population='checked regular-season physical opportunities; exact-strength common panels and separately paired source evidence',
        reference='virtual shooter, setter, goalie and coaching with zero residual execution; retain circumstances and inferred setup',
        limitations=['experimental seasonal fits; no scientific admission or calibrated uncertainty',
                    'same-season fitted expectations are not held-out forecasts or causal effects',
                    'blocked origins and setup are inferred; recorded facts remain separate',
                    'qualification uses exact-strength current-season elapsed membership; panel and likelihood denominators differ'],
        evidence=evidence,purpose=facts.manifest['purpose'],inputs=inputs,reference_id=REFERENCE,support_policy_id=POLICY,
        assessment=dict(status='experimental',findings=[dict(quantities=quantities,
            population='annual fitted opportunity panels and paired source attempts',
            summary='experimental point estimates; calibration, recovery and assumption sensitivity are not certified; per-head priors and unavailable coefficients remain explicit',
            evidence=evidence)]))


def _empty_projection(person, strength, qualification, neutral):
    missing = dict(available=False,likelihood_events=None,prior_only=None,prior_seasons=[],reason='focal_projection_unavailable_for_prepared_kind')
    coefficients = dict(shooter={h:dict(missing) for h in ('u','q','r','g')},
                        setter=dict(g=dict(missing,candidate_events=None,mean_coupled_events=None)))
    fields = publication.ESTIMATE_FIELDS['skater_execution']
    metrics = {}
    for field in fields:
        metric = deepcopy(qualification) if qualification is not None else support(None,gap=True,reasons=['elapsed_unavailable'])
        metric.update(events=None,eligible_weight=None,current_season_information=False,prior_only=False,prior_seasons=[])
        metrics[field] = metric
    panel = dict(panel_id=neutral['panel_id'],opportunities=neutral['opportunities'],setup_weight=.8*neutral['opportunities'],
                 neutral=neutral['prefixes'],focal_shooter=dict.fromkeys(('u','uq','uqr','uqrg')),
                 setting_setup=dict(neutral_goal_mass=neutral['setup_goal_mass'],focal_goal_mass=None))
    empty = neutral['opportunities'] == 0
    return dict(season=person['season'],player_id=person['player_id'],strength=strength,values=dict.fromkeys(fields),
                unavailable={field:dict(reason='no_exposure' if empty else 'missing_source',explanation='the exact-state common panel has no supported physical attempts' if empty else 'the factual skater has no saved annual projection because its prepared person kind is not resolved as skater; this does not establish coefficient absence') for field in fields},
                reference_panel=panel,coefficient_support=coefficients,support=metrics)


def _neutral_panel(annual, strength):
    from .execution import ExecutionPanel, neutral_panel_masses
    import numpy as np

    a,d = map(int,strength.split('v'))
    record = next(r for r in annual.manifest['panels'] if r['state'] == dict(attacking_skaters=a,defending_skaters=d,attacking_goalies=1,defending_goalies=1))
    root = annual.path.parent
    with (root/record['events_path']).open('rb') as source:
        events = tuple(strict_json(line) for line in source)
    with np.load(root/record['arrays_path'],allow_pickle=False) as stored:
        arrays = {name:stored[name] for name in stored.files}
    panel = ExecutionPanel(record['panel_id'],annual.manifest['season'],(a,d,1),events,arrays,{}, {})
    return dict(neutral_panel_masses(panel),panel_id=record['panel_id'],opportunities=len(events))


def _season(facts, annual, prepared, year, execution_method, xg_method, output, methods):
    """keep sparse source rows for one season; stream the large fitted maps."""
    people = [p for (season,pid),p in facts.people.items() if season == year and p['kind'] == 'skater']
    people.sort(key=lambda p:p['player_id'])
    by_game = {table:defaultdict(list) for table in ('attempt_fact','dressed_game','interval_fact','interval_player','interval_location')}
    for table,groups in by_game.items():
        for row in _rows(facts,year,'evidence',table):
            groups[row['game_id']].append(row)
    old_coverage = list(_rows(facts,year,'evidence','context_coverage'))
    event_scores = {(r['game_id'],r['source_index']):r for r in annual.events()}
    scores_by_game = defaultdict(list)
    for (gid,index),row in event_scores.items():
        scores_by_game[gid].append(row)
    games = sorted(next(r['selected_game_ids'] for r in prepared['seasons'] if r['season'] == year))
    source_rows = {(r['game_id'],r['source_index']):r for rows in by_game['attempt_fact'].values() for r in rows}
    source_keys = set(source_rows)
    require({key[0] for key in source_keys} <= set(games), 'factual source game absent from selected preparation')
    receipt = dict(season=year,source_results_sha256=_sha(facts.directory/'manifest.json'),scores_sha256=_sha(annual.path),
                   intersection=[list(k) for k in sorted(source_keys & event_scores.keys())],
                   source_only=[list(k) for k in sorted(source_keys - event_scores.keys())],
                   numerical_only=[list(k) for k in sorted(event_scores.keys() - source_keys)])
    valued_facts,valued_locations,micro = [],[],[]
    coverage,game_participation = {},[]
    prepared_attempts,credits = {},{}
    source_gaps = Counter()
    receipt['missing_source_collections'] = []
    receipt['valued_exclusions'] = []
    for gid in games:
        game = read_prepared_game(prepared,year,gid)
        evidence = {table:groups.get(gid,[]) for table,groups in by_game.items()}
        evidence['context_coverage'] = old_coverage
        if game['events'] is None:
            receipt['missing_source_collections'].append(dict(game_id=gid,source='play-by-play'))
            source_gaps.update(r['player_id'] for r in evidence['dressed_game'])
            if not evidence['dressed_game']:
                source_gaps.update(p['player_id'] for p in people)
        scores = scores_by_game[gid]
        valued = valued_evidence(game,evidence,scores,{pop:f'execution-v1-06-{year}-{pop}' for pop in VALUED})
        valued_facts.extend(valued['interval_fact']);valued_locations.extend(valued['interval_location'])
        receipt['valued_exclusions'].extend(dict(row,game_id=gid) for row in valued['dispositions'] if row['reason'] is not None or row.get('personal_reason'))
        micro.append(reduce_reference_xg(valued))
        prepared_attempts.update({(gid,r['source_index']):r for r in game['attempts'] or []})
        credits.update({(gid,r['source_index']):r for r in game['credits'] or []})
        game_participation.append(execution_participation(game))
        for row in valued['context_coverage']:
            key = (row['player_id'],row['population'])
            total = coverage.setdefault(key,dict(row,known_excluded_seconds=0,reason_counts=Counter(),method_ids=[execution_method]))
            total['known_excluded_seconds'] += row['known_excluded_seconds']
            total['unquantified_gap'] |= row['unquantified_gap']
            total['reason_counts'].update({r['code']:r['count'] for r in row['reason_counts']})
    setter_rows,discrepancies = _setter_evidence(annual.setters(),source_rows,credits)
    receipt['setter_discrepancies'] = discrepancies
    participation = summarize_execution_participation(game_participation)
    coverage_rows = []
    for old in old_coverage:
        if old['population'] not in VALUED:
            coverage_rows.append(old)
            continue
        row = coverage.get((old['player_id'],old['population']))
        if row is None:
            row = dict(old,availability='provided',explanation=None,known_excluded_seconds=0,unquantified_gap=True,
                       reason_counts=Counter(source_unavailable=1),method_ids=[execution_method])
        row['reason_counts'] = [dict(code=k,count=v) for k,v in sorted(row['reason_counts'].items())]
        coverage_rows.append(row)
    xg = summarize_reference_xg(people,micro,xg_method)
    values,paired = [],defaultdict(lambda:dict(source=0,events=[],excluded=0))
    receipt['unvalued_source_attempts'] = []
    for gid in sorted(by_game['attempt_fact']):
        for source in by_game['attempt_fact'][gid]:
            key = gid,source['source_index'];score = event_scores.get(key)
            attempt = prepared_attempts.get(key)
            details = attempt['details']['values'] if attempt is not None else {}
            complete = score is not None and score['status'] == 'complete'
            if complete:
                require(attempt is not None, 'completed source key has no prepared attempt')
                _check_source_score(source,score,attempt)
            outside = details.get('physical_status') == 'outside_population'
            reason = 'not_applicable' if outside else 'missing_source'
            explanation = 'source outcome is outside the physical ordinary-attempt population' if outside else (
                '; '.join(r['code'] for r in score['reasons']) if score is not None else 'source key has no numerical event disposition')
            row = dict(season=year,game_id=gid,source_index=source['source_index'],method_id=execution_method,support_id=source['support_id'])
            for field in publication.ESTIMATE_FIELDS['attempt_value']:
                applies = not (source['outcome'] == 'block' and field == 'actor_unblocked_goal_probability'
                    or source['outcome'] in ('block','miss') and field in ('actor_on_net_goal_probability','neutral_goalie_on_net_goal_probability'))
                number = (score['prefixes']['actor' if field.startswith('actor') else 'neutral']['uqrg'] if field.endswith('all_attempt_opportunity')
                          else score['conditional_probabilities'][field]) if complete and applies else None
                row[field] = _datum(number,execution_method,reason='not_applicable' if not applies else reason if not complete else 'no_exposure',
                    explanation='conditional probability is outside its observed stage' if not applies else explanation if not complete else 'zero mathematical conditioning mass',source=source['source'])
            values.append(row)
            if not complete:
                receipt['unvalued_source_attempts'].append(dict(game_id=gid,source_index=source['source_index'],
                    reason=reason,physical_status=details.get('physical_status'),model_reasons=score['reasons'] if score else []))
            state = source['actual_state']
            strength = f"{state['attacking_skaters']}v{state['defending_skaters']}" if state and state['attacking_goalie_present'] and state['defending_goalie_present'] else None
            if source['shooter_id'] is not None and strength in publication.EXECUTION_STRENGTHS:
                personal = paired[source['shooter_id'],strength];personal['source'] += 1
                if complete:
                    danger = score['conditional_probabilities']['neutral_on_net_goal_probability']
                    personal['events'].append(dict(shot_type=score['shot_type'],danger=None if danger is None else DANGERS[0 if danger < .05 else 1 if danger < .15 else 2],
                        blocked=source['outcome']=='block',goal=int(source['outcome']=='goal'),reference=score['prefixes']['neutral']['uqrg'],actor=score['prefixes']['actor']['uqrg']))
                else:
                    personal['excluded'] += 1
    receipt_path = output/f'{year}-execution-composition.json'
    receipt_bytes = publication.json_bytes(receipt)
    receipt_path.write_bytes(receipt_bytes)
    binding = dict(uri=str(receipt_path),sha256=hashlib.sha256(receipt_bytes).hexdigest())
    # write_results serializes catalogs after these family generators finish.
    for method_id in (execution_method,xg_method):
        methods[method_id]['evidence'].append(binding)
    projections = {(r['player_id'],r['strength']):r for r in annual.projections()}
    saved_projections = set(projections)
    missing_panels = {}
    execution_rows,breakdowns = [],[]
    for person in people:
        for strength in publication.EXECUTION_STRENGTHS:
            key = person['player_id'],strength
            projection = projections.get(key)
            if projection is None:
                if strength not in missing_panels:
                    missing_panels[strength] = _neutral_panel(annual,strength)
                projection = _empty_projection(person,strength,participation.get(key),missing_panels[strength])
                projections[key] = projection
            personal = paired[key];events = personal['events']
            missing = [r for r in events if r['danger'] is None]
            payload = {field:_datum(number,execution_method,
                       reason=projection['unavailable'][field]['reason'] if number is None else 'no_exposure',
                       explanation=projection['unavailable'][field]['explanation'] if number is None else 'available',source=person['source'][0])
                       for field,number in projection['values'].items()}
            payload.update(reference_panel=projection['reference_panel'],coefficient_support=projection['coefficient_support'],support=projection['support'],method_id=execution_method,
                paired_evidence=dict(source_attempts=personal['source'],paired_attempts=len(events),unvalued_source_attempts=personal['excluded'],
                    danger_unavailable=dict(events=len(missing),observed_goals=sum(r['goal'] for r in missing),reference_expected_goals=fsum(r['reference'] for r in missing),actor_expected_goals=fsum(r['actor'] for r in missing))))
            execution_rows.append(dict(season=year,player_id=person['player_id'],strength=strength,result=dict(availability='provided',explanation=None,data=payload)))
            for kind,strata in (('shot_type',TYPES),('danger',DANGERS)):
                for stratum in strata:
                    selected = [r for r in events if r[kind] == stratum]
                    count=len(selected);goals=sum(r['goal'] for r in selected)
                    gap = person['player_id'] in source_gaps
                    reasons = ['source_unavailable']*source_gaps[person['player_id']]
                    data = dict(events=count,observed_goals=goals,support=support(None,events=count,gap=gap,reasons=reasons),method_id=execution_method)
                    data['support']['current_season_information'] = bool(personal['source'])
                    data['support']['inferred_inputs'] = (['blocked_origin','setter'] if any(r['blocked'] for r in selected) else ['setter']) if count else []
                    for name in ('reference','actor'):
                        mass=fsum(r[name] for r in selected)
                        data[name]=dict(expected_goals=mass,mean_opportunity=_datum(mass/count if count else None,execution_method,
                            reason='missing_source' if gap and not count else 'no_exposure',
                            explanation='a required source event collection is unavailable' if gap and not count else 'no paired opportunities',source=person['source'][0]),
                                        observed_minus_expected_goals=_datum(goals-mass,execution_method))
                    breakdowns.append(dict(season=year,player_id=person['player_id'],strength=strength,kind=kind,stratum=stratum,
                                           result=dict(availability='provided',explanation=None,data=data)))
    def maps():
        from .observed_spatial import cells
        for person in people:
            for kind,field,unit in (('finishing','finishing_goals_per100_attempts','goals_per100_attempts'),('setting','setting_goals_per100_assisted_opportunities','goals_per100_assisted_opportunities')):
                for strength in sorted(publication.EXECUTION_STRENGTHS):
                    projection=projections[person['player_id'],strength]
                    raw = annual.native_map(person['player_id'],strength,kind) if (person['player_id'],strength) in saved_projections else None
                    native = raw['cells'] if raw else None
                    number = projection['values'][field]
                    reason = _datum(number,execution_method,reason=projection['unavailable'][field]['reason'] if number is None else 'no_exposure',
                                    explanation=projection['unavailable'][field]['explanation'] if number is None else 'available',source=person['source'][0])
                    require((native is None) == (number is None), 'fitted native map availability differs from scalar')
                    display = None
                    if native is not None:
                        mass = publication.native_display_mass(native)
                        display = [dict(cell_id=shape['cell_id'],mass=float(value),density_per100sqft=float(100*value/shape['area_sqft'])) for shape,value in zip(cells(),mass)]
                    data = dict(grid_id='native656',unit=unit,reference=REFERENCE,cells=None if native is None else [dict(cell_id=i,value=v) for i,v in enumerate(native)],
                        display_cells=display,integrated_value=number,unavailable_reason=reason['unavailable_reason'],reason_detail=reason['reason_detail'],support=projection['support'][field],method_id=execution_method)
                    yield dict(season=year,player_id=person['player_id'],map_kind=kind,strength=strength,view='effect',result=dict(availability='provided',explanation=None,data=data))
    tables = dict(skater_execution=sorted(execution_rows,key=lambda r:tuple(r[k] for k in publication.KEYS['skater_execution'])),
                  execution_breakdown=sorted(breakdowns,key=lambda r:tuple(r[k] for k in publication.KEYS['execution_breakdown'])),
                  analysis_map=maps(),attempt_value=values,
                  attempt_setter=setter_rows,
                  attempt_execution_share=(r for r in annual.shares() if (r['game_id'],r['source_index']) in source_keys))
    evidence = {}
    for table in publication.FAMILY_TABLES['evidence']:
        if table == 'context_coverage':
            evidence[table] = sorted(coverage_rows,key=lambda r:tuple(r[k] for k in publication.KEYS[table]))
        elif table in ('interval_fact','interval_location'):
            added = valued_facts if table == 'interval_fact' else valued_locations
            evidence[table] = sorted([r for rs in by_game[table].values() for r in rs]+added,key=lambda r:tuple(r[k] for k in publication.KEYS[table]))
        else:
            evidence[table] = _rows(facts,year,'evidence',table)
    def microstats():
        for row in _rows(facts,year,'microstats','skater_microstats'):
            row=deepcopy(row);row['result']['data']['reference_xg_per60']=xg[row['player_id']]
            yield row
    for original in facts.manifest['families']:
        if original['season'] != year:
            continue
        family = original['family']
        if family in ('execution','evidence','microstats'):
            yield dict(season=year,family=family,availability='provided',explanation=None,
                       tables=tables if family == 'execution' else evidence if family == 'evidence' else dict(skater_microstats=microstats()))
        else:
            yield dict(original,tables={table:_rows(facts,year,family,table) for table in original['tables']})


def compose_results(prepared, factual_results, scores_selection, output):
    """bind one preparation, factual exchange and ordered annual score chain."""
    from .execution_scores import read_execution_scores
    from .chance_cli import output_path

    facts = publication.read_results(Path(factual_results))
    purpose = facts.manifest['purpose']
    prepared = read_prepared(prepared,purpose)
    prepared_sha = _sha(prepared.directory/'manifest.json')
    require(facts.manifest['prepared_sha256'] == prepared_sha, 'factual/prepared binding differs')
    prepared_selection = strict_json((prepared.directory/'selection.json').read_bytes())
    corpus_hashes = {r['season']:r['sha256'] for r in prepared_selection['seasons']}
    require(all(corpus_hashes.get(r['season']) == r['corpus_sha256'] for r in facts.manifest['observed_bindings']),
            'factual/prepared observed corpus binding differs')
    selection = strict_json(Path(scores_selection).read_bytes())
    publication.fields(selection,('schema_version','purpose','prepared_sha256','scores'))
    require(type(selection['schema_version']) is int and selection['schema_version'] == 1 and selection['purpose'] == purpose
            and selection['prepared_sha256'] == prepared_sha, 'score selection purpose/preparation differs')
    require(type(selection['scores']) is list and selection['scores'], 'missing annual scores')
    years=[];annuals={}
    for item in selection['scores']:
        publication.fields(item,('season','path','sha256'));publication.digest(item['sha256'])
        require(item['season'] in YEARS and type(item['path']) is str and Path(item['path']).is_absolute(), 'invalid annual score selection')
        path=Path(item['path']);path=path/'manifest.json' if path.is_dir() else path
        require(_sha(path) == item['sha256'], 'annual score manifest digest differs')
        annual=read_execution_scores(path,purpose);year=item['season']
        require(annual.manifest['season'] == year and annual.manifest['prepared']['sha256'] == prepared_sha, 'annual season/preparation binding differs')
        require(annual.manifest['prepared']['members'] == [r for r in prepared['files'] if r['season'] == year and r['kind'] in ('game','people')], 'annual selected preparation members differ')
        years.append(year);annuals[year]=annual
    require(years == sorted(set(years)) and years == list(YEARS[YEARS.index(years[0]):YEARS.index(years[-1])+1]), 'annual scores must be unique ordered consecutive years')
    require(purpose != 'real' or years == list(YEARS), 'real composition requires all five annual scores')
    require(set(facts.manifest['seasons']) <= set(years), 'score selection omits a displayed season')
    for previous,current in zip(years,years[1:]):
        left,right=annuals[previous].manifest,annuals[current].manifest
        require(right['state']['previous'] == {k:left['state'][k] for k in ('path','sha256')}, 'annual state history chain differs')
        require(right['recipe'] == left['recipe'] and right['scoring_version'] == left['scoring_version']
                and all(right['coaches'][k] == left['coaches'][k] for k in ('path','sha256')), 'annual recipe/scoring/coaches bindings differ')
    output=output_path(str(output),[str(prepared.directory),str(facts.directory),*[str(a.path.parent) for a in annuals.values()]])
    source_sha=_sha(facts.directory/'manifest.json')
    catalogs=dict(people=list(facts.people.values()),sources=list(facts.catalogs['source'].values()),
                  methods=[r for r in facts.catalogs['method'].values() if r['method_id'] not in {f'factual-pending-reference-{y}-opportunity' for y in facts.manifest['seasons']}],
                  supports=list(facts.catalogs['support'].values()))
    method_ids,method_records={},{}
    for year in facts.manifest['seasons']:
        annual=annuals[year]
        panels=[r for r in annual.manifest['files'] if r['role'] in ('panel_arrays','panel_events')]
        history=[r['season'] for r in prepared['seasons'] if r['season'] <= year]
        inputs=[dict(role='prepared',sha256=prepared_sha,seasons=history),
                dict(role='coaches',sha256=annual.manifest['coaches']['sha256'],seasons=history),
                dict(role='opportunity_panel',sha256=hashlib.sha256(publication.json_bytes(panels)).hexdigest(),seasons=[year]),
                dict(role='source_results',sha256=source_sha,seasons=[year]),
                *[dict(role='annual_state',sha256=annuals[y].manifest['state']['sha256'],seasons=[y]) for y in years if y <= year]]
        method_ids[year]={}
        for family in ('execution','microstats'):
            method=_method(year,annual,prepared,facts,source_sha,inputs,family)
            method_ids[year][family]=method['method_id']
            existing=next((r for r in catalogs['methods'] if r['method_id']==method['method_id']),None)
            require(existing is None or existing == method, 'conflicting execution method identity')
            if existing is None:catalogs['methods'].append(method)
            method_records[method['method_id']] = existing if existing is not None else method
        for pop in VALUED:
            ids=sorted({s for r in _rows(facts,year,'evidence','context_coverage') if r['population']=='recorded_all_attempts' for s in r['source_ids']})
            support_row=dict(support_id=f'execution-v1-06-{year}-{pop}',season=year,population_id=pop,policy_id=POLICY,
                definition='recorded starting intervals intersect checked neutral opportunities and physical shooter membership; interval-local failures remove paired masses and time; locatable population excludes blocks and uses recorded display cells',
                source_ids=ids,method_ids=[method_ids[year]['execution']])
            existing=next((r for r in catalogs['supports'] if r['support_id']==support_row['support_id']),None)
            require(existing is None or existing == support_row, 'conflicting valued support identity')
            if existing is None:catalogs['supports'].append(support_row)
    def families():
        for year in facts.manifest['seasons']:
            yield from _season(facts,annuals[year],prepared,year,method_ids[year]['execution'],method_ids[year]['microstats'],output,method_records)
    for table in catalogs:
        catalogs[table].sort(key=lambda row:tuple(row[k] for k in publication.KEYS[table]))
    return publication.write_results({k:facts.manifest[k] for k in ('purpose','seasons','observed_bindings','prepared_sha256')},catalogs,families(),output)
