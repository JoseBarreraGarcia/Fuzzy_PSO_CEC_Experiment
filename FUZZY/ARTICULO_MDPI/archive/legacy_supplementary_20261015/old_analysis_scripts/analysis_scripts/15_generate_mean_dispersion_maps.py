#!/usr/bin/env python
"""Generate mean-versus-dispersion maps from the current MDPI run summaries.

Each point is one fixed algorithm configuration evaluated on one benchmark
instance. X is the mean normalized gap over 31 independent runs; Y is the sample
standard deviation of that same normalized gap. A lower-left point is better on
both criteria. Log axes are used because the observed ranges span several orders
of magnitude. Zero-gap instances are placed at a labelled display floor only.

Outputs:
    manuscript/figures/fig_mean_dispersion_representative.{png,pdf}
    manuscript/figures/supplementary/fig_mean_dispersion_by_function.pdf (23 pages)
    results/figures_all/fig_mean_dispersion_representative.{png,pdf}
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _naming import short_name

REPO_ROOT = Path(__file__).resolve().parents[3]
MDPI = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI"
STATS = MDPI / "results" / "level2_aggregated" / "stats_by_config_instance.csv"
PER_FUNCTION = MDPI / "results" / "level3_rankings" / "function_level_per_function.csv"
MS_FIGURES = MDPI / "manuscript" / "figures"
MS_SUPPLEMENT = MS_FIGURES / "supplementary"
OUT_FIGURES = MDPI / "results" / "figures_all"

FLOOR = 1e-12
DIMS = [10, 30, 50, 100]
RULES = [f"R{i}" for i in range(1, 9)]
MARKERS = {3: "o", 5: "s", 7: "^", 9: "D"}
RULE_COLORS = dict(zip(RULES, plt.get_cmap("tab10").colors[:8]))
REPRESENTATIVE_INSTANCES = ["F1_D30", "F9_D30", "F14_D2", "F23_D4"]


def function_sort_key(name: str) -> int:
    return int(name[1:])


def instance_data(df: pd.DataFrame, instance: str) -> pd.DataFrame:
    block = df[df["instance"] == instance].copy()
    block["config"] = block["mh_raw"].map(short_name)
    block["x"] = block["gap_mean"].clip(lower=FLOOR)
    block["y"] = block["gap_std"].clip(lower=FLOOR)
    block["rule"] = block["rule_set"].fillna("--")
    return block


def axis_limits(values: np.ndarray) -> tuple[float, float]:
    positive = values[np.isfinite(values) & (values > FLOOR)]
    if positive.size == 0:
        return FLOOR / 2, FLOOR * 20
    return max(FLOOR / 2, float(positive.min()) / 2), max(float(positive.max()) * 2, FLOOR * 20)


def add_instance(ax, block: pd.DataFrame, title: str, best_config: str | None = None,
                 annotate: bool = False,
                 shared_limits: dict[str, tuple[float, float]] | None = None) -> None:
    fcs = block[block["mh_family"] == "PSO_FCS"]
    for rule in RULES:
        subset = fcs[fcs["rule"] == rule]
        for n, points in subset.groupby("n_labels"):
            ax.scatter(points["x"], points["y"], s=34, marker=MARKERS[int(n)],
                       color=RULE_COLORS[rule], alpha=0.78, edgecolors="white",
                       linewidths=0.35, zorder=2)

    pso = block[block["mh_family"] == "PSO"]
    if not pso.empty:
        row = pso.iloc[0]
        ax.scatter(row["x"], row["y"], s=105, marker="*", color="black",
                   edgecolors="white", linewidths=0.45, zorder=6)
        if annotate:
            ax.annotate("PSO", (row["x"], row["y"]), xytext=(-22, 9),
                        textcoords="offset points", fontsize=7, fontweight="bold")

    if best_config and best_config != "--":
        best = block[block["mh_raw"].map(short_name) == best_config]
        if not best.empty:
            row = best.iloc[0]
            ax.scatter(row["x"], row["y"], s=115, marker="o", facecolors="none",
                       edgecolors="black", linewidths=1.3, zorder=5)
            if annotate and best_config != "PSO":
                ax.annotate(best_config, (row["x"], row["y"]), xytext=(6, -13),
                            textcoords="offset points", fontsize=7)

    ax.set_xscale("log")
    ax.set_yscale("log")
    for column, setter in (("x", ax.set_xlim), ("y", ax.set_ylim)):
        low, high = ((shared_limits or {}).get(column)
                     or axis_limits(block[column].to_numpy(dtype=float)))
        setter(low, high)
        ticks = np.geomspace(low, high, 3)
        formatter = [_tick_label(value) for value in ticks]
        if column == "x":
            ax.xaxis.set_major_locator(FixedLocator(ticks))
            ax.xaxis.set_major_formatter(FixedFormatter(formatter))
            ax.xaxis.set_minor_locator(NullLocator())
        else:
            ax.yaxis.set_major_locator(FixedLocator(ticks))
            ax.yaxis.set_major_formatter(FixedFormatter(formatter))
            ax.yaxis.set_minor_locator(NullLocator())
    if (block["gap_mean"].eq(0) & block["gap_std"].eq(0)).all():
        ax.text(0.5, 0.5, "All configurations reach the optimum",
                transform=ax.transAxes, ha="center", va="center", fontsize=8,
                bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"})
    ax.set_title(title, fontsize=9.5)
    ax.grid(True, which="both", alpha=0.22, linewidth=0.45)


def _tick_label(value: float) -> str:
    if value < 0.01 or value >= 1000:
        return f"{value:.0e}"
    return f"{value:.2g}"


def style_legend(fig) -> None:
    rule_handles = [Line2D([], [], marker="o", linestyle="none", color=RULE_COLORS[r],
                           markersize=5, label=r) for r in RULES]
    n_handles = [Line2D([], [], marker=MARKERS[n], linestyle="none", color="0.3",
                        markersize=5, label=f"n={n}") for n in MARKERS]
    special = [
        Line2D([], [], marker="*", linestyle="none", color="black", markersize=9,
               label="PSO baseline"),
        Line2D([], [], marker="o", linestyle="none", markerfacecolor="none",
               markeredgecolor="black", markersize=7, label="Best FCS for function"),
    ]
    fig.legend(handles=rule_handles + n_handles + special, ncol=7, fontsize=7.2,
               loc="lower center", bbox_to_anchor=(0.5, 0.015), frameon=False)


def save_representative(df: pd.DataFrame, best: pd.DataFrame) -> None:
    best_map = best.set_index("function")["best_fcs"].to_dict()
    cases = [("F1_D30", "F1", "Unimodal: F1, d=30"),
             ("F9_D30", "F9", "Scalable multimodal: F9, d=30"),
             ("F14_D2", "F14", "Fixed-dimensional: F14, d=2"),
             ("F23_D4", "F23", "Fixed-dimensional: F23, d=4")]
    fig, axes = plt.subplots(2, 2, figsize=(9.2, 7.0))
    for ax, (instance, function, title) in zip(axes.ravel(), cases):
        block = instance_data(df, instance)
        add_instance(ax, block, title, best_map.get(function), annotate=True)
        ax.set_xlabel("Mean normalized gap (31 runs)", fontsize=8)
        ax.set_ylabel("SD of normalized gap (31 runs)", fontsize=8)
    style_legend(fig)
    fig.suptitle("Performance versus run-to-run dispersion", fontsize=12, y=0.98)
    fig.text(0.5, 0.07,
             "Each point is a fixed configuration on one instance; lower-left is better. "
             "Log axes; zero gaps are shown at 10^-12.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.10, 1, 0.95))
    _save_fig(fig, "fig_mean_dispersion_representative")


def save_full_supplement(df: pd.DataFrame, best: pd.DataFrame) -> None:
    best_map = best.set_index("function")["best_fcs"].to_dict()
    MS_SUPPLEMENT.mkdir(parents=True, exist_ok=True)
    with PdfPages(MS_SUPPLEMENT / "fig_mean_dispersion_by_function.pdf") as pdf:
        for function in sorted(df["function"].unique(), key=function_sort_key):
            dims = sorted(df.loc[df["function"] == function, "dim"].unique())
            if len(dims) == 4:
                fig, axes = plt.subplots(2, 2, figsize=(8.4, 6.6), sharex=True, sharey=True)
                panel_axes = axes.ravel()
                all_dims = df[df["function"] == function]
                limits = {axis: axis_limits(all_dims[axis].clip(lower=FLOOR).to_numpy(dtype=float))
                          for axis in ("gap_mean", "gap_std")}
                # instance_data renames these columns to x/y for plotting.
                limits = {"x": limits["gap_mean"], "y": limits["gap_std"]}
                for ax, dim in zip(panel_axes, dims):
                    instance = f"{function}_D{dim}"
                    add_instance(ax, instance_data(df, instance), f"{function}, d={dim}",
                                 best_map.get(function), annotate=False, shared_limits=limits)
                for ax in panel_axes[2:]:
                    ax.set_xlabel("Mean normalized gap", fontsize=8)
                for ax in panel_axes[::2]:
                    ax.set_ylabel("SD of normalized gap", fontsize=8)
            else:
                fig, ax = plt.subplots(figsize=(8.4, 6.6))
                dim = dims[0]
                instance = f"{function}_D{dim}"
                add_instance(ax, instance_data(df, instance), f"{function}, d={dim}",
                             best_map.get(function), annotate=True)
                ax.set_xlabel("Mean normalized gap over 31 runs")
                ax.set_ylabel("SD of normalized gap over 31 runs")
            style_legend(fig)
            fig.suptitle(f"{function}: performance versus run-to-run dispersion", fontsize=11, y=0.98)
            fig.text(0.5, 0.045,
                     "Each point is one fixed configuration; lower-left is better. "
                     "Log axes; zero gaps are displayed at 10^-12.",
                     ha="center", fontsize=7.5)
            fig.tight_layout(rect=(0, 0.08, 1, 0.94))
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
    print(f"[15] wrote {MS_SUPPLEMENT / 'fig_mean_dispersion_by_function.pdf'} (23 pages)")


def _save_fig(fig, stem: str) -> None:
    for folder in (MS_FIGURES, OUT_FIGURES):
        folder.mkdir(parents=True, exist_ok=True)
        for ext in ("png", "pdf"):
            fig.savefig(folder / f"{stem}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[15] wrote {stem}.{{png,pdf}}")


def main() -> int:
    for path in (STATS, PER_FUNCTION):
        if not path.exists():
            raise FileNotFoundError(f"Missing input: {path}")
    df = pd.read_csv(STATS)
    expected = {"mh_raw", "mh_family", "rule_set", "n_labels", "function", "dim",
                "n_runs", "gap_mean", "gap_std"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Required run-summary columns absent: {sorted(missing)}")
    if not (df["n_runs"] == 31).all():
        raise ValueError("Expected 31 runs per configuration-instance row")
    df["instance"] = df["function"] + "_D" + df["dim"].astype(int).astype(str)
    best = pd.read_csv(PER_FUNCTION)
    save_representative(df, best)
    save_full_supplement(df, best)
    print("[15] rows:", len(df), "instances:", df[["function", "dim"]].drop_duplicates().shape[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
