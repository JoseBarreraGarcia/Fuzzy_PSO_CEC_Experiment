#!/usr/bin/env python
"""
13_analyze_granularity.py — Section 5.5 (effect of linguistic granularity).

Granularity is analysed jointly with the rule-base pattern rather than as an
isolated factor: the question is whether adding labels improves, degrades or
merely stabilizes each rule family, and whether it ever reorders them.

Inputs:
    results/tests/h1_friedman_nemenyi/mean_rank_per_config.csv
    results/level2_aggregated/stats_by_n_R.csv
    results/level1_raw/experiments_meta.csv
    results/tests/h3_factorial_anova/summary.json
    config/fuzzy_partitions.json

Outputs:
    results/level3_rankings/granularity_by_rule.csv
    results/level3_rankings/granularity_aggregate.csv
    manuscript/tables/tab_granularity_by_rule.tex
    manuscript/figures/fig_granularity_effect.{png,pdf}
    results/figures_all/fig_granularity_effect.{png,pdf}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import kendalltau

sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO_ROOT = Path(__file__).resolve().parents[3]
MDPI = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI"
MEAN_RANK = MDPI / "results" / "tests" / "h1_friedman_nemenyi" / "mean_rank_per_config.csv"
STATS_N_R = MDPI / "results" / "level2_aggregated" / "stats_by_n_R.csv"
META = MDPI / "results" / "level1_raw" / "experiments_meta.csv"
H3 = MDPI / "results" / "tests" / "h3_factorial_anova" / "summary.json"
PARTITIONS = REPO_ROOT / "config" / "fuzzy_partitions.json"
OUT_L3 = MDPI / "results" / "level3_rankings"
OUT_FIG = MDPI / "results" / "figures_all"
MS_TABLES = MDPI / "manuscript" / "tables"
MS_FIGURES = MDPI / "manuscript" / "figures"

GRANULARITIES = [3, 5, 7, 9]
RULES = [f"R{i}" for i in range(1, 9)]
STABLE_SPREAD = 2.5  # rank units below which the rule is insensitive to n
LOG_FLOOR = 1e-12


def rank_matrix() -> pd.DataFrame:
    mr = pd.read_csv(MEAN_RANK)
    mr = mr[mr["mh_raw"] != "PSO"].copy()
    mr["n"] = mr["mh_raw"].str.extract(r"G(\d+)").astype(int)
    mr["rule_set"] = mr["mh_raw"].str.extract(r":(R\d+):")
    return mr.pivot(index="rule_set", columns="n", values="mean_rank").loc[RULES, GRANULARITIES]


def trend_label(values: np.ndarray) -> str:
    spread = values.max() - values.min()
    monotone_worse = bool(np.all(np.diff(values) > 0))
    worse_at_end = bool(values[-1] > values[0])
    if spread < STABLE_SPREAD:
        return "stable"
    if monotone_worse:
        return "degradation"
    if worse_at_end:
        return "degrad. (non-monot.)"
    return "non-monotonic"


def build_by_rule(ranks: pd.DataFrame, patterns: dict) -> pd.DataFrame:
    rows = []
    for rule in RULES:
        values = ranks.loc[rule].to_numpy(dtype=float)
        rows.append({
            "rule_set": rule,
            "progress": patterns[rule]["prog"],
            "diversity": patterns[rule]["div"],
            **{f"rank_n{n}": float(v) for n, v in zip(GRANULARITIES, values)},
            "best_n": int(GRANULARITIES[int(np.argmin(values))]),
            "spread": float(values.max() - values.min()),
            "trend": trend_label(values),
        })
    return pd.DataFrame(rows)


def build_aggregate(ranks: pd.DataFrame, meta: pd.DataFrame, stats_n_r: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for n in GRANULARITIES:
        col = ranks[n].to_numpy(dtype=float)
        sub = meta[meta["n_labels"] == n]
        y = np.log10(np.maximum(sub["gap_final"].to_numpy(dtype=float), LOG_FLOOR) + LOG_FLOOR)
        gaps = stats_n_r[stats_n_r["n_labels"] == n]["gap_median"].to_numpy(dtype=float)
        rows.append({
            "n_labels": n,
            "mean_rank_over_rules": float(col.mean()),
            "best_rule_rank": float(col.min()),
            "std_rank_across_rules": float(col.std(ddof=1)),
            "median_log_gap": float(np.median(y)),
            "iqr_log_gap": float(np.percentile(y, 75) - np.percentile(y, 25)),
            "std_gap_median_across_rules": float(gaps.std(ddof=1)),
        })
    return pd.DataFrame(rows)


def emit_table(by_rule: pd.DataFrame, path: Path) -> None:
    lines = [
        "% Generado por code/13_analyze_granularity.py. No editar a mano.",
        "\\begin{table}[H]",
        "\\centering",
        "\\small",
        "\\caption{Mean Friedman rank of every rule-base pattern at each granularity (lower is "
        "better; the ranking is computed over the 33 configurations and 62 instances). "
        "\\emph{Best $n$} is the granularity that minimizes the rank of that pattern and "
        "\\emph{spread} is the difference between its worst and best rank across granularities. "
        "The \\emph{stable} label uses a descriptive spread threshold of "
        f"{STABLE_SPREAD:.1f} rank units; it is not an equivalence test. Patterns are labelled "
        "\\emph{degradation} when rank grows monotonically with $n$ and \\emph{non-monotonic} otherwise.}",
        "\\label{tab:granularity_by_rule}",
        "\\setlength{\\tabcolsep}{3.5pt}",
        "\\begin{tabular}{lcccccccl}",
        "\\toprule",
        "\\textbf{Pattern} & \\textbf{Progress} & \\boldmath$n=3$ & \\boldmath$n=5$ & "
        "\\boldmath$n=7$ & \\boldmath$n=9$ & \\textbf{Best} \\boldmath$n$ & "
        "\\textbf{Spread} & \\textbf{Trend} \\\\",
        "\\midrule",
    ]
    progress_short = {"decreasing": "dec.", "agnostic": "neutral", "increasing": "incr."}
    for _, r in by_rule.sort_values("rank_n3").iterrows():
        cells = " & ".join(f"{r[f'rank_n{n}']:.1f}" for n in GRANULARITIES)
        lines.append(
            f"{r['rule_set']} & {progress_short[r['progress']]} & {cells} & "
            f"{r['best_n']} & {r['spread']:.1f} & {r['trend']} \\\\"
        )
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[13] wrote {path.name}")


def emit_figure(ranks: pd.DataFrame, aggregate: pd.DataFrame, patterns: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4))

    ax = axes[0]
    styles = {"decreasing": ("tab:green", "-", "o"),
              "agnostic": ("tab:orange", "--", "s"),
              "increasing": ("tab:red", ":", "^")}
    end_values = ranks[GRANULARITIES[-1]].sort_values()
    # Nudge labels apart when two patterns end within less than one rank unit.
    offsets, previous = {}, None
    for rule, value in end_values.items():
        shift = 5 if previous is not None and value - previous < 1.0 else -2
        offsets[rule] = shift
        previous = value
    for rule in RULES:
        color, ls, marker = styles[patterns[rule]["prog"]]
        ax.plot(GRANULARITIES, ranks.loc[rule], color=color, linestyle=ls, marker=marker,
                markersize=4, linewidth=1.4)
        ax.annotate(rule, (GRANULARITIES[-1], ranks.loc[rule, 9]), fontsize=7,
                    xytext=(4, offsets[rule]), textcoords="offset points", color=color)
    ax.set_xticks(GRANULARITIES)
    ax.set_xlim(2.4, 10.2)
    ax.invert_yaxis()
    ax.set_xlabel("Number of linguistic labels $n$")
    ax.set_ylabel("Mean Friedman rank (better upwards)")
    ax.grid(alpha=0.3)

    ax = axes[1]
    ax.plot(aggregate["n_labels"], aggregate["std_rank_across_rules"],
            marker="o", color="tab:blue")
    ax.set_xticks(GRANULARITIES)
    ax.set_xlabel("Number of linguistic labels $n$")
    ax.set_ylabel("Std of mean rank across R1--R8")
    ax.grid(alpha=0.3)

    handles = [plt.Line2D([], [], color=c, linestyle=l, marker=m, markersize=4, label=lab)
               for lab, (c, l, m) in
               (("progress decreasing", styles["decreasing"]),
                ("progress neutral", styles["agnostic"]),
                ("progress increasing", styles["increasing"]))]
    fig.legend(handles=handles, fontsize=8, ncol=3, loc="lower center",
               bbox_to_anchor=(0.5, -0.04), frameon=False)

    fig.tight_layout()
    for directory in (MS_FIGURES, OUT_FIG):
        directory.mkdir(parents=True, exist_ok=True)
        for ext in ("png", "pdf"):
            fig.savefig(directory / f"fig_granularity_effect.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("[13] wrote fig_granularity_effect.{png,pdf}")


def main() -> int:
    for path in (MEAN_RANK, STATS_N_R, META, H3, PARTITIONS):
        if not path.exists():
            raise FileNotFoundError(f"missing input: {path}")

    patterns = json.loads(PARTITIONS.read_text(encoding="utf-8"))["rule_patterns"]
    ranks = rank_matrix()
    meta = pd.read_csv(META, usecols=["mh_family", "n_labels", "gap_final"])
    meta = meta[meta["mh_family"] == "PSO_FCS"].copy()
    meta["n_labels"] = meta["n_labels"].astype(int)
    stats_n_r = pd.read_csv(STATS_N_R)

    by_rule = build_by_rule(ranks, patterns)
    aggregate = build_aggregate(ranks, meta, stats_n_r)

    OUT_L3.mkdir(parents=True, exist_ok=True)
    MS_TABLES.mkdir(parents=True, exist_ok=True)
    by_rule.to_csv(OUT_L3 / "granularity_by_rule.csv", index=False)
    aggregate.to_csv(OUT_L3 / "granularity_aggregate.csv", index=False)

    emit_table(by_rule, MS_TABLES / "tab_granularity_by_rule.tex")
    emit_figure(ranks, aggregate, patterns)

    # Does granularity reorder the rule patterns, or only shift them?
    print("\n[13] Kendall tau between rule orderings at different granularities:")
    for i, a in enumerate(GRANULARITIES):
        for b in GRANULARITIES[i + 1:]:
            tau, p = kendalltau(ranks[a], ranks[b])
            print(f"     n={a} vs n={b}: tau={tau:.3f} (p={p:.4f})")

    print("\n[13] top-3 patterns at each granularity:")
    for n in GRANULARITIES:
        order = ranks[n].sort_values().index.tolist()[:3]
        print(f"     n={n}: {order}")

    decreasing = [r for r in RULES if patterns[r]["prog"] == "decreasing"]
    print("\n[13] is the progress-decreasing family the top-3 at every n? ",
          all(set(ranks[n].sort_values().index[:3]) == set(decreasing) for n in GRANULARITIES))

    h3 = json.loads(H3.read_text(encoding="utf-8"))
    print("\n[13] partial eta^2:", h3["partial_eta_squared"])
    print("[13] std of median gap across R is decreasing with n:",
          h3["h3_std_R_decreasing_with_n"])
    print("\n[13] aggregate by granularity:")
    print(aggregate.round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
