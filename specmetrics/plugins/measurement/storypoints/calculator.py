"""Story Points calculation logic."""

from __future__ import annotations

import time

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.csm.model import CanonicalSpecificationModel

from ._builders import build_cfm_non_fp_items, build_csm_items, build_fp_items
from .calibrator import StoryPointsCalibrationProfile, get_default_calibration
from .factor_scorer import DEFAULT_FACTOR_COEFFICIENTS
from .models import (
    ExecutionMetadata,
    MeasurementWarning,
    StoryPointMeasurementResult,
    WorkItem,
)
from .normalizer import RelativeRankingNormalizer


def calculate(
    cfm: CanonicalFunctionalModel | None,
    run_id: str = "",
    coefficients: dict[str, float] | None = None,
    previous_fingerprints: dict[str, str] | None = None,
    calibration: StoryPointsCalibrationProfile | None = None,
    csm: CanonicalSpecificationModel | None = None,
) -> StoryPointMeasurementResult:
    """Calculate the Story Points measurement from CFM and CSM models."""
    start = time.monotonic()
    warnings: list[MeasurementWarning] = []

    cal = calibration or get_default_calibration()
    content_multiplier = cal.content_multiplier

    if cfm is None and csm is None:
        return _missing_model_result(run_id, content_multiplier, cal)

    coeffs = _resolve_coeffs(cal, coefficients)

    all_items, counts = _build_all_items(
        cfm, csm, coeffs, coefficients, content_multiplier, cal, warnings
    )
    total_fp_count, total_merged, total_cfm_non_fp, total_csm_count, total_no_weight = counts

    scores_for_ranking = [(i.element_id, i.raw_score) for i in all_items]
    _apply_ranking(all_items, scores_for_ranking, cal)

    total_sp = sum(i.normalized_value for i in all_items)
    total_raw = sum(i.raw_score for i in all_items)
    cfm_total, csm_total = _split_totals(all_items)

    distribution, content_tokens_by_type, fps_estimated = _aggregate(all_items)

    duration_ms = (time.monotonic() - start) * 1000

    total_elements = total_fp_count + total_cfm_non_fp + total_csm_count

    metadata = ExecutionMetadata(
        duration_ms=round(duration_ms, 2),
        total_elements_processed=total_elements,
        cfm_elements_processed=total_fp_count + total_cfm_non_fp,
        csm_elements_processed=total_csm_count,
        total_fps_processed=total_fp_count,
        fps_estimated=fps_estimated,
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


def _resolve_coeffs(
    cal: StoryPointsCalibrationProfile,
    coefficients: dict[str, float] | None,
) -> dict[str, float]:
    """Resolve the effective factor coefficients."""
    base = cal.factor_coefficients or DEFAULT_FACTOR_COEFFICIENTS
    coeffs = dict(base)
    if coefficients:
        coeffs.update(coefficients)
    return coeffs


def _build_all_items(
    cfm: CanonicalFunctionalModel | None,
    csm: CanonicalSpecificationModel | None,
    coeffs: dict[str, float],
    coefficients: dict[str, float] | None,
    content_multiplier: float,
    cal: StoryPointsCalibrationProfile,
    warnings: list[MeasurementWarning],
) -> tuple[list[WorkItem], tuple[int, int, int, int, int]]:
    """Build all WorkItems from available CFM and CSM models."""
    all_items: list[WorkItem] = []
    total_fp, total_merged, total_non_fp, total_csm, total_no_weight = (0, 0, 0, 0, 0)

    fp_ids: set[str] = set()

    if cfm is not None:
        fp_ids = set(cfm.functional_processes.keys())
        fp_items, fp_warnings, fp_count, merged_count, _ = build_fp_items(
            cfm, coeffs, coefficients, content_multiplier, cal,
        )
        all_items.extend(fp_items)
        warnings.extend(fp_warnings)
        total_fp += fp_count
        total_merged += merged_count

        non_fp_items, non_fp_warnings, non_fp_count, no_weight_count = (
            build_cfm_non_fp_items(cfm, content_multiplier, cal, fp_ids)
        )
        all_items.extend(non_fp_items)
        warnings.extend(non_fp_warnings)
        total_non_fp += non_fp_count
        total_no_weight += no_weight_count

    if csm is not None:
        csm_items, csm_warnings, csm_count = build_csm_items(
            csm, content_multiplier, cal, fp_ids,
        )
        all_items.extend(csm_items)
        warnings.extend(csm_warnings)
        total_csm += csm_count

    if cfm is not None and not cfm.functional_processes:
        warnings.append(
            MeasurementWarning(
                code="NO_FPS_FOUND",
                message="No functional processes found in CFM. "
                "Only CSM and non-FP CFM elements contribute to estimation.",
            )
        )

    counts = (total_fp, total_merged, total_non_fp, total_csm, total_no_weight)
    return all_items, counts


def _split_totals(
    all_items: list[WorkItem],
) -> tuple[float, float]:
    """Split raw totals into CFM and CSM contributions."""
    cfm_total = sum(i.raw_score for i in all_items if i.source_model == "CFM")
    csm_total = sum(i.raw_score for i in all_items if i.source_model == "CSM")
    return cfm_total, csm_total


def _missing_model_result(
    run_id: str,
    content_multiplier: float,
    cal: StoryPointsCalibrationProfile,
) -> StoryPointMeasurementResult:
    """Return a zeroed result when neither CFM nor CSM is available."""
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


def _apply_ranking(
    all_items: list[WorkItem],
    scores_for_ranking: list[tuple[str, float]],
    cal: StoryPointsCalibrationProfile,
) -> None:
    """Apply relative ranking normalization to all items."""
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


def _aggregate(
    all_items: list[WorkItem],
) -> tuple[dict[int, int], dict[str, int], int]:
    """Aggregate distribution, token counts, and estimated FP count."""
    distribution: dict[int, int] = {}
    content_tokens_by_type: dict[str, int] = {}
    fps_estimated = 0
    for i in all_items:
        distribution[i.normalized_value] = (
            distribution.get(i.normalized_value, 0) + 1
        )
        etype = i.element_type
        content_tokens_by_type[etype] = (
            content_tokens_by_type.get(etype, 0) + i.content_tokens
        )
        if i.element_type == "functional_process":
            fps_estimated += 1
    return distribution, content_tokens_by_type, fps_estimated