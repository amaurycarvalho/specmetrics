from __future__ import annotations

from structlog.testing import capture_logs

from specmetrics.kernel._matching import MatchingMixin
from specmetrics.kernel._rule_execution import ExecutionMixin
from specmetrics.kernel._visitor_state import Observation
from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.engine_rule import ExtractionRule


class _TestEngine(ExecutionMixin, MatchingMixin):
    """Minimal engine combining the execution and matching mixins."""

    def __init__(
        self,
        observations: list[Observation] | None = None,
        fail_ids: set[str] | None = None,
    ) -> None:
        self._test_observations = observations or []
        self._fail_ids = fail_ids or set()

    def _run_visitors(self, tokens, state) -> None:
        state.observations = list(self._test_observations)

    def _attempt_rule(self, rule, doc, section_type, content, section_id, elements) -> str:
        if rule.id in self._fail_ids:
            return "failed"
        return super()._attempt_rule(
            rule, doc, section_type, content, section_id, elements
        )


def _doc(
    content: str = "invoice info here",
    document_type: str = "SPEC",
    doc_id: str = "doc1",
) -> Document:
    return Document(
        id=doc_id,
        path="p.md",
        document_type=document_type,
        content=content,
    )


def _rule(
    rule_id: str,
    *,
    document_type: str = "",
    target_sections: list[str] | None = None,
    pattern: dict | None = None,
) -> ExtractionRule:
    return ExtractionRule(
        id=rule_id,
        name=rule_id,
        pattern=pattern or {"regex": "invoice"},
        type="fact",
        confidence=1.0,
        priority=5,
        document_type=document_type,
        target_sections=target_sections or [],
    )


def _obs(
    content: str = "invoice info here",
    section_type: str | None = None,
    section_id: str = "sec-1",
) -> Observation:
    context: dict[str, str] = {}
    if section_type is not None:
        context["section_type"] = section_type
    return Observation(
        type="paragraph",
        content=content,
        context=context,
        location=("", section_id),
    )


def test_execute_rules_without_markdown_it_returns_empty(monkeypatch):
    """Kills ExecutionMixin::_execute_rules__mutmut_2/5/6/14/15 (markdown_it_not_available branch)."""
    import specmetrics.kernel._rule_execution as rex

    monkeypatch.setattr(rex, "_md", None)
    doc = _doc()
    rules = [_rule("r1"), _rule("r2")]
    with capture_logs() as logs:
        result = _TestEngine()._execute_rules(doc, rules)
    assert result == ([], 0, 0, 2, set())
    assert logs[0]["event"] == "markdown_it_not_available"


def test_execute_rules_skips_binary_content():
    """Kills ExecutionMixin::_execute_rules__mutmut_7/8/10 (binary content skip path)."""
    binary = "".join(chr(c) for c in range(1, 20)) * 10
    doc = _doc(content=binary)
    rules = [_rule("r1")]
    with capture_logs() as logs:
        result = _TestEngine()._execute_rules(doc, rules)
    assert result == ([], 0, 0, 1, set())
    assert logs[0]["event"] == "skipping_binary_content"
    assert logs[0]["doc_id"] == "doc1"


def test_execute_rules_with_no_observations_returns_zero_counters():
    """Kills ExecutionMixin::_execute_rules__mutmut_27/29/31 (counter initial values must be zero)."""
    result = _TestEngine()._execute_rules(_doc(), [_rule("r1"), _rule("r2")])
    assert result == ([], 0, 0, 0, set())


def test_execute_rules_lowercases_document_type():
    """Kills ExecutionMixin::_execute_rules__mutmut_33/34/35 (document_type normalization)."""
    doc = _doc(document_type="SPEC")
    rule = _rule("r1", document_type="spec")
    result = _TestEngine([_obs()])._execute_rules(doc, [rule])
    assert result[1] == 1
    assert result[2] == 1


def test_execute_rules_document_type_fallback_is_empty_string():
    """Kills ExecutionMixin::_execute_rules__mutmut_36 (missing document_type must normalize to empty string)."""
    doc = _doc(document_type="")
    rule = _rule("r1", document_type="XXXX")
    result = _TestEngine([_obs()])._execute_rules(doc, [rule])
    assert result[1] == 0


def test_execute_rules_uses_section_type_for_targeting():
    """Kills ExecutionMixin::_execute_rules__mutmut_37/38/40/42/43 (section_type read from context)."""
    doc = _doc()
    rule = _rule("r1", target_sections=["overview"])
    obs = _obs(section_type="Overview")
    result = _TestEngine([obs])._execute_rules(doc, [rule])
    assert result[1] == 1
    assert result[2] == 1


def test_execute_rules_missing_section_type_defaults_to_empty():
    """Kills ExecutionMixin::_execute_rules__mutmut_39/41 (missing section_type must default to empty string)."""
    doc = _doc()
    rule = _rule("r1", target_sections=[""])
    obs = _obs(section_type=None)
    result = _TestEngine([obs])._execute_rules(doc, [rule])
    assert result[1] == 1


def test_execute_rules_section_type_fallback_not_uppercased():
    """Kills ExecutionMixin::_execute_rules__mutmut_44 (missing section_type must default to empty, not 'XXXX')."""
    doc = _doc()
    rule = _rule("r1", target_sections=["xxxx"])
    obs = _obs(section_type=None)
    result = _TestEngine([obs])._execute_rules(doc, [rule])
    assert result[1] == 0


def test_execute_rules_preserves_section_id_in_evidence():
    """Kills ExecutionMixin::_execute_rules__mutmut_46 (section_id must come from observation location)."""
    doc = _doc()
    rule = _rule("r1")
    obs = _obs(section_id="sec-7")
    result = _TestEngine([obs])._execute_rules(doc, [rule])
    assert result[0][0].evidence.section_id == "sec-7"


def test_execute_rules_passes_doc_type_and_section_type_to_rule_applies():
    """Kills ExecutionMixin::_execute_rules__mutmut_50/51 (both doc_type and section_type passed to _rule_applies)."""
    doc = _doc(document_type="SPEC")
    rule = _rule("r1", document_type="spec", target_sections=["overview"])
    obs = _obs(section_type="Overview")
    result = _TestEngine([obs])._execute_rules(doc, [rule])
    assert result[1] == 1
    assert result[2] == 1


def test_execute_rules_continues_to_next_rule_after_skip():
    """Kills ExecutionMixin::_execute_rules__mutmut_55 (non-applying rule must not break the loop)."""
    doc = _doc()
    skip_rule = _rule("skip", document_type="other")
    apply_rule = _rule("apply")
    result = _TestEngine([_obs()])._execute_rules(doc, [skip_rule, apply_rule])
    assert result[1] == 1
    assert result[2] == 1


def test_execute_rules_counts_attempted_rules():
    """Kills ExecutionMixin::_execute_rules__mutmut_56/57/58 (rules_attempted increments by one per rule)."""
    doc = _doc()
    rules = [_rule("r1"), _rule("r2")]
    result = _TestEngine([_obs()])._execute_rules(doc, rules)
    assert result[1] == 2


def test_execute_rules_counts_matched_status():
    """Kills ExecutionMixin::_execute_rules__mutmut_72/73/74 (matched status must increment succeeded)."""
    doc = _doc()
    rule = _rule("r1")
    result = _TestEngine([_obs()])._execute_rules(doc, [rule])
    assert result[2] == 1
    assert result[3] == 0


def test_execute_rules_counts_succeeded_rules():
    """Kills ExecutionMixin::_execute_rules__mutmut_75/76/77 (rules_succeeded increments by one per match)."""
    doc = _doc()
    rules = [_rule("r1"), _rule("r2")]
    result = _TestEngine([_obs()])._execute_rules(doc, rules)
    assert result[2] == 2


def test_execute_rules_counts_failed_status():
    """Kills ExecutionMixin::_execute_rules__mutmut_78/79/80 (failed status must increment failed)."""
    doc = _doc()
    rule = _rule("f1")
    result = _TestEngine([_obs()], fail_ids={"f1"})._execute_rules(doc, [rule])
    assert result[3] == 1


def test_execute_rules_counts_failed_rules():
    """Kills ExecutionMixin::_execute_rules__mutmut_81/82/83 (rules_failed increments by one per failure)."""
    doc = _doc()
    rules = [_rule("f1"), _rule("f2")]
    result = _TestEngine([_obs()], fail_ids={"f1", "f2"})._execute_rules(doc, rules)
    assert result[3] == 2


def test_execute_rules_tracks_failed_rule_ids():
    """Kills ExecutionMixin::_execute_rules__mutmut_84 (failed rule ids must be added to the set)."""
    doc = _doc()
    rule = _rule("f1")
    result = _TestEngine([_obs()], fail_ids={"f1"})._execute_rules(doc, [rule])
    assert result[4] == {"f1"}


def test_run_visitors_logs_visitor_failure(monkeypatch):
    """Kills ExecutionMixin::_run_visitors__mutmut_5/8 (visitor_failed warning event)."""
    import specmetrics.kernel._rule_execution as rex
    from specmetrics.kernel.engine_visitors import ExtractionState

    class _BoomVisitor:
        def visit(self, tokens, state) -> None:
            raise RuntimeError("boom")

    monkeypatch.setattr(rex, "_VISITORS", [_BoomVisitor()])
    with capture_logs() as logs:
        rex.ExecutionMixin()._run_visitors([], ExtractionState())
    assert logs[0]["event"] == "visitor_failed"
    assert logs[0]["visitor"] == "_BoomVisitor"
    assert logs[0]["error"] == "boom"
