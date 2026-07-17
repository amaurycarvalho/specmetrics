from __future__ import annotations

from pathlib import Path

import structlog

from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from .loader import discover_and_load_calibration
from .models import CalibrationProfile

logger = structlog.get_logger(__name__)


class CalibrationHandler:
    @property
    def handled_event_type(self) -> EventType:
        return EventType.RULE_PACK_APPLIED

    @property
    def handler_id(self) -> str:
        return "calibration_loader"

    @property
    def stage_name(self) -> str:
        return "Calibration Profile Loading"

    def handle(self, event: PipelineEvent) -> PipelineContext:
        ctx = event.context

        calibration_dir = Path(".specmetrics") / "calibration"
        profile = discover_and_load_calibration(calibration_dir)

        if profile is None:
            profile = CalibrationProfile()

        logger.info(
            "calibration_loaded",
            version=profile.version,
            calibration_dir=str(calibration_dir),
        )

        return ctx.with_stage_output("metadata", profile)


class CalibrationPlugin:
    def plugin_id(self) -> str:
        return "calibration"

    def load_calibration(
        self, calibration_dir: str | Path | None = None
    ) -> CalibrationProfile:
        if calibration_dir is not None:
            profile = discover_and_load_calibration(calibration_dir)
            if profile is not None:
                return profile
        return CalibrationProfile()


def create_calibration_metadata() -> PluginMetadata:
    return PluginMetadata(
        id="calibration",
        api_version="0.1.0",
        plugin_type=PluginType.MEASUREMENT,
        handled_event_types=(EventType.RULE_PACK_APPLIED,),
        handler_factory=lambda: CalibrationHandler(),
        name="Calibration Profile Loader",
        description="Loads and merges calibration profiles from YAML files",
        version="0.1.0",
    )
