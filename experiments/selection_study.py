"""Confidence-calibrated selection from a hierarchy of candidate symmetries."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from almost_symmetric import (
    NormalFormGame,
    action_orbit_labels,
    exploitability,
    project_strategic,
    select_symmetry_group,
    solve_invariant_saddle_gap,
    strategic_distance,
)

from .common import duplicate_generators, lifted_matrix, save_plot


GROUP_SIZES = (1, 2, 4, 8)
FULL_SAMPLE_SIZES = (250, 500, 1_000, 2_500, 5_000, 10_000, 25_000)
QUICK_SAMPLE_SIZES = (250, 1_000, 10_000)
SELECTION_BUDGET = 0.38
SELECTION_ALPHA = 0.05


def _bounded_hierarchy_matrix(seed: int) -> tuple[np.ndarray, int, int]:
    """Construct a bounded zero-sum game with a four-level symmetry hierarchy."""

    rng = np.random.default_rng(seed)
    q, d = 2, 8
    _, exact_matrix = lifted_matrix(q, d, rng)
    row_pattern = np.array(
        [-0.30, -0.30, -0.10, -0.10, 0.10, 0.10, 0.40, 0.40]
    )
    column_pattern = np.array(
        [0.35, 0.35, 0.10, 0.10, -0.10, -0.10, -0.30, -0.30]
    )
    raw = exact_matrix.copy()
    raw += np.tile(row_pattern, q)[:, None]
    raw += np.tile(column_pattern, q)[None, :]
    raw += 0.01 * rng.normal(size=raw.shape)

    span = float(np.max(raw) - np.min(raw))
    if span <= 0.0:
        raise RuntimeError("selection hierarchy must have nonconstant payoffs")
    bounded = 0.10 + 0.80 * (raw - np.min(raw)) / span
    return bounded, q, d


def run_statistical_selection(
    seed: int,
    replicates: int,
    *,
    quick: bool = False,
) -> pd.DataFrame:
    """Select the most compressed group whose empirical certificate fits a budget."""

    true_matrix, q, d = _bounded_hierarchy_matrix(seed)
    true_game = NormalFormGame.zero_sum(true_matrix)
    candidates = []
    for group_size in GROUP_SIZES:
        generators = duplicate_generators(q, d, group_size=group_size)
        labels = action_orbit_labels((q * d, q * d), generators)
        projection = project_strategic(
            true_game,
            generators,
            structure="zero_sum",
        )
        candidates.append(
            {
                "group_size": group_size,
                "generators": generators,
                "action_orbits": int(labels.max(initial=-1) + 1),
                "true_defect": float(projection.distance),
            }
        )

    true_defects = np.asarray(
        [candidate["true_defect"] for candidate in candidates], dtype=float
    )
    complexities = np.asarray(
        [candidate["action_orbits"] for candidate in candidates], dtype=float
    )
    oracle_feasible = np.flatnonzero(true_defects <= SELECTION_BUDGET + 1e-12)
    if oracle_feasible.size == 0:
        raise RuntimeError("the synthetic selection hierarchy has no feasible group")
    oracle_index = min(
        (int(index) for index in oracle_feasible),
        key=lambda index: (complexities[index], true_defects[index], index),
    )

    sample_sizes = QUICK_SAMPLE_SIZES if quick else FULL_SAMPLE_SIZES
    m, n = true_matrix.shape
    rows = []
    for samples in sample_sizes:
        entry_radius = np.sqrt(
            np.log(2.0 * m * n / SELECTION_ALPHA) / (2.0 * samples)
        )
        strategic_radius = 2.0 * entry_radius
        for replicate in range(replicates):
            sample_rng = np.random.default_rng(
                seed + 90_000 + samples * 100 + replicate
            )
            estimate = sample_rng.binomial(samples, true_matrix) / samples
            estimate_game = NormalFormGame.zero_sum(estimate)

            projections = []
            estimated_defects = []
            for candidate in candidates:
                projection = project_strategic(
                    estimate_game,
                    candidate["generators"],
                    structure="zero_sum",
                )
                projections.append(projection)
                estimated_defects.append(float(projection.distance))

            selection = select_symmetry_group(
                estimated_defects,
                complexities,
                radius=strategic_radius,
                budget=SELECTION_BUDGET,
            )
            if selection.selected_index is None:
                raise RuntimeError(
                    "no candidate met the synthetic selection budget; "
                    "increase the minimum sample size"
                )
            selected_index = selection.selected_index
            selected = candidates[selected_index]
            selected_projection = projections[selected_index]
            solution = solve_invariant_saddle_gap(
                selected_projection.game.payoffs[0],
                selected["generators"],
                compress_constraints=True,
                exact_invariant_game=True,
            )
            row_regret, column_regret, gap = exploitability(
                true_matrix,
                solution.row_strategy,
                solution.column_strategy,
            )
            certificate = float(selection.certificates[selected_index])
            actual_estimation_distance = strategic_distance(
                true_game,
                estimate_game,
            )
            rows.append(
                {
                    "samples_per_entry": samples,
                    "replicate": replicate,
                    "budget": SELECTION_BUDGET,
                    "confidence_level": 1.0 - SELECTION_ALPHA,
                    "entry_radius": entry_radius,
                    "strategic_radius": strategic_radius,
                    "selected_index": selected_index,
                    "selected_group_size": selected["group_size"],
                    "selected_action_orbits": selected["action_orbits"],
                    "selected_estimated_defect": estimated_defects[selected_index],
                    "selected_true_defect": selected["true_defect"],
                    "selected_certificate": certificate,
                    "true_max_regret": max(row_regret, column_regret),
                    "true_saddle_gap": gap,
                    "oracle_group_size": candidates[oracle_index]["group_size"],
                    "oracle_action_orbits": candidates[oracle_index]["action_orbits"],
                    "oracle_true_defect": candidates[oracle_index]["true_defect"],
                    "selected_oracle": selected_index == oracle_index,
                    "confidence_event": (
                        actual_estimation_distance <= strategic_radius + 1e-12
                    ),
                    "defect_covered": (
                        selected["true_defect"] <= certificate + 1e-9
                    ),
                    "regret_covered": (
                        max(row_regret, column_regret) <= certificate + 1e-9
                    ),
                }
            )
    return pd.DataFrame(rows)


def make_selection_figures(table: pd.DataFrame) -> None:
    """Plot compression and certificate behavior as payoff data increase."""

    grouped = table.groupby("samples_per_entry", as_index=False).agg(
        selected_orbits_median=("selected_action_orbits", "median"),
        selected_orbits_q10=(
            "selected_action_orbits",
            lambda values: float(np.quantile(values, 0.10)),
        ),
        selected_orbits_q90=(
            "selected_action_orbits",
            lambda values: float(np.quantile(values, 0.90)),
        ),
        selected_certificate_mean=("selected_certificate", "mean"),
        selected_true_defect_mean=("selected_true_defect", "mean"),
        true_max_regret_mean=("true_max_regret", "mean"),
        oracle_action_orbits=("oracle_action_orbits", "first"),
        budget=("budget", "first"),
    )

    fig, axis = plt.subplots(figsize=(3.35, 2.25))
    axis.plot(
        grouped["samples_per_entry"],
        grouped["selected_orbits_median"],
        marker="o",
        label="Selected group",
    )
    axis.fill_between(
        grouped["samples_per_entry"],
        grouped["selected_orbits_q10"],
        grouped["selected_orbits_q90"],
        alpha=0.18,
        label="10--90% range",
    )
    axis.axhline(
        float(grouped["oracle_action_orbits"].iloc[0]),
        linestyle="--",
        label="Oracle compression",
    )
    axis.set_xscale("log")
    axis.set_xlabel("Samples per payoff entry")
    axis.set_ylabel("Action-orbit variables")
    axis.set_yticks(sorted(table["selected_action_orbits"].unique()))
    axis.grid(alpha=0.25)
    axis.legend(frameon=False)
    save_plot(fig, "statistical_selection_compression")

    fig, axis = plt.subplots(figsize=(3.35, 2.25))
    axis.plot(
        grouped["samples_per_entry"],
        grouped["selected_certificate_mean"],
        marker="o",
        label="Selection certificate",
    )
    axis.plot(
        grouped["samples_per_entry"],
        grouped["selected_true_defect_mean"],
        marker="s",
        label="True selected defect",
    )
    axis.plot(
        grouped["samples_per_entry"],
        grouped["true_max_regret_mean"],
        marker="^",
        label="True maximum regret",
    )
    axis.axhline(
        float(grouped["budget"].iloc[0]),
        linestyle="--",
        label="Target budget",
    )
    axis.set_xscale("log")
    axis.set_xlabel("Samples per payoff entry")
    axis.set_ylabel("Defect or regret")
    axis.grid(alpha=0.25)
    axis.legend(frameon=False)
    save_plot(fig, "statistical_selection_certificate")
