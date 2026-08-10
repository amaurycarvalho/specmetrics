"""T-Shirt Sizing measurement plugin."""

from __future__ import annotations

import time
from typing import Any, Self

import structlog

from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from ._extractors import _ItemExtractionMixin
from ._telemetry import _classify_duration, _distribution_histogram, _item_gauge
from .classifier import DEFAULT_MAPPING, TShirtClassifier
from .models import (
    ExecutionMetadata,
    MeasurementWarning,
    TShirtMeasurementResult,
)

logger = structlog.get_logger(__name__)


class TShirtHandler(_ItemExtractionMixin):
    """Pipeline handler that classifies Story Points into T-Shirt sizes."""

    @property
    def handled_event_type(self: Self) -> EventType:
        """Return the event type this handler processes."""
        return EventType.TSHIRT_CLASSIFICATION_COMPLETED

    @property
    def handler_id(self: Self) -> str:
        """Return the unique identifier of this handler."""
        return "tshirt_measurement"

    @property
    def stage_name(self: Self) -> str:
        """Return the display name of this handler stage."""
        return "T-Shirt Sizing"

    def handle(self: Self, event: PipelineEvent) -> PipelineContext:
        """Classify Story Points into T-Shirt sizes for the given pipeline event."""
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
            from .models import FunctionalWorkItem as TWItem
            from .models import MeasurementEvidence

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
        self: Self,
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

        tshirt_entities = [item.model_dump(mode="json") for item in result.items]

        payload: dict[str, Any] = {
            "method": result.method,
            "scale": result.scale,
            "tshirt": result.total_items,
            "tshirt_breakdown": {k: {"count": v} for k, v in result.distribution.items()},
            "total_items": result.total_items,
            "distribution": dist_str,
            "applied_rule_pack": result.applied_rule_pack,
            "source_measurement_run_id": result.source_measurement_run_id,
            "duration_ms": result.execution_metadata.duration_ms,
            "warnings": [w.model_dump() for w in result.warnings],
            "tshirt_entities": tshirt_entities,
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

        return ctx.merge_stage_output("measurement_result", payload, event=tshirt_event)


class TShirtPlugin:
    """Plugin facade exposing the T-Shirt sizing methodology."""

    def plugin_id(self: Self) -> str:
        """Return the unique plugin identifier."""
        return "tshirt"

    def supported_methodology(self: Self) -> str:
        """Return the methodology name supported by this plugin."""
        return "T-Shirt Sizing"

    def supported_component_types(self: Self) -> list[str]:
        """Return the component types this plugin supports."""
        return ["functional_process"]

    def measure(
        self: Self,
        story_points_result: object,
        mapping_override: list | None = None,
    ) -> TShirtMeasurementResult:
        """Measure T-Shirt sizes from a Story Points result."""
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
            execution_metadata=ExecutionMetadata(total_fps_processed=len(items)),
            warnings=warnings,
        )

    def _extract_items(self: Self, result: object) -> list:
        if isinstance(result, dict):
            return result.get("items") or result.get("estimated_items") or []
        if hasattr(result, "items"):
            return result.items
        return []


def create_tshirt_measurement_metadata() -> PluginMetadata:
    """Create the plugin metadata for the T-Shirt sizing plugin."""
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