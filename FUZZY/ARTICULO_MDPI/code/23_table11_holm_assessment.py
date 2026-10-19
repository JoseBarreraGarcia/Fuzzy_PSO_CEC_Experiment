#!/usr/bin/env python
"""Apply one Holm correction across all independently verified Table 11 tests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "final_dataset_20261015"
DETAIL = PACKAGE / "tables" / "table11_independent_mann_whitney_details.csv"
VERIFICATION = (
    PACKAGE / "analyses" / "independent_test_verification_provenance_20261015"
    / "table11_manual_mann_whitney_a12_verification.csv"
)
VALIDATION = PACKAGE / "validation_report.json"
CONSOLIDATED = PACKAGE / "consolidated_level1.parquet"
OUT = PACKAGE / "analyses" / "table11_holm_assessment_20261015"
ALPHA = 0.05
EXPECTED_TESTS = 1984
EXPECTED_PAIRS = 8
TEST_KEYS = ["pair", "n_labels", "benchmark_instance"]


def holm_adjust(p_values: np.ndarray) -> np.ndarray:
    order = np.argsort(p_values, kind="mergesort")
    multipliers = len(p_values) - np.arange(len(p_values))
    ordered_adjusted = np.maximum.accumulate(p_values[order] * multipliers)
    adjusted = np.empty(len(p_values), dtype=float)
    adjusted[order] = np.minimum(ordered_adjusted, 1.0)
    return adjusted


def direction_counts(block: pd.DataFrame, significant: pd.Series, dominant: str) -> tuple[int, int, int]:
    favored = significant & block.direction.eq(dominant)
    opposite = block.rule_b.iloc[0] if dominant == block.rule_a.iloc[0] else block.rule_a.iloc[0]
    opposed = significant & block.direction.eq(opposite)
    return int(favored.sum()), int((~significant).sum()), int(opposed.sum())


def main() -> int:
    for path in (DETAIL, VERIFICATION, VALIDATION, CONSOLIDATED):
        if not path.exists():
            raise FileNotFoundError(path)
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUT}")
    OUT.mkdir(parents=True, exist_ok=False)

    details = pd.read_csv(DETAIL)
    independent = pd.read_csv(VERIFICATION)
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    if len(details) != EXPECTED_TESTS or details.pair.nunique() != EXPECTED_PAIRS:
        raise ValueError("Table 11 must contain exactly eight pairs and 1,984 tests")
    if not (details.groupby("pair").size() == 248).all():
        raise ValueError("Each Table 11 pair must contain 248 comparisons")
    if not np.isfinite(details.mann_whitney_p_two_sided.to_numpy(dtype=float)).all():
        raise ValueError("Table 11 p-values must all be finite")

    verified = details[TEST_KEYS + ["mann_whitney_p_two_sided", "a12_first_vs_second"]].merge(
        independent[TEST_KEYS + ["manual_p", "manual_a12"]],
        on=TEST_KEYS,
        validate="one_to_one",
    )
    if len(verified) != EXPECTED_TESTS:
        raise ValueError("Independent verification rows do not match the Table 11 test family")
    if not np.allclose(verified.mann_whitney_p_two_sided, verified.manual_p, atol=1e-10, rtol=0):
        raise AssertionError("Saved Table 11 p-values differ from independent verification")
    if not np.allclose(verified.a12_first_vs_second, verified.manual_a12, atol=1e-10, rtol=0):
        raise AssertionError("Saved Table 11 A12 values differ from independent verification")

    details["holm_adjusted_p"] = holm_adjust(details.mann_whitney_p_two_sided.to_numpy(dtype=float))
    details["nominal_significant"] = details.mann_whitney_p_two_sided < ALPHA
    details["holm_significant"] = details.holm_adjusted_p < ALPHA
    details["direction"] = np.select(
        [details.a12_first_vs_second > 0.5, details.a12_first_vs_second < 0.5],
        [details.rule_a, details.rule_b],
        default="tie",
    )
    if (details.holm_significant & details.direction.eq("tie")).any():
        raise AssertionError("A significant comparison has no A12 direction")

    summary_rows = []
    class_rows = []
    for pair, block in details.groupby("pair", sort=False):
        nominal_first = int((block.nominal_significant & block.direction.eq(block.rule_a)).sum())
        nominal_second = int((block.nominal_significant & block.direction.eq(block.rule_b)).sum())
        holm_first = int((block.holm_significant & block.direction.eq(block.rule_a)).sum())
        holm_second = int((block.holm_significant & block.direction.eq(block.rule_b)).sum())
        nominal_dominant = block.rule_a.iloc[0] if nominal_first > nominal_second else block.rule_b.iloc[0]
        holm_dominant = block.rule_a.iloc[0] if holm_first > holm_second else block.rule_b.iloc[0]
        nominal_wins, nominal_nonsig, nominal_losses = direction_counts(
            block, block.nominal_significant, nominal_dominant
        )
        holm_wins, holm_nonsig, holm_losses = direction_counts(
            block, block.holm_significant, holm_dominant
        )
        class_rates = {}
        for problem_class, class_block in block.groupby("problem_class", sort=False):
            wins, nonsig, losses = direction_counts(class_block, class_block.holm_significant, holm_dominant)
            class_rates[problem_class] = wins / len(class_block)
            class_rows.append({
                "pair": pair,
                "holm_dominant_rule": holm_dominant,
                "problem_class": problem_class,
                "comparisons": len(class_block),
                "holm_wins_for_dominant": wins,
                "holm_nonsignificant": nonsig,
                "holm_losses_for_dominant": losses,
                "dominant_significant_win_rate": wins / len(class_block),
            })
        strongest_class = max(class_rates, key=class_rates.get)
        summary_rows.append({
            "pair": pair,
            "family": block.kind.iloc[0],
            "rule_a": block.rule_a.iloc[0],
            "rule_b": block.rule_b.iloc[0],
            "comparisons": len(block),
            "nominal_wins_for_dominant": nominal_wins,
            "nominal_nonsignificant": nominal_nonsig,
            "nominal_losses_for_dominant": nominal_losses,
            "holm_wins_for_dominant": holm_wins,
            "holm_nonsignificant": holm_nonsig,
            "holm_losses_for_dominant": holm_losses,
            "nominal_wins_rule_a": nominal_first,
            "nominal_wins_rule_b": nominal_second,
            "holm_wins_rule_a": holm_first,
            "holm_wins_rule_b": holm_second,
            "nominal_dominant_rule": nominal_dominant,
            "holm_dominant_rule": holm_dominant,
            "direction_survives_holm": nominal_dominant == holm_dominant and holm_wins > holm_losses,
            "strongest_class_by_holm_win_rate": strongest_class,
            "median_A12_rule_a_vs_rule_b": float(block.a12_first_vs_second.median()),
        })

    pair_summary = pd.DataFrame(summary_rows)
    class_summary = pd.DataFrame(class_rows)
    if not pair_summary.direction_survives_holm.all():
        raise AssertionError("At least one nominal dominant direction is not supported after Holm")
    pair_summary.to_csv(OUT / "table11_holm_pair_summary.csv", index=False)
    class_summary.to_csv(OUT / "table11_holm_pair_class_summary.csv", index=False)
    details.to_csv(OUT / "table11_holm_adjusted_1984.csv", index=False)

    rq3_info = validation["rq3"]
    rq3_descriptive = bool(rq3_info["rq3_is_descriptive"])
    h3_audit = validation["h3_audit"]
    no_historical_bootstrap_dependency = (
        not h3_audit["final_RQ3_uses_run_id_as_inferential_block"]
        and not h3_audit["new_interaction_test_introduced"]
        and not h3_audit["historical_common_seed_blocks_established"]
    )
    if not (rq3_descriptive and no_historical_bootstrap_dependency):
        raise AssertionError("RQ3/H3 validation does not match the requested descriptive-only treatment")

    old_strongest = "unimodal"  # Existing generated Table 11 classification.
    new_strongest = pair_summary.loc[pair_summary.pair.eq("R3 vs R4"), "strongest_class_by_holm_win_rate"].iloc[0]
    if new_strongest != "multimodal":
        raise AssertionError("Expected the R3-vs-R4 strongest class to be multimodal after Holm")

    manuscript_claims = [
        {
            "file": "manuscript/sections/05_results.tex",
            "claim": "Rule-pattern contrasts were paired by seed, and the listed wins/losses are paired comparisons.",
            "recommendation": "Replace with independent 31-vs-31 Mann-Whitney comparisons; remove the seed-pairing claim. Report Holm-adjusted wins/non-significant/losses over the complete 1,984-test family.",
        },
        {
            "file": "manuscript/tables/tab_rule_pairs.tex",
            "claim": "Caption and footnote describe paired comparisons and paired Wilcoxon significance at unadjusted alpha=0.05.",
            "recommendation": "Regenerate the table with the Holm counts from this assessment; identify the global Holm family and make clear that wins/losses are based on independent-sample tests.",
        },
        {
            "file": "manuscript/sections/05_results.tex",
            "claim": "Specific counts for R1/R2, R5/R7, R6/R8, R5/R6, R7/R8, and R3/R4 are carried forward from the paired analysis.",
            "recommendation": "Replace those counts with the independent-sample values in table11_holm_pair_summary.csv. All eight overall dominant directions remain supported, but the evidence should be described as an association among these tested rule tables, not a causal input effect.",
        },
        {
            "file": "manuscript/tables/tab_rule_pairs.tex",
            "claim": "R3 vs R4 is strongest in the unimodal class.",
            "recommendation": f"Change the Holm-based strongest class from {old_strongest} to {new_strongest} (largest familywise-significant win rate for dominant rule R4).",
        },
        {
            "file": "manuscript/sections/05_results.tex and manuscript/sections/06_discussion.tex",
            "claim": "Class-specific patterns for R1/R2 and R5/R8 on unimodal functions and R6/R7 on scalable multimodal functions.",
            "recommendation": "These three class rankings remain the highest Holm-significant win rates for their respective dominant patterns; retain only as descriptive, benchmark-specific results and update counts if included.",
        },
        {
            "file": "manuscript/sections/07_conclusion.tex",
            "claim": "Paired results demonstrate that mirror symmetry does not ensure equivalent optimization performance.",
            "recommendation": "Keep the bounded observation but describe the evidence as independent-sample, Holm-adjusted differences; do not imply matched trajectories or common random seeds.",
        },
    ]

    report = {
        "title": "Final Table 11 multiplicity assessment",
        "dataset_version": "final_dataset_20261015",
        "input_tests": len(details),
        "tests_per_rule_pair": 248,
        "rule_pairs": EXPECTED_PAIRS,
        "procedure": "Holm step-down adjustment over all 1,984 two-sided independent-sample Mann-Whitney p-values; alpha=0.05. P-values/A12 were cross-checked against the independent manual rank verification before adjustment.",
        "direction_rule": "For lower-is-better fitness, A12(rule_a vs rule_b)>0.5 favors rule_a; <0.5 favors rule_b. Wins/losses count significant comparisons in the Holm-dominant direction and its opposite; all non-significant tests are counted separately.",
        "nominal_significant_tests": int(details.nominal_significant.sum()),
        "holm_significant_tests": int(details.holm_significant.sum()),
        "nominal_significant_retained_after_holm": int(details.holm_significant.sum()),
        "familywise_alpha": ALPHA,
        "every_pair_direction_survives_holm": bool(pair_summary.direction_survives_holm.all()),
        "pair_summaries": pair_summary.to_dict(orient="records"),
        "r3_r4_strongest_class_before_holm": old_strongest,
        "r3_r4_strongest_class_after_holm": new_strongest,
        "class_summaries": class_summary.to_dict(orient="records"),
        "rq3_h3_confirmation": {
            "rq3_is_descriptive": rq3_descriptive,
            "uses_historical_h3_bootstrap": False,
            "uses_run_id_as_common_seed_block": False,
            "replacement_interaction_test_added": False,
            "basis": rq3_info["blocked_run_id_H3_inference"],
        },
        "manuscript_claims_to_revise": manuscript_claims,
        "input_hashes": {
            "table11_details_sha256": hashlib.sha256(DETAIL.read_bytes()).hexdigest(),
            "independent_verification_sha256": hashlib.sha256(VERIFICATION.read_bytes()).hexdigest(),
            "consolidated_dataset_sha256": hashlib.sha256(CONSOLIDATED.read_bytes()).hexdigest(),
        },
        "manuscript_edited": False,
        "pso_rerun": False,
        "historical_h3_bootstrap_rerun": False,
    }
    (OUT / "table11_holm_assessment.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Final Table 11 Multiplicity Assessment",
        "",
        "Holm step-down correction was applied once across the complete family of 1,984 two-sided independent-sample Mann-Whitney tests (8 pairs x 248 comparisons), at familywise alpha 0.05. The saved p-values and A12 values matched the independent manual-rank verification before adjustment.",
        "",
        f"Nominally significant comparisons: {int(details.nominal_significant.sum())}/1,984. Holm-significant comparisons: {int(details.holm_significant.sum())}/1,984. All eight pairwise dominant directions remain supported by more Holm-significant wins than losses.",
        "",
        "| Pair | Nominal wins | Nominal NS | Nominal losses | Holm wins | Holm NS | Holm losses | Holm dominant |",
        "|---|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for row in pair_summary.itertuples(index=False):
        lines.append(
            f"| {row.pair} | {row.nominal_wins_for_dominant} | {row.nominal_nonsignificant} | {row.nominal_losses_for_dominant} | "
            f"{row.holm_wins_for_dominant} | {row.holm_nonsignificant} | {row.holm_losses_for_dominant} | {row.holm_dominant_rule} |"
        )
    lines += [
        "",
        "## Manuscript Changes Needed",
        "",
        "- Replace claims that these comparisons were paired by seed or analyzed with paired Wilcoxon tests. The Table 11 results use independent 31-vs-31 Mann-Whitney tests.",
        "- Replace all paired-analysis counts and unadjusted significance labels with this globally Holm-adjusted summary. The dominant direction remains for every pair, but totals are smaller.",
        "- Change the R3 vs R4 strongest-class label from unimodal to multimodal under Holm. The R1/R2, R5/R8 unimodal and R6/R7 scalable-multimodal highlights remain the strongest class-specific rates.",
        "- Keep interpretations limited to associations among these eight implemented rule tables; these contrasts do not identify causal or independent input effects.",
        "",
        "## RQ3 and H3",
        "",
        "The validated final RQ3 remains descriptive and does not depend on the historical function x run_id bootstrap. No replacement interaction test was introduced. The old bootstrap is not valid as common-seed blocking because run_id is not the seed block.",
        "",
        "No manuscript, PSO run, or historical H3 analysis was changed or rerun.",
        "",
    ]
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved Table 11 Holm assessment: {OUT}")
    print(f"Nominal significant: {int(details.nominal_significant.sum())}; Holm significant: {int(details.holm_significant.sum())}")
    print(pair_summary[["pair", "nominal_wins_for_dominant", "nominal_nonsignificant", "nominal_losses_for_dominant", "holm_wins_for_dominant", "holm_nonsignificant", "holm_losses_for_dominant", "holm_dominant_rule"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())