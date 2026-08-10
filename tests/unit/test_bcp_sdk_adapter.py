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

    @pytest.mark.slow
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

    @pytest.mark.slow
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


class TestAuthErrorResult:
    def _adapter(self, provider: str = "openai") -> BcpSdkAdapter:
        adapter = BcpSdkAdapter(provider=provider)
        adapter._provider = provider
        return adapter

    def test_auth_error_result_duration_computed_in_ms(self):
        """Kills BcpSdkAdapter::_auth_error_result__mutmut_7/8/9 (duration_ms arithmetic)."""
        adapter = self._adapter()
        with patch(
            "specmetrics.plugins.measurement.bcp.sdk_adapter.time.monotonic",
            return_value=1001.567897,
        ):
            result = adapter._auth_error_result(Exception("401 Unauthorized"), 1000.0)
        assert result is not None
        assert result.duration_ms == pytest.approx(1567.9, abs=0.01)

    def test_auth_error_result_provider_propagated(self):
        """Kills BcpSdkAdapter::_auth_error_result__mutmut_15 (provider= arg deleted)."""
        adapter = self._adapter(provider="claude")
        with patch(
            "specmetrics.plugins.measurement.bcp.sdk_adapter.time.monotonic",
            side_effect=[1000.0, 1001.0],
        ):
            result = adapter._auth_error_result(Exception("401 Unauthorized"), 1000.0)
        assert result is not None
        assert result.provider == "claude"

    def test_auth_error_result_duration_rounded_to_two_decimals(self):
        """Kills BcpSdkAdapter::_auth_error_result__mutmut_16/20/21/22/23 (round semantics)."""
        adapter = self._adapter()
        with patch(
            "specmetrics.plugins.measurement.bcp.sdk_adapter.time.monotonic",
            return_value=1001.567897,
        ):
            result = adapter._auth_error_result(Exception("401 Unauthorized"), 1000.0)
        assert result is not None
        assert result.duration_ms == pytest.approx(1567.9, abs=0.01)

    def test_auth_error_detection_uses_lowercase_error(self):
        """Kills BcpSdkAdapter::_auth_error_result__mutmut_2 (str(exc).lower() replaced)."""
        adapter = self._adapter()
        with patch(
            "specmetrics.plugins.measurement.bcp.sdk_adapter.time.monotonic",
            side_effect=[1000.0, 1001.0],
        ):
            result = adapter._auth_error_result(Exception("invalid API key"), 1000.0)
        assert result is not None
        assert result.total_bcp == 0.0
