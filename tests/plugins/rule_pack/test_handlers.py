from __future__ import annotations

from datetime import UTC, datetime

from structlog.testing import capture_logs

from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    EvidenceRef,
    FunctionalProcess,
)
from specmetrics.kernel.cfm.models import Rule, RuleConfig, RulePack
from specmetrics.plugins.rule_pack._handlers import (
    handle_complexity_override_rule,
    handle_element_exclusion_rule,
    handle_exclusion_rule,
    handle_vaf_rule,
    handle_weight_override_rule,
    log_unused_elements,
    log_unused_references,
    log_unused_types,
)
from specmetrics.plugins.rule_pack._state import RuleApplyState
from specmetrics.plugins.rule_pack.annotator import RuleAnnotator


def _make_cfm(
    processes: dict[str, dict] | None = None,
) -> CanonicalFunctionalModel:
    if processes is None:
        processes = {"fp-001": {"name": "Input", "function_type": "EI"}}
    metadata = BuildMetadata(
        run_id="test-run",
        created_at=datetime.now(UTC),
    )
    return CanonicalFunctionalModel(
        run_id="test-run",
        functional_processes={
            pid: FunctionalProcess(
                id=pid,
                name=props["name"],
                evidence=EvidenceRef(
                    graph_node_id=f"n-{pid}",
                    document_id="doc-1",
                    text=f"Process {props['name']}",
                ),
                metadata={"function_type": props.get("function_type", "EI")},
            )
            for pid, props in processes.items()
        },
        metadata=metadata,
    )


def _rule(rule_type: str, config: dict | None = None) -> Rule:
    return Rule(id="r1", type=rule_type, config=RuleConfig(**(config or {})))  # type: ignore[arg-type]


class TestHandleExclusionRule:
    def test_update_state_and_record(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        pack = RulePack(id="pack-1")
        rule = _rule("exclusion", {"function_types": ["EQ", "EI"]})
        handle_exclusion_rule(annotator, pack, rule, state)
        assert state.excluded_types == {"EQ", "EI"}
        record = annotator.records[0]
        assert record.rule_pack_id == "pack-1"
        assert record.rule_id == "r1"
        assert record.rule_type == "exclusion"
        assert record.description == "Excluded function types: EQ, EI"
        assert record.after_state == {"excluded_types": ["EQ", "EI"]}
        assert state.seen_for("exclusion") == {"EQ", "EI"}

    def test_duplicate_warns(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        pack = RulePack(id="pack-1")
        rule = _rule("exclusion", {"function_types": ["EQ"]})
        with capture_logs() as captured:
            handle_exclusion_rule(annotator, pack, rule, state)
            handle_exclusion_rule(annotator, pack, rule, state)
        events = [e for e in captured if e["event"] == "rule_pack_override_exclusion"]
        assert len(events) == 1
        assert events[0]["function_type"] == "EQ"
        assert "already defined" in events[0]["message"]

    def test_empty_function_types(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        rule = _rule("exclusion", {"function_types": []})
        handle_exclusion_rule(annotator, pack=RulePack(id="p"), rule=rule, state=state)
        assert state.excluded_types == set()
        assert annotator.records[0].description == "Excluded function types: "


class TestHandleElementExclusionRule:
    def test_updates_state(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        rule = _rule("element_exclusion", {"element_ids": ["fp-1", "fp-2"]})
        handle_element_exclusion_rule(annotator, RulePack(id="p"), rule, state)
        assert state.excluded_element_ids == {"fp-1", "fp-2"}
        record = annotator.records[0]
        assert record.rule_type == "element_exclusion"
        assert record.after_state == {"excluded_element_ids": ["fp-1", "fp-2"]}


class TestHandleComplexityOverrideRule:
    def test_updates_state(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        rule = _rule(
            "complexity_override",
            {"function_type": "EI", "thresholds": {"det": [2, 8], "ftr": [1, 2]}},
        )
        handle_complexity_override_rule(annotator, RulePack(id="p"), rule, state)
        assert len(state.complexity_overrides) == 1
        override = state.complexity_overrides[0]
        assert override["function_type"] == "EI"
        assert override["thresholds"] == {"det": [2, 8], "ftr": [1, 2]}
        assert state.seen_for("complexity_override") == {"EI"}

    def test_upper_case_function_type(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        rule = _rule("complexity_override", {"function_type": "ei", "thresholds": {"det": [2, 8]}})
        handle_complexity_override_rule(annotator, RulePack(id="p"), rule, state)
        assert state.seen_for("complexity_override") == {"EI"}


class TestHandleWeightOverrideRule:
    def test_updates_state(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        rule = _rule(
            "weight_override",
            {"function_type": "EI", "complexity": "High", "weight": 5},
        )
        handle_weight_override_rule(annotator, RulePack(id="p"), rule, state)
        assert len(state.weight_overrides) == 1
        override = state.weight_overrides[0]
        assert override == {
            "pack_id": "p",
            "rule_id": "r1",
            "function_type": "EI",
            "complexity": "High",
            "weight": 5,
        }

    def test_duplicate_warns(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        rule = _rule(
            "weight_override",
            {"function_type": "EI", "complexity": "High", "weight": 5},
        )
        with capture_logs() as captured:
            handle_weight_override_rule(annotator, RulePack(id="p"), rule, state)
            handle_weight_override_rule(annotator, RulePack(id="p"), rule, state)
        events = [e for e in captured if e["event"] == "rule_pack_override_weight"]
        assert len(events) == 1


class TestHandleVafRule:
    def test_computes_vaf(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        gsc = {k: 2 for k in [
            "data_communications", "distributed_data_processing", "performance",
            "heavily_used_configuration", "transaction_rate", "online_data_entry",
            "end_user_efficiency", "online_update", "complex_processing", "reusability",
            "installation_ease", "operational_ease", "multiple_sites", "facilitate_change",
        ]}
        rule = _rule("vaf", {"gsc": gsc})
        handle_vaf_rule(annotator, RulePack(id="p"), rule, state)
        assert state.vaf_value == 0.93
        record = annotator.records[0]
        assert record.after_state == {"vaf": 0.93, "gsc_total": 28}

    def test_empty_gsc_noop(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        rule = _rule("vaf", {"gsc": {}})
        handle_vaf_rule(annotator, RulePack(id="p"), rule, state)
        assert state.vaf_value is None
        assert annotator.records == []


class TestLogUnused:
    def _cfm(self) -> CanonicalFunctionalModel:
        return _make_cfm(
            {"fp-001": {"name": "Input", "function_type": "EI"}}
        )

    def test_unused_type_logged(self) -> None:
        pack = RulePack(id="p", rules=[_rule("exclusion", {"function_types": ["EQ", "EI"]})])
        with capture_logs() as captured:
            log_unused_references(self._cfm(), [pack])
        events = [e for e in captured if e["event"] == "rule_pack_unused_type"]
        assert len(events) == 1
        assert events[0]["function_type"] == "EQ"
        assert events[0]["rule_pack_id"] == "p"

    def test_used_type_not_logged(self) -> None:
        pack = RulePack(id="p", rules=[_rule("exclusion", {"function_types": ["EI"]})])
        with capture_logs() as captured:
            log_unused_references(self._cfm(), [pack])
        assert all(e["event"] != "rule_pack_unused_type" for e in captured)

    def test_unused_elements_logged(self) -> None:
        pack = RulePack(
            id="p", rules=[_rule("element_exclusion", {"element_ids": ["missing", "fp-001"]})]
        )
        with capture_logs() as captured:
            log_unused_references(self._cfm(), [pack])
        events = [e for e in captured if e["event"] == "rule_pack_unused_element"]
        assert len(events) == 1
        assert events[0]["element_id"] == "missing"

    def test_log_unused_types_direct(self) -> None:
        with capture_logs() as captured:
            log_unused_types(RulePack(id="p"), _rule("exclusion", {"function_types": ["EQ"]}), {"EI"})
        assert [e["event"] for e in captured] == ["rule_pack_unused_type"]

    def test_log_unused_elements_direct(self) -> None:
        with capture_logs() as captured:
            log_unused_elements(RulePack(id="p"), _rule("element_exclusion", {"element_ids": ["x"]}), {})
        assert [e["event"] for e in captured] == ["rule_pack_unused_element"]

    def test_unused_type_logged_full_fields(self) -> None:
        with capture_logs() as captured:
            log_unused_types(RulePack(id="p"), _rule("exclusion", {"function_types": ["EQ"]}), {"EI"})
        events = [e for e in captured if e["event"] == "rule_pack_unused_type"]
        assert len(events) == 1
        assert events[0]["rule_pack_id"] == "p"
        assert events[0]["rule_id"] == "r1"
        assert "not present in CFM" in events[0]["message"]

    def test_unused_element_full_fields(self) -> None:
        with capture_logs() as captured:
            log_unused_elements(RulePack(id="p"), _rule("element_exclusion", {"element_ids": ["x"]}), {})
        events = [e for e in captured if e["event"] == "rule_pack_unused_element"]
        assert len(events) == 1
        assert events[0]["rule_pack_id"] == "p"
        assert events[0]["rule_id"] == "r1"
        assert "not present in CFM" in events[0]["message"]

    def _cfm_meta_without_type(self, meta_key: str) -> CanonicalFunctionalModel:
        cfm = self._cfm()
        fp = cfm.functional_processes["fp-001"].model_copy(
            update={"metadata": {meta_key: "value"}}
        )
        return cfm.model_copy(update={"functional_processes": {"fp-001": fp}})

    def test_metadata_without_function_type_does_not_raise(self) -> None:
        cfm = self._cfm_meta_without_type("source")
        with capture_logs() as captured:
            log_unused_references(cfm, [RulePack(id="p", rules=[])])
        assert all(e["event"] != "rule_pack_unused_type" for e in captured)

    def test_no_blank_ft_reference_reported_as_unused(self) -> None:
        cfm = self._cfm_meta_without_type("source")
        pack = RulePack(id="p", rules=[_rule("exclusion", {"function_types": [""]})])
        with capture_logs() as captured:
            log_unused_references(cfm, [pack])
        assert all(e["event"] != "rule_pack_unused_type" for e in captured)


class TestExclusionDuplicates:
    def test_no_warning_on_first_call(self) -> None:
        with capture_logs() as captured:
            handle_exclusion_rule(
                RuleAnnotator(), RulePack(id="p"),
                _rule("exclusion", {"function_types": ["EQ"]}),
                RuleApplyState(),
            )
        assert all(e["event"] != "rule_pack_override_exclusion" for e in captured)

    def test_duplicate_warning_full_fields(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        pack = RulePack(id="pack-1", methodology="FPA")
        rule = _rule("exclusion", {"function_types": ["EQ", "EI"]})
        with capture_logs() as captured:
            handle_exclusion_rule(annotator, pack, rule, state)
            handle_exclusion_rule(annotator, pack, rule, state)
        events = [e for e in captured if e["event"] == "rule_pack_override_exclusion"]
        assert len(events) == 2
        assert events[0]["rule_pack_id"] == "pack-1"
        assert events[0]["rule_id"] == "r1"
        assert events[0]["message"].endswith("this pack's rule takes precedence")
        assert annotator.records[0].methodology == "FPA"


class TestElementExclusionRecord:
    def test_record_fields(self) -> None:
        annotator = RuleAnnotator()
        handle_element_exclusion_rule(
            annotator, RulePack(id="p"), _rule("element_exclusion", {"element_ids": ["fp-1"]}), RuleApplyState()
        )
        record = annotator.records[0]
        assert record.rule_type == "element_exclusion"
        assert record.description == "Excluded element IDs: fp-1"
        assert record.methodology == "FPA"


class TestComplexityOverrideExtended:
    def test_missing_function_type_seen_empty(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        rule = _rule("complexity_override", {"function_type": "", "thresholds": {"det": [2, 8]}})
        handle_complexity_override_rule(annotator, RulePack(id="p"), rule, state)
        assert state.seen_for("complexity_override") == {""}

    def test_no_warning_on_single_call(self) -> None:
        with capture_logs() as captured:
            handle_complexity_override_rule(
                RuleAnnotator(), RulePack(id="p"),
                _rule("complexity_override", {"function_type": "EI", "thresholds": {"det": [2, 8]}}),
                RuleApplyState(),
            )
        assert all(e["event"] != "rule_pack_override_complexity" for e in captured)

    def test_duplicate_warning_full_fields(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        pack = RulePack(id="p")
        rule = _rule("complexity_override", {"function_type": "EI", "thresholds": {"det": [2, 8]}})
        with capture_logs() as captured:
            handle_complexity_override_rule(annotator, pack, rule, state)
            handle_complexity_override_rule(annotator, pack, rule, state)
        events = [e for e in captured if e["event"] == "rule_pack_override_complexity"]
        assert len(events) == 1
        assert events[0]["rule_pack_id"] == "p"
        assert events[0]["rule_id"] == "r1"
        assert events[0]["function_type"] == "EI"
        assert "already defined" in events[0]["message"]
        assert events[0]["message"].endswith("this pack's rule takes precedence")

    def test_override_dict_full(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        rule = _rule("complexity_override", {"function_type": "EI", "thresholds": {"det": [2, 8]}})
        handle_complexity_override_rule(annotator, RulePack(id="p"), rule, state)
        assert state.complexity_overrides == [
            {"pack_id": "p", "rule_id": "r1", "function_type": "EI", "thresholds": {"det": [2, 8]}}
        ]

    def test_record_fields(self) -> None:
        annotator = RuleAnnotator()
        rule = _rule("complexity_override", {"function_type": "EI", "thresholds": {"det": [2, 8]}})
        handle_complexity_override_rule(annotator, RulePack(id="p", methodology="FPA"), rule, RuleApplyState())
        record = annotator.records[0]
        assert record.rule_type == "complexity_override"
        assert record.methodology == "FPA"
        assert record.after_state == {"function_type": "EI", "thresholds": {"det": [2, 8]}}


class TestWeightOverrideExtended:
    def test_seen_key_uses_function_and_complexity(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        rule = _rule("weight_override", {"function_type": "EI", "complexity": "High", "weight": 5})
        handle_weight_override_rule(annotator, RulePack(id="p"), rule, state)
        assert state.seen_for("weight_override") == {"EI|High"}

    def test_seen_key_empty_parts(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        rule = _rule("weight_override", {"function_type": "", "complexity": "", "weight": 5})
        handle_weight_override_rule(annotator, RulePack(id="p"), rule, state)
        assert state.seen_for("weight_override") == {"|"}

    def test_no_warning_on_single_call(self) -> None:
        with capture_logs() as captured:
            handle_weight_override_rule(
                RuleAnnotator(), RulePack(id="p"),
                _rule("weight_override", {"function_type": "EI", "complexity": "High", "weight": 5}),
                RuleApplyState(),
            )
        assert all(e["event"] != "rule_pack_override_weight" for e in captured)

    def test_duplicate_warning_full_fields(self) -> None:
        annotator = RuleAnnotator()
        state = RuleApplyState()
        rule = _rule("weight_override", {"function_type": "EI", "complexity": "High", "weight": 5})
        with capture_logs() as captured:
            handle_weight_override_rule(annotator, RulePack(id="p"), rule, state)
            handle_weight_override_rule(annotator, RulePack(id="p"), rule, state)
        events = [e for e in captured if e["event"] == "rule_pack_override_weight"]
        assert len(events) == 1
        assert events[0]["rule_id"] == "r1"
        assert events[0]["function_type"] == "EI"
        assert events[0]["complexity"] == "High"
        assert "already defined" in events[0]["message"]
        assert events[0]["message"].endswith("this pack's rule takes precedence")

    def test_record_fields(self) -> None:
        annotator = RuleAnnotator()
        rule = _rule("weight_override", {"function_type": "EI", "complexity": "High", "weight": 5})
        handle_weight_override_rule(annotator, RulePack(id="p"), rule, RuleApplyState())
        record = annotator.records[0]
        assert record.rule_type == "weight_override"
        assert record.methodology == "FPA"
        assert record.after_state == {"function_type": "EI", "complexity": "High", "weight": 5}


class TestVafRecord:
    def _gsc(self) -> dict:
        return {k: 2 for k in [
            "data_communications", "distributed_data_processing", "performance",
            "heavily_used_configuration", "transaction_rate", "online_data_entry",
            "end_user_efficiency", "online_update", "complex_processing", "reusability",
            "installation_ease", "operational_ease", "multiple_sites", "facilitate_change",
        ]}

    def test_record_fields(self) -> None:
        annotator = RuleAnnotator()
        rule = _rule("vaf", {"gsc": self._gsc()})
        handle_vaf_rule(annotator, RulePack(id="p"), rule, RuleApplyState())
        record = annotator.records[0]
        assert record.rule_type == "vaf"
        assert record.methodology == "FPA"
        assert record.after_state == {"vaf": 0.93, "gsc_total": 28}

class TestNotifyDuplicateReference:
    def test_logs_pack_and_rule_ids(self) -> None:
        from specmetrics.plugins.rule_pack._handlers import _notify_duplicate_reference

        with capture_logs() as captured:
            _notify_duplicate_reference(
                "rule_pack_override_exclusion",
                RulePack(id="pack-9"),
                _rule("exclusion", {"function_types": ["EQ"]}),
                function_type="EQ",
            )
        assert len(captured) == 1
        event = captured[0]
        assert event["event"] == "rule_pack_override_exclusion"
        assert event["rule_pack_id"] == "pack-9"
        assert event["rule_id"] == "r1"

    def test_extra_kwargs_forwarded(self) -> None:
        from specmetrics.plugins.rule_pack._handlers import _notify_duplicate_reference

        with capture_logs() as captured:
            _notify_duplicate_reference(
                "rule_pack_override_complexity",
                RulePack(id="pack-9"),
                _rule("complexity_override", {"function_type": "EI"}),
                function_type="EI",
                message="already defined",
            )
        event = captured[0]
        assert event["function_type"] == "EI"
        assert event["message"] == "already defined"
