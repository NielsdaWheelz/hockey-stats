"""fixed native location transports projected through both covariance terms."""

import numpy as np

from .artifacts import require
from .attribution import AnnualState, project
from .shot_origins import grid


def location_transport(direction: str) -> tuple[np.ndarray, dict]:
    """one mass-conserving native-grid move; nominal targets may leave the rink."""
    require(direction in ("toward", "away"), "unknown location stress direction")
    centers, _ = grid()
    displacement = np.array([89.0, 0.0]) - centers
    distances = np.linalg.norm(displacement, axis=1)
    nonzero = distances != 0
    targets = centers.copy()
    targets[nonzero] += (
        (5 if direction == "toward" else -5) * displacement[nonzero] / distances[nonzero, None]
    )
    destinations = np.argmin(np.sum((centers[:, None, :] - targets[None, :, :]) ** 2, axis=2), axis=0)
    transport = np.zeros((len(centers), len(centers)))
    transport[destinations, np.arange(len(centers))] = 1
    return transport, dict(
        direction=direction,
        nominal_displacement_feet=5,
        goal_coordinate=[89, 0],
        destination_cells=destinations.tolist(),
        actual_displacement_feet=np.linalg.norm(centers[destinations] - centers, axis=1).tolist(),
    )


def project_transport(
    state: AnnualState, transport: np.ndarray, player_contrast: np.ndarray, response_weights: np.ndarray
) -> tuple[float, float]:
    """transport both covariance terms by pulling back the response functional."""
    transport = np.asarray(transport, dtype=float)
    v = np.asarray(response_weights, dtype=float)
    k = 1 if state.p is None else len(state.p)
    require(
        transport.ndim == 2
        and transport.shape[1] == k
        and v.shape == (transport.shape[0],)
        and np.isfinite(transport).all()
        and np.isfinite(v).all()
        and np.all(transport >= 0)
        and np.allclose(transport.sum(axis=0), 1, rtol=0, atol=1e-12),
        "response transport must be finite, nonnegative and column stochastic",
    )
    return project(state, player_contrast, transport.T @ v)
