#!/usr/bin/env python
"""
12_analyze_rule_structure.py — Section 5.4 (effect of the rule-base structure).

Summarizes the rule bank by its nominal consequent axes (progress direction and
diversity reaction) and compares implemented rule-pattern pairs under the same
two-input Mamdani inference mechanism.

Two families of paired comparisons are produced and must not be conflated (D20):

  * mirror pairs      both semantic axes are inverted simultaneously
                      (R1,R2), (R3,R4), (R5,R8), (R6,R7)
    * single-axis pairs one nominal consequent axis changes while the other is
                                            held fixed; these are rule-pattern contrasts, not
                                            isolated or independent effective-input effects

Comparisons are paired by run_id at equal granularity and instance, mirroring the
protocol of script 10 against the baseline.

Inputs:
    results/level1_raw/experiments_meta.csv
    results/tests/h1_friedman_nemenyi/mean_rank_per_config.csv
    config/fuzzy_partitions.json

Outputs:
    results/level3_rankings/rule_semantic_grid.csv
    results/level3_rankings/rule_pair_per_instance.csv
    results/level3_rankings/rule_pair_summary.csv
    manuscript/tables/tab_rule_semantic_grid.tex
    manuscript/tables/tab_rule_pairs.tex
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _naming import CLASS_SHORT

REPO_ROOT = Path(__file__).resolve().parents[3]
MDPI = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI"
META = MDPI / "results" / "level1_raw" / "experiments_meta.csv"
MEAN_RANK = MDPI / "results" / "tests" / "h1_friedman_nemenyi" / "mean_rank_per_config.csv"
PARTITIONS = REPO_ROOT / "config" / "fuzzy_partitions.json"
OUT_L3 = MDPI / "results" / "level3_rankings"
MS_TABLES = MDPI / "manuscript" / "tables"

ALPHA = 0.05
GRANULARITIES = [3, 5, 7, 9]

MIRROR_PAIRS = [("R1", "R2"), ("R3", "R4"), ("R5", "R8"), ("R6", "R7")]
SINGLE_AXIS_PAIRS = [("R5", "R7"), ("R6", "R8"), ("R5", "R6"), ("R7", "R8")]

PROGRESS_ORDER = ["decreasing", "agnostic", "increasing"]
DIVERSITY_ORDER = ["following", "agnostic", "compensating"]
PROGRESS_LABEL = {"decreasing": "Progress decreasing",
                  "agnostic": "Progress neutral",
                  "increasing": "Progress increasing"}
DIVERSITY_LABEL = {"following": "Diversity-following",
                   "agnostic": "Diversity-neutral",
                   "compensating": "Diversity-compensating"}


def landscape_class(function: str) -> str:
    idx = int(function[1:])
    if idx <= 7:
        return "unimodal"
    if idx <= 13:
        return "multimodal"
    return "composed"


def a12(x: np.ndarray, y: np.ndarray) -> float:
    """P(x < y) + 0.5 P(x = y). Fitness is minimized, so a12 > 0.5 favours x."""
    xm, ym = np.meshgrid(x, y, indexing="ij")
    return float(((xm < ym).sum() + 0.5 * (xm == ym).sum()) / (x.size * y.size))


def load_patterns() -> dict:
    return json.loads(PARTITIONS.read_text(encoding="utf-8"))["rule_patterns"]


def build_semantic_grid(patterns: dict) -> pd.DataFrame:
    mr = pd.read_csv(MEAN_RANK)
    mr = mr[mr["mh_raw"] != "PSO"].copy()
    mr["rule_set"] = mr["mh_raw"].str.extract(r":(R\d+):")
    by_rule = mr.groupby("rule_set")["mean_rank"].agg(["mean", "min", "max"])

    rows = []
    for rule, pat in patterns.items():
        if not rule.startswith("R"):
            continue
        rows.append({
            "rule_set": rule,
            "progress": pat["prog"],
            "diversity": pat["div"],
            "description": pat["_desc"],
            "mean_rank": float(by_rule.loc[rule, "mean"]),
            "best_rank": float(by_rule.loc[rule, "min"]),
            "worst_rank": float(by_rule.loc[rule, "max"]),
        })
    return pd.DataFrame(rows).sort_values("mean_rank").reset_index(drop=True)


def compare_pairs(meta: pd.DataFrame, pairs: list[tuple[str, str]], kind: str) -> pd.DataFrame:
    rows = []
    for ra, rb in pairs:
        for n in GRANULARITIES:
            a = meta[(meta["rule_set"] == ra) & (meta["n_labels"] == n)]
            b = meta[(meta["rule_set"] == rb) & (meta["n_labels"] == n)]
            for instance, ga in a.groupby("instance"):
                gb = b[b["instance"] == instance]
                if len(gb) != len(ga):
                    continue
                x = ga.sort_values("run_id")["fitness_best"].to_numpy()
                y = gb.sort_values("run_id")["fitness_best"].to_numpy()
                effect = a12(x, y)
                if np.allclose(x, y):
                    p_value, direction = 1.0, "tie"
                else:
                    try:
                        _, p_value = wilcoxon(x, y, alternative="two-sided", zero_method="wilcox")
                    except ValueError:
                        p_value = 1.0
                    direction = ("tie" if p_value >= ALPHA
                                 else (ra if effect > 0.5 else rb))
                rows.append({
                    "kind": kind,
                    "pair": f"{ra} vs {rb}",
                    "rule_a": ra, "rule_b": rb, "n_labels": n,
                    "instance": instance,
                    "function": ga["function"].iloc[0],
                    "landscape_class": landscape_class(ga["function"].iloc[0]),
                    "a12": effect, "p_value": p_value, "winner": direction,
                })
    return pd.DataFrame(rows)


def axis_inverted(patterns: dict, ra: str, rb: str) -> str:
    pa, pb = patterns[ra], patterns[rb]
    changed = []
    if pa["prog"] != pb["prog"]:
        changed.append("progress direction")
    if pa["div"] != pb["div"]:
        changed.append("diversity reaction")
    return " + ".join(changed)


def summarize(detail: pd.DataFrame, patterns: dict) -> pd.DataFrame:
    rows = []
    for (kind, pair), block in detail.groupby(["kind", "pair"], sort=False):
        ra, rb = block["rule_a"].iloc[0], block["rule_b"].iloc[0]
        wins_a = int((block["winner"] == ra).sum())
        wins_b = int((block["winner"] == rb).sum())
        ties = int((block["winner"] == "tie").sum())
        dominant = ra if wins_a > wins_b else (rb if wins_b > wins_a else "--")
        # Where the dominant side is strongest, measured by significant-win rate per class.
        rates = {}
        for cls, cblock in block.groupby("landscape_class"):
            rates[cls] = float((cblock["winner"] == dominant).mean()) if dominant != "--" else 0.0
        best_class = max(rates, key=rates.get) if rates else "--"
        rows.append({
            "kind": kind,
            "pair": pair,
            "axis_inverted": axis_inverted(patterns, ra, rb),
            "n_comparisons": len(block),
            "wins_a": wins_a, "wins_b": wins_b, "ties": ties,
            "dominant": dominant,
            "a12_median": float(block["a12"].median()),
            "best_class": best_class,
            "best_class_rate": float(rates.get(best_class, np.nan)),
        })
    return pd.DataFrame(rows)


def emit_grid_table(grid: pd.DataFrame, path: Path) -> None:
    lookup = {(r["progress"], r["diversity"]): r for _, r in grid.iterrows()}
    lines = [
        "% Generado por code/12_analyze_rule_structure.py. No editar a mano.",
        "\\begin{table}[H]",
        "\\centering",
        "\\small",
        "\\caption{Semantic layout of the rule bank. Rows give the direction of the progress effect "
        "and columns the reaction to diversity; each cell holds the rule-base pattern generated by "
        "that combination and, in parentheses, its mean Friedman rank averaged over the four "
        "granularities (lower is better). The centre cell is empty because a pattern that ignores "
        "both inputs produces a constant inertia weight and is not part of the bank.}",
        "\\label{tab:rule_semantic_grid}",
        "\\begin{tabular}{lccc}",
        "\\toprule",
        " & \\textbf{Diversity-following} & \\textbf{Diversity-neutral} & "
        "\\textbf{Diversity-compensating} \\\\",
        "\\midrule",
    ]
    for prog in PROGRESS_ORDER:
        cells = []
        for div in DIVERSITY_ORDER:
            entry = lookup.get((prog, div))
            cells.append("--" if entry is None
                         else f"{entry['rule_set']} ({entry['mean_rank']:.1f})")
        lines.append(f"\\textbf{{{PROGRESS_LABEL[prog]}}} & " + " & ".join(cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[12] wrote {path.name}")


def emit_pairs_table(summary: pd.DataFrame, path: Path) -> None:
    lines = [
        "% Generado por code/12_analyze_rule_structure.py. No editar a mano.",
        "\\begin{table}[H]",
        "\\centering",
        "\\small",
        "\\caption{Paired comparison of rule-base patterns at equal granularity and instance "
        "(248 comparisons per pair: 62 instances $\\times$ 4 granularities, each paired by run). "
        "Mirror pairs invert every non-neutral axis of the pattern and therefore reverse its whole "
        "semantics, which by Proposition~\\ref{prop:mirror} reflects the control surface about the "
        "midpoint of $[w_{\\min},w_{\\max}]$; single-axis pairs change one axis while the other stays "
        "fixed at a non-neutral value, and isolate its marginal effect. "
        "Wins are significant outcomes of a paired Wilcoxon test at $\\alpha=0.05$; the remaining "
        "comparisons are ties. $A_{12}$ is reported for the first pattern of each pair, so "
        "$A_{12}>0.5$ favours it. \\emph{Strongest in} names the landscape class where the dominant "
        "pattern wins the largest share of comparisons.}",
        "\\label{tab:rule_pairs}",
        "\\setlength{\\tabcolsep}{4pt}",
        "\\begin{tabularx}{\\textwidth}{l>{\\raggedright\\arraybackslash}X ccccl}",
        "\\toprule",
        "\\textbf{Pair} & \\textbf{Axis inverted} & \\textbf{Wins} & \\textbf{Ties} & "
        "\\textbf{Dominant} & \\boldmath$A_{12}$ & \\textbf{Strongest in} \\\\",
        "\\midrule",
    ]
    for kind, label in (("mirror", "Mirror pairs (all non-neutral axes inverted)"),
                        ("single-axis", "Single-axis pairs (one nominal consequent axis changed)")):
        block = summary[summary["kind"] == kind]
        lines.append(f"\\multicolumn{{7}}{{l}}{{\\emph{{{label}}}}} \\\\")
        for _, r in block.iterrows():
            ra, rb = r["pair"].split(" vs ")
            lines.append(
                f"{ra} vs {rb} & {r['axis_inverted']} & "
                f"{r['wins_a']}/{r['wins_b']} & {r['ties']} & "
                f"\\textbf{{{r['dominant']}}} & {r['a12_median']:.2f} & "
                f"{CLASS_SHORT.get(r['best_class'], r['best_class'])} \\\\"
            )
        if kind == "mirror":
            lines.append("\\midrule")
    lines += [
        "\\bottomrule",
        "\\end{tabularx}",
        "\\noindent\\footnotesize",
        "The \\emph{Wins} column reports significant wins of the first pattern over significant wins "
        "of the second.",
        "\\end{table}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[12] wrote {path.name}")


def emit_axes_table(grid: pd.DataFrame, path: Path) -> None:
    """Mapping used by Section 3.4; must stay identical to the grid of Section 5.4."""
    progress_label = {"decreasing": "decreasing", "agnostic": "neutral", "increasing": "increasing"}
    diversity_label = {"following": "following", "agnostic": "neutral", "compensating": "compensating"}
    lines = [
        "% Generado por code/12_analyze_rule_structure.py. No editar a mano.",
        "\\begin{table}[H]",
        "\\centering",
        "\\small",
        "\\caption{The eight rule-base patterns as combinations of the two semantic axes. "
        "$e_{\\mathrm{prog}}$ and $e_{\\mathrm{div}}$ are the ordinal effects of Equation~(\\ref{eq:axes}); "
        "a neutral axis contributes zero. The combination with both axes neutral is excluded because "
        "it yields a constant inertia weight.}",
        "\\label{tab:rule_axes}",
        "\\begin{tabular}{lll}",
        "\\toprule",
        "\\textbf{Pattern} & \\textbf{Progress direction} & \\textbf{Diversity reaction} \\\\",
        "\\midrule",
    ]
    for rule in sorted(grid["rule_set"], key=lambda r: int(r[1:])):
        row = grid[grid["rule_set"] == rule].iloc[0]
        lines.append(f"{rule} & {progress_label[row['progress']]} & "
                     f"{diversity_label[row['diversity']]} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[12] wrote {path.name}")


def main() -> int:
    for path in (META, MEAN_RANK, PARTITIONS):
        if not path.exists():
            raise FileNotFoundError(f"missing input: {path}")

    patterns = load_patterns()
    grid = build_semantic_grid(patterns)

    meta = pd.read_csv(META, usecols=["mh_family", "n_labels", "rule_set", "function", "dim",
                                      "run_id", "fitness_best"])
    meta = meta[meta["mh_family"] == "PSO_FCS"].copy()
    meta["n_labels"] = meta["n_labels"].astype(int)
    meta["instance"] = meta["function"] + "_D" + meta["dim"].astype(int).astype(str)

    detail = pd.concat([
        compare_pairs(meta, MIRROR_PAIRS, "mirror"),
        compare_pairs(meta, SINGLE_AXIS_PAIRS, "single-axis"),
    ], ignore_index=True)
    summary = summarize(detail, patterns)

    OUT_L3.mkdir(parents=True, exist_ok=True)
    MS_TABLES.mkdir(parents=True, exist_ok=True)
    grid.to_csv(OUT_L3 / "rule_semantic_grid.csv", index=False)
    detail.to_csv(OUT_L3 / "rule_pair_per_instance.csv", index=False)
    summary.to_csv(OUT_L3 / "rule_pair_summary.csv", index=False)
    print(f"[12] wrote rule_semantic_grid ({len(grid)} rules), "
          f"rule_pair_per_instance ({len(detail)} comparisons), rule_pair_summary")

    emit_grid_table(grid, MS_TABLES / "tab_rule_semantic_grid.tex")
    emit_pairs_table(summary, MS_TABLES / "tab_rule_pairs.tex")
    emit_axes_table(grid, MS_TABLES / "tab_rule_axes.tex")

    print("\n[12] mean Friedman rank by rule pattern (averaged over n):")
    print(grid[["rule_set", "description", "mean_rank", "best_rank", "worst_rank"]].to_string(index=False))
    print("\n[12] pair summary:")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
