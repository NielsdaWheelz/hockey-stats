"""one joint provisional reference and exact linear response transports.

native chance components own predictor meaning and annual state selection.
the reference owns event membership and weights; neither changes fitted maps.
"""

from collections import Counter
from dataclasses import replace
import hashlib
from itertools import groupby
import json
from pathlib import Path
import time

import numpy as np
from scipy.special import expit, log_expit

from .artifacts import clean_implementation, implementation, linked_path, require, resources, rows, write_json
from .attribution import AnnualState
from .attribution_data import ArtifactReference
from .chance import TYPES, component_prediction_context, component_reference_logits
from .chance_cli import identity, output_path, read_json
from .chance_components import read_completed_component
from .chance_data import prepare_game_attempts
from .shot_origins import grid


COMPONENTS = {
    "direct": ("unblocked_conversion", "87a0f4744dcf1756916464eafe55d2c7a1bfc15e49b46d4968800f7b0a9fbf8d"),
    "unblocked_on_net": ("unblocked_on_net", "3b61b35128fb375f5aedb2853f95ea23558848f08f70fd20e8ef281279e627e7"),
    "on_net_conversion": ("on_net_conversion", "f15b55183ab6474e15bdcfd7a5478fc25b8b5c1febe3c292d52bcefc2a27d926"),
}


def valuation_surfaces(components: dict[str, dict], joint: list[dict], weights: np.ndarray) -> dict[str, np.ndarray]:
    """average direct p and the joint q*g product under the same empirical law."""
    weights = np.asarray(weights, dtype=float)
    require(set(components) == set(COMPONENTS) and len(joint) > 0
            and weights.shape == (len(joint),) and np.isfinite(weights).all()
            and np.all(weights > 0) and np.isclose(weights.sum(), 1, rtol=0, atol=1e-12),
            "valuation requires three components and positive unit-sum joint weights")
    cells = np.arange(len(grid()[0]))
    contexts = {name: component_prediction_context(component, feature_games={}, feature_player_games={})
                for name, component in components.items()}
    direct, product = np.zeros(len(cells)), np.zeros(len(cells))
    for start in range(0, len(joint), 256):
        stop = start + 256
        logits = {name: component_reference_logits(component, joint[start:stop], cells, contexts[name])
                  for name, component in components.items()}
        direct += weights[start:stop] @ expit(logits["direct"])
        product += weights[start:stop] @ np.exp(log_expit(logits["unblocked_on_net"])
                                               + log_expit(logits["on_net_conversion"]))
    require(all(np.isfinite(value).all() and np.all((value >= 0) & (value <= 1))
                for value in (direct, product)), "nonfinite or invalid valuation surface")
    return dict(direct=direct, product=product)


def prepare_reference(prepared_path: Path | str, out: Path | str) -> ArtifactReference:
    """freeze source-keyed common membership, joint weights and native-cell values."""
    started = time.monotonic()
    path = Path(prepared_path).resolve(strict=True)
    prepared = read_json(path)
    require(type(prepared["schema_version"]) is int and prepared["schema_version"] == 1
            and prepared["kind"] == "attribution_prepared", "expected attribution prepared manifest")
    protocol_path = linked_path(prepared["protocol"])
    protocol = read_json(protocol_path)
    require(protocol["kind"] == "attribution_protocol" and protocol["purpose"] == prepared["purpose"]
            and protocol["target_season"] == prepared["target_season"], "reference protocol mismatch")
    bindings = protocol["components"]
    require(set(bindings) == set(COMPONENTS), "reference requires exactly the three frozen components")
    components, component_metadata = {}, {}
    target = prepared["target_season"]
    reason = None
    centers, _ = grid()
    for name, (quantity, digest) in COMPONENTS.items():
        binding = bindings[name]
        require(set(binding) == {"completion", "source_result"}
                and binding["completion"]["sha256"] == digest, "reference component differs from fixed transfer fit")
        result = read_json(linked_path(binding["source_result"]))
        direct = name == "direct"
        expected_kind = "chance_history_result" if direct else "chance_decomposition_result"
        require(result["artifact_kind"] == expected_kind and result["execution_status"] == "complete",
                "component source result is not complete")
        source = result["cells"]["season_transfer"]["short" if direct else name]
        completion, component, _ = read_completed_component(binding["completion"], quantity=quantity, purpose="research")
        design = component["layout"]["design"]
        design_sha256 = hashlib.sha256(json.dumps(design, sort_keys=True, separators=(",", ":"),
                                                   allow_nan=False).encode()).hexdigest()
        require(source["status"] == "complete" and source["fit"] == binding["completion"]
                and source["component"] == completion["component"]
                and source["training_cohort" if direct else "cohort"] == completion["training_cohort"]
                and source["design"]["sha256"] == design_sha256, "source result does not bind the fitted component")
        if direct:
            require(source["config"] == completion["config"], "source result config differs from fitted component")
        if (component["grid"]["centers"] != centers.tolist()
                or set(design["families"]) - {"game_additive", "recent_additive", "recent_interactions"}):
            reason = "component_predictors_incompatible_with_common_core_reference"
        if target < component["seasons"][0]:
            reason = "reference_season_precedes_component_history"
        basis = ("unavailable" if target < component["seasons"][0] else "carried_forward"
                 if target > component["seasons"][-1] else "fitted"
                 if target in component["training_seasons"] else "unobserved")
        component_metadata[name] = dict(quantity=quantity, component=completion["component"],
            config=completion["config"], cohort=completion["training_cohort"],
            design_sha256=design_sha256,
            families=design["families"], reference_season=target, season_basis=basis,
            state_season=None if basis == "unavailable" else min(target, component["seasons"][-1]))
        components[name] = component
    output = output_path(str(out), [str(path.parent), str(protocol_path.parent)] +
                         [str(Path(value["completion"]["path"]).parent) for value in bindings.values()])
    require(output.is_relative_to(Path(protocol["output_root"]).resolve()), "reference differs from frozen output root")
    current_implementation = implementation()
    if prepared["purpose"] == "research":
        clean_implementation(current_implementation)
        require(current_implementation == protocol["implementation"], "reference implementation differs from frozen protocol")
        require(output.is_relative_to(Path("/Volumes/Expansion/hockey-stats")), "research reference must remain external")
    event_path = linked_path(prepared["ledgers"]["events"])
    game_inputs = {value["path"]: {key: value[key] for key in ("path", "sha256")}
                   for value in prepared["inputs"] if value["kind"] == "game"}
    sources = {value["game_id"]: game_inputs[value["source"]]
               for value in rows(linked_path(prepared["ledgers"]["coverage"]))
               if value["season"] == target and value["populations"] is not None}
    annual = [value for value in prepared["annual"]
              if value["population"] == "unblocked_spatial" and value["season"] == target]
    require(len(annual) == 1, "final spatial population is missing")
    annual = annual[0]
    output.mkdir()
    event_output, joint_output = output / "events.jsonl", output / "joint.jsonl"
    tuples, tuple_indices, frequencies = [], {}, []
    support = np.zeros((len(centers), len(TYPES)), dtype=np.int64)
    exclusions, source_types = Counter(), Counter()
    with event_output.open("x") as destination:
        selected = (event for event in rows(event_path) if event["season"] == target)
        for game_id, game_events in groupby(selected, key=lambda event: event["game_id"]):
            source_path = linked_path(sources[game_id])
            envelope = read_json(source_path)
            require(envelope["interpreted"]["game"]["game_id"] == game_id
                    and envelope["interpreted"]["game"]["season"] == target,
                    "reference source identity differs from prepared coverage")
            native = {attempt["source_index"]: attempt for attempt in
                      prepare_game_attempts(envelope, source_path, envelope["interpreted"]["game"])["attempts"]}
            for event in game_events:
                if event["type"] == "blocked-shot":
                    continue
                attempt = native[event["source_index"]]
                reasons = []
                if event["unblocked_spatial"] != "retained":
                    reasons.append("outside_admitted_spatial_population")
                if attempt["status"] != "eligible":
                    reasons.append("native_core_ineligible")
                missing_actors = [dict(component=name, actor=actor, player_id=attempt[actor + "_id"])
                    for name, component in components.items() for actor in ("shooter", "goalie")
                    if attempt[actor + "_id"] not in component["layout"][actor + "s"]]
                if missing_actors:
                    reasons.append("actor_absent_from_component")
                index = None
                if not reasons:
                    predictor = {key: attempt[key] for key in
                                 ("season", "model_shot_type", "role", "shooter_id", "goalie_id", "context")}
                    predictor["previous_event"] = {"status": attempt["previous_event"]["status"]}
                    key = json.dumps(predictor, sort_keys=True, separators=(",", ":"))
                    if key not in tuple_indices:
                        tuple_indices[key] = len(tuples)
                        tuples.append(predictor)
                        frequencies.append(0)
                    index = tuple_indices[key]
                    frequencies[index] += 1
                    support[event["cell_id"], TYPES.index(attempt["model_shot_type"])] += 1
                    source_types[attempt["source_event"]["type_key"]] += 1
                else:
                    exclusions.update(reasons)
                row = dict(game_id=game_id, source_index=event["source_index"],
                    status="excluded" if reasons else "included", reasons=reasons, joint_index=index,
                    spatial_disposition=event["unblocked_spatial"], native_status=attempt["status"],
                    native_reasons=attempt["reasons"], missing_actors=missing_actors)
                destination.write(json.dumps(row, allow_nan=False) + "\n")
    total = sum(frequencies)
    weights = np.asarray(frequencies, dtype=float) / total if total else np.empty(0)
    with joint_output.open("x") as destination:
        for index, (predictor, frequency, weight) in enumerate(zip(tuples, frequencies, weights, strict=True)):
            destination.write(json.dumps(dict(joint_index=index, predictors=predictor,
                frequency=frequency, weight=float(weight)), allow_nan=False) + "\n")
    if not total:
        reason = "empty_common_reference"
    if annual["status"] != "prepared":
        reason = "final_spatial_population_unavailable"
    arrays_reference, shapes, baselines = None, {}, None
    if reason is None:
        surfaces = valuation_surfaces(components, tuples, weights)
        with np.load(linked_path(annual["arrays"]), allow_pickle=False) as arrays:
            counts = arrays["response_counts"]
        baselines = {name: float(annual["r"] * (counts / counts.sum()) @ surface)
                     for name, surface in surfaces.items()}
        values = dict(**surfaces, cell_type_counts=support,
                      unseen_cell_type_reference_mass=(support == 0) @ (support.sum(axis=0) / total))
        arrays_path = output / "surfaces.npz"
        with arrays_path.open("xb") as destination:
            np.savez(destination, **values)
        arrays_reference = identity(arrays_path)
        shapes = {name: list(value.shape) for name, value in values.items()}
    document = dict(schema_version=1, kind="attribution_reference", purpose=prepared["purpose"],
        implementation=current_implementation, protocol=prepared["protocol"], prepared=identity(path),
        population="unblocked_spatial", population_id=prepared["population_ids"]["unblocked_spatial"],
        season=target, components=bindings, component_metadata=component_metadata,
        status="available" if reason is None else "unavailable", reason=reason,
        retained_events=total, joint_tuples=len(tuples), source_types=dict(source_types),
        exclusions=dict(exclusions), exclusion_accounting="overlapping reasons per excluded source event",
        support_population="common_final_season_reference", type_order=TYPES,
        support_contract="observed cell/type counts; each crossed cell reports reference type mass unseen there",
        league_baselines=baselines, arrays=arrays_reference, shapes=shapes,
        ledgers=dict(events=identity(event_output), joint=identity(joint_output)),
        row_contracts=dict(events="one final-season recognized unblocked source key with inclusion, reasons and joint index",
                           joint="one distinct predictor tuple with event frequency and equal-event reference weight"),
        units=dict(surfaces="probability", league_baselines="provisional goals per 60 team minutes",
                   cell_type_counts="recorded common-reference events", unseen_cell_type_reference_mass="probability mass"),
        limitations=["unadmitted fixed transfer weights; no admission", "reference extrapolation is not empirical support",
                     "fixed chance fits and reference weights; attribution uncertainty only",
                     "location valuation omits player-specific type/context mix"], resources=resources(started))
    write_json(output / "reference.json", document)
    return identity(output / "reference.json")


def read_reference(path: Path | str) -> tuple[dict, dict[str, np.ndarray] | None]:
    """read the bound reference and two finite native-cell valuation vectors."""
    document = read_json(Path(path).resolve(strict=True))
    require(type(document["schema_version"]) is int and document["schema_version"] == 1
            and document["kind"] == "attribution_reference", "expected attribution reference")
    protocol = read_json(linked_path(document["protocol"]))
    prepared = read_json(linked_path(document["prepared"]))
    require(document["protocol"] == prepared["protocol"] and document["season"] == prepared["target_season"]
            and document["population_id"] == prepared["population_ids"]["unblocked_spatial"]
            and document["population"] == "unblocked_spatial"
            and document["purpose"] == prepared["purpose"] == protocol["purpose"]
            and document["components"] == protocol["components"],
            "reference differs from its prepared population")
    for reference in document["ledgers"].values():
        linked_path(reference)
    if document["status"] == "unavailable":
        require(document["reason"] is not None and document["arrays"] is None, "invalid unavailable reference")
        return document, None
    require(document["status"] == "available" and document["reason"] is None, "invalid reference status")
    shapes = dict(direct=[656], product=[656], cell_type_counts=[656, len(TYPES)],
                  unseen_cell_type_reference_mass=[656])
    require(document["shapes"] == shapes, "reference array shapes differ from native grid")
    with np.load(linked_path(document["arrays"]), allow_pickle=False) as arrays:
        require(set(arrays.files) == set(shapes), "reference array names differ")
        values = {name: arrays[name] for name in arrays.files}
    require(all(list(value.shape) == shapes[name] and np.isfinite(value).all() for name, value in values.items()),
            "reference arrays are nonfinite or incorrectly shaped")
    require(all(np.all((values[name] >= 0) & (values[name] <= 1)) for name in ("direct", "product")),
            "reference surfaces must contain probabilities")
    return document, {name: values[name] for name in ("direct", "product")}


def location_transport(direction: str) -> tuple[np.ndarray, dict]:
    """one mass-conserving native-grid move; nominal targets may leave the rink."""
    require(direction in ("toward", "away"), "unknown location stress direction")
    centers, _ = grid()
    displacement = np.array([89., 0.]) - centers
    distances = np.linalg.norm(displacement, axis=1)
    nonzero = distances != 0
    targets = centers.copy()
    targets[nonzero] += (5 if direction == "toward" else -5) * displacement[nonzero] / distances[nonzero, None]
    destinations = np.argmin(np.sum((centers[:, None, :] - targets[None, :, :])**2, axis=2), axis=0)
    transport = np.zeros((len(centers), len(centers)))
    transport[destinations, np.arange(len(centers))] = 1
    return transport, dict(direction=direction, nominal_displacement_feet=5,
        goal_coordinate=[89, 0], destination_cells=destinations.tolist(),
        actual_displacement_feet=np.linalg.norm(centers[destinations] - centers, axis=1).tolist())


def transport_state(state: AnnualState, transport: np.ndarray) -> AnnualState:
    """transform all response means/covariance; preserve row covariance and scale."""
    transport = np.asarray(transport, dtype=float)
    k = state.M.shape[1]
    require(transport.shape == (k, k) and np.isfinite(transport).all() and np.all(transport >= 0)
            and np.allclose(transport.sum(axis=0), 1, rtol=0, atol=1e-12),
            "response transport must be finite, nonnegative and column stochastic")
    return replace(state, M=state.M @ transport.T, S=transport @ state.S @ transport.T,
                   A=state.A @ transport.T, prior_mean=state.prior_mean @ transport.T,
                   response_counts=transport @ state.response_counts)
