"""XML exporter plugin for writing measurements as structured XML."""

from __future__ import annotations

from typing import IO, Self
from xml.etree.ElementTree import Element, SubElement, tostring

from specmetrics.kernel.cfm.model import EvidenceRef

from .base import ExporterPlugin, ExportError
from .models import ExportMetadata, Measurement


class XmlExporter(ExporterPlugin):
    """Exporter that serializes measurements to XML format."""

    def format_id(self: Self) -> str:
        """Return the unique identifier for this export format."""
        return "xml"

    def file_extension(self: Self) -> str:
        """Return the file extension used for exported files."""
        return ".xml"

    def content_type(self: Self) -> str:
        """Return the MIME content type for this export format."""
        return "application/xml"

    def export(
        self: Self,
        measurements: list[Measurement],
        evidence_refs: list[EvidenceRef],
        metadata: ExportMetadata,
        output: IO,
    ) -> None:
        """Write the measurements to ``output`` as an XML document."""
        try:
            root = Element("specmetrics-export")
            self._write_metadata(root, metadata)
            self._write_measurements(root, measurements)
            self._write_evidence_refs(root, evidence_refs)
            output.write(tostring(root, encoding="unicode", xml_declaration=True))
        except (OSError, ValueError) as e:
            raise ExportError(str(e), format_id="xml") from e

    def _write_metadata(
        self: Self, root: Element, metadata: ExportMetadata
    ) -> None:
        meta_el = SubElement(root, "metadata")
        if metadata.run_id:
            SubElement(meta_el, "run-id").text = metadata.run_id
        if metadata.specmetrics_version:
            SubElement(
                meta_el, "specmetrics-version"
            ).text = metadata.specmetrics_version
        SubElement(meta_el, "function-count").text = str(metadata.function_count)
        if metadata.export_timestamp:
            SubElement(
                meta_el, "export-timestamp"
            ).text = metadata.export_timestamp.isoformat()

    def _write_measurements(
        self: Self, root: Element, measurements: list[Measurement]
    ) -> None:
        measurements_el = SubElement(root, "measurements")
        for m in measurements:
            m_el = SubElement(measurements_el, "measurement")
            SubElement(m_el, "function-id").text = m.function_id
            SubElement(m_el, "function-name").text = m.function_name
            if m.category:
                SubElement(m_el, "category").text = m.category
            if m.complexity:
                SubElement(m_el, "complexity").text = m.complexity
            SubElement(m_el, "functional-size").text = str(m.functional_size)

            evidence_el = SubElement(m_el, "evidence")
            for e in m.evidence:
                e_el = SubElement(evidence_el, "evidence-ref")
                SubElement(e_el, "document-id").text = e.document_id
                if e.section_id:
                    SubElement(e_el, "section-id").text = e.section_id
                SubElement(e_el, "text").text = e.text[:200]

    def _write_evidence_refs(
        self: Self, root: Element, evidence_refs: list[EvidenceRef]
    ) -> None:
        evidence_el = SubElement(root, "evidence-refs")
        for r in evidence_refs:
            r_el = SubElement(evidence_el, "ref")
            SubElement(r_el, "document-id").text = r.document_id
            if r.section_id:
                SubElement(r_el, "section-id").text = r.section_id
            SubElement(r_el, "text").text = r.text[:200]
