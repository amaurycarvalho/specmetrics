from __future__ import annotations

import json
import time
import pytest
from unittest.mock import patch

from specmetrics.kernel.llm_gateway import (
    LLMGatewayConfig,
    RateLimiter,
    BatchRequest,
    DocumentPayload,
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
