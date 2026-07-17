from __future__ import annotations

from datetime import datetime, timezone

import pytest

from specmetrics.plugins.measurement.storypoints.models import (
    EvidenceRef,
    ExecutionMetadata,
    FunctionalWorkItem,
    MeasurementEvidence,
    MeasurementWarning,
    RawEffortScore,
    StoryPointEstimate,
    StoryPointMeasurementResult,
)


def _sample_result() -> StoryPointMeasurementResult:
    return StoryPointMeasurementResult(
        run_id="test-run-001",
        total_story_points=8,
        items=[
            FunctionalWorkItem(
                element_id="fp-001",
                element_name="Process Order",
                raw_score=6.0,
                normalized_value=5,
                factor_breakdown={
                    "business_interactions": 1.0,
                    "logical_information": 2.0,
                    "workflow_breadth": 3.0,
                    "external_integrations": 0.0,
                    "business_rule_density": 0.0,
                    "exception_handling": 0.0,
                },
            ),
            FunctionalWorkItem(
                element_id="fp-002",
                element_name="Validate Payment",
                raw_score=3.0,
                normalized_value=3,
                factor_breakdown={
                    "business_interactions": 1.0,
                    "logical_information": 1.0,
                    "workflow_breadth": 1.0,
                    "external_integrations": 0.0,
                    "business_rule_density": 0.0,
                    "exception_handling": 0.0,
                },
            ),
        ],
        distribution={5: 1, 3: 1},
        execution_metadata=ExecutionMetadata(
            duration_ms=10.0,
            total_fps_processed=2,
            fps_estimated=2,
            fps_merged_as_duplicates=0,
        ),
    )


class TestStoryPointMeasurementResult:
    def test_construct_minimal(self):
        r = _sample_result()
        assert r.run_id == "test-run-001"
        assert r.total_story_points == 8
        assert r.method == "StoryPoints"
        assert r.scale == "ModifiedFibonacci"
        assert len(r.items) == 2
        assert r.distribution == {5: 1, 3: 1}

    def test_serialization_roundtrip(self):
        r = _sample_result()
        d = r.model_dump()
        restored = StoryPointMeasurementResult.model_validate(d)
        assert restored.run_id == r.run_id
        assert restored.total_story_points == r.total_story_points

    def test_validation_total_mismatch(self):
        with pytest.raises(ValueError, match="total_story_points"):
            StoryPointMeasurementResult(
                run_id="test",
                total_story_points=999,
                items=[
                    FunctionalWorkItem(
                        element_id="fp-001",
                        element_name="Test",
                        raw_score=5.0,
                        normalized_value=5,
                        factor_breakdown={
                            "business_interactions": 5.0,
                            "logical_information": 0.0,
                            "external_integrations": 0.0,
                            "business_rule_density": 0.0,
                            "workflow_breadth": 0.0,
                            "exception_handling": 0.0,
                        },
                    )
                ],
                distribution={5: 1},
                execution_metadata=ExecutionMetadata(
                    total_fps_processed=1, fps_estimated=1
                ),
            )

    def test_validation_distribution_mismatch(self):
        with pytest.raises(ValueError, match="distribution"):
            StoryPointMeasurementResult(
                run_id="test",
                total_story_points=5,
                items=[
                    FunctionalWorkItem(
                        element_id="fp-001",
                        element_name="Test",
                        raw_score=5.0,
                        normalized_value=5,
                        factor_breakdown={
                            "business_interactions": 5.0,
                            "logical_information": 0.0,
                            "external_integrations": 0.0,
                            "business_rule_density": 0.0,
                            "workflow_breadth": 0.0,
                            "exception_handling": 0.0,
                        },
                    )
                ],
                distribution={3: 1},
                execution_metadata=ExecutionMetadata(
                    total_fps_processed=1, fps_estimated=1
                ),
            )

    def test_validation_empty_run_id(self):
        with pytest.raises(ValueError, match="run_id"):
            StoryPointMeasurementResult(
                run_id="",
                total_story_points=0,
                items=[],
                distribution={},
                execution_metadata=ExecutionMetadata(),
            )

    def test_measured_at_defaults_to_now(self):
        r = _sample_result()
        assert isinstance(r.measured_at, datetime)
        assert r.measured_at.tzinfo == timezone.utc


class TestFunctionalWorkItem:
    def test_construct(self):
        item = FunctionalWorkItem(
            element_id="fp-001",
            element_name="Login",
            raw_score=5.0,
            normalized_value=5,
            factor_breakdown={
                "business_interactions": 5.0,
                "logical_information": 0.0,
                "external_integrations": 0.0,
                "business_rule_density": 0.0,
                "workflow_breadth": 0.0,
                "exception_handling": 0.0,
            },
        )
        assert item.element_id == "fp-001"
        assert item.raw_score == 5.0
        assert item.normalized_value == 5

    def test_validation_raw_score_mismatch(self):
        with pytest.raises(ValueError, match="raw_score"):
            FunctionalWorkItem(
                element_id="fp-001",
                element_name="Test",
                raw_score=100.0,
                normalized_value=5,
                factor_breakdown={
                    "business_interactions": 5.0,
                    "logical_information": 0.0,
                    "external_integrations": 0.0,
                    "business_rule_density": 0.0,
                    "workflow_breadth": 0.0,
                    "exception_handling": 0.0,
                },
            )

    def test_with_evidence_refs(self):
        ref = EvidenceRef(
            graph_node_id="gn-001", document_id="doc-001", text="evidence"
        )
        item = FunctionalWorkItem(
            element_id="fp-001",
            element_name="Login",
            raw_score=5.0,
            normalized_value=5,
            factor_breakdown={
                "business_interactions": 5.0,
                "logical_information": 0.0,
                "external_integrations": 0.0,
                "business_rule_density": 0.0,
                "workflow_breadth": 0.0,
                "exception_handling": 0.0,
            },
            evidence_refs=[ref],
        )
        assert len(item.evidence_refs) == 1
        assert item.evidence_refs[0].graph_node_id == "gn-001"

    def test_applied_rules(self):
        item = FunctionalWorkItem(
            element_id="fp-001",
            element_name="Login",
            raw_score=5.0,
            normalized_value=5,
            factor_breakdown={
                "business_interactions": 5.0,
                "logical_information": 0.0,
                "external_integrations": 0.0,
                "business_rule_density": 0.0,
                "workflow_breadth": 0.0,
                "exception_handling": 0.0,
            },
            applied_rules=["custom:business_interactions=2.0"],
        )
        assert "custom:business_interactions=2.0" in item.applied_rules


class TestExecutionMetadata:
    def test_defaults(self):
        meta = ExecutionMetadata()
        assert meta.duration_ms == 0.0
        assert meta.total_fps_processed == 0
        assert meta.fps_estimated == 0
        assert meta.fps_merged_as_duplicates == 0
        assert meta.version == "1.0"

    def test_validation_count_mismatch(self):
        with pytest.raises(ValueError, match="total_fps_processed"):
            ExecutionMetadata(
                total_fps_processed=10,
                fps_estimated=5,
                fps_merged_as_duplicates=2,
            )

    def test_valid_counts(self):
        meta = ExecutionMetadata(
            total_fps_processed=10,
            fps_estimated=7,
            fps_merged_as_duplicates=3,
        )
        assert meta.fps_estimated == 7
        assert meta.fps_merged_as_duplicates == 3


class TestMeasurementWarning:
    def test_minimal(self):
        warn = MeasurementWarning(code="TEST", message="test warning")
        assert warn.code == "TEST"
        assert warn.element_id is None

    def test_with_element_id(self):
        warn = MeasurementWarning(
            code="MISSING_CFM",
            message="CFM not available",
            element_id="fp-001",
        )
        assert warn.element_id == "fp-001"


class TestRawEffortScore:
    def test_construct(self):
        score = RawEffortScore(
            value=10.0,
            factor_breakdown={
                "business_interactions": 3.0,
                "logical_information": 4.0,
            },
            factor_coefficients={
                "business_interactions": 1.0,
                "logical_information": 1.0,
            },
        )
        assert score.value == 10.0
        assert score.factor_breakdown["business_interactions"] == 3.0


class TestStoryPointEstimate:
    def test_construct(self):
        est = StoryPointEstimate(
            value=8, raw_score=14.5,
            normalization_rule="default_threshold_v1",
        )
        assert est.value == 8
        assert est.raw_score == 14.5


class TestMeasurementEvidence:
    def test_construct(self):
        ev = MeasurementEvidence(
            element_id="fp-001",
            document_id="doc-001",
            text="System shall process orders",
        )
        assert ev.element_id == "fp-001"
        assert ev.applied_rule == ""

    def test_with_rule(self):
        ev = MeasurementEvidence(
            element_id="fp-001",
            document_id="doc-001",
            applied_rule="custom:v2",
            text="evidence text",
        )
        assert ev.applied_rule == "custom:v2"
