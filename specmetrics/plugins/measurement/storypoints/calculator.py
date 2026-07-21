from __future__ import annotations

import hashlib
import time

from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    FunctionalProcess,
)
from specmetrics.kernel.csm.model import CanonicalSpecificationModel

from .calibrator import StoryPointsCalibrationProfile, get_default_calibration
from .factor_scorer import DEFAULT_FACTOR_COEFFICIENTS, score_all_factors
from .models import (
    EvidenceRef,
    ExecutionMetadata,
    MeasurementWarning,
    StoryPointMeasurementResult,
    WorkItem,
)
from .normalizer import RelativeRankingNormalizer
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


def _fingerprint(fp: FunctionalProcess) -> str:
    ev = fp.evidence
    doc_id = getattr(ev, "document_id", "")
    section_id = getattr(ev, "section_id", "") or ""
    text = getattr(ev, "text", "")
    raw = f"{doc_id}|{section_id}|{text}|functional_process"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _evidence_ref_from_fp(fp: FunctionalProcess) -> EvidenceRef:
    ev = fp.evidence
    return EvidenceRef(
        graph_node_id=getattr(ev, "graph_node_id", ""),
        document_id=getattr(ev, "document_id", ""),
        section_id=getattr(ev, "section_id", None),
        text=getattr(ev, "text", ""),
    )


def _evidence_ref_from_csm_evidence(refs: list) -> EvidenceRef | None:
    if not refs:
        return None
    r = refs[0]
    return EvidenceRef(
        graph_node_id=getattr(r, "graph_node_id", r.id if hasattr(r, "id") else ""),
        document_id=getattr(r, "document_id", ""),
        section_id=getattr(r, "section_id", None),
        text=getattr(r, "text", ""),
    )


def _evidence_ref_from_cfm_evidence(ev) -> EvidenceRef:
    return EvidenceRef(
        graph_node_id=getattr(ev, "graph_node_id", ""),
        document_id=getattr(ev, "document_id", ""),
        section_id=getattr(ev, "section_id", None),
        text=getattr(ev, "text", ""),
    )


def _build_fp_items(
    cfm: CanonicalFunctionalModel,
    coeffs: dict[str, float],
    coefficients: dict[str, float] | None,
    content_multiplier: float,
    cal: StoryPointsCalibrationProfile,
) -> tuple[list[WorkItem], list[MeasurementWarning], int, int, dict[str, bool]]:
    warnings: list[MeasurementWarning] = []
    items: list[WorkItem] = []
    fp_count = 0
    merged_count = 0
    seen_fingerprints: dict[str, bool] = {}

    for fp_id, fp in cfm.functional_processes.items():
        fp_count += 1
        fprint = _fingerprint(fp)

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
                evidence_refs=[_evidence_ref_from_fp(fp)],
            )
        )

    return items, warnings, fp_count, merged_count, seen_fingerprints


def _build_csm_items(
    csm: CanonicalSpecificationModel,
    content_multiplier: float,
    cal: StoryPointsCalibrationProfile,
    fp_ids: set[str],
) -> tuple[list[WorkItem], list[MeasurementWarning], int]:
    warnings: list[MeasurementWarning] = []
    items: list[WorkItem] = []
    csm_count = 0

    def _process_csm_element(element, element_type: str, container_name: str):
        nonlocal csm_count
        csm_count += 1
        base_weight = cal.csm_base_weights.get(element_type, cal.default_fallback_weight)
        element_name = getattr(element, "description", element.id)[:80]
        structural_score = base_weight
        content_tokens = count_tokens_for_element(element_type, element.description)
        content_score = content_tokens * content_multiplier
        raw_score = structural_score + content_score

        ref = _evidence_ref_from_csm_evidence(element.evidence_references)

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
            for act_id, act in container.items():
                _process_csm_element(act, act.activity_type, container_name)
        elif container_name in CSM_CONTAINER_TO_TYPE:
            etype = CSM_CONTAINER_TO_TYPE[container_name]
            for elem_id, elem in container.items():
                _process_csm_element(elem, etype, container_name)

    return items, warnings, csm_count


def _build_cfm_non_fp_items(
    cfm: CanonicalFunctionalModel,
    content_multiplier: float,
    cal: StoryPointsCalibrationProfile,
    fp_ids: set[str],
) -> tuple[list[WorkItem], list[MeasurementWarning], int, int]:
    warnings: list[MeasurementWarning] = []
    items: list[WorkItem] = []
    non_fp_count = 0
    no_weight_count = 0

    for br_id, br in cfm.business_rules.items():
        non_fp_count += 1
        base_weight = cal.cfm_base_weights.get("business_rule", cal.default_fallback_weight)
        structural_score = base_weight
        content_tokens = count_tokens_for_element(br.name, br.description)
        content_score = content_tokens * content_multiplier
        raw_score = structural_score + content_score
        if base_weight == cal.default_fallback_weight:
            no_weight_count += 1
        items.append(
            WorkItem(
                element_id=br_id,
                element_name=br.name,
                element_type="business_rule",
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
                evidence_refs=[_evidence_ref_from_cfm_evidence(br.evidence)],
            )
        )

    for op_id, op in cfm.operations.items():
        non_fp_count += 1
        base_weight = cal.cfm_base_weights.get("operation", cal.default_fallback_weight)
        structural_score = base_weight
        content_tokens = count_tokens_for_element(op.name, op.description)
        content_score = content_tokens * content_multiplier
        raw_score = structural_score + content_score
        if base_weight == cal.default_fallback_weight:
            no_weight_count += 1
        items.append(
            WorkItem(
                element_id=op_id,
                element_name=op.name,
                element_type="operation",
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
                evidence_refs=[_evidence_ref_from_cfm_evidence(op.evidence)],
            )
        )

    for dg_id, dg in cfm.data_groups.items():
        non_fp_count += 1
        base_weight = cal.cfm_base_weights.get("data_group", cal.default_fallback_weight)
        structural_score = base_weight
        content_tokens = count_tokens_for_element(dg.name, dg.description)
        content_score = content_tokens * content_multiplier
        raw_score = structural_score + content_score
        if base_weight == cal.default_fallback_weight:
            no_weight_count += 1
        items.append(
            WorkItem(
                element_id=dg_id,
                element_name=dg.name,
                element_type="data_group",
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
                evidence_refs=[_evidence_ref_from_cfm_evidence(dg.evidence)],
            )
        )

    for rel in cfm.relationships:
        non_fp_count += 1
        base_weight = cal.cfm_base_weights.get("relationship", cal.default_fallback_weight)
        structural_score = base_weight
        rel_name = f"{rel.source_id}->{rel.target_id}"
        content_tokens = count_tokens_for_element(rel_name, "")
        content_score = content_tokens * content_multiplier
        raw_score = structural_score + content_score
        if base_weight == cal.default_fallback_weight:
            no_weight_count += 1
        items.append(
            WorkItem(
                element_id=rel.id,
                element_name=rel_name,
                element_type="relationship",
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
                evidence_refs=[_evidence_ref_from_cfm_evidence(rel.evidence)],
            )
        )

    for act_id, act in cfm.actors.items():
        non_fp_count += 1
        base_weight = cal.cfm_base_weights.get("actor", cal.default_fallback_weight)
        structural_score = base_weight
        content_tokens = count_tokens_for_element(act.name, "")
        content_score = content_tokens * content_multiplier
        raw_score = structural_score + content_score
        if base_weight == cal.default_fallback_weight:
            no_weight_count += 1
        items.append(
            WorkItem(
                element_id=act_id,
                element_name=act.name,
                element_type="actor",
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
                evidence_refs=[_evidence_ref_from_cfm_evidence(act.evidence)],
            )
        )

    return items, warnings, non_fp_count, no_weight_count


def calculate(
    cfm: CanonicalFunctionalModel | None,
    run_id: str = "",
    coefficients: dict[str, float] | None = None,
    previous_fingerprints: dict[str, str] | None = None,
    calibration: StoryPointsCalibrationProfile | None = None,
    csm: CanonicalSpecificationModel | None = None,
) -> StoryPointMeasurementResult:
    start = time.monotonic()
    warnings: list[MeasurementWarning] = []

    cal = calibration or get_default_calibration()
    content_multiplier = cal.content_multiplier

    if cfm is None and csm is None:
        return StoryPointMeasurementResult(
            run_id=run_id,
            total_story_points=0,
            items=[],
            distribution={},
            content_multiplier=content_multiplier,
            calibration_version=cal.version,
            execution_metadata=ExecutionMetadata(
                duration_ms=0.0,
                total_fps_processed=0,
                fps_estimated=0,
                fps_merged_as_duplicates=0,
            ),
            warnings=[
                MeasurementWarning(
                    code="MISSING_CFM",
                    message="Canonical Functional Model (CFM) is not available. "
                    "Story Points defaults to 0.",
                )
            ],
        )

    coeffs = dict(cal.factor_coefficients) if cal.factor_coefficients else dict(DEFAULT_FACTOR_COEFFICIENTS)
    if coefficients:
        coeffs.update(coefficients)

    all_items: list[WorkItem] = []
    total_fp_count = 0
    total_merged = 0
    total_cfm_non_fp = 0
    total_csm_count = 0
    total_no_weight = 0

    fp_ids: set[str] = set()

    if cfm is not None:
        fp_ids = set(cfm.functional_processes.keys())

        fp_items, fp_warnings, fp_count, merged_count, _ = _build_fp_items(
            cfm, coeffs, coefficients, content_multiplier, cal,
        )
        all_items.extend(fp_items)
        warnings.extend(fp_warnings)
        total_fp_count = fp_count
        total_merged = merged_count

        cfm_non_fp_items, cfm_non_fp_warnings, non_fp_count, no_weight_count = (
            _build_cfm_non_fp_items(
                cfm, content_multiplier, cal, fp_ids,
            )
        )
        all_items.extend(cfm_non_fp_items)
        warnings.extend(cfm_non_fp_warnings)
        total_cfm_non_fp = non_fp_count
        total_no_weight = no_weight_count

    if csm is not None:
        csm_items, csm_warnings, csm_count = _build_csm_items(
            csm, content_multiplier, cal, fp_ids,
        )
        all_items.extend(csm_items)
        warnings.extend(csm_warnings)
        total_csm_count = csm_count

    if cfm is not None and len(cfm.functional_processes) == 0:
        warnings.append(
            MeasurementWarning(
                code="NO_FPS_FOUND",
                message="No functional processes found in CFM. "
                "Only CSM and non-FP CFM elements contribute to estimation.",
            )
        )

    scores_for_ranking = [(i.element_id, i.raw_score) for i in all_items]
    rank_normalizer = RelativeRankingNormalizer(
        fibonacci_scale=cal.fibonacci_scale,
        ranking_strategy=cal.ranking_strategy,
    )
    ranking_results = rank_normalizer.normalize_all(scores_for_ranking)

    for item in all_items:
        if item.element_id in ranking_results:
            nr = ranking_results[item.element_id]
            item.normalized_value = nr.output_value
            item.rank_position = nr.rank_position

    total_sp = sum(i.normalized_value for i in all_items)
    total_raw = sum(i.raw_score for i in all_items)
    distribution: dict[int, int] = {}
    for i in all_items:
        distribution[i.normalized_value] = distribution.get(i.normalized_value, 0) + 1

    content_tokens_by_type: dict[str, int] = {}
    for i in all_items:
        etype = i.element_type
        content_tokens_by_type[etype] = (
            content_tokens_by_type.get(etype, 0) + i.content_tokens
        )

    cfm_total = sum(
        i.raw_score for i in all_items if i.source_model == "CFM"
    )
    csm_total = sum(
        i.raw_score for i in all_items if i.source_model == "CSM"
    )

    duration_ms = (time.monotonic() - start) * 1000

    total_elements = total_fp_count + total_cfm_non_fp + total_csm_count

    metadata = ExecutionMetadata(
        duration_ms=round(duration_ms, 2),
        total_elements_processed=total_elements,
        cfm_elements_processed=total_fp_count + total_cfm_non_fp,
        csm_elements_processed=total_csm_count,
        total_fps_processed=total_fp_count,
        fps_estimated=len([i for i in all_items if i.element_type == "functional_process"]),
        fps_merged_as_duplicates=total_merged,
        elements_without_base_weight=total_no_weight,
    )

    return StoryPointMeasurementResult(
        run_id=run_id,
        total_story_points=total_sp,
        total_raw_score=total_raw,
        specification_effort_total=csm_total,
        implementation_effort_total=cfm_total,
        content_multiplier=content_multiplier,
        content_tokens_by_type=content_tokens_by_type,
        calibration_version=cal.version,
        items=all_items,
        distribution=distribution,
        execution_metadata=metadata,
        warnings=warnings,
    )
