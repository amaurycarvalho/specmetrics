from __future__ import annotations

import builtins
import importlib

import specmetrics.plugins.measurement.tshirt._telemetry as telemetry


class TestTshirtTelemetry:
    def test_instruments_defined_when_otel_available(self):
        module = importlib.reload(telemetry)
        assert module._classify_duration is not None
        assert module._item_gauge is not None
        assert module._distribution_histogram is not None

    def test_instruments_null_when_otel_unavailable(self, monkeypatch):
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "opentelemetry":
                raise ImportError("opentelemetry not installed")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        reloaded = importlib.reload(telemetry)
        assert reloaded._classify_duration is None
        assert reloaded._item_gauge is None
        assert reloaded._distribution_histogram is None

        monkeypatch.setattr(builtins, "__import__", real_import)
        importlib.reload(telemetry)