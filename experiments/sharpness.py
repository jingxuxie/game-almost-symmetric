"""Sharpness constructions for the Reynolds projection theorem."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from almost_symmetric import (
    NormalFormGame,
    cyclic_action_generator,
    project_strategic,
    project_strategic_cycle,
    reynolds_symmetrize,
    strategic_distance,
)

from .common import save_plot


def reynolds_tight_family(d: int):
    """Construct the family with ratio ``2 - 2 / d**2``.

    Each player has two blocks of ``d`` actions. The candidate group independently
    cycles actions inside each block. Player 2 has zero utility. The two critical
    comparisons for player 1 form a mean-minus-one cycle, so the optimal defect is
    one, while orbit averaging approaches distance two.
    """
    if d < 2:
        raise ValueError("d must be at least two")
    action_count = 2 * d
    row_payoff = np.zeros((action_count, action_count), dtype=float)

    row_payoff[1:d, 0] = -1.0
    row_payoff[d, 0] = -1.0
    row_payoff[d:, 1:d] = 1.0

    game = NormalFormGame(
        np.stack([row_payoff, np.zeros_like(row_payoff)], axis=0)
    )
    generators = []
    for player in (0, 1):
        generators.append(
            cyclic_action_generator(
                (action_count, action_count), player, list(range(d))
            )
        )
        generators.append(
            cyclic_action_generator(
                (action_count, action_count), player, list(range(d, 2 * d))
            )
        )
    return game, generators


def run_reynolds_tightness() -> pd.DataFrame:
    rows = []
    for d in [2, 3, 4, 5, 8, 12, 20]:
        game, generators = reynolds_tight_family(d)
        optimal = project_strategic(game, generators)
        cycle = project_strategic_cycle(game, generators)
        averaged = reynolds_symmetrize(game, generators)
        averaged_distance = strategic_distance(game, averaged)
        theory_ratio = 2.0 - 2.0 / d**2
        rows.append(
            {
                "block_size": d,
                "optimal_defect": optimal.distance,
                "cycle_defect": cycle.cycle_value,
                "reynolds_distance": averaged_distance,
                "observed_ratio": averaged_distance / optimal.distance,
                "theory_ratio": theory_ratio,
                "absolute_formula_error": abs(
                    averaged_distance / optimal.distance - theory_ratio
                ),
                "witness_length": len(cycle.witness),
            }
        )
    return pd.DataFrame(rows)


def make_reynolds_tightness_figure(table: pd.DataFrame) -> None:
    fig, axis = plt.subplots(figsize=(3.35, 2.45))
    axis.plot(
        table["block_size"],
        table["observed_ratio"],
        marker="o",
        label="Computed ratio",
    )
    axis.plot(
        table["block_size"],
        table["theory_ratio"],
        linestyle="--",
        label=r"$2-2/d^2$",
    )
    axis.axhline(2.0, linestyle=":", linewidth=1.0, label="Upper bound 2")
    axis.set_xscale("log")
    axis.set_ylim(1.4, 2.03)
    axis.set_xlabel("Actions per block $d$")
    axis.set_ylabel("Reynolds distance / optimal defect")
    axis.legend(frameon=False)
    axis.grid(alpha=0.25)
    save_plot(fig, "reynolds_tightness")
