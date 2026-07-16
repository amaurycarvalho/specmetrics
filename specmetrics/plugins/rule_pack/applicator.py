from __future__ import annotations

from typing import Any, Optional

import structlog

from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.cfm.models import AppliedRuleRecord, RulePack

from .annotator import RuleAnnotator

logger = structlog.get_logger(__name__)

GSC_KEYS: list[str] = [
    "data_communications",
    "distributed_data_processing",
    "performance",
    "heavily_used_configuration",
    "transaction_rate",
    "online_data_entry",
    "end_user_efficiency",
    "online_update",
    "complex_processing",
    "reusability",
    "installation_ease",
    "operational_ease",
    "multiple_sites",
    "facilitate_change",
]


class RuleApplicator:
    def __init__(self) -> None:
        self._annotator = RuleAnnotator()

    @property
    def applied_records(self) -> list[AppliedRuleRecord]:
        return self._annotator.records

    def apply(
        self,
        cfm: CanonicalFunctionalModel,
        packs: list[RulePack],
    ) -> CanonicalFunctionalModel:
        self._annotator.clear()
        result = cfm

        excluded_types: set[str] = set()
        excluded_element_ids: set[str] = set()
        vaf_value: Optional[float] = None
        complexity_overrides: list[dict[str, Any]] = []
        weight_overrides: list[dict[str, Any]] = []
        glossary: dict[str, str] = {}

        seen_exclusions: set[str] = set()
        seen_complexity: set[str] = set()
        seen_weight: set[str] = set()

        for pack in packs:
            glossary.update(pack.glossary_overrides)
            for rule in pack.rules:
                if rule.type == "exclusion":
                    ftypes = rule.config.function_types or []
                    for ft in ftypes:
                        if ft in seen_exclusions:
                            logger.warning(
                                "rule_pack_override_exclusion",
                                rule_pack_id=pack.id,
                                rule_id=rule.id,
                                function_type=ft,
                                message=f"Exclusion for '{ft}' already defined by another pack; this pack's rule takes precedence",
                            )
                        seen_exclusions.add(ft)
                    excluded_types.update(ftypes)
                    self._annotator.record_application(
                        rule_pack_id=pack.id,
                        rule_id=rule.id,
                        rule_type="exclusion",
                        description=f"Excluded function types: {', '.join(ftypes)}",
                        after_state={"excluded_types": list(ftypes)},
                    )

                elif rule.type == "element_exclusion":
                    eids = rule.config.element_ids or []
                    excluded_element_ids.update(eids)
                    self._annotator.record_application(
                        rule_pack_id=pack.id,
                        rule_id=rule.id,
                        rule_type="element_exclusion",
                        description=f"Excluded element IDs: {', '.join(eids)}",
                        after_state={"excluded_element_ids": list(eids)},
                    )

                elif rule.type == "complexity_override":
                    ft_key = (rule.config.function_type or "").upper()
                    if ft_key in seen_complexity:
                        logger.warning(
                            "rule_pack_override_complexity",
                            rule_pack_id=pack.id,
                            rule_id=rule.id,
                            function_type=rule.config.function_type,
                            message=f"Complexity override for '{rule.config.function_type}' already defined by another pack; this pack's rule takes precedence",
                        )
                    seen_complexity.add(ft_key)
                    override = {
                        "pack_id": pack.id,
                        "rule_id": rule.id,
                        "function_type": rule.config.function_type,
                        "thresholds": rule.config.thresholds or {},
                    }
                    complexity_overrides.append(override)
                    self._annotator.record_application(
                        rule_pack_id=pack.id,
                        rule_id=rule.id,
                        rule_type="complexity_override",
                        description=f"Complexity thresholds override for {rule.config.function_type}: {rule.config.thresholds}",
                        after_state={
                            "function_type": rule.config.function_type,
                            "thresholds": rule.config.thresholds or {},
                        },
                    )

                elif rule.type == "weight_override":
                    wk = f"{rule.config.function_type or ''}|{rule.config.complexity or ''}"
                    if wk in seen_weight:
                        logger.warning(
                            "rule_pack_override_weight",
                            rule_pack_id=pack.id,
                            rule_id=rule.id,
                            function_type=rule.config.function_type,
                            complexity=rule.config.complexity,
                            message=f"Weight override for '{rule.config.function_type}/{rule.config.complexity}' already defined by another pack; this pack's rule takes precedence",
                        )
                    seen_weight.add(wk)
                    override = {
                        "pack_id": pack.id,
                        "rule_id": rule.id,
                        "function_type": rule.config.function_type,
                        "complexity": rule.config.complexity,
                        "weight": rule.config.weight,
                    }
                    weight_overrides.append(override)
                    self._annotator.record_application(
                        rule_pack_id=pack.id,
                        rule_id=rule.id,
                        rule_type="weight_override",
                        description=f"Weight override for {rule.config.function_type}/{rule.config.complexity}: {rule.config.weight}",
                        after_state={
                            "function_type": rule.config.function_type,
                            "complexity": rule.config.complexity,
                            "weight": rule.config.weight,
                        },
                    )

                elif rule.type == "vaf":
                    gsc = rule.config.gsc
                    if gsc:
                        total = sum(gsc.values())
                        vaf_value = round(0.65 + 0.01 * total, 2)
                        self._annotator.record_application(
                            rule_pack_id=pack.id,
                            rule_id=rule.id,
                            rule_type="vaf",
                            description=f"Computed VAF={vaf_value} from GSC (total={total})",
                            after_state={"vaf": vaf_value, "gsc_total": total},
                        )

        cfm_types = {
            metadata.get("function_type", "").upper()
            for _pid, process in cfm.functional_processes.items()
            if (metadata := getattr(process, "metadata", None) or {})
        }
        for pack in packs:
            for rule in pack.rules:
                if rule.type == "exclusion":
                    for ft in (rule.config.function_types or []):
                        if ft.upper() not in cfm_types:
                            logger.info(
                                "rule_pack_unused_type",
                                rule_pack_id=pack.id,
                                rule_id=rule.id,
                                function_type=ft,
                                message=f"Rule references function type '{ft}' not present in CFM",
                            )
                elif rule.type == "element_exclusion":
                    for eid in (rule.config.element_ids or []):
                        if eid not in cfm.functional_processes:
                            logger.info(
                                "rule_pack_unused_element",
                                rule_pack_id=pack.id,
                                rule_id=rule.id,
                                element_id=eid,
                                message=f"Rule references element ID '{eid}' not present in CFM",
                            )

        if excluded_types or excluded_element_ids:
            result = self._mark_exclusions(result, excluded_types, excluded_element_ids)

        if complexity_overrides:
            result = self._apply_complexity_overrides(result, complexity_overrides)

        if weight_overrides:
            result = self._apply_weight_overrides(result, weight_overrides)

        if vaf_value is not None:
            result = self._set_vaf(result, vaf_value)

        result = self._annotator.annotate_cfm(result, glossary_overrides=glossary or None)

        logger.info(
            "rule_applicator_applied",
            excluded_types=sorted(excluded_types),
            excluded_elements=sorted(excluded_element_ids),
            complexity_overrides=len(complexity_overrides),
            weight_overrides=len(weight_overrides),
            vaf=vaf_value,
            applied_record_count=len(self._annotator.records),
        )

        return result

    def _mark_exclusions(
        self,
        cfm: CanonicalFunctionalModel,
        excluded_types: set[str],
        excluded_element_ids: set[str],
    ) -> CanonicalFunctionalModel:
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

    def _apply_complexity_overrides(
        self,
        cfm: CanonicalFunctionalModel,
        overrides: list[dict[str, Any]],
    ) -> CanonicalFunctionalModel:
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
                det_count = metadata.get("det_count", 0)
                ftr_count = metadata.get("ftr_count", 0)
                if isinstance(det_count, (int, float)) and isinstance(ftr_count, (int, float)):
                    det_bounds = thresholds.get("det", [0, 999])
                    ftr_bounds = thresholds.get("ftr", [0, 999])
                    if det_count <= det_bounds[0] and ftr_count <= ftr_bounds[0]:
                        metadata["complexity_rating"] = "Low"
                    elif det_count <= det_bounds[1] and ftr_count <= ftr_bounds[1]:
                        metadata["complexity_rating"] = "Average"
                    else:
                        metadata["complexity_rating"] = "High"
                updated_processes[pid] = process.model_copy(
                    update={"metadata": metadata}
                )

        return cfm.model_copy(update={"functional_processes": updated_processes})

    def _apply_weight_overrides(
        self,
        cfm: CanonicalFunctionalModel,
        overrides: list[dict[str, Any]],
    ) -> CanonicalFunctionalModel:
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

    def _set_vaf(
        self,
        cfm: CanonicalFunctionalModel,
        vaf: float,
    ) -> CanonicalFunctionalModel:
        metadata_dict = cfm.metadata.model_dump() if cfm.metadata else {}
        metadata_dict["vaf"] = vaf
        new_metadata = BuildMetadata(**metadata_dict)
        return cfm.model_copy(update={"metadata": new_metadata})
