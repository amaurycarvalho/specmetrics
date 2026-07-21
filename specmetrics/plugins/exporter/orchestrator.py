from __future__ import annotations

import csv
import io
import xml.etree.ElementTree as ET
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


def _ensure_list(data: list | dict) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def _flatten_items(items: list[dict], keys: list[str]) -> list[list]:
    rows: list[list] = []
    for item in items:
        row = [str(item.get(k, "")) for k in keys]
        rows.append(row)
    return rows


def normalize_discover_stage(stage_data: list | dict) -> str:
    entries = _ensure_list(stage_data)
    rows = _flatten_items(entries, ["name", "count", "count_type", "duration_ms"])
    entities_rows = _flatten_items(
        [e for entry in entries for e in entry.get("entities", [])],
        ["document_name", "relative_path"],
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "count", "count_type", "duration_ms"])
    writer.writerows(rows)
    writer.writerow([])
    writer.writerow(["document_name", "relative_path"])
    writer.writerows(entities_rows)
    return output.getvalue()


def normalize_measure_stage(stage_data: list | dict) -> str:
    entries = _ensure_list(stage_data)
    rows = _flatten_items(entries, ["name", "count", "count_type", "duration_ms"])
    entities: list[dict] = [e for entry in entries for e in entry.get("entities", [])]
    entity_rows = _flatten_items(entities, ["metric", "total", "status", "duration_ms"])
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "count", "count_type", "duration_ms"])
    writer.writerows(rows)
    writer.writerow([])
    writer.writerow(["metric", "total", "status", "duration_ms"])
    writer.writerows(entity_rows)
    return output.getvalue()


def normalize_items_stage(stage_data: list | dict) -> str:
    entries = _ensure_list(stage_data)
    rows = _flatten_items(entries, ["name", "count", "count_type", "duration_ms"])
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "count", "count_type", "duration_ms"])
    writer.writerows(rows)
    return output.getvalue()


def stage_to_csv(stage_name: str, stage_data: list | dict) -> str:
    if stage_name == "discover":
        return normalize_discover_stage(stage_data)
    if stage_name == "measure":
        return normalize_measure_stage(stage_data)
    return normalize_items_stage(stage_data)


def _dict_to_xml(parent: ET.Element, data: dict) -> None:
    for key, value in data.items():
        child = ET.SubElement(parent, str(key))
        if isinstance(value, dict):
            _dict_to_xml(child, value)
        else:
            child.text = str(value) if value is not None else ""


def stage_to_xml(stage_name: str, stage_data: list | dict) -> str:
    root = ET.Element("stage", name=stage_name)
    entries = _ensure_list(stage_data)
    for entry in entries:
        item = ET.SubElement(root, "entry")
        _dict_to_xml(item, entry)
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


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
            export_timestamp=cfm.metadata.created_at,
            function_count=len(measurements),
            pipeline_duration_ms=cfm.metadata.build_duration_ms,
        )

        selected = [
            e for e in self.exporters if formats is None or e.format_id() in formats
        ]
        results: list[dict] = []

        for exporter in selected:
            fmt_id = exporter.format_id()
            try:
                if len(measurements) > BATCH_SIZE:
                    paths: list[str] = []
                    for batch_idx, batch in enumerate(_batched(measurements)):
                        path = (
                            output_dir
                            / f"measurements_{batch_idx}{exporter.file_extension()}"
                        )
                        with open(path, "w", encoding="utf-8") as f:
                            exporter.export(batch, evidence_refs, metadata, f)
                        paths.append(str(path))
                    results.append(
                        {"format": fmt_id, "paths": paths, "status": "completed"}
                    )
                    logger.info(
                        "Export completed (batched)",
                        format=fmt_id,
                        batches=len(paths),
                        count=len(measurements),
                    )
                else:
                    path = output_dir / f"measurements{exporter.file_extension()}"
                    if path.exists():
                        logger.warning("Overwriting existing file", path=str(path))
                    with open(path, "w", encoding="utf-8") as f:
                        exporter.export(measurements, evidence_refs, metadata, f)
                    results.append(
                        {"format": fmt_id, "path": str(path), "status": "completed"}
                    )
                    logger.info(
                        "Export completed",
                        format=fmt_id,
                        path=str(path),
                        count=len(measurements),
                    )
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
            export_timestamp=cfm.metadata.created_at,
            function_count=len(measurements),
            pipeline_duration_ms=cfm.metadata.build_duration_ms,
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
