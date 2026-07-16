from __future__ import annotations

import json
from pathlib import Path

from mcp.types import TextContent, Tool

from specmetrics.kernel.explanation.formatters.json import (
    format_comparison,
    format_explanation,
)
from specmetrics.kernel.explanation.service import ExplainService


def _load_cfm(run_dir: Path):
    cfm_path = run_dir / "canonical_model.json"
    if not cfm_path.exists():
        return None
    from specmetrics.kernel.cfm.model import CanonicalFunctionalModel

    with open(cfm_path) as f:
        data = json.load(f)
    return CanonicalFunctionalModel.model_validate(data)


def _load_evidence_graph(run_dir: Path):
    graph_path = run_dir / "evidence_graph.json"
    if not graph_path.exists():
        return None
    from specmetrics.kernel.evidence_graph import EvidenceGraph

    with open(graph_path) as f:
        data = json.load(f)
    return EvidenceGraph.model_validate(data)


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
    run_id = arguments["run_id"]
    metric = arguments.get("metric")
    compare = arguments.get("compare")
    run_dir_str = arguments.get("run_dir")

    service = ExplainService()
    cfm = None
    graph = None

    if run_dir_str:
        run_dir = Path(run_dir_str)
        cfm = _load_cfm(run_dir)
        graph = _load_evidence_graph(run_dir)

    try:
        explanation = service.explain(run_id, metric_name=metric, cfm=cfm, graph=graph)
        result = json.loads(format_explanation(explanation))

        if compare:
            _ = service.explain(compare, cfm=cfm, graph=graph)
            comparison = service.compare(compare, run_id)
            result["comparison"] = json.loads(format_comparison(comparison))

        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except ValueError as exc:
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]
    except Exception as exc:
        return [TextContent(type="text", text=json.dumps({"error": f"Explanation failed: {exc}"}))]


def handle_explain_compare(arguments: dict) -> list[TextContent]:
    baseline_run_id = arguments["baseline_run_id"]
    comparison_run_id = arguments["comparison_run_id"]
    run_dir_str = arguments.get("run_dir")

    service = ExplainService()
    cfm = None
    graph = None

    if run_dir_str:
        run_dir = Path(run_dir_str)
        cfm = _load_cfm(run_dir)
        graph = _load_evidence_graph(run_dir)

    try:
        _ = service.explain(baseline_run_id, cfm=cfm, graph=graph)
        _ = service.explain(comparison_run_id, cfm=cfm, graph=graph)
        comparison = service.compare(baseline_run_id, comparison_run_id)
        return [TextContent(type="text", text=format_comparison(comparison))]
    except ValueError as exc:
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]
    except Exception as exc:
        return [TextContent(type="text", text=json.dumps({"error": f"Comparison failed: {exc}"}))]
