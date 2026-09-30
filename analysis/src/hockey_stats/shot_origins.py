"""fixed rink geometry and forward block observation law for chance-2."""

import numpy as np
from scipy.special import logsumexp

from .captures import InputContractError


def in_rink(x, y):
    return (
        abs(x) <= 100
        and abs(y) <= 42.5
        and max(abs(x) - 72, 0) ** 2 + max(abs(y) - 14.5, 0) ** 2 <= 28**2
    )


def grid():
    centers = np.array(
        [
            (x, y)
            for x in np.arange(-97.5, 100, 5)
            for y in np.arange(-40, 45, 5)
            if in_rink(x, y)
        ],
        dtype=np.float64,
    )
    lookup = {tuple(point): i for i, point in enumerate(centers)}
    edges = [
        (i, lookup[neighbor])
        for i, (x, y) in enumerate(centers)
        for neighbor in ((x + 5, y), (x, y + 5))
        if neighbor in lookup
    ]
    return centers, np.array(edges, dtype=np.int64)


def cell_id(point, centers=None):
    try:
        point = np.asarray(point, dtype=np.float64)
    except (ValueError, TypeError) as error:
        raise InputContractError("invalid origin coordinates") from error
    if (
        point.shape != (2,)
        or not np.isfinite(point).all()
        or not in_rink(point[0], point[1])
    ):
        raise InputContractError("origin coordinates outside rink")
    if centers is None:
        centers, _ = grid()
    return int(np.argmin(np.sum((centers - point) ** 2, axis=1)))


def forward_kernel(centers, distance_ft, direction_strength):
    """return log K[block, origin], normalized over block cells."""
    delta = centers[:, None, :] - centers[None, :, :]
    distance = np.linalg.norm(delta, axis=2)
    goal = np.array([89.0, 0.0]) - centers
    denominator = distance * np.linalg.norm(goal, axis=1)[None, :]
    cosine = np.divide(
        np.sum(delta * goal[None, :, :], axis=2),
        denominator,
        out=np.ones_like(distance),
        where=denominator != 0,
    )
    log_weight = -distance / distance_ft - direction_strength * (
        1 - np.clip(cosine, -1, 1)
    )
    return log_weight - logsumexp(log_weight, axis=0, keepdims=True)


def posterior(log_origin, log_block_probability, log_kernel_row):
    log_mass = log_origin + log_block_probability + log_kernel_row
    likelihood = logsumexp(log_mass, axis=-1)
    return np.exp(log_mass - np.expand_dims(likelihood, -1)), likelihood
