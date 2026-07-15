from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    EvidenceRef,
    FunctionalProcess,
)
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.plugins.rule_pack.plugin import RulePackEnginePlugin


@pytest.fixture
def cfm() -> CanonicalFunctionalModel:
    metadata = BuildMetadata(
        run_id="test-run",
        created_at=datetime.now(timezone.utc),
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
            yaml.dump({
                "id": "test-pack",
                "rules": [
                    {
                        "id": "exclude-eq",
                        "type": "exclusion",
                        "config": {"function_types": ["EQ"]},
                    },
                ],
            }, f)

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
