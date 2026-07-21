from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from specmetrics.application.metrics_json import (
    EntityScoreBuilder,
    MetricBreakdownBuilder,
    save_metrics_json,
)


class TestEntityScoreBuilder:
    def test_build_fpa_entity_data_function(self):
        entity = {
            "id": "cfm:data_group:user-profile",
            "name": "User Profile",
            "function_type": "ILF",
            "complexity": "Low",
            "det_count": 5,
            "ret_count": 1,
            "ufp_weight": 10,
        }
        result = EntityScoreBuilder.build_fpa_entity(entity)
        assert result.id == "cfm:data_group:user-profile"
        assert result.name == "User Profile"
        assert result.type == "data_group"
        assert result.score == 10.0
        assert result.metadata is not None
        assert result.metadata["function_type"] == "ILF"
        assert result.metadata["complexity"] == "Low"
        assert result.metadata["det_count"] == 5
        assert result.metadata["ret_count"] == 1

    def test_build_fpa_entity_transaction(self):
        entity = {
            "id": "cfm:operation:register",
            "name": "Register User",
            "function_type": "EI",
            "complexity": "Average",
            "det_count": 8,
            "ftr_count": 2,
            "ufp_weight": 4,
        }
        result = EntityScoreBuilder.build_fpa_entity(entity)
        assert result.type == "operation"
        assert result.score == 4.0
        assert result.metadata["function_type"] == "EI"
        assert result.metadata["ftr_count"] == 2

    def test_build_sfp_entity_functional_process(self):
        entity = {
            "id": "cfm:functional_process:place-order",
            "name": "Place Order",
            "component_type": "functional_process",
            "contribution": 5.0,
        }
        result = EntityScoreBuilder.build_sfp_entity(entity)
        assert result.type == "functional_process"
        assert result.score == 5.0

    def test_build_sfp_entity_logical_function(self):
        entity = {
            "id": "cfm:data_group:products",
            "name": "Products",
            "component_type": "logical_function",
            "contribution": 3.0,
        }
        result = EntityScoreBuilder.build_sfp_entity(entity)
        assert result.type == "data_group"
        assert result.score == 3.0

    def test_build_snap_entity(self):
        entity = {
            "id": "cfm:specification_activity:login-form",
            "name": "Login Form",
            "category_id": "presentation",
            "contribution": 4.0,
            "cfm_semantic_marker": "presentation_interface",
        }
        result = EntityScoreBuilder.build_snap_entity(entity)
        assert result.type == "specification_activity"
        assert result.score == 4.0
        assert result.metadata["category_id"] == "presentation"

    def test_build_bcp_entity(self):
        entity = {
            "element_id": "cfm:functional_process:onboard-user",
            "element_name": "Onboard User",
            "bcp_score": 12.0,
            "component_breakdown": {"login": 4, "profile_setup": 5},
            "generated_story": "As a user...",
            "status": "success",
        }
        result = EntityScoreBuilder.build_bcp_entity(entity)
        assert result.type == "functional_process"
        assert result.score == 12.0
        assert result.metadata["component_breakdown"]["login"] == 4

    def test_build_storypoints_entity(self):
        entity = {
            "element_id": "cfm:functional_process:place-order",
            "element_name": "Place Order",
            "raw_score": 10.5,
            "normalized_value": 8,
            "factor_breakdown": {"business_interactions": 2.0},
            "applied_rules": ["default_threshold_v1"],
        }
        result = EntityScoreBuilder.build_storypoints_entity(entity)
        assert result.type == "functional_process"
        assert result.score == 8.0
        assert result.metadata["raw_score"] == 10.5
        assert result.metadata["normalized_value"] == 8

    def test_build_tokenpoints_entity(self):
        entity = {
            "element_id": "csm:specification_activity:review",
            "element_name": "Review Requirements",
            "element_type": "specification_activity",
            "model_source": "csm",
            "applied_weight": 3.0,
            "partial_score": 15.0,
        }
        result = EntityScoreBuilder.build_tokenpoints_entity(entity)
        assert result.type == "specification_activity"
        assert result.score == 15.0
        assert result.metadata["applied_weight"] == 3.0
        assert result.metadata["model_source"] == "csm"

    def test_build_cognitive_entity(self):
        entity = {
            "element_id": "cfm:business_rule:valid-email",
            "element_name": "Valid Email Format",
            "element_type": "business_rule",
            "model_source": "cfm",
            "bloom_level": "Analyzing",
            "cognitive_weight": 4.0,
            "partial_score": 8.0,
        }
        result = EntityScoreBuilder.build_cognitive_entity(entity)
        assert result.type == "business_rule"
        assert result.score == 8.0
        assert result.metadata["bloom_level"] == "Analyzing"
        assert result.metadata["cognitive_weight"] == 4.0

    def test_build_tshirt_entity(self):
        entity = {
            "element_id": "cfm:functional_process:place-order",
            "element_name": "Place Order",
            "story_point_value": 8,
            "tshirt_size": "M",
            "mapping_rule": "default_v1",
        }
        result = EntityScoreBuilder.build_tshirt_entity(entity)
        assert result.type == "functional_process"
        assert result.score == 8.0
        assert result.metadata["tshirt_size"] == "M"

    def test_build_fpa_entity_unknown_function_type_defaults_to_operation(self):
        entity = {
            "id": "cfm:operation:test",
            "name": "Test",
            "function_type": "UNKNOWN",
            "complexity": "Low",
            "det_count": 1,
            "ufp_weight": 5,
        }
        result = EntityScoreBuilder.build_fpa_entity(entity)
        assert result.type == "operation"


class TestMetricBreakdownBuilder:
    def test_build_all_full_data(self):
        raw = {
            "fpa_entities": [
                {
                    "id": "cfm:data_group:profile",
                    "name": "Profile",
                    "function_type": "ILF",
                    "complexity": "Low",
                    "det_count": 5,
                    "ret_count": 1,
                    "ufp_weight": 10,
                },
                {
                    "id": "cfm:operation:register",
                    "name": "Register",
                    "function_type": "EI",
                    "complexity": "Average",
                    "det_count": 8,
                    "ftr_count": 2,
                    "ufp_weight": 4,
                },
            ],
            "storypoints_entities": [
                {
                    "element_id": "cfm:functional_process:order",
                    "element_name": "Order",
                    "raw_score": 10.5,
                    "normalized_value": 8,
                    "factor_breakdown": {"business_interactions": 2.0},
                    "applied_rules": ["default"],
                },
            ],
        }
        builder = MetricBreakdownBuilder(raw)
        entries = builder.build_all(metrics_filter=["fpa", "sp"])
        assert len(entries) == 2

        fpa_entry = next(e for e in entries if e.name == "fpa")
        assert fpa_entry.metric == "function_points"
        assert fpa_entry.total == 14.0
        assert fpa_entry.entity_count == 2
        assert fpa_entry.status == "success"
        assert fpa_entry.unit == "ufp"
        assert len(fpa_entry.entities) == 2

        sp_entry = next(e for e in entries if e.name == "sp")
        assert sp_entry.metric == "story_points"
        assert sp_entry.total == 8.0
        assert sp_entry.entity_count == 1
        assert sp_entry.status == "success"

    def test_build_all_empty_entities(self):
        raw = {
            "fpa_entities": [],
        }
        builder = MetricBreakdownBuilder(raw)
        entries = builder.build_all(metrics_filter=["fpa"])
        assert len(entries) == 1
        entry = entries[0]
        assert entry.total == 0.0
        assert entry.entity_count == 0
        assert entry.entities == []
        assert entry.status == "success"

    def test_build_all_missing_entity_key(self):
        raw: dict = {}
        builder = MetricBreakdownBuilder(raw)
        entries = builder.build_all(metrics_filter=["fpa"])
        assert len(entries) == 1
        entry = entries[0]
        assert entry.total == 0.0
        assert entry.entity_count == 0
        assert entry.status == "success"

    def test_build_all_filter_produces_only_selected(self):
        raw = {
            "fpa_entities": [
                {
                    "id": "cfm:data_group:x",
                    "name": "x",
                    "function_type": "ILF",
                    "complexity": "Low",
                    "det_count": 1,
                    "ufp_weight": 10,
                }
            ],
            "storypoints_entities": [
                {
                    "element_id": "cfm:functional_process:y",
                    "element_name": "y",
                    "raw_score": 5.0,
                    "normalized_value": 5,
                    "factor_breakdown": {},
                    "applied_rules": [],
                }
            ],
            "token_entities": [
                {
                    "element_id": "csm:operation:z",
                    "element_name": "z",
                    "element_type": "operation",
                    "model_source": "cfm",
                    "applied_weight": 1.0,
                    "partial_score": 3.0,
                }
            ],
        }
        builder = MetricBreakdownBuilder(raw)
        entries = builder.build_all(metrics_filter=["fpa", "tp"])
        names = {e.name for e in entries}
        assert names == {"fpa", "tp"}

    def test_build_all_error_entry(self):
        raw = {
            "fpa_entities": "not-a-list",
        }
        builder = MetricBreakdownBuilder(raw)
        entries = builder.build_all(metrics_filter=["fpa"])
        assert len(entries) == 1
        entry = entries[0]
        assert entry.entity_count == 0
        assert entry.entities == []

    def test_build_all_metadata_fpa(self):
        raw = {
            "fpa_entities": [
                {
                    "id": "cfm:data_group:x",
                    "name": "x",
                    "function_type": "ILF",
                    "complexity": "Low",
                    "det_count": 1,
                    "ufp_weight": 10,
                },
            ],
            "fpa_vaf": 1.0,
        }
        builder = MetricBreakdownBuilder(raw)
        entries = builder.build_all(metrics_filter=["fpa"])
        entry = entries[0]
        assert entry.metadata is not None
        assert entry.metadata["method"] == "ifpug"
        assert entry.metadata["vaf"] == 1.0

    def test_uniform_schema_all_entries(self):
        raw = {
            "fpa_entities": [
                {
                    "id": "cfm:data_group:a",
                    "name": "a",
                    "function_type": "ILF",
                    "complexity": "Low",
                    "det_count": 1,
                    "ufp_weight": 10,
                }
            ],
            "storypoints_entities": [
                {
                    "element_id": "cfm:functional_process:b",
                    "element_name": "b",
                    "raw_score": 5.0,
                    "normalized_value": 5,
                    "factor_breakdown": {},
                    "applied_rules": [],
                }
            ],
        }
        builder = MetricBreakdownBuilder(raw)
        entries = builder.build_all(metrics_filter=["fpa", "sp"])
        for entry in entries:
            assert hasattr(entry, "name")
            assert hasattr(entry, "metric")
            assert hasattr(entry, "total")
            assert hasattr(entry, "unit")
            assert hasattr(entry, "entity_count")
            assert hasattr(entry, "entities")
            assert hasattr(entry, "status")
        metric_keys = {
            "name",
            "metric",
            "total",
            "unit",
            "entity_count",
            "entities",
            "status",
        }
        entity_keys = {"id", "name", "type", "score"}
        for entry in entries:
            dumped = entry.model_dump(mode="json")
            assert metric_keys.issubset(dumped.keys()), f"Missing keys in {entry.name}"
            for entity in entry.entities:
                ed = entity.model_dump(mode="json")
                assert entity_keys.issubset(ed.keys()), (
                    f"Missing entity keys in {entry.name}"
                )


class TestSaveMetricsJson:
    def test_save_metrics_json_with_data(self, tmp_path: Path):
        project_path = tmp_path / "project"
        project_path.mkdir()
        measure_id = "test-001"

        mock_result = MagicMock()
        mock_result.measurement_result_raw = {
            "fpa_entities": [
                {
                    "id": "cfm:data_group:x",
                    "name": "X",
                    "function_type": "ILF",
                    "complexity": "Low",
                    "det_count": 1,
                    "ufp_weight": 10,
                },
            ],
        }

        result_path = save_metrics_json(
            project_path, measure_id, mock_result, metrics_filter=["fpa"]
        )
        assert result_path is not None
        assert result_path.exists()

        data = json.loads(result_path.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["name"] == "fpa"
        assert data[0]["status"] == "success"
        assert data[0]["entity_count"] == 1
        assert data[0]["total"] == 10.0

    def test_save_metrics_json_empty_raw(self, tmp_path: Path):
        project_path = tmp_path / "project"
        project_path.mkdir()
        measure_id = "test-002"

        mock_result = MagicMock()
        mock_result.measurement_result_raw = {}

        result_path = save_metrics_json(project_path, measure_id, mock_result)
        assert result_path is not None
        data = json.loads(result_path.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["status"] == "failed"

    def test_save_metrics_json_no_measurement_result_raw(self, tmp_path: Path):
        project_path = tmp_path / "project"
        project_path.mkdir()
        measure_id = "test-003"

        mock_result = MagicMock(spec=[])
        result_path = save_metrics_json(project_path, measure_id, mock_result)
        assert result_path is not None
        data = json.loads(result_path.read_text(encoding="utf-8"))
        assert data[0]["status"] == "failed"
