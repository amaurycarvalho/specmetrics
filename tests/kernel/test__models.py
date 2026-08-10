"""Tests for specmetrics.kernel._models."""

from __future__ import annotations

import re
import time
import uuid
from collections import deque

import pytest
import structlog

from specmetrics.kernel._models import (
    BatchRequest,
    DocumentPayload,
    LLMCallRecord,
    RateLimiter,
)

_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


def _doc(document_id: str, content: str = "") -> DocumentPayload:
    return DocumentPayload(document_id, content, "spec")


def test_call_record_default_fields():
    """Kills LLMCallRecord::__init____mutmut_1/2/3/4/5 (default 0 -> 1)."""
    rec = LLMCallRecord("openai", "gpt-4o-mini")
    assert rec.prompt_tokens == 0
    assert rec.response_tokens == 0
    assert rec.duration_ms == 0
    assert rec.rate_limit_delay_ms == 0
    assert rec.retry_count == 0


def test_call_record_default_status():
    """Kills LLMCallRecord::__init____mutmut_6/7 (status 'success')."""
    assert LLMCallRecord("p", "m").status == "success"


def test_call_record_call_id_is_uuid():
    """Kills LLMCallRecord::__init____mutmut_8/9 (call_id -> None / 'None')."""
    rec = LLMCallRecord("p", "m")
    assert isinstance(rec.call_id, str)
    assert rec.call_id != "None"
    uuid.UUID(rec.call_id)


def test_call_record_explicit_values():
    """Kills LLMCallRecord::__init____mutmut_11 (model -> None) and
    __mutmut_14 (duration_ms -> None)."""
    rec = LLMCallRecord("openai", "model-x", duration_ms=123)
    assert rec.provider == "openai"
    assert rec.model == "model-x"
    assert rec.duration_ms == 123
    assert rec.rate_limit_delay_ms == 0
    assert rec.retry_count == 0


def test_call_record_error_message():
    """Kills LLMCallRecord::__init____mutmut_18 (error_message -> None)."""
    rec = LLMCallRecord("p", "m", status="failed", error_message="boom")
    assert rec.error_message == "boom"
    assert rec.status == "failed"


def test_call_record_timestamp_format():
    """Kills LLMCallRecord::__init____mutmut_19 (timestamp -> None),
    __mutmut_23 (strftime arg dropped) and __mutmut_24/25/26 (format string)."""
    rec = LLMCallRecord("p", "m")
    assert isinstance(rec.timestamp, str)
    assert _TIMESTAMP_RE.match(rec.timestamp) is not None


def test_call_record_timestamp_strftime_args(monkeypatch):
    """Kills LLMCallRecord::__init____mutmut_23 (strftime second arg dropped)."""
    calls = []
    fake_gmtime = object()
    monkeypatch.setattr(time, "gmtime", lambda: fake_gmtime)
    monkeypatch.setattr(
        time,
        "strftime",
        lambda fmt, *rest: calls.append((fmt, rest)) or "2020-01-01T00:00:00",
    )
    LLMCallRecord("p", "m")
    assert calls == [("%Y-%m-%dT%H:%M:%S", (fake_gmtime,))]


def test_call_record_to_dict_keys():
    """Verifies to_dict serializes every field."""
    rec = LLMCallRecord("openai", "m", prompt_tokens=1, response_tokens=2)
    data = rec.to_dict()
    assert data["call_id"] == rec.call_id
    assert data["provider"] == "openai"
    assert data["model"] == "m"
    assert data["prompt_tokens"] == 1
    assert data["response_tokens"] == 2
    assert data["status"] == "success"
    assert data["timestamp"] == rec.timestamp


def test_rate_limiter_zero_rpm_returns_zero():
    """Verifies zero/negative rpm short-circuits."""
    assert RateLimiter(0).acquire() == 0.0
    assert RateLimiter(-1).acquire() == 0.0


def test_rate_limiter_empty_returns_zero():
    """Verifies empty timestamps return zero delay."""
    assert RateLimiter(5).acquire() == 0.0


def test_rate_limiter_positive_delay(monkeypatch):
    """Kills RateLimiter::acquire__mutmut_2 (<= 0 -> <= 1)."""
    rl = RateLimiter(1)
    rl.timestamps = deque([955.0])
    monkeypatch.setattr(time, "monotonic", lambda: 1000.0)
    assert rl.acquire() == 15.0


def test_rate_limiter_prune_window(monkeypatch):
    """Kills RateLimiter::acquire__mutmut_7 (cutoff now - 60.0 -> 61.0)."""
    rl = RateLimiter(1)
    rl.timestamps = deque([939.5, 941.0])
    monkeypatch.setattr(time, "monotonic", lambda: 1000.0)
    assert rl.acquire() == 1.0


def test_rate_limiter_prune_boundary(monkeypatch):
    """Kills RateLimiter::acquire__mutmut_10 (< cutoff -> <= cutoff)."""
    rl = RateLimiter(1)
    rl.timestamps = deque([940.0])
    monkeypatch.setattr(time, "monotonic", lambda: 1000.0)
    assert rl.acquire() == 0.0


def test_rate_limiter_uses_oldest_timestamp(monkeypatch):
    """Kills RateLimiter::acquire__mutmut_13 (oldest = timestamps[0] -> [1])."""
    rl = RateLimiter(1)
    rl.timestamps = deque([955.0, 950.0])
    monkeypatch.setattr(time, "monotonic", lambda: 1000.0)
    assert rl.acquire() == 15.0


def test_rate_limiter_delay_formula(monkeypatch):
    """Kills RateLimiter::acquire__mutmut_15 (60.0 - (now - oldest) -> +) and
    __mutmut_16 (60.0 -> 61.0)."""
    rl = RateLimiter(1)
    rl.timestamps = deque([955.0])
    monkeypatch.setattr(time, "monotonic", lambda: 1000.0)
    assert rl.acquire() == 15.0


def test_rate_limiter_sub_second_delay(monkeypatch):
    """Kills RateLimiter::acquire__mutmut_19 (delay > 0 -> delay > 1)."""
    rl = RateLimiter(1)
    rl.timestamps = deque([940.5])
    monkeypatch.setattr(time, "monotonic", lambda: 1000.0)
    assert rl.acquire() == 0.5


def test_wait_and_record_zero_delay_does_not_sleep(monkeypatch):
    """Kills RateLimiter::wait_and_record__mutmut_2 (delay > 0 -> >= 0)."""
    sleeps = []

    def fake_sleep(value):
        sleeps.append(value)
        raise KeyboardInterrupt

    rl = RateLimiter(5)
    monkeypatch.setattr(type(rl), "acquire", lambda self: 0.0)
    monkeypatch.setattr(time, "sleep", fake_sleep)
    monkeypatch.setattr(time, "monotonic", lambda: 1000.0)
    assert rl.wait_and_record() == 0.0
    assert sleeps == []
    assert len(rl.timestamps) == 1


def test_wait_and_record_sleeps_positive_delay(monkeypatch):
    """Kills RateLimiter::wait_and_record__mutmut_3 (delay > 0 -> > 1) and
    __mutmut_4 (time.sleep(None))."""
    sleeps = []
    rl = RateLimiter(5)
    monkeypatch.setattr(type(rl), "acquire", lambda self: 0.5)
    monkeypatch.setattr(time, "sleep", lambda value: sleeps.append(value))
    monkeypatch.setattr(time, "monotonic", lambda: 2000.0)
    assert rl.wait_and_record() == 0.5
    assert sleeps == [0.5]


def test_wait_and_record_interrupt_logs(monkeypatch):
    """Kills RateLimiter::wait_and_record__mutmut_6/7/8 (interrupt log fields)."""
    rl = RateLimiter(5)
    monkeypatch.setattr(type(rl), "acquire", lambda self: 0.5)

    def fake_sleep(value):
        raise KeyboardInterrupt

    monkeypatch.setattr(time, "sleep", fake_sleep)
    monkeypatch.setattr(time, "monotonic", lambda: 3000.0)
    with structlog.testing.capture_logs() as logs, pytest.raises(KeyboardInterrupt):
        rl.wait_and_record()
    assert logs and logs[0]["event"] == "rate_limiter_interrupted"
    assert logs[0]["completed_calls"] == len(rl.timestamps)


def test_batch_request_keeps_json_schema():
    """Kills BatchRequest::__init____mutmut_3 (json_schema -> None)."""
    schema = {"type": "object"}
    b = BatchRequest("SYS", [_doc("a")], schema)
    assert b.json_schema == schema


def test_assemble_prompt_exact_output():
    """Kills BatchRequest::assemble_prompt__mutmut_3 (doc_list -> None),
    __mutmut_5 (', ' join) and __mutmut_8 ('\\n\\n' join)."""
    b = BatchRequest("SYS", [_doc("a", "A"), _doc("b", "B")])
    assert b.assemble_prompt() == (
        'Document "a": A\n\n'
        'Document "b": B\n\n'
        'Respond with a JSON object keyed by document ID: '
        '{"a": {"elements": [...]}, "b": {"elements": [...]}}'
    )


def test_estimate_chars_exact():
    """Kills BatchRequest::_estimate_chars__mutmut_5 (+ len(document_id) -> -)."""
    b = BatchRequest("SYS", [_doc("ab", "cde")])
    assert b._estimate_chars() == len("SYS") + len("cde") + len("ab") + 50


def test_split_returns_self_within_limit():
    """Kills BatchRequest::split__mutmut_1 (<= max_chars -> <)."""
    b = BatchRequest("S", [_doc("1"), _doc("2")])
    result = b.split(b._estimate_chars())
    assert len(result) == 1
    assert result[0] is b


def test_split_sub_batch_fields():
    """Kills BatchRequest::split__mutmut_12/24 (system_prompt -> None) and
    __mutmut_14/17/26/29 (json_schema -> None)."""
    schema = {"type": "object"}
    b = BatchRequest("S", [_doc("1"), _doc("2"), _doc("3")], schema)
    for sub in b.split(52):
        assert sub.system_prompt == "S"
        assert sub.json_schema == schema


def test_split_counts_with_extra_chars():
    """Kills BatchRequest::split__mutmut_6 (+ _EXTRA_CHARS_PER_DOC -> -)."""
    b = BatchRequest("S", [_doc("1"), _doc("2"), _doc("3")])
    result = b.split(103)
    assert len(result) == 2
    assert [sub.documents[0].document_id for sub in result] == ["1", "3"]


def test_split_counts_with_id_length():
    """Kills BatchRequest::split__mutmut_7 (+ len(document_id) -> -)."""
    b = BatchRequest("S", [_doc("12345", "x"), _doc("12345", "x"), _doc("12345", "x")])
    result = b.split(101)
    assert len(result) == 3


def test_split_oversized_document_single_batch():
    """Kills BatchRequest::split__mutmut_8 (and current_docs -> or current_docs)."""
    b = BatchRequest("S", [_doc("long", "x" * 200)])
    result = b.split(100)
    assert len(result) == 1
    assert [sub.documents[0].document_id for sub in result] == ["long"]


def test_split_boundary_equality():
    """Kills BatchRequest::split__mutmut_10 (> max_chars -> >= max_chars)."""
    b = BatchRequest("S", [_doc("1"), _doc("2"), _doc("3")])
    result = b.split(103)
    assert len(result) == 2


def test_split_accumulated_size_reset():
    """Kills BatchRequest::split__mutmut_21 (current_size += doc_size -> = doc_size)."""
    b = BatchRequest("S", [_doc("1"), _doc("2"), _doc("3")])
    result = b.split(103)
    assert len(result) == 2
