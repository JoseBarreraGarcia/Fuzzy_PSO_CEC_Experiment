# Historical Analysis Code

These 17 scripts were relocated from `code/` on 2026-10-15, preserving their
current contents byte-for-byte, including uncommitted edits. Earlier copies in
other archive folders were not overwritten. This is an archival snapshot, not an
executable pipeline from this directory.

| Script | Reason for archival |
| --- | --- |
| [00_generate_level1_raw_data.py](00_generate_level1_raw_data.py) | Historical extraction; its seed field uses the old synthetic formula. |
| [01_generate_level2_aggregated_stats.py](01_generate_level2_aggregated_stats.py) | Historical aggregation chain. |
| [02_generate_level3_rankings.py](02_generate_level3_rankings.py) | Historical rankings. |
| [03_run_factorial_anova.py](03_run_factorial_anova.py) | Earlier factorial inference; final RQ3 is descriptive. |
| [05_run_pareto_problemtype.py](05_run_pareto_problemtype.py) | Earlier class and subset summaries. |
| [06_generate_paper_figures.py](06_generate_paper_figures.py) | Mixed historical figure inputs, including superseded tests. |
| [07_generate_paper_tables.py](07_generate_paper_tables.py) | Historical table generation. |
| [08_export_results_to_manuscript.py](08_export_results_to_manuscript.py) | Unconditional export that can overwrite final manuscript assets. |
| [09_run_h1_friedman_nemenyi.py](09_run_h1_friedman_nemenyi.py) | Earlier ranking analysis; final ranks are recalculated by script 21. |
| [10_run_h4_wilcoxon_vs_baseline.py](10_run_h4_wilcoxon_vs_baseline.py) | Paired tests superseded by independent-sample inference. |
| [11_generate_function_level_analysis.py](11_generate_function_level_analysis.py) | Uses earlier tests and overwrites article tables. |
| [12_analyze_rule_structure.py](12_analyze_rule_structure.py) | Historical rule contrasts; retained as required provenance for script 22. |
| [13_analyze_granularity.py](13_analyze_granularity.py) | Depends on the old factorial summary. |
| [14_analyze_controller_dynamics.py](14_analyze_controller_dynamics.py) | Historical trajectories without the consolidated F14 substitution. |
| [17_reanalyze_h3_blocked.py](17_reanalyze_h3_blocked.py) | Exploratory run-id clustering, not shared-seed inference. |
| [18_h3_function_dispersion.py](18_h3_function_dispersion.py) | Descriptive method, but superseded historical inputs and outputs. |
| [19_reanalyze_independent_samples.py](19_reanalyze_independent_samples.py) | Intermediate independent-sample analysis before final consolidation. |

The original [reproducibility guide](REPRODUCIBILITY_legacy.md) is preserved for
history only. Its execution instructions, paths, seed statement and statistical
claims are not current guidance.

Many scripts derive the repository root from their original directory depth and
use the shared naming helper from `code/`. Those assumptions no longer hold when
executing them here. Historical reconstruction requires an isolated restoration
of the original layout, helper version and input snapshots, not a direct run in
this archive. Do not regenerate old outputs over the final manuscript.

Do not delete the historical result files merely because these scripts moved:
scripts 21 and 22 still read historical data for comparisons and provenance.
The preserved script 12 is also a required input of script 22.