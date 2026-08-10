"""Persistence of per-run artifacts under the project's ``.specmetrics/runs`` folder.

Moved verbatim from ``specmetrics.application.orchestrator`` as part of the
orchestrator maintainability refactor (FR-003). Only depends on ``truncation``
and the application result models.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import structlog

from specmetrics.application.models import PipelineResult

from .truncation import _truncate_entities

logger = structlog.get_logger(__name__)


def _serialize_stage_data(
    result: PipelineResult,
    max_entities_per_stage: int = 5000,
) -> dict[str, list[dict]]:
    stages: dict[str, list[dict]] = {}
    csm_cfm_stages = {"csm", "cfm"}
    for sd in result.stage_details:
        entry: dict = {
            "name": sd.name,
            "count": sd.count,
            "count_type": sd.count_type,
            "duration_ms": sd.duration_ms,
        }
        raw_entities = result.stage_entities.get(sd.name, [])
        if raw_entities:
            per_category = sd.name in csm_cfm_stages
            entry["entities"] = _truncate_entities(
                raw_entities, max_entities_per_stage, per_category=per_category
            )
        else:
            entry["entities"] = []
        stages[sd.name] = [entry]
    return stages


def save_run_artifacts(
    project_path: Path,
    measure_id: str,
    result: PipelineResult,
    max_entities_per_stage: int = 5000,
) -> Path:
    """Persist metadata and per-stage artifacts for a run under the run folder."""
    runs_dir = project_path / ".specmetrics" / "runs" / measure_id
    runs_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "id": measure_id,
        "created_at": datetime.now(UTC).isoformat(),
        "sdd_framework": (
            result._framework_detected
            if getattr(result, "_framework_detected", None)
            and isinstance(result._framework_detected, str)
            else "unknown"
        ),
        "llm": (
            {"provider": result.llm_provider, "model": result.llm_model}
            if result.llm_provider and result.llm_provider != "none"
            else {"provider": "none"}
        ),
        "project_path": str(result.project_path or project_path),
    }
    (runs_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    stages = _serialize_stage_data(
        result, max_entities_per_stage=max_entities_per_stage
    )
    for stage_name, entries in stages.items():
        (runs_dir / f"{stage_name}.json").write_text(json.dumps(entries, indent=2))

    logger.info("run_artifacts_saved", path=str(runs_dir), stages=list(stages.keys()))
    return runs_dir


def read_run_artifacts(run_dir: Path) -> dict:
    """Read all saved run artifacts from a run directory into a mapping."""
    artifacts: dict = {}
    metadata_file = run_dir / "metadata.json"
    if metadata_file.exists():
        artifacts["metadata"] = json.loads(metadata_file.read_text())
    for stage_file in sorted(run_dir.glob("*.json")):
        if stage_file.name in ("metadata.json", "metrics.json"):
            continue
        artifacts[stage_file.stem] = json.loads(stage_file.read_text())
    return artifacts