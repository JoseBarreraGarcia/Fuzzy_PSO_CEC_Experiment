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

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _naming import CLASS_SHORT, short_name

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
    df["mh_raw"] = df["mh_raw"].map(short_name)
    df.columns = ["Configuration", "Mean rank"]
    n_configs = len(mr)
    _write_pair(df, "tab_top_configs",
                caption=f"Top-10 of the {n_configs} algorithmic configurations by mean Friedman rank over the "
                        "62 benchmark instances (lower is better). The classical PSO baseline is included in the "
                        "ranking. Configurations are named FCS-n-Rk, where n is the number of linguistic labels "
                        "and Rk the rule-base pattern.",
                label="tab:top_configs")


def table_h4() -> None:
    cs = pd.read_csv(RESULTS / "tests" / "h4_wilcoxon_vs_baseline" / "wilcoxon_config_summary.csv")
    cs = cs.head(10)[["mh_raw", "n_labels", "rule_set", "raw_wins", "raw_ties", "raw_losses",
                       "bonf_wins", "bonf_ties", "bonf_losses", "a12_mean"]].copy()
    cs["mh_raw"] = cs["mh_raw"].map(short_name)
    cs["n_labels"] = cs["n_labels"].astype(int)
    cs.columns = ["Config.", "n", "R", "Wins", "Ties", "Losses", "Wins*", "Ties*", "Losses*", "A12 mean"]
    _write_pair(cs, "tab_h4_wilcoxon",
                caption="Paired Wilcoxon signed-rank comparison of the top-10 fuzzy configurations against the "
                        "classical PSO baseline, over the 62 instances. Columns marked * apply the Bonferroni "
                        "correction over the full 32x62 grid. A12 is the Vargha-Delaney effect size computed on "
                        "the final fitness; since lower fitness is better, A12 > 0.5 favours the fuzzy "
                        "configuration and A12 < 0.5 favours the baseline.",
                label="tab:h4_wilcoxon",
                float_fmt="%.3f")


def table_kendall_class() -> None:
    tau = pd.read_csv(RESULTS / "tests" / "h5_pareto_problemtype" / "kendall_tau_by_class.csv", index_col=0)
    tau = tau.rename(index=CLASS_SHORT, columns=CLASS_SHORT)
    order = [CLASS_SHORT[k] for k in ("unimodal", "multimodal", "composed")]
    tau = tau.loc[order, order].round(3).reset_index().rename(columns={"index": "Class"})
    _write_pair(tau, "tab_kendall_class",
                caption="Kendall's tau between the configuration rankings induced by each landscape class "
                        "(higher = more agreement). The two scalable classes agree closely, whereas the "
                        "fixed-dimensional class is almost unrelated to both.",
                label="tab:kendall_class")


def table_scaling_slopes() -> None:
    slopes = pd.read_csv(RESULTS / "tests" / "scaling_curves" / "scaling_slopes_by_mh.csv")
    top = slopes.head(5).assign(status="best-scaling")
    bot = slopes.tail(5).assign(status="worst-scaling")
    df = pd.concat([top, bot])[["status", "mh_raw", "n_labels", "rule_set",
                                 "mean_slope", "median_slope", "mean_r2"]].reset_index(drop=True)
    df["mh_raw"] = df["mh_raw"].map(short_name)
    df["n_labels"] = df["n_labels"].astype(int)
    df.columns = ["Status", "Config.", "n", "R", "Mean slope", "Median slope", "Mean R^2"]
    _write_pair(df, "tab_scaling_slopes",
                caption="Log-log slope of the median normalized gap against dimension over the scalable subset "
                        "S1 (F1-F13), for the five best- and five worst-scaling configurations.",
                label="tab:scaling_slopes")


def table_hypothesis_summary() -> None:
    h1 = json.loads((RESULTS / "tests" / "h1_friedman_nemenyi" / "summary.json").read_text(encoding="utf-8"))
    h3 = json.loads((RESULTS / "tests" / "h3_factorial_anova" / "summary.json").read_text(encoding="utf-8"))
    h5 = json.loads((RESULTS / "tests" / "h5_pareto_problemtype" / "summary.json").read_text(encoding="utf-8"))
    h4 = json.loads((RESULTS / "tests" / "h4_wilcoxon_vs_baseline" / "summary.json").read_text(encoding="utf-8"))

    tau_composed_unimodal = float(h5["kendall_by_class"]["composed"]["unimodal"])
    tau_S1_S2 = float(h5["kendall_tau_S1_vs_S2"])
    p_S1_S2 = float(h5["kendall_p_S1_vs_S2"])
    best_S1 = short_name(h5["best_by_subgroup"]["S1"]["mh_raw"])
    best_S2 = short_name(h5["best_by_subgroup"]["S2"]["mh_raw"])
    friedman_p = float(h1["friedman"]["p_value"])
    interaction_p_srh = next(row["p_value"] for row in h3["srh_table"] if row["factor"] == "n_labels:rule_set")
    peta_rule = float(h3["partial_eta_squared"]["rule_set"])
    peta_n = float(h3["partial_eta_squared"]["n_labels"])

    rows = [
        ("H1", "Granularity has diminishing returns",
         f"Friedman $\\chi^2$, $p={friedman_p:.0e}$",
         "Rejected globally; within R1 the effect of $n$ falls below the critical difference"),
        ("H2", "The best rule pattern depends on the landscape class",
         f"$\\tau$(fixed-dim., unimodal) $= {tau_composed_unimodal:.2f}$",
         "Supported"),
        ("H3", "Sensitivity to the rule pattern decreases with $n$",
         f"$n \\times R$ SRH $p={interaction_p_srh:.2f}$; $\\eta_p^2(R)={peta_rule:.3f}$, "
         f"$\\eta_p^2(n)={peta_n:.4f}$",
         "Not supported"),
        ("H4", "A fuzzy configuration beats PSO on at least half of the instances",
         "Best configuration: 27 wins / 33 ties / 2 losses of 62",
         f"Not supported under the 50\\% criterion ({h4['H4_supported_raw']})"),
        ("H5", "No static $(n,R)$ dominates both $S_1$ and $S_2$",
         f"$\\tau(S_1,S_2)={tau_S1_S2:.2f}$ ($p={p_S1_S2:.2f}$); "
         f"best on $S_1$: \\texttt{{{best_S1}}}, best on $S_2$: \\texttt{{{best_S2}}}",
         "Supported"),
    ]

    pd.DataFrame(rows, columns=["id", "statement", "statistic", "verdict"]).to_csv(
        OUT_DIR / "tab_hypothesis_summary.csv", index=False)

    lines = [
        "\\begin{table}[H]",
        "\\centering",
        "\\small",
        "\\caption{Research questions H1--H5 with their governing statistic and outcome. "
        "$S_1$ denotes the scalable subset (F1--F13) and $S_2$ the fixed-dimensional subset "
        "(F14--F23). Configurations follow the FCS-$n$-R$k$ notation.}",
        "\\label{tab:hypothesis_summary}",
        "\\setlength{\\tabcolsep}{4pt}",
        "\\begin{tabularx}{\\textwidth}{l>{\\raggedright\\arraybackslash}p{4.1cm}"
        ">{\\raggedright\\arraybackslash}X>{\\raggedright\\arraybackslash}p{3.2cm}}",
        "\\toprule",
        "\\textbf{ID} & \\textbf{Question} & \\textbf{Key statistic} & \\textbf{Outcome} \\\\",
        "\\midrule",
    ]
    for rid, statement, statistic, verdict in rows:
        lines.append(f"{rid} & {statement} & {statistic} & {verdict} \\\\")
    lines += ["\\bottomrule", "\\end{tabularx}", "\\end{table}", ""]
    (OUT_DIR / "tab_hypothesis_summary.tex").write_text("\n".join(lines), encoding="utf-8")
    print(f"[07] wrote tab_hypothesis_summary.tex / .csv  ({len(rows)} rows)")


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
