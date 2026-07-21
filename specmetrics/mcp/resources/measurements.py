from __future__ import annotations

import json

from mcp.types import ResourceTemplate

from specmetrics.mcp.server import ToolError

_measurement_store: dict[str, dict] = {}
_evidence_store: dict[str, dict] = {}


def store_measurement(run_id: str, data: dict) -> None:
    _measurement_store[run_id] = data


def store_evidence(run_id: str, data: dict) -> None:
    _evidence_store[run_id] = data


MEASUREMENT_RESOURCE_TEMPLATE = ResourceTemplate(
    uriTemplate="specmetrics://measurement/{run_id}",
    name="Measurement Results",
    description="Access measurement results by run ID",
    mimeType="application/json",
)


EVIDENCE_RESOURCE_TEMPLATE = ResourceTemplate(
    uriTemplate="specmetrics://evidence/{run_id}",
    name="Evidence Graph",
    description="Access evidence graph data for a measurement run",
    mimeType="application/json",
)


EXPORT_RESOURCE_TEMPLATE = ResourceTemplate(
    uriTemplate="specmetrics://export/{run_id}/{format}",
    name="Export Artifact",
    description="Access exported measurement results by run ID and format",
    mimeType="text/plain",
)


def handle_measurement_resource(uri: str) -> str:
    run_id = uri.replace("specmetrics://measurement/", "", 1)
    data = _measurement_store.get(run_id)
    if data is None:
        raise ToolError(-32601, f"Measurement not found for run: {run_id}")
    return json.dumps(data, indent=2)


def handle_evidence_resource(uri: str) -> str:
    run_id = uri.replace("specmetrics://evidence/", "", 1)
    data = _evidence_store.get(run_id)
    if data is None:
        raise ToolError(-32601, f"Evidence data not found for run: {run_id}")
    return json.dumps(data, indent=2)


def handle_export_resource(uri: str) -> str:
    remainder = uri.replace("specmetrics://export/", "", 1)
    parts = remainder.split("/", 1)
    if len(parts) != 2:
        raise ToolError(-32601, f"Invalid export URI: {uri}")

    run_id, fmt = parts
    data = _measurement_store.get(run_id)
    if data is None:
        raise ToolError(-32601, f"Export data not found for run: {run_id}")

    if fmt == "json":
        return json.dumps(data, indent=2)
    elif fmt == "csv":
        lines = ["metric,value,unit"]
        if "measurement" in data:
            m = data["measurement"]
            fp = m.get("fpa_total_function_points") or m.get(
                "total_function_points", ""
            )
            lines.append(f"total_function_points,{fp},function_points")
        return "\n".join(lines)
    else:
        raise ToolError(-32602, f"Unsupported export format: {fmt}")
