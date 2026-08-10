"""Exception hierarchy for the SpecMetrics kernel."""

from __future__ import annotations

from typing import Self


class PipelineError(Exception):
    """Base class for all pipeline errors."""


class PluginError(PipelineError):
    """Raised when a plugin fails to initialize or execute."""

    def __init__(self: Self, plugin_id: str, message: str) -> None:
        """Initialize the error with the failing plugin ID and message."""
        super().__init__(plugin_id, message)
        self.plugin_id = plugin_id
        self.message = message


class StageError(PipelineError):
    """Raised when a pipeline stage fails to execute."""

    def __init__(self: Self, stage_name: str, message: str) -> None:
        """Initialize the error with the failing stage name and message."""
        super().__init__(stage_name, message)
        self.stage_name = stage_name
        self.message = message


class HandlerNotFoundError(PipelineError):
    """Raised when no handler is registered for an event type."""

    def __init__(self: Self, event_type: str) -> None:
        """Initialize the error with the unhandled event type."""
        super().__init__(f"No handler registered for event type: {event_type}")
        self.event_type = event_type
