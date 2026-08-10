"""Explanation builder for FPA measurement results."""

from __future__ import annotations

from typing import Self

from .models import (
    FPAMeasurementResult,
    MeasuredFunction,
    MeasurementExplanation,
)


class MeasurementExplainer:
    """Builds human-readable explanations for measured functions."""

    def build_explanations(
        self: Self, result: FPAMeasurementResult
    ) -> list[MeasurementExplanation]:
        """Build explanations for every measured function in the result."""
        explanations: list[MeasurementExplanation] = []

        for fn in result.measured_functions:
            explanation = self._explain_function(fn, result)
            explanations.append(explanation)

        return explanations

    def _explain_function(
        self: Self,
        fn: MeasuredFunction,
        result: FPAMeasurementResult,
    ) -> MeasurementExplanation:
        classification_reason = self._build_classification_reason(fn)
        complexity_reason = self._build_complexity_reason(fn)
        evidence_chain = self._build_evidence_chain(fn)

        rule_exceptions = [
            exp.rule_applied
            for exp in result.measured_functions
            if exp.id == fn.id and exp.rule_applied
        ]
        rule_exceptions = [r for r in rule_exceptions if r is not None]

        return MeasurementExplanation(
            function_id=fn.id,
            cfm_element_id=fn.cfm_element_id,
            cfm_element_name=fn.name,
            classification_reason=classification_reason,
            complexity_reason=complexity_reason,
            rule_exceptions=rule_exceptions,
            evidence_chain=evidence_chain,
        )

    def _build_classification_reason(self: Self, fn: MeasuredFunction) -> str:
        if fn.function_type in ("ILF", "EIF"):
            source = "DataGroup"
            subtype_map = {"ILF": "internal/shared", "EIF": "external"}
            subtype = subtype_map.get(fn.function_type, "unknown")
            return (
                f"CFM {source} '{fn.name}' with data_type='{subtype}' "
                f"→ classified as {fn.function_type}"
            )
        else:
            source = "Operation"
            dir_map = {"EI": "input", "EO": "output", "EQ": "query"}
            direction = dir_map.get(fn.function_type, "unknown")
            return (
                f"CFM {source} '{fn.name}' with direction='{direction}' "
                f"→ classified as {fn.function_type}"
            )

    def _build_complexity_reason(self: Self, fn: MeasuredFunction) -> str:
        if fn.function_type in ("ILF", "EIF"):
            ret = fn.ret_count or 0
            return (
                f"{fn.det_count} DETs × {ret} RETs → {fn.complexity} complexity "
                f"per IFPUG data function matrix, weight={fn.ufp_weight} UFP"
            )
        else:
            ftr = fn.ftr_count or 0
            return (
                f"{fn.det_count} DETs × {ftr} FTRs → {fn.complexity} complexity "
                f"per IFPUG {fn.function_type} matrix, weight={fn.ufp_weight} UFP"
            )

    def _build_evidence_chain(self: Self, fn: MeasuredFunction) -> list[str]:
        chain: list[str] = []
        for ref in fn.evidence_refs:
            section = f" (section {ref.section_id})" if ref.section_id else ""
            chain.append(
                f"document '{ref.document_id}'{section} → "
                f"graph node '{ref.graph_node_id}' → "
                f"CFM element '{fn.cfm_element_id}' → "
                f"measured function '{fn.id}'"
            )
        if not chain:
            chain.append(
                f"CFM element '{fn.cfm_element_id}' → measured function '{fn.id}' (no evidence graph refs)"
            )
        return chain
