"""CLI command for validating specification documents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

if TYPE_CHECKING:
    from specmetrics.kernel.validation.pipeline import ValidationPipeline

validate_cli = typer.Typer(
    name="validate",
    help="Validate specification documents for correctness and compliance",
)


def _load_validation_pipeline() -> type[ValidationPipeline]:
    """Import the validation pipeline lazily to keep ``cli.app`` cheap."""
    from specmetrics.kernel.validation.pipeline import ValidationPipeline

    return ValidationPipeline


def _format_text_report(report_json: dict) -> str:
    """Render a JSON validation report as human-readable text."""
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


def _resolve_mode(constitution_only: bool, structural_only: bool) -> str:
    """Resolve the validation mode from the CLI flags."""
    if constitution_only:
        return "constitutional"
    if structural_only:
        return "structural"
    return "all"


def _overall_pass(report_json: dict) -> bool:
    """Return whether the overall validation passed."""
    overall_pass = report_json.get(
        "overall_passed",
        report_json.get("summary", {}).get("failed_documents", 0) == 0,
    )
    if isinstance(overall_pass, int):
        return overall_pass == 0
    return bool(overall_pass)


def _build_report(
    pipeline: ValidationPipeline,
    spec_files: list[Path],
    mode: str,
    do_batch: bool,
) -> dict:
    """Run validation in batch or single mode and return a JSON report."""
    if do_batch:
        report = pipeline.run_batch(spec_files, mode=mode)
        return report.model_dump() if hasattr(report, "model_dump") else {}
    single = pipeline.run(spec_files[0], mode=mode)
    return {
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


def _emit_report(format: str, report_json: dict) -> None:
    """Render the report in the requested output format."""
    if format == "json":
        typer.echo(json.dumps(report_json, indent=2, default=str))
    elif format == "quiet":
        pass
    else:
        typer.echo(_format_text_report(report_json))


@validate_cli.command()
def validate(
    spec_paths: Annotated[
        list[Path],
        typer.Argument(
            help="Path(s) to specification file(s) or directory(ies)",
            exists=False,
            file_okay=True,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    rules: Annotated[
        Path | None,
        typer.Option(
            "--rules",
            help="Path to custom validation rules configuration",
            exists=False,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = None,
    format: Annotated[
        str,
        typer.Option(
            "--format",
            help="Output format: text, json, quiet",
        ),
    ] = "text",
    batch: Annotated[
        bool,
        typer.Option(
            "--batch",
            help="Treat paths as a batch",
        ),
    ] = False,
    constitution_only: Annotated[
        bool,
        typer.Option(
            "--constitution-only",
            help="Only run constitutional compliance checks",
        ),
    ] = False,
    structural_only: Annotated[
        bool,
        typer.Option(
            "--structural-only",
            help="Only run structural checks",
        ),
    ] = False,
) -> None:
    """Validate specification documents for correctness and compliance."""
    ValidationPipeline = _load_validation_pipeline()
    pipeline = ValidationPipeline()

    if rules is not None:
        pipeline.load_rules(rules)

    mode = _resolve_mode(constitution_only, structural_only)

    spec_files = pipeline.find_spec_files(spec_paths)
    if not spec_files:
        typer.echo("No specification files found")
        raise typer.Exit(code=0)

    do_batch = batch or len(spec_files) > 1

    report_json = _build_report(pipeline, spec_files, mode, do_batch)

    _emit_report(format, report_json)

    raise typer.Exit(code=0 if _overall_pass(report_json) else 1)
