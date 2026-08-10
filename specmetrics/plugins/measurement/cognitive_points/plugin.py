"""Cognitive Points measurement plugin."""

from __future__ import annotations

from typing import Any, Self

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.csm.model import CanonicalSpecificationModel
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from .calculator import calculate
from .calibration import CognitiveCalibrationProfile
from .models import CognitivePointsMeasurement

logger = structlog.get_logger(__name__)


class CognitivePointsHandler:
    """Pipeline handler that computes Cognitive Points on measurement completion."""

    @property
    def handled_event_type(self: Self) -> EventType:
        """Return the event type this handler processes."""
        return EventType.MEASUREMENT_COMPLETED

    @property
    def handler_id(self: Self) -> str:
        """Return the unique identifier of this handler."""
        return "cognitive_points_measurement"

    @property
    def stage_name(self: Self) -> str:
        """Return the display name of this handler stage."""
        return "Cognitive Points Measurement"

    def handle(self: Self, event: PipelineEvent) -> PipelineContext:
        """Compute Cognitive Points for the given pipeline event."""
        ctx = event.context
        cfm: CanonicalFunctionalModel | None = ctx.canonical_model
        csm: CanonicalSpecificationModel | None = ctx.canonical_spec_model
        calibration = self._resolve_calibration(ctx)

        if not isinstance(cfm, CanonicalFunctionalModel):
            cfm = None

        if not isinstance(csm, CanonicalSpecificationModel):
            csm = None

        logger.info(
            "cognitive_points_measurement_started",
            execution_id=str(ctx.execution_id),
            has_cfm=cfm is not None,
            has_csm=csm is not None,
        )

        result = calculate(
            cfm,
            csm,
            calibration,
            run_id=str(ctx.execution_id),
        )

        spec_bloom = dict(result.specification_review_effort.bloom_breakdown)
        func_bloom = dict(result.functional_validation_effort.bloom_breakdown)

        all_cognitive_contributions = (
            result.specification_review_effort.contributions
            + result.functional_validation_effort.contributions
        )
        cognitive_entities = [
            c.model_dump(mode="json") for c in all_cognitive_contributions
        ]

        bloom_breakdown: dict[str, float] = {}
        for c in all_cognitive_contributions:
            level = c.bloom_level
            bloom_breakdown[level] = bloom_breakdown.get(level, 0.0) + c.partial_score

        bloom_levels = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
        cognitive_bloom_breakdown = {
            level: {"total": bloom_breakdown[level]}
            for level in bloom_levels
            if bloom_breakdown.get(level, 0.0) > 0
        }

        cognitive_content_tokens: dict[str, int] = {}
        for c in all_cognitive_contributions:
            etype = c.element_type
            cognitive_content_tokens[etype] = (
                cognitive_content_tokens.get(etype, 0) + c.content_token_count
            )

        payload: dict[str, Any] = {
            "cognitive_total_cognitive_points": result.total_cognitive_points,
            "cognitive_raw_score": result.raw_score,
            "cognitive_specification_review_effort": {
                "total_raw": result.specification_review_effort.total_raw,
                "bloom_breakdown": spec_bloom,
            },
            "cognitive_functional_validation_effort": {
                "total_raw": result.functional_validation_effort.total_raw,
                "bloom_breakdown": func_bloom,
            },
            "cognitive_fibonacci_normalization": {
                "raw_score": result.fibonacci_normalization.raw_score,
                "threshold": result.fibonacci_normalization.threshold_applied,
                "output": result.fibonacci_normalization.output_value,
            },
            "cognitive_content_multiplier": calibration.content_multiplier,
            "cognitive_content_tokens": cognitive_content_tokens,
            "cognitive_element_counts": {
                "csm": result.measurement_metadata.csm_element_count,
                "cfm": result.measurement_metadata.cfm_element_count,
                "total": result.measurement_metadata.total_elements_processed,
            },
            "cognitive_bloom_distribution": dict(
                result.measurement_metadata.bloom_distribution
            ),
            "cognitive_calibration_version": result.calibration_version,
            "cognitive_duration_ms": result.measurement_metadata.duration_ms,
            "cognitive_warnings": [
                w.model_dump() for w in result.measurement_metadata.warnings
            ],
            "cognitive_entities": cognitive_entities,
            "cognitive_bloom_breakdown": cognitive_bloom_breakdown,
        }

        cognitive_event = PipelineEvent(
            event_type=EventType.COGNITIVE_POINTS_MEASURED,
            publisher="cognitive_points",
            payload=payload,
            context=ctx,
        )

        logger.info(
            "cognitive_points_measurement_completed",
            total_cognitive_points=result.total_cognitive_points,
            raw_score=result.raw_score,
            spec_effort=result.specification_review_effort.total_raw,
            func_effort=result.functional_validation_effort.total_raw,
            element_count=result.measurement_metadata.total_elements_processed,
            duration_ms=result.measurement_metadata.duration_ms,
        )

        return ctx.merge_stage_output(
            "measurement_result", payload, event=cognitive_event
        )

    def _resolve_calibration(self: Self, ctx: PipelineContext) -> CognitiveCalibrationProfile | None:
        metadata = ctx.metadata
        if isinstance(metadata, CognitiveCalibrationProfile):
            return metadata
        from .calibration import get_default_calibration

        return get_default_calibration()


class CognitivePointsPlugin:
    """Plugin facade exposing the Cognitive Points measurement methodology."""

    def plugin_id(self: Self) -> str:
        """Return the unique plugin identifier."""
        return "cognitive_points"

    def supported_methodology(self: Self) -> str:
        """Return the methodology name supported by this plugin."""
        return "Cognitive Points"

    def measure(
        self: Self,
        cfm: CanonicalFunctionalModel | None,
        csm: CanonicalSpecificationModel | None = None,
        calibration: CognitiveCalibrationProfile | None = None,
    ) -> CognitivePointsMeasurement:
        """Measure Cognitive Points from the given CFM and CSM models."""
        if calibration is None:
            from .calibration import get_default_calibration

            calibration = get_default_calibration()
        return calculate(cfm, csm, calibration, run_id="")


def create_cognitive_points_measurement_metadata() -> PluginMetadata:
    """Create the plugin metadata for the Cognitive Points plugin."""
    return PluginMetadata(
        id="cognitive_points",
        api_version="0.1.0",
        plugin_type=PluginType.MEASUREMENT,
        handled_event_types=(EventType.MEASUREMENT_COMPLETED,),
        handler_factory=lambda: CognitivePointsHandler(),
        name="Cognitive Points",
        description="Cognitive Points measurement — estimates human cognitive effort from CFM and CSM using Bloom taxonomy and Fibonacci normalization",
        version="0.1.0",
    )
