"""Pipeline setup helpers for the CLI measure command."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from specmetrics.application.enums import OutputFormat, StageName
from specmetrics.infrastructure.config.loader import ConfigurationSystem

_config_system: ConfigurationSystem | None = None


def _setup_log_file(project_path: Path, filename: str) -> str | None:
    logs_dir = project_path / ".specmetrics" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    path = str(logs_dir / filename)
    root = logging.getLogger()
    for h in root.handlers[:]:
        if isinstance(h, logging.StreamHandler):
            h.setLevel(logging.WARNING)
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    fh = logging.FileHandler(path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    plain = logging.Formatter("%(message)s")
    fh.setFormatter(plain)
    fh.addFilter(lambda rec: setattr(rec, "msg", ansi_escape.sub("", rec.msg)) or True)
    root.addHandler(fh)
    root.setLevel(logging.DEBUG)
    return path


def get_config_system() -> ConfigurationSystem:
    """Return the shared configuration system, creating it on first use."""
    global _config_system
    if _config_system is None:
        _config_system = ConfigurationSystem()
    return _config_system


def resolve_output(
    output: str | None,
) -> tuple[OutputFormat, Path | None]:
    """Resolve the CLI output argument into a format and optional path."""
    if not output:
        return OutputFormat.TEXT, None
    if ":" in output:
        fmt, path_str = output.split(":", 1)
        return OutputFormat(fmt), Path(path_str)
    return OutputFormat(output), None


def resolve_config_system(
    project_path: Path, config_path: Path | None
) -> ConfigurationSystem | None:
    """Resolve the configuration system, honoring an explicit config path."""
    if config_path is None:
        return get_config_system()
    cfg_system = ConfigurationSystem(
        project_root=project_path, config_path=config_path
    )
    cfg_system.load()
    return cfg_system


def configure_logging(
    log_file: str | None,
    project_path: Path,
    verbose: bool,
    quiet: bool,
) -> None:
    """Configure root logging based on the CLI flags."""
    if log_file:
        _setup_log_file(Path(project_path).resolve(), log_file)
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)


def resolve_stages(
    stage: str | None,
    from_stage: str | None,
) -> tuple[list[StageName] | None, StageName | None]:
    """Resolve the stage/from-stage CLI arguments into StageName values."""
    parsed_stages = [StageName(stage)] if stage else None
    parsed_from_stage = StageName(from_stage) if from_stage else None
    return parsed_stages, parsed_from_stage