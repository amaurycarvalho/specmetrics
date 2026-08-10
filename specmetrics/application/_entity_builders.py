"""Entity-score builders for the ``metrics.json`` serialization."""

from __future__ import annotations

from typing import Any

from .models import CanonicalEntityType, EntityScore, resolve_entity_id

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
    """Build canonical ``EntityScore`` objects from raw measurement output."""

    @staticmethod
    def build_fpa_entity(entity: dict[str, Any]) -> EntityScore:
        """Build an FPA entity score from a raw measurement entry."""
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
        """Build an SFP entity score from a raw measurement entry."""
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
        """Build a SNAP entity score from a raw measurement entry."""
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
        """Build a BCP entity score from a raw measurement entry."""
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
        """Build a story points entity score from a raw measurement entry."""
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
        """Build a token points entity score from a raw measurement entry."""
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
        """Build a cognitive points entity score from a raw measurement entry."""
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
        """Build a t-shirt entity score from a raw measurement entry."""
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