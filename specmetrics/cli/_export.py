"""Auto-export helpers for the CLI measure command."""

from __future__ import annotations

import shutil
from pathlib import Path

from specmetrics.application.orchestrator import read_run_artifacts
from specmetrics.plugins.exporter.orchestrator import stage_to_csv, stage_to_xml


def _auto_export_json(runs_dir: Path, out_dir: Path) -> None:
    for src in runs_dir.glob("*.json"):
        if src.name in ("metadata.json", "metrics.json"):
            continue
        shutil.copy2(src, out_dir / src.name)


def _auto_export_csv(artifacts: dict, out_dir: Path) -> None:
    for fname, data in artifacts.items():
        if fname == "metadata":
            continue
        (out_dir / f"{fname}.csv").write_text(stage_to_csv(fname, data))


def _auto_export_xml(artifacts: dict, out_dir: Path) -> None:
    for fname, data in artifacts.items():
        if fname == "metadata":
            continue
        (out_dir / f"{fname}.xml").write_text(stage_to_xml(fname, data))


def run_auto_export(project_path: Path, measure_id: str, export_fmt: str) -> None:
    """Export the stored artifacts of a completed measure run."""
    runs_dir = project_path / ".specmetrics" / "runs" / measure_id
    if not runs_dir.exists():
        print(f"Measure run '{measure_id}' not found. Skipping auto-export.")
        return

    out_dir = project_path / ".specmetrics" / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)

    selected_formats = [f.strip() for f in export_fmt.split(",") if f.strip()]

    artifacts = read_run_artifacts(runs_dir)

    for fmt in selected_formats:
        if fmt == "json":
            _auto_export_json(runs_dir, out_dir)
        elif fmt == "csv":
            _auto_export_csv(artifacts, out_dir)
        elif fmt == "xml":
            _auto_export_xml(artifacts, out_dir)

    print(f"Auto-export complete \u2014 {out_dir}")


def run_export_requested(
    project_path: Path,
    measure_id: str,
    export_format: str | None,
) -> None:
    """Validate and run the requested auto-export, reporting invalid formats."""
    export_fmt = export_format or "json"
    invalid = [
        f
        for f in export_fmt.split(",")
        if f.strip() and f.strip() not in ("json", "csv", "xml")
    ]
    if invalid:
        print(
            f"Error: Invalid export format(s): {', '.join(invalid)}. Use json, csv, xml."
        )
    else:
        run_auto_export(project_path.resolve(), measure_id, export_fmt)

    return 0