from __future__ import annotations

from typing import Any, Optional

import structlog

try:
    from opentelemetry import metrics as otel_metrics

    _meter = otel_metrics.get_meter("specmetrics.storypoints")
    _measurement_duration = _meter.create_histogram(
        name="storypoints.estimation.duration",
        description="Duration of Story Points estimation execution",
        unit="ms",
    )
    _item_gauge = _meter.create_gauge(
        name="storypoints.estimated_items",
        description="Number of Functional Processes estimated",
    )
    _distribution_histogram = _meter.create_histogram(
        name="storypoints.distribution",
        description="Distribution of estimated Story Point values",
        unit="1",
    )
except Exception:
    _measurement_duration = None
    _item_gauge = None
    _distribution_histogram = None

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from .calculator import calculate
from .models import StoryPointMeasurementResult

logger = structlog.get_logger(__name__)


class StoryPointsHandler:
    @property
    def handled_event_type(self) -> EventType:
        return EventType.MEASUREMENT_COMPLETED

    @property
    def handler_id(self) -> str:
        return "storypoints_measurement"

    @property
    def stage_name(self) -> str:
        return "Story Points Measurement"

    def handle(self, event: PipelineEvent) -> PipelineContext:
        ctx = event.context
        cfm: Optional[CanonicalFunctionalModel] = ctx.canonical_model

        if not isinstance(cfm, CanonicalFunctionalModel):
            cfm = None

        logger.info(
            "storypoints_measurement_started",
            execution_id=str(ctx.execution_id),
            has_cfm=cfm is not None,
        )

        coefficients, thresholds, output_values = self._resolve_rule_pack_overrides(cfm)

        result = calculate(
            cfm,
            run_id=str(ctx.execution_id),
            coefficients=coefficients,
            thresholds=thresholds,
            output_values=output_values,
        )

        if _measurement_duration is not None:
            _measurement_duration.record(result.execution_metadata.duration_ms)
        if _item_gauge is not None:
            _item_gauge.set(result.execution_metadata.fps_estimated)
        if _distribution_histogram is not None:
            for value, count in result.distribution.items():
                _distribution_histogram.record(count, {"storypoint_value": str(value)})

        dist_str = {str(k): v for k, v in result.distribution.items()}

        payload: dict[str, Any] = {
            "method": result.method,
            "scale": result.scale,
            "total_story_points": result.total_story_points,
            "estimated_items": len(result.items),
            "distribution": dist_str,
            "applied_rule_pack": result.applied_rule_pack,
            "duration_ms": result.execution_metadata.duration_ms,
            "warnings": [
                w.model_dump() for w in result.warnings
            ],
        }

        storypoints_event = PipelineEvent(
            event_type=EventType.STORY_POINTS_MEASURED,
            publisher="storypoints",
            payload=payload,
            context=ctx,
        )

        logger.info(
            "storypoints_measurement_completed",
            total_story_points=result.total_story_points,
            estimated_items=len(result.items),
            duration_ms=result.execution_metadata.duration_ms,
        )

        return ctx.with_stage_output(
            "measurement_result", payload, event=storypoints_event
        )

    def _resolve_rule_pack_overrides(
        self, cfm: CanonicalFunctionalModel | None
    ) -> tuple[dict[str, float] | None, list[float] | None, list[int] | None]:
        if cfm is None:
            return None, None, None

        coefficients: dict[str, float] | None = None
        thresholds: list[float] | None = None
        output_values: list[int] | None = None

        cfm_metadata = cfm.metadata if hasattr(cfm, "metadata") else None
        if cfm_metadata is not None:
            extra = getattr(cfm_metadata, "extra", None) or {}
            coeffs_raw = extra.get("storypoints_coefficients")
            if isinstance(coeffs_raw, dict):
                coefficients = {k: float(v) for k, v in coeffs_raw.items()}
            thresholds_raw = extra.get("storypoints_thresholds")
            if isinstance(thresholds_raw, list):
                thresholds = [float(v) for v in thresholds_raw]
            values_raw = extra.get("storypoints_output_values")
            if isinstance(values_raw, list):
                output_values = [int(v) for v in values_raw]

        return coefficients, thresholds, output_values


class StoryPointsPlugin:
    def plugin_id(self) -> str:
        return "storypoints"

    def supported_methodology(self) -> str:
        return "Story Points"

    def measure(
        self,
        cfm: CanonicalFunctionalModel | None,
        previous_fingerprints: dict[str, str] | None = None,
    ) -> StoryPointMeasurementResult:
        return calculate(cfm, run_id="", previous_fingerprints=previous_fingerprints)


def create_storypoints_measurement_metadata() -> PluginMetadata:
    return PluginMetadata(
        id="storypoints",
        api_version="0.1.0",
        plugin_type=PluginType.MEASUREMENT,
        handled_event_types=(EventType.MEASUREMENT_COMPLETED,),
        handler_factory=lambda: StoryPointsHandler(),
        name="Story Points",
        description="Story Points measurement — estimates relative implementation effort from CFM using multi-factor weighted sum and Modified Fibonacci normalization",
        version="0.1.0",
    )
