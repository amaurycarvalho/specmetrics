from __future__ import annotations

import json
from typing import IO

from specmetrics.kernel.cfm.model import EvidenceRef

from .base import ExporterPlugin, ExportError
from .models import ExportMetadata, Measurement


class JsonExporter(ExporterPlugin):
    def format_id(self) -> str:
        return "json"

    def file_extension(self) -> str:
        return ".json"

    def content_type(self) -> str:
        return "application/json"

    def export(
        self,
        measurements: list[Measurement],
        evidence_refs: list[EvidenceRef],
        metadata: ExportMetadata,
        output: IO,
    ) -> None:
        try:
            data = {
                "metadata": metadata.model_dump(mode="json"),
                "measurements": [
                    {
                        "function_id": m.function_id,
                        "function_name": m.function_name,
                        "category": m.category,
                        "complexity": m.complexity,
                        "functional_size": m.functional_size,
                        "evidence": [e.model_dump(mode="json") for e in m.evidence],
                        "attributes": m.attributes,
                    }
                    for m in measurements
                ],
                "evidence_refs": [r.model_dump(mode="json") for r in evidence_refs],
            }
            output.write(json.dumps(data, indent=2, default=str))
        except (OSError, TypeError) as e:
            raise ExportError(str(e), format_id="json") from e
