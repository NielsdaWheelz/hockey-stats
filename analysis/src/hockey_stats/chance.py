"""chance-2: finite-grid origins, seasonal execution and exact joint reference."""

from collections import Counter, OrderedDict
from datetime import date
import math

import numpy as np
from scipy.optimize import minimize
from scipy.special import log_expit, logsumexp, expit

from .captures import InputContractError
from .shot_origins import cell_id, forward_kernel, grid, posterior

TYPES = ["wrist", "snap", "slap", "backhand", "tip", "other"]
ROLES = ["F", "D", "unknown"]
CONTEXT_CATEGORIES = OrderedDict(
    score_bucket=[
        "trailing_2_plus",
        "trailing_1",
        "tied",
        "leading_1",
        "leading_2_plus",
    ],
    period=["1", "2", "3", "OT"],
    home_away=["home", "away"],
    minute_band=["first", "middle", "last"],
    recent_kind=[
        "faceoff",
        "hit",
        "giveaway",
        "takeaway",
        "shot-on-goal",
        "missed-shot",
        "blocked-shot",
    ],
    recent_team=["same", "opponent"],
    recent_delay=list(range(6)),
    recent_zone=["attacking", "other"],
    recent_shooter=["same", "different"],
)
CONTEXT_FIELDS = list(CONTEXT_CATEGORIES)
CONTEXT_REFERENCES = dict(
    score_bucket="tied", period="1", home_away="away", minute_band="middle"
)
SCALAR_FEATURES = [
    f"{key}:{level}"
    for key, levels in CONTEXT_CATEGORIES.items()
    for level in levels
    if level != CONTEXT_REFERENCES.get(key)
]
BATCH_SIZE = 32
REFERENCE_CACHE_CELLS = 65536
CONFIG_FIELDS = {
    "kernel_distance_ft",
    "kernel_direction_strength",
    "ridge_origin_base",
    "ridge_origin_factor",
    "smooth_origin",
    "ridge_cell",
    "ridge_type_cell",
    "smooth_cell",
    "ridge_context",
    "ridge_benchmark",
    "ridge_shooter",
    "change_shooter",
    "ridge_goalie",
    "change_goalie",
    "optimizer_max_iterations",
    "optimizer_ftol",
    "optimizer_gtol",
    "em_max_iterations",
    "em_relative_tolerance",
    "em_posterior_tolerance",
    "objective_decrease_tolerance",
}
ZERO_ALLOWED = {
    "smooth_origin",
    "smooth_cell",
    "kernel_direction_strength",
    "change_shooter",
    "change_goalie",
}
STARTS = ["uniform", "unblocked_multinomial"]


def validate_config(config):
    if not isinstance(config, dict) or set(config) != CONFIG_FIELDS | {
        "schema_version"
    }:
        raise InputContractError("candidate configuration keys do not match schema 2")
    if type(config["schema_version"]) is not int or config["schema_version"] != 2:
        raise InputContractError("unsupported candidate schema")
    for key in CONFIG_FIELDS:
        value = config[key]
        try:
            valid = type(value) in (int, float) and math.isfinite(value)
        except OverflowError:
            valid = False
        if not valid:
            raise InputContractError(f"{key} must be finite numeric data")
        if key.endswith("max_iterations") and type(value) is not int:
            raise InputContractError(f"{key} must be a positive integer")
        if value < 0 or value == 0 and key not in ZERO_ALLOWED:
            raise InputContractError(f"{key} has invalid sign")
    return config


def scalar_features(context):
    """fixed contrasts; missing recent action is the zero reference."""
    if not isinstance(context, dict) or list(context) != CONTEXT_FIELDS:
        raise InputContractError("attempt context fields/order disagree with chance-2")
    for key, levels in CONTEXT_CATEGORIES.items():
        value = context[key]
        if key.startswith("recent_") and value is None:
            continue
        if value not in levels or key == "recent_delay" and type(value) is not int:
            raise InputContractError(f"unsupported context {key}")
    recent = context["recent_kind"] is not None
    if any(
        (context[key] is not None) != recent
        for key in ("recent_team", "recent_delay", "recent_zone")
    ):
        raise InputContractError("recent context factors disagree")
    is_attempt = context["recent_kind"] in (
        "shot-on-goal",
        "missed-shot",
        "blocked-shot",
    )
    if (context["recent_shooter"] is not None) != is_attempt:
        raise InputContractError("recent shooter applicability disagrees")
    return np.array(
        [
            context[key] == level
            for key, levels in CONTEXT_CATEGORIES.items()
            for level in levels
            if level != CONTEXT_REFERENCES.get(key)
        ],
        dtype=np.float64,
    )


def _season(value):
    if not isinstance(value, str) or len(value) != 8 or not value.isdigit():
        raise InputContractError("unsupported season identity")
    year = int(value[:4])
    if value != f"{year:04d}{year + 1:04d}":
        raise InputContractError("unsupported season identity")
    return year


def _validate_attempt(row, centers):
    if (
        not isinstance(row, dict)
        or row.get("model_shot_type") not in TYPES
        or row.get("role") not in ROLES
    ):
        raise InputContractError("attempt requires supported model type and role")
    _season(row.get("season"))
    scalar_features(row.get("context"))
    if any(
        type(row.get(key)) is not int or row[key] <= 0
        for key in ("shooter_id", "goalie_id")
    ):
        raise InputContractError("attempt requires actor identities")
    if (
        type(row.get("blocked")) is not bool
        or type(row.get("goal")) is not bool
        or row["blocked"]
        and row["goal"]
    ):
        raise InputContractError("invalid attempt outcomes")
    return cell_id([row.get("attacking_x"), row.get("attacking_y")], centers)


def _counts(rows, actor, seasons):
    counts = Counter(row[actor + "_id"] for row in rows)
    by_season = Counter((row[actor + "_id"], row["season"]) for row in rows)
    return {
        str(a): dict(total=counts[a], by_season={y: by_season[a, y] for y in seasons})
        for a in sorted(counts)
    }


def _stage_features(kind, seasons, cells, shooters, goalies):
    features = ["intercept"] + [f"season:{y}" for y in seasons[1:]]
    if kind in ("u", "r"):
        features += [f"cell:{h}" for h in range(cells)]
        features += [f"type:{t}:cell:{h}" for t in TYPES[1:] for h in range(cells)]
    else:
        features += [f"type:{t}" for t in TYPES[1:]]
        if kind == "unblocked":
            features += [
                f"type:{t}:geometry:{g}"
                for t in TYPES
                for g in ("d", "a", "d2", "da", "a2")
            ]
        else:
            features += [f"role:{r}" for r in ROLES[1:]]
    features += SCALAR_FEATURES
    features += [f"shooter:{a}:season:{y}" for a in shooters for y in seasons]
    features += [f"goalie:{a}:season:{y}" for a in goalies for y in seasons]
    return features


def _layout(rows, seasons, cells, kind):
    shooters = sorted({r["shooter_id"] for r in rows})
    goalies = sorted({r["goalie_id"] for r in rows}) if kind != "u" else []
    features = _stage_features(kind, seasons, cells, shooters, goalies)
    return dict(
        kind=kind,
        features=features,
        seasons=seasons.copy(),
        cells=cells,
        size=len(features),
        shooters=shooters,
        goalies=goalies,
        shooter_counts=_counts(rows, "shooter", seasons),
        goalie_counts=_counts(rows, "goalie", seasons) if goalies else {},
    )


def _offsets(layout):
    y, h = len(layout["seasons"]), layout["cells"]
    spatial = layout["kind"] in ("u", "r")
    cell = y
    type_start = cell + h if spatial else y
    extra = type_start + 5 * h if spatial else type_start + 5
    scalar = extra if spatial else extra + (30 if layout["kind"] == "unblocked" else 2)
    shooter = scalar + len(SCALAR_FEATURES)
    goalie = shooter + len(layout["shooters"]) * y
    return dict(
        season=1,
        cell=cell,
        type=type_start,
        extra=extra,
        scalar=scalar,
        shooter=shooter,
        goalie=goalie,
    )


def _origin_layout(seasons, cells):
    maps = (
        ["base"] + [f"type:{t}" for t in TYPES[1:]] + [f"role:{r}" for r in ROLES[1:]]
    )
    maps += [f"season:{y}" for y in seasons[1:]] + SCALAR_FEATURES
    features = [f"{name}:cell:{h}" for name in maps for h in range(cells)]
    return dict(
        maps=maps,
        features=features,
        seasons=seasons.copy(),
        cells=cells,
        size=len(features),
    )


def _encode(rows, layout, cells):
    shooters = {a: i for i, a in enumerate(layout["shooters"])}
    goalies = {a: i for i, a in enumerate(layout["goalies"])}
    return dict(
        cell=np.asarray(cells, dtype=np.int64),
        type=np.array([TYPES.index(r["model_shot_type"]) for r in rows]),
        role=np.array([ROLES.index(r["role"]) for r in rows]),
        season=np.array([layout["seasons"].index(r["season"]) for r in rows]),
        scalar=np.array([scalar_features(r["context"]) for r in rows]),
        shooter=np.array([shooters.get(r["shooter_id"], -1) for r in rows]),
        goalie=np.array([goalies.get(r["goalie_id"], -1) for r in rows]),
        goal=np.array([r["goal"] for r in rows], dtype=np.float64),
    )


def _origin_design(data, seasons):
    n = len(data["type"])
    return np.column_stack(
        (
            np.ones(n),
            data["type"][:, None] == np.arange(1, 6),
            data["role"][:, None] == np.arange(1, 3),
            data["season"][:, None] == np.arange(1, len(seasons)),
            data["scalar"],
        )
    )


def _map_penalty(beta, cells, ridges, smooth, edges):
    maps = beta.reshape(-1, cells)
    gradient = ridges[:, None] * maps
    value = 0.5 * np.sum(maps * gradient)
    difference = maps[:, edges[:, 0]] - maps[:, edges[:, 1]]
    value += 0.5 * smooth * np.sum(difference**2)
    for i in range(len(maps)):
        np.add.at(gradient[i], edges[:, 0], smooth * difference[i])
        np.add.at(gradient[i], edges[:, 1], -smooth * difference[i])
    return float(value), gradient.ravel()


def _origin_penalty(beta, layout, config, edges):
    ridges = np.full(len(layout["maps"]), config["ridge_origin_factor"])
    ridges[0] = config["ridge_origin_base"]
    return _map_penalty(beta, layout["cells"], ridges, config["smooth_origin"], edges)


def _penalty(beta, layout, config, edges):
    offsets = _offsets(layout)
    benchmark = layout["kind"] not in ("u", "r")
    ridge = config["ridge_benchmark"] if benchmark else config["ridge_context"]
    gradient = ridge * beta.copy()
    gradient[0] = 0
    value = 0.5 * np.dot(beta, gradient)
    if not benchmark:
        start, end = offsets["cell"], offsets["scalar"]
        value -= 0.5 * ridge * np.dot(beta[start:end], beta[start:end])
        map_value, map_grad = _map_penalty(
            beta[start:end],
            layout["cells"],
            np.array([config["ridge_cell"]] + [config["ridge_type_cell"]] * 5),
            config["smooth_cell"],
            edges,
        )
        value += map_value
        gradient[start:end] = map_grad
    years = len(layout["seasons"])
    for actor in ("shooter", "goalie"):
        start = offsets[actor]
        end = start + len(layout[actor + "s"]) * years
        values = beta[start:end].reshape(-1, years)
        value -= 0.5 * ridge * np.sum(values**2)
        value += 0.5 * config["ridge_" + actor] * np.sum(values**2)
        actor_gradient = config["ridge_" + actor] * values
        difference = np.diff(values, axis=1)
        value += 0.5 * config["change_" + actor] * np.sum(difference**2)
        actor_gradient[:, :-1] -= config["change_" + actor] * difference
        actor_gradient[:, 1:] += config["change_" + actor] * difference
        gradient[start:end] = actor_gradient.ravel()
    return float(value), gradient


def _scalar_logits(beta, layout, data):
    offsets = _offsets(layout)
    value = np.full(len(data["type"]), beta[0])
    season = data["season"]
    valid = season > 0
    value[valid] += beta[season[valid]]
    value += data["scalar"] @ beta[offsets["scalar"] : offsets["shooter"]]
    for actor in ("shooter", "goalie"):
        ids = data[actor]
        valid = ids >= 0
        value[valid] += beta[
            offsets[actor] + ids[valid] * len(layout["seasons"]) + season[valid]
        ]
    return value


def _stage_logits(beta, layout, data, cells, *, scalar_logits=None):
    """cell logits, with optional exact precomputed reference scalar terms."""
    offsets = _offsets(layout)
    h = layout["cells"]
    shared = beta[offsets["cell"] : offsets["type"]]
    types = np.vstack(
        (np.zeros(h), beta[offsets["type"] : offsets["scalar"]].reshape(5, h))
    )
    scalar = _scalar_logits(beta, layout, data) if scalar_logits is None else scalar_logits
    if np.ndim(cells) == 2:
        ids = cells[0]
        return (
            scalar[:, None]
            + shared[ids][None, :]
            + types[data["type"][:, None], ids[None, :]]
        )
    return scalar + shared[cells] + types[data["type"], cells]


def _scalar_gradient(gradient, layout, data, totals):
    offsets = _offsets(layout)
    gradient[0] += totals.sum()
    valid = data["season"] > 0
    np.add.at(gradient, data["season"][valid], totals[valid])
    gradient[offsets["scalar"] : offsets["shooter"]] += data["scalar"].T @ totals
    for actor in ("shooter", "goalie"):
        valid = data[actor] >= 0
        np.add.at(
            gradient,
            offsets[actor]
            + data[actor][valid] * len(layout["seasons"])
            + data["season"][valid],
            totals[valid],
        )


def _slice_data(data, indices):
    return {key: value[indices] for key, value in data.items()}


def _paired_stage_gradient(gradient, layout, data, residual):
    """accumulate scalar and spatial derivatives at known recorded cells."""
    _scalar_gradient(gradient, layout, data, residual)
    offsets = _offsets(layout)
    np.add.at(gradient, offsets["cell"] + data["cell"], residual)
    valid = data["type"] > 0
    np.add.at(
        gradient,
        offsets["type"]
        + (data["type"][valid] - 1) * layout["cells"]
        + data["cell"][valid],
        residual[valid],
    )


def _conversion_objective(beta, data, layout, config, edges):
    value, gradient = _penalty(beta, layout, config, edges)
    logits = _stage_logits(beta, layout, data, data["cell"])
    value -= log_expit(np.where(data["goal"], logits, -logits)).sum()
    residual = expit(logits) - data["goal"]
    _paired_stage_gradient(gradient, layout, data, residual)
    return float(value), gradient


def _avoidance_objective(
    beta, successes, failure_data, failures, layout, config, edges
):
    """known-cell successes and posterior-weighted failures, with one penalty."""
    value, gradient = _penalty(beta, layout, config, edges)
    logits = _stage_logits(beta, layout, successes, successes["cell"])
    value -= np.dot(successes["count"], log_expit(logits))
    residual = successes["count"] * (expit(logits) - 1)
    _paired_stage_gradient(gradient, layout, successes, residual)
    offsets = _offsets(layout)
    h = layout["cells"]
    cells = np.arange(h)[None, :]
    maps = gradient[offsets["type"] : offsets["scalar"]].reshape(5, h)
    for start in range(0, len(failures), BATCH_SIZE):
        end = start + BATCH_SIZE
        batch = _slice_data(failure_data, slice(start, end))
        logits = _stage_logits(beta, layout, batch, cells)
        weights = failures[start:end]
        value -= (weights * log_expit(-logits)).sum()
        residual = weights * expit(logits)
        _scalar_gradient(gradient, layout, batch, residual.sum(axis=1))
        gradient[offsets["cell"] : offsets["type"]] += residual.sum(axis=0)
        for t in range(1, 6):
            maps[t - 1] += residual[batch["type"] == t].sum(axis=0)
    return float(value), gradient


def _origin_objective(beta, design, counts, layout, config, edges):
    value, gradient = _origin_penalty(beta, layout, config, edges)
    maps = beta.reshape(-1, layout["cells"])
    grad = gradient.reshape(maps.shape)
    for start in range(0, len(design), BATCH_SIZE):
        x, target = (
            design[start : start + BATCH_SIZE],
            counts[start : start + BATCH_SIZE],
        )
        logits = x @ maps
        log_pi = logits - logsumexp(logits, axis=1, keepdims=True)
        value -= np.sum(target * log_pi)
        grad += x.T @ (target.sum(axis=1, keepdims=True) * np.exp(log_pi) - target)
    return float(value), gradient


def fit_logistic(objective, initial, config):
    """one optimizer contract for every penalized logistic/multinomial solve."""
    result = minimize(
        objective,
        np.asarray(initial, dtype=np.float64),
        jac=True,
        method="L-BFGS-B",
        options=dict(
            maxiter=config["optimizer_max_iterations"],
            ftol=config["optimizer_ftol"],
            gtol=config["optimizer_gtol"],
        ),
    )
    success = bool(
        result.success and np.isfinite(result.x).all() and np.isfinite(result.fun)
    )
    return result.x, dict(
        converged=success,
        termination=str(result.message),
        iterations=int(result.nit),
        objective=float(result.fun) if np.isfinite(result.fun) else None,
    )


def _geometry(cells, centers):
    points = centers[cells]
    d = np.hypot(89 - points[:, 0], points[:, 1]) / 100
    a = np.arctan2(np.abs(points[:, 1]), 89 - points[:, 0]) / math.pi
    return np.column_stack((d, a, d * d, d * a, a * a))


def _benchmark_features(data, layout, centers):
    years = len(layout["seasons"])
    features = np.zeros((len(data["type"]), layout["size"]))
    features[:, 0] = 1
    valid = data["season"] > 0
    features[np.flatnonzero(valid), data["season"][valid]] = 1
    offsets = _offsets(layout)
    valid = data["type"] > 0
    features[np.flatnonzero(valid), offsets["type"] + data["type"][valid] - 1] = 1
    if layout["kind"] == "unblocked":
        geometry = _geometry(data["cell"], centers)
        for i in range(5):
            features[
                np.arange(len(features)), offsets["extra"] + 5 * data["type"] + i
            ] = geometry[:, i]
    else:
        valid = data["role"] > 0
        features[np.flatnonzero(valid), offsets["extra"] + data["role"][valid] - 1] = 1
    features[:, offsets["scalar"] : offsets["shooter"]] = data["scalar"]
    for actor in ("shooter", "goalie"):
        valid = data[actor] >= 0
        features[
            np.flatnonzero(valid),
            offsets[actor] + data[actor][valid] * years + data["season"][valid],
        ] = 1
    return features


def _benchmark_objective(beta, data, layout, config, edges, centers):
    value, gradient = _penalty(beta, layout, config, edges)
    for start in range(0, len(data["goal"]), BATCH_SIZE):
        batch = _slice_data(data, slice(start, start + BATCH_SIZE))
        x = _benchmark_features(batch, layout, centers)
        logits = x @ beta
        value -= log_expit(np.where(batch["goal"], logits, -logits)).sum()
        gradient += x.T @ (expit(logits) - batch["goal"])
    return float(value), gradient


def _expectation(
    origin_beta,
    beta,
    data,
    origin_design,
    origin_group,
    avoidance_group,
    unblocked_counts,
    failure_group_count,
    origin_layout,
    layout,
    config,
    edges,
    kernel,
    conversion_objective,
):
    counts = unblocked_counts.copy()
    failures = np.zeros((failure_group_count, layout["cells"]))
    maps = origin_beta.reshape(-1, layout["cells"])
    value = (
        -_origin_penalty(origin_beta, origin_layout, config, edges)[0]
        - _penalty(beta, layout, config, edges)[0]
        - conversion_objective
    )
    cells = np.arange(layout["cells"])[None, :]
    for start in range(0, len(data["cell"]), BATCH_SIZE):
        indices = np.arange(start, min(start + BATCH_SIZE, len(data["cell"])))
        batch = _slice_data(data, indices)
        logits = _stage_logits(beta, layout, batch, cells)
        log_pi = origin_design[origin_group[indices]] @ maps
        log_pi -= logsumexp(log_pi, axis=1, keepdims=True)
        blocked = data["blocked"][indices]
        unblocked = ~blocked
        value += (
            log_pi[unblocked, batch["cell"][unblocked]]
            + log_expit(logits[unblocked, batch["cell"][unblocked]])
        ).sum()
        if blocked.any():
            q, likelihood = posterior(
                log_pi[blocked],
                log_expit(-logits[blocked]),
                kernel[batch["cell"][blocked]],
            )
            np.add.at(counts, origin_group[indices[blocked]], q)
            np.add.at(failures, avoidance_group[indices[blocked]], q)
            value += likelihood.sum()
    return counts, failures, float(value)


def _posterior_change(
    old_origin,
    old_u,
    new_origin,
    new_u,
    data,
    origin_design,
    origin_group,
    layout,
    kernel,
):
    change = 0.0
    indices = np.flatnonzero(data["blocked"])
    cells = np.arange(layout["cells"])[None, :]
    for start in range(0, len(indices), BATCH_SIZE):
        ids = indices[start : start + BATCH_SIZE]
        batch = _slice_data(data, ids)
        q = []
        for origin, u in ((old_origin, old_u), (new_origin, new_u)):
            log_pi = origin_design[origin_group[ids]] @ origin.reshape(
                -1, layout["cells"]
            )
            log_pi -= logsumexp(log_pi, axis=1, keepdims=True)
            logits = _stage_logits(u, layout, batch, cells)
            q.append(posterior(log_pi, log_expit(-logits), kernel[batch["cell"]])[0])
        change = max(change, float(np.max(0.5 * np.sum(np.abs(q[0] - q[1]), axis=1))))
    return change


def _numeric_array(value, shape):
    def numeric(data):
        if isinstance(data, list):
            return all(numeric(v) for v in data)
        return type(data) in (int, float) and math.isfinite(data)

    if not isinstance(value, list) or not numeric(value):
        raise ValueError("arrays require finite json numbers")
    array = np.asarray(value, dtype=np.float64)
    if array.shape != shape:
        raise ValueError("array dimensions disagree")
    return array


def _validate_solve(result, *, accepted):
    if not isinstance(result, dict) or set(result) != {
        "converged",
        "termination",
        "iterations",
        "objective",
    }:
        raise ValueError("optimizer diagnostic fields disagree")
    if type(result["converged"]) is not bool or accepted and not result["converged"]:
        raise ValueError("accepted optimizer did not converge")
    if (
        not isinstance(result["termination"], str)
        or not result["termination"]
        or type(result["iterations"]) is not int
        or result["iterations"] < 0
    ):
        raise ValueError("invalid optimizer termination")
    value = result["objective"]
    if value is None:
        if result["converged"]:
            raise ValueError("converged optimizer has no objective")
    elif type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("invalid optimizer objective")


def _validate_start(diag, config, *, active=False):
    fields = {"converged", "termination", "iterations", "inner", "objective_history"}
    optional = {
        "maximum_posterior_change",
        "initializer",
        "failed_solve",
        "rejected_objective",
    }
    if (
        not isinstance(diag, dict)
        or not fields <= set(diag)
        or set(diag) - fields - optional
    ):
        raise ValueError("start diagnostic fields disagree")
    n, history = diag["iterations"], diag["objective_history"]
    if (
        type(n) is not int
        or not 0 <= n <= config["em_max_iterations"]
        or type(diag["converged"]) is not bool
    ):
        raise ValueError("invalid accepted iteration count")
    if (
        not isinstance(diag["inner"], list)
        or len(diag["inner"]) != n
        or not isinstance(history, list)
        or len(history) != n + 1
    ):
        raise ValueError("accepted history dimensions disagree")
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in history):
        raise ValueError("nonfinite accepted objective")
    for previous, value in zip(history, history[1:]):
        if value - previous < -config["objective_decrease_tolerance"] * max(
            1, abs(previous)
        ):
            raise ValueError("accepted observed objective decreased")
    terms = {
        "converged",
        "em iteration limit",
        "avoidance optimizer failed",
        "origin optimizer failed",
        "nonfinite observed objective",
        "observed objective decreased",
        "unblocked origin initializer failed",
    }
    if diag["termination"] not in terms or diag["converged"] != (
        diag["termination"] == "converged"
    ):
        raise ValueError("convergence declaration disagrees")
    if active and (
        diag["termination"] != "em iteration limit" or n >= config["em_max_iterations"]
    ):
        raise ValueError("current state is terminal")
    if (
        not active
        and diag["termination"] == "em iteration limit"
        and n != config["em_max_iterations"]
    ):
        raise ValueError("terminal start did not exhaust its iteration budget")
    if ("maximum_posterior_change" in diag) != (n > 0):
        raise ValueError("posterior evidence disagrees with accepted iterations")
    if n:
        tv = diag["maximum_posterior_change"]
        if type(tv) not in (int, float) or not math.isfinite(tv) or not 0 <= tv <= 1:
            raise ValueError("invalid posterior total variation")
    if diag["converged"] and (
        n == 0
        or abs(history[-1] - history[-2]) / max(1, abs(history[-2]))
        > config["em_relative_tolerance"]
        or diag["maximum_posterior_change"] > config["em_posterior_tolerance"]
    ):
        raise ValueError("start does not meet both convergence tolerances")
    for inner in diag["inner"]:
        if not isinstance(inner, dict) or set(inner) != {"avoidance", "origin"}:
            raise ValueError("accepted inner families disagree")
        for result in inner.values():
            _validate_solve(result, accepted=True)
    if "initializer" in diag:
        _validate_solve(diag["initializer"], accepted=False)
        if diag["initializer"]["converged"] == (
            diag["termination"] == "unblocked origin initializer failed"
        ):
            raise ValueError("initializer result disagrees with start termination")
    elif diag["termination"] == "unblocked origin initializer failed":
        raise ValueError("missing failed initializer evidence")
    if diag["termination"] == "unblocked origin initializer failed" and n:
        raise ValueError("failed initializer has accepted em iterations")
    if ("failed_solve" in diag) != (
        diag["termination"] in ("avoidance optimizer failed", "origin optimizer failed")
    ):
        raise ValueError("failed solve evidence disagrees")
    if "failed_solve" in diag:
        _validate_solve(diag["failed_solve"], accepted=False)
        if diag["failed_solve"]["converged"]:
            raise ValueError("failed optimizer claims convergence")
    if ("rejected_objective" in diag) != (
        diag["termination"] == "observed objective decreased"
    ):
        raise ValueError("rejected objective evidence disagrees")
    if "rejected_objective" in diag:
        value = diag["rejected_objective"]
        if (
            type(value) not in (int, float)
            or not math.isfinite(value)
            or value - history[-1]
            >= -config["objective_decrease_tolerance"] * max(1, abs(history[-1]))
        ):
            raise ValueError("rejected objective did not decrease beyond tolerance")


def _fit_resume(resume, origin_layout, layout, config):
    if resume is None:
        return {}, None
    try:
        if (
            not isinstance(resume, dict)
            or set(resume) != {"schema_version", "completed_starts", "current_start"}
            or type(resume["schema_version"]) is not int
            or resume["schema_version"] != 2
        ):
            raise ValueError("unsupported numerical state schema")
        completed, current = resume["completed_starts"], resume["current_start"]
        if (
            not isinstance(completed, dict)
            or list(completed) != STARTS[: len(completed)]
        ):
            raise ValueError("starts must follow fixed order")
        if current is not None and (
            len(completed) >= 2 or current.get("name") != STARTS[len(completed)]
        ):
            raise ValueError("current start order disagrees")
        for record, active in [(r, False) for r in completed.values()] + (
            [(current, True)] if current else []
        ):
            if not isinstance(record, dict) or set(record) != {
                "origin_coefficients",
                "avoidance_coefficients",
                "diagnostics",
            } | ({"name"} if active else set()):
                raise ValueError("start state fields disagree")
            _numeric_array(record["origin_coefficients"], (origin_layout["size"],))
            _numeric_array(record["avoidance_coefficients"], (layout["size"],))
            _validate_start(record["diagnostics"], config, active=active)
        return completed.copy(), current
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError) as error:
        raise InputContractError(f"invalid fit checkpoint state: {error}") from error


def _em(
    origin,
    beta,
    data,
    design,
    origin_group,
    failure_data,
    avoidance_group,
    counts0,
    successes,
    origin_layout,
    layout,
    config,
    edges,
    kernel,
    conversion_objective,
    resume=None,
    checkpoint=None,
):
    if resume is None:
        diag = dict(
            converged=False,
            termination="em iteration limit",
            iterations=0,
            inner=[],
            objective_history=[],
        )
    else:
        origin = np.array(resume["origin_coefficients"])
        beta = np.array(resume["avoidance_coefficients"])
        diag = dict(
            resume["diagnostics"],
            inner=resume["diagnostics"]["inner"].copy(),
            objective_history=resume["diagnostics"]["objective_history"].copy(),
        )
    args = (
        data,
        design,
        origin_group,
        avoidance_group,
        counts0,
        len(failure_data["type"]),
        origin_layout,
        layout,
        config,
        edges,
        kernel,
        conversion_objective,
    )
    counts, failures, objective = _expectation(origin, beta, *args)
    if not np.isfinite(objective):
        raise InputContractError("nonfinite initial observed objective")
    if resume is None:
        diag["objective_history"].append(objective)
    elif abs(objective - diag["objective_history"][-1]) > 1e-10 * max(
        1, abs(objective)
    ):
        raise InputContractError(
            "checkpoint accepted objective disagrees with numerical state"
        )
    for _ in range(diag["iterations"], config["em_max_iterations"]):
        next_beta, u_diag = fit_logistic(
            lambda b: _avoidance_objective(
                b, successes, failure_data, failures, layout, config, edges
            ),
            beta,
            config,
        )
        if not u_diag["converged"]:
            diag.update(termination="avoidance optimizer failed", failed_solve=u_diag)
            break
        next_origin, pi_diag = fit_logistic(
            lambda b: _origin_objective(
                b, design, counts, origin_layout, config, edges
            ),
            origin,
            config,
        )
        if not pi_diag["converged"]:
            diag.update(termination="origin optimizer failed", failed_solve=pi_diag)
            break
        next_counts, next_failures, objective = _expectation(
            next_origin, next_beta, *args
        )
        if not np.isfinite(objective):
            diag["termination"] = "nonfinite observed objective"
            break
        previous = diag["objective_history"][-1]
        scale = max(1, abs(previous))
        change = objective - previous
        if change < -config["objective_decrease_tolerance"] * scale:
            diag.update(
                termination="observed objective decreased", rejected_objective=objective
            )
            break
        tv = _posterior_change(
            origin,
            beta,
            next_origin,
            next_beta,
            data,
            design,
            origin_group,
            layout,
            kernel,
        )
        origin, beta, counts, failures = (
            next_origin,
            next_beta,
            next_counts,
            next_failures,
        )
        diag["objective_history"].append(objective)
        diag["inner"].append(dict(avoidance=u_diag, origin=pi_diag))
        diag.update(iterations=diag["iterations"] + 1, maximum_posterior_change=tv)
        if (
            abs(change) / scale <= config["em_relative_tolerance"]
            and tv <= config["em_posterior_tolerance"]
        ):
            diag.update(converged=True, termination="converged")
            break
        if checkpoint is not None and diag["iterations"] < config["em_max_iterations"]:
            checkpoint(origin, beta, diag)
    return origin, beta, diag


def fit_model(attempts, config, metadata, *, resume=None, checkpoint=None):
    """fit two fixed starts; checkpoints contain only fully accepted em states."""
    validate_config(config)
    rows = list(attempts)
    centers, edges = grid()
    ids = np.array([_validate_attempt(r, centers) for r in rows], dtype=np.int64)
    selected_years = [int(game_id[:4]) for game_id in metadata["training_game_dates"]]
    seasons = [
        f"{y:04d}{y + 1:04d}"
        for y in range(min(selected_years), max(selected_years) + 1)
    ]
    if any(r["season"] not in seasons for r in rows):
        raise InputContractError("attempt season outside selected training seasons")
    diagnostics = dict(
        status="failed",
        chosen_start=None,
        starts={},
        scientific_assessment="not_performed",
    )
    blocked = np.array([r["blocked"] for r in rows])
    unblocked = [r for r in rows if not r["blocked"]]
    goals = sum(r["goal"] for r in unblocked)
    if (
        not unblocked
        or not goals
        or goals == len(unblocked)
        or len(unblocked) == len(rows)
    ):
        diagnostics["termination"] = (
            "training requires blocks, unblocked goals and unblocked non-goals"
        )
        return None, diagnostics
    reference_rows = [r for r in rows if r["season"] == seasons[-1]]
    if not reference_rows:
        diagnostics["termination"] = (
            "target reference season requires eligible attempts"
        )
        return None, diagnostics
    u_layout = _layout(rows, seasons, len(centers), "u")
    r_layout = _layout(unblocked, seasons, len(centers), "r")
    origin_layout = _origin_layout(seasons, len(centers))
    completed, current = _fit_resume(resume, origin_layout, u_layout, config)
    u_data = _encode(rows, u_layout, ids)
    r_data = _encode(unblocked, r_layout, ids[~blocked])
    u_data["blocked"] = blocked
    design, origin_group = np.unique(
        _origin_design(u_data, seasons), axis=0, return_inverse=True
    )
    group_keys, groups = np.unique(
        np.column_stack(
            (u_data["type"], u_data["season"], u_data["shooter"], u_data["scalar"])
        ),
        axis=0,
        return_inverse=True,
    )
    group_data = dict(
        type=group_keys[:, 0].astype(int),
        season=group_keys[:, 1].astype(int),
        shooter=group_keys[:, 2].astype(int),
        scalar=group_keys[:, 3:],
        goalie=np.full(len(group_keys), -1),
    )
    counts0 = np.zeros((len(design), len(centers)))
    np.add.at(counts0, (origin_group[~blocked], ids[~blocked]), 1)
    # successes have known cells; blocked failure groups retain every grid cell.
    positive_keys, positive_counts = np.unique(
        np.column_stack((groups[~blocked], ids[~blocked])),
        axis=0,
        return_counts=True,
    )
    successes = _slice_data(group_data, positive_keys[:, 0])
    successes["cell"] = positive_keys[:, 1]
    successes["count"] = positive_counts
    failure_groups, failure_indices = np.unique(groups[blocked], return_inverse=True)
    failure_data = _slice_data(group_data, failure_groups)
    avoidance_group = np.full(len(rows), -1, dtype=np.int64)
    avoidance_group[blocked] = failure_indices
    r_initial = np.zeros(r_layout["size"])
    r_initial[0] = math.log(goals / (len(unblocked) - goals))
    r_beta, r_diag = fit_logistic(
        lambda b: _conversion_objective(b, r_data, r_layout, config, edges),
        r_initial,
        config,
    )
    diagnostics["r"] = r_diag
    if not r_diag["converged"]:
        diagnostics["termination"] = "conversion optimizer failed"
        return None, diagnostics
    kernel = forward_kernel(
        centers, config["kernel_distance_ft"], config["kernel_direction_strength"]
    )
    u_initial = np.zeros(u_layout["size"])
    u_initial[0] = math.log(len(unblocked) / (len(rows) - len(unblocked)))
    chosen = None
    for name in STARTS:
        if name in completed:
            record = completed[name]
            origin, beta, diag = (
                np.array(record["origin_coefficients"]),
                np.array(record["avoidance_coefficients"]),
                record["diagnostics"],
            )
            objective = _expectation(
                origin,
                beta,
                u_data,
                design,
                origin_group,
                avoidance_group,
                counts0,
                len(failure_groups),
                origin_layout,
                u_layout,
                config,
                edges,
                kernel,
                r_diag["objective"],
            )[2]
            if not math.isfinite(objective) or abs(
                objective - diag["objective_history"][-1]
            ) > 1e-10 * max(1, abs(objective)):
                raise InputContractError(
                    "checkpoint accepted objective disagrees with numerical state"
                )
        else:
            origin = np.zeros(origin_layout["size"])
            initializer = None
            if name == "unblocked_multinomial" and current is None:
                origin, initializer = fit_logistic(
                    lambda b: _origin_objective(
                        b, design, counts0, origin_layout, config, edges
                    ),
                    origin,
                    config,
                )

            def save_current(origin, beta, diag):
                saved_diag = dict(
                    diag,
                    inner=diag["inner"].copy(),
                    objective_history=diag["objective_history"].copy(),
                )
                if initializer is not None:
                    saved_diag["initializer"] = initializer
                checkpoint(
                    dict(
                        schema_version=2,
                        completed_starts=completed.copy(),
                        current_start=dict(
                            name=name,
                            origin_coefficients=origin.tolist(),
                            avoidance_coefficients=beta.tolist(),
                            diagnostics=saved_diag,
                        ),
                    )
                )

            if initializer is not None and not initializer["converged"]:
                origin = np.zeros(origin_layout["size"])
                beta = u_initial.copy()
                objective = _expectation(
                    origin,
                    beta,
                    u_data,
                    design,
                    origin_group,
                    avoidance_group,
                    counts0,
                    len(failure_groups),
                    origin_layout,
                    u_layout,
                    config,
                    edges,
                    kernel,
                    r_diag["objective"],
                )[2]
                diag = dict(
                    converged=False,
                    termination="unblocked origin initializer failed",
                    iterations=0,
                    inner=[],
                    objective_history=[objective],
                    initializer=initializer,
                )
            else:
                origin, beta, diag = _em(
                    origin,
                    u_initial.copy(),
                    u_data,
                    design,
                    origin_group,
                    failure_data,
                    avoidance_group,
                    counts0,
                    successes,
                    origin_layout,
                    u_layout,
                    config,
                    edges,
                    kernel,
                    r_diag["objective"],
                    resume=current,
                    checkpoint=save_current if checkpoint else None,
                )
                if initializer is not None:
                    diag["initializer"] = initializer
            completed[name] = dict(
                origin_coefficients=origin.tolist(),
                avoidance_coefficients=beta.tolist(),
                diagnostics=diag,
            )
            current = None
            if checkpoint:
                checkpoint(
                    dict(
                        schema_version=2,
                        completed_starts=completed.copy(),
                        current_start=None,
                    )
                )
        diagnostics["starts"][name] = diag
        if diag["converged"] and (
            chosen is None or diag["objective_history"][-1] > chosen[3]
        ):
            chosen = (name, origin, beta, diag["objective_history"][-1])
    if chosen is None:
        diagnostics["termination"] = "no em start converged"
        return None, diagnostics
    benchmarks = {}
    for name, selected, cells in (
        ("unblocked", unblocked, ids[~blocked]),
        ("all_attempt", rows, ids),
    ):
        layout = _layout(selected, seasons, len(centers), name)
        data = _encode(selected, layout, cells)
        initial = np.zeros(layout["size"])
        initial[0] = math.log(sum(data["goal"]) / (len(selected) - sum(data["goal"])))
        beta, diag = fit_logistic(
            lambda b: _benchmark_objective(b, data, layout, config, edges, centers),
            initial,
            config,
        )
        benchmarks[name] = dict(layout, coefficients=beta.tolist(), diagnostics=diag)
    diagnostics["benchmarks"] = {k: v["diagnostics"] for k, v in benchmarks.items()}
    if any(not v["diagnostics"]["converged"] for v in benchmarks.values()):
        diagnostics["termination"] = "benchmark optimizer failed"
        return None, diagnostics
    pairs = Counter((r["shooter_id"], r["goalie_id"]) for r in reference_rows)
    diagnostics.update(status="fitted", chosen_start=chosen[0], termination="converged")
    model = dict(
        metadata,
        schema_version=2,
        model_kind="chance-2",
        config=dict(config),
        grid=dict(centers=centers.tolist(), neighbors=edges.tolist()),
        type_order=TYPES.copy(),
        role_order=ROLES.copy(),
        context_categories=dict(CONTEXT_CATEGORIES),
        scalar_features=SCALAR_FEATURES.copy(),
        seasons=seasons,
        training_seasons=sorted({r["season"] for r in rows}),
        reference_season=seasons[-1],
        origin=dict(origin_layout, coefficients=chosen[1].tolist()),
        stages=dict(
            u=dict(u_layout, coefficients=chosen[2].tolist()),
            r=dict(r_layout, coefficients=r_beta.tolist()),
        ),
        kernel=dict(
            distance_ft=config["kernel_distance_ft"],
            direction_strength=config["kernel_direction_strength"],
        ),
        reference=[
            dict(shooter_id=s, goalie_id=g, count=n, weight=n / len(reference_rows))
            for (s, g), n in sorted(pairs.items())
        ],
        benchmarks=benchmarks,
        diagnostics=diagnostics,
        scientific_assessment="not_performed",
    )
    model["training_game_ids"] = list(model["training_game_dates"])
    model["training_dates"] = sorted(set(model["training_game_dates"].values()))
    validate_model(model)
    return model, diagnostics


def _validate_layout(layout, seasons, cells, kind):
    fields = {
        "kind",
        "features",
        "seasons",
        "cells",
        "size",
        "shooters",
        "goalies",
        "shooter_counts",
        "goalie_counts",
        "coefficients",
    }
    if kind not in ("u", "r"):
        fields.add("diagnostics")
    if not isinstance(layout, dict) or set(layout) != fields or layout["kind"] != kind:
        raise ValueError("layout fields/kind disagree")
    if (
        layout["seasons"] != seasons
        or type(layout["cells"]) is not int
        or layout["cells"] != cells
    ):
        raise ValueError("layout seasons/cells disagree")
    for actor in ("shooter", "goalie"):
        ids, counts = layout[actor + "s"], layout[actor + "_counts"]
        if (
            not isinstance(ids, list)
            or any(type(a) is not int or a <= 0 for a in ids)
            or ids != sorted(set(ids))
            or set(counts) != {str(a) for a in ids}
        ):
            raise ValueError("invalid actor order/counts")
        for a in ids:
            count = counts[str(a)]
            if set(count) != {"total", "by_season"} or set(count["by_season"]) != set(
                seasons
            ):
                raise ValueError("actor evidence seasons disagree")
            ns = list(count["by_season"].values())
            if (
                type(count["total"]) is not int
                or count["total"] <= 0
                or any(type(n) is not int or n < 0 for n in ns)
                or sum(ns) != count["total"]
            ):
                raise ValueError("invalid actor evidence")
    if kind == "u" and layout["goalies"]:
        raise ValueError("avoidance stage cannot contain goalies")
    if kind != "u":
        for y in seasons:
            shooters = sum(c["by_season"][y] for c in layout["shooter_counts"].values())
            goalies = sum(c["by_season"][y] for c in layout["goalie_counts"].values())
            if shooters != goalies:
                raise ValueError("shooter/goalie evidence populations disagree")
    expected_features = _stage_features(
        kind, seasons, cells, layout["shooters"], layout["goalies"]
    )
    if (
        layout["features"] != expected_features
        or type(layout["size"]) is not int
        or layout["size"] != len(expected_features)
    ):
        raise ValueError("coefficient order disagrees")
    _numeric_array(layout["coefficients"], (layout["size"],))


def validate_model(model):
    """reject incomplete, old or inconsistent numerical/provenance artifacts."""
    try:
        if (
            not isinstance(model, dict)
            or type(model["schema_version"]) is not int
            or model["schema_version"] != 2
            or model["model_kind"] != "chance-2"
        ):
            raise ValueError("unsupported model version")
        fields = {
            "schema_version",
            "model_kind",
            "purpose",
            "implementation",
            "inputs",
            "selection",
            "game_dates",
            "coverage",
            "scientific_assessment",
            "config_identity",
            "resumed_from",
            "training_game_dates",
            "training_game_ids",
            "training_dates",
            "config",
            "grid",
            "type_order",
            "role_order",
            "context_categories",
            "scalar_features",
            "seasons",
            "training_seasons",
            "reference_season",
            "origin",
            "stages",
            "kernel",
            "reference",
            "benchmarks",
            "diagnostics",
        }
        if set(model) != fields:
            raise ValueError("model fields do not match schema 2")
        if (
            model["purpose"] not in ("fixture_exercise", "research")
            or model["scientific_assessment"] != "not_performed"
        ):
            raise ValueError("unsupported purpose/assessment")
        validate_config(model["config"])
        centers, edges = grid()
        if (
            set(model["grid"]) != {"centers", "neighbors"}
            or not np.array_equal(
                _numeric_array(model["grid"]["centers"], centers.shape), centers
            )
            or not np.array_equal(
                _numeric_array(model["grid"]["neighbors"], edges.shape), edges
            )
        ):
            raise ValueError("grid differs from chance-2")
        if (
            model["type_order"] != TYPES
            or model["role_order"] != ROLES
            or model["context_categories"] != dict(CONTEXT_CATEGORIES)
            or model["scalar_features"] != SCALAR_FEATURES
        ):
            raise ValueError("category/feature order differs from chance-2")
        seasons = model["seasons"]
        years = [_season(y) for y in seasons]
        if not years or years != list(range(years[0], years[-1] + 1)):
            raise ValueError("season states are not contiguous")
        observed = model["training_seasons"]
        if (
            not isinstance(observed, list)
            or observed != sorted(set(observed))
            or not set(observed) <= set(seasons)
            or model["reference_season"] != seasons[-1]
            or seasons[-1] not in observed
        ):
            raise ValueError("invalid target/training seasons")
        expected_origin = _origin_layout(seasons, len(centers))
        origin = model["origin"]
        if set(origin) != set(expected_origin) | {"coefficients"} or any(
            origin[k] != v for k, v in expected_origin.items()
        ):
            raise ValueError("origin coefficient layout disagrees")
        _numeric_array(origin["coefficients"], (origin["size"],))
        if set(model["stages"]) != {"u", "r"} or set(model["benchmarks"]) != {
            "unblocked",
            "all_attempt",
        }:
            raise ValueError("stage/benchmark families disagree")
        for kind, layout in list(model["stages"].items()) + list(
            model["benchmarks"].items()
        ):
            _validate_layout(layout, seasons, len(centers), kind)
        if model["kernel"] != dict(
            distance_ft=model["config"]["kernel_distance_ft"],
            direction_strength=model["config"]["kernel_direction_strength"],
        ):
            raise ValueError("kernel/config mismatch")
        u, r = model["stages"]["u"], model["stages"]["r"]
        total = sum(c["total"] for c in u["shooter_counts"].values())
        conversion = sum(c["total"] for c in r["shooter_counts"].values())
        if not 0 < conversion < total or conversion != sum(
            c["total"] for c in r["goalie_counts"].values()
        ):
            raise ValueError("stage counts disagree")
        observed_from_counts = [
            y
            for y in seasons
            if sum(c["by_season"][y] for c in u["shooter_counts"].values())
        ]
        if observed != observed_from_counts:
            raise ValueError("training seasons disagree with evidence")
        if not set(r["shooters"]) <= set(u["shooters"]):
            raise ValueError("conversion shooters lack avoidance evidence")
        for a in r["shooters"]:
            if any(
                r["shooter_counts"][str(a)]["by_season"][y]
                > u["shooter_counts"][str(a)]["by_season"][y]
                for y in seasons
            ):
                raise ValueError("conversion evidence exceeds avoidance evidence")
        for kind, candidate in (("unblocked", r), ("all_attempt", u)):
            benchmark = model["benchmarks"][kind]
            if (
                benchmark["shooter_counts"] != candidate["shooter_counts"]
                or kind == "unblocked"
                and benchmark["goalie_counts"] != r["goalie_counts"]
            ):
                raise ValueError("benchmark evidence population disagrees")
        pairs = model["reference"]
        if not isinstance(pairs, list) or not pairs:
            raise ValueError("missing joint reference")
        identities = [(p["shooter_id"], p["goalie_id"]) for p in pairs]
        if identities != sorted(set(identities)):
            raise ValueError("reference actor order disagrees")
        reference_total = sum(
            c["by_season"][seasons[-1]] for c in u["shooter_counts"].values()
        )
        if sum(p["count"] for p in pairs) != reference_total:
            raise ValueError("reference counts disagree with target season")
        for p in pairs:
            if (
                set(p) != {"shooter_id", "goalie_id", "count", "weight"}
                or type(p["shooter_id"]) is not int
                or p["shooter_id"] not in u["shooters"]
                or type(p["goalie_id"]) is not int
                or p["goalie_id"] <= 0
                or type(p["count"]) is not int
                or p["count"] <= 0
                or type(p["weight"]) not in (int, float)
                or not math.isfinite(p["weight"])
                or abs(p["weight"] - p["count"] / reference_total) > 1e-12
            ):
                raise ValueError("invalid joint reference member")
        for a in u["shooters"]:
            if (
                sum(p["count"] for p in pairs if p["shooter_id"] == a)
                != u["shooter_counts"][str(a)]["by_season"][seasons[-1]]
            ):
                raise ValueError("target reference shooter counts disagree")
        all_attempt = model["benchmarks"]["all_attempt"]
        if not set(r["goalies"]) <= set(all_attempt["goalies"]):
            raise ValueError("conversion goalies lack all-attempt evidence")
        for a in r["goalies"]:
            if any(
                r["goalie_counts"][str(a)]["by_season"][y]
                > all_attempt["goalie_counts"][str(a)]["by_season"][y]
                for y in seasons
            ):
                raise ValueError(
                    "conversion goalie evidence exceeds all-attempt evidence"
                )
        if any(p["goalie_id"] not in all_attempt["goalies"] for p in pairs):
            raise ValueError("reference goalie lacks all-attempt evidence")
        for a in all_attempt["goalies"]:
            if (
                sum(p["count"] for p in pairs if p["goalie_id"] == a)
                != all_attempt["goalie_counts"][str(a)]["by_season"][seasons[-1]]
            ):
                raise ValueError("target reference goalie counts disagree")
        dates = model["training_game_dates"]
        if (
            not isinstance(dates, dict)
            or not dates
            or any(
                not isinstance(g, str) or len(g) != 10 or not g.isdigit() for g in dates
            )
        ):
            raise ValueError("invalid training identities")
        for value in dates.values():
            if (
                not isinstance(value, str)
                or date.fromisoformat(value).isoformat() != value
            ):
                raise ValueError("invalid training calendar date")
        selected_years = [int(g[:4]) for g in dates]
        if (
            min(selected_years) != years[0]
            or max(selected_years) != years[-1]
            or model["training_game_ids"] != list(dates)
            or model["training_dates"] != sorted(set(dates.values()))
        ):
            raise ValueError("training dates/seasons disagree")
        if model["game_dates"] != dates:
            raise ValueError("source/training game dates disagree")
        coverage = model["coverage"]
        if not isinstance(coverage, dict) or set(coverage) != {
            "games",
            "games_by_status",
            "attempts",
            "attempts_by_status",
            "attempts_by_reason",
            "per_game",
        }:
            raise ValueError("incomplete coverage fields")
        if (
            coverage["games"]["selected"] != len(dates)
            or coverage["attempts"]["chance_2_eligible_attempts"] != total
            or coverage["attempts_by_status"]["eligible"] != total
        ):
            raise ValueError("coverage/training counts disagree")
        if not isinstance(coverage["per_game"], list) or [
            g["game_id"] for g in coverage["per_game"]
        ] != list(dates):
            raise ValueError("coverage game ledger disagrees")
        if (
            sum(g["chance_2_eligible_attempts"] or 0 for g in coverage["per_game"])
            != total
        ):
            raise ValueError("coverage game counts disagree")
        implementation = model["implementation"]
        if not isinstance(implementation, dict) or set(implementation) != {
            "git_commit",
            "git_dirty",
            "python_version",
            "numpy_version",
            "scipy_version",
            "lockfile_sha256",
        }:
            raise ValueError("implementation identity fields disagree")
        commit, dirty = implementation["git_commit"], implementation["git_dirty"]
        if commit is None:
            if dirty is not None:
                raise ValueError("unidentified implementation cannot have git state")
        elif (
            not isinstance(commit, str)
            or len(commit) != 40
            or any(c not in "0123456789abcdef" for c in commit)
            or type(dirty) is not bool
        ):
            raise ValueError("invalid implementation git identity/state")
        if any(
            not isinstance(implementation[k], str) or not implementation[k]
            for k in ("python_version", "numpy_version", "scipy_version")
        ):
            raise ValueError("missing implementation versions")
        digest = implementation["lockfile_sha256"]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(c not in "0123456789abcdef" for c in digest)
        ):
            raise ValueError("invalid lockfile identity")
        if not isinstance(model["inputs"], list) or not model["inputs"]:
            raise ValueError("missing input identities")
        identities = [(model["config_identity"], False)] + [
            (identity, True) for identity in model["inputs"]
        ]
        if model["resumed_from"] is not None:
            identities.append((model["resumed_from"], False))
        for identity, source in identities:
            digest = identity["sha256"]
            if (
                set(identity) != {"path", "sha256"} | ({"kind"} if source else set())
                or source
                and identity["kind"] not in ("selection", "corpus", "game")
                or not isinstance(identity["path"], str)
                or not identity["path"]
                or not isinstance(digest, str)
                or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)
            ):
                raise ValueError("invalid input identity")
        selection = model["selection"]
        if (
            set(selection) != {"schema_version", "purpose", "corpora"}
            or type(selection["schema_version"]) is not int
            or selection["schema_version"] != 1
            or selection["purpose"] != model["purpose"]
            or not isinstance(selection["corpora"], list)
            or not selection["corpora"]
        ):
            raise ValueError("invalid selection")
        selected = []
        for corpus in selection["corpora"]:
            if (
                set(corpus) != {"path", "game_ids"}
                or not isinstance(corpus["path"], str)
                or not corpus["path"]
                or not isinstance(corpus["game_ids"], list)
                or not corpus["game_ids"]
            ):
                raise ValueError("invalid selected corpus")
            selected += corpus["game_ids"]
        if len(set(selected)) != len(selected) or set(selected) != set(dates):
            raise ValueError("selection/training identities disagree")
        diag = model["diagnostics"]
        if (
            set(diag)
            != {
                "status",
                "chosen_start",
                "starts",
                "scientific_assessment",
                "r",
                "benchmarks",
                "termination",
            }
            or list(diag["starts"]) != STARTS
            or diag["scientific_assessment"] != "not_performed"
            or diag["termination"] != "converged"
        ):
            raise ValueError("fit completion fields disagree")
        for start in diag["starts"].values():
            _validate_start(start, model["config"])
        chosen = diag["starts"][diag["chosen_start"]]
        if (
            diag["status"] != "fitted"
            or diag["chosen_start"] not in STARTS
            or chosen["converged"] is not True
            or diag["r"]["converged"] is not True
        ):
            raise ValueError("model has no successful fit")
        best = None
        for name in STARTS:
            start = diag["starts"][name]
            if start["converged"] and (
                best is None
                or start["objective_history"][-1]
                > diag["starts"][best]["objective_history"][-1]
            ):
                best = name
        if diag["chosen_start"] != best:
            raise ValueError(
                "selected start does not maximize converged penalized objective"
            )
        _validate_solve(diag["r"], accepted=True)
        if diag["benchmarks"] != {
            k: v["diagnostics"] for k, v in model["benchmarks"].items()
        }:
            raise ValueError("benchmark completion evidence disagrees")
        for benchmark in model["benchmarks"].values():
            _validate_solve(benchmark["diagnostics"], accepted=True)
    except (
        KeyError,
        TypeError,
        ValueError,
        OverflowError,
        AttributeError,
        IndexError,
        ZeroDivisionError,
    ) as error:
        raise InputContractError(f"invalid chance model: {error}") from error
    return model


def _season_state(model, attempt):
    season = attempt["season"]
    if season < model["seasons"][0]:
        raise InputContractError("season_unsupported")
    if season > model["seasons"][-1]:
        return "carried_forward", model["seasons"][-1]
    return ("fitted" if season in model["training_seasons"] else "unobserved"), season


def actor_evidence(model, row, state_season=None):
    _, state = _season_state(model, row)
    if state_season is not None:
        state = state_season
    result = {}
    for name in ("u", "r"):
        result[name] = {}
        for actor in ("shooter",) if name == "u" else ("shooter", "goalie"):
            counts = model["stages"][name][actor + "_counts"].get(
                str(row[actor + "_id"])
            )
            total = counts["total"] if counts else 0
            count = counts["by_season"][state] if counts else 0
            result[name][actor] = dict(
                total_training_count=total,
                state_season_count=count,
                basis="observed_in_state"
                if count
                else "other_seasons_only"
                if total
                else "unseen",
                coefficient_basis="fitted_seasonal_state"
                if total
                else "zero_penalty_prior_mode",
            )
    return result


def prediction_context(model):
    """opaque reusable numerical state and bounded exact reference cache."""
    validate_model(model)
    centers, _ = grid()
    context = {
        "centers": centers,
        "kernel": forward_kernel(
            centers,
            model["kernel"]["distance_ft"],
            model["kernel"]["direction_strength"],
        ),
        "origin": np.asarray(model["origin"]["coefficients"]),
        "stages": {k: np.asarray(v["coefficients"]) for k, v in model["stages"].items()},
        "benchmarks": {
            k: np.asarray(v["coefficients"]) for k, v in model["benchmarks"].items()
        },
        "reference_cache": OrderedDict(),
        "reference_weights": np.array([pair["weight"] for pair in model["reference"]]),
        "reference_scalar_logits": {},
    }
    # the zero contrast leaves intercept, target season and joint actor terms.
    neutral_context = {key: CONTEXT_REFERENCES.get(key) for key in CONTEXT_FIELDS}
    reference_rows = [
        {
            "season": model["reference_season"],
            "model_shot_type": TYPES[0],
            "role": ROLES[0],
            "context": neutral_context,
            "goal": False,
            "shooter_id": pair["shooter_id"],
            "goalie_id": pair["goalie_id"],
        }
        for pair in model["reference"]
    ]
    for name, stage in model["stages"].items():
        data = _encode(reference_rows, stage, [0] * len(reference_rows))
        context["reference_scalar_logits"][name] = _scalar_logits(
            context["stages"][name], stage, data
        )
    return context


def _prediction_data(attempt, layout, h, state):
    row = dict(attempt, season=state)
    return _encode([row], layout, [h])


def reference_probabilities(model, attempt, cell_ids, context):
    """exact target-season pairwise products, in requested cell order."""
    cells = np.asarray(cell_ids)
    if (
        cells.ndim != 1
        or cells.dtype.kind not in ("i", "u")
        or (cells < 0).any()
        or (cells >= len(context["centers"])).any()
    ):
        raise InputContractError("invalid requested reference cells")
    scalar = scalar_features(attempt["context"])
    prefix = (attempt["model_shot_type"], tuple(scalar))
    cache = context["reference_cache"]
    missing = sorted({int(h) for h in cells if (prefix, int(h)) not in cache})
    if missing:
        data = {
            "type": np.full(len(model["reference"]), TYPES.index(attempt["model_shot_type"]))
        }
        scalar_logits = {}
        for name, stage in model["stages"].items():
            offsets = _offsets(stage)
            scalar_logits[name] = context["reference_scalar_logits"][name] + (
                scalar @ context["stages"][name][offsets["scalar"] : offsets["shooter"]]
            )
    for start in range(0, len(missing), BATCH_SIZE):
        hs = np.array(missing[start : start + BATCH_SIZE])
        logits = {
            name: _stage_logits(
                context["stages"][name],
                stage,
                data,
                hs[None, :],
                scalar_logits=scalar_logits[name],
            )
            for name, stage in model["stages"].items()
        }
        values = context["reference_weights"] @ np.exp(
            log_expit(logits["u"]) + log_expit(logits["r"])
        )
        for h, v in zip(hs, values):
            cache[prefix, int(h)] = float(v)
    result = np.array([cache[prefix, int(h)] for h in cells])
    for h in cells:
        cache.move_to_end((prefix, int(h)))
    while len(cache) > REFERENCE_CACHE_CELLS:
        cache.popitem(last=False)
    return result


def predict_attempt(model, attempt, context=None):
    if context is None:
        context = prediction_context(model)
    h = _validate_attempt(attempt, context["centers"])
    basis, state = _season_state(model, attempt)
    logits = {}
    for name in ("u", "r"):
        stage = model["stages"][name]
        data = _prediction_data(attempt, stage, h, state)
        logits[name] = _stage_logits(
            context["stages"][name],
            stage,
            data,
            np.arange(len(context["centers"]))[None, :],
        )[0]
    data = _prediction_data(attempt, model["stages"]["u"], h, state)
    log_pi = (
        _origin_design(data, model["seasons"])
        @ context["origin"].reshape(-1, len(context["centers"]))
    )[0]
    log_pi -= logsumexp(log_pi)
    log_goal = logsumexp(log_pi + log_expit(logits["u"]) + log_expit(logits["r"]))
    log_not_goal = logsumexp(
        log_pi
        + np.logaddexp(
            log_expit(-logits["u"]), log_expit(logits["u"]) + log_expit(-logits["r"])
        )
    )
    log_unblocked = logsumexp(log_pi + log_expit(logits["u"]))
    log_blocked = logsumexp(log_pi + log_expit(-logits["u"]))
    if attempt["blocked"]:
        q, observed = posterior(log_pi, log_expit(-logits["u"]), context["kernel"][h])
    else:
        q = np.zeros(len(context["centers"]))
        q[h] = 1
        observed = (
            log_pi[h]
            + log_expit(logits["u"][h])
            + log_expit(logits["r"][h] if attempt["goal"] else -logits["r"][h])
        )
    result = dict(
        candidate_r=None,
        benchmark_r=None,
        candidate_all=dict(log_p=float(log_goal), log_not_p=float(log_not_goal)),
        candidate_unblocked=dict(
            log_p=float(log_unblocked), log_not_p=float(log_blocked)
        ),
        observed_log_likelihood=float(observed),
        origin_weights=q,
        actor_evidence=actor_evidence(model, attempt, state),
        season_basis=basis,
        state_season=state,
    )
    if not attempt["blocked"]:
        result["candidate_r"] = dict(
            log_p=float(log_expit(logits["r"][h])),
            log_not_p=float(log_expit(-logits["r"][h])),
        )
    for output, name in (
        ("benchmark_r", "unblocked"),
        ("benchmark_all", "all_attempt"),
    ):
        if output == "benchmark_r" and attempt["blocked"]:
            continue
        layout = model["benchmarks"][name]
        data = _prediction_data(attempt, layout, h, state)
        logit = float(
            (
                _benchmark_features(data, layout, context["centers"])
                @ context["benchmarks"][name]
            )[0]
        )
        result[output] = dict(
            log_p=float(log_expit(logit)), log_not_p=float(log_expit(-logit))
        )
    return result


def score_attempt(model, attempt, context):
    prediction = predict_attempt(model, attempt, context)
    weights = prediction["origin_weights"]
    ids = (
        np.arange(len(weights))
        if attempt["blocked"]
        else np.array([int(np.argmax(weights))])
    )
    reference = reference_probabilities(model, attempt, ids, context)
    mass = weights[ids] * reference
    return dict(
        origin_basis="inferred_block" if attempt["blocked"] else "recorded_proxy",
        origin_distribution=[
            dict(cell_id=int(h), weight=float(weights[h]), opportunity_mass=float(v))
            for h, v in zip(ids, mass)
        ],
        reference_opportunity_value=float(mass.sum()),
        actor_evidence=prediction["actor_evidence"],
        season_basis=prediction["season_basis"],
        state_season=prediction["state_season"],
    )
