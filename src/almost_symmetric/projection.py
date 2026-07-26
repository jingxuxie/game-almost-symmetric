"""Strategic and payoff-level projections onto exact game symmetries."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable, Literal, Sequence

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

from .game import NormalFormGame, payoff_linf_distance, strategic_distance
from .symmetry import Relabeling, validate_generators

Structure = Literal["none", "zero_sum", "team"]


@dataclass(frozen=True)
class ProjectionResult:
    game: NormalFormGame
    distance: float
    success: bool
    message: str
    n_variables: int
    n_equalities: int
    n_inequalities: int


def _coordinate_index(game: NormalFormGame, player: int, profile: Sequence[int]) -> int:
    return player * game.n_profiles + int(
        np.ravel_multi_index(tuple(profile), game.action_sizes)
    )


def _slice_indices(game: NormalFormGame) -> tuple[list[list[int]], np.ndarray]:
    """Group payoff coordinates by (player, opponents' pure profile)."""
    slices: list[list[int]] = []
    coordinate_to_slice = np.empty(game.payoffs.size, dtype=int)
    for i, m_i in enumerate(game.action_sizes):
        opponent_players = [j for j in range(game.n_players) if j != i]
        opponent_sizes = [game.action_sizes[j] for j in opponent_players]
        for opponents in product(*(range(m) for m in opponent_sizes)):
            base = [0] * game.n_players
            for j, action in zip(opponent_players, opponents):
                base[j] = action
            indices: list[int] = []
            slice_id = len(slices)
            for action_i in range(m_i):
                base[i] = action_i
                idx = _coordinate_index(game, i, base)
                indices.append(idx)
                coordinate_to_slice[idx] = slice_id
            slices.append(indices)
    return slices, coordinate_to_slice


def _symmetry_equalities(
    game: NormalFormGame,
    generators: tuple[Relabeling, ...],
) -> tuple[list[int], list[int], list[float], list[float]]:
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    rhs: list[float] = []
    seen_pairs: set[tuple[int, int]] = set()
    row = 0
    for generator in generators:
        for profile in game.profiles():
            mapped_profile = generator.map_profile(profile)
            for i in range(game.n_players):
                left = _coordinate_index(game, i, profile)
                right = _coordinate_index(
                    game, generator.player_perm[i], mapped_profile
                )
                if left == right:
                    continue
                pair = (min(left, right), max(left, right))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                rows.extend([row, row])
                cols.extend([left, right])
                data.extend([1.0, -1.0])
                rhs.append(0.0)
                row += 1
    return rows, cols, data, rhs


def _append_structure_equalities(
    game: NormalFormGame,
    structure: Structure,
    start_row: int,
    rows: list[int],
    cols: list[int],
    data: list[float],
    rhs: list[float],
) -> int:
    row = start_row
    if structure == "none":
        return row
    if structure == "zero_sum":
        if game.n_players != 2:
            raise ValueError("zero_sum structure requires exactly two players")
        for profile in game.profiles():
            rows.extend([row, row])
            cols.extend(
                [
                    _coordinate_index(game, 0, profile),
                    _coordinate_index(game, 1, profile),
                ]
            )
            data.extend([1.0, 1.0])
            rhs.append(0.0)
            row += 1
        return row
    if structure == "team":
        for profile in game.profiles():
            reference = _coordinate_index(game, 0, profile)
            for i in range(1, game.n_players):
                rows.extend([row, row])
                cols.extend([reference, _coordinate_index(game, i, profile)])
                data.extend([1.0, -1.0])
                rhs.append(0.0)
                row += 1
        return row
    raise ValueError(f"unknown structure: {structure}")


def project_strategic(
    game: NormalFormGame,
    generators: Iterable[Relabeling],
    structure: Structure = "none",
) -> ProjectionResult:
    """Find an exactly symmetric game minimizing MPD.

    The LP uses a lower and upper residual variable for each
    (player, opponents' pure profile) slice, avoiding all pairwise-deviation
    constraints while representing the residual range exactly.
    """
    gens = validate_generators(game.action_sizes, generators)
    slices, coordinate_to_slice = _slice_indices(game)
    n_pay = game.payoffs.size
    t_idx = n_pay
    lower_start = t_idx + 1
    upper_start = lower_start + len(slices)
    n_variables = upper_start + len(slices)

    objective = np.zeros(n_variables, dtype=float)
    objective[t_idx] = 1.0
    bounds = [(None, None)] * n_variables
    bounds[t_idx] = (0.0, None)

    # L_s <= u - uhat <= U_s and U_s - L_s <= t.
    ub_rows: list[int] = []
    ub_cols: list[int] = []
    ub_data: list[float] = []
    b_ub: list[float] = []
    row = 0
    for idx, value in enumerate(game.payoffs.reshape(-1)):
        slice_id = int(coordinate_to_slice[idx])
        # uhat + L <= u.
        ub_rows.extend([row, row])
        ub_cols.extend([idx, lower_start + slice_id])
        ub_data.extend([1.0, 1.0])
        b_ub.append(float(value))
        row += 1
        # -uhat - U <= -u.
        ub_rows.extend([row, row])
        ub_cols.extend([idx, upper_start + slice_id])
        ub_data.extend([-1.0, -1.0])
        b_ub.append(float(-value))
        row += 1
    for slice_id in range(len(slices)):
        ub_rows.extend([row, row, row])
        ub_cols.extend([upper_start + slice_id, lower_start + slice_id, t_idx])
        ub_data.extend([1.0, -1.0, -1.0])
        b_ub.append(0.0)
        row += 1
    A_ub = coo_matrix(
        (ub_data, (ub_rows, ub_cols)), shape=(row, n_variables)
    ).tocsr()

    eq_rows, eq_cols, eq_data, b_eq = _symmetry_equalities(game, gens)
    n_eq = _append_structure_equalities(
        game,
        structure,
        len(b_eq),
        eq_rows,
        eq_cols,
        eq_data,
        b_eq,
    )
    A_eq = (
        coo_matrix(
            (eq_data, (eq_rows, eq_cols)), shape=(n_eq, n_variables)
        ).tocsr()
        if n_eq
        else None
    )

    result = linprog(
        objective,
        A_ub=A_ub,
        b_ub=np.asarray(b_ub, dtype=float),
        A_eq=A_eq,
        b_eq=np.asarray(b_eq, dtype=float) if n_eq else None,
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"strategic projection LP failed: {result.message}")
    projected = NormalFormGame(result.x[:n_pay].reshape(game.payoffs.shape))
    return ProjectionResult(
        game=projected,
        distance=strategic_distance(game, projected),
        success=True,
        message=str(result.message),
        n_variables=n_variables,
        n_equalities=n_eq,
        n_inequalities=A_ub.shape[0],
    )


def project_payoff_linf(
    game: NormalFormGame,
    generators: Iterable[Relabeling],
    structure: Structure = "none",
) -> ProjectionResult:
    """Find an exactly symmetric game minimizing raw payoff L-infinity error."""
    gens = validate_generators(game.action_sizes, generators)
    n_pay = game.payoffs.size
    t_idx = n_pay
    n_variables = n_pay + 1
    objective = np.zeros(n_variables, dtype=float)
    objective[t_idx] = 1.0
    bounds = [(None, None)] * n_variables
    bounds[t_idx] = (0.0, None)

    ub_rows: list[int] = []
    ub_cols: list[int] = []
    ub_data: list[float] = []
    b_ub: list[float] = []
    row = 0
    for idx, value in enumerate(game.payoffs.reshape(-1)):
        ub_rows.extend([row, row])
        ub_cols.extend([idx, t_idx])
        ub_data.extend([1.0, -1.0])
        b_ub.append(float(value))
        row += 1
        ub_rows.extend([row, row])
        ub_cols.extend([idx, t_idx])
        ub_data.extend([-1.0, -1.0])
        b_ub.append(float(-value))
        row += 1
    A_ub = coo_matrix(
        (ub_data, (ub_rows, ub_cols)), shape=(row, n_variables)
    ).tocsr()

    eq_rows, eq_cols, eq_data, b_eq = _symmetry_equalities(game, gens)
    n_eq = _append_structure_equalities(
        game,
        structure,
        len(b_eq),
        eq_rows,
        eq_cols,
        eq_data,
        b_eq,
    )
    A_eq = (
        coo_matrix(
            (eq_data, (eq_rows, eq_cols)), shape=(n_eq, n_variables)
        ).tocsr()
        if n_eq
        else None
    )

    result = linprog(
        objective,
        A_ub=A_ub,
        b_ub=np.asarray(b_ub, dtype=float),
        A_eq=A_eq,
        b_eq=np.asarray(b_eq, dtype=float) if n_eq else None,
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"payoff projection LP failed: {result.message}")
    projected = NormalFormGame(result.x[:n_pay].reshape(game.payoffs.shape))
    return ProjectionResult(
        game=projected,
        distance=payoff_linf_distance(game, projected),
        success=True,
        message=str(result.message),
        n_variables=n_variables,
        n_equalities=n_eq,
        n_inequalities=A_ub.shape[0],
    )
