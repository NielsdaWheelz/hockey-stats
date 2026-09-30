"""bounded latent-origin fitting and fixed-reference opportunity scoring."""

from collections import Counter
from datetime import date
import math

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, log_expit, logsumexp

from .captures import InputContractError
from .shot_origins import cell_id, forward_kernel, grid, posterior

SCORES = ["trailing", "tied", "leading"]
ROLES = ["F", "D", "unknown"]
BATCH_SIZE = 64
CONFIG_FIELDS = {
    "kernel_distance_ft",
    "kernel_direction_strength",
    "origin_pseudocount",
    "ridge_cell",
    "ridge_score",
    "ridge_actor",
    "smooth_cell",
    "ridge_benchmark",
    "optimizer_max_iterations",
    "optimizer_ftol",
    "optimizer_gtol",
    "em_max_iterations",
    "em_relative_tolerance",
    "em_posterior_tolerance",
    "objective_decrease_tolerance",
}


def validate_config(config):
    if not isinstance(config, dict) or set(config) != CONFIG_FIELDS | {"schema_version"}:
        raise InputContractError("candidate configuration keys do not match schema 1")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise InputContractError("unsupported candidate schema")
    for key in CONFIG_FIELDS:
        value = config[key]
        try:
            finite = type(value) in (int, float) and math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            raise InputContractError(f"{key} must be finite numeric data")
        if key.endswith("max_iterations") and type(value) is not int:
            raise InputContractError(f"{key} must be a positive integer")
        if value < 0 or (value == 0 and key not in ("smooth_cell", "kernel_direction_strength")):
            raise InputContractError(f"{key} has invalid sign")
    return config


def _stage_features(cells, shooters, goalies):
    return (
        ["intercept"]
        + [f"cell:{h}" for h in range(cells)]
        + ["score:trailing", "score:leading"]
        + [f"shooter:{a}" for a in shooters]
        + [f"goalie:{a}" for a in goalies]
    )


def _layout(rows, conversion, cells):
    shooters = sorted({row["shooter_id"] for row in rows})
    goalies = sorted({row["goalie_id"] for row in rows}) if conversion else []
    features = _stage_features(cells, shooters, goalies)
    return dict(
        features=features,
        shooters=shooters,
        goalies=goalies,
        cells=cells,
        size=1 + cells + 2 + len(shooters) + len(goalies),
        shooter_counts={str(a): n for a, n in Counter(row["shooter_id"] for row in rows).items()},
        goalie_counts=(
            {str(a): n for a, n in Counter(row["goalie_id"] for row in rows).items()}
            if conversion
            else {}
        ),
    )


def _indices(row, layout):
    score = SCORES.index(row["score"])
    shooter = (
        layout["shooters"].index(row["shooter_id"])
        if row["shooter_id"] in layout["shooters"]
        else -1
    )
    goalie = (
        layout["goalies"].index(row["goalie_id"]) if row["goalie_id"] in layout["goalies"] else -1
    )
    return score, shooter, goalie


def _logits(beta, layout, score, shooter, goalie=-1):
    cells = layout["cells"]
    value = beta[0] + beta[1 : 1 + cells]
    if score != 1:
        value = value + beta[1 + cells + (score == 2)]
    if shooter >= 0:
        value = value + beta[3 + cells + shooter]
    if goalie >= 0:
        value = value + beta[3 + cells + len(layout["shooters"]) + goalie]
    return value


def _penalty(beta, layout, config, edges):
    cells = layout["cells"]
    ridge = np.full(len(beta), config["ridge_actor"], dtype=np.float64)
    ridge[0] = 0
    ridge[1 : 1 + cells] = config["ridge_cell"]
    ridge[1 + cells : 3 + cells] = config["ridge_score"]
    gradient = ridge * beta
    value = 0.5 * np.dot(beta, gradient)
    difference = beta[1 + edges[:, 0]] - beta[1 + edges[:, 1]]
    value += 0.5 * config["smooth_cell"] * np.dot(difference, difference)
    np.add.at(gradient, 1 + edges[:, 0], config["smooth_cell"] * difference)
    np.add.at(gradient, 1 + edges[:, 1], -config["smooth_cell"] * difference)
    return value, gradient


def fit_logistic(objective, initial, config):
    """objective returns summed negative penalized log likelihood and gradient."""
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
    success = bool(result.success and np.isfinite(result.x).all() and np.isfinite(result.fun))
    return result.x, dict(
        converged=success,
        termination=str(result.message),
        iterations=int(result.nit),
        objective=float(result.fun) if np.isfinite(result.fun) else None,
    )


def _fit_data(rows, layout, cell_ids):
    """encode fixed event fields once; arrays retain the supplied event order."""
    shooters = {actor: i for i, actor in enumerate(layout["shooters"])}
    goalies = {actor: i for i, actor in enumerate(layout["goalies"])}
    scores = {score: i for i, score in enumerate(SCORES)}
    roles = {role: i for i, role in enumerate(ROLES)}
    score = np.array([scores[row["score"]] for row in rows], dtype=np.int64)
    data = dict(
        cell=np.asarray(cell_ids, dtype=np.int64),
        score=score,
        shooter=np.array([shooters[row["shooter_id"]] for row in rows], dtype=np.int64),
        stratum=np.array([roles[row["role"]] for row in rows], dtype=np.int64) * 3 + score,
        goal=np.array([row["goal"] for row in rows], dtype=np.bool_),
    )
    if goalies:
        data["goalie"] = np.array([goalies[row["goalie_id"]] for row in rows], dtype=np.int64)
    return data


def _conversion_objective(beta, data, layout, config, edges):
    value, gradient = _penalty(beta, layout, config, edges)
    cells = layout["cells"]
    logits = beta[0] + beta[1 + data["cell"]]
    logits += np.where(
        data["score"] == 0, beta[1 + cells], np.where(data["score"] == 2, beta[2 + cells], 0)
    )
    logits += beta[3 + cells + data["shooter"]]
    logits += beta[3 + cells + len(layout["shooters"]) + data["goalie"]]
    value -= log_expit(np.where(data["goal"], logits, -logits)).sum()
    residual = expit(logits) - data["goal"]
    gradient[0] += residual.sum()
    gradient[1 : 1 + cells] += np.bincount(data["cell"], weights=residual, minlength=cells)
    gradient[1 + cells] += residual[data["score"] == 0].sum()
    gradient[2 + cells] += residual[data["score"] == 2].sum()
    gradient[3 + cells : 3 + cells + len(layout["shooters"])] += np.bincount(
        data["shooter"], weights=residual, minlength=len(layout["shooters"])
    )
    gradient[3 + cells + len(layout["shooters"]) :] += np.bincount(
        data["goalie"], weights=residual, minlength=len(layout["goalies"])
    )
    return float(value), gradient


def _context_logits(beta, groups, layout):
    cells = layout["cells"]
    score_effect = np.where(
        groups[:, 0] == 0, beta[1 + cells], np.where(groups[:, 0] == 2, beta[2 + cells], 0)
    )
    return (
        beta[0]
        + beta[None, 1 : 1 + cells]
        + score_effect[:, None]
        + beta[3 + cells + groups[:, 1], None]
    )


def _block_objective(beta, data, failures, layout, config, edges):
    """frozen fractional counts share one u logit per score/shooter/cell."""
    value, gradient = _penalty(beta, layout, config, edges)
    cells = layout["cells"]
    logits = _context_logits(beta, data["groups"], layout)
    successes = data["successes"]
    value -= (successes * log_expit(logits) + failures * log_expit(-logits)).sum()
    residual = (successes + failures) * expit(logits) - successes
    totals = residual.sum(axis=1)
    gradient[0] += totals.sum()
    gradient[1 : 1 + cells] += residual.sum(axis=0)
    gradient[1 + cells] += totals[data["groups"][:, 0] == 0].sum()
    gradient[2 + cells] += totals[data["groups"][:, 0] == 2].sum()
    gradient[3 + cells :] += np.bincount(
        data["groups"][:, 1], weights=totals, minlength=len(layout["shooters"])
    )
    return float(value), gradient


def _posterior_batch(logits, log_pi, data, kernel, indices):
    return posterior(
        log_pi[data["stratum"][indices]],
        log_expit(-logits[data["context"][indices]]),
        kernel[data["cell"][indices]],
    )


def _expectation(beta, pi, data, layout, config, edges, kernel):
    """aggregate frozen counts; retain at most BATCH_SIZE event posteriors."""
    logits = _context_logits(beta, data["groups"], layout)
    log_pi = np.log(pi)
    failures = np.zeros_like(data["successes"])
    counts = data["unblocked_origins"] + config["origin_pseudocount"] / layout["cells"]
    value = -_penalty(beta, layout, config, edges)[0]
    value += config["origin_pseudocount"] / layout["cells"] * log_pi.sum()
    indices = data["unblocked_rows"]
    value += (
        log_pi[data["stratum"][indices], data["cell"][indices]]
        + log_expit(logits[data["context"][indices], data["cell"][indices]])
    ).sum()
    for start in range(0, len(data["blocked_rows"]), BATCH_SIZE):
        indices = data["blocked_rows"][start : start + BATCH_SIZE]
        weights, likelihood = _posterior_batch(logits, log_pi, data, kernel, indices)
        np.add.at(failures, data["context"][indices], weights)
        np.add.at(counts, data["stratum"][indices], weights)
        value += likelihood.sum()
    next_pi = counts / (data["stratum_counts"][:, None] + config["origin_pseudocount"])
    return failures, next_pi, float(value)


def _fit_resume(resume, layout, config):
    """decode only accepted current state and terminal starts; never inner solver state."""
    if resume is None:
        return {}, None
    names = ["uniform", "unblocked_frequency"]
    try:
        if (
            not isinstance(resume, dict)
            or set(resume) != {"schema_version", "completed_starts", "current_start"}
            or type(resume["schema_version"]) is not int
            or resume["schema_version"] != 1
        ):
            raise ValueError("unsupported numerical state schema")
        completed, current = resume["completed_starts"], resume["current_start"]
        if not isinstance(completed, dict) or list(completed) != names[: len(completed)]:
            raise ValueError("completed starts must follow the fixed start order")
        if current is not None and (
            len(completed) == len(names)
            or not isinstance(current, dict)
            or current.get("name") != names[len(completed)]
        ):
            raise ValueError("current start must follow completed starts")
        for record, active in [(record, False) for record in completed.values()] + (
            [(current, True)] if current is not None else []
        ):
            fields = {"coefficients", "origin_probabilities", "diagnostics"}
            if not isinstance(record, dict) or set(record) != fields | ({"name"} if active else set()):
                raise ValueError("start state fields disagree")
            _numeric_array(record["coefficients"], (layout["size"],))
            pi = _numeric_array(record["origin_probabilities"], (9, layout["cells"]))
            if (pi <= 0).any() or not np.allclose(pi.sum(axis=1), 1, rtol=0, atol=1e-12):
                raise ValueError("origin probabilities must be positive and normalized")
            diag = record["diagnostics"]
            fields = {"converged", "termination", "objective_history", "inner", "iterations"}
            if not isinstance(diag, dict) or set(diag) not in (
                fields, fields | {"maximum_posterior_change"}
            ):
                raise ValueError("start diagnostics fields disagree")
            n = diag["iterations"]
            term = diag["termination"]
            inner, history = diag["inner"], diag["objective_history"]
            if (
                type(n) is not int or not 0 <= n <= config["em_max_iterations"]
                or type(diag["converged"]) is not bool
                or not isinstance(inner, list) or len(inner) != n
                or not isinstance(history, list)
                or term not in ("converged", "em iteration limit", "inner optimization failed",
                                "nonfinite initial observed objective", "nonfinite observed objective",
                                "observed objective decreased")
                or diag["converged"] != (term == "converged")
            ):
                raise ValueError("start termination or iteration budget disagrees")
            for i, result in enumerate(inner):
                if (
                    not isinstance(result, dict)
                    or set(result) != {"converged", "termination", "iterations", "objective"}
                    or type(result["converged"]) is not bool
                    or result["converged"] != (term != "inner optimization failed" or i < n - 1)
                    or not isinstance(result["termination"], str)
                    or type(result["iterations"]) is not int or result["iterations"] < 0
                    or result["objective"] is not None and (
                        type(result["objective"]) not in (int, float)
                        or not math.isfinite(result["objective"])
                    )
                    or result["converged"] and result["objective"] is None
                ):
                    raise ValueError("inner optimization diagnostics disagree")
            if term == "nonfinite initial observed objective":
                valid_history = n == 0 and history == [None]
                accepted = 0
            else:
                accepted = n - (term in ("inner optimization failed", "nonfinite observed objective", "observed objective decreased"))
                valid_history = n > 0 and len(history) == n + (term != "inner optimization failed")
                for i, value in enumerate(history):
                    valid_history = valid_history and (
                        value is None if term == "nonfinite observed objective" and i == len(history) - 1
                        else type(value) in (int, float) and math.isfinite(value)
                    )
            if not valid_history or ("maximum_posterior_change" in diag) != (accepted > 0):
                raise ValueError("history does not describe accepted updates and terminal attempts")
            if accepted > 0:
                change = diag["maximum_posterior_change"]
                if type(change) not in (int, float) or not math.isfinite(change) or not 0 <= change <= 1:
                    raise ValueError("maximum posterior change is invalid")
            if term == "em iteration limit" and (
                active and n >= config["em_max_iterations"]
                or not active and n != config["em_max_iterations"]
            ) or active and term != "em iteration limit":
                raise ValueError("current state must be accepted, nonterminal and within its budget")
        return completed.copy(), current
    except (ValueError, TypeError, OverflowError) as error:
        raise InputContractError(f"invalid fit checkpoint state: {error}") from error


def _em(data, layout, config, edges, kernel, initial_pi, initial_beta, conversion_objective,
        resume=None, checkpoint=None):
    if resume is None:
        pi, beta = initial_pi.copy(), initial_beta.copy()
        diagnostics = dict(
            converged=False, termination="em iteration limit", objective_history=[], inner=[]
        )
    else:
        pi = np.asarray(resume["origin_probabilities"], dtype=np.float64)
        beta = np.asarray(resume["coefficients"], dtype=np.float64)
        diagnostics = dict(
            resume["diagnostics"],
            objective_history=resume["diagnostics"]["objective_history"].copy(),
            inner=resume["diagnostics"]["inner"].copy(),
        )
    failures, next_pi, objective = _expectation(beta, pi, data, layout, config, edges, kernel)
    history = diagnostics["objective_history"]
    if resume is None:
        history.append(objective - conversion_objective)
    if not np.isfinite(history[0]):
        history[0] = None
        diagnostics.update(termination="nonfinite initial observed objective", iterations=0)
        return beta, pi, diagnostics
    for _ in range(len(diagnostics["inner"]), config["em_max_iterations"]):
        next_beta, inner = fit_logistic(
            lambda trial: _block_objective(trial, data, failures, layout, config, edges),
            beta,
            config,
        )
        diagnostics["inner"].append(inner)
        if not inner["converged"]:
            diagnostics["termination"] = "inner optimization failed"
            break
        next_failures, following_pi, objective = _expectation(
            next_beta, next_pi, data, layout, config, edges, kernel
        )
        objective -= conversion_objective
        history.append(objective if np.isfinite(objective) else None)
        if not np.isfinite(objective):
            diagnostics["termination"] = "nonfinite observed objective"
            break
        change = objective - history[-2]
        scale = max(1.0, abs(history[-2]))
        if change < -config["objective_decrease_tolerance"] * scale:
            diagnostics["termination"] = "observed objective decreased"
            break
        posterior_change = 0.0
        old_logits = _context_logits(beta, data["groups"], layout)
        new_logits = _context_logits(next_beta, data["groups"], layout)
        old_log_pi, new_log_pi = np.log(pi), np.log(next_pi)
        for start in range(0, len(data["blocked_rows"]), BATCH_SIZE):
            indices = data["blocked_rows"][start : start + BATCH_SIZE]
            old, _ = _posterior_batch(old_logits, old_log_pi, data, kernel, indices)
            new, _ = _posterior_batch(new_logits, new_log_pi, data, kernel, indices)
            posterior_change = max(posterior_change, float(np.max(np.abs(old - new))))
        beta, pi = next_beta, next_pi
        failures, next_pi = next_failures, following_pi
        diagnostics.update(
            maximum_posterior_change=posterior_change, iterations=len(diagnostics["inner"])
        )
        if (
            abs(change) / scale < config["em_relative_tolerance"]
            and posterior_change < config["em_posterior_tolerance"]
        ):
            diagnostics.update(converged=True, termination="converged")
            break
        if (
            checkpoint is not None
            and diagnostics["iterations"] < config["em_max_iterations"]
            and diagnostics["iterations"] % 25 == 0
        ):
            checkpoint(beta, pi, diagnostics)
    diagnostics["iterations"] = len(diagnostics["inner"])
    return beta, pi, diagnostics


def _benchmark_features(row, centers, unblocked, h):
    if unblocked:
        x, y = centers[h]
        return np.array([1.0, math.hypot(89 - x, y) / 100, math.atan2(abs(y), 89 - x) / math.pi])
    return np.array(
        [
            1.0,
            row["score"] == "trailing",
            row["score"] == "leading",
            row["role"] == "D",
            row["role"] == "unknown",
        ],
        dtype=np.float64,
    )


def _benchmark(rows, cell_ids, centers, config, unblocked):
    size = 3 if unblocked else 5
    initial = np.zeros(size)
    targets = np.array([row["goal"] for row in rows], dtype=np.bool_)
    features = np.array(
        [_benchmark_features(row, centers, unblocked, h) for row, h in zip(rows, cell_ids)]
    )
    proportion = targets.sum() / len(rows)
    initial[0] = math.log(proportion / (1 - proportion))

    def objective(beta):
        gradient = config["ridge_benchmark"] * beta.copy()
        gradient[0] = 0
        value = 0.5 * config["ridge_benchmark"] * np.dot(beta[1:], beta[1:])
        logits = features @ beta
        value -= log_expit(np.where(targets, logits, -logits)).sum()
        gradient += features.T @ (expit(logits) - targets)
        return float(value), gradient

    beta, diag = fit_logistic(objective, initial, config)
    return dict(
        coefficients=beta.tolist(),
        diagnostics=diag,
        features=(
            ["intercept", "distance_to_goal/100", "angle/pi"]
            if unblocked
            else ["intercept", "score:trailing", "score:leading", "role:D", "role:unknown"]
        ),
    )


def fit_model(attempts, config, metadata, *, resume=None, checkpoint=None):
    """fit fixed starts; resume/checkpoint carry opaque accepted numerical state."""
    validate_config(config)
    rows = list(attempts)
    centers, edges = grid()
    cell_ids = np.array([_validate_attempt(row, centers) for row in rows], dtype=np.int64)
    blocked = np.array([row["blocked"] for row in rows], dtype=np.bool_)
    unblocked = [row for row in rows if not row["blocked"]]
    diagnostics = dict(
        status="failed", chosen_start=None, starts={}, scientific_assessment="not_performed"
    )
    u_layout = _layout(rows, False, len(centers))
    r_layout = _layout(unblocked, True, len(centers))
    diagnostics["actor_counts"] = dict(u=u_layout, r=r_layout)
    completed, current = _fit_resume(resume, u_layout, config)
    if resume is not None and checkpoint is not None:
        checkpoint(dict(schema_version=1, completed_starts=completed.copy(), current_start=current))
    goals = sum(row["goal"] for row in unblocked)
    if not unblocked or not goals or goals == len(unblocked) or len(unblocked) == len(rows):
        diagnostics["termination"] = (
            "training requires blocks, unblocked goals and unblocked non-goals"
        )
        return None, diagnostics
    u_data = _fit_data(rows, u_layout, cell_ids)
    r_data = _fit_data(unblocked, r_layout, cell_ids[~blocked])
    # role affects the origin prior; u logits share only score and shooter.
    u_data["groups"], u_data["context"] = np.unique(
        np.column_stack((u_data["score"], u_data["shooter"])), axis=0, return_inverse=True
    )
    u_data["blocked_rows"] = np.flatnonzero(blocked)
    u_data["unblocked_rows"] = np.flatnonzero(~blocked)
    u_data["stratum_counts"] = np.bincount(u_data["stratum"], minlength=9)
    u_data["successes"] = np.zeros((len(u_data["groups"]), len(centers)))
    np.add.at(u_data["successes"], (u_data["context"][~blocked], cell_ids[~blocked]), 1)
    u_data["unblocked_origins"] = np.zeros((9, len(centers)))
    np.add.at(u_data["unblocked_origins"], (u_data["stratum"][~blocked], cell_ids[~blocked]), 1)
    r_initial = np.zeros(r_layout["size"])
    r_initial[0] = math.log(goals / (len(unblocked) - goals))
    r_beta, r_diag = fit_logistic(
        lambda trial: _conversion_objective(trial, r_data, r_layout, config, edges),
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
    pi_uniform = np.full((9, len(centers)), 1 / len(centers))
    pi_empirical = u_data["unblocked_origins"] + config["origin_pseudocount"] / len(centers)
    pi_empirical /= pi_empirical.sum(axis=1, keepdims=True)
    u_initial = np.zeros(u_layout["size"])
    u_initial[0] = math.log(len(unblocked) / (len(rows) - len(unblocked)))
    chosen = None
    for name, initial in [("uniform", pi_uniform), ("unblocked_frequency", pi_empirical)]:
        if name in completed:
            record = completed[name]
            beta = np.asarray(record["coefficients"], dtype=np.float64)
            pi = np.asarray(record["origin_probabilities"], dtype=np.float64)
            diag = record["diagnostics"]
        else:
            def save_current(beta, pi, diag):
                checkpoint(dict(
                    schema_version=1, completed_starts=completed.copy(),
                    current_start=dict(name=name, coefficients=beta.tolist(),
                                       origin_probabilities=pi.tolist(), diagnostics=dict(
                                           diag, objective_history=diag["objective_history"].copy(),
                                           inner=diag["inner"].copy(),
                                       )),
                ))

            beta, pi, diag = _em(
                u_data, u_layout, config, edges, kernel, initial, u_initial, r_diag["objective"],
                resume=current, checkpoint=save_current if checkpoint is not None else None,
            )
            completed[name] = dict(
                coefficients=beta.tolist(), origin_probabilities=pi.tolist(), diagnostics=diag
            )
            current = None
            if checkpoint is not None:
                checkpoint(dict(schema_version=1, completed_starts=completed.copy(), current_start=None))
        diagnostics["starts"][name] = diag
        if diag["converged"] and (chosen is None or diag["objective_history"][-1] > chosen[3]):
            chosen = (name, beta, pi, diag["objective_history"][-1])
    if chosen is None:
        diagnostics["termination"] = "no em start converged"
        return None, diagnostics
    benchmarks = dict(
        unblocked=_benchmark(unblocked, cell_ids[~blocked], centers, config, True),
        all_attempt=_benchmark(rows, cell_ids, centers, config, False),
    )
    diagnostics["benchmarks"] = {key: value["diagnostics"] for key, value in benchmarks.items()}
    if not all(value["diagnostics"]["converged"] for value in benchmarks.values()):
        diagnostics["termination"] = "benchmark optimizer failed"
        return None, diagnostics
    pairs = Counter((row["shooter_id"], row["goalie_id"]) for row in rows)
    diagnostics.update(status="fitted", chosen_start=chosen[0], termination="converged")
    model = dict(metadata)
    model["training_game_ids"] = list(model["training_game_dates"])
    model["training_dates"] = sorted(set(model["training_game_dates"].values()))
    model.update(
        schema_version=1,
        model_kind="chance-1",
        config=dict(config),
        grid=dict(centers=centers.tolist(), neighbors=edges.tolist()),
        score_order=SCORES.copy(),
        role_order=ROLES.copy(),
        origin_strata=[[role, score] for role in ROLES for score in SCORES],
        stages=dict(
            u=dict(u_layout, coefficients=chosen[1].tolist()),
            r=dict(r_layout, coefficients=r_beta.tolist()),
        ),
        origin_probabilities=chosen[2].tolist(),
        kernel=dict(
            distance_ft=config["kernel_distance_ft"],
            direction_strength=config["kernel_direction_strength"],
        ),
        reference=[
            dict(shooter_id=s, goalie_id=g, weight=n / len(rows), count=n)
            for (s, g), n in sorted(pairs.items())
        ],
        benchmarks=benchmarks,
        diagnostics=diagnostics,
        scientific_assessment="not_performed",
    )
    validate_model(model)
    return model, diagnostics


def _validate_attempt(row, centers):
    if not isinstance(row, dict) or row.get("score") not in SCORES or row.get("role") not in ROLES:
        raise InputContractError("attempt requires supported score and role")
    if any(type(row.get(key)) is not int or row[key] <= 0 for key in ("shooter_id", "goalie_id")):
        raise InputContractError("attempt requires actor identities")
    if (
        type(row.get("blocked")) is not bool
        or type(row.get("goal")) is not bool
        or (row["blocked"] and row["goal"])
    ):
        raise InputContractError("invalid attempt outcomes")
    return cell_id([row.get("attacking_x"), row.get("attacking_y")], centers)


def _numeric_array(value, shape):
    def finite_numbers(data):
        if isinstance(data, list):
            return all(finite_numbers(item) for item in data)
        return type(data) in (int, float) and math.isfinite(data)

    if not isinstance(value, list) or not finite_numbers(value):
        raise ValueError("arrays require finite json numbers")
    result = np.asarray(value, dtype=np.float64)
    if result.shape != shape:
        raise ValueError("array dimensions disagree")
    return result


def validate_model(model):
    """reject unsupported or inconsistent numerical artifacts before prediction."""
    try:
        if not isinstance(model, dict):
            raise ValueError("model must be an object")
        if (
            type(model["schema_version"]) is not int
            or model["schema_version"] != 1
            or model["model_kind"] != "chance-1"
        ):
            raise ValueError("unsupported model version")
        if model["purpose"] not in ("fixture_exercise", "research"):
            raise ValueError("unsupported purpose")
        validate_config(model["config"])
        centers, edges = grid()
        saved_centers = _numeric_array(model["grid"]["centers"], centers.shape)
        saved_edges = _numeric_array(model["grid"]["neighbors"], edges.shape)
        if not np.array_equal(saved_centers, centers) or not np.array_equal(saved_edges, edges):
            raise ValueError("grid differs from chance-1")
        if (
            model["score_order"] != SCORES
            or model["role_order"] != ROLES
            or model["origin_strata"] != [[r, s] for r in ROLES for s in SCORES]
        ):
            raise ValueError("category order differs from chance-1")
        pi = _numeric_array(model["origin_probabilities"], (9, len(centers)))
        if (pi <= 0).any() or not np.allclose(pi.sum(axis=1), 1, atol=1e-10, rtol=0):
            raise ValueError("invalid origin mass")
        for name in ("u", "r"):
            stage = model["stages"][name]
            if (
                type(stage["cells"]) is not int
                or type(stage["size"]) is not int
                or stage["cells"] != len(centers)
                or stage["size"]
                != 3 + len(centers) + len(stage["shooters"]) + len(stage["goalies"])
            ):
                raise ValueError("invalid stage dimensions")
            if name == "u" and stage["goalies"]:
                raise ValueError("block stage cannot contain goalies")
            for actors, counts in [("shooters", "shooter_counts"), ("goalies", "goalie_counts")]:
                ids = stage[actors]
                if not isinstance(ids, list) or not isinstance(stage[counts], dict):
                    raise ValueError("actor order/counts require array/object")
                if (
                    any(type(a) is not int or a <= 0 for a in ids)
                    or len(set(ids)) != len(ids)
                    or set(stage[counts]) != {str(a) for a in ids}
                ):
                    raise ValueError("invalid actor identities/counts")
                if any(type(n) is not int or n <= 0 for n in stage[counts].values()):
                    raise ValueError("invalid actor evidence")
            expected_features = _stage_features(len(centers), stage["shooters"], stage["goalies"])
            if stage["features"] != expected_features:
                raise ValueError("stage coefficient order disagrees")
            beta = _numeric_array(stage["coefficients"], (stage["size"],))
            if beta.shape != (stage["size"],) or not np.isfinite(beta).all():
                raise ValueError("invalid coefficients")
        if model["kernel"] != dict(
            distance_ft=model["config"]["kernel_distance_ft"],
            direction_strength=model["config"]["kernel_direction_strength"],
        ):
            raise ValueError("kernel/config mismatch")
        pairs = model["reference"]
        identities = [(p["shooter_id"], p["goalie_id"]) for p in pairs]
        if not pairs or len(set(identities)) != len(pairs):
            raise ValueError("invalid reference identities")
        if any(type(p["count"]) is not int or p["count"] <= 0 for p in pairs):
            raise ValueError("invalid reference counts")
        total = sum(p["count"] for p in pairs)
        for p in pairs:
            if (
                p["shooter_id"] not in model["stages"]["u"]["shooters"]
                or type(p["goalie_id"]) is not int
                or p["goalie_id"] <= 0
            ):
                raise ValueError("reference actor mismatch")
            if (
                type(p["count"]) is not int
                or p["count"] <= 0
                or type(p["weight"]) not in (int, float)
                or not math.isfinite(p["weight"])
                or abs(p["weight"] - p["count"] / total) > 1e-10
            ):
                raise ValueError("invalid reference weight")
        if abs(sum(p["weight"] for p in pairs) - 1) > 1e-10:
            raise ValueError("reference weights not normalized")
        u = model["stages"]["u"]
        r = model["stages"]["r"]
        if total != sum(u["shooter_counts"].values()):
            raise ValueError("reference and block-stage counts disagree")
        if (
            sum(r["shooter_counts"].values()) != sum(r["goalie_counts"].values())
            or not 0 < sum(r["shooter_counts"].values()) < total
        ):
            raise ValueError("conversion-stage evidence totals disagree")
        if {
            str(a): sum(p["count"] for p in pairs if p["shooter_id"] == a) for a in u["shooters"]
        } != u["shooter_counts"]:
            raise ValueError("reference shooter counts disagree")
        if not set(r["shooters"]).issubset(u["shooters"]):
            raise ValueError("conversion actors lack block-stage evidence")
        for actor, counts in [("shooters", "shooter_counts"), ("goalies", "goalie_counts")]:
            for a in r[actor]:
                key = "shooter_id" if actor == "shooters" else "goalie_id"
                if r[counts][str(a)] > sum(p["count"] for p in pairs if p[key] == a):
                    raise ValueError("conversion evidence exceeds reference evidence")
        for name, size in [("unblocked", 3), ("all_attempt", 5)]:
            benchmark = model["benchmarks"][name]
            beta = _numeric_array(benchmark["coefficients"], (size,))
            expected_features = (
                ["intercept", "distance_to_goal/100", "angle/pi"]
                if name == "unblocked"
                else ["intercept", "score:trailing", "score:leading", "role:D", "role:unknown"]
            )
            if (
                benchmark["features"] != expected_features
                or benchmark["diagnostics"]["converged"] is not True
            ):
                raise ValueError("invalid benchmark")
        dates = model["training_game_dates"]
        if not isinstance(dates, dict):
            raise ValueError("training dates must be an object")
        ids = list(dates)
        if (
            len(set(ids)) != len(ids)
            or any(not isinstance(x, str) or len(x) != 10 or not x.isdigit() for x in ids)
            or not dates
        ):
            raise ValueError("invalid training identities")
        for value in dates.values():
            if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                raise ValueError("invalid training calendar date")
        if model["training_game_ids"] != ids or model["training_dates"] != sorted(
            set(dates.values())
        ):
            raise ValueError("training dates and identities disagree")
        implementation = model["implementation"]
        if not isinstance(implementation, dict) or any(
            not isinstance(implementation[key], str) or not implementation[key]
            for key in ("python_version", "numpy_version", "scipy_version")
        ):
            raise ValueError("missing implementation versions")
        digest = implementation["lockfile_sha256"]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(c not in "0123456789abcdef" for c in digest)
        ):
            raise ValueError("invalid lockfile identity")
        inputs = model["inputs"]
        if not isinstance(inputs, list) or not inputs:
            raise ValueError("missing input identities")
        for identity in [model["config_identity"], *inputs]:
            if (
                not isinstance(identity, dict)
                or not isinstance(identity["path"], str)
                or not identity["path"]
            ):
                raise ValueError("missing input identity path")
            digest = identity["sha256"]
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)
            ):
                raise ValueError("invalid input digest")
        selection = model["selection"]
        if (
            not isinstance(selection, dict)
            or type(selection["schema_version"]) is not int
            or selection["schema_version"] != 1
            or selection["purpose"] != model["purpose"]
            or not isinstance(selection["corpora"], list)
            or not selection["corpora"]
        ):
            raise ValueError("invalid training selection")
        selected = []
        for corpus in selection["corpora"]:
            if (
                not isinstance(corpus["path"], str)
                or not corpus["path"]
                or not isinstance(corpus["game_ids"], list)
                or not corpus["game_ids"]
            ):
                raise ValueError("invalid selected corpus")
            selected.extend(corpus["game_ids"])
        if len(set(selected)) != len(selected) or set(selected) != set(ids):
            raise ValueError("selection/training ids disagree")
        if model["scientific_assessment"] != "not_performed":
            raise ValueError("unsupported scientific assessment claim")
        diag = model["diagnostics"]
        chosen = diag["starts"][diag["chosen_start"]]
        if chosen["converged"] is not True or diag["r"]["converged"] is not True:
            raise ValueError("model stages did not converge")
        if not chosen["objective_history"] or any(
            type(v) not in (int, float) or not math.isfinite(v) for v in chosen["objective_history"]
        ):
            raise ValueError("invalid observed objective history")
        for numerical in [
            diag["r"],
            *chosen["inner"],
            *[b["diagnostics"] for b in model["benchmarks"].values()],
        ]:
            if (
                numerical["converged"] is not True
                or type(numerical["objective"]) not in (int, float)
                or not math.isfinite(numerical["objective"])
            ):
                raise ValueError("invalid inner numerical result")
        if model["diagnostics"]["status"] != "fitted" or model["diagnostics"][
            "chosen_start"
        ] not in ("uniform", "unblocked_frequency"):
            raise ValueError("model has no successful fit")
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


def reference_probabilities(model):
    centers, _ = grid()
    result = np.zeros((3, len(centers)), dtype=np.float64)
    for start in range(0, len(model["reference"]), BATCH_SIZE):
        for pair in model["reference"][start : start + BATCH_SIZE]:
            row = dict(score="tied", shooter_id=pair["shooter_id"], goalie_id=pair["goalie_id"])
            for score in range(3):
                logits = []
                for name in ("u", "r"):
                    stage = model["stages"][name]
                    _, s, g = _indices(row, stage)
                    logits.append(_logits(np.asarray(stage["coefficients"]), stage, score, s, g))
                result[score] += pair["weight"] * np.exp(
                    log_expit(logits[0]) + log_expit(logits[1])
                )
    return result


def actor_evidence(model, row):
    result = {}
    for name in ("u", "r"):
        stage = model["stages"][name]
        result[name] = {}
        for actor, counts in [("shooter", "shooter_counts"), ("goalie", "goalie_counts")]:
            if name == "u" and actor == "goalie":
                continue
            count = stage[counts].get(str(row[actor + "_id"]), 0)
            result[name][actor] = dict(
                count=count,
                basis="seen" if count else "unseen",
                coefficient_basis="fitted" if count else "penalty_prior_mode",
            )
    return result


def prediction_context(model):
    """prepare an opaque reusable numerical context; never mutate the saved model."""
    centers, _ = grid()
    return dict(
        centers=centers,
        kernel=forward_kernel(
            centers, model["kernel"]["distance_ft"], model["kernel"]["direction_strength"]
        ),
    )


def predict_attempt(model, attempt, context=None):
    """return stable nested predictors and record likelihood; r predictors are null for blocks.

    context is an opaque numerical dictionary from prediction_context, reused per run.
    """
    if context is None:
        context = prediction_context(model)
    centers = context["centers"]
    h = _validate_attempt(attempt, centers)
    score = SCORES.index(attempt["score"])
    z = ROLES.index(attempt["role"]) * 3 + score
    logits = {}
    for name in ("u", "r"):
        stage = model["stages"][name]
        _, s, g = _indices(attempt, stage)
        logits[name] = _logits(np.asarray(stage["coefficients"]), stage, score, s, g)
    log_pi = np.log(np.asarray(model["origin_probabilities"])[z])
    log_normalizer = logsumexp(log_pi)
    log_goal = logsumexp(log_pi + log_expit(logits["u"]) + log_expit(logits["r"])) - log_normalizer
    # 1-u*r = (1-u) + u*(1-r), avoiding subtraction of rounded probabilities.
    log_not_goal = (
        logsumexp(
            log_pi
            + np.logaddexp(
                log_expit(-logits["u"]), log_expit(logits["u"]) + log_expit(-logits["r"])
            )
        )
        - log_normalizer
    )
    if attempt["blocked"]:
        q, observed = posterior(log_pi, log_expit(-logits["u"]), context["kernel"][h])
    else:
        q = np.zeros(len(centers))
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
        observed_log_likelihood=float(observed),
        origin_weights=q,
        actor_evidence=actor_evidence(model, attempt),
    )
    if not attempt["blocked"]:
        result["candidate_r"] = dict(
            log_p=float(log_expit(logits["r"][h])), log_not_p=float(log_expit(-logits["r"][h]))
        )
    for name, unblocked in [("benchmark_r", True), ("benchmark_all", False)]:
        if unblocked and attempt["blocked"]:
            continue
        benchmark = "unblocked" if unblocked else "all_attempt"
        logit = float(
            np.dot(
                _benchmark_features(attempt, centers, unblocked, h),
                model["benchmarks"][benchmark]["coefficients"],
            )
        )
        result[name] = dict(log_p=float(log_expit(logit)), log_not_p=float(log_expit(-logit)))
    return result


def score_attempt(model, attempt, reference=None, context=None):
    prediction = predict_attempt(model, attempt, context)
    if reference is None:
        reference = reference_probabilities(model)
    weights = prediction["origin_weights"]
    mass = weights * reference[SCORES.index(attempt["score"])]
    indices = range(len(weights)) if attempt["blocked"] else [int(np.argmax(weights))]
    return dict(
        origin_basis="inferred_block" if attempt["blocked"] else "recorded_proxy",
        origin_distribution=[
            dict(cell_id=int(h), weight=float(weights[h]), opportunity_mass=float(mass[h]))
            for h in indices
        ],
        reference_opportunity_value=float(mass.sum()),
        actor_evidence=prediction["actor_evidence"],
    )
