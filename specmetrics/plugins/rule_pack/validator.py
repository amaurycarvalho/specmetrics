"""Validation of rule pack definitions."""

from __future__ import annotations

from collections.abc import Callable
from typing import Self

import structlog

from specmetrics.kernel.cfm.models import (
    FileLoadResult,
    Rule,
    RulePack,
    RuleValidationReport,
    ValidationError,
    ValidationWarning,
)

from ._validators import (
    GSC_KEYS,  # noqa: F401  (re-exported)
    VALID_COMPLEXITIES,  # noqa: F401  (re-exported)
    VALID_FUNCTION_TYPES,  # noqa: F401  (re-exported)
    VALID_RULE_TYPES,
    validate_complexity_override_config,
    validate_element_exclusion_config,
    validate_exclusion_config,
    validate_vaf_config,
    validate_weight_override_config,
)

logger = structlog.get_logger(__name__)


class RulePackValidator:
    """Validates rule pack definitions and detects conflicts."""

    def validate_pack(
        self: Self,
        pack: RulePack,
        load_result: FileLoadResult,
    ) -> RuleValidationReport:
        """Validate a rule pack and return the validation report."""
        report = RuleValidationReport()
        if load_result.status == "error":
            report.errors.append(
                ValidationError(
                    file_path=load_result.file_path,
                    message=load_result.error,
                )
            )
            return report

        report.loaded_files.append(load_result)
        seen_ids: set[str] = set()

        for rule in pack.rules:
            report.total_rules += 1

            rule_errors = self._validate_rule(rule, load_result.file_path, seen_ids)
            report.errors.extend(rule_errors)

            if not rule_errors:
                report.active_rules += 1

        conflicts = self._detect_conflicts(pack, load_result.file_path)
        report.warnings.extend(conflicts)

        if report.active_rules > 0:
            logger.info(
                "rule_pack_validated",
                file=load_result.file_path,
                rules=len(pack.rules),
                active=report.active_rules,
                errors=len(report.errors),
                warnings=len(report.warnings),
            )

        return report

    def _validate_rule(
        self: Self,
        rule: Rule,
        file_path: str,
        seen_ids: set[str],
    ) -> list[ValidationError]:
        errors: list[ValidationError] = []

        if not rule.id:
            errors.append(
                ValidationError(
                    file_path=file_path,
                    message="Rule is missing required 'id' field",
                    rule_id=rule.id,
                    field="id",
                )
            )
            return errors

        if rule.id in seen_ids:
            errors.append(
                ValidationError(
                    file_path=file_path,
                    message=f"Duplicate rule id '{rule.id}'",
                    rule_id=rule.id,
                    field="id",
                )
            )
        seen_ids.add(rule.id)

        if rule.type not in VALID_RULE_TYPES:
            errors.append(
                ValidationError(
                    file_path=file_path,
                    message=f"Unknown rule type '{rule.type}'. Must be one of: {', '.join(sorted(VALID_RULE_TYPES))}",
                    rule_id=rule.id,
                    field="type",
                )
            )
            return errors

        type_errors = self._validate_config_by_type(rule, file_path)
        errors.extend(type_errors)

        return errors

    def _validate_config_by_type(
        self: Self,
        rule: Rule,
        file_path: str,
    ) -> list[ValidationError]:
        validators: dict[str, Callable[[Rule, str], list[ValidationError]]] = {
            "exclusion": validate_exclusion_config,
            "complexity_override": validate_complexity_override_config,
            "weight_override": validate_weight_override_config,
            "vaf": validate_vaf_config,
            "element_exclusion": validate_element_exclusion_config,
        }
        validator = validators.get(rule.type)
        return validator(rule, file_path) if validator else []

    def _detect_conflicts(
        self: Self,
        pack: RulePack,
        file_path: str,
    ) -> list[ValidationWarning]:
        warnings: list[ValidationWarning] = []
        seen_function_types: dict[str, str] = {}

        for rule in pack.rules:
            if rule.type == "exclusion":
                ftypes = rule.config.function_types or []
                for ft in ftypes:
                    if ft in seen_function_types:
                        warnings.append(
                            ValidationWarning(
                                file_path=file_path,
                                message=f"Function type '{ft}' is excluded by multiple rules ('{seen_function_types[ft]}' and '{rule.id}')",
                                rule_id=rule.id,
                            )
                        )
                    seen_function_types[ft] = rule.id

        return warnings