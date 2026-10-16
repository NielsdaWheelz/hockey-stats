"""joint game-refit projections with fixed references and exact-null protection."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from .artifacts import clean_implementation, implementation, linked_path, require, resources, write_json
from .captures import InputContractError
from .chance_cli import identity, output_path, read_json
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


def exact_duplicate_groups(populations: dict, seasons: list[str]) -> dict:
    """compare exact membership prefixes, then independently check their likelihood nulls."""
    from .attribution_data import weighted_population

    result = {}
    for benchmark in ("all_attempts", "unblocked_spatial"):
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


def load_refit_inputs(prepared: Path | str) -> RefitInputs:
    from .attribution_data import load_grouped_population, read_revision_prepared

    path = Path(prepared).resolve(strict=True)
    document = read_revision_prepared(path)
    protocol = read_json(linked_path(document["protocol"]))
    populations = {(benchmark, season): load_grouped_population(path, benchmark, season)
                   for season in document["seasons"]
                   for benchmark in ("all_attempts", "unblocked_spatial")}
    return RefitInputs(document, protocol, populations, identity(path),
                       exact_duplicate_groups(populations, document["seasons"]))


def request_key(request: dict) -> str:
    return "/".join(request[name] for name in ("benchmark", "season", "name", "functional"))


def request_identity(requests: list[dict]) -> str:
    return hashlib.sha256(json.dumps(requests, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def projection_requests(states: dict, pairs: dict, target_season: str) -> list[dict]:
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
            working = project_native(state, c)
        else:
            functional = request["functional"]
            v = (np.ones(1 if state.p is None else len(state.p)) if functional == "scalar" else
                 (regions == REGION_NAMES.index(functional)).astype(float))
            working = project_interval(state, c, v)
        unidentified = null_component(request["role"], request["coefficients"], duplicate_groups)
        row.update(status="not_data_identified" if unidentified else "available", reason=
                   "persistent_same_role_co_deployment_null_component" if unidentified else None,
                   mean=working["mean"], working=working, r=state.r,
                   duplicate_groups=[group for group in duplicate_groups if group["role"] == request["role"]])
        result.append(row)
    return result


def refit_history(prepared: RefitInputs | Path | str, protocol: dict, draw_id: int,
                  projection_requests: list[dict], *, seed_prefix: list[int] | None = None) -> dict:
    """refit every scale and covariance in chronological order; retain completed projections on failure."""
    from .attribution import fit_revision_year
    from .attribution_data import weighted_population

    inputs = prepared if isinstance(prepared, RefitInputs) else load_refit_inputs(prepared)
    require(protocol == inputs.protocol and type(draw_id) is int and draw_id >= 0,
            "refit source/protocol/draw identity differs")
    require(len({request_key(request) for request in projection_requests}) == len(projection_requests),
            "refit projection requests must be unique")
    synthetic = inputs.reference is None
    if synthetic:
        require(isinstance(seed_prefix, list) and len(seed_prefix) == 3 and seed_prefix[0] == 40421
                and type(seed_prefix[1]) is int and 0 <= seed_prefix[1] < 2
                and type(seed_prefix[2]) is int and 0 <= seed_prefix[2] < protocol["budgets"]["outer_per_case"],
                "synthetic refit requires its fixed case/outer seed stream")
    else:
        require(seed_prefix is None, "real refits require the fixed real weight seed stream")
    require(draw_id < protocol["budgets"]["inner_refits" if synthetic else "real_refits"],
            "refit draw exceeds the frozen budget")
    prefix = list(seed_prefix) if synthetic else [40422]
    previous = {benchmark: None for benchmark in ("all_attempts", "unblocked_spatial")}
    projections, annual, weights, seeds = [], [], {}, []
    started = time.monotonic()
    for year_index, season in enumerate(inputs.document["seasons"]):
        groups = [inputs.populations[(benchmark, season)][0]
                  for benchmark in ("all_attempts", "unblocked_spatial")]
        require(groups[0].game_ids == groups[1].game_ids, "paired populations differ in game inventory")
        seed = [*prefix, draw_id, year_index]
        multipliers = game_weights(groups[0].game_ids, seed)
        weights[season] = multipliers
        seeds.append(dict(season=season, seed=seed))
        for benchmark in ("all_attempts", "unblocked_spatial"):
            grouped, references = inputs.populations[(benchmark, season)]
            try:
                population = weighted_population(grouped, multipliers, references)
                state = fit_revision_year(population, previous[benchmark])
            except (InputContractError, np.linalg.LinAlgError, FloatingPointError) as error:
                annual.append(dict(benchmark=benchmark, season=season, status="error", error=str(error)))
                return dict(status="error", error=str(error), failed=dict(benchmark=benchmark, season=season),
                            draw_id=draw_id, projections=projections, annual=annual,
                            weights=weights, seeds=seeds, resources=resources(started))
            previous[benchmark] = state
            annual.append(dict(benchmark=benchmark, season=season, status="complete",
                               volume=dict(scale=state.volume.scale, diagnostics=state.volume.diagnostics),
                               shape=None if state.shape is None else
                               dict(scale=state.shape.scale, diagnostics=state.shape.diagnostics)))
            requests = [request for request in projection_requests
                        if request["benchmark"] == benchmark and request["season"] == season]
            projections.extend(project_requests(state, requests, inputs.duplicate_groups[(benchmark, season)]))
    require(len(projections) == len(projection_requests), "refit did not satisfy all projection requests")
    return dict(status="complete", error=None, failed=None, draw_id=draw_id, projections=projections,
                annual=annual, weights=weights, seeds=seeds, resources=resources(started))


def _write_refit(output: Path, result: dict, inputs: RefitInputs, fits: dict, requests: list[dict]) -> dict:
    arrays = {f"weights_{season}": value for season, value in result["weights"].items()}
    projections = []
    for index, row in enumerate(result["projections"]):
        record = {name: row[name] for name in ("key", "request", "status", "reason")}
        if row["mean"] is not None:
            name = f"projection_{index}"
            arrays[name] = np.asarray(row["mean"])
            record.update(array=name, shape=list(arrays[name].shape))
        else:
            record.update(array=None, shape=None)
        projections.append(record)
    array_path = output / f"refit-{result['draw_id']:03d}.npz"
    with array_path.open("xb") as destination:
        np.savez(destination, **arrays)
    document = dict(schema_version=2, kind="attribution_refit", purpose=inputs.document["purpose"],
                    implementation=implementation(), protocol=inputs.document["protocol"], prepared=inputs.reference,
                    fits=fits, request_sha256=request_identity(requests), draw_id=result["draw_id"],
                    status=result["status"], error=result["error"], failed=result["failed"],
                    seeds=result["seeds"], annual=result["annual"], projections=projections,
                    arrays=identity(array_path), shapes={name: list(value.shape) for name, value in arrays.items()},
                    reference_binding="original annual prepared r,u,p,player ordering and context design",
                    resources=result["resources"])
    path = output / f"refit-{result['draw_id']:03d}.json"
    write_json(path, document)
    return identity(path)


def refit_range(prepared: Path | str, fits: Path | str, start: int, stop: int, out: Path | str) -> dict:
    """one explicit manual range; no replacement draws or hidden continuation."""
    from .attribution import read_fits

    started = time.monotonic()
    inputs = load_refit_inputs(prepared)
    current_implementation = implementation()
    if inputs.document["purpose"] == "research":
        clean_implementation(current_implementation)
        require(current_implementation == inputs.protocol["implementation"],
                "refit implementation differs from frozen protocol")
    fit_path = Path(fits).resolve(strict=True)
    fit_document, states = read_fits(fit_path)
    require(fit_document["prepared"] == inputs.reference and fit_document["protocol"] == inputs.document["protocol"],
            "refit point fits differ from preparation")
    budget = inputs.protocol["budgets"]["real_refits"]
    require(type(start) is int and type(stop) is int and 0 <= start < stop <= budget,
            "invalid half-open refit range")
    requests = projection_requests(states, inputs.document["pairs"], inputs.document["target_season"])
    output = output_path(str(out), [str(Path(prepared).resolve().parent), str(fit_path.parent)])
    require(output.is_relative_to(Path(inputs.protocol["output_root"]).resolve()), "refit output differs from frozen root")
    if inputs.document["purpose"] == "research":
        require(output.is_relative_to(Path("/Volumes/Expansion/hockey-stats")), "research refits must remain external")
    output.mkdir()
    refs, errors = [], []
    for draw_id in range(start, stop):
        result = refit_history(inputs, inputs.protocol, draw_id, requests)
        refs.append(_write_refit(output, result, inputs, identity(fit_path), requests))
        if result["status"] != "complete":
            errors.append(draw_id)
    path = output / "refits.json"
    write_json(path, dict(schema_version=2, kind="attribution_refit_range", purpose=inputs.document["purpose"],
                         implementation=implementation(), protocol=inputs.document["protocol"], prepared=inputs.reference,
                         fits=identity(fit_path), requested_range=[start, stop], requests=requests,
                         request_sha256=request_identity(requests), draws=refs, missing_ids=[], error_ids=errors,
                         status="complete" if not errors else "incomplete", resources=resources(started)))
    return identity(path)


def summarize_refits(prepared: Path | str, fits: Path | str, ranges: list[Path | str]) -> dict:
    """validate explicit ranges and produce no empirical interval unless every assigned draw completed."""
    from .attribution import read_fits

    inputs = load_refit_inputs(prepared)
    fit_reference = identity(Path(fits).resolve(strict=True))
    _, states = read_fits(fits)
    requests = projection_requests(states, inputs.document["pairs"], inputs.document["target_season"])
    request_sha = request_identity(requests)
    base = []
    for benchmark in ("all_attempts", "unblocked_spatial"):
        season = inputs.document["target_season"]
        base.extend(project_requests(states[(benchmark, season)],
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
