from __future__ import annotations

import time
from typing import Any

import structlog

try:
    from opentelemetry import metrics as otel_metrics

    _meter = otel_metrics.get_meter("specmetrics.tshirt")
    _classify_duration = _meter.create_histogram(
        name="tshirt.classification.duration",
        description="Duration of T-Shirt classification execution",
        unit="ms",
    )
    _item_gauge = _meter.create_gauge(
        name="tshirt.classified_items",
        description="Number of Functional Processes classified",
    )
    _distribution_histogram = _meter.create_histogram(
        name="tshirt.distribution",
        description="Distribution of T-Shirt sizes",
        unit="1",
    )
except Exception:
    _classify_duration = None
    _item_gauge = None
    _distribution_histogram = None

from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from .classifier import DEFAULT_MAPPING, TShirtClassifier
from .models import (
    ExecutionMetadata,
    MeasurementWarning,
    TShirtMeasurementResult,
)
logger = structlog.get_logger(__name__)


class TShirtHandler:
    @property
    def handled_event_type(self) -> EventType:
        return EventType.TSHIRT_CLASSIFICATION_COMPLETED

    @property
    def handler_id(self) -> str:
        return "tshirt_measurement"

    @property
    def stage_name(self) -> str:
        return "T-Shirt Sizing"

    def handle(self, event: PipelineEvent) -> PipelineContext:
        ctx = event.context
        start = time.monotonic()
        warnings: list[MeasurementWarning] = []

        measurement_result = ctx.measurement_result
        sp_items = self._extract_sp_items(measurement_result)
        source_run_id = self._extract_run_id(measurement_result)

        if sp_items is None:
            logger.debug(
                "tshirt_no_story_points",
                execution_id=str(ctx.execution_id),
            )
            result = TShirtMeasurementResult(
                run_id=str(ctx.execution_id),
                total_items=0,
                items=[],
                distribution={},
                execution_metadata=ExecutionMetadata(
                    duration_ms=0.0, total_fps_processed=0
                ),
                source_measurement_run_id=source_run_id or "",
                warnings=[
                    MeasurementWarning(
                        code="NO_STORY_POINTS",
                        message="No Story Points measurement result available. "
                        "T-Shirt Sizing requires a Story Points result.",
                    )
                ],
            )
            return self._finalize(ctx, result, start)

        mapping_override = self._resolve_mapping_override(ctx)
        mapping = mapping_override if mapping_override else DEFAULT_MAPPING

        classifier = TShirtClassifier(mapping=mapping)
        classified_items: list = []
        fps_processed = 0

        for item in sp_items:
            fps_processed += 1
            sp_value = self._get_sp_value(item)
            if sp_value is None:
                continue

            tshirt_size, rule = classifier.classify(sp_value)
            from .models import FunctionalWorkItem as TWItem, MeasurementEvidence

            classified_items.append(
                TWItem(
                    element_id=self._get_elem_id(item),
                    element_name=self._get_elem_name(item),
                    story_point_value=sp_value,
                    tshirt_size=tshirt_size,
                    mapping_rule=rule,
                    evidence_refs=[
                        MeasurementEvidence(
                            element_id=self._get_elem_id(item),
                            story_point_value=sp_value,
                            mapping_rule=rule,
                        )
                    ],
                )
            )

        dist: dict[str, int] = {}
        for ci in classified_items:
            dist[ci.tshirt_size] = dist.get(ci.tshirt_size, 0) + 1

        duration_ms = (time.monotonic() - start) * 1000

        result = TShirtMeasurementResult(
            run_id=str(ctx.execution_id),
            total_items=len(classified_items),
            items=classified_items,
            distribution=dist,
            execution_metadata=ExecutionMetadata(
                duration_ms=round(duration_ms, 2),
                total_fps_processed=fps_processed,
            ),
            source_measurement_run_id=source_run_id or "",
            warnings=warnings,
        )

        return self._finalize(ctx, result, start)

    def _finalize(
        self,
        ctx: PipelineContext,
        result: TShirtMeasurementResult,
        start: float,
    ) -> PipelineContext:
        duration_ms = (time.monotonic() - start) * 1000

        if _classify_duration is not None:
            _classify_duration.record(duration_ms)
        if _item_gauge is not None:
            _item_gauge.set(result.total_items)
        if _distribution_histogram is not None:
            for size, count in result.distribution.items():
                _distribution_histogram.record(count, {"tshirt_size": size})

        dist_str = {str(k): v for k, v in result.distribution.items()}

        payload: dict[str, Any] = {
            "method": result.method,
            "scale": result.scale,
            "total_items": result.total_items,
            "distribution": dist_str,
            "applied_rule_pack": result.applied_rule_pack,
            "source_measurement_run_id": result.source_measurement_run_id,
            "duration_ms": result.execution_metadata.duration_ms,
            "warnings": [w.model_dump() for w in result.warnings],
        }

        tshirt_event = PipelineEvent(
            event_type=EventType.TSHIRT_CLASSIFICATION_COMPLETED,
            publisher="tshirt",
            payload=payload,
            context=ctx,
        )

        logger.info(
            "tshirt_classification_completed",
            total_items=result.total_items,
            duration_ms=result.execution_metadata.duration_ms,
        )

        return ctx.with_stage_output(
            "measurement_result", payload, event=tshirt_event
        )

    def _extract_sp_items(self, measurement_result: Any) -> list | None:
        if measurement_result is None:
            return None
        if isinstance(measurement_result, dict):
            return measurement_result.get("items") or measurement_result.get("estimated_items")
        if hasattr(measurement_result, "items"):
            return measurement_result.items
        return None

    def _extract_run_id(self, measurement_result: Any) -> str | None:
        if measurement_result is None:
            return None
        if isinstance(measurement_result, dict):
            return measurement_result.get("run_id")
        if hasattr(measurement_result, "run_id"):
            return measurement_result.run_id
        return None

    def _get_sp_value(self, item: Any) -> int | None:
        if isinstance(item, dict):
            val = item.get("normalized_value") or item.get("story_point_value") or item.get("value")
            return int(val) if val is not None else None
        for attr in ("normalized_value", "story_point_value", "value"):
            val = getattr(item, attr, None)
            if val is not None:
                return int(val)
        return None

    def _get_elem_id(self, item: Any) -> str:
        if isinstance(item, dict):
            return str(item.get("element_id", ""))
        return str(getattr(item, "element_id", ""))

    def _get_elem_name(self, item: Any) -> str:
        if isinstance(item, dict):
            return str(item.get("element_name", ""))
        return str(getattr(item, "element_name", ""))

    def _resolve_mapping_override(self, ctx: PipelineContext) -> list | None:
        metadata = ctx.metadata
        if metadata is None:
            return None
        extra = metadata if isinstance(metadata, dict) else getattr(metadata, "extra", None) or {}
        raw = extra.get("tshirt_mapping") if isinstance(extra, dict) else None
        if raw is None:
            return None
        from .models import TShirtSize

        sizes: list[TShirtSize] = []
        for entry in raw:
            sizes.append(
                TShirtSize(
                    label=entry["label"],
                    story_point_range=tuple(entry["story_point_range"]),
                    ordinal=entry.get("ordinal", len(sizes) + 1),
                )
            )
        return sizes


class TShirtPlugin:
    def plugin_id(self) -> str:
        return "tshirt"

    def supported_methodology(self) -> str:
        return "T-Shirt Sizing"

    def supported_component_types(self) -> list[str]:
        return ["functional_process"]

    def measure(
        self,
        story_points_result: Any,
        mapping_override: list | None = None,
    ) -> TShirtMeasurementResult:
        from .classifier import classify_all
        from .models import ExecutionMetadata

        if story_points_result is None:
            return TShirtMeasurementResult(
                run_id="",
                total_items=0,
                items=[],
                distribution={},
                execution_metadata=ExecutionMetadata(),
                warnings=[
                    MeasurementWarning(
                        code="NO_STORY_POINTS",
                        message="No Story Points result available.",
                    )
                ],
            )

        items, warnings = classify_all(
            self._extract_items(story_points_result),
            mapping=mapping_override,
        )

        dist: dict[str, int] = {}
        for i in items:
            dist[i.tshirt_size] = dist.get(i.tshirt_size, 0) + 1

        return TShirtMeasurementResult(
            run_id="",
            total_items=len(items),
            items=items,
            distribution=dist,
            execution_metadata=ExecutionMetadata(
                total_fps_processed=len(items)
            ),
            warnings=warnings,
        )

    def _extract_items(self, result: Any) -> list:
        if isinstance(result, dict):
            return result.get("items") or result.get("estimated_items") or []
        if hasattr(result, "items"):
            return result.items
        return []


def create_tshirt_measurement_metadata() -> PluginMetadata:
    return PluginMetadata(
        id="tshirt",
        api_version="0.1.0",
        plugin_type=PluginType.MEASUREMENT,
        handled_event_types=(EventType.TSHIRT_CLASSIFICATION_COMPLETED,),
        handler_factory=lambda: TShirtHandler(),
        name="T-Shirt Sizing",
        description="T-Shirt Sizing — classifies Story Points into relative effort categories (XS–XXL) using a configurable lookup table",
        version="0.1.0",
    )
