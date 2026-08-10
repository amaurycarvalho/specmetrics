"""Serialization of measurement results into the ``metrics.json`` artifact."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Self

from ._entity_builders import _BUILDERS, EntityScoreBuilder
from ._metadata import build_metric_metadata as _build_metric_metadata
from .models import (
    EntityScore,
    MetricBreakdownEntry,
    PipelineResult,
)

METRIC_UNIT_MAP: dict[str, str] = {
    "fpa": "ufp",
    "sfp": "sfp",
    "snap": "snap",
    "bcp": "bcp",
    "sp": "story_points",
    "tp": "tokens",
    "cp": "cognitive_points",
    "tshirt": "entities",
}

METRIC_JSON_NAME_MAP: dict[str, str] = {
    "bcp": "business_complexity_points",
    "fpa": "function_points",
    "sfp": "simplified_function_points",
    "snap": "snap",
    "sp": "story_points",
    "tshirt": "tshirt",
    "tp": "token_points",
    "cp": "cognitive_points",
}

WARNING_KEY_MAP: dict[str, str] = {
    "bcp": "bcp_warnings",
    "sp": "storypoints_warnings",
    "tp": "token_warnings",
    "cp": "cognitive_warnings",
}

ENTITY_KEY_MAP: dict[str, str] = {
    "fpa": "fpa_entities",
    "sfp": "sfp_entities",
    "snap": "snap_entities",
    "bcp": "bcp_entities",
    "sp": "storypoints_entities",
    "tp": "token_entities",
    "cp": "cognitive_entities",
    "tshirt": "tshirt_entities",
}


def _compute_total(cli_id: str, entities: list[EntityScore]) -> float:
    if cli_id == "tshirt":
        return float(len(entities))
    total = sum(e.score for e in entities)
    if cli_id in ("tp", "cp"):
        return round(total, 1)
    return total


def _failure_entry(
    cli_id: str,
    json_name: str,
    unit: str,
    errors: list[str],
    metric_warnings: list[str],
    metric_metadata: dict[str, Any] | None,
) -> MetricBreakdownEntry:
    return MetricBreakdownEntry(
        name=cli_id,
        metric=json_name,
        total=0.0,
        unit=unit,
        entity_count=0,
        entities=[],
        status="failed",
        errors=errors,
        warnings=metric_warnings if metric_warnings else None,
        metadata=metric_metadata,
    )


class MetricBreakdownBuilder:
    """Build ``MetricBreakdownEntry`` objects from a raw measurement result."""

    def __init__(self: Self, measurement_result_raw: dict[str, Any]) -> None:
        """Initialize the builder with the raw measurement result."""
        self._raw = measurement_result_raw

    def build_all(
        self: Self, metrics_filter: list[str] | None = None
    ) -> list[MetricBreakdownEntry]:
        """Build breakdown entries for every requested metric identifier."""
        entries: list[MetricBreakdownEntry] = []
        metric_ids = metrics_filter or list(ENTITY_KEY_MAP.keys())

        for cli_id in metric_ids:
            if cli_id not in ENTITY_KEY_MAP:
                continue
            entry = self._build_entry(cli_id)
            if entry is not None:
                entries.append(entry)

        return entries

    def _build_entry(self: Self, cli_id: str) -> MetricBreakdownEntry | None:
        """Build a single breakdown entry for the given metric identifier."""
        entity_key = ENTITY_KEY_MAP[cli_id]
        raw_entities: list[dict[str, Any]] = self._raw.get(entity_key, [])

        builder_fn = _BUILDERS.get(cli_id)
        if builder_fn is None:
            return None

        entities, errors = self._build_entities(builder_fn, raw_entities)
        total = _compute_total(cli_id, entities)
        unit = METRIC_UNIT_MAP.get(cli_id, "")
        json_name = METRIC_JSON_NAME_MAP.get(cli_id, cli_id)
        metric_metadata = _build_metric_metadata(cli_id, self._raw)
        metric_warnings = self._collect_warnings(WARNING_KEY_MAP.get(cli_id))

        if errors:
            return _failure_entry(
                cli_id, json_name, unit, errors, metric_warnings, metric_metadata
            )

        return MetricBreakdownEntry(
            name=cli_id,
            metric=json_name,
            total=total,
            unit=unit,
            entity_count=len(entities),
            entities=entities,
            status="success",
            warnings=metric_warnings if metric_warnings else None,
            metadata=metric_metadata,
        )

    def _build_entities(
        self: Self, builder_fn: Callable[[dict[str, Any]], EntityScore], raw_entities: object
    ) -> tuple[list[EntityScore], list[str]]:
        entities: list[EntityScore] = []
        errors: list[str] = []
        if not isinstance(raw_entities, list):
            return entities, errors
        for raw_entity in raw_entities:
            try:
                entity = builder_fn(raw_entity)
                entities.append(entity)
            except (ValueError, TypeError, KeyError) as exc:
                errors.append(f"Failed to build entity: {exc}")
        return entities, errors

    def _collect_warnings(self: Self, warning_key: str | None) -> list[str]:
        metric_warnings: list[str] = []
        if warning_key is None:
            return metric_warnings
        raw_warnings = self._raw.get(warning_key, [])
        if not isinstance(raw_warnings, list):
            return metric_warnings
        for w in raw_warnings:
            if isinstance(w, dict):
                metric_warnings.append(str(w.get("message", str(w))))
            elif isinstance(w, str):
                metric_warnings.append(w)
        return metric_warnings


def save_metrics_json(
    project_path: Path,
    measure_id: str,
    result: PipelineResult,
    metrics_filter: list[str] | None = None,
) -> Path | None:
    """Persist the measurement breakdown to ``metrics.json`` under the run folder."""
    measurement_result_raw: dict[str, Any] = getattr(
        result, "measurement_result_raw", {}
    )
    if not measurement_result_raw:
        runs_dir = project_path / ".specmetrics" / "runs" / measure_id
        runs_dir.mkdir(parents=True, exist_ok=True)
        failed_entry = MetricBreakdownEntry(
            name="error",
            metric="error",
            total=0.0,
            unit="",
            entity_count=0,
            entities=[],
            status="failed",
            errors=["measurement_result_raw is missing or empty"],
        )
        metrics_path = runs_dir / "metrics.json"
        metrics_path.write_text(
            json.dumps([failed_entry.model_dump(mode="json")], indent=2),
            encoding="utf-8",
        )
        return metrics_path

    builder = MetricBreakdownBuilder(measurement_result_raw)
    entries = builder.build_all(metrics_filter=metrics_filter)

    runs_dir = project_path / ".specmetrics" / "runs" / measure_id
    runs_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = runs_dir / "metrics.json"
    metrics_path.write_text(
        json.dumps(
            [e.model_dump(mode="json", exclude_none=True) for e in entries],
            indent=2,
        ),
        encoding="utf-8",
    )
    return metrics_path


__all__ = [
    "EntityScoreBuilder",
    "MetricBreakdownBuilder",
    "save_metrics_json",
]