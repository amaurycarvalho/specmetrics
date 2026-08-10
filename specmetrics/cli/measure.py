"""Core measure pipeline logic shared by the CLI entrypoint."""

from __future__ import annotations

from pathlib import Path

import structlog

from specmetrics.application.config import AppConfig
from specmetrics.application.enums import OutputFormat
from specmetrics.application.measure_id import generate_measure_id
from specmetrics.application.metrics_json import save_metrics_json
from specmetrics.application.models import PipelineRequest, PipelineResult
from specmetrics.application.orchestrator import (
    PipelineOrchestrator,
    save_run_artifacts,
)

from ._export import run_export_requested
from ._pipeline import (
    configure_logging,
    get_config_system,
    resolve_config_system,
    resolve_output,
    resolve_stages,
)
from .formatters import format_json_result, format_text_result

logger = structlog.get_logger(__name__)

__all__ = [
    "_parse_metrics",
    "get_config_system",
    "run_measure",
]

VALID_METRICS = {"all", "bcp", "fpa", "sfp", "snap", "sp", "tshirt", "tp", "cp"}


def _parse_metrics(metrics_str: str | None) -> list[str] | None:
    """Parse the comma-separated metrics filter into a validated list."""
    if metrics_str is None:
        return None

    parts = [m.strip() for m in metrics_str.split(",") if m.strip()]

    if not parts:
        return None

    if invalid := [m for m in parts if m not in VALID_METRICS]:
        print(
            f"Error: Unknown metric identifier(s): {', '.join(invalid)}\n"
            f"Valid identifiers: {', '.join(sorted(VALID_METRICS))}"
        )
        return None

    if "all" in parts:
        return None

    return list(dict.fromkeys(parts))


def run_measure(
    project_path: Path,
    metrics: str | None = None,
    output: str | None = None,
    stage: str | None = None,
    from_stage: str | None = None,
    export_run: bool = False,
    export_format: str | None = None,
    verbose: bool = False,
    quiet: bool = False,
    log_file: str | None = None,
    config_path: Path | None = None,
    llm_rpm_limit: int = 15,
) -> int:
    """Run the measurement pipeline and return the process exit code."""
    config = AppConfig.load(project_path)

    metrics_filter = _parse_metrics(metrics)
    if metrics_filter is None and metrics is not None:
        return 1

    output_format, output_path = resolve_output(output)

    cfg_system = resolve_config_system(project_path, config_path)

    verbose = verbose or config.verbose
    configure_logging(log_file, project_path, verbose, quiet)

    parsed_stages, parsed_from_stage = resolve_stages(stage, from_stage)

    measure_id = generate_measure_id()

    request = PipelineRequest(
        project_path=project_path.resolve(),
        stages=parsed_stages,
        from_stage=parsed_from_stage,
        metrics_filter=metrics_filter,
        output_format=output_format,
        output_path=output_path,
        verbose=verbose,
        quiet=quiet,
        measure_id=measure_id,
        llm_rpm_limit=llm_rpm_limit,
    )

    orchestrator = PipelineOrchestrator()
    if cfg_system is not None:
        orchestrator.set_config_system(cfg_system)
    result = orchestrator.execute(request)

    print(f"Measure ID: {measure_id}")

    save_run_artifacts(
        project_path.resolve(),
        measure_id,
        result,
        max_entities_per_stage=getattr(result, "_max_entities_per_stage", 5000),
    )

    save_metrics_json(
        project_path.resolve(),
        measure_id,
        result,
        metrics_filter=metrics_filter,
    )

    if quiet:
        if result.status.value == "failed":
            print(result.error)
        return 0 if result.status.value == "success" else 1

    _print_result(result, output_format, verbose)

    if export_run:
        run_export_requested(project_path, measure_id, export_format)

    return 1 if result.status.value == "failed" else 0


def _print_result(
    result: PipelineResult,
    output_format: OutputFormat,
    verbose: bool,
) -> None:
    if output_format == OutputFormat.JSON:
        print(format_json_result(result))
    else:
        print(format_text_result(result, verbose=verbose))