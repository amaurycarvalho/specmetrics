from __future__ import annotations


import structlog

from specmetrics.kernel.cfm.models import (
    FileLoadResult,
    Rule,
    RulePack,
    RuleValidationReport,
    ValidationError,
    ValidationWarning,
)

logger = structlog.get_logger(__name__)

VALID_FUNCTION_TYPES: set[str] = {"ILF", "EIF", "EI", "EO", "EQ"}
VALID_RULE_TYPES: set[str] = {
    "exclusion",
    "complexity_override",
    "weight_override",
    "vaf",
    "element_exclusion",
}
VALID_COMPLEXITIES: set[str] = {"Low", "Average", "High"}
GSC_KEYS: set[str] = {
    "data_communications",
    "distributed_data_processing",
    "performance",
    "heavily_used_configuration",
    "transaction_rate",
    "online_data_entry",
    "end_user_efficiency",
    "online_update",
    "complex_processing",
    "reusability",
    "installation_ease",
    "operational_ease",
    "multiple_sites",
    "facilitate_change",
}


class RulePackValidator:
    def validate_pack(
        self,
        pack: RulePack,
        load_result: FileLoadResult,
    ) -> RuleValidationReport:
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
        self,
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
        self,
        rule: Rule,
        file_path: str,
    ) -> list[ValidationError]:
        errors: list[ValidationError] = []
        cfg = rule.config

        if rule.type == "exclusion":
            ftypes = cfg.function_types
            if not ftypes or not isinstance(ftypes, list) or len(ftypes) == 0:
                errors.append(
                    ValidationError(
                        file_path=file_path,
                        message="Exclusion rule requires non-empty 'function_types' list",
                        rule_id=rule.id,
                        field="config.function_types",
                    )
                )
            else:
                for ft in ftypes:
                    if ft not in VALID_FUNCTION_TYPES:
                        errors.append(
                            ValidationError(
                                file_path=file_path,
                                message=f"Unknown function type '{ft}' in exclusion rule. Must be one of: {', '.join(sorted(VALID_FUNCTION_TYPES))}",
                                rule_id=rule.id,
                                field="config.function_types",
                            )
                        )

        elif rule.type == "complexity_override":
            ft = cfg.function_type
            if not ft or ft not in VALID_FUNCTION_TYPES:
                errors.append(
                    ValidationError(
                        file_path=file_path,
                        message=f"Complexity override requires valid 'function_type'. Got '{ft}'",
                        rule_id=rule.id,
                        field="config.function_type",
                    )
                )
            thresholds = cfg.thresholds
            if not thresholds or not isinstance(thresholds, dict):
                errors.append(
                    ValidationError(
                        file_path=file_path,
                        message="Complexity override requires 'thresholds' with det/ftr or ret bounds",
                        rule_id=rule.id,
                        field="config.thresholds",
                    )
                )
            else:
                for key in ("det", "ret", "ftr"):
                    bounds = thresholds.get(key)
                    if bounds is not None:
                        if not isinstance(bounds, list) or len(bounds) != 2:
                            errors.append(
                                ValidationError(
                                    file_path=file_path,
                                    message=f"Threshold '{key}' must be a list of exactly 2 integers",
                                    rule_id=rule.id,
                                    field=f"config.thresholds.{key}",
                                )
                            )
                        elif not all(isinstance(v, int) and v > 0 for v in bounds):
                            errors.append(
                                ValidationError(
                                    file_path=file_path,
                                    message=f"Threshold '{key}' values must be positive integers, got {bounds}",
                                    rule_id=rule.id,
                                    field=f"config.thresholds.{key}",
                                )
                            )
                        elif bounds[0] >= bounds[1]:
                            errors.append(
                                ValidationError(
                                    file_path=file_path,
                                    message=f"Threshold '{key}' first value must be less than second, got {bounds}",
                                    rule_id=rule.id,
                                    field=f"config.thresholds.{key}",
                                )
                            )

        elif rule.type == "weight_override":
            if not cfg.function_type or cfg.function_type not in VALID_FUNCTION_TYPES:
                errors.append(
                    ValidationError(
                        file_path=file_path,
                        message=f"Weight override requires valid 'function_type'. Got '{cfg.function_type}'",
                        rule_id=rule.id,
                        field="config.function_type",
                    )
                )
            if not cfg.complexity or cfg.complexity not in VALID_COMPLEXITIES:
                errors.append(
                    ValidationError(
                        file_path=file_path,
                        message=f"Weight override requires valid 'complexity' (Low/Average/High). Got '{cfg.complexity}'",
                        rule_id=rule.id,
                        field="config.complexity",
                    )
                )
            if cfg.weight is None or not isinstance(cfg.weight, int) or cfg.weight < 1:
                errors.append(
                    ValidationError(
                        file_path=file_path,
                        message=f"Weight override requires positive integer 'weight'. Got {cfg.weight}",
                        rule_id=rule.id,
                        field="config.weight",
                    )
                )

        elif rule.type == "vaf":
            gsc = cfg.gsc
            if not gsc or not isinstance(gsc, dict):
                errors.append(
                    ValidationError(
                        file_path=file_path,
                        message="VAF rule requires 'gsc' dictionary with all 14 GSC keys",
                        rule_id=rule.id,
                        field="config.gsc",
                    )
                )
            else:
                provided = set(gsc.keys())
                missing = GSC_KEYS - provided
                if missing:
                    errors.append(
                        ValidationError(
                            file_path=file_path,
                            message=f"VAF rule missing GSC keys: {', '.join(sorted(missing))}",
                            rule_id=rule.id,
                            field="config.gsc",
                        )
                    )
                extra = provided - GSC_KEYS
                if extra:
                    errors.append(
                        ValidationError(
                            file_path=file_path,
                            message=f"VAF rule has unknown GSC keys: {', '.join(sorted(extra))}",
                            rule_id=rule.id,
                            field="config.gsc",
                        )
                    )
                for key, val in gsc.items():
                    if not isinstance(val, int) or val < 0 or val > 5:
                        errors.append(
                            ValidationError(
                                file_path=file_path,
                                message=f"GSC '{key}' value must be integer 0-5, got {val}",
                                rule_id=rule.id,
                                field=f"config.gsc.{key}",
                            )
                        )

        elif rule.type == "element_exclusion":
            eids = cfg.element_ids
            if not eids or not isinstance(eids, list) or len(eids) == 0:
                errors.append(
                    ValidationError(
                        file_path=file_path,
                        message="Element exclusion rule requires non-empty 'element_ids' list",
                        rule_id=rule.id,
                        field="config.element_ids",
                    )
                )

        return errors

    def _detect_conflicts(
        self,
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
