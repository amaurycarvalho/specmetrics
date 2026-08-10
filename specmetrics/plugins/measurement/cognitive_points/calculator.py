"""Cognitive Points calculation logic."""

from __future__ import annotations

import time

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.csm.model import CanonicalSpecificationModel

from ._processors import process_cfm, process_csm
from .bloom_classifier import DefaultBloomClassifier
from .calibration import CognitiveCalibrationProfile
from .fibonacci_normalizer import FibonacciNormalizer
from .models import (
    CognitiveContribution,
    CognitivePointsMeasurement,
    FunctionalValidationEffort,
    MeasurementMetadata,
    MeasurementWarning,
    SpecificationReviewEffort,
)


def calculate(
    cfm: CanonicalFunctionalModel | None,
    csm: CanonicalSpecificationModel | None,
    calibration: CognitiveCalibrationProfile | None = None,
    run_id: str = "",
) -> CognitivePointsMeasurement:
    """Calculate the Cognitive Points measurement from CFM and CSM models."""
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

    content_multiplier = calibration.content_multiplier

    spec_contributions: list[CognitiveContribution] = []
    code_contributions: list[CognitiveContribution] = []
    bloom_counts: dict[str, int] = {}

    csm_element_count = 0
    cfm_element_count = 0

    if csm is not None:
        process_csm(
            csm,
            classifier,
            spec_contributions,
            bloom_counts,
            warnings,
            content_multiplier,
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
        process_cfm(
            cfm,
            classifier,
            code_contributions,
            bloom_counts,
            warnings,
            content_multiplier,
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