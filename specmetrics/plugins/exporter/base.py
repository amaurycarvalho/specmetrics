from __future__ import annotations

from abc import ABC, abstractmethod
from typing import IO

from pydantic import BaseModel

from specmetrics.kernel.cfm.model import EvidenceRef

from .models import ExportMetadata, Measurement


class ExportError(Exception):
    def __init__(self, message: str, format_id: str = ""):
        self.format_id = format_id
        self.message = message
        super().__init__(f"[{format_id}] {message}")


class ExporterConfig(BaseModel):
    indent: int = 2
    encoding: str = "utf-8"


class ExporterPlugin(ABC):
    @abstractmethod
    def format_id(self) -> str:
        ...

    @abstractmethod
    def file_extension(self) -> str:
        ...

    @abstractmethod
    def content_type(self) -> str:
        ...

    @classmethod
    def config_schema(cls) -> type[BaseModel]:
        return ExporterConfig

    @abstractmethod
    def export(
        self,
        measurements: list[Measurement],
        evidence_refs: list[EvidenceRef],
        metadata: ExportMetadata,
        output: IO,
    ) -> None:
        ...
