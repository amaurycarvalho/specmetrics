"""MCP tool handlers for explaining measurement runs."""

from __future__ import annotations

import json
from pathlib import Path

from mcp.types import TextContent, Tool

from specmetrics.kernel.explanation.formatters.json import (
    format_comparison,
    format_explanation,
)
from specmetrics.kernel.explanation.loader import load_cfm, load_evidence_graph
from specmetrics.kernel.explanation.service import ExplainService

EXPLAIN_TOOL = Tool(
    name="explain_measurement",
    description="Generate an explanation for a completed measurement run, showing which specification elements contributed to each metric and what evidence supports them",
    inputSchema={
        "type": "object",
        "properties": {
            "run_id": {
                "type": "string",
                "description": "Identifier of the measurement run to explain",
            },
            "metric": {
                "type": "string",
                "description": "Optional metric name to filter (e.g., function_count)",
            },
            "compare": {
                "type": "string",
                "description": "Optional baseline run ID to compare against",
            },
            "run_dir": {
                "type": "string",
                "description": "Path to directory containing measurement run artifacts",
            },
        },
        "required": ["run_id"],
    },
)


EXPLAIN_COMPARE_TOOL = Tool(
    name="explain_compare",
    description="Compare explanations between two measurement runs",
    inputSchema={
        "type": "object",
        "properties": {
            "baseline_run_id": {
                "type": "string",
                "description": "Baseline measurement run ID",
            },
            "comparison_run_id": {
                "type": "string",
                "description": "Comparison measurement run ID",
            },
            "run_dir": {
                "type": "string",
                "description": "Path to directory containing measurement run artifacts",
            },
        },
        "required": ["baseline_run_id", "comparison_run_id"],
    },
)


def handle_explain_measurement(arguments: dict) -> list[TextContent]:
    """Explain a measurement run and return the result as text content."""
    run_id = arguments["run_id"]
    metric = arguments.get("metric")
    compare = arguments.get("compare")
    run_dir_str = arguments.get("run_dir")

    service = ExplainService()
    cfm = None
    graph = None

    if run_dir_str:
        run_dir = Path(run_dir_str)
        cfm = load_cfm(run_dir)
        graph = load_evidence_graph(run_dir)

    spec_path_arg = str(run_dir / "spec.md") if run_dir_str else None

    try:
        explanation = service.explain(
            run_id, metric_name=metric, cfm=cfm, graph=graph, spec_path=spec_path_arg
        )
        result = json.loads(format_explanation(explanation))

        if compare:
            _ = service.explain(compare, cfm=cfm, graph=graph, spec_path=spec_path_arg)
            comparison = service.compare(compare, run_id)
            result["comparison"] = json.loads(format_comparison(comparison))

        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except ValueError as exc:
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]
    except Exception as exc:
        return [
            TextContent(
                type="text", text=json.dumps({"error": f"Explanation failed: {exc}"})
            )
        ]


def handle_explain_compare(arguments: dict) -> list[TextContent]:
    """Compare explanations between two measurement runs."""
    baseline_run_id = arguments["baseline_run_id"]
    comparison_run_id = arguments["comparison_run_id"]
    run_dir_str = arguments.get("run_dir")

    service = ExplainService()
    cfm = None
    graph = None

    if run_dir_str:
        run_dir = Path(run_dir_str)
        cfm = load_cfm(run_dir)
        graph = load_evidence_graph(run_dir)

    spec_path_arg = str(run_dir / "spec.md") if run_dir_str else None

    try:
        _ = service.explain(
            baseline_run_id, cfm=cfm, graph=graph, spec_path=spec_path_arg
        )
        _ = service.explain(
            comparison_run_id, cfm=cfm, graph=graph, spec_path=spec_path_arg
        )
        comparison = service.compare(baseline_run_id, comparison_run_id)
        return [TextContent(type="text", text=format_comparison(comparison))]
    except ValueError as exc:
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]
    except Exception as exc:
        return [
            TextContent(
                type="text", text=json.dumps({"error": f"Comparison failed: {exc}"})
            )
        ]
