#!/usr/bin/env python
"""Generate mean-versus-dispersion maps from the current MDPI run summaries.

Each point is one fixed algorithm configuration evaluated on one benchmark
instance. X is the mean normalized gap over 31 independent runs; Y is the sample
standard deviation of that same normalized gap. A lower-left point is better on
both criteria. Log axes are used because the observed ranges span several orders
of magnitude. Zero-gap instances are placed at a labelled display floor only.

Outputs:
    manuscript/figures/fig_mean_dispersion_representative.{png,pdf}
    manuscript/figures/appendices/fig_mean_dispersion_by_function.pdf (7 portrait pages, 3x3 panels)
    manuscript/figures/appendices/dispersion_atlas_figures.tex (MDPI full-width wrappers)
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
MS_APPENDIX = MS_FIGURES / "appendices"
MS_APPENDIX_TEX = MS_APPENDIX / "dispersion_atlas_figures.tex"
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
                 shared_limits: dict[str, tuple[float, float]] | None = None,
                 compact: bool = False) -> None:
    marker_size = 18 if compact else 34
    baseline_size = 60 if compact else 105
    best_size = 70 if compact else 115
    fcs = block[block["mh_family"] == "PSO_FCS"]
    for rule in RULES:
        subset = fcs[fcs["rule"] == rule]
        for n, points in subset.groupby("n_labels"):
            ax.scatter(points["x"], points["y"], s=marker_size, marker=MARKERS[int(n)],
                       color=RULE_COLORS[rule], alpha=0.78, edgecolors="white",
                       linewidths=0.35, zorder=2)

    pso = block[block["mh_family"] == "PSO"]
    if not pso.empty:
        row = pso.iloc[0]
        ax.scatter(row["x"], row["y"], s=baseline_size, marker="*", color="black",
                   edgecolors="white", linewidths=0.45, zorder=6)
        if annotate:
            ax.annotate("PSO", (row["x"], row["y"]), xytext=(-22, 9),
                        textcoords="offset points", fontsize=7, fontweight="bold")

    if best_config and best_config != "--":
        best = block[block["mh_raw"].map(short_name) == best_config]
        if not best.empty:
            row = best.iloc[0]
            ax.scatter(row["x"], row["y"], s=best_size, marker="o", facecolors="none",
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
    if compact:
        ax.tick_params(axis="both", labelsize=6, pad=1)
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
    for panel, (ax, (instance, function, title)) in enumerate(zip(axes.ravel(), cases)):
        block = instance_data(df, instance)
        add_instance(ax, block, title, best_map.get(function), annotate=True)
        ax.text(0.03, 0.96, f"({chr(97 + panel)}) {function}, $d={int(block['dim'].iloc[0])}$",
                transform=ax.transAxes, va="top", fontsize=8, fontweight="bold")
        ax.set_xlabel("Mean normalized gap (31 runs)", fontsize=8)
        ax.set_ylabel("SD of normalized gap (31 runs)", fontsize=8)
    style_legend(fig)
    fig.text(0.5, 0.07,
             "Each point is a fixed configuration on one instance; lower-left is better. "
             "Log axes; zero gaps are shown at 10^-12.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.10, 1, 0.95))
    _save_fig(fig, "fig_mean_dispersion_representative")


def save_full_supplement(df: pd.DataFrame, best: pd.DataFrame) -> None:
    best_map = best.set_index("function")["best_fcs"].to_dict()
    MS_APPENDIX.mkdir(parents=True, exist_ok=True)
    functions = sorted(df["function"].unique(), key=function_sort_key)
    limits_by_function = {}
    for function in functions:
        function_data = df[df["function"] == function]
        if function_data["dim"].nunique() == 4:
            limits_by_function[function] = {
                "x": axis_limits(function_data["gap_mean"].clip(lower=FLOOR).to_numpy(dtype=float)),
                "y": axis_limits(function_data["gap_std"].clip(lower=FLOOR).to_numpy(dtype=float)),
            }
    instances = [
        (function, int(dim))
        for function in functions
        for dim in sorted(df.loc[df["function"] == function, "dim"].unique())
    ]
    with PdfPages(MS_APPENDIX / "fig_mean_dispersion_by_function.pdf") as pdf:
        for start in range(0, len(instances), 9):
            page_instances = instances[start:start + 9]
            fig, axes = plt.subplots(3, 3, figsize=(8.27, 9.4))
            for panel, (function, dim) in enumerate(page_instances):
                ax = axes.ravel()[panel]
                instance = f"{function}_D{dim}"
                add_instance(
                    ax, instance_data(df, instance), f"{function}, d={dim}",
                    best_map.get(function), annotate=False,
                    shared_limits=limits_by_function.get(function), compact=True,
                )
                ax.set_box_aspect(0.85)
                ax.text(0.03, 0.95, f"{function}, d={dim}",
                        transform=ax.transAxes, va="top", fontsize=7, fontweight="bold")
                row, column = divmod(panel, 3)
                if row == 2:
                    ax.set_xlabel("Mean normalized gap", fontsize=7)
                if column == 0:
                    ax.set_ylabel("SD of normalized gap", fontsize=7)
            for ax in axes.ravel()[len(page_instances):]:
                ax.set_visible(False)
            style_legend(fig)
            fig.subplots_adjust(left=0.075, right=0.99, top=0.98, bottom=0.15,
                                wspace=0.28, hspace=0.32)
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
    page_count = (len(instances) + 8) // 9
    tex_lines = ["% Generated by code/15_generate_mean_dispersion_maps.py."]
    for page in range(1, page_count + 1):
        tex_lines.extend([
            "\\begin{figure}[p]",
            "  \\begin{adjustwidth}{-\\extralength}{0cm}",
            "  \\centering",
            f"  \\includegraphics[page={page},width=\\fulllength,height=0.82\\textheight,keepaspectratio]{{figures/appendices/fig_mean_dispersion_by_function.pdf}}",
            "  \\end{adjustwidth}",
            "  \\caption{Mean-versus-dispersion panels for the function--dimension instances identified in each subplot.}",
            f"  \\label{{fig:app_dispersion_{page}}}",
            "\\end{figure}",
            "\\clearpage",
            "",
        ])
    MS_APPENDIX_TEX.write_text("\n".join(tex_lines), encoding="utf-8")
    print(f"[15] wrote {MS_APPENDIX / 'fig_mean_dispersion_by_function.pdf'} "
          f"({page_count} pages, up to 9 panels/page)")
    print(f"[15] wrote {MS_APPENDIX_TEX}")


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
