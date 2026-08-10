"""FPA measurement plugin: handler, plugin, and metadata factory."""

from __future__ import annotations

from typing import Any, Protocol, Self

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from .complexity import UFP_WEIGHTS
from .counter import FPACounter
from .explainer import MeasurementExplainer
from .models import FPAMeasurementResult, RulePack

logger = structlog.get_logger(__name__)


class MeasurementPlugin(Protocol):
    """Protocol that every measurement engine plugin must satisfy."""

    def plugin_id(self: Self) -> str:
        """Return the plugin identifier."""
        ...

    def supported_methodology(self: Self) -> str:
        """Return the methodology name implemented by this plugin."""
        ...

    def supported_function_types(self: Self) -> list[str]:
        """Return the function types measured by this plugin."""
        ...

    def measure(
        self: Self,
        cfm: CanonicalFunctionalModel,
        rule_pack: RulePack | None = None,
    ) -> FPAMeasurementResult:
        """Measure function points for the given canonical functional model."""
        ...


class FPAMeasurementPlugin:
    """Measurement engine plugin for IFPUG/FPA Function Point Analysis."""

    def plugin_id(self: Self) -> str:
        """Return the plugin identifier."""
        return "fpa"

    def supported_methodology(self: Self) -> str:
        """Return the methodology name implemented by this plugin."""
        return "IFPUG/FPA Function Point Analysis"

    def supported_function_types(self: Self) -> list[str]:
        """Return the function types measured by this plugin."""
        return ["ILF", "EIF", "EI", "EO", "EQ"]

    def measure(
        self: Self,
        cfm: CanonicalFunctionalModel,
        rule_pack: RulePack | None = None,
    ) -> FPAMeasurementResult:
        """Measure function points for the given canonical functional model."""
        if cfm is None:
            raise ValueError("CFM input cannot be None")

        weight_overrides = None
        excluded_types = None
        rule_pack_id = None

        if rule_pack is not None:
            rule_pack_id = rule_pack.id
            if rule_pack.weight_overrides:
                merged = {}
                for ft in UFP_WEIGHTS:
                    merged[ft] = {
                        **UFP_WEIGHTS[ft],
                        **(rule_pack.weight_overrides.get(ft) or {}),
                    }
                weight_overrides = merged
            if rule_pack.excluded_types:
                excluded_types = rule_pack.excluded_types

        counter = FPACounter()
        result = counter.count(
            cfm,
            rule_pack_id=rule_pack_id,
            weight_overrides=weight_overrides,
            excluded_types=excluded_types,
        )

        explainer = MeasurementExplainer()
        result.explanations.extend(explainer.build_explanations(result))

        return result


class FPAMeasurementHandler:
    """Pipeline event handler for FPA measurement."""

    @property
    def handled_event_type(self: Self) -> EventType:
        """Return the event type this handler consumes."""
        return EventType.MEASUREMENT_COMPLETED

    @property
    def handler_id(self: Self) -> str:
        """Return the unique identifier of this handler."""
        return "fpa_measurement"

    @property
    def stage_name(self: Self) -> str:
        """Return the human-readable name of this handler stage."""
        return "FPA Measurement"

    def handle(self: Self, event: PipelineEvent) -> PipelineContext:
        """Measure FPA for the event context and merge stage output."""
        ctx = event.context
        cfm = ctx.canonical_model

        if not isinstance(cfm, CanonicalFunctionalModel):
            logger.warning("fpa_measurement_no_cfm", execution_id=str(ctx.execution_id))
            return ctx

        logger.info(
            "fpa_measurement_started",
            execution_id=str(ctx.execution_id),
        )

        plugin = FPAMeasurementPlugin()
        result = plugin.measure(cfm)

        fpa_entities = [f.model_dump(mode="json") for f in result.measured_functions]

        vaf = result.summary.vaf

        payload: dict[str, Any] = {
            "fpa_total_function_points": result.summary.total_ufp,
            "fpa_breakdown": {
                ft: {"count": b.count, "total_ufp": b.total_ufp}
                for ft, b in result.summary.by_type.items()
            },
            "fpa_complexity_distribution": [
                {
                    "function_type": c.function_type,
                    "complexity": c.complexity,
                    "count": c.count,
                    "total_ufp": c.total_ufp,
                }
                for c in result.summary.complexity_distribution
            ],
            "fpa_function_counts": result.summary.by_type,
            "fpa_complexity_counts": result.summary.by_complexity,
            "fpa_entities": fpa_entities,
        }
        if vaf is not None:
            payload["fpa_vaf"] = vaf

        return ctx.merge_stage_output("measurement_result", payload)


def create_fpa_measurement_metadata() -> PluginMetadata:
    """Build the plugin metadata entry for the FPA measurement plugin."""
    return PluginMetadata(
        id="fpa",
        api_version="0.1.0",
        plugin_type=PluginType.MEASUREMENT,
        handled_event_types=(EventType.MEASUREMENT_COMPLETED,),
        handler_factory=lambda: FPAMeasurementHandler(),
        name="FPA Function Point Analysis",
        description="IFPUG-approved Albrecht/FPA Function Point measurement methodology",
        version="0.1.0",
    )
