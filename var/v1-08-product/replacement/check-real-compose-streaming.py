"""tiny synthetic indexing/merge/copy controls; the held real main stays unrun."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from time import perf_counter

WORK = Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
HELPER = WORK / 'var/v1-08-product/replacement/verify-real-execution-compose.py'


def main():
    began = perf_counter()
    ast.parse(HELPER.read_text())
    spec = importlib.util.spec_from_file_location('held_compose', HELPER)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    scratch = Path(tempfile.mkdtemp(prefix='compose-controls-', dir=HELPER.parent))
    h.CAMPAIGN, h.OUTPUT = scratch, scratch / 'output'
    year = '20242025'
    source = dict(kind='source', id='synthetic-source')
    method = 'execution-v1-06-'+year

    def member(root, name, records):
        root.mkdir(parents=True, exist_ok=True)
        payload = b''.join((json.dumps(row, separators=(',', ':'))+'\n').encode() for row in records)
        (root / name).write_bytes(payload)
        return dict(path=name, rows=len(records), sha256=hashlib.sha256(payload).hexdigest())

    def datum(value, reason='missing_source', explanation='synthetic missing'):
        return dict(value=value, unavailable_reason=reason if value is None else None,
            reason_detail=dict(explanation=explanation, evidence=[dict(kind='method', id=method), source]) if value is None else None,
            uncertainty=dict(kind='not_estimated'))

    raw_projections, raw_maps, public_projections, public_maps = [], [], [], []
    people = {(year, player): dict(source=[source]) for player in ('1', '2', '3')}
    for strength in ('5v5', '5v4'):
        for player in ('1', '2', '4'):  #4 is numerical-only;3 is factual-only.
            values = {field: float(player)/10 for field in h.FIELDS}
            values[h.FIELDS[1]] = None if player == '1' else values[h.FIELDS[1]]
            support = {field: dict(current_season_information=True, prior_only=False, prior_seasons=[], marker=player) for field in h.FIELDS}
            raw = dict(season=year, player_id=player, strength=strength, values=values,
                unavailable={field: dict(reason='no_exposure', explanation='synthetic missing') for field, value in values.items() if value is None},
                support=support, coefficient_support={}, reference_panel=dict(panel_id=strength, opportunities=2))
            raw_projections.append(raw)
            data = dict({field: datum(value, 'no_exposure') for field, value in values.items()},
                support=support, coefficient_support={}, reference_panel=raw['reference_panel'], method_id=method)
            if player != '4':
                public_projections.append(dict(season=year, player_id=player, strength=strength, result=dict(availability='provided', explanation=None, data=data)))
            for kind, field, unit in (('finishing', h.FIELDS[0], 'goals_per100_attempts'), ('setting', h.FIELDS[1], 'goals_per100_assisted_opportunities')):
                value = values[field]
                native = None if value is None else [value]+[0.]*655
                raw_maps.append(dict(season=year, player_id=player, strength=strength, map_kind=kind, panel_id=strength, cells=native, integrated_value=value))
                if player != '4':
                    public_maps.append(dict(season=year, player_id=player, strength=strength, map_kind=kind, view='effect',
                        result=dict(availability='provided', explanation=None, data=dict(grid_id='native656', unit=unit,
                            reference='reference-execution-zero', method_id=method, support=support[field], integrated_value=value,
                            cells=None if native is None else [dict(cell_id=i, value=v) for i, v in enumerate(native)],
                            display_cells=None if native is None else [dict(cell_id=i, mass=0., density_per100sqft=0.) for i in range(668)],
                            unavailable_reason=data[field]['unavailable_reason'], reason_detail=data[field]['reason_detail']))))
    for strength in ('5v5', '5v4'):
        data = {field: datum(None, 'missing_source', 'the factual skater has no saved annual projection because its prepared person kind is not resolved as skater; this does not establish coefficient absence') for field in h.FIELDS}
        data.update(method_id=method, reference_panel=dict(opportunities=2), coefficient_support=dict(shooter=dict(u=dict(available=False, reason='focal_projection_unavailable_for_prepared_kind'))),
            support={field: dict(current_season_information=False, prior_only=False, prior_seasons=[]) for field in h.FIELDS})
        public_projections.append(dict(season=year, player_id='3', strength=strength, result=dict(availability='provided', explanation=None, data=data)))
        for kind, field, unit in (('finishing', h.FIELDS[0], 'goals_per100_attempts'), ('setting', h.FIELDS[1], 'goals_per100_assisted_opportunities')):
            public_maps.append(dict(season=year, player_id='3', strength=strength, map_kind=kind, view='effect', result=dict(availability='provided', explanation=None,
                data=dict(grid_id='native656', unit=unit, reference='reference-execution-zero', method_id=method, support=data['support'][field],
                          integrated_value=None, cells=None, display_cells=None, unavailable_reason='missing_source', reason_detail=data[field]['reason_detail']))))
    public_projections.sort(key=lambda row: (row['player_id'], row['strength']))
    public_maps.sort(key=lambda row: (row['player_id'], row['map_kind'], row['strength']))
    score_root = scratch / 'scores' / year
    annual = dict(files=[member(score_root, 'projections.jsonl', raw_projections), member(score_root, 'maps.jsonl', raw_maps)], resources=dict(projections=6))
    tables = dict(skater_execution=member(h.OUTPUT, 'projections.jsonl', public_projections), analysis_map=member(h.OUTPUT, 'maps.jsonl', public_maps))
    manifest = dict(families=[dict(season=year, family='execution', tables=tables)])
    copied = h.check_projections_maps(year, manifest, annual, people)
    assert copied['copied_projections_exact'] == 4 and copied['factual_only_unavailable_projections'] == 2
    assert copied['copied_native_maps_exact'] == 8 and copied['raw_only_map_rows'] == 4 and copied['raw_only_projection_rows'] == 2
    old = [dict(season=year, game_id='g1', interval_id=1, team_id='t', population='recorded', seconds=10)]
    added = dict(old[0], population='neutral_all_attempt_value')
    after = sorted([old[0], added], key=lambda row: tuple(row[key] for key in h.KEYS['interval_fact']))
    assert h.compare_intervals(old, after, 'interval_fact') == dict(original_rows_exact=1, added_valued_rows=1)
    facts = [dict(season=year, game_id='g1', source_index=i, outcome=outcome, source=source, support_id='s') for i, outcome in ((1, 'goal'), (2, 'block'), (3, 'miss'))]
    scores = [dict(season=year, game_id='g1', source_index=i, status='complete', prefixes=dict(actor=dict(uqrg=.1), neutral=dict(uqrg=.05)),
        conditional_probabilities=dict(actor_unblocked_goal_probability=.2, actor_on_net_goal_probability=.3, neutral_goalie_on_net_goal_probability=.4)) for i in (1, 2)]
    scores.append(dict(season=year, game_id='g2', source_index=1, status='excluded'))
    values = []
    for fact in facts:
        value = {key: fact[key] for key in ('season', 'game_id', 'source_index', 'support_id')}
        value['method_id'] = method
        for field in ('actor_all_attempt_opportunity', 'neutral_all_attempt_opportunity', 'actor_unblocked_goal_probability', 'actor_on_net_goal_probability', 'neutral_goalie_on_net_goal_probability'):
            applies = not (fact['outcome'] == 'block' and field == 'actor_unblocked_goal_probability'
                or fact['outcome'] in ('block', 'miss') and field in ('actor_on_net_goal_probability', 'neutral_goalie_on_net_goal_probability'))
            number = (.1 if field.startswith('actor') else .05) if field.endswith('all_attempt_opportunity') else {'actor_unblocked_goal_probability': .2, 'actor_on_net_goal_probability': .3, 'neutral_goalie_on_net_goal_probability': .4}[field]
            value[field] = datum(number if applies and fact['source_index'] != 3 else None, 'not_applicable' if not applies else 'missing_source',
                'conditional probability is outside its observed stage' if not applies else 'source key has no numerical event disposition')
        values.append(value)
    raw_setters = [dict(season=year, game_id='g1', source_index=1, candidate_id='none', pre_outcome_weight=1., posterior_weight=1., recorded_assist_evidence=[])]
    shares = [dict(season=year, game_id='g1', source_index=1, group='shooter', recipient_id='1', goals=.05)]
    annual['files'] += [member(score_root, 'events.jsonl', scores), member(score_root, 'setters.jsonl', raw_setters), member(score_root, 'shares.jsonl', shares)]
    tables.update(attempt_value=member(h.OUTPUT, 'values.jsonl', values), attempt_setter=member(h.OUTPUT, 'setters.jsonl', raw_setters), attempt_execution_share=member(h.OUTPUT, 'shares.jsonl', shares))
    manifest['families'].append(dict(season=year, family='evidence', tables=dict(attempt_fact=member(h.OUTPUT, 'facts.jsonl', facts))))
    receipt = dict(intersection=[['g1', 1], ['g1', 2]], source_only=[['g1', 3]], numerical_only=[['g2', 1]],
        unvalued_source_attempts=[dict(game_id='g1', source_index=3, model_reasons=[], physical_status='ordinary', reason='missing_source')])
    bridge = h.check_event_bridges(year, manifest, annual, receipt)
    assert bridge['intersection'] == 2 and bridge['source_only'] == bridge['numerical_only'] == 1
    refused = []
    for name in ('map_wrong_key', 'map_nullability', 'interval_changed', 'source_value_wrong_key'):
        try:
            if name.startswith('map_'):
                row = deepcopy(public_maps[0]); raw = deepcopy(next(row for row in raw_maps if (row['player_id'], row['strength'], row['map_kind']) == ('1', '5v4', 'finishing')))
                if name == 'map_wrong_key':
                    raw['player_id'] = '2'
                else:
                    row['result']['data']['cells'] = None
                data = next(row['result']['data'] for row in public_projections if (row['player_id'], row['strength']) == ('1', '5v4'))
                h.check_copied_map(row, raw, data, method)
            elif name == 'interval_changed':
                h.compare_intervals(old, [dict(old[0], seconds=11)], 'interval_fact')
            else:
                changed = deepcopy(values); changed[0]['source_index'] = 99
                tables['attempt_value'] = member(h.OUTPUT, 'values.jsonl', changed)
                h.check_event_bridges(year, manifest, annual, receipt)
        except AssertionError:
            refused.append(name)
        else:
            raise AssertionError('corruption accepted: '+name)
    result = dict(kind='held-real-compose-stream-controls', status='passed', recorded_at_utc=datetime.now(timezone.utc).isoformat(),
        checker=h.identity(HELPER), controls=h.identity(Path(__file__).resolve()), scratch=str(scratch),
        copied=copied, event_merge=bridge, wrong_records_refused=refused,
        scope='tiny synthetic rows only; map display cells are scaffolding and their geometry math is outside these copy controls',
        main_invocations=0, real_or_fixture_artifact_reads=0, strict_reads=0, source_passes=0, array_reads=0, wall_seconds=perf_counter()-began)
    destination = HELPER.parent / 'real-compose-streaming-controls-02.json'
    with destination.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
