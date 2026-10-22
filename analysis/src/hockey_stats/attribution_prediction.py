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
    """align explicit coarse or continuous context moments without dropping exposure."""
    s, n, k = len(game["context_ids"]), 2*len(game["player_ids"]), len(prediction["p"])
    C, A, K = (sparse.csr_matrix(game[name]) for name in ("C", "A", "K"))
    N = np.asarray(game["N"])
    general = "G" in game
    gram = np.asarray(game["G"] if general else game["E"])
    require(game["player_ids"] == prediction["player_ids"]
            and np.array_equal(game["p"], prediction["p"])
            and gram.shape == ((s, s) if general else (s,))
            and C.shape == (s, n) and A.shape == (n, n)
            and N.shape == (s, k) and K.shape == (n, k)
            and prediction["context"].shape == (len(prediction["context_ids"]), k)
            and prediction["maps"].shape == (n, k)
            and all(np.isfinite(value).all() for value in (gram, C.data, A.data, N, K.data))
            and (general or np.all(gram >= 0)), "empirical game moments or prediction axes differ")
    positions = {context: i for i, context in enumerate(game["context_ids"])}
    require(len(positions) == s and len(set(prediction["context_ids"])) == len(prediction["context_ids"])
            and all(context in positions for context in prediction["context_ids"]),
            "empirical prediction contexts differ from source")
    selected = [positions[context] for context in prediction["context_ids"]]
    omitted = [i for i in range(s) if i not in selected]
    require(not omitted or (np.all(gram[omitted] == 0) and np.all(N[omitted] == 0)
                            and C[omitted].nnz == 0),
            "assessment context is absent from training")
    if general:
        integral = np.asarray(game["context_integral"])
        require(integral.shape == (s,) and np.isfinite(integral).all()
                and np.isfinite(game["directed_hours"]) and game["directed_hours"] >= 0
                and np.allclose(gram, gram.T, rtol=1e-8, atol=1e-10),
                "continuous context exposure or gram differs")
        gram = gram[np.ix_(selected, selected)]
    else:
        gram = gram[selected]
    return gram, C[selected], A, N[selected], K


def _context_product(gram, values):
    return gram @ values if gram.ndim == 2 else gram[:, None]*values


def _game_hours(game):
    return float(game["directed_hours"] if "G" in game else np.sum(game["E"]))


def _context_integral(game, prediction):
    if "G" not in game:
        return _empirical_moments(game, prediction)[0]
    positions = {context: i for i, context in enumerate(game["context_ids"])}
    return np.asarray(game["context_integral"])[[positions[c] for c in prediction["context_ids"]]]


def empirical_paired_loss(game_moments, left, right, metric, *, response="shape", aggregate=False) -> dict:
    """signed loss difference; response self energy cancels before contraction."""
    require(response in ("shape", "complete"), "paired loss response must be shape or complete")
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
    if aggregate:
        require(metric.ndim == 1 and "map_coordinates" in left and "map_coordinates" in right
                and np.array_equal(left["map_basis"], right["map_basis"]),
                "aggregate native loss requires explicit common player factors")
        operator = left["map_basis"]
        dc = left["map_coordinates"]-right["map_coordinates"]
        sc = left["map_coordinates"]+right["map_coordinates"]
        require(operator.ndim == 2 and operator.shape[1] == len(p)
                and dc.shape == sc.shape == (len(difference_m), len(operator))
                and all(np.isfinite(v).all() for v in (operator,dc,sc)),
                "aggregate native player factors differ")
        shape_n = N-N.sum(axis=1,keepdims=True)*p if response == "shape" else N
        response_term = float(np.sum(shape_n*difference_f*metric))
        player_response = K @ (operator*metric).T
        if response == "shape":
            player_response -= np.asarray(K.sum(axis=1))*((operator*metric) @ p)
        response_term += float(np.sum(player_response*dc))
        value = float(np.sum(difference_f*_context_product(E,sum_f)*metric))
        value += float(np.sum(((C @ dc) @ operator)*sum_f*metric))
        value += float(np.sum(difference_f*((C @ sc) @ operator)*metric))
        value += float(np.sum(dc*((A @ sc) @ ((operator*metric) @ operator.T))))
        value -= 2*response_term
        require(np.isfinite(value), "aggregate native paired loss is nonfinite")
        return dict(loss_numerator=value,component_numerators=np.asarray([value]),
                    directed_hours=_game_hours(game_moments))
    if metric.ndim == 2:
        difference_f, sum_f = difference_f @ metric, sum_f @ metric
        if "map_coordinates" in left and "map_coordinates" in right:
            require(np.array_equal(left["map_basis"],right["map_basis"]),
                    "regional player factors use different native axes")
            operator = left["map_basis"] @ metric
            difference_m = (left["map_coordinates"]-right["map_coordinates"]) @ operator
            sum_m = (left["map_coordinates"]+right["map_coordinates"]) @ operator
        else:
            difference_m, sum_m = difference_m @ metric, sum_m @ metric
        shape_n, shape_k = N @ metric, K @ metric
        if response == "shape":
            shape_n = shape_n-N.sum(axis=1, keepdims=True)*(p @ metric)
            shape_k = shape_k-np.asarray(K.sum(axis=1))*(p @ metric)
        response_term = np.sum(shape_n*difference_f, axis=0)+np.sum(shape_k*difference_m, axis=0)
        weights = 1.
    else:
        weights = metric
        shape_n = N-N.sum(axis=1, keepdims=True)*p if response == "shape" else N
        response_term = np.sum(shape_n*difference_f*weights, axis=0)
        response_term += np.asarray(K.multiply(difference_m*weights).sum(axis=0)).ravel()
        if response == "shape":
            response_term -= np.sum(np.asarray(K.sum(axis=1))*p*difference_m*weights, axis=0)
    components = np.sum(difference_f*(_context_product(E, sum_f)+C @ sum_m)*weights, axis=0)
    components += np.sum(difference_m*(C.T @ sum_f+A @ sum_m)*weights, axis=0)
    components -= 2*response_term
    require(np.isfinite(components).all(), "empirical paired loss is nonfinite")
    return dict(loss_numerator=float(components.sum()), component_numerators=components,
                directed_hours=_game_hours(game_moments))


def empirical_residuals(game_moments, prediction, *, response="shape", operator=None) -> dict:
    """native signed response sums and overlapping role-specific on-ice associations."""
    E, C, A, N, K = _empirical_moments(game_moments, prediction)
    require(response in ('shape', 'complete'), 'residual response must be shape or complete')
    F, M, p = prediction["context"], prediction["maps"], prediction["p"]
    observed_N = N[:len(game_moments['E'])] if 'G' in game_moments else N
    if operator is None:
        observed = (observed_N-observed_N.sum(axis=1,keepdims=True)*p).sum(axis=0) if response=='shape' else observed_N.sum(axis=0)
        predicted = (_context_integral(game_moments,prediction) @ F+A.diagonal() @ M
                     if 'G' in game_moments else (E[:,None]*F+C @ M).sum(axis=0))
        player_residual = K.toarray()-C.T @ F-A @ M
        if response == 'shape':
            # preserve the historical order of operations for frozen 04m values.
            player_residual = K.toarray()-np.asarray(K.sum(axis=1))*p-C.T @ F-A @ M
    else:
        require(operator.ndim == 2 and operator.shape[0] == len(p) and np.isfinite(operator).all(),
                'residual regional operator differs')
        projected_f = F @ operator
        projected_m = (prediction['map_coordinates'] @ (prediction['map_basis'] @ operator)
                       if 'map_coordinates' in prediction else M @ operator)
        observed = observed_N.sum(axis=0) @ operator
        predicted = _context_integral(game_moments,prediction) @ projected_f + (A.diagonal() if 'G' in game_moments else np.asarray(C.sum(axis=0)).ravel()) @ projected_m
        player_residual = K @ operator-C.T @ projected_f-A @ projected_m
        if response == 'shape':
            observed -= observed_N.sum()*(p @ operator)
            player_residual -= np.asarray(K.sum(axis=1))*(p @ operator)
    require(all(np.isfinite(value).all() for value in (observed, predicted, player_residual)),
            "empirical residual is nonfinite")
    return dict(observed_sum=observed, predicted_sum=predicted, residual_sum=observed-predicted,
                player_residual_sum=player_residual, player_hours=A.diagonal(), directed_hours=_game_hours(game_moments))


def complete_prediction(training, scalar_state, shape_state, evaluation_ids):
    """compose raw volume and zero-sum shape in one training-only reference."""
    require(
        (scalar_state is None) == (shape_state is None),
        "complete prediction requires both fitted components or context only",
    )
    shape = empirical_prediction(training, shape_state, evaluation_ids)
    likelihood, ids = training.likelihood, tuple(evaluation_ids)
    p, current = likelihood.basis.p, likelihood.player_ids
    volume_maps = np.zeros((2 * len(ids), 1))
    current_maps = np.zeros((2 * len(current), 1))
    if scalar_state is not None:
        state = scalar_state
        require(
            state.season == likelihood.season
            and state.current_player_ids == current
            and state.r == likelihood.r
            and state.player_ids == shape_state.player_ids
            and state.entrant_ids == shape_state.entrant_ids
            and state.carried_only_ids == shape_state.carried_only_ids
            and np.array_equal(state.u, shape_state.u)
            and state.uncentered_beta.shape == (2 * len(state.player_ids), 1)
            and np.isfinite(state.uncentered_beta).all(),
            "volume and shape state populations or training references differ",
        )
        positions = {player: i for i, player in enumerate(state.player_ids)}
        raw = likelihood.r * state.uncentered_beta
        for i, player in enumerate(ids):
            if player in positions:
                volume_maps[i] = raw[positions[player]]
                volume_maps[len(ids) + i] = raw[len(positions) + positions[player]]
        selected = [positions[player] for player in current]
        current_maps = raw[selected + [len(positions) + i for i in selected]]
        # each role has its own gauge. unseen raw zero becomes minus that shift.
        for fitted, raw_name, centered_name in (
            (state, "uncentered_beta", "beta"),
            (shape_state, "uncentered_Theta", "Theta"),
        ):
            n = len(fitted.player_ids)
            raw_coefficients, centered = getattr(fitted, raw_name), getattr(fitted, centered_name)
            shifts = np.vstack(
                [
                    np.broadcast_to(
                        fitted.u @ raw_coefficients[role * n : (role + 1) * n], (n, raw_coefficients.shape[1])
                    )
                    for role in range(2)
                ]
            )
            require(
                np.allclose(centered, raw_coefficients - shifts, rtol=1e-10, atol=1e-11),
                "raw and role-centered coefficient predictions differ",
            )
    volume_context = training.nbar.sum(axis=1, keepdims=True) - training.xbar @ current_maps
    shape_context, shape_maps = shape["context"], shape["maps"]
    context, maps = volume_context * p + shape_context, volume_maps * p + shape_maps
    require(
        np.allclose(shape_context.sum(axis=1), 0.0, atol=1e-9)
        and np.allclose(shape_maps.sum(axis=1), 0.0, atol=1e-9)
        and np.allclose(context.sum(axis=1, keepdims=True), volume_context, atol=1e-9)
        and np.allclose(maps.sum(axis=1, keepdims=True), volume_maps, atol=1e-9),
        "complete prediction volume or zero-sum shape does not close",
    )
    map_basis = np.vstack((p, likelihood.basis.R.T))
    shape_coordinates = np.zeros((2*len(ids),1+likelihood.basis.R.shape[1]))
    if shape_state is not None:
        for i, player in enumerate(ids):
            if player in positions:
                shape_coordinates[i,1:] = likelihood.r*shape_state.uncentered_Theta[positions[player]]
                shape_coordinates[len(ids)+i,1:] = likelihood.r*shape_state.uncentered_Theta[len(positions)+positions[player]]
    coordinates = shape_coordinates.copy()
    coordinates[:,0] = volume_maps.ravel()
    require(np.allclose(coordinates @ map_basis,maps,rtol=1e-8,atol=1e-10),
            "complete player factorization differs from physical maps")
    return dict(
        shape,
        map_basis=map_basis, map_coordinates=coordinates, shape_coordinates=shape_coordinates,
        context=context,
        maps=maps,
        volume_context=volume_context,
        volume_maps=volume_maps,
        shape_context=shape_context,
        shape_maps=shape_maps,
    )


def complete_paired_decomposition(game, left, right, regions):
    """paired physical loss, with signed volume, shape and interaction terms."""
    p = left["p"]
    volume = empirical_paired_loss(game, left, right, np.ones((len(p), 1)), response="complete")[
        "loss_numerator"
    ]
    shape_left = dict(left, context=left["shape_context"], maps=left["shape_maps"])
    if "map_coordinates" in left:
        shape_left["map_coordinates"] = left["shape_coordinates"]
    shape_right = dict(right, context=right["shape_context"], maps=right["shape_maps"])
    if "map_coordinates" in right:
        shape_right["map_coordinates"] = right["shape_coordinates"]
    E, C, A, N, K = _empirical_moments(game, left)
    total_n, total_k = N.sum(axis=1), np.asarray(K.sum(axis=1)).ravel()
    result = dict(volume=volume)
    for name, metric, weight in (
        ("regional", regions, float(np.sum((p @ regions) ** 2))),
        ("native_inverse_share", 1.0 / p, 1.0),
    ):
        aggregate = metric.ndim == 1 and "map_coordinates" in left and "map_coordinates" in right
        complete = empirical_paired_loss(game, left, right, metric, response="complete", aggregate=aggregate)
        shape = empirical_paired_loss(game, shape_left, shape_right, metric, aggregate=aggregate)
        # expand the cross residual directly; response self products cancel.
        q_native = metric @ (p @ metric) if metric.ndim == 2 else p * metric
        shape_n = N @ q_native - total_n * float(p @ q_native)
        shape_k = np.asarray(K @ q_native).ravel() - total_k * float(p @ q_native)
        cross = []
        for prediction in (left, right):
            vf, vm = prediction["volume_context"].ravel(), prediction["volume_maps"].ravel()
            hf, hm = prediction["shape_context"] @ q_native, prediction["shape_maps"] @ q_native
            cross.append(
                float(
                    vf @ (_context_product(E, hf[:, None]).ravel() + C @ hm)
                    + vm @ (C.T @ hf + A @ hm)
                    - total_n @ hf
                    - total_k @ hm
                    - shape_n @ vf
                    - shape_k @ vm
                )
            )
        interaction = 2 * (cross[0] - cross[1])
        require(
            np.isclose(
                complete["loss_numerator"],
                weight * volume + shape["loss_numerator"] + interaction,
                rtol=1e-8 if "G" in game else 1e-9,
                atol=1e-10 if "G" in game else 1e-8,
            ),
            "direct volume/shape interaction does not close",
        )
        if name == "native_inverse_share":
            require(
                abs(interaction)
                <= 1e-9
                * max(1.0, abs(complete["loss_numerator"]), abs(shape["loss_numerator"]), abs(volume)),
                "native inverse-share volume/shape interaction is nonzero",
            )
        result[name] = dict(
            complete=complete["loss_numerator"],
            volume=volume,
            weighted_volume=weight * volume,
            shape=shape["loss_numerator"],
            interaction=interaction,
            region_numerators=complete["component_numerators"],
            directed_hours=complete["directed_hours"],
        )
    return result


def prediction_row_batches(rows, predictions, batch_size=256, *, receipt):
    """evaluate bounded native matrices; source iteration/reconciliation has one owner."""
    require(
        type(batch_size) is int and batch_size > 0 and bool(predictions), "invalid prediction row batch size"
    )
    arm_rates = {arm: [] for arm in predictions}
    volume_rates = {arm: [] for arm in predictions}
    receipt.update(
        rows=0,
        maximum_shape_sum_absolute=0.0,
        maximum_complete_volume_absolute=0.0,
        absolute_tolerance=1e-9,
        relative_tolerance=1e-10,
    )
    seconds, locators = [], []
    references = {
        arm: (
            {player: i for i, player in enumerate(prediction["player_ids"])},
            {context: i for i, context in enumerate(prediction["context_ids"])},
        )
        for arm, prediction in predictions.items()
    }
    for row in rows:
        require(np.isfinite(row["seconds"]) and row["seconds"] > 0, "invalid prediction row duration")
        for arm, prediction in predictions.items():
            players, contexts = references[arm]
            context = tuple(row["stratum"])
            require(
                context in contexts
                and all(player in players for player in (*row["offense"], *row["defense"])),
                "prediction row population differs from fitted reference",
            )
            selected = [players[player] for player in row["offense"]]
            selected += [len(players) + players[player] for player in row["defense"]]
            native = prediction["context"][contexts[context]] + prediction["maps"][selected].sum(axis=0)
            volume = float(
                prediction["volume_context"][contexts[context], 0] + prediction["volume_maps"][selected].sum()
            )
            shape = prediction["shape_context"][contexts[context]] + prediction["shape_maps"][selected].sum(
                axis=0
            )
            shape_error, volume_error = abs(float(shape.sum())), abs(float(native.sum()) - volume)
            require(
                shape_error <= 1e-9 and np.isclose(native.sum(), volume, rtol=1e-10, atol=1e-9),
                "row physical shape or complete-volume identity differs",
            )
            receipt["maximum_shape_sum_absolute"] = max(receipt["maximum_shape_sum_absolute"], shape_error)
            receipt["maximum_complete_volume_absolute"] = max(
                receipt["maximum_complete_volume_absolute"], volume_error
            )
            arm_rates[arm].append(native)
            volume_rates[arm].append([volume])
        receipt["rows"] += 1
        seconds.append(row["seconds"])
        locators.append(
            {
                key: row[key]
                for key in (
                    "game_id",
                    "period",
                    "start",
                    "end",
                    "segment_index",
                    "attacking_team",
                    "offense",
                    "defense",
                    "stratum",
                )
            }
        )
        if len(seconds) == batch_size:
            yield (
                {arm: np.array(value) for arm, value in arm_rates.items()},
                np.array(seconds),
                locators,
                {arm: np.array(value) for arm, value in volume_rates.items()},
            )
            arm_rates = {arm: [] for arm in predictions}
            volume_rates = {arm: [] for arm in predictions}
            seconds, locators = [], []
    if seconds:
        yield (
            {arm: np.array(value) for arm, value in arm_rates.items()},
            np.array(seconds),
            locators,
            {arm: np.array(value) for arm, value in volume_rates.items()},
        )
    receipt["status"] = "verified"


def complete_rate_diagnostics(batches, p, regions, region_names, training_r):
    """strict physical signs at each resolution, sharing the historical accumulator."""
    from .attribution import negative_rate_summaries

    extra = {}

    def transformed():
        for rates, seconds, locators, volumes in batches:
            require(set(rates) == set(volumes), "native and scalar diagnostic arms differ")
            selected = {}
            for arm, native in rates.items():
                require(native.shape[1] == len(p), "native diagnostic cells differ")
                require(volumes[arm].shape == (len(native), 1), "scalar diagnostic row axes differ")
                for resolution, values in (
                    ("total", volumes[arm]),
                    ("regional", native @ regions),
                    ("native", native),
                ):
                    name = arm + ":" + resolution
                    selected[name] = values
                    entry = extra.setdefault(
                        name, dict(seconds=0.0, any_negative_seconds=0.0, locations=values.shape[1])
                    )
                    entry["seconds"] += float(seconds.sum())
                    entry["any_negative_seconds"] += float(seconds @ np.any(values < 0, axis=1))
            yield selected, seconds, locators

    iterator = iter(transformed())
    first = next(iterator, None)
    require(first is not None, "rate diagnostics require positive held-out exposure")
    import itertools

    summaries = negative_rate_summaries(
        itertools.chain((first,), iterator), {name: training_r for name in first[0]}
    )
    result = []
    for name, summary in summaries.items():
        arm, resolution = name.split(":")
        total_summary = summaries[arm + ":total"]
        details = extra[name]
        location = dict(summary["minimum_cell_example"])
        cell = location.pop("cell_id")
        location.update(
            location_index=cell,
            location_label=(
                region_names[cell] if resolution == "regional" else "total" if resolution == "total" else cell
            ),
        )
        result.append(
            dict(
                arm=arm,
                resolution=resolution,
                rows=summary["rows"],
                locations=details["locations"],
                strict_sign_rule="prediction < 0",
                closure_absolute_tolerance=1e-9,
                negative_entries=summary["negative_cell_rates"],
                negative_total_rows=total_summary["negative_complete_rates"],
                directed_hours=summary["team_seconds"] / 3600.0,
                entry_exposure_denominator=details["locations"] * summary["team_seconds"] / 3600.0,
                negative_entry_location_hours=summary["exposure_weighted_negative_cell_frequency"]
                * details["locations"]
                * summary["team_seconds"]
                / 3600.0,
                any_negative_entry_row_directed_hours=details["any_negative_seconds"] / 3600.0,
                negative_total_rate_directed_hours=total_summary[
                    "exposure_weighted_negative_complete_frequency"
                ]
                * total_summary["team_seconds"]
                / 3600.0,
                negative_entry_exposure_fraction=summary["exposure_weighted_negative_cell_frequency"],
                negative_total_rate_exposure_fraction=total_summary[
                    "exposure_weighted_negative_complete_frequency"
                ],
                any_negative_entry_row_exposure_fraction=details["any_negative_seconds"] / details["seconds"],
                negative_mass_predicted_attempts=summary["negative_mass"]
                * training_r
                * summary["team_seconds"]
                / 3600.0,
                negative_mass_reference=training_r * summary["team_seconds"] / 3600.0,
                negative_mass_fraction=summary["negative_mass"],
                training_r=training_r,
                minimum=summary["minimum_cell_rate"],
                worst_location=location,
                minimum_total_rate=total_summary["minimum_complete_rate"],
                minimum_total_location=total_summary["minimum_complete_example"],
            )
        )
    return result


def quadratic_interval_signs(coefficients, directed_hours):
    """exact strictly negative portions of a quadratic on normalized time [0,1].

    each row contains constant, linear and quadratic coefficients. floating
    tolerances are deliberately absent from sign decisions. zero-duration roots
    do not contribute exposure; the minimum can be an unattained boundary limit.
    """
    q = np.asarray(coefficients)
    require(q.ndim == 2 and q.shape[1] == 3 and len(q)>0 and q.dtype == np.dtype('float64')
            and np.isfinite(q).all() and np.isfinite(directed_hours) and directed_hours > 0,
            'quadratic signs require finite coefficients and positive directed hours')
    import math

    c, b, a = q.T
    roots = np.zeros((len(q),2),dtype=np.float64)
    linear = (a == 0) & (b != 0)
    roots[linear] = (-c[linear]/b[linear])[:,None]
    quadratic = a != 0
    discriminant = b*b-4*a*c
    require(np.isfinite(discriminant).all(), 'quadratic discriminant is nonfinite')
    uncertain = quadratic & (np.abs(discriminant) <= 8*np.finfo(np.float64).eps*(b*b+np.abs(4*a*c)))
    # a compensated difference of products preserves near-tangent signs;
    # factored values below avoid cancellation between nearby roots.
    for index in np.flatnonzero(uncertain):
        cc,bb,aa = (float(v) for v in q[index])
        product=4*aa*cc
        require(np.isfinite(product) and np.isfinite(4*aa), 'quadratic product is nonfinite')
        error=math.fma(-4*aa,cc,product)
        difference=math.fma(bb,bb,-product)
        discriminant[index]=math.fsum((difference,error))
    require(np.isfinite(discriminant).all(), 'compensated discriminant is nonfinite')
    repeated = quadratic & (discriminant == 0)
    roots[repeated] = (-b[repeated]/(2*a[repeated]))[:,None]
    distinct = quadratic & (discriminant > 0)
    stable = -.5*(b[distinct]+np.copysign(np.sqrt(discriminant[distinct]),b[distinct]))
    roots[distinct,0] = stable/a[distinct]
    roots[distinct,1] = c[distinct]/stable
    # absent/outside roots become duplicate boundary cuts, with zero duration.
    roots.sort(axis=1)
    unbounded_roots=roots.copy()
    roots = np.clip(roots,0.,1.)
    cuts = np.column_stack((np.zeros(len(q)),roots,np.ones(len(q))))
    lo, hi = cuts[:,:-1], cuts[:,1:]
    width, mid = hi-lo, (lo+hi)/2
    at_mid = (a[:,None]*mid+b[:,None])*mid+c[:,None]
    at_mid[linear] = b[linear,None]*(mid[linear]-unbounded_roots[linear,0,None])
    real = quadratic & (discriminant >= 0)
    at_mid[real] = a[real,None]*(mid[real]-unbounded_roots[real,0,None])*(mid[real]-unbounded_roots[real,1,None])
    negative = (at_mid < 0) & (width > 0)
    no_real=quadratic & (discriminant < 0)
    negative[no_real] = (a[no_real,None] < 0) & (width[no_real] > 0)
    at_mid[no_real] = (a[no_real,None]*(mid[no_real]+b[no_real,None]/(2*a[no_real,None]))**2
                       -discriminant[no_real,None]/(4*a[no_real,None]))
    duration = np.where(negative,width,0.).sum(axis=1)*directed_hours
    integral = at_mid*width+a[:,None]*width**3/12
    mass = -np.where(negative,integral,0.).sum(axis=1)*directed_hours
    require(np.isfinite(mass).all() and np.all(mass >= 0),
            'quadratic negative mass is nonfinite or negative')
    vertex = np.divide(-b,2*a,out=np.zeros_like(a),where=a != 0)
    vertex_value = np.divide(-discriminant,4*a,out=np.zeros_like(a),where=a != 0)
    interior = (a > 0) & (vertex > 0) & (vertex < 1)
    constant=(a == 0) & (b == 0)
    endpoint=a+b+c
    cancellation=np.abs(endpoint) <= 8*np.finfo(np.float64).eps*(np.abs(a)+np.abs(b)+np.abs(c))
    for index in np.flatnonzero(cancellation & ~constant):
        endpoint[index]=math.fsum(float(v) for v in q[index])
    candidate_values = np.column_stack((c,endpoint,np.where(interior,vertex_value,np.inf)))
    candidate_times = np.column_stack((np.where(constant,.5,0.),np.ones(len(q)),vertex))
    selected = np.argmin(candidate_values,axis=1)
    minimum = candidate_values[np.arange(len(q)),selected]
    times = candidate_times[np.arange(len(q)),selected]
    attainment = np.full(len(q),'attained',dtype='<U11')
    attainment[times == 0] = 'right_limit'
    attainment[times == 1] = 'left_limit'
    lower, upper = lo[negative], hi[negative]
    order = np.argsort(lower)
    lower, upper = lower[order], upper[order]
    previous = np.r_[0.,np.maximum.accumulate(upper)[:-1]] if len(upper) else np.empty(0)
    union = float(np.maximum(0.,upper-np.maximum(lower,previous)).sum())
    return dict(negative_location_hours=np.asarray(duration,dtype=np.float64),negative_mass=np.asarray(mass,dtype=np.float64),
        negative_pairs=int(np.count_nonzero(duration)),any_negative_hours=union*directed_hours,
        minimum=np.asarray(minimum,dtype=np.float64),minimum_at=np.asarray(times,dtype=np.float64),minimum_attainment=attainment,
        negative_interval_bounds=np.stack((lo,hi),axis=2),negative_interval_mask=negative)


def context_prediction_row_batches(rows, predictions, training, batch_size=64, *, receipt):
    """bounded complete-rate polynomial rows; source owns timing and event assignment."""
    from .attribution_context import context_polynomial, TEMPORAL_IDS

    require(type(batch_size) is int and batch_size > 0 and bool(predictions),
            'invalid continuous prediction batch size')
    refs = {arm: {player: i for i, player in enumerate(pred['player_ids'])}
            for arm, pred in predictions.items()}
    batches, durations, locators = {arm: [] for arm in predictions}, [], []
    receipt.update(rows=0, maximum_shape_sum_absolute=0., maximum_complete_volume_absolute=0.)
    for row in rows:
        seconds = float(row['end']-row['start'])
        require(np.isfinite(seconds) and seconds > 0, 'continuous row duration must be positive')
        Z = context_polynomial(tuple(row['stratum']), row['start'], training.M, training.strata)
        for arm, prediction in predictions.items():
            require(prediction['context_ids'] == training.strata+TEMPORAL_IDS,
                    'continuous prediction context axes differ')
            positions = refs[arm]
            require(all(p in positions for p in (*row['offense'], *row['defense'])),
                    'continuous row players differ')
            indices = [positions[p] for p in row['offense']]
            indices += [len(positions)+positions[p] for p in row['defense']]
            native = Z.T @ prediction['context']
            native[0] += prediction['maps'][indices].sum(axis=0)
            volume = Z.T @ prediction['volume_context']
            volume[0] += prediction['volume_maps'][indices].sum(axis=0)
            shape = Z.T @ prediction['shape_context']
            shape[0] += prediction['shape_maps'][indices].sum(axis=0)
            native *= np.array([1., seconds, seconds**2])[:, None]
            volume *= np.array([1., seconds, seconds**2])[:, None]
            shape *= np.array([1., seconds, seconds**2])[:, None]
            shape_error = float(np.max(np.abs(shape.sum(axis=1))))
            volume_error = float(np.max(np.abs(native.sum(axis=1, keepdims=True)-volume)))
            require(np.allclose(shape.sum(axis=1), 0., rtol=1e-8, atol=1e-10)
                    and np.allclose(native.sum(axis=1, keepdims=True), volume, rtol=1e-8, atol=1e-10),
                    'continuous physical volume/shape identity differs')
            receipt['maximum_shape_sum_absolute'] = max(receipt['maximum_shape_sum_absolute'], shape_error)
            receipt['maximum_complete_volume_absolute'] = max(receipt['maximum_complete_volume_absolute'], volume_error)
            batches[arm].append(native)
        receipt['rows'] += 1
        durations.append(seconds/3600.)
        locators.append(dict({key: row[key] for key in ('game_id','period','start','end','segment_index','attacking_team')},
                             side=row['stratum'][0]))
        if len(durations) == batch_size:
            yield {arm: np.asarray(v) for arm,v in batches.items()}, np.asarray(durations), locators
            batches, durations, locators = {arm: [] for arm in predictions}, [], []
    if durations:
        yield {arm: np.asarray(v) for arm,v in batches.items()}, np.asarray(durations), locators
    receipt['status'] = 'verified'


def continuous_rate_diagnostics(batches, regions, region_names, training_r):
    """integrated strict physical signs and exact row/clock witnesses at three resolutions."""
    require(np.isfinite(training_r) and training_r > 0 and len(region_names) == regions.shape[1],
            'continuous rate reference differs')
    summaries = {}
    for arms, hours, locators in batches:
        for arm, native in arms.items():
            require(native.ndim == 3 and native.shape[:2] == (len(hours),3)
                    and native.shape[2] == len(regions) and np.isfinite(native).all(),
                    'continuous native polynomial axes differ')
            for resolution, values in (('total',native.sum(axis=2,keepdims=True)),
                                       ('regional',native @ regions),('native',native)):
                n = values.shape[2]
                entry = summaries.setdefault((arm,resolution), dict(arm=arm,resolution=resolution,
                    rows=0,locations=n,directed_hours=0.,negative_interval_location_pairs=0,
                    negative_location_hours=0.,any_negative_directed_hours=0.,negative_mass_predicted_attempts=0.,
                    minimum=None,worst_location=None))
                for q, duration, locator in zip(values,hours,locators,strict=True):
                    result = quadratic_interval_signs(q.T,float(duration))
                    entry['rows'] += 1; entry['directed_hours'] += float(duration)
                    entry['negative_interval_location_pairs'] += result['negative_pairs']
                    entry['negative_location_hours'] += float(result['negative_location_hours'].sum())
                    entry['any_negative_directed_hours'] += float(result['any_negative_hours'])
                    entry['negative_mass_predicted_attempts'] += float(result['negative_mass'].sum())
                    cell = int(np.argmin(result['minimum']))
                    minimum = float(result['minimum'][cell])
                    if entry['minimum'] is None or minimum < entry['minimum']:
                        fraction = float(result['minimum_at'][cell])
                        entry['minimum'] = minimum
                        entry['worst_location'] = dict(locator,location_index=cell,
                            location_label=region_names[cell] if resolution=='regional' else 'total' if resolution=='total' else cell,
                            time=float(locator['start']+fraction*(locator['end']-locator['start'])),
                            attainment=result['minimum_attainment'][cell])
    require(bool(summaries), 'continuous rate diagnostics require positive exposure')
    for entry in summaries.values():
        hours=entry['directed_hours']; denominator=entry['locations']*hours
        entry.update(strict_sign_rule='prediction < 0 on positive-duration intervals',
            polynomial_precision='float64 saved coefficients; compensated fma discriminant and factored integration; no sign tolerance',
            minimum_domain='row exposure interior; boundary values are one-sided infima',
            negative_location_time_fraction=entry['negative_location_hours']/denominator,
            any_negative_exposure_fraction=entry['any_negative_directed_hours']/hours,
            negative_mass_reference=training_r*hours,
            negative_mass_fraction=entry['negative_mass_predicted_attempts']/(training_r*hours),
            location_exposure_denominator=denominator,training_r=training_r)
    return list(summaries.values())


def context_complete_prediction(training, scalar_state, shape_state, evaluation_ids):
    """compose physical coarse/time/player fields in the saved training reference."""
    from .attribution_context import TEMPORAL_IDS

    base = complete_prediction(training, scalar_state, shape_state, evaluation_ids)
    likelihood, basis = training.likelihood, training.likelihood.basis
    n = len(likelihood.player_ids)
    raw_volume = np.zeros((2*n,1))
    raw_shape = np.zeros((2*n,basis.R.shape[1]))
    if scalar_state is not None:
        raw_volume = likelihood.r*scalar_state.uncentered_beta[current_player_rows(scalar_state,likelihood.player_ids)]
        raw_shape = likelihood.r*shape_state.uncentered_Theta[current_player_rows(shape_state,likelihood.player_ids)]
    volume_rhs = training.Nh.sum(axis=1,keepdims=True)-training.Ch @ raw_volume
    shape_rhs = training.Nh @ basis.B-training.Ch @ raw_shape
    volume_time = np.linalg.solve(training.D,volume_rhs)
    shape_time = np.linalg.solve(training.D,shape_rhs) @ basis.R.T
    require(np.allclose(training.D @ volume_time,volume_rhs,rtol=1e-8,atol=1e-10)
            and np.allclose(training.D @ (shape_time @ basis.B),shape_rhs,rtol=1e-8,atol=1e-10)
            and np.allclose(shape_time.sum(axis=1),0.,rtol=1e-8,atol=1e-10),
            'continuous context compensation solve or zero-sum shape differs')
    result = dict(base,context_ids=training.strata+TEMPORAL_IDS,
        volume_context=np.vstack((base['volume_context'],volume_time)),
        shape_context=np.vstack((base['shape_context'],shape_time)))
    result['context'] = result['volume_context']*basis.p+result['shape_context']
    require(np.allclose(result['context'].sum(axis=1,keepdims=True),result['volume_context'],rtol=1e-8,atol=1e-10),
            'continuous complete context does not sum to volume')
    return result


def embed_constant_prediction(prediction, temporal_ids):
    """embed an unchanged saved coarse predictor with exactly zero temporal terms."""
    result = dict(prediction,context_ids=prediction['context_ids']+tuple(temporal_ids))
    for name in ('context','volume_context','shape_context'):
        result[name] = np.vstack((prediction[name],np.zeros((len(temporal_ids),prediction[name].shape[1]))))
    return result
