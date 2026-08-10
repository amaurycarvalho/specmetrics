from __future__ import annotations

from structlog.testing import capture_logs

from specmetrics.kernel._rule_loading import RuleLoadingMixin
from specmetrics.kernel.engine_rule import ExtractionRule


def _rule(rule_id: str, priority: int = 5) -> ExtractionRule:
    return ExtractionRule(
        id=rule_id,
        name=rule_id,
        pattern={"regex": "x"},
        type="fact",
        confidence=1.0,
        priority=priority,
    )


class _Stub(RuleLoadingMixin):
    def __init__(
        self,
        default: str | None = "custom.yaml",
        extras: list[str] | None = None,
    ) -> None:
        self._default_rule_pack = default
        self._extra_rule_packs = extras or []
        self.loaded: list[tuple[str, str | None]] = []
        self.resolved: list[tuple[str, str]] = []

    def _load_pack_safely(
        self, packs: list[list[ExtractionRule]], path: str, log_path: str | None = None
    ) -> None:
        self.loaded.append((path, log_path))

    def _resolve_rule_conflict(self, merged, rule, existing) -> None:
        self.resolved.append((rule.id, existing.id))


def test_load_rules_logs_total_and_conflicts():
    """Kills RuleLoadingMixin::_load_rules__mutmut_4/5/7/8 (rules_loaded log counts)."""
    stub = _Stub()
    stub._merge_rule_packs = lambda packs: ([_rule("r1"), _rule("r2")], 0)
    with capture_logs() as logs:
        result = stub._load_rules()
    assert len(result) == 2
    assert logs[0]["event"] == "rules_loaded"
    assert logs[0]["total_rules"] == 2
    assert logs[0]["conflicts_detected"] == 0


def test_collect_rule_packs_loads_configured_default():
    """Kills RuleLoadingMixin::_collect_rule_packs__mutmut_2 (configured default pack must be used)."""
    stub = _Stub(default="my/custom.yaml", extras=[])
    stub._collect_rule_packs()
    assert stub.loaded[0][0] == "my/custom.yaml"


def test_collect_rule_packs_loads_extra_packs_with_log_path():
    """Kills RuleLoadingMixin::_collect_rule_packs__mutmut_17/18/19/20/21/22 (extra pack args)."""
    stub = _Stub(extras=["a.yaml", "b.yaml"])
    stub._collect_rule_packs()
    assert stub.loaded == [
        ("custom.yaml", None),
        ("a.yaml", "a.yaml"),
        ("b.yaml", "b.yaml"),
    ]


def test_load_pack_safely_default_failure_logs_default_event():
    """Kills RuleLoadingMixin::_load_pack_safely__mutmut_3/4/6 (default pack failure branch)."""
    with capture_logs() as logs:
        RuleLoadingMixin()._load_pack_safely([], "/nonexistent/rules.yaml")
    assert logs[0]["event"] == "default_rule_pack_not_loaded"
    assert logs[0]["error"] == "Rule pack not found: /nonexistent/rules.yaml"


def test_load_pack_safely_extra_failure_logs_path_and_event():
    """Kills RuleLoadingMixin::_load_pack_safely__mutmut_11/14 (extra pack failure branch)."""
    with capture_logs() as logs:
        RuleLoadingMixin()._load_pack_safely(
            [], "/nonexistent/rules.yaml", log_path="extra.yaml"
        )
    assert logs[0]["event"] == "extra_rule_pack_not_loaded"
    assert logs[0]["path"] == "extra.yaml"


def test_merge_rule_packs_no_conflict_returns_zero():
    """Kills RuleLoadingMixin::_merge_rule_packs__mutmut_2 and __mutmut_3 (conflict_count initial value)."""
    stub = _Stub()
    merged, conflict_count = stub._merge_rule_packs(
        [[_rule("r1", priority=5)], [_rule("r2", priority=10)]]
    )
    assert conflict_count == 0
    assert [r.id for r in merged] == ["r2", "r1"]


def test_merge_rule_packs_detects_duplicate_rule():
    """Kills RuleLoadingMixin::_merge_rule_packs__mutmut_4/5 (existing rule lookup by id)."""
    stub = _Stub()
    merged, conflict_count = stub._merge_rule_packs([[_rule("r1")], [_rule("r1")]])
    assert conflict_count == 1
    assert [r.id for r in merged] == ["r1"]


def test_merge_rule_packs_counts_two_conflicts():
    """Kills RuleLoadingMixin::_merge_rule_packs__mutmut_8/9/10 (conflict_count increments by one)."""
    stub = _Stub()
    _merged, conflict_count = stub._merge_rule_packs(
        [[_rule("r1"), _rule("r2")], [_rule("r1"), _rule("r2")]]
    )
    assert conflict_count == 2


def test_merge_rule_packs_resolves_conflict_with_existing_rule():
    """Kills RuleLoadingMixin::_merge_rule_packs__mutmut_11/12/13/14/15/16 (conflict resolution args)."""
    stub = _Stub()
    first = _rule("r1", priority=5)
    second = _rule("r1", priority=10)
    merged, _ = stub._merge_rule_packs([[first], [second]])
    assert stub.resolved == [("r1", "r1")]
    assert [r.id for r in merged] == ["r1"]


def test_merge_rule_packs_sorts_by_priority_descending():
    """Kills RuleLoadingMixin::_merge_rule_packs__mutmut_22 (rules sorted by descending priority)."""
    stub = _Stub()
    low = _rule("low", priority=5)
    high = _rule("high", priority=10)
    merged, _ = stub._merge_rule_packs([[low, high]])
    assert [r.id for r in merged] == ["high", "low"]
