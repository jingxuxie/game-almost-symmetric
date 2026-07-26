"""Shared deterministic experiment utilities."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from almost_symmetric import cyclic_action_generator

mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42
mpl.rcParams["font.size"] = 9
mpl.rcParams["axes.labelsize"] = 9
mpl.rcParams["legend.fontsize"] = 8

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments" / "results"
FIGURES = ROOT / "experiments" / "figures"

def duplicate_generators(q: int, d: int, group_size: int | None = None):
    """Cycle duplicate actions inside each quotient-action block."""
    h = d if group_size is None else group_size
    if h < 1 or d % h != 0:
        raise ValueError("group_size must be a positive divisor of d")
    sizes = (q * d, q * d)
    generators = []
    if h == 1:
        return generators
    for player in (0, 1):
        for block in range(q):
            block_start = block * d
            for subgroup_start in range(0, d, h):
                actions = list(
                    range(block_start + subgroup_start, block_start + subgroup_start + h)
                )
                generators.append(cyclic_action_generator(sizes, player, actions))
    return generators

def lifted_matrix(
    q: int, d: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    quotient = rng.normal(size=(q, q))
    quotient /= max(1.0, float(np.max(np.abs(quotient))))
    matrix = np.repeat(np.repeat(quotient, d, axis=0), d, axis=1)
    return quotient, matrix

def save_plot(fig: plt.Figure, filename: str) -> None:
    fig.tight_layout()
    fig.savefig(FIGURES / f"{filename}.pdf", bbox_inches="tight")
    fig.savefig(FIGURES / f"{filename}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
