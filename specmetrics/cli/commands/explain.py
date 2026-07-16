from __future__ import annotations

import json
from pathlib import Path

import structlog
import typer

from specmetrics.kernel.explanation.formatters.json import (
    format_comparison as json_format_comparison,
)
from specmetrics.kernel.explanation.formatters.json import (
    format_explanation as json_format_explanation,
)
from specmetrics.kernel.explanation.formatters.text import (
    format_comparison as text_format_comparison,
)
from specmetrics.kernel.explanation.formatters.text import (
    format_explanation as text_format_explanation,
)
from specmetrics.kernel.explanation.service import ExplainService

logger = structlog.get_logger(__name__)

explain_cli = typer.Typer(
    name="explain",
    help="Explain measurement results with evidence traces and rule effects",
)


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


@explain_cli.command()
def explain(
    run_id: str = typer.Argument(
        ...,
        help="Identifier of the measurement run to explain",
    ),
    metric: str | None = typer.Option(
        None,
        "--metric",
        help="Specific metric to explain (e.g., functional_size)",
    ),
    format: str = typer.Option(
        "text",
        "--format",
        help="Output format: text or json",
    ),
    compare: str | None = typer.Option(
        None,
        "--compare",
        help="Compare with another run ID",
    ),
    run_dir: Path | None = typer.Option(
        None,
        "--run-dir",
        help="Directory containing measurement run artifacts",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    service = ExplainService()

    cfm = None
    graph = None

    if run_dir is not None:
        cfm = _load_cfm(run_dir)
        graph = _load_evidence_graph(run_dir)

    try:
        if compare:
            _ = service.explain(compare, cfm=cfm, graph=graph)
            explanation = service.explain(run_id, metric_name=metric, cfm=cfm, graph=graph)
            comparison = service.compare(compare, run_id)

            if format == "json":
                combined = {
                    "explanation": json.loads(json_format_explanation(explanation)),
                    "comparison": json.loads(json_format_comparison(comparison)),
                }
                typer.echo(json.dumps(combined, indent=2, default=str))
            else:
                typer.echo(text_format_explanation(explanation))
                typer.echo("")
                typer.echo(text_format_comparison(comparison))
        else:
            explanation = service.explain(run_id, metric_name=metric, cfm=cfm, graph=graph)
            if format == "json":
                typer.echo(json_format_explanation(explanation))
            else:
                typer.echo(text_format_explanation(explanation))
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        logger.error("explain_command_failed", error=str(exc))
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
