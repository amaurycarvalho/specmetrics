from __future__ import annotations

from datetime import UTC, datetime

import pytest

from specmetrics.plugins.measurement.bcp.models import (
    BCPMeasurementResult,
    BCPWorkItem,
    ExecutionMetadata,
    GeneratedStory,
    MeasurementEvidence,
    MeasurementWarning,
    SDKResult,
)


def _sample_result() -> BCPMeasurementResult:
    return BCPMeasurementResult(
        run_id="test-run-001",
        total_bcp=25.0,
        items=[
            BCPWorkItem(
                element_id="fp-001",
                element_name="Login",
                generated_story="# User Story: Login",
                bcp_score=15.0,
                component_breakdown={"business_logic": 8.0, "data": 7.0},
                status="success",
            ),
            BCPWorkItem(
                element_id="fp-002",
                element_name="Logout",
                generated_story="# User Story: Logout",
                bcp_score=10.0,
                component_breakdown={"business_logic": 5.0, "data": 5.0},
                status="success",
            ),
        ],
        execution_metadata=ExecutionMetadata(
            duration_ms=100.0,
            total_fps_processed=2,
            items_succeeded=2,
            sdk_call_count=2,
        ),
    )


class TestBCPMeasurementResult:
    def test_construct_minimal(self):
        r = _sample_result()
        assert r.run_id == "test-run-001"
        assert r.total_bcp == 25.0
        assert r.method == "BCP"
        assert len(r.items) == 2

    def test_serialization_roundtrip(self):
        r = _sample_result()
        d = r.model_dump()
        restored = BCPMeasurementResult.model_validate(d)
        assert restored.run_id == r.run_id
        assert restored.total_bcp == r.total_bcp

    def test_validation_total_mismatch(self):
        with pytest.raises(ValueError, match="total_bcp"):
            BCPMeasurementResult(
                run_id="test",
                total_bcp=999.0,
                items=[
                    BCPWorkItem(
                        element_id="fp-001",
                        element_name="A",
                        generated_story="# A",
                        bcp_score=15.0,
                        status="success",
                    )
                ],
                execution_metadata=ExecutionMetadata(
                    total_fps_processed=1,
                    items_succeeded=1,
                    sdk_call_count=1,
                ),
            )

    def test_validation_empty_run_id(self):
        with pytest.raises(ValueError, match="run_id"):
            BCPMeasurementResult(
                run_id="",
                total_bcp=0.0,
                items=[],
                execution_metadata=ExecutionMetadata(),
            )

    def test_measured_at_defaults_to_now(self):
        r = _sample_result()
        assert isinstance(r.measured_at, datetime)
        assert r.measured_at.tzinfo == UTC


class TestBCPWorkItem:
    def test_construct_success(self):
        item = BCPWorkItem(
            element_id="fp-001",
            element_name="Login",
            generated_story="# User Story: Login",
            bcp_score=15.0,
            status="success",
        )
        assert item.element_id == "fp-001"
        assert item.bcp_score == 15.0
        assert item.status == "success"

    def test_construct_failed(self):
        item = BCPWorkItem(
            element_id="fp-001",
            element_name="Login",
            generated_story="# User Story: Login",
            bcp_score=0.0,
            status="failed",
        )
        assert item.status == "failed"

    def test_with_component_breakdown(self):
        item = BCPWorkItem(
            element_id="fp-001",
            element_name="Login",
            generated_story="# User Story: Login",
            bcp_score=15.0,
            component_breakdown={"business_logic": 8.0, "data": 7.0},
            status="success",
        )
        assert item.component_breakdown["business_logic"] == 8.0


class TestExecutionMetadata:
    def test_defaults(self):
        meta = ExecutionMetadata()
        assert meta.duration_ms == 0.0
        assert meta.total_fps_processed == 0
        assert meta.items_succeeded == 0

    def test_validation_counts(self):
        with pytest.raises(ValueError, match="total_fps_processed"):
            ExecutionMetadata(
                total_fps_processed=10,
                items_succeeded=5,
                items_failed=2,
            )

    def test_valid_counts(self):
        meta = ExecutionMetadata(
            total_fps_processed=10,
            items_succeeded=7,
            items_failed=3,
            sdk_call_count=10,
        )
        assert meta.items_succeeded == 7


class TestGeneratedStory:
    def test_construct(self):
        ev = MeasurementEvidence(element_id="fp-001")
        story = GeneratedStory(
            content="# User Story: Login",
            evidence_ref=ev,
        )
        assert story.content == "# User Story: Login"
        assert story.evidence_ref.element_id == "fp-001"


class TestSDKResult:
    def test_construct(self):
        result = SDKResult(total_bcp=15.0, breakdown={"bl": 8.0})
        assert result.total_bcp == 15.0
        assert result.breakdown["bl"] == 8.0
        assert result.provider == "openai"


class TestMeasurementWarning:
    def test_minimal(self):
        warn = MeasurementWarning(code="TEST", message="test")
        assert warn.code == "TEST"


class TestMeasurementEvidence:
    def test_construct(self):
        ev = MeasurementEvidence(element_id="fp-001", document_id="doc-001")
        assert ev.element_id == "fp-001"
        assert ev.document_id == "doc-001"
