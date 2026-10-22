"""04o's fixed score and game-time attribution comparison."""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys
import time

for _thread in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_thread] = "1"

import numpy as np

from hockey_stats.artifacts import (
    artifact, clean_implementation, json_values, linked_path, load_arrays,
    ordered_array_digest, require, resources, write_arrays, write_json,
)
from hockey_stats.attribution import (
    decode_shape_basis, fit_shape_coefficients, fit_scalar_score_coefficients,
    scalar_score_control_equivalence, validate_shape_coefficient_state,
    validate_scalar_coefficient_state, validate_scalar_score_coefficient_state,
)
from hockey_stats.attribution_data import (
    coefficient_state_row, decode_coefficient_state, read_coefficient_record,
    read_context_fixture, read_context_source, verify_context_control_training,
)
from hockey_stats.captures import InputContractError
from hockey_stats.chance_cli import identity, read_json


SPEC = Path(__file__).resolve().parents[2] / "docs/specs/04o-attribution-context.md"
RESEARCH_ROOT = Path("/Volumes/Expansion/hockey-stats/runs")
SEASONS = tuple(f"{year}{year+1}" for year in range(2021, 2026))
STATE_ARRAYS = dict(volume=("beta", "V", "uncentered_beta", "centering_shift", "u"),
    shape=("Theta", "V", "uncentered_Theta", "centering_shift", "u"))
OBJECTIVES = dict(volume="gaussian_score_scale_contrast_v1", shape="gaussian_shape_score_scale_contrast_v1")
MAIN_COMPONENTS = tuple((arm, component) for arm in ("control", "candidate") for component in ("volume", "shape"))
RULES = dict(
    arms=["control", "candidate"], components=["volume", "shape"],
    states=dict(selected=20, new=10, reused=10), seasons=SEASONS,
    temporal_basis=dict(periods=[1, 2, 3], score_factors=["1", "max(s,0)", "max(-s,0)"],
        powers=[1, 2], order="period, score factor, time power", rank=18,
        time="tau=(period_seconds-600)/600", overtime="zero added terms; preserve coarse context"),
    shape_modes=40, centering="within coarse context using training exposure only",
    rank_rule="lambda_min(correlation(D)) > 18*eps_float64*lambda_max(correlation(D))",
    scale_grid=np.arange(-8., .1, .5).tolist(), refinement=dict(xatol=1e-4, maxiter=40),
    probes=dict(xatol=1e-6, maxiter=80, equation_residual_max=1e-8, current_movement_fraction=1e-4),
    main_bit_order=[dict(arm=arm, component=component) for arm, component in MAIN_COMPONENTS],
    variants=16, seed=404130, draws=2000, bit_generator="PCG64",
    schemes=["games", "calendar_7_day", "calendar_14_day"],
    intervals="linear two-sided 95% percentile; fits, scales, split and population fixed",
    metric="complete twelve-region contrast / (12*directed_hours)",
    units="(recorded unblocked attempts/60)^2", direction="lower is better",
    scalar_objective=OBJECTIVES["volume"],
    nominal_rank_check="fixed eighteen-column design; no column removal or ridge rescue",
    nomination=None, admission="not_admitted", handoff=None,
)


@dataclass(frozen=True)
class Prepared:
    reference: dict
    document: dict
    trainings: tuple
    populations: tuple
    basis: object


def _ref(path):
    return identity(Path(path).absolute())


def _cost(started, process_started, root):
    return dict(**resources(started), process_seconds=time.process_time()-process_started,
        output_bytes=sum(path.stat().st_size for path in root.rglob("*") if path.is_file()),
        output_bytes_scope="tree before current manifest serialization")


def _output(path, purpose):
    root = Path(path).absolute()
    if purpose == "research":
        require(RESEARCH_ROOT.is_dir() and root.is_relative_to(RESEARCH_ROOT),
            "research outputs require the mounted external research root")
    require(not root.exists(), "output directory already exists")
    root.mkdir(parents=True)
    return root


def _control_rows(document):
    rows = tuple(row for row in document["states"] if row["arm"] == "borrowing")
    require(len(rows) == 10 and [(row["component"], row["season"]) for row in rows]
        == [(component, season) for component in ("volume", "shape") for season in SEASONS],
        "context controls require the ten ordered frozen borrowing states")
    return rows


def prepare(source_result, fixture, output):
    from hockey_stats.attribution_context import (
        BASIS_COLUMNS, prepare_context_source,
        context_training, context_training_arrays, context_training_row,
        context_population_arrays, context_population_row, context_game_moments,
    )
    from hockey_stats.attribution_simulation import shape_regions
    from hockey_stats.shot_origins import grid

    started, process_started = time.monotonic(), time.process_time()
    purpose = "fixture_exercise" if fixture else "research"
    source, metadata = (read_context_fixture(fixture) if fixture
        else read_context_source(_ref(source_result)))
    require(source.seasons == SEASONS, "context preparation requires five chronological seasons")
    populations = prepare_context_source(source, metadata)
    train, heldout = tuple(metadata["train_ids"]), tuple(metadata["assessment_ids"])
    require(train == tuple(sorted(set(train))) and heldout == tuple(sorted(set(heldout)))
        and not set(train).intersection(heldout)
        and tuple(sorted(train+heldout)) == source.grouped[-1].game_ids,
        "context preparation changed the frozen final-season partition")
    trainings = tuple(context_training(population, references,
        train if year == 4 else population.grouped.game_ids, source.basis)
        for year, (population, references) in enumerate(zip(populations, source.references, strict=True)))
    if purpose == "research":
        verify_context_control_training(trainings, metadata)
    assessment_hours = 0.
    for game in heldout:
        moment = context_game_moments(populations[-1], trainings[-1], game)
        assessment_hours += moment["directed_hours"]
    require(assessment_hours > 0, "context fixed assessment partition has no retained exposure")
    controls = _control_rows(metadata["controls_fit"])
    control_probes = tuple(probe for probe in metadata["controls_assessment"]["probes"]
        if probe["arm"] == "borrowing")
    require([(row["component"], row["season"]) for row in control_probes]
        == [(row["component"], row["season"]) for row in controls],
        "context control probes differ from the ten selected frozen states")
    root = _output(output, purpose)
    snapshot = root/"spec.md"
    snapshot.write_bytes(SPEC.read_bytes())
    arrays = dict(B=source.basis.B, p=source.basis.p, eigenvalues=source.basis.eigenvalues)
    years, population_rows = [], []
    for year, (training, population) in enumerate(zip(trainings, populations, strict=True)):
        training_prefix, population_prefix = f"training_{year}", f"population_{year}"
        arrays.update({training_prefix+"_"+name: value
            for name, value in context_training_arrays(training).items()})
        arrays.update({population_prefix+"_"+name: value
            for name, value in context_population_arrays(population).items()})
        years.append(context_training_row(training, training_prefix))
        population_rows.append(context_population_row(population, population_prefix))
    data = write_arrays(root, "moments.npz", arrays)
    regions, names = shape_regions()
    fields = dict(sources=source.source_identity, source_result=_ref(source_result) if source_result else None,
        fixture=_ref(fixture) if fixture else None, correction=metadata["correction_reference"],
        controls=dict(fit=metadata["controls_fit_reference"], assessment=metadata["controls_assessment_reference"]),
        control_states=controls, control_probes=control_probes, seasons=SEASONS, years=years,
        populations=population_rows, basis_sha256=source.basis.sha256,
        training_sha256=ordered_array_digest({key: value for key, value in arrays.items() if key.startswith("training_")}),
        moments_sha256=ordered_array_digest(arrays), inventory=[dict(row,
            partition="assessment" if row["game_id"] in heldout else "training") for row in metadata["inventory"]],
        train_ids=train, assessment_ids=heldout, months=metadata["months"],
        axes=dict(basis_columns=BASIS_COLUMNS, native_coordinates=grid()[0].tolist(),
            regions=names, region_shape=list(regions.shape), player_roles=["offense", "defense"]),
        coverage=dict(inventory_games=len(source.grouped[-1].game_ids), training_games=len(train),
            assessment_games=len(heldout), training_directed_hours=trainings[-1].directed_hours,
            assessment_directed_hours=assessment_hours,
            zero_time_game_ids=[game for game, hours in zip(source.grouped[-1].game_ids,
                source.grouped[-1].stratum_e.sum(axis=1), strict=True) if hours == 0],
            source_annual=source.annual[-1]["coverage"]),
        expected_states=20, expected_new_states=10, expected_reused_states=10, expected_probes=20, **data)
    protocol = artifact("attribution_context_protocol", purpose, dict(spec_snapshot=_ref(snapshot)),
        schema_version=1, rules=RULES, **fields, resources=_cost(started, process_started, root))
    write_json(root/"protocol.json", json_values(protocol))
    prepared = artifact("attribution_context_prepared", purpose,
        dict(protocol=_ref(root/"protocol.json"), moments=data["arrays"]), schema_version=1,
        protocol=_ref(root/"protocol.json"), **fields, resources=_cost(started, process_started, root))
    write_json(root/"prepared.json", json_values(prepared))
    return _ref(root/"prepared.json")


def read_prepared(path):
    from hockey_stats.attribution_context import (
        BASIS_COLUMNS, decode_context_training, decode_context_population,
    )
    from hockey_stats.attribution_simulation import shape_regions
    from hockey_stats.shot_origins import grid

    reference = _ref(path)
    document = read_json(Path(path))
    protocol = read_json(linked_path(document["protocol"]))
    require(document["kind"] == "attribution_context_prepared" and document["schema_version"] == 1
        and document["purpose"] in ("research", "fixture_exercise")
        and protocol["kind"] == "attribution_context_protocol" and protocol["schema_version"] == 1
        and protocol["purpose"] == document["purpose"] and protocol["rules"] == json_values(RULES),
        "context preparation or frozen protocol identity differs")
    if document["purpose"] == "research":
        clean_implementation(document["implementation"])
        clean_implementation(protocol["implementation"])
    linked_path(protocol["consumed"]["spec_snapshot"])
    for value in document["controls"].values(): linked_path(value)
    linked_path(document["correction"])
    excluded = {"kind", "implementation", "consumed", "resources", "protocol", "rules"}
    require({key: value for key, value in document.items() if key not in excluded}
        == {key: value for key, value in protocol.items() if key not in excluded},
        "context saved protocol/preparation bindings differ")
    require(tuple(document["seasons"]) == SEASONS
        and [row["season"] for row in document["years"]] == list(SEASONS)
        and [row["season"] for row in document["populations"]] == list(SEASONS)
        and document["expected_states"] == 20 and document["expected_new_states"] == 10
        and document["expected_reused_states"] == 10 and document["expected_probes"] == 20,
        "context saved annual or state inventory differs")
    arrays = load_arrays(document)
    require(ordered_array_digest(arrays) == document["moments_sha256"]
        and ordered_array_digest({key: value for key, value in arrays.items() if key.startswith("training_")})
            == document["training_sha256"], "context saved sufficient statistics differ")
    basis = decode_shape_basis({key: arrays[key] for key in ("B", "p", "eigenvalues")},
        basis_sha256=document["basis_sha256"])
    regions, names = shape_regions()
    require(document["axes"] == json_values(dict(basis_columns=BASIS_COLUMNS,
        native_coordinates=grid()[0].tolist(), regions=names, region_shape=list(regions.shape),
        player_roles=["offense", "defense"])), "context saved native, regional or temporal axes differ")
    def values(prefix):
        return {key[len(prefix)+1:]: value for key, value in arrays.items() if key.startswith(prefix+"_")}
    trainings = tuple(decode_context_training(row, values(row["prefix"]), basis) for row in document["years"])
    populations = tuple(decode_context_population(row, values(row["prefix"])) for row in document["populations"])
    expected_members = {"B", "p", "eigenvalues"}
    for row in document["years"]+document["populations"]:
        expected_members.update(row["prefix"]+"_"+name for name in values(row["prefix"]))
    require(set(arrays) == expected_members and len({row["prefix"] for row in
        document["years"]+document["populations"]}) == 10,
        "context saved archive prefixes overlap or contain unexpected arrays")
    require(tuple(document["train_ids"]) == trainings[-1].game_ids
        and tuple(sorted(document["train_ids"]+document["assessment_ids"])) == populations[-1].grouped.game_ids
        and not set(document["train_ids"]).intersection(document["assessment_ids"])
        and [row["game_id"] for row in document["inventory"]] == list(populations[-1].grouped.game_ids),
        "context saved inventory and fixed partition differ")
    _control_rows(dict(states=document["control_states"]))
    return Prepared(reference, document, trainings, populations, basis)


def fit(prepared, output):
    started, process_started = time.monotonic(), time.process_time()
    source = read_prepared(prepared)
    root = _output(output, source.document["purpose"])
    rows = []
    originals = {(row["component"], row["season"]): row
        for row in source.document["control_states"]}
    for arm in ("control", "candidate"):
        for component in ("volume", "shape"):
            previous, parent = None, None
            for year, training in enumerate(source.trainings):
                if arm == "control":
                    original = originals[component, SEASONS[year]]
                    require(original["parent"] == parent, "frozen control incoming parent differs")
                    state = decode_coefficient_state(original, component)
                    likelihood = (training.coarse_scalar_likelihood if component == "volume"
                        else training.coarse_training.likelihood)
                    (validate_scalar_coefficient_state if component == "volume"
                        else validate_shape_coefficient_state)(likelihood, previous, state)
                    row = dict(original, arm=arm, index=year, component=component,
                        execution="reused", original_record=original["record"],
                        likelihood_identity="coarse_energy" if component == "volume" else "coarse_shape_score",
                        objective_identity="gaussian_scalar_full_objective_v1" if component == "volume"
                            else OBJECTIVES["shape"])
                    if component == "volume":
                        row["score_equivalence"] = scalar_score_control_equivalence(likelihood, previous, state)
                else:
                    likelihood = training.scalar_likelihood if component == "volume" else training.likelihood
                    print(f"fitting {likelihood.season} {component} {arm}", file=sys.stderr, flush=True)
                    state = (fit_scalar_score_coefficients if component == "volume"
                        else fit_shape_coefficients)(likelihood, previous)
                    (validate_scalar_score_coefficient_state if component == "volume"
                        else validate_shape_coefficient_state)(likelihood, previous, state)
                    data = write_arrays(root, f"{component}-state-{year}.npz",
                        {name: getattr(state, name) for name in STATE_ARRAYS[component]})
                    binding = dict(prepared=source.reference, season=likelihood.season, component=component,
                        training_sha256=source.document["training_sha256"])
                    row = coefficient_state_row(state, year, arm, parent, binding, data, component)
                    row.update(component=component, execution="new", objective_identity=OBJECTIVES[component],
                        likelihood_identity="temporal_scalar_score" if component == "volume" else "temporal_shape_score")
                    write_json(root/f"{component}-state-{year}.json", json_values(row))
                    row["record"] = _ref(root/f"{component}-state-{year}.json")
                rows.append(row)
                previous, parent = state, row["record"]
    document = artifact("attribution_context_fit", source.document["purpose"],
        dict(prepared=source.reference, protocol=source.document["protocol"]), schema_version=1,
        prepared=source.reference, protocol=source.document["protocol"], execution_status="complete",
        states=rows, state_count=20, new_state_count=10, reused_state_count=10,
        scale_objective_evaluations=sum(len(row["scale"]["curve"]) for row in rows if row["execution"] == "new"),
        resources=_cost(started, process_started, root))
    write_json(root/"fit.json", json_values(document))
    return _ref(root/"fit.json")


def read_fit(source, path):
    reference = _ref(path)
    document = read_json(Path(path))
    require(document["kind"] == "attribution_context_fit" and document["schema_version"] == 1
        and document["purpose"] == source.document["purpose"] and document["prepared"] == source.reference
        and document["protocol"] == source.document["protocol"] and document["execution_status"] == "complete"
        and document["state_count"] == len(document["states"]) == 20
        and document["new_state_count"] == document["reused_state_count"] == 10,
        "context fit inventory or preparation binding differs")
    if document["purpose"] == "research":
        clean_implementation(document["implementation"])
    expected = [(arm, component, season) for arm in ("control", "candidate")
        for component in ("volume", "shape") for season in SEASONS]
    require([(row["arm"], row["component"], row["season"]) for row in document["states"]] == expected,
        "context fit ordered arm/component/season axes differ")
    originals = {(row["component"], row["season"]): row for row in source.document["control_states"]}
    states = {}
    for arm in ("control", "candidate"):
        for component in ("volume", "shape"):
            previous, parent = None, None
            for year, training in enumerate(source.trainings):
                row = document["states"][expected.index((arm, component, SEASONS[year]))]
                require(row["index"] == year and row["parent"] == parent
                    and row["execution"] == ("reused" if arm == "control" else "new"),
                    "context component incoming parent or execution identity differs")
                record = read_coefficient_record(row["record"])
                if arm == "control":
                    original = originals[component, SEASONS[year]]
                    require(row["record"] == row["original_record"] == original["record"]
                        and all(row[key] == value for key, value in original.items() if key not in ("arm", "index"))
                        and record == read_coefficient_record(original["record"]),
                        "reused control changed original state, likelihood or artifact identity")
                    likelihood = (training.coarse_scalar_likelihood if component == "volume"
                        else training.coarse_training.likelihood)
                else:
                    require(record == {key: value for key, value in row.items() if key != "record"}
                        and row["objective_identity"] == OBJECTIVES[component]
                        and row["likelihood"] == dict(prepared=source.reference, season=SEASONS[year],
                            component=component, training_sha256=source.document["training_sha256"]),
                        "new context state record or training identity differs")
                    likelihood = training.scalar_likelihood if component == "volume" else training.likelihood
                state = decode_coefficient_state(row, component)
                validator = (validate_scalar_score_coefficient_state if arm == "candidate"
                    else validate_scalar_coefficient_state) if component == "volume" else validate_shape_coefficient_state
                validator(likelihood, previous, state)
                states[arm, component, SEASONS[year]] = state
                previous, parent = state, row["record"]
    require(document["scale_objective_evaluations"] == sum(len(row["scale"]["curve"])
        for row in document["states"] if row["execution"] == "new"),
        "new context scale-evaluation inventory differs")
    return reference, document, states


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    preparation = sub.add_parser("prepare")
    inputs = preparation.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--source-result"); inputs.add_argument("--fixture")
    preparation.add_argument("--output", required=True)
    fitting = sub.add_parser("fit")
    fitting.add_argument("--prepared", required=True); fitting.add_argument("--output", required=True)
    assessment = sub.add_parser("assess")
    assessment.add_argument("--prepared", required=True); assessment.add_argument("--fit", required=True)
    assessment.add_argument("--output", required=True)
    reporting = sub.add_parser("report")
    reporting.add_argument("--assessment", required=True); reporting.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(args.source_result, args.fixture, args.output)
        elif args.command == "fit":
            result = fit(args.prepared, args.output)
        elif args.command == "assess":
            from attribution_context_assessment import assess
            result = assess(args.prepared, args.fit, args.output)
        else:
            from attribution_context_report import report
            result = report(args.assessment, args.output)
    except (InputContractError, OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
