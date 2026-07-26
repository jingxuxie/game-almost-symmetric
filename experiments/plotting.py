"""Paper figure generation."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd

from .common import save_plot

def make_figures(tables: dict[str, pd.DataFrame]) -> None:
    nonstrategic = tables["nonstrategic"]
    fig, axis = plt.subplots(figsize=(3.35, 2.45))
    axis.plot(
        nonstrategic["scale"],
        nonstrategic["raw_payoff_defect"],
        marker="o",
        label="Raw payoff defect",
    )
    axis.plot(
        nonstrategic["scale"],
        nonstrategic["strategic_defect"],
        marker="s",
        label="Strategic defect",
    )
    axis.set_xlabel("Nonstrategic shift magnitude")
    axis.set_ylabel("Distance to exact symmetry")
    axis.legend(frameon=False)
    axis.grid(alpha=0.25)
    save_plot(fig, "nonstrategic_separation")

    calibration = tables["calibration"]
    grouped = calibration.groupby("sigma", as_index=False).agg(
        saddle_gap=("saddle_gap", "mean"),
        saddle_gap_std=("saddle_gap", "std"),
        certificate=("certificate", "mean"),
        direct_gap=("direct_invariant_gap", "mean"),
    )
    fig, axis = plt.subplots(figsize=(3.35, 2.45))
    axis.plot(
        grouped["sigma"],
        grouped["saddle_gap"],
        marker="o",
        label="Projected equilibrium",
    )
    axis.fill_between(
        grouped["sigma"],
        np.maximum(0.0, grouped["saddle_gap"] - grouped["saddle_gap_std"].fillna(0.0)),
        grouped["saddle_gap"] + grouped["saddle_gap_std"].fillna(0.0),
        alpha=0.15,
    )
    axis.plot(
        grouped["sigma"],
        grouped["certificate"],
        marker="s",
        label=r"Certificate $2\delta_G$",
    )
    axis.plot(
        grouped["sigma"],
        grouped["direct_gap"],
        marker="^",
        label="Best invariant profile",
    )
    axis.set_xlabel("Payoff perturbation scale")
    axis.set_ylabel("Saddle-point gap")
    axis.legend(frameon=False)
    axis.grid(alpha=0.25)
    save_plot(fig, "certificate_calibration")

    hierarchy = tables["hierarchy"].sort_values("action_orbits", ascending=False)
    fig, axis = plt.subplots(figsize=(3.35, 2.45))
    axis.plot(
        hierarchy["action_orbits"],
        hierarchy["strategic_defect"],
        marker="o",
        label=r"Defect $\delta_G$",
    )
    axis.plot(
        hierarchy["action_orbits"],
        hierarchy["saddle_gap"],
        marker="s",
        label="Transferred gap",
    )
    axis.plot(
        hierarchy["action_orbits"],
        hierarchy["direct_invariant_gap"],
        marker="^",
        label="Best invariant gap",
    )
    axis.invert_xaxis()
    axis.set_xlabel("Action orbits (fewer = more compression)")
    axis.set_ylabel("Error")
    axis.legend(frameon=False)
    axis.grid(alpha=0.25)
    save_plot(fig, "compression_frontier")

    runtime = tables["runtime"]
    fig, axis = plt.subplots(figsize=(3.35, 2.45))
    axis.plot(
        runtime["actions_per_player"],
        runtime["full_time_seconds"],
        marker="o",
        label="Full equilibrium LP",
    )
    axis.plot(
        runtime["actions_per_player"],
        runtime["orbit_time_seconds"],
        marker="s",
        label="Orbit-reduced LP",
    )
    axis.set_xscale("log", base=2)
    axis.set_yscale("log")
    axis.set_xlabel("Actions per player")
    axis.set_ylabel("Median solve time (s)")
    axis.legend(frameon=False)
    axis.grid(alpha=0.25)
    save_plot(fig, "runtime")

    tightness = tables["tightness"]
    fig, axis = plt.subplots(figsize=(3.35, 2.45))
    axis.plot(
        tightness["orbit_size"],
        tightness["regret_over_defect"],
        marker="o",
        label="Measured",
    )
    axis.plot(
        tightness["orbit_size"],
        tightness["theory_ratio"],
        linestyle="--",
        label=r"$1-1/k$",
    )
    axis.set_xscale("log")
    axis.set_ylim(0.45, 1.02)
    axis.set_xlabel("Symmetric action-orbit size $k$")
    axis.set_ylabel(r"Invariant regret / $\delta_G$")
    axis.legend(frameon=False)
    axis.grid(alpha=0.25)
    save_plot(fig, "tightness")

    sampling = tables["sampling"]
    sampling_grouped = sampling.groupby("samples_per_entry", as_index=False).agg(
        true_regret=("true_max_regret", "mean"),
        certificate=("max_regret_certificate", "mean"),
        coverage=("covered", "mean"),
    )
    fig, axis = plt.subplots(figsize=(3.35, 2.45))
    axis.plot(
        sampling_grouped["samples_per_entry"],
        sampling_grouped["true_regret"],
        marker="o",
        label="True maximum regret",
    )
    axis.plot(
        sampling_grouped["samples_per_entry"],
        sampling_grouped["certificate"],
        marker="s",
        label="95% certificate",
    )
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("Samples per payoff entry")
    axis.set_ylabel("Regret")
    axis.legend(frameon=False)
    axis.grid(alpha=0.25)
    save_plot(fig, "sampling_certificate")

def make_overview_figure() -> None:
    """Generate a compact conceptual overview of the certified pipeline."""
    fig, axis = plt.subplots(figsize=(7.0, 1.55))
    axis.set_xlim(0.0, 1.0)
    axis.set_ylim(0.0, 1.0)
    axis.axis("off")
    boxes = [
        (0.015, 0.25, 0.205, 0.55, "Observed game $\\Gamma$\nsmall heterogeneities"),
        (0.275, 0.25, 0.205, 0.55, "Nearest $G$-symmetric\nsurrogate $\\widehat{\\Gamma}$"),
        (0.535, 0.25, 0.205, 0.55, "$G$-respecting\nequilibrium $\\widehat{\\sigma}$"),
        (0.795, 0.25, 0.19, 0.55, "Certificate in $\\Gamma$\n$R_i(\\widehat{\\sigma})\\leq\\delta_G$"),
    ]
    for x, y, w, h, label in boxes:
        patch = FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.018", fill=False, linewidth=1.2
        )
        axis.add_patch(patch)
        axis.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=8.5)
    arrow_labels = [r"LP or cycle mean", r"orbit-reduced solver", r"transfer theorem"]
    for idx, label in enumerate(arrow_labels):
        left = boxes[idx][0] + boxes[idx][2]
        right = boxes[idx + 1][0]
        arrow = FancyArrowPatch(
            (left + 0.008, 0.525), (right - 0.008, 0.525),
            arrowstyle="-|>", mutation_scale=10, linewidth=1.0
        )
        axis.add_patch(arrow)
        axis.text((left + right) / 2, 0.73, label, ha="center", va="bottom", fontsize=7.5)
    axis.text(
        0.5, 0.08,
        r"Strategic defect $\delta_G$ measures unilateral-incentive distortion, not raw payoff mismatch.",
        ha="center", va="center", fontsize=8.5,
    )
    save_plot(fig, "overview")
