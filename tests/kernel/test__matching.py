"""Tests for specmetrics.kernel._matching."""

from __future__ import annotations

import hashlib

import structlog

from specmetrics.kernel._matching import (
    MatchingMixin,
    _content_hash,
    _is_likely_binary,
)
from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.engine_rule import ExtractionRule


def _rule(pattern: dict, **kwargs) -> ExtractionRule:
    base = {
        "id": "r1",
        "name": "Rule 1",
        "pattern": pattern,
        "type": "fact",
        "confidence": 0.8,
        "priority": 1,
    }
    base.update(kwargs)
    return ExtractionRule(**base)


def _doc(**kwargs) -> Document:
    base = {"id": "d1", "path": "p.md", "document_type": "spec", "content": "x"}
    base.update(kwargs)
    return Document(**base)


def test_is_likely_binary_empty_content_false():
    """Kills _is_likely_binary__mutmut_2 (return False -> True)."""
    assert _is_likely_binary("") is False
    assert _is_likely_binary("plain human text") is False


def test_is_likely_binary_threshold_sum():
    """Kills _is_likely_binary__mutmut_5 (sum 1 -> 2)."""
    assert _is_likely_binary("\x01\x02abcdefgh") is False


def test_is_likely_binary_exact_boundary():
    """Kills _is_likely_binary__mutmut_13 (> -> >=)."""
    assert _is_likely_binary("\x01\x02\x03abcdefg") is False


def test_is_likely_binary_control_definition():
    """Kills _is_likely_binary__mutmut_8/9 (ord < 32 -> <= 32 / < 33)."""
    assert _is_likely_binary("a b") is False


def test_is_likely_binary_allows_whitespace_controls():
    """Kills _is_likely_binary__mutmut_10/11 (exclusion set membership)."""
    assert _is_likely_binary("a\nb") is False


def test_is_likely_binary_ratio_division():
    """Kills _is_likely_binary__mutmut_12 (/ -> *)."""
    assert _is_likely_binary("\x01abcdefghi") is False


def test_content_hash_matches_exact_raw():
    """Kills _content_hash__mutmut_2/3 (section_id or '' variants)."""
    expected = hashlib.sha256(b"doc::::txt").hexdigest()[:16]
    assert _content_hash("doc", None, "txt") == expected
    expected2 = hashlib.sha256(b"doc::sec::txt").hexdigest()[:16]
    assert _content_hash("doc", "sec", "txt") == expected2


def test_content_hash_short_digest():
    """Kills _content_hash__mutmut_5 ([:16] -> [:17])."""
    value = _content_hash("doc", None, "txt")
    assert isinstance(value, str)
    assert len(value) == 16


def test_match_rule_regex_branch():
    """Kills MatchingMixin::_match_rule_against_observation__mutmut_2/3/4
    (regex key lookups) and __mutmut_5/6/7/8/9/10/11/12 (regex call variants)."""
    m = MatchingMixin()
    rule = _rule({"regex": "alpha"})
    assert m._match_rule_against_observation(rule, "s", "h", "contains alpha here") is True


def test_match_rule_heading_branch():
    """Kills MatchingMixin::_match_rule_against_observation__mutmut_13/14/15
    (heading key lookups) and __mutmut_16/17/18/19/20/21 (heading call variants)."""
    m = MatchingMixin()
    rule = _rule({"heading": "Installation"})
    assert m._match_rule_against_observation(rule, "unrelated", "Installation", "y") is True


def test_match_rule_regex_error_logs_rule_id():
    """Kills MatchingMixin::_match_rule_against_observation__mutmut_8
    (rule.id -> None in regex call)."""
    m = MatchingMixin()
    rule = _rule({"regex": "["}, id="regex_rule")
    with structlog.testing.capture_logs() as logs:
        result = m._match_rule_against_observation(rule, "s", "h", "content")
    assert result is False
    assert logs and logs[0]["event"] == "regex_error"
    assert logs[0]["rule_id"] == "regex_rule"
    assert logs[0]["pattern"] == "["


def test_match_rule_structure_branch():
    """Kills MatchingMixin::_match_rule_against_observation__mutmut_29/30/31/32
    (structure key lookups)."""
    m = MatchingMixin()
    assert m._match_rule_against_observation(_rule({"structure": True}), "s", "h", "c") is True
    assert m._match_rule_against_observation(_rule({}), "s", "h", "c") is False


def test_match_heading_pattern_returns_true_on_match():
    """Kills MatchingMixin::_match_heading_pattern__mutmut_17 (return True -> False)."""
    m = MatchingMixin()
    assert m._match_heading_pattern({"heading": "Installation"}, "installation", "h") is True


def test_match_heading_pattern_returns_false_on_mismatch():
    """Kills MatchingMixin::_match_heading_pattern__mutmut_18 (return False -> True)."""
    m = MatchingMixin()
    assert m._match_heading_pattern({"heading": "Installation"}, "requirements", "requirements") is False


def test_match_heading_pattern_default_missing_key():
    """Kills MatchingMixin::_match_heading_pattern__mutmut_1/4/5/8
    (heading get defaults)."""
    m = MatchingMixin()
    assert m._match_heading_pattern({}, "guide", "guide") is False
    assert m._match_heading_pattern({"heading": "Guide"}, "guide", "guide") is True


def test_match_heading_pattern_heading_key():
    """Kills MatchingMixin::_match_heading_pattern__mutmut_2/6/7 (heading key variants)."""
    m = MatchingMixin()
    assert m._match_heading_pattern({"heading": "Guide"}, "guide", "x") is True


def test_match_heading_pattern_candidates_list():
    """Kills MatchingMixin::_match_heading_pattern__mutmut_9 (candidates=None) and
    __mutmut_12 (match_values=None)."""
    m = MatchingMixin()
    assert m._match_heading_pattern({"heading": "Guide"}, "guide", "x") is True


def test_match_heading_pattern_append_heading_text():
    """Kills MatchingMixin::_match_heading_pattern__mutmut_11 (append(None))."""
    m = MatchingMixin()
    assert m._match_heading_pattern({"heading": "Installation"}, "guide", "Installation") is True


def test_match_heading_pattern_matches_heading_text():
    """Kills MatchingMixin::_match_heading_pattern__mutmut_14/15/16
    (comparison operators)."""
    m = MatchingMixin()
    assert m._match_heading_pattern({"heading": "Installation"}, "guide", "installation") is True


def test_match_heading_pattern_non_str_value_skipped():
    """Kills MatchingMixin::_match_heading_pattern__mutmut_13 (and -> or)."""
    m = MatchingMixin()
    assert m._match_heading_pattern({"heading": [123, "Requirement"]}, "requirement", "x") is True


def test_match_heading_pattern_no_match_returns_false():
    """Kills MatchingMixin::_match_heading_pattern__mutmut_11 (append(None))."""
    m = MatchingMixin()
    assert m._match_heading_pattern({"heading": "Nope"}, "a", "b") is False


def test_match_keyword_pattern_default_keywords():
    """Kills MatchingMixin::_match_keyword_pattern__mutmut_3/5 (keywords default)."""
    m = MatchingMixin()
    assert m._match_keyword_pattern({}, "zz") is True


def test_match_keyword_pattern_keywords_present():
    """Kills MatchingMixin::_match_keyword_pattern__mutmut_19 (in -> not in)."""
    m = MatchingMixin()
    assert m._match_keyword_pattern({"keywords": ["alpha"]}, "text alpha text") is True


def test_match_keyword_pattern_default_min_matches():
    """Kills MatchingMixin::_match_keyword_pattern__mutmut_10/12
    (min_matches default to len(keywords))."""
    m = MatchingMixin()
    assert m._match_keyword_pattern({"keywords": ["alpha"]}, "alpha") is True


def test_match_keyword_pattern_min_matches_boundary():
    """Kills MatchingMixin::_match_keyword_pattern__mutmut_21 (>= -> >)."""
    m = MatchingMixin()
    assert m._match_keyword_pattern({"keywords": ["alpha"], "min_matches": 1}, "alpha") is True


def test_match_keyword_pattern_min_matches_key():
    """Kills MatchingMixin::_match_keyword_pattern__mutmut_9/13/14
    (min_matches key lookups)."""
    m = MatchingMixin()
    assert m._match_keyword_pattern({"keywords": ["a", "b"], "min_matches": 1}, "only a here") is True


def test_match_keyword_pattern_sum_increment():
    """Kills MatchingMixin::_match_keyword_pattern__mutmut_17 (sum 1 -> 2)."""
    m = MatchingMixin()
    assert m._match_keyword_pattern({"keywords": ["a", "b", "c"], "min_matches": 2}, "only a here") is False


def test_rule_applies_matching_document_type():
    """Kills MatchingMixin::_rule_applies__mutmut_2 (== -> !=)."""
    m = MatchingMixin()
    rule = _rule({"structure": True}, document_type="spec")
    assert m._rule_applies(rule, "spec", "section") is True


def test_rule_applies_wrong_document_type():
    """Kills MatchingMixin::_rule_applies__mutmut_3 (return False -> True)."""
    m = MatchingMixin()
    rule = _rule({"structure": True}, document_type="spec")
    assert m._rule_applies(rule, "adr", "section") is False


def test_rule_applies_section_type_lowercased():
    """Kills MatchingMixin::_rule_applies__mutmut_4/5 (section_type lower)."""
    m = MatchingMixin()
    rule = _rule({"structure": True}, target_sections=["Requirements"])
    assert m._rule_applies(rule, "spec", "requirements") is True


def test_rule_applies_section_match():
    """Kills MatchingMixin::_rule_applies__mutmut_6/7/8 (target_sections any)."""
    m = MatchingMixin()
    rule = _rule({"structure": True}, target_sections=["spec"])
    assert m._rule_applies(rule, "spec", "spec") is True


def test_rule_applies_section_mismatch():
    """Kills MatchingMixin::_rule_applies__mutmut_9/10 (target_sections negation)."""
    m = MatchingMixin()
    rule = _rule({"structure": True}, target_sections=["spec"])
    assert m._rule_applies(rule, "spec", "other") is False


def test_attempt_rule_returns_matched_and_builds_element():
    """Kills MatchingMixin::_attempt_rule__mutmut_13 (section_id -> None)."""
    m = MatchingMixin()
    rule = _rule({"regex": "needle"})
    doc = _doc()
    elements = []
    assert m._attempt_rule(rule, doc, "s", "a needle here", "sec1", elements) == "matched"
    assert len(elements) == 1
    assert elements[0].evidence.section_id == "sec1"


def test_attempt_rule_returns_skipped():
    """Kills MatchingMixin::_attempt_rule__mutmut_33/34 ('skipped' literal)."""
    m = MatchingMixin()
    rule = _rule({"regex": "nope"})
    elements = []
    assert m._attempt_rule(rule, _doc(), "s", "no match", None, elements) == "skipped"
    assert elements == []


def test_attempt_rule_returns_failed_on_error():
    """Kills MatchingMixin::_attempt_rule__mutmut_31/32 ('failed' literal)."""
    m = MatchingMixin()
    rule = _rule({"regex": 123})
    assert m._attempt_rule(rule, _doc(), "s", "x", None, []) == "failed"


def test_attempt_rule_logs_rule_execution_failed():
    """Kills MatchingMixin::_attempt_rule__mutmut_21/22/23/24/25/26/27/30
    (warning log fields)."""
    m = MatchingMixin()
    rule = _rule({"regex": 123})
    doc = _doc(id="docX")
    with structlog.testing.capture_logs() as logs:
        m._attempt_rule(rule, doc, "s", "x", None, [])
    assert logs and logs[0]["event"] == "rule_execution_failed"
    assert logs[0]["rule_id"] == "r1"
    assert logs[0]["doc_id"] == "docX"
    assert logs[0]["error"] == "first argument must be string or compiled pattern"


def test_build_element_fields():
    """Kills MatchingMixin::_build_element__mutmut_2/3/4 (hash args),
    __mutmut_10/14 (section_id) and __mutmut_16 (rule_id)."""
    m = MatchingMixin()
    rule = _rule({"regex": "x"}, type="entity")
    doc = _doc()
    elem = m._build_element(rule, doc, "body text", "s7")
    expected_id = hashlib.sha256(b"d1::s7::body text").hexdigest()[:16]
    assert elem.id == expected_id
    assert elem.type == "entity"
    assert elem.content == "body text"
    assert elem.confidence == 0.8
    assert elem.evidence.document_id == "d1"
    assert elem.evidence.section_id == "s7"
    assert elem.evidence.text == "body text"
    assert elem.evidence.rule_id == "r1"


def test_build_element_without_section():
    """Verifies _build_element handles None section_id consistently."""
    m = MatchingMixin()
    rule = _rule({"regex": "x"})
    elem = m._build_element(rule, _doc(), "body text", None)
    expected_id = hashlib.sha256(b"d1::::body text").hexdigest()[:16]
    assert elem.id == expected_id
    assert elem.evidence.section_id is None
