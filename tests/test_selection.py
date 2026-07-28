"""Tests for confidence-calibrated symmetry-group selection."""

from __future__ import annotations

import numpy as np

from almost_symmetric import select_symmetry_group


def test_selects_most_compressed_feasible_candidate():
    result = select_symmetry_group(
        [0.01, 0.05, 0.16, 0.30],
        [32, 16, 8, 4],
        radius=0.04,
        budget=0.22,
    )

    assert result.selected_index == 2
    assert result.feasible_indices == (0, 1, 2)
    assert np.allclose(result.certificates, [0.05, 0.09, 0.20, 0.34])


def test_returns_none_when_no_candidate_is_certified():
    result = select_symmetry_group(
        [0.03, 0.10],
        [8, 4],
        radius=0.20,
        budget=0.15,
    )

    assert result.selected_index is None
    assert result.feasible_indices == ()


def test_selected_true_defect_is_within_budget_under_uniform_radius():
    rng = np.random.default_rng(7)
    true_defects = np.array([0.00, 0.06, 0.14, 0.31])
    complexities = np.array([32, 16, 8, 4])
    radius = 0.025
    budget = 0.20

    for _ in range(200):
        estimate = true_defects + rng.uniform(
            -radius, radius, size=true_defects.shape
        )
        estimate = np.maximum(estimate, 0.0)
        result = select_symmetry_group(
            estimate,
            complexities,
            radius=radius,
            budget=budget,
        )
        assert result.selected_index is not None
        assert true_defects[result.selected_index] <= budget + 1e-12


def test_oracle_margin_guarantees_at_least_oracle_compression():
    rng = np.random.default_rng(11)
    true_defects = np.array([0.00, 0.06, 0.14, 0.31])
    complexities = np.array([32, 16, 8, 4])
    radius = 0.02
    budget = 0.20
    margin_feasible = np.flatnonzero(true_defects <= budget - 2.0 * radius)
    oracle_complexity = float(np.min(complexities[margin_feasible]))

    for _ in range(200):
        estimate = true_defects + rng.uniform(
            -radius, radius, size=true_defects.shape
        )
        estimate = np.maximum(estimate, 0.0)
        result = select_symmetry_group(
            estimate,
            complexities,
            radius=radius,
            budget=budget,
        )
        assert result.selected_index is not None
        assert complexities[result.selected_index] <= oracle_complexity
