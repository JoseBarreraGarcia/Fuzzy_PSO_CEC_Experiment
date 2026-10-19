#!/usr/bin/env python
"""
06_generate_paper_figures.py — publication figures for the MDPI paper.

Consumes results from scripts 00-05, 09, 10 and produces PNG + PDF figures
for the results section of the manuscript. Only data-driven figures are
generated here; fuzzy-partition schematics stay in FUZZY/1_generate_fuzzy_plots.py.

Figures produced (results/figures_all/):
    fig_cd_diagram_h1.{png,pdf}         critical-difference diagram (H1)
    fig_rule_class_heatmap.{png,pdf}    mean rank (n,R) x problem class (H2)
    fig_pareto_s1_s2.{png,pdf}          S1 vs S2 rank Pareto front (H5)
    fig_scaling_curves.{png,pdf}        gap vs dim curves for top-5 configs
    fig_boxplot_gap_by_n.{png,pdf}      log gap distribution by n_labels
    fig_std_R_vs_n.{png,pdf}            std across R per n (H3)
    fig_h4_wilcoxon_bars.{png,pdf}      wins/ties/losses top-10 configs (H4)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _naming import CLASS_SHORT, short_name

REPO_ROOT = Path(__file__).resolve().parents[3]
RESULTS = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results"
OUT_DIR = RESULTS / "figures_all"

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "legend.fontsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.grid": True,
    "grid.alpha": 0.3,
})

LOG_FLOOR = 1e-12


def _save(fig: plt.Figure, stem: str) -> None:
    fig.savefig(OUT_DIR / f"{stem}.png", bbox_inches="tight")
    fig.savefig(OUT_DIR / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"[06] wrote {stem}.png/.pdf")


def cd_diagram(mean_ranks: pd.DataFrame, cd: float, alpha: float, out_stem: str) -> None:
    """Simple critical-difference diagram: horizontal ranks + CD bar."""
    df = mean_ranks.sort_values("mean_rank").reset_index(drop=True)
    k = len(df)
    fig, ax = plt.subplots(figsize=(9.5, 0.32 * k + 1.5))
    y = np.arange(k)[::-1]
    ax.hlines(y, xmin=0, xmax=df["mean_rank"], color="tab:blue", alpha=0.5)
    ax.plot(df["mean_rank"], y, "o", color="tab:blue")
    ax.set_yticks(y)
    labels = [short_name(s) for s in df["mh_raw"]]
    ax.set_yticklabels(labels)
    # The baseline is the reference of the whole comparison: make it findable at a glance.
    for tick, name in zip(ax.get_yticklabels(), labels):
        if name == "PSO":
            tick.set_fontweight("bold")
    ax.set_xlabel("Mean Friedman rank (lower is better)")
    ax.set_title(f"Critical difference diagram over {k} configurations (CD={cd:.2f}, alpha={alpha})")
    best = df["mean_rank"].min()
    ax.axvspan(best, best + cd, alpha=0.15, color="green", label=f"within CD of top")
    ax.legend(loc="lower right")
    fig.tight_layout()
    _save(fig, out_stem)


def rule_class_heatmap(per_class: pd.DataFrame, out_stem: str) -> None:
    """Heatmap of mean gap_median for PSO_FCS across (n,R) x problem class."""
    fcs = per_class[per_class["mh_family"] == "PSO_FCS"].copy()
    fcs["config"] = "FCS-" + fcs["n_labels"].astype(int).astype(str) + "-" + fcs["rule_set"].astype(str)
    piv = fcs.pivot_table(index="config", columns="problem_class", values="gap_median")
    piv = piv.loc[sorted(piv.index, key=lambda s: (int(s.split("-")[1]), s.split("-")[2]))]
    piv = piv.rename(columns=CLASS_SHORT)

    fig, ax = plt.subplots(figsize=(5.5, 0.25 * len(piv) + 1.5))
    log = np.log10(np.maximum(piv.to_numpy(), LOG_FLOOR) + LOG_FLOOR)
    im = ax.imshow(log, aspect="auto", cmap="RdYlGn_r")
    ax.set_xticks(range(len(piv.columns)))
    ax.set_xticklabels(piv.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(piv)))
    ax.set_yticklabels(piv.index, fontsize=7)
    cbar = fig.colorbar(im, ax=ax, shrink=0.75)
    cbar.set_label("log10(median normalized gap)")
    ax.set_title("Median gap across (granularity, rule pattern) and landscape class")
    fig.tight_layout()
    _save(fig, out_stem)


def pareto_s1_s2(pareto: pd.DataFrame, all_pts: pd.DataFrame, out_stem: str) -> None:
    fig, ax = plt.subplots(figsize=(5.8, 4.6))
    ax.scatter(all_pts["S1"], all_pts["S2"], alpha=0.6, color="grey", label="all configurations")
    ax.plot(pareto["S1"], pareto["S2"], "o-", color="tab:red", label="non-dominated front")
    for _, r in pareto.iterrows():
        ax.annotate(short_name(r["mh_raw"]),
                    (r["S1"], r["S2"]), fontsize=7, xytext=(4, 4),
                    textcoords="offset points")
    baseline = all_pts[all_pts["mh_raw"] == "PSO"]
    if len(baseline):
        ax.scatter(baseline["S1"], baseline["S2"], marker="*", s=160, color="black",
                   zorder=5, label="PSO baseline")
    ax.set_xlabel("Rank on S1: scalable functions (F1-F13)")
    ax.set_ylabel("Rank on S2: fixed-dimensional functions (F14-F23)")
    ax.set_title("Configuration rank on the scalable vs fixed-dimensional subsets")
    ax.legend(loc="lower left", fontsize=8)
    ax.invert_xaxis()
    ax.invert_yaxis()
    fig.tight_layout()
    _save(fig, out_stem)


def scaling_curves(long: pd.DataFrame, top_configs: list[str], out_stem: str) -> None:
    fig, ax = plt.subplots(figsize=(6, 4.5))
    cmap = plt.get_cmap("tab10")
    for i, cfg in enumerate(top_configs):
        sub = long[long["mh_raw"] == cfg]
        med_by_dim = sub.groupby("dim")["gap_median"].median().sort_index()
        ax.plot(med_by_dim.index, np.maximum(med_by_dim.values, LOG_FLOOR),
                marker="o", label=short_name(cfg),
                color=cmap(i % 10))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Dimension")
    ax.set_ylabel("Median normalized gap over S1 (F1-F13)")
    ax.set_title("Scaling of median gap with dimension")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    _save(fig, out_stem)


def boxplot_gap_by_n(meta: pd.DataFrame, out_stem: str) -> None:
    fcs = meta[meta["mh_family"] == "PSO_FCS"].copy()
    fcs["y"] = np.log10(np.maximum(fcs["gap_final"], LOG_FLOOR) + LOG_FLOOR)
    groups = [fcs[fcs["n_labels"] == n]["y"].to_numpy() for n in [3, 5, 7, 9]]
    fig, ax = plt.subplots(figsize=(5.5, 4))
    ax.boxplot(groups, tick_labels=["n=3", "n=5", "n=7", "n=9"], showfliers=False)
    ax.set_ylabel("log10(normalized gap + 1e-12)")
    ax.set_title("Gap distribution vs linguistic granularity (fuzzy configurations)")
    fig.tight_layout()
    _save(fig, out_stem)


def std_R_vs_n(std_df: pd.DataFrame, out_stem: str) -> None:
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.plot(std_df["n_labels"], std_df["std_across_R"], marker="o", color="tab:blue")
    ax.set_xlabel("Number of linguistic labels $n$")
    ax.set_ylabel("Std of median normalized gap across R1..R8")
    ax.set_title("Dispersion between rule patterns on the raw gap scale")
    ax.set_xticks([3, 5, 7, 9])
    fig.tight_layout()
    _save(fig, out_stem)


def h4_wilcoxon_bars(csummary: pd.DataFrame, top_n: int, out_stem: str) -> None:
    top = csummary.head(top_n).iloc[::-1]
    labels = [short_name(s) for s in top["mh_raw"]]
    y = np.arange(len(top))
    fig, ax = plt.subplots(figsize=(6.5, 0.36 * len(top) + 1))
    ax.barh(y, top["raw_wins"], color="tab:green", label="wins")
    ax.barh(y, top["raw_ties"], left=top["raw_wins"], color="tab:grey", label="ties")
    ax.barh(y, top["raw_losses"], left=top["raw_wins"] + top["raw_ties"],
            color="tab:red", label="losses")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Instances (of 62)")
    ax.set_title(f"Paired Wilcoxon outcome of the top-{top_n} configurations against PSO (alpha=0.05)")
    ax.legend(loc="lower right")
    fig.tight_layout()
    _save(fig, out_stem)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-scaling", type=int, default=5)
    parser.add_argument("--top-wilcoxon", type=int, default=10)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[06] output dir : {OUT_DIR}")

    # H1 CD diagram.
    mean_ranks = pd.read_csv(RESULTS / "tests" / "h1_friedman_nemenyi" / "mean_rank_per_config.csv")
    cd_info = json.loads((RESULTS / "tests" / "h1_friedman_nemenyi" / "critical_difference.json").read_text(encoding="utf-8"))
    cd_diagram(mean_ranks, cd_info["CD"], 0.05, "fig_cd_diagram_h1")

    # H2 heatmap: reuse pareto script's per-class file if present; otherwise recompute from l2.
    l2 = pd.read_parquet(RESULTS / "level2_aggregated" / "stats_by_config_instance.parquet")
    class_map_path = RESULTS / "tests" / "h5_pareto_problemtype" / "problem_class_assignment.csv"
    class_map = pd.read_csv(class_map_path)
    per_class = l2.merge(class_map[["function", "problem_class"]], on="function")
    per_class = per_class.groupby(["mh_raw", "mh_family", "n_labels", "rule_set", "problem_class"],
                                  dropna=False)["gap_median"].mean().reset_index()
    rule_class_heatmap(per_class, "fig_rule_class_heatmap")

    # H5 Pareto.
    pareto = pd.read_csv(RESULTS / "tests" / "h5_pareto_problemtype" / "pareto_front.csv")
    ranks_sub = pd.read_csv(RESULTS / "tests" / "h5_pareto_problemtype" / "ranking_by_subgroup.csv")
    all_pts = ranks_sub.pivot(index="mh_raw", columns="subgroup", values="rank").reset_index().dropna()
    pareto_s1_s2(pareto, all_pts, "fig_pareto_s1_s2")

    # Scaling curves for top-5 by mean rank.
    long = pd.read_parquet(RESULTS / "tests" / "scaling_curves" / "scaling_long.parquet")
    top_scaling = mean_ranks.head(args.top_scaling)["mh_raw"].tolist()
    scaling_curves(long, top_scaling, "fig_scaling_curves")

    # Boxplot by n.
    meta = pd.read_parquet(RESULTS / "level1_raw" / "experiments_meta.parquet")
    boxplot_gap_by_n(meta, "fig_boxplot_gap_by_n")

    # std(R) vs n.
    std_df = pd.read_csv(RESULTS / "tests" / "h3_factorial_anova" / "std_across_R_vs_n.csv")
    std_R_vs_n(std_df, "fig_std_R_vs_n")

    # H4 Wilcoxon bars.
    csummary = pd.read_csv(RESULTS / "tests" / "h4_wilcoxon_vs_baseline" / "wilcoxon_config_summary.csv")
    h4_wilcoxon_bars(csummary, args.top_wilcoxon, "fig_h4_wilcoxon_bars")

    print("[06] === DONE ===")
    for p in sorted(OUT_DIR.glob("*.png")):
        print(f"    {p.name}  {p.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
