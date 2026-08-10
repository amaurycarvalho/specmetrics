from __future__ import annotations

import time
import uuid

import pytest

from specmetrics.application.models import MetricOutputItem, PipelineResult
from specmetrics.cli.formatters import format_text_result
from specmetrics.kernel.cfm.model import (
    Actor,
    BusinessRule,
    CanonicalFunctionalModel,
    DataGroup,
    FunctionalProcess,
    Operation,
    Relationship,
)
from specmetrics.kernel.cfm.model import (
    BuildMetadata as CfmBuildMetadata,
)
from specmetrics.kernel.cfm.model import (
    EvidenceRef as CfmEvidenceRef,
)
from specmetrics.kernel.csm.model import (
    AcceptanceCriterion,
    Assumption,
    CanonicalSpecificationModel,
    Constraint,
    Decision,
    GlossaryTerm,
    OpenQuestion,
    Risk,
    SpecificationActivity,
)
from specmetrics.kernel.csm.model import (
    BuildMetadata as CsmBuildMetadata,
)
from specmetrics.kernel.csm.model import (
    EvidenceRef as CsmEvidenceRef,
)
from specmetrics.plugins.measurement.cognitive_points.calculator import (
    calculate,
)
from specmetrics.plugins.measurement.cognitive_points.calibration import (
    CognitiveCalibrationProfile,
)
from specmetrics.plugins.measurement.cognitive_points.models import (
    CognitivePointsMeasurement,
)


def _uid() -> str:
    return str(uuid.uuid4())


def _make_default_calibration() -> CognitiveCalibrationProfile:
    return CognitiveCalibrationProfile()


def _make_cfm_evidence() -> CfmEvidenceRef:
    return CfmEvidenceRef(
        graph_node_id="gn-cfm-001",
        document_id="doc-001",
        text="cfm evidence",
    )


def _make_csm_evidence() -> CsmEvidenceRef:
    return CsmEvidenceRef(
        graph_node_id="gn-csm-001",
        document_id="doc-001",
        text="csm evidence",
    )


def _make_cfm() -> CanonicalFunctionalModel:
    ev = _make_cfm_evidence()
    return CanonicalFunctionalModel(
        run_id="cfm-test-001",
        actors={
            _uid(): Actor(id=_uid(), name="User", actor_type="person", evidence=ev),
        },
        functional_processes={
            _uid(): FunctionalProcess(
                id=_uid(),
                name="Login",
                description="User login",
                actor_ids=[],
                operation_ids=[],
                evidence=ev,
            ),
        },
        business_rules={
            _uid(): BusinessRule(
                id=_uid(),
                name="Password Policy",
                description="Min 8 chars",
                evidence=ev,
            ),
        },
        data_groups={
            _uid(): DataGroup(id=_uid(), name="User Data", evidence=ev),
        },
        relationships=[
            Relationship(
                id=_uid(),
                source_id=_uid(),
                target_id=_uid(),
                relationship_type="triggers",
                evidence=ev,
            ),
        ],
        operations={
            _uid(): Operation(
                id=_uid(),
                name="Authenticate",
                parent_process_id=_uid(),
                evidence=ev,
            ),
        },
        metadata=CfmBuildMetadata(run_id="cfm-test-001", version="1.0", source="test"),
    )


def _make_csm() -> CanonicalSpecificationModel:
    ev = _make_csm_evidence()
    return CanonicalSpecificationModel(
        run_id="csm-test-001",
        specification_activities={
            _uid(): SpecificationActivity(
                id=_uid(),
                description="Initial exploration",
                activity_type="exploration",
                evidence_references=[ev],
            ),
            _uid(): SpecificationActivity(
                id=_uid(),
                description="Requirements clarification",
                activity_type="clarification",
                evidence_references=[ev],
            ),
        },
        decisions={
            _uid(): Decision(
                id=_uid(),
                description="Use PostgreSQL",
                evidence_references=[ev],
            ),
        },
        assumptions={
            _uid(): Assumption(
                id=_uid(),
                description="Users have internet",
                evidence_references=[ev],
            ),
        },
        constraints={
            _uid(): Constraint(
                id=_uid(),
                description="GDPR compliance",
                constraint_type="regulatory",
                evidence_references=[ev],
            ),
        },
        risks={
            _uid(): Risk(
                id=_uid(),
                description="Performance risk",
                evidence_references=[ev],
            ),
        },
        open_questions={
            _uid(): OpenQuestion(
                id=_uid(),
                description="Scaling strategy",
                evidence_references=[ev],
            ),
        },
        acceptance_criteria={
            _uid(): AcceptanceCriterion(
                id=_uid(),
                description="Login works",
                verification_method="test",
                evidence_references=[ev],
            ),
        },
        glossary_terms={
            _uid(): GlossaryTerm(
                id=_uid(),
                description="SLA definition",
                evidence_references=[ev],
            ),
        },
        metadata=CsmBuildMetadata(run_id="csm-test-001", version="1.0", source="test"),
    )


class TestCalculateFromKnownModels:
    def test_calculate_from_known_models(self):
        cfm = _make_cfm()
        csm = _make_csm()
        calibration = _make_default_calibration()
        result = calculate(cfm, csm, calibration, run_id="test-run-001")
        assert isinstance(result, CognitivePointsMeasurement)
        assert result.run_id == "test-run-001"
        assert result.total_cognitive_points > 0
        assert result.raw_score > 0
        assert result.specification_review_effort.total_raw > 0
        assert result.functional_validation_effort.total_raw > 0
        assert len(result.specification_review_effort.contributions) > 0
        assert len(result.functional_validation_effort.contributions) > 0

    def test_deterministic(self):
        cfm = _make_cfm()
        csm = _make_csm()
        calibration = _make_default_calibration()
        result1 = calculate(cfm, csm, calibration, run_id="det-test")
        result2 = calculate(cfm, csm, calibration, run_id="det-test")
        d1 = result1.model_dump()
        d2 = result2.model_dump()
        d1.pop("measured_at", None)
        d2.pop("measured_at", None)
        d1["measurement_metadata"]["duration_ms"] = 0
        d2["measurement_metadata"]["duration_ms"] = 0
        assert d1 == d2

    def test_missing_csm(self):
        cfm = _make_cfm()
        calibration = _make_default_calibration()
        result = calculate(cfm, None, calibration, run_id="no-csm")
        assert result.specification_review_effort.total_raw == 0.0
        assert result.functional_validation_effort.total_raw > 0
        warning_codes = [w.code for w in result.measurement_metadata.warnings]
        assert "MISSING_CSM" in warning_codes

    def test_missing_cfm(self):
        csm = _make_csm()
        calibration = _make_default_calibration()
        result = calculate(None, csm, calibration, run_id="no-cfm")
        assert result.functional_validation_effort.total_raw == 0.0
        assert result.specification_review_effort.total_raw > 0
        warning_codes = [w.code for w in result.measurement_metadata.warnings]
        assert "MISSING_CFM" in warning_codes

    def test_both_missing(self):
        calibration = _make_default_calibration()
        result = calculate(None, None, calibration, run_id="empty")
        assert result.raw_score == 0.0
        assert result.total_cognitive_points == 1
        assert result.specification_review_effort.total_raw == 0.0
        assert result.functional_validation_effort.total_raw == 0.0

    def test_metadata_tracks_counts(self):
        cfm = _make_cfm()
        csm = _make_csm()
        result = calculate(cfm, csm, _make_default_calibration(), run_id="meta")
        assert result.measurement_metadata.total_elements_processed > 0
        assert result.measurement_metadata.csm_element_count > 0
        assert result.measurement_metadata.cfm_element_count > 0
        assert result.measurement_metadata.total_elements_processed == (
            result.measurement_metadata.csm_element_count
            + result.measurement_metadata.cfm_element_count
        )

    def test_three_stage_formula(self):
        cfm = _make_cfm()
        csm = _make_csm()
        calibration = _make_default_calibration()
        result = calculate(cfm, csm, calibration, run_id="three-stage")
        spec_raw = result.specification_review_effort.total_raw
        func_raw = result.functional_validation_effort.total_raw
        assert result.raw_score == pytest.approx(spec_raw + func_raw)
        assert (
            result.total_cognitive_points == result.fibonacci_normalization.output_value
        )


class TestCustomCalibration:
    def test_custom_calibration_applied(self):
        from specmetrics.plugins.measurement.cognitive_points.calibration import (
            FibonacciNormalizationProfile,
        )

        cal = CognitiveCalibrationProfile(
            bloom_levels={"analyze": 6.0},
            bloom_mappings={"functional_process": "analyze"},
            fibonacci_normalization=FibonacciNormalizationProfile(
                thresholds=[100], output_values=[1, 5]
            ),
        )
        result = calculate(_make_cfm(), _make_csm(), cal, run_id="custom")
        fp = next(
            c
            for c in result.functional_validation_effort.contributions
            if c.element_type == "functional_processes"
        )
        assert fp.bloom_level == "analyze"
        assert fp.cognitive_weight == 6.0
        assert result.fibonacci_normalization.threshold_applied == 100
        assert result.fibonacci_normalization.output_value == 1

    def test_bloom_breakdown_exact_spec(self):
        result = calculate(
            None, _make_csm(), _make_default_calibration(), run_id="spec-bd"
        )
        assert result.specification_review_effort.bloom_breakdown == {
            "understand": 3,
            "analyze": 3,
            "evaluate": 1,
            "apply": 1,
            "remember": 1,
        }

    def test_bloom_breakdown_exact_cfm(self):
        result = calculate(
            _make_cfm(), None, _make_default_calibration(), run_id="cfm-bd"
        )
        assert result.functional_validation_effort.bloom_breakdown == {
            "create": 1,
            "apply": 2,
            "understand": 2,
            "remember": 1,
        }

    def test_empty_models_zero_counts(self):
        result = calculate(
            None, None, _make_default_calibration(), run_id="zero-counts"
        )
        assert result.measurement_metadata.csm_element_count == 0
        assert result.measurement_metadata.cfm_element_count == 0
        assert result.measurement_metadata.total_elements_processed == 0

    def test_missing_warning_exact_messages(self):
        result = calculate(None, None, _make_default_calibration(), run_id="warn")
        by_code = {w.code: w.message for w in result.measurement_metadata.warnings}
        assert by_code["MISSING_CSM"] == (
            "Canonical Specification Model (CSM) is not available. "
            "Specification Review Effort defaults to 0."
        )
        assert by_code["MISSING_CFM"] == (
            "Canonical Functional Model (CFM) is not available. "
            "Functional Validation Effort defaults to 0."
        )

    def test_default_calibration_when_none(self):
        result = calculate(None, None, run_id="default-cal")
        assert result.calibration_version == "1.0"
        assert result.total_cognitive_points == 1

    def test_unclassified_cfm_warning(self):
        from specmetrics.kernel.cfm.model import UnclassifiedElement

        ev = _make_cfm_evidence()
        cfm = _make_cfm()
        cfm = cfm.model_copy(
            update={
                "unclassified": {
                    "u1": UnclassifiedElement(
                        id="u1",
                        original_type="mystery",
                        content="something",
                        evidence=ev,
                    ),
                }
            }
        )
        result = calculate(cfm, None, _make_default_calibration(), run_id="unk")
        codes = [w.code for w in result.measurement_metadata.warnings]
        assert "UNKNOWN_CFM_ELEMENTS" in codes

    def test_duration_reported(self, monkeypatch):
        calls = iter([100.0, 100.123456])

        class FakeTime:
            @staticmethod
            def monotonic():
                return next(calls)

        import specmetrics.plugins.measurement.cognitive_points.calculator as mod

        monkeypatch.setattr(mod.time, "monotonic", FakeTime.monotonic)
        result = calculate(
            None, None, _make_default_calibration(), run_id="duration"
        )
        assert result.measurement_metadata.duration_ms == 123.46


class TestAggregation:
    def test_aggregate_summing(self):
        from specmetrics.plugins.measurement.cognitive_points.models import (
            aggregate,
        )

        cal = _make_default_calibration()
        cfm = _make_cfm()
        csm = _make_csm()
        m1 = calculate(cfm, csm, cal, run_id="m1")
        m2 = calculate(cfm, csm, cal, run_id="m2")
        aggregated = aggregate([m1, m2])
        assert aggregated.raw_score == pytest.approx(m1.raw_score + m2.raw_score)
        assert aggregated.specification_review_effort.total_raw == pytest.approx(
            m1.specification_review_effort.total_raw
            + m2.specification_review_effort.total_raw
        )
        assert aggregated.functional_validation_effort.total_raw == pytest.approx(
            m1.functional_validation_effort.total_raw
            + m2.functional_validation_effort.total_raw
        )


class TestPerformance:
    @pytest.mark.slow
    def test_performance_500_elements(self):
        ev = _make_cfm_evidence()
        ops = {}
        for i in range(250):
            uid = _uid()
            ops[uid] = Operation(
                id=uid,
                name=f"Process {i}",
                parent_process_id=_uid(),
                evidence=ev,
            )
        cfm = CanonicalFunctionalModel(
            run_id="perf-test",
            operations=ops,
            metadata=CfmBuildMetadata(run_id="perf-test", version="1.0", source="test"),
        )
        csm_ev = _make_csm_evidence()
        decisions = {}
        for i in range(250):
            uid = _uid()
            decisions[uid] = Decision(
                id=uid,
                description=f"Decision {i}",
                evidence_references=[csm_ev],
            )
        csm = CanonicalSpecificationModel(
            run_id="perf-test-csm",
            decisions=decisions,
            metadata=CsmBuildMetadata(
                run_id="perf-test-csm", version="1.0", source="test"
            ),
        )
        start = time.monotonic()
        calculate(cfm, csm, _make_default_calibration(), run_id="perf")
        elapsed = time.monotonic() - start
        assert elapsed < 2.0


class TestCognitivePointsCLIFormatter:
    def test_format_text_shows_breakdown_lines(self):
        result = PipelineResult(
            status="success",
            metric_results=[
                MetricOutputItem(name="cognitive_points", total=100.0),
            ],
            measurement_result_raw={
                "cognitive_bloom_breakdown": {
                    "remember": {"total": 10.0},
                    "understand": {"total": 30.0},
                    "apply": {"total": 60.0},
                },
            },
        )
        output = format_text_result(result)
        assert "Remember: 10.0" in output
        assert "Understand: 30.0" in output
        assert "Apply: 60.0" in output

    def test_format_text_no_breakdown_when_empty(self):
        result = PipelineResult(
            status="success",
            metric_results=[
                MetricOutputItem(name="cognitive_points", total=0.0),
            ],
            measurement_result_raw={},
        )
        output = format_text_result(result)
        assert "    " not in output or "Cognitive Points" in output

    def test_format_text_no_breakdown_when_missing_key(self):
        result = PipelineResult(
            status="success",
            metric_results=[
                MetricOutputItem(name="cognitive_points", total=50.0),
            ],
            measurement_result_raw={
                "cognitive_bloom_breakdown": {},
            },
        )
        output = format_text_result(result)
        lines = output.split("\n")
        cp_lines = [line for line in lines if "Cognitive Points" in line or line.startswith("    ")]
        assert any("Cognitive Points" in line for line in cp_lines)
        assert not any(line.startswith("    ") for line in cp_lines)
