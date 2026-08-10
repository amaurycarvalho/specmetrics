"""Multi-factor scoring for Story Points measurement."""

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


def _score_business_interactions(
    fp_id: str, cfm: CanonicalFunctionalModel, fp: FunctionalProcess
) -> float:
    return float(len(fp.actor_ids))


def _score_logical_information(
    fp_id: str, cfm: CanonicalFunctionalModel, fp: FunctionalProcess
) -> float:
    return float(len(fp.data_group_ids) + len(fp.operation_ids))


def _score_external_integrations(
    fp_id: str, cfm: CanonicalFunctionalModel, fp: FunctionalProcess
) -> float:
    count = 0
    for rel in cfm.relationships:
        if rel.relationship_type == "communicates_with" and (
            rel.source_id == fp_id or rel.target_id == fp_id
        ):
            count += 1
    return float(count)


def _score_business_rule_density(
    fp_id: str, cfm: CanonicalFunctionalModel, fp: FunctionalProcess
) -> float:
    count = 0
    for br in cfm.business_rules.values():
        if fp_id in br.related_process_ids:
            count += 1
    return float(count)


def _score_workflow_breadth(
    fp_id: str, cfm: CanonicalFunctionalModel, fp: FunctionalProcess
) -> float:
    count = 0
    for op in cfm.operations.values():
        if op.parent_process_id == fp_id:
            count += 1
    return float(count)


def _score_exception_handling(
    fp_id: str, cfm: CanonicalFunctionalModel, fp: FunctionalProcess
) -> float:
    for op in cfm.operations.values():
        if op.parent_process_id == fp_id:
            meta = op.metadata or {}
            if meta.get("type") in ("conditional", "branching", "exception"):
                return 1.0
    return 0.0


_FACTOR_SCORERS: dict[str, object] = {
    "business_interactions": _score_business_interactions,
    "logical_information": _score_logical_information,
    "external_integrations": _score_external_integrations,
    "business_rule_density": _score_business_rule_density,
    "workflow_breadth": _score_workflow_breadth,
    "exception_handling": _score_exception_handling,
}


def score_factor(
    factor_name: str,
    fp_id: str,
    cfm: CanonicalFunctionalModel,
    fp: FunctionalProcess,
) -> float:
    """Score a single factor for the given functional process."""
    handler = _FACTOR_SCORERS.get(factor_name)
    if handler is None:
        return 0.0
    return handler(fp_id, cfm, fp)


def score_all_factors(
    fp_id: str,
    cfm: CanonicalFunctionalModel,
    fp: FunctionalProcess,
    coefficients: dict[str, float] | None = None,
) -> dict[str, float]:
    """Score all factors for the given functional process."""
    coeffs = dict(DEFAULT_FACTOR_COEFFICIENTS)
    if coefficients:
        coeffs.update(coefficients)

    result: dict[str, float] = {}
    for factor_name in FACTOR_NAMES:
        raw = score_factor(factor_name, fp_id, cfm, fp)
        result[factor_name] = raw * coeffs[factor_name]
    return result
