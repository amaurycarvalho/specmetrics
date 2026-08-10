"""Token Points measurement plugin."""

from __future__ import annotations

from typing import Any, Self

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.csm.model import CanonicalSpecificationModel
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType
from specmetrics.plugins.calibration.models import CalibrationProfile

from .calculator import calculate
from .explainer import get_breakdown_by_type
from .models import TokenPointsMeasurement

logger = structlog.get_logger(__name__)


class TokenPointsHandler:
    """Pipeline handler that computes Token Points on measurement completion."""

    @property
    def handled_event_type(self: Self) -> EventType:
        """Return the event type this handler processes."""
        return EventType.MEASUREMENT_COMPLETED

    @property
    def handler_id(self: Self) -> str:
        """Return the unique identifier of this handler."""
        return "token_points_measurement"

    @property
    def stage_name(self: Self) -> str:
        """Return the display name of this handler stage."""
        return "Token Points Measurement"

    def handle(self: Self, event: PipelineEvent) -> PipelineContext:
        """Compute Token Points for the given pipeline event."""
        ctx = event.context
        cfm: CanonicalFunctionalModel | None = ctx.canonical_model
        csm: CanonicalSpecificationModel | None = ctx.canonical_spec_model
        calibration: CalibrationProfile = self._resolve_calibration(ctx)

        if not isinstance(cfm, CanonicalFunctionalModel):
            cfm = None

        if not isinstance(csm, CanonicalSpecificationModel):
            csm = None

        logger.info(
            "token_points_measurement_started",
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

        breakdown = get_breakdown_by_type(result)

        all_token_contributions = (
            result.specification_cost.contributions
            + result.code_generation_cost.contributions
        )
        token_entities = [c.model_dump(mode="json") for c in all_token_contributions]

        token_content_tokens: dict[str, int] = {}
        for t, v in breakdown.items():
            token_content_tokens[t] = v["content_tokens"]

        payload: dict[str, Any] = {
            "token_total_score": result.total_score,
            "token_specification_cost": result.specification_cost.total,
            "token_code_generation_cost": result.code_generation_cost.total,
            "token_content_multiplier": calibration.content_multiplier,
            "token_content_tokens": token_content_tokens,
            "token_element_counts": {
                "csm": result.measurement_metadata.csm_element_count,
                "cfm": result.measurement_metadata.cfm_element_count,
                "total": result.measurement_metadata.total_elements_processed,
                "unknown_csm": result.measurement_metadata.unknown_csm_element_count,
                "unknown_cfm": result.measurement_metadata.unknown_cfm_element_count,
            },
            "token_calibration_version": result.calibration_version,
            "token_top_contributors": [
                {
                    "type": t,
                    "count": v["count"],
                    "total": v["total"],
                    "content_tokens": v["content_tokens"],
                }
                for t, v in breakdown.items()
            ],
            "token_duration_ms": result.measurement_metadata.duration_ms,
            "token_warnings": [
                w.model_dump() for w in result.measurement_metadata.warnings
            ],
            "token_entities": token_entities,
        }

        token_event = PipelineEvent(
            event_type=EventType.TOKEN_POINTS_MEASURED,
            publisher="token_points",
            payload=payload,
            context=ctx,
        )

        logger.info(
            "token_points_measurement_completed",
            total_score=result.total_score,
            spec_cost=result.specification_cost.total,
            code_cost=result.code_generation_cost.total,
            element_count=result.measurement_metadata.total_elements_processed,
            duration_ms=result.measurement_metadata.duration_ms,
        )

        return ctx.merge_stage_output("measurement_result", payload, event=token_event)

    def _resolve_calibration(self: Self, ctx: PipelineContext) -> CalibrationProfile:
        metadata = ctx.metadata
        if isinstance(metadata, CalibrationProfile):
            return metadata
        from .calibration import get_default_calibration

        return get_default_calibration()


class TokenPointsPlugin:
    """Plugin facade exposing the Token Points measurement methodology."""

    def plugin_id(self: Self) -> str:
        """Return the unique plugin identifier."""
        return "token_points"

    def supported_methodology(self: Self) -> str:
        """Return the methodology name supported by this plugin."""
        return "Token Points"

    def measure(
        self: Self,
        cfm: CanonicalFunctionalModel | None,
        csm: CanonicalSpecificationModel | None = None,
        calibration: CalibrationProfile | None = None,
    ) -> TokenPointsMeasurement:
        """Measure Token Points from the given CFM and CSM models."""
        if calibration is None:
            from .calibration import get_default_calibration

            calibration = get_default_calibration()
        return calculate(cfm, csm, calibration, run_id="")


def create_token_points_measurement_metadata() -> PluginMetadata:
    """Create the plugin metadata for the Token Points plugin."""
    return PluginMetadata(
        id="token_points",
        api_version="0.1.0",
        plugin_type=PluginType.MEASUREMENT,
        handled_event_types=(EventType.MEASUREMENT_COMPLETED,),
        handler_factory=lambda: TokenPointsHandler(),
        name="Token Points",
        description="Token Points measurement — estimates AI computational cost from CFM and CSM with per-element explainability",
        version="0.1.0",
    )
