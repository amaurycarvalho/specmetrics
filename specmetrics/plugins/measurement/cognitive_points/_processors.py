"""Model processors that build Cognitive Contributions from CFM and CSM."""
from __future__ import annotations

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.csm.model import CanonicalSpecificationModel

from ._contribution import build_contribution
from ._evidence import (
    cfm_evidence,
    csm_evidence,
    extract_content_text_cfm,
    extract_content_text_csm,
)
from .bloom_classifier import DefaultBloomClassifier
from .models import CognitiveContribution, MeasurementWarning


def process_csm(
    csm: CanonicalSpecificationModel,
    classifier: DefaultBloomClassifier,
    spec_contributions: list[CognitiveContribution],
    bloom_counts: dict[str, int],
    warnings: list[MeasurementWarning],
    content_multiplier: float,
) -> None:
    """Process CSM elements into specification review contributions."""
    _process_spec_activities(
        csm, classifier, spec_contributions, bloom_counts, content_multiplier
    )
    _process_csm_references(
        csm, classifier, spec_contributions, bloom_counts, content_multiplier
    )
    _process_csm_entities(
        csm, classifier, spec_contributions, bloom_counts, content_multiplier
    )


def _process_spec_activities(
    csm: CanonicalSpecificationModel,
    classifier: DefaultBloomClassifier,
    spec_contributions: list[CognitiveContribution],
    bloom_counts: dict[str, int],
    content_multiplier: float,
) -> None:
    collection_name = "specification_activities"
    type_attr = "activity_type"
    name_attr = "description"
    evidence_attr = "evidence_references"
    collection = getattr(csm, collection_name, {})
    if isinstance(collection, dict):
        for elem_id, elem in collection.items():
            elem_type = getattr(elem, type_attr, "unknown")
            bloom_level = classifier.classify(elem_type, elem)
            weight = classifier.get_weight(bloom_level)
            bloom_counts[bloom_level] = bloom_counts.get(bloom_level, 0) + 1
            name = getattr(elem, name_attr, None) or str(elem_id)
            evidence = getattr(elem, evidence_attr, [])
            content_text = extract_content_text_csm(elem)
            spec_contributions.append(
                build_contribution(
                    element_id=str(elem_id),
                    element_type=str(elem_type),
                    element_name=str(name)[:80],
                    model_source="csm",
                    bloom_level=bloom_level,
                    cognitive_weight=weight,
                    content_text=content_text,
                    content_multiplier=content_multiplier,
                    evidence_ref=csm_evidence(evidence),
                )
            )


def _process_csm_references(
    csm: CanonicalSpecificationModel,
    classifier: DefaultBloomClassifier,
    spec_contributions: list[CognitiveContribution],
    bloom_counts: dict[str, int],
    content_multiplier: float,
) -> None:
    for elem_id, elem in getattr(csm, "references", {}).items():
        elem_type = "references"
        bloom_level = classifier.classify(elem_type, elem)
        weight = classifier.get_weight(bloom_level)
        bloom_counts[bloom_level] = bloom_counts.get(bloom_level, 0) + 1
        evidence = getattr(elem, "evidence_references", [])
        content_text = (
            (getattr(elem, "title", None) or "")
            + " "
            + (getattr(elem, "url", None) or "")
        ).strip()
        spec_contributions.append(
            build_contribution(
                element_id=str(elem_id),
                element_type="references",
                element_name=str(elem_id),
                model_source="csm",
                bloom_level=bloom_level,
                cognitive_weight=weight,
                content_text=content_text,
                content_multiplier=content_multiplier,
                evidence_ref=csm_evidence(evidence),
            )
        )


def _process_csm_entities(
    csm: CanonicalSpecificationModel,
    classifier: DefaultBloomClassifier,
    spec_contributions: list[CognitiveContribution],
    bloom_counts: dict[str, int],
    content_multiplier: float,
) -> None:
    entity_collections = [
        "decisions",
        "assumptions",
        "constraints",
        "risks",
        "open_questions",
        "acceptance_criteria",
        "glossary_terms",
    ]
    for collection_name in entity_collections:
        collection = getattr(csm, collection_name, {})
        if isinstance(collection, dict):
            for elem_id, elem in collection.items():
                elem_type = collection_name.rstrip("s")
                bloom_level = classifier.classify(elem_type, elem)
                weight = classifier.get_weight(bloom_level)
                bloom_counts[bloom_level] = bloom_counts.get(bloom_level, 0) + 1
                name = (
                    getattr(elem, "description", None)
                    or getattr(elem, "name", None)
                    or str(elem_id)
                )
                evidence = getattr(elem, "evidence_references", [])
                content_text = extract_content_text_csm(elem)
                spec_contributions.append(
                    build_contribution(
                        element_id=str(elem_id),
                        element_type=collection_name,
                        element_name=str(name)[:80],
                        model_source="csm",
                        bloom_level=bloom_level,
                        cognitive_weight=weight,
                        content_text=content_text,
                        content_multiplier=content_multiplier,
                        evidence_ref=csm_evidence(evidence),
                    )
                )


def iter_cfm_collection_items(
    collection: object,
) -> list:
    """Iterate a CFM collection into (id, element) pairs."""
    if isinstance(collection, dict):
        return list(collection.items())
    if isinstance(collection, list):
        return [(getattr(e, "id", str(i)), e) for i, e in enumerate(collection)]
    return []


def process_cfm(
    cfm: CanonicalFunctionalModel,
    classifier: DefaultBloomClassifier,
    code_contributions: list[CognitiveContribution],
    bloom_counts: dict[str, int],
    warnings: list[MeasurementWarning],
    content_multiplier: float,
) -> None:
    """Process CFM elements into functional validation contributions."""
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
        items = iter_cfm_collection_items(collection)

        for elem_id, elem in items:
            bloom_level = classifier.classify(type_name, elem)
            weight = classifier.get_weight(bloom_level)
            bloom_counts[bloom_level] = bloom_counts.get(bloom_level, 0) + 1
            name = (
                getattr(elem, "name", None)
                or getattr(elem, "description", None)
                or str(elem_id)
            )
            evidence = getattr(elem, "evidence", None)
            content_text = extract_content_text_cfm(elem, collection_name)
            code_contributions.append(
                build_contribution(
                    element_id=str(elem_id),
                    element_type=collection_name,
                    element_name=str(name)[:80],
                    model_source="cfm",
                    bloom_level=bloom_level,
                    cognitive_weight=weight,
                    content_text=content_text,
                    content_multiplier=content_multiplier,
                    evidence_ref=cfm_evidence(evidence),
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