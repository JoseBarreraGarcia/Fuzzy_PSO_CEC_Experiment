#!/usr/bin/env python
"""Reproduce descriptive H3 dispersion after aggregating dimensions by function."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
RESULTS = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results"
RANKS = RESULTS / "tests" / "h1_friedman_nemenyi" / "mean_rank_matrix.csv"
INSTANCE_STATS = RESULTS / "level2_aggregated" / "stats_by_config_instance.csv"
MEAN_RANKS = RESULTS / "tests" / "h1_friedman_nemenyi" / "mean_rank_per_config.csv"
MARGINAL_GAPS = RESULTS / "level2_aggregated" / "stats_by_n_R.csv"
OUTPUT = RESULTS / "tests" / "h3_function_dispersion" / "function_dispersion.csv"
GRANULARITIES = [3, 5, 7, 9]
RULES = [f"R{i}" for i in range(1, 9)]
LOG_FLOOR = 1e-12


def main() -> int:
    rank_matrix = pd.read_csv(RANKS)
    rank_long = rank_matrix.melt(
        id_vars="instance", var_name="mh_raw", value_name="rank"
    )
    rank_long = rank_long[rank_long["mh_raw"].str.startswith("PSO_FCS:")].copy()
    rank_long["function"] = rank_long["instance"].str.extract(r"^(F\d+)_")
    rank_long["n_labels"] = rank_long["mh_raw"].str.extract(r"G(\d+)").astype(int)
    rank_long["rule_set"] = rank_long["mh_raw"].str.extract(r":(R\d+):")
    rank_profiles = (
        rank_long.groupby(["function", "n_labels", "rule_set"], observed=True)["rank"]
        .mean()
        .rename("mean_rank_over_dimensions")
        .reset_index()
    )

    instance_stats = pd.read_csv(INSTANCE_STATS)
    gaps = instance_stats[instance_stats["mh_family"].eq("PSO_FCS")].copy()
    gaps["log10_median_gap"] = np.log10(
        np.maximum(gaps["gap_median"].astype(float), LOG_FLOOR) + LOG_FLOOR
    )
    gap_profiles = (
        gaps.groupby(["function", "n_labels", "rule_set"], observed=True)["log10_median_gap"]
        .mean()
        .rename("mean_log10_median_gap_over_dimensions")
        .reset_index()
    )

    profiles = rank_profiles.merge(
        gap_profiles, on=["function", "n_labels", "rule_set"], validate="one_to_one"
    )
    expected = 23 * len(GRANULARITIES) * len(RULES)
    if len(profiles) != expected or set(profiles["rule_set"]) != set(RULES):
        raise ValueError(f"Expected {expected} complete function/configuration profiles; found {len(profiles)}")

    function_dispersion = (
        profiles.groupby(["function", "n_labels"], observed=True)
        .agg(
            rank_sd_across_R=("mean_rank_over_dimensions", "std"),
            loggap_sd_across_R=("mean_log10_median_gap_over_dimensions", "std"),
        )
        .reset_index()
    )
    function_dispersion["subset"] = np.where(
        function_dispersion["function"].str.extract(r"F(\d+)")[0].astype(int) <= 13,
        "S1",
        "S2",
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    function_dispersion.to_csv(OUTPUT, index=False)

    for measure in ("rank_sd_across_R", "loggap_sd_across_R"):
        print(f"\n{measure}: function-level median and mean across functions")
        for subset in ("all", "S1", "S2"):
            selected = function_dispersion
            if subset != "all":
                selected = selected[selected["subset"].eq(subset)]
            summary = selected.groupby("n_labels")[measure].agg(["median", "mean"])
            print(subset, summary.round(4).to_dict(orient="index"))
        wide = function_dispersion.pivot(index="function", columns="n_labels", values=measure)
        monotone = (wide[3] >= wide[5]) & (wide[5] >= wide[7]) & (wide[7] >= wide[9])
        print(
            "all functions: n=9 below n=3:", int((wide[9] < wide[3]).sum()),
            "/", len(wide), "; monotone non-increasing:", int(monotone.sum()), "/", len(wide),
        )

    mean_ranks = pd.read_csv(MEAN_RANKS)
    mean_ranks = mean_ranks[mean_ranks["mh_raw"].str.startswith("PSO_FCS:")].copy()
    mean_ranks["n_labels"] = mean_ranks["mh_raw"].str.extract(r"G(\d+)").astype(int)
    print(
        "\nBenchmark-wide SD across eight mean Friedman ranks:",
        mean_ranks.groupby("n_labels")["mean_rank"].std().round(4).to_dict(),
    )
    marginal_gaps = pd.read_csv(MARGINAL_GAPS)
    print(
        "Benchmark-wide SD across eight pooled median gaps:",
        marginal_gaps.groupby("n_labels")["gap_median"].std().round(4).to_dict(),
    )
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
