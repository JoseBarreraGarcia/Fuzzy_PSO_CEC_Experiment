from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import numpy as np
from matplotlib import rcParams
from matplotlib.figure import Figure
from matplotlib.image import imread

from afcs.analysis import AnalysisExportError, write_fuzzy_diagnostics
from afcs.fuzzy import MamdaniController


def make_controller(
    granularity: int = 3,
    family: str = "triangular_v1",
    overlap: float = 0.0,
) -> MamdaniController:
    return MamdaniController(
        granularity=granularity,
        rule_base="R5",
        membership_family=family,
        diversity_overlap=overlap,
        progress_overlap=0.5,
        output_overlap=1.0,
    )


class TestFuzzyDiagnostics(unittest.TestCase):
    def test_numeric_data_and_hashes_match_canonical_inference(self) -> None:
        for granularity, family, overlap in (
            (3, "triangular_v1", 0.0),
            (5, "triangular_v1", 0.5),
            (7, "triangular_v1", 1.0),
            (9, "gaussian_v1", 0.5),
        ):
            with self.subTest(granularity=granularity, family=family):
                controller = make_controller(granularity, family, overlap)
                with tempfile.TemporaryDirectory() as name:
                    directory = Path(name)
                    manifest_path = write_fuzzy_diagnostics(
                        controller, directory, grid_points=5
                    )
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    self.assertEqual(
                        set(path.name for path in directory.iterdir()),
                        {*manifest["files"], "manifest.json"},
                    )
                    self.assertEqual(len(manifest["files"]), 4)
                    for filename, digest in manifest["files"].items():
                        content = (directory / filename).read_bytes()
                        self.assertEqual(hashlib.sha256(content).hexdigest(), digest)
                        if filename.endswith(".png"):
                            self.assertTrue(content.startswith(b"\x89PNG\r\n\x1a\n"))
                            image = imread(directory / filename)
                            self.assertEqual(image.ndim, 3)
                            self.assertGreater(float(np.std(image)), 0.01)
                    data = json.loads(
                        (directory / "diagnostics.json").read_text(encoding="utf-8")
                    )
                    self.assertEqual(data["controller"]["granularity"], granularity)
                    self.assertEqual(data["controller"]["membership_family"], family)
                    self.assertEqual(
                        data["controller"]["evaluation_mode"],
                        controller.evaluation_mode,
                    )
                    self.assertEqual(
                        data["response_axes"],
                        {"rows": "progress", "columns": "diversity"},
                    )
                    self.assertEqual(
                        data["diversity_coordinates"], [0.0, 0.25, 0.5, 0.75, 1.0]
                    )
                    np.testing.assert_array_equal(data["rules"], controller.rules)
                    for index, (axis, partition) in enumerate(
                        (
                            ("diversity", controller.diversity_partition),
                            ("progress", controller.progress_partition),
                            ("output", controller.output_partition),
                        )
                    ):
                        self.assertEqual(
                            data["controller"]["partitions"][axis],
                            [asdict(item) for item in partition],
                        )
                        for label, membership in enumerate(partition):
                            self.assertEqual(
                                data["membership_degrees"][index][label],
                                [membership.degree(value) for value in controller.grid],
                            )
                    for row, progress in enumerate(data["progress_coordinates"]):
                        for column, diversity in enumerate(
                            data["diversity_coordinates"]
                        ):
                            expected = controller.infer(diversity, progress)
                            self.assertEqual(
                                data["normalized_output"][row][column],
                                expected.normalized_output,
                            )
                            self.assertEqual(
                                data["boundary_events"][row][column],
                                expected.boundary_events,
                            )
                    if granularity == 3:
                        self.assertGreater(data["boundary_events"][0][1], 0)
                        degrees = data["membership_degrees"][0]
                        self.assertEqual(sum(row[125] for row in degrees), 0.0)

    def test_figures_use_data_axes_and_do_not_change_global_style(self) -> None:
        controller = make_controller()
        style_before = dict(rcParams)
        captured = {}
        original_savefig = Figure.savefig

        def capture(figure, path, **kwargs):
            captured[Path(path).name] = {
                "images": [
                    np.array(image.get_array(), copy=True)
                    for axis in figure.axes
                    for image in axis.images
                ],
                "lines": [
                    np.array(line.get_ydata(), copy=True)
                    for axis in figure.axes
                    for line in axis.lines
                ],
                "labels": [
                    (axis.get_xlabel(), axis.get_ylabel()) for axis in figure.axes
                ],
            }
            return original_savefig(figure, path, **kwargs)

        with tempfile.TemporaryDirectory() as name:
            with patch.object(Figure, "savefig", capture):
                write_fuzzy_diagnostics(controller, name, grid_points=5)
            data = json.loads((Path(name) / "diagnostics.json").read_text())
        self.assertEqual(dict(rcParams), style_before)
        np.testing.assert_array_equal(captured["rules.png"]["images"][0], data["rules"])
        np.testing.assert_array_equal(
            captured["response.png"]["images"][0], data["normalized_output"]
        )
        self.assertEqual(
            captured["rules.png"]["labels"][0],
            ("Progress label index", "Diversity label index"),
        )
        self.assertEqual(
            captured["response.png"]["labels"][0],
            ("Diversity (normalized)", "Progress (normalized)"),
        )
        lines = captured["memberships.png"]["lines"]
        for index, degrees in enumerate(data["membership_degrees"]):
            start = index * (controller.granularity + 1)
            np.testing.assert_array_equal(lines[start : start + 3], degrees)
            np.testing.assert_array_equal(
                lines[start + controller.granularity], np.sum(degrees, axis=0)
            )

    def test_invalid_grid_is_rejected_before_output(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name) / "not-created"
            for grid in (True, 3.5, "5", 0, 1, -3):
                with self.subTest(grid=grid):
                    with self.assertRaises((TypeError, ValueError)):
                        write_fuzzy_diagnostics(
                            make_controller(), directory, grid_points=grid
                        )
                    self.assertFalse(directory.exists())

    def test_inference_failure_propagates_without_success_artifacts(self) -> None:
        controller = make_controller()
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name) / "not-created"
            with patch.object(
                controller, "infer", side_effect=RuntimeError("no response")
            ):
                with self.assertRaisesRegex(RuntimeError, "no response"):
                    write_fuzzy_diagnostics(controller, directory, grid_points=2)
            self.assertFalse(directory.exists())

    def test_render_failure_preserves_previous_files_and_cleans_staging(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            previous = directory / "manifest.json"
            previous.write_text("previous manifest", encoding="utf-8")
            with patch.object(Figure, "savefig", side_effect=OSError("cannot render")):
                with self.assertRaisesRegex(AnalysisExportError, "cannot render"):
                    write_fuzzy_diagnostics(make_controller(), directory, grid_points=2)
            self.assertEqual(previous.read_text(), "previous manifest")
            self.assertEqual(list(directory.iterdir()), [previous])


if __name__ == "__main__":
    unittest.main()
