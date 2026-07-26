"""Finite normal-form games and strategically meaningful distances."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterator, Sequence

import numpy as np

Profile = tuple[int, ...]


@dataclass(frozen=True)
class NormalFormGame:
    """An explicit finite normal-form game.

    ``payoffs`` has shape ``(n_players, m_1, ..., m_n)``. Arrays are copied and
    made read-only so optimization routines cannot mutate a game accidentally.
    """

    payoffs: np.ndarray

    def __post_init__(self) -> None:
        arr = np.asarray(self.payoffs, dtype=float)
        if arr.ndim < 3:
            raise ValueError("payoffs must have shape (players, action_1, ..., action_n)")
        n_players = int(arr.shape[0])
        if n_players < 2:
            raise ValueError("a game must have at least two players")
        if arr.ndim != n_players + 1:
            raise ValueError(
                "the number of payoff tensor axes must equal n_players + 1; "
                f"got shape {arr.shape}"
            )
        if any(int(m) <= 0 for m in arr.shape[1:]):
            raise ValueError("every player must have at least one action")
        arr = np.array(arr, copy=True, dtype=float)
        if not np.all(np.isfinite(arr)):
            raise ValueError("payoffs must be finite")
        arr.setflags(write=False)
        object.__setattr__(self, "payoffs", arr)

    @property
    def n_players(self) -> int:
        return int(self.payoffs.shape[0])

    @property
    def action_sizes(self) -> tuple[int, ...]:
        return tuple(int(x) for x in self.payoffs.shape[1:])

    @property
    def n_profiles(self) -> int:
        return int(np.prod(self.action_sizes, dtype=int))

    def profiles(self) -> Iterator[Profile]:
        return product(*(range(m) for m in self.action_sizes))

    def utility(self, player: int, profile: Sequence[int]) -> float:
        return float(self.payoffs[(player, *profile)])

    def expected_utility(self, player: int, strategies: Sequence[np.ndarray]) -> float:
        """Expected utility under an independent mixed-strategy profile."""
        if len(strategies) != self.n_players:
            raise ValueError("one mixed strategy is required for each player")
        value = self.payoffs[player]
        for axis in reversed(range(self.n_players)):
            probs = np.asarray(strategies[axis], dtype=float)
            if probs.shape != (self.action_sizes[axis],):
                raise ValueError(f"strategy {axis} has incompatible shape {probs.shape}")
            if np.min(probs, initial=0.0) < -1e-10 or not np.isclose(np.sum(probs), 1.0):
                raise ValueError(f"strategy {axis} is not a probability vector")
            value = np.tensordot(value, probs, axes=([axis], [0]))
        return float(value)

    @classmethod
    def zero_sum(cls, matrix: np.ndarray) -> "NormalFormGame":
        matrix = np.asarray(matrix, dtype=float)
        if matrix.ndim != 2:
            raise ValueError("a zero-sum matrix game requires a 2-D payoff matrix")
        return cls(np.stack([matrix, -matrix], axis=0))

    def is_zero_sum(self, atol: float = 1e-9) -> bool:
        return self.n_players == 2 and bool(
            np.max(np.abs(self.payoffs[0] + self.payoffs[1]), initial=0.0) <= atol
        )

    def is_team(self, atol: float = 1e-9) -> bool:
        return bool(np.max(np.ptp(self.payoffs, axis=0), initial=0.0) <= atol)


def residual_ranges(game_a: NormalFormGame, game_b: NormalFormGame) -> list[np.ndarray]:
    """Ranges of payoff residuals over each player's own actions."""
    if game_a.payoffs.shape != game_b.payoffs.shape:
        raise ValueError("games must have identical player and action sets")
    residual = game_a.payoffs - game_b.payoffs
    ranges: list[np.ndarray] = []
    for i, m_i in enumerate(game_a.action_sizes):
        own_first = np.moveaxis(residual[i], i, 0).reshape(m_i, -1)
        ranges.append(np.ptp(own_first, axis=0))
    return ranges


def strategic_distance(game_a: NormalFormGame, game_b: NormalFormGame) -> float:
    """Maximum pairwise difference (MPD) between two games.

    The value is the largest change in any unilateral-deviation incentive. It is
    a seminorm on payoff tensors and a norm modulo nonstrategic payoff terms.
    """
    ranges = residual_ranges(game_a, game_b)
    return float(max((np.max(x, initial=0.0) for x in ranges), default=0.0))


def payoff_linf_distance(game_a: NormalFormGame, game_b: NormalFormGame) -> float:
    if game_a.payoffs.shape != game_b.payoffs.shape:
        raise ValueError("games must have identical shapes")
    return float(np.max(np.abs(game_a.payoffs - game_b.payoffs), initial=0.0))


def add_nonstrategic_component(
    game: NormalFormGame,
    components: Sequence[np.ndarray],
) -> NormalFormGame:
    """Add a payoff term independent of each player's own action."""
    if len(components) != game.n_players:
        raise ValueError("one component is required for each player")
    out = np.array(game.payoffs, copy=True)
    for i, component in enumerate(components):
        expected_shape = tuple(m for j, m in enumerate(game.action_sizes) if j != i)
        comp = np.asarray(component, dtype=float)
        if comp.shape != expected_shape:
            raise ValueError(
                f"component {i} should have shape {expected_shape}, got {comp.shape}"
            )
        out[i] += np.expand_dims(comp, axis=i)
    return NormalFormGame(out)


def pure_regrets(game: NormalFormGame, strategies: Sequence[np.ndarray]) -> np.ndarray:
    """Per-player unilateral regret of an independent mixed profile."""
    if len(strategies) != game.n_players:
        raise ValueError("one mixed strategy is required for each player")
    regrets = np.zeros(game.n_players, dtype=float)
    for i in range(game.n_players):
        current = game.expected_utility(i, strategies)
        values = np.empty(game.action_sizes[i], dtype=float)
        for action in range(game.action_sizes[i]):
            deviating = [np.asarray(s, dtype=float) for s in strategies]
            one_hot = np.zeros(game.action_sizes[i], dtype=float)
            one_hot[action] = 1.0
            deviating[i] = one_hot
            values[action] = game.expected_utility(i, deviating)
        regrets[i] = max(0.0, float(np.max(values) - current))
    return regrets
