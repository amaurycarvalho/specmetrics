from __future__ import annotations

import builtins
import importlib

import specmetrics.plugins.measurement.bcp._telemetry as telemetry


class TestBcpTelemetry:
    def test_instruments_defined_when_otel_available(self):
        module = importlib.reload(telemetry)
        assert module._sdk_duration is not None
        assert module._story_gauge is not None
        assert module._sdk_requests is not None
        assert module._sdk_errors is not None

    def test_instruments_null_when_otel_unavailable(self, monkeypatch):
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "opentelemetry":
                raise ImportError("opentelemetry not installed")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        reloaded = importlib.reload(telemetry)
        assert reloaded._sdk_duration is None
        assert reloaded._story_gauge is None
        assert reloaded._sdk_requests is None
        assert reloaded._sdk_errors is None

        monkeypatch.setattr(builtins, "__import__", real_import)
        importlib.reload(telemetry)