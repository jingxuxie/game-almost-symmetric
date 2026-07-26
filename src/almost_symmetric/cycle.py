"""Cycle characterization and combinatorial projection for strategic symmetry."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import inf, isfinite
from typing import Iterable, Sequence

import numpy as np

from .game import NormalFormGame, strategic_distance
from .symmetry import Relabeling, payoff_coordinate_orbit_labels, validate_generators


@dataclass(frozen=True)
class IncentiveEdge:
    """One deviation comparison after payoff coordinates are symmetry-identified."""

    tail: int
    head: int
    label: float
    player: int
    opponents_profile: tuple[int, ...]
    action_from: int
    action_to: int


@dataclass(frozen=True)
class CycleProjectionResult:
    game: NormalFormGame
    distance: float
    cycle_value: float
    witness: tuple[IncentiveEdge, ...]
    n_vertices: int
    n_edges: int


def _coordinate_index(game: NormalFormGame, player: int, profile: Sequence[int]) -> int:
    return player * game.n_profiles + int(
        np.ravel_multi_index(tuple(profile), game.action_sizes)
    )


def build_incentive_graph(
    game: NormalFormGame,
    generators: Iterable[Relabeling],
) -> tuple[int, tuple[IncentiveEdge, ...], np.ndarray]:
    """Construct the symmetry-quotiented deviation graph.

    For a unilateral comparison from action ``b`` to action ``a``, the edge runs
    from the payoff-coordinate orbit of ``b`` to that of ``a`` and is labeled by
    ``u_i(a,a_-i)-u_i(b,a_-i)``. Parallel edges retain only the smallest label,
    because it is the strongest associated difference constraint; reverse
    comparisons are included separately.
    """
    gens = validate_generators(game.action_sizes, generators)
    labels = payoff_coordinate_orbit_labels(game.action_sizes, gens)
    n_vertices = int(labels.max(initial=-1) + 1)
    strongest: dict[tuple[int, int], IncentiveEdge] = {}

    for i, m_i in enumerate(game.action_sizes):
        opponent_players = [j for j in range(game.n_players) if j != i]
        opponent_sizes = [game.action_sizes[j] for j in opponent_players]
        for opponents in product(*(range(m) for m in opponent_sizes)):
            base = [0] * game.n_players
            for j, action in zip(opponent_players, opponents):
                base[j] = action
            utilities = np.empty(m_i, dtype=float)
            orbits = np.empty(m_i, dtype=int)
            for action in range(m_i):
                base[i] = action
                utilities[action] = game.payoffs[(i, *base)]
                orbits[action] = labels[_coordinate_index(game, i, base)]
            for action_from in range(m_i):
                for action_to in range(m_i):
                    if action_from == action_to:
                        continue
                    tail = int(orbits[action_from])
                    head = int(orbits[action_to])
                    label = float(utilities[action_to] - utilities[action_from])
                    edge = IncentiveEdge(
                        tail=tail,
                        head=head,
                        label=label,
                        player=i,
                        opponents_profile=tuple(int(x) for x in opponents),
                        action_from=action_from,
                        action_to=action_to,
                    )
                    key = (tail, head)
                    if key not in strongest or label < strongest[key].label:
                        strongest[key] = edge
    return n_vertices, tuple(strongest.values()), labels


def _maximum_cycle_mean_with_witness(
    n_vertices: int,
    edges: Sequence[IncentiveEdge],
) -> tuple[float, tuple[IncentiveEdge, ...]]:
    """Karp's maximum-cycle-mean dynamic program with a closed-walk witness.

    Edge weights are the negatives of incentive labels. Thus the returned value
    is the largest negative mean label around a directed cycle.
    """
    if n_vertices == 0 or not edges:
        return 0.0, ()
    incoming: list[list[tuple[int, float, int]]] = [
        [] for _ in range(n_vertices)
    ]
    for edge_id, edge in enumerate(edges):
        incoming[edge.head].append((edge.tail, -edge.label, edge_id))

    negative_infinity = -1e300
    dp = np.full((n_vertices + 1, n_vertices), negative_infinity, dtype=float)
    predecessor_vertex = np.full(
        (n_vertices + 1, n_vertices), -1, dtype=int
    )
    predecessor_edge = np.full((n_vertices + 1, n_vertices), -1, dtype=int)
    dp[0, :] = 0.0  # Equivalent to a zero-weight super-source to every vertex.

    for length in range(1, n_vertices + 1):
        for vertex in range(n_vertices):
            best = negative_infinity
            best_pred = -1
            best_edge = -1
            for tail, weight, edge_id in incoming[vertex]:
                candidate = dp[length - 1, tail] + weight
                if candidate > best:
                    best = candidate
                    best_pred = tail
                    best_edge = edge_id
            dp[length, vertex] = best
            predecessor_vertex[length, vertex] = best_pred
            predecessor_edge[length, vertex] = best_edge

    optimum = -inf
    optimum_vertex = -1
    for vertex in range(n_vertices):
        if dp[n_vertices, vertex] <= negative_infinity / 2:
            continue
        ratios = [
            (dp[n_vertices, vertex] - dp[length, vertex])
            / (n_vertices - length)
            for length in range(n_vertices)
            if dp[length, vertex] > negative_infinity / 2
        ]
        if ratios:
            candidate = min(ratios)
            if candidate > optimum:
                optimum = candidate
                optimum_vertex = vertex

    if not isfinite(optimum) or optimum_vertex < 0:
        return 0.0, ()

    # Reconstruct an optimal length-n walk and select its highest-mean closed
    # segment. Standard Karp backtracking yields a maximum-mean closed walk.
    vertices_reversed = [optimum_vertex]
    edges_reversed: list[int] = []
    vertex = optimum_vertex
    for length in range(n_vertices, 0, -1):
        edge_id = int(predecessor_edge[length, vertex])
        tail = int(predecessor_vertex[length, vertex])
        if edge_id < 0 or tail < 0:
            return max(0.0, float(optimum)), ()
        edges_reversed.append(edge_id)
        vertices_reversed.append(tail)
        vertex = tail
    path_vertices = list(reversed(vertices_reversed))
    path_edges = list(reversed(edges_reversed))

    positions: dict[int, list[int]] = {}
    best_mean = -inf
    best_segment: tuple[int, int] | None = None
    prefix = np.zeros(len(path_edges) + 1, dtype=float)
    for index, edge_id in enumerate(path_edges):
        prefix[index + 1] = prefix[index] - edges[edge_id].label
    for end, node in enumerate(path_vertices):
        for start in positions.get(node, []):
            mean = float((prefix[end] - prefix[start]) / (end - start))
            if mean > best_mean:
                best_mean = mean
                best_segment = (start, end)
        positions.setdefault(node, []).append(end)

    witness: tuple[IncentiveEdge, ...] = ()
    if best_segment is not None:
        start, end = best_segment
        witness = tuple(edges[path_edges[index]] for index in range(start, end))
    return max(0.0, float(optimum)), witness


def _difference_constraint_potentials(
    n_vertices: int,
    edges: Sequence[IncentiveEdge],
    defect: float,
) -> np.ndarray:
    """Recover orbit payoffs from feasible difference constraints."""
    potentials = np.zeros(n_vertices, dtype=float)
    tolerance = 1e-10 * (1.0 + abs(defect))
    relaxed_defect = defect + tolerance
    for _ in range(max(0, n_vertices - 1)):
        changed = False
        for edge in edges:
            candidate = potentials[edge.tail] + edge.label + relaxed_defect
            if candidate < potentials[edge.head] - tolerance:
                potentials[edge.head] = candidate
                changed = True
        if not changed:
            break
    # A final pass detects implementation or numerical failures.
    max_violation = max(
        (
            potentials[edge.head]
            - potentials[edge.tail]
            - edge.label
            - relaxed_defect
            for edge in edges
        ),
        default=0.0,
    )
    if max_violation > 1e-7 * (1.0 + abs(defect)):
        raise RuntimeError(
            "difference constraints remained infeasible after cycle computation; "
            f"maximum violation={max_violation}"
        )
    return potentials


def project_strategic_cycle(
    game: NormalFormGame,
    generators: Iterable[Relabeling],
) -> CycleProjectionResult:
    """Compute the unstructured strategic symmetry projection combinatorially.

    The optimal defect equals the maximum mean cycle inconsistency. At that
    defect, shortest-path difference constraints recover a nearest exactly
    symmetric surrogate.
    """
    n_vertices, edges, labels = build_incentive_graph(game, generators)
    cycle_value, witness = _maximum_cycle_mean_with_witness(n_vertices, edges)
    potentials = _difference_constraint_potentials(n_vertices, edges, cycle_value)
    projected = NormalFormGame(potentials[labels].reshape(game.payoffs.shape))
    distance = strategic_distance(game, projected)
    if distance > cycle_value + 1e-7 * (1.0 + abs(cycle_value)):
        raise RuntimeError(
            "cycle projection failed to attain the computed defect: "
            f"distance={distance}, cycle_value={cycle_value}"
        )
    return CycleProjectionResult(
        game=projected,
        distance=distance,
        cycle_value=cycle_value,
        witness=witness,
        n_vertices=n_vertices,
        n_edges=len(edges),
    )
