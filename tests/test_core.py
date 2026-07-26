import numpy as np

from almost_symmetric import (
    NormalFormGame,
    Relabeling,
    add_nonstrategic_component,
    cyclic_action_generator,
    exploitability,
    is_invariant_game,
    project_payoff_linf,
    project_strategic,
    project_strategic_cycle,
    reynolds_symmetrize,
    solve_invariant_saddle_gap,
    solve_zero_sum,
    strategic_distance,
)


def duplicate_generators(q: int, d: int):
    sizes = (q * d, q * d)
    generators = []
    for player in (0, 1):
        for block in range(q):
            actions = list(range(block * d, (block + 1) * d))
            generators.append(cyclic_action_generator(sizes, player, actions))
    return generators


def test_strategic_distance_ignores_nonstrategic_components():
    rng = np.random.default_rng(0)
    game = NormalFormGame(rng.normal(size=(2, 3, 4)))
    shifted = add_nonstrategic_component(
        game,
        [rng.normal(size=(4,)), rng.normal(size=(3,))],
    )
    assert strategic_distance(game, shifted) < 1e-12
    assert np.max(np.abs(game.payoffs - shifted.payoffs)) > 0.1


def test_reynolds_average_is_exactly_invariant():
    rng = np.random.default_rng(1)
    game = NormalFormGame(rng.normal(size=(2, 4, 4)))
    generators = duplicate_generators(q=2, d=2)
    averaged = reynolds_symmetrize(game, generators)
    assert is_invariant_game(averaged, generators, atol=1e-10)


def test_strategic_projection_recovers_zero_defect_after_nonstrategic_shift():
    quotient = np.array([[1.0, -0.5], [0.25, 0.75]])
    matrix = np.repeat(np.repeat(quotient, 2, axis=0), 2, axis=1)
    symmetric = NormalFormGame.zero_sum(matrix)
    shifted = add_nonstrategic_component(
        symmetric,
        [np.array([3.0, -2.0, 3.0, -2.0]), np.array([5.0, 5.0, -4.0, -4.0])],
    )
    generators = duplicate_generators(q=2, d=2)
    strategic = project_strategic(shifted, generators)
    raw = project_payoff_linf(shifted, generators)
    cycle = project_strategic_cycle(shifted, generators)
    assert strategic.distance < 1e-8
    assert cycle.distance < 1e-8
    assert raw.distance > 1.0
    assert is_invariant_game(strategic.game, generators, atol=1e-7)
    assert is_invariant_game(cycle.game, generators, atol=1e-7)


def test_cycle_characterization_matches_projection_lp_random_games():
    generators = duplicate_generators(q=2, d=2)
    for seed in range(8):
        rng = np.random.default_rng(seed + 100)
        game = NormalFormGame(rng.normal(size=(2, 4, 4)))
        lp = project_strategic(game, generators)
        cycle = project_strategic_cycle(game, generators)
        assert abs(lp.distance - cycle.cycle_value) < 2e-7
        assert abs(cycle.distance - cycle.cycle_value) < 2e-7
        assert cycle.witness
        mean_label = np.mean([edge.label for edge in cycle.witness])
        assert abs(abs(mean_label) - cycle.cycle_value) < 2e-7


def test_transfer_bound_for_zero_sum_projection():
    rng = np.random.default_rng(2)
    quotient = rng.normal(size=(3, 3))
    matrix = np.repeat(np.repeat(quotient, 3, axis=0), 3, axis=1)
    matrix += 0.07 * rng.normal(size=matrix.shape)
    game = NormalFormGame.zero_sum(matrix)
    generators = duplicate_generators(q=3, d=3)
    projection = project_strategic(game, generators, structure="zero_sum")
    solution = solve_zero_sum(projection.game.payoffs[0])
    row_regret, column_regret, gap = exploitability(
        matrix, solution.row_strategy, solution.column_strategy
    )
    assert row_regret <= projection.distance + 1e-7
    assert column_regret <= projection.distance + 1e-7
    assert gap <= 2.0 * projection.distance + 2e-7


def test_invariant_gap_solver_matches_exact_symmetric_equilibrium():
    quotient = np.array([[0.0, 1.0], [-1.0, 0.5]])
    matrix = np.repeat(np.repeat(quotient, 3, axis=0), 3, axis=1)
    generators = duplicate_generators(q=2, d=3)
    solution = solve_invariant_saddle_gap(
        matrix,
        generators,
        compress_constraints=True,
        exact_invariant_game=True,
    )
    assert solution.saddle_gap < 1e-9
    for block in range(2):
        row = solution.row_strategy[block * 3 : (block + 1) * 3]
        column = solution.column_strategy[block * 3 : (block + 1) * 3]
        assert np.ptp(row) < 1e-10
        assert np.ptp(column) < 1e-10


def test_reynolds_projection_is_within_factor_two_of_optimal():
    rng = np.random.default_rng(3)
    game = NormalFormGame(rng.normal(size=(2, 4, 4)))
    generators = duplicate_generators(q=2, d=2)
    optimal = project_strategic(game, generators)
    averaged = reynolds_symmetrize(game, generators)
    averaged_distance = strategic_distance(game, averaged)
    assert averaged_distance + 1e-8 >= optimal.distance
    assert averaged_distance <= 2.0 * optimal.distance + 1e-7


def test_cycle_projection_handles_trivial_action_sets():
    game = NormalFormGame(np.array([[[2.0]], [[-5.0]]]))
    result = project_strategic_cycle(game, [])
    assert result.cycle_value == 0.0
    assert result.distance == 0.0



def test_player_swap_symmetry_projection_and_zero_sum_solver():
    """Exercise symmetries that exchange players, not only actions."""
    matrix = np.array(
        [
            [0.0, -1.0, 1.0],
            [1.0, 0.0, -1.0],
            [-1.0, 1.0, 0.0],
        ]
    )
    game = NormalFormGame.zero_sum(matrix)
    identity_actions = tuple(range(3))
    player_swap = Relabeling(
        player_perm=(1, 0),
        action_perms=(identity_actions, identity_actions),
    )
    assert is_invariant_game(game, [player_swap])

    solution = solve_invariant_saddle_gap(
        matrix,
        [player_swap],
        compress_constraints=True,
        exact_invariant_game=True,
    )
    assert solution.saddle_gap < 1e-9
    assert np.max(np.abs(solution.row_strategy - solution.column_strategy)) < 1e-10

    perturbed = NormalFormGame.zero_sum(
        matrix + np.array(
            [
                [0.00, 0.03, -0.01],
                [-0.02, 0.00, 0.04],
                [0.01, -0.03, 0.00],
            ]
        )
    )
    lp = project_strategic(perturbed, [player_swap], structure="zero_sum")
    assert is_invariant_game(lp.game, [player_swap], atol=1e-7)
