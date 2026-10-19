#!/usr/bin/env python
"""
02_generate_level3_rankings.py — Level-3 disaggregated rankings.

Per-instance winner tables and per-config specialization profiles derived from
the run-level parquet plus the level-2 aggregated stats. Feeds the H2/H4/H5
narrative of FUZZY/ARTICULO_MDPI/04_hipotesis_metricas_analisis.md.

Outputs (results/level3_rankings/):
    ranking_per_instance.{parquet,csv}       ranked (mh) inside each (function, dim)
    winners_per_instance.{parquet,csv}       one row per instance = best mh (by median)
    top_configs_global.{parquet,csv}         top-N configs by number of wins
    config_specialization.{parquet,csv}      per mh: instances where it ranks first
    rank_matrix_median.{parquet,csv}         wide matrix mh x instance of median rank
    summary.json                             totals + head/tail
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
L2_PATH = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "level2_aggregated" / "stats_by_config_instance.parquet"
OUT_DIR = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "level3_rankings"


def _write(df: pd.DataFrame, stem: str) -> None:
    df.to_parquet(OUT_DIR / f"{stem}.parquet", index=False)
    df.to_csv(OUT_DIR / f"{stem}.csv", index=False)
    print(f"[02] wrote {stem}: {len(df):>6} rows")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-n", type=int, default=10,
                        help="rows in top_configs_global (default 10).")
    parser.add_argument("--rank-metric", choices=["gap_median", "gap_mean", "median_best"],
                        default="gap_median",
                        help="metric used to rank configs within each instance.")
    args = parser.parse_args()

    if not L2_PATH.exists():
        raise FileNotFoundError(f"missing input: {L2_PATH}. Run script 01 first.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[02] source     : {L2_PATH}")
    print(f"[02] output dir : {OUT_DIR}")
    print(f"[02] rank metric: {args.rank_metric}")

    df = pd.read_parquet(L2_PATH)
    df["instance"] = df["function"] + "_D" + df["dim"].astype(str)

    # 1) Rank per instance (1 = best on that instance).
    df["rank"] = df.groupby(["function", "dim"])[args.rank_metric].rank(method="min", ascending=True).astype(int)
    ranked = df.sort_values(["function", "dim", "rank"]).reset_index(drop=True)
    keep = ["function", "dim", "instance", "rank", "mh_raw", "mh_family",
            "n_labels", "rule_set", args.rank_metric, "median_best", "mean_best",
            "success_rate", "n_runs"]
    _write(ranked[keep], "ranking_per_instance")

    # 2) Winners per instance (rank == 1). Ties preserved.
    winners = ranked[ranked["rank"] == 1].copy()
    _write(winners[["function", "dim", "instance", "mh_raw", "mh_family", "n_labels",
                    "rule_set", args.rank_metric, "median_best", "success_rate"]],
           "winners_per_instance")

    # 3) Top-N global by number of first-place instances (ties count as fractional wins).
    ties_per_instance = winners.groupby("instance")["mh_raw"].transform("size")
    winners["fractional_win"] = 1.0 / ties_per_instance
    wins = (
        winners.groupby(["mh_raw", "mh_family", "n_labels", "rule_set"], dropna=False)
               .agg(wins=("mh_raw", "size"), fractional_wins=("fractional_win", "sum"))
               .reset_index()
               .sort_values(["fractional_wins", "wins"], ascending=False)
               .reset_index(drop=True)
    )
    _write(wins.head(args.top_n), "top_configs_global")

    # 4) Specialization: for every mh list the instances where it ranks first + its own mean rank.
    mean_rank = ranked.groupby(["mh_raw", "mh_family", "n_labels", "rule_set"], dropna=False)["rank"].agg(
        mean_rank="mean", median_rank="median", rank_1_count=lambda s: int((s == 1).sum())
    ).reset_index()
    _write(mean_rank.sort_values(["mean_rank", "rank_1_count"], ascending=[True, False]).reset_index(drop=True),
           "config_specialization")

    # 5) Wide rank matrix (mh x instance) for heatmaps / Friedman inputs.
    matrix = ranked.pivot(index="mh_raw", columns="instance", values="rank")
    matrix.to_parquet(OUT_DIR / "rank_matrix_median.parquet")
    matrix.to_csv(OUT_DIR / "rank_matrix_median.csv")
    print(f"[02] wrote rank_matrix_median: {matrix.shape[0]} x {matrix.shape[1]}")

    summary = {
        "rank_metric": args.rank_metric,
        "n_instances": int(ranked.groupby(["function", "dim"]).ngroups),
        "n_configs": int(ranked["mh_raw"].nunique()),
        "instances_with_ties_at_rank1": int((winners.groupby("instance")["mh_raw"].size() > 1).sum()),
        "total_first_place_records": int(len(winners)),
        "top5_configs": wins.head(5).to_dict(orient="records"),
        "config_with_best_mean_rank": mean_rank.sort_values("mean_rank").iloc[0].to_dict(),
        "config_with_worst_mean_rank": mean_rank.sort_values("mean_rank").iloc[-1].to_dict(),
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)
    print(f"[02] wrote summary : summary.json\n")
    print("[02] === SUMMARY ===")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
