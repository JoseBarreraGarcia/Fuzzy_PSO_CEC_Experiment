#!/usr/bin/env python
"""Sensitivity analysis for tests that used run_id as a pairing key.

Reads the archived level-1 results and original paired-test outputs. Writes all
new files to a dated, separate directory and refuses to overwrite that directory.
No optimizer is run and no manuscript, database, or original result is modified.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon


ROOT = Path(__file__).resolve().parents[3]
MDPI = ROOT / "FUZZY" / "ARTICULO_MDPI"
META = MDPI / "results" / "level1_raw" / "experiments_meta.parquet"
H4_ARCHIVE = MDPI / "results" / "tests" / "h4_wilcoxon_vs_baseline" / "wilcoxon_pairs.csv"
RULE_ARCHIVE = MDPI / "results" / "level3_rankings" / "rule_pair_per_instance.csv"
RULE_SUMMARY_ARCHIVE = MDPI / "results" / "level3_rankings" / "rule_pair_summary.csv"
OUT = MDPI / "results" / "tests" / "independent_seed_reanalysis_20261014"

ALPHA = 0.05
RULE_PAIRS = [
    ("mirror", "R1", "R2"),
    ("mirror", "R3", "R4"),
    ("mirror", "R5", "R8"),
    ("mirror", "R6", "R7"),
    ("single-axis", "R5", "R7"),
    ("single-axis", "R6", "R8"),
    ("single-axis", "R5", "R6"),
    ("single-axis", "R7", "R8"),
]


def a12(first: np.ndarray, second: np.ndarray) -> float:
    """P(first < second) + 0.5 P(equal); lower fitness is better."""
    return float(
        ((first[:, None] < second[None, :]).sum()
         + 0.5 * (first[:, None] == second[None, :]).sum())
        / (first.size * second.size)
    )


def category(p_value: float, effect: float, alpha: float, first: str, second: str) -> str:
    if p_value >= alpha:
        return "tie"
    return first if effect > 0.5 else second


def tally(values: pd.Series) -> dict[str, int]:
    counts = values.value_counts().to_dict()
    return {
        "wins": int(counts.get("win", 0)),
        "ties": int(counts.get("tie", 0)),
        "losses": int(counts.get("loss", 0)),
    }


def tally_rule(values: pd.Series, first: str, second: str) -> dict[str, int]:
    counts = values.value_counts().to_dict()
    return {
        "first_wins": int(counts.get(first, 0)),
        "ties": int(counts.get("tie", 0)),
        "second_wins": int(counts.get(second, 0)),
    }


def json_safe(value):
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def paired_h4(first: np.ndarray, second: np.ndarray) -> tuple[float, float]:
    # Preserve the original H4 script's exact-zero convention.
    if np.all(first - second == 0):
        return float("nan"), 1.0
    try:
        stat, p_value = wilcoxon(
            first, second, alternative="two-sided", zero_method="wilcox"
        )
        return float(stat), float(p_value)
    except ValueError:
        return float("nan"), 1.0


def paired_rule(first: np.ndarray, second: np.ndarray) -> float:
    # Preserve the original rule-analysis script's allclose convention.
    if np.allclose(first, second):
        return 1.0
    try:
        return float(wilcoxon(
            first, second, alternative="two-sided", zero_method="wilcox"
        ).pvalue)
    except ValueError:
        return 1.0


def samples_for(meta: pd.DataFrame, mask: pd.Series) -> np.ndarray:
    sample = meta.loc[mask].sort_values("run_id")["fitness_best"].to_numpy(dtype=float)
    if sample.size != 31:
        raise ValueError(f"Expected 31 runs; found {sample.size}")
    if not np.array_equal(np.sort(meta.loc[mask, "run_id"].to_numpy()), np.arange(1, 32)):
        raise ValueError("Expected run identifiers 1..31 exactly once")
    return sample


def h4_analysis(meta: pd.DataFrame, archived: pd.DataFrame, bonf_alpha: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    baseline = meta[meta["mh_family"].eq("PSO")]
    for cfg in sorted(meta.loc[meta["mh_family"].eq("PSO_FCS"), "mh_raw"].unique()):
        cfg_data = meta[meta["mh_raw"].eq(cfg)]
        for instance in sorted(cfg_data["instance"].unique()):
            x = samples_for(meta, meta["mh_raw"].eq(cfg) & meta["instance"].eq(instance))
            y = samples_for(meta, baseline["instance"].eq(instance).reindex(meta.index, fill_value=False))
            # The baseline mask above is reindexed to the full metadata index.
            u_stat, mw_p = mannwhitneyu(
                x, y, alternative="two-sided", method="asymptotic", use_continuity=True
            )
            if not np.isfinite(mw_p):
                mw_p = 1.0
            effect = a12(x, y)
            old = archived[(archived["mh_raw"].eq(cfg)) & archived["instance"].eq(instance)]
            if len(old) != 1:
                raise ValueError(f"Expected one archived H4 row for {cfg} / {instance}")
            old = old.iloc[0]
            w_stat, w_p = paired_h4(x, y)
            if not np.isclose(effect, float(old["a12"]), rtol=0, atol=1e-12):
                raise ValueError(f"Archived H4 A12 does not match source samples: {cfg} / {instance}")
            if not np.isclose(w_p, float(old["p_value"]), rtol=0, atol=1e-12):
                raise ValueError(f"Archived H4 Wilcoxon p does not match source samples: {cfg} / {instance}")
            old_nominal = str(old["direction_alpha_0.05"])
            old_bonf = str(old["direction_bonferroni"])
            new_nominal = category(float(mw_p), effect, ALPHA, "win", "loss")
            new_bonf = category(float(mw_p), effect, bonf_alpha, "win", "loss")
            rows.append({
                "mh_raw": cfg, "n_labels": int(cfg_data["n_labels"].iloc[0]),
                "rule_set": cfg_data["rule_set"].iloc[0], "instance": instance,
                "paired_wilcoxon_stat": w_stat, "paired_wilcoxon_p": w_p,
                "archived_paired_nominal": old_nominal,
                "archived_paired_bonferroni": old_bonf,
                "archived_a12": float(old["a12"]),
                "independent_mann_whitney_u_fcs": float(u_stat),
                "independent_mann_whitney_p": float(mw_p), "a12_pso_fcs": effect,
                "independent_nominal": new_nominal,
                "independent_bonferroni": new_bonf,
                "nominal_changed": old_nominal != new_nominal,
                "bonferroni_changed": old_bonf != new_bonf,
            })
    detail = pd.DataFrame(rows)
    summary = []
    for cfg, block in detail.groupby("mh_raw", sort=True):
        row = {
            "mh_raw": cfg, "n_labels": int(block["n_labels"].iloc[0]),
            "rule_set": block["rule_set"].iloc[0], "n_instances": len(block),
        }
        for label, column in (("paired_nominal", "archived_paired_nominal"),
                              ("independent_nominal", "independent_nominal"),
                              ("paired_bonferroni", "archived_paired_bonferroni"),
                              ("independent_bonferroni", "independent_bonferroni")):
            row.update({f"{label}_{key}": val for key, val in tally(block[column]).items()})
        row["a12_mean"] = float(block["a12_pso_fcs"].mean())
        row["a12_median"] = float(block["a12_pso_fcs"].median())
        row["nominal_tests_changed"] = int(block["nominal_changed"].sum())
        row["bonferroni_tests_changed"] = int(block["bonferroni_changed"].sum())
        summary.append(row)
    return detail, pd.DataFrame(summary)


def rule_analysis(meta: pd.DataFrame, archived: pd.DataFrame,
                  archived_summary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for kind, first, second in RULE_PAIRS:
        for n_labels in (3, 5, 7, 9):
            fcs = meta[meta["n_labels"].eq(n_labels)]
            for instance in sorted(fcs["instance"].unique()):
                first_mask = fcs["rule_set"].eq(first) & fcs["instance"].eq(instance)
                second_mask = fcs["rule_set"].eq(second) & fcs["instance"].eq(instance)
                x = samples_for(fcs, first_mask)
                y = samples_for(fcs, second_mask)
                u_stat, mw_p = mannwhitneyu(
                    x, y, alternative="two-sided", method="asymptotic", use_continuity=True
                )
                if not np.isfinite(mw_p):
                    mw_p = 1.0
                effect = a12(x, y)
                current_w_p = paired_rule(x, y)
                old = archived[(archived["pair"].eq(f"{first} vs {second}"))
                                & archived["n_labels"].eq(n_labels)
                                & archived["instance"].eq(instance)]
                if len(old) != 1:
                    raise ValueError(f"Expected one archived rule row: {first}/{second}, {instance}, n={n_labels}")
                old = old.iloc[0]
                rows.append({
                    "kind": kind, "pair": f"{first} vs {second}", "rule_a": first,
                    "rule_b": second, "n_labels": n_labels, "instance": instance,
                    "function": str(fcs.loc[first_mask, "function"].iloc[0]),
                    "landscape_class": str(old["landscape_class"]),
                    "archived_paired_p": float(old["p_value"]),
                    "recomputed_paired_p_from_current_meta": current_w_p,
                    "independent_mann_whitney_u_first": float(u_stat),
                    "independent_mann_whitney_p": float(mw_p),
                    "archived_a12": float(old["a12"]), "a12_first_vs_second": effect,
                    "archived_winner": str(old["winner"]),
                    "recomputed_paired_winner": category(current_w_p, effect, ALPHA, first, second),
                    "independent_winner": category(float(mw_p), effect, ALPHA, first, second),
                    "archived_a12_differs_from_current": not np.isclose(
                        float(old["a12"]), effect, rtol=0, atol=1e-12
                    ),
                    "archived_p_differs_from_current_paired": not np.isclose(
                        float(old["p_value"]), current_w_p, rtol=0, atol=1e-10
                    ),
                })
    detail = pd.DataFrame(rows)
    summaries = []
    for (kind, pair), block in detail.groupby(["kind", "pair"], sort=False):
        first, second = pair.split(" vs ")
        old = archived_summary[archived_summary["pair"].eq(pair)].iloc[0]
        row = {"kind": kind, "pair": pair, "n_comparisons": len(block)}
        for label, col in (("archive_table", "archived_winner"),
                           ("current_paired_recalc", "recomputed_paired_winner"),
                           ("independent", "independent_winner")):
            row.update({f"{label}_{key}": val for key, val in
                    tally_rule(block[col], first, second).items()})
        row["archive_a12_median"] = float(old["a12_median"])
        row["current_a12_median"] = float(block["a12_first_vs_second"].median())
        row["archive_best_class"] = str(old["best_class"])
        winner_counts = block["independent_winner"].value_counts()
        if winner_counts.get(first, 0) == winner_counts.get(second, 0):
            dominant = "--"
        else:
            dominant = first if winner_counts.get(first, 0) > winner_counts.get(second, 0) else second
        row["independent_dominant"] = dominant
        if dominant == "--":
            row["independent_strongest_in"] = "--"
        else:
            class_rates = block.groupby("landscape_class")["independent_winner"].apply(
                lambda outcomes: float(outcomes.eq(dominant).mean())
            )
            row["independent_strongest_in"] = str(class_rates.idxmax())
        row["archived_a12_mismatches"] = int(block["archived_a12_differs_from_current"].sum())
        row["archived_p_mismatches_vs_current_paired"] = int(block["archived_p_differs_from_current_paired"].sum())
        summaries.append(row)
    return detail, pd.DataFrame(summaries)


def main() -> int:
    inputs = (META, H4_ARCHIVE, RULE_ARCHIVE, RULE_SUMMARY_ARCHIVE)
    for path in inputs:
        if not path.exists():
            raise FileNotFoundError(path)
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite existing output directory: {OUT}")

    meta = pd.read_parquet(META)
    if len(meta) != 63_426:
        raise ValueError(f"Expected 63,426 archived runs; found {len(meta)}")
    meta["instance"] = meta["function"].astype(str) + "_D" + meta["dim"].astype(int).astype(str)
    for _, block in meta.groupby(["mh_raw", "instance"], sort=False):
        if len(block) != 31:
            raise ValueError("Every configuration-instance group must contain 31 runs")

    h4_archive = pd.read_csv(H4_ARCHIVE)
    rule_archive = pd.read_csv(RULE_ARCHIVE)
    rule_summary_archive = pd.read_csv(RULE_SUMMARY_ARCHIVE)
    if len(h4_archive) != 1_984 or len(rule_archive) != 1_984:
        raise ValueError("Expected 1,984 archived rows for each analysis")
    bonf_alpha = ALPHA / 1_984

    h4_detail, h4_summary = h4_analysis(meta, h4_archive, bonf_alpha)
    rule_detail, rule_summary = rule_analysis(meta, rule_archive, rule_summary_archive)

    OUT.mkdir(parents=True, exist_ok=False)
    h4_detail.to_csv(OUT / "rq4_independent_mann_whitney_details.csv", index=False)
    h4_summary.to_csv(OUT / "rq4_before_after_by_configuration.csv", index=False)
    rule_detail.to_csv(OUT / "rule_pairs_independent_details.csv", index=False)
    rule_summary.to_csv(OUT / "rule_pairs_before_after_summary.csv", index=False)

    h4_before = tally(h4_detail["archived_paired_nominal"])
    h4_after = tally(h4_detail["independent_nominal"])
    h4_before_bonf = tally(h4_detail["archived_paired_bonferroni"])
    h4_after_bonf = tally(h4_detail["independent_bonferroni"])
    target = h4_summary[h4_summary["mh_raw"].eq("PSO_FCS:G3:I1:R1:O1")]
    rule_archive_mismatches = rule_detail[
        rule_detail["archived_a12_differs_from_current"]
        | rule_detail["archived_p_differs_from_current_paired"]
    ]
    summary = {
        "source_level1": str(META.relative_to(ROOT)),
        "archived_run_rows": len(meta),
        "configurations": int(meta["mh_raw"].nunique()),
        "instances": int(meta["instance"].nunique()),
        "runs_per_configuration_instance": 31,
        "rq4_tests": len(h4_detail),
        "rule_pair_tests": len(rule_detail),
        "alpha": ALPHA,
        "rq4_bonferroni_family_size": 1_984,
        "rq4_bonferroni_alpha": bonf_alpha,
        "rq4_paired_original_global": {"nominal": h4_before, "bonferroni": h4_before_bonf},
        "rq4_independent_global": {"nominal": h4_after, "bonferroni": h4_after_bonf},
        "rq4_nominal_classifications_changed": int(h4_detail["nominal_changed"].sum()),
        "rq4_bonferroni_classifications_changed": int(h4_detail["bonferroni_changed"].sum()),
        "fcs_3_r1": target.iloc[0].to_dict(),
        "rq4_a12_max_abs_change": float(np.max(np.abs(
            h4_detail["a12_pso_fcs"].to_numpy() - h4_detail["archived_a12"].to_numpy()
        ))),
        "rule_archive_rows_not_reproduced_from_current_level1": len(rule_archive_mismatches),
        "rule_archive_a12_mismatches": int(rule_detail["archived_a12_differs_from_current"].sum()),
        "rule_archive_p_mismatches_vs_paired_recalc": int(
            rule_detail["archived_p_differs_from_current_paired"].sum()
        ),
        "rule_comparison_summary": rule_summary.to_dict(orient="records"),
        "notes": [
            "Mann-Whitney U is two-sided, asymptotic with continuity correction, on independent 31-vs-31 samples.",
            "RQ4 retains Bonferroni alpha=0.05/1984; rule-pattern table retains its original unadjusted alpha=0.05.",
            "A12 is recomputed from the same two empirical samples and is independent of run pairing.",
            "Original paired rule outputs are separately compared with a paired recalculation from current level-1 data because some archived rows do not reproduce.",
            "No PSO was rerun; no original files, database rows, or manuscript files were changed.",
        ],
    }
    (OUT / "summary.json").write_text(
        json.dumps(json_safe(summary), indent=2, allow_nan=False), encoding="utf-8"
    )
    print(f"Output directory: {OUT}")
    print(f"RQ4 tests: {len(h4_detail)}; Bonferroni alpha={bonf_alpha:.12g}")
    print("RQ4 paired nominal:", h4_before, "independent:", h4_after)
    print("RQ4 paired Bonferroni:", h4_before_bonf, "independent:", h4_after_bonf)
    print("FCS-3-R1:", target.to_dict(orient="records")[0])
    print("Rule archive A12 mismatches:", summary["rule_archive_a12_mismatches"])
    print("Rule archive p mismatches vs paired recalculation:", summary["rule_archive_p_mismatches_vs_paired_recalc"])
    print("Rule before/after:")
    print(rule_summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())