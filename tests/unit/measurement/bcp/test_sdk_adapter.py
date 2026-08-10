from __future__ import annotations

import builtins

import pytest
import structlog
from structlog.testing import capture_logs

from specmetrics.plugins.measurement.bcp import sdk_adapter
from specmetrics.plugins.measurement.bcp.sdk_adapter import BcpSdkAdapter


class FakeBcpClient:
    def __init__(self, provider: str = "openai") -> None:
        self.provider = provider
        self.calls: list[str] = []

    def calculate(self, story: str) -> dict:
        self.calls.append(story)
        return {"total_bcp": 12.5, "breakdown": {"complexity": 7.5, "effort": 5.0}}


class RaisingClient:
    def __init__(self, provider: str = "openai") -> None:
        self.provider = provider

    def calculate(self, story: str) -> dict:
        raise RuntimeError("boom")


class AuthFailingClient:
    def __init__(self, provider: str = "openai") -> None:
        self.provider = provider

    def calculate(self, story: str) -> dict:
        raise RuntimeError("401 unauthorized")


class MixedCaseAuthClient:
    def __init__(self, provider: str = "openai") -> None:
        self.provider = provider

    def calculate(self, story: str) -> dict:
        raise RuntimeError("Unauthorized access")


class PartiallyRaisingClient:
    def __init__(self, provider: str = "openai") -> None:
        self.provider = provider
        self.attempts = 0

    def calculate(self, story: str) -> dict:
        self.attempts += 1
        if self.attempts < 3:
            raise RuntimeError("transient")
        return {"total_bcp": 3.0}


@pytest.fixture(autouse=True)
def _reset_import_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    yield
    sdk_adapter.BCP_CLIENT = None


def _patch_client(monkeypatch: pytest.MonkeyPatch, client_cls: type) -> None:
    monkeypatch.setattr(
        sdk_adapter, "_import_bcp_client", lambda: client_cls
    )


def _adapter(client_cls: type, provider: str = "openai") -> BcpSdkAdapter:
    adapter = BcpSdkAdapter.__new__(BcpSdkAdapter)
    adapter._provider = provider
    adapter._log_level = "INFO"
    adapter._client = client_cls(provider=provider)
    adapter._client_class = client_cls
    adapter._import_error = None
    return adapter


class TestImportBcpClient:
    def test_returns_cached_client(self, monkeypatch: pytest.MonkeyPatch) -> None:
        sdk_adapter.BCP_CLIENT = object()
        result = sdk_adapter._import_bcp_client()
        assert result is sdk_adapter.BCP_CLIENT

    def test_returns_none_when_imports_fail(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_import(name, *args, **kwargs):
            raise ImportError("nope")

        monkeypatch.setattr(
            builtins, "__import__", fake_import
        )
        sdk_adapter.BCP_CLIENT = None
        assert sdk_adapter._import_bcp_client() is None

    def test_imports_from_bcp_calculator(self, monkeypatch: pytest.MonkeyPatch) -> None:
        real_import = builtins.__import__
        sdk_adapter.BCP_CLIENT = None

        def fake_import(name, *args, **kwargs):
            if name == "bcp_calculator":
                module = type("mod", (), {"BCPClient": FakeBcpClient})
                return module
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        assert sdk_adapter._import_bcp_client() is FakeBcpClient

    def test_imports_from_src_sdk_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        real_import = builtins.__import__
        sdk_adapter.BCP_CLIENT = None

        def fake_import(name, *args, **kwargs):
            if name == "bcp_calculator":
                raise ImportError("missing")
            if name == "src.sdk":
                module = type("mod", (), {"BCPClient": RaisingClient})
                return module
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        assert sdk_adapter._import_bcp_client() is RaisingClient


class TestCheckCredentials:
    def test_missing_openai_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        assert sdk_adapter.check_credentials("openai") == "OPENAI_API_KEY"

    def test_missing_claude_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert sdk_adapter.check_credentials("claude") == "ANTHROPIC_API_KEY"

    def test_present_key_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        assert sdk_adapter.check_credentials("openai") is None

    def test_present_claude_key_returns_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        assert sdk_adapter.check_credentials("claude") is None


class TestAuthErrorDetection:
    def test_detects_common_error_codes(self) -> None:
        for err in ["401", "403", "auth failed", "unauthorized", "invalid api key"]:
            assert sdk_adapter._is_auth_error(err) is True

    def test_ignores_unrelated_errors(self) -> None:
        assert sdk_adapter._is_auth_error("connection reset") is False


class TestBcpSdkAdapter:
    def test_constructor_imports_client(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        adapter = BcpSdkAdapter(provider="openai")
        assert adapter.is_available is True
        assert adapter.provider == "openai"

    def test_constructor_records_import_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_client(monkeypatch, None)
        adapter = BcpSdkAdapter()
        assert adapter.is_available is False
        assert "SDK not installed" in (adapter._import_error or "")

    def test_constructor_uses_default_values(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        adapter = BcpSdkAdapter()
        assert adapter.provider == "openai"
        assert adapter._log_level == "INFO"
        assert adapter._client_class is FakeBcpClient
        assert adapter._client is not None

    def test_constructor_passes_provider_to_client(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        adapter = BcpSdkAdapter(provider="anthropic")
        assert adapter._client.provider == "anthropic"

    def test_constructor_exact_import_error_message(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, None)
        adapter = BcpSdkAdapter()
        assert (
            adapter._import_error
            == "bcp-calculator SDK not installed. "
            "Install with: pip install bcp-calculator"
        )

    def test_constructor_records_client_exception(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class ExplodingClient:
            def __init__(self, provider):
                raise RuntimeError("client init failed")

        _patch_client(monkeypatch, ExplodingClient)
        adapter = BcpSdkAdapter(provider="openai")
        assert adapter.is_available is False
        assert adapter._import_error == "client init failed"

    def test_calculate_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        adapter = _adapter(FakeBcpClient)
        result = adapter.calculate("story text")
        assert result.total_bcp == 12.5
        assert result.breakdown == {"complexity": 7.5, "effort": 5.0}
        assert result.errors == []
        assert result.provider == "openai"

    def test_calculate_non_dict_response(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class NonDictClient:
            def __init__(self, provider="openai"):
                self.provider = provider

            def calculate(self, story):
                return "not a dict"

        _patch_client(monkeypatch, NonDictClient)
        result = _adapter(NonDictClient).calculate("s")
        assert result.total_bcp == 0.0
        assert "non-dict" in result.errors[0]

    def test_calculate_auth_error_short_circuits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_client(monkeypatch, AuthFailingClient)
        result = _adapter(AuthFailingClient).calculate("s")
        assert result.total_bcp == 0.0
        assert "Auth error" in result.errors[0]

    def test_calculate_retries_then_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_client(monkeypatch, RaisingClient)
        adapter = _adapter(RaisingClient)
        monkeypatch.setattr(sdk_adapter.time, "sleep", lambda _s: None)
        result = adapter.calculate("s")
        assert result.total_bcp == 0.0
        assert "Failed after 3 retries" in result.errors[0]

    def test_calculate_succeeds_on_retry(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_client(monkeypatch, PartiallyRaisingClient)
        adapter = _adapter(PartiallyRaisingClient)
        monkeypatch.setattr(sdk_adapter.time, "sleep", lambda _s: None)
        result = adapter.calculate("s")
        assert result.total_bcp == 3.0

    def test_calculate_passes_story_to_client(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        adapter = _adapter(FakeBcpClient)
        adapter.calculate("the story text")
        assert adapter._client.calls == ["the story text"]

    def test_calculate_retries_use_backoff(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, PartiallyRaisingClient)
        adapter = _adapter(PartiallyRaisingClient)
        sleeps: list[float] = []
        monkeypatch.setattr(sdk_adapter.time, "sleep", lambda s: sleeps.append(s))
        adapter.calculate("s")
        assert sleeps == [2, 4]

    def test_calculate_failure_includes_last_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, RaisingClient)
        adapter = _adapter(RaisingClient)
        monkeypatch.setattr(sdk_adapter.time, "sleep", lambda _s: None)
        result = adapter.calculate("s")
        assert "boom" in result.errors[0]

    def test_calculate_failure_keeps_provider_and_duration(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        _patch_client(monkeypatch, RaisingClient)
        adapter = _adapter(RaisingClient, provider="anthropic")
        monkeypatch.setattr(sdk_adapter.time, "sleep", lambda _s: None)
        counter = [0.0]

        def fake_monotonic() -> float:
            counter[0] += 0.567897
            return counter[0]

        monkeypatch.setattr(sdk_adapter.time, "monotonic", fake_monotonic)
        result = adapter.calculate("s")
        assert result.provider == "anthropic"
        assert result.duration_ms == round(567.897, 2)
        assert "boom" in result.errors[0]

    def test_calculate_mixed_case_auth_detected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, MixedCaseAuthClient)
        adapter = _adapter(MixedCaseAuthClient)
        monkeypatch.setattr(sdk_adapter.time, "sleep", lambda _s: None)
        result = adapter.calculate("s")
        assert "Auth error" in result.errors[0]

    def test_calculate_logs_retry_debug(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, RaisingClient)
        adapter = _adapter(RaisingClient)
        monkeypatch.setattr(sdk_adapter.time, "sleep", lambda _s: None)
        old_wrapper = structlog.get_config()["wrapper_class"]
        old_cache = structlog.get_config()["cache_logger_on_first_use"]
        structlog.configure(
            wrapper_class=structlog.BoundLogger,
            cache_logger_on_first_use=False,
        )
        monkeypatch.setattr(
            sdk_adapter, "logger", structlog.get_logger(sdk_adapter.__name__)
        )
        try:
            with capture_logs() as captured:
                adapter.calculate("s")
        finally:
            structlog.configure(
                wrapper_class=old_wrapper,
                cache_logger_on_first_use=old_cache,
            )
        retries = [e for e in captured if e["event"] == "bcp_sdk_retry"]
        assert [r["attempt"] for r in retries] == [1, 2, 3]
        assert all(r["error"] == "boom" for r in retries)

    def test_calculate_duration_uses_elapsed_ms(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        adapter = _adapter(FakeBcpClient)
        counter = [1000.0]

        def fake_monotonic() -> float:
            counter[0] += 5.0
            return counter[0]

        monkeypatch.setattr(sdk_adapter.time, "monotonic", fake_monotonic)
        result = adapter.calculate("s")
        assert result.duration_ms == round(5000.0, 2)

    def test_parse_response_total_bcp_defaults_to_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        adapter = _adapter(FakeBcpClient)
        result = adapter._parse_response({"breakdown": {}}, 0.0)
        assert result.total_bcp == 0.0

    def test_parse_response_preserves_fields(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        adapter = _adapter(FakeBcpClient, provider="anthropic")
        raw = {"total_bcp": 2.5, "breakdown": {"bl": 2.5}}
        result = adapter._parse_response(raw, 0.0)
        assert result.total_bcp == 2.5
        assert result.breakdown == {"bl": 2.5}
        assert result.raw_response == raw
        assert result.provider == "anthropic"

    def test_parse_response_non_dict_exact_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        adapter = _adapter(FakeBcpClient, provider="anthropic")
        result = adapter._parse_response("oops", 0.0)
        assert result.total_bcp == 0.0
        assert result.provider == "anthropic"
        assert result.errors == ["SDK returned non-dict response"]

    def test_parse_response_rounds_duration_to_two_decimals(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        adapter = _adapter(FakeBcpClient)
        counter = [0.0]

        def fake_monotonic() -> float:
            counter[0] += 0.567897
            return counter[0]

        monkeypatch.setattr(sdk_adapter.time, "monotonic", fake_monotonic)
        result = adapter._parse_response({"total_bcp": 1.0}, 0.0)
        assert result.duration_ms == round(567.897, 2)

    def test_calculate_unavailable_returns_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        adapter = BcpSdkAdapter.__new__(BcpSdkAdapter)
        adapter._provider = "openai"
        adapter._log_level = "INFO"
        adapter._client = None
        adapter._client_class = None
        adapter._import_error = "SDK not installed. Install with: pip install bcp-calculator"
        result = adapter.calculate("s")
        assert result.errors == [adapter._import_error]

    def test_calculate_missing_credentials(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        result = _adapter(FakeBcpClient).calculate("s")
        assert "Missing environment variable: OPENAI_API_KEY" in result.errors[0]

    def test_unavailable_result_zero_total(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        adapter = _adapter(FakeBcpClient)
        adapter._client = None
        result = adapter.calculate("s")
        assert result.total_bcp == 0.0
        assert result.provider == "openai"

    def test_unavailable_result_default_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        adapter = _adapter(FakeBcpClient)
        adapter._client = None
        adapter._import_error = None
        result = adapter.calculate("s")
        assert result.errors == ["SDK not available"]

    def test_missing_credentials_result_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        result = _adapter(FakeBcpClient).calculate("s")
        assert result.total_bcp == 0.0
        assert result.provider == "openai"

    def test_batch_calculate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        adapter = _adapter(FakeBcpClient)
        results = adapter.batch_calculate(["a", "b"])
        assert len(results) == 2
        assert results[0].total_bcp == 12.5
        assert results[1].total_bcp == 12.5

    def test_batch_calculate_forwards_stories(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_client(monkeypatch, FakeBcpClient)
        adapter = _adapter(FakeBcpClient)
        adapter.batch_calculate(["story one", "story two"])
        assert adapter._client.calls == ["story one", "story two"]

    def test_calculate_auth_error_duration(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        _patch_client(monkeypatch, AuthFailingClient)
        adapter = _adapter(AuthFailingClient, provider="anthropic")
        counter = [0.0]

        def fake_monotonic() -> float:
            counter[0] += 0.519832
            return counter[0]

        monkeypatch.setattr(sdk_adapter.time, "monotonic", fake_monotonic)
        result = adapter.calculate("s")
        assert result.provider == "anthropic"
        assert result.duration_ms == round(519.832, 2)
        assert result.errors[0] == "Auth error: 401 unauthorized"