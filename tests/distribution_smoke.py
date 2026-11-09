"""Run with python -I outside the checkout against a non-editable installation."""

import argparse
import json
import math
import os
import pkgutil
import subprocess
import sys
import tempfile
from contextlib import closing
from dataclasses import asdict
from importlib import import_module, metadata
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extras", action="store_true")
    parser.add_argument("--workers", type=int, choices=(1, 2), default=1)
    parser.add_argument("--config", type=Path, required=True)
    arguments = parser.parse_args()
    if not sys.flags.isolated or sys.flags.optimize or os.environ.get("PYTHONPATH"):
        parser.error("Use python -I without -O and with PYTHONPATH unset")

    import afcs
    from afcs.analysis import (
        AnalysisError,
        AnalysisExportError,
        export_campaign_csv,
        friedman_objective_test,
        run_campaign_analysis,
        write_fuzzy_diagnostics,
    )
    from afcs.core import ReplicaRandomStreams
    from afcs.experiments import load_campaign_config
    from afcs.fuzzy import MamdaniController
    from afcs.metrics import load_metric_registry
    from afcs.persistence import (
        audit_campaign_integrity,
        current_schema_version,
        initialize_v2_database,
    )
    from afcs.problems import ProblemFactory

    distribution = metadata.distribution("afcs")
    installed_root = Path(distribution.locate_file("afcs")).resolve()
    assert installed_root.is_relative_to(Path(sys.prefix).resolve()), installed_root
    direct_url = json.loads(distribution.read_text("direct_url.json") or "{}")
    assert not direct_url.get("dir_info", {}).get("editable"), direct_url
    assert not Path.cwd().is_relative_to(Path(__file__).resolve().parents[1])
    modules = [afcs]
    for module in pkgutil.walk_packages(afcs.__path__, "afcs."):
        modules.append(import_module(module.name))
    for module in modules:
        assert Path(module.__file__).resolve().is_relative_to(installed_root), module

    installed = {
        item.metadata["Name"].lower(): item.version for item in metadata.distributions()
    }
    if not arguments.extras:
        assert {"pip", "afcs", "numpy"} <= set(installed), installed
        assert set(installed) <= {"pip", "afcs", "numpy", "setuptools"}, installed
        for family in ("OPFUNU_CEC",):
            try:
                ProblemFactory().build(
                    family=family,
                    dimension=10,
                    parameters={"suite_year": 2014, "function_number": 1},
                    random_streams=ReplicaRandomStreams(42),
                )
            except RuntimeError as error:
                assert "optional dependency 'opfunu'" in str(error), error
            else:
                raise AssertionError("Missing OPFUNU must fail explicitly")
        try:
            friedman_objective_test([])
        except AnalysisError as error:
            assert "install the 'analysis' extra" in str(error), error
        else:
            raise AssertionError("Missing SciPy must fail explicitly")

    for family, parameters in (
        ("CEC2017", {"function_number": 1}),
        ("CLASSICAL", {"function_number": 1}),
        *(
            (("OPFUNU_CEC", {"suite_year": 2014, "function_number": 1}),)
            if arguments.extras
            else ()
        ),
    ):
        problem = ProblemFactory().build(
            family=family,
            dimension=10,
            parameters=parameters,
            random_streams=ReplicaRandomStreams(42),
        )
        assert math.isfinite(problem.evaluate([0.0] * 10).objective)
    assert load_metric_registry().resolve("minimal")

    config = load_campaign_config(arguments.config, code_commit="distribution-smoke")
    assert config.summary.total_runs == 3, config.summary
    assert all(
        treatment["parameters"]["population_size"] == 4
        and treatment["parameters"]["max_iterations"] == 2
        for treatment in config.resolved_config["treatments"]
    ), "Only the bounded technical fixture is allowed"
    cli = Path(sys.executable).with_name(
        "afcs-campaign.exe" if os.name == "nt" else "afcs-campaign"
    )

    def command(*args: str) -> dict:
        completed = subprocess.run(
            [str(cli), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)

    subprocess.run([str(cli), "--help"], check=True, capture_output=True)
    with tempfile.TemporaryDirectory(prefix="afcs-distribution-") as directory:
        root = Path(directory)
        raw = json.loads(arguments.config.read_text(encoding="utf-8"))
        raw["problems"] = [
            {"family": "CLASSICAL", "functions": [1, 2], "dimensions": [2]}
        ]
        raw["execution"]["parallel_workers"] = arguments.workers
        fixture = root / "technical.json"
        fixture.write_text(json.dumps(raw, allow_nan=False), encoding="utf-8")
        config = load_campaign_config(fixture, code_commit="distribution-smoke")
        assert config.summary.total_runs == 6 and config.summary.total_evaluations == 72
        preview = command(
            "preview",
            "--config",
            str(fixture),
            "--code-commit",
            "distribution-smoke",
        )
        assert preview["summary"] == asdict(config.summary)
        assert not list(root.glob("*.db")), "Preview must not create a database"
        database = root / "smoke.db"
        plan = command(
            "plan",
            "--config",
            str(fixture),
            "--database",
            str(database),
            "--code-commit",
            "distribution-smoke",
        )
        assert plan["planned_runs"] == 6, plan
        campaign_id = config.campaign.campaign_id
        execution = command(
            "run",
            "--database",
            str(database),
            "--campaign-id",
            campaign_id,
        )
        assert execution["completed"] == 6 and execution["failed"] == 0, execution
        audit = command(
            "audit",
            "--database",
            str(database),
            "--campaign-id",
            campaign_id,
        )
        assert audit["is_valid"], audit
        command("seal", "--database", str(database), "--campaign-id", campaign_id)
        with closing(initialize_v2_database(database)) as connection:
            assert current_schema_version(connection) == 7
            assert audit_campaign_integrity(connection, campaign_id).is_valid
            if arguments.extras:
                result = run_campaign_analysis(
                    connection, campaign_id, root / "analysis"
                )
                assert result.run_row_count == 6, result
            else:
                runs, traces = root / "runs.csv", root / "traces.csv"
                export_campaign_csv(connection, campaign_id, runs, traces)
                try:
                    write_fuzzy_diagnostics(
                        MamdaniController(
                            granularity=3,
                            rule_base="R1",
                            membership_family="triangular_v1",
                            diversity_overlap=0.5,
                            progress_overlap=0.5,
                            output_overlap=0.5,
                        ),
                        root / "figures",
                        grid_points=2,
                    )
                except AnalysisExportError as error:
                    assert "install the 'analysis' extra" in str(error), error
                else:
                    raise AssertionError("Missing Matplotlib must fail explicitly")

    print(
        json.dumps(
            {
                "mode": "extras" if arguments.extras else "core",
                "python": sys.version,
                "executable": sys.executable,
                "installed_root": str(installed_root),
                "module_count": len(modules),
                "packages": installed,
                "technical_runs": 6,
                "parallel_workers": arguments.workers,
                "schema_version": 7,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
