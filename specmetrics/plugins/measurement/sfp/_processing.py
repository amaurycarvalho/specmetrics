"""Element processing helpers for the SFP counter."""
from __future__ import annotations

import fnmatch
import hashlib
from typing import Self

from specmetrics.kernel.cfm.model import DataGroup, Operation

from ._config import _ComponentSpec
from .models import (
    ComponentType,
    EvidenceRef,
    MeasuredComponent,
    MeasurementSummary,
    MeasurementWarning,
    SFPMeasurementResult,
    TypeBreakdown,
)


class _ComponentProcessor:
    """Processes operations and data groups into measured components."""

    def _process_element(
        self: Self,
        op: Operation | DataGroup,
        spec: _ComponentSpec,
        excluded: set[str],
        excluded_ids: set[str],
        excluded_patterns: list[str],
        included_ids: set[str],
        included_patterns: list[str],
        components: list[MeasuredComponent],
        warnings: list[MeasurementWarning],
        seen_fingerprints: dict[str, str],
    ) -> None:
        if spec.excluded_name in excluded:
            return
        is_included = self._is_included(op.id, op.name, included_ids, included_patterns)
        if not is_included and not self._is_element(op, spec):
            return
        if self._is_excluded(op.id, op.name, excluded_ids, excluded_patterns):
            return

        component = self._create_component(
            element=op,
            element_id=op.id,
            element_name=op.name,
            element_type_name=spec.element_type_name,
            component_type=spec.component_type,
            contribution=spec.contribution,
            component_counter=len(components) + 1,
        )
        component, warning = self._deduplicate(
            component, seen_fingerprints, self._fingerprint(op)
        )
        if warning:
            warnings.append(warning)
        if component is not None:
            components.append(component)

    @staticmethod
    def _is_element(element: Operation | DataGroup, spec: _ComponentSpec) -> bool:
        node_type = element.metadata.get("node_type", "")
        if spec.node_types:
            return node_type in spec.node_types
        if isinstance(element, Operation):
            return not (node_type and node_type != "elementary_process")
        return not (node_type and node_type != "data_group")

    @staticmethod
    def _is_excluded(
        element_id: str, element_name: str, excluded_ids: set[str], excluded_patterns: list[str]
    ) -> bool:
        if element_id in excluded_ids:
            return True
        return any(
            fnmatch.fnmatch(element_id, pattern) or fnmatch.fnmatch(element_name, pattern)
            for pattern in excluded_patterns
        )

    @staticmethod
    def _is_included(
        element_id: str, element_name: str, included_ids: set[str], included_patterns: list[str]
    ) -> bool:
        if element_id in included_ids:
            return True
        return any(
            fnmatch.fnmatch(element_id, pattern) or fnmatch.fnmatch(element_name, pattern)
            for pattern in included_patterns
        )

    @staticmethod
    def _fingerprint(element: Operation | DataGroup) -> str:
        raw = f"{element.evidence.document_id}:{element.evidence.section_id or ''}:{element.evidence.text}:{type(element).__name__}"
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _merge_previous(
        components: list[MeasuredComponent],
        previous_result: SFPMeasurementResult | None,
        modified_element_ids: list[str] | None,
    ) -> None:
        if previous_result is None or modified_element_ids is None:
            return
        modified_set = set(modified_element_ids)
        current_ids = {c.cfm_element_id for c in components}
        for c in previous_result.measured_components:
            if c.cfm_element_id not in modified_set and c.cfm_element_id not in current_ids:
                components.append(c)

    def _create_component(
        self: Self,
        element: Operation | DataGroup,
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
        self: Self,
        component: MeasuredComponent,
        seen_fingerprints: dict[str, str],
        fingerprint: str,
    ) -> tuple[MeasuredComponent | None, MeasurementWarning | None]:
        if fingerprint in seen_fingerprints:
            return None, MeasurementWarning(
                code="DUPLICATE_MERGED",
                message=f"Duplicate component '{component.name}' merged; only one counted",
                cfm_element_id=component.cfm_element_id,
                details={"merged_into": seen_fingerprints[fingerprint]},
            )
        seen_fingerprints[fingerprint] = component.id
        return component, None

    def _build_summary(self: Self, components: list[MeasuredComponent]) -> MeasurementSummary:
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