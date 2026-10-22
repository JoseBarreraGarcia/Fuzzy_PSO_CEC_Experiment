"""Command-line entry point for previewing, planning and running campaigns."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Sequence

from afcs.metrics import load_metric_registry
from afcs.persistence import ExperimentRepository, initialize_v2_database

from .configuration import LoadedCampaignConfig, load_campaign_config
from .orchestration import SequentialCampaignOrchestrator


def campaign_preview(loaded: LoadedCampaignConfig) -> dict:
    """Return an auditable preview without writing a database."""

    return {
        "campaign_id": loaded.campaign.campaign_id,
        "name": loaded.campaign.name,
        "code_commit": loaded.campaign.code_commit,
        "summary": asdict(loaded.summary),
        "metrics": loaded.campaign.metric_selection,
        "randomness": dict(loaded.resolved_config["randomness"]),
        "problems": list(loaded.resolved_config["problems"]),
        "treatments": list(loaded.resolved_config["treatments"]),
        "execution": dict(loaded.resolved_config["execution"]),
        "trace": dict(loaded.resolved_config["trace"]),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    registry = load_metric_registry()

    if arguments.command == "preview":
        loaded = load_campaign_config(
            arguments.config,
            code_commit=arguments.code_commit,
            metric_registry=registry,
        )
        _print_json(campaign_preview(loaded))
        return 0

    connection = initialize_v2_database(arguments.database)
    try:
        repository = ExperimentRepository(connection, registry)
        orchestrator = SequentialCampaignOrchestrator(repository)
        if arguments.command == "plan":
            loaded = load_campaign_config(
                arguments.config,
                code_commit=arguments.code_commit,
                metric_registry=registry,
            )
            plan = orchestrator.plan(loaded)
            _print_json(
                {
                    "campaign_id": plan.campaign_id,
                    "configurations": len(plan.configuration_ids),
                    "problem_instances": len(plan.instance_ids),
                    "planned_runs": len(plan.run_ids),
                    "database": str(Path(arguments.database).resolve()),
                }
            )
        else:
            _print_json(asdict(orchestrator.execute_pending(arguments.campaign_id)))
    finally:
        connection.close()
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="afcs-campaign",
        description="Validate, inspect and execute AFCS v2 campaigns.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    preview = commands.add_parser("preview", help="validate without writing SQLite")
    _config_arguments(preview)
    plan = commands.add_parser("plan", help="persist the expanded plan in SQLite")
    _config_arguments(plan)
    plan.add_argument("--database", required=True, type=Path)
    run = commands.add_parser("run", help="execute only pending runs sequentially")
    run.add_argument("--database", required=True, type=Path)
    run.add_argument("--campaign-id", required=True)
    return parser


def _config_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument(
        "--code-commit",
        required=True,
        help="exact Git commit associated with the campaign",
    )


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
