from __future__ import annotations

from pathlib import Path
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
from specmetrics.kernel.csm.model import CanonicalSpecificationModel
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from .calculator import calculate
from .calibrator import StoryPointsCalibrationProfile, load_calibration
from .models import StoryPointMeasurementResult

logger = structlog.get_logger(__name__)


class StoryPointsHandler:
    def __init__(self, calibration_dir: str | Path | None = None) -> None:
        self._calibration_dir = calibration_dir
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
        csm: Optional[CanonicalSpecificationModel] = ctx.canonical_spec_model

        if not isinstance(cfm, CanonicalFunctionalModel):
            cfm = None
        if not isinstance(csm, CanonicalSpecificationModel):
            csm = None

        logger.info(
            "storypoints_measurement_started",
            execution_id=str(ctx.execution_id),
            has_cfm=cfm is not None,
            has_csm=csm is not None,
        )

        calibration = load_calibration(self._calibration_dir)

        result = calculate(
            cfm,
            run_id=str(ctx.execution_id),
            csm=csm,
            calibration=calibration,
        )

        if _measurement_duration is not None:
            _measurement_duration.record(result.execution_metadata.duration_ms)
        if _item_gauge is not None:
            _item_gauge.set(result.execution_metadata.fps_estimated)
        if _distribution_histogram is not None:
            for value, count in result.distribution.items():
                _distribution_histogram.record(count, {"storypoint_value": str(value)})

        dist_str = {str(k): v for k, v in result.distribution.items()}

        storypoints_entities = [item.model_dump(mode="json") for item in result.items]

        payload: dict[str, Any] = {
            "storypoints_method": result.method,
            "storypoints_scale": result.scale,
            "storypoints_total_story_points": result.total_story_points,
            "storypoints_estimated_items": len(result.items),
            "storypoints_distribution": dist_str,
            "storypoints_total_raw_score": result.total_raw_score,
            "storypoints_specification_effort_total": result.specification_effort_total,
            "storypoints_implementation_effort_total": result.implementation_effort_total,
            "storypoints_content_multiplier": result.content_multiplier,
            "storypoints_calibration_version": result.calibration_version,
            "storypoints_duration_ms": result.execution_metadata.duration_ms,
            "storypoints_warnings": [w.model_dump() for w in result.warnings],
            "storypoints_entities": storypoints_entities,
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

        return ctx.merge_stage_output(
            "measurement_result", payload, event=storypoints_event
        )



class StoryPointsPlugin:
    def __init__(self, calibration_dir: str | Path | None = None) -> None:
        self._calibration_dir = calibration_dir

    def plugin_id(self) -> str:
        return "storypoints"

    def supported_methodology(self) -> str:
        return "Story Points"

    def measure(
        self,
        cfm: CanonicalFunctionalModel | None,
        csm: CanonicalSpecificationModel | None = None,
        previous_fingerprints: dict[str, str] | None = None,
        calibration: StoryPointsCalibrationProfile | None = None,
    ) -> StoryPointMeasurementResult:
        if calibration is None:
            calibration = load_calibration(self._calibration_dir)
        return calculate(
            cfm,
            run_id="",
            previous_fingerprints=previous_fingerprints,
            csm=csm,
            calibration=calibration,
        )


def create_storypoints_measurement_metadata(
    calibration_dir: str | Path | None = None,
) -> PluginMetadata:
    return PluginMetadata(
        id="storypoints",
        api_version="0.1.0",
        plugin_type=PluginType.MEASUREMENT,
        handled_event_types=(EventType.MEASUREMENT_COMPLETED,),
        handler_factory=lambda: StoryPointsHandler(
            calibration_dir=calibration_dir,
        ),
        name="Story Points",
        description="Story Points measurement — estimates relative implementation effort from CFM using multi-factor weighted sum and Modified Fibonacci normalization. "
        "Supports configurable calibration profiles, CSM element estimation, and relative ranking normalization.",
        version="0.1.0",
    )
