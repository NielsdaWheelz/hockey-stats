"""joint game-refit projections with fixed references and exact-null protection."""

from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from .artifacts import linked_path, ordered_array_digest, require, resources
from .captures import InputContractError
from .chance_cli import identity, read_json
from .chance_evaluation import REGION_NAMES, compound_regions
from .shot_origins import grid


@dataclass(frozen=True)
class RefitInputs:
    """one immutable grouped history; all draws recompute its context statistics."""

    document: dict
    protocol: dict
    populations: dict
    reference: dict | None
    duplicate_groups: dict
    source_kind: str


def game_weights(game_ids, seed: list[int]) -> np.ndarray:
    """one positive normalized multiplier per sorted inventory game, including empties."""
    require(list(game_ids) == sorted(set(game_ids)) and len(game_ids) > 0,
            "game weights require a nonempty sorted unique inventory")
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed)))
    weights = rng.exponential(size=len(game_ids))
    weights *= len(game_ids) / weights.sum()
    require(np.isfinite(weights).all() and np.all(weights > 0), "invalid normalized game weights")
    return weights


def basic_interval(estimate, draws: np.ndarray) -> dict:
    """pointwise basic interval; draws are joint trajectory projections, not a posterior."""
    draws = np.asarray(draws, dtype=float)
    estimate = np.asarray(estimate, dtype=float)
    require(draws.ndim >= 1 and draws.shape[1:] == estimate.shape and len(draws) > 0
            and np.isfinite(draws).all() and np.isfinite(estimate).all(), "invalid refit projections")
    low, high = np.quantile(draws, [.025, .975], axis=0, method="linear")
    return dict(kind="basic_game_refit", lower=2 * estimate - high, upper=2 * estimate - low,
                quantile_025=low, quantile_975=high, draws=len(draws),
                reference_meaning="conditional on original annual r,u,p and observed topology")


def meaningful_claim(lower: float, upper: float) -> str:
    """strict five-percent rule for scalar league-relative intervals only."""
    if lower > .05:
        return "meaningful_positive"
    if upper < -.05:
        return "meaningful_negative"
    if lower >= -.05 and upper <= .05:
        return "within_meaningful_band"
    return "unresolved"


def null_component(role: str, coefficients, groups: list[dict]) -> bool:
    """a single member, as well as a difference, contains the persistent null direction."""
    values = {}
    for player, coefficient in coefficients:
        values[player] = values.get(player, 0) + coefficient
    for group in groups:
        if group["role"] == role and len({values.get(player, 0) for player in group["players"]}) > 1:
            return True
    return False


def exact_duplicate_groups(populations: dict, seasons: list[str], *, benchmarks: tuple[str, ...]) -> dict:
    """compare exact membership prefixes, then independently check their likelihood nulls."""
    from .attribution_data import weighted_population

    result = {}
    require(bool(benchmarks) and len(set(benchmarks)) == len(benchmarks)
            and set(populations) == {(benchmark, season) for benchmark in benchmarks for season in seasons},
            "duplicate checks require exactly the selected population history")
    for benchmark in benchmarks:
        signatures = {}
        prefix = []
        for season in seasons:
            grouped, references = populations[(benchmark, season)]
            prefix.append((grouped, references))
            players = references.player_ids
            n = len(players)
            for key in signatures:
                signatures[key].append(None)
            for role_index, role in enumerate(("offense", "defense")):
                for i, player in enumerate(players):
                    key = (role, player)
                    if key not in signatures:
                        signatures[key] = [None] * len(prefix)
                    signatures[key][-1] = grouped.membership_signatures[role_index * n + i]
            by_history = {}
            for (role, player), history in signatures.items():
                by_history.setdefault((role, tuple(history)), []).append(player)
            candidates = [(key[0], members) for key, members in by_history.items() if len(members) > 1]
            annual_populations = []
            if candidates:
                annual_populations = [weighted_population(group, np.ones(len(group.game_ids)), refs)
                                      for group, refs in prefix]
            groups = []
            for role, members in candidates:
                maximum = 0.0
                for population in annual_populations:
                    positions = {player: i for i, player in enumerate(population.player_ids)}
                    offset = len(positions) if role == "defense" else 0
                    for player in members[1:]:
                        direction = np.zeros(2 * len(positions))
                        if members[0] in positions:
                            direction[offset + positions[members[0]]] = 1
                        if player in positions:
                            direction[offset + positions[player]] -= 1
                        residual = population.H @ direction
                        maximum = max(maximum, float(np.max(np.abs(residual), initial=0)))
                        tolerance = 1e-10 * max(1, float(np.linalg.norm(population.H, ord=np.inf)))
                        require(np.max(np.abs(residual), initial=0) <= tolerance,
                                "exact membership duplicate is not independently likelihood-null")
                        require(np.max(np.abs(direction @ population.T), initial=0) <=
                                1e-10 * max(1, float(np.linalg.norm(population.T, ord=np.inf))),
                                "exact membership duplicate has a nonnull response score")
                groups.append(dict(role=role, players=sorted(members),
                                   evidence="identical positive-row membership histories including absence/entry",
                                   likelihood_null_maximum_residual=maximum))
            result[(benchmark, season)] = groups
    return result


def load_native_04b_refit_inputs(prepared: Path | str) -> RefitInputs:
    from .attribution_data import load_grouped_population, read_revision_prepared

    path = Path(prepared).resolve(strict=True)
    document = read_revision_prepared(path)
    protocol = read_json(linked_path(document["protocol"]))
    populations = {(benchmark, season): load_grouped_population(path, benchmark, season)
                   for season in document["seasons"]
                   for benchmark in ("all_attempts", "unblocked_spatial")}
    return RefitInputs(document, protocol, populations, identity(path),
                       exact_duplicate_groups(populations, document["seasons"],
                                              benchmarks=("all_attempts", "unblocked_spatial")), "recorded")


def request_key(request: dict) -> str:
    return "/".join(request[name] for name in ("benchmark", "season", "name", "functional"))


def request_identity(requests: list[dict]) -> str:
    return hashlib.sha256(json.dumps(requests, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def native_04b_projection_requests(states: dict, pairs: dict, target_season: str) -> list[dict]:
    """all current scalar/region claims; native projections only for frozen examples/pairs."""
    pairs = {name: pairs[name] for name in ("greatest_shared", "greatest_disjoint")}
    selected = sorted({player for pair in pairs.values() if pair is not None for player in pair})
    requests = []
    for benchmark in ("all_attempts", "unblocked_spatial"):
        state = states[(benchmark, target_season)]
        for role in ("offense", "defense"):
            comparisons = [(f"player_{player}", [[player, 1]])
                           for player in sorted(set(state.current_player_ids) | set(selected))]
            comparisons += [(name, [[pair[0], 1], [pair[1], -1]])
                            for name, pair in sorted(pairs.items()) if pair is not None]
            for name, coefficients in comparisons:
                functionals = ["scalar"]
                if benchmark == "unblocked_spatial":
                    functionals += list(REGION_NAMES)
                    if name in pairs or coefficients[0][0] in selected:
                        functionals.append("native")
                requests.extend(dict(name=f"{role}_{name}", benchmark=benchmark, season=target_season,
                                     role=role, coefficients=coefficients, functional=functional,
                                     negate=role == "defense") for functional in functionals)
    return requests


def project_requests(state, requests: list[dict], duplicate_groups: list[dict]) -> list[dict]:
    """project one joint annual state through the model's sole projection owner."""
    from .attribution import project_interval, project_native

    positions = {player: i for i, player in enumerate(state.player_ids)}
    regions = compound_regions(grid()[0])
    result = []
    for request in requests:
        row = dict(key=request_key(request), request=request)
        if any(player not in state.current_player_ids for player, _ in request["coefficients"]):
            row.update(status="unavailable", reason="player_not_currently_observed", mean=None, working=None,
                       r=state.r, duplicate_groups=[])
            result.append(row)
            continue
        c = np.zeros(2 * len(positions))
        offset = len(positions) if request["role"] == "defense" else 0
        for player, coefficient in request["coefficients"]:
            c[offset + positions[player]] += coefficient * (-1 if request.get("negate", False) else 1)
        if request["functional"] == "native":
            require(state.p is not None, "native projections require the spatial population")
            working = project_native(state, c, estimand=request["estimand"])
        else:
            functional = request["functional"]
            v = (np.asarray(request["weights"], dtype=float) if "weights" in request else
                 np.ones(1 if state.p is None else len(state.p)) if functional == "scalar" else
                 (regions == REGION_NAMES.index(functional)).astype(float))
            working = project_interval(state, c, v, estimand=request["estimand"])
        unidentified = null_component(request["role"], request["coefficients"], duplicate_groups)
        row.update(status="not_data_identified" if unidentified else "available", reason=
                   "persistent_same_role_co_deployment_null_component" if unidentified else None,
                   mean=working["mean"], working=working, r=state.r,
                   duplicate_groups=[group for group in duplicate_groups if group["role"] == request["role"]])
        result.append(row)
    return result


def project_native_04b_requests(state, requests: list[dict], duplicate_groups: list[dict]) -> list[dict]:
    """read-only native-04b control projections under its original request contract."""
    projected = project_requests(state, [dict(request, estimand="complete_rate") for request in requests],
                                 duplicate_groups)
    for row, request in zip(projected, requests, strict=True):
        row["request"] = request
    return projected


def _history_input_identity(grouped, references, multipliers: np.ndarray) -> str:
    """bind grouped response, row order, references and weights; raw draws belong to the study."""
    arrays = {name: np.asarray(getattr(references, name)) for name in
              ("r", "u", "player_exposure", "response_counts")}
    if references.p is not None:
        arrays["p"] = references.p
    arrays["game_weights"] = np.asarray(multipliers)
    for name in ("stratum_e", "Q_t", "Q_h"):
        value = getattr(grouped, name)
        if value is not None:
            arrays[name] = value
    for name in ("H_e", "T_raw", "stratum_x", "stratum_n"):
        value = getattr(grouped, name)
        arrays.update({f"{name}_{part}": np.asarray(getattr(value, part)) for part in
                       ("shape", "indptr", "indices", "data")})
    metadata = [references.benchmark, references.season, references.season_index,
                references.protocol_sha256, references.population_id, references.player_ids,
                references.strata, grouped.game_ids, grouped.membership_signatures, grouped.row_count,
                ordered_array_digest(arrays)]
    return hashlib.sha256(json.dumps(metadata, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def fit_history(inputs: RefitInputs, projection_requests: list[dict], *, benchmarks: tuple[str, ...],
                game_multipliers: dict[str, np.ndarray], representation: str, basis,
                model_protocol_sha256: str, shared_volume: dict | None = None) -> tuple[dict, dict]:
    """one chronology owner; paired arms share explicit same-evidence annual volume states."""
    from .attribution import TwoBandShapeState, fit_recovery_year
    from .attribution_data import weighted_population

    seasons = inputs.document["seasons"]
    require(bool(benchmarks) and len(set(benchmarks)) == len(benchmarks)
            and set(inputs.populations) == {(benchmark, season) for benchmark in benchmarks for season in seasons}
            and set(game_multipliers) == set(seasons), "fit history differs from selected population years")
    require(inputs.source_kind in ("recorded", "synthetic"), "unknown history source kind")
    require((inputs.source_kind == "recorded" and inputs.reference is not None)
            or (inputs.source_kind == "synthetic" and inputs.reference is None
                and all(references.population_id.startswith("synthetic:")
                        for _, references in inputs.populations.values())),
            "history source identity is absent or contradicts its declared kind")
    require(len({request_key(request) for request in projection_requests}) == len(projection_requests)
            and all(request["benchmark"] in benchmarks and request["season"] in seasons
                    for request in projection_requests), "history projection requests are duplicated or outside its population")
    require((representation == "graph_two_band_80ft" and shared_volume is not None
                and set(shared_volume) == set(inputs.populations))
            or (representation != "graph_two_band_80ft" and shared_volume is None),
            "two-band history requires exactly its explicit control volume history")
    previous = {benchmark: None for benchmark in benchmarks}
    projections, annual, states = [], [], {}
    started = time.monotonic()
    for season in seasons:
        groups = [inputs.populations[(benchmark, season)][0] for benchmark in benchmarks]
        require(all(group.game_ids == groups[0].game_ids for group in groups),
                "selected populations differ in game inventory")
        multipliers = game_multipliers[season]
        for benchmark in benchmarks:
            grouped, references = inputs.populations[(benchmark, season)]
            try:
                population = weighted_population(grouped, multipliers, references)
                input_sha256 = _history_input_identity(grouped, references, multipliers)
                shared = None if shared_volume is None else shared_volume[(benchmark, season)]
                if shared is not None:
                    require(shared.representation == "graph_40ft"
                            and shared.volume.diagnostics.get("history_input_sha256") == input_sha256,
                            "shared volume history differs in grouped response, row order or fixed references")
                    if previous[benchmark] is not None:
                        require(previous[benchmark].volume is
                                shared_volume[(benchmark, previous[benchmark].season)].volume,
                                "shared volume history changed previous-volume lineage")
                state = fit_recovery_year(population, previous[benchmark], representation=representation,
                                          basis=basis, model_protocol_sha256=model_protocol_sha256,
                                          shared_volume=shared)
                if shared is not None:
                    require(state.volume is shared.volume, "paired history did not share its explicit volume block")
                else:
                    state = replace(state, volume=replace(state.volume, diagnostics=dict(
                        state.volume.diagnostics, history_input_sha256=input_sha256)))
                requests = [request for request in projection_requests
                            if request["benchmark"] == benchmark and request["season"] == season]
                projected = project_requests(state, requests, inputs.duplicate_groups[(benchmark, season)])
            except (InputContractError, np.linalg.LinAlgError, FloatingPointError) as error:
                annual.append(dict(benchmark=benchmark, season=season, status="error", error=str(error)))
                return dict(status="error", error=str(error), failed=dict(benchmark=benchmark, season=season),
                            projections=projections, annual=annual, weights=game_multipliers,
                            resources=resources(started)), states
            previous[benchmark] = state
            states[(benchmark, season)] = state
            if isinstance(state.shape, TwoBandShapeState):
                shape = dict(kind="two_band", low=dict(scale=state.shape.low.scale, diagnostics=state.shape.low.diagnostics),
                             high=dict(scale=state.shape.high.scale, diagnostics=state.shape.high.diagnostics))
            else:
                shape = None if state.shape is None else dict(scale=state.shape.scale, diagnostics=state.shape.diagnostics)
            annual.append(dict(benchmark=benchmark, season=season, status="complete",
                               volume=dict(scale=state.volume.scale, diagnostics=state.volume.diagnostics), shape=shape))
            projections.extend(projected)
    require(len(projections) == len(projection_requests), "history did not satisfy all projection requests")
    return dict(status="complete", error=None, failed=None, projections=projections, annual=annual,
                weights=game_multipliers, resources=resources(started)), states


def refit_history(inputs: RefitInputs, draw_id: int, projection_requests: list[dict], *,
                  benchmarks: tuple[str, ...], year_seeds: list[list[int]], representation: str,
                  basis, model_protocol_sha256: str) -> dict:
    """one positive game draw per year; policy and budgets belong to the study caller."""
    seasons = inputs.document["seasons"]
    require(type(draw_id) is int and draw_id >= 0 and bool(benchmarks)
            and len(year_seeds) == len(seasons)
            and all(isinstance(seed, list) and bool(seed)
                    and all(type(value) is int and value >= 0 for value in seed) for seed in year_seeds),
            "refit requires explicit draw identity and annual seeds")
    weights = {season: game_weights(inputs.populations[(benchmarks[0], season)][0].game_ids, seed)
               for season, seed in zip(seasons, year_seeds, strict=True)}
    result, _ = fit_history(inputs, projection_requests, benchmarks=benchmarks, game_multipliers=weights,
                            representation=representation, basis=basis,
                            model_protocol_sha256=model_protocol_sha256)
    result.update(draw_id=draw_id, seeds=[dict(season=season, seed=seed)
                                       for season, seed in zip(seasons, year_seeds, strict=True)])
    return result


def _block_receipt(block: dict) -> dict:
    receipt = {key: block["scale"][key] for key in
               ("status", "selected", "own_reasons", "inherited_limitation")}
    receipt["numerical"] = {key: block["diagnostics"][key] for key in (
        "equation_relative_residual", "original_mean_equation_relative_residual",
        "original_covariance_equation_relative_residual", "covariance_rounding_tolerance",
        "centered_covariance_symmetry", "centered_mean_residual")}
    return receipt


def annual_receipts(annual: list[dict]) -> list[dict]:
    result = []
    for row in annual:
        reduced = {key: row[key] for key in ("benchmark", "season", "status")}
        if row["status"] != "complete":
            reduced["error"] = row["error"]
        else:
            reduced["volume"] = _block_receipt(row["volume"])
            shape = row["shape"]
            if shape is None:
                reduced["shape"] = None
            elif shape.get("kind") == "two_band":
                reduced["shape"] = dict(kind="two_band", low=_block_receipt(shape["low"]),
                                        high=_block_receipt(shape["high"]))
            else:
                reduced["shape"] = _block_receipt(shape)
        result.append(reduced)
    return result


def summarize_native_04b_refits(prepared: Path | str, fits: Path | str, ranges: list[Path | str]) -> dict:
    """validate explicit ranges and produce no empirical interval unless every assigned draw completed."""
    from .attribution import read_native_04b_fits

    inputs = load_native_04b_refit_inputs(prepared)
    fit_reference = identity(Path(fits).resolve(strict=True))
    _, states = read_native_04b_fits(fits)
    requests = native_04b_projection_requests(states, inputs.document["pairs"], inputs.document["target_season"])
    request_sha = request_identity(requests)
    base = []
    for benchmark in ("all_attempts", "unblocked_spatial"):
        season = inputs.document["target_season"]
        base.extend(project_native_04b_requests(states[(benchmark, season)],
                    [request for request in requests if request["benchmark"] == benchmark],
                    inputs.duplicate_groups[(benchmark, season)]))
    base_by_key = {row["key"]: row for row in base}
    draw_values, error_ids, scale_count, unresolved, inherited = {}, [], 0, 0, 0
    requested_ids = set()
    for range_path in ranges:
        document = read_json(Path(range_path).resolve(strict=True))
        require(type(document["schema_version"]) is int and document["schema_version"] == 2
                and document["kind"] == "attribution_refit_range" and document["purpose"] == inputs.document["purpose"]
                and document["prepared"] == inputs.reference and document["fits"] == fit_reference
                and document["protocol"] == inputs.document["protocol"]
                and document["request_sha256"] == request_sha and document["requests"] == requests,
                "refit range identity differs from requested assessment")
        start, stop = document["requested_range"]
        require(type(start) is int and type(stop) is int
                and 0 <= start < stop <= inputs.protocol["budgets"]["real_refits"]
                and not requested_ids.intersection(range(start, stop)), "overlapping or invalid refit ranges")
        requested_ids.update(range(start, stop))
        if inputs.document["purpose"] == "research":
            require(document["implementation"] == inputs.protocol["implementation"],
                    "refit range implementation differs from frozen protocol")
        ids = []
        actual_errors = []
        for reference in document["draws"]:
            draw = read_json(linked_path(reference))
            draw_id = draw["draw_id"]
            require(type(draw_id) is int and start <= draw_id < stop and draw_id not in draw_values,
                    "duplicate or out-of-range refit draw")
            require(draw["schema_version"] == 2 and draw["kind"] == "attribution_refit"
                    and all(draw[key] == document[key] for key in ("purpose", "prepared", "protocol", "fits", "request_sha256")),
                    "refit draw identity differs from its range")
            if inputs.document["purpose"] == "research":
                require(draw["implementation"] == inputs.protocol["implementation"],
                        "refit draw implementation differs from frozen protocol")
            ids.append(draw_id)
            with np.load(linked_path(draw["arrays"]), allow_pickle=False) as arrays:
                require(set(arrays.files) == set(draw["shapes"]), "refit array names differ")
                require(all(list(arrays[name].shape) == shape and np.isfinite(arrays[name]).all()
                            for name, shape in draw["shapes"].items()), "invalid refit arrays")
                values = {row["key"]: None if row["array"] is None else arrays[row["array"]].copy()
                          for row in draw["projections"]}
                require(len(values) == len(draw["projections"]), "duplicate projection in refit draw")
                for row in draw["projections"]:
                    require(row["key"] in base_by_key, "refit contains an unrequested projection")
                    expected = base_by_key[row["key"]]
                    require(row["request"] == expected["request"] and row["status"] == expected["status"],
                            "refit projection topology/status differs from point fit")
                    require((values[row["key"]] is None) == (expected["mean"] is None)
                            and (expected["mean"] is None or
                                 values[row["key"]].shape == np.asarray(expected["mean"]).shape),
                            "refit projection value/shape differs from point fit")
            if draw["status"] == "complete":
                require(set(values) == {request_key(request) for request in requests},
                        "complete refit omitted projection requests")
                require([(row["benchmark"], row["season"], row["status"]) for row in draw["annual"]] ==
                        [(benchmark, season, "complete") for season in inputs.document["seasons"]
                         for benchmark in ("all_attempts", "unblocked_spatial")],
                        "complete refit omitted annual fits")
                require(draw["seeds"] == [dict(season=season, seed=[40422, draw_id, year])
                                         for year, season in enumerate(inputs.document["seasons"])],
                        "complete refit seed stream differs from frozen contract")
            else:
                actual_errors.append(draw_id)
                error_ids.append(draw_id)
            draw_values[draw_id] = values
            for annual in draw["annual"]:
                if annual["status"] != "complete":
                    continue
                for name in ("volume", "shape"):
                    block = annual[name]
                    if block is not None:
                        scale_count += 1
                        unresolved += block["scale"]["status"] == "scale_unresolved"
                        inherited += bool(block["scale"]["inherited_limitation"])
        require(len(ids) == len(set(ids)) and document["missing_ids"] == sorted(set(range(start, stop)) - set(ids))
                and document["error_ids"] == sorted(actual_errors), "refit range completion ledger differs")
    budget = inputs.protocol["budgets"]["real_refits"]
    require(set(draw_values) <= set(range(budget)), "refit ids exceed frozen budget")
    missing_ids = sorted(set(range(budget)) - set(draw_values))
    complete = not missing_ids and not error_ids
    for row in base:
        values = [draw_values[draw][row["key"]] for draw in sorted(draw_values)
                  if draw not in error_ids and row["key"] in draw_values[draw]
                  and draw_values[draw][row["key"]] is not None]
        row["raw_replicate_spread"] = (dict(
            minimum=np.min(values, axis=0), maximum=np.max(values, axis=0),
            quantile_025=np.quantile(values, .025, axis=0, method="linear"),
            quantile_975=np.quantile(values, .975, axis=0, method="linear"), draws=len(values)) if values else None)
        require(not complete or row["status"] != "available" or len(values) == budget,
                "complete refit set does not contain the full projection denominator")
        row["refit"] = (basic_interval(row["mean"], np.stack(values))
                        if complete and row["status"] == "available" else None)
        row["refit_reason"] = (row["reason"] if row["status"] != "available" else
                               None if complete else "incomplete_refit_set")
        if row["request"]["functional"] == "scalar":
            row["meaningful_claim"] = (meaningful_claim(float(row["refit"]["lower"] / row["r"]),
                                                       float(row["refit"]["upper"] / row["r"]))
                                       if row["refit"] is not None else None)
    return dict(status="complete" if complete else "incomplete", expected_draws=budget,
                requested_draw_ids=list(range(budget)), requests=requests,
                completed_draw_ids=sorted(set(draw_values) - set(error_ids)), error_ids=sorted(error_ids),
                missing_ids=missing_ids, projections=base, duplicate_groups=[dict(benchmark=benchmark,
                    season=season, groups=groups) for (benchmark, season), groups in inputs.duplicate_groups.items()],
                scale_searches=scale_count, unresolved_scale_searches=unresolved,
                unresolved_scale_fraction=unresolved / scale_count if scale_count else None,
                inherited_limitations=inherited, admission="not_admitted", handoff=None)
