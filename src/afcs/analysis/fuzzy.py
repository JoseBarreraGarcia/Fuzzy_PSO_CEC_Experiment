"""Scientific diagnostics derived from a canonical Mamdani controller."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

import numpy as np

from afcs.fuzzy import MamdaniController

from .export import AnalysisExportError

_FILES = ("diagnostics.json", "memberships.png", "rules.png", "response.png")


def write_fuzzy_diagnostics(
    controller: MamdaniController,
    directory: str | Path,
    *,
    grid_points: int = 41,
) -> Path:
    """Write sampled diagnostics and three figures; install a hash manifest last.

    Outputs are normalized controller responses, not physical inertia weights or
    campaign results. Response rows index progress and columns index diversity;
    rule rows index diversity and columns index progress.
    """
    if isinstance(grid_points, bool) or not isinstance(grid_points, int):
        raise TypeError("grid_points must be an integer")
    if grid_points < 2:
        raise ValueError("grid_points must be >= 2")
    try:
        import matplotlib
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
    except ImportError as error:
        raise AnalysisExportError(
            "Fuzzy diagnostics require Matplotlib; install the 'analysis' extra"
        ) from error

    coordinates = np.linspace(0.0, 1.0, grid_points).tolist()
    partitions = (
        controller.diversity_partition,
        controller.progress_partition,
        controller.output_partition,
    )
    membership_coordinates = controller.grid.tolist()
    memberships = [
        [
            [membership.degree(value) for value in membership_coordinates]
            for membership in partition
        ]
        for partition in partitions
    ]
    response = []
    boundary_events = []
    for progress in coordinates:
        results = [controller.infer(diversity, progress) for diversity in coordinates]
        response.append([result.normalized_output for result in results])
        boundary_events.append([result.boundary_events for result in results])
    data = {
        "schema_version": "fuzzy_diagnostics_v1",
        "controller": {
            "controller_id": controller.controller_id,
            "version": controller.version,
            "granularity": controller.granularity,
            "rule_base": controller.rule_base,
            "membership_family": controller.membership_family,
            "evaluation_mode": controller.evaluation_mode,
            "zero_overlap_boundary_policy": controller.zero_overlap_boundary_policy,
            "partitions": {
                name: [asdict(membership) for membership in partition]
                for name, partition in zip(
                    ("diversity", "progress", "output"), partitions
                )
            },
        },
        "membership_coordinates": membership_coordinates,
        "membership_degrees": memberships,
        "rules": controller.rules,
        "rule_axes": {"rows": "diversity", "columns": "progress"},
        "diversity_coordinates": coordinates,
        "progress_coordinates": coordinates,
        "response_axes": {"rows": "progress", "columns": "diversity"},
        "normalized_output": response,
        "boundary_events": boundary_events,
    }
    encoded = json.dumps(data, allow_nan=False, indent=2, sort_keys=True) + "\n"
    output_directory = Path(directory)
    title = (
        f"{controller.rule_base}, G={controller.granularity}, "
        f"{controller.membership_family}"
    )
    try:
        output_directory.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=".afcs-fuzzy-diagnostics-", dir=output_directory
        ) as staged_name:
            staged = Path(staged_name)
            (staged / _FILES[0]).write_text(encoded, encoding="utf-8", newline="\n")
            with matplotlib.rc_context({"font.family": "DejaVu Sans", "font.size": 9}):
                figure = Figure(figsize=(12, 4), dpi=160)
                FigureCanvasAgg(figure)
                try:
                    for index, name in enumerate(("Diversity", "Progress", "Output")):
                        axis = figure.add_subplot(1, 3, index + 1)
                        for label, degrees in enumerate(memberships[index]):
                            axis.plot(membership_coordinates, degrees, label=str(label))
                        axis.plot(
                            membership_coordinates,
                            np.sum(memberships[index], axis=0),
                            "k--",
                            label="Sum",
                        )
                        axis.set(
                            xlabel=f"{name} (normalized)",
                            ylabel="Raw membership degree",
                            title=name,
                            xlim=(0.0, 1.0),
                            ylim=(0.0, None),
                        )
                        axis.legend(fontsize=7)
                        axis.grid(alpha=0.25)
                    figure.suptitle(title)
                    figure.tight_layout()
                    figure.savefig(staged / _FILES[1], metadata={"Software": "AFCS"})
                finally:
                    figure.clear()

                figure = Figure(figsize=(6, 5), dpi=160)
                FigureCanvasAgg(figure)
                try:
                    axis = figure.add_subplot(1, 1, 1)
                    image = axis.imshow(
                        controller.rules,
                        origin="lower",
                        interpolation="nearest",
                        vmin=0,
                        vmax=controller.granularity - 1,
                        cmap="viridis",
                    )
                    labels = range(controller.granularity)
                    axis.set_xticks(labels)
                    axis.set_yticks(labels)
                    for diversity, row in enumerate(controller.rules):
                        for progress, consequent in enumerate(row):
                            axis.text(
                                progress,
                                diversity,
                                str(consequent),
                                ha="center",
                                va="center",
                                color="black",
                                bbox={
                                    "facecolor": "white",
                                    "alpha": 0.6,
                                    "edgecolor": "none",
                                    "pad": 1,
                                },
                            )
                    axis.set(
                        xlabel="Progress label index",
                        ylabel="Diversity label index",
                        title=f"Consequent indices: {title}",
                    )
                    figure.colorbar(
                        image, ax=axis, ticks=labels, label="Output label index"
                    )
                    figure.tight_layout()
                    figure.savefig(staged / _FILES[2], metadata={"Software": "AFCS"})
                finally:
                    figure.clear()

                figure = Figure(figsize=(6, 5), dpi=160)
                FigureCanvasAgg(figure)
                try:
                    axis = figure.add_subplot(1, 1, 1)
                    # Center pixels on sampled coordinates, including domain endpoints.
                    half_step = 0.5 / (grid_points - 1)
                    image = axis.imshow(
                        response,
                        origin="lower",
                        interpolation="nearest",
                        extent=(
                            -half_step,
                            1.0 + half_step,
                            -half_step,
                            1.0 + half_step,
                        ),
                        vmin=0.0,
                        vmax=1.0,
                        cmap="viridis",
                        aspect="auto",
                    )
                    axis.set(
                        xlabel="Diversity (normalized)",
                        ylabel="Progress (normalized)",
                        title=f"Sampled response: {title}",
                        xlim=(0.0, 1.0),
                        ylim=(0.0, 1.0),
                    )
                    figure.colorbar(image, ax=axis, label="Normalized output (not w)")
                    figure.tight_layout()
                    figure.savefig(staged / _FILES[3], metadata={"Software": "AFCS"})
                finally:
                    figure.clear()

            manifest = {
                "schema_version": "fuzzy_diagnostics_manifest_v1",
                "matplotlib_version": matplotlib.__version__,
                "files": {
                    filename: hashlib.sha256(
                        (staged / filename).read_bytes()
                    ).hexdigest()
                    for filename in _FILES
                },
            }
            (staged / "manifest.json").write_text(
                json.dumps(manifest, allow_nan=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            for filename in (*_FILES, "manifest.json"):
                os.replace(staged / filename, output_directory / filename)
    except OSError as error:
        raise AnalysisExportError(
            f"Could not write fuzzy diagnostics to {output_directory}: {error}"
        ) from error
    return output_directory / "manifest.json"
