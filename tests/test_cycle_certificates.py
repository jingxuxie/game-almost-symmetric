"""Adversarial regression tests for cycle witnesses and sharp constants."""

from __future__ import annotations

import numpy as np

from almost_symmetric import (
    NormalFormGame,
    Relabeling,
    build_incentive_graph,
    cyclic_action_generator,
    project_strategic,
    project_strategic_cycle,
    reynolds_symmetrize,
    solve_invariant_saddle_gap,
    strategic_distance,
)


def _duplicate_generators(q: int, d: int):
    sizes = (q * d, q * d)
    generators = []
    for player in (0, 1):
        for block in range(q):
            actions = list(range(block * d, (block + 1) * d))
            generators.append(cyclic_action_generator(sizes, player, actions))
    return generators


def _assert_witness_is_critical(result, atol: float = 5e-7) -> None:
    assert result.witness
    for edge, next_edge in zip(
        result.witness, result.witness[1:] + result.witness[:1]
    ):
        assert edge.head == next_edge.tail
    witness_value = float(np.mean([-edge.label for edge in result.witness]))
    assert abs(witness_value - result.cycle_value) <= atol


def _reynolds_tight_family(d: int):
    """Return the family attaining Reynolds ratio 2 - 2/d^2."""
    if d < 2:
        raise ValueError("d must be at least two")
    action_count = 2 * d
    row_payoff = np.zeros((action_count, action_count), dtype=float)

    # Only the first column block is nonzero. Rows are split into R0 and R1.
    # At the special column t=0:
    #   R0: [0, -1, ..., -1], R1: [-1, 0, ..., 0].
    # At every other column in C0:
    #   R0: all 0, R1: all 1.
    row_payoff[1:d, 0] = -1.0
    row_payoff[d, 0] = -1.0
    row_payoff[d:, 1:d] = 1.0

    payoffs = np.stack([row_payoff, np.zeros_like(row_payoff)], axis=0)
    game = NormalFormGame(payoffs)
    generators = []
    for player in (0, 1):
        generators.append(
            cyclic_action_generator(
                (action_count, action_count), player, list(range(0, d))
            )
        )
        generators.append(
            cyclic_action_generator(
                (action_count, action_count), player, list(range(d, 2 * d))
            )
        )
    return game, generators


def test_self_loop_is_retained_as_a_critical_obstruction():
    payoffs = np.zeros((2, 2, 1), dtype=float)
    payoffs[0, :, 0] = [0.0, 2.0]
    game = NormalFormGame(payoffs)
    generator = cyclic_action_generator((2, 1), 0, [0, 1])

    result = project_strategic_cycle(game, [generator])

    assert abs(result.cycle_value - 2.0) < 1e-8
    assert len(result.witness) == 1
    assert result.witness[0].tail == result.witness[0].head
    assert abs(result.witness[0].label + 2.0) < 1e-8
    _assert_witness_is_critical(result)


def test_parallel_edges_keep_the_strongest_difference_constraints():
    payoffs = np.zeros((2, 2, 2), dtype=float)
    payoffs[0, 1, 0] = 1.0
    payoffs[0, 1, 1] = 3.0
    game = NormalFormGame(payoffs)
    generator = cyclic_action_generator((2, 2), 1, [0, 1])

    n_vertices, edges, _ = build_incentive_graph(game, [generator])
    result = project_strategic_cycle(game, [generator])

    assert n_vertices > 0
    assert any(abs(edge.label - 1.0) < 1e-10 for edge in edges)
    assert any(abs(edge.label + 3.0) < 1e-10 for edge in edges)
    assert abs(result.cycle_value - 1.0) < 1e-8
    _assert_witness_is_critical(result)


def test_tight_edge_witness_matches_lp_on_random_games():
    generators = _duplicate_generators(q=2, d=2)
    for seed in range(100):
        rng = np.random.default_rng(1_000 + seed)
        game = NormalFormGame(rng.normal(size=(2, 4, 4)))
        lp = project_strategic(game, generators)
        cycle = project_strategic_cycle(game, generators)

        assert abs(lp.distance - cycle.cycle_value) < 5e-7
        assert abs(cycle.distance - cycle.cycle_value) < 5e-7
        _assert_witness_is_critical(cycle)


def test_reynolds_factor_two_is_asymptotically_tight():
    for d in (2, 3, 4, 6, 10):
        game, generators = _reynolds_tight_family(d)
        optimal = project_strategic(game, generators)
        cycle = project_strategic_cycle(game, generators)
        averaged = reynolds_symmetrize(game, generators)
        averaged_distance = strategic_distance(game, averaged)

        assert abs(optimal.distance - 1.0) < 2e-7
        assert abs(cycle.cycle_value - 1.0) < 2e-7
        assert abs(averaged_distance - (2.0 - 2.0 / d**2)) < 2e-7
        assert averaged_distance <= 2.0 * optimal.distance + 2e-7


def test_player_swap_compression_matches_uncompressed_program():
    matrix = np.array(
        [
            [0.0, -1.0, 1.0],
            [1.0, 0.0, -1.0],
            [-1.0, 1.0, 0.0],
        ]
    )
    identity_actions = tuple(range(3))
    player_swap = Relabeling(
        player_perm=(1, 0),
        action_perms=(identity_actions, identity_actions),
    )

    uncompressed = solve_invariant_saddle_gap(matrix, [player_swap])
    compressed = solve_invariant_saddle_gap(
        matrix,
        [player_swap],
        compress_constraints=True,
        exact_invariant_game=True,
    )

    assert uncompressed.saddle_gap < 1e-9
    assert compressed.saddle_gap < 1e-9
    assert abs(np.sum(compressed.row_strategy) - 1.0) < 1e-10
    assert abs(np.sum(compressed.column_strategy) - 1.0) < 1e-10
    assert np.max(
        np.abs(compressed.row_strategy - compressed.column_strategy)
    ) < 1e-10
