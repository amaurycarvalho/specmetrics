from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import (
    CanonicalEntityType,
    EntityScore,
    MetricBreakdownEntry,
    resolve_entity_id,
)

METRIC_UNIT_MAP: dict[str, str] = {
    "fpa": "ufp",
    "sfp": "sfp",
    "snap": "snap",
    "bcp": "bcp",
    "sp": "story_points",
    "tp": "tokens",
    "cp": "cognitive_points",
    "tshirt": "entities",
}

METRIC_JSON_NAME_MAP: dict[str, str] = {
    "bcp": "business_complexity_points",
    "fpa": "function_points",
    "sfp": "simplified_function_points",
    "snap": "snap",
    "sp": "story_points",
    "tshirt": "tshirt",
    "tp": "token_points",
    "cp": "cognitive_points",
}

WARNING_KEY_MAP: dict[str, str] = {
    "bcp": "bcp_warnings",
    "sp": "storypoints_warnings",
    "tp": "token_warnings",
    "cp": "cognitive_warnings",
}

ENTITY_KEY_MAP: dict[str, str] = {
    "fpa": "fpa_entities",
    "sfp": "sfp_entities",
    "snap": "snap_entities",
    "bcp": "bcp_entities",
    "sp": "storypoints_entities",
    "tp": "token_entities",
    "cp": "cognitive_entities",
    "tshirt": "tshirt_entities",
}

FPA_TYPE_MAP: dict[str, str] = {
    "ILF": "data_group",
    "EIF": "data_group",
    "EI": "operation",
    "EO": "operation",
    "EQ": "operation",
}

SFP_TYPE_MAP: dict[str, str] = {
    "functional_process": "functional_process",
    "logical_function": "data_group",
}

SNAP_TYPE_MAP: dict[str, str] = {
    "presentation": "specification_activity",
    "data_operations": "operation",
    "operational_capabilities": "functional_process",
    "technical_interaction": "relationship",
}

CANONICAL_TYPE_SET: frozenset[str] = frozenset(CanonicalEntityType.__args__)


def _validate_canonical_type(entity_type: str) -> str:
    if entity_type not in CANONICAL_TYPE_SET:
        raise ValueError(
            f"Unknown canonical entity type: {entity_type}. "
            f"Must be one of: {sorted(CANONICAL_TYPE_SET)}"
        )
    return entity_type


class EntityScoreBuilder:
    @staticmethod
    def build_fpa_entity(entity: dict[str, Any]) -> EntityScore:
        raw_type = entity.get("function_type", "")
        canonical = FPA_TYPE_MAP.get(raw_type, "operation")
        _validate_canonical_type(canonical)
        metadata: dict[str, Any] = {
            "function_type": entity.get("function_type"),
            "complexity": entity.get("complexity"),
            "det_count": entity.get("det_count"),
        }
        if entity.get("ret_count") is not None:
            metadata["ret_count"] = entity["ret_count"]
        if entity.get("ftr_count") is not None:
            metadata["ftr_count"] = entity["ftr_count"]
        return EntityScore(
            id=resolve_entity_id(
                raw_id=entity.get("id", ""),
                category=canonical,
                name=entity.get("name", ""),
            ),
            name=entity.get("name", ""),
            type=canonical,
            score=float(entity.get("ufp_weight", 0)),
            metadata=metadata,
        )

    @staticmethod
    def build_sfp_entity(entity: dict[str, Any]) -> EntityScore:
        raw_type = entity.get("component_type", "")
        canonical = SFP_TYPE_MAP.get(raw_type, "functional_process")
        _validate_canonical_type(canonical)
        return EntityScore(
            id=resolve_entity_id(
                raw_id=entity.get("id", ""),
                category=canonical,
                name=entity.get("name", ""),
            ),
            name=entity.get("name", ""),
            type=canonical,
            score=float(entity.get("contribution", 0)),
            metadata={"component_type": entity.get("component_type")},
        )

    @staticmethod
    def build_snap_entity(entity: dict[str, Any]) -> EntityScore:
        raw_category = entity.get("category_id", "")
        canonical = SNAP_TYPE_MAP.get(raw_category, "specification_activity")
        _validate_canonical_type(canonical)
        return EntityScore(
            id=resolve_entity_id(
                raw_id=entity.get("id", ""),
                category=canonical,
                name=entity.get("name", ""),
            ),
            name=entity.get("name", ""),
            type=canonical,
            score=float(entity.get("contribution", 0)),
            metadata={
                "category_id": entity.get("category_id"),
                "cfm_semantic_marker": entity.get("cfm_semantic_marker"),
            },
        )

    @staticmethod
    def build_bcp_entity(entity: dict[str, Any]) -> EntityScore:
        _validate_canonical_type("functional_process")
        metadata: dict[str, Any] = {}
        if entity.get("component_breakdown"):
            metadata["component_breakdown"] = entity["component_breakdown"]
        if entity.get("generated_story"):
            metadata["generated_story"] = entity["generated_story"]
        return EntityScore(
            id=resolve_entity_id(
                raw_id=entity.get("element_id", ""),
                category="functional_process",
                name=entity.get("element_name", ""),
            ),
            name=entity.get("element_name", ""),
            type="functional_process",
            score=float(entity.get("bcp_score", 0)),
            metadata=metadata or None,
        )

    @staticmethod
    def build_storypoints_entity(entity: dict[str, Any]) -> EntityScore:
        _validate_canonical_type("functional_process")
        return EntityScore(
            id=resolve_entity_id(
                raw_id=entity.get("element_id", ""),
                category="functional_process",
                name=entity.get("element_name", ""),
            ),
            name=entity.get("element_name", ""),
            type="functional_process",
            score=float(entity.get("normalized_value", 0)),
            metadata={
                "raw_score": entity.get("raw_score"),
                "normalized_value": entity.get("normalized_value"),
                "factor_breakdown": entity.get("factor_breakdown"),
                "applied_rules": entity.get("applied_rules", []),
            },
        )

    @staticmethod
    def build_tokenpoints_entity(entity: dict[str, Any]) -> EntityScore:
        element_type = entity.get("element_type", "")
        canonical = (
            element_type
            if element_type in CANONICAL_TYPE_SET
            else "specification_activity"
        )
        _validate_canonical_type(canonical)
        return EntityScore(
            id=resolve_entity_id(
                raw_id=entity.get("element_id", ""),
                category=canonical,
                name=entity.get("element_name", ""),
                model_source=entity.get("model_source", "cfm"),
            ),
            name=entity.get("element_name", ""),
            type=canonical,
            score=round(float(entity.get("partial_score", 0)), 1),
            metadata={
                "applied_weight": entity.get("applied_weight"),
                "model_source": entity.get("model_source"),
                "element_type": element_type,
            },
        )

    @staticmethod
    def build_cognitive_entity(entity: dict[str, Any]) -> EntityScore:
        element_type = entity.get("element_type", "")
        canonical = (
            element_type if element_type in CANONICAL_TYPE_SET else "business_rule"
        )
        _validate_canonical_type(canonical)
        return EntityScore(
            id=resolve_entity_id(
                raw_id=entity.get("element_id", ""),
                category=canonical,
                name=entity.get("element_name", ""),
                model_source=entity.get("model_source", "cfm"),
            ),
            name=entity.get("element_name", ""),
            type=canonical,
            score=round(float(entity.get("partial_score", 0)), 1),
            metadata={
                "bloom_level": entity.get("bloom_level"),
                "cognitive_weight": entity.get("cognitive_weight"),
                "model_source": entity.get("model_source"),
                "element_type": element_type,
            },
        )

    @staticmethod
    def build_tshirt_entity(entity: dict[str, Any]) -> EntityScore:
        entity_type = entity.get("type") or entity.get("element_type") or "functional_process"
        _validate_canonical_type(entity_type)
        return EntityScore(
            id=resolve_entity_id(
                raw_id=entity.get("element_id", ""),
                category=entity_type,
                name=entity.get("element_name", ""),
            ),
            name=entity.get("element_name", ""),
            type=entity_type,
            score=float(entity.get("story_point_value", 0)),
            metadata={
                "story_point_value": entity.get("story_point_value"),
                "tshirt_size": entity.get("tshirt_size"),
                "mapping_rule": entity.get("mapping_rule"),
            },
        )


_BUILDERS: dict[str, Any] = {
    "fpa": EntityScoreBuilder.build_fpa_entity,
    "sfp": EntityScoreBuilder.build_sfp_entity,
    "snap": EntityScoreBuilder.build_snap_entity,
    "bcp": EntityScoreBuilder.build_bcp_entity,
    "sp": EntityScoreBuilder.build_storypoints_entity,
    "tp": EntityScoreBuilder.build_tokenpoints_entity,
    "cp": EntityScoreBuilder.build_cognitive_entity,
    "tshirt": EntityScoreBuilder.build_tshirt_entity,
}

_METRIC_METADATA_BUILDERS: dict[str, Any] = {}


def _build_metric_metadata(cli_id: str, raw: dict[str, Any]) -> dict[str, Any] | None:
    if cli_id == "fpa":
        meta: dict[str, Any] = {"method": "ifpug"}
        vaf = raw.get("fpa_vaf")
        if vaf is not None:
            meta["vaf"] = vaf
        return meta
    if cli_id == "sfp":
        meta: dict[str, Any] = {"method": "simplified"}
        sfp_breakdown = raw.get("sfp_breakdown")
        if sfp_breakdown:
            fp = sfp_breakdown.get("functional_process", {})
            lf = sfp_breakdown.get("logical_function", {})
            meta["fp_contribution"] = fp.get("total_sfp", 0)
            meta["lf_contribution"] = lf.get("total_sfp", 0)
        return meta
    if cli_id == "snap":
        meta: dict[str, Any] = {"method": "snap"}
        snap_by_category = raw.get("snap_by_category")
        if snap_by_category:
            meta["categories"] = snap_by_category
        return meta
    if cli_id == "bcp":
        return {
            "method": raw.get("bcp_method", "BCP"),
            "provider": raw.get("bcp_provider", ""),
            "sdk_version": raw.get("bcp_sdk_version", ""),
        }
    if cli_id == "sp":
        return {
            "method": raw.get("storypoints_method", "fibonacci_factor_based"),
            "scale": raw.get("storypoints_scale", "fibonacci"),
        }
    if cli_id == "tp":
        meta = {"calibration_version": raw.get("token_calibration_version", "1.0")}
        spec_cost = raw.get("token_specification_cost")
        code_cost = raw.get("token_code_generation_cost")
        if spec_cost is not None:
            meta["specification_cost"] = round(spec_cost, 1)
        if code_cost is not None:
            meta["code_generation_cost"] = round(code_cost, 1)
        return meta
    if cli_id == "cp":
        meta = {"calibration_version": raw.get("cognitive_calibration_version", "1.0")}
        raw_score = raw.get("cognitive_raw_score")
        if raw_score is not None:
            meta["raw_score"] = round(raw_score, 1)
        fib = raw.get("cognitive_fibonacci_normalization")
        if fib is not None:
            meta["fibonacci_normalization"] = {
                k: round(v, 1) if isinstance(v, float) else v
                for k, v in fib.items()
            }
        return meta
    if cli_id == "tshirt":
        from specmetrics.plugins.measurement.tshirt.classifier import DEFAULT_MAPPING
        mapping = {}
        for size in DEFAULT_MAPPING:
            mapping[size.label] = size.story_point_range[1]
        return {
            "scale": raw.get("scale", "XS-S-M-L-XL-XXL"),
            "mapping": mapping,
        }
    return None


class MetricBreakdownBuilder:
    def __init__(self, measurement_result_raw: dict[str, Any]) -> None:
        self._raw = measurement_result_raw

    def build_all(
        self, metrics_filter: list[str] | None = None
    ) -> list[MetricBreakdownEntry]:
        entries: list[MetricBreakdownEntry] = []
        metric_ids = metrics_filter or list(ENTITY_KEY_MAP.keys())

        for cli_id in metric_ids:
            if cli_id not in ENTITY_KEY_MAP:
                continue
            entry = self._build_entry(cli_id)
            if entry is not None:
                entries.append(entry)

        return entries

    def _build_entry(self, cli_id: str) -> MetricBreakdownEntry | None:
        entity_key = ENTITY_KEY_MAP[cli_id]
        raw_entities: list[dict[str, Any]] = self._raw.get(entity_key, [])

        builder_fn = _BUILDERS.get(cli_id)
        if builder_fn is None:
            return None

        if not isinstance(raw_entities, list):
            raw_entities = []

        entities: list[EntityScore] = []
        errors: list[str] = []

        for raw_entity in raw_entities:
            try:
                entity = builder_fn(raw_entity)
                entities.append(entity)
            except (ValueError, TypeError, KeyError) as exc:
                errors.append(f"Failed to build entity: {exc}")

        if cli_id == "tshirt":
            total = float(len(entities))
        else:
            total = sum(e.score for e in entities)
            if cli_id in ("tp", "cp"):
                total = round(total, 1)
        unit = METRIC_UNIT_MAP.get(cli_id, "")
        json_name = METRIC_JSON_NAME_MAP.get(cli_id, cli_id)
        metric_metadata = _build_metric_metadata(cli_id, self._raw)

        warning_key = WARNING_KEY_MAP.get(cli_id)
        metric_warnings: list[str] = []
        if warning_key:
            raw_warnings = self._raw.get(warning_key, [])
            if isinstance(raw_warnings, list):
                for w in raw_warnings:
                    if isinstance(w, dict):
                        metric_warnings.append(str(w.get("message", str(w))))
                    elif isinstance(w, str):
                        metric_warnings.append(w)

        if errors:
            return MetricBreakdownEntry(
                name=cli_id,
                metric=json_name,
                total=0.0,
                unit=unit,
                entity_count=0,
                entities=[],
                status="failed",
                errors=errors,
                warnings=metric_warnings if metric_warnings else None,
                metadata=metric_metadata,
            )

        return MetricBreakdownEntry(
            name=cli_id,
            metric=json_name,
            total=total,
            unit=unit,
            entity_count=len(entities),
            entities=entities,
            status="success",
            warnings=metric_warnings if metric_warnings else None,
            metadata=metric_metadata,
        )


def save_metrics_json(
    project_path: Path,
    measure_id: str,
    result: Any,
    metrics_filter: list[str] | None = None,
) -> Path | None:
    measurement_result_raw: dict[str, Any] = getattr(
        result, "measurement_result_raw", {}
    )
    if not measurement_result_raw:
        runs_dir = project_path / ".specmetrics" / "runs" / measure_id
        runs_dir.mkdir(parents=True, exist_ok=True)
        failed_entry = MetricBreakdownEntry(
            name="error",
            metric="error",
            total=0.0,
            unit="",
            entity_count=0,
            entities=[],
            status="failed",
            errors=["measurement_result_raw is missing or empty"],
        )
        metrics_path = runs_dir / "metrics.json"
        metrics_path.write_text(
            json.dumps([failed_entry.model_dump(mode="json")], indent=2),
            encoding="utf-8",
        )
        return metrics_path

    builder = MetricBreakdownBuilder(measurement_result_raw)
    entries = builder.build_all(metrics_filter=metrics_filter)

    runs_dir = project_path / ".specmetrics" / "runs" / measure_id
    runs_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = runs_dir / "metrics.json"
    metrics_path.write_text(
        json.dumps(
            [e.model_dump(mode="json", exclude_none=True) for e in entries],
            indent=2,
        ),
        encoding="utf-8",
    )
    return metrics_path
