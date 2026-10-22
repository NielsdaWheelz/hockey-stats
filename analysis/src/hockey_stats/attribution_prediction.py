"""prediction in a fixed deployment and the original training reference."""

import numpy as np
from scipy import sparse

from .artifacts import require


def current_player_rows(state, players) -> np.ndarray:
    """select current offense then defense rows from an all-seen annual state."""
    require(tuple(players) == state.current_player_ids, "current player identity differs from annual state")
    positions = {player: i for i, player in enumerate(state.player_ids)}
    selected = [positions[player] for player in players]
    return np.asarray(selected + [len(positions) + i for i in selected])


def deployment_gram(X, stratum_indices, exposure, n_strata: int) -> np.ndarray:
    """return the exposure-normalized gram of stratum indicators and current rows."""
    X = sparse.csr_matrix(X)
    si, exposure = np.asarray(stratum_indices), np.asarray(exposure)
    require(type(n_strata) is int and n_strata > 0 and si.shape == exposure.shape == (X.shape[0],)
            and si.dtype.kind in "iu" and np.all((si >= 0) & (si < n_strata))
            and np.isfinite(X.data).all() and np.isfinite(exposure).all()
            and np.all(exposure >= 0) and exposure.sum() > 0,
            "invalid deployment rows, strata or exposure")
    Z = sparse.csr_matrix((np.ones(len(si)), (np.arange(len(si)), si)), shape=(len(si), n_strata))
    deployment = sparse.hstack((Z, X), format="csr")
    return (deployment.T @ deployment.multiply(exposure[:, None])).toarray() / exposure.sum()


def prediction_inner(gram, left, right, *, p=None, rate=40.) -> float:
    """signed native-metric inner product; rows stack context then current maps."""
    require(gram.ndim == left.ndim == right.ndim == 2 and left.shape == right.shape
            and gram.shape == (len(left), len(left)) and np.isfinite(gram).all()
            and np.isfinite(left).all() and np.isfinite(right).all()
            and np.isfinite(rate) and rate > 0,
            "invalid prediction inner-product dimensions or values")
    if p is not None:
        require(p.shape == (left.shape[1],) and np.isfinite(p).all() and np.all(p > 0),
                "prediction shares must be finite and positive")
    metric = left @ right.T if p is None else (left / p) @ right.T
    value = rate ** 2 * float(np.sum(gram * metric))
    require(np.isfinite(value), "prediction inner product is nonfinite")
    return value


def prediction_loss(gram, context, maps, *, p=None, rate=40.) -> float:
    """squared known-mean risk, retaining the original roundoff treatment."""
    difference = np.vstack((context, maps))
    risk = prediction_inner(gram, difference, difference, p=p, rate=rate)
    metric = difference @ difference.T if p is None else (difference / p) @ difference.T
    tolerance = 1e-10 * max(1., rate ** 2 * float(np.sum(np.abs(gram * metric))))
    require(risk >= -tolerance, "known-mean evaluation risk is invalid")
    return max(0., risk)


def excess_prediction_terms(gram, xbar, noise_context, true_maps, fitted_maps, *, p=None, rate=40.) -> dict:
    """error minus known deployment-signal energy plus signed context coupling."""
    require(true_maps.shape == fitted_maps.shape and xbar.shape[1] == len(true_maps)
            and noise_context.shape == (len(xbar), true_maps.shape[1]),
            "excess prediction inputs differ from the training reference")
    truth = np.vstack((-xbar @ true_maps, true_maps))
    fitted = np.vstack((-xbar @ fitted_maps, fitted_maps))
    error = fitted - truth
    noise = np.vstack((noise_context, np.zeros_like(true_maps)))
    E = prediction_inner(gram, error, error, p=p, rate=rate)
    S = prediction_inner(gram, truth, truth, p=p, rate=rate)
    I = 2 * prediction_inner(gram, noise, fitted, p=p, rate=rate)
    return dict(error=E, signal=S, coupling=I, delta=E - S + I)


def shape_recovery(maps, truth, selected_rows, operator, denominator) -> dict:
    """native physical errors with a caller-declared population and normalization."""
    rows = np.asarray(selected_rows)
    require(maps.ndim == truth.ndim == 2 and maps.shape == truth.shape
            and rows.ndim == 1 and rows.dtype.kind in "iu" and len(np.unique(rows)) == len(rows)
            and np.all((0 <= rows) & (rows < len(maps)))
            and operator.ndim == 2 and operator.shape[0] == maps.shape[1] and operator.shape[1] > 0
            and all(value.dtype == np.dtype("float64") and np.isfinite(value).all()
                    for value in (maps, truth, operator))
            and np.isfinite(denominator) and ((len(rows) > 0 and denominator > 0)
                                             or (len(rows) == 0 and denominator == 0)),
            "shape recovery requires finite native maps, explicit rows, operator and denominator")
    error, target = (maps[rows]-truth[rows]) @ operator, truth[rows] @ operator
    return dict(mse=float(np.sum(error**2)/denominator) if len(rows) else None,
                zero_mse=float(np.sum(target**2)/denominator) if len(rows) else None,
                error=error, target=target, count=len(rows), denominator=denominator,
                reason=None if len(rows) else "empty_population")


def same_deployment_excess(H, r, total_hours, Theta, F, B) -> float:
    """signed known-mean excess over the same fitted-context, zero-player predictor."""
    require(H.ndim == Theta.ndim == F.ndim == B.ndim == 2
            and H.shape == (len(Theta), len(Theta)) and F.shape == (len(Theta), len(B))
            and Theta.shape[1] == B.shape[1] and np.isfinite(r) and r > 0
            and np.isfinite(total_hours) and total_hours > 0
            and all(value.dtype == np.dtype("float64") and np.isfinite(value).all()
                    for value in (H, Theta, F, B)),
            "same-deployment excess requires matched finite current-player coefficient axes")
    G = H/(r*total_hours)
    return prediction_inner(G, Theta, Theta, rate=r)-2*r*prediction_inner(G, Theta, F @ B, rate=1.)


def realized_shape_errors(maps, context, *, p, xbar, ybar, true_raw, true_centered,
                          true_context, J, operators, gram, rate=40.) -> dict:
    """realized native recovery and signed prediction in the training reference.

    raw truth retains physical fields; centered truth and context use the final
    exposure gauge. the fixed full-player denominator is 64 for every partition.
    """
    require(maps.shape == true_raw.shape == true_centered.shape
            and context.shape == ybar.shape
            and true_context.shape in ((maps.shape[1],), context.shape)
            and xbar.shape == (len(context), len(maps))
            and J.shape == (len(maps), len(maps))
            and len(operators) == 3 and all(operator.ndim == 2
                and operator.shape[0] == maps.shape[1] and operator.shape[1] > 0
                and np.isfinite(operator).all() for operator in operators)
            and all(np.isfinite(value).all() for value in
                    (maps, context, ybar, xbar, true_raw, true_centered, true_context, J)),
            "realized shape inputs differ from their native final-season reference")
    yh = ybar-ybar.sum(axis=1, keepdims=True)*p
    noise = yh-true_context-xbar @ true_centered
    terms = excess_prediction_terms(gram, xbar, noise, true_centered, maps, p=p, rate=rate)
    P_zero = prediction_loss(gram, yh-true_context, -true_centered, p=p, rate=rate)
    P = prediction_loss(gram, context-true_context, maps-true_centered, p=p, rate=rate)
    require(np.isclose(P-P_zero, terms["delta"], rtol=1e-8, atol=1e-10),
            "realized spatial prediction excess differs")
    errors = [rate*J @ (maps-true_raw) @ operator for operator in operators]
    risks = np.asarray([np.sum(error**2)/64 for error in errors])
    zero = np.asarray([np.sum((rate*J @ true_raw @ operator)**2)/64 for operator in operators])
    return dict(risk=risks, zero_risk=zero, prediction_excess=P-P_zero, prediction=P,
                prediction_zero=P_zero, region_error=errors[0],
                functional_error=np.hstack(errors[1:]), coupling=terms["coupling"])


def expected_excess_prediction_terms(gram, xbar, true_maps, selection, K, mean_score,
                                      covariance, context_cross_score, *, p, B, rate=40.):
    """fixed-penalty expected spatial excess over noisy training context.

    the known-law score covariance is summed over spatial coefficients. the
    context cross-score retains its sign and final training reference. true_maps
    are physical native fields, including detail omitted from the fitted basis.
    a response-selected K does not satisfy this fixed-penalty risk contract.
    """
    n, d = mean_score.shape
    current, cells = true_maps.shape
    strata = len(xbar)
    require(K.shape == covariance.shape == (n, n) and selection.shape == (current, n)
            and xbar.shape == (strata, current) and context_cross_score.shape == (n, strata)
            and B.shape == (cells, d) and p.shape == (cells,)
            and gram.shape == (strata+current, strata+current)
            and all(np.isfinite(value).all() for value in
                    (K, covariance, selection, xbar, context_cross_score, B, p, mean_score, true_maps))
            and np.all(p > 0) and np.isfinite(rate) and rate > 0,
            "fixed expected prediction inputs differ from their explicit geometry")
    influence = selection @ K
    bias = influence @ mean_score @ (p[:, None]*B).T - true_maps
    correction = np.vstack((-xbar, np.eye(current)))
    G = correction.T @ gram @ correction
    bias_squared = prediction_loss(gram, -xbar @ bias, bias, p=p, rate=rate)
    variation = rate**2 * float(np.trace((influence.T @ G @ influence) @ covariance))
    signal = prediction_loss(gram, -xbar @ true_maps, true_maps, p=p, rate=rate)
    zbar = gram[:strata, strata:] - gram[:strata, :strata] @ xbar
    coupling = 2*rate**2 * float(np.sum((zbar @ influence)*context_cross_score.T))
    error = bias_squared + variation
    delta = error-signal+coupling
    require(all(np.isfinite(value) for value in (bias_squared, variation, signal, coupling, error, delta)),
            "fixed expected spatial prediction is nonfinite")
    return dict(error=error, bias_squared=bias_squared, sampling_variance=variation,
                signal=signal, coupling=coupling, delta=delta)


def empirical_prediction(training, state_or_none, evaluation_ids) -> dict:
    """physical prediction in the training reference, with zero raw priors for unseen ids."""
    likelihood = training.likelihood
    basis, current = likelihood.basis, likelihood.player_ids
    ids = tuple(evaluation_ids)
    require(len(ids) == len(set(ids)) and training.xbar.shape == (len(training.strata), 2*len(current))
            and training.nbar.shape == (len(training.strata), len(basis.p))
            and all(np.isfinite(value).all() for value in (training.xbar, training.nbar)),
            "empirical prediction training or evaluation axes differ")
    maps = np.zeros((2*len(ids), len(basis.p)))
    current_maps = np.zeros((2*len(current), len(basis.p)))
    if state_or_none is not None:
        state = state_or_none
        require(state.current_player_ids == current and state.season == likelihood.season
                and state.r == likelihood.r and state.basis_sha256 == basis.sha256
                and state.uncentered_Theta.shape == (2*len(state.player_ids), basis.R.shape[1])
                and np.isfinite(state.uncentered_Theta).all(),
                "empirical prediction state differs from its training likelihood")
        positions = {player: i for i, player in enumerate(state.player_ids)}
        raw_maps = likelihood.r * state.uncentered_Theta @ basis.R.T
        for i, player in enumerate(ids):
            if player in positions:
                maps[i] = raw_maps[positions[player]]
                maps[len(ids)+i] = raw_maps[len(positions)+positions[player]]
        selected = [positions[player] for player in current]
        current_maps = raw_maps[selected + [len(positions)+i for i in selected]]
    context = training.nbar-training.nbar.sum(axis=1, keepdims=True)*basis.p-training.xbar @ current_maps
    require(np.isfinite(context).all() and np.isfinite(maps).all(),
            "empirical prediction is nonfinite")
    return dict(context=context, maps=maps, context_ids=training.strata, player_ids=ids, p=basis.p)


def _empirical_moments(game, prediction):
    """align supported contexts without dropping positive assessment exposure."""
    s, n, k = len(game["context_ids"]), 2*len(game["player_ids"]), len(prediction["p"])
    E = np.asarray(game["E"])
    C, A, K = (sparse.csr_matrix(game[name]) for name in ("C", "A", "K"))
    N = np.asarray(game["N"])
    require(game["player_ids"] == prediction["player_ids"]
            and np.array_equal(game["p"], prediction["p"])
            and E.shape == (s,) and C.shape == (s, n) and A.shape == (n, n)
            and N.shape == (s, k) and K.shape == (n, k)
            and prediction["context"].shape == (len(prediction["context_ids"]), k)
            and prediction["maps"].shape == (n, k)
            and all(np.isfinite(value).all() for value in (E, C.data, A.data, N, K.data))
            and np.all(E >= 0), "empirical game moments or prediction axes differ")
    positions = {context: i for i, context in enumerate(game["context_ids"])}
    require(len(positions) == s and len(set(prediction["context_ids"])) == len(prediction["context_ids"])
            and all(context in positions for context in prediction["context_ids"]),
            "empirical prediction contexts differ from source")
    selected = [positions[context] for context in prediction["context_ids"]]
    omitted = [i for i in range(s) if i not in selected]
    require(not omitted or (np.all(E[omitted] == 0) and np.all(N[omitted] == 0)
                            and C[omitted].nnz == 0),
            "assessment context is absent from training")
    return E[selected], C[selected], A, N[selected], K


def empirical_paired_loss(game_moments, left, right, metric) -> dict:
    """signed loss difference; response self energy cancels before contraction."""
    require(left["context_ids"] == right["context_ids"] and left["player_ids"] == right["player_ids"]
            and np.array_equal(left["p"], right["p"]), "empirical paired prediction references differ")
    E, C, A, N, K = _empirical_moments(game_moments, left)
    difference_f, sum_f = left["context"]-right["context"], left["context"]+right["context"]
    difference_m, sum_m = left["maps"]-right["maps"], left["maps"]+right["maps"]
    p = left["p"]
    metric = np.asarray(metric)
    require(metric.ndim in (1, 2) and metric.shape[0] == len(p) and np.isfinite(metric).all()
            and (metric.ndim == 2 and metric.shape[1] > 0 or metric.ndim == 1 and np.all(metric > 0)),
            "empirical loss requires a finite native operator or positive diagonal metric")
    if metric.ndim == 2:
        difference_f, sum_f, difference_m, sum_m = (
            value @ metric for value in (difference_f, sum_f, difference_m, sum_m))
        shape_n = N @ metric-N.sum(axis=1, keepdims=True)*(p @ metric)
        shape_k = K @ metric-np.asarray(K.sum(axis=1))*(p @ metric)
        response = np.sum(shape_n*difference_f, axis=0)+np.sum(shape_k*difference_m, axis=0)
        weights = 1.
    else:
        weights = metric
        shape_n = N-N.sum(axis=1, keepdims=True)*p
        response = np.sum(shape_n*difference_f*weights, axis=0)
        response += np.asarray(K.multiply(difference_m*weights).sum(axis=0)).ravel()
        response -= np.sum(np.asarray(K.sum(axis=1))*p*difference_m*weights, axis=0)
    components = np.sum(difference_f*(E[:, None]*sum_f+C @ sum_m)*weights, axis=0)
    components += np.sum(difference_m*(C.T @ sum_f+A @ sum_m)*weights, axis=0)
    components -= 2*response
    require(np.isfinite(components).all(), "empirical paired loss is nonfinite")
    return dict(loss_numerator=float(components.sum()), component_numerators=components,
                directed_hours=float(E.sum()))


def empirical_residuals(game_moments, prediction) -> dict:
    """native signed response sums and overlapping role-specific on-ice associations."""
    E, C, A, N, K = _empirical_moments(game_moments, prediction)
    F, M, p = prediction["context"], prediction["maps"], prediction["p"]
    observed = (N-N.sum(axis=1, keepdims=True)*p).sum(axis=0)
    predicted = (E[:, None]*F+C @ M).sum(axis=0)
    player_residual = K.toarray()-np.asarray(K.sum(axis=1))*p-C.T @ F-A @ M
    require(all(np.isfinite(value).all() for value in (observed, predicted, player_residual)),
            "empirical residual is nonfinite")
    return dict(observed_sum=observed, predicted_sum=predicted, residual_sum=observed-predicted,
                player_residual_sum=player_residual, player_hours=A.diagonal(), directed_hours=float(E.sum()))
