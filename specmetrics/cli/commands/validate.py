from __future__ import annotations

import json
from pathlib import Path

import typer

from specmetrics.kernel.validation.pipeline import ValidationPipeline

validate_cli = typer.Typer(
    name="validate",
    help="Validate specification documents for correctness and compliance",
)


def _format_text_report(report_json: dict) -> str:
    lines: list[str] = []
    for doc in report_json.get("documents", []):
        passed = doc.get("passed", False)
        symbol = "\u2713" if passed else "\u2717"
        path = doc.get("path", "?")
        s = doc.get("summary", {})
        lines.append(
            f"  {symbol} {path} \u2014 {s.get('passed', 0)}/{s.get('total', 0)} rules passed"
        )
        for r in doc.get("results", []):
            if not r.get("passed", True):
                flag = "WARN" if r.get("severity") == "WARNING" else "FAIL"
                lines.append(
                    f"    {flag}: {r.get('rule_name', '?')} \u2014 {r.get('message', '')}"
                )
    return "\n".join(lines)


@validate_cli.command()
def validate(
    spec_paths: list[Path] = typer.Argument(
        ...,
        help="Path(s) to specification file(s) or directory(ies)",
        exists=False,
        file_okay=True,
        dir_okay=True,
        resolve_path=True,
    ),
    rules: Path | None = typer.Option(
        None,
        "--rules",
        help="Path to custom validation rules configuration",
        exists=False,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    format: str = typer.Option(
        "text",
        "--format",
        help="Output format: text, json, quiet",
    ),
    batch: bool = typer.Option(
        False,
        "--batch",
        help="Treat paths as a batch",
    ),
    constitution_only: bool = typer.Option(
        False,
        "--constitution-only",
        help="Only run constitutional compliance checks",
    ),
    structural_only: bool = typer.Option(
        False,
        "--structural-only",
        help="Only run structural checks",
    ),
) -> None:
    pipeline = ValidationPipeline()

    if rules is not None:
        pipeline.load_rules(rules)

    mode = "all"
    if constitution_only:
        mode = "constitutional"
    elif structural_only:
        mode = "structural"

    spec_files = pipeline.find_spec_files(spec_paths)
    if not spec_files:
        typer.echo("No specification files found")
        raise typer.Exit(code=0)

    do_batch = batch or len(spec_files) > 1

    if do_batch:
        report = pipeline.run_batch(spec_files, mode=mode)
        report_json = report.model_dump() if hasattr(report, "model_dump") else {}
    else:
        single = pipeline.run(spec_files[0], mode=mode)
        report_json = {
            "version": "1.0",
            "overall_passed": single.overall_passed,
            "documents": [single.model_dump() if hasattr(single, "model_dump") else {}],
            "summary": {
                "total_documents": 1,
                "passed_documents": 1 if single.overall_passed else 0,
                "failed_documents": 0 if single.overall_passed else 1,
                "total_rules": single.summary.total_rules
                if hasattr(single, "summary")
                else 0,
                "total_passed": single.summary.passed
                if hasattr(single, "summary")
                else 0,
                "total_failed": single.summary.failed
                if hasattr(single, "summary")
                else 0,
                "duration_ms": single.summary.duration_ms
                if hasattr(single, "summary")
                else 0,
            },
        }

    overall_pass = report_json.get(
        "overall_passed", report_json.get("summary", {}).get("failed_documents", 0) == 0
    )
    if isinstance(overall_pass, int):
        overall_pass = overall_pass == 0

    if format == "json":
        typer.echo(json.dumps(report_json, indent=2, default=str))
    elif format == "quiet":
        pass
    else:
        typer.echo(_format_text_report(report_json))

    if not overall_pass:
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)
