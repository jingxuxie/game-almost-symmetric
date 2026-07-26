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


def _coordinate_index(
    game: NormalFormGame, player: int, profile: Sequence[int]
) -> int:
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
    comparisons are included separately. Self-loops are retained because an
    orbit identification can make one comparison an immediate obstruction.
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


def _maximum_cycle_mean_value(
    n_vertices: int,
    edges: Sequence[IncentiveEdge],
) -> float:
    """Return the maximum cycle mean of weights ``-edge.label``.

    This is Karp's dynamic program with a zero-weight super-source to every
    vertex. The graph produced by :func:`build_incentive_graph` contains every
    comparison and its reverse before parallel-edge compression, so its maximum
    cycle mean is nonnegative up to numerical error.
    """
    if n_vertices == 0 or not edges:
        return 0.0

    incoming: list[list[tuple[int, float]]] = [
        [] for _ in range(n_vertices)
    ]
    for edge in edges:
        incoming[edge.head].append((edge.tail, -edge.label))

    negative_infinity = -1e300
    dp = np.full((n_vertices + 1, n_vertices), negative_infinity, dtype=float)
    dp[0, :] = 0.0

    for length in range(1, n_vertices + 1):
        for vertex in range(n_vertices):
            best = negative_infinity
            for tail, weight in incoming[vertex]:
                candidate = dp[length - 1, tail] + weight
                if candidate > best:
                    best = candidate
            dp[length, vertex] = best

    optimum = -inf
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
            optimum = max(optimum, min(ratios))

    if not isfinite(optimum):
        return 0.0
    return max(0.0, float(optimum))


def _longest_path_potentials(
    n_vertices: int,
    edges: Sequence[IncentiveEdge],
    cycle_mean: float,
) -> np.ndarray:
    """Compute feasible max-plus potentials for the reduced edge weights.

    For reduced weights ``w_e=-c_e-cycle_mean``, every directed cycle has
    nonpositive total weight. With a zero-weight super-source to every vertex,
    the maximum walk value is therefore attained by a simple path, so at most
    ``n_vertices-1`` relaxation passes are required.
    """
    potentials = np.zeros(n_vertices, dtype=float)
    scale = 1.0 + abs(cycle_mean) + max(
        (abs(edge.label) for edge in edges), default=0.0
    )
    tolerance = 1e-13 * scale

    for _ in range(max(0, n_vertices - 1)):
        changed = False
        for edge in edges:
            reduced_weight = -edge.label - cycle_mean
            candidate = potentials[edge.tail] + reduced_weight
            if candidate > potentials[edge.head] + tolerance:
                potentials[edge.head] = candidate
                changed = True
        if not changed:
            break
    return potentials


def _find_directed_cycle(
    n_vertices: int,
    edges: Sequence[IncentiveEdge],
    adjacency: Sequence[Sequence[int]],
) -> tuple[int, ...]:
    """Return one directed cycle from an edge-index adjacency list."""
    state = np.zeros(n_vertices, dtype=np.int8)
    parent_vertex = np.full(n_vertices, -1, dtype=int)
    parent_edge = np.full(n_vertices, -1, dtype=int)

    for start in range(n_vertices):
        if state[start] != 0:
            continue
        state[start] = 1
        stack: list[tuple[int, int]] = [(start, 0)]

        while stack:
            vertex, next_index = stack[-1]
            if next_index >= len(adjacency[vertex]):
                state[vertex] = 2
                stack.pop()
                continue

            edge_id = int(adjacency[vertex][next_index])
            stack[-1] = (vertex, next_index + 1)
            edge = edges[edge_id]
            head = edge.head

            if state[head] == 0:
                state[head] = 1
                parent_vertex[head] = vertex
                parent_edge[head] = edge_id
                stack.append((head, 0))
            elif state[head] == 1:
                # The tree path head -> ... -> vertex followed by vertex -> head
                # is a directed cycle. This also handles a tight self-loop.
                tree_edges_reversed: list[int] = []
                cursor = vertex
                while cursor != head:
                    incoming_edge = int(parent_edge[cursor])
                    if incoming_edge < 0:
                        raise RuntimeError("failed to reconstruct a directed cycle")
                    tree_edges_reversed.append(incoming_edge)
                    cursor = int(parent_vertex[cursor])
                return tuple(reversed(tree_edges_reversed)) + (edge_id,)
    return ()


def _critical_cycle_from_tight_edges(
    n_vertices: int,
    edges: Sequence[IncentiveEdge],
    cycle_mean: float,
) -> tuple[IncentiveEdge, ...]:
    """Recover a certified critical cycle from the reduced-weight tight graph.

    If ``lambda`` is the maximum cycle mean of weights ``w_e=-c_e``, the reduced
    graph ``w_e-lambda`` has no positive cycle and has at least one zero-weight
    cycle. Longest-path potentials satisfy

        h(head) >= h(tail) + w_e - lambda.

    Every edge of a zero-weight cycle must be tight, because the slacks are
    nonnegative and telescope to zero around the cycle. A DFS in the tight-edge
    subgraph therefore recovers a critical cycle. Tolerances are increased only
    to absorb floating-point error; every returned cycle is checked against the
    Karp value.
    """
    if n_vertices == 0 or not edges:
        return ()

    potentials = _longest_path_potentials(n_vertices, edges, cycle_mean)
    scale = 1.0 + abs(cycle_mean) + max(
        (abs(edge.label) for edge in edges), default=0.0
    )

    for relative_tolerance in (
        1e-12,
        1e-11,
        1e-10,
        1e-9,
        1e-8,
        1e-7,
        1e-6,
    ):
        tolerance = relative_tolerance * scale
        adjacency: list[list[int]] = [[] for _ in range(n_vertices)]
        for edge_id, edge in enumerate(edges):
            reduced_weight = -edge.label - cycle_mean
            slack = (
                potentials[edge.head]
                - potentials[edge.tail]
                - reduced_weight
            )
            if abs(slack) <= tolerance:
                adjacency[edge.tail].append(edge_id)

        cycle_ids = _find_directed_cycle(n_vertices, edges, adjacency)
        if not cycle_ids:
            continue

        witness = tuple(edges[edge_id] for edge_id in cycle_ids)
        witness_value = float(np.mean([-edge.label for edge in witness]))
        if abs(witness_value - cycle_mean) <= 100.0 * tolerance:
            return witness

    raise RuntimeError(
        "maximum-cycle-mean value was computed, but no numerically certified "
        "critical cycle could be extracted"
    )


def _maximum_cycle_mean_with_witness(
    n_vertices: int,
    edges: Sequence[IncentiveEdge],
) -> tuple[float, tuple[IncentiveEdge, ...]]:
    cycle_mean = _maximum_cycle_mean_value(n_vertices, edges)
    witness = _critical_cycle_from_tight_edges(n_vertices, edges, cycle_mean)
    return cycle_mean, witness


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
    defect, difference constraints recover a nearest exactly symmetric
    surrogate, while a critical tight-edge cycle certifies optimality.
    """
    n_vertices, edges, labels = build_incentive_graph(game, generators)
    cycle_value, witness = _maximum_cycle_mean_with_witness(n_vertices, edges)
    potentials = _difference_constraint_potentials(n_vertices, edges, cycle_value)
    projected = NormalFormGame(potentials[labels].reshape(game.payoffs.shape))
    distance = strategic_distance(game, projected)

    tolerance = 1e-7 * (1.0 + abs(cycle_value))
    if distance > cycle_value + tolerance:
        raise RuntimeError(
            "cycle projection failed to attain the computed defect: "
            f"distance={distance}, cycle_value={cycle_value}"
        )
    if edges:
        if not witness:
            raise RuntimeError("a nonempty incentive graph must have a cycle witness")
        for edge, next_edge in zip(witness, witness[1:] + witness[:1]):
            if edge.head != next_edge.tail:
                raise RuntimeError("critical-cycle witness is not a closed walk")
        witness_value = float(np.mean([-edge.label for edge in witness]))
        if abs(witness_value - cycle_value) > tolerance:
            raise RuntimeError(
                "critical-cycle witness does not certify the computed defect: "
                f"witness_value={witness_value}, cycle_value={cycle_value}"
            )

    return CycleProjectionResult(
        game=projected,
        distance=distance,
        cycle_value=cycle_value,
        witness=witness,
        n_vertices=n_vertices,
        n_edges=len(edges),
    )
