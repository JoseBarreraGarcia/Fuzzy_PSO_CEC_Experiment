#!/usr/bin/env python
"""
04_run_scaling_curves.py — dimensional scaling of gap_final over F1-F13.

For each (mh, function) restricted to F1-F13 (the four dims 10/30/50/100) we
report the median gap at each dim and fit a log-log slope
    log10(gap_median + eps) = a + b * log10(dim).
Slope b quantifies how strongly a configuration degrades with dim.

Outputs (results/tests/scaling_curves/):
    scaling_long.{csv,parquet}     long-format (mh, function, dim, gap_median, gap_mean, success)
    scaling_slopes.{csv,parquet}   per (mh, function) log-log slope + R^2
    scaling_slopes_by_mh.csv       aggregated slope by mh (mean/median/std)
    summary.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
L2_PATH = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "level2_aggregated" / "stats_by_config_instance.parquet"
OUT_DIR = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "tests" / "scaling_curves"

SCALABLE = [f"F{i}" for i in range(1, 14)]   # F1..F13
SCALABLE_DIMS = (10, 30, 50, 100)
LOG_FLOOR = 1e-12


def fit_slope(dims: np.ndarray, gap_med: np.ndarray) -> tuple[float, float, float]:
    """Fit log10(gap+eps) = a + b log10(dim); returns (b, intercept, R^2)."""
    x = np.log10(dims.astype(float))
    y = np.log10(np.maximum(gap_med.astype(float), LOG_FLOOR) + LOG_FLOOR)
    n = len(x)
    if n < 2:
        return (float("nan"), float("nan"), float("nan"))
    xm = x.mean()
    ym = y.mean()
    sxx = ((x - xm) ** 2).sum()
    if sxx == 0:
        return (float("nan"), float("nan"), float("nan"))
    b = ((x - xm) * (y - ym)).sum() / sxx
    a = ym - b * xm
    y_hat = a + b * x
    ss_res = ((y - y_hat) ** 2).sum()
    ss_tot = ((y - ym) ** 2).sum()
    r2 = float("nan") if ss_tot == 0 else 1 - ss_res / ss_tot
    return float(b), float(a), r2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metric", choices=["gap_median", "gap_mean"], default="gap_median")
    args = parser.parse_args()

    if not L2_PATH.exists():
        raise FileNotFoundError(f"missing input: {L2_PATH}. Run script 01 first.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[04] source     : {L2_PATH}")
    print(f"[04] output dir : {OUT_DIR}")
    print(f"[04] metric     : {args.metric}")

    df = pd.read_parquet(L2_PATH)
    df = df[df["function"].isin(SCALABLE) & df["dim"].isin(SCALABLE_DIMS)].copy()
    print(f"[04] scalable rows: {len(df):,}  (expected 33 mh x 13 fn x 4 dims = 1716)")

    base_cols = ["mh_raw", "mh_family", "n_labels", "rule_set", "function", "dim",
                 "gap_median", "gap_mean", "success_rate", "median_best"]
    long_cols = list(dict.fromkeys(base_cols + [args.metric]))
    long = df[long_cols].sort_values(["mh_raw", "function", "dim"]).reset_index(drop=True)
    long.to_parquet(OUT_DIR / "scaling_long.parquet", index=False)
    long.to_csv(OUT_DIR / "scaling_long.csv", index=False)
    print(f"[04] wrote scaling_long : {len(long)} rows")

    slopes: list[dict] = []
    for (mh, fn), sub in df.groupby(["mh_raw", "function"], observed=True):
        sub = sub.sort_values("dim")
        b, a, r2 = fit_slope(sub["dim"].to_numpy(), sub[args.metric].to_numpy())
        slopes.append({
            "mh_raw": mh,
            "mh_family": sub["mh_family"].iloc[0],
            "n_labels": sub["n_labels"].iloc[0],
            "rule_set": sub["rule_set"].iloc[0],
            "function": fn,
            "n_points": int(len(sub)),
            "slope_loglog": b,
            "intercept_loglog": a,
            "r2": r2,
        })
    slopes_df = pd.DataFrame(slopes).sort_values(["mh_raw", "function"]).reset_index(drop=True)
    slopes_df.to_parquet(OUT_DIR / "scaling_slopes.parquet", index=False)
    slopes_df.to_csv(OUT_DIR / "scaling_slopes.csv", index=False)
    print(f"[04] wrote scaling_slopes : {len(slopes_df)} rows")

    by_mh = (
        slopes_df.groupby(["mh_raw", "mh_family", "n_labels", "rule_set"], dropna=False)
                 .agg(mean_slope=("slope_loglog", "mean"),
                      median_slope=("slope_loglog", "median"),
                      std_slope=("slope_loglog", "std"),
                      mean_r2=("r2", "mean"),
                      n_functions=("function", "size"))
                 .reset_index()
                 .sort_values("median_slope")
                 .reset_index(drop=True)
    )
    by_mh.to_csv(OUT_DIR / "scaling_slopes_by_mh.csv", index=False)
    print(f"[04] wrote scaling_slopes_by_mh : {len(by_mh)} rows")

    summary = {
        "metric": args.metric,
        "n_scalable_rows": int(len(long)),
        "n_slopes_fitted": int(len(slopes_df)),
        "slope_stats_global": {
            "mean": float(slopes_df["slope_loglog"].mean()),
            "median": float(slopes_df["slope_loglog"].median()),
            "min": float(slopes_df["slope_loglog"].min()),
            "max": float(slopes_df["slope_loglog"].max()),
        },
        "best_scaling_configs": by_mh.head(5).to_dict(orient="records"),
        "worst_scaling_configs": by_mh.tail(5).to_dict(orient="records"),
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)
    print(f"[04] wrote summary : summary.json\n")
    print("[04] === SUMMARY ===")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
