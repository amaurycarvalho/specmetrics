from __future__ import annotations

import hashlib
import time

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel, FunctionalProcess

from .factor_scorer import DEFAULT_FACTOR_COEFFICIENTS, score_all_factors
from .models import (
    EvidenceRef,
    ExecutionMetadata,
    FunctionalWorkItem,
    MeasurementWarning,
    StoryPointMeasurementResult,
)
from .normalizer import FibonacciNormalizer


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


def calculate(
    cfm: CanonicalFunctionalModel | None,
    run_id: str = "",
    coefficients: dict[str, float] | None = None,
    thresholds: list[float] | None = None,
    output_values: list[int] | None = None,
    previous_fingerprints: dict[str, str] | None = None,
) -> StoryPointMeasurementResult:
    start = time.monotonic()
    warnings: list[MeasurementWarning] = []

    if cfm is None:
        return StoryPointMeasurementResult(
            run_id=run_id,
            total_story_points=0,
            items=[],
            distribution={},
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

    coeffs = dict(DEFAULT_FACTOR_COEFFICIENTS)
    if coefficients:
        coeffs.update(coefficients)

    normalizer = FibonacciNormalizer(
        thresholds=thresholds,
        output_values=output_values,
    )

    seen_fingerprints: dict[str, bool] = {}
    items: list[FunctionalWorkItem] = []
    fp_count = 0
    merged_count = 0
    cached_count = 0

    for fp_id, fp in cfm.functional_processes.items():
        fp_count += 1
        fprint = _fingerprint(fp)

        if fprint in seen_fingerprints:
            merged_count += 1
            continue
        seen_fingerprints[fprint] = True

        if previous_fingerprints and fp_id in previous_fingerprints:
            if previous_fingerprints[fp_id] == fprint:
                cached_count += 1

        factor_scores = score_all_factors(fp_id, cfm, fp, coeffs)
        raw_score = sum(factor_scores.values())

        fib_result = normalizer.normalize(raw_score)

        applied_rules = ["default_coefficients_v1"]
        if coefficients:
            applied_rules = [f"custom_coefficients:{k}={v}" for k, v in coefficients.items()]

        items.append(
            FunctionalWorkItem(
                element_id=fp_id,
                element_name=fp.name,
                raw_score=raw_score,
                normalized_value=fib_result.output_value,
                factor_breakdown=factor_scores,
                applied_rules=applied_rules,
                evidence_refs=[_evidence_ref_from_fp(fp)],
            )
        )

    total_sp = sum(i.normalized_value for i in items)
    distribution: dict[int, int] = {}
    for i in items:
        distribution[i.normalized_value] = distribution.get(i.normalized_value, 0) + 1

    duration_ms = (time.monotonic() - start) * 1000

    metadata = ExecutionMetadata(
        duration_ms=round(duration_ms, 2),
        total_fps_processed=fp_count,
        fps_estimated=len(items),
        fps_merged_as_duplicates=merged_count,
    )

    return StoryPointMeasurementResult(
        run_id=run_id,
        total_story_points=total_sp,
        items=items,
        distribution=distribution,
        execution_metadata=metadata,
        warnings=warnings,
    )
