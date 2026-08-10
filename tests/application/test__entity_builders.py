from __future__ import annotations

import pytest

from specmetrics.application._entity_builders import (
    EntityScoreBuilder,
    _validate_canonical_type,
)


def test_validate_canonical_type_accepts_known():
    """Kills mutants that swap the canonical-type membership set."""
    assert _validate_canonical_type("operation") == "operation"
    assert _validate_canonical_type("data_group") == "data_group"
    assert _validate_canonical_type("relationship") == "relationship"
    with pytest.raises(ValueError):
        _validate_canonical_type("not-a-type")

def test_validate_canonical_type_rejects_unknown():
    """Kills mutants replacing the unknown-type error path."""
    with pytest.raises(ValueError, match="Unknown canonical entity type"):
        _validate_canonical_type("bogus")

def test_build_fpa_entity_defaults():
    """Kills mutmut_3, mutmut_5, mutmut_8 (function_type default ''), mutmut_61/67/68/69/70/71/72/73 (raw_id), mutmut_63/74-80/82/84/87 (name), mutmut_90/92/95 (ufp_weight default 0), mutmut_62 (category)."""
    result = EntityScoreBuilder.build_fpa_entity(
        {"id": "cfm:operation:foo", "name": "Foo"}
    )
    assert result.type == "operation"
    assert result.name == "Foo"
    assert result.score == 0.0
    assert result.metadata["function_type"] is None

def test_build_fpa_entity_preserves_values():
    """Kills mutmut_71/72/78/79 (key renames id/name), mutmut_73/80/87 (default swaps to XXXX), mutmut_67 (get None)."""
    result = EntityScoreBuilder.build_fpa_entity(
        {
            "function_type": "ILF",
            "id": "cfm:data_group:orders",
            "name": "Orders",
            "ufp_weight": 15,
            "complexity": "Average",
            "det_count": 7,
        }
    )
    assert result.type == "data_group"
    assert result.id == "cfm:data_group:orders"
    assert result.name == "Orders"
    assert result.score == 15.0
    assert result.metadata["function_type"] == "ILF"
    assert result.metadata["complexity"] == "Average"
    assert result.metadata["det_count"] == 7

def test_build_sfp_entity_defaults():
    """Kills mutmut_3/5/8 (component_type default), mutmut_11/13/14/15 (canonical default), mutmut_27/33-39 (raw_id), mutmut_29/40-53 (name), mutmut_56/58/61 (contribution default 0), mutmut_21/26/62-66 (metadata)."""
    result = EntityScoreBuilder.build_sfp_entity(
        {"id": "cfm:functional_process:foo", "name": "Foo"}
    )
    assert result.type == "functional_process"
    assert result.name == "Foo"
    assert result.score == 0.0
    assert result.metadata == {"component_type": None}

def test_build_sfp_entity_preserves_values():
    """Kills mutmut_37/38 (id key rename), mutmut_44/45/51/52 (name key rename), mutmut_62/63/65/66 (metadata key rename), mutmut_64 (get None)."""
    result = EntityScoreBuilder.build_sfp_entity(
        {
            "component_type": "logical_function",
            "id": "cfm:data_group:orders",
            "name": "Orders",
            "contribution": 9,
        }
    )
    assert result.type == "data_group"
    assert result.id == "cfm:data_group:orders"
    assert result.name == "Orders"
    assert result.score == 9.0
    assert result.metadata == {"component_type": "logical_function"}

def test_build_snap_entity_defaults():
    """Kills mutmut_1-8 (category_id default), mutmut_10/11/13/14/15 (canonical default), mutmut_27/33-39 (raw_id), mutmut_29/40-53 (name), mutmut_56/58/61 (contribution default), mutmut_67-71 (cfm_semantic_marker key)."""
    result = EntityScoreBuilder.build_snap_entity(
        {"id": "csm:specification_activity:foo", "name": "Foo"}
    )
    assert result.type == "specification_activity"
    assert result.name == "Foo"
    assert result.score == 0.0
    assert result.metadata == {"category_id": None, "cfm_semantic_marker": None}

def test_build_snap_entity_preserves_values():
    """Kills mutmut_37/38/44/45/51/52/67/68/70/71 key renames and mutmut_69/2 get(None)."""
    result = EntityScoreBuilder.build_snap_entity(
        {
            "category_id": "presentation",
            "id": "csm:specification_activity:home",
            "name": "Home",
            "contribution": 4,
            "cfm_semantic_marker": "marker",
        }
    )
    assert result.type == "specification_activity"
    assert result.id == "csm:specification_activity:home"
    assert result.name == "Home"
    assert result.score == 4.0
    assert result.metadata["category_id"] == "presentation"
    assert result.metadata["cfm_semantic_marker"] == "marker"

def test_build_bcp_entity_defaults():
    """Kills mutmut_13/14/15 (generated_story get), mutmut_16/17/18 (metadata generated_story), mutmut_31/37-43 (raw_id), and bcp score default."""
    result = EntityScoreBuilder.build_bcp_entity(
        {"element_id": "cfm:functional_process:foo", "element_name": "Foo"}
    )
    assert result.type == "functional_process"
    assert result.name == "Foo"
    assert result.score == 0.0
    assert result.metadata is None

def test_build_bcp_entity_preserves_values():
    """Kills mutmut_13/14/15 (generated_story key), mutmut_16/17/18 (metadata key), mutmut_41/42 (element_id key rename)."""
    result = EntityScoreBuilder.build_bcp_entity(
        {
            "element_id": "cfm:functional_process:payment",
            "element_name": "Payment",
            "bcp_score": 12,
            "component_breakdown": [{"x": 1}],
            "generated_story": "story",
        }
    )
    assert result.id == "cfm:functional_process:payment"
    assert result.name == "Payment"
    assert result.score == 12.0
    assert result.metadata["component_breakdown"] == [{"x": 1}]
    assert result.metadata["generated_story"] == "story"

def test_build_storypoints_entity_defaults():
    """Kills storypoints id/name/score/metadata default mutants."""
    result = EntityScoreBuilder.build_storypoints_entity(
        {"element_id": "cfm:functional_process:foo", "element_name": "Foo"}
    )
    assert result.type == "functional_process"
    assert result.name == "Foo"
    assert result.score == 0.0
    assert result.metadata["raw_score"] is None
    assert result.metadata["applied_rules"] == []

def test_build_storypoints_entity_preserves_values():
    """Kills storypoints key renames and applied_rules default."""
    result = EntityScoreBuilder.build_storypoints_entity(
        {
            "element_id": "cfm:functional_process:item",
            "element_name": "Item",
            "normalized_value": 5,
            "raw_score": 8,
            "factor_breakdown": [1, 2],
            "applied_rules": ["r1"],
        }
    )
    assert result.id == "cfm:functional_process:item"
    assert result.name == "Item"
    assert result.score == 5.0
    assert result.metadata["applied_rules"] == ["r1"]
    assert result.metadata["factor_breakdown"] == [1, 2]

def test_build_tokenpoints_entity_defaults():
    """Kills tokenpoints element_type default, model_source default, score default, metadata defaults."""
    result = EntityScoreBuilder.build_tokenpoints_entity(
        {"element_id": "cfm:specification_activity:foo", "element_name": "Foo"}
    )
    assert result.type == "specification_activity"
    assert result.name == "Foo"
    assert result.score == 0.0
    assert result.metadata["model_source"] is None
    assert result.metadata["element_type"] == ""

def test_build_tokenpoints_entity_preserves_values():
    """Kills tokenpoints key renames and rounding behavior."""
    result = EntityScoreBuilder.build_tokenpoints_entity(
        {
            "element_type": "operation",
            "element_id": "cfm:operation:load",
            "element_name": "Load",
            "partial_score": 12.34,
            "applied_weight": 2,
            "model_source": "cfm",
        }
    )
    assert result.type == "operation"
    assert result.id == "cfm:operation:load"
    assert result.name == "Load"
    assert result.score == 12.3
    assert result.metadata["applied_weight"] == 2

def test_build_cognitive_entity_defaults():
    """Kills cognitive element_type default, model_source default, score default, metadata defaults."""
    result = EntityScoreBuilder.build_cognitive_entity(
        {"element_id": "cfm:business_rule:foo", "element_name": "Foo"}
    )
    assert result.type == "business_rule"
    assert result.name == "Foo"
    assert result.score == 0.0
    assert result.metadata["bloom_level"] is None
    assert result.metadata["cognitive_weight"] is None

def test_build_cognitive_entity_preserves_values():
    """Kills cognitive key renames and rounding behavior."""
    result = EntityScoreBuilder.build_cognitive_entity(
        {
            "element_type": "data_group",
            "element_id": "cfm:data_group:entity",
            "element_name": "Entity",
            "partial_score": 5.67,
            "bloom_level": 3,
            "cognitive_weight": 1.5,
            "model_source": "cfm",
        }
    )
    assert result.type == "data_group"
    assert result.id == "cfm:data_group:entity"
    assert result.name == "Entity"
    assert result.score == 5.7
    assert result.metadata["bloom_level"] == 3
    assert result.metadata["cognitive_weight"] == 1.5

def test_build_tshirt_entity_defaults():
    """Kills tshirt entity_type default, score default, metadata defaults."""
    result = EntityScoreBuilder.build_tshirt_entity(
        {"element_id": "cfm:functional_process:foo", "element_name": "Foo"}
    )
    assert result.type == "functional_process"
    assert result.name == "Foo"
    assert result.score == 0.0
    assert result.metadata["story_point_value"] is None
    assert result.metadata["tshirt_size"] is None

def test_build_tshirt_entity_preserves_values():
    """Kills tshirt key renames (type/element_type, story_point_value, mapping_rule)."""
    result = EntityScoreBuilder.build_tshirt_entity(
        {
            "type": "operation",
            "element_id": "cfm:operation:op",
            "element_name": "Op",
            "story_point_value": 3,
            "tshirt_size": "M",
            "mapping_rule": "r",
        }
    )
    assert result.type == "operation"
    assert result.id == "cfm:operation:op"
    assert result.name == "Op"
    assert result.score == 3.0
    assert result.metadata["story_point_value"] == 3
    assert result.metadata["tshirt_size"] == "M"
    assert result.metadata["mapping_rule"] == "r"

