"""Work item builders for Story Points calculation."""
from __future__ import annotations

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.csm.model import CanonicalSpecificationModel, CsmElement

from ._refs import (
    evidence_ref_from_cfm_evidence,
    evidence_ref_from_csm_evidence,
    evidence_ref_from_fp,
    fingerprint,
)
from .calibrator import StoryPointsCalibrationProfile
from .factor_scorer import score_all_factors
from .models import MeasurementWarning, WorkItem
from .token_counter import count_tokens_for_element

CSM_CONTAINER_TO_TYPE: dict[str, str] = {
    "decisions": "decision",
    "assumptions": "assumption",
    "constraints": "constraint",
    "risks": "risk",
    "open_questions": "open_question",
    "acceptance_criteria": "acceptance_criterion",
    "glossary_terms": "glossary_term",
    "references": "reference",
}

CSM_CONTAINER_NAMES: list[str] = [
    "specification_activities",
    "decisions",
    "assumptions",
    "constraints",
    "risks",
    "open_questions",
    "acceptance_criteria",
    "glossary_terms",
    "references",
]

CFM_NON_FP_TYPES: dict[str, str] = {
    "business_rules": "business_rule",
    "operations": "operation",
    "data_groups": "data_group",
    "relationships": "relationship",
    "actors": "actor",
}


def build_fp_items(
    cfm: CanonicalFunctionalModel,
    coeffs: dict[str, float],
    coefficients: dict[str, float] | None,
    content_multiplier: float,
    cal: StoryPointsCalibrationProfile,
) -> tuple[list[WorkItem], list[MeasurementWarning], int, int, dict[str, bool]]:
    """Build WorkItems for all functional processes in the CFM."""
    warnings: list[MeasurementWarning] = []
    items: list[WorkItem] = []
    fp_count = 0
    merged_count = 0
    seen_fingerprints: dict[str, bool] = {}

    for fp_id, fp in cfm.functional_processes.items():
        fp_count += 1
        fprint = fingerprint(fp)

        if fprint in seen_fingerprints:
            merged_count += 1
            continue
        seen_fingerprints[fprint] = True

        factor_scores = score_all_factors(fp_id, cfm, fp, coeffs)
        structural_score = sum(factor_scores.values())

        content_tokens = count_tokens_for_element(fp.name, fp.description)
        content_score = content_tokens * content_multiplier
        raw_score = structural_score + content_score

        applied_rules = ["default_coefficients_v1"]
        if coefficients:
            applied_rules = [
                f"custom_coefficients:{k}={v}" for k, v in coefficients.items()
            ]

        items.append(
            WorkItem(
                element_id=fp_id,
                element_name=fp.name,
                element_type="functional_process",
                source_model="CFM",
                raw_score=raw_score,
                normalized_value=0,
                rank_position=0,
                structural_score=structural_score,
                content_tokens=content_tokens,
                content_score=content_score,
                factor_breakdown=factor_scores,
                base_weight=None,
                applied_rules=applied_rules,
                evidence_refs=[evidence_ref_from_fp(fp)],
            )
        )

    return items, warnings, fp_count, merged_count, seen_fingerprints


def build_csm_items(
    csm: CanonicalSpecificationModel,
    content_multiplier: float,
    cal: StoryPointsCalibrationProfile,
    fp_ids: set[str],
) -> tuple[list[WorkItem], list[MeasurementWarning], int]:
    """Build WorkItems for all CSM elements."""
    warnings: list[MeasurementWarning] = []
    items: list[WorkItem] = []
    csm_count = 0

    def _process_csm_element(
        element: CsmElement, element_type: str, container_name: str
    ) -> None:
        nonlocal csm_count
        csm_count += 1
        base_weight = cal.csm_base_weights.get(element_type, cal.default_fallback_weight)
        element_name = getattr(element, "description", element.id)[:80]
        structural_score = base_weight
        content_tokens = count_tokens_for_element(element_type, element.description)
        content_score = content_tokens * content_multiplier
        raw_score = structural_score + content_score

        ref = evidence_ref_from_csm_evidence(element.evidence_references)

        if base_weight == cal.default_fallback_weight and element_type not in cal.csm_base_weights:
            warnings.append(
                MeasurementWarning(
                    code="UNKNOWN_ELEMENT_TYPE",
                    message=f"Element type '{element_type}' not in csm_base_weights, using default_fallback_weight={cal.default_fallback_weight}",
                    element_id=element.id,
                )
            )

        items.append(
            WorkItem(
                element_id=element.id,
                element_name=element_name,
                element_type=element_type,
                source_model="CSM",
                raw_score=raw_score,
                normalized_value=0,
                rank_position=0,
                structural_score=structural_score,
                content_tokens=content_tokens,
                content_score=content_score,
                factor_breakdown={},
                base_weight=base_weight,
                applied_rules=["csm_base_weight"],
                evidence_refs=[ref] if ref else [],
            )
        )

    for container_name in CSM_CONTAINER_NAMES:
        container = getattr(csm, container_name, {})
        if container_name == "specification_activities":
            for act in container.values():
                _process_csm_element(act, act.activity_type, container_name)
        elif container_name in CSM_CONTAINER_TO_TYPE:
            etype = CSM_CONTAINER_TO_TYPE[container_name]
            for elem in container.values():
                _process_csm_element(elem, etype, container_name)

    return items, warnings, csm_count


def build_cfm_non_fp_items(
    cfm: CanonicalFunctionalModel,
    content_multiplier: float,
    cal: StoryPointsCalibrationProfile,
    fp_ids: set[str],
) -> tuple[list[WorkItem], list[MeasurementWarning], int, int]:
    """Build WorkItems for non-functional-process CFM elements."""
    warnings: list[MeasurementWarning] = []
    items: list[WorkItem] = []
    non_fp_count = 0
    no_weight_count = 0

    for br_id, br in cfm.business_rules.items():
        inc, nowt = _append_cfm_weighted_item(
            items,
            element_id=br_id,
            element_name=br.name,
            content_name=br.name,
            content_desc=br.description,
            element_type="business_rule",
            evidence=br.evidence,
            cal=cal,
            content_multiplier=content_multiplier,
        )
        non_fp_count += inc
        no_weight_count += nowt

    for op_id, op in cfm.operations.items():
        inc, nowt = _append_cfm_weighted_item(
            items,
            element_id=op_id,
            element_name=op.name,
            content_name=op.name,
            content_desc=op.description,
            element_type="operation",
            evidence=op.evidence,
            cal=cal,
            content_multiplier=content_multiplier,
        )
        non_fp_count += inc
        no_weight_count += nowt

    for dg_id, dg in cfm.data_groups.items():
        inc, nowt = _append_cfm_weighted_item(
            items,
            element_id=dg_id,
            element_name=dg.name,
            content_name=dg.name,
            content_desc=dg.description,
            element_type="data_group",
            evidence=dg.evidence,
            cal=cal,
            content_multiplier=content_multiplier,
        )
        non_fp_count += inc
        no_weight_count += nowt

    for rel in cfm.relationships:
        rel_name = f"{rel.source_id}->{rel.target_id}"
        inc, nowt = _append_cfm_weighted_item(
            items,
            element_id=rel.id,
            element_name=rel_name,
            content_name=rel_name,
            content_desc="",
            element_type="relationship",
            evidence=rel.evidence,
            cal=cal,
            content_multiplier=content_multiplier,
        )
        non_fp_count += inc
        no_weight_count += nowt

    for act_id, act in cfm.actors.items():
        inc, nowt = _append_cfm_weighted_item(
            items,
            element_id=act_id,
            element_name=act.name,
            content_name=act.name,
            content_desc="",
            element_type="actor",
            evidence=act.evidence,
            cal=cal,
            content_multiplier=content_multiplier,
        )
        non_fp_count += inc
        no_weight_count += nowt

    return items, warnings, non_fp_count, no_weight_count


def _append_cfm_weighted_item(
    items: list[WorkItem],
    *,
    element_id: str,
    element_name: str,
    content_name: str,
    content_desc: str,
    element_type: str,
    evidence: object,
    cal: StoryPointsCalibrationProfile,
    content_multiplier: float,
) -> tuple[int, int]:
    """Append a CFM non-FP WorkItem and report whether it lacked a base weight."""
    base_weight = cal.cfm_base_weights.get(
        element_type, cal.default_fallback_weight
    )
    structural_score = base_weight
    content_tokens = count_tokens_for_element(content_name, content_desc)
    content_score = content_tokens * content_multiplier
    raw_score = structural_score + content_score

    items.append(
        WorkItem(
            element_id=element_id,
            element_name=element_name,
            element_type=element_type,
            source_model="CFM",
            raw_score=raw_score,
            normalized_value=0,
            rank_position=0,
            structural_score=structural_score,
            content_tokens=content_tokens,
            content_score=content_score,
            factor_breakdown={},
            base_weight=base_weight,
            applied_rules=["cfm_base_weight"],
            evidence_refs=[evidence_ref_from_cfm_evidence(evidence)],
        )
    )

    if base_weight == cal.default_fallback_weight:
        return 1, 1
    return 1, 0