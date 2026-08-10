from __future__ import annotations

from specmetrics.plugins.measurement.snap.explainer import AssessmentExplainer
from specmetrics.plugins.measurement.snap.models import AssessedItem, EvidenceRef


def _item(
    cfm_element_id: str = "elem-1",
    rule_applied: str | None = None,
    excluded: bool = False,
    contribution: float = 4.0,
    evidence_refs: list[EvidenceRef] | None = None,
) -> AssessedItem:
    return AssessedItem(
        id="snap-item-1",
        name=f"name-{cfm_element_id}",
        category_id="presentation",
        contribution=contribution,
        cfm_element_id=cfm_element_id,
        cfm_semantic_marker="presentation_interface",
        rule_applied=rule_applied,
        excluded=excluded,
        evidence_refs=evidence_refs or [],
    )


def _evidence(section_id: str | None = "sec-1") -> EvidenceRef:
    return EvidenceRef(
        graph_node_id="g-1",
        document_id="doc-1",
        section_id=section_id,
        text="evidence text",
    )


class TestContributionReason:
    def test_excluded_item_reason_exact(self) -> None:
        """Mutmut 1/2/3: excluded items use the exact contribution reason."""
        item = _item(excluded=True, contribution=0.0)
        reason = AssessmentExplainer()._build_contribution_reason(item)
        assert reason == "Item excluded by Rule Pack; contribution set to 0"

    def test_rule_applied_exclusion_slug_uses_default_reason(self) -> None:
        """Mutmut 5/6/7: a rule containing 'excluded' falls back to the default reason."""
        item = _item(rule_applied="excluded_by_id")
        reason = AssessmentExplainer()._build_contribution_reason(item)
        assert reason == "Default SNAP weight for presentation: 4.0 SNAP"

    def test_rule_override_reason(self) -> None:
        item = _item(rule_applied="weight_override")
        reason = AssessmentExplainer()._build_contribution_reason(item)
        assert "via Rule Pack override" in reason
        assert "weight_override" in reason


class TestEvidenceChain:
    def test_with_section(self) -> None:
        """Mutmut 2: a ref with a section id embeds it in the chain."""
        item = _item(evidence_refs=[_evidence("sec-9")])
        chain = AssessmentExplainer()._build_evidence_chain(item)
        assert "(section sec-9)" in chain[0]

    def test_without_section_omits_section(self) -> None:
        """Mutmut 3: a ref without a section omits the section fragment."""
        item = _item(evidence_refs=[_evidence(None)])
        chain = AssessmentExplainer()._build_evidence_chain(item)
        assert "(section" not in chain[0]
        assert "XXXX" not in chain[0]

    def test_no_evidence_uses_fallback(self) -> None:
        """Mutmut 5: an empty chain must use the no-evidence fallback."""
        item = _item(evidence_refs=[])
        chain = AssessmentExplainer()._build_evidence_chain(item)
        assert len(chain) == 1
        assert "no evidence graph refs" in chain[0]


class TestExplainItem:
    def test_rule_exceptions_preserved(self) -> None:
        """Mutmut 21: rule_exceptions must be forwarded into the explanation."""
        item = _item(rule_applied="weight_override")
        exp = AssessmentExplainer()._explain_item(item, None)
        assert exp.rule_exceptions == ["weight_override"]

    def test_evidence_chain_preserved(self) -> None:
        """Mutmut 22: evidence_chain must be forwarded into the explanation."""
        item = _item(evidence_refs=[_evidence("sec-1")])
        exp = AssessmentExplainer()._explain_item(item, None)
        assert len(exp.evidence_chain) == 1
        assert "document 'doc-1'" in exp.evidence_chain[0]
