from __future__ import annotations

from pathlib import Path

from structlog.testing import capture_logs

from specmetrics.kernel._rule_parsing import build_rule


def _path() -> Path:
    return Path("rules/x.yaml")


def test_build_rule_non_dict_returns_none_and_logs_event():
    """Kills build_rule__mutmut_2 and build_rule__mutmut_5 (event argument of the rule_entry_not_dict warning)."""
    with capture_logs() as logs:
        result = build_rule("not-a-dict", 0, _path())
    assert result is None
    assert logs[0]["event"] == "rule_entry_not_dict"
    assert logs[0]["path"] == "rules/x.yaml"
    assert logs[0]["index"] == 0


def test_build_rule_missing_rid_keeps_index_and_path():
    """Kills build_rule__mutmut_13 and build_rule__mutmut_14 (index/path passed to _validated_rid)."""
    with capture_logs() as logs:
        result = build_rule({"type": "fact", "priority": 5}, 2, _path())
    assert result is None
    assert logs[0]["event"] == "rule_missing_id"
    assert logs[0]["path"] == "rules/x.yaml"
    assert logs[0]["index"] == 2


def test_build_rule_invalid_type_keeps_index_and_path():
    """Kills build_rule__mutmut_20 and build_rule__mutmut_21 (index/path passed to _validated_type)."""
    with capture_logs() as logs:
        result = build_rule({"rule_id": "r1", "type": "banana", "priority": 5}, 2, _path())
    assert result is None
    assert logs[0]["event"] == "rule_invalid_type"
    assert logs[0]["path"] == "rules/x.yaml"
    assert logs[0]["index"] == 2


def test_build_rule_keeps_confidence_index_path_and_event():
    """Kills build_rule__mutmut_27/28, _validated_confidence__mutmut_18/19/21/22/23/27 (confidence validation log args)."""
    with capture_logs() as logs:
        result = build_rule(
            {"rule_id": "r1", "type": "fact", "priority": 5, "confidence": 2.0}, 2, _path()
        )
    assert result is None
    assert logs[0]["event"] == "rule_invalid_confidence"
    assert logs[0]["path"] == "rules/x.yaml"
    assert logs[0]["index"] == 2
    assert logs[0]["confidence"] == 2.0


def test_build_rule_keeps_priority_index_path_and_event():
    """Kills build_rule__mutmut_34/35, _validated_priority__mutmut_18/19/21/22/23/27 (priority validation log args)."""
    with capture_logs() as logs:
        result = build_rule({"rule_id": "r1", "type": "fact", "priority": 0}, 2, _path())
    assert result is None
    assert logs[0]["event"] == "rule_invalid_priority"
    assert logs[0]["path"] == "rules/x.yaml"
    assert logs[0]["index"] == 2
    assert logs[0]["priority"] == 0


def test_build_rule_keeps_pattern_index_and_path():
    """Kills build_rule__mutmut_41 and build_rule__mutmut_42 (index/path passed to _pattern_from)."""
    with capture_logs() as logs:
        result = build_rule(
            {"rule_id": "r1", "type": "fact", "priority": 5, "pattern": 42}, 2, _path()
        )
    assert result is None
    assert logs[0]["event"] == "rule_invalid_pattern"
    assert logs[0]["path"] == "rules/x.yaml"
    assert logs[0]["index"] == 2


def test_build_rule_uses_provided_name():
    """Kills build_rule__mutmut_65/66/68/70/71 (name lookup must read the 'name' key)."""
    rule = build_rule(
        {"rule_id": "r1", "type": "fact", "priority": 5, "name": "Invoice"}, 0, _path()
    )
    assert rule is not None
    assert rule.name == "Invoice"


def test_build_rule_name_falls_back_to_rid():
    """Kills build_rule__mutmut_67 and build_rule__mutmut_69 (default fallback for name must be the rule id)."""
    rule = build_rule({"rule_id": "r1", "type": "fact", "priority": 5}, 0, _path())
    assert rule is not None
    assert rule.name == "r1"


def test_build_rule_keeps_provided_confidence():
    """Kills _validated_confidence__mutmut_20 and _validated_confidence__mutmut_24 (confidence must be forwarded)."""
    rule = build_rule(
        {"rule_id": "r1", "type": "fact", "priority": 5, "confidence": 0.5}, 0, _path()
    )
    assert rule is not None
    assert rule.confidence == 0.5


def test_build_rule_keeps_provided_priority():
    """Kills _validated_priority__mutmut_20 and _validated_priority__mutmut_24 (priority must be forwarded)."""
    rule = build_rule(
        {"rule_id": "r1", "type": "fact", "priority": 42}, 0, _path()
    )
    assert rule is not None
    assert rule.priority == 42


def test_build_rule_validation_error_logs_full_context():
    """Kills build_rule__mutmut_95/96/97/98/99/100/101/104/105 (rule_validation_error log event, path, index, error)."""
    with capture_logs() as logs:
        result = build_rule(
            {"rule_id": "r1", "type": "fact", "priority": 5, "name": ""}, 3, _path()
        )
    assert result is None
    assert logs[0]["event"] == "rule_validation_error"
    assert logs[0]["path"] == "rules/x.yaml"
    assert logs[0]["index"] == 3
    assert isinstance(logs[0]["error"], str)
    assert "at least 1 character" in logs[0]["error"]


def test_validated_rid_rejects_blank_rid():
    """Kills _validated_rid__mutmut_14 and _validated_rid__mutmut_17 (blank rule_id must be rejected and logged)."""
    with capture_logs() as logs:
        result = build_rule({"rule_id": "", "type": "fact", "priority": 5}, 0, _path())
    assert result is None
    assert logs[0]["event"] == "rule_missing_id"


def test_validated_type_logs_invalid_event():
    """Kills _validated_type__mutmut_14 and _validated_type__mutmut_18 (event name of rule_invalid_type warning)."""
    with capture_logs() as logs:
        result = build_rule({"rule_id": "r1", "type": "banana", "priority": 5}, 0, _path())
    assert result is None
    assert logs[0]["event"] == "rule_invalid_type"


def test_build_rule_confidence_defaults_to_zero():
    """Kills _validated_confidence__mutmut_3/5/8 (default confidence must be 0.0)."""
    rule = build_rule({"rule_id": "r1", "type": "fact", "priority": 5}, 0, _path())
    assert rule is not None
    assert rule.confidence == 0.0


def test_build_rule_rejects_non_numeric_confidence():
    """Kills _validated_confidence__mutmut_11 (isinstance check on confidence must not be bypassed)."""
    with capture_logs() as logs:
        result = build_rule(
            {"rule_id": "r1", "type": "fact", "priority": 5, "confidence": "1.0"}, 0, _path()
        )
    assert result is None
    assert logs[0]["event"] == "rule_invalid_confidence"


def test_build_rule_rejects_negative_confidence():
    """Kills _validated_confidence__mutmut_10 (confidence below 0 must be invalid)."""
    with capture_logs() as logs:
        result = build_rule(
            {"rule_id": "r1", "type": "fact", "priority": 5, "confidence": -1.0}, 0, _path()
        )
    assert result is None
    assert logs[0]["event"] == "rule_invalid_confidence"


def test_build_rule_accepts_zero_confidence():
    """Kills _validated_confidence__mutmut_12 (confidence equal to 0 must be valid)."""
    rule = build_rule(
        {"rule_id": "r1", "type": "fact", "priority": 5, "confidence": 0.0}, 0, _path()
    )
    assert rule is not None
    assert rule.confidence == 0.0


def test_build_rule_accepts_one_confidence():
    """Kills _validated_confidence__mutmut_14 (confidence equal to 1 must be valid)."""
    rule = build_rule(
        {"rule_id": "r1", "type": "fact", "priority": 5, "confidence": 1.0}, 0, _path()
    )
    assert rule is not None
    assert rule.confidence == 1.0


def test_build_rule_rejects_confidence_above_one():
    """Kills _validated_confidence__mutmut_15 (confidence above 1 must be invalid)."""
    with capture_logs() as logs:
        result = build_rule(
            {"rule_id": "r1", "type": "fact", "priority": 5, "confidence": 1.5}, 0, _path()
        )
    assert result is None
    assert logs[0]["event"] == "rule_invalid_confidence"


def test_build_rule_rejects_non_int_priority():
    """Kills _validated_priority__mutmut_10 and _validated_priority__mutmut_11 (isinstance check on priority)."""
    with capture_logs() as logs:
        result = build_rule(
            {"rule_id": "r1", "type": "fact", "priority": "high"}, 0, _path()
        )
    assert result is None
    assert logs[0]["event"] == "rule_invalid_priority"


def test_build_rule_accepts_minimum_priority():
    """Kills _validated_priority__mutmut_12 and _validated_priority__mutmut_13 (priority equal to 1 must be valid)."""
    rule = build_rule({"rule_id": "r1", "type": "fact", "priority": 1}, 0, _path())
    assert rule is not None
    assert rule.priority == 1


def test_build_rule_accepts_maximum_priority():
    """Kills _validated_priority__mutmut_14 (priority equal to 100 must be valid)."""
    rule = build_rule({"rule_id": "r1", "type": "fact", "priority": 100}, 0, _path())
    assert rule is not None
    assert rule.priority == 100


def test_build_rule_rejects_priority_above_one_hundred():
    """Kills _validated_priority__mutmut_15 (priority above 100 must be invalid)."""
    with capture_logs() as logs:
        result = build_rule({"rule_id": "r1", "type": "fact", "priority": 101}, 0, _path())
    assert result is None
    assert logs[0]["event"] == "rule_invalid_priority"


def test_build_rule_pattern_defaults_to_empty_dict():
    """Kills _pattern_from__mutmut_5 (missing pattern must default to an empty mapping)."""
    rule = build_rule({"rule_id": "r1", "type": "fact", "priority": 5}, 0, _path())
    assert rule is not None
    assert rule.pattern == {}


def test_build_rule_invalid_pattern_logs_event():
    """Kills _pattern_from__mutmut_10 and _pattern_from__mutmut_13 (event name of rule_invalid_pattern warning)."""
    with capture_logs() as logs:
        result = build_rule(
            {"rule_id": "r1", "type": "fact", "priority": 5, "pattern": 42}, 0, _path()
        )
    assert result is None
    assert logs[0]["event"] == "rule_invalid_pattern"
