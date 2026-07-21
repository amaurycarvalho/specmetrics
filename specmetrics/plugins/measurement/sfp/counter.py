from __future__ import annotations

import hashlib
from typing import Optional
from uuid import uuid4

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel

from .models import (
    SFPMeasurementResult,
    ComponentType,
    EvidenceRef,
    MeasuredComponent,
    MeasurementSummary,
    MeasurementWarning,
    TypeBreakdown,
)

DEFAULT_FP_CONTRIBUTION = 4.6
DEFAULT_LF_CONTRIBUTION = 7.1


class SFPCounter:
    def count(
        self,
        cfm: CanonicalFunctionalModel,
        rule_pack_id: Optional[str] = None,
        contribution_overrides: Optional[dict[ComponentType, float]] = None,
        excluded_types: Optional[list[str]] = None,
        element_exclusions: Optional[dict[str, list[str]]] = None,
        element_inclusions: Optional[dict[str, list[str]]] = None,
        inclusion_criteria: Optional[dict[str, dict[str, list[str]]]] = None,
        run_id: Optional[str] = None,
        previous_result: Optional[SFPMeasurementResult] = None,
        modified_element_ids: Optional[list[str]] = None,
    ) -> SFPMeasurementResult:
        excluded = set(excluded_types or [])
        fp_contribution = (contribution_overrides or {}).get(
            "functional_process", DEFAULT_FP_CONTRIBUTION
        )
        lf_contribution = (contribution_overrides or {}).get(
            "logical_function", DEFAULT_LF_CONTRIBUTION
        )

        fp_criteria = (inclusion_criteria or {}).get("functional_process", {})
        lf_criteria = (inclusion_criteria or {}).get("logical_function", {})
        fp_node_types = set(fp_criteria.get("node_types", []) or [])
        lf_node_types = set(lf_criteria.get("node_types", []) or [])

        components: list[MeasuredComponent] = []
        warnings: list[MeasurementWarning] = []
        seen_fingerprints: dict[str, str] = {}

        excluded_ids = set(
            element_exclusions.get("by_id", []) if element_exclusions else []
        )
        excluded_patterns = (
            element_exclusions.get("by_pattern", []) if element_exclusions else []
        )

        included_ids = set(
            element_inclusions.get("by_id", []) if element_inclusions else []
        )
        included_patterns = (
            element_inclusions.get("by_pattern", []) if element_inclusions else []
        )

        import fnmatch

        def _is_excluded(element_id: str, element_name: str) -> bool:
            if element_id in excluded_ids:
                return True
            for pattern in excluded_patterns:
                if fnmatch.fnmatch(element_id, pattern) or fnmatch.fnmatch(
                    element_name, pattern
                ):
                    return True
            return False

        def _is_included(element_id: str, element_name: str) -> bool:
            if element_id in included_ids:
                return True
            for pattern in included_patterns:
                if fnmatch.fnmatch(element_id, pattern) or fnmatch.fnmatch(
                    element_name, pattern
                ):
                    return True
            return False

        def _is_fp(op) -> bool:
            node_type = op.metadata.get("node_type", "")
            if fp_node_types:
                return node_type in fp_node_types
            if node_type and node_type != "elementary_process":
                return False
            return True

        def _is_lf(dg) -> bool:
            node_type = dg.metadata.get("node_type", "")
            if lf_node_types:
                return node_type in lf_node_types
            if node_type and node_type != "data_group":
                return False
            return True

        def _fingerprint(element) -> str:
            raw = f"{element.evidence.document_id}:{element.evidence.section_id or ''}:{element.evidence.text}:{type(element).__name__}"
            return hashlib.sha256(raw.encode()).hexdigest()

        for op_id, op in cfm.operations.items():
            if "functional_process" in excluded:
                continue
            if _is_included(op.id, op.name):
                pass
            elif not _is_fp(op):
                continue
            if _is_excluded(op.id, op.name):
                continue

            fp = self._create_component(
                element=op,
                element_id=op.id,
                element_name=op.name,
                element_type_name="Operation",
                component_type="functional_process",
                contribution=fp_contribution,
                component_counter=len(components) + 1,
            )
            fp, warning = self._deduplicate(fp, seen_fingerprints, _fingerprint(op))
            if warning:
                warnings.append(warning)
            if fp is not None:
                components.append(fp)

        for dg_id, dg in cfm.data_groups.items():
            if "logical_function" in excluded:
                continue
            if _is_included(dg.id, dg.name):
                pass
            elif not _is_lf(dg):
                continue
            if _is_excluded(dg.id, dg.name):
                continue

            lf = self._create_component(
                element=dg,
                element_id=dg.id,
                element_name=dg.name,
                element_type_name="DataGroup",
                component_type="logical_function",
                contribution=lf_contribution,
                component_counter=len(components) + 1,
            )
            lf, warning = self._deduplicate(lf, seen_fingerprints, _fingerprint(dg))
            if warning:
                warnings.append(warning)
            if lf is not None:
                components.append(lf)

        if previous_result is not None and modified_element_ids is not None:
            modified_set = set(modified_element_ids)
            kept = [
                c
                for c in previous_result.measured_components
                if c.cfm_element_id not in modified_set
            ]
            for c in kept:
                if c.cfm_element_id not in {x.cfm_element_id for x in components}:
                    components.append(c)

        summary = self._build_summary(components)

        return SFPMeasurementResult(
            run_id=run_id or str(uuid4()),
            cfm_run_id=cfm.run_id,
            rule_pack_id=rule_pack_id,
            measured_components=components,
            summary=summary,
            warnings=warnings,
        )

    def _create_component(
        self,
        element,
        element_id: str,
        element_name: str,
        element_type_name: str,
        component_type: ComponentType,
        contribution: float,
        component_counter: int,
    ) -> MeasuredComponent:
        refs = [
            EvidenceRef(
                graph_node_id=element.evidence.graph_node_id,
                document_id=element.evidence.document_id,
                section_id=element.evidence.section_id,
                text=element.evidence.text,
            )
        ]
        return MeasuredComponent(
            id=f"cmp-{component_type}-{component_counter}",
            name=element_name,
            component_type=component_type,
            contribution=contribution,
            cfm_element_id=element_id,
            cfm_element_type=element_type_name,
            evidence_refs=refs,
        )

    def _deduplicate(
        self,
        component: MeasuredComponent,
        seen_fingerprints: dict[str, str],
        fingerprint: str,
    ) -> tuple[Optional[MeasuredComponent], Optional[MeasurementWarning]]:
        if fingerprint in seen_fingerprints:
            return None, MeasurementWarning(
                code="DUPLICATE_MERGED",
                message=f"Duplicate component '{component.name}' merged; only one counted",
                cfm_element_id=component.cfm_element_id,
                details={"merged_into": seen_fingerprints[fingerprint]},
            )
        seen_fingerprints[fingerprint] = component.id
        return component, None

    def _build_summary(self, components: list[MeasuredComponent]) -> MeasurementSummary:
        total_sfp = sum(c.contribution for c in components)
        by_type: dict[ComponentType, TypeBreakdown] = {}

        for c in components:
            if c.component_type not in by_type:
                by_type[c.component_type] = TypeBreakdown(count=0, total_sfp=0.0)
            by_type[c.component_type].count += 1
            by_type[c.component_type].total_sfp += c.contribution

        return MeasurementSummary(
            total_component_count=len(components),
            total_sfp=total_sfp,
            by_type=by_type,
        )
