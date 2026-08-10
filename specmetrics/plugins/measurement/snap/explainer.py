"""Explanation builder for SNAP assessment results."""

from __future__ import annotations

from typing import Self

from .models import AssessedItem, AssessmentExplanation, SNAPMeasurementResult


class AssessmentExplainer:
    """Builds human-readable explanations for assessed items."""

    def build_explanations(
        self: Self, result: SNAPMeasurementResult
    ) -> list[AssessmentExplanation]:
        """Build explanations for every assessed item in the result."""
        explanations: list[AssessmentExplanation] = []
        for item in result.assessed_items:
            explanation = self._explain_item(item, result)
            explanations.append(explanation)
        return explanations

    def _explain_item(
        self: Self,
        item: AssessedItem,
        result: SNAPMeasurementResult,
    ) -> AssessmentExplanation:
        identification_reason = self._build_identification_reason(item)
        contribution_reason = self._build_contribution_reason(item)
        evidence_chain = self._build_evidence_chain(item)
        rule_exceptions = [r for r in [item.rule_applied] if r is not None]
        return AssessmentExplanation(
            item_id=item.id,
            cfm_element_id=item.cfm_element_id,
            cfm_element_name=item.name,
            identification_reason=identification_reason,
            contribution_reason=contribution_reason,
            rule_exceptions=rule_exceptions,
            evidence_chain=evidence_chain,
        )

    def _build_identification_reason(self: Self, item: AssessedItem) -> str:
        return (
            f"CFM semantic marker='{item.cfm_semantic_marker}' on element "
            f"'{item.cfm_element_id}' → {item.category_id} category"
        )

    def _build_contribution_reason(self: Self, item: AssessedItem) -> str:
        if item.excluded:
            return "Item excluded by Rule Pack; contribution set to 0"
        if item.rule_applied and "excluded" not in item.rule_applied:
            return (
                f"Contribution value {item.contribution} SNAP assigned "
                f"via Rule Pack override (rule: {item.rule_applied})"
            )
        return f"Default SNAP weight for {item.category_id}: {item.contribution} SNAP"

    def _build_evidence_chain(self: Self, item: AssessedItem) -> list[str]:
        chain: list[str] = []
        for ref in item.evidence_refs:
            section = f" (section {ref.section_id})" if ref.section_id else ""
            chain.append(
                f"document '{ref.document_id}'{section} → "
                f"graph node '{ref.graph_node_id}' → "
                f"CFM element '{item.cfm_element_id}' → "
                f"assessed item '{item.id}'"
            )
        if not chain:
            chain.append(
                f"CFM element '{item.cfm_element_id}' → "
                f"assessed item '{item.id}' (no evidence graph refs)"
            )
        return chain
