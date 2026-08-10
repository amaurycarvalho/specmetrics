"""Internal per-config validators and shared constants for rule pack validation."""

from __future__ import annotations

from specmetrics.kernel.cfm.models import Rule, ValidationError

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


def validate_exclusion_config(
    rule: Rule, file_path: str
) -> list[ValidationError]:
    """Validate an exclusion rule's configuration."""
    errors: list[ValidationError] = []
    ftypes = rule.config.function_types
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
    return errors


def validate_complexity_override_config(
    rule: Rule, file_path: str
) -> list[ValidationError]:
    """Validate a complexity override rule's configuration."""
    errors: list[ValidationError] = []
    cfg = rule.config
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
            errors.extend(validate_threshold(thresholds, key, rule, file_path))
    return errors


def validate_weight_override_config(
    rule: Rule, file_path: str
) -> list[ValidationError]:
    """Validate a weight override rule's configuration."""
    errors: list[ValidationError] = []
    cfg = rule.config
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
    return errors


def validate_vaf_config(rule: Rule, file_path: str) -> list[ValidationError]:
    """Validate a VAF rule's configuration."""
    errors: list[ValidationError] = []
    gsc = rule.config.gsc
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
        errors.extend(validate_gsc(gsc, rule, file_path))
    return errors


def validate_gsc(
    gsc: dict, rule: Rule, file_path: str
) -> list[ValidationError]:
    """Validate the GSC dictionary of a VAF rule."""
    errors: list[ValidationError] = []
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
    return errors


def validate_element_exclusion_config(
    rule: Rule, file_path: str
) -> list[ValidationError]:
    """Validate an element exclusion rule's configuration."""
    eids = rule.config.element_ids
    if not eids or not isinstance(eids, list) or len(eids) == 0:
        return [
            ValidationError(
                file_path=file_path,
                message="Element exclusion rule requires non-empty 'element_ids' list",
                rule_id=rule.id,
                field="config.element_ids",
            )
        ]
    return []


def validate_threshold(
    thresholds: dict,
    key: str,
    rule: Rule,
    file_path: str,
) -> list[ValidationError]:
    """Validate a single threshold bound list for a key."""
    bounds = thresholds.get(key)
    if bounds is None:
        return []
    if not isinstance(bounds, list) or len(bounds) != 2:
        return [
            ValidationError(
                file_path=file_path,
                message=f"Threshold '{key}' must be a list of exactly 2 integers",
                rule_id=rule.id,
                field=f"config.thresholds.{key}",
            )
        ]
    if not all(isinstance(v, int) and v > 0 for v in bounds):
        return [
            ValidationError(
                file_path=file_path,
                message=f"Threshold '{key}' values must be positive integers, got {bounds}",
                rule_id=rule.id,
                field=f"config.thresholds.{key}",
            )
        ]
    if bounds[0] >= bounds[1]:
        return [
            ValidationError(
                file_path=file_path,
                message=f"Threshold '{key}' first value must be less than second, got {bounds}",
                rule_id=rule.id,
                field=f"config.thresholds.{key}",
            )
        ]
    return []