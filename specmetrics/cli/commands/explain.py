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
from specmetrics.kernel.explanation.loader import load_cfm, load_evidence_graph
from specmetrics.kernel.explanation.service import ExplainService

logger = structlog.get_logger(__name__)

explain_cli = typer.Typer(
    name="explain",
    help="Explain measurement results with evidence traces and rule effects",
)


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
        cfm = load_cfm(run_dir)
        graph = load_evidence_graph(run_dir)

    spec_path_arg = str(run_dir / "spec.md") if run_dir else None

    try:
        if compare:
            _ = service.explain(compare, cfm=cfm, graph=graph, spec_path=spec_path_arg)
            explanation = service.explain(
                run_id,
                metric_name=metric,
                cfm=cfm,
                graph=graph,
                spec_path=spec_path_arg,
            )
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
            explanation = service.explain(
                run_id,
                metric_name=metric,
                cfm=cfm,
                graph=graph,
                spec_path=spec_path_arg,
            )
            if format == "json":
                typer.echo(json_format_explanation(explanation))
            else:
                typer.echo(text_format_explanation(explanation))
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(code=2)
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        logger.error("explain_command_failed", error=str(exc))
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
