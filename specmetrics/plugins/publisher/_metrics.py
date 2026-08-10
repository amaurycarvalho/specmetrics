"""Internal conversion of measurements into metric dictionaries."""

from __future__ import annotations

import time
from typing import Any

from specmetrics.plugins.exporter.models import ExportMetadata, Measurement


def build_evidence_refs(measurements: list[Measurement]) -> list[dict[str, str]]:
    """Build deduplicated evidence reference dictionaries for the measurements."""
    refs: list[dict[str, str]] = []
    seen: set[str] = set()
    for m in measurements:
        for ref in m.evidence:
            key = f"{ref.document_id}|{ref.section_id or ''}|{ref.graph_node_id or ''}"
            if key not in seen:
                seen.add(key)
                refs.append(
                    {
                        "spec_document": ref.document_id,
                        "spec_section": ref.section_id or "",
                        "spec_element_id": ref.graph_node_id or "",
                        "extracted_text": ref.text or "",
                    }
                )
    return refs


def convert_measurements(
    measurements: list[Measurement],
    metadata: ExportMetadata,
) -> list[dict[str, Any]]:
    """Convert measurements and metadata into a list of metric dictionaries."""
    metrics: list[dict[str, Any]] = []
    evidence_refs = build_evidence_refs(measurements)
    base_attrs = {
        "service.name": "specmetrics",
        "project_name": metadata.run_id or "unknown",
        "run_id": metadata.run_id or "",
        "specification_version": metadata.specmetrics_version or "",
    }

    total_fp = sum(m.functional_size for m in measurements)
    metrics.append(
        {
            "name": "specmetrics.function_points.total",
            "value": total_fp,
            "unit": "{function_points}",
            "description": "Total unadjusted function point count",
            "timestamp": time.time(),
            "attributes": {**base_attrs, "metric.type": "function_points_total"},
            "evidence_refs": evidence_refs,
        }
    )

    metrics.append(
        {
            "name": "specmetrics.functions.count",
            "value": len(measurements),
            "unit": "{functions}",
            "description": "Total number of identified functions",
            "timestamp": time.time(),
            "attributes": {**base_attrs, "metric.type": "functions_count"},
            "evidence_refs": evidence_refs,
        }
    )

    by_type: dict[str, int] = {}
    by_complexity: dict[str, int] = {}
    type_measurements: dict[str, list[Measurement]] = {}
    complexity_measurements: dict[str, list[Measurement]] = {}
    for m in measurements:
        cat = m.category or "unknown"
        by_type[cat] = by_type.get(cat, 0) + 1
        type_measurements.setdefault(cat, []).append(m)
        comp = m.complexity or "unknown"
        by_complexity[comp] = by_complexity.get(comp, 0) + 1
        complexity_measurements.setdefault(comp, []).append(m)

    for ftype, count in by_type.items():
        type_refs = build_evidence_refs(type_measurements[ftype])
        metrics.append(
            {
                "name": "specmetrics.functions.by_type",
                "value": count,
                "unit": "{functions}",
                "description": f"Function count for type {ftype}",
                "timestamp": time.time(),
                "attributes": {
                    **base_attrs,
                    "type": ftype,
                    "metric.type": "functions_by_type",
                },
                "evidence_refs": type_refs,
            }
        )

    for comp, count in by_complexity.items():
        comp_refs = build_evidence_refs(complexity_measurements[comp])
        metrics.append(
            {
                "name": "specmetrics.functions.by_complexity",
                "value": count,
                "unit": "{functions}",
                "description": f"Function count for complexity {comp}",
                "timestamp": time.time(),
                "attributes": {
                    **base_attrs,
                    "complexity": comp,
                    "metric.type": "functions_by_complexity",
                },
                "evidence_refs": comp_refs,
            }
        )

    return metrics