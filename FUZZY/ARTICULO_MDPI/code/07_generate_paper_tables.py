#!/usr/bin/env python
"""
07_generate_paper_tables.py — LaTeX tables for the MDPI paper.

Produces booktabs-style .tex tables from the results of scripts 00-05, 09, 10.
Every table is also written as .csv for inspection.

Outputs (results/tables_all/):
    tab_top_configs.{tex,csv}          top-10 configs by mean Friedman rank
    tab_h4_wilcoxon.{tex,csv}          wins/ties/losses vs PSO baseline
    tab_kendall_class.{tex,csv}        Kendall tau between problem classes
    tab_scaling_slopes.{tex,csv}       top/bottom scaling slopes
    tab_hypothesis_summary.{tex,csv}   H1-H5 verdicts
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
RESULTS = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results"
OUT_DIR = RESULTS / "tables_all"


_LATEX_ESC = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    "<": r"\textless{}", ">": r"\textgreater{}",
}


def _tex_escape(s: str) -> str:
    out = []
    for ch in s:
        out.append(_LATEX_ESC.get(ch, ch))
    return "".join(out)


def _fmt(v, float_fmt: str) -> str:
    if isinstance(v, float):
        if pd.isna(v):
            return "--"
        return float_fmt % v
    if pd.isna(v):
        return "--"
    return _tex_escape(str(v))


def to_latex(df: pd.DataFrame, caption: str, label: str, float_fmt: str = "%.3f") -> str:
    cols = list(df.columns)
    header = " & ".join(_tex_escape(str(c)) for c in cols) + " \\\\"
    rows = []
    for _, r in df.iterrows():
        rows.append(" & ".join(_fmt(r[c], float_fmt) for c in cols) + " \\\\")
    body = (
        "\\begin{tabular}{" + "l" * len(cols) + "}\n"
        "\\toprule\n"
        f"{header}\n"
        "\\midrule\n"
        + "\n".join(rows) + "\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
    )
    return (
        "\\begin{table}[h]\n"
        f"\\centering\n\\caption{{{_tex_escape(caption)}}}\n\\label{{{label}}}\n"
        + body
        + "\\end{table}\n"
    )


def _write_pair(df: pd.DataFrame, stem: str, caption: str, label: str, float_fmt: str = "%.3f") -> None:
    df.to_csv(OUT_DIR / f"{stem}.csv", index=False)
    (OUT_DIR / f"{stem}.tex").write_text(
        to_latex(df, caption=caption, label=label, float_fmt=float_fmt), encoding="utf-8"
    )
    print(f"[07] wrote {stem}.tex / {stem}.csv  ({len(df)} rows)")


def table_top_configs() -> None:
    mr = pd.read_csv(RESULTS / "tests" / "h1_friedman_nemenyi" / "mean_rank_per_config.csv")
    df = mr.head(10).copy()
    df.columns = ["Configuration", "Mean rank"]
    _write_pair(df, "tab_top_configs",
                caption="Top-10 configurations by mean Friedman rank across 62 instances (lower is better).",
                label="tab:top_configs")


def table_h4() -> None:
    cs = pd.read_csv(RESULTS / "tests" / "h4_wilcoxon_vs_baseline" / "wilcoxon_config_summary.csv")
    cs = cs.head(10)[["mh_raw", "n_labels", "rule_set", "raw_wins", "raw_ties", "raw_losses",
                       "bonf_wins", "bonf_ties", "bonf_losses", "a12_mean"]].copy()
    cs.columns = ["Config.", "n", "R", "Wins", "Ties", "Losses", "Wins*", "Ties*", "Losses*", "A12 mean"]
    _write_pair(cs, "tab_h4_wilcoxon",
                caption="Wilcoxon signed-rank comparison of top-10 PSO_FCS configurations against classical PSO (paired by run). "
                        "Columns marked * apply Bonferroni correction over the full 32x62 grid.",
                label="tab:h4_wilcoxon",
                float_fmt="%.3f")


def table_kendall_class() -> None:
    tau = pd.read_csv(RESULTS / "tests" / "h5_pareto_problemtype" / "kendall_tau_by_class.csv", index_col=0)
    tau = tau.round(3).reset_index().rename(columns={"index": "class"})
    _write_pair(tau, "tab_kendall_class",
                caption="Kendall's tau between rankings induced by the three problem classes (higher = more agreement).",
                label="tab:kendall_class")


def table_scaling_slopes() -> None:
    slopes = pd.read_csv(RESULTS / "tests" / "scaling_curves" / "scaling_slopes_by_mh.csv")
    top = slopes.head(5).assign(status="best-scaling")
    bot = slopes.tail(5).assign(status="worst-scaling")
    df = pd.concat([top, bot])[["status", "mh_raw", "n_labels", "rule_set",
                                 "mean_slope", "median_slope", "mean_r2"]].reset_index(drop=True)
    df.columns = ["Status", "Config.", "n", "R", "Mean slope", "Median slope", "Mean R^2"]
    _write_pair(df, "tab_scaling_slopes",
                caption="Log-log slope of median gap vs dimension for the five best- and five worst-scaling configurations.",
                label="tab:scaling_slopes")


def table_hypothesis_summary() -> None:
    h1 = json.loads((RESULTS / "tests" / "h1_friedman_nemenyi" / "summary.json").read_text(encoding="utf-8"))
    h3 = json.loads((RESULTS / "tests" / "h3_factorial_anova" / "summary.json").read_text(encoding="utf-8"))
    h5 = json.loads((RESULTS / "tests" / "h5_pareto_problemtype" / "summary.json").read_text(encoding="utf-8"))
    h4 = json.loads((RESULTS / "tests" / "h4_wilcoxon_vs_baseline" / "summary.json").read_text(encoding="utf-8"))

    tau_composed_unimodal = float(h5["kendall_by_class"]["composed"]["unimodal"])
    tau_S1_S2 = float(h5["kendall_tau_S1_vs_S2"])
    friedman_p = float(h1["friedman"]["p_value"])
    interaction_p_srh = next(row["p_value"] for row in h3["srh_table"] if row["factor"] == "n_labels:rule_set")
    peta_rule = float(h3["partial_eta_squared"]["rule_set"])
    peta_n = float(h3["partial_eta_squared"]["n_labels"])

    rows = [
        {"Hypothesis": "H1", "Statement": "Granularity has diminishing returns",
         "Key statistic": f"Friedman chi2 p={friedman_p:.2e}",
         "Verdict": "H0 rejected globally; within R1 the effect of n is < CD (not sig.)"},
        {"Hypothesis": "H2", "Statement": "Best R depends on problem class",
         "Key statistic": f"tau(composed, unimodal)={tau_composed_unimodal:.2f}",
         "Verdict": "supported"},
        {"Hypothesis": "H3", "Statement": "Sensitivity to R decreases with n",
         "Key statistic": f"n x R SRH p={interaction_p_srh:.2f}; peta^2(R)={peta_rule:.3f}, peta^2(n)={peta_n:.4f}",
         "Verdict": "rejected"},
        {"Hypothesis": "H4", "Statement": "PSO_FCS beats PSO on >=50% of instances",
         "Key statistic": "best config: 27 wins / 33 ties / 2 losses (of 62)",
         "Verdict": f"rejected under strict >=50% criterion; supported = {h4['H4_supported_raw']}"},
        {"Hypothesis": "H5", "Statement": "No static (n*, R*) dominates both S1 and S2",
         "Key statistic": f"tau(S1, S2)={tau_S1_S2:.2f}; argmin(S1)={h5['best_by_subgroup']['S1']['mh_raw']}, argmin(S2)={h5['best_by_subgroup']['S2']['mh_raw']}",
         "Verdict": "supported"},
    ]
    df = pd.DataFrame(rows)
    _write_pair(df, "tab_hypothesis_summary",
                caption="Summary of hypotheses H1--H5 with their governing statistic and verdict.",
                label="tab:hypothesis_summary")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[07] output dir : {OUT_DIR}")
    table_top_configs()
    table_h4()
    table_kendall_class()
    table_scaling_slopes()
    table_hypothesis_summary()
    print("[07] === DONE ===")
    for p in sorted(OUT_DIR.glob("*.tex")):
        print(f"    {p.name}  {p.stat().st_size} B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
