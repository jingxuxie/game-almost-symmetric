"""Regression tests for invariant CE/CCE computation and transfer."""

from __future__ import annotations

from itertools import product
from math import factorial

import numpy as np

from almost_symmetric import (
    NormalFormGame,
    Relabeling,
    correlated_equilibrium_violations,
    is_invariant_distribution,
    profile_orbit_labels,
    project_strategic,
    solve_correlated_equilibrium,
)


def _player_swap_two_actions() -> Relabeling:
    identity = (0, 1)
    return Relabeling(
        player_perm=(1, 0),
        action_perms=(identity, identity),
    )


def _role_assignment_game(n: int) -> NormalFormGame:
    payoffs = np.zeros((n,) + (n,) * n, dtype=float)
    for profile in product(range(n), repeat=n):
        if len(set(profile)) == n:
            payoffs[(slice(None), *profile)] = 1.0
    return NormalFormGame(payoffs)


def _full_role_assignment_generators(n: int) -> list[Relabeling]:
    sizes = (n,) * n
    identity_actions = tuple(range(n))
    generators: list[Relabeling] = []

    # Adjacent player transpositions generate all player permutations.
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

    # A common role cycle and transposition generate all role relabelings.
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


def test_ce_and_cce_transfer_through_strategic_projection():
    base = np.array([[2.0, 0.0], [0.0, 1.0]])
    symmetric = np.stack([base, base], axis=0)
    perturbation = np.array(
        [
            [[0.10, -0.04], [0.02, -0.08]],
            [[-0.03, 0.07], [-0.06, 0.05]],
        ]
    )
    game = NormalFormGame(symmetric + perturbation)
    generator = _player_swap_two_actions()
    projection = project_strategic(game, [generator])

    ce = solve_correlated_equilibrium(
        projection.game,
        [generator],
        invariant=True,
        kind="ce",
    )
    cce = solve_correlated_equilibrium(
        projection.game,
        [generator],
        invariant=True,
        kind="cce",
    )
    ce_violation, _ = correlated_equilibrium_violations(game, ce.distribution)
    _, cce_violation = correlated_equilibrium_violations(game, cce.distribution)

    assert is_invariant_distribution(ce.distribution, [generator])
    assert is_invariant_distribution(cce.distribution, [generator])
    assert ce_violation <= projection.distance + 2e-7
    assert cce_violation <= projection.distance + 2e-7


def test_role_assignment_correlation_recovers_full_welfare():
    n = 3
    game = _role_assignment_game(n)
    generators = _full_role_assignment_generators(n)
    solution = solve_correlated_equilibrium(
        game,
        generators,
        invariant=True,
        kind="ce",
    )

    ce_violation, _ = correlated_equilibrium_violations(
        game, solution.distribution
    )
    success_probability = solution.objective_value / n
    independent_success = factorial(n) / n**n

    assert is_invariant_distribution(solution.distribution, generators)
    assert ce_violation < 1e-9
    assert abs(success_probability - 1.0) < 1e-9
    assert independent_success < success_probability
    for profile in product(range(n), repeat=n):
        if len(set(profile)) < n:
            assert solution.distribution[profile] < 1e-9


def test_invariant_welfare_optimum_matches_full_ce_in_exact_game():
    n = 3
    game = _role_assignment_game(n)
    generators = _full_role_assignment_generators(n)
    full = solve_correlated_equilibrium(game, kind="ce")
    invariant = solve_correlated_equilibrium(
        game,
        generators,
        invariant=True,
        kind="ce",
    )

    assert abs(full.objective_value - invariant.objective_value) < 1e-8
    assert invariant.n_variables < full.n_variables


def test_profile_orbits_handle_player_swaps():
    generator = _player_swap_two_actions()
    labels = profile_orbit_labels((2, 2), [generator]).reshape(2, 2)

    assert labels[0, 1] == labels[1, 0]
    assert labels[0, 0] != labels[0, 1]
    assert labels[1, 1] != labels[0, 1]
