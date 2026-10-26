"""Command-line entry point for previewing, planning and running campaigns."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Sequence

from afcs.metrics import load_metric_registry
from afcs.persistence import (
    ExperimentRepository,
    audit_campaign_integrity,
    initialize_v2_database,
)

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
        elif arguments.command == "run":
            _print_json(asdict(orchestrator.execute_pending(arguments.campaign_id)))
        elif arguments.command == "recover":
            _print_json(
                asdict(
                    orchestrator.recover_interrupted(
                        arguments.campaign_id,
                        tuple(arguments.run_id),
                        arguments.reason,
                    )
                )
            )
        elif arguments.command == "cancel":
            _print_json(
                asdict(
                    orchestrator.cancel_runs(
                        arguments.campaign_id,
                        tuple(arguments.run_id),
                        arguments.reason,
                    )
                )
            )
        elif arguments.command == "seal":
            repository.seal_campaign(
                arguments.campaign_id, waiver_reason=arguments.waiver_reason
            )
            _print_json(
                {
                    "campaign_id": arguments.campaign_id,
                    "campaign_status": repository.campaign_status(arguments.campaign_id),
                }
            )
        elif arguments.command == "audit":
            report = audit_campaign_integrity(connection, arguments.campaign_id)
            payload = asdict(report)
            payload["is_valid"] = report.is_valid
            _print_json(payload)
            if not report.is_valid:
                return 2
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
    recover = commands.add_parser(
        "recover",
        help="explicitly abandon interrupted attempts and requeue their runs",
    )
    recover.add_argument("--database", required=True, type=Path)
    recover.add_argument("--campaign-id", required=True)
    recover.add_argument("--run-id", required=True, type=int, nargs="+")
    recover.add_argument("--reason", required=True)
    cancel = commands.add_parser(
        "cancel", help="intentionally exclude planned or running runs"
    )
    cancel.add_argument("--database", required=True, type=Path)
    cancel.add_argument("--campaign-id", required=True)
    cancel.add_argument("--run-id", required=True, type=int, nargs="+")
    cancel.add_argument("--reason", required=True)
    seal = commands.add_parser(
        "seal", help="seal a completed campaign for scientific use"
    )
    seal.add_argument("--database", required=True, type=Path)
    seal.add_argument("--campaign-id", required=True)
    seal.add_argument(
        "--waiver-reason",
        help="required justification when failed or cancelled runs exist",
    )
    audit = commands.add_parser(
        "audit", help="validate persisted campaign integrity without changing it"
    )
    audit.add_argument("--database", required=True, type=Path)
    audit.add_argument("--campaign-id", required=True)
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
