from __future__ import annotations

from typing import Any, Optional, Protocol

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from .counter import SFPCounter
from .explainer import MeasurementExplainer
from .models import SFPMeasurementResult, RulePack

logger = structlog.get_logger(__name__)


class MeasurementPlugin(Protocol):
    def plugin_id(self) -> str: ...
    def supported_methodology(self) -> str: ...
    def supported_component_types(self) -> list[str]: ...
    def measure(
        self,
        cfm: CanonicalFunctionalModel,
        rule_pack: Optional[RulePack] = None,
        async_execution: bool = False,
    ) -> SFPMeasurementResult: ...


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


class SFPMeasurementPlugin:
    def plugin_id(self) -> str:
        return "sfp"

    def supported_methodology(self) -> str:
        return "Simple Function Points (SFP)"

    def supported_component_types(self) -> list[str]:
        return ["functional_process", "logical_function"]

    def measure(
        self,
        cfm: CanonicalFunctionalModel,
        rule_pack: Optional[RulePack] = None,
        async_execution: bool = False,
    ) -> SFPMeasurementResult:
        if cfm is None:
            raise ValueError("CFM input cannot be None")

        import time

        start_time = time.monotonic()

        rule_pack_id = None
        contribution_overrides = None
        excluded_component_types = None
        element_exclusions = None
        element_inclusions = None
        inclusion_criteria = None

        if rule_pack is not None:
            rule_pack_id = rule_pack.id
            contribution_overrides = rule_pack.contribution_overrides
            excluded_component_types = rule_pack.excluded_types
            element_exclusions = rule_pack.element_exclusions
            element_inclusions = rule_pack.element_inclusions
            inclusion_criteria = rule_pack.inclusion_criteria

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

        logger.info(
            "sfp_measurement_completed",
            total_components=result.summary.total_component_count,
            total_sfp=result.summary.total_sfp,
            duration_ms=round(duration_ms, 2),
            warnings_count=len(result.warnings),
        )

        if async_execution:
            import asyncio

            loop = asyncio.get_event_loop()
            future = loop.create_future()
            future.set_result(result)
            return future  # type: ignore[return-value]

        return result


class SFPMeasurementHandler:
    @property
    def handled_event_type(self) -> EventType:
        return EventType.MEASUREMENT_COMPLETED

    @property
    def handler_id(self) -> str:
        return "sfp_measurement"

    @property
    def stage_name(self) -> str:
        return "SFP Measurement"

    def handle(self, event: PipelineEvent) -> PipelineContext:
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
