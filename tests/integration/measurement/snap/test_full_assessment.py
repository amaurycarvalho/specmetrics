from __future__ import annotations

from typing import Any

from specmetrics.kernel.cfm.model import (
    BuildMetadata,
    CanonicalFunctionalModel,
    Operation,
)
from specmetrics.kernel.cfm.model import (
    EvidenceRef as CFMEvidenceRef,
)
from specmetrics.plugins.measurement.snap.assessor import SNAPAssessor
from specmetrics.plugins.measurement.snap.models import (
    RulePack,
)


def _ev(
    doc_id: str = "doc-1", section: str = "sec-1", text: str = "evidence"
) -> CFMEvidenceRef:
    return CFMEvidenceRef(
        graph_node_id="graph-node-1",
        document_id=doc_id,
        section_id=section,
        text=text,
    )


def _cfm(**extra_elements: list[tuple[str, Any]]) -> CanonicalFunctionalModel:
    ops = {}
    fps = {}
    dgs = {}
    brs = {}
    acts = {}
    uncs = {}
    for category, items in extra_elements.items():
        for eid, elem in items:
            target = {
                "operations": ops,
                "functional_processes": fps,
                "data_groups": dgs,
                "business_rules": brs,
                "actors": acts,
                "unclassified": uncs,
            }.get(category)
            if target is not None:
                target[eid] = elem
    return CanonicalFunctionalModel(
        run_id="integration-test-run",
        actors=acts,
        functional_processes=fps,
        business_rules=brs,
        data_groups=dgs,
        operations=ops,
        unclassified=uncs,
        metadata=BuildMetadata(run_id="integration-test-run"),
    )


class TestFullAssessment:
    def test_basic_assessment_with_multiple_categories(self):
        cfm = _cfm(
            operations=[
                (
                    "op-1",
                    Operation(
                        id="op-1",
                        name="Login Screen",
                        parent_process_id="fp-1",
                        evidence=_ev(),
                        metadata={"semantic_marker": "presentation_interface"},
                    ),
                ),
                (
                    "op-2",
                    Operation(
                        id="op-2",
                        name="Save Record",
                        parent_process_id="fp-1",
                        evidence=_ev(),
                        metadata={"semantic_marker": "data_operation"},
                    ),
                ),
                (
                    "op-3",
                    Operation(
                        id="op-3",
                        name="Auto-Update",
                        parent_process_id="fp-1",
                        evidence=_ev(doc_id="doc-2"),
                        metadata={"semantic_marker": "operational_feature"},
                    ),
                ),
            ]
        )
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert result.cfm_run_id == "integration-test-run"
        assert len(result.assessed_items) == 3
        assert result.summary.total_item_count == 3
        assert result.summary.total_snap == 4.0 + 4.0 + 7.0
        assert len(result.categories) == 3
        cat_ids = {c.category_id for c in result.categories}
        assert cat_ids == {
            "presentation",
            "data_operations",
            "operational_capabilities",
        }

    def test_assessment_with_evidence_refs(self):
        cfm = _cfm(
            operations=[
                (
                    "op-1",
                    Operation(
                        id="op-1",
                        name="Report",
                        parent_process_id="fp-1",
                        evidence=_ev(
                            doc_id="spec.pdf", section="3.2", text="report generation"
                        ),
                        metadata={"semantic_marker": "presentation_interface"},
                    ),
                ),
            ]
        )
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert len(result.assessed_items) == 1
        item = result.assessed_items[0]
        assert len(item.evidence_refs) > 0
        ref = item.evidence_refs[0]
        assert ref.document_id == "spec.pdf"
        assert ref.section_id == "3.2"

    def test_empty_cfm(self):
        cfm = _cfm()
        assessor = SNAPAssessor()
        result = assessor.assess(cfm)
        assert len(result.assessed_items) == 0
        assert result.summary.total_item_count == 0
        assert result.summary.total_snap == 0.0
        assert result.summary.total_active_count == 0

    def test_rule_pack_exclusion(self):
        cfm = _cfm(
            operations=[
                (
                    "op-1",
                    Operation(
                        id="op-1",
                        name="UI",
                        parent_process_id="fp-1",
                        evidence=_ev(),
                        metadata={"semantic_marker": "presentation_interface"},
                    ),
                ),
                (
                    "op-2",
                    Operation(
                        id="op-2",
                        name="Batch",
                        parent_process_id="fp-1",
                        evidence=_ev(doc_id="doc-2"),
                        metadata={"semantic_marker": "data_operation"},
                    ),
                ),
            ]
        )
        rule_pack = RulePack(
            id="test-rp",
            excluded_categories=["presentation"],
        )
        assessor = SNAPAssessor()
        result = assessor.assess(cfm, rule_pack=rule_pack)
        assert len(result.assessed_items) == 1
        assert result.assessed_items[0].category_id == "data_operations"
        assert result.summary.total_snap == 4.0

    def test_rule_pack_contribution_override(self):
        cfm = _cfm(
            operations=[
                (
                    "op-1",
                    Operation(
                        id="op-1",
                        name="UI",
                        parent_process_id="fp-1",
                        evidence=_ev(),
                        metadata={"semantic_marker": "presentation_interface"},
                    ),
                ),
            ]
        )
        rule_pack = RulePack(
            id="override-rp",
            contribution_overrides={"presentation": 10.0},
        )
        assessor = SNAPAssessor()
        result = assessor.assess(cfm, rule_pack=rule_pack)
        assert len(result.assessed_items) == 1
        assert result.assessed_items[0].contribution == 10.0

    def test_item_exclusion_by_id(self):
        cfm = _cfm(
            operations=[
                (
                    "op-1",
                    Operation(
                        id="op-1",
                        name="UI",
                        parent_process_id="fp-1",
                        evidence=_ev(),
                        metadata={"semantic_marker": "presentation_interface"},
                    ),
                ),
                (
                    "op-2",
                    Operation(
                        id="op-2",
                        name="Data",
                        parent_process_id="fp-1",
                        evidence=_ev(doc_id="doc-2"),
                        metadata={"semantic_marker": "data_operation"},
                    ),
                ),
            ]
        )
        rule_pack = RulePack(
            id="exclude-rp",
            item_exclusions={"by_id": ["op-1"]},
        )
        assessor = SNAPAssessor()
        result = assessor.assess(cfm, rule_pack=rule_pack)
        assert len(result.assessed_items) == 2
        excluded = [i for i in result.assessed_items if i.excluded]
        assert len(excluded) == 1
        assert excluded[0].cfm_element_id == "op-1"
        assert excluded[0].contribution == 0.0
        active = [i for i in result.assessed_items if not i.excluded]
        assert len(active) == 1
