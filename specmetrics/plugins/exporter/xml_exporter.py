from __future__ import annotations

from typing import IO
from xml.etree.ElementTree import Element, SubElement, tostring

from specmetrics.kernel.cfm.model import EvidenceRef

from .base import ExporterPlugin, ExportError
from .models import ExportMetadata, Measurement


class XmlExporter(ExporterPlugin):
    def format_id(self) -> str:
        return "xml"

    def file_extension(self) -> str:
        return ".xml"

    def content_type(self) -> str:
        return "application/xml"

    def export(
        self,
        measurements: list[Measurement],
        evidence_refs: list[EvidenceRef],
        metadata: ExportMetadata,
        output: IO,
    ) -> None:
        try:
            root = Element("specmetrics-export")
            meta_el = SubElement(root, "metadata")
            if metadata.run_id:
                SubElement(meta_el, "run-id").text = metadata.run_id
            if metadata.specmetrics_version:
                SubElement(meta_el, "specmetrics-version").text = metadata.specmetrics_version
            SubElement(meta_el, "function-count").text = str(metadata.function_count)
            if metadata.export_timestamp:
                SubElement(meta_el, "export-timestamp").text = metadata.export_timestamp.isoformat()

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

            evidence_el = SubElement(root, "evidence-refs")
            for r in evidence_refs:
                r_el = SubElement(evidence_el, "ref")
                SubElement(r_el, "document-id").text = r.document_id
                if r.section_id:
                    SubElement(r_el, "section-id").text = r.section_id
                SubElement(r_el, "text").text = r.text[:200]

            output.write(tostring(root, encoding="unicode", xml_declaration=True))
        except (OSError, ValueError) as e:
            raise ExportError(str(e), format_id="xml") from e
