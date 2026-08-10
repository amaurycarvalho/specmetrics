"""CSV exporter plugin for writing measurements as comma-separated values."""

from __future__ import annotations

import csv
from typing import IO, Self

from specmetrics.kernel.cfm.model import EvidenceRef

from .base import ExporterPlugin, ExportError
from .models import ExportMetadata, Measurement


class CsvExporter(ExporterPlugin):
    """Exporter that serializes measurements to CSV format."""

    def format_id(self: Self) -> str:
        """Return the unique identifier for this export format."""
        return "csv"

    def file_extension(self: Self) -> str:
        """Return the file extension used for exported files."""
        return ".csv"

    def content_type(self: Self) -> str:
        """Return the MIME content type for this export format."""
        return "text/csv"

    def export(
        self: Self,
        measurements: list[Measurement],
        evidence_refs: list[EvidenceRef],
        metadata: ExportMetadata,
        output: IO,
    ) -> None:
        """Write the measurements to ``output`` as CSV rows."""
        try:
            fieldnames = [
                "function_id",
                "function_name",
                "category",
                "complexity",
                "functional_size",
                "evidence_document_id",
                "evidence_text",
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for m in measurements:
                evidence_str = "; ".join(
                    f"{e.document_id}: {e.text[:100]}" for e in m.evidence
                )
                writer.writerow(
                    {
                        "function_id": m.function_id,
                        "function_name": m.function_name,
                        "category": m.category,
                        "complexity": m.complexity,
                        "functional_size": m.functional_size,
                        "evidence_document_id": m.evidence[0].document_id
                        if m.evidence
                        else "",
                        "evidence_text": evidence_str,
                    }
                )
        except (OSError, csv.Error) as e:
            raise ExportError(str(e), format_id="csv") from e
