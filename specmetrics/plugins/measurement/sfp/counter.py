"""Counter that measures components for Simple Function Points."""

from __future__ import annotations

from typing import Self
from uuid import uuid4

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel

from ._config import (
    DEFAULT_FP_CONTRIBUTION,
    DEFAULT_LF_CONTRIBUTION,
    _ComponentSpec,
    _CountConfig,
)
from ._processing import _ComponentProcessor
from .models import (
    ComponentType,
    MeasuredComponent,
    MeasurementWarning,
    SFPMeasurementResult,
)

__all__ = [
    "DEFAULT_FP_CONTRIBUTION",
    "DEFAULT_LF_CONTRIBUTION",
    "SFPCounter",
]


class SFPCounter:
    """Counts SFP components from a canonical functional model."""

    def count(
        self: Self,
        cfm: CanonicalFunctionalModel,
        rule_pack_id: str | None = None,
        contribution_overrides: dict[ComponentType, float] | None = None,
        excluded_types: list[str] | None = None,
        element_exclusions: dict[str, list[str]] | None = None,
        element_inclusions: dict[str, list[str]] | None = None,
        inclusion_criteria: dict[str, dict[str, list[str]]] | None = None,
        run_id: str | None = None,
        previous_result: SFPMeasurementResult | None = None,
        modified_element_ids: list[str] | None = None,
    ) -> SFPMeasurementResult:
        """Count SFP components from the given CFM."""
        config = _CountConfig.from_params(
            excluded_types=excluded_types,
            contribution_overrides=contribution_overrides,
            inclusion_criteria=inclusion_criteria,
            element_exclusions=element_exclusions,
            element_inclusions=element_inclusions,
        )

        processor = _ComponentProcessor()
        components: list[MeasuredComponent] = []
        warnings: list[MeasurementWarning] = []
        seen_fingerprints: dict[str, str] = {}

        fp_spec = _ComponentSpec(
            excluded_name="functional_process",
            contribution=config.fp_contribution,
            node_types=config.fp_node_types,
            element_type_name="Operation",
            component_type="functional_process",
        )
        lf_spec = _ComponentSpec(
            excluded_name="logical_function",
            contribution=config.lf_contribution,
            node_types=config.lf_node_types,
            element_type_name="DataGroup",
            component_type="logical_function",
        )

        for op in cfm.operations.values():
            processor._process_element(
                op=op,
                spec=fp_spec,
                excluded=config.excluded_types,
                excluded_ids=config.excluded_ids,
                excluded_patterns=config.excluded_patterns,
                included_ids=config.included_ids,
                included_patterns=config.included_patterns,
                components=components,
                warnings=warnings,
                seen_fingerprints=seen_fingerprints,
            )

        for dg in cfm.data_groups.values():
            processor._process_element(
                op=dg,
                spec=lf_spec,
                excluded=config.excluded_types,
                excluded_ids=config.excluded_ids,
                excluded_patterns=config.excluded_patterns,
                included_ids=config.included_ids,
                included_patterns=config.included_patterns,
                components=components,
                warnings=warnings,
                seen_fingerprints=seen_fingerprints,
            )

        processor._merge_previous(
            components, previous_result, modified_element_ids
        )

        summary = processor._build_summary(components)

        return SFPMeasurementResult(
            run_id=run_id or str(uuid4()),
            cfm_run_id=cfm.run_id,
            rule_pack_id=rule_pack_id,
            measured_components=components,
            summary=summary,
            warnings=warnings,
        )