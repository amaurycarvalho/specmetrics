from __future__ import annotations

import time

from .bloom_classifier import DefaultBloomClassifier
from .calibration import CognitiveCalibrationProfile
from .fibonacci_normalizer import FibonacciNormalizer
from .models import (
    CognitiveContribution,
    CognitivePointsMeasurement,
    EvidenceRef,
    FunctionalValidationEffort,
    MeasurementMetadata,
    MeasurementWarning,
    SpecificationReviewEffort,
)


def _csm_evidence(evidence_refs: list) -> EvidenceRef | None:
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


def calculate(
    cfm,
    csm,
    calibration: CognitiveCalibrationProfile | None = None,
    run_id: str = "",
) -> CognitivePointsMeasurement:
    start = time.monotonic()
    warnings: list[MeasurementWarning] = []

    if calibration is None:
        from .calibration import get_default_calibration

        calibration = get_default_calibration()

    classifier = DefaultBloomClassifier(
        bloom_mappings=calibration.bloom_mappings,
        bloom_weights=calibration.bloom_levels,
        default_bloom_level=calibration.default_bloom_level,
    )

    normalizer = FibonacciNormalizer(
        thresholds=calibration.fibonacci_normalization.thresholds,
        output_values=calibration.fibonacci_normalization.output_values,
    )

    spec_contributions: list[CognitiveContribution] = []
    code_contributions: list[CognitiveContribution] = []
    bloom_counts: dict[str, int] = {}

    csm_element_count = 0
    cfm_element_count = 0

    if csm is not None:
        _process_csm(
            csm,
            classifier,
            spec_contributions,
            bloom_counts,
            warnings,
        )
        csm_element_count = len(spec_contributions)
    else:
        warnings.append(
            MeasurementWarning(
                code="MISSING_CSM",
                message="Canonical Specification Model (CSM) is not available. "
                "Specification Review Effort defaults to 0.",
            )
        )

    if cfm is not None:
        _process_cfm(
            cfm,
            classifier,
            code_contributions,
            bloom_counts,
            warnings,
        )
        cfm_element_count = len(code_contributions)
    else:
        warnings.append(
            MeasurementWarning(
                code="MISSING_CFM",
                message="Canonical Functional Model (CFM) is not available. "
                "Functional Validation Effort defaults to 0.",
            )
        )

    spec_raw = sum(c.partial_score for c in spec_contributions)
    code_raw = sum(c.partial_score for c in code_contributions)
    raw_score = spec_raw + code_raw

    fib_result = normalizer.normalize(raw_score)

    spec_bloom_breakdown: dict[str, int] = {}
    for c in spec_contributions:
        level = c.bloom_level
        spec_bloom_breakdown[level] = spec_bloom_breakdown.get(level, 0) + 1

    code_bloom_breakdown: dict[str, int] = {}
    for c in code_contributions:
        level = c.bloom_level
        code_bloom_breakdown[level] = code_bloom_breakdown.get(level, 0) + 1

    duration_ms = (time.monotonic() - start) * 1000

    metadata = MeasurementMetadata(
        total_elements_processed=csm_element_count + cfm_element_count,
        csm_element_count=csm_element_count,
        cfm_element_count=cfm_element_count,
        bloom_distribution=dict(bloom_counts),
        duration_ms=round(duration_ms, 2),
        warnings=warnings,
        calibration_profile_applied=calibration.version,
    )

    return CognitivePointsMeasurement(
        run_id=run_id,
        total_cognitive_points=fib_result.output_value,
        raw_score=raw_score,
        specification_review_effort=SpecificationReviewEffort(
            total_raw=spec_raw,
            contributions=spec_contributions,
            bloom_breakdown=spec_bloom_breakdown,
        ),
        functional_validation_effort=FunctionalValidationEffort(
            total_raw=code_raw,
            contributions=code_contributions,
            bloom_breakdown=code_bloom_breakdown,
        ),
        fibonacci_normalization=fib_result,
        calibration_version=calibration.version,
        measurement_metadata=metadata,
    )


def _process_csm(
    csm,
    classifier: DefaultBloomClassifier,
    spec_contributions: list[CognitiveContribution],
    bloom_counts: dict[str, int],
    warnings: list[MeasurementWarning],
) -> None:
    spec_data = [
        ("specification_activities", "activity_type", "description", "evidence_references"),
    ]

    for collection_name, type_attr, name_attr, evidence_attr in spec_data:
        collection = getattr(csm, collection_name, {})
        if isinstance(collection, dict):
            for elem_id, elem in collection.items():
                elem_type = getattr(elem, type_attr, "unknown")
                bloom_level = classifier.classify(elem_type)
                weight = classifier.get_weight(bloom_level)
                bloom_counts[bloom_level] = bloom_counts.get(bloom_level, 0) + 1
                name = (
                    getattr(elem, name_attr, None)
                    or str(elem_id)
                )
                evidence = getattr(elem, evidence_attr, [])
                spec_contributions.append(
                    CognitiveContribution(
                        element_id=str(elem_id),
                        element_type=str(elem_type),
                        element_name=str(name)[:80],
                        model_source="csm",
                        bloom_level=bloom_level,
                        cognitive_weight=weight,
                        partial_score=weight,
                        evidence_ref=_csm_evidence(evidence),
                    )
                )

    entity_collections = [
        "decisions", "assumptions", "constraints",
        "risks", "open_questions", "acceptance_criteria",
        "glossary_terms",
    ]
    for collection_name in entity_collections:
        collection = getattr(csm, collection_name, {})
        if isinstance(collection, dict):
            for elem_id, elem in collection.items():
                elem_type = collection_name.rstrip("s")
                bloom_level = classifier.classify(elem_type)
                weight = classifier.get_weight(bloom_level)
                bloom_counts[bloom_level] = bloom_counts.get(bloom_level, 0) + 1
                name = (
                    getattr(elem, "description", None)
                    or getattr(elem, "name", None)
                    or str(elem_id)
                )
                evidence = getattr(elem, "evidence_references", [])
                spec_contributions.append(
                    CognitiveContribution(
                        element_id=str(elem_id),
                        element_type=collection_name,
                        element_name=str(name)[:80],
                        model_source="csm",
                        bloom_level=bloom_level,
                        cognitive_weight=weight,
                        partial_score=weight,
                        evidence_ref=_csm_evidence(evidence),
                    )
                )


def _process_cfm(
    cfm,
    classifier: DefaultBloomClassifier,
    code_contributions: list[CognitiveContribution],
    bloom_counts: dict[str, int],
    warnings: list[MeasurementWarning],
) -> None:
    cfm_collections = [
        ("functional_processes", "functional_process"),
        ("business_rules", "business_rule"),
        ("operations", "operation"),
        ("data_groups", "data_group"),
        ("relationships", "relationship"),
        ("actors", "actor"),
    ]
    for collection_name, type_name in cfm_collections:
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
            bloom_level = classifier.classify(type_name)
            weight = classifier.get_weight(bloom_level)
            bloom_counts[bloom_level] = bloom_counts.get(bloom_level, 0) + 1
            name = (
                getattr(elem, "name", None)
                or getattr(elem, "description", None)
                or str(elem_id)
            )
            evidence = getattr(elem, "evidence", None)
            code_contributions.append(
                CognitiveContribution(
                    element_id=str(elem_id),
                    element_type=collection_name,
                    element_name=str(name)[:80],
                    model_source="cfm",
                    bloom_level=bloom_level,
                    cognitive_weight=weight,
                    partial_score=weight,
                    evidence_ref=_cfm_evidence(evidence),
                )
            )

    unk_count = len(getattr(cfm, "unclassified", []))
    if unk_count > 0:
        warnings.append(
            MeasurementWarning(
                code="UNKNOWN_CFM_ELEMENTS",
                message=f"{unk_count} CFM unclassified element(s) found with no configurable weight — excluded from Cognitive Points",
                details={"count": str(unk_count), "category": "unclassified"},
            )
        )
