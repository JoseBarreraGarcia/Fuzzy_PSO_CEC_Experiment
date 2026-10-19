#!/usr/bin/env python
"""Build a versioned final dataset and recalculate F14-affected paper analyses.

This script never writes to historical databases, analysis outputs, or manuscript
files. Run it from any working directory with the repository's ``env`` Python.
It streams the 63M-row historical iteration parquet and substitutes corrected
F14 iteration blobs for dynamics summaries and figures.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import scikit_posthocs as sph
from scipy.stats import friedmanchisquare, kendalltau, mannwhitneyu, wilcoxon


ROOT = Path(__file__).resolve().parents[3]
MDPI = ROOT / "FUZZY" / "ARTICULO_MDPI"
RESULTS = MDPI / "results"
OUT = RESULTS / "final_dataset_20261015"
HIST_META = RESULTS / "level1_raw" / "experiments_meta.parquet"
HIST_ITER = RESULTS / "level1_raw" / "iterations.parquet"
CORRECTED_F14 = RESULTS / "f14_corrected_20261014" / "corrected_f14_level1.csv"
F14_DB = RESULTS / "f14_corrected_20261014" / "BD" / "resultados.db"
F14_VALIDATION = RESULTS / "f14_corrected_20261014" / "validation_report.json"
ARCHIVE_DB = ROOT / "BD" / "resultados.db"
MANUSCRIPT_RESULTS = MDPI / "manuscript" / "sections" / "05_results.tex"
ALPHA = 0.05
BONF_FAMILY = 32 * 62
BONF_ALPHA = ALPHA / BONF_FAMILY
LOG_FLOOR = 1e-12
GRANULARITIES = [3, 5, 7, 9]
RULES = [f"R{i}" for i in range(1, 9)]
MIRROR_PAIRS = [("R1", "R2"), ("R3", "R4"), ("R5", "R8"), ("R6", "R7")]
SINGLE_AXIS_PAIRS = [("R5", "R7"), ("R6", "R8"), ("R5", "R6"), ("R7", "R8")]
RULE_PAIRS = [("mirror", *p) for p in MIRROR_PAIRS] + [("single-axis", *p) for p in SINGLE_AXIS_PAIRS]
CLASS_SHORT = {
    "unimodal": "Unimodal",
    "multimodal": "Scalable multimodal",
    "composed": "Fixed-dimensional",
}
PROGRESS = {"R1": "decreasing", "R2": "increasing", "R3": "neutral", "R4": "neutral",
            "R5": "decreasing", "R6": "decreasing", "R7": "increasing", "R8": "increasing"}
COLORS = {"decreasing": "#167d74", "neutral": "#c27a23", "increasing": "#a94747"}
STYLES = {"decreasing": "-", "neutral": "--", "increasing": ":"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_json(value):
    if isinstance(value, pd.DataFrame):
        return safe_json(value.to_dict(orient="records"))
    if isinstance(value, pd.Series):
        return safe_json(value.to_dict())
    if isinstance(value, dict):
        return {str(k): safe_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe_json(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(safe_json(payload), indent=2), encoding="utf-8")


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    frame.to_csv(path, index=False)


def config_id(mh: str) -> str:
    if mh == "PSO":
        return "PSO"
    match = re.search(r"G(\d+).*?:(R\d+)", mh)
    if match:
        return f"FCS-{match.group(1)}-{match.group(2)}"
    match = re.search(r"PSO_FCS:O\d+:(\d+):I\d+:(R\d+)", mh)
    if match:
        return f"FCS-{match.group(1)}-{match.group(2)}"
    raise ValueError(f"Cannot normalize configuration ID: {mh}")


def landscape_class(function: str) -> str:
    number = int(function[1:])
    if number <= 7:
        return "unimodal"
    if number <= 13:
        return "multimodal"
    return "composed"


def subset(function: str) -> str:
    return "S1" if int(function[1:]) <= 13 else "S2"


def instance_label(function: str, dim: int) -> str:
    return f"{function}_D{int(dim)}"


def make_consolidated() -> tuple[pd.DataFrame, dict]:
    for path in (HIST_META, HIST_ITER, CORRECTED_F14, F14_DB, F14_VALIDATION,
                 ARCHIVE_DB, MANUSCRIPT_RESULTS):
        if not path.exists():
            raise FileNotFoundError(path)
    validation = json.loads(F14_VALIDATION.read_text(encoding="utf-8"))
    if validation.get("passed") is not True or validation.get("completed_runs") != 1023:
        raise ValueError("Corrected F14 dataset has no passing 1,023-run validation report")

    historical_all = pd.read_parquet(HIST_META)
    if len(historical_all) != 63_426:
        raise ValueError(f"Expected 63,426 historical level-1 rows; got {len(historical_all)}")
    historical_f14 = historical_all.loc[historical_all["function"].eq("F14")].copy()
    historical = historical_all.loc[~historical_all["function"].eq("F14")].copy()
    corrected = pd.read_csv(CORRECTED_F14)
    if len(historical) != 62_403 or len(corrected) != 1_023:
        raise ValueError(f"Unexpected source counts: historical={len(historical)}, corrected F14={len(corrected)}")
    if not corrected["function"].eq("F14").all() or not corrected["dim"].eq(2).all():
        raise ValueError("Corrected source contains records outside F14_D2")
    if corrected["historical_exp_id"].duplicated().any():
        raise ValueError("Corrected F14 source contains duplicate historical IDs")
    if set(historical["id_exp"].astype(int)) & set(corrected["historical_exp_id"].astype(int)):
        raise ValueError("Historical and corrected sources overlap on experiment IDs")

    # Preserve the exporter's synthetic metadata, but do not mislabel it as the actual seed.
    historical["historical_exp_id"] = historical["id_exp"].astype("int64")
    historical["configuration_id"] = historical["mh_raw"].map(config_id)
    historical["benchmark_instance"] = [instance_label(f, d)
                                         for f, d in zip(historical["function"], historical["dim"])]
    historical["seed_exporter_synthetic"] = historical["seed"]
    historical["actual_seed"] = 42 + historical["historical_exp_id"].astype("int64")
    historical["seed"] = historical["actual_seed"]
    historical["seed_source"] = "reconstructed_from_verified_runner_formula; not stored in historical DB"
    historical["source_version"] = "historical_level1_excluding_F14"

    corrected["historical_exp_id"] = corrected["historical_exp_id"].astype("int64")
    if not np.array_equal(corrected["historical_exp_id"], corrected["id_exp"].astype("int64")):
        raise ValueError("Corrected F14 export ID does not preserve historical_exp_id")
    if not np.array_equal(corrected["actual_seed"].astype("int64"),
                           42 + corrected["historical_exp_id"]):
        raise ValueError("Corrected F14 actual seeds do not match 42 + historical_exp_id")
    corrected["configuration_id"] = corrected["configuration_id"].astype(str)
    if not corrected["configuration_id"].eq(corrected["mh_raw"].map(config_id)).all():
        raise ValueError("Corrected F14 configuration labels do not normalize consistently")
    corrected["benchmark_instance"] = "F14_D2"
    corrected["seed_exporter_synthetic"] = pd.Series(np.nan, index=corrected.index)
    corrected["seed"] = corrected["actual_seed"].astype("Int64")
    corrected["actual_seed"] = corrected["actual_seed"].astype("Int64")
    corrected["seed_source"] = "recovered_from_original_global_exp_id_and_verified_runner"
    corrected["source_version"] = "corrected_F14_rerun_20261014"

    # Recover stable instance IDs from the untouched archive in read-only mode.
    uri = f"file:{ARCHIVE_DB.as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        instance_rows = connection.execute(
            "SELECT id_instancia,nombre FROM instancias WHERE tipo_problema='BEN'"
        ).fetchall()
    finally:
        connection.close()
    instance_ids = {name: int(instance_id) for instance_id, name in instance_rows}
    historical["instance_id"] = historical["function"].map(instance_ids).astype("int64")
    corrected["instance_id"] = corrected["instance_id"].astype("int64")

    frame = pd.concat([historical, corrected], ignore_index=True, sort=False)
    frame["id_exp"] = frame["historical_exp_id"].astype("int64")
    frame["run_id"] = frame["run_id"].astype("int64")
    frame["dim"] = frame["dim"].astype("int64")
    frame["n_labels"] = pd.to_numeric(frame["n_labels"], errors="coerce").astype("Int64")
    frame["rule_set"] = frame["rule_set"].fillna("-").astype(str)
    frame["configuration_id"] = frame["configuration_id"].astype(str)
    frame["benchmark_instance"] = frame["benchmark_instance"].astype(str)
    frame["instance_id"] = frame["instance_id"].astype("int64")
    frame["problem_class"] = frame["function"].map(landscape_class)
    frame["subgroup"] = frame["function"].map(subset)

    if len(frame) != 63_426 or frame["historical_exp_id"].nunique() != 63_426:
        raise ValueError("Consolidated row count/experiment ID uniqueness check failed")
    if frame["configuration_id"].nunique() != 33 or frame["benchmark_instance"].nunique() != 62:
        raise ValueError("Consolidated configuration or instance count is not 33 × 62")
    group_counts = frame.groupby(["configuration_id", "benchmark_instance"]).agg(
        n=("historical_exp_id", "size"), runs=("run_id", "nunique"),
        id_unique=("historical_exp_id", "nunique"),
    )
    if (len(group_counts) != 2_046 or not group_counts["n"].eq(31).all()
            or not group_counts["runs"].eq(31).all() or not group_counts["id_unique"].eq(31).all()):
        raise ValueError("Expected exactly 2,046 configuration-instance groups of 31 distinct runs")
    for field in ("historical_exp_id", "configuration_id", "instance_id", "benchmark_instance",
                  "function", "dim", "run_id", "fitness_best", "gap_final", "t_exec", "seed_source"):
        if frame[field].isna().any():
            raise ValueError(f"Required consolidated field has missing values: {field}")
    if not frame.loc[frame.function.eq("F14"), "actual_seed"].notna().all():
        raise ValueError("Corrected F14 actual seed provenance is incomplete")
    historical_seed_rows=frame.loc[~frame.function.eq("F14")]
    if not (historical_seed_rows.actual_seed.astype("int64") ==
            42 + historical_seed_rows.historical_exp_id.astype("int64")).all():
        raise ValueError("Reconstructed historical seed formula mismatch")
    if frame["fitness_best"].isna().any() or frame["t_exec"].isna().any():
        raise ValueError("Consolidated fitness or runtime contains missing values")

    original_paired = pd.read_csv(RESULTS / "tests" / "h4_wilcoxon_vs_baseline" / "wilcoxon_pairs.csv")
    original_rule = pd.read_csv(RESULTS / "level3_rankings" / "rule_pair_per_instance.csv")
    validation_meta = {
        "output_version": OUT.name,
        "historical_source_rows_total": len(historical_all),
        "historical_non_F14_rows_used": len(historical),
        "corrected_F14_rows_used": len(corrected),
        "consolidated_rows": len(frame),
        "unique_historical_exp_ids": int(frame.historical_exp_id.nunique()),
        "benchmark_instances": int(frame.benchmark_instance.nunique()),
        "configurations": int(frame.configuration_id.nunique()),
        "configuration_instance_groups": int(len(group_counts)),
        "runs_per_group": sorted(frame.groupby(["configuration_id", "benchmark_instance"]).size().unique().tolist()),
        "missing_actual_seeds_historical": int(frame.loc[~frame.function.eq("F14"), "actual_seed"].isna().sum()),
        "historical_actual_seeds_persisted": 0,
        "historical_actual_seeds_reconstructed_from_verified_runner": int((~frame.function.eq("F14")).sum()),
        "F14_actual_seeds": int(frame.loc[frame.function.eq("F14"), "actual_seed"].notna().sum()),
        "historical_synthetic_seed_values_preserved": int(frame["seed_exporter_synthetic"].notna().sum()),
        "original_RQ4_rows": len(original_paired),
        "original_rule_pair_rows": len(original_rule),
        "F14_validation_report": validation,
        "source_sha256": {
            "historical_level1_parquet": sha256(HIST_META),
            "corrected_F14_level1_csv": sha256(CORRECTED_F14),
            "historical_iterations_parquet": sha256(HIST_ITER),
            "original_rule_outputs": sha256(RESULTS / "level3_rankings" / "rule_pair_per_instance.csv"),
            "original_H4_outputs": sha256(RESULTS / "tests" / "h4_wilcoxon_vs_baseline" / "wilcoxon_pairs.csv"),
        },
        "pairing_policy": "Run-level comparisons use independent samples; historical actual seeds are reconstructed only where the verified runner formula and global IDs permit. No run_id pairing is treated as common-seed pairing.",
    }
    return frame, validation_meta


def compute_stats_by_instance(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    keys = ["configuration_id", "mh_raw", "mh_family", "n_labels", "rule_set",
            "benchmark_instance", "function", "dim", "problem_class", "subgroup"]
    for group_keys, block in frame.groupby(keys, dropna=False, observed=True, sort=True):
        row = dict(zip(keys, group_keys))
        gap = block.gap_final.astype(float)
        fitness = block.fitness_best.astype(float)
        runtime = block.t_exec.astype(float)
        row.update({
            "n_runs": len(block),
            "gap_mean": float(gap.mean()),
            "gap_median": float(gap.median()),
            "gap_std": float(gap.std(ddof=1)),
            "fitness_mean": float(fitness.mean()),
            "fitness_median": float(fitness.median()),
            "fitness_std": float(fitness.std(ddof=1)),
            "fitness_min": float(fitness.min()),
            "runtime_median": float(runtime.median()),
            "runtime_mean": float(runtime.mean()),
        })
        rows.append(row)
    return pd.DataFrame(rows)


def nemenyi_cd(ranks: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    columns = list(ranks.columns)
    matrix = ranks.to_numpy(dtype=float)
    friedman_stat, friedman_p = friedmanchisquare(*[ranks[c].to_numpy() for c in columns])
    pvalues = sph.posthoc_nemenyi_friedman(matrix)
    pvalues.index = columns
    pvalues.columns = columns
    q_table = {
        2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850, 7: 2.949, 8: 3.031, 9: 3.102,
        10: 3.164, 11: 3.219, 12: 3.268, 13: 3.313, 14: 3.354, 15: 3.391, 16: 3.426,
        17: 3.458, 18: 3.489, 19: 3.517, 20: 3.544, 21: 3.569, 22: 3.593, 23: 3.616,
        24: 3.637, 25: 3.658, 26: 3.678, 27: 3.696, 28: 3.714, 29: 3.732, 30: 3.749,
        31: 3.765, 32: 3.780, 33: 3.795, 34: 3.810, 35: 3.824,
    }
    k, n = ranks.shape[1], ranks.shape[0]
    q = q_table.get(k, 4.0)
    cd = q * math.sqrt(k * (k + 1) / (6 * n))
    mean_ranks = ranks.mean(axis=0).rename("mean_rank").reset_index()
    mean_ranks.columns = ["configuration_id", "mean_rank"]
    mean_ranks = mean_ranks.sort_values("mean_rank").reset_index(drop=True)
    report = {
        "metric": "median_normalized_gap_over_31_runs",
        "alpha": ALPHA,
        "friedman_chi2": float(friedman_stat),
        "friedman_df": k - 1,
        "friedman_p": float(friedman_p),
        "friedman_reject_equal_configuration_ranks": bool(friedman_p < ALPHA),
        "n_instances": n,
        "n_configurations": k,
        "nemenyi_significant_pairs": int(sum(pvalues.iloc[i, j] < ALPHA
            for i in range(k) for j in range(i + 1, k))),
        "cd": cd,
        "cd_q_alpha": q,
        "best": mean_ranks.iloc[0].to_dict(),
        "worst": mean_ranks.iloc[-1].to_dict(),
    }
    return pvalues, report


def a12(first: np.ndarray, second: np.ndarray) -> float:
    return float(((first[:, None] < second[None, :]).sum()
                  + 0.5 * (first[:, None] == second[None, :]).sum())
                 / (first.size * second.size))


def test_category(p: float, effect: float, alpha: float, first: str, second: str) -> str:
    if not np.isfinite(p) or p >= alpha:
        return "tie"
    return first if effect > 0.5 else second


def mann_whitney(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    if np.all(x == x[0]) and np.all(y == y[0]) and x[0] == y[0]:
        return float("nan"), 1.0
    result = mannwhitneyu(x, y, alternative="two-sided", method="asymptotic", use_continuity=True)
    p = float(result.pvalue)
    return float(result.statistic), (p if np.isfinite(p) else 1.0)


def h4_tests(frame: pd.DataFrame, old_pairs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    baseline = frame[frame.configuration_id.eq("PSO")]
    rows = []
    old = old_pairs.copy()
    old["configuration_id"] = old["mh_raw"].map(config_id)
    for cfg in sorted(frame.configuration_id.unique()):
        if cfg == "PSO":
            continue
        cdf = frame[frame.configuration_id.eq(cfg)]
        for inst in sorted(cdf.benchmark_instance.unique()):
            xblock = cdf[cdf.benchmark_instance.eq(inst)].sort_values("run_id")
            yblock = baseline[baseline.benchmark_instance.eq(inst)].sort_values("run_id")
            if len(xblock) != 31 or len(yblock) != 31:
                raise ValueError(f"Expected 31 independent observations in H4 {cfg}/{inst}")
            x, y = xblock.fitness_best.to_numpy(float), yblock.fitness_best.to_numpy(float)
            u, p = mann_whitney(x, y)
            effect = a12(x, y)
            nominal = test_category(p, effect, ALPHA, "win", "loss")
            bonf = test_category(p, effect, BONF_ALPHA, "win", "loss")
            old_row = old[old.configuration_id.eq(cfg) & old.instance.eq(inst)]
            if len(old_row) != 1:
                raise ValueError(f"Historical H4 output row missing/duplicated: {cfg}/{inst}")
            old_row = old_row.iloc[0]
            rows.append({
                "configuration_id": cfg, "mh_raw": xblock.mh_raw.iloc[0],
                "n_labels": int(xblock.n_labels.iloc[0]) if pd.notna(xblock.n_labels.iloc[0]) else None,
                "rule_set": xblock.rule_set.iloc[0], "benchmark_instance": inst,
                "n_fcs": len(x), "n_pso": len(y), "mann_whitney_u": u,
                "mann_whitney_p_two_sided": p, "a12_fcs_vs_pso": effect,
                "independent_nominal": nominal, "independent_bonferroni": bonf,
                "historical_paired_wilcoxon_p": float(old_row.p_value),
                "historical_paired_a12": float(old_row.a12),
                "historical_nominal": old_row["direction_alpha_0.05"],
                "historical_bonferroni": old_row["direction_bonferroni"],
                "nominal_changed": nominal != old_row["direction_alpha_0.05"],
                "bonferroni_changed": bonf != old_row["direction_bonferroni"],
                "a12_changed_after_f14_correction": not np.isclose(effect, old_row.a12, atol=1e-12, rtol=0),
            })
    detail = pd.DataFrame(rows)
    summary_rows = []
    for cfg, block in detail.groupby("configuration_id", sort=True):
        row = {"configuration_id": cfg, "n_instances": len(block),
               "n_labels": block.n_labels.iloc[0], "rule_set": block.rule_set.iloc[0]}
        for label, column in (("independent_nominal", "independent_nominal"),
                              ("independent_bonferroni", "independent_bonferroni"),
                              ("historical_paired_nominal", "historical_nominal"),
                              ("historical_paired_bonferroni", "historical_bonferroni")):
            counts = block[column].value_counts().to_dict()
            row.update({f"{label}_{key}": int(counts.get(value, 0)) for key, value in
                        (("wins", "win"), ("ties", "tie"), ("losses", "loss"))})
        row["a12_mean"] = float(block.a12_fcs_vs_pso.mean())
        row["a12_median"] = float(block.a12_fcs_vs_pso.median())
        row["nominal_classifications_changed"] = int(block.nominal_changed.sum())
        row["bonferroni_classifications_changed"] = int(block.bonferroni_changed.sum())
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows).sort_values(
        ["independent_bonferroni_wins", "independent_nominal_wins", "a12_mean"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    total = {
        "n_tests": len(detail), "alpha": ALPHA, "bonferroni_family": BONF_FAMILY,
        "bonferroni_alpha": BONF_ALPHA,
        "historical_paired_nominal": detail.historical_nominal.value_counts().to_dict(),
        "independent_nominal": detail.independent_nominal.value_counts().to_dict(),
        "historical_paired_bonferroni": detail.historical_bonferroni.value_counts().to_dict(),
        "independent_bonferroni": detail.independent_bonferroni.value_counts().to_dict(),
        "nominal_classifications_changed": int(detail.nominal_changed.sum()),
        "bonferroni_classifications_changed": int(detail.bonferroni_changed.sum()),
        "a12_changes_after_f14_correction": int(detail.a12_changed_after_f14_correction.sum()),
        "a12_max_abs_change_vs_historical": float(np.max(np.abs(
            detail.a12_fcs_vs_pso - detail.historical_paired_a12))),
    }
    return detail, summary, total


def rule_pair_tests(frame: pd.DataFrame, old_detail: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    rows = []
    archive = old_detail.copy()
    for kind, first, second in RULE_PAIRS:
        for n in GRANULARITIES:
            for inst in sorted(frame.benchmark_instance.unique()):
                block_a = frame[frame.configuration_id.eq(f"FCS-{n}-{first}") & frame.benchmark_instance.eq(inst)].sort_values("run_id")
                block_b = frame[frame.configuration_id.eq(f"FCS-{n}-{second}") & frame.benchmark_instance.eq(inst)].sort_values("run_id")
                if len(block_a) != 31 or len(block_b) != 31:
                    raise ValueError(f"Expected 31 independent samples in rule contrast {first}/{second}/{n}/{inst}")
                x, y = block_a.fitness_best.to_numpy(float), block_b.fitness_best.to_numpy(float)
                u, p = mann_whitney(x, y)
                effect = a12(x, y)
                winner = test_category(p, effect, ALPHA, first, second)
                original = archive[(archive.pair.eq(f"{first} vs {second}"))
                                   & archive.n_labels.eq(n) & archive.instance.eq(inst)]
                if len(original) != 1:
                    raise ValueError(f"Historical Table 11 row missing/duplicated: {first}/{second}/{n}/{inst}")
                original = original.iloc[0]
                # Audit the archived paired test against this source only; it is not treated as a valid test.
                if np.allclose(x, y):
                    current_paired = 1.0
                else:
                    try:
                        current_paired = float(wilcoxon(x, y, alternative="two-sided", zero_method="wilcox").pvalue)
                    except ValueError:
                        current_paired = 1.0
                rows.append({
                    "kind": kind, "pair": f"{first} vs {second}", "rule_a": first, "rule_b": second,
                    "n_labels": n, "benchmark_instance": inst, "function": block_a.function.iloc[0],
                    "problem_class": block_a.problem_class.iloc[0], "n_first": len(x), "n_second": len(y),
                    "mann_whitney_u": u, "mann_whitney_p_two_sided": p,
                    "a12_first_vs_second": effect, "independent_winner": winner,
                    "archived_a12": float(original.a12), "archived_paired_p": float(original.p_value),
                    "current_paired_p_audit_only": current_paired,
                    "archived_a12_mismatch": not np.isclose(effect, float(original.a12), atol=1e-12, rtol=0),
                    "archived_p_mismatch_vs_current_paired": not np.isclose(current_paired, float(original.p_value), atol=1e-10, rtol=0),
                })
    detail = pd.DataFrame(rows)
    summaries = []
    archived_summary = pd.read_csv(RESULTS / "level3_rankings" / "rule_pair_summary.csv")
    for (kind, pair), block in detail.groupby(["kind", "pair"], sort=False):
        first, second = pair.split(" vs ")
        counts = block.independent_winner.value_counts().to_dict()
        first_w, second_w = int(counts.get(first, 0)), int(counts.get(second, 0))
        dominant = first if first_w > second_w else second if second_w > first_w else "--"
        if dominant == "--":
            strongest = "--"
        else:
            rates = block.groupby("problem_class").independent_winner.apply(lambda s: float(s.eq(dominant).mean()))
            strongest = rates.idxmax()
        old = archived_summary[archived_summary.pair.eq(pair)].iloc[0]
        summaries.append({
            "kind": kind, "pair": pair, "n_comparisons": len(block),
            "archived_first_wins": int(old.wins_a), "archived_ties": int(old.ties),
            "archived_second_wins": int(old.wins_b),
            "independent_first_wins": first_w, "independent_ties": int(counts.get("tie", 0)),
            "independent_second_wins": second_w, "independent_dominant": dominant,
            "archived_a12_median": float(old.a12_median),
            "independent_a12_median": float(block.a12_first_vs_second.median()),
            "archived_strongest_class": old.best_class,
            "independent_strongest_class": strongest,
            "archived_a12_mismatches": int(block.archived_a12_mismatch.sum()),
            "archived_p_mismatches_vs_paired_recalc": int(block.archived_p_mismatch_vs_current_paired.sum()),
        })
    summary = pd.DataFrame(summaries)
    discrepancy = {
        "archived_table_rows": len(archive),
        "a12_mismatch_rows_against_corrected_dataset": int(detail.archived_a12_mismatch.sum()),
        "p_mismatch_rows_against_current_paired_recalculation": int(detail.archived_p_mismatch_vs_current_paired.sum()),
        "rows_with_either_mismatch": int((detail.archived_a12_mismatch | detail.archived_p_mismatch_vs_current_paired).sum()),
        "interpretation": "Historical Table 11 outputs do not fully reproduce from the current consolidated scores. A12 differences cannot be caused by paired versus independent p-value choice; archived inputs/code revision remains to be reconciled.",
    }
    return detail, summary, discrepancy


def function_level_tables(stats_ci: pd.DataFrame, h4_detail: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    stats_ci = stats_ci.copy()
    if "rank" not in stats_ci.columns:
        stats_ci["rank"] = stats_ci.groupby("benchmark_instance", observed=True).gap_median.rank(
            method="average", ascending=True
        )
    rows = []
    for inst, block in stats_ci.groupby("benchmark_instance", sort=True):
        pso = block[block.configuration_id.eq("PSO")].iloc[0]
        fcs = block[block.mh_family.eq("PSO_FCS")]
        best = fcs.sort_values(["rank", "n_labels", "rule_set"]).iloc[0]
        tied = int(fcs["rank"].eq(best["rank"]).sum())
        test = h4_detail[(h4_detail.configuration_id.eq(best.configuration_id))
                         & h4_detail.benchmark_instance.eq(inst)].iloc[0]
        gap_pso, gap_fcs = float(pso.gap_median), float(best.gap_median)
        rows.append({
            "benchmark_instance": inst, "function": best.function, "dim": int(best.dim),
            "problem_class": best.problem_class, "subgroup": best.subgroup,
            "best_fcs": best.configuration_id, "best_n": int(best.n_labels), "best_rule": best.rule_set,
            "n_tied_at_best": tied, "rank_pso": int(pso["rank"]), "rank_best_fcs": int(best["rank"]),
            "gap_pso": gap_pso, "gap_best_fcs": gap_fcs,
            "improvement_pct": (gap_pso-gap_fcs)/gap_pso*100 if gap_pso>0 else np.nan,
            "independent_mw_p": float(test.mann_whitney_p_two_sided),
            "a12": float(test.a12_fcs_vs_pso),
            "winner_family": "PSO_FCS" if int(best["rank"]) < int(pso["rank"]) else
                             "PSO" if int(pso["rank"]) < int(best["rank"]) else "tie",
        })
    per_instance = pd.DataFrame(rows)
    per_function_rows = []
    for function, block in per_instance.groupby("function", sort=True):
        counts = block.best_fcs.value_counts()
        all_tied = bool(block.rank_best_fcs.eq(1).all() & block.rank_pso.eq(1).all())
        if all_tied:
            best_cfg = "--"
            best_n = best_rule = None
        else:
            top_count = counts.max()
            candidates = counts[counts.eq(top_count)].index.tolist()
            if len(candidates)>1:
                mean_rank_for_candidate = {cfg: float(block.loc[block.best_fcs.eq(cfg), "rank_best_fcs"].mean())
                                           for cfg in candidates}
                best_cfg = min(mean_rank_for_candidate, key=mean_rank_for_candidate.get)
            else:
                best_cfg = candidates[0]
            chosen = block[block.best_fcs.eq(best_cfg)].iloc[0]
            best_n, best_rule = int(chosen.best_n), chosen.best_rule
        per_function_rows.append({
            "function": function, "problem_class": block.problem_class.iloc[0],
            "subgroup": block.subgroup.iloc[0], "n_instances": len(block),
            "all_tied": all_tied, "best_fcs": best_cfg, "best_n": best_n, "best_rule": best_rule,
            "rank_pso_median": float(block.rank_pso.median()),
            "rank_best_fcs_median": float(block.rank_best_fcs.median()),
            "fcs_wins": int(block.winner_family.eq("PSO_FCS").sum()),
            "significant_wins_independent": int(((block.winner_family=="PSO_FCS")
                & (block.independent_mw_p<ALPHA)).sum()),
            "a12_median": float(block.a12.median()),
        })
    return per_instance, pd.DataFrame(per_function_rows)


def runtime_unpaired(frame: pd.DataFrame, per_function: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in per_function.itertuples(index=False):
        if row.best_fcs == "--":
            continue
        pso = frame[(frame.function.eq(row.function)) & frame.configuration_id.eq("PSO")].t_exec.astype(float)
        fcs = frame[(frame.function.eq(row.function)) & frame.configuration_id.eq(row.best_fcs)].t_exec.astype(float)
        if not len(pso) or not len(fcs):
            raise ValueError(f"Missing runtime sample for {row.function}/{row.best_fcs}")
        median_pso, median_fcs = float(pso.median()), float(fcs.median())
        rows.append({
            "function": row.function, "best_fcs": row.best_fcs,
            "n_pso_independent": len(pso), "n_fcs_independent": len(fcs),
            "pso_median_seconds": median_pso, "fcs_median_seconds": median_fcs,
            "unpaired_ratio_of_medians_overhead_pct": (median_fcs/median_pso-1)*100,
            "method": "100*(median(FCS time)/median(PSO time)-1); no run_id join",
        })
    return pd.DataFrame(rows)


def summarize_rq3(frame: pd.DataFrame, stats_ci: pd.DataFrame, ranks: pd.DataFrame) -> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame,dict]:
    rank_long = ranks.rename_axis("benchmark_instance").reset_index().melt(
        id_vars="benchmark_instance", var_name="configuration_id", value_name="rank")
    info=frame[["configuration_id","n_labels","rule_set"]].drop_duplicates()
    rank_long=rank_long.merge(info,on="configuration_id",validate="many_to_one")
    rank_long["function"]=rank_long["benchmark_instance"].str.extract(r"^(F\d+)_")
    rank_profiles=rank_long.groupby(["function","n_labels","rule_set"],observed=True)["rank"].mean().rename("mean_rank_over_dimensions").reset_index()
    gaps=stats_ci[stats_ci.mh_family.eq("PSO_FCS")].copy()
    gaps["log10_median_gap"]=np.log10(np.maximum(gaps.gap_median.astype(float),LOG_FLOOR)+LOG_FLOOR)
    gap_profiles=gaps.groupby(["function","n_labels","rule_set"],observed=True).log10_median_gap.mean().rename("mean_log10_median_gap_over_dimensions").reset_index()
    profiles=rank_profiles.merge(gap_profiles,on=["function","n_labels","rule_set"],validate="one_to_one")
    if len(profiles)!=23*4*8: raise ValueError(f"Incomplete RQ3 profiles: {len(profiles)}")
    dispersion=profiles.groupby(["function","n_labels"],observed=True).agg(
        rank_sd_across_R=("mean_rank_over_dimensions","std"),
        loggap_sd_across_R=("mean_log10_median_gap_over_dimensions","std")).reset_index()
    dispersion["subgroup"]=dispersion.function.map(subset)
    # Match the manuscript's benchmark-wide rank aggregation: equal weight per instance (62 blocks).
    by_rule=rank_long.groupby(["n_labels","rule_set"],observed=True)["rank"].mean().unstack("rule_set").reindex(index=GRANULARITIES,columns=RULES)
    gran_rows=[]
    for rule in RULES:
        vals=by_rule.loc[:,rule].to_numpy(float)
        gran_rows.append({"rule_set":rule,**{f"mean_rank_n{n}":float(by_rule.loc[n,rule]) for n in GRANULARITIES},
                          "best_n":GRANULARITIES[int(np.argmin(vals))],"spread":float(vals.max()-vals.min())})
    granularity=pd.DataFrame(gran_rows)
    raw=frame[frame.mh_family.eq("PSO_FCS")].copy()
    raw["log_gap_run"]=np.log10(np.maximum(raw.gap_final.astype(float),LOG_FLOOR)+LOG_FLOOR)
    pooled=raw.groupby("n_labels").log_gap_run.agg(
        median="median",q1=lambda x:x.quantile(.25),q3=lambda x:x.quantile(.75),
        mean="mean",std="std",n="size").reset_index()
    pooled["iqr"]=pooled.q3-pooled.q1
    gap_medians_nr=raw.groupby(["n_labels","rule_set"],observed=True).gap_final.median().unstack("rule_set").reindex(index=GRANULARITIES,columns=RULES)
    aggregate_rows=[]
    for n in GRANULARITIES:
        y=raw.loc[raw.n_labels.eq(n),"log_gap_run"].to_numpy(dtype=float)
        ranks_n=by_rule.loc[n].to_numpy(dtype=float)
        gaps_n=gap_medians_nr.loc[n].to_numpy(dtype=float)
        aggregate_rows.append({
            "n_labels":n,
            "mean_rank_over_rules":float(ranks_n.mean()),
            "best_rule_rank":float(ranks_n.min()),
            "std_rank_across_rules":float(ranks_n.std(ddof=1)),
            "median_log_gap":float(np.median(y)),
            "iqr_log_gap":float(np.quantile(y,.75)-np.quantile(y,.25)),
            "std_gap_median_across_rules":float(gaps_n.std(ddof=1)),
        })
    aggregate=pd.DataFrame(aggregate_rows)
    summary={"rq3_is_descriptive":True,
             "rank_dispersion_median_by_n":dispersion.groupby("n_labels").rank_sd_across_R.median().to_dict(),
             "loggap_dispersion_median_by_n":dispersion.groupby("n_labels").loggap_sd_across_R.median().to_dict(),
             "rank_endpoint_decreases":int((dispersion.pivot(index="function",columns="n_labels",values="rank_sd_across_R")[9]<dispersion.pivot(index="function",columns="n_labels",values="rank_sd_across_R")[3]).sum()),
             "loggap_endpoint_decreases":int((dispersion.pivot(index="function",columns="n_labels",values="loggap_sd_across_R")[9]<dispersion.pivot(index="function",columns="n_labels",values="loggap_sd_across_R")[3]).sum()),
             "rank_nonincreasing_all_n":int(((dispersion.pivot(index="function",columns="n_labels",values="rank_sd_across_R")[3]>=dispersion.pivot(index="function",columns="n_labels",values="rank_sd_across_R")[5])&(dispersion.pivot(index="function",columns="n_labels",values="rank_sd_across_R")[5]>=dispersion.pivot(index="function",columns="n_labels",values="rank_sd_across_R")[7])&(dispersion.pivot(index="function",columns="n_labels",values="rank_sd_across_R")[7]>=dispersion.pivot(index="function",columns="n_labels",values="rank_sd_across_R")[9])).sum()),
             "blocked_run_id_H3_inference": "not recalculated/included: historical actual seeds differ by global experiment ID, so run_id does not identify common random-number blocks"}
    return profiles,dispersion,granularity,{"summary":summary,"pooled_loggap":pooled,
                                             "benchmark_wide_aggregate":aggregate,
                                             "mean_rank_by_n_rule":by_rule}


def plot_granularity_summary(by_rule: pd.DataFrame, aggregate: pd.DataFrame):
    profiles = by_rule.reindex(index=GRANULARITIES, columns=RULES)
    summary = aggregate.set_index("n_labels").loc[GRANULARITIES]
    np.testing.assert_allclose(
        profiles.std(axis=1, ddof=1), summary.std_rank_across_rules,
        rtol=0, atol=1e-12,
    )
    with plt.rc_context({"font.family": "serif", "font.size": 11}):
        figure, axes = plt.subplots(
            1, 2, figsize=(9.2, 3.8), width_ratios=(1.6, 1),
            layout="constrained",
        )
        markers = ["o", "s", "^", "v", "D", "P", "X", "*"]
        for rule, marker in zip(RULES, markers):
            direction = PROGRESS[rule]
            axes[0].plot(
                GRANULARITIES, profiles[rule], label=rule, marker=marker,
                markersize=4.5, linewidth=1.3,
                color=COLORS[direction], linestyle=STYLES[direction],
            )
        axes[0].invert_yaxis()
        axes[0].set_ylabel("Mean Friedman rank")
        axes[0].set_title("(a) Pattern-specific mean ranks", fontsize=11)
        axes[0].legend(
            loc="upper center", bbox_to_anchor=(0.5, -0.18),
            ncol=4, fontsize=9, frameon=False,
        )
        axes[1].plot(
            GRANULARITIES, summary.std_rank_across_rules,
            marker="o", color="#3478a8", linewidth=1.4,
        )
        axes[1].set_ylabel("SD across pattern-specific mean ranks")
        axes[1].set_title("(b) Between-pattern rank dispersion", fontsize=11)
        for axis in axes:
            axis.set_xticks(GRANULARITIES)
            axis.set_xlabel("Number of labels n")
            axis.grid(alpha=0.25)
    return figure


def save_figures(out_fig: Path, mean_ranks: pd.DataFrame, cd: float,
                 class_stats: pd.DataFrame, ranks_sub: pd.DataFrame,
                 h4_summary: pd.DataFrame, rule_summary: pd.DataFrame,
                 function_instance: pd.DataFrame, runtime: pd.DataFrame,
                 consolidated: pd.DataFrame, trajectories: pd.DataFrame | None,
                 convergence: pd.DataFrame | None, before_after: pd.DataFrame,
                 rank_matrix: pd.DataFrame, rq3_aggregate: pd.DataFrame) -> list[str]:
    out_fig.mkdir(parents=True,exist_ok=True)
    created=[]
    def save(fig,stem):
        fig.savefig(out_fig/f"{stem}.png",bbox_inches="tight",dpi=240)
        fig.savefig(out_fig/f"{stem}.pdf",bbox_inches="tight")
        plt.close(fig); created.extend([f"{stem}.png",f"{stem}.pdf"])

    df=mean_ranks.sort_values("mean_rank").reset_index(drop=True)
    fig,ax=plt.subplots(figsize=(9,12)); y=np.arange(len(df))[::-1]
    ax.hlines(y,0,df.mean_rank,color="#3478a8",alpha=.45); ax.scatter(df.mean_rank,y,color="#3478a8",s=17)
    names=df.configuration_id.tolist(); ax.set_yticks(y); ax.set_yticklabels(names,fontsize=7)
    for tick,name in zip(ax.get_yticklabels(),names):
        if name=="PSO": tick.set_fontweight("bold")
    ax.axvspan(df.mean_rank.min(),df.mean_rank.min()+cd,color="#7ba784",alpha=.18)
    ax.set_xlabel("Mean Friedman rank (lower is better)"); ax.set_title("Consolidated 62-instance ranking")
    save(fig,"fig_cd_diagram_h1")

    fig,ax=plt.subplots(figsize=(13,9))
    heat=rank_matrix.T.to_numpy(dtype=float)
    image=ax.imshow(heat,aspect="auto",interpolation="nearest",cmap="viridis_r")
    ax.set_yticks(np.arange(rank_matrix.shape[1]));ax.set_yticklabels(rank_matrix.columns,fontsize=6)
    ax.set_xticks(np.arange(rank_matrix.shape[0]));ax.set_xticklabels(rank_matrix.index,rotation=90,fontsize=5)
    ax.set_xlabel("Benchmark instance");ax.set_ylabel("Configuration rank")
    fig.colorbar(image,ax=ax,label="Median-gap rank (1 = best)",shrink=.7)
    save(fig,"fig_function_heatmap_consolidated")

    fcs=class_stats[class_stats.mh_family.eq("PSO_FCS")].copy()
    pivot=fcs.pivot(index="configuration_id",columns="problem_class",values="gap_median_mean")
    pivot=pivot.reindex(sorted(pivot.index,key=lambda x:(int(x.split('-')[1]),x.split('-')[2])))
    fig,ax=plt.subplots(figsize=(6,10)); image=ax.imshow(np.log10(np.maximum(pivot.to_numpy(),LOG_FLOOR)+LOG_FLOOR),aspect="auto",cmap="RdYlGn_r")
    ax.set_yticks(range(len(pivot)));ax.set_yticklabels(pivot.index,fontsize=7)
    ax.set_xticks(range(len(pivot.columns)));ax.set_xticklabels([CLASS_SHORT.get(x,x) for x in pivot.columns],rotation=25,ha="right")
    fig.colorbar(image,ax=ax,label="log10(mean instance-median normalized gap)");save(fig,"fig_rule_class_heatmap")

    by_rule = pd.DataFrame({
        rule: [rank_matrix[f"FCS-{granularity}-{rule}"].mean()
               for granularity in GRANULARITIES]
        for rule in RULES
    }, index=GRANULARITIES)
    fig = plot_granularity_summary(by_rule, rq3_aggregate)
    save(fig,"fig_granularity_effect_consolidated")

    pts=ranks_sub.copy()
    fig,ax=plt.subplots(figsize=(6,5));ax.scatter(pts.S1,pts.S2,color="#647c8b",alpha=.75)
    pareto=pts[pts.pareto].sort_values("S1");ax.plot(pareto.S1,pareto.S2,"o-",color="#b44b45")
    for _,r in pareto.iterrows():
        ax.annotate(r.configuration_id,(r.S1,r.S2),fontsize=7,xytext=(-10,-10),
                    textcoords="offset points",ha="right",va="top",clip_on=True)
    baseline=pts[pts.configuration_id.eq("PSO")]
    ax.scatter(baseline.S1,baseline.S2,marker="*",s=110,color="black",zorder=5)
    ax.set_xlabel("Rank on S1 (F1–F13)");ax.set_ylabel("Rank on S2 (F14–F23)");ax.invert_xaxis();ax.invert_yaxis();save(fig,"fig_pareto_s1_s2")

    top=h4_summary.sort_values(["independent_bonferroni_wins","independent_nominal_wins","a12_mean"],ascending=False).head(10).iloc[::-1]
    fig,ax=plt.subplots(figsize=(7,5));y=np.arange(len(top));ax.barh(y,top.independent_nominal_wins,color="#3b8975",label="wins")
    ax.barh(y,top.independent_nominal_ties,left=top.independent_nominal_wins,color="#aab3b8",label="ties")
    ax.barh(y,top.independent_nominal_losses,left=top.independent_nominal_wins+top.independent_nominal_ties,color="#ad514b",label="losses")
    ax.set_yticks(y);ax.set_yticklabels(top.configuration_id);ax.set_xlabel("Instances (of 62)");ax.legend();save(fig,"fig_h4_independent_outcomes")

    fig,ax=plt.subplots(figsize=(8,5));x=np.arange(len(rule_summary));w=.24
    ax.bar(x-w,rule_summary.independent_first_wins,width=w,label="first pattern wins",color="#3478a8")
    ax.bar(x,rule_summary.independent_ties,width=w,label="ties",color="#aab3b8")
    ax.bar(x+w,rule_summary.independent_second_wins,width=w,label="second pattern wins",color="#b44b45")
    ax.set_xticks(x);ax.set_xticklabels(rule_summary.pair,rotation=25,ha="right");ax.set_ylabel("Significant outcomes of 248")
    ax.legend();save(fig,"fig_rule_pattern_independent_outcomes")

    f14=before_after[before_after.configuration_id.ne("PSO")]
    fig,ax=plt.subplots(figsize=(5.8,5));ax.scatter(f14.historical_mean,f14.corrected_mean,color="#3478a8")
    lo=min(f14.historical_mean.min(),f14.corrected_mean.min());hi=max(f14.historical_mean.max(),f14.corrected_mean.max())
    ax.plot([lo,hi],[lo,hi],"--",color="#555");
    for _,r in f14.iterrows():
        if abs(r.mean_delta)>1e-6:ax.annotate(r.configuration_id,(r.historical_mean,r.corrected_mean),fontsize=7)
    ax.set_xlabel("Historical mean fitness");ax.set_ylabel("Corrected F14 mean fitness");save(fig,"fig_f14_historical_vs_corrected")

    fig,ax=plt.subplots(figsize=(6,4)); bins=np.linspace(min(before_after.historical_mean.min(),before_after.corrected_mean.min()),max(before_after.historical_mean.max(),before_after.corrected_mean.max()),18)
    ax.hist(before_after.historical_mean,bins=bins,alpha=.5,label="historical");ax.hist(before_after.corrected_mean,bins=bins,alpha=.5,label="corrected")
    ax.set_xlabel("Configuration mean fitness on F14");ax.set_ylabel("Configurations");ax.legend();save(fig,"fig_f14_mean_fitness_distribution")

    fig,ax=plt.subplots(figsize=(6,5))
    ax.scatter(before_after.historical_sd,before_after.corrected_sd,color="#3478a8",alpha=.8)
    lo=min(before_after.historical_sd.min(),before_after.corrected_sd.min())
    hi=max(before_after.historical_sd.max(),before_after.corrected_sd.max())
    ax.plot([lo,hi],[lo,hi],"--",color="#555")
    for _,r in before_after.iterrows():
        if abs(r.mean_delta)>1e-6:ax.annotate(r.configuration_id,(r.historical_sd,r.corrected_sd),fontsize=7)
    ax.set_xlabel("Historical run SD");ax.set_ylabel("Corrected run SD");save(fig,"fig_f14_dispersion_historical_vs_corrected")

    fcs_runs=consolidated[consolidated.mh_family.eq("PSO_FCS")].copy()
    fcs_runs["log_gap_display"]=np.log10(np.maximum(fcs_runs.gap_final.astype(float),LOG_FLOOR)+LOG_FLOOR)
    groups=[fcs_runs.loc[fcs_runs.n_labels.eq(n),"log_gap_display"].to_numpy() for n in GRANULARITIES]
    fig,ax=plt.subplots(figsize=(6,4));ax.boxplot(groups,tick_labels=[f"n={n}" for n in GRANULARITIES],showfliers=False)
    ax.set_ylabel(r"$\log_{10}(\max(\mathrm{gap},10^{-12})+10^{-12})$")
    save(fig,"fig_boxplot_gap_by_n_consolidated")

    fig,ax=plt.subplots(figsize=(5.8,4))
    ax.plot(rq3_aggregate.n_labels,rq3_aggregate.std_gap_median_across_rules,marker="o",color="#b44b45")
    ax.set_xticks(GRANULARITIES);ax.set_xlabel("Number of linguistic labels n")
    ax.set_ylabel("SD across rule-pattern median gaps");save(fig,"fig_gap_dispersion_by_n_consolidated")

    if str(ROOT) not in sys.path:
        sys.path.insert(0,str(ROOT))
    from Problem.Benchmark.Problem import F14
    axis=np.linspace(-65.536,65.536,121)
    xx,yy=np.meshgrid(axis,axis)
    zz=np.fromiter((float(F14(np.array([x,y]))) for x,y in zip(xx.ravel(),yy.ravel())),
                    dtype=float,count=xx.size).reshape(xx.shape)
    fig,ax=plt.subplots(figsize=(6.2,5.2))
    image=ax.contourf(xx,yy,np.log10(np.maximum(zz,1e-12)),levels=35,cmap="viridis")
    ax.scatter([32], [32], marker="x", color="red", s=45, label="25th Foxholes center")
    ax.set_xlabel("x1");ax.set_ylabel("x2");ax.set_title("Corrected F14 objective (log10 scale)")
    ax.legend(fontsize=8);fig.colorbar(image,ax=ax,label="log10(F14)")
    save(fig,"fig_f14_corrected_objective_surface")

    fig,ax=plt.subplots(figsize=(7,5));f=function_instance[function_instance.function.eq("F14")]
    x=np.arange(len(f));ax.scatter(x,f.gap_pso,label="PSO",marker="x");ax.scatter(x,f.gap_best_fcs,label="best FCS by instance",marker="o")
    ax.set_xticks(x);ax.set_xticklabels(f.benchmark_instance,rotation=55,ha="right");ax.set_ylabel("Median normalized gap");ax.legend();save(fig,"fig_f14_instance_ranks")

    if trajectories is not None:
        piv_w=trajectories.pivot(index="iter",columns="configuration_id",values="w_mean")
        piv_x=trajectories.pivot(index="iter",columns="configuration_id",values="xpl_mean").shift(1)
        fig,axes=plt.subplots(2,4,figsize=(12,6),sharex=True)
        for col,n in enumerate(GRANULARITIES):
            for rule in RULES:
                name=f"FCS-{n}-{rule}"
                if name in piv_w:
                    axes[0,col].plot(piv_w.index,piv_w[name],color=COLORS[PROGRESS[rule]],linestyle=STYLES[PROGRESS[rule]],lw=.9)
                    axes[1,col].plot(piv_x.index,piv_x[name],color=COLORS[PROGRESS[rule]],linestyle=STYLES[PROGRESS[rule]],lw=.9)
            if "PSO" in piv_w: axes[0,col].plot(piv_w.index,piv_w.PSO,color="black",lw=1.2)
            if "PSO" in piv_x: axes[1,col].plot(piv_x.index,piv_x.PSO,color="black",lw=1.2)
            axes[0,col].set_title(f"n={n}");axes[1,col].set_yscale("log");axes[1,col].set_xlabel("Iteration")
        axes[0,0].set_ylabel("Mean inertia weight");axes[1,0].set_ylabel("Mean XPL (%)")
        save(fig,"fig_w_trajectories_consolidated")
    if convergence is not None and len(convergence):
        cases=list(convergence.groupby(["function","dim"],sort=True))
        fig,axes=plt.subplots(2,2,figsize=(10,7));axes=axes.ravel()
        for ax,((fn,dim),block) in zip(axes,cases):
            for cfg,sub in block.groupby("configuration_id"):
                curve=sub.sort_values("iter")
                ax.plot(curve.iter,curve["median"],label=cfg,lw=1)
                ax.fill_between(curve.iter,curve.q1,curve.q3,alpha=.12)
            ax.set_title(f"{fn}, d={dim}");ax.set_yscale("symlog");ax.set_xlabel("Iteration");ax.legend(fontsize=6)
        save(fig,"fig_convergence_representative_consolidated")

    fig,ax=plt.subplots(figsize=(7,4));
    ax.bar(runtime.function,runtime.unpaired_ratio_of_medians_overhead_pct,color="#3478a8")
    ax.axhline(0,color="#555",lw=.7);ax.set_ylabel("Overhead from independent medians (%)");ax.tick_params(axis="x",rotation=60)
    save(fig,"fig_runtime_unpaired_overhead")
    return created


def stream_dynamics(frame: pd.DataFrame, per_function: pd.DataFrame,
                    stats_ci: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate all-62-instance trajectories, replacing old F14 blobs in-stream."""
    max_id = int(frame.historical_exp_id.max())
    config_names = sorted(frame.configuration_id.unique())
    config_index = {name: idx for idx, name in enumerate(config_names)}
    lookup = np.full(max_id + 1, -1, dtype=np.int32)
    historical = frame[frame.source_version.eq("historical_level1_excluding_F14")]
    lookup[historical.historical_exp_id.to_numpy(dtype=np.int64)] = historical.configuration_id.map(config_index).to_numpy(dtype=np.int32)
    cells = len(config_names) * 1001
    w_sum = np.zeros(cells, dtype=np.float64)
    xpl_sum = np.zeros(cells, dtype=np.float64)
    counts = np.zeros(cells, dtype=np.int32)

    # Build the representative convergence subset from recalculated function winners.
    cases = [("F1",30),("F9",30),("F14",2),("F23",4)]
    best_by_function = per_function.set_index("function")["best_fcs"].to_dict()
    convergence_specs: dict[int, tuple[str,str]] = {}
    for function, dim in cases:
        configs = ["PSO", "FCS-3-R1"]
        best = best_by_function.get(function)
        if isinstance(best,str) and best not in configs and best != "--":
            configs.append(best)
        configs.append("FCS-9-R2")
        eligible = frame[(frame.function.eq(function)) & frame.dim.eq(dim) & frame.configuration_id.isin(configs)]
        for row in eligible.itertuples(index=False):
            convergence_specs[int(row.historical_exp_id)] = (function, row.configuration_id)
    wanted_ids = set(convergence_specs)
    conv_chunks=[]
    batch_rows=2_000_000
    reader=pq.ParquetFile(HIST_ITER)
    processed=0
    for batch in reader.iter_batches(batch_size=batch_rows,columns=["id_exp","iter","w","XPL","best_fitness"]):
        ids=batch.column("id_exp").to_numpy().astype(np.int64,copy=False)
        iters=batch.column("iter").to_numpy().astype(np.int64,copy=False)
        valid_id=(ids>=0)&(ids<=max_id)
        cfg=np.full(ids.shape,-1,dtype=np.int32)
        cfg[valid_id]=lookup[ids[valid_id]]
        valid=(cfg>=0)&(iters>=0)&(iters<=1000)
        flat=cfg[valid].astype(np.int64)*1001+iters[valid]
        w=batch.column("w").to_numpy()[valid]
        xpl=batch.column("XPL").to_numpy()[valid]
        finite=np.isfinite(w)&np.isfinite(xpl)
        if finite.any():
            w_sum+=np.bincount(flat[finite],weights=w[finite],minlength=cells)
            xpl_sum+=np.bincount(flat[finite],weights=xpl[finite],minlength=cells)
            counts+=np.bincount(flat[finite],minlength=cells).astype(np.int32)
        selected=(cfg>=0)&np.isin(ids,list(wanted_ids))
        if selected.any():
            conv_chunks.append(pd.DataFrame({
                "historical_exp_id":ids[selected],"iter":iters[selected],
                "best_fitness":batch.column("best_fitness").to_numpy()[selected],
            }))
        processed+=len(ids)
        print(f"Streamed historical iterations: {processed:,}",end="\r",flush=True)
    print()

    connection=sqlite3.connect(F14_DB)
    try:
        blobs=connection.execute("SELECT fk_id_experimento,archivo FROM iteraciones ORDER BY fk_id_experimento")
        f14_rows=frame[frame.function.eq("F14")].set_index("historical_exp_id")
        n_blobs=0
        for exp_id,blob in blobs:
            exp_id=int(exp_id)
            row=f14_rows.loc[exp_id]
            cfg=config_index[row.configuration_id]
            history=pd.read_csv(io.BytesIO(blob))
            if len(history)!=1001 or not history["iter"].iloc[0]==0 or not history["iter"].iloc[-1]==1000:
                raise ValueError(f"Corrected F14 iteration log malformed for historical ID {exp_id}")
            iters=history["iter"].to_numpy(dtype=np.int64)
            flat=cfg*1001+iters
            w=history["w"].to_numpy(dtype=float)
            xpl=history["XPL"].to_numpy(dtype=float)
            finite=np.isfinite(w)&np.isfinite(xpl)
            np.add.at(w_sum,flat[finite],w[finite]);np.add.at(xpl_sum,flat[finite],xpl[finite]);np.add.at(counts,flat[finite],1)
            if exp_id in wanted_ids:
                conv_chunks.append(pd.DataFrame({"historical_exp_id":exp_id,"iter":iters,
                                                 "best_fitness":history["best_fitness"].to_numpy()}))
            n_blobs+=1
    finally:
        connection.close()
    if n_blobs!=1023:
        raise ValueError(f"Expected 1,023 corrected F14 iteration blobs; got {n_blobs}")

    trajectory_rows=[]
    for cfg,idx in config_index.items():
        for iteration in range(1001):
            cell=idx*1001+iteration
            trajectory_rows.append({"configuration_id":cfg,"iter":iteration,
                                    "w_mean":w_sum[cell]/counts[cell] if counts[cell] else np.nan,
                                    "xpl_mean":xpl_sum[cell]/counts[cell] if counts[cell] else np.nan,
                                    "n_runs":int(counts[cell])})
    trajectories=pd.DataFrame(trajectory_rows)
    expected_runs=1922
    if not trajectories.n_runs.eq(expected_runs).all():
        bad=trajectories.loc[~trajectories.n_runs.eq(expected_runs)].head(10)
        raise ValueError(f"Iteration aggregation does not contain 1,922 runs per configuration/iteration: {bad}")
    convergence_raw=pd.concat(conv_chunks,ignore_index=True)
    convergence_raw["function"]=convergence_raw.historical_exp_id.map(lambda exp_id:convergence_specs.get(int(exp_id),(None,None))[0])
    convergence_raw["configuration_id"]=convergence_raw.historical_exp_id.map(lambda exp_id:convergence_specs.get(int(exp_id),(None,None))[1])
    case_dimensions={function:dim for function,dim in cases}
    convergence_raw["dim"]=convergence_raw.function.map(case_dimensions)
    convergence=(convergence_raw.groupby(["function","dim","configuration_id","iter"],observed=True).best_fitness
                 .agg(median="median",q1=lambda s:s.quantile(.25),q3=lambda s:s.quantile(.75),n_runs="size").reset_index())
    expected_keys={(fn,cfg) for fn,dim in cases for cfg in
                   (["PSO","FCS-3-R1"]+([best_by_function[fn]] if best_by_function.get(fn) not in (None,"--","PSO","FCS-3-R1") else [])+["FCS-9-R2"])}
    present=set(zip(convergence.function,convergence.configuration_id))
    if not expected_keys.issubset(present) or not convergence.n_runs.eq(31).all():
        missing=sorted(expected_keys-present)
        bad=convergence.loc[~convergence.n_runs.eq(31),["function","dim","configuration_id","iter","n_runs"]].head(20).to_dict("records")
        raise ValueError(f"Representative convergence data are incomplete; missing={missing}; non-31 cells={bad}")
    return trajectories,convergence


def render_readme(report: dict, changes: pd.DataFrame) -> str:
    f14=report["f14_comparison"]
    h4=report["rq4"]
    fcs=report["rq4_fcs_3_r1"]
    lines=[
        "# Consolidated Mathematics dataset and recalculated analyses",
        "",
        f"Version: `{report['version']}`. This package is separate from all historical outputs and the manuscript.",
        "",
        "## Validation",
        "",
        f"- Records: {report['dataset']['consolidated_rows']:,}; 62 instances; 33 configurations; 2,046 groups of 31 runs.",
        f"- Historical F1–F13/F15–F23: {report['dataset']['historical_non_F14_rows_used']:,}; corrected F14: {report['dataset']['corrected_F14_rows_used']:,}.",
        f"- Historical actual seeds were not persisted ({report['dataset']['historical_actual_seeds_persisted']:,}); {report['dataset']['historical_actual_seeds_reconstructed_from_verified_runner']:,} values are reconstructed as `42 + historical_exp_id` from the verified runner. Exporter values `42*run_id` are retained separately as synthetic metadata and are never used for inference.",
        f"- Corrected F14 actual seeds: `42 + historical_exp_id`; 1,023 unique values recovered and checked.",
        "- Consolidation schema and configuration IDs are validated before any statistical calculation.",
        "",
        "## Before / After",
        "",
        f"- F14 fitness values materially changed (`abs(delta)>1e-6`) in {f14['material_changes_abs_gt_1e-6']}/1,023 runs: {f14['corrected_higher']} higher, {f14['corrected_lower']} lower, {f14['equal_within_1e-6']} unchanged within tolerance.",
        f"- F14 mean fitness: {f14['historical_mean']:.8f} → {f14['corrected_mean']:.8f}; median: {f14['historical_median']:.8f} → {f14['corrected_median']:.8f}; best: {f14['historical_best']:.8f} → {f14['corrected_best']:.8f}.",
        f"- RQ4: {h4['n_tests']} independent two-sided Mann–Whitney tests; Bonferroni alpha `{h4['bonferroni_alpha']:.10g}`. FCS-3-R1 has {fcs['independent_nominal_wins']}/{fcs['independent_nominal_ties']}/{fcs['independent_nominal_losses']} nominal and {fcs['independent_bonferroni_wins']}/{fcs['independent_bonferroni_ties']}/{fcs['independent_bonferroni_losses']} corrected wins/ties/losses.",
        "- Table 11 uses independent-sample tests; per-pair A12 is reported alongside p-values. Historical row-level outputs are reconciled separately.",
        "- Runtime overhead is a ratio of independent group medians, with no join on `run_id`.",
        "",
        "## Manuscript Update Register",
        "",
        "See `tables/manuscript_change_register.csv` and `tables/scientific_claim_deltas.csv` for current-output values, recalculated values, and actions by section. Affected sections include 5.1–5.7, the hypothesis summary, function-level table, Table 11, runtime prose, and F14-dependent figures. S1-only dimensional scaling is unaffected.",
        "",
        "## Methodological Caveats",
        "",
        "- Do not interpret `run_id` as a shared-seed block. RQ4 and Table 11 are recalculated as independent samples.",
        "- The previous H3 two-way bootstrap using function × run_id blocks is not reused as confirmatory inference. RQ3 outputs here are descriptive only; see `tables/h3_artifact_audit.csv` for legacy consumers.",
        "- The archived Table 11 detail does not fully reproduce from the current historical level-1 export; see `analyses/table11_archive_reconciliation.json`.",
        "- Manuscript files and historical output files were not modified. No PSO runs were executed.",
        "",
        "## Key Outputs",
        "",
        "- `consolidated_level1.csv` / `.parquet`: consolidated run-level dataset with seed provenance.",
        "- `tables/`: RQ tables and before/after comparisons.",
        "- `analyses/`: inferential summaries, reconciliation, and validation details.",
        "- `figures/`: regenerated figures affected by F14 and independent-test changes.",
        "- `tables/h3_artifact_audit.csv`: legacy H3 script/output consumers and their status.",
        "- `validation_report.json`: machine-readable validation and recommendation.",
        "",
    ]
    return "\n".join(lines)


def finalize_existing_package(refresh_existing: bool = False) -> None:
    """Write the final report/README from completed outputs without recalculating."""
    required = [
        OUT / "validation.json",
        OUT / "analyses" / "rq1_friedman_nemenyi.json",
        OUT / "analyses" / "rq2_class_winners.csv",
        OUT / "analyses" / "rq3_descriptive_summary.json",
        OUT / "analyses" / "rq4_independent_summary.json",
        OUT / "analyses" / "rq5_subset_summary.json",
        OUT / "analyses" / "table11_archive_reconciliation.json",
        OUT / "tables" / "f14_run_level_historical_vs_corrected.csv",
        OUT / "tables" / "rq4_configuration_summary.csv",
        OUT / "tables" / "table11_rule_pair_summary.csv",
        OUT / "tables" / "manuscript_change_register.csv",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Cannot finalize incomplete analysis outputs: {missing}")
    report_path, readme_path = OUT / "validation_report.json", OUT / "README.md"
    if (report_path.exists() or readme_path.exists()) and not refresh_existing:
        raise FileExistsError("Refusing to overwrite existing final report or README")

    validation = json.loads((OUT / "validation.json").read_text(encoding="utf-8"))
    h1 = json.loads((OUT / "analyses" / "rq1_friedman_nemenyi.json").read_text(encoding="utf-8"))
    rq3 = json.loads((OUT / "analyses" / "rq3_descriptive_summary.json").read_text(encoding="utf-8"))
    h4 = json.loads((OUT / "analyses" / "rq4_independent_summary.json").read_text(encoding="utf-8"))
    rq5 = json.loads((OUT / "analyses" / "rq5_subset_summary.json").read_text(encoding="utf-8"))
    rule_audit = json.loads((OUT / "analyses" / "table11_archive_reconciliation.json").read_text(encoding="utf-8"))
    fcs3 = pd.read_csv(OUT / "tables" / "rq4_configuration_summary.csv")
    fcs3 = fcs3[fcs3.configuration_id.eq("FCS-3-R1")].iloc[0].to_dict()
    rule_summary = pd.read_csv(OUT / "tables" / "table11_rule_pair_summary.csv")
    class_winners = pd.read_csv(OUT / "analyses" / "rq2_class_winners.csv")
    class_taus = pd.read_csv(OUT / "tables" / "rq2_class_rank_concordance.csv")
    deltas = pd.read_csv(OUT / "tables" / "f14_run_level_historical_vs_corrected.csv")
    rank_before = pd.read_csv(OUT / "tables" / "rq1_rank_before_after.csv")
    nemenyi_old = pd.read_csv(RESULTS / "tests" / "h1_friedman_nemenyi" / "nemenyi_pvalues.csv", index_col=0)
    nemenyi_new = pd.read_csv(OUT / "tables" / "rq1_nemenyi_pvalues.csv", index_col=0)
    nemenyi_old.index = [config_id(x) for x in nemenyi_old.index]
    nemenyi_old.columns = [config_id(x) for x in nemenyi_old.columns]
    common_configs = sorted(set(nemenyi_old.index) & set(nemenyi_new.index))
    p_changed = 0
    old_significant, new_significant = set(), set()
    for i, first in enumerate(common_configs):
        for second in common_configs[i + 1:]:
            old_p = float(nemenyi_old.loc[first, second])
            new_p = float(nemenyi_new.loc[first, second])
            if abs(old_p - new_p) > 1e-10:
                p_changed += 1
            if old_p < ALPHA:
                old_significant.add((first, second))
            if new_p < ALPHA:
                new_significant.add((first, second))
    class_before = pd.read_csv(OUT / "tables" / "rq2_class_before_after.csv")
    subset_before = pd.read_csv(OUT / "tables" / "rq5_subgroup_before_after.csv")
    gran_before = pd.read_csv(OUT / "tables" / "rq3_granularity_before_after.csv")
    dispersion_before = pd.read_csv(OUT / "tables" / "rq3_function_dispersion_before_after.csv")
    function_before = pd.read_csv(OUT / "tables" / "function_level_before_after.csv")
    runtime_before = pd.read_csv(OUT / "tables" / "runtime_before_after.csv")
    old_dynamics = pd.read_csv(RESULTS / "level3_rankings" / "w_trajectory_by_config.csv")
    new_dynamics = pd.read_csv(OUT / "tables" / "dynamics_trajectory_by_configuration.csv")
    old_dynamics = old_dynamics.rename(columns={"config": "configuration_id"})
    dyn = old_dynamics.merge(new_dynamics, on=["configuration_id", "iter"], suffixes=("_old", "_new"), validate="one_to_one")
    dynamics_delta = {
        "cells": len(dyn),
        "max_abs_w_mean_change": float((dyn.w_mean_new-dyn.w_mean_old).abs().max()),
        "max_abs_xpl_mean_change": float((dyn.xpl_mean_new-dyn.xpl_mean_old).abs().max()),
        "w_cells_changed_gt_1e-12": int(((dyn.w_mean_new-dyn.w_mean_old).abs()>1e-12).sum()),
        "xpl_cells_changed_gt_1e-12": int(((dyn.xpl_mean_new-dyn.xpl_mean_old).abs()>1e-12).sum()),
    }
    figure_names = sorted(path.name for path in (OUT / "figures").glob("*.png"))
    if len(figure_names) < 14:
        raise ValueError(f"Expected generated statistical figures; found {len(figure_names)} PNGs")
    delta = deltas.delta_corrected_minus_historical.astype(float)

    h3_artifacts = pd.DataFrame([
        {"artifact_or_script":"21_recalculate_final_dataset.py / tables/rq3_function_dispersion.csv",
         "use":"Function-level rank/log-gap dispersion from consolidated scores; descriptive only; no run_id blocking.",
         "status":"Current versioned RQ3 output; valid for descriptive reporting."},
        {"artifact_or_script":"code/03_run_factorial_anova.py -> results/tests/h3_factorial_anova/{anova_table,srh_table,summary}.csv/json",
         "use":"Legacy ANOVA/Scheirer–Ray–Hare factorial H3 inference and partial eta-squared from the earlier dataset.",
         "status":"Archived legacy inference; not recalculated or used as confirmatory evidence in this package."},
        {"artifact_or_script":"code/17_reanalyze_h3_blocked.py -> results/tests/h3_blocked/summary.json",
         "use":"Exploratory two-way function × run_id cluster bootstrap; assumes run_id clusters are shared across configurations.",
         "status":"Archived exploratory output; not valid as common-seed blocking because seed assignment was based on global exp_id."},
        {"artifact_or_script":"code/06_generate_paper_figures.py -> results/tests/h3_factorial_anova/std_across_R_vs_n.csv -> fig_std_R_vs_n",
         "use":"Reads the old factorial H3 output to generate the std-across-rules figure.",
         "status":"Stale dependency if that script is run; replace its input with the consolidated descriptive RQ3 table. Current TeX search finds only the generated-input manifest comment for this figure."},
        {"artifact_or_script":"code/13_analyze_granularity.py -> results/tests/h3_factorial_anova/summary.json",
         "use":"Requires the old H3 summary and prints partial_eta_squared and h3_std_R_decreasing_with_n after creating granularity tables/figure.",
         "status":"Do not use its H3 console claims for final reporting; its descriptive rank/gap outputs should be regenerated from the consolidated inputs."},
        {"artifact_or_script":"code/18_h3_function_dispersion.py and code/07_generate_paper_tables.py -> results/tests/h3_function_dispersion/function_dispersion.csv",
         "use":"Descriptive function-level dispersion; no run_id pairing or bootstrap in script 18.",
         "status":"Method is descriptive, but the old file is superseded by tables/rq3_function_dispersion.csv and must be replaced before paper-table regeneration."},
    ])
    h3_artifacts.to_csv(OUT / "tables" / "h3_artifact_audit.csv", index=False)
    h3_audit = {
        "final_RQ3_is_descriptive_only": True,
        "final_RQ3_uses_run_id_as_inferential_block": False,
        "new_interaction_test_introduced": False,
        "historical_common_seed_blocks_established": False,
        "legacy_artifact_rows": h3_artifacts.to_dict(orient="records"),
    }

    claims = [
        {"section":"5.1 / RQ1","claim":"Friedman/Nemenyi global ranking","current":"FCS-3-R1 leader; 272/528 Nemenyi pairs significant; CD 6.5908","recalculated":f"{int((rank_before.delta_mean_rank.abs()>1e-12).sum())}/33 mean ranks changed; {p_changed}/528 Nemenyi p-values changed; {len(old_significant^new_significant)} significance memberships changed; leader {h1['best']['configuration_id']}; CD {h1['cd']:.4f}","action":"Refresh all reported rank numerics and CD diagram; critical-difference group membership is unchanged."},
        {"section":"5.2 / RQ2 and RQ5","claim":"Class and S1/S2 rankings","current":"Class/subgroup leaders and rank concordance","recalculated":f"class rank positions changed {int(class_before.delta_rank.ne(0).sum())}/99; S1/S2 rank positions changed {int(subset_before.delta_rank.ne(0).sum())}/66; tau(S1,S2)={rq5['kendall_tau_S1_S2']:.4f}, p={rq5['kendall_p_S1_S2']:.4f}","action":"Update changed median-gap magnitudes; leaders, rank positions, and S1/S2 concordance are retained."},
        {"section":"5.3 / RQ3 and Table granularity","claim":"Granularity/rule descriptive dispersion","current":"Function-level dispersion and mean ranks across n","recalculated":f"granularity rank cells changed {int(sum((gran_before[f'rank_n{n}']-gran_before[f'mean_rank_n{n}']).abs().gt(1e-12).sum() for n in GRANULARITIES))}/32; n=9 median rank SD {dispersion_before.loc[dispersion_before.n_labels.eq(9),'rank_sd_across_R_historical'].median():.3f} -> {dispersion_before.loc[dispersion_before.n_labels.eq(9),'rank_sd_across_R_consolidated'].median():.3f}","action":"Refresh numeric summaries and figures; RQ3 remains descriptive, not a blocked run_id test."},
        {"section":"5.4 / RQ4","claim":"FCS versus PSO win/tie/loss and significance","current":json.dumps(h4['historical_paired_bonferroni']),"recalculated":json.dumps(h4['independent_bonferroni']),"action":"Replace paired Wilcoxon claims with independent Mann–Whitney results and Bonferroni correction."},
        {"section":"5.4 / Table 11","claim":"Eight rule-pattern contrasts","current":"Archived paired Wilcoxon outcomes","recalculated":f"Independent outcomes for all eight contrasts; {rule_audit['a12_mismatch_rows_against_corrected_dataset']} archived A12 rows and {rule_audit['p_mismatch_rows_against_current_paired_recalculation']} archived p rows still fail historical reproduction; R3 vs R4 strongest class is {rule_summary.loc[rule_summary.pair.eq('R3 vs R4'),'independent_strongest_class'].iloc[0]}","action":"Replace test/results text; reconcile archive discrepancies. R3 vs R4 strongest class changes from unimodal to scalable multimodal."},
        {"section":"5.2 / function-level table","claim":"Best FCS per function and significance counts","current":f"Historical significant-win counts by function", "recalculated":f"Significant-win counts differ for {function_before.loc[function_before.significant_wins.ne(function_before.significant_wins_independent),'function'].tolist()}; F14 PSO median rank {function_before.loc[function_before.function.eq('F14'),'rank_pso_median_historical'].iloc[0]:.0f} -> {function_before.loc[function_before.function.eq('F14'),'rank_pso_median_consolidated'].iloc[0]:.0f}","action":"Refresh per-function inferential columns and F14 rank details; winner FCS-3-R1 remains the F14 best-FCS label."},
        {"section":"5.6 / runtime","claim":"FCS runtime overhead","current":"Median of per-run FCS/PSO ratios matched by run_id","recalculated":f"Independent ratio-of-medians differs in {int((runtime_before.delta_overhead_pct_unpaired_minus_paired.abs()>1e-6).sum())}/23 functions; F14 {runtime_before.loc[runtime_before.function.eq('F14'),'runtime_overhead_pct'].iloc[0]:.1f}% -> {runtime_before.loc[runtime_before.function.eq('F14'),'unpaired_ratio_of_medians_overhead_pct'].iloc[0]:.1f}%","action":"Replace paired-runtime estimator and prose; do not infer significance from run_id matches."},
        {"section":"5.7 / dynamics and appendices","claim":"All-instance w/XPL trajectories and representative F14 convergence","current":"Historical trajectory means include incorrect F14","recalculated":f"{dynamics_delta['w_cells_changed_gt_1e-12']} w cells and {dynamics_delta['xpl_cells_changed_gt_1e-12']} XPL cells changed; corrected F14 convergence panel generated","action":"Replace dynamics, function heatmap, class, Pareto, Table 11, RQ4 and F14 dispersion figures from this package. S1-only scaling curves are unaffected."},
    ]
    pd.DataFrame(claims).to_csv(OUT / "tables" / "scientific_claim_deltas.csv", index=False)

    report = {
        "title": "Consolidated statistical dataset validation",
        "version": OUT.name,
        "dataset": validation,
        "analysis_methods": {
            "rq1": "Median normalized gap over 31 runs per configuration-instance; within-instance average ranks; Friedman and Nemenyi.",
            "rq2_rq5": "Descriptive gap_median aggregation by class/subset; minimum ranks; Kendall tau for rank concordance.",
            "rq3": "Descriptive function-level rank/log-gap dispersion only. Crossed run_id bootstrap not used because historical run_id does not identify common-seed blocks.",
            "rq4": "Two-sided Mann–Whitney U, independent 31-vs-31 samples, asymptotic continuity correction; A12; Bonferroni 0.05/1984.",
            "table11": "Two-sided Mann–Whitney U for independent samples, per pair/granularity/instance; unadjusted alpha=0.05, matching the original correction policy; A12.",
            "runtime": "Ratio of independent sample medians; no run_id join.",
        },
        "rq1": h1,
        "rq1_before_after": {
            "configuration_mean_ranks_changed": int((rank_before.delta_mean_rank.abs()>1e-12).sum()),
            "nemenyi_p_values_changed": p_changed,
            "historical_significant_pairs": len(old_significant),
            "consolidated_significant_pairs": len(new_significant),
            "significance_membership_changes": len(old_significant ^ new_significant),
        },
        "rq2_before_after": {
            "class_rank_position_changes": int(class_before.delta_rank.ne(0).sum()),
            "subgroup_rank_position_changes": int(subset_before.delta_rank.ne(0).sum()),
        },
        "rq3_before_after": {
            "granularity_rank_cells_changed": int(sum((gran_before[f"rank_n{n}"]-gran_before[f"mean_rank_n{n}"]).abs().gt(1e-12).sum() for n in GRANULARITIES)),
            "granularity_rank_cells_total": int(len(gran_before)*len(GRANULARITIES)),
            "rank_dispersion_median_n9_historical": float(dispersion_before.loc[dispersion_before.n_labels.eq(9),"rank_sd_across_R_historical"].median()),
            "rank_dispersion_median_n9_consolidated": float(dispersion_before.loc[dispersion_before.n_labels.eq(9),"rank_sd_across_R_consolidated"].median()),
        },
        "rq4_before_after": {
            "nominal_classification_changes": int(h4["nominal_classifications_changed"]),
            "bonferroni_classification_changes": int(h4["bonferroni_classifications_changed"]),
            "FCS3R1_significance_count_changed_functions": function_before.loc[
                function_before.significant_wins.ne(function_before.significant_wins_independent),"function"].tolist(),
        },
        "rq2_class_winners": class_winners.to_dict(orient="records"),
        "rq2_class_taus": class_taus.to_dict(orient="records"),
        "rq3": rq3,
        "h3_audit": h3_audit,
        "rq4": h4,
        "rq4_fcs_3_r1": fcs3,
        "rq5": rq5,
        "rule_pair_summary": rule_summary.to_dict(orient="records"),
        "table11_archive_reconciliation": rule_audit,
        "dynamics_before_after": dynamics_delta,
        "scientific_claim_deltas_csv": str(OUT / "tables" / "scientific_claim_deltas.csv"),
        "f14_comparison": {
            "n_runs": len(deltas),
            "material_changes_abs_gt_1e-6": int((delta.abs() > 1e-6).sum()),
            "corrected_lower": int((delta < -1e-6).sum()),
            "equal_within_1e-6": int((delta.abs() <= 1e-6).sum()),
            "corrected_higher": int((delta > 1e-6).sum()),
            "historical_mean": float(deltas.historical_fitness.mean()),
            "corrected_mean": float(deltas.fitness_best.mean()),
            "historical_median": float(deltas.historical_fitness.median()),
            "corrected_median": float(deltas.fitness_best.median()),
            "historical_best": float(deltas.historical_fitness.min()),
            "corrected_best": float(deltas.fitness_best.min()),
            "mean_delta": float(delta.mean()),
            "median_delta": float(delta.median()),
            "min_delta": float(delta.min()),
            "max_delta": float(delta.max()),
            "material_run_changes": deltas.loc[delta.abs().gt(1e-6), [
                "historical_exp_id", "run_id", "configuration_id", "actual_seed",
                "historical_fitness", "fitness_best", "delta_corrected_minus_historical",
            ]].to_dict(orient="records"),
        },
        "runtime_method": "Unpaired ratio of medians; current paired overheads are unsupported.",
        "blocked_H3_note": "The previous crossed-function/run_id bootstrap is not reused as confirmatory inference; RQ3 is descriptive.",
        "manuscript_change_register": str(OUT / "tables" / "manuscript_change_register.csv"),
        "figures_generated": figure_names,
        "outputs": {
            "consolidated_csv": str(OUT / "consolidated_level1.csv"),
            "consolidated_parquet": str(OUT / "consolidated_level1.parquet"),
            "tables": str(OUT / "tables"),
            "analyses": str(OUT / "analyses"),
            "figures": str(OUT / "figures"),
        },
        "recommendation": "The consolidated scores and independent-sample analyses are validated for reanalysis. Do not use run_id as a common-seed block. Reconcile the archived Table 11 row-level discrepancies and decide whether the H3 blocked inference is excluded or redesigned before treating the outputs as definitive. Manuscript and historical outputs were not modified.",
    }
    write_json(report_path, report)
    changes = pd.read_csv(OUT / "tables" / "manuscript_change_register.csv")
    readme_path.write_text(render_readme(report, changes), encoding="utf-8")
    print(json.dumps({
        "finalized_existing_outputs": True,
        "report": str(report_path),
        "readme": str(readme_path),
        "figures": len(figure_names),
        "F14_material_changes": report["f14_comparison"]["material_changes_abs_gt_1e-6"],
    }, indent=2))


def refresh_existing_figures() -> None:
    """Regenerate only the figures from already-computed tables and streams."""
    required = [
        OUT / "consolidated_level1.parquet",
        OUT / "tables" / "rq1_mean_rank_per_configuration.csv",
        OUT / "tables" / "rq1_mean_rank_matrix.csv",
        OUT / "tables" / "rq2_rankings_by_class.csv",
        OUT / "tables" / "rq5_pareto_ranks.csv",
        OUT / "tables" / "rq4_configuration_summary.csv",
        OUT / "tables" / "table11_rule_pair_summary.csv",
        OUT / "tables" / "function_level_per_instance.csv",
        OUT / "tables" / "runtime_unpaired_ratio_of_medians.csv",
        OUT / "tables" / "dynamics_trajectory_by_configuration.csv",
        OUT / "tables" / "convergence_representative_summary.csv",
        OUT / "tables" / "f14_historical_vs_corrected_by_configuration.csv",
        OUT / "tables" / "rq3_benchmark_wide_aggregate.csv",
        OUT / "analyses" / "rq1_friedman_nemenyi.json",
    ]
    missing=[str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Cannot regenerate figures from incomplete outputs: {missing}")
    mean_ranks=pd.read_csv(OUT/"tables"/"rq1_mean_rank_per_configuration.csv")
    matrix=pd.read_csv(OUT/"tables"/"rq1_mean_rank_matrix.csv",index_col=0)
    h1=json.loads((OUT/"analyses"/"rq1_friedman_nemenyi.json").read_text(encoding="utf-8"))
    generated=save_figures(
        OUT/"figures",mean_ranks,float(h1["cd"]),
        pd.read_csv(OUT/"tables"/"rq2_rankings_by_class.csv"),
        pd.read_csv(OUT/"tables"/"rq5_pareto_ranks.csv"),
        pd.read_csv(OUT/"tables"/"rq4_configuration_summary.csv"),
        pd.read_csv(OUT/"tables"/"table11_rule_pair_summary.csv"),
        pd.read_csv(OUT/"tables"/"function_level_per_instance.csv"),
        pd.read_csv(OUT/"tables"/"runtime_unpaired_ratio_of_medians.csv"),
        pd.read_parquet(OUT/"consolidated_level1.parquet"),
        pd.read_csv(OUT/"tables"/"dynamics_trajectory_by_configuration.csv"),
        pd.read_csv(OUT/"tables"/"convergence_representative_summary.csv"),
        pd.read_csv(OUT/"tables"/"f14_historical_vs_corrected_by_configuration.csv"),
        matrix,pd.read_csv(OUT/"tables"/"rq3_benchmark_wide_aggregate.csv"),
    )
    print(json.dumps({"regenerated_figures":generated,"count":len(generated)},indent=2))


def main() -> int:
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--finalize-existing",action="store_true",
                        help="Create the report/README from completed versioned output without recalculation.")
    parser.add_argument("--refresh-report",action="store_true",
                        help="Refresh report/README after adding audit details; does not recalculate analyses.")
    parser.add_argument("--refresh-figures",action="store_true",
                        help="Regenerate figures from completed versioned tables without rescanning iterations.")
    args=parser.parse_args()
    if args.refresh_figures:
        refresh_existing_figures()
        return 0
    if args.finalize_existing:
        finalize_existing_package(refresh_existing=args.refresh_report)
        return 0
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUT}")
    frame, validation = make_consolidated()
    OUT.mkdir(parents=True,exist_ok=False)
    tables=OUT/"tables"; analyses=OUT/"analyses"; figures=OUT/"figures"
    for folder in (tables,analyses,figures):folder.mkdir()

    frame.to_csv(OUT/"consolidated_level1.csv",index=False)
    frame.to_parquet(OUT/"consolidated_level1.parquet",index=False)
    write_json(OUT/"validation.json",validation)

    stats_ci=compute_stats_by_instance(frame)
    write_csv(tables/"stats_by_configuration_instance.csv",stats_ci)
    write_csv(tables/"stats_by_configuration.csv",frame.groupby("configuration_id",observed=True).agg(
        n_runs=("fitness_best","size"),fitness_mean=("fitness_best","mean"),fitness_median=("fitness_best","median"),
        gap_mean=("gap_final","mean"),gap_median=("gap_final","median"),runtime_median=("t_exec","median")).reset_index())

    matrix=stats_ci.pivot(index="benchmark_instance",columns="configuration_id",values="gap_median")
    ranks=matrix.rank(axis=1,method="average",ascending=True)
    ranks.to_csv(tables/"rq1_mean_rank_matrix.csv")
    mean_ranks=ranks.mean(axis=0).rename("mean_rank").reset_index().rename(columns={"index":"configuration_id"}).sort_values("mean_rank").reset_index(drop=True)
    pvalues,h1=nemenyi_cd(ranks)
    pvalues.to_csv(tables/"rq1_nemenyi_pvalues.csv")
    write_csv(tables/"rq1_mean_rank_per_configuration.csv",mean_ranks)
    h1["best_rank_by_granularity"]={str(n):float(mean_ranks.loc[mean_ranks.configuration_id.str.startswith(f"FCS-{n}-"),"mean_rank"].min()) for n in GRANULARITIES}
    h1["best_configuration_by_granularity"]={str(n):str(mean_ranks[mean_ranks.configuration_id.str.startswith(f"FCS-{n}-")].iloc[0].configuration_id) for n in GRANULARITIES}
    old_mean=pd.read_csv(RESULTS/"tests"/"h1_friedman_nemenyi"/"mean_rank_per_config.csv")
    old_mean["configuration_id"]=old_mean.mh_raw.map(config_id)
    rank_compare=old_mean.merge(mean_ranks,on="configuration_id",suffixes=("_historical","_consolidated"),validate="one_to_one")
    rank_compare["delta_mean_rank"]=rank_compare.mean_rank_consolidated-rank_compare.mean_rank_historical
    write_csv(tables/"rq1_rank_before_after.csv",rank_compare)
    write_json(analyses/"rq1_friedman_nemenyi.json",h1)

    # Class and dimensional-regime rankings (H2/RQ2 and H5/RQ5).
    class_stats=stats_ci.groupby(["configuration_id","mh_family","n_labels","rule_set","problem_class"],dropna=False,observed=True).gap_median.mean().rename("gap_median_mean").reset_index()
    class_stats["rank"]=class_stats.groupby("problem_class").gap_median_mean.rank(method="min",ascending=True)
    class_stats.to_csv(tables/"rq2_rankings_by_class.csv",index=False)
    old_class=pd.read_csv(RESULTS/"tests"/"h5_pareto_problemtype"/"ranking_by_class.csv")
    old_class["configuration_id"]=old_class.mh_raw.map(config_id)
    class_compare=old_class.merge(class_stats[["configuration_id","problem_class","gap_median_mean","rank"]],
                                  on=["configuration_id","problem_class"],suffixes=("_historical","_consolidated"),validate="one_to_one")
    class_compare["delta_rank"]=class_compare.rank_consolidated-class_compare.rank_historical
    class_compare["delta_gap_median_mean"]=class_compare.gap_median_mean-class_compare.gap_median
    write_csv(tables/"rq2_class_before_after.csv",class_compare)
    class_winners=class_stats.sort_values(["problem_class","gap_median_mean"]).groupby("problem_class").head(1).reset_index(drop=True)
    class_ranks=class_stats.pivot(index="configuration_id",columns="problem_class",values="rank")
    tau_class=[]
    classes=sorted(class_ranks.columns)
    for i,a in enumerate(classes):
        for b in classes[i+1:]:
            tau,p=kendalltau(class_ranks[a],class_ranks[b])
            tau_class.append({"class_a":a,"class_b":b,"kendall_tau":float(tau),"p_value":float(p)})
    class_tau=pd.DataFrame(tau_class);write_csv(tables/"rq2_class_rank_concordance.csv",class_tau)
    class_stats.to_csv(analyses/"rq2_class_rankings.csv",index=False)
    class_winners.to_csv(analyses/"rq2_class_winners.csv",index=False)

    sub_stats=stats_ci.groupby(["configuration_id","mh_family","n_labels","rule_set","subgroup"],dropna=False,observed=True).gap_median.mean().rename("gap_median_mean").reset_index()
    sub_stats["rank"]=sub_stats.groupby("subgroup").gap_median_mean.rank(method="min",ascending=True)
    write_csv(tables/"rq5_rankings_by_subgroup.csv",sub_stats)
    old_sub=pd.read_csv(RESULTS/"tests"/"h5_pareto_problemtype"/"ranking_by_subgroup.csv")
    old_sub["configuration_id"]=old_sub.mh_raw.map(config_id)
    sub_compare=old_sub.merge(sub_stats[["configuration_id","subgroup","gap_median_mean","rank"]],
                              on=["configuration_id","subgroup"],suffixes=("_historical","_consolidated"),validate="one_to_one")
    sub_compare["delta_rank"]=sub_compare.rank_consolidated-sub_compare.rank_historical
    sub_compare["delta_gap_median_mean"]=sub_compare.gap_median_mean-sub_compare.gap_median
    write_csv(tables/"rq5_subgroup_before_after.csv",sub_compare)
    sub_wide=sub_stats.pivot(index="configuration_id",columns="subgroup",values="rank")
    tau_s1_s2,p_s1_s2=kendalltau(sub_wide.S1,sub_wide.S2)
    sub_winners=sub_stats.sort_values("gap_median_mean").groupby("subgroup").head(1)
    old_h5=json.loads((RESULTS/"tests"/"h5_pareto_problemtype"/"summary.json").read_text(encoding="utf-8"))
    write_json(analyses/"rq5_subset_summary.json",{
        "kendall_tau_S1_S2":float(tau_s1_s2),"kendall_p_S1_S2":float(p_s1_s2),
        "leaders":sub_winners[["subgroup","configuration_id","gap_median_mean","rank"]].to_dict("records"),
        "historical_tau":old_h5["kendall_tau_S1_vs_S2"],"historical_p":old_h5["kendall_p_S1_vs_S2"],
        "historical_leaders":old_h5["best_by_subgroup"],
    })
    sub_rank=sub_stats.pivot(index="configuration_id",columns="subgroup",values="rank").reset_index()
    # Pareto front uses ascending ranks in S1/S2.
    sorted_sub=sub_rank.sort_values(["S1","S2"])
    front=[];best_s2=float("inf")
    for row in sorted_sub.itertuples(index=False):
        if row.S2<best_s2:
            front.append(row.configuration_id);best_s2=row.S2
    sub_rank["pareto"]=sub_rank.configuration_id.isin(front)
    write_csv(tables/"rq5_pareto_ranks.csv",sub_rank)

    # Descriptive RQ3 only. Do not use run_id as a crossed/common-seed block.
    profiles,dispersion,granularity,rq3=summarize_rq3(frame,stats_ci,ranks)
    write_csv(tables/"rq3_function_n_rule_profiles.csv",profiles)
    write_csv(tables/"rq3_function_dispersion.csv",dispersion)
    write_csv(tables/"rq3_granularity_by_rule.csv",granularity)
    write_csv(tables/"rq3_pooled_loggap_by_granularity.csv",rq3["pooled_loggap"])
    write_csv(tables/"rq3_benchmark_wide_aggregate.csv",rq3["benchmark_wide_aggregate"])
    rq3["mean_rank_by_n_rule"].to_csv(tables/"rq3_mean_rank_by_n_rule.csv")
    write_json(analyses/"rq3_descriptive_summary.json",rq3["summary"])

    # Independent-sample RQ4 and Table 11.
    old_h4=pd.read_csv(RESULTS/"tests"/"h4_wilcoxon_vs_baseline"/"wilcoxon_pairs.csv")
    h4_detail,h4_summary,h4_total=h4_tests(frame,old_h4)
    write_csv(tables/"rq4_independent_mann_whitney_details.csv",h4_detail)
    write_csv(tables/"rq4_configuration_summary.csv",h4_summary)
    write_json(analyses/"rq4_independent_summary.json",h4_total)
    old_h4_config=pd.read_csv(RESULTS/"tests"/"h4_wilcoxon_vs_baseline"/"wilcoxon_config_summary.csv")
    old_h4_config["configuration_id"]=old_h4_config.mh_raw.map(config_id)
    h4_compare=old_h4_config.merge(h4_summary,on="configuration_id",suffixes=("_historical","_independent"),validate="one_to_one")
    write_csv(tables/"rq4_config_before_after.csv",h4_compare)
    old_rule=pd.read_csv(RESULTS/"level3_rankings"/"rule_pair_per_instance.csv")
    rule_detail,rule_summary,rule_discrepancy=rule_pair_tests(frame,old_rule)
    write_csv(tables/"table11_independent_mann_whitney_details.csv",rule_detail)
    write_csv(tables/"table11_rule_pair_summary.csv",rule_summary)
    write_json(analyses/"table11_archive_reconciliation.json",rule_discrepancy)

    per_instance,per_function=function_level_tables(stats_ci,h4_detail)
    runtime=runtime_unpaired(frame,per_function)
    write_csv(tables/"function_level_per_instance.csv",per_instance)
    write_csv(tables/"function_level_per_function.csv",per_function.merge(runtime,on="function",how="left"))
    write_csv(tables/"runtime_unpaired_ratio_of_medians.csv",runtime)

    # F14-only historical/corrected score comparison and exact affected run IDs.
    f14=frame[frame.function.eq("F14")].copy()
    delta_frame=f14[["historical_exp_id","run_id","configuration_id","actual_seed","fitness_best"]].copy()
    corrected_source=pd.read_parquet(HIST_META,columns=["id_exp","exp_name","fitness_best"])
    corrected_source=corrected_source[corrected_source.exp_name.eq("F14 2")][["id_exp","fitness_best"]]
    corrected_source=corrected_source.rename(columns={"id_exp":"historical_exp_id","fitness_best":"historical_fitness"})
    delta_frame=delta_frame.merge(corrected_source,on="historical_exp_id",validate="one_to_one")
    delta_frame["delta_corrected_minus_historical"]=delta_frame.fitness_best-delta_frame.historical_fitness
    delta_frame["material_change_gt_1e-6"]=delta_frame.delta_corrected_minus_historical.abs()>1e-6
    write_csv(tables/"f14_run_level_historical_vs_corrected.csv",delta_frame)
    f14_by_config=delta_frame.groupby("configuration_id").agg(
        n_runs=("historical_exp_id","size"),historical_mean=("historical_fitness","mean"),
        corrected_mean=("fitness_best","mean"),historical_median=("historical_fitness","median"),
        corrected_median=("fitness_best","median"),historical_sd=("historical_fitness","std"),
        corrected_sd=("fitness_best","std"),historical_min=("historical_fitness","min"),
        corrected_min=("fitness_best","min"),n_changed=("material_change_gt_1e-6","sum"),
        mean_delta=("delta_corrected_minus_historical","mean"),
    ).reset_index()
    write_csv(tables/"f14_historical_vs_corrected_by_configuration.csv",f14_by_config)

    # Compare recalculated products with their archived counterparts.
    current_hypothesis=pd.read_csv(RESULTS/"tables_all"/"tab_hypothesis_summary.csv") if (RESULTS/"tables_all"/"tab_hypothesis_summary.csv").exists() else None
    old_h1=json.loads((RESULTS/"tests"/"h1_friedman_nemenyi"/"summary.json").read_text(encoding="utf-8"))
    old_h4_summary=json.loads((RESULTS/"tests"/"h4_wilcoxon_vs_baseline"/"summary.json").read_text(encoding="utf-8"))
    old_h3=pd.read_csv(RESULTS/"tests"/"h3_function_dispersion"/"function_dispersion.csv")
    old_gran=pd.read_csv(RESULTS/"level3_rankings"/"granularity_by_rule.csv")
    old_function=pd.read_csv(RESULTS/"level3_rankings"/"function_level_per_function.csv")
    old_rule_summary=pd.read_csv(RESULTS/"level3_rankings"/"rule_pair_summary.csv")
    old_runtime=old_function[["function","runtime_overhead_pct"]] if "runtime_overhead_pct" in old_function else pd.DataFrame(columns=["function","runtime_overhead_pct"])
    dispersion_compare=old_h3.merge(dispersion,on=["function","n_labels"],suffixes=("_historical","_consolidated"),validate="one_to_one")
    for metric in ("rank_sd_across_R","loggap_sd_across_R"):
        dispersion_compare[f"delta_{metric}"]=dispersion_compare[f"{metric}_consolidated"]-dispersion_compare[f"{metric}_historical"]
    write_csv(tables/"rq3_function_dispersion_before_after.csv",dispersion_compare)
    gran_compare=old_gran.merge(granularity,on="rule_set",suffixes=("_historical","_consolidated"),validate="one_to_one")
    write_csv(tables/"rq3_granularity_before_after.csv",gran_compare)
    function_compare=old_function.merge(per_function,on="function",suffixes=("_historical","_consolidated"),validate="one_to_one")
    write_csv(tables/"function_level_before_after.csv",function_compare)
    runtime_compare=old_runtime.merge(runtime,on="function",how="outer",validate="one_to_one")
    runtime_compare["delta_overhead_pct_unpaired_minus_paired"]=(
        runtime_compare["unpaired_ratio_of_medians_overhead_pct"]-runtime_compare["runtime_overhead_pct"])
    write_csv(tables/"runtime_before_after.csv",runtime_compare)
    current_hypothesis_text=MANUSCRIPT_RESULTS.read_text(encoding="utf-8")
    changes=[]
    def add_change(section,claim,old_value,new_value,required_action,status="Recalculate"):
        changes.append({"manuscript_section":section,"claim_or_output":claim,
                        "current_value":old_value,"consolidated_value":new_value,
                        "required_action":required_action,"status":status})
    add_change("5.1 / RQ1", "Friedman omnibus / CD",
               f"chi2={old_h1['friedman']['chi2']:.6g}, p={old_h1['friedman']['p_value']:.6g}, CD={old_h1['critical_difference']['CD']:.4f}",
               f"chi2={h1['friedman_chi2']:.6g}, p={h1['friedman_p']:.6g}, CD={h1['cd']:.4f}",
               "Update global-ranking evidence, critical-difference group, and CD figure.")
    old_top=old_mean.iloc[0].configuration_id if "old_mean" in locals() else None
    add_change("5.1 / RQ1", "Top configuration and rank changes",
               f"old leader={old_top}; configs with changed mean rank={(rank_compare.delta_mean_rank.abs()>1e-12).sum()}",
               f"new leader={mean_ranks.iloc[0].configuration_id}; configs with changed mean rank={(rank_compare.delta_mean_rank.abs()>1e-12).sum()}",
               "Update top-config table, global prose, Nemenyi interpretations, and CD figure.")
    add_change("5.2 / RQ2", "Class and dimensional-regime rankings",
               f"old leaders={old_h5['winners_by_class']}; S1/S2 tau={old_h5['kendall_tau_S1_vs_S2']:.4f}, p={old_h5['kendall_p_S1_vs_S2']:.4f}",
               f"new class leaders={class_winners[['problem_class','configuration_id']].to_dict('records')}; S1/S2 tau={tau_s1_s2:.4f}, p={p_s1_s2:.4f}",
               "Update class rankings, Kendall tables, S1/S2 specialists, Pareto figure and interpretation.")
    old_h3_medians=old_h3.groupby("n_labels").agg(rank_sd=("rank_sd_across_R","median"),loggap_sd=("loggap_sd_across_R","median")).to_dict("index")
    add_change("5.3 / RQ3", "Function-level descriptive dispersion",
               json.dumps(safe_json(old_h3_medians)),json.dumps(safe_json(rq3["summary"]["rank_dispersion_median_by_n"])),
               "Update descriptive RQ3 summaries/plots. Do not restore paired/crossed run_id inference.")
    old_rq4=old_h4_summary.get("global",old_h4_summary)
    add_change("5.4 / RQ4", "Independent FCS-versus-PSO comparisons",
               json.dumps(old_rq4),json.dumps(h4_total),
               "Replace paired Wilcoxon wording, counts, p-values and outcomes with independent Mann–Whitney results; A12 is recomputed.")
    add_change("5.4 / Table 11", "Eight rule-pattern contrasts",
               old_rule_summary.to_json(orient="records"),rule_summary.to_json(orient="records"),
               "Replace paired-test claims/counts with independent tests; reconcile archived row-level discrepancies first.")
    changed_instances=per_instance[per_instance.function.eq("F14")]
    add_change("5.2 / Table function-level", "F14 row and per-instance winner/test",
               "Historical F14 implementation and archived paired p-value/A12.",
               f"Corrected F14 has {int(delta_frame['material_change_gt_1e-6'].sum())} material run fitness changes; revised F14 instance summary={changed_instances.to_dict('records')}",
               "Update F14 rows, function-level statistics, F14-specific interpretations and oracle counts.")
    add_change("5.6 / Runtime", "Runtime overhead estimator",
               "Median of per-run ratios after joining FCS/PSO by run_id.",
               "Ratio of independent group medians; see runtime_unpaired_ratio_of_medians.csv.",
               "Replace paired-runtime language and all displayed overhead values; no run_id join.")
    add_change("5.7 / Dynamics", "Mean w/XPL and representative F14 convergence",
               "Old 62-instance dynamics included the incorrect F14 objective.",
               "Recomputed from corrected F14 blobs plus historical non-F14 blobs; see dynamic summaries and figures.",
               "Replace all-62-instance w/XPL figures and F14 convergence panel; F1/F9/F23 scores remain historical.")
    add_change("Appendices / figures", "Function heatmap, class map, F14 dispersion, figures",
               "Generated from old F14 scores and paired RQ4 artifacts.",
               "Recomputed outputs are saved under the versioned package; S1-only scaling curves are unaffected.",
               "Replace affected figures/tables from this package; no manuscript assets were overwritten.")
    changes_df=pd.DataFrame(changes)
    write_csv(tables/"manuscript_change_register.csv",changes_df)

    # Stream historical iteration data and replace old F14 blobs with corrected blobs.
    trajectories,convergence=stream_dynamics(frame,per_function,stats_ci)
    write_csv(tables/"dynamics_trajectory_by_configuration.csv",trajectories)
    write_csv(tables/"convergence_representative_summary.csv",convergence)

    figfiles=save_figures(figures,mean_ranks,h1["cd"],class_stats,sub_rank,
        h4_summary,rule_summary,per_instance,runtime,frame,trajectories,convergence,
        f14_by_config,ranks,rq3["benchmark_wide_aggregate"])

    old_rule_mismatch=rule_discrepancy
    # Audit current legacy outputs against consolidated samples; it is not used for inference.
    write_json(analyses/"historical_output_reconciliation.json",{
        "rq1_old_summary":old_h1,
        "rq4_old_global_summary":old_h4_summary,
        "table11_archived_discrepancy":old_rule_mismatch,
        "table11_discrepant_functions":rule_detail.loc[
            rule_detail.archived_a12_mismatch | rule_detail.archived_p_mismatch_vs_current_paired,
            "function"].value_counts().to_dict(),
        "paired_recalculation_use": "audit only; not considered valid inference because run_id is not a shared-seed block",
    })

    f14_deltas=delta_frame.delta_corrected_minus_historical
    report={
        "title":"Consolidated statistical dataset validation",
        "version":OUT.name,
        "dataset":validation,
        "analysis_methods":{
            "rq1":"Median normalized gap over 31 runs per configuration-instance; within-instance average ranks; Friedman and Nemenyi.",
            "rq2_rq5":"Descriptive gap_median aggregation by class/subset; minimum ranks; Kendall tau for rank concordance.",
            "rq3":"Descriptive function-level rank/log-gap dispersion only. Crossed run_id bootstrap not used because historical run_id does not encode common seeds.",
            "rq4":"Two-sided Mann–Whitney U, independent 31-vs-31 samples, asymptotic continuity correction; A12; Bonferroni 0.05/1984.",
            "table11":"Two-sided Mann–Whitney U for independent samples, per pair/granularity/instance; unadjusted alpha=0.05 to match original family policy; A12.",
            "runtime":"Ratio of independent sample medians; no run_id pairing or paired runtime inference.",
        },
        "rq1":h1,"rq2_class_winners":class_winners[["problem_class","configuration_id","gap_median_mean","rank"]].to_dict("records"),
        "rq2_class_taus":class_tau,
        "rq3":rq3["summary"],"rq4":h4_total,
        "rq4_fcs_3_r1":h4_summary[h4_summary.configuration_id.eq("FCS-3-R1")].iloc[0].to_dict(),
        "rq5_tau_s1_s2":float(tau_s1_s2),"rq5_p_s1_s2":float(p_s1_s2),
        "rq5_leaders":sub_winners[["subgroup","configuration_id","gap_median_mean","rank"]].to_dict("records"),
        "rule_pair_summary":rule_summary.to_dict("records"),
        "f14_comparison":{
            "n_runs":len(delta_frame),"material_changes_abs_gt_1e-6":int(delta_frame["material_change_gt_1e-6"].sum()),
            "corrected_lower":int((f14_deltas < -1e-6).sum()),
            "equal_within_1e-6":int((f14_deltas.abs() <= 1e-6).sum()),
            "corrected_higher":int((f14_deltas > 1e-6).sum()),
            "historical_mean":float(delta_frame.historical_fitness.mean()),
            "corrected_mean":float(delta_frame.fitness_best.mean()),
            "historical_median":float(delta_frame.historical_fitness.median()),
            "corrected_median":float(delta_frame.fitness_best.median()),
            "historical_best":float(delta_frame.historical_fitness.min()),
            "corrected_best":float(delta_frame.fitness_best.min()),
            "mean_delta":float(f14_deltas.mean()),"median_delta":float(f14_deltas.median()),
            "min_delta":float(f14_deltas.min()),"max_delta":float(f14_deltas.max()),
        },
        "runtime_method":"Unpaired ratio of medians; current paired overheads are unsupported.",
        "blocked_H3_note":"The previous crossed-function/run_id bootstrap was not reissued as confirmatory; run_id does not identify common-seed blocks.",
        "manuscript_changes_csv":str(tables/"manuscript_change_register.csv"),
        "figures_generated":figfiles,
        "outputs":{
            "consolidated_csv":str(OUT/"consolidated_level1.csv"),
            "consolidated_parquet":str(OUT/"consolidated_level1.parquet"),
            "tables":str(tables),"analyses":str(analyses),"figures":str(figures),
        },
        "recommendation":"Data/scores are validated for independent-sample descriptive and inferential recalculation. Do not treat run_id as common-seed pairing. Before designating the package definitive, reconcile the archived Table 11 row-level discrepancies and decide whether the paper's H3 blocked inference is excluded or redesigned. Manuscript and historical outputs were not modified.",
    }
    write_json(OUT/"validation_report.json",report)
    (OUT/"README.md").write_text(render_readme(report,changes_df),encoding="utf-8")
    print(json.dumps({"output":str(OUT),"validation":validation,
                      "RQ1":h1,"RQ4":h4_total,"RQ4_FCS3R1":report["rq4_fcs_3_r1"],
                      "F14":report["f14_comparison"],"figures":len(figfiles)},indent=2,default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())