from __future__ import annotations

from pathlib import Path

import structlog

from specmetrics.application.config import AppConfig
from specmetrics.application.enums import OutputFormat, StageName
from specmetrics.application.models import PipelineRequest
from specmetrics.application.orchestrator import PipelineOrchestrator
from specmetrics.infrastructure.config.loader import ConfigurationSystem

from .formatters import format_json_result, format_text_result

logger = structlog.get_logger(__name__)

_config_system: ConfigurationSystem | None = None


def get_config_system() -> ConfigurationSystem:
    global _config_system
    if _config_system is None:
        _config_system = ConfigurationSystem()
    return _config_system


def run_measure(
    project_path: Path,
    output: str | None = None,
    stage: str | None = None,
    from_stage: str | None = None,
    verbose: bool = False,
    quiet: bool = False,
    config_path: Path | None = None,
) -> int:
    config = AppConfig.load(project_path)

    output_format = OutputFormat.TEXT
    output_path: Path | None = None

    cfg_system = get_config_system()
    if config_path is not None:
        cfg_system = ConfigurationSystem(project_root=project_path, config_path=config_path)
        cfg_system.load()

    if output:
        if ":" in output:
            fmt, path_str = output.split(":", 1)
            output_format = OutputFormat(fmt)
            output_path = Path(path_str)
        else:
            output_format = OutputFormat(output)

    parsed_stages: list[StageName] | None = None
    parsed_from_stage: StageName | None = None

    if stage:
        parsed_stages = [StageName(stage)]

    if from_stage:
        parsed_from_stage = StageName(from_stage)

    if not verbose and config.verbose:
        verbose = True

    request = PipelineRequest(
        project_path=project_path.resolve(),
        stages=parsed_stages,
        from_stage=parsed_from_stage,
        output_format=output_format,
        output_path=output_path,
        verbose=verbose,
        quiet=quiet,
    )

    orchestrator = PipelineOrchestrator()
    result = orchestrator.execute(request)

    if quiet:
        if result.status.value == "failed":
            print(result.error)
        return 0 if result.status.value == "success" else 1

    if output_format == OutputFormat.JSON:
        print(format_json_result(result))
    else:
        print(format_text_result(result, verbose=verbose))

    if result.status.value == "failed":
        return 1

    return 0
