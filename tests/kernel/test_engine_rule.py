from __future__ import annotations

from specmetrics.kernel.engine_rule import RulePackMeta


class TestRulePackMetaFromYaml:
    def test_missing_framework_defaults_to_empty(self) -> None:
        meta = RulePackMeta.from_yaml({})
        assert meta.framework == ""

    def test_framework_flow_through(self) -> None:
        meta = RulePackMeta.from_yaml({"framework": "openspec"})
        assert meta.framework == "openspec"

    def test_missing_description_defaults_to_empty(self) -> None:
        meta = RulePackMeta.from_yaml({})
        assert meta.description == ""

    def test_description_flow_through(self) -> None:
        meta = RulePackMeta.from_yaml({"description": "A rule pack"})
        assert meta.description == "A rule pack"

    def test_version_and_document_types(self) -> None:
        meta = RulePackMeta.from_yaml(
            {"version": "1.0.0", "document_types": ["section", "feature"]}
        )
        assert meta.version == "1.0.0"
        assert meta.document_types == ["section", "feature"]
