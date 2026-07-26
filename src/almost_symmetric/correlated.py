"""Correlated and coarse-correlated equilibrium under game symmetries."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable, Literal, Sequence

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

from .game import NormalFormGame
from .symmetry import Relabeling, profile_orbit_labels, validate_generators

EquilibriumKind = Literal["ce", "cce"]


@dataclass(frozen=True)
class CorrelatedSolution:
    """A correlated distribution and its explicit incentive diagnostics."""

    distribution: np.ndarray
    objective_value: float
    ce_violation: float
    cce_violation: float
    success: bool
    message: str
    kind: EquilibriumKind
    epsilon: float
    n_variables: int
    n_inequalities: int
    n_profile_orbits: int


def _validate_distribution(game: NormalFormGame, distribution: np.ndarray) -> np.ndarray:
    mu = np.asarray(distribution, dtype=float)
    if mu.shape != game.action_sizes:
        raise ValueError(
            f"distribution should have shape {game.action_sizes}, got {mu.shape}"
        )
    if not np.all(np.isfinite(mu)):
        raise ValueError("distribution must be finite")
    if np.min(mu, initial=0.0) < -1e-9:
        raise ValueError("distribution must be nonnegative")
    total = float(np.sum(mu))
    if not np.isclose(total, 1.0, atol=1e-8):
        raise ValueError(f"distribution must sum to one, got {total}")
    return np.maximum(mu, 0.0) / total


def correlated_equilibrium_violations(
    game: NormalFormGame,
    distribution: np.ndarray,
) -> tuple[float, float]:
    """Return maximum CE and CCE deviation gains.

    CE uses the standard unconditional linear inequalities: for every player and
    every ordered recommendation/deviation pair, the probability-weighted gain
    from deviating is nonpositive. CCE allows a player to commit to one fixed
    action before observing a recommendation.
    """

    mu = _validate_distribution(game, distribution)
    max_ce = 0.0
    max_cce = 0.0

    for player, own_size in enumerate(game.action_sizes):
        opponent_players = [j for j in range(game.n_players) if j != player]
        opponent_sizes = [game.action_sizes[j] for j in opponent_players]

        for recommended in range(own_size):
            for deviation in range(own_size):
                if deviation == recommended:
                    continue
                gain = 0.0
                for opponents in product(*(range(m) for m in opponent_sizes)):
                    profile = [0] * game.n_players
                    for j, action in zip(opponent_players, opponents):
                        profile[j] = action
                    profile[player] = recommended
                    probability = float(mu[tuple(profile)])
                    if probability == 0.0:
                        continue
                    current = game.payoffs[(player, *profile)]
                    profile[player] = deviation
                    changed = game.payoffs[(player, *profile)]
                    gain += probability * float(changed - current)
                max_ce = max(max_ce, gain)

        for deviation in range(own_size):
            gain = 0.0
            for profile_tuple in game.profiles():
                probability = float(mu[profile_tuple])
                if probability == 0.0:
                    continue
                current = game.payoffs[(player, *profile_tuple)]
                deviating = list(profile_tuple)
                deviating[player] = deviation
                changed = game.payoffs[(player, *deviating)]
                gain += probability * float(changed - current)
            max_cce = max(max_cce, gain)

    return max(0.0, float(max_ce)), max(0.0, float(max_cce))


def is_invariant_distribution(
    distribution: np.ndarray,
    generators: Iterable[Relabeling],
    *,
    atol: float = 1e-8,
) -> bool:
    """Check invariance of a joint distribution under supplied generators."""

    mu = np.asarray(distribution, dtype=float)
    action_sizes = tuple(int(x) for x in mu.shape)
    gens = validate_generators(action_sizes, generators)
    for generator in gens:
        for profile in product(*(range(m) for m in action_sizes)):
            if abs(float(mu[profile]) - float(mu[generator.map_profile(profile)])) > atol:
                return False
    return True


def _profile_index(action_sizes: Sequence[int], profile: Sequence[int]) -> int:
    return int(np.ravel_multi_index(tuple(profile), tuple(action_sizes)))


def solve_correlated_equilibrium(
    game: NormalFormGame,
    generators: Iterable[Relabeling] = (),
    *,
    invariant: bool = False,
    kind: EquilibriumKind = "ce",
    epsilon: float = 0.0,
    objective_values: np.ndarray | None = None,
) -> CorrelatedSolution:
    """Optimize a linear objective over CE or CCE distributions.

    When ``invariant`` is true, one variable represents the probability assigned
    to every pure profile in the same group orbit. The simplex equation weights
    that variable by its orbit cardinality. The default objective maximizes total
    social welfare, but any profile-wise linear objective may be supplied.
    """

    if kind not in ("ce", "cce"):
        raise ValueError("kind must be 'ce' or 'cce'")
    if epsilon < 0.0:
        raise ValueError("epsilon must be nonnegative")

    gens = validate_generators(game.action_sizes, generators)
    n_profiles = game.n_profiles
    if invariant:
        labels = profile_orbit_labels(game.action_sizes, gens)
    else:
        labels = np.arange(n_profiles, dtype=int)
    n_variables = int(labels.max(initial=-1) + 1)
    orbit_sizes = np.bincount(labels, minlength=n_variables).astype(float)

    if objective_values is None:
        objective_array = np.sum(game.payoffs, axis=0)
    else:
        objective_array = np.asarray(objective_values, dtype=float)
        if objective_array.shape != game.action_sizes:
            raise ValueError(
                "objective_values must have one value for every pure profile"
            )
        if not np.all(np.isfinite(objective_array)):
            raise ValueError("objective_values must be finite")

    objective = -np.bincount(
        labels,
        weights=objective_array.reshape(-1),
        minlength=n_variables,
    )

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    rhs: list[float] = []
    row = 0

    if kind == "ce":
        for player, own_size in enumerate(game.action_sizes):
            opponent_players = [j for j in range(game.n_players) if j != player]
            opponent_sizes = [game.action_sizes[j] for j in opponent_players]
            for recommended in range(own_size):
                for deviation in range(own_size):
                    if deviation == recommended:
                        continue
                    coefficients: dict[int, float] = {}
                    for opponents in product(*(range(m) for m in opponent_sizes)):
                        profile = [0] * game.n_players
                        for j, action in zip(opponent_players, opponents):
                            profile[j] = action
                        profile[player] = recommended
                        current = game.payoffs[(player, *profile)]
                        flat = _profile_index(game.action_sizes, profile)
                        variable = int(labels[flat])
                        profile[player] = deviation
                        changed = game.payoffs[(player, *profile)]
                        coefficients[variable] = coefficients.get(variable, 0.0) + float(
                            changed - current
                        )
                    for variable, coefficient in coefficients.items():
                        if coefficient != 0.0:
                            rows.append(row)
                            cols.append(variable)
                            data.append(coefficient)
                    rhs.append(float(epsilon))
                    row += 1
    else:
        for player, own_size in enumerate(game.action_sizes):
            for deviation in range(own_size):
                coefficients: dict[int, float] = {}
                for profile_tuple in game.profiles():
                    current = game.payoffs[(player, *profile_tuple)]
                    deviating = list(profile_tuple)
                    deviating[player] = deviation
                    changed = game.payoffs[(player, *deviating)]
                    flat = _profile_index(game.action_sizes, profile_tuple)
                    variable = int(labels[flat])
                    coefficients[variable] = coefficients.get(variable, 0.0) + float(
                        changed - current
                    )
                for variable, coefficient in coefficients.items():
                    if coefficient != 0.0:
                        rows.append(row)
                        cols.append(variable)
                        data.append(coefficient)
                rhs.append(float(epsilon))
                row += 1

    A_ub = coo_matrix(
        (data, (rows, cols)), shape=(row, n_variables), dtype=float
    ).tocsr()
    A_eq = orbit_sizes.reshape(1, -1)

    result = linprog(
        objective,
        A_ub=A_ub,
        b_ub=np.asarray(rhs, dtype=float),
        A_eq=A_eq,
        b_eq=np.ones(1),
        bounds=[(0.0, None)] * n_variables,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"correlated-equilibrium LP failed: {result.message}")

    flat_distribution = np.asarray(result.x, dtype=float)[labels]
    distribution = flat_distribution.reshape(game.action_sizes)
    distribution = np.maximum(distribution, 0.0)
    distribution /= np.sum(distribution)
    ce_violation, cce_violation = correlated_equilibrium_violations(
        game, distribution
    )

    return CorrelatedSolution(
        distribution=distribution,
        objective_value=float(np.sum(distribution * objective_array)),
        ce_violation=ce_violation,
        cce_violation=cce_violation,
        success=True,
        message=str(result.message),
        kind=kind,
        epsilon=float(epsilon),
        n_variables=n_variables,
        n_inequalities=A_ub.shape[0],
        n_profile_orbits=n_variables,
    )
