"""Internal helpers for applying CFM overrides from rule packs."""

from __future__ import annotations

from typing import Any

from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.kernel.cfm.model import CanonicalFunctionalModel


def rating_for(metadata: dict[str, Any], thresholds: dict[str, list[int]]) -> str:
    """Rate a metadata entry's complexity from its DET/FTR counts."""
    det_count = metadata.get("det_count", 0)
    ftr_count = metadata.get("ftr_count", 0)
    if not isinstance(det_count, (int, float)) or not isinstance(
        ftr_count, (int, float)
    ):
        return metadata.get("complexity_rating", "Average")
    det_bounds = thresholds.get("det", [0, 999])
    ftr_bounds = thresholds.get("ftr", [0, 999])
    if det_count <= det_bounds[0] and ftr_count <= ftr_bounds[0]:
        return "Low"
    if det_count <= det_bounds[1] and ftr_count <= ftr_bounds[1]:
        return "Average"
    return "High"


def mark_exclusions(
    cfm: CanonicalFunctionalModel,
    excluded_types: set[str],
    excluded_element_ids: set[str],
) -> CanonicalFunctionalModel:
    """Mark excluded processes in a copy of the CFM."""
    updated_processes = dict(cfm.functional_processes)

    for pid, process in updated_processes.items():
        metadata = dict(process.metadata)

        if pid in excluded_element_ids:
            metadata["excluded"] = True
            metadata["excluded_by"] = "element_exclusion"
            updated_processes[pid] = process.model_copy(
                update={"metadata": metadata}
            )
            continue

        for excluded in excluded_types:
            ft = metadata.get("function_type", "")
            if isinstance(ft, str) and ft.upper() == excluded:
                metadata["excluded"] = True
                metadata["excluded_by"] = f"type_exclusion:{excluded}"
                updated_processes[pid] = process.model_copy(
                    update={"metadata": metadata}
                )

    return cfm.model_copy(update={"functional_processes": updated_processes})


def apply_complexity_overrides(
    cfm: CanonicalFunctionalModel,
    overrides: list[dict[str, Any]],
) -> CanonicalFunctionalModel:
    """Apply complexity threshold overrides to the CFM."""
    updated_processes = dict(cfm.functional_processes)

    override_map: dict[str, dict[str, list[int]]] = {}
    for ov in overrides:
        ft = ov["function_type"]
        if ft:
            override_map[ft.upper()] = ov["thresholds"]

    for pid, process in updated_processes.items():
        metadata = dict(process.metadata)
        ft = metadata.get("function_type", "")
        if isinstance(ft, str) and ft.upper() in override_map:
            thresholds = override_map[ft.upper()]
            metadata["complexity_thresholds"] = thresholds
            metadata["complexity_source"] = "rule_pack_override"
            metadata["complexity_rating"] = rating_for(metadata, thresholds)
            updated_processes[pid] = process.model_copy(
                update={"metadata": metadata}
            )

    return cfm.model_copy(update={"functional_processes": updated_processes})


def apply_weight_overrides(
    cfm: CanonicalFunctionalModel,
    overrides: list[dict[str, Any]],
) -> CanonicalFunctionalModel:
    """Apply weight overrides to the CFM."""
    updated_processes = dict(cfm.functional_processes)

    override_map: dict[str, dict[str, int]] = {}
    for ov in overrides:
        ft = ov.get("function_type", "")
        comp = ov.get("complexity", "")
        weight = ov.get("weight")
        if ft and comp and weight is not None:
            ft_key = ft.upper()
            if ft_key not in override_map:
                override_map[ft_key] = {}
            override_map[ft_key][comp] = weight

    for pid, process in updated_processes.items():
        metadata = dict(process.metadata)
        ft = metadata.get("function_type", "")
        if isinstance(ft, str) and ft.upper() in override_map:
            comp = metadata.get("complexity_rating", "Average")
            ft_overrides = override_map[ft.upper()]
            if comp in ft_overrides:
                metadata["ufp_weight"] = ft_overrides[comp]
                metadata["weight_source"] = "rule_pack_override"
                updated_processes[pid] = process.model_copy(
                    update={"metadata": metadata}
                )

    return cfm.model_copy(update={"functional_processes": updated_processes})


def set_vaf(cfm: CanonicalFunctionalModel, vaf: float) -> CanonicalFunctionalModel:
    """Set the value adjustment factor on the CFM metadata."""
    metadata_dict = cfm.metadata.model_dump() if cfm.metadata else {}
    metadata_dict["vaf"] = vaf
    new_metadata = BuildMetadata(**metadata_dict)
    return cfm.model_copy(update={"metadata": new_metadata})