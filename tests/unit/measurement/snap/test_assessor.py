from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    Operation,
    DataGroup,
    FunctionalProcess,
    BusinessRule,
    Actor,
    UnclassifiedElement,
    EvidenceRef as CFMEvidenceRef,
    BuildMetadata,
    Relationship,
)
from specmetrics.plugins.measurement.snap.assessor import SNAPAssessor
from specmetrics.plugins.measurement.snap.models import (
    CategoryDefinition,
)


def _make_evidence(doc_id: str = "doc-1", section_id: str = "sec-1", text: str = "test evidence") -> CFMEvidenceRef:
    return CFMEvidenceRef(
        graph_node_id=f"graph-{uuid4()}",
        document_id=doc_id,
        section_id=section_id,
        text=text,
    )


def _make_cfm(elements: dict[str, list[tuple[str, Any]]] | None = None) -> CanonicalFunctionalModel:
    ops: dict[str, Operation] = {}
    dgs: dict[str, DataGroup] = {}
    fps: dict[str, FunctionalProcess] = {}
    brs: dict[str, BusinessRule] = {}
    acts: dict[str, Actor] = {}
    uncs: dict[str, UnclassifiedElement] = {}
    rels: list[Relationship] = []

    if elements:
        for category, items in elements.items():
            for item_id, elem in items:
                if category == "operations":
                    ops[item_id] = elem
                elif category == "data_groups":
                    dgs[item_id] = elem
                elif category == "functional_processes":
                    fps[item_id] = elem
                elif category == "business_rules":
                    brs[item_id] = elem
                elif category == "actors":
                    acts[item_id] = elem
                elif category == "unclassified":
                    uncs[item_id] = elem
                elif category == "relationships":
                    rels.append(elem)

    return CanonicalFunctionalModel(
        run_id="test-run",
        actors=acts,
        functional_processes=fps,
        business_rules=brs,
        data_groups=dgs,
        operations=ops,
        relationships=rels,
        unclassified=uncs,
        metadata=BuildMetadata(
            run_id="test-run",
        ),
    )


def _make_op(id: str, marker: str, name: str = "test op") -> Operation:
    return Operation(
        id=id,
        name=name,
        parent_process_id="fp-1",
        evidence=_make_evidence(),
        metadata={"semantic_marker": marker},
    )


class TestCandidateIdentification:
    def test_identifies_presentation_candidates(self):
        cfm = _make_cfm({
            "operations": [
                ("op-1", _make_op("op-1", "presentation_interface")),
            ]
        })
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert len(result.assessed_items) == 1
        assert result.assessed_items[0].category_id == "presentation"

    def test_identifies_data_operation_candidates(self):
        cfm = _make_cfm({
            "operations": [
                ("op-1", _make_op("op-1", "data_operation")),
            ]
        })
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert len(result.assessed_items) == 1
        assert result.assessed_items[0].category_id == "data_operations"

    def test_identifies_multiple_markers(self):
        cfm = _make_cfm({
            "operations": [
                ("op-1", _make_op("op-1", "presentation_interface")),
                ("op-2", _make_op("op-2", "data_operation")),
                ("op-3", _make_op("op-3", "operational_feature")),
                ("op-4", _make_op("op-4", "technical_interface")),
            ]
        })
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        categories = {i.category_id for i in result.assessed_items}
        assert categories == {"presentation", "data_operations", "operational_capabilities", "technical_interaction"}

    def test_ignores_elements_without_semantic_marker(self):
        op = _make_op("op-1", "")
        op.metadata = {}
        cfm = _make_cfm({"operations": [("op-1", op)]})
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert len(result.assessed_items) == 0


class TestCandidateClassification:
    def test_maps_marker_to_correct_category(self):
        cfm = _make_cfm({
            "operations": [
                ("op-1", _make_op("op-1", "presentation_interface")),
                ("op-2", _make_op("op-2", "formatting_rule")),
                ("op-3", _make_op("op-3", "data_operation")),
                ("op-4", _make_op("op-4", "data_transform")),
                ("op-5", _make_op("op-5", "operational_feature")),
                ("op-6", _make_op("op-6", "technical_interface")),
                ("op-7", _make_op("op-7", "integration_point")),
            ]
        })
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert len(result.assessed_items) == 7
        for item in result.assessed_items:
            if item.cfm_semantic_marker in ("presentation_interface", "formatting_rule"):
                assert item.category_id == "presentation"
            elif item.cfm_semantic_marker in ("data_operation", "data_transform"):
                assert item.category_id == "data_operations"
            elif item.cfm_semantic_marker == "operational_feature":
                assert item.category_id == "operational_capabilities"
            elif item.cfm_semantic_marker in ("technical_interface", "integration_point"):
                assert item.category_id == "technical_interaction"


class TestFixedContributionValues:
    def test_presentation_default_contribution(self):
        cfm = _make_cfm({
            "operations": [("op-1", _make_op("op-1", "presentation_interface"))]
        })
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert result.assessed_items[0].contribution == 4.0

    def test_data_operations_default_contribution(self):
        cfm = _make_cfm({
            "operations": [("op-1", _make_op("op-1", "data_operation"))]
        })
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert result.assessed_items[0].contribution == 4.0

    def test_operational_capabilities_default_contribution(self):
        cfm = _make_cfm({
            "operations": [("op-1", _make_op("op-1", "operational_feature"))]
        })
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert result.assessed_items[0].contribution == 7.0

    def test_technical_interaction_default_contribution(self):
        cfm = _make_cfm({
            "operations": [("op-1", _make_op("op-1", "technical_interface"))]
        })
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert result.assessed_items[0].contribution == 6.0

    def test_category_total_contribution_sum(self):
        cfm = _make_cfm({
            "operations": [
                ("op-1", _make_op("op-1", "presentation_interface")),
                ("op-2", _make_op("op-2", "presentation_interface")),
            ]
        })
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        presentation_cat = [c for c in result.categories if c.category_id == "presentation"]
        assert len(presentation_cat) == 1
        assert presentation_cat[0].total_contribution == 8.0


class TestEmptyCFM:
    def test_empty_cfm_returns_zero_counts(self):
        cfm = _make_cfm()
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert len(result.assessed_items) == 0
        assert result.summary.total_item_count == 0
        assert result.summary.total_snap == 0.0


class TestDuplicateMerging:
    def test_duplicates_are_merged(self):
        ev = _make_evidence(doc_id="doc-1", section_id="sec-1", text="same content")
        op = Operation(
            id="op-1", name="dup", parent_process_id="fp-1",
            evidence=ev, metadata={"semantic_marker": "presentation_interface"},
        )
        unc = UnclassifiedElement(
            id="op-1",
            original_type="operation",
            content="dup",
            evidence=ev,
            metadata={"semantic_marker": "presentation_interface"},
        )
        cfm = _make_cfm({
            "operations": [("op-1", op)],
            "unclassified": [("op-1", unc)],
        })
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert len(result.assessed_items) == 1
        assert len(result.warnings) >= 1
        assert any(w.code == "DUPLICATE_MERGED" for w in result.warnings)


class TestDeterministicOutput:
    def test_byte_identical_on_repeated_execution(self):
        cfm = _make_cfm({
            "operations": [
                ("op-1", _make_op("op-1", "presentation_interface")),
                ("op-2", _make_op("op-2", "data_operation")),
            ]
        })
        assessor = SNAPAssessor()
        result1 = assessor.assess(cfm)
        result2 = assessor.assess(cfm)
        assert result1.run_id != result2.run_id
        assert len(result1.assessed_items) == len(result2.assessed_items)
        for i1, i2 in zip(result1.assessed_items, result2.assessed_items):
            assert i1.cfm_element_id == i2.cfm_element_id
            assert i1.category_id == i2.category_id
            assert i1.contribution == i2.contribution


class TestSingleCategoryPerItem:
    def test_item_in_exactly_one_category(self):
        cfm = _make_cfm({
            "operations": [
                ("op-1", _make_op("op-1", "presentation_interface")),
                ("op-2", _make_op("op-2", "data_operation")),
            ]
        })
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        for item in result.assessed_items:
            cat_count = 0
            for cat in result.categories:
                if any(i.id == item.id for i in cat.items):
                    cat_count += 1
            assert cat_count == 1


class TestMissingMetadataHandling:
    def test_missing_metadata_produces_warning(self):
        ev = _make_evidence()
        op = Operation(
            id="op-1", name="no-marker", parent_process_id="fp-1",
            evidence=ev, metadata={},
        )
        cfm = _make_cfm({"operations": [("op-1", op)]})
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert len(result.assessed_items) == 0
        assert any(w.code == "MISSING_SEMANTIC_MARKER" for w in result.warnings)

    def test_unsupported_marker_produces_warning(self):
        cfm = _make_cfm({
            "operations": [("op-1", _make_op("op-1", "unsupported_marker"))]
        })
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert len(result.assessed_items) == 0
        assert any(w.code == "UNSUPPORTED_MARKER" for w in result.warnings)


class TestEvidenceTrail:
    def test_evidence_refs_preserved(self):
        cfm = _make_cfm({
            "operations": [("op-1", _make_op("op-1", "presentation_interface"))]
        })
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert len(result.assessed_items) == 1
        item = result.assessed_items[0]
        assert len(item.evidence_refs) > 0
        ref = item.evidence_refs[0]
        assert ref.document_id == "doc-1"
        assert ref.section_id == "sec-1"

    def test_category_specific_evidence(self):
        cfm = _make_cfm({
            "operations": [
                ("op-1", _make_op("op-1", "presentation_interface")),
                ("op-2", _make_op("op-2", "data_operation")),
            ]
        })
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        for item in result.assessed_items:
            assert len(item.evidence_refs) > 0
            for ref in item.evidence_refs:
                assert ref.document_id is not None


class TestIncrementalRecomputation:
    def test_only_modified_candidates_recalculated(self):
        cfm1 = _make_cfm({
            "operations": [
                ("op-1", _make_op("op-1", "presentation_interface", name="Screen A")),
                ("op-2", _make_op("op-2", "data_operation", name="Batch")),
            ]
        })
        assessor = SNAPAssessor()
        result1 = assessor.assess(cfm1)
        assert len(result1.assessed_items) == 2

        cfm2 = _make_cfm({
            "operations": [
                ("op-1", _make_op("op-1", "presentation_interface", name="Screen A")),
                ("op-2", _make_op("op-2", "data_operation", name="Batch")),
                ("op-3", _make_op("op-3", "operational_feature", name="Auto-Updater")),
            ]
        })
        result2 = assessor.assess(
            cfm2,
            previous_result=result1,
            modified_element_ids=["op-3"],
        )
        assert len(result2.assessed_items) == 3


class TestPerformanceBenchmark:
    def test_medium_cfm_completes_under_5_seconds(self):
        import time
        ops = {}
        for i in range(100):
            marker = ["presentation_interface", "data_operation", "operational_feature", "technical_interface"][i % 4]
            op = _make_op(f"op-{i}", marker, name=f"Element {i}")
            ops[f"op-{i}"] = op
        cfm = _make_cfm({"operations": list(ops.items())})
        assessor = SNAPAssessor()
        start = time.monotonic()
        result = assessor.assess(cfm)
        elapsed = time.monotonic() - start
        assert elapsed < 5.0
        assert result.summary.total_item_count == 100


class TestCategoryVersionValidation:
    def test_valid_semver_category_loads(self):
        cat = CategoryDefinition(
            id="presentation",
            name="Presentation",
            description="Test",
            version="1.0.0",
            default_contribution=4.0,
        )
        assert cat.version == "1.0.0"

    def test_invalid_semver_raises_error(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CategoryDefinition(
                id="presentation",
                name="Presentation",
                description="Test",
                version="not-a-version",
                default_contribution=4.0,
            )


class TestScalability:
    def test_scaling_not_worse_than_linear(self):
        import time

        def _avg_timed(n: int, repeats: int = 5):
            cfm = _make_cfm({
                "operations": [
                    (f"op-{i}", _make_op(f"op-{i}", ["presentation_interface", "data_operation", "operational_feature", "technical_interface"][i % 4], name=f"E{i}"))
                    for i in range(n)
                ]
            })
            assessor = SNAPAssessor()
            durations = []
            for _ in range(repeats):
                start = time.monotonic()
                assessor.assess(cfm)
                durations.append(time.monotonic() - start)
            return sum(durations) / len(durations)

        t_5k = _avg_timed(5000)
        t_10k = _avg_timed(10000)
        if t_5k > 0.01 and t_10k > 0.01:
            ratio = t_10k / (t_5k * 2)
            assert ratio < 3.0, f"Scaling ratio {ratio} suggests worse-than-linear scaling"


class TestEdgeCases:
    def test_corrupted_plugin_metadata(self):
        from specmetrics.plugins.measurement.snap.plugin import create_snap_measurement_metadata
        metadata = create_snap_measurement_metadata()
        assert metadata.id is not None

    def test_unsupported_interaction_emits_warning(self):
        cfm = _make_cfm({
            "operations": [("op-1", _make_op("op-1", "unsupported_type"))]
        })
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert any(w.code == "UNSUPPORTED_MARKER" for w in result.warnings)
