"""CLI command for explaining measurement results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import structlog
import typer

if TYPE_CHECKING:
    from typing import Any

logger = structlog.get_logger(__name__)

explain_cli = typer.Typer(
    name="explain",
    help="Explain measurement results with evidence traces and rule effects",
)


def _load_explanation() -> dict[str, Any]:
    """Import the explanation module lazily to keep ``cli.app`` cheap."""
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
    from specmetrics.kernel.explanation.loader import (
        load_cfm,
        load_evidence_graph,
    )
    from specmetrics.kernel.explanation.service import ExplainService

    return {
        "json": (json_format_explanation, json_format_comparison),
        "text": (text_format_explanation, text_format_comparison),
        "loader": (load_cfm, load_evidence_graph),
        "service": ExplainService,
    }


@explain_cli.command()
def explain(
    run_id: Annotated[
        str,
        typer.Argument(
            help="Identifier of the measurement run to explain",
        ),
    ],
    metric: Annotated[
        str | None,
        typer.Option(
            "--metric",
            help="Specific metric to explain (e.g., functional_size)",
        ),
    ] = None,
    format: Annotated[
        str,
        typer.Option(
            "--format",
            help="Output format: text or json",
        ),
    ] = "text",
    compare: Annotated[
        str | None,
        typer.Option(
            "--compare",
            help="Compare with another run ID",
        ),
    ] = None,
    run_dir: Annotated[
        Path | None,
        typer.Option(
            "--run-dir",
            help="Directory containing measurement run artifacts",
            exists=False,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = None,
) -> None:
    """Explain a measurement run with evidence traces and rule effects."""
    deps = _load_explanation()
    json_format_explanation, json_format_comparison = deps["json"]
    text_format_explanation, text_format_comparison = deps["text"]
    load_cfm, load_evidence_graph = deps["loader"]
    ExplainService = deps["service"]

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
