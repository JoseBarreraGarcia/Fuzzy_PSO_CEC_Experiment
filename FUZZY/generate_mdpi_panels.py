#!/usr/bin/env python
"""Regenerate only the fuzzy panels included in the MDPI paper and SI.

Descriptive titles are kept in LaTeX captions. In-image labels are limited to
panel identifiers (granularity or rule pattern) required to read comparisons.
"""
from __future__ import annotations

from fuzzy_plots import plot_fuzzy_rules_heatmap_panel, plot_3d_surface_panel
from fuzzy_plots_06_10_parametric import (
    plot_06_input_diversity_mf_panel,
    plot_07_input_progress_mf_panel,
    plot_08_output_w_mf_panel,
)


def main() -> int:
    plot_06_input_diversity_mf_panel(input_set="I1", num_labels_list=[3, 5, 7, 9])
    plot_07_input_progress_mf_panel(input_set="I1", num_labels_list=[3, 5, 7, 9])
    plot_08_output_w_mf_panel(num_labels_list=[3, 5, 7, 9])
    plot_fuzzy_rules_heatmap_panel(
        rule_sets=[f"R{i}" for i in range(1, 9)], num_labels=[3, 5, 7, 9]
    )
    plot_3d_surface_panel(
        rule_sets=[f"R{i}" for i in range(1, 9)],
        num_labels=[3, 5, 7, 9], input_set="I1", w_min=0.1, w_max=0.9,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
