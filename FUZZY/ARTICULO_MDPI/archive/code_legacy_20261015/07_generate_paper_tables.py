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
    manuscript/tables/tab_class_summary.tex  class-level positions from H2 rankings
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
MS_TABLES = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "manuscript" / "tables"


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
                caption="Paired Wilcoxon comparisons of the ten FCS configurations with the most "
                    "Bonferroni-significant wins against PSO (62 instances), ordered by corrected wins, "
                    "nominal wins, and mean A12. * marks the correction across all 32x62 tests; "
                    "A12 > 0.5 favours FCS because lower fitness is better.",
                label="tab:h4_wilcoxon",
                float_fmt="%.3f")


def table_kendall_class() -> None:
    tau = pd.read_csv(RESULTS / "tests" / "h5_pareto_problemtype" / "kendall_tau_by_class.csv", index_col=0)
    tau = tau.rename(index=CLASS_SHORT, columns=CLASS_SHORT)
    order = [CLASS_SHORT[k] for k in ("unimodal", "multimodal", "composed")]
    tau = tau.loc[order, order].round(3).reset_index().rename(columns={"index": "Class"})
    _write_pair(tau, "tab_kendall_class",
                caption="Kendall's $\\tau$ between configuration rankings induced by each landscape class. "
                    "The two scalable classes show strong observed concordance; concordance with the "
                    "fixed-dimensional class is weak.",
                label="tab:kendall_class")


def table_class_summary() -> None:
    ranking = pd.read_csv(RESULTS / "tests" / "h5_pareto_problemtype" / "ranking_by_class.csv")
    winners = pd.read_csv(RESULTS / "tests" / "h5_pareto_problemtype" / "winners_by_class.csv")
    groups = [
        ("unimodal", "Unimodal (F1--F7)", 7, 28),
        ("multimodal", "Scalable multimodal (F8--F13)", 6, 24),
        ("composed", "Fixed-dimensional (F14--F23)", 10, 10),
    ]
    lines = [
        "% Generated from the existing H2 class-ranking outputs; no new analysis.",
        "\\begin{table}[H]",
        "\\centering",
        "\\small",
        "\\caption{Positions of the 33 configurations by mean instance-level median normalized gap within each benchmark group (lower is better). For each configuration--instance pair, the median normalized gap over 31 runs was first computed; these medians were then averaged within the group. Positions use minimum ranks for ties and are not Friedman mean ranks.}",
        "\\label{tab:class_summary}",
        "\\setlength{\\tabcolsep}{3pt}",
        "\\begin{tabularx}{\\textwidth}{@{}>{\\raggedright\\arraybackslash}Xcc>{\\raggedright\\arraybackslash}p{2.7cm}cc@{}}",
        "\\toprule",
        "\\textbf{Benchmark group} & \\textbf{Functions} & \\textbf{Instances} & ",
        "\\textbf{Leading configuration} & \\textbf{PSO position} & \\textbf{FCS-3-R1 position} \\\\",
        "\\midrule",
    ]
    for class_key, label, n_functions, n_instances in groups:
        class_rows = ranking[ranking["problem_class"] == class_key]
        winner_rows = winners[winners["problem_class"] == class_key]
        if class_rows["mh_raw"].nunique() != 33 or len(winner_rows) != 1:
            raise ValueError(f"Expected 33 ranked configurations and one leader for {class_key}")
        leader = short_name(winner_rows.iloc[0]["mh_raw"])
        pso_rank = int(class_rows.loc[class_rows["mh_raw"] == "PSO", "rank"].iloc[0])
        fcs3r1_rank = int(class_rows.loc[
            class_rows["mh_raw"] == "PSO_FCS:G3:I1:R1:O1", "rank"
        ].iloc[0])
        lines.append(
            f"{label} & {n_functions} & {n_instances} & {leader} & "
            f"{pso_rank}/33 & {fcs3r1_rank}/33 \\\\"
        )
    lines += ["\\bottomrule", "\\end{tabularx}", "\\end{table}", ""]
    MS_TABLES.mkdir(parents=True, exist_ok=True)
    (MS_TABLES / "tab_class_summary.tex").write_text(chr(10).join(lines), encoding="utf-8")
    print("[07] wrote manuscript/tables/tab_class_summary.tex")


def table_scaling_slopes() -> None:
    slopes = pd.read_csv(RESULTS / "tests" / "scaling_curves" / "scaling_slopes_by_mh.csv")
    top = slopes.head(5).assign(status="lowest-median-slope")
    bot = slopes.tail(5).assign(status="highest-median-slope")
    df = pd.concat([top, bot])[["status", "mh_raw", "n_labels", "rule_set",
                                 "mean_slope", "median_slope", "mean_r2"]].reset_index(drop=True)
    df["mh_raw"] = df["mh_raw"].map(short_name)
    df["n_labels"] = df["n_labels"].astype(int)
    df.columns = ["Status", "Config.", "n", "R", "Mean slope", "Median slope", "Mean R^2"]
    _write_pair(df, "tab_scaling_slopes",
                caption="Log-log slope of the median normalized gap against dimension over the scalable subset "
                    "S1 (F1-F13). The table lists the five configurations with the lowest and highest "
                    "median fitted slopes; a lower slope describes less relative degradation but does not "
                    "necessarily indicate better absolute performance.",
                label="tab:scaling_slopes")


def table_hypothesis_summary() -> None:
    h1 = json.loads((RESULTS / "tests" / "h1_friedman_nemenyi" / "summary.json").read_text(encoding="utf-8"))
    h3_dispersion = pd.read_csv(RESULTS / "tests" / "h3_function_dispersion" / "function_dispersion.csv")
    h5 = json.loads((RESULTS / "tests" / "h5_pareto_problemtype" / "summary.json").read_text(encoding="utf-8"))
    h4 = json.loads((RESULTS / "tests" / "h4_wilcoxon_vs_baseline" / "summary.json").read_text(encoding="utf-8"))
    mean_ranks = pd.read_csv(RESULTS / "tests" / "h1_friedman_nemenyi" / "mean_rank_per_config.csv")
    mean_ranks = mean_ranks[mean_ranks["mh_raw"].str.startswith("PSO_FCS:")].copy()
    mean_ranks["n_labels"] = mean_ranks["mh_raw"].str.extract(r"G(\d+)").astype(int)
    best_mean_rank_by_n = mean_ranks.groupby("n_labels")["mean_rank"].min()

    tau_composed_unimodal = float(h5["kendall_by_class"]["composed"]["unimodal"])
    tau_unimodal_multimodal = float(h5["kendall_by_class"]["unimodal"]["multimodal"])
    tau_multimodal_composed = float(h5["kendall_by_class"]["multimodal"]["composed"])
    tau_S1_S2 = float(h5["kendall_tau_S1_vs_S2"])
    p_S1_S2 = float(h5["kendall_p_S1_vs_S2"])
    best_S1 = short_name(h5["best_by_subgroup"]["S1"]["mh_raw"])
    best_S2 = short_name(h5["best_by_subgroup"]["S2"]["mh_raw"])
    friedman_p = float(h1["friedman"]["p_value"])
    cd = float(h1["critical_difference"]["CD"])
    rank_medians = h3_dispersion.groupby("n_labels")["rank_sd_across_R"].median()
    loggap_medians = h3_dispersion.groupby("n_labels")["loggap_sd_across_R"].median()
    rank_wide = h3_dispersion.pivot(index="function", columns="n_labels", values="rank_sd_across_R")
    loggap_wide = h3_dispersion.pivot(index="function", columns="n_labels", values="loggap_sd_across_R")
    rank_endpoint_decreases = int((rank_wide[9] < rank_wide[3]).sum())
    loggap_endpoint_decreases = int((loggap_wide[9] < loggap_wide[3]).sum())
    rank_monotone = int(((rank_wide[3] >= rank_wide[5]) &
                         (rank_wide[5] >= rank_wide[7]) &
                         (rank_wide[7] >= rank_wide[9])).sum())
    loggap_monotone = int(((loggap_wide[3] >= loggap_wide[5]) &
                           (loggap_wide[5] >= loggap_wide[7]) &
                           (loggap_wide[7] >= loggap_wide[9])).sum())
    best_h4 = h4["top5_raw_wins"][0]

    rows = [
        ("\\textbf{RQ1.} Does higher granularity improve configuration ranks?",
         f"Friedman $p={friedman_p:.1e}$; Nemenyi critical difference (CD) $={cd:.2f}$. Best mean rank at "
         f"$n=3/5/7/9$: " + "/".join(f"{best_mean_rank_by_n[n]:.2f}" for n in (3, 5, 7, 9)) + ".",
         "Configuration ranks differ overall; best mean rank worsens as $n$ increases. "
         "FCS-3-R1 and PSO share the same Nemenyi group.",
         "The omnibus test compares complete configurations; it does not isolate an independent granularity effect."),
        ("\\textbf{RQ2.} How do rankings transfer across classes and dimensional regimes?",
         f"Class-level rank concordance: $\\tau={tau_unimodal_multimodal:.3f}$ (unimodal/scalable); "
         f"{tau_composed_unimodal:.3f} (unimodal/fixed); {tau_multimodal_composed:.3f} (scalable/fixed).",
         "Concordance is high between the two scalable groups and weak between either and the fixed-dimensional group.",
         "These comparisons describe the evaluated groups; they establish neither causal class effects nor general transferability."),
        ("\\textbf{RQ3.} Does increasing linguistic granularity consistently reduce performance differences among rule-base patterns?",
         "Function-level median standard deviation (SD) across R1--R8 at $n=3/5/7/9$: ranks "
         + "/".join(f"{rank_medians[n]:.3f}" for n in (3, 5, 7, 9)) + "; log-gap "
         + "/".join(f"{loggap_medians[n]:.3f}" for n in (3, 5, 7, 9)) + ". "
         + f"Between $n=3$ and $n=9$, spread is lower in {rank_endpoint_decreases}/23 functions "
         + f"(rank) and {loggap_endpoint_decreases}/23 (log-gap); it is non-increasing across "
         + f"$n$ in {rank_monotone}/23 functions for each measure.",
         "Neither response shows a consistent decrease in dispersion with granularity.",
         "Exploratory, descriptive evidence; not a confirmatory interaction test."),
        ("\\textbf{RQ4.} What paired outcomes occur for a fixed FCS configuration vs PSO?",
         f"FCS-3-R1: {best_h4['raw_wins']}/{best_h4['raw_ties']}/{best_h4['raw_losses']} "
         "nominal wins/ties/losses; "
         f"{best_h4['bonf_wins']}/{best_h4['bonf_ties']}/{best_h4['bonf_losses']} "
         "after Bonferroni correction over $32\\times62=1,984$ tests.",
         "FCS-3-R1 retains 13 corrected wins and no corrected losses.",
         "Non-significance does not establish equivalence. Selecting the best FCS separately for each instance is an oracle comparison, not a fixed policy."),
        ("\\textbf{H5.} Do the best-ranked configurations transfer between $S_1$ and $S_2$?",
                 f"$\\tau(S_1,S_2)={tau_S1_S2:.3f}$, $p={p_S1_S2:.3f}$; mean-gap leaders: "
         f"$S_1$ \\texttt{{{best_S1}}}, $S_2$ \\texttt{{{best_S2}}}.",
         "The subset leaders differ; observed rank concordance is weak.",
         "The non-significant association is not evidence of independence and applies only to this evaluated split."),
    ]

    rows = [
        (question.replace(r"\textbf{H", r"\textbf{RQ"), evidence, finding, scope)
        for question, evidence, finding, scope in rows
    ]
    pd.DataFrame(rows, columns=["research_question", "main_evidence", "observed_finding", "interpretation_scope"]).to_csv(
        OUT_DIR / "tab_hypothesis_summary.csv", index=False)

    lines = [
        "\\begin{table}[H]",
        "\\centering",
        "\\small",
        "\\caption{Research questions RQ1--RQ5, principal evidence, observed findings, and scope within the evaluated benchmark. RQ3 is descriptive; non-significant results are not interpreted as equivalence or independence.}",
        "\\label{tab:hypothesis_summary}",
        "\\setlength{\\tabcolsep}{3pt}",
        "\\begin{tabularx}{\\textwidth}{@{}>{\\raggedright\\arraybackslash}p{2.7cm}"
        ">{\\raggedright\\arraybackslash}p{3.7cm}>{\\raggedright\\arraybackslash}p{3.0cm}"
        ">{\\raggedright\\arraybackslash}X@{}}",
        "\\toprule",
        "\\textbf{Research question} & \\textbf{Main evidence} & \\textbf{Observed finding} & \\textbf{Interpretation and scope} \\\\",
        "\\midrule",
    ]
    for question, evidence, finding, scope in rows:
        lines.append(f"{question} & {evidence} & {finding} & {scope} \\\\")
    lines += ["\\bottomrule", "\\end{tabularx}", "\\end{table}", ""]
    table_tex = "\n".join(lines)
    (OUT_DIR / "tab_hypothesis_summary.tex").write_text(table_tex, encoding="utf-8")
    MS_TABLES.mkdir(parents=True, exist_ok=True)
    (MS_TABLES / "tab_hypothesis_summary.tex").write_text(table_tex, encoding="utf-8")
    print(f"[07] wrote tab_hypothesis_summary.tex / .csv  ({len(rows)} rows)")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[07] output dir : {OUT_DIR}")
    table_top_configs()
    table_h4()
    table_kendall_class()
    table_class_summary()
    table_scaling_slopes()
    table_hypothesis_summary()
    print("[07] === DONE ===")
    for p in sorted(OUT_DIR.glob("*.tex")):
        print(f"    {p.name}  {p.stat().st_size} B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
