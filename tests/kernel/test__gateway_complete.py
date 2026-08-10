from __future__ import annotations

from specmetrics.kernel._config import LLMGatewayConfig
from specmetrics.kernel._gateway_complete import CompleteMixin


def _mixin(**config_overrides) -> CompleteMixin:
    mixin = CompleteMixin.__new__(CompleteMixin)
    mixin.config = LLMGatewayConfig(**config_overrides)
    mixin.rate_limiter = None
    mixin.call_records = []
    return mixin


def test_build_messages_appends_instruction_for_unsupported_provider() -> None:
    """Kills _build_messages__mutmut_5 (``system +=`` -> ``system =``)."""
    mixin = _mixin()
    messages = mixin._build_messages("sys", "user", True, "anthropic")
    assert messages[0]["content"] == (
        "sys\n\nRespond with valid JSON only. No markdown fences."
    )
    assert messages[1]["content"] == "user"


def test_build_messages_no_instruction_for_openai() -> None:
    """Targets _build_messages__mutmut_2/4/7 (json_mode gating for a supported provider)."""
    mixin = _mixin()
    messages = mixin._build_messages("sys", "user", True, "openai")
    assert messages[0]["content"] == "sys"
    assert messages[1]["content"] == "user"


def test_build_messages_no_instruction_when_json_mode_off() -> None:
    """Kills _build_messages__mutmut_2 (``and`` -> ``or``)."""
    mixin = _mixin()
    messages = mixin._build_messages("sys", "user", False, "anthropic")
    assert messages[0]["content"] == "sys"


def test_enforce_json_response_rewrites_last_message_on_invalid() -> None:
    """Kills _enforce_json_response__mutmut_4 (``messages[-1]`` -> ``messages[+1]``)."""
    mixin = _mixin(max_retries=2)
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "user"},
        {"role": "user", "content": "extra"},
    ]
    result = mixin._enforce_json_response("not json", 0, messages, "user")
    assert result is True
    assert messages[2]["content"].startswith("You MUST respond with valid JSON only")
    assert messages[2]["content"].endswith("user")


def test_enforce_json_response_passes_valid_json() -> None:
    """Kills _enforce_json_response__mutmut_4 (``messages[-1]`` -> ``messages[+1]``)."""
    mixin = _mixin(max_retries=2)
    messages = [{"role": "system", "content": "sys"}, {"role": "user", "content": "u"}]
    assert mixin._enforce_json_response('{"ok": true}', 0, messages, "u") is False
    assert messages[1]["content"] == "u"


class _Usage:
    prompt_tokens = 10
    completion_tokens = 5


class _Resp:
    usage = _Usage()


class _RespNoUsage:
    pass


def test_extract_token_counts_uses_usage_block() -> None:
    """Targets _extract_token_counts__mutmut_6/13/25 (usage attribute access)."""
    mixin = _mixin()
    assert mixin._extract_token_counts(_Resp()) == (10, 5)


def test_extract_token_counts_defaults_to_zero_without_usage() -> None:
    """Kills _extract_token_counts__mutmut_6 (``getattr(response, "usage", )`` default dropped)."""
    mixin = _mixin()
    assert mixin._extract_token_counts(_RespNoUsage()) == (0, 0)


def test_record_success_records_provider_and_model() -> None:
    """Kills _record_success__mutmut_3 (model=None), mutmut_6 (duration_ms=None), mutmut_14 (duration_ms arg deletion)."""
    mixin = _mixin(model="gpt-4o-mini")
    mixin._record_success("openai", 123, 45, 0, 10, 5)
    assert len(mixin.call_records) == 1
    record = mixin.call_records[0]
    assert record.provider == "openai"
    assert record.model == "gpt-4o-mini"
    assert record.prompt_tokens == 10
    assert record.response_tokens == 5
    assert record.duration_ms == 123
    assert record.rate_limit_delay_ms == 45
    assert record.retry_count == 0
    assert record.status == "success"


def test_record_failure_records_error_details() -> None:
    """Kills _record_failure__mutmut_2 (provider=None), mutmut_3 (model=None), mutmut_4 (duration_ms=None), mutmut_5 (rate_limit_delay_ms=None), mutmut_8 (error_message=None), mutmut_11 (duration_ms arg deletion), mutmut_12 (rate_limit_delay_ms arg deletion), mutmut_15 (error_message arg deletion)."""
    mixin = _mixin(model="gpt-4o-mini")
    mixin._record_failure("openai", 200, 50, 1, "boom")
    assert len(mixin.call_records) == 1
    record = mixin.call_records[0]
    assert record.provider == "openai"
    assert record.model == "gpt-4o-mini"
    assert record.duration_ms == 200
    assert record.rate_limit_delay_ms == 50
    assert record.retry_count == 1
    assert record.status == "failed"
    assert record.error_message == "boom"
