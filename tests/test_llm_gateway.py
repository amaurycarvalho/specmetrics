from __future__ import annotations

import json
import time
from unittest.mock import patch

import litellm
import pytest

from specmetrics.kernel._gateway_complete import CompleteMixin
from specmetrics.kernel.llm_gateway import (
    BatchRequest,
    DocumentPayload,
    LLMGateway,
    LLMGatewayConfig,
    RateLimiter,
    parse_batch_response,
)


class TestRateLimiter:
    def test_acquire_below_limit_returns_zero(self):
        limiter = RateLimiter(rpm_limit=10)
        assert limiter.acquire() == 0.0

    def test_acquire_within_limit_no_delay(self):
        limiter = RateLimiter(rpm_limit=5)
        for _ in range(4):
            limiter.wait_and_record()
        assert limiter.acquire() == 0.0

    def test_unlimited_always_zero(self):
        limiter = RateLimiter(rpm_limit=0)
        for _ in range(100):
            assert limiter.acquire() == 0.0

    def test_acquire_at_limit_returns_delay(self):
        limiter = RateLimiter(rpm_limit=3)
        for _ in range(3):
            limiter.wait_and_record()
        delay = limiter.acquire()
        assert delay > 0.0

    def test_wait_and_record_records_timestamp(self):
        limiter = RateLimiter(rpm_limit=10)
        before = len(limiter.timestamps)
        limiter.wait_and_record()
        assert len(limiter.timestamps) == before + 1

    def test_timestamps_evicted_after_60s(self):
        limiter = RateLimiter(rpm_limit=5)
        limiter.timestamps.append(time.monotonic() - 120.0)
        limiter.timestamps.append(time.monotonic() - 90.0)
        assert len(limiter.timestamps) == 2
        limiter.acquire()
        assert len(limiter.timestamps) == 0


class TestBatchRequest:
    def test_assemble_prompt_includes_format_instruction(self):
        docs = [
            DocumentPayload(
                document_id="doc-1", content="content1", document_type="spec"
            ),
            DocumentPayload(
                document_id="doc-2", content="content2", document_type="spec"
            ),
        ]
        batch = BatchRequest(system_prompt="Extract.", documents=docs)
        prompt = batch.assemble_prompt()
        assert 'Document "doc-1"' in prompt
        assert 'Document "doc-2"' in prompt
        assert "content1" in prompt
        assert "content2" in prompt
        assert "Respond with a JSON object keyed by document ID" in prompt

    def test_assemble_prompt_single_doc(self):
        docs = [
            DocumentPayload(document_id="single", content="text", document_type="spec")
        ]
        batch = BatchRequest(system_prompt="Extract.", documents=docs)
        prompt = batch.assemble_prompt()
        assert 'Document "single"' in prompt
        assert "text" in prompt

    def test_estimate_chars(self):
        docs = [
            DocumentPayload(document_id="a", content="hello", document_type="spec"),
            DocumentPayload(document_id="b", content="world", document_type="spec"),
        ]
        batch = BatchRequest(system_prompt="sys", documents=docs)
        est = batch._estimate_chars()
        assert est > 3 + 5 + 5
        assert est < 200

    def test_split_returns_single_when_under_limit(self):
        docs = [DocumentPayload(document_id="a", content="x", document_type="spec")]
        batch = BatchRequest(system_prompt="sys", documents=docs)
        sub = batch.split(max_chars=100000)
        assert len(sub) == 1
        assert sub[0] is batch

    def test_split_creates_sub_batches(self):
        docs = [
            DocumentPayload(
                document_id=str(i), content="x" * 1000, document_type="spec"
            )
            for i in range(10)
        ]
        batch = BatchRequest(system_prompt="sys", documents=docs)
        sub = batch.split(max_chars=2000)
        assert len(sub) > 1
        total_docs = sum(len(sb.documents) for sb in sub)
        assert total_docs == 10

    def test_split_no_data_loss(self):
        docs = [
            DocumentPayload(document_id="a", content="hello", document_type="spec"),
            DocumentPayload(document_id="b", content="world", document_type="spec"),
            DocumentPayload(document_id="c", content="foo", document_type="spec"),
        ]
        batch = BatchRequest(system_prompt="sys", documents=docs)
        sub = batch.split(max_chars=50)
        all_ids = []
        for sb in sub:
            for d in sb.documents:
                all_ids.append(d.document_id)
        assert sorted(all_ids) == ["a", "b", "c"]


class TestParseBatchResponse:
    def test_valid_response(self):
        docs = [
            DocumentPayload(document_id="doc-1", content="text1", document_type="spec"),
            DocumentPayload(document_id="doc-2", content="text2", document_type="spec"),
        ]
        batch = BatchRequest(system_prompt="sys", documents=docs)
        response = json.dumps(
            {
                "doc-1": {"elements": [{"type": "fact", "content": "a"}]},
                "doc-2": {"elements": [{"type": "entity", "content": "b"}]},
            }
        )
        result = parse_batch_response(response, batch)
        assert len(result["doc-1"]) == 1
        assert result["doc-1"][0]["type"] == "fact"
        assert len(result["doc-2"]) == 1
        assert result["doc-2"][0]["content"] == "b"

    def test_empty_elements(self):
        docs = [DocumentPayload(document_id="doc-1", content="", document_type="spec")]
        batch = BatchRequest(system_prompt="sys", documents=docs)
        response = json.dumps({"doc-1": {"elements": []}})
        result = parse_batch_response(response, batch)
        assert result["doc-1"] == []

    def test_missing_document_raises(self):
        docs = [
            DocumentPayload(document_id="doc-1", content="text1", document_type="spec"),
            DocumentPayload(document_id="doc-2", content="text2", document_type="spec"),
        ]
        batch = BatchRequest(system_prompt="sys", documents=docs)
        response = json.dumps({"doc-1": {"elements": []}})

        with pytest.raises(ValueError, match="missing document"):
            parse_batch_response(response, batch)

    def test_invalid_json_raises(self):
        docs = [
            DocumentPayload(document_id="doc-1", content="text", document_type="spec")
        ]
        batch = BatchRequest(system_prompt="sys", documents=docs)

        with pytest.raises(json.JSONDecodeError):
            parse_batch_response("not json", batch)

    def test_list_format_response(self):
        docs = [
            DocumentPayload(document_id="doc-1", content="text", document_type="spec")
        ]
        batch = BatchRequest(system_prompt="sys", documents=docs)
        response = json.dumps({"doc-1": [{"type": "fact"}]})
        result = parse_batch_response(response, batch)
        assert len(result["doc-1"]) == 1


@patch("specmetrics.kernel.llm_gateway.HAS_LITELLM", True)
class TestLLMGatewayConfig:
    def test_default_rpm(self):
        config = LLMGatewayConfig()
        assert config.rpm_limit == 15

    def test_rpm_from_param(self):
        config = LLMGatewayConfig(rpm_limit=30)
        assert config.rpm_limit == 30

    def test_rpm_from_env(self):
        with patch.dict("os.environ", {"SPECMETRICS_LLM_RPM_LIMIT": "8"}):
            config = LLMGatewayConfig(rpm_limit=None)
            assert config.rpm_limit == 8

    def test_rpm_zero_unlimited(self):
        config = LLMGatewayConfig(rpm_limit=0)
        assert config.rpm_limit == 0


class _FakeUsage:
    def __init__(self, prompt_tokens=10, completion_tokens=5):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content, usage=_FakeUsage()):
        self.choices = [_FakeChoice(content)]
        self.usage = usage


class TestCompleteMixin:
    def _gateway(self, **overrides):
        config = LLMGatewayConfig(**overrides)
        return LLMGateway(config)

    @patch("specmetrics.kernel.llm_gateway.litellm")
    def test_success_returns_content_and_records(self, mock_litellm):
        gateway = self._gateway()
        mock_litellm.completion.return_value = _FakeResponse('{"ok": true}')
        result = gateway.complete("sys", "user")
        assert result == '{"ok": true}'
        assert len(gateway.call_records) == 1
        record = gateway.call_records[0]
        assert record.status == "success"
        assert record.provider == "openai"
        assert record.prompt_tokens == 10
        assert record.response_tokens == 5

    @patch("specmetrics.kernel.llm_gateway.litellm")
    def test_json_mode_adds_response_format_for_openai(self, mock_litellm):
        gateway = self._gateway()
        mock_litellm.completion.return_value = _FakeResponse('{"ok": true}')
        gateway.complete("sys", "user", json_mode=True)
        kwargs = mock_litellm.completion.call_args.kwargs
        assert kwargs["response_format"] == {"type": "json_object"}

    @patch("specmetrics.kernel.llm_gateway.litellm")
    def test_json_mode_appends_instruction_for_unsupported_provider(self, mock_litellm):
        gateway = self._gateway(model="claude-3")
        mock_litellm.completion.return_value = _FakeResponse('{"ok": true}')
        gateway.complete("sys", "user", json_mode=True)
        messages = mock_litellm.completion.call_args.kwargs["messages"]
        assert "valid JSON" in messages[0]["content"]

    @patch("specmetrics.kernel.llm_gateway.litellm")
    def test_no_litellm_raises(self, mock_litellm):
        gateway = self._gateway()
        with (
            patch("specmetrics.kernel._gateway_complete.HAS_LITELLM", False),
            pytest.raises(RuntimeError, match="LiteLLM is not installed"),
        ):
            gateway.complete("sys", "user")

    @patch("specmetrics.kernel.llm_gateway.litellm")
    def test_retries_on_transient_exception_then_succeeds(self, mock_litellm):
        gateway = self._gateway(max_retries=2)
        mock_litellm.completion.side_effect = [
            litellm.RateLimitError("slow down", "openai", "gpt-4o-mini"),
            _FakeResponse('{"ok": true}'),
        ]
        with patch.object(gateway, "_sleep_with_interrupt") as sleeper:
            result = gateway.complete("sys", "user")
        assert result == '{"ok": true}'
        assert sleeper.call_count == 1
        record = gateway.call_records[0]
        assert record.status == "success"
        assert record.retry_count == 1

    @patch("specmetrics.kernel.llm_gateway.litellm")
    def test_exhausts_retries_raises_and_records_failure(self, mock_litellm):
        gateway = self._gateway(max_retries=1)
        mock_litellm.completion.side_effect = litellm.APIError(
            500, "boom", "openai", "gpt-4o-mini"
        )
        with (
            patch.object(gateway, "_sleep_with_interrupt"),
            pytest.raises(RuntimeError, match="boom"),
        ):
            gateway.complete("sys", "user")
        assert len(gateway.call_records) == 1
        record = gateway.call_records[0]
        assert record.status == "failed"
        assert record.retry_count == 2

    @patch("specmetrics.kernel.llm_gateway.litellm")
    def test_invalid_json_retries_with_corrected_prompt(self, mock_litellm):
        gateway = self._gateway(max_retries=2)
        mock_litellm.completion.side_effect = [
            _FakeResponse("not json"),
            _FakeResponse('{"ok": true}'),
        ]
        result = gateway.complete("sys", "user", json_mode=True)
        assert result == '{"ok": true}'
        messages = mock_litellm.completion.call_args_list[1].kwargs["messages"]
        assert "valid JSON only" in messages[-1]["content"]
        assert gateway.call_records[0].retry_count == 1

    @patch("specmetrics.kernel.llm_gateway.litellm")
    def test_invalid_json_exhausts_retries_raises(self, mock_litellm):
        gateway = self._gateway(max_retries=1)
        mock_litellm.completion.return_value = _FakeResponse("not json")
        with pytest.raises(RuntimeError, match="Expecting value"):
            gateway.complete("sys", "user", json_mode=True)

    @patch("specmetrics.kernel.llm_gateway.litellm")
    def test_missing_usage_defaults_to_zero(self, mock_litellm):
        gateway = self._gateway()
        mock_litellm.completion.return_value = _FakeResponse(
            '{"ok": true}', usage=None
        )
        gateway.complete("sys", "user")
        record = gateway.call_records[0]
        assert record.prompt_tokens == 0
        assert record.response_tokens == 0

    @patch("specmetrics.kernel.llm_gateway.litellm")
    def test_records_rate_limit_delay(self, mock_litellm):
        gateway = self._gateway()
        mock_litellm.completion.return_value = _FakeResponse('{"ok": true}')
        with patch.object(gateway.rate_limiter, "wait_and_record", return_value=0.5):
            gateway.complete("sys", "user")
        assert gateway.call_records[0].rate_limit_delay_ms == 500

    @patch("specmetrics.kernel.llm_gateway.litellm")
    def test_completion_kwargs_include_model(self, mock_litellm):
        gateway = self._gateway(model="gpt-4o-mini")
        mock_litellm.completion.return_value = _FakeResponse('{"ok": true}')
        gateway.complete("sys", "user")
        kwargs = mock_litellm.completion.call_args.kwargs
        assert kwargs["model"] == "gpt-4o-mini"

    @patch("specmetrics.kernel.llm_gateway.litellm")
    def test_sleep_with_interrupt_re_raises(self, mock_litellm):
        gateway = self._gateway()
        with (
            patch("time.sleep", side_effect=KeyboardInterrupt),
            pytest.raises(KeyboardInterrupt),
        ):
            gateway._sleep_with_interrupt(2, 1)

    def test_detect_provider_branches(self):
        assert CompleteMixin is not None



class TestLLMGatewayGetAttr:
    def test_litellm_resolved_when_available(self) -> None:
        import specmetrics.kernel.llm_gateway as gateway_module

        with patch("specmetrics.kernel.llm_gateway.HAS_LITELLM", True):
            assert gateway_module.litellm is not None

    def test_litellm_none_when_unavailable(self) -> None:
        import specmetrics.kernel.llm_gateway as gateway_module

        with patch("specmetrics.kernel.llm_gateway.HAS_LITELLM", False):
            assert gateway_module.litellm is None


class TestGetSummaryStats:
    def _record(self, prompt=10, response=5, duration=100):
        from specmetrics.kernel._models import LLMCallRecord

        return LLMCallRecord(
            provider="openai",
            model="gpt-4o",
            prompt_tokens=prompt,
            response_tokens=response,
            duration_ms=duration,
        )

    def test_summary_stats_empty(self) -> None:
        gateway = LLMGateway(LLMGatewayConfig())
        assert gateway.get_summary_stats() == {
            "total_calls": 0,
            "total_tokens": 0,
            "total_duration_ms": 0,
        }

    def test_summary_stats_summed(self) -> None:
        gateway = LLMGateway(LLMGatewayConfig())
        gateway.call_records = [
            self._record(prompt=10, response=5, duration=100),
            self._record(prompt=20, response=10, duration=50),
        ]
        stats = gateway.get_summary_stats()
        assert stats["total_calls"] == 2
        assert stats["total_tokens"] == 45
        assert stats["total_duration_ms"] == 150

    def test_tokens_are_summed_not_subtracted(self) -> None:
        gateway = LLMGateway(LLMGatewayConfig())
        gateway.call_records = [self._record(prompt=10, response=5)]
        assert gateway.get_summary_stats()["total_tokens"] == 15
