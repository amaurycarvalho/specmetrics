from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from specmetrics.plugins.measurement.bcp.sdk_adapter import (
    BcpSdkAdapter,
    check_credentials,
)


class TestCheckCredentials:
    def test_openai_key_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            result = check_credentials("openai")
            assert result == "OPENAI_API_KEY"

    def test_openai_key_present(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            result = check_credentials("openai")
            assert result is None

    def test_claude_key_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            result = check_credentials("claude")
            assert result == "ANTHROPIC_API_KEY"


class TestBcpSdkAdapter:
    def test_sdk_not_installed(self):
        adapter = BcpSdkAdapter(provider="openai")
        if adapter.is_available:
            pytest.skip("SDK is installed, skipping")
        assert not adapter.is_available
        assert adapter._import_error is not None

    def test_calculate_returns_sdk_result(self):
        mock_client = MagicMock()
        mock_client.calculate.return_value = {
            "total_bcp": 15.0,
            "breakdown": {"business_logic": 8.0, "data": 7.0},
        }
        adapter = BcpSdkAdapter(provider="openai")
        adapter._client = mock_client
        adapter._import_error = None

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            result = adapter.calculate("# Story")
            assert result.total_bcp == 15.0
            assert result.breakdown["business_logic"] == 8.0
            assert len(result.errors) == 0

    def test_retry_on_transient_error(self):
        mock_client = MagicMock()
        mock_client.calculate.side_effect = [
            Exception("timeout"),
            Exception("rate limit"),
            {"total_bcp": 10.0, "breakdown": {}},
        ]
        adapter = BcpSdkAdapter(provider="openai")
        adapter._client = mock_client
        adapter._import_error = None

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            result = adapter.calculate("# Story")
            assert result.total_bcp == 10.0
            assert len(result.errors) == 0

    def test_fails_after_3_retries(self):
        mock_client = MagicMock()
        mock_client.calculate.side_effect = Exception("always fails")
        adapter = BcpSdkAdapter(provider="openai")
        adapter._client = mock_client
        adapter._import_error = None

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            result = adapter.calculate("# Story")
            assert result.total_bcp == 0.0
            assert len(result.errors) > 0

    def test_auth_error_fails_immediately(self):
        mock_client = MagicMock()
        mock_client.calculate.side_effect = Exception("401 Unauthorized")
        adapter = BcpSdkAdapter(provider="openai")
        adapter._client = mock_client
        adapter._import_error = None

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            result = adapter.calculate("# Story")
            assert result.total_bcp == 0.0
            assert any("Auth" in e for e in result.errors)

    def test_missing_credentials_returns_error(self):
        mock_client = MagicMock()
        adapter = BcpSdkAdapter(provider="openai")
        adapter._client = mock_client
        adapter._import_error = None

        with patch.dict(os.environ, {}, clear=True):
            result = adapter.calculate("# Story")
            assert result.total_bcp == 0.0
            assert any("OPENAI_API_KEY" in e for e in result.errors)

    def test_batch_calculate(self):
        mock_client = MagicMock()
        mock_client.calculate.return_value = {
            "total_bcp": 10.0,
            "breakdown": {},
        }
        adapter = BcpSdkAdapter(provider="openai")
        adapter._client = mock_client
        adapter._import_error = None

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            results = adapter.batch_calculate(["# A", "# B"])
            assert len(results) == 2
            assert results[0].total_bcp == 10.0
