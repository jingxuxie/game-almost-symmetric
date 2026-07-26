"""Almost symmetric games: projections, witnesses, and equilibrium certificates."""

from .cycle import (
    CycleProjectionResult,
    IncentiveEdge,
    build_incentive_graph,
    project_strategic_cycle,
)
from .game import (
    NormalFormGame,
    add_nonstrategic_component,
    payoff_linf_distance,
    pure_regrets,
    residual_ranges,
    strategic_distance,
)
from .projection import ProjectionResult, project_payoff_linf, project_strategic
from .symmetry import (
    Relabeling,
    action_orbit_labels,
    apply_relabeling,
    cyclic_action_generator,
    group_closure,
    is_exact_symmetry,
    is_invariant_game,
    payoff_coordinate_orbit_labels,
    reynolds_symmetrize,
)
from .zero_sum import (
    ZeroSumSolution,
    exploitability,
    solve_invariant_saddle_gap,
    solve_zero_sum,
)

__all__ = [
    "NormalFormGame",
    "Relabeling",
    "ProjectionResult",
    "CycleProjectionResult",
    "IncentiveEdge",
    "ZeroSumSolution",
    "add_nonstrategic_component",
    "payoff_linf_distance",
    "pure_regrets",
    "residual_ranges",
    "strategic_distance",
    "project_payoff_linf",
    "project_strategic",
    "project_strategic_cycle",
    "build_incentive_graph",
    "action_orbit_labels",
    "payoff_coordinate_orbit_labels",
    "apply_relabeling",
    "cyclic_action_generator",
    "group_closure",
    "is_exact_symmetry",
    "is_invariant_game",
    "reynolds_symmetrize",
    "exploitability",
    "solve_invariant_saddle_gap",
    "solve_zero_sum",
]
