"""Document loading helper for the validation pipeline."""

from __future__ import annotations

import time
from pathlib import Path

from specmetrics.kernel.validation.models import (
    ReportSummary,
    SpecificationDocument,
    ValidationReport,
    ValidationResult,
)


def build_load_error_report(
    path: Path,
    result: ValidationResult,
    start: float,
) -> ValidationReport:
    """Build a report for a document that failed to load."""
    return ValidationReport(
        document_path=path,
        overall_passed=False,
        results=[result],
        summary=ReportSummary(
            total_rules=1,
            passed=0,
            failed=1,
            warnings=0,
            duration_ms=int((time.monotonic() - start) * 1000),
        ),
    )


def load_spec_document(path: Path) -> SpecificationDocument | ValidationResult:
    """Load a specification document from disk, or return a load error result."""
    try:
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        return SpecificationDocument(
            path=path,
            content=content,
            size_bytes=path.stat().st_size,
            line_count=len(lines),
        )
    except FileNotFoundError:
        return ValidationResult(
            rule_name="file-readable",
            passed=False,
            message=f"File not found: {path}",
            severity="ERROR",
        )
    except PermissionError:
        return ValidationResult(
            rule_name="file-readable",
            passed=False,
            message=f"Permission denied: {path}",
            severity="ERROR",
        )
    except UnicodeDecodeError:
        return SpecificationDocument(
            path=path,
            content="",
            size_bytes=path.stat().st_size,
            line_count=0,
        )
    except OSError as exc:
        return ValidationResult(
            rule_name="file-readable",
            passed=False,
            message=f"Cannot read file {path}: {exc}",
            severity="ERROR",
        )