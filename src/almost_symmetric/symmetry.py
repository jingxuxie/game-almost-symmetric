"""Player/action relabelings and orbit computations."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable, Sequence

import numpy as np

from .game import NormalFormGame, Profile


@dataclass(frozen=True)
class Relabeling:
    """A bijection of players and their action sets.

    ``player_perm[i]`` is the destination of source player ``i`` and
    ``action_perms[i][a]`` is the destination action of source action ``a``.
    """

    player_perm: tuple[int, ...]
    action_perms: tuple[tuple[int, ...], ...]

    def validate(self, action_sizes: Sequence[int]) -> None:
        n = len(action_sizes)
        if len(self.player_perm) != n or sorted(self.player_perm) != list(range(n)):
            raise ValueError("player_perm must be a permutation of all players")
        if len(self.action_perms) != n:
            raise ValueError("one action permutation is required for each source player")
        for i, mapping in enumerate(self.action_perms):
            target = self.player_perm[i]
            if len(mapping) != action_sizes[i]:
                raise ValueError(f"source player {i} has an incorrectly sized action map")
            if sorted(mapping) != list(range(action_sizes[target])):
                raise ValueError(
                    f"action map for player {i} must biject onto player {target}'s actions"
                )

    @classmethod
    def identity(cls, action_sizes: Sequence[int]) -> "Relabeling":
        return cls(
            tuple(range(len(action_sizes))),
            tuple(tuple(range(m)) for m in action_sizes),
        )

    def map_profile(self, profile: Sequence[int]) -> Profile:
        out = [0] * len(self.player_perm)
        for i, action in enumerate(profile):
            out[self.player_perm[i]] = self.action_perms[i][action]
        return tuple(out)

    def map_action(self, player: int, action: int) -> tuple[int, int]:
        return self.player_perm[player], self.action_perms[player][action]

    def compose(self, other: "Relabeling") -> "Relabeling":
        """Return ``self`` after ``other`` (self o other)."""
        if len(self.player_perm) != len(other.player_perm):
            raise ValueError("incompatible relabelings")
        player_perm: list[int] = []
        action_perms: list[tuple[int, ...]] = []
        for i in range(len(self.player_perm)):
            middle = other.player_perm[i]
            player_perm.append(self.player_perm[middle])
            action_perms.append(
                tuple(
                    self.action_perms[middle][other.action_perms[i][a]]
                    for a in range(len(other.action_perms[i]))
                )
            )
        return Relabeling(tuple(player_perm), tuple(action_perms))


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1

    def labels(self) -> np.ndarray:
        roots = [self.find(i) for i in range(len(self.parent))]
        mapping: dict[int, int] = {}
        labels = np.empty(len(roots), dtype=int)
        for i, root in enumerate(roots):
            mapping.setdefault(root, len(mapping))
            labels[i] = mapping[root]
        return labels


def validate_generators(
    action_sizes: Sequence[int], generators: Iterable[Relabeling]
) -> tuple[Relabeling, ...]:
    gens = tuple(generators)
    for generator in gens:
        generator.validate(action_sizes)
    return gens


def action_offsets(action_sizes: Sequence[int]) -> np.ndarray:
    offsets = np.zeros(len(action_sizes) + 1, dtype=int)
    offsets[1:] = np.cumsum(action_sizes)
    return offsets


def action_orbit_labels(
    action_sizes: Sequence[int], generators: Iterable[Relabeling]
) -> np.ndarray:
    gens = validate_generators(action_sizes, generators)
    offsets = action_offsets(action_sizes)
    uf = _UnionFind(int(offsets[-1]))
    for generator in gens:
        for i, m_i in enumerate(action_sizes):
            for action in range(m_i):
                j, mapped_action = generator.map_action(i, action)
                uf.union(
                    int(offsets[i] + action),
                    int(offsets[j] + mapped_action),
                )
    return uf.labels()


def profile_orbit_labels(
    action_sizes: Sequence[int], generators: Iterable[Relabeling]
) -> np.ndarray:
    """Orbit labels for pure joint-action profiles."""

    sizes = tuple(int(m) for m in action_sizes)
    gens = validate_generators(sizes, generators)
    n_profiles = int(np.prod(sizes, dtype=int))
    uf = _UnionFind(n_profiles)
    for profile in product(*(range(m) for m in sizes)):
        flat = int(np.ravel_multi_index(profile, sizes))
        for generator in gens:
            mapped = generator.map_profile(profile)
            mapped_flat = int(np.ravel_multi_index(mapped, sizes))
            uf.union(flat, mapped_flat)
    return uf.labels()


def payoff_coordinate_orbit_labels(
    action_sizes: Sequence[int], generators: Iterable[Relabeling]
) -> np.ndarray:
    """Orbit labels for payoff coordinates ``(player, pure profile)``."""
    gens = validate_generators(action_sizes, generators)
    n = len(action_sizes)
    n_profiles = int(np.prod(action_sizes, dtype=int))
    uf = _UnionFind(n * n_profiles)

    def flat(player: int, profile: Sequence[int]) -> int:
        return player * n_profiles + int(np.ravel_multi_index(tuple(profile), action_sizes))

    for generator in gens:
        for profile in product(*(range(m) for m in action_sizes)):
            mapped_profile = generator.map_profile(profile)
            for i in range(n):
                uf.union(
                    flat(i, profile),
                    flat(generator.player_perm[i], mapped_profile),
                )
    return uf.labels()


def apply_relabeling(game: NormalFormGame, relabeling: Relabeling) -> NormalFormGame:
    relabeling.validate(game.action_sizes)
    out = np.empty_like(game.payoffs)
    for profile in game.profiles():
        mapped_profile = relabeling.map_profile(profile)
        for i in range(game.n_players):
            out[(relabeling.player_perm[i], *mapped_profile)] = game.payoffs[(i, *profile)]
    return NormalFormGame(out)


def is_exact_symmetry(
    game: NormalFormGame, relabeling: Relabeling, atol: float = 1e-8
) -> bool:
    return bool(
        np.max(
            np.abs(game.payoffs - apply_relabeling(game, relabeling).payoffs),
            initial=0.0,
        )
        <= atol
    )


def is_invariant_game(
    game: NormalFormGame,
    generators: Iterable[Relabeling],
    atol: float = 1e-8,
) -> bool:
    return all(is_exact_symmetry(game, generator, atol=atol) for generator in generators)


def reynolds_symmetrize(
    game: NormalFormGame, generators: Iterable[Relabeling]
) -> NormalFormGame:
    """Average payoff coordinates over generated group orbits."""
    labels = payoff_coordinate_orbit_labels(game.action_sizes, generators)
    flat = game.payoffs.reshape(-1)
    sums = np.bincount(labels, weights=flat)
    counts = np.bincount(labels)
    averaged = sums[labels] / counts[labels]
    return NormalFormGame(averaged.reshape(game.payoffs.shape))


def group_closure(
    action_sizes: Sequence[int],
    generators: Iterable[Relabeling],
    max_size: int = 100_000,
) -> tuple[Relabeling, ...]:
    """Enumerate a small generated group; intended for diagnostics and tests."""
    gens = validate_generators(action_sizes, generators)
    identity = Relabeling.identity(action_sizes)
    seen = {identity}
    queue = [identity]
    while queue:
        current = queue.pop()
        for generator in gens:
            candidate = generator.compose(current)
            if candidate not in seen:
                seen.add(candidate)
                queue.append(candidate)
                if len(seen) > max_size:
                    raise ValueError(f"generated group exceeds max_size={max_size}")
    return tuple(seen)


def cyclic_action_generator(
    action_sizes: Sequence[int],
    player: int,
    actions: Sequence[int],
) -> Relabeling:
    """Cycle selected actions of one player while fixing everything else."""
    actions = tuple(int(a) for a in actions)
    if len(actions) < 2:
        raise ValueError("a nontrivial cycle needs at least two actions")
    if len(set(actions)) != len(actions):
        raise ValueError("cycled actions must be distinct")
    mapping = [list(range(m)) for m in action_sizes]
    for source, destination in zip(actions, actions[1:] + actions[:1]):
        mapping[player][source] = destination
    relabeling = Relabeling(
        tuple(range(len(action_sizes))),
        tuple(tuple(x) for x in mapping),
    )
    relabeling.validate(action_sizes)
    return relabeling
