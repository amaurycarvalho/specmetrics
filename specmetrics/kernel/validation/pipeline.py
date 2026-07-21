from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import structlog

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
    def __init__(self) -> None:
        self._rules: list[ValidationRule] = list(BUILTIN_STRUCTURAL_RULES)
        self._rule_fns: dict[str, Callable] = dict(STRUCTURAL_RULE_FN)
        self._constitutional_rules: list[ValidationRule] = list(
            BUILTIN_CONSTITUTIONAL_RULES
        )
        self._constitutional_rule_fns: dict[str, Callable] = dict(
            CONSTITUTIONAL_RULE_FN
        )

    def register_rule(
        self,
        rule: ValidationRule,
        fn: Callable[[SpecificationDocument], ValidationResult],
    ) -> None:
        self._rules.append(rule)
        self._rule_fns[rule.name] = fn

    def register_constitutional_rule(
        self,
        rule: ValidationRule,
        fn: Callable[[SpecificationDocument], ValidationResult],
    ) -> None:
        self._constitutional_rules.append(rule)
        self._constitutional_rule_fns[rule.name] = fn

    def load_rules(self, config_path: Path | None = None) -> None:
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

    def _load_document(self, path: Path) -> SpecificationDocument | ValidationResult:
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

    def run(
        self,
        path: Path,
        mode: str = "all",
    ) -> ValidationReport:
        start = time.monotonic()
        doc_or_error = self._load_document(path)

        results: list[ValidationResult] = []

        if isinstance(doc_or_error, ValidationResult):
            results.append(doc_or_error)
            report = ValidationReport(
                document_path=path,
                overall_passed=False,
                results=results,
                summary=ReportSummary(
                    total_rules=1,
                    passed=0,
                    failed=1,
                    warnings=0,
                    duration_ms=int((time.monotonic() - start) * 1000),
                ),
            )
            return report

        document = doc_or_error

        logger.info(
            "validation_started",
            path=str(path),
            mode=mode,
            line_count=document.line_count,
        )

        if mode in ("all", "structural"):
            for rule in self._rules:
                if not rule.enabled:
                    continue
                fn = self._rule_fns.get(rule.name)
                if fn is None:
                    continue
                result = fn(document)
                results.append(result)

        if mode in ("all", "constitutional"):
            for rule in self._constitutional_rules:
                if not rule.enabled:
                    continue
                fn = self._constitutional_rule_fns.get(rule.name)
                if fn is None:
                    continue
                result = fn(document)
                results.append(result)

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

        report = ValidationReport(
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
        return report

    def run_batch(
        self,
        paths: list[Path],
        mode: str = "all",
    ) -> BatchReport:
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

    def find_spec_files(self, paths: list[Path]) -> list[Path]:
        spec_files: list[Path] = []
        for p in paths:
            if p.is_file():
                spec_files.append(p)
            elif p.is_dir():
                spec_files.extend(sorted(p.rglob("spec.md")))
        return spec_files
