from __future__ import annotations

import logging
from pathlib import Path

import structlog

from specmetrics.application.config import AppConfig
from specmetrics.application.enums import OutputFormat, StageName
from specmetrics.application.measure_id import generate_measure_id
from specmetrics.application.models import PipelineRequest
from specmetrics.application.orchestrator import PipelineOrchestrator, save_run_artifacts
from specmetrics.infrastructure.config.loader import ConfigurationSystem

from .formatters import format_json_result, format_text_result

logger = structlog.get_logger(__name__)

_config_system: ConfigurationSystem | None = None

VALID_METRICS = {"all", "bcp", "fpa", "sfp", "snap", "sp", "tshirt", "tp", "cp"}


def _setup_log_file(project_path: Path, filename: str) -> str | None:
    import re
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


def _run_auto_export(project_path: Path, measure_id: str, export_fmt: str) -> None:

    runs_dir = project_path / ".specmetrics" / "runs" / measure_id
    if not runs_dir.exists():
        print(f"Measure run '{measure_id}' not found. Skipping auto-export.")
        return

    out_dir = project_path / ".specmetrics" / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)

    selected_formats = [f.strip() for f in export_fmt.split(",") if f.strip()]

    from specmetrics.application.orchestrator import read_run_artifacts
    from specmetrics.plugins.exporter.orchestrator import stage_to_csv, stage_to_xml
    import shutil

    artifacts = read_run_artifacts(runs_dir)

    for fmt in selected_formats:
        if fmt == "json":
            for src in runs_dir.glob("*.json"):
                if src.name == "metadata.json":
                    continue
                dst = out_dir / src.name
                shutil.copy2(src, dst)
        elif fmt == "csv":
            for fname, data in artifacts.items():
                if fname == "metadata":
                    continue
                csv_content = stage_to_csv(fname, data)
                (out_dir / f"{fname}.csv").write_text(csv_content)
        elif fmt == "xml":
            for fname, data in artifacts.items():
                if fname == "metadata":
                    continue
                xml_content = stage_to_xml(fname, data)
                (out_dir / f"{fname}.xml").write_text(xml_content)

    print(f"Auto-export complete — {out_dir}")


def get_config_system() -> ConfigurationSystem:
    global _config_system
    if _config_system is None:
        _config_system = ConfigurationSystem()
    return _config_system


def _parse_metrics(metrics_str: str | None) -> list[str] | None:
    if metrics_str is None:
        return None

    parts = [m.strip() for m in metrics_str.split(",")]
    parts = [m for m in parts if m]

    if not parts:
        return None

    invalid = [m for m in parts if m not in VALID_METRICS]
    if invalid:
        print(
            f"Error: Unknown metric identifier(s): {', '.join(invalid)}\n"
            f"Valid identifiers: {', '.join(sorted(VALID_METRICS))}"
        )
        return None

    if "all" in parts:
        return None

    seen: set[str] = set()
    deduped: list[str] = []
    for m in parts:
        if m not in seen:
            seen.add(m)
            deduped.append(m)
    return deduped


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
) -> int:
    config = AppConfig.load(project_path)

    metrics_filter = _parse_metrics(metrics)
    if metrics_filter is None and metrics is not None:
        return 1

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

    if log_file:
        _setup_log_file(Path(project_path).resolve(), log_file)
    else:
        if quiet:
            logging.getLogger().setLevel(logging.ERROR)
        elif verbose:
            logging.getLogger().setLevel(logging.INFO)

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

    if quiet:
        if result.status.value == "failed":
            print(result.error)
        return 0 if result.status.value == "success" else 1

    if output_format == OutputFormat.JSON:
        print(format_json_result(result))
    else:
        print(format_text_result(result, verbose=verbose))

    if export_run:
        export_fmt = export_format or "json"
        invalid = [f for f in export_fmt.split(",") if f.strip() and f.strip() not in ("json", "csv", "xml")]
        if invalid:
            print(f"Error: Invalid export format(s): {', '.join(invalid)}. Use json, csv, xml.")
        else:
            _run_auto_export(project_path.resolve(), measure_id, export_fmt)

    if result.status.value == "failed":
        return 1

    return 0
