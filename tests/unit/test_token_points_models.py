from __future__ import annotations

from datetime import UTC, datetime

import pytest

from specmetrics.plugins.measurement.token_points.models import (
    CodeGenerationCost,
    EvidenceRef,
    MeasurementMetadata,
    MeasurementWarning,
    SpecificationCost,
    TokenContribution,
    TokenPointsMeasurement,
)


def _sample_measurement() -> TokenPointsMeasurement:
    return TokenPointsMeasurement(
        run_id="test-run-001",
        total_score=10.0,
        specification_cost=SpecificationCost(total=4.0, contributions=[]),
        code_generation_cost=CodeGenerationCost(total=6.0, contributions=[]),
        measurement_metadata=MeasurementMetadata(total_elements_processed=5),
    )


class TestTokenPointsMeasurement:
    def test_construct_minimal(self):
        m = _sample_measurement()
        assert m.run_id == "test-run-001"
        assert m.total_score == 10.0
        assert m.specification_cost.total == 4.0
        assert m.code_generation_cost.total == 6.0
        assert m.calibration_version == "1.0"

    def test_serialization_roundtrip(self):
        m = _sample_measurement()
        d = m.model_dump()
        restored = TokenPointsMeasurement.model_validate(d)
        assert restored.run_id == m.run_id
        assert restored.total_score == m.total_score

    def test_validation_total_mismatch(self):
        with pytest.raises(ValueError, match="total_score"):
            TokenPointsMeasurement(
                run_id="test",
                total_score=100.0,
                specification_cost=SpecificationCost(total=4.0),
                code_generation_cost=CodeGenerationCost(total=6.0),
                measurement_metadata=MeasurementMetadata(),
            )

    def test_validation_empty_run_id(self):
        with pytest.raises(ValueError, match="run_id"):
            TokenPointsMeasurement(
                run_id="",
                total_score=0.0,
                specification_cost=SpecificationCost(),
                code_generation_cost=CodeGenerationCost(),
                measurement_metadata=MeasurementMetadata(),
            )

    def test_measured_at_defaults_to_now(self):
        m = _sample_measurement()
        assert isinstance(m.measured_at, datetime)
        assert m.measured_at.tzinfo == UTC


class TestTokenContribution:
    def test_construct(self):
        contrib = TokenContribution(
            element_id="elem-001",
            element_type="functional_process",
            element_name="Login",
            model_source="cfm",
            applied_weight=5.0,
            partial_score=5.0,
        )
        assert contrib.element_id == "elem-001"
        assert contrib.model_source == "cfm"

    def test_with_evidence_ref(self):
        ref = EvidenceRef(
            graph_node_id="gn-001", document_id="doc-001", text="evidence"
        )
        contrib = TokenContribution(
            element_id="elem-001",
            element_type="decision",
            element_name="Decision 1",
            model_source="csm",
            applied_weight=1.5,
            partial_score=1.5,
            evidence_ref=ref,
        )
        assert contrib.evidence_ref is not None
        assert contrib.evidence_ref.graph_node_id == "gn-001"


class TestSpecificationCost:
    def test_default_total(self):
        cost = SpecificationCost()
        assert cost.total == 0.0
        assert cost.contributions == []

    def test_with_contributions(self):
        contribs = [
            TokenContribution(
                element_id="e1",
                element_type="decision",
                element_name="D1",
                model_source="csm",
                applied_weight=1.5,
                partial_score=1.5,
            ),
        ]
        cost = SpecificationCost(total=1.5, contributions=contribs)
        assert cost.total == 1.5
        assert len(cost.contributions) == 1


class TestCodeGenerationCost:
    def test_default_total(self):
        cost = CodeGenerationCost()
        assert cost.total == 0.0
        assert cost.contributions == []


class TestMeasurementMetadata:
    def test_defaults(self):
        meta = MeasurementMetadata()
        assert meta.total_elements_processed == 0
        assert meta.warnings == []

    def test_with_warnings(self):
        warn = MeasurementWarning(code="TEST", message="test warning")
        meta = MeasurementMetadata(warnings=[warn])
        assert len(meta.warnings) == 1
        assert meta.warnings[0].code == "TEST"


class TestMeasurementWarning:
    def test_minimal(self):
        warn = MeasurementWarning(code="MISSING_CSM", message="CSM not available")
        assert warn.code == "MISSING_CSM"
        assert warn.details is None

    def test_with_details(self):
        warn = MeasurementWarning(
            code="TEST",
            message="test",
            details={"key": "value"},
        )
        assert warn.details == {"key": "value"}


def _contribution(
    element_id: str,
    element_type: str,
    model_source: str,
    weight: float,
) -> TokenContribution:
    return TokenContribution(
        element_id=element_id,
        element_type=element_type,
        element_name=element_id,
        model_source=model_source,
        applied_weight=weight,
        partial_score=weight,
    )


def _measured(
    run_id: str,
    csm: int = 0,
    cfm: int = 0,
    unknown_csm: int = 0,
    unknown_cfm: int = 0,
    spec_contribs: tuple[TokenContribution, ...] = (),
    code_contribs: tuple[TokenContribution, ...] = (),
) -> TokenPointsMeasurement:
    spec_total = sum(c.partial_score for c in spec_contribs)
    code_total = sum(c.partial_score for c in code_contribs)
    return TokenPointsMeasurement(
        run_id=run_id,
        total_score=spec_total + code_total,
        specification_cost=SpecificationCost(
            total=spec_total, contributions=list(spec_contribs)
        ),
        code_generation_cost=CodeGenerationCost(
            total=code_total, contributions=list(code_contribs)
        ),
        measurement_metadata=MeasurementMetadata(
            total_elements_processed=csm + cfm,
            csm_element_count=csm,
            cfm_element_count=cfm,
            unknown_csm_element_count=unknown_csm,
            unknown_cfm_element_count=unknown_cfm,
        ),
    )


class TestAggregate:
    def test_aggregate_empty_raises(self):
        from specmetrics.plugins.measurement.token_points.models import aggregate

        with pytest.raises(ValueError, match="Cannot aggregate empty"):
            aggregate([])

    def test_aggregate_sums_counts_and_run_id(self):
        from specmetrics.plugins.measurement.token_points.models import aggregate

        m1 = _measured("a", csm=3, cfm=1)
        m2 = _measured("b", csm=1, cfm=2)
        agg = aggregate([m1, m2])
        assert agg.measurement_metadata.csm_element_count == 4
        assert agg.measurement_metadata.cfm_element_count == 3
        assert agg.measurement_metadata.total_elements_processed == 7
        assert agg.run_id == "aggregated:a,b"

    def test_aggregate_zero_init_counts(self):
        from specmetrics.plugins.measurement.token_points.models import aggregate

        m1 = _measured("a", csm=0, cfm=0)
        m2 = _measured("b", csm=0, cfm=0)
        agg = aggregate([m1, m2])
        assert agg.measurement_metadata.csm_element_count == 0
        assert agg.measurement_metadata.cfm_element_count == 0
        assert agg.measurement_metadata.total_elements_processed == 0

    def test_aggregate_counts_unknown(self):
        from specmetrics.plugins.measurement.token_points.models import aggregate

        m1 = _measured("a", csm=2, cfm=1, unknown_csm=1, unknown_cfm=2)
        m2 = _measured("b", csm=1, cfm=3, unknown_csm=2, unknown_cfm=1)
        agg = aggregate([m1, m2])
        assert agg.measurement_metadata.unknown_csm_element_count == 3
        assert agg.measurement_metadata.unknown_cfm_element_count == 3

    def test_aggregate_preserves_contributions(self):
        from specmetrics.plugins.measurement.token_points.models import aggregate

        c1 = _contribution("e1", "decision", "csm", 1.5)
        c2 = _contribution("e2", "operation", "cfm", 2.0)
        m1 = _measured("a", csm=1, cfm=0, spec_contribs=(c1,))
        m2 = _measured("b", csm=0, cfm=1, code_contribs=(c2,))
        agg = aggregate([m1, m2])
        assert [c.element_id for c in agg.specification_cost.contributions] == ["e1"]
        assert [c.element_id for c in agg.code_generation_cost.contributions] == ["e2"]

    def test_aggregate_totals_sum(self):
        from specmetrics.plugins.measurement.token_points.models import aggregate

        c1 = _contribution("e1", "decision", "csm", 1.5)
        c2 = _contribution("e2", "decision", "csm", 0.5)
        c3 = _contribution("e3", "operation", "cfm", 2.0)
        m1 = _measured("a", spec_contribs=(c1,), code_contribs=(c3,))
        m2 = _measured("b", spec_contribs=(c2,))
        agg = aggregate([m1, m2])
        assert agg.specification_cost.total == 2.0
        assert agg.code_generation_cost.total == 2.0
        assert agg.total_score == 4.0
