from __future__ import annotations

from typing import Any, Optional, Protocol

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

    def plugin_id(self) -> str: ...
    def supported_methodology(self) -> str: ...
    def supported_function_types(self) -> list[str]: ...
    def measure(
        self,
        cfm: CanonicalFunctionalModel,
        rule_pack: Optional[RulePack] = None,
    ) -> FPAMeasurementResult: ...


class FPAMeasurementPlugin:
    def plugin_id(self) -> str:
        return "fpa"

    def supported_methodology(self) -> str:
        return "IFPUG/FPA Function Point Analysis"

    def supported_function_types(self) -> list[str]:
        return ["ILF", "EIF", "EI", "EO", "EQ"]

    def measure(
        self,
        cfm: CanonicalFunctionalModel,
        rule_pack: Optional[RulePack] = None,
    ) -> FPAMeasurementResult:
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
    @property
    def handled_event_type(self) -> EventType:
        return EventType.MEASUREMENT_COMPLETED

    @property
    def handler_id(self) -> str:
        return "fpa_measurement"

    @property
    def stage_name(self) -> str:
        return "FPA Measurement"

    def handle(self, event: PipelineEvent) -> PipelineContext:
        ctx = event.context
        cfm: CanonicalFunctionalModel | None = ctx.canonical_model

        if cfm is None:
            logger.warning("fpa_measurement_no_cfm", execution_id=str(ctx.execution_id))
            return ctx

        logger.info(
            "fpa_measurement_started",
            execution_id=str(ctx.execution_id),
        )

        plugin = FPAMeasurementPlugin()
        result = plugin.measure(cfm)

        payload: dict[str, Any] = {
            "total_function_points": result.summary.total_ufp,
            "breakdown": {ft: {"count": b.count, "total_ufp": b.total_ufp} for ft, b in result.summary.by_type.items()},
            "complexity_distribution": [
                {"function_type": c.function_type, "complexity": c.complexity, "count": c.count, "total_ufp": c.total_ufp}
                for c in result.summary.complexity_distribution
            ],
            "function_counts": result.summary.by_type,
            "complexity_counts": result.summary.by_complexity,
        }

        return ctx.with_stage_output("measurement_result", payload)


def create_fpa_measurement_metadata() -> PluginMetadata:
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
