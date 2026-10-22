"""04n's fixed complete recorded-rate comparison."""

import argparse
from dataclasses import dataclass
from itertools import product
import json
import os
from pathlib import Path
import sys
import time

for _thread in (
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OMP_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ[_thread] = "1"

import numpy as np

from hockey_stats.artifacts import (
    artifact,
    clean_implementation,
    json_values,
    linked_path,
    load_arrays,
    ordered_array_digest,
    require,
    resources,
    write_arrays,
    write_json,
)
from hockey_stats.attribution import (
    ShapeCoefficientLikelihood,
    ScalarCoefficientLikelihood,
    decode_shape_basis,
    fit_shape_coefficients,
    fit_scalar_coefficients,
    validate_shape_coefficient_state,
    validate_scalar_coefficient_state,
    bounded_shape_coefficient_probe,
    bounded_scalar_coefficient_probe,
    validate_shape_coefficient_probe,
)
from hockey_stats.attribution_data import (
    EmpiricalTraining,
    complete_training,
    read_complete_source,
    read_complete_fixture,
    coefficient_state_row,
    decode_coefficient_state,
    read_coefficient_chain,
    exact_shape_reuse_proofs,
    empirical_game_moments,
    iter_complete_rows,
    reconcile_complete_rows,
    read_complete_fixture_controls,
    read_coefficient_record,
    complete_grouped,
    verify_grouped_population,
)
from hockey_stats.attribution_prediction import (
    empirical_prediction,
    complete_prediction,
    prediction_row_batches,
    complete_rate_diagnostics,
)
from hockey_stats.attribution_simulation import shape_regions
from hockey_stats.captures import InputContractError
from hockey_stats.chance_cli import identity, read_json
from hockey_stats.shot_origins import grid

SPEC = Path(__file__).resolve().parents[2] / "docs/specs/04n-attribution-follow-up.md"
RESEARCH_ROOT = Path("/Volumes/Expansion/hockey-stats/runs")
TRAINING_ARRAYS = (
    "H",
    "Q",
    "u",
    "xbar",
    "nbar",
    "player_exposure",
    "response_counts",
    "scalar_score",
    "scalar_energy",
)
STATE_ARRAYS = dict(
    shape=("Theta", "V", "uncentered_Theta", "centering_shift", "u"),
    volume=("beta", "V", "uncentered_beta", "centering_shift", "u"),
)
MAIN_VARIANT_COMPONENTS = (
    ("volume", "borrowing"),
    ("shape", "borrowing"),
    ("volume", "independent"),
    ("shape", "independent"),
)
RULES = dict(
    seed=404130,
    draws=2000,
    bit_generator="PCG64",
    schemes=["games", "calendar_7_day", "calendar_14_day"],
    arms=["borrowing", "independent", "context"],
    components=["volume", "shape"],
    states=dict(selected=12, new=9, reused=3),
    variants=dict(
        main_bit_order=[
            dict(component=component, arm=arm)
            for component, arm in MAIN_VARIANT_COMPONENTS
        ],
        source_only_bit_order=["corrected borrowing shape", "original borrowing shape"],
        bit_meanings={"0": "primary", "1": "bounded probe"},
        ordinal_origin=0,
        order="lexicographic binary bits; all-zero combination is named primary",
        main_count=16,
        source_only_count=4,
    ),
    probes=dict(
        new=9,
        reused=3,
        source_control=1,
        xatol=1e-6,
        maxiter=80,
        equation_residual_max=1e-8,
        current_movement_fraction=1e-4,
    ),
    scale_grid=np.arange(-8.0, 0.1, 0.5).tolist(),
    refinement=dict(xatol=1e-4, maxiter=40),
    partition="exact frozen 04m inventory; no redraw",
    training="selected raw counted moments; directed hours",
    formulas=dict(
        scalar_score="(K-C.T@(N/E))@1",
        scalar_energy="(sum(Q_t)-sum((N@1)**2/E))/r",
        shape_score="(T-(T@1)*p.T)@B",
        complete_prediction="v*p.T+h",
        complete_loss="raw N,K; paired grouped contraction",
        normalizer="12*directed_hours",
    ),
    intervals="linear two-sided 95% percentile; fitted histories, split, selected scales and population fixed",
    nomination=None,
    admission="not_admitted",
    handoff=None,
)
LIMITS = [
    "joint lineup prediction of recorded locatable unblocked rates; not individual ability or chance value",
    "one frozen partition of research-exposed seasons; not untouched confirmation or a pregame forecast",
    "intervals condition on fits, scales, split and population; no empirical player uncertainty claim",
    "signed effects may be negative; negative complete predictions are not event intensities; no clipping",
    "paired response moments establish differences, not absolute regional mse or rmse",
    "source-only sensitivity concerns shape; complete volume correction sensitivity was not fitted",
    "limited context, relative-rate carry and forty-mode geometry remain assumptions; no ability admission",
]


@dataclass(frozen=True)
class Prepared:
    reference: dict
    document: dict
    trainings: tuple
    scalar_likelihoods: tuple
    basis: object


def _ref(path):
    return identity(Path(path).absolute())


def _cost(started, process_started, root):
    return dict(
        **resources(started),
        process_seconds=time.process_time() - process_started,
        output_bytes=sum(
            path.stat().st_size for path in root.rglob("*") if path.is_file()
        ),
        output_bytes_scope="tree before current manifest serialization",
    )


def _output(path, purpose):
    root = Path(path).absolute()
    if purpose == "research":
        require(
            RESEARCH_ROOT.is_dir() and root.is_relative_to(RESEARCH_ROOT),
            "research outputs require the mounted external research root",
        )
    require(not root.exists(), "output directory already exists")
    root.mkdir(parents=True)
    return root


def _source(source_result, source_audit, fixture):
    if fixture:
        return read_complete_fixture(fixture)
    require(
        source_result is not None and source_audit is not None,
        "research preparation requires both source-result and accepted source-audit",
    )
    return read_complete_source(_ref(source_result), _ref(source_audit))


def _controls(original, metadata, fixture):
    if fixture:
        document, reference = read_complete_fixture_controls(fixture, original)
        return document, document["probes"], dict(controls=reference)
    return (
        metadata["fit"],
        metadata["assessment"]["probes"],
        dict(
            fit=metadata["fit_ref"],
            assessment=metadata["assessment_ref"],
            prepared=metadata["prepared_ref"],
        ),
    )


def prepare(source_result, source_audit, fixture, output):
    started, process_started = time.monotonic(), time.process_time()
    purpose = "fixture_exercise" if fixture else "research"
    source, original, correction, metadata = _source(
        source_result, source_audit, fixture
    )
    train, heldout = tuple(metadata["train_ids"]), tuple(metadata["assessment_ids"])
    require(
        len(source.seasons) == 5
        and len(set(train) & set(heldout)) == 0
        and tuple(sorted(train + heldout)) == source.grouped[-1].game_ids,
        "complete rates require the exact complete five-year partition",
    )
    trainings = []
    scalars = []
    original_trainings = []
    for index, (grouped, refs) in enumerate(
        zip(source.grouped, source.references, strict=True)
    ):
        selected = train if index == 4 else grouped.game_ids
        shape, scalar = complete_training(grouped, refs, selected, source.basis)
        trainings.append(shape)
        scalars.append(scalar)
        original_trainings.append(
            complete_training(original.grouped[index], refs, selected, source.basis)[0]
        )
    controls, probes, control_refs = _controls(original, metadata, fixture)
    old_states = read_coefficient_chain(original_trainings, controls)
    proofs = exact_shape_reuse_proofs(original_trainings, trainings, controls)
    heldout_rows = [source.grouped[-1].game_ids.index(game) for game in heldout]
    require(
        float(source.grouped[-1].stratum_e[heldout_rows].sum()) > 0,
        "fixed assessment partition has zero retained exposure",
    )
    supported = set(trainings[-1].strata)
    for context, hours in zip(
        source.references[-1].strata,
        source.grouped[-1].stratum_e[heldout_rows].sum(axis=0),
        strict=True,
    ):
        require(
            hours == 0 or context in supported,
            "positive assessment context absent from training",
        )
    require(
        len(probes) == 6
        and all(
            row["verified"] and row["receipt"]["status"] == "verified" for row in probes
        ),
        "frozen original shape probe receipts are incomplete",
    )
    root = _output(output, purpose)
    snapshot = root / "spec.md"
    snapshot.write_bytes(SPEC.read_bytes())
    correction_archives = []
    for index in (2, 3):
        grouped = source.grouped[index]
        arrays = dict(stratum_e=grouped.stratum_e, Q_t=grouped.Q_t, Q_h=grouped.Q_h)
        for name in ("H_e", "T_raw", "stratum_x", "stratum_n"):
            matrix = getattr(grouped, name)
            arrays.update(
                {
                    name + suffix: getattr(matrix, attribute)
                    for suffix, attribute in (
                        ("_data", "data"),
                        ("_indices", "indices"),
                        ("_indptr", "indptr"),
                    )
                }
            )
        data = write_arrays(root, f"corrected-{source.seasons[index]}.npz", arrays)
        manifest = dict(
            season=source.seasons[index],
            players=source.references[index].player_ids,
            strata=source.references[index].strata,
            game_ids=grouped.game_ids,
            row_count=grouped.row_count,
            membership_signatures=grouped.membership_signatures,
            correction_identity=grouped.correction_identity,
            old_identity=source.annual[index]["grouped"],
            grouped=data["arrays"],
            grouped_shapes={name: list(value.shape) for name, value in arrays.items()},
            **data,
        )
        decoded = complete_grouped(manifest, linked_path(data["arrays"]))
        roundtrip = verify_grouped_population(grouped, decoded)
        manifest["roundtrip_max_absolute_errors"] = roundtrip
        correction_archives.append(manifest)
    correction["corrected_archives"] = correction_archives
    write_json(root / "correction.json", json_values(correction))
    arrays = dict(
        B=source.basis.B, p=source.basis.p, eigenvalues=source.basis.eigenvalues
    )
    years = []
    for index, (shape, scalar) in enumerate(zip(trainings, scalars, strict=True)):
        prefix = f"year_{index}"
        values = dict(
            H=shape.likelihood.H,
            Q=shape.likelihood.Q,
            u=shape.likelihood.u,
            xbar=shape.xbar,
            nbar=shape.nbar,
            player_exposure=shape.player_exposure,
            response_counts=shape.response_counts,
            scalar_score=scalar.score,
            scalar_energy=np.array(scalar.energy),
        )
        arrays.update({prefix + "_" + name: value for name, value in values.items()})
        years.append(
            dict(
                season=shape.likelihood.season,
                prefix=prefix,
                game_ids=shape.game_ids,
                source_player_ids=shape.source_player_ids,
                player_ids=shape.likelihood.player_ids,
                strata=shape.strata,
                source_strata=shape.source_strata,
                r=shape.likelihood.r,
                directed_hours=shape.directed_hours,
                training_attempts=float(shape.response_counts.sum()),
                source_identity=shape.source_identity,
                scalar_source_identity=scalar.source_identity,
                source_annual=source.annual[index],
            )
        )
    data = write_arrays(root, "training.npz", arrays)
    inventory = metadata.get(
        "inventory",
        [
            dict(
                game_id=game,
                date=source.game_dates[game],
                partition="assessment" if game in heldout else "training",
            )
            for game in source.grouped[-1].game_ids
        ],
    )
    fields = dict(
        sources=source.source_identity,
        source_result=_ref(source_result) if source_result else None,
        source_audit=_ref(source_audit) if source_audit else None,
        fixture=_ref(fixture) if fixture else None,
        correction=_ref(root / "correction.json"),
        seasons=source.seasons,
        years=years,
        basis_sha256=source.basis.sha256,
        training_sha256=ordered_array_digest(arrays),
        inventory=inventory,
        train_ids=train,
        assessment_ids=heldout,
        months=metadata.get("months", []),
        coverage=dict(
            inventory_games=len(inventory),
            training_games=len(train),
            assessment_games=len(heldout),
            training_directed_hours=trainings[-1].directed_hours,
            assessment_directed_hours=float(
                source.grouped[-1].stratum_e[heldout_rows].sum()
            ),
            zero_time_game_ids=[
                game
                for game, E in zip(
                    source.grouped[-1].game_ids,
                    source.grouped[-1].stratum_e,
                    strict=True,
                )
                if E.sum() == 0
            ],
            source_annual=source.annual[-1]["coverage"],
        ),
        reuse_proofs=proofs,
        controls=control_refs,
        original_shape_states=controls["states"],
        original_shape_probes=probes,
        expected_states=12,
        expected_new_states=9,
        expected_reused_states=3,
        expected_probes=13,
        **data,
    )
    protocol = artifact(
        "attribution_complete_protocol",
        purpose,
        dict(spec_snapshot=_ref(snapshot)),
        schema_version=1,
        rules=RULES,
        **fields,
        resources=_cost(started, process_started, root),
    )
    write_json(root / "protocol.json", json_values(protocol))
    prepared = artifact(
        "attribution_complete_prepared",
        purpose,
        dict(protocol=_ref(root / "protocol.json"), training=data["arrays"]),
        schema_version=1,
        protocol=_ref(root / "protocol.json"),
        **fields,
        resources=_cost(started, process_started, root),
    )
    write_json(root / "prepared.json", json_values(prepared))
    return _ref(root / "prepared.json")


def read_prepared(path):
    reference = _ref(path)
    document = read_json(Path(path))
    protocol = read_json(linked_path(document["protocol"]))
    require(
        document["kind"] == "attribution_complete_prepared"
        and document["schema_version"] == 1
        and document["purpose"] in ("research", "fixture_exercise")
        and protocol["kind"] == "attribution_complete_protocol"
        and protocol["schema_version"] == 1
        and protocol["rules"] == RULES
        and document["purpose"] == protocol["purpose"],
        "wrong complete-rate preparation or frozen protocol",
    )
    if document["purpose"] == "research":
        clean_implementation(document["implementation"])
        clean_implementation(protocol["implementation"])
    linked_path(protocol["consumed"]["spec_snapshot"])
    excluded = {"kind", "implementation", "consumed", "resources", "protocol", "rules"}
    require(
        {k: v for k, v in document.items() if k not in excluded}
        == {k: v for k, v in protocol.items() if k not in excluded},
        "saved preparation/protocol bindings differ",
    )
    correction = read_json(linked_path(document["correction"]))
    require(
        len(correction["rows"]) == 6 and correction["count_loss"] == 0,
        "saved correction inventory differs",
    )
    for archive in correction["corrected_archives"]:
        decoded = complete_grouped(archive, linked_path(archive["grouped"]))
        require(
            decoded.membership_signatures == tuple(archive["membership_signatures"])
            and archive["correction_identity"] is not None,
            "saved corrected moment support or correction identity differs",
        )
    arrays = load_arrays(document)
    require(
        ordered_array_digest(arrays) == document["training_sha256"],
        "saved training arrays differ",
    )
    basis = decode_shape_basis(
        {name: arrays[name] for name in ("B", "p", "eigenvalues")},
        basis_sha256=document["basis_sha256"],
    )
    trainings = []
    scalars = []
    for row in document["years"]:
        values = {name: arrays[row["prefix"] + "_" + name] for name in TRAINING_ARRAYS}
        shape = ShapeCoefficientLikelihood(
            row["season"],
            tuple(row["player_ids"]),
            values["H"],
            values["Q"],
            values["u"],
            row["r"],
            basis,
            row["source_identity"],
        )
        scalar = ScalarCoefficientLikelihood(
            row["season"],
            tuple(row["player_ids"]),
            values["H"],
            values["scalar_score"],
            float(values["scalar_energy"]),
            values["u"],
            row["r"],
            row["scalar_source_identity"],
        )
        trainings.append(
            EmpiricalTraining(
                shape,
                tuple(row["game_ids"]),
                tuple(row["source_player_ids"]),
                tuple(map(tuple, row["strata"])),
                tuple(map(tuple, row["source_strata"])),
                values["xbar"],
                values["nbar"],
                values["player_exposure"],
                row["directed_hours"],
                values["response_counts"],
                row["source_identity"],
            )
        )
        scalars.append(scalar)
    require(
        len(trainings) == 5
        and document["expected_states"] == 12
        and document["expected_probes"] == 13
        and len(document["reuse_proofs"]) == 3
        and len(document["original_shape_states"]) == 6,
        "complete preparation finite inventory differs",
    )
    return Prepared(reference, document, tuple(trainings), tuple(scalars), basis)


def fit(prepared, output):
    started, process_started = time.monotonic(), time.process_time()
    source = read_prepared(prepared)
    root = _output(output, source.document["purpose"])
    rows = []
    for component in ("volume", "shape"):
        previous = None
        parent = None
        for index in range(6):
            independent = index == 5
            year = min(index, 4)
            arm = "independent" if independent else "borrowing"
            likelihood = (
                source.scalar_likelihoods[year]
                if component == "volume"
                else source.trainings[year].likelihood
            )
            incoming = None if independent else previous
            reused = component == "shape" and index in (0, 1, 5)
            if reused:
                old = source.document["original_shape_states"][index]
                require(
                    old["parent"] == (None if independent else parent),
                    "selected unchanged state parent differs",
                )
                state = decode_coefficient_state(old)
                validate_shape_coefficient_state(likelihood, incoming, state)
                row = dict(
                    old,
                    component=component,
                    origin="reused",
                    original_record=old["record"],
                )
            else:
                print(
                    f"fitting {likelihood.season} {component} {arm}",
                    file=sys.stderr,
                    flush=True,
                )
                state = (
                    fit_scalar_coefficients
                    if component == "volume"
                    else fit_shape_coefficients
                )(likelihood, incoming)
                (
                    validate_scalar_coefficient_state
                    if component == "volume"
                    else validate_shape_coefficient_state
                )(likelihood, incoming, state)
                data = write_arrays(
                    root,
                    f"{component}-state-{index}.npz",
                    {name: getattr(state, name) for name in STATE_ARRAYS[component]},
                )
                binding = dict(
                    prepared=source.reference,
                    season=likelihood.season,
                    component=component,
                    training_sha256=source.document["training_sha256"],
                )
                row = coefficient_state_row(
                    state,
                    index,
                    arm,
                    None if independent else parent,
                    binding,
                    data,
                    component,
                )
                write_json(root / f"{component}-state-{index}.json", json_values(row))
                row.update(
                    record=_ref(root / f"{component}-state-{index}.json"),
                    component=component,
                    origin="new",
                )
            rows.append(row)
            previous, parent = state, row["record"]
    document = artifact(
        "attribution_complete_fit",
        source.document["purpose"],
        dict(prepared=source.reference, protocol=source.document["protocol"]),
        schema_version=1,
        prepared=source.reference,
        protocol=source.document["protocol"],
        execution_status="complete",
        states=rows,
        state_count=12,
        new_state_count=9,
        reused_state_count=3,
        scale_objective_evaluations=sum(
            len(row["scale"]["curve"]) for row in rows if row["origin"] == "new"
        ),
        resources=_cost(started, process_started, root),
    )
    write_json(root / "fit.json", json_values(document))
    return _ref(root / "fit.json")


def read_fit(source, path):
    reference = _ref(path)
    document = read_json(Path(path))
    require(
        document["kind"] == "attribution_complete_fit"
        and document["schema_version"] == 1
        and document["purpose"] == source.document["purpose"]
        and document["prepared"] == source.reference
        and document["protocol"] == source.document["protocol"]
        and document["execution_status"] == "complete"
        and document["state_count"] == len(document["states"]) == 12
        and document["new_state_count"] == 9
        and document["reused_state_count"] == 3,
        "complete fit is incomplete or preparation differs",
    )
    if document["purpose"] == "research":
        clean_implementation(document["implementation"])
    states = {}
    for component in ("volume", "shape"):
        selected = [row for row in document["states"] if row["component"] == component]
        require(len(selected) == 6, "component selected-state inventory differs")
        values = []
        for index, row in enumerate(selected):
            independent = index == 5
            year = min(index, 4)
            reused = component == "shape" and index in (0, 1, 5)
            likelihood = (
                source.scalar_likelihoods[year]
                if component == "volume"
                else source.trainings[year].likelihood
            )
            require(
                row["origin"] == ("reused" if reused else "new")
                and row["index"] == index
                and row["arm"] == ("independent" if independent else "borrowing")
                and row["parent"]
                == (
                    None if independent or index == 0 else selected[index - 1]["record"]
                ),
                "selected component identity or incoming parent differs",
            )
            record = read_coefficient_record(row["record"])
            ignore = {"record", "component", "origin", "original_record"}
            require(
                record == {k: v for k, v in row.items() if k not in ignore},
                "selected saved state record differs",
            )
            if reused:
                require(
                    row["original_record"]
                    == source.document["original_shape_states"][index]["record"]
                    and record
                    == {
                        k: v
                        for k, v in source.document["original_shape_states"][
                            index
                        ].items()
                        if k != "record"
                    },
                    "reused state changed original identity",
                )
            else:
                require(
                    row["likelihood"]
                    == dict(
                        prepared=source.reference,
                        season=likelihood.season,
                        component=component,
                        training_sha256=source.document["training_sha256"],
                    ),
                    "new selected state training binding differs",
                )
            state = decode_coefficient_state(row, component)
            (
                validate_scalar_coefficient_state
                if component == "volume"
                else validate_shape_coefficient_state
            )(likelihood, None if independent or index == 0 else values[-1], state)
            values.append(state)
        states[component] = tuple(values)
    require(
        document["scale_objective_evaluations"]
        == sum(
            len(row["scale"]["curve"])
            for row in document["states"]
            if row["origin"] == "new"
        ),
        "new scale-evaluation inventory differs",
    )
    return reference, document, states


def assess(prepared, fitted, output):
    from attribution_complete_assessment import assess_games

    started, process_started = time.monotonic(), time.process_time()
    source = read_prepared(prepared)
    document = source.document
    require(
        {
            row["game_id"]
            for row in document["inventory"]
            if row["partition"] == "assessment"
        }
        == set(document["assessment_ids"])
        and {
            row["game_id"]
            for row in document["inventory"]
            if row["partition"] == "training"
        }
        == set(document["train_ids"]),
        "saved inventory partition labels differ from frozen assessment/training ids",
    )
    fit_ref, fit_document, states = read_fit(source, fitted)
    corrected, original, correction, metadata = _source(
        document["source_result"]["path"] if document["source_result"] else None,
        document["source_audit"]["path"] if document["source_audit"] else None,
        document["fixture"]["path"] if document["fixture"] else None,
    )
    require(
        original.source_identity == document["sources"]
        and correction["rows"]
        == read_json(linked_path(document["correction"]))["rows"],
        "assessment original source or accepted correction differs",
    )
    root = _output(output, document["purpose"])
    probes = []
    alternatives = {}
    for component in ("volume", "shape"):
        for index, state in enumerate(states[component]):
            independent = index == 5
            year = min(index, 4)
            likelihood = (
                source.scalar_likelihoods[year]
                if component == "volume"
                else source.trainings[year].likelihood
            )
            previous = (
                None if independent or index == 0 else states[component][index - 1]
            )
            selected = next(
                row
                for row in fit_document["states"]
                if row["component"] == component and row["index"] == index
            )
            if selected["origin"] == "reused":
                frozen = document["original_shape_probes"][index]
                receipt = frozen["receipt"]
                alternative = decode_coefficient_state(frozen["alternative"])
                alternative_row = frozen["alternative"]
                validate_shape_coefficient_probe(
                    likelihood, previous, state, receipt, alternative
                )
            else:
                receipt, alternative = (
                    bounded_scalar_coefficient_probe
                    if component == "volume"
                    else bounded_shape_coefficient_probe
                )(likelihood, previous, state)
                data = write_arrays(
                    root,
                    f"{component}-probe-{index}.npz",
                    {
                        name: getattr(alternative, name)
                        for name in STATE_ARRAYS[component]
                    },
                )
                alternative_row = coefficient_state_row(
                    alternative,
                    index,
                    selected["arm"],
                    selected["parent"],
                    selected["likelihood"],
                    data,
                    component,
                )
            probes.append(
                dict(
                    component=component,
                    index=index,
                    season=state.season,
                    arm=selected["arm"],
                    origin=selected["origin"],
                    verified=receipt["status"] == "verified",
                    receipt=receipt,
                    alternative=alternative_row,
                )
            )
            if index in (4, 5):
                alternatives[component, selected["arm"]] = alternative
    original_final = decode_coefficient_state(document["original_shape_states"][4])
    original_probe = document["original_shape_probes"][4]
    original_alternative = decode_coefficient_state(original_probe["alternative"])
    # the original control conditions on its original incoming history, not the corrected history.
    original_trainings = [
        complete_training(
            grouped,
            refs,
            document["train_ids"] if index == 4 else grouped.game_ids,
            source.basis,
        )[0]
        for index, (grouped, refs) in enumerate(
            zip(original.grouped, original.references, strict=True)
        )
    ]
    original_states = read_coefficient_chain(
        original_trainings, dict(states=document["original_shape_states"])
    )
    validate_shape_coefficient_probe(
        original_trainings[-1].likelihood,
        original_states[3],
        original_final,
        original_probe["receipt"],
        original_alternative,
    )
    probes.append(
        dict(
            component="shape",
            index=4,
            season=original_final.season,
            arm="original_borrowing",
            origin="frozen_source_control",
            verified=original_probe["verified"],
            receipt=original_probe["receipt"],
            alternative=original_probe["alternative"],
        )
    )
    final = source.trainings[-1]
    ids = original.references[-1].player_ids
    predictions = {
        arm: complete_prediction(
            final, states["volume"][index], states["shape"][index], ids
        )
        for arm, index in (("borrowing", 4), ("independent", 5))
    }
    predictions["context"] = complete_prediction(final, None, None, ids)
    variants = {}
    keys = MAIN_VARIANT_COMPONENTS
    for bits in product((False, True), repeat=4):
        chosen = {
            key: alternatives[key]
            if bit
            else states[key[0]][4 if key[1] == "borrowing" else 5]
            for key, bit in zip(keys, bits, strict=True)
        }
        name = (
            "primary"
            if not any(bits)
            else "probe_" + "".join("1" if value else "0" for value in bits)
        )
        variants[name] = {
            arm: complete_prediction(
                final, chosen["volume", arm], chosen["shape", arm], ids
            )
            for arm in ("borrowing", "independent")
        }
        variants[name]["context"] = predictions["context"]
    source_variants = {}
    for corrected_probe, old_probe in product((False, True), repeat=2):
        name = (
            "primary"
            if not corrected_probe and not old_probe
            else f"probe_{int(corrected_probe)}{int(old_probe)}"
        )
        source_variants[name] = dict(
            corrected=empirical_prediction(
                final,
                alternatives["shape", "borrowing"]
                if corrected_probe
                else states["shape"][4],
                ids,
            ),
            original=empirical_prediction(
                original_trainings[-1],
                original_alternative if old_probe else original_final,
                ids,
            ),
        )
    earlier = set().union(
        *(training.likelihood.player_ids for training in source.trainings[:-1])
    )
    current = set(final.likelihood.player_ids)
    support = {
        player: dict(
            group="current_training"
            if player in current
            else "carried_only"
            if player in earlier
            else "new_to_fit",
            first_in_corpus_final=player not in earlier,
        )
        for player in ids
    }
    inventory = {row["game_id"]: row for row in document["inventory"]}

    def games():
        for game in original.grouped[-1].game_ids:
            yield dict(
                empirical_game_moments(
                    original.grouped[-1], original.references[-1], game
                ),
                **inventory[game],
                coverage=original.game_coverage[game],
                source_identity=original.source_identity,
            )

    regions, names = shape_regions()
    payload, native = assess_games(
        games(),
        predictions,
        source.basis.p,
        regions,
        names,
        support,
        variants,
        probes,
        source_predictions=source_variants,
    )
    reconciliation = {}
    rows = reconcile_complete_rows(
        iter_complete_rows(original, metadata, tuple(document["assessment_ids"])),
        original.grouped[-1],
        original.references[-1],
        tuple(document["assessment_ids"]),
        reconciliation,
    )
    prediction_receipt = {}
    rates = complete_rate_diagnostics(
        prediction_row_batches(rows, predictions, receipt=prediction_receipt),
        source.basis.p,
        regions,
        names,
        final.likelihood.r,
    )
    require(
        reconciliation.get("status") == "verified",
        "held-out row reconciliation did not finish",
    )
    data = write_arrays(root, "native-diagnostics.npz", native)
    payload.update(
        prepared=source.reference,
        protocol=document["protocol"],
        fit=fit_ref,
        probes=probes,
        partition=document["inventory"],
        months=document["months"],
        sources=document["sources"],
        years=document["years"],
        limits=LIMITS,
        rate_rows=rates,
        source_correction=read_json(linked_path(document["correction"])),
        inventory=dict(
            states=12,
            new_states=9,
            reused_states=3,
            probes=13,
            new_probes=9,
            reused_probes=3,
            source_control_probes=1,
            main_variants=16,
            source_only_variants=4,
            variant_contract=RULES["variants"],
            main_variant_ordinals=[
                dict(
                    ordinal=index,
                    variant=name,
                    bits="0000" if name == "primary" else name.removeprefix("probe_"),
                )
                for index, name in enumerate(variants)
            ],
            source_only_variant_ordinals=[
                dict(
                    ordinal=index,
                    variant=name,
                    bits="00" if name == "primary" else name.removeprefix("probe_"),
                )
                for index, name in enumerate(source_variants)
            ],
            games=len(inventory),
            assessment_games=len(document["assessment_ids"]),
        ),
        preparation_resources=document["resources"],
        fit_resources=fit_document["resources"],
        state_resources=[
            row["diagnostics"]["resources"] for row in fit_document["states"]
        ],
    )
    payload["coverage"].update(
        source_annual=document["coverage"]["source_annual"],
        zero_time_game_ids=document["coverage"]["zero_time_game_ids"],
    )
    payload["verification"] = dict(
        source_chain=(
            "accepted final 02d correction and frozen 04m references verified"
            if document["purpose"] == "research"
            else "explicit synthetic counted fixture correction and original controls verified"
        ),
        reuse_proofs=document["reuse_proofs"],
        heldout_rows=reconciliation,
        physical_prediction=prediction_receipt,
        state_count=12,
        new_states=9,
        reused_states=3,
        probe_count=13,
        primary_fit_preserved=fit_ref,
        conditional_probe_scope="fixed incoming primary histories; sixteen main and four source-only combinations",
    )
    payload["native_axes"].update(
        coordinates=grid()[0].tolist(),
        reference_p=source.basis.p.tolist(),
        basis_sha256=source.basis.sha256,
        units="recorded unblocked attempts/60",
    )
    payload["native_diagnostics"] = dict(**data, axes=payload["native_axes"])
    result = artifact(
        "attribution_complete_assessment",
        document["purpose"],
        dict(prepared=source.reference, protocol=document["protocol"], fit=fit_ref),
        schema_version=1,
        execution_status="complete",
        **payload,
        **data,
        resources=_cost(started, process_started, root),
    )
    write_json(root / "assessment.json", json_values(result))
    return _ref(root / "assessment.json")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    preparation = sub.add_parser("prepare")
    inputs = preparation.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--source-result")
    inputs.add_argument("--fixture")
    preparation.add_argument("--source-audit")
    preparation.add_argument("--output", required=True)
    fitting = sub.add_parser("fit")
    fitting.add_argument("--prepared", required=True)
    fitting.add_argument("--output", required=True)
    assessment = sub.add_parser("assess")
    assessment.add_argument("--prepared", required=True)
    assessment.add_argument("--fit", required=True)
    assessment.add_argument("--output", required=True)
    reporting = sub.add_parser("report")
    reporting.add_argument("--assessment", required=True)
    reporting.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            require(
                not args.fixture or args.source_audit is None,
                "fixture replaces both research source arguments",
            )
            result = prepare(
                args.source_result, args.source_audit, args.fixture, args.output
            )
        elif args.command == "fit":
            result = fit(args.prepared, args.output)
        elif args.command == "assess":
            result = assess(args.prepared, args.fit, args.output)
        else:
            from attribution_complete_report import report

            result = report(args.assessment, args.output)
    except (InputContractError, OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
