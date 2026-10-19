# Final Table 11 Multiplicity Assessment

Holm step-down correction was applied once across the complete family of 1,984 two-sided independent-sample Mann-Whitney tests (8 pairs x 248 comparisons), at familywise alpha 0.05. The saved p-values and A12 values matched the independent manual-rank verification before adjustment.

Nominally significant comparisons: 1450/1,984. Holm-significant comparisons: 1200/1,984. All eight pairwise dominant directions remain supported by more Holm-significant wins than losses.

| Pair | Nominal wins | Nominal NS | Nominal losses | Holm wins | Holm NS | Holm losses | Holm dominant |
|---|---:|---:|---:|---:|---:|---:|:---:|
| R1 vs R2 | 192 | 56 | 0 | 175 | 73 | 0 | R1 |
| R3 vs R4 | 118 | 59 | 71 | 104 | 98 | 46 | R4 |
| R5 vs R8 | 173 | 73 | 2 | 142 | 106 | 0 | R5 |
| R6 vs R7 | 173 | 57 | 18 | 152 | 91 | 5 | R6 |
| R5 vs R7 | 172 | 75 | 1 | 152 | 96 | 0 | R5 |
| R6 vs R8 | 176 | 65 | 7 | 156 | 92 | 0 | R6 |
| R5 vs R6 | 132 | 81 | 35 | 99 | 130 | 19 | R5 |
| R7 vs R8 | 154 | 68 | 26 | 137 | 98 | 13 | R8 |

## Manuscript Changes Needed

- Replace claims that these comparisons were paired by seed or analyzed with paired Wilcoxon tests. The Table 11 results use independent 31-vs-31 Mann-Whitney tests.
- Replace all paired-analysis counts and unadjusted significance labels with this globally Holm-adjusted summary. The dominant direction remains for every pair, but totals are smaller.
- Change the R3 vs R4 strongest-class label from unimodal to multimodal under Holm. The R1/R2, R5/R8 unimodal and R6/R7 scalable-multimodal highlights remain the strongest class-specific rates.
- Keep interpretations limited to associations among these eight implemented rule tables; these contrasts do not identify causal or independent input effects.

## RQ3 and H3

The validated final RQ3 remains descriptive and does not depend on the historical function x run_id bootstrap. No replacement interaction test was introduced. The old bootstrap is not valid as common-seed blocking because run_id is not the seed block.

No manuscript, PSO run, or historical H3 analysis was changed or rerun.
