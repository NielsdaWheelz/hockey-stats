"""annual execution likelihoods, native penalties and deterministic setter em."""

from time import perf_counter

import numpy as np
from scipy.special import expit, log_expit

from .chance import _map_penalty, solve_logistic


def annual_priors(design, ledger):
    """bind raw last-supported history; returning means receive no level ridge."""
    previous = {(row["block"], str(row["id"])): row for row in ledger}
    actors = []
    for source in design["actors"]:
        actor = dict(source)
        block = actor["block"]
        entry, carry = ((16., 64.) if block == "goalie" else
                        (256., 1024.) if block in ("attacking_coach", "defending_coach")
                        else (4., 16.))
        last = previous.get((block, str(actor["id"])))
        actor.update(mean=0. if last is None else last["coefficient"],
                     precision=entry if last is None else carry,
                     prior_only=not bool(actor["likelihood_support"]),
                     age_delta=[], age_indices=[],
                     transition_reason="entry" if last is None else "age_neutral")
        if last is not None and block not in ("attacking_coach", "defending_coach"):
            role = actor["role"]
            if role not in ("F", "D", "G") or last["role"] != role:
                actor["transition_reason"] = "missing_or_changed_role"
            elif actor["age"] is None or last["age"] is None:
                actor["transition_reason"] = "missing_age"
            else:
                current = (actor["age"] - 27.) / 10.
                earlier = (last["age"] - 27.) / 10.
                actor.update(age_delta=[current-earlier, current**2-earlier**2],
                             age_indices=design["age_indices_by_block_role"][block][role],
                             transition_reason="age_carry")
        actors.append(actor)
    return actors


def prior_mean(actor, beta):
    return float(actor["mean"] + np.dot(actor["age_delta"], beta[actor["age_indices"]]))


def penalty(beta, design, actors):
    """expand mirror ties before the original native-grid penalty."""
    gradient = np.zeros_like(beta)
    maps = np.asarray(design["map_indices"], dtype=np.int64)
    value, native_gradient = _map_penalty(
        beta[maps].ravel(), maps.shape[1], np.array([.25, 1., 1., 1., 1., 1.]),
        4., np.asarray(design["native_neighbors"], dtype=np.int64),
    )
    np.add.at(gradient, maps.ravel(), native_gradient)
    for indices, precision in ((design["circumstance_indices"], 4.),
                               (design["age_indices"], 64.)):
        indices = np.asarray(indices, dtype=np.int64)
        value += .5 * precision * np.dot(beta[indices], beta[indices])
        gradient[indices] += precision * beta[indices]
    for actor in actors:
        # profiling a zero-likelihood actor removes its quadratic exactly.
        if not actor["likelihood_support"]:
            continue
        difference = beta[actor["index"]] - prior_mean(actor, beta)
        scaled = actor["precision"] * difference
        value += .5 * difference * scaled
        gradient[actor["index"]] += scaled
        gradient[actor["age_indices"]] -= scaled * np.asarray(actor["age_delta"])
    return float(value), gradient


def setter_logits(beta, design, batch):
    """unknown/goalie setting uses the current, differentiable skater mean."""
    offsets = batch["offsets"]
    setter = batch["setter_index"]
    rows = np.repeat(np.arange(len(offsets)-1), np.diff(offsets))
    logits = np.asarray(batch["matrix"] @ beta).ravel()[rows]
    setup = setter != -1
    logits[setup] += beta[design["setup_index"]]
    known = setter >= 0
    logits[known] += beta[setter[known]]
    unknown = setter == -2
    logits[unknown] += np.dot(beta[design["setter_mean_indices"]],
                              design["setter_mean_weights"])
    return logits, rows


def setter_responsibilities(beta, design, batch):
    """return exact observed log likelihoods and posterior branch mass."""
    logits, rows = setter_logits(beta, design, batch)
    targets = design["target"][batch["row"]]
    log_joint = np.log(batch["prior"]) + log_expit((2*targets[rows]-1)*logits)
    offsets = batch["offsets"]
    starts = offsets[:-1]
    maxima = np.maximum.reduceat(log_joint, starts)
    normalizer = maxima + np.log(np.add.reduceat(np.exp(log_joint-maxima[rows]), starts))
    posterior = np.exp(log_joint-normalizer[rows])
    known_rows = np.flatnonzero(batch["observed"] >= 0)
    if len(known_rows):
        positions = starts[known_rows] + batch["observed"][known_rows]
        normalizer[known_rows] = log_joint[positions]
        known_mask = np.zeros(len(starts), dtype=bool)
        known_mask[known_rows] = True
        posterior[known_mask[rows]] = 0.
        posterior[positions] = 1.
    return normalizer, posterior


def _setter_gradient(beta, design, batch, posterior):
    logits, rows = setter_logits(beta, design, batch)
    targets = design["target"][batch["row"]][rows]
    weights = batch["weight"][rows] * posterior
    value = -np.dot(weights, log_expit((2*targets-1)*logits))
    residual = weights * (expit(logits)-targets)
    row_residual = np.add.reduceat(residual, batch["offsets"][:-1])
    gradient = np.asarray(batch["matrix"].T @ row_residual).ravel()
    setter = batch["setter_index"]
    gradient[design["setup_index"]] += np.sum(residual[setter != -1])
    known = setter >= 0
    np.add.at(gradient, setter[known], residual[known])
    gradient[design["setter_mean_indices"]] += (
        np.sum(residual[setter == -2]) * design["setter_mean_weights"]
    )
    return float(value), gradient


def objective(beta, design, actors, responsibilities=None):
    """weighted sum of origin log losses, never a log of averaged origins."""
    value, gradient = penalty(beta, design, actors)
    for number, batch in enumerate(design["batches"]()):
        if design["head"] == "g":
            if responsibilities is None:
                log_likelihood, posterior = setter_responsibilities(beta, design, batch)
                _, partial = _setter_gradient(beta, design, batch, posterior)
                value -= np.dot(batch["weight"], log_likelihood)
            else:
                loss, partial = _setter_gradient(beta, design, batch, responsibilities[number])
                value += loss
            gradient += partial
        else:
            logits = np.asarray(batch["matrix"] @ beta).ravel()
            targets = design["target"][batch["row"]]
            value -= np.dot(batch["weight"], log_expit((2*targets-1)*logits))
            gradient += np.asarray(batch["matrix"].T @ (
                batch["weight"] * (expit(logits)-targets)
            )).ravel()
    return float(value), gradient


def _complete_prior_only(beta, actors):
    result = beta.copy()
    for actor in actors:
        if not actor["likelihood_support"]:
            result[actor["index"]] = prior_mean(actor, result)
    return result


def head_diagnostics(beta, design):
    """in-sample probabilities use pre-outcome branches and count attempts once."""
    target = design["target"]
    probabilities = np.zeros(len(target))
    mass = np.zeros(len(target))
    likelihood_loss = 0.
    outcome_loss = 0.
    expanded_rows = candidate_branches = nonzeros = batches = 0
    for batch in design["batches"]():
        batches += 1
        expanded_rows += len(batch["row"])
        nonzeros += batch["matrix"].nnz
        if design["head"] == "g":
            logits, _ = setter_logits(beta, design, batch)
            predicted = np.add.reduceat(batch["prior"] * expit(logits), batch["offsets"][:-1])
            log_likelihood, _ = setter_responsibilities(beta, design, batch)
            outcome_batch = dict(batch, observed=np.full(len(batch["row"]), -1, dtype=np.int64))
            outcome_log_likelihood, _ = setter_responsibilities(beta, design, outcome_batch)
            candidate_branches += len(logits)
        else:
            logits = np.asarray(batch["matrix"] @ beta).ravel()
            predicted = expit(logits)
            log_likelihood = log_expit((2*target[batch["row"]]-1)*logits)
            outcome_log_likelihood = log_likelihood
        likelihood_loss -= float(np.dot(batch["weight"], log_likelihood))
        outcome_loss -= float(np.dot(batch["weight"], outcome_log_likelihood))
        np.add.at(probabilities, batch["row"], batch["weight"] * predicted)
        np.add.at(mass, batch["row"], batch["weight"])
    bins = np.minimum(np.searchsorted(np.linspace(0., 1., 21), probabilities, side="right")-1, 19)
    reliability = []
    for index in range(20):
        selected = bins == index
        reliability.append(dict(lower=index/20., upper=(index+1)/20.,
                                count=int(selected.sum()),
                                observed_positive=int(target[selected].sum()),
                                predicted_mass=float(probabilities[selected].sum())))
    return dict(attempts=len(target), positive=int(target.sum()),
                class_fraction=float(target.mean()),
                mean_predicted_probability=float(probabilities.mean()),
                mean_imputation_weighted_negative_log_likelihood=likelihood_loss/len(target),
                mean_outcome_only_negative_log_likelihood=outcome_loss/len(target),
                reliability=reliability,
                origin_mass_error=float(np.max(np.abs(mass-1.))),
                expanded_rows=expanded_rows, candidate_branches=candidate_branches,
                base_matrix_nonzeros=nonzeros, batches=batches)


def _solve_start(design, actors, initial, tightened):
    scale = .1 if tightened else 1.
    options = dict(maxiter=2000, ftol=1e-10*scale, gtol=1e-6*scale)
    if design["head"] != "g":
        beta, result = solve_logistic(lambda b: objective(b, design, actors), initial, **options)
        value, gradient = objective(beta, design, actors)
        finite = bool(np.isfinite(value) and np.isfinite(gradient).all())
        result.update(converged=result["converged"] and finite,
                      objective=value if np.isfinite(value) else None,
                      gradient_max=float(np.max(np.abs(gradient))) if finite else None,
                      inner_solves=[], objective_trace=[value], em_iterations=0,
                      responsibility_change=None)
        return _complete_prior_only(beta, actors), result
    beta = initial.copy()
    old_value, _ = objective(beta, design, actors)
    posterior = [setter_responsibilities(beta, design, batch)[1]
                 for batch in design["batches"]()]
    trace = [old_value]
    inners = []
    increases = []
    change = None
    relative = None
    converged = False
    termination = "setter em iteration limit"
    for iteration in range(100):
        candidate, inner = solve_logistic(
            lambda b: objective(b, design, actors, posterior), beta, **options,
        )
        inners.append(inner)
        if not inner["converged"]:
            termination = "setter em inner solve failed"
            break
        new_value, _ = objective(candidate, design, actors)
        if not np.isfinite(new_value):
            termination = "setter em nonfinite observed objective"
            break
        difference = new_value-old_value
        if difference > 0:
            increases.append(dict(iteration=iteration+1, increase=difference,
                                  allowed=1e-10*(1+abs(old_value))))
        if difference > 1e-10*(1+abs(old_value)):
            termination = "setter em observed objective increased"
            break
        new_posterior = [setter_responsibilities(candidate, design, batch)[1]
                         for batch in design["batches"]()]
        change = max(float(np.max(np.abs(a-b))) for a, b in zip(posterior, new_posterior))
        relative = abs(difference)/(1+abs(old_value))
        beta, posterior, old_value = candidate, new_posterior, new_value
        trace.append(new_value)
        if relative <= 1e-8*scale and change <= 1e-6*scale:
            converged = True
            termination = "setter em objective and responsibility tolerances satisfied"
            break
    value, gradient = objective(beta, design, actors)
    finite = bool(np.isfinite(value) and np.isfinite(gradient).all())
    return _complete_prior_only(beta, actors), dict(
        converged=converged and finite, termination=termination,
        iterations=sum(item["iterations"] for item in inners),
        evaluations=sum(item["evaluations"] for item in inners),
        objective=value if np.isfinite(value) else None,
        gradient_max=float(np.max(np.abs(gradient))) if finite else None,
        inner_solves=inners, objective_trace=trace, objective_increases=increases,
        em_iterations=len(inners), responsibility_change=change,
        relative_objective_change=relative,
    )


def fit_head(design, previous_ledger=None, *, tightened=False, initial=None):
    """retain the best completed start; unfinished endpoints are diagnostics."""
    began = perf_counter()
    actors = annual_priors(design, [] if previous_ledger is None else previous_ledger)
    target = design["target"]
    requested = ["zero", "prior_mean"] if initial is None else ["continuation"]
    result = dict(status="unavailable", coefficients=None, actors=actors,
                  selected_start=None, requested_starts=requested, starts=[], endpoints={},
                  reasons=[])
    if not len(target) or len(np.unique(target)) < 2:
        result["reasons"] = ["empty_head" if not len(target) else "single_class_head"]
        result["wall_seconds"] = perf_counter()-began
        return result
    zero = np.zeros(design["size"], dtype=np.float64)
    prior = zero.copy()
    for actor in actors:
        prior[actor["index"]] = actor["mean"]
    candidates = [("zero", zero), ("prior_mean", prior)] if initial is None else [
        ("continuation", np.asarray(initial, dtype=np.float64))]
    starts = []
    for name, start in candidates:
        duplicate = next((label for label, earlier in starts if np.array_equal(start, earlier)), None)
        if duplicate is not None:
            result["starts"].append(dict(name=name, deduplicated_to=duplicate))
            continue
        starts.append((name, start))
        coefficients, diagnostics = _solve_start(design, actors, start, tightened)
        result["starts"].append(dict(name=name, deduplicated_to=None, **diagnostics))
        if np.isfinite(coefficients).all():
            result["endpoints"][name] = coefficients
        if diagnostics["converged"]:
            if (result["selected_start"] is None or
                    diagnostics["objective"] < result["diagnostics"]["objective"]):
                result.update(status="complete", coefficients=coefficients,
                              selected_start=name, diagnostics=diagnostics)
    if result["status"] == "unavailable":
        result["reasons"] = ["no_completed_start"]
    else:
        for actor in actors:
            actor["prior_mean"] = prior_mean(actor, result["coefficients"])
            actor["prior_only"] = not bool(actor["likelihood_support"])
        result["diagnostics"]["in_sample"] = head_diagnostics(result["coefficients"], design)
    result["wall_seconds"] = perf_counter()-began
    return result


def continue_head(design, previous_ledger, baseline_coefficients):
    """tighten this head on the identical objective; never replace its base state."""
    actors = annual_priors(design, previous_ledger)
    baseline = np.asarray(baseline_coefficients, dtype=np.float64)
    base_value, base_gradient = objective(baseline, design, actors)
    result = fit_head(design, previous_ledger, tightened=True, initial=baseline)
    result["comparison"] = dict(
        base_objective=base_value, base_gradient_max=float(np.max(np.abs(base_gradient))),
        optimizer_maxiter=2000, optimizer_ftol=1e-11, optimizer_gtol=1e-7,
        em_maxiter=100, em_relative_tolerance=1e-9, em_responsibility_tolerance=1e-7,
    )
    if result["status"] == "complete":
        tighter = result["coefficients"]
        value, gradient = objective(tighter, design, actors)
        difference = tighter-baseline
        result["comparison"].update(
            tightened_objective=value, objective_change=value-base_value,
            tightened_gradient_max=float(np.max(np.abs(gradient))),
            gradient_max_change=float(np.max(np.abs(gradient-base_gradient))),
            coefficient_max_change=float(np.max(np.abs(difference))),
            coefficient_l2_change=float(np.linalg.norm(difference)),
        )
    return result
