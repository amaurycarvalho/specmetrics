from __future__ import annotations

from datetime import UTC, datetime

import pytest

from specmetrics.plugins.measurement.tshirt.models import (
    ExecutionMetadata,
    FunctionalWorkItem,
    MeasurementEvidence,
    MeasurementWarning,
    TShirtMeasurementResult,
    TShirtSize,
)


def _sample_result() -> TShirtMeasurementResult:
    return TShirtMeasurementResult(
        run_id="test-run-001",
        total_items=3,
        items=[
            FunctionalWorkItem(
                element_id="fp-001",
                element_name="Process A",
                story_point_value=3,
                tshirt_size="S",
            ),
            FunctionalWorkItem(
                element_id="fp-002",
                element_name="Process B",
                story_point_value=8,
                tshirt_size="M",
            ),
            FunctionalWorkItem(
                element_id="fp-003",
                element_name="Process C",
                story_point_value=20,
                tshirt_size="XL",
            ),
        ],
        distribution={"S": 1, "M": 1, "XL": 1},
        execution_metadata=ExecutionMetadata(duration_ms=1.0, total_fps_processed=3),
    )


class TestTShirtMeasurementResult:
    def test_construct_minimal(self):
        r = _sample_result()
        assert r.run_id == "test-run-001"
        assert r.total_items == 3
        assert r.method == "TShirtSizing"
        assert r.scale == "XS-S-M-L-XL-XXL"
        assert len(r.items) == 3
        assert r.distribution == {"S": 1, "M": 1, "XL": 1}

    def test_serialization_roundtrip(self):
        r = _sample_result()
        d = r.model_dump()
        restored = TShirtMeasurementResult.model_validate(d)
        assert restored.run_id == r.run_id
        assert restored.total_items == r.total_items

    def test_validation_total_mismatch(self):
        with pytest.raises(ValueError, match="total_items"):
            TShirtMeasurementResult(
                run_id="test",
                total_items=999,
                items=[
                    FunctionalWorkItem(
                        element_id="fp-001",
                        element_name="A",
                        story_point_value=3,
                        tshirt_size="S",
                    )
                ],
                distribution={"S": 1},
                execution_metadata=ExecutionMetadata(total_fps_processed=1),
            )

    def test_validation_distribution_mismatch(self):
        with pytest.raises(ValueError, match="distribution"):
            TShirtMeasurementResult(
                run_id="test",
                total_items=1,
                items=[
                    FunctionalWorkItem(
                        element_id="fp-001",
                        element_name="A",
                        story_point_value=3,
                        tshirt_size="S",
                    )
                ],
                distribution={"M": 1},
                execution_metadata=ExecutionMetadata(total_fps_processed=1),
            )

    def test_validation_empty_run_id(self):
        with pytest.raises(ValueError, match="run_id"):
            TShirtMeasurementResult(
                run_id="",
                total_items=0,
                items=[],
                distribution={},
                execution_metadata=ExecutionMetadata(),
            )

    def test_measured_at_defaults_to_now(self):
        r = _sample_result()
        assert isinstance(r.measured_at, datetime)
        assert r.measured_at.tzinfo == UTC


class TestFunctionalWorkItem:
    def test_construct(self):
        item = FunctionalWorkItem(
            element_id="fp-001",
            element_name="Login",
            story_point_value=8,
            tshirt_size="M",
        )
        assert item.element_id == "fp-001"
        assert item.story_point_value == 8
        assert item.tshirt_size == "M"
        assert item.applied_rule_pack == "default"

    def test_with_evidence(self):
        ev = MeasurementEvidence(
            element_id="fp-001",
            story_point_value=8,
            mapping_rule="default: 5-8 → M",
        )
        item = FunctionalWorkItem(
            element_id="fp-001",
            element_name="Login",
            story_point_value=8,
            tshirt_size="M",
            evidence_refs=[ev],
        )
        assert len(item.evidence_refs) == 1
        assert item.evidence_refs[0].mapping_rule == "default: 5-8 → M"

    def test_mapping_rule(self):
        item = FunctionalWorkItem(
            element_id="fp-001",
            element_name="Login",
            story_point_value=3,
            tshirt_size="S",
            mapping_rule="default: 2-3 → S",
        )
        assert item.mapping_rule == "default: 2-3 → S"


class TestTShirtSize:
    def test_construct(self):
        size = TShirtSize(label="M", story_point_range=(5, 8), ordinal=3)
        assert size.label == "M"
        assert size.story_point_range == (5, 8)
        assert size.ordinal == 3

    def test_validation_min_gt_max(self):
        with pytest.raises(ValueError, match="min ≤ max"):
            TShirtSize(
                label="Invalid",
                story_point_range=(10, 5),
                ordinal=1,
            )


class TestExecutionMetadata:
    def test_defaults(self):
        meta = ExecutionMetadata()
        assert meta.duration_ms == 0.0
        assert meta.total_fps_processed == 0
        assert meta.version == "1.0"


class TestMeasurementWarning:
    def test_minimal(self):
        warn = MeasurementWarning(code="TEST", message="test")
        assert warn.code == "TEST"
        assert warn.element_id is None

    def test_with_element_id(self):
        warn = MeasurementWarning(code="NO_SP", message="no sp", element_id="fp-001")
        assert warn.element_id == "fp-001"


class TestMeasurementEvidence:
    def test_construct(self):
        ev = MeasurementEvidence(
            element_id="fp-001",
            story_point_value=8,
            mapping_rule="default: 5-8 → M",
        )
        assert ev.element_id == "fp-001"
        assert ev.story_point_value == 8
