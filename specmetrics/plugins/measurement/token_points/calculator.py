"""Token Points calculation logic."""

from __future__ import annotations

import time

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.csm.model import CanonicalSpecificationModel
from specmetrics.kernel.token_utils import count_tokens
from specmetrics.plugins.calibration.models import CalibrationProfile

from .models import (
    CodeGenerationCost,
    EvidenceRef,
    MeasurementMetadata,
    MeasurementWarning,
    SpecificationCost,
    TokenContribution,
    TokenPointsMeasurement,
)

logger = structlog.get_logger(__name__)


def _extract_content_text_csm(elem: object) -> str:
    name = getattr(elem, "name", None) or ""
    description = getattr(elem, "description", None) or ""
    return (name + " " + description).strip()


def _extract_content_text_cfm(elem: object, collection_name: str) -> str:
    if collection_name == "relationships":
        name = getattr(elem, "name", None) or ""
        return name.strip()
    name = getattr(elem, "name", None) or ""
    description = getattr(elem, "description", None) or ""
    return (name + " " + description).strip()


def _build_token_contribution(
    *,
    element_id: str,
    element_type: str,
    element_name: str,
    model_source: str,
    applied_weight: float,
    content_text: str,
    content_multiplier: float,
    evidence_ref: EvidenceRef | None,
) -> TokenContribution:
    if not content_text:
        content_tokens = 0
        content_score = 0.0
        logger.debug("empty_content", element_id=element_id, element_type=element_type)
    else:
        content_tokens = count_tokens(content_text)
        content_score = content_tokens * content_multiplier
    partial_score = applied_weight + content_score
    logger.debug(
        "token_contribution",
        element_id=element_id,
        element_type=element_type,
        content_token_count=content_tokens,
        content_score=content_score,
    )
    return TokenContribution(
        element_id=element_id,
        element_type=element_type,
        element_name=element_name,
        model_source=model_source,
        applied_weight=applied_weight,
        content_token_count=content_tokens,
        content_score=content_score,
        partial_score=partial_score,
        evidence_ref=evidence_ref,
    )


def calculate(
    cfm: CanonicalFunctionalModel | None,
    csm: CanonicalSpecificationModel | None,
    calibration: CalibrationProfile,
    run_id: str = "",
) -> TokenPointsMeasurement:
    """Calculate the Token Points measurement from CFM and CSM models."""
    start = time.monotonic()
    warnings: list[MeasurementWarning] = []

    spec_weight = calibration.specification_cost
    code_weight = calibration.code_generation_cost
    content_multiplier = calibration.content_multiplier

    spec_contributions, csm_element_count, unknown_csm_count = _collect_csm(
        csm, spec_weight, content_multiplier, warnings
    )
    code_contributions, cfm_element_count, unknown_cfm_count = _collect_cfm(
        cfm, code_weight, content_multiplier, warnings
    )

    spec_total = sum(c.partial_score for c in spec_contributions)
    code_total = sum(c.partial_score for c in code_contributions)
    total_score = spec_total + code_total

    duration_ms = (time.monotonic() - start) * 1000

    metadata = MeasurementMetadata(
        total_elements_processed=csm_element_count + cfm_element_count,
        csm_element_count=csm_element_count,
        cfm_element_count=cfm_element_count,
        unknown_csm_element_count=unknown_csm_count,
        unknown_cfm_element_count=unknown_cfm_count,
        duration_ms=round(duration_ms, 2),
        warnings=warnings,
        calibration_profile_applied=calibration.version,
    )

    return TokenPointsMeasurement(
        run_id=run_id,
        total_score=total_score,
        specification_cost=SpecificationCost(
            total=spec_total, contributions=spec_contributions
        ),
        code_generation_cost=CodeGenerationCost(
            total=code_total, contributions=code_contributions
        ),
        calibration_version=calibration.version,
        measurement_metadata=metadata,
    )


def _collect_csm(
    csm: CanonicalSpecificationModel | None,
    spec_weight: object,
    content_multiplier: float,
    warnings: list[MeasurementWarning],
) -> tuple[list[TokenContribution], int, int]:
    contributions: list[TokenContribution] = []
    count = 0
    unknown = 0
    if csm is None:
        warnings.append(
            MeasurementWarning(
                code="MISSING_CSM",
                message="Canonical Specification Model (CSM) is not available. "
                "Specification Cost defaults to 0.",
            )
        )
        return contributions, count, unknown

    for activity_id, activity in csm.specification_activities.items():
        weight = spec_weight.activities.get(activity.activity_type, 0.0)
        content_text = _extract_content_text_csm(activity)
        contributions.append(
            _build_token_contribution(
                element_id=activity_id,
                element_type=activity.activity_type,
                element_name=activity.description[:80]
                if activity.description
                else activity_id,
                model_source="csm",
                applied_weight=weight,
                content_text=content_text,
                content_multiplier=content_multiplier,
                evidence_ref=_csm_evidence(activity.evidence_references),
            )
        )
        count += 1

    for elem_id, elem in csm.references.items():
        content_text = (
            (getattr(elem, "title", None) or "")
            + " "
            + (getattr(elem, "url", None) or "")
        ).strip()
        contributions.append(
            _build_token_contribution(
                element_id=elem_id,
                element_type="references",
                element_name=elem_id,
                model_source="csm",
                applied_weight=spec_weight.references,
                content_text=content_text,
                content_multiplier=content_multiplier,
                evidence_ref=_csm_evidence(elem.evidence_references),
            )
        )
        count += 1

    for collection_name in (
        "decisions",
        "assumptions",
        "constraints",
        "risks",
        "open_questions",
        "acceptance_criteria",
        "glossary_terms",
    ):
        weight = getattr(spec_weight, collection_name, 0.0)
        for elem_id, elem in getattr(csm, collection_name, {}).items():
            content_text = _extract_content_text_csm(elem)
            contributions.append(
                _build_token_contribution(
                    element_id=elem_id,
                    element_type=collection_name,
                    element_name=elem.description[:80]
                    if elem.description
                    else elem_id,
                    model_source="csm",
                    applied_weight=weight,
                    content_text=content_text,
                    content_multiplier=content_multiplier,
                    evidence_ref=_csm_evidence(elem.evidence_references),
                )
            )
            count += 1

    return contributions, count, unknown


def _collect_cfm(
    cfm: CanonicalFunctionalModel | None,
    code_weight: object,
    content_multiplier: float,
    warnings: list[MeasurementWarning],
) -> tuple[list[TokenContribution], int, int]:
    contributions: list[TokenContribution] = []
    count = 0
    unknown = 0
    if cfm is None:
        warnings.append(
            MeasurementWarning(
                code="MISSING_CFM",
                message="Canonical Functional Model (CFM) is not available. "
                "Code Generation Cost defaults to 0.",
            )
        )
        return contributions, count, unknown

    for collection_name, weight_attr in [
        ("functional_processes", "functional_processes"),
        ("business_rules", "business_rules"),
        ("operations", "operations"),
        ("data_groups", "data_groups"),
        ("relationships", "relationships"),
        ("actors", "actors"),
    ]:
        weight = getattr(code_weight, weight_attr, 0.0)
        for elem_id, elem in _collection_items(getattr(cfm, collection_name, {})):
            contributions.append(
                _cfm_contribution(
                    elem_id, elem, collection_name, weight, content_multiplier
                )
            )
            count += 1

    unk_count = len(cfm.unclassified)
    if unk_count > 0:
        unknown = unk_count
        warnings.append(
            MeasurementWarning(
                code="UNKNOWN_CFM_ELEMENTS",
                message=f"{unk_count} CFM unclassified element(s) found with no configurable weight — excluded from Code Generation Cost",
                details={"count": str(unk_count), "category": "unclassified"},
            )
        )

    return contributions, count, unknown


def _collection_items(collection: object) -> list[tuple[str, object]]:
    if isinstance(collection, dict):
        return list(collection.items())  # type: ignore[arg-type]
    if isinstance(collection, list):
        return [(getattr(e, "id", str(i)), e) for i, e in enumerate(collection)]
    return []


def _cfm_contribution(
    elem_id: str,
    elem: object,
    collection_name: str,
    weight: float,
    content_multiplier: float,
) -> TokenContribution:
    name = (
        getattr(elem, "name", None)
        or getattr(elem, "description", None)
        or elem_id
    )
    evidence = getattr(elem, "evidence", None)
    content_text = _extract_content_text_cfm(elem, collection_name)
    return _build_token_contribution(
        element_id=elem_id,
        element_type=collection_name,
        element_name=str(name)[:80] if name else elem_id,
        model_source="cfm",
        applied_weight=weight,
        content_text=content_text,
        content_multiplier=content_multiplier,
        evidence_ref=_cfm_evidence(evidence),
    )


def _csm_evidence(
    evidence_refs: list,
) -> EvidenceRef | None:
    if not evidence_refs:
        return None
    ref = evidence_refs[0]
    return EvidenceRef(
        graph_node_id=getattr(ref, "graph_node_id", ""),
        document_id=getattr(ref, "document_id", ""),
        section_id=getattr(ref, "section_id", None),
        text=getattr(ref, "text", ""),
    )


def _cfm_evidence(evidence: object) -> EvidenceRef | None:
    if evidence is None:
        return None
    return EvidenceRef(
        graph_node_id=getattr(evidence, "graph_node_id", ""),
        document_id=getattr(evidence, "document_id", ""),
        section_id=getattr(evidence, "section_id", None),
        text=getattr(evidence, "text", ""),
    )
