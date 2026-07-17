from __future__ import annotations

from typing import Any, Optional, Protocol

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
    def plugin_id(self) -> str: ...
    def supported_methodology(self) -> str: ...
    def supported_function_types(self) -> list[str]: ...
    def measure(
        self,
        cfm: CanonicalFunctionalModel,
        rule_pack: Optional[RulePack] = None,
        async_execution: bool = False,
    ) -> SNAPMeasurementResult: ...


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
    def plugin_id(self) -> str:
        return "snap"

    def supported_methodology(self) -> str:
        return "SNAP (Software Non-functional Assessment Process)"

    def supported_function_types(self) -> list[str]:
        return ["presentation", "data_operations", "operational_capabilities", "technical_interaction"]

    def measure(
        self,
        cfm: CanonicalFunctionalModel,
        rule_pack: Optional[RulePack] = None,
        async_execution: bool = False,
    ) -> SNAPMeasurementResult:
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
    @property
    def handled_event_type(self) -> EventType:
        return EventType.MEASUREMENT_COMPLETED

    @property
    def handler_id(self) -> str:
        return "snap_measurement"

    @property
    def stage_name(self) -> str:
        return "SNAP Measurement"

    def handle(self, event: PipelineEvent) -> PipelineContext:
        ctx = event.context
        cfm = ctx.canonical_model

        if not isinstance(cfm, CanonicalFunctionalModel):
            logger.warning("snap_measurement_no_cfm", execution_id=str(ctx.execution_id))
            return ctx

        plugin = SNAPMeasurementPlugin()
        result = plugin.measure(cfm)

        payload: dict[str, Any] = {
            "total_snap": result.summary.total_snap,
            "total_items": result.summary.total_item_count,
            "by_category": {
                cat.category_id: {"count": len(cat.items), "total_contribution": cat.total_contribution}
                for cat in result.categories
            },
        }

        return ctx.with_stage_output("measurement_result", payload)


def create_snap_measurement_metadata() -> PluginMetadata:
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
