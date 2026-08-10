"""Run structural and constitutional validation over specification documents."""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Self

import structlog

from specmetrics.kernel.validation._loader import (
    build_load_error_report,
    load_spec_document,
)
from specmetrics.kernel.validation.models import (
    BatchReport,
    ReportSummary,
    SpecificationDocument,
    ValidationReport,
    ValidationResult,
    ValidationRule,
)
from specmetrics.kernel.validation.rules.constitutional import (
    BUILTIN_CONSTITUTIONAL_RULES,
    CONSTITUTIONAL_RULE_FN,
)
from specmetrics.kernel.validation.rules.structural import (
    BUILTIN_STRUCTURAL_RULES,
    STRUCTURAL_RULE_FN,
)

logger = structlog.get_logger(__name__)


class ValidationPipeline:
    """Pipeline that runs structural and constitutional rules over documents."""

    def __init__(self: Self) -> None:
        """Initialize the pipeline with built-in structural and constitutional rules."""
        self._rules: list[ValidationRule] = list(BUILTIN_STRUCTURAL_RULES)
        self._rule_fns: dict[str, Callable] = dict(STRUCTURAL_RULE_FN)
        self._constitutional_rules: list[ValidationRule] = list(
            BUILTIN_CONSTITUTIONAL_RULES
        )
        self._constitutional_rule_fns: dict[str, Callable] = dict(
            CONSTITUTIONAL_RULE_FN
        )

    def register_rule(
        self: Self,
        rule: ValidationRule,
        fn: Callable[[SpecificationDocument], ValidationResult],
    ) -> None:
        """Register a structural validation rule with its function."""
        self._rules.append(rule)
        self._rule_fns[rule.name] = fn

    def register_constitutional_rule(
        self: Self,
        rule: ValidationRule,
        fn: Callable[[SpecificationDocument], ValidationResult],
    ) -> None:
        """Register a constitutional validation rule with its function."""
        self._constitutional_rules.append(rule)
        self._constitutional_rule_fns[rule.name] = fn

    def load_rules(self: Self, config_path: Path | None = None) -> None:
        """Load rule enablement flags from an optional YAML config file."""
        if config_path is None:
            return
        if not config_path.exists():
            return
        try:
            import yaml

            with open(config_path) as f:
                raw = yaml.safe_load(f)
            if not raw or "rules" not in raw:
                return
            configured = raw["rules"]
            for rule in self._rules:
                if rule.name in configured:
                    rule.enabled = configured[rule.name].get("enabled", True)
        except Exception:
            pass

    def _load_document(self: Self, path: Path) -> SpecificationDocument | ValidationResult:
        return load_spec_document(path)

    def run(
        self: Self,
        path: Path,
        mode: str = "all",
    ) -> ValidationReport:
        """Validate a single document and return a validation report."""
        start = time.monotonic()
        doc_or_error = self._load_document(path)

        if isinstance(doc_or_error, ValidationResult):
            return build_load_error_report(path, doc_or_error, start)

        document = doc_or_error

        logger.info(
            "validation_started",
            path=str(path),
            mode=mode,
            line_count=document.line_count,
        )

        results = self._collect_results(document, mode)

        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed and r.severity == "ERROR")
        warnings = sum(1 for r in results if not r.passed and r.severity == "WARNING")

        duration_ms = int((time.monotonic() - start) * 1000)

        logger.info(
            "validation_completed",
            path=str(path),
            overall_passed=failed == 0,
            total_rules=len(results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            duration_ms=duration_ms,
        )

        return ValidationReport(
            document_path=path,
            overall_passed=failed == 0,
            results=results,
            summary=ReportSummary(
                total_rules=len(results),
                passed=passed,
                failed=failed,
                warnings=warnings,
                duration_ms=duration_ms,
            ),
        )

    def _collect_results(
        self: Self, document: SpecificationDocument, mode: str
    ) -> list[ValidationResult]:
        """Run enabled rules matching the requested mode."""
        results: list[ValidationResult] = []
        if mode in ("all", "structural"):
            results.extend(self._run_structural(document))
        if mode in ("all", "constitutional"):
            results.extend(self._run_constitutional(document))
        return results

    def _run_structural(
        self: Self, document: SpecificationDocument
    ) -> list[ValidationResult]:
        """Run all enabled structural rules over a document."""
        results: list[ValidationResult] = []
        for rule in self._rules:
            if not rule.enabled:
                continue
            fn = self._rule_fns.get(rule.name)
            if fn is None:
                continue
            results.append(fn(document))
        return results

    def _run_constitutional(
        self: Self, document: SpecificationDocument
    ) -> list[ValidationResult]:
        """Run all enabled constitutional rules over a document."""
        results: list[ValidationResult] = []
        for rule in self._constitutional_rules:
            if not rule.enabled:
                continue
            fn = self._constitutional_rule_fns.get(rule.name)
            if fn is None:
                continue
            results.append(fn(document))
        return results

    def run_batch(
        self: Self,
        paths: list[Path],
        mode: str = "all",
    ) -> BatchReport:
        """Validate multiple documents and return a batch report."""
        start = time.monotonic()
        logger.info("batch_validation_started", document_count=len(paths), mode=mode)
        reports: list[ValidationReport] = []
        for p in paths:
            report = self.run(p, mode=mode)
            reports.append(report)

        passed_docs = sum(1 for r in reports if r.overall_passed)
        failed_docs = sum(1 for r in reports if not r.overall_passed)
        duration_ms = int((time.monotonic() - start) * 1000)

        logger.info(
            "batch_validation_completed",
            total_documents=len(reports),
            passed_documents=passed_docs,
            failed_documents=failed_docs,
            duration_ms=duration_ms,
        )

        return BatchReport(
            reports=reports,
            total_documents=len(reports),
            passed_documents=passed_docs,
            failed_documents=failed_docs,
            duration_ms=duration_ms,
        )

    def find_spec_files(self: Self, paths: list[Path]) -> list[Path]:
        """Collect specification files from the given files and directories."""
        spec_files: list[Path] = []
        for p in paths:
            if p.is_file():
                spec_files.append(p)
            elif p.is_dir():
                spec_files.extend(sorted(p.rglob("spec.md")))
        return spec_files
