"""04m's fixed recorded-game attribution comparison."""

import argparse
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import sys
import time

for _thread in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[_thread] = '1'

import numpy as np

from hockey_stats.artifacts import (
    artifact, clean_implementation, json_values, linked_path, load_arrays,
    ordered_array_digest, require, resources, write_arrays, write_json,
)
from hockey_stats.attribution import (
    ShapeBasis, ShapeCoefficientLikelihood, ShapeCoefficientState, bounded_shape_coefficient_probe,
    decode_shape_basis, fit_shape_coefficients, validate_shape_coefficient_state,
)
from hockey_stats.attribution_data import EmpiricalTraining, empirical_training, read_empirical_fixture, read_empirical_source
from hockey_stats.attribution_prediction import empirical_prediction
from hockey_stats.attribution_simulation import shape_regions
from hockey_stats.captures import InputContractError
from hockey_stats.chance_cli import identity, read_json
from hockey_stats.shot_origins import grid


SPEC = Path(__file__).resolve().parents[2] / 'docs/specs/04m-attribution-empirical.md'
RESEARCH_ROOT = Path('/Volumes/Expansion/hockey-stats/runs')
BASIS_REF = dict(path='/Volumes/Expansion/hockey-stats/runs/attribution-04c-20261016/prepared/basis.npz',
    sha256='67d7ee706f1d8d251cc68a0d22378e67e1961b2ac53fb764bfc0efdff11d43fc')
CORPUS_REF = dict(path='/Volumes/Expansion/hockey-stats/corpora/03m-20261010/20252026/corpus.json',
    sha256='8229fc6686fa03c4f6cc00d68d68aac1d1d2b83d6950d56eeebb7c9fc923fd43')
RULES = dict(split_namespace='hockey-stats:04m:split:v1:',
    split='within each calendar month sort by (sha256(namespace + game_id), game_id); first floor(n/5) assess',
    arms=['borrowing', 'independent', 'context'], scale_grid=np.arange(-8., .1, .5).tolist(),
    refinement=dict(xatol=1e-4, maxiter=40), probes=dict(xatol=1e-6, maxiter=80,
        equation_residual_max=1e-8, current_map_movement_fraction=1e-4),
    seed=404130, draws=2000, bit_generator='PCG64', schemes=['games', 'calendar_7_day', 'calendar_14_day'],
    intervals='two-sided 95% percentile; linear quantiles; fixed split and fits',
    score='zero-sum recorded shape; signed paired differences, never absolute mse',
    formulas=dict(training='r=sum(N)/sum(E); xbar=C/E; nbar=N/E; H=r*(A-C.T@xbar); T=K-C.T@nbar; Q=(T-(T@1)*p.T)@B',
        prediction='M=r*uncentered_Theta@R.T; F=nbar-(nbar@1)*p.T-xbar@M; Z@F+X@M',
        target='h=n/e-(sum(n)/e)*p; e=seconds/3600',
        paired='D_ab=inner((L_a-L_b)W,G((L_a+L_b)W))-2*inner(SW,(L_a-L_b)W)',
        native='replace W@W.T by diag(1/p); denominator=directed_hours'),
    training='selected raw game moments; training rate, player exposure and contexts; first-season p and B',
    prediction='raw physical player maps plus independently compensated training contexts',
    metric='twelve physical regions; numerator / (12 * directed_hours)',
    direction='all three valid intervals strictly on one side of zero, otherwise unresolved',
    scientific_gate=None, nomination=None, admission='not_admitted', handoff=None)
TRAINING_ARRAYS = ('H', 'Q', 'u', 'xbar', 'nbar', 'player_exposure', 'response_counts')
STATE_ARRAYS = ('Theta', 'V', 'uncentered_Theta', 'centering_shift', 'u')
LIMITS = [
    'joint lineup prediction of recorded locatable unblocked shape, not individual ability or chance value',
    'one fixed calendar-spanning split of research-exposed seasons; not untouched confirmation or a pregame forecast',
    'intervals condition on fitting, scale selection, split and included population; no player uncertainty claim',
    'paired moments cancel response self energy; absolute errors, complete rates and entrant squared errors are unavailable',
    'limited home/period/score context, forty-mode geometry and relative-rate annual carry remain assumptions',
    'recording and reconstructed membership/exposure gaps can be selective; shared source defects need not cancel',
    'prediction does not resolve synthetic recovery failures or identify the prior as their sole cause',
    'support-group residual associations overlap on ice and are not individual accuracy or independent samples',
]


@dataclass(frozen=True)
class Prepared:
    reference: dict
    document: dict
    trainings: tuple[EmpiricalTraining, ...]
    basis: ShapeBasis


def _ref(path):
    return identity(Path(path).absolute())


def _cost(started, process_started, root):
    return dict(**resources(started), process_seconds=time.process_time()-process_started,
        output_bytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),
        output_bytes_scope='tree before current manifest serialization')


def _output(path, purpose):
    root = Path(path).absolute()
    if purpose == 'research':
        require(RESEARCH_ROOT.is_dir() and root.is_relative_to(RESEARCH_ROOT),
            'research outputs require the mounted external research root')
    require(not root.exists(), 'output directory already exists')
    root.mkdir(parents=True)
    return root


def calendar_split(game_ids, dates):
    """freeze whole inventory games before reading their held-out responses."""
    require(tuple(game_ids) == tuple(sorted(set(game_ids))) and set(game_ids) == set(dates),
        'split requires exact sorted inventory ids and dates')
    months = defaultdict(list)
    for game in game_ids:
        months[dates[game][:7]].append(game)
    assessment, rows = set(), []
    for month, games in sorted(months.items()):
        ordered = sorted(games, key=lambda game: (
            hashlib.sha256((RULES['split_namespace']+str(game)).encode('utf-8')).digest(), game))
        selected = ordered[:len(games)//5]
        assessment.update(selected)
        rows.append(dict(month=month, inventory_games=len(games), assessment_games=len(selected)))
    train = tuple(game for game in game_ids if game not in assessment)
    heldout = tuple(game for game in game_ids if game in assessment)
    require(bool(train) and bool(heldout), 'fixed partition has no training or assessment games')
    return train, heldout, rows


def prepare(source_result, fixture, output):
    started, process_started = time.monotonic(), time.process_time()
    purpose = 'fixture_exercise' if fixture else 'research'
    source = (read_empirical_fixture(Path(fixture)) if fixture else
        read_empirical_source(_ref(source_result), BASIS_REF, CORPUS_REF))
    final = source.grouped[-1]
    # the calendar partition is fixed before any selected assessment contraction.
    train, heldout, months = calendar_split(final.game_ids, source.game_dates)
    trainings = tuple(empirical_training(grouped, references,
        train if i == len(source.seasons)-1 else grouped.game_ids, source.basis)
        for i, (grouped, references) in enumerate(zip(source.grouped, source.references, strict=True)))
    heldout_rows = [final.game_ids.index(game) for game in heldout]
    require(float(final.stratum_e[heldout_rows].sum()) > 0, 'fixed assessment partition has zero retained exposure')
    empirical_prediction(trainings[-1], None, source.references[-1].player_ids)
    supported = set(trainings[-1].strata)
    for context, hours in zip(source.references[-1].strata, final.stratum_e[heldout_rows].sum(axis=0), strict=True):
        require(hours == 0 or context in supported, 'assessment context absent from training in fixed partition')
    arrays = dict(B=source.basis.B, p=source.basis.p, eigenvalues=source.basis.eigenvalues)
    years = []
    for i, (training, original) in enumerate(zip(trainings, source.annual, strict=True)):
        prefix = f'year_{i}'
        values = dict(H=training.likelihood.H, Q=training.likelihood.Q, u=training.likelihood.u,
            xbar=training.xbar, nbar=training.nbar, player_exposure=training.player_exposure,
            response_counts=training.response_counts)
        arrays.update({prefix+'_'+name: value for name, value in values.items()})
        years.append(dict(season=training.likelihood.season, prefix=prefix,
            game_ids=training.game_ids, source_player_ids=training.source_player_ids,
            player_ids=training.likelihood.player_ids, strata=training.strata, source_strata=training.source_strata,
            r=training.likelihood.r, directed_hours=training.directed_hours,
            source_identity=training.source_identity, source_annual=original))
    coverage = dict(inventory_games=len(final.game_ids), training_games=len(train), assessment_games=len(heldout),
        assessment_fraction=len(heldout)/len(final.game_ids),
        training_directed_hours=trainings[-1].directed_hours,
        assessment_directed_hours=float(final.stratum_e[heldout_rows].sum()),
        zero_time_game_ids=[game for game, hours in zip(final.game_ids, final.stratum_e.sum(axis=1), strict=True) if hours == 0],
        source_annual=source.annual[-1]['coverage'])
    root = _output(output, purpose)
    snapshot = root/'spec.md'
    snapshot.write_bytes(SPEC.read_bytes())
    data = write_arrays(root, 'training.npz', arrays)
    fields = dict(sources=source.source_identity, seasons=source.seasons, years=years,
        basis_sha256=source.basis.sha256, training_sha256=ordered_array_digest(arrays),
        inventory=[dict(game_id=game, date=source.game_dates[game], partition='assessment' if game in heldout else 'training')
            for game in final.game_ids],
        train_ids=train, assessment_ids=heldout, months=months, coverage=coverage,
        expected_states=len(trainings)+1, expected_probes=len(trainings)+1, **data)
    protocol = artifact('attribution_empirical_protocol', purpose, dict(spec_snapshot=_ref(snapshot)),
        schema_version=1, rules=RULES, **fields, resources=_cost(started, process_started, root))
    write_json(root/'protocol.json', json_values(protocol))
    prepared = artifact('attribution_empirical_prepared', purpose, dict(protocol=_ref(root/'protocol.json'), training=data['arrays']),
        schema_version=1, protocol=_ref(root/'protocol.json'), **fields, resources=_cost(started, process_started, root))
    write_json(root/'prepared.json', json_values(prepared))
    return _ref(root/'prepared.json')


def read_prepared(path):
    reference = _ref(path)
    # the command argument was just hashed; named dependencies are checked once below.
    document = read_json(Path(path))
    require(document['kind'] == 'attribution_empirical_prepared' and document['schema_version'] == 1
        and document['purpose'] in ('research', 'fixture_exercise'),
        'wrong empirical preparation')
    if document['purpose'] == 'research':
        clean_implementation(document['implementation'])
    protocol = read_json(linked_path(document['protocol']))
    require(protocol['kind'] == 'attribution_empirical_protocol' and protocol['schema_version'] == 1,
        'wrong empirical protocol')
    if protocol['purpose'] == 'research':
        clean_implementation(protocol['implementation'])
    fields = ('sources', 'seasons', 'years', 'basis_sha256', 'training_sha256', 'inventory',
        'train_ids', 'assessment_ids', 'months', 'coverage', 'expected_states', 'expected_probes', 'arrays', 'array_shapes')
    require(protocol['rules'] == RULES and document['purpose'] == protocol['purpose']
        and all(document[name] == protocol[name] for name in fields), 'prepared protocol bindings differ')
    linked_path(protocol['consumed']['spec_snapshot'])
    arrays = load_arrays(document)
    require(ordered_array_digest(arrays) == document['training_sha256'], 'saved training statistics differ')
    basis = decode_shape_basis({name: arrays[name] for name in ('B', 'p', 'eigenvalues')},
        basis_sha256=document['basis_sha256'])
    trainings = []
    for row in document['years']:
        values = {name: arrays[row['prefix']+'_'+name] for name in TRAINING_ARRAYS}
        likelihood = ShapeCoefficientLikelihood(row['season'], tuple(row['player_ids']),
            values['H'], values['Q'], values['u'], row['r'], basis, row['source_identity'])
        trainings.append(EmpiricalTraining(likelihood, tuple(row['game_ids']), tuple(row['source_player_ids']),
            tuple(map(tuple, row['strata'])), tuple(map(tuple, row['source_strata'])),
            values['xbar'], values['nbar'], values['player_exposure'], row['directed_hours'],
            values['response_counts'], row['source_identity']))
    require(len(trainings)+1 == document['expected_states'] == document['expected_probes']
        == (6 if document['purpose'] == 'research' else 4), 'empirical state/probe inventory differs')
    return Prepared(reference, document, tuple(trainings), basis)


def _state_row(state, index, arm, parent, arrays):
    return dict(index=index, arm=arm, season=state.season, player_ids=state.player_ids,
        current_player_ids=state.current_player_ids, entrant_ids=state.entrant_ids,
        carried_only_ids=state.carried_only_ids, r=state.r, a=state.a, q=state.q,
        basis_sha256=state.basis_sha256, source_identity=state.source_identity, parent=parent,
        scale=state.scale, diagnostics=state.diagnostics, **arrays)


def fit(prepared, output):
    started, process_started = time.monotonic(), time.process_time()
    source = read_prepared(prepared)
    root = _output(output, source.document['purpose'])
    rows, previous, parent = [], None, None
    for index in range(source.document['expected_states']):
        independent = index == len(source.trainings)
        training = source.trainings[-1] if independent else source.trainings[index]
        incoming = None if independent else previous
        print(f'fitting {training.likelihood.season} {"independent" if independent else "borrowing"}', file=sys.stderr, flush=True)
        state = fit_shape_coefficients(training.likelihood, incoming)
        validate_shape_coefficient_state(training.likelihood, incoming, state)
        data = write_arrays(root, f'state-{index}.npz', {name: getattr(state, name) for name in STATE_ARRAYS})
        row = _state_row(state, index, 'independent' if independent else 'borrowing', None if independent else parent, data)
        write_json(root/f'state-{index}.json', json_values(row))
        row['record'] = _ref(root/f'state-{index}.json')
        rows.append(row)
        previous, parent = state, row['record']
    document = artifact('attribution_empirical_fit', source.document['purpose'],
        dict(prepared=source.reference, protocol=source.document['protocol']), schema_version=1,
        prepared=source.reference, protocol=source.document['protocol'], execution_status='complete',
        states=rows, state_count=len(rows),
        scale_objective_evaluations=sum(len(row['scale']['curve']) for row in rows),
        resources=_cost(started, process_started, root))
    write_json(root/'fit.json', json_values(document))
    return _ref(root/'fit.json')


def read_fit(source, path):
    reference = _ref(path)
    document = read_json(Path(path))
    require(document['kind'] == 'attribution_empirical_fit' and document['schema_version'] == 1
        and document['purpose'] == source.document['purpose'] and document['prepared'] == source.reference
        and document['protocol'] == source.document['protocol'] and document['execution_status'] == 'complete'
        and document['state_count'] == len(document['states']) == source.document['expected_states'],
        'fit is incomplete or its preparation differs')
    if document['purpose'] == 'research':
        clean_implementation(document['implementation'])
    states = []
    for index, row in enumerate(document['states']):
        independent = index == len(source.trainings)
        training = source.trainings[-1] if independent else source.trainings[index]
        record = read_json(linked_path(row['record']))
        require(record == {name: value for name, value in row.items() if name != 'record'}
            and row['index'] == index and row['arm'] == ('independent' if independent else 'borrowing')
            and row['parent'] == (None if independent or index == 0 else document['states'][index-1]['record']),
            'saved state identity or predecessor differs')
        values = load_arrays(row)
        state = ShapeCoefficientState(season=row['season'], player_ids=tuple(row['player_ids']),
            current_player_ids=tuple(row['current_player_ids']), entrant_ids=tuple(row['entrant_ids']),
            carried_only_ids=tuple(row['carried_only_ids']), r=row['r'], a=row['a'], q=row['q'],
            basis_sha256=row['basis_sha256'], source_identity=row['source_identity'], scale=row['scale'],
            diagnostics=row['diagnostics'], **values)
        validate_shape_coefficient_state(training.likelihood, None if independent or index == 0 else states[-1], state)
        states.append(state)
    require(document['scale_objective_evaluations'] == sum(len(state.scale['curve']) for state in states),
        'scale evaluation inventory differs')
    return reference, document, tuple(states)


def assess(prepared, fitted, output):
    from attribution_empirical_assessment import assess_games
    from hockey_stats.attribution_data import empirical_game_moments

    started, process_started = time.monotonic(), time.process_time()
    source = read_prepared(prepared)
    fit_ref, fit_document, states = read_fit(source, fitted)
    original = (read_empirical_fixture(Path(source.document['sources']['fixture']['path']))
        if source.document['purpose'] == 'fixture_exercise' else
        read_empirical_source(source.document['sources']['source_result'], BASIS_REF, CORPUS_REF))
    require(original.source_identity == source.document['sources']
        and original.basis.sha256 == source.basis.sha256, 'assessment original source identity differs')
    final = source.trainings[-1]
    ids = original.references[-1].player_ids
    predictions = {arm: empirical_prediction(final, state, ids) for arm, state in
        (('borrowing', states[-2]), ('independent', states[-1]), ('context', None))}
    root = _output(output, source.document['purpose'])
    probes, alternatives = [], {}
    for index, state in enumerate(states):
        independent = index == len(source.trainings)
        training = final if independent else source.trainings[index]
        previous = None if independent or index == 0 else states[index-1]
        receipt, alternative = bounded_shape_coefficient_probe(training.likelihood, previous, state)
        data = write_arrays(root, f'probe-{index}.npz', {name: getattr(alternative, name) for name in STATE_ARRAYS})
        probes.append(dict(index=index, season=state.season, arm='independent' if independent else 'borrowing',
            verified=receipt['status'] == 'verified', receipt=receipt, alternative=_state_row(alternative,
                index, 'independent' if independent else 'borrowing', fit_document['states'][index]['parent'], data)))
        if index >= len(states)-2:
            alternatives['independent_probe' if independent else 'borrowing_probe'] = empirical_prediction(final, alternative, ids)
    earlier = set().union(*(training.likelihood.player_ids for training in source.trainings[:-1]))
    current = set(final.likelihood.player_ids)
    support = {player: dict(group='current_training' if player in current else
        'carried_only' if player in earlier else 'new_to_fit', first_in_corpus_final=player not in earlier)
        for player in ids}
    inventory = {row['game_id']: row for row in source.document['inventory']}
    require(tuple(inventory) == original.grouped[-1].game_ids, 'assessment original game inventory differs')
    def games():
        for game in original.grouped[-1].game_ids:
            moment = empirical_game_moments(original.grouped[-1], original.references[-1], game)
            yield dict(moment, **inventory[game], coverage=original.game_coverage[game],
                source_identity=original.source_identity)
    regions, names = shape_regions()
    payload, native = assess_games(games(), predictions, source.basis.p, regions, names, support, alternatives, probes)
    payload['next_question'] = None
    if source.document['purpose'] == 'research' and payload['numerical_status'] == 'verified':
        payload['unresolved_reason'] = ('this joint prediction comparison does not identify a uniquely justified prior revision; '
            'frozen-source exposure consequences, omitted context and synthetic recovery remain unresolved')
    data = write_arrays(root, 'native-diagnostics.npz', native)
    payload['coverage'].update(source_annual=source.document['coverage']['source_annual'],
        zero_time_game_ids=source.document['coverage']['zero_time_game_ids'])
    payload.update(probes=probes, prepared=source.reference, protocol=source.document['protocol'], fit=fit_ref,
        partition=source.document['inventory'], months=source.document['months'],
        sources=source.document['sources'], years=source.document['years'], limits=LIMITS,
        inventory=dict(states=len(states), probes=len(probes), games=len(inventory),
            assessment_games=len(source.document['assessment_ids'])),
        preparation_resources=source.document['resources'], fit_resources=fit_document['resources'],
        state_resources=[row['diagnostics']['resources'] for row in fit_document['states']])
    payload['verification'] = dict(source_chain='verified against bound original preparation, dates, coverage and basis',
        saved_states='validated against posterior, gauge and original predecessor equations',
        state_count=len(states), probe_count=len(probes), partition_inventory='exact original inventory including zero-time games',
        source_identity_unchanged=original.source_identity == source.document['sources'],
        primary_fit_preserved=fit_ref, closure=payload['numerical']['per_game_closure_max_absolute'],
        conditional_probe_scope='fixed incoming histories; final alternatives rescored separately and together')
    payload['native_axes'].update(coordinates=grid()[0].tolist(), reference_p=source.basis.p.tolist(),
        basis_sha256=source.basis.sha256, units='recorded unblocked attempts/60',
        meaning='game means and group signed residual associations, not player-effect maps')
    payload['native_diagnostics'] = dict(**data, axes=payload['native_axes'])
    document = artifact('attribution_empirical_assessment', source.document['purpose'],
        dict(prepared=source.reference, protocol=source.document['protocol'], fit=fit_ref),
        schema_version=1, execution_status='complete', **payload, **data,
        resources=_cost(started, process_started, root))
    write_json(root/'assessment.json', json_values(document))
    return _ref(root/'assessment.json')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    preparation = sub.add_parser('prepare')
    inputs = preparation.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--source-result'); inputs.add_argument('--fixture')
    preparation.add_argument('--output', required=True)
    fitting = sub.add_parser('fit')
    fitting.add_argument('--prepared', required=True); fitting.add_argument('--output', required=True)
    assessment = sub.add_parser('assess')
    assessment.add_argument('--prepared', required=True); assessment.add_argument('--fit', required=True)
    assessment.add_argument('--output', required=True)
    reporting = sub.add_parser('report')
    reporting.add_argument('--assessment', required=True); reporting.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare': result = prepare(args.source_result, args.fixture, args.output)
        elif args.command == 'fit': result = fit(args.prepared, args.output)
        elif args.command == 'assess': result = assess(args.prepared, args.fit, args.output)
        else:
            from attribution_empirical_report import report
            result = report(args.assessment, args.output)
    except (InputContractError, OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
