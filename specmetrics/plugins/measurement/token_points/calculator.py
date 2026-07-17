from __future__ import annotations

import time

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.csm.model import CanonicalSpecificationModel
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


def calculate(
    cfm: CanonicalFunctionalModel | None,
    csm: CanonicalSpecificationModel | None,
    calibration: CalibrationProfile,
    run_id: str = "",
) -> TokenPointsMeasurement:
    start = time.monotonic()
    warnings: list[MeasurementWarning] = []

    spec_contributions: list[TokenContribution] = []
    code_contributions: list[TokenContribution] = []

    spec_weight = calibration.specification_cost
    code_weight = calibration.code_generation_cost

    csm_element_count = 0
    cfm_element_count = 0
    unknown_csm_count = 0
    unknown_cfm_count = 0

    if csm is not None:
        for activity_id, activity in csm.specification_activities.items():
            weight = spec_weight.activities.get(activity.activity_type, 0.0)
            contrib = TokenContribution(
                element_id=activity_id,
                element_type=activity.activity_type,
                element_name=activity.description[:80]
                if activity.description
                else activity_id,
                model_source="csm",
                applied_weight=weight,
                partial_score=weight,
                evidence_ref=_csm_evidence(activity.evidence_references),
            )
            spec_contributions.append(contrib)
            csm_element_count += 1

        for elem_id, elem in csm.references.items():
            unknown_csm_count += 1
        warnings.append(
            MeasurementWarning(
                code="UNKNOWN_CSM_ELEMENTS",
                message=f"{unknown_csm_count} CSM reference element(s) found with no configurable weight — excluded from Specification Cost",
                details={"count": str(unknown_csm_count), "category": "references"},
            )
        )

        for collection_name, collection in [
            ("decisions", csm.decisions),
            ("assumptions", csm.assumptions),
            ("constraints", csm.constraints),
            ("risks", csm.risks),
            ("open_questions", csm.open_questions),
            ("acceptance_criteria", csm.acceptance_criteria),
            ("glossary_terms", csm.glossary_terms),
        ]:
            weight = getattr(spec_weight, collection_name, 0.0)
            for elem_id, elem in collection.items():
                contrib = TokenContribution(
                    element_id=elem_id,
                    element_type=collection_name,
                    element_name=elem.description[:80] if elem.description else elem_id,
                    model_source="csm",
                    applied_weight=weight,
                    partial_score=weight,
                    evidence_ref=_csm_evidence(elem.evidence_references),
                )
                spec_contributions.append(contrib)
                csm_element_count += 1
    else:
        warnings.append(
            MeasurementWarning(
                code="MISSING_CSM",
                message="Canonical Specification Model (CSM) is not available. "
                "Specification Cost defaults to 0.",
            )
        )

    if cfm is not None:
        for collection_name, weight_attr in [
            ("functional_processes", "functional_processes"),
            ("business_rules", "business_rules"),
            ("operations", "operations"),
            ("data_groups", "data_groups"),
            ("relationships", "relationships"),
            ("actors", "actors"),
        ]:
            weight = getattr(code_weight, weight_attr, 0.0)
            collection = getattr(cfm, collection_name, {})
            if isinstance(collection, dict):
                items = collection.items()
            elif isinstance(collection, list):
                items = [
                    (getattr(e, "id", str(i)), e) for i, e in enumerate(collection)
                ]
            else:
                items = []

            for elem_id, elem in items:
                name = (
                    getattr(elem, "name", None)
                    or getattr(elem, "description", None)
                    or elem_id
                )
                evidence = getattr(elem, "evidence", None)
                contrib = TokenContribution(
                    element_id=elem_id,
                    element_type=collection_name,
                    element_name=str(name)[:80] if name else elem_id,
                    model_source="cfm",
                    applied_weight=weight,
                    partial_score=weight,
                    evidence_ref=_cfm_evidence(evidence),
                )
                code_contributions.append(contrib)
                cfm_element_count += 1
        unk_count = len(cfm.unclassified)
        if unk_count > 0:
            unknown_cfm_count += unk_count
            warnings.append(
                MeasurementWarning(
                    code="UNKNOWN_CFM_ELEMENTS",
                    message=f"{unk_count} CFM unclassified element(s) found with no configurable weight — excluded from Code Generation Cost",
                    details={"count": str(unk_count), "category": "unclassified"},
                )
            )
    else:
        warnings.append(
            MeasurementWarning(
                code="MISSING_CFM",
                message="Canonical Functional Model (CFM) is not available. "
                "Code Generation Cost defaults to 0.",
            )
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


def _cfm_evidence(evidence) -> EvidenceRef | None:
    if evidence is None:
        return None
    return EvidenceRef(
        graph_node_id=getattr(evidence, "graph_node_id", ""),
        document_id=getattr(evidence, "document_id", ""),
        section_id=getattr(evidence, "section_id", None),
        text=getattr(evidence, "text", ""),
    )
