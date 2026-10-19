# Consolidated Mathematics dataset and recalculated analyses

Version: `final_dataset_20261015`. This package is separate from all historical outputs and the manuscript.

## Validation

- Records: 63,426; 62 instances; 33 configurations; 2,046 groups of 31 runs.
- Historical F1–F13/F15–F23: 62,403; corrected F14: 1,023.
- Historical actual seeds were not persisted (0); 62,403 values are reconstructed as `42 + historical_exp_id` from the verified runner. Exporter values `42*run_id` are retained separately as synthetic metadata and are never used for inference.
- Corrected F14 actual seeds: `42 + historical_exp_id`; 1,023 unique values recovered and checked.
- Consolidation schema and configuration IDs are validated before any statistical calculation.

## Before / After

- F14 fitness values materially changed (`abs(delta)>1e-6`) in 4/1,023 runs: 3 higher, 1 lower, 1019 unchanged within tolerance.
- F14 mean fitness: 4.24010855 → 4.25220853; median: 2.98210516 → 2.98210516; best: 0.99800384 → 0.99800384.
- RQ4: 1984 independent two-sided Mann–Whitney tests; Bonferroni alpha `2.52016129e-05`. FCS-3-R1 has 30/30/2 nominal and 16/46/0 corrected wins/ties/losses.
- Table 11 uses independent-sample tests; per-pair A12 is reported alongside p-values. Historical row-level outputs are reconciled separately.
- Runtime overhead is a ratio of independent group medians, with no join on `run_id`.

## Manuscript Update Register

See `tables/manuscript_change_register.csv` and `tables/scientific_claim_deltas.csv` for current-output values, recalculated values, and actions by section. Affected sections include 5.1–5.7, the hypothesis summary, function-level table, Table 11, runtime prose, and F14-dependent figures. S1-only dimensional scaling is unaffected.

## Methodological Caveats

- Do not interpret `run_id` as a shared-seed block. RQ4 and Table 11 are recalculated as independent samples.
- The previous H3 two-way bootstrap using function × run_id blocks is not reused as confirmatory inference. RQ3 outputs here are descriptive only; see `tables/h3_artifact_audit.csv` for legacy consumers.
- The archived Table 11 detail does not fully reproduce from the current historical level-1 export; see `analyses/table11_archive_reconciliation.json`.
- Manuscript files and historical output files were not modified. No PSO runs were executed.

## Key Outputs

- `consolidated_level1.csv` / `.parquet`: consolidated run-level dataset with seed provenance.
- `tables/`: RQ tables and before/after comparisons.
- `analyses/`: inferential summaries, reconciliation, and validation details.
- `figures/`: regenerated figures affected by F14 and independent-test changes.
- `tables/h3_artifact_audit.csv`: legacy H3 script/output consumers and their status.
- `validation_report.json`: machine-readable validation and recommendation.
