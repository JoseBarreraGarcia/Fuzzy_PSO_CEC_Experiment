#!/usr/bin/env python
"""
03_run_factorial_anova.py — H3: interaction n x R on PSO_FCS response.

Implements the tests declared in
FUZZY/ARTICULO_MDPI/04_hipotesis_metricas_analisis.md::H3:
    (a) Two-way parametric ANOVA on log10(gap_final + 1e-12) with factors n_labels x rule_set.
    (b) Scheirer-Ray-Hare non-parametric alternative.
    (c) Variance partition (partial eta-squared).
    (d) Standard deviation of aggregated response across R for each n
        (expected negative slope under H3).

Only PSO_FCS rows are analysed (H3 does not include the classical PSO baseline).

Outputs (results/tests/h3_factorial_anova/):
    anova_table.{csv,parquet}          Type-II ANOVA table
    srh_table.{csv,parquet}            Scheirer-Ray-Hare table
    variance_partition.csv             partial eta-squared per factor
    std_across_R_vs_n.csv              std of median response across R for each n
    residual_diagnostics.json          Shapiro / Levene on residuals
    summary.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[3]
META_PATH = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "level1_raw" / "experiments_meta.parquet"
L2_NR_PATH = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "level2_aggregated" / "stats_by_n_R.parquet"
OUT_DIR = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "tests" / "h3_factorial_anova"

LOG_FLOOR = 1e-12


def _log_response(x: pd.Series) -> pd.Series:
    return np.log10(np.maximum(x.astype(float), LOG_FLOOR) + LOG_FLOOR)


def scheirer_ray_hare(df: pd.DataFrame, y: str, a: str, b: str) -> pd.DataFrame:
    """Scheirer-Ray-Hare non-parametric 2-way ANOVA on ranks."""
    d = df[[y, a, b]].copy()
    d["R"] = stats.rankdata(d[y])
    n = len(d)
    ss_total = ((d["R"] - d["R"].mean()) ** 2).sum()
    ms_total = ss_total / (n - 1)

    def ss_factor(cols: list[str]) -> float:
        g = d.groupby(cols)["R"].agg(["mean", "count"])
        return float((g["count"] * (g["mean"] - d["R"].mean()) ** 2).sum())

    ss_a = ss_factor([a])
    ss_b = ss_factor([b])
    ss_ab_cells = ss_factor([a, b])
    ss_interaction = ss_ab_cells - ss_a - ss_b

    la = d[a].nunique() - 1
    lb = d[b].nunique() - 1
    lab = la * lb

    rows = []
    for name, ss, df_num in [(a, ss_a, la), (b, ss_b, lb), (f"{a}:{b}", ss_interaction, lab)]:
        H = ss / ms_total
        p = 1 - stats.chi2.cdf(H, df_num)
        rows.append({"factor": name, "H": H, "df": df_num, "p_value": p})
    return pd.DataFrame(rows)


def partial_eta_squared(anova: pd.DataFrame) -> dict[str, float]:
    ss = anova["sum_sq"].to_dict()
    residual = ss.get("Residual", np.nan)
    return {k: float(v / (v + residual)) for k, v in ss.items() if k != "Residual"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--response", choices=["gap_final", "fitness_best"], default="gap_final")
    args = parser.parse_args()

    for p in (META_PATH, L2_NR_PATH):
        if not p.exists():
            raise FileNotFoundError(f"missing input: {p}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[03] source     : {META_PATH}")
    print(f"[03] output dir : {OUT_DIR}")
    print(f"[03] response   : log10({args.response})")

    meta = pd.read_parquet(META_PATH)
    fcs = meta[meta["mh_family"] == "PSO_FCS"].copy()
    fcs["y"] = _log_response(fcs[args.response])
    fcs["n_labels"] = fcs["n_labels"].astype(int).astype("category")
    fcs["rule_set"] = fcs["rule_set"].astype("category")
    print(f"[03] PSO_FCS obs: {len(fcs):,}  (32 configs x 62 instances x 31 runs)")

    # (a) Type-II ANOVA via statsmodels.
    import statsmodels.formula.api as smf
    from statsmodels.stats.anova import anova_lm
    model = smf.ols("y ~ C(n_labels) * C(rule_set)", data=fcs).fit()
    anova = anova_lm(model, typ=2)
    anova.index = anova.index.map(
        lambda s: s.replace("C(n_labels):C(rule_set)", "n_labels:rule_set")
                   .replace("C(n_labels)", "n_labels")
                   .replace("C(rule_set)", "rule_set")
    )
    anova.to_csv(OUT_DIR / "anova_table.csv")
    anova.reset_index(names="factor").to_parquet(OUT_DIR / "anova_table.parquet", index=False)
    print(f"[03] wrote anova_table (residual df = {model.df_resid:.0f})")

    # (b) Scheirer-Ray-Hare non-parametric.
    srh = scheirer_ray_hare(fcs, y="y", a="n_labels", b="rule_set")
    srh.to_csv(OUT_DIR / "srh_table.csv", index=False)
    srh.to_parquet(OUT_DIR / "srh_table.parquet", index=False)
    print(f"[03] wrote srh_table")

    # (c) Variance partition.
    peta = partial_eta_squared(anova)
    (OUT_DIR / "variance_partition.csv").write_text(
        "factor,partial_eta_sq\n" + "\n".join(f"{k},{v:.6f}" for k, v in peta.items()),
        encoding="utf-8",
    )
    print(f"[03] wrote variance_partition")

    # (d) Std of response across R at each n (from level-2 marginal aggregates for readability).
    l2 = pd.read_parquet(L2_NR_PATH)
    std_R_vs_n = (
        l2.groupby("n_labels")["gap_median"]
          .agg(["std", "mean", "min", "max"])
          .reset_index()
          .rename(columns={"std": "std_across_R", "mean": "mean_across_R"})
    )
    std_R_vs_n.to_csv(OUT_DIR / "std_across_R_vs_n.csv", index=False)
    print(f"[03] wrote std_across_R_vs_n")

    # Residual diagnostics.
    resid = model.resid
    sample = resid.sample(min(5000, len(resid)), random_state=42)
    shapiro_stat, shapiro_p = stats.shapiro(sample)
    levene_stat, levene_p = stats.levene(
        *[grp["y"].values for _, grp in fcs.groupby(["n_labels", "rule_set"], observed=True)]
    )
    diag = {
        "shapiro_stat": float(shapiro_stat),
        "shapiro_p": float(shapiro_p),
        "shapiro_sample_size": int(len(sample)),
        "levene_stat": float(levene_stat),
        "levene_p": float(levene_p),
        "residual_mean": float(resid.mean()),
        "residual_std": float(resid.std(ddof=1)),
    }
    with (OUT_DIR / "residual_diagnostics.json").open("w", encoding="utf-8") as fh:
        json.dump(diag, fh, indent=2)

    summary = {
        "response": args.response,
        "transform": "log10(x + 1e-12)",
        "n_obs": int(len(fcs)),
        "anova_table_head": anova.reset_index(names="factor").to_dict(orient="records"),
        "srh_table": srh.to_dict(orient="records"),
        "partial_eta_squared": peta,
        "std_across_R_vs_n": std_R_vs_n.to_dict(orient="records"),
        "h3_slope_sign": "negative_if_H3_supported",
        "h3_std_R_decreasing_with_n": bool(
            std_R_vs_n.sort_values("n_labels")["std_across_R"].is_monotonic_decreasing
        ),
        "residual_diagnostics": diag,
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)
    print(f"[03] wrote summary : summary.json\n")
    print("[03] === SUMMARY ===")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
