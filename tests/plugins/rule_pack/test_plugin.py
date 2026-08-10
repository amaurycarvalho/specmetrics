from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from structlog.testing import capture_logs

from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    EvidenceRef,
    FunctionalProcess,
)
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.plugins.rule_pack.plugin import (
    RulePackEnginePlugin,
    create_rule_pack_engine_metadata,
)


@pytest.fixture
def cfm() -> CanonicalFunctionalModel:
    metadata = BuildMetadata(
        run_id="test-run",
        created_at=datetime.now(UTC),
    )
    return CanonicalFunctionalModel(
        run_id="test-run",
        functional_processes={
            "fp-001": FunctionalProcess(
                id="fp-001",
                name="User Login",
                evidence=EvidenceRef(
                    graph_node_id="n-001",
                    document_id="doc-1",
                    text="User login process",
                ),
                metadata={"function_type": "EI"},
            ),
            "fp-002": FunctionalProcess(
                id="fp-002",
                name="Generate Report",
                evidence=EvidenceRef(
                    graph_node_id="n-002",
                    document_id="doc-1",
                    text="Report generation",
                ),
                metadata={"function_type": "EO"},
            ),
        },
        metadata=metadata,
    )


@pytest.fixture
def plugin(tmp_path: Path) -> RulePackEnginePlugin:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    return RulePackEnginePlugin(str(rules_dir))


class TestRulePackEnginePlugin:
    def test_handle_no_cfm(self, plugin: RulePackEnginePlugin) -> None:
        ctx = PipelineContext()
        event = PipelineEvent(
            event_type=EventType.RULE_PACK_APPLIED,
            publisher="test",
            payload={},
            context=ctx,
        )
        result = plugin.handle(event)
        assert result == ctx

    def test_handle_no_rules(
        self,
        plugin: RulePackEnginePlugin,
        cfm: CanonicalFunctionalModel,
    ) -> None:
        ctx = PipelineContext()
        ctx = ctx.with_stage_output("canonical_model", cfm)
        event = PipelineEvent(
            event_type=EventType.RULE_PACK_APPLIED,
            publisher="test",
            payload={},
            context=ctx,
        )
        result = plugin.handle(event)
        annotated = result.canonical_model
        assert annotated is not None
        assert len(annotated.metadata.applied_rules) == 1
        assert annotated.metadata.applied_rules[0]["rule_type"] == "default"

    def test_handle_with_rules(
        self,
        plugin: RulePackEnginePlugin,
        cfm: CanonicalFunctionalModel,
        tmp_path: Path,
    ) -> None:
        rules_dir = Path(plugin._rules_dir)
        rule_pack_path = rules_dir / "test.yml"
        with open(rule_pack_path, "w") as f:
            yaml.dump(
                {
                    "id": "test-pack",
                    "rules": [
                        {
                            "id": "exclude-eq",
                            "type": "exclusion",
                            "config": {"function_types": ["EQ"]},
                        },
                    ],
                },
                f,
            )

        ctx = PipelineContext()
        ctx = ctx.with_stage_output("canonical_model", cfm)
        event = PipelineEvent(
            event_type=EventType.RULE_PACK_APPLIED,
            publisher="test",
            payload={},
            context=ctx,
        )
        result = plugin.handle(event)
        annotated = result.canonical_model
        assert annotated is not None
        assert len(annotated.metadata.applied_rules) >= 1
        applied_types = [r["rule_type"] for r in annotated.metadata.applied_rules]
        assert "exclusion" in applied_types

    def test_apply_rules_public_method(
        self,
        plugin: RulePackEnginePlugin,
        cfm: CanonicalFunctionalModel,
    ) -> None:
        result = plugin.apply_rules(cfm)
        assert result is not None
        assert result.run_id == cfm.run_id

    def test_handler_properties(self, plugin: RulePackEnginePlugin) -> None:
        assert plugin.handled_event_type == EventType.RULE_PACK_APPLIED
        assert plugin.handler_id == "rule_pack_engine"
        assert plugin.stage_name == "Rule Pack Engine"

    def test_handle_no_cfm_logs(self, plugin: RulePackEnginePlugin) -> None:
        ctx = PipelineContext()
        event = PipelineEvent(
            event_type=EventType.RULE_PACK_APPLIED,
            publisher="test",
            payload={},
            context=ctx,
        )
        with capture_logs() as captured:
            result = plugin.handle(event)
        assert result == ctx
        events = {e["event"] for e in captured}
        assert "rule_pack_engine_no_cfm" in events
        event_log = next(e for e in captured if e["event"] == "rule_pack_engine_no_cfm")
        assert event_log["execution_id"] == str(ctx.execution_id)
        assert event_log["actual_type"] == "NoneType"

    def test_handle_non_cfm_logs_actual_type(
        self, plugin: RulePackEnginePlugin
    ) -> None:
        ctx = PipelineContext()
        ctx = ctx.with_stage_output("canonical_model", 42)
        event = PipelineEvent(
            event_type=EventType.RULE_PACK_APPLIED,
            publisher="test",
            payload={},
            context=ctx,
        )
        with capture_logs() as captured:
            result = plugin.handle(event)
        assert ctx is result or result is not None
        event_log = next(
            e for e in captured if e["event"] == "rule_pack_engine_no_cfm"
        )
        assert event_log["actual_type"] == "int"

    def test_handle_started_logs(
        self, plugin: RulePackEnginePlugin, cfm: CanonicalFunctionalModel
    ) -> None:
        ctx = PipelineContext()
        ctx = ctx.with_stage_output("canonical_model", cfm)
        event = PipelineEvent(
            event_type=EventType.RULE_PACK_APPLIED,
            publisher="test",
            payload={},
            context=ctx,
        )
        with capture_logs() as captured:
            plugin.handle(event)
        events = {e["event"] for e in captured}
        assert "rule_pack_engine_started" in events
        assert "rule_pack_engine_no_rules" in events
        started = next(e for e in captured if e["event"] == "rule_pack_engine_started")
        assert started["execution_id"] == str(ctx.execution_id)
        assert started["rules_dir"] == plugin._rules_dir
        no_rules = next(
            e for e in captured if e["event"] == "rule_pack_engine_no_rules"
        )
        assert no_rules["execution_id"] == str(ctx.execution_id)

    def test_handle_loaded_logs(
        self, plugin: RulePackEnginePlugin, cfm: CanonicalFunctionalModel
    ) -> None:
        rules_dir = Path(plugin._rules_dir)
        with open(rules_dir / "test.yml", "w") as f:
            yaml.dump(
                {
                    "id": "test-pack",
                    "rules": [
                        {
                            "id": "ex-eq",
                            "type": "exclusion",
                            "config": {"function_types": ["EQ"]},
                        },
                    ],
                },
                f,
            )
        ctx = PipelineContext()
        ctx = ctx.with_stage_output("canonical_model", cfm)
        event = PipelineEvent(
            event_type=EventType.RULE_PACK_APPLIED,
            publisher="test",
            payload={},
            context=ctx,
        )
        with capture_logs() as captured:
            plugin.handle(event)
        events = {e["event"] for e in captured}
        assert "rule_pack_engine_started" in events
        assert "rule_pack_engine_loaded" in events
        loaded = next(e for e in captured if e["event"] == "rule_pack_engine_loaded")
        assert loaded["pack_count"] == 1
        assert loaded["total_rules"] >= 1
        assert loaded["active_rules"] >= 1

    def test_metadata(self) -> None:
        md = create_rule_pack_engine_metadata()
        assert md.id == "rule_pack_engine"
        assert md.api_version == "0.1.0"
        assert md.plugin_type.value == "measurement"
        assert md.handled_event_types == (EventType.RULE_PACK_APPLIED,)
        assert md.name == "Rule Pack Engine"
        assert md.description == (
            "Loads, validates, and applies Rule Pack rules to the Canonical Functional Model"
        )
        assert md.version == "0.1.0"
        handler = md.handler_factory()
        assert isinstance(handler, RulePackEnginePlugin)

    def test_handle_validation_error_and_warning_logs(
        self,
        plugin: RulePackEnginePlugin,
        cfm: CanonicalFunctionalModel,
    ) -> None:
        rules_dir = Path(plugin._rules_dir)
        with open(rules_dir / "test.yml", "w") as f:
            yaml.dump(
                {
                    "id": "test-pack",
                    "rules": [
                        {
                            "id": "ex-eq",
                            "type": "exclusion",
                            "config": {"function_types": ["EQ"]},
                        },
                        {
                            "id": "ex-eq",
                            "type": "exclusion",
                            "config": {"function_types": ["EQ"]},
                        },
                        {
                            "id": "ex-eq-2",
                            "type": "exclusion",
                            "config": {"function_types": ["EQ"]},
                        },
                    ],
                },
                f,
            )
        ctx = PipelineContext()
        ctx = ctx.with_stage_output("canonical_model", cfm)
        event = PipelineEvent(
            event_type=EventType.RULE_PACK_APPLIED,
            publisher="test",
            payload={},
            context=ctx,
        )
        with capture_logs() as captured:
            plugin.handle(event)
        events = {e["event"] for e in captured}
        assert "rule_pack_validation_error" in events
        assert "rule_pack_validation_warning" in events
        err = next(
            e for e in captured if e["event"] == "rule_pack_validation_error"
        )
        assert err["file"].endswith("test.yml")
        assert "Duplicate rule id" in err["message"]
        assert err["rule_id"] == "ex-eq"
        warn = next(
            e for e in captured if e["event"] == "rule_pack_validation_warning"
        )
        assert warn["file"].endswith("test.yml")
        assert "excluded by multiple rules" in warn["message"]
        assert warn["rule_id"] == "ex-eq"

    def test_handle_load_error_logs(
        self,
        plugin: RulePackEnginePlugin,
        cfm: CanonicalFunctionalModel,
    ) -> None:
        rules_dir = Path(plugin._rules_dir)
        with open(rules_dir / "broken.yml", "w") as f:
            yaml.dump({"rules": []}, f)
        ctx = PipelineContext()
        ctx = ctx.with_stage_output("canonical_model", cfm)
        event = PipelineEvent(
            event_type=EventType.RULE_PACK_APPLIED,
            publisher="test",
            payload={},
            context=ctx,
        )
        with capture_logs() as captured:
            result = plugin.handle(event)
        events = {e["event"] for e in captured}
        assert "rule_pack_validation_error" in events
        err = next(
            e for e in captured if e["event"] == "rule_pack_validation_error"
        )
        assert err["file"].endswith("broken.yml")
        assert "missing required 'id'" in err["message"]
        annotated = result.canonical_model
        assert annotated is not None
        assert len(annotated.metadata.applied_rules) == 1
        assert annotated.metadata.applied_rules[0]["rule_type"] == "default"

    def test_load_and_validate_merges_multiple_packs(
        self,
        plugin: RulePackEnginePlugin,
    ) -> None:
        rules_dir = Path(plugin._rules_dir)
        for name, rules in [
            (
                "a.yml",
                [
                    {
                        "id": "r1",
                        "type": "exclusion",
                        "config": {"function_types": ["EQ"]},
                    }
                ],
            ),
            (
                "b.yml",
                [
                    {
                        "id": "r2",
                        "type": "exclusion",
                        "config": {"function_types": ["EO"]},
                    }
                ],
            ),
        ]:
            with open(rules_dir / name, "w") as f:
                yaml.dump({"id": f"pack-{name[0]}", "rules": rules}, f)
        packs, report = plugin._load_and_validate()
        assert len(packs) == 2
        assert report.total_rules == 2
        assert report.active_rules == 2

    def test_load_and_validate_skips_broken_pack(
        self,
        plugin: RulePackEnginePlugin,
    ) -> None:
        rules_dir = Path(plugin._rules_dir)
        with open(rules_dir / "broken.yml", "w") as f:
            yaml.dump({"rules": []}, f)
        with open(rules_dir / "ok.yml", "w") as f:
            yaml.dump(
                {
                    "id": "ok",
                    "rules": [
                        {"id": "r1", "type": "exclusion", "config": {"function_types": ["EO"]}}
                    ],
                },
                f,
            )
        packs, report = plugin._load_and_validate()
        assert len(packs) == 1
        assert len(report.errors) == 1

    def test_apply_rules_with_packs(
        self,
        plugin: RulePackEnginePlugin,
        cfm: CanonicalFunctionalModel,
    ) -> None:
        rules_dir = Path(plugin._rules_dir)
        with open(rules_dir / "test.yml", "w") as f:
            yaml.dump(
                {
                    "id": "test-pack",
                    "rules": [
                        {
                            "id": "ex-eq",
                            "type": "exclusion",
                            "config": {"function_types": ["EQ"]},
                        },
                    ],
                },
                f,
            )
        result = plugin.apply_rules(cfm)
        assert result is not None
        assert result.run_id == cfm.run_id
        assert len(result.metadata.applied_rules) >= 1

    def test_apply_rules_empty_packs(self, plugin: RulePackEnginePlugin, cfm: CanonicalFunctionalModel) -> None:
        result = plugin.apply_rules(cfm, packs=[])
        assert result is cfm
