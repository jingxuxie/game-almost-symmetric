#!/usr/bin/env python3
"""Run all lightweight experiments and generate paper-ready figures.

From the repository root:

    PYTHONPATH=src python -m experiments.run_all
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from .common import FIGURES, RESULTS
from .correlated_studies import (
    make_correlated_figures,
    run_correlated_calibration,
    run_correlated_runtime,
    run_role_assignment_correlation,
)
from .plotting import make_figures, make_overview_figure
from .selection_study import (
    make_selection_figures,
    run_statistical_selection,
)
from .sharpness import (
    make_reynolds_tightness_figure,
    run_reynolds_tightness,
)
from .studies import (
    run_calibration,
    run_cycle_characterization,
    run_hierarchy,
    run_nonstrategic,
    run_role_assignment,
    run_runtime,
    run_sampling,
    run_tightness,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--replicates", type=int, default=20)
    parser.add_argument("--sampling-replicates", type=int, default=40)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="run a small deterministic CI smoke configuration",
    )
    args = parser.parse_args()

    calibration_replicates = (
        min(args.replicates, 3) if args.quick else args.replicates
    )
    sampling_replicates = (
        min(args.sampling_replicates, 3)
        if args.quick
        else args.sampling_replicates
    )
    runtime_repetitions = 2 if args.quick else 7
    correlated_runtime_repetitions = 1 if args.quick else 3
    correlated_duplicate_factors = (1, 2, 4) if args.quick else (1, 2, 3, 4, 6, 8, 12)

    RESULTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    make_overview_figure()
    tables = {
        "nonstrategic": run_nonstrategic(args.seed),
        "cycles": run_cycle_characterization(
            args.seed + 1, calibration_replicates
        ),
        "calibration": run_calibration(
            args.seed + 2, calibration_replicates
        ),
        "hierarchy": run_hierarchy(args.seed + 3),
        "role_assignment": run_role_assignment(),
        "tightness": run_tightness(),
        "reynolds_tightness": run_reynolds_tightness(),
        "runtime": run_runtime(
            args.seed + 4, repetitions=runtime_repetitions
        ),
        "sampling": run_sampling(
            args.seed + 5, sampling_replicates
        ),
        "correlated_calibration": run_correlated_calibration(
            args.seed + 6, calibration_replicates
        ),
        "correlated_role_assignment": run_role_assignment_correlation(),
        "correlated_runtime": run_correlated_runtime(
            args.seed + 7,
            repetitions=correlated_runtime_repetitions,
            duplicate_factors=correlated_duplicate_factors,
        ),
        "statistical_selection": run_statistical_selection(
            args.seed + 8,
            calibration_replicates,
            quick=args.quick,
        ),
    }
    for name, table in tables.items():
        table.to_csv(RESULTS / f"{name}.csv", index=False)
    tables["calibration"].groupby("sigma", as_index=False).agg(
        strategic_defect_mean=("strategic_defect", "mean"),
        saddle_gap_mean=("saddle_gap", "mean"),
        saddle_gap_std=("saddle_gap", "std"),
        certificate_mean=("certificate", "mean"),
        direct_invariant_gap_mean=("direct_invariant_gap", "mean"),
        reynolds_ratio_max=("reynolds_over_optimal", "max"),
    ).to_csv(RESULTS / "calibration_summary.csv", index=False)
    tables["sampling"].groupby("samples_per_entry", as_index=False).agg(
        true_max_regret_mean=("true_max_regret", "mean"),
        certificate_mean=("max_regret_certificate", "mean"),
        empirical_coverage=("covered", "mean"),
    ).to_csv(RESULTS / "sampling_summary.csv", index=False)
    tables["correlated_calibration"].groupby("sigma", as_index=False).agg(
        strategic_defect_mean=("strategic_defect", "mean"),
        transferred_ce_violation_mean=("transferred_ce_violation", "mean"),
        direct_ce_violation_mean=("direct_ce_violation", "mean"),
        transferred_welfare_mean=("transferred_welfare", "mean"),
        direct_welfare_mean=("direct_welfare", "mean"),
    ).to_csv(RESULTS / "correlated_calibration_summary.csv", index=False)
    tables["statistical_selection"].groupby(
        "samples_per_entry", as_index=False
    ).agg(
        selected_action_orbits_median=("selected_action_orbits", "median"),
        selected_certificate_mean=("selected_certificate", "mean"),
        selected_true_defect_mean=("selected_true_defect", "mean"),
        true_max_regret_mean=("true_max_regret", "mean"),
        oracle_selection_rate=("selected_oracle", "mean"),
        confidence_event_rate=("confidence_event", "mean"),
        defect_coverage=("defect_covered", "mean"),
        regret_coverage=("regret_covered", "mean"),
    ).to_csv(RESULTS / "statistical_selection_summary.csv", index=False)
    make_figures(tables)
    make_reynolds_tightness_figure(tables["reynolds_tightness"])
    make_correlated_figures(
        tables["correlated_calibration"],
        tables["correlated_role_assignment"],
        tables["correlated_runtime"],
    )
    make_selection_figures(tables["statistical_selection"])

    solved_roles = tables["correlated_role_assignment"].dropna(
        subset=["solver_welfare"]
    )
    largest_selection_sample = tables["statistical_selection"][
        "samples_per_entry"
    ].max()
    largest_selection_rows = tables["statistical_selection"][
        tables["statistical_selection"]["samples_per_entry"]
        == largest_selection_sample
    ]
    summary = {
        "seed": args.seed,
        "calibration_replicates": calibration_replicates,
        "sampling_replicates": sampling_replicates,
        "quick": args.quick,
        "max_transfer_violation": float(
            np.max(
                tables["calibration"]["saddle_gap"]
                - tables["calibration"]["certificate"]
            )
        ),
        "max_ce_transfer_violation": float(
            np.max(
                tables["correlated_calibration"]["transferred_ce_violation"]
                - tables["correlated_calibration"]["certificate"]
            )
        ),
        "max_ce_direct_violation": float(
            np.max(
                tables["correlated_calibration"]["direct_ce_violation"]
                - tables["correlated_calibration"]["certificate"]
            )
        ),
        "max_reynolds_ratio_random": float(
            tables["calibration"]["reynolds_over_optimal"].max()
        ),
        "max_reynolds_ratio_sharpness": float(
            tables["reynolds_tightness"]["observed_ratio"].max()
        ),
        "max_reynolds_formula_error": float(
            tables["reynolds_tightness"]["absolute_formula_error"].max()
        ),
        "max_cycle_lp_disagreement": float(
            np.max(
                np.abs(
                    tables["cycles"]["lp_defect"]
                    - tables["cycles"]["cycle_defect"]
                )
            )
        ),
        "max_cycle_witness_disagreement": float(
            np.max(
                np.abs(
                    tables["cycles"]["witness_mean_inconsistency"]
                    - tables["cycles"]["cycle_defect"]
                )
            )
        ),
        "max_role_assignment_ce_welfare_error": float(
            np.max(np.abs(solved_roles["solver_welfare"] - 1.0))
        ),
        "sampling_empirical_coverage": float(
            tables["sampling"]["covered"].mean()
        ),
        "selection_defect_coverage": float(
            tables["statistical_selection"]["defect_covered"].mean()
        ),
        "selection_regret_coverage": float(
            tables["statistical_selection"]["regret_covered"].mean()
        ),
        "selection_oracle_rate_largest_sample": float(
            largest_selection_rows["selected_oracle"].mean()
        ),
        "largest_runtime_speedup": float(
            tables["runtime"]["speedup"].max()
        ),
        "largest_correlated_variable_reduction": float(
            np.max(
                tables["correlated_runtime"]["full_profile_variables"]
                / tables["correlated_runtime"]["orbit_profile_variables"]
            )
        ),
    }
    (RESULTS / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
