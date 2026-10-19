"""04k's finite annual-borrowing comparison on response-free deployment."""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys
import time

for _thread in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[_thread] = '1'

import numpy as np
from scipy.stats import t

from hockey_stats.artifacts import (
    artifact, clean_implementation, json_values, linked_path, load_arrays,
    ordered_array_digest, read_artifact, require, resources, write_arrays, write_json,
)
from hockey_stats.attribution import (
    ShapeCoefficientLikelihood, ShapeCoefficientState, decode_shape_basis,
    fit_shape_coefficients, bounded_shape_coefficient_probe, validate_shape_coefficient_state,
)
from hockey_stats.attribution_data import (
    DeploymentDesign, deployment_accounting, deployment_design_from_rows,
    exposure_centering, grouped_deployment_from_rows, likelihood_spectrum,
    read_grouped_deployment_design, read_real_deployment_designs,
)
from hockey_stats.attribution_prediction import shape_recovery, same_deployment_excess
from hockey_stats.attribution_simulation import (
    generate_shape_score, native_transfer_templates, shape_operators, shape_regions,
)
from hockey_stats.captures import InputContractError
from hockey_stats.chance_cli import identity, output_path, read_json
from hockey_stats.shot_origins import grid


SPEC = Path(__file__).resolve().parents[2]/'docs/specs/04k-attribution-history.md'
RESEARCH_ROOT = Path('/Volumes/Expansion/hockey-stats/runs')
SEASONS = tuple(f'{year}{year+1}' for year in range(2021, 2026))
RESULT_SHA = 'c59f54cdc9256e5dcb198b916f175d90a45b59944dbd2ef3c67abb524c397e3e'
PREPARED_SHA = '94247ec3244c0fd35b886bfaae041cd01491af908752756a833805b970b7b91c'
REAL_PREPARED_SHA = 'fbc40ab798493be6fcc7068ea52eb43831ad725fb89d7a4c87242f689cb7d17b'
BASIS_REF = dict(path='/Volumes/Expansion/hockey-stats/runs/attribution-04c-20261016/prepared/basis.npz',
    sha256='67d7ee706f1d8d251cc68a0d22378e67e1961b2ac53fb764bfc0efdff11d43fc')
BASIS_SHA = '649a49ecba19de5df609d6980d9de76491afa13e9108df0d8e6500659886cc51'
CELLS = ('gaussian_half', 'gaussian_base', 'gaussian_double', 'gaussian_null', 'game_shared_base')
AMPLITUDES = dict(zip(CELLS, (.5, 1., 2., 0., 1.), strict=True))
STUDY_LABEL = 'simulated effects on observed deployment — not player ability estimates'
UNITS = '(recorded unblocked attempts/60)^2'
RULES = dict(cells=[dict(id=cell, amplitude=AMPLITUDES[cell],
    noise='working_gaussian_plus_game_shared_mean' if cell == 'game_shared_base' else 'working_gaussian') for cell in CELLS],
    namespace=404110, bit_generator='PCG64', seed_sequence='SeedSequence',
    assignment_seed=[404110, 0, 'role'], trajectory_seed=[404110, 3, 'role'],
    gaussian_seed=[404110, 1, 'record', 'year_index'], game_seed=[404110, 2, 'record', 'year_index'],
    game_variance=.5, trajectory='floor(n/6) reversal, next floor(n/6) onset; start of final season',
    templates='closest reference-mass half; radial distance to (89,0),x,y; lateral y,x; shorter prefix on ties',
    score='Q=(H/r) F B + S Z; S S.T=H', game_score='sum xi_g (A_g-xbar.T X_g) F B; raw physical F',
    carry='unchanged centered relative-rate mean and covariance; no rate rescaling',
    regional_mse='sum(((M-T)W)[C]**2)/(12*len(C)); full native physical truth',
    prediction='r**2 trace(Theta.T G Theta)-2*r trace(Theta.T G F B); G=H/(r*directed_hours)',
    scale_grid=np.arange(-8., .1, .5).tolist(), refinement=dict(xatol=1e-4,maxiter=40),
    probes=dict(record=0, base='all states', other_cells=['gaussian_double','gaussian_null','game_shared_base'],
        other_states=['borrowing_final','independent_final'], xatol=1e-6,maxiter=80,
        equation_residual_max=1e-8, physical_map_change_fraction=1e-4),
    interval='mean +/- t_.975,N-1 * sample_sd/sqrt(N); independent units are records',
    scientific_gate=None, nomination=None, admission='not_admitted', handoff=None)
LIMITS = [
    'one fixed simulated truth population on observed deployment; real-sized geometry does not make effects empirical',
    'twenty shared gaussian histories across research cells limit generality and precision; cells are not independent',
    'forty modes discard native detail; projection discrepancy is not a regional error floor',
    'league-relative carry approximates physical persistence while annual rates and exposure references change',
    'stable, reversal and onset proportions are arbitrary; actual entry and return flags are observation history, not nhl debut or ability change',
    'game-shared gaussian mean perturbations omit count-dependent shot noise and are not the earlier gamma-poisson law or empirical calibration',
    'same-deployment prediction uses fixed covariates and shared fitted context; it does not validate new lineups or future seasons',
    'monte carlo intervals condition on this truth, geometry and noise law; they are not player intervals or uncertainty over populations',
    'bounded scale-search limitations remain visible; no scientific pass gate, nominee, model admission or publication follows',
]
DESIGN_FIELDS = ('H','xbar','stratum_weight','player_exposure','u','p')
ROW_FIELDS = ('offense','defense','seconds','si','row_game_ids','player_exposure','u')


@dataclass(frozen=True)
class Prepared:
    reference: dict
    document: dict
    protocol: dict
    arrays: dict
    designs: tuple
    basis: object


def _cost(started, process_started, root):
    return dict(**resources(started),process_seconds=time.process_time()-process_started,
        output_bytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),
        output_bytes_scope='tree before current manifest serialization')


def _ref(path):
    return identity(Path(path).absolute())


def _relative_ref(parent, reference):
    return dict(reference,path=str(parent/reference['path']))


def _fixture(reference):
    path = linked_path(reference)
    document = read_json(path)
    require(document['kind']=='attribution_history_fixture' and document['schema_version']==1
        and document['purpose']=='fixture_exercise', 'wrong history fixture contract')
    parents = {name:_relative_ref(path.parent, ref) for name,ref in document['sources'].items()}
    original = read_json(linked_path(parents['deployment_fixture']))
    require(original['kind']=='attribution_deployment_fixture' and original['purpose']=='fixture_exercise',
        'wrong original synthetic deployment fixture')
    basis_document = read_json(linked_path(parents['basis_fixture']))
    basis_ref = dict(path=str(path.parent/basis_document['arrays']['file']),sha256=basis_document['arrays']['sha256'])
    with np.load(linked_path(basis_ref),allow_pickle=False) as archive:
        basis = decode_shape_basis({name:archive[name] for name in archive.files},
            basis_sha256=basis_document['basis_sha256'])
    original_ref=_relative_ref(path.parent,original['arrays'])
    parents['deployment_arrays']=original_ref
    selected=tuple(f'real_{year}_{name}' for year in range(3) for name in ROW_FIELDS)
    with np.load(linked_path(original_ref),allow_pickle=False) as archive:
        require(archive.files==[row['name'] for row in original['array_shapes']],
            'original fixture archive inventory differs')
        originals={name:archive[name] for name in selected}
    arrays = load_arrays(dict(document,arrays=_relative_ref(path.parent,document['arrays'])))
    require(document['seasons']==original['seasons']
        and [e['season'] for e in document['years']]==document['seasons']
        and np.array_equal(basis.p,np.full(656,1/656)), 'fixture seasons or uniform basis reference differ')
    designs, rows = [], []
    for year,entry in enumerate(document['years']):
        prior=original['designs']['real'][year]
        require(entry['season']==prior['season'] and entry['strata']==prior['strata'],
            'fixture geometry season/context axes changed')
        for name in ROW_FIELDS:
            expected=originals[f'real_{year}_{name}'].copy()
            if year==2 and name in ('offense','defense'):
                expected[expected==13]=15
            require(np.array_equal(arrays[entry['prefix']+'_'+name],expected),
                'history fixture changes more than the declared final identity replacement')
        current = {name:arrays[entry['prefix']+'_'+name] for name in ROW_FIELDS}
        source_refs = dict(fixture=reference,coverage=dict(kind='explicit synthetic geometry',complete=True),
            masks=dict(kind='paired synthetic spatial rows'),row_count=len(current['seconds']))
        design = deployment_design_from_rows(season=entry['season'],player_ids=tuple(entry['player_ids']),
            strata=tuple(map(tuple,entry['strata'])),arrays=current,p=basis.p,r=entry['r'],source_refs=source_refs)
        designs.append(design)
        rows.append(current)
    require([d.r for d in designs]==[50.,60.,70.]
        and [len(d.player_ids) for d in designs]==[12]*3
        and len(set().union(*(d.player_ids for d in designs)))==15,
        'history fixture rates, current or union axes differ')
    return tuple(designs),basis,rows,dict(fixture=reference,**parents,basis=basis_ref),[18,20,20]


def _research(reference):
    require(reference['sha256']==RESULT_SHA,'04j result differs from pinned selection')
    result = read_json(linked_path(reference))
    require(result['kind']=='attribution_deployment_result' and result['schema_version']==1, 'wrong selected deployment result')
    clean_implementation(result['implementation'])
    require(result['purpose']=='research' and result['execution_status']=='complete'
        and result['consumed']['prepared']['sha256']==PREPARED_SHA,'04j is incomplete or preparation differs')
    preparation = read_json(linked_path(result['consumed']['prepared']))
    require(preparation['kind']=='attribution_deployment_prepared' and preparation['schema_version']==1
        and preparation['purpose']=='research', 'wrong selected deployment preparation')
    clean_implementation(preparation['implementation'])
    real_ref = preparation['sources']['real_result']
    designs = read_real_deployment_designs(real_ref,SEASONS)
    require(designs[0].source_refs['prepared']['sha256']==REAL_PREPARED_SHA
        and [len(d.player_ids) for d in designs]==[1003,951,924,910,940]
        and [d.source_refs['row_count'] for d in designs]==[698940,881742,864050,857462,881612]
        and all(len(d.strata)==42 for d in designs)
        and len(set().union(*(d.player_ids for d in designs)))==1477,
        'selected research spatial population differs')
    with np.load(linked_path(BASIS_REF),allow_pickle=False) as archive:
        basis = decode_shape_basis({name:archive[name] for name in archive.files},basis_sha256=BASIS_SHA)
    return designs,basis,None,dict(deployment_result=reference,deployment_prepared=result['consumed']['prepared'],
        real_result=real_ref,real_prepared=designs[0].source_refs['prepared'],basis=BASIS_REF),[2004,1900,1846,1818,1878]


def _truth_history(designs, templates: np.ndarray) -> tuple[tuple[np.ndarray, ...], list[dict]]:
    """construct unit-amplitude history from validated designs and transfer templates."""
    players = tuple(sorted(set().union(*(design.player_ids for design in designs))))
    previous = set().union(*(design.player_ids for design in designs[:-1]))
    final = set(designs[-1].player_ids)
    eligible = np.asarray(sorted(final & previous), dtype=np.int64)
    assignments, positions = [], {player: i for i, player in enumerate(players)}
    labels = np.zeros((2, len(players)), dtype=np.int64)
    trajectories = np.zeros_like(labels)
    for role in range(2):
        permutation = np.random.Generator(np.random.PCG64(np.random.SeedSequence([404110, 0, role]))).permutation(players)
        for index, player in enumerate(permutation):
            labels[role, positions[int(player)]] = index % 4
        changed = np.random.Generator(np.random.PCG64(np.random.SeedSequence([404110, 3, role]))).permutation(eligible)
        k = len(eligible)//6
        for player in changed[:k]:
            trajectories[role, positions[int(player)]] = 1
        for player in changed[k:2*k]:
            trajectories[role, positions[int(player)]] = 2
        for player in players:
            code = int(labels[role, positions[player]])
            trajectory = int(trajectories[role, positions[player]])
            observed = [design.season for design in designs if player in design.player_ids]
            assignments.append(dict(role=("offense", "defense")[role], player_id=player,
                template=("radial", "lateral")[code//2], sign=1 if code % 2 == 0 else -1,
                trajectory=("no_prior_observation" if player in final-previous else
                            ("stable", "reversal", "onset")[trajectory]),
                current=player in final, prior_observation=player in previous,
                return_after_absence=player in final & previous and player not in designs[-2].player_ids,
                first_observed_season=observed[0], observed_seasons=observed))
    truths = []
    for year, design in enumerate(designs):
        raw, n = np.zeros((2*len(design.player_ids), templates.shape[1])), len(design.player_ids)
        for role in range(2):
            for row, player in enumerate(design.player_ids):
                index = positions[player]
                code, trajectory = labels[role, index], trajectories[role, index]
                sign = 1 if code % 2 == 0 else -1
                if trajectory == 1 and year == len(designs)-1:
                    sign = -sign
                if trajectory != 2 or year == len(designs)-1:
                    raw[role*n+row] = sign*templates[code//2]
        truths.append(raw)
    return tuple(truths), assignments


def prepare(deployment_result, fixture, purpose, output):
    started, process_started = time.monotonic(),time.process_time()
    require(purpose in ('research','fixture_exercise') and (deployment_result is not None)==(purpose=='research')
        and (fixture is not None)==(purpose=='fixture_exercise'),'select exactly the source matching purpose')
    designs,basis,rows,parents,ranks = (_research(_ref(deployment_result)) if purpose=='research' else _fixture(_ref(fixture)))
    root = output_path(str(output),[str(Path(ref['path']).parent) for ref in parents.values()])
    if purpose=='research':
        require(root.is_relative_to(RESEARCH_ROOT) and any(part.startswith('attribution-04k-') for part in root.parts),
            'research requires an external attribution-04k directory')
    require(all(np.array_equal(d.p,basis.p) for d in designs),'basis and annual references differ exactly')
    templates,boundaries = native_transfer_templates(grid()[0],basis.p)
    positivity = min(d.r for d in designs)-20*float(np.max(np.abs(templates/basis.p)))
    require(positivity>0,'fixed unperturbed native means fail the prospectively selected positivity bound')
    truths,assignments = _truth_history(designs,templates)
    W,names = shape_regions()
    _,near,lateral = shape_operators(W)
    arrays = dict(B=basis.B,p=basis.p,eigenvalues=basis.eigenvalues,templates=templates,W=W,near=near,lateral=lateral)
    entries,checks = [],[]
    for year,(design,truth,rank) in enumerate(zip(designs,truths,ranks,strict=True)):
        accounting = deployment_accounting(design)
        values,vectors,tau,masks = likelihood_spectrum(design.H)
        require(all(int(mask.sum())==rank for mask in masks),'annual rank differs under the existing cutoff contract')
        factor = vectors[:,masks[1]]*np.sqrt(values[masks[1]])
        residual = float(np.linalg.norm(factor@factor.T-design.H)/max(1.,np.linalg.norm(design.H)))
        require(residual<=1e-10,'annual score covariance reconstruction failed')
        n=len(design.player_ids)
        gauges=np.kron(np.eye(2),np.ones((n,1))/np.sqrt(n))
        gauge=float(np.linalg.norm(design.H@gauges)/max(1.,np.linalg.norm(design.H)))
        require(gauge<=1e-10 and (purpose!='research' or len(design.H)-rank==2),
            'discarded research directions are not exactly the two role gauges')
        grouped = read_grouped_deployment_design(design) if rows is None else grouped_deployment_from_rows(design,rows[year])
        require(rows is not None or len(grouped.game_ids)==1312, 'research game inventory differs')
        overlap=[]
        for i,player in enumerate(design.player_ids):
            shared=accounting['same_team_seconds'][i].copy()
            shared[i]=-1
            partner=int(np.argmax(shared))
            overlap.append(dict(player_id=player,strongest_partner_id=design.player_ids[partner],
                shared_minutes=float(shared[partner]/60),
                without_partner_minutes=float((design.player_exposure[i]-shared[partner])/60),
                opponent_minutes=float(accounting['opponent_seconds'][i,partner]/60)))
        accounting={key:value for key,value in accounting.items() if key not in ('same_team_seconds','opponent_seconds')}
        prefix=f'year_{year}'
        for name in DESIGN_FIELDS:
            arrays[prefix+'_'+name]=getattr(design,name)
        arrays[prefix+'_factor'],arrays[prefix+'_truth']=factor,truth
        arrays[prefix+'_centered_truth']=exposure_centering(design.u)@truth
        if rows is not None:
            for name,value in rows[year].items():
                arrays[prefix+'_rows_'+name]=value
        entries.append(dict(season=design.season,player_ids=list(design.player_ids),strata=design.strata,r=design.r,
            source_refs=design.source_refs,prefix=prefix,rank=rank,game_ids=list(grouped.game_ids),
            directed_hours=float(design.stratum_weight.sum()/design.r),accounting=accounting,overlap=overlap))
        checks.append(dict(season=design.season,rank=rank,tau=tau,covariance_relative_residual=residual,
            gauge_relative_residual=gauge,verified=True))
    root.mkdir()
    snapshot=root/'spec-snapshot.md'
    snapshot.write_bytes(SPEC.read_bytes())
    data=write_arrays(root,'geometry.npz',arrays)
    n_records=20 if purpose=='research' else 2
    inventory=[dict(cell=cell,record=record,path=f'{cell}/{record}/fit.json') for cell in CELLS for record in range(n_records)]
    counts=[]
    for role in ('offense','defense'):
        for population in ('union','final_current'):
            selected=[row for row in assignments if row['role']==role and (population=='union' or row['current'])]
            for trajectory in ('stable','reversal','onset','no_prior_observation'):
                for template in ('radial','lateral'):
                    for sign in (-1,1):
                        counts.append(dict(role=role,population=population,trajectory=trajectory,template=template,sign=sign,
                            count=sum(row['trajectory']==trajectory and row['template']==template and row['sign']==sign for row in selected)))
    fields=dict(sources=parents,seasons=[d.season for d in designs],years=entries,basis_sha256=basis.sha256,
        records=list(range(n_records)),inventory=inventory,assignments=assignments,truth_counts=counts,partitions=boundaries,
        positivity_lower_bound=positivity,region_names=list(names),factor_checks=checks,
        geometry_sha256=ordered_array_digest(arrays),
        budget=dict(pairs=len(inventory),scores=len(inventory)*len(designs),states=len(inventory)*(len(designs)+1),
            probes=len(designs)+7,scale_objective_evaluations_max=57*len(inventory)*(len(designs)+1)),**data)
    protocol=artifact('attribution_history_protocol',purpose,dict(**parents,spec_snapshot=_ref(snapshot)),
        schema_version=1,rules=RULES,study_label=STUDY_LABEL,**fields,resources=_cost(started,process_started,root))
    write_json(root/'protocol.json',json_values(protocol))
    document=artifact('attribution_history_prepared',purpose,dict(**parents,protocol=_ref(root/'protocol.json'),geometry=data['arrays']),
        schema_version=1,protocol=_ref(root/'protocol.json'),study_label=STUDY_LABEL,**fields,
        resources=_cost(started,process_started,root))
    write_json(root/'prepared.json',json_values(document))
    return _ref(root/'prepared.json')


def read_prepared(path):
    reference=_ref(path)
    document=read_artifact(linked_path(reference),'attribution_history_prepared',expected_schema=1)
    protocol=read_artifact(linked_path(document['protocol']),'attribution_history_protocol',expected_schema=1)
    fields=('sources','seasons','years','basis_sha256','records','inventory','assignments','partitions',
        'truth_counts','positivity_lower_bound','region_names','factor_checks','geometry_sha256','budget','arrays','array_shapes')
    require(document['purpose']==protocol['purpose'] and protocol['rules']==RULES
        and all(document[name]==protocol[name] for name in fields),'history prepared/protocol bindings differ')
    arrays=load_arrays(document)
    require(ordered_array_digest(arrays)==document['geometry_sha256'],'prepared numeric geometry differs')
    basis=decode_shape_basis({name:arrays[name] for name in ('B','p','eigenvalues')},basis_sha256=document['basis_sha256'])
    designs=[]
    for entry in document['years']:
        values=[arrays[entry['prefix']+'_'+name] for name in DESIGN_FIELDS]
        design=DeploymentDesign(entry['season'],tuple(entry['player_ids']),tuple(map(tuple,entry['strata'])),
            *values,entry['r'],entry['source_refs'])
        require(np.array_equal(design.p,basis.p),'prepared annual reference differs from basis')
        designs.append(design)
    return Prepared(reference,document,protocol,arrays,tuple(designs),basis)


def _likelihood(prepared,year,Q):
    design=prepared.designs[year]
    return ShapeCoefficientLikelihood(design.season,design.player_ids,design.H,Q,design.u,design.r,prepared.basis,
        dict(prepared=prepared.reference,season=design.season,score_sha256=ordered_array_digest(dict(Q=Q))))


def _state_arrays(state):
    return dict(Theta=state.Theta,V=state.V,uncentered_Theta=state.uncentered_Theta,
        centering_shift=state.centering_shift,u=state.u)


def fit(prepared,cell,record,output_root):
    started,process_started=time.monotonic(),time.process_time()
    source=read_prepared(prepared)
    require(cell in CELLS and type(record) is int and record in source.document['records'],'pair is outside fixed inventory')
    root=Path(output_root).absolute()/cell/str(record)
    if source.document['purpose']=='research':
        require(root.is_relative_to(RESEARCH_ROOT),'expensive fits require external storage')
    root.parent.mkdir(parents=True,exist_ok=True)
    require(not root.exists(),'pair output already exists')
    states,generation=[],[]
    previous=None
    numeric={}
    scores=[]
    for year,design in enumerate(source.designs):
        prefix=f'year_{year}'
        factor=source.arrays[prefix+'_factor']
        raw=AMPLITUDES[cell]*source.arrays[prefix+'_truth']
        gaussian=np.random.Generator(np.random.PCG64(np.random.SeedSequence([404110,1,record,year]))).standard_normal((factor.shape[1],40))
        grouped,game=None,None
        if cell=='game_shared_base':
            grouped=(read_grouped_deployment_design(design) if source.document['purpose']=='research' else
                grouped_deployment_from_rows(design,{name:source.arrays[prefix+'_rows_'+name] for name in ROW_FIELDS}))
            game=np.random.Generator(np.random.PCG64(np.random.SeedSequence([404110,2,record,year]))).normal(0.,np.sqrt(.5),len(grouped.game_ids))
        Q,receipt=generate_shape_score(design,factor,raw,source.basis.B,gaussian,grouped,game)
        scores.append(Q)
        numeric[prefix+'_Q']=Q
        generation.append(dict(season=design.season,**receipt))
        likelihood=_likelihood(source,year,Q)
        state=fit_shape_coefficients(likelihood,previous)
        states.append(state)
        previous=state
    states.append(fit_shape_coefficients(_likelihood(source,len(source.designs)-1,scores[-1])))
    state_rows=[]
    for index,state in enumerate(states):
        values=_state_arrays(state)
        for name,value in values.items():
            numeric[f'state_{index}_{name}']=value
        state_rows.append(dict(index=index,arm='independent' if index==len(states)-1 else 'borrowing',season=state.season,
            player_ids=list(state.player_ids),current_player_ids=list(state.current_player_ids),
            entrant_ids=list(state.entrant_ids),carried_only_ids=list(state.carried_only_ids),
            r=state.r,a=state.a,q=state.q,basis_sha256=state.basis_sha256,source_identity=state.source_identity,
            parent=None if index in (0,len(states)-1) else dict(index=index-1,sha256=ordered_array_digest(_state_arrays(states[index-1]))),
            sha256=ordered_array_digest(values),scale=state.scale,diagnostics=state.diagnostics))
    evaluations=sum(len(state.scale['curve']) for state in states)
    require(evaluations<=57*len(states),'pair exceeds fixed primary scale-objective budget')
    root.mkdir()
    data=write_arrays(root,'states.npz',numeric)
    document=artifact('attribution_history_fit',source.document['purpose'],
        dict(prepared=source.reference,protocol=source.document['protocol'],geometry=source.document['arrays']),
        schema_version=1,prepared=source.reference,protocol=source.document['protocol'],cell=cell,record=record,
        states=state_rows,generation=generation,score_count=len(scores),state_count=len(states),
        scale_objective_evaluations=evaluations,**data,resources=_cost(started,process_started,root))
    write_json(root/'fit.json',json_values(document))
    return _ref(root/'fit.json')


def _restore(source,document,arrays):
    require(document['prepared']==source.reference and document['protocol']==source.document['protocol']
        and document['purpose']==source.document['purpose'] and document['consumed']==dict(
            prepared=source.reference,protocol=source.document['protocol'],geometry=source.document['arrays']),
        'paired fit parent identity differs')
    require(document['score_count']==len(source.designs) and document['state_count']==len(source.designs)+1
        and len(document['states'])==len(source.designs)+1 and len(document['generation'])==len(source.designs),
        'paired fit score/state inventory differs')
    states=[]
    for index,row in enumerate(document['states']):
        year=min(index,len(source.designs)-1)
        values={name:arrays[f'state_{index}_{name}'] for name in ('Theta','V','uncentered_Theta','centering_shift','u')}
        parent=None if index in (0,len(source.designs)) else dict(index=index-1,sha256=ordered_array_digest(_state_arrays(states[index-1])))
        require(row['index']==index and row['parent']==parent and row['sha256']==ordered_array_digest(values)
            and row['season']==source.designs[year].season and row['r']==source.designs[year].r
            and row['basis_sha256']==source.basis.sha256
            and row['arm']==('independent' if index==len(source.designs) else 'borrowing'),
            'paired selected state identity, order or numeric digest differs')
        Q=arrays[f'year_{year}_Q']
        likelihood=_likelihood(source,year,Q)
        require(row['source_identity']==likelihood.source_identity,'state score identity differs')
        state=ShapeCoefficientState(season=row['season'],player_ids=tuple(row['player_ids']),
            current_player_ids=tuple(row['current_player_ids']),entrant_ids=tuple(row['entrant_ids']),
            carried_only_ids=tuple(row['carried_only_ids']),r=row['r'],a=row['a'],q=row['q'],
            basis_sha256=row['basis_sha256'],source_identity=row['source_identity'],scale=row['scale'],
            diagnostics=row['diagnostics'],**values)
        validate_shape_coefficient_state(likelihood,None if index in (0,len(source.designs)) else states[-1],state)
        states.append(state)
    require(document['scale_objective_evaluations']==sum(len(state.scale['curve']) for state in states),
        'paired objective-evaluation accounting differs from retained search receipts')
    return states


def _cohorts(source,role):
    final=source.designs[-1]
    assignments={row['player_id']:row for row in source.document['assignments'] if row['role']==('defense' if role=='attempts_allowed' else role)}
    labels={name:[] for name in ('all','stable','reversal','onset','no_prior_observation','actual_returner',
        'minutes_0_300','minutes_300_600','minutes_600_1000','minutes_1000_plus','template_radial','template_lateral')}
    for index,player in enumerate(final.player_ids):
        row=assignments[player]
        minutes=final.player_exposure[index]/60
        labels['all'].append(index)
        labels[row['trajectory']].append(index)
        labels['actual_returner']+=([index] if row['return_after_absence'] else [])
        labels['template_'+row['template']].append(index)
        bucket=('minutes_0_300' if minutes<300 else 'minutes_300_600' if minutes<600 else
            'minutes_600_1000' if minutes<1000 else 'minutes_1000_plus')
        labels[bucket].append(index)
    offset=0 if role=='offense' else len(final.player_ids)
    return {name:np.asarray(indices,dtype=np.int64)+offset for name,indices in labels.items()}


def _current_theta(state,design):
    indices=np.searchsorted(state.player_ids,design.player_ids)
    require(tuple(state.player_ids[i] for i in indices)==design.player_ids,'final current identities are absent from state')
    selected=np.r_[indices,len(state.player_ids)+indices]
    return exposure_centering(design.u)@state.Theta[selected]


def _record_metrics(source,cell,record,states):
    final=source.designs[-1]
    raw=AMPLITUDES[cell]*source.arrays[f'year_{len(source.designs)-1}_truth']
    truth=AMPLITUDES[cell]*source.arrays[f'year_{len(source.designs)-1}_centered_truth']
    operators=dict(twelve_region_vector=source.arrays['W'],within_20_ft=source.arrays['near'],
        lateral_redistribution=source.arrays['lateral'])
    maps={arm:final.r*_current_theta(state,final)@source.basis.R.T
        for arm,state in zip(('borrowing','independent'),states[-2:],strict=True)}
    metrics,players=[],{}
    for role in ('offense','attempts_allowed'):
        for cohort,selected in _cohorts(source,role).items():
            for operator,W in operators.items():
                denominator=len(selected)*(12 if operator=='twelve_region_vector' else 1)
                errors={arm:shape_recovery(value,truth,selected,W,denominator) if denominator else None
                    for arm,value in maps.items()}
                values={arm:None if error is None else error['mse'] for arm,error in errors.items()}
                values['zero']=None if not denominator else errors['borrowing']['zero_mse']
                values['paired_benefit']=None if not denominator else values['independent']-values['borrowing']
                for arm,value in values.items():
                    metrics.append(dict(cell=cell,record=record,role=role,cohort=cohort,operator=operator,arm=arm,
                        metric='recovery_benefit' if arm=='paired_benefit' else operator.replace('twelve_region_vector','regional')+'_mse',
                        n_players=len(selected),denominator=denominator,units=UNITS,value=value,
                        reason='empty cohort' if not denominator else None))
                if operator=='twelve_region_vector' and not denominator:
                    for arm in maps:
                        metrics.append(dict(cell=cell,record=record,role=role,cohort=cohort,operator=operator,arm=arm,
                            metric='directional_bias',n_players=0,denominator=0,omitted_zero_targets=0,
                            units='recorded unblocked attempts/60',value=None,reason='empty cohort'))
                if operator=='twelve_region_vector' and denominator:
                    target=(truth@W)[selected]
                    norm=np.linalg.norm(target,axis=1)
                    nonzero=norm>0
                    for arm,value in maps.items():
                        error=((value-truth)@W)[selected]
                        directional=None if not nonzero.any() else float(np.mean(np.sum(error[nonzero]*target[nonzero],axis=1)/norm[nonzero]))
                        metrics.append(dict(cell=cell,record=record,role=role,cohort=cohort,operator=operator,arm=arm,
                            metric='directional_bias',n_players=len(selected),denominator=int(nonzero.sum()),
                            omitted_zero_targets=int((~nonzero).sum()),units='recorded unblocked attempts/60',value=directional,
                            reason='all regional targets exactly zero' if directional is None else None))
    for arm,value in maps.items():
        players[arm]=dict(target=truth@source.arrays['W'],error=(value-truth)@source.arrays['W'])
    hours=float(final.stratum_weight.sum()/final.r)
    predictions={arm:same_deployment_excess(final.H,final.r,hours,_current_theta(state,final),raw,source.basis.B)
        for arm,state in zip(('borrowing','independent'),states[-2:],strict=True)}
    predictions['zero']=0.
    predictions['paired_cost']=predictions['borrowing']-predictions['independent']
    for arm,value in predictions.items():
        metrics.append(dict(cell=cell,record=record,role='both',cohort='all',operator='same_deployment',arm=arm,
            metric='prediction_cost' if arm=='paired_cost' else 'prediction_excess',n_players=2*len(final.player_ids),
            denominator=hours,units=UNITS,value=value,reason=None))
    return metrics,players


def _summaries(rows,n_records):
    groups={}
    for row in rows:
        key=tuple(row[name] for name in ('cell','role','cohort','operator','arm','metric'))
        groups.setdefault(key,[]).append(row)
    result=[]
    for key,records in groups.items():
        require(len(records)==n_records and len({r['record'] for r in records})==n_records,
            'metric record inventory is incomplete')
        require(len({r['denominator'] for r in records})==1 and len({r['n_players'] for r in records})==1,
            'cohort denominator changes across fixed-population records')
        values=[row['value'] for row in records]
        common=dict(zip(('cell','role','cohort','operator','arm','metric'),key,strict=True))
        common.update(n_records=n_records,n_players=records[0]['n_players'],denominator=records[0]['denominator'],
            units=records[0]['units'])
        if all(value is None for value in values):
            result.append(dict(common,mean=None,sd=None,mc_se=None,ci_low=None,ci_high=None,reason=records[0]['reason']))
            continue
        require(all(value is not None and np.isfinite(value) for value in values),'partial or nonfinite metric records')
        mean=float(np.mean(values)); sd=float(np.std(values,ddof=1)); se=sd/np.sqrt(n_records)
        margin=float(t.ppf(.975,n_records-1)*se)
        result.append(dict(common,mean=mean,sd=sd,mc_se=se,ci_low=mean-margin,ci_high=mean+margin,reason=None))
    return result


def _diagnostic_answer(index, purpose, numerical_status):
    """describe saved summaries without a threshold, gate or model choice."""
    if purpose == 'fixture_exercise':
        return 'the detached fixture verifies software behavior; it supplies no research conclusion'
    if numerical_status != 'verified':
        return 'conditional numerical movement remains unresolved; no substantive recovery or prediction conclusion is assigned'
    def summary(cell, role, cohort, arm, metric, operator='twelve_region_vector'):
        return index[(cell, role, cohort, operator, arm, metric)]
    def interval(row):
        return f"{row['mean']:.5g} [{row['ci_low']:.5g}, {row['ci_high']:.5g}]"
    clauses = []
    for role in ('offense', 'attempts_allowed'):
        independent = summary('gaussian_base', role, 'all', 'independent', 'regional_rms')
        borrowing = summary('gaussian_base', role, 'all', 'borrowing', 'regional_rms')
        benefit = summary('gaussian_base', role, 'all', 'paired_benefit', 'recovery_benefit')
        cohorts = '; '.join(cohort + ' ' + interval(summary('gaussian_base', role, cohort,
            'paired_benefit', 'recovery_benefit')) for cohort in ('stable', 'reversal', 'onset'))
        null_borrowing = summary('gaussian_null', role, 'all', 'borrowing', 'regional_rms')
        null_independent = summary('gaussian_null', role, 'all', 'independent', 'regional_rms')
        null_benefit = summary('gaussian_null', role, 'all', 'paired_benefit', 'recovery_benefit')
        clauses.append(f"{role.replace('_', ' ')}: on the fixed gaussian_base mixture, regional rms changes "
            f"from {independent['mean']:.5g} independently to {borrowing['mean']:.5g} with borrowing; "
            f"paired mse benefit is {interval(benefit)}. cohort benefits are {cohorts}. "
            f"under null truth, borrowing / independent false-map rms is {null_borrowing['mean']:.5g} / "
            f"{null_independent['mean']:.5g}; paired mse benefit is {interval(null_benefit)}.")
    prediction = '; '.join(cell + ' ' + interval(summary(cell, 'both', 'all', 'paired_cost',
        'prediction_cost', 'same_deployment')) for cell in CELLS)
    clauses.append('same-deployment prediction cost, borrowing minus independent: ' + prediction + '.')
    clauses.append('positive mse benefit favors borrowing; negative benefit is borrowing harm. '
        'positive prediction cost is borrowing harm. rms uses recorded unblocked attempts/60; '
        'benefits and costs use its square. brackets are 95% monte carlo t intervals for paired means, '
        'conditional on this truth, deployment and shared noise histories. crossing zero establishes '
        'neither equivalence nor acceptable cost; no winner or scientific gate is assigned.')
    return '\n\n'.join(clauses)


def assess(prepared,fits,output):
    started,process_started=time.monotonic(),time.process_time()
    source=read_prepared(prepared)
    root=output_path(str(output),[str(Path(prepared).absolute().parent),str(Path(fits).absolute())])
    if source.document['purpose']=='research':
        require(root.is_relative_to(RESEARCH_ROOT),'research assessment requires external storage')
    rows,probes,refs,costs=[],[],{},[]
    accum={}
    objective_evaluations=0
    for item in source.document['inventory']:
        path=Path(fits)/item['path']
        document=read_artifact(path,'attribution_history_fit',expected_schema=1)
        require(document['cell']==item['cell'] and document['record']==item['record'],'pair path and identity differ')
        arrays=load_arrays(document)
        states=_restore(source,document,arrays)
        metrics,players=_record_metrics(source,item['cell'],item['record'],states)
        rows.extend(metrics)
        refs[item['path']]=_ref(path)
        costs.append(document['resources'])
        objective_evaluations+=document['scale_objective_evaluations']
        for arm,values in players.items():
            accum.setdefault((item['cell'],arm),[]).append(values)
        if item['record']==0 and item['cell'] in ('gaussian_base','gaussian_double','gaussian_null','game_shared_base'):
            indices=range(len(states)) if item['cell']=='gaussian_base' else (len(states)-2,len(states)-1)
            for index in indices:
                year=min(index,len(source.designs)-1)
                previous=None if index in (0,len(states)-1) else states[index-1]
                likelihood=_likelihood(source,year,arrays[f'year_{year}_Q'])
                receipt,alternative=bounded_shape_coefficient_probe(likelihood,previous,states[index])
                movement=[]
                if year==len(source.designs)-1:
                    altered=list(states); altered[index]=alternative
                    changed,_=_record_metrics(source,item['cell'],item['record'],altered)
                    for original,revised in zip(metrics,changed,strict=True):
                        if original['value'] is not None:
                            movement.append(dict(role=original['role'],cohort=original['cohort'],operator=original['operator'],
                                arm=original['arm'],metric=original['metric'],record_change=revised['value']-original['value'],
                                mean_change=(revised['value']-original['value'])/len(source.document['records'])))
                probes.append(dict(cell=item['cell'],record=0,state_index=index,season=likelihood.season,
                    arm='independent' if index==len(states)-1 else 'borrowing',**receipt,metric_movement=movement))
    require(len(refs)==source.document['budget']['pairs'] and len(probes)==source.document['budget']['probes']
        and objective_evaluations<=source.document['budget']['scale_objective_evaluations_max'],
        'assessment inventory or primary evaluation budget differs')
    summaries=_summaries(rows,len(source.document['records']))
    rms_rows=[]
    for row in summaries:
        if row['metric']=='regional_mse':
            rms_rows.append(dict(row,metric='regional_rms',units='recorded unblocked attempts/60',
                **{key:None if row[key] is None else float(np.sqrt(max(0,row[key]))) for key in ('mean','ci_low','ci_high')},
                sd=None,mc_se=None,source_mse_sd=row['sd'],source_mse_mc_se=row['mc_se'],
                reason=row['reason'] or 'rms is sqrt(mean mse); sd and mc_se belong to the source mse'))
    summaries.extend(rms_rows)
    index={tuple(row[name] for name in ('cell','role','cohort','operator','arm','metric')):row for row in summaries}
    for probe in probes:
        for change in probe['metric_movement']:
            row=index[(probe['cell'],*(change[name] for name in ('role','cohort','operator','arm','metric')))]
            change['mc_se']=row['mc_se']
            change['movement_in_mc_se']=None if not row['mc_se'] else change['mean_change']/row['mc_se']
    player_rows=[]
    final=source.designs[-1]
    assignment_index={(row['role'],row['player_id']):row for row in source.document['assignments']}
    for (cell,arm),records in accum.items():
        errors=np.stack([r['error'] for r in records]); targets=records[0]['target']
        mean_error=errors.mean(axis=0); mse=np.mean(errors**2,axis=0)
        for role_index,role in enumerate(('offense','attempts_allowed')):
            for i,player in enumerate(final.player_ids):
                j=role_index*len(final.player_ids)+i
                assignment=assignment_index[('offense' if role_index==0 else 'defense',player)]
                player_rows.append(dict(cell=cell,arm=arm,role=role,player_id=player,
                    n_records=len(records),minutes=float(final.player_exposure[i]/60),
                    physical_amplitude=AMPLITUDES[cell],physical_units='recorded unblocked attempts/60',
                    squared_error_units=UNITS,
                    assigned_template_sign=assignment['sign'],
                    final_raw_template_sign=(0 if AMPLITUDES[cell]==0 else
                        assignment['sign']*(-1 if assignment['trajectory']=='reversal' else 1)),
                    target_reference='final exposure-centered physical truth',
                    target=targets[j],mean_error=mean_error[j],mean_squared_error=mse[j],
                    **{key:value for key,value in source.document['years'][-1]['overlap'][i].items() if key!='player_id'},
                    **{key:assignment[key] for key in ('template','trajectory','prior_observation',
                        'return_after_absence','first_observed_season','observed_seasons')}))
    design_rows=[]
    for year,design in enumerate(source.designs):
        entry=source.document['years'][year]
        design_rows.append(dict(season=design.season,source_refs=design.source_refs,rate=design.r,
            player_ids=design.player_ids,strata=design.strata,
            coverage=design.source_refs['coverage'],contexts=len(design.strata),directed_rows=design.source_refs['row_count'],
            players=len(design.player_ids),games=len(entry['game_ids']),directed_hours=entry['directed_hours'],
            rank=entry['rank'],exposure_seconds=float(design.player_exposure.sum()),reference_u=design.u))
    truth_rows=[dict(record_type='region_axis',region_names=source.document['region_names'])]
    for cell in RULES['cells']:
        truth_rows.append(dict(record_type='cell',cell=cell['id'],physical_amplitude=cell['amplitude'],
            noise_law=cell['noise'],amplitude_reference=1.0,physical_units='recorded unblocked attempts/60',
            squared_projection_units=UNITS,
            amplitude_scaling='physical targets and l1 transfers multiply by amplitude; squared projection discrepancies multiply by amplitude squared',
            trajectory_interpretation=('bookkeeping only; zero raw and centered effects' if cell['amplitude']==0 else
                'injected raw physical trajectories; centered targets retain the annual exposure reference')))
    templates=source.arrays['templates']
    for boundary,template in zip(source.document['partitions'],templates,strict=True):
        projection=(template@source.basis.B)@source.basis.R.T
        truth_rows.append(dict(record_type='partition',**boundary,amplitude_reference=1.0,
            physical_units='recorded unblocked attempts/60',squared_projection_units=UNITS,
            raw_l1_transfer=float(np.abs(template).sum()/2),
            projection_native_inverse_share_squared=float(np.sum((template-projection)**2/source.basis.p)),
            projection_regional_squared=float(np.sum(((template-projection)@source.arrays['W'])**2)),
            projection_limitation='native representation discrepancy; not a regional error floor'))
    for row in source.document['truth_counts']:
        exported=dict(row)
        exported['assigned_template_sign']=exported.pop('sign')
        if exported['role']=='defense':
            exported['role']='attempts_allowed'
        truth_rows.append(dict(record_type='cohort_template_sign_count',**exported))
    for row in source.document['assignments']:
        annual=[]
        for year,design in enumerate(source.designs):
            values,raw_sign=None,None
            if row['player_id'] in design.player_ids:
                raw=source.arrays[f'year_{year}_truth']
                centered=source.arrays[f'year_{year}_centered_truth']
                i=design.player_ids.index(row['player_id'])+(0 if row['role']=='offense' else len(design.player_ids))
                template=templates[0 if row['template']=='radial' else 1]
                raw_sign=int(np.sign(raw[i]@template))
                values=dict(raw_l1_transfer=float(np.abs(raw[i]).sum()/2),
                    centered_native_l1_transfer=float(np.abs(centered[i]).sum()/2),
                    raw_regional_target=raw[i]@source.arrays['W'],centered_regional_target=centered[i]@source.arrays['W'])
            annual.append(dict(season=design.season,present=values is not None,
                raw_template_sign_at_unit_amplitude=raw_sign,magnitudes=values))
        exported=dict(row)
        exported['assigned_template_sign']=exported.pop('sign')
        if exported['role']=='defense':
            exported['role']='attempts_allowed'
        truth_rows.append(dict(record_type='player_assignment',**exported,amplitude_reference=1.0,
            physical_units='recorded unblocked attempts/60',annual_physical_targets=annual))
    diagnostic_rows=[row for row in summaries if row['cohort']!='all' or row['operator']!='twelve_region_vector']
    for cell in CELLS:
        if cell=='gaussian_null':
            for role in ('offense','attempts_allowed'):
                diagnostic_rows.append(dict(cell=cell,role=role,cohort='all',operator='twelve_region_vector',
                    arm='both',metric='relative_error',n_records=len(source.document['records']),mean=None,sd=None,
                    mc_se=None,ci_low=None,ci_high=None,reason='zero native truth: report absolute false-map error',
                    denominator=0,units='ratio unavailable'))
    for item in source.document['inventory']:
        document=read_json(linked_path(refs[item['path']]))
        for state in document['states']:
            diagnostic_rows.append(dict(cell=item['cell'],record=item['record'],season=state['season'],arm=state['arm'],
                metric='scale_search',status=state['scale']['status'],own_reasons=state['scale']['own_reasons'],
                inherited_limitation=state['scale']['inherited_limitation'],a=state['a'],q=state['q']))
    numerical_status='verified' if all(probe['status']=='verified' for probe in probes) else 'unresolved'
    root.mkdir()
    numeric=write_arrays(root,'player-errors.npz',{f'{cell}_{arm}_{field}':value
        for (cell,arm),records in accum.items() for field,value in (
            ('target',records[0]['target']),('error',np.stack([r['error'] for r in records])))})
    document=artifact('attribution_history_assessment',source.document['purpose'],dict(prepared=source.reference,
        protocol=source.document['protocol'],**{f'fit_{i:03d}':ref for i,ref in enumerate(refs.values())}),
        schema_version=1,prepared=source.reference,protocol=source.document['protocol'],study_label=STUDY_LABEL,
        execution_status='complete',numerical_status=numerical_status,
        inventory=dict(**source.document['budget'],pair_paths=list(refs),
            scale_objective_evaluations=objective_evaluations),
        design_rows=design_rows,truth_rows=truth_rows,partitions=source.document['partitions'],
        region_names=source.document['region_names'],
        metric_rows=rows,comparison_rows=summaries,diagnostic_rows=diagnostic_rows,player_rows=player_rows,
        probes=probes,limits=LIMITS,
        diagnostic_answer=_diagnostic_answer(index,source.document['purpose'],numerical_status),
        next_question=None if source.document['purpose']=='fixture_exercise' or numerical_status!='verified' else
            'can an empirically justified annual prior preserve gains for stable players while reducing harm under reversals, first observations and null effects within a prospectively chosen prediction-cost budget?',
        unresolved_reason=None if numerical_status=='verified' else 'bounded conditional numerical probes did not resolve all movements',
        verification_checks=[dict(boundary='source_and_generation',status='verified',checks=source.document['factor_checks']),
            dict(boundary='inventory',status='verified',pairs=len(refs),scores=source.document['budget']['scores'],states=source.document['budget']['states']),
            dict(boundary='conditional_probes',status=numerical_status,count=len(probes))],
        preflight_resources=next(cost for item,cost in zip(source.document['inventory'],costs,strict=True)
            if item['cell']=='gaussian_base' and item['record']==0),
        preparation_resources=source.document['resources'],fit_resources=costs,**numeric,resources=_cost(started,process_started,root))
    write_json(root/'assessment.json',json_values(document))
    return _ref(root/'assessment.json')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    prepare_parser=sub.add_parser('prepare')
    group=prepare_parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--deployment-result'); group.add_argument('--fixture')
    prepare_parser.add_argument('--purpose',choices=('research','fixture_exercise'),required=True)
    prepare_parser.add_argument('--output',required=True)
    fit_parser=sub.add_parser('fit')
    fit_parser.add_argument('--prepared',required=True); fit_parser.add_argument('--cell',choices=CELLS,required=True)
    fit_parser.add_argument('--record',type=int,required=True); fit_parser.add_argument('--output-root',required=True)
    assess_parser=sub.add_parser('assess')
    assess_parser.add_argument('--prepared',required=True); assess_parser.add_argument('--fits',required=True)
    assess_parser.add_argument('--output',required=True)
    report_parser=sub.add_parser('report')
    report_parser.add_argument('--assessment',required=True); report_parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=='prepare': result=prepare(args.deployment_result,args.fixture,args.purpose,args.output)
        elif args.command=='fit': result=fit(args.prepared,args.cell,args.record,args.output_root)
        elif args.command=='assess': result=assess(args.prepared,args.fits,args.output)
        else:
            from attribution_history_report import report
            result=report(args.assessment,args.output)
    except (InputContractError,OSError,ValueError,KeyError) as error:
        print(str(error),file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
