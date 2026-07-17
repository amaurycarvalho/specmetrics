from __future__ import annotations

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel, FunctionalProcess


DEFAULT_FACTOR_COEFFICIENTS: dict[str, float] = {
    "business_interactions": 1.0,
    "logical_information": 1.0,
    "external_integrations": 2.0,
    "business_rule_density": 1.5,
    "workflow_breadth": 1.0,
    "exception_handling": 3.0,
}

FACTOR_NAMES: list[str] = list(DEFAULT_FACTOR_COEFFICIENTS.keys())


def score_factor(
    factor_name: str,
    fp_id: str,
    cfm: CanonicalFunctionalModel,
    fp: FunctionalProcess,
) -> float:
    if factor_name == "business_interactions":
        return float(len(fp.actor_ids))

    if factor_name == "logical_information":
        return float(len(fp.data_group_ids) + len(fp.operation_ids))

    if factor_name == "external_integrations":
        count = 0
        for rel in cfm.relationships:
            if rel.relationship_type == "communicates_with":
                if rel.source_id == fp_id or rel.target_id == fp_id:
                    count += 1
        return float(count)

    if factor_name == "business_rule_density":
        count = 0
        for br in cfm.business_rules.values():
            if fp_id in br.related_process_ids:
                count += 1
        return float(count)

    if factor_name == "workflow_breadth":
        count = 0
        for op in cfm.operations.values():
            if op.parent_process_id == fp_id:
                count += 1
        return float(count)

    if factor_name == "exception_handling":
        for op in cfm.operations.values():
            if op.parent_process_id == fp_id:
                meta = op.metadata or {}
                if meta.get("type") in ("conditional", "branching", "exception"):
                    return 1.0
        return 0.0

    return 0.0


def score_all_factors(
    fp_id: str,
    cfm: CanonicalFunctionalModel,
    fp: FunctionalProcess,
    coefficients: dict[str, float] | None = None,
) -> dict[str, float]:
    coeffs = dict(DEFAULT_FACTOR_COEFFICIENTS)
    if coefficients:
        coeffs.update(coefficients)

    result: dict[str, float] = {}
    for factor_name in FACTOR_NAMES:
        raw = score_factor(factor_name, fp_id, cfm, fp)
        result[factor_name] = raw * coeffs[factor_name]
    return result
