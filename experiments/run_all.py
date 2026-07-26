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
from .plotting import make_figures, make_overview_figure
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
    make_figures(tables)
    make_reynolds_tightness_figure(tables["reynolds_tightness"])

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
        "sampling_empirical_coverage": float(
            tables["sampling"]["covered"].mean()
        ),
        "largest_runtime_speedup": float(
            tables["runtime"]["speedup"].max()
        ),
    }
    (RESULTS / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
