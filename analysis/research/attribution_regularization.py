"""04g's finite comparison of annual borrowing and population shrinkage."""

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import sys
import time

for _thread in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_thread] = "1"

import numpy as np

from hockey_stats.artifacts import (
    artifact, implementation, json_values, linked_path, load_arrays, ordered_array_digest,
    read_artifact, require, resources, write_arrays, write_json,
)
from hockey_stats.attribution import (
    read_pooling_annual, read_pooling_source, read_pooling_statistics, shape_mean,
)
from hockey_stats.attribution_data import (
    POOLING_STAT_FIELDS, pooling_population, statistic_digest, synthetic_population, weighted_population,
)
from hockey_stats.attribution_prediction import (
    current_player_rows, deployment_gram, excess_prediction_terms, prediction_inner, prediction_loss,
)
from hockey_stats.attribution_simulation import synthetic_response, synthetic_rosters
from hockey_stats.captures import InputContractError
from hockey_stats.chance_cli import identity, output_path
from hockey_stats.shot_origins import grid
from attribution_pooling import (
    ARMS as OLD_ARMS, BASIS_SHA, LAWS, POPULATIONS, SEASONS, _activation_digest,
    criterion_status, fit_inventory as pooling_fit_inventory, physical_truths as paired_truths,
    read_prepared as read_pooling_prepared, truth_digest,
)
from attribution_prediction import PredictionSource, read_source


SPEC = Path(__file__).resolve().parents[2] / "docs/specs/04g-attribution-regularization.md"
RESEARCH_ROOT = Path("/Volumes/Expansion/hockey-stats/runs")
SOURCE_RESULT_SHA256 = "b2b1b2225221bc3297556229ca6fb548c78494f7cc843ba90cb3e3f28e006c32"
RATIONALE_RESULT_SHA256 = "a22161d74224c71b2f58bbfa1b39b661291bb341b6e23e5c2ae35297ada41a49"
BENCHMARK = "unblocked_spatial"
FAMILIES = ("paired", "independent")
POLICIES = ("history", "population_history")
METRICS = ("R_zero", "R_control", "R_candidate", "P_zero", "P_control", "P_candidate")
CRITERIA = ("recovery_progress", "prediction_progress", "useful_recovery", "useful_prediction")
RULES = dict(
    seasons=list(SEASONS), families=list(FAMILIES), populations=list(POPULATIONS), laws=list(LAWS),
    policies=list(POLICIES), representation="graph_40ft", rate=40., shared_null="paired",
    seeds=dict(physical_fields=40802, activation=40803, responses=40804, bootstrap=40805,
               bit_generator="PCG64", index_base=0),
    truth=dict(amplitude=.09, x=[0, 80], y=[-30, 30], width=[20, 40],
               draw_order=["x1", "y1", "w1", "x2", "y2", "w2"],
               sparse_slots=2, fields="team/role/slot; persistent across years and laws",
               reference="training role exposure; exact compensated native context",
               positivity_floor=dict(sparse=.64, diffuse=.10),
               paired="exact frozen 04e truth, activation, responses and references"),
    search=dict(q_log10=[-8., 0.], lambda_log10_one_plus=[0., 8.], spacing=.5,
                coarse_points=289, boundary="original one-dimensional selector; common full objective",
                refinement=dict(method="Powell", xtol=1e-4, ftol=1e-10, maxfev=160),
                tie_order=["objective", "lambda", "q"], expansion=False),
    numerical=dict(outer=0, years=[2, 5], states=20, equation_residual_max=1e-8,
                   movement_divided_by_r_max=1e-4, quarter_step=.25,
                   refinement=dict(method="Powell", xtol=1e-6, ftol=1e-12, maxfev=320),
                   substitutions="ten final-year candidate states; same bootstrap indices",
                   new_histories=False, downstream_propagation=False),
    recovery=dict(denominator=64, operator="J=P E_H", cutoff="100*n*eps*lambda_max",
                  sensitivity=[.1, 1., 10.], final_rank=60, regions=12,
                  inseparable=[[26, 31]], useful_fraction=.75,
                  truth="actual physical native fields; no fitted-basis projection"),
    prediction=dict(owner="hockey_stats.attribution_prediction", designs="complete fresh deployment",
                    metric="diag(p)^(-1)", zero="noisy training native context",
                    evaluation_refit=False, region_division=False),
    bootstrap=dict(resamples=10000, interval=[.025, .975], quantile="linear",
                   unit="whole paired outer records", shared_indices=True,
                   strict_positive=[True, True, False, True]),
    units="squared attempts per 60 team minutes", admission="not_admitted", handoff=None,
)
LIMITATIONS = [
    "population shrinkage can erase persistent truth as well as inherited false maps",
    "retaining marginal likelihood isolates the prior change and leaves selector suitability open",
    "the broader primary recovery target is not directly comparable with 04e's thirty-pair score",
    "independent physical fields differ in amplitude; family comparisons are not causal decompositions",
    "fixed deployments, training references, slot transitions and synthetic laws limit transport",
    "bounded local numerical checks do not prove global optimality or downstream history stability",
    "gaussian working moments are not calibrated individual-player intervals",
    "no success establishes positive fitted intensities, chance valuation or real-hockey ability",
    "the identifiable average of players 26 and 31 does not identify either individual effect",
    "paired cases and their seasons remain research-exposed",
]


def _rng(seed):
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed)))


def case_identity(family, population, law):
    require(family in FAMILIES and population in POPULATIONS and law in LAWS
            and (family == "paired" or population != "null"),
            "invalid case or duplicate independent/null inventory")
    return family, population, law


def independent_truths(designs, p, population, outer):
    """draw physical slot fields before any response; no fitted directions enter."""
    require(population in POPULATIONS[:2] and type(outer) is int and outer >= 0,
            "invalid independent truth identity")
    centers, fields, activation = grid()[0], {}, []
    for team in range(4):
        for role in range(2):
            slots = sorted(_rng([40803, outer, team, role]).choice(8, 2, replace=False).tolist())
            if population == "diffuse":
                slots = list(range(8))
            activation.append(dict(team=team, role=("offense", "defense")[role], slots=slots))
            for slot in range(8):
                rng = _rng([40802, outer, team, role, slot])
                x1, y1, w1 = rng.uniform(0, 80), rng.uniform(-30, 30), rng.uniform(20, 40)
                x2, y2, w2 = rng.uniform(0, 80), rng.uniform(-30, 30), rng.uniform(20, 40)
                g0 = (np.exp(-np.sum((centers - [x1, y1]) ** 2, axis=1) / (2 * w1 ** 2))
                      - np.exp(-np.sum((centers - [x2, y2]) ** 2, axis=1) / (2 * w2 ** 2)))
                centered = g0 - p @ g0
                normalizer = float(np.max(np.abs(centered)))
                require(np.isfinite(normalizer) and normalizer > 0, "invalid independent lobe normalization")
                fields[(team, role, slot)] = .09 * p * centered / normalizer
    truths = []
    for year, design in enumerate(designs):
        rosters, players = synthetic_rosters(year), design["players"]
        require(players == tuple(sorted(player for team in rosters for player in team)),
                "independent physical roster differs from fixed deployment")
        positions, n = {player: i for i, player in enumerate(players)}, len(players)
        raw, active = np.zeros((2 * n, len(p))), np.zeros(2 * n, dtype=bool)
        for row in activation:
            role, team = int(row["role"] == "defense"), row["team"]
            for slot in row["slots"]:
                index = role * n + positions[rosters[team][slot]]
                raw[index], active[index] = fields[(team, role, slot)], True
        means = np.array([design["u"] @ raw[role * n:(role + 1) * n] for role in range(2)])
        centered = raw - np.repeat(means, n, axis=0)
        context = 5 * means.sum(axis=0)
        floor = RULES["truth"]["positivity_floor"][population]
        rates = 40 * (p + design["X"] @ raw)
        require(np.isfinite(raw).all() and np.isfinite(centered).all() and np.isfinite(context).all()
                and np.max(np.abs(raw.sum(axis=1))) <= 1e-12
                and np.max(np.abs(centered.sum(axis=1))) <= 1e-12
                and all(np.max(np.abs(design["u"] @ centered[role*n:(role+1)*n])) <= 1e-12
                        for role in range(2))
                and np.all(rates > 0) and np.all(rates >= floor * 40 * p - 1e-12)
                and np.max(np.abs(rates - 40 * (p + context + design["X"] @ centered))) <= 1e-12,
                "independent truth positivity, normalization or role compensation failed")
        truths.append(dict(raw=raw, centered=centered, context=context, activation=activation, active=active))
    return truths


def _truths(source, family, population, outer):
    return (paired_truths if family == "paired" else independent_truths)(
        source.training, source.basis.p, population, outer)


def _activation(truths, family):
    rows = [truth["pairs" if family == "paired" else "activation"] for truth in truths]
    if family == "paired":
        return rows, _activation_digest(truths)
    import hashlib
    import json
    return rows, hashlib.sha256(json.dumps(rows, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def _cost(started, process_started, root=None):
    return dict(**resources(started), process_seconds=time.process_time() - process_started,
                output_bytes=sum(path.stat().st_size for path in root.rglob("*") if path.is_file()) if root else 0,
                output_bytes_scope="tree_before_current_manifest_serialization")


def _budget(n):
    return dict(outer_per_cell=n, cells=10, datasets=10*n, reused_datasets=6*n, fresh_datasets=4*n,
                new_histories=14*n, new_annual_states=70*n, reused_control_states=30*n,
                fresh_shape_selections=60*n, fresh_volume_selections=20*n, numerical_probes=20)


def _fixture_source(path):
    """explicit schema-4 fixture evidence; never a substitute for research inputs."""
    reference = identity(Path(path).resolve(strict=True))
    result = read_artifact(path, "attribution_pooling_result", expected_schema=4)
    require(result["purpose"] == "fixture_exercise" and result["nomination"] is None
            and result["admission"] == "not_admitted" and result["handoff"] is None,
            "fixture source must be an explicit unadmitted schema-4 fixture result")
    context = read_pooling_source(linked_path(result["prepared"]))
    prepared, protocol, basis, training, evaluation, W = read_pooling_prepared(context.reference["path"], source=context)
    require(prepared["purpose"] == "fixture_exercise" and result["protocol"] == prepared["protocol"]
            and result["spec_snapshot"] == prepared["spec_snapshot"], "fixture source parents differ")
    records, refs, manifests = pooling_fit_inventory(
        [linked_path(value) for value in result["consumed_fits"]], context.reference, prepared, protocol)
    require(refs == result["consumed_fits"] and len(records) == 12,
            "fixture source requires its exact twelve complete original datasets")
    consumed = dict(source_result=reference, source_prepared=context.reference,
                    source_protocol=prepared["protocol"], source_basis=prepared["basis"],
                    source_designs=prepared["designs"]["arrays"],
                    **{f"source_fit_{i:03d}": ref for i, ref in enumerate(refs)})
    return PredictionSource(reference, result, context, prepared, protocol, basis, training, evaluation, W,
                            records, consumed, tuple(str(Path(ref["path"]).parent) for ref in consumed.values()),
                            dict(datasets=12, annual_states=120, final_states=24,
                                 statistics_archives=12, fit_manifests=len(manifests)))


@dataclass(frozen=True)
class Prepared:
    reference: dict
    document: dict
    protocol: dict
    source: PredictionSource
    recovery: tuple
    fixed_populations: tuple


def _parents(prepared):
    document = prepared.document
    return dict(prepared=prepared.reference, protocol=document["protocol"],
                source_result=document["source_result"], source_prepared=document["source_prepared"],
                basis=document["basis"], designs=document["designs"],
                operators=document["operators"]["arrays"], spec_snapshot=document["spec_snapshot"])


def _close(actual, expected, label):
    actual, expected = np.asarray(actual), np.asarray(expected)
    require(actual.shape == expected.shape and np.isfinite(actual).all() and np.isfinite(expected).all(),
            label + ": incompatible or nonfinite values")
    error = float(np.max(np.abs(actual - expected))) if actual.size else 0.
    require(error <= 1e-8 * (1 + float(np.max(np.abs(expected), initial=0.))), label + ": reconciliation failed")
    return error


def _pair_matrix(truth, players):
    pairs = [pair for pair in truth["pairs"] if pair["expected_estimable"]]
    require(len(pairs) == 30, "original thirty-pair target changed")
    positions, n = {player: i for i, player in enumerate(players)}, len(players)
    C = np.zeros((30, 2*n))
    for row, pair in enumerate(pairs):
        role = int(pair["role"] == "defense")
        for player, value in zip(pair["players"], (1., -1.), strict=True):
            C[row, role*n + positions[player]] = value
    _close(C @ C.T, 2*np.eye(30), "original disjoint pair span")
    return C


def _original_controls(source, record, truths):
    """decode unchanged original controls, checking every saved pair and prediction risk."""
    statistics = read_pooling_statistics(record["statistics"]["arrays"], source.context)
    require(record["truth_sha256"] == truth_digest(truths)
            and record["activation_sha256"] == _activation_digest(truths)
            and record["activation"] == [truth["pairs"] for truth in truths]
            and len(record["responses"]) == len(record["losses"]) == 5
            and list(record["annual"]) == list(OLD_ARMS), "original truth or history inventory differs")
    require(record["statistics"]["array_shapes"] == [dict(name=name, shape=list(value.shape), dtype=value.dtype.str)
            for name, value in statistics.arrays.items()], "original statistic metadata changed")
    populations, states, previous, audit = [], {}, None, []
    for year, season in enumerate(SEASONS):
        response = record["responses"][year]
        population = pooling_population(source.context, statistics, record["population"], record["law"], record["outer"], season)
        require(response["year"] == year+1 and response["season"] == season
                and response["seed"] == [40604, POPULATIONS.index(record["population"]), LAWS.index(record["law"]), record["outer"], year]
                and response["sufficient_statistics_sha256"] == statistic_digest(population),
                "original response or statistic lineage changed")
        ref = record["annual"]["graph_40ft"][year]
        annual = read_artifact(linked_path(ref), "attribution_pooling_annual", expected_schema=4)
        require(annual["prepared"] == source.context.reference and annual["population"] == record["population"]
                and annual["law"] == record["law"] and annual["outer"] == record["outer"]
                and annual["season"] == season and annual["representation"] == "graph_40ft"
                and annual["response_sha256"] == response["sha256"]
                and annual["statistics"] == record["statistics"]["arrays"], "original control source or response changed")
        state = read_pooling_annual(ref["path"], source=source.context, previous=previous, statistics=statistics)
        maps = shape_mean(state)[current_player_rows(state, population.player_ids)]
        C = _pair_matrix(truths[year], population.player_ids)
        R = float(np.sum((40*C @ (maps-truths[year]["centered"]) @ source.W)**2)/30)
        gram = deployment_gram(source.evaluation[year]["X"], source.evaluation[year]["si"],
                               source.evaluation[year]["e"], len(population.strata))
        P = prediction_loss(gram, state.shape.A-truths[year]["context"], maps-truths[year]["centered"], p=source.basis.p)
        audit.append(dict(year=year+1, pair_recovery=_close(R, record["losses"][year]["R_control"], "original control pair risk"),
                          prediction=_close(P, record["losses"][year]["P_control"], "original control prediction risk")))
        populations.append(population)
        states[(BENCHMARK, season)] = state
        previous = (ref, state)
    return tuple(populations), states, audit


def prepare(source_result, purpose, output):
    from hockey_stats.attribution_data import identifiable_recovery_operator

    started, process_started = time.monotonic(), time.process_time()
    require(purpose in ("research", "fixture_exercise"), "invalid preparation purpose")
    source = read_source(source_result) if purpose == "research" else _fixture_source(source_result)
    root = output_path(str(output), list(source.input_roots))
    if purpose == "research":
        require(root.is_relative_to(RESEARCH_ROOT) and root.name.startswith("attribution-04g-"),
                "research output requires an exclusive external attribution-04g directory")
    root.mkdir()
    snapshot = root/"spec-snapshot.md"
    with snapshot.open("xb") as destination:
        destination.write(SPEC.read_bytes())
    operators, receipts = {}, []
    # designs and likelihood geometry are response independent; check the score before new draws.
    first = source.records[0]
    first_stats = read_pooling_statistics(first["statistics"]["arrays"], source.context)
    for year, design in enumerate(source.training):
        population = pooling_population(source.context, first_stats, first["population"], first["law"], first["outer"], SEASONS[year])
        J, receipt = identifiable_recovery_operator(population.H, design["u"], design["players"],
            inseparable_groups=((26, 31),), expected_rank=60 if purpose == "research" else None)
        operators[SEASONS[year]+"_J"] = J
        receipts.append(dict(season=SEASONS[year], **receipt))
    original_audit = []
    for record in source.records:
        truths = paired_truths(source.training, source.basis.p, record["population"], record["outer"])
        _, _, audit = _original_controls(source, record, truths)
        original_audit.append(dict(population=record["population"], law=record["law"], outer=record["outer"], annual=audit))
    binding = write_arrays(root, "recovery-operators.npz", operators)
    consumed = dict(source_result=source.reference, source_prepared=source.context.reference,
                    source_protocol=source.prepared["protocol"], basis=source.prepared["basis"],
                    designs=source.prepared["designs"]["arrays"], operators=binding["arrays"], spec_snapshot=identity(snapshot))
    protocol_path = root/"protocol.json"
    n = 200 if purpose == "research" else 2
    protocol = artifact("attribution_regularization_protocol", purpose, consumed, schema_version=5,
        **consumed, **RULES, output_root=str(root), source_inventory=source.inventory,
        source_result_sha256=SOURCE_RESULT_SHA256 if purpose == "research" else source.reference["sha256"],
        rationale_result_sha256=RATIONALE_RESULT_SHA256, rationale_selection_input=False,
        source_exposure="research_exposed" if purpose == "research" else "fixture_exercise",
        basis_sha256=source.basis.sha256, source_design_sha256=source.prepared["design_sha256"],
        budget=_budget(n), recovery_receipts=receipts, limitations=LIMITATIONS, resources=_cost(started, process_started, root))
    write_json(protocol_path, json_values(protocol))
    prepared = artifact("attribution_regularization_prepared", purpose,
        dict(protocol=identity(protocol_path), **consumed), schema_version=5,
        protocol=identity(protocol_path), **{key: value for key, value in consumed.items() if key != "operators"},
        operators=binding, budget=_budget(n),
        basis_sha256=source.basis.sha256, source_design_sha256=source.prepared["design_sha256"],
        source_inventory=source.inventory, recovery_receipts=receipts, original_control_audit=original_audit,
        original_control_audit_count=len(original_audit), original_annual_audit_count=5*len(original_audit),
        limits=LIMITATIONS, admission="not_admitted", handoff=None, resources=_cost(started, process_started, root))
    path = root/"prepared.json"
    write_json(path, json_values(prepared))
    return identity(path)


def read_prepared(path):
    from hockey_stats.attribution_data import identifiable_recovery_operator

    reference = identity(Path(path).resolve(strict=True))
    document = read_artifact(path, "attribution_regularization_prepared", expected_schema=5)
    protocol = read_artifact(linked_path(document["protocol"]), "attribution_regularization_protocol", expected_schema=5)
    purpose = document["purpose"]
    source = read_source(linked_path(document["source_result"])) if purpose == "research" else _fixture_source(linked_path(document["source_result"]))
    n = 200 if purpose == "research" else 2
    require(protocol["purpose"] == purpose and all(protocol.get(name) == expected for name, expected in RULES.items())
            and protocol["budget"] == document["budget"] == _budget(n)
            and document["source_inventory"] == protocol["source_inventory"] == source.inventory
            and document["basis_sha256"] == protocol["basis_sha256"] == source.basis.sha256
            and (purpose != "research" or source.basis.sha256 == BASIS_SHA)
            and document["source_design_sha256"] == protocol["source_design_sha256"] == source.prepared["design_sha256"]
            and document["source_prepared"] == source.context.reference
            and document["source_result"] == source.reference and document["source_protocol"] == source.prepared["protocol"]
            and document["basis"] == source.prepared["basis"] and document["designs"] == source.prepared["designs"]["arrays"]
            and document["spec_snapshot"] == protocol["spec_snapshot"]
            and document["operators"]["arrays"] == protocol["operators"]
            and document["recovery_receipts"] == protocol["recovery_receipts"]
            and document["original_control_audit_count"] == len(source.records)
            and document["original_annual_audit_count"] == 5*len(source.records)
            and document["limits"] == protocol["limitations"] == LIMITATIONS
            and document["admission"] == "not_admitted" and document["handoff"] is None,
            "04g prepared scientific, source, geometry or inventory contract differs")
    require(document["consumed"] == dict(protocol=document["protocol"], **protocol["consumed"])
            and all(document[name] == value for name, value in protocol["consumed"].items()
                    if name != "operators"), "04g prepared parents differ")
    if purpose == "research":
        require(document["implementation"] == protocol["implementation"]
                and protocol["source_result_sha256"] == SOURCE_RESULT_SHA256,
                "04g producer or original result changed")
    arrays, recovery, fixed_populations = load_arrays(document["operators"]), [], []
    first = source.records[0]
    statistics = read_pooling_statistics(first["statistics"]["arrays"], source.context)
    require(list(arrays) == [season+"_J" for season in SEASONS], "recovery operator names/order differ")
    for year, design in enumerate(source.training):
        population = pooling_population(source.context, statistics, first["population"], first["law"], first["outer"], SEASONS[year])
        J, receipt = identifiable_recovery_operator(population.H, design["u"], design["players"],
            inseparable_groups=((26, 31),), expected_rank=60 if purpose == "research" else None)
        require(np.array_equal(arrays[SEASONS[year]+"_J"], J)
                and document["recovery_receipts"][year] == json_values(dict(season=SEASONS[year], **receipt)),
                "saved recovery operator or rank receipt changed")
        recovery.append(J)
        fixed_populations.append(population)
    return Prepared(reference, document, protocol, source, tuple(recovery), tuple(fixed_populations))


def _construction_receipts(source, truths, population, outer):
    """check both deployments and the old pair complement before response draws."""
    receipts = []
    old_truths = paired_truths(source.training, source.basis.p, "null", outer)
    for year, truth in enumerate(truths):
        training, evaluation = source.training[year], source.evaluation[year]
        C = _pair_matrix(old_truths[year], training["players"])
        complement = truth["centered"] - .5*C.T @ (C @ truth["centered"])
        gram = deployment_gram(evaluation["X"], evaluation["si"], evaluation["e"], len(training["strata"]))
        # deployment designs expose stratum means through their sufficient geometry.
        xbar = np.zeros((len(training["strata"]), 64))
        for stratum in range(len(xbar)):
            rows = training["si"] == stratum
            xbar[stratum] = np.asarray(training["X"][rows].T @ training["e"][rows]).ravel()/training["e"][rows].sum()
        whole = np.vstack((-xbar @ truth["centered"], truth["centered"]))
        rest = np.vstack((-xbar @ complement, complement))
        total = prediction_inner(gram, whole, whole, p=source.basis.p)
        omitted = prediction_inner(gram, rest, rest, p=source.basis.p)
        require(np.isfinite(total) and np.isfinite(omitted) and total > 0 and omitted > 0,
                "independent truth has no nonzero evaluation-deployment pair-complement signal")
        for name, design in (("training", training), ("evaluation", evaluation)):
            rates = 40*(source.basis.p + design["X"] @ truth["raw"])
            floor = RULES["truth"]["positivity_floor"][population]
            require(np.isfinite(rates).all() and np.all(rates > 0)
                    and np.all(rates >= floor*40*source.basis.p-1e-12),
                    "independent "+name+" physical rate positivity failed")
        receipts.append(dict(year=year+1, total_energy=total, complement_energy=omitted,
                             complement_fraction=omitted/total, selected_truth=False))
    return receipts


def _check_fixed_design(population, frozen):
    require(population.player_ids == frozen.player_ids and population.strata == frozen.strata
            and population.r == frozen.r and np.array_equal(population.p, frozen.p)
            and all(np.array_equal(getattr(population, name), getattr(frozen, name))
                    for name in ("H", "xbar", "u", "player_exposure", "stratum_weight")),
            "fresh sufficient statistics changed the fixed training design or exposure reference")


def _fresh_populations(prepared, truths, protocol_sha, population, law, outer):
    source = prepared.source
    populations, responses, arrays = [], [], {}
    for year, (design, truth) in enumerate(zip(source.training, truths, strict=True)):
        seed = [40804, POPULATIONS.index(population), LAWS.index(law), outer, year]
        response = synthetic_response(design, 40*(source.basis.p + design["X"] @ truth["raw"]), law, _rng(seed))
        response_sha = ordered_array_digest(dict(response=response))
        grouped, references = synthetic_population(design, response, year, protocol_sha, LAWS.index(law), outer,
            population_id=f"synthetic:04g:independent:{population}:{law}:{outer}:{BENCHMARK}")
        annual = weighted_population(grouped, np.ones(len(grouped.game_ids)), references)
        _check_fixed_design(annual, prepared.fixed_populations[year])
        populations.append(annual)
        responses.append(dict(year=year+1, season=SEASONS[year], seed=seed, sha256=response_sha,
                              sufficient_statistics_sha256=statistic_digest(annual)))
        arrays.update({SEASONS[year]+"_"+name: np.asarray(getattr(annual, name)) for name in POOLING_STAT_FIELDS})
        del response
    return tuple(populations), responses, arrays


def _decode_populations(prepared, record):
    from hockey_stats.attribution_data import decode_saved_population

    source, arrays = prepared.source, load_arrays(record["statistics"])
    require(list(arrays) == [season+"_"+name for season in SEASONS for name in POOLING_STAT_FIELDS],
            "04g sufficient-statistic names or annual order changed")
    populations = []
    for year, season in enumerate(SEASONS):
        design = source.training[year]
        population = decode_saved_population(
            {name: arrays[season+"_"+name] for name in POOLING_STAT_FIELDS}, benchmark=BENCHMARK,
            season=season, season_index=year, source_protocol_sha256=prepared.document["protocol"]["sha256"],
            population_id=f"synthetic:04g:independent:{record['population']}:{record['law']}:{record['outer']}:{BENCHMARK}",
            player_ids=design["players"], strata=tuple(map(tuple, design["strata"])),
            expected_p=source.basis.p, expected_r=40.)
        _check_fixed_design(population, prepared.fixed_populations[year])
        response = record["responses"][year]
        require(response["year"] == year+1 and response["season"] == season
                and response["seed"] == [40804, POPULATIONS.index(record["population"]), LAWS.index(record["law"]), record["outer"], year]
                and response["sufficient_statistics_sha256"] == statistic_digest(population),
                "new response seed or sufficient-statistic identity changed")
        populations.append(population)
    return tuple(populations)


def _active_rows(truth, players):
    if "active" in truth:
        return truth["active"]
    positions, n = {player: i for i, player in enumerate(players)}, len(players)
    active = np.zeros(2*n, dtype=bool)
    for pair in truth["pairs"]:
        for player in pair["players"]:
            active[int(pair["role"] == "defense")*n+positions[player]] = pair["active"]
    return active


def annual_risks(control, candidate, population, training, evaluation, truth, basis, W, J, *, direct=False):
    """score actual physical truth with training geometry and fresh complete lineups."""
    from hockey_stats.attribution import complete_rates

    p, true_maps, n = basis.p, truth["centered"], len(population.player_ids)
    require(n == 32 and J.shape == (64, 64) and W.shape == (656, 12)
            and control.player_ids == candidate.player_ids
            and control.current_player_ids == candidate.current_player_ids
            and all(np.array_equal(getattr(control.volume, key), getattr(candidate.volume, key))
                    for key in ("M", "V", "A", "prior_mean", "prior_covariance")),
            "paired annual states changed identity, denominator or shared volume")
    gram = deployment_gram(evaluation["X"], evaluation["si"], evaluation["e"], len(population.strata))
    yh = population.ybar-population.ybar.sum(axis=1, keepdims=True)*p
    noise = yh-truth["context"]-population.xbar @ true_maps
    projected = true_maps @ basis.B @ basis.R.T
    target = 40*J @ true_maps @ W
    active = _active_rows(truth, population.player_ids)
    # the old pair grouping is fixed by team slots, independent of family activation.
    pairs = []
    positions = {player: i for i, player in enumerate(population.player_ids)}
    from attribution_pooling import PAIR_SLOTS
    rosters = synthetic_rosters(population.season_index)
    for team, roster in enumerate(rosters):
        for role in range(2):
            for slots in PAIR_SLOTS[team]:
                players = [roster[slot] for slot in slots]
                if players == [26, 31]:
                    continue
                c = np.zeros(64)
                c[role*n+positions[players[0]]], c[role*n+positions[players[1]]] = 1., -1.
                pairs.append(c)
    C = np.asarray(pairs)
    require(C.shape == (30, 64), "secondary thirty-pair denominator changed")
    result = dict(R_zero=float(np.sum(target**2)/64),
                  P_zero=prediction_loss(gram, yh-truth["context"], -true_maps, p=p),
                  denominator=64, pair_denominator=30,
                  pair_R_zero=float(np.sum((40*C @ true_maps @ W)**2)/30),
                  projected_truth_regional_error=float(np.sum((40*J @ (projected-true_maps) @ W)**2)/64),
                  projected_truth_native_error=float(np.sum((40*J @ (projected-true_maps))**2)/64),
                  true_native_energy=float(np.sum((40*J @ true_maps)**2)/64),
                  physically_active=int(active.sum()), direct_verified=direct, residuals={})
    rows_by_arm = {}
    for name, state in (("control", control), ("candidate", candidate)):
        selected = current_player_rows(state, population.player_ids)
        maps = shape_mean(state)[selected]
        rows_by_arm[name] = maps
        result["residuals"][name+"_context"] = _close(state.shape.A, yh-population.xbar @ maps, name+" native context")
        error = 40*J @ (maps-true_maps)
        region_errors = np.sum((error @ W)**2, axis=1)/64
        R = float(region_errors.sum())
        P = prediction_loss(gram, state.shape.A-truth["context"], maps-true_maps, p=p)
        excess = excess_prediction_terms(gram, population.xbar, noise, true_maps, maps, p=p)
        result["residuals"][name+"_signed_excess"] = _close(excess["delta"], P-result["P_zero"], name+" signed prediction excess")
        result["R_"+name], result["P_"+name] = R, P
        result["pair_R_"+name] = float(np.sum((40*C @ (maps-true_maps) @ W)**2)/30)
        partitions = dict(active=float(region_errors[active].sum()), inactive=float(region_errors[~active].sum()),
                          offense=float(region_errors[:n].sum()), defense=float(region_errors[n:].sum()))
        _close(partitions["active"]+partitions["inactive"], R, "full-J activation partition")
        _close(partitions["offense"]+partitions["defense"], R, "role recovery partition")
        volume_maps = state.volume.M[selected, 0, None]*p
        complete = error+40*J @ volume_maps
        volume_error = 40*J @ volume_maps
        native_shape, native_volume = float(np.sum(error**2)/64), float(np.sum(volume_error**2)/64)
        cross = float(2*np.sum(error*volume_error)/64)
        native_complete = float(np.sum(complete**2)/64)
        _close(native_complete, native_shape+native_volume+cross, "native complete-rate signed partition")
        transition = []
        for player in (32, 33, 8):
            if player not in positions or (player == 8 and population.season_index < 3):
                continue
            event_year = 4 if player == 8 else 3
            for role in range(2):
                index = role*n+positions[player]
                transition.append(dict(player=player, role=("offense", "defense")[role], event_year=event_year,
                    event=("return" if player == 8 else "entry") if population.season_index+1 == event_year else "post_transition",
                    regional_squared_error=float(region_errors[index])))
        inseparable = []
        for role in range(2):
            a, b = role*n+positions[26], role*n+positions[31]
            difference = 40*((maps[a]-maps[b])-(true_maps[a]-true_maps[b])) @ W
            average = 20*((maps[a]+maps[b])-(true_maps[a]+true_maps[b])) @ W
            inseparable.append(dict(role=("offense", "defense")[role], players=[26, 31],
                average_status="identifiable", average_regional_squared_error=float(2*np.sum(average**2)/64),
                difference_status="not_estimable", difference_regional_squared_error=float(np.sum(difference**2))))
        scale = state.shape.scale
        positions_seen = {player: i for i, player in enumerate(state.player_ids)}
        columns = np.asarray([[positions_seen[player] for player in offense]
            + [len(positions_seen)+positions_seen[player] for player in defense]
            for offense, defense in zip(evaluation["offense"], evaluation["defense"], strict=True)])
        negative_cells, negative_rows, minimum = 0, 0, None
        for start in range(0, len(columns), 256):
            rates = complete_rates(state, columns[start:start+256], evaluation["si"][start:start+256])
            negative_cells += int(np.count_nonzero(rates < 0))
            negative_rows += int(np.count_nonzero(np.any(rates < 0, axis=1)))
            minimum = float(rates.min()) if minimum is None else min(minimum, float(rates.min()))
        result[name] = dict(regional_partition=partitions, native_shape_error=native_shape,
            native_volume_error=native_volume, native_cross_term=cross, native_complete_error=native_complete,
            projected_regional_error=float(np.sum((40*J @ (maps-projected) @ W)**2)/64),
            projected_native_error=float(np.sum((40*J @ (maps-projected))**2)/64),
            complete_prediction_error=prediction_loss(gram,
                state.shape.A+state.volume.A*p-p-truth["context"], maps+volume_maps-true_maps, p=p),
            false_map_regional_rms=float(np.sqrt(partitions["inactive"])),
            maximum_inactive_regional_error=float(np.max(region_errors[~active], initial=0.)),
            transitions=transition, inseparable=inseparable, prediction_excess=excess,
            scale=dict(a=state.shape.a, q=state.shape.q,
                       selected=scale["selected"], status=scale["status"], own_reasons=scale["own_reasons"],
                       inherited_limitation=scale["inherited_limitation"]),
            negativity=dict(cells=negative_cells, rows=negative_rows, evaluated_cells=len(columns)*len(p),
                            evaluated_rows=len(columns), minimum_rate=minimum))
    if direct:
        direct_losses = dict(zero=0., control=0., candidate=0.)
        exposure_total = float(evaluation["e"].sum())
        for start in range(0, len(evaluation["e"]), 256):
            stop = start+256
            X, si, exposure = evaluation["X"][start:stop], evaluation["si"][start:stop], evaluation["e"][start:stop]
            truth_eta = 40*(X @ truth["raw"])
            estimators = dict(zero=40*yh[si],
                control=40*(control.shape.A[si]+X @ rows_by_arm["control"]),
                candidate=40*(candidate.shape.A[si]+X @ rows_by_arm["candidate"]))
            for arm, values in estimators.items():
                direct_losses[arm] += float(np.sum(exposure[:, None]*(values-truth_eta)**2/p)/exposure_total)
        for arm, loss in direct_losses.items():
            result["residuals"][arm+"_direct_prediction"] = _close(loss, result["P_"+arm], arm+" direct deployment rows")
        # direct row multiplication avoids the gram risk implementation.
        for arm in ("control", "candidate"):
            direct_R = 40**2*float(np.linalg.norm(J @ (rows_by_arm[arm]-true_maps) @ W, ord="fro")**2)/64
            result["residuals"][arm+"_direct_recovery"] = _close(direct_R, result["R_"+arm], arm+" direct recovery rows")
    return result


def fit(prepared, family, population, law, start, stop, output):
    from hockey_stats.attribution import bounded_regularization_resolution_check, write_regularization_annual
    from hockey_stats.attribution_uncertainty import annual_receipts, fit_population_history

    started, process_started = time.monotonic(), time.process_time()
    prepared = read_prepared(prepared)
    source, document, protocol = prepared.source, prepared.document, prepared.protocol
    case_identity(family, population, law)
    require(type(start) is int and type(stop) is int and 0 <= start < stop <= protocol["budget"]["outer_per_cell"],
            "fit outer range differs from frozen budget")
    root = output_path(str(output), list(source.input_roots))
    require(root.is_relative_to(Path(protocol["output_root"])), "fit output escaped frozen 04g root")
    if document["purpose"] == "research":
        require(implementation() == protocol["implementation"], "fit producer differs from frozen protocol")
    root.mkdir()
    records = []
    originals = {(row["population"], row["law"], row["outer"]): row for row in source.records}
    for outer in range(start, stop):
        outer_started, outer_process = time.monotonic(), time.process_time()
        directory = root/f"outer-{outer:03d}"
        directory.mkdir()
        truths = _truths(source, family, population, outer)
        activation, activation_sha = _activation(truths, family)
        source_identity = dict(kind="synthetic", prepared=document["source_prepared"],
                               family=family, population=population, law=law, outer=outer)
        histories = {policy: [] for policy in POLICIES}
        original_audit, construction = [], []
        if family == "paired":
            original = originals[(population, law, outer)]
            populations, control, original_audit = _original_controls(source, original, truths)
            statistics, responses = original["statistics"], original["responses"]
            histories["history"] = original["annual"]["graph_40ft"]
            control_receipt = dict(status="reused_control", source=source.reference,
                                   original_annual_audit=original_audit)
        else:
            construction = _construction_receipts(source, truths, population, outer)
            populations, responses, arrays = _fresh_populations(prepared, truths, document["protocol"]["sha256"], population, law, outer)
            statistics = write_arrays(directory, "statistics.npz", arrays)
            control_receipt, control = fit_population_history(populations, [], source_identity=source_identity,
                model_protocol_sha256=document["protocol"]["sha256"], prior_policy="history",
                representation="graph_40ft", basis=source.basis)
            require(control_receipt["status"] == "complete", "independent control history is incomplete: "+str(control_receipt.get("error")))
            previous = None
            for year, season in enumerate(SEASONS):
                state = control[(BENCHMARK, season)]
                ref = write_regularization_annual(state, directory/f"history-{season}", population=populations[year],
                    basis=source.basis, prepared=prepared.reference, protocol=document["protocol"],
                    source=document["source_prepared"], statistics=statistics["arrays"], basis_reference=document["basis"],
                    previous=previous, shared_volume=None, family=family, population_name=population, law=law,
                    outer=outer, response_sha256=responses[year]["sha256"], purpose=document["purpose"])
                histories["history"].append(ref)
                previous = (ref, state)
        controls = {(BENCHMARK, season): ref for season, ref in zip(SEASONS, histories["history"], strict=True)}
        candidate_receipt, candidate = fit_population_history(populations, [], source_identity=source_identity,
            model_protocol_sha256=document["protocol"]["sha256"], prior_policy="population_history",
            representation="graph_40ft", basis=source.basis, shared_volume=control, control_references=controls)
        require(candidate_receipt["status"] == "complete", "candidate history is incomplete: "+str(candidate_receipt.get("error")))
        previous, probes = None, []
        for year, season in enumerate(SEASONS):
            key = (BENCHMARK, season)
            state, shared = candidate[key], (controls[key], control[key])
            ref = write_regularization_annual(state, directory/f"population-history-{season}", population=populations[year],
                basis=source.basis, prepared=prepared.reference, protocol=document["protocol"], source=document["source_prepared"],
                statistics=statistics["arrays"], basis_reference=document["basis"], previous=previous, shared_volume=shared,
                family=family, population_name=population, law=law, outer=outer,
                response_sha256=responses[year]["sha256"], purpose=document["purpose"])
            histories["population_history"].append(ref)
            if outer == 0 and year in (1, 4):
                altered, receipt = bounded_regularization_resolution_check(populations[year],
                    previous[1] if previous else None, state, regions=source.W)
                receipt = dict(receipt, original_annual=ref)
                probe_ref = write_regularization_annual(altered, directory/f"probe-population-history-{season}",
                    population=populations[year], basis=source.basis, prepared=prepared.reference,
                    protocol=document["protocol"], source=document["source_prepared"], statistics=statistics["arrays"],
                    basis_reference=document["basis"], previous=previous, shared_volume=shared,
                    family=family, population_name=population, law=law, outer=outer,
                    response_sha256=responses[year]["sha256"], purpose=document["purpose"], numerical_probe=receipt)
                probes.append(dict(year=year+1, annual=probe_ref, original_annual=ref, receipt=receipt))
            previous = (ref, state)
        records.append(dict(family=family, population=population, law=law, outer=outer, status="complete",
            truth_sha256=truth_digest(truths), activation=activation, activation_sha256=activation_sha,
            exposure="research_exposed" if family == "paired" else "new_synthetic",
            responses=responses, statistics=statistics, annual=histories,
            work=dict(history="reused_control" if family == "paired" else "computed", population_history="computed"),
            control_source=source.reference if family == "paired" else None,
            original_control_audit=original_audit, construction=construction, numerical_probes=probes,
            history_receipts={policy: (dict(status=receipt["status"], annual=annual_receipts(receipt["annual"]),
                source_identity=receipt["source_identity"], prior_policy=receipt["prior_policy"], resources=receipt["resources"])
                if "annual" in receipt else receipt)
                for policy, receipt in (("history", control_receipt), ("population_history", candidate_receipt))},
            resources=_cost(outer_started, outer_process, directory)))
    cost_per = (dict(datasets=1, new_histories=1, new_annual_states=5, reused_control_states=5,
                     fresh_shape_selections=4, fresh_volume_selections=0) if family == "paired" else
                dict(datasets=1, new_histories=2, new_annual_states=10, reused_control_states=0,
                     fresh_shape_selections=9, fresh_volume_selections=5))
    result = artifact("attribution_regularization_fit", document["purpose"], _parents(prepared), schema_version=5,
        **_parents(prepared), family=family, population=population, law=law,
        range=dict(start=start, stop=stop), records=records, status="complete",
        cost={key: value*(stop-start) for key, value in cost_per.items()},
        resources=_cost(started, process_started, root), admission="not_admitted", handoff=None)
    path = root/"fit.json"
    write_json(path, json_values(result))
    return identity(path)


def fit_inventory(paths, prepared):
    """require exact disjoint coverage; missing work never becomes scientific rejection."""
    expected = prepared.protocol["budget"]["outer_per_cell"]
    records, references, documents, identities = [], [], [], set()
    parents = _parents(prepared)
    for path in paths:
        reference = identity(Path(path).resolve(strict=True))
        require(reference not in references, "duplicate 04g fit manifest")
        document = read_artifact(path, "attribution_regularization_fit", expected_schema=5)
        family, population, law = case_identity(document["family"], document["population"], document["law"])
        require(document["purpose"] == prepared.document["purpose"] and document["consumed"] == parents
                and all(document[name] == value for name, value in parents.items())
                and document["status"] == "complete" and document["admission"] == "not_admitted"
                and document["handoff"] is None, "04g fit parents, purpose or completion changed")
        if document["purpose"] == "research":
            require(document["implementation"] == prepared.protocol["implementation"], "fit producer differs from frozen protocol")
        start, stop = document["range"]["start"], document["range"]["stop"]
        require(type(start) is int and type(stop) is int and 0 <= start < stop <= expected
                and [row["outer"] for row in document["records"]] == list(range(start, stop)),
                "fit half-open range is invalid or its ordered records are incomplete")
        per = dict(datasets=1, new_histories=1 if family == "paired" else 2,
                   new_annual_states=5 if family == "paired" else 10,
                   reused_control_states=5 if family == "paired" else 0,
                   fresh_shape_selections=4 if family == "paired" else 9,
                   fresh_volume_selections=0 if family == "paired" else 5)
        require(document["cost"] == {key: value*(stop-start) for key, value in per.items()},
                "fit selected-work inventory differs")
        for row in document["records"]:
            key = (family, population, law, row["outer"])
            require(key not in identities and (row["family"], row["population"], row["law"]) == key[:3]
                    and row["status"] == "complete" and list(row["annual"]) == list(POLICIES)
                    and all(len(row["annual"][policy]) == 5 for policy in POLICIES)
                    and len(row["responses"]) == 5, "duplicate, overlapping or mismatched fitted dataset")
            identities.add(key)
            records.append(row)
        references.append(reference)
        documents.append(document)
    required = {(family, population, law, outer) for family in FAMILIES
                for population in (POPULATIONS if family == "paired" else POPULATIONS[:2])
                for law in LAWS for outer in range(expected)}
    require(identities == required, "assessment requires all ten exact disjoint family/population/law ranges")
    total = {name: sum(document["cost"][name] for document in documents) for name in documents[0]["cost"]}
    budget = prepared.protocol["budget"]
    require(all(value == budget[name] for name, value in total.items()), "total work differs from frozen finite budget")
    return sorted(records, key=lambda row: (FAMILIES.index(row["family"]), POPULATIONS.index(row["population"]),
                                           LAWS.index(row["law"]), row["outer"])), references, documents


def _read_fresh_annual(prepared, record, reference, population, previous, shared):
    from hockey_stats.attribution import read_regularization_annual

    annual = read_artifact(linked_path(reference), "attribution_regularization_annual", expected_schema=5)
    require(all(annual[name] == record[name] for name in ("family", "law", "outer"))
            and annual["population"] == record["population"] and annual["season"] == population.season
            and annual["response_sha256"] == record["responses"][population.season_index]["sha256"],
            "fresh annual case, year or response identity differs from its manifest")
    return read_regularization_annual(reference["path"], population=population, basis=prepared.source.basis,
        prepared=prepared.reference, protocol=prepared.document["protocol"], source=prepared.document["source_prepared"],
        statistics=record["statistics"]["arrays"], basis_reference=prepared.document["basis"],
        previous=previous, shared_volume=shared)


def criterion_rows(records, family, population, law):
    """one paired bootstrap index matrix drives every contrast in a cell."""
    case_identity(family, population, law)
    require(population != "null" and bool(records)
            and [row["outer"] for row in records] == list(range(len(records))),
            "criterion records must contain the complete ordered non-null cell")
    values = np.asarray([[row[name] for name in METRICS] for row in records])
    require(np.isfinite(values).all(), "nonfinite primary risk")
    seed = [40805, FAMILIES.index(family), POPULATIONS.index(population), LAWS.index(law)]
    indices = _rng(seed).integers(0, len(records), size=(10000, len(records)))
    means = values.mean(axis=0)
    bootstrap_means = values[indices].mean(axis=1)
    def contrasts(v):
        rz, rc, rb, pz, pc, pb = v.T
        return np.column_stack((rc-rb, pc-pb, .75*rz-rb, pz-pb))
    point = contrasts(means[None, :])[0]
    bounds = np.quantile(contrasts(bootstrap_means), [.025, .975], axis=0, method="linear")
    return [dict(family=family, population=population, law=law, criterion=name,
                 mean=float(point[i]), lower=float(bounds[0, i]), upper=float(bounds[1, i]),
                 status=criterion_status(bounds[0, i], bounds[1, i], strict), strict_positive=strict,
                 seed=seed, n=len(records), resamples=10000, quantile="linear", units=RULES["units"])
            for i, (name, strict) in enumerate(zip(CRITERIA, (True, True, False, True), strict=True))]


def _null_rows(records, law):
    seed = [40805, 0, 2, LAWS.index(law)]
    values = np.asarray([[row[name] for name in METRICS] for row in records])
    require(np.isfinite(values).all() and np.all(values[:, 0] == 0), "null physical recovery truth is not zero")
    indices = _rng(seed).integers(0, len(records), size=(10000, len(records)))
    def metrics(v):
        rz, rc, rb, pz, pc, pb = v.T
        return np.column_stack((rc, rb, rc-rb, pz, pc, pb, pc-pb, pz-pb))
    names = ("R_control", "R_candidate", "recovery_progress", "P_zero", "P_control", "P_candidate",
             "prediction_progress", "own_prediction_gain")
    point = metrics(values.mean(axis=0, keepdims=True))[0]
    bounds = np.quantile(metrics(values[indices].mean(axis=1)), [.025, .975], axis=0, method="linear")
    return [dict(family="paired", population="null", law=law, metric=name, mean=float(point[i]),
                 lower=float(bounds[0, i]), upper=float(bounds[1, i]), seed=seed, n=len(records),
                 resamples=10000, units=RULES["units"], nomination_gate=False) for i, name in enumerate(names)]


def _joint_status(rows, names):
    selected = [row["status"] for row in rows if row["criterion"] in names]
    require(len(selected) == 8*len(names), "joint decision has an incomplete criterion denominator")
    return "supported" if all(status == "supported" for status in selected) else (
        "failed" if "failed" in selected else "inconclusive")


def _summary(records):
    summaries = []
    for family in FAMILIES:
        for population in (POPULATIONS if family == "paired" else POPULATIONS[:2]):
            for law in LAWS:
                cell = [row for row in records if (row["family"], row["population"], row["law"]) == (family, population, law)]
                row = dict(family=family, population=population, law=law, n=len(cell),
                           means={name: float(np.mean([record[name] for record in cell])) for name in METRICS})
                for arm in ("control", "candidate"):
                    details = [record[arm] for record in cell]
                    row[arm] = dict(inactive=float(np.mean([record["regional_partition"]["inactive"] for record in details])),
                        native_shape_error=float(np.mean([record["native_shape_error"] for record in details])),
                        native_volume_error=float(np.mean([record["native_volume_error"] for record in details])),
                        native_cross_term=float(np.mean([record["native_cross_term"] for record in details])),
                        complete_prediction_error=float(np.mean([record["complete_prediction_error"] for record in details])),
                        negative_cells=sum(record["negativity"]["cells"] for record in details),
                        evaluated_cells=sum(record["negativity"]["evaluated_cells"] for record in details),
                        unresolved_scales=sum(record["scale"]["status"] == "scale_unresolved" for record in details),
                        inherited_scales=sum(bool(record["scale"]["inherited_limitation"]) for record in details),
                        mean_q=float(np.mean([record["scale"]["q"] for record in details])),
                        mean_lambda=float(np.mean([record["scale"]["selected"].get("lambda", 0) for record in details])),
                        lower_q=sum(record["scale"]["selected"]["variance"] == 1e-8 for record in details),
                        upper_q=sum(record["scale"]["selected"]["variance"] == 1. for record in details),
                        upper_lambda=sum(record["scale"]["selected"].get("lambda", 0) == 1e8-1 for record in details),
                        zero_lambda=sum(record["scale"]["selected"].get("lambda", 0) == 0 for record in details),
                        transitions=[dict(player=player, role=role,
                            regional_squared_error=float(np.mean([event["regional_squared_error"] for record in details
                                for event in record["transitions"] if event["player"] == player and event["role"] == role])))
                            for player in (32, 33, 8) for role in ("offense", "defense")])
                summaries.append(row)
    return summaries


def assess(prepared, fits, output):
    """read selected states and saved probes; never fit or search during assessment."""
    started, process_started = time.monotonic(), time.process_time()
    prepared = read_prepared(prepared)
    source, document, protocol = prepared.source, prepared.document, prepared.protocol
    records, references, manifests = fit_inventory(fits, prepared)
    root = output_path(str(output), list(source.input_roots))
    require(root.is_relative_to(Path(protocol["output_root"])), "assessment output escaped frozen 04g root")
    if document["purpose"] == "research":
        require(implementation() == protocol["implementation"], "assessment producer differs from frozen protocol")
    originals = {(row["population"], row["law"], row["outer"]): row for row in source.records}
    primary, secondary, probe_records, substitutions = [], [], [], {}
    n = protocol["budget"]["outer_per_cell"]
    for record in records:
        family, population, law, outer = (record[name] for name in ("family", "population", "law", "outer"))
        truths = _truths(source, family, population, outer)
        activation, activation_sha = _activation(truths, family)
        require(record["truth_sha256"] == truth_digest(truths) and record["activation"] == activation
                and record["activation_sha256"] == activation_sha,
                "record physical truth, activation or deterministic digest changed")
        if family == "paired":
            original = originals[(population, law, outer)]
            populations, control, audit = _original_controls(source, original, truths)
            require(record["statistics"] == original["statistics"] and record["responses"] == original["responses"]
                    and record["annual"]["history"] == original["annual"]["graph_40ft"]
                    and record["original_control_audit"] == audit
                    and record["control_source"] == source.reference and record["construction"] == []
                    and record["work"] == dict(history="reused_control", population_history="computed"),
                    "paired record changed original responses, controls or reused-work identity")
        else:
            populations, control = _decode_populations(prepared, record), {}
            require(record["construction"] == _construction_receipts(source, truths, population, outer)
                    and record["original_control_audit"] == [] and record["control_source"] is None
                    and record["work"] == dict(history="computed", population_history="computed"),
                    "new physical construction or fresh-work identity differs")
        expected_probe_years = [2, 5] if outer == 0 else []
        require([probe["year"] for probe in record["numerical_probes"]] == expected_probe_years,
                "record does not contain exactly its frozen candidate numerical probes")
        previous = {policy: None for policy in POLICIES}
        for year, season in enumerate(SEASONS):
            annual_population = populations[year]
            control_ref = record["annual"]["history"][year]
            if family == "independent":
                control[(BENCHMARK, season)] = _read_fresh_annual(prepared, record, control_ref, annual_population,
                                                               previous["history"], None)
            control_state = control[(BENCHMARK, season)]
            candidate_ref = record["annual"]["population_history"][year]
            shared = (control_ref, control_state)
            candidate_state = _read_fresh_annual(prepared, record, candidate_ref, annual_population,
                                                previous["population_history"], shared)
            require(control_state.prior_policy == "history" and candidate_state.prior_policy == "population_history",
                    "control/candidate prior policy swap")
            risks = annual_risks(control_state, candidate_state, annual_population, source.training[year],
                source.evaluation[year], truths[year], source.basis, source.W, prepared.recovery[year],
                direct=outer in (0, n-1))
            output_row = dict(family=family, population=population, law=law, outer=outer, year=year+1, **risks)
            secondary.append(output_row)
            if year == 4:
                primary.append(output_row)
            if outer == 0 and year in (1, 4):
                probe = next(probe for probe in record["numerical_probes"] if probe["year"] == year+1)
                require(probe["original_annual"] == candidate_ref
                        and probe["receipt"]["original_annual"] == candidate_ref,
                        "numerical probe changed its original annual parent")
                alternate = _read_fresh_annual(prepared, record, probe["annual"], annual_population,
                                              previous["population_history"], shared)
                selected = current_player_rows(candidate_state, annual_population.player_ids)
                delta = shape_mean(alternate)[selected]-shape_mean(candidate_state)[selected]
                movement = max(float(np.max(np.abs(delta))), float(np.max(np.abs(delta @ source.W))))
                receipt = probe["receipt"]
                saved = read_artifact(linked_path(probe["annual"]), "attribution_regularization_annual", expected_schema=5)
                require(saved["numerical_probe"] == receipt, "probe receipt differs from its saved state")
                valid = receipt["status"] == "verified" and movement <= 1e-4
                probe_risks = annual_risks(control_state, alternate, annual_population, source.training[year],
                    source.evaluation[year], truths[year], source.basis, source.W, prepared.recovery[year])
                probe_records.append(dict(family=family, population=population, law=law, outer=outer,
                    year=year+1, original_annual=candidate_ref, probe_annual=probe["annual"], receipt=receipt,
                    maximum_current_native_or_region_movement_divided_by_r=movement,
                    verified=valid, risks={name: probe_risks[name] for name in METRICS}))
                if year == 4:
                    substitutions[(family, population, law, outer)] = probe_risks
            previous["history"] = (control_ref, control_state)
            previous["population_history"] = (candidate_ref, candidate_state)
    require(len(primary) == 10*n and len(secondary) == 50*n and len(probe_records) == 20
            and len(substitutions) == 10, "assessment record or numerical probe inventory differs")
    changed_primary = [dict(row, **substitutions[(row["family"], row["population"], row["law"], 0)])
                       if row["outer"] == 0 else row for row in primary]
    rows, substituted_rows, null_rows, substituted_null_rows = [], [], [], []
    for family in FAMILIES:
        for population in POPULATIONS[:2]:
            for law in LAWS:
                cell = [row for row in primary if (row["family"], row["population"], row["law"]) == (family, population, law)]
                rows.extend(criterion_rows(cell, family, population, law))
                changed = [row for row in changed_primary
                           if (row["family"], row["population"], row["law"]) == (family, population, law)]
                substituted_rows.extend(criterion_rows(changed, family, population, law))
    for law in LAWS:
        null_rows.extend(_null_rows([row for row in primary if row["population"] == "null" and row["law"] == law], law))
        substituted_null_rows.extend(_null_rows(
            [row for row in changed_primary if row["population"] == "null" and row["law"] == law], law))
    unchanged = all(row["status"] == changed["status"] for row, changed in zip(rows, substituted_rows, strict=True))
    numerical_verified = unchanged and all(probe["verified"] for probe in probe_records)
    criterion_decision = dict(progress=_joint_status(rows, CRITERIA[:2]), nomination=_joint_status(rows, CRITERIA))
    progress = criterion_decision["progress"] if numerical_verified else "numerically_unresolved"
    nomination = criterion_decision["nomination"] if numerical_verified else "numerically_unresolved"
    scientific_nomination = "population_history" if nomination == "supported" else None
    if document["purpose"] == "fixture_exercise":
        scientific_nomination = None
    summaries = _summary(primary)
    root.mkdir()
    figures = _figure(root, rows, document["purpose"], "verified" if numerical_verified else "numerically_unresolved")
    consumed = dict(**_parents(prepared), **{f"fit_{i:03d}": reference for i, reference in enumerate(references)})
    assessment = artifact("attribution_regularization_assessment", document["purpose"], consumed, schema_version=5,
        prepared=prepared.reference, protocol=document["protocol"], fits=references,
        execution_status="complete", numerical_status="verified" if numerical_verified else "numerically_unresolved",
        progress_status=progress, nomination_status=nomination, nomination=scientific_nomination,
        criterion_decision=criterion_decision,
        admission="not_admitted", handoff=None, records=primary, secondary=secondary,
        criterion_rows=rows, null_rows=null_rows, summaries=summaries,
        earlier_years=[dict(year=year, family=family, population=population, law=law, n=n,
            means={name: float(np.mean([row[name] for row in secondary
                if (row["year"], row["family"], row["population"], row["law"]) == (year, family, population, law)]))
                for name in METRICS}) for year in range(1, 5) for family in FAMILIES
            for population in (POPULATIONS if family == "paired" else POPULATIONS[:2]) for law in LAWS],
        numerical=dict(probes=probe_records, substitutions=substituted_rows, classes_unchanged=unchanged,
                       substituted_null_rows=substituted_null_rows, substituted_summaries=_summary(changed_primary),
                       final_year_substitutions=10, no_downstream_propagation=True),
        exact_completeness=dict(datasets=len(primary), annual_states=10*10*n, primary_denominator=64,
                                paired_records=6*n, independent_records=4*n, null_datasets=2*n,
                                original_control_audit=6*n, probes=len(probe_records)),
        costs={key: sum(manifest["cost"][key] for manifest in manifests) for key in manifests[0]["cost"]},
        fit_resources=[manifest["resources"] for manifest in manifests], figures=figures,
        interval_meaning="mean risks over generated truths and fitting/selection variation, conditional on fixed designs, references and frozen fitting rule; not individual-player intervals",
        limits=LIMITATIONS, resources=_cost(started, process_started, root))
    assessment_path = root/"assessment.json"
    write_json(assessment_path, json_values(assessment))
    reports = _report(root, assessment)
    result = artifact("attribution_regularization_result", document["purpose"],
        dict(assessment=identity(assessment_path), **consumed,
             **{f"report_{i:02d}": reference for i, reference in enumerate(reports)},
             **{f"figure_{i:02d}": reference for i, reference in enumerate(figures)}),
        schema_version=5, assessment=identity(assessment_path), prepared=prepared.reference,
        protocol=document["protocol"], consumed_fits=references, execution_status=assessment["execution_status"],
        numerical_status=assessment["numerical_status"], criterion_rows=rows,
        progress_status=progress, nomination_status=nomination, nomination=scientific_nomination,
        criterion_decision=criterion_decision,
        admission="not_admitted", handoff=None, exact_completeness=assessment["exact_completeness"],
        costs=assessment["costs"], reports=reports, figures=figures, limits=LIMITATIONS,
        resources=_cost(started, process_started, root))
    path = root/"result.json"
    write_json(path, json_values(result))
    return identity(path)


def _figure(output, rows, purpose, numerical_status):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    titles = ("recovery improvement over history", "prediction improvement over history",
              "recovery: 25% below zero maps", "prediction gain over zero maps")
    colors = dict(paired="#246178", independent="#8e5441")
    figure, axes = plt.subplots(1, 4, figsize=(17, 5.7), sharey=True, constrained_layout=True)
    labels = []
    for panel, (criterion, title) in enumerate(zip(CRITERIA, titles, strict=True)):
        ax = axes[panel]
        selected = [row for row in rows if row["criterion"] == criterion]
        require(len(selected) == 8, "figure needs every non-null cell in each panel")
        for index, row in enumerate(selected):
            color = colors[row["family"]]
            ax.plot([row["lower"], row["upper"]], [index, index], color=color, linewidth=2)
            ax.plot(row["mean"], index, "o", color=color, markersize=4)
            if panel == 0:
                labels.append(" / ".join(row[name].replace("_", " ") for name in ("family", "population", "law")))
        ax.axvline(0, color="#666666", linewidth=.9)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("squared attempts / 60 team minutes", fontsize=9)
        ax.grid(axis="x", color="#dddddd", linewidth=.5)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", labelsize=8)
    axes[0].set_yticks(range(8), labels, fontsize=9)
    axes[0].invert_yaxis()
    heading = "population shrinkage with annual borrowing: mean paired contrasts and 95% intervals"
    if purpose == "fixture_exercise":
        heading = "fixture exercise — "+heading
    figure.suptitle(heading, fontsize=13)
    figure.supxlabel(f"numerical status: {numerical_status}; positive values favor population_history\nfixed designs and references; no individual-player interval claim", fontsize=9)
    path = output/"recovery-prediction.png"
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return [identity(path)]


def _report(output, assessment):
    def number(value):
        return f"{value:.6g}"
    rows, summaries = assessment["criterion_rows"], assessment["summaries"]
    table = ["# recovery and prediction", "", f"numerical status: `{assessment['numerical_status']}`. the interval conclusions below are criterion-only classifications; a numerically unresolved result withholds the overall scientific conclusions.", "", "all contrasts use squared attempts per 60 team minutes. intervals describe mean risks across whole paired outer records, conditional on fixed designs and references. positive contrasts favor population shrinkage. useful recovery admits a zero lower bound; the other three claims require a positive lower bound. zero-map prediction retains the noisy training native context. evaluation uses fresh complete within-season deployment and known means, without an evaluation context fit; it is not future-season forecasting.", "",
             "| family | population | law | contrast | mean | 95% interval | conclusion |",
             "|---|---|---|---|---:|---|---|"]
    for row in rows:
        table.append("| "+" | ".join([row["family"], row["population"], row["law"],
            row["criterion"].replace("_", " "), number(row["mean"]),
            f"[{number(row['lower'])}, {number(row['upper'])}]", row["status"]])+" |")
    table.extend(["", "| family | population | law | zero recovery | history recovery | population recovery | zero prediction | history prediction | population prediction |",
                  "|---|---|---|---:|---:|---:|---:|---:|---:|"])
    for row in summaries:
        table.append("| "+" | ".join([row["family"], row["population"], row["law"],
                                      *(number(row["means"][name]) for name in METRICS)])+" |")
    table.extend(["", "the primary score averages the full identifiable, exposure-centered player space with denominator 64. the inseparable players {26,31} contribute their identifiable average twice. their individual difference remains `not_estimable`. the historical thirty-pair score and frozen verdict retain their original meaning.", ""])
    comparison = output/"comparison-table.md"
    with comparison.open("x") as destination:
        destination.write("\n".join(table))
    diagnostics = ["# null, scale and transition diagnostics", "", "null cells are shared once, under the paired family. they carry no nomination veto. all risks use squared attempts per 60 team minutes; no null ratios are formed.", "",
                   "| law | null risk or difference | mean | 95% interval |",
                   "|---|---|---:|---|"]
    for row in assessment["null_rows"]:
        diagnostics.append(f"| {row['law']} | {row['metric']} | {number(row['mean'])} | [{number(row['lower'])}, {number(row['upper'])}] |")
    diagnostics.extend(["", "inactive risks apply the full identifiable and reference-centering operator before selecting physically inactive rows. an inactive physical field can have nonzero relative truth. scale limitations are retained and reported without becoming a separate nomination veto.", "",
                        "| family | population | law | arm | inactive recovery | mean q | mean lambda | lower q / n | upper q / n | zero lambda / n | upper lambda / n | unresolved / n | inherited / n | negative complete cells / total |",
                        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"])
    for row in summaries:
        for arm in ("control", "candidate"):
            values = row[arm]
            diagnostics.append("| "+" | ".join([row["family"], row["population"], row["law"], arm,
                number(values["inactive"]), number(values["mean_q"]), number(values["mean_lambda"]),
                f"{values['lower_q']} / {row['n']}", f"{values['upper_q']} / {row['n']}",
                f"{values['zero_lambda']} / {row['n']}", f"{values['upper_lambda']} / {row['n']}",
                f"{values['unresolved_scales']} / {row['n']}", f"{values['inherited_scales']} / {row['n']}",
                f"{values['negative_cells']} / {values['evaluated_cells']}"])+" |")
    diagnostics.extend(["", "| family | population | law | arm | player | role | final-year transition recovery contribution |",
                        "|---|---|---|---|---:|---|---:|"])
    for row in summaries:
        for arm in ("control", "candidate"):
            for transition in row[arm]["transitions"]:
                diagnostics.append("| "+" | ".join([row["family"], row["population"], row["law"], arm,
                    str(transition["player"]), transition["role"], number(transition["regional_squared_error"])])+" |")
    diagnostics.extend(["", "native complete-rate error retains signed volume–shape cross terms. actual versus spatially projected truth, roles, activation, every year, the thirty-pair score, identifiable pair averages and unsupported differences remain in assessment.json. no map examples were selected.",
                        "", f"new fitted histories: {assessment['costs']['new_histories']}; fresh shape selections: {assessment['costs']['fresh_shape_selections']}; fresh volume selections: {assessment['costs']['fresh_volume_selections']}. measured fitting wall time: {number(sum(row['wall_seconds'] for row in assessment['fit_resources']))} seconds; maximum recorded process memory: {max(row['peak_memory_bytes'] for row in assessment['fit_resources'])} bytes; fit output before fit-manifest serialization: {sum(row['output_bytes'] for row in assessment['fit_resources'])} bytes. numerical probe work is recorded separately and does not add histories.",
                        "", f"numerical status: `{assessment['numerical_status']}`. all twenty probes retain original incoming histories; ten final-year substitutions reuse bootstrap indices. classification stability: `{str(assessment['numerical']['classes_unchanged']).lower()}`. this does not test global optimality or propagation of earlier probe changes.", ""])
    diagnostic_path = output/"diagnostics-table.md"
    with diagnostic_path.open("x") as destination:
        destination.write("\n".join(diagnostics))
    contrary = sorted(rows, key=lambda row: row["lower"])
    weakest = contrary[0]
    supported_nomination = assessment["nomination"] == "population_history"
    decision = ["# population shrinkage with annual borrowing", "",
        f"progress support: **{assessment['progress_status']}**. nomination support: **{assessment['nomination_status']}**. nominated estimator: **{assessment['nomination'] or 'none'}**. numerical status: **{assessment['numerical_status']}**.", ""]
    if assessment["purpose"] == "fixture_exercise":
        decision.append("this is a tiny fixture exercise. it verifies software boundaries and cannot supply a research conclusion or nomination.")
    elif supported_nomination:
        decision.append("population_history is nominated only as a synthetic mean estimator under these fixed deployments, physical truths and frozen selection rule. no real-hockey model or player ability is admitted.")
    else:
        decision.append("no estimator is nominated. a completed computation, supported improvement over history and useful-estimator nomination are separate claims.")
    if assessment["numerical_status"] != "verified":
        decision.append(f"the criterion-only conjunctions are progress `{assessment['criterion_decision']['progress']}` and nomination `{assessment['criterion_decision']['nomination']}`. the overall scientific conclusions remain numerically unresolved.")
    decision.extend(["", f"the least favorable lower endpoint is {number(weakest['lower'])} for {weakest['criterion'].replace('_', ' ')} in {weakest['family']}/{weakest['population']}/{weakest['law']} (95% interval [{number(weakest['lower'])}, {number(weakest['upper'])}]). the [comparison table](comparison-table.md) gives every cell, including contrary and inconclusive evidence. null risks, inactive maps, scale limitations, entry/return behavior and fitted-rate negativity appear beside it in the [diagnostics table](diagnostics-table.md). the [four aligned interval panels](recovery-prediction.png) show every non-null cell.", "",
        "the new recovery target covers all identifiable, training-reference-centered player combinations. it weights the identifiable average of players {26,31} twice; neither individual effect nor their difference is identified. it changes the primary target prospectively and preserves 04e's frozen thirty-pair failure and 04f's accounting.", "",
        "continued shrinkage can erase persistent truth as well as false maps. retaining marginal likelihood isolates the prior change while leaving that selector's suitability open. independently generated fields broaden the physical truths and differ in amplitude; between-family differences are not causal effects. fixed designs, synthetic laws and slot transitions limit transport. bounded probes leave global-search and downstream-history uncertainty. working covariance is not a calibrated player interval; negative fitted rates are not clipped.", "",
        "admission remains `not_admitted`; handoff is null. no additional fit or scientific question is selected by this report.", ""])
    decision_path = output/"decision.md"
    text = "\n".join(decision)
    require(len(text.split()) <= 500, "decision report exceeds five hundred words")
    with decision_path.open("x") as destination:
        destination.write(text)
    return [identity(path) for path in (decision_path, comparison, diagnostic_path)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    preparation = commands.add_parser("prepare")
    preparation.add_argument("--source-result", required=True)
    preparation.add_argument("--purpose", choices=("research", "fixture_exercise"), required=True)
    preparation.add_argument("--output", required=True)
    fitting = commands.add_parser("fit")
    fitting.add_argument("--prepared", required=True)
    fitting.add_argument("--family", choices=FAMILIES, required=True)
    fitting.add_argument("--population", choices=POPULATIONS, required=True)
    fitting.add_argument("--law", choices=LAWS, required=True)
    fitting.add_argument("--start", type=int, required=True)
    fitting.add_argument("--stop", type=int, required=True)
    fitting.add_argument("--output", required=True)
    assessment = commands.add_parser("assess")
    assessment.add_argument("--prepared", required=True)
    assessment.add_argument("--fits", nargs="+", required=True)
    assessment.add_argument("--output", required=True)
    arguments = vars(parser.parse_args(argv))
    command = arguments.pop("command")
    try:
        reference = {"prepare": prepare, "fit": fit, "assess": assess}[command](**arguments)
    except (InputContractError, OSError, ValueError, KeyError, np.linalg.LinAlgError) as error:
        print(str(error), file=sys.stderr)
        return 1
    import json
    print(json.dumps(reference, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
