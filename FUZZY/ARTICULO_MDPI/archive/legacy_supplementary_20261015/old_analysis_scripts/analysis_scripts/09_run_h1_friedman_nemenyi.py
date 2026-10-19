#!/usr/bin/env python
"""
09_run_h1_friedman_nemenyi.py — H1: Friedman + Nemenyi over configurations.

Ranks the 33 configurations on each (function, dim) instance by their mean rank
of fitness_best across 31 runs; then runs the Friedman omnibus test on the
resulting instance x config rank matrix, followed by Nemenyi post-hoc.

Aligned with 04_hipotesis_metricas_analisis.md::H1
(effect of granularity n; also produces CD-diagram data usable in figures).

Outputs (results/tests/h1_friedman_nemenyi/):
    mean_rank_matrix.{csv,parquet}     rows=instance, cols=mh_raw
    mean_rank_per_config.{csv,parquet} config, mean rank across instances
    friedman_omnibus.json              chi2, df, p-value
    nemenyi_pvalues.{csv,parquet}      pairwise post-hoc p-values
    nemenyi_significant_pairs.csv      pairs with p < alpha
    critical_difference.json           CD value at alpha, sample size
    cd_diagram_data.csv                pretty format for CD-diagram figure
    summary.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare
import scikit_posthocs as sph

REPO_ROOT = Path(__file__).resolve().parents[3]
META_PATH = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "level1_raw" / "experiments_meta.parquet"
OUT_DIR = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "tests" / "h1_friedman_nemenyi"


def studentized_range_q_alpha_005(k: int) -> float:
    """Approximate q_alpha=0.05 for k treatments (Demsar 2006 Nemenyi table)."""
    table = {
        2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850, 7: 2.949, 8: 3.031, 9: 3.102,
        10: 3.164, 11: 3.219, 12: 3.268, 13: 3.313, 14: 3.354, 15: 3.391, 16: 3.426,
        17: 3.458, 18: 3.489, 19: 3.517, 20: 3.544, 21: 3.569, 22: 3.593, 23: 3.616,
        24: 3.637, 25: 3.658, 26: 3.678, 27: 3.696, 28: 3.714, 29: 3.732, 30: 3.749,
        31: 3.765, 32: 3.780, 33: 3.795, 34: 3.810, 35: 3.824,
    }
    return table.get(k, 4.0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metric", choices=["gap_final", "fitness_best"], default="gap_final")
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()

    if not META_PATH.exists():
        raise FileNotFoundError(f"missing input: {META_PATH}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[09] source     : {META_PATH}")
    print(f"[09] output dir : {OUT_DIR}")
    print(f"[09] metric     : {args.metric}   alpha : {args.alpha}")

    meta = pd.read_parquet(META_PATH)
    meta["instance"] = meta["function"] + "_D" + meta["dim"].astype(str)
    print(f"[09] rows: {len(meta):,}  instances: {meta['instance'].nunique()}  configs: {meta['mh_raw'].nunique()}")

    # Median metric across 31 runs -> one value per (instance, mh_raw).
    med = meta.groupby(["instance", "mh_raw"])[args.metric].median().unstack("mh_raw")

    # Rank across configs within each instance (lower metric = rank 1).
    ranks = med.rank(axis=1, method="average", ascending=True)
    ranks.to_parquet(OUT_DIR / "mean_rank_matrix.parquet")
    ranks.to_csv(OUT_DIR / "mean_rank_matrix.csv")
    print(f"[09] wrote mean_rank_matrix: {ranks.shape[0]} instances x {ranks.shape[1]} configs")

    mean_rank_per_config = (
        ranks.mean(axis=0).rename("mean_rank").reset_index()
             .sort_values("mean_rank").reset_index(drop=True)
    )
    mean_rank_per_config.to_csv(OUT_DIR / "mean_rank_per_config.csv", index=False)
    mean_rank_per_config.to_parquet(OUT_DIR / "mean_rank_per_config.parquet", index=False)

    # Friedman omnibus.
    friedman_stat, friedman_p = friedmanchisquare(*[ranks[c].values for c in ranks.columns])
    friedman = {
        "chi2": float(friedman_stat),
        "df": int(ranks.shape[1] - 1),
        "p_value": float(friedman_p),
        "n_instances": int(ranks.shape[0]),
        "n_configs": int(ranks.shape[1]),
        "reject_H0_no_difference": bool(friedman_p < args.alpha),
    }
    with (OUT_DIR / "friedman_omnibus.json").open("w", encoding="utf-8") as fh:
        json.dump(friedman, fh, indent=2)
    print(f"[09] Friedman chi2={friedman_stat:.2f}  df={friedman['df']}  p={friedman_p:.3g}")

    # Nemenyi post-hoc on rank matrix (rows=instances = blocks, cols=treatments).
    nemenyi = sph.posthoc_nemenyi_friedman(ranks.to_numpy())
    nemenyi.index = ranks.columns
    nemenyi.columns = ranks.columns
    nemenyi.to_csv(OUT_DIR / "nemenyi_pvalues.csv")
    nemenyi.reset_index(names="mh_raw").to_parquet(OUT_DIR / "nemenyi_pvalues.parquet", index=False)
    print(f"[09] wrote nemenyi_pvalues: {nemenyi.shape}")

    # Significant pairs.
    sig_rows = []
    cfgs = list(nemenyi.columns)
    for i, ci in enumerate(cfgs):
        for cj in cfgs[i + 1:]:
            pval = float(nemenyi.loc[ci, cj])
            if pval < args.alpha:
                sig_rows.append({
                    "config_i": ci,
                    "config_j": cj,
                    "p_value": pval,
                    "mean_rank_i": float(mean_rank_per_config.set_index("mh_raw").loc[ci, "mean_rank"]),
                    "mean_rank_j": float(mean_rank_per_config.set_index("mh_raw").loc[cj, "mean_rank"]),
                })
    sig_df = pd.DataFrame(sig_rows).sort_values("p_value").reset_index(drop=True)
    sig_df.to_csv(OUT_DIR / "nemenyi_significant_pairs.csv", index=False)
    print(f"[09] significant pairs (p<{args.alpha}): {len(sig_df)} of {len(cfgs) * (len(cfgs)-1) // 2}")

    # Critical difference for CD diagram (Demsar 2006).
    k = ranks.shape[1]
    N = ranks.shape[0]
    q_alpha = studentized_range_q_alpha_005(k)
    cd = q_alpha * math.sqrt(k * (k + 1) / (6 * N))
    cd_info = {"k": int(k), "N": int(N), "q_alpha_0.05": q_alpha, "CD": float(cd)}
    with (OUT_DIR / "critical_difference.json").open("w", encoding="utf-8") as fh:
        json.dump(cd_info, fh, indent=2)
    print(f"[09] CD (alpha=0.05): {cd:.4f}  (k={k}, N={N}, q={q_alpha})")

    cd_data = mean_rank_per_config.copy()
    cd_data["cd_reference"] = cd
    cd_data.to_csv(OUT_DIR / "cd_diagram_data.csv", index=False)

    summary = {
        "metric": args.metric,
        "alpha": args.alpha,
        "friedman": friedman,
        "critical_difference": cd_info,
        "best_config_by_mean_rank": mean_rank_per_config.iloc[0].to_dict(),
        "worst_config_by_mean_rank": mean_rank_per_config.iloc[-1].to_dict(),
        "top5_mean_rank": mean_rank_per_config.head(5).to_dict(orient="records"),
        "significant_pairs_count": int(len(sig_df)),
        "H1_supported_by_friedman": bool(friedman_p < args.alpha),
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)
    print(f"[09] wrote summary : summary.json\n")
    print("[09] === SUMMARY ===")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
