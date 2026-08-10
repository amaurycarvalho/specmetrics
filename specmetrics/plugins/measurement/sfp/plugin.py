"""SFP measurement plugin: handler, plugin, and metadata factory."""

from __future__ import annotations

from typing import Any, Protocol, Self

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from .counter import SFPCounter
from .explainer import MeasurementExplainer
from .models import RulePack, SFPMeasurementResult

logger = structlog.get_logger(__name__)


class MeasurementPlugin(Protocol):
    """Protocol that every measurement engine plugin must satisfy."""

    def plugin_id(self: Self) -> str:
        """Return the plugin identifier."""
        ...

    def supported_methodology(self: Self) -> str:
        """Return the methodology name implemented by this plugin."""
        ...

    def supported_component_types(self: Self) -> list[str]:
        """Return the component types measured by this plugin."""
        ...

    def measure(
        self: Self,
        cfm: CanonicalFunctionalModel,
        rule_pack: RulePack | None = None,
        async_execution: bool = False,
    ) -> SFPMeasurementResult:
        """Measure SFP for the given canonical functional model."""
        ...


try:
    from opentelemetry import metrics as otel_metrics

    _meter = otel_metrics.get_meter("specmetrics.sfp")
    _measurement_duration = _meter.create_histogram(
        name="sfp.measurement.duration",
        description="Duration of SFP measurement execution",
        unit="ms",
    )
    _fp_gauge = _meter.create_gauge(
        name="sfp.functional_processes",
        description="Number of Functional Processes measured",
    )
    _lf_gauge = _meter.create_gauge(
        name="sfp.logical_functions",
        description="Number of Logical Functions measured",
    )
except Exception:
    _measurement_duration = None
    _fp_gauge = None
    _lf_gauge = None


def _resolve_rule_pack(
    rule_pack: RulePack | None,
) -> tuple[
    str | None,
    object | None,
    object | None,
    object | None,
    object | None,
    object | None,
]:
    if rule_pack is None:
        return (None, None, None, None, None, None)
    return (
        rule_pack.id,
        rule_pack.contribution_overrides,
        rule_pack.excluded_types,
        rule_pack.element_exclusions,
        rule_pack.element_inclusions,
        rule_pack.inclusion_criteria,
    )


def _record_metrics(result: SFPMeasurementResult, duration_ms: float) -> None:
    if _measurement_duration is not None:
        _measurement_duration.record(duration_ms)
    if _fp_gauge is not None:
        fp_count = sum(
            1
            for c in result.measured_components
            if c.component_type == "functional_process"
        )
        _fp_gauge.set(fp_count)
    if _lf_gauge is not None:
        lf_count = sum(
            1
            for c in result.measured_components
            if c.component_type == "logical_function"
        )
        _lf_gauge.set(lf_count)


class SFPMeasurementPlugin:
    """Measurement engine plugin for Simple Function Points."""

    def plugin_id(self: Self) -> str:
        """Return the plugin identifier."""
        return "sfp"

    def supported_methodology(self: Self) -> str:
        """Return the methodology name implemented by this plugin."""
        return "Simple Function Points (SFP)"

    def supported_component_types(self: Self) -> list[str]:
        """Return the component types measured by this plugin."""
        return ["functional_process", "logical_function"]

    def measure(
        self: Self,
        cfm: CanonicalFunctionalModel,
        rule_pack: RulePack | None = None,
        async_execution: bool = False,
    ) -> SFPMeasurementResult:
        """Measure SFP for the given canonical functional model."""
        if cfm is None:
            raise ValueError("CFM input cannot be None")

        import time

        start_time = time.monotonic()

        (
            rule_pack_id,
            contribution_overrides,
            excluded_component_types,
            element_exclusions,
            element_inclusions,
            inclusion_criteria,
        ) = _resolve_rule_pack(rule_pack)

        logger.info(
            "sfp_measurement_started",
            component_count=len(cfm.operations) + len(cfm.data_groups),
            rule_pack_id=rule_pack_id,
        )

        counter = SFPCounter()
        result = counter.count(
            cfm,
            rule_pack_id=rule_pack_id,
            contribution_overrides=contribution_overrides,
            excluded_types=excluded_component_types,
            element_exclusions=element_exclusions,
            element_inclusions=element_inclusions,
            inclusion_criteria=inclusion_criteria,
        )

        explainer = MeasurementExplainer()
        result.explanations.extend(explainer.build_explanations(result))

        duration_ms = (time.monotonic() - start_time) * 1000

        _record_metrics(result, duration_ms)

        logger.info(
            "sfp_measurement_completed",
            total_components=result.summary.total_component_count,
            total_sfp=result.summary.total_sfp,
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
            return future  # type: ignore[return-value]

        return result


class SFPMeasurementHandler:
    """Pipeline event handler for SFP measurement."""

    @property
    def handled_event_type(self: Self) -> EventType:
        """Return the event type this handler consumes."""
        return EventType.MEASUREMENT_COMPLETED

    @property
    def handler_id(self: Self) -> str:
        """Return the unique identifier of this handler."""
        return "sfp_measurement"

    @property
    def stage_name(self: Self) -> str:
        """Return the human-readable name of this handler stage."""
        return "SFP Measurement"

    def handle(self: Self, event: PipelineEvent) -> PipelineContext:
        """Measure SFP for the event context and merge stage output."""
        ctx = event.context
        cfm = ctx.canonical_model

        if not isinstance(cfm, CanonicalFunctionalModel):
            logger.warning("sfp_measurement_no_cfm", execution_id=str(ctx.execution_id))
            return ctx

        plugin = SFPMeasurementPlugin()
        result = plugin.measure(cfm)

        sfp_entities = [c.model_dump(mode="json") for c in result.measured_components]

        payload: dict[str, Any] = {
            "sfp_total_sfp": result.summary.total_sfp,
            "sfp_total_components": result.summary.total_component_count,
            "sfp_breakdown": {
                ct: {"count": b.count, "total_sfp": b.total_sfp}
                for ct, b in result.summary.by_type.items()
            },
            "sfp_entities": sfp_entities,
        }

        return ctx.merge_stage_output("measurement_result", payload)


def create_sfp_measurement_metadata() -> PluginMetadata:
    """Build the plugin metadata entry for the SFP measurement plugin."""
    return PluginMetadata(
        id="sfp",
        api_version="0.1.0",
        plugin_type=PluginType.MEASUREMENT,
        handled_event_types=(EventType.MEASUREMENT_COMPLETED,),
        handler_factory=lambda: SFPMeasurementHandler(),
        name="SFP Simple Function Points",
        description="Simple Function Points (SFP) measurement methodology",
        version="0.1.0",
    )
