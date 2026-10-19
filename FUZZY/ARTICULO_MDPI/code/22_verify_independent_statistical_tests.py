#!/usr/bin/env python
"""Independent verification of final RQ4 and Table 11 calculations.

The verifier does not call the analysis module's A12 or Mann–Whitney helpers.
It computes A12 from sorted samples and computes the asymptotic Mann–Whitney
normal approximation from average ranks and tie-corrected variance, then checks
both against SciPy and the saved versioned outputs.
"""
from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, norm, rankdata, wilcoxon


ROOT = Path(__file__).resolve().parents[3]
MDPI = ROOT / "FUZZY" / "ARTICULO_MDPI"
PACKAGE = MDPI / "results" / "final_dataset_20261015"
OUT = PACKAGE / "analyses" / "independent_test_verification_provenance_20261015"
META = PACKAGE / "consolidated_level1.parquet"
H4_DETAIL = PACKAGE / "tables" / "rq4_independent_mann_whitney_details.csv"
RULE_DETAIL = PACKAGE / "tables" / "table11_independent_mann_whitney_details.csv"
HIST_RULE_DETAIL = MDPI / "results" / "level3_rankings" / "rule_pair_per_instance.csv"
HIST_META_CSV = MDPI / "results" / "level1_raw" / "experiments_meta.csv"
HIST_META_PARQUET = MDPI / "results" / "level1_raw" / "experiments_meta.parquet"
HIST_RULE_SCRIPT = MDPI / "archive" / "code_legacy_20261015" / "12_analyze_rule_structure.py"
ALPHA = 0.05


def manual_a12(first: np.ndarray, second: np.ndarray) -> float:
    """P(first < second) + 0.5 P(tie), independently via sorted second sample."""
    ordered = np.sort(second)
    less_or_equal = np.searchsorted(ordered, first, side="right")
    less = np.searchsorted(ordered, first, side="left")
    wins_for_first = int((len(second) - less_or_equal).sum())
    ties = int((less_or_equal - less).sum())
    return (wins_for_first + 0.5 * ties) / (len(first) * len(second))


def manual_mann_whitney(first: np.ndarray, second: np.ndarray) -> tuple[float, float]:
    """Return U(first), two-sided asymptotic p with tie and continuity correction."""
    n1, n2 = len(first), len(second)
    combined = np.concatenate((first, second))
    ranks = rankdata(combined, method="average")
    u1 = float(ranks[:n1].sum() - n1 * (n1 + 1) / 2)
    _, tie_counts = np.unique(combined, return_counts=True)
    n = n1 + n2
    tie_term = float(np.sum(tie_counts.astype(float) ** 3 - tie_counts))
    variance = n1 * n2 / 12.0 * (n + 1.0 - tie_term / (n * (n - 1.0)))
    if variance <= 0:
        return u1, 1.0
    difference = abs(u1 - n1 * n2 / 2.0)
    # scipy's two-sided continuity correction moves U 0.5 toward its null mean.
    corrected = max(0.0, difference - 0.5) if difference > 0 else 0.0
    z = corrected / math.sqrt(variance)
    return u1, float(2.0 * norm.sf(z))


def build_samples(meta: pd.DataFrame) -> tuple[dict, dict, dict]:
    samples = {}
    for (config, instance), block in meta.groupby(["configuration_id", "benchmark_instance"], sort=False):
        ordered = block.sort_values("run_id")
        if len(ordered) != 31 or ordered.run_id.nunique() != 31:
            raise ValueError(f"Expected 31 distinct run_id values: {config}/{instance}")
        samples[(config, instance)] = ordered.fitness_best.to_numpy(dtype=float)
    info = meta.drop_duplicates("configuration_id").set_index("configuration_id")
    instances = sorted(meta.benchmark_instance.unique())
    return samples, info, {instance: samples[("PSO", instance)] for instance in instances}


def prepare_legacy_meta(path: Path, file_type: str) -> pd.DataFrame:
    columns = ["mh_family", "n_labels", "rule_set", "function", "dim", "run_id", "fitness_best"]
    if file_type == "csv":
        frame = pd.read_csv(path, usecols=columns)
    else:
        frame = pd.read_parquet(path, columns=columns)
    frame = frame[frame.mh_family == "PSO_FCS"].copy()
    frame["n_labels"] = frame.n_labels.astype(int)
    frame["dim"] = frame.dim.astype(int)
    frame["instance"] = frame.function + "_D" + frame.dim.astype(str)
    frame["configuration_id"] = "FCS-" + frame.n_labels.astype(str) + "-" + frame.rule_set
    return frame


def reproduce_legacy_table(meta: pd.DataFrame, archived: pd.DataFrame, snapshot: str) -> pd.DataFrame:
    rows = []
    for row in archived.itertuples(index=False):
        block_a = meta[(meta.rule_set == row.rule_a) & (meta.n_labels == row.n_labels)
                       & (meta.instance == row.instance)].sort_values("run_id")
        block_b = meta[(meta.rule_set == row.rule_b) & (meta.n_labels == row.n_labels)
                       & (meta.instance == row.instance)].sort_values("run_id")
        first = block_a.fitness_best.to_numpy(dtype=float)
        second = block_b.fitness_best.to_numpy(dtype=float)
        if len(first) != 31 or len(second) != 31:
            raise ValueError(f"Historical sample size differs from 31: {snapshot}/{row.pair}/{row.instance}")
        effect = manual_a12(first, second)
        if np.allclose(first, second):
            p_value = 1.0
        else:
            try:
                p_value = float(wilcoxon(first, second, alternative="two-sided", zero_method="wilcox").pvalue)
            except ValueError:
                p_value = 1.0
        rows.append({
            "snapshot": snapshot, "kind": row.kind, "pair": row.pair,
            "rule_a": row.rule_a, "rule_b": row.rule_b, "n_labels": row.n_labels,
            "instance": row.instance, "function": row.function,
            "archived_a12": row.a12, "reproduced_a12": effect,
            "archived_paired_p": row.p_value, "reproduced_paired_p": p_value,
            "a12_differs": not np.isclose(effect, row.a12, atol=1e-12, rtol=0),
            "paired_p_differs": not np.isclose(p_value, row.p_value, atol=1e-12, rtol=0),
        })
    return pd.DataFrame(rows)


def main() -> int:
    required = (META, H4_DETAIL, RULE_DETAIL, HIST_RULE_DETAIL, HIST_META_CSV,
                HIST_META_PARQUET, HIST_RULE_SCRIPT)
    for path in required:
        if not path.exists():
            raise FileNotFoundError(path)
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite audit evidence {OUT}")
    OUT.mkdir(parents=True, exist_ok=False)

    meta = pd.read_parquet(META)
    samples, info, baseline = build_samples(meta)
    h4 = pd.read_csv(H4_DETAIL)
    rules = pd.read_csv(RULE_DETAIL)
    if len(h4) != 1_984 or len(rules) != 1_984:
        raise ValueError("Expected 1,984 H4 tests and 1,984 rule-pattern tests")

    h4_rows = []
    for row in h4.itertuples(index=False):
        first = samples[(row.configuration_id, row.benchmark_instance)]
        second = baseline[row.benchmark_instance]
        u_manual, p_manual = manual_mann_whitney(first, second)
        effect_manual = manual_a12(first, second)
        scipy = mannwhitneyu(first, second, alternative="two-sided", method="asymptotic", use_continuity=True)
        h4_rows.append({
            "configuration_id": row.configuration_id,
            "benchmark_instance": row.benchmark_instance,
            "n_fcs": len(first), "n_pso": len(second),
            "saved_u": row.mann_whitney_u,
            "manual_u": u_manual, "scipy_u": float(scipy.statistic),
            "saved_p": row.mann_whitney_p_two_sided,
            "manual_p": p_manual, "scipy_p": float(scipy.pvalue) if np.isfinite(scipy.pvalue) else 1.0,
            "saved_a12": row.a12_fcs_vs_pso, "manual_a12": effect_manual,
            "all_observations_tied": bool(np.unique(np.concatenate((first, second))).size == 1),
        })

    rule_rows = []
    for row in rules.itertuples(index=False):
        first_config = f"FCS-{row.n_labels}-{row.rule_a}"
        second_config = f"FCS-{row.n_labels}-{row.rule_b}"
        first = samples[(first_config, row.benchmark_instance)]
        second = samples[(second_config, row.benchmark_instance)]
        u_manual, p_manual = manual_mann_whitney(first, second)
        effect_manual = manual_a12(first, second)
        scipy = mannwhitneyu(first, second, alternative="two-sided", method="asymptotic", use_continuity=True)
        rule_rows.append({
            "pair": row.pair, "n_labels": row.n_labels,
            "benchmark_instance": row.benchmark_instance,
            "n_first": len(first), "n_second": len(second),
            "saved_u": row.mann_whitney_u,
            "manual_u": u_manual, "scipy_u": float(scipy.statistic),
            "saved_p": row.mann_whitney_p_two_sided,
            "manual_p": p_manual, "scipy_p": float(scipy.pvalue) if np.isfinite(scipy.pvalue) else 1.0,
            "saved_a12": row.a12_first_vs_second, "manual_a12": effect_manual,
            "all_observations_tied": bool(np.unique(np.concatenate((first, second))).size == 1),
        })

    h4_check = pd.DataFrame(h4_rows)
    rule_check = pd.DataFrame(rule_rows)
    for name, checked in (("RQ4", h4_check), ("Table 11", rule_check)):
        required_finite = checked[["manual_u", "scipy_u", "saved_p", "manual_p", "scipy_p",
                                   "saved_a12", "manual_a12"]]
        if not np.isfinite(required_finite.to_numpy(dtype=float)).all():
            raise ValueError(f"Non-finite recomputed statistic/effect size in {name}")
    tolerance = 1e-10
    checks = {}
    for name, checked in (("RQ4", h4_check), ("Table 11", rule_check)):
        saved_u_present = checked.saved_u.notna()
        missing_u_valid = checked.loc[~saved_u_present, "all_observations_tied"].all()
        if (~saved_u_present).any():
            missing_rows = checked.loc[~saved_u_present]
            missing_u_valid = bool(
                missing_u_valid
                and np.allclose(missing_rows.manual_u, missing_rows.scipy_u, atol=tolerance, rtol=0)
                and np.allclose(missing_rows.manual_p, 1.0, atol=tolerance, rtol=0)
                and np.allclose(missing_rows.manual_a12, 0.5, atol=tolerance, rtol=0)
            )
        checks[name] = {
            "tests": len(checked),
            "tests_with_saved_U_omitted": int((~saved_u_present).sum()),
            "manual_vs_saved_max_abs_U": float((checked.loc[saved_u_present, "manual_u"] - checked.loc[saved_u_present, "saved_u"]).abs().max()),
            "manual_vs_saved_max_abs_p": float((checked.manual_p - checked.saved_p).abs().max()),
            "manual_vs_saved_max_abs_A12": float((checked.manual_a12 - checked.saved_a12).abs().max()),
            "scipy_vs_manual_max_abs_p": float((checked.scipy_p - checked.manual_p).abs().max()),
            "U_matches": bool(missing_u_valid and np.allclose(checked.loc[saved_u_present, "manual_u"], checked.loc[saved_u_present, "saved_u"], atol=tolerance, rtol=0)),
            "p_matches": bool(np.allclose(checked.manual_p, checked.saved_p, atol=tolerance, rtol=0)),
            "A12_matches": bool(np.allclose(checked.manual_a12, checked.saved_a12, atol=tolerance, rtol=0)),
            "scipy_p_matches_manual": bool(np.allclose(checked.scipy_p, checked.manual_p, atol=tolerance, rtol=0)),
        }
        if not all(checks[name][key] for key in ("U_matches", "p_matches", "A12_matches", "scipy_p_matches_manual")):
            raise AssertionError(f"Independent verification failed for {name}: {checks[name]}")

    h4_check.to_csv(OUT / "rq4_manual_mann_whitney_a12_verification.csv", index=False)
    rule_check.to_csv(OUT / "table11_manual_mann_whitney_a12_verification.csv", index=False)

    # Reproduce the archived routine from each surviving historical data snapshot.
    old_rule = pd.read_csv(HIST_RULE_DETAIL)
    historical_csv = prepare_legacy_meta(HIST_META_CSV, "csv")
    historical_parquet = prepare_legacy_meta(HIST_META_PARQUET, "parquet")
    csv_reproduction = reproduce_legacy_table(historical_csv, old_rule, "historical_csv")
    parquet_reproduction = reproduce_legacy_table(historical_parquet, old_rule, "historical_parquet")
    historical_reproduction = pd.concat([csv_reproduction, parquet_reproduction], ignore_index=True)
    historical_reproduction.to_csv(OUT / "historical_table11_reproduction.csv", index=False)

    old_csv_scores = historical_csv.rename(columns={"instance": "benchmark_instance"})
    old_parquet_scores = historical_parquet.rename(columns={"instance": "benchmark_instance"})
    score_keys = ["configuration_id", "benchmark_instance", "run_id"]
    csv_vs_parquet = old_csv_scores.merge(
        old_parquet_scores[score_keys + ["fitness_best"]], on=score_keys,
        suffixes=("_csv", "_parquet"), validate="one_to_one",
    )
    csv_vs_parquet["absolute_score_delta"] = (
        csv_vs_parquet.fitness_best_csv - csv_vs_parquet.fitness_best_parquet
    ).abs()
    consolidated_fuzzy = meta[meta.configuration_id.str.startswith("FCS-")]
    parquet_vs_final = old_parquet_scores.merge(
        consolidated_fuzzy[["configuration_id", "benchmark_instance", "run_id", "fitness_best"]],
        on=["configuration_id", "benchmark_instance", "run_id"],
        suffixes=("_parquet", "_final"), validate="one_to_one",
    )
    parquet_vs_final["absolute_score_delta"] = (
        parquet_vs_final.fitness_best_parquet - parquet_vs_final.fitness_best_final
    ).abs()
    score_summary = []
    for label, frame in (("historical_csv_vs_parquet", csv_vs_parquet),
                         ("historical_parquet_vs_final", parquet_vs_final)):
        frame = frame.assign(function=frame.benchmark_instance.str.split("_").str[0])
        for function, group in frame.groupby("function"):
            score_summary.append({
                "comparison": label, "function": function, "rows": len(group),
                "exact_score_differences": int((group.absolute_score_delta != 0).sum()),
                "differences_over_1e-12": int((group.absolute_score_delta > 1e-12).sum()),
                "maximum_absolute_difference": float(group.absolute_score_delta.max()),
            })
    score_summary = pd.DataFrame(score_summary)
    score_summary.to_csv(OUT / "historical_snapshot_score_differences.csv", index=False)

    final_vs_archived = rules.merge(
        old_rule[["pair", "n_labels", "instance", "a12", "p_value"]],
        left_on=["pair", "n_labels", "benchmark_instance"],
        right_on=["pair", "n_labels", "instance"], validate="one_to_one",
    )
    final_vs_archived["a12_diff"] = final_vs_archived.a12_first_vs_second - final_vs_archived.a12
    final_vs_archived["p_diff"] = final_vs_archived.mann_whitney_p_two_sided - final_vs_archived.p_value
    by_function = final_vs_archived.groupby("function").agg(
        rows=("pair", "size"), a12_mismatch_rows=("archived_a12_mismatch", "sum"),
        p_mismatch_rows=("archived_p_mismatch_vs_current_paired", "sum"),
        max_abs_A12_diff=("a12_diff", lambda values: float(np.max(np.abs(values)))),
        max_abs_independent_p_diff=("p_diff", lambda values: float(np.max(np.abs(values)))),
    ).reset_index()
    by_function.to_csv(OUT / "final_vs_archived_table11_by_function.csv", index=False)

    stat = {}
    for path in required:
        stat[str(path.relative_to(ROOT))] = {
            "sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
            "modified": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(),
            "bytes": path.stat().st_size,
        }
    report = {
        "audit": "Final independent-test verification; all checks use final_dataset_20261015 consolidated samples.",
        "independent_test_verification": checks,
        "RQ4_family": {"tests": len(h4_check), "Bonferroni_alpha": 0.05 / 1984,
                       "two_sided": True, "sample_sizes": [31, 31]},
        "Table11_family": {"tests": len(rule_check), "alpha": 0.05,
                            "adjustment": "none in the original Table 11 family policy",
                            "sample_sizes": [31, 31]},
        "historical_Table11_discrepancies": {
            "a12_mismatch_rows": int(rules.archived_a12_mismatch.sum()),
            "paired_p_mismatch_rows_vs_current_consolidated_samples": int(rules.archived_p_mismatch_vs_current_paired.sum()),
            "rows_with_either_discrepancy": int((rules.archived_a12_mismatch | rules.archived_p_mismatch_vs_current_paired).sum()),
            "A12_mismatches_outside_F14": int((rules.archived_a12_mismatch & rules.function.ne("F14")).sum()),
            "p_mismatches_outside_F14": int((rules.archived_p_mismatch_vs_current_paired & rules.function.ne("F14")).sum()),
            "by_function_csv": str(OUT / "archived_table11_discrepancies_by_function.csv"),
        },
        "historical_Table11_reproduction": {
            "historical_csv_rows": len(csv_reproduction),
            "historical_csv_A12_mismatches": int(csv_reproduction.a12_differs.sum()),
            "historical_csv_paired_p_mismatches": int(csv_reproduction.paired_p_differs.sum()),
            "historical_parquet_rows": len(parquet_reproduction),
            "historical_parquet_A12_mismatches": int(parquet_reproduction.a12_differs.sum()),
            "historical_parquet_paired_p_mismatches": int(parquet_reproduction.paired_p_differs.sum()),
        },
        "root_cause_assessment": "The non-F14 discrepancy is attributable to CSV float serialization/round-trip precision: the archived Table 11 reproduces exactly from experiments_meta.csv (0/1,984 A12 and 0/1,984 paired-p mismatches), while the corresponding full-precision historical Parquet yields 37 non-F14 A12 and 52 non-F14 paired-p mismatches. The historical Parquet matches the consolidated PSO_FCS scores exactly outside corrected F14. Tiny CSV/Parquet score deltas can change pairwise ties/ranks and Wilcoxon differences. F14 correction separately changes F14 comparisons. The current script documents this CSV-based procedure, but its filesystem modification time is later than the archived Table 11 output and no executed-script hash was retained; therefore the exact historical script revision cannot be certified. The new independent Mann–Whitney p-values/A12 are independently verified against consolidated full-precision samples.",
        "execution_version_provenance": {
            "current_rule_analysis_script_modified": datetime.fromtimestamp(HIST_RULE_SCRIPT.stat().st_mtime).astimezone().isoformat(),
            "archived_rule_detail_modified": datetime.fromtimestamp(HIST_RULE_DETAIL.stat().st_mtime).astimezone().isoformat(),
            "current_script_modified_after_archived_detail": HIST_RULE_SCRIPT.stat().st_mtime > HIST_RULE_DETAIL.stat().st_mtime,
            "executed_script_hash_available": False,
            "interpretation": "The historical procedure is exactly reproducible from its CSV input, but the exact byte-level script revision used to create the old detail is not recoverable from retained metadata."
        },
        "manuscript_update_readiness": "NOT READY for final manuscript updates until H3 inference is explicitly removed/reframed or recalculated under a defensible design, and the unadjusted 1,984-test Table 11 interpretation/multiplicity policy is stated and approved. The consolidated data and independent Table 11 recalculation are ready for that decision.",
        "remaining_methodological_issues": [
            "Final RQ3 is descriptive; historical H3 factorial inference is stale and the run_id bootstrap is invalid as common-seed blocking because run_id does not identify a shared seed.",
            "Table 11 reports 1,984 two-sided tests without multiplicity adjustment under the archived policy; treat significance counts as exploratory unless a family-wise or false-discovery policy is adopted and reported.",
            "Use full-precision consolidated/Parquet values for final statistics; do not reproduce Table 11 from the rounded CSV serialization used by the legacy script."
        ],
        "RQ3_H3_audit": json.loads((PACKAGE / "validation_report.json").read_text(encoding="utf-8"))["h3_audit"],
        "source_files": stat,
        "no_PSO_rerun": True,
        "no_historical_outputs_overwritten": True,
        "manuscript_or_database_modified": False,
    }
    (OUT / "verification_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Audit evidence: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())