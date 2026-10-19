#!/usr/bin/env python
"""Blocked H3 reanalysis with a two-way function/run-id cluster bootstrap."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.linalg import helmert

ROOT = Path(__file__).resolve().parents[3]
INPUT = ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "level1_raw" / "experiments_meta.parquet"
OUTPUT = ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "tests" / "h3_blocked"
N_LEVELS = [3, 5, 7, 9]
RULE_LEVELS = [f"R{i}" for i in range(1, 9)]
BOOTSTRAP_REPLICATES = 100_000
BOOTSTRAP_SEED = 20261013
BOOTSTRAP_BATCH = 500


def two_way_cluster_bootstrap(
    contrasts: np.ndarray,
    block_index: pd.MultiIndex,
    replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, float | int]:
    """Test a zero mean interaction vector with crossed function/run clusters."""
    mean = contrasts.mean(axis=0)
    centered = contrasts - mean
    functions = block_index.get_level_values("function").to_numpy()
    run_ids = block_index.get_level_values("run_id").to_numpy()
    function_levels = np.unique(functions)
    run_levels = np.unique(run_ids)
    function_count = len(function_levels)
    run_count = len(run_levels)
    block_count, contrast_count = contrasts.shape

    cluster_index = pd.MultiIndex.from_product(
        [function_levels, run_levels], names=["function", "run_id"]
    )
    residual_frame = pd.DataFrame(
        centered,
        index=block_index,
        columns=[f"c{i}" for i in range(contrast_count)],
    ).reset_index()
    cluster_sums = (
        residual_frame.groupby(["function", "run_id"], observed=True)
        [[f"c{i}" for i in range(contrast_count)]]
        .sum()
        .reindex(cluster_index, fill_value=0.0)
    )
    cluster_sums = cluster_sums.to_numpy().reshape(
        function_count, run_count, contrast_count
    )

    size_frame = pd.DataFrame(
        {"function": functions, "run_id": run_ids, "size": np.ones(block_count)}
    )
    cluster_sizes = (
        size_frame.groupby(["function", "run_id"], observed=True)["size"]
        .sum()
        .reindex(cluster_index, fill_value=0.0)
        .to_numpy()
        .reshape(function_count, run_count)
    )

    function_sums = cluster_sums.sum(axis=1)
    run_sums = cluster_sums.sum(axis=0)
    intersection_meat = np.einsum(
        "grq,grs->qs", cluster_sums, cluster_sums
    )
    covariance = (
        function_count / (function_count - 1) * (function_sums.T @ function_sums)
        + run_count / (run_count - 1) * (run_sums.T @ run_sums)
        - (function_count * run_count)
        / (function_count * run_count - 1)
        * intersection_meat
    ) / block_count**2
    variance = np.diag(covariance)
    if np.any(variance <= 0):
        raise ValueError("Two-way cluster covariance has non-positive diagonal entries")

    observed = float(np.sum(mean**2 / variance))
    rng = np.random.default_rng(seed)
    exceedances = 0
    for start in range(0, replicates, BOOTSTRAP_BATCH):
        batch_size = min(BOOTSTRAP_BATCH, replicates - start)
        function_weights = rng.multinomial(
            function_count,
            np.full(function_count, 1 / function_count),
            size=batch_size,
        )
        run_weights = rng.multinomial(
            run_count, np.full(run_count, 1 / run_count), size=batch_size
        )
        bootstrap_sum = np.einsum(
            "bg,grq,br->bq",
            function_weights,
            cluster_sums,
            run_weights,
            optimize=True,
        )
        bootstrap_size = np.einsum(
            "bg,gr,br->b",
            function_weights,
            cluster_sizes,
            run_weights,
            optimize=True,
        )
        bootstrap_mean = bootstrap_sum / bootstrap_size[:, None]
        statistic = np.sum(bootstrap_mean**2 / variance[None, :], axis=1)
        exceedances += int(np.count_nonzero(statistic >= observed - 1e-14))

    p_value = (exceedances + 1) / (replicates + 1)
    return {
        "statistic_diagonal_wald_q": observed,
        "exploratory_p_value": p_value,
        "bootstrap_replicates": replicates,
        "bootstrap_exceedances": exceedances,
        "monte_carlo_se": float(
            np.sqrt(p_value * (1 - p_value) / (replicates + 1))
        ),
        "function_clusters": function_count,
        "run_id_clusters": run_count,
        "paired_blocks": block_count,
        "interaction_contrasts": contrast_count,
    }


def simulate_null_calibration(
    simulations: int = 500,
    bootstrap_replicates: int = 999,
    seed: int = 20261015,
) -> dict[str, dict[str, float | int]]:
    """Estimate finite-cluster rejection rates under synthetic null interactions."""
    function_count, run_count, contrast_count = 23, 31, 21
    instance_counts = np.array([1] * 10 + [4] * 13)
    block_count = int(instance_counts.sum() * run_count)
    rng = np.random.default_rng(seed)
    correlation = 0.35 ** np.abs(
        np.subtract.outer(np.arange(contrast_count), np.arange(contrast_count))
    )
    cholesky = np.linalg.cholesky(correlation)
    function_weights = rng.multinomial(
        function_count,
        np.full(function_count, 1 / function_count),
        size=bootstrap_replicates,
    )
    run_weights = rng.multinomial(
        run_count, np.full(run_count, 1 / run_count), size=bootstrap_replicates
    )
    results: dict[str, dict[str, float | int]] = {}

    for distribution in ("normal", "t4"):
        rejected_bootstrap = 0
        rejected_wald = 0
        for _ in range(simulations):
            function_effect = rng.normal(0, 0.8, (function_count, contrast_count)) @ cholesky.T
            run_effect = rng.normal(0, 0.6, (run_count, contrast_count)) @ cholesky.T
            cluster_sums = np.zeros((function_count, run_count, contrast_count))
            for function_index, instance_count in enumerate(instance_counts):
                if distribution == "t4":
                    errors = rng.standard_t(
                        4, (run_count, instance_count, contrast_count)
                    ) / np.sqrt(2)
                else:
                    errors = rng.normal(
                        size=(run_count, instance_count, contrast_count)
                    )
                errors = errors @ cholesky.T
                values = (
                    function_effect[function_index][None, None, :]
                    + run_effect[:, None, :]
                    + errors
                )
                cluster_sums[function_index] = values.sum(axis=1)

            cell_sizes = np.repeat(instance_counts[:, None], run_count, axis=1).astype(float)
            mean = cluster_sums.sum(axis=(0, 1)) / block_count
            centered = cluster_sums - cell_sizes[:, :, None] * mean[None, None, :]
            function_sums = centered.sum(axis=1)
            run_sums = centered.sum(axis=0)
            intersection = np.einsum("grq,grs->qs", centered, centered)
            covariance = (
                function_count / (function_count - 1) * (function_sums.T @ function_sums)
                + run_count / (run_count - 1) * (run_sums.T @ run_sums)
                - (function_count * run_count)
                / (function_count * run_count - 1)
                * intersection
            ) / block_count**2
            variance = np.diag(covariance)
            if np.any(variance <= 0):
                continue

            wald = float(mean @ np.linalg.solve(covariance, mean))
            wald_p = float(
                stats.f.sf(
                    wald / contrast_count,
                    contrast_count,
                    min(function_count, run_count) - 1,
                )
            )
            rejected_wald += wald_p < 0.05

            bootstrap_sum = np.einsum(
                "bg,grq,br->bq",
                function_weights,
                centered,
                run_weights,
                optimize=True,
            )
            bootstrap_size = np.einsum(
                "bg,gr,br->b",
                function_weights,
                cell_sizes,
                run_weights,
                optimize=True,
            )
            bootstrap_mean = bootstrap_sum / bootstrap_size[:, None]
            bootstrap_stat = np.sum(
                bootstrap_mean**2 / variance[None, :], axis=1
            )
            exceedances = int(np.count_nonzero(bootstrap_stat >= np.sum(mean**2 / variance)))
            bootstrap_p = (exceedances + 1) / (bootstrap_replicates + 1)
            rejected_bootstrap += bootstrap_p < 0.05

        bootstrap_ci = stats.binomtest(
            rejected_bootstrap, simulations
        ).proportion_ci(confidence_level=0.95, method="wilson")
        wald_ci = stats.binomtest(
            rejected_wald, simulations
        ).proportion_ci(confidence_level=0.95, method="wilson")
        results[distribution] = {
            "simulations": simulations,
            "bootstrap_replicates_per_simulation": bootstrap_replicates,
            "bootstrap_rejection_rate": rejected_bootstrap / simulations,
            "bootstrap_rejection_rate_95pct_wilson": [
                bootstrap_ci.low, bootstrap_ci.high
            ],
            "wald_f_rejection_rate": rejected_wald / simulations,
            "wald_f_rejection_rate_95pct_wilson": [wald_ci.low, wald_ci.high],
            "bootstrap_rejections": rejected_bootstrap,
            "wald_f_rejections": rejected_wald,
        }
    return results


def main() -> int:
    if not INPUT.exists():
        raise FileNotFoundError(INPUT)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    data = pd.read_parquet(INPUT)
    data = data.loc[data["mh_family"].eq("PSO_FCS")].copy()
    data["n_labels"] = data["n_labels"].astype(int)
    data["log_gap"] = np.log10(
        np.maximum(data["gap_final"].astype(float), 1e-12) + 1e-12
    )
    data["rank_gap"] = data.groupby(
        ["exp_name", "run_id"], observed=True
    )["gap_final"].rank(method="average", ascending=True)

    expected_configs = len(N_LEVELS) * len(RULE_LEVELS)
    block_counts = data.groupby(["exp_name", "run_id"], observed=True).size()
    if not block_counts.eq(expected_configs).all():
        raise ValueError("Every instance/run block must contain all 32 FCS configurations")
    if data[["n_labels", "rule_set"]].drop_duplicates().shape[0] != expected_configs:
        raise ValueError("Expected exactly 32 distinct factorial configurations")
    runs_per_configuration = data.groupby(
        ["exp_name", "n_labels", "rule_set"], observed=True
    )["run_id"].nunique()
    if runs_per_configuration.nunique() != 1:
        raise ValueError("Every instance/configuration cell must have the same run count")

    column_index = pd.MultiIndex.from_product(
        [N_LEVELS, RULE_LEVELS], names=["n_labels", "rule_set"]
    )
    block_index_names = ["exp_name", "function", "run_id"]
    contrast_basis = np.kron(
        helmert(len(N_LEVELS), full=False).T,
        helmert(len(RULE_LEVELS), full=False).T,
    )
    if not np.allclose(contrast_basis.T @ contrast_basis, np.eye(21)):
        raise ValueError("Interaction contrast basis is not orthonormal")

    results: dict[str, object] = {}
    for response in ("log_gap", "rank_gap"):
        wide = data.pivot(
            index=block_index_names,
            columns=["n_labels", "rule_set"],
            values=response,
        ).reindex(columns=column_index)
        if wide.isna().any().any():
            raise ValueError(f"Incomplete factorial block in {response}")
        contrasts = wide.to_numpy(dtype=float) @ contrast_basis
        test = two_way_cluster_bootstrap(
            contrasts, wide.index, seed=BOOTSTRAP_SEED
        )
        results[response] = test

        if response == "rank_gap":
            interaction_ss = len(wide) * float(
                contrasts.mean(axis=0) @ contrasts.mean(axis=0)
            )
            error_ss = float(
                np.sum((contrasts - contrasts.mean(axis=0)) ** 2)
            )
            test["descriptive_partial_eta_squared"] = interaction_ss / (
                interaction_ss + error_ss
            )

    rank_mean_by_n = (
        data.groupby(["n_labels", "rule_set"], observed=True)["rank_gap"]
        .mean()
        .unstack("rule_set")
        .reindex(index=N_LEVELS, columns=RULE_LEVELS)
    )
    rank_spread_by_n = rank_mean_by_n.std(axis=1, ddof=1)
    pd.DataFrame(
        {
            "n_labels": N_LEVELS,
            "std_mean_rank_across_rule_patterns": [
                float(rank_spread_by_n.loc[n]) for n in N_LEVELS
            ],
        }
    ).to_csv(OUTPUT / "rank_spread_by_granularity.csv", index=False)
    rank_mean_by_n.to_csv(OUTPUT / "mean_rank_by_granularity_and_rule.csv")

    summary = {
        "method": "exploratory two-way function x run_id pigeonhole bootstrap with finite-cluster null calibration",
        "estimand": "interaction in within-block relative configuration ranks and log-gap across n and rule pattern",
        "source": str(INPUT.relative_to(ROOT)),
        "fcs_observations": int(len(data)),
        "instances": int(data["exp_name"].nunique()),
        "functions": int(data["function"].nunique()),
        "runs_per_instance_config": int(runs_per_configuration.min()),
        "configurations_per_block": expected_configs,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_batch_size": BOOTSTRAP_BATCH,
        "tests": results,
        "null_calibration": simulate_null_calibration(),
        "rank_spread_by_granularity": {
            str(n): float(rank_spread_by_n.loc[n]) for n in N_LEVELS
        },
        "rank_spread_decreases_monotonically": bool(
            rank_spread_by_n.is_monotonic_decreasing
        ),
        "interpretation": "Bootstrap p-values are exploratory and require independent statistical review. The Wald F approximation is not used because null simulations show severe Type-I error inflation.",
    }
    with (OUTPUT / "summary.json").open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())