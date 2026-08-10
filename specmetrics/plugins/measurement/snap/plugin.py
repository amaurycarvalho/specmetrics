"""SNAP measurement plugin: handler, plugin, and metadata factory."""

from __future__ import annotations

from typing import Any, Protocol, Self

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from .assessor import SNAPAssessor
from .explainer import AssessmentExplainer
from .models import RulePack, SNAPMeasurementResult

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
        async_execution: bool = False,
    ) -> SNAPMeasurementResult:
        """Measure SNAP for the given canonical functional model."""
        ...


try:
    from opentelemetry import metrics as otel_metrics

    _meter = otel_metrics.get_meter("specmetrics.snap")
    _measurement_duration = _meter.create_histogram(
        name="snap.measurement.duration",
        description="Duration of SNAP measurement execution",
        unit="ms",
    )
    _category_gauge = _meter.create_gauge(
        name="snap.category_item_count",
        description="Per-category assessment item count",
    )
except Exception:
    _measurement_duration = None
    _category_gauge = None


class SNAPMeasurementPlugin:
    """Measurement engine plugin for SNAP assessment."""

    def plugin_id(self: Self) -> str:
        """Return the plugin identifier."""
        return "snap"

    def supported_methodology(self: Self) -> str:
        """Return the methodology name implemented by this plugin."""
        return "SNAP (Software Non-functional Assessment Process)"

    def supported_function_types(self: Self) -> list[str]:
        """Return the function types measured by this plugin."""
        return [
            "presentation",
            "data_operations",
            "operational_capabilities",
            "technical_interaction",
        ]

    def measure(
        self: Self,
        cfm: CanonicalFunctionalModel,
        rule_pack: RulePack | None = None,
        async_execution: bool = False,
    ) -> SNAPMeasurementResult:
        """Measure SNAP for the given canonical functional model."""
        if cfm is None:
            raise ValueError("CFM input cannot be None")

        import time

        start_time = time.monotonic()

        rule_pack_id = None
        if rule_pack is not None:
            rule_pack_id = rule_pack.id

        total_element_count = (
            len(cfm.operations)
            + len(cfm.data_groups)
            + len(cfm.functional_processes)
            + len(cfm.business_rules)
            + len(cfm.actors)
            + len(cfm.unclassified)
            + len(cfm.relationships)
        )

        logger.info(
            "snap_measurement_started",
            element_count=total_element_count,
            rule_pack_id=rule_pack_id,
        )

        assessor = SNAPAssessor()
        result = assessor.assess(cfm, rule_pack=rule_pack)

        explainer = AssessmentExplainer()
        explanations = explainer.build_explanations(result)
        result = result.model_copy(update={"explanations": explanations})

        duration_ms = (time.monotonic() - start_time) * 1000

        if _measurement_duration is not None:
            _measurement_duration.record(duration_ms)
        if _category_gauge is not None:
            for cat in result.categories:
                _category_gauge.set(len(cat.items), {"category": cat.category_id})

        logger.info(
            "snap_measurement_completed",
            total_items=result.summary.total_item_count,
            total_snap=result.summary.total_snap,
            duration_ms=round(duration_ms, 2),
            warnings_count=len(result.warnings),
        )

        if async_execution:
            import asyncio

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
            future = loop.create_future()
            future.set_result(result)
            return future

        return result


class SNAPMeasurementHandler:
    """Pipeline event handler for SNAP measurement."""

    @property
    def handled_event_type(self: Self) -> EventType:
        """Return the event type this handler consumes."""
        return EventType.MEASUREMENT_COMPLETED

    @property
    def handler_id(self: Self) -> str:
        """Return the unique identifier of this handler."""
        return "snap_measurement"

    @property
    def stage_name(self: Self) -> str:
        """Return the human-readable name of this handler stage."""
        return "SNAP Measurement"

    def handle(self: Self, event: PipelineEvent) -> PipelineContext:
        """Measure SNAP for the event context and merge stage output."""
        ctx = event.context
        cfm = ctx.canonical_model

        if not isinstance(cfm, CanonicalFunctionalModel):
            logger.warning(
                "snap_measurement_no_cfm", execution_id=str(ctx.execution_id)
            )
            return ctx

        plugin = SNAPMeasurementPlugin()
        result = plugin.measure(cfm)

        snap_entities = [a.model_dump(mode="json") for a in result.assessed_items]

        payload: dict[str, Any] = {
            "snap_total_snap": result.summary.total_snap,
            "snap_total_items": result.summary.total_item_count,
            "snap_by_category": {
                cat.category_id: {
                    "count": len(cat.items),
                    "total_contribution": cat.total_contribution,
                }
                for cat in result.categories
            },
            "snap_entities": snap_entities,
        }

        return ctx.merge_stage_output("measurement_result", payload)


def create_snap_measurement_metadata() -> PluginMetadata:
    """Build the plugin metadata entry for the SNAP measurement plugin."""
    return PluginMetadata(
        id="snap",
        api_version="0.1.0",
        plugin_type=PluginType.MEASUREMENT,
        handled_event_types=(EventType.MEASUREMENT_COMPLETED,),
        handler_factory=lambda: SNAPMeasurementHandler(),
        name="SNAP Software Non-functional Assessment",
        description="SNAP (Software Non-functional Assessment Process) measurement methodology",
        version="0.1.0",
    )
