"""Lightweight synthetic studies used in the paper."""

from __future__ import annotations

import itertools
import time

import numpy as np
import pandas as pd

from almost_symmetric import (
    NormalFormGame,
    Relabeling,
    action_orbit_labels,
    add_nonstrategic_component,
    exploitability,
    project_payoff_linf,
    project_strategic,
    project_strategic_cycle,
    pure_regrets,
    reynolds_symmetrize,
    solve_invariant_saddle_gap,
    solve_zero_sum,
    strategic_distance,
    cyclic_action_generator,
)

from .common import duplicate_generators, lifted_matrix

def run_nonstrategic(seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    q, d = 3, 3
    _, matrix = lifted_matrix(q, d, rng)
    base = NormalFormGame.zero_sum(matrix)
    generators = duplicate_generators(q, d)
    component_0 = rng.normal(size=(q * d,))
    component_1 = rng.normal(size=(q * d,))
    component_0 /= np.max(np.abs(component_0))
    component_1 /= np.max(np.abs(component_1))

    rows = []
    for scale in [0.0, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]:
        shifted = add_nonstrategic_component(
            base,
            [scale * component_0, scale * component_1],
        )
        strategic = project_strategic(shifted, generators)
        raw = project_payoff_linf(shifted, generators)
        averaged = reynolds_symmetrize(shifted, generators)
        rows.append(
            {
                "scale": scale,
                "strategic_defect": strategic.distance,
                "raw_payoff_defect": raw.distance,
                "reynolds_strategic_distance": strategic_distance(shifted, averaged),
            }
        )
    return pd.DataFrame(rows)

def run_cycle_characterization(seed: int, replicates: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    generators = duplicate_generators(q=2, d=2)
    rows = []
    for replicate in range(replicates):
        game = NormalFormGame(rng.normal(size=(2, 4, 4)))
        start = time.perf_counter()
        lp = project_strategic(game, generators)
        lp_time = time.perf_counter() - start
        start = time.perf_counter()
        cycle = project_strategic_cycle(game, generators)
        cycle_time = time.perf_counter() - start
        witness_mean = (
            abs(float(np.mean([edge.label for edge in cycle.witness])))
            if cycle.witness
            else 0.0
        )
        rows.append(
            {
                "replicate": replicate,
                "lp_defect": lp.distance,
                "cycle_defect": cycle.cycle_value,
                "projected_distance": cycle.distance,
                "witness_mean_inconsistency": witness_mean,
                "witness_length": len(cycle.witness),
                "graph_vertices": cycle.n_vertices,
                "graph_edges": cycle.n_edges,
                "lp_time_seconds": lp_time,
                "cycle_time_seconds": cycle_time,
            }
        )
    return pd.DataFrame(rows)

def run_calibration(seed: int, replicates: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    q, d = 3, 3
    _, exact_matrix = lifted_matrix(q, d, rng)
    generators = duplicate_generators(q, d)
    rows = []
    for sigma in [0.0, 0.01, 0.03, 0.05, 0.10, 0.20, 0.35]:
        for replicate in range(replicates):
            noise_rng = np.random.default_rng(
                seed + 10_000 + replicate + int(10_000 * sigma)
            )
            matrix = exact_matrix + sigma * noise_rng.normal(size=exact_matrix.shape)
            game = NormalFormGame.zero_sum(matrix)

            projection = project_strategic(game, generators, structure="zero_sum")
            surrogate_solution = solve_invariant_saddle_gap(
                projection.game.payoffs[0],
                generators,
                compress_constraints=True,
                exact_invariant_game=True,
            )
            row_regret, column_regret, gap = exploitability(
                matrix,
                surrogate_solution.row_strategy,
                surrogate_solution.column_strategy,
            )

            averaged = reynolds_symmetrize(game, generators)
            average_distance = strategic_distance(game, averaged)
            average_solution = solve_invariant_saddle_gap(
                averaged.payoffs[0],
                generators,
                compress_constraints=True,
                exact_invariant_game=True,
            )
            _, _, average_gap = exploitability(
                matrix,
                average_solution.row_strategy,
                average_solution.column_strategy,
            )

            direct = solve_invariant_saddle_gap(matrix, generators)
            rows.append(
                {
                    "sigma": sigma,
                    "replicate": replicate,
                    "strategic_defect": projection.distance,
                    "reynolds_distance": average_distance,
                    "reynolds_over_optimal": (
                        average_distance / projection.distance
                        if projection.distance > 1e-10
                        else 1.0
                    ),
                    "row_regret": row_regret,
                    "column_regret": column_regret,
                    "saddle_gap": gap,
                    "certificate": 2.0 * projection.distance,
                    "reynolds_saddle_gap": average_gap,
                    "reynolds_certificate": 2.0 * average_distance,
                    "direct_invariant_gap": direct.saddle_gap,
                }
            )
    return pd.DataFrame(rows)

def run_hierarchy(seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    q, d = 3, 8
    _, exact_matrix = lifted_matrix(q, d, rng)
    row_pattern = np.array([-0.30, -0.30, -0.10, -0.10, 0.10, 0.10, 0.40, 0.40])
    column_pattern = np.array([0.35, 0.35, 0.10, 0.10, -0.10, -0.10, -0.30, -0.30])
    row_bias = np.tile(row_pattern, q)
    column_bias = np.tile(column_pattern, q)
    matrix = exact_matrix + row_bias[:, None] + column_bias[None, :]
    matrix += 0.01 * rng.normal(size=exact_matrix.shape)
    game = NormalFormGame.zero_sum(matrix)

    rows = []
    for group_size in [1, 2, 4, 8]:
        generators = duplicate_generators(q, d, group_size=group_size)
        labels = action_orbit_labels((q * d, q * d), generators)
        start = time.perf_counter()
        projection = project_strategic(game, generators, structure="zero_sum")
        projection_time = time.perf_counter() - start
        solution = solve_invariant_saddle_gap(
            projection.game.payoffs[0],
            generators,
            compress_constraints=True,
            exact_invariant_game=True,
        )
        _, _, gap = exploitability(
            matrix, solution.row_strategy, solution.column_strategy
        )
        direct = solve_invariant_saddle_gap(matrix, generators)
        rows.append(
            {
                "group_size": group_size,
                "action_orbits": int(labels.max(initial=-1) + 1),
                "profile_variables_full": 2 * q * d,
                "strategic_defect": projection.distance,
                "saddle_gap": gap,
                "certificate": 2.0 * projection.distance,
                "direct_invariant_gap": direct.saddle_gap,
                "projection_time_seconds": projection_time,
            }
        )
    return pd.DataFrame(rows)

def _symmetric_team_equilibria(matrix: np.ndarray) -> list[np.ndarray]:
    """Enumerate symmetric equilibria of a small symmetric common-payoff game."""
    matrix = np.asarray(matrix, dtype=float)
    m = matrix.shape[0]
    equilibria: list[np.ndarray] = []
    for support_size in range(1, m + 1):
        for support_tuple in itertools.combinations(range(m), support_size):
            support = np.asarray(support_tuple, dtype=int)
            system = np.block(
                [
                    [matrix[np.ix_(support, support)], -np.ones((support_size, 1))],
                    [np.ones((1, support_size)), np.zeros((1, 1))],
                ]
            )
            target = np.concatenate([np.zeros(support_size), np.ones(1)])
            solution, *_ = np.linalg.lstsq(system, target, rcond=None)
            if np.max(np.abs(system @ solution - target), initial=0.0) > 1e-7:
                continue
            strategy = np.zeros(m, dtype=float)
            strategy[support] = solution[:support_size]
            if np.min(strategy[support], initial=0.0) < -1e-8:
                continue
            strategy = np.maximum(strategy, 0.0)
            strategy /= np.sum(strategy)
            action_values = matrix @ strategy
            equilibrium_value = float(np.max(action_values[support]))
            if np.max(action_values - equilibrium_value, initial=0.0) > 1e-7:
                continue
            if not any(np.max(np.abs(strategy - other)) < 1e-7 for other in equilibria):
                equilibria.append(strategy)
    return equilibria

def run_role_assignment() -> pd.DataFrame:
    """Two heterogeneous agents choose complementary operational roles."""
    base = np.array(
        [
            [0.00, 0.90, 1.00, 0.80],
            [0.90, 0.00, 0.75, 1.10],
            [1.00, 0.75, 0.00, 0.95],
            [0.80, 1.10, 0.95, 0.00],
        ]
    )
    agent_one_skill = np.array([0.60, 0.20, -0.30, -0.10])
    agent_two_skill = np.array([-0.20, 0.50, 0.10, -0.40])
    identity_actions = tuple(range(base.shape[0]))
    player_swap = Relabeling(
        player_perm=(1, 0),
        action_perms=(identity_actions, identity_actions),
    )
    rows = []
    for heterogeneity in [0.00, 0.05, 0.10, 0.20, 0.40]:
        welfare = base + heterogeneity * (
            agent_one_skill[:, None] + agent_two_skill[None, :]
        )
        game = NormalFormGame(np.stack([welfare, welfare], axis=0))
        projection = project_strategic(game, [player_swap], structure="team")
        symmetric_matrix = projection.game.payoffs[0]
        equilibria = _symmetric_team_equilibria(symmetric_matrix)
        if not equilibria:
            raise RuntimeError("failed to find a symmetric equilibrium in role assignment")
        # Select by true team welfare only to make the deterministic reporting rule
        # invariant to arbitrary payoff constants in a strategically equivalent surrogate.
        strategy = max(equilibria, key=lambda x: float(x @ welfare @ x))
        regrets = pure_regrets(game, [strategy, strategy])
        rows.append(
            {
                "heterogeneity": heterogeneity,
                "strategic_defect": projection.distance,
                "max_regret": float(np.max(regrets)),
                "agent_one_regret": float(regrets[0]),
                "agent_two_regret": float(regrets[1]),
                "symmetric_team_welfare": float(strategy @ welfare @ strategy),
                "best_joint_welfare": float(np.max(welfare)),
            }
        )
    return pd.DataFrame(rows)

def run_tightness() -> pd.DataFrame:
    rows = []
    for orbit_size in [2, 3, 5, 10, 20, 50, 100]:
        payoffs = np.zeros((2, orbit_size, 2), dtype=float)
        payoffs[0, 0, :] = 1.0
        game = NormalFormGame(payoffs)
        generator = cyclic_action_generator(
            (orbit_size, 2), 0, list(range(orbit_size))
        )
        projection = project_strategic(game, [generator])
        strategies = [
            np.full(orbit_size, 1.0 / orbit_size),
            np.array([0.5, 0.5]),
        ]
        regret = pure_regrets(game, strategies)[0]
        rows.append(
            {
                "orbit_size": orbit_size,
                "strategic_defect": projection.distance,
                "invariant_regret": regret,
                "regret_over_defect": regret / projection.distance,
                "theory_ratio": 1.0 - 1.0 / orbit_size,
            }
        )
    return pd.DataFrame(rows)

def run_runtime(seed: int, repetitions: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    q = 4
    quotient = rng.normal(size=(q, q))
    quotient /= np.max(np.abs(quotient))
    rows = []
    for duplicate_factor in [1, 2, 4, 8, 16, 32, 64, 128]:
        matrix = np.repeat(
            np.repeat(quotient, duplicate_factor, axis=0),
            duplicate_factor,
            axis=1,
        )
        generators = duplicate_generators(q, duplicate_factor)
        full_times = []
        orbit_times = []
        for _ in range(repetitions):
            start = time.perf_counter()
            full = solve_zero_sum(matrix)
            full_times.append(time.perf_counter() - start)
            start = time.perf_counter()
            orbit = solve_invariant_saddle_gap(
                matrix,
                generators,
                compress_constraints=True,
                exact_invariant_game=True,
            )
            orbit_times.append(time.perf_counter() - start)
        rows.append(
            {
                "actions_per_player": q * duplicate_factor,
                "duplicate_factor": duplicate_factor,
                "full_time_seconds": float(np.median(full_times)),
                "orbit_time_seconds": float(np.median(orbit_times)),
                "speedup": float(np.median(full_times) / np.median(orbit_times)),
                "full_gap": full.saddle_gap,
                "orbit_gap": orbit.saddle_gap,
                "orbit_variables": orbit.n_variables,
            }
        )
    return pd.DataFrame(rows)

def run_sampling(seed: int, replicates: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    q, d = 3, 3
    _, exact = lifted_matrix(q, d, rng)
    true_matrix = np.clip(
        0.5 + 0.30 * exact + 0.03 * rng.normal(size=exact.shape),
        0.05,
        0.95,
    )
    generators = duplicate_generators(q, d)
    alpha = 0.05
    rows = []
    m, n = true_matrix.shape
    for samples in [5, 10, 25, 50, 100, 250, 500, 1000]:
        epsilon = np.sqrt(np.log(2.0 * m * n / alpha) / (2.0 * samples))
        for replicate in range(replicates):
            sample_rng = np.random.default_rng(
                seed + 50_000 + samples * 100 + replicate
            )
            positives = sample_rng.binomial(samples, true_matrix)
            estimate = positives / samples
            estimate_game = NormalFormGame.zero_sum(estimate)
            projection = project_strategic(
                estimate_game, generators, structure="zero_sum"
            )
            solution = solve_invariant_saddle_gap(
                projection.game.payoffs[0],
                generators,
                compress_constraints=True,
                exact_invariant_game=True,
            )
            row_regret, column_regret, gap = exploitability(
                true_matrix, solution.row_strategy, solution.column_strategy
            )
            max_regret = max(row_regret, column_regret)
            regret_certificate = projection.distance + 2.0 * epsilon
            gap_certificate = 2.0 * projection.distance + 4.0 * epsilon
            rows.append(
                {
                    "samples_per_entry": samples,
                    "replicate": replicate,
                    "epsilon_hoeffding": epsilon,
                    "estimated_defect": projection.distance,
                    "true_max_regret": max_regret,
                    "true_saddle_gap": gap,
                    "max_regret_certificate": regret_certificate,
                    "gap_certificate": gap_certificate,
                    "covered": max_regret <= regret_certificate + 1e-9,
                }
            )
    return pd.DataFrame(rows)
