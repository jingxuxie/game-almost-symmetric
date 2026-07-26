"""General-sum experiments for invariant correlated equilibria."""

from __future__ import annotations

from itertools import product
from math import factorial
from time import perf_counter
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from almost_symmetric import (
    NormalFormGame,
    Relabeling,
    correlated_equilibrium_violations,
    project_strategic,
    solve_correlated_equilibrium,
)

from .common import duplicate_generators, save_plot


def _lifted_general_sum(
    q: int,
    d: int,
    rng: np.random.Generator,
) -> np.ndarray:
    quotient = rng.normal(size=(2, q, q))
    quotient /= max(1.0, float(np.max(np.abs(quotient))))
    return np.repeat(np.repeat(quotient, d, axis=1), d, axis=2)


def run_correlated_calibration(seed: int, replicates: int) -> pd.DataFrame:
    """Check CE transfer and direct invariant optimization in general-sum games."""

    rng = np.random.default_rng(seed)
    q, d = 3, 2
    exact_payoffs = _lifted_general_sum(q, d, rng)
    generators = duplicate_generators(q, d)
    rows: list[dict[str, float | int]] = []

    for sigma in [0.0, 0.02, 0.05, 0.10, 0.20, 0.35]:
        for replicate in range(replicates):
            noise_rng = np.random.default_rng(
                seed + 70_000 + replicate + int(10_000 * sigma)
            )
            payoffs = exact_payoffs + sigma * noise_rng.normal(
                size=exact_payoffs.shape
            )
            game = NormalFormGame(payoffs)
            objective = np.sum(payoffs, axis=0)
            projection = project_strategic(game, generators)

            transferred = solve_correlated_equilibrium(
                projection.game,
                generators,
                invariant=True,
                kind="ce",
                objective_values=objective,
            )
            transferred_violation, _ = correlated_equilibrium_violations(
                game, transferred.distribution
            )

            direct = solve_correlated_equilibrium(
                game,
                generators,
                invariant=True,
                kind="ce",
                epsilon=projection.distance,
                objective_values=objective,
            )
            direct_violation, _ = correlated_equilibrium_violations(
                game, direct.distribution
            )

            unrestricted = solve_correlated_equilibrium(
                game,
                kind="ce",
                objective_values=objective,
            )
            rows.append(
                {
                    "sigma": sigma,
                    "replicate": replicate,
                    "strategic_defect": projection.distance,
                    "transferred_ce_violation": transferred_violation,
                    "direct_ce_violation": direct_violation,
                    "certificate": projection.distance,
                    "transferred_welfare": transferred.objective_value,
                    "direct_welfare": direct.objective_value,
                    "unrestricted_ce_welfare": unrestricted.objective_value,
                    "full_profile_variables": unrestricted.n_variables,
                    "orbit_profile_variables": transferred.n_variables,
                }
            )
    return pd.DataFrame(rows)


def _role_assignment_game(n: int) -> NormalFormGame:
    payoffs = np.zeros((n,) + (n,) * n, dtype=float)
    for profile in product(range(n), repeat=n):
        if len(set(profile)) == n:
            payoffs[(slice(None), *profile)] = 1.0
    return NormalFormGame(payoffs)


def _role_assignment_generators(n: int) -> list[Relabeling]:
    sizes = (n,) * n
    identity_actions = tuple(range(n))
    generators: list[Relabeling] = []

    for left in range(n - 1):
        player_perm = list(range(n))
        player_perm[left], player_perm[left + 1] = (
            player_perm[left + 1],
            player_perm[left],
        )
        generators.append(
            Relabeling(
                player_perm=tuple(player_perm),
                action_perms=tuple(identity_actions for _ in range(n)),
            )
        )

    role_cycle = tuple(list(range(1, n)) + [0])
    generators.append(
        Relabeling(
            player_perm=tuple(range(n)),
            action_perms=tuple(role_cycle for _ in range(n)),
        )
    )
    if n >= 2:
        role_swap = list(range(n))
        role_swap[0], role_swap[1] = role_swap[1], role_swap[0]
        generators.append(
            Relabeling(
                player_perm=tuple(range(n)),
                action_perms=tuple(tuple(role_swap) for _ in range(n)),
            )
        )
    for generator in generators:
        generator.validate(sizes)
    return generators


def run_role_assignment_correlation(max_n: int = 10) -> pd.DataFrame:
    """Compare independent invariant play with an invariant correlation device."""

    rows: list[dict[str, float | int]] = []
    for n in range(2, max_n + 1):
        independent = factorial(n) / n**n
        solver_welfare = np.nan
        solver_violation = np.nan
        profile_orbits = np.nan
        if n <= 5:
            game = _role_assignment_game(n)
            generators = _role_assignment_generators(n)
            solution = solve_correlated_equilibrium(
                game,
                generators,
                invariant=True,
                kind="ce",
            )
            solver_welfare = solution.objective_value / n
            solver_violation = solution.ce_violation
            profile_orbits = solution.n_profile_orbits
        rows.append(
            {
                "players_and_roles": n,
                "independent_invariant_welfare": independent,
                "correlated_invariant_welfare": 1.0,
                "solver_welfare": solver_welfare,
                "solver_ce_violation": solver_violation,
                "pure_profiles": n**n,
                "profile_orbits": profile_orbits,
            }
        )
    return pd.DataFrame(rows)


def run_correlated_runtime(
    seed: int,
    *,
    repetitions: int = 3,
    duplicate_factors: Sequence[int] = (1, 2, 3, 4, 6, 8, 12),
) -> pd.DataFrame:
    """Compare full and orbit-variable CE LPs on exactly symmetric games."""

    rng = np.random.default_rng(seed)
    q = 3
    quotient = rng.normal(size=(2, q, q))
    quotient /= max(1.0, float(np.max(np.abs(quotient))))
    rows: list[dict[str, float | int]] = []

    for d in duplicate_factors:
        payoffs = np.repeat(np.repeat(quotient, d, axis=1), d, axis=2)
        game = NormalFormGame(payoffs)
        generators = duplicate_generators(q, d)

        # Warm up HiGHS and sparse matrix construction.
        solve_correlated_equilibrium(game, kind="ce")
        solve_correlated_equilibrium(
            game, generators, invariant=True, kind="ce"
        )

        full_times: list[float] = []
        orbit_times: list[float] = []
        for _ in range(repetitions):
            start = perf_counter()
            full = solve_correlated_equilibrium(game, kind="ce")
            full_times.append(perf_counter() - start)

            start = perf_counter()
            orbit = solve_correlated_equilibrium(
                game,
                generators,
                invariant=True,
                kind="ce",
            )
            orbit_times.append(perf_counter() - start)

        rows.append(
            {
                "actions_per_player": q * d,
                "duplicate_factor": d,
                "full_profile_variables": full.n_variables,
                "orbit_profile_variables": orbit.n_variables,
                "full_time_seconds": float(np.median(full_times)),
                "orbit_time_seconds": float(np.median(orbit_times)),
                "speedup": float(np.median(full_times) / np.median(orbit_times)),
                "welfare_difference": abs(
                    full.objective_value - orbit.objective_value
                ),
            }
        )
    return pd.DataFrame(rows)


def make_correlated_figures(
    calibration: pd.DataFrame,
    role_assignment: pd.DataFrame,
    runtime: pd.DataFrame,
) -> None:
    grouped = calibration.groupby("sigma", as_index=False).agg(
        defect=("strategic_defect", "mean"),
        transferred=("transferred_ce_violation", "mean"),
        direct=("direct_ce_violation", "mean"),
        transferred_welfare=("transferred_welfare", "mean"),
        direct_welfare=("direct_welfare", "mean"),
    )
    fig, axis = plt.subplots(figsize=(3.35, 2.45))
    axis.plot(grouped["sigma"], grouped["defect"], marker="s", label="Certificate $\\delta_G$")
    axis.plot(grouped["sigma"], grouped["transferred"], marker="o", label="Transferred invariant CE")
    axis.plot(grouped["sigma"], grouped["direct"], marker="^", label="Direct invariant $\\delta_G$-CE")
    axis.set_xlabel("Payoff perturbation scale")
    axis.set_ylabel("Maximum CE deviation gain")
    axis.legend(frameon=False)
    axis.grid(alpha=0.25)
    save_plot(fig, "correlated_calibration")

    fig, axis = plt.subplots(figsize=(3.35, 2.45))
    axis.plot(
        role_assignment["players_and_roles"],
        role_assignment["independent_invariant_welfare"],
        marker="o",
        label="Independent invariant play",
    )
    axis.plot(
        role_assignment["players_and_roles"],
        role_assignment["correlated_invariant_welfare"],
        marker="s",
        label="Invariant correlated equilibrium",
    )
    solved = role_assignment.dropna(subset=["solver_welfare"])
    axis.scatter(
        solved["players_and_roles"],
        solved["solver_welfare"],
        marker="x",
        label="LP verification",
    )
    axis.set_xlabel("Agents and distinct roles $n$")
    axis.set_ylabel("Team welfare")
    axis.set_ylim(-0.02, 1.05)
    axis.legend(frameon=False)
    axis.grid(alpha=0.25)
    save_plot(fig, "role_assignment_correlation")

    fig, axis = plt.subplots(figsize=(3.35, 2.45))
    axis.plot(
        runtime["actions_per_player"],
        runtime["full_profile_variables"],
        marker="o",
        label="Full CE LP",
    )
    axis.plot(
        runtime["actions_per_player"],
        runtime["orbit_profile_variables"],
        marker="s",
        label="Orbit-variable CE LP",
    )
    axis.set_xscale("log", base=2)
    axis.set_yscale("log")
    axis.set_xlabel("Actions per player")
    axis.set_ylabel("Joint-distribution variables")
    axis.legend(frameon=False)
    axis.grid(alpha=0.25)
    save_plot(fig, "correlated_compression")
