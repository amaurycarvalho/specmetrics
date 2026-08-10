"""Explanation builder for SFP measurement results."""

from __future__ import annotations

from typing import Self

from .models import (
    MeasuredComponent,
    MeasurementExplanation,
    SFPMeasurementResult,
)


class MeasurementExplainer:
    """Builds human-readable explanations for measured components."""

    def build_explanations(
        self: Self, result: SFPMeasurementResult
    ) -> list[MeasurementExplanation]:
        """Build explanations for every measured component in the result."""
        explanations: list[MeasurementExplanation] = []
        for component in result.measured_components:
            explanation = self._explain_component(component, result)
            explanations.append(explanation)
        return explanations

    def _explain_component(
        self: Self,
        component: MeasuredComponent,
        result: SFPMeasurementResult,
    ) -> MeasurementExplanation:
        identification_reason = self._build_identification_reason(component)
        contribution_reason = self._build_contribution_reason(component)
        evidence_chain = self._build_evidence_chain(component)
        rule_exceptions = [r for r in [component.rule_applied] if r is not None]
        return MeasurementExplanation(
            component_id=component.id,
            cfm_element_id=component.cfm_element_id,
            cfm_element_name=component.name,
            identification_reason=identification_reason,
            contribution_reason=contribution_reason,
            rule_exceptions=rule_exceptions,
            evidence_chain=evidence_chain,
        )

    def _build_identification_reason(self: Self, component: MeasuredComponent) -> str:
        if component.component_type == "functional_process":
            return (
                f"CFM element '{component.cfm_element_id}' of type "
                f"{component.cfm_element_type} → classified as Functional Process"
            )
        return (
            f"CFM element '{component.cfm_element_id}' of type "
            f"{component.cfm_element_type} → classified as Logical Function"
        )

    def _build_contribution_reason(self: Self, component: MeasuredComponent) -> str:
        if component.rule_applied:
            return (
                f"Contribution value {component.contribution} SFP assigned "
                f"via Rule Pack override (rule: {component.rule_applied})"
            )
        return (
            f"Default SFP weight for {component.component_type}: "
            f"{component.contribution} SFP"
        )

    def _build_evidence_chain(self: Self, component: MeasuredComponent) -> list[str]:
        chain: list[str] = []
        for ref in component.evidence_refs:
            section = f" (section {ref.section_id})" if ref.section_id else ""
            chain.append(
                f"document '{ref.document_id}'{section} → "
                f"graph node '{ref.graph_node_id}' → "
                f"CFM element '{component.cfm_element_id}' → "
                f"measured component '{component.id}'"
            )
        if not chain:
            chain.append(
                f"CFM element '{component.cfm_element_id}' → "
                f"measured component '{component.id}' (no evidence graph refs)"
            )
        return chain
