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
    """Construct a zero-sum family with ratio ``2 - 2 / d``.

    The row player has one orbit of ``d`` actions. The column player has two
    ``d``-action blocks. A distinguished row receives zero in the first block
    and one in the second; every other row receives the opposite payoff. Every
    row and column payoff range is one, so the zero game is an invariant
    surrogate at strategic distance one. Orbit averaging, however, subtracts
    opposing block means and creates a residual range ``2 - 2 / d`` on the
    distinguished row.
    """
    if d < 2:
        raise ValueError("d must be at least two")

    matrix = np.zeros((d, 2 * d), dtype=float)
    matrix[0, d:] = 1.0
    matrix[1:, :d] = 1.0
    game = NormalFormGame.zero_sum(matrix)

    generators = [
        cyclic_action_generator((d, 2 * d), 0, list(range(d))),
        cyclic_action_generator((d, 2 * d), 1, list(range(d))),
        cyclic_action_generator((d, 2 * d), 1, list(range(d, 2 * d))),
    ]
    return game, generators


def run_reynolds_tightness() -> pd.DataFrame:
    rows = []
    for d in [2, 3, 4, 5, 8, 12, 20, 40]:
        game, generators = reynolds_tight_family(d)
        optimal = project_strategic(
            game,
            generators,
            structure="zero_sum",
        )
        cycle = project_strategic_cycle(game, generators)
        averaged = reynolds_symmetrize(game, generators)
        averaged_distance = strategic_distance(game, averaged)
        theory_ratio = 2.0 - 2.0 / d
        rows.append(
            {
                "orbit_size": d,
                "optimal_structured_defect": optimal.distance,
                "cycle_unrestricted_defect": cycle.cycle_value,
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
        table["orbit_size"],
        table["observed_ratio"],
        marker="o",
        label="Computed ratio",
    )
    axis.plot(
        table["orbit_size"],
        table["theory_ratio"],
        linestyle="--",
        label=r"$2-2/d$",
    )
    axis.axhline(2.0, linestyle=":", linewidth=1.0, label="Upper bound 2")
    axis.set_xscale("log")
    axis.set_ylim(0.95, 2.03)
    axis.set_xlabel("Actions in the row orbit $d$")
    axis.set_ylabel("Reynolds distance / optimal defect")
    axis.legend(frameon=False)
    axis.grid(alpha=0.25)
    save_plot(fig, "reynolds_tightness")
