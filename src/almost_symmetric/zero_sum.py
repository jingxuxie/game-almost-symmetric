"""Equilibrium and symmetry-constrained solvers for zero-sum matrix games."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

from .symmetry import Relabeling, action_offsets, action_orbit_labels, validate_generators


@dataclass(frozen=True)
class ZeroSumSolution:
    row_strategy: np.ndarray
    column_strategy: np.ndarray
    value: float
    row_regret: float
    column_regret: float
    saddle_gap: float
    success: bool
    message: str
    n_variables: int | None = None
    n_inequalities: int | None = None


def exploitability(
    matrix: np.ndarray, x: np.ndarray, y: np.ndarray
) -> tuple[float, float, float]:
    matrix = np.asarray(matrix, dtype=float)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if matrix.shape != (x.size, y.size):
        raise ValueError("matrix and strategy dimensions are inconsistent")
    payoff = float(x @ matrix @ y)
    row_regret = max(0.0, float(np.max(matrix @ y) - payoff))
    column_regret = max(0.0, float(payoff - np.min(x @ matrix)))
    return row_regret, column_regret, row_regret + column_regret


def solve_zero_sum(matrix: np.ndarray) -> ZeroSumSolution:
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    m, n = matrix.shape

    # Row player's maximin LP.
    c_row = np.zeros(m + 1)
    c_row[-1] = -1.0
    A_ub_row = np.zeros((n, m + 1))
    A_ub_row[:, :m] = -matrix.T
    A_ub_row[:, -1] = 1.0
    A_eq_row = np.zeros((1, m + 1))
    A_eq_row[0, :m] = 1.0
    row_result = linprog(
        c_row,
        A_ub=A_ub_row,
        b_ub=np.zeros(n),
        A_eq=A_eq_row,
        b_eq=np.ones(1),
        bounds=[(0.0, None)] * m + [(None, None)],
        method="highs",
    )
    if not row_result.success:
        raise RuntimeError(f"row equilibrium LP failed: {row_result.message}")

    # Column player's minimax LP.
    c_col = np.zeros(n + 1)
    c_col[-1] = 1.0
    A_ub_col = np.zeros((m, n + 1))
    A_ub_col[:, :n] = matrix
    A_ub_col[:, -1] = -1.0
    A_eq_col = np.zeros((1, n + 1))
    A_eq_col[0, :n] = 1.0
    col_result = linprog(
        c_col,
        A_ub=A_ub_col,
        b_ub=np.zeros(m),
        A_eq=A_eq_col,
        b_eq=np.ones(1),
        bounds=[(0.0, None)] * n + [(None, None)],
        method="highs",
    )
    if not col_result.success:
        raise RuntimeError(f"column equilibrium LP failed: {col_result.message}")

    x = np.asarray(row_result.x[:m])
    y = np.asarray(col_result.x[:n])
    row_regret, column_regret, gap = exploitability(matrix, x, y)
    return ZeroSumSolution(
        row_strategy=x,
        column_strategy=y,
        value=float(x @ matrix @ y),
        row_regret=row_regret,
        column_regret=column_regret,
        saddle_gap=gap,
        success=True,
        message="optimal",
        n_variables=m + n + 2,
        n_inequalities=m + n,
    )


def _orbit_probability_maps(
    row_actions: int,
    column_actions: int,
    generators: Iterable[Relabeling],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    action_sizes = (row_actions, column_actions)
    gens = validate_generators(action_sizes, generators)
    labels = action_orbit_labels(action_sizes, gens)
    offsets = action_offsets(action_sizes)
    n_orbits = int(labels.max(initial=-1) + 1)
    row_map = np.zeros((row_actions, n_orbits), dtype=float)
    column_map = np.zeros((column_actions, n_orbits), dtype=float)
    for i in range(row_actions):
        row_map[i, labels[offsets[0] + i]] = 1.0
    for j in range(column_actions):
        column_map[j, labels[offsets[1] + j]] = 1.0
    return row_map, column_map, labels


def solve_invariant_saddle_gap(
    matrix: np.ndarray,
    generators: Iterable[Relabeling],
    *,
    compress_constraints: bool = False,
    exact_invariant_game: bool = False,
) -> ZeroSumSolution:
    """Minimize saddle-point gap over symmetry-respecting profiles.

    With ``compress_constraints=True``, one best-response constraint is retained
    per within-player action orbit. This is valid only for a matrix known to be
    exactly invariant under the supplied generators.
    """
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    m, n = matrix.shape
    gens = validate_generators((m, n), generators)
    row_map, column_map, _ = _orbit_probability_maps(m, n, gens)
    n_orbits = row_map.shape[1]

    if compress_constraints and not exact_invariant_game:
        raise ValueError("constraint compression requires an exactly invariant matrix")

    alpha_idx = n_orbits
    beta_idx = n_orbits + 1
    n_variables = n_orbits + 2
    objective = np.zeros(n_variables)
    objective[alpha_idx] = 1.0
    objective[beta_idx] = -1.0

    row_indices = list(range(m))
    column_indices = list(range(n))
    if compress_constraints:
        row_labels = [int(np.argmax(row_map[i])) for i in range(m)]
        column_labels = [int(np.argmax(column_map[j])) for j in range(n)]
        row_indices = [row_labels.index(label) for label in sorted(set(row_labels))]
        column_indices = [
            column_labels.index(label) for label in sorted(set(column_labels))
        ]

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    b_ub: list[float] = []
    row = 0

    # A y <= alpha 1, with y = column_map z.
    Ay_coeff = matrix @ column_map
    for i in row_indices:
        for orbit, coefficient in enumerate(Ay_coeff[i]):
            if coefficient != 0.0:
                rows.append(row)
                cols.append(orbit)
                data.append(float(coefficient))
        rows.append(row)
        cols.append(alpha_idx)
        data.append(-1.0)
        b_ub.append(0.0)
        row += 1

    # x^T A >= beta 1, with x = row_map z.
    xA_coeff = row_map.T @ matrix
    for j in column_indices:
        for orbit, coefficient in enumerate(xA_coeff[:, j]):
            if coefficient != 0.0:
                rows.append(row)
                cols.append(orbit)
                data.append(float(-coefficient))
        rows.append(row)
        cols.append(beta_idx)
        data.append(1.0)
        b_ub.append(0.0)
        row += 1

    A_ub = coo_matrix(
        (data, (rows, cols)), shape=(row, n_variables)
    ).tocsr()
    A_eq = np.zeros((2, n_variables), dtype=float)
    A_eq[0, :n_orbits] = np.sum(row_map, axis=0)
    A_eq[1, :n_orbits] = np.sum(column_map, axis=0)
    bounds = [(0.0, None)] * n_orbits + [(None, None), (None, None)]

    result = linprog(
        objective,
        A_ub=A_ub,
        b_ub=np.asarray(b_ub),
        A_eq=A_eq,
        b_eq=np.ones(2),
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"invariant saddle-gap LP failed: {result.message}")

    z = result.x[:n_orbits]
    x = row_map @ z
    y = column_map @ z
    row_regret, column_regret, gap = exploitability(matrix, x, y)
    return ZeroSumSolution(
        row_strategy=x,
        column_strategy=y,
        value=float(x @ matrix @ y),
        row_regret=row_regret,
        column_regret=column_regret,
        saddle_gap=gap,
        success=True,
        message=str(result.message),
        n_variables=n_variables,
        n_inequalities=A_ub.shape[0],
    )
