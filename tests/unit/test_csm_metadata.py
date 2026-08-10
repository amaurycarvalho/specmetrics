from __future__ import annotations

from datetime import UTC, datetime

from specmetrics.kernel.csm.metadata import BuildMetadata, ClassificationConflict


class TestBuildMetadata:
    def test_default_construction(self):
        bm = BuildMetadata(run_id="run-1")
        assert bm.run_id == "run-1"
        assert bm.build_duration_ms == 0
        assert bm.element_counts == {}
        assert bm.total_input_nodes == 0
        assert bm.unclassified_count == 0
        assert bm.classification_conflicts == []
        assert isinstance(bm.created_at, datetime)
        assert bm.created_at.tzinfo is not None

    def test_element_counts(self):
        bm = BuildMetadata(
            run_id="run-1",
            element_counts={
                "decisions": 5,
                "assumptions": 3,
                "risks": 2,
            },
        )
        assert bm.element_counts["decisions"] == 5
        assert bm.element_counts["assumptions"] == 3
        assert bm.element_counts["risks"] == 2

    def test_with_classification_conflicts(self):
        conflicts = [
            ClassificationConflict(
                node_id="n1",
                competing_categories=["decision", "assumption"],
                resolved_category="decision",
                reason="Stronger pattern match on decision keywords",
            ),
        ]
        bm = BuildMetadata(run_id="run-1", classification_conflicts=conflicts)
        assert len(bm.classification_conflicts) == 1
        assert bm.classification_conflicts[0].node_id == "n1"
        assert bm.classification_conflicts[0].resolved_category == "decision"

    def test_created_at_utc(self):
        bm = BuildMetadata(run_id="run-1")
        assert bm.created_at.tzinfo == UTC


class TestClassificationConflict:
    def test_construction(self):
        cc = ClassificationConflict(
            node_id="n1",
            competing_categories=["decision", "assumption"],
            resolved_category="decision",
        )
        assert cc.node_id == "n1"
        assert cc.competing_categories == ["decision", "assumption"]
        assert cc.resolved_category == "decision"
        assert cc.reason == ""

    def test_with_reason(self):
        cc = ClassificationConflict(
            node_id="n1",
            competing_categories=["decision", "assumption"],
            resolved_category="decision",
            reason="Text matches decision pattern more strongly",
        )
        assert cc.reason == "Text matches decision pattern more strongly"
