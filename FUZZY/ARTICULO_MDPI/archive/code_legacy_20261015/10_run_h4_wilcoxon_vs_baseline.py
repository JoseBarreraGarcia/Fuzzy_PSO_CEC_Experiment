#!/usr/bin/env python
"""
10_run_h4_wilcoxon_vs_baseline.py — H4: PSO_FCS beats PSO in a majority of instances.

For every (function, dim) instance and every PSO_FCS configuration, tests
    H0 : fitness_best(PSO_FCS) == fitness_best(PSO)   (paired by run_id)
vs.  H1 : fitness_best(PSO_FCS) != fitness_best(PSO)
using the Wilcoxon signed-rank test on paired samples of 31 runs.
Effect size is quantified with Vargha-Delaney A12.

Aligned with FUZZY/ARTICULO_MDPI/04_hipotesis_metricas_analisis.md::H4.

Outputs (results/tests/h4_wilcoxon_vs_baseline/):
    wilcoxon_pairs.{csv,parquet}       one row per (config, instance)
    wilcoxon_config_summary.csv        wins / ties / losses per config
    top_configs_wins.csv               ranked by (raw_wins, Bonferroni_wins)
    summary.json
"""
from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

REPO_ROOT = Path(__file__).resolve().parents[3]
META_PATH = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "level1_raw" / "experiments_meta.parquet"
OUT_DIR = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "tests" / "h4_wilcoxon_vs_baseline"


def vargha_delaney_a12(x: np.ndarray, y: np.ndarray) -> float:
    """Non-parametric effect size. A12 = P(X < Y) + 0.5 P(X = Y).
    Lower fitness is better, so A12 > 0.5 means x tends to be smaller (better) than y."""
    m, n = len(x), len(y)
    if m == 0 or n == 0:
        return float("nan")
    xt = x[:, None]
    yt = y[None, :]
    less = float((xt < yt).sum())
    equal = float((xt == yt).sum())
    return (less + 0.5 * equal) / (m * n)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alpha", type=float, default=0.05)
    args = parser.parse_args()

    if not META_PATH.exists():
        raise FileNotFoundError(f"missing input: {META_PATH}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[10] source     : {META_PATH}")
    print(f"[10] output dir : {OUT_DIR}")
    print(f"[10] alpha      : {args.alpha}")

    meta = pd.read_parquet(META_PATH)
    meta["instance"] = meta["function"] + "_D" + meta["dim"].astype(str)

    pso = meta[meta["mh_family"] == "PSO"][["instance", "run_id", "fitness_best"]].rename(
        columns={"fitness_best": "fb_pso"}
    )
    fcs = meta[meta["mh_family"] == "PSO_FCS"]
    print(f"[10] baseline PSO rows : {len(pso):,}")
    print(f"[10] PSO_FCS rows      : {len(fcs):,}")

    instances = sorted(pso["instance"].unique())
    fcs_configs = sorted(fcs["mh_raw"].unique())
    total_tests = len(instances) * len(fcs_configs)
    bonf_alpha = args.alpha / total_tests
    print(f"[10] total tests: {total_tests}   Bonferroni alpha: {bonf_alpha:.3g}")

    rows: list[dict] = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")   # zero-difference cases raise scipy warnings.
        for cfg, cfg_df in fcs.groupby("mh_raw"):
            n_labels = cfg_df["n_labels"].iloc[0]
            rule_set = cfg_df["rule_set"].iloc[0]
            cfg_frame = cfg_df[["instance", "run_id", "fitness_best"]].rename(
                columns={"fitness_best": "fb_fcs"}
            )
            merged = cfg_frame.merge(pso, on=["instance", "run_id"], how="inner")
            for inst, sub in merged.groupby("instance"):
                x = sub["fb_fcs"].to_numpy()
                y = sub["fb_pso"].to_numpy()
                diff = x - y
                median_diff = float(np.median(diff))
                if np.all(diff == 0):
                    stat = float("nan")
                    pval = 1.0
                else:
                    try:
                        stat, pval = wilcoxon(x, y, alternative="two-sided", zero_method="wilcox")
                        pval = float(pval)
                    except ValueError:
                        stat, pval = float("nan"), 1.0
                a12 = vargha_delaney_a12(x, y)
                # Lower fitness is better; A12 > 0.5 means PSO_FCS smaller (better).
                if pval < args.alpha:
                    direction = "win" if a12 > 0.5 else "loss"
                else:
                    direction = "tie"
                bonf_direction = "tie"
                if pval < bonf_alpha:
                    bonf_direction = "win" if a12 > 0.5 else "loss"
                rows.append({
                    "mh_raw": cfg,
                    "n_labels": n_labels,
                    "rule_set": rule_set,
                    "instance": inst,
                    "median_fitness_fcs": float(np.median(x)),
                    "median_fitness_pso": float(np.median(y)),
                    "median_diff": median_diff,
                    "wilcoxon_stat": stat,
                    "p_value": pval,
                    "a12": a12,
                    "direction_alpha_0.05": direction,
                    "direction_bonferroni": bonf_direction,
                })
    df = pd.DataFrame(rows)
    df.to_parquet(OUT_DIR / "wilcoxon_pairs.parquet", index=False)
    df.to_csv(OUT_DIR / "wilcoxon_pairs.csv", index=False)
    print(f"[10] wrote wilcoxon_pairs: {len(df)} rows")

    def tally(sub: pd.DataFrame, col: str) -> dict:
        c = sub[col].value_counts().to_dict()
        return {"wins": int(c.get("win", 0)), "ties": int(c.get("tie", 0)), "losses": int(c.get("loss", 0))}

    summary_rows = []
    for cfg, sub in df.groupby("mh_raw"):
        row = {"mh_raw": cfg,
               "n_labels": float(sub["n_labels"].iloc[0]) if pd.notna(sub["n_labels"].iloc[0]) else np.nan,
               "rule_set": sub["rule_set"].iloc[0],
               "n_instances": int(len(sub))}
        raw = tally(sub, "direction_alpha_0.05")
        bonf = tally(sub, "direction_bonferroni")
        row.update({f"raw_{k}": v for k, v in raw.items()})
        row.update({f"bonf_{k}": v for k, v in bonf.items()})
        row["a12_mean"] = float(sub["a12"].mean())
        row["a12_median"] = float(sub["a12"].median())
        summary_rows.append(row)
    csummary = pd.DataFrame(summary_rows).sort_values(
        ["bonf_wins", "raw_wins", "a12_mean"], ascending=[False, False, False]
    ).reset_index(drop=True)
    csummary.to_csv(OUT_DIR / "wilcoxon_config_summary.csv", index=False)
    csummary.to_parquet(OUT_DIR / "wilcoxon_config_summary.parquet", index=False)
    print(f"[10] wrote wilcoxon_config_summary: {len(csummary)} configs")

    top = csummary.head(10)
    top.to_csv(OUT_DIR / "top_configs_wins.csv", index=False)

    # H4 criterion: at least one config with raw_wins >= 50% of |instances|.
    n_inst = len(instances)
    winners_h4 = csummary[csummary["raw_wins"] >= 0.5 * n_inst]
    winners_h4_bonf = csummary[csummary["bonf_wins"] >= 0.5 * n_inst]

    summary = {
        "alpha": args.alpha,
        "n_instances": int(n_inst),
        "n_configs": int(len(fcs_configs)),
        "bonferroni_alpha": bonf_alpha,
        "H4_supported_raw": bool(len(winners_h4) > 0),
        "H4_supported_bonferroni": bool(len(winners_h4_bonf) > 0),
        "H4_winning_configs_raw": winners_h4["mh_raw"].tolist(),
        "H4_winning_configs_bonferroni": winners_h4_bonf["mh_raw"].tolist(),
        "top5_raw_wins": csummary.head(5).to_dict(orient="records"),
        "worst5_raw_wins": csummary.tail(5).to_dict(orient="records"),
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)
    print(f"[10] wrote summary : summary.json\n")
    print("[10] === SUMMARY ===")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
