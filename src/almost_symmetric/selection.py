"""Confidence-calibrated selection among candidate symmetry groups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class SymmetrySelectionResult:
    """Result of selecting the most compressed certified candidate.

    ``complexities`` are minimized, so a smaller value should correspond to a
    more compressed representation, such as fewer action or profile orbits.
    """

    selected_index: int | None
    certificates: np.ndarray
    feasible_indices: tuple[int, ...]
    radius: float
    budget: float


def select_symmetry_group(
    estimated_defects: Sequence[float],
    complexities: Sequence[float],
    *,
    radius: float,
    budget: float,
    atol: float = 1e-12,
) -> SymmetrySelectionResult:
    """Select the lowest-complexity group whose defect is certified.

    The certificate for candidate ``k`` is ``estimated_defects[k] + radius``.
    The routine returns ``selected_index=None`` when no candidate meets the
    requested budget. Ties are broken by the smaller certificate and then by
    the original candidate order.
    """

    defects = np.asarray(estimated_defects, dtype=float)
    costs = np.asarray(complexities, dtype=float)
    if defects.ndim != 1 or costs.ndim != 1:
        raise ValueError("estimated_defects and complexities must be one-dimensional")
    if defects.size == 0 or defects.size != costs.size:
        raise ValueError("candidate arrays must be nonempty and have equal length")
    if not np.all(np.isfinite(defects)) or not np.all(np.isfinite(costs)):
        raise ValueError("candidate values must be finite")
    if np.min(defects) < -atol:
        raise ValueError("estimated defects must be nonnegative")
    if not np.isfinite(radius) or radius < 0.0:
        raise ValueError("radius must be finite and nonnegative")
    if not np.isfinite(budget) or budget < 0.0:
        raise ValueError("budget must be finite and nonnegative")

    certificates = np.maximum(defects, 0.0) + float(radius)
    feasible = tuple(
        int(index)
        for index in np.flatnonzero(certificates <= float(budget) + atol)
    )
    selected: int | None = None
    if feasible:
        selected = min(
            feasible,
            key=lambda index: (costs[index], certificates[index], index),
        )

    return SymmetrySelectionResult(
        selected_index=selected,
        certificates=certificates,
        feasible_indices=feasible,
        radius=float(radius),
        budget=float(budget),
    )
