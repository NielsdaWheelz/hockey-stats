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
