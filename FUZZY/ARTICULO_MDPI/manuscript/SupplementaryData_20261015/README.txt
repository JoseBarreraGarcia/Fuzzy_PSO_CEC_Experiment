Supplementary data for the Mathematics article

The run-level file contains the final consolidated outcomes for 63,426 runs: 33 configurations across 62 function-dimension instances, with 31 independent replicates in each group. Each run has a distinct random seed equal to 42 plus its unique experiment identifier; seeds are not shared across configurations. Replicate numbers are local to each configuration-instance group.

run_level_results.csv fields:
- configuration_id: FCS-n-Rk identifier or PSO
- algorithm, n_labels, rule_pattern: configuration descriptors
- function, dimension, benchmark_instance: benchmark identifiers
- replicate: replicate index within the configuration-instance group
- random_seed: unique seed used for the run
- final_best_fitness, normalized_gap, runtime_seconds: final run outcomes

The remaining CSV files contain configuration and class rankings, descriptive RQ3 summaries, independent-sample RQ4 Mann-Whitney tests with Bonferroni adjustment, Table 11 tests with Holm adjustment over all 1,984 comparisons, runtime ratios of independent medians, and controller/convergence summaries. All listed p-values and summary tables use the same final run-level dataset.

The package contains machine-readable data and results rather than copies of article figures or tables. The per-instance A1-A3 table, landscape panels, rule matrices, and dispersion atlas are presented in the article appendices. `landscape_slices_values.csv` retains the numerical samples underlying the illustrative landscape panels. RQ3 is descriptive; no factorial interaction test is supplied.
