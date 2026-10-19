# Analysis Code

Organization as of 2026-10-15. Historical scripts were moved, not discarded.

## Final analysis and verification

| Script | Role |
| --- | --- |
| [21_recalculate_final_dataset.py](21_recalculate_final_dataset.py) | Builds the consolidated dataset and recalculates rankings, descriptive RQ3, independent RQ4, rule contrasts, runtime and dynamics. |
| [22_verify_independent_statistical_tests.py](22_verify_independent_statistical_tests.py) | Independently verifies Mann-Whitney and A12 calculations and records historical provenance. |
| [23_table11_holm_assessment.py](23_table11_holm_assessment.py) | Applies one Holm correction to the complete Table 11 family. |

These scripts use `results/final_dataset_20261015` and historical inputs outside
this folder. Script 21 precedes 22, and 22 precedes 23 when reconstructing their
outputs. Their output directories already exist; the scripts refuse to overwrite
them. They are not routine manuscript-build commands. Do not remove existing
outputs to bypass these safeguards.

Script 22 reads the preserved source at
[12_analyze_rule_structure.py](../archive/code_legacy_20261015/12_analyze_rule_structure.py)
for provenance; it does not execute that historical analysis.

## Retained utilities

| Script | Status |
| --- | --- |
| [04_run_scaling_curves.py](04_run_scaling_curves.py) | Useful scaling analysis; still reads historical level-2 aggregates. |
| [15_generate_mean_dispersion_maps.py](15_generate_mean_dispersion_maps.py) | Generates representative dispersion panels and the appendix atlas; its inputs still point to historical summaries. |
| [16_generate_benchmark_landscapes.py](16_generate_benchmark_landscapes.py) | Generates landscape panels and numerical samples; still recreates the retired Supplementary tree. |
| [_naming.py](_naming.py) | Shared naming helper used by retained and historical utilities. |

Retaining a utility is not an endorsement of rerunning it unchanged. Review its
input dataset and output paths before use. Scripts 15 and 16 can overwrite
manuscript assets. No data paths or scientific logic in these utilities were
changed during this reorganization.

## Preparation and provenance

[20_prepare_corrected_f14.py](20_prepare_corrected_f14.py) preserves the isolated
F14 preparation and validation procedure. It is not part of routine editorial
work, and no optimizer rerun is required for the completed manuscript.

## Historical code

Seventeen earlier scripts and the former reproducibility guide are preserved in
[the legacy archive](../archive/code_legacy_20261015/README.md). Their generated
data remain in their existing results directories because the final analysis
still reads some of them for historical comparisons.

For current availability and build instructions, see
[the reproducibility guide](../REPRODUCIBILITY.md).