"""Calibration profile loading plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Self

import structlog

from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from .loader import discover_and_load_calibration
from .models import CalibrationProfile

logger = structlog.get_logger(__name__)


class CalibrationHandler:
    """Handler that loads and merges calibration profiles."""

    @property
    def handled_event_type(self: Self) -> EventType:
        """Return the handled event type."""
        return EventType.RULE_PACK_APPLIED

    @property
    def handler_id(self: Self) -> str:
        """Return the handler identifier."""
        return "calibration_loader"

    @property
    def stage_name(self: Self) -> str:
        """Return the stage name."""
        return "Calibration Profile Loading"

    def handle(self: Self, event: PipelineEvent) -> PipelineContext:
        """Handle the event and return the updated pipeline context."""
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
    """Plugin facade for loading calibration profiles."""

    def plugin_id(self: Self) -> str:
        """Return the plugin identifier."""
        return "calibration"

    def load_calibration(
        self: Self,
        calibration_dir: str | Path | None = None,
    ) -> CalibrationProfile:
        """Load and merge the calibration profile for the given directory."""
        if calibration_dir is not None:
            profile = discover_and_load_calibration(calibration_dir)
            if profile is not None:
                return profile
        return CalibrationProfile()


def create_calibration_metadata() -> PluginMetadata:
    """Create metadata for the calibration plugin."""
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
