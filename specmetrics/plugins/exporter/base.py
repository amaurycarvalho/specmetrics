"""Base classes and errors shared by all exporter plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import IO, Self

from pydantic import BaseModel

from specmetrics.kernel.cfm.model import EvidenceRef

from .models import ExportMetadata, Measurement


class ExportError(Exception):
    """Raised when an exporter fails to serialize or write its output."""

    def __init__(self: Self, message: str, format_id: str = "") -> None:
        """Initialize the error with a message and the affected format id."""
        self.format_id = format_id
        self.message = message
        super().__init__(message, format_id)


class ExporterConfig(BaseModel):
    """Configuration options shared by all exporter plugins."""

    indent: int = 2
    encoding: str = "utf-8"


class ExporterPlugin(ABC):
    """Base class that all export format plugins must implement."""

    @abstractmethod
    def format_id(self: Self) -> str:
        """Return the unique identifier for this export format."""
        ...

    @abstractmethod
    def file_extension(self: Self) -> str:
        """Return the file extension used for exported files."""
        ...

    @abstractmethod
    def content_type(self: Self) -> str:
        """Return the MIME content type for this export format."""
        ...

    @classmethod
    def config_schema(cls: type[Self]) -> type[BaseModel]:
        """Return the configuration model class for this exporter."""
        return ExporterConfig

    @abstractmethod
    def export(
        self: Self,
        measurements: list[Measurement],
        evidence_refs: list[EvidenceRef],
        metadata: ExportMetadata,
        output: IO,
    ) -> None:
        """Write the measurements and evidence refs to the given output."""
        ...
