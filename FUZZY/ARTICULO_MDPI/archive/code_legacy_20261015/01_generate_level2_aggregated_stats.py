#!/usr/bin/env python
"""
01_generate_level2_aggregated_stats.py — Level-2 descriptive statistics.

Consumes results/level1_raw/experiments_meta.parquet and produces marginal
aggregations aligned with the derived metrics of section 1 of
FUZZY/ARTICULO_MDPI/04_hipotesis_metricas_analisis.md
(mean_best, median_best, std_best, IQR_best, success_rate, gap statistics).

Outputs (results/level2_aggregated/):
    stats_by_config_instance.{parquet,csv}   per (mh_raw, function, dim)
    stats_by_config.{parquet,csv}            marginal over instances (per mh_raw)
    stats_by_n_R.{parquet,csv}               marginal PSO_FCS only (n_labels x rule_set)
    stats_by_function.{parquet,csv}          per function (problem difficulty)
    stats_by_dim.{parquet,csv}               per dim
    summary.json                             sanity flags + global aggregates
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
META_PATH = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "level1_raw" / "experiments_meta.parquet"
OUT_DIR = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "level2_aggregated"

# ε for "success" (fitness_best within ε of the real optimum).
DEFAULT_SUCCESS_EPS = 1e-6


def _quantile(series: pd.Series, q: float) -> float:
    return float(series.quantile(q))


def _stats_block(fitness: pd.Series, gap: pd.Series, t_exec: pd.Series, eps: float) -> dict:
    n = int(fitness.size)
    mean = float(fitness.mean())
    std = float(fitness.std(ddof=1)) if n > 1 else float("nan")
    q1 = _quantile(fitness, 0.25)
    q3 = _quantile(fitness, 0.75)
    return {
        "n_runs": n,
        "mean_best": mean,
        "median_best": float(fitness.median()),
        "std_best": std,
        "min_best": float(fitness.min()),
        "max_best": float(fitness.max()),
        "iqr_best": q3 - q1,
        "cv_pct_best": float("nan") if mean == 0 else abs(std / mean) * 100.0,
        "gap_mean": float(gap.mean()),
        "gap_median": float(gap.median()),
        "gap_min": float(gap.min()),
        "gap_max": float(gap.max()),
        "gap_std": float(gap.std(ddof=1)) if n > 1 else float("nan"),
        "success_rate": float((gap <= eps).mean()),
        "t_mean": float(t_exec.mean()),
        "t_median": float(t_exec.median()),
    }


def _aggregate(df: pd.DataFrame, group_cols: list[str], eps: float) -> pd.DataFrame:
    rows: list[dict] = []
    for keys, sub in df.groupby(group_cols, dropna=False, observed=True):
        keys_t = keys if isinstance(keys, tuple) else (keys,)
        row = dict(zip(group_cols, keys_t))
        row.update(_stats_block(sub["fitness_best"], sub["gap_final"], sub["t_exec"], eps))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(group_cols).reset_index(drop=True)


def _write(df: pd.DataFrame, stem: str) -> None:
    df.to_parquet(OUT_DIR / f"{stem}.parquet", index=False)
    df.to_csv(OUT_DIR / f"{stem}.csv", index=False)
    print(f"[01] wrote {stem}: {len(df):>6} rows")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eps", type=float, default=DEFAULT_SUCCESS_EPS,
                        help=f"success threshold on gap_final (default {DEFAULT_SUCCESS_EPS:g}).")
    args = parser.parse_args()

    if not META_PATH.exists():
        raise FileNotFoundError(f"missing input: {META_PATH}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[01] source     : {META_PATH}")
    print(f"[01] output dir : {OUT_DIR}")
    print(f"[01] success eps: {args.eps:g}")

    meta = pd.read_parquet(META_PATH)
    print(f"[01] loaded meta: {len(meta):,} rows")

    # 1) per (mh_raw, function, dim) — the atomic aggregation unit for H2/H4/H5.
    by_ci = _aggregate(meta, ["mh_raw", "mh_family", "n_labels", "rule_set", "function", "dim"], args.eps)
    _write(by_ci, "stats_by_config_instance")

    # 2) per mh (marginal over 62 instances).
    by_c = _aggregate(meta, ["mh_raw", "mh_family", "n_labels", "rule_set"], args.eps)
    _write(by_c, "stats_by_config")

    # 3) PSO_FCS only, marginal (n_labels, rule_set) — for H3 interaction.
    fcs = meta[meta["mh_family"] == "PSO_FCS"]
    by_nR = _aggregate(fcs, ["n_labels", "rule_set"], args.eps)
    _write(by_nR, "stats_by_n_R")

    # 4) per function — problem difficulty ranking.
    by_f = _aggregate(meta, ["function"], args.eps)
    by_f = by_f.assign(_num=by_f["function"].str[1:].astype(int)).sort_values("_num").drop(columns="_num").reset_index(drop=True)
    _write(by_f, "stats_by_function")

    # 5) per dim (F1-F13 scaling only makes sense here).
    by_d = _aggregate(meta, ["dim"], args.eps)
    _write(by_d, "stats_by_dim")

    summary = {
        "eps_success": args.eps,
        "n_experiments": int(len(meta)),
        "n_configs": int(meta["mh_raw"].nunique()),
        "n_instances": int(meta.groupby(["function", "dim"]).ngroups),
        "n_functions": int(meta["function"].nunique()),
        "dims_distinct": sorted(int(x) for x in meta["dim"].unique()),
        "runs_per_config_instance_unique": sorted(int(x) for x in meta.groupby(["mh_raw", "function", "dim"]).size().unique()),
        "success_rate_by_family": {
            fam: float((sub["gap_final"] <= args.eps).mean())
            for fam, sub in meta.groupby("mh_family")
        },
        "gap_final_by_family": {
            fam: {
                "median": float(sub["gap_final"].median()),
                "mean": float(sub["gap_final"].mean()),
                "max": float(sub["gap_final"].max()),
            }
            for fam, sub in meta.groupby("mh_family")
        },
        "best_config_by_mean_gap": (
            by_c.sort_values("gap_mean").iloc[0][["mh_raw", "gap_mean", "gap_median"]].to_dict()
        ),
        "best_config_by_median_gap": (
            by_c.sort_values("gap_median").iloc[0][["mh_raw", "gap_mean", "gap_median"]].to_dict()
        ),
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)
    print(f"[01] wrote summary : summary.json\n")
    print("[01] === SUMMARY ===")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
