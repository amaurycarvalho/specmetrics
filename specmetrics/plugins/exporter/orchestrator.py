from __future__ import annotations

from pathlib import Path
from typing import IO, Optional

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel, EvidenceRef

from .base import ExportError, ExporterPlugin
from .models import ExportMetadata, Measurement

logger = structlog.get_logger(__name__)


def _extract_measurements(cfm: CanonicalFunctionalModel) -> list[Measurement]:
    measurements: list[Measurement] = []
    for proc in cfm.functional_processes.values():
        measurements.append(
            Measurement(
                function_id=proc.id,
                function_name=proc.name,
                category="functional_process",
                complexity="",
                functional_size=0.0,
                evidence=[proc.evidence],
                attributes=proc.metadata,
            )
        )
    return measurements


def _extract_evidence(cfm: CanonicalFunctionalModel) -> list[EvidenceRef]:
    refs: list[EvidenceRef] = []
    seen: set[str] = set()
    for proc in cfm.functional_processes.values():
        key = f"{proc.evidence.document_id}:{proc.evidence.text}"
        if key not in seen:
            refs.append(proc.evidence)
            seen.add(key)
    return refs


BATCH_SIZE = 5000


def _batched(items: list, size: int = BATCH_SIZE):
    for i in range(0, len(items), size):
        yield items[i : i + size]


class ExportOrchestrator:
    def __init__(self, exporters: list[ExporterPlugin]) -> None:
        self.exporters = exporters

    def export_to_dir(
        self,
        cfm: CanonicalFunctionalModel,
        output_dir: Path,
        formats: Optional[list[str]] = None,
    ) -> list[dict]:
        measurements = _extract_measurements(cfm)
        evidence_refs = _extract_evidence(cfm)
        metadata = ExportMetadata(
            specmetrics_version=self._get_version(),
            run_id=cfm.run_id,
            export_timestamp=cfm.metadata.build_date if hasattr(cfm.metadata, "build_date") else None,
            function_count=len(measurements),
        )

        selected = [e for e in self.exporters if formats is None or e.format_id() in formats]
        results: list[dict] = []

        for exporter in selected:
            fmt_id = exporter.format_id()
            try:
                if len(measurements) > BATCH_SIZE:
                    paths: list[str] = []
                    for batch_idx, batch in enumerate(_batched(measurements)):
                        path = output_dir / f"measurements_{batch_idx}{exporter.file_extension()}"
                        with open(path, "w", encoding="utf-8") as f:
                            exporter.export(batch, evidence_refs, metadata, f)
                        paths.append(str(path))
                    results.append({"format": fmt_id, "paths": paths, "status": "completed"})
                    logger.info("Export completed (batched)", format=fmt_id, batches=len(paths), count=len(measurements))
                else:
                    path = output_dir / f"measurements{exporter.file_extension()}"
                    if path.exists():
                        logger.warning("Overwriting existing file", path=str(path))
                    with open(path, "w", encoding="utf-8") as f:
                        exporter.export(measurements, evidence_refs, metadata, f)
                    results.append({"format": fmt_id, "path": str(path), "status": "completed"})
                    logger.info("Export completed", format=fmt_id, path=str(path), count=len(measurements))
            except ExportError as e:
                logger.warning("Export failed for format", format=fmt_id, error=str(e))
                results.append({"format": fmt_id, "status": "failed", "error": str(e)})
            except Exception as e:
                logger.error("Unexpected export error", format=fmt_id, error=str(e))
                results.append({"format": fmt_id, "status": "error", "error": str(e)})

        return results

    def export_to_stream(
        self,
        cfm: CanonicalFunctionalModel,
        output: IO,
        fmt: str = "json",
    ) -> None:
        measurements = _extract_measurements(cfm)
        evidence_refs = _extract_evidence(cfm)
        metadata = ExportMetadata(
            specmetrics_version=self._get_version(),
            run_id=cfm.run_id,
            export_timestamp=None,
            function_count=len(measurements),
        )
        exporters = {e.format_id(): e for e in self.exporters}
        exporter = exporters.get(fmt)
        if exporter is None:
            raise ExportError(f"Unknown export format: {fmt}", format_id=fmt)
        exporter.export(measurements, evidence_refs, metadata, output)

    def _get_version(self) -> str:
        try:
            from importlib.metadata import version as _v
            return _v("specmetrics")
        except Exception:
            return "0.1.0"
