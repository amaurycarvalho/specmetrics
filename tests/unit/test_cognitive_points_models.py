from __future__ import annotations

from datetime import UTC, datetime

import pytest

from specmetrics.plugins.measurement.cognitive_points.models import (
    CognitiveContribution,
    CognitivePointsMeasurement,
    EvidenceRef,
    FibonacciNormalizationResult,
    FunctionalValidationEffort,
    MeasurementMetadata,
    MeasurementWarning,
    SpecificationReviewEffort,
)


def _sample_measurement() -> CognitivePointsMeasurement:
    return CognitivePointsMeasurement(
        run_id="test-run-001",
        total_cognitive_points=8,
        raw_score=25.0,
        specification_review_effort=SpecificationReviewEffort(
            total_raw=10.0,
            contributions=[
                CognitiveContribution(
                    element_id="e1",
                    element_type="decision",
                    element_name="Decision 1",
                    model_source="csm",
                    bloom_level="evaluate",
                    cognitive_weight=5.0,
                    partial_score=5.0,
                ),
            ],
            bloom_breakdown={"evaluate": 1},
        ),
        functional_validation_effort=FunctionalValidationEffort(
            total_raw=15.0,
            contributions=[
                CognitiveContribution(
                    element_id="e2",
                    element_type="functional_process",
                    element_name="Login",
                    model_source="cfm",
                    bloom_level="create",
                    cognitive_weight=8.0,
                    partial_score=8.0,
                ),
            ],
            bloom_breakdown={"create": 1},
        ),
        fibonacci_normalization=FibonacciNormalizationResult(
            raw_score=25.0, threshold_applied=22, output_value=8
        ),
        measurement_metadata=MeasurementMetadata(total_elements_processed=6),
    )


class TestCognitivePointsMeasurement:
    def test_construct_minimal(self):
        m = _sample_measurement()
        assert m.run_id == "test-run-001"
        assert m.total_cognitive_points == 8
        assert m.raw_score == 25.0
        assert m.specification_review_effort.total_raw == 10.0
        assert m.functional_validation_effort.total_raw == 15.0
        assert m.calibration_version == "1.0"

    def test_serialization_roundtrip(self):
        m = _sample_measurement()
        d = m.model_dump()
        restored = CognitivePointsMeasurement.model_validate(d)
        assert restored.run_id == m.run_id
        assert restored.total_cognitive_points == m.total_cognitive_points
        assert restored.raw_score == m.raw_score

    def test_validation_raw_score_mismatch(self):
        with pytest.raises(ValueError, match="raw_score"):
            CognitivePointsMeasurement(
                run_id="test",
                total_cognitive_points=8,
                raw_score=100.0,
                specification_review_effort=SpecificationReviewEffort(total_raw=10.0),
                functional_validation_effort=FunctionalValidationEffort(total_raw=15.0),
                fibonacci_normalization=FibonacciNormalizationResult(
                    raw_score=25.0, threshold_applied=22, output_value=8
                ),
                measurement_metadata=MeasurementMetadata(),
            )

    def test_validation_empty_run_id(self):
        with pytest.raises(ValueError, match="run_id"):
            CognitivePointsMeasurement(
                run_id="",
                total_cognitive_points=1,
                raw_score=0.0,
                specification_review_effort=SpecificationReviewEffort(),
                functional_validation_effort=FunctionalValidationEffort(),
                fibonacci_normalization=FibonacciNormalizationResult(
                    raw_score=0.0, threshold_applied=0, output_value=1
                ),
                measurement_metadata=MeasurementMetadata(),
            )

    def test_measured_at_defaults_to_now(self):
        m = _sample_measurement()
        assert isinstance(m.measured_at, datetime)
        assert m.measured_at.tzinfo == UTC


class TestCognitiveContribution:
    def test_construct(self):
        contrib = CognitiveContribution(
            element_id="elem-001",
            element_type="functional_process",
            element_name="Login",
            model_source="cfm",
            bloom_level="create",
            cognitive_weight=8.0,
            partial_score=8.0,
        )
        assert contrib.element_id == "elem-001"
        assert contrib.model_source == "cfm"
        assert contrib.bloom_level == "create"

    def test_with_evidence_ref(self):
        ref = EvidenceRef(
            graph_node_id="gn-001", document_id="doc-001", text="evidence"
        )
        contrib = CognitiveContribution(
            element_id="elem-001",
            element_type="decision",
            element_name="Decision 1",
            model_source="csm",
            bloom_level="evaluate",
            cognitive_weight=5.0,
            partial_score=5.0,
            evidence_ref=ref,
        )
        assert contrib.evidence_ref is not None
        assert contrib.evidence_ref.graph_node_id == "gn-001"

    def test_evidence_ref_preserved(self):
        ref = EvidenceRef(
            graph_node_id="gn-002", document_id="doc-002", text="test evidence"
        )
        contrib = CognitiveContribution(
            element_id="e2",
            element_type="decision",
            element_name="D2",
            model_source="csm",
            bloom_level="evaluate",
            cognitive_weight=5.0,
            partial_score=5.0,
            evidence_ref=ref,
        )
        assert contrib.evidence_ref.graph_node_id == "gn-002"
        assert contrib.evidence_ref.document_id == "doc-002"


class TestSpecificationReviewEffort:
    def test_default_total(self):
        effort = SpecificationReviewEffort()
        assert effort.total_raw == 0.0
        assert effort.contributions == []
        assert effort.bloom_breakdown == {}

    def test_with_contributions(self):
        contribs = [
            CognitiveContribution(
                element_id="e1",
                element_type="decision",
                element_name="D1",
                model_source="csm",
                bloom_level="evaluate",
                cognitive_weight=5.0,
                partial_score=5.0,
            ),
        ]
        effort = SpecificationReviewEffort(
            total_raw=5.0,
            contributions=contribs,
            bloom_breakdown={"evaluate": 1},
        )
        assert effort.total_raw == 5.0
        assert len(effort.contributions) == 1
        assert effort.bloom_breakdown["evaluate"] == 1


class TestFunctionalValidationEffort:
    def test_default_total(self):
        effort = FunctionalValidationEffort()
        assert effort.total_raw == 0.0
        assert effort.contributions == []
        assert effort.bloom_breakdown == {}

    def test_with_contributions(self):
        contribs = [
            CognitiveContribution(
                element_id="e2",
                element_type="functional_process",
                element_name="Login",
                model_source="cfm",
                bloom_level="create",
                cognitive_weight=8.0,
                partial_score=8.0,
            ),
        ]
        effort = FunctionalValidationEffort(
            total_raw=8.0,
            contributions=contribs,
            bloom_breakdown={"create": 1},
        )
        assert effort.total_raw == 8.0
        assert len(effort.contributions) == 1


class TestMeasurementMetadata:
    def test_defaults(self):
        meta = MeasurementMetadata()
        assert meta.total_elements_processed == 0
        assert meta.warnings == []
        assert meta.bloom_distribution == {}

    def test_with_warnings(self):
        warn = MeasurementWarning(code="TEST", message="test warning")
        meta = MeasurementMetadata(warnings=[warn])
        assert len(meta.warnings) == 1
        assert meta.warnings[0].code == "TEST"

    def test_bloom_distribution(self):
        meta = MeasurementMetadata(bloom_distribution={"analyze": 5, "evaluate": 3})
        assert meta.bloom_distribution["analyze"] == 5
        assert meta.bloom_distribution["evaluate"] == 3


class TestMeasurementWarning:
    def test_minimal(self):
        warn = MeasurementWarning(code="MISSING_CSM", message="CSM not available")
        assert warn.code == "MISSING_CSM"
        assert warn.details is None

    def test_with_details(self):
        warn = MeasurementWarning(code="TEST", message="test", details={"key": "value"})
        assert warn.details == {"key": "value"}


class TestAggregate:
    def test_empty_raises_with_message(self):
        from specmetrics.plugins.measurement.cognitive_points.models import aggregate

        with pytest.raises(
            ValueError, match="Cannot aggregate empty list of measurements"
        ):
            aggregate([])

    def test_aggregate_merges_counts_and_breakdowns(self):
        from specmetrics.plugins.measurement.cognitive_points.models import aggregate

        def build(csm_count, cfm_count, bloom) -> CognitivePointsMeasurement:
            meta = MeasurementMetadata(
                total_elements_processed=csm_count + cfm_count,
                csm_element_count=csm_count,
                cfm_element_count=cfm_count,
                bloom_distribution=dict(bloom),
            )
            return CognitivePointsMeasurement(
                run_id=f"agg-{csm_count}-{cfm_count}",
                total_cognitive_points=1,
                raw_score=float(csm_count + cfm_count),
                specification_review_effort=SpecificationReviewEffort(
                    total_raw=float(csm_count),
                    bloom_breakdown={"understand": csm_count},
                ),
                functional_validation_effort=FunctionalValidationEffort(
                    total_raw=float(cfm_count),
                    bloom_breakdown={"create": cfm_count},
                ),
                fibonacci_normalization=FibonacciNormalizationResult(
                    raw_score=0.0, threshold_applied=0, output_value=1
                ),
                measurement_metadata=meta,
            )

        m1 = build(1, 1, {"understand": 1, "create": 1})
        m2 = build(2, 3, {"understand": 2, "create": 3})
        merged = aggregate([m1, m2])
        assert merged.measurement_metadata.csm_element_count == 3
        assert merged.measurement_metadata.cfm_element_count == 4
        assert merged.measurement_metadata.total_elements_processed == 7
        assert merged.measurement_metadata.bloom_distribution == {
            "understand": 3,
            "create": 4,
        }
        assert merged.specification_review_effort.bloom_breakdown == {"understand": 3}
        assert merged.functional_validation_effort.bloom_breakdown == {"create": 4}

    def test_aggregate_run_id_joins_ids(self):
        from specmetrics.plugins.measurement.cognitive_points.models import aggregate

        def build(run_id):
            return CognitivePointsMeasurement(
                run_id=run_id,
                total_cognitive_points=1,
                raw_score=1.0,
                specification_review_effort=SpecificationReviewEffort(total_raw=1.0),
                functional_validation_effort=FunctionalValidationEffort(),
                fibonacci_normalization=FibonacciNormalizationResult(
                    raw_score=1.0, threshold_applied=0, output_value=1
                ),
                measurement_metadata=MeasurementMetadata(),
            )

        merged = aggregate([build("r1"), build("r2")])
        assert merged.run_id == "aggregated:r1,r2"


class TestFibonacciNormalizationResult:
    def test_construct(self):
        result = FibonacciNormalizationResult(
            raw_score=42.5, threshold_applied=35, output_value=13
        )
        assert result.raw_score == 42.5
        assert result.threshold_applied == 35
        assert result.output_value == 13


class TestMergeContributions:
    def _merge_measurement(self, csm_count, cfm_count, bloom):
        meta = MeasurementMetadata(
            total_elements_processed=csm_count + cfm_count,
            csm_element_count=csm_count,
            cfm_element_count=cfm_count,
            bloom_distribution=dict(bloom),
        )
        return CognitivePointsMeasurement(
            run_id=f"mc-{csm_count}-{cfm_count}",
            total_cognitive_points=1,
            raw_score=float(csm_count + cfm_count),
            specification_review_effort=SpecificationReviewEffort(
                total_raw=float(csm_count),
                bloom_breakdown={"understand": csm_count},
            ),
            functional_validation_effort=FunctionalValidationEffort(
                total_raw=float(cfm_count),
                bloom_breakdown={"create": cfm_count},
            ),
            fibonacci_normalization=FibonacciNormalizationResult(
                raw_score=0.0, threshold_applied=0, output_value=1
            ),
            measurement_metadata=meta,
        )

    def test_empty_measurements_has_zero_totals(self):
        from specmetrics.plugins.measurement.cognitive_points.models import (
            _merge_contributions,
        )

        result = _merge_contributions([])
        assert result[2] == 0
        assert result[3] == 0
        assert result[4] == {}

    def test_csm_counts_summed_across_measurements(self):
        from specmetrics.plugins.measurement.cognitive_points.models import (
            _merge_contributions,
        )

        m1 = self._merge_measurement(2, 0, {})
        m2 = self._merge_measurement(3, 0, {})
        result = _merge_contributions([m1, m2])
        assert result[2] == 5

    def test_cfm_counts_summed_across_measurements(self):
        from specmetrics.plugins.measurement.cognitive_points.models import (
            _merge_contributions,
        )

        m1 = self._merge_measurement(0, 4, {})
        m2 = self._merge_measurement(0, 1, {})
        result = _merge_contributions([m1, m2])
        assert result[3] == 5

    def test_bloom_distribution_merged_with_sums(self):
        from specmetrics.plugins.measurement.cognitive_points.models import (
            _merge_contributions,
        )

        m1 = self._merge_measurement(1, 0, {"understand": 1, "create": 1})
        m2 = self._merge_measurement(1, 0, {"understand": 2, "analyze": 3})
        result = _merge_contributions([m1, m2])
        assert result[4] == {"understand": 3, "create": 1, "analyze": 3}

    def test_bloom_distribution_new_level_starts_at_zero(self):
        from specmetrics.plugins.measurement.cognitive_points.models import (
            _merge_contributions,
        )

        m1 = self._merge_measurement(1, 0, {"understand": 1})
        m2 = self._merge_measurement(1, 0, {"evaluate": 2})
        result = _merge_contributions([m1, m2])
        assert result[4] == {"understand": 1, "evaluate": 2}


class TestMergeBreakdown:
    def _measurement(self, breakdown):
        meta = MeasurementMetadata(total_elements_processed=1)
        return CognitivePointsMeasurement(
            run_id="mb",
            total_cognitive_points=1,
            raw_score=1.0,
            specification_review_effort=SpecificationReviewEffort(
                total_raw=1.0, bloom_breakdown=dict(breakdown)
            ),
            functional_validation_effort=FunctionalValidationEffort(),
            fibonacci_normalization=FibonacciNormalizationResult(
                raw_score=1.0, threshold_applied=0, output_value=1
            ),
            measurement_metadata=meta,
        )

    def test_breakdown_levels_merged_with_sums(self):
        from specmetrics.plugins.measurement.cognitive_points.models import (
            _merge_breakdown,
        )

        m1 = self._measurement({"understand": 1, "create": 1})
        m2 = self._measurement({"understand": 2, "evaluate": 1})
        merged = _merge_breakdown(
            [m1, m2], lambda m: m.specification_review_effort.bloom_breakdown
        )
        assert merged == {"understand": 3, "create": 1, "evaluate": 1}

    def test_breakdown_single_measurement_passthrough(self):
        from specmetrics.plugins.measurement.cognitive_points.models import (
            _merge_breakdown,
        )

        m1 = self._measurement({"apply": 2})
        merged = _merge_breakdown(
            [m1], lambda m: m.specification_review_effort.bloom_breakdown
        )
        assert merged == {"apply": 2}
